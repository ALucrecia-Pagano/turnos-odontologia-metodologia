# Verificación de specs-requisitos-concisos

Change de mantenimiento documental: acorta a menos de 500 caracteres 15 requisitos de `appointment-lifecycle` y `appointment-scheduling` para que `openspec validate --all --strict` vuelva a verde. No toca `backend/`, `frontend/` ni tests.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección (2026-11-07).

- Línea de base (0.1): [validate-antes-specs.txt](validate-antes-specs.txt). Falla solo en `spec/appointment-lifecycle` (3 warnings `>500 characters`) y `spec/appointment-scheduling` (12 warnings); `Totals: 12 passed, 2 failed (14 items)`.
- Escenarios conservados: [escenarios-specs.txt](escenarios-specs.txt), generado por [escenarios-specs.py](escenarios-specs.py). Compara carácter por carácter cada `#### Scenario:` de los 15 requisitos `MODIFIED` del delta con el mismo requisito de `openspec/specs/`: `15 requisitos, 132 escenarios, 0 diferencias`. Los finales de línea se normalizan a LF: la copia de trabajo de `openspec/specs/appointment-scheduling/spec.md` está en CRLF por `core.autocrlf`, pero en el repo está en LF.
- Suite por defecto (2.1): [pytest-specs.txt](pytest-specs.txt): `895 passed, 524 deselected`, igual que en [pytest-C-24.txt](pytest-C-24.txt).
- Integración (2.1): [pytest-integration-specs.txt](pytest-integration-specs.txt): `524 passed, 895 deselected`, igual que en [pytest-integration-C-24.txt](pytest-integration-C-24.txt).
- `mypy --strict app tests` (2.1): [mypy-specs.txt](mypy-specs.txt): `Success: no issues found in 184 source files`.
- Trazabilidad (2.2): todos terminan con código 0 y 0 problemas.
  - [matriz-C-19.txt](matriz-C-19.txt): `codigo de salida: 0`.
  - [trazabilidad-C-19.txt](trazabilidad-C-19.txt): `problemas: 0` (135/135 escenarios).
  - [trazabilidad-C-20.txt](trazabilidad-C-20.txt): `108 escenarios, 0 problemas`.
  - [trazabilidad-C-21.txt](trazabilidad-C-21.txt): `48 escenarios, 0 problemas`.
  - [trazabilidad-C-22.txt](trazabilidad-C-22.txt): `20 escenarios, 0 problemas`.
  - [trazabilidad-C-23.txt](trazabilidad-C-23.txt): `36 escenarios, 0 problemas`.
  - [trazabilidad-C-24.txt](trazabilidad-C-24.txt): `34 escenarios, 0 problemas`.

  Al regenerarse, `trazabilidad-C-19.txt` y `trazabilidad-C-20.txt` solo cambiaban la línea `tests recolectados por pytest` (1349 → 1419, por los tests de changes posteriores). Se restauraron para no reescribir evidencias de otros changes.
- Sincronización simulada: [validate-simulacion-archive-specs.txt](validate-simulacion-archive-specs.txt). Sobre una copia de `openspec/` fuera del repo, `openspec archive specs-requisitos-concisos --yes` aplicó `appointment-lifecycle` (~3) y `appointment-scheduling` (+6, ~12), y `openspec validate --all --strict` terminó con `Totals: 13 passed, 0 failed (13 items)`.
- Sincronización (1.1 y 1.2): la CLI 1.16.0 no tiene un comando `sync`, y la única fusión de deltas que hace la herramienta es la de `openspec archive`. Por eso se corrió `openspec archive specs-requisitos-concisos --yes` sobre una copia nueva de `openspec/` fuera del repo y se trajeron al repo solo los dos `spec.md` que generó. No se editó `openspec/specs/` a mano. `git diff --stat openspec/specs/` muestra solo `appointment-lifecycle/spec.md` (7 líneas) y `appointment-scheduling/spec.md` (85 líneas). `openspec validate appointment-lifecycle --type spec --strict` y `openspec validate appointment-scheduling --type spec --strict` dan `is valid` (código 0).
- Validación después de sincronizar (2.3): [validate-despues-specs.txt](validate-despues-specs.txt): `Totals: 14 passed, 0 failed (14 items)`, con todas las specs y los changes abiertos (`frontend-base-react-vite`, `ui-login-y-sesion` y este) válidos. Da lo mismo que la simulación. La única diferencia es la línea `change/specs-requisitos-concisos`, que en la simulación ya estaba archivado (13 ítems).
- Archivo: el change se archivó con `openspec archive specs-requisitos-concisos --yes --skip-specs`, porque los deltas ya estaban sincronizados. `openspec/specs/` quedó idéntico antes y después del archive.

## Los 15 requisitos acortados (`MODIFIED`)

| # | Spec | Requisito | Chars viejos | Chars nuevos | Escenarios |
|---|------|-----------|-------------:|-------------:|-----------:|
| 1 | `appointment-lifecycle` | Tabla única de transiciones ordinarias | 705 | 481 | 2 |
| 2 | `appointment-lifecycle` | Operaciones con resultado de agenda y copia | 523 | 493 | 3 |
| 3 | `appointment-lifecycle` | Mensajes exactos y metadatos | 599 | 444 | 9 |
| 4 | `appointment-scheduling` | Alta de un turno válido | 1089 | 487 | 2 |
| 5 | `appointment-scheduling` | Todas las violaciones, en orden estable | 1520 | 422 | 21 |
| 6 | `appointment-scheduling` | Validez de la duración | 572 | 412 | 13 |
| 7 | `appointment-scheduling` | Contenido de cada violación | 3213 | 492 | 12 |
| 8 | `appointment-scheduling` | Turno dentro de un solo día local | 618 | 441 | 4 |
| 9 | `appointment-scheduling` | Turno dentro del horario de atención | 2979 | 463 | 24 |
| 10 | `appointment-scheduling` | Validez de un conjunto de tramos | 1757 | 493 | 8 |
| 11 | `appointment-scheduling` | Turno fuera de los bloqueos del profesional | 563 | 434 | 17 |
| 12 | `appointment-scheduling` | Mensaje de un turno bloqueado | 1107 | 459 | 4 |
| 13 | `appointment-scheduling` | Turnos afectados por un bloqueo | 926 | 495 | 5 |
| 14 | `appointment-scheduling` | Mensaje de un turno en el pasado | 934 | 480 | 5 |
| 15 | `appointment-scheduling` | Nombre del profesional y del sillón | 576 | 426 | 3 |
| | | **Total** | | | **132** |

Los caracteres viejos y nuevos vienen de la tabla de [design.md](../../openspec/changes/archive/2026-11-07-specs-requisitos-concisos/design.md). La columna de escenarios sale de [escenarios-specs.txt](escenarios-specs.txt).

## Los 6 requisitos desglosados (`ADDED`, en `appointment-scheduling`)

| Requisito nuevo | Chars | Viene de |
|-----------------|------:|----------|
| Orden de los conflictos de agenda | 441 | Todas las violaciones, en orden estable |
| Mensajes de validez de duración, inicio y medianoche | 486 | Contenido de cada violación |
| Plantillas y nombres en mensajes de solapamiento | 495 | Contenido de cada violación |
| Unión de tramos contiguos o superpuestos del día | 448 | Turno dentro del horario de atención |
| Mensaje de un turno fuera del horario de atención | 474 | Turno dentro del horario de atención |
| Orden y mensajes al validar tramos de horario | 458 | Validez de un conjunto de tramos |

Cada uno tiene su propio escenario. La trazabilidad cláusula por cláusula está en [design.md](../../openspec/changes/archive/2026-11-07-specs-requisitos-concisos/design.md).

## Archivos no tocados

`backend/`, `frontend/` y `docker-compose.yml` quedan sin cambios. En `openspec/specs/` solo cambian los dos `spec.md` sincronizados.
