# Registro de entrevista de requisitos

**Proyecto:** PF-01 – Sistema de gestión de solicitudes de servicio
**Autor:** Berrio (GitHub: KBerrioC)
**Entrevistado:** docente de la asignatura, en el rol de representante de la organización
**Medio:** chat de Teams, en tres rondas de preguntas (se enviaron por bloques para dejar registro)
**Fechas:** _por completar (ronda 1: __/__; ronda 2 y 3: __/__)_
**Evidencia:** capturas del chat en `evidencias/entrevista/`

Convención: cada intercambio tiene un identificador `E-XX`. Los requisitos de [requisitos.md](requisitos.md) citan estos identificadores como origen.

## 1. Preguntas y respuestas

### Ronda 1 – Contexto y proceso

| ID | Pregunta | Respuesta del docente (resumen) | Acuerdo o decisión |
|---|---|---|---|
| E-01 | ¿Qué tipo de organización y de servicios debo asumir? | Institución educativa que ofrece servicios administrativos: expedición de certificados, actualización de información, solicitud de documentos y trámites generales. | Se modela una institución educativa con un catálogo de servicios administrativos. |
| E-02 | ¿Qué datos mínimos debe tener una solicitud? | Debe identificar al solicitante, el servicio requerido, el asunto y una descripción. Debe permitir adjuntar documentos cuando el trámite lo requiera. Los demás campos los define el equipo. | Adjuntos incluidos en el alcance. Campos adicionales definidos en el diseño. |
| E-03 | Estados propuestos: Recibida → En evaluación → En gestión → Finalizada. ¿Hay otros? ¿Reapertura? | Los estados propuestos son un buen punto de partida. Se debe analizar si hacen falta estados para solicitudes rechazadas, canceladas o pendientes de información. La reapertura es posible si se definen las condiciones. | El estudiante define los estados finales y decide sobre la reapertura (ver SUP-02). |
| E-04 | ¿Qué significa «evaluar» una solicitud? | Comprobar que la información esté completa y que el trámite corresponda a los servicios de la organización. Resultados posibles: aceptar, solicitar información adicional o rechazar indicando el motivo. Al aceptarse, se asigna al responsable. | Evaluar tiene tres resultados. Rechazar y pedir información exigen motivo. |
| E-05 | ¿Roles y login? | Los tres roles propuestos (solicitante, personal de atención, coordinación) son adecuados. Se requiere autenticación porque se maneja información de los solicitantes. El equipo define la implementación y los permisos. | Autenticación obligatoria para los tres roles. |
| E-06 | ¿El solicitante usa cuenta o código de radicado? | Debe poder registrar y consultar sus solicitudes. Se puede usar cuenta o código, siempre que la información no quede expuesta a personas no autorizadas. Los requisitos, reglas de negocio y decisiones técnicas corresponden al estudiante. | Se elige cuenta (ver SUP-01). |

### Ronda 2 – Permisos, consolidado y avance

| ID | Pregunta | Respuesta del docente (resumen) | Acuerdo o decisión |
|---|---|---|---|
| E-07 | Al aceptar una solicitud, ¿quién la asigna? Propuesta: atención asigna y coordinación solo consulta. | El personal de atención puede asignar, pero coordinación también debe poder intervenir y reasignar solicitudes cuando sea necesario. | Atención y coordinación asignan y reasignan. Coordinación no es solo de consulta. |
| E-08 | Resumen de coordinación: conteo por estado, servicio y responsable. ¿Algo más? | Está bien incluir esos conteos. También es útil conocer los tiempos de atención y las solicitudes que llevan más tiempo pendientes. | El resumen incluye cinco medidas (ver RF-18). |
| E-09 | ¿Puedo avanzar con el repositorio y la implementación mientras revisa la especificación? | Puede avanzar con la organización del repositorio y el diseño inicial (el mensaje llegó cortado). | Se avanza con repositorio y diseño. Ver también E-13. |

### Ronda 3 – Prioridad, trazabilidad, CRUD y entrega

| ID | Pregunta | Respuesta del docente (resumen) | Acuerdo o decisión |
|---|---|---|---|
| E-10 | ¿Plazos máximos o prioridad, o basta con registrar fechas? | No todos los trámites tienen la misma urgencia. La organización necesita identificar cuáles requieren atención prioritaria y cuánto tiempo llevan pendientes. El estudiante propone cómo manejarlo. | Se define prioridad de tres niveles y cálculo de tiempo pendiente (ver RN-09 y RN-10). |
| E-11 | Trazabilidad: el solicitante ve historial de estados y respuesta; las notas internas solo atención y coordinación. | Está bien. El solicitante debe conocer el avance de su trámite y la respuesta recibida; atención y coordinación pueden necesitar información adicional para gestionar el caso. | Se separan eventos visibles al solicitante y notas internas (ver RN-05 y RF-15). |
| E-12 | ¿Basta con implementar las operaciones CRUD que el proceso requiera? | Sí. No es obligatorio desarrollar las cuatro operaciones CRUD por cada entidad, pero hay que demostrar el uso de los servicios web y las operaciones HTTP correspondientes. | Cada endpoint se justifica por el proceso. No se implementa DELETE (ver RNF-09). |
| E-13 | ¿Cómo prefiere recibir `requisitos.md` para aprobarlo? | Puede continuar de forma autónoma. La revisión de los requisitos se hará junto con los demás entregables al finalizar el proyecto. | No hay aprobación previa. La revisión es al final. |

## 2. Decisiones del estudiante que el docente no objetó

El docente recibió estas decisiones en la ronda 2 y no las objetó. No se consideran aprobadas, por lo que se tratan como supuestos (ver sección 9 de [requisitos.md](requisitos.md)):

- Cuenta con usuario y contraseña para los tres roles; solicitantes con registro propio y personal creado previamente.
- Siete estados y reapertura fuera de alcance.
- Catálogo de servicios con marca «requiere adjunto».
- Adjuntos en PDF, JPG o PNG con tamaño máximo; visibles solo para el solicitante y el personal.
- Tipos de solicitante, cancelación antes de «En gestión», respuesta a solicitud de información y respuesta final con adjunto opcional.

## 3. Cuestiones pendientes

- La revisión formal de los requisitos queda para el final (E-13). Hasta entonces, todo lo no confirmado permanece marcado como supuesto.
- La respuesta E-09 llegó cortada. Se interpreta, junto con E-13, que se puede continuar con el diseño y el desarrollo de forma autónoma.
