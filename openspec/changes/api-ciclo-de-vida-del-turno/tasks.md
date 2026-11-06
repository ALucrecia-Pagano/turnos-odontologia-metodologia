# Tasks

> **Regla para todas las tareas de los grupos 1 a 6: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-23/<tarea>.txt`. Desde `backend/`: `.venv/Scripts/python.exe -m pytest <tests> [-m integration] > ../docs/evidencias/red-C-23/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-23/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano. Sin `unittest.mock`, `patch`, `monkeypatch` ni `dependency_overrides`. Sin `type: ignore`. Solo datos ficticios de `app/demo_data.py`. pytest se corre fuera del sandbox. No se commitea.

## 0. Precondiciones

- [ ] 0.1 Verificar que C-21 (`api-horarios-y-bloqueos`) y C-22 (`api-dar-turno`) están archivados, que `ensure_own_professional` existe donde lo dejó C-21 y que el router y los esquemas de C-22 están disponibles. Redirigir a `docs/evidencias/precondicion-C-23.txt` la salida de `openspec list` y de `ls openspec/changes/archive`. **Si alguno no está archivado, detenerse.**
- [ ] 0.2 Línea de base: pytest, pytest -m integration y mypy --strict app tests, redirigidos a `docs/evidencias/baseline-C-23.txt`. Todo tiene que estar en verde.

## 1. Esquemas

- [ ] 1.1 Tests en `backend/tests/api/test_appointment_lifecycle_schemas.py`: `StatusChangeInput` acepta solo `confirmado`, `atendido` y `ausente`; `cancelado`, `reservado` y un campo extra se rechazan. `RescheduleInput` acepta `startAt` con zona y `professionalId`/`chairId`/`durationMin` opcionales; rechaza `startAt` sin zona y campos extra (D3, D8). Implementarlos en `backend/app/api/schemas.py`.
- [ ] 1.2 Tests de `HistoryEntryResponse` y `RescheduleDetailResponse`: `from` y `reschedule` se serializan siempre, `reschedule` es `null` o el objeto plano de ocho campos y no se usa `exclude_none` (D11, C1, C2). Implementarlos en `backend/app/api/schemas.py`.

## 2. Lectura de nombres

- [ ] 2.1 Tests en `backend/tests/integration/test_user_repository.py` para `UserRepository.get_display_names(ids) -> dict[UUID, str]`: devuelve solo `display_name`, resuelve ids únicos en una sola consulta y no hace una consulta por entrada (D12, C6). Implementarlo en `backend/app/repositories/users.py`.

## 3. Servicio de historial

- [ ] 3.1 Tests en `backend/tests/integration/test_appointment_lifecycle_services.py` para `get_appointment_history(session, appointment_id)`: devuelve `None` si el turno no existe, respeta el orden ascendente de `AppointmentStatusChangeRepository`, arma `changedByName` con una sola lectura y mapea el detalle de reprogramación a los ocho campos planos (D11, D12, D13, D17). Implementarlo en `backend/app/services/appointments.py` sin `commit` ni `rollback`.
- [ ] 3.2 Test del caso sin nombre visible: `changedByName` queda `null` sin romper el resto del historial (D12). Completar el servicio.

## 4. Rutas

- [ ] 4.1 Tests de integración en `backend/tests/integration/test_api_appointment_cancel.py` para `POST /api/appointments/{id}/cancel`: cancelar desde `reservado` y `confirmado`, `422 INVALID_TRANSITION` desde `atendido` y `cancelado`, `404 "Turno no encontrado."` y `403` del odontólogo. Implementar la ruta en `backend/app/api/appointments.py` con `require_permission(APPOINTMENT, CANCEL)`, `now`/`tz` del borde, `None` → `NotFoundError` y `Rejected` → `DomainRejectedError` (D1, D2, D14, D17).
- [ ] 4.2 Tests de integración en `backend/tests/integration/test_api_appointment_reschedule.py` para `POST /api/appointments/{id}/reschedule`: éxito con y sin `professionalId`/`chairId`/`durationMin`, conservación de la duración real, vuelta a `reservado`, `409` por choque de profesional, choque de sillón, bloqueo y fuera de horario; `422` al pasado y por estado terminal; `400` por `startAt` sin zona y por campo extra; `404`; `403` del odontólogo. Implementar la ruta con `require_permission(APPOINTMENT, RESCHEDULE)` y `RescheduleInput` (D1, D8, D9, D14, D17).
- [ ] 4.3 Tests de integración en `backend/tests/integration/test_api_appointment_status.py` para `POST /api/appointments/{id}/status`: confirmar, marcar `atendido` y `ausente` con inicio pasado insertado con los repositorios y fechas relativas al reloj real (C5); `422 STATUS_CHANGE_TOO_EARLY`; `422 INVALID_TRANSITION` por mismo estado, cancelado y atendido; `400` por `cancelado` y `reservado`; `404`; `403` por propiedad del dominio. Implementar la ruta con `require_permission(APPOINTMENT, CHANGE_STATUS)`, `StatusChangeInput` y sin comparar `professional_id` en la ruta (D1, D3, D5, D14, D15, D17).
- [ ] 4.4 Tests de integración en `backend/tests/integration/test_api_appointment_history.py` para `GET /api/appointments/{id}/history`: historial ascendente, alta con `from: null`, `changedByName`, `reschedule` siempre presente y detalle plano; `404`; `403` por propiedad de la API; recepción y administración leen historial ajeno. Implementar la ruta con `require_permission(APPOINTMENT_HISTORY, READ)` e importar `ensure_own_professional` desde donde lo dejó C-21, sin crear `backend/app/api/ownership.py` (D6, D7, D11, D17, C4).
- [ ] 4.5 Verificar que las rutas usen el router protegido de C-22, que el guardián de rutas las detecte con su permiso y que ningún `commit`/`rollback` quede en la capa HTTP (D17).

## 5. OpenAPI

- [ ] 5.1 Test en `backend/tests/integration/test_appointment_lifecycle_openapi.py`: las cuatro operaciones documentan `400`, `401`, `403` y `404`; `cancel`, `reschedule` y `status` documentan `422`; `reschedule` documenta `409`; `history` no documenta `409` ni `422` de dominio; las respuestas usan los esquemas de turno y de violaciones. Implementar `response_model`, `status_code=200`, tag "Turnos" y `responses` en `backend/app/api/appointments.py` (D18).

## 6. Tests por requisito

- [ ] 6.1 Completar la cobertura de "Cancelación autorizada de turnos": todas las transiciones válidas, `INVALID_TRANSITION`, `404`, `403` por rol y ausencia de `note` en el cuerpo (D1–D4).
- [ ] 6.2 Completar la cobertura de "Reprogramación autorizada de turnos": todos los escenarios de éxito, choques, bloqueo, fuera de horario, pasado, `startAt` sin zona, campo extra, `404`, `403` y estado terminal (D8, D9).
- [ ] 6.3 Completar la cobertura de "Cambio de estado autorizado": `confirmado`, `atendido`, `ausente`, `STATUS_CHANGE_TOO_EARLY`, `INVALID_TRANSITION`, `cancelado`/`reservado` con `400`, `404` y `403` por propiedad del dominio (D3, D5, D15).
- [ ] 6.4 Completar la cobertura de "Historial de turnos" y "Permisos por propiedad del historial": orden ascendente, `from: null` en el alta, `changedByName`, `reschedule` `null` u objeto de ocho campos, entrada de reprogramación con `to: "reservado"`, `404`, `403` por propiedad y lecturas de recepción/administración (D6, D7, D11, D12, D13, C1, C2, C4).
- [ ] 6.5 Verificar el test secuencial de doble transición: primera operación `200`, segunda `422 INVALID_TRANSITION` y una sola entrada nueva de historial, sin `time.sleep` (D16).
- [ ] 6.6 Ejecutar `test_route_guards.py` y los tests de OpenAPI existentes; actualizar solo lo que C-23 agrega, sin relajar guardias ni listas de rutas (D18).

## 7. Verificación y evidencias

- [ ] 7.1 `docs/evidencias/mutaciones-C-23.py`, con la estructura de `mutaciones-C-20.py`: una mutación por cada test nuevo, siempre en el código de producción, copiando los textos del código real (el script aborta si el original no aparece exactamente una vez), restaurando en un `finally`. Salida cruda en `mutaciones-C-23.txt`. Ninguna mutación puede sobrevivir.
- [ ] 7.2 `docs/evidencias/trazabilidad-C-23.py`, con la estructura de `trazabilidad-C-20.py`: los 36 escenarios de `specs/appointments-api/spec.md` mapeados a tests, comprobados con `pytest --collect-only`. Salida en `trazabilidad-C-23.txt`, terminada en "36 escenarios, 0 problemas".
- [ ] 7.3 Evidencias completas de pytest redirigidas a `pytest-C-23.txt` y `pytest-integration-C-23.txt`, con todos los tests en verde; evidencia de tipos redirigida a `mypy-C-23.txt` con `mypy --strict app tests` sin errores.
- [ ] 7.4 `verify-C-23.md` con el formato de `verify-C-20.md`: resultados con referencias a cada `.txt`, desvíos y las tablas generadas desde `mutaciones-C-23.txt` y `trazabilidad-C-23.txt`.
- [ ] 7.5 `openspec validate api-ciclo-de-vida-del-turno --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-23.txt`.
