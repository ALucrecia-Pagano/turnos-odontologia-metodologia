"""Trazabilidad de C-28: cada escenario de la spec delta a un test listado por Vitest.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-28.py

Lee los escenarios de la spec delta, comprueba con `vitest list --json` que cada test existe,
genera trazabilidad-C-28.txt y regenera la tabla de verify-C-28.md. Termina con codigo 0
solo si no falta ningun escenario y no sobra ninguna fila.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "trazabilidad-C-28.txt"
VERIFY = EVIDENCE / "verify-C-28.md"
SPEC = (
    REPO
    / "openspec"
    / "changes"
    / "ui-agenda-semanal"
    / "specs"
    / "frontend-agenda"
    / "spec.md"
)
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

T_AGENDA_TIME = "src/features/agenda/agendaTime.test.ts"
T_AGENDA_LAYOUT = "src/features/agenda/agendaLayout.test.ts"
T_USE_AGENDA = "src/features/agenda/useAgenda.test.tsx"
T_AGENDA_TOOLBAR = "src/features/agenda/AgendaToolbar.test.tsx"
T_AGENDA_STYLES = "src/features/agenda/agendaStyles.test.ts"
T_AGENDA_VIEW = "src/features/agenda/AgendaView.test.tsx"
T_AGENDA_PAGE = "src/features/agenda/AgendaPage.test.tsx"

TRACE: dict[str, dict[str, str]] = {
    "Alternancia entre vista diaria y semanal": {
        "Alternancia de día a semana conservando fecha y filtros": (
            f"{T_AGENDA_PAGE} > alterna de día a semana conservando fecha y filtros"
        ),
        "Alternancia de semana a día conservando el día exacto": (
            f"{T_AGENDA_PAGE} > alterna de semana a día conservando el día exacto de anclaje y filtros"
        ),
        "Un view desconocido o ausente cae a vista diaria": (
            f"{T_AGENDA_PAGE} > un view desconocido o ausente cae a vista diaria con botón Día seleccionado"
        ),
    },
    "Vista semanal por profesional y grilla de siete días": {
        "Grilla de siete días de lunes a domingo": (
            f"{T_AGENDA_VIEW} > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles"
        ),
        "La semana se pide en una sola llamada": (
            f"{T_USE_AGENDA} > pide la semana completa en una sola llamada a GET /api/agenda cuando se especifica toDate"
        ),
        "Turno en el día local correcto según timezone": (
            f"{T_AGENDA_LAYOUT} > groupByDayForProfessional genera 7 columnas de lunes a domingo para un profesional, distribuye turnos, horarios y bloqueos en hora local y marca isToday"
        ),
        "Preselección por rol odontólogo": (
            f"{T_AGENDA_PAGE} > preselecciona automáticamente por rol odontólogo su propio professionalId"
        ),
        "Preselección por rol recepción o administrador": (
            f"{T_AGENDA_PAGE} > preselecciona automáticamente por rol recepción al primer profesional activo en el orden del selector"
        ),
        "Turno cancelado visible con texto en vista semanal": (
            f"{T_AGENDA_VIEW} > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles"
        ),
    },
    "Navegación semanal": {
        "Navegación semanal que cruza mes y año": (
            f"{T_AGENDA_PAGE} > navegación semanal avanza y retrocede 7 días cruzando mes y año"
        ),
        "Botón Hoy en vista semanal": (
            f"{T_AGENDA_PAGE} > botón Hoy en vista semanal navega a la fecha actual del Clock"
        ),
    },
    "Indicador accesible de día actual": {
        "Marca Hoy con texto visible y aria-current": (
            f"{T_AGENDA_VIEW} > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles"
        ),
    },
    "Estado vacío y visualización en tablet para vista semanal": {
        "Semana vacía con grilla y aviso informativo": (
            f"{T_AGENDA_VIEW} > muestra grilla y aviso informativo cuando la semana está vacía sin turnos para la profesional"
        ),
        "Semana vacía con filtro de sillón": (
            f"{T_AGENDA_VIEW} > muestra grilla y aviso de filtro cuando la semana está vacía con filtro de sillón activo"
        ),
        "Tarjetas en dos líneas en tablet": (
            f"{T_AGENDA_STYLES} > verifica estáticamente los estilos de tablet y el tag de Hoy para la vista semanal (C-28)"
        ),
    },
}


def spec_scenarios(path: Path) -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    current_requirement: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Requirement: "):
            current_requirement = line.removeprefix("### Requirement: ").strip()
        elif line.startswith("#### Scenario: "):
            if current_requirement is None:
                raise ValueError("Escenario sin requisito")
            scenarios.append((current_requirement, line.removeprefix("#### Scenario: ").strip()))
    return scenarios


def listed_tests() -> set[str]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "NO_COLOR": "1"},
        check=False,
    )
    entries = json.loads(result.stdout[result.stdout.find("[") :])
    nodes: set[str] = set()
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        nodes.add(f"{file} > {entry['name'].split(' > ')[-1]}")
    return nodes


def main() -> int:
    nodes = listed_tests()
    rows: list[str] = []
    problems: list[str] = []
    number = 0
    seen: set[tuple[str, str]] = set()

    for requirement, scenario in spec_scenarios(SPEC):
        number += 1
        seen.add((requirement, scenario))
        node = TRACE.get(requirement, {}).get(scenario)
        if node is None:
            problems.append(f"sin test: {requirement} / {scenario}")
            continue
        for single in node.split(" ; "):
            if single not in nodes:
                problems.append(f"test inexistente: {single}")
        rows.append(f"| {number} | {requirement} | {scenario} | `{node}` |")

    for requirement, scenarios in TRACE.items():
        for scenario in scenarios:
            if (requirement, scenario) not in seen:
                problems.append(f"fila sin escenario en la spec: {requirement} / {scenario}")

    table = "\n".join(["| # | Requisito | Escenario | Test |", "|---|---|---|---|", *rows])
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-28.py. No editar a mano.",
        f"tests listados por vitest: {len(nodes)}",
        f"escenarios en la spec delta: {number}",
        f"escenarios con test listado: {len(rows) - len({p for p in problems if p.startswith('test inexistente')})}",
        *problems,
        f"problemas: {len(problems)}",
        f"{number} escenarios, {len(problems)} problemas",
    ]
    report = "\n".join(lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)

    if VERIFY.exists():
        verify = VERIFY.read_text(encoding="utf-8")
        start = verify.find(TABLE_START)
        end = verify.find(TABLE_END)
        if start == -1 or end == -1:
            print("Faltan los marcadores de trazabilidad en verify-C-28.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
