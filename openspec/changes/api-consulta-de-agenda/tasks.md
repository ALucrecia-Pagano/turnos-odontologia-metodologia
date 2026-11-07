# Tasks

> **Regla para todas las tareas de los grupos 1 a 6: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-24/<tarea>.txt`. Desde `backend/`: `.venv/Scripts/python.exe -m pytest <tests> [-m integration] > ../docs/evidencias/red-C-24/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-24/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano. Sin `unittest.mock`, `patch`, `monkeypatch` ni `dependency_overrides`. Sin `type: ignore`. Solo datos ficticios de `app/demo_data.py`. pytest se corre fuera del sandbox. No se commitea.

## 0. Precondiciones

- [ ] 0.1 Verificar que C-21 (`api-horarios-y-bloqueos`), C-22 (`api-dar-turno`) y C-23 (`api-ciclo-de-vida-del-turno`) están archivados y verdes; C-23 es obligatorio porque los tests cancelan turnos con `POST /api/appointments/{id}/cancel`. Redirigir a `docs/evidencias/precondicion-C-24.txt` la salida de `openspec list` y de `ls openspec/changes/archive`. **Si C-21, C-22 o C-23 no está archivado, detenerse (C3).**
- [ ] 0.2 Línea de base: pytest, pytest -m integration y mypy --strict app tests, redirigidos a `docs/evidencias/baseline-C-24.txt`. Todo tiene que estar en verde.

## 1. Esquemas

- [ ] 1.1 Tests en `backend/tests/api/test_agenda_schemas.py` para `AgendaQuery`: `from`/`to` obligatorios y fechas locales estrictas, `to` inclusivo, máximo de 31 días, `to < from`, alias `from`/`to`/`professionalId`/`chairId`, `professionalId`/`chairId` UUID opcionales, `extra="forbid"` y `model_dump(by_alias=True)`. Cubrir `invalid_date_format`, `invalid_range_order`, `invalid_range_length`, `missing`, `uuid_parsing` y `extra_forbidden` (D2, D3, D12, C1). Implementar `AgendaQuery` en `backend/app/api/schemas.py`.
- [ ] 1.2 Tests de `AgendaAppointmentResponse`, `AgendaWorkingHoursResponse` y `AgendaResponse`: camelCase, nombres enriquecidos, `startAt`/`endAt` UTC con `Z`, `status`, `workingHours` con `start`/`end` `HH:MM` incluido `24:00`, `blocks` reutilizando `BlockResponse`, `from`/`to`/`timezone` en el sobre y serialización con `by_alias=True`. Implementarlos en `backend/app/api/schemas.py` (D4, D5, D13).
- [ ] 1.3 Agregar `invalid_date_format`, `invalid_range_order` e `invalid_range_length` a `MALFORMED_MESSAGES` en `backend/app/api/errors.py` y verificar que el handler devuelve `{ "errors": [{field, type, message}] }` con `400` (D12, C1).

## 2. Repositorios

- [ ] 2.1 Tests en `backend/tests/integration/test_agenda_repositories.py` para `AppointmentWithNames`, `AppointmentRepository.list_for_agenda_in_range(start_at, end_at, professional_id=None, chair_id=None)` y `get_with_names(id)`: joins con paciente, profesional, sillón y prestación, predicado semiabierto, filtros opcionales combinados, orden `(start_at, id)` y `None` si el id no existe (D10, D8). Implementarlos en `backend/app/repositories/appointment.py`.
- [ ] 2.2 Tests para `BlockRepository.list_in_range(start_at, end_at, professional_id=None)`: solapamiento semiabierto, filtro opcional de profesional, bloqueos que cruzan la medianoche y orden `(start_at, id)` (D6, D8). Implementarlo en `backend/app/repositories/blocks.py` sin romper `list_by_professional_in_range` de C-21.

## 3. Servicio

- [ ] 3.1 Tests en `backend/tests/integration/test_agenda_service.py` para `get_agenda(session, from_date, to_date, professional_id, chair_id, tz)` y `get_agenda_appointment(session, identifier)`: medianoches locales con `ZoneInfo`, mapeo de `AppointmentWithNames` a `AgendaAppointment`, horarios filtrados por profesional, bloqueos por rango, ventana `from`/`to` y `None` para un id inexistente; sin `commit` ni `rollback` (D11, D13). Implementarlos en `backend/app/services/agenda.py`.

## 4. Rutas

- [ ] 4.1 Tests de integración en `backend/tests/integration/test_api_agenda.py` para `GET /api/agenda`: sobre completo, día y semana, filtros por profesional y sillón, combinados, id inexistente, `chairId` que no filtra horarios ni bloqueos, cancelados con estado, orden, rango que cruza semanas y meses, y el odontólogo viendo turnos de otro profesional. Implementar la ruta en `backend/app/api/agenda.py` con `Annotated[AgendaQuery, Query()]`, `require_permission(APPOINTMENT, READ_AGENDA)`, `ZoneInfo(settings.app_timezone)` y `response_model=AgendaResponse` (D1, D3–D9, D14).
- [ ] 4.2 Tests de integración en `backend/tests/integration/test_api_agenda_midnight.py` para el borde de medianoche: reemplazar antes el horario semanal de P1 por `PUT /api/professionals/{id}/working-hours` con un tramo del lunes que termina en `"24:00"` y un tramo del martes que empieza en `"00:00"`; crear con `POST /api/appointments` el turno 23:30–00:00 del lunes L y el 00:00–00:30 del martes L+1; verificar cada uno solo en su día y un bloqueo que cruza la medianoche en los dos días (D8, D16, C2).
- [ ] 4.3 Tests de integración en `backend/tests/integration/test_api_agenda_validation.py` para los `400` de `GET /api/agenda`: falta `from`, falta `to`, formato inválido, `to < from`, más de 31 días, UUID malformado de `professionalId` y de `chairId`, parámetro de query desconocido y `401` sin token (D2, D3, D12, C1).
- [ ] 4.4 Tests de integración en `backend/tests/integration/test_api_appointment_detail.py` para `GET /api/appointments/{id}`: `200` enriquecido, `404 "Turno no encontrado."`, `400` por UUID malformado, `401` sin token y el odontólogo leyendo un turno ajeno. Implementar la ruta en `backend/app/api/appointments.py` con `require_permission(APPOINTMENT, READ_AGENDA)` y `NotFoundError("Turno no encontrado.")` (D1, D9, D17).
- [ ] 4.5 Registrar el router de agenda en `backend/app/main.py` y verificar que `test_route_guards.py` detecta las dos rutas nuevas con su permiso y que ningún `commit`/`rollback` queda en la capa HTTP (D17).

## 5. OpenAPI

- [ ] 5.1 Test en `backend/tests/integration/test_agenda_openapi.py`: `/api/agenda` documenta `400`, `401`, `403`, los parámetros `from`/`to` requeridos y `professionalId`/`chairId` opcionales, y `$ref` a `AgendaResponse`/`AgendaAppointmentResponse`; `/api/appointments/{id}` documenta `400`, `401`, `403`, `404` y `$ref` a `AgendaAppointmentResponse`. Implementar `response_model`, `status_code=200`, tags "Agenda"/"Turnos" y `responses` en `backend/app/api/agenda.py` y `backend/app/api/appointments.py` (D17).

## 6. Tests por requisito

- [ ] 6.1 Completar la cobertura de "Parámetros y validación de la agenda": los nueve escenarios de `400`/`401` con `field`, `type` y `message` (D2, D3, D12, C1).
- [ ] 6.2 Completar la cobertura de "Sobre de respuesta de la agenda": día, semana, rango de ocho días que cruza semanas y rango de 31 días que cruza meses (D2, D4).
- [ ] 6.3 Completar la cobertura de "Filtros y visibilidad de la agenda": profesional, sillón, combinados, inexistentes, `chairId` que no filtra horarios/bloqueos y odontólogo viendo a otro profesional (D3, D6, D9).
- [ ] 6.4 Completar la cobertura de "Horarios de atención del rango": plantilla de todos los profesionales y filtro por profesional, sin filtro por sillón (D5).
- [ ] 6.5 Completar la cobertura de "Bloqueos del rango": motivo, bloqueo que empieza antes, filtro por profesional y bloqueo que cruza la medianoche en los dos días (D6, D8).
- [ ] 6.6 Completar la cobertura de "Estados y orden de la agenda": cancelados con `status` y orden estable de turnos, bloqueos y horarios (D7).
- [ ] 6.7 Completar la cobertura de "Borde de medianoche de los turnos": turno 23:30–00:00 solo en su día y turno 00:00–00:30 solo en el suyo, con el horario reemplazado por `PUT` (D8, D16, C2).
- [ ] 6.8 Completar la cobertura de "Consulta de un turno por id": `200` enriquecido, `404`, `400`, `401` y odontólogo leyendo un turno ajeno (D9, D17).

## 7. Verificación y evidencias

- [ ] 7.1 `docs/evidencias/mutaciones-C-24.py`, con la estructura de `mutaciones-C-20.py` y **una mutación por cada test nuevo**, siempre en el código de producción, copiando los textos del código real (el script aborta si el original no aparece exactamente una vez), restaurando en un `finally`. Salida cruda en `mutaciones-C-24.txt`. Ninguna mutación puede sobrevivir.
- [ ] 7.2 `docs/evidencias/trazabilidad-C-24.py`, con la estructura de `trazabilidad-C-20.py`: los 34 escenarios de las dos specs (29 de `agenda-api` y 5 de `appointments-api`) mapeados a tests, comprobados con `pytest --collect-only`. Salida en `trazabilidad-C-24.txt`, terminada en "34 escenarios, 0 problemas".
- [ ] 7.3 Evidencias completas de pytest redirigidas a `pytest-C-24.txt` y `pytest-integration-C-24.txt`, con todos los tests en verde; evidencia de tipos redirigida a `mypy-C-24.txt` con `mypy --strict app tests` sin errores.
- [ ] 7.4 `verify-C-24.md` con el formato de `verify-C-20.md`: resultados con referencias a cada `.txt`, desvíos y las tablas generadas desde `mutaciones-C-24.txt` y `trazabilidad-C-24.txt`.
- [ ] 7.5 `openspec validate api-consulta-de-agenda --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-24.txt`.
