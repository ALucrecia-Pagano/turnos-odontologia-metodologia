import ast
from dataclasses import dataclass
from pathlib import Path

DOMAIN_ALLOWED_MODULES: frozenset[str] = frozenset(
    {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "enum",
        "typing",
        "tzdata",
        "uuid",
        "zoneinfo",
    }
)


DOMAIN_PACKAGE = "app.domain"


@dataclass(frozen=True, slots=True)
class ForbiddenImport:
    path: Path
    line: int
    module: str


def _is_allowed(module: str) -> bool:
    if module == DOMAIN_PACKAGE or module.startswith(DOMAIN_PACKAGE + "."):
        return True
    return module.split(".")[0] in DOMAIN_ALLOWED_MODULES


def _parse_domain_files(domain_dir: Path) -> list[tuple[Path, ast.Module]]:
    """Parsea todos los .py bajo domain_dir, ordenados por ruta."""
    return [
        (path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for path in sorted(domain_dir.rglob("*.py"))
    ]


def find_forbidden_imports(domain_dir: Path) -> list[ForbiddenImport]:
    """Devuelve los imports estaticos no permitidos de todos los .py bajo domain_dir.

    Recorre todo el arbol de cada archivo (funciones, TYPE_CHECKING, try/except) y
    reporta los resultados ordenados por ruta. Los imports relativos se permiten.

    Limitacion: solo detecta sentencias `import` / `from ... import`. Los imports
    dinamicos (`importlib.import_module("x")`, `__import__("x")`) NO se detectan;
    igualmente `importlib` no esta en la lista permitida y se reportaria.
    """
    violations: list[ForbiddenImport] = []
    for path, tree in _parse_domain_files(domain_dir):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not _is_allowed(alias.name):
                        violations.append(ForbiddenImport(path, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module is not None and not _is_allowed(node.module):
                    violations.append(ForbiddenImport(path, node.lineno, node.module))
    return violations


def format_violations(violations: list[ForbiddenImport], base: Path) -> str:
    """Una linea por violacion: `<ruta relativa a base>:<linea>: import no permitido ...`."""
    return "\n".join(
        f"{v.path.relative_to(base).as_posix()}:{v.line}: "
        f"import no permitido en el dominio: '{v.module}'"
        for v in violations
    )


@dataclass(frozen=True, slots=True)
class GlobalClockCall:
    path: Path
    line: int
    expression: str


_DATETIME_CLASS_CLOCK = frozenset({"now", "utcnow", "today"})
_DATE_CLASS_CLOCK = frozenset({"today"})


def _clock_bindings(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    modules: set[str] = set()
    datetime_classes: set[str] = set()
    date_classes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "datetime":
                    modules.add(alias.asname or "datetime")
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "datetime":
            for alias in node.names:
                if alias.name == "datetime":
                    datetime_classes.add(alias.asname or "datetime")
                elif alias.name == "date":
                    date_classes.add(alias.asname or "date")
    return modules, datetime_classes, date_classes


def _is_clock_access(
    node: ast.Attribute,
    modules: set[str],
    datetime_classes: set[str],
    date_classes: set[str],
) -> bool:
    owner = node.value
    if isinstance(owner, ast.Name):
        if owner.id in datetime_classes:
            return node.attr in _DATETIME_CLASS_CLOCK
        if owner.id in date_classes:
            return node.attr in _DATE_CLASS_CLOCK
    elif isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name):
        if owner.value.id in modules:
            if owner.attr == "datetime":
                return node.attr in _DATETIME_CLASS_CLOCK
            if owner.attr == "date":
                return node.attr in _DATE_CLASS_CLOCK
    return False


def find_global_clock_calls(domain_dir: Path) -> list[GlobalClockCall]:
    """Devuelve los accesos al reloj global de `datetime` de todos los .py bajo domain_dir.

    Resuelve por archivo (no por ambito) que denota cada nombre importado del modulo
    `datetime` y reporta todo ACCESO (llamado o no, en cualquier funcion) a `now`,
    `utcnow` o `today` de la clase `datetime`, y a `today` de la clase `date`, sea por la
    clase importada, con alias o por el modulo (`datetime.datetime.now`), mas
    `from datetime import *`. Ordena por (ruta, linea, columna). No reporta `context.now`,
    un parametro `now` ni la construccion de instantes. `time` lo cubre
    `find_forbidden_imports`.

    Limitaciones: no detecta accesos dinamicos (`getattr(datetime, "now")`) ni
    reasignaciones (`d = datetime; d.now()`); un parametro llamado `datetime` en un
    archivo que importa la clase daria un falso positivo (sombrearlo ya es un defecto).
    """
    found: list[tuple[Path, int, int, str]] = []
    for path, tree in _parse_domain_files(domain_dir):
        modules, datetime_classes, date_classes = _clock_bindings(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and _is_clock_access(
                node, modules, datetime_classes, date_classes
            ):
                found.append((path, node.lineno, node.col_offset, ast.unparse(node)))
            elif (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module == "datetime"
                and any(alias.name == "*" for alias in node.names)
            ):
                found.append((path, node.lineno, node.col_offset, "from datetime import *"))
    found.sort(key=lambda item: (item[0], item[1], item[2]))
    return [GlobalClockCall(path, line, expression) for path, line, _, expression in found]


def format_clock_calls(calls: list[GlobalClockCall], base: Path) -> str:
    """Una linea por acceso: `<ruta relativa a base>:<linea>: reloj global en el dominio ...`."""
    return "\n".join(
        f"{c.path.relative_to(base).as_posix()}:{c.line}: "
        f"reloj global en el dominio: '{c.expression}' (usar el now inyectado)"
        for c in calls
    )
