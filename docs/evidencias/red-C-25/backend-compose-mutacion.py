"""Mutacion a mano del test de compose de C-18, actualizado en C-25.

Uso, desde la raiz del repo:

    python docs/evidencias/red-C-25/backend-compose-mutacion.py > docs/evidencias/red-C-25/backend-compose-mutacion.txt 2>&1

Le agrega JWT_SECRET al entorno del servicio frontend de docker-compose.yml, corre solo
test_compose_defines_services_without_literal_secrets (tiene que fallar), restaura el
archivo byte a byte en un finally y vuelve a correr el test (tiene que pasar).
"""

from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
COMPOSE = REPO / "docker-compose.yml"
BACKEND = REPO / "backend"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
TEST = "tests/test_compose.py::test_compose_defines_services_without_literal_secrets"
ORIGINAL = '      CHOKIDAR_USEPOLLING: "true"\n'
MUTATED = '      CHOKIDAR_USEPOLLING: "true"\n      JWT_SECRET: ${JWT_SECRET}\n'


def run_test() -> int:
    result = subprocess.run(
        [str(PYTHON if PYTHON.exists() else sys.executable), "-m", "pytest", "-o", "addopts=",
         "--no-header", "--tb=short", "-p", "no:cacheprovider", TEST],
        cwd=BACKEND, capture_output=True, encoding="utf-8", errors="replace", check=False,
    )
    print(result.stdout + result.stderr)
    return result.returncode


def main() -> int:
    original_bytes = COMPOSE.read_bytes()
    content = original_bytes.decode("utf-8")
    newline = "\r\n" if "\r\n" in content else "\n"
    original = ORIGINAL.replace("\n", newline)
    count = content.count(original)
    if count != 1:
        print(f"ABORTADO: el original aparece {count} veces en docker-compose.yml")
        return 2
    mutated_content = content.replace(original, MUTATED.replace("\n", newline), 1)
    if mutated_content == content:
        print("ABORTADO: la mutacion no cambia docker-compose.yml")
        return 2

    print("diff:")
    print("".join(difflib.unified_diff(
        content.replace("\r\n", "\n").splitlines(keepends=True),
        mutated_content.replace("\r\n", "\n").splitlines(keepends=True),
        fromfile="a/docker-compose.yml", tofile="b/docker-compose.yml", n=2,
    )))
    COMPOSE.write_bytes(mutated_content.encode("utf-8"))
    try:
        print("--- con la mutacion (se espera que falle) ---")
        mutated_code = run_test()
    finally:
        COMPOSE.write_bytes(original_bytes)

    print("--- restaurado (se espera que pase) ---")
    restored_code = run_test()
    restored_ok = COMPOSE.read_bytes() == original_bytes
    print(f"codigo con la mutacion: {mutated_code}")
    print(f"codigo restaurado: {restored_code}")
    print(f"docker-compose.yml restaurado byte a byte: {'si' if restored_ok else 'NO'}")
    return 0 if mutated_code != 0 and restored_code == 0 and restored_ok else 1


if __name__ == "__main__":
    sys.exit(main())
