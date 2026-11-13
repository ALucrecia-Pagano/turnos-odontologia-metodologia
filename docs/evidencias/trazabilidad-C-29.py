"""Trazabilidad de C-29: cada escenario de las specs delta a un test listado por Vitest y su mutación.

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/trazabilidad-C-29.py

Lee los escenarios de las specs delta de C-29 (frontend-agenda y frontend-appointment-form),
comprueba con `vitest list --json` que cada test existe, genera trazabilidad-C-29.txt y
regenera la tabla de verify-C-29.md. Termina con código 0 solo si no falta ningún escenario,
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
OUTPUT = EVIDENCE / "trazabilidad-C-29.txt"
VERIFY = EVIDENCE / "verify-C-29.md"
SPECS_DIR = REPO / "openspec" / "changes" / "ui-dar-turno-con-errores" / "specs"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

T_DIALOG = "src/shared/components/Dialog.test.tsx"
T_CLIENT_VIOLATIONS = "src/shared/api/client.violations.test.ts"
T_PATIENT_SEARCH = "src/features/appointments/PatientSearchGroup.test.tsx"
T_FORM = "src/features/appointments/AppointmentFormDialog.test.tsx"
T_TOOLBAR = "src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx"
T_PAGE = "src/features/agenda/AgendaPage.nuevoTurno.test.tsx"

# Mapa de mutación por nombre del test
MUTATION_BY_TEST: dict[str, str] = {
    "abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby": (
        "M1: eliminación de dialog.setAttribute('open', '')"
    ),
    "Escape llama onClose exactamente una vez": (
        "M2: cambio de condición event.key !== 'Escape' por 'Enter'"
    ),
    "al pasar open de true a false el foco vuelve a returnFocusRef": (
        "M3: eliminación de llamada returnFocusRef?.current?.focus()"
    ),
    "captura conflictingAppointmentId, conflictingBlockId, conflictingInterval y referenceKind": (
        "M4: omisión de mapeo de referenceKind en violation"
    ),
    "renderizado inicial: input de búsqueda, botón Buscar paciente habilitado y sin radio buttons": (
        "M5: forzar disabled=true en botón Buscar paciente"
    ),
    "búsqueda con resultados muestra radio buttons con nombre y DNI": (
        "M6: omisión de DNI en etiqueta accesible de paciente"
    ),
    "búsqueda sin resultados muestra aviso accesible y sin radio buttons": (
        "M7: alteración de texto 'No se encontraron pacientes'"
    ),
    "selección por clic o teclado invoca onSelectPatient con el id correspondiente": (
        "M8: omisión de llamada a onSelectPatient en radio onChange"
    ),
    "apertura y foco inicial": (
        "M9: omisión de foco automático en patientSearchInputRef"
    ),
    "prellenado con fecha y filtros activos": (
        "M10: inicialización de professionalId sin valor por defecto"
    ),
    "sin filtros activos los selectores quedan sin selección": (
        "M11: inicialización de chairId con valor por defecto cuando initialChairId es nulo"
    ),
    "duración sugerida al elegir prestación": (
        "M12: asignación de duración fija 15 min en lugar de sugerida"
    ),
    "edición manual de duración se conserva": (
        "M13: forzar duración fija 60 min en onChange de duración"
    ),
    "armado de startAt con offset exacto para la fecha elegida y timezone de la API": (
        "M14: hardcodeo de sufijo 'Z' en lugar de offset local calculado"
    ),
    "envío exitoso 201 cierra el modal, llama onSuccess con los datos del turno y devuelve foco": (
        "M15: omisión de invocación a onSuccess tras 201"
    ),
    "respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias": (
        "M16: omisión de renderizado de badge con code de violación"
    ),
    "rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos": (
        "M17: desactivación de manejo de kind unprocessable"
    ),
    "mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline": (
        "M18: omisión de actualización de setFieldErrors ante error 400"
    ),
    "respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión": (
        "M19: alteración de condición de kind forbidden"
    ),
    "foco al resumen de alerta ante fallo": (
        "M20: omisión de foco al alert ante violaciones"
    ),
    "pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura": (
        "M21: no-op en onClick de botón Cancelar"
    ),
    "Escape cierra sin enviar solicitudes y devuelve el foco": (
        "M22: no-op en handleDialogClose ante Escape"
    ),
    "visible para recepción y dispara onNewAppointment al clic": (
        "M23: restricción de botón Nuevo turno solo a rol administrador"
    ),
    "visible para administrador": (
        "M24: restricción de botón Nuevo turno solo a rol recepcion"
    ),
    "no visible para odontólogo": (
        "M25: mostrar botón Nuevo turno para todos los roles"
    ),
    "al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda": (
        "M26: omisión de refresh en onSuccess de AppointmentFormDialog"
    ),
    "tras alta exitosa (201) anuncia el turno creado en una región de estado accesible": (
        "M27: alteración del mensaje de anuncio en AgendaPage"
    ),
}

# (capability, requirement, scenario) -> (test_node, mutation_desc)
TRACE: dict[tuple[str, str, str], tuple[str, str]] = {
    # frontend-agenda
    (
        "frontend-agenda",
        "Acción Nuevo turno en la agenda",
        "Visible para recepción",
    ): (
        f"{T_TOOLBAR} > visible para recepción y dispara onNewAppointment al clic",
        MUTATION_BY_TEST["visible para recepción y dispara onNewAppointment al clic"],
    ),
    (
        "frontend-agenda",
        "Acción Nuevo turno en la agenda",
        "Visible para administrador",
    ): (
        f"{T_TOOLBAR} > visible para administrador",
        MUTATION_BY_TEST["visible para administrador"],
    ),
    (
        "frontend-agenda",
        "Acción Nuevo turno en la agenda",
        "No visible para odontólogo",
    ): (
        f"{T_TOOLBAR} > no visible para odontólogo",
        MUTATION_BY_TEST["no visible para odontólogo"],
    ),
    (
        "frontend-agenda",
        "Acción Nuevo turno en la agenda",
        "Refresco tras alta",
    ): (
        f"{T_PAGE} > al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda",
        MUTATION_BY_TEST["al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda"],
    ),

    # frontend-appointment-form
    (
        "frontend-appointment-form",
        "Primitiva de diálogo modal accesible",
        "Abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby",
    ): (
        f"{T_DIALOG} > abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby",
        MUTATION_BY_TEST["abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby"],
    ),
    (
        "frontend-appointment-form",
        "Primitiva de diálogo modal accesible",
        "Escape llama onClose exactamente una vez",
    ): (
        f"{T_DIALOG} > Escape llama onClose exactamente una vez",
        MUTATION_BY_TEST["Escape llama onClose exactamente una vez"],
    ),
    (
        "frontend-appointment-form",
        "Primitiva de diálogo modal accesible",
        "Al pasar open de true a false el foco vuelve a returnFocusRef",
    ): (
        f"{T_DIALOG} > al pasar open de true a false el foco vuelve a returnFocusRef",
        MUTATION_BY_TEST["al pasar open de true a false el foco vuelve a returnFocusRef"],
    ),
    (
        "frontend-appointment-form",
        "Apertura y foco inicial",
        "Apertura y foco inicial",
    ): (
        f"{T_FORM} > apertura y foco inicial",
        MUTATION_BY_TEST["apertura y foco inicial"],
    ),
    (
        "frontend-appointment-form",
        "Prellenado contextual desde la agenda",
        "Prellenado con fecha y filtros activos",
    ): (
        f"{T_FORM} > prellenado con fecha y filtros activos",
        MUTATION_BY_TEST["prellenado con fecha y filtros activos"],
    ),
    (
        "frontend-appointment-form",
        "Prellenado contextual desde la agenda",
        "Sin filtros activos los selectores quedan sin selección",
    ): (
        f"{T_FORM} > sin filtros activos los selectores quedan sin selección",
        MUTATION_BY_TEST["sin filtros activos los selectores quedan sin selección"],
    ),
    (
        "frontend-appointment-form",
        "Búsqueda y selección de paciente",
        "Búsqueda con resultados muestra radio buttons",
    ): (
        f"{T_PATIENT_SEARCH} > búsqueda con resultados muestra radio buttons con nombre y DNI",
        MUTATION_BY_TEST["búsqueda con resultados muestra radio buttons con nombre y DNI"],
    ),
    (
        "frontend-appointment-form",
        "Búsqueda y selección de paciente",
        "Búsqueda sin coincidencias muestra aviso",
    ): (
        f"{T_PATIENT_SEARCH} > búsqueda sin resultados muestra aviso accesible y sin radio buttons",
        MUTATION_BY_TEST["búsqueda sin resultados muestra aviso accesible y sin radio buttons"],
    ),
    (
        "frontend-appointment-form",
        "Búsqueda y selección de paciente",
        "Selección de radio button asigna patientId",
    ): (
        f"{T_PATIENT_SEARCH} > selección por clic o teclado invoca onSelectPatient con el id correspondiente",
        MUTATION_BY_TEST["selección por clic o teclado invoca onSelectPatient con el id correspondiente"],
    ),
    (
        "frontend-appointment-form",
        "Sugerencia y edición de duración",
        "Duración sugerida al elegir prestación",
    ): (
        f"{T_FORM} > duración sugerida al elegir prestación",
        MUTATION_BY_TEST["duración sugerida al elegir prestación"],
    ),
    (
        "frontend-appointment-form",
        "Sugerencia y edición de duración",
        "Edición manual de duración",
    ): (
        f"{T_FORM} > edición manual de duración se conserva",
        MUTATION_BY_TEST["edición manual de duración se conserva"],
    ),
    (
        "frontend-appointment-form",
        "Composición de fecha, hora y timezone",
        "startAt incluye offset horario exacto para la fecha elegida",
    ): (
        f"{T_FORM} > armado de startAt con offset exacto para la fecha elegida y timezone de la API",
        MUTATION_BY_TEST["armado de startAt con offset exacto para la fecha elegida y timezone de la API"],
    ),
    (
        "frontend-appointment-form",
        "Renderizado de violaciones de dominio 409 y 422",
        "Conflicto múltiple 409 muestra todas las violaciones con sus referencias",
    ): (
        f"{T_FORM} > respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias",
        MUTATION_BY_TEST["respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias"],
    ),
    (
        "frontend-appointment-form",
        "Renderizado de violaciones de dominio 409 y 422",
        "Rechazo 422 muestra violaciones en el resumen",
    ): (
        f"{T_FORM} > rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos",
        MUTATION_BY_TEST["rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos"],
    ),
    (
        "frontend-appointment-form",
        "Errores de validación 400 y permisos 403",
        "Error 400 marca campo con aria-invalid",
    ): (
        f"{T_FORM} > mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline",
        MUTATION_BY_TEST["mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline"],
    ),
    (
        "frontend-appointment-form",
        "Errores de validación 400 y permisos 403",
        "Error 403 muestra mensaje de rechazo",
    ): (
        f"{T_FORM} > respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión",
        MUTATION_BY_TEST["respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión"],
    ),
    (
        "frontend-appointment-form",
        "Errores de validación 400 y permisos 403",
        "Foco se traslada al resumen de alerta ante fallo",
    ): (
        f"{T_FORM} > foco al resumen de alerta ante fallo",
        MUTATION_BY_TEST["foco al resumen de alerta ante fallo"],
    ),
    (
        "frontend-appointment-form",
        "Éxito, refresco de agenda y retorno de foco",
        "Alta exitosa 201 refresca agenda y anuncia resultado",
    ): (
        f"{T_PAGE} > tras alta exitosa (201) anuncia el turno creado en una región de estado accesible",
        MUTATION_BY_TEST["tras alta exitosa (201) anuncia el turno creado en una región de estado accesible"],
    ),
    (
        "frontend-appointment-form",
        "Éxito, refresco de agenda y retorno de foco",
        "Cancelación retorna el foco",
    ): (
        f"{T_FORM} > pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura",
        MUTATION_BY_TEST["pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura"],
    ),
    (
        "frontend-appointment-form",
        "Adaptabilidad visual del formulario",
        "Visualización en escritorio a 1440 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-29-1440.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
    (
        "frontend-appointment-form",
        "Adaptabilidad visual del formulario",
        "Visualización en tablet a 768 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-29-768.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
    (
        "frontend-appointment-form",
        "Adaptabilidad visual del formulario",
        "Visualización en móvil a 390 px",
    ): (
        "Captura a cargo de Claude (`docs/evidencias/capturas/C-29-390.png`)",
        "Sin mutación (verificación visual independiente a cargo de Claude)",
    ),
}


def load_spec_scenarios() -> list[tuple[str, str, str]]:
    scenarios: list[tuple[str, str, str]] = []
    spec_files = [
        SPECS_DIR / "frontend-agenda" / "spec.md",
        SPECS_DIR / "frontend-appointment-form" / "spec.md",
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
        "Salida generada por docs/evidencias/trazabilidad-C-29.py. No editar a mano.",
        f"tests listados por vitest en el repo: {len(nodes)}",
        f"escenarios totales en las specs delta de C-29: {number}",
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
            print("Faltan marcadores de trazabilidad en verify-C-29.md", file=sys.stderr)
            return 2
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
            encoding="utf-8",
            newline="\n",
        )

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
