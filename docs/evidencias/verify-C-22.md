# Verificación de C-22 — api-dar-turno

## Aprobación de la autora (governance MEDIO)

> Aprobado por la autora según propuesta y respuestas del explore (D1 a D13).
> Implementación completada con Strict TDD en todos los niveles.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 16/16 en [tasks.md](../../openspec/changes/api-dar-turno/tasks.md).
- Suite por defecto: [pytest-C-22.txt](pytest-C-22.txt) (872 passed, 426 deselected).
- Integración: [pytest-integration-C-22.txt](pytest-integration-C-22.txt) (426 passed, 872 deselected).
- `mypy --strict app tests`: [mypy-C-22.txt](mypy-C-22.txt) (Success: no issues found in 163 source files).
- Mutaciones: [mutaciones-C-22.txt](mutaciones-C-22.txt) (25/25 mutaciones hicieron fallar su test; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-22.txt](trazabilidad-C-22.txt) (20 escenarios recolectados, 0 problemas).
- Concurrencia HTTP: [concurrencia-C-22.txt](concurrencia-C-22.txt) (5 corridas consecutivas en verde).
- Validación OpenSpec: [validate-C-22.txt](validate-C-22.txt) (`openspec validate --strict` válido).
- Línea de base: [baseline-C-22.txt](baseline-C-22.txt) (866 passed / 407 deselected; 407 integración; 158 archivos mypy).

## Artefactos

- [proposal.md](../../openspec/changes/api-dar-turno/proposal.md)
- [design.md](../../openspec/changes/api-dar-turno/design.md)
- [tasks.md](../../openspec/changes/api-dar-turno/tasks.md)
- [spec.md (appointments-api)](../../openspec/changes/api-dar-turno/specs/appointments-api/spec.md)

## Línea de base

Antes de escribir código: 866 passed (y 407 deselected); 407 passed en integración; `mypy` Success en 158 archivos (documentado en `baseline-C-22.txt`).

## Concurrencia

5 corridas consecutivas del test de carrera HTTP en `test_appointments_http_concurrency.py`, todas exitosas (documentado en `concurrencia-C-22.txt`).

## Desvíos

- **D8 y D13 (fechas relativas al reloj del sistema)**: en los tests de integración y concurrencia se utilizaron fechas calculadas dinámicamente relativas al momento de ejecución (primer lunes a 7 o más días, "lunes futuro L") sin emplear mocks, monkeypatch, patch ni fechas fijas pasadas.
- **Trigger append-only en AppointmentStatusChangeModel**: en la fixture de limpieza `clean_database_tables` (o teardown de tests), para permitir el truncate/clean se desactiva y reactiva temporalmente el trigger `trg_appointment_history_append_only` dentro de la transacción de limpieza, manteniendo la inmutabilidad durante la ejecución de los casos de prueba.

## Trazabilidad

Cada escenario de la spec delta `appointments-api` mapeado a un test unitario o de integración. `trazabilidad-C-22.py` comprueba con `pytest --collect-only` que cada test existe.

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | appointments-api | Alta autorizada de turnos | Recepción da un turno válido | `tests/integration/test_api_appointments.py::test_reception_creates_valid_appointment` |
| 2 | appointments-api | Alta autorizada de turnos | El administrador da un turno válido | `tests/integration/test_api_appointments.py::test_admin_creates_valid_appointment` |
| 3 | appointments-api | Alta autorizada de turnos | El odontólogo intenta dar un turno | `tests/integration/test_api_appointments.py::test_doctor_cannot_create_appointment_forbidden` |
| 4 | appointments-api | Alta autorizada de turnos | Alta sin token | `tests/integration/test_api_appointments.py::test_create_appointment_without_token_unauthorized` |
| 5 | appointments-api | Duración y validación del cuerpo | durationMin explícito se usa en lugar de la duración de la prestación | `tests/integration/test_api_appointments.py::test_explicit_duration_min_overrides_service_default` |
| 6 | appointments-api | Duración y validación del cuerpo | Sin durationMin se usa la duración de la prestación | `tests/integration/test_api_appointments.py::test_default_service_duration_used_when_duration_min_omitted` |
| 7 | appointments-api | Duración y validación del cuerpo | startAt sin zona horaria responde 400 | `tests/integration/test_api_appointments.py::test_start_at_without_timezone_returns_400` |
| 8 | appointments-api | Duración y validación del cuerpo | Un campo extra responde 400 | `tests/integration/test_api_appointments.py::test_extra_field_in_body_returns_400` |
| 9 | appointments-api | Conflictos de agenda | Choque de profesional | `tests/integration/test_api_appointments.py::test_agenda_conflict_professional_overlap` |
| 10 | appointments-api | Conflictos de agenda | Choque de sillón | `tests/integration/test_api_appointments.py::test_agenda_conflict_chair_overlap` |
| 11 | appointments-api | Conflictos de agenda | Choque de profesional y sillón | `tests/integration/test_api_appointments.py::test_agenda_conflict_professional_and_chair_overlap` |
| 12 | appointments-api | Conflictos de agenda | Fuera de horario | `tests/integration/test_api_appointments.py::test_agenda_conflict_outside_working_hours` |
| 13 | appointments-api | Conflictos de agenda | En un bloqueo | `tests/integration/test_api_appointments.py::test_agenda_conflict_blocked_time` |
| 14 | appointments-api | Referencias y reglas de validez | En el pasado | `tests/integration/test_api_appointments.py::test_validity_rule_in_the_past` |
| 15 | appointments-api | Referencias y reglas de validez | Paciente inexistente | `tests/integration/test_api_appointments.py::test_validity_rule_unknown_patient` |
| 16 | appointments-api | Referencias y reglas de validez | Dos referencias inexistentes | `tests/integration/test_api_appointments.py::test_validity_rule_two_unknown_references` |
| 17 | appointments-api | Referencias y reglas de validez | Profesional inactivo | `tests/integration/test_api_appointments.py::test_validity_rule_inactive_professional` |
| 18 | appointments-api | Atomicidad y cableado del alta | Un rechazo no deja turno ni historial | `tests/integration/test_api_appointments.py::test_rejection_leaves_no_appointment_nor_history` |
| 19 | appointments-api | Atomicidad y cableado del alta | Dos altas simultáneas del mismo hueco por HTTP | `tests/integration/test_appointments_http_concurrency.py::test_two_concurrent_http_appointments_produce_single_slot` |
| 20 | appointments-api | Documentación OpenAPI del alta | Swagger documenta los status del alta | `tests/api/test_appointment_openapi.py::test_appointment_create_in_openapi` |
<!-- trazabilidad:fin -->

## Mutaciones

Comprobación por mutación sobre código de producción para verificar sensibilidad de las pruebas.

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_appointment_input_start_at_with_tz_accepted` | `backend/app/api/schemas.py` | `- if v.tzinfo is None:`<br>`+ if v.tzinfo is not None:` | `pydantic_core._pydantic_core.ValidationError: 1 validation error for AppointmentInput` |
| 2 | `test_appointment_input_start_at_without_tz_rejected` | `backend/app/api/schemas.py` | `- if v.tzinfo is None:`<br>`+ if False and v.tzinfo is None:` | `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 3 | `test_appointment_input_extra_field_forbidden` | `backend/app/api/schemas.py` | `- model_config = ConfigDict(populate_by_name=True, extra="forbid")`<br>`+ model_config = ConfigDict(populate_by_name=True, extra="ignore")` | `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 4 | `test_appointment_input_optional_duration_min` | `backend/app/api/schemas.py` | `- duration_min: int \| None = Field(default=None, alias="durationMin")`<br>`+ duration_min: int = Field(alias="durationMin")` | `pydantic_core._pydantic_core.ValidationError: 1 validation error for AppointmentInput` |
| 5 | `test_appointment_response_camelcase_and_utc` | `backend/app/api/schemas.py` | `- patient_id: UUID = Field(serialization_alias="patientId")`<br>`+ patient_id: UUID = Field(serialization_alias="patient_id")` | `AssertionError: assert {'chairId': '...00000c1', ...} == {'chairId': '...00000c1', ...}` |
| 6 | `test_appointment_create_in_openapi` | `backend/app/api/appointments.py` | `- **violation_responses(409, 422),`<br>`+ **violation_responses(409),` | `AssertionError: assert '422' in {'201': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/AppointmentResponse'}}}, 'descripti... '#/components/schemas/ViolationResponseSchema'` |
| 7 | `test_reception_creates_valid_appointment` | `backend/app/api/appointments.py` | `- status_code=status.HTTP_201_CREATED,`<br>`+ status_code=status.HTTP_200_OK,` | `AssertionError: {"id":"cc205c7a-fca3-460a-ab1d-c4b878588ea7","patientId":"00000000-0000-0000-0000-0000000000c1","professionalId":"00000000-0000-0000-0000-000000000001","chairId":"00000000-0000-0000-00` |
| 8 | `test_admin_creates_valid_appointment` | `backend/app/api/appointments.py` | `- professional_id=body.professional_id,`<br>`+ professional_id=uuid4(),` | `AssertionError: {"violations":[{"code":"UNKNOWN_REFERENCE","message":"El profesional indicado no existe (id 0c7232aa-05d7-4588-ba6b-97fe45f36c42).","referenceKind":"PROFESSIONAL"}]}` |
| 9 | `test_doctor_cannot_create_appointment_forbidden` | `backend/app/api/appointments.py` | `- Depends(require_permission(Resource.APPOINTMENT, Action.CREATE)),`<br>`+ Depends(require_permission(Resource.APPOINTMENT, Action.READ)),` | `KeyError: (<Resource.APPOINTMENT: 'appointment'>, <Action.READ: 'read'>)` |
| 10 | `test_create_appointment_without_token_unauthorized` | `backend/app/api/errors.py` | `- status_code=401,`<br>`+ status_code=403,` | `AssertionError: {"code":"INVALID_TOKEN","message":"La sesión venció o no es válida. Inicie sesión de nuevo."}` |
| 11 | `test_explicit_duration_min_overrides_service_default` | `backend/app/api/appointments.py` | `- duration_min=body.duration_min,`<br>`+ duration_min=None,` | `AssertionError: assert '2026-11-16T13:30:00Z' == '2026-11-16T13:45:00Z'` |
| 12 | `test_default_service_duration_used_when_duration_min_omitted` | `backend/app/api/appointments.py` | `- duration_min=body.duration_min,`<br>`+ duration_min=body.duration_min or 15,` | `AssertionError: assert '2026-11-16T13:15:00Z' == '2026-11-16T14:00:00Z'` |
| 13 | `test_start_at_without_timezone_returns_400` | `backend/app/api/errors.py` | `- return JSONResponse(status_code=400, content={"errors": error_items})`<br>`+ return JSONResponse(status_code=422, content={"errors": error_items})` | `AssertionError: {"errors":[{"field":"startAt","type":"value_error","message":"Dato inválido."}]}` |
| 14 | `test_extra_field_in_body_returns_400` | `backend/app/api/schemas.py` | `- model_config = ConfigDict(populate_by_name=True, extra="forbid")`<br>`+ model_config = ConfigDict(populate_by_name=True, extra="allow")` | `AssertionError: {"id":"1146d79f-0d3b-411e-b58e-3ccb735ab0de","patientId":"00000000-0000-0000-0000-0000000000c1","professionalId":"00000000-0000-0000-0000-000000000001","chairId":"00000000-0000-0000-00` |
| 15 | `test_agenda_conflict_professional_overlap` | `backend/app/api/errors.py` | `- ViolationCode.PROFESSIONAL_OVERLAP: 409,`<br>`+ ViolationCode.PROFESSIONAL_OVERLAP: 422,` | `AssertionError: {"violations":[{"code":"PROFESSIONAL_OVERLAP","message":"Dra. Ficticia Uno ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 3956eb1d-8ee8-4906-b0c7-1a0f341b975e)` |
| 16 | `test_agenda_conflict_chair_overlap` | `backend/app/api/errors.py` | `- ViolationCode.CHAIR_OVERLAP: 409,`<br>`+ ViolationCode.CHAIR_OVERLAP: 422,` | `AssertionError: {"violations":[{"code":"CHAIR_OVERLAP","message":"Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno 2d5e617d-4eb6-4d4e-8ef6-cf0e80a9a42c).","conf` |
| 17 | `test_agenda_conflict_professional_and_chair_overlap` | `backend/app/api/errors.py` | `- "violations": [serialize_violation(v) for v in exc.rejected.violations]`<br>`+ "violations": [serialize_violation(exc.rejected.violations[0])] if exc.rejected.violations else []` | `AssertionError: assert 'CHAIR_OVERLAP' in ['PROFESSIONAL_OVERLAP']` |
| 18 | `test_agenda_conflict_outside_working_hours` | `backend/app/api/errors.py` | `- ViolationCode.OUTSIDE_WORKING_HOURS: 409,`<br>`+ ViolationCode.OUTSIDE_WORKING_HOURS: 422,` | `AssertionError: {"violations":[{"code":"OUTSIDE_WORKING_HOURS","message":"El turno de 18:00 a 18:30 (hora local) queda fuera del horario de atención: Dr. Ficticio Dos atiende el lunes de 09:00 a 13:00` |
| 19 | `test_agenda_conflict_blocked_time` | `backend/app/api/errors.py` | `- ViolationCode.BLOCKED_TIME: 409,`<br>`+ ViolationCode.BLOCKED_TIME: 422,` | `AssertionError: {"violations":[{"code":"BLOCKED_TIME","message":"El turno de 10:00 a 10:30 (hora local) se superpone con un bloqueo de agenda: Dra. Ficticia Uno tiene la agenda bloqueada del 16/11/202` |
| 20 | `test_validity_rule_in_the_past` | `backend/app/api/errors.py` | `- ViolationCode.IN_THE_PAST: 422,`<br>`+ ViolationCode.IN_THE_PAST: 409,` | `AssertionError: {"violations":[{"code":"IN_THE_PAST","message":"El inicio del turno (05/11/2026 10:00, hora local) es anterior al momento actual (06/11/2026 22:23:34, hora local): no se pueden dar tur` |
| 21 | `test_validity_rule_unknown_patient` | `backend/app/api/errors.py` | `- ViolationCode.UNKNOWN_REFERENCE: 422,`<br>`+ ViolationCode.UNKNOWN_REFERENCE: 404,` | `AssertionError: {"violations":[{"code":"UNKNOWN_REFERENCE","message":"El paciente indicado no existe (id 00000000-0000-0000-0000-0000000000c9).","referenceKind":"PATIENT"}]}` |
| 22 | `test_validity_rule_two_unknown_references` | `backend/app/api/schemas.py` | `- reference_kind=v.reference_kind,`<br>`+ reference_kind=None,` | `AssertionError: assert 'PATIENT' in {None}` |
| 23 | `test_validity_rule_inactive_professional` | `backend/app/api/errors.py` | `- ViolationCode.INACTIVE_REFERENCE: 422,`<br>`+ ViolationCode.INACTIVE_REFERENCE: 409,` | `AssertionError: {"violations":[{"code":"INACTIVE_REFERENCE","message":"El profesional indicado está inactivo (id 00000000-0000-0000-0000-000000000002).","referenceKind":"PROFESSIONAL"}]}` |
| 24 | `test_rejection_leaves_no_appointment_nor_history` | `backend/app/api/appointments.py` | `- raise DomainRejectedError(result)`<br>`+ return AppointmentResponse(`<br>`+ id=uuid4(),`<br>`+ patient_id=body.patient_id,`<br>`+ professional_id=body.professional_id,`<br>`+ chair_id=body.chair_id,`<br>`+ service_id=body.service_id,`<br>`+ start_at="2026-01-01T00:00:00Z",`<br>`+ end_at="2026-01-01T00:30:00Z",`<br>`+ status="reservado",`<br>`+ )` | `AssertionError: {"id":"f6630c25-4430-4bee-a1a8-4318209b746d","patientId":"00000000-0000-0000-0000-0000000000c1","professionalId":"00000000-0000-0000-0000-000000000001","chairId":"00000000-0000-0000-00` |
| 25 | `test_two_concurrent_http_appointments_produce_single_slot` | `backend/app/api/appointments.py` | `- auto_commit=True,`<br>`+ auto_commit=False,` | `assert [201, 201] == [201, 409]` |
<!-- mutaciones:fin -->
