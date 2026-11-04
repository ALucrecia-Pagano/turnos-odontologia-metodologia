# Proposal

## Why

C-14 dejó lista la metadata y la línea de base de Alembic, pero las entidades
persistibles del catálogo y los pacientes todavía no tienen tablas ni una
frontera de repositorios. C-15 conecta las altas puras de C-09 con PostgreSQL,
manteniendo las reglas del dominio, la unicidad bajo concurrencia y un seed
ficticio reproducible antes de construir la API de C-20.

## What Changes

- Agregar modelos SQLAlchemy para `Professional`, `Chair`, `Service` y
  `Patient` en `backend/app/db/models.py`, separados de los tipos del dominio.
- Agregar repositorios que reciban y devuelvan tipos del dominio, con
  consultas parametrizadas y operaciones de alta, lectura, listado y
  activación donde corresponda.
- Persistir nombres originales y nombres normalizados de sillones y
  prestaciones, con unicidad sobre la representación normalizada.
- Persistir el DNI normalizado como texto de 7 u 8 dígitos, con índice único y
  `CHECK` explícito.
- Crear una migración `20261103_02_catalogos_y_pacientes` encadenada a la
  baseline de C-14.
- Ampliar los datos ficticios reutilizables y agregar un seed idempotente
  ejecutable manualmente.
- Agregar tests de integración sobre `<POSTGRES_DB>_test`, con rollback por
  test, incluyendo traducción de conflictos de unicidad y ciclo de migración.

## Capabilities

### New Capabilities

- Ninguna. Se conserva la frontera existente de `database-infrastructure`:
  la persistencia de C-15 es comportamiento de la infraestructura de base de
  datos y debe evolucionar junto con Alembic, metadata y su base de
  integración.

### Modified Capabilities

- `database-infrastructure`: agrega las tablas, mapeos, repositorios, seed y
  garantías de integración para catálogos y pacientes.

## Impact

- `backend/app/db/models.py`, `backend/app/db/seed.py` y repositorios bajo
  `backend/app/repositories/`.
- Nueva migración bajo `backend/alembic/versions/`.
- Ampliación de `backend/app/demo_data.py`.
- Nuevos tests de integración y ajustes de metadata/fixtures necesarios para
  que la base de test termine en `head`.
- El dominio, la API y los archivos protegidos por el alcance del change no
  se modifican; `license_number` queda solo en persistencia.
