# Verificación de C-20 — api-catalogos-y-pacientes

## Aprobación de la autora (governance BAJO)

> Aprobado por la autora según propuesta y respuestas del explore (D1 a D15).
> Implementación completada con Strict TDD en todos los niveles.

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 15/15 en [tasks.md](../../openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/tasks.md).
- Suite por defecto: [pytest-C-20.txt](pytest-C-20.txt) (850 passed, 360 deselected).
- Integración: [pytest-integration-C-20.txt](pytest-integration-C-20.txt) (360 passed, 850 deselected).
- `mypy --strict app tests`: [mypy-C-20.txt](mypy-C-20.txt) (Success: 148 source files).
- Mutaciones: [mutaciones-C-20.txt](mutaciones-C-20.txt) (15/15 mutaciones hicieron fallar su test; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-20.txt](trazabilidad-C-20.txt) (108 escenarios recolectados, 0 problemas).
- Validación OpenSpec: [validate-C-20.txt](validate-C-20.txt) (`openspec validate --strict` válido).
- Línea de base: [baseline-C-20.txt](baseline-C-20.txt) (826 passed / 244 deselected; 244 integración; 130 archivos mypy).

## Verificación manual por HTTP (2026-11-07)

Se ejecutó [http-C-20.sh](http-C-20.sh) contra la API con PostgreSQL 16 real y el seed ficticio; la salida cruda está en [http-C-20.txt](http-C-20.txt).

| # | Título | Código HTTP | Resultado |
|---|---|---|---|
| 1 | recepcion lista profesionales (200) | 200 | Lista de profesionales activos ordenados (`Dr. Martín Sosa`, `Dra. Laura Quiroga`, `Dra. Paula Ben...`) |
| 2 | odontologo lista sillones (200) | 200 | Lista de 3 sillones (`Sillón 1`, `Sillón 2`, `Sillón 3`) |
| 3 | odontologo lista prestaciones (200) | 200 | Lista de prestaciones (`Blanqueamiento`, `Control`, `Extracción`, …) |
| 4 | admin crea profesional Dr. Ficticio Nuevo (201) | 201 | Profesional creado (`fullName: "Dr. Ficticio Nuevo"`, `licenseNumber: "MP-9999"`, `active: true`) |
| 5 | recepcion intenta crear profesional (403) | 403 | `FORBIDDEN_OPERATION`: `"No tiene permiso para crear profesionales."` |
| 6 | admin edita el profesional (200) | 200 | `fullName: "Dr. Ficticio Editado"`, `licenseNumber: "MP-9999"`, `active: true` |
| 7 | admin desactiva el profesional (200, active false) | 200 | `active: false` |
| 8 | admin reactiva el profesional (200, active true) | 200 | `active: true` |
| 9 | profesional inexistente (404) | 404 | `code="NOT_FOUND"`, `"Profesional no encontrado."` |
| 10 | admin crea Sillon 4 (201) | 201 | Sillón creado (`name: "Sillón 4"`, `active: true`) |
| 11 | sillon con nombre repetido, otras mayusculas (409 DUPLICATE_NAME) | 409 | `DUPLICATE_NAME`: `"Ya existe un sillón con el nombre \"sillón 4\"."` |
| 12 | admin crea prestacion Sellado ficticio 45 min (201) | 201 | Prestación creada (`name: "Sellado ficticio"`, `defaultDurationMin: 45`, `active: true`) |
| 12b | prestacion repetida Blanqueamiento, ya existe en el seed (409 DUPLICATE_NAME) | 409 | `DUPLICATE_NAME`: `"Ya existe una prestación con el nombre \"Blanqueamiento\"."` |
| 13 | prestacion con duracion 0 (422) | 422 | `INVALID_DURATION`: `"La duración de la prestación debe ser positiva: se recibió 0 min."` |
| 14 | recepcion crea paciente ficticio (201) | 201 | Paciente creado (`fullName: "Paciente Ficticio"`, `dni: "40111222"`, `phone: "261-0000000"`, `insurance: "OSDE"`) |
| 15 | paciente con DNI repetido (409 DUPLICATE_DNI) | 409 | `DUPLICATE_DNI`: `"Ya existe un paciente con el DNI 40.111.222."` |
| 16 | paciente con DNI de 6 digitos (422) | 422 | `INVALID_DNI`: `"El DNI del paciente debe tener 7 u 8 dígitos: se recibió \"123456\"."` |
| 17 | odontologo intenta crear paciente (403) | 403 | `FORBIDDEN_OPERATION`: `"No tiene permiso para crear pacientes."` |
| 18 | buscar paciente por nombre 'pérez' (200) | 200 | 1 paciente (`fullName: "Ana Pérez"`, `dni: "30111222"`) |
| 19 | buscar paciente por prefijo de DNI '401' (200) | 200 | 1 paciente (`fullName: "Paciente Ficticio"`, `dni: "40111222"`) |
| 20 | recepcion edita el telefono del paciente (200) | 200 | `phone: "261-1111111"` |
| 21 | campo extra en el paciente (400) | 400 | `errors`: `field="historiaClinica"`, `type="extra_forbidden"`, `"Dato inválido."` |
| 22 | sin token (401) | 401 | `code="INVALID_TOKEN"`, `"La sesión venció o no es válida. Inicie sesión de nuevo."` |

## Artefactos

- [proposal.md](../../openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/proposal.md)
- [design.md](../../openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/design.md)
- [tasks.md](../../openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/tasks.md)
- [spec.md (catalog-and-patients)](../../openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/specs/catalog-and-patients/spec.md)

## Línea de base

Antes de escribir código: 826 passed (y 244 deselected); 244 passed en integración; `mypy` Success en 130 archivos (documentado en `baseline-C-20.txt`).

## Trazabilidad

Cada escenario de la spec delta `catalog-and-patients` mapeado a un test unitario o de integración. `trazabilidad-C-20.py` comprueba con `pytest --collect-only` que cada test existe.

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | catalog-and-patients | Endpoints de profesionales | Alta exitosa de profesional con matrícula responde 201 | `tests/integration/test_api_professionals.py::test_create_professional_with_license_responds_201` |
| 2 | catalog-and-patients | Endpoints de profesionales | Edición exitosa de profesional responde 200 | `tests/integration/test_api_professionals.py::test_update_professional_responds_200` |
| 3 | catalog-and-patients | Endpoints de profesionales | Edición de profesional conservando su propio nombre responde 200 | `tests/integration/test_api_professionals.py::test_update_professional_conserving_own_name_responds_200` |
| 4 | catalog-and-patients | Endpoints de profesionales | Edición de profesional inexistente responde 404 | `tests/integration/test_api_professionals.py::test_update_professional_nonexistent_responds_404` |
| 5 | catalog-and-patients | Endpoints de profesionales | Listado de profesionales con filtro active verdadero | `tests/integration/test_api_professionals.py::test_list_professionals_with_active_filter_true` |
| 6 | catalog-and-patients | Endpoints de profesionales | Listado de profesionales sin filtro incluye inactivos en orden alfabético | `tests/integration/test_api_professionals.py::test_list_professionals_without_filter_includes_inactive_alphabetical` |
| 7 | catalog-and-patients | Endpoints de profesionales | Recepción lista profesionales y responde 200 | `tests/integration/test_api_professionals.py::test_reception_lists_professionals_responds_200` |
| 8 | catalog-and-patients | Endpoints de profesionales | El odontólogo lista profesionales y responde 200 | `tests/integration/test_api_professionals.py::test_doctor_lists_professionals_responds_200` |
| 9 | catalog-and-patients | Endpoints de profesionales | Detalle de profesional existente responde 200 | `tests/integration/test_api_professionals.py::test_detail_professional_existing_responds_200` |
| 10 | catalog-and-patients | Endpoints de profesionales | Detalle de profesional inexistente responde 404 | `tests/integration/test_api_professionals.py::test_detail_professional_nonexistent_responds_404` |
| 11 | catalog-and-patients | Endpoints de profesionales | Consulta de profesionales sin token responde 401 | `tests/integration/test_api_professionals.py::test_consult_professionals_without_token_responds_401` |
| 12 | catalog-and-patients | Endpoints de profesionales | Alta de profesional rechazada para rol recepción con 403 | `tests/integration/test_api_professionals.py::test_create_professional_rejected_for_reception_403` |
| 13 | catalog-and-patients | Endpoints de profesionales | Alta de profesional rechazada para rol odontólogo con 403 | `tests/integration/test_api_professionals.py::test_create_professional_rejected_for_doctor_403` |
| 14 | catalog-and-patients | Endpoints de profesionales | Edición de profesional rechazada para rol recepción con 403 | `tests/integration/test_api_professionals.py::test_update_professional_rejected_for_reception_403` |
| 15 | catalog-and-patients | Endpoints de profesionales | Edición de profesional rechazada para rol odontólogo con 403 | `tests/integration/test_api_professionals.py::test_update_professional_rejected_for_doctor_403` |
| 16 | catalog-and-patients | Endpoints de profesionales | Alta de profesional con nombre vacío responde 422 | `tests/integration/test_api_professionals.py::test_create_professional_empty_name_responds_422` |
| 17 | catalog-and-patients | Endpoints de profesionales | Alta de profesional con cuerpo malformado responde 400 | `tests/integration/test_api_professionals.py::test_create_professional_malformed_body_responds_400` |
| 18 | catalog-and-patients | Endpoints de sillones | Alta exitosa de sillón responde 201 | `tests/integration/test_api_chairs.py::test_create_chair_responds_201` |
| 19 | catalog-and-patients | Endpoints de sillones | Edición exitosa de sillón responde 200 | `tests/integration/test_api_chairs.py::test_update_chair_responds_200` |
| 20 | catalog-and-patients | Endpoints de sillones | Edición de sillón conservando su propio nombre responde 200 | `tests/integration/test_api_chairs.py::test_update_chair_conserving_own_name_responds_200` |
| 21 | catalog-and-patients | Endpoints de sillones | Edición de sillón con el nombre de otro sillón responde 409 | `tests/integration/test_api_chairs.py::test_update_chair_with_name_of_another_responds_409` |
| 22 | catalog-and-patients | Endpoints de sillones | Edición de sillón inexistente responde 404 | `tests/integration/test_api_chairs.py::test_update_chair_nonexistent_responds_404` |
| 23 | catalog-and-patients | Endpoints de sillones | Listado de sillones con filtro active verdadero | `tests/integration/test_api_chairs.py::test_list_chairs_with_active_filter_true` |
| 24 | catalog-and-patients | Endpoints de sillones | Listado de sillones con filtro active falso devuelve solo inactivos | `tests/integration/test_api_chairs.py::test_list_chairs_with_active_filter_false_returns_only_inactive` |
| 25 | catalog-and-patients | Endpoints de sillones | Listado de sillones sin filtro incluye inactivos en orden alfabético | `tests/integration/test_api_chairs.py::test_list_chairs_without_filter_includes_inactive_alphabetical` |
| 26 | catalog-and-patients | Endpoints de sillones | Recepción lista sillones y responde 200 | `tests/integration/test_api_chairs.py::test_reception_lists_chairs_responds_200` |
| 27 | catalog-and-patients | Endpoints de sillones | El odontólogo lista sillones y responde 200 | `tests/integration/test_api_chairs.py::test_doctor_lists_chairs_responds_200` |
| 28 | catalog-and-patients | Endpoints de sillones | Detalle de sillón existente responde 200 | `tests/integration/test_api_chairs.py::test_detail_chair_existing_responds_200` |
| 29 | catalog-and-patients | Endpoints de sillones | Detalle de sillón inexistente responde 404 | `tests/integration/test_api_chairs.py::test_detail_chair_nonexistent_responds_404` |
| 30 | catalog-and-patients | Endpoints de sillones | Consulta de sillones sin token responde 401 | `tests/integration/test_api_chairs.py::test_consult_chairs_without_token_responds_401` |
| 31 | catalog-and-patients | Endpoints de sillones | Alta de sillón rechazada para rol recepción con 403 | `tests/integration/test_api_chairs.py::test_create_chair_rejected_for_reception_403` |
| 32 | catalog-and-patients | Endpoints de sillones | Alta de sillón rechazada para rol odontólogo con 403 | `tests/integration/test_api_chairs.py::test_create_chair_rejected_for_doctor_403` |
| 33 | catalog-and-patients | Endpoints de sillones | Edición de sillón rechazada para rol recepción con 403 | `tests/integration/test_api_chairs.py::test_update_chair_rejected_for_reception_403` |
| 34 | catalog-and-patients | Endpoints de sillones | Edición de sillón rechazada para rol odontólogo con 403 | `tests/integration/test_api_chairs.py::test_update_chair_rejected_for_doctor_403` |
| 35 | catalog-and-patients | Endpoints de sillones | Alta de sillón con nombre duplicado responde 409 | `tests/integration/test_api_chairs.py::test_create_chair_duplicate_name_responds_409` |
| 36 | catalog-and-patients | Endpoints de sillones | Alta de sillón con nombre vacío responde 422 | `tests/integration/test_api_chairs.py::test_create_chair_empty_name_responds_422` |
| 37 | catalog-and-patients | Endpoints de sillones | Alta de sillón con cuerpo malformado responde 400 | `tests/integration/test_api_chairs.py::test_create_chair_malformed_body_responds_400` |
| 38 | catalog-and-patients | Endpoints de prestaciones | Alta exitosa de prestación responde 201 | `tests/integration/test_api_services.py::test_create_service_responds_201` |
| 39 | catalog-and-patients | Endpoints de prestaciones | Edición exitosa de prestación responde 200 | `tests/integration/test_api_services.py::test_update_service_responds_200` |
| 40 | catalog-and-patients | Endpoints de prestaciones | Edición de prestación conservando su propio nombre responde 200 | `tests/integration/test_api_services.py::test_update_service_conserving_own_name_responds_200` |
| 41 | catalog-and-patients | Endpoints de prestaciones | Edición de prestación con el nombre de otra prestación responde 409 | `tests/integration/test_api_services.py::test_update_service_with_name_of_another_responds_409` |
| 42 | catalog-and-patients | Endpoints de prestaciones | Edición de prestación inexistente responde 404 | `tests/integration/test_api_services.py::test_update_service_nonexistent_responds_404` |
| 43 | catalog-and-patients | Endpoints de prestaciones | Listado de prestaciones con filtro active verdadero | `tests/integration/test_api_services.py::test_list_services_with_active_filter_true` |
| 44 | catalog-and-patients | Endpoints de prestaciones | Listado de prestaciones sin filtro incluye inactivos en orden alfabético | `tests/integration/test_api_services.py::test_list_services_without_filter_includes_inactive_alphabetical` |
| 45 | catalog-and-patients | Endpoints de prestaciones | Recepción lista prestaciones y responde 200 | `tests/integration/test_api_services.py::test_reception_lists_services_responds_200` |
| 46 | catalog-and-patients | Endpoints de prestaciones | El odontólogo lista prestaciones y responde 200 | `tests/integration/test_api_services.py::test_doctor_lists_services_responds_200` |
| 47 | catalog-and-patients | Endpoints de prestaciones | Detalle de prestación existente responde 200 | `tests/integration/test_api_services.py::test_detail_service_existing_responds_200` |
| 48 | catalog-and-patients | Endpoints de prestaciones | Detalle de prestación inexistente responde 404 | `tests/integration/test_api_services.py::test_detail_service_nonexistent_responds_404` |
| 49 | catalog-and-patients | Endpoints de prestaciones | Consulta de prestaciones sin token responde 401 | `tests/integration/test_api_services.py::test_consult_services_without_token_responds_401` |
| 50 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación rechazada para rol recepción con 403 | `tests/integration/test_api_services.py::test_create_service_rejected_for_reception_403` |
| 51 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación rechazada para rol odontólogo con 403 | `tests/integration/test_api_services.py::test_create_service_rejected_for_doctor_403` |
| 52 | catalog-and-patients | Endpoints de prestaciones | Edición de prestación rechazada para rol recepción con 403 | `tests/integration/test_api_services.py::test_update_service_rejected_for_reception_403` |
| 53 | catalog-and-patients | Endpoints de prestaciones | Edición de prestación rechazada para rol odontólogo con 403 | `tests/integration/test_api_services.py::test_update_service_rejected_for_doctor_403` |
| 54 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación con nombre duplicado responde 409 | `tests/integration/test_api_services.py::test_create_service_duplicate_name_responds_409` |
| 55 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación con duración inválida responde 422 | `tests/integration/test_api_services.py::test_create_service_invalid_duration_responds_422` |
| 56 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación con nombre vacío responde 422 | `tests/integration/test_api_services.py::test_create_service_empty_name_responds_422` |
| 57 | catalog-and-patients | Endpoints de prestaciones | Alta de prestación con cuerpo malformado responde 400 | `tests/integration/test_api_services.py::test_create_service_malformed_body_responds_400` |
| 58 | catalog-and-patients | Endpoints de pacientes | Alta exitosa de paciente por recepción responde 201 | `tests/integration/test_api_patients.py::test_create_patient_by_reception_responds_201` |
| 59 | catalog-and-patients | Endpoints de pacientes | Alta exitosa de paciente por administrador responde 201 | `tests/integration/test_api_patients.py::test_create_patient_by_admin_responds_201` |
| 60 | catalog-and-patients | Endpoints de pacientes | Edición exitosa de paciente responde 200 | `tests/integration/test_api_patients.py::test_update_patient_responds_200` |
| 61 | catalog-and-patients | Endpoints de pacientes | Edición de paciente conservando su propio DNI responde 200 | `tests/integration/test_api_patients.py::test_update_patient_conserving_own_dni_responds_200` |
| 62 | catalog-and-patients | Endpoints de pacientes | Edición de paciente con el DNI de otro paciente responde 409 | `tests/integration/test_api_patients.py::test_update_patient_with_dni_of_another_responds_409` |
| 63 | catalog-and-patients | Endpoints de pacientes | Edición de paciente inexistente responde 404 | `tests/integration/test_api_patients.py::test_update_patient_nonexistent_responds_404` |
| 64 | catalog-and-patients | Endpoints de pacientes | Búsqueda de pacientes por parte del nombre | `tests/integration/test_api_patients.py::test_search_patients_by_name_part` |
| 65 | catalog-and-patients | Endpoints de pacientes | Búsqueda de pacientes sin tilde no encuentra el nombre con tilde | `tests/integration/test_api_patients.py::test_search_patients_without_accent_does_not_find_accented_name` |
| 66 | catalog-and-patients | Endpoints de pacientes | Búsqueda de pacientes por inicio del DNI | `tests/integration/test_api_patients.py::test_search_patients_by_dni_prefix` |
| 67 | catalog-and-patients | Endpoints de pacientes | El odontólogo lista pacientes y responde 200 | `tests/integration/test_api_patients.py::test_doctor_lists_patients_responds_200` |
| 68 | catalog-and-patients | Endpoints de pacientes | Detalle de paciente existente responde 200 | `tests/integration/test_api_patients.py::test_detail_patient_existing_responds_200` |
| 69 | catalog-and-patients | Endpoints de pacientes | Detalle de paciente inexistente responde 404 | `tests/integration/test_api_patients.py::test_detail_patient_nonexistent_responds_404` |
| 70 | catalog-and-patients | Endpoints de pacientes | Consulta de pacientes sin token responde 401 | `tests/integration/test_api_patients.py::test_consult_patients_without_token_responds_401` |
| 71 | catalog-and-patients | Endpoints de pacientes | Alta de paciente rechazada para rol odontólogo con 403 | `tests/integration/test_api_patients.py::test_create_patient_rejected_for_doctor_403` |
| 72 | catalog-and-patients | Endpoints de pacientes | Edición de paciente rechazada para rol odontólogo con 403 | `tests/integration/test_api_patients.py::test_update_patient_rejected_for_doctor_403` |
| 73 | catalog-and-patients | Endpoints de pacientes | Alta de paciente con DNI duplicado responde 409 | `tests/integration/test_api_patients.py::test_create_patient_duplicate_dni_responds_409` |
| 74 | catalog-and-patients | Endpoints de pacientes | Alta de paciente con DNI de formato inválido responde 422 | `tests/integration/test_api_patients.py::test_create_patient_invalid_dni_format_responds_422` |
| 75 | catalog-and-patients | Endpoints de pacientes | Alta de paciente con nombre vacío responde 422 | `tests/integration/test_api_patients.py::test_create_patient_empty_name_responds_422` |
| 76 | catalog-and-patients | Endpoints de pacientes | Alta de paciente con cuerpo malformado responde 400 | `tests/integration/test_api_patients.py::test_create_patient_malformed_body_responds_400` |
| 77 | catalog-and-patients | Endpoints de pacientes | Desactivación de paciente no existe en la API | `tests/integration/test_api_patients.py::test_patient_deactivation_does_not_exist_in_api` |
| 78 | catalog-and-patients | Endpoints de pacientes | Borrado de paciente no existe en la API | `tests/integration/test_api_patients.py::test_patient_deletion_does_not_exist_in_api` |
| 79 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar profesional activo responde 200 | `tests/integration/test_api_deactivation.py::test_deactivate_professional_active_responds_200` |
| 80 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar profesional inactivo responde 200 | `tests/integration/test_api_deactivation.py::test_reactivate_professional_inactive_responds_200` |
| 81 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar profesional ya inactivo responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_deactivate_professional_already_inactive_responds_200_no_changes` |
| 82 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar profesional ya activo responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_reactivate_professional_already_active_responds_200_no_changes` |
| 83 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar profesional inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_deactivate_professional_nonexistent_responds_404` |
| 84 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar profesional inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_reactivate_professional_nonexistent_responds_404` |
| 85 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar profesional rechazado para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_professional_rejected_for_reception_403` |
| 86 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar profesional rechazado para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_professional_rejected_for_doctor_403` |
| 87 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar profesional rechazado para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_professional_rejected_for_reception_403` |
| 88 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar profesional rechazado para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_professional_rejected_for_doctor_403` |
| 89 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar sillón activo responde 200 | `tests/integration/test_api_deactivation.py::test_deactivate_chair_active_responds_200` |
| 90 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar sillón inactivo responde 200 | `tests/integration/test_api_deactivation.py::test_reactivate_chair_inactive_responds_200` |
| 91 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar sillón ya inactivo responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_deactivate_chair_already_inactive_responds_200_no_changes` |
| 92 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar sillón ya activo responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_reactivate_chair_already_active_responds_200_no_changes` |
| 93 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar sillón inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_deactivate_chair_nonexistent_responds_404` |
| 94 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar sillón inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_reactivate_chair_nonexistent_responds_404` |
| 95 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar sillón rechazado para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_chair_rejected_for_reception_403` |
| 96 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar sillón rechazado para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_chair_rejected_for_doctor_403` |
| 97 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar sillón rechazado para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_chair_rejected_for_reception_403` |
| 98 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar sillón rechazado para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_chair_rejected_for_doctor_403` |
| 99 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar prestación activa responde 200 | `tests/integration/test_api_deactivation.py::test_deactivate_service_active_responds_200` |
| 100 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar prestación inactiva responde 200 | `tests/integration/test_api_deactivation.py::test_reactivate_service_inactive_responds_200` |
| 101 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar prestación ya inactiva responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_deactivate_service_already_inactive_responds_200_no_changes` |
| 102 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar prestación ya activa responde 200 sin cambios | `tests/integration/test_api_deactivation.py::test_reactivate_service_already_active_responds_200_no_changes` |
| 103 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar prestación inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_deactivate_service_nonexistent_responds_404` |
| 104 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar prestación inexistente responde 404 | `tests/integration/test_api_deactivation.py::test_reactivate_service_nonexistent_responds_404` |
| 105 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar prestación rechazada para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_service_rejected_for_reception_403` |
| 106 | catalog-and-patients | Desactivación y reactivación en la API | Desactivar prestación rechazada para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_deactivate_service_rejected_for_doctor_403` |
| 107 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar prestación rechazada para rol recepción con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_service_rejected_for_reception_403` |
| 108 | catalog-and-patients | Desactivación y reactivación en la API | Reactivar prestación rechazada para rol odontólogo con 403 | `tests/integration/test_api_deactivation.py::test_reactivate_service_rejected_for_doctor_403` |
<!-- trazabilidad:fin -->

## Mutaciones

Comprobación por mutación sobre código de producción para verificar sensibilidad de las pruebas.

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_update_chair_conserving_own_name_responds_200` | `backend/app/domain/catalog/update.py` | `- other_names = [item.name for item in existing if item.id != candidate.id]`<br>`+ other_names = [item.name for item in existing if item.id == candidate.id]` | `assert 409 == 200` |
| 2 | `test_update_service_invalid_duration` | `backend/app/domain/catalog/update.py` | `- violations += check_duration(candidate.default_duration_min, subject="de la prestación")`<br>`+ pass` | `AssertionError: assert Ok(entity=Service(id=UUID('00000000-0000-0000-0000-0000000000c1'), name='Consulta General', default_duration_min=0, active=True)) == Rejected(violations=(Violation(code=<Violati` |
| 3 | `test_update_patient_conserving_own_dni_responds_200` | `backend/app/domain/catalog/update.py` | `- other_dnis = [item.dni for item in existing if item.id != candidate.id]`<br>`+ other_dnis = [item.dni for item in existing if item.id == candidate.id]` | `assert 409 == 200` |
| 4 | `test_detail_professional_existing_responds_200` | `backend/app/repositories/catalog.py` | `- row = self._session.get(ProfessionalModel, identifier)`<br>`+ row = None` | `assert 404 == 200` |
| 5 | `test_update_professional_responds_200` | `backend/app/repositories/catalog.py` | `- return Ok(result.entity)`<br>`+ return None` | `assert 404 == 200` |
| 6 | `test_search_patients_by_name_part` | `backend/app/repositories/patients.py` | `- clauses: list[ColumnElement[bool]] = [PatientModel.full_name.ilike(f"%{escaped}%", escape="\\")]`<br>`+ clauses: list[ColumnElement[bool]] = [PatientModel.full_name.ilike(f"{escaped}%", escape="\\")]` | `assert False` |
| 7 | `test_search_patients_by_dni_prefix` | `backend/app/repositories/patients.py` | `- if digits:`<br>`+ if False:` | `assert False` |
| 8 | `test_detail_professional_nonexistent_responds_404` | `backend/app/services/catalog.py` | `- raise NotFoundError("Profesional no encontrado.")`<br>`+ raise NotFoundError("Profesional inexistente.")` | `AssertionError: assert {'code': 'NOT...inexistente.'} == {'code': 'NOT... encontrado.'}` |
| 9 | `test_detail_patient_nonexistent_responds_404` | `backend/app/services/patients.py` | `- raise NotFoundError("Paciente no encontrado.")`<br>`+ raise NotFoundError("Paciente inexistente.")` | `AssertionError: assert {'code': 'NOT...inexistente.'} == {'code': 'NOT... encontrado.'}` |
| 10 | `test_create_professional_malformed_body_responds_400` | `backend/app/api/schemas.py` | `- model_config = ConfigDict(populate_by_name=True, extra="forbid")`<br>`+ model_config = ConfigDict(populate_by_name=True, extra="ignore")` | `assert 201 == 400` |
| 11 | `test_detail_chair_nonexistent_responds_404` | `backend/app/api/errors.py` | `- status_code=404,`<br>`+ status_code=400,` | `assert 400 == 404` |
| 12 | `test_create_professional_with_license_responds_201` | `backend/app/api/professionals.py` | `- status_code=status.HTTP_201_CREATED,`<br>`+ status_code=status.HTTP_200_OK,` | `assert 200 == 201` |
| 13 | `test_list_services_without_filter_includes_inactive_alphabetical` | `backend/app/api/services.py` | `- services = list_services(session, active=active)`<br>`+ services = list_services(session, active=True)` | `assert False` |
| 14 | `test_create_patient_by_reception_responds_201` | `backend/app/api/patients.py` | `- Depends(require_permission(Resource.PATIENT, Action.CREATE)),`<br>`+ Depends(require_permission(Resource.PROFESSIONAL, Action.CREATE)),` | `assert 403 == 201` |
| 15 | `test_deactivate_chair_rejected_for_reception_403` | `backend/app/api/chairs.py` | `- Depends(require_permission(Resource.CHAIR, Action.DELETE)),`<br>`+ Depends(require_permission(Resource.CHAIR, Action.READ)),` | `assert 200 == 403` |
<!-- mutaciones:fin -->

## Desvíos

- **Mutaciones reescritas**: tenía 2 mutaciones inválidas (la 8 y la 9: quitaban el `raise NotFoundError` y la API fallaba con un `AttributeError` sobre `None` antes de cualquier assert); se reescribieron para cambiar el mensaje del `NotFoundError`, que detecta el `assert res.json() == {...}` del test, y el script ahora tiene el arreglo de CRLF y el detector de C-23. El SHA-256 es `1f58d…` porque hoy se hashea el código actual de `backend/app`.
