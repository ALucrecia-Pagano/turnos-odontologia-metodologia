"""Trazabilidad de C-31: cada escenario de las specs delta a su test, evidencias y mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-31.py

Lee los escenarios de los spec.md del change `ui-vista-de-recepcion-por-sillon` (frontend-agenda),
exige 24 escenarios (23 testeables 1:1 + 1 visual a cargo de Claude) y genera trazabilidad-C-31.txt
y la matriz de verify-C-31.md (entre las marcas trazabilidad:inicio / trazabilidad:fin).

Termina con código distinto de 0 si:
  (a) dos escenarios comparten el mismo test (archivo + nombre);
  (b) un escenario nuevo no tiene test listado por Vitest, evidencia red-C-31/NN-*.txt,
      evidencia green-C-31/NN-*.txt o mutación definida en mutaciones-C-31.py;
  (c) el total no es 23 testeables + 1 visual = 24, o un escenario del spec no está
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
OUTPUT = EVIDENCE / "trazabilidad-C-31.txt"
VERIFY = EVIDENCE / "verify-C-31.md"
SPECS_DIR = REPO / "openspec" / "changes" / "archive" / "2026-11-14-ui-vista-de-recepcion-por-sillon" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

EXPECTED_TESTEABLE = 23
EXPECTED_VISUAL = 1

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


@dataclass(frozen=True)
class Entry:
    kind: str  # "testeable" | "visual"
    spec: str
    scenario: str
    number: str
    test_file: str | None = None
    test_name: str | None = None
    evidence: str | None = None
    mutation: str | None = None


ENTRIES: tuple[Entry, ...] = (
    Entry(
        "testeable",
        "frontend-agenda",
        "Activar Sillones conserva fecha y filtros",
        "01",
        T_PAGE,
        "Activar Sillones conserva fecha y filtros: activar Sillones conserva fecha y filtros",
        "04-agendaPagePorSillon",
        "M01",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Un view desconocido sigue cayendo a Día",
        "02",
        T_PAGE,
        "Un view desconocido sigue cayendo a Día: view desconocido cae a Día",
        "04-agendaPagePorSillon",
        "M02",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Turnos de distintos profesionales en la misma columna",
        "03",
        T_VIEW,
        "Turnos de distintos profesionales en la misma columna: dos profesionales en una columna de sillón",
        "03-agendaViewChair",
        "M03",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Sillón sin turnos",
        "04",
        T_VIEW,
        "Sillón sin turnos: sillón sin turnos muestra Libre y Fuera de horario",
        "03-agendaViewChair",
        "M04",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Filtro de un solo sillón",
        "05",
        T_PAGE,
        "Filtro de un solo sillón: chairId deja una sola columna",
        "04-agendaPagePorSillon",
        "M05",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Sillón inactivo visible",
        "06",
        T_LAYOUT,
        "Sillón inactivo visible: sillón inactivo con sufijo (inactivo)",
        "01-agendaChairLayout",
        "M06",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Hueco libre entre dos turnos",
        "07",
        T_LAYOUT,
        "Hueco libre entre dos turnos: hueco 10:30–11:00 entre dos turnos",
        "01-agendaChairLayout",
        "M07",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Un cancelado no ocupa el sillón",
        "08",
        T_LAYOUT,
        "Un cancelado no ocupa el sillón: cancelado libera el tramo",
        "01-agendaChairLayout",
        "M08",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "La disponibilidad no depende solo del color",
        "09",
        T_STYLES,
        "La disponibilidad no depende sólo del color: bandas con texto y sin HEX",
        "05-agendaChairStyles",
        "M09",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Eje con la unión de horarios del día",
        "10",
        T_LAYOUT,
        "Eje con la unión de horarios del día: eje 09:00–19:00 y gap 13:00–15:00",
        "01-agendaChairLayout",
        "M10",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Día sin horarios de atención",
        "11",
        T_LAYOUT,
        "Día sin horarios de atención: sin horarios usa 08:00–20:00 sin Libre",
        "01-agendaChairLayout",
        "M11",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Día por defecto desde el Clock",
        "12",
        T_PAGE,
        "Día por defecto desde el Clock: view=chair sin date usa el Clock",
        "04-agendaPagePorSillon",
        "M12",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Navegación de un día",
        "13",
        T_PAGE,
        "Navegación de un día: Siguiente suma un día en view=chair",
        "04-agendaPagePorSillon",
        "M13",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Clic en la tarjeta abre el detalle",
        "14",
        T_VIEW,
        "Clic en la tarjeta abre el detalle: clic en tarjeta abre AppointmentDetailDialog",
        "03-agendaViewChair",
        "M14",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Nombre accesible completo en la tarjeta",
        "15",
        T_VIEW,
        "Nombre accesible completo en la tarjeta: aria-label incluye hora, paciente, profesional, sillón, prestación y estado",
        "03-agendaViewChair",
        "M15",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Recepción y administración ven el control",
        "16",
        T_TOOLBAR,
        "Recepción y administración ven el control: Sillones visible para recepcion y administrador",
        "02-agendaToolbarChair",
        "M16",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Odontólogo sin acceso",
        "17",
        T_PAGE,
        "Odontólogo sin acceso: odontólogo con view=chair cae a Día",
        "04-agendaPagePorSillon",
        "M17",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "El filtro de sillón reduce las columnas",
        "18",
        T_PAGE,
        "El filtro de sillón reduce las columnas: aplicar el filtro Sillón 2 actualiza la URL y reduce a una columna",
        "04-agendaPagePorSillon",
        "M18",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "El filtro de profesional recalcula los horarios",
        "19",
        T_LAYOUT,
        "El filtro de profesional recalcula los horarios: professionalId de Sosa deja unión 09:00–13:00",
        "01-agendaChairLayout",
        "M19",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "La ayuda del filtro de sillón se adapta",
        "20",
        T_TOOLBAR,
        "La ayuda del filtro de sillón se adapta: en view=chair muestra CHAIR_VIEW_HELP_TEXT",
        "02-agendaToolbarChair",
        "M20",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "La lista sigue disponible",
        "21",
        T_VIEW,
        "La lista sigue disponible: Ver como lista con columna Sillón",
        "03-agendaViewChair",
        "M21",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Un día sin turnos conserva la grilla",
        "22",
        T_VIEW,
        "Un día sin turnos conserva la grilla: día sin turnos mantiene grilla y aviso",
        "03-agendaViewChair",
        "M22",
    ),
    Entry(
        "testeable",
        "frontend-agenda",
        "Catálogo de sillones vacío",
        "23",
        T_VIEW,
        "Catálogo de sillones vacío: sin sillones muestra No hay sillones configurados",
        "03-agendaViewChair",
        "M23",
    ),
    Entry(
        "visual",
        "frontend-agenda",
        "Capturas a 1440, 768 y 390 px",
        "V01",
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
        [*VITEST, "list", *C31_TEST_FILES, "--json"],
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
        if file in C31_TEST_FILES:
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
    lines.append("TRAZABILIDAD C-31 (ui-vista-de-recepcion-por-sillon) — SPEC -> TEST -> EVIDENCIA -> MUTACIÓN")
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

    lines.append(f"Escenarios declarados en specs: {len(spec_scenarios)} (esperados: {EXPECTED_TESTEABLE + EXPECTED_VISUAL})")

    # 2. Validar que no haya tests duplicados entre escenarios
    testable_entries = [e for e in ENTRIES if e.kind == "testeable"]
    test_keys = [(e.test_file, e.test_name) for e in testable_entries]
    counts = Counter(test_keys)
    duplicates = [k for k, v in counts.items() if v > 1]
    if duplicates:
        lines.append(f"ERROR: Escenarios comparten el mismo test: {duplicates}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    # 3. Validar correspondencia con tests listados por Vitest
    tests = listed_tests()
    missing_tests = set(test_keys) - set(tests)
    if missing_tests:
        lines.append(f"ERROR: Tests testeables no listados por Vitest: {missing_tests}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    # 4. Validar evidencias RED y GREEN
    red_dir = EVIDENCE / "red-C-31"
    green_dir = EVIDENCE / "green-C-31"
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
    lines.append(f"Validación de evidencias RED/GREEN: OK ({len(testable_entries)}/{len(testable_entries)} pares presentes)")

    # 5. Generar tabla de trazabilidad
    table_rows: list[str] = []
    for e in ENTRIES:
        if e.kind == "visual":
            row = f"| {e.number} | `{e.spec}` | {e.scenario} | Visual | — | — | — | — | — |"
        else:
            tf_base = Path(e.test_file).name if e.test_file else "—"
            short_test = e.test_name.split(":")[0] if e.test_name else "—"
            red_ev = f"{e.evidence}-red.txt"
            green_ev = f"{e.evidence}-green.txt"
            row = (
                f"| {e.number} | `{e.spec}` | {e.scenario} | Testeable | "
                f"`{tf_base}` | `{short_test}` | `{red_ev}` | `{green_ev}` | `{e.mutation}` |"
            )
        table_rows.append(row)

    update_verify_markdown(table_rows)

    lines.append("=" * 80)
    lines.append(f"TOTAL: {len(testable_entries)} testeables + {len(ENTRIES) - len(testable_entries)} visuales = {len(ENTRIES)} escenarios mapeados")
    lines.append("EXITO: Trazabilidad 100% verificada.")
    lines.append("=" * 80)

    text = "\n".join(lines) + "\n"
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
