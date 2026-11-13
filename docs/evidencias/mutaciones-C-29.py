"""Verificación por mutación, reproducible, de los tests de C-29 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-29.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación por cada test nuevo de C-29: antes de mutar se cuentan los tests con `vitest list --json`
y se exige una correspondencia uno a uno con los 27 tests nuevos.

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-29.txt (salida cruda de Vitest incluida) y actualiza la tabla de verify-C-29.md.
Termina con código 0 solo si todas las mutaciones hicieron fallar su test, ninguna es INVÁLIDA y el SHA-256
del código de producción no cambió.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "mutaciones-C-29.txt"
VERIFY = EVIDENCE / "verify-C-29.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 300
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

INVALID_ERROR = re.compile(
    r"^(ReferenceError|SyntaxError|TypeError|RangeError|TestingLibraryElementError"
    r"|Error: (Failed to load|Failed to resolve|Cannot find module|Transform failed))"
)
ASSERTION = re.compile(r"^(AssertionError\b|Error: expect\()")
STACK_FRAME = re.compile(r"^\s*at (?:.*\()?(?:file:///)?(?P<path>[A-Za-z]:[\\/][^:()]+|/[^:()]+):\d+:\d+\)?$")
TEST_FILE = re.compile(r"\.test\.tsx?$")

# --- Archivos de test de C-29 ---
T_DIALOG = "src/shared/components/Dialog.test.tsx"
T_CLIENT_VIOLATIONS = "src/shared/api/client.violations.test.ts"
T_PATIENT_SEARCH = "src/features/appointments/PatientSearchGroup.test.tsx"
T_FORM = "src/features/appointments/AppointmentFormDialog.test.tsx"
T_TOOLBAR = "src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx"
T_PAGE = "src/features/agenda/AgendaPage.nuevoTurno.test.tsx"

C29_TEST_FILES = (
    T_DIALOG,
    T_CLIENT_VIOLATIONS,
    T_PATIENT_SEARCH,
    T_FORM,
    T_TOOLBAR,
    T_PAGE,
)

# --- Archivos de producción modificados o creados en C-29 ---
P_DIALOG = "frontend/src/shared/components/Dialog.tsx"
P_CLIENT = "frontend/src/shared/api/client.ts"
P_PATIENT_SEARCH = "frontend/src/features/appointments/PatientSearchGroup.tsx"
P_FORM = "frontend/src/features/appointments/AppointmentFormDialog.tsx"
P_TOOLBAR = "frontend/src/features/agenda/AgendaToolbar.tsx"
P_PAGE = "frontend/src/features/agenda/AgendaPage.tsx"

PRODUCTION_FILES = (
    P_DIALOG,
    P_CLIENT,
    P_PATIENT_SEARCH,
    P_FORM,
    P_TOOLBAR,
    P_PAGE,
)


@dataclass(frozen=True)
class Mutation:
    test_file: str
    test_name: str
    file: str
    original: str
    mutated: str

    @property
    def node_id(self) -> str:
        return f"{self.test_file} > {self.test_name}"


MUTATIONS: tuple[Mutation, ...] = (
    # --- 1. Primitiva Dialog (3 tests) ---
    Mutation(
        T_DIALOG,
        "abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby",
        P_DIALOG,
        '      } else {\n        dialog.setAttribute("open", "");\n      }',
        '      } else {\n        // dialog.setAttribute("open", "");\n      }',
    ),
    Mutation(
        T_DIALOG,
        "Escape llama onClose exactamente una vez",
        P_DIALOG,
        '    if (event.key !== "Escape") {\n      return;\n    }',
        '    if (event.key !== "Enter") {\n      return;\n    }',
    ),
    Mutation(
        T_DIALOG,
        "al pasar open de true a false el foco vuelve a returnFocusRef",
        P_DIALOG,
        "      wasOpenRef.current = false;\n      returnFocusRef?.current?.focus();",
        "      wasOpenRef.current = false;\n      // returnFocusRef?.current?.focus();",
    ),
    # --- 2. Contratos y tipos de API (1 test) ---
    Mutation(
        T_CLIENT_VIOLATIONS,
        "captura conflictingAppointmentId, conflictingBlockId, conflictingInterval y referenceKind",
        P_CLIENT,
        "    if (isString(item.referenceKind)) {\n      violation.referenceKind = item.referenceKind;\n    }",
        "    if (isString(item.referenceKind)) {\n      // violation.referenceKind = item.referenceKind;\n    }",
    ),
    # --- 3. Búsqueda de pacientes (4 tests) ---
    Mutation(
        T_PATIENT_SEARCH,
        "renderizado inicial: input de búsqueda, botón Buscar paciente habilitado y sin radio buttons",
        P_PATIENT_SEARCH,
        '        <button\n          type="button"\n          className={styles.searchButton}\n          onClick={() => void handleSearch()}\n          disabled={isLoading}\n        >',
        '        <button\n          type="button"\n          className={styles.searchButton}\n          onClick={() => void handleSearch()}\n          disabled={true}\n        >',
    ),
    Mutation(
        T_PATIENT_SEARCH,
        "búsqueda con resultados muestra radio buttons con nombre y DNI",
        P_PATIENT_SEARCH,
        "              <span>\n                {p.fullName} (DNI {p.dni})\n              </span>",
        "              <span>\n                {p.fullName}\n              </span>",
    ),
    Mutation(
        T_PATIENT_SEARCH,
        "búsqueda sin resultados muestra aviso accesible y sin radio buttons",
        P_PATIENT_SEARCH,
        '        <p className={styles.notice} role="status">\n          No se encontraron pacientes\n        </p>',
        '        <p className={styles.notice} role="status">\n          Sin resultados\n        </p>',
    ),
    Mutation(
        T_PATIENT_SEARCH,
        "selección por clic o teclado invoca onSelectPatient con el id correspondiente",
        P_PATIENT_SEARCH,
        "                onChange={() => onSelectPatient(p.id)}",
        "                onChange={() => undefined}",
    ),
    # --- 4. Formulario modal de turnos (14 tests) ---
    Mutation(
        T_FORM,
        "apertura y foco inicial",
        P_FORM,
        "    if (open) {\n      patientSearchInputRef.current?.focus();",
        "    if (open) {\n      // patientSearchInputRef.current?.focus();",
    ),
    Mutation(
        T_FORM,
        "prellenado con fecha y filtros activos",
        P_FORM,
        '  const [professionalId, setProfessionalId] = useState(initialProfessionalId ?? "");',
        '  const [professionalId, setProfessionalId] = useState("");',
    ),
    Mutation(
        T_FORM,
        "sin filtros activos los selectores quedan sin selección",
        P_FORM,
        '  const [chairId, setChairId] = useState(initialChairId ?? "");',
        '  const [chairId, setChairId] = useState(initialChairId ?? "00000000-0000-0000-0000-0000000000b1");',
    ),
    Mutation(
        T_FORM,
        "duración sugerida al elegir prestación",
        P_FORM,
        "    const s = services.find((srv) => srv.id === selectedId);\n    if (s) {\n      setDurationMin(s.defaultDurationMin);\n    }",
        "    const s = services.find((srv) => srv.id === selectedId);\n    if (s) {\n      setDurationMin(15);\n    }",
    ),
    Mutation(
        T_FORM,
        "edición manual de duración se conserva",
        P_FORM,
        '                  const val = e.target.value;\n                  setDurationMin(val === "" ? "" : Number(val));',
        '                  const val = e.target.value;\n                  setDurationMin(val === "" ? "" : 60);',
    ),
    Mutation(
        T_FORM,
        "armado de startAt con offset exacto para la fecha elegida y timezone de la API",
        P_FORM,
        "  return `${dateStr}T${timeStr}:00${offset}`;",
        '  return `${dateStr}T${timeStr}:00Z`;',
    ),
    Mutation(
        T_FORM,
        "envío exitoso 201 cierra el modal, llama onSuccess con los datos del turno y devuelve foco",
        P_FORM,
        "    if (result.ok && result.status === 201) {\n      onSuccess?.({ date, time });\n      onClose();\n      return;\n    }",
        "    if (result.ok && result.status === 201) {\n      // onSuccess?.({ date, time });\n      onClose();\n      return;\n    }",
    ),
    Mutation(
        T_FORM,
        "respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias",
        P_FORM,
        '                <li key={i}>\n                  <span className={styles.codeBadge}>{v.code}</span>\n                  {v.message}\n                </li>',
        '                <li key={i}>\n                  {/* <span className={styles.codeBadge}>{v.code}</span> */}\n                  {v.message}\n                </li>',
    ),
    Mutation(
        T_FORM,
        "rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos",
        P_FORM,
        '        result.error.kind === "unprocessable" ||',
        '        // result.error.kind === "unprocessable" ||',
    ),
    Mutation(
        T_FORM,
        "mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline",
        P_FORM,
        '      } else if (result.error.kind === "validation") {\n        const mappedErrors: Record<string, string> = {};\n        for (const err of result.error.errors) {\n          if (err.field) {\n            mappedErrors[err.field] = err.message;\n          }\n        }\n        setFieldErrors(mappedErrors);',
        '      } else if (result.error.kind === "validation") {\n        const mappedErrors: Record<string, string> = {};\n        for (const err of result.error.errors) {\n          if (err.field) {\n            mappedErrors[err.field] = err.message;\n          }\n        }\n        // setFieldErrors(mappedErrors);',
    ),
    Mutation(
        T_FORM,
        "respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión",
        P_FORM,
        '        result.error.kind === "forbidden"',
        '        result.error.kind === ("unknown" as string)',
    ),
    Mutation(
        T_FORM,
        "foco al resumen de alerta ante fallo",
        P_FORM,
        '        setViolations(result.error.violations);\n        setTimeout(() => alertRef.current?.focus(), 0);',
        '        setViolations(result.error.violations);\n        // setTimeout(() => alertRef.current?.focus(), 0);',
    ),
    Mutation(
        T_FORM,
        "pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura",
        P_FORM,
        '            <button\n              type="button"\n              className={styles.secondaryButton}\n              onClick={onClose}\n              disabled={isSubmitting}\n            >\n              Cancelar\n            </button>',
        '            <button\n              type="button"\n              className={styles.secondaryButton}\n              onClick={() => undefined}\n              disabled={isSubmitting}\n            >\n              Cancelar\n            </button>',
    ),
    Mutation(
        T_FORM,
        "Escape cierra sin enviar solicitudes y devuelve el foco",
        P_FORM,
        "  const handleDialogClose = () => {\n    onClose();\n  };",
        "  const handleDialogClose = () => {\n    // onClose();\n  };",
    ),
    # --- 5. Toolbar acción Nuevo turno (3 tests) ---
    Mutation(
        T_TOOLBAR,
        "visible para recepción y dispara onNewAppointment al clic",
        P_TOOLBAR,
        '  const canCreateAppointment =\n    (userRole === "recepcion" || userRole === "administrador") &&\n    onNewAppointment !== undefined;',
        '  const canCreateAppointment =\n    (userRole === "administrador") &&\n    onNewAppointment !== undefined;',
    ),
    Mutation(
        T_TOOLBAR,
        "visible para administrador",
        P_TOOLBAR,
        '  const canCreateAppointment =\n    (userRole === "recepcion" || userRole === "administrador") &&\n    onNewAppointment !== undefined;',
        '  const canCreateAppointment =\n    (userRole === "recepcion") &&\n    onNewAppointment !== undefined;',
    ),
    Mutation(
        T_TOOLBAR,
        "no visible para odontólogo",
        P_TOOLBAR,
        '  const canCreateAppointment =\n    (userRole === "recepcion" || userRole === "administrador") &&\n    onNewAppointment !== undefined;',
        '  const canCreateAppointment =\n    (userRole !== null) &&\n    onNewAppointment !== undefined;',
    ),
    # --- 6. Integración en AgendaPage (2 tests) ---
    Mutation(
        T_PAGE,
        "al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda",
        P_PAGE,
        "    void state.refresh();",
        "    // void state.refresh();",
    ),
    Mutation(
        T_PAGE,
        "tras alta exitosa (201) anuncia el turno creado en una región de estado accesible",
        P_PAGE,
        '      setStatusMessage(`Turno creado para el ${day}/${month}/${year} a las ${info.time}.`);',
        '      setStatusMessage("Turno creado");',
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text: str) -> None:
        self.stream.write(text.rstrip() + "\n")
        self.stream.flush()


def production_sha256() -> str:
    hasher = hashlib.sha256()
    for relative in sorted(PRODUCTION_FILES):
        path = REPO / relative
        hasher.update(path.as_posix().encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def vitest_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env


def apply_mutation(mutation: Mutation, content: str) -> str:
    original = mutation.original
    mutated = mutation.mutated
    if "\r\n" in content and "\r\n" not in original:
        original = original.replace("\n", "\r\n")
        mutated = mutated.replace("\n", "\r\n")
    elif "\r\n" not in content and "\r\n" in original:
        original = original.replace("\r\n", "\n")
        mutated = mutated.replace("\r\n", "\n")
    return content.replace(original, mutated, 1)


def check_definition(mutation: Mutation) -> None:
    path = REPO / mutation.file
    if not path.is_file():
        raise MutationAbort(f"{mutation.node_id}: no existe {mutation.file}")
    content = path.read_text(encoding="utf-8")
    norm_content = content.replace("\r\n", "\n")
    norm_original = mutation.original.replace("\r\n", "\n")
    count = norm_content.count(norm_original)
    if count == 0:
        raise MutationAbort(f"{mutation.node_id}: original no encontrado en {mutation.file}")
    if count > 1:
        raise MutationAbort(f"{mutation.node_id}: original aparece {count} veces en {mutation.file}")


def listed_tests() -> list[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=vitest_env(),
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
        if file in C29_TEST_FILES:
            tests.append((file, name))
    return tests


def check_one_to_one() -> int:
    tests = listed_tests()
    mutated = [(m.test_file, m.test_name) for m in MUTATIONS]
    missing = sorted(set(tests) - set(mutated))
    unknown = sorted(set(mutated) - set(tests))
    repeated = sorted({t for t in mutated if mutated.count(t) > 1})
    if missing or unknown or repeated or len(tests) != len(MUTATIONS):
        raise MutationAbort(
            f"tests nuevos de C-29 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
            cwd=FRONTEND,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=vitest_env(),
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        report: dict[str, object] = (
            json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {}
        )
    return result, report


def run_single(mutation: Mutation) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    pattern = re.escape(mutation.test_name) + "$"
    return run_vitest([mutation.test_file, "-t", pattern])


def first_own_frame(message: str) -> str | None:
    for line in message.splitlines():
        match = STACK_FRAME.match(line)
        if match and "node_modules" not in match.group("path"):
            return match.group("path").replace("\\", "/")
    return None


def invalid_reason(mutation: Mutation, report: dict[str, object]) -> str | None:
    """Devuelve el motivo si el test no detecto la mutacion con una afirmacion propia."""
    files = report.get("testResults")
    if not isinstance(files, list) or not files:
        return "Vitest no genero resultados"
    ran: list[dict[str, object]] = []
    for file_result in files:
        assertions = file_result.get("assertionResults", [])
        message = str(file_result.get("message") or "")
        if message and not assertions:
            return f"el archivo de test no cargo: {message.splitlines()[0]}"
        ran += [a for a in assertions if a.get("status") in ("passed", "failed")]
    if len(ran) != 1 or ran[0].get("title") != mutation.test_name:
        return f"se ejecutaron {len(ran)} tests en lugar de solo el de la mutacion"
    failures = ran[0].get("failureMessages") or []
    if not isinstance(failures, list) or not failures:
        return "el test fallo sin mensaje"
    message = str(failures[0])
    first_line = message.splitlines()[0] if message else ""
    if INVALID_ERROR.match(first_line):
        return f"el fallo no es una afirmacion: {first_line}"
    if not ASSERTION.match(first_line):
        return f"el fallo no es AssertionError ni expect(...): {first_line}"
    frame = first_own_frame(message)
    if frame is None or not TEST_FILE.search(frame):
        return f"el primer frame propio no es un *.test.ts(x): {frame}"
    return None


def first_failure_line(report: dict[str, object]) -> str:
    for file_result in report.get("testResults", []) or []:
        for assertion in file_result.get("assertionResults", []):
            failures = assertion.get("failureMessages") or []
            if failures:
                return str(failures[0]).splitlines()[0][:90]
    return "sin fallo"


def run_mutation(
    mutation: Mutation,
    index: int,
    report: Report,
) -> tuple[bool, str | None, str, str]:
    target = REPO / mutation.file
    original_bytes = target.read_bytes()
    original_content = original_bytes.decode("utf-8")
    mutated_content = apply_mutation(mutation, original_content)
    if mutated_content == original_content:
        raise MutationAbort(f"{mutation.node_id}: el mutante no cambio el archivo {mutation.file}")

    diff_lines = list(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            mutated_content.splitlines(keepends=True),
            fromfile=f"a/{mutation.file}",
            tofile=f"b/{mutation.file}",
        )
    )

    report.write(SEPARATOR)
    report.write(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}")
    report.write(f"test: {mutation.node_id}")
    report.write("diff:")
    report.write("".join(diff_lines))

    target.write_bytes(mutated_content.encode("utf-8"))
    try:
        mutated_result, mutated_report = run_single(mutation)
    finally:
        target.write_bytes(original_bytes)

    report.write(f"--- salida mutada (codigo de salida {mutated_result.returncode}) ---")
    report.write(mutated_result.stdout + mutated_result.stderr)

    restored_result, _ = run_single(mutation)
    if restored_result.returncode != 0:
        report.write("FATAL: el test no volvio a verde tras restaurar el archivo")
        report.write(restored_result.stdout + restored_result.stderr)
        raise MutationAbort(f"{mutation.node_id}: no volvio a verde tras restaurar {mutation.file}")
    report.write("restaurado: test en verde")

    killed = mutated_result.returncode != 0
    reason = invalid_reason(mutation, mutated_report) if killed else None
    if reason:
        report.write(f"INVALIDA: {reason}")
    changed = " ".join(
        line.strip()
        for line in diff_lines
        if line.startswith(("-", "+")) and not line.startswith(("---", "+++"))
    )[:90]
    return killed, reason, changed, first_failure_line(mutated_report)


def update_verify_table(rows: list[str]) -> None:
    if not VERIFY.exists():
        return
    table = "\n".join(
        ["| # | Test | Archivo | Mutación | Primera línea del fallo |", "|---|---|---|---|---|", *rows]
    )
    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start != -1 and end != -1:
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
            encoding="utf-8",
            newline="\n",
        )


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("`", "'")


def main() -> int:
    for mutation in MUTATIONS:
        check_definition(mutation)
    total_tests = check_one_to_one()

    if "--check" in sys.argv:
        print(
            f"Las {len(MUTATIONS)} mutaciones estan bien definidas, "
            f"una por cada uno de los {total_tests} tests de C-29."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-29.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-29 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C29_TEST_FILES))
        report.write(f"--- linea de base, sin mutaciones (codigo de salida {baseline.returncode}) ---")
        report.write(baseline.stdout + baseline.stderr)
        if baseline.returncode != 0:
            raise MutationAbort("Los tests no estan en verde antes de mutar")

        for index, mutation in enumerate(MUTATIONS, start=1):
            print(f"[{index:02d}/{len(MUTATIONS)}] {mutation.node_id}", flush=True)
            was_killed, reason, changed, failure = run_mutation(mutation, index, report)
            if reason:
                invalid.append(f"{mutation.node_id}: {reason}")
                print(f"    INVALIDA: {reason}", flush=True)
            elif was_killed:
                killed.append(mutation.node_id)
            else:
                survived.append(mutation.node_id)
                print("    NO hizo fallar su test", flush=True)
            rows.append(
                f"| {index} | `{cell(mutation.test_name)}` | `{mutation.file}` | `{cell(changed)}` | `{cell(failure)}` |"
            )

        sha_after = production_sha256()
        same = sha_before == sha_after
        summary = [
            SEPARATOR,
            *[f"  - sobrevivio: {name}" for name in survived],
            *[f"  - invalida: {entry}" for entry in invalid],
            "RESUMEN",
            f"mutaciones que hicieron fallar su test: {len(killed)}",
            f"mutaciones que NO lo hicieron fallar: {len(survived)}",
            f"mutaciones inválidas: {len(invalid)}",
            f"SHA-256 de produccion despues: {sha_after}",
            f"SHA-256 sin cambios: {'si' if same else 'NO'}",
        ]
        report.write("\n".join(summary))

    print("\n".join(summary))
    update_verify_table(rows)
    return 0 if same and not survived and not invalid else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationAbort as error:
        print(f"ABORTADO: {error}", file=sys.stderr)
        sys.exit(2)
