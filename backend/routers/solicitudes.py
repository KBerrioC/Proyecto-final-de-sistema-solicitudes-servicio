"""EP-06: creación de solicitudes (los demás endpoints de solicitudes llegan en pasos siguientes)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import requiere_rol
from ..database import get_db
from ..models import Usuario
from ..schemas import SolicitudDetalle
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
