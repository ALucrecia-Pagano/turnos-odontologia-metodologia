"""Escenarios de specs-requisitos-concisos: los MODIFIED conservan los escenarios vigentes.

Uso, desde la raiz del repo:

    python docs/evidencias/escenarios-specs.py > docs/evidencias/escenarios-specs.txt

Para cada requisito bajo `## MODIFIED Requirements` de las specs delta del change,
busca el requisito del mismo titulo en `openspec/specs/<capacidad>/spec.md` y compara,
caracter por caracter, cada bloque `#### Scenario:` (titulo y cuerpo, hasta el siguiente
escenario o requisito). Solo se quitan los saltos de linea finales de cada bloque, que
separan un bloque del siguiente. Los finales de linea se normalizan a LF antes de comparar
(en Windows, git con autocrlf puede dejar en CRLF la copia de trabajo de un archivo que en
el repo esta en LF); la salida informa el final de linea de cada archivo leido. Termina con
codigo 0 solo si los escenarios son identicos en cantidad, orden y contenido.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHANGE_SPECS = REPO / "openspec" / "changes" / "specs-requisitos-concisos" / "specs"
MAIN_SPECS = REPO / "openspec" / "specs"
CAPABILITIES = ("appointment-lifecycle", "appointment-scheduling")

REQUIREMENT = re.compile(r"^### Requirement: (.+?)\s*$", re.MULTILINE)
SECTION = re.compile(r"^## ", re.MULTILINE)
SCENARIO = re.compile(r"^#### Scenario:", re.MULTILINE)


def read(path: Path) -> str:
    """Lee el archivo en UTF-8, informa su final de linea y lo devuelve normalizado a LF."""
    with path.open(encoding="utf-8", newline="") as handle:
        raw = handle.read()
    eol = "CRLF" if "\r\n" in raw else "LF"
    print(f"  leido ({eol}): {path.relative_to(REPO).as_posix()}")
    return raw.replace("\r\n", "\n")


def section(text: str, title: str) -> str:
    """Devuelve el cuerpo de la seccion `## {title}` hasta la siguiente `## `."""
    match = re.search(rf"^## {re.escape(title)}\s*$", text, re.MULTILINE)
    if match is None:
        return ""
    rest = text[match.end():]
    end = SECTION.search(rest)
    return rest if end is None else rest[: end.start()]


def requirements(text: str) -> dict[str, str]:
    """Titulo -> bloque del requisito (hasta el siguiente requisito o seccion)."""
    blocks: dict[str, str] = {}
    matches = list(REQUIREMENT.finditer(text))
    for index, match in enumerate(matches):
        start = match.end()
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:stop]
        end = SECTION.search(body)
        blocks[match.group(1)] = body if end is None else body[: end.start()]
    return blocks


def scenarios(block: str) -> list[str]:
    starts = [m.start() for m in SCENARIO.finditer(block)]
    return [
        block[start: starts[i + 1] if i + 1 < len(starts) else len(block)].rstrip("\n")
        for i, start in enumerate(starts)
    ]


def main() -> int:
    total_requirements = 0
    total_scenarios = 0
    differences: list[str] = []

    for capability in CAPABILITIES:
        print(f"## {capability}")
        delta = read(CHANGE_SPECS / capability / "spec.md")
        main_spec = read(MAIN_SPECS / capability / "spec.md")
        modified = requirements(section(delta, "MODIFIED Requirements"))
        current = requirements(main_spec)

        for title, block in modified.items():
            total_requirements += 1
            new = scenarios(block)
            if title not in current:
                differences.append(f"{capability} / {title}: no existe en openspec/specs")
                print(f"  FALTA  {title}")
                continue
            old = scenarios(current[title])
            total_scenarios += len(new)
            problems = 0
            if len(new) != len(old):
                differences.append(
                    f"{capability} / {title}: {len(new)} escenarios en el delta, "
                    f"{len(old)} en openspec/specs"
                )
                problems += 1
            for position, (a, b) in enumerate(zip(new, old), start=1):
                if a != b:
                    first = next(
                        (i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                        min(len(a), len(b)),
                    )
                    differences.append(
                        f"{capability} / {title} / escenario {position}: "
                        f"difiere desde el caracter {first}"
                    )
                    problems += 1
            status = "OK" if problems == 0 else "DIFF"
            print(f"  {status:5}  {len(new):3} escenarios  {title}")
        print()

    for difference in differences:
        print(f"DIFERENCIA: {difference}")
    print(
        f"{total_requirements} requisitos, {total_scenarios} escenarios, "
        f"{len(differences)} diferencias"
    )
    return 0 if not differences else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
