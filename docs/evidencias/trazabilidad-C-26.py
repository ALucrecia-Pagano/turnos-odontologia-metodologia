"""Trazabilidad de C-26: cada escenario de la spec delta a un test listado por Vitest.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-26.py

Lee los escenarios de la spec, comprueba con `vitest list --json` que cada test existe,
genera trazabilidad-C-26.txt y regenera la tabla de verify-C-26.md. Termina con codigo 0
solo si no falta ningun escenario y no sobra ninguna fila.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "trazabilidad-C-26.txt"
VERIFY = EVIDENCE / "verify-C-26.md"
SPEC_ACTIVE = REPO / "openspec" / "changes" / "ui-login-y-sesion" / "specs" / "frontend-auth-session" / "spec.md"
SPEC_ARCHIVED = (
    REPO / "openspec" / "changes" / "archive" / "2026-11-07-ui-login-y-sesion" / "specs" / "frontend-auth-session" / "spec.md"
)
SPEC = SPEC_ACTIVE if SPEC_ACTIVE.exists() else SPEC_ARCHIVED
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

TOKEN_STORE = "src/features/auth/tokenStore.test.ts"
STORAGE_GUARD = "src/features/auth/storageGuard.test.ts"
AUTH_API = "src/features/auth/authApi.test.ts"
AUTH_CONTEXT = "src/features/auth/AuthContext.test.tsx"
SAFE_PATH = "src/features/auth/safeInternalPath.test.ts"
APP = "src/App.test.tsx"
LOGIN_PAGE = "src/features/login/LoginPage.test.tsx"
MENU_FOR = "src/features/auth/menuFor.test.ts"
APP_SHELL = "src/shared/components/AppShell.test.tsx"
LOGOUT = "src/features/auth/Logout.test.tsx"

TRACE: dict[str, dict[str, str]] = {
    "TokenStore": {
        "Guardar y leer el token de la pestaña": f"{TOKEN_STORE} > guardar y leer el token de la pestaña",
        "Limpiar el token": f"{TOKEN_STORE} > limpiar el token",
        "Fallback a memoria si el almacenamiento falla": f"{TOKEN_STORE} > fallback a memoria si el almacenamiento falla",
        "El storage está confinado a un solo archivo": f"{STORAGE_GUARD} > el storage está confinado a un solo archivo",
    },
    "Login": {
        "Login correcto del administrador": f"{LOGIN_PAGE} > login correcto del administrador",
        "Login correcto de recepción y del odontólogo": f"{LOGIN_PAGE} > login correcto de recepción y del odontólogo",
        "Credenciales inválidas con mensaje genérico": f"{LOGIN_PAGE} > credenciales inválidas con mensaje genérico",
        "Envío en curso y doble submit": f"{LOGIN_PAGE} > envío en curso y doble submit",
        "Accesibilidad del formulario": f"{LOGIN_PAGE} > accesibilidad del formulario",
    },
    "Carga inicial de la sesión con /me": {
        "Estado checking mientras se verifica la sesión": f"{AUTH_CONTEXT} > estado checking mientras se verifica la sesión",
        "Sesión autenticada con el usuario de /me": f"{AUTH_CONTEXT} > sesión autenticada con el usuario de /me",
        "/me responde 401 y limpia la sesión": f"{AUTH_CONTEXT} > /me responde 401 y limpia la sesión",
        "Error de red en /me conserva el token y permite reintentar": f"{AUTH_CONTEXT} > error de red en /me conserva el token y permite reintentar",
    },
    "Rutas protegidas y redirección con from validado": {
        "Ruta protegida sin sesión conserva el destino": f"{APP} > ruta protegida sin sesión conserva el destino",
        "Login con sesión vuelve al destino válido": f"{APP} > login con sesión vuelve al destino válido",
        "Se rechaza una ruta protocol-relative": f"{SAFE_PATH} > se rechaza una ruta protocol-relative",
        "Se rechaza una URL absoluta": f"{SAFE_PATH} > se rechaza una URL absoluta",
        "Se rechaza volver al propio login": f"{SAFE_PATH} > se rechaza volver al propio login",
        "Sin parpadeo de login a home": f"{APP} > sin parpadeo de login a home",
    },
    "401 durante el uso": {
        "Token vencido en una request protegida": (
            f"{APP} > token vencido en una request protegida"
            f" ; {AUTH_CONTEXT} > lastEvent registra expired ante 401 protegido y manual ante logout"
        ),
        "El 401 del login no es sesión vencida": f"{LOGIN_PAGE} > el 401 del login no es sesión vencida",
    },
    "403 sin cerrar sesión": {
        "Rol sin permiso muestra la violación": (
            f"{AUTH_CONTEXT} > rol sin permiso muestra la violación ante 403 sin cerrar sesión ni refrescar /me"
            f" ; {APP_SHELL} > muestra en un alerta del shell la violación de un 403 sin cerrar la sesión"
        ),
    },
    "Menú por rol": {
        "Menú del administrador": (
            f"{MENU_FOR} > menú del administrador incluye los 6 ítems deshabilitados con Próximamente"
            f" ; {APP_SHELL} > renderiza el menú del rol con los ítems deshabilitados y la etiqueta Próximamente"
        ),
        "Menú de recepción": (
            f"{MENU_FOR} > menú de recepción no incluye Usuarios y roles"
            f" ; {APP_SHELL} > renderiza el menú del rol con los ítems deshabilitados y la etiqueta Próximamente"
        ),
        "Menú del odontólogo": (
            f"{MENU_FOR} > menú del odontólogo no incluye Turnos ni Usuarios y roles"
            f" ; {APP_SHELL} > renderiza el menú del rol con los ítems deshabilitados y la etiqueta Próximamente"
        ),
    },
    "Logout": {
        "Cerrar sesión desde el shell": f"{LOGOUT} > cerrar sesión desde el shell descarta token y usuario y navega a /login con replace",
    },
    "Header Authorization Bearer": {
        "Petición autenticada con Bearer": f"{AUTH_API} > petición autenticada con Bearer",
        "El login no manda un token viejo": f"{AUTH_API} > el login no manda un token viejo",
        "Sin token no se envía Authorization": f"{AUTH_API} > sin token no se envía Authorization",
    },
}


def spec_scenarios(path: Path) -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    current_requirement: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Requirement: "):
            current_requirement = line.removeprefix("### Requirement: ").strip()
        elif line.startswith("#### Scenario: "):
            if current_requirement is None:
                raise ValueError("Escenario sin requisito")
            scenarios.append((current_requirement, line.removeprefix("#### Scenario: ").strip()))
    return scenarios


def listed_tests() -> set[str]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "NO_COLOR": "1"},
        check=False,
    )
    entries = json.loads(result.stdout[result.stdout.find("[") :])
    nodes: set[str] = set()
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        nodes.add(f"{file} > {entry['name'].split(' > ')[-1]}")
    return nodes


def main() -> int:
    nodes = listed_tests()
    rows: list[str] = []
    problems: list[str] = []
    number = 0
    seen: set[tuple[str, str]] = set()

    for requirement, scenario in spec_scenarios(SPEC):
        number += 1
        seen.add((requirement, scenario))
        node = TRACE.get(requirement, {}).get(scenario)
        if node is None:
            problems.append(f"sin test: {requirement} / {scenario}")
            continue
        for single in node.split(" ; "):
            if single not in nodes:
                problems.append(f"test inexistente: {single}")
        rows.append(f"| {number} | {requirement} | {scenario} | `{node}` |")

    for requirement, scenarios in TRACE.items():
        for scenario in scenarios:
            if (requirement, scenario) not in seen:
                problems.append(f"fila sin escenario en la spec: {requirement} / {scenario}")

    table = "\n".join(["| # | Requisito | Escenario | Test |", "|---|---|---|---|", *rows])
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-26.py. No editar a mano.",
        f"tests listados por vitest: {len(nodes)}",
        f"escenarios en la spec delta: {number}",
        f"escenarios con test listado: {len(rows) - len({p for p in problems if p.startswith('test inexistente')})}",
        *problems,
        f"problemas: {len(problems)}",
        f"{number} escenarios, {len(problems)} problemas",
    ]
    report = "\n".join(lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)

    if VERIFY.exists():
        verify = VERIFY.read_text(encoding="utf-8")
        start = verify.find(TABLE_START)
        end = verify.find(TABLE_END)
        if start == -1 or end == -1:
            print("Faltan los marcadores de trazabilidad en verify-C-26.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
