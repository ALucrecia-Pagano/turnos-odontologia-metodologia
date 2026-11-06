## ADDED Requirements

### Requirement: Consulta del horario de atención
La API SHALL exponer GET /api/professionals/{id}/working-hours, autorizado con WORKING_HOURS READ. Responde 200 con los tramos del profesional ordenados por weekday y por inicio, cada uno como { weekday, start, end } con horas locales "HH:MM". El odontólogo solo puede consultar el horario de su propio profesional.

#### Scenario: Recepción consulta el horario de un profesional
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con el tramo del lunes (weekday 1) de 540 a 780 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/working-hours
- **THEN** el status es 200
- **AND** el cuerpo es una lista con { "weekday": 1, "start": "09:00", "end": "13:00" }

#### Scenario: La odontóloga consulta su propio horario
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/working-hours
- **THEN** el status es 200

#### Scenario: La odontóloga consulta el horario de otro profesional
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000002/working-hours
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para leer horarios."

#### Scenario: Consulta del horario sin token
- **GIVEN** una solicitud sin header Authorization
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/working-hours
- **THEN** el status es 401

#### Scenario: Consulta del horario de un profesional inexistente
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000999/working-hours
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Profesional no encontrado." }

### Requirement: Reemplazo del horario de atención
La API SHALL exponer PUT /api/professionals/{id}/working-hours, autorizado con WORKING_HOURS UPDATE, que reemplaza la semana completa del profesional con los tramos enviados. Una lista vacía deja al profesional sin horario. Responde 200 con { workingHours, appointmentsOutsideHours }. Un profesional inactivo también puede cambiar su horario.

#### Scenario: El administrador reemplaza el horario de un profesional
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000002/working-hours con [{ "weekday": 2, "start": "08:00", "end": "12:00" }]
- **THEN** el status es 200
- **AND** workingHours es [{ "weekday": 2, "start": "08:00", "end": "12:00" }]
- **AND** una consulta GET posterior devuelve ese único tramo

#### Scenario: La odontóloga reemplaza su propio horario
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 1, "start": "09:00", "end": "13:00" }]
- **THEN** el status es 200

#### Scenario: La odontóloga reemplaza el horario de otro profesional
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000002/working-hours con [{ "weekday": 1, "start": "09:00", "end": "13:00" }]
- **THEN** el status es 403
- **AND** el horario del profesional 00000000-0000-0000-0000-000000000002 no cambia

#### Scenario: Recepción reemplaza un horario
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 1, "start": "09:00", "end": "13:00" }]
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para actualizar horarios."

#### Scenario: Reemplazo con lista vacía deja al profesional sin horario
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con el tramo del lunes de 540 a 780 y un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con []
- **THEN** el status es 200
- **AND** workingHours es una lista vacía

#### Scenario: Reemplazo con tramos solapados responde 422
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con el tramo del lunes de 540 a 780 y un usuario administrador autenticado
- **WHEN** invoca PUT con [{ "weekday": 2, "start": "09:00", "end": "13:00" }, { "weekday": 2, "start": "12:00", "end": "16:00" }]
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación OVERLAPPING_WORKING_HOURS
- **AND** la profesional conserva su tramo del lunes de 540 a 780

#### Scenario: Reemplazo con un tramo de inicio posterior al fin responde 422
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 1, "start": "13:00", "end": "09:00" }]
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_WORKING_HOURS

#### Scenario: Reemplazo con una hora mal formada responde 400
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 1, "start": "25:00", "end": "26:00" }]
- **THEN** el status es 400

#### Scenario: Reemplazo con fin a las 24:00 se acepta
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 5, "start": "20:00", "end": "24:00" }]
- **THEN** el status es 200
- **AND** workingHours es [{ "weekday": 5, "start": "20:00", "end": "24:00" }]

#### Scenario: Reemplazo del horario de un profesional inexistente
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000999/working-hours con []
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Profesional no encontrado." }

#### Scenario: Reemplazo del horario de un profesional inactivo
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 desactivada y un usuario administrador autenticado
- **WHEN** invoca PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con [{ "weekday": 1, "start": "09:00", "end": "13:00" }]
- **THEN** el status es 200

### Requirement: Turnos que quedan fuera del horario nuevo
La respuesta de PUT /api/professionals/{id}/working-hours SHALL incluir en appointmentsOutsideHours los turnos del profesional que ocupan agenda, empiezan entre el momento actual y 90 días después, y quedan fuera del horario nuevo. Cada uno trae id, patientId, patientName, chairId, startAt, endAt y status. Esos turnos no se cancelan ni se mueven.

#### Scenario: Un turno que queda fuera del horario nuevo se informa sin cancelarlo
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con el tramo del lunes de 540 a 780 y un turno reservado de la paciente Ana Pérez el lunes futuro L de 10:00 a 10:30 local (L definido en D13)
- **WHEN** el administrador invoca PUT con [{ "weekday": 1, "start": "15:00", "end": "19:00" }]
- **THEN** el status es 200
- **AND** appointmentsOutsideHours tiene ese turno, con patientName "Ana Pérez" y status "reservado"
- **AND** el turno sigue en estado reservado en la base

#### Scenario: Un turno que sigue dentro del horario nuevo no se informa
- **GIVEN** el mismo turno reservado del lunes futuro L de 10:00 a 10:30 local
- **WHEN** el administrador invoca PUT con [{ "weekday": 1, "start": "09:00", "end": "12:00" }]
- **THEN** el status es 200
- **AND** appointmentsOutsideHours es una lista vacía

#### Scenario: Un turno cancelado fuera del horario nuevo no se informa
- **GIVEN** el mismo turno del lunes futuro L, cancelado
- **WHEN** el administrador invoca PUT con [{ "weekday": 1, "start": "15:00", "end": "19:00" }]
- **THEN** el status es 200
- **AND** appointmentsOutsideHours es una lista vacía

### Requirement: Listado de bloqueos
La API SHALL exponer GET /api/professionals/{id}/blocks, autorizado con BLOCK READ, que responde 200 con los bloqueos del profesional ordenados por startAt. Admite los filtros opcionales from y to (ISO 8601 con zona horaria), que devuelven solo los bloqueos que se solapan con ese rango. El odontólogo solo puede listar los bloqueos de su propio profesional.

#### Scenario: Recepción lista los bloqueos de un profesional
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con dos bloqueos y un usuario recepcion autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/blocks
- **THEN** el status es 200
- **AND** la lista tiene los dos bloqueos ordenados por startAt, con startAt y endAt en UTC

#### Scenario: La odontóloga lista sus propios bloqueos
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/blocks
- **THEN** el status es 200

#### Scenario: La odontóloga lista los bloqueos de otro profesional
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000002/blocks
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para leer bloqueos."

#### Scenario: El listado con from y to devuelve solo los bloqueos que se solapan
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con un bloqueo de 2026-12-07T12:00:00Z a 2026-12-07T16:00:00Z y otro de 2026-12-21T12:00:00Z a 2026-12-21T16:00:00Z, y un usuario administrador autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/blocks con from 2026-12-07T00:00:00-03:00 y to 2026-12-14T00:00:00-03:00
- **THEN** el status es 200
- **AND** la lista tiene solo el bloqueo del 2026-12-07

#### Scenario: El listado con un from sin zona horaria responde 400
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000001/blocks con from 2026-12-07T00:00:00
- **THEN** el status es 400

#### Scenario: El listado de bloqueos de un profesional inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/professionals/00000000-0000-0000-0000-000000000999/blocks
- **THEN** el status es 404

### Requirement: Alta de bloqueos
La API SHALL exponer POST /api/professionals/{id}/blocks, autorizado con BLOCK CREATE, con startAt y endAt en ISO 8601 con zona horaria obligatoria y reason opcional. El id lo genera el servidor. Responde 201 con { block, affectedAppointments }. El odontólogo solo puede crear bloqueos para su propio profesional.

#### Scenario: La odontóloga crea un bloqueo propio sin turnos afectados
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001, sin turnos el lunes futuro L
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000001/blocks con startAt el lunes L a las 09:00 -03:00, endAt el lunes L a las 13:00 -03:00 y reason "Congreso"
- **THEN** el status es 201
- **AND** block tiene un id generado, reason "Congreso", y startAt y endAt en UTC
- **AND** affectedAppointments es una lista vacía

#### Scenario: El administrador crea un bloqueo para cualquier profesional
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000002/blocks con un intervalo válido del lunes futuro L
- **THEN** el status es 201

#### Scenario: La odontóloga crea un bloqueo para otro profesional
- **GIVEN** el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000002/blocks con un intervalo válido del lunes futuro L
- **THEN** el status es 403
- **AND** no se guarda ningún bloqueo

#### Scenario: Recepción crea un bloqueo
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000001/blocks con un intervalo válido del lunes futuro L
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para crear bloqueos."

#### Scenario: Un bloqueo con inicio igual al fin responde 422
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000001/blocks con startAt y endAt iguales
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_BLOCK
- **AND** no se guarda ningún bloqueo

#### Scenario: Un bloqueo sin zona horaria responde 400
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000001/blocks con startAt 2026-12-07T09:00:00 y endAt 2026-12-07T13:00:00, sin zona horaria
- **THEN** el status es 400

#### Scenario: Un bloqueo para un profesional inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000999/blocks con un intervalo válido
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Profesional no encontrado." }

### Requirement: Turnos afectados por un bloqueo nuevo
La respuesta de POST /api/professionals/{id}/blocks SHALL incluir en affectedAppointments los turnos del profesional que ocupan agenda y se solapan con el bloqueo, con el mismo resumen que appointmentsOutsideHours. El bloqueo se guarda igual y esos turnos no se cancelan ni se mueven (RN-DI-04).

#### Scenario: Un bloqueo que pisa un turno reservado lo informa sin cancelarlo
- **GIVEN** un turno reservado de la paciente Ana Pérez con la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L de 10:00 a 10:30 local, y un usuario administrador autenticado
- **WHEN** invoca POST /api/professionals/00000000-0000-0000-0000-000000000001/blocks del lunes L de 09:00 a 13:00 local
- **THEN** el status es 201
- **AND** affectedAppointments tiene ese turno, con patientName "Ana Pérez" y status "reservado"
- **AND** el turno sigue en estado reservado en la base

#### Scenario: Un bloqueo que pisa un turno cancelado no lo informa
- **GIVEN** el mismo turno del lunes futuro L, cancelado
- **WHEN** el administrador invoca POST del lunes L de 09:00 a 13:00 local
- **THEN** el status es 201
- **AND** affectedAppointments es una lista vacía

### Requirement: Eliminación de bloqueos
La API SHALL exponer DELETE /api/blocks/{block_id}, autorizado con BLOCK DELETE, que borra el bloqueo y responde 200 con el bloqueo borrado. Un bloqueo inexistente responde 404. El odontólogo solo puede borrar los bloqueos de su propio profesional. Borrar el bloqueo libera ese horario para dar turnos.

#### Scenario: La odontóloga borra su propio bloqueo
- **GIVEN** un bloqueo de la profesional 00000000-0000-0000-0000-000000000001 y el usuario odontologo vinculado a ella
- **WHEN** invoca DELETE /api/blocks/{block_id}
- **THEN** el status es 200
- **AND** el cuerpo es el bloqueo borrado
- **AND** un GET posterior del listado de bloqueos ya no lo incluye

#### Scenario: El administrador borra el bloqueo de cualquier profesional
- **GIVEN** un bloqueo del profesional 00000000-0000-0000-0000-000000000002 y un usuario administrador autenticado
- **WHEN** invoca DELETE /api/blocks/{block_id}
- **THEN** el status es 200

#### Scenario: La odontóloga borra el bloqueo de otro profesional
- **GIVEN** un bloqueo del profesional 00000000-0000-0000-0000-000000000002 y el usuario odontologo vinculado a la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca DELETE /api/blocks/{block_id}
- **THEN** el status es 403
- **AND** el bloqueo sigue guardado

#### Scenario: Recepción borra un bloqueo
- **GIVEN** un bloqueo de la profesional 00000000-0000-0000-0000-000000000001 y un usuario recepcion autenticado
- **WHEN** invoca DELETE /api/blocks/{block_id}
- **THEN** el status es 403
- **AND** el bloqueo sigue guardado

#### Scenario: Borrar un bloqueo inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca DELETE /api/blocks/00000000-0000-0000-0000-000000000b99
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Bloqueo no encontrado." }

#### Scenario: Borrar un bloqueo libera el horario
- **GIVEN** un bloqueo de la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L de 09:00 a 13:00 local
- **WHEN** el administrador lo borra con DELETE /api/blocks/{block_id}
- **THEN** book_appointment acepta un turno de esa profesional el lunes L de 10:00 a 10:30 local

### Requirement: Bloqueos y altas de turnos serializados
POST /api/professionals/{id}/blocks y PUT /api/professionals/{id}/working-hours SHALL tomar SELECT ... FOR UPDATE sobre la fila del profesional antes de escribir y de calcular los turnos afectados, en el mismo orden que el alta de turnos de C-17. Así, un turno nuevo ve el bloqueo, o el bloqueo informa el turno nuevo.

#### Scenario: Un bloqueo que espera a un alta informa el turno nuevo
- **GIVEN** la conexión A que ejecuta book_appointment para la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L de 10:00 a 10:30 local, con auto_commit False, reteniendo el bloqueo de fila
- **WHEN** la conexión B crea un bloqueo de la misma profesional del lunes L de 09:00 a 13:00 local y queda esperando (verificado consultando pg_locks), y después A hace commit
- **THEN** B guarda el bloqueo
- **AND** los turnos afectados que devuelve B incluyen el turno de A

#### Scenario: Un alta que espera a un bloqueo recibe BLOCKED_TIME
- **GIVEN** la conexión A que crea un bloqueo de la profesional 00000000-0000-0000-0000-000000000001 del lunes futuro L de 09:00 a 13:00 local, con auto_commit False, reteniendo el bloqueo de fila
- **WHEN** la conexión B ejecuta book_appointment para esa profesional el lunes L de 10:00 a 10:30 local y queda esperando (verificado consultando pg_locks), y después A hace commit
- **THEN** B recibe Rejected con una violación BLOCKED_TIME
- **AND** no se guarda ningún turno de B
