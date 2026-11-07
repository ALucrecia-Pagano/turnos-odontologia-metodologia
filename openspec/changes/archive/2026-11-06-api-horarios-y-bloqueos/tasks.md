# Tasks

> **Regla para todas las tareas de los grupos 1 a 6: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-21/<tarea>.txt`. Desde `backend/`: `.venv/Scripts/python.exe -m pytest <tests> [-m integration] > ../docs/evidencias/red-C-21/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-21/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano. Sin `unittest.mock`, `patch`, `monkeypatch` ni `dependency_overrides`. Sin `type: ignore`. Solo datos ficticios de `app/demo_data.py`. pytest se corre fuera del sandbox. No se commitea.

## 0. Precondiciones

- [x] 0.1 Verificar que C-20 (`api-catalogos-y-pacientes`) está archivado y que existe `NotFoundError` con el cuerpo `{ "code": "NOT_FOUND", "message": ... }`. Redirigir a `docs/evidencias/precondicion-C-21.txt` la salida de `openspec list` y de `grep -rn "NOT_FOUND" backend/app/api`. **Si C-20 no está archivado, detenerse.**
- [x] 0.2 Línea de base: pytest, pytest -m integration y mypy --strict app tests, redirigidos a `docs/evidencias/baseline-C-21.txt`. Todo tiene que estar en verde.

## 1. Dominio: turnos fuera de un horario

- [x] 1.1 Tests unitarios en `backend/tests/domain/test_working_hours.py` para `appointments_outside_working_hours`, uno por cada escenario de `specs/appointment-scheduling/spec.md` (6 escenarios), con fechas fijas y `now` por parámetro. Implementar la función en `backend/app/domain/rules/working_hours.py` (D5). Verificar que las guardias de pureza del dominio siguen pasando sin tocar su allowlist.

## 2. Repositorio y esquemas

- [x] 2.1 Test de integración para `BlockRepository.list_by_professional_in_range` (solapamiento semiabierto con `[from, to)`, extremo abierto con un solo filtro, orden por inicio) e implementarlo en `backend/app/repositories/blocks.py` (D11).
- [x] 2.2 Tests de los esquemas: tramo `HH:MM` válido, `"24:00"` aceptado como fin, `"25:00"` rechazado, `"24:00"` rechazado como inicio, `extra="forbid"`, bloqueo con zona obligatoria, filtros `from`/`to` con zona obligatoria, resumen de turno afectado en camelCase (D4, D7). Implementarlos en `backend/app/api/schemas.py`.

## 3. Servicio y propiedad

- [x] 3.1 Tests de integración de `backend/app/services/availability.py`: consulta, reemplazo con lista vacía, 404 del profesional inexistente, profesional inactivo permitido, `appointmentsOutsideHours` con la ventana de 90 días (D7, D8, D13), alta de bloqueo con `affectedAppointments`, borrado con el bloqueo devuelto y 404 del inexistente. Implementar el servicio con commit explícito y el lock de la fila del profesional en `replace_working_hours` y `create_block` (D9, D10).
- [x] 3.2 Tests del helper `ensure_own_professional`: el odontólogo sobre su profesional pasa, sobre otro da 403 `FORBIDDEN_OPERATION` con el mensaje de la celda; recepción y administrador (`Scope.ALL`) pasan siempre (D3). Implementarlo en `backend/app/api/`.

## 4. Routers de horarios

- [x] 4.1 Tests de integración para `GET /api/professionals/{id}/working-hours`: los 5 escenarios del requisito "Consulta del horario de atención". Implementar `backend/app/api/working_hours.py` y registrarlo en `main.py`.
- [x] 4.2 Tests de integración para `PUT /api/professionals/{id}/working-hours`: los 11 escenarios del requisito "Reemplazo del horario de atención" y los 3 de "Turnos que quedan fuera del horario nuevo". Completar el router.

## 5. Routers de bloqueos

- [x] 5.1 Tests de integración para `GET /api/professionals/{id}/blocks`: los 6 escenarios del requisito "Listado de bloqueos". Implementar `backend/app/api/blocks.py` y registrarlo en `main.py`.
- [x] 5.2 Tests de integración para `POST /api/professionals/{id}/blocks`: los 7 escenarios de "Alta de bloqueos" y los 2 de "Turnos afectados por un bloqueo nuevo".
- [x] 5.3 Tests de integración para `DELETE /api/blocks/{block_id}`: los 6 escenarios de "Eliminación de bloqueos", incluido el de liberar el horario con `book_appointment`.

## 6. Concurrencia

- [x] 6.1 Dos tests de concurrencia en `backend/tests/integration/test_availability_concurrency.py`, uno por escenario del requisito "Bloqueos y altas de turnos serializados", con el patrón de `test_appointment_concurrency.py` (dos sesiones en hilos, `pg_locks`, `SET lock_timeout`, sin `time.sleep`). Correrlos 5 veces seguidas y redirigir las 5 salidas a `docs/evidencias/concurrencia-C-21.txt`.

## 7. Verificación y evidencias

- [x] 7.1 Swagger: comprobar con un test que las 5 rutas aparecen con sus tags y documentan 400, 403, 404 y 422 donde corresponde, y que `test_route_guards.py` de C-19 pasa sin modificarlo.
- [x] 7.2 `docs/evidencias/mutaciones-C-21.py`, con la estructura de `mutaciones-C-20.py`: una mutación por cada test nuevo, siempre en el código de producción, copiando los textos del código real (el script aborta si el original no aparece exactamente una vez), restaurando en un `finally`. Salida cruda en `mutaciones-C-21.txt`. Ninguna mutación puede sobrevivir.
- [x] 7.3 `docs/evidencias/trazabilidad-C-21.py`, con la estructura de `trazabilidad-C-20.py`: los 48 escenarios del change (6 de `appointment-scheduling` y 42 de `working-hours-and-blocks-api`) mapeados a tests, comprobados con `pytest --collect-only`. Salida en `trazabilidad-C-21.txt`, terminada en "48 escenarios, 0 problemas".
- [x] 7.4 Evidencias redirigidas a archivo: `pytest-C-21.txt`, `pytest-integration-C-21.txt` y `mypy-C-21.txt`. `verify-C-21.md` con el formato de `verify-C-20.md`: resultados con referencias a cada `.txt`, desvíos, y las tablas generadas desde `mutaciones-C-21.txt` y `trazabilidad-C-21.txt`.
- [x] 7.5 `openspec validate api-horarios-y-bloqueos --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-21.txt`.
