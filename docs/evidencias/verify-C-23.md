# Verificación de C-23 — api-ciclo-de-vida-del-turno

## Aprobación de la autora (governance MEDIO)

> Aprobado por la autora según propuesta y respuestas del explore (D1 a D18 con correcciones C1 a C6).
> Implementación completada con Strict TDD en todos los niveles.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 24/24 en [tasks.md](../../openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/tasks.md).
- Suite por defecto: [pytest-C-23.txt](pytest-C-23.txt) (882 passed, 467 deselected).
- Integración: [pytest-integration-C-23.txt](pytest-integration-C-23.txt) (467 passed, 882 deselected).
- `mypy --strict app tests`: [mypy-C-23.txt](mypy-C-23.txt) (Success: no issues found in 170 source files).
- Mutaciones: [mutaciones-C-23.txt](mutaciones-C-23.txt) (51/51 mutaciones hicieron fallar su test; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-23.txt](trazabilidad-C-23.txt) (36 escenarios recolectados, 0 problemas).
- Validación OpenSpec: [validate-C-23.txt](validate-C-23.txt) (`openspec validate --strict` válido).
- Línea de base: [baseline-C-23.txt](baseline-C-23.txt) (872 passed / 426 deselected; 426 integración; 163 archivos mypy).

## Verificación manual por HTTP (2026-11-07)

Se ejecutó [http-C-23.sh](http-C-23.sh) contra la API con PostgreSQL 16 real y el seed ficticio; la salida cruda está en [http-C-23.txt](http-C-23.txt). Son 24 pruebas: la 21 inserta un turno en la base y la 24 consulta la base, ambas sin pedido HTTP.

| # | Prueba | HTTP | Código |
|---|---|---|---|
| 1 | recepcion da turno A1: Quiroga lunes 10:00 Sillon 1 (201) | 201 | — |
| 2 | recepcion da turno A2: Sosa lunes 09:00 Sillon 2 (201) | 201 | — |
| 3 | odontologo (Quiroga) confirma A1, turno propio (200) | 200 | — |
| 4 | confirmar A1 otra vez: mismo estado (422 INVALID_TRANSITION) | 422 | `INVALID_TRANSITION` |
| 5 | odontologo (Quiroga) confirma A2 de Sosa (403 del dominio) | 403 | `FORBIDDEN_OPERATION` |
| 6 | /status con cancelado (400) | 400 | Sin código de violación; `errors`: `toStatus`, `literal_error` |
| 7 | marcar atendido A1 antes de su hora (422 STATUS_CHANGE_TOO_EARLY) | 422 | `STATUS_CHANGE_TOO_EARLY` |
| 8 | reprogramar A1 a las 11:00, solo startAt (200, vuelve a reservado) | 200 | — |
| 9 | reprogramar A2 a las 11:00 en Sillon 1 (409 CHAIR_OVERLAP) | 409 | `CHAIR_OVERLAP` |
| 10 | reprogramar A2 al pasado (422 IN_THE_PAST) | 422 | `IN_THE_PAST` |
| 11 | reprogramar sin zona horaria (400) | 400 | Sin código de violación; `errors`: `startAt`, `value_error` |
| 12 | odontologo intenta reprogramar (403) | 403 | `FORBIDDEN_OPERATION` |
| 13 | odontologo intenta cancelar (403) | 403 | `FORBIDDEN_OPERATION` |
| 14 | recepcion cancela A2 (200) | 200 | — |
| 15 | cancelar A2 otra vez (422 INVALID_TRANSITION) | 422 | `INVALID_TRANSITION` |
| 16 | cancelar turno inexistente (404) | 404 | `NOT_FOUND` (campo `code`, no en `violations`) |
| 17 | historial de A1 como recepcion (200: alta, confirmado, reprogramacion) | 200 | — |
| 18 | historial de A1 como odontologo, turno propio (200) | 200 | — |
| 19 | historial de A2 (Sosa) como odontologo (403) | 403 | `FORBIDDEN_OPERATION` |
| 20 | historial de turno inexistente (404) | 404 | `NOT_FOUND` (campo `code`, no en `violations`) |
| 21 | turno A3 de Quiroga ya empezado, insertado en la base (como en los tests de C-23) | No aplica | `INSERT 0 1`; fila `2026-11-07 01:00:00+00\|reservado` |
| 22 | odontologo marca atendido A3 (200) | 200 | — |
| 23 | marcar ausente A3 ya atendido (422 INVALID_TRANSITION) | 422 | `INVALID_TRANSITION` |
| 24 | historial completo en la base | No aplica | 6 filas: `f\|reservado\|atendido\|odontologo\|f`, `f\|-\|reservado\|recepcion\|f`, `f\|reservado\|cancelado\|recepcion\|f`, `t\|-\|reservado\|recepcion\|f`, `t\|reservado\|confirmado\|odontologo\|f`, `t\|confirmado\|reservado\|recepcion\|t` |

## Artefactos

- [proposal.md](../../openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/proposal.md)
- [design.md](../../openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/design.md)
- [tasks.md](../../openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/tasks.md)
- [spec.md (appointments-api)](../../openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/specs/appointments-api/spec.md)

## Línea de base

Antes de escribir código: 872 passed (y 426 deselected); 426 passed en integración; `mypy` Success en 163 archivos (documentado en `baseline-C-23.txt`).

## Desvíos

- **C5 CORREGIDA (inserción de turnos pasados en tests)**: AppointmentRepository no tiene método de inserción. Para los turnos con inicio pasado requeridos por los escenarios de atención y ausencia, los tests insertan directamente con los modelos ORM `AppointmentModel` y `AppointmentStatusChangeModel` en una sesión propia del test con claves foráneas de `demo_data.py` y fechas relativas al reloj real. No se introdujo código de inserción en el repositorio de producción solo para testing.
- **C6 / Nombres de visualización en auth_support**: los tests de integración que comprueban los nombres legibles de `demo_data.py` ("Recepción Demo", etc.) ajustan explícitamente el `display_name` del `AppUserModel` generado por `create_auth_users` durante la preparación del test.
- **Fechas relativas en tests**: todos los tests calculan fechas futuras relativas al reloj del sistema (lunes futuro a las 10:00 local -03:00) y pasadas relativas al reloj real, sin mocks, sin patch, sin monkeypatch y sin fechas fijas.
- **Mutaciones reescritas**: la primera versión tenía 10 inválidas por nombres inexistentes y 7 detenidas por guardas de producción; se reescribieron todas y el script ahora detecta los dos casos.
- **Bug CRLF del script de mutaciones**: falsos sobrevivientes por finales de línea de Windows, corregido; SHA 7e528… -> dfde27… sin diferencias de contenido con HEAD ignorando finales de línea.
- La mutación 40 prueba que /status responde 400 y no 422; la mutación natural (ampliar el Literal con "cancelado") la frena el ValueError del dominio y no una afirmación del test, así que se eligió esta. El detector acepta como afirmación pytest.raises (DID NOT RAISE) y ValidationError en los tests que validan el esquema directamente.

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
| 12 | `test_get_display_names_resolves_in_single_query` | `backend/app/repositories/users.py` | `-        stmt = select(UserModel.id, UserModel.display_name).where(UserModel.id.` | `E   AssertionError: assert {} == {UUID('000000...traciÃ³n Demo'}` |
| 13 | `test_get_appointment_history_returns_none_if_appointment_not_found` | `backend/app/services/appointments.py` | `-        return None +        return []` | `E   assert [] is None` |
| 14 | `test_get_appointment_history_ascending_order_and_reschedule_mapping` | `backend/app/services/appointments.py` | `-    changes = status_repo.list_by_appointment_id(appointment_id) +    changes =` | `E   AssertionError: assert 'confirmado' is None` |
| 15 | `test_get_appointment_history_unknown_user_leaves_changed_by_name_null` | `backend/app/services/appointments.py` | `-        changed_name = names_by_id.get(c.changed_by) +        changed_name = na` | `E   AssertionError: assert 'Usuario Ficticio' is None` |
| 16 | `test_reception_cancels_reserved_appointment` | `backend/app/api/appointments.py` | `-        auto_commit=True, +        auto_commit=False,` | `E   AssertionError: assert 1 == 2` |
| 17 | `test_admin_cancels_confirmed_appointment` | `backend/app/api/appointments.py` | `-        status=appointment.status.value, +        status="reservado",` | `E   AssertionError: assert 'reservado' == 'cancelado'` |
| 18 | `test_cancel_attended_appointment_returns_422` | `backend/app/api/appointments.py` | `-        raise DomainRejectedError(result) +        raise NotFoundError("Turno n` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 19 | `test_cancel_already_cancelled_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 20 | `test_cancel_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        return Appointment` | `E   assert 200 == 404` |
| 21 | `test_dentist_cannot_cancel_appointment_returns_403` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)), +    ` | `E   assert False` |
| 22 | `test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado` | `backend/app/api/appointments.py` | `-        duration_min=body.duration_min, +        duration_min=999,` | `E   AssertionError: {"violations":[{"code":"INVALID_DURATION","message":"La dura` |
| 23 | `test_reschedule_with_explicit_professional_chair_and_duration` | `backend/app/api/appointments.py` | `-        professional_id=body.professional_id, +        professional_id=None,` | `E   AssertionError: assert '00000000-000...-000000000001' == '00000000-000...-00` |
| 24 | `test_reschedule_professional_overlap_returns_409` | `backend/app/api/appointments.py` | `-        professional_id=body.professional_id, +        professional_id=None,` | `E   AssertionError: {"id":"232a8d26-9865-43ea-b1ee-8749fcbf993f","patientId":"00` |
| 25 | `test_reschedule_chair_overlap_returns_409` | `backend/app/api/appointments.py` | `-        chair_id=body.chair_id, +        chair_id=None,` | `E   AssertionError: {"id":"ac301b7f-a4d1-410a-96a3-09c475eb4b2f","patientId":"00` |
| 26 | `test_reschedule_inside_block_returns_409` | `backend/app/api/appointments.py` | `-        start_at=body.start_at, +        start_at=body.start_at.replace(hour=14` | `E   assert False` |
| 27 | `test_reschedule_outside_working_hours_returns_409` | `backend/app/api/appointments.py` | `-        start_at=body.start_at, +        start_at=body.start_at.replace(hour=10` | `E   AssertionError: {"id":"a3052ab2-7752-446e-b8a3-6ac47e0a722b","patientId":"00` |
| 28 | `test_reschedule_in_the_past_returns_422` | `backend/app/api/appointments.py` | `-        now=now, +        now=datetime(2000, 1, 1, tzinfo=UTC),` | `E   AssertionError: {"violations":[{"code":"OUTSIDE_WORKING_HOURS","message":"El` |
| 29 | `test_reschedule_start_at_without_timezone_returns_400` | `backend/app/api/schemas.py` | `-            raise ValueError("La fecha y hora debe incluir zona horaria.") +   ` | `E   assert 409 == 400` |
| 30 | `test_reschedule_extra_field_returns_400` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   assert 200 == 400` |
| 31 | `test_reschedule_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        return Appointment` | `E   assert 200 == 404` |
| 32 | `test_dentist_cannot_reschedule_returns_403` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT, Action.RESCHEDULE)), +` | `E   assert False` |
| 33 | `test_reschedule_terminal_state_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 34 | `test_confirm_reserved_appointment` | `backend/app/api/appointments.py` | `-        target_status=AppointmentStatus(body.to_status), +        target_status` | `E   AssertionError: {"violations":[{"code":"STATUS_CHANGE_TOO_EARLY","message":"` |
| 35 | `test_mark_attended_confirmed_appointment_with_past_start` | `backend/app/api/appointments.py` | `-    now = datetime.now(UTC) +    now = datetime(2000, 1, 1, tzinfo=UTC)` | `E   AssertionError: {"violations":[{"code":"STATUS_CHANGE_TOO_EARLY","message":"` |
| 36 | `test_mark_absent_confirmed_appointment_with_past_start` | `backend/app/api/appointments.py` | `-        target_status=AppointmentStatus(body.to_status), +        target_status` | `E   AssertionError: assert 'atendido' == 'ausente'` |
| 37 | `test_mark_attended_before_start_returns_422` | `backend/app/api/appointments.py` | `-        raise DomainRejectedError(result) +        raise NotFoundError("Turno n` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 38 | `test_double_sequential_transition_leaves_single_new_entry` | `backend/app/api/appointments.py` | `-        auto_commit=True, +        auto_commit=False,` | `E   AssertionError: {"id":"2501fac5-a927-4436-9777-d85b139014f1","patientId":"00` |
| 39 | `test_confirm_cancelled_appointment_returns_422` | `backend/app/api/appointments.py` | `+    if isinstance(result, Rejected): +        result = None` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 40 | `test_to_status_cancelado_returns_400` | `backend/app/api/errors.py` | `-    return JSONResponse(status_code=400, content={"errors": error_items}) +    ` | `E   assert 422 == 400` |
| 41 | `test_to_status_reservado_returns_400` | `backend/app/api/schemas.py` | `-    to_status: AllowedStatusChange = Field(alias="toStatus") +    to_status: st` | `E   assert 422 == 400` |
| 42 | `test_change_status_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        return Appointment` | `E   assert 200 == 404` |
| 43 | `test_dentist_changes_status_of_other_professional_returns_403_from_domain` | `backend/app/api/appointments.py` | `-        actor=permission.actor, +        actor=type(permission.actor)( +       ` | `E   AssertionError: {"id":"58f0c46a-47c6-4061-8be0-96e6ad7ec6d8","patientId":"00` |
| 44 | `test_history_ascending_with_creation_and_changed_by_name` | `backend/app/api/appointments.py` | `-    return history +    return list(reversed(history))` | `E   AssertionError: assert 'reservado' is None` |
| 45 | `test_history_reschedule_entry_has_to_reservado_and_flat_detail` | `backend/app/api/appointments.py` | `+    if history is not None: +        history = []` | `E   assert 0 == 3` |
| 46 | `test_history_nonexistent_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        return []` | `E   assert 200 == 404` |
| 47 | `test_dentist_reads_own_appointment_history_returns_200` | `backend/app/api/appointments.py` | `-        ensure_own_professional(permission, appointment.professional_id) +     ` | `E   AssertionError: {"violations":[{"code":"FORBIDDEN_OPERATION","message":"No t` |
| 48 | `test_dentist_reads_other_professional_history_returns_403` | `backend/app/api/appointments.py` | `-    if permission.scope is Scope.OWN: +    if False and permission.scope is Sco` | `E   AssertionError: [{"from":null,"to":"reservado","changedBy":"00000000-0000-00` |
| 49 | `test_reception_reads_other_professional_history_returns_200` | `backend/app/api/appointments.py` | `-        Depends(require_permission(Resource.APPOINTMENT_HISTORY, Action.READ)),` | `E   AssertionError: {"violations":[{"code":"FORBIDDEN_OPERATION","message":"No t` |
| 50 | `test_admin_reads_other_professional_history_returns_200` | `backend/app/api/appointments.py` | `-    status_code=status.HTTP_200_OK, +    status_code=status.HTTP_403_FORBIDDEN,` | `E   AssertionError: [{"from":null,"to":"reservado","changedBy":"00000000-0000-00` |
| 51 | `test_appointment_lifecycle_openapi_documentation` | `backend/app/api/appointments.py` | `-        **violation_responses(409, 422), +        **violation_responses(422),` | `E   AssertionError: assert '409' in {'200': {'content': {'application/json': {'s` |
<!-- mutaciones:fin -->
