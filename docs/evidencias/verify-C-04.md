# Verify de C-04 hora-local-y-turno-en-un-dia

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fecha: 2026-10-23, antes del archive.
- Quién: Amanda Pagano (el apply lo ejecutó un agente; la autora aprobó el punto de control 4.4 el 2026-10-23).
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy`
- Desde la raíz: `openspec validate hora-local-y-turno-en-un-dia --strict`
- Salidas completas: [pytest-C-04.txt](pytest-C-04.txt) y [mypy-C-04.txt](mypy-C-04.txt)

## Resultado

- pytest: pasaron los 181 tests (ver pytest-C-04.txt). C-03 terminó con 149 tests y C-04 agregó 32 (ver el desglose más abajo).
- mypy en modo estricto: "Success: no issues found in 24 source files". Hay tres archivos más que en C-03: `rules/grid.py`, `rules/start_time.py` y `rules/same_day.py`.
- `openspec validate hora-local-y-turno-en-un-dia --strict`: "Change 'hora-local-y-turno-en-un-dia' is valid".
- No hubo tests en rojo ni errores de tipos.

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Inicio en la grilla (10:05 hora local) | Feliz | `test_validate_new_appointment_start_on_grid_returns_ok` |
| Turno que cruza la medianoche local (23:30 con 60 minutos) | Error de negocio | `test_validate_new_appointment_crossing_local_midnight_is_rejected_as_crosses_midnight` |
| Turno que termina justo a la medianoche local (23:30–00:00) | Borde | `test_validate_new_appointment_ending_at_or_before_local_midnight_returns_ok[termina-justo-a-la-medianoche]` |
| Inicio fuera de la grilla en un turno que cruza la medianoche (23:33 con 60 minutos) | Borde | `test_validate_new_appointment_off_grid_start_crossing_midnight_reports_start_then_midnight` |

Los 29 escenarios del delta de la spec `appointment-scheduling` tienen al menos un test cada uno.

## Los 29 escenarios del delta y su test

En el orden de [la delta spec](../../openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/specs/appointment-scheduling/spec.md). Todos los tests están en `backend/tests/domain/test_validate_new_appointment.py` y llevan el prefijo `test_validate_new_appointment_`, que se omite en la tabla. En los parametrizados, el id del caso va entre corchetes. Los escenarios de C-02 y C-03 que este change no toca siguen cubiertos por los tests de [verify-C-02.md](verify-C-02.md) y [verify-C-03.md](verify-C-03.md), que siguen en verde.

Nuevos (16), marcados con **N**; el resto ya existía en los requisitos modificados (13). El escenario "Inicio con segundos en un turno que cruza la medianoche por segundos" se agregó durante el apply (hallazgo 8 de los desvíos).

| Requisito | Escenario de la spec | Test |
|---|---|---|
| Alta de un turno válido | Turno válido con profesional y sillón libres | `free_professional_and_chair_returns_ok_with_reserved_appointment`; `all_references_existing_and_active_returns_ok` |
| Alta de un turno válido | Turno válido con otros turnos que no chocan | `without_conflict_returns_ok[otros-turnos-que-no-chocan]` |
| Todas las violaciones, en orden estable | Varios conflictos de ambos tipos | `many_conflicts_are_ordered_professional_first_by_start` |
| Todas las violaciones, en orden estable | Orden independiente del orden de la lista recibida | `violation_order_ignores_input_list_order[d-c-b]`; `violation_order_ignores_input_list_order[c-d-b]` |
| Todas las violaciones, en orden estable | Varias referencias que fallan a la vez | `several_failing_references_are_reported_in_fixed_order` |
| Todas las violaciones, en orden estable | Referencia y duración inválidas a la vez | `invalid_reference_and_duration_are_reported_together` |
| Todas las violaciones, en orden estable | Prestación inactiva con duración por defecto inválida | `service_problem_and_invalid_duration_are_reported_in_order[prestacion-inactiva-con-defecto-invalido]` |
| Todas las violaciones, en orden estable | Violación de validez en un horario ocupado | `reference_violation_in_busy_slot_reports_no_overlap` |
| Todas las violaciones, en orden estable | **N** Referencia, duración e inicio inválidos a la vez | `unknown_reference_invalid_duration_and_invalid_start_are_reported_together` |
| Todas las violaciones, en orden estable | **N** Inicio fuera de la grilla en un turno que cruza la medianoche | `off_grid_start_crossing_midnight_reports_start_then_midnight` |
| Todas las violaciones, en orden estable | **N** Inicio con segundos en un turno que cruza la medianoche por segundos | `off_grid_start_with_seconds_crossing_midnight_by_seconds_reports_both` |
| Todas las violaciones, en orden estable | **N** Inicio fuera de la grilla en un horario ocupado | `start_off_grid_in_busy_slot_reports_only_start` |
| Contenido de cada violación | Mensajes de las violaciones de solapamiento | `overlap_messages_name_resource_and_conflicting_id` |
| Contenido de cada violación | Mensaje de duración inválida | `invalid_duration_message_mentions_received_value` |
| Contenido de cada violación | Mensaje de duración que rompe dos condiciones | `duration_breaking_two_conditions_message_names_all_reasons` |
| Contenido de cada violación | Tipo de referencia en las violaciones de referencias | `reference_violation_has_kind_id_in_message_and_no_conflict[sillon-inexistente]`; `reference_violation_has_kind_id_in_message_and_no_conflict[profesional-inactivo]` |
| Contenido de cada violación | Violaciones sin tipo de referencia | `non_reference_violations_have_no_reference_kind[solapamientos]`; `non_reference_violations_have_no_reference_kind[duracion-invalida]` |
| Contenido de cada violación | **N** Mensaje de inicio fuera de la grilla | `start_off_grid_message_names_time_and_reason` |
| Contenido de cada violación | **N** Mensaje de cruce de medianoche | `crosses_midnight_message_shows_local_start_and_end` |
| Turno dentro de un solo día local | **N** Turno que cruza la medianoche local | `crossing_local_midnight_is_rejected_as_crosses_midnight` |
| Turno dentro de un solo día local | **N** Turno que termina antes de la medianoche local | `ending_at_or_before_local_midnight_returns_ok[termina-antes-de-la-medianoche]` |
| Turno dentro de un solo día local | **N** Turno que termina justo a la medianoche local | `ending_at_or_before_local_midnight_returns_ok[termina-justo-a-la-medianoche]` |
| Turno dentro de un solo día local | **N** Duración inválida en un turno que cruzaría la medianoche | `invalid_duration_crossing_midnight_reports_only_duration` |
| Inicio en la grilla de 5 minutos | **N** Inicio con minutos fuera de la grilla | `start_minutes_off_grid_is_rejected_as_invalid_start_time` |
| Inicio en la grilla de 5 minutos | **N** Inicio en la grilla | `start_on_grid_returns_ok` |
| Inicio en la grilla de 5 minutos | **N** Inicio con segundos o microsegundos | `start_with_seconds_or_microseconds_is_rejected_with_time_shown[segundos]` y `[microsegundos]`; `start_with_seconds_message_names_only_seconds_reason[segundos]` y `[microsegundos]` |
| Inicio en la grilla de 5 minutos | **N** Inicio que rompe dos condiciones | `start_breaking_two_conditions_gives_one_violation_with_exact_message` |
| Hora local en la zona horaria recibida | **N** Instante UTC que en hora local cae en otro día | `utc_instant_on_previous_local_day_is_rejected_as_crosses_midnight` |
| Hora local en la zona horaria recibida | **N** Turno que cruza la medianoche UTC pero no la local | `crossing_utc_midnight_but_not_local_midnight_returns_ok` |

## Desglose de los 181 tests

| Archivo | Qué prueba | Hasta C-03 | C-04 | Total |
|---|---|---|---|---|
| `test_import_guard.py`, `test_domain_dependencies.py` y `test_smoke.py` | Guardia de dependencias y smoke (C-01) | 35 | 0 | 35 |
| `test_model.py` | Modelo | 8 | 0 | 8 |
| `test_intervals.py` | Intervalos y hora local (`local_day_and_minutes`, `format_local_time`) | 18 | 11 | 29 |
| `test_violations.py` | Códigos de violación (los dos nuevos), `ReferenceKind` y `Violation.reference_kind` | 16 | 2 | 18 |
| `test_validate_new_appointment.py` | Escenarios de la spec y verificación de ids | 72 | 19 | 91 |
| **Total** | | **149** | **32** | **181** |

La adaptación de las 28 llamadas existentes de `test_validate_new_appointment.py` solo suma `CTX` al final: no se cambió ninguna aserción.

## Desvíos durante el apply

El detalle está en la sección "Desvíos durante el apply" de [design.md](../../openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/design.md). Los principales:

1. **Adición aprobada en 4.4:** `format_local_time` lanza `ValueError` con un instante *naive*, como `local_day_and_minutes` (helper privado `_to_local`). No estaba en las tareas originales.
2. **Redacción de `INVALID_START_TIME` aprobada en 4.4** ("... (se recibió {hora}, hora local): ..." con las razones "debe caer en un minuto múltiplo de 5" y "no puede tener segundos ni fracciones de segundo").
3. **Tareas 3.5 y 3.6** se hicieron en un solo paso (el rojo de 3.5 sí se vio).
4. **Varias triangulaciones pasaron de entrada** (3.3, 6.5, 7.3 a 7.6). Para comprobar que los tests pueden fallar se rompió el código a propósito (corte del grupo 1, `>=` por `>`, zona UTC en el test, condición de la duración) y se restauró.
5. **Tarea 7.4:** se comprobó cambiando temporalmente la zona del test a UTC: los dos escenarios de hora local fallan (y cinco tests más que dependen de la zona). Se restauró Buenos Aires.
6. **Tarea 7.8:** `_request_validity_violations` recibe `duration` y `end_at` para calcular el fin una sola vez.
7. **`CHANGES.md` §[C-04] no se editó:** no contradice lo implementado, aunque no nombra `rules/grid.py` ni `rules/start_time.py`.

8. **Hallazgo del apply que volvió a la spec (tareas 10.1 a 10.5, aprobado por la autora el 2026-10-23).** `check_same_local_day` truncaba el fin a minutos, así que 23:30:30 con 30 minutos (fin 00:00:30) no daba `CROSSES_MIDNIGHT`. Se agregó el escenario a la spec, se corrigió el texto del requisito y D9, y la regla compara ahora el instante completo del fin con las 00:00 locales del día siguiente. `MINUTES_PER_DAY` quedó sin uso y por decisión de la autora (2026-10-23) se eliminó de `intervals.py`: C-05 la agrega con su propio test si la necesita. `local_day_and_minutes` se conserva, porque `check_same_local_day` la usa.

## Otras verificaciones

- **El dominio sigue siendo puro.** `test_domain_package_real_directory_has_no_forbidden_imports` pasa sin cambiar la allowlist. En `backend/app/domain` no hay `datetime.now`, `utcnow`, `time.time`, `uuid1`, `Any`, `os.environ`, `getenv` ni la zona escrita en el código. Los únicos `raise` son `ValueError` por errores de programación (instante sin zona, `start >= end`, `Rejected` vacío, ids de referencias que no coinciden). La palabra `uuid4()` aparece solo en un docstring de `model.py` que dice que el dominio no lo llama.
- **La zona se recibe por parámetro.** `ScheduleContext(tz)` no tiene valor por defecto; la zona solo aparece en los tests.
- **Las reglas de negocio son violaciones, no excepciones.** `CROSSES_MIDNIGHT` e `INVALID_START_TIME` se devuelven en `Rejected`.
- **El ejemplo de `backend/README.md` funciona.** Se actualizó con `ScheduleContext` y la firma nueva, y se ejecutó una vez en el entorno virtual: imprime `2026-10-20 13:30:00+00:00`.
- **No se hizo ningún commit.**
