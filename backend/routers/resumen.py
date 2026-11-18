"""EP-18: resumen consolidado, solo para coordinación (CA-06)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import requiere_rol
from ..database import get_db
from ..models import Usuario
from ..schemas import ResumenSalida
from ..services.resumen import generar_resumen

router = APIRouter(prefix="/api/resumen", tags=["Resumen"])


@router.get("", response_model=ResumenSalida)
def resumen(
    desde: date | None = None,
    hasta: date | None = None,
    usuario: Usuario = Depends(requiere_rol("coordinacion")),
    db: Session = Depends(get_db),
):
    """EP-18: conteos por estado, servicio y responsable, tiempo promedio y pendientes antiguas."""
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "La fecha «desde» no puede ser posterior a «hasta»")
    return generar_resumen(db, desde, hasta)
