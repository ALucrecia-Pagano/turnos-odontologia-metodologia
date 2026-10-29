from pathlib import Path

import pytest

from tests.domain.import_guard import (
    find_forbidden_imports,
    find_global_clock_calls,
    format_clock_calls,
)


def _write_module(root: Path, relpath: str, source: str) -> Path:
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_find_global_clock_calls_datetime_now_reports_one_access(tmp_path: Path) -> None:
    _write_module(
        tmp_path,
        "model.py",
        "from datetime import datetime, timezone\n\nstamp = datetime.now(timezone.utc)\n",
    )

    calls = find_global_clock_calls(tmp_path)

    assert [c.expression for c in calls] == ["datetime.now"]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "from datetime import datetime\n\na = datetime.utcnow()\nb = datetime.today()\n",
            ["datetime.utcnow", "datetime.today"],
            id="utcnow-y-today",
        ),
        pytest.param(
            "from datetime import date\n\nd = date.today()\n",
            ["date.today"],
            id="date-today",
        ),
        pytest.param(
            "import datetime\n\na = datetime.datetime.now()\nb = datetime.date.today()\n",
            ["datetime.datetime.now", "datetime.date.today"],
            id="por-el-modulo",
        ),
        pytest.param(
            "import datetime as dt\nfrom datetime import datetime as D\n\n"
            "a = dt.datetime.now()\nb = D.now()\n",
            ["dt.datetime.now", "D.now"],
            id="con-alias",
        ),
        pytest.param(
            "from datetime import datetime\n\nreloj = datetime.now\n",
            ["datetime.now"],
            id="referencia-sin-llamar",
        ),
        pytest.param(
            "from datetime import datetime\n\n\ndef f() -> object:\n    return datetime.now()\n",
            ["datetime.now"],
            id="dentro-de-una-funcion",
        ),
        pytest.param(
            "from datetime import *\n",
            ["from datetime import *"],
            id="import-con-asterisco",
        ),
    ],
)
def test_find_global_clock_calls_clock_access_reports_expression(
    tmp_path: Path, source: str, expected: list[str]
) -> None:
    _write_module(tmp_path, "model.py", source)

    calls = find_global_clock_calls(tmp_path)

    assert [c.expression for c in calls] == expected


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "def f(context: object) -> object:\n    return context.now\n",
            id="context-now",
        ),
        pytest.param(
            "def f(now: object) -> object:\n    return now\n",
            id="parametro-now",
        ),
        pytest.param(
            "from datetime import datetime, timedelta, timezone\n\n"
            "a = datetime(2026, 10, 20, tzinfo=timezone.utc)\n"
            "b = timedelta(minutes=30)\n",
            id="construccion-de-instantes",
        ),
        pytest.param(
            'from datetime import datetime\n\n\ndef f() -> datetime:\n    """Usa datetime.now() solo en la doc."""\n'
            "    raise NotImplementedError\n",
            id="now-en-un-docstring",
        ),
        pytest.param(
            'from datetime import datetime\n\nx = getattr(datetime, "now")()\n',
            id="getattr-no-detectado",
        ),
        pytest.param(
            "from datetime import datetime\n\nd = datetime\nx = d.now()\n",
            id="reasignacion-no-detectada",
        ),
    ],
)
def test_find_global_clock_calls_non_clock_access_reports_nothing(
    tmp_path: Path, source: str
) -> None:
    _write_module(tmp_path, "model.py", source)

    calls = find_global_clock_calls(tmp_path)

    assert calls == []


@pytest.mark.parametrize(
    ("source", "expected_module"),
    [
        pytest.param("import time\n", "time", id="import-time"),
        pytest.param("from time import time as t\n", "time", id="from-time-as"),
    ],
)
def test_find_forbidden_imports_time_module_reports_time(
    tmp_path: Path, source: str, expected_module: str
) -> None:
    _write_module(tmp_path, "model.py", source)

    violations = find_forbidden_imports(tmp_path)

    assert [v.module for v in violations] == [expected_module]


def test_find_global_clock_calls_access_in_rules_file_reports_path_and_line(
    tmp_path: Path,
) -> None:
    source = (
        "from datetime import datetime, timezone\n"
        "\n"
        "\n"
        "stamp = datetime.now(timezone.utc)\n"
    )
    _write_module(tmp_path, "rules/past.py", source)

    calls = find_global_clock_calls(tmp_path)

    assert [(c.path.as_posix().endswith("rules/past.py"), c.line, c.expression) for c in calls] == [
        (True, 4, "datetime.now")
    ]


def test_find_global_clock_calls_several_accesses_are_ordered_by_line(tmp_path: Path) -> None:
    source = (
        "from datetime import datetime\n"
        "\n"
        "\n"
        "def f() -> object:\n"
        "    return datetime.now()\n"
        "\n"
        "\n"
        "later = datetime.utcnow()\n"
    )
    _write_module(tmp_path, "model.py", source)

    calls = find_global_clock_calls(tmp_path)

    assert [(c.line, c.expression) for c in calls] == [(5, "datetime.now"), (8, "datetime.utcnow")]


def test_find_global_clock_calls_two_accesses_in_order_are_reported_in_order(
    tmp_path: Path,
) -> None:
    source = "from datetime import datetime\n\na = datetime.now()\nb = datetime.today()\n"
    _write_module(tmp_path, "model.py", source)

    calls = find_global_clock_calls(tmp_path)

    assert [(c.line, c.expression) for c in calls] == [(3, "datetime.now"), (4, "datetime.today")]


def test_format_clock_calls_one_access_gives_one_line(tmp_path: Path) -> None:
    source = "from datetime import datetime\n\n\nstamp = datetime.now()\n"
    _write_module(tmp_path, "app/domain/rules/past.py", source)

    text = format_clock_calls(find_global_clock_calls(tmp_path), tmp_path)

    assert text == (
        "app/domain/rules/past.py:4: reloj global en el dominio: 'datetime.now' "
        "(usar el now inyectado)"
    )


def test_format_clock_calls_two_accesses_give_one_line_each(tmp_path: Path) -> None:
    source = "from datetime import datetime\n\n\na = datetime.now()\nb = datetime.today()\n"
    _write_module(tmp_path, "app/domain/rules/past.py", source)

    text = format_clock_calls(find_global_clock_calls(tmp_path), tmp_path)

    assert text == (
        "app/domain/rules/past.py:4: reloj global en el dominio: 'datetime.now' "
        "(usar el now inyectado)\n"
        "app/domain/rules/past.py:5: reloj global en el dominio: 'datetime.today' "
        "(usar el now inyectado)"
    )
