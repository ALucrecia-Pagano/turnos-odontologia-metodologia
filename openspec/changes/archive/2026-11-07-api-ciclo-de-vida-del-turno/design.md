# Design — C-23 `api-ciclo-de-vida-del-turno`

## Context

Este change expone por HTTP el ciclo de vida del turno que C-17 ya implementa en los servicios `cancel_appointment`, `reschedule_appointment` y `change_appointment_status`, y que C-11/C-12 resolvieron en el dominio puro con historial inmutable. Parte de `docs/evidencias/explore-C-23.md`; las decisiones D1–D18 y las preguntas P1–P9 son las aprobadas por la autora, con las correcciones C1–C6 incorporadas en este documento.

Depende de C-11 (reprogramación de dominio), C-12 (historial persistido), C-17 (servicios transaccionales), C-19 (matriz RBAC y `require_permission`), C-21 (helper `ensure_own_professional`) y C-22 (router `api/appointments.py`, esquemas en camelCase, `AppointmentResponse` y patrón de tests con tokens reales). **C-21 y C-22 tienen que estar archivados antes de empezar el apply** (tarea 0.1), porque C-23 extiende el router y reutiliza el helper ya archivado. No se toma como fuente de verdad ningún archivo a medio hacer de esos changes.

## Goals / Non-Goals

**Goals**: exponer las cuatro rutas del ciclo de vida; autorizar por rol y por propiedad; inyectar `now` UTC y `APP_TIMEZONE`; reutilizar los servicios transaccionales de C-17; traducir `Rejected` a `409`/`422` y `None` a `404`; devolver el turno actualizado; exponer el historial ordenado con `changedByName` y el detalle plano de reprogramación; documentar y probar cada contrato.

**Non-Goals**: `GET /api/agenda` y listados (C-24); `GET /api/appointments/{id}` (fuera de C-22 y C-23); pantallas (C-25 en adelante); edición o borrado del historial; soporte de `note`; claves de idempotencia; cambios de dominio, migraciones, RBAC o Docker; concurrencia HTTP nueva (la prueba real sigue en C-17).

## Decisions

### D1 — Endpoints, rutas y RBAC

**Problema**: definir las cuatro rutas, colgarlas del guardián correcto y asignarles la celda de la matriz.

| # | Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores posibles |
|---|--------|------|------------------|------------|-----------|-------|-------|------------------|
| 1 | `POST` | `/api/appointments/{id}/cancel` | `APPOINTMENT` / `CANCEL` | — (`403`) | todos | todos | `200` | `400`, `401`, `403`, `404`, `422` |
| 2 | `POST` | `/api/appointments/{id}/reschedule` | `APPOINTMENT` / `RESCHEDULE` | — (`403`) | todos | todos | `200` | `400`, `401`, `403`, `404`, `409`, `422` |
| 3 | `POST` | `/api/appointments/{id}/status` | `APPOINTMENT` / `CHANGE_STATUS` | propios (decide el dominio) | todos | todos | `200` | `400`, `401`, `403`, `404`, `422` |
| 4 | `GET` | `/api/appointments/{id}/history` | `APPOINTMENT_HISTORY` / `READ` | propios (decide la API) | todos | todos | `200` | `400`, `401`, `403`, `404` |

- **Opción A (recomendada)**: las cuatro rutas en `backend/app/api/appointments.py` (el mismo router de C-22), con las acciones de la matriz tal cual. `cancel` no lleva cuerpo; `status` y `reschedule` sí. El `400` cubre UUID de ruta inválido y cuerpos malformados.
- **Opción B**: unificar cancelar dentro de `POST /status` aceptando `cancelado`. Mezcla dos permisos y le daría al odontólogo la posibilidad de cancelar sus propios turnos, que la KB prohíbe.
- **Opción C**: usar `PATCH /api/appointments/{id}` para todo. Obliga a decidir por cuerpo qué regla aplicar y pierde la trazabilidad de permisos por acción.
- **Decisión**: **A**. Respeta el scope de `CHANGES.md`, la matriz de C-19 y los Flujos 2 y 3 de KB 07. El guardián `test_route_guards.py` debe seguir pasando sin modificarlo.

### D2 — Turno inexistente en la ruta: `404 NOT_FOUND`

**Problema**: los tres servicios devuelven `None` si el `appointment_id` no existe; hay que traducirlo.

- **Opción A (recomendada)**: si el servicio devuelve `None`, la ruta lanza `NotFoundError("Turno no encontrado.")`. El manejador global responde `404` con `{ "code": "NOT_FOUND", "message": "Turno no encontrado." }`. En `GET /history` se carga el turno primero con `AppointmentRepository.get_by_id`; si es `None`, el mismo `404`.
- **Opción B**: `422 UNKNOWN_REFERENCE`. Es el código de C-22 para referencias del **cuerpo**, no para el recurso de la **ruta**.
- **Opción C**: devolver `200` con lista vacía o un turno ficticio. Oculta el error y rompe el contrato de C-20 y C-21.
- **Decisión**: **A**. Es el mismo patrón de C-20 y C-21, y el mensaje queda en español.

### D3 — Cuerpo de `POST /status`: solo `confirmado`, `atendido` y `ausente`

**Problema**: el endpoint de estado no debe permitir cancelar ni volver a `reservado`, y el dominio lanza `ValueError` si recibe `cancelado` como target.

- **Opción A (recomendada)**: el cuerpo es `{ "toStatus": "confirmado" | "atendido" | "ausente" }`, con un enum/literal propio del esquema y `extra="forbid"`. `"cancelado"`, `"reservado"` y cualquier otro valor se rechazan con `400` en el esquema, antes de tocar el dominio. Cancelar tiene su propia ruta.
- **Opción B**: aceptar el enum completo `AppointmentStatus` y dejar que el dominio decida. `"cancelado"` produce `ValueError` → `500`; `"reservado"` produce `422 INVALID_TRANSITION`. Inconsistente y con un `500` evitable.
- **Opción C**: aceptar strings libres y mapear a mano en la ruta. Duplica la validación, pierde el `400` automático y es fácil de olvidar.
- **Decisión**: **A**. El `400` por esquema es el lugar correcto para "este endpoint no acepta ese estado"; el `422 INVALID_TRANSITION` queda reservado a estados permitidos por el esquema pero inválidos para el turno actual.

### D4 — `note` en los cuerpos de `status`, `cancel` y `reschedule`

**Problema**: KB 07 Flujo 3 muestra `{ toStatus, note? }`, pero el dominio cerrado no modela `note` y los servicios guardan `note=None`.

- **Opción A (recomendada)**: no aceptar `note` en C-23. El esquema usa `extra="forbid"`, así que mandarlo da `400`. El detalle de reprogramación ya se persiste en las columnas `reschedule_*` y se expone en `GET /history`.
- **Opción B**: aceptar `note` y persistirlo. Requiere extender `AppointmentStatusChange` (C-12), los servicios (C-17) y los esquemas; es un cambio de dominio/persistencia fuera del scope de C-23.
- **Opción C**: aceptar `note` y descartarlo en silencio. El cliente cree que quedó registrado y no queda.
- **Decisión**: **A**. C-23 expone lo que C-12/C-17 ya modelan. El `note` puede sumarse en un change posterior.

### D5 — `CHANGE_STATUS` del odontólogo: el `403` por turno ajeno lo produce el dominio

**Problema**: la fila `APPOINTMENT CHANGE_STATUS` le da al odontólogo `Scope.OWN`, pero la matriz declara que en turnos `OWN` significa "dejar pasar y que decida el dominio".

- **Opción A (recomendada)**: la ruta solo ejecuta `require_permission(APPOINTMENT, CHANGE_STATUS)` y pasa el `Actor` al servicio. El dominio (`transitions.py:81-89`) compara `actor.professional_id` con `appointment.professional_id` y devuelve `FORBIDDEN_OPERATION` con el mensaje detallado. La ruta no mira `professional_id`.
- **Opción B**: aplicar también `ensure_own_professional` en la ruta. Duplica la comparación y devuelve el mensaje genérico de la matriz antes de que el dominio dé el mensaje específico.
- **Opción C**: quitar `Scope.OWN` de la matriz y dejar la fila en `ALL`. Contradice C-19 y la KB 03.
- **Decisión**: **A**. Orden esperado: `401` → `403` por rol (matriz) → `404` si el turno no existe → `403` por propiedad (dominio). Para un turno ajeno en estado terminal gana el `403` de permiso, no el `422` de transición, porque el dominio evalúa permiso primero.

### D6 — Historial del odontólogo: la API compara el `professional_id` y reutiliza el helper de C-21

**Problema**: el dominio no decide la propiedad del historial y `GET /history` no recibe un `professional_id` de ruta.

- **Opción A (recomendada)**: después de cargar el turno, si `permission.scope is Scope.OWN`, llamar a `ensure_own_professional(permission, appointment.professional_id)`, importado desde donde lo dejó C-21 (`backend/app/api/deps.py`). Si el `professional_id` no coincide con el del `Actor`, el helper lanza el `403` de la celda con `FORBIDDEN_OPERATION` y el mensaje `"No tiene permiso para leer el historial de turnos."`. Recepción y administración tienen `Scope.ALL` y no se comparan.
- **Opción B**: repetir la comparación inline en la ruta del historial. Duplica el helper y se desincroniza.
- **Opción C**: agregar una regla de dominio que reciba el historial y el `Actor`. Requiere un cambio de dominio nuevo y el historial no guarda el `professional_id` del turno.
- **Decisión**: **A**, **sin crear `backend/app/api/ownership.py`**: se importa directamente `ensure_own_professional` desde C-21 y no se duplica la comparación. Orden: `401` → `403` por rol → `404` si el turno no existe → `403` por propiedad. El `404` antes del `403` de propiedad revela que el turno existe, pero solo a un odontólogo autenticado y sin devolver datos; se acepta por consistencia con C-21.

### D7 — El historial se autoriza con `APPOINTMENT_HISTORY READ`, no con `APPOINTMENT READ`

**Problema**: la matriz tiene una fila propia para el historial, pero `APPOINTMENT` no tiene una acción `READ` (solo `READ_AGENDA`).

- **Opción A (recomendada)**: `require_permission(APPOINTMENT_HISTORY, READ)`. La carga del turno para el `404` y la comparación de propiedad es interna y no exige otra celda.
- **Opción B**: usar `APPOINTMENT READ_AGENDA`. Es para la agenda (C-24), no para el historial, y le daría al odontólogo el alcance de agenda (todos) en vez de "solo los propios".
- **Opción C**: exigir las dos celdas. Agrega una dependencia que la matriz no pide y complica el test de `403`.
- **Decisión**: **A**. Es la fila de la KB 03 y de C-19; el historial es un recurso propio en la matriz.

### D8 — Cuerpo de `POST /reschedule` y valores por defecto

**Problema**: definir qué manda el cliente y qué conserva el servidor.

- **Opción A (recomendada)**:
  - Cuerpo: `{ "startAt": "...", "professionalId?": "...", "chairId?": "...", "durationMin?": 30 }`.
  - `startAt` es ISO 8601 **con zona obligatoria**; sin offset se rechaza con `400` en el esquema, antes del `ValueError` del dominio.
  - `professionalId`, `chairId` y `durationMin` son opcionales. Si faltan, se deja `None` en `RescheduleRequest` y el dominio conserva el profesional, el sillón y la **duración real actual** del turno (`end_at - start_at`), no la duración por defecto de la prestación.
  - El paciente y la prestación no se cambian nunca; el id del turno no se manda en el cuerpo (viene en la ruta).
  - `extra="forbid"`: mandar `patientId`, `serviceId`, `status`, `changedBy` o `note` da `400`.
- **Opción B**: exigir `professionalId`, `chairId` y `durationMin` siempre. Obliga al front a releer y reenviar valores que no quiere cambiar y contradice `RescheduleRequest`, que ya define `None` como "conservar".
- **Opción C**: aceptar solo `startAt` y no permitir cambiar profesional ni sillón. Pierde US-031 CA-1 y la capacidad que C-11 ya implementó.
- **Decisión**: **A**. Es el contrato del Flujo 2 y de `RescheduleRequest`.

### D9 — Mapeo de los rechazos de `POST /reschedule`

**Problema**: la reprogramación puede fallar por muchas reglas distintas; hay que decidir el status de cada una.

- **Opción A (recomendada)**: si el servicio devuelve `Rejected`, la ruta lanza `DomainRejectedError` y el manejador global aplica la tabla de `api-foundation` con la precedencia `403` → `422` → `409`. Casos: `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` → `409`; `OUTSIDE_WORKING_HOURS` y `BLOCKED_TIME` → `409`; `IN_THE_PAST`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE` e `INVALID_TRANSITION` → `422`; `FORBIDDEN_OPERATION` → `403`.
- **Opción B**: traducir código por código en la ruta. Duplica `VIOLATION_STATUS_MAP`, se desactualiza y puede perder violaciones.
- **Opción C**: devolver `409` para todo lo que no sea `404`/`403`. Convierte un turno en el pasado o una duración inválida en un conflicto de agenda.
- **Decisión**: **A**. Es el mismo patrón de C-22 D5 y conserva todas las violaciones en el orden del dominio. El servicio ya hizo `rollback` antes de devolver el `Rejected`.

### D10 — Respuesta de las mutaciones: solo el turno actualizado

**Problema**: decidir si cancelar, cambiar estado y reprogramar devuelven solo el turno o también la entrada de historial nueva.

- **Opción A (recomendada)**: las tres devuelven `200` con el mismo `AppointmentResponse` de C-22 (`id`, `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt`, `endAt`, `status`) en camelCase y con instantes en UTC (`Z`). La entrada de historial se verifica en el test y se lee por `GET /history`.
- **Opción B**: devolver `{ "appointment": {...}, "historyEntry": {...} }`. Duplica la forma del historial en dos respuestas y obliga a definirla ahora en todas las mutaciones.
- **Opción C**: `204 No Content`. El front tendría que volver a consultar el turno y no hay `GET /api/appointments/{id}` todavía.
- **Decisión**: **A**. Mantiene la coherencia con C-22 D3 y deja el historial como un recurso de lectura independiente. En reprogramación, el turno devuelto trae el nuevo profesional, sillón, inicio y fin, y el estado `reservado`.

### D11 — Forma de cada entrada de `GET /history` (correcciones C1 y C2)

**Problema**: definir el contrato de lectura del historial, incluida la entrada inicial y el detalle de reprogramación.

- **Opción A (recomendada)**: lista de objetos planos en camelCase. `from` está **siempre** presente y es `null` solo en la entrada inicial del alta. `reschedule` está **siempre** presente: es el objeto plano de ocho campos cuando la entrada es una reprogramación y `null` cuando no. **Nada de `exclude_none`.** Una reprogramación **siempre** registra `to: "reservado"`, venga el turno de `reservado` o de `confirmado`:
  ```json
  [
    {
      "from": null,
      "to": "reservado",
      "changedBy": "00000000-0000-0000-0000-0000000000e2",
      "changedByName": "Recepción Demo",
      "changedAt": "2026-11-06T21:00:00Z",
      "reschedule": null
    },
    {
      "from": "reservado",
      "to": "confirmado",
      "changedBy": "00000000-0000-0000-0000-0000000000e2",
      "changedByName": "Recepción Demo",
      "changedAt": "2026-11-06T21:05:00Z",
      "reschedule": null
    },
    {
      "from": "confirmado",
      "to": "reservado",
      "changedBy": "00000000-0000-0000-0000-0000000000e2",
      "changedByName": "Recepción Demo",
      "changedAt": "2026-11-06T21:10:00Z",
      "reschedule": {
        "previousStartAt": "2026-11-16T13:00:00Z",
        "previousEndAt": "2026-11-16T13:30:00Z",
        "newStartAt": "2026-11-16T14:00:00Z",
        "newEndAt": "2026-11-16T14:30:00Z",
        "previousProfessionalId": "00000000-0000-0000-0000-000000000001",
        "newProfessionalId": "00000000-0000-0000-0000-000000000002",
        "previousChairId": "00000000-0000-0000-0000-0000000000b1",
        "newChairId": "00000000-0000-0000-0000-0000000000b2"
      }
    }
  ]
  ```
  El objeto de `reschedule` tiene exactamente ocho campos planos, mapeados 1:1 desde `RescheduleDetail`. `changedAt` está en UTC con `Z`.
- **Opción B**: anidar el detalle como `{ "previous": {...}, "new": {...} }`. Es más legible, pero se aparta de las columnas planas y de la forma de `AppointmentResponse`.
- **Opción C**: devolver la fila cruda de la base con nombres de columnas. Rompe el camelCase de la API y expone detalles de persistencia.
- **Decisión**: **A**, con las correcciones de la autora: `to: "reservado"` en toda reprogramación (C1) y `from`/`reschedule` siempre presentes, sin `exclude_none` (C2).

### D12 — `changedByName`: nombre visible del usuario que hizo el cambio

**Problema**: `changedBy` es un UUID y no hay endpoint de usuarios; sin un nombre, la vista de administración no puede cumplir "ver quién cambió qué".

- **Opción A (recomendada)**: agregar `changedByName` con `app_user.display_name`. Se resuelve con **un solo método de lectura nuevo** en `UserRepository`, `get_display_names(ids) -> dict[UUID, str]`, que hace **una sola consulta** por los ids únicos de las entradas, no una por entrada. No se expone ningún otro campo del usuario (ni hash, ni rol, ni credenciales). Si un usuario no existe (no debería ocurrir en el MVP), el nombre queda `null`.
- **Opción B**: devolver solo `changedBy` (UUID). Es el contrato mínimo, pero el front no puede mostrar un nombre y la KB 03 no tiene ruta de usuarios.
- **Opción C**: devolver `changedBy` como objeto `{ "id", "displayName" }`. Cambia la forma plana y obliga a un nested que el resto de la API no usa.
- **Decisión**: **A** (C6). Es una lectura interna, sin endpoint nuevo, y resuelve la trazabilidad visible de US-033. El método devuelve únicamente el mapa de nombres.

### D13 — Orden del historial

**Problema**: definir la dirección de la lista.

- **Opción A (recomendada)**: orden **ascendente** por `(changedAt, id)`, tal como ya lo devuelve `AppointmentStatusChangeRepository.list_by_appointment_id` (`backend/app/repositories/appointment.py:162`). La primera entrada es el alta y la última es el cambio más reciente. El `id` es el desempate estable.
- **Opción B**: descendente (más reciente primero). Obliga a invertir la consulta o la lista y se aparta del repositorio ya probado.
- **Opción C**: sin orden garantizado. El test de "historial ordenado" de C-23 quedaría indefinido.
- **Decisión**: **A** (C3). El repositorio correcto es **`AppointmentStatusChangeRepository`**, no `AppointmentStatusHistoryRepository`; ya garantiza el orden y el test puede afirmar la secuencia completa. Si la UI prefiere lo más reciente arriba, lo invierte en el cliente.

### D14 — Origen de `now` y de la zona horaria

**Problema**: el dominio exige `now` y `tz` inyectados; la API tiene que obtenerlos sin romper la reproducibilidad.

- **Opción A (recomendada)**: el router calcula `now = datetime.now(UTC)` una vez por request y `tz = ZoneInfo(settings.app_timezone)`, y los pasa a `change_appointment_status`, `cancel_appointment` o `reschedule_appointment`. El mismo `now` se usa para la regla del pasado, `STATUS_CHANGE_TOO_EARLY` y `changed_at` del historial. `GET /history` no necesita `now`.
- **Opción B**: que el servicio llame a `datetime.now()` por dentro. Viola la regla dura del proyecto y hace que los tests dependan del reloj.
- **Opción C**: inyectar un proveedor de reloj o una dependencia FastAPI reemplazable en tests. Agrega indirección y empuja a `dependency_overrides`, prohibido por C-19 y C-21.
- **Decisión**: **A**. `ZoneInfo` se puede construir por request o una vez al arrancar; la interfaz de los servicios no cambia. El reloj no se toma del cliente ni de un header.

### D15 — Tests de `atendido` y `ausente` con el reloj real, sin `monkeypatch` ni overrides (corrección C5)

**Problema**: `atendido` y `ausente` exigen `now >= appointment.start_at`; la API no deja crear turnos en el pasado, así que un test que solo use `POST /api/appointments` no puede llegar a esas transiciones.

- **Opción A (recomendada)**: insertar el turno **directamente en la base de test** con `AppointmentRepository` y su entrada inicial de historial con `AppointmentStatusChangeRepository`, dentro de una sesión del test. El `start_at` es **relativo al reloj real** (por ejemplo, `now` redondeado a 5 minutos menos 2 h) y las FKs salen de `app/demo_data.py` (paciente, profesional, sillón y prestación existentes), con `created_at = updated_at` coherentes. Después se llama a `POST /status` con el reloj real; como `now >= start_at`, la transición es válida. Para `STATUS_CHANGE_TOO_EARLY` se usa un turno con `start_at` futuro y se pide `atendido`.
- **Opción B**: crear un turno futuro por la API y luego `UPDATE appointment SET start_at = now - ...` en la base. Deja el historial inicial con un intervalo anterior distinto al actual y puede confundir las aserciones.
- **Opción C**: `monkeypatch`, `unittest.mock` o `dependency_overrides` para fijar el reloj. Prohibido por las reglas de tests de C-19 y C-21, y no probaría el `datetime.now(UTC)` real del borde.
- **Decisión**: **A** (C5). **Nunca fechas fijas en tests de integración** (D13 de C-21): el turno pasado se arma con fechas relativas al reloj real y se inserta con los repositorios, sin reemplazar el reloj.

### D16 — Tests de concurrencia: alcanzan los de C-17

**Problema**: decidir si C-23 necesita una prueba de concurrencia nueva a nivel HTTP.

- **Opción A (recomendada)**: los tests de concurrencia de C-17 (`test_appointment_concurrency.py`) ya prueban el `SELECT ... FOR UPDATE` y la relectura del estado con dos conexiones reales, `pg_locks` y `SET lock_timeout`. C-23 solo agrega rutas que llaman a esos mismos servicios, así que la serialización real sigue cubierta. Se agrega un test **secuencial** de doble transición a nivel API: la primera operación responde `200`, la segunda responde `422 INVALID_TRANSITION` y en la base queda **una sola** entrada nueva de historial. Eso prueba el cableado de la ruta, no la concurrencia.
- **Opción B**: agregar un test HTTP de dos transiciones simultáneas con barrera. Con `TestClient` las peticiones pueden ejecutarse en serie; no demuestra concurrencia real y sería más frágil que el test de C-17.
- **Opción C**: no agregar ningún test de ruta y confiar solo en C-17. No prueba el `None` → `404`, el mapeo de estados, el `403` de propiedad ni el historial por HTTP.
- **Decisión**: **A**. La prueba real de concurrencia es la de C-17; C-23 suma el test secuencial de doble transición y los tests de contrato de cada ruta.

### D17 — Organización del código y transacción

**Problema**: dónde viven las rutas, los esquemas y la lectura del historial, y quién confirma.

- **Opción A (recomendada)**: `backend/app/api/appointments.py` (el mismo router de C-22) con las cuatro rutas; esquemas en `backend/app/api/schemas.py` (`StatusChangeInput`, `RescheduleInput`, `AppointmentResponse` reutilizado, `HistoryEntryResponse` y `RescheduleDetailResponse`); una función de servicio `get_appointment_history(session, appointment_id)` en `backend/app/services/appointments.py` que cargue el turno, devuelva `None` si no existe y arme las entradas con el nombre visible. La ruta no hace `commit` ni `rollback`: los servicios de mutación ya son dueños de la transacción.
- **Opción B**: un módulo nuevo `services/lifecycle.py` que envuelva a los servicios de C-17. Agrega una capa sin lógica propia.
- **Opción C**: leer historial directo desde el router con los repositorios. Deja el `404` y la resolución de nombres en la capa HTTP.
- **Decisión**: **A**. Reutiliza C-17 y C-22, mantiene el patrón de C-20 (servicios con commit, routers delgados) y deja la única lógica nueva (historial + nombres) en un servicio de lectura. La API no confirma ni revierte por su cuenta.

### D18 — Documentación OpenAPI de las cuatro rutas

**Problema**: las rutas nuevas deben documentar sus errores y seguir los guardianes de C-18/C-19.

- **Opción A (recomendada)**: en cada ruta, `response_model`, `status_code=200`, tag "Turnos" y `responses` con `not_found_responses("Turno")` en las cuatro; `permission_responses()` en las cuatro; `violation_responses(422)` en `cancel`, `status` y `reschedule`; `violation_responses(409)` en `reschedule`. `400` y `401` los agrega `setup_openapi` automáticamente.
- **Opción B**: dejar solo los modelos por defecto de FastAPI. Incumple `api-foundation`: las rutas que rechazan deben documentar sus status con el esquema de violaciones.
- **Opción C**: documentar solo `200` y `404`. El front no vería los códigos de rechazo y los guardianes de OpenAPI podrían fallar.
- **Decisión**: **A**. Es coherente con C-20, C-21 y C-22. En `history` no se documentan `409` ni `422` de dominio; sí `400`, `401`, `403` y `404`.

## Decisiones registradas de la autora

- **D1–D18** y **P1–P9**: aprobadas con la recomendación del explore, con las correcciones **C1–C6** incorporadas en este documento.
- **C1 (D11)**: una reprogramación **siempre** genera una entrada con `to: "reservado"`, venga de `reservado` o de `confirmado`; el ejemplo del explore quedó corregido.
- **C2 (D11)**: `from` y `reschedule` están **siempre** en cada entrada (`from: null` solo en el alta; `reschedule: null` si no es reprogramación). Nada de `exclude_none`.
- **C3 (D13)**: el repositorio correcto es `AppointmentStatusChangeRepository` (`backend/app/repositories/appointment.py:162`), no `AppointmentStatusHistoryRepository`.
- **C4 (D6/P6)**: el apply de C-23 empieza con C-21 y C-22 **archivados**. Se importa directamente `ensure_own_professional` desde donde lo dejó C-21; **no** se crea `backend/app/api/ownership.py` ni se duplica la comparación.
- **C5 (D15)**: el turno con inicio pasado se inserta en la base de test con `AppointmentRepository` y su entrada inicial de historial con `AppointmentStatusChangeRepository`, dentro de una sesión del test, con FKs de `app/demo_data.py` y fechas **relativas al reloj real**; nunca fechas fijas en tests de integración.
- **C6 (D12)**: `changedByName` se resuelve con un único método de lectura nuevo, `UserRepository.get_display_names(ids) -> dict[UUID, str]`, en una sola consulta; no se expone ningún otro campo del usuario.
- **P1** (`changedByName`): sí, D12.
- **P2** (entrada inicial con `from: null`): sí, D11 y D13.
- **P3** (historial ascendente): sí, D13.
- **P4** (sin `note`): sí, D4.
- **P5** (`"Turno no encontrado."`): sí, D2.
- **P6** (reutilizar el helper de C-21): sí, D6, sin `ownership.py`.
- **P7** (detalle de reprogramación plano): sí, D11.
- **P8** (respuesta de mutación solo con el turno): sí, D10.
- **P9** (C-17 + test secuencial de doble transición): sí, D16.

## Risks / Trade-offs

- **[Riesgo] C-21 o C-22 sin archivar** → tarea 0.1; si alguno no está archivado, el apply se detiene (C4).
- **[Riesgo] Se duplica la comparación de propiedad del historial** → D6: importar `ensure_own_professional` de C-21, sin `ownership.py`.
- **[Riesgo] `"cancelado"` llega a `change_appointment_status` y el dominio lanza `ValueError` → `500`** → D3: el esquema de `status` solo acepta `confirmado`, `atendido` y `ausente`.
- **[Riesgo] La API duplica la comparación de propiedad en `CHANGE_STATUS` y tapa el mensaje del dominio** → D5: la ruta de estado no llama al helper; pasa el `Actor` y deja decidir al dominio.
- **[Riesgo] El odontólogo lee el historial de un turno ajeno** → D6: comparación con `ensure_own_professional` cuando el scope es `OWN`.
- **[Riesgo] El `404` antes del `403` de propiedad en el historial revela que un turno existe** → se acepta por consistencia con C-21; solo lo ve un usuario autenticado y no se devuelven datos del turno.
- **[Riesgo] Reprogramar sin `durationMin` usa la duración por defecto de la prestación** → D8: la ruta deja `duration_min=None` y el dominio usa `end_at - start_at` del turno original; test explícito.
- **[Riesgo] Un test de `atendido`/`ausente` intenta crear el turno en el pasado por la API y recibe `422 IN_THE_PAST`** → D15: inserción directa con los repositorios y fechas relativas al reloj real.
- **[Riesgo] Un test de concurrencia HTTP se interpreta como prueba de serialización real** → D16: C-17 es la prueba real con `pg_locks`; C-23 solo agrega el test secuencial.
- **[Riesgo] `changedByName` genera N+1 consultas** → D12: `get_display_names(ids)` con una sola lectura.
- **[Riesgo] El historial omite `from` o incluye `reschedule` solo a veces por usar `exclude_none`** → D11: `from` y `reschedule` siempre presentes (C2).
- **[Riesgo] Repetir una operación ya aplicada devuelve `200` por error** → el dominio trata el mismo estado como `INVALID_TRANSITION`; la UI debe deshabilitar el botón mientras la petición está en vuelo.
- **[Riesgo] Las rutas nuevas no declaran permiso y el guardián las detecta** → montarlas en el router de C-22 bajo `protected_router` con `require_permission` y correr `test_route_guards.py`.
- **[Trade-off] No hay `GET /api/appointments/{id}`** → el historial y las mutaciones no lo necesitan; si la UI requiere el detalle, se suma a C-24.

## Migration Plan

Sin migraciones. Rollback: revertir el commit del change.

## Correcciones aplicadas de la autora (C1–C6)

- **C1**: corregido el ejemplo de reprogramación del explore; `to` es siempre `"reservado"`.
- **C2**: `from` y `reschedule` siempre presentes en cada entrada; sin `exclude_none`.
- **C3**: nombre correcto del repositorio de historial en D13.
- **C4**: precondición C-21 y C-22 archivados; `ensure_own_professional` se importa de C-21 y no se crea `ownership.py`.
- **C5**: inserción directa del turno pasado con los repositorios y fechas relativas al reloj real.
- **C6**: `UserRepository.get_display_names(ids)` como única lectura de nombres.
