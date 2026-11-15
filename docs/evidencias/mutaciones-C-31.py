"""Verificación por mutación, reproducible, de los tests nuevos de C-31 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-31.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación (M01-M23) por cada escenario testeable nuevo de C-31: antes de mutar se cuentan los tests
con `vitest list --json` y se exige una correspondencia uno a uno con los 23 tests nuevos.

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-31.txt (salida cruda de Vitest incluida) y actualiza la tabla de verify-C-31.md.
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
OUTPUT = EVIDENCE / "mutaciones-C-31.txt"
VERIFY = EVIDENCE / "verify-C-31.md"
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

# --- Archivos de test de C-31 ---
T_PAGE = "src/features/agenda/AgendaPage.porSillon.test.tsx"
T_TOOLBAR = "src/features/agenda/AgendaToolbar.chair.test.tsx"
T_VIEW = "src/features/agenda/AgendaView.chair.test.tsx"
T_LAYOUT = "src/features/agenda/agendaChairLayout.test.ts"
T_STYLES = "src/features/agenda/agendaChairStyles.test.ts"

C31_TEST_FILES = (
    T_PAGE,
    T_TOOLBAR,
    T_VIEW,
    T_LAYOUT,
    T_STYLES,
)

# --- Archivos de producción modificados o creados en C-31 ---
P_PAGE_TSX = "frontend/src/features/agenda/AgendaPage.tsx"
P_VIEW_TSX = "frontend/src/features/agenda/AgendaView.tsx"
P_GRID_TSX = "frontend/src/features/agenda/AgendaGrid.tsx"
P_GRID_CSS = "frontend/src/features/agenda/AgendaGrid.module.css"
P_TOOLBAR_TSX = "frontend/src/features/agenda/AgendaToolbar.tsx"
P_TABLE_TSX = "frontend/src/features/agenda/AgendaTable.tsx"
P_LAYOUT_TS = "frontend/src/features/agenda/agendaChairLayout.ts"
P_TOKENS = "frontend/src/shared/styles/tokens.css"

PRODUCTION_FILES = (
    P_PAGE_TSX,
    P_VIEW_TSX,
    P_GRID_TSX,
    P_GRID_CSS,
    P_TOOLBAR_TSX,
    P_TABLE_TSX,
    P_LAYOUT_TS,
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
    # M01 - Activar Sillones conserva fecha y filtros
    Mutation(
        T_PAGE,
        "Activar Sillones conserva fecha y filtros: activar Sillones conserva fecha y filtros",
        P_PAGE_TSX,
        '    } else if (nextView === "chair") {\n      params.set("view", "chair");\n    }',
        '    } else if (nextView === "chair") {\n      // params.set("view", "chair");\n    }',
    ),
    # M02 - Un view desconocido sigue cayendo a Día
    Mutation(
        T_PAGE,
        "Un view desconocido sigue cayendo a Día: view desconocido cae a Día",
        P_PAGE_TSX,
        '  const view: "day" | "week" | "chair" =\n    rawView === "week"\n      ? "week"\n      : rawView === "chair" && !isOdontologo\n        ? "chair"\n        : "day";',
        '  const view: "day" | "week" | "chair" =\n    rawView === "week"\n      ? "week"\n      : !isOdontologo\n        ? "chair"\n        : "day";',
    ),
    # M03 - Turnos de distintos profesionales en la misma columna
    Mutation(
        T_VIEW,
        "Turnos de distintos profesionales en la misma columna: dos profesionales en una columna de sillón",
        P_VIEW_TSX,
        "  const columns =\n    isChairView\n      ? groupByChair({",
        "  const columns =\n    false\n      ? groupByChair({",
    ),
    # M04 - Sillón sin turnos
    Mutation(
        T_VIEW,
        "Sillón sin turnos: sillón sin turnos muestra Libre y Fuera de horario",
        P_LAYOUT_TS,
        "  return chairList.map((chair) => {",
        "  return chairList.filter((chair) => appointments.some((a) => a.chairId === chair.id)).map((chair) => {",
    ),
    # M05 - Filtro de un solo sillón
    Mutation(
        T_PAGE,
        "Filtro de un solo sillón: chairId deja una sola columna",
        P_LAYOUT_TS,
        '  if (filterChairId !== null && filterChairId !== "") {\n    chairList = chairList.filter((c) => c.id === filterChairId);\n  }',
        '  if (false && filterChairId !== null && filterChairId !== "") {\n    chairList = chairList.filter((c) => c.id === filterChairId);\n  }',
    ),
    # M06 - Sillón inactivo visible
    Mutation(
        T_LAYOUT,
        "Sillón inactivo visible: sillón inactivo con sufijo (inactivo)",
        P_LAYOUT_TS,
        "      displayLabel: chair.active ? chair.name : `${chair.name} (inactivo)`,",
        "      displayLabel: chair.name,",
    ),
    # M07 - Hueco libre entre dos turnos
    Mutation(
        T_LAYOUT,
        "Hueco libre entre dos turnos: hueco 10:30–11:00 entre dos turnos",
        P_LAYOUT_TS,
        "    for (const occ of mergedOccupied) {",
        "    for (const occ of [] as MinuteRange[]) {",
    ),
    # M08 - Un cancelado no ocupa el sillón
    Mutation(
        T_LAYOUT,
        "Un cancelado no ocupa el sillón: cancelado libera el tramo",
        P_LAYOUT_TS,
        '    if (\n      appt.status !== "reservado" &&\n      appt.status !== "confirmado" &&\n      appt.status !== "atendido"\n    ) {\n      continue;\n    }',
        '    if (\n      appt.status !== "reservado" &&\n      appt.status !== "confirmado" &&\n      appt.status !== "atendido" &&\n      appt.status !== "cancelado"\n    ) {\n      continue;\n    }',
    ),
    # M09 - La disponibilidad no depende sólo del color
    Mutation(
        T_STYLES,
        "La disponibilidad no depende sólo del color: bandas con texto y sin HEX",
        P_GRID_TSX,
        "                      <span>{slot.label}</span>",
        "                      {/* slot label removed */}",
    ),
    # M10 - Eje con la unión de horarios del día
    Mutation(
        T_LAYOUT,
        "Eje con la unión de horarios del día: eje 09:00–19:00 y gap 13:00–15:00",
        P_LAYOUT_TS,
        "    if (end > start) {\n      parsedRanges.push({ startMinute: start, endMinute: end });\n    }",
        "    if (end > start) {\n      parsedRanges.push({ startMinute: start, endMinute: end });\n      break;\n    }",
    ),
    # M11 - Día sin horarios de atención
    Mutation(
        T_LAYOUT,
        "Día sin horarios de atención: sin horarios usa 08:00–20:00 sin Libre",
        P_LAYOUT_TS,
        "    const fallbackStart = AGENDA_DEFAULT_START_MINUTE; // 480 (08:00)",
        "    const fallbackStart = 540;",
    ),
    # M12 - Día por defecto desde el Clock
    Mutation(
        T_PAGE,
        "Día por defecto desde el Clock: view=chair sin date usa el Clock",
        P_PAGE_TSX,
        "  const fallbackToday = todayInTimeZone(clock.now(), DEFAULT_AGENDA_TIMEZONE);",
        '  const fallbackToday = "2099-01-01";',
    ),
    # M13 - Navegación de un día
    Mutation(
        T_PAGE,
        "Navegación de un día: Siguiente suma un día en view=chair",
        P_PAGE_TSX,
        "        onNextDay={() => navigateToDate(addDays(effectiveDate, isWeek ? 7 : 1))}",
        "        onNextDay={() => navigateToDate(addDays(effectiveDate, 7))}",
    ),
    # M14 - Clic en la tarjeta abre el detalle
    Mutation(
        T_VIEW,
        "Clic en la tarjeta abre el detalle: clic en tarjeta abre AppointmentDetailDialog",
        P_VIEW_TSX,
        "            showProfessional={isChairView}\n            onSelectAppointment={onSelectAppointment}",
        "            showProfessional={isChairView}\n            onSelectAppointment={isChairView ? undefined : onSelectAppointment}",
    ),
    # M15 - Nombre accesible completo en la tarjeta
    Mutation(
        T_VIEW,
        "Nombre accesible completo en la tarjeta: aria-label incluye hora, paciente, profesional, sillón, prestación y estado",
        P_GRID_TSX,
        "                  const cardAriaLabel = `${timeLabel}, ${appt.patientName}, ${appt.serviceName}, ${appt.professionalName}, ${appt.chairName}, ${statusLabel}`;",
        "                  const cardAriaLabel = `${timeLabel}, ${appt.patientName}, ${appt.serviceName}, ${appt.chairName}, ${statusLabel}`;",
    ),
    # M16 - Recepción y administración ven el control
    Mutation(
        T_TOOLBAR,
        "Recepción y administración ven el control: Sillones visible para recepcion y administrador",
        P_TOOLBAR_TSX,
        '  const canViewChairs = userRole === "recepcion" || userRole === "administrador";',
        "  const canViewChairs = false;",
    ),
    # M17 - Odontólogo sin acceso
    Mutation(
        T_PAGE,
        "Odontólogo sin acceso: odontólogo con view=chair cae a Día",
        P_PAGE_TSX,
        '    const needsChairViewNorm = rawView === "chair" && isOdontologo;',
        "    const needsChairViewNorm = false;",
    ),
    # M18 - El filtro de sillón reduce las columnas
    Mutation(
        T_PAGE,
        "El filtro de sillón reduce las columnas: aplicar el filtro Sillón 2 actualiza la URL y reduce a una columna",
        P_PAGE_TSX,
        "  const handleSelectChair = (nextChairId: string | null) => {\n    setSearchParams(buildParams({ chairId: nextChairId }), { replace: false });\n  };",
        "  const handleSelectChair = (_nextChairId: string | null) => {\n    setSearchParams(buildParams({ chairId: null }), { replace: false });\n  };",
    ),
    # M19 - El filtro de profesional recalcula los horarios
    Mutation(
        T_LAYOUT,
        "El filtro de profesional recalcula los horarios: professionalId de Sosa deja unión 09:00–13:00",
        P_LAYOUT_TS,
        '    if (professionalId !== null && professionalId !== undefined && professionalId !== "") {\n      return wh.professionalId === professionalId;\n    }',
        '    if (false && professionalId !== null && professionalId !== undefined && professionalId !== "") {\n      return wh.professionalId === professionalId;\n    }',
    ),
    # M20 - La ayuda del filtro de sillón se adapta
    Mutation(
        T_TOOLBAR,
        "La ayuda del filtro de sillón se adapta: en view=chair muestra CHAIR_VIEW_HELP_TEXT",
        P_TOOLBAR_TSX,
        "      {hasChairFilter && isChairView && <p className={styles.helpText}>{CHAIR_VIEW_HELP_TEXT}</p>}",
        "      {hasChairFilter && isChairView && <p className={styles.helpText}>{CHAIR_FILTER_HELP_TEXT}</p>}",
    ),
    # M21 - La lista sigue disponible
    Mutation(
        T_VIEW,
        "La lista sigue disponible: Ver como lista con columna Sillón",
        P_VIEW_TSX,
        '          <button\n            type="button"\n            className={styles.toggleButton}\n            aria-pressed={viewMode === "list"}\n            onClick={() =>\n              setViewMode((current) => (current === "grid" ? "list" : "grid"))\n            }\n          >\n            Ver como lista\n          </button>',
        '          {!isChairView && (\n            <button\n              type="button"\n              className={styles.toggleButton}\n              aria-pressed={viewMode === "list"}\n              onClick={() =>\n                setViewMode((current) => (current === "grid" ? "list" : "grid"))\n              }\n            >\n              Ver como lista\n            </button>\n          )}',
    ),
    # M22 - Un día sin turnos conserva la grilla
    Mutation(
        T_VIEW,
        "Un día sin turnos conserva la grilla: día sin turnos mantiene grilla y aviso",
        P_VIEW_TSX,
        '      ) : !isWeekView && !isChairView && agenda.appointments.length === 0 && !hasActiveFilter ? (\n        <EmptyState\n          title="No hay turnos para este día"\n          description="No se registraron turnos en la agenda para esta fecha."\n        />',
        '      ) : !isWeekView && agenda.appointments.length === 0 && !hasActiveFilter ? (\n        <EmptyState\n          title="No hay turnos para este día"\n          description="No se registraron turnos en la agenda para esta fecha."\n        />',
    ),
    # M23 - Catálogo de sillones vacío
    Mutation(
        T_VIEW,
        "Catálogo de sillones vacío: sin sillones muestra No hay sillones configurados",
        P_VIEW_TSX,
        "      {isChairView && (!chairs || chairs.length === 0) ? (\n        <EmptyState\n          title=\"No hay sillones configurados\"\n          description=\"No se encontraron sillones en el catálogo.\"\n        />",
        "      {false ? (\n        <EmptyState\n          title=\"No hay sillones configurados\"\n          description=\"No se encontraron sillones en el catálogo.\"\n        />",
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
        [*VITEST, "list", *C31_TEST_FILES, "--json"],
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
        if file in C31_TEST_FILES:
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
            f"tests nuevos de C-31 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
    pattern = re.sub(r"([()[\]{}*+?^$|.\\])", r"\\\1", mutation.test_name) + "$"
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
    new_table = f"{TABLE_START}\n{header}" + "\n".join(rows) + f"\n{TABLE_END}"
    pattern = re.compile(
        re.escape(TABLE_START) + r".*?" + re.escape(TABLE_END), re.DOTALL
    )
    VERIFY.write_text(pattern.sub(new_table, content), encoding="utf-8")


def run_all(report: Report) -> int:
    initial_sha = production_sha256()
    report.write(SEPARATOR)
    report.write("VERIFICACION POR MUTACION DE C-31 (MODO SILLONES)")
    report.write(f"SHA-256 inicial de archivos de produccion: {initial_sha}")
    report.write(SEPARATOR)

    for mutation in MUTATIONS:
        check_definition(mutation)

    test_count = check_one_to_one()
    report.write(
        f"Correspondencia 1:1 verificada: {test_count} tests nuevos vs {len(MUTATIONS)} mutaciones."
    )
    report.write(SEPARATOR)

    killed = 0
    invalid = 0
    markdown_rows: list[str] = []

    for idx, mutation in enumerate(MUTATIONS, start=1):
        mid = mutation_id(idx)
        report.write(f"[{mid}] {mutation.node_id}")
        report.write(f"    Archivo: {mutation.file}")

        target_path = REPO / mutation.file
        original_content = target_path.read_text(encoding="utf-8")
        mutated_content = apply_mutation(mutation, original_content)
        if mutated_content == original_content:
            report.write("    FALLO: el mutante no cambio el archivo.")
            return 2

        print_diff(mutation, original_content, mutated_content, report)

        target_path.write_text(mutated_content, encoding="utf-8")
        try:
            res_mutated, rep_mutated = run_single(mutation)
        finally:
            target_path.write_text(original_content, encoding="utf-8")

        res_restored, rep_restored = run_single(mutation)

        reason = invalid_reason(mutation, rep_mutated)
        if reason:
            invalid += 1
            status = f"INVALIDA ({reason})"
            first_fail = (
                res_mutated.stderr.splitlines()[0]
                if res_mutated.stderr.splitlines()
                else "sin stderr"
            )
        else:
            killed += 1
            status = "Matada"
            assertions = [
                a
                for f in rep_mutated.get("testResults", [])
                for a in f.get("assertionResults", [])
                if a.get("status") == "failed"
            ]
            first_msg = (
                assertions[0]["failureMessages"][0]
                if assertions and assertions[0].get("failureMessages")
                else "fallo esperado"
            )
            first_fail = first_msg.splitlines()[0].strip()

        restored_ok = res_restored.returncode == 0
        report.write(f"    Estado: {status}")
        report.write(f"    Fallo:  {first_fail}")
        report.write(
            f"    Restaurado a verde: {'si' if restored_ok else 'NO (PELIGRO)'}"
        )
        report.write("-" * 80)

        markdown_rows.append(build_markdown_row(mid, mutation, status, first_fail))

        if not restored_ok:
            report.write("ABORTANDO: el archivo restaurado no volvio a verde.")
            return 3

    final_sha = production_sha256()
    sha_ok = final_sha == initial_sha

    report.write(SEPARATOR)
    report.write("RESUMEN DE MUTACIONES")
    report.write(f"Mutaciones totales:    {len(MUTATIONS)}")
    report.write(f"Matadas por asercion:  {killed}")
    report.write(f"Invalidas:             {invalid}")
    report.write(f"SHA-256 inicial:       {initial_sha}")
    report.write(f"SHA-256 final:         {final_sha}")
    report.write(f"SHA-256 sin cambios:   {'si' if sha_ok else 'NO'}")
    report.write(SEPARATOR)

    update_verify_markdown(markdown_rows)

    if killed == len(MUTATIONS) and invalid == 0 and sha_ok:
        report.write("EXITO: todas las mutaciones fueron detectadas limpiamente.")
        return 0
    report.write("FALLO: se detectaron anomalias en la suite de mutacion.")
    return 1


def main() -> int:
    if "--check" in sys.argv:
        for m in MUTATIONS:
            check_definition(m)
        count = check_one_to_one()
        print(f"OK: {count} tests nuevos coinciden 1:1 con las {len(MUTATIONS)} mutaciones.")
        return 0

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rep = Report(sys.stdout)
    code = run_all(rep)
    return code


if __name__ == "__main__":
    sys.exit(main())
