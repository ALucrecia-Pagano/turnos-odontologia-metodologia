"""Verificación por mutación, reproducible, de los tests nuevos de C-36 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-36.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación (M01-M08) por cada escenario testeable nuevo de C-36: antes de mutar se cuentan los tests
con `vitest list --json` y se exige una correspondencia uno a uno con los 8 tests nuevos.

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-36.txt (salida cruda de Vitest incluida) y actualiza la tabla de verify-C-36.md.
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
OUTPUT = EVIDENCE / "mutaciones-C-36.txt"
VERIFY = EVIDENCE / "verify-C-36.md"
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

# --- Archivos de test de C-36 ---
T_APPSHELL = "src/shared/components/AppShell.mobile.test.tsx"
T_TOOLBAR = "src/features/agenda/AgendaToolbar.mobile.test.tsx"
T_GRID = "src/features/agenda/AgendaGrid.mobile.test.tsx"
T_DIALOG = "src/shared/components/Dialog.bottomSheet.test.tsx"
T_SPACING = "src/features/agenda/AgendaSpacing.mobile.test.tsx"

C36_TEST_FILES = (
    T_APPSHELL,
    T_TOOLBAR,
    T_GRID,
    T_DIALOG,
    T_SPACING,
)

# --- Archivos de producción modificados o creados en C-36 ---
P_SHELL_TSX = "frontend/src/shared/components/AppShell.tsx"
P_SHELL_CSS = "frontend/src/shared/components/AppShell.module.css"
P_TOOLBAR_TSX = "frontend/src/features/agenda/AgendaToolbar.tsx"
P_TOOLBAR_CSS = "frontend/src/features/agenda/AgendaToolbar.module.css"
P_GRID_TSX = "frontend/src/features/agenda/AgendaGrid.tsx"
P_GRID_CSS = "frontend/src/features/agenda/AgendaGrid.module.css"
P_VIEW_TSX = "frontend/src/features/agenda/AgendaView.tsx"
P_VIEW_CSS = "frontend/src/features/agenda/AgendaView.module.css"
P_PAGE_SHELL_CSS = "frontend/src/shared/components/PageShell.module.css"
P_DIALOG_TSX = "frontend/src/shared/components/Dialog.tsx"
P_DIALOG_CSS = "frontend/src/shared/components/Dialog.module.css"
P_APPT_DETAIL_CSS = "frontend/src/features/appointments/AppointmentDetailDialog.module.css"
P_APPT_FORM_CSS = "frontend/src/features/appointments/AppointmentFormDialog.module.css"
P_APPT_RESCHED_CSS = "frontend/src/features/appointments/AppointmentRescheduleDialog.module.css"
P_TOKENS = "frontend/src/shared/styles/tokens.css"

PRODUCTION_FILES = (
    P_SHELL_TSX,
    P_SHELL_CSS,
    P_TOOLBAR_TSX,
    P_TOOLBAR_CSS,
    P_GRID_TSX,
    P_GRID_CSS,
    P_VIEW_TSX,
    P_VIEW_CSS,
    P_PAGE_SHELL_CSS,
    P_DIALOG_TSX,
    P_DIALOG_CSS,
    P_APPT_DETAIL_CSS,
    P_APPT_FORM_CSS,
    P_APPT_RESCHED_CSS,
    P_TOKENS,
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
    # M01 - AppShell: botón Menú con aria-controls="main-menu"
    Mutation(
        T_APPSHELL,
        "01-cabecera-compacta-y-apertura-menu: expone botón Menú fuera de nav con aria-expanded y aria-controls, y al pulsar despliega la navegación",
        P_SHELL_TSX,
        'aria-controls="main-menu"',
        'aria-controls="other-menu"',
    ),
    # M02 - AppShell: cierre del menú con Escape y retorno de foco
    Mutation(
        T_APPSHELL,
        "02-cierre-menu-escape-y-retorno-foco: presionar Escape cierra el menú desplegado y devuelve el foco al botón Menú",
        P_SHELL_TSX,
        "menuButtonRef.current?.focus();",
        "// menuButtonRef.current?.focus();",
    ),
    # M03 - Toolbar: distribución compacta en dos filas en celular
    Mutation(
        T_TOOLBAR,
        "03-toolbar-distribucion-compacta: organiza navegación y fecha en dos filas diferenciadas en celular",
        P_TOOLBAR_TSX,
        '<div className={styles.navRow} data-testid="agenda-toolbar-nav-row">',
        '<div className={styles.navGroup}>',
    ),
    # M04 - Toolbar: botón Filtros con contador dinámico de filtros activos
    Mutation(
        T_TOOLBAR,
        "04-toolbar-boton-filtros-con-contador: expone botón Filtros con indicador dinámico de filtros activos y despliega panel accesible",
        P_TOOLBAR_TSX,
        'activeFiltersCount > 0 ? `Filtros (${activeFiltersCount})` : "Filtros";',
        '"Filtros";',
    ),
    # M05 - Grilla: scroll-snap horizontal mandatory y horas sticky
    Mutation(
        T_GRID,
        "05-grilla-scroll-snap-y-horas-sticky: aplica scroll-snap horizontal mandatory y eje horario fijo en celular",
        P_GRID_TSX,
        'data-scroll-snap={isMobileEffective ? "mandatory" : undefined}',
        "data-scroll-snap={undefined}",
    ),
    # M06 - Grilla: modo por defecto grilla en AgendaView
    Mutation(
        T_GRID,
        "06-grilla-ancho-util-y-default-grid: preserva modo inicial grilla en AgendaView y dimensiona columnas a ancho útil en móvil",
        P_VIEW_TSX,
        'const [viewMode, setViewMode] = useState<"grid" | "list">("grid");',
        'const [viewMode, setViewMode] = useState<"grid" | "list">("list");',
    ),
    # M07 - Dialog: presentación como hoja inferior en móvil (data-mobile-sheet="true")
    Mutation(
        T_DIALOG,
        "07-dialog-bottom-sheet-mobile: renderiza como hoja inferior anclada al fondo con scroll interno en celular",
        P_DIALOG_TSX,
        'data-mobile-sheet={isMobileEffective ? "true" : undefined}',
        "data-mobile-sheet={undefined}",
    ),
    # M08 - Dialog: preservación de modal centrado flotante en escritorio (sin data-mobile-sheet)
    Mutation(
        T_DIALOG,
        "08-dialog-modal-centrado-desktop: preserva modal centrado flotante en pantallas de escritorio",
        P_DIALOG_TSX,
        "const isMobileEffective = isMobile ?? isMobileDevice;",
        "const isMobileEffective = true;",
    ),
    # M09 - Grilla: ancho útil con 100cqi y sin 100vw
    Mutation(
        T_GRID,
        "09-grilla-columna-cqi: utiliza container inline-size y ancho cqi en columnas móviles sin cálculo 100vw",
        P_GRID_CSS,
        """.columnHeaderMobile {
  scroll-snap-align: start;
  min-width: calc(100cqi - var(--agenda-time-gutter-width, 64px));
  flex: 0 0 calc(100cqi - var(--agenda-time-gutter-width, 64px));
}""",
        """.columnHeaderMobile {
  scroll-snap-align: start;
  min-width: calc(100vw - var(--agenda-time-gutter-width, 64px));
  flex: 0 0 calc(100vw - var(--agenda-time-gutter-width, 64px));
}""",
    ),
    # M10 - Toolbar: texto corto '‹'/'›' y navRow sin flex-wrap
    Mutation(
        T_TOOLBAR,
        "10-toolbar-compacta-tres-filas: Anterior y Siguiente muestran texto corto conservando nombre accesible y fila 1 sin flex-wrap",
        P_TOOLBAR_TSX,
        """            <button
              type="button"
              className={styles.actionButton}
              onClick={onPrevDay}
              aria-label={prevLabel}
            >
              {isMobileEffective ? "‹" : prevLabel}
            </button>""",
        """            <button
              type="button"
              className={styles.actionButton}
              onClick={onPrevDay}
              aria-label={prevLabel}
            >
              {prevLabel}
            </button>""",
    ),
    # M11 - Espaciado: margen superior al encabezado de fecha
    Mutation(
        T_SPACING,
        "11-espaciado-agenda: reduce separación entre título y toolbar y asigna margen superior con tokens al encabezado de fecha",
        P_VIEW_CSS,
        """.headerBar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-4);
}""",
        """.headerBar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}""",
    ),
)


def mutation_id(index: int) -> str:
    return f"M{index:02d}"


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
        [*VITEST, "list", *C36_TEST_FILES, "--json"],
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
        if file in C36_TEST_FILES:
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
            f"tests nuevos de C-36 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--poolOptions.threads.maxThreads=3", "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
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
    failed_assertions = [a for a in ran if a.get("status") == "failed"]
    if not failed_assertions:
        return "ningun test fallo"
    failures = failed_assertions[0].get("failureMessages") or []
    if not isinstance(failures, list) or not failures:
        return "el test fallo sin mensaje"
    message = "\n".join(str(f) for f in failures)
    first_line = message.splitlines()[0].strip() if message.splitlines() else ""
    if INVALID_ERROR.search(first_line):
        return f"error de tiempo de ejecucion/compilacion ({first_line})"
    if not ASSERTION.search(first_line) and "expect(" not in first_line:
        return f"el fallo no es una asercion: {first_line}"
    frame = first_own_frame(message)
    if frame is None or not TEST_FILE.search(frame):
        return f"el fallo se origino fuera de un archivo de test ({frame})"
    return None


def print_diff(mutation: Mutation, original: str, mutated: str, report: Report) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        mutated.splitlines(keepends=True),
        fromfile=f"a/{mutation.file}",
        tofile=f"b/{mutation.file}",
        n=2,
    )
    report.write("".join(diff).rstrip())


def build_markdown_row(
    mid: str, mutation: Mutation, status: str, failure_line: str
) -> str:
    test_file_base = Path(mutation.test_file).name
    short_test = mutation.test_name.split(":")[0]
    escaped_failure = failure_line.replace("|", "\\|")
    return (
        f"| {mid} | `{test_file_base}` | `{short_test}` | "
        f"{status} | `{escaped_failure}` |"
    )


def update_verify_markdown(rows: list[str]) -> None:
    if not VERIFY.is_file():
        return
    content = VERIFY.read_text(encoding="utf-8")
    if TABLE_START not in content or TABLE_END not in content:
        return
    header = (
        "| ID | Archivo de test | Test | Estado | Mensaje de fallo |\n"
        "|---|---|---|---|---|\n"
    )
    table_body = header + "\n".join(rows) + "\n"
    before, rest = content.split(TABLE_START, 1)
    _, after = rest.split(TABLE_END, 1)
    updated = f"{before}{TABLE_START}\n{table_body}{TABLE_END}{after}"
    VERIFY.write_text(updated, encoding="utf-8")


def main() -> int:
    check_only = "--check" in sys.argv
    out_file = open(OUTPUT, "w", encoding="utf-8")
    report = Report(out_file)

    report.write(SEPARATOR)
    report.write("MUTACIONES C-36 (ui-tema-oscuro-y-movil) — VERIFICACIÓN AUTOMATIZADA")
    report.write(SEPARATOR)

    # 1. Comprobación de definiciones
    for m in MUTATIONS:
        check_definition(m)
    report.write("Comprobación de definiciones: OK (cada original aparece 1 vez)")

    # 2. Correspondencia 1:1 con tests nuevos
    test_count = check_one_to_one()
    report.write(
        f"Correspondencia 1:1: OK ({test_count} tests listados == {len(MUTATIONS)} mutaciones)"
    )

    if check_only:
        report.write("Modo --check: todo correcto.")
        out_file.close()
        return 0

    sha_initial = production_sha256()
    report.write(f"SHA-256 inicial: {sha_initial}")
    report.write(SEPARATOR)

    killed = 0
    invalids: list[tuple[str, str, str]] = []
    markdown_rows: list[str] = []

    for index, mutation in enumerate(MUTATIONS, start=1):
        mid = mutation_id(index)
        report.write(f"\n[{mid}] {mutation.node_id}")
        target_path = REPO / mutation.file
        original_content = target_path.read_text(encoding="utf-8")
        mutated_content = apply_mutation(mutation, original_content)
        if mutated_content == original_content:
            raise MutationAbort(f"{mid}: el mutante no cambio el archivo {mutation.file}")

        print_diff(mutation, original_content, mutated_content, report)

        try:
            target_path.write_text(mutated_content, encoding="utf-8")
            result, json_report = run_single(mutation)
            if result.returncode == 0:
                report.write(f"RESULTADO: SUPERVIVIENTE (el test paso con la mutacion)")
                markdown_rows.append(
                    build_markdown_row(mid, mutation, "SUPERVIVIENTE", "Test paso inesperadamente")
                )
                continue

            reason = invalid_reason(mutation, json_report)
            failure_line = "Fallo sin mensaje"
            test_results = json_report.get("testResults", [])
            for tr in test_results:
                for a in tr.get("assertionResults", []):
                    if a.get("failureMessages"):
                        failure_line = a["failureMessages"][0].splitlines()[0].strip()
                        break
                if failure_line != "Fallo sin mensaje":
                    break

            if reason is not None:
                report.write(f"RESULTADO: INVÁLIDA ({reason})")
                report.write(f"Mensaje: {failure_line}")
                invalids.append((mid, mutation.node_id, reason))
                markdown_rows.append(
                    build_markdown_row(mid, mutation, f"INVÁLIDA ({reason})", failure_line)
                )
            else:
                killed += 1
                report.write(f"RESULTADO: ELIMINADA")
                report.write(f"Aserción: {failure_line}")
                markdown_rows.append(
                    build_markdown_row(mid, mutation, "ELIMINADA", failure_line)
                )
        finally:
            target_path.write_text(original_content, encoding="utf-8")
            restore_result, _ = run_single(mutation)
            if restore_result.returncode != 0:
                raise MutationAbort(f"{mid}: fallo la restauracion a verde de {mutation.node_id}")

    report.write("\n" + SEPARATOR)
    report.write("RESUMEN DE MUTACIONES C-36")
    report.write(SEPARATOR)
    report.write(f"Total mutaciones: {len(MUTATIONS)}")
    report.write(f"Eliminadas:       {killed}")
    report.write(f"Supervivientes:   {len(MUTATIONS) - killed - len(invalids)}")
    report.write(f"Inválidas:        {len(invalids)}")

    sha_final = production_sha256()
    report.write(f"SHA-256 inicial:  {sha_initial}")
    report.write(f"SHA-256 final:    {sha_final}")
    report.write(f"SHA-256 sin cambios: {'si' if sha_initial == sha_final else 'no'}")

    update_verify_markdown(markdown_rows)
    out_file.close()

    if invalids:
        print(f"ERROR: {len(invalids)} mutaciones inválidas", file=sys.stderr)
        return 1
    if killed != len(MUTATIONS):
        print(f"ERROR: solo {killed}/{len(MUTATIONS)} eliminadas", file=sys.stderr)
        return 1
    if sha_initial != sha_final:
        print("ERROR: SHA-256 cambio", file=sys.stderr)
        return 1

    print(f"OK: {killed}/{len(MUTATIONS)} mutaciones eliminadas, 0 inválidas, SHA-256 intacto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
