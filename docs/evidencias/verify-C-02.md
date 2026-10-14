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

- pytest: 107 tests pasaron (0,96 s en la corrida del 2026-10-12). La suite completa tiene 107 tests y no 39 (los de los escenarios de la spec, en `test_validate_new_appointment.py`) porque también incluye los de C-01 (guardia de dependencias y smoke: 35 tests, 3 de ellos casos de `uuid` que agregó C-02) y los unitarios de modelo (8), intervalos (18) y violaciones (7).
- mypy en modo estricto: "Success: no issues found in 20 source files".
- No hubo ningún test en rojo ni errores de tipos, así que el change se archivó el 2026-10-08 (commit `d51264a`).

## Escenarios obligatorios de la consigna y su test

| Escenario de la spec | Tipo | Test |
|---|---|---|
| Turno válido con profesional y sillón libres | Feliz | `test_validate_new_appointment_free_professional_and_chair_returns_ok_with_reserved_appointment` |
| Solapamiento con un turno del mismo profesional | Error de negocio | `test_validate_new_appointment_same_professional_overlap_is_rejected_with_conflicting_id` |
| Turno que empieza exactamente cuando termina otro | Borde | `test_validate_new_appointment_without_conflict_returns_ok[empieza-cuando-termina-otro]` |

Los 31 escenarios de la spec `appointment-scheduling` tienen al menos un test cada uno.

## Los 31 escenarios de la spec y su test

En el orden de [openspec/specs/appointment-scheduling/spec.md](../../openspec/specs/appointment-scheduling/spec.md). Los tests están en `backend/tests/domain/test_validate_new_appointment.py`, salvo los marcados con `test_model.py`. En los parametrizados, el id del caso va entre corchetes, como lo muestra `pytest -v`.

| Escenario de la spec | Test |
|---|---|
| Turno válido con profesional y sillón libres | `test_validate_new_appointment_free_professional_and_chair_returns_ok_with_reserved_appointment` |
| Turno válido con otros turnos que no chocan | `test_validate_new_appointment_without_conflict_returns_ok[otros-turnos-que-no-chocan]` |
| Duración por defecto de la prestación | `test_validate_new_appointment_effective_duration_sets_end[45-None-expected_end0]` |
| Duración explícita que reemplaza la de la prestación | `test_validate_new_appointment_explicit_duration_replaces_service_default`; `test_validate_new_appointment_effective_duration_sets_end[45-20-expected_end1]` |
| Duración explícita válida con una prestación de duración no positiva | `test_validate_new_appointment_effective_duration_sets_end[0-30-expected_end2]` |
| Turno que empieza exactamente cuando termina otro | `test_validate_new_appointment_without_conflict_returns_ok[empieza-cuando-termina-otro]` |
| Turno que termina exactamente cuando empieza otro | `test_validate_new_appointment_without_conflict_returns_ok[termina-cuando-empieza-otro]` |
| Solapamiento con un turno del mismo profesional | `test_validate_new_appointment_same_professional_overlap_is_rejected_with_conflicting_id` |
| Fin del turno nuevo dentro de un turno existente | `test_validate_new_appointment_professional_overlap_geometry_is_rejected[fin-dentro-de-existente]` |
| Turno nuevo que contiene por completo a uno existente | `test_validate_new_appointment_professional_overlap_geometry_is_rejected[contiene-al-existente]` |
| Turno nuevo contenido dentro de uno existente | `test_validate_new_appointment_professional_overlap_geometry_is_rejected[contenido-en-existente]` |
| Mismo intervalo exacto | `test_validate_new_appointment_professional_overlap_geometry_is_rejected[mismo-intervalo]` |
| Otro profesional a la misma hora y en otro sillón | `test_validate_new_appointment_without_conflict_returns_ok[otro-profesional-y-otro-sillon]` |
| Mismo sillón con otro profesional | `test_validate_new_appointment_same_chair_other_professional_is_chair_overlap` |
| Mismo profesional y mismo sillón solapados | `test_validate_new_appointment_same_professional_and_chair_reports_both_in_order` |
| Otro sillón a la misma hora | `test_validate_new_appointment_other_chair_same_time_is_ok` |
| Turno cancelado no bloquea | `test_validate_new_appointment_cancelled_appointment_does_not_block` (turno cancelado de P1 en S2, según la tarea 8.4); `test_validate_new_appointment_irrelevant_appointments_in_list_are_ignored` (turno cancelado de P1 en S1, como en la spec) |
| Turno ausente no bloquea | `test_validate_new_appointment_no_show_appointment_does_not_block_chair`; `test_validate_new_appointment_only_occupying_statuses_block_professional[ausente]` |
| Turnos confirmados y atendidos sí bloquean | `test_validate_new_appointment_confirmed_and_attended_block_professional_and_chair[AppointmentStatus.CONFIRMED]`; `test_validate_new_appointment_confirmed_and_attended_block_professional_and_chair[AppointmentStatus.ATTENDED]` |
| Lista con turnos de otros profesionales y otros sillones | `test_validate_new_appointment_irrelevant_appointments_in_list_are_ignored` |
| Varios conflictos de ambos tipos | `test_validate_new_appointment_many_conflicts_are_ordered_professional_first_by_start` |
| Orden independiente del orden de la lista recibida | `test_validate_new_appointment_violation_order_ignores_input_list_order[d-c-b]`; `test_validate_new_appointment_violation_order_ignores_input_list_order[c-d-b]` |
| Duración explícita de cero minutos | `test_validate_new_appointment_explicit_zero_duration_is_rejected_as_invalid_duration` |
| Duración explícita negativa | `test_validate_new_appointment_non_positive_effective_duration_is_rejected[30--15]` |
| Duración por defecto de la prestación no positiva | `test_validate_new_appointment_non_positive_effective_duration_is_rejected[0-None]`; `test_validate_new_appointment_non_positive_effective_duration_is_rejected[-30-None]` |
| Duración inválida en un horario ocupado | `test_validate_new_appointment_invalid_duration_in_busy_slot_reports_only_duration` |
| Mensajes de las violaciones de solapamiento | `test_validate_new_appointment_overlap_messages_name_resource_and_conflicting_id` |
| Mensaje de duración inválida | `test_validate_new_appointment_invalid_duration_message_mentions_received_value` |
| Inicio sin zona horaria | `test_model.py`: `test_new_appointment_request_start_without_timezone_raises_value_error`; `test_appointment_instant_without_timezone_raises_value_error[start_at0-end_at0]` (inicio sin zona); `test_appointment_instant_without_timezone_raises_value_error[start_at1-end_at1]` (fin sin zona) |
| Inicio en hora de Buenos Aires | `test_validate_new_appointment_start_in_buenos_aires_time_returns_utc_appointment` |
| Turno existente en otra zona que choca | `test_validate_new_appointment_existing_appointment_in_other_timezone_still_conflicts` |

## Otras verificaciones

- **El README funciona en un clon limpio** (2026-10-08): se clonó el repositorio en una carpeta nueva y se siguieron solo los comandos del README. La instalación terminó bien y pasaron los 107 tests y mypy.
- **El dominio sigue siendo puro**: el test `test_domain_package_real_directory_has_no_forbidden_imports` comprueba que `backend/app/domain` no importa FastAPI, SQLAlchemy, Redis, Pydantic ni módulos de archivos o red.
- **No se suben archivos generados**: se comprobó con `git check-ignore` que `.venv`, `.pytest_cache` y `.mypy_cache` quedan fuera del repositorio.
- **Otra máquina** (2026-10-09): el asistente de IA clonó el repositorio en Linux con Python 3.13, siguió el README y obtuvo los mismos 107 tests en verde y mypy sin errores.