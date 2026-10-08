# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. No commitear.

## 1. Entorno y proyecto instalable (scaffolding, sin lógica)

- [ ] 1.1 Agregar al `.gitignore` raíz las líneas `.venv/`, `__pycache__/`, `.pytest_cache/` y `.mypy_cache/`, conservando `node_modules/` y `.env`; verificar leyendo el archivo que están las seis entradas.
- [ ] 1.2 Crear `backend/pyproject.toml` según design D2/D3 (hatchling con `packages = ["app"]`, `requires-python = ">=3.12"`, `tzdata`, extra `dev` con `pytest>=8,<9` y `mypy>=1.10`, pytest `testpaths = ["tests"]`, mypy `strict`, `python_version = "3.12"`, `files = ["app", "tests"]`) y `backend/app/__init__.py` vacío (sin `app/domain` todavía); verificar que el TOML parsea con `python -c "import tomllib;tomllib.load(open('pyproject.toml','rb'))"`.
- [ ] 1.3 Crear el venv con `py -3.13 -m venv .venv` e instalar con `pip install -e ".[dev]"`; verificar que `pytest --version` reporta 8.x, que `mypy --version` responde y que `pip show turnos-odontologia-backend` muestra `Requires-Python: >=3.12`.
- [ ] 1.4 Crear `backend/tests/__init__.py` y `backend/tests/domain/__init__.py` vacíos; verificar que `mypy` corre sin errores sobre `app` y `tests`.

## 2. Paquete `app.domain` (test de humo, TDD)

- [ ] 2.1 RED: escribir `tests/domain/test_smoke.py` con `test_domain_package_is_importable_package` (aserta que `app.domain` tiene `__path__` / `submodule_search_locations` no vacío) y `test_domain_package_resolves_to_repo_directory` (aserta que `Path(app.domain.__file__).parent` == `Path(__file__).parents[2] / "app" / "domain"`, design D8); verificar que `pytest` falla con `ModuleNotFoundError: app.domain`.
- [ ] 2.2 GREEN: crear `backend/app/domain/__init__.py` vacío; verificar que los 2 tests de humo pasan.
- [ ] 2.3 REFACTOR: revisar nombres (`test_<unidad>_<escenario>_<esperado>`) y estructura AAA; verificar `pytest` y `mypy` en verde.

## 3. Guardia de dependencias: imports permitidos y prohibidos (TDD sobre el helper)

> Tests en `tests/domain/test_import_guard.py`; helper en `tests/domain/import_guard.py` (design D1, D5, D6). Cada test arma un dominio falso en `tmp_path` escribiendo archivos `.py` literales; nada de mocks.

- [ ] 3.1 RED: test `import fastapi` → una violación con `module == "fastapi"`; verificar que falla porque `tests.domain.import_guard` no existe.
- [ ] 3.2 GREEN: crear `import_guard.py` con `ForbiddenImport` (`path`, `line`, `module`), `DOMAIN_ALLOWED_MODULES` y `find_forbidden_imports(domain_dir: Path) -> list[ForbiddenImport]` mínimo; verificar que el test pasa.
- [ ] 3.3 TRIANGULATE (permitidos): tests parametrizados que no reportan violaciones para `import datetime`, `from . import model`, `from .rules import overlap`, `from app.domain.model import Appointment`, `from __future__ import annotations`, `from collections.abc import Sequence`, `import tzdata`; verificar que fallan si el helper es un fake y pasan con la lógica de allowlist real.
- [ ] 3.4 TRIANGULATE (prohibidos): tests parametrizados que reportan exactamente una violación con el módulo esperado para `from sqlalchemy.orm import Session` (`sqlalchemy.orm`), `import redis`, `import pydantic`, `import os`, `from pathlib import Path`, `from app.api import routers` (`app.api`), `import app.db` (`app.db`) y `from app import domain` (`app`); verificar en verde.
- [ ] 3.5 TRIANGULATE (primer segmento exacto): tests `import fastapi_utils` → exactamente una violación con `module == "fastapi_utils"` (no `"fastapi"`), e `import datetime_utils` → una violación con `module == "datetime_utils"`; verificar en verde (si el helper comparara por prefijo de texto, el segundo caso fallaría).
- [ ] 3.6 REFACTOR: extraer la decisión a una función pura `_is_allowed(module: str) -> bool` y la constante `DOMAIN_PACKAGE`; verificar `pytest` y `mypy` en verde tras cada paso.

## 4. Guardia de dependencias: cobertura y reporte (TDD sobre el helper)

- [ ] 4.1 RED → GREEN: test con `import redis` dentro del cuerpo de una función → violación detectada (requiere recorrer todo el árbol con `ast.walk`); verificar rojo antes del cambio si el helper solo miraba el nivel del módulo, y verde después.
- [ ] 4.2 TRIANGULATE: test con `import fastapi` dentro de `if TYPE_CHECKING:` → violación; test con `rules/overlap.py` en un subpaquete que importa `pydantic` → la violación identifica ese archivo; verificar en verde.
- [ ] 4.3 RED → GREEN: test con dos archivos que tienen, cada uno, un import prohibido → se reportan las dos violaciones, en orden determinístico por ruta; verificar en verde.
- [ ] 4.4 TRIANGULATE (reporte): test de `model.py` con `import fastapi` en la línea 3 → la violación tiene `path` que termina en `model.py`, `line == 3` y `module == "fastapi"`; segundo caso con el import en otra línea y otro archivo; verificar en verde.
- [ ] 4.5 Test de limitación documentada: archivo con `__import__("fastapi")` y sin sentencias `import` → lista vacía; agregar al docstring del helper la limitación de imports dinámicos (design D6); verificar en verde.
- [ ] 4.6 REFACTOR: revisar duplicación en la creación de archivos falsos (fixture o helper `_write_module(tmp_path, relpath, source)` tipado); verificar `pytest` y `mypy` en verde.

## 5. Guardia aplicada al dominio real

- [ ] 5.1 RED: escribir `tests/domain/test_domain_dependencies.py` según design D7 (verifica que existe `app/domain/__init__.py`, corre el helper sobre `Path(app.domain.__path__[0])` y aserta lista vacía con un mensaje de una línea por violación `"<ruta>:<línea>: import no permitido en el dominio: '<módulo>'"`); agregar temporalmente `import sqlalchemy` a `app/domain/__init__.py` y verificar que el test falla y el mensaje nombra `app/domain/__init__.py` y `sqlalchemy`.
- [ ] 5.2 GREEN: quitar el import temporal (el `__init__.py` vuelve a estar vacío); verificar que el test pasa.
- [ ] 5.3 REFACTOR: extraer el formateo del mensaje a una función pura del helper (`format_violations`) cubierta por 2 casos (una y dos violaciones); verificar `pytest` y `mypy` en verde.

## 6. Documentación y CHANGES.md

- [ ] 6.1 Escribir `backend/README.md` corto en español: requisitos (Python 3.12+; en esta máquina 3.13), crear venv (`py -3.13 -m venv .venv`, alternativa `python3.13 -m venv .venv`), activar en PowerShell (`.\.venv\Scripts\Activate.ps1`), instalar (`pip install -e ".[dev]"`), correr `pytest` y `mypy`, y una línea sobre la guardia de dependencias del dominio y cómo ampliar la allowlist; verificar siguiendo los pasos tal cual en una terminal nueva.
- [ ] 6.2 Verificar que `CHANGES.md` §[C-01] coincide con lo implementado (allowlist, paquete instalable, mypy sobre `app` y `tests`) y que §[C-07] tiene la idea del explore de C-01 (estas ediciones se hicieron en el propose; solo ajustar si algo cambió en el apply).

## 7. Verificación integral

- [ ] 7.1 Desde `backend/`: `pytest` en verde (todos los tests recolectados de `tests/`) y `mypy` con `Success: no issues found` sobre `app` y `tests`.
- [ ] 7.2 Verificar el rechazo de mypy estricto: agregar temporalmente `def f(x): return x` en un módulo de `tests/`, confirmar que `mypy` reporta error, y quitarlo.
- [ ] 7.3 `git status` desde la raíz: no aparecen `.venv/`, `__pycache__/`, `.pytest_cache/` ni `.mypy_cache/`; `app/domain/__init__.py` sigue vacío y sin lógica de negocio.
