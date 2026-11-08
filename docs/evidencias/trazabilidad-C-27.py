"""Trazabilidad de C-27: cada escenario de la spec delta a un test listado por Vitest.

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-27.py

Lee los escenarios de la spec, comprueba con `vitest list --json` que cada test existe,
genera trazabilidad-C-27.txt y regenera la tabla de verify-C-27.md. Termina con codigo 0
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
OUTPUT = EVIDENCE / "trazabilidad-C-27.txt"
VERIFY = EVIDENCE / "verify-C-27.md"
SPEC = (
    REPO / "openspec" / "changes" / "ui-agenda-diaria" / "specs" / "frontend-agenda" / "spec.md"
)
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

T_AGENDA_TIME = "src/features/agenda/agendaTime.test.ts"
T_CLOCK = "src/features/agenda/clock.test.ts"
T_AGENDA_CONFIG = "src/features/agenda/agendaConfig.test.ts"
T_TIME_GUARD = "src/features/agenda/agendaTimeGuard.test.ts"
T_AGENDA_LAYOUT = "src/features/agenda/agendaLayout.test.ts"
T_AGENDA_API = "src/features/agenda/agendaApi.test.ts"
T_USE_AGENDA = "src/features/agenda/useAgenda.test.tsx"
T_APP = "src/App.test.tsx"
T_MENU_FOR = "src/features/auth/menuFor.test.ts"
T_APP_SHELL = "src/shared/components/AppShell.test.tsx"
T_AGENDA_VIEW = "src/features/agenda/AgendaView.test.tsx"
T_AGENDA_TOOLBAR = "src/features/agenda/AgendaToolbar.test.tsx"
T_AGENDA_PAGE = "src/features/agenda/AgendaPage.test.tsx"
T_AGENDA_TABLE = "src/features/agenda/AgendaTable.test.tsx"
T_AGENDA_STYLES = "src/features/agenda/agendaStyles.test.ts"

TRACE: dict[str, dict[str, str]] = {
    "Ruta /agenda y pantalla principal": {
        "/ redirige a /agenda": f"{T_APP} > la ruta raíz redirige con replace a /agenda según el Clock y no renderiza HomePage",
        "Agenda habilitada en el menú de los tres roles": (
            f"{T_MENU_FOR} > menú del administrador incluye Agenda habilitada y los otros 5 ítems deshabilitados con Próximamente"
            f" ; {T_APP_SHELL} > renderiza Agenda como enlace habilitado en los tres roles y el resto deshabilitado con Próximamente"
        ),
    },
    "Carga con fetch y Clock inyectados": {
        "Carga con fetch y Clock inyectados": f"{T_AGENDA_PAGE} > carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible",
        "La fecha inicial respeta el borde de medianoche": f"{T_AGENDA_PAGE} > respeta el borde de medianoche en la fecha inicial y normaliza una fecha inválida con replace mostrando aviso",
    },
    "Conversión a hora local con el timezone de la respuesta": {
        "13:00Z se muestra como 10:00 en Buenos Aires": f"{T_AGENDA_TIME} > 13:00Z se convierte a 10:00 y 2026-11-16 en Buenos Aires y formatea la etiqueta del día",
        "El resultado es independiente de la zona del proceso": f"{T_AGENDA_TIME} > una zona con DST como America/New_York no altera la hora de Buenos Aires y el resultado no depende del proceso",
        "Las fechas de la request son locales": f"{T_AGENDA_API} > fetchAgenda pide GET /api/agenda con from y to locales sin sufijo Z, filtros opcionales y signal, y parsea el 200 completo",
    },
    "Eje de horas": {
        "Eje del lunes con datos": f"{T_AGENDA_LAYOUT} > calcula el eje 08:00 a 20:00 para el lunes 2026-11-16 con horarios 09:00–13:00 y 15:00–19:00, bloqueo y turnos",
        "Eje de un día vacío": f"{T_AGENDA_LAYOUT} > usa 08:00–20:00 en día vacío, expande rangos menores a 4 horas y clampea bloqueos y turnos en medianoche a [0, 1440]",
    },
    "Columnas por profesional": {
        "Tres columnas en orden estable": f"{T_AGENDA_VIEW} > dibuja el eje 08:00–20:00 y las tres columnas en orden alfabético estable con inactivo y columna vacía",
        "Profesional inactivo visible": f"{T_AGENDA_LAYOUT} > marca profesionales inactivos con (inactivo) y el filtro professionalId deja una sola columna",
        "Filtro por profesional deja una sola columna": f"{T_AGENDA_PAGE} > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha",
    },
    "Posición, alto y carriles de turnos superpuestos": {
        "Posición y alto del turno de Quiroga": f"{T_AGENDA_VIEW} > posiciona el turno de Quiroga 10:00–10:30 a 120 minutos del inicio con 30 minutos de alto y muestra la fecha local",
        "Carriles para un cancelado y un activo superpuestos": f"{T_AGENDA_VIEW} > reparte un turno cancelado y uno activo superpuestos en dos carriles y da alto mínimo al turno de cinco minutos",
        "Turno de cinco minutos con alto mínimo": f"{T_AGENDA_LAYOUT} > aplica alto mínimo a un turno de 5 minutos, clampea el inicio al eje y soporta un turno que termina a las 00:00",
    },
    "Horarios de atención, bloqueos y cancelados": {
        "Horarios y bloqueo del lunes": f"{T_AGENDA_VIEW} > dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado",
        "El cancelado permanece visible": f"{T_AGENDA_VIEW} > dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado",
    },
    "Color por estado más texto": {
        "Reservado y cancelado se distinguen por texto": f"{T_AGENDA_VIEW} > muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta",
        "Nombre accesible completo": f"{T_AGENDA_VIEW} > muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta",
    },
    "Filtros por profesional y sillón con estado en la URL": {
        "El filtro por sillón conserva horarios y bloqueos": f"{T_AGENDA_PAGE} > carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible",
        "El filtro por profesional filtra las tres colecciones": f"{T_AGENDA_PAGE} > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha",
        "Filtros combinados sin turnos": f"{T_AGENDA_PAGE} > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha",
    },
    "Navegación anterior, siguiente, Hoy y selector": {
        "Anterior y siguiente": f"{T_AGENDA_PAGE} > navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL",
        "Hoy y selector de fecha": f"{T_AGENDA_PAGE} > navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL",
    },
    "Estados de carga, vacío y error": {
        "Carga inicial": f"{T_AGENDA_PAGE} > muestra Cargando... con role=status en la carga inicial sin mostrar error",
        "Día sin turnos": f"{T_AGENDA_VIEW} > muestra No hay turnos para este día conservando la grilla y las bandas de horario cuando appointments está vacío",
        "Error de red con reintento": f"{T_AGENDA_PAGE} > muestra ErrorState con Reintentar ante error de red, al reintentar con 200 renderiza la agenda y Actualizar agenda refresca manualmente",
    },
    "401 delegado en C-26 y 403 visible": {
        "401 durante el uso": f"{T_AGENDA_PAGE} > delega el 401 de GET /api/agenda en C-26 descartando el token y redirigiendo a /login sin mostrar error local",
        "403 con la violación visible": f"{T_AGENDA_PAGE} > muestra la violación de un 403 en el error local sin cerrar sesión ni duplicar el banner global",
    },
    "Vista en lista accesible": {
        "Tabla accesible del lunes": f"{T_AGENDA_TABLE} > renderiza la tabla semántica con caption, encabezados con scope=col y filas en el mismo orden de la agenda",
        "Anuncio de la cantidad de turnos": f"{T_AGENDA_VIEW} > anuncia la cantidad de turnos con aria-live y alterna a la vista en lista con Ver como lista",
    },
    "Responsive para escritorio y tablet": {
        "Tablet de 768 por 1024": f"{T_AGENDA_STYLES} > define los tokens de agenda en tokens.css, scroll horizontal, sticky, controles >= 44x44 px y cero HEX en TSX",
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
        "Salida generada por docs/evidencias/trazabilidad-C-27.py. No editar a mano.",
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
            print("Faltan los marcadores de trazabilidad en verify-C-27.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}", encoding="utf-8", newline="\n"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
