from pathlib import Path

from tests.domain.import_guard import find_forbidden_imports, find_global_clock_calls

DOMAIN = Path(__file__).resolve().parents[2] / "app" / "domain"


def test_catalog_real_domain_has_no_forbidden_dependencies() -> None:
    assert find_forbidden_imports(DOMAIN) == []


def test_catalog_guard_detects_demo_import_without_importing_it(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    module = catalog / "create.py"
    module.write_text("import app.demo_data\n", encoding="utf-8")
    violations = find_forbidden_imports(tmp_path)
    assert [(violation.path, violation.line, violation.module) for violation in violations] == [
        (module, 1, "app.demo_data"),
    ]


def test_catalog_real_domain_has_no_global_clock_calls() -> None:
    assert find_global_clock_calls(DOMAIN) == []
