import importlib.util
from pathlib import Path

from tests.domain.import_guard import find_forbidden_imports, format_violations


def _real_domain_dir() -> Path:
    # find_spec no ejecuta app/domain/__init__.py: si tuviera un import
    # prohibido, importar el paquete fallaria antes de que la guardia lo reporte.
    spec = importlib.util.find_spec("app.domain")
    assert spec is not None
    assert spec.submodule_search_locations is not None
    return Path(next(iter(spec.submodule_search_locations)))


def test_domain_package_real_directory_has_no_forbidden_imports() -> None:
    domain_dir = _real_domain_dir()
    assert (domain_dir / "__init__.py").is_file()
    backend_dir = domain_dir.parents[1]

    violations = find_forbidden_imports(domain_dir)

    formatted = format_violations(violations, backend_dir)
    assert violations == [], formatted
