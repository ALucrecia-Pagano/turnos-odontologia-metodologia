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
        "zoneinfo",
        "tzdata",
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


def find_forbidden_imports(domain_dir: Path) -> list[ForbiddenImport]:
    """Devuelve los imports estaticos no permitidos de todos los .py bajo domain_dir.

    Recorre todo el arbol de cada archivo (funciones, TYPE_CHECKING, try/except) y
    reporta los resultados ordenados por ruta. Los imports relativos se permiten.

    Limitacion: solo detecta sentencias `import` / `from ... import`. Los imports
    dinamicos (`importlib.import_module("x")`, `__import__("x")`) NO se detectan;
    igualmente `importlib` no esta en la lista permitida y se reportaria.
    """
    violations: list[ForbiddenImport] = []
    for path in sorted(domain_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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
