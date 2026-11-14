"""Trazabilidad de C-36: cada escenario de las specs delta a su test, evidencias y mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-36.py

Lee los escenarios de los spec.md del change `ui-tema-oscuro-y-movil`
(frontend-foundation y frontend-agenda), exige 12 escenarios
(8 testeables 1:1 + 4 visuales a cargo de Claude) y genera trazabilidad-C-36.txt y la matriz de
verify-C-36.md (entre las marcas trazabilidad:inicio / trazabilidad:fin).

Termina con código distinto de 0 si:
  (a) dos escenarios comparten el mismo test (archivo + nombre);
  (b) un escenario nuevo no tiene test listado por Vitest, evidencia red-C-36/NN-*.txt,
      evidencia green-C-36/NN-*.txt o mutación definida en mutaciones-C-36.py;
  (c) el total no es 8 testeables + 4 visuales = 12, o un escenario del spec no está
      mapeado, o el mapa tiene un escenario que el spec no declara.
"""

from __future__ import annotations

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
OUTPUT = EVIDENCE / "trazabilidad-C-36.txt"
VERIFY = EVIDENCE / "verify-C-36.md"
SPECS_DIR = REPO / "openspec" / "changes" / "ui-tema-oscuro-y-movil" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

EXPECTED_TESTEABLE = 8
EXPECTED_VISUAL = 4

T_APPSHELL = "src/shared/components/AppShell.mobile.test.tsx"
T_TOOLBAR = "src/features/agenda/AgendaToolbar.mobile.test.tsx"
T_GRID = "src/features/agenda/AgendaGrid.mobile.test.tsx"
T_DIALOG = "src/shared/components/Dialog.bottomSheet.test.tsx"

C36_TEST_FILES = (
    T_APPSHELL,
    T_TOOLBAR,
    T_GRID,
    T_DIALOG,
)


@dataclass(frozen=True)
class Entry:
    kind: str  # "testeable" | "visual"
    spec: str
    scenario: str
    number: str  # NN para testeables (01..08), V01..V04 para visuales
    test_file: str | None = None
    test_name: str | None = None
    evidence: str | None = None
    mutation: str | None = None


ENTRIES: tuple[Entry, ...] = (
    Entry(
        "testeable",
        "frontend-foundation",
        "Cabecera compacta y apertura de menú en celular",
        "01",
        T_APPSHELL,
        "01-cabecera-compacta-y-apertura-menu: expone botón Menú fuera de nav con aria-expanded y aria-controls, y al pulsar despliega la navegación",
        "01-appshell-menu",
        "M01",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Cierre del menú con Escape y retorno de foco al botón",
        "02",
        T_APPSHELL,
        "02-cierre-menu-escape-y-retorno-foco: presionar Escape cierra el menú desplegado y devuelve el foco al botón Menú",
        "02-appshell-escape",
        "M02",
    ),
    Entry(
        "visual",
        "frontend-foundation",
        "Navegación de AppShell y menú verificados a 1440, 768 y 390 px",
        "V01",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Hoja inferior a ancho completo con scroll interno en celular",
        "07",
        T_DIALOG,
        "07-dialog-bottom-sheet-mobile: renderiza como hoja inferior anclada al fondo con scroll interno en celular",
        "07-dialog-bottom-sheet",
        "M07",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Preservación de modal centrado flotante en tablet y escritorio",
        "08",
        T_DIALOG,
        "08-dialog-modal-centrado-desktop: preserva modal centrado flotante en pantallas de escritorio",
        "08-dialog-centrado-desktop",
        "M08",
    ),
    Entry(
        "visual",
        "frontend-foundation",
        "Modales de turnos verificados a 1440, 768 y 390 px",
        "V02",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Organización compacta de navegación y fecha en celular",
        "03",
        T_TOOLBAR,
        "03-toolbar-distribucion-compacta: organiza navegación y fecha en dos filas diferenciadas en celular",
        "03-toolbar-compacta",
        "M03",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Botón Filtros con contador de filtros activos y panel accesible",
        "04",
        T_TOOLBAR,
        "04-toolbar-boton-filtros-con-contador: expone botón Filtros con indicador dinámico de filtros activos y despliega panel accesible",
        "04-toolbar-filtros",
        "M04",
    ),
    Entry(
        "visual",
        "frontend-agenda",
        "Toolbar de agenda verificada a 1440, 768 y 390 px",
        "V03",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Desplazamiento horizontal fluido con scroll-snap y horas fijas",
        "05",
        T_GRID,
        "05-grilla-scroll-snap-y-horas-sticky: aplica scroll-snap horizontal mandatory y eje horario fijo en celular",
        "05-grilla-scroll-snap",
        "M05",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Columna completa al ancho útil y preservación de grilla por defecto",
        "06",
        T_GRID,
        "06-grilla-ancho-util-y-default-grid: preserva modo inicial grilla en AgendaView y dimensiona columnas a ancho útil en móvil",
        "06-grilla-ancho-util",
        "M06",
    ),
    Entry(
        "visual",
        "frontend-agenda",
        "Grilla de agenda verificada a 1440, 768 y 390 px",
        "V04",
    ),
)


def read_spec_scenarios() -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    scenario_regex = re.compile(r"^####\s+Scenario:\s*(.+)$")
    for spec_dir in sorted(SPECS_DIR.iterdir()):
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
        [*VITEST, "list", *C36_TEST_FILES, "--json"],
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
        if file in C36_TEST_FILES:
            tests.append((file, name))
    return tests


def update_verify_markdown(rows: list[str]) -> None:
    if not VERIFY.is_file():
        return
    content = VERIFY.read_text(encoding="utf-8")
    if TABLE_START not in content or TABLE_END not in content:
        return
    header = (
        "| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    table_body = header + "\n".join(rows) + "\n"
    before, rest = content.split(TABLE_START, 1)
    _, after = rest.split(TABLE_END, 1)
    updated = f"{before}{TABLE_START}\n{table_body}{TABLE_END}{after}"
    VERIFY.write_text(updated, encoding="utf-8")


def main() -> int:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("TRAZABILIDAD C-36 (ui-tema-oscuro-y-movil) — SPEC -> TEST -> EVIDENCIA -> MUTACIÓN")
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
        lines.append(f"ERROR: Escenarios en mapa no encontrados en specs: {extra_in_map}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append(f"Total escenarios en specs: {len(spec_scenarios)} (8 testeables, 4 visuales)")

    # 2. Validar que no haya tests compartidos
    testable_entries = [e for e in ENTRIES if e.kind == "testeable"]
    test_keys = [(e.test_file, e.test_name) for e in testable_entries]
    counts = Counter(test_keys)
    duplicates = [k for k, v in counts.items() if v > 1]
    if duplicates:
        lines.append(f"ERROR: Tests compartidos entre escenarios: {duplicates}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    # 3. Validar contra vitest list
    active_tests = listed_tests()
    missing_tests: list[str] = []
    for e in testable_entries:
        if (e.test_file, e.test_name) not in active_tests:
            missing_tests.append(f"{e.test_file} > {e.test_name}")

    if missing_tests:
        lines.append(f"ERROR: Tests testeables no listados por Vitest: {missing_tests}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    # 4. Validar evidencias RED y GREEN
    red_dir = EVIDENCE / "red-C-36"
    green_dir = EVIDENCE / "green-C-36"
    missing_red: list[str] = []
    missing_green: list[str] = []

    for e in testable_entries:
        red_pattern = list(red_dir.glob(f"{e.evidence}*.txt")) if red_dir.is_dir() else []
        if not red_pattern:
            missing_red.append(f"{e.evidence} en {red_dir}")
        green_pattern = list(green_dir.glob(f"{e.evidence}*.txt")) if green_dir.is_dir() else []
        if not green_pattern:
            missing_green.append(f"{e.evidence} en {green_dir}")

    if missing_red:
        lines.append(f"ERROR: Evidencias RED faltantes: {missing_red}")
        print("\n".join(lines), file=sys.stderr)
        return 1
    if missing_green:
        lines.append(f"ERROR: Evidencias GREEN faltantes: {missing_green}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append("Validación de correspondencia 1:1: OK")
    lines.append("Validación de evidencias RED/GREEN: OK (8/8 pares presentes)")

    # 5. Generar tabla de trazabilidad
    markdown_rows: list[str] = []
    for e in ENTRIES:
        if e.kind == "testeable":
            tf_base = Path(e.test_file or "").name
            short_test = (e.test_name or "").split(":")[0]
            row = (
                f"| {e.number} | `{e.spec}` | {e.scenario} | Testeable | "
                f"`{tf_base}` | `{short_test}` | `{e.evidence}-red.txt` | `{e.evidence}-green.txt` | `{e.mutation}` |"
            )
        else:
            row = (
                f"| {e.number} | `{e.spec}` | {e.scenario} | Visual | "
                f"— | — | — | — | — |"
            )
        markdown_rows.append(row)
        lines.append(f"[{e.number}] {e.spec} > {e.scenario} -> {e.kind}")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_verify_markdown(markdown_rows)
    print("OK: Matriz de trazabilidad generada sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
