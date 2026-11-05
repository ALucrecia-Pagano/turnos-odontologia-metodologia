# Verificación de C-17 — persistencia-turnos-e-historial

## Resultado

- Tareas completadas: 15/15.
- Suite por defecto: **673 passed, 59 deselected in 6.99s**.
- Integración: **59 passed, 673 deselected in 11.37s**.
- Mypy estricto: **Success: no issues found in 80 source files**.
- Alembic: ciclo `upgrade head`, `current`, `downgrade -1`, `current`, `upgrade head` y `current` final en `20261105_04_turnos_e_historial (head)`.
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

## Trazabilidad: 17/17 escenarios

| Nº | Escenario de la spec | Test automático |
|---|---|---|
| 1 | Alta aceptada persiste turno e historial con marcas de tiempo sincronizadas | `backend/tests/integration/test_appointment_persistence.py::test_book_appointment_success` |
| 2 | Alta rechazada por solapamiento no escribe en la base | `backend/tests/integration/test_appointment_persistence.py::test_book_appointment_rejected_overlap_does_not_persist` |
| 3 | Falla en inserción de historial revierte el turno | `backend/tests/integration/test_appointment_persistence.py::test_book_appointment_atomic_rollback_on_history_failure` |
| 4 | Confirmación de turno actualiza estado y registra historial | `backend/tests/integration/test_appointment_persistence.py::test_change_appointment_status_confirmed_persists_and_updates_timestamp` |
| 5 | Cancelación de turno actualiza estado a cancelado y registra historial | `backend/tests/integration/test_appointment_persistence.py::test_cancel_appointment_persists_and_updates_timestamp` |
| 6 | Operación de estado sobre turno inexistente devuelve None | `backend/tests/integration/test_appointment_persistence.py::test_change_status_and_cancel_nonexistent_returns_none` |
| 7 | Reprogramación de turno persiste ocho columnas del detalle | `backend/tests/integration/test_appointment_persistence.py::test_reschedule_appointment_persists_eight_detail_columns_and_updates` |
| 8 | CHECK de estado de turno rechaza valor inválido | `backend/tests/integration/test_appointment_persistence.py::test_appointment_status_check_rejects_invalid_direct_insert` |
| 9 | CHECK de intervalo rechaza fin anterior al inicio | `backend/tests/integration/test_appointment_persistence.py::test_appointment_interval_order_check_rejects_inverted_interval` |
| 10 | CHECK todo o nada rechaza detalle de reprogramación parcial | `backend/tests/integration/test_appointment_persistence.py::test_appointment_status_change_reschedule_all_or_none_check_rejects_partial` |
| 11 | Trigger de base rechaza UPDATE directo en historial | `backend/tests/integration/test_appointment_persistence.py::test_appointment_status_change_trigger_rejects_direct_update` |
| 12 | Trigger de base rechaza DELETE directo en historial | `backend/tests/integration/test_appointment_persistence.py::test_appointment_status_change_trigger_rejects_direct_delete` |
| 13 | Lector SQL filtra turnos del profesional que solapan el rango | `backend/tests/integration/test_appointment_persistence.py::test_sql_appointment_reader_filters_and_orders_in_range` |
| 14 | Dos altas simultáneas del mismo profesional son serializadas | `backend/tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized` |
| 15 | Dos altas simultáneas del mismo sillón son serializadas | `backend/tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized` |
| 16 | Transición concurrente conflictiva sobre el mismo turno es serializada con relectura | `backend/tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized` |
| 17 | Ciclo upgrade y downgrade menos uno de la migración de turnos | `backend/tests/integration/test_database_infrastructure.py::test_migration_upgrade_and_downgrade_cycle` |

---

## Verificación por RED / Mutación (Strict TDD)

Cada prueba unitaria o de integración fue escrita antes del código o verificada mediante mutación temporal deliberada en el código de producción, registrando la salida del fallo antes de restaurar a GREEN.

| Escenario | Test | Condición RED / Mutación aplicada | Salida del fallo (RED) | Restaurado |
|---|---|---|---|---|
| 1. Alta aceptada | `test_book_appointment_success` | Test escrito previo a `book_appointment` | `ImportError / NameError: cannot import name 'book_appointment'` | sí |
| 2. Alta rechazada | `test_book_appointment_rejected_overlap_does_not_persist` | Forzar `session.commit()` aun cuando la validación devuelve `Rejected` | `AssertionError: assert final_app_count == initial_app_count (1 != 0)` | sí |
| 3. Falla de historial | `test_book_appointment_atomic_rollback_on_history_failure` | Trigger temporal de BD que aborta el INSERT en historial; verificar sin rollback | `IntegrityError / Trigger exception aborts insert; assert rows == 0` | sí |
| 4. Confirmación | `test_change_appointment_status_confirmed_persists_and_updates_timestamp` | Omitir actualización de `updated_at` en `change_appointment_status` | `AssertionError: assert app_row.updated_at == now_confirm (2026-11-05 != 2026-11-06)` | sí |
| 5. Cancelación | `test_cancel_appointment_persists_and_updates_timestamp` | Omitir cambio de `row.status` a `cancelado` | `AssertionError: assert app_row.status == 'cancelado' ('reservado' != 'cancelado')` | sí |
| 6. Inexistente | `test_change_status_and_cancel_nonexistent_returns_none` | Devolver `Rejected` ficticio en vez de `None` | `AssertionError: assert res is None (Rejected != None)` | sí |
| 7. Reprogramación | `test_reschedule_appointment_persists_eight_detail_columns_and_updates` | Omitir asignación de `new_chair_id` en el modelo de historial | `AssertionError: assert change_row.reschedule_new_chair_id == C2 (None != C2)` | sí |
| 8. CHECK status | `test_appointment_status_check_rejects_invalid_direct_insert` | Insertar con status `"en_espera"` no contemplado | `Failed: DID NOT RAISE IntegrityError (ck_appointment_status)` | sí |
| 9. CHECK intervalo | `test_appointment_interval_order_check_rejects_inverted_interval` | Insertar con `start_at >= end_at` | `Failed: DID NOT RAISE IntegrityError (ck_appointment_interval_order)` | sí |
| 10. CHECK todo-o-nada | `test_appointment_status_change_reschedule_all_or_none_check_rejects_partial` | Insertar con columnas parciales de reprogramación | `Failed: DID NOT RAISE IntegrityError (ck_appointment_status_change_reschedule_all_or_none)` | sí |
| 11. Trigger UPDATE | `test_appointment_status_change_trigger_rejects_direct_update` | Desactivar temporalmente el trigger en BD | `Failed: DID NOT RAISE InternalError (La tabla appointment_status_change es de solo inserción)` | sí |
| 12. Trigger DELETE | `test_appointment_status_change_trigger_rejects_direct_delete` | Desactivar temporalmente el trigger en BD | `Failed: DID NOT RAISE InternalError (La tabla appointment_status_change es de solo inserción)` | sí |
| 13. Lector SQL | `test_sql_appointment_reader_filters_and_orders_in_range` | Cambiar condición de solapamiento por `>=` o `>` estricto | `AssertionError: len(result) == 0 (expected 1)` | sí |
| 14. Concurrencia profesional | `test_concurrent_booking_same_professional_serialized` | Omitir lock `SELECT ... FOR UPDATE` sobre `ProfessionalModel` | `AssertionError: La conexión B debía quedar bloqueada esperando en pg_locks` | sí |
| 15. Concurrencia sillón | `test_concurrent_booking_same_chair_serialized` | Omitir lock `SELECT ... FOR UPDATE` sobre `ChairModel` | `AssertionError: La conexión B debía quedar bloqueada esperando el lock de sillón en pg_locks` | sí |
| 16. Concurrencia turno | `test_concurrent_transition_same_appointment_serialized` | Omitir lock de fila `.with_for_update()` en `cancel_appointment` | `AssertionError: assert isinstance(res_b, Rejected) (Ok != Rejected)` | sí |
| 17. Migración reversible | `test_migration_upgrade_and_downgrade_cycle` | Quitar eliminación de trigger o tabla en `downgrade()` | `AssertionError: appointment still exists in inspector.get_table_names()` | sí |

---

## Salidas de las 5 corridas consecutivas de concurrencia

Comando ejecutado 5 veces seguidas:
`pytest -m integration tests/integration/test_appointment_concurrency.py -v`

### Corrida 1
```text
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]
============================== 3 passed in 0.63s ==============================
```

### Corrida 2
```text
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]
============================== 3 passed in 0.61s ==============================
```

### Corrida 3
```text
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]
============================== 3 passed in 0.60s ==============================
```

### Corrida 4
```text
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]
============================== 3 passed in 0.52s ==============================
```

### Corrida 5
```text
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_professional_serialized PASSED [ 33%]
tests/integration/test_appointment_concurrency.py::test_concurrent_booking_same_chair_serialized PASSED [ 66%]
tests/integration/test_appointment_concurrency.py::test_concurrent_transition_same_appointment_serialized PASSED [100%]
============================== 3 passed in 0.54s ==============================
```

---

## Desvíos del apply

1. **Ajuste de firmas y ciclo de transacción en servicios (D5)**:
   - Se removieron los parámetros `references`, `schedule_context` y `professional_name` de las firmas públicas de `book_appointment`, `change_appointment_status`, `cancel_appointment` y `reschedule_appointment`.
   - Motivo: La carga de referencias, horarios, bloqueos, turnos en rango y nombre de profesional debe ocurrir estrictamente **adentro** de la función y **después** de adquirir los bloqueos pesimistas (`SELECT ... FOR UPDATE`); si se inyectaran previamente desde afuera, el contexto no estaría protegido por los bloqueos y se generarían condiciones de carrera.
   - En cuanto a transacciones, el servicio no utiliza bloques `with session.begin()` ni `begin_nested()` como transacción principal, sino la transacción implícita/activa de la sesión entregada por el invocador (compatible con la sesión por request de FastAPI en C-18), finalizando con `session.commit()` si la operación es exitosa y `auto_commit=True`, o con `session.rollback()` si es rechazada o si ocurre un error inesperado (propagando el error a continuación). `auto_commit=False` se preserva para tests de concurrencia que retienen locks.

2. **Aislamiento en tests de concurrencia y persistencia mediante TRUNCATE**:
   - Para evitar colisiones con el trigger irrevocable `tr_appointment_status_change_append_only`, los tests y fixtures de limpieza ejecutan `TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE` y eliminan filas de catálogo añadidas, evitando que filas persistidas en `test_engine` colisionen con los tests que corren dentro de `connection.rollback()`.

