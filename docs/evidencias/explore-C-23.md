# Explore C-23 — `api-ciclo-de-vida-del-turno`

Fecha: 2026-11-06
Fase: 5 — API REST FastAPI y JWT
Governance: **MEDIO** (según `CHANGES.md` §[C-23])
Dependencias en `CHANGES.md`: `C-11`, `C-12`, `C-22`.

> Este explore es analítico: no ejecutó docker, pytest, alembic ni pip, y no tocó código, tests, migraciones, specs, `CHANGES.md` ni la KB. Se hizo sobre el repositorio con C-21 **en implementación** (árbol de trabajo sucio en `backend/`) y C-22 **todavía no implementado** (`openspec list`: `api-dar-turno` 0/16). Los archivos a medio hacer de C-21 **no se tomaron como fuente de verdad**; las referencias a C-21 salen de `openspec/changes/api-horarios-y-bloqueos/design.md`. Las referencias a C-22 salen de `openspec/changes/api-dar-turno/design.md` y de `docs/evidencias/explore-C-22.md`. El apply de C-23 tiene que esperar a que C-22 esté archivado y verde.

---

## 1. Alcance de C-23 según `CHANGES.md` y qué queda afuera

### Qué entra en C-23

1. **`POST /api/appointments/{id}/cancel`**: cancelar un turno `reservado` o `confirmado`.
2. **`POST /api/appointments/{id}/reschedule`**: mover inicio, profesional, sillón y/o duración, revalidando todas las RN-AG y excluyendo al propio turno.
3. **`POST /api/appointments/{id}/status`**: cambiar a `confirmado`, `atendido` o `ausente` según RN-TU-02 y RN-TU-05.
4. **`GET /api/appointments/{id}/history`**: leer el historial inmutable, ordenado, con `from`, `to`, `changed_by` y `changed_at`, más el detalle de reprogramación cuando exista.
5. **Transaccionalidad**: turno e historial en una sola transacción; ya la resuelven los servicios de C-17.
6. **RBAC**: cancelar y reprogramar solo recepción/administración; cambiar estado el odontólogo solo en turnos propios; historial el odontólogo solo de turnos propios (RN-AC-01).
7. **Traducción de errores**: `404` si el turno de la ruta no existe; `403` por rol o por propiedad; `409` para choques de agenda al reprogramar; `422` para reglas de validez y transiciones inválidas; `400` para entrada malformada.
8. **Tests de integración**: cada transición válida e inválida, reprogramación con choque y al pasado, `403` por rol y por propiedad, historial ordenado y con su forma completa.

### Qué queda explícitamente afuera

- **`GET /api/agenda`** y listados de turnos: es C-24.
- **`GET /api/appointments/{id}`** (detalle puntual): quedó fuera de C-22 y C-23; si la UI lo necesita, se suma a C-24.
- **Pantallas**: C-25 en adelante.
- **ABM de usuarios o `GET /api/users`**: C-19 lo cerró; los usuarios salen del seed y no hay endpoint para resolver nombres.
- **Nuevas reglas de dominio, migraciones o tablas**: no hacen falta. C-10, C-11, C-12 y C-17 ya dejaron transiciones, reprogramación e historial persistido.
- **Edición o borrado del historial**: prohibido por diseño; solo lectura.
- **Soporte de `note`**: la KB lo menciona en los Flujos 2 y 3, pero el dominio y la persistencia cerrados no lo modelan (ver D4).

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-23 reutiliza

| Pieza | Dónde | Qué ofrece |
|-------|-------|------------|
| `change_appointment_status(...)` | `backend/app/services/appointments.py:169` | Bloquea la fila del turno con `SELECT ... FOR UPDATE`, relee el estado, llama a `change_status`, actualiza turno e inserta historial. Devuelve `ValidationResult` o `None`. |
| `cancel_appointment(...)` | `backend/app/services/appointments.py:244` | Igual, pero con el destino fijo `cancelado`; llama a `cancel_appointment` del dominio. |
| `reschedule_appointment(...)` | `backend/app/services/appointments.py:317` | Bloquea turno, profesionales y sillones (origen y destino), revalida el nuevo destino, actualiza el turno y persiste las 8 columnas de `RescheduleDetail`. |
| `change_status` / `cancel_appointment` | `backend/app/domain/appointment/transitions.py:69` y `:36` | Tabla RN-TU-02, permiso del odontólogo por propiedad, `STATUS_CHANGE_TOO_EARLY` e `INVALID_TRANSITION`. |
| `reschedule_appointment` | `backend/app/domain/appointment/reschedule.py:40` | Solo desde `reservado`/`confirmado`, vuelve a `reservado`, conserva id, excluye al propio turno y revalida RN-AG. |
| `RescheduleRequest` | `backend/app/domain/model.py:162` | `start_at` obligatorio; `professional_id`, `chair_id` y `duration_min` opcionales (`None` conserva el valor actual). |
| `AppointmentStatus`, `AppointmentStatusChange`, `RescheduleDetail`, `Actor` | `backend/app/domain/model.py:22`, `:356`, `:335`, `:40` | Estados en español; historial inmutable; detalle tipado de reprogramación; identidad con `user_id`, `role` y `professional_id`. |
| Matriz RBAC | `backend/app/auth/permissions.py:47-53` | `APPOINTMENT CANCEL` y `RESCHEDULE` solo recepción/admin; `CHANGE_STATUS` con odontólogo `OWN`; `APPOINTMENT_HISTORY READ` con odontólogo `OWN`. |
| `AppointmentStatusChangeRepository.list_by_appointment_id` | `backend/app/repositories/appointment.py:162` | Devuelve las entradas ordenadas por `(changed_at, id)` y reconstruye `RescheduleDetail`. |
| `AppointmentRepository.get_by_id` | `backend/app/repositories/appointment.py:130` | Devuelve el turno o `None`; sirve para el `404` y para comparar propiedad en el historial. |
| `UserRepository.get_by_id` | `backend/app/repositories/users.py:47` | Devuelve `display_name`; sirve para el nombre visible de `changedBy`. |
| `UserRepository` / `AuthenticatedUser` | `backend/app/auth/model.py:7` y `backend/app/repositories/users.py:21` | El `Actor` sale del JWT; `display_name` no se expone en ninguna ruta todavía. |
| `DomainRejectedError`, `NotFoundError`, manejadores | `backend/app/api/errors.py` | Traducen rechazos y `404` con el cuerpo unificado; precedencia `403` → `422` → `409`. |
| `VIOLATION_STATUS_MAP` | `backend/app/api/errors.py:11` | `INVALID_TRANSITION` y `STATUS_CHANGE_TOO_EARLY` → `422`; choques, bloqueo y fuera de horario → `409`; `FORBIDDEN_OPERATION` → `403`. |
| `protected_router`, `require_permission` | `backend/app/api/deps.py:60` y `:77` | Autenticación y autorización por celda de la matriz. |
| `Settings.app_timezone` | `backend/app/config.py:26` | Zona configurada (`America/Argentina/Buenos_Aires`). |
| `datetime.now(UTC)` en el borde | `backend/app/api/auth.py:67` y `docs/evidencias/explore-C-22.md` D4 | Precedente del proyecto para el reloj. |
| Harness de integración | `backend/tests/integration/conftest.py`, `auth_support.py` | PostgreSQL real, usuarios y tokens reales, limpieza con `clean_database_tables`; sin mocks ni `dependency_overrides`. |
| Concurrencia de C-17 | `backend/tests/integration/test_appointment_concurrency.py` | Cancelar vs. confirmar el mismo turno con dos conexiones reales, `pg_locks` y `SET lock_timeout`. |

### 2.2. Qué recibe, qué devuelve y qué le falta a cada servicio para usarse desde la API

Los tres servicios comparten la misma forma: **el llamador ya autorizó**; ellos no reciben permisos ni `Actor` para autorizar, solo el `Actor` para la autoría y las reglas de propiedad. Todos aceptan `auto_commit=True` y son los dueños de la transacción: hacen `commit` en `Ok`, `rollback` en `Rejected` y `rollback` ante excepción.

| Servicio | Recibe | Devuelve | `None` |
|----------|--------|----------|--------|
| `change_appointment_status` | `session`, `appointment_id`, `target_status: AppointmentStatus`, `actor`, `now`, `tz`, `auto_commit=True` | `ValidationResult`: `Ok(appointment, status_change)` o `Rejected(violations)` | **Sí**: si el turno no existe. |
| `cancel_appointment` | `session`, `appointment_id`, `actor`, `now`, `tz`, `auto_commit=True` | `ValidationResult`; el destino es siempre `cancelado` | **Sí**: si el turno no existe. |
| `reschedule_appointment` | `session`, `appointment_id`, `request: RescheduleRequest`, `actor`, `now`, `tz`, `auto_commit=True` | `ValidationResult`; `Ok` trae el turno en `reservado` con el mismo id y `status_change.reschedule` | **Sí**: si el turno no existe. |

En `Ok`, el turno y la entrada de historial ya quedaron persistidos y el `commit` ya se hizo. En `Rejected`, el servicio ya hizo `rollback` y el historial no creció. La ruta no debe volver a hacer `commit` ni `rollback`.

**Qué les falta para usarse desde la API**:

1. Las cuatro rutas bajo `protected_router`, con `require_permission` de la celda correcta.
2. Esquemas Pydantic en camelCase con `extra="forbid"`: cuerpo de `status`, cuerpo de `reschedule`, respuesta de turno y respuesta de historial.
3. En `status`: mapear el `toStatus` del cuerpo a `AppointmentStatus` **solo** para `confirmado`, `atendido` y `ausente`. No se puede mandar `cancelado` al servicio: el dominio lanza `ValueError` y sería un `500` (ver D3).
4. En `reschedule`: construir `RescheduleRequest` con `start_at` del cuerpo y dejar `None` en profesional, sillón y duración cuando no se mandan.
5. Inyectar `now = datetime.now(UTC)` y `tz = ZoneInfo(settings.app_timezone)` una vez por request en las tres mutaciones.
6. Convertir el `None` de los servicios en `NotFoundError("Turno no encontrado.")`.
7. Convertir `Rejected` en `DomainRejectedError` y reutilizar el manejador global.
8. Serializar el turno aceptado con el mismo `AppointmentResponse` de C-22.
9. Agregar una lectura de historial (servicio o router) que primero cargue el turno para distinguir `404` de lista vacía, y que resuelva el nombre visible de `changedBy`.
10. Tests de integración y documentación OpenAPI de cada ruta.

### 2.3. Observaciones que condicionan el diseño

- **El dominio sí decide la propiedad en `CHANGE_STATUS`**: `transitions.py:81` compara `actor.professional_id` con `appointment.professional_id` y devuelve `FORBIDDEN_OPERATION` **solo** para el odontólogo. La API no debe repetir esa comparación (D5).
- **El dominio no decide la propiedad en el historial**: `AppointmentStatusChange` no guarda el profesional del turno y no hay regla que compare al actor. La API tiene que cargar el turno y comparar `professional_id` (D6).
- **Cancelar y reprogramar los rechaza la matriz antes que el dominio**: el odontólogo no tiene entrada en `CANCEL` ni `RESCHEDULE`, así que el `403` de la ruta es el genérico de `PERMISSION_MESSAGES` (`"No tiene permiso para cancelar turnos."` / `"No tiene permiso para reprogramar turnos."`). El `403` detallado del dominio para esas operaciones queda inalcanzable desde la API, pero sigue siendo la red de seguridad del servicio.
- **`change_status` con `target=CANCELLED` lanza `ValueError`** (`transitions.py:79`): es una guarda de programación, no una violación. El esquema debe impedir que `cancelado` llegue al servicio.
- **Las transiciones al mismo estado son inválidas**: `INVALID_TRANSITION`, no idempotencia (spec `appointment-lifecycle`). Repetir una cancelación o un estado terminal devuelve `422`, no `200`.
- **La reprogramación usa la duración real del turno original** cuando no se manda `durationMin` (`reschedule.py:116-118`), no la duración por defecto de la prestación.
- **El historial ya está ordenado por `(changed_at, id)`** en el repositorio; incluye la entrada inicial del alta (`from_status = None`).
- **`changed_by` es el `user_id` del `Actor`**, no el `professional_id`; el nombre visible está en `app_user.display_name` y no hay endpoint de usuarios que el front pueda usar.
- **No hay soporte de `note`** en el dominio ni en los servicios: `AppointmentStatusChangeModel.note` existe y siempre se guarda `None`. El Flujo 2 de la KB habla de "intervalo anterior en note", pero C-17 lo persistió en las 8 columnas de `reschedule_*`.
- **C-21 puede aportar el helper de propiedad** (`ensure_own_professional`) según su D3; a la fecha de este explore no está en HEAD. C-23 no declara a C-21 como dependencia formal, pero lo necesita para no duplicar la comparación del historial.

---

## 3. Decisiones de diseño (`D1`–`D18`)

### D1 — Endpoints, rutas y RBAC

**Problema**: definir las cuatro rutas, colgarlas del guardián correcto y asignarles la celda de la matriz.

| # | Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores posibles |
|---|--------|------|------------------|------------|-----------|-------|-------|------------------|
| 1 | `POST` | `/api/appointments/{id}/cancel` | `APPOINTMENT` / `CANCEL` | — (`403`) | todos | todos | `200` | `400`, `401`, `403`, `404`, `422` |
| 2 | `POST` | `/api/appointments/{id}/reschedule` | `APPOINTMENT` / `RESCHEDULE` | — (`403`) | todos | todos | `200` | `400`, `401`, `403`, `404`, `409`, `422` |
| 3 | `POST` | `/api/appointments/{id}/status` | `APPOINTMENT` / `CHANGE_STATUS` | propios (decide el dominio) | todos | todos | `200` | `400`, `401`, `403`, `404`, `422` |
| 4 | `GET` | `/api/appointments/{id}/history` | `APPOINTMENT_HISTORY` / `READ` | propios (decide la API) | todos | todos | `200` | `400`, `401`, `403`, `404` |

- **Opción A (recomendada)**: las cuatro rutas, con las acciones de la matriz tal cual, en `backend/app/api/appointments.py` (el mismo router que crea C-22). `cancel` no lleva cuerpo; `status` y `reschedule` sí. El `400` cubre UUID de ruta inválido y cuerpos malformados.
- **Opción B**: unificar cancelar dentro de `POST /status` aceptando `cancelado`. Contradice el scope de `CHANGES.md`, mezcla dos permisos (`CANCEL` vs `CHANGE_STATUS`) y le daría al odontólogo la posibilidad de cancelar sus propios turnos, que la KB prohíbe.
- **Opción C**: usar `PATCH /api/appointments/{id}` para todo. Obliga a decidir por cuerpo qué regla aplicar y pierde la trazabilidad de permisos por acción; además se aparta de las rutas que fijan KB 07 y `CHANGES.md`.
- **Recomendación**: **A**. Respeta el scope, la matriz de C-19 y los Flujos 2 y 3 de KB 07. El guardián `test_route_guards.py` debe seguir pasando sin modificarlo.

### D2 — Turno inexistente en la ruta: `404 NOT_FOUND`

**Problema**: los tres servicios devuelven `None` si el `appointment_id` no existe; hay que traducirlo.

- **Opción A (recomendada)**: si el servicio devuelve `None`, la ruta lanza `NotFoundError("Turno no encontrado.")`. El manejador global responde `404` con `{ "code": "NOT_FOUND", "message": "Turno no encontrado." }`. En `GET /history` se carga el turno primero con `AppointmentRepository.get_by_id`; si es `None`, el mismo `404`.
- **Opción B**: `422 UNKNOWN_REFERENCE`. Es el código de C-22 para referencias del **cuerpo**, no para el recurso de la **ruta**; además confundiría un turno inexistente con una referencia inválida del pedido.
- **Opción C**: devolver `200` con lista vacía o un turno ficticio. Oculta el error y rompe el contrato de C-20 y C-21.
- **Recomendación**: **A**. Es el mismo patrón de C-20 (`NotFoundError`) y C-21 (`"Profesional no encontrado."`, `"Bloqueo no encontrado."`), y el mensaje queda en español.

### D3 — Cuerpo de `POST /status`: solo `confirmado`, `atendido` y `ausente`

**Problema**: el endpoint de estado no debe permitir cancelar ni volver a `reservado`, y el dominio lanza `ValueError` si recibe `cancelado` como target.

- **Opción A (recomendada)**: el cuerpo es `{ "toStatus": "confirmado" | "atendido" | "ausente" }`, con un enum/literal propio del esquema y `extra="forbid"`. `"cancelado"` y `"reservado"` (y cualquier otro valor) se rechazan con `400` en el esquema, antes de tocar el dominio. Cancelar tiene su propia ruta.
  - *Pros*: evita el `500` de `ValueError`; el contrato es explícito; el `400` distingue "no es un estado de esta operación" de "la transición no es válida".
  - *Contras*: el cliente no recibe `422 INVALID_TRANSITION` para `"reservado"`, aunque el dominio también lo rechazaría; es una diferencia de capa deliberada.
- **Opción B**: aceptar el enum completo `AppointmentStatus` y dejar que el dominio decida. `"cancelado"` produce `ValueError` → `500`; `"reservado"` produce `422 INVALID_TRANSITION`. Inconsistente y con un `500` evitable.
- **Opción C**: aceptar strings libres y mapear a mano en la ruta. Duplica la validación, pierde el `400` automático y es fácil de olvidar.
- **Recomendación**: **A**. El `400` por esquema es el lugar correcto para "este endpoint no acepta ese estado"; el `422 INVALID_TRANSITION` queda reservado a estados permitidos por el esquema pero inválidos para el turno actual (por ejemplo, `confirmado` sobre un turno `atendido`). Si la autora prefiere que `"reservado"` dé `422`, se puede aceptar el enum completo y traducir `"cancelado"` a `400` antes de llamar al servicio; no se recomienda porque agranda la superficie de error.

### D4 — `note` en los cuerpos de `status`, `cancel` y `reschedule`

**Problema**: KB 07 Flujo 3 muestra `{ toStatus, note? }` y el Flujo 2 dice "intervalo anterior en note"; sin embargo, el dominio cerrado no modela `note` y los servicios guardan `note=None`.

- **Opción A (recomendada)**: no aceptar `note` en C-23. El esquema usa `extra="forbid"`, así que mandarlo da `400`. El detalle de reprogramación ya se persiste en las columnas `reschedule_*` y se expone en `GET /history`.
- **Opción B**: aceptar `note` y persistirlo. Requiere extender `AppointmentStatusChange` (C-12), los servicios (C-17) y los esquemas; es un cambio de dominio/persistencia fuera del scope de C-23 y con impacto en los tests cerrados.
- **Opción C**: aceptar `note` y descartarlo en silencio. Es el peor: el cliente cree que quedó registrado y no queda.
- **Recomendación**: **A**. C-23 expone lo que C-12/C-17 ya modelan. El `note` puede sumarse en un change posterior si la autora lo considera necesario; que el Flujo 2 hable de `note` se resuelve con el detalle tipado `reschedule` que ya existe.

### D5 — `CHANGE_STATUS` del odontólogo: el `403` por turno ajeno lo produce el dominio

**Problema**: la fila `APPOINTMENT CHANGE_STATUS` le da al odontólogo `Scope.OWN`, pero el comentario de `permissions.py:45-46` dice que `OWN` significa "dejar pasar y que decida el dominio". Hay que confirmar que la API no duplica la comparación.

- **Opción A (recomendada)**: la ruta solo ejecuta `require_permission(APPOINTMENT, CHANGE_STATUS)` y pasa el `Actor` al servicio. El dominio (`transitions.py:81-89`) compara `actor.professional_id` con `appointment.professional_id` y devuelve `FORBIDDEN_OPERATION` con el mensaje detallado ("un odontólogo solo puede cambiar el estado de sus propios turnos."). La ruta no mira `professional_id`.
  - *Pros*: una sola fuente de verdad; el mensaje del dominio describe el turno; el test de `403` por propiedad prueba el dominio a través de la API.
  - *Contras*: el `403` del turno ajeno no viene del helper de C-21, así que hay que probarlo por separado.
- **Opción B**: aplicar también `ensure_own_professional` en la ruta. Duplica la comparación y, peor, devuelve el mensaje genérico de la matriz antes de que el dominio dé el mensaje específico; el test dejaría de probar la regla de dominio.
- **Opción C**: quitar `Scope.OWN` de la matriz y dejar la fila en `ALL`. Contradice C-19 y la KB 03.
- **Recomendación**: **A**. Es exactamente lo que el comentario de la matriz declara. El orden esperado es `401` → `403` por rol (matriz) → `404` si el turno no existe → `403` por propiedad (dominio). Para un turno ajeno en estado terminal, gana el `403` de permiso, no el `422` de transición, porque el dominio evalúa permiso primero.

### D6 — Historial del odontólogo: la API compara el `professional_id` y reutiliza el helper de C-21

**Problema**: el dominio no decide la propiedad del historial y `GET /history` no recibe un `professional_id` de ruta. Sin una comparación en la API, un odontólogo podría leer el historial de turnos ajenos.

- **Opción A (recomendada)**: después de cargar el turno, si `permission.scope is Scope.OWN`, llamar al helper de C-21 (`ensure_own_professional(permission, appointment.professional_id)`) o a su versión compartida en `backend/app/api/ownership.py`. Si el `professional_id` no coincide con el del `Actor`, lanza el `403` de la celda con `FORBIDDEN_OPERATION` y el mensaje `"No tiene permiso para leer el historial de turnos."`. Recepción y administración tienen `Scope.ALL` y no se comparan.
  - *Pros*: reutiliza una sola definición de "solo lo propio"; el mensaje es el de la matriz; el test de `403` por propiedad es directo.
  - *Contras*: C-21 no es dependencia formal de C-23; hay que coordinar que el helper esté archivado o extraerlo a un módulo común.
- **Opción B**: repetir la comparación inline en la ruta del historial. Duplica el helper, pero es aceptable si C-21 todavía no está archivado; no se recomienda a largo plazo.
- **Opción C**: agregar una regla de dominio que reciba el historial y el `Actor`. Requiere un cambio de dominio nuevo (C-12 ya cerró el modelo) y no aporta: el historial no tiene el `professional_id` del turno, habría que pasarlo igual.
- **Recomendación**: **A**, con la salvedad de coordinación. Orden: `401` → `403` por rol → `404` si el turno no existe → `403` por propiedad. Es el mismo orden de C-21 D3. El `404` antes del `403` de propiedad revela que el turno existe, pero solo a un odontólogo autenticado y sin devolver datos; se acepta por consistencia (ver riesgos).

### D7 — El historial se autoriza con `APPOINTMENT_HISTORY READ`, no con `APPOINTMENT READ`

**Problema**: la matriz tiene una fila propia para el historial, pero `APPOINTMENT` no tiene una acción `READ` (solo `READ_AGENDA`).

- **Opción A (recomendada)**: `require_permission(APPOINTMENT_HISTORY, READ)`. La carga del turno para el `404` y la comparación de propiedad es interna y no exige otra celda.
- **Opción B**: usar `APPOINTMENT READ_AGENDA`. Es para la agenda (C-24), no para el historial, y le daría al odontólogo el alcance de agenda (todos) en vez de "solo los propios".
- **Opción C**: exigir las dos celdas. Agrega una dependencia que la matriz no pide y complica el test de `403`.
- **Recomendación**: **A**. Es la fila 6 de la KB 03 y la de C-19; el historial es un recurso propio en la matriz.

### D8 — Cuerpo de `POST /reschedule` y valores por defecto

**Problema**: definir qué manda el cliente y qué conserva el servidor.

- **Opción A (recomendada)**:
  - Cuerpo: `{ "startAt": "...", "professionalId?": "...", "chairId?": "...", "durationMin?": 30 }`.
  - `startAt` es ISO 8601 **con zona obligatoria**; sin offset se rechaza con `400` en el esquema, antes del `ValueError` del dominio.
  - `professionalId`, `chairId` y `durationMin` son opcionales. Si faltan, se deja `None` en `RescheduleRequest` y el dominio conserva el profesional, el sillón y la **duración real actual** del turno (`end_at - start_at`), no la duración por defecto de la prestación.
  - El paciente y la prestación no se cambian nunca; el id del turno no se manda en el cuerpo (viene en la ruta).
  - `extra="forbid"`: mandar `patientId`, `serviceId`, `status` o `changedBy` da `400`.
- **Opción B**: exigir `professionalId`, `chairId` y `durationMin` siempre. Es más explícito, pero obliga al front a releer y reenviar valores que no quiere cambiar, y contradice `RescheduleRequest`, que ya define `None` como "conservar".
- **Opción C**: aceptar solo `startAt` y no permitir cambiar profesional ni sillón. Pierde US-031 CA-1 ("mover a otro horario, profesional o sillón") y la capacidad que C-11 ya implementó.
- **Recomendación**: **A**. Es el contrato del Flujo 2 y de `RescheduleRequest`. Además, reenviar la duración actual explícitamente no cambia el resultado, pero dejarla en `None` evita que el front tenga que calcularla.

### D9 — Mapeo de los rechazos de `POST /reschedule`

**Problema**: la reprogramación puede fallar por muchas reglas distintas; hay que decidir el status de cada una.

- **Opción A (recomendada)**: si el servicio devuelve `Rejected`, la ruta lanza `DomainRejectedError` y el manejador global aplica la tabla de `api-foundation` con la precedencia `403` → `422` → `409`. Casos:
  - **Choques**: `PROFESSIONAL_OVERLAP` y/o `CHAIR_OVERLAP` → `409` con todas las violaciones.
  - **Agenda**: `OUTSIDE_WORKING_HOURS` o `BLOCKED_TIME` → `409`.
  - **Pasado**: `IN_THE_PAST` → `422`.
  - **Validez**: `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT` → `422`.
  - **Referencias del cuerpo**: `UNKNOWN_REFERENCE` (profesional o sillón inexistente) o `INACTIVE_REFERENCE` → `422`, no `404`; el id del turno de la ruta es el único que produce `404`.
  - **Estado**: `INVALID_TRANSITION` (turno terminal) → `422`.
  - **Permiso**: `FORBIDDEN_OPERATION` → `403` (en la API, el odontólogo ya fue rechazado por la matriz antes de llegar al dominio).
- **Opción B**: traducir código por código en la ruta. Duplica `VIOLATION_STATUS_MAP`, se desactualiza y puede perder violaciones.
- **Opción C**: devolver `409` para todo lo que no sea `404`/`403`. Convierte un turno en el pasado o una duración inválida en un conflicto de agenda; contradice KB 07 y la spec.
- **Recomendación**: **A**. Es el mismo patrón de C-22 D5 y conserva todas las violaciones en el orden del dominio. El servicio ya hizo `rollback` antes de devolver el `Rejected`.

### D10 — Respuesta de las mutaciones: solo el turno actualizado

**Problema**: decidir si cancelar, cambiar estado y reprogramar devuelven solo el turno o también la entrada de historial nueva.

- **Opción A (recomendada)**: las tres devuelven `200` con el mismo `AppointmentResponse` de C-22: `id`, `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt`, `endAt` y `status`, en camelCase y con instantes en UTC (`Z`). La entrada de historial se verifica en el test y se lee por `GET /history`.
  - *Pros*: contrato uniforme con C-22; el front actualiza el turno sin tener que entender el historial; no expone `changedBy` en una respuesta de mutación.
  - *Contras*: el cliente que quiere mostrar "quién lo cambió" hace una segunda consulta; es aceptable porque el historial es otra vista.
- **Opción B**: devolver `{ "appointment": {...}, "historyEntry": {...} }`. Ahorra una consulta, pero duplica la forma del historial en dos respuestas y obliga a definirla ahora en todas las mutaciones.
- **Opción C**: `204 No Content`. El front tendría que volver a consultar el turno (y no hay `GET /api/appointments/{id}` todavía).
- **Recomendación**: **A**. Mantiene la coherencia con C-22 D3 y deja el historial como un recurso de lectura independiente. En reprogramación, el turno devuelto ya trae el nuevo profesional, sillón, inicio y fin, y el estado `reservado`.

### D11 — Forma de cada entrada de `GET /history`

**Problema**: definir el contrato de lectura del historial, incluida la entrada inicial y el detalle de reprogramación.

- **Opción A (recomendada)**: lista de entradas planas en camelCase:
  ```json
  [
    {
      "from": null,
      "to": "reservado",
      "changedBy": "…uuid del usuario…",
      "changedByName": "Usuario Ficticio recepcion",
      "changedAt": "2026-11-06T21:00:00Z",
      "reschedule": null
    },
    {
      "from": "reservado",
      "to": "confirmado",
      "changedBy": "…uuid del usuario…",
      "changedByName": "Usuario Ficticio recepcion",
      "changedAt": "2026-11-06T21:05:00Z",
      "reschedule": {
        "previousStartAt": "2026-11-16T13:00:00Z",
        "previousEndAt": "2026-11-16T13:30:00Z",
        "newStartAt": "2026-11-16T14:00:00Z",
        "newEndAt": "2026-11-16T14:30:00Z",
        "previousProfessionalId": "…",
        "newProfessionalId": "…",
        "previousChairId": "…",
        "newChairId": "…"
      }
    }
  ]
  ```
  - `from` es `null` **solo** en la entrada inicial del alta; se incluye siempre para no confundir "no había estado" con "campo ausente".
  - `to` es el estado nuevo.
  - `changedBy` es el `user_id` del `Actor`; `changedAt` está en UTC con `Z`.
  - `reschedule` aparece con el detalle cuando la entrada viene de una reprogramación; en las demás se puede omitir o enviar `null` (recomendado: omitirlo para no ensuciar; `from` sí se mantiene aunque sea `null`).
- **Opción B**: anidar el detalle como `{ "previous": { "startAt", "endAt", "professionalId", "chairId" }, "new": { ... } }`. Es más legible, pero se aparta de las columnas planas y de la forma de `AppointmentResponse`.
- **Opción C**: devolver la fila cruda de la base con nombres de columnas (`from_status`, `changed_by`, etc.). Rompe el camelCase de la API y expone detalles de persistencia.
- **Recomendación**: **A**. La forma plana es la más simple de consumir y de testear; el detalle de reprogramación se mapea 1:1 desde `RescheduleDetail`. La entrada inicial se incluye porque es parte de la trazabilidad de US-033.

### D12 — `changedByName`: nombre visible del usuario que hizo el cambio

**Problema**: `changedBy` es un UUID y no hay endpoint de usuarios; sin un nombre, la vista de administración no puede cumplir "ver quién cambió qué".

- **Opción A (recomendada)**: agregar `changedByName` con `app_user.display_name`. Se resuelve con una consulta por los ids únicos de las entradas (por ejemplo, un método de lectura `UserRepository.get_display_names(ids)`), no una consulta por entrada. Si un usuario no existe (no debería ocurrir en el MVP), el campo queda `null` o se omite.
  - *Pros*: cumple US-033 sin abrir un ABM de usuarios; no expone hash ni credenciales; el front no tiene que resolver ids.
  - *Contras*: agrega una lectura y un campo más al contrato; los nombres de usuarios internos quedan visibles para odontólogos con historial propio, recepción y administración.
- **Opción B**: devolver solo `changedBy` (UUID). Es el contrato mínimo, pero el front no puede mostrar un nombre y la KB 03 no tiene ruta de usuarios.
- **Opción C**: devolver `changedBy` como objeto `{ "id", "displayName" }`. Es claro, pero cambia la forma plana y obliga a un nested que el resto de la API no usa.
- **Recomendación**: **A**. Es una lectura interna, sin endpoint nuevo, y resuelve la trazabilidad visible de US-033. Si la autora prefiere el contrato mínimo, se puede quitar `changedByName` sin tocar el resto; el front mostraría el UUID o el nombre que ya tenga en sesión, que no cubre a los demás usuarios.

### D13 — Orden del historial

**Problema**: definir la dirección de la lista.

- **Opción A (recomendada)**: orden **ascendente** por `(changedAt, id)`, tal como ya lo devuelve `AppointmentStatusHistoryRepository.list_by_appointment_id`. La primera entrada es el alta y la última es el cambio más reciente. El `id` es el desempate estable.
- **Opción B**: descendente (más reciente primero). Es común en una auditoría, pero obliga a invertir la consulta o la lista y se aparta del repositorio ya probado.
- **Opción C**: sin orden garantizado. El test de "historial ordenado" de C-23 quedaría indefinido.
- **Recomendación**: **A**. El repositorio ya lo garantiza y el test puede afirmar la secuencia completa (alta → confirmado → reprogramado → cancelado). Si la UI prefiere lo más reciente arriba, lo invierte en el cliente.

### D14 — Origen de `now` y de la zona horaria

**Problema**: el dominio exige `now` y `tz` inyectados; la API tiene que obtenerlos sin romper la reproducibilidad.

- **Opción A (recomendada)**: el router calcula `now = datetime.now(UTC)` una vez por request y `tz = ZoneInfo(settings.app_timezone)`, y los pasa a `change_appointment_status`, `cancel_appointment` o `reschedule_appointment`. El mismo `now` se usa para la regla del pasado, `STATUS_CHANGE_TOO_EARLY` y `changed_at` del historial. `GET /history` no necesita `now`.
- **Opción B**: que el servicio llame a `datetime.now()` por dentro. Viola la regla dura del proyecto y hace que los tests dependan del reloj.
- **Opción C**: inyectar un proveedor de reloj o una dependencia FastAPI reemplazable en tests. Agrega indirección y empuja a `dependency_overrides`, que C-19 y C-21 prohíben; además C-22 ya fijó el patrón de `datetime.now(UTC)` en el borde.
- **Recomendación**: **A**. `ZoneInfo` es barato y se puede construir por request o una vez al arrancar; la interfaz de los servicios no cambia. El reloj no se toma del cliente ni de un header.

### D15 — Tests de `atendido` y `ausente` con el reloj real, sin `monkeypatch` ni overrides

**Problema**: `atendido` y `ausente` exigen `now >= appointment.start_at`; la API no deja crear turnos en el pasado, así que un test que solo use `POST /api/appointments` no puede llegar a esas transiciones.

- **Opción A (recomendada)**: insertar el turno **directamente en la base de test** con un `start_at` ya pasado (por ejemplo, `now - 30 min`), estado `reservado` o `confirmado`, FKs válidas (paciente, profesional, sillón y prestación existentes) y `created_at = updated_at` coherentes. Opcionalmente insertar también su entrada inicial de historial para que el historial sea completo. Después, llamar a `POST /status` con el reloj real; como `now >= start_at`, la transición es válida. Para el caso `STATUS_CHANGE_TOO_EARLY`, usar un turno con `start_at` futuro (creado por la API o directo) y pedir `atendido`.
  - *Pros*: prueba el cableado real del borde y la regla del reloj; no reemplaza el reloj; usa el mismo PostgreSQL y las mismas constraints.
  - *Contras*: el turno de prueba no pasó por `book_appointment`; hay que respetar `ck_appointment_interval_order` y las FKs, y limpiar con `clean_database_tables`.
- **Opción B**: crear un turno futuro por la API y luego `UPDATE appointment SET start_at = now - ...` en la base. También sirve, pero deja el historial inicial con un intervalo anterior distinto al actual y puede confundir las aserciones; la inserción directa es más limpia.
- **Opción C**: `monkeypatch`, `unittest.mock` o `dependency_overrides` para fijar el reloj. Prohibido por las reglas de tests de C-19 y C-21, y no probaría el `datetime.now(UTC)` real del borde.
- **Recomendación**: **A**. Los tests de integración pueden usar `test_engine` para la inserción directa y luego el `TestClient` con tokens reales; no se fija el reloj. Los tests de dominio siguen usando fechas fijas porque reciben `now` por parámetro.

### D16 — Tests de concurrencia: alcanzan los de C-17

**Problema**: decidir si C-23 necesita una prueba de concurrencia nueva a nivel HTTP.

- **Opción A (recomendada)**: los tests de concurrencia de C-17 (`test_appointment_concurrency.py`) ya prueban el `SELECT ... FOR UPDATE` y la relectura del estado con dos conexiones reales, `pg_locks` y `SET lock_timeout`. C-23 solo agrega rutas que llaman a esos mismos servicios, así que la serialización real sigue cubierta. Se agrega, sí, un test **secuencial** de "doble transición" a nivel API: la primera operación responde `200`, la segunda responde `422 INVALID_TRANSITION` y en la base queda **una sola** entrada nueva de historial. Eso prueba el cableado de la ruta, no la concurrencia.
- **Opción B**: agregar un test HTTP de dos transiciones simultáneas con barrera. Con `TestClient` las peticiones pueden ejecutarse en serie; no demuestra concurrencia real y sería más frágil que el test de C-17.
- **Opción C**: no agregar ningún test de ruta y confiar solo en C-17. No alcanza para el criterio de C-23: no prueba el `None` → `404`, el mapeo de estados, el `403` de propiedad ni el historial por HTTP.
- **Recomendación**: **A**. La prueba real de concurrencia es la de C-17; C-23 suma el test secuencial de doble transición y los tests de contrato de cada ruta.

### D17 — Organización del código y transacción

**Problema**: dónde viven las rutas, los esquemas y la lectura del historial, y quién confirma.

- **Opción A (recomendada)**: `backend/app/api/appointments.py` (el mismo router de C-22) con las cuatro rutas; esquemas en `backend/app/api/schemas.py` (`StatusChangeInput`, `RescheduleInput`, `AppointmentResponse` reutilizado, `HistoryEntryResponse`, `RescheduleDetailResponse`); una función de servicio `get_appointment_history(session, appointment_id)` en `backend/app/services/appointments.py` (o un módulo de lectura) que cargue el turno, devuelva `None` si no existe y arme las entradas con el nombre visible. La ruta no hace `commit` ni `rollback`: los servicios de mutación ya son dueños de la transacción.
- **Opción B**: un módulo nuevo `services/lifecycle.py` que envuelva a los servicios de C-17. Agrega una capa sin lógica propia; C-17 ya es el caso de uso y la ruta puede llamarlo directo.
- **Opción C**: leer historial directo desde el router con los repositorios. Es aceptable para una lectura, pero deja el `404` y la resolución de nombres en la capa HTTP; el servicio mantiene la API delgada y testeable.
- **Recomendación**: **A**. Reutiliza C-17 y C-22, mantiene el patrón de C-20 (servicios con commit, routers delgados) y deja la única lógica nueva (historial + nombres) en un servicio de lectura.

### D18 — Documentación OpenAPI de las cuatro rutas

**Problema**: las rutas nuevas deben documentar sus errores y seguir los guardianes de C-18/C-19.

- **Opción A (recomendada)**: en cada ruta, `response_model`, `status_code=200`, tag "Turnos" y `responses` con:
  - `not_found_responses("Turno")` en las cuatro.
  - `permission_responses()` en las cuatro (403 por rol; en `status` y `history` también el 403 por propiedad).
  - `violation_responses(422)` en `cancel`, `status` y `reschedule`.
  - `violation_responses(409)` en `reschedule` (choques, bloqueo, fuera de horario).
  - `400` y `401` los agrega `setup_openapi` automáticamente.
- **Opción B**: dejar solo los modelos por defecto de FastAPI. Incumple `api-foundation`: las rutas que rechazan deben documentar sus status con el esquema de violaciones.
- **Opción C**: documentar solo `200` y `404`. El front no vería los códigos de rechazo y los guardianes de OpenAPI podrían fallar.
- **Recomendación**: **A**. Es coherente con C-20, C-21 y C-22, y verificable con los tests de OpenAPI existentes. En `history` no se documentan `409` ni `422` de dominio; sí `400`, `401`, `403` y `404`.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| C-22 todavía no está implementado (0/16) y C-23 lo necesita | El apply de C-23 empieza solo con C-22 archivado y verde (precondición, como C-22 con C-20). Este explore no toma archivos de C-22 a medio hacer como fuente de verdad. |
| C-21 está en implementación y su helper de propiedad podría no existir al aplicar C-23 | Coordinar: reutilizar `ensure_own_professional` si C-21 está archivado; si no, extraerlo a `backend/app/api/ownership.py` y que C-21 y C-23 lo importen, sin duplicar la comparación. |
| `"cancelado"` llega a `change_appointment_status` y el dominio lanza `ValueError` → `500` | El esquema de `status` solo acepta `confirmado`, `atendido` y `ausente` (D3); cancelar tiene su propia ruta. |
| La API duplica la comparación de propiedad en `CHANGE_STATUS` y tapa el mensaje del dominio | La ruta de estado no llama al helper; pasa el `Actor` y deja decidir al dominio (D5). |
| El odontólogo lee el historial de un turno ajeno | La API compara `appointment.professional_id` con el `Actor` cuando el scope es `OWN` (D6). |
| El `404` antes del `403` de propiedad en el historial revela que un turno existe | Se acepta por consistencia con C-21; solo lo ve un usuario autenticado y no se devuelven datos del turno. Si se prefiere ocultar la existencia, se invierte el orden, pero se aparta de C-21. |
| Reprogramar sin `durationMin` usa la duración por defecto de la prestación en vez de la real | La ruta deja `duration_min=None` y el dominio usa `end_at - start_at` del turno original (D8); test explícito. |
| Un test de `atendido`/`ausente` intenta crear el turno en el pasado por la API y recibe `422 IN_THE_PAST` | Insertar el turno directamente en la base de test con `start_at` pasado (D15). |
| Un test de concurrencia HTTP se interpreta como prueba de serialización real | C-17 es la prueba real con `pg_locks`; C-23 solo agrega el test secuencial de doble transición (D16). |
| `changedByName` genera N+1 consultas | Resolver los nombres de los ids únicos con una sola lectura (D12). |
| La respuesta de historial omite `from` en la entrada inicial por usar `exclude_none` | `from` se incluye siempre, con `null` solo en el alta; `reschedule` se omite cuando no existe (D11). |
| El contrato de `note` de la KB no se cumple | D4: C-23 no acepta `note`; el detalle de reprogramación ya está en `reschedule`. Documentar la diferencia y dejarlo para un change posterior. |
| Repetir una operación ya aplicada devuelve `200` por error | El dominio trata el mismo estado como `INVALID_TRANSITION`; la UI debe deshabilitar el botón mientras la petición está en vuelo (sin clave de idempotencia). |
| Las rutas nuevas no declaran permiso y el guardián las detecta | Montarlas en el router de C-22 bajo `protected_router` con `require_permission` y correr `test_route_guards.py`. |

### Preguntas para la autora

- **P1**: ¿Agregamos `changedByName` (display_name) a cada entrada del historial (D12)? Sugerencia: sí; sin endpoint de usuarios, es la única forma de mostrar "quién" en US-033.
- **P2**: ¿El historial incluye la entrada inicial del alta con `from: null` (D11, D13)? Sugerencia: sí; es parte de la trazabilidad y ya está persistida.
- **P3**: ¿El historial va ascendente (más viejo primero) o descendente (más reciente primero) (D13)? Sugerencia: ascendente, como ya lo devuelve el repositorio; la UI puede invertirlo.
- **P4**: ¿Aceptamos no soportar `note` en C-23 (D4)? Sugerencia: sí; el dominio cerrado no lo modela y el detalle de reprogramación ya está en `reschedule`. Si lo querés, se suma a un change posterior.
- **P5**: ¿El `404` del turno inexistente usa el mensaje `"Turno no encontrado."` (D2)? Sugerencia: sí, igual que C-20 y C-21.
- **P6**: ¿Reutilizamos el helper de propiedad de C-21 para el historial (D6)? Sugerencia: sí; si C-21 no está archivado, se extrae a un módulo común.
- **P7**: ¿El detalle de reprogramación va plano (`previousStartAt`, `newProfessionalId`, …) o anidado en `previous`/`new` (D11)? Sugerencia: plano, como el resto de la API.
- **P8**: ¿La respuesta de las mutaciones es solo el turno actualizado (D10)? Sugerencia: sí; el historial se lee por `GET /history`.
- **P9**: ¿Basta con los tests de concurrencia de C-17 más el test secuencial de doble transición (D16)? Sugerencia: sí; C-23 no cambia la lógica de locks.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

0. **Precondición**: C-20 archivado (ya está), C-21 archivado o helper de propiedad disponible, C-22 archivado y verde, C-17 verde. No tocar los archivos a medio hacer de C-21.
1. **Helper de propiedad**: reutilizar `ensure_own_professional` de C-21 o extraerlo a `backend/app/api/ownership.py`; tests de `403` por propiedad para el historial (D6, D7).
2. **Esquemas**: `StatusChangeInput` con enum `confirmado`/`atendido`/`ausente` y `extra="forbid"`; `RescheduleInput` con `startAt` con zona obligatoria, `professionalId?`, `chairId?`, `durationMin?` y `extra="forbid"`; `HistoryEntryResponse` y `RescheduleDetailResponse`; reutilizar `AppointmentResponse` de C-22 (D3, D8, D11, D12).
3. **Servicio de lectura de historial**: `get_appointment_history` que cargue el turno (para `404`), devuelva las entradas ordenadas y resuelva `changedByName` en una sola lectura de usuarios (D6, D11, D12, D13, D17).
4. **Rutas**: agregar `POST /cancel`, `POST /reschedule`, `POST /status` y `GET /history` en `backend/app/api/appointments.py`, con `require_permission`, `now`/`tz`, `None` → `NotFoundError`, `Rejected` → `DomainRejectedError` y serialización (D1, D2, D5, D9, D10, D14, D17).
5. **OpenAPI**: `response_model`, tags y `responses` de `400`, `401`, `403`, `404`, `409` y `422` según cada ruta; verificar los guardianes de rutas y de OpenAPI (D18).
6. **Tests de integración de mutaciones**: cancelar válido y desde terminal; cambiar a confirmado/atendido/ausente; `STATUS_CHANGE_TOO_EARLY`; transición inválida; `400` por `cancelado`/`reservado` en `status`; `404`; `403` por rol; `403` por propiedad en `status`; `400` por `startAt` sin zona y por campos extra; `422` por duración o referencias inválidas (D3, D8, D9, D15).
7. **Tests de reprogramación**: éxito con y sin profesional/sillón/duración; conserva la duración real; choque de profesional, de sillón y ambos; fuera de horario; bloqueo; pasado; estado terminal; `403` por rol; `404` (D8, D9).
8. **Tests de historial**: entrada inicial con `from: null`; orden ascendente; `changedByName`; detalle de reprogramación; `403` por propiedad; `404`; recepción/admin ven todo; lista vacía solo si el turno existe sin entradas (D11, D12, D13).
9. **Test secuencial de doble transición**: primera operación `200`, segunda `422 INVALID_TRANSITION`, una sola entrada nueva de historial; sin `time.sleep` (D16).
10. **Evidencias**: pytest de integración, mypy strict, guardianes de rutas/OpenAPI y `docs/evidencias/verify-C-23.md` con el formato de C-20/C-21/C-22. Si el proyecto lo mantiene, `mutaciones-C-23.py` y `trazabilidad-C-23.py`.
