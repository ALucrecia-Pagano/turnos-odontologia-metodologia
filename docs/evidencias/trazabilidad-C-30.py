"""Trazabilidad de C-30: cada escenario de las specs delta a un test listado por Vitest y su mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-30.py

Lee los escenarios de las specs delta de C-30 (frontend-agenda y frontend-appointment-actions),
comprueba con `vitest list --json` que cada test existe, genera trazabilidad-C-30.txt y
regenera la tabla de verify-C-30.md. Termina con código 0 solo si no falta ningún escenario,
no sobra ninguna fila y ningún test es compartido por más de un escenario.
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
OUTPUT = EVIDENCE / "trazabilidad-C-30.txt"
VERIFY = EVIDENCE / "verify-C-30.md"
SPECS_DIR = (
    REPO
    / "openspec"
    / "changes"
    / "archive"
    / "2026-11-13-ui-reprogramar-cancelar-y-estados"
    / "specs"
)
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

T_GRID = "src/features/agenda/AgendaGrid.accionable.test.tsx"
T_TABLE = "src/features/agenda/AgendaTable.accionable.test.tsx"
T_DETAIL = "src/features/appointments/AppointmentDetailDialog.test.tsx"
T_STATUS = "src/features/appointments/AppointmentStatusActions.test.tsx"
T_CANCEL = "src/features/appointments/AppointmentCancel.test.tsx"
T_RESCHEDULE = "src/features/appointments/AppointmentRescheduleDialog.test.tsx"
T_PAGE = "src/features/agenda/AgendaPage.acciones.test.tsx"

# Mapa de mutación por nombre del test
MUTATION_BY_TEST: dict[str, str] = {
    "cada turno en AgendaGrid es un button type=button accesible con aria-label completo": (
        "M1: forzar type='submit' en botón de turno de AgendaGrid"
    ),
    "al pulsar el turno invoca onSelectAppointment con los datos del turno": (
        "M2: omisión de llamada a onSelectAppointment en onClick de tarjeta"
    ),
    "con onSelectAppointment renderiza el botón Ver turno y al activarlo invoca el callback": (
        "M3: omisión de onSelectAppointment en botón Ver turno de AgendaTable"
    ),
    "sin onSelectAppointment conserva exactamente las 6 columnas originales": (
        "M4: inclusión incondicional de columna de acción en AgendaTable"
    ),
    "3.1 detalle renderiza datos completos en hora local con StatusBadge y botón cerrar": (
        "M5: omisión de onClose en botón Cerrar de AppointmentDetailDialog"
    ),
    "3.2 historial renderiza transiciones cronológicas con autor, estados y hora local": (
        "M6: alteración de nombre de autor en AppointmentHistoryList"
    ),
    "3.3 historial renderiza desglose de reprogramación con horario previo y nuevo en hora local": (
        "M7: intervalo previo idéntico en desglose de AppointmentHistoryList"
    ),
    "3.4 historial maneja error de carga mostrando aviso accesible sin romper el detalle": (
        "M8: alteración de mensaje de error accesible al fallar carga de historial"
    ),
    "4.1 botones contextuales según estado y rol": (
        "M9: alteración de texto informativo en turnos de estado terminal"
    ),
    "4.2 confirmar turno envía toStatus confirmado y cierra modal con éxito": (
        "M10: envío de toStatus 'atendido' en lugar de 'confirmado'"
    ),
    "4.3 marcar atendido envía toStatus atendido y cierra modal con éxito": (
        "M11: envío de toStatus 'ausente' en lugar de 'atendido'"
    ),
    "4.4 marcar ausente envía toStatus ausente y cierra modal con éxito": (
        "M12: envío de toStatus 'atendido' en lugar de 'ausente'"
    ),
    "4.5 rechazo 422 STATUS_CHANGE_TOO_EARLY expone alerta con código, mensaje y foco": (
        "M13: omisión de badge de código en alerta de AppointmentDetailDialog"
    ),
    "4.6 rechazo 422 INVALID_TRANSITION expone mensaje en alerta con foco": (
        "M14: omisión de foco automático al alert ante violaciones"
    ),
    "5.1 cancelar turno muestra subvista de confirmación in-dialog": (
        "M15: alteración de texto de advertencia en subvista de confirmación"
    ),
    "5.2 volver al detalle o Escape restaura la vista sin enviar petición": (
        "M16: omisión de restauración de estado al presionar Volver al detalle"
    ),
    "5.3 confirmar cancelación envía POST sin cuerpo y cierra modal": (
        "M17: envío de método HTTP DELETE en lugar de POST en cancelAppointment"
    ),
    "5.4 error 422 INVALID_TRANSITION en cancelación muestra alerta con foco": (
        "M18: omisión de asignación de violaciones ante fallo en handleConfirmCancel"
    ),
    "6.1 apertura con paciente y prestación en solo lectura y campos prellenados": (
        "M19: alteración de fecha prellenada por defecto en reprogramación"
    ),
    "6.2 reprogramación exitosa envía POST con offset exacto y cierra modal": (
        "M20: alteración de durationMin enviado en reprogramación"
    ),
    "6.3 rechazo 409 con violaciones múltiples de solapamiento muestra badges y alert con foco": (
        "M21: omisión de badges de código en alert de reprogramación"
    ),
    "6.4 rechazo 422 IN_THE_PAST expone mensaje del dominio en alert con foco": (
        "M22: alteración de mensaje de violación en alert de reprogramación"
    ),
    "6.5 error 400 marca campos con aria-invalid y mensaje inline": (
        "M23: omisión de atributo aria-invalid en input de duración"
    ),
    "6.6 cancelar reprogramación cierra diálogo y retorna foco": (
        "M24: omisión de onClose en botón Cancelar de reprogramación"
    ),
    "7.1 restringir acciones de odontólogo en turnos propios a cambios de estado e historial": (
        "M25: anulación de currentUser en AppointmentDetailDialog desde AgendaPage"
    ),
    "7.2 bloquear acciones e historial para odontólogo en turnos ajenos": (
        "M26: desactivación de restricción isDentistOther en AppointmentDetailDialog"
    ),
    "7.3 respuesta 403 FORBIDDEN_OPERATION muestra alerta sin cerrar sesión": (
        "M27: omisión de captura de kind forbidden en AppointmentDetailDialog"
    ),
    "7.4 seleccionar turno abre modal y mutación exitosa refresca la agenda": (
        "M28: omisión de llamada a state.refresh() en mutación exitosa"
    ),
    "7.5 confirmación emite anuncio Turno confirmado.": (
        "M29: alteración de texto de anuncio tras confirmación en AgendaPage"
    ),
    "7.6 marcar atendido emite anuncio Turno marcado como atendido.": (
        "M30: alteración de texto de anuncio tras marcar atendido en AgendaPage"
    ),
    "7.7 marcar ausente emite anuncio Turno marcado como ausente.": (
        "M31: alteración de texto de anuncio tras marcar ausente en AgendaPage"
    ),
    "7.8 cancelar emite anuncio Turno cancelado.": (
        "M32: alteración de texto de anuncio tras cancelar turno en AgendaPage"
    ),
    "7.9 reprogramar emite anuncio Turno reprogramado para el DD/MM/AAAA a las HH:MM.": (
        "M33: alteración de texto de anuncio tras reprogramar turno en AgendaPage"
    ),
    "3.5 alert muestra código estable y mensaje textual en español": (
        "M34: omisión de badge de código en alerta de AppointmentDetailDialog"
    ),
    "3.6 foco automático al alert de error": (
        "M35: omisión de foco automático al alert ante violaciones"
    ),
    "5.5 Escape sobre el diálogo con confirmación abierta vuelve a la vista de detalle": (
        "M36: omisión de guarda isConfirmingCancel en onClose de AppointmentDetailDialog"
    ),
    "7.10 al cerrar el detalle con el botón Cerrar el foco vuelve al botón del turno": (
        "M37: omisión de returnFocusRef en AppointmentDetailDialog desde AgendaPage"
    ),
    "7.11 al cerrar el detalle con Escape sobre el diálogo el foco vuelve al botón del turno": (
        "M38: omisión de guardado de triggerAppointmentBtnRef en AgendaPage"
    ),
    "5.6 al volver de la confirmación con Escape el foco queda en el botón Cancelar turno": (
        "M39: omisión del foco al botón Cancelar turno al volver de la confirmación"
    ),
    "5.7 al entrar a la confirmación se limpia el alert de una acción anterior": (
        "M40: omisión de setViolations([]) al entrar a la confirmación de cancelación"
    ),
    "un segundo Escape (evento cancel posterior) vuelve a llamar onClose": (
        "M41: omisión del reset diferido de closeHandledRef en Dialog"
    ),
}

# (capability, requirement, scenario) -> (test_node, mutation_desc)
TRACE: dict[tuple[str, str, str], tuple[str, str]] = {
    # frontend-agenda
    (
        "frontend-agenda",
        "Turnos accionables en la agenda",
        "Tarjeta de turno como botón accesible en la grilla",
    ): (
        f"{T_GRID} > cada turno en AgendaGrid es un button type=button accesible con aria-label completo",
        MUTATION_BY_TEST["cada turno en AgendaGrid es un button type=button accesible con aria-label completo"],
    ),
    (
        "frontend-agenda",
        "Turnos accionables en la agenda",
        "Selección de turno en la grilla abre el detalle",
    ): (
        f"{T_GRID} > al pulsar el turno invoca onSelectAppointment con los datos del turno",
        MUTATION_BY_TEST["al pulsar el turno invoca onSelectAppointment con los datos del turno"],
    ),
    (
        "frontend-agenda",
        "Turnos accionables en la agenda",
        "Fila de tabla con acción accesible Ver turno",
    ): (
        f"{T_TABLE} > con onSelectAppointment renderiza el botón Ver turno y al activarlo invoca el callback",
        MUTATION_BY_TEST["con onSelectAppointment renderiza el botón Ver turno y al activarlo invoca el callback"],
    ),

    # frontend-appointment-actions
    (
        "frontend-appointment-actions",
        "Diálogo de detalle del turno",
        "Apertura con datos completos y formato horario local",
    ): (
        f"{T_DETAIL} > 3.1 detalle renderiza datos completos en hora local con StatusBadge y botón cerrar",
        MUTATION_BY_TEST["3.1 detalle renderiza datos completos en hora local con StatusBadge y botón cerrar"],
    ),
    (
        "frontend-appointment-actions",
        "Diálogo de detalle del turno",
        "Retorno de foco al cerrar el detalle",
    ): (
        f"{T_PAGE} > 7.10 al cerrar el detalle con el botón Cerrar el foco vuelve al botón del turno",
        MUTATION_BY_TEST["7.10 al cerrar el detalle con el botón Cerrar el foco vuelve al botón del turno"],
    ),
    (
        "frontend-appointment-actions",
        "Consulta y visualización del historial de cambios",
        "Historial renderiza transiciones cronológicas con hora local",
    ): (
        f"{T_DETAIL} > 3.2 historial renderiza transiciones cronológicas con autor, estados y hora local",
        MUTATION_BY_TEST["3.2 historial renderiza transiciones cronológicas con autor, estados y hora local"],
    ),
    (
        "frontend-appointment-actions",
        "Consulta y visualización del historial de cambios",
        "Historial renderiza desglose de reprogramación con horario previo y nuevo",
    ): (
        f"{T_DETAIL} > 3.3 historial renderiza desglose de reprogramación con horario previo y nuevo en hora local",
        MUTATION_BY_TEST["3.3 historial renderiza desglose de reprogramación con horario previo y nuevo en hora local"],
    ),
    (
        "frontend-appointment-actions",
        "Consulta y visualización del historial de cambios",
        "Error al cargar historial muestra aviso accesible",
    ): (
        f"{T_DETAIL} > 3.4 historial maneja error de carga mostrando aviso accesible sin romper el detalle",
        MUTATION_BY_TEST["3.4 historial maneja error de carga mostrando aviso accesible sin romper el detalle"],
    ),
    (
        "frontend-appointment-actions",
        "Cambios de estado ordinarios",
        "Confirmación exitosa de turno reservado",
    ): (
        f"{T_STATUS} > 4.2 confirmar turno envía toStatus confirmado y cierra modal con éxito",
        MUTATION_BY_TEST["4.2 confirmar turno envía toStatus confirmado y cierra modal con éxito"],
    ),
    (
        "frontend-appointment-actions",
        "Cambios de estado ordinarios",
        "Rechazo 422 por marcar atendido antes del inicio",
    ): (
        f"{T_STATUS} > 4.5 rechazo 422 STATUS_CHANGE_TOO_EARLY expone alerta con código, mensaje y foco",
        MUTATION_BY_TEST["4.5 rechazo 422 STATUS_CHANGE_TOO_EARLY expone alerta con código, mensaje y foco"],
    ),
    (
        "frontend-appointment-actions",
        "Cambios de estado ordinarios",
        "Rechazo 422 por transición desde estado terminal",
    ): (
        f"{T_STATUS} > 4.6 rechazo 422 INVALID_TRANSITION expone mensaje en alerta con foco",
        MUTATION_BY_TEST["4.6 rechazo 422 INVALID_TRANSITION expone mensaje en alerta con foco"],
    ),
    (
        "frontend-appointment-actions",
        "Cancelación de turnos con confirmación interna",
        "Cancelación confirmada pasa turno a cancelado",
    ): (
        f"{T_CANCEL} > 5.3 confirmar cancelación envía POST sin cuerpo y cierra modal",
        MUTATION_BY_TEST["5.3 confirmar cancelación envía POST sin cuerpo y cierra modal"],
    ),
    (
        "frontend-appointment-actions",
        "Cancelación de turnos con confirmación interna",
        "Desestimar confirmación retorna al detalle",
    ): (
        f"{T_CANCEL} > 5.2 volver al detalle o Escape restaura la vista sin enviar petición",
        MUTATION_BY_TEST["5.2 volver al detalle o Escape restaura la vista sin enviar petición"],
    ),
    (
        "frontend-appointment-actions",
        "Cancelación de turnos con confirmación interna",
        "Error 422 al intentar cancelar turno terminal",
    ): (
        f"{T_CANCEL} > 5.4 error 422 INVALID_TRANSITION en cancelación muestra alerta con foco",
        MUTATION_BY_TEST["5.4 error 422 INVALID_TRANSITION en cancelación muestra alerta con foco"],
    ),
    (
        "frontend-appointment-actions",
        "Formulario y flujo de reprogramación",
        "Reprogramación exitosa revalida agenda y vuelve a reservado",
    ): (
        f"{T_RESCHEDULE} > 6.2 reprogramación exitosa envía POST con offset exacto y cierra modal",
        MUTATION_BY_TEST["6.2 reprogramación exitosa envía POST con offset exacto y cierra modal"],
    ),
    (
        "frontend-appointment-actions",
        "Formulario y flujo de reprogramación",
        "Conflicto 409 por solapamiento de agenda",
    ): (
        f"{T_RESCHEDULE} > 6.3 rechazo 409 con violaciones múltiples de solapamiento muestra badges y alert con foco",
        MUTATION_BY_TEST["6.3 rechazo 409 con violaciones múltiples de solapamiento muestra badges y alert con foco"],
    ),
    (
        "frontend-appointment-actions",
        "Formulario y flujo de reprogramación",
        "Rechazo 422 por reprogramar al pasado",
    ): (
        f"{T_RESCHEDULE} > 6.4 rechazo 422 IN_THE_PAST expone mensaje del dominio en alert con foco",
        MUTATION_BY_TEST["6.4 rechazo 422 IN_THE_PAST expone mensaje del dominio en alert con foco"],
    ),
    (
        "frontend-appointment-actions",
        "Formulario y flujo de reprogramación",
        "Error de entrada 400 marca campos con aria-invalid",
    ): (
        f"{T_RESCHEDULE} > 6.5 error 400 marca campos con aria-invalid y mensaje inline",
        MUTATION_BY_TEST["6.5 error 400 marca campos con aria-invalid y mensaje inline"],
    ),
    (
        "frontend-appointment-actions",
        "Control de acceso por rol en las acciones",
        "Odontólogo cambia estado de turno propio exitosamente",
    ): (
        f"{T_PAGE} > 7.1 restringir acciones de odontólogo en turnos propios a cambios de estado e historial",
        MUTATION_BY_TEST["7.1 restringir acciones de odontólogo en turnos propios a cambios de estado e historial"],
    ),
    (
        "frontend-appointment-actions",
        "Control de acceso por rol en las acciones",
        "Odontólogo en turno ajeno tiene vista de solo lectura",
    ): (
        f"{T_PAGE} > 7.2 bloquear acciones e historial para odontólogo en turnos ajenos",
        MUTATION_BY_TEST["7.2 bloquear acciones e historial para odontólogo en turnos ajenos"],
    ),
    (
        "frontend-appointment-actions",
        "Control de acceso por rol en las acciones",
        "Rechazo 403 muestra mensaje de permiso denegado",
    ): (
        f"{T_PAGE} > 7.3 respuesta 403 FORBIDDEN_OPERATION muestra alerta sin cerrar sesión",
        MUTATION_BY_TEST["7.3 respuesta 403 FORBIDDEN_OPERATION muestra alerta sin cerrar sesión"],
    ),
    (
        "frontend-appointment-actions",
        "Gestión de errores del dominio en alertas accesibles",
        "Alert muestra código estable y mensaje textual en español",
    ): (
        f"{T_DETAIL} > 3.5 alert muestra código estable y mensaje textual en español",
        MUTATION_BY_TEST["3.5 alert muestra código estable y mensaje textual en español"],
    ),
    (
        "frontend-appointment-actions",
        "Gestión de errores del dominio en alertas accesibles",
        "Foco automático al alert de error",
    ): (
        f"{T_DETAIL} > 3.6 foco automático al alert de error",
        MUTATION_BY_TEST["3.6 foco automático al alert de error"],
    ),
    (
        "frontend-appointment-actions",
        "Anuncios accesibles y refresco de agenda",
        "Anuncio accesible y refresco tras confirmar turno",
    ): (
        f"{T_PAGE} > 7.5 confirmación emite anuncio Turno confirmado.",
        MUTATION_BY_TEST["7.5 confirmación emite anuncio Turno confirmado."],
    ),
    (
        "frontend-appointment-actions",
        "Anuncios accesibles y refresco de agenda",
        "Anuncio accesible y refresco tras marcar atendido",
    ): (
        f"{T_PAGE} > 7.6 marcar atendido emite anuncio Turno marcado como atendido.",
        MUTATION_BY_TEST["7.6 marcar atendido emite anuncio Turno marcado como atendido."],
    ),
    (
        "frontend-appointment-actions",
        "Anuncios accesibles y refresco de agenda",
        "Anuncio accesible y refresco tras marcar ausente",
    ): (
        f"{T_PAGE} > 7.7 marcar ausente emite anuncio Turno marcado como ausente.",
        MUTATION_BY_TEST["7.7 marcar ausente emite anuncio Turno marcado como ausente."],
    ),
    (
        "frontend-appointment-actions",
        "Anuncios accesibles y refresco de agenda",
        "Anuncio accesible y refresco tras cancelar turno",
    ): (
        f"{T_PAGE} > 7.8 cancelar emite anuncio Turno cancelado.",
        MUTATION_BY_TEST["7.8 cancelar emite anuncio Turno cancelado."],
    ),
    (
        "frontend-appointment-actions",
        "Anuncios accesibles y refresco de agenda",
        "Anuncio accesible y refresco tras reprogramar turno",
    ): (
        f"{T_PAGE} > 7.9 reprogramar emite anuncio Turno reprogramado para el DD/MM/AAAA a las HH:MM.",
        MUTATION_BY_TEST["7.9 reprogramar emite anuncio Turno reprogramado para el DD/MM/AAAA a las HH:MM."],
    ),

    # Adaptabilidad visual (verificación independiente por capturas)
    (
        "frontend-appointment-actions",
        "Adaptabilidad visual de las interfaces de turno",
        "Visualización en escritorio a 1440 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-30-detalle-1440.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
    (
        "frontend-appointment-actions",
        "Adaptabilidad visual de las interfaces de turno",
        "Visualización en tablet a 768 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-30-detalle-768.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
    (
        "frontend-appointment-actions",
        "Adaptabilidad visual de las interfaces de turno",
        "Visualización en móvil a 390 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-30-detalle-390.png`, `docs/evidencias/capturas/C-30-reprogramar-409-390.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
}


def load_spec_scenarios() -> list[tuple[str, str, str]]:
    scenarios: list[tuple[str, str, str]] = []
    spec_files = [
        SPECS_DIR / "frontend-agenda" / "spec.md",
        SPECS_DIR / "frontend-appointment-actions" / "spec.md",
    ]
    for spec_path in spec_files:
        cap = spec_path.parent.name
        current_req: str | None = None
        for line in spec_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("### Requirement: "):
                current_req = line.removeprefix("### Requirement: ").strip()
            elif line.startswith("#### Scenario: "):
                if current_req is None:
                    raise ValueError(f"Escenario sin requisito en {spec_path}")
                sc = line.removeprefix("#### Scenario: ").strip()
                scenarios.append((cap, current_req, sc))
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
    seen: set[tuple[str, str, str]] = set()
    seen_test_nodes: set[str] = set()

    for cap, req, scenario in load_spec_scenarios():
        number += 1
        seen.add((cap, req, scenario))
        mapping = TRACE.get((cap, req, scenario))
        if mapping is None:
            problems.append(f"sin mapeo: [{cap}] {req} / {scenario}")
            continue
        test_str, mut_str = mapping
        # Validar existencia de test si no es verificación visual
        if not test_str.startswith("Captura a cargo de Claude"):
            if test_str in seen_test_nodes:
                problems.append(f"test compartido por más de un escenario: {test_str}")
            seen_test_nodes.add(test_str)
            for single in test_str.split(" ; "):
                if single.strip() not in nodes:
                    problems.append(f"test inexistente: {single.strip()}")
        rows.append(
            f"| {number} | `{cap}` | {req} | {scenario} | {test_str} | {mut_str} |"
        )

    for (cap, req, scenario) in TRACE:
        if (cap, req, scenario) not in seen:
            problems.append(f"fila sin escenario en spec: [{cap}] {req} / {scenario}")

    table = "\n".join(
        [
            "| # | Capacidad | Requisito | Escenario | Test Vitest / Verificación | Mutación asociada |",
            "|---|---|---|---|---|---|",
            *rows,
        ]
    )

    visual_count = 3
    vitest_scenarios = number - visual_count
    report_lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-30.py. No editar a mano.",
        f"tests listados por vitest en el repo: {len(nodes)}",
        f"escenarios totales en las specs delta de C-30: {number}",
        f"escenarios verificados con tests de Vitest: {vitest_scenarios}",
        f"escenarios de adaptabilidad visual (verificación visual independiente): {visual_count}",
        *problems,
        f"problemas: {len(problems)}",
        f"{number} escenarios, {len(problems)} problemas",
    ]
    report = "\n".join(report_lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)

    if VERIFY.exists():
        verify = VERIFY.read_text(encoding="utf-8")
        start = verify.find(TABLE_START)
        end = verify.find(TABLE_END)
        if start == -1 or end == -1:
            print("Faltan marcadores de trazabilidad en verify-C-30.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
            encoding="utf-8",
            newline="\n",
        )

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
