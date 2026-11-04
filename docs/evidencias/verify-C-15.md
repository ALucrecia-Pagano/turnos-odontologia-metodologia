# Verify de C-15 — persistencia-catalogos-y-pacientes

## Resultado

- Fecha: 2026-11-04.
- Tareas completadas: 26/26.
- Suite por defecto: **648 passed, 19 deselected**.
- Integración: **19 passed, 648 deselected**.
- Mypy estricto: **Success: no issues found in 71 source files**.
- Alembic: ciclo `upgrade head`, `current`, `downgrade -1`,
  `upgrade head` y `current` final en
  `20261103_02_catalogos_y_pacientes (head)`.
- Seed: dos ejecuciones con `professional: 3`, `chair: 3`, `service: 5` y
  `patient: 5` en ambas.
- OpenSpec estricto: `Change ... is valid`.
- `git diff --check`: sin salida y código 0.
- Docker Compose: PostgreSQL 16 y Redis 7 saludables.

Las salidas completas están en
[pytest-C-15.txt](pytest-C-15.txt),
[pytest-integration-C-15.txt](pytest-integration-C-15.txt),
[mypy-C-15.txt](mypy-C-15.txt),
[alembic-C-15.txt](alembic-C-15.txt) y
[seed-C-15.txt](seed-C-15.txt).

## Trazabilidad: 16/16 escenarios

| Nº | Escenario de la spec | Test o evidencia |
|---|---|---|
| 1 | Filas de catálogo y paciente se leen como dominio | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities` |
| 2 | Matrícula persistida no aparece en `Professional` | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities`; nota: la lectura devuelve `Professional` y no expone `license_number` |
| 3 | Duplicado de sillón con espacios y mayúsculas | `tests/integration/test_catalog_persistence.py::test_catalog_duplicate_names_and_dni_return_domain_rejections` |
| 4 | Tildes significativas | `tests/domain/test_catalog.py::test_create_service_accents_distinguish_names` |
| 5 | Nombre repetido permitido para profesionales | `tests/domain/test_catalog.py::test_create_professional_repeated_name_allowed` |
| 6 | DNI de entrada normalizado | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities` |
| 7 | DNI duplicado | `tests/integration/test_catalog_persistence.py::test_catalog_duplicate_names_and_dni_return_domain_rejections` |
| 8 | CHECK persistente de DNI | `tests/integration/test_catalog_persistence.py::test_patient_dni_check_rejects_invalid_direct_insert` |
| 9 | Alta inválida rechazada antes de persistir | `tests/integration/test_catalog_persistence.py::test_invalid_repository_highs_are_rejected_before_persistence` |
| 10 | Lectura y listado tipados | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities` |
| 11 | Activación idempotente | `tests/integration/test_catalog_persistence.py::test_catalog_activation_is_idempotent` |
| 12 | Primera ejecución del seed | `tests/integration/test_catalog_persistence.py::test_seed_database_is_idempotent_on_test_database` |
| 13 | Segunda ejecución idempotente | `tests/integration/test_catalog_persistence.py::test_seed_database_is_idempotent_on_test_database` |
| 14 | Aislamiento y rollback por test | `tests/integration/test_database_infrastructure.py::test_transaction_fixture_rolls_back_rows`; nota: usa la fixture transaccional de `tests/integration/conftest.py` |
| 15 | Ciclo de migración de catálogos | `tests/integration/test_database_infrastructure.py::test_migration_cycle_restores_test_database_to_head`; nota: la salida manual completa está en `alembic-C-15.txt` |
| 16 | Violación de índice traducida sin catch amplio | `tests/integration/test_catalog_persistence.py::test_concurrent_chair_name_conflict_is_translated` y `tests/integration/test_catalog_persistence.py::test_patient_unrelated_primary_key_error_is_propagated` |

## Ciclo TDD y desvíos

Se ejecutó RED antes de los modelos y repositorios: faltaban
`app.db.models` y `app.repositories`. El primer GREEN de migración reveló que
el identificador de C-15 no cabía en el `VARCHAR(32)` heredado de
`alembic_version`; la revisión amplía la columna a `VARCHAR(64)`. En el
primer downgrade se intentó reducirla demasiado pronto y PostgreSQL rechazó
el truncamiento; se retiró esa reducción y el ciclo final pasó.

Los detalles de estos desvíos están también en la sección
[Desvíos del apply](../../openspec/changes/persistencia-catalogos-y-pacientes/design.md#desvíos-del-apply).

Para este ajuste se agregaron cinco tests de integración: el CHECK parametrizado
para `12AB567` y `123456`, el rechazo previo de altas inválidas, el seed
idempotente, la traducción del conflicto concurrente de nombre y la
propagación de una violación de clave primaria no relacionada. Cada mutación
temporal hizo fallar su test y fue restaurada; no se modificó producción de
forma permanente.
