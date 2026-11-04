# Verificación C-12 — Historial de transiciones

## Resultado

- Artefactos archivados: [proposal.md](../../openspec/changes/archive/2026-11-04-historial-de-transiciones/proposal.md), [design.md](../../openspec/changes/archive/2026-11-04-historial-de-transiciones/design.md), [specs/appointment-lifecycle/spec.md](../../openspec/changes/archive/2026-11-04-historial-de-transiciones/specs/appointment-lifecycle/spec.md), [specs/appointment-scheduling/spec.md](../../openspec/changes/archive/2026-11-04-historial-de-transiciones/specs/appointment-scheduling/spec.md) y [tasks.md](../../openspec/changes/archive/2026-11-04-historial-de-transiciones/tasks.md).
- Baseline real antes de tocar código: `648 passed, 19 deselected in 13.00s`; `mypy --strict app tests`: `Success: no issues found in 71 source files`.
- Resultado final: `668 passed, 19 deselected in 6.60s` ([pytest-C-12.txt](pytest-C-12.txt)); `mypy --strict app tests`: `Success: no issues found in 72 source files` ([mypy-C-12.txt](mypy-C-12.txt)).
- `openspec validate historial-de-transiciones --strict`: `Change 'historial-de-transiciones' is valid`.
- `git diff --check`: sin salida y código 0.

## Trazabilidad de escenarios

Los 24 escenarios del delta (`specs/appointment-lifecycle/spec.md` y `specs/appointment-scheduling/spec.md`) tienen cobertura automatizada:

| # | Spec | Escenario | Test |
|---|---|---|---|
| 1 | `appointment-lifecycle` | Inmutabilidad de AppointmentStatusChange | `tests/domain/test_status_history.py::test_appointment_status_change_is_immutable` |
| 2 | `appointment-lifecycle` | Inmutabilidad de RescheduleDetail | `tests/domain/test_status_history.py::test_reschedule_detail_is_immutable` |
| 3 | `appointment-lifecycle` | changed_at sin zona horaria lanza ValueError | `tests/domain/test_status_history.py::test_status_change_naive_changed_at_raises_value_error` |
| 4 | `appointment-lifecycle` | changed_at con zona horaria distinta se normaliza a UTC | `tests/domain/test_status_history.py::test_status_change_normalizes_changed_at_to_utc` |
| 5 | `appointment-lifecycle` | Misma transición sin detalle de reprogramación lanza ValueError | `tests/domain/test_status_history.py::test_status_change_same_status_without_reschedule_raises_value_error` |
| 6 | `appointment-lifecycle` | Entrada al confirmar un turno reservado | `tests/domain/test_status_history.py::test_change_status_confirm_reserved_returns_status_change` |
| 7 | `appointment-lifecycle` | Entrada al marcar como atendido | `tests/domain/test_status_history.py::test_change_status_attended_and_no_show_return_status_change` |
| 8 | `appointment-lifecycle` | Entrada al marcar como ausente | `tests/domain/test_status_history.py::test_change_status_attended_and_no_show_return_status_change` |
| 9 | `appointment-lifecycle` | Entrada al cancelar un turno | `tests/domain/test_status_history.py::test_cancel_appointment_returns_status_change` |
| 10 | `appointment-lifecycle` | Reprogramar desde reservado registra reservado a reservado con detalle | `tests/domain/test_status_history.py::test_reschedule_from_reserved_returns_single_status_change_with_detail` |
| 11 | `appointment-lifecycle` | Reprogramar desde confirmado registra confirmado a reservado con detalle | `tests/domain/test_status_history.py::test_reschedule_from_confirmed_changing_resources_returns_status_change_with_detail` |
| 12 | `appointment-lifecycle` | Reprogramar no deja la entrada de alta de la validación interna | `tests/domain/test_status_history.py::test_reschedule_from_reserved_returns_single_status_change_with_detail` |
| 13 | `appointment-lifecycle` | Rechazo en change_status no genera entrada | `tests/domain/test_status_history.py::test_change_status_and_cancel_rejections_have_no_status_change` |
| 14 | `appointment-lifecycle` | Rechazo en cancel_appointment no genera entrada | `tests/domain/test_status_history.py::test_change_status_and_cancel_rejections_have_no_status_change` |
| 15 | `appointment-lifecycle` | Rechazo en reschedule_appointment no genera entrada | `tests/domain/test_status_history.py::test_reschedule_rejections_have_no_status_change` |
| 16 | `appointment-lifecycle` | Cancelar reservado | `tests/domain/test_status_history.py::test_cancel_appointment_returns_status_change` y `tests/domain/test_transitions.py::test_cancel_reserved_returns_cancelled_copy` |
| 17 | `appointment-lifecycle` | Confirmar reservado | `tests/domain/test_status_history.py::test_change_status_confirm_reserved_returns_status_change` y `tests/domain/test_transitions.py::test_confirm_reserved_returns_confirmed_copy` |
| 18 | `appointment-lifecycle` | Rechazo no altera turno | `tests/domain/test_status_history.py::test_change_status_and_cancel_rejections_have_no_status_change` y `tests/domain/test_transitions.py::test_rejected_operations_leave_originals_unchanged` |
| 19 | `appointment-lifecycle` | Guardias sobre dominio real | `tests/domain/test_import_guard.py::test_domain_file_has_no_forbidden_imports`, `tests/domain/test_clock_guard.py::test_domain_file_has_no_clock_calls` y `tests/domain/test_domain_dependencies.py::test_domain_package_only_imports_allowed_modules` |
| 20 | `appointment-lifecycle` | Alta y catálogo conservan payload | `tests/domain/test_lifecycle_agenda.py::test_new_booking_and_catalog_keep_separate_payloads` |
| 21 | `appointment-lifecycle` | El alta conserva el mensaje del pasado | `tests/domain/test_status_history.py::test_validate_new_appointment_rejection_has_no_status_change` y `tests/domain/test_reschedule.py::test_validate_new_appointment_alta_default_past_verb_still_says_dar_turnos` |
| 22 | `appointment-lifecycle` | Sin códigos nuevos ni cambios de ocupación | `tests/domain/test_violations.py::test_violation_code_value_is_stable_api_code` y `tests/domain/test_validate_new_appointment.py::test_validate_new_appointment_only_occupying_statuses_block_professional` |
| 23 | `appointment-scheduling` | Entrada de historial al crear un turno válido | `tests/domain/test_status_history.py::test_validate_new_appointment_returns_creation_status_change` |
| 24 | `appointment-scheduling` | Rechazo en el alta no genera entrada de historial | `tests/domain/test_status_history.py::test_validate_new_appointment_rejection_has_no_status_change` |

## Evidencia del ciclo TDD

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 2.1 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 648/648 | ✅ `ImportError: cannot import name 'AppointmentStatusChange'` | ✅ `1 passed` | ✅ `2 passed` (con `RescheduleDetail` y reexports) | ✅ Clean |
| 2.2 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 2/2 | ✅ `2 failed` (`DID NOT RAISE ValueError` y `utcoffset != 0`) | ✅ `4 passed` (`_to_utc` en `__post_init__`) | ✅ `+02:00` y `-03:00` normalizados a UTC | ✅ Clean |
| 2.3 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 4/4 | ✅ `1 failed` (`DID NOT RAISE ValueError` en `RESERVED -> RESERVED`) | ✅ `5 passed` | ✅ `CONFIRMED -> CONFIRMED` sin `reschedule` y `RESERVED -> RESERVED` con `RescheduleDetail` | ✅ Clean |
| 2.4 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 5/5 | ✅ Mutación `frozen=False` → `2 failed` (`DID NOT RAISE FrozenInstanceError`) | ✅ `7 passed` (restaurado `frozen=True`) | ✅ Todos los campos de ambas dataclasses + `slots=True` | ✅ Clean |
| 3.1 | `tests/domain/test_violations.py`, `tests/domain/test_model.py` | Domain Unit | ✅ 70/70 | ✅ `2 failed` (`TypeError` en `Ok` y `NewAppointmentRequest`) | ✅ `72 passed` | ✅ `74 passed` (`pytest.raises(TypeError)` al omitir `status_change` o `changed_by`) | ✅ Clean |
| 4.1 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 7/7 | ✅ `1 failed` (`TypeError: Ok.__init__() missing 'status_change'`) | ✅ `8 passed` | ✅ `9 passed` (`U2`, `U3`, `PROFESSIONAL_OVERLAP` e `IN_THE_PAST`) | ✅ Clean |
| 5.1 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 9/9 | ✅ `1 failed` (`TypeError` en `change_status`) | ✅ `10 passed` | ✅ `11 passed` (`CONFIRMED`, `ATTENDED`, `NO_SHOW`, `now` local `-03:00`) | ✅ Clean |
| 5.2 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 11/11 | ✅ `1 failed` (`TypeError` en `cancel_appointment`) | ✅ `12 passed` | ✅ `13 passed` (desde `CONFIRMED` y `RESERVED` + rechazos sin historial) | ✅ Clean |
| 6.1 | `tests/domain/test_status_history.py` | Domain Unit | ✅ 13/13 | ✅ `1 failed` (`AssertionError: assert None is not None` en `from_status`) | ✅ `14 passed` | ✅ `16 passed` (desde `RESERVED` y `CONFIRMED` cambiando `P2`/`S2` + rechazos) | ✅ Clean |

## Desvíos del apply

1. **Tarea 2.4 (`test_appointment_status_change_is_immutable` y `test_reschedule_detail_is_immutable`)**: Como `RescheduleDetail` y `AppointmentStatusChange` se definieron con `@dataclass(frozen=True, slots=True)` en la Tarea 2.1 (según pedía esa tarea), los tests de inmutabilidad de la Tarea 2.4 pasaron de entrada (`7 passed in 0.15s`). Siguiendo la regla de TDD del apply, se aplicó una mutación temporal cambiando `frozen=False` en ambas dataclasses de `backend/app/domain/model.py`; pytest falló como se esperaba (`2 failed, 5 passed in 0.28s`, `Failed: DID NOT RAISE <class 'dataclasses.FrozenInstanceError'>`), y luego se restauró `frozen=True` (`7 passed in 0.24s`).
2. **Tarea 3.1 / D2 (constructores directos de `Ok` vs. aserciones de igualdad)**: En D2 y en la Tarea 3.1 se mencionaba actualizar constructores previos de `Ok` en `test_violations.py`, pero `test_violations.py` no tenía llamadas previas a `Ok(...)` (allí se agregaron los nuevos tests `test_ok_carries_appointment_and_status_change` y `test_ok_without_status_change_raises_type_error`). En cambio, tal como indicó la autora en las instrucciones del apply (paso 3), al pasar `Ok` a `Ok(appointment, status_change)` se actualizaron únicamente las **8 aserciones de igualdad** `assert result == Ok(...)` existentes en `test_validate_new_appointment.py` (3), `test_reschedule.py` (1) y `test_lifecycle_agenda.py` (4), además de los **5 sitios de construcción** de `NewAppointmentRequest`.
