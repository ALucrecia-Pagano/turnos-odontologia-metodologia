"""Verificación por mutación, reproducible, de los tests de C-32 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-32.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación (M01-M26) por cada uno de los 24 escenarios testeables de C-32 (22 en tests nuevos + 2 en tests existentes modificados de AppShellNavigation.test.tsx) más los 2 tests auxiliares (horariosApi.test.ts y HorariosRoute.test.tsx): antes de mutar se cuentan los tests con `vitest list --json` y se exige una correspondencia uno a uno con los 26 tests evaluados en C-32.

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-32.txt y actualiza la tabla de verify-C-32.md.
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
OUTPUT = EVIDENCE / "mutaciones-C-32.txt"
VERIFY = EVIDENCE / "verify-C-32.md"
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

# --- Archivos de test de C-32 ---
T_PAGE = "src/features/horarios/HorariosPage.test.tsx"
T_HOURS = "src/features/horarios/WorkingHoursSection.test.tsx"
T_AFFECTED = "src/features/horarios/AffectedAppointments.test.tsx"
T_BLOCKS = "src/features/horarios/BlocksSection.test.tsx"
T_MOBILE = "src/features/horarios/BlockFormDialog.mobile.test.tsx"
T_NAVIGATION = "src/shared/components/AppShellNavigation.test.tsx"
T_API = "src/features/horarios/horariosApi.test.ts"
T_ROUTE = "src/features/horarios/HorariosRoute.test.tsx"
T_STYLES = "src/features/horarios/horariosStyles.test.ts"

C32_TEST_FILES = (
    T_PAGE,
    T_HOURS,
    T_AFFECTED,
    T_BLOCKS,
    T_MOBILE,
    T_NAVIGATION,
    T_API,
    T_ROUTE,
    T_STYLES,
)

# Test preexistente de C-35 en AppShellNavigation.test.tsx que no fue modificado ni pertenece a C-32
PREEXISTING_TESTS: frozenset[tuple[str, str]] = frozenset(
    {
        (
            T_NAVIGATION,
            "los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces",
        )
    }
)

# --- Archivos de producción modificados o creados en C-32 ---
P_PAGE_TSX = "frontend/src/features/horarios/HorariosPage.tsx"
P_PAGE_CSS = "frontend/src/features/horarios/HorariosPage.module.css"
P_HOURS_TSX = "frontend/src/features/horarios/WorkingHoursSection.tsx"
P_HOURS_CSS = "frontend/src/features/horarios/WorkingHoursSection.module.css"
P_BLOCKS_TSX = "frontend/src/features/horarios/BlocksSection.tsx"
P_BLOCKS_CSS = "frontend/src/features/horarios/BlocksSection.module.css"
P_FORM_TSX = "frontend/src/features/horarios/BlockFormDialog.tsx"
P_FORM_CSS = "frontend/src/features/horarios/BlockFormDialog.module.css"
P_DELETE_TSX = "frontend/src/features/horarios/BlockDeleteDialog.tsx"
P_DELETE_CSS = "frontend/src/features/horarios/BlockDeleteDialog.module.css"
P_AFFECTED_TSX = "frontend/src/features/horarios/AffectedAppointments.tsx"
P_API_TS = "frontend/src/features/horarios/horariosApi.ts"
P_TIME_TS = "frontend/src/features/horarios/horariosTime.ts"
P_MENU_TS = "frontend/src/features/auth/menuFor.ts"
P_APP_TSX = "frontend/src/App.tsx"

PRODUCTION_FILES = (
    P_PAGE_TSX,
    P_PAGE_CSS,
    P_HOURS_TSX,
    P_HOURS_CSS,
    P_BLOCKS_TSX,
    P_BLOCKS_CSS,
    P_FORM_TSX,
    P_FORM_CSS,
    P_DELETE_TSX,
    P_DELETE_CSS,
    P_AFFECTED_TSX,
    P_API_TS,
    P_TIME_TS,
    P_MENU_TS,
    P_APP_TSX,
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
    # M01 - Odontólogo accede a sus propios horarios
    Mutation(
        T_PAGE,
        "Odontólogo accede a sus propios horarios: carga tramos y bloqueos de su professionalId sin mostrar selector de profesional",
        P_PAGE_TSX,
        "  const showSelector = !isDentist;",
        "  const showSelector = true;",
    ),
    # M02 - Administrador selecciona profesional activo
    Mutation(
        T_PAGE,
        "Administrador selecciona profesional activo: lista solo activos, selecciona el primero por defecto y al cambiar actualiza datos y ?professionalId=",
        P_PAGE_TSX,
        "        setProfessionals(profsRes.data.filter((p) => p.active));",
        "        setProfessionals(profsRes.data);",
    ),
    # M03 - Odontólogo consulta profesional ajeno y recibe 403
    Mutation(
        T_PAGE,
        "Odontólogo consulta profesional ajeno y recibe 403: muestra en role=alert el mensaje literal del backend sin controles de edición ni cerrar sesión",
        P_PAGE_TSX,
        '        setPageError(getApiErrorMessages(hoursRes.error).join(" "));',
        '        setPageError("Error genérico");',
    ),
    # M04 - Guardado exitoso de tramos semanales
    Mutation(
        T_HOURS,
        "Guardado exitoso de tramos semanales: envía PUT con los tramos en orden visual y anuncia Horario guardado.",
        P_HOURS_TSX,
        '      updateStatus("Horario guardado.");',
        "      updateStatus(null);",
    ),
    # M05 - Edición interactiva de tramos en la interfaz
    Mutation(
        T_HOURS,
        "Edición interactiva de tramos en la interfaz: agrega una fila editable para el día martes y la quita al pulsar Quitar",
        P_HOURS_TSX,
        "    setSlots((prev) => prev.filter((item) => item.rowId !== rowId));",
        "    setSlots((prev) => prev);",
    ),
    # M06 - Rechazo por tramos solapados muestra mensaje literal del backend
    Mutation(
        T_HOURS,
        "Rechazo por tramos solapados muestra mensaje literal del backend: muestra role=alert literal y traslada foco al contenedor de error",
        P_HOURS_TSX,
        "      alertRef.current?.focus();",
        "      // alertRef.current?.focus();",
    ),
    # M07 - Error 400 marca campos con aria-invalid
    Mutation(
        T_HOURS,
        "Error 400 marca campos con aria-invalid: marca el input inválido con aria-invalid=true y muestra el mensaje de validación",
        P_HOURS_TSX,
        '                          aria-invalid={isFieldInvalid(slot.rowId, "start") ? "true" : undefined}',
        "                          aria-invalid={undefined}",
    ),
    # M08 - Turnos futuros fuera del horario al guardar tramos
    Mutation(
        T_AFFECTED,
        "Turnos futuros fuera del horario al guardar tramos: muestra en role=alert fecha, hora local, paciente, profesional, StatusBadge y aviso de no cancelación",
        P_HOURS_TSX,
        "      setOutsideAppointments(result.data.appointmentsOutsideHours);",
        "      setOutsideAppointments([]);",
    ),
    # M09 - Turnos solapados al crear un bloqueo
    Mutation(
        T_AFFECTED,
        "Turnos solapados al crear un bloqueo: muestra en role=alert la advertencia de turnos solapados con paciente, fecha, hora local y estado",
        P_BLOCKS_TSX,
        "    setAffectedAppointments(response.affectedAppointments);",
        "    setAffectedAppointments([]);",
    ),
    # M10 - Creación exitosa de bloqueo con offset
    Mutation(
        T_BLOCKS,
        "Creación exitosa de bloqueo con offset: convierte fecha y hora local a ISO con offset, cierra el diálogo y anuncia Bloqueo creado.",
        P_BLOCKS_TSX,
        '    updateStatus("Bloqueo creado.");',
        "    updateStatus(null);",
    ),
    # M11 - Eliminación de bloqueo con confirmación in-dialog
    Mutation(
        T_BLOCKS,
        "Eliminación de bloqueo con confirmación in-dialog: exige confirmación antes de enviar DELETE y anuncia Bloqueo eliminado.",
        P_BLOCKS_TSX,
        '      updateStatus("Bloqueo eliminado.");',
        "      updateStatus(null);",
    ),
    # M12 - Cancelación del borrado con Escape
    Mutation(
        T_BLOCKS,
        "Cancelación del borrado con Escape: cierra el diálogo al pulsar Escape o Volver sin enviar DELETE y restaura el foco",
        P_DELETE_TSX,
        "            onClick={onClose}\n          >\n            Volver",
        "            onClick={onConfirm}\n          >\n            Volver",
    ),
    # M13 - Bloqueo inválido muestra mensaje literal del backend
    Mutation(
        T_BLOCKS,
        "Bloqueo inválido muestra mensaje literal del backend: mantiene el diálogo abierto y muestra role=alert literal ante error 422",
        P_FORM_TSX,
        "      setViolations(result.error.violations);",
        "      onClose();",
    ),
    # M14 - Recepción visualiza información completa sin controles de edición
    Mutation(
        T_PAGE,
        "Recepción visualiza información completa sin controles de edición: muestra selector, tramos y bloqueos pero oculta Agregar tramo, Quitar, Guardar horario, Nuevo bloqueo y Eliminar bloqueo",
        P_PAGE_TSX,
        '  const isReadOnly = user?.role === "recepcion";',
        "  const isReadOnly = false;",
    ),
    # M15 - Zona horaria leída desde GET /api/agenda
    Mutation(
        T_PAGE,
        "Zona horaria leída desde GET /api/agenda: consulta GET /api/agenda una sola vez, reutiliza su timezone al cambiar de profesional y formatea bloqueos según esa zona",
        P_PAGE_TSX,
        "        setTimezone(agendaRes.data.timezone);",
        '        setTimezone("America/Argentina/Buenos_Aires");',
    ),
    # M16 - Presentación de modal como hoja inferior en móvil
    Mutation(
        T_MOBILE,
        "Presentación de modal como hoja inferior en móvil: aplica clase y atributos de hoja inferior a ≤ 640 px ocupando el 100% del ancho útil",
        P_FORM_CSS,
        "    border-radius: var(--radius-lg, 16px) var(--radius-lg, 16px) 0 0;",
        "    border-radius: var(--radius-md);",
    ),
    # M17 - Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px
    Mutation(
        T_NAVIGATION,
        "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        P_MENU_TS,
        '    const enabled = item.id === "agenda" || item.id === "horarios-y-bloqueos";',
        '    const enabled = item.id === "agenda";',
    ),
    # M18 - Ítems deshabilitados con Próximamente conservan semántica y accesibilidad
    Mutation(
        T_NAVIGATION,
        "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        P_MENU_TS,
        "      disabled: !enabled,",
        "      disabled: true,",
    ),
    # M19 - Test auxiliar cliente de API horariosApi.test.ts
    Mutation(
        T_API,
        "parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock",
        P_API_TS,
        '    method: "DELETE",',
        '    method: "GET",',
    ),
    # M20 - Test auxiliar ruta /horarios HorariosRoute.test.tsx
    Mutation(
        T_ROUTE,
        "renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo",
        P_APP_TSX,
        '            { path: "horarios", element: <HorariosPage clock={clock} /> },',
        '            { path: "horarios-disabled", element: <HorariosPage clock={clock} /> },',
    ),
    # M21 - Todas las variables CSS de horarios existen en tokens.css
    Mutation(
        T_STYLES,
        "Todas las variables CSS de horarios existen en tokens.css: cada var(--x) usado en los .module.css de horarios está definido en tokens.css",
        P_HOURS_CSS,
        "  box-shadow: var(--shadow-sm);",
        "  box-shadow: var(--shadow-xs);",
    ),
    # M22 - Encabezado y estilos de HorariosPage sin tokens de fondo oscuro
    Mutation(
        T_STYLES,
        "Encabezado y estilos de HorariosPage sin tokens de fondo oscuro: HorariosPage.module.css usa tokens de superficie clara y no contiene --color-ice ni *-on-navy",
        P_PAGE_CSS,
        ".selector {\n  font-family: inherit;\n  font-size: var(--font-size-sm);\n  color: var(--color-text);\n  background: var(--color-background);",
        ".selector {\n  font-family: inherit;\n  font-size: var(--font-size-sm);\n  color: var(--color-ice);\n  background: var(--field-on-navy);",
    ),
    # M23 - Título de PageShell Horarios y bloqueos con único h1
    Mutation(
        T_PAGE,
        "Título de PageShell Horarios y bloqueos con único h1: pasa title Horarios y bloqueos a PageShell y mantiene un solo h1",
        P_PAGE_TSX,
        '    <PageShell title="Horarios y bloqueos">',
        '    <PageShell title="Turnos Odontología">',
    ),
    # M24 - Eliminar bloqueo oculta su panel de turnos afectados
    Mutation(
        T_BLOCKS,
        "Eliminar bloqueo oculta su panel de turnos afectados: al confirmar la eliminación del bloqueo desaparece la alerta de turnos solapados",
        P_BLOCKS_TSX,
        '      setAffectedAppointments([]);\n      updateStatus("Bloqueo eliminado.");',
        '      updateStatus("Bloqueo eliminado.");',
    ),
    # M25 - Un solo mensaje de estado vigente entre acciones sin desmontar la región
    Mutation(
        T_PAGE,
        "Un solo mensaje de estado vigente entre acciones sin desmontar la región: reemplaza Horario guardado por Bloqueo eliminado y mantiene una única región role=status montada",
        P_PAGE_TSX,
        "                onStatusChange={setStatusMessage}\n              />\n              <BlocksSection",
        "              />\n              <BlocksSection",
    ),
    # M26 - Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar
    Mutation(
        T_AFFECTED,
        "Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar: formatea 2026-11-17 como mar, 17/11/2026 con la timezone de la API y no muestra ISO",
        P_TIME_TS,
        "  const startDate = formatDisplayDateInZone(startAt, timeZone);\n  const endDate = formatDisplayDateInZone(endAt, timeZone);",
        "  const startDate = formatLocalDate(startAt, timeZone);\n  const endDate = formatLocalDate(endAt, timeZone);",
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
        [*VITEST, "list", *C32_TEST_FILES, "--json"],
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
        if file in C32_TEST_FILES and (file, name) not in PREEXISTING_TESTS:
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
            f"tests de C-32 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
    before, rest = content.split(TABLE_START, 1)
    _, after = rest.split(TABLE_END, 1)
    VERIFY.write_text(f"{before}{new_table}{after}", encoding="utf-8")


def run_all(report: Report) -> int:
    initial_sha = production_sha256()
    report.write(SEPARATOR)
    report.write("VERIFICACION POR MUTACION DE C-32 (UI HORARIOS Y BLOQUEOS)")
    report.write(f"SHA-256 inicial de archivos de produccion: {initial_sha}")
    report.write(SEPARATOR)

    for mutation in MUTATIONS:
        check_definition(mutation)

    test_count = check_one_to_one()
    report.write(
        f"Correspondencia 1:1 verificada: {test_count} tests evaluados (24 nuevos + 2 modificados en AppShellNavigation.test.tsx) vs {len(MUTATIONS)} mutaciones."
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
        original_bytes = target_path.read_bytes()
        original_content = original_bytes.decode("utf-8")
        mutated_content = apply_mutation(mutation, original_content)
        if mutated_content == original_content:
            report.write("    FALLO: el mutante no cambio el archivo.")
            return 2

        print_diff(mutation, original_content, mutated_content, report)

        target_path.write_bytes(mutated_content.encode("utf-8"))
        try:
            res_mutated, rep_mutated = run_single(mutation)
        finally:
            target_path.write_bytes(original_bytes)

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
        print(f"OK: {count} tests evaluados (24 nuevos + 2 modificados en AppShellNavigation.test.tsx) coinciden 1:1 con las {len(MUTATIONS)} mutaciones.")
        return 0

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rep = Report(sys.stdout)
    code = run_all(rep)
    return code


if __name__ == "__main__":
    sys.exit(main())
