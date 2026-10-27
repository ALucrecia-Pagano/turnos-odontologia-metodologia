# Verify de C-05 horario-de-atencion

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fecha: 2026-10-26, antes del archive.
- Quién: Amanda Pagano (el apply lo ejecutó un agente; la autora aprobó el punto de control 3.5 el 2026-10-26, con dos ajustes).
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy --strict app tests`
- Desde la raíz: `openspec validate horario-de-atencion --strict`
- Salidas completas: [pytest-C-05.txt](pytest-C-05.txt) y [mypy-C-05.txt](mypy-C-05.txt)

## Resultado

- pytest: pasaron los 232 tests (ver pytest-C-05.txt). C-04 terminó con 181; el baseline del apply en el punto de control fue 186 y los grupos 4 a 7 agregaron 46.
- mypy en modo estricto: "Success: no issues found in 26 source files". Hay dos archivos más que en C-04: `rules/working_hours.py` y `tests/domain/test_working_hours.py`.
- `openspec validate horario-de-atencion --strict`: "Change 'horario-de-atencion' is valid".
- No hubo tests en rojo ni errores de tipos.

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Turno completo dentro de un tramo (10:00–10:30) | Feliz | `test_validate_new_appointment_inside_a_slot_returns_ok[completo-dentro]` |
| Turno que empieza dentro y termina después del fin del tramo (12:30–13:30) | Error de negocio | `test_validate_new_appointment_starting_inside_and_ending_after_the_slot_is_outside_working_hours` |
| Instante UTC dentro del tramo que en hora local queda fuera (06:00 local) | Borde | `test_validate_new_appointment_utc_instant_inside_slot_but_outside_in_local_time_is_rejected` |
| Turno que pasa de un tramo a otro contiguo (12:30–13:30) | Borde | `test_validate_new_appointment_spanning_two_contiguous_slots_returns_ok` |

## Los 47 escenarios del delta y su test

En el orden de [la delta spec](../../openspec/changes/horario-de-atencion/specs/appointment-scheduling/spec.md). Los tests de `Alta`, `Todas las violaciones`, `Hora local` y `Turno dentro del horario de atención` están en `backend/tests/domain/test_validate_new_appointment.py` y llevan el prefijo `test_validate_new_appointment_`, que se omite en la tabla; los de `Validez de un conjunto de tramos` están en `backend/tests/domain/test_working_hours.py` con el prefijo `test_validate_working_hours_`. En los parametrizados, el id del caso va entre corchetes. Los 14 escenarios que ya existían en los requisitos modificados siguen cubiertos por los mismos tests de C-02 a C-04 (no se cambió ninguna llamada ni aserción; solo `CTX` suma los tramos de día completo). Los escenarios de C-02 a C-04 que este change no toca siguen cubiertos por [verify-C-02.md](verify-C-02.md), [verify-C-03.md](verify-C-03.md) y [verify-C-04.md](verify-C-04.md).

Nuevos (33), marcados con **N**; los otros 14 ya existían. Dos de los nuevos ("Turno que termina a la medianoche local, después del fin del tramo" y "Tramo contenido en otro") son hallazgos del apply que volvieron a la spec.

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
| Todas las violaciones, en orden estable | **N** Fuera de horario y solapado a la vez | `outside_working_hours_and_overlapping_reports_horario_first` |
| Todas las violaciones, en orden estable | **N** Duración inválida en un día sin horario | `invalid_duration_on_a_day_without_slots_reports_only_duration` |
| Todas las violaciones, en orden estable | **N** Inicio fuera de la grilla en un día sin horario | `off_grid_start_on_a_day_without_slots_reports_only_start` |
| Hora local en la zona horaria recibida | Instante UTC que en hora local cae en otro día | `utc_instant_on_previous_local_day_is_rejected_as_crosses_midnight` |
| Hora local en la zona horaria recibida | Turno que cruza la medianoche UTC pero no la local | `crossing_utc_midnight_but_not_local_midnight_returns_ok` |
| Turno dentro del horario de atención | **N** Turno completo dentro de un tramo | `inside_a_slot_returns_ok[completo-dentro]` |
| Turno dentro del horario de atención | **N** Turno que empieza justo al inicio del tramo | `inside_a_slot_returns_ok[justo-al-inicio]` |
| Turno dentro del horario de atención | **N** Turno que termina justo al fin del tramo de la mañana | `inside_a_slot_returns_ok[justo-al-fin-de-la-manana]` |
| Turno dentro del horario de atención | **N** Turno que termina justo al fin del tramo de la tarde | `inside_a_slot_returns_ok[justo-al-fin-de-la-tarde]` |
| Turno dentro del horario de atención | **N** Turno que empieza dentro y termina después del fin del tramo | `starting_inside_and_ending_after_the_slot_is_outside_working_hours` |
| Turno dentro del horario de atención | **N** Turno que empieza antes del inicio del tramo | `outside_the_slots_is_rejected[empieza-antes]` |
| Turno dentro del horario de atención | **N** Turno que ocupa justo el hueco entre dos tramos | `outside_the_slots_is_rejected[ocupa-el-hueco]` |
| Turno dentro del horario de atención | **N** Turno dentro del hueco entre dos tramos | `outside_the_slots_is_rejected[dentro-del-hueco]` |
| Turno dentro del horario de atención | **N** Turno que empieza en un tramo y termina en el siguiente, con hueco | `outside_the_slots_is_rejected[une-tramos-con-hueco]` |
| Turno dentro del horario de atención | **N** Turno en un día sin tramos | `outside_the_slots_is_rejected[domingo]` |
| Turno dentro del horario de atención | **N** Instante UTC dentro del tramo que en hora local queda fuera | `utc_instant_inside_slot_but_outside_in_local_time_is_rejected` |
| Turno dentro del horario de atención | **N** Instante UTC fuera del tramo que en hora local queda dentro | `utc_instant_outside_slots_but_inside_in_local_time_returns_ok` |
| Turno dentro del horario de atención | **N** El día de la semana es el local, no el de UTC | `weekday_is_the_local_one_not_the_utc_one` |
| Turno dentro del horario de atención | **N** Turno del martes local que en UTC cae el miércoles | `tuesday_local_evening_that_is_wednesday_in_utc_returns_ok` |
| Turno dentro del horario de atención | **N** Turno que termina a la medianoche local, al fin del tramo | `ending_at_local_midnight_at_slot_end_returns_ok` |
| Turno dentro del horario de atención | **N** Turno que termina a la medianoche local, después del fin del tramo (hallazgo del apply) | `ending_at_local_midnight_after_slot_end_is_rejected` |
| Turno dentro del horario de atención | **N** Tramo de otro profesional | `slot_of_another_professional_does_not_count` |
| Turno dentro del horario de atención | **N** Turno que pasa de un tramo a otro contiguo | `spanning_two_contiguous_slots_returns_ok` |
| Turno dentro del horario de atención | **N** Tramo contenido en otro (hallazgo del apply) | `slot_nested_in_another_does_not_shorten_the_merged_slot` |
| Turno dentro del horario de atención | **N** Mensaje de un turno fuera de los tramos del día | `outside_working_hours_message_lists_the_day_slots` |
| Turno dentro del horario de atención | **N** Mensaje de un turno en un día sin tramos | `outside_working_hours_message_on_a_day_without_slots` |
| Turno dentro del horario de atención | **N** Mensaje con tramos contiguos y un tramo hasta la medianoche | `outside_working_hours_message_merges_slots_and_shows_24` |
| Validez de un conjunto de tramos | **N** Varios tramos válidos el mismo día | `valid_slots_report_nothing[varios-tramos-validos]` |
| Validez de un conjunto de tramos | **N** Tramos con inicio igual o posterior al fin | `start_equal_or_after_end_reports_one_invalid_per_slot`; `invalid_slots_messages_name_the_position_without_references` |
| Validez de un conjunto de tramos | **N** Tramos solapados el mismo día | `overlapping_slots_same_day_report_one_overlap`; `overlap_message_names_positions_and_weekday` |
| Validez de un conjunto de tramos | **N** Los mismos tramos en días distintos | `non_overlapping_slots_report_nothing[dias-distintos]` |
| Validez de un conjunto de tramos | **N** Tramos contiguos | `non_overlapping_slots_report_nothing[tramos-contiguos]` |
| Validez de un conjunto de tramos | **N** Límites del día y valores fuera de rango | `valid_slots_report_nothing[limite-del-dia]`; `out_of_range_slot_reports_exactly_one_invalid[inicio-negativo]`, `[fin-mayor-a-1440]`, `[dia-0]`, `[dia-8]` |
| Validez de un conjunto de tramos | **N** Tramos solapados de profesionales distintos | `non_overlapping_slots_report_nothing[profesionales-distintos]` |
| Validez de un conjunto de tramos | **N** Orden de las violaciones de un conjunto | `set_reports_invalid_first_then_overlaps_by_position` |

Tests extra de mensajes de tramos (D9, no son escenarios): `invalid_slot_message_lists_every_broken_condition` (4 casos), `overlap_message_shows_both_ranges` y `slot_breaking_three_conditions_joins_reasons_with_comma_and_y`; y el caso `dia-8-e-inicio-posterior-al-fin` (un tramo que rompe dos condiciones da una sola violación).

## Desglose de los 232 tests

| Archivo | Qué prueba | Hasta C-04 | C-05 | Total |
|---|---|---|---|---|
| `test_import_guard.py`, `test_domain_dependencies.py` y `test_smoke.py` | Guardia de dependencias y smoke (C-01) | 35 | 0 | 35 |
| `test_model.py` | Modelo, incluido `WorkingHours` con valores inválidos (2 casos) | 8 | 2 | 10 |
| `test_intervals.py` | Intervalos y hora local | 29 | 0 | 29 |
| `test_violations.py` | Códigos de violación (los tres nuevos) | 18 | 3 | 21 |
| `test_validate_new_appointment.py` | Escenarios de la spec | 91 | 25 | 116 |
| `test_working_hours.py` (nuevo) | Validez de un conjunto de tramos | 0 | 21 | 21 |
| **Total** | | **181** | **51** | **232** |

## Desvíos durante el apply

El detalle está en la sección "Desvíos durante el apply" de [design.md](../../openspec/changes/horario-de-atencion/design.md). Los principales:

1. **Punto de control 3.5 (2026-10-26), dos ajustes de la autora:** el mensaje sin tramos termina en ": no atiende los {día en plural}." (spec y D6 actualizados) y se quitó de `test_model.py` el test que solo comprobaba los cuatro valores de `WorkingHours`.
2. **Hallazgos del apply que volvieron a la spec (5.6 y 5.8):** quitar el fin 1440 no hacía fallar ningún escenario, así que se agregó el test del tramo `[1200, 1380)` con el turno 23:30–00:00 → rechazo; y el test del tramo `[600, 700)` contenido en `[540, 780)` fija que la unión toma el mayor fin. La autora decidió que eran comportamiento que la spec no cubría: hoy son los escenarios "Turno que termina a la medianoche local, después del fin del tramo" y "Tramo contenido en otro".
3. **Tests extra (no son escenarios):** mensajes exactos de D9 y tres razones (4.7).
4. **Pasos unidos:** 4.7 y 4.8, y 6.1 a 6.4 en un solo GREEN. Los rojos se vieron.
5. **Triangulaciones que pasaron de entrada** (4.3, 4.5, 4.6, 5.3 a 5.7, 7.1, 7.2): se comprobó con mutaciones temporales que pueden fallar, y se restauró el código.

## Otras verificaciones

- **El dominio sigue siendo puro.** `test_domain_package_real_directory_has_no_forbidden_imports` pasa sin cambiar la allowlist. En `backend/app/domain` no hay `datetime.now`, `utcnow`, `time.time`, `uuid1`, `Any`, `os.environ`, `getenv` ni la zona escrita en el código. Los únicos `raise` son los `ValueError` de errores de programación que ya existían (instante sin zona, `start >= end`, `Rejected` vacío, ids de referencias que no coinciden); `rules/working_hours.py` no lanza nada. `uuid4()` aparece solo en un docstring de `model.py` que dice que el dominio no lo llama.
- **La zona se recibe por parámetro.** `ScheduleContext(tz, working_hours)` no tiene valores por defecto; la zona solo aparece en los tests.
- **Las reglas de negocio son violaciones, no excepciones.** `OUTSIDE_WORKING_HOURS`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` se devuelven como resultado.
- **El ejemplo de `backend/README.md` funciona.** Se corrió una vez en el entorno virtual: imprime `2026-10-20 13:30:00+00:00`.
- **No se hizo ningún commit.**
