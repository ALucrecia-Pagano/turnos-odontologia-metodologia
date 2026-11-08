# Spec Delta

## ADDED Requirements

### Requirement: Alternancia entre vista diaria y semanal
La aplicación SHALL ofrecer un control para alternar entre vista diaria y semanal en `/agenda`. El parámetro `view` en la URL SHALL definir la vista activa: `view=week` activa la vista semanal, mientras que `view=day`, un valor desconocido o la ausencia del parámetro MUST activar la vista diaria. Al alternar entre vistas, se MUST conservar la fecha `date` y los filtros `professionalId` y `chairId`.

#### Scenario: Alternancia de día a semana conservando fecha y filtros
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1` en vista diaria
- **WHEN** el usuario pulsa el control "Semana"
- **THEN** la URL pasa a `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1&view=week`
- **AND** se muestra la grilla semanal con los 7 días correspondientes

#### Scenario: Un view desconocido o ausente cae a vista diaria
- **GIVEN** una sesión autenticada en `/agenda?date=2026-11-16&view=invalido`
- **WHEN** se renderiza la página
- **THEN** la vista activa es la vista diaria con columnas por profesional
- **AND** el botón "Día" del selector figura seleccionado

### Requirement: Vista semanal por profesional y grilla de siete días
En vista semanal, la aplicación SHALL renderizar siete columnas correspondientes a los días lunes a domingo de la semana que contiene `date`. Si no se especifica `professionalId`, para rol `odontologo` SHALL seleccionarse su propio id, y para `recepcion` o `administrador` el primer profesional activo en orden alfabético. Cada turno MUST ubicarse en la columna de su día local según el `timezone` de la respuesta, con cancelados visibles con texto.

#### Scenario: Grilla de siete días de lunes a domingo
- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&view=week&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** termina la carga de la agenda
- **THEN** se renderizan 7 columnas con fechas de `2026-11-16` (lunes) a `2026-11-22` (domingo)
- **AND** cada columna muestra su día de la semana y fecha local correspondiente

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
- **THEN** la vista selecciona por defecto a la "Dra. Laura Quiroga" por orden alfabético
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

#### Scenario: Tarjetas en dos líneas en tablet
- **GIVEN** un viewport de 768 px con la vista semanal activa y un turno de 30 minutos de Ana Pérez
- **WHEN** se renderiza la columna del día
- **THEN** el contenedor permite scroll horizontal conservando la columna de horas fija
- **AND** la tarjeta del turno presenta dos líneas: hora y paciente en la primera y badge de estado visible en la segunda
