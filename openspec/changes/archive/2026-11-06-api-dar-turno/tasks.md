# Tasks

> **Regla para todas las tareas de los grupos 1 a 3: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-22/<tarea>.txt`. Desde `backend/`: `.venv/Scripts/python.exe -m pytest <tests> [-m integration] > ../docs/evidencias/red-C-22/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-22/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano. Sin `unittest.mock`, `patch`, `monkeypatch` ni `dependency_overrides`. Sin `type: ignore`. Solo datos ficticios de `app/demo_data.py`. pytest se corre fuera del sandbox. No se commitea.

## 0. Precondiciones

- [x] 0.1 Verificar que C-20 (`api-catalogos-y-pacientes`) está archivado (D13), que su patrón de esquemas y de tests está disponible y que C-16 y C-17 están verdes. Redirigir a `docs/evidencias/precondicion-C-22.txt` la salida de `openspec list` y de la verificación de los archivos de C-20. **Si C-20 no está archivado, detenerse.**
- [x] 0.2 Línea de base: pytest, pytest -m integration y mypy --strict app tests, redirigidos a `docs/evidencias/baseline-C-22.txt`. Todo tiene que estar en verde.

## 1. Esquemas del alta

- [x] 1.1 Tests de los esquemas en `backend/tests/api/test_appointment_schemas.py`: `startAt` con zona aceptado, `startAt` sin zona rechazado, campo extra rechazado, `durationMin` opcional aceptado, respuesta en camelCase con `startAt` y `endAt` en UTC. Implementar `AppointmentInput` y `AppointmentResponse` en `backend/app/api/schemas.py` (D2, D3). Si un test pasa de entrada, mutación obligatoria.

## 2. Ruta, dominio y errores

- [x] 2.1 Tests de integración en `backend/tests/integration/test_api_appointments.py` para los 4 escenarios de "Alta autorizada de turnos": recepción con `201`, historial persistido, administrador con `201`, odontólogo con `403 FORBIDDEN_OPERATION` y sin token con `401`. Implementar `backend/app/api/appointments.py`, el cableado de `now`, `tz` y `changed_by` (D1, D4, D10), y registrarlo bajo `protected_router` en `main.py`.
- [x] 2.2 Tests de integración para los 4 escenarios de "Duración y validación del cuerpo": `durationMin` explícito, duración por defecto de la prestación, `startAt` sin zona con `400` y campo extra con `400`. Completar el esquema y la construcción de `NewAppointmentRequest` (D2).
- [x] 2.3 Tests de integración para los 5 escenarios de "Conflictos de agenda": choque de profesional, choque de sillón, ambas violaciones juntas, fuera de horario y bloqueo. Verificar `409` y todas las violaciones. No duplicar el mapeo: lanzar `DomainRejectedError` (D5).
- [x] 2.4 Tests de integración para los 4 escenarios de "Referencias y reglas de validez": pasado, paciente inexistente, dos referencias inexistentes y profesional inactivo. Verificar `422`, `referenceKind` y que no se guardan filas (D6).
- [x] 2.5 Test de integración para el escenario "Un rechazo no deja turno ni historial": alta rechazada por `BLOCKED_TIME`, con conteo cero de turnos y de historial para la profesional (D5).
- [x] 2.6 Test de OpenAPI para el escenario "Swagger documenta los status del alta" y verificación de que `test_route_guards.py` pasa sin modificarlo. Documentar `201`, `400`, `401`, `403`, `409` y `422` en la ruta (D11).

## 3. Carrera por HTTP

- [x] 3.1 Test de integración en `backend/tests/integration/test_appointments_http_concurrency.py` para el escenario "Dos altas simultáneas del mismo hueco por HTTP": dos solicitudes con barrera, un `201`, un `409`, un solo turno y una sola entrada de historial. El test prueba el cableado de la ruta y la fila única; **no** prueba la concurrencia real, que sigue en C-17 con `pg_locks` (D9). Correrlo 5 veces seguidas y redirigir las 5 salidas a `docs/evidencias/concurrencia-C-22.txt`.

## 4. Verificación y evidencias

- [x] 4.1 `docs/evidencias/mutaciones-C-22.py`, con la estructura de `mutaciones-C-20.py`: una mutación por cada test nuevo, siempre en el código de producción, copiando los textos del código real (el script aborta si el original no aparece exactamente una vez) y restaurando en un `finally`. Salida cruda en `mutaciones-C-22.txt`. Ninguna mutación puede sobrevivir.
- [x] 4.2 `docs/evidencias/trazabilidad-C-22.py`, con la estructura de `trazabilidad-C-20.py`: los 20 escenarios de `specs/appointments-api/spec.md` mapeados a tests, comprobados con `pytest --collect-only`. Salida en `trazabilidad-C-22.txt`, terminada en "20 escenarios, 0 problemas".
- [x] 4.3 Evidencias completas de pytest redirigidas a `pytest-C-22.txt` y `pytest-integration-C-22.txt`, con todos los tests en verde.
- [x] 4.4 Evidencia de tipos redirigida a `mypy-C-22.txt`: `mypy --strict app tests` sin errores.
- [x] 4.5 `verify-C-22.md` con el formato de `verify-C-20.md`: resultados con referencias a cada `.txt`, desvíos y las tablas generadas desde `mutaciones-C-22.txt` y `trazabilidad-C-22.txt`.
- [x] 4.6 `openspec validate api-dar-turno --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-22.txt`.
