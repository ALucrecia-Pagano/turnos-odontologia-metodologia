## ADDED Requirements

### Requirement: Parámetros y validación de la agenda
La API SHALL exponer GET /api/agenda autorizado con APPOINTMENT READ_AGENDA. `from` y `to` son fechas locales obligatorias en formato AAAA-MM-DD, con `to` inclusivo y un máximo de 31 días; `professionalId` y `chairId` son UUID opcionales. Un parámetro faltante, malformado o desconocido, o un rango inválido, responde 400; sin token responde 401.

#### Scenario: Falta el parámetro from responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda?to=2026-11-09
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "from", type "missing" y message "Falta este dato."

#### Scenario: Falta el parámetro to responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda?from=2026-11-09
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "to", type "missing" y message "Falta este dato."

#### Scenario: Una fecha con formato inválido responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda?from=09-11-2026&to=2026-11-09
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "from", type "invalid_date_format" y message "La fecha debe tener formato AAAA-MM-DD."

#### Scenario: Un to anterior al from responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from el martes L+1 y to el lunes L
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con type "invalid_range_order" y message "La fecha final no puede ser anterior a la inicial."

#### Scenario: Un rango de más de 31 días responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from el lunes futuro L y to el día L+31
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con type "invalid_range_length" y message "El rango no puede superar los 31 días."

#### Scenario: Un professionalId malformado responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y professionalId "no-es-un-uuid"
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "professionalId", type "uuid_parsing" y message "Dato inválido."

#### Scenario: Un chairId malformado responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y chairId "no-es-un-uuid"
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "chairId", type "uuid_parsing" y message "Dato inválido."

#### Scenario: Un parámetro de query desconocido responde 400
- **GIVEN** un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y el parámetro desconocido status "cancelado"
- **THEN** el status es 400
- **AND** el cuerpo tiene un error con field "status", type "extra_forbidden" y message "Dato inválido."

#### Scenario: La agenda sin token responde 401
- **GIVEN** un cliente sin token de autenticación
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 401

### Requirement: Sobre de respuesta de la agenda
La API SHALL responder GET /api/agenda con un sobre `{ from, to, timezone, appointments, workingHours, blocks }`. `from` y `to` repiten las fechas pedidas, `timezone` es APP_TIMEZONE y `appointments` trae los turnos enriquecidos con nombres, `startAt`/`endAt` en UTC con `Z` y `status`. La respuesta no pagina ni filtra por estado.

#### Scenario: La agenda de un día devuelve el sobre completo
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 "Dra. Laura Quiroga" con horario del lunes de 09:00 a 13:00, la paciente 00000000-0000-0000-0000-0000000000c1 "Ana Pérez", el sillón 00000000-0000-0000-0000-0000000000b1 "Sillón 1", la prestación 00000000-0000-0000-0000-0000000000d4 "Control", un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** el cuerpo tiene from y to iguales al lunes futuro L y timezone "America/Argentina/Buenos_Aires"
- **AND** appointments tiene un turno con patientName "Ana Pérez", professionalName "Dra. Laura Quiroga", chairName "Sillón 1", serviceName "Control", startAt el lunes futuro L a las 13:00Z, endAt el lunes futuro L a las 13:30Z y status "reservado"

#### Scenario: La agenda de una semana devuelve los turnos del rango
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from el lunes futuro L y to el día L+6
- **THEN** el status es 200
- **AND** el cuerpo tiene from el lunes futuro L y to el día L+6
- **AND** appointments contiene el turno del lunes futuro L

#### Scenario: Un rango de ocho días cruza dos semanas
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 09:00 -03:00, otro turno reservado el lunes L+7 a las 09:00 -03:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from el lunes futuro L y to el lunes L+7
- **THEN** el status es 200
- **AND** appointments tiene los dos turnos ordenados por startAt

#### Scenario: Un rango de 31 días cruza meses
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 09:00 -03:00, otro turno reservado el día L+30 a las 09:00 -03:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from el lunes futuro L y to el día L+30
- **THEN** el status es 200
- **AND** appointments tiene los dos turnos

### Requirement: Filtros y visibilidad de la agenda
La API SHALL aceptar `professionalId` y `chairId` opcionales y combinables con AND. `professionalId` filtra appointments, workingHours y blocks; `chairId` filtra solo appointments. Un id inexistente no es 404: devuelve 200 con las listas filtradas vacías. Los tres roles leen toda la agenda sin comparación de propiedad.

#### Scenario: El filtro por profesional devuelve sus turnos
- **GIVEN** cuatro turnos reservados el lunes futuro L con la profesional 00000000-0000-0000-0000-000000000001 "Dra. Laura Quiroga" y el profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa": uno de la profesional a las 09:00 en el sillón 00000000-0000-0000-0000-0000000000b1, uno de la profesional a las 10:00 en el sillón 00000000-0000-0000-0000-0000000000b2, uno del profesional a las 09:00 en el sillón 00000000-0000-0000-0000-0000000000b2 y uno del profesional a las 10:00 en el sillón 00000000-0000-0000-0000-0000000000b1, y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y professionalId 00000000-0000-0000-0000-000000000001
- **THEN** el status es 200
- **AND** appointments tiene solo los dos turnos de la profesional 00000000-0000-0000-0000-000000000001

#### Scenario: El filtro por sillón devuelve sus turnos
- **GIVEN** los cuatro turnos del escenario anterior y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y chairId 00000000-0000-0000-0000-0000000000b1
- **THEN** el status es 200
- **AND** appointments tiene solo los dos turnos del sillón 00000000-0000-0000-0000-0000000000b1

#### Scenario: Los filtros de profesional y sillón se combinan
- **GIVEN** los cuatro turnos del escenario de filtro por profesional y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L, professionalId 00000000-0000-0000-0000-000000000001 y chairId 00000000-0000-0000-0000-0000000000b2
- **THEN** el status es 200
- **AND** appointments tiene solo el turno de la profesional 00000000-0000-0000-0000-000000000001 en el sillón 00000000-0000-0000-0000-0000000000b2

#### Scenario: Un professionalId inexistente devuelve listas vacías
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y professionalId 00000000-0000-0000-0000-000000000999
- **THEN** el status es 200
- **AND** appointments, workingHours y blocks son listas vacías

#### Scenario: Un chairId inexistente deja vacíos los turnos pero no los horarios ni los bloqueos
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00, un bloqueo de la profesional el lunes futuro L de 14:00 a 15:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y chairId 00000000-0000-0000-0000-000000000999
- **THEN** el status es 200
- **AND** appointments es una lista vacía
- **AND** workingHours y blocks no están vacías

#### Scenario: El chairId no filtra horarios ni bloqueos
- **GIVEN** las profesionales 00000000-0000-0000-0000-000000000001 y 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00, un bloqueo de la profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L de 14:00 a 15:00 -03:00 y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y chairId 00000000-0000-0000-0000-0000000000b1
- **THEN** el status es 200
- **AND** workingHours incluye el tramo del lunes de las dos profesionales
- **AND** blocks incluye el bloqueo de la profesional 00000000-0000-0000-0000-000000000002

#### Scenario: El odontólogo ve los turnos de otro profesional
- **GIVEN** el usuario odontologo autenticado vinculado a la profesional 00000000-0000-0000-0000-000000000001 y un turno reservado de la profesional 00000000-0000-0000-0000-000000000002 "Dr. Martín Sosa" en el sillón 00000000-0000-0000-0000-0000000000b2 el lunes futuro L a las 09:00 -03:00
- **WHEN** el usuario odontologo invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** appointments incluye el turno con professionalId 00000000-0000-0000-0000-000000000002 y professionalName "Dr. Martín Sosa"

### Requirement: Horarios de atención del rango
La API SHALL devolver la plantilla semanal de horarios en `workingHours`, con `professionalId`, `weekday` de 1 a 7 y `start`/`end` en HH:MM, admitiendo `24:00` como fin. La plantilla incluye a todos los profesionales o solo al filtrado por `professionalId`; `chairId` no la filtra.

#### Scenario: La plantilla semanal incluye a todos los profesionales
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00 y de 15:00 a 19:00, el profesional 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** workingHours incluye el tramo de la profesional 00000000-0000-0000-0000-000000000001 con weekday 1, start "09:00" y end "13:00"
- **AND** workingHours incluye el tramo de la profesional 00000000-0000-0000-0000-000000000001 con weekday 1, start "15:00" y end "19:00"
- **AND** workingHours incluye el tramo del profesional 00000000-0000-0000-0000-000000000002 con weekday 1, start "09:00" y end "13:00"

#### Scenario: El filtro por profesional también filtra los horarios
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 y el profesional 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y professionalId 00000000-0000-0000-0000-000000000002
- **THEN** el status es 200
- **AND** workingHours solo tiene tramos con professionalId 00000000-0000-0000-0000-000000000002

### Requirement: Bloqueos del rango
La API SHALL devolver en `blocks` los bloqueos que se solapan con el rango, con `id`, `professionalId`, `startAt` y `endAt` en UTC con `Z` y `reason`. Se incluyen los bloqueos que empiezan antes del rango o cruzan la medianoche; `professionalId` los filtra y `chairId` no.

#### Scenario: Un bloqueo dentro del rango se devuelve con su motivo
- **GIVEN** el profesional 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00, un bloqueo de ese profesional el lunes futuro L de 14:00 a 15:00 -03:00 con reason "Congreso" y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** blocks tiene un bloqueo con professionalId 00000000-0000-0000-0000-000000000002, startAt el lunes futuro L a las 17:00Z, endAt el lunes futuro L a las 18:00Z y reason "Congreso"

#### Scenario: Un bloqueo que empieza antes del rango se incluye
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un bloqueo de esa profesional desde el domingo L-1 a las 23:00 -03:00 hasta el lunes futuro L a las 01:00 -03:00 con reason "Guardia" y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** blocks incluye el bloqueo con reason "Guardia"

#### Scenario: El filtro por profesional también filtra los bloqueos
- **GIVEN** un bloqueo de la profesional 00000000-0000-0000-0000-000000000001 el lunes futuro L de 14:00 a 15:00 -03:00, un bloqueo del profesional 00000000-0000-0000-0000-000000000002 el lunes futuro L de 16:00 a 17:00 -03:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L y professionalId 00000000-0000-0000-0000-000000000001
- **THEN** el status es 200
- **AND** blocks solo tiene el bloqueo de la profesional 00000000-0000-0000-0000-000000000001

#### Scenario: Un bloqueo que cruza la medianoche aparece en los dos días
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00 y un bloqueo de esa profesional desde el lunes futuro L a las 23:00 -03:00 hasta el martes L+1 a las 01:00 -03:00 con reason "Guardia", y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200 y blocks incluye el bloqueo
- **WHEN** invoca GET /api/agenda con from y to el martes L+1
- **THEN** el status es 200 y blocks incluye el mismo bloqueo

### Requirement: Estados y orden de la agenda
La API SHALL incluir todos los estados del turno, cancelado incluido, con su `status`, sin filtro de estado ni paginación. `appointments` se ordena por `startAt` y luego por `id`; `blocks` por `startAt` y luego por `id`; `workingHours` por `professionalId`, `weekday` y `start`.

#### Scenario: Los turnos cancelados se incluyen con su estado
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con horario del lunes de 09:00 a 13:00, un turno reservado el lunes futuro L a las 10:00 -03:00 cancelado por recepción y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** appointments incluye el turno cancelado con status "cancelado"

#### Scenario: Turnos, bloqueos y horarios salen en orden estable
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 y el profesional 00000000-0000-0000-0000-000000000002 con horario del lunes de 09:00 a 13:00, un turno a las 09:00 de la profesional en el sillón 00000000-0000-0000-0000-0000000000b1, un turno a las 09:30 del profesional en el sillón 00000000-0000-0000-0000-0000000000b2, un turno a las 10:00 de la profesional en el sillón 00000000-0000-0000-0000-0000000000b2, dos bloqueos a las 10:30 y 11:00 y un usuario administrador autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** appointments tiene los turnos en el orden 09:00, 09:30, 10:00
- **AND** blocks tiene los bloqueos en el orden 10:30, 11:00
- **AND** workingHours tiene primero los tramos de la profesional 00000000-0000-0000-0000-000000000001 y después los del profesional 00000000-0000-0000-0000-000000000002

### Requirement: Borde de medianoche de los turnos
La API SHALL tratar el rango como semiabierto `[from 00:00 local, to+1 00:00 local)`. Un turno que termina exactamente a las 00:00 pertenece al día en que empieza y no al siguiente; uno que empieza a las 00:00 pertenece a ese día. El servidor calcula las medianoches en APP_TIMEZONE.

#### Scenario: Un turno que termina a las 00:00 solo aparece en su día
- **GIVEN** la profesional 00000000-0000-0000-0000-000000000001 con el horario semanal reemplazado por PUT /api/professionals/00000000-0000-0000-0000-000000000001/working-hours con un tramo del lunes de 23:00 a "24:00" y un tramo del martes de "00:00" a 01:00, un turno creado por POST /api/appointments el lunes futuro L de 23:30 a 00:00 -03:00 con la prestación 00000000-0000-0000-0000-0000000000d4 "Control", otro turno creado el martes L+1 de 00:00 a 00:30 -03:00 con la misma prestación y un usuario recepcion autenticado
- **WHEN** invoca GET /api/agenda con from y to el lunes futuro L
- **THEN** el status es 200
- **AND** appointments incluye el turno que empieza el lunes futuro L a las 23:30 -03:00
- **AND** appointments no incluye el turno que empieza el martes L+1 a las 00:00 -03:00
- **WHEN** invoca GET /api/agenda con from y to el martes L+1
- **THEN** el status es 200
- **AND** appointments incluye el turno que empieza el martes L+1 a las 00:00 -03:00
- **AND** appointments no incluye el turno que empieza el lunes futuro L a las 23:30 -03:00
