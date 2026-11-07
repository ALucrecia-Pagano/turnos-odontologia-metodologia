## ADDED Requirements

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
