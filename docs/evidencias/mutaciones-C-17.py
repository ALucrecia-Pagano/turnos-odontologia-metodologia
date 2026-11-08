"""Verificacion por mutacion, reproducible, de los tests de integracion de C-17.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-17.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de
produccion. Por cada una: comprueba que el original aparezca exactamente una
vez, aplica la mutacion, recrea la base de test si toco una migracion, corre
solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-17.txt y regenera la
tabla de verify-C-17.md leyendo ese .txt. Termina con codigo 0 solo si todas las
mutaciones hicieron fallar su test, ninguna es INVALIDA y el SHA-256 de backend/app
y backend/alembic no cambio.

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
OUTPUT = EVIDENCE / "mutaciones-C-17.txt"
VERIFY = EVIDENCE / "verify-C-17.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
PRE_APPOINTMENT_REVISION = "20261104_03_horarios_y_bloqueos"
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

PERSISTENCE = "tests/integration/test_appointment_persistence.py"
CONCURRENCY = "tests/integration/test_appointment_concurrency.py"
INFRASTRUCTURE = "tests/integration/test_database_infrastructure.py"

SERVICES = "backend/app/services/appointments.py"
REPOSITORY = "backend/app/repositories/appointment.py"
MIGRATION_04 = "backend/alembic/versions/20261105_04_turnos_e_historial.py"
MIGRATION_05 = "backend/alembic/versions/20261105_05_historial_sin_truncate.py"

# Corre en un proceso aparte para que Alembic importe la migracion tal como esta
# en disco en ese momento. La URL siempre apunta a la base _test.
DB_HELPER = """
import sys
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.config import load_settings
from tests.integration.conftest import migration_config

settings = load_settings()
url = make_url(settings.database_url).set(database=f"{settings.postgres_db}_test")
if not str(url.database).endswith("_test"):
    raise SystemExit("La base de destino no es de test")
action = sys.argv[1]
if action == "recreate":
    config = migration_config(url.render_as_string(hide_password=False))
    command.downgrade(config, sys.argv[2])
    command.upgrade(config, "head")
elif action == "sql":
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text(sys.argv[2]))
    engine.dispose()
else:
    raise SystemExit(f"Accion desconocida: {action}")
"""


@dataclass(frozen=True)
class Mutation:
    test_file: str
    test_name: str
    file: str
    original: str
    mutated: str
    # Las mutaciones de downgrade dejan restos en la base que el downgrade no
    # puede revertir: este SQL los quita despues de restaurar el archivo. La
    # base se recrea antes de aplicarlas, porque el downgrade mutado no serviria.
    repair_sql: str | None = None

    @property
    def node_id(self) -> str:
        return f"{self.test_file}::{self.test_name}"

    @property
    def function_name(self) -> str:
        return self.test_name.split("[", 1)[0]

    @property
    def is_migration(self) -> bool:
        return self.file.startswith("backend/alembic/")


_ROW_LOCK = """        # D4 & D11: Bloqueo de fila del turno existente con SELECT ... FOR UPDATE
        row = session.scalars(
            select(AppointmentModel)
            .where(AppointmentModel.id == appointment_id)
            .with_for_update()
        ).first()
"""
_CHANGE_STATUS_HEADER = """    target_status: AppointmentStatus,
    actor: Actor,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult | None:
    try:
"""
_RESCHEDULE_HEADER = """    request: RescheduleRequest,
    actor: Actor,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult | None:
    try:
"""
_MISSING_ROW = """        if row is None:
            return None
"""
# Informa el turno inexistente como rechazo de dominio en vez de None.
_MISSING_ROW_AS_REJECTION = """        if row is None:
            from app.domain.violations import Violation, ViolationCode

            return Rejected(
                (Violation(ViolationCode.UNKNOWN_REFERENCE, "Turno inexistente."),)
            )
"""
_SET_STATUS = """        if isinstance(result, Ok):
            row.status = result.appointment.status.value
"""
_KEEP_STATUS = """        if isinstance(result, Ok):
"""
_CHANGE_STATUS_CALL = """            target_status,
            actor,
            now,
            professional_name,
            tz,
        )

"""
_CANCEL_CALL = """        result = domain_cancel_appointment(
            appointment_entity,
            actor,
            now,
            professional_name,
            tz,
        )

"""
_BOOK_REJECTED_BRANCH_TAIL = """    except Exception:
        session.rollback()
        raise


def change_appointment_status(
"""

MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        PERSISTENCE,
        "test_appointment_status_check_rejects_invalid_direct_insert",
        MIGRATION_04,
        """"status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",""",
        """"status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado', 'en_espera')",""",
    ),
    Mutation(
        PERSISTENCE,
        "test_appointment_interval_check_rejects_direct_insert",
        MIGRATION_04,
        '''"start_at < end_at",''',
        '''"start_at <> end_at",''',
    ),
    Mutation(
        PERSISTENCE,
        "test_appointment_status_change_reschedule_all_or_none_check_rejects_partial",
        MIGRATION_04,
        '''"OR "\n''',
        '''"OR reschedule_previous_start_at IS NOT NULL OR "\n''',
    ),
    Mutation(
        PERSISTENCE,
        "test_appointment_status_change_trigger_rejects_direct_update",
        MIGRATION_04,
        "BEFORE UPDATE OR DELETE ON appointment_status_change",
        "BEFORE DELETE ON appointment_status_change",
    ),
    Mutation(
        PERSISTENCE,
        "test_appointment_status_change_trigger_rejects_direct_delete",
        MIGRATION_04,
        "BEFORE UPDATE OR DELETE ON appointment_status_change",
        "BEFORE UPDATE ON appointment_status_change",
    ),
    Mutation(
        PERSISTENCE,
        "test_appointment_status_change_trigger_rejects_truncate",
        MIGRATION_05,
        "BEFORE TRUNCATE ON appointment_status_change",
        "BEFORE UPDATE ON appointment_status_change",
    ),
    Mutation(
        PERSISTENCE,
        "test_sql_appointment_reader_filters_and_orders_in_range",
        REPOSITORY,
        "AppointmentModel.professional_id == professional_id,",
        "AppointmentModel.professional_id.is_not(None),",
    ),
    Mutation(
        PERSISTENCE,
        "test_block_repository_uses_sql_appointment_reader_with_real_rows",
        REPOSITORY,
        """AppointmentModel.professional_id == professional_id,
                AppointmentModel.start_at < end_at,""",
        """AppointmentModel.professional_id == professional_id,
                AppointmentModel.start_at > end_at,""",
    ),
    Mutation(
        PERSISTENCE,
        "test_book_appointment_success_persists_appointment_and_initial_history",
        SERVICES,
        "created_at=status_change.changed_at,",
        "created_at=appointment_entity.start_at,",
    ),
    Mutation(
        PERSISTENCE,
        "test_book_appointment_rejected_overlap_does_not_persist",
        SERVICES,
        """        else:
            session.rollback()
            return result
"""
        + _BOOK_REJECTED_BRANCH_TAIL,
        """        else:
            session.add(AppointmentModel(id=request.id, patient_id=request.patient_id, professional_id=request.professional_id, chair_id=request.chair_id, service_id=request.service_id, start_at=request.start_at, end_at=request.start_at + timedelta(minutes=30), status="reservado", created_at=now, updated_at=now))
            session.commit()
            return result
"""
        + _BOOK_REJECTED_BRANCH_TAIL,
    ),
    Mutation(
        PERSISTENCE,
        "test_book_appointment_atomic_rollback_on_history_failure",
        SERVICES,
        "            session.add(app_model)\n",
        "            session.add(app_model)\n            session.commit()\n",
    ),
    Mutation(
        PERSISTENCE,
        "test_book_appointment_acquires_resource_locks_ordered_by_uuid",
        SERVICES,
        "for prof_id in sorted(set(professional_ids)):",
        "for prof_id in sorted(set(professional_ids), reverse=True):",
    ),
    Mutation(
        PERSISTENCE,
        "test_change_appointment_status_confirmed_updates_status_and_history",
        SERVICES,
        _CHANGE_STATUS_CALL + _SET_STATUS,
        _CHANGE_STATUS_CALL + _KEEP_STATUS,
    ),
    Mutation(
        PERSISTENCE,
        "test_cancel_appointment_updates_status_and_history",
        SERVICES,
        _CANCEL_CALL + _SET_STATUS,
        _CANCEL_CALL + _KEEP_STATUS,
    ),
    Mutation(
        PERSISTENCE,
        "test_status_operations_on_nonexistent_appointment_return_none",
        SERVICES,
        _CHANGE_STATUS_HEADER + _ROW_LOCK + _MISSING_ROW,
        _CHANGE_STATUS_HEADER
        + _ROW_LOCK
        + _MISSING_ROW_AS_REJECTION,
    ),
    Mutation(
        PERSISTENCE,
        "test_reschedule_appointment_success_persists_eight_detail_columns",
        SERVICES,
        "reschedule_new_chair_id=reschedule_detail.new_chair_id,",
        "reschedule_new_chair_id=reschedule_detail.previous_chair_id,",
    ),
    Mutation(
        PERSISTENCE,
        "test_reschedule_nonexistent_appointment_returns_none",
        SERVICES,
        _RESCHEDULE_HEADER + _ROW_LOCK + _MISSING_ROW,
        _RESCHEDULE_HEADER
        + _ROW_LOCK
        + _MISSING_ROW_AS_REJECTION,
    ),
    Mutation(
        CONCURRENCY,
        "test_concurrent_booking_same_professional_serialized",
        SERVICES,
        """            .where(ProfessionalModel.id == prof_id)
            .with_for_update()
""",
        """            .where(ProfessionalModel.id == prof_id)
""",
    ),
    Mutation(
        CONCURRENCY,
        "test_concurrent_booking_same_chair_serialized",
        SERVICES,
        """            .where(ChairModel.id == chair_id)
            .with_for_update()
""",
        """            .where(ChairModel.id == chair_id)
""",
    ),
    Mutation(
        CONCURRENCY,
        "test_concurrent_transition_same_appointment_serialized",
        SERVICES,
        _CHANGE_STATUS_HEADER + _ROW_LOCK,
        _CHANGE_STATUS_HEADER
        + _ROW_LOCK.replace("            .with_for_update()\n", ""),
    ),
    Mutation(
        INFRASTRUCTURE,
        "test_appointment_migration_downgrade_minus_one_cycle",
        MIGRATION_04,
        "        CREATE TRIGGER tr_appointment_status_change_append_only\n"
        "        BEFORE UPDATE OR DELETE ON appointment_status_change\n"
        "        FOR EACH ROW EXECUTE FUNCTION prevent_appointment_status_change_modification();\n",
        "",
    ),
    Mutation(
        INFRASTRUCTURE,
        "test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle",
        MIGRATION_05,
        "DROP TRIGGER IF EXISTS tr_appointment_status_change_no_truncate ON appointment_status_change;",
        "SELECT 1;",
        repair_sql=(
            "DROP TRIGGER IF EXISTS tr_appointment_status_change_no_truncate "
            "ON appointment_status_change"
        ),
    ),
)


class MutationAbort(Exception):
    """El experimento no es valido: no se puede sacar conclusion de esta corrida."""


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
            "integration",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]
    )


def run_db_helper(report: Report, title: str, *arguments: str) -> None:
    result = run_command([PYTHON, "-c", DB_HELPER, *arguments])
    report.write(f"--- {title} (codigo de salida {result.returncode}) ---")
    report.write(result.stdout + result.stderr)
    if result.returncode != 0:
        raise MutationAbort(f"Fallo el paso de base de test: {title}")


def recreate_test_database(report: Report, title: str) -> None:
    run_db_helper(report, title, "recreate", PRE_APPOINTMENT_REVISION)


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
            return redact(line[1:].strip())
    return "(sin linea E)"


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


def classify(result: subprocess.CompletedProcess[str]) -> str:
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if re.search(r"\berrors?\b", summary):
        raise MutationAbort(f"pytest informo un error, no un fallo: {summary}")
    if result.returncode == 1 and re.search(r"\b1 failed\b", summary):
        return "FALLO"
    if result.returncode == 0 and re.search(r"\b1 passed\b", summary):
        return "NO FALLO"
    raise MutationAbort(f"Salida inesperada de pytest: {summary or result.stderr}")


def run_mutation(mutation: Mutation, index: int, report: Report) -> tuple[bool, str | None]:
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
    original_source = original_bytes.decode("utf-8")
    mutated_source = apply_mutation(mutation, original_source)
    if mutated_source == original_source:
        raise MutationAbort(f"{mutation.test_name}: la mutacion no cambia {mutation.file}")

    if mutation.is_migration and mutation.repair_sql is not None:
        recreate_test_database(report, "base de test recreada antes de aplicar la mutacion")

    try:
        path.write_bytes(mutated_source.encode("utf-8"))
        if mutation.is_migration and mutation.repair_sql is None:
            recreate_test_database(report, "base de test recreada con la migracion mutada")
        mutated_run = run_pytest([mutation.node_id])
    finally:
        path.write_bytes(original_bytes)
        os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
        if mutation.is_migration:
            if mutation.repair_sql is not None:
                run_db_helper(
                    report,
                    f"restos del downgrade mutado quitados: {mutation.repair_sql}",
                    "sql",
                    mutation.repair_sql,
                )
            recreate_test_database(report, "base de test recreada con la migracion restaurada")

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
    for root in (BACKEND / "app", BACKEND / "alembic"):
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
    if "--check" in sys.argv[1:]:
        print(f"check_definition: {len(MUTATIONS)} mutaciones correctas")
        return 0

    sha_before = tree_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-17.py. No editar a mano.")
        report.write(f"SHA-256 de backend/app y backend/alembic antes: {sha_before}")
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
            f"SHA-256 de backend/app y backend/alembic despues: {sha_after}",
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
