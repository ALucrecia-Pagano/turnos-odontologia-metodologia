# appointment-scheduling Specification

## Purpose
Reglas del dominio para dar un turno nuevo en la agenda del consultorio. El turno se acepta solo si el pedido es válido y no choca con la agenda. El pedido es válido si el paciente existe, si el profesional, el sillón y la prestación existen y están activos, y si la duración es un múltiplo de 5 minutos entre 5 y 480. No choca con la agenda si no se solapa con otro turno activo del mismo profesional ni del mismo sillón. Si se rechaza, el resultado explica cada problema: primero los del pedido y, solo si el pedido es válido, los conflictos de agenda.

Convenciones de los escenarios: todos los instantes son del 2026-10-20 en UTC (por ejemplo, "13:00" es `2026-10-20T13:00:00+00:00`). P1 y P2 son profesionales; S1, S2 y S3, sillones. Salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos, y los turnos existentes están en estado `reservado`. Turno existente "A" = profesional P1, sillón S1, de 13:00 a 13:30.

## Requirements

### Requirement: Alta de un turno válido
Si el paciente existe, el profesional, el sillón y la prestación existen y están activos, la duración es válida y el profesional y el sillón están libres en el intervalo pedido, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador. En todos los escenarios, salvo que se diga otra cosa, el paciente, los profesionales, los sillones y la prestación del pedido existen y están activos.

#### Scenario: Turno válido con profesional y sillón libres
- **GIVEN** una prestación con duración por defecto de 30 minutos y ningún turno existente para P1 ni para S1
- **WHEN** se pide un turno con el id `T-NUEVO`, para P1 en S1, a las 13:00 y sin duración explícita
- **THEN** el resultado es `Ok`
- **AND** el turno devuelto tiene el id `T-NUEVO`, va de 13:00 a 13:30, está en estado `reservado` y conserva el paciente, el profesional, el sillón y la prestación pedidos

#### Scenario: Turno válido con otros turnos que no chocan
- **GIVEN** el turno existente A
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 15:00
- **THEN** el resultado es `Ok` con el turno de 15:00 a 15:30 en estado `reservado`

### Requirement: Duración del turno
La duración efectiva SHALL ser la duración explícita, si el llamador la informa, o en caso contrario la duración por defecto de la prestación (RN-AG-07). El fin del turno SHALL ser `inicio + duración efectiva` (US-001 CA-2 y CA-3).

#### Scenario: Duración por defecto de la prestación
- **GIVEN** una prestación con duración por defecto de 45 minutos
- **WHEN** se pide un turno a las 13:00 sin duración explícita
- **THEN** el turno devuelto termina a las 13:45

#### Scenario: Duración explícita que reemplaza la de la prestación
- **GIVEN** una prestación con duración por defecto de 45 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 20 minutos
- **THEN** el turno devuelto termina a las 13:20

#### Scenario: Duración explícita válida con una prestación de duración no positiva
- **GIVEN** una prestación con duración por defecto de 0 minutos
- **WHEN** se pide un turno a las 13:00 con duración explícita de 30 minutos
- **THEN** el resultado es `Ok` con un turno que termina a las 13:30, porque se evalúa solo la duración efectiva

### Requirement: Intervalos semiabiertos y turnos consecutivos
Todo turno SHALL ocupar el intervalo semiabierto `[inicio, fin)`. Dos intervalos se solapan solo si cada uno empieza antes de que termine el otro, así que un turno que empieza exactamente cuando termina otro, o que termina exactamente cuando empieza otro, MUST ser válido aunque compartan profesional y sillón (US-001 CA-4, DD-07).

#### Scenario: Turno que empieza exactamente cuando termina otro
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno de 30 minutos para P1 en S1 que empieza a las 13:30
- **THEN** el resultado es `Ok`, sin violaciones

#### Scenario: Turno que termina exactamente cuando empieza otro
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno de 30 minutos para P1 en S1 que empieza a las 12:30
- **THEN** el resultado es `Ok`, sin violaciones

### Requirement: Rechazo por solapamiento de profesional
Si el intervalo del turno nuevo se solapa con el de un turno existente del mismo profesional que ocupa agenda, el dominio SHALL rechazarlo con una violación `PROFESSIONAL_OVERLAP` que identifica ese turno. No hay opción de forzar el turno (RN-AG-01, RN-AG-03, US-002).

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

### Requirement: Rechazo por solapamiento de sillón
Si el intervalo del turno nuevo se solapa con el de un turno existente del mismo sillón que ocupa agenda, el dominio SHALL rechazarlo con una violación `CHAIR_OVERLAP` que identifica ese turno, sea cual sea el profesional (RN-AG-02, US-003).

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

### Requirement: Estados que ocupan agenda
Solo los turnos existentes en estado `reservado`, `confirmado` o `atendido` SHALL contar para los solapamientos. Los turnos `cancelado` y `ausente` MUST NOT generar violaciones (RN-AG-08, SU-07, US-002 CA-5).

#### Scenario: Turno cancelado no bloquea
- **GIVEN** un turno existente de P1 en S1 de 13:00 a 13:30 en estado `cancelado`
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 13:30
- **THEN** el resultado es `Ok`

#### Scenario: Turno ausente no bloquea
- **GIVEN** un turno existente de P1 en S1 de 13:00 a 13:30 en estado `ausente`
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 13:30
- **THEN** el resultado es `Ok`

#### Scenario: Turnos confirmados y atendidos sí bloquean
- **GIVEN** un turno existente de P1 en S1 de 13:00 a 13:30, en estado `confirmado` (primer caso) o `atendido` (segundo caso)
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 13:30
- **THEN** en ambos casos el resultado es `Rejected` con `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` sobre ese turno

### Requirement: El dominio filtra los turnos que recibe
El dominio SHALL decidir por sí mismo qué turnos existentes son relevantes (mismo profesional para `PROFESSIONAL_OVERLAP`, mismo sillón para `CHAIR_OVERLAP`, estado que ocupa agenda). La corrección del resultado MUST NOT depender de que el llamador haya filtrado la lista.

#### Scenario: Lista con turnos de otros profesionales y otros sillones
- **GIVEN** una lista de turnos existentes que solapan con 13:00–13:30 pero son de P2 en S2, más un turno cancelado de P1 en S1 a la misma hora
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 13:30
- **THEN** el resultado es `Ok`

### Requirement: Todas las violaciones, en orden estable
El dominio SHALL evaluar el pedido en dos grupos. Primero la validez del pedido: referencias y duración, informadas todas juntas, en este orden: paciente, profesional, sillón, prestación y, al final, duración (RN-AG-12). Si hay alguna, el dominio SHALL devolverlas sin evaluar los conflictos de agenda: un resultado MUST NOT mezclar violaciones de validez con violaciones de solapamiento. Si el pedido es válido, el dominio SHALL devolver todas las violaciones de solapamiento, no solo la primera (DD-08): una por cada turno con el que choca. Primero van todas las `PROFESSIONAL_OVERLAP` y después todas las `CHAIR_OVERLAP` (RN-AG-12). Dentro de cada grupo se ordenan por el inicio del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo.

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

### Requirement: Validez de la duración
La duración efectiva SHALL ser mayor que cero, múltiplo de 5 minutos y de 480 minutos como máximo (RN-AG-09, RN-DI-05 en la parte de la duración, SU-02, US-007 CA-1). Si no cumple alguna de esas condiciones, el dominio SHALL rechazar el turno con **una sola** violación `INVALID_DURATION`, sin id de turno en conflicto, aunque rompa más de una condición. Si la prestación no existe y no hay duración explícita, no hay duración efectiva y la duración MUST NOT validarse. Con una duración inválida no existe un intervalo válido, así que los solapamientos MUST NOT evaluarse.

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
Cada violación SHALL tener un código estable, un mensaje no vacío en español y, en las de solapamiento, el id del turno con el que choca; el mensaje MUST incluir ese id. Las violaciones de referencias SHALL indicar el tipo de referencia que falló (`reference_kind`: `PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`) y su mensaje MUST incluir el id de esa referencia; las demás violaciones no llevan tipo de referencia. El mensaje de `INVALID_DURATION` MUST mencionar la duración recibida y cada condición incumplida. El texto completo, con nombres y rango horario local, queda para C-08. Las violaciones de negocio se devuelven en el resultado y nunca como excepción.

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

### Requirement: Instantes con zona horaria y normalizados a UTC
Todo instante del modelo (inicio y fin de los turnos, inicio pedido) SHALL tener zona horaria. Un instante sin zona (*naive*) es un error de programación del llamador y MUST rechazarse con una excepción `ValueError` al construir el valor, no como violación de negocio. Un instante con zona distinta de UTC MUST normalizarse a UTC conservando el mismo momento.

#### Scenario: Inicio sin zona horaria
- **WHEN** se construye un pedido de turno o un turno con un inicio `2026-10-20T13:00:00` sin zona (primer caso) o con un fin sin zona (segundo caso)
- **THEN** la construcción falla con `ValueError` cuyo mensaje indica que el instante necesita zona horaria

#### Scenario: Inicio en hora de Buenos Aires
- **GIVEN** una prestación con duración por defecto de 30 minutos
- **WHEN** se pide un turno con inicio `2026-10-20T10:00:00-03:00`
- **THEN** el turno devuelto tiene inicio `2026-10-20T13:00:00+00:00` y fin `2026-10-20T13:30:00+00:00`, ambos en UTC

#### Scenario: Turno existente en otra zona que choca
- **GIVEN** un turno existente de P1 en S1 cargado con inicio `2026-10-20T10:00:00-03:00` y fin `2026-10-20T10:30:00-03:00`
- **WHEN** se pide un turno para P1 en S2 de 13:15 a 13:45 UTC
- **THEN** el resultado es `Rejected` con `PROFESSIONAL_OVERLAP` sobre ese turno

### Requirement: Referencias existentes y activas
El paciente del turno MUST existir, y el profesional, el sillón y la prestación MUST existir y estar activos (RN-AG-11, US-007 CA-2). Si una referencia no existe, el dominio SHALL rechazar el turno con `UNKNOWN_REFERENCE`; si existe pero está inactiva, con `INACTIVE_REFERENCE`. Se informa una violación por cada referencia que falla. El paciente no tiene estado activo: solo puede dar `UNKNOWN_REFERENCE`.

#### Scenario: Referencia inexistente
- **GIVEN** que no existe el paciente (primer caso), el profesional P1 (segundo caso), el sillón S1 (tercer caso) o la prestación (cuarto caso) del pedido, y el resto de las referencias existen y están activas
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 13:00
- **THEN** en cada caso el resultado es `Rejected` con exactamente una violación `UNKNOWN_REFERENCE`, cuyo tipo es `PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE` respectivamente

#### Scenario: Referencia inactiva
- **GIVEN** que está inactivo el profesional P1 (primer caso), el sillón S1 (segundo caso) o la prestación (tercer caso) del pedido, y el resto de las referencias existen y están activas
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 13:00
- **THEN** en cada caso el resultado es `Rejected` con exactamente una violación `INACTIVE_REFERENCE`, cuyo tipo es `PROFESSIONAL`, `CHAIR` o `SERVICE` respectivamente

#### Scenario: Todas las referencias existen y están activas
- **GIVEN** que el paciente existe y el profesional P1, el sillón S1 y la prestación existen y están activos, sin turnos existentes
- **WHEN** se pide un turno de 30 minutos para P1 en S1 a las 13:00
- **THEN** el resultado es `Ok`, sin violaciones de referencias
