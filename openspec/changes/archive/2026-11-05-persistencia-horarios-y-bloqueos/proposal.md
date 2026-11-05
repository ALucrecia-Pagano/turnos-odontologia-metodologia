# Proposal

## Why

C-05 y C-06 definieron las entidades y reglas puras de disponibilidad (`WorkingHours`, `Block`, `validate_working_hours`, `validate_block` y `appointments_affected_by_block`), y C-15 persistió los catálogos y pacientes en PostgreSQL, pero los horarios de atención semanales y los bloqueos de agenda todavía no tienen tablas ni repositorios. C-16 conecta esa disponibilidad con PostgreSQL preservando al dominio como autoridad de validación, exponiendo la interfaz de consulta de turnos afectados mediante un lector inyectable (`AppointmentReader`) y sembrando horarios ficticios reproducibles antes de implementar la persistencia de turnos (C-17) y la API de disponibilidad (C-21).

## What Changes

- Agregar los modelos declarativos SQLAlchemy `WorkingHoursModel` (`working_hours`) y `BlockModel` (`block`) en `backend/app/db/models.py`, separados de los tipos del dominio.
- Ampliar el `TypeVar` de `CatalogResult` en `backend/app/domain/catalog/result.py` para admitir `Block` y `tuple[WorkingHours, ...]` sin modificar ningún otro código de C-09 ni de C-15.
- Ampliar `backend/app/repositories/contracts.py` con los protocolos `AppointmentReader`, `WorkingHoursRepository` y `BlockRepository` usando únicamente tipos del dominio.
- Implementar los repositorios SQL de horarios de atención y de bloqueos con validación previa del dominio (`validate_working_hours` y `validate_block`), traducción de la clave foránea de profesional inexistente a `UNKNOWN_REFERENCE` (`ReferenceKind.PROFESSIONAL`), reemplazo transaccional de tramos por profesional (incluida la lista vacía), borrado de bloqueos que devuelve el `Block` eliminado o `None`, y consulta de turnos afectados (`list_affected_appointments(block)`) delegada en `AppointmentReader` y `appointments_affected_by_block`.
- Crear la migración reversible `20261104_03_horarios_y_bloqueos` encadenada a `20261103_02_catalogos_y_pacientes`.
- Ampliar `backend/app/demo_data.py` con 25 tramos de `WORKING_HOURS` (lunes a viernes para los tres profesionales, con el segundo profesional solo de mañana) y extender `backend/app/db/seed.py` de forma idempotente, sin precargar bloqueos.
- Agregar tests unitarios de metadata y contratos y tests de integración sobre `<POSTGRES_DB>_test` con rollback por test.

## Capabilities

### New Capabilities

- Ninguna. Se conserva la frontera existente de `database-infrastructure`: la persistencia de horarios y bloqueos extiende la infraestructura de base de datos, migraciones Alembic, repositorios y seed.

### Modified Capabilities

- `database-infrastructure`: agrega las tablas `working_hours` y `block`, sus restricciones e índices, los repositorios tipados de disponibilidad, el contrato `AppointmentReader`, la extensión idempotente del seed con 25 tramos horarios y la migración `20261104_03_horarios_y_bloqueos`.

## Impact

- `backend/app/domain/catalog/result.py` (únicamente las restricciones del `TypeVar` `T`).
- `backend/app/db/models.py`, `backend/app/db/seed.py` y `backend/app/demo_data.py`.
- `backend/app/repositories/contracts.py` y nuevos repositorios en `backend/app/repositories/`.
- Nueva migración `backend/alembic/versions/20261104_03_horarios_y_bloqueos.py`.
- Tests unitarios (`tests/test_persistence_metadata.py`, `tests/test_repository_contracts.py`, `tests/domain/test_catalog.py`) y de integración (`tests/integration/test_availability_persistence.py`, ajustes de `head` y limpieza en `tests/integration/test_database_infrastructure.py` y `tests/integration/test_catalog_persistence.py`).
- Las reglas del dominio en `backend/app/domain/rules/`, los modelos `WorkingHours` y `Block`, la tabla `appointment` (C-17) y la API HTTP (C-21) no se modifican.

