# Design

## Context

Repositorio sin código (solo `knowledge-base/`, `openspec/`, `docs/`, `CHANGES.md`, `AGENTS.md`/`CLAUDE.md`). `.gitignore` raíz con `node_modules/` y `.env`. La máquina de la autora tiene Python 3.14, 3.13 y 3.11 (sin 3.12) y no tiene `uv`. Motivación y alcance: ver `proposal.md`. Requisitos: `specs/domain-dependency-guard/spec.md` y `specs/backend-toolchain/spec.md`.

La regla de dependencias de KB 08 (§Estructura de directorios) dice que `domain` solo usa biblioteca estándar (`dataclasses`, `datetime`, `zoneinfo`, `enum`) y `tzdata`. Este diseño la convierte en una **allowlist** verificable.

## Goals / Non-Goals

**Goals:**
- Que `pytest` y `mypy` corran desde `backend/` sin argumentos, con la misma configuración para la autora y para cualquier agente.
- Que la guardia de dependencias sea un helper puro, testeable con archivos falsos en `tmp_path`, y que también custodie el dominio real.
- Dejar el árbol `backend/app/domain` y `backend/tests/domain` en la forma que esperan C-02 en adelante (KB 08).

**Non-Goals:**
- Detectar uso de reloj global (`datetime.now()` y similares): idea registrada para C-07.
- Detectar imports dinámicos.
- Chequear dependencias de otras capas (`app.api`, `app.db`, …): se evalúa cuando existan.

## Decisions

### D1 — Estructura de archivos

```
backend/
├── pyproject.toml
├── README.md
├── app/
│   ├── __init__.py              # vacío
│   └── domain/
│       └── __init__.py          # vacío
└── tests/
    ├── __init__.py              # vacío (tests como paquete)
    └── domain/
        ├── __init__.py          # vacío
        ├── import_guard.py      # helper: find_forbidden_imports, ForbiddenImport, DOMAIN_ALLOWED_MODULES
        ├── test_smoke.py
        ├── test_import_guard.py # tests del helper con tmp_path
        └── test_domain_dependencies.py  # helper aplicado al app/domain real
```

- `tests/` y `tests/domain/` son paquetes para que los tests importen el helper como `tests.domain.import_guard` y para que mypy no choque por módulos de test con el mismo nombre en directorios distintos. Con el modo de import por defecto de pytest (`prepend`) y `tests/__init__.py`, pytest inserta `backend/` en `sys.path`, así que `tests.*` es importable sin configuración extra.
- El helper vive en `tests/` (no en `app/`) porque es una herramienta de verificación, no código del producto; no se instala ni se distribuye.
- **Alternativa descartada**: `tests/conftest.py` con el helper como fixture. Un módulo normal es más explícito, se importa con tipos y se testea igual que cualquier función pura.

### D2 — Backend de build: hatchling

`[build-system] requires = ["hatchling"]`, `build-backend = "hatchling.build"`, con `[tool.hatch.build.targets.wheel] packages = ["app"]` (el nombre del proyecto, `turnos-odontologia-backend`, no coincide con el paquete `app`, así que se declara explícito; `tests` queda fuera del wheel).

- **Por qué hatchling**: su instalación editable agrega `backend/` al `sys.path` mediante un `.pth` simple, que mypy y cualquier herramienta entienden; la configuración es una sola tabla.
- **Alternativa descartada**: setuptools. En layout plano con `app/` y `tests/` su autodescubrimiento falla ("multiple top-level packages") y obliga a configurar `packages.find`; además, según la versión, su modo editable usa un *import hook* que mypy no sigue. Ambos son resolubles, pero hatchling evita los dos problemas.

### D3 — `pyproject.toml`

- `[project]`: `name = "turnos-odontologia-backend"`, `version = "0.1.0"`, `requires-python = ">=3.12"`, `dependencies = ["tzdata>=2024.1"]`.
- `[project.optional-dependencies] dev = ["pytest>=8,<9", "mypy>=1.10"]`.
- `[tool.pytest.ini_options]`: `minversion = "8.0"`, `testpaths = ["tests"]`.
- `[tool.mypy]`: `python_version = "3.12"`, `strict = true`, `files = ["app", "tests"]`. Correr mypy 3.13 con objetivo 3.12 está soportado y detecta uso de sintaxis o APIs posteriores a 3.12.
- Sin ruff ni black (decisión de la autora). Sin `pythonpath` en pytest: lo resuelve la instalación editable más `tests/__init__.py`.

### D4 — Entorno local

venv en `backend/.venv` creado con `py -3.13 -m venv .venv` (no hay 3.12 en la máquina; 3.13 cumple `>=3.12`). Instalación con `pip install -e ".[dev]"`. El README documenta la activación en PowerShell (`.\.venv\Scripts\Activate.ps1`) y la alternativa sin activar (`.\.venv\Scripts\python -m pytest`).

### D5 — Allowlist final

```python
DOMAIN_ALLOWED_MODULES: frozenset[str] = frozenset({
    "__future__", "collections", "dataclasses", "datetime",
    "enum", "typing", "zoneinfo", "tzdata",
})
DOMAIN_PACKAGE = "app.domain"
```

| Entrada | Por qué |
|---------|---------|
| `dataclasses`, `datetime`, `zoneinfo`, `enum` | Listados en KB 08: modelos inmutables, instantes, zona horaria, códigos de violación |
| `tzdata` | Paquete de datos para que `zoneinfo` funcione en Windows (SU-10) |
| `typing` | Type hints exigidos por `mypy --strict` (`Final`, `Literal`, `Protocol`, `TypeAlias`); sin efectos ni I/O |
| `collections` | Para `collections.abc` (`Sequence`, `Iterable`, `Mapping`) en firmas de reglas; módulo puro. Se permite el primer segmento completo para mantener una sola regla de comparación |
| `__future__` | `from __future__ import annotations`; es una directiva del compilador, no una dependencia |

Excluidos a propósito: `abc` (no hace falta mientras alcance `typing.Protocol`), `uuid`, `math`, `itertools`, `functools`, y todo módulo con I/O (`os`, `pathlib`, `io`, `sys`, `time`, `logging`, `json`, …). **Agregar una entrada es una edición deliberada**: se hace en el change que la necesita, con su justificación en el design de ese change.

### D6 — Algoritmo de `find_forbidden_imports`

Firma: `find_forbidden_imports(domain_dir: Path) -> list[ForbiddenImport]`, con `ForbiddenImport` como `@dataclass(frozen=True)` de `path: Path`, `line: int`, `module: str`.

1. Recorre `sorted(domain_dir.rglob("*.py"))` (orden determinístico de reportes).
2. Para cada archivo, `ast.parse(source, filename=str(path))` y `ast.walk` sobre todo el árbol (incluye imports dentro de funciones, `if TYPE_CHECKING:` y `try/except`).
3. `ast.Import`: evalúa cada `alias.name`. `ast.ImportFrom`: si `level > 0` (relativo) → permitido; si no, evalúa `node.module`.
4. Un nombre absoluto está permitido si `name.split(".")[0] in DOMAIN_ALLOWED_MODULES` **o** `name == "app.domain" or name.startswith("app.domain.")`. Todo lo demás es una violación.
5. Devuelve la lista completa (no corta en la primera).

Consecuencias que fijan los specs:
- `import fastapi_utils` → **una violación con `module == "fastapi_utils"`**: se compara el primer segmento exacto, así que no se confunde con `fastapi`, y como tampoco está en la allowlist, se reporta. Lo mismo `import datetime_utils` (no lo salva el prefijo `datetime`).
- `from sqlalchemy.orm import Session` → violación con `module == "sqlalchemy.orm"` (se reporta el nombre completo importado; se juzga por `sqlalchemy`).
- `from app import domain` → violación con `module == "app"`: la regla mira el módulo del `from`, no los nombres importados. Se escribe `from app.domain import x` o un import relativo.
- Un archivo con error de sintaxis hace fallar el test con `SyntaxError` (falla ruidosa, no silenciosa).
- Imports dinámicos (`importlib.import_module`, `__import__`) no son sentencias `import`, así que no se detectan: limitación anotada en el docstring del helper.

El helper parametriza la allowlist como constante de módulo, no como argumento: hay una sola allowlist en el proyecto y los tests la ejercen tal cual.

### D7 — Mensaje de falla del test sobre el dominio real

`test_domain_dependencies.py` primero verifica que `app/domain/__init__.py` existe (para no pasar en vacío si la ruta está mal) y luego hace `assert violations == [], formatted`, donde `formatted` tiene una línea por violación: `"{ruta relativa a backend}:{línea}: import no permitido en el dominio: '{módulo}'"`. La ruta del dominio se obtiene de `app.domain.__path__[0]`, no de una ruta escrita a mano. El formateo termina en una función pura del helper (`format_violations(violations: list[ForbiddenImport], base: Path) -> str`) para poder testearlo aparte.

### D8 — Smoke test concreto

`test_smoke.py` con dos casos: (a) `app.domain` es un paquete (`hasattr(app.domain, "__path__")` / `__spec__.submodule_search_locations` no vacío); (b) `Path(app.domain.__file__).parent` coincide con `backend/app/domain` calculado desde la ubicación del test (`Path(__file__).parents[2] / "app" / "domain"`), lo que prueba la instalación editable contra el código del repo.

## Decisiones confirmadas por la autora

Revisión del propose, 2026-10-08:

1. **`collections` completo en la allowlist (D5): aceptado.** Es biblioteca estándar sin I/O, así que respeta el dominio puro, y la regla de comparar el primer segmento queda más simple que permitir solo `collections.abc`.
2. **`uuid`, `abc` y `functools` fuera de la allowlist (D5): aceptado.** Si C-02 u otro change necesita alguno, se agrega de forma explícita en ese change, con su justificación.
3. **Errores puestos a propósito en las tareas 5.1 y 7.2: aceptado.** El import prohibido y la función sin anotar sirven para ver fallar la guardia y mypy. Al terminar el apply tienen que quedar eliminados; la autora lo revisa en el verify.

## Risks / Trade-offs

- [Imports dinámicos no detectados] → Limitación documentada; un `importlib` en el dominio igual exige importar `importlib`, que no está en la allowlist y sí se detecta.
- [Allowlist demasiado estrecha para C-02 (p. ej. `uuid` para ids)] → Se amplía en ese change con justificación; la guardia lo hace visible en vez de dejarlo pasar.
- [Permitir `collections` entero habilita `collections.OrderedDict` etc.] → Son estructuras puras sin I/O; se acepta a cambio de una regla de comparación única.
- [Python 3.13 local vs. objetivo 3.12] → mypy chequea con `python_version = "3.12"`; un uso de API exclusiva de 3.13 que mypy no detecte es improbable y se cubrirá cuando el Dockerfile (C-13) fije la versión de runtime.
- [El README y el venv dependen del launcher `py` de Windows] → El README indica también el equivalente `python3.13 -m venv .venv` para otros sistemas.

## Migration Plan

No aplica: no hay código previo. Rollback = borrar `backend/` y revertir `.gitignore` y `CHANGES.md`.
