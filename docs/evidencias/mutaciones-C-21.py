"""Verificacion por mutacion, reproducible, de los tests de C-21.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-21.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, corre solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-21.txt y regenera la tabla de
verify-C-21.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
hicieron fallar su test y el SHA-256 no cambio.
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
OUTPUT = EVIDENCE / "mutaciones-C-21.txt"
VERIFY = EVIDENCE / "verify-C-21.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 180

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

TEST_DOMAIN_WH = "tests/domain/test_working_hours.py"
TEST_API_WH = "tests/integration/test_api_working_hours.py"
TEST_API_BLOCKS = "tests/integration/test_api_blocks.py"
TEST_CONCURRENCY = "tests/integration/test_availability_concurrency.py"

DOMAIN_WH = "backend/app/domain/rules/working_hours.py"
REPO_BLOCKS = "backend/app/repositories/blocks.py"
API_SCHEMAS = "backend/app/api/schemas.py"
SERVICE_AVAILABILITY = "backend/app/services/availability.py"
API_WH = "backend/app/api/working_hours.py"
API_BLOCKS = "backend/app/api/blocks.py"
API_DEPS = "backend/app/api/deps.py"


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
    # -------------------------------------------------------------------------
    # 1.1 Dominio: turnos fuera de un horario nuevo (6 tests)
    # -------------------------------------------------------------------------
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_lists_future_occupying_appointment_outside_new_hours",
        DOMAIN_WH,
        "            if any(v.code == ViolationCode.OUTSIDE_WORKING_HOURS for v in violations):\n                outside.append(appointment)",
        "            if any(v.code == ViolationCode.OUTSIDE_WORKING_HOURS for v in violations):\n                pass",
    ),
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_ignores_appointment_inside_new_hours",
        DOMAIN_WH,
        "            if any(v.code == ViolationCode.OUTSIDE_WORKING_HOURS for v in violations):",
        "            if True:",
    ),
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_ignores_cancelled_appointment",
        DOMAIN_WH,
        "            and appointment.status in OCCUPYING_STATUSES\n            and appointment.start_at >= now",
        "            and True\n            and appointment.start_at >= now",
    ),
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_ignores_past_appointment",
        DOMAIN_WH,
        "            and appointment.status in OCCUPYING_STATUSES\n            and appointment.start_at >= now",
        "            and appointment.status in OCCUPYING_STATUSES\n            and True",
    ),
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_ignores_other_professional_appointments",
        DOMAIN_WH,
        "        if (\n            appointment.professional_id == professional_id",
        "        if (\n            True",
    ),
    Mutation(
        TEST_DOMAIN_WH,
        "test_appointments_outside_working_hours_returns_appointments_ordered_by_start_and_id",
        DOMAIN_WH,
        "    return sorted(outside, key=lambda a: (a.start_at, str(a.id)))",
        "    return outside",
    ),
    # -------------------------------------------------------------------------
    # 4.1 y 4.2 Router de horarios (19 tests)
    # -------------------------------------------------------------------------
    Mutation(
        TEST_API_WH,
        "test_reception_gets_working_hours_returns_200",
        API_WH,
        '@router.get(\n    "/{id}/working-hours",\n    status_code=status.HTTP_200_OK,',
        '@router.get(\n    "/{id}/working-hours",\n    status_code=status.HTTP_201_CREATED,',
    ),
    Mutation(
        TEST_API_WH,
        "test_odontologist_gets_own_working_hours_returns_200",
        API_WH,
        "    slots = get_working_hours(session, id)\n    ensure_own_professional(permission, id)",
        '    raise NotFoundError("Forzado")\n    slots = get_working_hours(session, id)\n    ensure_own_professional(permission, id)',
    ),
    Mutation(
        TEST_API_WH,
        "test_odontologist_gets_other_professional_working_hours_returns_403",
        API_WH,
        "    slots = get_working_hours(session, id)\n    ensure_own_professional(permission, id)",
        "    slots = get_working_hours(session, id)\n    pass",
    ),
    Mutation(
        TEST_API_WH,
        "test_get_working_hours_without_token_returns_401",
        API_DEPS,
        "    if credentials is None:\n        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)",
        "    if False:\n        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)",
    ),
    Mutation(
        TEST_API_WH,
        "test_get_working_hours_unknown_professional_returns_404",
        SERVICE_AVAILABILITY,
        '    if prof is None:\n        raise NotFoundError("Profesional no encontrado.")\n    return WorkingHoursRepository(session).list_by_professional(professional_id)',
        '    if False:\n        raise NotFoundError("Profesional no encontrado.")\n    return WorkingHoursRepository(session).list_by_professional(professional_id)',
    ),
    Mutation(
        TEST_API_WH,
        "test_admin_replaces_working_hours_returns_200",
        API_WH,
        '@router.put(\n    "/{id}/working-hours",\n    status_code=status.HTTP_200_OK,',
        '@router.put(\n    "/{id}/working-hours",\n    status_code=status.HTTP_202_ACCEPTED,',
    ),
    Mutation(
        TEST_API_WH,
        "test_odontologist_replaces_own_working_hours_returns_200",
        API_WH,
        "    ensure_own_professional(permission, id)\n\n    domain_slots: list[WorkingHours] = []",
        '    raise NotFoundError("Forzado")\n\n    domain_slots: list[WorkingHours] = []',
    ),
    Mutation(
        TEST_API_WH,
        "test_odontologist_replaces_other_professional_working_hours_returns_403",
        API_WH,
        "    ensure_own_professional(permission, id)\n\n    domain_slots: list[WorkingHours] = []",
        "    pass\n\n    domain_slots: list[WorkingHours] = []",
    ),
    Mutation(
        TEST_API_WH,
        "test_reception_replaces_working_hours_returns_403",
        API_WH,
        "        Depends(require_permission(Resource.WORKING_HOURS, Action.UPDATE)),",
        "        Depends(require_permission(Resource.WORKING_HOURS, Action.READ)),",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_with_empty_list_returns_empty",
        SERVICE_AVAILABILITY,
        "    res = repo.replace_for_professional(professional_id, slots)\n    if isinstance(res, Rejected):",
        "    res = repo.replace_for_professional(professional_id, slots or [WorkingHours(professional_id, 1, 540, 780)])\n    if isinstance(res, Rejected):",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_overlapping_returns_422",
        DOMAIN_WH,
        "                        code=ViolationCode.OVERLAPPING_WORKING_HOURS,",
        "                        code=ViolationCode.INVALID_WORKING_HOURS,",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_start_after_end_returns_422",
        DOMAIN_WH,
        "                    code=ViolationCode.INVALID_WORKING_HOURS,",
        "                    code=ViolationCode.OVERLAPPING_WORKING_HOURS,",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_malformed_time_returns_400",
        API_SCHEMAS,
        '    @field_validator("start")\n    @classmethod\n    def validate_start(cls, v: str) -> str:\n        if not _START_TIME_REGEX.match(v):\n            raise ValueError("start debe tener formato HH:MM válido (00:00 a 23:59).")\n        return v\n\n    @field_validator("end")\n    @classmethod\n    def validate_end(cls, v: str) -> str:\n        if not _END_TIME_REGEX.match(v):\n            raise ValueError("end debe tener formato HH:MM válido (00:00 a 24:00).")\n        return v',
        '    @field_validator("start")\n    @classmethod\n    def validate_start(cls, v: str) -> str:\n        return v\n\n    @field_validator("end")\n    @classmethod\n    def validate_end(cls, v: str) -> str:\n        return v',
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_end_at_24_accepted_returns_200",
        API_SCHEMAS,
        '_END_TIME_REGEX: Final = re.compile(r"^(?:(?:[01]\\d|2[0-3]):[0-5]\\d|24:00)$")',
        '_END_TIME_REGEX: Final = re.compile(r"^(?:[01]\\d|2[0-3]):[0-5]\\d$")',
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_unknown_professional_returns_404",
        API_WH,
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None:\n        raise NotFoundError("Profesional no encontrado.")',
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None:\n        raise ValueError("Error forzado")',
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_inactive_professional_accepted",
        API_WH,
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None:\n        raise NotFoundError("Profesional no encontrado.")',
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None or not prof.active:\n        raise NotFoundError("Profesional no encontrado.")',
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_reports_outside_appointment_without_cancelling",
        SERVICE_AVAILABILITY,
        "    outside = appointments_outside_working_hours(professional_id, candidates, slots, tz, now)\n    affected = _affected_summary(session, outside)",
        "    outside: list[Appointment] = []\n    affected = _affected_summary(session, outside)",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_does_not_report_appointment_inside_new_hours",
        SERVICE_AVAILABILITY,
        "    outside = appointments_outside_working_hours(professional_id, candidates, slots, tz, now)\n    affected = _affected_summary(session, outside)",
        "    outside = list(candidates)\n    affected = _affected_summary(session, outside)",
    ),
    Mutation(
        TEST_API_WH,
        "test_replace_working_hours_does_not_report_cancelled_appointment",
        DOMAIN_WH,
        "            and appointment.status in OCCUPYING_STATUSES\n            and appointment.start_at >= now",
        "            and True\n            and appointment.start_at >= now",
    ),
    # -------------------------------------------------------------------------
    # 5.1, 5.2 y 5.3 Routers de bloqueos (21 tests)
    # -------------------------------------------------------------------------
    Mutation(
        TEST_API_BLOCKS,
        "test_reception_lists_blocks_of_professional",
        API_BLOCKS,
        '@router.get(\n    "/professionals/{id}/blocks",\n    status_code=status.HTTP_200_OK,',
        '@router.get(\n    "/professionals/{id}/blocks",\n    status_code=status.HTTP_201_CREATED,',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_lists_own_blocks",
        API_BLOCKS,
        "    blocks = list_blocks(session, id, params.from_time, params.to_time)",
        "    blocks: tuple[Block, ...] = ()",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_lists_other_professional_blocks_forbidden",
        API_BLOCKS,
        "    blocks = list_blocks(session, id, params.from_time, params.to_time)\n    ensure_own_professional(permission, id)",
        "    blocks = list_blocks(session, id, params.from_time, params.to_time)\n    pass",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_list_blocks_with_from_and_to_filters_overlapping",
        REPO_BLOCKS,
        "        if end_at is not None:\n            stmt = stmt.where(BlockModel.start_at < end_at)",
        "        if False:\n            stmt = stmt.where(BlockModel.start_at < end_at)",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_list_blocks_from_without_timezone_returns_400",
        API_SCHEMAS,
        '        if v is not None and v.tzinfo is None:\n            raise ValueError("La fecha y hora debe incluir zona horaria.")',
        "        if False:\n            pass",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_list_blocks_unknown_professional_returns_404",
        SERVICE_AVAILABILITY,
        'def list_blocks(\n    session: Session,\n    professional_id: UUID,\n    start_at: datetime | None = None,\n    end_at: datetime | None = None,\n) -> tuple[Block, ...]:\n    prof = ProfessionalRepository(session).get_by_id(professional_id)\n    if prof is None:\n        raise NotFoundError("Profesional no encontrado.")',
        'def list_blocks(\n    session: Session,\n    professional_id: UUID,\n    start_at: datetime | None = None,\n    end_at: datetime | None = None,\n) -> tuple[Block, ...]:\n    prof = ProfessionalRepository(session).get_by_id(professional_id)\n    if False:\n        raise NotFoundError("Profesional no encontrado.")',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_creates_own_block_without_affected_appointments",
        API_BLOCKS,
        '@router.post(\n    "/professionals/{id}/blocks",\n    status_code=status.HTTP_201_CREATED,',
        '@router.post(\n    "/professionals/{id}/blocks",\n    status_code=status.HTTP_200_OK,',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_admin_creates_block_for_any_professional",
        API_BLOCKS,
        "    ensure_own_professional(permission, id)\n\n    block, affected = create_block(",
        '    raise NotFoundError("Forzado")\n\n    block, affected = create_block(',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_creates_block_for_other_professional_forbidden",
        API_BLOCKS,
        "    ensure_own_professional(permission, id)\n\n    block, affected = create_block(",
        "    pass\n\n    block, affected = create_block(",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_reception_creates_block_forbidden",
        API_BLOCKS,
        "        Depends(require_permission(Resource.BLOCK, Action.CREATE)),",
        "        Depends(require_permission(Resource.BLOCK, Action.READ)),",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_block_start_equal_to_end_returns_422",
        SERVICE_AVAILABILITY,
        "    res = repo.create(candidate)\n    if isinstance(res, Rejected):\n        raise DomainRejectedError(res)",
        "    res = repo.create(candidate)\n    if False:\n        raise DomainRejectedError(res)",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_block_without_timezone_returns_400",
        API_SCHEMAS,
        '        if v.tzinfo is None:\n            raise ValueError("La fecha y hora debe incluir zona horaria.")',
        "        if False:\n            pass",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_block_unknown_professional_returns_404",
        API_BLOCKS,
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None:\n        raise NotFoundError("Profesional no encontrado.")',
        '    prof = ProfessionalRepository(session).get_by_id(id)\n    if prof is None:\n        raise ValueError("Error forzado")',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_block_overlapping_reserved_appointment_reports_it_without_canceling",
        SERVICE_AVAILABILITY,
        "    affected_apts = repo.list_affected_appointments(res.entity)\n    affected = _affected_summary(session, affected_apts)",
        "    affected_apts: list[Appointment] = []\n    affected = _affected_summary(session, affected_apts)",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_block_overlapping_canceled_appointment_not_reported",
        "backend/app/domain/rules/blocks.py",
        "            and appointment.status in OCCUPYING_STATUSES\n            and _overlaps(appointment.start_at, appointment.end_at, block.start_at, block.end_at)",
        "            and True\n            and _overlaps(appointment.start_at, appointment.end_at, block.start_at, block.end_at)",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_deletes_own_block",
        API_BLOCKS,
        '@router.delete(\n    "/blocks/{block_id}",\n    status_code=status.HTTP_200_OK,',
        '@router.delete(\n    "/blocks/{block_id}",\n    status_code=status.HTTP_201_CREATED,',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_admin_deletes_block_of_any_professional",
        API_BLOCKS,
        "    ensure_own_professional(permission, block.professional_id, Resource.BLOCK, Action.DELETE)\n    deleted = delete_block(session, block_id)",
        '    raise NotFoundError("Forzado")\n    deleted = delete_block(session, block_id)',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_odontologist_deletes_other_professional_block_forbidden",
        API_BLOCKS,
        "    ensure_own_professional(permission, block.professional_id, Resource.BLOCK, Action.DELETE)\n    deleted = delete_block(session, block_id)",
        "    pass\n    deleted = delete_block(session, block_id)",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_reception_deletes_block_forbidden",
        API_BLOCKS,
        "        Depends(require_permission(Resource.BLOCK, Action.DELETE)),",
        "        Depends(require_permission(Resource.BLOCK, Action.READ)),",
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_delete_unknown_block_returns_404",
        SERVICE_AVAILABILITY,
        'def get_block(session: Session, block_id: UUID) -> Block:\n    repo = BlockRepository(session, SqlAppointmentReader(session))\n    block = repo.get_by_id(block_id)\n    if block is None:\n        raise NotFoundError("Bloqueo no encontrado.")\n    return block',
        'def get_block(session: Session, block_id: UUID) -> Block:\n    repo = BlockRepository(session, SqlAppointmentReader(session))\n    block = repo.get_by_id(block_id)\n    if False:\n        raise NotFoundError("Bloqueo no encontrado.")\n    return block',
    ),
    Mutation(
        TEST_API_BLOCKS,
        "test_delete_block_frees_schedule",
        SERVICE_AVAILABILITY,
        "def delete_block(session: Session, block_id: UUID, auto_commit: bool = True) -> Block:\n    repo = BlockRepository(session, SqlAppointmentReader(session))\n    deleted = repo.delete(block_id)\n    if deleted is None:\n        raise NotFoundError(\"Bloqueo no encontrado.\")\n    if auto_commit:\n        session.commit()\n    return deleted",
        "def delete_block(session: Session, block_id: UUID, auto_commit: bool = True) -> Block:\n    repo = BlockRepository(session, SqlAppointmentReader(session))\n    deleted = repo.get_by_id(block_id)\n    if deleted is None:\n        raise NotFoundError(\"Bloqueo no encontrado.\")\n    return deleted",
    ),
    # -------------------------------------------------------------------------
    # 6.1 Concurrencia (2 tests)
    # -------------------------------------------------------------------------
    Mutation(
        TEST_CONCURRENCY,
        "test_concurrent_block_waiting_for_booking_reports_new_appointment",
        SERVICE_AVAILABILITY,
        "    affected_apts = repo.list_affected_appointments(res.entity)\n    affected = _affected_summary(session, affected_apts)",
        "    affected_apts: list[Appointment] = []\n    affected = _affected_summary(session, affected_apts)",
    ),
    Mutation(
        TEST_CONCURRENCY,
        "test_concurrent_booking_waiting_for_block_receives_blocked_time",
        SERVICE_AVAILABILITY,
        "    res = repo.create(candidate)\n    if isinstance(res, Rejected):\n        raise DomainRejectedError(res)",
        "    res = Ok(candidate)\n    if isinstance(res, Rejected):\n        raise DomainRejectedError(res)",
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text_to_write: str) -> None:
        self.stream.write(f"{text_to_write}\n")
        self.stream.flush()


def redact(text_to_redact: str) -> str:
    cleaned = text_to_redact
    cleaned = re.sub(r":\d+", ":<linea>", cleaned)
    return cleaned


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(BACKEND)
    return subprocess.run(
        command,
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
    return (REPO / mutation.file).read_text(encoding="utf-8")


def check_definition(mutation: Mutation) -> None:
    occurrences = read_source(mutation).count(mutation.original)
    if occurrences != 1:
        raise MutationAbort(
            f"{mutation.test_name}: el texto original aparece {occurrences} veces "
            f"en {mutation.file}; debe aparecer exactamente una"
        )
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


def run_mutation(mutation: Mutation, index: int, report: Report) -> bool:
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
    crlf = b"\r\n" in original_bytes

    try:
        source = path.read_text(encoding="utf-8")
        mutated_source = source.replace(mutation.original, mutation.mutated)
        if crlf:
            mutated_source = mutated_source.replace("\r\n", "\n").replace("\n", "\r\n")
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
    return outcome == "FALLO"


def tree_sha256() -> str:
    digest = hashlib.sha256()
    for root in (BACKEND / "app",):
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(BACKEND).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


def code_span(text_to_span: str) -> str:
    escaped = text_to_span.replace("|", "\\|")
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
    for index, match in enumerate(pattern.finditer(report_text), start=1):
        mutated = match["mutated"]
        if mutated == "(se quita el texto)":
            mutated = ""
        rows.append(
            f"| {index} | {code_span(match['test'])} | {code_span(match['file'])} "
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
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-21.py. No editar a mano.")
        report.write(f"SHA-256 de backend/app antes: {sha_before}")
        baseline = run_pytest([mutation.node_id for mutation in MUTATIONS])
        report.write(f"--- linea de base, sin mutaciones (codigo de salida {baseline.returncode}) ---")
        report.write(baseline.stdout + baseline.stderr)
        if baseline.returncode != 0:
            raise MutationAbort("Los tests no estan en verde antes de mutar")

        for index, mutation in enumerate(MUTATIONS, start=1):
            print(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}", flush=True)
            if run_mutation(mutation, index, report):
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
            f"SHA-256 de backend/app despues: {sha_after}",
            f"SHA-256 sin cambios: {'si' if same else 'NO'}",
        ]
        report.write("\n".join(summary))

    print("\n".join(summary))
    update_verify_table()
    return 0 if same and not survived else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationAbort as error:
        print(f"ABORTADO: {error}", file=sys.stderr)
        sys.exit(2)
