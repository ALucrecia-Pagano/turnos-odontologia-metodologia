"""Trazabilidad de C-35: cada escenario de las specs delta a un test y a una mutacion.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-35.py

Lee los escenarios de las dos specs delta, comprueba con `vitest list --json` que
cada test existe, genera trazabilidad-C-35.txt y regenera la tabla de
verify-C-35.md. Los escenarios de verificacion visual o de CSS se marcan como
tales y no se mapean a mutacion. Termina con codigo 0 solo si no falta ningun
escenario y no sobra ninguna fila.
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
OUTPUT = EVIDENCE / "trazabilidad-C-35.txt"
VERIFY = EVIDENCE / "verify-C-35.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

SPECS = (
    REPO / "openspec" / "changes" / "ui-portada-y-acceso" / "specs" / "frontend-auth-session" / "spec.md",
    REPO / "openspec" / "changes" / "ui-portada-y-acceso" / "specs" / "frontend-foundation" / "spec.md",
    REPO / "openspec" / "changes" / "ui-portada-y-acceso" / "specs" / "frontend-landing" / "spec.md",
)

T_LANDING_CONTENT = "src/features/landing/landingContent.test.ts"
T_LANDING_TOKENS = "src/shared/styles/landingTokens.test.ts"
T_LANDING = "src/features/landing/LandingPage.test.tsx"
T_LOGIN_DIALOG = "src/features/landing/LoginDialog.test.tsx"
T_DIALOG = "src/shared/components/Dialog.test.tsx"
T_REVEAL = "src/features/landing/RevealSection.test.tsx"
T_APP = "src/App.test.tsx"
T_LOGIN_BRAND = "src/features/login/LoginBrand.test.tsx"

VISUAL = "— (verificación visual)"
CSS = "— (verificación CSS/grep)"
NO_MUTATION = "— (test existente)"


TRACE: dict[tuple[str, str], tuple[str, str]] = {
    ("Bajada y tarjeta del login", "La bajada es visible"): (
        f"{T_LOGIN_BRAND} > muestra el logo claro, el heading accesible y la bajada",
        NO_MUTATION,
    ),
    ("Bajada y tarjeta del login", "La tarjeta tipo vidrio sobre overlay navy"): (
        VISUAL,
        "—",
    ),
    ("Tokens de layout de la portada", "Los tokens de layout existen"): (
        f"{T_LANDING_TOKENS} > define los dos tokens de layout",
        "4",
    ),
    ("Tokens de layout de la portada", "La portada usa los tokens de layout"): (
        f"{T_LANDING_TOKENS} > la portada usa los tokens de layout",
        "5",
    ),
    ("Tokens de layout de la portada", "No se agregan colores nuevos"): (
        f"{T_LANDING_TOKENS} > no agrega colores nuevos",
        "6",
    ),
    ("Diálogo modal reutilizable", "Sin showModal el diálogo usa el atributo open"): (
        f"{T_DIALOG} > se renderiza abierto sin depender de showModal y expone sus atributos accesibles",
        "19",
    ),
    ("Diálogo modal reutilizable", "Escape cierra y devuelve el foco"): (
        f"{T_DIALOG} > cierra con Escape y devuelve el foco al disparador",
        "20",
    ),
    ("Diálogo modal reutilizable", "El evento cancel cierra"): (
        f"{T_DIALOG} > atiende cancel y refleja el cierre sin close() nativo",
        "21",
    ),
    ("Portada pública en /login", "La portada se muestra en /login"): (
        f"{T_LANDING} > LoginPage monta la portada y conserva el aviso de sesión vencida",
        "13",
    ),
    ("Portada pública en /login", "El anónimo en / sigue llegando a la portada"): (
        f"{T_APP} > ruta protegida sin sesión conserva el destino",
        NO_MUTATION,
    ),
    ("Portada pública en /login", "El autenticado en /login no ve la portada"): (
        f"{T_APP} > login con sesión vuelve al destino válido",
        NO_MUTATION,
    ),
    ("Hero con marca, carrusel y llamada a la acción", "La marca se anuncia una sola vez"): (
        f"{T_LANDING} > muestra la marca una sola vez, la bajada, el lead y el CTA",
        "7",
    ),
    ("Hero con marca, carrusel y llamada a la acción", "El CTA y el submit tienen nombres distintos"): (
        f"{T_LANDING} > mantiene un único botón Ingresar y un CTA accesible sin ocultar",
        "12",
    ),
    ("Hero con marca, carrusel y llamada a la acción", "El carrusel del hero se reutiliza"): (
        f"{T_LANDING} > reutiliza el carrusel de cinco fotos y su botón de pausa",
        "10",
    ),
    ("Hero con marca, carrusel y llamada a la acción", "El hero mide al menos 60vh"): (
        VISUAL,
        "—",
    ),
    ("Hero con marca, carrusel y llamada a la acción", "El badge de demostración es visible"): (
        f"{T_LANDING} > marca el sitio y los datos de contacto como demostración",
        "8",
    ),
    ("Secciones informativas con datos ficticios", "Las cuatro secciones están en el DOM"): (
        f"{T_LANDING} > muestra las cuatro secciones informativas visibles sin IntersectionObserver",
        "9",
    ),
    ("Secciones informativas con datos ficticios", "El equipo coincide con el seed"): (
        f"{T_LANDING_CONTENT} > el equipo coincide con el seed",
        "1",
    ),
    ("Secciones informativas con datos ficticios", "Los servicios y duraciones coinciden con el seed"): (
        f"{T_LANDING_CONTENT} > los servicios y duraciones coinciden con el seed",
        "2",
    ),
    ("Secciones informativas con datos ficticios", "Los horarios coinciden con el seed"): (
        f"{T_LANDING_CONTENT} > horarios y contacto son ficticios y coinciden con el seed",
        "3",
    ),
    ("Secciones informativas con datos ficticios", "Los datos ficticios se marcan visiblemente"): (
        f"{T_LANDING} > marca el sitio y los datos de contacto como demostración ; {T_LANDING_CONTENT} > horarios y contacto son ficticios y coinciden con el seed",
        "8 ; 3",
    ),
    ("Diálogo de acceso", "El diálogo se abre al entrar"): (
        f"{T_LOGIN_DIALOG} > abre con el diálogo, el heading, el formulario y el botón para recorrer la clínica",
        "14",
    ),
    ("Diálogo de acceso", "Ver la clínica cierra el diálogo"): (
        f"{T_LANDING} > abre el acceso al entrar y lo reabre con el CTA",
        "11",
    ),
    ("Diálogo de acceso", "El mensaje de sesión vencida cae en el formulario"): (
        f"{T_LOGIN_DIALOG} > muestra el aviso de sesión vencida dentro del formulario",
        "16",
    ),
    ("Diálogo de acceso", "Los nombres de los botones no colisionan"): (
        f"{T_LANDING} > mantiene un único botón Ingresar y un CTA accesible sin ocultar",
        "12",
    ),
    ("Diálogo de acceso", "El diálogo tiene backdrop y tarjeta tipo vidrio"): (
        VISUAL,
        "—",
    ),
    ("Diálogo de acceso", "El foco queda atrapado en el diálogo"): (
        VISUAL,
        "—",
    ),
    ("Foco y scroll del diálogo de acceso", "El foco inicia en Usuario"): (
        f"{T_LOGIN_DIALOG} > enfoca Usuario al abrir",
        "17",
    ),
    ("Foco y scroll del diálogo de acceso", "El scroll del fondo queda bloqueado"): (
        f"{T_LOGIN_DIALOG} > bloquea el overflow del body mientras está abierto y lo restaura al cerrar",
        "18",
    ),
    ("Reveal accesible de secciones", "Sin IntersectionObserver las secciones quedan visibles"): (
        f"{T_REVEAL} > sin IntersectionObserver queda revelada y su contenido es visible",
        "22",
    ),
    ("Reveal accesible de secciones", "Con observador inyectado pasa a revelado y limpia"): (
        f"{T_REVEAL} > con observador inyectado pasa de pendiente a revelada y limpia al desmontar",
        "23",
    ),
    ("Reveal accesible de secciones", "Reduced motion evita el estado pendiente"): (
        f"{T_REVEAL} > con movimiento reducido no queda pendiente y el contenido está en el DOM",
        "24",
    ),
    ("Reveal accesible de secciones", "El contenido sigue en el DOM durante la animación"): (
        f"{T_REVEAL} > con observador inyectado pasa de pendiente a revelada y limpia al desmontar",
        "23",
    ),
    ("Reveal accesible de secciones", "La animación de reveal es visual"): (
        CSS,
        "—",
    ),
}


def spec_scenarios(path: Path) -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    current_requirement: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Requirement: "):
            current_requirement = line.removeprefix("### Requirement: ").strip()
        elif line.startswith("#### Scenario: "):
            if current_requirement is None:
                raise ValueError(f"Escenario sin requisito en {path}")
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

    for spec in SPECS:
        for requirement, scenario in spec_scenarios(spec):
            number += 1
            seen.add((requirement, scenario))
            entry = TRACE.get((requirement, scenario))
            if entry is None:
                problems.append(f"sin test: {requirement} / {scenario}")
                continue
            test, mutation = entry
            if test not in (VISUAL, CSS):
                for single in test.split(" ; "):
                    if single not in nodes:
                        problems.append(f"test inexistente: {single}")
            rows.append(f"| {number} | {requirement} | {scenario} | `{test}` | {mutation} |")

    for requirement, scenario in TRACE:
        if (requirement, scenario) not in seen:
            problems.append(f"fila sin escenario en la spec: {requirement} / {scenario}")

    table = "\n".join(["| # | Requisito | Escenario | Test | Mutación |", "|---|---|---|---|---|", *rows])
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-35.py. No editar a mano.",
        f"tests listados por vitest: {len(nodes)}",
        f"escenarios en las specs delta: {number}",
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
            print("Faltan los marcadores de trazabilidad en verify-C-35.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
