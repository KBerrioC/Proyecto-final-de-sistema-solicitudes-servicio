"""EP-05: personal de atención disponible para asignar."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import requiere_rol
from ..database import get_db
from ..models import Usuario
from ..schemas import AtencionSalida

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(requiere_rol("atencion", "coordinacion"))],
)


@router.get("/atencion", response_model=list[AtencionSalida])
def listar_atencion(db: Session = Depends(get_db)):
    """EP-05: personal de atención activo."""
    return db.scalars(
        select(Usuario)
        .where(Usuario.rol == "atencion", Usuario.activo.is_(True))
        .order_by(Usuario.nombre)
    ).all()
