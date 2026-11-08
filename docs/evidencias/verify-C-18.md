# Verificación de C-18 — api-base-fastapi

## Resultado

- Tareas completadas: 21/21.
- Suite por defecto: 744 passed, 65 deselected en 6.81s (referencia: [pytest-C-18.txt](pytest-C-18.txt)).
- Integración: 65 passed, 744 deselected en 8.74s (referencia: [pytest-C-18.txt](pytest-C-18.txt)).
- Mypy estricto: `Success: no issues found in 100 source files` (referencia: [mypy-C-18.txt](mypy-C-18.txt)).
- Verificación por mutación: 45/45 mutaciones matadas, 0 sobrevivientes (referencia: [mutaciones-C-18.txt](mutaciones-C-18.txt)).
- Verificación manual en Docker: Contenedor `backend` construido y levantado con `docker compose up --build -d backend`. Estado `healthy`. `alembic upgrade head` ejecutado antes de `uvicorn`. `curl http://localhost:8000/api/health` -> HTTP 200 `{"status":"ok","database":"ok"}`. `curl http://localhost:8000/api/docs` -> HTTP 200 Swagger UI (referencia: [docker-C-18.txt](docker-C-18.txt)).
- OpenSpec estricto: `Change 'api-base-fastapi' is valid` (`openspec validate api-base-fastapi --strict`).
- Higiene git: `git diff --check` limpio (código de salida 0).

Los artefactos del change están ubicados en:
- [proposal.md](../../openspec/changes/archive/2026-11-06-api-base-fastapi/proposal.md)
- [design.md](../../openspec/changes/archive/2026-11-06-api-base-fastapi/design.md)
- [tasks.md](../../openspec/changes/archive/2026-11-06-api-base-fastapi/tasks.md)
- [spec.md (api-foundation)](../../openspec/changes/archive/2026-11-06-api-base-fastapi/specs/api-foundation/spec.md)
- [spec.md (database-infrastructure)](../../openspec/changes/archive/2026-11-06-api-base-fastapi/specs/database-infrastructure/spec.md)

Las salidas completas están en:
- [pytest-C-18.txt](pytest-C-18.txt)
- [mypy-C-18.txt](mypy-C-18.txt)
- [docker-C-18.txt](docker-C-18.txt)
- [mutaciones-C-18.txt](mutaciones-C-18.txt)

---

## Trazabilidad: escenarios a tests automáticos

Todos los nombres corresponden a funciones reales existentes comprobadas mediante `git grep -c "def <nombre>"` con resultado 1 para cada una.

| Nº | Escenario de la spec | Test automático (nombre real en código) | Archivo |
|---|---|---|---|
| 1 | Health 200 con la base disponible | `test_health_returns_200_with_database` | `tests/integration/test_api_health.py` |
| 2 | Health 503 con la base caída | `test_health_returns_503_with_closed_port` | `tests/api/test_health.py` |
| 3 | JSON sintácticamente inválido | `test_invalid_json_returns_400` | `tests/api/test_malformed_request.py` |
| 4 | Campo obligatorio faltante | `test_missing_field_returns_400` | `tests/api/test_malformed_request.py` |
| 5 | El valor enviado no se devuelve | `test_sent_value_is_not_returned` | `tests/api/test_malformed_request.py` |
| 6 | Parámetro de consulta inválido | `test_invalid_query_param_returns_400` | `tests/api/test_malformed_request.py` |
| 7 | PROFESSIONAL_OVERLAP responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 8 | CHAIR_OVERLAP responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 9 | OUTSIDE_WORKING_HOURS responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 10 | BLOCKED_TIME responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 11 | DUPLICATE_DNI responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 12 | DUPLICATE_NAME responde 409 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 13 | UNKNOWN_REFERENCE responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 14 | INACTIVE_REFERENCE responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 15 | INVALID_DURATION responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 16 | INVALID_START_TIME responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 17 | CROSSES_MIDNIGHT responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 18 | IN_THE_PAST responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 19 | INVALID_WORKING_HOURS responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 20 | OVERLAPPING_WORKING_HOURS responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 21 | INVALID_BLOCK responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 22 | INVALID_DNI responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 23 | EMPTY_NAME responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 24 | STATUS_CHANGE_TOO_EARLY responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 25 | INVALID_TRANSITION responde 422 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 26 | FORBIDDEN_OPERATION responde 403 | `test_violation_code_maps_to_status` | `tests/api/test_domain_rejection.py` |
| 27 | Nombre vacío y DNI duplicado responden 422 | `test_mixed_codes_use_precedence` | `tests/api/test_error_mapping.py` |
| 28 | Nombre duplicado y duración inválida responden 422 | `test_mixed_codes_use_precedence` | `tests/api/test_error_mapping.py` |
| 29 | Operación prohibida prevalece sobre validez | `test_mixed_codes_use_precedence` | `tests/api/test_error_mapping.py` |
| 30 | Todos los códigos están clasificados | `test_all_violation_codes_are_classified` | `tests/api/test_error_mapping.py` |
| 31 | Un código sin clasificar se detecta | `test_unclassified_code_is_detected` | `tests/api/test_error_mapping.py` |
| 32 | Violación de solapamiento | `test_overlap_body` | `tests/api/test_violation_body.py` |
| 33 | Violación de bloqueo | `test_blocked_time_body` | `tests/api/test_violation_body.py` |
| 34 | Violación de referencia | `test_reference_body` | `tests/api/test_violation_body.py` |
| 35 | Violación sin datos adicionales | `test_violation_without_extras_body` | `tests/api/test_violation_body.py` |
| 36 | Preflight permitido desde CORS_ORIGIN | `test_preflight_allowed_from_cors_origin` | `tests/api/test_cors.py` |
| 37 | Respuesta simple permitida desde CORS_ORIGIN | `test_simple_response_allowed_from_cors_origin` | `tests/api/test_cors.py` |
| 38 | Preflight rechazado desde otro origen | `test_preflight_rejected_from_other_origin` | `tests/api/test_cors.py` |
| 39 | Swagger disponible en /api/docs | `test_swagger_served_at_api_docs` | `tests/api/test_openapi.py` |
| 40 | Sin el 422 automático | `test_automatic_422_is_removed` | `tests/api/test_openapi.py` |
| 41 | 400 documentado en una ruta con entrada | `test_400_documented_on_route_with_input` | `tests/api/test_openapi.py` |
| 42 | 409 documentado en una ruta que rechaza | `test_409_documented_on_rejecting_route` | `tests/api/test_openapi.py` |
| 43 | 422 documentado en una ruta que rechaza | `test_422_documented_on_rejecting_route` | `tests/api/test_openapi.py` |
| 44 | El esquema lista todos los códigos de violación | `test_schema_lists_all_violation_codes` | `tests/api/test_openapi.py` |
| 45 | Salud documenta 200 y 503 | `test_health_documents_200_and_503` | `tests/api/test_openapi.py` |
| 46 | Una escritura confirmada persiste | `test_committed_write_persists` | `tests/integration/test_api_session.py` |
| 47 | Una escritura sin confirmar no persiste | `test_uncommitted_write_does_not_persist` | `tests/integration/test_api_session.py` |
| 48 | Una excepción revierte la escritura | `test_exception_rolls_back_write` | `tests/integration/test_api_session.py` |
| 49 | Compose sin secretos | `test_compose_defines_services_without_literal_secrets` | `tests/test_compose.py` |
| 50 | Backend conecta a la base por el nombre del servicio | `test_backend_database_url_uses_postgres_service` | `tests/test_compose.py` |
| 51 | Backend espera a postgres sano | `test_backend_waits_for_healthy_postgres` | `tests/test_compose.py` |
| 52 | Backend espera a redis sano | `test_backend_waits_for_healthy_redis` | `tests/test_compose.py` |
| 53 | Backend migra antes de levantar la app | `test_dockerfile_migrates_before_uvicorn` | `tests/test_compose.py` |
| 54 | Healthcheck del backend contra la API | `test_backend_healthcheck_uses_api_health` | `tests/test_compose.py` |

## Tests adicionales sin escenario en la spec

Estos tests no corresponden a ningún escenario de la spec: verifican D12 del [design](../../openspec/changes/archive/2026-11-06-api-base-fastapi/design.md).

| Qué verifica | Test automático (nombre real en código) | Archivo |
|---|---|---|
| El contenedor corre como usuario sin privilegios | `test_dockerfile_runs_as_non_root` | `tests/test_compose.py` |
| `.dockerignore` excluye artefactos locales | `test_dockerignore_excludes_local_artifacts` | `tests/test_compose.py` |

## Refuerzo de tres tests de Compose

Tres tests pasaban aunque su escenario no se cumpliera. Para cada uno se aplicó la mutación con el test viejo, se reforzó el test, se volvió a aplicar la misma mutación y se restauró. Las tres mutaciones quedaron en [mutaciones-C-18.py](mutaciones-C-18.py).

| Escenario | Mutación | Test viejo | Test nuevo | Restaurado |
|---|---|---|---|---|
| Backend migra antes de levantar la app | `backend/Dockerfile`: `&&` por `;` | Pasa (hueco) | Falla: `assert None` | Pasa |
| Healthcheck del backend contra la API | `docker-compose.yml`: `'/health'` en el healthcheck y `# /api/health` como comentario | Pasa (hueco) | Falla: `assert None` | Pasa |
| Compose sin secretos | `docker-compose.yml`: `JWT_SECRET: clave-ficticia-literal` en `backend` | Pasa (hueco) | Falla: `assert ['backend.JWT_SECRET'] == []` | Pasa |

Qué exige ahora cada test:

- `test_dockerfile_migrates_before_uvicorn`: la línea `CMD` tiene `alembic upgrade head && ` seguido de `uvicorn`, con `exec` opcional.
- `test_backend_healthcheck_uses_api_health`: `/api/health` aparece en el healthcheck del servicio `backend` del Compose parseado con PyYAML.
- `test_compose_defines_services_without_literal_secrets`: `POSTGRES_PASSWORD`, `JWT_SECRET`, `SEED_USER_PASSWORD` y las credenciales de `DATABASE_URL` solo aceptan referencias `${...}`, en el `environment` de cualquier servicio.

`test_literal_secret_is_detected` (9 casos) y `test_env_reference_is_accepted` (5 casos) prueban esa detección con textos literales: valores literales, cadena vacía, `${VAR:-valor}`, forma de lista y credenciales literales en la URL.

Límites conocidos: la detección de secretos mira solo `environment`, no `build.args` ni `command`; el puerto `API_PORT` del backend sigue sin test.

---

## Verificación por mutación

Se regenera con `python ../docs/evidencias/mutaciones-C-18.py` desde `backend/`. El script copia sus textos del código real, muta solo producción (`backend/app/`, `docker-compose.yml`, `backend/Dockerfile`, `backend/.dockerignore`, `knowledge-base/`), corre únicamente el test de cada mutación, restaura el archivo y comprueba que el test vuelva a pasar. La salida completa está en [mutaciones-C-18.txt](mutaciones-C-18.txt); esta tabla se genera desde ese archivo.

<!-- mutaciones:inicio -->
| Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|
| `test_api_dependencies_are_declared` | `backend/pyproject.toml` | `- "fastapi>=0.118,<1",`<br>`+ #"fastapi>=0.118,<1",` | `AssertionError: assert 'fastapi>=0.118,<1' in ['tzdata>=2024.1', 'sqlalchemy>=2,<3', 'alembic>=1.13,<2', 'psycopg[binary]>=3,<4', 'pydantic-settings>=2,<3', 'uvicorn>=0.30,<1', ...]` |
| `test_create_app_accepts_literal_settings` | `backend/app/main.py` | `- app.state.settings = resolved_settings`<br>`+ app.state.settings = None` | `AssertionError: assert None == Settings(app_env='test', api_port=8000, postgres_user='test_user', postgres_db='test_db', redis_url='redis://localhost...mezone='America/Argentina/Buenos_Aires', cors_origin='http://localhost:5173', vite_api_url='http://localhost:8000/api')` |
| `test_create_app_keeps_one_session_factory` | `backend/app/main.py` | `- app.state.session_factory = session_factory`<br>`+ app.state.session_factory = None` | `assert False` |
| `test_get_session_helper_is_removed` | `backend/app/db/session.py` | `+ def get_session(): pass`<br>`+ ` | `AssertionError: assert not True` |
| `test_all_violation_codes_are_classified` | `backend/app/api/errors.py` | `- ViolationCode.PROFESSIONAL_OVERLAP: 409,`<br>`+ # ViolationCode.PROFESSIONAL_OVERLAP: 409,` | `AssertionError: assert {<ViolationCo...NAL_OVERLAP'>} == set()` |
| `test_unclassified_code_is_detected` | `backend/app/api/errors.py` | `- return set(ViolationCode) - set(mapping.keys())`<br>`+ return set()` | `AssertionError: assert set() == {<ViolationCo...AIR_OVERLAP'>}` |
| `test_mixed_codes_use_precedence` | `backend/app/api/errors.py` | `- if 403 in statuses:`<br>`- return 403`<br>`+ if 409 in statuses:`<br>`+ return 409`<br>`- return 409`<br>`+ return 403` | `AssertionError: assert 409 == 422` |
| `test_kb_07_lists_all_violation_codes` | `knowledge-base/07_flujos_principales.md` | `- DUPLICATE_DNI`<br>`+ DNI_CLONADO` | `` AssertionError: assert 'DUPLICATE_DNI' in '# Flujos Principales\n\n## Flujo 1: Dar un turno\n\n> Flujo completo del MVP. C-02 implementa solo el núcleo de domin...`@pytest.mark.parametrize`) y reloj fijo inyectado (`now` como `datetime` UTC literal), sin base de datos ni Docker.\n' `` |
| `test_violation_code_maps_to_status` | `backend/app/api/errors.py` | `- ViolationCode.PROFESSIONAL_OVERLAP: 409,`<br>`+ ViolationCode.PROFESSIONAL_OVERLAP: 422,` | `assert 422 == 409` |
| `test_mixed_rejection_keeps_all_violations_in_order` | `backend/app/api/errors.py` | `- "violations": [serialize_violation(v) for v in exc.rejected.violations]`<br>`+ "violations": [serialize_violation(v) for v in reversed(exc.rejected.violations)]` | `AssertionError: assert ['DUPLICATE_D... 'EMPTY_NAME'] == ['EMPTY_NAME'...UPLICATE_DNI']` |
| `test_overlap_body` | `backend/app/api/schemas.py` | `- serialization_alias="conflictingAppointmentId"`<br>`+ serialization_alias="conflictingAppId"` | `AssertionError: assert {'code', 'con...l', 'message'} == {'code', 'con...l', 'message'}` |
| `test_blocked_time_body` | `backend/app/api/schemas.py` | `- serialization_alias="conflictingBlockId"`<br>`+ serialization_alias="conflictingBlkId"` | `AssertionError: assert {'code', 'con...l', 'message'} == {'code', 'con...l', 'message'}` |
| `test_reference_body` | `backend/app/api/schemas.py` | `- serialization_alias="referenceKind"`<br>`+ serialization_alias="refKind"` | `AssertionError: assert {'code', 'message', 'refKind'} == {'code', 'mes...eferenceKind'}` |
| `test_violation_without_extras_body` | `backend/app/api/schemas.py` | `- exclude_none=True`<br>`+ exclude_none=False` | `AssertionError: assert {'code', 'con...eferenceKind'} == {'code', 'message'}` |
| `test_invalid_json_returns_400` | `backend/app/api/errors.py` | `- "json_invalid": "El cuerpo no es JSON válido.",`<br>`+ "json_invalid": "JSON inválido.",` | `AssertionError: assert 'JSON inválido.' == 'El cuerpo no es JSON válido.'` |
| `test_missing_field_returns_400` | `backend/app/api/errors.py` | `- "missing": "Falta este dato.",`<br>`+ "missing": "Falta dato.",` | `AssertionError: assert 'Falta dato.' == 'Falta este dato.'` |
| `test_sent_value_is_not_returned` | `backend/app/api/errors.py` | `- error_items.append(`<br>`+ error_items.append({"leaked": str(err.get("input"))}); error_items.append(` | `assert 'valor-marcado-c18' not in '{"errors":[...nválido."}]}'` |
| `test_invalid_query_param_returns_400` | `backend/app/api/errors.py` | `- return JSONResponse(status_code=400, content={"errors": error_items})`<br>`+ return JSONResponse(status_code=422, content={"errors": error_items})` | `assert 422 == 400` |
| `test_committed_write_persists` | `backend/app/api/deps.py` | `+ session.commit = session.flush  # type: ignore[method-assign]` | `assert None is not None` |
| `test_uncommitted_write_does_not_persist` | `backend/app/api/deps.py` | `+ session.commit()` | `AssertionError: assert ('uncommitted',) is None` |
| `test_exception_rolls_back_write` | `backend/app/api/deps.py` | `- session.rollback()`<br>`+ session.commit()` | `AssertionError: assert ('exception',) is None` |
| `test_health_returns_503_with_closed_port` | `backend/app/api/health.py` | `- status_code=status.HTTP_503_SERVICE_UNAVAILABLE,`<br>`+ status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,` | `assert 500 == 503` |
| `test_health_returns_200_with_database` | `backend/app/api/health.py` | `- content={"status": "ok", "database": "ok"},`<br>`+ content={"status": "ok", "database": "down"},` | `AssertionError: assert {'database': ...status': 'ok'} == {'database': ...status': 'ok'}` |
| `test_preflight_allowed_from_cors_origin` | `backend/app/main.py` | `- allow_credentials=False,`<br>`+ allow_credentials=True,` | `AssertionError: assert 'access-control-allow-credentials' not in Headers({'vary': 'Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Privat...ss-control-allow-origin': 'http://localhost:5173', 'content-length': '2', 'content-type': 'text/plain; charset=utf-8'})` |
| `test_simple_response_allowed_from_cors_origin` | `backend/app/main.py` | `- allow_origins=[resolved_settings.cors_origin],`<br>`+ allow_origins=["http://localhost:9999"],` | `AssertionError: assert None == 'http://localhost:5173'` |
| `test_preflight_rejected_from_other_origin` | `backend/app/main.py` | `- allow_origins=[resolved_settings.cors_origin],`<br>`+ allow_origins=["*"],` | `AssertionError: assert 'access-control-allow-origin' not in Headers({'vary': 'Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Privat...e, Authorization, Content-Language, Content-Type', 'content-length': '2', 'content-type': 'text/plain; charset=utf-8'})` |
| `test_swagger_served_at_api_docs` | `backend/app/main.py` | `- docs_url="/api/docs",`<br>`+ docs_url="/docs",` | `assert 404 == 200` |
| `test_automatic_422_is_removed` | `backend/app/api/openapi.py` | `- if "HTTPValidationError" in schema_ref:`<br>`+ if False and "HTTPValidationError" in schema_ref:` | `AssertionError: assert '422' not in {'200': {'content': {'application/json': {'schema': {'additionalProperties': {'type': 'string'}, 'title': 'Response Du...plication/json': {'schema': {'$ref': '#/components/schemas/HTTPValidationError'}}}, 'description': 'Validation Error'}}` |
| `test_400_documented_on_route_with_input` | `backend/app/api/openapi.py` | `- if has_input and "400" not in responses:`<br>`+ if False and "400" not in responses:` | `AssertionError: assert '400' in {'200': {'content': {'application/json': {'schema': {'additionalProperties': {'type': 'string'}, 'title': 'Response Dummy Route Dummy Post', 'type': 'object'}}}, 'description': 'Successful Response'}}` |
| `test_409_documented_on_rejecting_route` | `backend/app/api/openapi.py` | `- responses: dict[int \| str, dict[str, Any]] = {}`<br>`+ if 409 in status_codes: return {}`<br>`+ responses: dict[int \| str, dict[str, Any]] = {}` | `AssertionError: assert '409' in {'200': {'content': {'application/json': {'schema': {'additionalProperties': {'type': 'string'}, 'title': 'Response Du...on/json': {'schema': {'$ref': '#/components/schemas/MalformedRequestResponse'}}}, 'description': 'Entrada malformada'}}` |
| `test_422_documented_on_rejecting_route` | `backend/app/api/openapi.py` | `- responses: dict[int \| str, dict[str, Any]] = {}`<br>`+ if 422 in status_codes: return {}`<br>`+ responses: dict[int \| str, dict[str, Any]] = {}` | `AssertionError: assert '422' in {'200': {'content': {'application/json': {'schema': {'additionalProperties': {'type': 'string'}, 'title': 'Response Du...on/json': {'schema': {'$ref': '#/components/schemas/MalformedRequestResponse'}}}, 'description': 'Entrada malformada'}}` |
| `test_schema_lists_all_violation_codes` | `backend/app/api/schemas.py` | `- code: ViolationCode`<br>`+ code: str` | `KeyError: 'enum'` |
| `test_health_documents_200_and_503` | `backend/app/api/health.py` | `- 503: {`<br>`+ 500: {` | `AssertionError: assert '503' in {'200': {'content': {'application/json': {'example': {'database': 'ok', 'status': 'ok'}, 'schema': {'$ref': '#/compone...vailable'}, 'schema': {'$ref': '#/components/schemas/HealthResponse'}}}, 'description': 'Base de datos no disponible'}}` |
| `test_compose_defines_services_without_literal_secrets` | `docker-compose.yml` | `- backend:`<br>`+ api_svc:` | `assert 'backend:' in 'services:\n  postgres:\n    image: postgres:16\n    ports:\n      - "5432:5432"\n    environment:\n      POSTGRES_USE...\n      - ./frontend:/app\n      - /app/node_modules\n    depends_on:\n      - backend\n\nvolumes:\n  turnos_pgdata:\n'` |
| `test_backend_database_url_uses_postgres_service` | `docker-compose.yml` | `- @postgres:5432`<br>`+ @localhost:5432` | `assert 'DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:***@postgres:5432/${POSTGRES_DB}' in 'services:\n  postgres:\n    image: postgres:16\n    ports:\n      - "5432:5432"\n    environment:\n      POSTGRES_USE...\n      - ./frontend:/app\n      - /app/node_modules\n    depends_on:\n      - backend\n\nvolumes:\n  turnos_pgdata:\n'` |
| `test_backend_waits_for_healthy_postgres` | `docker-compose.yml` | `- condition: service_healthy`<br>`+ condition: service_started` | `AssertionError: assert 'postgres:\n        condition: service_healthy' in 'backend:\n    build: ./backend\n    env_file: .env\n    environment:\n      DATABASE_URL: postgresql+psycopg://${POST...\n      - ./frontend:/app\n      - /app/node_modules\n    depends_on:\n      - backend\n\nvolumes:\n  turnos_pgdata:\n'` |
| `test_backend_waits_for_healthy_redis` | `docker-compose.yml` | `- condition: service_healthy`<br>`+ condition: service_started` | `AssertionError: assert 'redis:\n        condition: service_healthy' in 'backend:\n    build: ./backend\n    env_file: .env\n    environment:\n      DATABASE_URL: postgresql+psycopg://${POST...\n      - ./frontend:/app\n      - /app/node_modules\n    depends_on:\n      - backend\n\nvolumes:\n  turnos_pgdata:\n'` |
| `test_backend_healthcheck_uses_api_health` | `docker-compose.yml` | `- '/api/health'`<br>`+ '/health'` | `assert None` |
| `test_dockerfile_runs_as_non_root` | `backend/Dockerfile` | `- USER appuser`<br>`+ USER root` | `assert 'USER appuser' in 'FROM python:3.13-slim\nENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1\nWORKDIR /app\nCOPY pyproject.toml ./\nCOPY a... "-c", "alembic upgrade head && exec uvicorn --factory app.main:create_app --host 0.0.0.0 --port \\"$API_PORT\\""]\n\n'` |
| `test_dockerfile_migrates_before_uvicorn` | `backend/Dockerfile` | `- alembic upgrade head &&` | `assert None` |
| `test_dockerfile_migrates_before_uvicorn` | `backend/Dockerfile` | `- alembic upgrade head && exec`<br>`+ alembic upgrade head ; exec` | `assert None` |
| `test_backend_healthcheck_uses_api_health` | `docker-compose.yml` | `- '/api/health', timeout=2)"]`<br>`+ '/health', timeout=2)"]  # /api/health` | `assert None` |
| `test_compose_defines_services_without_literal_secrets` | `docker-compose.yml` | `+ JWT_SECRET: clave-ficticia-literal` | `AssertionError: assert ['backend.JWT_SECRET'] == []` |
| `test_dockerignore_excludes_local_artifacts` | `backend/.dockerignore` | `- .venv`<br>`+ .local_venv` | `AssertionError: assert '.venv' in '.local_venv\ntests\n__pycache__\n.mypy_cache\n.pytest_cache\n\n'` |
| `test_readme_warns_about_reserved_password_characters` | `backend/README.md` | `- caracteres reservados`<br>`+ caracteres permitidos` | `` AssertionError: assert 'caracteres reservados' in '# backend — turnos-odontologia\n\nbackend en python del sistema de agenda de turnos: proyecto instalable, `pytest`,\n...s y un futuro seed; no ejecuta i/o ni contiene secretos. importa entidades del dominio; el dominio nunca lo importa.\n' `` |
<!-- mutaciones:fin -->

---

## Versiones de dependencias instaladas (Tarea 1.2)

- `fastapi`: 0.162.0
- `uvicorn`: 0.54.0
- `httpx`: 0.28.1
- `python-dotenv`: 1.2.4
- `pyyaml`: 6.0.3 (solo `dev`)
- `types-PyYAML`: 6.0.12.20261103 (solo `dev`)

## Desvíos

- **Mutaciones con el detector de C-23**: con `--tb=long` el detector no encontraba frames y marcaba las 45; el script ahora corre con `--tb=short`, tiene `--check`, el arreglo de CRLF, el detector de inválidas y un SHA-256 de `backend/app` y de los archivos mutados fuera de él (`b0b97…`). La única inválida real era la 19 (`yield None` hacía fallar la ruta con `AttributeError` dentro de FastAPI); se reescribió para que el `commit` de la sesión sea solo un `flush`, y la detecta `assert row is not None`. Las mutaciones de `docker-compose.yml` siguen aplicando tal cual tras el servicio `frontend` de C-25.
