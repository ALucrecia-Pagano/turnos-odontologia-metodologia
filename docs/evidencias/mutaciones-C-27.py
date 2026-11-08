"""Verificacion por mutacion, reproducible, de los tests de C-27 (frontend, Vitest).

Uso, desde la raiz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-27.py [--check]

Misma logica que mutaciones-C-26.py. Cada mutacion es
(archivo de test, nombre del test, archivo de produccion, texto_original, texto_mutado).
Hay UNA mutacion por cada test nuevo/actualizado de C-27: antes de mutar se cuentan los tests
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

Genera mutaciones-C-27.txt (salida cruda de Vitest incluida) y regenera la tabla de
verify-C-27.md. Termina con codigo 0 solo si todas las mutaciones hicieron fallar su
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
OUTPUT = EVIDENCE / "mutaciones-C-27.txt"
VERIFY = EVIDENCE / "verify-C-27.md"
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

# --- archivos de test de C-27 ------------------------------------------------
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

C27_TEST_FILES = (
    T_AGENDA_TIME,
    T_CLOCK,
    T_AGENDA_CONFIG,
    T_TIME_GUARD,
    T_AGENDA_LAYOUT,
    T_AGENDA_API,
    T_USE_AGENDA,
    T_APP,
    T_MENU_FOR,
    T_APP_SHELL,
    T_AGENDA_VIEW,
    T_AGENDA_TOOLBAR,
    T_AGENDA_PAGE,
    T_AGENDA_TABLE,
    T_AGENDA_STYLES,
)

# Tests de src/App.test.tsx y src/shared/components/AppShell.test.tsx creados y mutados en C-25/C-26.
PRIOR_EXISTING_TESTS = {
    (T_APP, "una ruta desconocida muestra la página de no encontrada"),
    (T_APP, "ruta protegida sin sesión conserva el destino"),
    (T_APP, "login con sesión vuelve al destino válido"),
    (T_APP, "sin parpadeo de login a home"),
    (T_APP, "token vencido en una request protegida"),
    (T_APP_SHELL, "muestra en un alerta del shell la violación de un 403 sin cerrar la sesión"),
}

# --- archivos de produccion (siempre dentro de frontend/src) -----------------
P_AGENDA_TIME = "frontend/src/features/agenda/agendaTime.ts"
P_CLOCK = "frontend/src/features/agenda/clock.ts"
P_AGENDA_CONFIG = "frontend/src/features/agenda/agendaConfig.ts"
P_AGENDA_LAYOUT = "frontend/src/features/agenda/agendaLayout.ts"
P_AGENDA_API = "frontend/src/features/agenda/agendaApi.ts"
P_USE_AGENDA = "frontend/src/features/agenda/useAgenda.ts"
P_APP = "frontend/src/App.tsx"
P_MENU_FOR = "frontend/src/features/auth/menuFor.ts"
P_APP_SHELL = "frontend/src/shared/components/AppShell.tsx"
P_AGENDA_VIEW = "frontend/src/features/agenda/AgendaView.tsx"
P_AGENDA_GRID = "frontend/src/features/agenda/AgendaGrid.tsx"
P_AGENDA_GRID_CSS = "frontend/src/features/agenda/AgendaGrid.module.css"
P_AGENDA_TOOLBAR = "frontend/src/features/agenda/AgendaToolbar.tsx"
P_AGENDA_PAGE = "frontend/src/features/agenda/AgendaPage.tsx"
P_AGENDA_TABLE = "frontend/src/features/agenda/AgendaTable.tsx"


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
    # --- 1. Conversion a hora local, reloj y guardian (R3, C1) ---
    Mutation(
        T_AGENDA_TIME,
        "13:00Z se convierte a 10:00 y 2026-11-16 en Buenos Aires y formatea la etiqueta del día",
        P_AGENDA_TIME,
        "  return `${start}–${end}`;",
        "  return `${start}-${end}`;",
    ),
    Mutation(
        T_AGENDA_TIME,
        "respeta el borde de medianoche entre 02:30Z y 03:30Z en Buenos Aires",
        P_AGENDA_TIME,
        "export function todayInTimeZone(now: Date, timeZone: string): string {\n  return formatLocalDate(now, timeZone);\n}",
        'export function todayInTimeZone(now: Date, timeZone: string): string {\n  void timeZone;\n  return formatLocalDate(now, "UTC");\n}',
    ),
    Mutation(
        T_AGENDA_TIME,
        "addDays suma y resta días calendario cruzando mes y año y weekdayOf devuelve ISO con domingo 7",
        P_AGENDA_TIME,
        "  return day === 0 ? 7 : day;",
        "  return day === 0 ? 0 : day;",
    ),
    Mutation(
        T_AGENDA_TIME,
        "parseHHMM convierte 24:00 a 1440 y appointmentRange maneja el cruce de medianoche",
        P_AGENDA_TIME,
        '  if (hhmm === "24:00") {\n    return 1440;\n  }',
        '  if (hhmm === "24:00") {\n    return 0;\n  }',
    ),
    Mutation(
        T_AGENDA_TIME,
        "una zona con DST como America/New_York no altera la hora de Buenos Aires y el resultado no depende del proceso",
        P_AGENDA_TIME,
        "export function isValidLocalDate(value: string | null | undefined): value is string {\n  return parseLocalDate(value) !== null;\n}",
        "export function isValidLocalDate(value: string | null | undefined): value is string {\n  return parseLocalDate(value) === null;\n}",
    ),
    Mutation(
        T_CLOCK,
        "systemClock devuelve el instante actual y createFixedClock inyecta un reloj determinista con new Date() solo en clock.ts",
        P_CLOCK,
        "      return new Date(fixedTime);",
        "      return new Date(fixedTime + 1000);",
    ),
    Mutation(
        T_AGENDA_CONFIG,
        "DEFAULT_AGENDA_TIMEZONE vive en un único archivo de configuración y resolveAgendaTimezone prioriza el timezone de la respuesta",
        P_AGENDA_CONFIG,
        'export const DEFAULT_AGENDA_TIMEZONE = "America/Argentina/Buenos_Aires";',
        'export const DEFAULT_AGENDA_TIMEZONE = "UTC";',
    ),
    Mutation(
        T_TIME_GUARD,
        "prohíbe getters locales de Date y toLocale* sin timeZone y confina new Date() a clock.ts",
        P_AGENDA_TIME,
        "function toDate(instant: Date | string): Date {",
        "function toDate(instant: Date | string): Date { /* getHours */",
    ),
    # --- 2, 3, 4. Eje, columnas por profesional y carriles (R4, R5, R6) ---
    Mutation(
        T_AGENDA_LAYOUT,
        "calcula el eje 08:00 a 20:00 para el lunes 2026-11-16 con horarios 09:00–13:00 y 15:00–19:00, bloqueo y turnos",
        P_AGENDA_LAYOUT,
        "  let startMinute = Math.max(0, Math.floor(minStart / 60) * 60 - 60);",
        "  let startMinute = Math.max(0, Math.floor(minStart / 60) * 60);",
    ),
    Mutation(
        T_AGENDA_LAYOUT,
        "usa 08:00–20:00 en día vacío, expande rangos menores a 4 horas y clampea bloqueos y turnos en medianoche a [0, 1440]",
        P_AGENDA_LAYOUT,
        "export const AGENDA_DEFAULT_START_MINUTE = 480;",
        "export const AGENDA_DEFAULT_START_MINUTE = 540;",
    ),
    Mutation(
        T_AGENDA_LAYOUT,
        "ordena las columnas de forma alfabética estable con desempate por id, conserva columnas vacías y une defensivamente la agenda",
        P_AGENDA_LAYOUT,
        "  return a.id.localeCompare(b.id);",
        "  return b.id.localeCompare(a.id);",
    ),
    Mutation(
        T_AGENDA_LAYOUT,
        "marca profesionales inactivos con (inactivo) y el filtro professionalId deja una sola columna",
        P_AGENDA_LAYOUT,
        "  return professional.active ? professional.fullName : `${professional.fullName} (inactivo)`;",
        "  return professional.active ? professional.fullName : professional.fullName;",
    ),
    Mutation(
        T_AGENDA_LAYOUT,
        "asigna carriles a turnos sin solape, a un cancelado y un activo superpuestos y a tres turnos en cadena",
        P_AGENDA_LAYOUT,
        "    const laneCount = Math.max(1, laneEnds.length);",
        "    const laneCount = Math.max(2, laneEnds.length);",
    ),
    Mutation(
        T_AGENDA_LAYOUT,
        "aplica alto mínimo a un turno de 5 minutos, clampea el inicio al eje y soporta un turno que termina a las 00:00",
        P_AGENDA_LAYOUT,
        "export const AGENDA_MIN_APPOINTMENT_MINUTES = 15;",
        "export const AGENDA_MIN_APPOINTMENT_MINUTES = 5;",
    ),
    # --- 5. Cliente de agenda y hook useAgenda (R2) ---
    Mutation(
        T_AGENDA_API,
        "fetchAgenda pide GET /api/agenda con from y to locales sin sufijo Z, filtros opcionales y signal, y parsea el 200 completo",
        P_AGENDA_API,
        '  search.set("from", params.from);',
        '  search.set("from", `${params.from}Z`);',
    ),
    Mutation(
        T_AGENDA_API,
        "fetchAgenda propaga errores 400, 401, 403, 500, red y rechaza una respuesta 200 con JSON o forma inválida",
        P_AGENDA_API,
        '  const parsed = parseAgendaResponse(result.data);\n  if (parsed === null) {\n    return {\n      ok: false,\n      status: result.status,\n      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSAGE },\n    };\n  }',
        '  const parsed = parseAgendaResponse(result.data);\n  if (parsed === null) {\n    return {\n      ok: false,\n      status: result.status,\n      error: { kind: "unknown", status: result.status, rawText: "Otro error" },\n    };\n  }',
    ),
    Mutation(
        T_AGENDA_API,
        "fetchProfessionals y fetchChairs cargan los catálogos con activos e inactivos y validan la respuesta",
        P_AGENDA_API,
        '  const result = await client.request("/chairs", {',
        '  const result = await client.request("/sillones", {',
    ),
    Mutation(
        T_USE_AGENDA,
        "dispara las tres requests en paralelo, pasa por loading/refreshing/success y tolera fallo del catálogo con Promise.allSettled",
        P_USE_AGENDA,
        'export const CATALOG_FALLBACK_WARNING =\n  "No se pudo cargar el catálogo completo; las columnas se armaron con los datos de la agenda.";',
        'export const CATALOG_FALLBACK_WARNING =\n  "Aviso de catálogo distinto.";',
    ),
    Mutation(
        T_USE_AGENDA,
        "aborta e ignora respuestas viejas al cambiar de fecha y expone error cuando falla la agenda",
        P_USE_AGENDA,
        "    return () => {\n      controller.abort();\n    };",
        "    return () => {\n      void controller;\n    };",
    ),
    # --- 6. Ruta /agenda, redireccion de / y menu (R1) ---
    Mutation(
        T_APP,
        "la ruta raíz redirige con replace a /agenda según el Clock y no renderiza HomePage",
        P_APP,
        "  return <Navigate to={`/agenda?date=${today}`} replace />;",
        "  return <Navigate to={`/agenda?date=${today}`} replace={false} />;",
    ),
    Mutation(
        T_MENU_FOR,
        "menú del administrador incluye Agenda habilitada y los otros 5 ítems deshabilitados con Próximamente",
        P_MENU_FOR,
        '    const enabled = item.id === "agenda";',
        "    const enabled = false;",
    ),
    Mutation(
        T_MENU_FOR,
        "menú de recepción habilita Agenda y no incluye Usuarios y roles",
        P_MENU_FOR,
        '      badge: enabled ? null : ("Próximamente" as const),',
        '      badge: "Próximamente" as const,',
    ),
    Mutation(
        T_MENU_FOR,
        "menú del odontólogo habilita Agenda y no incluye Turnos ni Usuarios y roles",
        P_MENU_FOR,
        "      disabled: !enabled,",
        "      disabled: true,",
    ),
    Mutation(
        T_APP_SHELL,
        "renderiza Agenda como enlace habilitado en los tres roles y el resto deshabilitado con Próximamente",
        P_APP_SHELL,
        "                  to={item.path}",
        '                  to="/otra-ruta"',
    ),
    # --- 7, 8, 9, 12, 14. AgendaView y AgendaGrid (R4–R8, R11, R13) ---
    Mutation(
        T_AGENDA_VIEW,
        "dibuja el eje 08:00–20:00 y las tres columnas en orden alfabético estable con inactivo y columna vacía",
        P_AGENDA_GRID,
        '                  <div className={styles.emptyColumnNote}>Sin turnos</div>',
        '                  <div className={styles.emptyColumnNote}>Columna vacía</div>',
    ),
    Mutation(
        T_AGENDA_VIEW,
        "posiciona el turno de Quiroga 10:00–10:30 a 120 minutos del inicio con 30 minutos de alto y muestra la fecha local",
        P_AGENDA_GRID,
        "                      data-offset-minutes={item.offsetMinutes}",
        "                      data-offset-minutes={0}",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "reparte un turno cancelado y uno activo superpuestos en dos carriles y da alto mínimo al turno de cinco minutos",
        P_AGENDA_GRID,
        "                      data-lane-count={item.laneCount}",
        "                      data-lane-count={1}",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado",
        P_AGENDA_GRID,
        "                      ? `Bloqueo: ${block.reason}, de ${startLabel} a ${endLabel}`",
        "                      ? `Bloqueo sin horario: ${block.reason}`",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta",
        P_AGENDA_GRID,
        "                  const cardAriaLabel = `${timeLabel}, ${appt.patientName}, ${appt.serviceName}, ${appt.professionalName}, ${appt.chairName}, ${statusLabel}`;",
        "                  const cardAriaLabel = `${timeLabel}, ${appt.patientName}`;",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "en un día sin turnos muestra SOLO el EmptyState sin grilla en modo grilla ni tabla en modo lista",
        P_AGENDA_VIEW,
        '          title="No hay turnos para este día"',
        '          title="Agenda sin registros"',
    ),
    Mutation(
        T_AGENDA_VIEW,
        "la tarjeta de 30 minutos muestra el nombre del paciente en su texto visible y el aria-label completo",
        P_AGENDA_GRID,
        "                  const isCompact = item.durationMinutes < 45;",
        "                  const isCompact = item.durationMinutes < 0;",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "la tarjeta de 60 minutos muestra la prestación en su texto visible en una línea separada",
        P_AGENDA_GRID,
        "                          <div className={styles.cardMeta}>{appt.serviceName}</div>",
        '                          <div className={styles.cardMeta}>{"Sin prestación"}</div>',
    ),
    # --- Revisión visual 2: el estado nunca tapa al paciente ---
    Mutation(
        T_AGENDA_VIEW,
        "en un solapamiento de dos carriles la tarjeta muestra en dos líneas el paciente y el nombre del estado como texto visible",
        P_AGENDA_GRID,
        "                  const isSplitLane = item.laneCount > 1;",
        "                  const isSplitLane = item.laneCount > 2;",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "un turno de un solo carril conserva el formato de una línea con la etiqueta de estado",
        P_AGENDA_GRID,
        "                  const isSplitLane = item.laneCount > 1;",
        "                  const isSplitLane = item.laneCount > 0;",
    ),
    Mutation(
        T_AGENDA_VIEW,
        "anuncia la cantidad de turnos con aria-live y alterna a la vista en lista con Ver como lista",
        P_AGENDA_VIEW,
        "            {`Turnos del ${dayLabel}: ${agenda.appointments.length}`}",
        "            {`Turnos del ${dayLabel}: 0`}",
    ),
    # --- 10, 11, 12, 13. AgendaToolbar y AgendaPage (R9, R10, R11, R12) ---
    Mutation(
        T_AGENDA_TOOLBAR,
        "renderiza selectores de Profesional y Sillón con opción Todos, marca (inactivo), ayuda de sillón y Limpiar filtros",
        P_AGENDA_TOOLBAR,
        "                  {chair.active ? chair.name : `${chair.name} (inactivo)`}",
        "                  {chair.name}",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible",
        P_AGENDA_TOOLBAR,
        'export const CHAIR_FILTER_HELP_TEXT =\n  "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.";',
        'export const CHAIR_FILTER_HELP_TEXT =\n  "Texto de ayuda alterado.";',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha",
        P_AGENDA_PAGE,
        "  const handleClearFilters = () => {\n    setSearchParams(buildParams({ professionalId: null, chairId: null }), { replace: false });\n  };",
        "  const handleClearFilters = () => {\n    setSearchParams(buildParams({}), { replace: false });\n  };",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL",
        P_AGENDA_PAGE,
        "        onPrevDay={() => navigateToDate(addDays(effectiveDate, -1))}",
        "        onPrevDay={() => navigateToDate(addDays(effectiveDate, 1))}",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "respeta el borde de medianoche en la fecha inicial y normaliza una fecha inválida con replace mostrando aviso",
        P_AGENDA_PAGE,
        'export const INVALID_DATE_NOTICE = "La fecha del enlace no era válida; se muestra hoy.";',
        'export const INVALID_DATE_NOTICE = "Fecha no válida.";',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "muestra Cargando... con role=status en la carga inicial sin mostrar error",
        P_AGENDA_PAGE,
        '      {state.phase === "loading" && state.agenda === null && <LoadingState />}',
        '      {state.phase === "loading" && state.agenda !== null && <LoadingState />}',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "muestra ErrorState con Reintentar ante error de red, al reintentar con 200 renderiza la agenda y Actualizar agenda refresca manualmente",
        P_AGENDA_PAGE,
        "        onRefresh={state.refresh}",
        "        onRefresh={undefined}",
    ),
    Mutation(
        T_AGENDA_PAGE,
        "delega el 401 de GET /api/agenda en C-26 descartando el token y redirigiendo a /login sin mostrar error local",
        P_AGENDA_API,
        '  const result = await client.request(`/agenda?${search.toString()}`, {\n    method: "GET",\n    signal: params.signal,\n  });',
        '  const result = await client.request(`/agenda?${search.toString()}`, {\n    method: "GET",\n    auth: "omit",\n    signal: params.signal,\n  });',
    ),
    Mutation(
        T_AGENDA_PAGE,
        "muestra la violación de un 403 en el error local sin cerrar sesión ni duplicar el banner global",
        P_AGENDA_PAGE,
        "    onForbidden: clearActionErrors,",
        "    onForbidden: undefined,",
    ),
    # --- 14, 15. AgendaTable y agendaStyles (R13, R14) ---
    Mutation(
        T_AGENDA_TABLE,
        "renderiza la tabla semántica con caption, encabezados con scope=col y filas en el mismo orden de la agenda",
        P_AGENDA_TABLE,
        "        <caption className={styles.caption}>{`Turnos del ${dayLabel}`}</caption>",
        "        <caption className={styles.caption}>{dayLabel}</caption>",
    ),
    Mutation(
        T_AGENDA_STYLES,
        "define los tokens de agenda en tokens.css, scroll horizontal, sticky, controles >= 44x44 px y cero HEX en TSX",
        P_AGENDA_GRID_CSS,
        "  overflow-x: auto;",
        "  overflow-x: hidden;",
    ),
    Mutation(
        T_AGENDA_STYLES,
        "la columna es un contenedor y por debajo de 260 px la tarjeta compacta pasa a dos líneas con la etiqueta reducida",
        P_AGENDA_GRID_CSS,
        "  .cardCompactRow {\n    flex-direction: column;",
        "  .cardCompactRow {\n    flex-direction: row;",
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text: str) -> None:
        # rstrip por linea: los code frames de Vitest traen espacios finales que git diff --check rechaza.
        self.stream.write("\n".join(line.rstrip() for line in text.rstrip().splitlines()) + "\n")
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
        if file in C27_TEST_FILES and (file, name) not in PRIOR_EXISTING_TESTS:
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
            f"tests nuevos de C-27 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
            f"una por cada uno de los {total_tests} tests de C-27."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-27.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-27 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C27_TEST_FILES))
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
