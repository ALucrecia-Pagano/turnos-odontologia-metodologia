# Verificación C-11 — Reprogramar turno

## Resultado

- Artefactos archivados: [design.md](../../openspec/changes/archive/2026-11-03-reprogramar-turno/design.md) y [tasks.md](../../openspec/changes/archive/2026-11-03-reprogramar-turno/tasks.md).
- Apply iniciado por Kiro, interrumpido por límite de uso, y retomado por Copilot.
- Baseline real: `619 passed, 8 deselected`; `mypy --strict`: Success en 62 archivos.
- Resultado final: `645 passed, 8 deselected`; `mypy --strict`: Success en 62 archivos.
- `openspec validate reprogramar-turno --strict`: `Change 'reprogramar-turno' is valid`.
- `git diff --check`: sin salida y código 0.

## Trazabilidad de escenarios

Los 31 escenarios del delta tienen cobertura automatizada:

| Escenario | Test |
|---|---|
| Reprogramar válido conserva id y vuelve a reservado | `test_reschedule_valid_keeps_id_and_returns_reserved` |
| Desde confirmado vuelve a reservado | `test_reschedule_from_confirmed_returns_reserved` |
| No choca consigo mismo en su mismo intervalo | `test_reschedule_excludes_itself_from_overlaps` |
| No choca consigo mismo al solapar su intervalo viejo | `test_reschedule_excludes_itself_from_overlaps` |
| Cambia solo el profesional y no choca por sillón consigo mismo | `test_reschedule_can_change_only_professional_without_self_chair_conflict` |
| Conserva la duración real si no se indica | `test_reschedule_keeps_real_duration_when_omitted` |
| Cambia la duración indicada | `test_reschedule_uses_requested_duration` |
| El original no cambia al reprogramar | `test_reschedule_valid_original_unchanged` |
| El dominio excluye al propio aunque el llamador lo incluya | `test_reschedule_excludes_itself_from_overlaps` |
| Desde cada estado terminal | `test_reschedule_terminal_status_returns_dedicated_violation` |
| El turno terminal no se altera | `test_reschedule_terminal_status_does_not_change_original` |
| Odontólogo propio y ajeno no reprograman | `test_dentist_cannot_reschedule_any_appointment` |
| Recepción y administración reprograman | `test_reception_and_administration_can_reschedule` |
| El permiso corta y oculta el resto | `test_reschedule_permission_precedes_terminal_status_and_slot` |
| El estado corta y oculta los conflictos del slot | `test_reschedule_status_precedes_slot_conflicts` |
| Choca con otro turno del mismo profesional | `test_reschedule_rejects_professional_overlap_with_existing_appointment` |
| Choca con otro turno del mismo sillón | `test_reschedule_rejects_chair_overlap_with_existing_appointment` |
| Fuera de horario | `test_reschedule_rejects_outside_working_hours` |
| Bloqueado | `test_reschedule_rejects_blocked_slot` |
| Al pasado con verbo de reprogramar | `test_reschedule_rejects_past_with_reprogramar_message` |
| Profesional nuevo inexistente | `test_reschedule_rejects_unknown_new_professional` |
| Prestación inactiva al reprogramar | `test_reschedule_rejects_inactive_service_from_original_references` |
| now naive en el contexto | `test_reschedule_rejects_naive_context_now` |
| El original no cambia ante un rechazo de slot | `test_reschedule_rejection_does_not_change_original` |
| El alta conserva el mensaje del pasado | `test_validate_new_appointment_alta_default_past_verb_still_says_dar_turnos` |
| Sin códigos nuevos ni cambios de ocupación | `test_violation_code_value_is_stable_api_code` y `test_validate_new_appointment_only_occupying_statuses_block_professional` |
| Mensaje de un turno en el pasado | `test_validate_new_appointment_in_the_past_message_is_exact_and_has_no_conflict_ids` |
| Mensaje con el momento actual en el mismo minuto que el inicio | `test_check_not_in_the_past_message_uses_local_date_and_now_with_seconds` |
| Mensaje con la fecha local y no la de UTC | `test_check_not_in_the_past_message_uses_local_date_and_now_with_seconds` |
| Mensaje al reprogramar un turno al pasado | `test_reschedule_rejects_past_with_reprogramar_message` |
| Mensaje al reprogramar con el momento actual en el mismo minuto que el inicio | `test_reschedule_rejects_same_minute_past_with_seconds` |

## TDD y mutación

- Las tareas nuevas se trabajaron con ciclos RED → GREEN y triangulación en el archivo de pruebas de reprogramación.
- Mutación temporal: se cambió el default de `operation` a `"reprogramar turnos"` en `validate_new_appointment` y `check_not_in_the_past`; la suite focalizada falló con 4 fallos (`1 passed, 4 failed` en los casos seleccionados), demostrando que la regresión del alta es sensible. Se restauró el default `"dar turnos"` y las pruebas finales quedaron verdes.
