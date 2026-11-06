"""Trazabilidad de C-20: cada escenario de la spec delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-20.py

Lee los escenarios de la spec, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-20.txt y regenera la tabla de verify-C-20.md. Termina con
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
OUTPUT = EVIDENCE / "trazabilidad-C-20.txt"
VERIFY = EVIDENCE / "verify-C-20.md"
SPECS = REPO / "openspec" / "changes" / "api-catalogos-y-pacientes" / "specs"
CATALOG_SPEC = SPECS / "catalog-and-patients" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

PROFESSIONALS = "tests/integration/test_api_professionals.py"
CHAIRS = "tests/integration/test_api_chairs.py"
SERVICES = "tests/integration/test_api_services.py"
PATIENTS = "tests/integration/test_api_patients.py"
DEACTIVATION = "tests/integration/test_api_deactivation.py"

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "catalog-and-patients": {
        "Endpoints de profesionales": {
            "Alta exitosa de profesional con matrícula responde 201": f"{PROFESSIONALS}::test_create_professional_with_license_responds_201",
            "Edición exitosa de profesional responde 200": f"{PROFESSIONALS}::test_update_professional_responds_200",
            "Edición de profesional conservando su propio nombre responde 200": f"{PROFESSIONALS}::test_update_professional_conserving_own_name_responds_200",
            "Edición de profesional inexistente responde 404": f"{PROFESSIONALS}::test_update_professional_nonexistent_responds_404",
            "Listado de profesionales con filtro active verdadero": f"{PROFESSIONALS}::test_list_professionals_with_active_filter_true",
            "Listado de profesionales sin filtro incluye inactivos en orden alfabético": f"{PROFESSIONALS}::test_list_professionals_without_filter_includes_inactive_alphabetical",
            "Recepción lista profesionales y responde 200": f"{PROFESSIONALS}::test_reception_lists_professionals_responds_200",
            "El odontólogo lista profesionales y responde 200": f"{PROFESSIONALS}::test_doctor_lists_professionals_responds_200",
            "Detalle de profesional existente responde 200": f"{PROFESSIONALS}::test_detail_professional_existing_responds_200",
            "Detalle de profesional inexistente responde 404": f"{PROFESSIONALS}::test_detail_professional_nonexistent_responds_404",
            "Consulta de profesionales sin token responde 401": f"{PROFESSIONALS}::test_consult_professionals_without_token_responds_401",
            "Alta de profesional rechazada para rol recepción con 403": f"{PROFESSIONALS}::test_create_professional_rejected_for_reception_403",
            "Alta de profesional rechazada para rol odontólogo con 403": f"{PROFESSIONALS}::test_create_professional_rejected_for_doctor_403",
            "Edición de profesional rechazada para rol recepción con 403": f"{PROFESSIONALS}::test_update_professional_rejected_for_reception_403",
            "Edición de profesional rechazada para rol odontólogo con 403": f"{PROFESSIONALS}::test_update_professional_rejected_for_doctor_403",
            "Alta de profesional con nombre vacío responde 422": f"{PROFESSIONALS}::test_create_professional_empty_name_responds_422",
            "Alta de profesional con cuerpo malformado responde 400": f"{PROFESSIONALS}::test_create_professional_malformed_body_responds_400",
        },
        "Endpoints de sillones": {
            "Alta exitosa de sillón responde 201": f"{CHAIRS}::test_create_chair_responds_201",
            "Edición exitosa de sillón responde 200": f"{CHAIRS}::test_update_chair_responds_200",
            "Edición de sillón conservando su propio nombre responde 200": f"{CHAIRS}::test_update_chair_conserving_own_name_responds_200",
            "Edición de sillón con el nombre de otro sillón responde 409": f"{CHAIRS}::test_update_chair_with_name_of_another_responds_409",
            "Edición de sillón inexistente responde 404": f"{CHAIRS}::test_update_chair_nonexistent_responds_404",
            "Listado de sillones con filtro active verdadero": f"{CHAIRS}::test_list_chairs_with_active_filter_true",
            "Listado de sillones con filtro active falso devuelve solo inactivos": f"{CHAIRS}::test_list_chairs_with_active_filter_false_returns_only_inactive",
            "Listado de sillones sin filtro incluye inactivos en orden alfabético": f"{CHAIRS}::test_list_chairs_without_filter_includes_inactive_alphabetical",
            "Recepción lista sillones y responde 200": f"{CHAIRS}::test_reception_lists_chairs_responds_200",
            "El odontólogo lista sillones y responde 200": f"{CHAIRS}::test_doctor_lists_chairs_responds_200",
            "Detalle de sillón existente responde 200": f"{CHAIRS}::test_detail_chair_existing_responds_200",
            "Detalle de sillón inexistente responde 404": f"{CHAIRS}::test_detail_chair_nonexistent_responds_404",
            "Consulta de sillones sin token responde 401": f"{CHAIRS}::test_consult_chairs_without_token_responds_401",
            "Alta de sillón rechazada para rol recepción con 403": f"{CHAIRS}::test_create_chair_rejected_for_reception_403",
            "Alta de sillón rechazada para rol odontólogo con 403": f"{CHAIRS}::test_create_chair_rejected_for_doctor_403",
            "Edición de sillón rechazada para rol recepción con 403": f"{CHAIRS}::test_update_chair_rejected_for_reception_403",
            "Edición de sillón rechazada para rol odontólogo con 403": f"{CHAIRS}::test_update_chair_rejected_for_doctor_403",
            "Alta de sillón con nombre duplicado responde 409": f"{CHAIRS}::test_create_chair_duplicate_name_responds_409",
            "Alta de sillón con nombre vacío responde 422": f"{CHAIRS}::test_create_chair_empty_name_responds_422",
            "Alta de sillón con cuerpo malformado responde 400": f"{CHAIRS}::test_create_chair_malformed_body_responds_400",
        },
        "Endpoints de prestaciones": {
            "Alta exitosa de prestación responde 201": f"{SERVICES}::test_create_service_responds_201",
            "Edición exitosa de prestación responde 200": f"{SERVICES}::test_update_service_responds_200",
            "Edición de prestación conservando su propio nombre responde 200": f"{SERVICES}::test_update_service_conserving_own_name_responds_200",
            "Edición de prestación con el nombre de otra prestación responde 409": f"{SERVICES}::test_update_service_with_name_of_another_responds_409",
            "Edición de prestación inexistente responde 404": f"{SERVICES}::test_update_service_nonexistent_responds_404",
            "Listado de prestaciones con filtro active verdadero": f"{SERVICES}::test_list_services_with_active_filter_true",
            "Listado de prestaciones sin filtro incluye inactivos en orden alfabético": f"{SERVICES}::test_list_services_without_filter_includes_inactive_alphabetical",
            "Recepción lista prestaciones y responde 200": f"{SERVICES}::test_reception_lists_services_responds_200",
            "El odontólogo lista prestaciones y responde 200": f"{SERVICES}::test_doctor_lists_services_responds_200",
            "Detalle de prestación existente responde 200": f"{SERVICES}::test_detail_service_existing_responds_200",
            "Detalle de prestación inexistente responde 404": f"{SERVICES}::test_detail_service_nonexistent_responds_404",
            "Consulta de prestaciones sin token responde 401": f"{SERVICES}::test_consult_services_without_token_responds_401",
            "Alta de prestación rechazada para rol recepción con 403": f"{SERVICES}::test_create_service_rejected_for_reception_403",
            "Alta de prestación rechazada para rol odontólogo con 403": f"{SERVICES}::test_create_service_rejected_for_doctor_403",
            "Edición de prestación rechazada para rol recepción con 403": f"{SERVICES}::test_update_service_rejected_for_reception_403",
            "Edición de prestación rechazada para rol odontólogo con 403": f"{SERVICES}::test_update_service_rejected_for_doctor_403",
            "Alta de prestación con nombre duplicado responde 409": f"{SERVICES}::test_create_service_duplicate_name_responds_409",
            "Alta de prestación con duración inválida responde 422": f"{SERVICES}::test_create_service_invalid_duration_responds_422",
            "Alta de prestación con nombre vacío responde 422": f"{SERVICES}::test_create_service_empty_name_responds_422",
            "Alta de prestación con cuerpo malformado responde 400": f"{SERVICES}::test_create_service_malformed_body_responds_400",
        },
        "Endpoints de pacientes": {
            "Alta exitosa de paciente por recepción responde 201": f"{PATIENTS}::test_create_patient_by_reception_responds_201",
            "Alta exitosa de paciente por administrador responde 201": f"{PATIENTS}::test_create_patient_by_admin_responds_201",
            "Edición exitosa de paciente responde 200": f"{PATIENTS}::test_update_patient_responds_200",
            "Edición de paciente conservando su propio DNI responde 200": f"{PATIENTS}::test_update_patient_conserving_own_dni_responds_200",
            "Edición de paciente con el DNI de otro paciente responde 409": f"{PATIENTS}::test_update_patient_with_dni_of_another_responds_409",
            "Edición de paciente inexistente responde 404": f"{PATIENTS}::test_update_patient_nonexistent_responds_404",
            "Búsqueda de pacientes por parte del nombre": f"{PATIENTS}::test_search_patients_by_name_part",
            "Búsqueda de pacientes sin tilde no encuentra el nombre con tilde": f"{PATIENTS}::test_search_patients_without_accent_does_not_find_accented_name",
            "Búsqueda de pacientes por inicio del DNI": f"{PATIENTS}::test_search_patients_by_dni_prefix",
            "El odontólogo lista pacientes y responde 200": f"{PATIENTS}::test_doctor_lists_patients_responds_200",
            "Detalle de paciente existente responde 200": f"{PATIENTS}::test_detail_patient_existing_responds_200",
            "Detalle de paciente inexistente responde 404": f"{PATIENTS}::test_detail_patient_nonexistent_responds_404",
            "Consulta de pacientes sin token responde 401": f"{PATIENTS}::test_consult_patients_without_token_responds_401",
            "Alta de paciente rechazada para rol odontólogo con 403": f"{PATIENTS}::test_create_patient_rejected_for_doctor_403",
            "Edición de paciente rechazada para rol odontólogo con 403": f"{PATIENTS}::test_update_patient_rejected_for_doctor_403",
            "Alta de paciente con DNI duplicado responde 409": f"{PATIENTS}::test_create_patient_duplicate_dni_responds_409",
            "Alta de paciente con DNI de formato inválido responde 422": f"{PATIENTS}::test_create_patient_invalid_dni_format_responds_422",
            "Alta de paciente con nombre vacío responde 422": f"{PATIENTS}::test_create_patient_empty_name_responds_422",
            "Alta de paciente con cuerpo malformado responde 400": f"{PATIENTS}::test_create_patient_malformed_body_responds_400",
            "Desactivación de paciente no existe en la API": f"{PATIENTS}::test_patient_deactivation_does_not_exist_in_api",
            "Borrado de paciente no existe en la API": f"{PATIENTS}::test_patient_deletion_does_not_exist_in_api",
        },
        "Desactivación y reactivación en la API": {
            "Desactivar profesional activo responde 200": f"{DEACTIVATION}::test_deactivate_professional_active_responds_200",
            "Reactivar profesional inactivo responde 200": f"{DEACTIVATION}::test_reactivate_professional_inactive_responds_200",
            "Desactivar profesional ya inactivo responde 200 sin cambios": f"{DEACTIVATION}::test_deactivate_professional_already_inactive_responds_200_no_changes",
            "Reactivar profesional ya activo responde 200 sin cambios": f"{DEACTIVATION}::test_reactivate_professional_already_active_responds_200_no_changes",
            "Desactivar profesional inexistente responde 404": f"{DEACTIVATION}::test_deactivate_professional_nonexistent_responds_404",
            "Reactivar profesional inexistente responde 404": f"{DEACTIVATION}::test_reactivate_professional_nonexistent_responds_404",
            "Desactivar profesional rechazado para rol recepción con 403": f"{DEACTIVATION}::test_deactivate_professional_rejected_for_reception_403",
            "Desactivar profesional rechazado para rol odontólogo con 403": f"{DEACTIVATION}::test_deactivate_professional_rejected_for_doctor_403",
            "Reactivar profesional rechazado para rol recepción con 403": f"{DEACTIVATION}::test_reactivate_professional_rejected_for_reception_403",
            "Reactivar profesional rechazado para rol odontólogo con 403": f"{DEACTIVATION}::test_reactivate_professional_rejected_for_doctor_403",
            "Desactivar sillón activo responde 200": f"{DEACTIVATION}::test_deactivate_chair_active_responds_200",
            "Reactivar sillón inactivo responde 200": f"{DEACTIVATION}::test_reactivate_chair_inactive_responds_200",
            "Desactivar sillón ya inactivo responde 200 sin cambios": f"{DEACTIVATION}::test_deactivate_chair_already_inactive_responds_200_no_changes",
            "Reactivar sillón ya activo responde 200 sin cambios": f"{DEACTIVATION}::test_reactivate_chair_already_active_responds_200_no_changes",
            "Desactivar sillón inexistente responde 404": f"{DEACTIVATION}::test_deactivate_chair_nonexistent_responds_404",
            "Reactivar sillón inexistente responde 404": f"{DEACTIVATION}::test_reactivate_chair_nonexistent_responds_404",
            "Desactivar sillón rechazado para rol recepción con 403": f"{DEACTIVATION}::test_deactivate_chair_rejected_for_reception_403",
            "Desactivar sillón rechazado para rol odontólogo con 403": f"{DEACTIVATION}::test_deactivate_chair_rejected_for_doctor_403",
            "Reactivar sillón rechazado para rol recepción con 403": f"{DEACTIVATION}::test_reactivate_chair_rejected_for_reception_403",
            "Reactivar sillón rechazado para rol odontólogo con 403": f"{DEACTIVATION}::test_reactivate_chair_rejected_for_doctor_403",
            "Desactivar prestación activa responde 200": f"{DEACTIVATION}::test_deactivate_service_active_responds_200",
            "Reactivar prestación inactiva responde 200": f"{DEACTIVATION}::test_reactivate_service_inactive_responds_200",
            "Desactivar prestación ya inactiva responde 200 sin cambios": f"{DEACTIVATION}::test_deactivate_service_already_inactive_responds_200_no_changes",
            "Reactivar prestación ya activa responde 200 sin cambios": f"{DEACTIVATION}::test_reactivate_service_already_active_responds_200_no_changes",
            "Desactivar prestación inexistente responde 404": f"{DEACTIVATION}::test_deactivate_service_nonexistent_responds_404",
            "Reactivar prestación inexistente responde 404": f"{DEACTIVATION}::test_reactivate_service_nonexistent_responds_404",
            "Desactivar prestación rechazada para rol recepción con 403": f"{DEACTIVATION}::test_deactivate_service_rejected_for_reception_403",
            "Desactivar prestación rechazada para rol odontólogo con 403": f"{DEACTIVATION}::test_deactivate_service_rejected_for_doctor_403",
            "Reactivar prestación rechazada para rol recepción con 403": f"{DEACTIVATION}::test_reactivate_service_rejected_for_reception_403",
            "Reactivar prestación rechazada para rol odontólogo con 403": f"{DEACTIVATION}::test_reactivate_service_rejected_for_doctor_403",
        },
    }
}


def spec_scenarios(path: Path) -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    requirement = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Requirement: "):
            requirement = line.removeprefix("### Requirement: ").strip()
        elif line.startswith("#### Scenario: "):
            scenarios.append((requirement, line.removeprefix("#### Scenario: ").strip()))
    return scenarios


def collected_nodes() -> set[str]:
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [PYTHON, "-m", "pytest", "--collect-only", "-q", "-m", "integration or not integration"],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {line.strip() for line in result.stdout.splitlines() if "::" in line}


def node_exists(node: str, nodes: set[str]) -> bool:
    return node in nodes or any(item.startswith(f"{node}[") for item in nodes)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    nodes = collected_nodes()
    problems: list[str] = []
    rows: list[str] = []
    number = 0
    for spec_name, path in (("catalog-and-patients", CATALOG_SPEC),):
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
        "Salida generada por docs/evidencias/trazabilidad-C-20.py. No editar a mano.",
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
        print("Faltan los marcadores de trazabilidad en verify-C-20.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
