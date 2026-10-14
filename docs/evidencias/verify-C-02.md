# Verify de C-02 crear-turno-sin-solapamientos

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fechas: 2026-10-08 (antes del archive) y 2026-10-12 (nueva corrida para guardar la evidencia).
- Quién: Amanda Pagano.
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy`
- Salidas completas de la corrida del 2026-10-12: [pytest-C-02.txt](pytest-C-02.txt) y [mypy-C-02.txt](mypy-C-02.txt)

## Resultado

- pytest: 107 tests pasaron (0,96 s en la corrida del 2026-10-12).
- mypy en modo estricto: "Success: no issues found in 20 source files".
- No hubo ningún test en rojo ni errores de tipos, así que el change se archivó el 2026-10-08 (commit `d51264a`).

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Turno válido con profesional y sillón libres | Feliz | `test_validate_new_appointment_free_professional_and_chair_returns_ok_with_reserved_appointment` |
| Solapamiento con un turno del mismo profesional | Error de negocio | `test_validate_new_appointment_same_professional_overlap_is_rejected_with_conflicting_id` |
| Turno que empieza exactamente cuando termina otro | Borde | `test_validate_new_appointment_without_conflict_returns_ok[empieza-cuando-termina-otro]` |

Los 31 escenarios de la spec `appointment-scheduling` tienen al menos un test cada uno.

## Otras verificaciones

- **El README funciona en un clon limpio** (2026-10-08): se clonó el repositorio en una carpeta nueva y se siguieron solo los comandos del README. La instalación terminó bien y pasaron los 107 tests y mypy.
- **El dominio sigue siendo puro**: el test `test_domain_package_real_directory_has_no_forbidden_imports` comprueba que `backend/app/domain` no importa FastAPI, SQLAlchemy, Redis, Pydantic ni módulos de archivos o red.
- **No se suben archivos generados**: se comprobó con `git check-ignore` que `.venv`, `.pytest_cache` y `.mypy_cache` quedan fuera del repositorio.
- **Otra máquina** (2026-10-09): el asistente de IA clonó el repositorio en Linux con Python 3.13, siguió el README y obtuvo los mismos 107 tests en verde y mypy sin errores.