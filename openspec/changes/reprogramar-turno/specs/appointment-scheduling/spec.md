## MODIFIED Requirements

### Requirement: Mensaje de un turno en el pasado
El mensaje de `IN_THE_PAST` MUST decir, en hora local, el inicio del turno con fecha (`dd/mm/aaaa HH:MM`) y el momento actual con fecha y segundos (`dd/mm/aaaa HH:MM:SS`, sin microsegundos): "El inicio del turno ({inicio}, hora local) es anterior al momento actual ({now}, hora local): no se pueden {operación} en el pasado." La fecha es la del día local, no la de UTC. El mensaje no menciona al profesional ni al sillón. La operación (verbo del mensaje) SHALL recibirse como parámetro de `validate_new_appointment`, con valor por defecto "dar turnos", que la pasa a la regla del pasado (`check_not_in_the_past`): el alta no la pasa y conserva "dar turnos"; reprogramar le pasa "reprogramar turnos". El alta conserva exactamente el texto vigente "no se pueden dar turnos en el pasado"; reprogramar usa "no se pueden reprogramar turnos en el pasado". El valor por defecto "dar turnos" mantiene el alta y sus tests existentes idénticos.

#### Scenario: Mensaje de un turno en el pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado."
- **AND** la violación no tiene id de turno ni de bloqueo en conflicto ni tipo de referencia

#### Scenario: Mensaje con el momento actual en el mismo minuto que el inicio
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se pide un turno a las 10:00 hora local (13:00 UTC), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento actual (20/10/2026 10:00:30, hora local): no se pueden dar turnos en el pasado."

#### Scenario: Mensaje con la fecha local y no la de UTC
- **GIVEN** que `now` es el martes 2026-10-20 a las 23:30 hora local (02:30 UTC del miércoles 2026-10-21)
- **WHEN** se pide un turno el martes 2026-10-20 a las 23:00 hora local (02:00 UTC del 2026-10-21), sin duración explícita
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 23:00, hora local) es anterior al momento actual (20/10/2026 23:30:00, hora local): no se pueden dar turnos en el pasado."
- **AND** el mensaje no contiene la fecha ni las horas en UTC (`21/10/2026`, `02:00`, `02:30`)

#### Scenario: Mensaje al reprogramar un turno al pasado
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00 hora local (13:00 UTC)
- **WHEN** se reprograma un turno a las 09:00 hora local (12:00 UTC)
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:00, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden reprogramar turnos en el pasado."

#### Scenario: Mensaje al reprogramar con el momento actual en el mismo minuto que el inicio
- **GIVEN** que `now` es el martes 2026-10-20 a las 10:00:30 hora local (13:00:30 UTC)
- **WHEN** se reprograma un turno a las 10:00 hora local (13:00 UTC)
- **THEN** el mensaje de la violación `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento actual (20/10/2026 10:00:30, hora local): no se pueden reprogramar turnos en el pasado."
