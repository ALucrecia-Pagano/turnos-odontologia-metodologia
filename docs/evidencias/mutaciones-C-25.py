"""Verificacion por mutacion, reproducible, de los tests de C-25 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-25.py [--check]

Misma logica que mutaciones-C-23.py, adaptada a Vitest. Cada mutacion es
(archivo de test, nombre del test, archivo de produccion, texto_original, texto_mutado).
Hay UNA mutacion por cada test nuevo de C-25: antes de mutar se cuentan los tests con
`vitest list --json` y se exige una correspondencia uno a uno.

Por cada mutacion: comprueba que el original aparezca exactamente una vez y que el
mutante cambie el archivo (respetando LF o CRLF), aplica la mutacion, corre Vitest solo
para ese test (`vitest run <archivo> -t <nombre>$`), restaura el archivo en un finally y
vuelve a correr el test, que tiene que volver a verde.

Una mutacion es INVALIDA si su test no la detecta con una afirmacion propia:
- el archivo de test no carga (error de import, de compilacion o SyntaxError);
- no se ejecuto exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro
  error que no sea AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no esta en un archivo *.test.ts(x) (una guarda
  del codigo de produccion que lanza).

Genera mutaciones-C-25.txt (salida cruda de Vitest incluida) y regenera la tabla de
verify-C-25.md. Termina con codigo 0 solo si todas las mutaciones hicieron fallar su
test, ninguna es INVALIDA y el SHA-256 del codigo de produccion no cambio.
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
OUTPUT = EVIDENCE / "mutaciones-C-25.txt"
VERIFY = EVIDENCE / "verify-C-25.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 300
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

# Archivos de produccion cubiertos por el SHA-256 (todo frontend/src salvo tests, y la configuracion mutada).
CONFIG_FILES = (
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/eslint.config.js",
    "frontend/vite.config.ts",
    "frontend/Dockerfile",
    "docker-compose.yml",
)

INVALID_ERROR = re.compile(
    r"^(ReferenceError|SyntaxError|TypeError|RangeError|TestingLibraryElementError"
    r"|Error: (Failed to load|Failed to resolve|Cannot find module|Transform failed))"
)
ASSERTION = re.compile(r"^(AssertionError\b|Error: expect\()")
STACK_FRAME = re.compile(r"^\s*at (?:.*\()?(?:file:///)?(?P<path>[A-Za-z]:[\\/][^:()]+|/[^:()]+):\d+:\d+\)?$")
TEST_FILE = re.compile(r"\.test\.tsx?$")

# --- archivos de test -------------------------------------------------------
T_TOOLING = "src/test/tooling.test.ts"
T_SMOKE = "src/test/smoke.test.tsx"
T_DOCKER = "src/test/docker.test.ts"
T_STATUS_TOKENS = "src/shared/styles/appointmentStatusTokens.test.ts"
T_TOKENS = "src/shared/styles/tokens.test.ts"
T_BADGE = "src/shared/components/StatusBadge.test.tsx"
T_LOADING = "src/shared/components/LoadingState.test.tsx"
T_EMPTY = "src/shared/components/EmptyState.test.tsx"
T_ERROR = "src/shared/components/ErrorState.test.tsx"
T_SHELL = "src/shared/components/PageShell.test.tsx"
T_CLIENT = "src/shared/api/client.test.ts"
T_ERRORS = "src/shared/api/errors.test.ts"
T_AUTH = "src/shared/api/auth.test.ts"
T_APP = "src/App.test.tsx"

# --- archivos de produccion -------------------------------------------------
P_PACKAGE = "frontend/package.json"
P_TSCONFIG = "frontend/tsconfig.json"
P_ESLINT = "frontend/eslint.config.js"
P_VITE = "frontend/vite.config.ts"
P_COMPOSE = "docker-compose.yml"
P_STATUS_TOKENS = "frontend/src/shared/styles/appointmentStatusTokens.ts"
P_TOKENS_CSS = "frontend/src/shared/styles/tokens.css"
P_RESET_CSS = "frontend/src/shared/styles/reset.css"
P_BADGE = "frontend/src/shared/components/StatusBadge.tsx"
P_LOADING = "frontend/src/shared/components/LoadingState.tsx"
P_EMPTY = "frontend/src/shared/components/EmptyState.tsx"
P_ERROR = "frontend/src/shared/components/ErrorState.tsx"
P_SHELL = "frontend/src/shared/components/PageShell.tsx"
P_CLIENT = "frontend/src/shared/api/client.ts"
P_ERRORS = "frontend/src/shared/api/errors.ts"
P_AUTH = "frontend/src/shared/api/auth.ts"
P_APP = "frontend/src/App.tsx"
P_HOME = "frontend/src/pages/HomePage.tsx"


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
    # --- tooling (configuracion) ---
    Mutation(T_TOOLING, "npm run typecheck falla con un tipo inválido", P_TSCONFIG,
             '"include": ["src"]', '"include": ["src/shared"]'),
    Mutation(T_TOOLING, "npm run lint detecta una violación", P_ESLINT,
             '{ ignores: ["dist", "node_modules"] }', '{ ignores: ["dist", "node_modules", "src/**"] }'),
    Mutation(T_TOOLING, "la estructura de carpetas y los scripts están presentes", P_PACKAGE,
             '    "preview": "vite preview",\n', ''),
    Mutation(T_SMOKE, "monta App y muestra el título", P_HOME,
             '<h1 className={styles.title}>Turnos Odontología</h1>', '<h1 className={styles.title}>Turnos</h1>'),
    # --- tokens ---
    Mutation(T_STATUS_TOKENS, "el mapa cubre los cinco estados sin undefined", P_STATUS_TOKENS,
             'export const APPOINTMENT_STATUSES = ["reservado", "confirmado", "atendido", "ausente", "cancelado"] as const;',
             'export const APPOINTMENT_STATUSES = ["reservado", "confirmado", "atendido", "ausente"] as const;'),
    Mutation(T_STATUS_TOKENS, "cada par texto y fondo cumple contraste AA", P_STATUS_TOKENS,
             'ausente: { text: "#B45309"', 'ausente: { text: "#D97706"'),
    Mutation(T_TOKENS, "define la escala de espaciado 4/8/12/16/24/32/48 px", P_TOKENS_CSS,
             '--space-5: 24px;', '--space-5: 20px;'),
    Mutation(T_TOKENS, "define la tipografía 12/14/16/20/24/32 px", P_TOKENS_CSS,
             '--font-size-lg: 20px;', '--font-size-lg: 18px;'),
    Mutation(T_TOKENS, "usa el system font stack en el reset", P_RESET_CSS,
             '  font-family: var(--font-family-base);', '  font-family: serif;'),
    Mutation(T_TOKENS, "el foco es visible", P_RESET_CSS,
             '  outline: 2px solid var(--color-focus);', '  outline: none;'),
    # --- StatusBadge ---
    Mutation(T_BADGE, "el estado reservado muestra su variante", P_BADGE,
             '  reservado: "Reservado",', '  reservado: "Reservada",'),
    Mutation(T_BADGE, "el estado confirmado muestra su variante", P_BADGE,
             '  confirmado: "Confirmado",', '  confirmado: "Confirmada",'),
    Mutation(T_BADGE, "el estado atendido muestra su variante", P_BADGE,
             '  atendido: "Atendido",', '  atendido: "Atendida",'),
    Mutation(T_BADGE, "el estado ausente muestra su variante", P_BADGE,
             '  ausente: "Ausente",', '  ausente: "Ausencia",'),
    Mutation(T_BADGE, "el estado cancelado muestra su variante", P_BADGE,
             '  cancelado: "Cancelado",', '  cancelado: "Cancelada",'),
    # --- estados base ---
    Mutation(T_LOADING, "renderiza su rol y su texto", P_LOADING,
             'label = "Cargando..."', 'label = "Cargando"'),
    Mutation(T_EMPTY, "con acción muestra el botón", P_EMPTY,
             'onClick={action.onClick}', 'onClick={() => undefined}'),
    Mutation(T_EMPTY, "sin acción no muestra botón", P_EMPTY,
             '<p className={styles.description}>{description}</p>', '<p className={styles.description}>{title}</p>'),
    Mutation(T_ERROR, "muestra uno y varios mensajes", P_ERROR,
             '{messages.map((message, index) => (', '{messages.slice(0, 1).map((message, index) => ('),
    Mutation(T_ERROR, "muestra el mensaje de un 409 textual", P_ERROR,
             '>{message}</li>', '>{message.replace(" (hora local)", "")}</li>'),
    Mutation(T_ERROR, "con reintento muestra el botón y lo ejecuta", P_ERROR,
             'onClick={onRetry}', 'onClick={() => undefined}'),
    Mutation(T_ERROR, "sin reintento no muestra botón", P_ERROR,
             '{onRetry !== undefined && (', '{(onRetry !== undefined || messages.length > 0) && ('),
    Mutation(T_SHELL, "envuelve header, main y footer y renderiza sus hijos", P_SHELL,
             '<footer className={styles.footer}>Consultorio odontológico · agenda de turnos</footer>',
             '<div className={styles.footer}>Consultorio odontológico · agenda de turnos</div>'),
    # --- cliente de API ---
    Mutation(T_CLIENT, "una respuesta 200 devuelve ok con los datos", P_CLIENT,
             'data: parseJson(text) ?? null };', 'data: null };'),
    Mutation(T_CLIENT, "serializa el cuerpo como JSON y envía los headers de contenido", P_CLIENT,
             'headers.set("Content-Type", "application/json");', 'headers.set("Content-Type", "text/plain");'),
    Mutation(T_CLIENT, "un 400 con errors se modela como validation", P_CLIENT,
             'if (status === 400) {', 'if (status === 418) {'),
    Mutation(T_CLIENT, "un 401 con code y message se modela como auth", P_CLIENT,
             'if (status === 401 || status === 404) {', 'if (status === 404) {'),
    Mutation(T_CLIENT, "un 403 con violations se modela como forbidden", P_CLIENT,
             'if (status === 403) return { kind: "forbidden", status, violations };',
             'if (status === 403) return { kind: "unknown", status, rawText };'),
    Mutation(T_CLIENT, "un 409 con PROFESSIONAL_OVERLAP conserva el mensaje exacto", P_CLIENT,
             'if (status === 409) return { kind: "conflict", status, violations };',
             'if (status === 409) return { kind: "unprocessable", status: 422, violations };'),
    Mutation(T_CLIENT, "un 422 con violations se modela como unprocessable", P_CLIENT,
             '        return { kind: "unprocessable", status, violations };',
             '        return { kind: "unknown", status, rawText };'),
    Mutation(T_CLIENT, "un 404 con code y message se modela como not_found", P_CLIENT,
             ': { kind: "not_found", status, code, message };', ': { kind: "unknown", status, rawText };'),
    Mutation(T_CLIENT, "una respuesta desconocida se modela como unknown", P_CLIENT,
             '  return { kind: "unknown", status, rawText };\n}', '  return { kind: "unknown", status, rawText: "" };\n}'),
    Mutation(T_CLIENT, "un fallo de red se modela como unknown con status 0 sin lanzar", P_CLIENT,
             'return { ok: false, status: 0, error: { kind: "unknown", status: 0, rawText } };',
             'return { ok: false, status: -1, error: { kind: "unknown", status: -1, rawText } };'),
    # --- getApiErrorMessages ---
    Mutation(T_ERRORS, "devuelve errors[].message de un 400 en orden y tal cual", P_ERRORS,
             '(fieldError) => fieldError.message', '(fieldError) => fieldError.field'),
    Mutation(T_ERRORS, "devuelve message de un 401 tal cual", P_ERRORS,
             '    case "auth":\n    case "not_found":\n      return [error.message];\n    case "unknown":',
             '    case "not_found":\n      return [error.message];\n    case "auth":\n    case "unknown":'),
    Mutation(T_ERRORS, "devuelve violations[].message de un 409 con PROFESSIONAL_OVERLAP sin reformular", P_ERRORS,
             '(violation) => violation.message)', '(violation) => violation.message.replace(" (hora local)", ""))'),
    Mutation(T_ERRORS, "devuelve violations[].message de un 403 y de un 422", P_ERRORS,
             '    case "forbidden":\n    case "conflict":\n    case "unprocessable":\n      return error.violations',
             '    case "conflict":\n      return error.violations'),
    Mutation(T_ERRORS, "devuelve message de un 404 tal cual", P_ERRORS,
             '    case "auth":\n    case "not_found":\n      return [error.message];\n    case "unknown":',
             '    case "auth":\n      return [error.message];\n    case "not_found":\n    case "unknown":'),
    Mutation(T_ERRORS, "un error unknown devuelve un mensaje genérico con el status, sin el texto crudo", P_ERRORS,
             '`Ocurrió un error inesperado (HTTP ${error.status}).`', '`Ocurrió un error inesperado: ${error.rawText}`'),
    # --- costura del token ---
    Mutation(T_AUTH, "sin provider no se envía Authorization", P_AUTH,
             'let currentProvider: AuthProvider | null = null;',
             'let currentProvider: AuthProvider | null = { getToken: () => "token-por-defecto" };'),
    Mutation(T_AUTH, "con provider se agrega el Bearer", P_CLIENT,
             'headers.set("Authorization", `Bearer ${token}`);', 'headers.set("Authorization", token);'),
    Mutation(T_AUTH, "C-25 no persiste el token", P_AUTH,
             'return currentProvider?.getToken() ?? null;',
             'return currentProvider?.getToken() ?? localStorage.getItem("token");'),
    # --- router ---
    Mutation(T_APP, "la ruta raíz renderiza el HomePage de bienvenida", P_HOME,
             '{APPOINTMENT_STATUSES.map((status) => (', '{APPOINTMENT_STATUSES.slice(1).map((status) => ('),
    Mutation(T_APP, "una ruta desconocida muestra la página de no encontrada", P_APP,
             '{ path: "*", element: <NotFoundPage /> },', '{ path: "*", element: <HomePage /> },'),
    # --- Docker Compose (configuracion) ---
    Mutation(T_DOCKER, "docker compose up levanta el frontend en 5173", P_COMPOSE,
             '      - "5173:5173"', '      - "5174:5173"'),
    Mutation(T_DOCKER, "un cambio de archivo se refleja por HMR en Windows", P_COMPOSE,
             'CHOKIDAR_USEPOLLING: "true"', 'CHOKIDAR_USEPOLLING: "false"'),
    Mutation(T_DOCKER, "VITE_API_URL del navegador apunta a localhost", P_COMPOSE,
             '      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000/api}',
             '      VITE_API_URL: http://backend:8000/api'),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text: str) -> None:
        self.stream.write(text.rstrip() + "\n")
        self.stream.flush()


def vitest_env() -> dict[str, str]:
    return {**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"}


def production_sha256() -> str:
    hasher = hashlib.sha256()
    paths = [
        path
        for path in sorted((FRONTEND / "src").rglob("*"))
        if path.is_file() and not TEST_FILE.search(path.name)
    ]
    paths += [REPO / name for name in CONFIG_FILES]
    for path in paths:
        hasher.update(path.relative_to(REPO).as_posix().encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def apply_mutation(mutation: Mutation, content: str) -> str:
    """Aplica la mutacion respetando el final de linea del archivo (LF o CRLF)."""
    newline = "\r\n" if "\r\n" in content else "\n"
    original = mutation.original.replace("\n", newline)
    mutated = mutation.mutated.replace("\n", newline)
    count = content.count(original)
    if count != 1:
        raise MutationAbort(f"{mutation.node_id}: original presente {count} veces en {mutation.file}")
    return content.replace(original, mutated, 1)


def check_definition(mutation: Mutation) -> None:
    target = REPO / mutation.file
    if not target.exists():
        raise MutationAbort(f"{mutation.node_id}: {mutation.file} no existe")
    raw_content = target.read_bytes().decode("utf-8")
    count = raw_content.replace("\r\n", "\n").count(mutation.original)
    if count != 1:
        raise MutationAbort(
            f"{mutation.node_id}: original presente {count} veces en {mutation.file}\n"
            f"Original buscado:\n{mutation.original}"
        )
    if mutation.original == mutation.mutated:
        raise MutationAbort(f"{mutation.node_id}: mutacion identica al original")
    if apply_mutation(mutation, raw_content) == raw_content:
        raise MutationAbort(f"{mutation.node_id}: la mutacion no cambia {mutation.file}")


def listed_tests() -> list[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND, capture_output=True, encoding="utf-8", errors="replace",
        env=vitest_env(), timeout=TIMEOUT_SECONDS, check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
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
            f"tests listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
            cwd=FRONTEND, capture_output=True, encoding="utf-8", errors="replace",
            env=vitest_env(), timeout=TIMEOUT_SECONDS, check=False,
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
        print(f"Las {len(MUTATIONS)} mutaciones estan bien definidas, una por cada uno de los {total_tests} tests.")
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-25.py. No editar a mano.")
        report.write(f"tests de C-25 listados por vitest: {total_tests}; mutaciones: {len(MUTATIONS)} (una por test)")
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest([])
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
