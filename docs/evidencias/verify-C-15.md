# Verify de C-15 — persistencia-catalogos-y-pacientes

## Resultado

- Fecha: 2026-11-04.
- Tareas completadas: 26/26.
- Suite por defecto: **648 passed, 13 deselected**.
- Integración: **13 passed, 648 deselected**.
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
| 2 | Matrícula persistida no aparece en `Professional` | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities`; `ProfessionalModel` mantiene `license_number` solo en persistencia |
| 3 | Duplicado de sillón con espacios y mayúsculas | `tests/integration/test_catalog_persistence.py::test_catalog_duplicate_names_and_dni_return_domain_rejections` |
| 4 | Tildes significativas | `tests/domain/test_catalog.py::test_create_service_accents_distinguish_names` |
| 5 | Nombre repetido permitido para profesionales | `tests/domain/test_catalog.py::test_create_professional_repeated_name_allowed` |
| 6 | DNI de entrada normalizado | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities` |
| 7 | DNI duplicado | `tests/integration/test_catalog_persistence.py::test_catalog_duplicate_names_and_dni_return_domain_rejections` |
| 8 | CHECK persistente de DNI | `backend/app/db/models.py::PatientModel`; `backend/alembic/versions/20261103_02_catalogos_y_pacientes.py` |
| 9 | Alta inválida rechazada antes de persistir | `tests/domain/test_catalog.py`; repositorios llaman `create_*` antes de `flush` |
| 10 | Lectura y listado tipados | `tests/integration/test_catalog_persistence.py::test_catalog_repositories_round_trip_domain_entities` |
| 11 | Activación idempotente | `tests/integration/test_catalog_persistence.py::test_catalog_activation_is_idempotent` |
| 12 | Primera ejecución del seed | `docs/evidencias/seed-C-15.txt`, bloque `seed 1` |
| 13 | Segunda ejecución idempotente | `docs/evidencias/seed-C-15.txt`, bloque `seed 2` |
| 14 | Aislamiento y rollback por test | `tests/integration/conftest.py`; `tests/integration/test_database_infrastructure.py::test_transaction_fixture_rolls_back_rows` |
| 15 | Ciclo de migración de catálogos | `tests/integration/test_database_infrastructure.py::test_migration_cycle_restores_test_database_to_head`; `alembic-C-15.txt` |
| 16 | Violación de índice traducida sin catch amplio | `ChairRepository`, `PatientRepository` y tests de duplicados; la traducción inspecciona únicamente la constraint esperada |

## Ciclo TDD y desvíos

Se ejecutó RED antes de los modelos y repositorios: faltaban
`app.db.models` y `app.repositories`. El primer GREEN de migración reveló que
el identificador de C-15 no cabía en el `VARCHAR(32)` heredado de
`alembic_version`; la revisión amplía la columna a `VARCHAR(64)`. En el
primer downgrade se intentó reducirla demasiado pronto y PostgreSQL rechazó
el truncamiento; se retiró esa reducción y el ciclo final pasó.

Los detalles de estos desvíos están también en la sección
[Desvíos del apply](../../openspec/changes/persistencia-catalogos-y-pacientes/design.md#desvíos-del-apply).
