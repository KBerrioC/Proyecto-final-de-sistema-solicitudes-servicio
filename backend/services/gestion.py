"""Gestión de solicitudes: transiciones, permisos y eventos (docs/diseno.md, sección 5)."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Adjunto, Evento, Solicitud, Usuario, ahora
from . import archivos as servicio_archivos
from .archivos import ArchivoValidado

# Tabla de transiciones válidas (RN-01). Los estados finales no tienen salidas (RN-12).
TRANSICIONES = {
    "recibida": ("en_evaluacion", "cancelada"),
    "en_evaluacion": ("en_gestion", "pendiente_informacion", "rechazada", "cancelada"),
    "pendiente_informacion": ("en_evaluacion", "cancelada"),
    "en_gestion": ("finalizada",),
    "finalizada": (),
    "rechazada": (),
    "cancelada": (),
}
ESTADOS_FINALES = ("finalizada", "rechazada", "cancelada")


def validar_transicion(solicitud: Solicitud, nuevo_estado: str) -> None:
    """RN-01 y RN-12: responde 409 si el estado actual no permite pasar al pedido."""
    if nuevo_estado not in TRANSICIONES[solicitud.estado]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"No se puede pasar de «{solicitud.estado}» a «{nuevo_estado}»",
        )


def exigir_gestion(solicitud: Solicitud, usuario: Usuario) -> None:
    """Solo el responsable asignado o coordinación gestionan la solicitud (diseno.md, 5.3)."""
    if usuario.rol == "coordinacion":
        return
    if usuario.rol == "atencion" and solicitud.responsable_id == usuario.id:
        return
    raise HTTPException(
        status.HTTP_403_FORBIDDEN, "Solo el responsable asignado o coordinación pueden hacerlo"
    )


def exigir_no_final(solicitud: Solicitud) -> None:
    if solicitud.estado in ESTADOS_FINALES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"La solicitud está «{solicitud.estado}» y ya no admite cambios",
        )


def exigir_personal_atencion(db: Session, usuario_id: int | None) -> Usuario:
    """RN-07: el responsable debe ser personal de atención activo."""
    responsable = db.get(Usuario, usuario_id) if usuario_id is not None else None
    if responsable is None or not responsable.activo or responsable.rol != "atencion":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "El responsable debe ser personal de atención activo"
        )
    return responsable


def registrar_evento(
    db: Session,
    solicitud: Solicitud,
    autor: Usuario,
    tipo: str,
    *,
    estado_anterior: str | None = None,
    estado_nuevo: str | None = None,
    de_responsable_id: int | None = None,
    a_responsable_id: int | None = None,
    detalle: str | None = None,
    visible_solicitante: bool = True,
) -> Evento:
    evento = Evento(
        solicitud_id=solicitud.id,
        autor_id=autor.id,
        tipo=tipo,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        de_responsable_id=de_responsable_id,
        a_responsable_id=a_responsable_id,
        detalle=detalle,
        visible_solicitante=visible_solicitante,
    )
    db.add(evento)
    return evento


def _cambiar_estado(db, solicitud, autor, nuevo_estado, tipo, detalle=None) -> None:
    anterior = solicitud.estado
    solicitud.estado = nuevo_estado
    registrar_evento(
        db, solicitud, autor, tipo,
        estado_anterior=anterior, estado_nuevo=nuevo_estado, detalle=detalle,
    )


def _confirmar(db: Session, guardados: list[str]) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        servicio_archivos.eliminar_archivos(guardados)
        raise


def _adjuntar(db, solicitud, autor, archivos: list[ArchivoValidado], proposito, guardados) -> None:
    for archivo in archivos:
        nombre = servicio_archivos.guardar_archivo(archivo)
        guardados.append(nombre)
        db.add(
            Adjunto(
                solicitud_id=solicitud.id,
                subido_por_id=autor.id,
                proposito=proposito,
                nombre_original=archivo.nombre_original,
                nombre_almacenado=nombre,
                tipo_mime=archivo.tipo_mime,
                tamano_bytes=len(archivo.contenido),
            )
        )


def evaluar(db: Session, solicitud: Solicitud, usuario: Usuario, datos) -> Solicitud:
    """EP-09: mueve la solicitud por el flujo de evaluación."""
    nuevo = datos.estado
    validar_transicion(solicitud, nuevo)
    motivo = datos.motivo or None
    if nuevo == "en_evaluacion":
        _cambiar_estado(db, solicitud, usuario, nuevo, "evaluacion_iniciada")
    elif nuevo == "en_gestion":
        responsable = exigir_personal_atencion(db, datos.responsable_id)
        _cambiar_estado(db, solicitud, usuario, nuevo, "aceptada", motivo)
        solicitud.responsable_id = responsable.id
        registrar_evento(
            db, solicitud, usuario, "asignada",
            a_responsable_id=responsable.id, visible_solicitante=False,
        )
        if datos.prioridad and datos.prioridad != solicitud.prioridad:
            registrar_evento(
                db, solicitud, usuario, "prioridad_cambiada",
                detalle=f"{solicitud.prioridad} → {datos.prioridad}"
                + (f". Motivo: {motivo}" if motivo else ""),
                visible_solicitante=False,
            )
            solicitud.prioridad = datos.prioridad
    else:  # pendiente_informacion o rechazada: exigen motivo (RN-02)
        if not motivo:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Indique el motivo")
        tipo = "informacion_solicitada" if nuevo == "pendiente_informacion" else "rechazada"
        _cambiar_estado(db, solicitud, usuario, nuevo, tipo, motivo)
    _confirmar(db, [])
    db.refresh(solicitud)
    return solicitud


def finalizar(
    db: Session, solicitud: Solicitud, usuario: Usuario, respuesta: str,
    archivo: ArchivoValidado | None,
) -> Solicitud:
    """EP-10: finaliza con una respuesta (RN-04)."""
    exigir_gestion(solicitud, usuario)
    validar_transicion(solicitud, "finalizada")
    guardados: list[str] = []
    try:
        solicitud.respuesta = respuesta
        solicitud.finalizado_en = ahora()
        _cambiar_estado(db, solicitud, usuario, "finalizada", "finalizada")
        if archivo:
            db.flush()
            _adjuntar(db, solicitud, usuario, [archivo], "respuesta", guardados)
        _confirmar(db, guardados)
    except Exception:
        db.rollback()
        servicio_archivos.eliminar_archivos(guardados)
        raise
    db.refresh(solicitud)
    return solicitud


def reasignar(db: Session, solicitud: Solicitud, usuario: Usuario, datos) -> Solicitud:
    """EP-11: cambia el responsable y lo registra (RN-08)."""
    exigir_gestion(solicitud, usuario)
    if solicitud.estado != "en_gestion":
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se reasigna una solicitud en gestión")
    nuevo = exigir_personal_atencion(db, datos.responsable_id)
    if nuevo.id == solicitud.responsable_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esa persona ya es la responsable")
    registrar_evento(
        db, solicitud, usuario, "reasignada",
        de_responsable_id=solicitud.responsable_id, a_responsable_id=nuevo.id,
        detalle=datos.motivo or None, visible_solicitante=False,
    )
    solicitud.responsable_id = nuevo.id
    _confirmar(db, [])
    db.refresh(solicitud)
    return solicitud


def cambiar_prioridad(db: Session, solicitud: Solicitud, usuario: Usuario, datos) -> Solicitud:
    """EP-12: ajusta la prioridad con motivo (RN-09)."""
    exigir_gestion(solicitud, usuario)
    exigir_no_final(solicitud)
    if datos.prioridad == solicitud.prioridad:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La solicitud ya tiene esa prioridad")
    registrar_evento(
        db, solicitud, usuario, "prioridad_cambiada",
        detalle=f"{solicitud.prioridad} → {datos.prioridad}. Motivo: {datos.motivo}",
        visible_solicitante=False,
    )
    solicitud.prioridad = datos.prioridad
    _confirmar(db, [])
    db.refresh(solicitud)
    return solicitud


def registrar_nota(db: Session, solicitud: Solicitud, usuario: Usuario, datos) -> Evento:
    """EP-13: nota o acción de gestión; interna salvo que se marque como visible."""
    exigir_gestion(solicitud, usuario)
    exigir_no_final(solicitud)
    evento = registrar_evento(
        db, solicitud, usuario, "nota", detalle=datos.texto,
        visible_solicitante=datos.visible_solicitante,
    )
    _confirmar(db, [])
    db.refresh(evento)
    return evento


def responder_informacion(
    db: Session, solicitud: Solicitud, usuario: Usuario, texto: str | None,
    archivos: list[ArchivoValidado],
) -> Solicitud:
    """EP-14: el solicitante entrega la información pedida y la solicitud vuelve a evaluación."""
    if solicitud.estado != "pendiente_informacion":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La solicitud no está esperando información"
        )
    if not texto and not archivos:
        raise HTTPException(422, "Envíe un texto o un archivo")
    guardados: list[str] = []
    try:
        _cambiar_estado(db, solicitud, usuario, "en_evaluacion", "informacion_recibida", texto)
        db.flush()
        _adjuntar(db, solicitud, usuario, archivos, "informacion", guardados)
        _confirmar(db, guardados)
    except Exception:
        db.rollback()
        servicio_archivos.eliminar_archivos(guardados)
        raise
    db.refresh(solicitud)
    return solicitud


def cancelar(db: Session, solicitud: Solicitud, usuario: Usuario, motivo: str | None) -> Solicitud:
    """EP-15: el solicitante cancela antes de que la gestión comience (RN-11)."""
    if solicitud.estado not in ("recibida", "en_evaluacion", "pendiente_informacion"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede cancelar antes de que la solicitud pase a gestión",
        )
    _cambiar_estado(db, solicitud, usuario, "cancelada", "cancelada", motivo or None)
    _confirmar(db, [])
    db.refresh(solicitud)
    return solicitud
