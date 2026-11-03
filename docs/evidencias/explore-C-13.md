# Explore C-13

El explore lo hizo Copilot y las decisiones D1 a D12 las cerró la autora el
2026-11-02. Este documento registra el alcance acordado para C-13; no
implementa código ni infraestructura.

## Inventario

- Existe el backend Python instalable en `backend/`, con `pytest`, `mypy
  --strict`, `tzdata` y el dominio puro en `backend/app/domain`.
- La guardia de dependencias del dominio impide importar SQLAlchemy, Redis,
  FastAPI, Pydantic o I/O desde `backend/app/domain`.
- La KB 08 define Compose, las variables de entorno, los puertos 5432 y 6379,
  los servicios `postgres` y `redis`, y la separación entre dominio e
  infraestructura.
- La KB 09 fija PostgreSQL con SQLAlchemy (DD-03), Compose (DD-05), UTC
  (DD-07), Redis sin uso funcional en el MVP (DD-10/SU-11) y Alembic como
  supuesto posterior (SU-10).
- C-13 debe crear solo PostgreSQL, Redis, configuración, sesión y soporte de
  tests de integración. C-18 agregará backend y C-25 frontend al Compose.
- No existen todavía `docker-compose.yml`, `.env.example`, `app/config.py`,
  `app/db/session.py`, dependencias SQLAlchemy/psycopg, fixtures de
  integración ni tests de PostgreSQL.
- C-14 agregará Alembic; C-15 agregará persistencia de catálogos y pacientes.

## Decisiones

### D1 — Driver y sesión

Se usará psycopg 3 con SQLAlchemy 2.x en modo síncrono. El MVP no tiene
funcionalidades asincrónicas y la sesión síncrona simplifica transacciones,
fixtures y el futuro uso de FastAPI en C-18. No se usará psycopg2 ni asyncpg.

### D2 — Configuración

`backend/app/config.py` usará `pydantic-settings`. Una variable obligatoria
faltante producirá un error claro al cargar la configuración y nombrará la
variable. No habrá valores por defecto para secretos ni para `DATABASE_URL`.

### D3 — Variables y secretos

`.env.example` estará en la raíz y contendrá todos los nombres de la tabla de
KB 08, sin valores ni credenciales:

`APP_ENV`, `API_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MIN`,
`SEED_USER_PASSWORD`, `APP_TIMEZONE`, `CORS_ORIGIN`, `VITE_API_URL`.

`.env` permanecerá ignorado por Git. No se agregará una variable específica
para la base de test.

### D4 — Base de test

Una fixture de pytest de alcance de sesión derivará `<POSTGRES_DB>_test`, la
creará si no existe y la reutilizará. Cada test correrá dentro de una
transacción que se deshace al terminar. La fixture nunca borrará ni modificará
la base real.

### D5 — Tests de integración

La marca `integration` se registrará en `backend/pyproject.toml` y se
excluirá por defecto mediante `addopts = "-m \"not integration\""`. La suite
de integración se ejecutará explícitamente con `pytest -m integration`.

### D6 — UTC

Cada conexión SQLAlchemy ejecutará `SET TIME ZONE 'UTC'` mediante un evento de
conexión. Las columnas temporales serán `timestamptz`. El test de ida y vuelta
guardará un instante con zona `-03:00` y verificará que el mismo instante
vuelva representado en UTC.

### D7 — Compose

El Compose de la raíz tendrá solo:

- `postgres` con imagen `postgres:16`, `5432:5432`, volumen nombrado
  `turnos_pgdata` y healthcheck `pg_isready`.
- `redis` con imagen `redis:7`, `6379:6379` y healthcheck `redis-cli ping`.

Usuario, contraseña y base de PostgreSQL se leerán de `.env`. No se agregarán
los servicios `backend` ni `frontend`, que corresponden a C-18 y C-25.

### D8 — Dependencias

Se declararán como dependencias de runtime:

- `sqlalchemy>=2,<3`
- `psycopg[binary]>=3,<4`
- `pydantic-settings>=2,<3`

No se inventan versiones más específicas.

### D9 — Ejecución de integración

Los tests de integración correrán desde Windows, en el host, contra
`localhost:5432`.

### D10 — Aislamiento del dominio

`config.py` y `db/` vivirán fuera de `backend/app/domain`. La guardia de
dependencias del dominio no se modificará.

### D11 — Gobernanza

No habrá punto de control adicional en `tasks.md`. La última tarea verificará
todo lo versionado en busca de contraseñas y URLs con credenciales, y fallará
si encuentra secretos.

### D12 — Capacidad OpenSpec

Se agrega la capacidad `database-infrastructure` como spec nueva. No se
modifican las cinco capacidades existentes.

## Riesgos y pendientes

- La base de test necesita permisos para `CREATE DATABASE`.
- La reutilización de una base de test exige aislamiento transaccional correcto.
- El puerto 5432 está libre en el entorno de la autora, pero puede estar
  ocupado en otras máquinas.
- El volumen nombrado persiste entre ejecuciones; no se debe usar `down -v`
  durante la verificación normal.

