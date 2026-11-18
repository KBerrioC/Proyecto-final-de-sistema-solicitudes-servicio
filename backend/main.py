"""Punto de entrada de la API del sistema de gestión de solicitudes de servicio."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models  # noqa: F401  (registra las tablas en Base.metadata)
from .config import configuracion
from .database import Base, engine, get_db
from .routers import auth, servicios, solicitudes, usuarios


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    Path(configuracion.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sistema de gestión de solicitudes de servicio",
    description="API REST del Proyecto Final 01 (PF-01) de Aplicaciones y Servicios Web.",
    version="0.3.0",
    lifespan=ciclo_de_vida,
)

app.include_router(auth.router)
app.include_router(servicios.router)
app.include_router(solicitudes.router)
app.include_router(usuarios.router)


@app.get("/api/salud", tags=["Sistema"])
def salud(db: Session = Depends(get_db)):
    """Comprueba que el servidor responde y que la base de datos es accesible."""
    db.execute(text("SELECT 1"))
    return {"estado": "ok", "base_de_datos": "ok"}
