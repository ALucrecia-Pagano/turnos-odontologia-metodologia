# Design

## Context

C-13 ya provee `load_settings()`, SQLAlchemy síncrono, UTC y la fixture que
crea o reutiliza `<POSTGRES_DB>_test`. C-14 debe agregar la infraestructura de
migraciones sin crear tablas de negocio, porque esas tablas pertenecen a
C-15, C-16 y C-17. La metadata declarativa será compartida por Alembic y por
los modelos futuros.

## Goals / Non-Goals

**Goals:**

- Mantener Alembic, su configuración y sus versiones dentro de `backend/`.
- Evitar URLs y credenciales en `alembic.ini`.
- Probar upgrade, downgrade, restauración final en `head` y autogenerate vacío
  sobre la base de test.
- Establecer desde ahora la convención de nombres para futuros modelos.

**Non-Goals:**

- Crear tablas de `Professional`, `Chair`, `Service`, `Patient` u otras
  entidades de negocio.
- Cambiar la fixture de C-13 para usar una base distinta.
- Agregar un punto de control formal en `tasks.md`.

## Decisions

### D1 — Ubicación y ejecución

Se crearán `backend/alembic.ini`, `backend/alembic/env.py`,
`backend/alembic/script.py.mako` y `backend/alembic/versions/`. Alembic se
ejecutará desde `backend/` con el entorno virtual activo. Se usará la opción
de configuración dentro del backend porque coincide con la KB 08 y mantiene
el tooling junto al código Python.

Alternativas descartadas: configuración en la raíz, que mezcla aplicaciones;
configuración externa, que reduce reproducibilidad.

### D2 — Fuente de `DATABASE_URL`

`env.py` llamará a `load_settings()` y usará `Settings.database_url`;
`alembic.ini` no tendrá URL. Los tests construirán la URL de
`<POSTGRES_DB>_test` usando la fixture de C-13 y la inyectarán al contexto de
Alembic sin modificar la URL de desarrollo.

Alternativas descartadas: leer directamente desde un placeholder del INI o
duplicar la carga de configuración con una segunda implementación.

### D3 — Metadata y naming convention

`backend/app/db/base.py` expondrá una `DeclarativeBase` cuya metadata use
exactamente:

```python
{
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
```

Los `CheckConstraint` futuros tendrán nombre explícito. No se usará una
convención sin nombres, porque produciría nombres variables y migraciones
menos revisables.

### D4 — Nombres y versionado

`alembic.ini` configurará `file_template` para
`YYYYMMDD_NN_slug`. La primera revisión será
`20261103_01_baseline`. Todas las migraciones se versionarán; no se
versionarán caches ni archivos temporales.

### D5 — Línea de base

La migración inicial no tendrá tablas de negocio. Sus operaciones `upgrade` y
`downgrade` serán vacías. La metadata inicialmente sin modelos evita que
autogenerate proponga tablas; Alembic administrará únicamente su tabla
`alembic_version`.

### D6 — Orden de los tests y estado final

Una fixture de sesión ejecutará `upgrade head` sobre `<POSTGRES_DB>_test`
antes de los tests de integración. El test de ciclo ejecutará upgrade,
verificación de revisión, downgrade a `base`, verificación de ausencia de
tablas de negocio y, al final, upgrade nuevamente a `head`. Así C-15 en
adelante encuentra la base preparada.

La base de desarrollo nunca será seleccionada por las fixtures.

### D7 — Autogenerate vacío

El test abrirá una conexión a la base de test migrada, creará un
`MigrationContext`, ejecutará `compare_metadata` contra `Base.metadata` y
afirmará que no hay diferencias. `alembic_version` se excluirá del alcance
de tablas de negocio/comparación.

No se ejecutará `revision --autogenerate` en el test, porque escribiría
archivos.

### D8 — Dependencia

`alembic>=1.13,<2` se agregará como dependencia de runtime, porque C-18
deberá poder ejecutar migraciones durante el arranque del backend.

### D9 — Gobernanza

No se agregará un punto de control adicional en `tasks.md`; la verificación
final del change cubrirá los escenarios del delta y el aislamiento.

## Risks / Trade-offs

- **[Riesgo]** La base de test reutilizada puede conservar objetos de pruebas
  previas. **Mitigación:** aislar cada test en transacción y verificar tablas
  de negocio explícitamente después de `downgrade base`.
- **[Riesgo]** Importaciones futuras de modelos pueden quedar fuera de
  `Base.metadata`. **Mitigación:** centralizar el registro de modelos en
  `base.py` y exigir autogenerate vacío en cada change de persistencia.
- **[Riesgo]** Un `CheckConstraint` sin nombre rompe la convención `ck`.
  **Mitigación:** exigir nombre explícito en C-14 y en los changes posteriores.
- **[Riesgo]** Ejecutar Alembic contra la base equivocada. **Mitigación:** las
  fixtures derivan y comprueban `<POSTGRES_DB>_test`; no se agrega una URL de
  test al `.env`.

## Migration Plan

1. Instalar la dependencia declarada y crear la configuración/base declarativa.
2. Crear la línea de base vacía y ejecutar los tests sobre la base de test.
3. Mantener la base en `head` al finalizar la suite.
4. En caso de rollback del change, retirar los artefactos de Alembic y la
   dependencia; la base de negocio sigue sin tablas porque C-14 no las crea.

## Verificación manual

Desde Git Bash, en la raíz:

```bash
docker compose up -d
```

Desde `backend/`, con el entorno virtual activo:

```bash
alembic upgrade head
alembic current
alembic downgrade base
alembic upgrade head
pytest
pytest -m integration
```

Desde la raíz, al terminar:

```bash
docker compose down
```

No usar `docker compose down -v`.
