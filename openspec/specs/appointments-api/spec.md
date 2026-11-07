# appointments-api Specification

## Purpose
API REST para dar turnos. Expone POST /api/appointments, autorizado para recepción y administrador, que construye el pedido con el now UTC y la zona de la aplicación, delega la validación en el dominio y persiste el turno y su entrada de historial en una sola transacción. La duración es la informada en durationMin o, si falta, la de la prestación. Los conflictos de agenda responden 409, las referencias inválidas y los turnos en el pasado responden 422 y la entrada malformada responde 400; los rechazos de dominio conservan todas las violaciones y no dejan filas. De dos altas simultáneas sobre el mismo hueco, una responde 201 y la otra 409.

## Requirements

### Requirement: Alta autorizada de turnos
La API SHALL exponer POST /api/appointments autorizado con APPOINTMENT CREATE. Recepción y administrador responden 201 con el turno creado. El odontólogo responde 403 con FORBIDDEN_OPERATION y el mensaje "No tiene permiso para dar turnos.". Sin token responde 401. El id, el estado reservado y changedBy los genera el servidor, y la entrada de historial queda persistida con fromStatus nulo.

#### Scenario: Recepción da un turno válido
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 "Dra. Laura Quiroga" con horario del lunes de 09:00 a 13:00, la paciente 00000000-0000-0000-0000-0000000000c1 "Ana Pérez", el sillón 00000000-0000-0000-0000-0000000000b1 "Sillón 1", la prestación 00000000-0000-0000-0000-0000000000d4 "Control" y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments con patientId 00000000-0000-0000-0000-0000000000c1, professionalId 00000000-0000-0000-0000-000000000001, chairId 00000000-0000-0000-0000-0000000000b1, serviceId 00000000-0000-0000-0000-0000000000d4 y startAt el lunes futuro L a las 10:00 -03:00, sin durationMin
- **THEN** el status es 201
- **AND** el cuerpo tiene un id generado, status "reservado" y endAt el lunes futuro L a las 10:30 -03:00
- **AND** en la base queda el turno y su entrada de historial con fromStatus nulo, toStatus "reservado" y changedBy 00000000-0000-0000-0000-0000000000e2

#### Scenario: El administrador da un turno válido
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa" con horario del lunes de 09:00 a 13:00, la paciente 00000000-0000-0000-0000-0000000000c2 "Bruno Acosta", el sillón 00000000-0000-0000-0000-0000000000b2 "Sillón 2", la prestación 00000000-0000-0000-0000-0000000000d4 "Control" y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments con patientId 00000000-0000-0000-0000-0000000000c2, professionalId 00000000-0000-0000-0000-000000000002, chairId 00000000-0000-0000-0000-0000000000b2, serviceId 00000000-0000-0000-0000-0000000000d4 y startAt el lunes futuro L a las 11:00 -03:00
- **THEN** el status es 201
- **AND** el cuerpo tiene status "reservado" y professionalId 00000000-0000-0000-0000-000000000002

#### Scenario: El odontólogo intenta dar un turno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un cuerpo válido para esa profesional el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para dar turnos."
- **AND** no se guarda ningún turno

#### Scenario: Alta sin token
- **GIVEN** una solicitud sin header Authorization y un cuerpo válido para la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments
- **THEN** el status es 401
- **AND** no se guarda ningún turno

### Requirement: Duración y validación del cuerpo
El cuerpo SHALL aceptar patientId, professionalId, chairId, serviceId, startAt y durationMin opcional, con extra="forbid". startAt exige zona horaria. Si viene durationMin se usa ese valor; si falta se usa la duración de la prestación. Un startAt sin zona horaria responde 400 y un campo extra responde 400, sin llegar al dominio.

#### Scenario: durationMin explícito se usa en lugar de la duración de la prestación
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, la prestación 00000000-0000-0000-0000-0000000000d4 "Control" de 30 minutos y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 10:00 -03:00 con durationMin 45
- **THEN** el status es 201
- **AND** endAt es el lunes futuro L a las 10:45 -03:00

#### Scenario: Sin durationMin se usa la duración de la prestación
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, la prestación 00000000-0000-0000-0000-0000000000d2 "Extracción" de 60 minutos y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 10:00 -03:00 sin durationMin
- **THEN** el status es 201
- **AND** endAt es el lunes futuro L a las 11:00 -03:00

#### Scenario: startAt sin zona horaria responde 400
- **GIVEN** un usuario recepcion autenticado y un cuerpo válido para la profesional 00000000-0000-0000-0000-000000000001
- **WHEN** invoca POST /api/appointments con startAt el lunes futuro L a las 10:00:00, sin offset de zona horaria
- **THEN** el status es 400
- **AND** no se guarda ningún turno

#### Scenario: Un campo extra responde 400
- **GIVEN** un usuario recepcion autenticado y un cuerpo válido para la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments agregando el campo status con valor "reservado"
- **THEN** el status es 400
- **AND** no se guarda ningún turno

### Requirement: Conflictos de agenda
La API SHALL rechazar el alta cuando el turno se solapa con otro del mismo profesional, cuando se solapa con otro del mismo sillón, cuando cae fuera del horario de atención y cuando cae dentro de un bloqueo. El status es 409 y el cuerpo conserva todas las violaciones del dominio con sus códigos PROFESSIONAL_OVERLAP, CHAIR_OVERLAP, OUTSIDE_WORKING_HOURS y BLOCKED_TIME.

#### Scenario: Choque de profesional
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments para la misma profesional el lunes futuro L a las 10:00 -03:00 en el sillón 00000000-0000-0000-0000-0000000000b2
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación PROFESSIONAL_OVERLAP
- **AND** no se guarda el turno nuevo

#### Scenario: Choque de sillón
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments para la profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L a las 10:00 -03:00 en el sillón 00000000-0000-0000-0000-0000000000b1
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación CHAIR_OVERLAP
- **AND** no se guarda el turno nuevo

#### Scenario: Choque de profesional y sillón
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments para la misma profesional el lunes futuro L a las 10:00 -03:00 en el mismo sillón 00000000-0000-0000-0000-0000000000b1
- **THEN** el status es 409
- **AND** el cuerpo tiene las violaciones PROFESSIONAL_OVERLAP y CHAIR_OVERLAP
- **AND** no se guarda el turno nuevo

#### Scenario: Fuera de horario
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 18:00 -03:00 para esa profesional
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación OUTSIDE_WORKING_HOURS
- **AND** no se guarda el turno nuevo

#### Scenario: En un bloqueo
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un bloqueo de esa profesional el lunes futuro L de 09:00 a 13:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 10:00 -03:00 para esa profesional
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación BLOCKED_TIME
- **AND** no se guarda el turno nuevo

### Requirement: Referencias y reglas de validez
La API SHALL rechazar con 422 las altas con referencias inexistentes, referencias inactivas y turnos en el pasado. Cada referencia inexistente produce una violación UNKNOWN_REFERENCE con referenceKind, una referencia inactiva produce INACTIVE_REFERENCE y un turno pasado produce IN_THE_PAST. Se devuelven todas las violaciones juntas.

#### Scenario: En el pasado
- **GIVEN** un usuario recepcion autenticado y un cuerpo válido para la profesional 00000000-0000-0000-0000-000000000001 en un múltiplo de 5 minutos de ayer a las 10:00 local
- **WHEN** invoca POST /api/appointments
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación IN_THE_PAST
- **AND** no se guarda el turno nuevo

#### Scenario: Paciente inexistente
- **GIVEN** un usuario recepcion autenticado y un cuerpo válido para la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L a las 10:00 -03:00 con patientId 00000000-0000-0000-0000-0000000000c9
- **WHEN** invoca POST /api/appointments
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación UNKNOWN_REFERENCE con referenceKind "PATIENT"
- **AND** no se guarda el turno nuevo

#### Scenario: Dos referencias inexistentes
- **GIVEN** un usuario recepcion autenticado y un cuerpo el lunes futuro L a las 10:00 -03:00 con patientId 00000000-0000-0000-0000-0000000000c9 y chairId 00000000-0000-0000-0000-0000000000b9
- **WHEN** invoca POST /api/appointments para la profesional 00000000-0000-0000-0000-000000000001
- **THEN** el status es 422
- **AND** el cuerpo tiene dos violaciones UNKNOWN_REFERENCE, una con referenceKind "PATIENT" y otra con referenceKind "CHAIR"
- **AND** no se guarda el turno nuevo

#### Scenario: Profesional inactivo
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa" desactivada, con horario del lunes de 09:00 a 13:00, y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 10:00 -03:00 para esa profesional
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INACTIVE_REFERENCE con referenceKind "PROFESSIONAL"
- **AND** no se guarda el turno nuevo

### Requirement: Atomicidad y cableado del alta
La ruta SHALL construir NewAppointmentRequest con now UTC y la zona APP_TIMEZONE, invocar book_appointment y persistir turno e historial en una sola transacción. Un rechazo no deja filas. Dos requests en el mismo hueco devuelven un 201 y un 409, con un solo turno y una sola entrada de historial; la concurrencia real se prueba en C-17.

#### Scenario: Un rechazo no deja turno ni historial
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un bloqueo de esa profesional el lunes futuro L de 09:00 a 13:00 -03:00, sin turnos previos, y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments el lunes futuro L a las 10:00 -03:00 y recibe BLOCKED_TIME
- **THEN** la base no tiene turnos para esa profesional
- **AND** la base no tiene entradas de historial para esa profesional

#### Scenario: Dos altas simultáneas del mismo hueco por HTTP
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, dos solicitudes preparadas con el mismo cuerpo para el lunes futuro L a las 10:00 -03:00 y una barrera que las libera juntas
- **WHEN** se envían las dos solicitudes POST /api/appointments
- **THEN** una respuesta tiene status 201 y la otra tiene status 409
- **AND** la base tiene un solo turno para ese hueco
- **AND** la base tiene una sola entrada de historial para ese turno

### Requirement: Documentación OpenAPI del alta
La operación POST /api/appointments SHALL documentar en OpenAPI los status 201, 400, 401, 403, 409 y 422. La respuesta 201 usa el esquema del turno en camelCase y las respuestas de rechazo usan el esquema de violaciones.

#### Scenario: Swagger documenta los status del alta
- **GIVEN** la aplicación con la ruta POST /api/appointments registrada
- **WHEN** se consulta GET /api/openapi.json
- **THEN** la operación POST /api/appointments documenta los status 201, 400, 401, 403, 409 y 422
- **AND** la respuesta 201 referencia el esquema del turno

### Requirement: Cancelación autorizada de turnos
La API SHALL exponer POST /api/appointments/{id}/cancel autorizado con APPOINTMENT CANCEL. Recepción y administración cancelan turnos reservados o confirmados y reciben 200 con el turno en estado cancelado. El odontólogo recibe 403 FORBIDDEN_OPERATION con "No tiene permiso para cancelar turnos.". Un turno inexistente responde 404 con "Turno no encontrado." y una transición inválida responde 422 INVALID_TRANSITION. El cuerpo no acepta note.

#### Scenario: Recepción cancela un turno reservado
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 "Dra. Laura Quiroga" con horario del lunes de 09:00 a 13:00, la paciente 00000000-0000-0000-0000-0000000000c1 "Ana Pérez", el sillón 00000000-0000-0000-0000-0000000000b1, la prestación 00000000-0000-0000-0000-0000000000d4 "Control", un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/cancel con el id de ese turno
- **THEN** el status es 200
- **AND** el cuerpo tiene status "cancelado" y el mismo id
- **AND** en la base queda una entrada de historial nueva de "reservado" a "cancelado" con changedBy 00000000-0000-0000-0000-0000000000e2

#### Scenario: El administrador cancela un turno confirmado
- **GIVEN** un turno confirmado de la paciente 00000000-0000-0000-0000-0000000000c2 "Bruno Acosta" con la profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa" el lunes futuro L a las 11:00 -03:00 y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/{id}/cancel
- **THEN** el status es 200
- **AND** el cuerpo tiene status "cancelado"
- **AND** en la base queda una entrada de historial nueva de "confirmado" a "cancelado" con changedBy 00000000-0000-0000-0000-0000000000e1

#### Scenario: Cancelar un turno atendido responde 422
- **GIVEN** un turno atendido insertado directamente en la base de test con inicio dos horas antes del reloj real, redondeado a cinco minutos, la profesional 00000000-0000-0000-0000-000000000001, la paciente 00000000-0000-0000-0000-0000000000c1, el sillón 00000000-0000-0000-0000-0000000000b1, la prestación 00000000-0000-0000-0000-0000000000d4 y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/{id}/cancel
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_TRANSITION
- **AND** no se agrega ninguna entrada de historial

#### Scenario: Cancelar un turno ya cancelado responde 422
- **GIVEN** un turno cancelado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/cancel
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_TRANSITION
- **AND** no se agrega ninguna entrada de historial

#### Scenario: Cancelar un turno inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/00000000-0000-0000-0000-000000000999/cancel
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Turno no encontrado." }

#### Scenario: El odontólogo intenta cancelar un turno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno reservado de esa profesional el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments/{id}/cancel
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para cancelar turnos."
- **AND** el turno sigue "reservado" en la base

### Requirement: Reprogramación autorizada de turnos
La API SHALL exponer POST /api/appointments/{id}/reschedule autorizado con APPOINTMENT RESCHEDULE. Recepción y administración reciben 200 con el turno en estado reservado; el odontólogo recibe 403. El cuerpo exige startAt con zona y acepta professionalId, chairId y durationMin opcionales; sin durationMin se conserva la duración real. Choques, bloqueos y fuera de horario responden 409; reglas de validez y transiciones terminales 422; entrada malformada 400; turno inexistente 404.

#### Scenario: Reprogramar solo el inicio conserva la duración real
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:45 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00, sin professionalId, chairId ni durationMin
- **THEN** el status es 200
- **AND** el cuerpo tiene startAt el lunes futuro L a las 11:00 -03:00, endAt el lunes futuro L a las 11:45 -03:00 y status "reservado"
- **AND** conserva professionalId 00000000-0000-0000-0000-000000000001 y chairId 00000000-0000-0000-0000-0000000000b1

#### Scenario: Reprogramar con profesional, sillón y duración explícitos
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00, professionalId 00000000-0000-0000-0000-000000000002, chairId 00000000-0000-0000-0000-0000000000b2 y durationMin 60
- **THEN** el status es 200
- **AND** el cuerpo tiene professionalId 00000000-0000-0000-0000-000000000002, chairId 00000000-0000-0000-0000-0000000000b2, endAt el lunes futuro L a las 12:00 -03:00 y status "reservado"

#### Scenario: Choque de profesional al reprogramar
- **GIVEN** un turno reservado de la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00, un segundo turno reservado de la profesional 00000000-0000-0000-0000-000000000002 en el sillón 00000000-0000-0000-0000-0000000000b2 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule sobre el segundo turno con startAt el lunes futuro L a las 10:00 -03:00 y professionalId 00000000-0000-0000-0000-000000000001
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación PROFESSIONAL_OVERLAP
- **AND** el segundo turno conserva su profesional y su inicio en la base

#### Scenario: Choque de sillón al reprogramar
- **GIVEN** un turno reservado de la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b1 el lunes futuro L de 10:00 a 10:30 -03:00, un segundo turno reservado de la profesional 00000000-0000-0000-0000-000000000002 en el sillón 00000000-0000-0000-0000-0000000000b2 el lunes futuro L de 10:00 a 10:30 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule sobre el segundo turno con startAt el lunes futuro L a las 10:00 -03:00 y chairId 00000000-0000-0000-0000-0000000000b1
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación CHAIR_OVERLAP
- **AND** el segundo turno conserva su sillón y su inicio en la base

#### Scenario: Reprogramar dentro de un bloqueo responde 409
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00, un bloqueo de esa profesional el lunes futuro L de 09:00 a 13:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación BLOCKED_TIME
- **AND** el turno conserva su inicio original en la base

#### Scenario: Reprogramar fuera de horario responde 409
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 18:00 -03:00
- **THEN** el status es 409
- **AND** el cuerpo tiene una violación OUTSIDE_WORKING_HOURS
- **AND** el turno conserva su inicio original en la base

#### Scenario: Reprogramar al pasado responde 422
- **GIVEN** un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt ayer a las 10:00 -03:00, en un múltiplo de 5 minutos
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación IN_THE_PAST
- **AND** el turno conserva su inicio original en la base

#### Scenario: startAt sin zona horaria responde 400
- **GIVEN** un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00:00, sin offset de zona horaria
- **THEN** el status es 400
- **AND** el turno conserva su inicio original en la base

#### Scenario: Un campo extra en la reprogramación responde 400
- **GIVEN** un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00 y el campo extra status con valor "cancelado"
- **THEN** el status es 400
- **AND** el turno conserva su estado reservado en la base

#### Scenario: Reprogramar un turno inexistente responde 404
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/00000000-0000-0000-0000-000000000999/reschedule con startAt el lunes futuro L a las 11:00 -03:00
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Turno no encontrado." }

#### Scenario: El odontólogo intenta reprogramar un turno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno reservado de esa profesional el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para reprogramar turnos."
- **AND** el turno conserva su inicio original en la base

#### Scenario: Reprogramar un turno en estado terminal responde 422
- **GIVEN** un turno cancelado el lunes futuro L a las 10:00 -03:00 y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/{id}/reschedule con startAt el lunes futuro L a las 11:00 -03:00
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_TRANSITION
- **AND** el turno sigue "cancelado" en la base

### Requirement: Cambio de estado autorizado
La API SHALL exponer POST /api/appointments/{id}/status autorizado con APPOINTMENT CHANGE_STATUS. El cuerpo acepta solo confirmado, atendido y ausente; cancelado y reservado responden 400. Las transiciones válidas responden 200. Un estado no alcanzable responde 422 INVALID_TRANSITION y hacerlo antes del inicio responde 422 STATUS_CHANGE_TOO_EARLY. El odontólogo solo opera turnos propios; el dominio responde 403. Un turno inexistente responde 404.

#### Scenario: Confirmar un turno reservado
- **GIVEN** un turno reservado de la paciente 00000000-0000-0000-0000-0000000000c1 con la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "confirmado"
- **THEN** el status es 200
- **AND** el cuerpo tiene status "confirmado"
- **AND** en la base queda una entrada de historial nueva de "reservado" a "confirmado"

#### Scenario: Marcar atendido un turno confirmado con inicio pasado
- **GIVEN** un turno confirmado insertado directamente en la base de test con inicio dos horas antes del reloj real, redondeado a cinco minutos, la profesional 00000000-0000-0000-0000-000000000001, la paciente 00000000-0000-0000-0000-0000000000c1, el sillón 00000000-0000-0000-0000-0000000000b1, la prestación 00000000-0000-0000-0000-0000000000d4 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "atendido"
- **THEN** el status es 200
- **AND** el cuerpo tiene status "atendido"
- **AND** en la base queda una entrada de historial nueva de "confirmado" a "atendido"

#### Scenario: Marcar ausente un turno confirmado con inicio pasado
- **GIVEN** un turno confirmado insertado directamente en la base de test con inicio dos horas antes del reloj real, redondeado a cinco minutos, la profesional 00000000-0000-0000-0000-000000000002, la paciente 00000000-0000-0000-0000-0000000000c2, el sillón 00000000-0000-0000-0000-0000000000b2, la prestación 00000000-0000-0000-0000-0000000000d4 y un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "ausente"
- **THEN** el status es 200
- **AND** el cuerpo tiene status "ausente"
- **AND** en la base queda una entrada de historial nueva de "confirmado" a "ausente"

#### Scenario: Marcar atendido antes del inicio responde 422
- **GIVEN** un turno confirmado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "atendido"
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación STATUS_CHANGE_TOO_EARLY
- **AND** el turno sigue "confirmado" en la base

#### Scenario: Doble transición secuencial deja una sola entrada nueva
- **GIVEN** un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca dos veces seguidas POST /api/appointments/{id}/status con toStatus "confirmado"
- **THEN** la primera respuesta tiene status 200 y la segunda tiene status 422 con INVALID_TRANSITION
- **AND** el turno queda "confirmado" en la base
- **AND** queda una sola entrada de historial nueva de "reservado" a "confirmado"

#### Scenario: Confirmar un turno cancelado responde 422
- **GIVEN** un turno cancelado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "confirmado"
- **THEN** el status es 422
- **AND** el cuerpo tiene una violación INVALID_TRANSITION
- **AND** el turno sigue "cancelado" en la base

#### Scenario: toStatus "cancelado" responde 400
- **GIVEN** un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "cancelado"
- **THEN** el status es 400
- **AND** el turno sigue "reservado" en la base

#### Scenario: toStatus "reservado" responde 400
- **GIVEN** un turno confirmado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "reservado"
- **THEN** el status es 400
- **AND** el turno sigue "confirmado" en la base

#### Scenario: Cambiar el estado de un turno inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca POST /api/appointments/00000000-0000-0000-0000-000000000999/status con toStatus "confirmado"
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Turno no encontrado." }

#### Scenario: El odontólogo cambia el estado de un turno ajeno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno reservado de la profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca POST /api/appointments/{id}/status con toStatus "confirmado"
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para cambiar el estado del turno de Dr. Martín Sosa del lunes futuro L de 10:00 a 10:30 (hora local): un odontólogo solo puede cambiar el estado de sus propios turnos."
- **AND** el turno sigue "reservado" en la base

### Requirement: Historial de turnos
La API SHALL exponer GET /api/appointments/{id}/history autorizado con APPOINTMENT_HISTORY READ. Responde 200 con las entradas ordenadas de forma ascendente por changedAt e id. Cada entrada incluye siempre from, to, changedBy, changedByName, changedAt y reschedule; reschedule es null salvo en una reprogramación, donde es un objeto plano de ocho campos. La entrada del alta tiene from null. Una reprogramación siempre registra to "reservado". Un turno inexistente responde 404.

#### Scenario: Historial ascendente con el alta y changedByName
- **GIVEN** un turno creado el lunes futuro L a las 10:00 -03:00 y luego confirmado, y un usuario recepcion autenticado
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 200
- **AND** el cuerpo tiene dos entradas en orden ascendente
- **AND** la primera entrada tiene from null, to "reservado", changedByName "Recepción Demo" y reschedule null
- **AND** la segunda entrada tiene from "reservado", to "confirmado", changedByName "Recepción Demo" y reschedule null

#### Scenario: Entrada de reprogramación con to reservado y detalle plano
- **GIVEN** un turno confirmado el lunes futuro L a las 10:00 -03:00 reprogramado al lunes futuro L a las 11:00 -03:00 por recepción, y un usuario administrador autenticado
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 200
- **AND** la última entrada tiene from "confirmado", to "reservado" y changedAt posterior a las entradas anteriores
- **AND** reschedule es un objeto con previousStartAt, previousEndAt, newStartAt, newEndAt, previousProfessionalId, newProfessionalId, previousChairId y newChairId

#### Scenario: Historial de un turno inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/appointments/00000000-0000-0000-0000-000000000999/history
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Turno no encontrado." }

### Requirement: Permisos por propiedad del historial
La API SHALL aplicar propiedad al historial: el odontólogo solo lee el historial de los turnos de su propio profesional; recepción y administración leen el de todos. Si un odontólogo pide el historial de un turno ajeno, responde 403 FORBIDDEN_OPERATION con "No tiene permiso para leer el historial de turnos.". La comparación usa el professionalId del turno y el helper ensure_own_professional, sin exponer datos del turno en el rechazo.

#### Scenario: El odontólogo lee el historial de su propio turno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno de esa profesional el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 200
- **AND** el cuerpo es una lista con al menos la entrada del alta

#### Scenario: El odontólogo lee el historial de un turno ajeno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno de la profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 403
- **AND** el cuerpo tiene una violación FORBIDDEN_OPERATION con el mensaje "No tiene permiso para leer el historial de turnos."
- **AND** el cuerpo no expone datos del turno

#### Scenario: Recepción lee el historial de un turno ajeno
- **GIVEN** un usuario recepcion autenticado y un turno de la profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 200
- **AND** el cuerpo es una lista con al menos la entrada del alta

#### Scenario: El administrador lee el historial de un turno ajeno
- **GIVEN** un usuario administrador autenticado y un turno de la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L a las 10:00 -03:00
- **WHEN** invoca GET /api/appointments/{id}/history
- **THEN** el status es 200
- **AND** el cuerpo es una lista con al menos la entrada del alta

### Requirement: Documentación OpenAPI del ciclo de vida
Las cuatro operaciones del ciclo de vida SHALL documentarse en OpenAPI con 400, 401, 403 y 404. Cancelación, reprogramación y cambio de estado documentan 422; la reprogramación documenta además 409. El historial no documenta 409 ni 422 de dominio. Las respuestas de rechazo usan el esquema de violaciones y la respuesta exitosa usa el esquema del turno.

#### Scenario: Swagger documenta los status del ciclo de vida
- **GIVEN** la aplicación con las rutas POST /cancel, POST /reschedule, POST /status y GET /history registradas
- **WHEN** se consulta GET /api/openapi.json
- **THEN** las cuatro operaciones documentan los status 400, 401, 403 y 404
- **AND** POST /cancel, POST /reschedule y POST /status documentan 422
- **AND** POST /reschedule documenta 409
- **AND** GET /history no documenta 409 ni 422
