# Design

## Context

La motivación está en `proposal.md` y el análisis de alternativas completo en `docs/evidencias/explore-C-18.md`. La autora aceptó las 15 decisiones con la opción recomendada; acá quedan como contrato, con las precisiones que agregó.

Restricciones que dan forma al diseño:

- `ViolationCode` tiene 20 valores y `Rejected` es un único tipo, compartido por agenda y catálogos.
- Los repositorios nunca hacen `commit`; los servicios de C-17 sí (D5 de su `design.md`), pero todavía no existen.
- `get_session` (`app/db/session.py:60`) crea un engine por llamada y no tiene usos.
- FastAPI, uvicorn y httpx no están instalados en `backend/.venv`.
- C-16 y C-17 siguen activos en `backend/`, sin archivos en común con este change.

## Goals / Non-Goals

**Goals:**

- Dejar un contrato HTTP único para errores, que C-19 a C-24 reutilizan sin reescribir.
- Probar ese contrato con la app real, sin endpoints de negocio y sin mocks.
- Que el compose levante la API con el esquema migrado.

**Non-Goals:**

- JWT, `401` y el botón *Authorize* de Swagger (C-19).
- Endpoints de negocio y sus esquemas (C-20 a C-24).
- Servicios transaccionales (C-17).
- Servicio `frontend` (C-25).
- Cliente de Redis y cualquier uso funcional (SU-11).
- Cambios en `app/domain`: el mapeo a HTTP vive en `app/api`.

## Decisions

### D1 — Tabla completa `ViolationCode` → status HTTP

Un `Mapping[ViolationCode, int]` en `app/api/errors.py`, sin valor por defecto. `unclassified_codes(mapping)` devuelve los códigos faltantes: un test lo llama con la tabla real y otro con una tabla incompleta.

| # | `ViolationCode` | Status | Motivo | Fuente |
|---|-----------------|--------|--------|--------|
| 1 | `PROFESSIONAL_OVERLAP` | 409 | Choca con otro turno del profesional | KB 07, Flujo 1 |
| 2 | `CHAIR_OVERLAP` | 409 | Choca con otro turno del sillón | KB 07, Flujo 1 |
| 3 | `OUTSIDE_WORKING_HOURS` | 409 | Conflicto con la agenda del profesional | KB 07 paso 7; design de C-05 |
| 4 | `BLOCKED_TIME` | 409 | Conflicto con un bloqueo existente | Design de C-06 |
| 5 | `DUPLICATE_DNI` | 409 | Choca con un paciente existente | `CHANGES.md` (C-20) |
| 6 | `DUPLICATE_NAME` | 409 | Choca con un registro existente | `CHANGES.md` (C-20) |
| 7 | `UNKNOWN_REFERENCE` | 422 | El pedido apunta a algo inexistente | KB 07 |
| 8 | `INACTIVE_REFERENCE` | 422 | Grupo 1, validez del pedido | Design de C-03 |
| 9 | `INVALID_DURATION` | 422 | Grupo 1, validez del pedido | Design de C-03 |
| 10 | `INVALID_START_TIME` | 422 | Grupo 1, no depende de la agenda | Design de C-04 |
| 11 | `CROSSES_MIDNIGHT` | 422 | Grupo 1, no depende de la agenda | Design de C-04 |
| 12 | `IN_THE_PAST` | 422 | Validez del pedido | KB 07; design de C-07 |
| 13 | `INVALID_WORKING_HOURS` | 422 | Tramo inválido en sí mismo | Inferido de RN-DI-02 |
| 14 | `OVERLAPPING_WORKING_HOURS` | 422 | Tramos enviados inconsistentes entre sí | `CHANGES.md` (C-21) |
| 15 | `INVALID_BLOCK` | 422 | `inicio >= fin` | Design de C-06 |
| 16 | `INVALID_DNI` | 422 | Formato inválido | Inferido |
| 17 | `EMPTY_NAME` | 422 | Dato inválido | Inferido |
| 18 | `STATUS_CHANGE_TOO_EARLY` | 422 | Precondición de tiempo | KB 07, Flujo 3 |
| 19 | `INVALID_TRANSITION` | 422 | Ver D3 | KB 07 |
| 20 | `FORBIDDEN_OPERATION` | 403 | Ver D2 | KB 07, Flujo 3; `CHANGES.md` (C-23) |

### D2 — `FORBIDDEN_OPERATION` responde `403`

Con el cuerpo `{ "violations": [...] }`. KB 07 y C-23 piden `403` por rol y por propiedad, y el dominio garantiza que este código viene solo. *Alternativa descartada*: `422`, que contradice KB 07 y separa el `403` de rol (C-19) del de propiedad.

### D3 — `INVALID_TRANSITION` responde `422`

KB 07 es la fuente de verdad. El dominio puede devolverlo junto con `STATUS_CHANGE_TOO_EARLY`, y con `422` ese resultado no mezcla status. *Alternativa descartada*: `409`, que crearía un caso mixto dentro del ciclo de vida.

**Corrección hecha en este propose**: `CHANGES.md:546`, en el alcance de C-23, pasó de `409` a `422`. Es la única edición permitida en `CHANGES.md`.

### D4 — Precedencia `403 > 422 > 409` con códigos mixtos

Función pura `status_for(violations)`. El cuerpo lleva la lista completa, en el orden del dominio. Los dos casos mixtos reales están en `catalog/create.py`: `EMPTY_NAME` + `DUPLICATE_DNI` y `DUPLICATE_NAME` + `INVALID_DURATION`. *Alternativas descartadas*: `409 > 422`, que contradice el orden de grupos de RN-AG-12; y separar en el dominio, que cambia specs archivadas de C-09.

### D5 — Cuerpo `{ "violations": [...] }` en camelCase, con excepción de borde

camelCase, consistente con KB 07 (`patientId`, `startAt`, `durationMin`). Los campos en `None` se omiten, como en el ejemplo de KB 07.

| Campo JSON | Tipo | Campo del dominio | Presente en |
|------------|------|-------------------|-------------|
| `code` | `ViolationCode` | `code` | Siempre |
| `message` | string en español | `message` | Siempre |
| `conflictingAppointmentId` | UUID | `conflicting_appointment_id` | Solapamientos |
| `conflictingBlockId` | UUID | `conflicting_block_id` | `BLOCKED_TIME` |
| `conflictingInterval` | `{ startAt, endAt }` ISO-8601 UTC | `conflicting_interval` (`start`, `end`) | Solapamientos y `BLOCKED_TIME` |
| `referenceKind` | `PATIENT`, `PROFESSIONAL`, `CHAIR`, `SERVICE` | `reference_kind` | Referencias |

```json
{
  "violations": [
    {
      "code": "PROFESSIONAL_OVERLAP",
      "message": "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (turno a1b2).",
      "conflictingAppointmentId": "00000000-0000-0000-0000-00000000a1b2",
      "conflictingInterval": { "startAt": "2026-10-20T13:00:00Z", "endAt": "2026-10-20T13:30:00Z" }
    }
  ]
}
```

Las rutas lanzan `DomainRejectedError(rejected)` y un handler global arma la respuesta. No rompe la regla dura: el dominio sigue devolviendo resultados tipados y solo el borde HTTP lanza. *Alternativa descartada*: un helper que devuelve `JSONResponse`, que repite la bifurcación en cada ruta.

### D6 — `RequestValidationError` responde `400` con cuerpo `errors`

```json
{
  "errors": [
    { "field": "startAt", "type": "missing", "message": "Falta este dato." },
    { "field": null, "type": "json_invalid", "message": "El cuerpo no es JSON válido." }
  ]
}
```

Cubre cuerpo, JSON roto, path y query. `field` se arma con `loc` sin su primer elemento. Los mensajes salen de una tabla corta por `type`, con un texto genérico en español como respaldo. **Nunca** se devuelven `input`, `ctx` ni `url`, porque `input` expondría contraseñas de login. *Alternativas descartadas*: sobre `violations` con `MALFORMED_REQUEST`, que no es un `ViolationCode`; y reenviar `exc.errors()`, por la fuga de datos.

### D7 — `/api/health` hace `SELECT 1`

`200 { "status": "ok", "database": "ok" }`. Ante `SQLAlchemyError`, `503 { "status": "unavailable", "database": "unavailable" }`, sin texto del error. Ruta pública (KB 03), definida con `def`. Se agrega `connect_args={"connect_timeout": 3}` en `create_database_engine`. *Alternativas descartadas*: comparar la revisión de Alembic, porque el contenedor ya migra antes de levantar; y hacer ping a Redis, sin uso (SU-11).

### D8 — CORS con lista cerrada

`allow_origins=[settings.cors_origin]`, `allow_credentials=False`, métodos `GET, POST, PUT, PATCH, DELETE`, headers `Authorization, Content-Type`. El JWT viaja en un header, no en cookies. *Alternativas descartadas*: comodines, más permisivos de lo que pide KB 08; y varios orígenes, porque `CORS_ORIGIN` es singular.

### D9 — Transformación del esquema OpenAPI en `app/api/openapi.py`

A toda operación con parámetros o cuerpo: se le quita el `422` automático y se le agrega `400` con `MalformedRequestResponse`. Se quitan del esquema `HTTPValidationError` y `ValidationError`. Las respuestas de negocio se declaran por ruta con `responses=violation_responses(409, 422)`, con un ejemplo ficticio en español. Un `422` declarado por la ruta se conserva. URLs: `docs_url="/api/docs"`, `openapi_url="/api/openapi.json"`, `redoc_url=None`. *Alternativas descartadas*: declarar todo a mano, que no resuelve los `GET` sin `422` de negocio; y `responses` a nivel de router, que documenta errores que muchas rutas no pueden dar.

**Límite para el video**: en C-18 Swagger muestra solo `/api/health`. Los `400`, `409` y `422` se ven con el primer endpoint con cuerpo (C-19 o C-20). Swagger UI carga sus archivos desde un CDN: al grabar hace falta internet.

### D10 — La dependencia de sesión nunca confirma

```python
def get_db_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
```

**Regla**: confirma quien es dueño de la escritura, el servicio o caso de uso, nunca la ruta ni la dependencia. Encaja con C-17 D5 sin tocarlo (`auto_commit=True`). C-20 y C-21 necesitan un caso de uso fino que haga `commit`. *Alternativas descartadas*: unidad de trabajo en la dependencia, porque desde FastAPI 0.118 el código tras el `yield` corre después de enviar la respuesta y el cliente podría recibir un `201` con un `commit` fallido; y `scope="function"` con `auto_commit=False`, que reescribe el contrato de C-17.

**Aviso para C-17**: C-19 leerá el usuario con esta sesión, lo que abre una transacción implícita. `with session.begin():` lanzaría `InvalidRequestError`; el `begin_nested()` de su D5 no. Hay que mantenerlo.

### D11 — Factory `create_app` con engine único, y se borra `get_session`

`create_app(settings: Settings | None = None)` guarda el session factory en `app.state`, y `lifespan` hace `engine.dispose()` al cerrar. Se levanta con `uvicorn --factory app.main:create_app`. **`get_session` se borra**: la autora verificó que no tiene usos. Estructura: `app/main.py` y `app/api/{errors,schemas,deps,health,openapi}.py`. Rutas con `def`, porque SQLAlchemy y psycopg se usan de forma síncrona.

*Desvío de una convención*: la skill `fastapi` recomienda `fastapi run`, pensado para un `app` a nivel de módulo, que obligaría a tener un entorno completo con solo importar `app.main`.

### D12 — `backend/Dockerfile`

```dockerfile
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY alembic ./alembic
RUN useradd --create-home appuser
USER appuser
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn --factory app.main:create_app --host 0.0.0.0 --port \"$API_PORT\""]
```

Contexto de build `./backend`, así que `.env` queda fuera. Más `backend/.dockerignore` con `.venv`, `tests`, `__pycache__`, `.mypy_cache` y `.pytest_cache`. Python 3.13 es la versión con la que corrió toda la evidencia. *Alternativas descartadas*: `python:3.12-slim`, nunca ejecutada en este repo; y el comando en el compose, que obliga a escapar `$$`.

### D13 — Servicio `backend` y `MODIFIED` de "Compose reproducible"

```yaml
backend:
  build: ./backend
  env_file: .env
  environment:
    DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    REDIS_URL: redis://redis:6379/0
  ports:
    - "${API_PORT}:${API_PORT}"
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ['API_PORT'] + '/api/health', timeout=2)"]
    interval: 10s
    timeout: 3s
    retries: 5
    start_period: 15s
```

El `DATABASE_URL` de `.env` no se cambia, porque lo usan los tests de integración desde el host. El seed no corre al arrancar. *Alternativas descartadas*: variable nueva `DOCKER_DATABASE_URL`, que repite la contraseña y cambia KB 08; y armar la URL en un entrypoint, otro archivo solo para esto.

**Escenarios del requisito vigente**, listados con `openspec show database-infrastructure --type spec` antes de escribir el `MODIFIED`. Tiene uno solo:

| Escenario vigente | Qué pasa | Motivo |
|-------------------|----------|--------|
| "Compose sin secretos" | **Se conserva con el mismo nombre, con dos cambios** | Ver abajo |

Cambios en ese escenario:

1. "aparecen los dos servicios" pasa a "aparecen los servicios `postgres`, `redis` y `backend`". **Motivo**: el servicio `backend` es el alcance de C-18.
2. "ni URLs con credenciales" pasa a "ni URLs con credenciales literales". **Motivo**: la `DATABASE_URL` del backend es una plantilla con `${POSTGRES_USER}` y `${POSTGRES_PASSWORD}`, sin ningún valor. La garantía se mantiene: el secreto sigue solo en `.env`. **Esto debilita el texto original, y es la decisión que la autora aceptó en D13.**

Texto del requisito: se reemplaza "SHALL definir solo `postgres:16` y `redis:7`" por los tres servicios, se agrega el puerto `API_PORT`, y se agrega una frase sobre dependencias sanas y esquema migrado. Se agregan cinco escenarios nuevos. El resto no cambia.

`backend/tests/test_compose.py` cambia en consecuencia: se quitan `"backend:" not in content` y `"postgresql+psycopg://" not in content`, y se conserva `"turnos_local_dev" not in content`.

### D14 — Dependencias nuevas, con `pip install` como paso explícito

- En `dependencies`: `fastapi>=0.118,<1`, `uvicorn>=0.30,<1` y `python-dotenv>=1,<2`, que `config.py` importa directamente.
- En `dev`: `httpx>=0.27,<1`.
- El piso `0.118` fija el comportamiento de `yield` de D10, y es compatible con el `0.110+` de KB 02.
- **El apply necesita `pip install` y red solo para estas dependencias**: es la tarea 1.2.

*Alternativa descartada*: `fastapi[standard]`, que suma paquetes sin uso y deja `httpx` en producción.

### D15 — Probar el mapeo con la app real y rutas agregadas por el test

Una fixture llama a `create_app(settings_literales)` y le monta un `APIRouter` definido en el test, cuya ruta lanza `DomainRejectedError` con **tipos reales del dominio**, a través del handler y el `TestClient` reales. El engine conecta de forma perezosa, así que estos tests no tocan la base. No se usan mocks, `monkeypatch` ni `dependency_overrides`. El `503` usa un puerto obtenido abriendo un socket en el puerto `0` y cerrándolo, así queda realmente cerrado. *Alternativas descartadas*: ruta de prueba en la app protegida por `APP_ENV`, que entra en producción y en Swagger; y probar solo `status_for`, que no cubre el handler.

## Risks / Trade-offs

- **[Riesgo] Trabajo en paralelo en `backend/`**: `alembic upgrade head` corre en el arranque del contenedor y en los tests de integración, así que una migración de C-17 a medio hacer los rompe → La verificación con Docker e integración se hace con el árbol estable, y se registra el estado en `verify-C-18.md`.
- **[Riesgo] `500` sin headers de CORS**: el handler de errores no controlados corre fuera de `CORSMiddleware` (a comprobar en el apply) → Se acepta en el MVP; la UI muestra un mensaje genérico.
- **[Riesgo] Tipos estrictos**: `mypy --strict` puede exigir ajustes en los handlers y en la transformación de OpenAPI, y la regla prohíbe `Any` → `@app.exception_handler` y `object` con narrowing.
- **[Riesgo] El `422` automático**: la forma exacta de quitarlo depende de la versión instalada → El test de la tarea 6.1 lo fija contra el esquema real, no contra la implementación.
- **[Riesgo] Contraseña con caracteres reservados en `.env`**: rompe la URL interpolada de D13 → Se documenta en `backend/README.md`.
- **[Trade-off] Dos formas de error en la UI** (`errors` y `violations`) → Un `400` es un error de programación, o algo que el formulario ya evita.
- **[Trade-off] Un `commit` olvidado pierde la escritura** → Lo detecta un test de integración, y es más seguro que confirmar de más.

## Migration Plan

1. Instalar las dependencias (tarea 1.2).
2. Implementar por grupos, en el orden de `tasks.md`.
3. Levantar con `docker compose up --build -d backend`, con el árbol estable.

Rollback: revertir el commit del change. El esquema no cambia, porque C-18 no agrega migraciones.

## Puntos pendientes fuera de este change

- `CHANGES.md:470` sigue diciendo "`409` o `422`" sin mencionar el `403` de D2. No se edita porque la línea 546 es la única edición permitida en ese archivo; la decisión vigente es la de este `design.md`.
- El requisito nuevo `api-foundation` no lleva `## Purpose`, por el pedido de que no haya texto antes del primer requisito. Al archivar, la spec principal queda con un `TBD` en `Purpose` que hay que completar a mano.
