# Proposal

## Why

C-13 dejó PostgreSQL, SQLAlchemy y una base de integración separada, pero el
esquema todavía no tiene un historial versionado ni una forma reproducible de
verificar migraciones. C-14 incorpora Alembic como base para que C-15, C-16 y
C-17 puedan agregar persistencia sin tocar la base de desarrollo ni divergir
de la metadata declarativa.

## What Changes

- Agregar Alembic como dependencia de runtime del backend.
- Crear la configuración y estructura de Alembic dentro de `backend/`.
- Crear la base declarativa SQLAlchemy con la convención acordada para nombres
  de constraints e índices.
- Crear una migración inicial vacía, versionada como línea de base, sin tablas
  de negocio.
- Agregar tests de integración para `upgrade head`, `downgrade base`,
  restauración final en `head` y autogenerate vacío sobre la base de test.
- Documentar los comandos manuales de verificación.

## Capabilities

### New Capabilities

- No se crea una capacidad nueva: la capacidad existente
  `database-infrastructure` es la frontera durable para esta funcionalidad.

### Modified Capabilities

- `database-infrastructure`: agrega requisitos para migraciones Alembic,
  metadata declarativa, aislamiento de la base de test y ausencia de
  diferencias de autogenerate.

## Impact

- Archivos de planificación de C-14 y delta de
  `openspec/specs/database-infrastructure/spec.md`.
- Implementación futura en `backend/alembic.ini`, `backend/alembic/`,
  `backend/app/db/base.py` y tests de integración.
- `backend/pyproject.toml` incorporará `alembic>=1.13,<2`.
- C-15, C-16 y C-17 dependerán de la línea de base y de la metadata compartida.
