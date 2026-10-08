# Proposal

## Why

El repositorio todavía no tiene código: no hay paquete de Python, ni runner de tests, ni chequeo de tipos. C-02 (`crear-turno-sin-solapamientos`, el change evaluado del TP) necesita un paquete `backend/app/domain` donde aplicar Strict TDD desde el primer test, y la regla de dependencias del dominio (KB 08 §Estructura de directorios, DD-06) tiene que estar custodiada por un test automático **antes** de que exista la primera regla de negocio, para que nunca se cuele un import de framework o de I/O.

## What Changes

- Nuevo proyecto Python instalable en `backend/` (`pyproject.toml` con `[build-system]`): `requires-python = ">=3.12"`, dependencia de runtime `tzdata`, extras de desarrollo `dev` con pytest 8 y mypy; instalación con `pip install -e ".[dev]"` en un entorno virtual local.
- Configuración de pytest (`testpaths = ["tests"]`) y de mypy (`strict`, `python_version = "3.12"`, chequeando `app` y `tests`).
- Paquete `backend/app/` con `backend/app/domain/__init__.py` vacío (sin lógica de negocio).
- Test de humo que comprueba que `app.domain` es un paquete importable y que se resuelve al directorio `backend/app/domain` del repo.
- **Guardia de dependencias del dominio por lista permitida (allowlist)**: un helper puro de tests, `find_forbidden_imports`, analiza con `ast` los módulos de `app/domain` y reporta todo import cuyo primer segmento no esté en la lista permitida (biblioteca estándar explícita + `tzdata` + los propios módulos del dominio). Un test lo corre sobre el `app/domain` real y exige cero violaciones; el mensaje de falla nombra el archivo y el import ofensivo.
- `.gitignore` raíz: se agregan `.venv/`, `__pycache__/`, `.pytest_cache/` y `.mypy_cache/`, conservando `node_modules/` y `.env`.
- `backend/README.md` corto en español: crear el venv (`py -3.13 -m venv .venv`), instalar, correr `pytest` y `mypy`.
- `CHANGES.md`: el scope de C-01 se alinea con este change (allowlist, paquete instalable, mypy sobre `app` y `tests`) y se agrega una idea al scope de C-07.

### Fuera de alcance

- Cualquier lógica de negocio, modelo o regla RN-AG (van desde C-02).
- Docker, PostgreSQL, Alembic, Redis, FastAPI, JWT y frontend (C-13, C-14, C-19, C-25 y otros).
- **Detección de llamadas a `datetime.now()`, `datetime.utcnow()` o `time.time()` en el dominio**: no se hace en C-01; queda registrada como idea en el scope de C-07 (`no-turnos-en-el-pasado`), que es donde se introduce el reloj inyectado.
- Detección de imports dinámicos (`importlib.import_module("...")`, `__import__(...)`): limitación documentada de la guardia.
- Linters y formateadores (ruff, black): no se incorporan.

## Capabilities

### New Capabilities
- `domain-dependency-guard`: regla verificable de que el paquete de dominio solo depende de una lista permitida explícita de módulos (stdlib acotada, `tzdata` y sus propios módulos), con reporte de cada import ofensivo.
- `backend-toolchain`: proyecto Python del backend instalable, con suite de pytest y chequeo `mypy --strict` reproducibles en un entorno virtual local, y el paquete `app.domain` disponible para los changes siguientes.

### Modified Capabilities
<!-- Ninguna: no existen specs previos en openspec/specs/. -->

## Impact

- **Código nuevo**: `backend/pyproject.toml`, `backend/README.md`, `backend/app/__init__.py`, `backend/app/domain/__init__.py`, `backend/tests/` (smoke test, helper de la guardia y sus tests).
- **Archivos modificados**: `.gitignore` (raíz), `CHANGES.md` (scope de C-01 y C-07).
- **Dependencias**: `tzdata` (runtime); `pytest` 8 y `mypy` (dev); `hatchling` como backend de build.
- **Entorno**: Python 3.13 local (la máquina no tiene 3.12); el proyecto declara compatibilidad desde 3.12 y mypy chequea contra 3.12.
- **Governance**: BAJO. Sin APIs, datos ni secretos involucrados.
