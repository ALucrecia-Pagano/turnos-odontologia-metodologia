"""Verificación por mutación, reproducible, de los tests de C-33 (frontend, Vitest).

Uso, desde la raíz del repo o desde frontend/:

    python docs/evidencias/mutaciones-C-33.py [--check]

Cada mutación es (archivo de test, nombre del test, archivo de producción, texto_original, texto_mutado).
Hay UNA mutación (M01-M30) por cada uno de los 30 escenarios testeables de C-33
(28 en tests nuevos + 2 en tests existentes modificados de AppShellNavigation.test.tsx).
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
OUTPUT = EVIDENCE / "mutaciones-C-33.txt"
VERIFY = EVIDENCE / "verify-C-33.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 300
VITEST = ["node", str((FRONTEND / "node_modules" / "vitest" / "vitest.mjs").resolve())]

INVALID_ERROR = re.compile(
    r"^(ReferenceError|SyntaxError|TypeError|RangeError|TestingLibraryElementError"
    r"|Error: (Failed to load|Failed to resolve|Cannot find module|Transform failed))"
)
ASSERTION = re.compile(r"^(AssertionError\b|Error: expect\()")
STACK_FRAME = re.compile(r"^\s*at (?:.*\()?(?:file:///)?(?P<path>[A-Za-z]:[\\/][^:()]+|/[^:()]+):\d+:\d+\)?$")
TEST_FILE = re.compile(r"\.test\.tsx?$")

# --- Archivos de test de C-33 ---
T_PACIENTES_PAGE = "src/features/pacientes/PacientesPage.test.tsx"
T_PACIENTES_FORM = "src/features/pacientes/PatientFormDialog.test.tsx"
T_CATALOGOS_STYLES = "src/features/catalogos/catalogosPacientesStyles.test.ts"
T_CATALOGOS_PAGE = "src/features/catalogos/CatalogosPage.test.tsx"
T_ROUTES = "src/features/catalogos/CatalogosPacientesRoutes.test.tsx"
T_CATALOGOS_FORM = "src/features/catalogos/CatalogFormDialog.test.tsx"
T_CATALOGOS_MOBILE = "src/features/catalogos/CatalogFormDialog.mobile.test.tsx"
T_CONFIRM = "src/features/catalogos/CatalogConfirmDialog.test.tsx"
T_SHELL_NEW = "src/shared/components/AppShellCatalogosPacientes.test.tsx"
T_SHELL_NAV = "src/shared/components/AppShellNavigation.test.tsx"

C33_TEST_FILES = (
    T_PACIENTES_PAGE,
    T_PACIENTES_FORM,
    T_CATALOGOS_STYLES,
    T_CATALOGOS_PAGE,
    T_ROUTES,
    T_CATALOGOS_FORM,
    T_CATALOGOS_MOBILE,
    T_CONFIRM,
    T_SHELL_NEW,
    T_SHELL_NAV,
)

PREEXISTING_TESTS: frozenset[tuple[str, str]] = frozenset(
    {
        (
            T_SHELL_NAV,
            "los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces",
        )
    }
)

# --- Archivos de producción modificados o creados en C-33 ---
P_PACIENTES_PAGE_TSX = "frontend/src/features/pacientes/PacientesPage.tsx"
P_PACIENTES_PAGE_CSS = "frontend/src/features/pacientes/PacientesPage.module.css"
P_PATIENT_FORM_TSX = "frontend/src/features/pacientes/PatientFormDialog.tsx"
P_PATIENT_FORM_CSS = "frontend/src/features/pacientes/PatientFormDialog.module.css"
P_PACIENTES_API_TS = "frontend/src/features/pacientes/pacientesApi.ts"
P_CATALOGOS_PAGE_TSX = "frontend/src/features/catalogos/CatalogosPage.tsx"
P_CATALOGOS_PAGE_CSS = "frontend/src/features/catalogos/CatalogosPage.module.css"
P_CATALOG_FORM_TSX = "frontend/src/features/catalogos/CatalogFormDialog.tsx"
P_CATALOG_FORM_CSS = "frontend/src/features/catalogos/CatalogFormDialog.module.css"
P_CONFIRM_TSX = "frontend/src/features/catalogos/CatalogConfirmDialog.tsx"
P_CONFIRM_CSS = "frontend/src/features/catalogos/CatalogConfirmDialog.module.css"
P_CONFIGS_TS = "frontend/src/features/catalogos/catalogConfigs.ts"
P_CATALOGOS_API_TS = "frontend/src/features/catalogos/catalogosApi.ts"
P_ACTIVE_BADGE_TSX = "frontend/src/features/catalogos/ActiveBadge.tsx"
P_ACTIVE_BADGE_CSS = "frontend/src/features/catalogos/ActiveBadge.module.css"
P_MENU_TS = "frontend/src/features/auth/menuFor.ts"
P_APP_TSX = "frontend/src/App.tsx"

PRODUCTION_FILES = (
    P_PACIENTES_PAGE_TSX,
    P_PACIENTES_PAGE_CSS,
    P_PATIENT_FORM_TSX,
    P_PATIENT_FORM_CSS,
    P_PACIENTES_API_TS,
    P_CATALOGOS_PAGE_TSX,
    P_CATALOGOS_PAGE_CSS,
    P_CATALOG_FORM_TSX,
    P_CATALOG_FORM_CSS,
    P_CONFIRM_TSX,
    P_CONFIRM_CSS,
    P_CONFIGS_TS,
    P_CATALOGOS_API_TS,
    P_ACTIVE_BADGE_TSX,
    P_ACTIVE_BADGE_CSS,
    P_MENU_TS,
    P_APP_TSX,
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
    # M01 - Listado de pacientes con sus cuatro datos
    Mutation(
        T_PACIENTES_PAGE,
        "Listado de pacientes con sus cuatro datos",
        P_PACIENTES_PAGE_TSX,
        "                  <th scope=\"col\" className={styles.th}>\n                    Obra social\n                  </th>",
        "                  {/* M01 */ false && <th scope=\"col\" className={styles.th}>\n                    Obra social\n                  </th>}",
    ),
    # M02 - Búsqueda envía la consulta codificada y muestra el resultado
    Mutation(
        T_PACIENTES_PAGE,
        "Búsqueda envía la consulta codificada y muestra el resultado",
        P_PACIENTES_API_TS,
        "? `/patients?query=${encodeURIComponent(trimmed)}` : \"/patients\";",
        "? `/patients?query=${trimmed}` : \"/patients\";",
    ),
    # M03 - Búsqueda sin resultados
    Mutation(
        T_PACIENTES_PAGE,
        "Búsqueda sin resultados",
        P_PACIENTES_PAGE_TSX,
        "        setPatients(res.data);",
        "        if (res.data.length > 0) setPatients(res.data);",
    ),
    # M04 - Error de carga de pacientes con reintento
    Mutation(
        T_PACIENTES_PAGE,
        "Error de carga de pacientes con reintento",
        P_PACIENTES_PAGE_TSX,
        "  const handleRetry = () => {\n    setLoading(true);\n    setErrorMessages(null);\n    setReloadToken((prev) => prev + 1);\n  };",
        "  const handleRetry = () => {\n    setLoading(true);\n    setErrorMessages(null);\n    // setReloadToken((prev) => prev + 1);\n  };",
    ),
    # M05 - Toda variable CSS de las pantallas existe en tokens.css
    Mutation(
        T_CATALOGOS_STYLES,
        "Toda variable CSS de las pantallas existe en tokens.css",
        P_PACIENTES_PAGE_CSS,
        "  color: var(--color-text);\n  line-height: var(--line-height-base);",
        "  color: var(--color-inexistente);\n  line-height: var(--line-height-base);",
    ),
    # M06 - Sin tokens de fondo oscuro en las pantallas
    Mutation(
        T_CATALOGOS_STYLES,
        "Sin tokens de fondo oscuro en las pantallas",
        P_PACIENTES_PAGE_CSS,
        ".statusBanner {\n  padding: var(--space-3) var(--space-4);\n  background: var(--color-surface);",
        ".statusBanner {\n  padding: var(--space-3) var(--space-4);\n  background: var(--color-ice);",
    ),
    # M07 - Profesionales por defecto con estado en texto
    Mutation(
        T_CATALOGOS_PAGE,
        "Profesionales por defecto con estado en texto",
        P_CATALOGOS_API_TS,
        'export async function listCatalog(\n  client: ApiClient,\n  sectionKey: CatalogSectionKey,\n): Promise<ApiResult<readonly AnyCatalogItem[]>> {\n  const path =\n    sectionKey === "sillones"\n      ? "/chairs"\n      : sectionKey === "prestaciones"\n        ? "/services"\n        : "/professionals";',
        'export async function listCatalog(\n  client: ApiClient,\n  sectionKey: CatalogSectionKey,\n): Promise<ApiResult<readonly AnyCatalogItem[]>> {\n  const path =\n    sectionKey === "sillones"\n      ? "/chairs"\n      : sectionKey === "prestaciones"\n        ? "/services"\n        : "/professionals?active=true";',
    ),
    # M08 - Cambio a la sección de prestaciones
    Mutation(
        T_CATALOGOS_PAGE,
        "Cambio a la sección de prestaciones",
        P_CATALOGOS_PAGE_TSX,
        "  const config = resolveCatalogConfig(rawSection);",
        "  const config = resolveCatalogConfig(null);",
    ),
    # M09 - Pacientes y Catálogos con su título y un único h1
    Mutation(
        T_ROUTES,
        "Pacientes y Catálogos con su título y un único h1",
        P_CATALOGOS_PAGE_TSX,
        '<PageShell title="Catálogos">',
        '<PageShell title="Turnos Odontología">',
    ),
    # M10 - Tablas apiladas en celular, controles táctiles y foco visible
    Mutation(
        T_CATALOGOS_STYLES,
        "Tablas apiladas en celular, controles táctiles y foco visible",
        P_CATALOGOS_PAGE_CSS,
        "@media (max-width: 640px) {",
        "@media (max-width: 0px) {",
    ),
    # M11 - Catálogos y Pacientes habilitados para los tres roles
    Mutation(
        T_SHELL_NEW,
        "Catálogos y Pacientes habilitados para los tres roles",
        P_MENU_TS,
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "horarios-y-bloqueos",\n'
            '  "catalogos",\n'
            '  "pacientes",\n'
            '];'
        ),
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "horarios-y-bloqueos",\n'
            '  "pacientes",\n'
            '];'
        ),
    ),
    # M12 - Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px
    Mutation(
        T_SHELL_NAV,
        "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px",
        P_MENU_TS,
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "horarios-y-bloqueos",\n'
            '  "catalogos",\n'
            '  "pacientes",\n'
            '];'
        ),
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "horarios-y-bloqueos",\n'
            '  "catalogos",\n'
            '];'
        ),
    ),
    # M13 - Ítems deshabilitados con Próximamente conservan semántica y accesibilidad
    Mutation(
        T_SHELL_NAV,
        "ítems deshabilitados con Próximamente conservan semántica y accesibilidad",
        P_MENU_TS,
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "horarios-y-bloqueos",\n'
            '  "catalogos",\n'
            '  "pacientes",\n'
            '];'
        ),
        (
            'const ENABLED_MENU_IDS: readonly string[] = [\n'
            '  "agenda",\n'
            '  "turnos",\n'
            '  "horarios-y-bloqueos",\n'
            '  "catalogos",\n'
            '  "pacientes",\n'
            '];'
        ),
    ),
    # M14 - Alta de paciente
    Mutation(
        T_PACIENTES_FORM,
        "Alta de paciente",
        P_PATIENT_FORM_TSX,
        'phone: phone.trim() === "" ? null : phone.trim(),',
        'phone: phone.trim() === "" ? "" : phone.trim(),',
    ),
    # M15 - El formulario de paciente tiene solo los cuatro datos mínimos
    Mutation(
        T_PACIENTES_FORM,
        "El formulario de paciente tiene solo los cuatro datos mínimos",
        P_PATIENT_FORM_TSX,
        '<div className={styles.actions}>',
        '<div className={styles.fieldGroup}><label className={styles.label}>Observaciones</label><input className={styles.input} /></div><div className={styles.actions}>',
    ),
    # M16 - Edición de paciente con valores precargados
    Mutation(
        T_PACIENTES_FORM,
        "Edición de paciente con valores precargados",
        P_PATIENT_FORM_TSX,
        'setHealthInsurance(patient.healthInsurance ?? "");',
        'setHealthInsurance("");',
    ),
    # M17 - DNI duplicado muestra el mensaje literal del backend
    Mutation(
        T_PACIENTES_FORM,
        "DNI duplicado muestra el mensaje literal del backend",
        P_PATIENT_FORM_TSX,
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n      }',
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n        if (res.error.status === 409) setFieldErrors({ dni: "Error" });\n      }',
    ),
    # M18 - DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)
    Mutation(
        T_PACIENTES_FORM,
        "DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)",
        P_PATIENT_FORM_TSX,
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n      }',
        '      } else {\n        setGeneralAlert(["DNI inválido."]);\n      }',
    ),
    # M19 - Error 400 por campo marca el campo con aria-invalid
    Mutation(
        T_PACIENTES_FORM,
        "Error 400 por campo marca el campo con aria-invalid",
        P_PATIENT_FORM_TSX,
        "errorsByField[err.field] = err.message;",
        "// errorsByField[err.field] = err.message;",
    ),
    # M20 - Odontólogo consulta pacientes en solo lectura
    Mutation(
        T_PACIENTES_PAGE,
        "Odontólogo consulta pacientes en solo lectura",
        P_PACIENTES_PAGE_TSX,
        'const canEdit = user?.role === "administrador" || user?.role === "recepcion";',
        "const canEdit = true;",
    ),
    # M21 - El mensaje de estado se reemplaza entre acciones sin desmontar la región
    Mutation(
        T_PACIENTES_FORM,
        "El mensaje de estado se reemplaza entre acciones sin desmontar la región",
        P_PACIENTES_PAGE_TSX,
        "          onSuccess={(msg) => {\n            setStatusMessage(msg);",
        "          onSuccess={(msg) => {\n            setStatusMessage((prev) => (prev ? `${prev} ${msg}` : msg));",
    ),
    # M22 - Alta de prestación con duración numérica
    Mutation(
        T_CATALOGOS_FORM,
        "Alta de prestación con duración numérica",
        P_CONFIGS_TS,
        '    defaultDurationMin: Number(formData["defaultDurationMin"]),',
        '    defaultDurationMin: String(formData["defaultDurationMin"]),',
    ),
    # M23 - Duración no entera no se envía
    Mutation(
        T_CATALOGOS_FORM,
        "Duración no entera no se envía",
        P_CATALOG_FORM_TSX,
        'if (!/^\\d+$/.test(rawDuration)) {',
        'if (false && !/^\\d+$/.test(rawDuration)) {',
    ),
    # M24 - Duración inválida muestra el mensaje literal del backend
    Mutation(
        T_CATALOGOS_FORM,
        "Duración inválida muestra el mensaje literal del backend",
        P_CATALOG_FORM_TSX,
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n      }',
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n        onClose();\n      }',
    ),
    # M25 - Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)
    Mutation(
        T_CATALOGOS_FORM,
        "Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)",
        P_CATALOG_FORM_TSX,
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n      }',
        '      } else {\n        setGeneralAlert(getApiErrorMessages(res.error));\n        if (res.error.status === 409) setFieldErrors({ name: "Error" });\n      }',
    ),
    # M26 - Edición de profesional con matrícula vacía
    Mutation(
        T_CATALOGOS_FORM,
        "Edición de profesional con matrícula vacía",
        P_CONFIGS_TS,
        '    licenseNumber: formData["licenseNumber"]?.trim() ? formData["licenseNumber"].trim() : null,',
        '    licenseNumber: formData["licenseNumber"]?.trim() ? formData["licenseNumber"].trim() : "",',
    ),
    # M27 - Recepción y odontólogo consultan catálogos en solo lectura
    Mutation(
        T_CATALOGOS_PAGE,
        "Recepción y odontólogo consultan catálogos en solo lectura",
        P_CATALOGOS_PAGE_TSX,
        '  const isAdmin = user?.role === "administrador";',
        '  const isAdmin = user?.role === "administrador" || user?.role === "recepcion";',
    ),
    # M28 - Formulario de catálogo como hoja inferior en celular
    Mutation(
        T_CATALOGOS_MOBILE,
        "Formulario de catálogo como hoja inferior en celular",
        P_CATALOG_FORM_TSX,
        '      returnFocusRef={returnFocusRef}\n      isMobile={isMobile}\n    >',
        '      returnFocusRef={returnFocusRef}\n      isMobile={false}\n    >',
    ),
    # M29 - Desactivar un sillón exige confirmación interna
    Mutation(
        T_CONFIRM,
        "Desactivar un sillón exige confirmación interna",
        P_CATALOGOS_PAGE_TSX,
        '                              onClick={() => {\n                                setStatusMessage(null);\n                                setConfirmItem(item);\n                                setConfirmAction("deactivate");\n                                setConfirmDialogOpen(true);\n                              }}',
        '                              onClick={() => {\n                                setStatusMessage(null);\n                                void client.request(`/chairs/${item.id}/deactivate`, { method: "POST" });\n                                setConfirmItem(item);\n                                setConfirmAction("deactivate");\n                                setConfirmDialogOpen(true);\n                              }}',
    ),
    # M30 - Reactivar una prestación inactiva
    Mutation(
        T_CONFIRM,
        "Reactivar una prestación inactiva",
        P_CONFIRM_TSX,
        '    const res = isDeactivate\n      ? await deactivateCatalogItem(client, config.key, item.id)\n      : await reactivateCatalogItem(client, config.key, item.id);',
        '    const res = isDeactivate\n      ? await deactivateCatalogItem(client, config.key, item.id)\n      : await deactivateCatalogItem(client, config.key, item.id);',
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stdout: TextIO) -> None:
        self.stdout = stdout
        self.lines: list[str] = []

    def write(self, text: str) -> None:
        self.stdout.write(text + "\n")
        self.stdout.flush()
        self.lines.append(text)

    def save(self) -> None:
        OUTPUT.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def vitest_env() -> dict[str, str]:
    env = os.environ.copy()
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env


def file_sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def production_sha256() -> str:
    hasher = hashlib.sha256()
    for rel in PRODUCTION_FILES:
        path = REPO / rel
        if path.is_file():
            content = path.read_bytes().replace(b"\r\n", b"\n")
            hasher.update(rel.encode("utf-8"))
            hasher.update(b"\0")
            hasher.update(content)
            hasher.update(b"\0")
    return hasher.hexdigest()


def mutation_id(idx: int) -> str:
    return f"M{idx:02d}"


def check_definition(mutation: Mutation) -> None:
    path = REPO / mutation.file
    if not path.is_file():
        raise MutationAbort(f"No existe el archivo a mutar: {mutation.file}")
    content = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    orig = mutation.original.replace("\r\n", "\n")
    mut = mutation.mutated.replace("\r\n", "\n")
    count = content.count(orig)
    if count == 0:
        raise MutationAbort(
            f"El fragmento original no aparece en {mutation.file}:\n{orig}"
        )
    if count > 1:
        raise MutationAbort(
            f"El fragmento original aparece {count} veces en {mutation.file}:\n{orig}"
        )
    if orig == mut:
        raise MutationAbort(f"La mutación no modifica el contenido en {mutation.file}")


def apply_mutation(mutation: Mutation, content: str) -> str:
    orig = mutation.original.replace("\r\n", "\n")
    mut = mutation.mutated.replace("\r\n", "\n")
    norm_content = content.replace("\r\n", "\n")
    if orig not in norm_content:
        raise MutationAbort(f"Fragmento no encontrado al mutar {mutation.file}")
    replaced = norm_content.replace(orig, mut, 1)
    if "\r\n" in content:
        return replaced.replace("\n", "\r\n")
    return replaced


def listed_tests() -> list[tuple[str, str]]:
    result = subprocess.run(
        [*VITEST, "list", *C33_TEST_FILES, "--json"],
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
        if file in C33_TEST_FILES and (file, name) not in PREEXISTING_TESTS:
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
            f"tests de C-33 listados: {len(tests)}; mutaciones: {len(MUTATIONS)}\n"
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
    pattern = re.sub(r"([()[\]{}*+?^$|.\\])", r"\\\1", mutation.test_name) + "$"
    return run_vitest([mutation.test_file, "-t", pattern])


def first_own_frame(message: str) -> str | None:
    for line in message.splitlines():
        match = STACK_FRAME.match(line)
        if match and "node_modules" not in match.group("path"):
            return match.group("path").replace("\\", "/")
    return None


def invalid_reason(mutation: Mutation, report: dict[str, object]) -> str | None:
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
    failed_assertions = [a for a in ran if a.get("status") == "failed"]
    if not failed_assertions:
        return "ningun test fallo"
    failures = failed_assertions[0].get("failureMessages") or []
    if not isinstance(failures, list) or not failures:
        return "el test fallo sin mensaje"
    message = "\n".join(str(f) for f in failures)
    first_line = message.splitlines()[0].strip() if message.splitlines() else ""
    if INVALID_ERROR.search(first_line):
        return f"error de tiempo de ejecucion/compilacion ({first_line})"
    if not ASSERTION.search(first_line) and "expect(" not in first_line:
        return f"el fallo no es una asercion: {first_line}"
    frame = first_own_frame(message)
    if frame is None or not TEST_FILE.search(frame):
        return f"el fallo se origino fuera de un archivo de test ({frame})"
    return None


def print_diff(mutation: Mutation, original: str, mutated: str, report: Report) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        mutated.splitlines(keepends=True),
        fromfile=f"a/{mutation.file}",
        tofile=f"b/{mutation.file}",
        n=2,
    )
    report.write("".join(diff).rstrip())


def build_markdown_row(
    mid: str, mutation: Mutation, status: str, failure_line: str
) -> str:
    test_file_base = Path(mutation.test_file).name
    short_test = mutation.test_name.split(":")[0]
    escaped_failure = failure_line.replace("|", "\\|")
    return (
        f"| {mid} | `{test_file_base}` | `{short_test}` | "
        f"{status} | `{escaped_failure}` |"
    )


def update_verify_markdown(rows: list[str]) -> None:
    if not VERIFY.is_file():
        return
    content = VERIFY.read_text(encoding="utf-8")
    if TABLE_START not in content or TABLE_END not in content:
        return
    header = (
        "| ID | Archivo de test | Test | Estado | Mensaje de fallo |\n"
        "|---|---|---|---|---|\n"
    )
    new_table = f"{TABLE_START}\n{header}" + "\n".join(rows) + f"\n{TABLE_END}"
    before, rest = content.split(TABLE_START, 1)
    _, after = rest.split(TABLE_END, 1)
    VERIFY.write_text(f"{before}{new_table}{after}", encoding="utf-8")


def run_all(report: Report) -> int:
    initial_sha = production_sha256()
    report.write(SEPARATOR)
    report.write("VERIFICACION POR MUTACION DE C-33 (UI CATALOGOS Y PACIENTES)")
    report.write(f"SHA-256 inicial de archivos de produccion: {initial_sha}")
    report.write(SEPARATOR)

    for mutation in MUTATIONS:
        check_definition(mutation)

    test_count = check_one_to_one()
    report.write(
        f"Correspondencia 1:1 verificada: {test_count} tests evaluados (28 nuevos + 2 modificados en AppShellNavigation.test.tsx) vs {len(MUTATIONS)} mutaciones."
    )
    report.write(SEPARATOR)

    killed = 0
    invalid = 0
    markdown_rows: list[str] = []

    for idx, mutation in enumerate(MUTATIONS, start=1):
        mid = mutation_id(idx)
        report.write(f"[{mid}] {mutation.node_id}")
        report.write(f"    Archivo: {mutation.file}")

        target_path = REPO / mutation.file
        original_bytes = target_path.read_bytes()
        original_content = original_bytes.decode("utf-8")
        mutated_content = apply_mutation(mutation, original_content)
        if mutated_content == original_content:
            report.write("    FALLO: el mutante no cambio el archivo.")
            return 2

        print_diff(mutation, original_content, mutated_content, report)

        target_path.write_bytes(mutated_content.encode("utf-8"))
        try:
            res_mutated, rep_mutated = run_single(mutation)
        finally:
            target_path.write_bytes(original_bytes)

        res_restored, rep_restored = run_single(mutation)

        reason = invalid_reason(mutation, rep_mutated)
        if reason:
            invalid += 1
            status = f"INVALIDA ({reason})"
            first_fail = (
                res_mutated.stderr.splitlines()[0]
                if res_mutated.stderr.splitlines()
                else "sin stderr"
            )
        else:
            killed += 1
            status = "Matada"
            assertions = [
                a
                for f in rep_mutated.get("testResults", [])
                for a in f.get("assertionResults", [])
                if a.get("status") == "failed"
            ]
            first_msg = (
                assertions[0]["failureMessages"][0]
                if assertions and assertions[0].get("failureMessages")
                else "fallo esperado"
            )
            first_fail = first_msg.splitlines()[0].strip()

        restored_ok = res_restored.returncode == 0
        report.write(f"    Estado: {status}")
        report.write(f"    Fallo:  {first_fail}")
        report.write(
            f"    Restaurado a verde: {'si' if restored_ok else 'NO (PELIGRO)'}"
        )
        report.write("-" * 80)

        markdown_rows.append(build_markdown_row(mid, mutation, status, first_fail))

        if not restored_ok:
            report.write("ABORTANDO: el archivo restaurado no volvio a verde.")
            return 3

    final_sha = production_sha256()
    sha_ok = final_sha == initial_sha

    report.write(SEPARATOR)
    report.write("RESUMEN DE MUTACIONES")
    report.write(f"Mutaciones totales:    {len(MUTATIONS)}")
    report.write(f"Matadas por asercion:  {killed}")
    report.write(f"Invalidas:             {invalid}")
    report.write(f"SHA-256 inicial:       {initial_sha}")
    report.write(f"SHA-256 final:         {final_sha}")
    report.write(f"SHA-256 sin cambios:   {'si' if sha_ok else 'NO'}")
    report.write(SEPARATOR)

    update_verify_markdown(markdown_rows)

    if killed == len(MUTATIONS) and invalid == 0 and sha_ok:
        report.write("EXITO: todas las mutaciones fueron detectadas limpiamente.")
        return 0
    report.write("FALLO: se detectaron anomalias en la suite de mutacion.")
    return 1


def main() -> int:
    if "--check" in sys.argv:
        for m in MUTATIONS:
            check_definition(m)
        count = check_one_to_one()
        print(f"OK: {count} tests evaluados (28 nuevos + 2 modificados en AppShellNavigation.test.tsx) coinciden 1:1 con las {len(MUTATIONS)} mutaciones.")
        return 0

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rep = Report(sys.stdout)
    code = run_all(rep)
    rep.save()
    return code


if __name__ == "__main__":
    sys.exit(main())
