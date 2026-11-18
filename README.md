# Sistema de gestión de solicitudes de servicio

Proyecto Final 01 (PF-01) de Aplicaciones y Servicios Web. Aplicación web con interfaz, API REST y base de datos para registrar y dar seguimiento a solicitudes de servicio de una institución educativa.

## Contenido

1. [Información general](#1-información-general)
2. [Descripción del sistema](#2-descripción-del-sistema)
3. [Requisitos y alcance](#3-requisitos-y-alcance)
4. [Arquitectura, diseño de API y modelo de datos](#4-arquitectura-diseño-de-api-y-modelo-de-datos)
5. [Configuración del entorno](#5-configuración-del-entorno)
6. [Servicios web implementados](#6-servicios-web-implementados)
7. [Pruebas de API e integración y evidencias de funcionamiento](#7-pruebas-de-api-e-integración-y-evidencias-de-funcionamiento)
8. [Control de versiones](#8-control-de-versiones)
9. [Conclusiones y limitaciones](#9-conclusiones-y-limitaciones)

## 1. Información general

- **Proyecto:** sistema de gestión de solicitudes de servicio.
- **Asignatura:** Aplicaciones y Servicios Web, programa de Tecnología en Desarrollo de Software.
- **Integrante y contribución:** Berrio (GitHub: [KBerrioC](https://github.com/KBerrioC)). Proyecto individual: análisis de requisitos, diseño, backend, frontend, pruebas y documentación.
- **Fecha:** 18 de noviembre de 2026.
- **Repositorio:** https://github.com/KBerrioC/Proyecto-final-de-sistema-solicitudes-servicio

## 2. Descripción del sistema

**Problema.** Una institución educativa recibe solicitudes de servicios administrativos (certificados, actualización de información, documentos y trámites generales) por correo, llamadas y mensajes, sin trazabilidad. Los solicitantes no saben el estado de su trámite y el personal no tiene una vista consolidada.

**Actores.**
- Solicitante: presenta solicitudes y consulta su estado y respuesta.
- Personal de atención: evalúa, gestiona y finaliza solicitudes.
- Coordinación: supervisa el proceso, reasigna y consulta el resumen consolidado.

**Resumen de la solución.** Una aplicación web donde el solicitante registra una solicitud (con adjuntos cuando el servicio lo requiere), el personal la evalúa, la asigna y la gestiona hasta responderla, y coordinación consulta el estado general. Cada acción queda registrada en un historial.

**Fuera de alcance.** Facturación, pagos, WhatsApp, envío real de correos, integración con plataformas externas y reapertura de solicitudes finalizadas.

Detalle completo: [docs/requisitos.md](docs/requisitos.md).

## 3. Requisitos y alcance

- **Método de levantamiento:** entrevista con el docente en el rol de representante de la organización, por el chat de Teams, en tres rondas.
- **Evidencia y decisiones confirmadas:** [docs/entrevista.md](docs/entrevista.md).
- **Requisitos, reglas de negocio, historias de usuario y criterios de aceptación:** [docs/requisitos.md](docs/requisitos.md) (19 requisitos funcionales, 10 no funcionales, 12 reglas de negocio y 10 historias de usuario).
- **Supuestos no confirmados con el docente:** sección 9 de [docs/requisitos.md](docs/requisitos.md).

## 4. Arquitectura, diseño de API y modelo de datos

La aplicación es cliente-servidor y se ejecuta en un solo proceso: FastAPI expone la API REST y entrega los archivos estáticos del frontend. Los datos se guardan en SQLite y los adjuntos, en la carpeta `uploads/`.

| Capa | Tecnología | Razón |
|---|---|---|
| Frontend | HTML, CSS y JavaScript con `fetch` | No requiere compilación ni un segundo servidor; consume la API real |
| Backend | Python y FastAPI | Validación con Pydantic y documentación OpenAPI automática |
| Base de datos | SQLite con SQLAlchemy | Un solo archivo, sin instalación; claves foráneas activas |
| Seguridad | JWT, bcrypt y roles | Contraseñas con hash y permisos validados en el servidor |

- **Diseño completo** (decisiones, arquitectura, modelo de datos con sus cinco tablas, especificación de los 19 endpoints, reglas y control de acceso, interfaces y prototipos): [docs/diseno.md](docs/diseno.md).
- **Estructura del código:** `backend/` (API, modelos, servicios y rutas), `frontend/` (seis pantallas), `evidencias/` (pruebas y capturas) y `docs/`.

## 5. Configuración del entorno

**Requisitos:** Python (desarrollado con 3.14 y probado también con 3.13) y Git.

**Instalación y ejecución en Windows (PowerShell):**

```powershell
git clone https://github.com/KBerrioC/Proyecto-final-de-sistema-solicitudes-servicio.git
cd Proyecto-final-de-sistema-solicitudes-servicio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

En Linux o macOS: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements-dev.txt` y `cp .env.example .env`.

**Variables de entorno** (archivo `.env`, que no se sube al repositorio):

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave para firmar los tokens. Obligatoria, de al menos 32 caracteres | `.env.example` trae un valor de relleno: cámbielo |
| `DATABASE_URL` | Base de datos | `sqlite:///./app.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración de la sesión | `30` |
| `UPLOAD_DIR` | Carpeta de adjuntos | `uploads` |
| `MAX_UPLOAD_MB` | Tamaño máximo por archivo | `5` |

Para generar una clave segura: `python -c "import secrets; print(secrets.token_urlsafe(48))"` y pegarla en `SECRET_KEY`.

**Datos de demostración y arranque:**

```powershell
python -m backend.seed
uvicorn backend.main:app --reload
```

La aplicación queda en http://127.0.0.1:8000/ y la documentación interactiva de la API en http://127.0.0.1:8000/docs. Las tablas se crean al iniciar.

**Usuarios ficticios** (contraseña `Demo12345!`):

| Rol | Correo | Nombre |
|---|---|---|
| Solicitante | ana.perez@ejemplo.edu | Ana Pérez |
| Solicitante | carlos.ruiz@ejemplo.edu | Carlos Ruiz |
| Personal de atención | luis.gomez@ejemplo.edu | Luis Gómez |
| Personal de atención | maria.rios@ejemplo.edu | María Ríos |
| Coordinación | coordinacion@ejemplo.edu | Coordinación Académica |

El seed también crea cinco servicios: Actualización de información personal, Atención de trámites generales, Certificado de estudios, Corrección de calificaciones y Solicitud de copia de documentos.

## 6. Servicios web implementados

La documentación interactiva con ejemplos y esquemas está en `/docs`. Solo se usan los métodos GET, POST y PATCH; no hay DELETE, porque las solicitudes se cancelan o finalizan, no se borran (RNF-09).

| ID | Método | Ruta | Quién | Descripción | Requisitos |
|---|---|---|---|---|---|
| EP-01 | POST | `/api/auth/registro` | Público | Registra un solicitante | RF-01 |
| EP-02 | POST | `/api/auth/login` | Público | Inicia sesión y devuelve el token | RF-02 |
| EP-03 | GET | `/api/auth/perfil` | Cualquiera | Datos del usuario autenticado | RF-02, RF-03 |
| EP-04 | GET | `/api/servicios` | Cualquiera | Catálogo de servicios activos | RF-04 |
| EP-05 | GET | `/api/usuarios/atencion` | Atención, coordinación | Personal de atención para elegir responsable | RF-13 |
| EP-06 | POST | `/api/solicitudes` | Solicitante | Crea una solicitud con adjuntos | RF-05, RF-06 |
| EP-07 | GET | `/api/solicitudes` | Cualquiera | Lista lo que el usuario puede ver, con filtros y paginación | RF-07, RF-09, RF-19 |
| EP-08 | GET | `/api/solicitudes/{id}` | Cualquiera | Detalle de una solicitud | RF-07, RF-19 |
| EP-09 | PATCH | `/api/solicitudes/{id}/estado` | Atención, coordinación | Evalúa: iniciar, aceptar y asignar, pedir información o rechazar | RF-10, RF-11 |
| EP-10 | POST | `/api/solicitudes/{id}/finalizacion` | Atención, coordinación | Finaliza con una respuesta y un archivo opcional | RF-16 |
| EP-11 | PATCH | `/api/solicitudes/{id}/responsable` | Atención, coordinación | Reasigna el responsable | RF-13 |
| EP-12 | PATCH | `/api/solicitudes/{id}/prioridad` | Atención, coordinación | Ajusta la prioridad con motivo | RF-14 |
| EP-13 | POST | `/api/solicitudes/{id}/notas` | Atención, coordinación | Registra una nota en el historial | RF-15 |
| EP-14 | POST | `/api/solicitudes/{id}/informacion` | Solicitante | Responde a una petición de información | RF-12 |
| EP-15 | POST | `/api/solicitudes/{id}/cancelacion` | Solicitante | Cancela antes de que pase a gestión | RF-08 |
| EP-16 | GET | `/api/solicitudes/{id}/eventos` | Cualquiera | Historial de trazabilidad | RF-17 |
| EP-17 | GET | `/api/adjuntos/{id}` | Cualquiera autorizado | Descarga un archivo | RF-06, RNF-05 |
| EP-18 | GET | `/api/resumen` | Coordinación | Resumen consolidado | RF-18 |
| EP-19 | GET | `/api/salud` | Público | Estado del servidor y de la base de datos | RNF-07 |

**Ejemplo: crear una solicitud (EP-06).** Petición `POST /api/solicitudes` con `Authorization: Bearer <token>` y `multipart/form-data` con `servicio_id=3`, `asunto=Certificado para trámite de beca`, `descripcion=Necesito el certificado de estudios para renovar mi beca.` y `archivos=documento-prueba.pdf`. Respuesta 201:

```json
{
  "id": 1, "radicado": "SOL-2026-00001",
  "servicio": { "id": 3, "nombre": "Certificado de estudios" },
  "asunto": "Certificado para trámite de beca",
  "estado": "recibida", "prioridad": "media",
  "solicitante": { "id": 4, "nombre": "Ana Pérez" }, "responsable": null,
  "adjuntos": [ { "id": 1, "nombre_original": "documento-prueba.pdf", "proposito": "solicitud", "tipo_mime": "application/pdf", "tamano_bytes": 28 } ],
  "dias_pendientes": 0, "dias_atencion": null
}
```

**Validaciones y errores.** Todos los errores usan el formato `{ "detail": "mensaje" }`:

| Código | Cuándo |
|---|---|
| 400 | Regla de negocio incumplida: servicio sin el adjunto exigido, más de 5 archivos, falta el motivo o el responsable, responsable que no es de atención |
| 401 | Falta el token o venció |
| 403 | El rol no puede hacer la operación |
| 404 | La solicitud o el adjunto no existe o el usuario no puede verlo (se responde igual para no revelar qué números existen) |
| 409 | Transición de estado no permitida o solicitud en estado final |
| 413 / 415 | Archivo demasiado grande o de un tipo que no es PDF, JPG ni PNG |
| 422 | Datos con formato inválido o archivo vacío |

## 7. Pruebas de API e integración y evidencias de funcionamiento

El script `evidencias/probar_api.py` ejecuta 90 pruebas funcionales contra la API real con una base de datos temporal (`pruebas.db`, que se borra al terminar) y no toca `app.db`. Cada línea muestra el identificador, el requisito, el método, la ruta y el código esperado y obtenido.

```powershell
python evidencias/probar_api.py
python evidencias/verificar_modelo.py
```

**Resultado: 90 de 90 pruebas aprobadas** y todas las verificaciones del modelo de datos aprobadas.

| Grupo | Pruebas | Qué comprueban | Resultados |
|---|---|---|---|
| Autenticación, catálogo y roles | T-01 a T-15 | Registro, login, tokens inválidos o vencidos, hash de contraseñas, control por rol | [pruebas_autenticacion_resultado.txt](evidencias/pruebas_autenticacion_resultado.txt) |
| Creación de solicitudes | T-16 a T-27 | Adjunto obligatorio, tipo, contenido y tamaño de archivos, límite de archivos, radicados únicos | [pruebas_solicitudes_resultado.txt](evidencias/pruebas_solicitudes_resultado.txt) |
| Consulta | T-28 a T-46 | Visibilidad por rol, filtros, paginación, 404 en lo ajeno, notas internas ocultas, descarga de adjuntos | [pruebas_consulta_resultado.txt](evidencias/pruebas_consulta_resultado.txt) |
| Gestión | T-47 a T-83 | Flujo completo, transiciones válidas e inválidas, motivos, reasignación, prioridad, notas, cancelación, estados finales | [pruebas_gestion_resultado.txt](evidencias/pruebas_gestion_resultado.txt) |
| Resumen | T-84 a T-90 | Conteos consistentes con la base de datos, filtros por fecha, acceso solo para coordinación | [pruebas_resumen_resultado.txt](evidencias/pruebas_resumen_resultado.txt) |

**Evidencias** (carpeta [evidencias/](evidencias/)):

- Proceso completo en la interfaz: `ui-01-login.png`, `ui-02-mis-solicitudes.png`, `ui-04-detalle-solicitante-recibida.png`, `ui-05-bandeja.png`, `ui-04-detalle-personal-pendiente.png`, `ui-04-detalle-personal-gestion.png`, `ui-04-detalle-solicitante-finalizada.png` y `ui-06-resumen.png`.
- Casos válidos en la API (Swagger): `solicitud-crear-201.png`, `consulta-listado-atencion-200.png`, `consulta-historial-personal-200.png`, `gestion-aceptar-200.png`, `gestion-finalizar-200.png`, `resumen-coordinacion-200.png`, `auth-login-200.png`.
- Casos inválidos: `solicitud-sin-adjunto-400.png`, `solicitud-tipo-415.png`, `ui-03-nueva-sin-adjunto.png`, `consulta-detalle-ajena-404.png`, `gestion-transicion-409.png`, `gestion-cancelar-409.png`, `auth-atencion-403.png`.
- Las capturas de la API de los pull requests 3 a 7 se generaron ejecutando el código del repositorio en un entorno de pruebas aparte, con los mismos datos de demostración.

La matriz que une cada condición obligatoria con sus requisitos, implementación, pruebas y evidencias está en [docs/trazabilidad.md](docs/trazabilidad.md).

## 8. Control de versiones

- **Repositorio:** https://github.com/KBerrioC/Proyecto-final-de-sistema-solicitudes-servicio
- **Flujo de trabajo:** una rama por tarea, commits descriptivos con el formato `tipo: descripción (requisito)` y pull requests con propósito, cambios, pruebas y requisitos asociados.
- **Pull requests relevantes y aportes:**

| Rama | Aporte |
|---|---|
| `docs/requisitos-entrevista`, `docs/diseno-api`, `docs/diseno-arquitectura-interfaces` | Entrevista, requisitos y diseño completo |
| `chore/estructura-base` y `feat/base-backend` | Estructura del repositorio, modelo de datos y semillas |
| `feat/autenticacion` | Registro, login, roles y control de acceso |
| `feat/crear-solicitudes` | Creación de solicitudes con adjuntos (CA-01) |
| `feat/consulta-solicitudes` | Listado, detalle, historial y descarga (CA-03, CA-04, CA-05) |
| `feat/gestion-solicitudes` | Evaluación, finalización, reasignación, prioridad, notas, información y cancelación (CA-02) |
| `feat/resumen-coordinacion` | Resumen consolidado (CA-06) |
| `feat/frontend` | Seis pantallas de la interfaz |
| `docs/cierre` | Matriz de trazabilidad, README y ajustes del diseño |

## 9. Conclusiones y limitaciones

**Cumplimiento.** Se cumplen las seis condiciones obligatorias (CA-01 a CA-06): el sistema registra solicitudes con adjuntos según el servicio, gestiona el flujo de evaluación hasta la finalización con respuesta, conserva un historial con autor y fecha, muestra a cada rol solo lo que le corresponde y ofrece un resumen para coordinación. Cada requisito tiene su prueba en la [matriz de trazabilidad](docs/trazabilidad.md).

**Dificultades técnicas y soluciones.**
- SQLite no hace cumplir las claves foráneas por defecto: se activó `PRAGMA foreign_keys=ON` en cada conexión y se comprobó con `verificar_modelo.py`.
- bcrypt solo admite 72 bytes: la validación de la contraseña cuenta bytes, no caracteres, para que una contraseña con tildes no falle al guardarse.
- Si una operación falla después de escribir archivos en disco, podrían quedar adjuntos huérfanos: se deshace la transacción y se borran los archivos de esa operación (pruebas T-20 a T-23 y T-63).
- Para que un solicitante no pueda deducir qué números de solicitud existen, lo ajeno responde 404, igual que lo inexistente (T-37).
- Al probar la interfaz se vio que quien asigna una solicitud a otra persona deja de verla (visibilidad del personal, SUP-10) y la pantalla mostraba un error aunque la acción había funcionado: ahora lo lleva a la bandeja con un aviso, y la regla quedó documentada en el diseño.
- En Windows, Git mostraba archivos como modificados solo por la diferencia de saltos de línea (CRLF y LF): se resolvió comparando con `git diff --ignore-cr-at-eol` y restaurando esos archivos.

**Restricciones y comportamientos pendientes dentro del alcance.**
- Los supuestos SUP-01 a SUP-11 no se confirmaron con el docente (sección 9 de [docs/requisitos.md](docs/requisitos.md)); la revisión de requisitos se hará al final, según lo acordado.
- El sistema guarda los adjuntos en disco local y los datos en SQLite: sirve para una instalación pequeña y de un solo servidor, no para varios servidores.
- No incluye recuperación de contraseña ni gestión de usuarios de personal desde la interfaz: el personal y coordinación se crean con `seed.py`.
- No envía correos (fuera de alcance); el solicitante se entera de los cambios al consultar su solicitud.
- La interfaz se probó recorriendo el proceso completo en un navegador automatizado y con capturas; no hay un conjunto de pruebas de interfaz en el repositorio.
