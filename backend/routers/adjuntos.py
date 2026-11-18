"""EP-17: descarga de adjuntos, solo para quien puede ver la solicitud (RNF-05)."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import get_usuario_actual
from ..config import configuracion
from ..database import get_db
from ..models import Adjunto, Usuario
from ..services import solicitudes as servicio_solicitudes

router = APIRouter(prefix="/api/adjuntos", tags=["Adjuntos"])


@router.get("/{adjunto_id}")
def descargar_adjunto(
    adjunto_id: int,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """EP-17: devuelve el archivo con su nombre original. 404 si no existe o no es visible."""
    adjunto = db.get(Adjunto, adjunto_id)
    if adjunto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Adjunto no encontrado")
    servicio_solicitudes.obtener_visible(db, usuario, adjunto.solicitud_id)  # 404 si no la ve
    carpeta = Path(configuracion.upload_dir).resolve()
    ruta = (carpeta / adjunto.nombre_almacenado).resolve()
    if carpeta not in ruta.parents or not ruta.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Adjunto no encontrado")
    return FileResponse(
        ruta, media_type=adjunto.tipo_mime, filename=adjunto.nombre_original
    )
