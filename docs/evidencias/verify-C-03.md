# Verify de C-03 validar-duracion-y-referencias

OPSX no tiene un comando propio de verify, así que la verificación se hizo a mano, como indica la consigna.

## Cómo se verificó

- Fecha: 2026-10-22, antes del archive.
- Quién: Amanda Pagano.
- Comandos, desde `backend/` con el entorno virtual activo:
  - `pytest -v`
  - `mypy`
- Salidas completas: [pytest-C-03.txt](pytest-C-03.txt) y [mypy-C-03.txt](mypy-C-03.txt)

## Resultado

- pytest: pasaron los 149 tests (0,89 s). C-02 terminó con 107 tests y C-03 agregó 42 (ver el desglose más abajo).
- mypy en modo estricto: "Success: no issues found in 21 source files". Hay un archivo más que en C-02: el nuevo `rules/references.py`.
- `openspec validate validar-duracion-y-referencias --strict`: "Change 'validar-duracion-y-referencias' is valid".
- No hubo tests en rojo ni errores de tipos.

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Todas las referencias existen y están activas | Feliz | `test_validate_new_appointment_all_references_existing_and_active_returns_ok` |
| Referencia inexistente | Error de negocio | `test_validate_new_appointment_unknown_reference_reports_matching_kind[paciente]`, `[profesional]`, `[sillon]` y `[prestacion]` |
| Duración máxima válida (480 minutos) | Borde | `test_validate_new_appointment_valid_duration_boundaries_return_ok[maxima]` |
| Duración que rompe dos condiciones (487 minutos: una sola violación) | Borde | `test_validate_new_appointment_duration_breaking_two_conditions_gives_one_violation` |

Los 29 escenarios del delta de la spec `appointment-scheduling` tienen al menos un test cada uno.

## Los 29 escenarios del delta y su test

En el orden de [la delta spec](../../openspec/changes/validar-duracion-y-referencias/specs/appointment-scheduling/spec.md). Todos los tests están en `backend/tests/domain/test_validate_new_appointment.py` y llevan el prefijo `test_validate_new_appointment_`, que se omite en la tabla. En los parametrizados, el id del caso va entre corchetes, como lo muestra `pytest -v`. Los escenarios de C-02 que este change no toca siguen cubiertos por los tests listados en [verify-C-02.md](verify-C-02.md).

| Requisito | Escenario de la spec | Test |
|---|---|---|
| Alta de un turno válido | Turno válido con profesional y sillón libres | `free_professional_and_chair_returns_ok_with_reserved_appointment` |
| Alta de un turno válido | Turno válido con otros turnos que no chocan | `without_conflict_returns_ok[otros-turnos-que-no-chocan]` |
| Validez de la duración | Duración explícita de cero minutos | `explicit_zero_duration_is_rejected_as_invalid_duration` |
| Validez de la duración | Duración explícita negativa | `non_positive_effective_duration_is_rejected[30--15]` |
| Validez de la duración | Duración por defecto de la prestación no positiva | `non_positive_effective_duration_is_rejected[0-None]`; `non_positive_effective_duration_is_rejected[-30-None]` |
| Validez de la duración | Duración que no es múltiplo de 5 | `duration_not_multiple_of_five_is_invalid_duration[7]`; `duration_not_multiple_of_five_is_invalid_duration[32]` |
| Validez de la duración | Duración mayor que el máximo | `duration_above_maximum_is_invalid_duration` |
| Validez de la duración | Duración que rompe dos condiciones | `duration_breaking_two_conditions_gives_one_violation` |
| Validez de la duración | Duración máxima válida | `valid_duration_boundaries_return_ok[maxima]` |
| Validez de la duración | Duración mínima válida | `valid_duration_boundaries_return_ok[minima]` |
| Validez de la duración | Duración por defecto de la prestación que no es múltiplo de 5 | `default_duration_not_multiple_of_five_is_rejected` |
| Validez de la duración | Duración explícita válida que reemplaza una por defecto inválida | `valid_duration_boundaries_return_ok[explicita-reemplaza-defecto-invalido]` |
| Validez de la duración | Prestación inexistente sin duración explícita | `unknown_service_without_explicit_duration_skips_duration` |
| Validez de la duración | Prestación inexistente con duración explícita inválida | `service_problem_and_invalid_duration_are_reported_in_order[prestacion-inexistente-con-explicita-invalida]` |
| Validez de la duración | Duración inválida en un horario ocupado | `invalid_duration_in_busy_slot_reports_only_duration` |
| Todas las violaciones, en orden estable | Varios conflictos de ambos tipos | `many_conflicts_are_ordered_professional_first_by_start` |
| Todas las violaciones, en orden estable | Orden independiente del orden de la lista recibida | `violation_order_ignores_input_list_order[d-c-b]`; `violation_order_ignores_input_list_order[c-d-b]` |
| Todas las violaciones, en orden estable | Varias referencias que fallan a la vez | `several_failing_references_are_reported_in_fixed_order` |
| Todas las violaciones, en orden estable | Referencia y duración inválidas a la vez | `invalid_reference_and_duration_are_reported_together` |
| Todas las violaciones, en orden estable | Prestación inactiva con duración por defecto inválida | `service_problem_and_invalid_duration_are_reported_in_order[prestacion-inactiva-con-defecto-invalido]` |
| Todas las violaciones, en orden estable | Violación de validez en un horario ocupado | `reference_violation_in_busy_slot_reports_no_overlap` |
| Contenido de cada violación | Mensajes de las violaciones de solapamiento | `overlap_messages_name_resource_and_conflicting_id` |
| Contenido de cada violación | Mensaje de duración inválida | `invalid_duration_message_mentions_received_value` |
| Contenido de cada violación | Mensaje de duración que rompe dos condiciones | `duration_breaking_two_conditions_message_names_all_reasons` |
| Contenido de cada violación | Tipo de referencia en las violaciones de referencias | `reference_violation_has_kind_id_in_message_and_no_conflict[sillon-inexistente]`; `reference_violation_has_kind_id_in_message_and_no_conflict[profesional-inactivo]` |
| Contenido de cada violación | Violaciones sin tipo de referencia | `non_reference_violations_have_no_reference_kind[solapamientos]`; `non_reference_violations_have_no_reference_kind[duracion-invalida]` |
| Referencias existentes y activas | Referencia inexistente | `unknown_reference_reports_matching_kind[paciente]`, `[profesional]`, `[sillon]` y `[prestacion]`; `unknown_professional_is_rejected_as_unknown_reference` |
| Referencias existentes y activas | Referencia inactiva | `inactive_reference_reports_matching_kind[profesional]`, `[sillon]` y `[prestacion]` |
| Referencias existentes y activas | Todas las referencias existen y están activas | `all_references_existing_and_active_returns_ok` |

La verificación de ids de las referencias (design D9) no es un escenario de la spec, porque es un error de programación y no una regla de negocio. La cubren `reference_with_other_id_raises_value_error_naming_field[paciente]`, `[profesional]`, `[sillon]` y `[prestacion]`, y `all_references_none_is_not_a_value_error`.

## Desglose de los 149 tests

| Archivo | Qué prueba | C-02 | C-03 | Total |
|---|---|---|---|---|
| `test_import_guard.py`, `test_domain_dependencies.py` y `test_smoke.py` | Guardia de dependencias y smoke (C-01) | 35 | 0 | 35 |
| `test_model.py` | Modelo | 8 | 0 | 8 |
| `test_intervals.py` | Intervalos | 18 | 0 | 18 |
| `test_violations.py` | Códigos de violación, `ReferenceKind` y `Violation.reference_kind` | 7 | 9 | 16 |
| `test_validate_new_appointment.py` | Escenarios de la spec y verificación de ids | 39 | 33 | 72 |
| **Total** | | **107** | **42** | **149** |

`test_model.py` no suma tests: en la tarea 3.3 solo se agregó `service_id` a una construcción de `NewAppointmentRequest` (desvío 2).

## Desvíos durante el apply

El detalle está en la sección "Desvíos durante el apply" de [design.md](../../openspec/changes/validar-duracion-y-referencias/design.md).

1. **Se cambió una aserción de C-02.** El test del mensaje de -15 comparaba el texto exacto, y el formato de D5 lo cambia. La spec solo pide que el mensaje mencione el valor recibido. La autora lo aprobó en el punto de control 3.4.
2. **Se tocó `test_model.py`, que la tarea 3.3 no nombraba.** Se sumó `service_id` a una construcción, sin cambiar ninguna aserción.
3. **485 se corrigió por 487.** El explore daba 485 como ejemplo de una duración que rompe dos condiciones, pero 485 es múltiplo de 5 (5 × 97). Lo detectó el test de la tarea 6.5. Se corrigió en la spec, el design, el proposal, tasks y con una nota en [explore-C-03.md](explore-C-03.md).
4. **Tarea 4.3.** El test usa `duration_min=0` en vez de 30, para no depender de la regla de referencias, que todavía no existía. Pasó en verde de entrada.
5. **Tareas 6.4 y 6.5.** Pasaron en verde de entrada, porque `check_duration` ya tenía la lógica desde las tareas 6.2 y 6.3.
6. **Grupo 7 sin RED estricto.** Solo la tarea 7.1 se vio en rojo. En la 7.2 se armaron de una vez los dos grupos de violaciones, en lugar del mínimo que pedía el test de la 7.1. Por eso las tareas 7.3 a 7.6 pasaron de entrada. El comportamiento coincide con la spec y cada escenario tiene su test, pero en este grupo el ciclo RED → GREEN no fue estricto. La 7.3 sí tiene un rojo previo: su test se escribió en la tarea 5.3 y falló por la rama provisoria.
7. **Tarea 5.6.** El test de horario ocupado pasó de entrada por el corte del grupo 1. Para verlo en rojo se quitó el corte un momento: fallaron 13 tests y después se restauró.

## Otras verificaciones

- **El dominio sigue siendo puro.** El test `test_domain_package_real_directory_has_no_forbidden_imports` comprueba que `backend/app/domain`, incluido el nuevo `rules/references.py`, no importa FastAPI, SQLAlchemy, Redis, Pydantic ni módulos de archivos o red.
- **No quedó código provisorio.** Un `grep` de `NotImplementedError` en `backend/app/domain` no da resultados. La rama temporal del punto de control se reemplazó por la regla de D3.
- **Las reglas de negocio son violaciones, no excepciones.** Los únicos `raise` del dominio son `ValueError` por errores de programación: un instante sin zona horaria, `start_at >= end_at`, un `Rejected` vacío o ids de referencias que no coinciden (D9).
- **El ejemplo de `backend/README.md` funciona.** Se actualizó a la firma nueva y se ejecutó una vez en el entorno virtual: imprime `2026-10-20 13:30:00+00:00`.
