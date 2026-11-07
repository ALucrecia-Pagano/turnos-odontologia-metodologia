## ADDED Requirements

### Requirement: Consulta de un turno por id
La API SHALL exponer GET /api/appointments/{id} autorizado con APPOINTMENT READ_AGENDA. Responde 200 con el turno enriquecido: patientName, professionalName, chairName, serviceName, startAt y endAt en UTC con `Z`, y status. Un turno inexistente responde 404 con "Turno no encontrado."; un UUID malformado responde 400 y la falta de token 401. El odontólogo lee cualquier turno.

#### Scenario: El detalle devuelve el turno enriquecido
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 "Dra. Laura Quiroga" con horario del lunes de 09:00 a 13:00, la paciente 00000000-0000-0000-0000-0000000000c1 "Ana Pérez", el sillón 00000000-0000-0000-0000-0000000000b1 "Sillón 1", la prestación 00000000-0000-0000-0000-0000000000d4 "Control", un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/appointments/{id}
- **THEN** el status es 200
- **AND** el cuerpo tiene patientName "Ana Pérez", professionalName "Dra. Laura Quiroga", chairName "Sillón 1", serviceName "Control", startAt el lunes futuro L a las 13:00Z, endAt el lunes futuro L a las 13:30Z y status "reservado"

#### Scenario: Un turno inexistente responde 404
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/appointments/00000000-0000-0000-0000-000000000999
- **THEN** el status es 404
- **AND** el cuerpo es { "code": "NOT_FOUND", "message": "Turno no encontrado." }

#### Scenario: Un id con UUID malformado responde 400
- **GIVEN** un usuario administrador autenticado
- **WHEN** invoca GET /api/appointments/no-es-un-uuid
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "id", type "uuid_parsing" y message "Dato inválido."

#### Scenario: El detalle sin token responde 401
- **GIVEN** un cliente sin token de autenticación
- **WHEN** invoca GET /api/appointments/00000000-0000-0000-0000-000000000999
- **THEN** el status es 401

#### Scenario: El odontólogo lee el detalle de un turno ajeno
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001, un turno reservado del profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa" en el sillón 00000000-0000-0000-0000-0000000000b2 el lunes futuro L a las 09:00 -03:00
- **WHEN** el usuario odontologo invoca GET /api/appointments/{id}
- **THEN** el status es 200
- **AND** el cuerpo tiene professionalId 00000000-0000-0000-0000-000000000002 y professionalName "Dr. Martín Sosa"
