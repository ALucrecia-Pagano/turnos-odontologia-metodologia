# Design

## Context

La motivación está en `proposal.md` y el análisis de alternativas completo en `docs/evidencias/explore-C-19.md`. La autora aceptó D1 a D18 con la opción recomendada, con un ajuste en D6, y respondió P1 a P4. Acá quedan como contrato.

**Governance CRÍTICO: este documento es el que la autora aprueba explícitamente. Sin esa aprobación no se escribe código.**

Restricciones que dan forma al diseño:

- `Actor` y `Role` ya existen en `app/domain/model.py`, y el dominio no autentica ni conoce usuarios.
- C-18 fija `DomainRejectedError`, `get_db_session` (nunca confirma), `create_app`, la transformación de OpenAPI y las rutas de prueba montadas por el test. **C-18 está en curso**: este diseño se apoya en su `design.md`, no en sus archivos a medio hacer.
- La guarda del dominio es una lista de módulos permitidos, así que `jwt` y `argon2` ya quedan prohibidos ahí.
- `app/services/appointments.py` usa `commit` y `rollback` sin `session.begin()`, así que leer el usuario en la misma sesión no lo rompe.
- Las reglas duras prohíben `Any`, mocks en tests de dominio y secretos en el repo.

## Goals / Non-Goals

**Goals:**

- Que ninguna ruta de C-20 a C-24 pueda nacer sin autenticación ni permiso sin que falle un test.
- Que un usuario inactivo no pueda operar ni firmar el historial con un token viejo.
- Que hash, contraseña y secretos no salgan por respuestas, logs ni errores.
- Que producción no tenga ningún parámetro que baje el costo del hash.

**Non-Goals:**

- Refresh tokens, revocación por token, cambio y recuperación de contraseña (SU-06, P1).
- ABM de usuarios y `/api/users` (D17).
- Límite de intentos de login (riesgo aceptado).
- FK en `changed_by` (D16).
- Login de la web y dónde guarda el token el navegador (C-26).
- Aplicar el alcance `propio` en horarios, bloqueos e historial: C-19 lo entrega a la ruta, y lo aplican C-21 y C-23.
- Cambios en `app/domain`, `docker-compose.yml` y `.env.example`.

## Decisions

### D1 — Tabla `app_user`

`user` es palabra reservada de PostgreSQL. Modelo `UserModel`, migración `20261106_06_usuarios`, encadenada a `20261105_05_historial_sin_truncate`.

| Columna | Tipo | Nulo | Notas |
|---------|------|------|-------|
| `id` | `Uuid` | No | PK generada por la aplicación |
| `username` | `String(150)` | No | Único |
| `display_name` | `String(255)` | No | KB 04 no lo aclara; `/me` lo muestra siempre |
| `password_hash` | `String(255)` | No | Cadena PHC de argon2 |
| `role` | `String(20)` | No | Igual que `appointment.status` |
| `professional_id` | `Uuid` | Sí | FK `ondelete="RESTRICT"` |
| `active` | `Boolean` | No | `server_default=sa.true()`, como los catálogos |

| Restricción | Definición |
|-------------|------------|
| `ck_app_user_role` | `role IN ('odontologo', 'recepcion', 'administrador')` |
| `ck_app_user_username_format` | `username ~ '^[a-z0-9._-]{3,150}$'` |
| `ck_app_user_professional_by_role` | D2 |
| `ux_app_user_username` | Índice único |
| `ux_app_user_professional_id` | Índice único |
| `fk_app_user_professional_id_professional` | FK |

El login aplica `strip().lower()` antes de buscar. *Alternativa descartada*: `user` entre comillas, y el par `name`/`name_normalized`, innecesario porque el nombre visible es `display_name`.

### D2 — El odontólogo tiene profesional y los demás roles no

```sql
CONSTRAINT ck_app_user_professional_by_role CHECK (
  (role = 'odontologo' AND professional_id IS NOT NULL)
  OR (role <> 'odontologo' AND professional_id IS NULL)
)
```

`role` es `NOT NULL`, así que el `CHECK` no puede pasar por dar `NULL`. El `ValueError` de `Actor` queda como segunda barrera: con el `CHECK` no puede ocurrir, y si ocurriera, un `500` es correcto. *Alternativa descartada*: validar en un caso de uso, que el seed y el SQL a mano saltean.

### D3 — Argon2id con `argon2-cffi`, y tests rápidos sin tocar producción

Parámetros fijos en `app/auth/passwords.py`, escritos de forma explícita para que una actualización de la librería no los cambie: `argon2id`, `time_cost=3`, `memory_cost=65536`, `parallelism=4`, `hash_len=32`, `salt_len=16` (perfil `RFC_9106_LOW_MEMORY`).

Los tests son rápidos porque argon2 guarda los parámetros **dentro de cada hash** y `verify` usa los de ese hash (se fija con un test). Los datos de prueba se insertan con un hash generado por `PasswordHasher.from_parameters(CHEAPEST)`, en un helper de `tests/`. **En producción no existe parámetro, variable ni función que baje el costo**: `hash_password` es el único camino de escritura. Solo usan costo real los tests de `passwords.py`, los del seed y el hash ficticio.

Sin rehash al iniciar sesión. *Alternativas descartadas*: `pwdlib[argon2]`, una capa innecesaria con un solo algoritmo; bcrypt, por su límite de 72 bytes; `passlib`, sin mantenimiento activo; variable `PASSWORD_HASH_COST`, porque una mala configuración bajaría la seguridad sin que se note.

### D4 — PyJWT, tres claims y configuración validada

`PyJWT>=2.10,<3`. Claims exactos: `sub`, `role`, `exp`, con `now` inyectado en `create_access_token(user, settings, now)`.

```python
payload: Mapping[str, object] = jwt.decode(
    token, secret, algorithms=[settings.jwt_algorithm], options={"require": ["exp", "sub", "role"]}
)
```

Se captura `jwt.InvalidTokenError` y se valida `sub` como UUID y `role` como `Role`. El `alg` nunca sale del token, y `leeway` queda en 0.

| Campo de `Settings` | Regla | Motivo |
|---------------------|-------|--------|
| `jwt_secret` | `SecretStr`, mínimo 32 caracteres | RFC 7518 §3.2; PyJWT solo avisa |
| `jwt_algorithm` | `Literal["HS256"]` | Bloquea `none` y algoritmos asimétricos |
| `jwt_expires_min` | `gt=0` | Un cero emitiría tokens vencidos |
| `seed_user_password` | `SecretStr \| None = None` | D11 |
| `model_config` | `hide_input_in_errors=True` | El error de Pydantic imprimiría el valor recibido |

*Alternativas descartadas*: `python-jose`; `joserfc` y `authlib`, pensadas para OAuth completo. No se agregan `iat`, `iss`, `aud`, `jti` ni `professional_id`.

### D5 — Se lee el usuario en cada request

```
Authorization: Bearer <token>
      |
      v
HTTPBearer(auto_error=False) -- falta o no es Bearer --> 401
      |
      v
jwt.decode -- vencido / firma / alg / claims ----------> 401  (sin tocar la base)
      |
      v
UserRepository.get_by_id(sub) -- no existe / inactivo -> 401
      |
      v
token.role == user.role ? -- no ------------------------> 401
      |
      v
AuthenticatedUser --> require_permission --> Actor --> dominio
```

Desactivar corta el acceso en el siguiente request. El rol usado sale del token (RN-AC-02) y además está confirmado contra la base. `professional_id` sale solo de la base. Cerrar sesión en la UI descarta el token, que sigue valiendo hasta `exp`: eso es lo que SU-06 deja afuera.

*Alternativas descartadas*: usar en silencio el rol de la base, que contradice RN-AC-02; confiar en el token hasta `exp`, porque un usuario desactivado operaría hasta 60 minutos y quedaría en el historial; columna `token_version`, que es revocación.

### D6 — Mismo `401` para usuario inexistente, contraseña incorrecta y usuario inactivo (ajuste de la autora)

```python
credentials = repository.get_credentials_by_username(normalized_username)
password_ok = verify_password(candidate_password_hash(credentials), password)
if credentials is None or not password_ok or not credentials.active:
    raise AuthenticationError(AuthErrorCode.INVALID_CREDENTIALS)
```

`candidate_password_hash` devuelve el hash guardado o, si no hay credenciales, `dummy_password_hash()`: un valor aleatorio hasheado con los costos de producción, una vez por proceso (`functools.cache`), y precalentado en `create_app` para que el primer login no sea un caso distinto. `active` se mira al final. Las rutas son `def`, así que argon2 corre en el threadpool y no bloquea el event loop.

**Por qué importa el tiempo.** Argon2 tarda órdenes de magnitud más que una búsqueda por usuario. Si el camino de "usuario inexistente" no hasheara nada, esa respuesta sería mucho más rápida, y un atacante podría enumerar qué usuarios existen midiendo tiempos, aunque el cuerpo sea idéntico. Por eso el diseño ejecuta los mismos pasos en todos los casos.

**Por qué no hay test de tiempo.** Decisión de la autora: un test que compara tiempos es inestable, sobre todo en Windows, y genera fallos al azar. Se prueba con:

- **Cuerpo idéntico byte por byte** entre los cuatro casos, con `Content-Type` y `WWW-Authenticate`.
- **Elección del hash, de forma determinista**: `candidate_password_hash(None)` es el hash ficticio, con el prefijo de producción.
- **Mutación**: quitar el hash ficticio hace fallar ese test.

**Límite conocido**: ningún test automatizado mide la duración, y tampoco prueba que el `verify` se ejecute en la rama de usuario inexistente; eso queda garantizado por tener una única línea de `verify`, sin bifurcación, y por revisión de código en el verify.

### D7 — Cuerpo propio de `401`

```json
{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }
```
```json
{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }
```

| Status | Cuerpo | Origen |
|--------|--------|--------|
| `400` | `{ "errors": [...] }` | Entrada malformada (C-18 D6) |
| `401` | `{ "code", "message" }` | Autenticación (este change) |
| `403` | `{ "violations": [{ "code": "FORBIDDEN_OPERATION", ... }] }` | RBAC (este change) y propiedad (dominio) |
| `409` / `422` | `{ "violations": [...] }` | Dominio (C-18) |

Todo fallo de token da exactamente el mismo cuerpo. Todo `401` lleva `WWW-Authenticate: Bearer`. `AuthenticationError(code)` es una excepción de borde con su handler, como `DomainRejectedError`. `HTTPBearer(auto_error=False)`, porque si no FastAPI responde con su propio `{ "detail": ... }`. El `403` de RBAC se lanza como `DomainRejectedError` con `FORBIDDEN_OPERATION`.

*Alternativas descartadas*: reutilizar `errors`, que significa entrada malformada; códigos nuevos en `ViolationCode`, que meten autenticación en el dominio; `violations` con códigos fuera del enum, que haría mentir a OpenAPI; `{ "detail" }`, sin código estable.

### D8 — Contrato de login y `/me`

| Ruta | Status | Cuerpo |
|------|--------|--------|
| `POST /api/auth/login` | `200` | `{ "accessToken", "tokenType": "bearer" }`, con `Cache-Control: no-store` |
| | `400` | Contrato de C-18 D6, sin devolver lo enviado |
| | `401` | `INVALID_CREDENTIALS` |
| `GET /api/auth/me` | `200` | `{ "id", "username", "displayName", "role", "professionalId" }` |
| | `401` | `INVALID_TOKEN` |

Entrada: `username` de 1 a 150 caracteres, `password` como `SecretStr` de 1 a 128, `extra="forbid"`. `/me` no devuelve permisos. *Alternativa descartada*: formulario OAuth2, que exige `python-multipart` y `access_token` en snake_case.

**A fijar con un test**: FastAPI parsea el JSON antes de resolver dependencias, así que JSON roto en una ruta protegida sin token puede dar `400`. No expone datos; se acepta.

### D9 — Matriz RBAC

Tabla de datos en `app/auth/permissions.py`, sin FastAPI:

```python
PERMISSIONS: Mapping[tuple[Resource, Action], Mapping[Role, Scope]]  # Scope.ALL | Scope.OWN
```

`require_permission(resource, action)` devuelve `Permission(actor, scope)`, o lanza `403`. Un rol sin entrada recibe `403`. *Alternativas descartadas*: `require_role` por ruta, que reparte la matriz y no se puede comparar con KB 03; solo en el dominio, que no conoce catálogos ni usuarios.

#### Matriz RBAC

Es la tabla normativa de la spec `authentication-and-rbac`. Deriva de KB 03, con P2 en su opción A. `todos` = sobre cualquier registro · `propio` = solo los suyos · `—` = `403`. Son **34 filas y 102 celdas: 61 permitidas y 41 denegadas**.

| # | Recurso | Acción | Odontólogo | Recepción | Administrador | Mensaje: `No tiene permiso para ...` |
|---|---------|--------|------------|-----------|---------------|--------------------------------------|
| 1 | `APPOINTMENT` | `CREATE` | — | todos | todos | dar turnos |
| 2 | `APPOINTMENT` | `READ_AGENDA` | todos | todos | todos | leer la agenda |
| 3 | `APPOINTMENT` | `RESCHEDULE` | — | todos | todos | reprogramar turnos |
| 4 | `APPOINTMENT` | `CANCEL` | — | todos | todos | cancelar turnos |
| 5 | `APPOINTMENT` | `CHANGE_STATUS` | propio | todos | todos | cambiar el estado de turnos |
| 6 | `APPOINTMENT_HISTORY` | `READ` | propio | todos | todos | leer el historial de turnos |
| 7 | `WORKING_HOURS` | `CREATE` | propio | — | todos | crear horarios |
| 8 | `WORKING_HOURS` | `READ` | propio | todos | todos | leer horarios |
| 9 | `WORKING_HOURS` | `UPDATE` | propio | — | todos | actualizar horarios |
| 10 | `WORKING_HOURS` | `DELETE` | — | — | todos | borrar horarios |
| 11 | `BLOCK` | `CREATE` | propio | — | todos | crear bloqueos |
| 12 | `BLOCK` | `READ` | propio | todos | todos | leer bloqueos |
| 13 | `BLOCK` | `UPDATE` | propio | — | todos | actualizar bloqueos |
| 14 | `BLOCK` | `DELETE` | propio | — | todos | borrar bloqueos |
| 15 | `PROFESSIONAL` | `CREATE` | — | — | todos | crear profesionales |
| 16 | `PROFESSIONAL` | `READ` | todos | todos | todos | leer profesionales |
| 17 | `PROFESSIONAL` | `UPDATE` | — | — | todos | actualizar profesionales |
| 18 | `PROFESSIONAL` | `DELETE` | — | — | todos | borrar profesionales |
| 19 | `CHAIR` | `CREATE` | — | — | todos | crear sillones |
| 20 | `CHAIR` | `READ` | todos | todos | todos | leer sillones |
| 21 | `CHAIR` | `UPDATE` | — | — | todos | actualizar sillones |
| 22 | `CHAIR` | `DELETE` | — | — | todos | borrar sillones |
| 23 | `SERVICE` | `CREATE` | — | — | todos | crear prestaciones |
| 24 | `SERVICE` | `READ` | todos | todos | todos | leer prestaciones |
| 25 | `SERVICE` | `UPDATE` | — | — | todos | actualizar prestaciones |
| 26 | `SERVICE` | `DELETE` | — | — | todos | borrar prestaciones |
| 27 | `PATIENT` | `CREATE` | — | todos | todos | crear pacientes |
| 28 | `PATIENT` | `READ` | todos | todos | todos | leer pacientes |
| 29 | `PATIENT` | `UPDATE` | — | todos | todos | actualizar pacientes |
| 30 | `PATIENT` | `DELETE` | — | — | — | borrar pacientes |
| 31 | `USER` | `CREATE` | — | — | todos | crear usuarios |
| 32 | `USER` | `READ` | — | — | todos | leer usuarios |
| 33 | `USER` | `UPDATE` | — | — | todos | actualizar usuarios |
| 34 | `USER` | `DELETE` | — | — | todos | borrar usuarios |

Quién aplica cada cosa:

- **Filas 3, 4 y 5**: están en la matriz y en el dominio. `propio` en la fila 5 significa "dejar pasar y que decida el dominio": **la API nunca compara el propietario de un turno**.
- **Filas 6, 7 a 9, 11 a 14**: `propio` lo aplica la ruta con `permission.scope`, en C-21 y C-23.
- **Filas 18, 22 y 26**: "borrar" es desactivar (C-20). **Fila 34**: desactivar, nunca borrar físicamente (D16). **Filas 31 a 34**: sin ruta en el MVP (D17).
- **P2 opción A**: la fila 2 es `todos`, como dicen `CHANGES.md:561` y la suposición de KB 03; las filas 8 y 12 son `propio`. `GET /api/agenda` igual incluye horarios y bloqueos ajenos (C-24), así que sus motivos quedan visibles por esa vía. Aceptado.
- **Nota para C-21 (fila 10)**: el odontólogo no borra horarios, pero un `PUT /working-hours` con lista vacía equivale a borrar. C-21 lo tiene que resolver.

#### Test guardián de la matriz

La matriz se prueba como tabla, no como 102 escenarios:

1. `backend/tests/auth/rbac_matrix.py` tiene una **copia literal e independiente** de las 34 filas. No importa `PERMISSIONS`, para que un cambio en el código no arrastre al test.
2. `test_permissions_match_literal_matrix` compara las 102 celdas contra `PERMISSIONS`.
3. `test_matrix_cell_over_http` recorre las 102 celdas contra rutas montadas por el test, con usuarios reales y tokens reales: `200` en las permitidas, `403` con el mensaje exacto en las denegadas.
4. `test_literal_matrix_has_expected_totals` exige 34 filas, 61 permitidas y 41 denegadas.
5. **Copia contra `design.md`**: `docs/evidencias/matriz-C-19.py` lee esta tabla, la compara con la copia literal, y genera `matriz-C-19.txt`. Corre en el verify, antes de archivar, porque después `design.md` cambia de carpeta.

#### Rechazo por defecto

`protected_router = APIRouter(dependencies=[Depends(get_current_user)])`, del que cuelgan los routers de C-20 a C-24. Dos guardianes, como funciones puras sobre una app, que se prueban también con apps de prueba mal armadas (si no, un guardián roto pasaría siempre):

- `routes_without_auth(app)`: recorre `app.openapi()`; toda operación fuera de la lista pública debe tener `security`.
- `routes_without_permission(app)`: recorre `route.dependant`; toda ruta protegida, salvo `/api/auth/me`, debe incluir un `require_permission`.

Viven en `tests/api/guards.py`. El guardián sigue funcionando en C-20 a C-24, sin tocarlo.

#### Paridad con el dominio

`tests/auth/test_rbac_domain_parity.py` ejecuta `reschedule_appointment`, `cancel_appointment` y `change_status` reales con cada rol, y verifica que `FORBIDDEN_OPERATION` coincide con la tabla. La regla dura no se rompe porque la matriz es RN-AC, y el test evita que ambos lados se separen.

### D10 — `Actor` desde el usuario autenticado

```python
@dataclass(frozen=True, slots=True)
class AuthenticatedUser:          # app/auth/model.py. Sin password_hash.
    id: UUID
    username: str
    display_name: str
    role: Role
    professional_id: UUID | None

    def to_actor(self) -> Actor: ...
```

`get_current_actor` y `Permission.actor` lo exponen a las rutas. `changed_by` es siempre `actor.user_id` (lo aplican C-22 y C-23). En el seed, `user_id` y `professional_id` son distintos a propósito. *Alternativas descartadas*: armar `Actor` desde claims, sin `professional_id`; pasar `UserModel`, que saca el ORM de los repositorios y arrastra el hash.

### D11 — Seed por rol

En `app/demo_data.py`, sin contraseña, con ids fijos:

| `id` | `username` | `display_name` | `role` | `professional_id` |
|------|------------|----------------|--------|-------------------|
| `...0000000000e1` | `administrador` | Administración Demo | `administrador` | `null` |
| `...0000000000e2` | `recepcion` | Recepción Demo | `recepcion` | `null` |
| `...0000000000e3` | `odontologo` | Dra. Laura Quiroga | `odontologo` | `...000000000001` |

Orden de `seed_database`, **antes de abrir la transacción**: (1) `APP_ENV=production` → error (P3); (2) contraseña faltante, vacía, de solo espacios o de menos de 8 caracteres → error que nombra la variable, sin mostrar el valor. `main()` termina con código distinto de 0. El resultado suma la clave `app_user`.

La segunda corrida inserta 0, no hashea, y no actualiza contraseñas: cambiar la variable no cambia a los usuarios existentes (se documenta en `backend/README.md`). Si el `username` choca con otra fila de distinto id, falla, sin intentar arreglarlo.

Se agrega como requisito nuevo, igual que hizo C-16 con los horarios: "Seed ficticio e idempotente" no cambia. *Alternativas descartadas*: variable obligatoria en `Settings`, porque la API dependería de un secreto de desarrollo; saltear los usuarios con un aviso, porque el fallo aparecería en el login; generar e imprimir una contraseña.

### D12 — Botón *Authorize* con `HTTPBearer`

```python
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="bearerAuth",
    bearerFormat="JWT",
    description="Pegue el accessToken de POST /api/auth/login, sin la palabra Bearer.",
)
```

`create_app` agrega `swagger_ui_parameters={"persistAuthorization": True}`. La transformación de OpenAPI de C-18 suma una regla: toda operación con `security` recibe `401` con `AuthErrorResponse`. El `403` se declara por ruta con `permission_responses()`, y el login documenta su `401` a mano porque es pública. El ejemplo del login usa un texto que claramente no sirve como contraseña.

Flujo del video: `POST /api/auth/login` (sin candado) → copiar `accessToken` → *Authorize* → pegar → `GET /api/auth/me` da `200` con el rol. *Alternativas descartadas*: `OAuth2PasswordBearer`, que exige el formulario de D8; dos logins, que duplican la superficie más sensible.

### D13 — Sin variables de entorno nuevas

`JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MIN` y `SEED_USER_PASSWORD` ya existen. Cambia su validación (D4, D11). `.env.example` y `docker-compose.yml` no cambian.

### D14 — Tokens vencidos y alterados sin mocks

Un token vencido es un token real, con firma válida, emitido con un `now` en el pasado por el código de producción, y rechazado con el reloj real. Sin `monkeypatch`, `freezegun` ni `dependency_overrides`. Los alterados se arman con PyJWT o a mano.

- **Firma alterada: se cambia el PRIMER carácter.** Los últimos bits de una firma base64url de 32 bytes no se usan, y dos caracteres finales distintos pueden decodificar a los mismos bytes: el test fallaría al azar.
- **Sin base**: los casos de token inválido se rechazan antes de consultar la base, así que no llevan la marca `integration`. Una app contra un puerto cerrado lo demuestra.
- **Contraprueba**: `test_valid_token_is_accepted`, armado igual pero con `now` actual, responde `200`. Sin esto, un test de "rechaza todo" pasaría con el código roto.

*Alternativa descartada*: `verify_exp=False` y comparar a mano, que reimplementa una validación de seguridad.

### D15 — Hash y contraseña fuera de respuestas y logs

| # | Lugar de fuga | Cómo se tapa |
|---|---------------|--------------|
| 1 | Cuerpo de `/login` y `/me` | `response_model` explícito |
| 2 | OpenAPI | Ídem |
| 3 | `400` que devuelve la entrada | C-18 D6 |
| 4 | `repr` de tipos internos | El hash vive solo en `UserCredentials`, con `field(repr=False)` |
| 5 | `repr` de `Settings` | `SecretStr` |
| 6 | Error de validación de `Settings` | `hide_input_in_errors=True` |
| 7 | Errores de SQLAlchemy | `hide_parameters=True` en `create_engine`; por defecto el mensaje incluye `[parameters: ...]` |
| 8 | Errores de PostgreSQL | Un `CHECK` fallido incluye `DETAIL: Failing row contains (...)`, con el hash. `UserRepository.create` lo atrapa y relanza `UserWriteError(constraint_name)` con `from None` |
| 9 | Logs de la aplicación | `app/auth` no escribe logs |
| 10 | Log de acceso de uvicorn | Método, ruta y status; la contraseña nunca va en la URL |
| 11 | Salida del seed | Solo conteos |
| 12 | Cachés intermedios | `Cache-Control: no-store` |

`get_credentials_by_username` es el único método que lee el hash, y solo lo usa el login. El log del servidor PostgreSQL también guarda ese `DETAIL`, dentro del contenedor local; se acepta en el MVP.

### D16 — `changed_by` sigue sin FK

Las pruebas de integración mencionan `changed_by` en 17 líneas de 3 archivos, sin filas de usuario, y la spec usa ese id en un escenario. El `changed_by` real siempre viene de un usuario autenticado, y los usuarios nunca se borran físicamente. KB 04 anota la relación como lógica. *Alternativa descartada*: FK `RESTRICT` ahora, que amplía C-19 hacia C-17.

### D17 — Sin ABM de usuarios

Ningún change de `CHANGES.md` entrega `/api/users`. Los usuarios del MVP salen del seed, y desactivar o cambiar el rol se hace por SQL; los tests de D5 usan un `UPDATE` real. Las filas 31 a 34 quedan en la matriz para el backlog. Se corrige SU-06. *Alternativa descartada*: agregarlo acá, que agranda un change crítico con validación de contraseñas y cambio de rol.

### D18 — Organización del código

```
app/auth/model.py        AuthenticatedUser, UserCredentials
app/auth/passwords.py    hash_password, verify_password, dummy_password_hash, candidate_password_hash
app/auth/tokens.py       create_access_token, decode_access_token
app/auth/permissions.py  Resource, Action, Scope, PERMISSIONS (sin FastAPI)
app/auth/login.py        authenticate (sin FastAPI)
app/repositories/users.py  UserRepository, UserWriteError
app/api/auth.py          rutas /auth/login y /auth/me
app/api/deps.py          get_current_user, get_current_actor, require_permission, protected_router
app/api/errors.py        AuthenticationError y su handler
app/db/models.py         UserModel
```

El repositorio devuelve tipos de `auth`, no de `domain`, porque el dominio no conoce usuarios. Las rutas leen `settings` de `app.state.settings`; si C-18 lo archiva con otro nombre, se usa el suyo.

### D19 — Tests de migración con revisiones explícitas (pedido de la autora)

El pedido nombra el `downgrade "-1"` del test de TRUNCATE. **Al revisarlo aparecieron otros tres puntos que también se rompen con cualquier migración nueva**, porque fijan `head` en la revisión 05:

| `tests/integration/test_database_infrastructure.py` | Hoy | Queda |
|-----------------------------------------------------|-----|-------|
| Línea 95, `test_migration_cycle_restores_test_database_to_head` | `head` == 05 | Compara contra `ScriptDirectory.get_current_head()` |
| Línea 197, `test_appointment_migration_downgrade_minus_one_cycle` | `head` == 05 | Ídem |
| Líneas 207 a 224, test de TRUNCATE | `upgrade head`, == 05, `downgrade -1` | `upgrade head`, `downgrade` a **05**, verificar triggers; `downgrade` a **`20261105_04_turnos_e_historial`**, verificar |
| Línea 246, test de TRUNCATE | `head` == 05 | Compara contra `get_current_head()` |

La línea 174 sigue con `-1`, porque antes baja a 03 y sube a 04 de forma explícita, y queda igual que el test de C-16.

`test_user_migration_explicit_downgrade_cycle` y `test_user_migration_explicit_upgrade`, los tests propios de la migración nueva, usan solo revisiones explícitas (`20261105_05_historial_sin_truncate` y `20261106_06_usuarios`). No comparan contra `head` ni usan `-1`.

**Los escenarios de la spec también estaban desactualizados**: "Ciclo upgrade y downgrade reversible" y "Ciclo upgrade y downgrade menos uno" decían `upgrade head` seguido de `downgrade -1`, algo falso desde C-17. Se corrigen con un `MODIFIED`.

El test de TRUNCATE conserva su nombre `..._minus_one_cycle`, igual que el de C-16, para no romper la trazabilidad de C-17.

**Otros tests que cambian por la FK nueva**: `tests/integration/conftest.py:112` y `tests/integration/test_catalog_persistence.py:116,216,241` borran profesionales, así que tienen que borrar usuarios antes. Línea 101 de `test_database_infrastructure.py`: se agrega `app_user` a las tablas ausentes tras `downgrade base`.

### D20 — Evidencias y mutaciones

Toda evidencia se genera **redirigiendo la salida a un archivo**, nunca pegándola a mano.

| Archivo en `docs/evidencias/` | Contenido |
|-------------------------------|-----------|
| `red-C-19/<tarea>.txt` | Salida del RED de cada tarea, redirigida antes de escribir el código |
| `pytest-C-19.txt` | `pytest` |
| `pytest-integration-C-19.txt` | `pytest -m integration` |
| `mypy-C-19.txt` | `mypy --strict app tests` |
| `alembic-C-19.txt` | `upgrade`, `current`, `downgrade`, sobre la base de test |
| `seed-C-19.txt` | Salida del seed, solo conteos |
| `matriz-C-19.py` y `.txt` | Copia literal contra la tabla de este `design.md` |
| `e2e-C-19.py` y `.txt` | Login de los tres roles y `/me` contra el contenedor; imprime status y rol, nunca el token |
| `mutaciones-C-19.py` y `.txt` | Mutaciones |
| `verify-C-19.md` | Trazabilidad y resumen |

**`mutaciones-C-19.py` tiene el formato de `mutaciones-C-17.py`**: `Mutation(test_file, test_name, file, original, mutated, repair_sql)`, comprueba que el original aparezca una sola vez, muta, recrea la base de test si tocó una migración, corre solo su test, restaura en un `finally`, vuelve a correrlo, genera el `.txt` y regenera la tabla de `verify-C-19.md`. Termina con código 0 solo si todas las mutaciones hicieron fallar su test. Tres diferencias necesarias:

1. **Marca de pytest**: corre con `-m "integration or not integration"`, porque C-19 tiene tests sin base.
2. **Sin `git diff`**: en vez de exigir el árbol limpio, compara un SHA-256 de `backend/app` y `backend/alembic` antes y después, porque el código de C-19 todavía no estará commiteado, y commitear requiere pedido de la autora.
3. **Revisión de recreación**: `20261105_05_historial_sin_truncate`.

Lista mínima de mutaciones:

| # | Test que tiene que fallar | Archivo | Mutación |
|---|---------------------------|---------|----------|
| 1 | `test_doctor_without_professional_is_rejected` | migración 06 | Relaja el `CHECK` para el odontólogo |
| 2 | `test_reception_with_professional_is_rejected` | migración 06 | Relaja el `CHECK` para los demás roles |
| 3 | `test_two_users_for_same_professional_are_rejected` | migración 06 | Índice no único |
| 4 | `test_user_migration_explicit_downgrade_cycle` | migración 06 | `downgrade` no borra la tabla |
| 5 | `test_hash_uses_fixed_parameters` | `passwords.py` | `time_cost=1` |
| 6 | `test_missing_user_uses_dummy_hash` | `passwords.py` | Devuelve otro hash barato |
| 7 | `test_inactive_user_with_correct_password_is_rejected` | `login.py` | Quita `not credentials.active` |
| 8 | `test_rejected_token[other_algorithm]` | `tokens.py` | `algorithms=["HS256", "HS512"]` |
| 9 | `test_rejected_token[missing_exp]` | `tokens.py` | Quita `exp` de `require` |
| 10 | `test_deactivated_user_with_valid_token_is_rejected` | `deps.py` | Quita el chequeo de `active` |
| 11 | `test_role_changed_user_with_valid_token_is_rejected` | `deps.py` | Quita la comparación de rol |
| 12 | `test_permissions_match_literal_matrix` | `permissions.py` | Le da a recepción la fila 15 |
| 13 | `test_matrix_cell_over_http[...]` | `deps.py` | `require_permission` nunca rechaza |
| 14 | `test_seed_rejects_short_password` | `seed.py` | Quita el chequeo de largo |
| 15 | `test_seed_refuses_production` | `seed.py` | Quita el chequeo de `APP_ENV` |
| 16 | `test_duplicate_username_error_hides_hash` | `session.py` | `hide_parameters=False` |
| 17 | `test_role_rule_error_hides_hash` | `users.py` | Relanza sin `from None` y con el mensaje original |
| 18 | `test_credentials_repr_hides_hash` | `model.py` | Quita `repr=False` |
| 19 | `test_short_secret_error_hides_value` | `config.py` | Quita `hide_input_in_errors` |
| 20 | `test_valid_token_is_accepted` | `tokens.py` | `decode` rechaza todo |
| 21 | `test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle` | migración 05 | `downgrade` no borra el trigger de TRUNCATE |

## Decisiones registradas de la autora

- **P1**: se sigue con la suposición de SU-06 (sin refresh tokens ni revocación). **Queda pendiente de confirmar con la cátedra**: se registra en KB 09 y KB 10.
- **P2**: opción A, ver la matriz.
- **P3**: el seed se niega a correr con `APP_ENV=production`, con su test.
- **P4**: un odontólogo con su profesional desactivado sigue entrando en el MVP. `active` del usuario y del profesional son independientes, y el dominio igual rechaza turnos nuevos con `INACTIVE_REFERENCE`. Se registra en KB 09.
- **D6**: sin test de tiempo.

## Diferencias con el explore

- **D6**: se quitó el test de tiempo, por decisión de la autora, y se agregó `candidate_password_hash` para probar la elección del hash de forma determinista.
- **D19** agrega tres aserciones de `head` que el explore no listó.
- **D11**: el seed de usuarios es un requisito `ADDED`, no un `MODIFIED` como decía el explore, siguiendo a C-16.
- **`database-infrastructure`** también modifica "Configuración completa y errores explícitos": decía que los secretos no tienen valor por defecto, y `SEED_USER_PASSWORD` pasa a ser opcional.

## Risks / Trade-offs

- **[Riesgo] Fuerza bruta en el login**, sin límite de intentos → Argon2 frena cada intento y el alcance es local. Se acepta y se documenta.
- **[Riesgo] Memoria por login**: cada intento usa 64 MiB; con 40 hilos de anyio (a comprobar), unos 2,5 GiB de pico → Se acepta en local.
- **[Riesgo] `JWT_SECRET` filtrado** → Mínimo de 32 caracteres, solo en `.env`, y D5 exige que el usuario exista con ese rol. Rotarlo invalida todas las sesiones.
- **[Riesgo] Token robado**, válido hasta `exp` → `exp` corto; desactivar al usuario lo corta.
- **[Riesgo] XSS y dónde se guarda el token** → Fuera de este change: C-26 tiene governance ALTO.
- **[Riesgo] Sin HTTPS** → Local. Un despliegue real lo necesita; se documenta.
- **[Riesgo] Alcance `OWN` no aplicado en C-21 y C-23**: el guardián ve el permiso, no su uso → Tests de `403` por registro ajeno en esos changes.
- **[Riesgo] `.env` local que no cumple D4** → La API no arranca, con un error que nombra la variable. La tarea 1.4 lo comprueba sin mostrar valores y **se detiene para que la autora lo corrija**.
- **[Riesgo] Conflicto con C-18 en archivos comunes** → El apply arranca con C-18 archivado (tarea 0.1).
- **[Riesgo] El hash ficticio no se mide**: ver el límite conocido de D6.
- **[Riesgo] Comportamientos a comprobar en el RED**: `verify` con los parámetros del hash, `hide_input_in_errors`, orden `400`/`401`, `route.dependant`, `security` heredado del router, y el `DETAIL` de PostgreSQL → Cada uno tiene un test que lo fija.
- **[Trade-off] Una lectura por PK en cada request** → Costo mínimo, a cambio de D5.
- **[Trade-off] Tres formas de error** → El `401` lo trata un solo lugar del cliente (C-26).
- **[Trade-off] Cerrar sesión no invalida el token** → Consecuencia de P1.

## Migration Plan

1. Verificar la precondición: C-18 archivado.
2. Instalar `PyJWT` y `argon2-cffi` (tarea 1.2).
3. La autora revisa su `.env`, si la tarea 1.4 lo pide.
4. Implementar por grupos, en el orden de `tasks.md`.
5. `alembic upgrade head`, y seed manual.

Rollback: revertir el commit del change y ejecutar `alembic downgrade 20261105_05_historial_sin_truncate`, que borra `app_user`. Las demás tablas no se tocan.

## Correcciones de `CHANGES.md` para la autora

No se editan en este change. Son correcciones para que las hagas a mano:

| Línea | Dice | Debería decir |
|-------|------|---------------|
| 485 | "Modelo y migración de `user` (`username` único, `display_name`, `password_hash`, `role` con `CHECK`, `professional_id` FK nulo, `active`)" | "Modelo y migración de `app_user` (`username` único, `display_name`, `password_hash`, `role` con `CHECK`, `professional_id` FK nulo y único, obligatorio solo para `odontologo`, `active`)" |
| 486 | "Hash de contraseñas con un algoritmo lento estándar (bcrypt o argon2, SU-06)" | "Hash de contraseñas con Argon2id (SU-06)" |
| 487 | "`GET /api/auth/me`. Sin refresh tokens ni revocación (SU-06)." | Agregar: "Desactivar el usuario o cambiarle el rol corta el acceso en el siguiente request." |
| 489 | "Seed de un usuario por rol con contraseña tomada de `SEED_USER_PASSWORD`" | Agregar: "; sin esa variable, y con `APP_ENV=production`, el seed no escribe nada." |

Y un hueco para anotar donde prefieras: **ningún change entrega el ABM de usuarios** (`/api/users`, D17).

Al archivar, además, marcar `[x]` en C-19.

## Puntos pendientes fuera de este change

- **SU-06 con la cátedra** (P1).
- `authentication-and-rbac` no lleva `## Purpose`, por el pedido de que no haya texto antes del primer requisito. Al archivar, la spec principal queda con un `TBD` en `Purpose` que hay que completar a mano, igual que en C-18.
- `mutaciones-C-17.py` no se volverá a correr tal cual: depende de cómo estaba el árbol entonces, y es evidencia histórica.
