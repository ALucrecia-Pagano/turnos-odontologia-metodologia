# Spec Delta

## MODIFIED Requirements

### Requirement: Navegación anterior, siguiente, Hoy y selector

La barra de navegación MUST ofrecer Anterior, Siguiente, Hoy, un selector de fecha y, para recepción y administración, la acción Nuevo turno. Cada cambio de fecha MUST actualizar date en la URL con push. Anterior y Siguiente MUST sumar o restar un día calendario. Tras crear un turno exitosamente, la vista MUST refrescar la agenda mediante useAgenda.

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

#### Scenario: Acción Nuevo turno visible según rol y refresco tras alta

- **GIVEN** un usuario autenticado con rol `recepcion` en `/agenda`
- **WHEN** se visualiza la barra de herramientas de la agenda
- **THEN** se expone la acción "Nuevo turno"
- **AND** al completarse la creación de un turno se invoca el refresco de la vista
