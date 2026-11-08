"""Verificacion por mutacion, reproducible, de los tests de C-26 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-26.py [--check]

Misma logica que mutaciones-C-25.py. Cada mutacion es
(archivo de test, nombre del test, archivo de produccion, texto_original, texto_mutado).
Hay UNA mutacion por cada test nuevo de C-26: antes de mutar se cuentan los tests nuevos
con `vitest list --json` y se exige una correspondencia uno a uno.

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

Genera mutaciones-C-26.txt (salida cruda de Vitest incluida) y regenera la tabla de
verify-C-26.md. Termina con codigo 0 solo si todas las mutaciones hicieron fallar su
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
OUTPUT = EVIDENCE / "mutaciones-C-26.txt"
VERIFY = EVIDENCE / "verify-C-26.md"
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

# --- archivos de test de C-26 ------------------------------------------------
T_TOKEN_STORE = "src/features/auth/tokenStore.test.ts"
T_STORAGE_GUARD = "src/features/auth/storageGuard.test.ts"
T_AUTH_API = "src/features/auth/authApi.test.ts"
T_AUTH_CONTEXT = "src/features/auth/AuthContext.test.tsx"
T_SAFE_PATH = "src/features/auth/safeInternalPath.test.ts"
T_APP = "src/App.test.tsx"
T_LOGIN_PAGE = "src/features/login/LoginPage.test.tsx"
T_MENU_FOR = "src/features/auth/menuFor.test.ts"
T_APP_SHELL = "src/shared/components/AppShell.test.tsx"
T_LOGOUT = "src/features/auth/Logout.test.tsx"

C26_TEST_FILES = (
    T_TOKEN_STORE,
    T_STORAGE_GUARD,
    T_AUTH_API,
    T_AUTH_CONTEXT,
    T_SAFE_PATH,
    T_APP,
    T_LOGIN_PAGE,
    T_MENU_FOR,
    T_APP_SHELL,
    T_LOGOUT,
)

# Tests de src/App.test.tsx creados y mutados en C-25.
C25_EXISTING_TESTS = {
    (T_APP, "la ruta raíz renderiza el HomePage de bienvenida"),
    (T_APP, "una ruta desconocida muestra la página de no encontrada"),
}

# --- archivos de produccion (siempre dentro de frontend/src) -----------------
P_TOKEN_STORE = "frontend/src/features/auth/tokenStore.ts"
P_AUTH_API = "frontend/src/features/auth/authApi.ts"
P_CLIENT = "frontend/src/shared/api/client.ts"
P_AUTH_CONTEXT = "frontend/src/features/auth/AuthContext.tsx"
P_SAFE_PATH = "frontend/src/features/auth/safeInternalPath.ts"
P_REQUIRE_AUTH = "frontend/src/features/auth/RequireAuth.tsx"
P_PUBLIC_ONLY = "frontend/src/features/auth/PublicOnlyRoute.tsx"
P_LOGIN_FORM = "frontend/src/features/login/LoginForm.tsx"
P_MENU_FOR = "frontend/src/features/auth/menuFor.ts"
P_APP_SHELL = "frontend/src/shared/components/AppShell.tsx"


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
    # --- 1. TokenStore y confinamiento del storage ---
    Mutation(
        T_TOKEN_STORE,
        "guardar y leer el token de la pestaña",
        P_TOKEN_STORE,
        'export const ACCESS_TOKEN_STORAGE_KEY = "turnos.auth.accessToken";',
        'export const ACCESS_TOKEN_STORAGE_KEY = "turnos.auth.otroToken";',
    ),
    Mutation(
        T_TOKEN_STORE,
        "limpiar el token",
        P_TOKEN_STORE,
        "      storage.removeItem(ACCESS_TOKEN_STORAGE_KEY);",
        '      storage.setItem(ACCESS_TOKEN_STORAGE_KEY, "sin-borrar");',
    ),
    Mutation(
        T_TOKEN_STORE,
        "fallback a memoria si el almacenamiento falla",
        P_TOKEN_STORE,
        "  function setToken(token: string): void {\n    memoryToken = token;",
        "  function setToken(token: string): void {\n    memoryToken = null;",
    ),
    Mutation(
        T_TOKEN_STORE,
        "createMemoryTokenStore aísla cada instancia sin tocar sessionStorage",
        P_TOKEN_STORE,
        "  let currentToken: string | null = initialToken;",
        "  let currentToken: string | null = null;",
    ),
    Mutation(
        T_STORAGE_GUARD,
        "el storage está confinado a un solo archivo",
        P_TOKEN_STORE,
        "  storage: StorageLike | undefined = typeof window !== \"undefined\" ? window.sessionStorage : undefined,",
        "  storage: StorageLike | undefined = typeof window !== \"undefined\" ? window.localStorage : undefined,",
    ),
    # --- 2. API de autenticacion y header Bearer ---
    Mutation(
        T_AUTH_API,
        "login envía POST /api/auth/login y devuelve el accessToken con 200",
        P_AUTH_API,
        'const LOGIN_PATH = "/auth/login";',
        'const LOGIN_PATH = "/auth/signin";',
    ),
    Mutation(
        T_AUTH_API,
        "login devuelve error auth ante 401 INVALID_CREDENTIALS",
        P_AUTH_API,
        'function mapLoginError(error: ApiErrorPayload): ApiErrorPayload {\n  if (error.kind === "auth") {\n    return { kind: "auth", status: error.status, code: error.code, message: error.message };\n  }',
        'function mapLoginError(error: ApiErrorPayload): ApiErrorPayload {\n  if (error.kind === "auth") {\n    return { kind: "auth", status: error.status, code: "OTRO", message: error.message };\n  }',
    ),
    Mutation(
        T_AUTH_API,
        "login devuelve error validation ante 400 con errors",
        P_AUTH_API,
        '  if (error.kind === "validation") {\n    return { kind: "validation", status: error.status, errors: error.errors };\n  }',
        '  if (error.kind === "validation") {\n    return { kind: "validation", status: error.status, errors: [] };\n  }',
    ),
    Mutation(
        T_AUTH_API,
        "el login no manda un token viejo",
        P_AUTH_API,
        '    auth: "omit",',
        '    auth: "auto",',
    ),
    Mutation(
        T_AUTH_API,
        "petición autenticada con Bearer",
        P_AUTH_API,
        'const ME_PATH = "/auth/me";',
        'const ME_PATH = "/auth/current";',
    ),
    Mutation(
        T_AUTH_API,
        "sin token no se envía Authorization",
        P_CLIENT,
        "    if (token !== null) {",
        "    if (token !== undefined) {",
    ),
    Mutation(
        T_AUTH_API,
        "fetchMe devuelve error auth ante 401 INVALID_TOKEN y error unknown ante red o 5xx",
        P_AUTH_API,
        'function mapMeError(error: ApiErrorPayload): ApiErrorPayload {\n  if (error.kind === "auth") {\n    return { kind: "auth", status: error.status, code: error.code, message: error.message };\n  }',
        'function mapMeError(error: ApiErrorPayload): ApiErrorPayload {\n  if (error.kind === "auth") {\n    return { kind: "auth", status: error.status, code: "OTRO", message: error.message };\n  }',
    ),
    # --- 3. Contexto y arranque de sesion ---
    Mutation(
        T_AUTH_CONTEXT,
        "estado checking mientras se verifica la sesión",
        P_AUTH_CONTEXT,
        '  const [status, setStatus] = useState<AuthStatus>(() =>\n    store.getToken() !== null ? "checking" : "anonymous",\n  );',
        '  const [status, setStatus] = useState<AuthStatus>(() =>\n    store.getToken() !== null ? "anonymous" : "anonymous",\n  );',
    ),
    Mutation(
        T_AUTH_CONTEXT,
        "sesión autenticada con el usuario de /me",
        P_AUTH_CONTEXT,
        '      if (result.ok) {\n        statusRef.current = "authenticated";\n        setUser(result.data);',
        '      if (result.ok) {\n        statusRef.current = "authenticated";\n        setUser(null);',
    ),
    Mutation(
        T_AUTH_CONTEXT,
        "/me responde 401 y limpia la sesión",
        P_AUTH_CONTEXT,
        "      if (result.status === 401) {\n        store.clear();",
        "      if (result.status === 401) {\n        void store;",
    ),
    Mutation(
        T_AUTH_CONTEXT,
        "error de red en /me conserva el token y permite reintentar",
        P_AUTH_CONTEXT,
        "      setBootstrapError([NETWORK_ERROR_MESSAGE]);",
        '      setBootstrapError(["Error distinto"]);',
    ),
    Mutation(
        T_AUTH_CONTEXT,
        "lastEvent registra expired ante 401 protegido y manual ante logout",
        P_AUTH_CONTEXT,
        '    setLastEvent("expired");',
        "    setLastEvent(null);",
    ),
    Mutation(
        T_AUTH_CONTEXT,
        "rol sin permiso muestra la violación ante 403 sin cerrar sesión ni refrescar /me",
        P_AUTH_CONTEXT,
        '          } else if (result.error.kind === "forbidden") {\n            setActionErrors(getApiErrorMessages(result.error));\n          }',
        '          } else if (result.error.kind === "forbidden") {\n            setActionErrors([]);\n          }',
    ),
    # --- 4. Rutas y guards ---
    Mutation(
        T_SAFE_PATH,
        "acepta una ruta interna con query string como /agenda?date=2026-11-07",
        P_SAFE_PATH,
        "  return candidate;",
        '  return "/";',
    ),
    Mutation(
        T_SAFE_PATH,
        "se rechaza una ruta protocol-relative",
        P_SAFE_PATH,
        '  if (candidate.startsWith("//")) {\n    return "/";\n  }',
        '  if (candidate.startsWith("///")) {\n    return "/";\n  }',
    ),
    Mutation(
        T_SAFE_PATH,
        "se rechaza una URL absoluta",
        P_SAFE_PATH,
        '  if (typeof candidate !== "string" || candidate === "" || !candidate.startsWith("/")) {\n    return "/";\n  }',
        '  if (typeof candidate !== "string" || candidate === "") {\n    return "/";\n  }',
    ),
    Mutation(
        T_SAFE_PATH,
        "se rechaza volver al propio login",
        P_SAFE_PATH,
        '  if (candidate === "/login" || candidate.startsWith("/login?") || candidate.startsWith("/login/")) {\n    return "/";\n  }',
        '  if (candidate.startsWith("/login/")) {\n    return "/";\n  }',
    ),
    Mutation(
        T_APP,
        "ruta protegida sin sesión conserva el destino",
        P_REQUIRE_AUTH,
        "          from: `${location.pathname}${location.search}`,",
        "          from: location.pathname,",
    ),
    Mutation(
        T_APP,
        "login con sesión vuelve al destino válido",
        P_PUBLIC_ONLY,
        "    const destination = safeInternalPath(extractFromPath(location.state));",
        "    const destination = safeInternalPath(undefined);",
    ),
    Mutation(
        T_APP,
        "sin parpadeo de login a home",
        P_PUBLIC_ONLY,
        '  if (status === "checking") {\n    return <LoadingState />;\n  }',
        '  if (status === "checking") {\n    return <Outlet />;\n  }',
    ),
    Mutation(
        T_APP,
        "token vencido en una request protegida",
        P_REQUIRE_AUTH,
        '          expired: lastEvent === "expired",',
        "          expired: false,",
    ),
    # --- 5. Pantalla de login ---
    Mutation(
        T_LOGIN_PAGE,
        "login correcto del administrador",
        P_AUTH_CONTEXT,
        "      store.setToken(loginResult.data.accessToken);",
        '      store.setToken("");',
    ),
    Mutation(
        T_LOGIN_PAGE,
        "login correcto de recepción y del odontólogo",
        P_AUTH_API,
        "  return { id, username, displayName, role, professionalId };",
        "  return { id, username, displayName, role, professionalId: null };",
    ),
    Mutation(
        T_LOGIN_PAGE,
        "credenciales inválidas con mensaje genérico",
        P_LOGIN_FORM,
        '    const result = await onSubmit({ username: trimmedUsername, password });\n    setPassword("");',
        "    const result = await onSubmit({ username: trimmedUsername, password });",
    ),
    Mutation(
        T_LOGIN_PAGE,
        "el 401 del login no es sesión vencida",
        P_LOGIN_FORM,
        '        setErrorMessage(getApiErrorMessages(result.error).join(" "));',
        '        setErrorMessage("La sesión venció. Iniciá sesión de nuevo.");',
    ),
    Mutation(
        T_LOGIN_PAGE,
        "envío en curso y doble submit",
        P_LOGIN_FORM,
        '        {isSubmitting ? "Ingresando…" : "Ingresar"}',
        '        {isSubmitting ? "Enviando" : "Ingresar"}',
    ),
    Mutation(
        T_LOGIN_PAGE,
        "accesibilidad del formulario",
        P_LOGIN_FORM,
        '          autoComplete="current-password"',
        '          autoComplete="off"',
    ),
    # --- 6. Menu por rol y 403 ---
    Mutation(
        T_MENU_FOR,
        "menú del administrador incluye los 6 ítems deshabilitados con Próximamente",
        P_MENU_FOR,
        '    id: "usuarios-y-roles",\n    label: "Usuarios y roles",\n    path: "/usuarios-y-roles",\n    roles: ["administrador"],',
        '    id: "usuarios-y-roles",\n    label: "Usuarios y roles",\n    path: "/usuarios-y-roles",\n    roles: [],',
    ),
    Mutation(
        T_MENU_FOR,
        "menú de recepción no incluye Usuarios y roles",
        P_MENU_FOR,
        '    id: "turnos",\n    label: "Turnos",\n    path: "/turnos",\n    roles: ["administrador", "recepcion"],',
        '    id: "turnos",\n    label: "Turnos",\n    path: "/turnos",\n    roles: ["administrador"],',
    ),
    Mutation(
        T_MENU_FOR,
        "menú del odontólogo no incluye Turnos ni Usuarios y roles",
        P_MENU_FOR,
        '    id: "pacientes",\n    label: "Pacientes",\n    path: "/pacientes",\n    roles: ["administrador", "recepcion", "odontologo"],',
        '    id: "pacientes",\n    label: "Pacientes",\n    path: "/pacientes",\n    roles: ["administrador", "recepcion"],',
    ),
    Mutation(
        T_APP_SHELL,
        "renderiza el menú del rol con los ítems deshabilitados y la etiqueta Próximamente",
        P_APP_SHELL,
        "                  disabled={item.disabled}",
        "                  disabled={false}",
    ),
    Mutation(
        T_APP_SHELL,
        "muestra en un alerta del shell la violación de un 403 sin cerrar la sesión",
        P_APP_SHELL,
        "      {actionErrors !== null && actionErrors.length > 0 && (",
        "      {actionErrors !== null && actionErrors.length > 99 && (",
    ),
    # --- 7. Logout ---
    Mutation(
        T_LOGOUT,
        "cerrar sesión desde el shell descarta token y usuario y navega a /login con replace",
        P_APP_SHELL,
        '  const handleLogout = () => {\n    logout();\n    navigate("/login", { replace: true });\n  };',
        '  const handleLogout = () => {\n    navigate("/login", { replace: false });\n  };',
    ),
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
    if not mutation.file.startswith("frontend/src/"):
        raise MutationAbort(f"{mutation.node_id}: {mutation.file} no esta en frontend/src/")
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
        if file in C26_TEST_FILES and (file, name) not in C25_EXISTING_TESTS:
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
            f"tests nuevos de C-26 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
            f"una por cada uno de los {total_tests} tests nuevos de C-26."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-26.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-26 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C26_TEST_FILES))
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
