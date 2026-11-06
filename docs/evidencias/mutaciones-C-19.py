"""Verificacion por mutacion, reproducible, de los tests de C-19.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-19.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, recrea la base de test si toco una migracion, corre solo su test, restaura
el archivo en un finally y vuelve a correr el test.

Mismo formato que mutaciones-C-17.py, con tres diferencias (D20 de C-19):
1. Corre con -m "integration or not integration": C-19 tiene tests sin base.
2. No usa git diff: compara un SHA-256 de backend/app y backend/alembic antes y
   despues, porque el codigo de C-19 todavia no esta commiteado.
3. Revision de recreacion: 20261105_05_historial_sin_truncate.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-19.txt y regenera la tabla de
verify-C-19.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
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
OUTPUT = EVIDENCE / "mutaciones-C-19.txt"
VERIFY = EVIDENCE / "verify-C-19.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
RECREATE_REVISION = "20261105_05_historial_sin_truncate"
TIMEOUT_SECONDS = 180

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

USER_PERSISTENCE = "tests/integration/test_user_persistence.py"
INFRASTRUCTURE = "tests/integration/test_database_infrastructure.py"
PASSWORDS_TEST = "tests/auth/test_passwords.py"
LOGIN_TEST = "tests/integration/test_auth_login.py"
TOKEN_REJECTION = "tests/api/test_token_rejection.py"
CURRENT_USER = "tests/integration/test_auth_current_user.py"
PERMISSIONS_TEST = "tests/auth/test_permissions.py"
RBAC_MATRIX = "tests/integration/test_rbac_matrix.py"
SEED_USERS = "tests/integration/test_seed_users.py"
USER_REPOSITORY = "tests/integration/test_user_repository.py"
MODEL_TEST = "tests/auth/test_model.py"
CONFIG_TEST = "tests/test_config.py"

MIGRATION_05 = "backend/alembic/versions/20261105_05_historial_sin_truncate.py"
MIGRATION_06 = "backend/alembic/versions/20261106_06_usuarios.py"
PASSWORDS = "backend/app/auth/passwords.py"
LOGIN = "backend/app/auth/login.py"
TOKENS = "backend/app/auth/tokens.py"
DEPS = "backend/app/api/deps.py"
PERMISSIONS = "backend/app/auth/permissions.py"
SEED = "backend/app/db/seed.py"
SESSION = "backend/app/db/session.py"
USERS = "backend/app/repositories/users.py"
MODEL = "backend/app/auth/model.py"
CONFIG = "backend/app/config.py"

# Corre en un proceso aparte para que Alembic importe la migracion tal como esta en
# disco. "upgrade head" primero porque una mutacion de downgrade puede dejar la base
# por debajo de la revision de recreacion. La URL siempre apunta a la base _test.
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
    command.upgrade(config, "head")
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
    # Las mutaciones de downgrade dejan restos que el downgrade no puede revertir:
    # este SQL los quita despues de restaurar el archivo.
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


_INVALID_TOKEN = "        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)\n"

MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        USER_PERSISTENCE,
        "test_doctor_without_professional_is_rejected",
        MIGRATION_06,
        "\"(role = 'odontologo' AND professional_id IS NOT NULL) \"",
        "\"(role = 'odontologo') \"",
    ),
    Mutation(
        USER_PERSISTENCE,
        "test_reception_with_professional_is_rejected",
        MIGRATION_06,
        "\"OR (role <> 'odontologo' AND professional_id IS NULL)\"",
        "\"OR (role <> 'odontologo')\"",
    ),
    Mutation(
        USER_PERSISTENCE,
        "test_two_users_for_same_professional_are_rejected",
        MIGRATION_06,
        '["professional_id"],\n        unique=True,',
        '["professional_id"],\n        unique=False,',
    ),
    Mutation(
        INFRASTRUCTURE,
        "test_user_migration_explicit_downgrade_cycle",
        MIGRATION_06,
        '    op.drop_index("ux_app_user_professional_id", table_name="app_user")\n'
        '    op.drop_index("ux_app_user_username", table_name="app_user")\n'
        '    op.drop_table("app_user")\n',
        "    pass\n",
        repair_sql="DROP TABLE IF EXISTS app_user CASCADE",
    ),
    Mutation(
        PASSWORDS_TEST,
        "test_hash_uses_fixed_parameters",
        PASSWORDS,
        "time_cost=3,",
        "time_cost=1,",
    ),
    Mutation(
        PASSWORDS_TEST,
        "test_missing_user_uses_dummy_hash",
        PASSWORDS,
        "        return dummy_password_hash()\n",
        '        return "$argon2id$v=19$m=8,t=1,p=1$c2FsdHNhbHQ$aGFzaGhhc2g"\n',
    ),
    Mutation(
        LOGIN_TEST,
        "test_inactive_user_with_correct_password_is_rejected",
        LOGIN,
        "if credentials is None or not password_ok or not credentials.active:",
        "if credentials is None or not password_ok:",
    ),
    Mutation(
        TOKEN_REJECTION,
        "test_rejected_token[other_algorithm]",
        TOKENS,
        "algorithms=[settings.jwt_algorithm],",
        'algorithms=["HS256", "HS512"],',
    ),
    Mutation(
        TOKEN_REJECTION,
        "test_rejected_token[missing_exp]",
        TOKENS,
        'options={"require": ["exp", "sub", "role"]},',
        'options={"require": ["sub", "role"]},',
    ),
    Mutation(
        CURRENT_USER,
        "test_deactivated_user_with_valid_token_is_rejected",
        DEPS,
        "    if not stored.active:\n" + _INVALID_TOKEN,
        "",
    ),
    Mutation(
        CURRENT_USER,
        "test_role_changed_user_with_valid_token_is_rejected",
        DEPS,
        "    if stored.user.role is not claims.role:\n" + _INVALID_TOKEN,
        "",
    ),
    Mutation(
        PERMISSIONS_TEST,
        "test_permissions_match_literal_matrix",
        PERMISSIONS,
        "(Resource.PROFESSIONAL, Action.CREATE): {_A: _ALL},",
        "(Resource.PROFESSIONAL, Action.CREATE): {_R: _ALL, _A: _ALL},",
    ),
    Mutation(
        RBAC_MATRIX,
        "test_matrix_cell_over_http[PATIENT-DELETE-administrador]",
        DEPS,
        "        if scope is None:\n",
        "        scope = scope or Scope.ALL\n        if scope is None:\n",
    ),
    Mutation(
        SEED_USERS,
        "test_seed_rejects_short_password",
        SEED,
        "    if len(password) < SEED_PASSWORD_MIN_LENGTH:\n",
        "    if False:\n",
    ),
    Mutation(
        SEED_USERS,
        "test_seed_refuses_production",
        SEED,
        '    if settings.app_env == "production":\n',
        "    if False:\n",
    ),
    Mutation(
        USER_REPOSITORY,
        "test_duplicate_username_error_hides_hash",
        SESSION,
        "hide_parameters=True,",
        "hide_parameters=False,",
    ),
    Mutation(
        USER_REPOSITORY,
        "test_role_rule_error_hides_hash",
        USERS,
        "raise UserWriteError(constraint_name(error)) from None",
        "raise UserWriteError(str(error))",
    ),
    Mutation(
        MODEL_TEST,
        "test_credentials_repr_hides_hash",
        MODEL,
        "password_hash: str = field(repr=False)",
        "password_hash: str",
    ),
    Mutation(
        CONFIG_TEST,
        "test_short_secret_error_hides_value",
        CONFIG,
        "        hide_input_in_errors=True,\n",
        "",
    ),
    Mutation(
        CURRENT_USER,
        "test_valid_token_is_accepted",
        TOKENS,
        '    """Devuelve los claims, o `None` ante cualquier token inválido o vencido."""\n',
        "    return None\n",
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


def run_db_helper(report: Report, title: str, *arguments: str) -> None:
    result = run_command([PYTHON, "-c", DB_HELPER, *arguments])
    report.write(f"--- {title} (codigo de salida {result.returncode}) ---")
    report.write(result.stdout + result.stderr)
    if result.returncode != 0:
        raise MutationAbort(f"Fallo el paso de base de test: {title}")


def recreate_test_database(report: Report, title: str) -> None:
    run_db_helper(report, title, "recreate", RECREATE_REVISION)


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

    if mutation.is_migration and mutation.repair_sql is not None:
        recreate_test_database(report, "base de test recreada antes de aplicar la mutacion")

    try:
        path.write_bytes(
            read_source(mutation)
            .replace(mutation.original, mutation.mutated)
            .encode("utf-8")
        )
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
    return outcome == "FALLO"


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
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-19.py. No editar a mano.")
        report.write(f"SHA-256 de backend/app y backend/alembic antes: {sha_before}")
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
            f"SHA-256 de backend/app y backend/alembic despues: {sha_after}",
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
