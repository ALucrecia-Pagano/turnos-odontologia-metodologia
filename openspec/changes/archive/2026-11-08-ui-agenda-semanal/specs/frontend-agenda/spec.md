# Spec Delta

## ADDED Requirements

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
