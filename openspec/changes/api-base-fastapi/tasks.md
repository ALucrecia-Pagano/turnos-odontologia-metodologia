# Tasks

> Regla para todas las tareas de los grupos 1 a 8: **test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria** (romper el código a propósito, ver fallar el test, restaurar y registrar el resultado). Cada resultado va a la tabla de RED o mutación de `docs/evidencias/verify-C-18.md`. Sin mocks, `monkeypatch` ni `dependency_overrides`. Los comandos corren desde `backend/`, con `backend/.venv`.

## 1. Dependencias

- [ ] 1.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/test_api_dependencies.py::test_api_dependencies_are_declared`, que lee `pyproject.toml` con `tomllib` y exige los rangos de D14. Agregarlos a `backend/pyproject.toml`. Verificar con ese test.
- [ ] 1.2 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/test_api_dependencies.py::test_api_dependencies_are_installed`, con `importlib.metadata`. **Paso explícito, único que necesita red en el desarrollo local**: ejecutar `python -m pip install "fastapi>=0.118,<1" "uvicorn>=0.30,<1" "httpx>=0.27,<1"`, solo esas dependencias (`python-dotenv` ya está instalado), y `python -m pip check`. Registrar las versiones instaladas en `verify-C-18.md`. Verificar con ese test y con la suite actual en verde.

## 2. App base

- [ ] 2.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Crear `backend/tests/api/__init__.py` y `backend/tests/api/conftest.py` con `Settings` literales ficticios. Escribir `backend/tests/api/test_app.py::test_create_app_accepts_literal_settings` y `::test_create_app_keeps_one_session_factory`. Implementar `create_app`, `lifespan` y el paquete `app/api` (D11). Verificar con esos tests.
- [ ] 2.2 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/api/test_app.py::test_get_session_helper_is_removed`. Borrar `get_session` y su import sin uso de `backend/app/db/session.py` (D11). Verificar con ese test y `mypy --strict app tests`.

## 3. Rechazos del dominio

- [ ] 3.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_error_mapping.py`: `::test_all_violation_codes_are_classified`, `::test_unclassified_code_is_detected`, y `::test_mixed_codes_use_precedence` con sus tres casos. Implementar la tabla de D1, `unclassified_codes` y `status_for` (D1 a D4). Verificar con esos tests.
- [ ] 3.2 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_domain_rejection.py`: `::test_violation_code_maps_to_status`, parametrizado con los 20 códigos y su status escritos literalmente, y `::test_mixed_rejection_keeps_all_violations_in_order`, ambos con un `APIRouter` montado por el test que lanza `Rejected` real. Implementar `DomainRejectedError` y su handler (D5, D15). Verificar con esos tests.
- [ ] 3.3 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_violation_body.py`: `::test_overlap_body`, `::test_blocked_time_body`, `::test_reference_body` y `::test_violation_without_extras_body`, con igualdad exacta de claves. Implementar los esquemas en camelCase de D5. Verificar con esos tests.

## 4. Entrada malformada

- [ ] 4.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_malformed_request.py`: `::test_invalid_json_returns_400`, `::test_missing_field_returns_400`, `::test_sent_value_is_not_returned` y `::test_invalid_query_param_returns_400`. Implementar el handler de D6 con su tabla de mensajes en español. Verificar con esos tests.

## 5. Sesión, salud y CORS

- [ ] 5.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/integration/test_api_session.py`, con una tabla de prueba propia que se elimina al terminar: `::test_committed_write_persists`, `::test_uncommitted_write_does_not_persist` y `::test_exception_rolls_back_write`, leyendo desde otra conexión. Implementar `get_db_session` (D10). Verificar con `pytest -m integration`.
- [ ] 5.2 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/api/test_health.py::test_health_returns_503_with_closed_port`, con un puerto cerrado real, y verificar que el cuerpo es exacto. Implementar `GET /api/health` y el `connect_timeout` de `create_database_engine` (D7). Verificar con ese test.
- [ ] 5.3 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/integration/test_api_health.py::test_health_returns_200_with_database`, contra la base de test. Verificar con `pytest -m integration`.
- [ ] 5.4 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_cors.py`: `::test_preflight_allowed_from_cors_origin`, `::test_simple_response_allowed_from_cors_origin` y `::test_preflight_rejected_from_other_origin`. Implementar CORS (D8). Verificar con esos tests.

## 6. Swagger

- [ ] 6.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/api/test_openapi.py`: `::test_swagger_served_at_api_docs`, `::test_automatic_422_is_removed`, `::test_400_documented_on_route_with_input`, `::test_409_documented_on_rejecting_route`, `::test_422_documented_on_rejecting_route`, `::test_schema_lists_all_violation_codes` y `::test_health_documents_200_and_503`. Implementar `app/api/openapi.py`, `violation_responses`, los ejemplos ficticios y las URLs (D9). Verificar con esos tests.

## 7. Contenedores

- [ ] 7.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. En `backend/tests/test_compose.py`, reemplazar `test_compose_defines_only_postgres_and_redis_without_secrets` por `::test_compose_defines_services_without_literal_secrets`, y agregar `::test_backend_database_url_uses_postgres_service`, `::test_backend_waits_for_healthy_postgres`, `::test_backend_waits_for_healthy_redis` y `::test_backend_healthcheck_uses_api_health`. Agregar el servicio `backend` a `docker-compose.yml` (D13). Verificar con esos tests.
- [ ] 7.2 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir en `backend/tests/test_compose.py`: `::test_dockerfile_migrates_before_uvicorn`, `::test_dockerfile_runs_as_non_root` y `::test_dockerignore_excludes_local_artifacts`. Crear `backend/Dockerfile` y `backend/.dockerignore` (D12). Verificar con esos tests.
- [ ] 7.3 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/test_compose.py::test_readme_warns_about_reserved_password_characters`. Documentar en `backend/README.md` cómo levantar la API y el aviso sobre la contraseña (D13). Verificar con ese test.

## 8. Documentación del contrato

- [ ] 8.1 Test ANTES del código, registrar la salida del RED; si pasa de entrada, mutación obligatoria. Escribir `backend/tests/api/test_error_mapping.py::test_kb_07_lists_all_violation_codes`, que exige en `knowledge-base/07_flujos_principales.md` cada valor de `ViolationCode`. Completar en KB 07 los seis códigos faltantes y los campos del contrato de error de D5, sin cambiar el resto. Verificar con ese test.

## 9. Verificación final y evidencias

- [ ] 9.1 Con el árbol estable, ejecutar `pytest` y `pytest -m integration`, y guardar ambas salidas completas, en UTF-8, en `docs/evidencias/pytest-C-18.txt`. Verificar que no hay fallos; si un fallo viene de C-16 o C-17, registrarlo como ajeno, sin corregirlo.
- [ ] 9.2 Ejecutar `mypy --strict app tests` y guardar la salida completa, en UTF-8, en `docs/evidencias/mypy-C-18.txt`. Verificar `Success`.
- [ ] 9.3 Verificación manual en Docker. **Necesita red para descargar `python:3.13-slim` e instalar las dependencias dentro de la imagen.** Ejecutar `docker compose up --build -d backend`, `docker compose ps`, `docker compose logs backend`, `GET /api/health` y `GET /api/docs`, con PostgreSQL de Windows detenido (`verify-C-13.md`). Verificar que `backend` queda `healthy` y que el log muestra Alembic antes de uvicorn, y registrar la salida en `verify-C-18.md`.
- [ ] 9.4 Redactar `docs/evidencias/verify-C-18.md` con el resumen de resultados, la trazabilidad de CADA escenario de las dos specs delta a un test con nombre completo (`archivo::test`), la tabla de RED o mutación por tarea, las versiones instaladas y los desvíos. Ejecutar `openspec validate api-base-fastapi --strict` y `git diff --check`, y registrar la salida. Verificar que todos los escenarios tienen un test.

## Workflow follow-up

- Commit solo con pedido explícito de la autora, en su propio commit y agregando solo los archivos de C-18.
- `/opsx:archive api-base-fastapi` y marcar `[x]` en `CHANGES.md`.
- Al archivar, completar el `Purpose` de `openspec/specs/api-foundation/spec.md`, que queda con `TBD`.
