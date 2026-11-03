# Explore C-14

El explore lo hizo Copilot y las decisiones D1 a D9 las cerró la autora el
2026-11-02. Este documento registra el alcance acordado para C-14; no
implementa código, tests ni migraciones.

## Inventario

- C-13 está archivado y dejó PostgreSQL, SQLAlchemy, configuración por
  `DATABASE_URL`, UTC y la fixture de `<POSTGRES_DB>_test`.
- Existe `backend/app/config.py` con `load_settings()` y
  `backend/app/db/session.py` con el engine SQLAlchemy.
- Existen tests de integración marcados y excluidos por defecto.
- No existen `backend/alembic.ini`, `backend/alembic/`, versiones Alembic ni
  `backend/app/db/base.py`.
- `backend/pyproject.toml` todavía no declara Alembic.
- La KB 04 define PostgreSQL, SQLAlchemy, UTC y migraciones versionadas; la KB
  08 ubica Alembic bajo `backend/`; la KB 09 mantiene Alembic como SU-10.
- C-15, C-16 y C-17 agregarán las tablas de negocio y sus migraciones
  posteriores; C-14 solo establece la línea de base.

## Decisiones

### D1 — Ubicación y ejecución

`backend/alembic.ini` y `backend/alembic/` con `env.py`, `script.py.mako` y
`versions/`. Alembic se corre desde `backend/` con el entorno virtual activo.

### D2 — Configuración y base de test

`env.py` obtiene la URL llamando a `load_settings()` de
`backend/app/config.py`; `alembic.ini` no contiene URL. Los tests usan
`<POSTGRES_DB>_test`, creada por la fixture de C-13, nunca la base de
desarrollo.

### D3 — Metadata y nombres

`backend/app/db/base.py` expone `DeclarativeBase` con:

```python
{
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
```

Los `CheckConstraint` futuros llevan nombre explícito.

### D4 — Nombres y versionado

Las migraciones usan `YYYYMMDD_NN_slug`; la línea de base se llama
`20261103_01_baseline`. Se versionan todas las migraciones.

### D5 — Línea de base vacía

La migración inicial no crea ni borra tablas de negocio. `upgrade` y
`downgrade` son operaciones vacías.

### D6 — Ciclo de integración

Una fixture de sesión ejecuta `upgrade head` antes de los tests. El ciclo
verifica la revisión, ejecuta `downgrade base`, comprueba que no queden tablas
de negocio y ejecuta `upgrade head` al final para dejar la base preparada.

### D7 — Autogenerate vacío

Se usa `MigrationContext` con `compare_metadata` contra la base de test
migrada y `Base.metadata`, sin escribir archivos. `alembic_version` queda
fuera de las tablas de negocio.

### D8 — Dependencia

Se agrega `alembic>=1.13,<2` como dependencia de runtime.

### D9 — Gobernanza

No se agrega un punto de control en `tasks.md`.

## Riesgos y pendientes

- La base de test reutilizada debe conservar aislamiento transaccional.
- Los modelos futuros deberán registrarse en `Base.metadata` para que
  autogenerate detecte divergencias.
- Un constraint `CHECK` sin nombre explícito no satisface la convención.
- La disponibilidad exacta de la versión de Alembic en el entorno se valida
  durante la implementación, no en este explore.
