# Verify de C-06 bloqueos-de-agenda

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fecha: 2026-10-28, antes del archive.
- Quién: Amanda Pagano (el apply lo ejecutó un agente; la autora aprobó el punto de control 3.5 el 2026-10-28, con un ajuste).
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy --strict app tests`
- Desde la raíz: `openspec validate bloqueos-de-agenda --strict`
- Salidas completas: [pytest-C-06.txt](pytest-C-06.txt) y [mypy-C-06.txt](mypy-C-06.txt)

## Resultado

- pytest: pasaron los 273 tests (ver pytest-C-06.txt). C-05 terminó con 232; el baseline del apply en el punto de control fue 241 y los grupos 4 a 8 agregaron 32.
- mypy en modo estricto: "Success: no issues found in 28 source files". Hay dos archivos más que en C-05: `rules/blocks.py` y `tests/domain/test_blocks.py`.
- `openspec validate bloqueos-de-agenda --strict`: "Change 'bloqueos-de-agenda' is valid".
- No hubo tests en rojo ni errores de tipos.

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Turno que termina justo cuando empieza el bloqueo (09:30–10:00 local, 12:30–13:00 UTC) | Feliz | `test_validate_new_appointment_block_edges_are_half_open[termina-al-inicio]` |
| Turno dentro de un bloqueo (10:30–11:00 local dentro de BL1) | Error de negocio | `test_validate_new_appointment_inside_a_block_reports_blocked_time_with_block_id` |
| Último turno del domingo local dentro de un bloqueo de varios días (23:30 local = 02:30 UTC del lunes) | Borde | `test_validate_new_appointment_multi_day_block_compares_instants[ultimo-turno-del-domingo-local]` |
| Bloqueo que pisa turnos existentes (solo T2 y T3, sin cancelarlos) | Borde | `test_appointments_affected_by_block_returns_active_overlapping_of_same_professional` |

## Los 43 escenarios del delta y su test

En el orden de [la delta spec](../../openspec/changes/bloqueos-de-agenda/specs/appointment-scheduling/spec.md). Los tests de `Alta`, `Todas las violaciones`, `Turno fuera de los bloqueos del profesional` y `Mensaje de un turno bloqueado` están en `backend/tests/domain/test_validate_new_appointment.py` y llevan el prefijo `test_validate_new_appointment_`, que se omite en la tabla; los de `Validez de un bloqueo` y `Turnos afectados por un bloqueo`, en `backend/tests/domain/test_blocks.py`; los de `Instantes del bloqueo`, en `backend/tests/domain/test_model.py`. En los parametrizados, el id del caso va entre corchetes. Los 15 escenarios que ya existían en los requisitos modificados siguen cubiertos por los mismos tests de C-02 a C-05 (no se cambió ninguna llamada ni aserción; solo `CTX` y `_ctx` suman `blocks=()`). Los escenarios de C-02 a C-05 que este change no toca siguen cubiertos por [verify-C-02.md](verify-C-02.md) a [verify-C-05.md](verify-C-05.md).

Nuevos (28), marcados con **N**; los otros 15 ya existían. Uno de los nuevos ("Mensaje de un bloqueo con motivo vacío o en blanco") es el ajuste de la autora en el punto de control, y dos ("Bloqueo inválido recibido con la agenda" y "Turnos afectados por un bloqueo inválido") son hallazgos del apply que volvieron a la spec.

| Requisito | Escenario de la spec | Test |
|---|---|---|
| Alta de un turno válido | Turno válido con profesional y sillón libres | `free_professional_and_chair_returns_ok_with_reserved_appointment`; `all_references_existing_and_active_returns_ok` |
| Alta de un turno válido | Turno válido con otros turnos que no chocan | `without_conflict_returns_ok[otros-turnos-que-no-chocan]` |
| Todas las violaciones, en orden estable | Varios conflictos de ambos tipos | `many_conflicts_are_ordered_professional_first_by_start` |
| Todas las violaciones, en orden estable | Orden independiente del orden de la lista recibida | `violation_order_ignores_input_list_order[d-c-b]`; `[c-d-b]` |
| Todas las violaciones, en orden estable | Varias referencias que fallan a la vez | `several_failing_references_are_reported_in_fixed_order` |
| Todas las violaciones, en orden estable | Referencia y duración inválidas a la vez | `invalid_reference_and_duration_are_reported_together` |
| Todas las violaciones, en orden estable | Prestación inactiva con duración por defecto inválida | `service_problem_and_invalid_duration_are_reported_in_order[prestacion-inactiva-con-defecto-invalido]` |
| Todas las violaciones, en orden estable | Violación de validez en un horario ocupado | `reference_violation_in_busy_slot_reports_no_overlap` |
| Todas las violaciones, en orden estable | Referencia, duración e inicio inválidos a la vez | `unknown_reference_invalid_duration_and_invalid_start_are_reported_together` |
| Todas las violaciones, en orden estable | Inicio fuera de la grilla en un turno que cruza la medianoche | `off_grid_start_crossing_midnight_reports_start_then_midnight` |
| Todas las violaciones, en orden estable | Inicio con segundos en un turno que cruza la medianoche por segundos | `off_grid_start_with_seconds_crossing_midnight_by_seconds_reports_both` |
| Todas las violaciones, en orden estable | Inicio fuera de la grilla en un horario ocupado | `start_off_grid_in_busy_slot_reports_only_start` |
| Todas las violaciones, en orden estable | Fuera de horario y solapado a la vez | `outside_working_hours_and_overlapping_reports_horario_first` |
| Todas las violaciones, en orden estable | Duración inválida en un día sin horario | `invalid_duration_on_a_day_without_slots_reports_only_duration` |
| Todas las violaciones, en orden estable | Inicio fuera de la grilla en un día sin horario | `off_grid_start_on_a_day_without_slots_reports_only_start` |
| Todas las violaciones, en orden estable | **N** Fuera de horario, bloqueado y solapado a la vez | `outside_hours_blocked_and_overlapping_reports_all_in_order` |
| Todas las violaciones, en orden estable | **N** Duración inválida dentro de un bloqueo | `invalid_duration_inside_a_block_reports_only_duration` |
| Turno fuera de los bloqueos del profesional | **N** Turno dentro de un bloqueo | `inside_a_block_reports_blocked_time_with_block_id` |
| Turno fuera de los bloqueos del profesional | **N** Turno que termina justo cuando empieza el bloqueo | `block_edges_are_half_open[termina-al-inicio]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que empieza justo cuando termina el bloqueo | `block_edges_are_half_open[empieza-al-fin]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que pisa el inicio del bloqueo | `block_edges_are_half_open[pisa-el-inicio]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que pisa el fin del bloqueo | `block_edges_are_half_open[pisa-el-fin]` |
| Turno fuera de los bloqueos del profesional | **N** Bloqueo de otro profesional | `block_of_another_professional_does_not_count` |
| Turno fuera de los bloqueos del profesional | **N** Turno dentro de un bloqueo de varios días | `multi_day_block_compares_instants[martes-dentro]` |
| Turno fuera de los bloqueos del profesional | **N** Último turno del domingo local dentro de un bloqueo de varios días | `multi_day_block_compares_instants[ultimo-turno-del-domingo-local]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que empieza justo cuando termina un bloqueo de varios días | `multi_day_block_compares_instants[empieza-al-fin]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que termina justo cuando empieza un bloqueo de varios días | `multi_day_block_compares_instants[termina-al-inicio]` |
| Turno fuera de los bloqueos del profesional | **N** Turno que pisa dos bloqueos | `overlapping_two_blocks_reports_both_in_start_order[en-orden]` |
| Turno fuera de los bloqueos del profesional | **N** Orden de los bloqueos independiente del orden recibido | `overlapping_two_blocks_reports_both_in_start_order[invertidos]` |
| Turno fuera de los bloqueos del profesional | **N** Bloqueo inválido recibido con la agenda (hallazgo del apply) | `invalid_block_in_context_is_ignored_without_raising` |
| Mensaje de un turno bloqueado | **N** Mensaje de un bloqueo sin motivo | `blocked_time_message_without_reason` |
| Mensaje de un turno bloqueado | **N** Mensaje de un bloqueo de varios días con motivo | `blocked_time_message_multi_day_block_with_reason` |
| Mensaje de un turno bloqueado | **N** Mensaje de un bloqueo con motivo vacío o en blanco (ajuste del punto de control) | `blocked_time_message_blank_reason_counts_as_none[vacio]`; `[solo-espacios]` |
| Validez de un bloqueo | **N** Bloqueo válido | `test_validate_block_reports_invalid_only_when_start_is_not_before_end[bloqueo-valido]` |
| Validez de un bloqueo | **N** Bloqueo con inicio igual al fin | `test_validate_block_start_equal_to_end_reports_invalid_block`; `test_validate_block_message_says_start_must_be_before_end_without_conflicting_ids` |
| Validez de un bloqueo | **N** Bloqueo con inicio posterior al fin | `test_validate_block_reports_invalid_only_when_start_is_not_before_end[inicio-posterior-al-fin]` |
| Validez de un bloqueo | **N** Bloqueo de un minuto, fuera de la grilla | `test_validate_block_reports_invalid_only_when_start_is_not_before_end[un-minuto-fuera-de-la-grilla]` |
| Instantes del bloqueo con zona horaria y normalizados a UTC | **N** Bloqueo cargado en hora de Buenos Aires | `test_block_loaded_in_buenos_aires_time_is_normalized_to_utc` |
| Instantes del bloqueo con zona horaria y normalizados a UTC | **N** Bloqueo con un instante sin zona | `test_block_instant_without_timezone_raises_value_error[inicio-naive]`; `[fin-naive]` |
| Turnos afectados por un bloqueo | **N** Bloqueo que pisa turnos existentes | `test_appointments_affected_by_block_returns_active_overlapping_of_same_professional` |
| Turnos afectados por un bloqueo | **N** El bloqueo no cambia los turnos que pisa | `test_appointments_affected_by_block_returns_them_unchanged` |
| Turnos afectados por un bloqueo | **N** Bloqueo que no pisa ningún turno | `test_appointments_affected_by_block_without_overlapping_returns_empty` |
| Turnos afectados por un bloqueo | **N** Turnos afectados por un bloqueo inválido (hallazgo del apply) | `test_appointments_affected_by_invalid_block_returns_empty_without_raising` |

Tests extra (no son escenarios): en `test_model.py`, `test_block_with_start_after_end_is_built_without_raising` (D3: el orden no se valida al construir); en `test_violations.py`, los dos códigos nuevos y `conflicting_block_id` (3 tests); en `test_intervals.py`, `format_local_date_time` (3 instantes, entre ellos uno cuyo día local es anterior al de UTC, y el instante naive).

## Desglose de los 273 tests

| Archivo | Qué prueba | Hasta C-05 | C-06 | Total |
|---|---|---|---|---|
| `test_import_guard.py`, `test_domain_dependencies.py` y `test_smoke.py` | Guardia de dependencias y smoke (C-01) | 35 | 0 | 35 |
| `test_model.py` | Modelo, incluido `Block` (normalización, naive, orden no validado) | 10 | 4 | 14 |
| `test_intervals.py` | Intervalos y hora local, incluido `format_local_date_time` | 29 | 4 | 33 |
| `test_violations.py` | Códigos de violación (los dos nuevos) y `conflicting_block_id` | 21 | 5 | 26 |
| `test_validate_new_appointment.py` | Escenarios de la spec | 116 | 19 | 135 |
| `test_working_hours.py` | Validez de un conjunto de tramos | 21 | 0 | 21 |
| `test_blocks.py` (nuevo) | Validez de un bloqueo y turnos afectados | 0 | 9 | 9 |
| **Total** | | **232** | **41** | **273** |

## Desvíos durante el apply

El detalle está en la sección "Desvíos durante el apply" de [design.md](../../openspec/changes/bloqueos-de-agenda/design.md). Los principales:

1. **Punto de control 3.5 (2026-10-28), un ajuste de la autora:** un motivo con solo espacios (`"   "`) cuenta como vacío. Se actualizaron D8 y la spec y se agregó el escenario "Mensaje de un bloqueo con motivo vacío o en blanco"; el caso `"   "` se vio en rojo antes de agregar el `strip`.
2. **Hallazgo del apply que volvió a la spec (8.3):** D7 dice que un bloqueo con inicio igual o posterior al fin nunca se solapa, pero la spec no lo cubría. Hoy son los escenarios "Bloqueo inválido recibido con la agenda" y "Turnos afectados por un bloqueo inválido"; con `Interval` en vez de la comparación directa, los dos lanzan `ValueError`.
3. **GREEN en pasos:** 2.2 (primero los códigos, después el campo) y 6.3–6.4 (mensaje sin motivo, con motivo sin `strip`, con `strip`), para ver cada rojo.
4. **Refactors extra:** los helpers privados `_overlapping_blocks` (filtro y orden) y `_blocked_message` (mensaje); las firmas públicas de D7 no cambian.
5. **Triangulaciones que pasaron de entrada** (4.3, 5.3 a 5.5, 7.1, 7.2, 8.3): se comprobó con mutaciones temporales que pueden fallar (por ejemplo, comparar por fecha UTC hace fallar el último turno del domingo local), y se restauró el código.

## Otras verificaciones

- **El dominio sigue siendo puro.** `test_domain_package_real_directory_has_no_forbidden_imports` pasa sin cambiar la allowlist. En `backend/app/domain` no hay `datetime.now`, `utcnow`, `time.time`, `uuid1`, `Any`, `os.environ`, `getenv` ni la zona escrita en el código. No hay `raise` nuevos: `Block` usa el `_to_utc` que ya existía y `rules/blocks.py` no lanza nada. `uuid4()` aparece solo en un docstring de `model.py` que dice que el dominio no lo llama.
- **La zona se recibe por parámetro.** `ScheduleContext(tz, working_hours, blocks)` no tiene valores por defecto; la zona solo aparece en los tests.
- **Las reglas de negocio son violaciones, no excepciones.** `BLOCKED_TIME` e `INVALID_BLOCK` se devuelven como resultado; un bloqueo inválido se puede construir.
- **Crear un bloqueo no cancela ni mueve turnos (SU-05).** `appointments_affected_by_block` devuelve los mismos objetos recibidos, sin cambios.
- **El ejemplo de `backend/README.md` funciona.** Se corrió en el entorno virtual: imprime `2026-10-20 13:30:00+00:00`.
- **No se hizo ningún commit.**
