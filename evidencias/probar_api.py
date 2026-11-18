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
        # --- Consulta de solicitudes (EP-07, EP-08, EP-16 y EP-17)
        from backend.models import Evento as Ev

        token_carlos = iniciar_sesion(c, "carlos.ruiz@ejemplo.edu").json()["access_token"]
        token_maria = iniciar_sesion(c, "maria.rios@ejemplo.edu").json()["access_token"]
        token_coord = iniciar_sesion(c, "coordinacion@ejemplo.edu").json()["access_token"]
        r = c.post("/api/solicitudes", data={**base, "asunto": "Consulta de Carlos sobre un trámite"},
                   headers=encabezado(token_carlos))
        id_carlos = r.json()["id"]

        with SessionLocal() as db:
            ana = db.query(Usuario).filter_by(correo="ana.perez@ejemplo.edu").one()
            luis = db.query(Usuario).filter_by(correo="luis.gomez@ejemplo.edu").one()
            ids_ana = [s.id for s in db.query(Solicitud).filter_by(solicitante_id=ana.id).order_by(Solicitud.id)]
            id_adjunto = db.query(Adjunto).first().id
            id_solicitud_adjunto = db.query(Adjunto).first().solicitud_id

        r = c.get("/api/solicitudes", headers=auth_ana)
        cuerpo = r.json() if r.status_code == 200 else {}
        ids = [i["id"] for i in cuerpo.get("items", [])]
        probar("T-28", "RF-07, RF-19, CA-03", "El solicitante lista solo sus solicitudes, de más reciente a más antigua", r, 200,
               cuerpo.get("total") == len(ids_ana) and ids == sorted(ids_ana, reverse=True)
               and all("solicitante" not in i for i in cuerpo["items"]))

        r = c.get("/api/solicitudes", headers=encabezado(token_carlos))
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-29", "RF-19", "Otro solicitante solo ve la suya", r, 200,
               cuerpo.get("total") == 1 and cuerpo["items"][0]["id"] == id_carlos)

        r = c.get("/api/solicitudes", headers=encabezado(token_luis))
        cuerpo = r.json() if r.status_code == 200 else {}
        rango = {"alta": 0, "media": 1, "baja": 2}
        prioridades = [rango[i["prioridad"]] for i in cuerpo.get("items", [])]
        probar("T-30", "RF-09, RF-19", "El personal ve la bandeja de todos los solicitantes, ordenada por prioridad", r, 200,
               cuerpo.get("total") == len(ids_ana) + 1 and prioridades == sorted(prioridades)
               and all("solicitante" in i for i in cuerpo["items"]))

        r = c.get("/api/solicitudes", params={"prioridad": "media"}, headers=encabezado(token_luis))
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-31", "RF-09", "Filtro por prioridad", r, 200,
               cuerpo.get("total", 0) >= 1 and all(i["prioridad"] == "media" for i in cuerpo["items"]))

        r = c.get("/api/solicitudes", params={"limite": 2, "desplazamiento": 1}, headers=encabezado(token_luis))
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-32", "RF-07", "Paginación con límite y desplazamiento", r, 200,
               len(cuerpo.get("items", [])) == 2 and cuerpo.get("total") == len(ids_ana) + 1)

        r = c.get("/api/solicitudes", params={"limite": 101}, headers=auth_ana)
        probar("T-33", "RF-07", "Límite de página superior al máximo", r, 422)

        r = c.get("/api/solicitudes", params={"estado": "inventado"}, headers=auth_ana)
        probar("T-34", "RF-07", "Filtro con un estado que no existe", r, 422)

        r = c.get("/api/solicitudes")
        probar("T-35", "RF-03", "Listar sin token", r, 401)

        r = c.get(f"/api/solicitudes/{ids_ana[0]}", headers=auth_ana)
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-36", "RF-07, CA-03", "Detalle de una solicitud propia", r, 200,
               cuerpo.get("id") == ids_ana[0] and cuerpo.get("estado") == "recibida"
               and cuerpo.get("solicitante", {}).get("nombre") == "Ana Pérez")

        r = c.get(f"/api/solicitudes/{id_carlos}", headers=auth_ana)
        r2 = c.get("/api/solicitudes/99999", headers=auth_ana)
        probar("T-37", "RF-19, RNF-02", "Detalle de una solicitud ajena responde 404, igual que una inexistente", r, 404,
               r2.status_code == 404 and r.json() == r2.json())

        # Una solicitud en gestión asignada a Luis, con una nota interna.
        with SessionLocal() as db:
            gestion = Solicitud(radicado="SOL-2026-09001", solicitante_id=ana.id, servicio_id=id_sin_adjunto,
                                asunto="Solicitud en gestión de prueba", descripcion="Descripción de prueba.",
                                estado="en_gestion", prioridad="alta", responsable_id=luis.id)
            db.add(gestion)
            db.flush()
            db.add(Ev(solicitud_id=gestion.id, autor_id=ana.id, tipo="creada", estado_nuevo="recibida"))
            db.add(Ev(solicitud_id=gestion.id, autor_id=luis.id, tipo="nota", detalle="Nota interna de prueba",
                      visible_solicitante=False))
            db.commit()
            id_gestion = gestion.id

        r_maria = c.get(f"/api/solicitudes/{id_gestion}", headers=encabezado(token_maria))
        r_luis = c.get(f"/api/solicitudes/{id_gestion}", headers=encabezado(token_luis))
        r_coord = c.get(f"/api/solicitudes/{id_gestion}", headers=encabezado(token_coord))
        probar("T-38", "RF-19, SUP-10", "En gestión: no la ve otro funcionario, sí el responsable y coordinación",
               r_maria, 404, r_luis.status_code == 200 and r_coord.status_code == 200)

        r = c.get("/api/solicitudes", params={"estado": "en_gestion"}, headers=encabezado(token_maria))
        probar("T-39", "RF-19", "El listado de otro funcionario no incluye la que está en gestión", r, 200,
               r.json()["total"] == 0)

        r = c.get(f"/api/solicitudes/{id_gestion}/eventos", headers=auth_ana)
        cuerpo = r.json() if r.status_code == 200 else []
        probar("T-40", "RF-17, RN-05, CA-04", "El solicitante no recibe las notas internas del historial", r, 200,
               [e["tipo"] for e in cuerpo] == ["creada"] and all("visible_solicitante" not in e for e in cuerpo))

        r = c.get(f"/api/solicitudes/{id_gestion}/eventos", headers=encabezado(token_luis))
        cuerpo = r.json() if r.status_code == 200 else []
        probar("T-41", "RF-17, RN-05, CA-04", "El personal ve el historial completo, con las notas internas", r, 200,
               [e["tipo"] for e in cuerpo] == ["creada", "nota"] and cuerpo[1]["visible_solicitante"] is False
               and cuerpo[1]["autor"]["nombre"] == "Luis Gómez")

        r = c.get(f"/api/solicitudes/{id_carlos}/eventos", headers=auth_ana)
        probar("T-42", "RF-19, RNF-02", "Historial de una solicitud ajena", r, 404)

        r = c.get(f"/api/adjuntos/{id_adjunto}", headers=auth_ana)
        probar("T-43", "RF-06, RNF-05", "El dueño descarga su adjunto con su nombre original", r, 200,
               r.content == PDF and "certificado.pdf" in r.headers.get("content-disposition", "")
               and r.headers.get("content-type") == "application/pdf")

        r = c.get(f"/api/adjuntos/{id_adjunto}", headers=encabezado(token_luis))
        probar("T-44", "RF-06, RNF-05", "El personal que ve la solicitud también descarga el adjunto", r, 200,
               r.content == PDF)

        r = c.get(f"/api/adjuntos/{id_adjunto}", headers=encabezado(token_carlos))
        probar("T-45", "RNF-05", "Otro solicitante no puede descargar el adjunto (404)", r, 404)

        r = c.get(f"/api/adjuntos/{id_adjunto}")
        probar("T-46", "RNF-05", "Descargar sin token", r, 401)

        # --- Gestión de solicitudes (EP-09 a EP-15)
        with SessionLocal() as db:
            maria = db.query(Usuario).filter_by(correo="maria.rios@ejemplo.edu").one()
            coord = db.query(Usuario).filter_by(correo="coordinacion@ejemplo.edu").one()
            id_maria, id_coord = maria.id, coord.id
        auth_luis, auth_maria = encabezado(token_luis), encabezado(token_maria)
        auth_coord, auth_carlos = encabezado(token_coord), encabezado(token_carlos)

        def nueva(asunto="Solicitud de prueba de gestión", cabecera=auth_ana):
            return c.post("/api/solicitudes", data={**base, "asunto": asunto}, headers=cabecera).json()["id"]

        def eventos(id_, cabecera):
            return c.get(f"/api/solicitudes/{id_}/eventos", headers=cabecera).json()

        def tipos(id_, cabecera):
            return [e["tipo"] for e in eventos(id_, cabecera)]

        def estado(id_):
            with SessionLocal() as db:
                return db.get(Solicitud, id_).estado

        # Flujo completo de la solicitud principal: recibida -> evaluación -> información -> gestión -> finalizada
        s1 = nueva("Certificado para trámite de beca")
        r = c.patch(f"/api/solicitudes/{s1}/estado", json={"estado": "en_evaluacion"}, headers=auth_luis)
        probar("T-47", "RF-10, CA-02", "El personal inicia la evaluación (recibida -> en evaluación)", r, 200,
               r.json().get("estado") == "en_evaluacion"
               and tipos(s1, auth_luis) == ["creada", "evaluacion_iniciada"])

        r = c.patch(f"/api/solicitudes/{s1}/estado", json={"estado": "en_evaluacion"}, headers=auth_ana)
        probar("T-48", "RF-03, RF-10", "El solicitante intenta evaluar su solicitud (no autorizado)", r, 403,
               estado(s1) == "en_evaluacion")

        r = c.patch(f"/api/solicitudes/{s1}/estado", json={"estado": "finalizada"}, headers=auth_luis)
        probar("T-49", "RN-01", "Pedir «finalizada» por EP-09 (tiene su propio endpoint)", r, 422)

        s2 = nueva("Solicitud para probar transiciones")
        r = c.patch(f"/api/solicitudes/{s2}/estado",
                    json={"estado": "en_gestion", "responsable_id": id_maria}, headers=auth_luis)
        probar("T-50", "RN-01", "Saltar de «recibida» a «en gestión» (transición no permitida)", r, 409,
               estado(s2) == "recibida")

        r = c.patch(f"/api/solicitudes/{s1}/estado", json={"estado": "pendiente_informacion"}, headers=auth_luis)
        probar("T-51", "RN-02", "Pedir información sin indicar el motivo", r, 400, estado(s1) == "en_evaluacion")

        r = c.patch(f"/api/solicitudes/{s1}/estado",
                    json={"estado": "pendiente_informacion", "motivo": "Adjunte la constancia de matrícula."},
                    headers=auth_luis)
        vistos = eventos(s1, auth_ana)
        probar("T-52", "RF-11, RF-17", "Pedir información (el solicitante ve el motivo en su historial)", r, 200,
               r.json().get("estado") == "pendiente_informacion"
               and vistos[-1]["tipo"] == "informacion_solicitada"
               and vistos[-1]["detalle"] == "Adjunte la constancia de matrícula.")

        r = c.post(f"/api/solicitudes/{s1}/informacion", headers=auth_carlos, data={"texto": "Ya la adjunto."})
        probar("T-53", "RF-11", "Otro solicitante intenta responder la petición (404)", r, 404)

        r = c.post(f"/api/solicitudes/{s1}/informacion", headers=auth_ana)
        probar("T-54", "RF-11", "Responder la petición sin texto ni archivo", r, 422, estado(s1) == "pendiente_informacion")

        r = c.post(f"/api/solicitudes/{s1}/informacion", headers=auth_ana, data={"texto": "Adjunto la constancia."},
                   files=[("archivos", ("constancia.pdf", PDF, "application/pdf"))])
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-55", "RF-11, CA-02", "El solicitante entrega la información (vuelve a evaluación)", r, 200,
               cuerpo.get("estado") == "en_evaluacion"
               and [a["proposito"] for a in cuerpo.get("adjuntos", [])] == ["informacion"]
               and tipos(s1, auth_luis)[-1] == "informacion_recibida")

        r = c.post(f"/api/solicitudes/{s1}/informacion", headers=auth_ana, data={"texto": "Otra vez."})
        probar("T-56", "RN-01", "Entregar información cuando ya no se espera (409)", r, 409)

        r = c.patch(f"/api/solicitudes/{s1}/estado", json={"estado": "en_gestion"}, headers=auth_luis)
        probar("T-57", "RN-03", "Aceptar sin indicar responsable", r, 400, estado(s1) == "en_evaluacion")

        r = c.patch(f"/api/solicitudes/{s1}/estado",
                    json={"estado": "en_gestion", "responsable_id": id_coord}, headers=auth_luis)
        probar("T-58", "RN-07", "Asignar como responsable a alguien que no es de atención", r, 400,
               estado(s1) == "en_evaluacion")

        r = c.patch(f"/api/solicitudes/{s1}/estado",
                    json={"estado": "en_gestion", "responsable_id": id_maria, "prioridad": "alta"},
                    headers=auth_luis)
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-59", "RF-12, RN-03, RN-08, RN-09", "Aceptar y asignar (queda en gestión con responsable y prioridad)", r, 200,
               cuerpo.get("estado") == "en_gestion" and cuerpo.get("responsable", {}).get("nombre") == "María Ríos"
               and cuerpo.get("prioridad") == "alta"
               and tipos(s1, auth_maria)[-3:] == ["aceptada", "asignada", "prioridad_cambiada"])

        interno = {"asignada", "prioridad_cambiada"}
        vistos_ana = tipos(s1, auth_ana)
        r = c.get(f"/api/solicitudes/{s1}/eventos", headers=auth_ana)
        probar("T-60", "RN-05", "El solicitante ve la aceptación pero no la asignación ni el cambio de prioridad", r, 200,
               "aceptada" in vistos_ana and not interno & set(vistos_ana))

        r = c.post(f"/api/solicitudes/{s1}/finalizacion", data={"respuesta": "Su certificado fue emitido."}, headers=auth_luis)
        probar("T-61", "SUP-10", "Otro funcionario no ve la solicitud en gestión (404)", r, 404)

        r = c.post(f"/api/solicitudes/{s1}/finalizacion", data={"respuesta": "Corta"}, headers=auth_maria)
        probar("T-62", "RN-04", "Finalizar con una respuesta demasiado corta", r, 422, estado(s1) == "en_gestion")

        r = c.post(f"/api/solicitudes/{s1}/finalizacion", data={"respuesta": "Su certificado fue emitido."},
                   headers=auth_maria, files=[("archivo", ("programa.exe", b"MZ" + b"0" * 50, "application/octet-stream"))])
        probar("T-63", "RNF-05", "Finalizar con un adjunto no permitido (no cambia nada)", r, 415,
               estado(s1) == "en_gestion" and tipos(s1, auth_maria)[-1] == "prioridad_cambiada")

        r = c.post(f"/api/solicitudes/{s1}/finalizacion",
                   data={"respuesta": "Su certificado de estudios fue emitido y está adjunto."},
                   headers=auth_maria, files=[("archivo", ("certificado-emitido.pdf", PDF, "application/pdf"))])
        cuerpo = r.json() if r.status_code == 200 else {}
        probar("T-64", "RF-14, RN-04, CA-05", "El responsable finaliza con respuesta y archivo", r, 200,
               cuerpo.get("estado") == "finalizada" and bool(cuerpo.get("respuesta"))
               and cuerpo.get("finalizado_en") is not None and cuerpo.get("dias_pendientes") is None
               and cuerpo.get("dias_atencion") == 0
               and [a["proposito"] for a in cuerpo.get("adjuntos", [])] == ["informacion", "respuesta"]
               and tipos(s1, auth_ana)[-1] == "finalizada")
        id_respuesta = [a["id"] for a in cuerpo.get("adjuntos", []) if a["proposito"] == "respuesta"][0]

        r = c.get(f"/api/adjuntos/{id_respuesta}", headers=auth_ana)
        probar("T-65", "CA-05, RNF-05", "El solicitante descarga el archivo de respuesta", r, 200,
               r.content == PDF and "certificado-emitido.pdf" in r.headers.get("content-disposition", ""))

        r = c.post(f"/api/solicitudes/{s1}/notas", json={"texto": "Nota tardía"}, headers=auth_coord)
        r2 = c.patch(f"/api/solicitudes/{s1}/prioridad", json={"prioridad": "baja", "motivo": "Ya no aplica"}, headers=auth_coord)
        r3 = c.post(f"/api/solicitudes/{s1}/cancelacion", headers=auth_ana)
        probar("T-66", "RN-12", "Una solicitud finalizada ya no admite notas, prioridad ni cancelación", r, 409,
               r2.status_code == 409 and r3.status_code == 409 and estado(s1) == "finalizada")

        # Reasignación (EP-11)
        s3 = nueva("Solicitud para reasignar")
        c.patch(f"/api/solicitudes/{s3}/estado", json={"estado": "en_evaluacion"}, headers=auth_luis)
        c.patch(f"/api/solicitudes/{s3}/estado", json={"estado": "en_gestion", "responsable_id": id_maria}, headers=auth_luis)
        r = c.patch(f"/api/solicitudes/{s3}/responsable", json={"responsable_id": luis.id, "motivo": "Carga de trabajo"},
                    headers=auth_coord)
        ultimo = eventos(s3, auth_coord)[-1]
        with SessionLocal() as db:
            ev = db.query(Evento).filter_by(solicitud_id=s3, tipo="reasignada").one()
            de_a = (ev.de_responsable_id, ev.a_responsable_id)
        probar("T-67", "RF-13, RN-08", "Coordinación reasigna y queda registrado de quién a quién", r, 200,
               r.json().get("responsable", {}).get("nombre") == "Luis Gómez" and de_a == (id_maria, luis.id)
               and ultimo["tipo"] == "reasignada")

        r = c.patch(f"/api/solicitudes/{s3}/responsable", json={"responsable_id": luis.id}, headers=auth_coord)
        probar("T-68", "RN-07", "Reasignar a quien ya es el responsable", r, 400)

        r = c.patch(f"/api/solicitudes/{s3}/responsable", json={"responsable_id": ana.id}, headers=auth_coord)
        probar("T-69", "RN-07", "Reasignar a alguien que no es de atención", r, 400)

        r = c.patch(f"/api/solicitudes/{s3}/responsable", json={"responsable_id": id_maria}, headers=auth_maria)
        probar("T-70", "SUP-10", "El responsable anterior ya no ve ni reasigna la solicitud (404)", r, 404)

        # Prioridad y notas (EP-12 y EP-13)
        s4 = nueva("Solicitud para prioridad y notas")
        c.patch(f"/api/solicitudes/{s4}/estado", json={"estado": "en_evaluacion"}, headers=auth_luis)
        r = c.patch(f"/api/solicitudes/{s4}/prioridad", json={"prioridad": "alta", "motivo": "Vence el plazo"}, headers=auth_luis)
        probar("T-71", "RN-09, SUP-10", "Atención no ajusta la prioridad de una solicitud que no tiene asignada", r, 403)

        r = c.patch(f"/api/solicitudes/{s4}/prioridad", json={"prioridad": "alta"}, headers=auth_coord)
        probar("T-72", "RN-09", "Ajustar la prioridad sin motivo", r, 422)

        r = c.patch(f"/api/solicitudes/{s4}/prioridad", json={"prioridad": "alta", "motivo": "Vence el plazo"}, headers=auth_coord)
        probar("T-73", "RF-12, RN-09", "Coordinación ajusta la prioridad con motivo", r, 200,
               r.json().get("prioridad") == "alta" and "Vence el plazo" in eventos(s4, auth_coord)[-1]["detalle"])

        c.patch(f"/api/solicitudes/{s4}/estado", json={"estado": "en_gestion", "responsable_id": id_maria}, headers=auth_luis)
        r = c.post(f"/api/solicitudes/{s4}/notas", json={"texto": "Llamar al solicitante"}, headers=auth_maria)
        interna = r.json() if r.status_code == 201 else {}
        r2 = c.post(f"/api/solicitudes/{s4}/notas", json={"texto": "Estamos revisando su caso", "visible_solicitante": True},
                    headers=auth_maria)
        detalles_ana = [e["detalle"] for e in eventos(s4, auth_ana)]
        probar("T-74", "RN-05, RF-17", "Notas: la interna no la ve el solicitante, la marcada como visible sí", r, 201,
               interna.get("visible_solicitante") is False and r2.status_code == 201
               and "Estamos revisando su caso" in detalles_ana and "Llamar al solicitante" not in detalles_ana)

        r = c.post(f"/api/solicitudes/{s4}/notas", json={"texto": "x"}, headers=auth_maria)
        probar("T-75", "RF-12", "Nota demasiado corta", r, 422)

        # Rechazo, cancelación y coordinación
        s5 = nueva("Solicitud para rechazar")
        c.patch(f"/api/solicitudes/{s5}/estado", json={"estado": "en_evaluacion"}, headers=auth_maria)
        r = c.patch(f"/api/solicitudes/{s5}/estado", json={"estado": "rechazada"}, headers=auth_maria)
        probar("T-76", "RN-02", "Rechazar sin indicar el motivo", r, 400, estado(s5) == "en_evaluacion")

        r = c.patch(f"/api/solicitudes/{s5}/estado",
                    json={"estado": "rechazada", "motivo": "No corresponde a este servicio."}, headers=auth_maria)
        probar("T-77", "RF-10, RN-12", "Rechazar con motivo (estado final)", r, 200,
               r.json().get("estado") == "rechazada" and r.json().get("dias_pendientes") is None)

        r = c.patch(f"/api/solicitudes/{s5}/estado", json={"estado": "en_evaluacion"}, headers=auth_coord)
        probar("T-78", "RN-12", "Una solicitud rechazada no puede volver a evaluarse", r, 409)

        s6 = nueva("Solicitud para cancelar")
        r = c.post(f"/api/solicitudes/{s6}/cancelacion", headers=auth_carlos)
        probar("T-79", "RF-15, RNF-02", "Otro solicitante intenta cancelar una solicitud ajena (404)", r, 404,
               estado(s6) == "recibida")

        r = c.post(f"/api/solicitudes/{s6}/cancelacion", json={"motivo": "Ya no la necesito"}, headers=auth_ana)
        probar("T-80", "RF-15, RN-11", "El solicitante cancela antes de la gestión", r, 200,
               r.json().get("estado") == "cancelada" and tipos(s6, auth_ana)[-1] == "cancelada")

        r = c.post(f"/api/solicitudes/{s4}/cancelacion", headers=auth_ana)
        probar("T-81", "RN-11", "Cancelar una solicitud que ya está en gestión (409)", r, 409, estado(s4) == "en_gestion")

        r = c.post(f"/api/solicitudes/{s4}/finalizacion", data={"respuesta": "Resuelto por coordinación."}, headers=auth_coord)
        probar("T-82", "RF-13, RN-04", "Coordinación puede finalizar una solicitud que no tiene asignada", r, 200,
               r.json().get("estado") == "finalizada")

        r = c.patch(f"/api/solicitudes/{s2}/estado", json={"estado": "en_evaluacion"})
        probar("T-83", "RF-03", "Gestionar sin token", r, 401)

        # --- Resumen para coordinación (EP-18)
        r = c.get("/api/resumen", headers=auth_coord)
        res = r.json() if r.status_code == 200 else {}
        with SessionLocal() as db:
            total_bd = db.query(Solicitud).count()
            finalizadas_bd = db.query(Solicitud).filter_by(estado="finalizada").count()
        probar("T-84", "RF-18, CA-06", "Coordinación consulta el resumen (conteos consistentes con la base de datos)", r, 200,
               res.get("total") == total_bd == sum(res.get("por_estado", {}).values())
               and res["por_estado"]["finalizada"] == finalizadas_bd
               and sum(x["total"] for x in res["por_servicio"]) == total_bd
               and set(res["por_estado"]) == {"recibida", "en_evaluacion", "pendiente_informacion",
                                              "en_gestion", "finalizada", "rechazada", "cancelada"})

        probar("T-85", "RF-18, RN-10", "Tiempo promedio de atención y responsables en el resumen", r, 200,
               res.get("tiempo_promedio_atencion_dias") is not None
               and {x["responsable"] for x in res["por_responsable"]} >= {"María Ríos", "Luis Gómez"})

        dias = [x["dias_pendientes"] for x in res.get("pendientes_mas_antiguas", [])]
        probar("T-86", "RF-18, RF-19", "Las pendientes más antiguas excluyen estados finales y son 10 como máximo", r, 200,
               len(dias) <= 10 and dias == sorted(dias, reverse=True)
               and all(x["estado"] not in ("finalizada", "rechazada", "cancelada")
                       for x in res["pendientes_mas_antiguas"]))

        hoy = datetime.now(timezone.utc).date()
        r = c.get("/api/resumen", params={"hasta": str(hoy - timedelta(days=1))}, headers=auth_coord)
        r2 = c.get("/api/resumen", params={"desde": str(hoy)}, headers=auth_coord)
        probar("T-87", "RF-18", "Filtro por fechas (ayer o antes: 0 solicitudes; desde hoy: todas)", r, 200,
               r.json().get("total") == 0 and r2.json().get("total") == total_bd
               and r2.json().get("tiempo_promedio_atencion_dias") is not None)

        r = c.get("/api/resumen", params={"desde": "2026-12-31", "hasta": "2026-01-01"}, headers=auth_coord)
        probar("T-88", "RF-18", "Rango de fechas invertido", r, 422)

        r = c.get("/api/resumen", headers=auth_luis)
        r2 = c.get("/api/resumen", headers=auth_ana)
        probar("T-89", "RF-03, RF-18", "Atención y solicitante no acceden al resumen", r, 403, r2.status_code == 403)

        r = c.get("/api/resumen")
        probar("T-90", "RF-03", "Resumen sin token", r, 401)

finally:
    engine.dispose()
    if os.path.exists("pruebas.db"):
        os.remove("pruebas.db")
    shutil.rmtree(os.environ["UPLOAD_DIR"], ignore_errors=True)

aprobadas = sum(resultados)
print(f"\nResultado: {aprobadas} de {len(resultados)} pruebas aprobadas")
sys.exit(0 if aprobadas == len(resultados) else 1)
