from pathlib import Path

import pytest

from tests.domain.import_guard import (
    ForbiddenImport,
    find_forbidden_imports,
    format_violations,
)


def _write_module(root: Path, relpath: str, source: str) -> Path:
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_find_forbidden_imports_framework_import_reports_module(tmp_path: Path) -> None:
    _write_module(tmp_path, "model.py", "import fastapi\n")

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == ["fastapi"]


@pytest.mark.parametrize(
    "source",
    [
        "import datetime\n",
        "from . import model\n",
        "from .rules import overlap\n",
        "from app.domain.model import Appointment\n",
        "from __future__ import annotations\n",
        "from collections.abc import Sequence\n",
        "import tzdata\n",
    ],
)
def test_find_forbidden_imports_allowed_import_reports_nothing(
    tmp_path: Path, source: str
) -> None:
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert violations == []


@pytest.mark.parametrize(
    ("source", "expected_module"),
    [
        ("from sqlalchemy.orm import Session\n", "sqlalchemy.orm"),
        ("import redis\n", "redis"),
        ("import pydantic\n", "pydantic"),
        ("import os\n", "os"),
        ("from pathlib import Path\n", "pathlib"),
        ("from app.api import routers\n", "app.api"),
        ("import app.db\n", "app.db"),
        ("from app import domain\n", "app"),
    ],
)
def test_find_forbidden_imports_forbidden_import_reports_one_violation(
    tmp_path: Path, source: str, expected_module: str
) -> None:
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == [expected_module]


@pytest.mark.parametrize(
    ("source", "expected_module"),
    [
        ("import fastapi_utils\n", "fastapi_utils"),
        ("import datetime_utils\n", "datetime_utils"),
        ("from datetimes import parse\n", "datetimes"),
    ],
)
def test_find_forbidden_imports_name_with_allowed_prefix_is_distinct_module(
    tmp_path: Path, source: str, expected_module: str
) -> None:
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == [expected_module]


def test_find_forbidden_imports_absolute_import_of_own_package_is_allowed(
    tmp_path: Path,
) -> None:
    _write_module(tmp_path, "model.py", "import app.domain.model\n")

    assert find_forbidden_imports(tmp_path) == []


def test_find_forbidden_imports_import_inside_function_body_is_reported(
    tmp_path: Path,
) -> None:
    source = "def load() -> None:\n    import redis\n"
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == ["redis"]


def test_find_forbidden_imports_import_under_type_checking_is_reported(
    tmp_path: Path,
) -> None:
    source = "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    import fastapi\n"
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == ["fastapi"]


def test_find_forbidden_imports_import_in_subpackage_identifies_that_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "overlap.py").write_text("import pydantic\n", encoding="utf-8")
    _write_module(tmp_path, "model.py", "import datetime\n")

    violations = find_forbidden_imports(tmp_path)

    assert [(v.path.relative_to(tmp_path).as_posix(), v.module) for v in violations] == [
        ("rules/overlap.py", "pydantic")
    ]


def test_find_forbidden_imports_two_files_reports_both_in_path_order(
    tmp_path: Path,
) -> None:
    _write_module(tmp_path, "b_rules.py", "import redis\n")
    _write_module(tmp_path, "a_model.py", "import fastapi\n")

    violations = find_forbidden_imports(tmp_path)

    assert [(v.path.name, v.module) for v in violations] == [
        ("a_model.py", "fastapi"),
        ("b_rules.py", "redis"),
    ]


@pytest.mark.parametrize(
    ("relpath", "source", "expected_line"),
    [
        ("model.py", "import datetime\nimport enum\nimport fastapi\n", 3),
        ("rules/overlap.py", "\n\n\n\nimport sqlalchemy.orm\n", 5),
    ],
)
def test_find_forbidden_imports_violation_reports_file_line_and_module(
    tmp_path: Path, relpath: str, source: str, expected_line: int
) -> None:
    _write_module(tmp_path, relpath, source)

    (violation,) = find_forbidden_imports(tmp_path)

    assert violation.path.as_posix().endswith(relpath)
    assert violation.line == expected_line
    assert violation.module == ("fastapi" if relpath == "model.py" else "sqlalchemy.orm")


def test_find_forbidden_imports_dynamic_import_is_not_detected(tmp_path: Path) -> None:
    _write_module(tmp_path, "model.py", '__import__("fastapi")\n')

    assert find_forbidden_imports(tmp_path) == []


def test_format_violations_single_violation_is_one_line(tmp_path: Path) -> None:
    violation = ForbiddenImport(tmp_path / "app" / "domain" / "model.py", 3, "fastapi")

    message = format_violations([violation], tmp_path)

    assert message == "app/domain/model.py:3: import no permitido en el dominio: 'fastapi'"


def test_format_violations_two_violations_are_two_lines(tmp_path: Path) -> None:
    violations = [
        ForbiddenImport(tmp_path / "app" / "domain" / "model.py", 3, "fastapi"),
        ForbiddenImport(tmp_path / "app" / "domain" / "rules" / "overlap.py", 10, "redis"),
    ]

    message = format_violations(violations, tmp_path)

    assert message.splitlines() == [
        "app/domain/model.py:3: import no permitido en el dominio: 'fastapi'",
        "app/domain/rules/overlap.py:10: import no permitido en el dominio: 'redis'",
    ]
