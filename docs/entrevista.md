# Registro de entrevista de requisitos

**Proyecto:** PF-01 – Sistema de gestión de solicitudes de servicio
**Autor:** Berrio (GitHub: KBerrioC)
**Entrevistado:** docente de la asignatura, en el rol de representante de la organización
**Medio:** chat de Teams, en tres rondas de preguntas (se enviaron por bloques para dejar registro)
**Fechas:** ronda 1: 12/11; ronda 2 y 3: 14/11
**Evidencia:** texto literal de las respuestas del docente, copiado del chat de Teams

Convención: cada intercambio tiene un identificador `E-XX`. Los requisitos de [requisitos.md](requisitos.md) citan estos identificadores como origen. El texto de las preguntas y de las respuestas es el del chat; solo se sustituyó la numeración propia de cada mensaje por el identificador `E-XX`.

## 1. Preguntas y respuestas

### Ronda 1 – Contexto y proceso

**Mensaje del estudiante (apertura):**
Bueno profe si no le molesta quisiera seguir con la entrevista y pido disculpas por la hora igual soy consciente en que me responderá en el horario que pueda.
Estoy desarrollando el Proyecto Final 01 (gestión de solicitudes de servicio) yo solo . Para la entrevista de requisitos le estas son parte de mis preguntas

**Saludo del docente:** Buenas tardes. No hay problema,

#### E-01

**Pregunta:** ¿Qué tipo de organización y de servicios debo asumir (por ejemplo, universidad, alcaldía o empresa)?

**Respuesta del docente:** Puedes asumir que se trata de una institución educativa que ofrece servicios administrativos, como expedición de certificados, actualización de información, solicitudes de documentos y atención de trámites generales.

#### E-02

**Pregunta:** ¿Qué datos mínimos debe tener una solicitud (asunto, descripción, categoría, prioridad, otros)?

**Respuesta del docente:** Como mínimo, la solicitud debe identificar al solicitante, el servicio requerido, el asunto y una descripción de lo que necesita. También debe permitir adjuntar documentos cuando el trámite lo requiera. Los demás campos deben definirlos ustedes según las necesidades del proceso.

#### E-03

**Pregunta:** Como punto de partida propongo los estados: Recibida → En evaluación → En gestión → Finalizada. ¿Le parece bien, o debe haber otros como Rechazada o Cancelada? ¿Puede reabrirse una solicitud finalizada?

**Respuesta del docente:** Los estados que propones son un buen punto de partida. Debes analizar si necesitas estados adicionales para solicitudes rechazadas, canceladas o pendientes de información. También puedes contemplar la reapertura, siempre que definas las condiciones para permitirla.

#### E-04

**Pregunta:** ¿Qué significa "evaluar" una solicitud: aceptarla, rechazarla, clasificarla o asignarla?

**Respuesta del docente:** Evaluar una solicitud significa comprobar que la información esté completa y que el trámite corresponda a los servicios de la organización. Según el resultado, puede aceptarse, solicitar información adicional o rechazarse indicando el motivo. Una vez aceptada, se asigna al responsable de atenderla.

#### E-05

**Pregunta:** Propongo tres roles: solicitante, personal de atención y coordinación. ¿Debe haber login con usuario y contraseña, o basta con identificar el rol?

**Respuesta del docente:** Los tres roles que propones son adecuados. Como se maneja información de los solicitantes y existen diferentes responsabilidades, se requiere autenticación. Ustedes deben definir cómo implementarla y qué permisos tendrá cada rol.

#### E-06

**Pregunta:** ¿El solicitante necesita una cuenta o puede consultar su solicitud con un código?

**Respuesta del docente:** El solicitante debe poder registrar y consultar sus solicitudes. Puedes proponer el uso de una cuenta o un mecanismo de consulta mediante código de radicado, siempre que garantices que la información no quede expuesta a personas no autorizadas.

**Cierre de la respuesta del docente:** Recuerda que las respuestas permiten delimitar las necesidades de la organización, pero corresponde a ustedes definir los requisitos, las reglas de negocio y las decisiones técnicas que consideren necesarias para desarrollar la solución.

**Mensaje del estudiante (cierre de sus preguntas):** Quedo atento a sus respuestas para continuar con la entrevista . Gracias profe.

### Rondas 2 y 3 – Permisos, consolidado, prioridad y entrega

El docente respondió ambas rondas en un solo mensaje, que empieza con el saludo «Buenas tardes Kevin».

**Mensaje del estudiante (tras la ronda 1):** listo profe muchas gracias, sigo con la entrevista.

#### E-07

**Pregunta:** Al aceptar una solicitud, ¿quién la asigna? Propongo que lo haga el mismo personal de atención que la evalúa, a sí mismo o a otro funcionario, y que coordinación solo consulte. ¿Le parece bien?

**Respuesta del docente:** El personal de atención puede realizar la asignación, pero coordinación también debe tener la posibilidad de intervenir y reasignar solicitudes cuando sea necesario.

#### E-08

**Pregunta:** Para el resumen de coordinación propongo el conteo de solicitudes por estado, por servicio y por responsable. ¿Debe incluir algo más, como tiempos de atención?

**Respuesta del docente:** Está bien incluir los conteos por estado, servicio y responsable. También sería útil conocer los tiempos de atención y las solicitudes que llevan más tiempo pendientes.

#### E-09

**Pregunta:** ¿Puedo avanzar con el repositorio y la implementación mientras revisa la especificación, o debo esperar su aprobación? Quedo atento. Gracias.

**Respuesta del docente:** Puedes avanzar con la organización del repositorio y el diseño inicia

#### E-10

**Pregunta:** ¿Debo manejar plazos máximos de respuesta o niveles de prioridad, o basta con registrar las fechas de cada acción?

**Respuesta del docente:** No todos los trámites tienen la misma urgencia. La organización necesita identificar cuáles requieren atención prioritaria y conocer cuánto tiempo llevan pendientes. Puedes proponer cómo manejarlo.

#### E-11

**Pregunta:** Sobre la trazabilidad, propongo que el solicitante vea el historial de cambios de estado y la respuesta, y que las notas internas queden visibles solo para atención y coordinación. ¿Le parece bien?

**Respuesta del docente:** Está bien. El solicitante debe conocer el avance de su trámite y la respuesta recibida, mientras que el personal de atención y coordinación pueden necesitar información adicional para gestionar el caso.

#### E-12

**Pregunta:** La guía indica que las operaciones CRUD solo se implementan cuando el proceso las justifica, y la presentación menciona "operaciones CRUD". ¿Confirma que basta con implementar las que el proceso requiera, y no un CRUD completo de cada entidad?

**Respuesta del docente:** Sí, deben implementar las operaciones que realmente necesita el proceso. No es obligatorio desarrollar las cuatro operaciones CRUD para cada entidad, pero sí demostrar el uso de los servicios web y las operaciones HTTP correspondientes.

#### E-13

**Pregunta:** ¿Cómo prefiere recibir `docs/requisitos.md` para aprobarlo: el enlace al archivo en GitHub o un documento por este chat? ¿Y cómo dejará constancia de la aprobación? Muchas gracias.

**Respuesta del docente:** Puede continuar de forma autónoma la revisión de los requisitos se realizará junto con los demás entregables al finalizar el proyecto.

## 2. Decisiones del estudiante posteriores a la entrevista

Estas decisiones **no se consultaron con el docente** durante la entrevista. Se toman dentro de lo que él dejó a criterio del estudiante (E-03, E-06, E-10 y E-13) y se tratan como supuestos (ver sección 9 de [requisitos.md](requisitos.md)):

- Cuenta con usuario y contraseña para los tres roles; solicitantes con registro propio y personal creado previamente.
- Siete estados y reapertura fuera de alcance.
- Catálogo de servicios con marca «requiere adjunto».
- Adjuntos en PDF, JPG o PNG con tamaño máximo; visibles solo para el solicitante y el personal.
- Tipos de solicitante, cancelación antes de «En gestión», respuesta a solicitud de información y respuesta final con adjunto opcional.

## 3. Cuestiones pendientes

- La revisión formal de los requisitos queda para el final (E-13). Hasta entonces, todo lo no confirmado permanece marcado como supuesto.
- La respuesta E-09 llegó cortada. Se interpreta, junto con E-13, que se puede continuar con el diseño y el desarrollo de forma autónoma.
