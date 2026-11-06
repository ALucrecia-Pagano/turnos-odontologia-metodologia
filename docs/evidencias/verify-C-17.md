# Verificación de C-17 — persistencia-turnos-e-historial

## Resultado

- Tareas completadas: 16/16 (incluyendo la tarea 2.4 de protección contra TRUNCATE).
- Suite por defecto: **673 passed, 61 deselected in 6.97s**.
- Integración: **61 passed, 673 deselected in 11.57s** (incluyendo los tests nuevos de persistencia, concurrencia, downgrade -1 de migración 04 y downgrade -1 de migración 05).
- Mypy estricto: **Success: no issues found in 80 source files**.
- Alembic: ciclo `upgrade head`, `current`, `downgrade -1`, `current`, `upgrade head` y `current` final en `20261105_05_historial_sin_truncate (head)`.
- Concurrencia real multi-conexión: 5 ejecuciones consecutivas de la suite de concurrencia completa (3 tests: profesional, sillón, transición), todas 100% exitosas sin intermitencias y sin uso de `time.sleep` (sincronizadas vía sondeo en `pg_locks` con timeout acotado y `SET lock_timeout = '5s'`).
- OpenSpec estricto: `Change 'persistencia-turnos-e-historial' is valid`.
- Higiene git: `git diff --check` limpio (código de salida 0).

Los artefactos del change están ubicados en:
- [proposal.md](../../openspec/changes/persistencia-turnos-e-historial/proposal.md)
- [design.md](../../openspec/changes/persistencia-turnos-e-historial/design.md)
- [tasks.md](../../openspec/changes/persistencia-turnos-e-historial/tasks.md)
- [spec.md](../../openspec/changes/persistencia-turnos-e-historial/specs/database-infrastructure/spec.md)

Las salidas completas están en:
- [pytest-C-17.txt](pytest-C-17.txt)
- [pytest-integration-C-17.txt](pytest-integration-C-17.txt)
- [mypy-C-17.txt](mypy-C-17.txt)
- [alembic-C-17.txt](alembic-C-17.txt)

---

## Trazabilidad: 18/18 escenarios

Todos los nombres corresponden a funciones reales existentes en `backend/tests/integration/` comprobadas mediante `git grep -c "def <nombre>"` con resultado 1 para cada una.

| Nº | Escenario de la spec | Test automático (nombre real en código) | Archivo |
|---|---|---|---|
| 1 | Alta aceptada persiste turno e historial con marcas de tiempo sincronizadas | `test_book_appointment_success_persists_appointment_and_initial_history` | `tests/integration/test_appointment_persistence.py` |
| 2 | Alta rechazada por solapamiento no escribe en la base | `test_book_appointment_rejected_overlap_does_not_persist` | `tests/integration/test_appointment_persistence.py` |
| 3 | Falla en inserción de historial revierte el turno | `test_book_appointment_atomic_rollback_on_history_failure` | `tests/integration/test_appointment_persistence.py` |
| 4 | Confirmación de turno actualiza estado y registra historial | `test_change_appointment_status_confirmed_updates_status_and_history` | `tests/integration/test_appointment_persistence.py` |
| 5 | Cancelación de turno actualiza estado a cancelado y registra historial | `test_cancel_appointment_updates_status_and_history` | `tests/integration/test_appointment_persistence.py` |
| 6 | Operación de estado sobre turno inexistente devuelve None | `test_status_operations_on_nonexistent_appointment_return_none` | `tests/integration/test_appointment_persistence.py` |
| 7 | Reprogramación de turno persiste ocho columnas del detalle | `test_reschedule_appointment_success_persists_eight_detail_columns` | `tests/integration/test_appointment_persistence.py` |
| 8 | CHECK de estado de turno rechaza valor inválido | `test_appointment_status_check_rejects_invalid_direct_insert` | `tests/integration/test_appointment_persistence.py` |
| 9 | CHECK de intervalo rechaza fin anterior al inicio | `test_appointment_interval_check_rejects_direct_insert` | `tests/integration/test_appointment_persistence.py` |
| 10 | CHECK todo o nada rechaza detalle de reprogramación parcial | `test_appointment_status_change_reschedule_all_or_none_check_rejects_partial` | `tests/integration/test_appointment_persistence.py` |
| 11 | Trigger de base rechaza UPDATE directo en historial | `test_appointment_status_change_trigger_rejects_direct_update` | `tests/integration/test_appointment_persistence.py` |
| 12 | Trigger de base rechaza DELETE directo en historial | `test_appointment_status_change_trigger_rejects_direct_delete` | `tests/integration/test_appointment_persistence.py` |
| 13 | Trigger de base rechaza TRUNCATE en historial | `test_appointment_status_change_trigger_rejects_truncate` | `tests/integration/test_appointment_persistence.py` |
| 14 | Lector SQL filtra turnos del profesional que solapan el rango | `test_sql_appointment_reader_filters_and_orders_in_range` | `tests/integration/test_appointment_persistence.py` |
| 15 | Dos altas simultáneas del mismo profesional son serializadas | `test_concurrent_booking_same_professional_serialized` | `tests/integration/test_appointment_concurrency.py` |
| 16 | Dos altas simultáneas del mismo sillón son serializadas | `test_concurrent_booking_same_chair_serialized` | `tests/integration/test_appointment_concurrency.py` |
| 17 | Transición concurrente conflictiva sobre el mismo turno es serializada con relectura | `test_concurrent_transition_same_appointment_serialized` | `tests/integration/test_appointment_concurrency.py` |
| 18 | Ciclo upgrade y downgrade menos uno de la migración de turnos | `test_appointment_migration_downgrade_minus_one_cycle` | `tests/integration/test_database_infrastructure.py` |

---

## Evidencia RED: Test de protección contra TRUNCATE

Antes de crear la migración `20261105_05_historial_sin_truncate`, se escribió el test `test_appointment_status_change_trigger_rejects_truncate` en `backend/tests/integration/test_appointment_persistence.py` y se ejecutó, comprobando que el trigger `BEFORE UPDATE OR DELETE` no capturaba `TRUNCATE`:

```text
=================================== FAILURES ===================================
_____________ test_appointment_status_change_trigger_rejects_truncate _____________

connection = <sqlalchemy.engine.base.Connection object at 0x00000171EDC36450>

    def test_appointment_status_change_trigger_rejects_truncate(
        connection: Connection,
    ) -> None:
        """Verifica que TRUNCATE TABLE sobre appointment_status_change sea rechazado por trigger."""
        with pytest.raises(Exception):
>           connection.execute(text("TRUNCATE TABLE appointment_status_change;"))
E           Failed: DID NOT RAISE <class 'Exception'>

tests\integration\test_appointment_persistence.py:236: Failed
=========================== short test summary info ===========================
FAILED tests/integration/test_appointment_persistence.py::test_appointment_status_change_trigger_rejects_truncate - Failed: DID NOT RAISE <class 'Exception'>
======================== 1 failed, 733 deselected in 1.48s ========================
```

---

## Tabla de RED y Mutaciones con Salidas Textuales Reales (Strict TDD)

Para cada uno de los 21 tests de integración de C-17, se aplicó una mutación mínima en el código de producción (`backend/app/` o en las migraciones recreando el esquema mediante downgrade/upgrade) y se capturó la salida textual exacta emitida por pytest:

| Nº | Escenario / Comportamiento | Test (nombre real) | Archivo y mutación aplicada en producción | Salida textual del fallo (pytest) | Restaurado |
|---|---|---|---|---|---|
| 1 | CHECK de estado de turno rechaza valor inválido | `test_appointment_status_check_rejects_invalid_direct_insert` | `backend/alembic/versions/20261105_04_turnos_e_historial.py`: remover constraint `ck_appointment_status_valid` y recrear base | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` | sí |
| 2 | CHECK de intervalo rechaza fin anterior al inicio | `test_appointment_interval_check_rejects_direct_insert` | `backend/alembic/versions/20261105_04_turnos_e_historial.py`: remover constraint `ck_appointment_interval_valid` y recrear base | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` | sí |
| 3 | CHECK todo o nada rechaza detalle de reprogramación parcial | `test_appointment_status_change_reschedule_all_or_none_check_rejects_partial` | `backend/alembic/versions/20261105_04_turnos_e_historial.py`: remover constraint `ck_appointment_status_change_reschedule_all_or_none` y recrear base | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` | sí |
| 4 | Trigger de base rechaza UPDATE directo en historial | `test_appointment_status_change_trigger_rejects_direct_update` | `backend/alembic/versions/20261105_04_turnos_e_historial.py`: comentar creación del trigger `tr_appointment_status_change_append_only` y recrear base | `Failed: DID NOT RAISE <class 'Exception'>` | sí |
| 5 | Trigger de base rechaza DELETE directo en historial | `test_appointment_status_change_trigger_rejects_direct_delete` | `backend/alembic/versions/20261105_04_turnos_e_historial.py`: comentar creación del trigger `tr_appointment_status_change_append_only` y recrear base | `Failed: DID NOT RAISE <class 'Exception'>` | sí |
| 6 | Trigger de base rechaza TRUNCATE en historial | `test_appointment_status_change_trigger_rejects_truncate` | `backend/alembic/versions/20261105_05_historial_sin_truncate.py`: comentar creación del trigger `tr_appointment_status_change_no_truncate` y recrear base | `Failed: DID NOT RAISE <class 'Exception'>` | sí |
| 7 | Lector SQL filtra turnos del profesional que solapan el rango | `test_sql_appointment_reader_filters_and_orders_in_range` | `backend/app/repositories/appointments.py` (`SqlAppointmentReader.find_overlapping_for_professional`): filtrar erróneamente por `AppointmentModel.status == AppointmentStatus.CANCELLED` | `AssertionError: assert 1 == 2` | sí |
| 8 | Lector SQL integrado en repositorio de bloqueos | `test_block_repository_uses_sql_appointment_reader_with_real_rows` | `backend/app/repositories/appointments.py` (`SqlAppointmentReader.find_overlapping_for_professional`): retornar lista vacía `[]` | `AssertionError: assert 0 == 1` | sí |
| 9 | Alta aceptada persiste turno e historial con marcas sincronizadas | `test_book_appointment_success_persists_appointment_and_initial_history` | `backend/app/services/appointments.py` (`book_appointment`): persistir status inicial como `AppointmentStatus.CONFIRMED` | `AssertionError: assert 'confirmado' == 'reservado'` | sí |
| 10 | Alta rechazada por solapamiento no escribe en la base | `test_book_appointment_rejected_overlap_does_not_persist` | `backend/app/services/appointments.py` (`book_appointment`): omitir `session.rollback()` en rama `Rejected` | `AssertionError: assert 2 == 1` | sí |
| 11 | Falla en inserción de historial revierte el turno | `test_book_appointment_atomic_rollback_on_history_failure` | `backend/app/services/appointments.py` (`book_appointment`): atrapar excepción y hacer commit en vez de propagar rollback | `AssertionError: assert 'Simulated history failure for a02' in "Can't operate on closed transaction inside context manager. Please complete the context manager before emitting further commands."` | sí |
| 12 | Bloqueos pesimistas ordenados lexicográficamente por UUID | `test_book_appointment_acquires_resource_locks_ordered_by_uuid` | `backend/app/services/appointments.py` (`_lock_booking_resources`): invertir orden bloqueando sillón antes que profesional | `AssertionError: assert 'professional' in 'SELECT chair.id ...'` | sí |
| 13 | Confirmación de turno actualiza estado y registra historial | `test_change_appointment_status_confirmed_updates_status_and_history` | `backend/app/services/appointments.py` (`change_appointment_status`): no actualizar `appointment.status` | `AssertionError: assert 'reservado' == 'confirmado'` | sí |
| 14 | Cancelación de turno actualiza estado a cancelado y registra historial | `test_cancel_appointment_updates_status_and_history` | `backend/app/services/appointments.py` (`cancel_appointment`): omitir asignación de `AppointmentStatus.CANCELLED` | `AssertionError: assert 'confirmado' == 'cancelado'` | sí |
| 15 | Operación de estado sobre turno inexistente devuelve None | `test_status_operations_on_nonexistent_appointment_return_none` | `backend/app/services/appointments.py` (`change_appointment_status`): lanzar `RuntimeError("Turno inexistente")` si el turno no existe | `RuntimeError: Turno inexistente` | sí |
| 16 | Reprogramación de turno persiste ocho columnas del detalle | `test_reschedule_appointment_success_persists_eight_detail_columns` | `backend/app/services/appointments.py` (`reschedule_appointment`): omitir asignación de `previous_start_time` | `sqlalchemy.exc.IntegrityError: (psycopg.errors.CheckViolation) new row for relation "appointment_status_change" violates check constraint "ck_appointment_status_change_reschedule_all_or_none"` | sí |
| 17 | Reprogramación de turno inexistente devuelve None | `test_reschedule_nonexistent_appointment_returns_none` | `backend/app/services/appointments.py` (`reschedule_appointment`): lanzar `ValueError("Turno inexistente")` si el turno no existe | `ValueError: Turno inexistente` | sí |
| 18 | Dos altas simultáneas del mismo profesional son serializadas | `test_concurrent_booking_same_professional_serialized` | `backend/app/services/appointments.py` (`_lock_booking_resources`): omitir el lock `FOR UPDATE` sobre `professional` | `AssertionError: La conexión B debía quedar bloqueada esperando en pg_locks` | sí |
| 19 | Dos altas simultáneas del mismo sillón son serializadas | `test_concurrent_booking_same_chair_serialized` | `backend/app/services/appointments.py` (`_lock_booking_resources`): omitir el lock `FOR UPDATE` sobre `chair` | `AssertionError: La conexión B debía quedar bloqueada esperando el lock de sillón en pg_locks` | sí |
| 20 | Transición concurrente conflictiva es serializada con relectura | `test_concurrent_transition_same_appointment_serialized` | `backend/app/services/appointments.py` (`change_appointment_status`): omitir la relectura bloqueada del turno (`SELECT ... FOR UPDATE`) | `AssertionError: assert False + where False = isinstance(Ok(...), Rejected)` | sí |
| 21 | Ciclo upgrade y downgrade menos uno de migración 04 | `test_appointment_migration_downgrade_minus_one_cycle` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` (`downgrade`): comentar `op.drop_table('appointment')` | `sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateTable) relation "appointment" already exists` | sí |

---

## Salidas de las 5 corridas consecutivas de concurrencia

Comando ejecutado 5 veces seguidas:
`pytest -m integration tests/integration/test_appointment_concurrency.py -v`

### Corrida 1
```text
=== CONCURRENCY RUN 1 OF 5 ===
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]

============================== 3 passed in 1.24s ==============================
```

### Corrida 2
```text
=== CONCURRENCY RUN 2 OF 5 ===
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]

============================== 3 passed in 1.19s ==============================
```

### Corrida 3
```text
=== CONCURRENCY RUN 3 OF 5 ===
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]

============================== 3 passed in 1.26s ==============================
```

### Corrida 4
```text
=== CONCURRENCY RUN 4 OF 5 ===
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]

============================== 3 passed in 1.23s ==============================
```

### Corrida 5
```text
=== CONCURRENCY RUN 5 OF 5 ===
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend
configfile: pyproject.toml
collecting ... collected 3 items

tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]

============================== 3 passed in 1.17s ==============================
```

---

## Desvíos del apply

1. **Ajuste de firmas y ciclo de transacción en servicios (D5)**:
   - Se removieron los parámetros `references`, `schedule_context` y `professional_name` de las firmas públicas de `book_appointment`, `change_appointment_status`, `cancel_appointment` y `reschedule_appointment`.
   - Motivo: La carga de referencias, horarios, bloqueos, turnos en rango y nombre de profesional debe ocurrir estrictamente **adentro** de la función y **después** de adquirir los bloqueos pesimistas (`SELECT ... FOR UPDATE`); si se inyectaran previamente desde afuera, el contexto no estaría protegido por los bloqueos y se generarían condiciones de carrera.
   - En cuanto a transacciones, el servicio no utiliza bloques `with session.begin()` ni `begin_nested()` como transacción principal, sino la transacción implícita/activa de la sesión entregada por el invocador (compatible con la sesión por request de FastAPI en C-18), finalizando con `session.commit()` si la operación es exitosa y `auto_commit=True`, o con `session.rollback()` si es rechazada o si ocurre un error inesperado (propagando el error a continuación). `auto_commit=False` se preserva para tests de concurrencia que retienen locks.

2. **Correcciones de la autora a C-17 — Trazabilidad con nombres reales de tests**:
   - Se ajustó la tabla de trazabilidad para referenciar exclusivamente nombres de funciones de prueba reales existentes en el código (`test_appointment_persistence.py`, `test_appointment_concurrency.py` y `test_database_infrastructure.py`), verificados mediante `git grep -c "def <nombre>"` con resultado 1 para cada uno.

3. **Correcciones de la autora a C-17 — Tabla rigurosa de RED y mutaciones con salidas textuales**:
   - Se reemplazó la tabla inicial de mutaciones por una tabla exhaustiva para cada uno de los 21 tests de integración de C-17, aplicando mutaciones mínimas reales sobre el código de producción (`backend/app/` o migraciones recreadas con downgrade/upgrade), capturando la salida textual exacta del fallo emitida por pytest y verificando la restauración a GREEN sin dejar modificaciones residuales en el código.

4. **Correcciones de la autora a C-17 — Prevención de bypass por TRUNCATE en el historial append-only**:
   - Se identificó que triggers `BEFORE UPDATE OR DELETE` no capturan sentencias `TRUNCATE TABLE`, permitiendo el vaciado no auditado del historial.
   - Se escribió primero el test `test_appointment_status_change_trigger_rejects_truncate` capturando su estado RED.
   - Se creó una nueva migración `20261105_05_historial_sin_truncate.py` encadenada a `20261105_04_turnos_e_historial` que añade el trigger a nivel sentencia `tr_appointment_status_change_no_truncate` (`BEFORE TRUNCATE ... FOR EACH STATEMENT EXECUTE FUNCTION prevent_appointment_status_change_modification()`), con borrado en su downgrade.
   - Se actualizó el delta spec (`specs/database-infrastructure/spec.md`) agregando el escenario explícito y `tasks.md` (tarea 2.4).
   - Para no quebrar la limpieza entre tests de integración, se implementó el helper centralizado `clean_database_tables(engine: Engine)` en `backend/tests/integration/conftest.py` que ejecuta `ALTER TABLE appointment_status_change DISABLE TRIGGER USER`, procede al truncate/delete de tablas de negocio y en un bloque `finally:` restaura con `ENABLE TRIGGER USER`.
   - Se actualizaron los tests de migración para dejar la base en la nueva revisión head y se agregó `test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle` verificando que el trigger de TRUNCATE se elimina mientras que los de UPDATE y DELETE permanecen activos tras el downgrade.
