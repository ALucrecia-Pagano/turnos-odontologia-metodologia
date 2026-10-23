# Spec Delta

Convención de los escenarios nuevos de este change: "hora local" es `America/Argentina/Buenos_Aires` (UTC-3, sin horario de verano), la zona que recibe el dominio. Cada instante se da en hora local y en UTC; por ejemplo, "23:30 hora local del 2026-10-20" es `2026-10-21T02:30:00+00:00`. Las horas sin aclaración siguen siendo UTC del 2026-10-20, como en el resto de la spec ("13:00" UTC son las 10:00 hora local).

## MODIFIED Requirements

### Requirement: Alta de un turno válido
Si el paciente existe, el profesional, el sillón y la prestación existen y están activos, la duración es válida, el inicio está en la grilla de 5 minutos, el turno empieza y termina en el mismo día local y el profesional y el sillón están libres en el intervalo pedido, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador. En todos los escenarios, salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos.

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
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias, duración, inicio en la grilla y turno dentro de un solo día local, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación, duración, inicio y, al final, medianoche (RN-AG-12). Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con violaciones de solapamiento. Si el pedido es válido, el dominio SHALL devolver todas las violaciones de solapamiento, no solo la primera (DD-08): una por cada turno con el que choca. Primero van todas las `PROFESSIONAL_OVERLAP` y después todas las `CHAIR_OVERLAP` (RN-AG-12). Dentro de cada grupo se ordenan por el inicio del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo.

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

### Requirement: Contenido de cada violación
Cada violación SHALL tener un código estable, un mensaje no vacío en español y, en las de solapamiento, el id del turno con el que choca; el mensaje MUST incluir ese id. Las violaciones de referencias SHALL indicar el tipo de referencia que falló (`reference_kind`: `PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`) y su mensaje MUST incluir el id de esa referencia; las demás violaciones no llevan tipo de referencia. El mensaje de `INVALID_DURATION` MUST mencionar la duración recibida y cada condición incumplida. El mensaje de `INVALID_START_TIME` MUST mencionar la hora de inicio recibida en hora local (`se recibió {hora}, hora local`) y cada condición incumplida, con el inicio como sujeto: si los minutos no son múltiplo de 5, la razón MUST decir "debe caer en un minuto múltiplo de 5"; si el inicio tiene segundos o fracciones de segundo, la razón MUST decir "no puede tener segundos ni fracciones de segundo"; las dos razones se unen con " y ". El mensaje de `CROSSES_MIDNIGHT` MUST mencionar el inicio y el fin del turno en hora local. Las horas de los mensajes SHALL mostrarse con formato `HH:MM`, o `HH:MM:SS` si la hora tiene segundos o microsegundos distintos de cero (los microsegundos no se muestran). Ni `INVALID_START_TIME` ni `CROSSES_MIDNIGHT` llevan id de turno en conflicto. El texto completo, con nombres y rango horario local, queda para C-08. Las violaciones de negocio se devuelven en el resultado y nunca como excepción.

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

### Requirement: Turno dentro de un solo día local
El inicio y el fin del turno MUST caer en el mismo día local (RN-AG-10, SU-09, US-007 CA-3). Si el turno cruza la medianoche local, el dominio SHALL rechazarlo con una violación `CROSSES_MIDNIGHT`. Por el intervalo semiabierto (DD-07), un turno que termina justo a las 00:00 locales no ocupa el día siguiente y MUST ser válido. La medianoche se evalúa con el instante completo del fin, incluidos segundos y fracciones de segundo: un fin a las 00:00:30 locales del día siguiente cruza la medianoche. La medianoche solo se evalúa si hay una duración efectiva válida, y se evalúa aunque el inicio esté fuera de la grilla.

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

### Requirement: Inicio en la grilla de 5 minutos
En hora local, el inicio del turno MUST tener minutos múltiplos de 5 y segundos y microsegundos en cero (RN-DI-05 en la parte del inicio, SU-02). La granularidad es la misma que la de la duración. Si el inicio no cumple alguna condición, el dominio SHALL rechazar el turno con **una sola** violación `INVALID_START_TIME`, sin id de turno en conflicto, aunque falle más de una condición.

#### Scenario: Inicio con minutos fuera de la grilla
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 10:03 hora local (13:03 UTC)
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_START_TIME`

#### Scenario: Inicio en la grilla
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 10:05 hora local (13:05 UTC)
- **THEN** el resultado es `Ok` con un turno de 10:05 a 10:35 hora local (de 13:05 a 13:35 UTC)

#### Scenario: Inicio con segundos o microsegundos
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 10:05:30 hora local (13:05:30 UTC, primer caso) o a las 10:05:00.250000 hora local (13:05:00.250000 UTC, segundo caso)
- **THEN** en ambos casos el resultado es `Rejected` con exactamente una violación `INVALID_START_TIME`
- **AND** el mensaje contiene la hora local con segundos: `10:05:30` en el primer caso y `10:05:00` en el segundo
- **AND** en ambos casos el mensaje dice "no puede tener segundos ni fracciones de segundo"

#### Scenario: Inicio que rompe dos condiciones
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 10:03:30 hora local (13:03:30 UTC), con minutos fuera de la grilla y segundos distintos de cero
- **THEN** el resultado es `Rejected` con exactamente una violación `INVALID_START_TIME`, no dos
- **AND** su mensaje es exactamente "El inicio del turno no es válido (se recibió 10:03:30, hora local): debe caer en un minuto múltiplo de 5 y no puede tener segundos ni fracciones de segundo."

### Requirement: Hora local en la zona horaria recibida
Las reglas de hora local (grilla del inicio y medianoche) SHALL evaluarse en la zona horaria que el dominio recibe como parámetro: `America/Argentina/Buenos_Aires` en el consultorio (SU-01, RN-GL-03, DD-07). El dominio MUST NOT fijar la zona ni leerla del entorno, y MUST NOT evaluar esas reglas sobre la hora UTC.

#### Scenario: Instante UTC que en hora local cae en otro día
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 02:30 UTC del 2026-10-20, que son las 23:30 hora local del 2026-10-19, con duración explícita de 60 minutos (hasta las 03:30 UTC del 2026-10-20, 00:30 hora local del 2026-10-20)
- **THEN** el resultado es `Rejected` con exactamente una violación `CROSSES_MIDNIGHT`, aunque en UTC el inicio y el fin caen el mismo día

#### Scenario: Turno que cruza la medianoche UTC pero no la local
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:30 UTC del 2026-10-20, que son las 20:30 hora local, con duración explícita de 60 minutos (hasta las 00:30 UTC del 2026-10-21, 21:30 hora local del 2026-10-20)
- **THEN** el resultado es `Ok`, porque en hora local el turno empieza y termina el mismo día
