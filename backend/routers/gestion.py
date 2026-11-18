"""Gestión de solicitudes: EP-09 a EP-15 (docs/diseno.md, secciones 4 y 5)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import requiere_rol
from ..database import get_db
from ..models import Usuario
from ..schemas import (
    CancelacionEntrada,
    EstadoEntrada,
    EventoSalida,
    NotaEntrada,
    PrioridadEntrada,
    ResponsableEntrada,
    SolicitudDetalle,
)
from ..services import gestion
from ..services import solicitudes as consulta
from ..services.archivos import MAX_ARCHIVOS, validar_archivo

router = APIRouter(prefix="/api/solicitudes", tags=["Gestión de solicitudes"])

PERSONAL = requiere_rol("atencion", "coordinacion")
SOLICITANTE = requiere_rol("solicitante")


def _detalle(solicitud) -> SolicitudDetalle:
    return consulta.detalle_solicitud(solicitud)


@router.patch("/{solicitud_id}/estado", response_model=SolicitudDetalle)
def cambiar_estado(
    solicitud_id: int,
    datos: EstadoEntrada,
    usuario: Usuario = Depends(PERSONAL),
    db: Session = Depends(get_db),
):
    """EP-09: evalúa la solicitud (iniciar evaluación, aceptar, pedir información o rechazar)."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    return _detalle(gestion.evaluar(db, solicitud, usuario, datos))


@router.post("/{solicitud_id}/finalizacion", response_model=SolicitudDetalle)
def finalizar_solicitud(
    solicitud_id: int,
    respuesta: str = Form(...),
    archivo: UploadFile | None = File(default=None),
    usuario: Usuario = Depends(PERSONAL),
    db: Session = Depends(get_db),
):
    """EP-10: finaliza la solicitud con una respuesta y, opcionalmente, un archivo."""
    respuesta = respuesta.strip()
    if not 10 <= len(respuesta) <= 2000:
        raise HTTPException(422, "La respuesta debe tener entre 10 y 2000 caracteres")
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    validado = validar_archivo(archivo) if archivo is not None and archivo.filename else None
    return _detalle(gestion.finalizar(db, solicitud, usuario, respuesta, validado))


@router.patch("/{solicitud_id}/responsable", response_model=SolicitudDetalle)
def reasignar_responsable(
    solicitud_id: int,
    datos: ResponsableEntrada,
    usuario: Usuario = Depends(PERSONAL),
    db: Session = Depends(get_db),
):
    """EP-11: reasigna el responsable de una solicitud en gestión."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    return _detalle(gestion.reasignar(db, solicitud, usuario, datos))


@router.patch("/{solicitud_id}/prioridad", response_model=SolicitudDetalle)
def ajustar_prioridad(
    solicitud_id: int,
    datos: PrioridadEntrada,
    usuario: Usuario = Depends(PERSONAL),
    db: Session = Depends(get_db),
):
    """EP-12: ajusta la prioridad, con motivo."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    return _detalle(gestion.cambiar_prioridad(db, solicitud, usuario, datos))


@router.post(
    "/{solicitud_id}/notas",
    response_model=EventoSalida,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
)
def agregar_nota(
    solicitud_id: int,
    datos: NotaEntrada,
    usuario: Usuario = Depends(PERSONAL),
    db: Session = Depends(get_db),
):
    """EP-13: registra una nota o acción de gestión en el historial."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    evento = gestion.registrar_nota(db, solicitud, usuario, datos)
    return consulta.evento_salida(evento, personal=True)


@router.post("/{solicitud_id}/informacion", response_model=SolicitudDetalle)
def entregar_informacion(
    solicitud_id: int,
    texto: str | None = Form(default=None, max_length=2000),
    archivos: list[UploadFile] = File(default=[]),
    usuario: Usuario = Depends(SOLICITANTE),
    db: Session = Depends(get_db),
):
    """EP-14: el solicitante responde a una petición de información."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    texto = (texto or "").strip() or None
    archivos = [a for a in archivos if a.filename]
    if len(archivos) > MAX_ARCHIVOS:
        raise HTTPException(400, f"Se permiten como máximo {MAX_ARCHIVOS} archivos")
    validados = [validar_archivo(a) for a in archivos]
    return _detalle(gestion.responder_informacion(db, solicitud, usuario, texto, validados))


@router.post("/{solicitud_id}/cancelacion", response_model=SolicitudDetalle)
def cancelar_solicitud(
    solicitud_id: int,
    datos: CancelacionEntrada | None = None,
    usuario: Usuario = Depends(SOLICITANTE),
    db: Session = Depends(get_db),
):
    """EP-15: el solicitante cancela su solicitud antes de que pase a gestión."""
    solicitud = consulta.obtener_visible(db, usuario, solicitud_id)
    motivo = datos.motivo if datos else None
    return _detalle(gestion.cancelar(db, solicitud, usuario, motivo))
