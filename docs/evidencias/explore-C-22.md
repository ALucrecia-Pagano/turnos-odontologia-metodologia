# Explore C-22 — `api-dar-turno`

Fecha: 2026-11-06
Fase: 5 — API REST FastAPI y JWT
Governance: **MEDIO** (según `CHANGES.md` §[C-22])
Dependencias en `CHANGES.md`: `C-08`, `C-16`, `C-17`, `C-20`.

> Este explore es analítico: no ejecutó docker, pytest, alembic ni pip, y no tocó código, tests, migraciones ni specs. Se hizo sobre el repositorio en el commit `6c5f840` (propose de C-21). El árbol de trabajo está sucio porque C-20 (`api-catalogos-y-pacientes`) está en implementación: sus archivos modificados y sin trackear en `backend/` **no se tomaron como fuente de verdad**. Las referencias a C-20 salen de `openspec/changes/api-catalogos-y-pacientes/design.md` y de los specs, no de ese código a medio hacer.

---

## 1. Alcance de C-22 según `CHANGES.md` y qué queda afuera

### Qué entra en C-22

1. **`POST /api/appointments`**: alta de un turno nuevo.
2. **Caso de uso transaccional**: abre la transacción, toma `SELECT ... FOR UPDATE` sobre profesional y sillón, carga el contexto (referencias, horarios, bloqueos y turnos), llama a `validate_new_appointment` y persiste turno + historial. La lógica ya existe en `book_appointment` (C-17); C-22 la expone por HTTP.
3. **`now` real inyectado en el borde**: `datetime.now(UTC)`, y la zona horaria desde `APP_TIMEZONE` de la configuración.
4. **`changed_by` desde el JWT**: el `Actor` sale solo del usuario autenticado; nunca del cuerpo.
5. **Rechazo de dominio → `409`/`422`** con **todas** las violaciones (código + mensaje en español), usando la tabla de `api-foundation`.
6. **RBAC**: recepción y administrador crean; odontólogo `403` (fila `APPOINTMENT CREATE` de la matriz de C-19).
7. **Tests de integración**: turno válido (201 + entrada de historial), choque de profesional, choque de sillón, ambas violaciones juntas, fuera de horario, en bloqueo, en el pasado, referencias inexistentes y carrera de dos altas simultáneas sobre el mismo hueco.

### Qué queda explícitamente afuera

- **`GET /api/appointments/{id}`**: no está en el scope de C-22 (ver D7).
- **`GET /api/agenda`** y cualquier consulta de agenda: es C-24.
- **Cancelar, reprogramar, cambiar estado y leer historial**: es C-23.
- **Pantallas**: C-25 en adelante.
- **Cambios de dominio, migraciones o tablas**: no hacen falta. `book_appointment` y `NewAppointmentRequest` ya existen.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-22 reutiliza

| Pieza | Dónde | Qué ofrece |
|-------|-------|------------|
| `book_appointment(session, request, now, tz, auto_commit=True)` | `backend/app/services/appointments.py:90` | Bloquea profesional y sillón con `SELECT ... FOR UPDATE` en orden, carga referencias y contexto, llama a `validate_new_appointment`, inserta turno + primera entrada de historial, hace `commit` explícito y `rollback` ante rechazo. |
| `NewAppointmentRequest` | `backend/app/domain/model.py:131` | `id`, `patient_id`, `professional_id`, `chair_id`, `service_id`, `start_at` (zona obligatoria, normaliza a UTC), `duration_min` opcional y `changed_by` (keyword-only). |
| `Appointment` | `backend/app/domain/model.py:297` | Turno con `start_at`/`end_at` UTC y `status`; valida `start_at < end_at`. |
| `validate_new_appointment` | `backend/app/domain/appointment/validate.py:150` | Devuelve `Ok(appointment, status_change)` o `Rejected(violations)`. Evalúa en dos grupos: validez del pedido y conflictos de agenda. Devuelve todas las violaciones del primer grupo que falla, en orden estable (RN-AG-12). |
| `check_references` | `backend/app/domain/rules/references.py:59` | Devuelve una violación por cada referencia inexistente o inactiva, en orden paciente → profesional → sillón → prestación, con `reference_kind`. |
| `DomainRejectedError` + `domain_rejected_handler` | `backend/app/api/errors.py` (ya en HEAD) | Traduce un `Rejected` a HTTP: precedencia `403`, luego `422`, luego `409`; cuerpo `{ "violations": [...] }` en camelCase, conservando el orden del dominio. |
| `VIOLATION_STATUS_MAP` | `backend/app/api/errors.py` | `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST` → `422`; `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` → `409`. |
| `protected_router`, `get_current_user`, `get_current_actor` | `backend/app/api/deps.py` | Autenticación por request; `protected_router` no deja nacer rutas sin token. |
| `RequirePermission` / `require_permission` | `backend/app/api/deps.py:77` | Autoriza contra la matriz RBAC y entrega `Permission(actor, scope)`. |
| Fila `APPOINTMENT CREATE` | `backend/app/auth/permissions.py:48` | `{ recepcion: ALL, administrador: ALL }`; el odontólogo no tiene entrada y recibe `403` con `"No tiene permiso para dar turnos."` |
| `Settings.app_timezone` | `backend/app/config.py:26` | Nombre de la zona configurada (por ejemplo, `America/Argentina/Buenos_Aires`). |
| `datetime.now(UTC)` en el borde | `backend/app/api/auth.py:67` | Precedente del proyecto para el reloj en la capa API. |
| Harness de integración | `backend/tests/integration/conftest.py`, `auth_support.py` | App real contra PostgreSQL de test, usuarios y tokens reales por `POST /api/auth/login`, limpieza con `clean_database_tables`. Sin mocks ni `dependency_overrides`. |
| Patrón de concurrencia | `backend/tests/integration/test_appointment_concurrency.py` | Dos sesiones reales en hilos, espera verificada con `pg_locks` y `SET lock_timeout`; sin `time.sleep`. Prueba que `book_appointment` serializa por profesional y por sillón. |

### 2.2. Qué recibe, qué devuelve y qué le falta a `book_appointment` para la API

**Recibe**: `session` (SQLAlchemy), un `NewAppointmentRequest` ya construido, `now` con zona (UTC), `tz` (`ZoneInfo`) y `auto_commit=True`. No recibe `Actor` ni permisos: supone que el llamador ya autorizó la operación.

**Devuelve**: `ValidationResult`, es decir `Ok(appointment, status_change)` o `Rejected(violations)`. Nunca devuelve `None`. En `Ok`, el turno ya quedó persistido y el historial tiene la entrada inicial (`from_status` nulo, `to_status` `reservado`, `changed_by = request.changed_by`, `changed_at = now`). En `Rejected`, el servicio ya hizo `rollback`.

**Le falta para usarse desde la API**:

1. Una ruta `POST /api/appointments` montada bajo `protected_router`, con `require_permission(APPOINTMENT, CREATE)`.
2. Esquemas Pydantic de entrada y salida en camelCase, con `extra="forbid"`.
3. Construir el `NewAppointmentRequest` en el borde: generar `id`, tomar `changed_by` del `Actor` y resolver la duración.
4. Inyectar `now` y `tz` desde la configuración.
5. Traducir `Rejected` a la respuesta HTTP (reutilizando el manejador existente).
6. Serializar el turno aceptado en la respuesta `201`.
7. Tests de integración, incluida la carrera a nivel HTTP.

No hay que tocar la lógica de dominio ni la persistencia de C-17: esa parte ya está cerrada y probada.

---

## 3. Decisiones de diseño (`D1`–`D12`)

### D1 — Endpoint y RBAC

| Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores |
|--------|------|------------------|------------|-----------|-------|-------|---------|
| `POST` | `/api/appointments` | `APPOINTMENT` / `CREATE` | — (`403`) | todos | todos | `201` | `400`, `401`, `403`, `409`, `422` |

- **Opción A (recomendada)**: solo `POST /api/appointments`, colgado de `protected_router` y con `require_permission(Resource.APPOINTMENT, Action.CREATE)`.
- **Opción B**: sumar `GET /api/appointments/{id}` en C-22. Agranda el scope, exige decidir `404` y alcance de lectura, y duplica lo que C-24 debe resolver.
- **Opción C**: montar la ruta fuera de `protected_router` y validar el token a mano. Rompe el guardián de rutas de C-19.
- **Recomendación**: **A**. Respeta el scope de `CHANGES.md` y la matriz; el guardián `test_route_guards.py` debe seguir pasando sin modificarlo.

### D2 — Cuerpo del `POST` y campos que genera el servidor

- **Opción A (recomendada)**:
  - El cliente manda `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt` y, opcionalmente, `durationMin`.
  - `startAt` es ISO 8601 **con zona horaria obligatoria** (por ejemplo, `2026-11-16T10:00:00-03:00`). Un valor sin offset se rechaza con `400` en el esquema, antes de llegar al dominio (que lanzaría `ValueError` y produciría un `500`).
  - El servidor genera `id` (`uuid4`), `changedBy` (desde `Actor.user_id`), `status` (`reservado`) y `endAt` (`startAt + duración`); la duración sale de la prestación si no se manda `durationMin`.
  - `durationMin` opcional conserva US-001 CA-2 y el contrato del Flujo 1 de KB 07; el dominio ya valida `INVALID_DURATION`. El esquema usa `extra="forbid"`, así que mandar `id`, `changedBy` o `status` desde el cliente da `400`.
- **Opción B**: el cliente manda también `id`, `changedBy`, `status` o una duración obligatoria. Es un riesgo de seguridad y de determinismo: el usuario podría falsificar la autoría, y el dominio exige que los ids los inyecte el llamador.
- **Opción C**: no aceptar `durationMin` y usar siempre la duración de la prestación. Es más simple, pero pierde el caso "duración explícita" de US-001 CA-2 y del Flujo 1.
- **Recomendación**: **A**. Si la autora prefiere el cuerpo mínimo, se puede quitar `durationMin` sin tocar el dominio, pero se pierde una capacidad ya prevista en la KB (P1).

### D3 — Respuesta `201`: turno solo o turno + historial

- **Opción A (recomendada)**: responder solo el turno creado, en camelCase y con instantes en UTC (`Z`):
  ```json
  {
    "id": "...",
    "patientId": "...",
    "professionalId": "...",
    "chairId": "...",
    "serviceId": "...",
    "startAt": "2026-11-16T13:00:00Z",
    "endAt": "2026-11-16T13:30:00Z",
    "status": "reservado"
  }
  ```
  El historial se persiste igual y el test de integración verifica la fila en la base. El Flujo 1 de KB 07 dice "responde `201` con el turno".
- **Opción B**: devolver el turno más su primera entrada de historial. Prueba visualmente que el historial se creó, pero expone `changedBy` (id interno del usuario) y adelanta una forma de respuesta que C-23 todavía no definió.
- **Opción C**: devolver el turno con nombres (`patientName`, `professionalName`, `chairName`). Ahorra consultas al front, pero agrega joins y no lo pide la KB; la UI ya eligió esas entidades.
- **Recomendación**: **A**. La entrada de historial se verifica en el test, no se devuelve. Mantiene la respuesta mínima y el contrato del Flujo 1.

### D4 — Origen de `now` y de la zona horaria

- **Opción A (recomendada)**: el router calcula `now = datetime.now(UTC)` una vez por request y `tz = ZoneInfo(settings.app_timezone)`, y pasa ambos a `book_appointment`. El mismo `now` se usa para la regla del pasado y para `changed_at` del historial. El dominio nunca lee el reloj (RN-GL-04).
- **Opción B**: que el servicio llame a `datetime.now()` por dentro. Viola la regla dura del proyecto y rompe la reproducibilidad de los tests.
- **Opción C**: inyectar un proveedor de reloj o una dependencia FastAPI para reemplazarlo en tests. Agrega indirección y empuja a usar `dependency_overrides`, que C-19 y C-21 prohíben; además los tests pueden usar fechas relativas al reloj real (C-21 D13).
- **Recomendación**: **A**. `ZoneInfo` se puede construir por request (es barato y `zoneinfo` cachea) o una sola vez al arrancar la app; la interfaz de `book_appointment` no cambia. El reloj no se inyecta desde el cliente ni desde un header.

### D5 — Traducción del `Rejected` a `409` o `422`

- **Opción A (recomendada)**: si `book_appointment` devuelve `Rejected`, la ruta lanza `DomainRejectedError(rejected)`. El manejador global existente calcula el status con la precedencia de `api-foundation` (`403` → `422` → `409`) y serializa **todas** las violaciones, en el orden del dominio, en camelCase y omitiendo los campos vacíos.
- **Opción B**: traducir código por código en la ruta. Duplica la tabla de `api-foundation`, se desactualiza y puede perder violaciones.
- **Opción C**: crear una excepción nueva solo para turnos. No aporta; `DomainRejectedError` ya es el contrato del proyecto.
- **Recomendación**: **A**. Ejemplos:
  - `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT` o `IN_THE_PAST` → `422`.
  - `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `PROFESSIONAL_OVERLAP` o `CHAIR_OVERLAP` → `409`.
  - Dos solapamientos juntos (`PROFESSIONAL_OVERLAP` + `CHAIR_OVERLAP`) → `409` con **ambas** violaciones en el cuerpo.
  - No hay que reordenar ni filtrar nada: el dominio ya devuelve el orden de RN-AG-12. El servicio ya hizo `rollback` antes de devolver el `Rejected`.

### D6 — Referencias inexistentes: ¿`404` o `422 UNKNOWN_REFERENCE`?

- **Opción A (recomendada)**: `422 UNKNOWN_REFERENCE` para cualquier id del **cuerpo** que no exista. El dominio devuelve una violación por cada referencia faltante, todas juntas, con `referenceKind` (`PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`). Una referencia inactiva devuelve `422 INACTIVE_REFERENCE`.
- **Opción B**: `404 NOT_FOUND` para referencias faltantes. Es el contrato de C-20 y C-21, pero ahí el id viene en la **ruta**; acá viene en el cuerpo. Además obligaría a precargar y perdería las demás violaciones y el `referenceKind`.
- **Opción C**: `404` solo para profesional o sillón (porque se bloquean sus filas) y `422` para paciente o prestación. Inconsistente y sin beneficio.
- **Recomendación**: **A**. KB 07 Flujo 1 dice explícitamente "Referencia inexistente → `422 UNKNOWN_REFERENCE`", y `api-foundation` clasifica `UNKNOWN_REFERENCE` como `422`. Bloquear una fila inexistente con `SELECT ... FOR UPDATE` no falla: no devuelve filas, y el dominio recibe `None` y genera la violación. No hay que agregar un `404` para el cuerpo.

### D7 — ¿Hace falta `GET /api/appointments/{id}` en C-22?

- **Opción A (recomendada)**: no incluirlo en C-22. El `POST` devuelve el turno creado; C-24 resuelve las lecturas de agenda y C-23 el historial. Si el front necesita un detalle puntual, se agrega explícitamente en C-24 (su scope actual solo menciona `GET /api/agenda`, así que conviene dejarlo anotado).
- **Opción B**: agregarlo en C-22. Obliga a decidir `404`, `APPOINTMENT READ`/alcance y tests de lectura, y sale del scope del change.
- **Opción C**: dejarlo como lectura interna del repositorio, sin ruta. No lo usa nadie en C-22.
- **Recomendación**: **A**. Mantiene C-22 enfocado en el alta; el detalle no es un prerrequisito del `POST`. Si la autora lo quiere para la UI, que se sume al scope de C-24 antes de implementarlo (P3).

### D8 — Tests de "en el pasado", "en bloqueo" y "fuera de horario" con el reloj real

- **Opción A (recomendada)**: seguir C-21 D13. La API usa `datetime.now(UTC)` y no se reemplaza en los tests. Los tests calculan **el lunes futuro L**: el primer lunes que esté al menos 7 días después del momento actual. Cargan el horario del profesional para `weekday = 1`, de 09:00 a 13:00 locales, y usan `ZoneInfo(settings.app_timezone)` para convertir las horas locales a instantes. Escenarios:
  - **Válido**: `L` a las 10:00 locales, profesional y sillón libres → `201`; se verifica el turno y la entrada de historial con `from_status = NULL`, `to_status = reservado` y `changed_by` del usuario del token.
  - **En el pasado**: ayer a las 10:00 locales, en múltiplo de 5 → `422 IN_THE_PAST` (el grupo 1 no evalúa conflictos).
  - **En bloqueo**: bloqueo que cubre `L` de 09:00 a 13:00, turno `L` 10:00 dentro del horario → `409 BLOCKED_TIME`.
  - **Fuera de horario**: `L` a las 18:00 locales, sin bloqueo → `409 OUTSIDE_WORKING_HOURS`.
  - **Solapamiento de profesional**: primer `POST` en `L` 10:00 (profesional P, sillón 1); segundo `POST` en `L` 10:00 (mismo P, sillón 2) → `409 PROFESSIONAL_OVERLAP`.
  - **Solapamiento de sillón**: mismo horario, otro profesional, mismo sillón → `409 CHAIR_OVERLAP`.
  - **Ambas juntas**: mismo profesional y mismo sillón en el mismo horario → `409` con `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`.
- **Opción B**: fechas fijas. Se vuelven frágiles: cuando la fecha pase, "válido" empieza a dar `IN_THE_PAST` y el test falla sin que haya regresión.
- **Opción C**: reemplazar el reloj con `monkeypatch` o `dependency_overrides`. Prohibido por las reglas de tests de C-19/C-21, y además no probaría el cableado real del borde.
- **Recomendación**: **A**. Los tests unitarios del dominio siguen usando fechas fijas porque reciben `now` por parámetro; los de API usan fechas relativas. Se usan ids y recursos únicos por test y `clean_database_tables` entre casos. Nada de `time.sleep`.

### D9 — Carrera de dos altas simultáneas por HTTP

- **Opción A (recomendada)**: conservar los tests de concurrencia de C-17 sobre el servicio (prueban el `SELECT ... FOR UPDATE` por profesional y por sillón) **y** agregar un test nuevo a nivel API, como pide `CHANGES.md`. Dos `POST /api/appointments` concurrentes sobre el mismo hueco, con tokens reales, lanzados desde dos hilos sincronizados con una barrera. Se afirma que exactamente uno responde `201` y el otro `409` con `PROFESSIONAL_OVERLAP` y/o `CHAIR_OVERLAP`, y que en la base queda **un solo** turno y **una sola** entrada de historial. No se afirma cuál gana.
- **Opción B**: alcanzaría con los tests de C-17. No alcanza para el criterio de C-22: no prueban el cableado de la ruta, el `now`/`tz` del borde, el `changed_by` del JWT ni el `commit` a través de la sesión por request.
- **Opción C**: reproducir la espera en `pg_locks` a nivel HTTP. Es más difícil y frágil que en el test de servicio; C-17 ya demuestra el lock. No hace falta duplicarlo.
- **Recomendación**: **A**. El test de API usa la barrera para que ambas peticiones estén listas antes de disparar; la serialización de PostgreSQL hace el resto. El resultado esperado es un conjunto de status `{201, 409}`, no un orden.

### D10 — Organización del código y transacción

- **Opción A (recomendada)**: `backend/app/api/appointments.py` con el router y la ruta; esquemas `AppointmentInput` y `AppointmentResponse` en `backend/app/api/schemas.py`; la ruta construye `NewAppointmentRequest` (uuid4, `changed_by = actor.user_id`, duración opcional) y llama directamente a `book_appointment`. No se duplica la lógica de C-17.
- **Opción B**: crear un servicio `services/book_appointment_api.py` que envuelva a `book_appointment`. Agrega una capa sin lógica propia; C-17 ya es el caso de uso.
- **Opción C**: poner la construcción del pedido dentro de un método del esquema Pydantic. Es una variante de A; puede servir para ordenar, pero acopla el esquema al dominio.
- **Recomendación**: **A**, con un helper privado `_build_request(...)` en el router si hace falta claridad. El `commit` lo hace `book_appointment(auto_commit=True)`; la sesión de `get_db_session` no confirma. La ruta no hace `commit` ni `rollback` por su cuenta. El router se incluye bajo `protected_router` (o sus rutas declaran `Depends(require_permission(...))`) para que el guardián de C-19 lo vea.

### D11 — Documentación OpenAPI y respuestas de error

- **Opción A (recomendada)**: `response_model=AppointmentResponse`, `status_code=201`, tag "Turnos"; `responses` con `violation_responses(409, 422)` y `permission_responses()`; `400` y `401` los agrega `setup_openapi` automáticamente. Sin `404`, porque esta ruta no recibe ids de ruta.
- **Opción B**: dejar solo los modelos por defecto de FastAPI. Incumple `api-foundation`: las rutas que rechazan deben documentar sus status con el esquema de violaciones.
- **Recomendación**: **A**. Coherente con C-20 y C-21, y verificable con los tests de OpenAPI existentes.

### D12 — Idempotencia del `POST`

- **Opción A (recomendada)**: no agregar clave de idempotencia en el MVP. `POST` no es idempotente; el front de C-29 debe deshabilitar el botón mientras la petición está en vuelo. Si el cliente reintenta después de un `201`, el segundo intento choca por solapamiento (`409`) y no crea un duplicado en el mismo hueco; si el primero falló y se revirtió, el reintento es limpio.
- **Opción B**: aceptar un header `Idempotency-Key` y persistir la respuesta. Requiere tabla o columna nueva, migración y política de expiración; fuera del MVP y del scope de C-22.
- **Recomendación**: **A**. Se documenta el riesgo y se resuelve en la UI con el estado de carga; no se toca la base.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| C-20 está a medio implementar y C-22 depende de él (`CHANGES.md`) | No tomar sus archivos como fuente de verdad; archivarlo antes del apply de C-22. Este explore usa el `design.md` de C-20 para el formato de errores y servicios. |
| `startAt` sin zona horaria llega al dominio y produce `500` | Validación en el esquema Pydantic → `400` antes de construir `NewAppointmentRequest` (D2). |
| `APP_TIMEZONE` inválida revienta al construir `ZoneInfo` | Riesgo menor de configuración; opcionalmente validarla al arrancar en una tarea de infraestructura. No cambia el contrato. |
| El `POST` reintentado crea un segundo turno | D12: la UI deshabilita el envío; un reintento sobre el mismo hueco da `409` por solapamiento. Sin clave de idempotencia en el MVP. |
| Test de carrera HTTP inestable por tiempos | Usar barrera y afirmar el conjunto de status, no el orden; la serialización la garantiza PostgreSQL. |
| Falta `GET /api/appointments/{id}` para el front | D7: no es necesario en C-22; si se necesita, sumarlo explícitamente a C-24. |
| La ruta nueva no declara permiso y el guardián la detecta | Montarla bajo `protected_router` y declarar `require_permission(APPOINTMENT, CREATE)`; correr `test_route_guards.py`. |
| Un `409` mezclado con `422` por error de mapeo | No reimplementar la tabla: usar `DomainRejectedError` y su manejador (D5). |
| C-21 corre en paralelo y puede tocar servicios compartidos | C-22 no depende de C-21; no editar sus archivos. Si C-21 mueve `_lock_resources`, coordinar el merge, pero C-22 no lo necesita. |

### Preguntas para la autora

- **P1**: ¿Aceptás `durationMin` opcional en el cuerpo, además de la duración por defecto de la prestación (D2)? Sugerencia: sí, porque US-001 CA-2 y el Flujo 1 ya lo prevén. Si preferís el cuerpo mínimo, se quita.
- **P2**: ¿La respuesta `201` devuelve solo el turno, sin la entrada de historial (D3)? Sugerencia: sí; el historial se persiste y se verifica en el test, pero no se expone hasta C-23.
- **P3**: ¿Dejamos `GET /api/appointments/{id}` para C-24 (D7)? Sugerencia: sí. Si la UI lo necesita antes, hay que sumarlo al scope de C-24.
- **P4**: ¿Aceptás no tener clave de idempotencia en el MVP (D12)? Sugerencia: sí; el front deshabilita el botón mientras espera.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

0. **Precondición**: C-20 archivado y verde; C-16 y C-17 verdes; no tocar los archivos de C-20/C-21 en curso.
1. **Esquemas**: `AppointmentInput` (`patientId`, `professionalId`, `chairId`, `serviceId`, `startAt` con validador de zona obligatoria, `durationMin` opcional; `extra="forbid"`) y `AppointmentResponse` en camelCase (D2, D3).
2. **Ruta**: `backend/app/api/appointments.py` con `POST /appointments`, `require_permission(APPOINTMENT, CREATE)`, cálculo de `now`/`tz`, construcción de `NewAppointmentRequest` y llamada a `book_appointment` (D1, D4, D10).
3. **Errores**: lanzar `DomainRejectedError` ante `Rejected` y reutilizar el manejador; documentar `409`/`422`/`403` en Swagger (D5, D11).
4. **Registro**: incluir el router bajo `protected_router` en `main.py`; verificar que los guardianes de rutas y permisos sigan pasando (D1, D10).
5. **Tests de integración**: turno válido (201 + historial), solapamiento de profesional, de sillón y ambos juntos; fuera de horario, bloqueo y pasado con el lunes futuro L; referencias inexistentes e inactivas; `startAt` sin zona → 400; odontólogo → 403; sin token → 401; cuerpo malformado → 400 (D6, D8, D9).
6. **Helpers de test**: cálculo del lunes futuro L y de las horas locales, carga de horarios y bloqueos, usuarios y tokens reales; sin mocks ni overrides (D8, D9).
7. **Carrera HTTP**: test de dos altas simultáneas con barrera; exactamente un `201`, un `409`, un turno y una entrada de historial (D9).
8. **Evidencias**: pytest de dominio e integración, mypy strict, guardianes de rutas/OpenAPI, y `verify-C-22.md` con el formato de C-19/C-20. Si el proyecto lo mantiene, `mutaciones-C-22.py` y `trazabilidad-C-22.py`.
