"""EP-04: catálogo de servicios."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_usuario_actual
from ..database import get_db
from ..models import Servicio
from ..schemas import ServicioSalida

router = APIRouter(
    prefix="/api/servicios", tags=["Servicios"], dependencies=[Depends(get_usuario_actual)]
)


@router.get("", response_model=list[ServicioSalida])
def listar_servicios(db: Session = Depends(get_db)):
    """EP-04: servicios activos, con indicación de si requieren adjunto."""
    return db.scalars(
        select(Servicio).where(Servicio.activo.is_(True)).order_by(Servicio.nombre)
    ).all()
