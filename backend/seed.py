"""Datos ficticios iniciales: catálogo de servicios y usuarios de demostración (RNF-06).

Uso, desde la raíz del repositorio y con el entorno virtual activado:
    python -m backend.seed

Es seguro ejecutarlo varias veces: no duplica lo que ya existe.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import Servicio, Usuario

# Contraseña ficticia compartida por los usuarios de demostración. No es un secreto real.
CONTRASENA_DEMO = "Demo12345!"

SERVICIOS = [
    ("Actualización de información personal", "Corrección o actualización de datos personales.", True, "baja"),
    ("Atención de trámites generales", "Orientación y trámites administrativos no clasificados.", False, "baja"),
    ("Certificado de estudios", "Expedición de certificados de estudios y de notas.", True, "media"),
    ("Corrección de calificaciones", "Solicitud de revisión o corrección de una calificación.", True, "alta"),
    ("Solicitud de copia de documentos", "Copia de documentos del archivo institucional.", False, "media"),
]

USUARIOS = [
    ("Coordinación Académica", "coordinacion@ejemplo.edu", "coordinacion", None),
    ("Luis Gómez", "luis.gomez@ejemplo.edu", "atencion", None),
    ("María Ríos", "maria.rios@ejemplo.edu", "atencion", None),
    ("Ana Pérez", "ana.perez@ejemplo.edu", "solicitante", "estudiante"),
    ("Carlos Ruiz", "carlos.ruiz@ejemplo.edu", "solicitante", "docente"),
]


def sembrar(db: Session) -> tuple[int, int]:
    """Inserta los servicios y usuarios que falten. Devuelve cuántos creó de cada uno."""
    servicios_nuevos = 0
    for nombre, descripcion, requiere_adjunto, prioridad in SERVICIOS:
        if not db.scalar(select(Servicio).where(Servicio.nombre == nombre)):
            db.add(
                Servicio(
                    nombre=nombre,
                    descripcion=descripcion,
                    requiere_adjunto=requiere_adjunto,
                    prioridad_defecto=prioridad,
                )
            )
            servicios_nuevos += 1
    usuarios_nuevos = 0
    for nombre, correo, rol, tipo in USUARIOS:
        if not db.scalar(select(Usuario).where(Usuario.correo == correo)):
            db.add(
                Usuario(
                    nombre=nombre,
                    correo=correo,
                    password_hash=hash_password(CONTRASENA_DEMO),
                    rol=rol,
                    tipo_solicitante=tipo,
                )
            )
            usuarios_nuevos += 1
    db.commit()
    return servicios_nuevos, usuarios_nuevos


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as sesion:
        servicios_nuevos, usuarios_nuevos = sembrar(sesion)
    print(f"Servicios creados: {servicios_nuevos}. Usuarios creados: {usuarios_nuevos}.")
    print(f"\nUsuarios de demostración (contraseña: {CONTRASENA_DEMO})")
    for nombre, correo, rol, _tipo in USUARIOS:
        print(f"  {rol:<13} {correo:<28} {nombre}")
