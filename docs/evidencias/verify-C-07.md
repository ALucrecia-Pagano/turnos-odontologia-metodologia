# Verify de C-07 no-turnos-en-el-pasado

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fecha: 2026-10-29, antes del archive.
- Quién: Amanda Pagano (el apply lo ejecutó un agente; la autora aprobó el punto de control 5.3 el 2026-10-29, con condiciones que se cumplieron).
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy --strict app tests`
- Desde la raíz: `openspec validate no-turnos-en-el-pasado --strict`
- Salidas completas: [pytest-C-07.txt](pytest-C-07.txt) y [mypy-C-07.txt](mypy-C-07.txt)

## Resultado

- pytest: pasaron los 330 tests (ver pytest-C-07.txt). C-06 cerró con 273; este change suma 57.
- mypy en modo estricto: "Success: no issues found in 31 source files". Hay tres archivos más que en C-06: `rules/past.py`, `tests/domain/test_past.py` y `tests/domain/test_clock_guard.py`.
- `openspec validate no-turnos-en-el-pasado --strict`: "Change 'no-turnos-en-el-pasado' is valid".
- No hubo tests en rojo ni errores de tipos al cerrar.

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Inicio igual al momento actual (10:00 local, 13:00 UTC; `Ok` de 13:00 a 13:30 UTC) | Feliz | `test_validate_new_appointment_start_not_before_now_returns_ok[inicio-igual-al-momento-actual]` |
| Inicio cinco minutos antes del momento actual (09:55 local con `now` 10:00 local) | Error de negocio | `test_validate_new_appointment_start_five_minutes_before_now_reports_in_the_past` |
| Momento actual con segundos e inicio en el mismo minuto (`now` 10:00:30, inicio 10:00) | Borde | `test_validate_new_appointment_start_before_now_is_rejected_as_in_the_past[segundos-mismo-minuto]` |

## Los 44 escenarios de `appointment-scheduling` y su test

Tests de `test_validate_new_appointment.py` con el prefijo `test_validate_new_appointment_` omitido, salvo que se indique otro archivo. En los parametrizados, el id va entre corchetes. Marcados con **N** los 20 escenarios nuevos; los otros 24 ya existían en los requisitos modificados y siguen cubiertos por los mismos tests de C-02 a C-06 (no se cambió ninguna llamada ni aserción; solo `CTX`, `_ctx` y `_ctx_blocks` suman `now=EARLY_NOW`).

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
| Todas las violaciones, en orden estable | Fuera de horario, bloqueado y solapado a la vez | `outside_hours_blocked_and_overlapping_reports_all_in_order` |
| Todas las violaciones, en orden estable | Duración inválida dentro de un bloqueo | `invalid_duration_inside_a_block_reports_only_duration` |
| Todas las violaciones, en orden estable | **N** Inicio fuera de la grilla y en el pasado | `off_grid_start_in_the_past_reports_start_then_past` |
| Todas las violaciones, en orden estable | **N** Turno en el pasado que cruza la medianoche | `past_crossing_midnight_reports_midnight_then_past` |
| Todas las violaciones, en orden estable | **N** Duración inválida en el pasado | `invalid_duration_in_the_past_still_reports_past` |
| Todas las violaciones, en orden estable | **N** Prestación inexistente en el pasado | `unknown_service_in_the_past_still_reports_past` |
| Todas las violaciones, en orden estable | **N** Turno en el pasado en un horario ocupado | `past_in_an_occupied_slot_reports_only_past` |
| Todas las violaciones, en orden estable | **N** Turno en el pasado fuera del horario de atención | `past_outside_working_hours_reports_only_past` |
| Contenido de cada violación | Mensajes de las violaciones de solapamiento | `overlap_messages_name_resource_and_conflicting_id` |
| Contenido de cada violación | Mensaje de duración inválida | `invalid_duration_message_mentions_received_value` |
| Contenido de cada violación | Mensaje de duración que rompe dos condiciones | `duration_breaking_two_conditions_message_names_all_reasons` |
| Contenido de cada violación | Tipo de referencia en las violaciones de referencias | `reference_violation_has_kind_id_in_message_and_no_conflict` |
| Contenido de cada violación | Violaciones sin tipo de referencia | `non_reference_violations_have_no_reference_kind` |
| Contenido de cada violación | Mensaje de inicio fuera de la grilla | `start_off_grid_message_names_time_and_reason` |
| Contenido de cada violación | Mensaje de cruce de medianoche | `crosses_midnight_message_shows_local_start_and_end` |
| Turno que no empieza en el pasado | **N** Inicio cinco minutos antes del momento actual | `start_five_minutes_before_now_reports_in_the_past`; `test_past.py::test_check_not_in_the_past_start_five_minutes_before_now_reports_in_the_past` |
| Turno que no empieza en el pasado | **N** Inicio igual al momento actual | `start_not_before_now_returns_ok[inicio-igual-al-momento-actual]`; `test_past.py::...start_equal_to_now_reports_nothing` |
| Turno que no empieza en el pasado | **N** Inicio posterior al momento actual | `start_not_before_now_returns_ok[inicio-posterior]`; `test_past.py::...compares_instants_strictly_without_truncating[inicio-posterior]` |
| Turno que no empieza en el pasado | **N** Momento actual con segundos e inicio en el mismo minuto | `start_before_now_is_rejected_as_in_the_past[segundos-mismo-minuto]`; `test_past.py::...[segundos-mismo-minuto]` |
| Turno que no empieza en el pasado | **N** Momento actual con segundos e inicio en el paso siguiente de la grilla | `start_not_before_now_returns_ok[segundos-paso-siguiente]`; `test_past.py::...[segundos-paso-siguiente]` |
| Turno que no empieza en el pasado | **N** Momento actual un microsegundo después del inicio | `start_before_now_is_rejected_as_in_the_past[microsegundo-despues]`; `test_past.py::...[microsegundo]` |
| Turno que no empieza en el pasado | **N** Momento actual antes de la medianoche local e inicio en el día siguiente | `start_not_before_now_returns_ok[antes-de-medianoche-inicio-dia-siguiente]` |
| Turno que no empieza en el pasado | **N** Inicio en el pasado del mismo día local, que en UTC es otro día | `start_before_now_is_rejected_as_in_the_past[mismo-dia-local-otro-dia-utc]` |
| Mensaje de un turno en el pasado | **N** Mensaje de un turno en el pasado | `in_the_past_message_is_exact_and_has_no_conflict_ids[cinco-minutos-antes]`; `test_past.py::...message_uses_local_date_and_now_with_seconds[cinco-minutos-antes]` |
| Mensaje de un turno en el pasado | **N** Mensaje con el momento actual en el mismo minuto que el inicio | `in_the_past_message_is_exact_and_has_no_conflict_ids[mismo-minuto]`; `test_past.py::...[mismo-minuto]` |
| Mensaje de un turno en el pasado | **N** Mensaje con la fecha local y no la de UTC | `in_the_past_message_is_exact_and_has_no_conflict_ids[fecha-local-no-utc]`; `test_past.py::...[fecha-local-no-utc]` |
| Momento actual inyectado en el contexto | **N** Momento actual en hora de Buenos Aires | `test_model.py::test_schedule_context_now_with_zone_is_normalized_to_utc[buenos-aires]` |
| Momento actual inyectado en el contexto | **N** Momento actual en otra zona | `test_model.py::test_schedule_context_now_with_zone_is_normalized_to_utc[mas-uno]` |
| Momento actual inyectado en el contexto | **N** Momento actual sin zona horaria | `test_model.py::test_schedule_context_now_without_timezone_raises_value_error` |

## Los 16 escenarios de `domain-dependency-guard` y su test

Tests de `test_clock_guard.py` con el prefijo `test_find_global_clock_calls_` omitido, salvo que se indique otro nombre.

| Escenario de la spec | Test |
|---|---|
| Llamada a datetime.now | `datetime_now_reports_one_access` |
| Llamadas a datetime.utcnow y datetime.today | `clock_access_reports_expression[utcnow-y-today]` |
| Llamada a date.today | `clock_access_reports_expression[date-today]` |
| Llamada por el módulo datetime | `clock_access_reports_expression[por-el-modulo]` |
| Llamada con alias | `clock_access_reports_expression[con-alias]` |
| Referencia al reloj sin llamarlo | `clock_access_reports_expression[referencia-sin-llamar]` |
| Llamada dentro de una función | `clock_access_reports_expression[dentro-de-una-funcion]` |
| Import con asterisco del módulo datetime | `clock_access_reports_expression[import-con-asterisco]` |
| Momento actual inyectado | `non_clock_access_reports_nothing[context-now]`; `[parametro-now]` |
| Construcción de instantes y duraciones | `non_clock_access_reports_nothing[construccion-de-instantes]` |
| La palabra now en un docstring | `non_clock_access_reports_nothing[now-en-un-docstring]` |
| Reloj del módulo time | `test_find_forbidden_imports_time_module_reports_time[import-time]`; `[from-time-as]` |
| Accesos dinámicos no detectados | `non_clock_access_reports_nothing[getattr-no-detectado]`; `[reasignacion-no-detectada]` |
| Reporte con archivo y línea | `access_in_rules_file_reports_path_and_line`; `test_format_clock_calls_one_access_gives_one_line`; `test_format_clock_calls_two_accesses_give_one_line_each` |
| Varios accesos en orden de línea | `several_accesses_are_ordered_by_line`; `two_accesses_in_order_are_reported_in_order` |
| Dominio real sin reloj global | `test_domain_dependencies.py::test_domain_package_real_directory_has_no_global_clock_calls` |

Los escenarios de C-01 a C-06 que este change no toca siguen cubiertos por [verify-C-02.md](verify-C-02.md) a [verify-C-06.md](verify-C-06.md) (los tests de `test_import_guard.py` no cambiaron: `git diff` vacío).

Tests extra (no son escenarios): en `test_violations.py`, `IN_THE_PAST` en la tabla de valores serializados; en `test_intervals.py`, `format_local_date_time_with_seconds` (cinco casos, entre ellos el día local anterior al de UTC, la truncación de microsegundos y el instante naive).

## Desglose de los 330 tests

| Archivo | Qué prueba | Hasta C-06 | C-07 | Total |
|---|---|---|---|---|
| `test_import_guard.py`, `test_domain_dependencies.py` y `test_smoke.py` | Guardia de dependencias, guardia del reloj sobre el dominio real y smoke | 35 | 1 | 36 |
| `test_clock_guard.py` (nuevo) | Guardia del reloj global | 0 | 21 | 21 |
| `test_model.py` | Modelo, incluido `ScheduleContext.now` | 14 | 3 | 17 |
| `test_intervals.py` | Intervalos y hora local, incluido `format_local_date_time_with_seconds` | 33 | 5 | 38 |
| `test_violations.py` | Códigos de violación, incluido `IN_THE_PAST` | 26 | 1 | 27 |
| `test_validate_new_appointment.py` | Escenarios de la spec | 135 | 17 | 152 |
| `test_past.py` (nuevo) | `check_not_in_the_past` | 0 | 9 | 9 |
| `test_working_hours.py` y `test_blocks.py` | Sin cambios | 30 | 0 | 30 |
| **Total** | | **273** | **57** | **330** |

## Desvíos durante el apply

Los cuatro primeros están en la sección "Desvíos del apply" de [design.md](../../openspec/changes/archive/2026-10-29-no-turnos-en-el-pasado/design.md) (anotados en el punto de control 5.3); del 5 en adelante son de los grupos 6 a 8.

1. **Tarea 4.2 (guardia del reloj) no fue el paso mínimo.** Se implementó de una vez la resolución completa de nombres, sin un paso "Fake It"; varios casos de 4.3 pasaron de entrada. Se compensó con tres mutaciones temporales (sin resolver alias, solo `ast.Call`, filtrar solo por el atributo). La mutación de solo `ast.Call` no quedó limpia: fallaron casi todos los tests por el texto de la expresión, aunque el caso clave falló como se esperaba (`[] == ['datetime.now']`).
2. **Tarea 3.1: el rojo fue un `TypeError`**, no el `ValueError` del `now` naive, porque `ScheduleContext` todavía no aceptaba `now`. La causa era la correcta; el `ValueError` se vio recién en verde.
3. **Grupo 7 reordenado** a pedido de la autora: los escenarios que rechazan por el pasado, los del orden y el corte y los tres de mensaje se escribieron en rojo (7.1) antes de cablear (7.2).
4. **Escenario nuevo en `domain-dependency-guard`**: "Varios accesos en orden de línea" (los tests del orden de D11 no tenían escenario).
5. **7.1: el rojo de los casos 4, 6, 8 y de los tres mensajes fue `assert False` en `isinstance(result, Rejected)`** (hoy devuelve `Ok`), no una comparación de códigos; es la causa correcta (falta `IN_THE_PAST`), pero no se ve el mensaje. Los casos 9 a 14 fallaron comparando la lista de códigos. Para escribir menos tests, los casos 4, 6 y 8 van en una tabla y los tres mensajes en otra; cada caso tiene su id.
6. **6.1 GREEN con un mensaje mínimo** (`"El turno está en el pasado."`) y **6.4 REFACTOR**: los docstrings de `past.py` se escribieron junto con el GREEN de 6.3; en 6.4 solo quedó la fila de `rules/` en el README.
7. **Mutaciones con más fallas que las previstas.** 7.4 (C), la regla al principio del grupo 2, rompió además los casos 9 a 12 (el grupo 1 deja de cortar el pasado), no solo el 13 y el 14. 7.5, `context.tz` como UTC, rompió los tres tests de mensaje, no solo el de la fecha local (también cambian las horas). 7.3 (`<=`) rompió además `test_past.py::...start_equal_to_now_reports_nothing`. Todas se restauraron y la suite volvió a `330 passed`.
8. **7.6: se agregó una sección `Returns:`** al docstring de `_request_validity_violations` en lugar de la frase "C-05 a C-07 suman sus reglas".
9. **No se agregó ningún escenario nuevo a las specs en los grupos 6 a 8**: todos los tests nuevos mapean a un escenario existente.

## Limitaciones conocidas

- **Mensaje de `IN_THE_PAST` con un `now` con microsegundos** (aceptada por la autora el 2026-10-29, design D7 y Risks): con `now` a 13:00:00.000001 UTC e inicio 10:00 local, el rechazo es correcto pero el mensaje dice "10:00" y "10:00:00", porque los microsegundos no se muestran. Un `now` así solo llega por programa, nunca desde el formulario. No se cambió el comportamiento.
- **La guardia del reloj no ve** `getattr(datetime, "now")()` ni reasignaciones como `d = datetime; d.now()`, y un parámetro llamado `datetime` en un archivo que importa la clase da un falso positivo; los bindings son por archivo, no por ámbito (design D4, con tests de lo no detectado).

## Otras verificaciones

- **El dominio sigue siendo puro.** `test_domain_package_real_directory_has_no_forbidden_imports` y `test_domain_package_real_directory_has_no_global_clock_calls` pasan. Búsqueda en `backend/app/domain`: sin `datetime.now`, `utcnow`, `today(`, `time.time`, `uuid1`, `Any`, `os.environ`, `getenv` ni la zona escrita en el código; `uuid4()` solo en un docstring de `model.py`. Los `raise` son los de antes (`ValueError` de programación en `validate.py`, `intervals.py`, `model.py` y `violations.py`); `rules/past.py` no lanza nada.
- **`now` llega solo por `ScheduleContext`**, obligatorio, normalizado a UTC; un `now` naive lanza `ValueError`.
- **Las reglas de negocio son violaciones, no excepciones.** `IN_THE_PAST` se devuelve como resultado.
- **El ejemplo de `backend/README.md` con `now` funciona.** Se corrió en el entorno virtual: imprime `2026-10-20 13:30:00+00:00` (tarea 3.3).
- **No se hizo ningún commit.**
