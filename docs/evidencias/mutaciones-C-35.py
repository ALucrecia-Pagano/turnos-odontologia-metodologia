"""Verificacion por mutacion, reproducible, de los tests de C-35 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-35.py [--check]

Cada mutacion es (archivo de test, nombre del test, archivo de produccion,
texto_original, texto_mutado). Hay UNA mutacion por cada test nuevo de C-35:
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

Genera mutaciones-C-35.txt (salida cruda de Vitest incluida) y regenera la tabla
de verify-C-35.md si existe. Termina con codigo 0 solo si todas las mutaciones
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

T_LANDING_CONTENT = "src/features/landing/landingContent.test.ts"
T_LANDING_TOKENS = "src/shared/styles/landingTokens.test.ts"
T_LANDING = "src/features/landing/LandingPage.test.tsx"
T_LOGIN_DIALOG = "src/features/landing/LoginDialog.test.tsx"
T_DIALOG = "src/shared/components/Dialog.test.tsx"
T_REVEAL = "src/features/landing/RevealSection.test.tsx"

C35_TEST_FILES = (
    T_LANDING_CONTENT,
    T_LANDING_TOKENS,
    T_LANDING,
    T_LOGIN_DIALOG,
    T_DIALOG,
    T_REVEAL,
)

P_TOKENS = "frontend/src/shared/styles/tokens.css"
P_LANDING_CSS = "frontend/src/features/landing/LandingPage.module.css"
P_LANDING_CONTENT = "frontend/src/features/landing/landingContent.ts"
P_LANDING_PAGE = "frontend/src/features/landing/LandingPage.tsx"
P_LOGIN_DIALOG = "frontend/src/features/landing/LoginDialog.tsx"
P_DIALOG = "frontend/src/shared/components/Dialog.tsx"
P_REVEAL = "frontend/src/features/landing/RevealSection.tsx"
P_LOGIN_CAROUSEL = "frontend/src/features/login/LoginCarousel.tsx"


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
        T_LANDING_CONTENT,
        "el equipo coincide con el seed",
        P_LANDING_CONTENT,
        '"Dr. Martín Sosa",',
        '"Dr. Martín Sosa ",',
    ),
    Mutation(
        T_LANDING_CONTENT,
        "los servicios y duraciones coinciden con el seed",
        P_LANDING_CONTENT,
        "    durationMinutes: 45,",
        "    durationMinutes: 46,",
    ),
    Mutation(
        T_LANDING_CONTENT,
        "horarios y contacto son ficticios y coinciden con el seed",
        P_LANDING_CONTENT,
        '  phone: "(0261) 555-0101",',
        '  phone: "(0261) 555-0102",',
    ),
    Mutation(
        T_LANDING_TOKENS,
        "define los dos tokens de layout",
        P_TOKENS,
        "  --landing-hero-min-height: 60vh;",
        "  --landing-hero-min-height: 61vh;",
    ),
    Mutation(
        T_LANDING_TOKENS,
        "la portada usa los tokens de layout",
        P_LANDING_CSS,
        "  min-height: var(--landing-hero-min-height);",
        "  min-height: 60vh;",
    ),
    Mutation(
        T_LANDING_TOKENS,
        "no agrega colores nuevos",
        P_TOKENS,
        "  --landing-content-max-width: 1120px;",
        "  --landing-content-max-width: 1120px;\n  --landing-danger: #ff0000;",
    ),
    Mutation(
        T_LANDING,
        "muestra la marca una sola vez, la bajada, el lead y el CTA",
        P_LANDING_PAGE,
        '<p className={styles.tagline}>Claridad en cada cuidado.</p>',
        '<p className={styles.tagline} style={{ display: "none" }}>Claridad en cada cuidado.</p>',
    ),
    Mutation(
        T_LANDING,
        "marca el sitio y los datos de contacto como demostración",
        P_LANDING_PAGE,
        '<p className={styles.demoNote}>{demoContactNote}</p>',
        '<p className={styles.demoNote} style={{ display: "none" }}>{demoContactNote}</p>',
    ),
    Mutation(
        T_LANDING,
        "muestra las cuatro secciones informativas visibles sin IntersectionObserver",
        P_REVEAL,
        "const [revealed, setRevealed] = useState(!canAnimate);",
        "const [revealed, setRevealed] = useState(false);",
    ),
    Mutation(
        T_LANDING,
        "reutiliza el carrusel de cinco fotos y su botón de pausa",
        P_LOGIN_CAROUSEL,
        "const SLIDES = [hero1, hero2, hero3, hero4, hero5];",
        "const SLIDES = [hero1, hero2, hero3, hero4];",
    ),
    Mutation(
        T_LANDING,
        "abre el acceso al entrar y lo reabre con el CTA",
        P_LANDING_PAGE,
        "          setIsLoginOpen(false);",
        "          setIsLoginOpen(true);",
    ),
    Mutation(
        T_LANDING,
        "mantiene un único botón Ingresar y un CTA accesible sin ocultar",
        P_LANDING_PAGE,
        '            ref={ctaRef}\n            type="button"\n            className={styles.cta}',
        '            ref={ctaRef}\n            type="button"\n            tabIndex={-1}\n            className={styles.cta}',
    ),
    Mutation(
        T_LANDING,
        "LoginPage monta la portada y conserva el aviso de sesión vencida",
        "frontend/src/features/login/LoginPage.tsx",
        "initialNotice={showExpiredMessage ? SESSION_EXPIRED_MESSAGE : null}",
        'initialNotice={showExpiredMessage ? "Aviso distinto" : null}',
    ),
    Mutation(
        T_LOGIN_DIALOG,
        "abre con el diálogo, el heading, el formulario y el botón para recorrer la clínica",
        P_DIALOG,
        "      aria-labelledby={labelledBy}",
        "      aria-labelledby={undefined}",
    ),
    Mutation(
        T_LOGIN_DIALOG,
        "cierra el diálogo con el botón Ver la clínica",
        P_LOGIN_DIALOG,
        '<button type="button" className={styles.close} onClick={onClose}>',
        '<button type="button" className={styles.close} onClick={() => undefined}>',
    ),
    Mutation(
        T_LOGIN_DIALOG,
        "muestra el aviso de sesión vencida dentro del formulario",
        P_LOGIN_DIALOG,
        "          <LoginForm onSubmit={onLogin} initialNotice={initialNotice} />",
        '          <LoginForm onSubmit={onLogin} initialNotice={initialNotice === null ? null : "Otro aviso"} />',
    ),
    Mutation(
        T_LOGIN_DIALOG,
        "enfoca Usuario al abrir",
        P_LOGIN_DIALOG,
        '    document.getElementById("login-username")?.focus();',
        '    void document.getElementById("login-username");',
    ),
    Mutation(
        T_LOGIN_DIALOG,
        "bloquea el overflow del body mientras está abierto y lo restaura al cerrar",
        P_LOGIN_DIALOG,
        '    document.body.style.overflow = "hidden";',
        '    document.body.style.overflow = "visible";',
    ),
    Mutation(
        T_DIALOG,
        "se renderiza abierto sin depender de showModal y expone sus atributos accesibles",
        P_DIALOG,
        '      aria-modal="true"',
        '      aria-modal="false"',
    ),
    Mutation(
        T_DIALOG,
        "cierra con Escape y devuelve el foco al disparador",
        P_DIALOG,
        '    if (event.key !== "Escape") {',
        '    if (event.key === "Escape") {',
    ),
    Mutation(
        T_DIALOG,
        "atiende cancel y refleja el cierre sin close() nativo",
        P_DIALOG,
        "      onCancel={handleCancel}",
        "      onCancel={() => undefined}",
    ),
    Mutation(
        T_REVEAL,
        "sin IntersectionObserver queda revelada y su contenido es visible",
        P_REVEAL,
        "const [revealed, setRevealed] = useState(!canAnimate);",
        "const [revealed, setRevealed] = useState(false);",
    ),
    Mutation(
        T_REVEAL,
        "con observador inyectado pasa de pendiente a revelada y limpia al desmontar",
        P_REVEAL,
        "    return instance.observe(section, () => {\n      setRevealed(true);\n    });",
        "    return instance.observe(section, () => {});",
    ),
    Mutation(
        T_REVEAL,
        "con movimiento reducido no queda pendiente y el contenido está en el DOM",
        P_REVEAL,
        "const [revealed, setRevealed] = useState(!canAnimate);",
        "const [revealed, setRevealed] = useState(false);",
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
        if file in C35_TEST_FILES and name in expected_names:
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
