"""Trazabilidad de C-33: cada escenario de las specs delta a su test, evidencias y mutación.

Uso:
    python docs/evidencias/trazabilidad-C-33.py

Lee los escenarios de los spec.md del change `ui-catalogos-y-pacientes`
(frontend-catalogs-and-patients y frontend-foundation), exige 33 escenarios
(30 testeables 1:1 + 3 visuales a cargo de Claude) y genera trazabilidad-C-33.txt
y la matriz de verify-C-33.md (entre las marcas trazabilidad:inicio / trazabilidad:fin).

Termina con código distinto de 0 si:
  (a) dos escenarios comparten el mismo test (archivo + nombre);
  (b) un escenario testeable no tiene test listado por Vitest, evidencia red-C-33/NN-*.txt,
      evidencia green-C-33/NN-*.txt o mutación definida en mutaciones-C-33.py;
  (c) el total no es 30 testeables + 3 visuales = 33, o un escenario del spec no está
      mapeado, o el mapa tiene un escenario que el spec no declara.
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
OUTPUT = EVIDENCE / "trazabilidad-C-33.txt"
VERIFY = EVIDENCE / "verify-C-33.md"
ACTIVE_SPECS_DIR = REPO / "openspec" / "changes" / "ui-catalogos-y-pacientes" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str((FRONTEND / "node_modules" / "vitest" / "vitest.mjs").resolve())]

EXPECTED_TESTEABLE = 34
EXPECTED_VISUAL = 3

# Archivos de test de C-33
T_PACIENTES_PAGE = "src/features/pacientes/PacientesPage.test.tsx"
T_PACIENTES_FORM = "src/features/pacientes/PatientFormDialog.test.tsx"
T_CATALOGOS_STYLES = "src/features/catalogos/catalogosPacientesStyles.test.ts"
T_CATALOGOS_PAGE = "src/features/catalogos/CatalogosPage.test.tsx"
T_ROUTES = "src/features/catalogos/CatalogosPacientesRoutes.test.tsx"
T_CATALOGOS_FORM = "src/features/catalogos/CatalogFormDialog.test.tsx"
T_CATALOGOS_MOBILE = "src/features/catalogos/CatalogFormDialog.mobile.test.tsx"
T_CONFIRM = "src/features/catalogos/CatalogConfirmDialog.test.tsx"
T_SHELL_NEW = "src/shared/components/AppShellCatalogosPacientes.test.tsx"
T_SHELL_NAV = "src/shared/components/AppShellNavigation.test.tsx"
T_DIALOG_MODAL_CARD = "src/features/catalogos/DialogModalCard.test.tsx"
T_TABLE_ACTIONS = "src/features/catalogos/TableActionsHeader.test.tsx"

C33_TEST_FILES = (
    T_PACIENTES_PAGE,
    T_PACIENTES_FORM,
    T_CATALOGOS_STYLES,
    T_CATALOGOS_PAGE,
    T_ROUTES,
    T_CATALOGOS_FORM,
    T_CATALOGOS_MOBILE,
    T_CONFIRM,
    T_SHELL_NEW,
    T_SHELL_NAV,
    T_DIALOG_MODAL_CARD,
    T_TABLE_ACTIONS,
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
        "frontend-catalogs-and-patients",
        "Listado de pacientes con sus cuatro datos",
        "01",
        T_PACIENTES_PAGE,
        "Listado de pacientes con sus cuatro datos",
        "01-pacientes-listado.txt",
        "01-pacientes-listado.txt",
        "M01",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Búsqueda envía la consulta codificada y muestra el resultado",
        "02",
        T_PACIENTES_PAGE,
        "Búsqueda envía la consulta codificada y muestra el resultado",
        "02-pacientes-busqueda.txt",
        "02-pacientes-busqueda.txt",
        "M02",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Búsqueda sin resultados",
        "03",
        T_PACIENTES_PAGE,
        "Búsqueda sin resultados",
        "03-pacientes-sin-resultados.txt",
        "03-pacientes-sin-resultados.txt",
        "M03",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Error de carga de pacientes con reintento",
        "04",
        T_PACIENTES_PAGE,
        "Error de carga de pacientes con reintento",
        "04-pacientes-reintento.txt",
        "04-pacientes-reintento.txt",
        "M04",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Toda variable CSS de las pantallas existe en tokens.css",
        "05",
        T_CATALOGOS_STYLES,
        "Toda variable CSS de las pantallas existe en tokens.css",
        "05-css-tokens-existen.txt",
        "05-css-tokens-existen.txt",
        "M05",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Sin tokens de fondo oscuro en las pantallas",
        "06",
        T_CATALOGOS_STYLES,
        "Sin tokens de fondo oscuro en las pantallas",
        "06-css-superficie-clara.txt",
        "06-css-superficie-clara.txt",
        "M06",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Profesionales por defecto con estado en texto",
        "07",
        T_CATALOGOS_PAGE,
        "Profesionales por defecto con estado en texto",
        "07-catalogos-profesionales-defecto.txt",
        "07-catalogos-profesionales-defecto.txt",
        "M07",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Cambio a la sección de prestaciones",
        "08",
        T_CATALOGOS_PAGE,
        "Cambio a la sección de prestaciones",
        "08-catalogos-cambio-seccion.txt",
        "08-catalogos-cambio-seccion.txt",
        "M08",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Pacientes y Catálogos con su título y un único h1",
        "09",
        T_ROUTES,
        "Pacientes y Catálogos con su título y un único h1",
        "09-titulo-h1.txt",
        "09-titulo-h1.txt",
        "M09",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Tablas apiladas en celular, controles táctiles y foco visible",
        "10",
        T_CATALOGOS_STYLES,
        "Tablas apiladas en celular, controles táctiles y foco visible",
        "10-css-tablas-adaptables.txt",
        "10-css-tablas-adaptables.txt",
        "M10",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Catálogos y Pacientes habilitados para los tres roles",
        "11",
        T_SHELL_NEW,
        "Catálogos y Pacientes habilitados para los tres roles",
        "11-menu-habilitado.txt",
        "11-menu-habilitado.txt",
        "M11",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        "12",
        T_SHELL_NAV,
        "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        "12-13-menu-existentes.txt",
        "12-13-menu-existentes.txt",
        "M12",
    ),
    Entry(
        "testeable",
        "frontend-foundation",
        "Ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        "13",
        T_SHELL_NAV,
        "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        "12-13-menu-existentes.txt",
        "12-13-menu-existentes.txt",
        "M13",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Alta de paciente",
        "14",
        T_PACIENTES_FORM,
        "Alta de paciente",
        "14-paciente-alta.txt",
        "14-paciente-alta.txt",
        "M14",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "El formulario de paciente tiene solo los cuatro datos mínimos",
        "15",
        T_PACIENTES_FORM,
        "El formulario de paciente tiene solo los cuatro datos mínimos",
        "15-paciente-cuatro-campos.txt",
        "15-paciente-cuatro-campos.txt",
        "M15",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Edición de paciente con valores precargados",
        "16",
        T_PACIENTES_FORM,
        "Edición de paciente con valores precargados",
        "16-paciente-edicion.txt",
        "16-paciente-edicion.txt",
        "M16",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "DNI duplicado muestra el mensaje literal del backend",
        "17",
        T_PACIENTES_FORM,
        "DNI duplicado muestra el mensaje literal del backend",
        "17-paciente-dni-duplicado.txt",
        "17-paciente-dni-duplicado.txt",
        "M17",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)",
        "18",
        T_PACIENTES_FORM,
        "DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)",
        "18-paciente-dni-invalido.txt",
        "18-paciente-dni-invalido.txt",
        "M18",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Error 400 por campo marca el campo con aria-invalid",
        "19",
        T_PACIENTES_FORM,
        "Error 400 por campo marca el campo con aria-invalid",
        "19-paciente-400-campo.txt",
        "19-paciente-400-campo.txt",
        "M19",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Odontólogo consulta pacientes en solo lectura",
        "20",
        T_PACIENTES_PAGE,
        "Odontólogo consulta pacientes en solo lectura",
        "20-pacientes-odontologo-lectura.txt",
        "20-pacientes-odontologo-lectura.txt",
        "M20",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "El mensaje de estado se reemplaza entre acciones sin desmontar la región",
        "21",
        T_PACIENTES_FORM,
        "El mensaje de estado se reemplaza entre acciones sin desmontar la región",
        "21-status-unico.txt",
        "21-status-unico.txt",
        "M21",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Alta de prestación con duración numérica",
        "22",
        T_CATALOGOS_FORM,
        "Alta de prestación con duración numérica",
        "22-prestacion-alta.txt",
        "22-prestacion-alta.txt",
        "M22",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Duración no entera no se envía",
        "23",
        T_CATALOGOS_FORM,
        "Duración no entera no se envía",
        "23-duracion-no-entera.txt",
        "23-duracion-no-entera.txt",
        "M23",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Duración inválida muestra el mensaje literal del backend",
        "24",
        T_CATALOGOS_FORM,
        "Duración inválida muestra el mensaje literal del backend",
        "24-duracion-422.txt",
        "24-duracion-422.txt",
        "M24",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)",
        "25",
        T_CATALOGOS_FORM,
        "Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)",
        "25-catalogo-nombre-duplicado.txt",
        "25-catalogo-nombre-duplicado.txt",
        "M25",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Edición de profesional con matrícula vacía",
        "26",
        T_CATALOGOS_FORM,
        "Edición de profesional con matrícula vacía",
        "26-profesional-edicion.txt",
        "26-profesional-edicion.txt",
        "M26",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Recepción y odontólogo consultan catálogos en solo lectura",
        "27",
        T_CATALOGOS_PAGE,
        "Recepción y odontólogo consultan catálogos en solo lectura",
        "27-catalogos-solo-lectura.txt",
        "27-catalogos-solo-lectura.txt",
        "M27",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Formulario de catálogo como hoja inferior en celular",
        "28",
        T_CATALOGOS_MOBILE,
        "Formulario de catálogo como hoja inferior en celular",
        "28-catalogo-hoja-inferior.txt",
        "28-catalogo-hoja-inferior.txt",
        "M28",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Desactivar un sillón exige confirmación interna",
        "29",
        T_CONFIRM,
        "Desactivar un sillón exige confirmación interna",
        "29-sillon-desactivar.txt",
        "29-sillon-desactivar.txt",
        "M29",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Reactivar una prestación inactiva",
        "30",
        T_CONFIRM,
        "Reactivar una prestación inactiva",
        "30-prestacion-reactivar.txt",
        "30-prestacion-reactivar.txt",
        "M30",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Los tres diálogos muestran su contenido en una tarjeta",
        "31",
        T_DIALOG_MODAL_CARD,
        "Los tres diálogos muestran su contenido en una tarjeta",
        "31-dialogo-tarjeta.txt",
        "31-dialogo-tarjeta.txt",
        "M31",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Las tablas tienen encabezado para la columna de acciones",
        "32",
        T_TABLE_ACTIONS,
        "Las tablas tienen encabezado para la columna de acciones",
        "32-tablas-header-acciones.txt",
        "32-tablas-header-acciones.txt",
        "M32",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible",
        "33",
        T_CATALOGOS_STYLES,
        "Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible",
        "33-tabla-apilada-caption-thead.txt",
        "33-tabla-apilada-caption-thead.txt",
        "M33",
    ),
    Entry(
        "testeable",
        "frontend-catalogs-and-patients",
        "Búsqueda sin resultados muestra un único mensaje",
        "34",
        T_PACIENTES_PAGE,
        "Búsqueda sin resultados muestra un único mensaje",
        "34-pacientes-busqueda-mensaje-unico.txt",
        "34-pacientes-busqueda-mensaje-unico.txt",
        "M34",
    ),
    Entry(
        "visual",
        "frontend-catalogs-and-patients",
        "Pantallas verificadas a 1440, 768 y 390 px",
        "V01",
        visual="C-33-*-{1440,768,390}.png",
    ),
    Entry(
        "visual",
        "frontend-catalogs-and-patients",
        "Diálogo como hoja inferior verificado a 390 px",
        "V02",
        visual="C-33-*-dialogo-390.png",
    ),
    Entry(
        "visual",
        "frontend-foundation",
        "Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px)",
        "V03",
        visual="C-33-appshell-{768,390}.png",
    ),
)

ASSERTION_RE = re.compile(
    r"AssertionError|Error: expect\(|Unable to find|TestingLibraryElementError|failed"
)


def resolve_specs_dir() -> Path:
    if ACTIVE_SPECS_DIR.is_dir():
        return ACTIVE_SPECS_DIR
    archive_base = REPO / "openspec" / "changes" / "archive"
    if archive_base.is_dir():
        matches = sorted(archive_base.glob("*-ui-catalogos-y-pacientes/specs"))
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
        [*VITEST, "list", *C33_TEST_FILES, "--json"],
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
        if file in C33_TEST_FILES:
            tests.append((file, name))
    return tests


def load_mutations_map() -> dict[tuple[str, str], str]:
    path = EVIDENCE / "mutaciones-C-33.py"
    spec = importlib.util.spec_from_file_location("mutaciones_c33", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar mutaciones-C-33.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mutaciones_c33"] = module
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
    lines.append("TRAZABILIDAD C-33 (ui-catalogos-y-pacientes) — SPEC -> TEST -> EVIDENCIA -> MUTACIÓN")
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

    # 3. Validar correspondencia con tests listados por Vitest y mutaciones-C-33.py
    tests = set(listed_tests())
    mutations_map = load_mutations_map()

    for e in testable_entries:
        assert e.test_file and e.test_name
        key = (e.test_file, e.test_name)
        if key not in tests:
            lines.append(f"ERROR: Test no listado por Vitest: {e.test_file} > {e.test_name}")
            print("\n".join(lines), file=sys.stderr)
            return 1
        if mutations_map.get(key) != e.mutation:
            lines.append(
                f"ERROR: Mutación esperada {e.mutation} para {key}, encontrada {mutations_map.get(key)}"
            )
            print("\n".join(lines), file=sys.stderr)
            return 1

    # 4. Validar evidencias RED y GREEN de escenarios
    evidence_errors: list[str] = []
    for e in testable_entries:
        assert e.red_evidence and e.green_evidence
        err_r = check_evidence_file("red-C-33", e.red_evidence, is_red=True)
        if err_r:
            evidence_errors.append(err_r)
        err_g = check_evidence_file("green-C-33", e.green_evidence, is_red=False)
        if err_g:
            evidence_errors.append(err_g)

    if evidence_errors:
        lines.append(f"ERROR: Problemas de evidencia: {evidence_errors}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append("Validación de correspondencia 1:1 (cero tests compartidos): OK")
    lines.append(f"Validación de evidencias RED/GREEN: OK ({len(testable_entries)} escenarios)")

    # 5. Generar listado y tabla de trazabilidad
    table_rows: list[str] = []
    for e in ENTRIES:
        if e.kind == "visual":
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

    update_verify_markdown(table_rows)

    lines.append("=" * 80)
    lines.append(
        f"TOTAL: {len(testable_entries)} testeables (32 tests nuevos + 2 tests existentes modificados (12 y 13)) + {len(visual_entries)} visuales = "
        f"{len(ENTRIES)} escenarios mapeados."
    )
    lines.append("EXITO: Trazabilidad 100% verificada.")
    lines.append("=" * 80)

    text = "\n".join(lines) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
