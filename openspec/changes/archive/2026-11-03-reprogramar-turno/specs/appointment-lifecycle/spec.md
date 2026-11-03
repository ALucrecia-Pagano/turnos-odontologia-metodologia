## ADDED Requirements

### Requirement: Operación de reprogramar un turno
El dominio SHALL ofrecer `reschedule_appointment`, que revalida el turno nuevo con `validate_new_appointment` y devuelve `ValidationResult`. El turno aceptado SHALL conservar su id y volver a `reservado`. El inicio es obligatorio; profesional, sillón y duración son opcionales (`None` conserva el valor actual). El paciente y la prestación MUST NOT cambiar. Sin duración, SHALL usarse la duración real del turno (fin menos inicio), no la de la prestación.

#### Scenario: Reprogramar válido conserva id y vuelve a reservado
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Ok` y el turno devuelto tiene el mismo id que T1, va de 11:00 a 11:30 hora local (14:00–14:30 UTC) y está en estado `reservado`

#### Scenario: Desde confirmado vuelve a reservado
- **GIVEN** T1 confirmado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Ok` con el turno en estado `reservado` (ya no `confirmado`)

#### Scenario: No choca consigo mismo en su mismo intervalo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 10:00 hora local (13:00 UTC), mismo P1/S1 y duración 30 (su propio intervalo), con T1 incluido en la agenda recibida
- **THEN** el resultado es `Ok`, sin `PROFESSIONAL_OVERLAP` ni `CHAIR_OVERLAP`

#### Scenario: No choca consigo mismo al solapar su intervalo viejo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local, con T1 incluido en la agenda recibida
- **WHEN** se reprograma T1 a las 10:15 hora local (13:15 UTC), mismo P1/S1 y duración 30 (solapa su intervalo viejo 10:00–10:30)
- **THEN** el resultado es `Ok`, sin `PROFESSIONAL_OVERLAP` ni `CHAIR_OVERLAP`

#### Scenario: Cambia solo el profesional y no choca por sillón consigo mismo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local en S1, sin turnos de P2 en S1 a esa hora, recepción U2 y now 09:00 local, con T1 incluido en la agenda recibida
- **WHEN** se reprograma T1 a las 10:00 hora local (13:00 UTC) cambiando el profesional a P2 y conservando S1 y duración 30
- **THEN** el resultado es `Ok`, sin `CHAIR_OVERLAP` contra T1 (el propio queda excluido) y con profesional P2

#### Scenario: Conserva la duración real si no se indica
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local (duración efectiva 30) con una prestación de default 45, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) sin indicar duración, conservando P1/S1
- **THEN** el resultado es `Ok` con un turno de 11:00 a 11:30 hora local (14:00–14:30 UTC), no de 11:00 a 11:45

#### Scenario: Cambia la duración indicada
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local (duración efectiva 30), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) con duración 60, conservando P1/S1
- **THEN** el resultado es `Ok` con un turno de 11:00 a 12:00 hora local (14:00–15:00 UTC)

#### Scenario: El original no cambia al reprogramar
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado es `Ok` y el T1 original conserva su inicio 13:00 UTC, su fin 13:30 UTC y su estado `reservado`

### Requirement: Auto-exclusión del propio turno al revalidar
El dominio SHALL excluir de la lista de turnos existentes, antes de revalidar, al turno que se reprograma, comparando por id. La corrección de la revalidación MUST NOT depender de que el llamador haya filtrado la lista: el llamador pasa la agenda completa, incluido el turno a reprogramar, y el dominio lo excluye. La exclusión por id es universal y cubre el caso en que solo cambia el profesional y el propio turno seguiría coincidiendo por sillón.

#### Scenario: El dominio excluye al propio aunque el llamador lo incluya
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local, recepción U2, now 09:00 local, y la agenda recibida incluye a T1
- **WHEN** se reprograma T1 a las 10:15 hora local (13:15 UTC), mismo P1/S1 y duración 30
- **THEN** el resultado es `Ok`, porque T1 se excluye antes de evaluar los solapamientos

### Requirement: Precondición de estado de reprogramar
Reprogramar SHALL aceptarse solo desde `reservado` o `confirmado`. Los tres estados terminales (`atendido`, `ausente`, `cancelado`) SHALL rechazarse con una sola violación `INVALID_TRANSITION` y un mensaje dedicado de reprogramar que nombra al profesional, la fecha y el intervalo local del turno, y el estado terminal. La reprogramación no forma parte de la tabla ordinaria RN-TU-02 y MUST NOT usar `can_transition` como precondición.

#### Scenario: Desde cada estado terminal
- **GIVEN** T1 en `atendido` (primer caso), `ausente` (segundo) o `cancelado` (tercero), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** cada resultado es `Rejected` con una sola violación `INVALID_TRANSITION` cuyo mensaje es, respectivamente, "El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no se puede reprogramar porque está en estado terminal "atendido".", "...terminal "ausente"." y "...terminal "cancelado"."

#### Scenario: El turno terminal no se altera
- **GIVEN** T1 atendido y recepción U2, now 09:00 local
- **WHEN** se intenta reprogramar T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado es `Rejected` con `INVALID_TRANSITION` y T1 conserva su estado `atendido` y su intervalo 13:00–13:30 UTC

### Requirement: Permisos de reprogramar
El odontólogo MUST NOT reprogramar ningún turno, ni propio ni ajeno; el intento SHALL devolver una sola violación `FORBIDDEN_OPERATION` con mensaje dedicado de reprogramar. Recepción y administración SHALL poder reprogramar todos los turnos. La política específica RBAC de KB 03 (fila "reprogramar / cancelar") prevalece sobre el disparador de Flujo 2. La propiedad se compara por `professional_id`, nunca `user_id`.

#### Scenario: Odontólogo propio y ajeno no reprograman
- **GIVEN** Laura U1/P1 y T1 propio reservado (primer caso), y Laura U1/P1 con T2 reservado de P2 (segundo caso), now 09:00 local
- **WHEN** Laura intenta reprogramar cada turno a las 11:00 hora local (14:00 UTC)
- **THEN** cada resultado es `Rejected` con una sola violación `FORBIDDEN_OPERATION` cuyo mensaje es "No tiene permiso para reprogramar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden reprogramar turnos." en el primer caso, y "No tiene permiso para reprogramar el turno de Dra. Inés Molina del 20/10/2026 de 11:00 a 11:30 (hora local): solo recepción y administración pueden reprogramar turnos." en el segundo

#### Scenario: Recepción y administración reprograman
- **GIVEN** T1 reservado y now 09:00 local
- **WHEN** recepción U2 (primer caso) y administración U3 (segundo caso) reprograman T1 a las 11:00 hora local (14:00 UTC)
- **THEN** ambos resultados son `Ok` con el turno en `reservado` y ningún permiso depende de `professional_id`

### Requirement: Orden de evaluación de reprogramar
Tras los errores de contrato, el dominio SHALL evaluar permiso, estado y turno nuevo, en ese orden, con cortocircuito. Un actor no autorizado devuelve solo `FORBIDDEN_OPERATION`; un estado terminal, solo `INVALID_TRANSITION`; en otro caso devuelve las violaciones del turno nuevo en el orden RN-AG-12.

#### Scenario: El permiso corta y oculta el resto
- **GIVEN** Laura U1/P1, T1 propio atendido y now 10:30 local (posterior al inicio)
- **WHEN** Laura intenta reprogramar T1 a las 09:00 hora local (12:00 UTC), un slot en el pasado
- **THEN** el resultado contiene solo `FORBIDDEN_OPERATION`, sin `INVALID_TRANSITION` ni `IN_THE_PAST`

#### Scenario: El estado corta y oculta los conflictos del slot
- **GIVEN** T1 cancelado, recepción U2, now 09:00 local y un slot destino 11:00 que chocaría con otro turno
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado contiene solo `INVALID_TRANSITION`, sin `PROFESSIONAL_OVERLAP`

### Requirement: Reprogramar revalida todas las reglas del turno nuevo
Al reprogramar, el dominio SHALL revalidar todas las RN-AG del turno nuevo, incluida la actividad del paciente y de la prestación aunque no cambien. Un profesional o sillón inexistente SHALL dar `UNKNOWN_REFERENCE`, e inactivo, `INACTIVE_REFERENCE`. El pasado SHALL dar `IN_THE_PAST` con el verbo de reprogramar. Las demás violaciones reutilizan los códigos y textos vigentes del alta.

#### Scenario: Choca con otro turno del mismo profesional
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local, un turno T3 de P1 en S2 de 11:00 a 11:30 hora local (14:00–14:30 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` cuyo mensaje es exactamente "Dra. Laura Quiroga ya tiene un turno de 11:00 a 11:30 (hora local) que se superpone (turno {id de T3})."

#### Scenario: Choca con otro turno del mismo sillón
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local en S1, un turno T4 de P2 en S1 de 11:00 a 11:30 hora local (14:00–14:30 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `CHAIR_OVERLAP` cuyo mensaje es exactamente "Sillón 1 está ocupado de 11:00 a 11:30 (hora local) por un turno que se superpone (turno {id de T4})."

#### Scenario: Fuera de horario
- **GIVEN** T1 reservado, P1 atiende el martes solo de 09:00 a 11:00 hora local (sin tramo a las 11:00), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `OUTSIDE_WORKING_HOURS`, con el mismo texto exacto que al dar un turno nuevo en ese slot

#### Scenario: Bloqueado
- **GIVEN** T1 reservado, un bloqueo BL1 de P1 de 11:00 a 12:00 hora local (14:00–15:00 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `BLOCKED_TIME` con el id de BL1, con el mismo texto exacto que al dar un turno nuevo en ese slot

#### Scenario: Al pasado con verbo de reprogramar
- **GIVEN** T1 reservado y now 10:00:00 hora local (13:00 UTC)
- **WHEN** se reprograma T1 a las 09:00 hora local (12:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `IN_THE_PAST` cuyo mensaje es exactamente "El inicio del turno (20/10/2026 09:00, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden reprogramar turnos en el pasado."

#### Scenario: Profesional nuevo inexistente
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) cambiando el profesional a P3, que no existe
- **THEN** el resultado es `Rejected` con una violación `UNKNOWN_REFERENCE` de tipo `PROFESSIONAL`

#### Scenario: Prestación inactiva al reprogramar
- **GIVEN** T1 reservado y la prestación de T1 está inactiva, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y sin indicar duración
- **THEN** el resultado es `Rejected` con una violación `INACTIVE_REFERENCE` de tipo `SERVICE`

### Requirement: Errores de contrato e inmutabilidad de reprogramar
Un `now` sin zona (*naive*) en el contexto MUST rechazarse con `ValueError` al construir el contexto, como en el alta. Los errores de negocio MUST devolverse como `Violation`, nunca como excepción. El turno original MUST permanecer sin cambios ante cualquier rechazo. La operación SHALL ser síncrona, totalmente tipada y sin `Any`, reloj global, generación de ids, I/O, Pydantic, FastAPI, SQLAlchemy ni Redis.

#### Scenario: now naive en el contexto
- **GIVEN** T1 reservado y recepción U2
- **WHEN** se reprograma T1 con un contexto cuyo `now` es 2026-10-20T09:00:00 sin zona
- **THEN** la construcción del contexto lanza `ValueError` que indica que `now` necesita zona

#### Scenario: El original no cambia ante un rechazo de slot
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y un turno T3 de P1 en S2 de 11:00 a 11:30 hora local, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) y choca con T3
- **THEN** el resultado es `Rejected` y T1 conserva su inicio 13:00 UTC, su fin 13:30 UTC y su estado `reservado`

### Requirement: Pureza y compatibilidad de reprogramar
La operación de reprogramar SHALL reutilizar `validate_new_appointment` sin duplicar reglas RN-AG. SHALL pasar las guardias vigentes sin modificar la guardia de dependencias ni su allowlist. No SHALL añadirse historial (C-12), códigos `ViolationCode` nuevos ni cambios en `OCCUPYING_STATUSES`. El alta de turnos y el catálogo MUST conservar mensajes y contratos; en particular, el mensaje de `IN_THE_PAST` del alta conserva exactamente "no se pueden dar turnos en el pasado".

#### Scenario: El alta conserva el mensaje del pasado
- **GIVEN** un alta de turno con inicio en el pasado, now 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC)
- **THEN** el mensaje de `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado." (sin "reprogramar")

#### Scenario: Sin códigos nuevos ni cambios de ocupación
- **WHEN** se inspecciona `ViolationCode` y `OCCUPYING_STATUSES`
- **THEN** no se agregan códigos de violación y el conjunto de ocupación sigue exactamente `reservado`, `confirmado`, `atendido`
