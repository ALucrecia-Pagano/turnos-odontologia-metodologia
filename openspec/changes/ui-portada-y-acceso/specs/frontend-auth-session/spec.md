# Spec Delta

## MODIFIED Requirements

### Requirement: Bajada y tarjeta del login

El login SHALL mostrar la bajada "Claridad en cada cuidado." en el hero de la portada y el formulario dentro de una tarjeta tipo vidrio sobre un overlay degradado navy en el diálogo de acceso. MUST conservar el heading "Turnos Odontología".

#### Scenario: La bajada es visible

- **GIVEN** la portada de login renderizada
- **WHEN** se consulta el texto de la portada
- **THEN** la bajada "Claridad en cada cuidado." es visible en el hero
- **AND** no se repite dentro del diálogo

#### Scenario: La tarjeta tipo vidrio sobre overlay navy

- **GIVEN** el diálogo de acceso abierto
- **WHEN** se observa la tarjeta del formulario
- **THEN** la tarjeta tiene efecto vidrio sobre un overlay degradado navy
- **AND** esta verificación es visual (captura), no un test de Vitest
