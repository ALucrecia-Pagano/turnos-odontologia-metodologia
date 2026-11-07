# Tasks: specs-requisitos-concisos

## 0. Línea de base

- [ ] 0.1 Capturar la línea de base ejecutando `openspec validate --all --strict` y redirigiendo la salida a `docs/evidencias/validate-antes-specs.txt`, verificando que aparecen los 15 warnings (`>500 characters`) en `spec/appointment-lifecycle` (3) y `spec/appointment-scheduling` (12).

## 1. Aplicación de deltas en las especificaciones principales

- [ ] 1.1 Aplicar el delta de `specs/appointment-lifecycle/spec.md` sobre `openspec/specs/appointment-lifecycle/spec.md` (3 requisitos `MODIFIED`) y verificar con `openspec validate appointment-lifecycle --type spec --strict` que pasa sin advertencias ni errores.
- [ ] 1.2 Aplicar el delta de `specs/appointment-scheduling/spec.md` sobre `openspec/specs/appointment-scheduling/spec.md` (12 requisitos `MODIFIED` y 6 requisitos `ADDED`) y verificar con `openspec validate appointment-scheduling --type spec --strict` que pasa sin advertencias ni errores.

## 2. Comprobación de no regresión y evidencias

- [ ] 2.1 Ejecutar `pytest`, `pytest -m integration` y `mypy --strict` desde `backend/`, comprobando que el resultado sigue en verde sin tocar código ni tests.
- [ ] 2.2 Ejecutar `docs/evidencias/matriz-C-19.py`, `trazabilidad-C-19.py`, `trazabilidad-C-20.py`, `trazabilidad-C-21.py`, `trazabilidad-C-22.py` y `trazabilidad-C-23.py`, comprobando que todos terminan con código 0 y 0 problemas.
- [ ] 2.3 Ejecutar `openspec validate --all --strict` redirigiendo la salida en verde a `docs/evidencias/validate-despues-specs.txt` y verificar que todas las specs y changes pasan con código 0.
- [ ] 2.4 Redactar `docs/evidencias/verify-specs-requisitos-concisos.md` con el resumen de los 15 requisitos acortados, los 6 requisitos desglosados y las referencias a `validate-antes-specs.txt` y `validate-despues-specs.txt`.
