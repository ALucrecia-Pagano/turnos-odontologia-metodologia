# Explore C-18 — `api-base-fastapi`

Fecha: 2026-11-05
Fase: 5 — API REST FastAPI y JWT
Governance: **MEDIO** (implementar con puntos de control; presentar decisiones no obvias para revisión)
Dependencias en `CHANGES.md`: `C-14` (`migraciones-alembic`), completada (`verify-C-14.md`). C-18 no depende de C-15, C-16 ni C-17.

> Este explore no ejecutó docker, pytest ni pip. Lo que depende del comportamiento de FastAPI, que todavía no está instalado en `backend/.venv`, sale de su documentación oficial o queda marcado como **a comprobar en el RED**.

---

## 1. Alcance de C-18 según `CHANGES.md` y qué queda afuera

### Qué entra en C-18

1. **`backend/app/main.py`**: app FastAPI con prefijo `/api`, CORS solo para `CORS_ORIGIN` y `GET /api/health` con chequeo de la base.
2. **Manejo de errores uniforme**: violaciones del dominio → `409` o `422` con `{ "violations": [...] }`; entrada malformada → `400`, en lugar del `422` por defecto de FastAPI.
3. **Sesión de base por request** con `Depends`.
4. **`backend/Dockerfile` y servicio `backend`** en `docker-compose.yml`: espera a `postgres` y `redis` sanos, corre `alembic upgrade head` y levanta la app en `API_PORT`.
5. **Tests con `TestClient`**: salud, `400` por cuerpo malformado, una violación de prueba mapeada a `409` y a `422`, CORS.

Se agrega por pedido de la autora: **Swagger documenta también las respuestas de error**, porque hay que mostrarlo en el video del TP.

### Qué queda explícitamente afuera

- **C-19**: JWT, `user`, `get_current_user`, `require_permission`, `401`, y el botón *Authorize* de Swagger.
- **C-20 a C-24**: todo endpoint de negocio y sus esquemas de entrada. C-18 solo expone `/api/health`.
- **C-17**: `backend/app/services/appointments.py` y sus commits. C-18 define la sesión que esos servicios reciben.
- **C-25**: servicio `frontend` en el compose.
- **Redis**: no se agrega cliente ni uso funcional (DD-10, SU-11). Solo se espera a su healthcheck.
- **Dominio**: no se modifica. El mapeo a HTTP vive en `app/api`, porque el dominio no conoce HTTP.

---

## 2. Estado actual

### 2.1. Backend

| Elemento | Ubicación | Qué importa para C-18 |
|----------|-----------|-----------------------|
| `ViolationCode` | `app/domain/violations.py:16-38` | 20 códigos. El valor es igual al nombre. |
| `Violation` | `app/domain/violations.py:53-78` | `code`, `message`, `conflicting_appointment_id`, `reference_kind`, `conflicting_block_id`, `conflicting_interval`. |
| `Rejected` | `app/domain/violations.py:95-109` | Tupla no vacía. Lo reutiliza `CatalogResult` (`app/domain/catalog/result.py:7,27`), así que hay un único tipo de rechazo. |
| `Interval` | `app/domain/intervals.py:20-21` | Campos `start` y `end`. |
| `get_session(settings)` | `app/db/session.py:60-63` | **Crea un engine y un pool nuevos en cada llamada**. Nadie la usa hoy (ni `app` ni `tests`). No sirve para un `Depends` por request. |
| `create_session_factory` | `app/db/session.py:41-46` | `expire_on_commit=False`. La usa `seed.py`. |
| `create_database_engine` | `app/db/session.py:24-38` | `pool_pre_ping=True`, UTC por conexión, sin timeout de conexión. |
| `load_settings` | `app/config.py:34-43` | `os.environ` pisa a `.env`. Las 14 variables son obligatorias. Falla al importar si se la llama a nivel de módulo sin entorno. |
| Repositorios | `app/repositories/` | Ninguno hace `commit`: solo `flush` y `begin_nested`. |
| Servicios de C-17 | no existen todavía | Definidos en su `design.md` D5, con 0/17 tareas hechas. |

### 2.2. Lo que C-18 tiene que cambiar de lo que ya está fijado

| Dónde | Qué fija hoy | Por qué choca |
|-------|--------------|---------------|
| `tests/test_compose.py:10,22` | `"backend:" not in content` | El servicio `backend` es el alcance de C-18. |
| `tests/test_compose.py:26` | `"postgresql+psycopg://" not in content` | Choca con la opción recomendada en D13. |
| Spec `database-infrastructure`, "Compose reproducible" | "SHALL definir solo `postgres:16` y `redis:7`" y "ni URLs con credenciales" | Necesita un delta `MODIFIED`. |

### 2.3. Contradicciones en la documentación

| Tema | Una fuente dice | Otra fuente dice |
|------|-----------------|------------------|
| `INVALID_TRANSITION` | KB 07, Flujos 2 y 3: `422` | `CHANGES.md:546` (C-23): `409` |
| `FORBIDDEN_OPERATION` | El pedido de este explore y `CHANGES.md:470`: `409` o `422` | KB 07, Flujo 3, y `CHANGES.md:532,548`: `403` |
| Códigos | KB 07 lista 14 | El enum tiene 20: faltan `DUPLICATE_DNI`, `DUPLICATE_NAME`, `INVALID_DNI`, `EMPTY_NAME`, `FORBIDDEN_OPERATION`, `STATUS_CHANGE_TOO_EARLY` |

### 2.4. Dependencias y entorno

- En `backend/.venv` (Python 3.13.6) **no están** `fastapi`, `starlette`, `httpx` ni `uvicorn`.
- `pydantic` y `python-dotenv` ya están. `dotenv` lo importa `config.py` directamente, pero solo llega como dependencia transitiva de `pydantic-settings`.
- Toda la evidencia de tests existente se generó con Python 3.13.6; `pyproject.toml` pide `>=3.12`.
- **`.env.example` no se pudo leer**: la configuración de permisos deniega ese archivo. Sus 14 nombres, sin valores, se tomaron de KB 08 y de `tests/test_config.py:55-76`, que los verifica. **`.env` tampoco se leyó**, así que el host de su `DATABASE_URL` es una suposición (D13).

---

## 3. Decisiones abiertas (`D1`–`D15`)

### D1 — Tabla completa `ViolationCode` → status HTTP

- **Problema**: la KB clasifica solo algunos códigos. Hace falta una tabla total, sin casos por defecto.
- **Recomendación**: un `Mapping[ViolationCode, int]` en `app/api/errors.py`, con un test que exige `set(tabla) == set(ViolationCode)`. Un código nuevo sin clasificar rompe el test.

| # | `ViolationCode` | Status | Motivo | Fuente |
|---|-----------------|--------|--------|--------|
| 1 | `PROFESSIONAL_OVERLAP` | **409** | Choca con otro turno del profesional | KB 07, Flujo 1 |
| 2 | `CHAIR_OVERLAP` | **409** | Choca con otro turno del sillón | KB 07, Flujo 1 |
| 3 | `OUTSIDE_WORKING_HOURS` | **409** | Conflicto con la agenda del profesional | KB 07 paso 7; design de C-05 |
| 4 | `BLOCKED_TIME` | **409** | Conflicto con un bloqueo existente | Design de C-06 |
| 5 | `DUPLICATE_DNI` | **409** | Choca con un paciente existente | `CHANGES.md:505` (C-20) |
| 6 | `DUPLICATE_NAME` | **409** | Choca con un registro existente | `CHANGES.md:505` (C-20) |
| 7 | `UNKNOWN_REFERENCE` | **422** | El pedido apunta a algo inexistente | KB 07, casos de error |
| 8 | `INACTIVE_REFERENCE` | **422** | Grupo 1, validez del pedido | Design de C-03 |
| 9 | `INVALID_DURATION` | **422** | Grupo 1, validez del pedido | Design de C-03 |
| 10 | `INVALID_START_TIME` | **422** | Grupo 1, no depende de la agenda | Design de C-04 |
| 11 | `CROSSES_MIDNIGHT` | **422** | Grupo 1, no depende de la agenda | Design de C-04 |
| 12 | `IN_THE_PAST` | **422** | Validez del pedido | KB 07; design de C-07 |
| 13 | `INVALID_WORKING_HOURS` | **422** | El tramo cargado es inválido en sí mismo | Inferido de RN-DI-02; coherente con la fila 14 |
| 14 | `OVERLAPPING_WORKING_HOURS` | **422** | Los tramos enviados son inconsistentes entre sí, no chocan con datos guardados | `CHANGES.md:518` (C-21) |
| 15 | `INVALID_BLOCK` | **422** | `inicio >= fin` | Design de C-06 |
| 16 | `INVALID_DNI` | **422** | Formato inválido | Inferido: ninguna fuente lo clasifica |
| 17 | `EMPTY_NAME` | **422** | Dato inválido | Inferido: ninguna fuente lo clasifica |
| 18 | `STATUS_CHANGE_TOO_EARLY` | **422** | Precondición de tiempo | KB 07, Flujo 3 |
| 19 | `INVALID_TRANSITION` | **422** ⚠️ | Ver D3: las fuentes se contradicen | KB 07 contra `CHANGES.md:546` |
| 20 | `FORBIDDEN_OPERATION` | **403** ⚠️ | Ver D2: no es 409 ni 422 | KB 07, Flujo 3; `CHANGES.md:548` |

Total: 6 en `409`, 13 en `422`, 1 en `403`.

---

### D2 — `FORBIDDEN_OPERATION`: el único código que no entra en "409 o 422"

- **Problema**: el pedido de este explore y `CHANGES.md:470` hablan de `409` o `422`, pero el dominio emite `FORBIDDEN_OPERATION` por reglas de propiedad (`transitions.py:49,85`, `reschedule.py:156`), y KB 07 y `CHANGES.md:548` piden `403 por rol y por propiedad`.
- **Opciones**:
  - **Opción A — `403` con el cuerpo `{ "violations": [...] }`**. *Pros*: cumple KB 07 y C-23; conserva el mensaje en español. El dominio garantiza que este código viene solo (spec `appointment-lifecycle`, líneas 166 y 341), así que nunca se mezcla. *Contras*: amplía la frase de `CHANGES.md:470`.
  - **Opción B — `422`**. *Pros*: respeta literalmente "409 o 422". *Contras*: contradice KB 07 y C-23, y la UI no podría tratar igual el `403` de rol (C-19) y el de propiedad.
- **Recomendación**: **Opción A**. Es el mismo error para quien llama, venga del RBAC o de la regla de propiedad.

---

### D3 — `INVALID_TRANSITION`: `422` (KB 07) o `409` (`CHANGES.md:546`)

- **Problema**: las dos fuentes se contradicen. Además, el dominio puede devolver `INVALID_TRANSITION` y `STATUS_CHANGE_TOO_EARLY` **en el mismo resultado** (spec `appointment-lifecycle`, línea 176).
- **Opciones**:
  - **Opción A — `422` y corregir `CHANGES.md:546`**. *Pros*: una transición que falla junto con "demasiado temprano" no mezcla status; coincide con KB 07. *Contras*: en la carrera de C-17 D11 (dos personas cambian el mismo turno) el `422` suena menos a conflicto que un `409`.
  - **Opción B — `409` y corregir KB 07**. *Pros*: describe mejor esa carrera. *Contras*: crea un caso mixto `409`+`422` dentro del ciclo de vida, que dependería de la precedencia de D4.
- **Recomendación**: **Opción A**. El `message` ya explica el estado actual del turno, así que la UI no pierde información.

---

### D4 — Un mismo `Rejected` con códigos de distinto status

- **Problema**: en la agenda, el grupo 1 corta antes del grupo 2 y nunca se mezclan (`validate.py:205,224`). **En catálogos sí se mezclan**: un paciente puede dar `EMPTY_NAME` + `DUPLICATE_DNI` (`catalog/create.py:43-47`) y una prestación `DUPLICATE_NAME` + `INVALID_DURATION` (`catalog/create.py:33-37`).
- **Opciones**:
  - **Opción A — Precedencia `403 > 422 > 409`, con la lista completa en el cuerpo**. *Pros*: un pedido inválido se corrige primero, igual que el orden de RN-AG-12; no se pierde ninguna violación. *Contras*: el status no refleja el duplicado, aunque el cuerpo sí.
  - **Opción B — Precedencia `409 > 422`**. *Pros*: destaca el conflicto. *Contras*: contradice el criterio de grupos ya usado en la agenda.
  - **Opción C — Separar en el dominio para que no se mezclen**. *Contras*: cambia specs archivadas de C-09 y pierde "mostrar todo lo que está mal de una vez".
- **Recomendación**: **Opción A**, como función pura `status_for(violations)` testeada con los dos casos mixtos reales.

---

### D5 — Forma exacta de `{ "violations": [...] }` y cómo llega desde una ruta

- **Problema**: KB 07 da un ejemplo con tres campos, pero `Violation` tiene seis, y hay que decidir qué pasa con los vacíos.
- **Forma recomendada**: una lista no vacía, en el mismo orden que devuelve el dominio. `code` y `message` siempre; el resto **se omite** cuando es `None`, como en el ejemplo de KB 07.

| Campo JSON | Tipo | Campo del dominio | Presente en |
|------------|------|-------------------|-------------|
| `code` | `ViolationCode` (enum en OpenAPI) | `code` | Siempre |
| `message` | string en español | `message` | Siempre |
| `conflictingAppointmentId` | UUID | `conflicting_appointment_id` | Solapamientos |
| `conflictingBlockId` | UUID | `conflicting_block_id` | `BLOCKED_TIME` |
| `conflictingInterval` | `{ startAt, endAt }` ISO-8601 UTC | `conflicting_interval` (`start`, `end`) | Solapamientos y `BLOCKED_TIME` |
| `referenceKind` | `PATIENT`, `PROFESSIONAL`, `CHAIR`, `SERVICE` | `reference_kind` | Referencias |

Solapamiento (`409`, mensaje de KB 07 con ids de ejemplo):

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

Referencia inexistente (`422`):

```json
{
  "violations": [
    {
      "code": "UNKNOWN_REFERENCE",
      "message": "El profesional indicado no existe.",
      "referenceKind": "PROFESSIONAL"
    }
  ]
}
```

- **Cómo llega desde una ruta**:
  - **Opción A — Excepción de borde `DomainRejectedError(rejected)` con un handler global**. *Pros*: un solo lugar arma la respuesta; la excepción atraviesa la dependencia de sesión (D10). No rompe la regla dura: el dominio sigue devolviendo resultados tipados y solo el borde HTTP la lanza. *Contras*: control de flujo con excepción dentro de `app/api`.
  - **Opción B — Helper que devuelve `JSONResponse`**. *Pros*: sin excepciones. *Contras*: cada ruta repite la bifurcación y su tipo de retorno se vuelve una unión.
- **Recomendación**: **campos omitidos cuando son `None`** y **Opción A**.

---

### D6 — Reemplazo del `422` de FastAPI por `400`

- **Problema**: FastAPI responde `422` a errores de esquema, y ese status acá significa regla de negocio. También hay que definir el cuerpo: `exc.errors()` incluye `input`, que **devolvería tal cual lo enviado, contraseñas de login incluidas**, y sus mensajes están en inglés.
- **Opciones**:
  - **Opción A — Handler de `RequestValidationError` → `400` con un cuerpo propio `errors`**:
    ```json
    {
      "errors": [
        { "field": "startAt", "type": "missing", "message": "Falta este dato." },
        { "field": null, "type": "json_invalid", "message": "El cuerpo no es JSON válido." }
      ]
    }
    ```
    *Pros*: `violations` sigue siendo exclusivo de las reglas de negocio; no se devuelven `input`, `ctx` ni `url`. *Contras*: la UI maneja dos formas; la mitiga que un `400` es un error de programación o algo que el formulario ya evita.
  - **Opción B — Mismo sobre `violations` con `code: "MALFORMED_REQUEST"`**. *Pros*: la UI parsea una sola forma. *Contras*: ese código no es un `ViolationCode`, así que el enum de OpenAPI dejaría de ser el del dominio, o habría que agregar al dominio un concepto HTTP.
  - **Opción C — Reenviar `exc.errors()` tal cual**. *Contras*: fuga de datos y mensajes en inglés.
- **Alcance**: cubre cuerpo, JSON roto, path y query, porque todos llegan como `RequestValidationError`. `field` se arma con `loc` sin el primer elemento. Los mensajes salen de una tabla corta por `type` (`missing`, `json_invalid`, `uuid_parsing`, `datetime_from_date_parsing`…) con un texto genérico en español como respaldo.
- **Recomendación**: **Opción A**, con un test que envía un valor marcado en el cuerpo y verifica que no aparece en la respuesta.

---

### D7 — Qué chequea `/api/health`

- **Problema**: `CHANGES.md` pide "incluye chequeo de la BD". Hay que definir hasta dónde llega.
- **Opciones**:
  - **Opción A — `SELECT 1` por una sesión del factory de la app**. `200 { "status": "ok", "database": "ok" }`; ante `SQLAlchemyError`, `503 { "status": "unavailable", "database": "unavailable" }`, sin texto del error, que podría exponer host o usuario. *Pros*: comprueba lo que el servicio necesita; es rápido y sin datos. *Contras*: no detecta migraciones pendientes.
  - **Opción B — Además, comparar la revisión de Alembic con `head`**. *Pros*: detecta esquema viejo. *Contras*: el contenedor ya corre `upgrade head` antes de levantar; suma código sin un caso real.
  - **Opción C — Además, hacer ping a Redis**. *Contras*: sumaría un cliente para un servicio sin uso (SU-11) y bajaría la API por algo que no necesita.
- **Detalles**: ruta pública (KB 03), sin datos de negocio, definida con `def` para que corra en el threadpool. Se agrega `connect_args={"connect_timeout": 3}` en `create_database_engine` para que una base colgada no bloquee la respuesta ni los hilos.
- **Recomendación**: **Opción A**, con el timeout de 3 segundos.

---

### D8 — CORS

- **Problema**: KB 08 pide solo el origen del frontend.
- **Opciones**:
  - **Opción A — Una sola entrada `allow_origins=[settings.cors_origin]`, `allow_credentials=False`, métodos `GET, POST, PUT, PATCH, DELETE`, headers `Authorization, Content-Type`**. *Pros*: el JWT viaja en un header, no en cookies, así que no hacen falta credenciales; lista cerrada y coherente con KB 02. *Contras*: un header nuevo exige tocar la lista.
  - **Opción B — `allow_methods=["*"]`, `allow_headers=["*"]`**. *Pros*: menos mantenimiento. *Contras*: más permisivo de lo que KB 08 pide.
  - **Opción C — Admitir varios orígenes separados por coma**. *Contras*: `CORS_ORIGIN` es singular en KB 08 y no hay un segundo origen.
- **Recomendación**: **Opción A**. Swagger no necesita CORS porque se sirve desde el mismo origen que la API.

---

### D9 — Swagger con las respuestas de error documentadas

- **Problema**: FastAPI agrega por su cuenta un `422 HTTPValidationError` en toda ruta con parámetros o cuerpo. Esa respuesta nunca va a ocurrir con D6, y Swagger mentiría justo en el video. Según mi lectura del generador, declarar `422` en la ruta evita el automático (**a comprobar en el RED**), pero un `GET /appointments` con query params no tiene `422` de negocio que declarar.
- **Opciones**:
  - **Opción A — Personalizar el esquema OpenAPI en `app/api/openapi.py`**: a toda operación con parámetros o cuerpo le quita el `422` automático y le agrega `400` con `MalformedRequestResponse`; quita del esquema `HTTPValidationError` y `ValidationError`. Las respuestas de negocio se declaran por ruta con `responses=violation_responses(409, 422)`. *Pros*: un endpoint nuevo queda bien sin acordarse de nada; cada ruta documenta solo lo que puede devolver. *Contras*: unas 30 líneas de transformación, tipadas sin `Any`.
  - **Opción B — Declarar todo a mano en cada ruta, más un test guardián**. *Pros*: sin transformación. *Contras*: no resuelve los `GET` sin `422` de negocio.
  - **Opción C — `responses` a nivel de router con `400`, `409` y `422`**. *Contras*: documenta errores que muchas rutas no pueden dar.
- **Detalles**:
  - URLs: `docs_url="/api/docs"` y `openapi_url="/api/openapi.json"`, para que todo quede bajo `/api`; `redoc_url=None`.
  - `ViolationResponse` usa el enum `ViolationCode`, así que Swagger lista los 20 códigos. Cada status lleva un ejemplo ficticio en español y una descripción.
  - `/api/health` documenta `200` y `503`.
- **Límite para el video**: en C-18 Swagger muestra **solo `/api/health`**, porque las rutas de prueba existen solo en los tests. Los `400`, `409` y `422` recién se ven con el primer endpoint con cuerpo (C-19 o C-20). Swagger UI carga sus archivos desde un CDN: al grabar hace falta internet.
- **Recomendación**: **Opción A**, con un test que recorre el `app.openapi()` real y una app con ruta de prueba, y exige que no exista `HTTPValidationError`.

---

### D10 — Quién hace commit o rollback en la sesión por request

- **Problema**: C-17 D5 fija que los **servicios** abren su transacción, hacen `commit` y, ante `Rejected`, `rollback`. Falta definir qué hace la dependencia, y quién confirma las escrituras de catálogos y horarios, cuyos repositorios nunca hacen `commit`.
- **Opciones**:
  - **Opción A — La dependencia nunca confirma: entrega la sesión, revierte ante excepción y la cierra**:
    ```python
    def get_db_session(request: Request) -> Iterator[Session]:
        with request.app.state.session_factory() as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise
    ```
    **Regla**: confirma quien es dueño de la escritura, el servicio o caso de uso, nunca la ruta ni la dependencia. *Pros*: encaja con C-17 D5 sin tocarlo (`auto_commit=True`); un `commit` olvidado pierde la escritura y lo detecta un test de integración. *Contras*: C-20 y C-21 necesitan un caso de uso fino que haga `commit`.
  - **Opción B — Unidad de trabajo: la dependencia confirma al salir si no hubo excepción**. *Pros*: las rutas de catálogo quedan más cortas. *Contras*: **desde FastAPI 0.118 el código tras el `yield` corre después de enviar la respuesta**, así que el cliente podría recibir un `201` y que el `commit` falle después. Además, duplica el `commit` de C-17 y podría confirmar un `flush` parcial si un `Rejected` no pasa por excepción.
  - **Opción C — Igual que B, con `Depends(scope="function")`, y pasar `auto_commit=False` a los servicios**. *Pros*: resuelve el orden. *Contras*: reescribe el contrato de C-17, cuyo propose ya está revisado.
- **Aviso para C-17**: C-19 va a leer el usuario con esta misma sesión, y esa lectura abre una transacción implícita. `with session.begin():` lanzaría `InvalidRequestError` en ese caso. El `begin_nested()` de D5 no tiene ese problema: **conviene mantenerlo así al implementar**.
- **Recomendación**: **Opción A**.

---

### D11 — Creación de la app, engine único y ciclo de vida

- **Problema**: `get_session(settings)` crea un engine por llamada (§2.1), y una `app = FastAPI()` a nivel de módulo llamaría a `load_settings()` al importar.
- **Opciones**:
  - **Opción A — Factory `create_app(settings: Settings | None = None)`, con el session factory en `app.state`, `lifespan` que hace `engine.dispose()` al cerrar, y `uvicorn --factory app.main:create_app`**. Se **elimina** `get_session`, hoy sin uso. *Pros*: un solo pool; los tests pasan `Settings` literales sin `.env` ni variables de entorno. *Contras*: se aparta de la convención `fastapi run` de la skill `fastapi`, pensada para un `app` a nivel de módulo.
  - **Opción B — `app = create_app()` a nivel de módulo, con `fastapi run`**. *Pros*: sigue la skill. *Contras*: importar `app.main` exige un entorno completo y complica los tests sin `.env`.
- **Recomendación**: **Opción A**. Estructura: `app/main.py`, `app/api/{errors,schemas,deps,health,openapi}.py`. Rutas con `def`, porque SQLAlchemy y psycopg se usan de forma síncrona.

---

### D12 — `backend/Dockerfile`

- **Problema**: la imagen tiene que correr Alembic y uvicorn sin dependencias de desarrollo ni secretos.
- **Opciones**:
  - **Opción A — `python:3.13-slim`, una sola etapa, usuario no root, migración en el `CMD`**, con el contexto de build en `./backend`:
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
    *Pros*: 3.13 es la versión con la que corrió toda la evidencia; `.env` queda fuera del contexto porque está en la raíz; `exec` entrega las señales a uvicorn; si la migración falla, el contenedor termina con error y no sirve un esquema viejo. *Contras*: las migraciones corren en cada arranque, algo aceptable con un solo contenedor.
  - **Opción B — `python:3.12-slim`**. *Pros*: es el mínimo de `pyproject.toml` y de `mypy`. *Contras*: esa combinación nunca se ejecutó en este repo.
  - **Opción C — El comando en el `command:` del compose**. *Contras*: la imagen no se explica sola y obliga a escapar `$$`.
- **Además**: `backend/.dockerignore` con `.venv`, `tests`, `__pycache__`, `.mypy_cache` y `.pytest_cache`.
- **Recomendación**: **Opción A**.

---

### D13 — Servicio `backend` en `docker-compose.yml`

- **Problema**: dentro del contenedor la base es `postgres`, no `localhost`. Los tests de integración corren desde el host y usan el `DATABASE_URL` de `.env` (`tests/integration/conftest.py:32`), así que **ese valor no se puede cambiar**. La spec exige exactamente los nombres de KB 08, y hoy prohíbe "URLs con credenciales" en el compose.
- **Forma común**:
  ```yaml
  backend:
    build: ./backend
    env_file: .env
    environment:
      DATABASE_URL: <ver opciones>
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
  `environment` tiene prioridad sobre `env_file`, y `load_settings` prioriza `os.environ` sobre `.env`. Sin `curl` en la imagen slim, el healthcheck usa Python; `urlopen` falla con un `503`, así que el contenedor se marca como no sano. C-25 podrá depender de ese estado.
- **Opciones para `DATABASE_URL`**:
  - **Opción A — Interpolar: `postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}`**. *Pros*: sin variables nuevas y sin ningún valor literal: el secreto sigue solo en `.env`. *Contras*: una contraseña con caracteres reservados de URL rompe la conexión; exige un delta en la spec ("sin secretos literales") y cambiar `test_compose.py:26` por un test que rechace valores literales.
  - **Opción B — Variable nueva `DOCKER_DATABASE_URL` en `.env`**. *Pros*: mantiene la prohibición textual. *Contras*: repite la contraseña, y cambia KB 08, la spec, `.env.example`, `test_config.py` y el `.env` local de la autora.
  - **Opción C — Armar la URL en un entrypoint con `URL.create`**. *Pros*: maneja cualquier carácter. *Contras*: otro archivo y otra lógica solo para esto.
- **Recomendación**: **Opción A**, usando una contraseña sin caracteres reservados en `.env`. El seed no corre al arrancar: sigue siendo manual.

---

### D14 — Dependencias nuevas

- **Problema**: faltan FastAPI, el servidor y el cliente de `TestClient`.
- **Opciones**:
  - **Opción A — Explícitas**: en `dependencies`, `fastapi>=0.118,<1` y `uvicorn>=0.30,<1`, además de `python-dotenv>=1,<2`, que `config.py` importa directamente; en `dev`, `httpx>=0.27,<1`. *Pros*: mínimo y sin paquetes de sobra en la imagen. El piso `0.118` fija el comportamiento de `yield` descrito en D10, y es compatible con el `0.110+` de KB 02. *Contras*: los rangos se confirman al instalar en el apply.
  - **Opción B — `fastapi[standard]`**. *Pros*: un solo paquete, y trae `fastapi run`. *Contras*: suma paquetes que no se usan y deja `httpx` también en producción.
- **Sin agregar**: cliente de Redis (SU-11), `gunicorn`, `python-multipart`.
- **Recomendación**: **Opción A**.

---

### D15 — Probar el mapeo a `409` y `422` sin endpoints reales y sin mocks

- **Problema**: C-18 no tiene endpoints de negocio. Tampoco se quieren mocks, `monkeypatch` ni `dependency_overrides`, ni rutas de prueba visibles en producción.
- **Opciones**:
  - **Opción A — App real con rutas agregadas por el test**: una fixture llama a `create_app(settings_literales)` y le monta un `APIRouter` definido en el test, cuya ruta lanza `DomainRejectedError(Rejected((Violation(ViolationCode.CHAIR_OVERLAP, "..."),)))` con **tipos reales del dominio**, a través del handler y el `TestClient` reales. El engine conecta de forma perezosa, así que estos tests no tocan la base. *Pros*: ejercita todo el camino; nada de prueba entra en `create_app`. *Contras*: ninguno relevante.
  - **Opción B — Ruta de prueba en la app, protegida por `APP_ENV`**. *Contras*: código de prueba en producción, y aparecería en Swagger.
  - **Opción C — Probar solo la función `status_for`**. *Contras*: no cubre el handler, el cuerpo ni la serialización.
- **Casos** (`tests/api/`, sin marca `integration`, salvo donde se indica):
  | Test | Verifica |
  |------|----------|
  | Tabla total | `set(tabla) == set(ViolationCode)` |
  | Mapeo parametrizado | Cada uno de los 20 códigos responde su status y su `code` |
  | Casos mixtos | `EMPTY_NAME`+`DUPLICATE_DNI` y `DUPLICATE_NAME`+`INVALID_DURATION` → `422` con la lista completa, en orden |
  | Forma del cuerpo | Campos exactos en camelCase, `None` omitidos, `Z` en el intervalo |
  | `400` | JSON roto, campo faltante, tipo incorrecto y query inválido; el valor enviado no aparece en la respuesta |
  | Sesión y excepción | La excepción atraviesa la dependencia y el handler responde igual |
  | Salud caída | `Settings` con un puerto cerrado de verdad → `503` sin texto del error, **sin mock** |
  | Salud ok (`integration`) | Base de test real → `200` |
  | Rollback (`integration`) | Una escritura sin `commit` seguida de una excepción no persiste |
  | CORS | Preflight del origen permitido con su header; otro origen sin él |
  | OpenAPI | Sin `HTTPValidationError`; `400` en rutas con entrada; `409` y `422` referencian `ViolationsResponse`; `/api/docs` responde `200` |
  | Compose y Dockerfile | Texto: `backend`, `service_healthy`, sin valores literales, `alembic upgrade head` |
- **Recomendación**: **Opción A**. La verificación manual del contenedor (`docker compose up --build`, `GET /api/health`) queda como evidencia en el verify.

---

## 4. Riesgos y preguntas para la autora

### Riesgos identificados

1. **Trabajo en paralelo en `backend/`**: el servicio `backend` corre `alembic upgrade head`, así que una migración de C-17 a medio hacer impediría levantar el contenedor. *Mitigación*: la verificación de Docker de C-18 se hace con el árbol estable, y el commit agrega solo los archivos de C-18.
2. **`500` sin headers de CORS**: el handler de errores no controlados corre fuera de `CORSMiddleware`, así que el navegador lo vería como error de red (**a comprobar en el RED**). *Mitigación*: aceptarlo en el MVP y mostrar un mensaje genérico en la UI; un `500` nunca lleva traza.
3. **Tipos estrictos**: `mypy --strict` puede exigir ajustes en las firmas de los handlers y en la transformación de OpenAPI, y la regla prohíbe `Any`. *Mitigación*: usar `@app.exception_handler` y `object` con narrowing. **A comprobar en el RED.**
4. **Contraseña con caracteres reservados en `.env`**: rompe la URL interpolada de D13. *Mitigación*: anotarlo en `backend/README.md`.
5. **Swagger sin errores visibles hasta C-19 o C-20**: ver D9. *Mitigación*: grabar el video con endpoints ya implementados.

### Documentación por corregir si se aprueba (en el propose o apply de C-18)

- `CHANGES.md:470`: agregar `403` para `FORBIDDEN_OPERATION`.
- `CHANGES.md:546`: `INVALID_TRANSITION` → `422`.
- KB 07: completar los 20 códigos y los campos del contrato de error.
- Spec `database-infrastructure`: delta `MODIFIED` de "Compose reproducible".
- `tests/test_compose.py`: actualizar las aserciones de §2.2.

### Preguntas para la autora

Todas están formuladas como las decisiones **D1 a D15** para responderlas en un único mensaje (por ejemplo: *"Aprobadas D1–D15 con las opciones recomendadas"*, o indicando la opción de cada una). Las que más merecen tu atención:

- **D2**: `FORBIDDEN_OPERATION` → `403`, aunque el pedido decía "409 o 422".
- **D3**: `INVALID_TRANSITION` → `422`, corrigiendo `CHANGES.md:546`.
- **D4**: cuando se mezclan, gana `422`.
- **D6**: el `400` usa un cuerpo `errors` propio, no `violations`.
- **D13**: `DATABASE_URL` interpolada en el compose, con cambio de spec y de test.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md` del propose)

> Nota: esta lista es solo una propuesta dentro del explore; no se creó `openspec/changes/api-base-fastapi/` ni `tasks.md`.

### Grupo 1 — Dependencias y app base
- **1.1** Agregar las dependencias de D14 y verificar que la suite actual sigue en verde.
- **1.2** RED + GREEN: `create_app(settings)` con engine único y `lifespan`; eliminar `get_session` (D11).

### Grupo 2 — Errores de dominio
- **2.1** RED + GREEN: tabla total, `status_for` y casos mixtos (D1–D4).
- **2.2** RED + GREEN: `ViolationResponse`, `DomainRejectedError` y handler con rutas de prueba montadas por el test (D5, D15).

### Grupo 3 — Entrada malformada
- **3.1** RED + GREEN: handler `400` con cuerpo `errors`, mensajes en español y sin devolver lo enviado (D6).

### Grupo 4 — Sesión, salud y CORS
- **4.1** RED + GREEN: `get_db_session` con rollback y cierre, con prueba de integración (D10).
- **4.2** RED + GREEN: `/api/health` con `200` y `503`, y `connect_timeout` (D7).
- **4.3** RED + GREEN: CORS (D8).

### Grupo 5 — Swagger
- **5.1** RED + GREEN: transformación de OpenAPI, `violation_responses`, ejemplos y URLs bajo `/api` (D9).

### Grupo 6 — Contenedores
- **6.1** RED: actualizar `tests/test_compose.py` y su delta de spec.
- **6.2** GREEN: `backend/Dockerfile`, `backend/.dockerignore` y servicio `backend` (D12, D13).

### Grupo 7 — Verificación y documentación
- **7.1** Corregir `CHANGES.md` y KB 07.
- **7.2** Ejecutar `pytest`, `pytest -m integration`, `mypy --strict`, `docker compose up --build`, `GET /api/health` y `/api/docs`, `openspec validate api-base-fastapi --strict` y `git diff --check`, y registrar las evidencias en `docs/evidencias/`.
