"""Verificación por mutación de los ajustes finales (frontend, Vitest)."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
OUTPUT = REPO / "docs" / "evidencias" / "ajustes-mutaciones.txt"
VITEST = ["node", str(FRONTEND / "node_modules" / "vitest" / "vitest.mjs")]

PROD_FILES = (
    "frontend/src/features/appointments/AppointmentFormDialog.tsx",
    "frontend/src/features/appointments/PatientSearchGroup.tsx",
    "frontend/src/features/appointments/PatientSearchGroup.module.css",
    "frontend/src/features/agenda/AgendaToolbar.tsx",
)

INVALID_ERROR = re.compile(
    r"^(ReferenceError|SyntaxError|TypeError|RangeError|TestingLibraryElementError"
    r"|Error: (Failed to load|Failed to resolve|Cannot find module|Transform failed))"
)
ASSERTION = re.compile(r"^(AssertionError\b|Error: expect\(|TestingLibraryElementError)")
STACK_FRAME = re.compile(r"^\s*at (?:.*\()?(?:file:///)?(?P<path>[A-Za-z]:[\\/][^:()]+|/[^:()]+):\d+:\d+\)?$")
TEST_FILE = re.compile(r"\.test\.tsx?$")

@dataclass(frozen=True)
class Mutation:
    test_file: str
    test_name: str
    file: str
    original: str
    mutated: str

MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "src/features/appointments/AppointmentFormDialog.test.tsx",
        "con todos los campos completos salvo el paciente, al pulsar Crear turno aparece mensaje de alerta y no se envía POST",
        "frontend/src/features/appointments/AppointmentFormDialog.tsx",
        '    if (!patientId) {\n      setPatientError("Elegí un paciente de la lista.");\n      patientSearchInputRef.current?.focus();\n      return;\n    }',
        '    if (!patientId) {\n      // setPatientError("Elegí un paciente de la lista.");\n      patientSearchInputRef.current?.focus();\n      return;\n    }',
    ),
    Mutation(
        "src/features/agenda/AgendaToolbar.test.tsx",
        "en vista semana no existe la opción Todos en Profesional; en vista día sí existe",
        "frontend/src/features/agenda/AgendaToolbar.tsx",
        '          {!isWeekView && <option value="">Todos</option>}',
        '          <option value="">Todos</option>',
    ),
)

def production_sha256() -> str:
    hasher = hashlib.sha256()
    for relative in sorted(PROD_FILES):
        path = REPO / relative
        hasher.update(path.as_posix().encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()

def vitest_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    return env

def run_single(mutation: Mutation) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    pattern = re.sub(r"([()[\]{}*+?^$|.\\])", r"\\\1", mutation.test_name) + "$"
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "vitest.json"
        res = subprocess.run(
            [*VITEST, "run", mutation.test_file, "-t", pattern, "--reporter=default", "--reporter=json", f"--outputFile.json={json_path}"],
            cwd=FRONTEND,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=vitest_env(),
            check=False,
        )
        report: dict[str, object] = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {}
    return res, report

def invalid_reason(report: dict[str, object]) -> str | None:
    files = report.get("testResults")
    if not isinstance(files, list) or not files:
        return "Vitest no genero resultados"
    ran = []
    for file_result in files:
        assertions = file_result.get("assertionResults", [])
        ran += [a for a in assertions if a.get("status") in ("passed", "failed")]
    failed_assertions = [a for a in ran if a.get("status") == "failed"]
    if not failed_assertions:
        return "ningun test fallo"
    failures = failed_assertions[0].get("failureMessages") or []
    if not failures:
        return "el test fallo sin mensaje"
    message = str(failures[0])
    first_line = message.splitlines()[0].strip() if message.splitlines() else ""
    if INVALID_ERROR.search(first_line) and "TestingLibraryElementError" not in first_line:
        return f"error de tiempo de ejecucion/compilacion ({first_line})"
    return None

def main():
    sha_initial = production_sha256()
    lines: list[str] = [
        "=" * 80,
        "MUTACIONES AJUSTES FINALES — VERIFICACIÓN AUTOMATIZADA",
        "=" * 80,
        f"SHA-256 inicial: {sha_initial}",
        "=" * 80,
        "",
    ]

    invalid_count = 0
    killed_count = 0

    for i, m in enumerate(MUTATIONS, 1):
        mid = f"M{i:02d}"
        path = REPO / m.file
        content = path.read_text(encoding="utf-8")
        norm_content = content.replace("\r\n", "\n")
        norm_orig = m.original.replace("\r\n", "\n")
        norm_mut = m.mutated.replace("\r\n", "\n")

        assert norm_orig in norm_content, f"Original no encontrado para {mid}"
        assert norm_content.count(norm_orig) == 1, f"Original duplicado para {mid}"

        mutated_content = norm_content.replace(norm_orig, norm_mut, 1)
        if "\r\n" in content:
            mutated_content = mutated_content.replace("\n", "\r\n")

        # Generar diff
        diff = "".join(difflib.unified_diff(
            content.splitlines(keepends=True),
            mutated_content.splitlines(keepends=True),
            fromfile=f"a/{m.file}",
            tofile=f"b/{m.file}",
            n=2,
        )).rstrip()

        lines.append(f"[{mid}] {m.test_file} > {m.test_name}")
        lines.append(diff)

        # Aplicar mutación
        try:
            path.write_text(mutated_content, encoding="utf-8")
            res, rep = run_single(m)
            inv = invalid_reason(rep)
            if inv:
                lines.append(f"RESULTADO: INVÁLIDA ({inv})")
                invalid_count += 1
            elif res.returncode != 0:
                # Extraer primera aserción
                files = rep.get("testResults", [])
                msg = ""
                for fr in files:
                    for ar in fr.get("assertionResults", []):
                        if ar.get("status") == "failed":
                            failures = ar.get("failureMessages", [])
                            if failures:
                                msg = failures[0].splitlines()[0].strip()
                                break
                lines.append("RESULTADO: ELIMINADA")
                lines.append(f"Aserción: {msg}")
                killed_count += 1
            else:
                lines.append("RESULTADO: SUPERVIVIENTE")
        finally:
            path.write_text(content, encoding="utf-8")

        # Comprobar que vuelve a verde
        res_green, _ = run_single(m)
        assert res_green.returncode == 0, f"{mid} no volvio a verde"
        lines.append("")

    sha_final = production_sha256()
    lines.extend([
        "=" * 80,
        "RESUMEN DE MUTACIONES AJUSTES FINALES",
        "=" * 80,
        f"Total mutaciones: {len(MUTATIONS)}",
        f"Eliminadas:       {killed_count}",
        f"Supervivientes:   {len(MUTATIONS) - killed_count - invalid_count}",
        f"Inválidas:        {invalid_count}",
        f"SHA-256 inicial:  {sha_initial}",
        f"SHA-256 final:    {sha_final}",
        f"SHA-256 sin cambios: {'si' if sha_initial == sha_final else 'no'}",
    ])

    report_text = "\n".join(lines) + "\n"
    OUTPUT.write_text(report_text, encoding="utf-8")
    print(report_text)

if __name__ == "__main__":
    main()
