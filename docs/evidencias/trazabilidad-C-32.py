"""Trazabilidad de C-32: cada escenario de las specs delta a su test, evidencias y mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-32.py

Lee los escenarios de los spec.md del change `ui-horarios-y-bloqueos`
(frontend-working-hours-and-blocks y frontend-foundation), exige 26 escenarios
(24 testeables 1:1 + 2 visuales a cargo de Claude) y genera trazabilidad-C-32.txt
y la matriz de verify-C-32.md (entre las marcas trazabilidad:inicio / trazabilidad:fin).

Termina con código distinto de 0 si:
  (a) dos escenarios comparten el mismo test (archivo + nombre);
  (b) un escenario testeable no tiene test listado por Vitest, evidencia red-C-32/NN-*.txt,
      evidencia green-C-32/NN-*.txt o mutación definida en mutaciones-C-32.py;
  (c) el total no es 24 testeables + 2 visuales = 26, o un escenario del spec no está
      mapeado, o el mapa tiene un escenario que el spec no declara;
  (d) alguno de los 2 tests auxiliares (horariosApi.test.ts y HorariosRoute.test.tsx)
      no está listado por Vitest o no tiene evidencia RED/GREEN o mutación (M19-M20).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "trazabilidad-C-32.txt"
VERIFY = EVIDENCE / "verify-C-32.md"
ACTIVE_SPECS_DIR = REPO / "openspec" / "changes" / "ui-horarios-y-bloqueos" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

EXPECTED_TESTEABLE = 24
EXPECTED_VISUAL = 2

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


@dataclass(frozen=True)
class Entry:
    kind: str  # "testeable" | "visual"
    spec: str
    scenario: str
    number: str
    test_file: str | None = None
    test_name: str | None = None
    red_evidence: str | None = None
    green_evidence: str | None = None
    mutation: str | None = None
    visual: str | None = None


ENTRIES: tuple[Entry, ...] = (
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Odontólogo accede a sus propios horarios",
        "01",
        T_PAGE,
        "Odontólogo accede a sus propios horarios: carga tramos y bloqueos de su professionalId sin mostrar selector de profesional",
        "15-role-dentist-own.txt",
        "15-role-dentist-own.txt",
        "M01",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Administrador selecciona profesional activo",
        "02",
        T_PAGE,
        "Administrador selecciona profesional activo: lista solo activos, selecciona el primero por defecto y al cambiar actualiza datos y ?professionalId=",
        "16-role-admin-selector.txt",
        "16-role-admin-selector.txt",
        "M02",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Odontólogo consulta profesional ajeno y recibe 403",
        "03",
        T_PAGE,
        "Odontólogo consulta profesional ajeno y recibe 403: muestra en role=alert el mensaje literal del backend sin controles de edición ni cerrar sesión",
        "17-role-dentist-403.txt",
        "17-role-dentist-403.txt",
        "M03",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Guardado exitoso de tramos semanales",
        "04",
        T_HOURS,
        "Guardado exitoso de tramos semanales: envía PUT con los tramos en orden visual y anuncia Horario guardado.",
        "04-hours-save-ok.txt",
        "04-hours-save-ok.txt",
        "M04",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Edición interactiva de tramos en la interfaz",
        "05",
        T_HOURS,
        "Edición interactiva de tramos en la interfaz: agrega una fila editable para el día martes y la quita al pulsar Quitar",
        "05-hours-add-remove.txt",
        "05-hours-add-remove.txt",
        "M05",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Rechazo por tramos solapados muestra mensaje literal del backend",
        "06",
        T_HOURS,
        "Rechazo por tramos solapados muestra mensaje literal del backend: muestra role=alert literal y traslada foco al contenedor de error",
        "06-hours-overlap-422.txt",
        "06-hours-overlap-422.txt",
        "M06",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Error 400 marca campos con aria-invalid",
        "07",
        T_HOURS,
        "Error 400 marca campos con aria-invalid: marca el input inválido con aria-invalid=true y muestra el mensaje de validación",
        "07-hours-format-400.txt",
        "07-hours-format-400.txt",
        "M07",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Turnos futuros fuera del horario al guardar tramos",
        "08",
        T_AFFECTED,
        "Turnos futuros fuera del horario al guardar tramos: muestra en role=alert fecha, hora local, paciente, profesional, StatusBadge y aviso de no cancelación",
        "13-affected-hours.txt",
        "13-affected-hours.txt",
        "M08",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Turnos solapados al crear un bloqueo",
        "09",
        T_AFFECTED,
        "Turnos solapados al crear un bloqueo: muestra en role=alert la advertencia de turnos solapados con paciente, fecha, hora local y estado",
        "14-affected-block.txt",
        "14-affected-block.txt",
        "M09",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Creación exitosa de bloqueo con offset",
        "10",
        T_BLOCKS,
        "Creación exitosa de bloqueo con offset: convierte fecha y hora local a ISO con offset, cierra el diálogo y anuncia Bloqueo creado.",
        "08-block-create-ok.txt",
        "08-block-create-ok.txt",
        "M10",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Eliminación de bloqueo con confirmación in-dialog",
        "11",
        T_BLOCKS,
        "Eliminación de bloqueo con confirmación in-dialog: exige confirmación antes de enviar DELETE y anuncia Bloqueo eliminado.",
        "09-block-delete-ok.txt",
        "09-block-delete-ok.txt",
        "M11",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Cancelación del borrado con Escape",
        "12",
        T_BLOCKS,
        "Cancelación del borrado con Escape: cierra el diálogo al pulsar Escape o Volver sin enviar DELETE y restaura el foco",
        "10-block-delete-escape.txt",
        "10-block-delete-escape.txt",
        "M12",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Bloqueo inválido muestra mensaje literal del backend",
        "13",
        T_BLOCKS,
        "Bloqueo inválido muestra mensaje literal del backend: mantiene el diálogo abierto y muestra role=alert literal ante error 422",
        "11-block-invalid-422.txt",
        "11-block-invalid-422.txt",
        "M13",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Recepción visualiza información completa sin controles de edición",
        "14",
        T_PAGE,
        "Recepción visualiza información completa sin controles de edición: muestra selector, tramos y bloqueos pero oculta Agregar tramo, Quitar, Guardar horario, Nuevo bloqueo y Eliminar bloqueo",
        "18-role-reception-readonly.txt",
        "18-role-reception-readonly.txt",
        "M14",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Zona horaria leída desde GET /api/agenda",
        "15",
        T_PAGE,
        "Zona horaria leída desde GET /api/agenda: consulta GET /api/agenda una sola vez, reutiliza su timezone al cambiar de profesional y formatea bloqueos según esa zona",
        "19-timezone-api.txt",
        "19-timezone-api.txt",
        "M15",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Presentación de modal como hoja inferior en móvil",
        "16",
        T_MOBILE,
        "Presentación de modal como hoja inferior en móvil: aplica clase y atributos de hoja inferior a ≤ 640 px ocupando el 100% del ancho útil",
        "12-block-bottom-sheet.txt",
        "12-block-bottom-sheet.txt",
        "M16",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        "17",
        T_NAVIGATION,
        "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        "03-menu-pre.txt",
        "03-menu-ok.txt",
        "M17",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        "18",
        T_NAVIGATION,
        "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        "03-menu-pre.txt",
        "03-menu-ok.txt",
        "M18",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Todas las variables CSS de horarios existen en tokens.css",
        "19",
        T_STYLES,
        "Todas las variables CSS de horarios existen en tokens.css: cada var(--x) usado en los .module.css de horarios está definido en tokens.css",
        "20-css-tokens-exist.txt",
        "20-css-tokens-exist.txt",
        "M21",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Encabezado y estilos de HorariosPage sin tokens de fondo oscuro",
        "20",
        T_STYLES,
        "Encabezado y estilos de HorariosPage sin tokens de fondo oscuro: HorariosPage.module.css usa tokens de superficie clara y no contiene --color-ice ni *-on-navy",
        "21-css-header-light-tokens.txt",
        "21-css-header-light-tokens.txt",
        "M22",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Título de PageShell Horarios y bloqueos con único h1",
        "21",
        T_PAGE,
        "Título de PageShell Horarios y bloqueos con único h1: pasa title Horarios y bloqueos a PageShell y mantiene un solo h1",
        "22-pageshell-title-h1.txt",
        "22-pageshell-title-h1.txt",
        "M23",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Eliminar bloqueo oculta su panel de turnos afectados",
        "22",
        T_BLOCKS,
        "Eliminar bloqueo oculta su panel de turnos afectados: al confirmar la eliminación del bloqueo desaparece la alerta de turnos solapados",
        "23-delete-block-clears-affected.txt",
        "23-delete-block-clears-affected.txt",
        "M24",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Un solo mensaje de estado vigente entre acciones sin desmontar la región",
        "23",
        T_PAGE,
        "Un solo mensaje de estado vigente entre acciones sin desmontar la región: reemplaza Horario guardado por Bloqueo eliminado y mantiene una única región role=status montada",
        "24-single-status-message.txt",
        "24-single-status-message.txt",
        "M25",
    ),
    Entry(
        "testeable",
        "frontend-working-hours-and-blocks",
        "Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar",
        "24",
        T_AFFECTED,
        "Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar: formatea 2026-11-17 como mar, 17/11/2026 con la timezone de la API y no muestra ISO",
        "25-dates-local-format.txt",
        "25-dates-local-format.txt",
        "M26",
    ),
    Entry(
        "visual",
        "frontend-working-hours-and-blocks",
        "Verificación visual multi-resolución en 1440, 768 y 390 px",
        "V01",
        visual="C-32-horarios-{1440,768,390}.png",
    ),
    Entry(
        "visual",
        "frontend-foundation",
        "Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px)",
        "V02",
        visual="C-32-appshell-{768,390}.png",
    ),
)

AUXILIARY_ENTRIES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "M19",
        T_API,
        "parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock",
        "01-api-ok.txt",
        "01-api-ok.txt",
    ),
    (
        "M20",
        T_ROUTE,
        "renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo",
        "02-route.txt",
        "02-route.txt",
    ),
)

ASSERTION_RE = re.compile(r"AssertionError|Error: expect\(")


def resolve_specs_dir() -> Path:
    if ACTIVE_SPECS_DIR.is_dir():
        return ACTIVE_SPECS_DIR
    archive_base = REPO / "openspec" / "changes" / "archive"
    if archive_base.is_dir():
        matches = sorted(archive_base.glob("*-ui-horarios-y-bloqueos/specs"))
        if matches:
            return matches[-1]
    return ACTIVE_SPECS_DIR


def read_spec_scenarios() -> list[tuple[str, str]]:
    specs_dir = resolve_specs_dir()
    scenarios: list[tuple[str, str]] = []
    scenario_regex = re.compile(r"^####\s+Scenario:\s*(.+)$")
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_file = spec_dir / "spec.md"
        if not spec_file.is_file():
            continue
        spec_name = spec_dir.name
        for line in spec_file.read_text(encoding="utf-8").splitlines():
            match = scenario_regex.match(line)
            if match:
                scenarios.append((spec_name, match.group(1).strip()))
    return scenarios


def vitest_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env


def listed_tests() -> list[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", *C32_TEST_FILES, "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=vitest_env(),
        timeout=120,
        check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
        if file in C32_TEST_FILES:
            tests.append((file, name))
    return tests


def load_mutations_map() -> dict[tuple[str, str], str]:
    path = EVIDENCE / "mutaciones-C-32.py"
    spec = importlib.util.spec_from_file_location("mutaciones_c32", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar mutaciones-C-32.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mutaciones_c32"] = module
    spec.loader.exec_module(module)
    return {
        (m.test_file, m.test_name): module.mutation_id(idx)
        for idx, m in enumerate(module.MUTATIONS, start=1)
    }


def check_evidence_file(folder: str, filename: str, is_red: bool) -> str | None:
    path = EVIDENCE / folder / filename
    if not path.is_file():
        return f"Falta evidencia {folder}/{filename}"
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\x1b\[[0-9;]*m", "", raw_text)
    if is_red and not ASSERTION_RE.search(text):
        return f"{folder}/{filename} no contiene fallo por aserción (AssertionError / Error: expect)"
    if not is_red and not re.search(r"Tests\s+\d+ passed", text):
        return f"{folder}/{filename} no muestra tests pasados en verde"
    return None


def update_verify_markdown(rows: list[str], aux_rows: list[str]) -> None:
    if not VERIFY.is_file():
        return
    content = VERIFY.read_text(encoding="utf-8")
    if TABLE_START not in content or TABLE_END not in content:
        return
    header = (
        "| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    aux_section = (
        "\nTests auxiliares de contrato y enrutamiento (con par RED/GREEN y mutación propia):\n\n"
        "| Mutación | Archivo de test | Test | Evidencia RED | Evidencia GREEN |\n"
        "|---|---|---|---|---|\n"
        + "\n".join(aux_rows)
        + "\n"
    )
    table_body = header + "\n".join(rows) + "\n" + aux_section
    before, rest = content.split(TABLE_START, 1)
    _, after = rest.split(TABLE_END, 1)
    updated = f"{before}{TABLE_START}\n{table_body}{TABLE_END}{after}"
    VERIFY.write_text(updated, encoding="utf-8")


def main() -> int:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("TRAZABILIDAD C-32 (ui-horarios-y-bloqueos) — SPEC -> TEST -> EVIDENCIA -> MUTACIÓN")
    lines.append("=" * 80)

    # 1. Validar escenarios declarados en specs
    spec_scenarios = read_spec_scenarios()
    mapped_scenarios = [(e.spec, e.scenario) for e in ENTRIES]

    missing_in_map = set(spec_scenarios) - set(mapped_scenarios)
    extra_in_map = set(mapped_scenarios) - set(spec_scenarios)

    if missing_in_map:
        lines.append(f"ERROR: Escenarios en specs sin mapear: {missing_in_map}")
        print("\n".join(lines), file=sys.stderr)
        return 1
    if extra_in_map:
        lines.append(f"ERROR: Escenarios en mapa que no están en specs: {extra_in_map}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    testable_entries = [e for e in ENTRIES if e.kind == "testeable"]
    visual_entries = [e for e in ENTRIES if e.kind == "visual"]
    if len(testable_entries) != EXPECTED_TESTEABLE or len(visual_entries) != EXPECTED_VISUAL:
        lines.append(
            f"ERROR: Conteo inválido ({len(testable_entries)} testeables, {len(visual_entries)} visuales)"
        )
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append(
        f"Escenarios declarados en specs: {len(spec_scenarios)} "
        f"({len(testable_entries)} testeables + {len(visual_entries)} visuales = {EXPECTED_TESTEABLE + EXPECTED_VISUAL})"
    )

    # 2. Validar que no haya tests duplicados entre escenarios
    test_keys = [(e.test_file, e.test_name) for e in testable_entries]
    counts = Counter(test_keys)
    duplicates = [k for k, v in counts.items() if v > 1]
    if duplicates:
        lines.append(f"ERROR: Escenarios comparten el mismo test: {duplicates}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    # 3. Validar correspondencia con tests listados por Vitest y mutaciones-C-32.py
    tests = set(listed_tests())
    mutations_map = load_mutations_map()

    missing_tests = set(test_keys) - tests
    if missing_tests:
        lines.append(f"ERROR: Tests de escenarios no listados por Vitest: {missing_tests}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    for e in testable_entries:
        key = (e.test_file or "", e.test_name or "")
        if mutations_map.get(key) != e.mutation:
            lines.append(
                f"ERROR: Mutación esperada {e.mutation} para {key}, encontrada {mutations_map.get(key)}"
            )
            print("\n".join(lines), file=sys.stderr)
            return 1

    # 4. Validar evidencias RED y GREEN de escenarios y auxiliares
    evidence_errors: list[str] = []
    for e in testable_entries:
        assert e.red_evidence and e.green_evidence
        err_r = check_evidence_file("red-C-32", e.red_evidence, is_red=True)
        if err_r:
            evidence_errors.append(err_r)
        err_g = check_evidence_file("green-C-32", e.green_evidence, is_red=False)
        if err_g:
            evidence_errors.append(err_g)

    for mid, tf, tn, red_ev, green_ev in AUXILIARY_ENTRIES:
        if (tf, tn) not in tests:
            evidence_errors.append(f"Test auxiliar no listado por Vitest: {tf} > {tn}")
        if mutations_map.get((tf, tn)) != mid:
            evidence_errors.append(f"Test auxiliar {tf} > {tn} sin mutación {mid}")
        err_r = check_evidence_file("red-C-32", red_ev, is_red=True)
        if err_r:
            evidence_errors.append(err_r)
        err_g = check_evidence_file("green-C-32", green_ev, is_red=False)
        if err_g:
            evidence_errors.append(err_g)

    if evidence_errors:
        lines.append(f"ERROR: Problemas de evidencia/auxiliares: {evidence_errors}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append("Validación de correspondencia 1:1 (cero tests compartidos): OK")
    lines.append(
        f"Validación de evidencias RED/GREEN: OK ({len(testable_entries)} escenarios + {len(AUXILIARY_ENTRIES)} auxiliares)"
    )

    # 5. Generar listado y tabla de trazabilidad
    table_rows: list[str] = []
    for e in ENTRIES:
        if e.kind == "visual":
            if e.number == "V01":
                links = "[C-32-horarios-1440.png](capturas/C-32-horarios-1440.png), [C-32-horarios-768.png](capturas/C-32-horarios-768.png), [C-32-horarios-390.png](capturas/C-32-horarios-390.png)"
                row = f"| {e.number} | `{e.spec}` | {e.scenario} | Visual | {links} | — | — | — | — |"
            elif e.number == "V02":
                links = "[C-32-appshell-768.png](capturas/C-32-appshell-768.png), [C-32-appshell-390.png](capturas/C-32-appshell-390.png)"
                row = f"| {e.number} | `{e.spec}` | {e.scenario} | Visual | {links} | — | — | — | — |"
            else:
                row = f"| {e.number} | `{e.spec}` | {e.scenario} | Visual | `{e.visual}` | — | — | — | — |"
            lines.append(f"  [{e.number}] ({e.spec}) {e.scenario} -> Visual ({e.visual})")
        else:
            tf_base = Path(e.test_file).name if e.test_file else "—"
            short_test = e.test_name.split(":")[0] if e.test_name else "—"
            row = (
                f"| {e.number} | `{e.spec}` | {e.scenario} | Testeable | "
                f"`{tf_base}` | `{short_test}` | `{e.red_evidence}` | `{e.green_evidence}` | `{e.mutation}` |"
            )
            lines.append(
                f"  [{e.number}] ({e.spec}) {e.scenario} -> {tf_base} :: {short_test} "
                f"[RED: {e.red_evidence} | GREEN: {e.green_evidence} | MUT: {e.mutation}]"
            )
        table_rows.append(row)

    aux_rows: list[str] = []
    for mid, tf, tn, red_ev, green_ev in AUXILIARY_ENTRIES:
        tf_base = Path(tf).name
        aux_rows.append(f"| `{mid}` | `{tf_base}` | `{tn}` | `{red_ev}` | `{green_ev}` |")
        lines.append(
            f"  [{mid}] (auxiliar) {tf_base} :: {tn} [RED: {red_ev} | GREEN: {green_ev}]"
        )

    update_verify_markdown(table_rows, aux_rows)

    lines.append("=" * 80)
    lines.append(
        f"TOTAL: {len(testable_entries)} testeables + {len(visual_entries)} visuales = "
        f"{len(ENTRIES)} escenarios mapeados (+ {len(AUXILIARY_ENTRIES)} tests auxiliares con mutación)"
    )
    lines.append("EXITO: Trazabilidad 100% verificada.")
    lines.append("=" * 80)

    text = "\n".join(lines) + "\n"
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
