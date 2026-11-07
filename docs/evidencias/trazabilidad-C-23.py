"""Trazabilidad de C-23: cada escenario de la spec delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-23.py

Lee los escenarios de la spec, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-23.txt y regenera la tabla de verify-C-23.md. Termina con
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
OUTPUT = EVIDENCE / "trazabilidad-C-23.txt"
VERIFY = EVIDENCE / "verify-C-23.md"
SPECS = REPO / "openspec" / "changes" / "api-ciclo-de-vida-del-turno" / "specs"
APPOINTMENTS_SPEC = SPECS / "appointments-api" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

CANCEL = "tests/integration/test_api_appointment_cancel.py"
RESCHEDULE = "tests/integration/test_api_appointment_reschedule.py"
STATUS = "tests/integration/test_api_appointment_status.py"
HISTORY = "tests/integration/test_api_appointment_history.py"
OPENAPI = "tests/integration/test_appointment_lifecycle_openapi.py"

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "appointments-api": {
        "Cancelación autorizada de turnos": {
            "Recepción cancela un turno reservado": f"{CANCEL}::test_reception_cancels_reserved_appointment",
            "El administrador cancela un turno confirmado": f"{CANCEL}::test_admin_cancels_confirmed_appointment",
            "Cancelar un turno atendido responde 422": f"{CANCEL}::test_cancel_attended_appointment_returns_422",
            "Cancelar un turno ya cancelado responde 422": f"{CANCEL}::test_cancel_already_cancelled_appointment_returns_422",
            "Cancelar un turno inexistente responde 404": f"{CANCEL}::test_cancel_nonexistent_appointment_returns_404",
            "El odontólogo intenta cancelar un turno": f"{CANCEL}::test_dentist_cannot_cancel_appointment_returns_403",
        },
        "Reprogramación autorizada de turnos": {
            "Reprogramar solo el inicio conserva la duración real": f"{RESCHEDULE}::test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado",
            "Reprogramar con profesional, sillón y duración explícitos": f"{RESCHEDULE}::test_reschedule_with_explicit_professional_chair_and_duration",
            "Choque de profesional al reprogramar": f"{RESCHEDULE}::test_reschedule_professional_overlap_returns_409",
            "Choque de sillón al reprogramar": f"{RESCHEDULE}::test_reschedule_chair_overlap_returns_409",
            "Reprogramar dentro de un bloqueo responde 409": f"{RESCHEDULE}::test_reschedule_inside_block_returns_409",
            "Reprogramar fuera de horario responde 409": f"{RESCHEDULE}::test_reschedule_outside_working_hours_returns_409",
            "Reprogramar al pasado responde 422": f"{RESCHEDULE}::test_reschedule_in_the_past_returns_422",
            "startAt sin zona horaria responde 400": f"{RESCHEDULE}::test_reschedule_start_at_without_timezone_returns_400",
            "Un campo extra en la reprogramación responde 400": f"{RESCHEDULE}::test_reschedule_extra_field_returns_400",
            "Reprogramar un turno inexistente responde 404": f"{RESCHEDULE}::test_reschedule_nonexistent_appointment_returns_404",
            "El odontólogo intenta reprogramar un turno": f"{RESCHEDULE}::test_dentist_cannot_reschedule_returns_403",
            "Reprogramar un turno en estado terminal responde 422": f"{RESCHEDULE}::test_reschedule_terminal_state_appointment_returns_422",
        },
        "Cambio de estado autorizado": {
            "Confirmar un turno reservado": f"{STATUS}::test_confirm_reserved_appointment",
            "Marcar atendido un turno confirmado con inicio pasado": f"{STATUS}::test_mark_attended_confirmed_appointment_with_past_start",
            "Marcar ausente un turno confirmado con inicio pasado": f"{STATUS}::test_mark_absent_confirmed_appointment_with_past_start",
            "Marcar atendido antes del inicio responde 422": f"{STATUS}::test_mark_attended_before_start_returns_422",
            "Doble transición secuencial deja una sola entrada nueva": f"{STATUS}::test_double_sequential_transition_leaves_single_new_entry",
            "Confirmar un turno cancelado responde 422": f"{STATUS}::test_confirm_cancelled_appointment_returns_422",
            'toStatus "cancelado" responde 400': f"{STATUS}::test_to_status_cancelado_returns_400",
            'toStatus "reservado" responde 400': f"{STATUS}::test_to_status_reservado_returns_400",
            "Cambiar el estado de un turno inexistente responde 404": f"{STATUS}::test_change_status_nonexistent_appointment_returns_404",
            "El odontólogo cambia el estado de un turno ajeno": f"{STATUS}::test_dentist_changes_status_of_other_professional_returns_403_from_domain",
        },
        "Historial de turnos": {
            "Historial ascendente con el alta y changedByName": f"{HISTORY}::test_history_ascending_with_creation_and_changed_by_name",
            "Entrada de reprogramación con to reservado y detalle plano": f"{HISTORY}::test_history_reschedule_entry_has_to_reservado_and_flat_detail",
            "Historial de un turno inexistente responde 404": f"{HISTORY}::test_history_nonexistent_appointment_returns_404",
        },
        "Permisos por propiedad del historial": {
            "El odontólogo lee el historial de su propio turno": f"{HISTORY}::test_dentist_reads_own_appointment_history_returns_200",
            "El odontólogo lee el historial de un turno ajeno": f"{HISTORY}::test_dentist_reads_other_professional_history_returns_403",
            "Recepción lee el historial de un turno ajeno": f"{HISTORY}::test_reception_reads_other_professional_history_returns_200",
            "El administrador lee el historial de un turno ajeno": f"{HISTORY}::test_admin_reads_other_professional_history_returns_200",
        },
        "Documentación OpenAPI del ciclo de vida": {
            "Swagger documenta los status del ciclo de vida": f"{OPENAPI}::test_appointment_lifecycle_openapi_documentation",
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
            CANCEL,
            RESCHEDULE,
            STATUS,
            HISTORY,
            OPENAPI,
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
        "Salida generada por docs/evidencias/trazabilidad-C-23.py. No editar a mano.",
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
        print("Faltan los marcadores de trazabilidad en verify-C-23.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
