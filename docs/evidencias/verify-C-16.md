# Verificación de C-16 — persistencia-horarios-y-bloqueos

## Resultado

- Tareas completadas: 16/16.
- Suite por defecto: **671 passed, 39 deselected**.
- Integración: **39 passed, 671 deselected**.
- Mypy estricto: **Success: no issues found in 76 source files**.
- Alembic: ciclo `upgrade head`, `current`, `downgrade -1`, `current`,
  `upgrade head` y `current` final en
  `20261104_03_horarios_y_bloqueos (head)`.
- Seed: dos ejecuciones consecutivas; ambas conservaron `25` tramos y
  `0` bloqueos sembrados, y la segunda insertó `0` tramos.
- OpenSpec estricto: `Change ... is valid`.

Las salidas completas están en
[pytest-C-16.txt](pytest-C-16.txt),
[pytest-integration-C-16.txt](pytest-integration-C-16.txt),
[mypy-C-16.txt](mypy-C-16.txt),
[alembic-C-16.txt](alembic-C-16.txt) y
[seed-C-16.txt](seed-C-16.txt).

## Trazabilidad: 19/19 escenarios

| Nº | Escenario de la spec | Test automático |
|---|---|---|
| 1 | Ida y vuelta de tramos horarios semanales | `backend/tests/integration/test_availability_persistence.py::test_working_hours_round_trip_and_order` |
| 2 | Ida y vuelta de bloqueos en UTC con y sin motivo | `backend/tests/integration/test_availability_persistence.py::test_blocks_round_trip_in_utc_with_and_without_reason` |
| 3 | Reemplazo de tramos de un profesional sin afectar a otro | `backend/tests/integration/test_availability_persistence.py::test_working_hours_replacement_isolated` |
| 4 | Reemplazo por lista vacía deja al profesional sin horario | `backend/tests/integration/test_availability_persistence.py::test_working_hours_replacement_empty_removes_schedule` |
| 5 | Rechazo de tramos solapados conserva el horario previo | `backend/tests/integration/test_availability_persistence.py::test_overlapping_working_hours_rejection_preserves_previous` |
| 6 | Rechazo de tramo inválido conserva el horario previo | `backend/tests/integration/test_availability_persistence.py::test_invalid_working_hours_rejection_preserves_previous` |
| 7 | Rechazo de bloqueo con inicio mayor o igual al fin | `backend/tests/integration/test_availability_persistence.py::test_invalid_block_rejection_does_not_persist` |
| 8 | CHECK de base rechaza weekday inválido en working_hours | `backend/tests/integration/test_availability_persistence.py::test_working_hours_weekday_check_rejects_direct_insert` |
| 9 | CHECK de base rechaza minutos inválidos en working_hours | `backend/tests/integration/test_availability_persistence.py::test_working_hours_minute_check_rejects_direct_insert` |
| 10 | CHECK de base rechaza intervalo inválido en block | `backend/tests/integration/test_availability_persistence.py::test_block_interval_check_rejects_direct_insert` |
| 11 | Error de integridad no relacionado se propaga | `backend/tests/integration/test_availability_persistence.py::test_unrelated_block_primary_key_error_is_propagated` |
| 12 | Profesional inexistente al reemplazar horarios devuelve UNKNOWN_REFERENCE | `backend/tests/integration/test_availability_persistence.py::test_unknown_professional_working_hours_with_slots_is_rejected` |
| 13 | Profesional inexistente al crear un bloqueo devuelve UNKNOWN_REFERENCE | `backend/tests/integration/test_availability_persistence.py::test_unknown_professional_block_is_rejected` |
| 14 | Profesional inactivo puede guardar horarios | `backend/tests/integration/test_availability_persistence.py::test_inactive_professional_can_save_availability` |
| 15 | Borrar un bloqueo existente devuelve el bloqueo y libera el horario | `backend/tests/integration/test_availability_persistence.py::test_delete_block_returns_it_and_releases_schedule` |
| 16 | Borrar un bloqueo inexistente devuelve None | `backend/tests/integration/test_availability_persistence.py::test_delete_missing_block_returns_none` |
| 17 | Listado de turnos afectados con lector fake sin modificar turnos | `backend/tests/integration/test_availability_persistence.py::test_list_affected_appointments_uses_reader_without_mutation` |
| 18 | Primera y segunda ejecución idempotente del seed con horarios | `backend/tests/integration/test_availability_persistence.py::test_seed_working_hours_is_idempotent_and_preserves_existing` |
| 19 | Ciclo upgrade y downgrade reversible de la migración | `backend/tests/integration/test_database_infrastructure.py::test_availability_migration_downgrade_minus_one_cycle` |

## Verificación por mutación

Cada mutación se aplicó temporalmente en producción, se ejecutó únicamente el
test indicado y se restauró antes de continuar.

| Escenario | Test | Mutación aplicada | Salida del fallo | Restaurado |
|---|---|---|---|---|
| 1. Ida y vuelta de tramos horarios semanales | `backend/tests/integration/test_availability_persistence.py::test_working_hours_round_trip_and_order` | Ordenar `weekday` descendente en `list_by_professional` | `At index 0 diff: ... weekday=3 ... != ... weekday=1` | sí |
| 2. Ida y vuelta de bloqueos en UTC con y sin motivo | `backend/tests/integration/test_availability_persistence.py::test_blocks_round_trip_in_utc_with_and_without_reason` | Forzar `reason=None` en `_to_domain` de `BlockRepository` | `AssertionError: ... reason: None != 'Congreso'` | sí |
| 3. Reemplazo de tramos de un profesional sin afectar a otro | `backend/tests/integration/test_availability_persistence.py::test_working_hours_replacement_isolated` | Borrar horarios de un UUID distinto | `Left contains one more item: WorkingHours(... weekday=4 ...)` | sí |
| 4. Reemplazo por lista vacía deja al profesional sin horario | `backend/tests/integration/test_availability_persistence.py::test_working_hours_replacement_empty_removes_schedule` | Borrar horarios de un UUID distinto | `Left contains one more item: WorkingHours(... weekday=1 ...)` | sí |
| 5. Rechazo de tramos solapados conserva el horario previo | `backend/tests/integration/test_availability_persistence.py::test_overlapping_working_hours_rejection_preserves_previous` | Omitir `validate_working_hours` | `AssertionError: ... isinstance(Ok(...), Rejected)` | sí |
| 6. Rechazo de tramo inválido conserva el horario previo | `backend/tests/integration/test_availability_persistence.py::test_invalid_working_hours_rejection_preserves_previous` | Omitir `validate_working_hours` | `IntegrityError: INSERT INTO working_hours ... weekday=8` | sí |
| 7. Rechazo de bloqueo con inicio mayor o igual al fin | `backend/tests/integration/test_availability_persistence.py::test_invalid_block_rejection_does_not_persist` | Omitir el retorno temprano de `validate_block` | `IntegrityError: INSERT INTO block ... start_at == end_at` | sí |
| 8. CHECK de base rechaza weekday inválido | `backend/tests/integration/test_availability_persistence.py::test_working_hours_weekday_check_rejects_direct_insert` | Cambiar `weekday >= 1` por `weekday >= 0` en la migración | `Failed: DID NOT RAISE IntegrityError` | sí |
| 9. CHECK de base rechaza minutos inválidos | `backend/tests/integration/test_availability_persistence.py::test_working_hours_minute_check_rejects_direct_insert` | Cambiar `<` por `>` en el CHECK de minutos | `Failed: DID NOT RAISE IntegrityError` | sí |
| 10. CHECK de base rechaza intervalo inválido | `backend/tests/integration/test_availability_persistence.py::test_block_interval_check_rejects_direct_insert` | Cambiar `<` por `>` en el CHECK de bloque | `Failed: DID NOT RAISE IntegrityError` | sí |
| 11. Error de integridad no relacionado se propaga | `backend/tests/integration/test_availability_persistence.py::test_unrelated_block_primary_key_error_is_propagated` | Cambiar la detección de FK por `if True` | `Failed: DID NOT RAISE IntegrityError` | sí |
| 12. Profesional inexistente al reemplazar horarios | `backend/tests/integration/test_availability_persistence.py::test_unknown_professional_working_hours_with_slots_is_rejected` | Cambiar el nombre de la FK reconocida | `IntegrityError: INSERT INTO working_hours ... professional_id=...999` | sí |
| 13. Profesional inexistente al crear un bloqueo | `backend/tests/integration/test_availability_persistence.py::test_unknown_professional_block_is_rejected` | Cambiar el nombre de la FK reconocida | `IntegrityError: INSERT INTO block ... professional_id=...999` | sí |
| 14. Profesional inactivo puede guardar horarios | `backend/tests/integration/test_availability_persistence.py::test_inactive_professional_can_save_availability` | Reemplazar la validación de pertenencia por un rechazo incondicional | `ValueError: Todos los tramos deben pertenecer al profesional indicado` | sí |
| 15. Borrar un bloqueo existente libera el horario | `backend/tests/integration/test_availability_persistence.py::test_delete_block_returns_it_and_releases_schedule` | Devolver `None` en vez del `Block` eliminado | `assert None == Block(...)` | sí |
| 16. Borrar un bloqueo inexistente devuelve None | `backend/tests/integration/test_availability_persistence.py::test_delete_missing_block_returns_none` | Devolver `False` para una fila inexistente | `AssertionError` en `assert repository.delete(...) is None` | sí |
| 17. Listado de turnos afectados sin modificar turnos | `backend/tests/integration/test_availability_persistence.py::test_list_affected_appointments_uses_reader_without_mutation` | Omitir `appointments_affected_by_block` | `Left contains one more item: Appointment(... CANCELLED)` | sí |
| 18. Primera y segunda ejecución idempotente del seed | `backend/tests/integration/test_availability_persistence.py::test_seed_working_hours_is_idempotent_and_preserves_existing` | Omitir la condición de horarios existentes | `assert first_inserted == 15; assert 25 == 15` | sí |
| 19. Ciclo upgrade y downgrade reversible | `backend/tests/integration/test_database_infrastructure.py::test_availability_migration_downgrade_minus_one_cycle` | Quitar `drop_table("block")` del downgrade | `DROP TABLE not_block; ... test_availability_migration_downgrade_minus_one_cycle... FAILED` | sí |

El escenario 3 reforzó el test con una aserción explícita del listado final de
tramos de P1; antes la mutación de borrado selectivo no fallaba porque solo se
verificaba P2.
