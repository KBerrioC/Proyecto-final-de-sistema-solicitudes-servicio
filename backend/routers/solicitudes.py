"""Solicitudes: creación (EP-06), listado (EP-07), detalle (EP-08) e historial (EP-16)."""
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import get_usuario_actual, requiere_rol
from ..database import get_db
from ..models import Usuario
from ..schemas import EventoSalida, SolicitudDetalle, SolicitudLista
from ..services import solicitudes as servicio_solicitudes
from ..services.archivos import MAX_ARCHIVOS, validar_archivo

router = APIRouter(prefix="/api/solicitudes", tags=["Solicitudes"])


@router.post("", response_model=SolicitudDetalle, status_code=status.HTTP_201_CREATED)
def crear_solicitud(
    servicio_id: int = Form(...),
    asunto: str = Form(..., max_length=150),
    descripcion: str = Form(..., max_length=2000),
    archivos: list[UploadFile] = File(default=[]),
    usuario: Usuario = Depends(requiere_rol("solicitante")),
    db: Session = Depends(get_db),
):
    """EP-06: el solicitante presenta una solicitud, con adjuntos si el servicio los exige."""
    asunto = asunto.strip()
    descripcion = descripcion.strip()
    if len(asunto) < 5:
        raise HTTPException(422, "El asunto debe tener al menos 5 caracteres")
    if len(descripcion) < 10:
        raise HTTPException(
            422, "La descripción debe tener al menos 10 caracteres"
        )
    archivos = [a for a in archivos if a.filename]  # el navegador envía un campo vacío si no hay archivos
    if len(archivos) > MAX_ARCHIVOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Se permiten como máximo {MAX_ARCHIVOS} archivos")
    validados = [validar_archivo(a) for a in archivos]
    solicitud = servicio_solicitudes.crear_solicitud(db, usuario, servicio_id, asunto, descripcion, validados)
    return servicio_solicitudes.detalle_solicitud(solicitud)


Estado = Literal[
    "recibida", "en_evaluacion", "pendiente_informacion", "en_gestion",
    "finalizada", "rechazada", "cancelada",
]
Prioridad = Literal["alta", "media", "baja"]


@router.get("", response_model=SolicitudLista, response_model_exclude_unset=True)
def listar_solicitudes(
    estado: Estado | None = None,
    servicio_id: int | None = None,
    prioridad: Prioridad | None = None,
    responsable_id: int | None = None,
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """EP-07: solicitudes que el usuario puede ver, con filtros y paginación."""
    total, items = servicio_solicitudes.listar_solicitudes(
        db, usuario, estado=estado, servicio_id=servicio_id, prioridad=prioridad,
        responsable_id=responsable_id, limite=limite, desplazamiento=desplazamiento,
    )
    return SolicitudLista(total=total, items=items)


@router.get("/{solicitud_id}", response_model=SolicitudDetalle)
def detalle_solicitud(
    solicitud_id: int,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """EP-08: detalle de una solicitud. 404 si no existe o el usuario no puede verla."""
    solicitud = servicio_solicitudes.obtener_visible(db, usuario, solicitud_id)
    return servicio_solicitudes.detalle_solicitud(solicitud)


@router.get(
    "/{solicitud_id}/eventos", response_model=list[EventoSalida], response_model_exclude_unset=True
)
def historial_solicitud(
    solicitud_id: int,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """EP-16: historial de la solicitud. El solicitante no ve las notas internas (RN-05)."""
    solicitud = servicio_solicitudes.obtener_visible(db, usuario, solicitud_id)
    return servicio_solicitudes.listar_eventos(solicitud, usuario)
