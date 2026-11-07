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
