# Verify de C-14 — migraciones-alembic

## Resultado

- Fecha: 2026-11-03.
- Tareas completadas: 18/18.
- Suite por defecto: **610 passed, 8 deselected**.
- Integración: **8 passed, 610 deselected**.
- Mypy estricto: **Success: no issues found in 60 source files**.
- Alembic manual sobre la base de desarrollo: `upgrade head`, `current`,
  `downgrade base`, `upgrade head` y `current` final en
  `20261103_01_baseline (head)`.
- OpenSpec estricto: verificación ejecutada al finalizar.
- No se modificaron el dominio, las specs principales, `.env`, volúmenes de
  Docker ni archivos de otro change.

Las salidas completas se conservan en
[pytest-C-14.txt](pytest-C-14.txt),
[pytest-integration-C-14.txt](pytest-integration-C-14.txt),
[mypy-C-14.txt](mypy-C-14.txt) y
[alembic-C-14.txt](alembic-C-14.txt).

## Trazabilidad: 10/10 escenarios

| Nº | Escenario de la spec | Test o evidencia |
|---|---|---|
| 1 | `alembic.ini` no contiene URL y usa la estructura esperada | `tests/test_alembic_configuration.py::test_alembic_ini_uses_safe_configuration_without_database_url` |
| 2 | `upgrade head` registra la migración inicial sin tablas de negocio | `tests/integration/test_database_infrastructure.py::test_migration_cycle_restores_test_database_to_head` |
| 3 | `downgrade base` es reversible y no deja tablas de negocio | `tests/integration/test_database_infrastructure.py::test_migration_cycle_restores_test_database_to_head` |
| 4 | La suite usa `<POSTGRES_DB>_test` y termina en `head` | `tests/integration/test_database_infrastructure.py::test_migration_cycle_restores_test_database_to_head` |
| 5 | Autogenerate no encuentra diferencias | `tests/integration/test_database_infrastructure.py::test_autogenerate_finds_no_differences_after_migration` |
| 6 | `alembic_version` queda fuera de la metadata de negocio | `tests/integration/test_database_infrastructure.py::test_autogenerate_finds_no_differences_after_migration` |
| 7 | La convención genera nombres `ix`, `uq`, `ck`, `fk` y `pk` estables | `tests/integration/test_database_infrastructure.py::test_declarative_metadata_uses_stable_constraint_names` |
| 8 | La guardia del dominio no permite importar infraestructura | `tests/domain/test_domain_dependencies.py`; `tests/domain/test_import_guard.py` |
| 9 | La fixture de C-13 sigue revirtiendo la transacción por test | `tests/integration/test_database_infrastructure.py::test_transaction_fixture_rolls_back_rows` |
| 10 | pytest sin selector excluye integración y no requiere Docker | Salida de `pytest`: 610 ejecutados y 8 deseleccionados; `backend/pyproject.toml` |

## Ciclo TDD y desvíos

El test de configuración se ejecutó en RED antes de crear `alembic.ini`
(`FileNotFoundError`) y pasó en GREEN después de agregar la configuración.
Los escenarios de integración se ejecutaron después de agregar la fixture y
la implementación. El primer ciclo de migración falló por un snapshot
transaccional obsoleto del test, no por conexión ni autenticación; el test se
ajustó para consultar con conexiones nuevas y pasó. El detalle está también
en la sección [Desvíos del apply](../../openspec/changes/migraciones-alembic/design.md#desvíos-del-apply).

## Verificación manual

Desde `backend/`, se ejecutó el ciclo contra la base de desarrollo usando la
configuración de la aplicación:

```text
alembic upgrade head
alembic current
alembic downgrade base
alembic upgrade head
alembic current
```

La salida completa está en [alembic-C-14.txt](alembic-C-14.txt). El estado
final fue `20261103_01_baseline (head)`.

Los artefactos archivados son
[design.md](../../openspec/changes/archive/2026-11-03-migraciones-alembic/design.md)
y
[tasks.md](../../openspec/changes/archive/2026-11-03-migraciones-alembic/tasks.md).
