"""Compara la tabla "Matriz RBAC" de design.md con la copia literal de los tests.

Uso, desde backend/, antes de archivar el change:

    python ../docs/evidencias/matriz-C-19.py

Genera matriz-C-19.txt y termina con codigo distinto de 0 si alguna celda difiere.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
DESIGN = (
    REPO
    / "openspec"
    / "changes"
    / "archive"
    / "2026-11-06-autenticacion-jwt-y-roles"
    / "design.md"
)
OUTPUT = Path(__file__).resolve().with_name("matriz-C-19.txt")
HEADING = "#### Matriz RBAC"
EXPECTED_ROWS = 34

sys.path.insert(0, str(BACKEND))

from tests.auth.rbac_matrix import MATRIX  # noqa: E402

ROW = re.compile(
    r"^\|\s*(?P<number>\d+)\s*\|\s*`(?P<resource>\w+)`\s*\|\s*`(?P<action>\w+)`\s*\|"
    r"\s*(?P<odontologo>[^|]+?)\s*\|\s*(?P<recepcion>[^|]+?)\s*\|"
    r"\s*(?P<administrador>[^|]+?)\s*\|\s*(?P<message>[^|]+?)\s*\|\s*$"
)
COLUMNS = ("resource", "action", "odontologo", "recepcion", "administrador", "message")


def design_rows() -> dict[int, dict[str, str]]:
    text = DESIGN.read_text(encoding="utf-8")
    section = text[text.index(HEADING) :]
    rows: dict[int, dict[str, str]] = {}
    for line in section.splitlines():
        match = ROW.match(line)
        if match:
            rows[int(match["number"])] = {column: match[column] for column in COLUMNS}
        elif rows and not line.startswith("|"):
            break
    return rows


def main() -> int:
    rows = design_rows()
    literal = {row.number: row for row in MATRIX}
    differences: list[str] = []
    if len(rows) != EXPECTED_ROWS:
        differences.append(f"design.md tiene {len(rows)} filas, se esperaban {EXPECTED_ROWS}")
    for number in sorted(set(rows) | set(literal)):
        if number not in rows or number not in literal:
            differences.append(f"fila {number}: esta en un solo lado")
            continue
        for column in COLUMNS:
            expected = rows[number][column]
            actual = getattr(literal[number], column)
            if expected != actual:
                differences.append(
                    f"fila {number}, {column}: design.md={expected!r} copia={actual!r}"
                )

    cells = len(rows) * 3
    allowed = sum(
        row[column] != "—"
        for row in rows.values()
        for column in ("odontologo", "recepcion", "administrador")
    )
    lines = [
        "Salida generada por docs/evidencias/matriz-C-19.py. No editar a mano.",
        f"filas en design.md: {len(rows)}",
        f"celdas: {cells} ({allowed} permitidas, {cells - allowed} denegadas)",
        f"diferencias contra tests/auth/rbac_matrix.py: {len(differences)}",
        *differences,
        f"codigo de salida: {1 if differences else 0}",
    ]
    report = "\n".join(lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)
    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())
