# frontend-agenda Specification

## Purpose
Agenda diaria de solo lectura sobre `GET /api/agenda` en el frontend SPA (`frontend/`): ruta protegida `/agenda` para los tres roles y redirección con `replace` desde `/` según el `Clock` inyectado; carga inyectable de turnos, profesionales y sillones sin reloj global; eje de horas y posicionamiento por minutos en hora local usando el `timezone` de la respuesta; bandas de horarios de atención y bloqueos rayados; tarjetas de turnos con color por estado y texto accesible, con cancelados atenuados pero visibles; filtros combinables por profesional y sillón reflejados en la URL; navegación por días con `Anterior`, `Siguiente`, `Hoy` y selector de fecha; estados de carga, vacío y error con reintento; delegación del `401` en C-26 y `403` visible sin cerrar sesión; vista alternativa en tabla semántica accesible y diseño responsive con scroll horizontal para escritorio y tablet.

## Requirements

### Requirement: Ruta /agenda y pantalla principal

La aplicación SHALL exponer la ruta protegida `/agenda` para los tres roles. La ruta `/` MUST redirigir con `replace` a `/agenda` con la fecha de hoy según el `Clock` inyectado. El menú MUST mostrar `Agenda` habilitada y MUST mantener el resto de los ítems futuros deshabilitados con `"Próximamente"`.

#### Scenario: / redirige a /agenda

- **GIVEN** una sesión autenticada y un `Clock` fijo en `2026-11-16T12:00:00Z`
- **WHEN** se navega a `/`
- **THEN** se redirige con `replace` a `/agenda?date=2026-11-16`
- **AND** no se renderiza `HomePage`

#### Scenario: Agenda habilitada en el menú de los tres roles

- **GIVEN** sesiones de `administrador`, `recepcion` y `odontologo`
- **WHEN** se renderiza el menú
- **THEN** `Agenda` es un enlace habilitado en los tres roles
- **AND** el resto de los ítems futuros sigue deshabilitado con `"Próximamente"`

### Requirement: Carga con fetch y Clock inyectados

Al abrir `/agenda`, la vista SHALL pedir la agenda del día seleccionado y MUST cargar profesionales y sillones con el `fetch` inyectado. La fecha inicial y la acción `Hoy` MUST calcularse con el `Clock` inyectado; la vista MUST NOT usar el reloj global del componente.

#### Scenario: Carga con fetch y Clock inyectados

- **GIVEN** un `Clock` fijo en `2026-11-16T12:00:00Z` y una URL sin `date`
- **AND** un `fetch` inyectado que responde la agenda del lunes con Quiroga y Sosa, el catálogo de profesionales y el de sillones
- **WHEN** se monta `/agenda`
- **THEN** se piden `GET /api/agenda?from=2026-11-16&to=2026-11-16`, `GET /api/professionals` y `GET /api/chairs`
- **AND** se muestran las columnas de Quiroga y Sosa

#### Scenario: La fecha inicial respeta el borde de medianoche

- **GIVEN** un `Clock` fijo en `2026-11-16T02:30:00Z` y la zona de respaldo `America/Argentina/Buenos_Aires`
- **WHEN** se monta `/agenda` sin `date`
- **THEN** la request usa `from=2026-11-15` y `to=2026-11-15`

### Requirement: Conversión a hora local con el timezone de la respuesta

La agenda MUST pedir `from`/`to` como fechas locales `YYYY-MM-DD` sin convertirlas a UTC. Toda hora y fecha visible MUST formatearse con el `timezone` de la respuesta de `GET /api/agenda`, nunca con la zona del navegador o del proceso. El único valor de respaldo MUST vivir en un archivo de configuración y usarse solo antes de la primera respuesta.

#### Scenario: 13:00Z se muestra como 10:00 en Buenos Aires

- **GIVEN** la respuesta de `GET /api/agenda` con `timezone` `"America/Argentina/Buenos_Aires"` y el turno de Quiroga `startAt` `2026-11-16T13:00:00Z` y `endAt` `2026-11-16T13:30:00Z`
- **WHEN** se renderiza la agenda del `2026-11-16`
- **THEN** la tarjeta muestra `10:00–10:30`
- **AND** la etiqueta del día es `lunes 16 de noviembre de 2026`

#### Scenario: El resultado es independiente de la zona del proceso

- **GIVEN** el mismo turno `2026-11-16T13:00:00Z` y la misma respuesta con `timezone` `America/Argentina/Buenos_Aires`
- **WHEN** el proceso de tests corre con `TZ=Asia/Tokyo` o formatea con una zona distinta
- **THEN** la hora mostrada sigue siendo `10:00` y la fecha `2026-11-16`

#### Scenario: Las fechas de la request son locales

- **GIVEN** la fecha `2026-11-16` en la URL
- **WHEN** se pide la agenda
- **THEN** la request usa `from=2026-11-16` y `to=2026-11-16` sin zona ni sufijo `Z`

### Requirement: Eje de horas

La grilla SHALL dibujar un eje de horas que cubra la unión de `workingHours`, `blocks` y turnos del día, clampeada a `[0, 1440]`, redondeada a la hora y con una hora de margen. Sin datos MUST usar `08:00–20:00`; un rango menor a 4 horas MUST expandirse a 4.

#### Scenario: Eje del lunes con datos

- **GIVEN** el día `2026-11-16` con horarios de Quiroga `09:00–13:00` y `15:00–19:00`, el bloqueo `12:00–13:00` y los turnos de Quiroga y Sosa
- **WHEN** se calcula y dibuja el eje
- **THEN** el eje va de `08:00` a `20:00`
- **AND** las horas se muestran una por línea

#### Scenario: Eje de un día vacío

- **GIVEN** el domingo `2026-11-15` sin horarios, bloqueos ni turnos
- **WHEN** se dibuja el eje
- **THEN** el eje va de `08:00` a `20:00`

### Requirement: Columnas por profesional

Cada columna MUST corresponder a un profesional del catálogo, incluidos los inactivos marcados `(inactivo)`, y MUST ordenarse de forma alfabética estable por nombre. Un profesional sin turnos MUST conservar su columna vacía. Con un `professionalId` en la URL MUST mostrarse solo esa columna.

#### Scenario: Tres columnas en orden estable

- **GIVEN** el catálogo con `Dra. Laura Quiroga`, `Dr. Martín Sosa` y `Dra. Paula Benítez` en cualquier orden
- **WHEN** se renderiza la agenda del `2026-11-16`
- **THEN** aparecen las tres columnas con esos nombres en orden alfabético
- **AND** el mismo catálogo en otro orden produce el mismo orden de columnas

#### Scenario: Profesional inactivo visible

- **GIVEN** el catálogo con `Dra. Paula Benítez` y `active: false`
- **WHEN** se renderiza la agenda
- **THEN** la columna muestra `Dra. Paula Benítez (inactivo)`

#### Scenario: Filtro por profesional deja una sola columna

- **GIVEN** la URL `/agenda?date=2026-11-16&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** se renderiza la agenda
- **THEN** la única columna es `Dra. Laura Quiroga`

### Requirement: Posición, alto y carriles de turnos superpuestos

Cada turno MUST posicionarse por sus minutos locales de inicio y fin, clampeados al día, con alto proporcional a su duración y un alto mínimo legible. Los turnos superpuestos MUST repartirse en carriles lado a lado, y un cancelado MUST poder compartir horario con un activo sin taparlo.

#### Scenario: Posición y alto del turno de Quiroga

- **GIVEN** el eje `08:00–20:00` y el turno de Quiroga de `13:00Z` a `13:30Z` (10:00–10:30 local)
- **WHEN** se posiciona la tarjeta
- **THEN** la tarjeta ocupa de `10:00` a `10:30`, es decir 120 minutos desde el inicio del eje y 30 minutos de alto

#### Scenario: Carriles para un cancelado y un activo superpuestos

- **GIVEN** un turno cancelado de Sosa y un turno activo de Sosa, ambos de `09:00` a `09:30` del `2026-11-16`
- **WHEN** se asignan los carriles
- **THEN** ambos turnos se ven lado a lado en dos carriles
- **AND** ninguno tapa al otro

#### Scenario: Turno de cinco minutos con alto mínimo

- **GIVEN** un turno de `09:00` a `09:05`
- **WHEN** se posiciona
- **THEN** la tarjeta conserva un alto mínimo legible y su nombre accesible incluye `09:00–09:05`

### Requirement: Horarios de atención, bloqueos y cancelados

Los horarios de atención MUST dibujarse como bandas de fondo por profesional y día de la semana. Los bloqueos MUST dibujarse como bandas con motivo y etiqueta accesible. Los turnos cancelados MUST permanecer visibles, atenuados y con la palabra `Cancelado`, sin reducir el contraste del texto.

#### Scenario: Horarios y bloqueo del lunes

- **GIVEN** los horarios de Quiroga `09:00–13:00` y `15:00–19:00` y el bloqueo `12:00–13:00` con motivo `Congreso`
- **WHEN** se renderiza la columna de Quiroga
- **THEN** se ven las bandas de horario y la banda rayada del bloqueo
- **AND** el bloqueo expone `Bloqueo: Congreso, de 12:00 a 13:00`

#### Scenario: El cancelado permanece visible

- **GIVEN** el turno cancelado de Sosa de `09:00` a `09:30`
- **WHEN** se renderiza la columna de Sosa
- **THEN** el turno se ve atenuado con el texto `Cancelado`
- **AND** no se oculta de la grilla

### Requirement: Color por estado más texto

El estado de cada turno MUST comunicarse con texto visible y MUST usar la paleta AA de estados; MUST NOT depender solo del color. La tarjeta MUST exponer un nombre accesible con hora, paciente, profesional, sillón, prestación y estado.

#### Scenario: Reservado y cancelado se distinguen por texto

- **GIVEN** el turno reservado de Quiroga y el cancelado de Sosa del `2026-11-16`
- **WHEN** se renderizan las tarjetas
- **THEN** una muestra `Reservado` y la otra `Cancelado`
- **AND** ambas usan el color AA de su estado sin depender solo del color

#### Scenario: Nombre accesible completo

- **GIVEN** el turno de Quiroga de `10:00` a `10:30` con Ana Pérez en Sillón 1 y `Control`
- **WHEN** se consulta la tarjeta
- **THEN** su nombre accesible incluye `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control` y `Reservado`

### Requirement: Filtros por profesional y sillón con estado en la URL

Los filtros de profesional y sillón MUST ser combinables y MUST vivir en la URL. `professionalId` MUST filtrar turnos, horarios y bloqueos; `chairId` MUST filtrar solo turnos y MUST mostrar una ayuda visible que aclare que horarios y bloqueos siguen visibles. `Limpiar filtros` MUST volver a `Todos` conservando la fecha.

#### Scenario: El filtro por sillón conserva horarios y bloqueos

- **GIVEN** la agenda del `2026-11-16` y el filtro `chairId` del Sillón 2
- **WHEN** se aplica el filtro
- **THEN** la URL incluye `chairId=00000000-0000-0000-0000-0000000000b2`
- **AND** solo se muestra el turno de Sosa del Sillón 2
- **AND** el bloqueo `Congreso` de Quiroga y los horarios de atención siguen visibles
- **AND** se muestra la ayuda del filtro por sillón

#### Scenario: El filtro por profesional filtra las tres colecciones

- **GIVEN** la agenda del `2026-11-16` y el filtro `professionalId` de Quiroga
- **WHEN** se aplica el filtro
- **THEN** la URL incluye `professionalId=00000000-0000-0000-0000-000000000001`
- **AND** se muestra solo la columna de Quiroga con sus turnos, horarios y bloqueos

#### Scenario: Filtros combinados sin turnos

- **GIVEN** los filtros Quiroga y Sillón 2
- **WHEN** se combinan
- **THEN** no se muestra ningún turno
- **AND** se mantienen las bandas y se muestra `Sin turnos para este filtro`

### Requirement: Navegación anterior, siguiente, Hoy y selector

La barra de navegación MUST ofrecer `Anterior`, `Siguiente`, `Hoy` y un selector de fecha. Cada cambio MUST actualizar `date` en la URL con `push` y MUST pedir ese día. `Anterior` y `Siguiente` MUST sumar o restar un día calendario, no 24 horas.

#### Scenario: Anterior y siguiente

- **GIVEN** la URL `/agenda?date=2026-11-16`
- **WHEN** se activa `Anterior`
- **THEN** la URL pasa a `/agenda?date=2026-11-15` con `push` y se pide ese día
- **AND** al activar `Siguiente` desde esa fecha la URL vuelve a `2026-11-16`

#### Scenario: Hoy y selector de fecha

- **GIVEN** un `Clock` fijo en `2026-11-16T12:00:00Z` y la URL `/agenda?date=2026-11-10`
- **WHEN** se activa `Hoy`
- **THEN** la URL pasa a `/agenda?date=2026-11-16`
- **AND** al elegir `2026-12-01` en el selector la URL pasa a `/agenda?date=2026-12-01`

### Requirement: Estados de carga, vacío y error

La vista MUST mostrar un estado de carga con `role="status"`, MUST conservar la grilla con un aviso cuando el día no tiene turnos y MUST mostrar un `ErrorState` con `Reintentar` ante error de red o `5xx`. La actualización MUST ser manual, sin polling.

#### Scenario: Carga inicial

- **GIVEN** `/agenda` montada y las requests pendientes
- **WHEN** se renderiza
- **THEN** se muestra un elemento `role="status"` con `Cargando...`
- **AND** no se muestra un error

#### Scenario: Día sin turnos

- **GIVEN** la agenda del `2026-11-16` con `appointments` vacío y horarios de atención
- **WHEN** termina la carga
- **THEN** se ve la grilla con `No hay turnos para este día`
- **AND** las bandas de horario siguen visibles

#### Scenario: Error de red con reintento

- **GIVEN** que `GET /api/agenda` falla por red
- **WHEN** termina la carga
- **THEN** se muestra un `ErrorState` con `Reintentar`
- **AND** al reintentar y recibir `200` se renderiza la agenda

### Requirement: 401 delegado en C-26 y 403 visible

Un `401` de una request de agenda MUST delegarse en C-26: MUST limpiar la sesión y redirigir a `/login` con `La sesión venció. Iniciá sesión de nuevo.`, y la vista MUST NOT mostrar un error local. Un `403` MUST mostrar los mensajes de `violations` y MUST NOT cerrar la sesión.

#### Scenario: 401 durante el uso

- **GIVEN** una sesión autenticada y `GET /api/agenda` responde `401` con `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }`
- **WHEN** termina la request
- **THEN** el token se descarta y se redirige a `/login` con `La sesión venció. Iniciá sesión de nuevo.`
- **AND** la agenda no muestra un error local

#### Scenario: 403 con la violación visible

- **GIVEN** una sesión autenticada y `GET /api/agenda` responde `403` con `{ "violations": [{ "code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para leer la agenda." }] }`
- **WHEN** termina la request
- **THEN** se muestra exactamente `No tiene permiso para leer la agenda.`
- **AND** la sesión sigue autenticada y no se redirige

### Requirement: Vista en lista accesible

La vista MUST ofrecer un toggle visible `Ver como lista` que MUST renderizar una tabla semántica con `caption` y encabezados `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado`, con los mismos datos y orden que la grilla. La grilla MUST exponer nombres accesibles y anunciar la cantidad de turnos con `aria-live`.

#### Scenario: Tabla accesible del lunes

- **GIVEN** la agenda del `2026-11-16` con los turnos de Quiroga y Sosa
- **WHEN** se activa `Ver como lista`
- **THEN** la tabla tiene el caption `Turnos del lunes 16 de noviembre de 2026`
- **AND** los encabezados son `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado`
- **AND** la fila de Quiroga es `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control`, `Reservado`

#### Scenario: Anuncio de la cantidad de turnos

- **GIVEN** la agenda del `2026-11-16` con dos turnos
- **WHEN** termina la carga
- **THEN** la región `aria-live` anuncia `Turnos del lunes 16 de noviembre de 2026: 2`

### Requirement: Responsive para escritorio y tablet

La vista MUST ser usable en escritorio y tablet: con varias columnas MUST permitir scroll horizontal, MUST mantener fijos el encabezado de profesionales y la columna de horas, y MUST ofrecer controles de al menos 44×44 px sin información exclusiva de `hover`.

#### Scenario: Tablet de 768 por 1024

- **GIVEN** un viewport de `768×1024` con tres columnas
- **WHEN** se renderiza la agenda
- **THEN** la barra de herramientas se acomoda en varias líneas
- **AND** la grilla permite scroll horizontal con el encabezado de profesionales y la columna de horas fijos
- **AND** los controles miden al menos `44×44` px y no dependen de `hover`

### Requirement: Alternancia entre vista diaria y semanal
La aplicación SHALL ofrecer un control para alternar entre vista diaria y semanal en `/agenda`. El parámetro `view` en la URL SHALL definir la vista activa: `view=week` activa la vista semanal, mientras que `view=day`, un valor desconocido o la ausencia del parámetro MUST activar la vista diaria. Al alternar entre vistas, se MUST conservar la fecha `date` y los filtros `professionalId` y `chairId`.

#### Scenario: Alternancia de día a semana conservando fecha y filtros
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1` en vista diaria
- **WHEN** el usuario pulsa el control "Semana"
- **THEN** la URL pasa a `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1&view=week`
- **AND** se muestra la grilla semanal con los 7 días correspondientes

#### Scenario: Alternancia de semana a día conservando el día exacto
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&view=week&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1`
- **WHEN** el usuario pulsa el control "Día"
- **THEN** la URL queda sin `view` o con `view=day` conservando `date=2026-11-18`, `professionalId` y `chairId`
- **AND** se muestra la agenda diaria del 18 de noviembre de 2026

#### Scenario: Un view desconocido o ausente cae a vista diaria
- **GIVEN** una sesión autenticada en `/agenda?date=2026-11-16&view=invalido`
- **WHEN** se renderiza la página
- **THEN** la vista activa es la vista diaria con columnas por profesional
- **AND** el botón "Día" del selector figura seleccionado

### Requirement: Vista semanal por profesional y grilla de siete días
En vista semanal, la aplicación SHALL renderizar siete columnas correspondientes a los días lunes a domingo de la semana que contiene `date`. Si no se especifica `professionalId`, para rol `odontologo` SHALL seleccionarse su propio id, y para `recepcion` o `administrador` el primer profesional activo en el mismo orden del selector de profesionales. Cada turno MUST ubicarse en la columna de su día local según el `timezone` de la respuesta, con cancelados visibles con texto.

#### Scenario: Grilla de siete días de lunes a domingo
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&view=week&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** termina la carga de la agenda
- **THEN** se renderizan 7 columnas con fechas de `2026-11-16` (lunes) a `2026-11-22` (domingo)
- **AND** cada columna muestra su día de la semana y fecha local correspondiente

#### Scenario: La semana se pide en una sola llamada
- **GIVEN** una sesión autenticada con `fetch` inyectado y la URL `/agenda?date=2026-11-18&view=week&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** se monta y carga la vista semanal
- **THEN** se realiza exactamente una llamada a `GET /api/agenda` con `from=2026-11-16`, `to=2026-11-22` y `professionalId=00000000-0000-0000-0000-000000000001`

#### Scenario: Turno en el día local correcto según timezone
- **GIVEN** un turno con `startAt` en `2026-11-17T01:30:00Z` y respuesta con `timezone` `"America/Argentina/Buenos_Aires"` (-03:00)
- **WHEN** se renderiza la vista semanal de esa semana
- **THEN** el turno aparece ubicado en la columna del lunes `2026-11-16` a las `22:30` local
- **AND** no aparece en la columna del martes `2026-11-17`

#### Scenario: Preselección por rol odontólogo
- **GIVEN** un usuario autenticado con rol `odontologo` vinculado a `00000000-0000-0000-0000-000000000002` ("Dr. Martín Sosa")
- **WHEN** accede a `/agenda?date=2026-11-16&view=week` sin `professionalId`
- **THEN** la vista semanal selecciona automáticamente al "Dr. Martín Sosa"
- **AND** se cargan y muestran los turnos de la semana de ese profesional

#### Scenario: Preselección por rol recepción o administrador
- **GIVEN** un usuario con rol `recepcion` y profesionales activos "Dr. Martín Sosa" y "Dra. Laura Quiroga"
- **WHEN** accede a `/agenda?date=2026-11-16&view=week` sin `professionalId`
- **THEN** la vista selecciona por defecto al "Dr. Martín Sosa" en el mismo orden del selector
- **AND** el selector de profesional permite cambiar a cualquier otro profesional

#### Scenario: Turno cancelado visible con texto en vista semanal
- **GIVEN** un turno con estado `cancelado` de la Dra. Laura Quiroga el miércoles `2026-11-18`
- **WHEN** se renderiza la vista semanal de esa profesional
- **THEN** la tarjeta se muestra en la columna del miércoles con la clase visual de cancelado
- **AND** incluye el texto visible "Cancelado"

### Requirement: Navegación semanal
En vista semanal, los controles de navegación SHALL mostrar los textos visibles y accesibles "Semana anterior" y "Semana siguiente", desplazando la fecha siete días hacia atrás o hacia adelante con `addDays`. La navegación MUST operar sobre días calendarios admitiendo transiciones que cruzan mes y año. El botón "Hoy" MUST navegar a la semana que contiene la fecha actual del `Clock`.

#### Scenario: Navegación semanal que cruza mes y año
- **GIVEN** la URL `/agenda?date=2026-12-28&view=week&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** el usuario pulsa "Semana siguiente"
- **THEN** la URL se actualiza a `/agenda?date=2027-01-04&view=week&professionalId=00000000-0000-0000-0000-000000000001`
- **AND** la grilla muestra la semana del 4 al 10 de enero de 2027
- **AND** al pulsar "Semana anterior" vuelve a la semana del 28 de diciembre de 2026

#### Scenario: Botón Hoy en vista semanal
- **GIVEN** un `Clock` fijo en `2026-11-18T12:00:00Z` y la URL `/agenda?date=2026-12-15&view=week`
- **WHEN** el usuario pulsa "Hoy"
- **THEN** la URL navega a `/agenda?date=2026-11-18&view=week`
- **AND** se muestra la semana del 16 al 22 de noviembre de 2026

### Requirement: Indicador accesible de día actual
En vista semanal, la columna correspondiente al día de hoy según el `Clock` inyectado SHALL identificarse en su cabecera con el texto visible "Hoy" y el atributo `aria-current="date"`. La distinción MUST NOT depender únicamente del color.

#### Scenario: Marca Hoy con texto visible y aria-current
- **GIVEN** un `Clock` fijo en `2026-11-18T12:00:00Z` (miércoles) y la semana del `2026-11-16` al `2026-11-22`
- **WHEN** se renderiza la grilla semanal
- **THEN** la cabecera de la columna del miércoles contiene el texto visible "Hoy"
- **AND** dicha cabecera expone el atributo `aria-current="date"`

### Requirement: Estado vacío y visualización en tablet para vista semanal
En vista semanal, una semana sin turnos para el profesional SHALL mantener la grilla con sus horarios de atención y bloqueos visibles y MUST mostrar el aviso "No hay turnos esta semana para [profesional]". En viewport de tablet (768 px), la grilla SHALL permitir scroll horizontal y las tarjetas en columnas estrechas MUST adoptar el formato compacto de dos líneas con paciente y badge de estado.

#### Scenario: Semana vacía con grilla y aviso informativo
- **GIVEN** la Dra. Laura Quiroga con horarios configurados pero sin turnos registrados entre el `2026-11-16` y el `2026-11-22`
- **WHEN** termina la carga de la vista semanal
- **THEN** se dibuja la grilla con las bandas de horario y bloqueos de los 7 días
- **AND** se visualiza el aviso "No hay turnos esta semana para Dra. Laura Quiroga"

#### Scenario: Semana vacía con filtro de sillón
- **GIVEN** la vista semanal del `2026-11-16` al `2026-11-22` con `chairId=00000000-0000-0000-0000-0000000000b1` activo y sin turnos registrados
- **WHEN** termina la carga de la agenda
- **THEN** se muestra la grilla con horarios y bloqueos visibles
- **AND** se visualiza el aviso de filtro "Sin turnos para este filtro"
- **AND** no se visualiza el aviso "No hay turnos esta semana para [profesional]"

#### Scenario: Tarjetas en dos líneas en tablet
- **GIVEN** un viewport de 768 px con la vista semanal activa y un turno de 30 minutos de Ana Pérez
- **WHEN** se renderiza la columna del día
- **THEN** la estructura CSS del contenedor provee `overflow-x: auto` con la columna de horas sticky, verificado estáticamente y con captura visual a 768 px
- **AND** la tarjeta del turno presenta dos líneas: hora y paciente en la primera y badge de estado visible en la segunda

### Requirement: Llamada semanal con profesional preseleccionado y alcance de turnos
En vista semanal con preselección automática por omisión de `professionalId`, la aplicación SHALL enviar el identificador del profesional preseleccionado en la única llamada a `GET /api/agenda`. El contador de turnos anunciados y la vista de lista MUST incluir exclusivamente los turnos pertenecientes al profesional seleccionado.

#### Scenario: Preselección automática envía professionalId en la única llamada semanal
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&view=week` sin `professionalId` en la URL y profesionales activos con turnos registrados
- **WHEN** se carga la vista semanal
- **THEN** se realiza una única llamada a `GET /api/agenda` incluyendo el `professionalId` del "Dr. Martín Sosa" (primer profesional activo)
- **AND** el contador anuncia únicamente la cantidad de turnos de ese profesional
- **AND** la vista de lista muestra exclusivamente sus turnos

### Requirement: Encabezado, título y contador en vista semanal
En vista semanal, la aplicación SHALL titular la página como "Agenda semanal" y el contador accesible MUST anunciar "Turnos de la semana: N". El encabezado principal SHALL mostrar el rango semanal con el formato "Semana del [D] al [D] de [mes] de [año]", y en caso de cruce de mes o de año MUST incluir el mes o año respectivo en cada extremo.

#### Scenario: Textos y encabezados en vista semanal con cruce de año
- **GIVEN** la vista semanal en `/agenda?date=2026-11-18&view=week` con turnos registrados
- **WHEN** se renderiza la página
- **THEN** el título de la página es "Agenda semanal"
- **AND** el encabezado principal muestra "Semana del 16 al 22 de noviembre de 2026"
- **AND** el contador anuncia "Turnos de la semana: N"
- **AND** al navegar al 28 de diciembre de 2026 el encabezado muestra "Semana del 28 de diciembre de 2026 al 3 de enero de 2027"

### Requirement: Vista de lista en modo semanal
Al activar "Ver como lista" en vista semanal, la tabla SHALL presentar un caption descriptivo con el rango de la semana. La tabla MUST incorporar una columna "Fecha" con el día y fecha local formateados (ej. "lun 16/11") y las filas MUST presentarse ordenadas cronológicamente por fecha y hora de inicio.

#### Scenario: Tabla de turnos semanal con columna de fecha y orden cronológico
- **GIVEN** la vista semanal con turnos distribuidos en diferentes días de la semana
- **WHEN** el usuario pulsa "Ver como lista"
- **THEN** el caption de la tabla describe el rango de la semana
- **AND** la tabla incluye la columna "Fecha" con el formato "lun 16/11"
- **AND** los turnos aparecen ordenados por fecha y hora cronológica

### Requirement: Ancho de columnas semanales en escritorio y tablet
En vista semanal sobre pantallas de escritorio (≥ 1280 px), las siete columnas de lunes a domingo SHALL mostrarse simultáneamente visibles sin requerir scroll horizontal. El ancho de las columnas semanales SHALL definirse mediante un token CSS semántico sin un mínimo de 220 px. En viewport de tablet, el contenedor MUST conservar `overflow-x: auto` y columna de horas sticky.

#### Scenario: Columnas semanales visibles en escritorio y adaptables en tablet
- **GIVEN** los estilos de la grilla semanal
- **WHEN** se evalúa la definición de columnas
- **THEN** el contenedor define columnas semanales con ancho regulado por token semántico sin min-width de 220 px
- **AND** en tablet el contenedor preserva scroll horizontal y columna de horas sticky

### Requirement: Acción Nuevo turno en la agenda

La barra de herramientas de la agenda SHALL incorporar la acción "Nuevo turno" únicamente para usuarios autenticados con rol `recepcion` o `administrador`. El botón MUST NOT estar presente en el DOM para el rol `odontologo`. Al activar la acción, MUST abrirse el diálogo modal de alta de turnos y, al completarse exitosamente la creación de un turno, la vista MUST refrescar los datos de la agenda mediante `useAgenda`.

#### Scenario: Visible para recepción

- **GIVEN** un usuario autenticado con rol `recepcion` en `/agenda`
- **WHEN** se renderiza la barra de herramientas de la agenda
- **THEN** se muestra el botón "Nuevo turno" habilitado
- **AND** al activarlo se abre el formulario de dar turno

#### Scenario: Visible para administrador

- **GIVEN** un usuario autenticado con rol `administrador` en `/agenda`
- **WHEN** se renderiza la barra de herramientas de la agenda
- **THEN** se muestra el botón "Nuevo turno" habilitado
- **AND** al activarlo se abre el formulario de dar turno

#### Scenario: No visible para odontólogo

- **GIVEN** un usuario autenticado con rol `odontologo` en `/agenda`
- **WHEN** se renderiza la barra de herramientas de la agenda
- **THEN** el botón "Nuevo turno" no está presente en el DOM

#### Scenario: Refresco tras alta

- **GIVEN** la agenda abierta con el modal de nuevo turno
- **WHEN** se completa la creación exitosa de un turno desde el formulario
- **THEN** se invoca el refresco de los datos de la agenda mediante `useAgenda`
