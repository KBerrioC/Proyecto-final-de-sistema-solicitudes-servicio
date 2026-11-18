"""Conexión a la base de datos y sesión de SQLAlchemy."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import configuracion

ES_SQLITE = configuracion.database_url.startswith("sqlite")

engine = create_engine(
    configuracion.database_url,
    connect_args={"check_same_thread": False} if ES_SQLITE else {},
)


@event.listens_for(engine, "connect")
def activar_claves_foraneas(conexion, _registro):
    """SQLite no hace cumplir las claves foráneas si no se activan en cada conexión (RNF-04)."""
    if ES_SQLITE:
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar la solicitud."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
