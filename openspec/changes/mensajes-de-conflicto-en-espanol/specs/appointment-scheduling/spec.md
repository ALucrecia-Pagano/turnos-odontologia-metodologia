# Spec Delta

Convenciones de este delta, además de las de la spec principal: P1 se llama "Dra. Laura Quiroga" y S1 "Sillón 1"; los demás profesionales y sillones tienen un nombre no vacío que los escenarios no usan. La hora local es `America/Argentina/Buenos_Aires` (UTC-3 fijo en octubre de 2026): el martes 2026-10-20 a las 10:00 hora local son las 13:00 UTC (`2026-10-20T13:00:00+00:00`). Las horas sin zona son UTC del 2026-10-20, como en la spec principal. El intervalo en conflicto se da siempre en UTC; `{id de A}` es el id del turno A tal como aparece en el mensaje. Salvo que se diga otra cosa, cada profesional atiende todos los días de 00:00 a 24:00 hora local, no hay bloqueos, `now` es el 2026-10-01 a las 00:00 UTC y la prestación dura 30 minutos.

## MODIFIED Requirements

### Requirement: Rechazo por solapamiento de profesional
Si el intervalo del turno nuevo se solapa con el de un turno existente del mismo profesional que ocupa agenda, el dominio SHALL rechazarlo con una violación `PROFESSIONAL_OVERLAP` que identifica ese turno: lleva su id y su intervalo, el del turno existente, con inicio y fin en UTC (US-006 CA-1). No hay opción de forzar el turno (RN-AG-01, RN-AG-03, US-002).

#### Scenario: Solapamiento con un turno del mismo profesional
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno de 30 minutos para P1 en el sillón S2 que empieza a las 13:15
- **THEN** el resultado es `Rejected` con exactamente una violación `PROFESSIONAL_OVERLAP`
- **AND** la violación lleva el id del turno A y un mensaje en español que lo identifica

#### Scenario: Fin del turno nuevo dentro de un turno existente
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S2 de 12:45 a 13:15
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` que lleva el id del turno A

#### Scenario: Turno nuevo que contiene por completo a uno existente
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S2 de 12:45 a 13:45
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` que lleva el id del turno A

#### Scenario: Turno nuevo contenido dentro de uno existente
- **GIVEN** un turno existente de P1 en S1 de 13:00 a 14:00
- **WHEN** se pide un turno para P1 en S2 de 13:15 a 13:30
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` que lleva el id de ese turno

#### Scenario: Mismo intervalo exacto
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S2 de 13:00 a 13:30
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` que lleva el id del turno A

#### Scenario: Otro profesional a la misma hora y en otro sillón
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P2 en S2 de 13:00 a 13:30
- **THEN** el resultado es `Ok`

#### Scenario: Intervalo del turno con el que choca el profesional
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30, de 10:00 a 10:30 hora local) en un primer caso, o un turno existente de P1 en S1 de 13:00 a 14:00 (de 10:00 a 11:00 hora local) en un segundo caso
- **WHEN** se pide un turno de 30 minutos para P1 en el sillón S2 que empieza a las 13:15 (10:15 hora local)
- **THEN** la violación `PROFESSIONAL_OVERLAP` lleva el id del turno existente y su intervalo en UTC: de `2026-10-20T13:00:00+00:00` a `2026-10-20T13:30:00+00:00` en el primer caso, y de `2026-10-20T13:00:00+00:00` a `2026-10-20T14:00:00+00:00` en el segundo
- **AND** en ningún caso el intervalo es el del turno pedido (de 13:15 a 13:45)

#### Scenario: Intervalo en UTC de un turno existente cargado en hora de Buenos Aires
- **GIVEN** un turno existente de P1 en S1 cargado con inicio `2026-10-20T10:00:00-03:00` y fin `2026-10-20T10:30:00-03:00`
- **WHEN** se pide un turno para P1 en S2 de 13:15 a 13:45 UTC (de 10:15 a 10:45 hora local)
- **THEN** la violación `PROFESSIONAL_OVERLAP` lleva el intervalo de `2026-10-20T13:00:00+00:00` a `2026-10-20T13:30:00+00:00`, en UTC

### Requirement: Rechazo por solapamiento de sillón
Si el intervalo del turno nuevo se solapa con el de un turno existente del mismo sillón que ocupa agenda, el dominio SHALL rechazarlo con una violación `CHAIR_OVERLAP` que identifica ese turno con su id y su intervalo, el del turno existente, con inicio y fin en UTC (US-006 CA-1), sea cual sea el profesional (RN-AG-02, US-003).

#### Scenario: Mismo sillón con otro profesional
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno para P2 en S1 de 13:15 a 13:45
- **THEN** el resultado es `Rejected` con exactamente una violación `CHAIR_OVERLAP` que lleva el id del turno A

#### Scenario: Mismo profesional y mismo sillón solapados
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45
- **THEN** el resultado es `Rejected` con dos violaciones, en este orden: `PROFESSIONAL_OVERLAP` con el id del turno A y `CHAIR_OVERLAP` con el id del turno A

#### Scenario: Otro sillón a la misma hora
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P2 en S2 de 13:00 a 13:30
- **THEN** el resultado es `Ok`

#### Scenario: Intervalo del turno con el que choca el sillón
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30, de 10:00 a 10:30 hora local)
- **WHEN** se pide un turno para P2 en S1 de 13:15 a 13:45 (de 10:15 a 10:45 hora local)
- **THEN** la violación `CHAIR_OVERLAP` lleva el id del turno A y su intervalo, de `2026-10-20T13:00:00+00:00` a `2026-10-20T13:30:00+00:00`

#### Scenario: Cada violación de solapamiento lleva el intervalo de su turno
- **GIVEN** un turno B de P1 en S2 de 13:30 a 14:00, un turno C de P1 en S3 de 13:00 a 13:30 y un turno D de P2 en S1 de 13:45 a 14:15 (de 10:30 a 11:00, de 10:00 a 10:30 y de 10:45 a 11:15 hora local)
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 14:00 (de 10:00 a 11:00 hora local)
- **THEN** las tres violaciones, en este orden, llevan estos intervalos en UTC: `PROFESSIONAL_OVERLAP` con el turno C, de `2026-10-20T13:00:00+00:00` a `2026-10-20T13:30:00+00:00`; `PROFESSIONAL_OVERLAP` con el turno B, de `2026-10-20T13:30:00+00:00` a `2026-10-20T14:00:00+00:00`; y `CHAIR_OVERLAP` con el turno D, de `2026-10-20T13:45:00+00:00` a `2026-10-20T14:15:00+00:00`

### Requirement: Todas las violaciones, en orden estable
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias, duración, inicio en la grilla, turno dentro de un solo día local y turno que no empieza en el pasado, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación, duración, inicio, medianoche y, al final, pasado (RN-AG-12). El pasado se evalúa siempre, aunque no haya duración efectiva o la duración sea inválida, porque solo depende del inicio y del momento actual. Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con conflictos de agenda. Devolver todas las violaciones significa devolver todas las del primer grupo que falla, nunca solo la primera: si el pedido no es válido no hay un turno válido contra el cual comparar la agenda, así que los conflictos de agenda no se evalúan (RN-AG-12, US-006 CA-2). Si el pedido es válido, el dominio SHALL evaluar los conflictos de agenda y devolverlos todos juntos, no solo el primero (DD-08), en este orden: primero `OUTSIDE_WORKING_HOURS` (como mucho una), después todas las `BLOCKED_TIME`, después todas las `PROFESSIONAL_OVERLAP` y al final todas las `CHAIR_OVERLAP` (RN-AG-12). Hay una violación de bloqueo por cada bloqueo que pisa el turno y una de solapamiento por cada turno con el que choca; dentro de cada tipo se ordenan por el inicio del bloqueo o del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo de solapamiento.

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

### Requirement: Contenido de cada violación
Cada violación SHALL tener un código estable, un mensaje no vacío en español y, en las de solapamiento, el id del turno con el que choca; el mensaje MUST incluir ese id. Las violaciones de referencias SHALL indicar el tipo de referencia que falló (`reference_kind`: `PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`) y su mensaje MUST incluir el id de esa referencia; las demás violaciones no llevan tipo de referencia. El mensaje de `INVALID_DURATION` MUST mencionar la duración recibida y cada condición incumplida. El mensaje de `INVALID_START_TIME` MUST mencionar la hora de inicio recibida en hora local (`se recibió {hora}, hora local`) y cada condición incumplida, con el inicio como sujeto: si los minutos no son múltiplo de 5, la razón MUST decir "debe caer en un minuto múltiplo de 5"; si el inicio tiene segundos o fracciones de segundo, la razón MUST decir "no puede tener segundos ni fracciones de segundo"; las dos razones se unen con " y ". El mensaje de `CROSSES_MIDNIGHT` MUST mencionar el inicio y el fin del turno en hora local. Las horas de los mensajes SHALL mostrarse con formato `HH:MM`, o `HH:MM:SS` si la hora tiene segundos o microsegundos distintos de cero (los microsegundos no se muestran), salvo el momento actual del mensaje de `IN_THE_PAST`, que se muestra siempre con fecha y segundos (requisito "Mensaje de un turno en el pasado"). Ni `INVALID_START_TIME`, ni `CROSSES_MIDNIGHT` ni `IN_THE_PAST` llevan id de turno en conflicto. El intervalo en conflicto, con inicio y fin en UTC, SHALL estar presente si y solo si la violación lleva id de turno o de bloqueo en conflicto: en `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` es el del turno existente y en `BLOCKED_TIME`, el del bloqueo; ninguna otra violación lleva intervalo, tampoco `OUTSIDE_WORKING_HOURS` (US-006 CA-1). El mensaje de `PROFESSIONAL_OVERLAP` SHALL ser "{nombre del profesional} ya tiene un turno de {inicio} a {fin} (hora local) que se superpone (turno {id})." y el de `CHAIR_OVERLAP`, "{nombre del sillón} está ocupado de {inicio} a {fin} (hora local) por un turno que se superpone (turno {id}).", donde {inicio} y {fin} son los del turno existente, en hora local y con el formato de horas de este requisito (US-006 CA-3). Los nombres de los mensajes de conflicto de agenda son los del profesional y del sillón del pedido, tal como se cargaron, sin artículo y siempre como sujeto de la oración. Si el nombre está vacío o tiene solo espacios, el mensaje MUST usar en su lugar el sustantivo genérico: "El profesional" o "El sillón" al principio de la oración, y "el profesional", en minúscula, después de dos puntos (mensajes de `OUTSIDE_WORKING_HOURS` y `BLOCKED_TIME`). Los mensajes de `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_BLOCK`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` no llevan nombres y no cambian: las violaciones de referencias identifican la entidad por su id aunque tenga nombre. Las violaciones de negocio se devuelven en el resultado y nunca como excepción.

En los escenarios de este requisito P1 se llama "Dra. Laura Quiroga" y S1 "Sillón 1", salvo que se diga otra cosa.

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

#### Scenario: Mensaje de solapamiento con un turno existente con segundos
- **GIVEN** un turno existente G de P1 en S2 de 13:00:30 a 13:30:30 (de 10:00:30 a 10:30:30 hora local)
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45 (de 10:15 a 10:45 hora local)
- **THEN** el resultado es `Rejected` con una sola violación, `PROFESSIONAL_OVERLAP`, cuyo mensaje es exactamente "Dra. Laura Quiroga ya tiene un turno de 10:00:30 a 10:30:30 (hora local) que se superpone (turno {id de G})."

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

### Requirement: Turno dentro del horario de atención
El turno MUST caer completo dentro de un tramo del horario de atención del profesional del pedido para el día de la semana local del turno, evaluado en hora local (RN-AG-04, RN-GL-03; US-004 CA-1, CA-2, CA-3, CA-6 y CA-7). Si no, el dominio SHALL rechazarlo con una sola violación `OUTSIDE_WORKING_HOURS`, sin id de turno en conflicto ni tipo de referencia. Un tramo `[inicio, fin)` es semiabierto (DD-07): el turno es válido si empieza en el inicio del tramo o después y termina en el fin del tramo o antes; un turno que termina a las 00:00 locales tiene su fin en el minuto 1440 del día de su inicio. Los tramos del mismo profesional y día que son contiguos (uno termina justo donde empieza el otro) cuentan como un solo tramo, y lo mismo pasa con los que se pisan (por ejemplo, uno contenido en otro): se unen desde el menor inicio hasta el mayor fin, así que un tramo contenido en otro no lo acorta; si hay un hueco entre dos tramos, un turno que lo pisa se rechaza. Un día sin tramos del profesional es un día en que no atiende. El dominio SHALL elegir por sí mismo los tramos que corresponden (del profesional del pedido y del día local del turno): la corrección del resultado MUST NOT depender de que el llamador haya filtrado la lista. Un turno existente puede quedar fuera del horario (por ejemplo, si el horario cambió después): el horario solo se evalúa sobre el turno nuevo.

El mensaje de `OUTSIDE_WORKING_HOURS` MUST mencionar el inicio y el fin del turno en hora local, el nombre del profesional del pedido y, si el profesional tiene tramos ese día, todos los tramos del día ordenados por inicio, con los tramos contiguos ya unidos y el fin de la medianoche como `24:00`: "El turno de {inicio} a {fin} (hora local) queda fuera del horario de atención: {nombre del profesional} atiende el {día} de {inicio del tramo} a {fin del tramo}", con los tramos unidos por ", " y el último por " y ", y un punto final. Si el profesional no tiene tramos ese día, el mensaje termina en ": {nombre del profesional} no atiende los {día en plural}." El nombre va tal como se cargó, sin artículo y como sujeto; si está vacío o tiene solo espacios, se usa "el profesional", en minúscula porque va después de dos puntos (US-006 CA-3). El día de la semana va en español y en minúscula (lunes, martes, miércoles, jueves, viernes, sábado, domingo; en plural: lunes, martes, miércoles, jueves, viernes, sábados, domingos). Estos textos reemplazan a los aprobados antes ("…queda fuera del horario de atención del profesional: el {día} atiende…" y "…: no atiende los {día en plural}."), y con ellos cambian los tres escenarios de mensaje de este requisito.

Horario base de los escenarios de este requisito, salvo que se diga otra cosa: P1 atiende el martes (día ISO 2) en `[540, 780)` (de 09:00 a 13:00) y `[900, 1140)` (de 15:00 a 19:00), y no tiene tramos el domingo (día ISO 7). Los turnos son de P1 en S1, el martes 2026-10-20, sin turnos existentes. P1 se llama "Dra. Laura Quiroga".

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

### Requirement: Turno fuera de los bloqueos del profesional
El turno MUST NOT superponerse con ningún bloqueo del profesional del pedido (RN-AG-05; US-004 CA-4 y CA-5). Por cada bloqueo que pisa, el dominio SHALL devolver una violación `BLOCKED_TIME` con el id del bloqueo y su intervalo, con inicio y fin en UTC, completo aunque el bloqueo dure varios días (US-006 CA-1), sin id de turno ni tipo de referencia. Bloqueo y turno son semiabiertos (DD-07) y se comparan como instantes, aunque el bloqueo dure varios días. El dominio elige los bloqueos del profesional: el resultado MUST NOT depender del filtrado del llamador.

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
El mensaje de `BLOCKED_TIME` MUST decir, en hora local, el inicio y el fin del turno, el nombre del profesional del pedido, el inicio y el fin del bloqueo con fecha (`dd/mm/aaaa HH:MM`, porque puede durar varios días), el id del bloqueo y, si tiene, el motivo: "El turno de {inicio} a {fin} (hora local) se superpone con un bloqueo de agenda: {nombre del profesional} tiene la agenda bloqueada del {inicio del bloqueo} al {fin del bloqueo} (hora local) (bloqueo {id}).", seguido, si hay motivo, de la oración aparte " Motivo: {motivo}." Un motivo vacío o con solo espacios cuenta como sin motivo; si no, se muestra tal como se cargó. El nombre va tal como se cargó, sin artículo y como sujeto; si está vacío o tiene solo espacios, se usa "el profesional", en minúscula porque va después de dos puntos (US-006 CA-3). Este texto reemplaza al aprobado antes ("…se superpone con el bloqueo {id} del profesional, del {inicio del bloqueo} al {fin del bloqueo} (hora local)."), y con él cambian los tres escenarios de mensaje de este requisito. En los escenarios de este requisito P1 se llama "Dra. Laura Quiroga".

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

### Requirement: Mensaje de un turno en el pasado
El mensaje de `IN_THE_PAST` MUST decir, en hora local, el inicio del turno con fecha (`dd/mm/aaaa HH:MM`) y el momento actual con fecha y segundos (`dd/mm/aaaa HH:MM:SS`, sin microsegundos): "El inicio del turno ({inicio}, hora local) es anterior al momento actual ({now}, hora local): no se pueden dar turnos en el pasado." La fecha es la del día local, no la de UTC. El mensaje no menciona al profesional ni al sillón.

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

## ADDED Requirements

### Requirement: Nombre del profesional y del sillón
El profesional SHALL tener un nombre completo y el sillón, un nombre (KB 04), que el llamador informa siempre al construir la entidad: no tienen valor por defecto. El dominio MUST NOT validarlos ni lanzar una excepción al construir la entidad, aunque estén vacíos o tengan solo espacios, y MUST conservarlos tal como se cargaron: la validez del nombre la decide el alta del catálogo. El dominio usa el nombre solo en los mensajes de conflicto de agenda.

#### Scenario: Profesional y sillón con nombre
- **WHEN** se construyen P1 con el nombre "Dra. Laura Quiroga" y S1 con el nombre "Sillón 1", los dos activos
- **THEN** P1 conserva el nombre "Dra. Laura Quiroga" y S1 el nombre "Sillón 1", con su id y su estado activo

#### Scenario: Nombre vacío o en blanco al construir
- **WHEN** se construyen P1 y S1 con el nombre `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **THEN** en ambos casos la construcción no falla y cada entidad conserva el nombre tal como se cargó, sin recortarlo
