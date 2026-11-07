## ADDED Requirements

### Requirement: Turnos que quedan fuera de un horario de atención
El dominio SHALL ofrecer la función pura appointments_outside_working_hours(professional_id, appointments, working_hours, tz, now), que devuelve los turnos de ese profesional que quedarían fuera del horario indicado. Solo cuentan los turnos en un estado que ocupa agenda (OCCUPYING_STATUSES) y con inicio mayor o igual a now. Reutiliza check_working_hours, no modifica los turnos y los devuelve ordenados por inicio y por id.

#### Scenario: Turno futuro fuera del horario nuevo se lista
- **GIVEN** el turno T1 reservado de la profesional 00000000-0000-0000-0000-000000000001 el lunes 2026-12-07 de 13:00:00Z a 13:30:00Z (10:00 a 10:30 local) y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con el horario de esa profesional del lunes (weekday=1) de 900 a 1140 (15:00 a 19:00 local)
- **THEN** el resultado es una lista con T1
- **AND** T1 conserva su estado reservado

#### Scenario: Turno dentro del horario nuevo no se lista
- **GIVEN** el mismo turno T1 y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con el horario del lunes de 540 a 780 (09:00 a 13:00 local)
- **THEN** el resultado es una lista vacía

#### Scenario: Turno cancelado fuera del horario no se lista
- **GIVEN** el turno T2 cancelado de la misma profesional el lunes 2026-12-07 de 13:00:00Z a 13:30:00Z y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con el horario del lunes de 900 a 1140
- **THEN** el resultado es una lista vacía

#### Scenario: Turno anterior al momento actual no se lista
- **GIVEN** el turno T3 reservado de la misma profesional el lunes 2026-11-02 de 13:00:00Z a 13:30:00Z y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con el horario del lunes de 900 a 1140
- **THEN** el resultado es una lista vacía

#### Scenario: Turno de otro profesional no se lista
- **GIVEN** el turno T4 reservado del profesional 00000000-0000-0000-0000-000000000002 el lunes 2026-12-07 de 13:00:00Z a 13:30:00Z y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con professional_id 00000000-0000-0000-0000-000000000001 y un horario vacío
- **THEN** el resultado no incluye a T4

#### Scenario: Los turnos fuera de horario se devuelven ordenados
- **GIVEN** los turnos reservados T5 (lunes 2026-12-14 de 13:00:00Z a 13:30:00Z) y T6 (lunes 2026-12-07 de 13:00:00Z a 13:30:00Z) de la misma profesional y now 2026-11-06T12:00:00Z
- **WHEN** se llama a appointments_outside_working_hours con el horario del lunes de 900 a 1140
- **THEN** el resultado es la lista T6, T5
