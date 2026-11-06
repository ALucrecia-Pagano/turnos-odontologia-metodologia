# Proposal

## Why

El dominio y la persistencia ya rechazan turnos inválidos con violaciones tipadas, pero nada los expone por HTTP, y C-19 a C-24 necesitan una base común para no resolver cada uno los errores, la sesión de base y el arranque. Además, el TP exige mostrar Swagger, así que la documentación de errores tiene que nacer correcta en esta base.

## What Changes

- Nueva app FastAPI bajo `/api`, creada por una factory con un único engine, y `GET /api/health` con chequeo de la base (`200` o `503`).
- Traducción uniforme de rechazos del dominio a HTTP con `{ "violations": [...] }`: 6 códigos a `409`, 13 a `422` y `FORBIDDEN_OPERATION` a `403`, con precedencia `403 > 422 > 409` cuando se mezclan.
- Entrada malformada a `400` con cuerpo `{ "errors": [...] }`, en español y sin devolver lo enviado, en lugar del `422` por defecto de FastAPI.
- Sesión de base por request que revierte ante excepción y cierra, y que nunca confirma: confirma el servicio dueño de la escritura.
- CORS limitado a `CORS_ORIGIN`.
- Swagger en `/api/docs` sin el `422` automático y con las respuestas de error documentadas.
- `backend/Dockerfile` y servicio `backend` en el compose, que espera a `postgres` y `redis` sanos y corre `alembic upgrade head` al arrancar.
- **BREAKING** (solo interno): se elimina `get_session` de `app/db/session.py`, sin usos en el código.
- Corrección de `CHANGES.md`: `INVALID_TRANSITION` pasa de `409` a `422`, porque KB 07 es la fuente de verdad.

## Capabilities

### New Capabilities

- `api-foundation`: salud del servicio, contrato de errores HTTP, sesión por request, CORS y documentación OpenAPI, comunes a toda la API.

### Modified Capabilities

- `database-infrastructure`: el requisito "Compose reproducible" deja de limitar el compose a `postgres` y `redis`, y admite una `DATABASE_URL` interpolada sin valores literales.

## Impact

- **Código nuevo**: `backend/app/main.py`, `backend/app/api/`, `backend/tests/api/`, `backend/Dockerfile`, `backend/.dockerignore`.
- **Código modificado**: `backend/app/db/session.py` (timeout de conexión; se borra `get_session`), `backend/pyproject.toml`, `docker-compose.yml`, `backend/tests/test_compose.py`, `backend/README.md`.
- **Dependencias**: `fastapi`, `uvicorn`, `python-dotenv` y, en desarrollo, `httpx`.
- **Documentación**: `knowledge-base/07_flujos_principales.md` y una línea de `CHANGES.md`.
- **Sin cambios**: `backend/app/domain` y los repositorios. C-19 a C-24 construyen sobre esta base.
- **Trabajo en paralelo**: C-16 y C-17 siguen activos en `backend/`, sin archivos en común con este change.
