# Explore C-19 — `autenticacion-jwt-y-roles`

Fecha: 2026-11-05
Fase: 5 — API REST FastAPI y JWT
Governance: **CRÍTICO** (solo análisis; no se escribe código sin aprobación explícita de la autora sobre este diseño)
Dependencias en `CHANGES.md`: `C-15` (completada) y `C-18` (**en curso**: 2/21 tareas según `openspec list`).

> Este explore no ejecutó docker, pytest ni pip, y no leyó `.env`. Tampoco creó nada en `openspec/` ni tocó código o configuración. No se tomaron como fuente de verdad los archivos de C-18 a medio hacer (`backend/app/api/`, `backend/app/main.py`, `backend/tests/api/`, y `backend/app/db/session.py`, que cambió mientras se escribía este documento): lo que C-19 necesita de C-18 sale de su `design.md`. Los datos de PyJWT, argon2-cffi y FastAPI salen de su documentación oficial (Context7). Lo que depende del comportamiento real de las librerías, que todavía no están instaladas, queda marcado **a comprobar en el RED**.

---

## 1. Alcance de C-19 según `CHANGES.md` y qué queda afuera

### Qué entra en C-19

1. **Modelo y migración de usuarios**, con `password_hash`, rol con `CHECK`, vínculo opcional con el profesional y `active`.
2. **Hash de contraseñas** con un algoritmo lento estándar.
3. **`POST /api/auth/login`** (token de acceso firmado con `sub`, `role`, `exp`) y **`GET /api/auth/me`**.
4. **`get_current_user`** (Bearer, firma y vencimiento → `401`) y **`require_permission(recurso, acción)`** con la matriz de KB 03 (→ `403`).
5. **Seed de un usuario por rol** con `SEED_USER_PASSWORD`.
6. **Tests**: login correcto; mismo `401` para contraseña incorrecta y usuario inexistente; token vencido, alterado o ausente; cada rol contra rutas de prueba de la matriz; hash y contraseña ausentes de las respuestas.

Se agrega porque C-18 lo dejó para este change: **el botón *Authorize* de Swagger**.

### Qué queda explícitamente afuera

- **Refresh tokens, revocación por token, recuperación y cambio de contraseña, autoservicio** (SU-06).
- **Límite de intentos de login**: no está en SU-06 ni en `CHANGES.md`. Queda como riesgo aceptado (§4).
- **C-20 a C-24**: endpoints de negocio. C-19 entrega las dependencias que ellos usan.
- **C-26**: pantalla de login y dónde guarda el token el navegador.
- **Dominio**: no se modifica. `Actor` y `Role` ya existen, y la spec dice que el dominio "MUST NOT autenticar JWT ni consultar usuarios".
- **Redis**: sin uso (SU-11).

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-19 reutiliza

| Elemento | Ubicación | Qué importa para C-19 |
|----------|-----------|-----------------------|
| `Role` | `app/domain/model.py:32-37` | Valores `odontologo`, `recepcion`, `administrador`: los mismos del `CHECK` de KB 04. |
| `Actor` | `app/domain/model.py:40-50` | `user_id`, `role`, `professional_id`. **Odontólogo sin `professional_id` lanza `ValueError`**. No impide lo inverso: un recepcionista con `professional_id` se construye igual. |
| Propiedad | Spec `appointment-lifecycle`, línea 27 | Se compara por `professional_id`, nunca por `user_id`. |
| `FORBIDDEN_OPERATION` | `app/domain/violations.py` | C-18 D2 decide que responde `403` con `{ "violations": [...] }`, para que el `403` de rol y el de propiedad se traten igual. |
| `DomainRejectedError` + `get_db_session` | `design.md` de C-18, D5 y D10 | C-19 los reutiliza. La dependencia de sesión **nunca confirma**. |
| Rutas de prueba montadas por el test | `design.md` de C-18, D15 | Es el patrón para probar la matriz. |
| Guarda del dominio | `tests/domain/import_guard.py:5-17` | Es una lista de **permitidos**: `jwt` y `argon2` ya quedan prohibidos en el dominio sin cambiar nada. |
| Transacciones de servicios | `app/services/appointments.py` | Usan `commit` y `rollback`, sin `session.begin()`. La lectura del usuario en la misma sesión no los rompe, tal como pedía el aviso de C-18 D10. |
| Variables | `app/config.py:20-23` | `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MIN`, `SEED_USER_PASSWORD` **ya existen** como obligatorias. |

### 2.2. Lo que C-19 rompe de lo que ya está fijado

| Dónde | Qué fija hoy | Por qué choca |
|-------|--------------|---------------|
| `tests/test_persistence_metadata.py:10-19` | Conjunto **exacto** de 8 tablas | Se agrega una tabla. |
| `tests/integration/conftest.py:109-112` | `DELETE FROM professional` sin usuarios | La FK de usuario a profesional lo bloquearía si hay filas. Hay que borrar usuarios antes. |
| `tests/integration/test_catalog_persistence.py:225-233` | Diccionario **exacto** de conteos del seed | Se agrega la clave de usuarios. Su limpieza final también borra profesionales. |
| `tests/integration/test_database_infrastructure.py:201-241` | `upgrade head` y después `downgrade -1` espera que desaparezca el trigger de TRUNCATE | **Con una migración nueva, `-1` deshace la tabla de usuarios y no el trigger.** Hay que fijar la revisión destino. |
| `tests/test_config.py:18` | `JWT_SECRET` literal de 20 caracteres | Choca con el mínimo de D4. |
| Spec `database-infrastructure`, "Seed ficticio e idempotente" (línea 291) | Lista cerrada de lo que carga el seed | Necesita un delta `MODIFIED`. |

### 2.3. Contradicciones y huecos en la documentación

| Tema | Una fuente dice | Otra fuente dice | Ver |
|------|-----------------|------------------|-----|
| Nombre de la tabla | `CHANGES.md:485`: `user` | `user` es palabra reservada de PostgreSQL | D1 |
| De dónde sale el rol | KB 03, RN-AC-02: "del token" | El token no alcanza para `Actor`: falta `professional_id` | D5, D10 |
| Revocación | SU-06: "sin revocación" | El pedido de este explore: qué pasa si se desactiva con token vigente | D5 |
| Agenda del odontólogo | KB 03, fila 2: "R (propios; **Suposición:** agenda completa)" | `CHANGES.md:561`: "su agenda (y el resto en solo lectura)" | D9 |
| Horarios y bloqueos ajenos | KB 03: odontólogo solo `propio` | `CHANGES.md:560`: `GET /api/agenda` incluye horarios y bloqueos del rango | D9 |
| ABM de usuarios | KB 03: administrador CRUD; SU-06: "los crea el administrador o el seed" | **Ningún change de `CHANGES.md` tiene `/api/users`** | D17 |
| `changed_by` | KB 04, ERD: `User 1───* AppointmentStatusChange` | `app/db/models.py:201`: sin FK | D16 |
| Alcance de SU-06 | KB 09: "confirmar con la cátedra al llegar a C-19" | Sin registro de esa confirmación | §4, P1 |

### 2.4. Dependencias y entorno

- En `backend/.venv` **no están** PyJWT, argon2-cffi, bcrypt, passlib ni pwdlib.
- C-18 D14 ya descartó `python-multipart`, algo que condiciona D12.
- **`.env` no se leyó**, así que no se sabe si el `JWT_SECRET` local cumple D4. `.env.example` tampoco: sus nombres salen de `tests/test_config.py:55-76` y KB 08.
- **Head de Alembic**: `20261105_05_historial_sin_truncate`. C-18 no agrega migraciones.

---

## 3. Decisiones abiertas (`D1`–`D18`)

### D1 — La tabla de usuarios

- **Problema**: `CHANGES.md` y KB 04 piden `user`. En PostgreSQL es una palabra reservada: hay que escribirla siempre entre comillas, y un `SELECT * FROM user` escrito a mano no falla, sino que devuelve el usuario de la conexión (**a comprobar en el RED**). Es una trampa justo al mostrar la base en el video.
- **Opciones de nombre**:
  - **Opción A — `app_user`, con modelo `UserModel`**. *Pros*: sin comillas ni sorpresas. *Contras*: se aparta de `CHANGES.md:485` y KB 04, que hay que corregir, y de la convención de una sola palabra.
  - **Opción B — `user`**. *Pros*: respeta el texto. *Contras*: SQLAlchemy la cita sola, pero toda consulta manual y todo trigger futuro necesitan comillas.
- **Columnas recomendadas** (con cualquiera de los dos nombres):

| Columna | Tipo | Nulo | Notas |
|---------|------|------|-------|
| `id` | `Uuid` | No | PK generada por la aplicación, como el resto. |
| `username` | `String(150)` | No | Único. Ver abajo. |
| `display_name` | `String(255)` | **No** | KB 04 no lo aclara; `/me` y la UI lo muestran siempre. |
| `password_hash` | `String(255)` | No | Cadena PHC de argon2. |
| `role` | `String(20)` | No | Igual que `appointment.status`. |
| `professional_id` | `Uuid` | Sí | FK `ondelete="RESTRICT"`, como `appointment`. Ver D2. |
| `active` | `Boolean` | No | `server_default=sa.true()`, como los catálogos. |

| Restricción | Definición |
|-------------|------------|
| `ck_app_user_role` | `role IN ('odontologo', 'recepcion', 'administrador')` |
| `ck_app_user_username_format` | `username ~ '^[a-z0-9._-]{3,150}$'` |
| `ck_app_user_professional_by_role` | Ver D2 |
| `ux_app_user_username` | Índice único sobre `username` |
| `ux_app_user_professional_id` | Índice único sobre `professional_id` (D2) |

- **Usuario sin distinguir mayúsculas**: el login aplica `strip().lower()` antes de buscar, y el `CHECK` garantiza que lo guardado ya está en ese formato. Es más simple que el par `name`/`name_normalized` de los catálogos, porque el nombre visible ya es `display_name`.
- **Recomendación**: **Opción A**, con las columnas y restricciones de arriba, en la migración `20261106_06_usuarios`.

---

### D2 — El odontólogo DEBE tener `professional_id` y los demás roles no

- **Problema**: `Actor` solo impide un lado de la regla. Si la base aceptara filas incoherentes, cada request de ese usuario terminaría en un `500`.
- **Opciones**:
  - **Opción A — `CHECK` de dos sentidos en la base**:
    ```sql
    CONSTRAINT ck_app_user_professional_by_role CHECK (
      (role = 'odontologo' AND professional_id IS NOT NULL)
      OR (role <> 'odontologo' AND professional_id IS NULL)
    )
    ```
    *Pros*: ninguna escritura la saltea (seed, SQL a mano, un futuro ABM); es explícita, como `reschedule_all_or_none`. Como `role` es `NOT NULL`, el `CHECK` no puede pasar por dar `NULL`. *Contras*: ninguno relevante.
  - **Opción B — Solo validar en un caso de uso**. *Contras*: el seed y el SQL a mano la saltean; no hay ABM donde ponerla (D17).
- **Además, índice único sobre `professional_id`**: el ERD de KB 04 dice `User 0..1─1 Professional`. Sin él, dos usuarios serían "el mismo" odontólogo y se confundiría la autoría. En PostgreSQL varios `NULL` no chocan.
- **El `ValueError` de `Actor` queda como segunda barrera**: con el `CHECK` no puede ocurrir, y si ocurriera, un `500` es correcto.
- **Test**: integración que intenta las dos filas incoherentes, un segundo usuario para el mismo profesional, y verifica el nombre de la restricción violada.
- **Recomendación**: **Opción A**, con el índice único.

---

### D3 — Algoritmo, librería, parámetros y tests rápidos

- **Problema**: SU-06 admite bcrypt o argon2. Los tests tienen que ser rápidos sin que exista una forma de bajar la seguridad en producción.
- **Opciones de algoritmo y librería**:
  - **Opción A — Argon2id con `argon2-cffi`, directo**. *Pros*: lo usa la documentación de FastAPI (por `pwdlib`); sin el límite de 72 bytes de bcrypt; tipado; el hash lleva sus parámetros. *Contras*: consume memoria en cada login (ver abajo).
  - **Opción B — Argon2id con `pwdlib[argon2]`**. *Pros*: es literalmente el tutorial de FastAPI. *Contras*: una capa más sobre `argon2-cffi`, que no se necesita con un solo algoritmo.
  - **Opción C — bcrypt**. *Pros*: maduro, sin consumo alto de memoria. *Contras*: límite de 72 bytes, que obliga a decidir qué hacer con contraseñas largas; menos resistente a hardware dedicado.
  - **Descartada — `passlib`**: sin mantenimiento activo.
- **Parámetros** (fijos en código, no por entorno):

| Parámetro | Valor | Origen |
|-----------|-------|--------|
| Variante | `argon2id` | RFC 9106 |
| `time_cost` | 3 | Perfil `RFC_9106_LOW_MEMORY` |
| `memory_cost` | 65536 KiB (64 MiB) | Ídem |
| `parallelism` | 4 | Ídem |
| `hash_len` / `salt_len` | 32 / 16 bytes | Ídem |

  Son los valores por defecto de la librería, pero se escriben de forma explícita para que una actualización no los cambie sin que nadie lo note. *Alternativa*: el mínimo de OWASP (`m=19 MiB, t=2, p=1`) reduce el consumo de memoria, a cambio de más velocidad para un atacante. Para un consultorio con pocos usuarios no hace falta.

- **Tests rápidos sin tocar producción**: argon2 guarda los parámetros **dentro de cada hash** (`$argon2id$v=19$m=65536,t=3,p=4$...`) y `verify` usa los de ese hash (**a comprobar en el RED**).
  - **Opción A — Hash barato solo en los datos de prueba**: el helper de tests genera el hash con `PasswordHasher.from_parameters(CHEAPEST)` (perfil "solo para testing" de la librería) y lo inserta en la fila. El código de producción no cambia, y `verify_password` lo verifica rápido. *Pros*: **en producción no existe ningún parámetro, variable ni función que baje el costo**. *Contras*: un hash barato insertado a mano en una base real se aceptaría; el único camino de escritura, `hash_password`, siempre usa los costos altos.
  - **Opción B — Variable `PASSWORD_HASH_COST`**. *Contras*: una mala configuración baja la seguridad sin que se note.
  - **Opción C — Inyectar el hasher con `dependency_overrides`**. *Contras*: los tests no ejercitan el camino real.
- **Tests que protegen esto**: uno exige que `hash_password` produzca el prefijo exacto `$argon2id$v=19$m=65536,t=3,p=4$`; otro exige que `CHEAPEST` no aparezca en `app/`; dos hashes de la misma contraseña difieren (sal aleatoria). Solo estos, el de tiempo (D6) y el seed usan costo real.
- **Sin rehash al iniciar sesión**: `check_needs_rehash` protege ante cambios de parámetros, que no se esperan en el MVP y exigirían escribir durante el login.
- **Dependencia**: `argon2-cffi>=23.1,<26` (rango a confirmar al instalar).
- **Recomendación**: **Opción A de algoritmo** con los parámetros de la tabla, y **Opción A de tests**.

---

### D4 — Librería de JWT, claims y validación del secreto

- **Opciones de librería**:
  - **Opción A — `PyJWT>=2.10,<3`**. *Pros*: la que usa la documentación de FastAPI; `algorithms` es una lista permitida que rechaza cualquier otro `alg`; `require` exige claims; sin dependencias para HS256. *Contras*: `decode` devuelve `dict[str, Any]`, que hay que tipar como `Mapping[str, object]` y validar, por la regla sin `Any`.
  - **Opción B — `python-jose`**. *Contras*: FastAPI dejó de usarla; arrastra dependencias sin necesidad.
  - **Opción C — `joserfc` / `authlib`**. *Contras*: pensadas para OAuth y OIDC completos, mucho más de lo necesario.
- **Claims: exactamente los de DD-11**:

| Claim | Valor | Validación al leer |
|-------|-------|--------------------|
| `sub` | UUID del usuario, como string | Obligatorio; UUID válido |
| `role` | Valor de `Role` | Obligatorio; valor válido; ver D5 |
| `exp` | `now + JWT_EXPIRES_MIN`, con `now` inyectado | Obligatorio; `leeway` 0 |

  **No se agregan** `iat` (nadie lo usa), `iss` y `aud` (un solo servicio), ni `jti` (sin revocación). **No se agrega** `professional_id`: sale de la base (D5). El JWT va firmado, no cifrado, así que no lleva nombres ni datos personales.

- **Lectura**:
  ```python
  jwt.decode(token, secret, algorithms=[settings.jwt_algorithm], options={"require": ["exp", "sub", "role"]})
  ```
  El `alg` nunca sale del token. Se captura `jwt.InvalidTokenError`, la base de vencido, firma inválida y claim faltante.

- **Validaciones nuevas en `Settings`** (hoy aceptan cualquier string, incluso vacío; `.env.example` trae los valores vacíos):

| Campo | Regla | Motivo |
|-------|-------|--------|
| `jwt_secret` | `SecretStr`, mínimo 32 caracteres | RFC 7518 §3.2 pide al menos 256 bits para HS256. PyJWT solo avisa con `InsecureKeyLengthWarning`. |
| `jwt_algorithm` | `Literal["HS256"]` | Bloquea `none` y algoritmos asimétricos por configuración. |
| `jwt_expires_min` | `gt=0` | Un cero emitiría tokens ya vencidos. |
| `model_config` | `hide_input_in_errors=True` | **Sin esto, el error de validación de Pydantic imprime el valor recibido, secreto incluido** (**a comprobar en el RED**). |

- **Impacto en tu `.env`**: si tu `JWT_SECRET` local tiene menos de 32 caracteres, la API deja de arrancar con un error que lo nombra, sin mostrar el valor. Se genera con `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Lo cambiás vos: yo no leo ni edito `.env`.
- **Recomendación**: **Opción A**, con esos tres claims y esas validaciones.

---

### D5 — Usuario desactivado o con otro rol y token vigente

- **Problema**: con `exp` de 60 minutos, un usuario desactivado seguiría operando y firmando el historial. Además, `Actor` necesita `professional_id`, que no está en el token.
- **Opciones**:
  - **Opción A — Leer el usuario en cada request, y exigir que coincida con el token**. Se busca por `sub`, por PK. `401` si no existe, si está inactivo, o si `role` del token difiere del de la base. `professional_id` sale siempre de la base. *Pros*: desactivar corta el acceso **en el siguiente request**; el rol usado sale del token (RN-AC-02) y además está confirmado; no hay tablas ni claims nuevos; `Actor` queda completo. *Contras*: una lectura por PK en cada request; un cambio de rol obliga a iniciar sesión de nuevo.
  - **Opción B — Igual, pero usando en silencio el rol de la base**. *Pros*: el usuario no pierde la sesión. *Contras*: contradice "el rol sale del token"; lo que ve la UI queda desactualizado respecto de la API.
  - **Opción C — Sin estado: confiar en el token hasta `exp`**. *Pros*: lo más literal de SU-06, sin lectura. *Contras*: **un usuario desactivado opera hasta 60 minutos y queda en el historial**; hay que agregar `professional_id` como claim, fuera de DD-11.
  - **Opción D — Columna `token_version`**. *Pros*: permitiría cerrar sesiones. *Contras*: es revocación, afuera por SU-06.
- **Resultado con la Opción A**:

| Situación con un token vigente | Respuesta |
|--------------------------------|-----------|
| Usuario desactivado | `401` |
| Usuario borrado | `401` |
| Rol cambiado | `401`; al volver a entrar recibe el rol nuevo |
| `professional_id` cambiado | Sigue operando, con el vínculo nuevo |
| Reactivado antes de `exp` | El token vuelve a servir |
| Cierre de sesión en la UI (C-26) | La UI descarta el token, pero **sigue valiendo hasta `exp`**: eso es lo que SU-06 deja afuera |

- **Flujo**:
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
- **KB**: SU-06 gana una aclaración: "sin revocación por token; desactivar o cambiar el rol corta el acceso en el siguiente request".
- **Recomendación**: **Opción A**.

---

### D6 — El mismo `401`, con tiempo similar, para usuario inexistente y contraseña incorrecta

- **Problema**: si no se calcula un hash cuando el usuario no existe, la respuesta es mucho más rápida y delata qué usuarios existen. La documentación de FastAPI resuelve esto con un hash ficticio.
- **Opciones**:
  - **Opción A — Siempre se verifica un hash, y `active` se mira al final**:
    ```python
    credentials = repository.get_credentials_by_username(normalized_username)
    candidate = credentials.password_hash if credentials else dummy_password_hash()
    password_ok = verify_password(candidate, password)
    if credentials is None or not password_ok or not credentials.active:
        raise AuthenticationError(AuthErrorCode.INVALID_CREDENTIALS)
    ```
    `dummy_password_hash()` hashea un valor aleatorio con los costos de producción, una vez por proceso (`functools.cache`), y `create_app` lo precalienta para que el primer login no sea un caso distinto. *Pros*: mismos pasos en todos los casos; la contraseña correcta de un usuario inactivo tampoco se distingue. *Contras*: cada intento consume 64 MiB (§4).
  - **Opción B — Agregar un retardo fijo o aleatorio**. *Contras*: no iguala el tiempo real y frena a todos.
  - **Opción C — Comparar sin hash ficticio y aceptar la diferencia**. *Contras*: permite enumerar usuarios.
- **Casos que devuelven el mismo `401`**: usuario inexistente, contraseña incorrecta, usuario inactivo (con contraseña correcta o incorrecta), usuario con mayúsculas que no existe.
- **Un hash corrupto** cuenta como contraseña incorrecta (`VerifyMismatchError`, `InvalidHashError`, `VerificationError`).
- **Rutas con `def`**: FastAPI las corre en el threadpool, así que argon2 no bloquea el event loop.
- **Tests**:
  - **Cuerpo**: comparación de bytes exactos del cuerpo y de los headers relevantes entre los cuatro casos, parametrizada.
  - **Tiempo** (`integration`, usuario con hash de costo real): mediana de 5 intentos por caso; el cociente debe estar entre 0,5 y 2. El margen es amplio a propósito para que no sea un test inestable. **Es evidencia de que el camino es el mismo, no una prueba de tiempo constante**.
- **Recomendación**: **Opción A**.

---

### D7 — El cuerpo del `401` y cómo convive con `{ "violations": [...] }`

- **Problema**: un `401` no es una regla del dominio. C-18 D6 ya rechazó meter `MALFORMED_REQUEST` en `violations` por eso mismo, y D1 de C-18 fija una tabla total sobre `ViolationCode`.
- **Opciones**:
  - **Opción A — Cuerpo propio y plano, con dos códigos**:
    ```json
    { "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }
    ```
    ```json
    { "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }
    ```
    *Pros*: el dominio no se entera de la autenticación; el enum de `violations` en OpenAPI sigue siendo verdad; es una respuesta que el cliente de API trata en un solo lugar (C-26: "ante `401` se descarta el token"). *Contras*: una tercera forma de error.
  - **Opción B — Reutilizar `errors` del `400`**, con `field: null` y `type: "invalid_credentials"`. *Pros*: solo dos formas. *Contras*: `errors` significa entrada malformada, y `field` no tiene sentido acá; Swagger confundiría.
  - **Opción C — Agregar códigos a `ViolationCode`**. *Contras*: un concepto de HTTP y autenticación en el dominio; rompe la spec "el dominio MUST NOT autenticar".
  - **Opción D — `{ "violations": [...] }` con códigos fuera del enum**. *Contras*: el OpenAPI mentiría.
  - **Opción E — `{ "detail": "..." }` de `HTTPException`**. *Contras*: otra forma más, sin código estable.
- **Las formas de error quedan así**:

| Status | Cuerpo | Origen | Quién lo trata en la UI |
|--------|--------|--------|-------------------------|
| `400` | `{ "errors": [...] }` | Entrada malformada (C-18 D6) | Error de programación o formulario |
| `401` | `{ "code", "message" }` | Autenticación (**este change**) | Cliente de API: descarta el token, vuelve al login |
| `403` | `{ "violations": [{ "code": "FORBIDDEN_OPERATION", ... }] }` | RBAC (**este change**) o propiedad (dominio) | Muestra el mensaje |
| `409` / `422` | `{ "violations": [...] }` | Dominio (C-18) | Muestra los mensajes |

- **Detalles**:
  - **Todo fallo de token da exactamente el mismo cuerpo**: vencido, alterado, ausente, usuario inactivo o rol cambiado. La UI hace lo mismo en todos los casos, y no se le da información a un atacante.
  - **`WWW-Authenticate: Bearer`** en todos los `401`, como exige la RFC 9110.
  - **Excepción de borde `AuthenticationError(code)`** con su handler, igual que `DomainRejectedError`.
  - **`HTTPBearer(auto_error=False)`**: con `auto_error=True` FastAPI responde con su propio `{ "detail": "Not authenticated" }`, y el status de ese caso cambió entre versiones.
  - **El `403` de RBAC** se lanza como `DomainRejectedError(Rejected((Violation(FORBIDDEN_OPERATION, mensaje),)))`, con mensajes como "No tiene permiso para reprogramar turnos.".
- **Recomendación**: **Opción A**.

---

### D8 — Contrato de `POST /api/auth/login` y `GET /api/auth/me`

- **Opciones de formato del login**:
  - **Opción A — JSON en camelCase**: entrada `{ "username", "password" }`, salida `{ "accessToken", "tokenType": "bearer" }`. *Pros*: consistente con KB 07 y C-18 D5; es lo natural para el frontend; no suma `python-multipart`, que C-18 D14 descartó. *Contras*: *Authorize* no puede pedir usuario y contraseña (D12).
  - **Opción B — Formulario OAuth2 (`OAuth2PasswordRequestForm`)**. *Pros*: *Authorize* muestra usuario y contraseña. *Contras*: exige `python-multipart`, form-urlencoded y `access_token` en snake_case.
- **Respuestas**:

| Ruta | Status | Cuerpo |
|------|--------|--------|
| `POST /api/auth/login` | `200` | `{ "accessToken": "<jwt>", "tokenType": "bearer" }`, con `Cache-Control: no-store` |
| | `400` | Campo faltante o fuera de largo; no devuelve lo enviado (C-18 D6) |
| | `401` | `INVALID_CREDENTIALS` |
| `GET /api/auth/me` | `200` | `{ "id", "username", "displayName", "role", "professionalId" }` |
| | `401` | `INVALID_TOKEN` |

- **Validación de entrada**: `username` de 1 a 150 caracteres; `password` como `SecretStr`, de 1 a 128 caracteres (cota para no gastar recursos en valores enormes). `extra="forbid"`. Un valor fuera de largo da `400`, sin relación con que el usuario exista.
- **`professionalId` es `null`** para recepción y administración.
- **`/me` no devuelve permisos**: `CHANGES.md:598` hace que la UI decida por rol, y la API sigue siendo la que rechaza. Si C-26 lo necesita, se discute allá.
- **Orden `400`/`401`** (**a comprobar en el RED**): FastAPI parsea el JSON del cuerpo antes de resolver dependencias, así que una ruta protegida con JSON roto y sin token puede dar `400` y no `401`. No expone datos, y KB 07 pone el JWT primero solo como flujo general. Se acepta y se fija con un test.
- **Recomendación**: **Opción A**.

---

### D9 — Matriz RBAC completa y cómo se aplica

KB 03 tiene 12 filas. Abierta por acción da **34 combinaciones de recurso y acción**, y **102 celdas** con los tres roles: 61 permitidas y 41 denegadas. "Reprogramar / cancelar" se separa porque el dominio las trata por separado.

Leyenda: `todos` = sobre cualquier registro · `propio` = solo los suyos · `—` = `403`.

| # | Recurso | Acción | Odontólogo | Recepción | Administrador | Quién aplica `propio` y qué más valida |
|---|---------|--------|------------|-----------|---------------|----------------------------------------|
| 1 | Turnos | Dar (C) | — | todos | todos | Solo RBAC |
| 2 | Turnos | Leer agenda (R) | todos ⚠️ | todos | todos | Ver P2 |
| 3 | Turnos | Reprogramar (U) | — | todos | todos | RBAC y **dominio** (`reschedule`) |
| 4 | Turnos | Cancelar (U) | — | todos | todos | RBAC y **dominio** (`cancel_appointment`) |
| 5 | Turnos | Cambiar estado (U) | propio | todos | todos | **Dominio** (`change_status`, por `professional_id`) |
| 6 | Historial de turno | Leer (R) | propio | todos | todos | Caso de uso (C-23) |
| 7 | Horario de atención | Crear (C) | propio | — | todos | Caso de uso (C-21) |
| 8 | Horario de atención | Leer (R) | propio ⚠️ | todos | todos | Caso de uso (C-21); ver P2 |
| 9 | Horario de atención | Actualizar (U) | propio | — | todos | Caso de uso (C-21) |
| 10 | Horario de atención | Borrar (D) | — | — | todos | Solo RBAC; ver nota |
| 11 | Bloqueos | Crear (C) | propio | — | todos | Caso de uso (C-21) |
| 12 | Bloqueos | Leer (R) | propio ⚠️ | todos | todos | Caso de uso (C-21); ver P2 |
| 13 | Bloqueos | Actualizar (U) | propio | — | todos | Caso de uso (C-21) |
| 14 | Bloqueos | Borrar (D) | propio | — | todos | Caso de uso (C-21) |
| 15 | Profesionales | Crear (C) | — | — | todos | Solo RBAC |
| 16 | Profesionales | Leer (R) | todos | todos | todos | Solo RBAC |
| 17 | Profesionales | Actualizar (U) | — | — | todos | Solo RBAC |
| 18 | Profesionales | Borrar (D) | — | — | todos | Solo RBAC; es desactivación (C-20) |
| 19 | Sillones | Crear (C) | — | — | todos | Solo RBAC |
| 20 | Sillones | Leer (R) | todos | todos | todos | Solo RBAC |
| 21 | Sillones | Actualizar (U) | — | — | todos | Solo RBAC |
| 22 | Sillones | Borrar (D) | — | — | todos | Solo RBAC; es desactivación (C-20) |
| 23 | Prestaciones | Crear (C) | — | — | todos | Solo RBAC |
| 24 | Prestaciones | Leer (R) | todos | todos | todos | Solo RBAC |
| 25 | Prestaciones | Actualizar (U) | — | — | todos | Solo RBAC |
| 26 | Prestaciones | Borrar (D) | — | — | todos | Solo RBAC; es desactivación (C-20) |
| 27 | Pacientes | Crear (C) | — | todos | todos | Solo RBAC |
| 28 | Pacientes | Leer (R) | todos | todos | todos | Solo RBAC |
| 29 | Pacientes | Actualizar (U) | — | todos | todos | Solo RBAC |
| 30 | Pacientes | Borrar (D) | — | — | — | **Nadie**: KB 03 da `CRU`, sin `D` |
| 31 | Usuarios y roles | Crear (C) | — | — | todos | Solo RBAC; sin ruta en el MVP (D17) |
| 32 | Usuarios y roles | Leer (R) | — | — | todos | Ídem |
| 33 | Usuarios y roles | Actualizar (U) | — | — | todos | Ídem |
| 34 | Usuarios y roles | Borrar (D) | — | — | todos | Ídem; ver D16 |

**Nota para C-21 (fila 10)**: KB 03 le da al odontólogo `CRU` sin `D` en horarios, pero `PUT /working-hours` reemplaza todos los tramos: una lista vacía equivale a borrar. C-21 lo tiene que resolver.

- **Cómo se aplica — opciones**:
  - **Opción A — Tabla de datos y dependencia que devuelve el alcance**:
    ```python
    PERMISSIONS: Mapping[tuple[Resource, Action], Mapping[Role, Scope]]  # Scope.ALL | Scope.OWN

    @router.post("/appointments", responses=permission_responses())
    def create(permission: Annotated[Permission, Depends(require_permission(Resource.APPOINTMENT, Action.CREATE))]) -> ...:
        permission.actor  # Actor del dominio
        permission.scope  # ALL u OWN
    ```
    Un rol sin entrada recibe `403` por defecto. *Pros*: la tabla se lee igual que KB 03; sin casos especiales en las rutas. *Contras*: `Scope.OWN` no se aplica solo: lo tiene que usar la ruta.
  - **Opción B — `require_role(Role.X, Role.Y)` por ruta**. *Pros*: más corta. *Contras*: la matriz queda repartida entre rutas; no se puede probar ni comparar con KB 03; contradice `CHANGES.md:488`.
  - **Opción C — Solo en el dominio**. *Contras*: el dominio solo conoce turnos, no catálogos ni usuarios; no recibe `Actor` al dar turno.
- **¿Duplica reglas del dominio?** No se rompe la regla dura, que habla de RN-AG y RN-TU; la matriz es RN-AC. Pero las filas 3, 4 y 5 existen en ambos lados. Para que no se separen, un **test de paridad** recorre `cancel_appointment`, `reschedule_appointment` y `change_status` con cada rol, y exige que coincidan con la tabla. `OWN` en el borde significa "dejar pasar y que decida el dominio" en la fila 5: **la API nunca compara el propietario de un turno**.
- **Rechazo por defecto**:
  - `protected_router = APIRouter(dependencies=[Depends(get_current_user)])`: todos los routers de C-20 a C-24 cuelgan de él.
  - **Test guardián de rutas**: recorre `app.openapi()`, y toda operación fuera de la lista pública de KB 03 (`/api/health`, `/api/auth/login`) tiene que tener `security` y responder `401` sin token.
  - **Test guardián de permisos**: toda ruta protegida, salvo `/api/auth/me`, tiene que incluir un `require_permission` en sus dependencias (`route.dependant`, **a comprobar en el RED**). Así C-20 no puede olvidarlo sin que falle.
- **Tests**: tabla total contra el producto de recursos y acciones; las **102 celdas** parametrizadas contra rutas montadas por el test (patrón C-18 D15), con usuarios reales y token real, verificando `200`/`403` y el cuerpo `FORBIDDEN_OPERATION`.
- **Recomendación**: **Opción A**, con los dos guardianes y el test de paridad.

---

### D10 — Cómo se arma el `Actor` del dominio

- **Problema**: el `Actor` tiene que salir de datos confiables, y el dominio no puede conocer usuarios.
- **Opciones**:
  - **Opción A — Un tipo del borde y una dependencia que lo convierte**:
    ```python
    @dataclass(frozen=True, slots=True)
    class AuthenticatedUser:          # app/auth/model.py. Sin password_hash.
        id: UUID
        username: str
        display_name: str
        role: Role                    # enum del dominio
        professional_id: UUID | None

        def to_actor(self) -> Actor:
            return Actor(user_id=self.id, role=self.role, professional_id=self.professional_id)
    ```
    `get_current_actor` y `Permission.actor` lo exponen a las rutas. *Pros*: una sola conversión; `Role` no se duplica; el usuario autenticado no tiene hash. *Contras*: un tipo más.
  - **Opción B — Armar `Actor` desde los claims**. *Contras*: el token no tiene `professional_id`, y C-19 no lo quiere agregar (D4, D5).
  - **Opción C — Pasar `UserModel` a las rutas**. *Contras*: el ORM sale de los repositorios (DD-03) y arrastra el hash.
- **De dónde sale cada campo**:

| Campo de `Actor` | Fuente | Garantía |
|------------------|--------|----------|
| `user_id` | `sub`, confirmado contra la base | El usuario existe y está activo |
| `role` | Claim `role` | Igual al de la base (D5) |
| `professional_id` | **Solo** de la base | Coherente por el `CHECK` (D2) |

- **`changed_by` es siempre `actor.user_id`**, nunca un dato del cliente (`NewAppointmentRequest.changed_by`, RN-TU-06). Lo aplican C-22 y C-23.
- **En el seed, `user_id` y `professional_id` son distintos a propósito**, como en la spec (U1 ≠ P1), para que un bug que los confunda falle en los tests.
- **Recomendación**: **Opción A**.

---

### D11 — Seed por rol y qué pasa si falta `SEED_USER_PASSWORD`

- **Usuarios** (ficticios, en `app/demo_data.py`, sin contraseña; ids fijos, como el resto):

| `username` | `display_name` | `role` | `professional_id` |
|------------|----------------|--------|-------------------|
| `administrador` | Administración Demo | `administrador` | `null` |
| `recepcion` | Recepción Demo | `recepcion` | `null` |
| `odontologo` | Dra. Laura Quiroga | `odontologo` | `...000000000001` (primer profesional) |

- **Problema**: hoy `seed_user_password` es obligatorio en `Settings`, así que (a) **la API no arranca sin una variable que solo usa el seed**, y (b) `SEED_USER_PASSWORD=` vacío pasa la validación: se guardaría el hash de una contraseña vacía.
- **Opciones si falta o está vacía**:
  - **Opción A — Opcional en `Settings`; el seed falla antes de escribir nada**. `SecretStr | None`, con `None` por defecto. Vacía o solo espacios cuenta como faltante, y menos de 8 caracteres también se rechaza. `seed_database` lanza un error en español que nombra la variable, **antes de abrir la transacción**; `main()` termina con código distinto de 0. *Pros*: la API de producción no depende de un secreto de desarrollo; un seed nunca queda a medias; el error es claro. *Contras*: se relaja "las 14 son obligatorias" para esta variable (`.env.example` no cambia).
  - **Opción B — Sigue obligatoria, y solo se rechaza la vacía**. *Pros*: sin cambio de contrato. *Contras*: la API sigue exigiendo y cargando en memoria una contraseña de seed.
  - **Opción C — Cargar los catálogos y saltear los usuarios con un aviso**. *Pros*: el seed "funciona". *Contras*: el fallo aparece después, en el login, con un `401` difícil de entender.
  - **Opción D — Generar una contraseña e imprimirla**. *Contras*: una credencial en la consola y en los logs, contra DD-11.
- **Comportamiento recomendado**:

| Situación | Resultado |
|-----------|-----------|
| Falta, vacía, solo espacios o menos de 8 caracteres | Error que nombra la variable, sin mostrar el valor; **no se inserta nada**, tampoco catálogos |
| `APP_ENV=production` | El seed se niega a correr (KB 08: "solo desarrollo") |
| Primera corrida correcta | Crea los 3 usuarios con `hash_password`; imprime solo conteos |
| Segunda corrida | Inserta 0, sin hashear; **no actualiza contraseñas**, como pide la spec del seed ("no SHALL actualizar") |
| Cambiaste la variable después | No tiene efecto: hay que recrear los usuarios (se documenta en `backend/README.md`) |

- **Sigue siendo manual**: nunca corre al arrancar.
- **Tests** (`integration`): las 2 corridas con conteos exactos; login de cada rol con la contraseña de `Settings`; cada caso de error deja 0 filas en **todas** las tablas; el valor no aparece en `capsys`.
- **Recomendación**: **Opción A**, incluida la negativa en producción.

---

### D12 — El botón *Authorize* en Swagger

- **Opciones**:
  - **Opción A — `HTTPBearer`: se pega el token**:
    ```python
    bearer_scheme = HTTPBearer(
        auto_error=False,
        scheme_name="bearerAuth",
        bearerFormat="JWT",
        description="Pegue el accessToken de POST /api/auth/login, sin la palabra Bearer.",
    )
    ```
    `create_app` agrega `swagger_ui_parameters={"persistAuthorization": True}`, para no perder la autorización al recargar. *Pros*: encaja con D8; un solo esquema; refleja lo que hace el frontend. *Contras*: un paso más en el video.
  - **Opción B — `OAuth2PasswordBearer(tokenUrl=...)`**. *Pros*: *Authorize* pide usuario y contraseña, más vistoso en el video. *Contras*: exige el formulario de la Opción B de D8.
  - **Opción C — Dos logins, JSON y formulario**. *Contras*: duplica la superficie más sensible de la API solo para el video.
- **Lo que se ve en el video**:
  ```
  POST /api/auth/login  (sin candado)  --> copiar accessToken
           |
           v
  Authorize --> pegar el token --> candados cerrados
           |
           v
  GET /api/auth/me --> 200 con el rol
  ```
- **Documentación de errores**: la transformación de OpenAPI de C-18 D9 se extiende con una regla: toda operación con `security` recibe `401` con `AuthErrorResponse`, sin que nadie se acuerde. El `403` se declara por ruta con `permission_responses()`. Login documenta su `401` a mano, porque es pública. Como `security` no es un parámetro, no dispara el `400` automático.
- **Sin credenciales en los ejemplos**: el ejemplo del login usa un texto que claramente no sirve como contraseña; `SecretStr` la marca como `format: password`.
- **Con esto, C-19 es el primer endpoint con cuerpo en Swagger**, así que ya muestra el `400` que C-18 D9 anunciaba.
- **Tests**: `securitySchemes.bearerAuth` existe; `/auth/me` tiene `security` y `401`; `/auth/login` y `/health` no tienen `security`; ningún esquema contiene `passwordHash`.
- **Recomendación**: **Opción A**.

---

### D13 — Variables de entorno nuevas

**Ninguna.** Las cuatro que usa C-19 ya están en KB 08, en `Settings` y en `.env.example`:

- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRES_MIN`
- `SEED_USER_PASSWORD`

Lo que cambia es su validación (D4 y D11). A propósito **no** se agrega una variable para el costo del hash (D3) ni para un algoritmo alternativo. Compose no cambia: el servicio `backend` ya lee `.env` (C-18 D13).

**Recomendación**: **no agregar variables**.

---

### D14 — Probar tokens vencidos y alterados sin mocks

- **Problema**: PyJWT lee el reloj real y `decode` no acepta un `now`.
- **Opciones**:
  - **Opción A — Emitir tokens reales con un `now` en el pasado**: `create_access_token(user, settings, now)` recibe `now`, como todo en el proyecto. Un token vencido es un token real, con firma válida, emitido por el código de producción, y se rechaza con el reloj real. Los alterados se arman con PyJWT o a mano. *Pros*: sin `monkeypatch`, `freezegun` ni `dependency_overrides`; ejercita firma y vencimiento reales. *Contras*: no se puede probar el borde exacto del segundo, pero `leeway` queda en 0 y un caso `exp = ahora - 1 s` lo cubre.
  - **Opción B — `freezegun`**. *Contras*: otra dependencia; es un mock del reloj.
  - **Opción C — `verify_exp=False` y comparar `exp` a mano con un `now` inyectado**. *Pros*: testeable al segundo. *Contras*: **reimplementa a mano una validación de seguridad** que la librería ya resuelve.
- **Casos** (todos dan `401`, exactamente el mismo cuerpo `INVALID_TOKEN` y `WWW-Authenticate: Bearer`):

| # | Caso | Cómo se arma | ¿Base? |
|---|------|--------------|--------|
| 1 | Vencido hace tiempo | `create_access_token(user, settings, now=2020)` | No |
| 2 | Vencido hace 1 segundo | `now = ahora - JWT_EXPIRES_MIN - 1 s` | No |
| 3 | Rol cambiado sin refirmar | Se reemplaza el payload y se deja la firma original | No |
| 4 | Firma alterada | Se cambia el **primer** carácter de la firma | No |
| 5 | Otra clave | `jwt.encode` con otro secreto | No |
| 6 | `alg: none` | Header y payload a mano, sin firma | No |
| 7 | Otro algoritmo, misma clave | `jwt.encode(..., algorithm="HS512")` | No |
| 8 | Sin `exp` / `sub` / `role` | `jwt.encode` con la clave real, sin ese claim | No |
| 9 | `sub` no es UUID; `role` no existe | `jwt.encode` con la clave real | No |
| 10 | Ausente, vacío, `Basic ...`, basura | Header en el `TestClient` | No |
| 11 | Token en query (`?token=`) | Sin header | No |
| 12 | Válido de usuario inexistente | `create_access_token` con un id sin fila | **Sí** |
| 13 | Válido de usuario desactivado | `UPDATE` real, mismo token | **Sí** |
| 14 | Válido con rol cambiado | `UPDATE` real, mismo token | **Sí** |

- **Trampa del caso 4**: **no se debe cambiar el último carácter**. Los últimos bits de una firma base64url de 32 bytes no se usan, y dos caracteres finales distintos pueden decodificar a los mismos bytes: el test pasaría o fallaría al azar. Se cambia el primero.
- **Casos 1 a 11**: se rechazan antes de la base, así que corren sin la marca `integration`. **Es lo que hay que comprobar**: una fixture con un puerto cerrado demuestra que no se abre conexión.
- **Contraprueba**: el mismo armado con `now` actual y clave real responde `200`. Sin esto, un test de "rechaza todo" pasaría con el código roto.
- **Vigencia**: `exp - now == JWT_EXPIRES_MIN`, decodificando con PyJWT.
- **Recomendación**: **Opción A**.

---

### D15 — Que ni el hash ni la contraseña aparezcan en respuestas ni en logs

Revisando el camino de punta a punta hay más lugares de fuga que los esquemas de respuesta:

| # | Lugar de fuga | Cómo se tapa | Test |
|---|---------------|--------------|------|
| 1 | Cuerpo de `/login` y `/me` | `response_model` explícito, sin campo de hash | Se recorre el JSON: ni el hash, ni la contraseña, ni una clave `password*` |
| 2 | OpenAPI | Ídem | Ningún esquema de respuesta con `passwordHash` |
| 3 | `400` que devuelve la entrada | C-18 D6 ya descarta `input` | Login con contraseña marcada y campo inválido: la marca no vuelve |
| 4 | `repr` de los tipos internos | **El hash vive solo en `UserCredentials`**, con `field(repr=False)`; `AuthenticatedUser` no lo tiene | `repr` no contiene el hash |
| 5 | `repr` de `Settings` | `SecretStr` en `jwt_secret` y `seed_user_password` (D4, D11) | `repr` no contiene el valor |
| 6 | Error de validación de `Settings` | `hide_input_in_errors=True` (D4) | Secreto corto: el mensaje nombra la variable y no el valor |
| 7 | **Errores de SQLAlchemy** | `hide_parameters=True` en `create_engine`: por defecto el mensaje incluye `[parameters: ...]`, **hash incluido** | Insertar un `username` duplicado: `str(error)` no contiene el hash |
| 8 | **Errores de PostgreSQL** | Un `CHECK` fallido incluye `DETAIL: Failing row contains (...)`, **con el hash**, y `hide_parameters` no lo tapa (**a comprobar en el RED**). El repositorio mapea por `constraint_name` y relanza `from None` | Violar el `CHECK` por el repositorio: la excepción no contiene el hash |
| 9 | Logs de la aplicación | **`app/auth` no escribe logs**: ni intentos fallidos, porque un usuario a veces escribe la contraseña en el campo equivocado | `caplog` en `DEBUG`, con `sqlalchemy.engine`: un login correcto y uno fallido no contienen contraseña, hash ni token |
| 10 | Log de acceso de uvicorn | Registra método, ruta y status, sin cuerpo ni headers. La contraseña nunca va en la URL | Ídem: el login solo lee el cuerpo |
| 11 | Salida del seed | Imprime solo conteos | `capsys` |
| 12 | Cachés intermedios | `Cache-Control: no-store` en el login | Header exacto |

- **`/me` y el login no llevan el hash ni por error**: `get_credentials_by_username` es el único método del repositorio que lo lee, y solo lo usa el login.
- **Límite conocido**: el log del propio servidor PostgreSQL también guarda ese `DETAIL` al fallar un `CHECK`. Vive dentro del contenedor local, y el seed y los datos válidos no lo disparan. Se acepta en el MVP.
- **Recomendación**: **aplicar las 12 filas**.

---

### D16 — ¿`changed_by` pasa a ser FK a usuarios?

- **Problema**: el ERD de KB 04 lo marca como relación, pero `models.py:201` no tiene FK. Las pruebas de integración mencionan `changed_by` en 17 líneas de 3 archivos, con ids como `USER1 = ...000099` y sin ninguna fila de usuario, y la spec usa ese mismo id en un escenario.
- **Opciones**:
  - **Opción A — Sin FK en C-19, y los usuarios nunca se borran físicamente**. *Pros*: no toca C-17 ni su spec archivada; el `changed_by` real siempre viene de un usuario autenticado (D10). *Contras*: la base no garantiza la autoría; un borrado por SQL dejaría huérfanos.
  - **Opción B — FK `RESTRICT` ahora**. *Pros*: es lo que dice el ERD; integridad real. *Contras*: reescribe los datos de 3 archivos de integración y un escenario; amplía C-19 hacia C-17; una base local con turnos cargados con ese id de prueba haría fallar la migración.
- **Recomendación**: **Opción A**. Se anota en KB 04 que la relación es lógica. La fila 34 de la matriz (Borrar usuario) se implementa como desactivación.

---

### D17 — Hueco: nadie entrega el ABM de usuarios

- **Problema**: KB 03 le da al administrador CRUD de usuarios, y SU-06 dice "los crea el administrador o el seed", pero no encontré en `CHANGES.md` ninguna ruta `/api/users`. Sin eso, **desactivar un usuario o cambiarle el rol (D5) solo se puede hacer por SQL**.
- **Opciones**:
  - **Opción A — Dejarlo fuera de C-19, y aclararlo**: los usuarios del MVP salen del seed; las filas 31 a 34 quedan en la matriz, listas para el backlog; se corrige SU-06. Los tests de D5 usan un `UPDATE` real. *Pros*: no agranda un change crítico; alcanza para la demo con tres roles. *Contras*: la cláusula de la matriz no tiene ruta, y agregar un odontólogo requiere tocar el seed o SQL.
  - **Opción B — Agregar el ABM a C-19**. *Pros*: cumple KB 03 entera. *Contras*: suma validación de contraseñas, cambio de rol, y "no te desactives a vos mismo", en el change más sensible.
  - **Opción C — Change nuevo (`api-usuarios`) después de C-20, recortable**. *Pros*: respeta el orden. *Contras*: otro change más, con plazo ajustado.
- **Recomendación**: **Opción A**, y anotar la Opción C como backlog si te queda tiempo.

---

### D18 — Organización del código

- **Opción A — Estructura de KB 08, con una capa de tipos propia**:
  ```
  app/auth/model.py        AuthenticatedUser, UserCredentials
  app/auth/passwords.py    hash_password, verify_password, dummy_password_hash
  app/auth/tokens.py       create_access_token, decode_access_token
  app/auth/permissions.py  Resource, Action, Scope, PERMISSIONS (sin FastAPI)
  app/auth/login.py        authenticate(...) (sin FastAPI)
  app/repositories/users.py  UserRepository
  app/api/auth.py          rutas /auth/login y /auth/me
  app/api/deps.py          get_current_user, get_current_actor, require_permission
  app/api/errors.py        AuthenticationError y su handler
  app/db/models.py         UserModel
  ```
  *Pros*: `app/auth/` es lo que KB 08 ya prevé; lo que no depende de HTTP se prueba sin `TestClient`; el repositorio devuelve tipos propios, sin ORM. *Contras*: el repositorio de usuarios devuelve tipos de `auth`, no de `domain`, porque el dominio no conoce usuarios.
- **Opción B — Todo en `app/api/auth.py`**. *Contras*: mezcla HTTP, criptografía y reglas, y el seed tendría que importar de la API.
- **Por qué ningún `UserRepository.create` devuelve `Rejected`**: no hay regla del dominio. Solo lo usa el seed, con datos válidos; relanza errores sin el `DETAIL` (D15, fila 8).
- **Recomendación**: **Opción A**.

---

## 4. Riesgos y preguntas para la autora

### Riesgos de seguridad

| # | Riesgo | Severidad en el MVP | Mitigación o decisión |
|---|--------|---------------------|-----------------------|
| 1 | **Fuerza bruta en el login**: sin límite de intentos ni bloqueo | Media | Argon2 frena cada intento, y el alcance es local. **Se acepta y se documenta**. Un límite por usuario abriría, además, un bloqueo a cuentas ajenas. |
| 2 | **Denegación de servicio por memoria**: cada login usa 64 MiB; con los hilos por defecto de anyio (40, **a comprobar**) el pico serían unos 2,5 GiB | Media | Se acepta en local. Si molesta, el perfil de OWASP (D3) lo reduce. |
| 3 | **`JWT_SECRET` débil o filtrado**: con él se fabrica un token de administrador, aunque D5 exige que el usuario exista y el rol coincida | Alta si ocurre | Mínimo de 32 caracteres (D4), solo en `.env`. Rotarlo invalida todas las sesiones, algo aceptable. |
| 4 | **Token robado**: vale hasta `exp`, sin revocación | Media | `exp` corto (`JWT_EXPIRES_MIN`); desactivar al usuario lo corta (D5). |
| 5 | **XSS y dónde guardar el token** | Alta, en C-26 | Fuera de este change: C-26 tiene governance ALTO justamente por esto. |
| 6 | **Sin HTTPS**: credenciales y token viajan en claro | Baja en local | Fuera del alcance. Queda documentado que un despliegue real lo necesita. |
| 7 | **Ruta nueva sin protección** en C-20 a C-24 | Alta si ocurre | Rechazo por defecto y los dos guardianes (D9). |
| 8 | **Alcance `OWN` no aplicado** en C-21 o C-23: el guardián ve que hay permiso, pero no que se use el alcance | Media | Tests obligatorios de `403` por registro ajeno; C-21 ya los pide (`CHANGES.md:518`). |
| 9 | **Hash en logs de PostgreSQL** por un `CHECK` fallido | Baja | D15, fila 8. Se acepta en local. |
| 10 | **Contraseña única en el seed** para los tres roles | Baja | Solo desarrollo, y el seed se niega en producción (D11). |
| 11 | **`persistAuthorization` deja el token en el `localStorage` de Swagger** | Baja | Herramienta de desarrollo. El token vence. |
| 12 | **Odontólogo con profesional desactivado** sigue entrando | Baja | `active` del usuario y del profesional son independientes. Ver P4. |

### Riesgos de implementación

1. **C-18 no está terminado** (2/21 tareas) y otro agente lo está escribiendo. C-19 usa `DomainRejectedError`, `get_db_session`, `create_app` y la transformación de OpenAPI. *Mitigación*: **el apply de C-19 arranca recién con C-18 archivado**, como dice la dependencia en `CHANGES.md`. El propose se puede escribir antes, usando solo su `design.md`.
2. **Tocar `create_database_engine`** para `hide_parameters` y **`Settings`** choca con C-18 si se hace en paralelo (D7 de C-18 toca el mismo archivo). Se resuelve con el punto anterior.
3. **Test de `downgrade -1`** (§2.2): se rompe en cuanto exista la migración; hay que fijar la revisión destino. Es lo primero de la tarea 2.
4. **Test de tiempo inestable** (D6). *Mitigación*: margen amplio, mediana, y marca `integration`.
5. **Tipos**: `jwt.decode` devuelve `dict[str, Any]`. *Mitigación*: anotar `Mapping[str, object]` y validar con narrowing.
6. **Comportamientos marcados a comprobar**: `verify` con los parámetros del hash (D3); `hide_input_in_errors` (D4); orden `400`/`401` (D8); `route.dependant` (D9); `DETAIL` de PostgreSQL (D15); `SELECT * FROM user` (D1). Cada uno tiene un test que lo fija.

### Documentación por corregir si se aprueba (en el propose o el apply)

- `CHANGES.md:485`: tabla `app_user`, con la regla del `CHECK` y los índices.
- KB 04: nombre de la tabla, `display_name` no nulo, `CHECK` de D2, y `changed_by` como relación lógica (D16).
- KB 09, SU-06: aclaración de D5 y de D17. KB 03: precisión de la fila de agenda según P2.
- KB 08: `SEED_USER_PASSWORD` opcional para la API.
- Spec `database-infrastructure`: delta `MODIFIED` del seed, y `ADDED` de la tabla.
- Spec nueva `authentication-and-rbac`. Requisitos de `api-foundation`, según cómo haya quedado archivada C-18.
- `backend/README.md`: seed por rol, contraseña, y `JWT_SECRET` de 32 caracteres.

### Preguntas para la autora

Todas están formuladas como **D1 a D18** para responderlas en un único mensaje, por ejemplo: *"Aprobadas D1–D18 con las opciones recomendadas; P1 confirmada; P2 opción A; P3 sí; P4 no"*, o indicando la opción de cada una. **Por governance CRÍTICO, sin esa aprobación explícita no se escribe código.**

Además de las decisiones, estas cuatro no se pueden deducir del repo:

- **P1 — SU-06 con la cátedra**: KB 09 pide confirmar "al llegar a C-19" que sin refresh tokens ni revocación alcanza. ¿Ya lo confirmaste? *Sugerencia*: si no, seguir con la suposición y registrarlo como pendiente, porque D5 ya cubre lo más riesgoso.
- **P2 — Lectura del odontólogo sobre lo ajeno** (filas 2, 8 y 12):
  - **Opción A — Agenda completa (`todos`) en la fila 2; horarios y bloqueos directos solo `propio`**. `GET /api/agenda` igual los incluye, como pide C-24. Los motivos de bloqueo ajenos quedan visibles por esa vía. **Recomendada**: es lo que dicen `CHANGES.md:561` y la suposición de KB 03.
  - **Opción B — Igual, y C-24 oculta `reason` de los bloqueos ajenos**. Protege un dato más ("vacaciones", "médico"), con un poco más de trabajo.
  - **Opción C — Solo su propia agenda**. Contradice C-24.
- **P3 — Negativa del seed con `APP_ENV=production`** (D11): es una línea y un test, pero nadie lo pidió. *Sugerencia*: sí.
- **P4 — Odontólogo cuyo profesional está desactivado** (riesgo 12): ¿tiene que seguir entrando? *Sugerencia*: sí, en el MVP; puede ver su historial y no se le pueden dar turnos nuevos (`INACTIVE_REFERENCE`). Bloquearlo cruzaría dos entidades en `get_current_user`.

Las decisiones que más merecen tu atención:

- **D1**: la tabla se llama `app_user`, no `user`.
- **D5**: se lee el usuario en cada request, y un rol cambiado da `401`.
- **D7**: el `401` usa una tercera forma de error.
- **D11**: `SEED_USER_PASSWORD` deja de ser obligatoria para la API.
- **D16** y **D17**: sin FK en `changed_by` y sin ABM de usuarios.
- **D4**: tu `.env` local puede necesitar un `JWT_SECRET` más largo.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md` del propose)

> Esta lista es solo una propuesta dentro del explore; no se creó `openspec/changes/autenticacion-jwt-y-roles/`. **Prerrequisito del apply: C-18 archivado y este diseño aprobado.** Las tareas siguen Strict TDD.

### Grupo 1 — Configuración y dependencias
- **1.1** Agregar `PyJWT` y `argon2-cffi`, y verificar que la suite sigue en verde.
- **1.2** RED + GREEN: validaciones de `Settings`, `SecretStr`, `hide_input_in_errors`; `seed_user_password` opcional; actualizar `test_config.py` (D4, D11).
- **1.3** RED + GREEN: `hide_parameters=True` en el engine (D15, fila 7).

### Grupo 2 — Tabla de usuarios
- **2.1** Fijar la revisión destino del test de `downgrade -1` (§2.2) y verificar que sigue en verde.
- **2.2** RED + GREEN: `UserModel`, migración `20261106_06_usuarios`, `CHECK` e índices; actualizar el conjunto de tablas y `clean_database_tables`; ciclo `upgrade`/`downgrade` (D1, D2).
- **2.3** RED + GREEN: `UserRepository`, `AuthenticatedUser` y `UserCredentials`, y errores sin `DETAIL` (D10, D15, D18).

### Grupo 3 — Contraseñas
- **3.1** RED + GREEN: `hash_password` y `verify_password`, con el prefijo exacto y hash corrupto (D3).
- **3.2** RED + GREEN: helper de hash barato para tests, y guardia de `CHEAPEST` fuera de `app/` (D3).

### Grupo 4 — Tokens
- **4.1** RED + GREEN: `create_access_token` con `now` inyectado y `decode_access_token`: los 11 casos sin base, con contraprueba (D4, D14).

### Grupo 5 — Login
- **5.1** RED + GREEN: `authenticate` y hash ficticio (D6).
- **5.2** RED + GREEN: `AuthenticationError`, handler, cuerpo de `401` y `WWW-Authenticate` (D7).
- **5.3** RED + GREEN: `POST /api/auth/login`: `200`, `no-store`, los 4 casos de `401` idénticos, `400` sin eco; test de tiempo (D6, D8).

### Grupo 6 — Usuario autenticado y `/me`
- **6.1** RED + GREEN: `get_current_user`, `get_current_actor` y `GET /api/auth/me`; casos 12 a 14 con `UPDATE` real (D5, D10, D14).

### Grupo 7 — RBAC
- **7.1** RED + GREEN: tabla `PERMISSIONS` total, con los valores exactos de D9.
- **7.2** RED + GREEN: `require_permission` con `403 FORBIDDEN_OPERATION`, y las 102 celdas (D7, D9).
- **7.3** RED + GREEN: test de paridad con el dominio (filas 3, 4 y 5).
- **7.4** RED + GREEN: `protected_router` y los dos guardianes de rutas (D9).

### Grupo 8 — Seed
- **8.1** RED + GREEN: usuarios en `demo_data`, seed idempotente, errores sin escrituras, negativa en producción; actualizar `test_catalog_persistence.py` (D11).

### Grupo 9 — Swagger y fugas
- **9.1** RED + GREEN: `bearerAuth`, `persistAuthorization`, `401` automático en la transformación de OpenAPI (D12).
- **9.2** RED + GREEN: pruebas de fuga de D15 que falten, con `caplog` y `capsys`.

### Grupo 10 — Verificación y documentación
- **10.1** Corregir `CHANGES.md`, KB 03, 04, 08 y 09, y `backend/README.md`.
- **10.2** Ejecutar `pytest`, `pytest -m integration`, `mypy --strict`, mutaciones sobre las reglas críticas (`CHECK`, firma, `active`, rol), `docker compose up --build`, el flujo de Swagger de D12, `openspec validate --strict` y `git diff --check`, y registrar las evidencias en `docs/evidencias/`.
