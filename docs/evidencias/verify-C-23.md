# Verificación de C-23 — api-ciclo-de-vida-del-turno

## Aprobación de la autora (governance MEDIO)

> Aprobado por la autora según propuesta y respuestas del explore (D1 a D18 con correcciones C1 a C6).
> Implementación completada con Strict TDD en todos los niveles.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 24/24 en [tasks.md](../../openspec/changes/api-ciclo-de-vida-del-turno/tasks.md).
- Suite por defecto: [pytest-C-23.txt](pytest-C-23.txt) (882 passed, 467 deselected).
- Integración: [pytest-integration-C-23.txt](pytest-integration-C-23.txt) (467 passed, 882 deselected).
- `mypy --strict app tests`: [mypy-C-23.txt](mypy-C-23.txt) (Success: no issues found in 170 source files).
- Mutaciones: [mutaciones-C-23.txt](mutaciones-C-23.txt) (51/51 mutaciones hicieron fallar su test; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-23.txt](trazabilidad-C-23.txt) (36 escenarios recolectados, 0 problemas).
- Validación OpenSpec: [validate-C-23.txt](validate-C-23.txt) (`openspec validate --strict` válido).
- Línea de base: [baseline-C-23.txt](baseline-C-23.txt) (872 passed / 426 deselected; 426 integración; 163 archivos mypy).

## Artefactos

- [proposal.md](../../openspec/changes/api-ciclo-de-vida-del-turno/proposal.md)
- [design.md](../../openspec/changes/api-ciclo-de-vida-del-turno/design.md)
- [tasks.md](../../openspec/changes/api-ciclo-de-vida-del-turno/tasks.md)
- [spec.md (appointments-api)](../../openspec/changes/api-ciclo-de-vida-del-turno/specs/appointments-api/spec.md)

## Línea de base

Antes de escribir código: 872 passed (y 426 deselected); 426 passed en integración; `mypy` Success en 163 archivos (documentado en `baseline-C-23.txt`).

## Desvíos

- **C5 CORREGIDA (inserción de turnos pasados en tests)**: AppointmentRepository no tiene método de inserción. Para los turnos con inicio pasado requeridos por los escenarios de atención y ausencia, los tests insertan directamente con los modelos ORM `AppointmentModel` y `AppointmentStatusChangeModel` en una sesión propia del test con claves foráneas de `demo_data.py` y fechas relativas al reloj real. No se introdujo código de inserción en el repositorio de producción solo para testing.
- **C6 / Nombres de visualización en auth_support**: los tests de integración que comprueban los nombres legibles de `demo_data.py` ("Recepción Demo", etc.) ajustan explícitamente el `display_name` del `AppUserModel` generado por `create_auth_users` durante la preparación del test.
- **Fechas relativas en tests**: todos los tests calculan fechas futuras relativas al reloj del sistema (lunes futuro a las 10:00 local -03:00) y pasadas relativas al reloj real, sin mocks, sin patch, sin monkeypatch y sin fechas fijas.

## Trazabilidad

Cada escenario de la spec delta `appointments-api` mapeado a un test de integración. `trazabilidad-C-23.py` comprueba con `pytest --collect-only` que cada test existe.

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | appointments-api | Cancelación autorizada de turnos | Recepción cancela un turno reservado | `tests/integration/test_api_appointment_cancel.py::test_reception_cancels_reserved_appointment` |
| 2 | appointments-api | Cancelación autorizada de turnos | El administrador cancela un turno confirmado | `tests/integration/test_api_appointment_cancel.py::test_admin_cancels_confirmed_appointment` |
| 3 | appointments-api | Cancelación autorizada de turnos | Cancelar un turno atendido responde 422 | `tests/integration/test_api_appointment_cancel.py::test_cancel_attended_appointment_returns_422` |
| 4 | appointments-api | Cancelación autorizada de turnos | Cancelar un turno ya cancelado responde 422 | `tests/integration/test_api_appointment_cancel.py::test_cancel_already_cancelled_appointment_returns_422` |
| 5 | appointments-api | Cancelación autorizada de turnos | Cancelar un turno inexistente responde 404 | `tests/integration/test_api_appointment_cancel.py::test_cancel_nonexistent_appointment_returns_404` |
| 6 | appointments-api | Cancelación autorizada de turnos | El odontólogo intenta cancelar un turno | `tests/integration/test_api_appointment_cancel.py::test_dentist_cannot_cancel_appointment_returns_403` |
| 7 | appointments-api | Reprogramación autorizada de turnos | Reprogramar solo el inicio conserva la duración real | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado` |
| 8 | appointments-api | Reprogramación autorizada de turnos | Reprogramar con profesional, sillón y duración explícitos | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_with_explicit_professional_chair_and_duration` |
| 9 | appointments-api | Reprogramación autorizada de turnos | Choque de profesional al reprogramar | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_professional_overlap_returns_409` |
| 10 | appointments-api | Reprogramación autorizada de turnos | Choque de sillón al reprogramar | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_chair_overlap_returns_409` |
| 11 | appointments-api | Reprogramación autorizada de turnos | Reprogramar dentro de un bloqueo responde 409 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_inside_block_returns_409` |
| 12 | appointments-api | Reprogramación autorizada de turnos | Reprogramar fuera de horario responde 409 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_outside_working_hours_returns_409` |
| 13 | appointments-api | Reprogramación autorizada de turnos | Reprogramar al pasado responde 422 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_in_the_past_returns_422` |
| 14 | appointments-api | Reprogramación autorizada de turnos | startAt sin zona horaria responde 400 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_start_at_without_timezone_returns_400` |
| 15 | appointments-api | Reprogramación autorizada de turnos | Un campo extra en la reprogramación responde 400 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_extra_field_returns_400` |
| 16 | appointments-api | Reprogramación autorizada de turnos | Reprogramar un turno inexistente responde 404 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_nonexistent_appointment_returns_404` |
| 17 | appointments-api | Reprogramación autorizada de turnos | El odontólogo intenta reprogramar un turno | `tests/integration/test_api_appointment_reschedule.py::test_dentist_cannot_reschedule_returns_403` |
| 18 | appointments-api | Reprogramación autorizada de turnos | Reprogramar un turno en estado terminal responde 422 | `tests/integration/test_api_appointment_reschedule.py::test_reschedule_terminal_state_appointment_returns_422` |
| 19 | appointments-api | Cambio de estado autorizado | Confirmar un turno reservado | `tests/integration/test_api_appointment_status.py::test_confirm_reserved_appointment` |
| 20 | appointments-api | Cambio de estado autorizado | Marcar atendido un turno confirmado con inicio pasado | `tests/integration/test_api_appointment_status.py::test_mark_attended_confirmed_appointment_with_past_start` |
| 21 | appointments-api | Cambio de estado autorizado | Marcar ausente un turno confirmado con inicio pasado | `tests/integration/test_api_appointment_status.py::test_mark_absent_confirmed_appointment_with_past_start` |
| 22 | appointments-api | Cambio de estado autorizado | Marcar atendido antes del inicio responde 422 | `tests/integration/test_api_appointment_status.py::test_mark_attended_before_start_returns_422` |
| 23 | appointments-api | Cambio de estado autorizado | Doble transición secuencial deja una sola entrada nueva | `tests/integration/test_api_appointment_status.py::test_double_sequential_transition_leaves_single_new_entry` |
| 24 | appointments-api | Cambio de estado autorizado | Confirmar un turno cancelado responde 422 | `tests/integration/test_api_appointment_status.py::test_confirm_cancelled_appointment_returns_422` |
| 25 | appointments-api | Cambio de estado autorizado | toStatus "cancelado" responde 400 | `tests/integration/test_api_appointment_status.py::test_to_status_cancelado_returns_400` |
| 26 | appointments-api | Cambio de estado autorizado | toStatus "reservado" responde 400 | `tests/integration/test_api_appointment_status.py::test_to_status_reservado_returns_400` |
| 27 | appointments-api | Cambio de estado autorizado | Cambiar el estado de un turno inexistente responde 404 | `tests/integration/test_api_appointment_status.py::test_change_status_nonexistent_appointment_returns_404` |
| 28 | appointments-api | Cambio de estado autorizado | El odontólogo cambia el estado de un turno ajeno | `tests/integration/test_api_appointment_status.py::test_dentist_changes_status_of_other_professional_returns_403_from_domain` |
| 29 | appointments-api | Historial de turnos | Historial ascendente con el alta y changedByName | `tests/integration/test_api_appointment_history.py::test_history_ascending_with_creation_and_changed_by_name` |
| 30 | appointments-api | Historial de turnos | Entrada de reprogramación con to reservado y detalle plano | `tests/integration/test_api_appointment_history.py::test_history_reschedule_entry_has_to_reservado_and_flat_detail` |
| 31 | appointments-api | Historial de turnos | Historial de un turno inexistente responde 404 | `tests/integration/test_api_appointment_history.py::test_history_nonexistent_appointment_returns_404` |
| 32 | appointments-api | Permisos por propiedad del historial | El odontólogo lee el historial de su propio turno | `tests/integration/test_api_appointment_history.py::test_dentist_reads_own_appointment_history_returns_200` |
| 33 | appointments-api | Permisos por propiedad del historial | El odontólogo lee el historial de un turno ajeno | `tests/integration/test_api_appointment_history.py::test_dentist_reads_other_professional_history_returns_403` |
| 34 | appointments-api | Permisos por propiedad del historial | Recepción lee el historial de un turno ajeno | `tests/integration/test_api_appointment_history.py::test_reception_reads_other_professional_history_returns_200` |
| 35 | appointments-api | Permisos por propiedad del historial | El administrador lee el historial de un turno ajeno | `tests/integration/test_api_appointment_history.py::test_admin_reads_other_professional_history_returns_200` |
| 36 | appointments-api | Documentación OpenAPI del ciclo de vida | Swagger documenta los status del ciclo de vida | `tests/integration/test_appointment_lifecycle_openapi.py::test_appointment_lifecycle_openapi_documentation` |
<!-- trazabilidad:fin -->

## Mutaciones

Comprobación por mutación sobre código de producción para verificar sensibilidad de las pruebas.

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_status_change_input_valid_statuses` | `backend/app/api/schemas.py` | `-AllowedStatusChange = Literal["confirmado", "atendido", "ausente"] +AllowedStat` | `E   pydantic_core._pydantic_core.ValidationError: 1 validation error for StatusC` |
| 2 | `test_status_change_input_cancelado_rejected` | `backend/app/api/schemas.py` | `-    to_status: AllowedStatusChange = Field(alias="toStatus") +    to_status: st` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 3 | `test_status_change_input_reservado_rejected` | `backend/app/api/schemas.py` | `-AllowedStatusChange = Literal["confirmado", "atendido", "ausente"] +AllowedStat` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 4 | `test_status_change_input_extra_field_forbidden` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 5 | `test_reschedule_input_start_at_with_tz_accepted` | `backend/app/api/schemas.py` | `-        if v.tzinfo is None: +        if v.tzinfo is not None:` | `E   pydantic_core._pydantic_core.ValidationError: 1 validation error for Resched` |
| 6 | `test_reschedule_input_minimal_accepted` | `backend/app/api/schemas.py` | `-    professional_id: UUID | None = Field(default=None, alias="professionalId") ` | `E   pydantic_core._pydantic_core.ValidationError: 1 validation error for Resched` |
| 7 | `test_reschedule_input_start_at_without_tz_rejected` | `backend/app/api/schemas.py` | `-        if v.tzinfo is None: +        if False and v.tzinfo is None:` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 8 | `test_reschedule_input_extra_field_forbidden` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 9 | `test_history_entry_initial_entry_serializes_from_and_reschedule_as_null` | `backend/app/api/schemas.py` | `-    from_status: str | None = Field(default=None, serialization_alias="from") +` | `E   AssertionError: assert 'from' in {'changedAt': '2026-11-16T10:00:00Z', 'chan` |
| 10 | `test_history_entry_reschedule_detail_flat_eight_fields` | `backend/app/api/schemas.py` | `-    previous_start_at: str = Field(serialization_alias="previousStartAt") +    ` | `E   KeyError: 'previousStartAt'` |
| 11 | `test_get_display_names_empty_list_makes_zero_queries` | `backend/app/repositories/users.py` | `-            return {} +            return {UUID("00000000-0000-0000-0000-000000` | `E   AssertionError: assert {UUID('000000... 'Inesperado'} == {}` |
| 12 | `test_get_display_names_resolves_in_single_query` | `backend/app/repositories/users.py` | `-        stmt = select(UserModel.id, UserModel.display_name).where(UserModel.id.` | `E   AssertionError: assert {} == {UUID('000000...tración Demo'}` |
| 13 | `test_get_appointment_history_returns_none_if_appointment_not_found` | `backend/app/services/appointments.py` | `-        return None +        return []` | `E   assert [] is None` |
| 14 | `test_get_appointment_history_ascending_order_and_reschedule_mapping` | `backend/app/services/appointments.py` | `-    changes = status_repo.list_by_appointment_id(appointment_id) +    changes =` | `E   AssertionError: assert 'confirmado' is None` |
| 15 | `test_get_appointment_history_unknown_user_leaves_changed_by_name_null` | `backend/app/services/appointments.py` | `-        changed_name = names_by_id.get(c.changed_by) +        changed_name = na` | `E   AssertionError: assert 'Usuario Ficticio' is None` |
| 16 | `test_reception_cancels_reserved_appointment` | `backend/app/api/appointments.py` | `-        auto_commit=True, +        auto_commit=False,` | `E   AssertionError: assert 1 == 2` |
| 17 | `test_admin_cancels_confirmed_appointment` | `backend/app/api/appointments.py` | `-        status=appointment.status.value, +        status="reservado",` | `E   AssertionError: assert 'reservado' == 'cancelado'` |
| 18 | `test_cancel_attended_appointment_returns_422` | `backend/app/api/appointments.py` | `-    if isinstance(result, Rejected): +    if False and isinstance(result, Rejec` | `E   AssertionError` |
| 19 | `test_cancel_already_cancelled_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 20 | `test_cancel_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-    if result is None: +    if False and result is None:` | `E   AssertionError` |
| 21 | `test_dentist_cannot_cancel_appointment_returns_403` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)), +    ` | `E   KeyError: (<Resource.APPOINTMENT: 'appointment'>, <Action.READ: 'read'>)` |
| 22 | `test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado` | `backend/app/api/appointments.py` | `-        duration_min=body.duration_min, +        duration_min=999,` | `E   AssertionError: {"violations":[{"code":"INVALID_DURATION","message":"La dura` |
| 23 | `test_reschedule_with_explicit_professional_chair_and_duration` | `backend/app/api/appointments.py` | `-        professional_id=body.professional_id, +        professional_id=None,` | `E   AssertionError: assert '00000000-000...-000000000001' == '00000000-000...-00` |
| 24 | `test_reschedule_professional_overlap_returns_409` | `backend/app/api/appointments.py` | `-    if isinstance(result, Rejected): +    if False and isinstance(result, Rejec` | `E   AssertionError` |
| 25 | `test_reschedule_chair_overlap_returns_409` | `backend/app/api/appointments.py` | `-        chair_id=body.chair_id, +        chair_id=None,` | `E   AssertionError: {"id":"815f9856-9b9f-4226-9581-8c086e186aff","patientId":"00` |
| 26 | `test_reschedule_inside_block_returns_409` | `backend/app/api/appointments.py` | `-        start_at=body.start_at, +        start_at=body.start_at + timedelta(day` | `E   NameError: name 'timedelta' is not defined` |
| 27 | `test_reschedule_outside_working_hours_returns_409` | `backend/app/api/appointments.py` | `-        start_at=body.start_at, +        start_at=body.start_at.replace(hour=10` | `E   AssertionError: {"id":"f4e4265c-bde9-49c9-b3be-0108d3118eb8","patientId":"00` |
| 28 | `test_reschedule_in_the_past_returns_422` | `backend/app/api/appointments.py` | `-        now=now, +        now=now - timedelta(days=365),` | `E   NameError: name 'timedelta' is not defined` |
| 29 | `test_reschedule_start_at_without_timezone_returns_400` | `backend/app/api/schemas.py` | `-        if v.tzinfo is None: +        if False and v.tzinfo is None:` | `E   ValueError: start_at necesita zona horaria (datetime naive)` |
| 30 | `test_reschedule_extra_field_returns_400` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   assert 200 == 400` |
| 31 | `test_reschedule_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-    if result is None: +    if False and result is None:` | `E   AssertionError` |
| 32 | `test_dentist_cannot_reschedule_returns_403` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT, Action.RESCHEDULE)), +` | `E   KeyError: (<Resource.APPOINTMENT: 'appointment'>, <Action.READ: 'read'>)` |
| 33 | `test_reschedule_terminal_state_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 34 | `test_confirm_reserved_appointment` | `backend/app/api/appointments.py` | `-        target_status=AppointmentStatus(body.to_status), +        target_status` | `E   AttributeError: type object 'AppointmentStatus' has no attribute 'CANCELADO'` |
| 35 | `test_mark_attended_confirmed_appointment_with_past_start` | `backend/app/api/appointments.py` | `-    now = datetime.now(UTC) +    now = datetime.now(UTC) - timedelta(days=365)` | `E   NameError: name 'timedelta' is not defined` |
| 36 | `test_mark_absent_confirmed_appointment_with_past_start` | `backend/app/api/appointments.py` | `-        target_status=AppointmentStatus(body.to_status), +        target_status` | `E   AttributeError: type object 'AppointmentStatus' has no attribute 'CONFIRMADO` |
| 37 | `test_mark_attended_before_start_returns_422` | `backend/app/api/appointments.py` | `-        raise DomainRejectedError(result) +        raise NotFoundError("Turno n` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 38 | `test_double_sequential_transition_leaves_single_new_entry` | `backend/app/api/appointments.py` | `-        auto_commit=True, +        auto_commit=False,` | `E   AssertionError: {"id":"2f5c4e1d-e1cc-4381-9b1a-ed633569ff9d","patientId":"00` |
| 39 | `test_confirm_cancelled_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 40 | `test_to_status_cancelado_returns_400` | `backend/app/api/schemas.py` | `-AllowedStatusChange = Literal["confirmado", "atendido", "ausente"] +AllowedStat` | `E   ValueError: Para cancelar debe usar cancel_appointment` |
| 41 | `test_to_status_reservado_returns_400` | `backend/app/api/schemas.py` | `-    to_status: AllowedStatusChange = Field(alias="toStatus") +    to_status: st` | `E   assert 422 == 400` |
| 42 | `test_change_status_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-    if result is None: +    if False and result is None:` | `E   AssertionError` |
| 43 | `test_dentist_changes_status_of_other_professional_returns_403_from_domain` | `backend/app/api/appointments.py` | `-        actor=permission.actor, +        actor=Actor(user_id=permission.actor.u` | `E   NameError: name 'Actor' is not defined` |
| 44 | `test_history_ascending_with_creation_and_changed_by_name` | `backend/app/api/appointments.py` | `-    return history +    return list(reversed(history))` | `E   AssertionError: assert 'reservado' is None` |
| 45 | `test_history_reschedule_entry_has_to_reservado_and_flat_detail` | `backend/app/api/appointments.py` | `+    if history is not None: +        history = []` | `E   assert 0 == 3` |
| 46 | `test_history_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        return []` | `E   assert 200 == 404` |
| 47 | `test_dentist_reads_own_appointment_history_returns_200` | `backend/app/api/appointments.py` | `-        ensure_own_professional(permission, appointment.professional_id) +     ` | `E   NameError: name 'ForbiddenError' is not defined` |
| 48 | `test_dentist_reads_other_professional_history_returns_403` | `backend/app/api/appointments.py` | `-    if permission.scope is Scope.OWN: +    if False and permission.scope is Sco` | `E   AssertionError: [{"from":null,"to":"reservado","changedBy":"00000000-0000-00` |
| 49 | `test_reception_reads_other_professional_history_returns_200` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT_HISTORY, Action.READ)),` | `E   AttributeError: type object 'Resource' has no attribute 'SETTINGS'` |
| 50 | `test_admin_reads_other_professional_history_returns_200` | `backend/app/api/appointments.py` | `-    status_code=status.HTTP_200_OK, +    status_code=status.HTTP_403_FORBIDDEN,` | `E   AssertionError: [{"from":null,"to":"reservado","changedBy":"00000000-0000-00` |
| 51 | `test_appointment_lifecycle_openapi_documentation` | `backend/app/api/appointments.py` | `-        **violation_responses(409, 422), +        **violation_responses(422),` | `E   AssertionError: assert '409' in {'200': {'content': {'application/json': {'s` |
<!-- mutaciones:fin -->
