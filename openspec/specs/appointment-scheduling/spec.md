# appointment-scheduling Specification

## Purpose
Reglas del dominio para dar un turno nuevo en la agenda del consultorio. El turno se acepta solo si no se solapa con otro turno activo del mismo profesional ni del mismo sillón y si su duración es válida. Si se rechaza, el resultado explica cada conflicto.

Convenciones de los escenarios: todos los instantes son del 2026-10-20 en UTC (por ejemplo, "13:00" es `2026-10-20T13:00:00+00:00`). P1 y P2 son profesionales; S1, S2 y S3, sillones. Salvo que se diga otra cosa, los turnos existentes están en estado `reservado`. Turno existente "A" = profesional P1, sillón S1, de 13:00 a 13:30.

## Requirements

### Requirement: Alta de un turno válido
Si el profesional y el sillón están libres en el intervalo pedido y la duración es válida, el dominio SHALL devolver un resultado `Ok` con el turno nuevo: el id, el paciente, el profesional, el sillón y la prestación que pidió el llamador, inicio y fin en UTC, y estado `reservado` (RN-TU-01). El dominio no genera el id: lo recibe del llamador.

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
El dominio SHALL devolver todas las violaciones de solapamiento, no solo la primera (DD-08): una por cada turno con el que choca. Primero van todas las `PROFESSIONAL_OVERLAP` y después todas las `CHAIR_OVERLAP` (RN-AG-12). Dentro de cada grupo se ordenan por el inicio del turno con el que chocan. Un mismo turno existente puede producir una violación de cada tipo.

#### Scenario: Varios conflictos de ambos tipos
- **GIVEN** un turno B de P1 en S2 de 13:30 a 14:00, un turno C de P1 en S3 de 13:00 a 13:30 y un turno D de P2 en S1 de 13:45 a 14:15
- **WHEN** se pide un turno para P1 en S1 de 13:00 a 14:00
- **THEN** el resultado es `Rejected` con exactamente tres violaciones, en este orden: `PROFESSIONAL_OVERLAP` con el turno C, `PROFESSIONAL_OVERLAP` con el turno B y `CHAIR_OVERLAP` con el turno D

#### Scenario: Orden independiente del orden de la lista recibida
- **GIVEN** los mismos turnos B, C y D del escenario anterior, recibidos en orden inverso
- **WHEN** se pide el mismo turno
- **THEN** las violaciones se devuelven en el mismo orden: C, B (profesional) y D (sillón)

### Requirement: Rechazo de duración no positiva
Si la duración efectiva del turno es menor o igual a cero minutos, el dominio SHALL rechazarlo con una violación `INVALID_DURATION`, sin id de turno en conflicto (RN-AG-09 parcial, US-007 CA-1 parcial). En ese caso no existe un intervalo válido, así que los solapamientos MUST NOT evaluarse: es la única excepción a "devolver todas las violaciones".

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

#### Scenario: Duración inválida en un horario ocupado
- **GIVEN** el turno existente A (P1, S1, de 13:00 a 13:30)
- **WHEN** se pide un turno para P1 en S1 a las 13:00 con duración explícita de 0 minutos
- **THEN** el resultado es `Rejected` con una sola violación, `INVALID_DURATION`, sin violaciones de solapamiento

### Requirement: Contenido de cada violación
Cada violación SHALL tener un código estable, un mensaje no vacío en español y, en las de solapamiento, el id del turno con el que choca; el mensaje MUST incluir ese id. El texto completo, con nombres y rango horario local, queda para C-08. Las violaciones de negocio se devuelven en el resultado y nunca como excepción.

#### Scenario: Mensajes de las violaciones de solapamiento
- **GIVEN** el turno existente A
- **WHEN** se pide un turno para P1 en S1 de 13:15 a 13:45
- **THEN** cada una de las dos violaciones tiene un mensaje en español que contiene el id del turno A
- **AND** el mensaje de `PROFESSIONAL_OVERLAP` menciona al profesional y el de `CHAIR_OVERLAP` menciona al sillón

#### Scenario: Mensaje de duración inválida
- **WHEN** se pide un turno con duración explícita de -15 minutos
- **THEN** la violación `INVALID_DURATION` no tiene id de turno en conflicto y su mensaje en español menciona la duración recibida (-15)

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
