# Spec Delta

## ADDED Requirements

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
