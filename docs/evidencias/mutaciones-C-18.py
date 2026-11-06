"""Verificacion por mutacion, reproducible, de los tests nuevos de C-18.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-18.py
"""

from __future__ import annotations

import difflib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "mutaciones-C-18.txt"
VERIFY = EVIDENCE / "verify-C-18.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 60

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

TEST_DEPS = "tests/test_api_dependencies.py"
TEST_APP = "tests/api/test_app.py"
TEST_ERRORS = "tests/api/test_error_mapping.py"
TEST_REJECTION = "tests/api/test_domain_rejection.py"
TEST_BODY = "tests/api/test_violation_body.py"
TEST_MALFORMED = "tests/api/test_malformed_request.py"
TEST_SESSION = "tests/integration/test_api_session.py"
TEST_HEALTH = "tests/api/test_health.py"
TEST_INTEG_HEALTH = "tests/integration/test_api_health.py"
TEST_CORS = "tests/api/test_cors.py"
TEST_OPENAPI = "tests/api/test_openapi.py"
TEST_COMPOSE = "tests/test_compose.py"

PYPROJECT = "backend/pyproject.toml"
MAIN = "backend/app/main.py"
SESSION = "backend/app/db/session.py"
ERRORS = "backend/app/api/errors.py"
SCHEMAS = "backend/app/api/schemas.py"
DEPS = "backend/app/api/deps.py"
HEALTH = "backend/app/api/health.py"
OPENAPI = "backend/app/api/openapi.py"
COMPOSE = "docker-compose.yml"
DOCKERFILE = "backend/Dockerfile"
DOCKERIGNORE = "backend/.dockerignore"
README = "backend/README.md"
KB_07 = "knowledge-base/07_flujos_principales.md"


@dataclass(frozen=True)
class Mutation:
    test_file: str
    test_name: str
    file: str
    original: str
    mutated: str

    @property
    def node_id(self) -> str:
        return f"{self.test_file}::{self.test_name}"


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        TEST_DEPS,
        "test_api_dependencies_are_declared",
        PYPROJECT,
        '    "fastapi>=0.118,<1",\n',
        '    #"fastapi>=0.118,<1",\n',
    ),
    Mutation(
        TEST_APP,
        "test_create_app_accepts_literal_settings",
        MAIN,
        "app.state.settings = resolved_settings",
        "app.state.settings = None",
    ),
    Mutation(
        TEST_APP,
        "test_create_app_keeps_one_session_factory",
        MAIN,
        "app.state.session_factory = session_factory",
        "app.state.session_factory = None",
    ),
    Mutation(
        TEST_APP,
        "test_get_session_helper_is_removed",
        SESSION,
        "def database_url_for_test(settings: Settings) -> URL:",
        "def get_session(): pass\n\ndef database_url_for_test(settings: Settings) -> URL:",
    ),
    Mutation(
        TEST_ERRORS,
        "test_all_violation_codes_are_classified",
        ERRORS,
        "    ViolationCode.PROFESSIONAL_OVERLAP: 409,\n",
        "    # ViolationCode.PROFESSIONAL_OVERLAP: 409,\n",
    ),
    Mutation(
        TEST_ERRORS,
        "test_unclassified_code_is_detected",
        ERRORS,
        "return set(ViolationCode) - set(mapping.keys())",
        "return set()",
    ),
    Mutation(
        TEST_ERRORS,
        "test_mixed_codes_use_precedence",
        ERRORS,
        "    if 403 in statuses:\n        return 403\n    if 422 in statuses:\n        return 422\n    return 409",
        "    if 409 in statuses:\n        return 409\n    if 422 in statuses:\n        return 422\n    return 403",
    ),
    Mutation(
        TEST_ERRORS,
        "test_kb_07_lists_all_violation_codes",
        KB_07,
        "DUPLICATE_DNI",
        "DNI_CLONADO",
    ),
    Mutation(
        TEST_REJECTION,
        "test_violation_code_maps_to_status",
        ERRORS,
        "    ViolationCode.PROFESSIONAL_OVERLAP: 409,\n",
        "    ViolationCode.PROFESSIONAL_OVERLAP: 422,\n",
    ),
    Mutation(
        TEST_REJECTION,
        "test_mixed_rejection_keeps_all_violations_in_order",
        ERRORS,
        '"violations": [serialize_violation(v) for v in exc.rejected.violations]',
        '"violations": [serialize_violation(v) for v in reversed(exc.rejected.violations)]',
    ),
    Mutation(
        TEST_BODY,
        "test_overlap_body",
        SCHEMAS,
        'serialization_alias="conflictingAppointmentId"',
        'serialization_alias="conflictingAppId"',
    ),
    Mutation(
        TEST_BODY,
        "test_blocked_time_body",
        SCHEMAS,
        'serialization_alias="conflictingBlockId"',
        'serialization_alias="conflictingBlkId"',
    ),
    Mutation(
        TEST_BODY,
        "test_reference_body",
        SCHEMAS,
        'serialization_alias="referenceKind"',
        'serialization_alias="refKind"',
    ),
    Mutation(
        TEST_BODY,
        "test_violation_without_extras_body",
        SCHEMAS,
        "exclude_none=True",
        "exclude_none=False",
    ),
    Mutation(
        TEST_MALFORMED,
        "test_invalid_json_returns_400",
        ERRORS,
        '"json_invalid": "El cuerpo no es JSON válido.",',
        '"json_invalid": "JSON inválido.",',
    ),
    Mutation(
        TEST_MALFORMED,
        "test_missing_field_returns_400",
        ERRORS,
        '"missing": "Falta este dato.",',
        '"missing": "Falta dato.",',
    ),
    Mutation(
        TEST_MALFORMED,
        "test_sent_value_is_not_returned",
        ERRORS,
        "error_items.append(",
        'error_items.append({"leaked": str(err.get("input"))}); error_items.append(',
    ),
    Mutation(
        TEST_MALFORMED,
        "test_invalid_query_param_returns_400",
        ERRORS,
        'return JSONResponse(status_code=400, content={"errors": error_items})',
        'return JSONResponse(status_code=422, content={"errors": error_items})',
    ),
    Mutation(
        TEST_SESSION,
        "test_committed_write_persists",
        DEPS,
        "        try:\n            yield session",
        "        try:\n            yield None",
    ),
    Mutation(
        TEST_SESSION,
        "test_uncommitted_write_does_not_persist",
        DEPS,
        "        try:\n            yield session",
        "        try:\n            yield session\n            session.commit()",
    ),
    Mutation(
        TEST_SESSION,
        "test_exception_rolls_back_write",
        DEPS,
        "session.rollback()",
        "session.commit()",
    ),
    Mutation(
        TEST_HEALTH,
        "test_health_returns_503_with_closed_port",
        HEALTH,
        "status_code=status.HTTP_503_SERVICE_UNAVAILABLE,",
        "status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,",
    ),
    Mutation(
        TEST_INTEG_HEALTH,
        "test_health_returns_200_with_database",
        HEALTH,
        'content={"status": "ok", "database": "ok"},',
        'content={"status": "ok", "database": "down"},',
    ),
    Mutation(
        TEST_CORS,
        "test_preflight_allowed_from_cors_origin",
        MAIN,
        "allow_credentials=False,",
        "allow_credentials=True,",
    ),
    Mutation(
        TEST_CORS,
        "test_simple_response_allowed_from_cors_origin",
        MAIN,
        "allow_origins=[resolved_settings.cors_origin],",
        'allow_origins=["http://localhost:9999"],',
    ),
    Mutation(
        TEST_CORS,
        "test_preflight_rejected_from_other_origin",
        MAIN,
        "allow_origins=[resolved_settings.cors_origin],",
        'allow_origins=["*"],',
    ),
    Mutation(
        TEST_OPENAPI,
        "test_swagger_served_at_api_docs",
        MAIN,
        'docs_url="/api/docs",',
        'docs_url="/docs",',
    ),
    Mutation(
        TEST_OPENAPI,
        "test_automatic_422_is_removed",
        OPENAPI,
        'if "HTTPValidationError" in schema_ref:',
        'if False and "HTTPValidationError" in schema_ref:',
    ),
    Mutation(
        TEST_OPENAPI,
        "test_400_documented_on_route_with_input",
        OPENAPI,
        'if has_input and "400" not in responses:',
        'if False and "400" not in responses:',
    ),
    Mutation(
        TEST_OPENAPI,
        "test_409_documented_on_rejecting_route",
        OPENAPI,
        "responses: dict[int | str, dict[str, Any]] = {}",
        "if 409 in status_codes: return {}\n    responses: dict[int | str, dict[str, Any]] = {}",
    ),
    Mutation(
        TEST_OPENAPI,
        "test_422_documented_on_rejecting_route",
        OPENAPI,
        "responses: dict[int | str, dict[str, Any]] = {}",
        "if 422 in status_codes: return {}\n    responses: dict[int | str, dict[str, Any]] = {}",
    ),
    Mutation(
        TEST_OPENAPI,
        "test_schema_lists_all_violation_codes",
        SCHEMAS,
        "    code: ViolationCode\n",
        "    code: str\n",
    ),
    Mutation(
        TEST_OPENAPI,
        "test_health_documents_200_and_503",
        HEALTH,
        "503: {",
        "500: {",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_compose_defines_services_without_literal_secrets",
        COMPOSE,
        "  backend:\n",
        "  api_svc:\n",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_backend_database_url_uses_postgres_service",
        COMPOSE,
        "@postgres:5432",
        "@localhost:5432",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_backend_waits_for_healthy_postgres",
        COMPOSE,
        "      postgres:\n        condition: service_healthy",
        "      postgres:\n        condition: service_started",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_backend_waits_for_healthy_redis",
        COMPOSE,
        "      redis:\n        condition: service_healthy",
        "      redis:\n        condition: service_started",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_backend_healthcheck_uses_api_health",
        COMPOSE,
        "'/api/health'",
        "'/health'",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_dockerfile_runs_as_non_root",
        DOCKERFILE,
        "USER appuser",
        "USER root",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_dockerfile_migrates_before_uvicorn",
        DOCKERFILE,
        "alembic upgrade head && ",
        "",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_dockerignore_excludes_local_artifacts",
        DOCKERIGNORE,
        ".venv\n",
        ".local_venv\n",
    ),
    Mutation(
        TEST_COMPOSE,
        "test_readme_warns_about_reserved_password_characters",
        README,
        "caracteres reservados",
        "caracteres permitidos",
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text: str) -> None:
        self.stream.write(f"{text}\n")
        self.stream.flush()


def run_pytest(node_ids: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [PYTHON, "-m", "pytest", *node_ids, "-o", "addopts="]
    return subprocess.run(
        cmd,
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def read_source(mutation: Mutation) -> str:
    return (REPO / mutation.file).read_bytes().decode("utf-8")


def check_definition(mutation: Mutation) -> None:
    occurrences = read_source(mutation).count(mutation.original)
    if occurrences != 1:
        raise MutationAbort(
            f"{mutation.test_name}: el texto original aparece {occurrences} veces "
            f"en {mutation.file}; debe aparecer exactamente una"
        )
    test_source = (BACKEND / mutation.test_file).read_text(encoding="utf-8")
    if test_source.count(f"def {mutation.test_name}(") != 1:
        raise MutationAbort(f"No existe el test {mutation.node_id}")


def first_failure_line(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("E  "):
            return line[1:].strip()
    return "(sin linea E)"


def classify(result: subprocess.CompletedProcess[str]) -> str:
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if re.search(r"\berrors?\b", summary):
        raise MutationAbort(f"pytest informo un error, no un fallo: {summary}")
    if result.returncode == 1 and re.search(r"\b1 failed\b", summary):
        return "FALLO"
    if result.returncode == 0 and re.search(r"\b1 passed\b", summary):
        return "NO FALLO"
    # In case of parametrized tests or other summaries
    if result.returncode == 1 and "failed" in summary:
        return "FALLO"
    raise MutationAbort(f"Salida inesperada de pytest: {summary or result.stderr}")


def run_mutation(mutation: Mutation, index: int, report: Report) -> bool:
    check_definition(mutation)
    report.write(SEPARATOR)
    report.write(f"MUTACION {index:02d}/{len(MUTATIONS)}")
    report.write(f"test: {mutation.node_id}")
    report.write(f"archivo: {mutation.file}")
    report.write("--- texto original ---")
    report.write(mutation.original)
    report.write("--- texto mutado ---")
    report.write(mutation.mutated)
    report.write("--- fin de textos ---")

    path = REPO / mutation.file
    original_bytes = path.read_bytes()
    original_stat = path.stat()

    try:
        path.write_bytes(
            read_source(mutation)
            .replace(mutation.original, mutation.mutated, 1)
            .encode("utf-8")
        )
        mutated_run = run_pytest([mutation.node_id])
    finally:
        path.write_bytes(original_bytes)
        os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    report.write(f"--- pytest con la mutacion (codigo de salida {mutated_run.returncode}) ---")
    report.write(mutated_run.stdout + mutated_run.stderr)
    outcome = classify(mutated_run)
    report.write(f"resultado: {outcome}")
    if outcome == "FALLO":
        report.write(f"primera linea del fallo: {first_failure_line(mutated_run.stdout)}")
    else:
        report.write("primera linea del fallo: (el test no fallo)")

    restored_run = run_pytest([mutation.node_id])
    report.write(f"--- pytest tras restaurar (codigo de salida {restored_run.returncode}) ---")
    report.write(restored_run.stdout + restored_run.stderr)
    if restored_run.returncode != 0:
        raise MutationAbort(f"{mutation.test_name} no pasa con el codigo restaurado")
    report.write("restaurado: test en verde")
    return outcome == "FALLO"


def code_span(text: str) -> str:
    escaped = text.replace("|", "\\|")
    return f"`` {escaped} ``" if "`" in escaped else f"`{escaped}`"


def diff_cell(original: str, mutated: str) -> str:
    lines = difflib.unified_diff(
        original.splitlines(), mutated.splitlines(), lineterm="", n=0
    )
    changed = [
        code_span(f"{line[0]} {line[1:].strip()}")
        for line in lines
        if line[:1] in {"-", "+"} and line[:3] not in {"---", "+++"}
    ]
    return "<br>".join(changed)


def build_table(report_text: str) -> str:
    pattern = re.compile(
        r"^test: \S+::(?P<test>\S+)\n"
        r"archivo: (?P<file>\S+)\n"
        r"--- texto original ---\n(?P<original>.*?)\n"
        r"--- texto mutado ---\n(?P<mutated>.*?)\n"
        r"--- fin de textos ---\n"
        r".*?^primera linea del fallo: (?P<failure>[^\n]*)$",
        re.MULTILINE | re.DOTALL,
    )
    rows = [
        "| Test | Archivo | Mutación | Primera línea del fallo |",
        "|---|---|---|---|",
    ]
    for match in pattern.finditer(report_text):
        rows.append(
            f"| {code_span(match['test'])} | {code_span(match['file'])} "
            f"| {diff_cell(match['original'], match['mutated'])} "
            f"| {code_span(match['failure'])} |"
        )
    return "\n".join(rows)


def update_verify_table() -> None:
    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start == -1 or end == -1:
        raise MutationAbort(f"Faltan los marcadores de la tabla en {VERIFY.name}")
    table = build_table(OUTPUT.read_text(encoding="utf-8"))
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    for mutation in MUTATIONS:
        check_definition(mutation)

    killed: list[str] = []
    survived: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-18.py. No editar a mano.")
        baseline = run_pytest([mutation.node_id for mutation in MUTATIONS])
        report.write(f"--- linea de base, sin mutaciones (codigo de salida {baseline.returncode}) ---")
        report.write(baseline.stdout + baseline.stderr)
        if baseline.returncode != 0:
            raise MutationAbort(f"Los tests no estan en verde antes de mutar:\n{baseline.stdout}\n{baseline.stderr}")

        for index, mutation in enumerate(MUTATIONS, start=1):
            print(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}", flush=True)
            if run_mutation(mutation, index, report):
                killed.append(mutation.test_name)
            else:
                survived.append(mutation.test_name)
                print("    NO hizo fallar su test", flush=True)

        summary = [
            SEPARATOR,
            "RESUMEN",
            f"mutaciones que hicieron fallar su test: {len(killed)}",
            f"mutaciones que NO lo hicieron fallar: {len(survived)}",
            *[f"  - {name}" for name in survived],
        ]
        report.write("\n".join(summary))

    print("\n".join(summary))
    update_verify_table()
    return 0 if not survived else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationAbort as error:
        print(f"ABORTADO: {error}", file=sys.stderr)
        sys.exit(2)
