## ADDED Requirements

### Requirement: Entrada de historial en el alta del turno
`NewAppointmentRequest` SHALL exigir `changed_by` (`UUID` *keyword-only* del actor). Cuando `validate_new_appointment` acepta el turno, SHALL devolver `Ok(appointment, status_change)` con `appointment_id` igual al `id` del turno, `from_status` en `None`, `to_status` en `reservado`, `changed_by` igual a `request.changed_by`, `changed_at` igual a `context.now` en UTC y `reschedule` en `None` (RN-TU-01, RN-TU-06). Si devuelve `Rejected`, MUST NOT generar entrada de historial.

#### Scenario: Entrada de historial al crear un turno válido
- **GIVEN** un contexto válido con `now` en el lunes 20/10/2026 a las 09:00 hora local (`2026-10-20T12:00:00Z`), P1 ("Dra. Laura Quiroga") y S1 ("Sillón 1") libres
- **WHEN** recepción `U2` solicita con `validate_new_appointment` el turno `T1` para el martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`) pasando `changed_by=U2`
- **THEN** el resultado es `Ok(appointment, status_change)` donde `appointment.id` es `T1` y `appointment.status` es `reservado`
- **AND** `status_change` tiene `appointment_id=T1`, `from_status=None`, `to_status=reservado`, `changed_by=U2`, `changed_at=2026-10-20T12:00:00Z` (09:00 hora local) y `reschedule=None`

#### Scenario: Rechazo en el alta no genera entrada de historial
- **GIVEN** el turno existente `T1` de P1 el martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`) y `now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** recepción `U2` solicita otro turno en el mismo intervalo para P1 con `changed_by=U2`
- **THEN** el resultado es `Rejected` con `PROFESSIONAL_OVERLAP` y no devuelve `Ok` ni entrada `AppointmentStatusChange` alguna

