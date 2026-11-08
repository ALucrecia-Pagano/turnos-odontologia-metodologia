# Verificación de C-19 — autenticacion-jwt-y-roles

## Aprobación de la autora (governance CRÍTICO)

> APROBACIÓN EXPLÍCITA DE LA AUTORA (governance CRÍTICO): revisé y apruebo
> openspec/changes/autenticacion-jwt-y-roles/design.md tal como está
> commiteado, con las decisiones D1 a D20, la matriz RBAC de 34 filas y
> 102 celdas, y las decisiones registradas P1 a P4. C-18 está archivado
> (2026-11-06).

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 43/43 en [tasks.md](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/tasks.md). La 11.7 la confirmó la autora a mano.
- Suite por defecto: [pytest-C-19.txt](pytest-C-19.txt).
- Integración: [pytest-integration-C-19.txt](pytest-integration-C-19.txt).
- `mypy --strict app tests`: [mypy-C-19.txt](mypy-C-19.txt).
- Mutaciones de D20: [mutaciones-C-19.txt](mutaciones-C-19.txt), con el SHA-256 de `backend/app` y `backend/alembic` antes y después.
- Matriz contra [design.md](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/design.md): [matriz-C-19.txt](matriz-C-19.txt).
- Trazabilidad: [trazabilidad-C-19.txt](trazabilidad-C-19.txt).
- Alembic: [alembic-C-19.txt](alembic-C-19.txt). Seed: [seed-C-19.txt](seed-C-19.txt), solo conteos.
- Docker: [docker-C-19.txt](docker-C-19.txt). E2E: [e2e-C-19.txt](e2e-C-19.txt).
- Secretos en evidencias: [secretos-C-19.txt](secretos-C-19.txt).
- OpenSpec y `git diff --check`: [validate-C-19.txt](validate-C-19.txt).
- `.env` local: [env-C-19.txt](env-C-19.txt). Cumple D4, y `SEED_USER_PASSWORD` tiene al menos 8 caracteres.
- Precondición de C-18: [precondicion-C-19.txt](precondicion-C-19.txt).
- Instalación de dependencias: [pip-C-19.txt](pip-C-19.txt).

## Artefactos archivados

- [proposal.md](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/proposal.md)
- [design.md](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/design.md)
- [tasks.md](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/tasks.md)
- [spec.md (authentication-and-rbac)](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/specs/authentication-and-rbac/spec.md)
- [spec.md (database-infrastructure)](../../openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/specs/database-infrastructure/spec.md)

## Versiones instaladas

- `argon2-cffi==25.1.0`
- `fastapi==0.162.0`
- `pydantic==2.14.2`
- `PyJWT==2.15.1`
- `SQLAlchemy==2.1.6`

## Línea de base

Antes de escribir código: 744 passed, 65 deselected; 65 passed en integración; `mypy` Success en 100 archivos. La primera corrida de integración dio 65 errores porque Docker no estaba levantado: el apply se detuvo, la autora levantó Docker, y la segunda corrida dio 65 passed.

## Verificación manual en Swagger (tarea 11.7)

**Confirmación manual de la autora, 2026-11-06.** La autora probó el flujo de D12 en Swagger y comunicó este resultado:

- Login con `administrador`: `200`, con `accessToken`, `tokenType` igual a `bearer` y `Cache-Control: no-store`.
- *Authorize* con el token.
- `GET /api/auth/me`: `200`, con el usuario y el rol `administrador`.
- Login con credenciales incorrectas: `401` `INVALID_CREDENTIALS`, con `WWW-Authenticate: Bearer`.

Es una confirmación manual: no tiene un archivo de salida. Lo que comprobó el agente por HTTP contra el contenedor está en [e2e-C-19.txt](e2e-C-19.txt).

## Revisión de código de D6 (tarea 11.8)

Por lectura de `backend/app/auth/login.py`: `verify_password` se ejecuta en una única línea, sin bifurcación previa, antes del `if` que evalúa `credentials is None`, `password_ok` y `credentials.active`. `candidate_password_hash` elige el hash guardado o el ficticio sin evitar la verificación.

**Límite conocido**: ningún test automatizado mide la duración ni prueba que `verify` se ejecute en la rama de usuario inexistente. Lo garantizan esta estructura y esta revisión. Sin test de tiempo, por decisión de la autora.

## Trazabilidad

Cada escenario de las dos specs delta. `trazabilidad-C-19.py` comprueba con `pytest --collect-only` que cada test existe.

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | authentication-and-rbac | Login con credenciales válidas | Login correcto del administrador | `tests/integration/test_auth_login.py::test_login_success[administrador]` |
| 2 | authentication-and-rbac | Login con credenciales válidas | Login correcto de recepción | `tests/integration/test_auth_login.py::test_login_success[recepcion]` |
| 3 | authentication-and-rbac | Login con credenciales válidas | Login correcto del odontólogo | `tests/integration/test_auth_login.py::test_login_success[odontologo]` |
| 4 | authentication-and-rbac | Login con credenciales válidas | La respuesta del login no se guarda en caché | `tests/integration/test_auth_login.py::test_login_response_has_no_store` |
| 5 | authentication-and-rbac | Login con credenciales válidas | El usuario se normaliza al buscarlo | `tests/integration/test_auth_login.py::test_login_normalizes_username` |
| 6 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Contraseña incorrecta | `tests/integration/test_auth_login.py::test_wrong_password_is_rejected` |
| 7 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Usuario inexistente | `tests/integration/test_auth_login.py::test_unknown_user_is_rejected` |
| 8 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Usuario inactivo con contraseña correcta | `tests/integration/test_auth_login.py::test_inactive_user_with_correct_password_is_rejected` |
| 9 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Usuario inactivo con contraseña incorrecta | `tests/integration/test_auth_login.py::test_inactive_user_with_wrong_password_is_rejected` |
| 10 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Los cuerpos son idénticos byte por byte | `tests/integration/test_auth_login.py::test_invalid_credentials_are_byte_identical` |
| 11 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Un usuario inexistente se verifica contra el hash ficticio | `tests/auth/test_passwords.py::test_missing_user_uses_dummy_hash` |
| 12 | authentication-and-rbac | Mismo 401 ante credenciales inválidas | Un hash guardado corrupto cuenta como contraseña incorrecta | `tests/integration/test_auth_login.py::test_corrupt_stored_hash_is_rejected` |
| 13 | authentication-and-rbac | Entrada del login validada | Falta la contraseña | `tests/api/test_login_input.py::test_missing_password_returns_400` |
| 14 | authentication-and-rbac | Entrada del login validada | Contraseña de más de 128 caracteres | `tests/api/test_login_input.py::test_too_long_password_returns_400` |
| 15 | authentication-and-rbac | Entrada del login validada | Campo adicional | `tests/api/test_login_input.py::test_extra_field_returns_400` |
| 16 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | El hash usa los parámetros fijados | `tests/auth/test_passwords.py::test_hash_uses_fixed_parameters` |
| 17 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | Dos hashes de la misma contraseña difieren | `tests/auth/test_passwords.py::test_same_password_hashes_differ` |
| 18 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | Una contraseña correcta se verifica | `tests/auth/test_passwords.py::test_correct_password_verifies` |
| 19 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | Una contraseña incorrecta no se verifica | `tests/auth/test_passwords.py::test_wrong_password_does_not_verify` |
| 20 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | Se verifica con los parámetros guardados en el hash | `tests/auth/test_passwords.py::test_verify_uses_parameters_in_hash` |
| 21 | authentication-and-rbac | Contraseñas guardadas solo como hash Argon2id | El perfil barato no está en producción | `tests/auth/test_passwords.py::test_cheapest_profile_not_in_production` |
| 22 | authentication-and-rbac | Token firmado con exactamente tres claims | Claims exactos del token | `tests/auth/test_tokens.py::test_token_has_exact_claims` |
| 23 | authentication-and-rbac | Token firmado con exactamente tres claims | El token del login corresponde al usuario | `tests/integration/test_auth_login.py::test_login_token_matches_user` |
| 24 | authentication-and-rbac | Token ausente y formato inválido responden 401 | Sin header Authorization | `tests/api/test_token_rejection.py::test_rejected_token[no_header]` |
| 25 | authentication-and-rbac | Token ausente y formato inválido responden 401 | Bearer vacío | `tests/api/test_token_rejection.py::test_rejected_token[empty_bearer]` |
| 26 | authentication-and-rbac | Token ausente y formato inválido responden 401 | Esquema Basic | `tests/api/test_token_rejection.py::test_rejected_token[basic_scheme]` |
| 27 | authentication-and-rbac | Token ausente y formato inválido responden 401 | Texto que no es un token | `tests/api/test_token_rejection.py::test_rejected_token[garbage]` |
| 28 | authentication-and-rbac | Token ausente y formato inválido responden 401 | Token válido en la URL | `tests/api/test_token_rejection.py::test_rejected_token[token_in_url]` |
| 29 | authentication-and-rbac | Token vencido responde 401 | Token vencido hace años | `tests/api/test_token_rejection.py::test_rejected_token[expired_years]` |
| 30 | authentication-and-rbac | Token vencido responde 401 | Token vencido hace un segundo | `tests/api/test_token_rejection.py::test_rejected_token[expired_one_second]` |
| 31 | authentication-and-rbac | Token vencido responde 401 | Un token vencido no abre conexión con la base | `tests/api/test_token_rejection.py::test_expired_token_does_not_open_database_connection` |
| 32 | authentication-and-rbac | Token alterado responde 401 | Payload cambiado con la firma original | `tests/api/test_token_rejection.py::test_rejected_token[tampered_payload]` |
| 33 | authentication-and-rbac | Token alterado responde 401 | Firma alterada | `tests/api/test_token_rejection.py::test_rejected_token[tampered_signature]` |
| 34 | authentication-and-rbac | Token alterado responde 401 | Firmado con otra clave | `tests/api/test_token_rejection.py::test_rejected_token[other_key]` |
| 35 | authentication-and-rbac | Token alterado responde 401 | Algoritmo none | `tests/api/test_token_rejection.py::test_rejected_token[alg_none]` |
| 36 | authentication-and-rbac | Token alterado responde 401 | Otro algoritmo con la misma clave | `tests/api/test_token_rejection.py::test_rejected_token[other_algorithm]` |
| 37 | authentication-and-rbac | Token alterado responde 401 | Sin claim exp | `tests/api/test_token_rejection.py::test_rejected_token[missing_exp]` |
| 38 | authentication-and-rbac | Token alterado responde 401 | Sin claim sub | `tests/api/test_token_rejection.py::test_rejected_token[missing_sub]` |
| 39 | authentication-and-rbac | Token alterado responde 401 | Sin claim role | `tests/api/test_token_rejection.py::test_rejected_token[missing_role]` |
| 40 | authentication-and-rbac | Token alterado responde 401 | Claim sub que no es un UUID | `tests/api/test_token_rejection.py::test_rejected_token[sub_not_uuid]` |
| 41 | authentication-and-rbac | Token alterado responde 401 | Claim role desconocido | `tests/api/test_token_rejection.py::test_rejected_token[unknown_role]` |
| 42 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Usuario inexistente con token válido | `tests/integration/test_auth_current_user.py::test_unknown_user_with_valid_token_is_rejected` |
| 43 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Usuario desactivado con token vigente | `tests/integration/test_auth_current_user.py::test_deactivated_user_with_valid_token_is_rejected` |
| 44 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Usuario con otro rol y token vigente | `tests/integration/test_auth_current_user.py::test_role_changed_user_with_valid_token_is_rejected` |
| 45 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Después de cambiar el rol, un login nuevo trae el rol nuevo | `tests/integration/test_auth_current_user.py::test_new_login_after_role_change_has_new_role` |
| 46 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Usuario reactivado con token todavía vigente | `tests/integration/test_auth_current_user.py::test_reactivated_user_with_valid_token_is_accepted` |
| 47 | authentication-and-rbac | El usuario se confirma contra la base en cada request | Cambio de profesional con token vigente | `tests/integration/test_auth_current_user.py::test_professional_change_with_valid_token_is_accepted` |
| 48 | authentication-and-rbac | Datos del usuario autenticado | Usuario autenticado odontólogo | `tests/integration/test_auth_current_user.py::test_me_for_doctor` |
| 49 | authentication-and-rbac | Datos del usuario autenticado | Usuario autenticado de recepción | `tests/integration/test_auth_current_user.py::test_me_for_reception` |
| 50 | authentication-and-rbac | Datos del usuario autenticado | Usuario autenticado administrador | `tests/integration/test_auth_current_user.py::test_me_for_admin` |
| 51 | authentication-and-rbac | Odontólogo con profesional desactivado | Login con el profesional desactivado | `tests/integration/test_auth_current_user.py::test_login_with_inactive_professional` |
| 52 | authentication-and-rbac | Odontólogo con profesional desactivado | Consulta con el profesional desactivado | `tests/integration/test_auth_current_user.py::test_me_with_inactive_professional` |
| 53 | authentication-and-rbac | Actor del dominio desde el usuario autenticado | Actor del odontólogo | `tests/integration/test_auth_current_user.py::test_actor_for_doctor` |
| 54 | authentication-and-rbac | Actor del dominio desde el usuario autenticado | Actor de recepción | `tests/integration/test_auth_current_user.py::test_actor_for_reception` |
| 55 | authentication-and-rbac | Actor del dominio desde el usuario autenticado | Actor del administrador | `tests/integration/test_auth_current_user.py::test_actor_for_admin` |
| 56 | authentication-and-rbac | Actor del dominio desde el usuario autenticado | Un header del cliente no cambia el Actor | `tests/integration/test_auth_current_user.py::test_client_header_does_not_change_actor` |
| 57 | authentication-and-rbac | Matriz RBAC completa | La tabla de permisos coincide con la matriz | `tests/auth/test_permissions.py::test_permissions_match_literal_matrix` |
| 58 | authentication-and-rbac | Matriz RBAC completa | La tabla de permisos cubre todas las combinaciones | `tests/auth/test_permissions.py::test_no_combination_is_missing` |
| 59 | authentication-and-rbac | Matriz RBAC completa | Una combinación faltante se detecta | `tests/auth/test_permissions.py::test_missing_combination_is_detected` |
| 60 | authentication-and-rbac | Matriz RBAC completa | Las 102 celdas responden lo esperado por HTTP | `tests/integration/test_rbac_matrix.py::test_matrix_cell_over_http` |
| 61 | authentication-and-rbac | Rol sin permiso responde 403 con violaciones | Odontólogo que da un turno | `tests/integration/test_rbac_matrix.py::test_doctor_cannot_book` |
| 62 | authentication-and-rbac | Rol sin permiso responde 403 con violaciones | Recepción que crea un profesional | `tests/integration/test_rbac_matrix.py::test_reception_cannot_create_professional` |
| 63 | authentication-and-rbac | Rol sin permiso responde 403 con violaciones | Nadie borra pacientes | `tests/integration/test_rbac_matrix.py::test_nobody_deletes_patients` |
| 64 | authentication-and-rbac | Rol sin permiso responde 403 con violaciones | Sin token en una ruta con permiso | `tests/api/test_token_rejection.py::test_no_token_on_permission_route` |
| 65 | authentication-and-rbac | Alcance propio informado a la ruta | Odontólogo con alcance propio en horarios | `tests/integration/test_rbac_matrix.py::test_doctor_scope_own_on_working_hours` |
| 66 | authentication-and-rbac | Alcance propio informado a la ruta | Administrador con alcance total en horarios | `tests/integration/test_rbac_matrix.py::test_admin_scope_all_on_working_hours` |
| 67 | authentication-and-rbac | Alcance propio informado a la ruta | Odontólogo con alcance total en la agenda | `tests/integration/test_rbac_matrix.py::test_doctor_scope_all_on_agenda` |
| 68 | authentication-and-rbac | La matriz coincide con el dominio en los turnos | Paridad al reprogramar | `tests/auth/test_rbac_domain_parity.py::test_parity_reschedule` |
| 69 | authentication-and-rbac | La matriz coincide con el dominio en los turnos | Paridad al cancelar | `tests/auth/test_rbac_domain_parity.py::test_parity_cancel` |
| 70 | authentication-and-rbac | La matriz coincide con el dominio en los turnos | Paridad al cambiar estado de un turno propio | `tests/auth/test_rbac_domain_parity.py::test_parity_change_status_own` |
| 71 | authentication-and-rbac | La matriz coincide con el dominio en los turnos | Paridad al cambiar estado de un turno ajeno | `tests/auth/test_rbac_domain_parity.py::test_parity_change_status_foreign` |
| 72 | authentication-and-rbac | Rechazo por defecto en todas las rutas | Salud sin token | `tests/integration/test_auth_current_user.py::test_health_without_token` |
| 73 | authentication-and-rbac | Rechazo por defecto en todas las rutas | Las rutas reales no públicas exigen token | `tests/api/test_route_guards.py::test_real_non_public_routes_require_token` |
| 74 | authentication-and-rbac | Rechazo por defecto en todas las rutas | Una ruta sin protección se detecta | `tests/api/test_route_guards.py::test_route_without_protection_is_detected` |
| 75 | authentication-and-rbac | Rechazo por defecto en todas las rutas | Las rutas protegidas reales declaran permiso | `tests/api/test_route_guards.py::test_real_protected_routes_declare_permission` |
| 76 | authentication-and-rbac | Rechazo por defecto en todas las rutas | Una ruta protegida sin permiso se detecta | `tests/api/test_route_guards.py::test_protected_route_without_permission_is_detected` |
| 77 | authentication-and-rbac | Configuración del token validada al arrancar | Secreto de 31 caracteres | `tests/test_config.py::test_short_secret_error_hides_value` |
| 78 | authentication-and-rbac | Configuración del token validada al arrancar | Secreto de 32 caracteres | `tests/test_config.py::test_secret_of_32_characters_loads` |
| 79 | authentication-and-rbac | Configuración del token validada al arrancar | Secreto vacío | `tests/test_config.py::test_empty_secret_names_variable` |
| 80 | authentication-and-rbac | Configuración del token validada al arrancar | Algoritmo none | `tests/test_config.py::test_algorithm_none_is_rejected` |
| 81 | authentication-and-rbac | Configuración del token validada al arrancar | Algoritmo asimétrico | `tests/test_config.py::test_asymmetric_algorithm_is_rejected` |
| 82 | authentication-and-rbac | Configuración del token validada al arrancar | Vigencia en cero | `tests/test_config.py::test_zero_expiration_is_rejected` |
| 83 | authentication-and-rbac | Secretos fuera de respuestas | El login no devuelve hash ni contraseña | `tests/integration/test_auth_no_leaks.py::test_login_response_has_no_secrets` |
| 84 | authentication-and-rbac | Secretos fuera de respuestas | La consulta del usuario no devuelve hash | `tests/integration/test_auth_no_leaks.py::test_me_response_has_no_secrets` |
| 85 | authentication-and-rbac | Secretos fuera de respuestas | Un login malformado no devuelve la contraseña | `tests/api/test_login_input.py::test_malformed_login_does_not_return_password` |
| 86 | authentication-and-rbac | Secretos fuera de respuestas | Los esquemas de respuesta no tienen hash | `tests/api/test_login_input.py::test_response_schemas_have_no_hash` |
| 87 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | Un login correcto no deja secretos en los logs | `tests/integration/test_auth_no_leaks.py::test_successful_login_logs_no_secrets` |
| 88 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | Un login fallido no deja secretos en los logs | `tests/integration/test_auth_no_leaks.py::test_failed_login_logs_no_secrets` |
| 89 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | Las credenciales internas no muestran el hash | `tests/auth/test_model.py::test_credentials_repr_hides_hash` |
| 90 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | La configuración no muestra los secretos | `tests/test_config.py::test_settings_repr_hides_secrets` |
| 91 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | Un usuario duplicado no filtra el hash | `tests/integration/test_user_repository.py::test_duplicate_username_error_hides_hash` |
| 92 | authentication-and-rbac | Secretos fuera de logs y mensajes de error | Una regla de rol violada no filtra el hash | `tests/integration/test_user_repository.py::test_role_rule_error_hides_hash` |
| 93 | authentication-and-rbac | Autorización documentada en Swagger | Esquema bearerAuth declarado | `tests/api/test_auth_openapi.py::test_bearer_scheme_is_declared` |
| 94 | authentication-and-rbac | Autorización documentada en Swagger | La ruta del usuario autenticado tiene candado | `tests/api/test_auth_openapi.py::test_me_has_security_and_401` |
| 95 | authentication-and-rbac | Autorización documentada en Swagger | El login no tiene candado | `tests/api/test_auth_openapi.py::test_login_has_no_security_and_documents_responses` |
| 96 | authentication-and-rbac | Autorización documentada en Swagger | Salud no tiene candado | `tests/api/test_auth_openapi.py::test_health_has_no_security` |
| 97 | authentication-and-rbac | Autorización documentada en Swagger | Una ruta con permiso documenta 403 | `tests/api/test_auth_openapi.py::test_permission_route_documents_403` |
| 98 | authentication-and-rbac | Autorización documentada en Swagger | Swagger conserva la autorización | `tests/api/test_auth_openapi.py::test_swagger_persists_authorization` |
| 99 | database-infrastructure | Tabla de usuarios con restricciones en la base | Usuario duplicado | `tests/integration/test_user_persistence.py::test_duplicate_username_is_rejected` |
| 100 | database-infrastructure | Tabla de usuarios con restricciones en la base | Usuario con mayúsculas | `tests/integration/test_user_persistence.py::test_uppercase_username_is_rejected` |
| 101 | database-infrastructure | Tabla de usuarios con restricciones en la base | Rol desconocido | `tests/integration/test_user_persistence.py::test_unknown_role_is_rejected` |
| 102 | database-infrastructure | Tabla de usuarios con restricciones en la base | Activo por defecto | `tests/integration/test_user_persistence.py::test_active_defaults_to_true` |
| 103 | database-infrastructure | Tabla de usuarios con restricciones en la base | Profesional inexistente | `tests/integration/test_user_persistence.py::test_unknown_professional_is_rejected` |
| 104 | database-infrastructure | Tabla de usuarios con restricciones en la base | Borrar un profesional con usuario | `tests/integration/test_user_persistence.py::test_deleting_professional_with_user_is_rejected` |
| 105 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Odontólogo con profesional | `tests/integration/test_user_persistence.py::test_doctor_with_professional_is_accepted` |
| 106 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Odontólogo sin profesional | `tests/integration/test_user_persistence.py::test_doctor_without_professional_is_rejected` |
| 107 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Recepción sin profesional | `tests/integration/test_user_persistence.py::test_reception_without_professional_is_accepted` |
| 108 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Recepción con profesional | `tests/integration/test_user_persistence.py::test_reception_with_professional_is_rejected` |
| 109 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Administrador con profesional | `tests/integration/test_user_persistence.py::test_admin_with_professional_is_rejected` |
| 110 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Cambiar a recepción sin quitar el profesional | `tests/integration/test_user_persistence.py::test_changing_role_keeping_professional_is_rejected` |
| 111 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Dos usuarios para el mismo profesional | `tests/integration/test_user_persistence.py::test_two_users_for_same_professional_are_rejected` |
| 112 | database-infrastructure | El odontólogo tiene profesional y los demás roles no | Varios usuarios sin profesional | `tests/integration/test_user_persistence.py::test_several_users_without_professional_are_accepted` |
| 113 | database-infrastructure | Migración reversible de usuarios | Downgrade a la revisión anterior | `tests/integration/test_database_infrastructure.py::test_user_migration_explicit_downgrade_cycle` |
| 114 | database-infrastructure | Migración reversible de usuarios | Upgrade a la revisión de usuarios | `tests/integration/test_database_infrastructure.py::test_user_migration_explicit_upgrade` |
| 115 | database-infrastructure | Migración reversible de usuarios | Sin diferencias con la metadata | `tests/integration/test_database_infrastructure.py::test_metadata_has_no_differences_with_users` |
| 116 | database-infrastructure | Seed de un usuario por rol | Primera ejecución crea los tres usuarios | `tests/integration/test_seed_users.py::test_seed_creates_one_user_per_role` |
| 117 | database-infrastructure | Seed de un usuario por rol | Cada usuario del seed inicia sesión | `tests/integration/test_seed_users.py::test_seed_users_can_log_in` |
| 118 | database-infrastructure | Seed de un usuario por rol | Segunda ejecución no inserta | `tests/integration/test_seed_users.py::test_second_seed_inserts_nothing` |
| 119 | database-infrastructure | Seed de un usuario por rol | Una contraseña distinta no cambia a los usuarios existentes | `tests/integration/test_seed_users.py::test_seed_does_not_change_existing_password` |
| 120 | database-infrastructure | Seed de un usuario por rol | El seed guarda hash Argon2id | `tests/integration/test_seed_users.py::test_seed_stores_argon2id_hash` |
| 121 | database-infrastructure | Seed de un usuario por rol | El usuario y el profesional tienen ids distintos | `tests/integration/test_seed_users.py::test_seed_user_id_differs_from_professional_id` |
| 122 | database-infrastructure | Seed de un usuario por rol | La salida del seed no muestra la contraseña | `tests/integration/test_seed_users.py::test_seed_output_hides_password` |
| 123 | database-infrastructure | El seed exige una contraseña válida antes de escribir | Falta la contraseña | `tests/integration/test_seed_users.py::test_seed_rejects_missing_password` |
| 124 | database-infrastructure | El seed exige una contraseña válida antes de escribir | Contraseña vacía | `tests/integration/test_seed_users.py::test_seed_rejects_empty_password` |
| 125 | database-infrastructure | El seed exige una contraseña válida antes de escribir | Contraseña de solo espacios | `tests/integration/test_seed_users.py::test_seed_rejects_blank_password` |
| 126 | database-infrastructure | El seed exige una contraseña válida antes de escribir | Contraseña de 7 caracteres | `tests/integration/test_seed_users.py::test_seed_rejects_short_password` |
| 127 | database-infrastructure | El seed exige una contraseña válida antes de escribir | Contraseña de 8 caracteres | `tests/integration/test_seed_users.py::test_seed_accepts_eight_characters` |
| 128 | database-infrastructure | El seed exige una contraseña válida antes de escribir | El comando manual termina con error | `tests/integration/test_seed_users.py::test_seed_command_exits_with_error` |
| 129 | database-infrastructure | El seed se niega a correr en producción | Seed con APP_ENV production | `tests/integration/test_seed_users.py::test_seed_refuses_production` |
| 130 | database-infrastructure | El seed se niega a correr en producción | Seed con APP_ENV development | `tests/integration/test_seed_users.py::test_seed_runs_in_development` |
| 131 | database-infrastructure | Configuración completa y errores explícitos | Falta DATABASE_URL | `tests/test_config.py::test_missing_database_url_names_variable` |
| 132 | database-infrastructure | Configuración completa y errores explícitos | Configuración completa | `tests/test_config.py::test_complete_configuration_exposes_typed_values` |
| 133 | database-infrastructure | Configuración completa y errores explícitos | Falta SEED_USER_PASSWORD | `tests/test_config.py::test_missing_seed_password_loads_as_none` |
| 134 | database-infrastructure | Migración reversible de horarios y bloqueos | Ciclo upgrade y downgrade reversible de la migración | `tests/integration/test_database_infrastructure.py::test_availability_migration_downgrade_minus_one_cycle` |
| 135 | database-infrastructure | Migración reversible de turnos e historial | Ciclo upgrade y downgrade menos uno de la migración de turnos | `tests/integration/test_database_infrastructure.py::test_appointment_migration_downgrade_minus_one_cycle` |
<!-- trazabilidad:fin -->

## RED o mutación por tarea

| Tarea | RED | Mutación | Qué pasó |
|---|---|---|---|
| 1.1 | [1.1](red-C-19/1.1.txt) | — | Falla: no están declaradas |
| 1.2 | [1.2](red-C-19/1.2.txt) | — | Falla: no están instaladas |
| 1.3 | [1.3](red-C-19/1.3.txt) | — | 8 fallan |
| 2.1 | Pasa de entrada (cambio de tests) | [2.1-mutacion](red-C-19/2.1-mutacion.txt) | Fila 21 de D20 |
| 2.2 | [2.2](red-C-19/2.2.txt) | — | 2 fallan |
| 2.3 | [2.3](red-C-19/2.3.txt) | — | 18 fallan: no hay tabla ni revisión |
| 2.4 | [2.4](red-C-19/2.4.txt) | — | Colección: falta `app.auth.model` |
| 2.5 | [2.5](red-C-19/2.5.txt) | — | Falla: KB 04 sin `app_user` |
| 3.1 | [3.1](red-C-19/3.1.txt) | — | Colección: falta `app.auth.passwords` |
| 3.2 | [3.2](red-C-19/3.2.txt) | — | `ImportError` de `candidate_password_hash` |
| 4.1 | [4.1](red-C-19/4.1.txt) | — | Colección: falta `app.auth.tokens` |
| 4.2 | [4.2](red-C-19/4.2.txt) | — | Colección: falta `get_current_user` |
| 5.1 | [5.1](red-C-19/5.1.txt) | — | 3 fallan: no existe la ruta |
| 5.2 | [5.2](red-C-19/5.2.txt) | [5.2-mutacion](red-C-19/5.2-mutacion.txt) | 6 fallan; los 6 de rechazo pasaban por el stub de 5.1 |
| 6.1 | [6.1](red-C-19/6.1.txt) | [6.1-mutacion](red-C-19/6.1-mutacion.txt) | 11 fallan; `test_login_with_inactive_professional` pasaba |
| 6.2 | [6.2](red-C-19/6.2.txt) | — | `ImportError` de `get_current_actor` |
| 6.3 | [6.3](red-C-19/6.3.txt) | — | 2 fallan |
| 7.1 | [7.1](red-C-19/7.1.txt) | — | Colección: falta `app.auth.permissions` |
| 7.2 | [7.2](red-C-19/7.2.txt) | — | Colección: falta `Permission` |
| 7.3 | [7.3](red-C-19/7.3.txt), pasa de entrada | [7.3-mutacion](red-C-19/7.3-mutacion.txt) | Cuatro mutaciones sobre `PERMISSIONS` |
| 7.4 | [7.4](red-C-19/7.4.txt) | [7.4-mutacion](red-C-19/7.4-mutacion.txt) | Colección: falta `protected_router`; `test_health_without_token` lleva mutación |
| 7.5 | [7.5](red-C-19/7.5.txt) | — | Falla: KB 03 sin precisar |
| 8.1 | [8.1](red-C-19/8.1.txt) | [8.1-mutacion](red-C-19/8.1-mutacion.txt) | 8 fallan; `test_seed_does_not_change_existing_password` lleva mutación |
| 8.2 | [8.2](red-C-19/8.2.txt) | [8.2-mutacion](red-C-19/8.2-mutacion.txt) | 6 fallan; 8 caracteres y `development` llevan mutación |
| 8.3 | [8.3](red-C-19/8.3.txt) | — | 2 fallan |
| 9.1 | [9.1](red-C-19/9.1.txt) | — | Colección: falta `permission_responses` |
| 9.2 | [9.2](red-C-19/9.2.txt) | [9.2-mutacion](red-C-19/9.2-mutacion.txt) | Falla por una fuga real; los demás llevan mutación |
| 10.1 | [10.1](red-C-19/10.1.txt) | — | Falla con una celda cambiada, pasa al restaurar |
| 11.9 | [11.9](red-C-19/11.9.txt) | — | Falla: el `repr` de `Settings` mostraba la contraseña de PostgreSQL |

## Desvíos

1. **`StoredUser`, tipo nuevo en `app/auth/model.py`.** D10 fija `AuthenticatedUser` sin `active`, pero D5 exige mirar `active` en cada request. `get_by_id` devuelve `StoredUser(user, active)`, sin el hash.
2. **`authenticate` devuelve `None` en vez de lanzar `AuthenticationError`.** El fragmento de D6 lanza la excepción, pero D18 la ubica en `app/api/errors.py` y pide `login.py` sin FastAPI. La ruta traduce el `None`. Los pasos y el orden de D6 no cambian.
3. **El largo de `JWT_SECRET` se valida con un `field_validator`, no con `min_length`.** `load_settings()` pasa las claves en minúsculas, y con `min_length` el error nombraba `jwt_secret`, cuando la spec exige `JWT_SECRET`.
4. **Fuga no prevista en D15, hallada en el RED de la 9.2.** Con `sqlalchemy.engine` en `DEBUG`, SQLAlchemy registra cada fila leída (`Row (...)`), con el hash incluido; `hide_parameters` no lo cubre. Se agregó el filtro `_HideRowValues` en `app/db/session.py`. El filtro depende del texto `Row %r` de SQLAlchemy: si cambia en una actualización, `test_successful_login_logs_no_secrets` falla. Además, `get_by_id` difiere la columna del hash, para que `get_credentials_by_username` sea el único método que la lee, como dice D15.
5. **`test_duplicate_username_error_hides_hash` tiene dos partes.** Con `from None` en el repositorio, `hide_parameters` no influía en el error y la mutación 16 no podía hacer fallar el test. Se agregó el mismo choque sin pasar por el repositorio.
6. **D19: una aserción más de las listadas.** La línea 117 de `test_migration_cycle_restores_test_database_to_head` también fijaba `head` en la revisión 05, y también compara contra `get_current_head()`.
7. **`test_user_migration_explicit_downgrade_cycle` y `..._explicit_upgrade` terminan con `upgrade head`.** El ciclo verificado usa solo revisiones explícitas, como pide la spec; ese paso final solo deja la base como estaba, para que una migración futura no rompa los tests siguientes.
8. **Guardianes con `fastapi.routing.iter_route_contexts`.** FastAPI 0.162 ya no aplana los routers incluidos: `app.routes` solo ve `_IncludedRouter`, así que recorrerlo como decía D9 daba un guardián que nunca detectaba nada. Lo fijan los tests con apps mal armadas. Esa función no existe en todas las versiones que admite `fastapi>=0.118`; hoy solo la usan los tests.
9. **Script adicional `trazabilidad-C-19.py`,** no listado en D20, para que la comprobación de escenarios sea reproducible.
10. **Migración de la base local.** La tarea 11.3 corre el seed sobre la base local, que necesita la revisión 06: se ejecutó `alembic upgrade head` antes (Migration Plan, paso 5), registrado en `alembic-C-19.txt`. La base local quedó con la tabla `app_user` y los tres usuarios ficticios.

11. **Contraseña de PostgreSQL en el `repr` de `Settings`, hallada en la tarea 11.9.** D4 y D15 solo protegen `jwt_secret` y `seed_user_password`. `postgres_password` y `database_url` salían en el `repr`, y pytest lo mostró al fallar un test: el valor real quedó en `red-C-19/6.1.txt`, `8.1.txt` y `8.2.txt`, sin commitear. Se agregó `Field(repr=False)` a los dos campos, con `test_settings_repr_hides_database_password`. En esos tres archivos un script reemplazó el valor por `***` y agregó una nota al final: es la única alteración de evidencias después de generarlas. Después se repitió toda la verificación final.

12. **`Any` en dos firmas de `app/api/openapi.py`** (`permission_responses` y `login_responses`), contra la regla dura. El parámetro `responses` de FastAPI exige `dict[int | str, dict[str, Any]]`, y por invarianza `mypy --strict` rechaza `dict[str, object]`. Es la misma firma de `violation_responses` de C-18. La alternativa, `type: ignore`, también está prohibida.

13. **Mutaciones con el detector de C-23**: el script ahora tiene el arreglo de CRLF y el detector de inválidas, y ningún texto original fue ambiguo. La 8 y la 9 (`test_rejected_token[other_algorithm]` y `[missing_exp]`) fallan con `ConnectionTimeout` de psycopg, no con un assert. El test corre contra una base en un puerto cerrado, y ese puerto es parte de su oráculo ("rechazar antes de tocar la base"): una mutación que acepta el token llega a la base. Por decisión de la autora, se aceptan como "detectadas por centinela de base" mediante la lista explícita `DB_SENTINEL_TESTS`. Solo cuentan si el primer `E` es un error de conexión de psycopg y si el test usa de verdad esa base, lo que se verifica leyendo sus fixtures con `ast` (`database_url` armada con un helper que hace `bind` sin `listen`). `--check` aborta si alguno deja de usarla, y cualquier otro caso sigue siendo inválido. No se tocó el test. El SHA-256 es `f79aa…` porque hoy se hashea el código actual de `backend/app` y `backend/alembic`.

## Notas sobre el proceso de RED

- **Tarea 7.1**: el código de `permissions.py` se escribió antes de correr el RED y se apartó del árbol durante esa corrida. El test sí corrió primero sin el código, pero el orden de escritura no fue el de la regla.
- **Tareas 3.1 y 3.2**: los tests se escribieron juntos. Para tener un RED real de la 3.2 se movieron sus imports dentro de cada test, y el RED se generó con la 3.1 ya implementada.
- **Tarea 5.2**: el primer RED se corrió antes del código de la 5.1 y se regeneró después; el archivo es el segundo.
- **Tarea 9.2**: la primera mutación de `test_malformed_login_does_not_return_password` no hizo fallar el test porque estaba mal planteada: `err["input"]` solo trae el `username`. Se repitió con `exc.body`, y las dos corridas quedan en el archivo.
- **Marcado anticipado de 7.4**: se marcó con 2 tests en rojo, se desmarcó, y se volvió a marcar con los tests en verde.
- Las mutaciones manuales de `red-C-19/` se corrieron con un script auxiliar fuera del repo. Las 21 de D20 están en `mutaciones-C-19.py`.

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_doctor_without_professional_is_rejected` | `backend/alembic/versions/20261106_06_usuarios.py` | `- "(role = 'odontologo' AND professional_id IS NOT NULL) "`<br>`+ "(role = 'odontologo') "` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| 2 | `test_reception_with_professional_is_rejected` | `backend/alembic/versions/20261106_06_usuarios.py` | `- "OR (role <> 'odontologo' AND professional_id IS NULL)"`<br>`+ "OR (role <> 'odontologo')"` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| 3 | `test_two_users_for_same_professional_are_rejected` | `backend/alembic/versions/20261106_06_usuarios.py` | `- unique=True,`<br>`+ unique=False,` | `Failed: DID NOT RAISE <class 'sqlalchemy.exc.IntegrityError'>` |
| 4 | `test_user_migration_explicit_downgrade_cycle` | `backend/alembic/versions/20261106_06_usuarios.py` | `- op.drop_index("ux_app_user_professional_id", table_name="app_user")`<br>`- op.drop_index("ux_app_user_username", table_name="app_user")`<br>`- op.drop_table("app_user")`<br>`+ pass` | `AssertionError: assert 'app_user' not in ['alembic_version', 'appointment_status_change', 'appointment', 'professional', 'chair', 'patient', ...]` |
| 5 | `test_hash_uses_fixed_parameters` | `backend/app/auth/passwords.py` | `- time_cost=3,`<br>`+ time_cost=1,` | `AssertionError: assert False` |
| 6 | `test_missing_user_uses_dummy_hash` | `backend/app/auth/passwords.py` | `- return dummy_password_hash()`<br>`+ return "$argon2id$v=19$m=8,t=1,p=1$c2FsdHNhbHQ$aGFzaGhhc2g"` | `AssertionError: assert '$argon2id$v=...Q$aGFzaGhhc2g' == '$argon2id$v=...UaX4wY0N1l4eE'` |
| 7 | `test_inactive_user_with_correct_password_is_rejected` | `backend/app/auth/login.py` | `- if credentials is None or not password_ok or not credentials.active:`<br>`+ if credentials is None or not password_ok:` | `assert 200 == 401` |
| 8 | `test_rejected_token[other_algorithm]` | `backend/app/auth/tokens.py` | `- algorithms=[settings.jwt_algorithm],`<br>`+ algorithms=["HS256", "HS512"],` | `detectada por centinela de base: psycopg.errors.ConnectionTimeout: connection timeout expired` |
| 9 | `test_rejected_token[missing_exp]` | `backend/app/auth/tokens.py` | `- options={"require": ["exp", "sub", "role"]},`<br>`+ options={"require": ["sub", "role"]},` | `detectada por centinela de base: psycopg.errors.ConnectionTimeout: connection timeout expired` |
| 10 | `test_deactivated_user_with_valid_token_is_rejected` | `backend/app/api/deps.py` | `- if not stored.active:`<br>`- raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)` | `assert 200 == 401` |
| 11 | `test_role_changed_user_with_valid_token_is_rejected` | `backend/app/api/deps.py` | `- if stored.user.role is not claims.role:`<br>`- raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)` | `assert 200 == 401` |
| 12 | `test_permissions_match_literal_matrix` | `backend/app/auth/permissions.py` | `- (Resource.PROFESSIONAL, Action.CREATE): {_A: _ALL},`<br>`+ (Resource.PROFESSIONAL, Action.CREATE): {_R: _ALL, _A: _ALL},` | `AssertionError: assert ['fila 15, re....ALL != None'] == []` |
| 13 | `test_matrix_cell_over_http[PATIENT-DELETE-administrador]` | `backend/app/api/deps.py` | `+ scope = scope or Scope.ALL` | `assert 200 == 403` |
| 14 | `test_seed_rejects_short_password` | `backend/app/db/seed.py` | `- if len(password) < SEED_PASSWORD_MIN_LENGTH:`<br>`+ if False:` | `Failed: DID NOT RAISE <class 'app.db.seed.SeedConfigurationError'>` |
| 15 | `test_seed_refuses_production` | `backend/app/db/seed.py` | `- if settings.app_env == "production":`<br>`+ if False:` | `Failed: DID NOT RAISE <class 'app.db.seed.SeedConfigurationError'>` |
| 16 | `test_duplicate_username_error_hides_hash` | `backend/app/db/session.py` | `- hide_parameters=True,`<br>`+ hide_parameters=False,` | `AssertionError: assert 'hash-ficticio-reconocible' not in 'Traceback (...e/21/gkpj)\n'` |
| 17 | `test_role_rule_error_hides_hash` | `backend/app/repositories/users.py` | `- raise UserWriteError(constraint_name(error)) from None`<br>`+ raise UserWriteError(str(error))` | `AssertionError: assert 'hash-ficticio-reconocible' not in 'Traceback (...e/21/gkpj)\n'` |
| 18 | `test_credentials_repr_hides_hash` | `backend/app/auth/model.py` | `- password_hash: str = field(repr=False)`<br>`+ password_hash: str` | `assert 'hash-ficticio-reconocible' not in "UserCredent...econocible')"` |
| 19 | `test_short_secret_error_hides_value` | `backend/app/config.py` | `- hide_input_in_errors=True,` | `AssertionError: assert 'MARCA-RECONOCIBLE' not in '1 validatio.../value_error'` |
| 20 | `test_valid_token_is_accepted` | `backend/app/auth/tokens.py` | `` - """Devuelve los claims, o `None` ante cualquier token inválido o vencido.""" ``<br>`+ return None` | `assert 401 == 200` |
| 21 | `test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle` | `backend/alembic/versions/20261105_05_historial_sin_truncate.py` | `- DROP TRIGGER IF EXISTS tr_appointment_status_change_no_truncate ON appointment_status_change;`<br>`+ SELECT 1;` | `AssertionError: assert 'tr_appointment_status_change_no_truncate' not in ['tr_appointment_status_change_append_only', 'tr_appointment_status_change_no_truncate']` |
<!-- mutaciones:fin -->
