# Matriz de trazabilidad – Sistema de gestión de solicitudes de servicio (PF-01)

**Autor:** Berrio (GitHub: KBerrioC)
**Insumos:** [requisitos.md](requisitos.md), [diseno.md](diseno.md) y [entrevista.md](entrevista.md)

Esta matriz une cada condición obligatoria de la guía con sus requisitos, su diseño, su implementación, su prueba y su evidencia. Las pruebas se ejecutan con `python evidencias/probar_api.py` (90 pruebas, identificadas de T-01 a T-90) y los resultados están en los archivos `evidencias/pruebas_*_resultado.txt`.

## 1. Condiciones obligatorias

| Condición | Requisitos e historias | Diseño (endpoints y pantallas) | Implementación | Rama de la tarea | Pruebas | Evidencias |
|---|---|---|---|---|---|---|
| **CA-01** Registro de solicitudes con documentos adjuntos según el servicio | RF-04, RF-05, RF-06 · HU-02 | EP-04, EP-06 · PAN-03 | `backend/routers/solicitudes.py`, `backend/services/solicitudes.py` (`crear_solicitud`), `backend/services/archivos.py`, `frontend/nueva-solicitud.html` | `feat/crear-solicitudes`, `feat/frontend` | T-11, T-12, T-16 a T-27 | `solicitud-crear-201.png`, `solicitud-sin-adjunto-400.png`, `solicitud-tipo-415.png`, `ui-03-nueva-sin-adjunto.png` |
| **CA-02** Evaluación, asignación, información adicional, rechazo y finalización | RF-10, RF-11, RF-13, RF-15, RF-16 · HU-06, HU-07, HU-08 | EP-09 a EP-15 · PAN-04, PAN-05 | `backend/routers/gestion.py`, `backend/services/gestion.py` (tabla `TRANSICIONES`), `frontend/solicitud.html`, `frontend/bandeja.html` | `feat/gestion-solicitudes`, `feat/frontend` | T-47 a T-83 | `gestion-aceptar-200.png`, `gestion-transicion-409.png`, `gestion-finalizar-200.png`, `gestion-cancelar-409.png`, `ui-04-detalle-personal-pendiente.png`, `ui-04-detalle-personal-gestion.png` |
| **CA-03** Consulta de solicitudes y tiempo pendiente | RF-07, RF-19 · HU-03, HU-05 | EP-07, EP-08 · PAN-02, PAN-04, PAN-05 | `backend/routers/solicitudes.py`, `backend/services/solicitudes.py` (`listar_solicitudes`, `obtener_visible`), `frontend/mis-solicitudes.html`, `frontend/bandeja.html` | `feat/consulta-solicitudes`, `feat/frontend` | T-28 a T-39 | `consulta-listado-atencion-200.png`, `consulta-detalle-ajena-404.png`, `ui-02-mis-solicitudes.png`, `ui-05-bandeja.png` |
| **CA-04** Historial de trazabilidad | RF-15, RF-17 · HU-08, HU-09 | EP-16 · PAN-04 | `backend/services/solicitudes.py` (`listar_eventos`), `backend/services/gestion.py` (`registrar_evento`), tabla `eventos` | `feat/consulta-solicitudes`, `feat/gestion-solicitudes` | T-40 a T-42, T-47, T-52, T-55, T-59, T-60, T-74 | `consulta-historial-personal-200.png`, `consulta-historial-solicitante-200.png` |
| **CA-05** Respuesta al solicitante y descarga del adjunto | RF-07, RF-16 · HU-03, HU-08 | EP-08, EP-10, EP-17 · PAN-04 | `backend/services/gestion.py` (`finalizar`), `backend/routers/adjuntos.py`, `frontend/js/solicitud.js` | `feat/consulta-solicitudes`, `feat/gestion-solicitudes` | T-43 a T-46, T-62 a T-65 | `gestion-finalizar-200.png`, `ui-04-detalle-solicitante-finalizada.png` |
| **CA-06** Resumen consolidado para coordinación | RF-18 · HU-10 | EP-18 · PAN-06 | `backend/routers/resumen.py`, `backend/services/resumen.py`, `frontend/resumen.html` | `feat/resumen-coordinacion`, `feat/frontend` | T-84 a T-90 | `resumen-coordinacion-200.png`, `ui-06-resumen.png` |

## 2. Reglas de negocio

| Regla | Dónde se aplica | Pruebas |
|---|---|---|
| RN-01 Transiciones válidas | `TRANSICIONES` y `validar_transicion` en `services/gestion.py` | T-49, T-50, T-56, T-78 |
| RN-02 Motivo al rechazar o pedir información | `evaluar` en `services/gestion.py` | T-51, T-76 |
| RN-03 Responsable para pasar a «En gestión» | `evaluar` en `services/gestion.py` | T-57 |
| RN-04 Respuesta al finalizar | `routers/gestion.py` y `finalizar` | T-62, T-64, T-82 |
| RN-05 Notas internas ocultas al solicitante | `listar_eventos` en `services/solicitudes.py` | T-40, T-41, T-60, T-74 |
| RN-06 Adjunto obligatorio según el servicio | `crear_solicitud` | T-17, T-18 |
| RN-07 Responsable de atención | `exigir_personal_atencion` | T-58, T-68, T-69 |
| RN-08 Registro de asignaciones y reasignaciones | `evaluar` y `reasignar` | T-59, T-67 |
| RN-09 Prioridad con motivo | `cambiar_prioridad` | T-59, T-71, T-72, T-73 |
| RN-10 Tiempos calculados | `detalle_solicitud`, `generar_resumen` | T-16, T-64, T-85, T-86 |
| RN-11 Cancelación antes de «En gestión» | `cancelar` | T-79, T-80, T-81 |
| RN-12 Estados finales inmutables | `validar_transicion`, `exigir_no_final` | T-66, T-77, T-78 |

## 3. Requisitos no funcionales

| Requisito | Cómo se cumple | Pruebas y evidencias |
|---|---|---|
| RNF-01 Contraseñas con hash y tokens con expiración | `bcrypt` y JWT en `backend/auth.py` | T-04, T-09, T-10, T-15 |
| RNF-02 Validación en el servidor | Pydantic y reglas en los servicios; permisos por rol en cada endpoint | T-02, T-13, T-19, T-25, T-33, T-34, T-48 |
| RNF-03 Códigos HTTP coherentes | Un solo formato de error y códigos 400, 401, 403, 404, 409 y 422 | T-05, T-06, T-37, T-50 |
| RNF-04 Claves foráneas activas y estados solo por transiciones | `PRAGMA foreign_keys=ON` y `TRANSICIONES` | `verificar_modelo_resultado.txt`, T-27, T-50 |
| RNF-05 Adjuntos seguros | Extensión, firma del contenido, tamaño y nombre aleatorio; descarga solo con permiso | T-20 a T-23, T-43 a T-46, T-63 |
| RNF-06 Datos ficticios | `backend/seed.py` | — |
| RNF-07 Instalación reproducible | `README.md`, `requirements.txt` con versiones fijas, `.env.example` | Sección 5 del README |
| RNF-08 Documentación interactiva de la API | `/docs` de FastAPI | `base-backend-docs.png` |
| RNF-09 Solo GET, POST y PATCH | No existe ningún endpoint DELETE | Sección 6 del README |
| RNF-10 Interfaz simple con mensajes claros | `frontend/` | `ui-01-login.png` a `ui-06-resumen.png` |

## 4. Pruebas por grupo

| Grupo | Pruebas | Archivo de resultados |
|---|---|---|
| Autenticación, catálogo y roles | T-01 a T-15 | `pruebas_autenticacion_resultado.txt` |
| Creación de solicitudes | T-16 a T-27 | `pruebas_solicitudes_resultado.txt` |
| Consulta, historial y descarga | T-28 a T-46 | `pruebas_consulta_resultado.txt` |
| Gestión | T-47 a T-83 | `pruebas_gestion_resultado.txt` |
| Resumen | T-84 a T-90 | `pruebas_resumen_resultado.txt` |
| Modelo de datos | 6 verificaciones | `verificar_modelo_resultado.txt` |
