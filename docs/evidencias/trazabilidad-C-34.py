"""Trazabilidad de C-34: cada escenario de las specs delta a un test y a una mutacion.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-34.py

Lee los escenarios de las dos specs delta, comprueba con `vitest list --json` que
cada test existe, genera trazabilidad-C-34.txt y regenera la tabla de
verify-C-34.md. Los escenarios de verificacion visual o de CSS se marcan como
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
OUTPUT = EVIDENCE / "trazabilidad-C-34.txt"
VERIFY = EVIDENCE / "verify-C-34.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

SPECS = (
    REPO / "openspec" / "changes" / "archive" / "2026-11-09-ui-identidad-visual" / "specs" / "frontend-foundation" / "spec.md",
    REPO / "openspec" / "changes" / "archive" / "2026-11-09-ui-identidad-visual" / "specs" / "frontend-auth-session" / "spec.md",
)

T_STATUS = "src/shared/styles/appointmentStatusTokens.test.ts"
T_TOKENS = "src/shared/styles/tokens.test.ts"
T_AQUA = "src/shared/styles/aquaPalette.test.ts"
T_FONTS = "src/shared/styles/fonts.test.ts"
T_APP_SHELL_BRAND = "src/shared/components/AppShellBrand.test.tsx"
T_LOGIN_BRAND = "src/features/login/LoginBrand.test.tsx"
T_LOGIN_CAROUSEL = "src/features/login/LoginCarousel.test.tsx"
T_README = "src/test/readmeCredits.test.ts"
T_SMOKE = "src/test/smoke.test.tsx"

VISUAL = "— (verificación visual)"
CSS = "— (verificación CSS/grep)"
NO_MUTATION = "— (test existente actualizado)"


TRACE: dict[tuple[str, str], tuple[str, str]] = {
    ("Tokens de diseño y colores por estado", "El mapa cubre los cinco estados sin undefined"): (
        f"{T_STATUS} > el mapa cubre los cinco estados sin undefined",
        NO_MUTATION,
    ),
    ("Tokens de diseño y colores por estado", "Cada par texto y fondo cumple contraste AA"): (
        f"{T_STATUS} > cada par texto y fondo cumple contraste AA",
        NO_MUTATION,
    ),
    ("Tokens de diseño y colores por estado", "Los tokens de paleta usados como texto cumplen contraste AA"): (
        f"{T_AQUA} > mantiene los contrastes de texto del design",
        "2",
    ),
    ("Tokens de diseño y colores por estado", "El foco es visible"): (
        f"{T_TOKENS} > el foco es visible",
        NO_MUTATION,
    ),
    ("Tokens de diseño y colores por estado", "La familia base del sistema se conserva como fallback"): (
        f"{T_TOKENS} > usa el system font stack en el reset ; {T_FONTS} > el body conserva la base y usa Manrope después",
        "4",
    ),
    ("Tipografías autoalojadas sin CDN", "Las dependencias y los imports de fuentes están en el frontend"): (
        f"{T_FONTS} > declara las dependencias y las importa antes de los estilos en el entry point",
        "5",
    ),
    ("Tipografías autoalojadas sin CDN", "No hay fuentes externas ni CDN"): (
        f"{T_FONTS} > no usa URLs de Google Fonts ni CDNs externos en src",
        "6",
    ),
    ("Tipografías autoalojadas sin CDN", "Las familias se aplican con tokens y fallback"): (
        f"{T_FONTS} > define Jost para títulos y Manrope para texto con fallback al system stack",
        "3",
    ),
    ("Barra única con la marca Aqua", "Barra de escritorio con la marca completa"): (
        f"{T_APP_SHELL_BRAND} > muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica",
        "7",
    ),
    ("Barra única con la marca Aqua", "Barra de tablet con solo Aqua y máximo dos renglones"): (
        VISUAL,
        "—",
    ),
    ("Barra única con la marca Aqua", "La barra usa el isotipo oscuro"): (
        f"{T_APP_SHELL_BRAND} > muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica",
        "7",
    ),
    ("Barra única con la marca Aqua", "El título de página no se ve como una segunda barra"): (
        VISUAL,
        "—",
    ),
    ("Créditos de assets y tipografías", "El README acredita fotos, logo y tipografías"): (
        f"{T_README} > documenta las fotografías, el logo y la licencia de las tipografías",
        "16",
    ),
    ("Logo del login sobre fondo oscuro", "El login muestra la variante de logo clara"): (
        f"{T_LOGIN_BRAND} > muestra el logo claro, el heading accesible y la bajada",
        "9",
    ),
    ("Logo del login sobre fondo oscuro", "El fondo inmediato del logo es oscuro"): (
        VISUAL,
        "—",
    ),
    ("Logo del login sobre fondo oscuro", "El encabezado accesible del login se conserva"): (
        f"{T_LOGIN_BRAND} > muestra el logo claro, el heading accesible y la bajada ; {T_SMOKE} > monta App y muestra el título",
        "9",
    ),
    ("Bajada y tarjeta del login", "La bajada es visible"): (
        f"{T_LOGIN_BRAND} > muestra el logo claro, el heading accesible y la bajada",
        "9",
    ),
    ("Bajada y tarjeta del login", "La tarjeta tipo vidrio sobre overlay navy"): (
        VISUAL,
        "—",
    ),
    ("Carrusel decorativo del login", "Avanza al llamar al ticker y vuelve a la primera tras la quinta"): (
        f"{T_LOGIN_CAROUSEL} > inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta",
        "11",
    ),
    ("Pausa y ciclo de vida del carrusel", "La pausa detiene el avance"): (
        f"{T_LOGIN_CAROUSEL} > pausa y reanuda el avance sin aria-pressed",
        "12",
    ),
    ("Pausa y ciclo de vida del carrusel", "Reduced motion desactiva rotación y Ken Burns"): (
        f"{T_LOGIN_CAROUSEL} > reduced motion desactiva la rotación y el Ken Burns",
        "13",
    ),
    ("Pausa y ciclo de vida del carrusel", "El ticker se cancela al desmontar"): (
        f"{T_LOGIN_CAROUSEL} > cancela el ticker al desmontar",
        "14",
    ),
    ("Detección de reduced motion en producción", "Sin matchMedia el login renderiza sin error"): (
        f"{T_LOGIN_BRAND} > renderiza sin window.matchMedia, usa reduced motion falso y permite avanzar el carrusel",
        "10",
    ),
    ("Detección de reduced motion en producción", "El CSS desactiva Ken Burns y fundido con reduced motion"): (
        CSS,
        "—",
    ),
    ("Fotos decorativas y Ken Burns", "Las fotos son decorativas y accesibles"): (
        f"{T_LOGIN_CAROUSEL} > muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa",
        "15",
    ),
    ("Fotos decorativas y Ken Burns", "La clase de Ken Burns está solo en la foto activa"): (
        f"{T_LOGIN_CAROUSEL} > muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa",
        "15",
    ),
    ("Fotos decorativas y Ken Burns", "Reduced motion quita la clase de Ken Burns"): (
        f"{T_LOGIN_CAROUSEL} > reduced motion desactiva la rotación y el Ken Burns",
        "13",
    ),
    ("Fotos decorativas y Ken Burns", "Duración y reinicio del Ken Burns"): (
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
        "Salida generada por docs/evidencias/trazabilidad-C-34.py. No editar a mano.",
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
            print("Faltan los marcadores de trazabilidad en verify-C-34.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
