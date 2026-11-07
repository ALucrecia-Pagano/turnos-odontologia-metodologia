"""Trazabilidad de C-25: cada escenario de la spec delta a un test listado por Vitest.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-25.py

Lee los escenarios de la spec, comprueba con `vitest list --json` que cada test existe,
genera trazabilidad-C-25.txt y regenera la tabla de verify-C-25.md. Termina con codigo 0
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
OUTPUT = EVIDENCE / "trazabilidad-C-25.txt"
VERIFY = EVIDENCE / "verify-C-25.md"
SPEC = REPO / "openspec" / "changes" / "frontend-base-react-vite" / "specs" / "frontend-foundation" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

TOOLING = "src/test/tooling.test.ts"
DOCKER = "src/test/docker.test.ts"
STATUS_TOKENS = "src/shared/styles/appointmentStatusTokens.test.ts"
TOKENS = "src/shared/styles/tokens.test.ts"
BADGE = "src/shared/components/StatusBadge.test.tsx"
LOADING = "src/shared/components/LoadingState.test.tsx"
EMPTY = "src/shared/components/EmptyState.test.tsx"
ERROR = "src/shared/components/ErrorState.test.tsx"
CLIENT = "src/shared/api/client.test.ts"
ERRORS = "src/shared/api/errors.test.ts"
AUTH = "src/shared/api/auth.test.ts"

TRACE: dict[str, dict[str, str]] = {
    "Estructura y tooling del frontend": {
        "npm run typecheck falla con un tipo inválido": f"{TOOLING} > npm run typecheck falla con un tipo inválido",
        "npm run lint detecta una violación": f"{TOOLING} > npm run lint detecta una violación",
        "La estructura de carpetas y los scripts están presentes": f"{TOOLING} > la estructura de carpetas y los scripts están presentes",
    },
    "Tokens de diseño y colores por estado": {
        "El mapa cubre los cinco estados sin undefined": f"{STATUS_TOKENS} > el mapa cubre los cinco estados sin undefined",
        "Cada par texto y fondo cumple contraste AA": f"{STATUS_TOKENS} > cada par texto y fondo cumple contraste AA",
        "El foco es visible": f"{TOKENS} > el foco es visible",
    },
    "StatusBadge": {
        "El estado reservado muestra su variante": f"{BADGE} > el estado reservado muestra su variante",
        "El estado confirmado muestra su variante": f"{BADGE} > el estado confirmado muestra su variante",
        "El estado atendido muestra su variante": f"{BADGE} > el estado atendido muestra su variante",
        "El estado ausente muestra su variante": f"{BADGE} > el estado ausente muestra su variante",
        "El estado cancelado muestra su variante": f"{BADGE} > el estado cancelado muestra su variante",
    },
    "Estados base de carga, vacío y error": {
        "LoadingState renderiza su rol y su texto": f"{LOADING} > renderiza su rol y su texto",
        "EmptyState con acción muestra el botón": f"{EMPTY} > con acción muestra el botón",
        "EmptyState sin acción no muestra botón": f"{EMPTY} > sin acción no muestra botón",
        "ErrorState muestra uno y varios mensajes": f"{ERROR} > muestra uno y varios mensajes",
        "ErrorState muestra el mensaje de un 409 textual": f"{ERROR} > muestra el mensaje de un 409 textual",
    },
    "Cliente de API y las cuatro formas de error": {
        "Una respuesta 200 devuelve ok con los datos": f"{CLIENT} > una respuesta 200 devuelve ok con los datos",
        "Un 400 con errors se modela como validation": (
            f"{CLIENT} > un 400 con errors se modela como validation"
            f" ; {ERRORS} > devuelve errors[].message de un 400 en orden y tal cual"
        ),
        "Un 401 con code y message se modela como auth": (
            f"{CLIENT} > un 401 con code y message se modela como auth"
            f" ; {ERRORS} > devuelve message de un 401 tal cual"
        ),
        "Un 409 con PROFESSIONAL_OVERLAP conserva el mensaje exacto": (
            f"{CLIENT} > un 409 con PROFESSIONAL_OVERLAP conserva el mensaje exacto"
            f" ; {ERRORS} > devuelve violations[].message de un 409 con PROFESSIONAL_OVERLAP sin reformular"
        ),
        "Un 404 con code y message se modela como not_found": (
            f"{CLIENT} > un 404 con code y message se modela como not_found"
            f" ; {ERRORS} > devuelve message de un 404 tal cual"
        ),
        "Una respuesta desconocida se modela como unknown": f"{CLIENT} > una respuesta desconocida se modela como unknown",
    },
    "Punto de enganche del token para C-26": {
        "Sin provider no se envía Authorization": f"{AUTH} > sin provider no se envía Authorization",
        "Con provider se agrega el Bearer": f"{AUTH} > con provider se agrega el Bearer",
        "C-25 no persiste el token": f"{AUTH} > C-25 no persiste el token",
    },
    "Servicio frontend en Docker Compose": {
        "docker compose up levanta el frontend en 5173": f"{DOCKER} > docker compose up levanta el frontend en 5173",
        "Un cambio de archivo se refleja por HMR en Windows": f"{DOCKER} > un cambio de archivo se refleja por HMR en Windows",
        "VITE_API_URL del navegador apunta a localhost": f"{DOCKER} > VITE_API_URL del navegador apunta a localhost",
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
        "Salida generada por docs/evidencias/trazabilidad-C-25.py. No editar a mano.",
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

    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start == -1 or end == -1:
        print("Faltan los marcadores de trazabilidad en verify-C-25.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
