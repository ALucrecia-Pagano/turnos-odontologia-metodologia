# Verificación de C-21 — api-horarios-y-bloqueos

## Aprobación de la autora (governance MEDIO)

> Aprobado por la autora según propuesta y respuestas del explore.
> Implementación completada con Strict TDD en todos los niveles.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 18/18 en [tasks.md](../../openspec/changes/api-horarios-y-bloqueos/tasks.md).
- Suite por defecto: [pytest-C-21.txt](pytest-C-21.txt) (866 passed, 407 deselected).
- Integración: [pytest-integration-C-21.txt](pytest-integration-C-21.txt) (407 passed, 866 deselected).
- `mypy --strict app tests`: [mypy-C-21.txt](mypy-C-21.txt) (Success: 158 source files).
- Concurrencia: [concurrencia-C-21.txt](concurrencia-C-21.txt) (5/5 corridas exitosas, 2/2 tests en cada corrida).
- Mutaciones: [mutaciones-C-21.txt](mutaciones-C-21.txt) (48/48 mutaciones hicieron fallar su test; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-21.txt](trazabilidad-C-21.txt) (48 escenarios recolectados, 0 problemas).
- Validación OpenSpec: [validate-C-21.txt](validate-C-21.txt) (`openspec validate --strict` válido).
- Línea de base: [baseline-C-21.txt](baseline-C-21.txt) (850 passed / 360 deselected; 360 integración; 148 archivos mypy).

## Artefactos

- [proposal.md](../../openspec/changes/api-horarios-y-bloqueos/proposal.md)
- [design.md](../../openspec/changes/api-horarios-y-bloqueos/design.md)
- [tasks.md](../../openspec/changes/api-horarios-y-bloqueos/tasks.md)
- [spec.md (appointment-scheduling)](../../openspec/changes/api-horarios-y-bloqueos/specs/appointment-scheduling/spec.md)
- [spec.md (working-hours-and-blocks-api)](../../openspec/changes/api-horarios-y-bloqueos/specs/working-hours-and-blocks-api/spec.md)

## Desvíos

1. **Helper único `ensure_own_professional` en `backend/app/api/deps.py` (D3)**: Se implementó un único helper parametrizado con `resource` y `action` (por defecto `Resource.WORKING_HOURS`, `Action.READ`), devolviendo 403 con código `FORBIDDEN_OPERATION` y el mensaje exacto de `PERMISSION_MESSAGES` cuando un odontólogo intenta operar sobre el horario o bloqueos de otro profesional.
2. **Inyección de `Query()` con alias para `from` y `to` en listado de bloqueos**: En `backend/app/api/blocks.py`, para que FastAPI 0.162 popule `BlocksQuery` desde query parameters respetando los alias `from` y `to` (`from_time` y `to_time`), se utilizó `Annotated[BlocksQuery, Query()]`.
3. **Manejo de triggers de append-only en fixtures de tests**: La tabla `appointment_status_change` posee un trigger que impide `DELETE` directo. Los fixtures de limpieza de tests de integración para disponibilidad utilizan `clean_database_tables` (que desactiva triggers de usuario, trunca con cascade y reactiva triggers) para garantizar aislamiento idempotente.
4. **Respuesta de endpoints 204 y mutaciones**: FastAPI prohíbe explícitamente definir `response_model` en endpoints que retornan `status_code=204`. En el test de mutación de `DELETE /blocks/{id}`, la mutación altera el código a 201 para verificar la aserción de status code sin provocar conflicto de contrato interno en FastAPI.

## Línea de base

Antes de escribir código: 850 passed (y 360 deselected); 360 passed en integración; `mypy` Success en 148 archivos (documentado en `baseline-C-21.txt`).

## Trazabilidad

Cada escenario de las specs delta `appointment-scheduling` y `working-hours-and-blocks-api` mapeado a un test unitario o de integración. `trazabilidad-C-21.py` comprueba con `pytest --collect-only` que cada test existe.

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Turno futuro fuera del horario nuevo se lista | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_lists_future_occupying_appointment_outside_new_hours` |
| 2 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Turno dentro del horario nuevo no se lista | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_ignores_appointment_inside_new_hours` |
| 3 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Turno cancelado fuera del horario no se lista | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_ignores_cancelled_appointment` |
| 4 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Turno anterior al momento actual no se lista | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_ignores_past_appointment` |
| 5 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Turno de otro profesional no se lista | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_ignores_other_professional_appointments` |
| 6 | appointment-scheduling | Turnos que quedan fuera de un horario de atención | Los turnos fuera de horario se devuelven ordenados | `tests/domain/test_working_hours.py::test_appointments_outside_working_hours_returns_appointments_ordered_by_start_and_id` |
| 7 | working-hours-and-blocks-api | Consulta del horario de atención | Recepción consulta el horario de un profesional | `tests/integration/test_api_working_hours.py::test_reception_gets_working_hours_returns_200` |
| 8 | working-hours-and-blocks-api | Consulta del horario de atención | La odontóloga consulta su propio horario | `tests/integration/test_api_working_hours.py::test_odontologist_gets_own_working_hours_returns_200` |
| 9 | working-hours-and-blocks-api | Consulta del horario de atención | La odontóloga consulta el horario de otro profesional | `tests/integration/test_api_working_hours.py::test_odontologist_gets_other_professional_working_hours_returns_403` |
| 10 | working-hours-and-blocks-api | Consulta del horario de atención | Consulta del horario sin token | `tests/integration/test_api_working_hours.py::test_get_working_hours_without_token_returns_401` |
| 11 | working-hours-and-blocks-api | Consulta del horario de atención | Consulta del horario de un profesional inexistente | `tests/integration/test_api_working_hours.py::test_get_working_hours_unknown_professional_returns_404` |
| 12 | working-hours-and-blocks-api | Reemplazo del horario de atención | El administrador reemplaza el horario de un profesional | `tests/integration/test_api_working_hours.py::test_admin_replaces_working_hours_returns_200` |
| 13 | working-hours-and-blocks-api | Reemplazo del horario de atención | La odontóloga reemplaza su propio horario | `tests/integration/test_api_working_hours.py::test_odontologist_replaces_own_working_hours_returns_200` |
| 14 | working-hours-and-blocks-api | Reemplazo del horario de atención | La odontóloga reemplaza el horario de otro profesional | `tests/integration/test_api_working_hours.py::test_odontologist_replaces_other_professional_working_hours_returns_403` |
| 15 | working-hours-and-blocks-api | Reemplazo del horario de atención | Recepción reemplaza un horario | `tests/integration/test_api_working_hours.py::test_reception_replaces_working_hours_returns_403` |
| 16 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo con lista vacía deja al profesional sin horario | `tests/integration/test_api_working_hours.py::test_replace_working_hours_with_empty_list_returns_empty` |
| 17 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo con tramos solapados responde 422 | `tests/integration/test_api_working_hours.py::test_replace_working_hours_overlapping_returns_422` |
| 18 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo con un tramo de inicio posterior al fin responde 422 | `tests/integration/test_api_working_hours.py::test_replace_working_hours_start_after_end_returns_422` |
| 19 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo con una hora mal formada responde 400 | `tests/integration/test_api_working_hours.py::test_replace_working_hours_malformed_time_returns_400` |
| 20 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo con fin a las 24:00 se acepta | `tests/integration/test_api_working_hours.py::test_replace_working_hours_end_at_24_accepted_returns_200` |
| 21 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo del horario de un profesional inexistente | `tests/integration/test_api_working_hours.py::test_replace_working_hours_unknown_professional_returns_404` |
| 22 | working-hours-and-blocks-api | Reemplazo del horario de atención | Reemplazo del horario de un profesional inactivo | `tests/integration/test_api_working_hours.py::test_replace_working_hours_inactive_professional_accepted` |
| 23 | working-hours-and-blocks-api | Turnos que quedan fuera del horario nuevo | Un turno que queda fuera del horario nuevo se informa sin cancelarlo | `tests/integration/test_api_working_hours.py::test_replace_working_hours_reports_outside_appointment_without_cancelling` |
| 24 | working-hours-and-blocks-api | Turnos que quedan fuera del horario nuevo | Un turno que sigue dentro del horario nuevo no se informa | `tests/integration/test_api_working_hours.py::test_replace_working_hours_does_not_report_appointment_inside_new_hours` |
| 25 | working-hours-and-blocks-api | Turnos que quedan fuera del horario nuevo | Un turno cancelado fuera del horario nuevo no se informa | `tests/integration/test_api_working_hours.py::test_replace_working_hours_does_not_report_cancelled_appointment` |
| 26 | working-hours-and-blocks-api | Listado de bloqueos | Recepción lista los bloqueos de un profesional | `tests/integration/test_api_blocks.py::test_reception_lists_blocks_of_professional` |
| 27 | working-hours-and-blocks-api | Listado de bloqueos | La odontóloga lista sus propios bloqueos | `tests/integration/test_api_blocks.py::test_odontologist_lists_own_blocks` |
| 28 | working-hours-and-blocks-api | Listado de bloqueos | La odontóloga lista los bloqueos de otro profesional | `tests/integration/test_api_blocks.py::test_odontologist_lists_other_professional_blocks_forbidden` |
| 29 | working-hours-and-blocks-api | Listado de bloqueos | El listado con from y to devuelve solo los bloqueos que se solapan | `tests/integration/test_api_blocks.py::test_list_blocks_with_from_and_to_filters_overlapping` |
| 30 | working-hours-and-blocks-api | Listado de bloqueos | El listado con un from sin zona horaria responde 400 | `tests/integration/test_api_blocks.py::test_list_blocks_from_without_timezone_returns_400` |
| 31 | working-hours-and-blocks-api | Listado de bloqueos | El listado de bloqueos de un profesional inexistente responde 404 | `tests/integration/test_api_blocks.py::test_list_blocks_unknown_professional_returns_404` |
| 32 | working-hours-and-blocks-api | Alta de bloqueos | La odontóloga crea un bloqueo propio sin turnos afectados | `tests/integration/test_api_blocks.py::test_odontologist_creates_own_block_without_affected_appointments` |
| 33 | working-hours-and-blocks-api | Alta de bloqueos | El administrador crea un bloqueo para cualquier profesional | `tests/integration/test_api_blocks.py::test_admin_creates_block_for_any_professional` |
| 34 | working-hours-and-blocks-api | Alta de bloqueos | La odontóloga crea un bloqueo para otro profesional | `tests/integration/test_api_blocks.py::test_odontologist_creates_block_for_other_professional_forbidden` |
| 35 | working-hours-and-blocks-api | Alta de bloqueos | Recepción crea un bloqueo | `tests/integration/test_api_blocks.py::test_reception_creates_block_forbidden` |
| 36 | working-hours-and-blocks-api | Alta de bloqueos | Un bloqueo con inicio igual al fin responde 422 | `tests/integration/test_api_blocks.py::test_block_start_equal_to_end_returns_422` |
| 37 | working-hours-and-blocks-api | Alta de bloqueos | Un bloqueo sin zona horaria responde 400 | `tests/integration/test_api_blocks.py::test_block_without_timezone_returns_400` |
| 38 | working-hours-and-blocks-api | Alta de bloqueos | Un bloqueo para un profesional inexistente responde 404 | `tests/integration/test_api_blocks.py::test_block_unknown_professional_returns_404` |
| 39 | working-hours-and-blocks-api | Turnos afectados por un bloqueo nuevo | Un bloqueo que pisa un turno reservado lo informa sin cancelarlo | `tests/integration/test_api_blocks.py::test_block_overlapping_reserved_appointment_reports_it_without_canceling` |
| 40 | working-hours-and-blocks-api | Turnos afectados por un bloqueo nuevo | Un bloqueo que pisa un turno cancelado no lo informa | `tests/integration/test_api_blocks.py::test_block_overlapping_canceled_appointment_not_reported` |
| 41 | working-hours-and-blocks-api | Eliminación de bloqueos | La odontóloga borra su propio bloqueo | `tests/integration/test_api_blocks.py::test_odontologist_deletes_own_block` |
| 42 | working-hours-and-blocks-api | Eliminación de bloqueos | El administrador borra el bloqueo de cualquier profesional | `tests/integration/test_api_blocks.py::test_admin_deletes_block_of_any_professional` |
| 43 | working-hours-and-blocks-api | Eliminación de bloqueos | La odontóloga borra el bloqueo de otro profesional | `tests/integration/test_api_blocks.py::test_odontologist_deletes_other_professional_block_forbidden` |
| 44 | working-hours-and-blocks-api | Eliminación de bloqueos | Recepción borra un bloqueo | `tests/integration/test_api_blocks.py::test_reception_deletes_block_forbidden` |
| 45 | working-hours-and-blocks-api | Eliminación de bloqueos | Borrar un bloqueo inexistente responde 404 | `tests/integration/test_api_blocks.py::test_delete_unknown_block_returns_404` |
| 46 | working-hours-and-blocks-api | Eliminación de bloqueos | Borrar un bloqueo libera el horario | `tests/integration/test_api_blocks.py::test_delete_block_frees_schedule` |
| 47 | working-hours-and-blocks-api | Bloqueos y altas de turnos serializados | Un bloqueo que espera a un alta informa el turno nuevo | `tests/integration/test_availability_concurrency.py::test_concurrent_block_waiting_for_booking_reports_new_appointment` |
| 48 | working-hours-and-blocks-api | Bloqueos y altas de turnos serializados | Un alta que espera a un bloqueo recibe BLOCKED_TIME | `tests/integration/test_availability_concurrency.py::test_concurrent_booking_waiting_for_block_receives_blocked_time` |
<!-- trazabilidad:fin -->

## Mutaciones

Comprobación por mutación sobre código de producción para verificar sensibilidad de las pruebas.

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_appointments_outside_working_hours_lists_future_occupying_appointment_outside_new_hours` | `backend/app/domain/rules/working_hours.py` | `- outside.append(appointment)`<br>`+ pass` | `AssertionError: assert [] == [Appointment(...'reservado'>)]` |
| 2 | `test_appointments_outside_working_hours_ignores_appointment_inside_new_hours` | `backend/app/domain/rules/working_hours.py` | `- if any(v.code == ViolationCode.OUTSIDE_WORKING_HOURS for v in violations):`<br>`+ if True:` | `AssertionError: assert [Appointment(...'reservado'>)] == []` |
| 3 | `test_appointments_outside_working_hours_ignores_cancelled_appointment` | `backend/app/domain/rules/working_hours.py` | `- and appointment.status in OCCUPYING_STATUSES`<br>`+ and True` | `AssertionError: assert [Appointment(...'cancelado'>)] == []` |
| 4 | `test_appointments_outside_working_hours_ignores_past_appointment` | `backend/app/domain/rules/working_hours.py` | `- and appointment.start_at >= now`<br>`+ and True` | `AssertionError: assert [Appointment(...'reservado'>)] == []` |
| 5 | `test_appointments_outside_working_hours_ignores_other_professional_appointments` | `backend/app/domain/rules/working_hours.py` | `- appointment.professional_id == professional_id`<br>`+ True` | `AssertionError: assert [Appointment(...'reservado'>)] == []` |
| 6 | `test_appointments_outside_working_hours_returns_appointments_ordered_by_start_and_id` | `backend/app/domain/rules/working_hours.py` | `- return sorted(outside, key=lambda a: (a.start_at, str(a.id)))`<br>`+ return outside` | `AssertionError: assert [Appointment(...'reservado'>)] == [Appointment(...'reservado'>)]` |
| 7 | `test_reception_gets_working_hours_returns_200` | `backend/app/api/working_hours.py` | `- status_code=status.HTTP_200_OK,`<br>`+ status_code=status.HTTP_201_CREATED,` | `assert 201 == 200` |
| 8 | `test_odontologist_gets_own_working_hours_returns_200` | `backend/app/api/working_hours.py` | `+ raise NotFoundError("Forzado")` | `assert 404 == 200` |
| 9 | `test_odontologist_gets_other_professional_working_hours_returns_403` | `backend/app/api/working_hours.py` | `- ensure_own_professional(permission, id)`<br>`+ pass` | `assert 200 == 403` |
| 10 | `test_get_working_hours_without_token_returns_401` | `backend/app/api/deps.py` | `- if credentials is None:`<br>`+ if False:` | `AttributeError: 'NoneType' object has no attribute 'credentials'` |
| 11 | `test_get_working_hours_unknown_professional_returns_404` | `backend/app/services/availability.py` | `- if prof is None:`<br>`+ if False:` | `assert 200 == 404` |
| 12 | `test_admin_replaces_working_hours_returns_200` | `backend/app/api/working_hours.py` | `- status_code=status.HTTP_200_OK,`<br>`+ status_code=status.HTTP_202_ACCEPTED,` | `assert 202 == 200` |
| 13 | `test_odontologist_replaces_own_working_hours_returns_200` | `backend/app/api/working_hours.py` | `- ensure_own_professional(permission, id)`<br>`+ raise NotFoundError("Forzado")` | `assert 404 == 200` |
| 14 | `test_odontologist_replaces_other_professional_working_hours_returns_403` | `backend/app/api/working_hours.py` | `- ensure_own_professional(permission, id)`<br>`+ pass` | `assert 200 == 403` |
| 15 | `test_reception_replaces_working_hours_returns_403` | `backend/app/api/working_hours.py` | `- Depends(require_permission(Resource.WORKING_HOURS, Action.UPDATE)),`<br>`+ Depends(require_permission(Resource.WORKING_HOURS, Action.READ)),` | `assert 200 == 403` |
| 16 | `test_replace_working_hours_with_empty_list_returns_empty` | `backend/app/services/availability.py` | `- res = repo.replace_for_professional(professional_id, slots)`<br>`+ res = repo.replace_for_professional(professional_id, slots or [WorkingHours(professional_id, 1, 540, 780)])` | `AssertionError: assert [{'end': '13:...'weekday': 1}] == []` |
| 17 | `test_replace_working_hours_overlapping_returns_422` | `backend/app/domain/rules/working_hours.py` | `- code=ViolationCode.OVERLAPPING_WORKING_HOURS,`<br>`+ code=ViolationCode.INVALID_WORKING_HOURS,` | `AssertionError: assert 'INVALID_WORKING_HOURS' == 'OVERLAPPING_WORKING_HOURS'` |
| 18 | `test_replace_working_hours_start_after_end_returns_422` | `backend/app/domain/rules/working_hours.py` | `- code=ViolationCode.INVALID_WORKING_HOURS,`<br>`+ code=ViolationCode.OVERLAPPING_WORKING_HOURS,` | `AssertionError: assert 'OVERLAPPING_WORKING_HOURS' == 'INVALID_WORKING_HOURS'` |
| 19 | `test_replace_working_hours_malformed_time_returns_400` | `backend/app/api/schemas.py` | `- if not _START_TIME_REGEX.match(v):`<br>`- raise ValueError("start debe tener formato HH:MM válido (00:00 a 23:59).")`<br>`- if not _END_TIME_REGEX.match(v):`<br>`- raise ValueError("end debe tener formato HH:MM válido (00:00 a 24:00).")` | `assert 422 == 400` |
| 20 | `test_replace_working_hours_end_at_24_accepted_returns_200` | `backend/app/api/schemas.py` | `- _END_TIME_REGEX: Final = re.compile(r"^(?:(?:[01]\d\|2[0-3]):[0-5]\d\|24:00)$")`<br>`+ _END_TIME_REGEX: Final = re.compile(r"^(?:[01]\d\|2[0-3]):[0-5]\d$")` | `assert 400 == 200` |
| 21 | `test_replace_working_hours_unknown_professional_returns_404` | `backend/app/api/working_hours.py` | `- raise NotFoundError("Profesional no encontrado.")`<br>`+ raise ValueError("Error forzado")` | `ValueError: Error forzado` |
| 22 | `test_replace_working_hours_inactive_professional_accepted` | `backend/app/api/working_hours.py` | `- if prof is None:`<br>`+ if prof is None or not prof.active:` | `assert 404 == 200` |
| 23 | `test_replace_working_hours_reports_outside_appointment_without_cancelling` | `backend/app/services/availability.py` | `- outside = appointments_outside_working_hours(professional_id, candidates, slots, tz, now)`<br>`+ outside: list[Appointment] = []` | `assert 0 == 1` |
| 24 | `test_replace_working_hours_does_not_report_appointment_inside_new_hours` | `backend/app/services/availability.py` | `- outside = appointments_outside_working_hours(professional_id, candidates, slots, tz, now)`<br>`+ outside = list(candidates)` | `AssertionError: assert [{'chairId': ...0000c1', ...}] == []` |
| 25 | `test_replace_working_hours_does_not_report_cancelled_appointment` | `backend/app/domain/rules/working_hours.py` | `- and appointment.status in OCCUPYING_STATUSES`<br>`+ and True` | `AssertionError: assert [{'chairId': ...0000c1', ...}] == []` |
| 26 | `test_reception_lists_blocks_of_professional` | `backend/app/api/blocks.py` | `- status_code=status.HTTP_200_OK,`<br>`+ status_code=status.HTTP_201_CREATED,` | `AssertionError: [{"id":"ef93e7a9-4c6a-4afd-b31f-e7ab7436dbdd","professionalId":"00000000-0000-0000-0000-000000000001","startAt":"2026-11-16T09:<linea>:<linea>Z","endAt":"2026-11-16T11:<linea>:<linea>Z` |
| 27 | `test_odontologist_lists_own_blocks` | `backend/app/api/blocks.py` | `- blocks = list_blocks(session, id, params.from_time, params.to_time)`<br>`+ blocks: tuple[Block, ...] = ()` | `assert 0 == 1` |
| 28 | `test_odontologist_lists_other_professional_blocks_forbidden` | `backend/app/api/blocks.py` | `- ensure_own_professional(permission, id)`<br>`+ pass` | `AssertionError: []` |
| 29 | `test_list_blocks_with_from_and_to_filters_overlapping` | `backend/app/repositories/blocks.py` | `- if end_at is not None:`<br>`+ if False:` | `AssertionError: assert 2 == 1` |
| 30 | `test_list_blocks_from_without_timezone_returns_400` | `backend/app/api/schemas.py` | `- if v is not None and v.tzinfo is None:`<br>`- raise ValueError("La fecha y hora debe incluir zona horaria.")`<br>`+ if False:`<br>`+ pass` | `AssertionError: []` |
| 31 | `test_list_blocks_unknown_professional_returns_404` | `backend/app/services/availability.py` | `- if prof is None:`<br>`+ if False:` | `AssertionError: []` |
| 32 | `test_odontologist_creates_own_block_without_affected_appointments` | `backend/app/api/blocks.py` | `- status_code=status.HTTP_201_CREATED,`<br>`+ status_code=status.HTTP_200_OK,` | `AssertionError: {"block":{"id":"a186548f-da78-4419-bfd2-e3c4024f87ab","professionalId":"00000000-0000-0000-0000-000000000001","startAt":"2026-11-16T12:<linea>:<linea>Z","endAt":"2026-11-16T16:<linea>:` |
| 33 | `test_admin_creates_block_for_any_professional` | `backend/app/api/blocks.py` | `- ensure_own_professional(permission, id)`<br>`+ raise NotFoundError("Forzado")` | `AssertionError: {"code":"NOT_FOUND","message":"Forzado"}` |
| 34 | `test_odontologist_creates_block_for_other_professional_forbidden` | `backend/app/api/blocks.py` | `- ensure_own_professional(permission, id)`<br>`+ pass` | `AssertionError: {"block":{"id":"557c2aae-fc1c-48b0-9ef0-d06ae7e6bc35","professionalId":"00000000-0000-0000-0000-000000000002","startAt":"2026-11-16T12:<linea>:<linea>Z","endAt":"2026-11-16T16:<linea>:` |
| 35 | `test_reception_creates_block_forbidden` | `backend/app/api/blocks.py` | `- Depends(require_permission(Resource.BLOCK, Action.CREATE)),`<br>`+ Depends(require_permission(Resource.BLOCK, Action.READ)),` | `AssertionError: {"block":{"id":"856f36d1-544f-4513-a789-8cef4d5ec58b","professionalId":"00000000-0000-0000-0000-000000000001","startAt":"2026-11-16T12:<linea>:<linea>Z","endAt":"2026-11-16T16:<linea>:` |
| 36 | `test_block_start_equal_to_end_returns_422` | `backend/app/services/availability.py` | `- if isinstance(res, Rejected):`<br>`+ if False:` | `AttributeError: 'Rejected' object has no attribute 'entity'` |
| 37 | `test_block_without_timezone_returns_400` | `backend/app/api/schemas.py` | `- if v.tzinfo is None:`<br>`- raise ValueError("La fecha y hora debe incluir zona horaria.")`<br>`+ if False:`<br>`+ pass` | `ValueError: start_at necesita zona horaria (datetime naive)` |
| 38 | `test_block_unknown_professional_returns_404` | `backend/app/api/blocks.py` | `- raise NotFoundError("Profesional no encontrado.")`<br>`+ raise ValueError("Error forzado")` | `ValueError: Error forzado` |
| 39 | `test_block_overlapping_reserved_appointment_reports_it_without_canceling` | `backend/app/services/availability.py` | `- affected_apts = repo.list_affected_appointments(res.entity)`<br>`+ affected_apts: list[Appointment] = []` | `assert 0 == 1` |
| 40 | `test_block_overlapping_canceled_appointment_not_reported` | `backend/app/domain/rules/blocks.py` | `- and appointment.status in OCCUPYING_STATUSES`<br>`+ and True` | `AssertionError: assert [{'chairId': ...0000c1', ...}] == []` |
| 41 | `test_odontologist_deletes_own_block` | `backend/app/api/blocks.py` | `- status_code=status.HTTP_200_OK,`<br>`+ status_code=status.HTTP_201_CREATED,` | `AssertionError: {"id":"f129d5d5-d2d6-4972-aefb-83dbf7aade9b","professionalId":"00000000-0000-0000-0000-000000000001","startAt":"2026-11-16T09:<linea>:<linea>Z","endAt":"2026-11-16T12:<linea>:<linea>Z"` |
| 42 | `test_admin_deletes_block_of_any_professional` | `backend/app/api/blocks.py` | `- ensure_own_professional(permission, block.professional_id, Resource.BLOCK, Action.DELETE)`<br>`+ raise NotFoundError("Forzado")` | `AssertionError: {"code":"NOT_FOUND","message":"Forzado"}` |
| 43 | `test_odontologist_deletes_other_professional_block_forbidden` | `backend/app/api/blocks.py` | `- ensure_own_professional(permission, block.professional_id, Resource.BLOCK, Action.DELETE)`<br>`+ pass` | `AssertionError: {"id":"4c315cd0-e016-4392-896c-0bc70abed1bc","professionalId":"00000000-0000-0000-0000-000000000002","startAt":"2026-11-16T09:<linea>:<linea>Z","endAt":"2026-11-16T12:<linea>:<linea>Z"` |
| 44 | `test_reception_deletes_block_forbidden` | `backend/app/api/blocks.py` | `- Depends(require_permission(Resource.BLOCK, Action.DELETE)),`<br>`+ Depends(require_permission(Resource.BLOCK, Action.READ)),` | `AssertionError: {"id":"11cb02b0-788c-4a21-b25d-79b646085058","professionalId":"00000000-0000-0000-0000-000000000001","startAt":"2026-11-16T09:<linea>:<linea>Z","endAt":"2026-11-16T12:<linea>:<linea>Z"` |
| 45 | `test_delete_unknown_block_returns_404` | `backend/app/services/availability.py` | `- if block is None:`<br>`+ if False:` | `AttributeError: 'NoneType' object has no attribute 'professional_id'` |
| 46 | `test_delete_block_frees_schedule` | `backend/app/services/availability.py` | `- deleted = repo.delete(block_id)`<br>`+ deleted = repo.get_by_id(block_id)`<br>`- if auto_commit:`<br>`- session.commit()` | `AssertionError: assert False` |
| 47 | `test_concurrent_block_waiting_for_booking_reports_new_appointment` | `backend/app/services/availability.py` | `- affected_apts = repo.list_affected_appointments(res.entity)`<br>`+ affected_apts: list[Appointment] = []` | `assert False` |
| 48 | `test_concurrent_booking_waiting_for_block_receives_blocked_time` | `backend/app/services/availability.py` | `- res = repo.create(candidate)`<br>`+ res = Ok(candidate)` | `NameError: name 'Ok' is not defined` |
<!-- mutaciones:fin -->
