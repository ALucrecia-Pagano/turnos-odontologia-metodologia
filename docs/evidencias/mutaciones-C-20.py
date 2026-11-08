"""Verificacion por mutacion, reproducible, de los tests de C-20.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-20.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, corre solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-20.txt y regenera la tabla de
verify-C-20.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
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
OUTPUT = EVIDENCE / "mutaciones-C-20.txt"
VERIFY = EVIDENCE / "verify-C-20.md"
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

TEST_PROFESSIONALS = "tests/integration/test_api_professionals.py"
TEST_CHAIRS = "tests/integration/test_api_chairs.py"
TEST_SERVICES = "tests/integration/test_api_services.py"
TEST_PATIENTS = "tests/integration/test_api_patients.py"
TEST_DEACTIVATION = "tests/integration/test_api_deactivation.py"
TEST_DOMAIN_UPDATE = "tests/domain/test_catalog_update.py"

DOMAIN_UPDATE = "backend/app/domain/catalog/update.py"
REPO_CATALOG = "backend/app/repositories/catalog.py"
REPO_PATIENTS = "backend/app/repositories/patients.py"
SERVICE_CATALOG = "backend/app/services/catalog.py"
SERVICE_PATIENTS = "backend/app/services/patients.py"
API_SCHEMAS = "backend/app/api/schemas.py"
API_ERRORS = "backend/app/api/errors.py"
API_PROFESSIONALS = "backend/app/api/professionals.py"
API_CHAIRS = "backend/app/api/chairs.py"
API_SERVICES = "backend/app/api/services.py"
API_PATIENTS = "backend/app/api/patients.py"


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
    Mutation(
        TEST_CHAIRS,
        "test_update_chair_conserving_own_name_responds_200",
        DOMAIN_UPDATE,
        'def update_chair(candidate: Chair, existing: Sequence[Chair]) -> CatalogResult[Chair]:\n'
        '    """Valida la edición de un sillón excluyendo el propio identificador de duplicados."""\n'
        '    violations = check_name(candidate.name, "del sillón")\n'
        '    if not violations:\n'
        '        other_names = [item.name for item in existing if item.id != candidate.id]',
        'def update_chair(candidate: Chair, existing: Sequence[Chair]) -> CatalogResult[Chair]:\n'
        '    """Valida la edición de un sillón excluyendo el propio identificador de duplicados."""\n'
        '    violations = check_name(candidate.name, "del sillón")\n'
        '    if not violations:\n'
        '        other_names = [item.name for item in existing if item.id == candidate.id]',
    ),
    Mutation(
        TEST_DOMAIN_UPDATE,
        "test_update_service_invalid_duration",
        DOMAIN_UPDATE,
        '    violations += check_duration(candidate.default_duration_min, subject="de la prestación")',
        "    pass",
    ),
    Mutation(
        TEST_PATIENTS,
        "test_update_patient_conserving_own_dni_responds_200",
        DOMAIN_UPDATE,
        "other_dnis = [item.dni for item in existing if item.id != candidate.id]",
        "other_dnis = [item.dni for item in existing if item.id == candidate.id]",
    ),
    Mutation(
        TEST_PROFESSIONALS,
        "test_detail_professional_existing_responds_200",
        REPO_CATALOG,
        "    def get_with_license(self, identifier: UUID) -> ProfessionalWithLicense | None:\n"
        "        row = self._session.get(ProfessionalModel, identifier)",
        "    def get_with_license(self, identifier: UUID) -> ProfessionalWithLicense | None:\n"
        "        row = None",
    ),
    Mutation(
        TEST_PROFESSIONALS,
        "test_update_professional_responds_200",
        REPO_CATALOG,
        "        row.license_number = license_number\n"
        "        self._session.flush()\n"
        "        return Ok(result.entity)",
        "        row.license_number = license_number\n"
        "        self._session.flush()\n"
        "        return None",
    ),
    Mutation(
        TEST_PATIENTS,
        "test_search_patients_by_name_part",
        REPO_PATIENTS,
        '                clauses: list[ColumnElement[bool]] = [PatientModel.full_name.ilike(f"%{escaped}%", escape="\\\\")]',
        '                clauses: list[ColumnElement[bool]] = [PatientModel.full_name.ilike(f"{escaped}%", escape="\\\\")]',
    ),
    Mutation(
        TEST_PATIENTS,
        "test_search_patients_by_dni_prefix",
        REPO_PATIENTS,
        "                if digits:\n"
        "                    clauses.append(PatientModel.dni.startswith(digits))",
        "                if False:\n"
        "                    clauses.append(PatientModel.dni.startswith(digits))",
    ),
    Mutation(
        TEST_PROFESSIONALS,
        "test_detail_professional_nonexistent_responds_404",
        SERVICE_CATALOG,
        "    if record is None:\n"
        '        raise NotFoundError("Profesional no encontrado.")',
        "    if record is None:\n"
        '        raise NotFoundError("Profesional inexistente.")',
    ),
    Mutation(
        TEST_PATIENTS,
        "test_detail_patient_nonexistent_responds_404",
        SERVICE_PATIENTS,
        "    row = repo.get_by_id(identifier)\n"
        "    if row is None:\n"
        '        raise NotFoundError("Paciente no encontrado.")',
        "    row = repo.get_by_id(identifier)\n"
        "    if row is None:\n"
        '        raise NotFoundError("Paciente inexistente.")',
    ),
    Mutation(
        TEST_PROFESSIONALS,
        "test_create_professional_malformed_body_responds_400",
        API_SCHEMAS,
        'class ProfessionalInput(BaseModel):\n'
        '    full_name: str = Field(alias="fullName")\n'
        '    license_number: str | None = Field(default=None, alias="licenseNumber")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class ProfessionalInput(BaseModel):\n'
        '    full_name: str = Field(alias="fullName")\n'
        '    license_number: str | None = Field(default=None, alias="licenseNumber")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="ignore")',
    ),
    Mutation(
        TEST_CHAIRS,
        "test_detail_chair_nonexistent_responds_404",
        API_ERRORS,
        '    return JSONResponse(\n'
        '        status_code=404,\n'
        '        content={"code": "NOT_FOUND", "message": exc.message},\n'
        '    )',
        '    return JSONResponse(\n'
        '        status_code=400,\n'
        '        content={"code": "NOT_FOUND", "message": exc.message},\n'
        '    )',
    ),
    Mutation(
        TEST_PROFESSIONALS,
        "test_create_professional_with_license_responds_201",
        API_PROFESSIONALS,
        '@router.post(\n'
        '    "",\n'
        '    status_code=status.HTTP_201_CREATED,',
        '@router.post(\n'
        '    "",\n'
        '    status_code=status.HTTP_200_OK,',
    ),
    Mutation(
        TEST_SERVICES,
        "test_list_services_without_filter_includes_inactive_alphabetical",
        API_SERVICES,
        "    services = list_services(session, active=active)",
        "    services = list_services(session, active=True)",
    ),
    Mutation(
        TEST_PATIENTS,
        "test_create_patient_by_reception_responds_201",
        API_PATIENTS,
        '        Depends(require_permission(Resource.PATIENT, Action.CREATE)),',
        '        Depends(require_permission(Resource.PROFESSIONAL, Action.CREATE)),',
    ),
    Mutation(
        TEST_DEACTIVATION,
        "test_deactivate_chair_rejected_for_reception_403",
        API_CHAIRS,
        '        Depends(require_permission(Resource.CHAIR, Action.DELETE)),',
        '        Depends(require_permission(Resource.CHAIR, Action.READ)),',
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
        report.write("Salida generada por docs/evidencias/mutaciones-C-20.py. No editar a mano.")
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
