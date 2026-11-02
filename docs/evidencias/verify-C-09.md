# Verify de C-09 catalogo-y-pacientes-dominio

OPSX no tiene un comando propio de verify. Verificación manual con el formato de C-08. Artefactos: [design.md](../../openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/design.md) y [tasks.md](../../openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/tasks.md).

## Cómo se verificó

- Fecha: 2026-11-01. Implementó Codex sobre el propose aprobado y commiteado por la autora.
- Skills del proyecto: `tdd`, `python-testing-patterns`, `python-pro`; flujo `source-command-opsx-apply`.
- Desde `backend/`: `.venv/Scripts/python.exe -m pytest -v` y `.venv/Scripts/python.exe -m mypy --strict app tests`.
- Desde raíz: `openspec validate catalogo-y-pacientes-dominio --strict`.
- Línea de base antes de toda edición: **375 passed in 1.35s**, **Success: no issues found in 33 source files**.
- Evidencias completas: [pytest-C-09.txt](pytest-C-09.txt) y [mypy-C-09.txt](mypy-C-09.txt).
- Sin paquetes, red, datos reales, mocks ni operaciones Git de escritura. Los tests usan literales de la spec; solo las pruebas separadas de reutilización importan demo_data fuera del dominio.

## Resultado

```text
483 passed in 2.00s
Success: no issues found in 45 source files
```

Se conservan los 375 casos de C-01 a C-08 y se agregan 108. Los constructores previos de Service/Patient se migraron mecánicamente, sin cambiar expectativas ni textos exactos. `Ok.appointment` de agenda no cambia; catálogo usa su propio `Ok[T].entity`.

## Escenarios obligatorios de la consigna y su test

| Tipo | Escenario | Test |
|---|---|---|
| Feliz | Profesional válido | `test_create_professional_valid` |
| Feliz | Paciente válido con DNI con puntos | `test_create_patient_valid_dni_with_dots` |
| Error de negocio | Nombre y DNI inválidos juntos | `test_create_patient_name_and_dni_invalid_together` |
| Borde | DNI inválido no produce duplicado | `test_create_patient_invalid_dni_does_not_duplicate` |
| Regresión | Mensajes C-03 idénticos con sujeto predeterminado | `test_duration_default_keeps_exact_c03_message[zero/negative/grid/maximum/two-reasons]` |

## Trazabilidad integral: 63/63 escenarios

Cada fila se validó contra nodos PASSED de la salida final. Se expanden todas las variantes parametrizadas, incluidas las cuatro entidades con blancos y ambos órdenes de colecciones. El escenario del reloj se complementa con revisión de ausencia de generación de UUID e I/O; los ids literales y su conservación están probados por las altas y los ejemplos.

| Nº | Escenario de la spec | Test(s) PASSED |
|---|---|---|
| 1 | Profesional válido | `tests/domain/test_catalog.py::test_create_professional_valid` |
| 2 | Profesional con nombre repetido permitido | `tests/domain/test_catalog.py::test_create_professional_repeated_name_allowed` |
| 3 | Nombre original de profesional conservado | `tests/domain/test_catalog.py::test_create_professional_preserves_original_name` |
| 4 | Sillón válido | `tests/domain/test_catalog.py::test_create_chair_valid` |
| 5 | Sillón diferente permitido | `tests/domain/test_catalog.py::test_create_chair_different_preserves_collection` |
| 6 | Prestación válida | `tests/domain/test_catalog.py::test_create_service_valid` |
| 7 | Prestación con estado activo por defecto | `tests/domain/test_model.py::test_service_name_duration_and_default_active`<br>`tests/domain/test_catalog.py::test_create_service_valid` |
| 8 | Paciente válido con DNI con puntos | `tests/domain/test_catalog.py::test_create_patient_valid_dni_with_dots` |
| 9 | Paciente válido con DNI sin puntos | `tests/domain/test_catalog.py::test_create_patient_valid_dni_without_dots` |
| 10 | Paciente con nombre repetido permitido | `tests/domain/test_catalog.py::test_create_patient_repeated_name_allowed` |
| 11 | Datos opcionales como texto libre | `tests/domain/test_catalog.py::test_create_patient_preserves_optional_free_text[free-text]`<br>`tests/domain/test_catalog.py::test_create_patient_preserves_optional_free_text[empty]` |
| 12 | Nombre vacío de profesional | `tests/domain/test_catalog.py::test_create_professional_empty_name` |
| 13 | Nombre vacío de sillón | `tests/domain/test_catalog.py::test_create_chair_empty_name` |
| 14 | Nombre vacío de prestación | `tests/domain/test_catalog.py::test_create_service_empty_name` |
| 15 | Nombre vacío de paciente | `tests/domain/test_catalog.py::test_create_patient_empty_name` |
| 16 | Nombre solo de espacios en las cuatro entidades | `tests/domain/test_catalog.py::test_create_professional_blank_name`<br>`tests/domain/test_catalog.py::test_create_chair_empty_does_not_duplicate[empty]`<br>`tests/domain/test_catalog.py::test_create_chair_empty_does_not_duplicate[blank]`<br>`tests/domain/test_catalog.py::test_create_service_empty_does_not_duplicate[empty]`<br>`tests/domain/test_catalog.py::test_create_service_empty_does_not_duplicate[blank]`<br>`tests/domain/test_catalog.py::test_create_patient_blank_name` |
| 17 | Nombre vacío no produce duplicado | `tests/domain/test_catalog.py::test_create_chair_empty_does_not_duplicate[empty]`<br>`tests/domain/test_catalog.py::test_create_chair_empty_does_not_duplicate[blank]`<br>`tests/domain/test_catalog.py::test_create_service_empty_does_not_duplicate[empty]`<br>`tests/domain/test_catalog.py::test_create_service_empty_does_not_duplicate[blank]` |
| 18 | Nombre de sillón duplicado exacto | `tests/domain/test_catalog.py::test_create_chair_duplicate_exact` |
| 19 | Nombre de prestación duplicado exacto | `tests/domain/test_catalog.py::test_create_service_duplicate_exact` |
| 20 | Sillón duplicado con mayúsculas y espacios | `tests/domain/test_catalog.py::test_create_chair_duplicate_case_and_spaces` |
| 21 | Prestación duplicada con mayúsculas y espacios | `tests/domain/test_catalog.py::test_create_service_duplicate_case_and_spaces`<br>`tests/domain/test_catalog.py::test_create_service_duplicate_internal_spaces` |
| 22 | Las tildes distinguen prestaciones | `tests/domain/test_catalog.py::test_create_service_accents_distinguish_names` |
| 23 | Las tildes distinguen sillones | `tests/domain/test_catalog.py::test_create_chair_accents_distinguish_names` |
| 24 | Un existente inactivo conserva su nombre único | `tests/domain/test_catalog.py::test_create_chair_inactive_name_still_unique`<br>`tests/domain/test_catalog.py::test_create_service_inactive_name_still_unique` |
| 25 | Varios existentes equivalentes producen una violación | `tests/domain/test_catalog.py::test_create_chair_multiple_equivalents_one_violation[direct]`<br>`tests/domain/test_catalog.py::test_create_chair_multiple_equivalents_one_violation[reverse]`<br>`tests/domain/test_catalog.py::test_create_service_multiple_equivalents_one_violation[direct]`<br>`tests/domain/test_catalog.py::test_create_service_multiple_equivalents_one_violation[reverse]` |
| 26 | DNI de siete dígitos válido | `tests/domain/test_catalog.py::test_create_patient_valid_dni_seven` |
| 27 | DNI con puntos y espacios válido | `tests/domain/test_catalog.py::test_create_patient_valid_dni_outer_spaces`<br>`tests/domain/test_catalog.py::test_create_patient_valid_dni_inner_spaces` |
| 28 | DNI con guiones inválido | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_hyphens` |
| 29 | DNI de seis dígitos inválido | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_six` |
| 30 | DNI de nueve dígitos inválido | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_nine` |
| 31 | DNI con letras inválido | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_letters` |
| 32 | DNI vacío o blanco inválido | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_empty`<br>`tests/domain/test_catalog.py::test_create_patient_invalid_dni_blank` |
| 33 | DNI inválido no produce duplicado | `tests/domain/test_catalog.py::test_create_patient_invalid_dni_does_not_duplicate` |
| 34 | DNI duplicado sin puntos | `tests/domain/test_catalog.py::test_create_patient_duplicate_dni_exact` |
| 35 | DNI con y sin puntos son iguales | `tests/domain/test_catalog.py::test_create_patient_duplicate_dni_candidate_dots`<br>`tests/domain/test_catalog.py::test_create_patient_duplicate_dni_existing_dots` |
| 36 | DNI duplicado de siete dígitos | `tests/domain/test_catalog.py::test_create_patient_duplicate_dni_seven` |
| 37 | Pacientes recibidos en otro orden | `tests/domain/test_catalog.py::test_create_patient_duplicate_dni_collection_order[direct]`<br>`tests/domain/test_catalog.py::test_create_patient_duplicate_dni_collection_order[reverse]` |
| 38 | Duraciones límite válidas | `tests/domain/test_catalog.py::test_create_service_duration_valid_5`<br>`tests/domain/test_catalog.py::test_create_service_duration_valid_480` |
| 39 | Duración cero o negativa | `tests/domain/test_catalog.py::test_create_service_duration_0`<br>`tests/domain/test_catalog.py::test_create_service_duration_negative_5` |
| 40 | Duración fuera de la grilla | `tests/domain/test_catalog.py::test_create_service_duration_7` |
| 41 | Duración mayor que el máximo | `tests/domain/test_catalog.py::test_create_service_duration_485` |
| 42 | Duración con dos razones | `tests/domain/test_catalog.py::test_create_service_duration_487` |
| 43 | Nombre y DNI inválidos juntos | `tests/domain/test_catalog.py::test_create_patient_name_and_dni_invalid_together` |
| 44 | Nombre vacío y DNI duplicado | `tests/domain/test_catalog.py::test_create_patient_empty_name_and_duplicate_dni_ordered` |
| 45 | Prestación duplicada y duración inválida | `tests/domain/test_catalog.py::test_create_service_duplicate_and_duration_ordered` |
| 46 | Nombre vacío no oculta duración inválida | `tests/domain/test_catalog.py::test_create_service_empty_name_and_duration_ordered_without_duplicate` |
| 47 | Metadatos de las violaciones nuevas | `tests/domain/test_catalog.py::test_catalog_violation_metadata_empty`<br>`tests/domain/test_catalog.py::test_catalog_violation_metadata_name`<br>`tests/domain/test_catalog.py::test_catalog_violation_metadata_invalid`<br>`tests/domain/test_catalog.py::test_catalog_violation_metadata_dni` |
| 48 | Desactivar cada recurso activo | `tests/domain/test_catalog.py::test_deactivate_professional_returns_copy`<br>`tests/domain/test_catalog.py::test_deactivate_chair_returns_copy`<br>`tests/domain/test_catalog.py::test_deactivate_service_returns_copy` |
| 49 | Reactivar cada recurso inactivo | `tests/domain/test_catalog.py::test_reactivate_professional_returns_copy`<br>`tests/domain/test_catalog.py::test_reactivate_chair_returns_copy`<br>`tests/domain/test_catalog.py::test_reactivate_service_returns_copy` |
| 50 | Desactivar un recurso ya inactivo | `tests/domain/test_catalog.py::test_deactivate_professional_is_idempotent`<br>`tests/domain/test_catalog.py::test_deactivate_chair_is_idempotent`<br>`tests/domain/test_catalog.py::test_deactivate_service_is_idempotent` |
| 51 | Reactivar un recurso ya activo | `tests/domain/test_catalog.py::test_reactivate_professional_is_idempotent`<br>`tests/domain/test_catalog.py::test_reactivate_chair_is_idempotent`<br>`tests/domain/test_catalog.py::test_reactivate_service_is_idempotent` |
| 52 | Desactivar no modifica turnos existentes | `tests/domain/test_catalog_agenda.py::test_deactivate_professional_preserves_existing_appointment`<br>`tests/domain/test_catalog_agenda.py::test_deactivate_chair_preserves_existing_appointment`<br>`tests/domain/test_catalog_agenda.py::test_deactivate_service_preserves_existing_appointment` |
| 53 | Turno nuevo con profesional desactivado | `tests/domain/test_catalog_agenda.py::test_new_appointment_rejects_deactivated_professional` |
| 54 | Turno nuevo con sillón o prestación desactivados | `tests/domain/test_catalog_agenda.py::test_new_appointment_rejects_deactivated_chair`<br>`tests/domain/test_catalog_agenda.py::test_new_appointment_rejects_deactivated_service` |
| 55 | Turno nuevo después de reactivar | `tests/domain/test_catalog_agenda.py::test_new_appointment_after_reactivation_keeps_agenda_ok_payload` |
| 56 | Campos exactos del paciente | `tests/domain/test_model.py::test_patient_has_exactly_five_nonclinical_fields` |
| 57 | Opcionales de paciente ausentes | `tests/domain/test_model.py::test_patient_optional_fields_default_to_none` |
| 58 | Construcción no rechaza datos de negocio inválidos | `tests/domain/test_model.py::test_catalog_models_accept_invalid_business_data_without_raising` |
| 59 | Profesional sin matrícula en el dominio | `tests/domain/test_model.py::test_professional_fields_exclude_license_number` |
| 60 | Catálogo y paciente ficticios disponibles | `tests/test_demo_data.py::test_demo_data_fictional_entities_are_available` |
| 61 | Ejemplos válidos por las altas | `tests/test_demo_data.py::test_demo_professional_accepted_by_public_create`<br>`tests/test_demo_data.py::test_demo_chair_accepted_by_public_create`<br>`tests/test_demo_data.py::test_demo_service_accepted_by_public_create`<br>`tests/test_demo_data.py::test_demo_patient_accepted_by_public_create` |
| 62 | El dominio no importa demo_data | `tests/domain/test_catalog_dependencies.py::test_catalog_real_domain_has_no_forbidden_dependencies`<br>`tests/domain/test_catalog_dependencies.py::test_catalog_guard_detects_demo_import_without_importing_it` |
| 63 | Dominio sin reloj global ni generación de identificadores | `tests/domain/test_catalog_dependencies.py::test_catalog_real_domain_has_no_global_clock_calls`<br>`tests/test_demo_data.py::test_demo_data_fictional_entities_are_available` |

## Pureza y compatibilidad verificadas

- `find_forbidden_imports=[]`, `find_global_clock_calls=[]` sobre todo el dominio real, incluido catálogo.
- Revisión AST sin `Any`, `unicodedata`, imports de demo_data, llamadas de UUID generado, reloj ni I/O nuevos. Las altas no agregan `raise`; las excepciones existentes de programación se conservan.
- Patient tiene exactamente `id`, `full_name`, `dni`, `phone`, `health_insurance`.
- Comparación AST contra HEAD: `test_validate_new_appointment.py` queda idéntico al quitar exclusivamente los argumentos nuevos de Service y Patient. Todos los valores esperados y textos exactos son los originales. En test_model y test_violations, los nodos previos quedan idénticos y solo se agregan pruebas.
- Diff vacío para appointment, references, names gramatical y todas las reglas de agenda excepto duration. En duration solo cambia el parámetro subject, su documentación y el sustantivo del mensaje; constantes, condiciones, razones y orden están intactos.
- El `Ok` vigente de agenda y `ValidationResult` no cambian; el nuevo `catalog.result.Ok[T]` está separado.
- KB 04, SU-12, RN-PA-01/02, RN-AG-09 y US-020/021/022 coinciden con el alcance aplicado y no se editaron.

## Validación de OpenSpec

```text
Change 'catalogo-y-pacientes-dominio' is valid
```

## TDD Cycle Evidence

Cada ciclo registró su ejecución real. Las regresiones que pasaron inicialmente figuran como tales; las mutaciones no se presentan como RED históricos. Red de seguridad inicial 375/375; antes de cada refactor hubo estado verde, y cada refactor se ejecutó con tests después. Las tareas 1.x y 12.x son verificaciones sin producción nueva.

| Tarea | Archivo de test | Capa | Safety Net | RED | GREEN | TRIANGULATE / mutaciones | REFACTOR / evidencia |
|---|---|---|---|---|---|---|---|
| 2.1 | `test_model.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 20 deselected in 0.21s | Verde anterior conservado | Casos por seam; ver registro | RED ejecutado: AttributeError Service sin name (1 failed, 20 deselected). |
| 2.2 | `test_model.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 376 passed in 1.54s | Casos por seam; ver registro | GREEN 376 passed; mypy33 sin errores. Solo nombre añadido en constructores existentes, expectativas intactas. |
| 2.3 | `test_model.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 21 deselected in 0.20s | 1 passed, 22 deselected in 0.09s; 378 passed in 1.02s | 1 failed, 22 deselected in 0.19s | RED fields: 1 failed (id solamente); GREEN fields. Opcionales pasaron inicialmente; mutación None?texto vac?o:1 failed, restaurada. Suite378/mypy33. |
| 2.4 | `test_model.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 24 deselected in 0.10s; 380 passed in 0.99s | 1 failed, 23 deselected in 0.19s; 1 failed, 24 deselected in 0.18s; 1 failed, 24 deselected in 0.19s | Construcción y matrícula pasan inicialmente; mutaciones validación de constructor, license_number y campo clínico:1 fallo cada una, restauradas; suite380. |
| 2.5 | `test_model.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 380 passed in 0.85s; 2026-10-20 13:30:00+00:00 | Casos por seam; ver registro | Docstrings actualizados; suite380/mypy33. Ejemplo README ejecutado:2026-10-20 13:30:00+00:00. Expectativas previas intactas. |
| 3.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 error in 0.31s | 2 passed in 0.12s; 2 passed in 0.15s | 2 failed in 0.20s | RED ModuleNotFoundError catálogo; GREEN profesional. Paciente pasó inicialmente; mutación entity→payload:2 fallos/restaurada. |
| 3.2 | `test_violations.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 30 deselected in 0.32s; 1 failed, 31 deselected in 0.15s; 1 failed, 32 deselected in 0.15s; 1 failed, 33 deselected in 0.14s | 1 passed, 33 deselected in 0.07s; 34 passed in 0.09s | Casos por seam; ver registro | Cuatro ciclos RED AttributeError y GREEN uno por código; violations34/mypy36 sin errores; códigos y textos previos intactos. |
| 3.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 36 passed in 0.14s | Casos por seam; ver registro | Resultados/documentación separados; tests36 y mypy36 verdes, sin Any/ignore. |
| 4.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 2 deselected in 0.16s | 1 passed, 2 deselected in 0.08s | Casos por seam; ver registro | RED módulo create ausente; GREEN1 caso válido con entidad literal. |
| 4.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 3 deselected in 0.13s; 1 failed, 4 deselected in 0.13s | 1 passed, 3 deselected in 0.08s; 5 passed in 0.09s | Casos por seam; ver registro | RED vacío1 fallo; GREEN; RED blanco1 fallo; GREEN tras strip (5casos verdes). |
| 4.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 6 deselected in 0.16s; 1 passed, 6 deselected in 0.12s | 1 failed, 6 deselected in 0.29s | Repetido y nombre original verdes de entrada; mutación strip del nombre aceptado:1 fallo, restaurada. |
| 4.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 391 passed in 1.70s | Casos por seam; ver registro | Regla check_name compartible y README; suite391/mypy38 verdes. |
| 5.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 7 deselected in 0.27s | 1 passed, 8 deselected in 0.18s; 1 passed, 8 deselected in 0.11s | 1 failed, 8 deselected in 0.26s | RED ImportError create_chair; GREEN. Diferente verde inicialmente; mutación estadoFalse:1 fallo/restaurada, colección intacta. |
| 5.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 9 deselected in 0.28s | 2 passed, 10 deselected in 0.13s; 2 passed, 77 deselected in 0.16s | 2 failed, 10 deselected in 0.30s; 2 failed, 77 deselected in 0.45s | RED vacío1 fallo/GREEN. Vacío y blanco sin duplicado verdes; mutación agrega duplicado espurio2 fallos/restaurada (todavía no existía regla duplicado). |
| 5.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 12 deselected in 0.29s; 1 failed, 13 deselected in 0.33s | 1 passed, 13 deselected in 0.12s; 1 passed, 78 deselected in 0.15s | 1 failed, 13 deselected in 0.28s; 1 failed, 13 deselected in 0.56s; 1 failed, 78 deselected in 0.31s | RED exacto1fallo/GREEN; RED normalización1fallo/GREEN; mutaciones solo strip y casefold en texto:1fallo cada una, restauradas. |
| 5.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 17 deselected in 0.13s; 1 passed, 17 deselected in 0.14s | 1 failed, 14 deselected in 0.33s; 1 failed, 15 deselected in 0.29s; 2 failed, 16 deselected in 0.30s; 1 failed, 17 deselected in 0.26s; 1 failed, 17 deselected in 0.26s | Tildes/inactivo/dos existentes ambas órdenes verdes inicialmente; mutaciones tildes1, activos1, duplicados2, sin casefold1/sin colapso1 fallos; todas restauradas. |
| 5.5 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 402 passed in 1.74s | Casos por seam; ver registro | Reglas separadas de subject_name y documentación; suite402/mypy38 verdes. |
| 6.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 18 deselected in 0.45s | 1 passed, 18 deselected in 0.17s | Casos por seam; ver registro | RED ImportError create_service; GREEN prestación45activa. |
| 6.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 19 deselected in 0.33s | 2 passed, 20 deselected in 0.20s; 2 passed, 20 deselected in 0.13s | 1 failed, 1 passed, 20 deselected in 0.31s | RED vacío1fallo/GREEN; vacío/blanco sin duplicado inicialmente verdes; mutación guarda blancos1fallo/restaurada. |
| 6.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 22 deselected in 0.29s | 2 passed, 27 deselected in 0.18s; 2 passed, 27 deselected in 0.13s | 1 failed, 24 deselected in 0.25s; 1 failed, 24 deselected in 0.27s; 1 failed, 25 deselected in 0.24s; 1 failed, 26 deselected in 0.26s; 2 failed, 27 deselected in 0.24s | RED duplicado1fallo/GREEN. Variantes inicialmente verdes; mutaciones candidato solo1, presentación1, tildes1, filtroactivos1, duplicados2 fallos/restauradas. |
| 6.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 29 deselected in 0.29s | 1 passed, 35 deselected in 0.12s; 5 passed, 31 deselected in 0.13s | 1 failed, 34 deselected in 0.30s; 1 failed, 35 deselected in 0.28s; 5 failed, 31 deselected in 0.42s | RED duración7:1fallo; GREEN reglaúnica con subject. Casos0,-5,485,487 verdes y mutación omitirregla5fallos; límites5/480 mutaciones1fallo c/u restauradas. |
| 6.4a | `test_duration.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 4 deselected in 0.12s; 5 passed in 0.10s | 5 failed in 0.27s | Cinco regresiones literales C03 pasan inicialmente; mutación default a prestación:5fallos; restaurada5verdes. RED explícito parámetro previo6.4. |
| 6.5 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 5 passed in 0.24s; 425 passed in 1.83s | 5 failed, 31 deselected in 0.28s; 5 failed, 31 deselected in 0.32s; 5 failed in 0.28s | Tres mutaciones:omitirregla5, omitirsubject5, defaultprestación5fallos, restauradas. Suite421/mypy39. |
| 6.6 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 425 passed in 2.13s; 5 passed in 0.14s | Casos por seam; ver registro | Docstrings/README actualizados; suite425/mypy39. INACTIVE_REFERENCE intacto. |
| 7.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 36 deselected in 0.33s | 1 passed, 37 deselected in 0.25s; 2 passed, 36 deselected in 0.15s | 2 failed, 36 deselected in 0.32s | RED ImportError create_patient/GREEN puntos. Sinpuntos inicialmente verde; mutación DNIvacío2fallos/restaurada. Candidata/colección intactas. |
| 7.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 38 deselected in 0.34s | 2 passed, 41 deselected in 0.26s; 3 passed, 40 deselected in 0.14s | 1 failed, 39 deselected in 0.25s; 3 failed, 40 deselected in 0.32s | RED vacíonombre1/GREEN; blancos/repetido/opcionales verdes; mutaciones guarda1fallo y valores3fallos restauradas. |
| 7.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 43 deselected in 0.37s | 1 passed, 48 deselected in 0.27s; 6 passed, 43 deselected in 0.13s | 6 failed, 43 deselected in 0.48s | RED guiones1fallo/GREEN; seis/nueve/letras/vacío/blanco verdes; mutación omitirregla6fallos/restaurada. |
| 7.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 51 deselected in 0.13s; 2 passed, 50 deselected in 0.13s | 1 failed, 51 deselected in 0.29s; 2 failed, 50 deselected in 0.27s | Tres variantes inicialmente verdes; mutaciones solo8dígitos1fallo y noquitarespacios2fallos/restauradas. |
| 7.5 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 52 deselected in 0.37s | 2 passed, 56 deselected in 0.32s; 4 passed, 54 deselected in 0.15s | 4 failed, 54 deselected in 0.34s | RED duplicado1fallo/GREEN; puntosambossentidos/7dígitos/orden verdes, mutación omitirduplicadoconpuntos4fallos/restaurada. |
| 7.6 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 2 passed, 57 deselected in 0.13s; 448 passed in 1.73s | 1 failed, 58 deselected in 0.32s; 1 failed, 58 deselected in 0.27s; 2 failed, 57 deselected in 0.29s | Guarda inicialmente verde; mutaciones sin guarda1, comparaciónbruta1 y sinmiles2fallos/restauradas; suite448. |
| 7.7 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 448 passed in 1.75s | Casos por seam; ver registro | Docstrings/README sin nuevas validaciones de opcionales; suite448/mypy40 verdes. |
| 8.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 60 deselected in 0.29s; 2 passed, 59 deselected in 0.19s | 2 failed, 59 deselected in 0.30s | Dos casos composición verdes inicialmente; mutación retorno tras nombre2fallos/restaurada. |
| 8.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 62 deselected in 0.27s; 2 passed, 61 deselected in 0.13s | 2 failed, 61 deselected in 0.30s | Dos casos verdes inicialmente; mutación duración primero2fallos/restaurada; vacío no participa duplicado. |
| 8.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 66 deselected in 0.34s; 4 passed, 63 deselected in 0.15s | 1 failed, 3 passed, 63 deselected in 0.33s | Cuatro códigos con metadatosNone verdes; mutación reference_kind en EMPTY_NAME1fallo/restaurada. |
| 8.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 456 passed in 1.71s | Casos por seam; ver registro | Composición documentada y README; suite456/mypy40, reglas de agenda intactas salvo subjectduration autorizado. |
| 9.1 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 67 deselected in 0.39s | 1 passed, 69 deselected in 0.32s; 3 passed, 67 deselected in 0.13s | 3 failed, 67 deselected in 0.30s | RED móduloactivationausente; GREENtresrecursos, originalesintactos. Mutación devolveroriginal3fallos/restaurada. |
| 9.2 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed, 70 deselected in 0.47s | 1 passed, 72 deselected in 0.33s; 3 passed, 70 deselected in 0.13s | 3 failed, 70 deselected in 0.32s | RED ImportError reactivate; GREENtresrecursos, originalesintactos; mutacióndevolveroriginal3fallos/restaurada. |
| 9.3 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 78 deselected in 0.42s; 3 passed, 76 deselected in 0.21s | 3 failed, 73 deselected in 0.36s; 3 failed, 76 deselected in 0.36s | Seiscasos idempotentes verdes; mutaciones alternaractive3fallos poroperación/restauradas, sincódigosnuevos. |
| 9.4 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 3 passed, 76 deselected in 0.15s; 468 passed in 1.82s | 3 failed, 76 deselected in 0.31s | Mutación devolveroriginal3fallos/restaurada; originales/copia probados; Patient sinactive; suite468/mypy41. |
| 9.5 | `test_catalog.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 12 passed, 67 deselected in 0.12s | Casos por seam; ver registro | Docstrings/README y tiposconcretos;12casosactivación/mypy41 verdes. |
| 10.1 | `test_catalog_agenda.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 3 passed in 0.17s; 182 passed in 0.61s | 3 failed in 0.28s | Tresregresiones turno verdeinicial;mutación devolverrecursoactivo3fallos porestado, no seafirma probaralteracióndelturno. Agenda182verdes; excepción taskaplicada sinfalsearRED. |
| 10.2 | `test_catalog_agenda.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 5 deselected in 0.28s; 3 passed, 3 deselected in 0.15s | 3 failed, 3 deselected in 0.34s | Tresrecursos ya rechazados porregla vigente;mutación desactivarcomoactivo3fallos/restaurada, textos exactos sinnombre/conflictos. |
| 10.3 | `test_catalog_agenda.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 6 deselected in 0.14s; 475 passed in 1.79s | 1 failed, 6 deselected in 0.33s | Reactivación verdeinicial,mutaciónactivoFalse1fallo/restaurada. Contrato Ok.appointment/textosprevios intactos;suite475/mypy42. |
| 11.1 | `test_demo_data.py / test_catalog_dependencies.py` | Unidad, seam público | 375 inicial + verdes previos | 1 failed in 0.26s | 1 passed in 0.10s | Casos por seam; ver registro | RED ImportError demo_data; GREEN coleccionesinmutables conUUIDliterales ydatosficticios. |
| 11.2 | `test_demo_data.py / test_catalog_dependencies.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 1 passed, 4 deselected in 0.11s; 1 passed, 4 deselected in 0.10s | 1 failed, 4 deselected in 0.28s; 1 failed, 4 deselected in 0.27s | Cuatroaltas verdes deentrada; mutaciónduración1fallo yDNI1fallo/restauradas, datosreglas siguenliterales. |
| 11.3 | `test_demo_data.py / test_catalog_dependencies.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 3 passed in 0.19s; 23 passed in 0.66s | 1 failed, 1 deselected in 0.21s | Dominio real limpio. Por prohibición másreciente de importar demo_data, mutación soloenarchivo sintético tmp_path parseado sinimportar; detección app.demo_data ycontrolnegativo1fallo/restaurado. Guardiasreales yreloj23verdes. |
| 11.4 | `test_demo_data.py / test_catalog_dependencies.py` | Unidad, seam público | 375 inicial + verdes previos | Verde inicial o refactor; no se inventa RED | 483 passed in 2.01s | Casos por seam; ver registro | README/docstrings actualizados; suite483/mypy45; dominio no importa demo_data ysinsecretos. |

## Registro de salidas RED, GREEN, triangulación y restauración

Las salidas de fallo se registraron durante el ciclo, también en tasks.md. La tabla conserva el resumen real y la primera línea de error; no sustituye los textos literales de los tests.

| Ciclo | Exit | Salida | Primer error |
|---|---:|---|---|
| 2.1 RED | 1 | 1 failed, 20 deselected in 0.21s | E       AttributeError: 'Service' object has no attribute 'name' |
| 2.2 GREEN suite | 0 | 376 passed in 1.54s | — |
| 2.2 mypy | 0 | Success: no issues found in 33 source files | — |
| 2.3 RED fields | 1 | 1 failed, 21 deselected in 0.20s | E       AssertionError: assert ['id'] == ['id', 'full_...th_insurance'] |
| 2.3 GREEN fields | 0 | 1 passed, 21 deselected in 0.11s | — |
| 2.3 optional initially green | 0 | 1 passed, 22 deselected in 0.13s | — |
| 2.3 optional sensitivity | 1 | 1 failed, 22 deselected in 0.19s | E       AssertionError: assert ('', None) == (None, None) |
| 2.3 optional sensitivity restored | 0 | 1 passed, 22 deselected in 0.09s | — |
| 2.3 suite | 0 | 378 passed in 1.02s | — |
| 2.3 mypy | 0 | Success: no issues found in 33 source files | — |
| 2.4 construction initially green | 0 | 1 passed, 23 deselected in 0.15s | — |
| 2.4 constructor validation mutation | 1 | 1 failed, 23 deselected in 0.19s | E           ValueError: duración inválida |
| 2.4 constructor validation mutation restored | 0 | 1 passed, 23 deselected in 0.10s | — |
| 2.4 license initially green | 0 | 1 passed, 24 deselected in 0.13s | — |
| 2.4 license mutation | 1 | 1 failed, 24 deselected in 0.18s | E       AssertionError: assert ['id', 'full_...cense_number'] == ['id', 'full_name', 'active'] |
| 2.4 license mutation restored | 0 | 1 passed, 24 deselected in 0.11s | — |
| 2.4 clinical field mutation | 1 | 1 failed, 24 deselected in 0.19s | E       AssertionError: assert ['id', 'full_..., 'diagnosis'] == ['id', 'full_...th_insurance'] |
| 2.4 clinical field mutation restored | 0 | 1 passed, 24 deselected in 0.10s | — |
| 2.4 restored suite | 0 | 380 passed in 0.99s | — |
| 2.5 refactor suite | 0 | 380 passed in 0.85s | — |
| 2.5 mypy | 0 | Success: no issues found in 33 source files | — |
| 2.5 README example | 0 | 2026-10-20 13:30:00+00:00 | — |
| 3.1 RED result | 2 | 1 error in 0.31s | E   ModuleNotFoundError: No module named 'app.domain.catalog' |
| 3.1 GREEN professional | 0 | 1 passed in 0.10s | — |
| 3.1 patient initially green | 0 | 2 passed in 0.12s | — |
| 3.1 result payload mutation | 1 | 2 failed in 0.20s | E       AttributeError: 'Ok' object has no attribute 'entity' |
| 3.1 result payload mutation restored | 0 | 2 passed in 0.15s | — |
| 3.2 RED EMPTY_NAME | 1 | 1 failed, 30 deselected in 0.32s | E       AttributeError: type object 'ViolationCode' has no attribute 'EMPTY_NAME' |
| 3.2 GREEN EMPTY_NAME | 0 | 1 passed, 30 deselected in 0.07s | — |
| 3.2 RED DUPLICATE_NAME | 1 | 1 failed, 31 deselected in 0.15s | E       AttributeError: type object 'ViolationCode' has no attribute 'DUPLICATE_NAME' |
| 3.2 GREEN DUPLICATE_NAME | 0 | 1 passed, 31 deselected in 0.07s | — |
| 3.2 RED INVALID_DNI | 1 | 1 failed, 32 deselected in 0.15s | E       AttributeError: type object 'ViolationCode' has no attribute 'INVALID_DNI' |
| 3.2 GREEN INVALID_DNI | 0 | 1 passed, 32 deselected in 0.07s | — |
| 3.2 RED DUPLICATE_DNI | 1 | 1 failed, 33 deselected in 0.14s | E       AttributeError: type object 'ViolationCode' has no attribute 'DUPLICATE_DNI'. Did you mean: 'DUPLICATE_NAME'? |
| 3.2 GREEN DUPLICATE_DNI | 0 | 1 passed, 33 deselected in 0.07s | — |
| 3.2 violations | 0 | 34 passed in 0.09s | — |
| 3.2 mypy | 0 | Success: no issues found in 36 source files | — |
| 3.3 result refactor | 0 | 36 passed in 0.14s | — |
| 3.3 mypy | 0 | Success: no issues found in 36 source files | — |
| 4.1 RED | 1 | 1 failed, 2 deselected in 0.16s | E       ModuleNotFoundError: No module named 'app.domain.catalog.create' |
| 4.1 GREEN | 0 | 1 passed, 2 deselected in 0.08s | — |
| 4.2 RED empty | 1 | 1 failed, 3 deselected in 0.13s | E       AssertionError: assert Ok(entity=Professional(id=UUID('00000000-0000-0000-0000-000000000001'), full_name='', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre del profesional no pu...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 4.2 GREEN empty | 0 | 1 passed, 3 deselected in 0.08s | — |
| 4.2 RED blank | 1 | 1 failed, 4 deselected in 0.13s | E       AssertionError: assert Ok(entity=Professional(id=UUID('00000000-0000-0000-0000-000000000001'), full_name='   ', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre del profesional no pu...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 4.2 GREEN blank | 0 | 5 passed in 0.09s | — |
| 4.3 repeated initially green | 0 | 1 passed, 5 deselected in 0.17s | — |
| 4.3 original initially green | 0 | 1 passed, 6 deselected in 0.16s | — |
| 4.3 strip mutation | 1 | 1 failed, 6 deselected in 0.29s | E       AssertionError: assert Ok(entity=Pro... active=True)) == Ok(entity=Pro... active=True)) |
| 4.3 strip mutation restored | 0 | 1 passed, 6 deselected in 0.12s | — |
| 4.4 suite | 0 | 391 passed in 1.70s | — |
| 4.4 mypy | 0 | Success: no issues found in 38 source files | — |
| 5.1 RED valid | 1 | 1 failed, 7 deselected in 0.27s | E       ImportError: cannot import name 'create_chair' from 'app.domain.catalog.create' (C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\app\domain\catalog\create.py) |
| 5.1 GREEN valid | 0 | 1 passed, 7 deselected in 0.13s | — |
| 5.1 different initially green | 0 | 1 passed, 8 deselected in 0.18s | — |
| 5.1 active mutation | 1 | 1 failed, 8 deselected in 0.26s | E       AssertionError: assert Ok(entity=Cha...active=False)) == Ok(entity=Cha... active=True)) |
| 5.1 active mutation restored | 0 | 1 passed, 8 deselected in 0.11s | — |
| 5.2 RED empty | 1 | 1 failed, 9 deselected in 0.28s | E       AssertionError: assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b1'), name='', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre del sillón no puede e...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.2 GREEN empty | 0 | 1 passed, 9 deselected in 0.24s | — |
| 5.2 guard initially green | 0 | 2 passed, 10 deselected in 0.17s | — |
| 5.2 spurious duplicate mutation | 1 | 2 failed, 10 deselected in 0.30s | E       AssertionError: assert Rejected(viol...terval=None))) == Rejected(viol...erval=None),)) |
| 5.2 spurious duplicate mutation restored | 0 | 2 passed, 10 deselected in 0.13s | — |
| 5.3 RED exact | 1 | 1 failed, 12 deselected in 0.29s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='Sillón 1', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ón 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.3 GREEN exact | 0 | 1 passed, 12 deselected in 0.17s | — |
| 5.3 RED normalization | 1 | 1 failed, 13 deselected in 0.33s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='  SILLÓN   1  ', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ÓN 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.3 GREEN normalization | 0 | 2 passed, 12 deselected in 0.16s | — |
| 5.3 display strip mutation | 1 | 1 failed, 13 deselected in 0.28s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='  SILLÓN   1  ', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ÓN 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.3 display strip mutation restored | 0 | 1 passed, 13 deselected in 0.12s | — |
| 5.3 display casefold mutation | 1 | 1 failed, 13 deselected in 0.56s | E       assert Rejected(viol...erval=None),)) == Rejected(viol...erval=None),)) |
| 5.3 display casefold mutation restored | 0 | 1 passed, 13 deselected in 0.12s | — |
| 5.4 accents initially green | 0 | 1 passed, 14 deselected in 0.19s | — |
| 5.4 accent mutation | 1 | 1 failed, 14 deselected in 0.33s | E       assert Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...on 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='Sillon 1', active=True)) |
| 5.4 accent mutation restored | 0 | 1 passed, 14 deselected in 0.12s | — |
| 5.4 inactive initially green | 0 | 1 passed, 15 deselected in 0.21s | — |
| 5.4 active filter mutation | 1 | 1 failed, 15 deselected in 0.29s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='Sillón 1', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ón 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.4 active filter mutation restored | 0 | 1 passed, 15 deselected in 0.12s | — |
| 5.4 multiple initially green | 0 | 2 passed, 16 deselected in 0.20s | — |
| 5.4 repeated violations mutation | 1 | 2 failed, 16 deselected in 0.30s | E       assert Rejected(viol...terval=None))) == Rejected(viol...erval=None),)) |
| 5.4 repeated violations mutation restored | 0 | 2 passed, 16 deselected in 0.12s | — |
| 5.4 no casefold mutation | 1 | 1 failed, 17 deselected in 0.26s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='  SILLÓN   1  ', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ÓN 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.4 no casefold mutation restored | 0 | 1 passed, 17 deselected in 0.13s | — |
| 5.4 no collapse mutation | 1 | 1 failed, 17 deselected in 0.26s | E       assert Ok(entity=Chair(id=UUID('00000000-0000-0000-0000-0000000000b2'), name='  SILLÓN   1  ', active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe un sillón con...ÓN 1".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 5.4 no collapse mutation restored | 0 | 1 passed, 17 deselected in 0.14s | — |
| 5.5 suite | 0 | 402 passed in 1.74s | — |
| 5.5 mypy | 0 | Success: no issues found in 38 source files | — |
| 6.1 RED valid | 1 | 1 failed, 18 deselected in 0.45s | E       ImportError: cannot import name 'create_service' from 'app.domain.catalog.create' (C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\app\domain\catalog\create.py) |
| 6.1 GREEN | 0 | 1 passed, 18 deselected in 0.17s | — |
| 6.2 RED empty | 1 | 1 failed, 19 deselected in 0.33s | E       AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='', default_duration_min=45, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre de la prestación no p...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.2 GREEN | 0 | 1 passed, 19 deselected in 0.15s | — |
| 6.2 initially green | 0 | 2 passed, 20 deselected in 0.20s | — |
| 6.2 whitespace mutation | 1 | 1 failed, 1 passed, 20 deselected in 0.31s | E       AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d2'), name='   ', default_duration_min=45, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre de la prestación no p...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.2 whitespace mutation restored | 0 | 2 passed, 20 deselected in 0.13s | — |
| 6.3 RED exact | 1 | 1 failed, 22 deselected in 0.29s | E       assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d2'), name='Limpieza', default_duration_min=45, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe una prestació...ieza".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.3 GREEN exact | 0 | 1 passed, 22 deselected in 0.27s | — |
| 6.3 case_and_spaces initially green | 0 | 1 passed, 23 deselected in 0.20s | — |
| 6.3 internal_spaces initially green | 0 | 1 passed, 24 deselected in 0.21s | — |
| 6.3 normalize only candidate mutation | 1 | 1 failed, 24 deselected in 0.25s | E       assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d2'), name='  Limpieza  ', default_duration_min=45, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe una prestació...ieza".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.3 normalize only candidate mutation restored | 0 | 1 passed, 24 deselected in 0.13s | — |
| 6.3 display spaces mutation | 1 | 1 failed, 24 deselected in 0.27s | E       assert Rejected(viol...erval=None),)) == Rejected(viol...erval=None),)) |
| 6.3 display spaces mutation restored | 0 | 1 passed, 24 deselected in 0.12s | — |
| 6.3 accents initially green | 0 | 1 passed, 25 deselected in 0.21s | — |
| 6.3 accents mutation | 1 | 1 failed, 25 deselected in 0.24s | E       assert Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe una prestació...cion".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d2'), name='Extraccion', default_duration_min=60, active=True)) |
| 6.3 accents mutation restored | 0 | 1 passed, 25 deselected in 0.17s | — |
| 6.3 inactive initially green | 0 | 1 passed, 26 deselected in 0.17s | — |
| 6.3 active filter mutation | 1 | 1 failed, 26 deselected in 0.26s | E       assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d2'), name='Limpieza', default_duration_min=45, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_NAME: 'DUPLICATE_NAME'>, message='Ya existe una prestació...ieza".', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.3 active filter mutation restored | 0 | 1 passed, 26 deselected in 0.11s | — |
| 6.3 multiple initially green | 0 | 2 passed, 27 deselected in 0.18s | — |
| 6.3 repeated violations mutation | 1 | 2 failed, 27 deselected in 0.24s | E       assert Rejected(viol...terval=None))) == Rejected(viol...erval=None),)) |
| 6.3 repeated violations mutation restored | 0 | 2 passed, 27 deselected in 0.13s | — |
| 6.4 RED duration subject | 1 | 1 failed, 29 deselected in 0.29s | E       AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=7, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.4 GREEN 7 | 0 | 1 passed, 29 deselected in 0.17s | — |
| 6.4 GREEN 0 | 0 | 1 passed, 30 deselected in 0.19s | — |
| 6.4 GREEN negative_5 | 0 | 1 passed, 31 deselected in 0.22s | — |
| 6.4 GREEN 485 | 0 | 1 passed, 32 deselected in 0.22s | — |
| 6.4 GREEN 487 | 0 | 1 passed, 33 deselected in 0.19s | — |
| 6.4 boundary 5 initially green | 0 | 1 passed, 34 deselected in 0.20s | — |
| 6.4 lower bound mutation | 1 | 1 failed, 34 deselected in 0.30s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=5, active=True)) |
| 6.4 lower bound mutation restored | 0 | 1 passed, 34 deselected in 0.12s | — |
| 6.4 boundary 480 initially green | 0 | 1 passed, 35 deselected in 0.22s | — |
| 6.4 upper bound mutation | 1 | 1 failed, 35 deselected in 0.28s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=480, active=True)) |
| 6.4 upper bound mutation restored | 0 | 1 passed, 35 deselected in 0.12s | — |
| 6.4 invalid triangulation sensitivity | 1 | 5 failed, 31 deselected in 0.42s | E       AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=7, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.4 invalid triangulation sensitivity restored | 0 | 5 passed, 31 deselected in 0.13s | — |
| 6.4a regression 7 | 0 | 1 passed in 0.11s | — |
| 6.4a regression 0 | 0 | 1 passed, 1 deselected in 0.12s | — |
| 6.4a regression negative_5 | 0 | 1 passed, 2 deselected in 0.11s | — |
| 6.4a regression 485 | 0 | 1 passed, 3 deselected in 0.12s | — |
| 6.4a regression 487 | 0 | 1 passed, 4 deselected in 0.12s | — |
| 6.4a default subject mutation | 1 | 5 failed in 0.27s | E       AssertionError: assert [Violation(co...nterval=None)] == [Violation(co...nterval=None)] |
| 6.4a default subject mutation restored | 0 | 5 passed in 0.10s | — |
| 6.5 missing duration mutation | 1 | 5 failed, 31 deselected in 0.28s | E       AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=7, active=True)) == Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 6.5 missing duration mutation restored | 0 | 5 passed, 31 deselected in 0.14s | — |
| 6.5 missing explicit subject mutation | 1 | 5 failed, 31 deselected in 0.32s | E       AssertionError: assert Rejected(viol...erval=None),)) == Rejected(viol...erval=None),)) |
| 6.5 missing explicit subject mutation restored | 0 | 5 passed, 31 deselected in 0.13s | — |
| 6.5 default subject mutation | 1 | 5 failed in 0.28s | E       AssertionError: assert [Violation(co...nterval=None)] == [Violation(co...nterval=None)] |
| 6.5 default subject mutation restored | 0 | 5 passed in 0.24s | — |
| 6.5 restored suite | 0 | 425 passed in 1.83s | — |
| 6.5 mypy | 0 | Success: no issues found in 39 source files | — |
| 6.6 refactor suite | 0 | 425 passed in 2.13s | — |
| 6.6 mypy | 0 | Success: no issues found in 39 source files | — |
| 6.6 refactor parametrized regressions | 0 | 5 passed in 0.14s | — |
| 6.6 parametrized mypy | 0 | Success: no issues found in 39 source files | — |
| 7.1 RED | 1 | 1 failed, 36 deselected in 0.33s | E       ImportError: cannot import name 'create_patient' from 'app.domain.catalog.create' (C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\app\domain\catalog\create.py) |
| 7.1 GREEN dots | 0 | 1 passed, 36 deselected in 0.15s | — |
| 7.1 without dots initially green | 0 | 1 passed, 37 deselected in 0.25s | — |
| 7.1 normalized copy mutation | 1 | 2 failed, 36 deselected in 0.32s | E       AssertionError: assert Ok(entity=Pat...surance=None)) == Ok(entity=Pat...surance=None)) |
| 7.1 normalized copy mutation restored | 0 | 2 passed, 36 deselected in 0.15s | — |
| 7.2 RED empty | 1 | 1 failed, 38 deselected in 0.34s | E       AssertionError: assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='', dni='30111222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre del paciente no puede...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.2 GREEN | 0 | 1 passed, 38 deselected in 0.15s | — |
| 7.2 blank initially green | 0 | 1 passed, 39 deselected in 0.25s | — |
| 7.2 blank guard mutation | 1 | 1 failed, 39 deselected in 0.25s | E       AssertionError: assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='   ', dni='30111222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.EMPTY_NAME: 'EMPTY_NAME'>, message='El nombre del paciente no puede...vacío.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.2 blank guard mutation restored | 0 | 1 passed, 39 deselected in 0.15s | — |
| 7.2 repeated name initially green | 0 | 1 passed, 40 deselected in 0.26s | — |
| 7.2 free text initially green | 0 | 2 passed, 41 deselected in 0.26s | — |
| 7.2 values mutation | 1 | 3 failed, 40 deselected in 0.32s | E       AssertionError: assert Ok(entity=Pat...surance=None)) == Ok(entity=Pat...surance=None)) |
| 7.2 values mutation restored | 0 | 3 passed, 40 deselected in 0.14s | — |
| 7.3 RED invalid | 1 | 1 failed, 43 deselected in 0.37s | E       assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='Ana Pérez', dni='30-111-222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.INVALID_DNI: 'INVALID_DNI'>, message='El DNI no es válido (se recib...untos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.3 GREEN invalid | 0 | 1 passed, 43 deselected in 0.20s | — |
| 7.3 six initially green | 0 | 1 passed, 44 deselected in 0.52s | — |
| 7.3 nine initially green | 0 | 1 passed, 45 deselected in 0.26s | — |
| 7.3 letters initially green | 0 | 1 passed, 46 deselected in 0.23s | — |
| 7.3 empty initially green | 0 | 1 passed, 47 deselected in 0.25s | — |
| 7.3 blank initially green | 0 | 1 passed, 48 deselected in 0.27s | — |
| 7.3 validation missing mutation | 1 | 6 failed, 43 deselected in 0.48s | E       assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='Ana Pérez', dni='30-111-222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.INVALID_DNI: 'INVALID_DNI'>, message='El DNI no es válido (se recib...untos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.3 validation missing mutation restored | 0 | 6 passed, 43 deselected in 0.13s | — |
| 7.4 seven initially green | 0 | 1 passed, 49 deselected in 0.24s | — |
| 7.4 outer_spaces initially green | 0 | 1 passed, 50 deselected in 0.33s | — |
| 7.4 inner_spaces initially green | 0 | 1 passed, 51 deselected in 0.27s | — |
| 7.4 eight only mutation | 1 | 1 failed, 51 deselected in 0.29s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DNI: 'INVALID_DNI'>, message='El DNI no es válido (se recib...untos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='Ana Pérez', dni='3111222', phone=None, health_insurance=None)) |
| 7.4 eight only mutation restored | 0 | 1 passed, 51 deselected in 0.13s | — |
| 7.4 spaces mutation | 1 | 2 failed, 50 deselected in 0.27s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DNI: 'INVALID_DNI'>, message='El DNI no es válido (se recib...untos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='Ana Pérez', dni='30111222', phone=None, health_insurance=None)) |
| 7.4 spaces mutation restored | 0 | 2 passed, 50 deselected in 0.13s | — |
| 7.5 RED duplicate | 1 | 1 failed, 52 deselected in 0.37s | E       AssertionError: assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c2'), full_name='Ana Pérez', dni='30111222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_DNI: 'DUPLICATE_DNI'>, message='Ya existe un paciente con...1.222.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.5 GREEN duplicate | 0 | 1 passed, 52 deselected in 0.21s | — |
| 7.5 candidate_dots initially green | 0 | 1 passed, 53 deselected in 0.26s | — |
| 7.5 existing_dots initially green | 0 | 1 passed, 54 deselected in 0.28s | — |
| 7.5 seven initially green | 0 | 1 passed, 55 deselected in 0.26s | — |
| 7.5 order initially green | 0 | 2 passed, 56 deselected in 0.32s | — |
| 7.5 normalized input mutation | 1 | 4 failed, 54 deselected in 0.34s | E       AssertionError: assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c2'), full_name='Ana Pérez', dni='30111222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_DNI: 'DUPLICATE_DNI'>, message='Ya existe un paciente con...1.222.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.5 normalized input mutation restored | 0 | 4 passed, 54 deselected in 0.15s | — |
| 7.6 guard initially green | 0 | 1 passed, 58 deselected in 0.31s | — |
| 7.6 invalid duplicate guard mutation | 1 | 1 failed, 58 deselected in 0.32s | E       assert Rejected(viol...terval=None))) == Rejected(viol...erval=None),)) |
| 7.6 invalid duplicate guard mutation restored | 0 | 1 passed, 58 deselected in 0.12s | — |
| 7.6 raw comparison mutation | 1 | 1 failed, 58 deselected in 0.27s | E       AssertionError: assert Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c2'), full_name='Ana Pérez', dni='30111222', phone=None, health_insurance=None)) == Rejected(violations=(Violation(code=<ViolationCode.DUPLICATE_DNI: 'DUPLICATE_DNI'>, message='Ya existe un paciente con...1.222.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) |
| 7.6 raw comparison mutation restored | 0 | 1 passed, 58 deselected in 0.13s | — |
| 7.6 missing thousands mutation | 1 | 2 failed, 57 deselected in 0.29s | E       AssertionError: assert Rejected(viol...erval=None),)) == Rejected(viol...erval=None),)) |
| 7.6 missing thousands mutation restored | 0 | 2 passed, 57 deselected in 0.13s | — |
| 7.6 restored suite | 0 | 448 passed in 1.73s | — |
| 7.7 refactor suite | 0 | 448 passed in 1.75s | — |
| 7.7 mypy | 0 | Success: no issues found in 40 source files | — |
| 8.1 invalid together initially green | 0 | 1 passed, 59 deselected in 0.27s | — |
| 8.1 empty and duplicate initially green | 0 | 1 passed, 60 deselected in 0.29s | — |
| 8.1 early return mutation | 1 | 2 failed, 59 deselected in 0.30s | E       AssertionError: assert Rejected(viol...erval=None),)) == Rejected(viol...terval=None))) |
| 8.1 early return mutation restored | 0 | 2 passed, 59 deselected in 0.19s | — |
| 8.2 duplicate duration initially green | 0 | 1 passed, 61 deselected in 0.30s | — |
| 8.2 empty duration initially green | 0 | 1 passed, 62 deselected in 0.27s | — |
| 8.2 order mutation | 1 | 2 failed, 61 deselected in 0.30s | E       assert Rejected(viol...terval=None))) == Rejected(viol...terval=None))) |
| 8.2 order mutation restored | 0 | 2 passed, 61 deselected in 0.13s | — |
| 8.3 empty initially green | 0 | 1 passed, 63 deselected in 0.28s | — |
| 8.3 name initially green | 0 | 1 passed, 64 deselected in 0.30s | — |
| 8.3 invalid initially green | 0 | 1 passed, 65 deselected in 0.40s | — |
| 8.3 dni initially green | 0 | 1 passed, 66 deselected in 0.34s | — |
| 8.3 reference metadata mutation | 1 | 1 failed, 3 passed, 63 deselected in 0.33s | E       AssertionError: assert (Violation(co...terval=None),) == (Violation(co...terval=None),) |
| 8.3 reference metadata mutation restored | 0 | 4 passed, 63 deselected in 0.15s | — |
| 8.4 suite | 0 | 456 passed in 1.71s | — |
| 8.4 mypy | 0 | Success: no issues found in 40 source files | — |
| 9.1 RED deactivate | 1 | 1 failed, 67 deselected in 0.39s | E       ModuleNotFoundError: No module named 'app.domain.catalog.activation' |
| 9.1 GREEN professional | 0 | 1 passed, 67 deselected in 0.15s | — |
| 9.1 GREEN chair | 0 | 1 passed, 68 deselected in 0.30s | — |
| 9.1 GREEN service | 0 | 1 passed, 69 deselected in 0.32s | — |
| 9.1 copy sensitivity | 1 | 3 failed, 67 deselected in 0.30s | E       AssertionError: assert Professional(..., active=True) == Professional(... active=False) |
| 9.1 copy sensitivity restored | 0 | 3 passed, 67 deselected in 0.13s | — |
| 9.2 RED reactivate | 1 | 1 failed, 70 deselected in 0.47s | E       ImportError: cannot import name 'reactivate' from 'app.domain.catalog.activation' (C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\app\domain\catalog\activation.py) |
| 9.2 GREEN professional | 0 | 1 passed, 70 deselected in 0.15s | — |
| 9.2 GREEN chair | 0 | 1 passed, 71 deselected in 0.31s | — |
| 9.2 GREEN service | 0 | 1 passed, 72 deselected in 0.33s | — |
| 9.2 copy sensitivity | 1 | 3 failed, 70 deselected in 0.32s | E       AssertionError: assert Professional(... active=False) == Professional(..., active=True) |
| 9.2 copy sensitivity restored | 0 | 3 passed, 70 deselected in 0.13s | — |
| 9.3 deactivate professional initially green | 0 | 1 passed, 73 deselected in 0.32s | — |
| 9.3 deactivate chair initially green | 0 | 1 passed, 74 deselected in 0.34s | — |
| 9.3 deactivate service initially green | 0 | 1 passed, 75 deselected in 0.38s | — |
| 9.3 toggle deactivate mutation | 1 | 3 failed, 73 deselected in 0.36s | E       AssertionError: assert Professional(..., active=True) == Professional(... active=False) |
| 9.3 toggle deactivate mutation restored | 0 | 3 passed, 73 deselected in 0.19s | — |
| 9.3 reactivate professional initially green | 0 | 1 passed, 76 deselected in 0.34s | — |
| 9.3 reactivate chair initially green | 0 | 1 passed, 77 deselected in 0.38s | — |
| 9.3 reactivate service initially green | 0 | 1 passed, 78 deselected in 0.42s | — |
| 9.3 toggle reactivate mutation | 1 | 3 failed, 76 deselected in 0.36s | E       AssertionError: assert Professional(... active=False) == Professional(..., active=True) |
| 9.3 toggle reactivate mutation restored | 0 | 3 passed, 76 deselected in 0.21s | — |
| 9.4 return original mutation | 1 | 3 failed, 76 deselected in 0.31s | E       AssertionError: assert Professional(..., active=True) == Professional(... active=False) |
| 9.4 return original mutation restored | 0 | 3 passed, 76 deselected in 0.15s | — |
| 9.4 suite | 0 | 468 passed in 1.82s | — |
| 9.4 mypy | 0 | Success: no issues found in 41 source files | — |
| 9.5 refactor activation | 0 | 12 passed, 67 deselected in 0.12s | — |
| 9.5 mypy | 0 | Success: no issues found in 41 source files | — |
| 10.1 professional regression initially green | 0 | 1 passed in 0.15s | — |
| 10.1 chair regression initially green | 0 | 1 passed, 1 deselected in 0.15s | — |
| 10.1 service regression initially green | 0 | 1 passed, 2 deselected in 0.14s | — |
| 10.1 activation sensitivity | 1 | 3 failed in 0.28s | E       AssertionError: assert True is False |
| 10.1 activation sensitivity restored | 0 | 3 passed in 0.17s | — |
| 10.1 previous agenda regression | 0 | 182 passed in 0.61s | — |
| 10.2 professional initially green | 0 | 1 passed, 3 deselected in 0.16s | — |
| 10.2 chair initially green | 0 | 1 passed, 4 deselected in 0.17s | — |
| 10.2 service initially green | 0 | 1 passed, 5 deselected in 0.28s | — |
| 10.2 inactive operation mutation | 1 | 3 failed, 3 deselected in 0.34s | E       AssertionError: assert Ok(appointment=Appointment(id=UUID('00000000-0000-0000-0000-0000000000f1'), patient_id=UUID('00000000-0000-0000-0000-0...tetime.datetime(2026, 10, 20, 13, 30, tzinfo=datetime.timezone.utc), status=<AppointmentStatus.RESERVED: 'reservado'>)) == Rejected(violations=(Violation(code=<ViolationCode.INACTIVE_REFERENCE: 'INACTIVE_REFERENCE'>, message='El profesional ..., reference_kind=<ReferenceKind.PROFESSIONAL: 'PROFESSIONAL'>, conflicting_block_id=None, conflicting_interval=None),)) |
| 10.2 inactive operation mutation restored | 0 | 3 passed, 3 deselected in 0.15s | — |
| 10.3 initially green | 0 | 1 passed, 6 deselected in 0.17s | — |
| 10.3 reactivation mutation | 1 | 1 failed, 6 deselected in 0.33s | E       AssertionError: assert False |
| 10.3 reactivation mutation restored | 0 | 1 passed, 6 deselected in 0.14s | — |
| 10.3 suite | 0 | 475 passed in 1.79s | — |
| 10.3 mypy | 0 | Success: no issues found in 42 source files | — |
| 11.1 RED | 1 | 1 failed in 0.26s | E       ImportError: cannot import name 'demo_data' from 'app' (C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\backend\app\__init__.py) |
| 11.1 GREEN | 0 | 1 passed in 0.10s | — |
| 11.2 professional initially green | 0 | 1 passed, 1 deselected in 0.12s | — |
| 11.2 chair initially green | 0 | 1 passed, 2 deselected in 0.13s | — |
| 11.2 service initially green | 0 | 1 passed, 3 deselected in 0.14s | — |
| 11.2 patient initially green | 0 | 1 passed, 4 deselected in 0.12s | — |
| 11.2 invalid demo duration mutation | 1 | 1 failed, 4 deselected in 0.28s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DURATION: 'INVALID_DURATION'>, message='La duración de la p...nutos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000d1'), name='Limpieza', default_duration_min=0, active=True)) |
| 11.2 invalid demo duration mutation restored | 0 | 1 passed, 4 deselected in 0.11s | — |
| 11.2 invalid demo dni mutation | 1 | 1 failed, 4 deselected in 0.27s | E       AssertionError: assert Rejected(violations=(Violation(code=<ViolationCode.INVALID_DNI: 'INVALID_DNI'>, message='El DNI no es válido (se recib...untos.', conflicting_appointment_id=None, reference_kind=None, conflicting_block_id=None, conflicting_interval=None),)) == Ok(entity=Patient(id=UUID('00000000-0000-0000-0000-0000000000c1'), full_name='Ana Pérez', dni='30-111-222', phone=None, health_insurance=None)) |
| 11.2 invalid demo dni mutation restored | 0 | 1 passed, 4 deselected in 0.10s | — |
| 11.3 real domain guard | 0 | 1 passed in 0.14s | — |
| 11.3 synthetic mutation expected detection | 0 | 1 passed, 1 deselected in 0.14s | — |
| 11.3 synthetic negative control | 1 | 1 failed, 1 deselected in 0.21s | E       AssertionError: assert [] == [(WindowsPath...p.demo_data')] |
| 11.3 synthetic negative control restored | 0 | 1 passed, 1 deselected in 0.16s | — |
| 11.3 guards complete | 0 | 3 passed in 0.19s | — |
| 11.3 existing guard sensitivity | 0 | 23 passed in 0.66s | — |
| 11.4 suite | 0 | 483 passed in 2.01s | — |
| 11.4 mypy | 0 | Success: no issues found in 45 source files | — |
| Final readability refactor create | 0 | 79 passed in 0.29s | — |
| Final readability refactor names | 0 | 79 passed in 0.29s | — |
| Final readability refactor dni | 0 | 79 passed in 0.28s | — |
| 5.2 precise duplicate guard mutation | 1 | 2 failed, 77 deselected in 0.45s | E       assert Rejected(viol...terval=None))) == Rejected(viol...erval=None),)) |
| 5.2 precise duplicate guard mutation restored | 0 | 2 passed, 77 deselected in 0.16s | — |
| 5.3 precise presentation strip mutation | 1 | 1 failed, 78 deselected in 0.31s | E       assert Rejected(viol...erval=None),)) == Rejected(viol...erval=None),)) |
| 5.3 precise presentation strip mutation restored | 0 | 1 passed, 78 deselected in 0.15s | — |

## Mensajes exactos del código

```text
El nombre del profesional no puede estar vacío.
El nombre del sillón no puede estar vacío.
El nombre de la prestación no puede estar vacío.
El nombre del paciente no puede estar vacío.
Ya existe un sillón con el nombre "Sillón 1".
Ya existe un sillón con el nombre "SILLÓN 1".
Ya existe una prestación con el nombre "Limpieza".
Ya existe una prestación con el nombre "CONTROL DE ORTODONCIA".
El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.
Ya existe un paciente con el DNI 30.111.222.
Ya existe un paciente con el DNI 3.111.222.
La duración de la prestación no es válida (se recibió 0 minutos): debe ser mayor que cero minutos.
La duración de la prestación no es válida (se recibió -5 minutos): debe ser mayor que cero minutos.
La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.
La duración de la prestación no es válida (se recibió 485 minutos): no puede superar los 480 minutos.
La duración de la prestación no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos.
```

La plantilla de INVALID_DNI conserva también literalmente los recibidos "111222", "301112222", "30111A22", "" y "   ". El nombre duplicado usa espacios colapsados y conserva mayúsculas/tildes. El DNI duplicado se muestra con puntos de miles. El sujeto predeterminado de duración conserva exactamente «La duración del turno» con las mismas cinco razones y valores de C-03; están probados los cinco textos completos en test_duration.py y la agenda previa continúa en verde. INACTIVE_REFERENCE mantiene sus tres textos originales con ids, sin agregar nombres.

## Desvíos del apply

1. Varios casos de triangulación y regresión pasaron de entrada por composición de reglas compartidas o contratos existentes (opcionales del modelo, preservación de nombres, tildes, normalización, idempotencia y agenda). Se registraron como verdes iniciales y se comprobó sensibilidad con mutaciones restauradas, sin borrar tests ni fingir RED históricos. La tabla TDD y el registro detallan cada salida.
2. La primera mutación de 5.2 agregó un duplicado espurio porque todavía no existía la regla de duplicado, que se implementó después en 5.3. Al cierre se precisó con la guarda real: quitarla produjo dos fallos; restaurada, dos verdes. La primera mutación de strip en 5.3 afectaba también la clave de comparación; se añadió la mutación precisa de presentación, que produjo un fallo de texto y se restauró.
3. La tarea 10.1 ya pasaba: desactivar no recibe turnos. No se alteró el turno ni sus expectativas para falsear un RED; se conservó como regresión verde y se comprobó la operación con una mutación que devolvía el recurso aún activo (tres fallos por estado). La sensibilidad de la copia y el rechazo de nuevos turnos se verificaron además en 9.4 y 10.2.
4. La prohibición más reciente de importar demo_data desde el dominio prevalece sobre la mutación literal de 11.3. Se usó un archivo sintético de catálogo bajo tmp_path, parseado estáticamente y nunca importado: la guardia detectó app.demo_data. El control negativo con import permitido produjo un fallo, restaurado. El dominio real nunca recibió ese import y sus guardias quedaron vacías.
5. El transporte inicial PowerShell → Python requirió UTF-8 explícito. Se corrigieron los acentos de texto nuevo y la captura con PYTHONIOENCODING; una primera captura de la mutación de 2.4 falló al decodificar, su finally restauró el archivo y se repitió con captura válida. No se cambió ninguna expectativa previa. Las regresiones de duración se añadieron una por ciclo y luego se refactorizaron a un test parametrizado de cinco casos; cinco verdes después. La legibilidad de tres módulos se revisó al final, ejecutando los 79 tests de catálogo después de cada refactor.
6. El chequeo de trazabilidad inicial usó una expresión demasiado estrecha para nodos parametrizados con espacios y contó 456 nodos; se corrigió el parser y se verificaron los 483 PASSED, sin modificar tests. La tabla final contiene las 63 filas y todas sus variantes.

## Estado final

**Apply completo: 57/57 tareas; trazabilidad 63/63 escenarios.** Conteo con `grep -F -c -- '- [x]'` y total con `grep -E -c -- '^- \[[ x]\]'`: 57 y 57; OpenSpec `state: all_done`. `git diff --check` limpio y ningún archivo staged. Sin cambios de KB, CHANGES, specs principales, AGENTS, CLAUDE, estado del orquestador ni otros changes. No se hizo stage, commit, push ni archive.
