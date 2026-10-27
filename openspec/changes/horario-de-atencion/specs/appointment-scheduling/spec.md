# Spec Delta

Convención de los escenarios nuevos de este change: "hora local" es `America/Argentina/Buenos_Aires` (UTC-3, sin horario de verano), la zona que recibe el dominio, y cada instante se da en hora local y en UTC. El 2026-10-20 es martes (día ISO 2) y el 2026-10-25, domingo (día ISO 7). Los tramos del horario de atención se escriben como `[inicio, fin)` en minutos locales desde las 00:00 (por ejemplo, `[540, 780)` es de 09:00 a 13:00), con el día de la semana ISO (1 = lunes … 7 = domingo). Los escenarios de C-02 a C-04 no cambian: en ellos los profesionales atienden todo el día, los 7 días.

## MODIFIED Requirements

### Requirement: Alta de un turno válido
Si el paciente existe, el profesional, el sillón y la prestación existen y están activos, la duración es válida, el inicio está en la grilla de 5 minutos, el turno empieza y termina en el mismo día local, el turno cae completo dentro del horario de atención del profesional y el profesional y el sillón están libres en el intervalo pedido, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador. En todos los escenarios, salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos, y cada profesional atiende todos los días de la semana en un tramo de día completo, de 00:00 a 24:00 hora local (`[0, 1440)`).

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
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias, duración, inicio en la grilla y turno dentro de un solo día local, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación, duración, inicio y, al final, medianoche (RN-AG-12). Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con conflictos de agenda. Si el pedido es válido, el dominio SHALL evaluar los conflictos de agenda y devolverlos todos juntos, no solo el primero (DD-08), en este orden: primero `OUTSIDE_WORKING_HOURS` (como mucho una), después todas las `PROFESSIONAL_OVERLAP` y al final todas las `CHAIR_OVERLAP` (RN-AG-12). Hay una violación de solapamiento por cada turno con el que choca; dentro de cada tipo se ordenan por el inicio del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo.

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

### Requirement: Hora local en la zona horaria recibida
Las reglas de hora local (grilla del inicio, medianoche y horario de atención) SHALL evaluarse en la zona horaria que el dominio recibe como parámetro: `America/Argentina/Buenos_Aires` en el consultorio (SU-01, RN-GL-03, DD-07). El dominio MUST NOT fijar la zona ni leerla del entorno, y MUST NOT evaluar esas reglas sobre la hora UTC.

#### Scenario: Instante UTC que en hora local cae en otro día
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 02:30 UTC del 2026-10-20, que son las 23:30 hora local del 2026-10-19, con duración explícita de 60 minutos (hasta las 03:30 UTC del 2026-10-20, 00:30 hora local del 2026-10-20)
- **THEN** el resultado es `Rejected` con exactamente una violación `CROSSES_MIDNIGHT`, aunque en UTC el inicio y el fin caen el mismo día

#### Scenario: Turno que cruza la medianoche UTC pero no la local
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente
- **WHEN** se pide un turno a las 23:30 UTC del 2026-10-20, que son las 20:30 hora local, con duración explícita de 60 minutos (hasta las 00:30 UTC del 2026-10-21, 21:30 hora local del 2026-10-20)
- **THEN** el resultado es `Ok`, porque en hora local el turno empieza y termina el mismo día

## ADDED Requirements

### Requirement: Turno dentro del horario de atención
El turno MUST caer completo dentro de un tramo del horario de atención del profesional del pedido para el día de la semana local del turno, evaluado en hora local (RN-AG-04, RN-GL-03; US-004 CA-1, CA-2, CA-3, CA-6 y CA-7). Si no, el dominio SHALL rechazarlo con una sola violación `OUTSIDE_WORKING_HOURS`, sin id de turno en conflicto ni tipo de referencia. Un tramo `[inicio, fin)` es semiabierto (DD-07): el turno es válido si empieza en el inicio del tramo o después y termina en el fin del tramo o antes; un turno que termina a las 00:00 locales tiene su fin en el minuto 1440 del día de su inicio. Los tramos del mismo profesional y día que son contiguos (uno termina justo donde empieza el otro) cuentan como un solo tramo; si hay un hueco entre dos tramos, un turno que lo pisa se rechaza. Un día sin tramos del profesional es un día en que no atiende. El dominio SHALL elegir por sí mismo los tramos que corresponden (del profesional del pedido y del día local del turno): la corrección del resultado MUST NOT depender de que el llamador haya filtrado la lista. Un turno existente puede quedar fuera del horario (por ejemplo, si el horario cambió después): el horario solo se evalúa sobre el turno nuevo.

El mensaje de `OUTSIDE_WORKING_HOURS` MUST mencionar el inicio y el fin del turno en hora local y, si el profesional tiene tramos ese día, todos los tramos del día ordenados por inicio, con los tramos contiguos ya unidos y el fin de la medianoche como `24:00`: "El turno de {inicio} a {fin} (hora local) queda fuera del horario de atención del profesional: el {día} atiende de {inicio del tramo} a {fin del tramo}", con los tramos unidos por ", " y el último por " y ", y un punto final. Si el profesional no tiene tramos ese día, el mensaje termina en ": el profesional no atiende los {día en plural}." El día de la semana va en español y en minúscula (lunes, martes, miércoles, jueves, viernes, sábado, domingo; en plural: lunes, martes, miércoles, jueves, viernes, sábados, domingos). El texto completo, con el nombre del profesional, queda para C-08.

Horario base de los escenarios de este requisito, salvo que se diga otra cosa: P1 atiende el martes (día ISO 2) en `[540, 780)` (de 09:00 a 13:00) y `[900, 1140)` (de 15:00 a 19:00), y no tiene tramos el domingo (día ISO 7). Los turnos son de P1 en S1, el martes 2026-10-20, sin turnos existentes.

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

#### Scenario: Tramo de otro profesional
- **GIVEN** que P2 atiende el martes en `[540, 780)` y P1 no tiene tramos el martes
- **WHEN** se pide un turno para P1 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** el resultado es `Rejected` con exactamente una violación `OUTSIDE_WORKING_HOURS`, porque el tramo de P2 no cuenta para P1

#### Scenario: Turno que pasa de un tramo a otro contiguo
- **GIVEN** que P1 atiende el martes en `[540, 780)` (de 09:00 a 13:00) y `[780, 1020)` (de 13:00 a 17:00)
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** el resultado es `Ok`, porque los dos tramos contiguos cuentan como uno solo, de 09:00 a 17:00

#### Scenario: Mensaje de un turno fuera de los tramos del día
- **GIVEN** el horario base
- **WHEN** se pide un turno de 12:30 a 13:30 hora local (de 15:30 a 16:30 UTC), con duración explícita de 60 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención del profesional: el martes atiende de 09:00 a 13:00 y de 15:00 a 19:00."
- **AND** la violación no tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Mensaje de un turno en un día sin tramos
- **GIVEN** el horario base, en el que P1 no tiene tramos el domingo
- **WHEN** se pide un turno el domingo 2026-10-25 de 10:00 a 10:30 hora local (de 13:00 a 13:30 UTC), con duración explícita de 30 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención del profesional: el profesional no atiende los domingos."

#### Scenario: Mensaje con tramos contiguos y un tramo hasta la medianoche
- **GIVEN** que P1 atiende el martes en `[1200, 1440)` (de 20:00 a 24:00), `[780, 1020)` (de 13:00 a 17:00) y `[540, 780)` (de 09:00 a 13:00), recibidos en ese orden
- **WHEN** se pide un turno de 17:30 a 18:00 hora local (de 20:30 a 21:00 UTC), con duración explícita de 30 minutos
- **THEN** la violación `OUTSIDE_WORKING_HOURS` tiene exactamente el mensaje "El turno de 17:30 a 18:00 (hora local) queda fuera del horario de atención del profesional: el martes atiende de 09:00 a 17:00 y de 20:00 a 24:00."

### Requirement: Validez de un conjunto de tramos
El dominio SHALL ofrecer la validación de un conjunto de tramos del horario de atención (los que se cargan para uno o varios profesionales; RN-DI-01, RN-DI-02; US-010 CA-1 y CA-2) y devolver la lista de violaciones, vacía si el conjunto es válido; las violaciones se devuelven como resultado y nunca como excepción. Un tramo es inválido si su día de la semana no está entre 1 y 7, si su inicio o su fin no están entre 0 y 1440, o si su inicio no es anterior a su fin: el dominio SHALL informar una sola violación `INVALID_WORKING_HOURS` por tramo inválido, aunque falle más de una condición. Dos tramos válidos del mismo profesional y el mismo día que se solapan (comparten al menos un minuto, con tramos semiabiertos) SHALL producir una violación `OVERLAPPING_WORKING_HOURS` por cada par. Puede haber varios tramos por día; los tramos contiguos, los de días distintos y los de profesionales distintos no se solapan. Un tramo inválido no participa de la búsqueda de solapamientos.

Las violaciones se devuelven en orden estable: primero todas las `INVALID_WORKING_HOURS`, en el orden en que llegaron los tramos, y después todas las `OVERLAPPING_WORKING_HOURS`, ordenadas por la posición del primer tramo del par y, a igual primero, por la del segundo. Los tramos se identifican en los mensajes por su posición en la lista recibida, contando desde 1. El mensaje de `INVALID_WORKING_HOURS` MUST mencionar la posición del tramo; el de `OVERLAPPING_WORKING_HOURS` MUST mencionar las posiciones de los dos tramos y el día de la semana en español. Ninguna de las dos violaciones lleva id de turno en conflicto ni tipo de referencia.

En los escenarios de este requisito los tramos son de P1, salvo que se diga otra cosa, y se listan en el orden en que se reciben.

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
