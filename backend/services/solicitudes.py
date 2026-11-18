"""Reglas de negocio de las solicitudes (docs/diseno.md, sección 5)."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from ..models import Adjunto, Evento, Servicio, Solicitud, Usuario, ahora
from ..schemas import (
    AdjuntoSalida,
    AutorEvento,
    EventoSalida,
    PersonaResumen,
    ServicioResumen,
    SolicitudDetalle,
    SolicitudItem,
)
from . import archivos as servicio_archivos
from .archivos import ArchivoValidado

ESTADOS_FINALES = ("finalizada", "rechazada", "cancelada")
ESTADOS_BANDEJA = ("recibida", "en_evaluacion", "pendiente_informacion")


def crear_solicitud(
    db: Session,
    solicitante: Usuario,
    servicio_id: int,
    asunto: str,
    descripcion: str,
    adjuntos: list[ArchivoValidado],
) -> Solicitud:
    """EP-06: crea la solicitud en estado «recibida» con su evento y sus adjuntos."""
    servicio = db.get(Servicio, servicio_id)
    if servicio is None or not servicio.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El servicio indicado no existe o no está activo")
    if servicio.requiere_adjunto and not adjuntos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Este servicio requiere al menos un documento adjunto"
        )

    guardados: list[str] = []
    try:
        solicitud = Solicitud(
            radicado=f"TMP-{uuid.uuid4().hex}",  # se reemplaza al conocer el id
            solicitante_id=solicitante.id,
            servicio_id=servicio.id,
            asunto=asunto,
            descripcion=descripcion,
            estado="recibida",
            prioridad=servicio.prioridad_defecto,
        )
        db.add(solicitud)
        db.flush()
        solicitud.radicado = f"SOL-{solicitud.creado_en.year}-{solicitud.id:05d}"
        db.add(
            Evento(
                solicitud_id=solicitud.id,
                autor_id=solicitante.id,
                tipo="creada",
                estado_nuevo="recibida",
                visible_solicitante=True,
            )
        )
        for archivo in adjuntos:
            nombre_almacenado = servicio_archivos.guardar_archivo(archivo)
            guardados.append(nombre_almacenado)
            db.add(
                Adjunto(
                    solicitud_id=solicitud.id,
                    subido_por_id=solicitante.id,
                    proposito="solicitud",
                    nombre_original=archivo.nombre_original,
                    nombre_almacenado=nombre_almacenado,
                    tipo_mime=archivo.tipo_mime,
                    tamano_bytes=len(archivo.contenido),
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        servicio_archivos.eliminar_archivos(guardados)
        raise
    db.refresh(solicitud)
    return solicitud


def detalle_solicitud(solicitud: Solicitud) -> SolicitudDetalle:
    """Arma la respuesta de detalle. Los tiempos se calculan, no se guardan (RN-10)."""
    dias_pendientes = (
        None if solicitud.estado in ESTADOS_FINALES else (ahora() - solicitud.creado_en).days
    )
    dias_atencion = (
        (solicitud.finalizado_en - solicitud.creado_en).days if solicitud.finalizado_en else None
    )
    return SolicitudDetalle(
        id=solicitud.id,
        radicado=solicitud.radicado,
        servicio=ServicioResumen.model_validate(solicitud.servicio),
        asunto=solicitud.asunto,
        descripcion=solicitud.descripcion,
        estado=solicitud.estado,
        prioridad=solicitud.prioridad,
        solicitante=PersonaResumen.model_validate(solicitud.solicitante),
        responsable=(
            PersonaResumen.model_validate(solicitud.responsable) if solicitud.responsable else None
        ),
        respuesta=solicitud.respuesta,
        adjuntos=[AdjuntoSalida.model_validate(a) for a in solicitud.adjuntos],
        creado_en=solicitud.creado_en,
        actualizado_en=solicitud.actualizado_en,
        finalizado_en=solicitud.finalizado_en,
        dias_pendientes=dias_pendientes,
        dias_atencion=dias_atencion,
    )


def es_personal(usuario: Usuario) -> bool:
    return usuario.rol in ("atencion", "coordinacion")


def condicion_visible(usuario: Usuario):
    """Condición SQL con las solicitudes que el usuario puede ver (diseno.md, sección 5.2)."""
    if usuario.rol == "coordinacion":
        return Solicitud.id.is_not(None)
    if usuario.rol == "atencion":
        return or_(
            Solicitud.estado.in_(ESTADOS_BANDEJA), Solicitud.responsable_id == usuario.id
        )
    return Solicitud.solicitante_id == usuario.id


def obtener_visible(db: Session, usuario: Usuario, solicitud_id: int) -> Solicitud:
    """Devuelve la solicitud o responde 404, exista o no, si el usuario no puede verla."""
    solicitud = db.scalar(
        select(Solicitud).where(Solicitud.id == solicitud_id, condicion_visible(usuario))
    )
    if solicitud is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitud no encontrada")
    return solicitud


def _dias_pendientes(solicitud: Solicitud) -> int | None:
    if solicitud.estado in ESTADOS_FINALES:
        return None
    return (ahora() - solicitud.creado_en).days


def listar_solicitudes(
    db: Session,
    usuario: Usuario,
    *,
    estado: str | None,
    servicio_id: int | None,
    prioridad: str | None,
    responsable_id: int | None,
    limite: int,
    desplazamiento: int,
) -> tuple[int, list[SolicitudItem]]:
    """EP-07: lista paginada con filtros, solo con lo que el usuario puede ver."""
    filtros = [condicion_visible(usuario)]
    if estado:
        filtros.append(Solicitud.estado == estado)
    if servicio_id is not None:
        filtros.append(Solicitud.servicio_id == servicio_id)
    if prioridad:
        filtros.append(Solicitud.prioridad == prioridad)
    if responsable_id is not None:
        filtros.append(Solicitud.responsable_id == responsable_id)

    total = db.scalar(select(func.count()).select_from(Solicitud).where(*filtros)) or 0
    consulta = select(Solicitud).where(*filtros)
    if es_personal(usuario):
        orden_prioridad = case(
            (Solicitud.prioridad == "alta", 0), (Solicitud.prioridad == "media", 1), else_=2
        )
        consulta = consulta.order_by(orden_prioridad, Solicitud.creado_en, Solicitud.id)
    else:
        consulta = consulta.order_by(Solicitud.creado_en.desc(), Solicitud.id.desc())
    filas = db.scalars(consulta.limit(limite).offset(desplazamiento)).all()

    items = []
    for s in filas:
        datos = dict(
            id=s.id,
            radicado=s.radicado,
            asunto=s.asunto,
            servicio=ServicioResumen.model_validate(s.servicio),
            estado=s.estado,
            prioridad=s.prioridad,
            responsable=PersonaResumen.model_validate(s.responsable) if s.responsable else None,
            creado_en=s.creado_en,
            dias_pendientes=_dias_pendientes(s),
        )
        if es_personal(usuario):
            datos["solicitante"] = PersonaResumen.model_validate(s.solicitante)
        items.append(SolicitudItem(**datos))
    return total, items


def evento_salida(e: Evento, personal: bool) -> EventoSalida:
    datos = dict(
        id=e.id,
        tipo=e.tipo,
        autor=AutorEvento.model_validate(e.autor),
        estado_anterior=e.estado_anterior,
        estado_nuevo=e.estado_nuevo,
        detalle=e.detalle,
        creado_en=e.creado_en,
    )
    if personal:
        datos["visible_solicitante"] = e.visible_solicitante
    return EventoSalida(**datos)


def listar_eventos(solicitud: Solicitud, usuario: Usuario) -> list[EventoSalida]:
    """EP-16: historial. El solicitante no recibe los eventos internos (RN-05)."""
    personal = es_personal(usuario)
    return [
        evento_salida(e, personal)
        for e in solicitud.eventos
        if personal or e.visible_solicitante
    ]
