"""Trazabilidad de C-22: cada escenario de la spec delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-22.py

Lee los escenarios de la spec, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-22.txt y regenera la tabla de verify-C-22.md. Termina con
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
OUTPUT = EVIDENCE / "trazabilidad-C-22.txt"
VERIFY = EVIDENCE / "verify-C-22.md"
SPECS = REPO / "openspec" / "changes" / "api-dar-turno" / "specs"
APPOINTMENTS_SPEC = SPECS / "appointments-api" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

APPOINTMENTS = "tests/integration/test_api_appointments.py"
CONCURRENCY = "tests/integration/test_appointments_http_concurrency.py"
OPENAPI = "tests/api/test_appointment_openapi.py"

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "appointments-api": {
        "Alta autorizada de turnos": {
            "Recepción da un turno válido": f"{APPOINTMENTS}::test_reception_creates_valid_appointment",
            "El administrador da un turno válido": f"{APPOINTMENTS}::test_admin_creates_valid_appointment",
            "El odontólogo intenta dar un turno": f"{APPOINTMENTS}::test_doctor_cannot_create_appointment_forbidden",
            "Alta sin token": f"{APPOINTMENTS}::test_create_appointment_without_token_unauthorized",
        },
        "Duración y validación del cuerpo": {
            "durationMin explícito se usa en lugar de la duración de la prestación": f"{APPOINTMENTS}::test_explicit_duration_min_overrides_service_default",
            "Sin durationMin se usa la duración de la prestación": f"{APPOINTMENTS}::test_default_service_duration_used_when_duration_min_omitted",
            "startAt sin zona horaria responde 400": f"{APPOINTMENTS}::test_start_at_without_timezone_returns_400",
            "Un campo extra responde 400": f"{APPOINTMENTS}::test_extra_field_in_body_returns_400",
        },
        "Conflictos de agenda": {
            "Choque de profesional": f"{APPOINTMENTS}::test_agenda_conflict_professional_overlap",
            "Choque de sillón": f"{APPOINTMENTS}::test_agenda_conflict_chair_overlap",
            "Choque de profesional y sillón": f"{APPOINTMENTS}::test_agenda_conflict_professional_and_chair_overlap",
            "Fuera de horario": f"{APPOINTMENTS}::test_agenda_conflict_outside_working_hours",
            "En un bloqueo": f"{APPOINTMENTS}::test_agenda_conflict_blocked_time",
        },
        "Referencias y reglas de validez": {
            "En el pasado": f"{APPOINTMENTS}::test_validity_rule_in_the_past",
            "Paciente inexistente": f"{APPOINTMENTS}::test_validity_rule_unknown_patient",
            "Dos referencias inexistentes": f"{APPOINTMENTS}::test_validity_rule_two_unknown_references",
            "Profesional inactivo": f"{APPOINTMENTS}::test_validity_rule_inactive_professional",
        },
        "Atomicidad y cableado del alta": {
            "Un rechazo no deja turno ni historial": f"{APPOINTMENTS}::test_rejection_leaves_no_appointment_nor_history",
            "Dos altas simultáneas del mismo hueco por HTTP": f"{CONCURRENCY}::test_two_concurrent_http_appointments_produce_single_slot",
        },
        "Documentación OpenAPI del alta": {
            "Swagger documenta los status del alta": f"{OPENAPI}::test_appointment_create_in_openapi",
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
            APPOINTMENTS,
            CONCURRENCY,
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


def node_exists(node: str, nodes: set[str]) -> bool:
    clean = node.replace("\\", "/")
    return clean in nodes or any(n.startswith(clean + "[") for n in nodes)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    nodes = collected_nodes()
    problems: list[str] = []
    rows: list[str] = []
    number = 0
    for spec_name, path in (("appointments-api", APPOINTMENTS_SPEC),):
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
        "Salida generada por docs/evidencias/trazabilidad-C-22.py. No editar a mano.",
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
        print("Faltan los marcadores de trazabilidad en verify-C-22.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
