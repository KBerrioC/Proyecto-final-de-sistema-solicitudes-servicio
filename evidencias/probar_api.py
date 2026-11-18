"""Pruebas funcionales de la API (docs/diseno.md, sección 4).

Uso, desde la raíz del repositorio y con el entorno virtual activado:
    pip install -r requirements-dev.txt
    python evidencias/probar_api.py

Usa una base de datos temporal (pruebas.db) que se borra al terminar. No toca app.db.
Cada línea muestra: estado, identificador, requisito, descripción, método y ruta,
código HTTP esperado y obtenido.
"""
import os
import sys
import warnings
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.getcwd())
os.environ["DATABASE_URL"] = "sqlite:///./pruebas.db"
os.environ["SECRET_KEY"] = "clave-solo-para-las-pruebas-funcionales-0123456789"
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", message=".*httpx.*")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.config import configuracion  # noqa: E402
from backend.database import SessionLocal, engine  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import Usuario  # noqa: E402
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
finally:
    engine.dispose()
    if os.path.exists("pruebas.db"):
        os.remove("pruebas.db")

aprobadas = sum(resultados)
print(f"\nResultado: {aprobadas} de {len(resultados)} pruebas aprobadas")
sys.exit(0 if aprobadas == len(resultados) else 1)
