# Proposal

## Why

La API de C-18 no sabe quién llama, y los changes C-20 a C-24 necesitan identidad, rol y `Actor` para aplicar la matriz RBAC y firmar el historial. La cátedra exige JWT (DD-11), y tiene que quedar antes de cualquier endpoint de negocio para que ninguno nazca sin protección.

## What Changes

- Tabla `app_user` con migración propia: usuario único en minúsculas, hash, rol con `CHECK`, `active`, y la regla en la base de que el odontólogo tiene `professional_id` y los demás roles no, con un usuario como máximo por profesional.
- Contraseñas con Argon2id y parámetros fijos en código, sin ninguna configuración que baje el costo.
- `POST /api/auth/login` (JSON, con `Cache-Control: no-store`) y `GET /api/auth/me`. Token HS256 con exactamente `sub`, `role` y `exp`.
- Mismo `401`, idéntico byte por byte, para usuario inexistente, contraseña incorrecta y usuario inactivo. Siempre se verifica un hash, ficticio si el usuario no existe.
- Cuerpo propio de `401`, `{ "code", "message" }`, que no se mezcla con `{ "violations": [...] }` ni agrega códigos al dominio.
- En cada request se lee el usuario: inexistente, inactivo o con un rol distinto al del token responde `401` en el request siguiente al cambio.
- Matriz RBAC de KB 03 como tabla de datos, con 34 combinaciones y 102 celdas. `require_permission` responde `403` con `FORBIDDEN_OPERATION`. Rechazo por defecto, con tests guardianes sobre todas las rutas.
- `Actor` del dominio armado desde el usuario autenticado.
- Seed de un usuario por rol. Si `SEED_USER_PASSWORD` falta o no sirve, no se escribe nada; con `APP_ENV=production` se niega a correr.
- Botón *Authorize* en Swagger, con `401` y `403` documentados.
- Hash, contraseña y secretos fuera de respuestas, logs y mensajes de error.
- **BREAKING** (solo configuración local): `JWT_SECRET` exige al menos 32 caracteres y `JWT_ALGORITHM` solo admite `HS256`. La API no arranca con un `.env` que no lo cumpla.
- `SEED_USER_PASSWORD` deja de ser obligatoria para la API. No se agregan variables de entorno.

## Capabilities

### New Capabilities

- `authentication-and-rbac`: login, emisión y verificación de tokens, usuario autenticado, matriz de permisos, rechazo por defecto, armado del `Actor`, protección de secretos y documentación de seguridad en OpenAPI.

### Modified Capabilities

- `database-infrastructure`: tabla y migración de usuarios, seed por rol, excepción de `SEED_USER_PASSWORD` en "Configuración completa y errores explícitos", y los ciclos de downgrade de las migraciones 03 y 04, que pasan a revisiones explícitas.

## Impact

- **Código nuevo**: `backend/app/auth/`, `backend/app/repositories/users.py`, `backend/app/api/auth.py`, `backend/alembic/versions/20261106_06_usuarios.py`, y sus tests en `backend/tests/auth/`, `backend/tests/api/` y `backend/tests/integration/`.
- **Código modificado**: `backend/app/config.py`, `backend/app/db/session.py` (`hide_parameters`), `backend/app/db/models.py`, `backend/app/db/seed.py`, `backend/app/demo_data.py`, `backend/app/main.py`, `backend/app/api/deps.py`, `backend/app/api/errors.py`, `backend/app/api/openapi.py`, `backend/pyproject.toml`.
- **Tests existentes que cambian**: `tests/test_config.py`, `tests/test_persistence_metadata.py`, `tests/api/conftest.py`, `tests/integration/conftest.py`, `tests/integration/test_catalog_persistence.py`, `tests/integration/test_database_infrastructure.py`.
- **Dependencias**: `PyJWT` y `argon2-cffi`.
- **Documentación**: KB 03, 04, 08, 09 y 10, y `backend/README.md`. Las líneas de `CHANGES.md` quedan anotadas en `design.md` para que las corrija la autora.
- **Sin cambios**: `backend/app/domain`, `docker-compose.yml`, `.env.example`.
- **Precondición**: el apply arranca con C-18 archivado. Este propose se apoya solo en su `design.md`.
- **Acción de la autora**: revisar que su `.env` local cumpla las validaciones nuevas; el agente no lo lee.
