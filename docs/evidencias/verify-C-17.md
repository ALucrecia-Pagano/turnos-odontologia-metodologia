# Verificación de C-17 — persistencia-turnos-e-historial

## Resultado

- Tareas completadas: 16/16 (incluyendo la tarea 2.4 de protección contra TRUNCATE).
- Suite por defecto: **673 passed, 61 deselected in 7.42s**.
- Integración: **61 passed, 673 deselected in 15.53s** (incluyendo los tests nuevos de persistencia, concurrencia, downgrade -1 de migración 04 y downgrade -1 de migración 05).
- Mypy estricto: **Success: no issues found in 80 source files**.
- Alembic, sobre la base de test `turnos_test`: ciclo `upgrade head`, `current`, `downgrade -1`, `current`, `upgrade head` y `current` final en `20261105_05_historial_sin_truncate (head)`.
- Concurrencia real multi-conexión: 5 ejecuciones consecutivas de la suite de concurrencia completa (3 tests: profesional, sillón, transición), todas 100% exitosas sin intermitencias y sin uso de `time.sleep` (sincronizadas vía sondeo en `pg_locks` con timeout acotado y `SET lock_timeout = '5s'`).
- OpenSpec estricto: `Change 'persistencia-turnos-e-historial' is valid`.
- Higiene git: `git diff --check` limpio (código de salida 0).

Los artefactos del change están ubicados en:
- [proposal.md](../../openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/proposal.md)
- [design.md](../../openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/design.md)
- [tasks.md](../../openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/tasks.md)
- [spec.md](../../openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/specs/database-infrastructure/spec.md)

Las salidas completas están en:
- [pytest-C-17.txt](pytest-C-17.txt)
- [pytest-integration-C-17.txt](pytest-integration-C-17.txt)
- [mypy-C-17.txt](mypy-C-17.txt)
- [alembic-C-17.txt](alembic-C-17.txt)
- [concurrencia-C-17.txt](concurrencia-C-17.txt)
- [mutaciones-C-17.txt](mutaciones-C-17.txt)

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

## Detección del test de TRUNCATE

La detección de `test_appointment_status_change_trigger_rejects_truncate` está demostrada por su mutación en [mutaciones-C-17.txt](mutaciones-C-17.txt): en la migración 05, el trigger pasa de `BEFORE TRUNCATE` a `BEFORE UPDATE`, así que deja de proteger TRUNCATE. El RED original no se conserva.

---

## Verificación por mutación

Se regenera con `python ../docs/evidencias/mutaciones-C-17.py` desde `backend/`. El script copia sus textos del código real, muta solo producción (`backend/app/` o las migraciones), corre únicamente el test de cada mutación, restaura el archivo y comprueba que el test vuelva a pasar. La salida completa está en [mutaciones-C-17.txt](mutaciones-C-17.txt); esta tabla se genera desde ese archivo.

Son 22 tests: 17 de persistencia, 3 de concurrencia y 2 de migración. La primera corrida dio 21 de 22: invertir el orden de `sorted(set(professional_ids))` no hizo fallar `test_book_appointment_acquires_resource_locks_ordered_by_uuid`, porque el alta bloquea un solo profesional y un solo sillón. Se reforzó el test con una reprogramación que bloquea dos de cada uno, y la corrida actual da 22 de 22.

<!-- mutaciones:inicio -->
| Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|
| `test_appointment_status_check_rejects_invalid_direct_insert` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- "status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",`<br>`+ "status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado', 'en_espera')",` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| `test_appointment_interval_check_rejects_direct_insert` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- "start_at < end_at",`<br>`+ "start_at <> end_at",` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| `test_appointment_status_change_reschedule_all_or_none_check_rejects_partial` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- "OR "`<br>`+ "OR reschedule_previous_start_at IS NOT NULL OR "` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| `test_appointment_status_change_trigger_rejects_direct_update` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- BEFORE UPDATE OR DELETE ON appointment_status_change`<br>`+ BEFORE DELETE ON appointment_status_change` | `Failed: DID NOT RAISE <class 'Exception'>` |
| `test_appointment_status_change_trigger_rejects_direct_delete` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- BEFORE UPDATE OR DELETE ON appointment_status_change`<br>`+ BEFORE UPDATE ON appointment_status_change` | `Failed: DID NOT RAISE <class 'Exception'>` |
| `test_appointment_status_change_trigger_rejects_truncate` | `backend/alembic/versions/20261105_05_historial_sin_truncate.py` | `- BEFORE TRUNCATE ON appointment_status_change`<br>`+ BEFORE UPDATE ON appointment_status_change` | `Failed: DID NOT RAISE <class 'Exception'>` |
| `test_sql_appointment_reader_filters_and_orders_in_range` | `backend/app/repositories/appointment.py` | `- AppointmentModel.professional_id == professional_id,`<br>`+ AppointmentModel.professional_id.is_not(None),` | `AssertionError: assert 3 == 2` |
| `test_block_repository_uses_sql_appointment_reader_with_real_rows` | `backend/app/repositories/appointment.py` | `- AppointmentModel.start_at < end_at,`<br>`+ AppointmentModel.start_at > end_at,` | `assert 0 == 1` |
| `test_book_appointment_success_persists_appointment_and_initial_history` | `backend/app/services/appointments.py` | `- created_at=status_change.changed_at,`<br>`+ created_at=appointment_entity.start_at,` | `assert datetime.datetime(2026, 11, 9, 13, 0, tzinfo=datetime.timezone.utc) == datetime.datetime(2026, 11, 5, 12, 0, tzinfo=datetime.timezone.utc)` |
| `test_book_appointment_rejected_overlap_does_not_persist` | `backend/app/services/appointments.py` | `- session.rollback()`<br>`+ session.add(AppointmentModel(id=request.id, patient_id=request.patient_id, professional_id=request.professional_id, chair_id=request.chair_id, service_id=request.service_id, start_at=request.start_at, end_at=request.start_at + timedelta(minutes=30), status="reservado", created_at=now, updated_at=now))`<br>`+ session.commit()` | `assert 2 == 1` |
| `test_book_appointment_atomic_rollback_on_history_failure` | `backend/app/services/appointments.py` | `+ session.commit()` | `AssertionError: assert <app.db.models.AppointmentModel object at 0x0000020FEFE12210> is None` |
| `test_book_appointment_acquires_resource_locks_ordered_by_uuid` | `backend/app/services/appointments.py` | `- for prof_id in sorted(set(professional_ids)):`<br>`+ for prof_id in sorted(set(professional_ids), reverse=True):` | `AssertionError: assert [[UUID('00000...0000000001')]] == [[UUID('00000...0000000002')]]` |
| `test_change_appointment_status_confirmed_updates_status_and_history` | `backend/app/services/appointments.py` | `- row.status = result.appointment.status.value` | `AssertionError: assert 'reservado' == 'confirmado'` |
| `test_cancel_appointment_updates_status_and_history` | `backend/app/services/appointments.py` | `- row.status = result.appointment.status.value` | `AssertionError: assert 'reservado' == 'cancelado'` |
| `test_status_operations_on_nonexistent_appointment_return_none` | `backend/app/services/appointments.py` | `- return None`<br>`+ from app.domain.violations import Violation, ViolationCode`<br>`+ `<br>`+ return Rejected(`<br>`+ (Violation(ViolationCode.UNKNOWN_REFERENCE, "Turno inexistente."),)`<br>`+ )` | `AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.UNKNOWN_REFERENCE: 'UNKNOWN_REFERENCE'>, message='Turno inexistente.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) is None` |
| `test_reschedule_appointment_success_persists_eight_detail_columns` | `backend/app/services/appointments.py` | `- reschedule_new_chair_id=reschedule_detail.new_chair_id,`<br>`+ reschedule_new_chair_id=reschedule_detail.previous_chair_id,` | `AssertionError: assert UUID('00000000-0000-0000-0000-0000000000b1') == UUID('00000000-0000-0000-0000-0000000000b2')` |
| `test_reschedule_nonexistent_appointment_returns_none` | `backend/app/services/appointments.py` | `- return None`<br>`+ from app.domain.violations import Violation, ViolationCode`<br>`+ `<br>`+ return Rejected(`<br>`+ (Violation(ViolationCode.UNKNOWN_REFERENCE, "Turno inexistente."),)`<br>`+ )` | `AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.UNKNOWN_REFERENCE: 'UNKNOWN_REFERENCE'>, message='Turno inexistente.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) is None` |
| `test_concurrent_booking_same_professional_serialized` | `backend/app/services/appointments.py` | `- .with_for_update()` | `AssertionError: La conexión B debía quedar bloqueada esperando en pg_locks` |
| `test_concurrent_booking_same_chair_serialized` | `backend/app/services/appointments.py` | `- .with_for_update()` | `AssertionError: La conexión B debía quedar bloqueada esperando el lock de sillón en pg_locks` |
| `test_concurrent_transition_same_appointment_serialized` | `backend/app/services/appointments.py` | `- .with_for_update()` | `AssertionError: assert False` |
| `test_appointment_migration_downgrade_minus_one_cycle` | `backend/alembic/versions/20261105_04_turnos_e_historial.py` | `- CREATE TRIGGER tr_appointment_status_change_append_only`<br>`- BEFORE UPDATE OR DELETE ON appointment_status_change`<br>`- FOR EACH ROW EXECUTE FUNCTION prevent_appointment_status_change_modification();` | `assert 0 == 1` |
| `test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle` | `backend/alembic/versions/20261105_05_historial_sin_truncate.py` | `- DROP TRIGGER IF EXISTS tr_appointment_status_change_no_truncate ON appointment_status_change;`<br>`+ SELECT 1;` | `AssertionError: assert 'tr_appointment_status_change_no_truncate' not in ['tr_appointment_status_change_append_only', 'tr_appointment_status_change_no_truncate']` |
<!-- mutaciones:fin -->

---

## Corridas de concurrencia

Las 5 corridas consecutivas de `pytest -m integration tests/integration/test_appointment_concurrency.py -v` están en [concurrencia-C-17.txt](concurrencia-C-17.txt).

---

## Desvíos del apply

1. **Ajuste de firmas y ciclo de transacción en servicios (D5)**:
   - Se removieron los parámetros `references`, `schedule_context` y `professional_name` de las firmas públicas de `book_appointment`, `change_appointment_status`, `cancel_appointment` y `reschedule_appointment`.
   - Motivo: La carga de referencias, horarios, bloqueos, turnos en rango y nombre de profesional debe ocurrir estrictamente **adentro** de la función y **después** de adquirir los bloqueos pesimistas (`SELECT ... FOR UPDATE`); si se inyectaran previamente desde afuera, el contexto no estaría protegido por los bloqueos y se generarían condiciones de carrera.
   - En cuanto a transacciones, el servicio no utiliza bloques `with session.begin()` ni `begin_nested()` como transacción principal, sino la transacción implícita/activa de la sesión entregada por el invocador (compatible con la sesión por request de FastAPI en C-18), finalizando con `session.commit()` si la operación es exitosa y `auto_commit=True`, o con `session.rollback()` si es rechazada o si ocurre un error inesperado (propagando el error a continuación). `auto_commit=False` se preserva para tests de concurrencia que retienen locks.

2. **Correcciones de la autora a C-17 — Trazabilidad con nombres reales de tests**:
   - Se ajustó la tabla de trazabilidad para referenciar exclusivamente nombres de funciones de prueba reales existentes en el código (`test_appointment_persistence.py`, `test_appointment_concurrency.py` y `test_database_infrastructure.py`), verificados mediante `git grep -c "def <nombre>"` con resultado 1 para cada uno.

3. **Correcciones de la autora a C-17 — Verificación por mutación reproducible**:
   - La tabla anterior de 21 mutaciones nombraba archivos, funciones y constraints que no existen en el código, así que no era evidencia válida. Se reemplazó por la tabla de la sección "Verificación por mutación", generada por `mutaciones-C-17.py`, que cubre los 22 tests de integración de C-17.

4. **Correcciones de la autora a C-17 — Prevención de bypass por TRUNCATE en el historial append-only**:
   - Se identificó que triggers `BEFORE UPDATE OR DELETE` no capturan sentencias `TRUNCATE TABLE`, permitiendo el vaciado no auditado del historial.
   - Se escribió primero el test `test_appointment_status_change_trigger_rejects_truncate` y se ejecutó en RED; esa salida no se conserva.
   - Se creó una nueva migración `20261105_05_historial_sin_truncate.py` encadenada a `20261105_04_turnos_e_historial` que añade el trigger a nivel sentencia `tr_appointment_status_change_no_truncate` (`BEFORE TRUNCATE ... FOR EACH STATEMENT EXECUTE FUNCTION prevent_appointment_status_change_modification()`), con borrado en su downgrade.
   - Se actualizó el delta spec (`specs/database-infrastructure/spec.md`) agregando el escenario explícito y `tasks.md` (tarea 2.4).
   - Para no quebrar la limpieza entre tests de integración, se implementó el helper centralizado `clean_database_tables(engine: Engine)` en `backend/tests/integration/conftest.py` que ejecuta `ALTER TABLE appointment_status_change DISABLE TRIGGER USER`, procede al truncate/delete de tablas de negocio y en un bloque `finally:` restaura con `ENABLE TRIGGER USER`.
   - Se actualizaron los tests de migración para dejar la base en la nueva revisión head y se agregó `test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle` verificando que el trigger de TRUNCATE se elimina mientras que los de UPDATE y DELETE permanecen activos tras el downgrade.

5. **Mutaciones con el detector de C-23**: tenía 3 mutaciones inválidas; se reescribieron. En la 15 y la 17, el `raise` ante un turno inexistente pasó a devolver un `Rejected` con `UNKNOWN_REFERENCE` en lugar de `None`, y lo detecta `assert res is None`. **La 21 cambió de foco, del downgrade al upgrade (aceptado por la autora).** Antes quitaba `drop_table("appointment")` del downgrade de la 04. Toda mutación del downgrade que deje un objeto en la base hace que el `upgrade` siguiente del mismo test lo vuelva a crear y falle con `DuplicateTable` dentro de Alembic, antes de cualquier assert. Así ninguna mutación del downgrade puede ser detectada por una afirmación del test. Ahora quita el `CREATE TRIGGER tr_appointment_status_change_append_only` del upgrade de la 04, y el mismo ciclo lo detecta con `assert trigger_count == 1`. El downgrade de la 04 queda sin mutación propia en este script. El script ahora tiene `--check`, el arreglo de CRLF y el detector, y compara un SHA-256 de `backend/app` y `backend/alembic` (`f79aa…`) en lugar de `git diff`.
