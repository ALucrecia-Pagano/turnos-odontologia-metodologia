"""Verificación por mutación, reproducible, de los tests nuevos de C-35 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-35.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación (M01-M13) por cada escenario testeable nuevo de C-35: antes de mutar se cuentan los tests
con `vitest list --json` y se exige una correspondencia uno a uno con los 13 tests nuevos (los tests
auxiliares recuperados de cea858b y los históricos del login no llevan mutación).

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-35.txt (salida cruda de Vitest incluida) y actualiza la tabla de verify-C-35.md.
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
OUTPUT = EVIDENCE / "mutaciones-C-35.txt"
VERIFY = EVIDENCE / "verify-C-35.md"
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

# --- Archivos de test de C-35 ---
T_LANDING = "src/features/landing/LandingPage.test.tsx"
T_ROOTGATE = "src/features/landing/RootGate.test.tsx"
T_ACCESO = "src/features/landing/AccesoPage.test.tsx"
T_LOGIN = "src/features/login/LoginPage.translucido.test.tsx"
T_TOKENS = "src/shared/styles/landingTokens.test.ts"
T_DIALOG_THEME = "src/shared/components/DialogTheme.test.ts"
T_NAVIGATION = "src/shared/components/AppShellNavigation.test.tsx"
T_CONTENT = "src/features/landing/landingContent.test.ts"
T_REVEAL = "src/features/landing/RevealSection.test.tsx"

C35_TEST_FILES = (
    T_LANDING,
    T_ROOTGATE,
    T_ACCESO,
    T_LOGIN,
    T_TOKENS,
    T_DIALOG_THEME,
    T_NAVIGATION,
    T_CONTENT,
    T_REVEAL,
)

# Tests auxiliares recuperados de cea858b: no cubren escenarios ni llevan mutación.
# Los 9 tests auxiliares recuperados de cea858b tambien son tests nuevos de C-35: llevan su propia
# mutacion (A01-A09). No hay tests excluidos del recuento uno a uno.
AUX_TESTS: frozenset[tuple[str, str]] = frozenset()

# --- Archivos de producción modificados o creados en C-35 que tocan las mutaciones ---
P_LANDING = "frontend/src/features/landing/LandingPage.tsx"
P_ROOTGATE = "frontend/src/features/landing/RootGate.tsx"
P_REVEAL_TSX = "frontend/src/features/landing/RevealSection.tsx"
P_REVEAL_CSS = "frontend/src/features/landing/RevealSection.module.css"
P_ACCESO = "frontend/src/features/landing/AccesoPage.tsx"
P_LOGIN = "frontend/src/features/login/LoginPage.tsx"
P_TOKENS = "frontend/src/shared/styles/tokens.css"
P_DIALOG_CSS = "frontend/src/shared/components/Dialog.module.css"
P_SHELL_TSX = "frontend/src/shared/components/AppShell.tsx"
P_SHELL_CSS = "frontend/src/shared/components/AppShell.module.css"
P_CONTENT = "frontend/src/features/landing/landingContent.ts"
P_LANDING_CSS = "frontend/src/features/landing/LandingPage.module.css"
P_LOGIN_CSS = "frontend/src/features/login/LoginPage.module.css"

PRODUCTION_FILES = (
    P_LANDING,
    P_ROOTGATE,
    P_REVEAL_TSX,
    P_REVEAL_CSS,
    P_ACCESO,
    P_LOGIN,
    P_TOKENS,
    P_DIALOG_CSS,
    P_SHELL_TSX,
    P_SHELL_CSS,
    P_CONTENT,
    P_LANDING_CSS,
    P_LOGIN_CSS,
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
    # M01 - portada completa para anónimo en /
    Mutation(
        T_LANDING,
        "portada completa para anónimo en /",
        P_LANDING,
        '<Link to="/" className={styles.navLink} aria-current="page">',
        '<Link to="/" className={styles.navLink}>',
    ),
    # M02 - usuario autenticado en / redirige a agenda
    Mutation(
        T_ROOTGATE,
        "usuario autenticado en / redirige a agenda",
        P_ROOTGATE,
        '    if (status === "anonymous") {',
        '    if (status === "anonymous" || status === "authenticated") {',
    ),
    # M03 - secciones editoriales entran con animación lateral al scrollear
    Mutation(
        T_LANDING,
        "secciones editoriales entran con animación lateral al scrollear",
        P_REVEAL_CSS,
        "transform: translateX(var(--landing-reveal-offset));",
        "transform: translateY(var(--landing-reveal-offset));",
    ),
    # M04 - reduced motion desactiva la animación lateral y deja el contenido visible
    Mutation(
        T_LANDING,
        "reduced motion desactiva la animación lateral y deja el contenido visible",
        P_REVEAL_TSX,
        "const canAnimate = !reducedMotion && (observer",
        "const canAnimate = (observer",
    ),
    # M05 - navegación desde las tres tarjetas de rol hacia login
    Mutation(
        T_ACCESO,
        "navegación desde las tres tarjetas de rol hacia login",
        P_ACCESO,
        'to: "/login?rol=odontologo"',
        'to: "/login?rol=odontologia"',
    ),
    # M06 - navegación de retorno con el enlace Volver a Aqua
    Mutation(
        T_ACCESO,
        "navegación de retorno con el enlace Volver a Aqua",
        P_ACCESO,
        '<Link to="/" className={styles.backLink}>',
        '<Link to="/login" className={styles.backLink}>',
    ),
    # M07 - formulario translúcido con etiqueta de rol y envío de credenciales
    Mutation(
        T_LOGIN,
        "formulario translúcido en /login con etiqueta de rol y envío de credenciales",
        P_LOGIN,
        "? (ROLE_LABELS.get(roleParam) ?? null)",
        "? null",
    ),
    # M08 - un ?rol desconocido muestra su valor crudo como etiqueta
    Mutation(
        T_LOGIN,
        "parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter",
        P_LOGIN,
        "ROLE_LABELS.get(roleParam) ?? null",
        "ROLE_LABELS.get(roleParam) ?? roleParam",
    ),
    # M09 - no mostrar el aviso cuando state.expired === true
    Mutation(
        T_LOGIN,
        "cierre de sesión y preservación del mensaje literal de sesión vencida",
        P_LOGIN,
        ".expired === true;",
        ".expired === false;",
    ),
    # M10 - tokens de layout y contraste AA de superficies
    Mutation(
        T_TOKENS,
        "tokens de layout y contraste AA de superficies",
        P_TOKENS,
        "--landing-hero-min-height: 60vh;",
        "--landing-hero-min-height: 50vh;",
    ),
    # M11 - eliminar el bloque @supports not de Dialog.module.css
    Mutation(
        T_DIALOG_THEME,
        "fallback sólido sin soporte de backdrop-filter",
        P_DIALOG_CSS,
        "@supports not (backdrop-filter: blur(1px)) {\n  .dialog::backdrop {\n    background: var(--scrim-navy-strong);\n  }\n}",
        "",
    ),
    # M12 - quitar aria-current="page" del enlace Agenda
    Mutation(
        T_NAVIGATION,
        "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        P_SHELL_TSX,
        "                    to={item.path}\n",
        '                    to={item.path}\n                    aria-current="false"\n',
    ),
    # M13 - restaurar el borde en .badge
    Mutation(
        T_NAVIGATION,
        "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        P_SHELL_CSS,
        ".badge {\n  display: block;\n",
        ".badge {\n  display: block;\n  border: 1px solid var(--color-border);\n",
    ),
    # A01-A03 - tests auxiliares de landingTokens.test.ts
    Mutation(
        T_TOKENS,
        "define los dos tokens de layout",
        P_TOKENS,
        "--landing-content-max-width: 1120px;",
        "--landing-content-max-width: 1120;",
    ),
    Mutation(
        T_TOKENS,
        "la portada usa los tokens de layout",
        P_LANDING_CSS,
        "min-height: max(var(--landing-hero-min-height), 100svh);",
        "min-height: max(60vh, 100svh);",
    ),
    Mutation(
        T_TOKENS,
        "no agrega colores nuevos",
        P_TOKENS,
        "  --color-navy-deep: #011C40;\n",
        "  --color-navy-deep: #011C40;\n  --color-extra: #123456;\n",
    ),
    # A04-A06 - tests auxiliares de landingContent.test.ts
    Mutation(
        T_CONTENT,
        "el equipo coincide con el seed",
        P_CONTENT,
        'name: "Dra. Paula Benítez",',
        'name: "Dra. Paula Benitez",',
    ),
    Mutation(
        T_CONTENT,
        "los servicios y duraciones coinciden con el seed",
        P_CONTENT,
        "durationMinutes: 90,",
        "durationMinutes: 80,",
    ),
    Mutation(
        T_CONTENT,
        "horarios y contacto son ficticios y coinciden con el seed",
        P_CONTENT,
        'phone: "(0261) 555-0101",',
        'phone: "(0261) 555-0102",',
    ),
    # A07-A09 - tests auxiliares de RevealSection.test.tsx
    Mutation(
        T_REVEAL,
        "sin IntersectionObserver queda revelada y su contenido es visible",
        P_REVEAL_TSX,
        "useState(!canAnimate);",
        "useState(false);",
    ),
    Mutation(
        T_REVEAL,
        "con observador inyectado pasa de pendiente a revelada y limpia al desmontar",
        P_REVEAL_TSX,
        "    return instance.observe(section, () => {",
        "    instance.observe(section, () => {",
    ),
    Mutation(
        T_REVEAL,
        "con movimiento reducido no queda pendiente y el contenido está en el DOM",
        P_REVEAL_TSX,
        'data-reveal={revealed ? "revealed" : "pending"}',
        'data-reveal={revealed && !reducedMotion ? "revealed" : "pending"}',
    ),
    # M14-M17 - tests adicionales del ajuste de diseño (no son escenarios del spec)
    Mutation(
        T_NAVIGATION,
        "los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces",
        P_SHELL_CSS,
        "  background: transparent;\n  border: 0;\n",
        "  background: transparent;\n",
    ),
    Mutation(
        T_REVEAL,
        "from=right desplaza en positivo y from=left en negativo",
        P_REVEAL_CSS,
        "translateX(calc(-1 * var(--landing-reveal-offset)));",
        "translateX(var(--landing-reveal-offset));",
    ),
    Mutation(
        T_LANDING,
        "las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha",
        P_LANDING,
        'from="right">\n            <section className={`${styles.section} ${styles.sectionRight}`} aria-labelledby="seccion-servicios">',
        'from="left">\n            <section className={`${styles.section} ${styles.sectionRight}`} aria-labelledby="seccion-servicios">',
    ),
    Mutation(
        T_LANDING,
        "el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único",
        P_LANDING_CSS,
        "  background: transparent;\n  border-bottom: 1px solid var(--border-on-navy-strong);",
        "  background: var(--color-primary);\n  border-bottom: 1px solid var(--border-on-navy-strong);",
    ),
    # M18-M19 - tests adicionales de los ajustes del login (autofill y alerta oscura)
    Mutation(
        T_LOGIN,
        "los campos del login conservan la superficie oscura cuando el navegador los autocompleta",
        P_LOGIN_CSS,
        ".input:autofill {\n  box-shadow: 0 0 0 1000px var(--color-navy-deep) inset;",
        ".input:autofill {\n  box-shadow: 0 0 0 1000px var(--color-surface) inset;",
    ),
    Mutation(
        T_LOGIN,
        "el alerta de error del login usa la variante oscura con contraste AA sobre la superficie translúcida y el fallback",
        P_LOGIN_CSS,
        "  color: var(--alert-on-navy-text);\n  background: var(--alert-on-navy-bg);",
        "  color: var(--color-danger-text);\n  background: var(--alert-on-navy-bg);",
    ),
)


def mutation_id(index: int) -> str:
    """M01-M13 escenarios; A01-A09 auxiliares recuperados; M14-M17 tests adicionales del ajuste de diseño."""
    if index <= 13:
        return f"M{index:02d}"
    if index <= 22:
        return f"A{index - 13:02d}"
    return f"M{index - 9:02d}"


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
        if file in C35_TEST_FILES and (file, name) not in AUX_TESTS:
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
            f"tests nuevos de C-35 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
            f"una por cada uno de los {total_tests} tests de C-35."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-35.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-35 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C35_TEST_FILES))
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
                f"| {mutation_id(index)} | `{cell(mutation.test_name)}` | `{mutation.file}` | `{cell(changed)}` | `{cell(failure)}` |"
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
