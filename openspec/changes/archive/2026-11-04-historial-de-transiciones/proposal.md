# Proposal

## Why

El dominio del turno hoy crea turnos (`validate_new_appointment`), aplica cambios de estado (`change_status`), cancela (`cancel_appointment`) y reprograma (`reschedule_appointment`), pero devuelve únicamente `Ok(appointment=...)` sin producir las entradas del historial funcional (`AppointmentStatusChange`) exigidas por **RN-TU-06**, **US-033**, **US-030 CA-3** y **US-031 CA-5**. Este change cierra la Fase 3 del dominio y habilita el Gate G8 hacia la persistencia de turnos e historial en C-17 (`persistencia-turnos-y-bloqueos`), haciendo que toda operación exitosa de agenda y ciclo de vida devuelva de forma pura e inmutable tanto la nueva copia del turno como su entrada de historial asociada, mientras que los rechazos (`Rejected`) no producen entrada alguna.

## What Changes

- Se agrega en `backend/app/domain/model.py` el valor inmutable `RescheduleDetail` (`@dataclass(frozen=True, slots=True)`) con `previous_interval: Interval`, `new_interval: Interval`, `previous_professional_id: UUID`, `new_professional_id: UUID`, `previous_chair_id: UUID` y `new_chair_id: UUID`.
- Se agrega en `backend/app/domain/model.py` la entidad inmutable `AppointmentStatusChange` (`@dataclass(frozen=True, slots=True)`) sin `id` propio de dominio, con `appointment_id: UUID`, `from_status: AppointmentStatus | None` (`None` únicamente en el alta), `to_status: AppointmentStatus`, `changed_by: UUID`, `changed_at: datetime` (con zona horaria obligatoria y normalizada a UTC mediante `_to_utc`) y `reschedule: RescheduleDetail | None = None`, validando en `__post_init__` que `changed_at` no sea *naive* (`ValueError`) y que cuando `from_status == to_status` el campo `reschedule` no sea `None` (`ValueError`).
- **BREAKING (interno al dominio de turnos)**: Se amplía `Ok` en `backend/app/domain/violations.py` a `Ok(appointment: Appointment, status_change: AppointmentStatusChange)` con ambos campos obligatorios. `Rejected` y el `Ok` de catálogo (`app.domain.catalog.result.Ok`) no cambian.
- **BREAKING (interno al dominio de turnos)**: Se agrega `changed_by: UUID = field(kw_only=True)` obligatorio en `NewAppointmentRequest` (`backend/app/domain/model.py`), preservando las 7 posiciones posicionales actuales (`id` a `duration_min`).
- Se actualizan `validate_new_appointment`, `change_status`, `cancel_appointment` y `reschedule_appointment` para construir y devolver la entrada `AppointmentStatusChange` dentro de `Ok(appointment=..., status_change=...)`:
  - `validate_new_appointment`: `from_status=None`, `to_status=AppointmentStatus.RESERVED`, `changed_by=request.changed_by`, `changed_at=context.now`, `reschedule=None`.
  - `change_status` y `cancel_appointment`: `from_status=appointment.status`, `to_status` destino, `changed_by=actor.user_id`, `changed_at=now` normalizado a UTC, `reschedule=None`.
  - `reschedule_appointment`: reemplaza la entrada de alta de la delegación interna por una única entrada con `from_status=appointment.status` (`reservado` o `confirmado`), `to_status=AppointmentStatus.RESERVED`, `changed_by=actor.user_id`, `changed_at=context.now` y `reschedule=RescheduleDetail(...)` con los intervalos, profesionales y sillones anteriores y nuevos.
- Se reexportan `AppointmentStatusChange` y `RescheduleDetail` en `backend/app/domain/__init__.py` y `backend/app/domain/appointment/__init__.py`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-lifecycle`: incorpora los modelos inmutables `AppointmentStatusChange` y `RescheduleDetail`, el retorno `Ok(appointment, status_change)` en cambios de estado, cancelaciones y reprogramaciones, la ausencia de entrada ante `Rejected` y la actualización de los requisitos que excluían el historial en C-10 y C-11.
- `appointment-scheduling`: actualiza el requisito de alta de turno válido (`validate_new_appointment`) para exigir `changed_by` en `NewAppointmentRequest` y devolver `Ok(appointment, status_change)` con la entrada inicial (`from_status=None`, `to_status=reservado`).

## Impact

- **Código afectado**: `backend/app/domain/model.py`, `backend/app/domain/violations.py`, `backend/app/domain/appointment/validate.py`, `backend/app/domain/appointment/transitions.py`, `backend/app/domain/appointment/reschedule.py`, `backend/app/domain/appointment/__init__.py` y `backend/app/domain/__init__.py`.
- **Tests afectados**: constructores de `NewAppointmentRequest` en `backend/tests/domain/test_model.py`, `test_validate_new_appointment.py`, `test_catalog_agenda.py` y `test_lifecycle_agenda.py`; constructores directos de `Ok(...)` en `backend/tests/domain/test_violations.py`; más la nueva suite dedicada `backend/tests/domain/test_status_history.py`.
- **Persistencia, API y UI**: fuera de alcance. Cómo se persiste `AppointmentStatusChange` y `RescheduleDetail` en PostgreSQL corresponde a C-17 (`persistencia-turnos-y-bloqueos`), y la exposición HTTP a C-22/C-23.
- **Dependencias**: ninguna dependencia externa nueva; se mantiene la pureza absoluta de `backend/app/domain` verificada por `test_domain_purity.py`.

