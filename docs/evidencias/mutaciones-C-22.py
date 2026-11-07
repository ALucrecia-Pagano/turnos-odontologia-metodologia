"""Verificacion por mutacion, reproducible, de los tests de C-22.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-22.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, corre solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-22.txt y regenera la tabla de
verify-C-22.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
hicieron fallar su test, ninguna es INVALIDA y el SHA-256 no cambio.

Una mutacion es INVALIDA si su test no la detecta con una afirmacion propia: la salida
contiene NameError o ImportError, o el primer "E" no tiene su frame en tests/, o no es
assert/AssertionError. Dentro de tests/ tambien valen pytest.raises sin excepcion
("Failed: DID NOT RAISE"), un ValidationError del esquema que el test valida directamente
y un KeyError/IndexError sobre un campo que el propio test lee.
"""

from __future__ import annotations

import difflib
import hashlib
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
OUTPUT = EVIDENCE / "mutaciones-C-22.txt"
VERIFY = EVIDENCE / "verify-C-22.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 180

INVALID_NAME_ERROR = re.compile(r"\b(NameError|ImportError|ModuleNotFoundError)\b")
FRAME_LINE = re.compile(r"^(\S+\.py):\d+: ")
TEST_DETECTION = re.compile(
    r"""^(assert\b|AssertionError\b|Failed: DID NOT RAISE\b"""
    r"""|pydantic_core\._pydantic_core\.ValidationError\b"""
    r"""|KeyError: ['"]|IndexError\b)"""
)

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

TEST_SCHEMAS = "tests/api/test_appointment_schemas.py"
TEST_OPENAPI = "tests/api/test_appointment_openapi.py"
TEST_APPOINTMENTS = "tests/integration/test_api_appointments.py"
TEST_CONCURRENCY = "tests/integration/test_appointments_http_concurrency.py"

API_SCHEMAS = "backend/app/api/schemas.py"
API_APPOINTMENTS = "backend/app/api/appointments.py"
API_ERRORS = "backend/app/api/errors.py"


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

    @property
    def function_name(self) -> str:
        return self.test_name.split("[", 1)[0]


MUTATIONS: tuple[Mutation, ...] = (
    # 1. Esquemas - startAt con zona
    Mutation(
        TEST_SCHEMAS,
        "test_appointment_input_start_at_with_tz_accepted",
        API_SCHEMAS,
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:\n'
        '            raise ValueError("La fecha y hora debe incluir zona horaria.")\n'
        '        return v',
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is not None:\n'
        '            raise ValueError("La fecha y hora debe incluir zona horaria.")\n'
        '        return v',
    ),
    # 2. Esquemas - startAt sin zona
    Mutation(
        TEST_SCHEMAS,
        "test_appointment_input_start_at_without_tz_rejected",
        API_SCHEMAS,
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:',
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if False and v.tzinfo is None:',
    ),
    # 3. Esquemas - extra forbid
    Mutation(
        TEST_SCHEMAS,
        "test_appointment_input_extra_field_forbidden",
        API_SCHEMAS,
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="ignore")',
    ),
    # 4. Esquemas - durationMin opcional
    Mutation(
        TEST_SCHEMAS,
        "test_appointment_input_optional_duration_min",
        API_SCHEMAS,
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")',
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int = Field(alias="durationMin")',
    ),
    # 5. Esquemas - response camelCase y UTC
    Mutation(
        TEST_SCHEMAS,
        "test_appointment_response_camelcase_and_utc",
        API_SCHEMAS,
        'class AppointmentResponse(BaseModel):\n'
        '    id: UUID\n'
        '    patient_id: UUID = Field(serialization_alias="patientId")',
        'class AppointmentResponse(BaseModel):\n'
        '    id: UUID\n'
        '    patient_id: UUID = Field(serialization_alias="patient_id")',
    ),
    # 6. OpenAPI - Swagger documenta status del alta
    Mutation(
        TEST_OPENAPI,
        "test_appointment_create_in_openapi",
        API_APPOINTMENTS,
        '    responses={\n'
        '        **violation_responses(409, 422),\n'
        '        **permission_responses(),\n'
        '    },',
        '    responses={\n'
        '        **violation_responses(409),\n'
        '        **permission_responses(),\n'
        '    },',
    ),
    # 7. 2.1 Recepción da un turno válido
    Mutation(
        TEST_APPOINTMENTS,
        "test_reception_creates_valid_appointment",
        API_APPOINTMENTS,
        '@router.post(\n'
        '    "",\n'
        '    status_code=status.HTTP_201_CREATED,',
        '@router.post(\n'
        '    "",\n'
        '    status_code=status.HTTP_200_OK,',
    ),
    # 8. 2.1 Administrador da un turno válido
    Mutation(
        TEST_APPOINTMENTS,
        "test_admin_creates_valid_appointment",
        API_APPOINTMENTS,
        '        patient_id=body.patient_id,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,',
        '        patient_id=body.patient_id,\n'
        '        professional_id=uuid4(),\n'
        '        chair_id=body.chair_id,',
    ),
    # 9. 2.1 Odontólogo 403
    Mutation(
        TEST_APPOINTMENTS,
        "test_doctor_cannot_create_appointment_forbidden",
        API_APPOINTMENTS,
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CREATE)),\n'
        '    ],',
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.READ_AGENDA)),\n'
        '    ],',
    ),
    # 10. 2.1 Alta sin token 401
    Mutation(
        TEST_APPOINTMENTS,
        "test_create_appointment_without_token_unauthorized",
        API_ERRORS,
        'def authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:\n'
        '    if not isinstance(exc, AuthenticationError):\n'
        '        raise exc\n'
        '    body = AuthErrorResponse(code=exc.code, message=AUTH_ERROR_MESSAGES[exc.code])\n'
        '    return JSONResponse(\n'
        '        status_code=401,',
        'def authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:\n'
        '    if not isinstance(exc, AuthenticationError):\n'
        '        raise exc\n'
        '    body = AuthErrorResponse(code=exc.code, message=AUTH_ERROR_MESSAGES[exc.code])\n'
        '    return JSONResponse(\n'
        '        status_code=403,',
    ),
    # 11. 2.2 durationMin explícito
    Mutation(
        TEST_APPOINTMENTS,
        "test_explicit_duration_min_overrides_service_default",
        API_APPOINTMENTS,
        '        start_at=body.start_at,\n'
        '        duration_min=body.duration_min,\n'
        '        changed_by=permission.actor.user_id,',
        '        start_at=body.start_at,\n'
        '        duration_min=None,\n'
        '        changed_by=permission.actor.user_id,',
    ),
    # 12. 2.2 Sin durationMin usa defecto prestación
    Mutation(
        TEST_APPOINTMENTS,
        "test_default_service_duration_used_when_duration_min_omitted",
        API_APPOINTMENTS,
        '        duration_min=body.duration_min,\n'
        '        changed_by=permission.actor.user_id,',
        '        duration_min=body.duration_min or 15,\n'
        '        changed_by=permission.actor.user_id,',
    ),
    # 13. 2.2 startAt sin zona horaria responde 400
    Mutation(
        TEST_APPOINTMENTS,
        "test_start_at_without_timezone_returns_400",
        API_ERRORS,
        '    return JSONResponse(status_code=400, content={"errors": error_items})',
        '    return JSONResponse(status_code=422, content={"errors": error_items})',
    ),
    # 14. 2.2 Campo extra responde 400
    Mutation(
        TEST_APPOINTMENTS,
        "test_extra_field_in_body_returns_400",
        API_SCHEMAS,
        'class AppointmentInput(BaseModel):\n'
        '    patient_id: UUID = Field(alias="patientId")\n'
        '    professional_id: UUID = Field(alias="professionalId")\n'
        '    chair_id: UUID = Field(alias="chairId")\n'
        '    service_id: UUID = Field(alias="serviceId")\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class AppointmentInput(BaseModel):\n'
        '    patient_id: UUID = Field(alias="patientId")\n'
        '    professional_id: UUID = Field(alias="professionalId")\n'
        '    chair_id: UUID = Field(alias="chairId")\n'
        '    service_id: UUID = Field(alias="serviceId")\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="allow")',
    ),
    # 15. 2.3 Choque de profesional
    Mutation(
        TEST_APPOINTMENTS,
        "test_agenda_conflict_professional_overlap",
        API_ERRORS,
        '    ViolationCode.PROFESSIONAL_OVERLAP: 409,',
        '    ViolationCode.PROFESSIONAL_OVERLAP: 422,',
    ),
    # 16. 2.3 Choque de sillón
    Mutation(
        TEST_APPOINTMENTS,
        "test_agenda_conflict_chair_overlap",
        API_ERRORS,
        '    ViolationCode.CHAIR_OVERLAP: 409,',
        '    ViolationCode.CHAIR_OVERLAP: 422,',
    ),
    # 17. 2.3 Choque de profesional y sillón
    Mutation(
        TEST_APPOINTMENTS,
        "test_agenda_conflict_professional_and_chair_overlap",
        API_ERRORS,
        'def domain_rejected_handler(request: Request, exc: Exception) -> JSONResponse:\n'
        '    if not isinstance(exc, DomainRejectedError):\n'
        '        raise exc\n'
        '    status_code = status_for(exc.rejected.violations)\n'
        '    content = {\n'
        '        "violations": [serialize_violation(v) for v in exc.rejected.violations]\n'
        '    }',
        'def domain_rejected_handler(request: Request, exc: Exception) -> JSONResponse:\n'
        '    if not isinstance(exc, DomainRejectedError):\n'
        '        raise exc\n'
        '    status_code = status_for(exc.rejected.violations)\n'
        '    content = {\n'
        '        "violations": [serialize_violation(exc.rejected.violations[0])] if exc.rejected.violations else []\n'
        '    }',
    ),
    # 18. 2.3 Fuera de horario
    Mutation(
        TEST_APPOINTMENTS,
        "test_agenda_conflict_outside_working_hours",
        API_ERRORS,
        '    ViolationCode.OUTSIDE_WORKING_HOURS: 409,',
        '    ViolationCode.OUTSIDE_WORKING_HOURS: 422,',
    ),
    # 19. 2.3 Bloqueo
    Mutation(
        TEST_APPOINTMENTS,
        "test_agenda_conflict_blocked_time",
        API_ERRORS,
        '    ViolationCode.BLOCKED_TIME: 409,',
        '    ViolationCode.BLOCKED_TIME: 422,',
    ),
    # 20. 2.4 En el pasado
    Mutation(
        TEST_APPOINTMENTS,
        "test_validity_rule_in_the_past",
        API_ERRORS,
        '    ViolationCode.IN_THE_PAST: 422,',
        '    ViolationCode.IN_THE_PAST: 409,',
    ),
    # 21. 2.4 Paciente inexistente
    Mutation(
        TEST_APPOINTMENTS,
        "test_validity_rule_unknown_patient",
        API_ERRORS,
        '    ViolationCode.UNKNOWN_REFERENCE: 422,',
        '    ViolationCode.UNKNOWN_REFERENCE: 404,',
    ),
    # 22. 2.4 Dos referencias inexistentes
    Mutation(
        TEST_APPOINTMENTS,
        "test_validity_rule_two_unknown_references",
        API_SCHEMAS,
        '    item = ViolationItemSchema(\n'
        '        code=v.code,\n'
        '        message=v.message,\n'
        '        conflicting_appointment_id=v.conflicting_appointment_id,\n'
        '        conflicting_block_id=v.conflicting_block_id,\n'
        '        conflicting_interval=interval_schema,\n'
        '        reference_kind=v.reference_kind,\n'
        '    )',
        '    item = ViolationItemSchema(\n'
        '        code=v.code,\n'
        '        message=v.message,\n'
        '        conflicting_appointment_id=v.conflicting_appointment_id,\n'
        '        conflicting_block_id=v.conflicting_block_id,\n'
        '        conflicting_interval=interval_schema,\n'
        '        reference_kind=None,\n'
        '    )',
    ),
    # 23. 2.4 Profesional inactivo
    Mutation(
        TEST_APPOINTMENTS,
        "test_validity_rule_inactive_professional",
        API_ERRORS,
        '    ViolationCode.INACTIVE_REFERENCE: 422,',
        '    ViolationCode.INACTIVE_REFERENCE: 409,',
    ),
    # 24. 2.5 Un rechazo no deja turno ni historial
    Mutation(
        TEST_APPOINTMENTS,
        "test_rejection_leaves_no_appointment_nor_history",
        API_APPOINTMENTS,
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise DomainRejectedError(result)',
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if isinstance(result, Rejected):\n'
        '        return AppointmentResponse(\n'
        '            id=uuid4(),\n'
        '            patient_id=body.patient_id,\n'
        '            professional_id=body.professional_id,\n'
        '            chair_id=body.chair_id,\n'
        '            service_id=body.service_id,\n'
        '            start_at="2026-01-01T00:00:00Z",\n'
        '            end_at="2026-01-01T00:30:00Z",\n'
        '            status="reservado",\n'
        '        )',
    ),
    # 25. 3.1 Concurrencia HTTP
    Mutation(
        TEST_CONCURRENCY,
        "test_two_concurrent_http_appointments_produce_single_slot",
        API_APPOINTMENTS,
        '    result = book_appointment(\n'
        '        session=session,\n'
        '        request=appointment_req,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
        '    result = book_appointment(\n'
        '        session=session,\n'
        '        request=appointment_req,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=False,\n'
        '    )',
    ),
)


class MutationAbort(Exception):
    pass


def redact(text: str) -> str:
    return re.sub(r"(postgresql(?:\+\w+)?://[^:/\s]+:)[^@\s]+@", r"\1***@", text)


class Report:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def write(self, text: str) -> None:
        self._stream.write(redact(text).rstrip("\n") + "\n")
        self._stream.flush()


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
    }
    return subprocess.run(
        arguments,
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def run_pytest(node_ids: list[str]) -> subprocess.CompletedProcess[str]:
    return run_command(
        [
            PYTHON,
            "-m",
            "pytest",
            *node_ids,
            "-m",
            "integration or not integration",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]
    )


def read_source(mutation: Mutation) -> str:
    return (REPO / mutation.file).read_bytes().decode("utf-8")


def apply_mutation(mutation: Mutation, content: str) -> str:
    """Aplica la mutacion respetando el final de linea del archivo (LF o CRLF)."""
    newline = "\r\n" if "\r\n" in content else "\n"
    original = mutation.original.replace("\n", newline)
    mutated = mutation.mutated.replace("\n", newline)
    occurrences = content.count(original)
    if occurrences != 1:
        raise MutationAbort(
            f"{mutation.test_name}: el texto original aparece {occurrences} veces "
            f"en {mutation.file}; debe aparecer exactamente una"
        )
    return content.replace(original, mutated, 1)


def check_definition(mutation: Mutation) -> None:
    source = read_source(mutation)
    if apply_mutation(mutation, source) == source:
        raise MutationAbort(f"{mutation.test_name}: la mutacion no cambia {mutation.file}")
    test_source = (BACKEND / mutation.test_file).read_text(encoding="utf-8")
    if test_source.count(f"def {mutation.function_name}(") != 1:
        raise MutationAbort(f"No existe el test {mutation.node_id}")


def first_failure_line(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("E  "):
            return redact(line[1:].strip())[:200]
    return "(sin linea E)"


def classify(result: subprocess.CompletedProcess[str]) -> str:
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if re.search(r"\berrors?\b", summary):
        raise MutationAbort(f"pytest informo un error, no un fallo: {summary}")
    if result.returncode == 1 and re.search(r"\b1 failed\b", summary):
        return "FALLO"
    if result.returncode == 0 and re.search(r"\b1 passed\b", summary):
        return "NO FALLO"
    raise MutationAbort(f"Salida inesperada de pytest: {summary or result.stderr}")


def invalid_reason(output: str) -> str | None:
    """Devuelve el motivo si el test no detecto la mutacion con una afirmacion propia."""
    name_error = INVALID_NAME_ERROR.search(output)
    if name_error:
        return f"la salida contiene {name_error.group(1)}"

    frame = ""
    for line in output.splitlines():
        frame_match = FRAME_LINE.match(line)
        if frame_match:
            frame = frame_match.group(1).replace("\\", "/")
            continue
        if not line.startswith("E   "):
            continue
        first_error = line.removeprefix("E   ").strip()
        if not frame.startswith("tests/"):
            return f"primer E fuera de tests/ ({frame}): {first_error}"
        if not TEST_DETECTION.match(first_error):
            return f"primer E no es una afirmacion del test: {first_error}"
        return None
    return "la salida no tiene ninguna linea E"


def run_mutation(mutation: Mutation, index: int, report: Report) -> tuple[bool, str | None]:
    check_definition(mutation)
    report.write(SEPARATOR)
    report.write(f"MUTACION {index:02d}/{len(MUTATIONS)}")
    report.write(f"test: {mutation.node_id}")
    report.write(f"archivo: {mutation.file}")
    report.write("--- texto original ---")
    report.write(mutation.original)
    report.write("--- texto mutado ---")
    report.write(mutation.mutated or "(se quita el texto)")
    report.write("--- fin de textos ---")

    path = REPO / mutation.file
    original_bytes = path.read_bytes()
    original_stat = path.stat()
    original_source = original_bytes.decode("utf-8")
    mutated_source = apply_mutation(mutation, original_source)
    if mutated_source == original_source:
        raise MutationAbort(f"{mutation.test_name}: la mutacion no cambia {mutation.file}")

    try:
        path.write_bytes(mutated_source.encode("utf-8"))
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
    killed = outcome == "FALLO"
    reason = invalid_reason(mutated_run.stdout + mutated_run.stderr) if killed else None
    if reason:
        report.write(f"INVALIDA: {reason}")
    return killed, reason


def tree_sha256() -> str:
    digest = hashlib.sha256()
    for root in (BACKEND / "app",):
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(BACKEND).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


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
        "| # | Test | Archivo | Mutación | Primera línea del fallo |",
        "|---|---|---|---|---|",
    ]
    for number, match in enumerate(pattern.finditer(report_text), start=1):
        mutated = "" if match["mutated"] == "(se quita el texto)" else match["mutated"]
        rows.append(
            f"| {number} | {code_span(match['test'])} | {code_span(match['file'])} "
            f"| {diff_cell(match['original'], mutated)} "
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
    if "--check" in sys.argv[1:]:
        print(f"check_definition: {len(MUTATIONS)} mutaciones correctas")
        return 0

    sha_before = tree_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-22.py. No editar a mano.")
        report.write(f"SHA-256 de backend/app antes: {sha_before}")
        baseline = run_pytest([mutation.node_id for mutation in MUTATIONS])
        report.write(f"--- linea de base, sin mutaciones (codigo de salida {baseline.returncode}) ---")
        report.write(baseline.stdout + baseline.stderr)
        if baseline.returncode != 0:
            raise MutationAbort("Los tests no estan en verde antes de mutar")

        for index, mutation in enumerate(MUTATIONS, start=1):
            print(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}", flush=True)
            was_killed, reason = run_mutation(mutation, index, report)
            if reason:
                invalid.append(f"{mutation.test_name}: {reason}")
                print(f"    INVALIDA: {reason}", flush=True)
            elif was_killed:
                killed.append(mutation.test_name)
            else:
                survived.append(mutation.test_name)
                print("    NO hizo fallar su test", flush=True)

        sha_after = tree_sha256()
        same = sha_before == sha_after
        summary = [
            SEPARATOR,
            "RESUMEN",
            f"mutaciones que hicieron fallar su test: {len(killed)}",
            f"mutaciones que NO lo hicieron fallar: {len(survived)}",
            *[f"  - {name}" for name in survived],
            f"mutaciones inválidas: {len(invalid)}",
            *[f"  - {entry}" for entry in invalid],
            f"SHA-256 de backend/app despues: {sha_after}",
            f"SHA-256 sin cambios: {'si' if same else 'NO'}",
        ]
        report.write("\n".join(summary))

    print("\n".join(summary))
    update_verify_table()
    return 0 if same and not survived and not invalid else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationAbort as error:
        print(f"ABORTADO: {error}", file=sys.stderr)
        sys.exit(2)
