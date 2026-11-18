"""Reglas de negocio de las solicitudes (docs/diseno.md, sección 5)."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import Adjunto, Evento, Servicio, Solicitud, Usuario, ahora
from ..schemas import AdjuntoSalida, PersonaResumen, ServicioResumen, SolicitudDetalle
from . import archivos as servicio_archivos
from .archivos import ArchivoValidado

ESTADOS_FINALES = ("finalizada", "rechazada", "cancelada")


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
