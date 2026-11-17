# Requisitos – Sistema de gestión de solicitudes de servicio (PF-01)

**Autor:** Berrio (GitHub: KBerrioC)
**Estado:** borrador para revisión del docente (la revisión se hará al finalizar el proyecto, según E-13)
**Insumos:** guía PF-01 y [registro de entrevista](entrevista.md)

Cada requisito indica su **origen**: `E-XX` es una respuesta confirmada por el docente en la entrevista; `Guía` es la guía PF-01; `SUP-XX` es un supuesto del estudiante no confirmado (sección 9).

## 1. Contexto

Una institución educativa ofrece servicios administrativos: certificados, actualización de información, solicitud de documentos y trámites generales (E-01). Hoy las solicitudes llegan por correo, llamadas y WhatsApp, y no hay trazabilidad. El sistema debe registrar cada solicitud desde su recepción hasta su respuesta y finalización, para que cada actor consulte lo que le corresponde.

## 2. Alcance

**Dentro del alcance**
- Registro e inicio de sesión de usuarios con tres roles.
- Presentación de solicitudes con adjuntos cuando el servicio lo requiera.
- Evaluación, asignación, gestión y finalización de solicitudes.
- Historial de acciones, estado consultable y respuesta al solicitante.
- Prioridad y tiempos de atención.
- Resumen consolidado para coordinación.

**Fuera del alcance**
- Facturación, pagos, WhatsApp, envío real de correos e integración con plataformas externas (Guía).
- Reapertura de solicitudes finalizadas (SUP-02).
- Notificaciones fuera de la aplicación.
- Eliminación de solicitudes (RNF-09).

## 3. Actores y permisos

| Acción | Solicitante | Personal de atención | Coordinación |
|---|---|---|---|
| Registrarse e iniciar sesión | Sí | Sí | Sí |
| Crear solicitud y adjuntar documentos | Sí | No | No |
| Cancelar su propia solicitud (antes de «En gestión») | Sí | No | No |
| Responder una solicitud de información | Sí | No | No |
| Ver sus solicitudes, estado, historial público y respuesta | Sí | Sí | Sí |
| Ver notas internas | No | Sí | Sí |
| Evaluar (aceptar, pedir información, rechazar) | No | Sí | Sí |
| Asignar y reasignar responsable | No | Sí | Sí |
| Gestionar, registrar acciones y finalizar | No | Sí | Sí |
| Ajustar prioridad | No | Sí | Sí |
| Ver el resumen consolidado | No | No | Sí |

Origen: E-05, E-07, E-11. La visibilidad del personal de atención (solicitudes por evaluar y las asignadas a él) es SUP-10; coordinación ve todas.

## 4. Estados y transiciones

Estados: **Recibida, En evaluación, Pendiente de información, En gestión, Finalizada, Rechazada, Cancelada** (E-03, SUP-02).

| Desde | Hacia | Quién | Condición |
|---|---|---|---|
| Recibida | En evaluación | Atención o coordinación | Inicia la evaluación |
| Recibida | Cancelada | Solicitante | Solo su propia solicitud |
| En evaluación | En gestión | Atención o coordinación | Con responsable asignado y prioridad definida |
| En evaluación | Pendiente de información | Atención o coordinación | Con motivo obligatorio |
| En evaluación | Rechazada | Atención o coordinación | Con motivo obligatorio |
| En evaluación | Cancelada | Solicitante | Solo su propia solicitud |
| Pendiente de información | En evaluación | Solicitante | Al responder con texto o adjunto |
| Pendiente de información | Cancelada | Solicitante | Solo su propia solicitud |
| En gestión | Finalizada | Atención o coordinación | Con respuesta obligatoria |

Los estados Finalizada, Rechazada y Cancelada son finales. No hay otras transiciones.

## 5. Reglas de negocio

| ID | Regla | Origen |
|---|---|---|
| RN-01 | Un cambio de estado solo es válido si está en la tabla de la sección 4. | E-03, SUP-02 |
| RN-02 | Rechazar una solicitud o pedir información adicional exige un motivo. | E-04 |
| RN-03 | Una solicitud no pasa a «En gestión» sin responsable asignado. | E-04 |
| RN-04 | Finalizar una solicitud exige una respuesta para el solicitante. | Guía CA-05 |
| RN-05 | El solicitante solo ve sus solicitudes, sus cambios de estado y la respuesta. Las notas internas solo las ven atención y coordinación. | E-06, E-11 |
| RN-06 | Si el servicio requiere adjunto, la solicitud se crea con al menos un archivo. | E-02, SUP-04 |
| RN-07 | El responsable debe ser un usuario con rol de personal de atención. | E-04, SUP-01 |
| RN-08 | Toda asignación o reasignación queda registrada con quién la hizo y de quién a quién. | E-07 |
| RN-09 | La prioridad tiene tres niveles (Alta, Media, Baja). Cada servicio tiene una por defecto y el personal puede ajustarla con motivo. | E-10, SUP-09 |
| RN-10 | Tiempo pendiente = fecha actual − fecha de creación, para solicitudes no finalizadas. Tiempo de atención = fecha de finalización − fecha de creación. | E-08, E-10 |
| RN-11 | Solo se puede cancelar mientras la solicitud no esté «En gestión». | SUP-06 |
| RN-12 | Una solicitud en estado final no se modifica. No hay reapertura. | SUP-02 |

## 6. Requisitos funcionales

| ID | Requisito | Prioridad | Origen |
|---|---|---|---|
| RF-01 | El sistema permite registrar solicitantes con una cuenta (nombre, correo, tipo de solicitante, contraseña). | Alta | E-05, E-06, SUP-01, SUP-03 |
| RF-02 | El sistema permite iniciar y cerrar sesión, y mantiene la sesión con un token con expiración. | Alta | E-05 |
| RF-03 | El sistema restringe cada operación según el rol del usuario autenticado. | Alta | E-05, Guía |
| RF-04 | El sistema muestra el catálogo de servicios, indicando si requieren adjunto y su prioridad por defecto. | Alta | E-01, SUP-04 |
| RF-05 | El solicitante crea una solicitud indicando servicio, asunto y descripción. Queda en estado «Recibida». | Alta | E-02, Guía CA-01 |
| RF-06 | El solicitante adjunta documentos a su solicitud. El sistema valida tipo y tamaño. | Alta | E-02, SUP-05 |
| RF-07 | El solicitante consulta la lista de sus solicitudes y el detalle de cada una (estado, historial visible y respuesta). | Alta | E-06, E-11, Guía CA-03, CA-05 |
| RF-08 | El solicitante cancela su solicitud mientras no esté «En gestión». | Media | SUP-06 |
| RF-09 | El personal consulta la bandeja de solicitudes con filtros por estado, servicio, prioridad y responsable, ordenada por prioridad y antigüedad. | Alta | E-10, SUP-10 |
| RF-10 | El personal inicia la evaluación de una solicitud «Recibida». | Alta | E-04 |
| RF-11 | El personal resuelve la evaluación: aceptar (con responsable y prioridad), solicitar información o rechazar, estos dos últimos con motivo. | Alta | E-04, Guía CA-02 |
| RF-12 | El solicitante responde a una solicitud de información con texto o un nuevo adjunto, y la solicitud vuelve a «En evaluación». | Media | SUP-07 |
| RF-13 | Atención y coordinación asignan y reasignan el responsable de una solicitud. | Alta | E-07 |
| RF-14 | El personal ajusta la prioridad de una solicitud, indicando el motivo. | Media | E-10, SUP-09 |
| RF-15 | El personal registra acciones de gestión y notas, marcadas como visibles para el solicitante o internas. | Alta | E-11, Guía CA-02, CA-04 |
| RF-16 | El personal finaliza una solicitud en gestión con una respuesta de texto y un adjunto opcional. | Alta | Guía CA-05, SUP-08 |
| RF-17 | El sistema conserva y muestra el historial de eventos de una solicitud (creación, cambios de estado, asignaciones, acciones y respuesta), con autor y fecha. | Alta | Guía CA-04, E-11 |
| RF-18 | Coordinación consulta un resumen con: conteo por estado, por servicio y por responsable, tiempo promedio de atención y las solicitudes pendientes más antiguas. | Alta | E-08, Guía CA-06 |
| RF-19 | El sistema muestra, para cada solicitud no finalizada, el tiempo que lleva pendiente. | Media | E-08, E-10 |

## 7. Requisitos no funcionales

| ID | Requisito | Origen |
|---|---|---|
| RNF-01 | Las contraseñas se almacenan con hash. Los tokens tienen expiración. Los secretos van en `.env`, fuera del repositorio. | Guía (seguridad) |
| RNF-02 | El servidor valida todas las entradas, incluso si la solicitud no proviene de la interfaz. | Guía |
| RNF-03 | Los errores se devuelven con códigos HTTP coherentes (400, 401, 403, 404, 409, 422) y sin revelar información sensible. | Guía |
| RNF-04 | Las claves foráneas están activas y el estado de una solicitud solo cambia por transiciones válidas. | Guía, RN-01 |
| RNF-05 | Los adjuntos se limitan a PDF, JPG y PNG con tamaño máximo, se guardan fuera del control de versiones y solo se descargan mediante un endpoint autorizado. | SUP-05, E-06 |
| RNF-06 | Se usan solo datos ficticios en pruebas y demostración. | Guía |
| RNF-07 | La instalación y ejecución son reproducibles a partir del README, con dependencias fijadas. | Guía |
| RNF-08 | La API tiene documentación interactiva (OpenAPI/Swagger). | Guía |
| RNF-09 | Cada endpoint se justifica por el proceso. Se usan GET, POST y PATCH. No hay DELETE: la cancelación es un cambio de estado. | E-12 |
| RNF-10 | La interfaz es simple, con mensajes claros de error y de confirmación. | SUP-11 |

## 8. Historias de usuario y criterios de aceptación

| ID | Historia | Criterios de aceptación | Cubre |
|---|---|---|---|
| HU-01 | Como solicitante, quiero registrarme e iniciar sesión para presentar y consultar mis solicitudes. | Con datos válidos se crea la cuenta y se inicia sesión. Con correo repetido o contraseña inválida el sistema rechaza y no crea la cuenta. | RF-01, RF-02 |
| HU-02 | Como solicitante, quiero presentar una solicitud de un servicio con sus adjuntos. | Con datos válidos queda «Recibida» y puede recuperarse. Sin asunto, sin descripción o sin adjunto cuando el servicio lo exige, se rechaza y no se guarda. | CA-01, RF-04 a RF-06 |
| HU-03 | Como solicitante, quiero ver el estado y la respuesta de mi solicitud. | Veo solo mis solicitudes. El estado coincide con las acciones realizadas. En un caso finalizado veo la respuesta. Consultar una solicitud ajena o inexistente da error controlado. | CA-03, CA-05, RF-07 |
| HU-04 | Como solicitante, quiero cancelar o completar mi solicitud cuando haga falta. | Puedo cancelar antes de «En gestión». Si me piden información, puedo responder y la solicitud vuelve a «En evaluación». No puedo cancelar una en gestión. | RF-08, RF-12 |
| HU-05 | Como personal de atención, quiero ver una bandeja de solicitudes priorizada. | Veo la lista con filtros, ordenada por prioridad y antigüedad, con el tiempo pendiente de cada una. | RF-09, RF-19 |
| HU-06 | Como personal de atención, quiero evaluar una solicitud. | Puedo aceptarla (con responsable y prioridad), pedir información o rechazarla con motivo. Sin motivo, el sistema rechaza la operación. Un solicitante no puede evaluar. | CA-02, RF-10, RF-11 |
| HU-07 | Como personal o coordinación, quiero asignar y reasignar responsables. | La reasignación cambia el responsable y queda en el historial con autor y fecha. El responsable debe ser personal de atención. | RF-13 |
| HU-08 | Como personal de atención, quiero registrar acciones y finalizar con una respuesta. | Puedo registrar notas públicas o internas. Finalizar exige respuesta. Una solicitud finalizada no se modifica. | CA-02, RF-15, RF-16 |
| HU-09 | Como usuario autorizado, quiero ver el historial de una solicitud. | Se listan los eventos con autor y fecha. El solicitante no ve las notas internas. | CA-04, RF-17 |
| HU-10 | Como coordinación, quiero un resumen del proceso. | Se muestran conteos por estado, servicio y responsable, tiempo promedio de atención y las más antiguas pendientes, integrando varias solicitudes. Otro rol no accede. | CA-06, RF-18 |

## 9. Supuestos no confirmados

No se consultaron con el docente durante la entrevista. Son decisiones del estudiante dentro de lo que el docente dejó a su criterio (E-03, E-06, E-10 y E-13) y se revisarán al final del proyecto.

| ID | Supuesto |
|---|---|
| SUP-01 | Los tres roles usan cuenta con usuario y contraseña. El solicitante se registra solo; el personal y la coordinación se crean con datos iniciales. |
| SUP-02 | Siete estados (sección 4). La reapertura no se implementa; se justifica por el esfuerzo adicional de definir sus condiciones. |
| SUP-03 | Tipos de solicitante: estudiante, docente, egresado y externo. |
| SUP-04 | Existe un catálogo de servicios y cada servicio indica si requiere adjunto. |
| SUP-05 | Los adjuntos son PDF, JPG o PNG con un tamaño máximo de 5 MB por archivo. |
| SUP-06 | El solicitante puede cancelar solo antes de «En gestión». |
| SUP-07 | Al pedir información, el solicitante responde con texto o un adjunto. |
| SUP-08 | La respuesta final es un texto con un adjunto opcional, por ejemplo un certificado. |
| SUP-09 | Prioridad en tres niveles, con valor por defecto por servicio y ajuste del personal con motivo. |
| SUP-10 | El personal de atención ve las solicitudes por evaluar y las asignadas a él; coordinación ve todas. |
| SUP-11 | La interfaz es en español y de diseño sencillo. |

## 10. Correspondencia con las condiciones obligatorias

| Condición | Requisitos | Historias |
|---|---|---|
| CA-01 | RF-04, RF-05, RF-06 | HU-02 |
| CA-02 | RF-10, RF-11, RF-13, RF-15, RF-16 | HU-06, HU-07, HU-08 |
| CA-03 | RF-07, RF-19 | HU-03, HU-05 |
| CA-04 | RF-15, RF-17 | HU-08, HU-09 |
| CA-05 | RF-07, RF-16 | HU-03, HU-08 |
| CA-06 | RF-18 | HU-10 |

Esta tabla alimenta la matriz `trazabilidad.md`, que añade la implementación, el pull request y la prueba de cada condición.
