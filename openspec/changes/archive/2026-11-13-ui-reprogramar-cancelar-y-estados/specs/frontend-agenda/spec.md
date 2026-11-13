# Spec Delta

## ADDED Requirements

### Requirement: Turnos accionables en la agenda

Cada turno renderizado en la grilla temporal de la agenda SHALL ser un elemento interactivo `<button type="button">` con foco visible mediante `--color-focus` y un nombre accesible que incluya horario, paciente, prestación, profesional, sillón y estado. La escala porcentual de la grilla MUST NOT alterarse con alturas mínimas forzadas. En la vista de tabla alternativa, cada fila MUST incorporar una acción accesible "Ver turno" al estar disponible la selección.

#### Scenario: Tarjeta de turno como botón accesible en la grilla

- **GIVEN** la agenda diaria con un turno agendado
- **WHEN** se renderiza la grilla de agenda (`AgendaGrid`)
- **THEN** el turno se presenta como un `<button type="button">`
- **AND** posee un `aria-label` completo con hora, paciente, prestación, profesional, sillón y estado
- **AND** al recibir foco de teclado expone el contorno visible con `--color-focus`

#### Scenario: Selección de turno en la grilla abre el detalle

- **GIVEN** la grilla de agenda con turnos visibles y un callback de selección configurado
- **WHEN** el usuario hace clic o presiona Enter sobre la tarjeta del turno
- **THEN** se invoca la acción de selección con los datos del turno correspondiente

#### Scenario: Fila de tabla con acción accesible Ver turno

- **GIVEN** la agenda visualizada en modo tabla (`AgendaTable`) con turnos y selección disponible
- **WHEN** se renderizan las filas de la tabla
- **THEN** cada turno presenta un botón accesible "Ver turno"
- **AND** al activarlo se invoca la selección del turno
