"""Verifica el modelo de datos: tablas, claves foráneas y restricciones.

Uso, desde la raíz del repositorio y con el entorno virtual activado:
    python evidencias/verificar_modelo.py

Usa una base de datos temporal (verificacion.db) que se borra al terminar.
No toca app.db.
"""
import os
import sys

sys.path.insert(0, os.getcwd())
os.environ["DATABASE_URL"] = "sqlite:///./verificacion.db"
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.exc import IntegrityError  # noqa: E402

from backend import models  # noqa: E402
from backend.database import Base, SessionLocal, engine  # noqa: E402

fallos = 0


def comprobar(descripcion: str, resultado: bool, detalle: str = "") -> None:
    global fallos
    estado = "APROBADA" if resultado else "FALLIDA"
    if not resultado:
        fallos += 1
    print(f"[{estado}] {descripcion}" + (f" -> {detalle}" if detalle else ""))


def debe_fallar(descripcion: str, db, accion) -> None:
    try:
        accion()
        db.commit()
        db.rollback()
        comprobar(descripcion, False, "la base de datos aceptó un dato inválido")
    except IntegrityError as error:
        db.rollback()
        comprobar(descripcion, True, str(error.orig))


try:
    Base.metadata.create_all(bind=engine)
    tablas = sorted(Base.metadata.tables)
    comprobar(
        "Se crean las cinco tablas",
        tablas == ["adjuntos", "eventos", "servicios", "solicitudes", "usuarios"],
        ", ".join(tablas),
    )
    with engine.connect() as conexion:
        activas = conexion.exec_driver_sql("PRAGMA foreign_keys").scalar()
    comprobar("Las claves foráneas están activas", activas == 1)

    db = SessionLocal()
    debe_fallar(
        "Rechaza una solicitud con solicitante y servicio inexistentes",
        db,
        lambda: db.add(
            models.Solicitud(
                radicado="SOL-2026-00001",
                solicitante_id=99,
                servicio_id=99,
                asunto="Asunto de prueba",
                descripcion="Descripción de prueba",
            )
        ),
    )
    debe_fallar(
        "Rechaza un rol inválido",
        db,
        lambda: db.add(
            models.Usuario(nombre="Ana", correo="a@x.com", password_hash="h", rol="admin")
        ),
    )

    ana = models.Usuario(
        nombre="Ana", correo="ana@ejemplo.com", password_hash="h",
        rol="solicitante", tipo_solicitante="estudiante",
    )
    luis = models.Usuario(
        nombre="Luis", correo="luis@ejemplo.com", password_hash="h", rol="atencion"
    )
    servicio = models.Servicio(nombre="Certificado de estudios", requiere_adjunto=True)
    db.add_all([ana, luis, servicio])
    db.commit()

    solicitud = models.Solicitud(
        radicado="SOL-2026-00001", solicitante_id=ana.id, servicio_id=servicio.id,
        asunto="Certificado para beca", descripcion="Necesito un certificado.",
        responsable_id=luis.id,
    )
    db.add(solicitud)
    db.commit()
    db.add(models.Evento(solicitud_id=solicitud.id, autor_id=ana.id, tipo="creada",
                         estado_nuevo="recibida"))
    db.add(models.Adjunto(solicitud_id=solicitud.id, subido_por_id=ana.id,
                          proposito="solicitud", nombre_original="documento.pdf",
                          nombre_almacenado="a1b2c3.pdf", tipo_mime="application/pdf",
                          tamano_bytes=1024))
    db.commit()
    db.refresh(solicitud)
    comprobar(
        "Una solicitud válida se guarda con su estado inicial y sus relaciones",
        solicitud.estado == "recibida"
        and solicitud.solicitante.nombre == "Ana"
        and solicitud.responsable.nombre == "Luis"
        and len(solicitud.eventos) == 1
        and len(solicitud.adjuntos) == 1,
        f"estado={solicitud.estado}, prioridad={solicitud.prioridad}",
    )
    debe_fallar(
        "Rechaza borrar un usuario que tiene solicitudes (ON DELETE RESTRICT)",
        db,
        lambda: db.delete(ana),
    )
    db.close()
finally:
    engine.dispose()
    if os.path.exists("verificacion.db"):
        os.remove("verificacion.db")

print()
print("Resultado:", "todas las verificaciones aprobadas" if fallos == 0 else f"{fallos} fallidas")
sys.exit(1 if fallos else 0)
