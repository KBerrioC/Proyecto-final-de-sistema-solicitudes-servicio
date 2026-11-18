"""Pruebas funcionales de la API (docs/diseno.md, sección 4).

Uso, desde la raíz del repositorio y con el entorno virtual activado:
    pip install -r requirements-dev.txt
    python evidencias/probar_api.py

Usa una base de datos temporal (pruebas.db) que se borra al terminar. No toca app.db.
Cada línea muestra: estado, identificador, requisito, descripción, método y ruta,
código HTTP esperado y obtenido.
"""
import os
import re
import shutil
import sys
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.getcwd())
os.environ["DATABASE_URL"] = "sqlite:///./pruebas.db"
os.environ["SECRET_KEY"] = "clave-solo-para-las-pruebas-funcionales-0123456789"
os.environ["UPLOAD_DIR"] = "uploads/pruebas_tmp"
os.environ["MAX_UPLOAD_MB"] = "1"
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", message=".*httpx.*")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.config import configuracion  # noqa: E402
from backend.database import SessionLocal, engine  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import Adjunto, Evento, Servicio, Solicitud, Usuario  # noqa: E402
from backend.seed import CONTRASENA_DEMO, SERVICIOS  # noqa: E402

resultados = []


def probar(id_, requisito, descripcion, respuesta, esperado, condicion=True):
    solicitud = respuesta.request
    aprobada = respuesta.status_code == esperado and condicion
    resultados.append(aprobada)
    estado = "APROBADA" if aprobada else "FALLIDA"
    print(
        f"[{estado}] {id_} | {requisito} | {descripcion} | "
        f"{solicitud.method} {solicitud.url.path} | esperado {esperado}, obtenido {respuesta.status_code}"
    )


def encabezado(token):
    return {"Authorization": f"Bearer {token}"}


def iniciar_sesion(cliente, correo, password=CONTRASENA_DEMO):
    return cliente.post("/api/auth/login", data={"username": correo, "password": password})


try:
    with TestClient(app) as c:
        from backend.database import SessionLocal as Sesion
        from backend.seed import sembrar

        with Sesion() as db:
            sembrar(db)

        # --- Registro (EP-01)
        datos = {"nombre": "Ana Nueva", "correo": "ana.nueva@ejemplo.edu",
                 "password": "ClaveSegura1", "tipo_solicitante": "estudiante"}
        r = c.post("/api/auth/registro", json=datos)
        cuerpo = r.json() if r.status_code == 201 else {}
        probar("T-01", "RF-01", "Registro válido de solicitante", r, 201,
               cuerpo.get("rol") == "solicitante" and "password" not in cuerpo
               and "password_hash" not in cuerpo)

        r = c.post("/api/auth/registro", json={**datos, "correo": "otra@ejemplo.edu", "password": "123"})
        probar("T-02", "RF-01, RNF-02", "Registro con contraseña demasiado corta", r, 422)

        r = c.post("/api/auth/registro", json={**datos, "correo": "ANA.NUEVA@ejemplo.edu"})
        probar("T-03", "RF-01", "Registro con correo ya existente (sin distinguir mayúsculas)", r, 409)

        # --- Inicio de sesión (EP-02)
        r = iniciar_sesion(c, "ana.perez@ejemplo.edu")
        cuerpo = r.json() if r.status_code == 200 else {}
        token_ana = cuerpo.get("access_token", "")
        probar("T-04", "RF-02", "Inicio de sesión válido", r, 200,
               bool(token_ana) and cuerpo.get("usuario", {}).get("rol") == "solicitante")

        r1 = iniciar_sesion(c, "ana.perez@ejemplo.edu", "incorrecta")
        probar("T-05", "RF-02", "Inicio de sesión con contraseña incorrecta", r1, 401)

        r2 = iniciar_sesion(c, "no.existe@ejemplo.edu")
        probar("T-06", "RF-02, RNF-03", "Correo inexistente: mismo error que contraseña incorrecta", r2, 401,
               r1.json() == r2.json())

        # --- Perfil (EP-03) y sesión
        r = c.get("/api/auth/perfil")
        probar("T-07", "RF-03", "Perfil sin token", r, 401)

        r = c.get("/api/auth/perfil", headers=encabezado(token_ana))
        probar("T-08", "RF-02, RF-03", "Perfil con token válido", r, 200,
               r.status_code == 200 and r.json()["correo"] == "ana.perez@ejemplo.edu")

        r = c.get("/api/auth/perfil", headers=encabezado(token_ana[:-3] + "abc"))
        probar("T-09", "RNF-01", "Perfil con token manipulado", r, 401)

        vencido = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
            configuracion.secret_key, algorithm="HS256")
        r = c.get("/api/auth/perfil", headers=encabezado(vencido))
        probar("T-10", "RNF-01", "Perfil con token vencido", r, 401)

        # --- Catálogo de servicios (EP-04)
        r = c.get("/api/servicios")
        probar("T-11", "RF-04", "Catálogo de servicios sin token", r, 401)

        r = c.get("/api/servicios", headers=encabezado(token_ana))
        probar("T-12", "RF-04", "Catálogo de servicios con token", r, 200,
               r.status_code == 200 and len(r.json()) == len(SERVICIOS)
               and all("requiere_adjunto" in s for s in r.json()))

        # --- Control por rol (EP-05)
        r = c.get("/api/usuarios/atencion", headers=encabezado(token_ana))
        probar("T-13", "RF-03, RF-13", "Lista de atención con rol solicitante (no autorizado)", r, 403)

        token_luis = iniciar_sesion(c, "luis.gomez@ejemplo.edu").json()["access_token"]
        r = c.get("/api/usuarios/atencion", headers=encabezado(token_luis))
        probar("T-14", "RF-03, RF-13", "Lista de atención con rol atención", r, 200,
               r.status_code == 200 and {u["nombre"] for u in r.json()} == {"Luis Gómez", "María Ríos"})

        # --- Persistencia segura
        with SessionLocal() as db:
            usuario = db.query(Usuario).filter_by(correo="ana.nueva@ejemplo.edu").one()
            guardada_con_hash = usuario.password_hash.startswith("$2") and usuario.password_hash != "ClaveSegura1"
        r = c.get("/api/auth/perfil", headers=encabezado(token_ana))
        probar("T-15", "RNF-01", "La contraseña se guarda con hash, no en claro", r, 200, guardada_con_hash)

        # --- Creación de solicitudes (EP-06)
        PDF = b"%PDF-1.4\n" + b"contenido de prueba\n" * 20
        carpeta = Path(configuracion.upload_dir)

        def archivos_en_disco():
            return len([f for f in carpeta.glob("*") if f.is_file()]) if carpeta.exists() else 0

        def total_solicitudes():
            with SessionLocal() as db:
                return db.query(Solicitud).count()

        with SessionLocal() as db:
            id_sin_adjunto = db.query(Servicio).filter_by(nombre="Atención de trámites generales").one().id
            id_con_adjunto = db.query(Servicio).filter_by(nombre="Certificado de estudios").one().id
        base = {"servicio_id": id_sin_adjunto, "asunto": "Orientación sobre un trámite",
                "descripcion": "Necesito orientación sobre el trámite de matrícula."}
        auth_ana = encabezado(token_ana)

        r = c.post("/api/solicitudes", data=base, headers=auth_ana)
        cuerpo = r.json() if r.status_code == 201 else {}
        with SessionLocal() as db:
            eventos = db.query(Evento).filter_by(solicitud_id=cuerpo.get("id", 0), tipo="creada").count()
        probar("T-16", "RF-05, CA-01", "Registro válido de solicitud (sin adjunto)", r, 201,
               cuerpo.get("estado") == "recibida" and cuerpo.get("prioridad") == "baja"
               and bool(re.fullmatch(r"SOL-\d{4}-\d{5}", cuerpo.get("radicado", "")))
               and cuerpo.get("solicitante", {}).get("nombre") == "Ana Pérez"
               and cuerpo.get("adjuntos") == [] and cuerpo.get("dias_pendientes") == 0 and eventos == 1)
        primer_id = cuerpo.get("id")

        antes = total_solicitudes()
        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana)
        probar("T-17", "RN-06", "Servicio que exige adjunto, sin archivo (no se guarda nada)", r, 400,
               total_solicitudes() == antes)

        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana,
                   files=[("archivos", ("certificado.pdf", PDF, "application/pdf"))])
        cuerpo = r.json() if r.status_code == 201 else {}
        with SessionLocal() as db:
            adjunto = db.query(Adjunto).filter_by(solicitud_id=cuerpo.get("id", 0)).first()
            guardado = bool(adjunto) and (carpeta / adjunto.nombre_almacenado).exists()
            nombre_aleatorio = bool(adjunto) and adjunto.nombre_almacenado != "certificado.pdf"
        probar("T-18", "RF-06, RNF-05", "Registro con adjunto PDF (guardado con nombre aleatorio)", r, 201,
               len(cuerpo.get("adjuntos", [])) == 1
               and cuerpo["adjuntos"][0]["nombre_original"] == "certificado.pdf"
               and cuerpo["adjuntos"][0]["proposito"] == "solicitud" and guardado and nombre_aleatorio
               and cuerpo.get("prioridad") == "media")

        antes, discos = total_solicitudes(), archivos_en_disco()
        r = c.post("/api/solicitudes", data={**base, "asunto": "abc"}, headers=auth_ana)
        probar("T-19", "RF-05, RNF-02", "Registro con asunto demasiado corto (no se guarda)", r, 422,
               total_solicitudes() == antes)

        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana,
                   files=[("archivos", ("programa.exe", b"MZ" + b"0" * 50, "application/octet-stream"))])
        probar("T-20", "RNF-05", "Adjunto de tipo no permitido (.exe)", r, 415,
               total_solicitudes() == antes and archivos_en_disco() == discos)

        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana,
                   files=[("archivos", ("falso.pdf", b"MZ" + b"0" * 50, "application/pdf"))])
        probar("T-21", "RNF-05", "Archivo .pdf cuyo contenido no es un PDF", r, 415,
               total_solicitudes() == antes and archivos_en_disco() == discos)

        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana,
                   files=[("archivos", ("grande.pdf", b"%PDF-" + b"0" * (2 * 1024 * 1024), "application/pdf"))])
        probar("T-22", "RNF-05", "Adjunto mayor que el máximo permitido (1 MB en la prueba)", r, 413,
               total_solicitudes() == antes and archivos_en_disco() == discos)

        seis = [("archivos", (f"d{i}.pdf", PDF, "application/pdf")) for i in range(6)]
        r = c.post("/api/solicitudes", data={**base, "servicio_id": id_con_adjunto}, headers=auth_ana, files=seis)
        probar("T-23", "RNF-05", "Más archivos que el máximo permitido (6 de 5)", r, 400,
               total_solicitudes() == antes and archivos_en_disco() == discos)

        r = c.post("/api/solicitudes", data={**base, "servicio_id": 999}, headers=auth_ana)
        probar("T-24", "RF-05", "Servicio inexistente", r, 400, total_solicitudes() == antes)

        r = c.post("/api/solicitudes", data=base, headers=encabezado(token_luis))
        probar("T-25", "RF-03, CA-01", "Crear solicitud con rol atención (no autorizado)", r, 403,
               total_solicitudes() == antes)

        r = c.post("/api/solicitudes", data=base)
        probar("T-26", "RF-03", "Crear solicitud sin token", r, 401, total_solicitudes() == antes)

        r = c.post("/api/solicitudes", data=base, headers=auth_ana)
        segundo = r.json() if r.status_code == 201 else {}
        with SessionLocal() as db:
            filas = db.query(Solicitud).order_by(Solicitud.id).all()
            radicados = [f.radicado for f in filas]
            consistentes = all(f.solicitante.correo == "ana.perez@ejemplo.edu" for f in filas)
        probar("T-27", "RF-05, RNF-04", "Radicados únicos y solicitudes con su solicitante correcto", r, 201,
               len(set(radicados)) == len(radicados) == 3 and consistentes and segundo.get("id") != primer_id)
finally:
    engine.dispose()
    if os.path.exists("pruebas.db"):
        os.remove("pruebas.db")
    shutil.rmtree(os.environ["UPLOAD_DIR"], ignore_errors=True)

aprobadas = sum(resultados)
print(f"\nResultado: {aprobadas} de {len(resultados)} pruebas aprobadas")
sys.exit(0 if aprobadas == len(resultados) else 1)
