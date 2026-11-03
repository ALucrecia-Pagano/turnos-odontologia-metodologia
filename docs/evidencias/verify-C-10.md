# Verify de C-10 transiciones-de-estado-del-turno

## Cómo se verificó

- Fecha: 2026-11-02. Codex implementó sobre propose aprobado y commiteado por la autora; gobernanza MEDIO sin checkpoint.
- Skills del proyecto: tdd, python-testing-patterns, python-pro; flujo source-command-opsx-apply adaptado por prohibición expresa de ejecutar OpenSpec.
- Línea de base antes de editar: `.venv/Scripts/python.exe -m pytest`: **483 passed in 2.59s**; `.venv/Scripts/python.exe -m mypy --strict app tests`: **Success: no issues found in 45 source files**.
- Evidencia final desde backend: `.venv/Scripts/python.exe -m pytest -v` y `.venv/Scripts/python.exe -m mypy --strict app tests`.
- [pytest-C-10.txt](pytest-C-10.txt), [mypy-C-10.txt](mypy-C-10.txt) y [tdd-C-10.txt](tdd-C-10.txt) contienen resultados completos, fallos RED, mutaciones y restauraciones.
- Sin red, instalaciones, datos reales, mocks, patch/monkeypatch ni type: ignore. Sin Git de escritura ni archivo del change.

## Resultado

```text
603 passed in 3.06s
Success: no issues found in 50 source files
```

Se conservan los 483 casos previos y se agregan 120. Dominio puro, siete aristas, copias y resultados de agenda; catálogo y ocupación sin cambios. Los tests de 25 pares usan propiedades independientes de RN-TU-02. Las garantías estáticas Mapping/frozenset tienen dos tests públicos de herramienta, fuera de tests/domain, con controles negativos y mutaciones restauradas.

## Trazabilidad integral: 43/43 escenarios

Todos los nodos siguientes aparecen PASSED en la evidencia final; se expanden variantes parametrizadas. No se cuenta una coincidencia de nombre sin ejecución. Se comprobaron 603 nodos PASSED. La guardia existente sigue intacta y analiza todos los módulos reales. La revisión adicional confirmó ausencia de reloj/UUID global/I/O/historial/reprogramación/dependencias nuevas en el dominio.

| Nº | Escenario de la spec | Test(s) PASSED |
|---|---|---|
| 1 | Todos los pares de estados | `tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.RESERVED-AppointmentStatus.RESERVED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.RESERVED-AppointmentStatus.CONFIRMED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.RESERVED-AppointmentStatus.ATTENDED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.RESERVED-AppointmentStatus.NO_SHOW]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.RESERVED-AppointmentStatus.CANCELLED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CONFIRMED-AppointmentStatus.RESERVED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CONFIRMED-AppointmentStatus.CONFIRMED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CONFIRMED-AppointmentStatus.ATTENDED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CONFIRMED-AppointmentStatus.NO_SHOW]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CONFIRMED-AppointmentStatus.CANCELLED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.ATTENDED-AppointmentStatus.RESERVED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.ATTENDED-AppointmentStatus.CONFIRMED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.ATTENDED-AppointmentStatus.ATTENDED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.ATTENDED-AppointmentStatus.NO_SHOW]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.ATTENDED-AppointmentStatus.CANCELLED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.NO_SHOW-AppointmentStatus.RESERVED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.NO_SHOW-AppointmentStatus.CONFIRMED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.NO_SHOW-AppointmentStatus.ATTENDED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.NO_SHOW-AppointmentStatus.NO_SHOW]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.NO_SHOW-AppointmentStatus.CANCELLED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CANCELLED-AppointmentStatus.RESERVED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CANCELLED-AppointmentStatus.CONFIRMED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CANCELLED-AppointmentStatus.ATTENDED]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CANCELLED-AppointmentStatus.NO_SHOW]`<br>`tests/domain/test_transitions.py::test_all_25_pairs_independent_oracle[AppointmentStatus.CANCELLED-AppointmentStatus.CANCELLED]` |
| 2 | Mapa y destinos no mutables | `tests/test_transition_types.py::test_transition_policy_rejects_mutation_statically[mapping-assignment]`<br>`tests/test_transition_types.py::test_transition_policy_rejects_mutation_statically[frozenset-mutation]` |
| 3 | Odontólogo vinculado | `tests/domain/test_model.py::test_actor_odontologist_preserves_distinct_user_and_professional`<br>`tests/domain/test_model.py::test_actor_fields_are_frozen[role]`<br>`tests/domain/test_model.py::test_actor_fields_are_frozen[professional_id]` |
| 4 | Odontólogo sin vínculo | `tests/domain/test_model.py::test_actor_odontologist_missing_professional_raises`<br>`tests/domain/test_model.py::test_actor_odontologist_none_professional_raises` |
| 5 | Roles de gestión sin profesional | `tests/domain/test_model.py::test_actor_management_without_professional[RECEPCION]`<br>`tests/domain/test_model.py::test_actor_management_without_professional[ADMINISTRADOR]` |
| 6 | Cancelar reservado | `tests/domain/test_lifecycle.py::test_cancel_reserved_returns_agenda_copy` |
| 7 | Confirmar reservado | `tests/domain/test_lifecycle.py::test_change_reserved_to_confirmed_returns_copy` |
| 8 | Rechazo no altera turno | `tests/domain/test_lifecycle.py::test_cancel_attended_rejected_exact_message`<br>`tests/domain/test_lifecycle.py::test_cancel_terminal_cancelled_preserves_original` |
| 9 | Now naive en ambas operaciones | `tests/domain/test_lifecycle.py::test_cancel_naive_now_raises`<br>`tests/domain/test_lifecycle.py::test_change_naive_now_raises` |
| 10 | Now equivalente en otra zona | `tests/domain/test_lifecycle.py::test_change_equivalent_zone_10`<br>`tests/domain/test_lifecycle.py::test_change_equivalent_zone_14` |
| 11 | Cancelar por función incorrecta | `tests/domain/test_lifecycle.py::test_change_cancelled_requires_cancel_operation`<br>`tests/domain/test_lifecycle.py::test_change_cancelled_contract_precedes_foreign_permission` |
| 12 | Destino reservado no reprograma | `tests/domain/test_lifecycle.py::test_change_confirmed_to_reserved_rejected`<br>`tests/domain/test_lifecycle.py::test_change_reserved_diagonal_rejected` |
| 13 | Odontólogo cambia propios | `tests/domain/test_lifecycle.py::test_dentist_own_confirmed_uses_professional_not_user`<br>`tests/domain/test_lifecycle.py::test_dentist_own_attended_uses_professional_not_user`<br>`tests/domain/test_lifecycle.py::test_dentist_own_no_show_uses_professional_not_user` |
| 14 | Odontólogo no cambia ajenos | `tests/domain/test_lifecycle.py::test_dentist_foreign_change_forbidden_exact`<br>`tests/domain/test_lifecycle.py::test_dentist_foreign_attended_forbidden` |
| 15 | Odontólogo nunca cancela | `tests/domain/test_lifecycle.py::test_dentist_cannot_cancel_own_exact_message`<br>`tests/domain/test_lifecycle.py::test_dentist_cannot_cancel_foreign_confirmed` |
| 16 | Gestión opera todos | `tests/domain/test_lifecycle.py::test_management_recepcion_t1_confirm`<br>`tests/domain/test_lifecycle.py::test_management_recepcion_t1_cancel`<br>`tests/domain/test_lifecycle.py::test_management_recepcion_t2_confirm`<br>`tests/domain/test_lifecycle.py::test_management_recepcion_t2_cancel`<br>`tests/domain/test_lifecycle.py::test_management_administrador_t1_confirm`<br>`tests/domain/test_lifecycle.py::test_management_administrador_t1_cancel`<br>`tests/domain/test_lifecycle.py::test_management_administrador_t2_confirm`<br>`tests/domain/test_lifecycle.py::test_management_administrador_t2_cancel` |
| 17 | Cancelar confirmado antes del inicio | `tests/domain/test_lifecycle.py::test_cancel_confirmed_admin_returns_copy` |
| 18 | Cancelar después del inicio y fin | `tests/domain/test_lifecycle.py::test_cancel_reserved_after_13_15_allowed`<br>`tests/domain/test_lifecycle.py::test_cancel_confirmed_after_14_0_allowed` |
| 19 | Cancelar terminales | `tests/domain/test_lifecycle.py::test_cancel_attended_rejected_exact_message`<br>`tests/domain/test_lifecycle.py::test_cancel_terminal_no_show_preserves_original`<br>`tests/domain/test_lifecycle.py::test_cancel_terminal_cancelled_preserves_original` |
| 20 | Ambos destinos antes de inicio | `tests/domain/test_lifecycle.py::test_attended_before_start_exact_message`<br>`tests/domain/test_lifecycle.py::test_no_show_before_start_exact_message` |
| 21 | Igualdad exacta con inicio | `tests/domain/test_lifecycle.py::test_time_attended_equal`<br>`tests/domain/test_lifecycle.py::test_time_no_show_equal` |
| 22 | Un microsegundo antes | `tests/domain/test_lifecycle.py::test_time_attended_micro_before`<br>`tests/domain/test_lifecycle.py::test_time_no_show_micro_before` |
| 23 | Desde inicio sin esperar fin | `tests/domain/test_lifecycle.py::test_time_attended_micro_after`<br>`tests/domain/test_lifecycle.py::test_time_no_show_micro_after`<br>`tests/domain/test_lifecycle.py::test_time_attended_during`<br>`tests/domain/test_lifecycle.py::test_time_no_show_during` |
| 24 | Confirmar sin regla temporal | `tests/domain/test_lifecycle.py::test_confirmation_time_before`<br>`tests/domain/test_lifecycle.py::test_confirmation_time_after` |
| 25 | Diagonales de cambio de estado | `tests/domain/test_lifecycle.py::test_change_reserved_diagonal_rejected`<br>`tests/domain/test_lifecycle.py::test_diagonal_confirmed_invalid`<br>`tests/domain/test_lifecycle.py::test_diagonal_attended_invalid`<br>`tests/domain/test_lifecycle.py::test_diagonal_no_show_invalid` |
| 26 | Cancelación repetida | `tests/domain/test_lifecycle.py::test_cancel_terminal_cancelled_preserves_original` |
| 27 | Permiso oculta fallos posteriores | `tests/domain/test_lifecycle.py::test_permission_hides_invalid_and_early_attended`<br>`tests/domain/test_lifecycle.py::test_permission_hides_invalid_and_early_no_show` |
| 28 | Transición y tiempo juntos | `tests/domain/test_lifecycle.py::test_authorized_invalid_transition_and_early_attended_order`<br>`tests/domain/test_lifecycle.py::test_authorized_invalid_transition_and_early_no_show_order` |
| 29 | Solo transición con tiempo cumplido | `tests/domain/test_lifecycle.py::test_invalid_transition_time_fulfilled_no_show`<br>`tests/domain/test_lifecycle.py::test_invalid_transition_time_fulfilled_confirmed` |
| 30 | Texto de transición inválida | `tests/domain/test_lifecycle.py::test_cancel_attended_rejected_exact_message` |
| 31 | Texto de atención temprana | `tests/domain/test_lifecycle.py::test_attended_before_start_exact_message` |
| 32 | Texto de ausencia temprana | `tests/domain/test_lifecycle.py::test_no_show_before_start_exact_message` |
| 33 | Texto de cambio ajeno | `tests/domain/test_lifecycle.py::test_foreign_dentist_for_t1_exact_message` |
| 34 | Texto de cancelación prohibida | `tests/domain/test_lifecycle.py::test_dentist_cannot_cancel_own_exact_message` |
| 35 | Nombre con espacios y fallback | `tests/domain/test_lifecycle.py::test_transition_name_trim_exact`<br>`tests/domain/test_lifecycle.py::test_transition_name_empty_exact`<br>`tests/domain/test_lifecycle.py::test_transition_name_blank_exact`<br>`tests/domain/test_lifecycle.py::test_transition_name_internal_exact` |
| 36 | Fecha local distinta de UTC | `tests/domain/test_lifecycle.py::test_invalid_transition_uses_local_day_not_utc` |
| 37 | Now con segundos conservados | `tests/domain/test_lifecycle.py::test_early_message_now_retains_seconds` |
| 38 | Metadatos sin falso conflicto | `tests/domain/test_lifecycle.py::test_violation_metadata_never_claims_conflict[transition]`<br>`tests/domain/test_lifecycle.py::test_violation_metadata_never_claims_conflict[early]`<br>`tests/domain/test_lifecycle.py::test_violation_metadata_never_claims_conflict[foreign]`<br>`tests/domain/test_lifecycle.py::test_violation_metadata_never_claims_conflict[cancel]` |
| 39 | Cancelar y volver a reservar ambos recursos | `tests/domain/test_lifecycle_agenda.py::test_cancel_reserved_releases_both_resources`<br>`tests/domain/test_lifecycle_agenda.py::test_cancel_confirmed_releases_both_resources` |
| 40 | Antes de cancelar ocupa ambos recursos | `tests/domain/test_lifecycle_agenda.py::test_before_cancellation_reserved_occupies_both`<br>`tests/domain/test_lifecycle_agenda.py::test_before_cancellation_confirmed_occupies_both` |
| 41 | Regresión de estados ocupantes | `tests/domain/test_lifecycle_agenda.py::test_occupancy_regression_attended`<br>`tests/domain/test_lifecycle_agenda.py::test_occupancy_regression_no_show` |
| 42 | Guardias sobre dominio real | `tests/domain/test_domain_dependencies.py::test_domain_package_real_directory_has_no_forbidden_imports`<br>`tests/domain/test_domain_dependencies.py::test_domain_package_real_directory_has_no_global_clock_calls` |
| 43 | Alta y catálogo conservan payload | `tests/domain/test_lifecycle_agenda.py::test_new_booking_and_catalog_keep_separate_payloads` |

## TDD Cycle Evidence

| Tarea | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 | `suite existente` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | No aplica: verificación/documentación | Revisión/refactor y ejecución; ver registro |
| 1.2 | `suite existente` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | No aplica: verificación/documentación | Revisión/refactor y ejecución; ver registro |
| 2.1 | `tests/domain/test_model.py` | Unidad / integración | 483 tests + mypy45 | ImportError Actor | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 2.2 | `tests/domain/test_model.py` | Unidad / integración | 483 tests + mypy45 | DID NOT RAISE ValueError | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 3.1 | `tests/domain/test_transitions.py + tests/test_transition_types.py` | Unidad / integración / estática | 483 tests + mypy45 | ModuleNotFoundError y seis AssertionError por arista | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 3.2 | `tests/domain/test_transitions.py + tests/test_transition_types.py` | Unidad / integración / estática | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 3.3 | `tests/domain/test_transitions.py + tests/test_transition_types.py` | Unidad / integración / estática | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 4.1 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | ImportError cancel_appointment | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 4.2 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | AssertionError: esperado Rejected | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 4.3 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 5.1 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | ImportError change_status | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 5.2 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | DID NOT RAISE y AssertionError RESERVED | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 5.3 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | DID NOT RAISE en ambas operaciones | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 6.1 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | AttributeError código pendiente | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 6.2 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | AssertionError permiso cancelación | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 6.3 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 7.1 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | AttributeError código pendiente | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 7.2 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | AssertionError acumulación incompleta | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 7.3 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 8.1 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 8.2 | `tests/domain/test_lifecycle.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 9.1 | `tests/domain/test_lifecycle_agenda.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 9.2 | `tests/domain/test_lifecycle_agenda.py` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | Ejecutado, ver registro por tarea | Casos/mutaciones restauradas; registro | Revisión/refactor y ejecución; ver registro |
| 10.1 | `suite completa y evidencias` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | 603 finales; mypy50 | No aplica: verificación/documentación | Revisión/refactor y ejecución; ver registro |
| 10.2 | `suite completa y evidencias` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | 603 finales; mypy50 | No aplica: verificación/documentación | Revisión/refactor y ejecución; ver registro |
| 10.3 | `suite completa y evidencias` | Unidad / integración | 483 tests + mypy45 | No nuevo RED: regresión verde / revisión; ver registro | 603 finales; mypy50 | No aplica: verificación/documentación | Revisión/refactor y ejecución; ver registro |

## Mensajes exactos del código

Los cinco ejemplos normativos se verifican completos; plantillas aplican los estados y fechas recibidos.

```text
El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".
El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "atendido" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).
El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "ausente" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).
No tiene permiso para cambiar el estado del turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): un odontólogo solo puede cambiar el estado de sus propios turnos.
No tiene permiso para cancelar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden cancelar turnos.
El actor odontólogo necesita professional_id
now necesita zona horaria (datetime naive)
Para cancelar debe usar cancel_appointment
```

Fallback literal: `El turno de el profesional ...`; se preservan espacios internos. El formato temporal muestra segundos de now siempre y conserva comparación con microsegundos. Los cuatro metadatos son None.

## Desvíos del apply

1. Varios casos de triangulación y regresión pasaron inicialmente por composición. Se conservaron como verdes iniciales y se aplicaron mutaciones restauradas: Actor/default/frozen, política/aristas, copias, terminales, cancelación tardía, propiedad, permisos, igualdad/fin, orden/corte, nombres/segundos/metadatos, diagonales, integración y tipos. No se atribuye RED original a esos casos. El registro textual incluye salidas y restauraciones.
2. La triangulación de gestión/frozen de 2.1 se añadió como pequeño grupo antes de ejecutar los cinco casos; las restantes aristas/casos se incorporaron por ciclos. 5.1 se marcó antes de conectar change_status con can_transition; la conexión se completó en el RED/GREEN de 5.2. Las tres diagonales restantes por operación y la automatización de los dos rechazos estáticos se completaron en la revisión final, con pruebas y mutaciones restauradas.
3. Se inició el RED/GREEN de 7.1 antes de leer la salida asíncrona de mypy de 6.3. Esta contenía comparison-overlap en ramas constantes de tests nuevos. Se detuvo el avance de 7, se simplificaron exclusivamente esas ramas conservando todos los tests/aserciones, y 6.3 volvió a verde (38 pruebas con guardias, mypy48) antes de continuar. No se usaron ignores ni se modificaron expectativas previas.
4. El sandbox negó inicialmente acceso al Python313 externo del venv. Los mismos comandos funcionaron con ejecución escalada, sin instalar ni cambiar entorno. Un helper PowerShell no se ejecutó por política de scripts; se eliminó y se capturaron comandos directos. Un primer import del helper Python usó nombre incorrecto, corregido antes de ejecutar pruebas.
5. La primera prueba negativa mypy con -c heredó files de pyproject y devolvió error de invocación; se repitió con configuración aislada y produjo los dos errores de tipos esperados. La automatización final usa un archivo temporal mypy.ini con strict=True. Una selección pytest con expresión compuesta se separó incorrectamente en el helper: exit4 no se cuenta como mutación válida; corregido el parseo, se repitió y produjo dos fallos de aserción y dos verdes tras restaurar.
6. Automatic approval review rechazó un script de refactor que reemplazaba el tramo final de los tests por riesgo de borrar pruebas. No se ejecutó. La alternativa segura simplificó patrones exactos de ramas constantes y comprobó preservar la lista de funciones de test; todas las aserciones quedaron intactas. No queda acción bloqueada ni se necesita aprobación.
7. El nuevo test de compatibilidad llamó inicialmente create_professional con dos parámetros, provocando TypeError; se corrigió la llamada al contrato existente con el candidato Professional. No se cambió ningún esperado ni código de catálogo, y el test pasó.
8. Black/ruff no están instalados; se revisó estilo/docstrings manualmente y se ejecutaron tests/mypy después del refactor. Se conservan los 483 tests anteriores sin cambiar valores esperados ni textos. No se ejecutó OpenSpec por instrucción expresa; no se afirma validación CLI.

## Estado final

**Apply completo: 26/26 tareas; trazabilidad 43/43 escenarios.** Conteo real con `grep -F -c -- '- [x]'` y total con `grep -E -c -- '^- \[[ x]\]'`: ambos 26. `git diff --check` limpio; ningún archivo staged. Cambios limitados al Impact de C-10, tests/evidencias y sus design/tasks. No se modificaron KB, main specs, CHANGES, AGENTS, CLAUDE, estado del orquestador, guardia de dependencias ni archivos de otros changes. No se ejecutó stage, commit, push, restore, checkout, stash, archive ni OpenSpec. Helper temporal eliminado. Las advertencias Git sobre permisos del ignore global y conversión LF/CRLF no son errores de diff.
