# Spec Delta

## Purpose

Formulario modal para dar turnos desde la agenda (`frontend/`), autorizado para recepción y administración. Incluye la primitiva accesible `Dialog`, búsqueda de pacientes con radio buttons, duración sugerida y cálculo de offset horario nativo de la API. Muestra fielmente los rechazos de dominio (409, 422, 400, 403) en un resumen superior con `role="alert"` conservando las referencias de colisión. Al responder 201 Created, cierra el modal, refresca la agenda y emite confirmación accesible.

## ADDED Requirements

### Requirement: Primitiva de diálogo modal accesible

El componente `Dialog` SHALL renderizar un elemento `<dialog>` nativo accesible sin el atributo redundante `role="dialog"`. MUST requerir `aria-labelledby` y aplicar `aria-modal="true"` solo cuando no haya `showModal`. En entornos como `jsdom`, MUST abrirse mediante el atributo `open`. Al presionar la tecla Escape, MUST invocar `onClose` exactamente una vez. Al cambiar la propiedad `open` de `true` a `false`, el foco MUST retornar exactamente una vez a `returnFocusRef`.

#### Scenario: Abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby

- **GIVEN** un componente `Dialog` renderizado en un entorno de pruebas con `open=true` y un título asociado por `labelledBy`
- **WHEN** se evalúa el elemento en el DOM
- **THEN** el elemento `<dialog>` posee el atributo `open`
- **AND** no posee el atributo redundante `role="dialog"`
- **AND** expone su nombre accesible a través de `aria-labelledby`

#### Scenario: Escape llama onClose exactamente una vez

- **GIVEN** el diálogo modal abierto con un callback `onClose` asignado
- **WHEN** el usuario presiona la tecla Escape sobre el diálogo
- **THEN** el callback `onClose` se invoca exactamente una vez

#### Scenario: Al pasar open de true a false el foco vuelve a returnFocusRef

- **GIVEN** el diálogo modal abierto asociado a un elemento disparador mediante `returnFocusRef`
- **WHEN** la propiedad `open` cambia de `true` a `false`
- **THEN** el foco del navegador se traslada exactamente una vez al elemento referenciado por `returnFocusRef`

### Requirement: Apertura y foco inicial

El formulario de alta de turnos SHALL estructurarse como un diálogo modal accesible montado sobre la página de agenda. Al abrirse el modal, el foco MUST posicionarse en el primer control interactivo del formulario.

#### Scenario: Apertura y foco inicial

- **GIVEN** la página de agenda con el diálogo modal de dar turno cerrado
- **WHEN** se activa la apertura del formulario de nuevo turno
- **THEN** se abre el diálogo modal de dar turno
- **AND** el foco se posiciona en el primer campo interactivo del formulario

### Requirement: Prellenado contextual desde la agenda

Al abrirse, el formulario SHALL inicializar la fecha con la fecha activa de la agenda. Si la toolbar posee un filtro de profesional o sillón seleccionado, o la vista semanal define un profesional, dichos valores MUST venir preseleccionados en los campos correspondientes.

#### Scenario: Prellenado con fecha y filtros activos

- **GIVEN** la agenda en la fecha `2026-11-16` con filtro de profesional Quiroga y filtro de Sillón 1
- **WHEN** se abre el formulario de dar turno
- **THEN** el campo de fecha contiene `2026-11-16`
- **AND** el selector de profesional tiene preseleccionada a la Dra. Laura Quiroga
- **AND** el selector de sillón tiene preseleccionado al Sillón 1

#### Scenario: Sin filtros activos los selectores quedan sin selección

- **GIVEN** la agenda en la fecha `2026-11-16` sin filtros de profesional ni sillón activos
- **WHEN** se abre el formulario de dar turno
- **THEN** el campo de fecha contiene `2026-11-16`
- **AND** los selectores de profesional y sillón se encuentran sin selección inicial

### Requirement: Búsqueda y selección de paciente

La selección de paciente SHALL realizarse mediante un campo de texto y un botón "Buscar paciente" que consulte `GET /api/patients?query=`. Los resultados MUST desplegarse como un grupo de radio buttons con nombre y DNI. Si la búsqueda no arroja coincidencias, MUST mostrarse un aviso accesible.

#### Scenario: Búsqueda con resultados muestra radio buttons

- **GIVEN** el formulario de turno abierto y el texto "Pérez" en el campo de búsqueda
- **WHEN** se activa el botón "Buscar paciente" o se presiona Enter en el input
- **THEN** se realiza la consulta `GET /api/patients?query=P%C3%A9rez`
- **AND** se muestra un grupo de radio buttons con los pacientes devueltos
- **AND** cada opción expone el nombre completo y el DNI formateado

#### Scenario: Búsqueda sin coincidencias muestra aviso

- **GIVEN** el formulario de turno abierto y un texto que no coincide con ningún paciente
- **WHEN** se ejecuta la búsqueda de pacientes
- **THEN** se muestra un mensaje accesible indicando que no se encontraron pacientes
- **AND** no se listan radio buttons

#### Scenario: Selección de radio button asigna patientId

- **GIVEN** la lista de radio buttons con los pacientes coincidentes
- **WHEN** se selecciona la opción correspondiente a "Ana Pérez"
- **THEN** el valor de `patientId` queda seleccionado en el estado del formulario

### Requirement: Sugerencia y edición de duración

Al seleccionar una prestación, el formulario SHALL inicializar el campo de duración con la duración por defecto de dicha prestación. El operador MUST poder editar la duración manualmente en múltiplos de 5 minutos, dentro del rango permitido de 5 a 480 minutos.

#### Scenario: Duración sugerida al elegir prestación

- **GIVEN** el formulario de turno abierto con catálogo de prestaciones cargado
- **WHEN** se selecciona la prestación "Extracción" con duración por defecto de 60 minutos
- **THEN** el campo de duración se inicializa automáticamente con el valor 60

#### Scenario: Edición manual de duración

- **GIVEN** la prestación "Extracción" seleccionada con duración 60 minutos
- **WHEN** el usuario modifica el valor del campo duración a 45 minutos
- **THEN** el campo conserva el valor 45
- **AND** dicho valor será el enviado en `durationMin`

### Requirement: Composición de fecha, hora y timezone

Los campos de fecha y hora SHALL ser inputs nativos date y time con paso de 5 minutos. Al enviar la solicitud, el cliente MUST componer startAt en formato ISO con el offset local correspondiente a la fecha y hora elegidas, empleando la zona horaria provista por la API.

#### Scenario: startAt incluye offset horario exacto para la fecha elegida

- **GIVEN** fecha `2026-11-16`, hora `10:00` y `timezone` de la API `America/Argentina/Buenos_Aires`
- **WHEN** se envía el formulario
- **THEN** el cuerpo enviado a `POST /api/appointments` contiene `startAt` igual a `2026-11-16T10:00:00-03:00`

### Requirement: Renderizado de violaciones de dominio 409 y 422

Ante respuestas 409 o 422, el formulario SHALL mostrar todas las violaciones devueltas en un resumen superior con role="alert". Cada violación MUST incluir su código estable, su mensaje textual íntegro y la referencia al turno o bloqueo en conflicto. MUST NOT mapear violaciones a campos individuales.

#### Scenario: Conflicto múltiple 409 muestra todas las violaciones con sus referencias

- **GIVEN** un intento de alta que colisiona con el profesional y con el sillón a la vez
- **WHEN** la API responde 409 con `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`
- **THEN** ambas violaciones se muestran en el alert de resumen con sus mensajes textuales
- **AND** se incluyen las referencias a los turnos en conflicto
- **AND** los campos del formulario no se marcan con `aria-invalid`

#### Scenario: Rechazo 422 muestra violaciones en el resumen

- **GIVEN** un intento de alta con fecha en el pasado
- **WHEN** la API responde 422 con la violación `IN_THE_PAST`
- **THEN** el mensaje textual de la API se muestra en el alert de resumen

### Requirement: Errores de validación 400 y permisos 403

Ante un error 400 con lista de errores, el formulario SHALL marcar con aria-invalid="true" los campos afectados y presentar el mensaje junto a cada control. Ante un 403 FORBIDDEN_OPERATION, MUST mostrar el mensaje en el alert de resumen. Ante error, el foco MUST trasladarse al resumen.

#### Scenario: Error 400 marca campo con aria-invalid

- **GIVEN** una respuesta 400 de la API con error en el campo `durationMin`
- **WHEN** se procesa la respuesta de error
- **THEN** el campo de duración queda marcado con `aria-invalid="true"`
- **AND** se visualiza el mensaje de error junto al control y en el resumen

#### Scenario: Error 403 muestra mensaje de rechazo

- **GIVEN** una respuesta 403 de la API con código `FORBIDDEN_OPERATION`
- **WHEN** se procesa la respuesta
- **THEN** el mensaje de permiso denegado se muestra en el alert de resumen

#### Scenario: Foco se traslada al resumen de alerta ante fallo

- **GIVEN** el formulario enviado con datos que provocan un rechazo 409, 422, 400 o 403
- **WHEN** se recibe la respuesta con error
- **THEN** el foco del navegador se traslada programáticamente al contenedor `role="alert"`

### Requirement: Éxito, refresco de agenda y retorno de foco

Al responder 201 Created, el diálogo SHALL cerrarse, limpiar el estado del formulario, invocar el refresco de la agenda en useAgenda y emitir un anuncio accesible con role="status". Al cerrarse por éxito o cancelación, el foco MUST regresar al botón "Nuevo turno".

#### Scenario: Alta exitosa 201 refresca agenda y anuncia resultado

- **GIVEN** un formulario completo con datos válidos
- **WHEN** se envía y la API responde 201 Created
- **THEN** el diálogo modal se cierra
- **AND** se invoca la función `refresh()` de `useAgenda`
- **AND** se emite un anuncio para lectores de pantalla con `role="status"` confirmando la creación
- **AND** el foco retorna al botón "Nuevo turno"

#### Scenario: Cancelación retorna el foco

- **GIVEN** el diálogo modal abierto
- **WHEN** el usuario pulsa el botón "Cancelar" o presiona la tecla Escape
- **THEN** el diálogo se cierra sin enviar solicitudes
- **AND** el foco retorna al botón "Nuevo turno"

### Requirement: Adaptabilidad visual del formulario

El diálogo modal SHALL adaptarse visualmente a pantallas de escritorio (1440 px), tablet (768 px) y móvil (390 px), garantizando legibilidad, controles táctiles de al menos 44 px de altura y ausencia de desborde horizontal.

#### Scenario: Visualización en escritorio a 1440 px

- **GIVEN** el formulario abierto en un viewport de 1440 px de ancho
- **WHEN** se visualiza el contenido del modal
- **THEN** el diálogo se presenta centrado con campos dispuestos ordenadamente
- **AND** el alert de violaciones muestra textos largos sin desbordes
- **AND** esta verificación es visual (captura), no un test de Vitest

#### Scenario: Visualización en tablet a 768 px

- **GIVEN** el formulario abierto en un viewport de 768 px de ancho
- **WHEN** se visualiza la lista de radio buttons de pacientes y los botones de acción
- **THEN** los controles táctiles cumplen con una altura mínima de 44 px
- **AND** no se produce scroll horizontal dentro del modal
- **AND** esta verificación es visual (captura), no un test de Vitest

#### Scenario: Visualización en móvil a 390 px

- **GIVEN** el formulario abierto en un viewport de 390 px de ancho
- **WHEN** se visualiza la disposición de los campos y controles
- **THEN** el formulario adopta una disposición vertical de una sola columna
- **AND** los botones de acción se adaptan al ancho disponible sin desbordar
- **AND** esta verificación es visual (captura), no un test de Vitest
