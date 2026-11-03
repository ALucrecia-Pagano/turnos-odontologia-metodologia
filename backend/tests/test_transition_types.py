"""Garantías estáticas de la política: mypy rechaza escritura y mutación."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("expression", "diagnostic"),
    [
        ('_TRANSITIONS[S.RESERVED] = frozenset()', 'Unsupported target for indexed assignment'),
        ('_TRANSITIONS[S.CONFIRMED].add(S.RESERVED)', 'has no attribute "add"'),
    ],
    ids=["mapping-assignment", "frozenset-mutation"],
)
def test_transition_policy_rejects_mutation_statically(
    expression: str, diagnostic: str, tmp_path: Path,
) -> None:
    config = tmp_path / "mypy.ini"
    config.write_text("[mypy]\nstrict = True\n", encoding="utf-8")
    code = (
        "from app.domain.appointment.transitions import _TRANSITIONS\n"
        "from app.domain.model import AppointmentStatus as S\n" + expression + "\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--config-file", str(config), "-c", code],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        encoding="utf-8", check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout
    assert "Found 1 error" in result.stdout
