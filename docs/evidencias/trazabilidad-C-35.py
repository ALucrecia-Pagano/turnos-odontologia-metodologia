"""Trazabilidad de C-35: cada escenario de las specs delta a su test, evidencias y mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-35.py

Lee los escenarios de los tres spec.md del change `ui-portada-y-acceso`
(frontend-landing, frontend-auth-session y frontend-foundation), exige 24 escenarios
(13 nuevos + 5 históricos + 6 visuales) y genera trazabilidad-C-35.txt y la matriz de
verify-C-35.md (entre las marcas trazabilidad:inicio / trazabilidad:fin).

Termina con código distinto de 0 si:
  (a) dos escenarios comparten el mismo test (archivo + nombre);
  (b) un escenario nuevo no tiene test listado por Vitest, evidencia red-C-35/NN-*.txt,
      evidencia green-C-35/NN-*.txt o mutación definida en mutaciones-C-35.py;
  (c) un escenario histórico no encuentra, con búsqueda literal, su test en LoginPage.test.tsx;
  (d) el total no es 13 nuevos + 5 históricos + 6 visuales = 24, o un escenario del spec no está
      mapeado, o el mapa tiene un escenario que el spec no declara;
  (e) alguno de los 15 tests auxiliares o adicionales no está listado por Vitest o no tiene mutación (A01-A09, M14-M19).
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
OUTPUT = EVIDENCE / "trazabilidad-C-35.txt"
VERIFY = EVIDENCE / "verify-C-35.md"
SPECS_DIR = REPO / "openspec" / "changes" / "ui-portada-y-acceso" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]
LOGIN_TEST = FRONTEND / "src" / "features" / "login" / "LoginPage.test.tsx"

EXPECTED_NEW = 13
EXPECTED_HISTORIC = 5
EXPECTED_VISUAL = 6

T_LANDING = "src/features/landing/LandingPage.test.tsx"
T_ROOTGATE = "src/features/landing/RootGate.test.tsx"
T_ACCESO = "src/features/landing/AccesoPage.test.tsx"
T_LOGIN = "src/features/login/LoginPage.translucido.test.tsx"
T_LOGIN_EXISTING = "src/features/login/LoginPage.test.tsx"
T_TOKENS = "src/shared/styles/landingTokens.test.ts"
T_DIALOG_THEME = "src/shared/components/DialogTheme.test.ts"
T_NAVIGATION = "src/shared/components/AppShellNavigation.test.tsx"


@dataclass(frozen=True)
class Entry:
    kind: str  # "nuevo" | "historico" | "visual"
    spec: str
    scenario: str
    number: str  # NN para nuevos, H1..H5, V1..V6
    test_file: str | None = None
    test_name: str | None = None
    evidence: str | None = None  # NN-nombre para nuevos
    visual: str | None = None  # patrón de capturas


ENTRIES: tuple[Entry, ...] = (
    Entry("nuevo", "frontend-landing", "Portada completa para anónimo en /", "01", T_LANDING,
          "portada completa para anónimo en /", "01-portada-anonimo"),
    Entry("nuevo", "frontend-landing", "Usuario autenticado en / redirige a agenda", "02", T_ROOTGATE,
          "usuario autenticado en / redirige a agenda", "02-portada-autenticado-redirect"),
    Entry("nuevo", "frontend-landing", "Secciones editoriales entran con animación lateral al scrollear", "03",
          T_LANDING, "secciones editoriales entran con animación lateral al scrollear",
          "03-secciones-reveal-lateral"),
    Entry("nuevo", "frontend-landing",
          "Reduced motion desactiva la animación lateral y deja el contenido visible", "04", T_LANDING,
          "reduced motion desactiva la animación lateral y deja el contenido visible", "04-reduced-motion"),
    Entry("nuevo", "frontend-landing", "Navegación desde las tres tarjetas de rol hacia login", "05", T_ACCESO,
          "navegación desde las tres tarjetas de rol hacia login", "05-acceso-tarjetas"),
    Entry("nuevo", "frontend-landing", "Navegación de retorno con el enlace Volver a Aqua", "06", T_ACCESO,
          "navegación de retorno con el enlace Volver a Aqua", "06-acceso-volver"),
    Entry("nuevo", "frontend-auth-session",
          "Formulario translúcido en /login con etiqueta de rol y envío de credenciales", "07", T_LOGIN,
          "formulario translúcido en /login con etiqueta de rol y envío de credenciales",
          "07-login-translucido-rol"),
    Entry("nuevo", "frontend-auth-session",
          "Parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter", "08",
          T_LOGIN,
          "parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter",
          "08-login-rol-invalido-fallback"),
    Entry("nuevo", "frontend-auth-session",
          "Cierre de sesión y preservación del mensaje literal de sesión vencida", "09", T_LOGIN,
          "cierre de sesión y preservación del mensaje literal de sesión vencida", "09-login-sesion-vencida"),
    Entry("nuevo", "frontend-foundation", "Tokens de layout y contraste AA de superficies", "10", T_TOKENS,
          "tokens de layout y contraste AA de superficies", "10-tokens-contraste"),
    Entry("nuevo", "frontend-foundation", "Fallback sólido sin soporte de backdrop-filter", "11",
          T_DIALOG_THEME, "fallback sólido sin soporte de backdrop-filter", "11-fallback-solido-modales"),
    Entry("nuevo", "frontend-foundation",
          "Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px", "12", T_NAVIGATION,
          "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
          "12-appshell-nav-activa"),
    Entry("nuevo", "frontend-foundation",
          "Ítems deshabilitados con Próximamente conservan semántica y accesibilidad", "13", T_NAVIGATION,
          "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
          "13-appshell-proximamente"),
    Entry("historico", "frontend-auth-session", "Login correcto del administrador", "H1", T_LOGIN_EXISTING,
          "login correcto del administrador"),
    Entry("historico", "frontend-auth-session", "Login correcto de recepción y del odontólogo", "H2",
          T_LOGIN_EXISTING, "login correcto de recepción y del odontólogo"),
    Entry("historico", "frontend-auth-session", "Credenciales inválidas con mensaje genérico", "H3",
          T_LOGIN_EXISTING, "credenciales inválidas con mensaje genérico"),
    Entry("historico", "frontend-auth-session", "Envío en curso y doble submit", "H4", T_LOGIN_EXISTING,
          "envío en curso y doble submit"),
    Entry("historico", "frontend-auth-session", "Accesibilidad del formulario", "H5", T_LOGIN_EXISTING,
          "accesibilidad del formulario"),
    Entry("visual", "frontend-landing", "Adaptabilidad de la portada en 1440, 768 y 390 px", "V1",
          visual="capturas/C-35-portada-*.png"),
    Entry("visual", "frontend-landing",
          "Secciones editoriales intercaladas a ancho parcial en 1440 px y a ancho completo en 768 y 390 px", "V2",
          visual="capturas/C-35-secciones-*.png"),
    Entry("visual", "frontend-landing", "Adaptabilidad de las tarjetas de acceso en 1440, 768 y 390 px", "V3",
          visual="capturas/C-35-acceso-*.png"),
    Entry("visual", "frontend-auth-session", "Adaptabilidad de /login en 1440, 768 y 390 px", "V4",
          visual="capturas/C-35-login-*.png"),
    Entry("visual", "frontend-foundation",
          "Superficie clara suave de modales verificada a 1440, 768 y 390 px", "V5",
          visual="capturas/C-35-modales-*.png"),
    Entry("visual", "frontend-foundation",
          "Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px)", "V6",
          visual="capturas/C-35-appshell-*.png"),
)

SCENARIO = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.MULTILINE)
AUXILIARY: tuple[tuple[str, str], ...] = (
    ("src/shared/styles/landingTokens.test.ts", "define los dos tokens de layout"),
    ("src/shared/styles/landingTokens.test.ts", "la portada usa los tokens de layout"),
    ("src/shared/styles/landingTokens.test.ts", "no agrega colores nuevos"),
    ("src/features/landing/landingContent.test.ts", "el equipo coincide con el seed"),
    ("src/features/landing/landingContent.test.ts", "los servicios y duraciones coinciden con el seed"),
    ("src/features/landing/landingContent.test.ts", "horarios y contacto son ficticios y coinciden con el seed"),
    ("src/features/landing/RevealSection.test.tsx", "sin IntersectionObserver queda revelada y su contenido es visible"),
    (
        "src/features/landing/RevealSection.test.tsx",
        "con observador inyectado pasa de pendiente a revelada y limpia al desmontar",
    ),
    (
        "src/features/landing/RevealSection.test.tsx",
        "con movimiento reducido no queda pendiente y el contenido está en el DOM",
    ),
    # Tests adicionales del ajuste de diseño (no son escenarios; cada uno con su mutación M14-M17)
    (
        "src/shared/components/AppShellNavigation.test.tsx",
        "los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces",
    ),
    ("src/features/landing/RevealSection.test.tsx", "from=right desplaza en positivo y from=left en negativo"),
    (
        "src/features/landing/LandingPage.test.tsx",
        "las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha",
    ),
    (
        "src/features/landing/LandingPage.test.tsx",
        "el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único",
    ),
    # Tests adicionales de los ajustes del login (M18-M19)
    (
        "src/features/login/LoginPage.translucido.test.tsx",
        "los campos del login conservan la superficie oscura cuando el navegador los autocompleta",
    ),
    (
        "src/features/login/LoginPage.translucido.test.tsx",
        "el alerta de error del login usa la variante oscura con contraste AA sobre la superficie translúcida y el fallback",
    ),
)

ASSERTION = re.compile(r"AssertionError|Error: expect\(")


def spec_scenarios() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for spec_file in sorted(SPECS_DIR.glob("*/spec.md")):
        capability = spec_file.parent.name
        for title in SCENARIO.findall(spec_file.read_text(encoding="utf-8")):
            found.append((capability, title))
    return found


def vitest_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env


def listed_tests() -> set[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=vitest_env(),
        timeout=300,
        check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    tests: set[tuple[str, str]] = set()
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        tests.add((file, entry["name"].split(" > ")[-1]))
    return tests


def mutation_ids() -> dict[tuple[str, str], str]:
    path = EVIDENCE / "mutaciones-C-35.py"
    spec = importlib.util.spec_from_file_location("mutaciones_c35", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar mutaciones-C-35.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mutaciones_c35"] = module
    spec.loader.exec_module(module)
    return {(m.test_file, m.test_name): module.mutation_id(index) for index, m in enumerate(module.MUTATIONS, start=1)}


def evidence_problem(kind: str, name: str) -> str | None:
    path = EVIDENCE / f"{kind}-C-35" / f"{name}.txt"
    if not path.is_file():
        return f"falta {kind}-C-35/{name}.txt"
    raw = path.read_bytes()
    if raw[:3] == b"\xef\xbb\xbf" or raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return f"{kind}-C-35/{name}.txt tiene BOM o es UTF-16"
    text = raw.decode("utf-8", errors="replace")
    if kind == "red" and not ASSERTION.search(text):
        return f"red-C-35/{name}.txt no muestra un fallo por aserción"
    if kind == "green" and not re.search(r"Tests\s+\d+ passed", text):
        return f"green-C-35/{name}.txt no muestra tests en verde"
    if kind == "green" and re.search(r"\d+ failed", text):
        return f"green-C-35/{name}.txt contiene tests fallidos"
    return None


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def main() -> int:
    problems: list[str] = []

    declared = spec_scenarios()
    mapped = {(e.spec, e.scenario) for e in ENTRIES}
    for item in declared:
        if item not in mapped:
            problems.append(f"(d) escenario del spec sin mapear: {item[0]} / {item[1]}")
    for item in sorted(mapped - set(declared)):
        problems.append(f"(d) escenario mapeado que el spec no declara: {item[0]} / {item[1]}")
    if len(declared) != len(set(declared)):
        problems.append("(d) hay escenarios repetidos en los specs")

    counts = Counter(e.kind for e in ENTRIES)
    if (counts["nuevo"], counts["historico"], counts["visual"]) != (
        EXPECTED_NEW,
        EXPECTED_HISTORIC,
        EXPECTED_VISUAL,
    ) or len(declared) != EXPECTED_NEW + EXPECTED_HISTORIC + EXPECTED_VISUAL:
        problems.append(
            f"(d) total esperado 13 + 5 + 6 = 24; hay {counts['nuevo']} + {counts['historico']} + "
            f"{counts['visual']} = {len(ENTRIES)} mapeados y {len(declared)} declarados en los specs"
        )

    nodes = [(e.test_file, e.test_name) for e in ENTRIES if e.test_file is not None]
    for node, times in Counter(nodes).items():
        if times > 1:
            problems.append(f"(a) {times} escenarios comparten el test {node[0]} > {node[1]}")

    listed = listed_tests()
    mutations = mutation_ids()
    login_source = LOGIN_TEST.read_text(encoding="utf-8")

    rows: list[str] = []
    lines: list[str] = []
    for entry in ENTRIES:
        if entry.kind == "nuevo":
            assert entry.test_file and entry.test_name and entry.evidence
            node = (entry.test_file, entry.test_name)
            if node not in listed:
                problems.append(f"(b) {entry.number}: Vitest no lista el test {node[0]} > {node[1]}")
            for kind in ("red", "green"):
                found = evidence_problem(kind, entry.evidence)
                if found:
                    problems.append(f"(b) {entry.number}: {found}")
            mutation = mutations.get(node)
            if mutation is None:
                problems.append(f"(b) {entry.number}: sin mutación en mutaciones-C-35.py para {node[1]}")
            test_cell = f"`{entry.test_file}` > {entry.test_name}"
            mutation_cell = mutation or "SIN MUTACIÓN"
            evidence_cell = f"red/green-C-35/{entry.evidence}.txt"
            lines.append(f"{entry.number} [nuevo] {entry.scenario} -> {test_cell} | {mutation_cell} | {evidence_cell}")
        elif entry.kind == "historico":
            assert entry.test_file and entry.test_name
            if f'it("{entry.test_name}"' not in login_source:
                problems.append(
                    f"(c) {entry.number}: no se encuentra literalmente it(\"{entry.test_name}\") en LoginPage.test.tsx"
                )
            test_cell = f"`{entry.test_file}` > {entry.test_name}"
            mutation_cell = "— (test existente)"
            evidence_cell = "green-C-35/login-regresion.txt"
            lines.append(f"{entry.number} [historico] {entry.scenario} -> {test_cell} | {evidence_cell}")
        else:
            test_cell = "Captura (fase 9)"
            mutation_cell = "—"
            evidence_cell = entry.visual or ""
            lines.append(f"{entry.number} [visual] {entry.scenario} -> {evidence_cell}")
        rows.append(
            f"| {entry.number} | {entry.spec} | {cell(entry.scenario)} | {entry.kind} | {cell(test_cell)} | "
            f"{mutation_cell} | {evidence_cell} |"
        )

    aux_rows: list[str] = []
    aux_lines: list[str] = []
    for node in AUXILIARY:
        if node not in listed:
            problems.append(f"(e) test auxiliar no listado por Vitest: {node[0]} > {node[1]}")
        mutation = mutations.get(node)
        if mutation is None:
            problems.append(f"(e) test auxiliar sin mutación: {node[0]} > {node[1]}")
        if node in nodes:
            problems.append(f"(e) test auxiliar usado como escenario: {node[0]} > {node[1]}")
        aux_lines.append(f"[auxiliar] {node[0]} > {node[1]} | {mutation or 'SIN MUTACIÓN'}")
        aux_rows.append(f"| {mutation or 'SIN MUTACIÓN'} | `{node[0]}` | {cell(node[1])} |")

    lines_out = [
        "Salida generada por docs/evidencias/trazabilidad-C-35.py. No editar a mano.",
        f"escenarios declarados en los specs: {len(declared)}",
        f"mapeados: {len(ENTRIES)} = {counts['nuevo']} nuevos + {counts['historico']} históricos + {counts['visual']} visuales",
        "",
        *lines,
        "",
        f"tests auxiliares (9 recuperados de cea858b) y adicionales (4 del ajuste de diseño y 2 del login); no son escenarios, cada uno con su mutación: {len(AUXILIARY)}",
        *aux_lines,
        "",
        f"problemas: {len(problems)}",
        *[f"  - {problem}" for problem in problems],
        f"RESULTADO: {'OK' if not problems else 'FALLA'}",
    ]
    OUTPUT.write_text("\n".join(lines_out) + "\n", encoding="utf-8", newline="\n")

    table = "\n".join(
        [
            "| # | Spec | Escenario | Tipo | Test | Mutación | Evidencia |",
            "|---|------|-----------|------|------|----------|-----------|",
            *rows,
            "",
            "Tests auxiliares y adicionales (no son escenarios; 24 = 13 + 5 + 6 no cambia):",
            "",
            "| Mutación | Archivo | Test |",
            "|----------|---------|------|",
            *aux_rows,
        ]
    )
    if VERIFY.exists():
        verify = VERIFY.read_text(encoding="utf-8")
        start = verify.find(TABLE_START)
        end = verify.find(TABLE_END)
        if start != -1 and end != -1:
            VERIFY.write_text(
                f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
                encoding="utf-8",
                newline="\n",
            )

    print("\n".join(lines_out))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
