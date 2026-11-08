"""Verificacion por mutacion, reproducible, de los tests de C-28 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-28.py [--check]

Misma logica que mutaciones-C-27.py. Cada mutacion es
(archivo de test, nombre del test, archivo de produccion, texto_original, texto_mutado).
Hay UNA mutacion por cada test nuevo de C-28: antes de mutar se cuentan los tests
con `vitest list --json` y se exige una correspondencia uno a uno con los 15 tests nuevos.

Por cada mutacion: comprueba que el original aparezca exactamente una vez y que el
mutante cambie el archivo (respetando LF o CRLF), aplica la mutacion, corre Vitest solo
para ese test (`vitest run <archivo> -t <nombre>$`), restaura el archivo en un finally y
vuelve a correr el test, que tiene que volver a verde.

Una mutacion es INVALIDA si su test no la detecta con una afirmacion propia:
- el archivo de test no carga (error de import, de compilacion o SyntaxError);
- no se ejecuto exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro
  error que no sea AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no esta en un archivo *.test.ts(x) (una guarda
  del codigo de produccion que lanza).

Genera mutaciones-C-28.txt (salida cruda de Vitest incluida) y regenera la tabla de
verify-C-28.md. Termina con codigo 0 solo si todas las mutaciones hicieron fallar su
test, ninguna es INVALIDA y el SHA-256 del codigo de produccion no cambio.
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
OUTPUT = EVIDENCE / "mutaciones-C-28.txt"
VERIFY = EVIDENCE / "verify-C-28.md"
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

# --- archivos de test de C-28 con tests nuevos --------------------------------
T_AGENDA_TIME = "src/features/agenda/agendaTime.test.ts"
T_AGENDA_LAYOUT = "src/features/agenda/agendaLayout.test.ts"
T_USE_AGENDA = "src/features/agenda/useAgenda.test.tsx"
T_AGENDA_TOOLBAR = "src/features/agenda/AgendaToolbar.test.tsx"
T_AGENDA_STYLES = "src/features/agenda/agendaStyles.test.ts"
T_AGENDA_VIEW = "src/features/agenda/AgendaView.test.tsx"
T_AGENDA_PAGE = "src/features/agenda/AgendaPage.test.tsx"

C28_TEST_FILES = (
    T_AGENDA_TIME,
    T_AGENDA_LAYOUT,
    T_USE_AGENDA,
    T_AGENDA_TOOLBAR,
    T_AGENDA_STYLES,
    T_AGENDA_VIEW,
    T_AGENDA_PAGE,
)

# --- archivos de produccion (siempre dentro de frontend/src) -----------------
P_AGENDA_TIME = "frontend/src/features/agenda/agendaTime.ts"
P_AGENDA_LAYOUT = "frontend/src/features/agenda/agendaLayout.ts"
P_USE_AGENDA = "frontend/src/features/agenda/useAgenda.ts"
P_AGENDA_TOOLBAR = "frontend/src/features/agenda/AgendaToolbar.tsx"
P_AGENDA_GRID_CSS = "frontend/src/features/agenda/AgendaGrid.module.css"
P_AGENDA_GRID = "frontend/src/features/agenda/AgendaGrid.tsx"
P_AGENDA_VIEW = "frontend/src/features/agenda/AgendaView.tsx"
P_AGENDA_PAGE = "frontend/src/features/agenda/AgendaPage.tsx"
P_AGENDA_TABLE = "frontend/src/features/agenda/AgendaTable.tsx"
P_TOKENS_CSS = "frontend/src/shared/styles/tokens.css"


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
    # --- 1. Funciones puras de tiempo de semana ---
    Mutation(
        T_AGENDA_TIME,
        "weekRangeOf calcula lunes a domingo de la semana y getWeekDates genera los 7 días admitiendo cruce de mes y año",
        P_AGENDA_TIME,
        "  const sunday = addDays(monday, 6);",
        "  const sunday = addDays(monday, 5);",
    ),
    # --- 2. Layout y Hook de agenda ---
    Mutation(
        T_AGENDA_LAYOUT,
        "groupByDayForProfessional genera 7 columnas de lunes a domingo para un profesional, distribuye turnos, horarios y bloqueos en hora local y marca isToday",
        P_AGENDA_LAYOUT,
        "    const weekday = i + 1;",
        "    const weekday = i + 2;",
    ),
    Mutation(
        T_USE_AGENDA,
        "pide la semana completa en una sola llamada a GET /api/agenda cuando se especifica toDate",
        P_USE_AGENDA,
        "  const effectiveTo = toDate ?? date;",
        "  const effectiveTo = date;",
    ),
    # --- 3. Toolbar y navegación ---
    Mutation(
        T_AGENDA_TOOLBAR,
        "renderiza el selector de vista [ Día | Semana ], dispara onSelectView y adapta los botones de navegación a Semana anterior y Semana siguiente",
        P_AGENDA_TOOLBAR,
        '  const prevLabel = isWeekView ? "Semana anterior" : "Anterior";',
        '  const prevLabel = isWeekView ? "Anterior" : "Anterior";',
    ),
    # --- 4. Responsive y tag de Hoy (CSS estático) ---
    Mutation(
        T_AGENDA_STYLES,
        "verifica estáticamente los estilos de tablet y el tag de Hoy para la vista semanal (C-28)",
        P_AGENDA_GRID_CSS,
        "  border-radius: var(--radius-pill);",
        "  border-radius: var(--radius-md);",
    ),
    # --- 5. AgendaView semanal ---
    Mutation(
        T_AGENDA_VIEW,
        "renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles",
        P_AGENDA_GRID,
        '                aria-current={isToday ? "date" : undefined}',
        "                aria-current={undefined}",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "muestra grilla y aviso informativo cuando la semana está vacía sin turnos para la profesional",
        P_AGENDA_VIEW,
        "                : `No hay turnos esta semana para ${professionalName}`}",
        "                : `No hay turnos para ${professionalName}`}",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "muestra grilla y aviso de filtro cuando la semana está vacía con filtro de sillón activo",
        P_AGENDA_VIEW,
        '              {hasActiveChairFilter\n                ? "Sin turnos para este filtro"',
        '              {hasActiveChairFilter\n                ? "Sin turnos"',
    ),
    # --- 6. AgendaPage semanal ---
    Mutation(
        T_AGENDA_PAGE,
        "alterna de día a semana conservando fecha y filtros",
        P_AGENDA_TOOLBAR,
        '              onClick={() => onSelectView?.("week")}',
        '              onClick={() => onSelectView?.("day")}',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "alterna de semana a día conservando el día exacto de anclaje y filtros",
        P_AGENDA_PAGE,
        '  const handleSelectView = (nextView: "day" | "week") => {\n    setSearchParams(buildParams({ view: nextView }), { replace: false });\n  };',
        '  const handleSelectView = (nextView: "day" | "week") => {\n    void nextView;\n  };',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "un view desconocido o ausente cae a vista diaria con botón Día seleccionado",
        P_AGENDA_PAGE,
        '  const rawView = searchParams.get("view");\n  const view: "day" | "week" = rawView === "week" ? "week" : "day";',
        '  const rawView = searchParams.get("view");\n  const view: "day" | "week" = rawView === "invalido" ? "week" : "day";',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "preselecciona automáticamente por rol odontólogo su propio professionalId",
        P_AGENDA_PAGE,
        '  const initialProfessionalId =\n    explicitProfessionalId ??\n    (isWeek && user?.role === "odontologo" ? user.professionalId : null);',
        '  const initialProfessionalId =\n    explicitProfessionalId ??\n    (isWeek && user?.role === "odontologo" ? null : null);',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "preselecciona automáticamente por rol recepción al primer profesional activo en el orden del selector",
        P_AGENDA_PAGE,
        "      const sorted = [...state.professionals]\n        .filter((p) => p.active)\n        .sort(compareProfessionals);\n      const first = sorted[0];",
        "      const sorted = [...state.professionals]\n        .filter((p) => p.active)\n        .sort(compareProfessionals);\n      const first = sorted[1];",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "navegación semanal avanza y retrocede 7 días cruzando mes y año",
        P_AGENDA_PAGE,
        "        onPrevDay={() => navigateToDate(addDays(effectiveDate, isWeek ? -7 : -1))}\n        onNextDay={() => navigateToDate(addDays(effectiveDate, isWeek ? 7 : 1))}",
        "        onPrevDay={() => navigateToDate(addDays(effectiveDate, isWeek ? -1 : -1))}\n        onNextDay={() => navigateToDate(addDays(effectiveDate, isWeek ? 1 : 1))}",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "botón Hoy en vista semanal navega a la fecha actual del Clock",
        P_AGENDA_PAGE,
        "        onToday={() => navigateToDate(todayInTimeZone(clock.now(), state.timezone))}",
        "        onToday={() => navigateToDate(addDays(todayInTimeZone(clock.now(), state.timezone), 1))}",
    ),
    # --- 6. Revisión visual (H1 a H4) ---
    Mutation(
        T_AGENDA_PAGE,
        "preselección automática en vista semanal envía professionalId en la única llamada y el contador solo incluye sus turnos",
        P_USE_AGENDA,
        '    const isWeekly = toDate !== undefined && toDate !== date;\n    const needsPreselectedProfessional =\n      isWeekly && (professionalId === null || professionalId === "");',
        '    const isWeekly = toDate !== undefined && toDate !== date;\n    const needsPreselectedProfessional = false;',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "vista semanal muestra Agenda semanal como título, rango de semana en encabezado y Turnos de la semana en contador",
        P_AGENDA_PAGE,
        '    <PageShell title={isWeek ? "Agenda semanal" : "Agenda diaria"}>',
        '    <PageShell title={isWeek ? "Agenda diaria" : "Agenda diaria"}>',
    ),
    Mutation(
        T_AGENDA_VIEW,
        "ver como lista en vista semanal incluye caption de semana, columna Fecha y orden cronológico",
        P_AGENDA_TABLE,
        '  const isWeek = view === "week";',
        '  const isWeek = false;',
    ),
    Mutation(
        T_AGENDA_STYLES,
        "las columnas semanales usan token de ancho sin min-width de 220px y en tablet mantienen scroll horizontal",
        P_TOKENS_CSS,
        "  --agenda-week-column-min-width: 140px;",
        "  --agenda-week-min-width: 140px;",
    ),
    Mutation(
        T_AGENDA_STYLES,
        "en carriles divididos y tarjetas apiladas la etiqueta de estado no desborda la tarjeta con max-width 100%, overflow hidden y text-overflow ellipsis (H5)",
        P_AGENDA_GRID_CSS,
        ".cardCompactStacked .statusBadgeWrap > span {\n  font-size: var(--font-size-xs);\n  padding: 1px var(--space-1);\n  max-width: 100%;",
        ".cardCompactStacked .statusBadgeWrap > span {\n  font-size: var(--font-size-xs);\n  padding: 1px var(--space-1);\n  max-width: 200%;",
    ),
    Mutation(
        T_AGENDA_STYLES,
        "en columnas menores a 260 px las tarjetas no compactas usan etiqueta reducida y líneas con ellipsis en una línea (H6)",
        P_AGENDA_GRID_CSS,
        "  .cardTopRow > span:last-child {\n    font-size: var(--font-size-xs);",
        "  .cardTopRow > span:last-child {\n    font-size: var(--font-size-sm);",
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO):
        self._stream = stream

    def write(self, text: str) -> None:
        self._stream.write(text + "\n")
        self._stream.flush()


def production_files() -> list[Path]:
    seen: set[str] = set()
    files: list[Path] = []
    for mutation in MUTATIONS:
        if mutation.file not in seen:
            seen.add(mutation.file)
            files.append(REPO / mutation.file)
    return files


def production_sha256() -> str:
    hasher = hashlib.sha256()
    for path in sorted(production_files()):
        hasher.update(path.as_posix().encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(path.read_bytes())
        hasher.update(b"\x00")
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
        cwd=FRONTEND, capture_output=True, encoding="utf-8", errors="replace",
        env=vitest_env(), timeout=TIMEOUT_SECONDS, check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    expected_names = {m.test_name for m in MUTATIONS}
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
        if file in C28_TEST_FILES and name in expected_names:
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
            f"tests nuevos de C-28 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
            cwd=FRONTEND, capture_output=True, encoding="utf-8", errors="replace",
            env=vitest_env(), timeout=TIMEOUT_SECONDS, check=False,
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


def run_mutation(mutation: Mutation, index: int, report: Report) -> tuple[bool, str | None, str, str]:
    target = REPO / mutation.file
    original_bytes = target.read_bytes()
    original_content = original_bytes.decode("utf-8")
    mutated_content = apply_mutation(mutation, original_content)
    if mutated_content == original_content:
        raise MutationAbort(f"{mutation.node_id}: la mutacion no cambia {mutation.file}")

    diff_lines = list(
        difflib.unified_diff(
            original_content.replace("\r\n", "\n").splitlines(keepends=True),
            mutated_content.replace("\r\n", "\n").splitlines(keepends=True),
            fromfile=f"a/{mutation.file}",
            tofile=f"b/{mutation.file}",
            n=1,
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
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
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
            f"una por cada uno de los {total_tests} tests de C-28."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-28.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-28 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C28_TEST_FILES))
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
