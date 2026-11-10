"""Verificacion por mutacion, reproducible, de los tests de C-34 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-34.py [--check]

Cada mutacion es (archivo de test, nombre del test, archivo de produccion,
texto_original, texto_mutado). Hay UNA mutacion por cada test nuevo de C-34:
antes de mutar se cuentan los tests con `vitest list --json` y se exige una
correspondencia uno a uno con los 15 tests nuevos.

Por cada mutacion: comprueba que el original aparezca exactamente una vez y que el
mutante cambie el archivo (respetando LF o CRLF), aplica la mutacion, corre Vitest
solo para ese test (`vitest run <archivo> -t <nombre>$`), restaura el archivo en un
finally y vuelve a correr el test, que tiene que volver a verde.

Una mutacion es INVALIDA si su test no la detecta con una afirmacion propia:
- el archivo de test no carga (error de import, de compilacion o SyntaxError);
- no se ejecuto exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u
  otro error que no sea AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no esta en un archivo *.test.ts(x).

Genera mutaciones-C-34.txt (salida cruda de Vitest incluida) y regenera la tabla
de verify-C-34.md si existe. Termina con codigo 0 solo si todas las mutaciones
hicieron fallar su test, ninguna es INVALIDA y el SHA-256 del codigo de produccion
no cambio.
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
OUTPUT = EVIDENCE / "mutaciones-C-34.txt"
VERIFY = EVIDENCE / "verify-C-34.md"
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

T_AQUA = "src/shared/styles/aquaPalette.test.ts"
T_FONTS = "src/shared/styles/fonts.test.ts"
T_APP_SHELL_BRAND = "src/shared/components/AppShellBrand.test.tsx"
T_LOGIN_BRAND = "src/features/login/LoginBrand.test.tsx"
T_LOGIN_CAROUSEL = "src/features/login/LoginCarousel.test.tsx"
T_README = "src/test/readmeCredits.test.ts"

C34_TEST_FILES = (T_AQUA, T_FONTS, T_APP_SHELL_BRAND, T_LOGIN_BRAND, T_LOGIN_CAROUSEL, T_README)

P_TOKENS = "frontend/src/shared/styles/tokens.css"
P_RESET = "frontend/src/shared/styles/reset.css"
P_MAIN = "frontend/src/main.tsx"
P_APP_SHELL = "frontend/src/shared/components/AppShell.tsx"
P_LOGIN_PAGE = "frontend/src/features/login/LoginPage.tsx"
P_LOGIN_CAROUSEL = "frontend/src/features/login/LoginCarousel.tsx"
P_README = "README.md"


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
    Mutation(
        T_AQUA,
        "define los tokens semánticos con los valores del design",
        P_TOKENS,
        "  --color-primary: #26658C;",
        "  --color-primary: #26658D;",
    ),
    Mutation(
        T_AQUA,
        "mantiene los contrastes de texto del design",
        P_TOKENS,
        "  --color-text: #011C40;",
        "  --color-text: #011C41;",
    ),
    Mutation(
        T_FONTS,
        "define Jost para títulos y Manrope para texto con fallback al system stack",
        P_TOKENS,
        '"Jost Variable"',
        '"Jost"',
    ),
    Mutation(
        T_FONTS,
        "el body conserva la base y usa Manrope después",
        P_RESET,
        "  font-family: var(--font-family-base);\n  font-family: var(--font-family-body);",
        "  font-family: var(--font-family-body);",
    ),
    Mutation(
        T_FONTS,
        "declara las dependencias y las importa antes de los estilos en el entry point",
        P_MAIN,
        'import "@fontsource-variable/jost";\nimport "@fontsource-variable/manrope";\nimport "./shared/styles/tokens.css";',
        'import "./shared/styles/tokens.css";\nimport "@fontsource-variable/jost";\nimport "@fontsource-variable/manrope";',
    ),
    Mutation(
        T_FONTS,
        "no usa URLs de Google Fonts ni CDNs externos en src",
        P_MAIN,
        'import "@fontsource-variable/jost";',
        'import "https://fonts.googleapis.com/css2?family=Jost";',
    ),
    Mutation(
        T_APP_SHELL_BRAND,
        "muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica",
        P_APP_SHELL,
        '<img src={logoAquaOscuro} alt="" className={styles.brandLogo} />',
        '<img src={logoAquaOscuro} alt="Aqua" className={styles.brandLogo} />',
    ),
    Mutation(
        T_APP_SHELL_BRAND,
        "ubica logo, Aqua y subtítulo en la marca y el subtítulo usa la clase oculta en 768 px",
        P_APP_SHELL,
        '<div className={styles.brand} data-brand="aqua">',
        '<div className={styles.brand} data-brand="otro">',
    ),
    Mutation(
        T_LOGIN_BRAND,
        "muestra el logo claro, el heading accesible y la bajada",
        P_LOGIN_PAGE,
        'alt="Aqua — Clínica Odontológica"',
        'alt="Aqua"',
    ),
    Mutation(
        T_LOGIN_BRAND,
        "renderiza sin window.matchMedia, usa reduced motion falso y permite avanzar el carrusel",
        P_LOGIN_CAROUSEL,
        '  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {\n    return false;\n  }',
        '  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {\n    return true;\n  }',
    ),
    Mutation(
        T_LOGIN_CAROUSEL,
        "inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta",
        P_LOGIN_CAROUSEL,
        "setActiveIndex((current) => (current + 1) % SLIDES.length);",
        "setActiveIndex((current) => (current + 2) % SLIDES.length);",
    ),
    Mutation(
        T_LOGIN_CAROUSEL,
        "pausa y reanuda el avance sin aria-pressed",
        P_LOGIN_CAROUSEL,
        "    if (paused || reducedMotion) {",
        "    if (reducedMotion) {",
    ),
    Mutation(
        T_LOGIN_CAROUSEL,
        "reduced motion desactiva la rotación y el Ken Burns",
        P_LOGIN_CAROUSEL,
        "  const reducedMotion = prefersReducedMotion ?? detectPrefersReducedMotion();",
        "  const reducedMotion = false;",
    ),
    Mutation(
        T_LOGIN_CAROUSEL,
        "cancela el ticker al desmontar",
        P_LOGIN_CAROUSEL,
        "    return ticker(() => {\n      setActiveIndex((current) => (current + 1) % SLIDES.length);\n    });",
        "    ticker(() => {\n      setActiveIndex((current) => (current + 1) % SLIDES.length);\n    });",
    ),
    Mutation(
        T_LOGIN_CAROUSEL,
        "muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa",
        P_LOGIN_CAROUSEL,
        '            aria-hidden="true"\n            data-slide-index={index}',
        '            aria-hidden="false"\n            data-slide-index={index}',
    ),
    Mutation(
        T_README,
        "documenta las fotografías, el logo y la licencia de las tipografías",
        P_README,
        "SIL Open Font License 1.1",
        "SIL Open Font License 1.0",
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
    expected_names = {m.test_name for m in MUTATIONS}
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
        if file in C34_TEST_FILES and name in expected_names:
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
            f"tests nuevos de C-34 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
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
            f"una por cada uno de los {total_tests} tests de C-34."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-34.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-34 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C34_TEST_FILES))
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
