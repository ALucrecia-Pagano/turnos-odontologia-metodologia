# Spec Delta: appointment-scheduling

## MODIFIED Requirements

### Requirement: Alta de un turno válido
Si el pedido es válido (referencias activas, duración e inicio en grilla de 5 min, un solo día local e inicio >= `now`) y no choca con la agenda (dentro del horario del profesional y sin bloqueos ni turnos ocupantes del profesional o sillón), el dominio SHALL devolver `Ok` con el turno `reservado` (RN-TU-01), inicio/fin UTC y el id y referencias recibidos sin generar id (por defecto en escenarios: referencias activas, horario `[0, 1440)`, sin bloqueos, `now` `2026-10-01T00:00:00Z`).

#### Scenario: Turno válido con profesional y sillón libres
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente para P1 ni para S1
- **WHEN** se pide un turno con el id `T-NUEVO`, para P1 en S1, a las 13:00 y sin duración explícita
- **THEN** el resultado es `Ok`
- **AND** el turno devuelto tiene el id `T-NUEVO`, va de 13:00 a 13:30, está en estado `reservado` y conserva el paciente, el profesional, el sillón y la prestación pedidos

#### Scenario: Turno válido con otros turnos que no chocan
- **GIVEN** el turno existente A
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 15:00
- **THEN** el resultado es `Ok` con el turno de 15:00 a 15:30 en estado `reservado`

### Requirement: Todas las violaciones, en orden estable
El dominio SHALL evaluar el pedido en dos grupos y devolver todas las violaciones del primer grupo que falle, sin mezclar grupos (RN-AG-12, DD-08, US-006 CA-2). Primero evalúa la validez en orden: paciente, profesional, sillón, prestación, duración, inicio, medianoche y pasado (`IN_THE_PAST` se evalúa siempre, aun sin duración efectiva o válida). Si hay violaciones de validez, MUST NOT evaluar los conflictos de agenda.

#### Scenario: Varios conflictos de ambos tipos
- **GIVEN** un turno B de P1 en S2 de 13:30 a 14:00, un turno C de P1 en S3 de 13:00 a 13:30 y un turno D de P2 en S1 de 13:45 a 14:15
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 14:00
- **THEN** el resultado es `Rejected` con exactamente tres violaciones, en este orden: `PROFESSIONAL_OVERLAP` con el turno C, `PROFESSIONAL_OVERLAP` con el turno B y `CHAIR_OVERLAP` con el turno D

#### Scenario: Orden independiente del orden de la lista recibida
- **GIVEN** los mismos turnos B, C y D del escenario anterior, recibidos en orden inverso
- **WHEN** se pide el mismo turno
- **THEN** las violaciones se devuelven en el mismo orden: C, B (profesional) y D (sillón)

#### Scenario: Varias referencias que fallan a la vez
- **GIVEN** que la prestación del pedido está inactiva, el sillón no existe, el profesional está inactivo y el paciente no existe
- **WHEN** se pide un turno de 30 minutos a las 13:00
- **THEN** el resultado es `Rejected` con exactamente cuatro violaciones, en este orden: `UNKNOWN_REFERENCE` del paciente, `INACTIVE_REFERENCE` del profesional, `UNKNOWN_REFERENCE` del sillón e `INACTIVE_REFERENCE` de la prestación

#### Scenario: Referencia y duración inválidas a la vez
- **GIVEN** que el profesional del pedido no existe
- **WHEN** se pide un turno a las 13:00 con duración explícita de 7 minutos
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `UNKNOWN_REFERENCE` del profesional e `INVALID_DURATION`

#### Scenario: Prestación inactiva con duración por defecto inválida
- **GIVEN** una prestación inactiva con duración por defecto de 485 minutos
- **WHEN** se pide un turno a las 13:00 sin duración explícita
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `INACTIVE_REFERENCE` de la prestación e `INVALID_DURATION`, porque la prestación inactiva igual aporta su duración por defecto

#### Scenario: Violación de validez en un horario ocupado
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30) y el sillón S1 inactivo
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 13:00
- **THEN** el resultado es `Rejected` con una sola violación, `INACTIVE_REFERENCE` del sillón, sin violaciones de solapamiento

#### Scenario: Referencia, duración e inicio inválidos a la vez
- **GIVEN** que el profesional del pedido no existe
- **WHEN** se pide un turno a las 10:03 hora local (13:03 UTC) con duración explícita de 7 minutos
- **THEN** el resultado es `Rejected` con tres violaciones, en este orden: `UNKNOWN_REFERENCE` del profesional, `INVALID_DURATION` e `INVALID_START_TIME`

#### Scenario: Inicio fuera de la grilla en un turno que cruza la medianoche
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:33 hora local del 2026-10-20 (02:33 UTC del 2026-10-21) con duración explícita de 60 minutos, que terminaría a las 00:33 hora local del día siguiente
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `INVALID_START_TIME` y `CROSSES_MIDNIGHT`

#### Scenario: Inicio con segundos en un turno que cruza la medianoche por segundos
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:30:30 hora local del 2026-10-20 (02:30:30 UTC del 2026-10-21) con duración explícita de 30 minutos, que terminaría a las 00:00:30 hora local del día siguiente (03:00:30 UTC)
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `INVALID_START_TIME` y `CROSSES_MIDNIGHT`

#### Scenario: Inicio fuera de la grilla en un horario ocupado
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 10:03 hora local (13:03 UTC)
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_START_TIME`, sin violaciones de solapamiento

#### Scenario: Fuera de horario y solapado a la vez
- **GIVEN** el horario base (P1 atiende el martes `[540, 780)` y `[900, 1140)`)
- **AND** un turno existente B de P1 en S1 de 12:30 a 13:30 hora local del 2026-10-20 (de 15:30 a 16:30 UTC), que ya existía aunque hoy quede fuera de horario
- **WHEN** se pide un turno para P1 en S1 de 12:45 a 13:15 hora local (de 15:45 a 16:15 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente tres violaciones, en este orden: `OUTSIDE_WORKING_HOURS`, `PROFESSIONAL_OVERLAP` con el turno B y `CHAIR_OVERLAP` con el turno B

#### Scenario: Duración inválida en un día sin horario
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo
- **WHEN** se pide un turno para P1 el domingo 2026-10-25 a las 10:00 hora local (13:00 UTC) con duración explícita de 7 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_DURATION`, sin `OUTSIDE_WORKING_HOURS`

#### Scenario: Inicio fuera de la grilla en un día sin horario
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo
- **WHEN** se pide un turno de 30 minutos para P1 el domingo 2026-10-25 a las 10:03 hora local (13:03 UTC)
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_START_TIME`, sin `OUTSIDE_WORKING_HOURS`

#### Scenario: Fuera de horario, bloqueado y solapado a la vez
- **GIVEN** el horario base (P1 atiende el martes `[540, 780)` y `[900, 1140)`)
- **AND** un bloqueo BL3 de P1 del 2026-10-20 de 12:00 a 14:00 hora local (de 15:00 a 17:00 UTC)
- **AND** un turno existente E de P1 en S2 de 12:30 a 13:00 hora local (de 15:30 a 16:00 UTC) y un turno existente F de P2 en S1 de 12:45 a 13:15 hora local (de 15:45 a 16:15 UTC)
- **WHEN** se pide un turno para P1 en S1 de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con exactamente cuatro violaciones, en este orden: `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME` con el bloqueo BL3, `PROFESSIONAL_OVERLAP` con el turno E y `CHAIR_OVERLAP` con el turno F

#### Scenario: Duración inválida dentro de un bloqueo
- **GIVEN** el bloqueo BL1 (P1, de 10:00 a 12:00 hora local, de 13:00 a 15:00 UTC)
- **WHEN** se pide un turno para P1 a las 10:30 hora local (13:30 UTC) con duración explícita de 0 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_DURATION`, sin `BLOCKED_TIME`

#### Scenario: Inicio fuera de la grilla y en el pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno para P1 en S1 a las 09:52 hora local (12:52 UTC), sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente dos violaciones, en este orden: `INVALID_START_TIME` e `IN_THE_PAST`

#### Scenario: Turno en el pasado que cruza la medianoche
- **GIVEN** que `now` es el martes 2026-10-20 a las 23:45 hora local (02:45 UTC del miércoles 2026-10-21)
- **WHEN** se pide un turno para P1 en S1 a las 23:30 hora local del 2026-10-20 (02:30 UTC del 2026-10-21) con duración explícita de 60 minutos, que terminaría a las 00:30 hora local del día siguiente
- **THEN** el resultado es `Rejected` con exactamente dos violaciones, en este orden: `CROSSES_MIDNIGHT` e `IN_THE_PAST`

#### Scenario: Duración inválida en el pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno para P1 en S1 a las 09:00 hora local (12:00 UTC) con duración explícita de 7 minutos
- **THEN** el resultado es `Rejected` con exactamente dos violaciones, en este orden: `INVALID_DURATION` e `IN_THE_PAST`, porque el pasado se evalúa aunque la duración sea inválida

#### Scenario: Prestación inexistente en el pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC) y que la prestación del pedido no existe
- **WHEN** se pide un turno para P1 en S1 a las 09:00 hora local (12:00 UTC) sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente dos violaciones, en este orden: `UNKNOWN_REFERENCE` de la prestación (tipo `SERVICE`) e `IN_THE_PAST`, porque el pasado se evalúa aunque no haya duración efectiva

#### Scenario: Turno en el pasado en un horario ocupado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **AND** un turno existente de P1 en S1, en estado `reservado`, de 09:00 a 09:30 hora local del 2026-10-20 (de 12:00 a 12:30 UTC)
- **WHEN** se pide un turno para P1 en S1 a las 09:00 hora local (12:00 UTC) con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `IN_THE_PAST`, sin `PROFESSIONAL_OVERLAP` ni `CHAIR_OVERLAP`

#### Scenario: Turno en el pasado fuera del horario de atención
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **AND** el horario base (P1 atiende el martes `[540, 780)` y `[900, 1140)`, desde las 09:00)
- **WHEN** se pide un turno para P1 en S1 a las 08:00 hora local (11:00 UTC) con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `IN_THE_PAST`, sin `OUTSIDE_WORKING_HOURS`

### Requirement: Validez de la duración
La duración efectiva SHALL ser > 0, múltiplo de 5 minutos y <= 480 minutos (RN-AG-09, RN-DI-05, SU-02, US-007 CA-1). Si incumple una o más condiciones, el dominio SHALL rechazar el turno con **una sola** violación `INVALID_DURATION`, sin id de turno en conflicto, y MUST NOT evaluar solapamientos. Si la prestación no existe y no hay duración explícita, no hay duración efectiva y la duración MUST NOT validarse.

#### Scenario: Duración explícita de cero minutos
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 0 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración explícita negativa
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de -15 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración por defecto de la prestación no positiva
- **GIVEN** una prestación con duración por defecto de 0 minutos (primer caso) o de -30 minutos (segundo caso)
- **WHEN** se pide un turno a las 13:00 sin duración explícita
- **THEN** en ambos casos el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración que no es múltiplo de 5
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 7 minutos (primer caso) o de 32 minutos (segundo caso)
- **THEN** en ambos casos el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración mayor que el máximo
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 490 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración que rompe dos condiciones
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 487 minutos, que no es múltiplo de 5 y supera el máximo
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`, no dos

#### Scenario: Duración máxima válida
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 08:00 con duración explícita de 480 minutos
- **THEN** el resultado es `Ok` con un turno de 08:00 a 16:00

#### Scenario: Duración mínima válida
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 13:00 con duración explícita de 5 minutos
- **THEN** el resultado es `Ok` con un turno de 13:00 a 13:05

#### Scenario: Duración por defecto de la prestación que no es múltiplo de 5
- **GIVEN** una prestación con duración por defecto de 32 minutos
- **WHEN** se pide un turno a las 13:00 sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_DURATION`

#### Scenario: Duración explícita válida que reemplaza una por defecto inválida
- **GIVEN** una prestación con duración por defecto de 485 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 30 minutos
- **THEN** el resultado es `Ok` con un turno que termina a las 13:30, porque se evalúa solo la duración efectiva

#### Scenario: Prestación inexistente sin duración explícita
- **GIVEN** que la prestación del pedido no existe
- **WHEN** se pide un turno a las 13:00 sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación, `UNKNOWN_REFERENCE` de la prestación, y ninguna `INVALID_DURATION`

#### Scenario: Prestación inexistente con duración explícita inválida
- **GIVEN** que la prestación del pedido no existe
- **WHEN** se pide un turno a las 13:00 con duración explícita de 7 minutos
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `UNKNOWN_REFERENCE` de la prestación e `INVALID_DURATION`

#### Scenario: Duración inválida en un horario ocupado
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno para P1 en S1 a las 13:00 con duración explícita de 0 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_DURATION`, sin violaciones de solapamiento

### Requirement: Contenido de cada violación
Cada violación SHALL devolverse como resultado (nunca excepción) con código estable y mensaje en español. Solo `UNKNOWN_REFERENCE` e `INACTIVE_REFERENCE` llevan `reference_kind` (`PATIENT`, `PROFESSIONAL`, `CHAIR`, `SERVICE`) y el id en el mensaje (sin nombre). `conflicting_interval` (UTC) SHALL existir si y solo si hay `conflicting_appointment_id` (solapamientos, del turno existente) o `conflicting_block_id` (`BLOCKED_TIME`, del bloqueo); el resto no lleva id ni intervalo (US-006 CA-1).

#### Scenario: Mensajes de las violaciones de solapamiento
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30, de 10:00 a 10:30 hora local)
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45 (de 10:15 a 10:45 hora local)
- **THEN** el mensaje de `PROFESSIONAL_OVERLAP` es exactamente "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {id de A})."
- **AND** el mensaje de `CHAIR_OVERLAP` es exactamente "Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {id de A})."
- **AND** ninguno de los dos mensajes contiene las horas en UTC (`13:00`, `13:30`) ni el inicio del turno pedido (`10:15`)

#### Scenario: Mensaje de duración inválida
- **WHEN** se pide un turno con duración explícita de -15 minutos
- **THEN** la violación `INVALID_DURATION` no tiene id de turno en conflicto y su mensaje en español menciona la duración recibida (-15)

#### Scenario: Mensaje de duración que rompe dos condiciones
- **WHEN** se pide un turno con duración explícita de 487 minutos
- **THEN** la única violación `INVALID_DURATION` tiene un mensaje en español que menciona 487, el múltiplo de 5 minutos y el máximo de 480 minutos

#### Scenario: Tipo de referencia en las violaciones de referencias
- **GIVEN** que el sillón S2 del pedido no existe (primer caso) o que el profesional P1 del pedido está inactivo (segundo caso)
- **WHEN** se pide un turno de 30 minutos a las 13:00
- **THEN** la violación es `UNKNOWN_REFERENCE` con tipo `CHAIR` y un mensaje en español que contiene el id de S2 (primer caso), o `INACTIVE_REFERENCE` con tipo `PROFESSIONAL` y un mensaje que contiene el id de P1 (segundo caso)
- **AND** en ambos casos la violación no tiene id de turno en conflicto

#### Scenario: Violaciones sin tipo de referencia
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45 (primer caso) o un turno con duración explícita de 7 minutos (segundo caso)
- **THEN** ninguna de las violaciones devueltas (`PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` en el primer caso, `INVALID_DURATION` en el segundo) tiene tipo de referencia

#### Scenario: Mensaje de inicio fuera de la grilla
- **WHEN** se pide un turno de 30 minutos a las 10:03 hora local (13:03 UTC)
- **THEN** la violación `INVALID_START_TIME` tiene un mensaje en español que contiene `10:03, hora local` y la razón "debe caer en un minuto múltiplo de 5"
- **AND** la violación no tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Mensaje de cruce de medianoche
- **WHEN** se pide un turno a las 23:30 hora local del 2026-10-20 (02:30 UTC del 2026-10-21) con duración explícita de 60 minutos
- **THEN** la violación `CROSSES_MIDNIGHT` tiene un mensaje en español que contiene el inicio `23:30` y el fin `00:30` en hora local, y no el horario en UTC (`02:30`)
- **AND** la violación no tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Mensajes de solapamiento con el nombre vacío o en blanco
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30, de 10:00 a 10:30 hora local)
- **AND** P1 y S1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45 (de 10:15 a 10:45 hora local)
- **THEN** en ambos casos el mensaje de `PROFESSIONAL_OVERLAP` es exactamente "El profesional ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {id de A})."
- **AND** el mensaje de `CHAIR_OVERLAP` es exactamente "El sillón está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {id de A})."

#### Scenario: Mensajes completos de un rechazo con todos los conflictos de agenda
- **GIVEN** que P1 atiende el martes en `[540, 780)` y `[900, 1140)` (de 09:00 a 13:00 y de 15:00 a 19:00 hora local)
- **AND** un bloqueo BL3 de P1, sin motivo, del 2026-10-20 de 12:00 a 14:00 hora local (de 15:00 a 17:00 UTC)
- **AND** un turno existente E de P1 en S2 de 12:30 a 13:00 hora local (de 15:30 a 16:00 UTC) y un turno existente F de P2 en S1 de 12:45 a 13:15 hora local (de 15:45 a 16:15 UTC)
- **WHEN** se pide un turno para P1 en S1 de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con exactamente cuatro violaciones, en este orden y con estos mensajes exactos: `OUTSIDE_WORKING_HOURS`, "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00."; `BLOCKED_TIME`, "El turno de 12:30 a 13:30 (hora local) se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 20/10/2026 12:00 al 20/10/2026 14:00 (hora local) (bloqueo {id de BL3})."; `PROFESSIONAL_OVERLAP`, "Dra. Laura Quiroga ya tiene un turno de 12:30 a 13:00 (hora local) que se superpone (turno {id de E})."; y `CHAIR_OVERLAP`, "Sillón 1 está ocupado de 12:45 a 13:15 (hora local) por un turno que se superpone (turno {id de F})."

#### Scenario: Intervalo si y solo si hay un turno o un bloqueo en conflicto
- **GIVEN** el horario, el bloqueo BL3 y los turnos existentes E y F del escenario anterior
- **WHEN** se pide el mismo turno, de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC)
- **THEN** `OUTSIDE_WORKING_HOURS` no lleva intervalo ni id de turno o de bloqueo en conflicto
- **AND** `BLOCKED_TIME` lleva el id de BL3 y su intervalo, de `2026-10-20T15:00:00+00:00` a `2026-10-20T17:00:00+00:00`, sin id de turno
- **AND** `PROFESSIONAL_OVERLAP` lleva el id del turno E y su intervalo, de `2026-10-20T15:30:00+00:00` a `2026-10-20T16:00:00+00:00`, sin id de bloqueo
- **AND** `CHAIR_OVERLAP` lleva el id del turno F y su intervalo, de `2026-10-20T15:45:00+00:00` a `2026-10-20T16:15:00+00:00`, sin id de bloqueo
- **AND** cada una de las cuatro violaciones lleva intervalo si y solo si lleva id de turno o de bloqueo en conflicto

#### Scenario: Violaciones sin intervalo en conflicto
- **GIVEN** que P1 atiende el martes en `[540, 780)` y `[900, 1140)` en un primer caso, y todos los días de 00:00 a 24:00 en el resto
- **WHEN** se pide, para P1 en S1, un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC) con duración explícita de 60 minutos (primer caso); un turno a las 13:00 con duración explícita de 7 minutos (segundo caso); un turno de 30 minutos a las 10:03 hora local (13:03 UTC) (tercer caso); un turno a las 23:30 hora local (02:30 UTC del 2026-10-21) con duración explícita de 60 minutos (cuarto caso); con `now` el 2026-10-20 a las 10:00 hora local (13:00 UTC), un turno a las 09:55 hora local (12:55 UTC) (quinto caso); con el sillón S2 inexistente, un turno de 30 minutos en S2 a las 13:00 (sexto caso); y con P1 inactivo, un turno de 30 minutos a las 13:00 (séptimo caso)
- **THEN** la única violación de cada caso (`OUTSIDE_WORKING_HOURS`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `UNKNOWN_REFERENCE` e `INACTIVE_REFERENCE`, respectivamente) no lleva intervalo en conflicto ni id de turno o de bloqueo en conflicto

#### Scenario: Mensaje de una referencia inactiva con nombre
- **GIVEN** que P1, llamado "Dra. Laura Quiroga", está inactivo (primer caso) o que S1, llamado "Sillón 1", está inactivo (segundo caso)
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 13:00 (10:00 hora local)
- **THEN** la única violación es `INACTIVE_REFERENCE` con el mensaje exacto de siempre, "El profesional indicado está inactivo (id {id de P1})." en el primer caso y "El sillón indicado está inactivo (id {id de S1})." en el segundo
- **AND** ninguno de los dos mensajes contiene el nombre de la entidad

### Requirement: Turno dentro de un solo día local
El inicio y el fin del turno MUST caer en el mismo día local; si cruza la medianoche local, el dominio SHALL rechazarlo con `CROSSES_MIDNIGHT` (RN-AG-10, SU-09, US-007 CA-3). Por el intervalo semiabierto (DD-07), terminar exactamente a las `00:00:00.000000` del día siguiente es válido, pero cualquier segundo o fracción posterior cruza la medianoche. Solo se evalúa si hay duración efectiva válida, aunque el inicio esté fuera de la grilla.

#### Scenario: Turno que cruza la medianoche local
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:30 hora local del 2026-10-20 (02:30 UTC del 2026-10-21) con duración explícita de 60 minutos, que terminaría a las 00:30 hora local del 2026-10-21
- **THEN** el resultado es `Rejected` con exactamente una violación `CROSSES_MIDNIGHT`

#### Scenario: Turno que termina antes de la medianoche local
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:00 hora local del 2026-10-20 (02:00 UTC del 2026-10-21) con duración explícita de 55 minutos
- **THEN** el resultado es `Ok` con un turno de 23:00 a 23:55 hora local (de 02:00 a 02:55 UTC del 2026-10-21)

#### Scenario: Turno que termina justo a la medianoche local
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:30 hora local del 2026-10-20 (02:30 UTC del 2026-10-21) sin duración explícita
- **THEN** el resultado es `Ok` con un turno de 23:30 a 00:00 hora local (de 02:30 a 03:00 UTC del 2026-10-21), porque el fin no ocupa el día siguiente

#### Scenario: Duración inválida en un turno que cruzaría la medianoche
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno a las 23:30 hora local del 2026-10-20 (02:30 UTC del 2026-10-21) con duración explícita de 62 minutos, que no es múltiplo de 5 y terminaría a las 00:32 del día siguiente
- **THEN** el resultado es `Rejected` con exactamente una violación, `INVALID_DURATION`, y ninguna `CROSSES_MIDNIGHT`

### Requirement: Turno dentro del horario de atención
El turno nuevo MUST caer completo dentro del horario del profesional para su día de semana local, o rechazarse con una violación `OUTSIDE_WORKING_HOURS` sin id en conflicto ni `reference_kind` (RN-AG-04, RN-GL-03, US-004). El dominio filtra por sí mismo los tramos del profesional y día local (los turnos existentes no se reevalúan). Por defecto en los escenarios: P1 en S1 el martes 2026-10-20, con `[540, 780)` y `[900, 1140)` el martes y sin tramos el domingo.

#### Scenario: Turno completo dentro de un tramo
- **GIVEN** el horario base
- **WHEN** se pide un turno de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok` con el turno de 13:00 a 13:30 UTC

#### Scenario: Turno que empieza justo al inicio del tramo
- **GIVEN** el horario base
- **WHEN** se pide un turno de 09:00 a 09:30 hora local (de 12:00 a 12:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que termina justo al fin del tramo de la mañana
- **GIVEN** el horario base
- **WHEN** se pide un turno de 12:30 a 13:00 hora local (de 15:30 a 16:00 UTC), con duración explícita de 30 minutos, que termina en el minuto 780, el fin del tramo
- **THEN** el resultado es `Ok`

#### Scenario: Turno que termina justo al fin del tramo de la tarde
- **GIVEN** el horario base
- **WHEN** se pide un turno de 18:30 a 19:00 hora local (de 21:30 a 22:00 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que empieza dentro y termina después del fin del tramo
- **GIVEN** el horario base
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Turno que empieza antes del inicio del tramo
- **GIVEN** el horario base
- **WHEN** se pide un turno de 08:30 a 09:30 hora local (de 11:30 a 12:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Turno que ocupa justo el hueco entre dos tramos
- **GIVEN** el horario base
- **WHEN** se pide un turno de 13:00 a 15:00 hora local (de 16:00 a 18:00 UTC), con duración explícita de 120 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Turno dentro del hueco entre dos tramos
- **GIVEN** el horario base
- **WHEN** se pide un turno de 14:00 a 14:30 hora local (de 17:00 a 17:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Turno que empieza en un tramo y termina en el siguiente, con hueco
- **GIVEN** el horario base
- **WHEN** se pide un turno de 12:30 a 15:30 hora local (de 15:30 a 18:30 UTC), con duración explícita de 180 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Turno en un día sin tramos
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo
- **WHEN** se pide un turno el domingo 2026-10-25 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC del 2026-10-25), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`

#### Scenario: Instante UTC dentro del tramo que en hora local queda fuera
- **GIVEN** el horario base
- **WHEN** se pide un turno de 06:00 a 06:30 hora local (de 09:00 a 09:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`, aunque en UTC el turno parecería caer dentro del tramo de 09:00 a 13:00

#### Scenario: Instante UTC fuera del tramo que en hora local queda dentro
- **GIVEN** el horario base
- **WHEN** se pide un turno de 18:00 a 18:30 hora local (de 21:00 a 21:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`, aunque en UTC el turno parecería caer fuera de los dos tramos

#### Scenario: El día de la semana es el local, no el de UTC
- **GIVEN** que P1 solo tiene el tramo `[1200, 1380)` (de 20:00 a 23:00) el miércoles (día ISO 3)
- **WHEN** se pide un turno el martes 2026-10-20 de 22:00 a 22:30 hora local (del miércoles 2026-10-21 de 01:00 a 01:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`, porque en hora local el turno es del martes

#### Scenario: Turno del martes local que en UTC cae el miércoles
- **GIVEN** que P1 solo tiene el tramo `[1200, 1380)` (de 20:00 a 23:00) el martes (día ISO 2)
- **WHEN** se pide un turno el martes 2026-10-20 de 22:00 a 22:30 hora local (del miércoles 2026-10-21 de 01:00 a 01:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que termina a la medianoche local, al fin del tramo
- **GIVEN** que P1 solo tiene el tramo `[1200, 1440)` (de 20:00 a 24:00) el martes
- **WHEN** se pide un turno el martes 2026-10-20 de 23:30 a 00:00 hora local (de 02:30 a 03:00 UTC del 2026-10-21), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`, porque el fin del turno es el minuto 1440, igual al fin del tramo

#### Scenario: Turno que termina a la medianoche local, después del fin del tramo
- **GIVEN** que P1 solo tiene el tramo `[1200, 1380)` (de 20:00 a 23:00) el martes
- **WHEN** se pide un turno el martes 2026-10-20 de 23:30 a 00:00 hora local (de 02:30 a 03:00 UTC del 2026-10-21), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`, porque el fin del turno es el minuto 1440 (no el minuto 0 del día siguiente) y queda después del fin del tramo, el minuto 1380

#### Scenario: Tramo de otro profesional
- **GIVEN** que P2 atiende el martes en `[540, 780)` y P1 no tiene tramos el martes
- **WHEN** se pide un turno para P1 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`, porque el tramo de P2 no cuenta para P1

#### Scenario: Turno que pasa de un tramo a otro contiguo
- **GIVEN** que P1 atiende el martes en `[540, 780)` (de 09:00 a 13:00) y `[780, 1020)` (de 13:00 a 17:00)
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Ok`, porque los dos tramos contiguos cuentan como uno solo, de 09:00 a 17:00

#### Scenario: Tramo contenido en otro
- **GIVEN** que P1 atiende el martes en `[540, 780)` (de 09:00 a 13:00) y `[600, 700)` (de 10:00 a 11:40), contenido en el primero, recibidos en ese orden
- **WHEN** se pide un turno de 12:00 a 12:30 hora local (de 15:00 a 15:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok` con el turno de 15:00 a 15:30 UTC, porque los dos tramos se unen en `[540, 780)` (de 09:00 a 13:00): el tramo contenido no acorta al que lo contiene

#### Scenario: Mensaje de un turno fuera de los tramos del día
- **GIVEN** el horario base
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00."
- **AND** la violación no tiene id de turno en conflicto, intervalo en conflicto ni tipo de referencia

#### Scenario: Mensaje de un turno en un día sin tramos
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo
- **WHEN** se pide un turno el domingo 2026-10-25 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga no atiende los domingos."

#### Scenario: Mensaje con tramos contiguos y un tramo hasta la medianoche
- **GIVEN** que P1 atiende el martes en `[1200, 1440)` (de 20:00 a 24:00), `[780, 1020)` (de 13:00 a 17:00) y `[540, 780)` (de 09:00 a 13:00), recibidos en ese orden
- **WHEN** se pide un turno de 17:30 a 18:00 hora local (de 20:30 a 21:00 UTC), con duración explícita de 30 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 17:30 a 18:00 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 17:00 y de 20:00 a 24:00."

#### Scenario: Mensaje fuera de horario con el nombre vacío o en blanco
- **GIVEN** el horario base y P1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** en ambos casos la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención: el profesional atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00."

#### Scenario: Mensaje de un día sin tramos con el nombre vacío o en blanco
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo, y P1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno el domingo 2026-10-25 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** en ambos casos la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención: el profesional no atiende los domingos."

### Requirement: Validez de un conjunto de tramos
Al validar tramos de horario (RN-DI-01, RN-DI-02, US-010), el dominio SHALL devolver la lista de violaciones (vacía si es válido, nunca excepción). Un tramo con día fuera de `1..7`, límites fuera de `0..1440` o `inicio >= fin` da una sola `INVALID_WORKING_HOURS` y se excluye de solapamientos. Cada par de tramos válidos del mismo profesional y día que se pisen (semiabiertos) da `OVERLAPPING_WORKING_HOURS`; contiguos, de otro día o profesional no chocan (escenarios: de P1 en el orden dado).

#### Scenario: Varios tramos válidos el mismo día
- **GIVEN** los tramos del martes `[540, 780)` (de 09:00 a 13:00) y `[900, 1140)` (de 15:00 a 19:00)
- **WHEN** se valida el conjunto
- **THEN** no hay violaciones

#### Scenario: Tramos con inicio igual o posterior al fin
- **GIVEN** los tramos del martes `[780, 780)` y `[800, 700)`
- **WHEN** se valida el conjunto
- **THEN** hay exactamente dos violaciones `INVALID_WORKING_HOURS`, la primera con un mensaje que menciona el tramo 1 y la segunda, el tramo 2
- **AND** ninguna de las dos tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Tramos solapados el mismo día
- **GIVEN** los tramos del martes `[540, 780)` (de 09:00 a 13:00) y `[720, 900)` (de 12:00 a 15:00), que comparten de 12:00 a 13:00
- **WHEN** se valida el conjunto
- **THEN** hay exactamente una violación `OVERLAPPING_WORKING_HOURS`, con un mensaje que menciona los tramos 1 y 2 y el martes

#### Scenario: Los mismos tramos en días distintos
- **GIVEN** el tramo `[540, 780)` el martes y el tramo `[720, 900)` el miércoles
- **WHEN** se valida el conjunto
- **THEN** no hay violaciones

#### Scenario: Tramos contiguos
- **GIVEN** los tramos del martes `[540, 780)` (de 09:00 a 13:00) y `[780, 1020)` (de 13:00 a 17:00)
- **WHEN** se valida el conjunto
- **THEN** no hay violaciones

#### Scenario: Límites del día y valores fuera de rango
- **GIVEN** el tramo del martes `[1200, 1440)` (de 20:00 a 24:00), solo, en un primer caso
- **AND** en otros casos, un solo tramo con un valor fuera de rango: `[-5, 60)` el martes, `[0, 1445)` el martes, `[540, 780)` con día 0 y `[540, 780)` con día 8
- **WHEN** se valida cada conjunto por separado
- **THEN** el tramo `[1200, 1440)` no tiene violaciones
- **AND** cada uno de los otros cuatro casos tiene exactamente una violación `INVALID_WORKING_HOURS`

#### Scenario: Tramos solapados de profesionales distintos
- **GIVEN** el tramo `[540, 780)` de P1 el martes y el tramo `[720, 900)` de P2 el martes
- **WHEN** se valida el conjunto
- **THEN** no hay violaciones, porque cada profesional tiene su propio horario

#### Scenario: Orden de las violaciones de un conjunto
- **GIVEN** los tramos del martes `[540, 780)`, `[750, 750)`, `[720, 900)` y `[600, 660)`, en ese orden
- **WHEN** se valida el conjunto
- **THEN** hay exactamente tres violaciones, en este orden: `INVALID_WORKING_HOURS` del tramo 2, `OVERLAPPING_WORKING_HOURS` de los tramos 1 y 3 y `OVERLAPPING_WORKING_HOURS` de los tramos 1 y 4
- **AND** no hay violación de los tramos 3 y 4, que no se solapan, ni del tramo 2 con los tramos 1 o 3, aunque su minuto 750 cae dentro de los dos, porque es inválido

### Requirement: Turno fuera de los bloqueos del profesional
El turno MUST NOT superponerse con ningún bloqueo del profesional del pedido (RN-AG-05, US-004 CA-4 y CA-5). Por cada bloqueo con el que se solape (ambos semiabiertos, DD-07, comparados como instantes aunque duren varios días), el dominio SHALL devolver `BLOCKED_TIME` con el id del bloqueo y su intervalo completo en UTC (US-006 CA-1), sin id de turno ni `reference_kind`. El dominio filtra por sí mismo los bloqueos del profesional.

#### Scenario: Turno dentro de un bloqueo
- **GIVEN** el bloqueo BL1
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `BLOCKED_TIME` que lleva el id de BL1

#### Scenario: Turno que termina justo cuando empieza el bloqueo
- **GIVEN** el bloqueo BL1
- **WHEN** se pide un turno de 09:30 a 10:00 hora local (de 12:30 a 13:00 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que empieza justo cuando termina el bloqueo
- **GIVEN** el bloqueo BL1
- **WHEN** se pide un turno de 12:00 a 12:30 hora local (de 15:00 a 15:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que pisa el inicio del bloqueo
- **GIVEN** el bloqueo BL1
- **WHEN** se pide un turno de 09:45 a 10:15 hora local (de 12:45 a 13:15 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `BLOCKED_TIME` que lleva el id de BL1

#### Scenario: Turno que pisa el fin del bloqueo
- **GIVEN** el bloqueo BL1
- **WHEN** se pide un turno de 11:45 a 12:15 hora local (de 14:45 a 15:15 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `BLOCKED_TIME` que lleva el id de BL1

#### Scenario: Bloqueo de otro profesional
- **GIVEN** un bloqueo de P2 del 2026-10-20 de 10:00 a 12:00 hora local (de 13:00 a 15:00 UTC) y ningún bloqueo de P1
- **WHEN** se pide un turno para P1 de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno dentro de un bloqueo de varios días
- **GIVEN** un bloqueo BLV de P1, con motivo "vacaciones", del lunes 2026-10-19 a las 00:00 hora local (03:00 UTC del 2026-10-19) al lunes 2026-10-26 a las 00:00 hora local (03:00 UTC del 2026-10-26)
- **WHEN** se pide un turno el martes 2026-10-20 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `BLOCKED_TIME` que lleva el id de BLV

#### Scenario: Último turno del domingo local dentro de un bloqueo de varios días
- **GIVEN** el bloqueo BLV
- **WHEN** se pide un turno el domingo 2026-10-25 de 23:30 a 23:55 hora local (de 02:30 a 02:55 UTC del lunes 2026-10-26), con duración explícita de 25 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `BLOCKED_TIME` que lleva el id de BLV, porque en UTC ya es el 26 pero todavía antes de las 03:00, el fin del bloqueo

#### Scenario: Turno que empieza justo cuando termina un bloqueo de varios días
- **GIVEN** el bloqueo BLV
- **WHEN** se pide un turno el lunes 2026-10-26 de 00:00 a 00:30 hora local (de 03:00 a 03:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que termina justo cuando empieza un bloqueo de varios días
- **GIVEN** el bloqueo BLV
- **WHEN** se pide un turno el domingo 2026-10-18 de 23:30 a 00:00 hora local (de 02:30 a 03:00 UTC del lunes 2026-10-19), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`

#### Scenario: Turno que pisa dos bloqueos
- **GIVEN** el bloqueo BL1 y un bloqueo BL2 de P1 del 2026-10-20 de 11:00 a 13:00 hora local (de 14:00 a 16:00 UTC)
- **WHEN** se pide un turno de 11:30 a 12:30 hora local (de 14:30 a 15:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con exactamente dos violaciones, en este orden: `BLOCKED_TIME` con el id de BL1 y `BLOCKED_TIME` con el id de BL2

#### Scenario: Orden de los bloqueos independiente del orden recibido
- **GIVEN** los bloqueos BL1 y BL2 del escenario anterior, recibidos en orden inverso (BL2 primero)
- **WHEN** se pide el mismo turno
- **THEN** las violaciones se devuelven en el mismo orden: BL1 y después BL2

#### Scenario: Bloqueo inválido recibido con la agenda
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 12:00 a 10:00 hora local (de 15:00 a 13:00 UTC), con inicio posterior al fin, que llega por error junto con la agenda
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Ok`, sin excepción: un bloqueo con inicio igual o posterior al fin no se superpone con ningún turno

#### Scenario: Bloqueo inválido que abarca el turno pedido
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 12:00 a 10:00 hora local (de 15:00 a 13:00 UTC), con inicio posterior al fin
- **WHEN** se pide un turno de 09:00 a 13:00 hora local (de 12:00 a 16:00 UTC), con duración explícita de 240 minutos
- **THEN** el resultado es `Ok`, sin excepción y sin `BLOCKED_TIME`

#### Scenario: Intervalo del bloqueo con el que choca
- **GIVEN** el bloqueo BL1 (de 10:00 a 12:00 hora local, de 13:00 a 15:00 UTC)
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** la violación `BLOCKED_TIME` lleva el id de BL1 y su intervalo, de `2026-10-20T13:00:00+00:00` a `2026-10-20T15:00:00+00:00`

#### Scenario: Intervalo de un bloqueo de varios días
- **GIVEN** el bloqueo BLV, del lunes 2026-10-19 a las 00:00 hora local (03:00 UTC del 2026-10-19) al lunes 2026-10-26 a las 00:00 hora local (03:00 UTC del 2026-10-26)
- **WHEN** se pide un turno el martes 2026-10-20 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** la violación `BLOCKED_TIME` lleva el id de BLV y su intervalo completo, de `2026-10-19T03:00:00+00:00` a `2026-10-26T03:00:00+00:00`, sin recortarlo al día ni al horario del turno

#### Scenario: Cada bloqueo con su intervalo
- **GIVEN** el bloqueo BL1 y un bloqueo BL2 de P1 del 2026-10-20 de 11:00 a 13:00 hora local (de 14:00 a 16:00 UTC)
- **WHEN** se pide un turno de 11:30 a 12:30 hora local (de 14:30 a 15:30 UTC), con duración explícita de 60 minutos
- **THEN** la violación `BLOCKED_TIME` de BL1 lleva el intervalo de `2026-10-20T13:00:00+00:00` a `2026-10-20T15:00:00+00:00` y la de BL2, de `2026-10-20T14:00:00+00:00` a `2026-10-20T16:00:00+00:00`

### Requirement: Mensaje de un turno bloqueado
El mensaje de `BLOCKED_TIME` MUST ser `"El turno de {inicio} a {fin} (hora local) se superpone con un bloqueo de agenda: {nombre} tiene la agenda bloqueada del {inicio_bloqueo} al {fin_bloqueo} (hora local) (bloqueo {id})."`, con horas locales y el bloqueo en `dd/mm/aaaa HH:MM`, seguido de `" Motivo: {motivo}."` si el motivo no es vacío/blanco (tal como se cargó). `{nombre}` va recortado sin artículo, o `"el profesional"` si es vacío/blanco (US-006 CA-3).

#### Scenario: Mensaje de un bloqueo sin motivo
- **GIVEN** el bloqueo BL1, sin motivo
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** el mensaje de la violación `BLOCKED_TIME` es exactamente "El turno de 10:30 a 11:00 (hora local) se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {id de BL1})."
- **AND** la violación no tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Mensaje de un bloqueo de varios días con motivo
- **GIVEN** el bloqueo BLV, con motivo "vacaciones"
- **WHEN** se pide un turno el domingo 2026-10-25 de 23:30 a 23:55 hora local (de 02:30 a 02:55 UTC del 2026-10-26), con duración explícita de 25 minutos
- **THEN** el mensaje de la violación `BLOCKED_TIME` es exactamente "El turno de 23:30 a 23:55 (hora local) se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 19/10/2026 00:00 al 26/10/2026 00:00 (hora local) (bloqueo {id de BLV}). Motivo: vacaciones."
- **AND** el mensaje no contiene las horas en UTC (`02:30`, `03:00`)

#### Scenario: Mensaje de un bloqueo con motivo vacío o en blanco
- **GIVEN** el bloqueo BL1 con motivo `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** en ambos casos el mensaje de la violación `BLOCKED_TIME` es exactamente el mismo que el de un bloqueo sin motivo, terminado en "(bloqueo {id de BL1}).", sin "Motivo:"

#### Scenario: Mensaje de un bloqueo con el nombre vacío o en blanco
- **GIVEN** el bloqueo BL1, sin motivo, y P1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** en ambos casos el mensaje de la violación `BLOCKED_TIME` es exactamente "El turno de 10:30 a 11:00 (hora local) se superpone con un bloqueo de agenda: el profesional tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {id de BL1})."

### Requirement: Turnos afectados por un bloqueo
Dado un bloqueo y turnos existentes, el dominio SHALL devolver sin cambios los del mismo profesional en estado ocupante (`reservado`, `confirmado`, `atendido`) que se solapen con él (semiabiertos), ordenados por inicio, sin cancelarlos ni moverlos (RN-DI-04, SU-05, US-011 CA-3). Escenarios (2026-10-20 local): P1 con T1 09:30–10:00, T3 11:45–12:15, T7 12:00–12:30 `reservado`, T2 10:30–11:00 `confirmado`, T4 11:00–11:30 `cancelado`, T5 10:00–10:30 `ausente`; P2 con T6 10:30–11:00 `reservado`.

#### Scenario: Bloqueo que pisa turnos existentes
- **GIVEN** el bloqueo BL1 y los turnos T1 a T7, recibidos en orden inverso (T7 primero)
- **WHEN** se piden los turnos afectados por BL1
- **THEN** el resultado es exactamente T2 y T3, en ese orden
- **AND** no incluye T1 ni T7 (tocan el bloqueo en un borde), T4 (cancelado), T5 (ausente) ni T6 (otro profesional)

#### Scenario: El bloqueo no cambia los turnos que pisa
- **GIVEN** el bloqueo BL1 y los turnos T1 a T7
- **WHEN** se piden los turnos afectados por BL1
- **THEN** T2 sigue en estado `confirmado` y T3 en `reservado`, con el mismo inicio, fin, profesional y sillón que tenían

#### Scenario: Bloqueo que no pisa ningún turno
- **GIVEN** el bloqueo BL1 y solo los turnos T1, T6 y T7
- **WHEN** se piden los turnos afectados por BL1
- **THEN** el resultado está vacío

#### Scenario: Turnos afectados por un bloqueo inválido
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 12:00 a 10:00 hora local (de 15:00 a 13:00 UTC), con inicio posterior al fin, y los turnos T1 a T7
- **WHEN** se piden los turnos afectados por ese bloqueo
- **THEN** el resultado está vacío, sin excepción

#### Scenario: Turno que abarca un bloqueo inválido
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 12:00 a 10:00 hora local (de 15:00 a 13:00 UTC), con inicio posterior al fin, y un turno reservado de P1 de 09:00 a 13:00 hora local (de 12:00 a 16:00 UTC)
- **WHEN** se piden los turnos afectados por ese bloqueo
- **THEN** el resultado está vacío, sin excepción

### Requirement: Mensaje de un turno en el pasado
El mensaje de `IN_THE_PAST` MUST ser `"El inicio del turno ({inicio}, hora local) es anterior al momento actual ({now}, hora local): no se pueden {operación} en el pasado."`, en fecha/hora local (`{inicio}` `dd/mm/aaaa HH:MM`, `{now}` `dd/mm/aaaa HH:MM:SS` sin microsegundos, sin profesional ni sillón). `validate_new_appointment` SHALL recibir `operación` con default `"dar turnos"` y pasarla a `check_not_in_the_past` (alta: `"dar turnos"`; reprogramar: `"reprogramar turnos"`).

#### Scenario: Mensaje de un turno en el pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado."
- **AND** la violación no tiene id de turno ni de bloqueo en conflicto ni tipo de referencia

#### Scenario: Mensaje con el momento actual en el mismo minuto que el inicio
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se pide un turno a las 10:00 hora local (13:00 UTC), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento actual (20/10/2026 10:00:30, hora local): no se pueden dar turnos en el pasado."

#### Scenario: Mensaje con la fecha local y no la de UTC
- **GIVEN** que `now` es el martes 2026-10-20 a las 23:30 hora local (02:30 UTC del miércoles 2026-10-21)
- **WHEN** se pide un turno el martes 2026-10-20 a las 23:00 hora local (02:00 UTC del 2026-10-21), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 23:00, hora local) es anterior al momento actual (20/10/2026 23:30:00, hora local): no se pueden dar turnos en el pasado."
- **AND** el mensaje no contiene la fecha ni las horas en UTC (`21/10/2026`, `02:00`, `02:30`)

#### Scenario: Mensaje al reprogramar un turno al pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se reprograma un turno a las 09:00 hora local (12:00 UTC)
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:00, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden reprogramar turnos en el pasado."

#### Scenario: Mensaje al reprogramar con el momento actual en el mismo minuto que el inicio
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se reprograma un turno a las 10:00 hora local (13:00 UTC)
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento actual (20/10/2026 10:00:30, hora local): no se pueden reprogramar turnos en el pasado."

### Requirement: Nombre del profesional y del sillón
El profesional SHALL tener nombre completo y el sillón un nombre (KB 04), obligatorios y sin valor por defecto al construir la entidad. El dominio MUST conservarlos tal como se cargaron sin validarlos ni lanzar excepción aunque sean vacíos o solo espacios (su validez corresponde al alta del catálogo). Solo se usan en los mensajes de conflicto de agenda, donde MUST mostrarse recortados (`strip`) para evitar espacios dobles.

#### Scenario: Profesional y sillón con nombre
- **WHEN** se construyen P1 con el nombre "Dra. Laura Quiroga" y S1 con el nombre "Sillón 1", los dos activos
- **THEN** P1 conserva el nombre "Dra. Laura Quiroga" y S1 el nombre "Sillón 1", con su id y su estado activo

#### Scenario: Nombre vacío o en blanco al construir
- **WHEN** se construyen P1 y S1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **THEN** en ambos casos la construcción no falla y cada entidad conserva el nombre tal como se cargó, sin recortarlo

#### Scenario: Nombre con espacios alrededor en el mensaje
- **GIVEN** P1 con el nombre `"  Dra. Laura Quiroga  "`, con espacios al principio y al final, y el turno existente A (P1, S1, de 13:00 a 13:30, de 10:00 a 10:30 hora local)
- **WHEN** se pide un turno para P1 en S2 de 13:15 a 13:45 (de 10:15 a 10:45 hora local)
- **THEN** el resultado es `Rejected` con una sola violación, `PROFESSIONAL_OVERLAP`, cuyo mensaje es exactamente "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {id de A})."
- **AND** el mensaje no contiene espacios dobles
- **AND** P1 conserva el nombre tal como se cargó, con sus espacios

## ADDED Requirements

### Requirement: Orden de los conflictos de agenda
Si el pedido es válido, el dominio SHALL evaluar los conflictos de agenda y devolverlos todos juntos en este orden: `OUTSIDE_WORKING_HOURS` (como mucho una), todas las `BLOCKED_TIME`, todas las `PROFESSIONAL_OVERLAP` y todas las `CHAIR_OVERLAP` (RN-AG-12, DD-08). Se emite una violación por cada bloqueo o turno en conflicto, ordenadas dentro de cada tipo por el inicio del bloqueo o turno; un mismo turno puede producir ambos solapamientos.

#### Scenario: Orden entre horario, bloqueos y solapamientos de profesional y sillón
- **GIVEN** que P1 atiende el martes en `[540, 780)` y `[900, 1140)`
- **AND** un bloqueo BL3 de P1 del 2026-10-20 de 12:00 a 14:00 hora local (de 15:00 a 17:00 UTC)
- **AND** un turno existente E de P1 en S2 de 12:30 a 13:00 hora local (de 15:30 a 16:00 UTC) y un turno existente F de P2 en S1 de 12:45 a 13:15 hora local (de 15:45 a 16:15 UTC)
- **WHEN** se pide un turno para P1 en S1 de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Rejected` con `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME` (BL3), `PROFESSIONAL_OVERLAP` (E) y `CHAIR_OVERLAP` (F) en ese orden exacto

### Requirement: Mensajes de validez de duración, inicio y medianoche
Las violaciones de validez no llevan nombres ni id en conflicto. `INVALID_DURATION` MUST indicar la duración recibida y cada condición fallida. `INVALID_START_TIME` MUST decir `se recibió {hora}, hora local` y unir con `" y "` cada razón (`"debe caer en un minuto múltiplo de 5"`, `"no puede tener segundos ni fracciones de segundo"`). `CROSSES_MIDNIGHT` MUST indicar inicio y fin locales. Las horas usan `HH:MM`, o `HH:MM:SS` con segundos/fracciones != 0, salvo `now` en `IN_THE_PAST`.

#### Scenario: Formato de horas y razones en violaciones de validez
- **WHEN** se pide un turno con duración explícita de 487 minutos (primer caso), a las 10:03:30 hora local (segundo caso) o de 23:30 a 00:30 hora local (tercer caso)
- **THEN** `INVALID_DURATION` menciona 487 y ambas condiciones; `INVALID_START_TIME` muestra `10:03:30, hora local` y une las dos razones con `" y "`; y `CROSSES_MIDNIGHT` muestra `23:30` y `00:30` en hora local

### Requirement: Plantillas y nombres en mensajes de solapamiento
En `PROFESSIONAL_OVERLAP` el mensaje SHALL ser `"{nombre} ya tiene un turno de {inicio} a {fin} (hora local) que se superpone (turno {id})."` y en `CHAIR_OVERLAP`, `"{sillón} está ocupado de {inicio} a {fin} (hora local) por un turno que se superpone (turno {id})."`, con `{inicio}` y `{fin}` locales del turno existente (US-006 CA-3). En conflictos de agenda el nombre va con `strip` y sin artículo; si queda vacío, MUST usarse `"El profesional"`, `"El sillón"` o, tras `:`, `"el profesional"`.

#### Scenario: Plantillas de solapamiento con nombres reales y genéricos
- **GIVEN** el turno existente A (P1, S1, de 10:00 a 10:30 hora local) con nombres `"Dra. Laura Quiroga"` y `"Sillón 1"` en un primer caso, y nombres en blanco `"   "` en un segundo caso
- **WHEN** se pide un turno para P1 en S1 de 10:15 a 10:45 hora local
- **THEN** en el primer caso los mensajes usan `"Dra. Laura Quiroga"` y `"Sillón 1"`, y en el segundo usan `"El profesional"` y `"El sillón"` como sujeto

### Requirement: Unión de tramos contiguos o superpuestos del día
Al evaluar el horario del día local, cada tramo `[inicio, fin)` es semiabierto (DD-07) y un turno que termina a las `00:00` locales tiene fin en el minuto `1440` de su día de inicio. Los tramos del mismo profesional y día contiguos o superpuestos SHALL unirse desde el menor inicio hasta el mayor fin (un tramo contenido no acorta al que lo contiene); si queda un hueco entre tramos, un turno que lo pise se rechaza; sin tramos ese día, no atiende.

#### Scenario: Unión de tramos contiguos y superpuestos con fin en medianoche
- **GIVEN** que P1 atiende el martes en `[540, 780)`, `[600, 700)` y `[780, 1440)`
- **WHEN** se pide un turno para P1 el martes de 12:30 a 13:30 hora local (primer caso) o de 23:30 a 00:00 hora local (segundo caso)
- **THEN** ambos resultados son `Ok` porque los tramos se unen en `[540, 1440)` y el fin a las `00:00` locales corresponde al minuto `1440`

### Requirement: Mensaje de un turno fuera del horario de atención
El mensaje de `OUTSIDE_WORKING_HOURS` MUST ser `"El turno de {inicio} a {fin} (hora local) queda fuera del horario de atención: {nombre} atiende el {día} de {inicio_tramo} a {fin_tramo}."` (tramos del día unidos y ordenados, separados por `", "` y `" y "`, medianoche `24:00`), o `"...: {nombre} no atiende los {día_plural}."` si no atiende ese día (`lunes`..`domingo`, plural `sábados`/`domingos`; `{nombre}` recortado o `"el profesional"` si es vacío/blanco; US-006 CA-3).

#### Scenario: Mensajes fuera de horario con tramos unidos y día sin atención
- **GIVEN** que P1 ("Dra. Laura Quiroga") atiende el martes en `[540, 780)`, `[780, 1020)` y `[1200, 1440)` y no tiene tramos el domingo
- **WHEN** se pide un turno de 17:30 a 18:00 hora local el martes (primer caso) o de 10:00 a 10:30 hora local el domingo (segundo caso)
- **THEN** el primer mensaje indica `"Dra. Laura Quiroga atiende el martes de 09:00 a 17:00 y de 20:00 a 24:00."` y el segundo indica `"Dra. Laura Quiroga no atiende los domingos."`

### Requirement: Orden y mensajes al validar tramos de horario
Al validar tramos, el dominio SHALL devolver primero todas las `INVALID_WORKING_HOURS` en orden de llegada y luego todas las `OVERLAPPING_WORKING_HOURS` ordenadas por la posición (desde 1) del primer tramo del par y, a igualdad, la del segundo. El mensaje de `INVALID_WORKING_HOURS` MUST mencionar la posición del tramo y el de `OVERLAPPING_WORKING_HOURS`, ambas posiciones y el día de la semana en español; ninguna lleva id en conflicto ni `reference_kind`.

#### Scenario: Orden y posiciones en violaciones de tramos inválidos y solapados
- **GIVEN** los tramos del martes `[540, 780)`, `[750, 750)`, `[720, 900)` y `[600, 660)` en ese orden
- **WHEN** se valida el conjunto
- **THEN** devuelve `INVALID_WORKING_HOURS` (tramo 2), `OVERLAPPING_WORKING_HOURS` (tramos 1 y 3, martes) y `OVERLAPPING_WORKING_HOURS` (tramos 1 y 4, martes), todas sin id en conflicto ni `reference_kind`
