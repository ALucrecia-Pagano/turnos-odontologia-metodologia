# Proposal

## Why

C-13 incorpora la infraestructura mínima reproducible para que el backend
pueda persistir en PostgreSQL y probar su comportamiento temporal real. Hoy el
repositorio solo contiene el dominio puro, sin Compose, configuración de
entorno, sesión SQLAlchemy ni aislamiento para tests de integración.

## What Changes

- Agregar Compose raíz con `postgres:16` y `redis:7`, healthchecks, puertos y
  volumen nombrado acordados.
- Agregar `.env.example` con todos los nombres de variables de la KB 08, sin
  valores; mantener `.env` ignorado.
- Incorporar configuración tipada con `pydantic-settings` y errores explícitos
  para variables obligatorias faltantes.
- Incorporar sesión SQLAlchemy 2.x síncrona con psycopg 3 y zona UTC por
  conexión.
- Incorporar fixture y marca `integration`, con base `<POSTGRES_DB>_test`
  separada y transacciones revertidas por test.
- Declarar tests de conexión, `SELECT 1`, `timestamptz`, UTC, configuración,
  secretos y guardia del dominio.
- Mantener fuera de alcance los servicios `backend` y `frontend`, Alembic,
  modelos de negocio, migraciones y lógica del dominio.

## Capabilities

### New Capabilities

- `database-infrastructure`: configuración de entorno, Compose de PostgreSQL y
  Redis, sesión UTC y aislamiento de tests de integración.

### Modified Capabilities

Ninguna.

## Impact

- `docker-compose.yml` y `.env.example` en la raíz.
- `backend/pyproject.toml`, `backend/app/config.py`,
  `backend/app/db/session.py`, fixtures y tests de integración.
- Nuevas dependencias runtime: SQLAlchemy, psycopg con binarios y
  pydantic-settings.
- El dominio permanece sin cambios y sin dependencias de infraestructura.
- C-14 consumirá la sesión y configuración para Alembic; C-18 consumirá el
  Compose y agregará el servicio backend.

