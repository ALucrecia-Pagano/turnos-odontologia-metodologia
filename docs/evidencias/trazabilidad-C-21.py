"""Trazabilidad de C-21: cada escenario de la spec delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-21.py

Lee los escenarios de la spec, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-21.txt y regenera la tabla de verify-C-21.md. Termina con
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
OUTPUT = EVIDENCE / "trazabilidad-C-21.txt"
VERIFY = EVIDENCE / "verify-C-21.md"
SPECS = REPO / "openspec" / "changes" / "api-horarios-y-bloqueos" / "specs"
APPOINTMENT_SCHEDULING_SPEC = SPECS / "appointment-scheduling" / "spec.md"
WORKING_HOURS_SPEC = SPECS / "working-hours-and-blocks-api" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

DOMAIN_WH = "tests/domain/test_working_hours.py"
API_WH = "tests/integration/test_api_working_hours.py"
API_BLOCKS = "tests/integration/test_api_blocks.py"
CONCURRENCY = "tests/integration/test_availability_concurrency.py"

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "appointment-scheduling": {
        "Turnos que quedan fuera de un horario de atención": {
            "Turno futuro fuera del horario nuevo se lista": f"{DOMAIN_WH}::test_appointments_outside_working_hours_lists_future_occupying_appointment_outside_new_hours",
            "Turno dentro del horario nuevo no se lista": f"{DOMAIN_WH}::test_appointments_outside_working_hours_ignores_appointment_inside_new_hours",
            "Turno cancelado fuera del horario no se lista": f"{DOMAIN_WH}::test_appointments_outside_working_hours_ignores_cancelled_appointment",
            "Turno anterior al momento actual no se lista": f"{DOMAIN_WH}::test_appointments_outside_working_hours_ignores_past_appointment",
            "Turno de otro profesional no se lista": f"{DOMAIN_WH}::test_appointments_outside_working_hours_ignores_other_professional_appointments",
            "Los turnos fuera de horario se devuelven ordenados": f"{DOMAIN_WH}::test_appointments_outside_working_hours_returns_appointments_ordered_by_start_and_id",
        },
    },
    "working-hours-and-blocks-api": {
        "Consulta del horario de atención": {
            "Recepción consulta el horario de un profesional": f"{API_WH}::test_reception_gets_working_hours_returns_200",
            "La odontóloga consulta su propio horario": f"{API_WH}::test_odontologist_gets_own_working_hours_returns_200",
            "La odontóloga consulta el horario de otro profesional": f"{API_WH}::test_odontologist_gets_other_professional_working_hours_returns_403",
            "Consulta del horario sin token": f"{API_WH}::test_get_working_hours_without_token_returns_401",
            "Consulta del horario de un profesional inexistente": f"{API_WH}::test_get_working_hours_unknown_professional_returns_404",
        },
        "Reemplazo del horario de atención": {
            "El administrador reemplaza el horario de un profesional": f"{API_WH}::test_admin_replaces_working_hours_returns_200",
            "La odontóloga reemplaza su propio horario": f"{API_WH}::test_odontologist_replaces_own_working_hours_returns_200",
            "La odontóloga reemplaza el horario de otro profesional": f"{API_WH}::test_odontologist_replaces_other_professional_working_hours_returns_403",
            "Recepción reemplaza un horario": f"{API_WH}::test_reception_replaces_working_hours_returns_403",
            "Reemplazo con lista vacía deja al profesional sin horario": f"{API_WH}::test_replace_working_hours_with_empty_list_returns_empty",
            "Reemplazo con tramos solapados responde 422": f"{API_WH}::test_replace_working_hours_overlapping_returns_422",
            "Reemplazo con un tramo de inicio posterior al fin responde 422": f"{API_WH}::test_replace_working_hours_start_after_end_returns_422",
            "Reemplazo con una hora mal formada responde 400": f"{API_WH}::test_replace_working_hours_malformed_time_returns_400",
            "Reemplazo con fin a las 24:00 se acepta": f"{API_WH}::test_replace_working_hours_end_at_24_accepted_returns_200",
            "Reemplazo del horario de un profesional inexistente": f"{API_WH}::test_replace_working_hours_unknown_professional_returns_404",
            "Reemplazo del horario de un profesional inactivo": f"{API_WH}::test_replace_working_hours_inactive_professional_accepted",
        },
        "Turnos que quedan fuera del horario nuevo": {
            "Un turno que queda fuera del horario nuevo se informa sin cancelarlo": f"{API_WH}::test_replace_working_hours_reports_outside_appointment_without_cancelling",
            "Un turno que sigue dentro del horario nuevo no se informa": f"{API_WH}::test_replace_working_hours_does_not_report_appointment_inside_new_hours",
            "Un turno cancelado fuera del horario nuevo no se informa": f"{API_WH}::test_replace_working_hours_does_not_report_cancelled_appointment",
        },
        "Listado de bloqueos": {
            "Recepción lista los bloqueos de un profesional": f"{API_BLOCKS}::test_reception_lists_blocks_of_professional",
            "La odontóloga lista sus propios bloqueos": f"{API_BLOCKS}::test_odontologist_lists_own_blocks",
            "La odontóloga lista los bloqueos de otro profesional": f"{API_BLOCKS}::test_odontologist_lists_other_professional_blocks_forbidden",
            "El listado con from y to devuelve solo los bloqueos que se solapan": f"{API_BLOCKS}::test_list_blocks_with_from_and_to_filters_overlapping",
            "El listado con un from sin zona horaria responde 400": f"{API_BLOCKS}::test_list_blocks_from_without_timezone_returns_400",
            "El listado de bloqueos de un profesional inexistente responde 404": f"{API_BLOCKS}::test_list_blocks_unknown_professional_returns_404",
        },
        "Alta de bloqueos": {
            "La odontóloga crea un bloqueo propio sin turnos afectados": f"{API_BLOCKS}::test_odontologist_creates_own_block_without_affected_appointments",
            "El administrador crea un bloqueo para cualquier profesional": f"{API_BLOCKS}::test_admin_creates_block_for_any_professional",
            "La odontóloga crea un bloqueo para otro profesional": f"{API_BLOCKS}::test_odontologist_creates_block_for_other_professional_forbidden",
            "Recepción crea un bloqueo": f"{API_BLOCKS}::test_reception_creates_block_forbidden",
            "Un bloqueo con inicio igual al fin responde 422": f"{API_BLOCKS}::test_block_start_equal_to_end_returns_422",
            "Un bloqueo sin zona horaria responde 400": f"{API_BLOCKS}::test_block_without_timezone_returns_400",
            "Un bloqueo para un profesional inexistente responde 404": f"{API_BLOCKS}::test_block_unknown_professional_returns_404",
        },
        "Turnos afectados por un bloqueo nuevo": {
            "Un bloqueo que pisa un turno reservado lo informa sin cancelarlo": f"{API_BLOCKS}::test_block_overlapping_reserved_appointment_reports_it_without_canceling",
            "Un bloqueo que pisa un turno cancelado no lo informa": f"{API_BLOCKS}::test_block_overlapping_canceled_appointment_not_reported",
        },
        "Eliminación de bloqueos": {
            "La odontóloga borra su propio bloqueo": f"{API_BLOCKS}::test_odontologist_deletes_own_block",
            "El administrador borra el bloqueo de cualquier profesional": f"{API_BLOCKS}::test_admin_deletes_block_of_any_professional",
            "La odontóloga borra el bloqueo de otro profesional": f"{API_BLOCKS}::test_odontologist_deletes_other_professional_block_forbidden",
            "Recepción borra un bloqueo": f"{API_BLOCKS}::test_reception_deletes_block_forbidden",
            "Borrar un bloqueo inexistente responde 404": f"{API_BLOCKS}::test_delete_unknown_block_returns_404",
            "Borrar un bloqueo libera el horario": f"{API_BLOCKS}::test_delete_block_frees_schedule",
        },
        "Bloqueos y altas de turnos serializados": {
            "Un bloqueo que espera a un alta informa el turno nuevo": f"{CONCURRENCY}::test_concurrent_block_waiting_for_booking_reports_new_appointment",
            "Un alta que espera a un bloqueo recibe BLOCKED_TIME": f"{CONCURRENCY}::test_concurrent_booking_waiting_for_block_receives_blocked_time",
        },
    },
}


def spec_scenarios(spec_path: Path) -> list[tuple[str, str]]:
    current_req = ""
    scenarios: list[tuple[str, str]] = []
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        req_match = re.match(r"^###\s+Requirement:\s*(.+)$", line)
        if req_match:
            current_req = req_match.group(1).strip()
            continue
        sc_match = re.match(r"^####\s+Scenario:\s*(.+)$", line)
        if sc_match and current_req:
            scenarios.append((current_req, sc_match.group(1).strip()))
    return scenarios


def collected_nodes() -> set[str]:
    test_files = [DOMAIN_WH, API_WH, API_BLOCKS, CONCURRENCY]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", *test_files, "--collect-only", "-q", "-m", "integration or not integration"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    nodes: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.startswith("no tests"):
            clean = line.replace("\\", "/")
            nodes.add(clean)
    return nodes


def node_exists(node: str, nodes: set[str]) -> bool:
    clean = node.replace("\\", "/")
    if clean in nodes:
        return True
    return any(c.startswith(f"{clean}[") for c in nodes)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    nodes = collected_nodes()
    problems: list[str] = []
    rows: list[str] = []
    number = 0
    specs_to_check = [
        ("appointment-scheduling", APPOINTMENT_SCHEDULING_SPEC),
        ("working-hours-and-blocks-api", WORKING_HOURS_SPEC),
    ]
    for spec_name, path in specs_to_check:
        scenarios = spec_scenarios(path)
        mapped = {
            (requirement, scenario)
            for requirement, items in TRACE[spec_name].items()
            for scenario in items
        }
        for requirement, scenario in sorted(mapped - set(scenarios)):
            problems.append(f"sobra en el mapa: {spec_name} / {requirement} / {scenario}")
        for requirement, scenario in scenarios:
            number += 1
            node = TRACE[spec_name].get(requirement, {}).get(scenario)
            if node is None:
                problems.append(f"sin test: {spec_name} / {requirement} / {scenario}")
                continue
            if not node_exists(node, nodes):
                problems.append(f"test inexistente: {node}")
            rows.append(f"| {number} | {spec_name} | {requirement} | {scenario} | `{node}` |")

    table = "\n".join(
        [
            "| # | Spec | Requisito | Escenario | Test |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-21.py. No editar a mano.",
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
        print("Faltan los marcadores de trazabilidad en verify-C-21.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
