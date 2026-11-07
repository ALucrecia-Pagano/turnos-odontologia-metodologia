"""Trazabilidad de C-24: cada escenario de la spec delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-24.py

Lee los escenarios de la spec, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-24.txt y regenera la tabla de verify-C-24.md. Termina con
codigo 0 solo si no falta ningun escenario y no sobra ninguna fila.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "trazabilidad-C-24.txt"
VERIFY = EVIDENCE / "verify-C-24.md"
SPECS = REPO / "openspec" / "changes" / "archive" / "2026-11-07-api-consulta-de-agenda" / "specs"
AGENDA_SPEC = SPECS / "agenda-api" / "spec.md"
APPOINTMENTS_SPEC = SPECS / "appointments-api" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

AGENDA = "tests/integration/test_api_agenda.py"
MIDNIGHT = "tests/integration/test_api_agenda_midnight.py"
VALIDATION = "tests/integration/test_api_agenda_validation.py"
DETAIL = "tests/integration/test_api_appointment_detail.py"

TEST_FILES = (AGENDA, MIDNIGHT, VALIDATION, DETAIL)

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "agenda-api": {
        "Parámetros y validación de la agenda": {
            "Falta el parámetro from responde 400": f"{VALIDATION}::test_missing_from_returns_400",
            "Falta el parámetro to responde 400": f"{VALIDATION}::test_missing_to_returns_400",
            "Una fecha con formato inválido responde 400": f"{VALIDATION}::test_invalid_date_format_returns_400",
            "Un to anterior al from responde 400": f"{VALIDATION}::test_to_before_from_returns_400",
            "Un rango de más de 31 días responde 400": f"{VALIDATION}::test_range_longer_than_31_days_returns_400",
            "Un professionalId malformado responde 400": f"{VALIDATION}::test_malformed_professional_id_returns_400",
            "Un chairId malformado responde 400": f"{VALIDATION}::test_malformed_chair_id_returns_400",
            "Un parámetro de query desconocido responde 400": f"{VALIDATION}::test_unknown_query_parameter_returns_400",
            "La agenda sin token responde 401": f"{VALIDATION}::test_agenda_without_token_returns_401",
        },
        "Sobre de respuesta de la agenda": {
            "La agenda de un día devuelve el sobre completo": f"{AGENDA}::test_agenda_for_one_day_returns_complete_envelope",
            "La agenda de una semana devuelve los turnos del rango": f"{AGENDA}::test_agenda_for_a_week_returns_the_appointments_of_the_range",
            "Un rango de ocho días cruza dos semanas": f"{AGENDA}::test_agenda_of_eight_days_crosses_two_weeks_in_order",
            "Un rango de 31 días cruza meses": f"{AGENDA}::test_agenda_of_31_days_crosses_months",
        },
        "Filtros y visibilidad de la agenda": {
            "El filtro por profesional devuelve sus turnos": f"{AGENDA}::test_agenda_filter_by_professional_returns_their_appointments",
            "El filtro por sillón devuelve sus turnos": f"{AGENDA}::test_agenda_filter_by_chair_returns_their_appointments",
            "Los filtros de profesional y sillón se combinan": f"{AGENDA}::test_agenda_professional_and_chair_filters_combine",
            "Un professionalId inexistente devuelve listas vacías": f"{AGENDA}::test_agenda_unknown_professional_returns_empty_lists",
            "Un chairId inexistente deja vacíos los turnos pero no los horarios ni los bloqueos": f"{AGENDA}::test_agenda_unknown_chair_empties_appointments_but_not_hours_or_blocks",
            "El chairId no filtra horarios ni bloqueos": f"{AGENDA}::test_agenda_chair_filter_does_not_filter_hours_or_blocks",
            "El odontólogo ve los turnos de otro profesional": f"{AGENDA}::test_agenda_dentist_sees_appointments_of_another_professional",
        },
        "Horarios de atención del rango": {
            "La plantilla semanal incluye a todos los profesionales": f"{AGENDA}::test_agenda_working_hours_template_includes_all_professionals",
            "El filtro por profesional también filtra los horarios": f"{AGENDA}::test_agenda_professional_filter_also_filters_working_hours",
        },
        "Bloqueos del rango": {
            "Un bloqueo dentro del rango se devuelve con su motivo": f"{AGENDA}::test_agenda_block_inside_range_is_returned_with_reason",
            "Un bloqueo que empieza antes del rango se incluye": f"{AGENDA}::test_agenda_block_starting_before_the_range_is_included",
            "El filtro por profesional también filtra los bloqueos": f"{AGENDA}::test_agenda_professional_filter_also_filters_blocks",
            "Un bloqueo que cruza la medianoche aparece en los dos días": f"{MIDNIGHT}::test_block_crossing_midnight_appears_on_both_days",
        },
        "Estados y orden de la agenda": {
            "Los turnos cancelados se incluyen con su estado": f"{AGENDA}::test_agenda_includes_cancelled_appointments_with_their_status",
            "Turnos, bloqueos y horarios salen en orden estable": f"{AGENDA}::test_agenda_orders_appointments_blocks_and_working_hours",
        },
        "Borde de medianoche de los turnos": {
            "Un turno que termina a las 00:00 solo aparece en su día": (
                f"{MIDNIGHT}::test_appointment_ending_at_midnight_appears_only_on_its_own_day"
                f" ; {MIDNIGHT}::test_appointment_starting_at_midnight_appears_only_on_its_own_day"
            ),
        },
    },
    "appointments-api": {
        "Consulta de un turno por id": {
            "El detalle devuelve el turno enriquecido": f"{DETAIL}::test_detail_returns_the_enriched_appointment",
            "Un turno inexistente responde 404": f"{DETAIL}::test_detail_of_unknown_appointment_returns_404",
            "Un id con UUID malformado responde 400": f"{DETAIL}::test_detail_with_malformed_uuid_returns_400",
            "El detalle sin token responde 401": f"{DETAIL}::test_detail_without_token_returns_401",
            "El odontólogo lee el detalle de un turno ajeno": f"{DETAIL}::test_dentist_reads_the_detail_of_another_professionals_appointment",
        },
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
            scenario = line.removeprefix("#### Scenario: ").strip()
            scenarios.append((current_requirement, scenario))
    return scenarios


def collected_nodes() -> set[str]:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
    }
    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-m",
            "integration or not integration",
            "-p",
            "no:cacheprovider",
            *TEST_FILES,
        ],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    nodes: set[str] = set()
    for line in (result.stdout + result.stderr).splitlines():
        line = line.strip()
        if "::" in line and not line.startswith("ERROR") and not line.startswith("warnings"):
            node = line.split()[0].replace("\\", "/")
            nodes.add(node)
    return nodes


def node_exists(node: str, collected: set[str]) -> bool:
    clean_node = re.sub(r"\[.*\]$", "", node).replace("\\", "/")
    return clean_node in collected


def main() -> int:
    nodes = collected_nodes()
    specs: list[tuple[str, Path]] = [
        ("agenda-api", AGENDA_SPEC),
        ("appointments-api", APPOINTMENTS_SPEC),
    ]

    rows: list[str] = []
    problems: list[str] = []
    number = 0

    for spec_name, spec_path in specs:
        for requirement, scenario in spec_scenarios(spec_path):
            number += 1
            node = TRACE.get(spec_name, {}).get(requirement, {}).get(scenario)
            if node is None:
                problems.append(f"sin test: {spec_name} / {requirement} / {scenario}")
                continue
            for single in node.split(" ; "):
                if not node_exists(single, nodes):
                    problems.append(f"test inexistente: {single}")
            rows.append(f"| {number} | {spec_name} | {requirement} | {scenario} | `{node}` |")

    table = "\n".join(
        [
            "| # | Spec | Requisito | Escenario | Test |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-24.py. No editar a mano.",
        f"tests recolectados por pytest: {len(nodes)}",
        f"escenarios en la spec delta: {number}",
        f"escenarios con test recolectado: {len(rows) - sum(p.startswith('test inexistente') for p in problems)}",
        f"problemas: {len(problems)}",
        f"{number} escenarios, {len(problems)} problemas",
        *problems,
    ]
    report = "\n".join(lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)

    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start == -1 or end == -1:
        print("Faltan los marcadores de trazabilidad en verify-C-24.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
