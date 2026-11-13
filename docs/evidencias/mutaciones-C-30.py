"""Verificación por mutación, reproducible, de los tests de C-30 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-30.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación por cada test nuevo de C-30: antes de mutar se cuentan los tests con `vitest list --json`
y se exige una correspondencia uno a uno con los 33 tests nuevos.

Por cada mutación: comprueba que el original aparezca exactamente una vez y que el mutante cambie el archivo
(respetando LF o CRLF), aplica la mutación, corre Vitest solo para ese test (`vitest run <archivo> -t <nombre>$`),
restaura el archivo en un finally y vuelve a correr el test, que tiene que volver a verde.

Una mutación es INVÁLIDA si su test no la detecta con una afirmación propia:
- el archivo de test no carga (error de import, de compilación o SyntaxError);
- no se ejecutó exactamente ese test;
- el fallo es ReferenceError, SyntaxError, TypeError, TestingLibraryElementError u otro error que no sea
  AssertionError ni un `Error: expect(...)` de un matcher;
- el primer frame fuera de node_modules no está en un archivo *.test.ts(x).

Genera mutaciones-C-30.txt (salida cruda de Vitest incluida) y actualiza la tabla de verify-C-30.md.
Termina con código 0 solo si todas las mutaciones hicieron fallar su test, ninguna es INVÁLIDA y el SHA-256
del código de producción no cambió.
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
OUTPUT = EVIDENCE / "mutaciones-C-30.txt"
VERIFY = EVIDENCE / "verify-C-30.md"
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

# --- Archivos de test de C-30 ---
T_GRID = "src/features/agenda/AgendaGrid.accionable.test.tsx"
T_TABLE = "src/features/agenda/AgendaTable.accionable.test.tsx"
T_DETAIL = "src/features/appointments/AppointmentDetailDialog.test.tsx"
T_STATUS = "src/features/appointments/AppointmentStatusActions.test.tsx"
T_CANCEL = "src/features/appointments/AppointmentCancel.test.tsx"
T_RESCHEDULE = "src/features/appointments/AppointmentRescheduleDialog.test.tsx"
T_PAGE = "src/features/agenda/AgendaPage.acciones.test.tsx"

C30_TEST_FILES = (
    T_GRID,
    T_TABLE,
    T_DETAIL,
    T_STATUS,
    T_CANCEL,
    T_RESCHEDULE,
    T_PAGE,
)

# --- Archivos de producción modificados o creados en C-30 ---
P_GRID = "frontend/src/features/agenda/AgendaGrid.tsx"
P_TABLE = "frontend/src/features/agenda/AgendaTable.tsx"
P_VIEW = "frontend/src/features/agenda/AgendaView.tsx"
P_PAGE = "frontend/src/features/agenda/AgendaPage.tsx"
P_API = "frontend/src/features/appointments/appointmentApi.ts"
P_DETAIL = "frontend/src/features/appointments/AppointmentDetailDialog.tsx"
P_HISTORY = "frontend/src/features/appointments/AppointmentHistoryList.tsx"
P_RESCHEDULE = "frontend/src/features/appointments/AppointmentRescheduleDialog.tsx"

PRODUCTION_FILES = (
    P_GRID,
    P_TABLE,
    P_VIEW,
    P_PAGE,
    P_API,
    P_DETAIL,
    P_HISTORY,
    P_RESCHEDULE,
)


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
    # --- 1. AgendaGrid accionable (2 tests) ---
    Mutation(
        T_GRID,
        "cada turno en AgendaGrid es un button type=button accesible con aria-label completo",
        P_GRID,
        '                    <button\n                      type="button"\n                      key={appt.id}',
        '                    <button\n                      type="submit"\n                      key={appt.id}',
    ),
    Mutation(
        T_GRID,
        "al pulsar el turno invoca onSelectAppointment con los datos del turno",
        P_GRID,
        "                      onClick={() => onSelectAppointment?.(appt)}",
        "                      onClick={() => undefined}",
    ),

    # --- 2. AgendaTable accionable (2 tests) ---
    Mutation(
        T_TABLE,
        "con onSelectAppointment renderiza el botón Ver turno y al activarlo invoca el callback",
        P_TABLE,
        "                      onClick={() => onSelectAppointment(appt)}",
        "                      onClick={() => undefined}",
    ),
    Mutation(
        T_TABLE,
        "sin onSelectAppointment conserva exactamente las 6 columnas originales",
        P_TABLE,
        '            {onSelectAppointment && (\n              <th scope="col" className={styles.th}>\n                Acción\n              </th>\n            )}',
        '            {(!onSelectAppointment || true) && (\n              <th scope="col" className={styles.th}>\n                Acción\n              </th>\n            )}',
    ),

    # --- 3. AppointmentDetailDialog — Detalle e Historial (4 tests) ---
    Mutation(
        T_DETAIL,
        "3.1 detalle renderiza datos completos en hora local con StatusBadge y botón cerrar",
        P_DETAIL,
        '            <button\n              type="button"\n              disabled={isSubmitting}\n              onClick={onClose}\n              className={styles.secondaryButton}\n            >\n              Cerrar\n            </button>',
        '            <button\n              type="button"\n              disabled={isSubmitting}\n              onClick={() => undefined}\n              className={styles.secondaryButton}\n            >\n              Cerrar\n            </button>',
    ),
    Mutation(
        T_DETAIL,
        "3.2 historial renderiza transiciones cronológicas con autor, estados y hora local",
        P_HISTORY,
        '              <span className={styles.historyAuthor}>{author}</span>',
        '              <span className={styles.historyAuthor}>Anon</span>',
    ),
    Mutation(
        T_DETAIL,
        "3.3 historial renderiza desglose de reprogramación con horario previo y nuevo en hora local",
        P_HISTORY,
        '                  {formatTimeRange(\n                    entry.reschedule.previousStartAt,\n                    entry.reschedule.previousEndAt,\n                    timezone,\n                  )}',
        '                  {formatTimeRange(\n                    entry.reschedule.previousStartAt,\n                    entry.reschedule.previousStartAt,\n                    timezone,\n                  )}',
    ),
    Mutation(
        T_DETAIL,
        "3.4 historial maneja error de carga mostrando aviso accesible sin romper el detalle",
        P_HISTORY,
        '        setError("No se pudo cargar el historial de cambios.");',
        '        setError("Error inesperado al cargar historial.");',
    ),
    Mutation(
        T_DETAIL,
        "3.5 alert muestra código estable y mensaje textual en español",
        P_DETAIL,
        '                  <span className={styles.codeBadge}>{v.code}</span>\n                  {v.message}',
        '                  <span className={styles.codeBadge}></span>\n                  {"Error genérico"}',
    ),
    Mutation(
        T_DETAIL,
        "3.6 foco automático al alert de error",
        P_DETAIL,
        '          <div\n            ref={alertRef}\n            tabIndex={-1}',
        '          <div\n            tabIndex={-1}',
    ),

    # --- 4. AppointmentStatusActions — Cambios de estado (6 tests) ---
    Mutation(
        T_STATUS,
        "4.1 botones contextuales según estado y rol",
        P_DETAIL,
        '            {isTerminal ? (\n              <p className={styles.terminalNotice}>Este turno ya no admite cambios.</p>',
        '            {isTerminal ? (\n              <p className={styles.terminalNotice}>Modificaciones no admitidas.</p>',
    ),
    Mutation(
        T_STATUS,
        "4.2 confirmar turno envía toStatus confirmado y cierra modal con éxito",
        P_DETAIL,
        '                    onClick={() => handleStatusChange("confirmado")}',
        '                    onClick={() => handleStatusChange("atendido")}',
    ),
    Mutation(
        T_STATUS,
        "4.3 marcar atendido envía toStatus atendido y cierra modal con éxito",
        P_DETAIL,
        '                  onClick={() => handleStatusChange("atendido")}',
        '                  onClick={() => handleStatusChange("ausente")}',
    ),
    Mutation(
        T_STATUS,
        "4.4 marcar ausente envía toStatus ausente y cierra modal con éxito",
        P_DETAIL,
        '                  onClick={() => handleStatusChange("ausente")}',
        '                  onClick={() => handleStatusChange("atendido")}',
    ),
    Mutation(
        T_STATUS,
        "4.5 rechazo 422 STATUS_CHANGE_TOO_EARLY expone alerta con código, mensaje y foco",
        P_DETAIL,
        '                  <span className={styles.codeBadge}>{v.code}</span>',
        '                  <span className={styles.codeBadge}></span>',
    ),
    Mutation(
        T_STATUS,
        "4.6 rechazo 422 INVALID_TRANSITION expone mensaje en alerta con foco",
        P_DETAIL,
        '  useEffect(() => {\n    if (violations.length > 0) {\n      alertRef.current?.focus();\n    }\n  }, [violations]);',
        '  useEffect(() => {\n    if (violations.length > 0) {\n      // alertRef.current?.focus();\n    }\n  }, [violations]);',
    ),

    # --- 5. AppointmentCancel — Cancelación (4 tests) ---
    Mutation(
        T_CANCEL,
        "5.1 cancelar turno muestra subvista de confirmación in-dialog",
        P_DETAIL,
        '            <p className={styles.cancelConfirmWarning}>\n              ¿Confirma que desea cancelar el turno de {appointment.patientName}?\n            </p>',
        '            <p className={styles.cancelConfirmWarning}>\n              Confirmación para {appointment.patientName}?\n            </p>',
    ),
    Mutation(
        T_CANCEL,
        "5.2 volver al detalle o Escape restaura la vista sin enviar petición",
        P_DETAIL,
        '                onClick={() => setIsConfirmingCancel(false)}\n                className={styles.secondaryButton}\n              >\n                Volver al detalle',
        '                onClick={() => undefined}\n                className={styles.secondaryButton}\n              >\n                Volver al detalle',
    ),
    Mutation(
        T_CANCEL,
        "5.3 confirmar cancelación envía POST sin cuerpo y cierra modal",
        P_API,
        'export async function cancelAppointment(\n  client: ApiClient,\n  id: string,\n): Promise<ApiResult<AppointmentResponse>> {\n  const result = await client.request(`/appointments/${id}/cancel`, {\n    method: "POST",\n  });',
        'export async function cancelAppointment(\n  client: ApiClient,\n  id: string,\n): Promise<ApiResult<AppointmentResponse>> {\n  const result = await client.request(`/appointments/${id}/cancel`, {\n    method: "DELETE",\n  });',
    ),
    Mutation(
        T_CANCEL,
        "5.4 error 422 INVALID_TRANSITION en cancelación muestra alerta con foco",
        P_DETAIL,
        '    setIsConfirmingCancel(false);\n    if (\n      result.error.kind === "unprocessable" ||\n      result.error.kind === "conflict" ||\n      result.error.kind === "forbidden"\n    ) {\n      setViolations(result.error.violations);',
        '    setIsConfirmingCancel(false);\n    if (\n      result.error.kind === "unprocessable" ||\n      result.error.kind === "conflict" ||\n      result.error.kind === "forbidden"\n    ) {\n      // setViolations(result.error.violations);',
    ),
    Mutation(
        T_CANCEL,
        "5.5 Escape sobre el diálogo con confirmación abierta vuelve a la vista de detalle",
        P_DETAIL,
        '  const handleDialogClose = () => {\n    if (isConfirmingCancel) {\n      setIsConfirmingCancel(false);\n    } else {\n      onClose();\n    }\n  };',
        '  const handleDialogClose = () => {\n    onClose();\n  };',
    ),

    # --- 6. AppointmentRescheduleDialog — Reprogramación (6 tests) ---
    Mutation(
        T_RESCHEDULE,
        "6.1 apertura con paciente y prestación en solo lectura y campos prellenados",
        P_RESCHEDULE,
        '  const [date, setDate] = useState(() =>\n    appointment ? formatLocalDate(appointment.startAt, timezone) : "",\n  );',
        '  const [date, setDate] = useState(() =>\n    appointment ? "2000-01-01" : "",\n  );',
    ),
    Mutation(
        T_RESCHEDULE,
        "6.2 reprogramación exitosa envía POST con offset exacto y cierra modal",
        P_RESCHEDULE,
        "      durationMin: Number(durationMin),",
        "      durationMin: 999,",
    ),
    Mutation(
        T_RESCHEDULE,
        "6.3 rechazo 409 con violaciones múltiples de solapamiento muestra badges y alert con foco",
        P_RESCHEDULE,
        '                  <span className={styles.codeBadge}>{v.code}</span>',
        '                  <span className={styles.codeBadge}></span>',
    ),
    Mutation(
        T_RESCHEDULE,
        "6.4 rechazo 422 IN_THE_PAST expone mensaje del dominio en alert con foco",
        P_RESCHEDULE,
        '                  <span className={styles.codeBadge}>{v.code}</span>\n                  {v.message}',
        '                  <span className={styles.codeBadge}>{v.code}</span>\n                  {"Mensaje genérico"}',
    ),
    Mutation(
        T_RESCHEDULE,
        "6.5 error 400 marca campos con aria-invalid y mensaje inline",
        P_RESCHEDULE,
        '              aria-invalid={fieldErrors.durationMin ? "true" : undefined}',
        '              aria-invalid={undefined}',
    ),
    Mutation(
        T_RESCHEDULE,
        "6.6 cancelar reprogramación cierra diálogo y retorna foco",
        P_RESCHEDULE,
        '            <button\n              type="button"\n              disabled={isSubmitting}\n              onClick={onClose}\n              className={styles.secondaryButton}\n            >\n              Cancelar\n            </button>',
        '            <button\n              type="button"\n              disabled={isSubmitting}\n              onClick={() => undefined}\n              className={styles.secondaryButton}\n            >\n              Cancelar\n            </button>',
    ),

    # --- 7. AgendaPage — Integración de Acciones (11 tests) ---
    Mutation(
        T_PAGE,
        "7.1 restringir acciones de odontólogo en turnos propios a cambios de estado e historial",
        P_PAGE,
        '          currentUser={user}\n          returnFocusRef={detailReturnFocusRef}\n          onStatusChanged={handleStatusChanged}',
        '          currentUser={null}\n          returnFocusRef={detailReturnFocusRef}\n          onStatusChanged={handleStatusChanged}',
    ),
    Mutation(
        T_PAGE,
        "7.2 bloquear acciones e historial para odontólogo en turnos ajenos",
        P_DETAIL,
        "  const isDentistOther = isDentist && !isOwnAppointment;",
        "  const isDentistOther = false;",
    ),
    Mutation(
        T_PAGE,
        "7.3 respuesta 403 FORBIDDEN_OPERATION muestra alerta sin cerrar sesión",
        P_DETAIL,
        '    if (\n      result.error.kind === "unprocessable" ||\n      result.error.kind === "conflict" ||\n      result.error.kind === "forbidden"\n    ) {\n      setViolations(result.error.violations);\n    } else {\n      setViolations([\n        {\n          code: "REQUEST_FAILED",\n          message: "No se pudo realizar el cambio de estado.",',
        '    if (\n      result.error.kind === "unprocessable" ||\n      result.error.kind === "conflict"\n    ) {\n      setViolations(result.error.violations);\n    } else {\n      setViolations([\n        {\n          code: "REQUEST_FAILED",\n          message: "No se pudo realizar el cambio de estado.",',
    ),
    Mutation(
        T_PAGE,
        "7.4 seleccionar turno abre modal y mutación exitosa refresca la agenda",
        P_PAGE,
        '    void state.refresh();\n  };\n\n  const handleCancelled = () => {',
        '    // void state.refresh();\n  };\n\n  const handleCancelled = () => {',
    ),
    Mutation(
        T_PAGE,
        "7.5 confirmación emite anuncio Turno confirmado.",
        P_PAGE,
        '      setStatusMessage("Turno confirmado.");',
        '      setStatusMessage("Confirmado.");',
    ),
    Mutation(
        T_PAGE,
        "7.6 marcar atendido emite anuncio Turno marcado como atendido.",
        P_PAGE,
        '      setStatusMessage("Turno marcado como atendido.");',
        '      setStatusMessage("Atendido.");',
    ),
    Mutation(
        T_PAGE,
        "7.7 marcar ausente emite anuncio Turno marcado como ausente.",
        P_PAGE,
        '      setStatusMessage("Turno marcado como ausente.");',
        '      setStatusMessage("Ausente.");',
    ),
    Mutation(
        T_PAGE,
        "7.8 cancelar emite anuncio Turno cancelado.",
        P_PAGE,
        '  const handleCancelled = () => {\n    setStatusMessage("Turno cancelado.");',
        '  const handleCancelled = () => {\n    setStatusMessage("Cancelado.");',
    ),
    Mutation(
        T_PAGE,
        "7.9 reprogramar emite anuncio Turno reprogramado para el DD/MM/AAAA a las HH:MM.",
        P_PAGE,
        '    setStatusMessage(`Turno reprogramado para el ${day}/${month}/${year} a las ${time}.`);',
        '    setStatusMessage("Turno reprogramado.");',
    ),
    Mutation(
        T_PAGE,
        "7.10 al cerrar el detalle con el botón Cerrar el foco vuelve al botón del turno",
        P_PAGE,
        '          returnFocusRef={detailReturnFocusRef}\n          onStatusChanged={handleStatusChanged}',
        '          returnFocusRef={{ current: null }}\n          onStatusChanged={handleStatusChanged}',
    ),
    Mutation(
        T_PAGE,
        "7.11 al cerrar el detalle con Escape sobre el diálogo el foco vuelve al botón del turno",
        P_PAGE,
        '            triggerAppointmentBtnRef.current =\n              document.activeElement instanceof HTMLElement ? document.activeElement : null;',
        '            triggerAppointmentBtnRef.current = null;',
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


def production_sha256() -> str:
    hasher = hashlib.sha256()
    for relative in sorted(PRODUCTION_FILES):
        path = REPO / relative
        hasher.update(path.as_posix().encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def vitest_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env


def apply_mutation(mutation: Mutation, content: str) -> str:
    original = mutation.original
    mutated = mutation.mutated
    if "\r\n" in content and "\r\n" not in original:
        original = original.replace("\n", "\r\n")
        mutated = mutated.replace("\n", "\r\n")
    elif "\r\n" not in content and "\r\n" in original:
        original = original.replace("\r\n", "\n")
        mutated = mutated.replace("\r\n", "\n")
    return content.replace(original, mutated, 1)


def check_definition(mutation: Mutation) -> None:
    path = REPO / mutation.file
    if not path.is_file():
        raise MutationAbort(f"{mutation.node_id}: no existe {mutation.file}")
    content = path.read_text(encoding="utf-8")
    norm_content = content.replace("\r\n", "\n")
    norm_original = mutation.original.replace("\r\n", "\n")
    count = norm_content.count(norm_original)
    if count == 0:
        raise MutationAbort(f"{mutation.node_id}: original no encontrado en {mutation.file}")
    if count > 1:
        raise MutationAbort(f"{mutation.node_id}: original aparece {count} veces en {mutation.file}")


def listed_tests() -> list[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", "--json"],
        cwd=FRONTEND,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=vitest_env(),
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    start = result.stdout.find("[")
    entries = json.loads(result.stdout[start:])
    tests: list[tuple[str, str]] = []
    for entry in entries:
        file = Path(entry["file"]).resolve().relative_to(FRONTEND.resolve()).as_posix()
        name = entry["name"].split(" > ")[-1]
        if file in C30_TEST_FILES:
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
            f"tests nuevos de C-30 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
            f"sin mutacion: {missing}\nmutacion sin test: {unknown}\nrepetidas: {repeated}"
        )
    return len(tests)


def run_vitest(args: list[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        result = subprocess.run(
            [*VITEST, "run", *args, "--poolOptions.threads.maxThreads=3", "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
            cwd=FRONTEND,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=vitest_env(),
            timeout=TIMEOUT_SECONDS,
            check=False,
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


def run_mutation(
    mutation: Mutation,
    index: int,
    report: Report,
) -> tuple[bool, str | None, str, str]:
    target = REPO / mutation.file
    original_bytes = target.read_bytes()
    original_content = original_bytes.decode("utf-8")
    mutated_content = apply_mutation(mutation, original_content)
    if mutated_content == original_content:
        raise MutationAbort(f"{mutation.node_id}: el mutante no cambio el archivo {mutation.file}")

    diff_lines = list(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            mutated_content.splitlines(keepends=True),
            fromfile=f"a/{mutation.file}",
            tofile=f"b/{mutation.file}",
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
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
            encoding="utf-8",
            newline="\n",
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
            f"una por cada uno de los {total_tests} tests de C-30."
        )
        return 0

    sha_before = production_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    rows: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-30.py. No editar a mano.")
        report.write(
            f"tests nuevos de C-30 listados por vitest: {total_tests}; "
            f"mutaciones: {len(MUTATIONS)} (una por test)"
        )
        report.write(f"SHA-256 de produccion antes: {sha_before}")
        baseline, _ = run_vitest(list(C30_TEST_FILES))
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
