# Spec Delta

Convenciones de este delta, además de las de la spec principal: el momento actual (`now`) es el instante que recibe el dominio con el contexto de la agenda; se da en hora local (`America/Argentina/Buenos_Aires`, UTC-3 fijo en octubre de 2026) y en UTC. El martes 2026-10-20 a las 10:00 hora local son las 13:00 UTC, y el martes 2026-10-20 a las 23:30 hora local es el miércoles 2026-10-21 a las 02:30 UTC. Salvo que se diga otra cosa, `now` es el 2026-10-01 a las 00:00 UTC, anterior a todos los turnos pedidos; los escenarios de este change que dependen del pasado dicen su `now` explícitamente. P1 y P2 atienden todos los días en un tramo de día completo (`[0, 1440)`), los turnos pedidos son de P1 en S1, la prestación tiene duración por defecto de 30 minutos y no hay turnos existentes ni bloqueos.

## MODIFIED Requirements

### Requirement: Alta de un turno válido
Si el paciente existe, el profesional, el sillón y la prestación existen y están activos, la duración es válida, el inicio está en la grilla de 5 minutos, el turno empieza y termina en el mismo día local, el inicio no es anterior al momento actual (`now`), el turno cae completo dentro del horario de atención del profesional, no se superpone con ningún bloqueo del profesional y el profesional y el sillón están libres en el intervalo pedido, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador. En todos los escenarios, salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos, cada profesional atiende todos los días de la semana en un tramo de día completo, de 00:00 a 24:00 hora local (`[0, 1440)`), no hay bloqueos y el momento actual (`now`) es el 2026-10-01 a las 00:00 UTC, anterior a todos los turnos pedidos.

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
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias, duración, inicio en la grilla, turno dentro de un solo día local y turno que no empieza en el pasado, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación, duración, inicio, medianoche y, al final, pasado (RN-AG-12). El pasado se evalúa siempre, aunque no haya duración efectiva o la duración sea inválida, porque solo depende del inicio y del momento actual. Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con conflictos de agenda. Si el pedido es válido, el dominio SHALL evaluar los conflictos de agenda y devolverlos todos juntos, no solo el primero (DD-08), en este orden: primero `OUTSIDE_WORKING_HOURS` (como mucho una), después todas las `BLOCKED_TIME`, después todas las `PROFESSIONAL_OVERLAP` y al final todas las `CHAIR_OVERLAP` (RN-AG-12). Hay una violación de bloqueo por cada bloqueo que pisa el turno y una de solapamiento por cada turno con el que choca; dentro de cada tipo se ordenan por el inicio del bloqueo o del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo de solapamiento.

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
Cada violación SHALL tener un código estable, un mensaje no vacío en español y, en las de solapamiento, el id del turno con el que choca; el mensaje MUST incluir ese id. Las violaciones de referencias SHALL indicar el tipo de referencia que falló (`reference_kind`: `PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`) y su mensaje MUST incluir el id de esa referencia; las demás violaciones no llevan tipo de referencia. El mensaje de `INVALID_DURATION` MUST mencionar la duración recibida y cada condición incumplida. El mensaje de `INVALID_START_TIME` MUST mencionar la hora de inicio recibida en hora local (`se recibió {hora}, hora local`) y cada condición incumplida, con el inicio como sujeto: si los minutos no son múltiplo de 5, la razón MUST decir "debe caer en un minuto múltiplo de 5"; si el inicio tiene segundos o fracciones de segundo, la razón MUST decir "no puede tener segundos ni fracciones de segundo"; las dos razones se unen con " y ". El mensaje de `CROSSES_MIDNIGHT` MUST mencionar el inicio y el fin del turno en hora local. Las horas de los mensajes SHALL mostrarse con formato `HH:MM`, o `HH:MM:SS` si la hora tiene segundos o microsegundos distintos de cero (los microsegundos no se muestran), salvo el momento actual del mensaje de `IN_THE_PAST`, que se muestra siempre con fecha y segundos (requisito "Mensaje de un turno en el pasado"). Ni `INVALID_START_TIME`, ni `CROSSES_MIDNIGHT` ni `IN_THE_PAST` llevan id de turno en conflicto. El texto completo, con nombres y rango horario local, queda para C-08. Las violaciones de negocio se devuelven en el resultado y nunca como excepción.

#### Scenario: Mensajes de las violaciones de solapamiento
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45
- **THEN** cada una de las dos violaciones tiene un mensaje en español que contiene el id del turno A
- **AND** el mensaje de `PROFESSIONAL_OVERLAP` menciona al profesional y el de `CHAIR_OVERLAP` menciona al sillón

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

## ADDED Requirements

### Requirement: Turno que no empieza en el pasado
El inicio del turno MUST NOT ser anterior al momento actual (`now`) que recibe el dominio (RN-AG-06; US-005 CA-1 a CA-3). Si lo es, el dominio SHALL rechazarlo con una sola violación `IN_THE_PAST`, sin id de turno ni de bloqueo en conflicto ni tipo de referencia. La comparación es estricta entre instantes, con segundos y microsegundos: un inicio igual a `now` es válido, y `now` no se trunca ni tiene tolerancia.

#### Scenario: Inicio cinco minutos antes del momento actual
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC), sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación `IN_THE_PAST`

#### Scenario: Inicio igual al momento actual
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 10:00 hora local (13:00 UTC), sin duración explícita
- **THEN** el resultado es `Ok` con el turno de 13:00 a 13:30 UTC (de 10:00 a 10:30 hora local)

#### Scenario: Inicio posterior al momento actual
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 10:05 hora local (13:05 UTC), sin duración explícita
- **THEN** el resultado es `Ok` con el turno de 13:05 a 13:35 UTC (de 10:05 a 10:35 hora local)

#### Scenario: Momento actual con segundos e inicio en el mismo minuto
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se pide un turno a las 10:00 hora local (13:00 UTC), sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación `IN_THE_PAST`, porque `now` no se trunca al minuto

#### Scenario: Momento actual con segundos e inicio en el paso siguiente de la grilla
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se pide un turno a las 10:05 hora local (13:05 UTC), sin duración explícita
- **THEN** el resultado es `Ok`

#### Scenario: Momento actual un microsegundo después del inicio
- **GIVEN** que `now` es el martes 2026-10-20 a las 13:00:00.000001 UTC (10:00:00.000001 hora local)
- **WHEN** se pide un turno a las 10:00 hora local (13:00 UTC), sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación `IN_THE_PAST`, porque la comparación no tiene tolerancia

#### Scenario: Momento actual antes de la medianoche local e inicio en el día siguiente
- **GIVEN** que `now` es el martes 2026-10-20 a las 23:30 hora local (02:30 UTC del miércoles 2026-10-21)
- **WHEN** se pide un turno el miércoles 2026-10-21 a las 00:00 hora local (03:00 UTC del 2026-10-21), sin duración explícita
- **THEN** el resultado es `Ok`

#### Scenario: Inicio en el pasado del mismo día local, que en UTC es otro día
- **GIVEN** que `now` es el martes 2026-10-20 a las 23:30 hora local (02:30 UTC del miércoles 2026-10-21)
- **WHEN** se pide un turno el martes 2026-10-20 a las 23:00 hora local (02:00 UTC del 2026-10-21), sin duración explícita
- **THEN** el resultado es `Rejected` con exactamente una violación `IN_THE_PAST`

### Requirement: Mensaje de un turno en el pasado
El mensaje de `IN_THE_PAST` MUST decir, en hora local, el inicio del turno con fecha (`dd/mm/aaaa HH:MM`) y el momento actual con fecha y segundos (`dd/mm/aaaa HH:MM:SS`, sin microsegundos): "El inicio del turno ({inicio}, hora local) es anterior al momento actual ({now}, hora local): no se pueden dar turnos en el pasado." La fecha es la del día local, no la de UTC. El texto con nombres queda para C-08.

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

### Requirement: Momento actual inyectado en el contexto
El dominio SHALL recibir el momento actual (`now`) con el contexto de la agenda, junto con la zona, los tramos y los bloqueos, y MUST NOT leer el reloj del sistema (RN-GL-04; US-005 CA-4). `now` SHALL tener zona horaria y MUST normalizarse a UTC conservando el mismo momento. Un `now` sin zona (*naive*) es un error de programación del llamador y MUST rechazarse con `ValueError` al construir el contexto, no como violación de negocio.

#### Scenario: Momento actual en hora de Buenos Aires
- **WHEN** se construye el contexto con `now` igual a `2026-10-20T10:00:00-03:00`
- **THEN** el `now` del contexto es `2026-10-20T13:00:00+00:00`, en UTC

#### Scenario: Momento actual en otra zona
- **WHEN** se construye el contexto con `now` igual a `2026-10-20T14:00:00+01:00`
- **THEN** el `now` del contexto es `2026-10-20T13:00:00+00:00`, en UTC, el mismo momento

#### Scenario: Momento actual sin zona horaria
- **WHEN** se construye el contexto con `now` igual a `2026-10-20T10:00:00` sin zona
- **THEN** la construcción falla con `ValueError` cuyo mensaje indica que el instante necesita zona horaria
