# Spec Delta

Convenciones de este delta, además de las de la spec principal: los bloqueos se dan en hora local (`America/Argentina/Buenos_Aires`, UTC-3) y en UTC. BL1 = bloqueo de P1, sin motivo, del martes 2026-10-20 de 10:00 a 12:00 hora local (de 13:00 a 15:00 UTC). Salvo que se diga otra cosa, P1 y P2 atienden todos los días en un tramo de día completo (`[0, 1440)`), los turnos pedidos son de P1 en S1 y no hay turnos existentes.

## MODIFIED Requirements

### Requirement: Alta de un turno válido
Si el paciente existe, el profesional, el sillón y la prestación existen y están activos, la duración es válida, el inicio está en la grilla de 5 minutos, el turno empieza y termina en el mismo día local, el turno cae completo dentro del horario de atención del profesional, no se superpone con ningún bloqueo del profesional y el profesional y el sillón están libres en el intervalo pedido, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador. En todos los escenarios, salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos, cada profesional atiende todos los días de la semana en un tramo de día completo, de 00:00 a 24:00 hora local (`[0, 1440)`), y no hay bloqueos.

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
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias, duración, inicio en la grilla y turno dentro de un solo día local, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación, duración, inicio y, al final, medianoche (RN-AG-12). Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con conflictos de agenda. Si el pedido es válido, el dominio SHALL evaluar los conflictos de agenda y devolverlos todos juntos, no solo el primero (DD-08), en este orden: primero `OUTSIDE_WORKING_HOURS` (como mucho una), después todas las `BLOCKED_TIME`, después todas las `PROFESSIONAL_OVERLAP` y al final todas las `CHAIR_OVERLAP` (RN-AG-12). Hay una violación de bloqueo por cada bloqueo que pisa el turno y una de solapamiento por cada turno con el que choca; dentro de cada tipo se ordenan por el inicio del bloqueo o del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo de solapamiento.

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

## ADDED Requirements

### Requirement: Turno fuera de los bloqueos del profesional
El turno MUST NOT superponerse con ningún bloqueo del profesional del pedido (RN-AG-05; US-004 CA-4 y CA-5). Por cada bloqueo que pisa, el dominio SHALL devolver una violación `BLOCKED_TIME` con el id del bloqueo, sin id de turno ni tipo de referencia. Bloqueo y turno son semiabiertos (DD-07) y se comparan como instantes, aunque el bloqueo dure varios días. El dominio elige los bloqueos del profesional: el resultado MUST NOT depender del filtrado del llamador.

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

### Requirement: Mensaje de un turno bloqueado
El mensaje de `BLOCKED_TIME` MUST decir, en hora local, el inicio y el fin del turno, el id del bloqueo, su inicio y su fin con fecha (`dd/mm/aaaa HH:MM`, porque puede durar varios días) y, si tiene, el motivo: "El turno de {inicio} a {fin} (hora local) se superpone con el bloqueo {id} del profesional, del {inicio del bloqueo} al {fin del bloqueo} (hora local).", seguido, si hay motivo, de la oración aparte " Motivo: {motivo}." Un motivo vacío o con solo espacios cuenta como sin motivo. El texto con nombres queda para C-08.

#### Scenario: Mensaje de un bloqueo sin motivo
- **GIVEN** el bloqueo BL1, sin motivo
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** el mensaje de la violación `BLOCKED_TIME` es exactamente "El turno de 10:30 a 11:00 (hora local) se superpone con el bloqueo {id de BL1} del profesional, del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local)."
- **AND** la violación no tiene id de turno en conflicto ni tipo de referencia

#### Scenario: Mensaje de un bloqueo de varios días con motivo
- **GIVEN** el bloqueo BLV, con motivo "vacaciones"
- **WHEN** se pide un turno el domingo 2026-10-25 de 23:30 a 23:55 hora local (de 02:30 a 02:55 UTC del 2026-10-26), con duración explícita de 25 minutos
- **THEN** el mensaje de la violación `BLOCKED_TIME` es exactamente "El turno de 23:30 a 23:55 (hora local) se superpone con el bloqueo {id de BLV} del profesional, del 19/10/2026 00:00 al 26/10/2026 00:00 (hora local). Motivo: vacaciones."
- **AND** el mensaje no contiene las horas en UTC (`02:30`, `03:00`)

#### Scenario: Mensaje de un bloqueo con motivo vacío o en blanco
- **GIVEN** el bloqueo BL1 con motivo `""` (primer caso) o `"   "`, solo espacios (segundo caso)
- **WHEN** se pide un turno de 10:30 a 11:00 hora local (de 13:30 a 14:00 UTC), con duración explícita de 30 minutos
- **THEN** en ambos casos el mensaje de la violación `BLOCKED_TIME` es exactamente el mismo que el de un bloqueo sin motivo, terminado en "(hora local).", sin "Motivo:"

### Requirement: Validez de un bloqueo
El dominio SHALL ofrecer la validación de un bloqueo que carga el usuario (RN-DI-03; US-011 CA-1 y CA-2). Si `inicio >= fin`, SHALL devolver una violación `INVALID_BLOCK` con un mensaje en español que diga que el inicio debe ser anterior al fin, sin id de turno ni de bloqueo en conflicto. Un bloqueo así se puede construir: el rechazo es una violación, no una excepción. No se exige la grilla de 5 minutos ni se prohíbe que dos bloqueos se pisen.

#### Scenario: Bloqueo válido
- **GIVEN** el bloqueo BL1 (de 10:00 a 12:00 hora local, de 13:00 a 15:00 UTC)
- **WHEN** se valida el bloqueo
- **THEN** no hay violaciones

#### Scenario: Bloqueo con inicio igual al fin
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 10:00 a 10:00 hora local (de 13:00 a 13:00 UTC)
- **WHEN** se valida el bloqueo
- **THEN** hay exactamente una violación `INVALID_BLOCK`, con un mensaje que contiene "el inicio debe ser anterior al fin"

#### Scenario: Bloqueo con inicio posterior al fin
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 12:00 a 10:00 hora local (de 15:00 a 13:00 UTC)
- **WHEN** se valida el bloqueo
- **THEN** hay exactamente una violación `INVALID_BLOCK`

#### Scenario: Bloqueo de un minuto, fuera de la grilla
- **GIVEN** un bloqueo de P1 del 2026-10-20 de 10:00 a 10:01 hora local (de 13:00 a 13:01 UTC)
- **WHEN** se valida el bloqueo
- **THEN** no hay violaciones, porque los bloqueos no tienen grilla

### Requirement: Instantes del bloqueo con zona horaria y normalizados a UTC
El inicio y el fin de un bloqueo SHALL tener zona horaria y MUST normalizarse a UTC conservando el mismo momento. Un instante sin zona (*naive*) es un error de programación y MUST rechazarse con `ValueError` al construir el bloqueo, no como violación de negocio.

#### Scenario: Bloqueo cargado en hora de Buenos Aires
- **WHEN** se construye un bloqueo con inicio `2026-10-20T10:00:00-03:00` y fin `2026-10-20T12:00:00-03:00`
- **THEN** el bloqueo tiene inicio `2026-10-20T13:00:00+00:00` y fin `2026-10-20T15:00:00+00:00`, ambos en UTC

#### Scenario: Bloqueo con un instante sin zona
- **WHEN** se construye un bloqueo con inicio `2026-10-20T10:00:00` sin zona (primer caso) o con fin sin zona (segundo caso)
- **THEN** la construcción falla con `ValueError` cuyo mensaje indica que el instante necesita zona horaria

### Requirement: Turnos afectados por un bloqueo
Dado un bloqueo y una lista de turnos existentes, el dominio SHALL devolver los turnos que pisa: del mismo profesional, en un estado que ocupa agenda (`reservado`, `confirmado`, `atendido`) y que se solapan con el bloqueo (semiabiertos), ordenados por inicio (RN-DI-04, SU-05; US-011 CA-3). Crear el bloqueo MUST NOT cancelar ni mover esos turnos: se devuelven sin cambios, para que recepción los reprograme.

Turnos de los escenarios de este requisito, todos del 2026-10-20: T1 de P1 de 09:30 a 10:00 hora local (de 12:30 a 13:00 UTC), `reservado`; T2 de P1 de 10:30 a 11:00 (de 13:30 a 14:00 UTC), `confirmado`; T3 de P1 de 11:45 a 12:15 (de 14:45 a 15:15 UTC), `reservado`; T4 de P1 de 11:00 a 11:30 (de 14:00 a 14:30 UTC), `cancelado`; T5 de P1 de 10:00 a 10:30 (de 13:00 a 13:30 UTC), `ausente`; T6 de P2 de 10:30 a 11:00 (de 13:30 a 14:00 UTC), `reservado`; T7 de P1 de 12:00 a 12:30 (de 15:00 a 15:30 UTC), `reservado`.

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
