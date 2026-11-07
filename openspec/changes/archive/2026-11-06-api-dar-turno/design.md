# Design — C-22 `api-dar-turno`

## Context

Este change expone por HTTP el alta de turnos que C-17 ya implementa en `book_appointment`. Parte de `docs/evidencias/explore-C-22.md`; las decisiones D1–D12 son las del explore aprobadas por la autora, con la precisión de D9 sobre qué prueba el test HTTP y la precondición nueva D13.

Depende de C-08 (validación de turnos), C-16 (persistencia y bloqueos), C-17 (`book_appointment`, `AppointmentReader` y bloqueo de filas) y C-20 (esquemas en camelCase, servicios con commit y tests con tokens reales). **C-20 tiene que estar archivado antes de empezar el apply** (tarea 0.1), porque C-22 usa su patrón de esquemas y de tests.

## Goals / Non-Goals

**Goals**: exponer `POST /api/appointments`; autenticar y autorizar con la matriz RBAC; construir el pedido de dominio con ids y autoría del servidor; inyectar `now` UTC y `APP_TIMEZONE`; persistir turno e historial en una sola transacción; devolver `201` con el turno y `409`/`422` con todas las violaciones; documentar la ruta en OpenAPI; probar los contratos con tokens reales.

**Non-Goals**: `GET /api/appointments/{id}` (queda fuera; ver D7); agenda y listados (C-24); cancelar, reprogramar y cambiar estado (C-23); pantallas (C-25 en adelante); idempotencia con clave (D12); cambios de dominio, migraciones o tablas.

## Decisions

### D1 — Endpoint y RBAC

| Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores |
|--------|------|------------------|------------|-----------|-------|-------|---------|
| `POST` | `/api/appointments` | `APPOINTMENT` / `CREATE` | — (`403`) | todos | todos | `201` | `400`, `401`, `403`, `409`, `422` |

- **Opción A (recomendada)**: solo `POST /api/appointments`, colgado de `protected_router` y con `require_permission(Resource.APPOINTMENT, Action.CREATE)`.
- **Opción B**: sumar `GET /api/appointments/{id}` en C-22. Agranda el scope, exige decidir `404` y alcance de lectura, y duplica lo que C-24 debe resolver.
- **Opción C**: montar la ruta fuera de `protected_router` y validar el token a mano. Rompe el guardián de rutas de C-19.
- **Decisión**: **A**. Respeta el scope de `CHANGES.md` y la matriz; el guardián `test_route_guards.py` debe seguir pasando sin modificarlo.

### D2 — Cuerpo del `POST` y campos que genera el servidor

- **Opción A (recomendada)**:
  - El cliente manda `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt` y, opcionalmente, `durationMin`.
  - `startAt` es ISO 8601 **con zona horaria obligatoria** (por ejemplo, `2026-11-16T10:00:00-03:00`). Un valor sin offset se rechaza con `400` en el esquema, antes de llegar al dominio (que lanzaría `ValueError` y produciría un `500`).
  - El servidor genera `id` (`uuid4`), `changedBy` (desde `Actor.user_id`), `status` (`reservado`) y `endAt` (`startAt + duración`); la duración sale de la prestación si no se manda `durationMin`.
  - `durationMin` opcional conserva US-001 CA-2 y el contrato del Flujo 1 de KB 07; el dominio ya valida `INVALID_DURATION`. El esquema usa `extra="forbid"`, así que mandar `id`, `changedBy` o `status` desde el cliente da `400`.
- **Opción B**: el cliente manda también `id`, `changedBy`, `status` o una duración obligatoria. Es un riesgo de seguridad y de determinismo: el usuario podría falsificar la autoría, y el dominio exige que los ids los inyecte el llamador.
- **Opción C**: no aceptar `durationMin` y usar siempre la duración de la prestación. Es más simple, pero pierde el caso "duración explícita" de US-001 CA-2 y del Flujo 1.
- **Decisión**: **A** (respuesta de la autora a P1).

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
- **Decisión**: **A** (respuesta de la autora a P2). La entrada de historial se verifica en el test, no se devuelve.

### D4 — Origen de `now` y de la zona horaria

- **Opción A (recomendada)**: el router calcula `now = datetime.now(UTC)` una vez por request y `tz = ZoneInfo(settings.app_timezone)`, y pasa ambos a `book_appointment`. El mismo `now` se usa para la regla del pasado y para `changed_at` del historial. El dominio nunca lee el reloj (RN-GL-04).
- **Opción B**: que el servicio llame a `datetime.now()` por dentro. Viola la regla dura del proyecto y rompe la reproducibilidad de los tests.
- **Opción C**: inyectar un proveedor de reloj o una dependencia FastAPI para reemplazarlo en tests. Agrega indirección y empuja a usar `dependency_overrides`, que C-19 y C-21 prohíben; además los tests pueden usar fechas relativas al reloj real (C-21 D13).
- **Decisión**: **A**. `ZoneInfo` se puede construir por request o una sola vez al arrancar la app; la interfaz de `book_appointment` no cambia. El reloj no se inyecta desde el cliente ni desde un header.

### D5 — Traducción del `Rejected` a `409` o `422`

- **Opción A (recomendada)**: si `book_appointment` devuelve `Rejected`, la ruta lanza `DomainRejectedError(rejected)`. El manejador global existente calcula el status con la precedencia de `api-foundation` (`403` → `422` → `409`) y serializa **todas** las violaciones, en el orden del dominio, en camelCase y omitiendo los campos vacíos.
- **Opción B**: traducir código por código en la ruta. Duplica la tabla de `api-foundation`, se desactualiza y puede perder violaciones.
- **Opción C**: crear una excepción nueva solo para turnos. No aporta; `DomainRejectedError` ya es el contrato del proyecto.
- **Decisión**: **A**. Ejemplos:
  - `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT` e `IN_THE_PAST` → `422`.
  - `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` → `409`.
  - Dos solapamientos juntos (`PROFESSIONAL_OVERLAP` + `CHAIR_OVERLAP`) → `409` con **ambas** violaciones en el cuerpo.
  - No hay que reordenar ni filtrar nada: el dominio ya devuelve el orden de RN-AG-12. El servicio ya hizo `rollback` antes de devolver el `Rejected`.

### D6 — Referencias inexistentes: ¿`404` o `422 UNKNOWN_REFERENCE`?

- **Opción A (recomendada)**: `422 UNKNOWN_REFERENCE` para cualquier id del **cuerpo** que no exista. El dominio devuelve una violación por cada referencia faltante, todas juntas, con `referenceKind` (`PATIENT`, `PROFESSIONAL`, `CHAIR` o `SERVICE`). Una referencia inactiva devuelve `422 INACTIVE_REFERENCE`.
- **Opción B**: `404 NOT_FOUND` para referencias faltantes. Es el contrato de C-20 y C-21, pero ahí el id viene en la **ruta**; acá viene en el cuerpo. Además obligaría a precargar y perdería las demás violaciones y el `referenceKind`.
- **Opción C**: `404` solo para profesional o sillón (porque se bloquean sus filas) y `422` para paciente o prestación. Inconsistente y sin beneficio.
- **Decisión**: **A**. KB 07 Flujo 1 dice explícitamente "Referencia inexistente → `422 UNKNOWN_REFERENCE`", y `api-foundation` clasifica `UNKNOWN_REFERENCE` como `422`. Bloquear una fila inexistente con `SELECT ... FOR UPDATE` no falla: no devuelve filas, y el dominio recibe `None` y genera la violación. No hay que agregar un `404` para el cuerpo.

### D7 — ¿Hace falta `GET /api/appointments/{id}` en C-22?

- **Opción A (recomendada)**: no incluirlo en C-22. El `POST` devuelve el turno creado; C-24 resuelve las lecturas de agenda y C-23 el historial. Si el front necesita un detalle puntual, se agrega explícitamente en C-24 (su scope actual solo menciona `GET /api/agenda`, así que conviene dejarlo anotado).
- **Opción B**: agregarlo en C-22. Obliga a decidir `404`, `APPOINTMENT READ`/alcance y tests de lectura, y sale del scope del change.
- **Opción C**: dejarlo como lectura interna del repositorio, sin ruta. No lo usa nadie en C-22.
- **Decisión**: **A** (respuesta de la autora a P3). Mantiene C-22 enfocado en el alta; el detalle no es un prerrequisito del `POST`. La corrección propuesta para `CHANGES.md` queda al final de este documento.

### D8 — Tests de "en el pasado", "en bloqueo" y "fuera de horario" con el reloj real

- **Opción A (recomendada)**: seguir C-21 D13. La API usa `datetime.now(UTC)` y no se reemplaza en los tests. Los tests calculan **el lunes futuro L**: el primer lunes que esté al menos 7 días después del momento actual. Cargan el horario del profesional para `weekday = 1`, de 09:00 a 13:00 locales, y usan `ZoneInfo(settings.app_timezone)` para convertir las horas locales a instantes. Escenarios:
  - **Válido**: `L` a las 10:00 locales, profesional y sillón libres → `201`; se verifica el turno y la entrada de historial con `from_status = NULL`, `to_status = reservado` y `changed_by` del usuario del token.
  - **En el pasado**: ayer a las 10:00 locales, en múltiplo de 5 → `422 IN_THE_PAST`.
  - **En bloqueo**: bloqueo que cubre `L` de 09:00 a 13:00, turno `L` 10:00 dentro del horario → `409 BLOCKED_TIME`.
  - **Fuera de horario**: `L` a las 18:00 locales, con un profesional cuyo horario termina a las 13:00 → `409 OUTSIDE_WORKING_HOURS`.
  - **Solapamiento de profesional**: primer `POST` en `L` 10:00 (profesional P, sillón 1); segundo `POST` en `L` 10:00 (mismo P, sillón 2) → `409 PROFESSIONAL_OVERLAP`.
  - **Solapamiento de sillón**: mismo horario, otro profesional, mismo sillón → `409 CHAIR_OVERLAP`.
  - **Ambas juntas**: mismo profesional y mismo sillón en el mismo horario → `409` con `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`.
- **Opción B**: fechas fijas. Se vuelven frágiles: cuando la fecha pase, "válido" empieza a dar `IN_THE_PAST` y el test falla sin que haya regresión.
- **Opción C**: reemplazar el reloj con `monkeypatch` o `dependency_overrides`. Prohibido por las reglas de tests de C-19/C-21, y además no probaría el cableado real del borde.
- **Decisión**: **A**. Los tests unitarios del dominio siguen usando fechas fijas porque reciben `now` por parámetro; los de API usan fechas relativas. Se usan ids y recursos únicos por test y `clean_database_tables` entre casos. Nada de `time.sleep`.

### D9 — Carrera de dos altas simultáneas por HTTP

- **Opción A (recomendada)**: conservar los tests de concurrencia de C-17 sobre el servicio (prueban el `SELECT ... FOR UPDATE` por profesional y por sillón con `pg_locks`) **y** agregar un test nuevo a nivel API, como pide `CHANGES.md`. Dos `POST /api/appointments` sobre el mismo hueco, con tokens reales y una barrera. Se afirma que una respuesta es `201`, la otra es `409`, y que en la base queda **un solo** turno y **una sola** entrada de historial.
  - **Precisión de la autora**: el test HTTP prueba el cableado de la ruta (el `now` del borde, el `changed_by` del JWT y el `commit`) y que queda una sola fila. Con `TestClient` las dos peticiones pueden ejecutarse en serie, así que **no** demuestra concurrencia real. La prueba de la concurrencia real sigue siendo la de C-17 en `backend/tests/integration/test_appointment_concurrency.py`, con `pg_locks`.
- **Opción B**: alcanzaría con los tests de C-17. No alcanza para el criterio de C-22: no prueban el cableado de la ruta, el `now`/`tz` del borde, el `changed_by` del JWT ni el `commit` a través de la sesión por request.
- **Opción C**: reproducir la espera en `pg_locks` a nivel HTTP. Es más difícil y frágil que en el test de servicio; C-17 ya demuestra el lock. No hace falta duplicarlo.
- **Decisión**: **A**, con la precisión anterior: el test HTTP no exagera lo que prueba.

### D10 — Organización del código y transacción

- **Opción A (recomendada)**: `backend/app/api/appointments.py` con el router y la ruta; esquemas `AppointmentInput` y `AppointmentResponse` en `backend/app/api/schemas.py`; la ruta construye `NewAppointmentRequest` (uuid4, `changed_by = actor.user_id`, duración opcional) y llama directamente a `book_appointment`. No se duplica la lógica de C-17.
- **Opción B**: crear un servicio `services/book_appointment_api.py` que envuelva a `book_appointment`. Agrega una capa sin lógica propia; C-17 ya es el caso de uso.
- **Opción C**: poner la construcción del pedido dentro de un método del esquema Pydantic. Es una variante de A; puede servir para ordenar, pero acopla el esquema al dominio.
- **Decisión**: **A**, con un helper privado `_build_request(...)` en el router si hace falta claridad. El `commit` lo hace `book_appointment(auto_commit=True)`; la sesión de `get_db_session` no confirma. La ruta no hace `commit` ni `rollback` por su cuenta. El router se incluye bajo `protected_router` para que el guardián de C-19 lo vea.

### D11 — Documentación OpenAPI y respuestas de error

- **Opción A (recomendada)**: `response_model=AppointmentResponse`, `status_code=201`, tag "Turnos"; `responses` con `violation_responses(409, 422)` y `permission_responses()`; `400` y `401` los agrega `setup_openapi` automáticamente. Sin `404`, porque esta ruta no recibe ids de ruta.
- **Opción B**: dejar solo los modelos por defecto de FastAPI. Incumple `api-foundation`: las rutas que rechazan deben documentar sus status con el esquema de violaciones.
- **Decisión**: **A**. Coherente con C-20 y C-21, y verificable con los tests de OpenAPI existentes.

### D12 — Idempotencia del `POST`

- **Opción A (recomendada)**: no agregar clave de idempotencia en el MVP. `POST` no es idempotente; el front de C-29 debe deshabilitar el botón mientras la petición está en vuelo. Si el cliente reintenta después de un `201`, el segundo intento choca por solapamiento (`409`) y no crea un duplicado en el mismo hueco; si el primero falló y se revirtió, el reintento es limpio.
- **Opción B**: aceptar un header `Idempotency-Key` y persistir la respuesta. Requiere tabla o columna nueva, migración y política de expiración; fuera del MVP y del scope de C-22.
- **Decisión**: **A** (respuesta de la autora a P4). Se documenta el riesgo y se resuelve en la UI con el estado de carga; no se toca la base.

### D13 — Precondición: C-20 archivado

El apply de C-22 arranca con C-20 (`api-catalogos-y-pacientes`) **archivado y verde** (tarea 0.1), porque C-22 reutiliza su patrón de esquemas en camelCase, de servicios con commit y de tests de integración con tokens reales. Si C-20 no está archivado, el apply se detiene. No se toman como fuente de verdad los archivos de C-20 que estén sin commitear.

## Decisiones registradas de la autora

- **D1–D12**: aprobadas con la recomendación del explore.
- **P1** (`durationMin` opcional): sí, D2.
- **P2** (la respuesta `201` trae solo el turno): sí, D3.
- **P3** (`GET /api/appointments/{id}` fuera de C-22): sí, D7. La corrección para `CHANGES.md` queda al final.
- **P4** (sin clave de idempotencia): sí, D12.
- **D9**: el test HTTP prueba el cableado y la fila única, no la concurrencia real; esa sigue en C-17.
- **D13**: C-20 archivado es precondición del apply.

## Risks / Trade-offs

- **[Riesgo] C-20 sin archivar** → D13 y tarea 0.1; si no está archivado, el apply se detiene.
- **[Riesgo] `startAt` sin zona horaria llega al dominio y produce `500`** → validación en el esquema Pydantic, `400` antes de construir `NewAppointmentRequest` (D2).
- **[Riesgo] `APP_TIMEZONE` inválida revienta al construir `ZoneInfo`** → riesgo menor de configuración; opcionalmente validarla al arrancar. No cambia el contrato.
- **[Riesgo] El `POST` reintentado crea un segundo turno** → D12: la UI deshabilita el envío; sin clave de idempotencia en el MVP.
- **[Riesgo] El test HTTP de carrera se interpreta como prueba de concurrencia** → D9: se documenta que C-17 es la prueba real con `pg_locks`.
- **[Riesgo] La ruta nueva no declara permiso y el guardián la detecta** → montarla bajo `protected_router` con `require_permission(APPOINTMENT, CREATE)` y correr `test_route_guards.py`.
- **[Riesgo] Un `409` mezclado con `422` por error de mapeo** → no reimplementar la tabla: usar `DomainRejectedError` y su manejador (D5).
- **[Trade-off] No hay `GET /api/appointments/{id}`** → el `201` ya devuelve el turno; si la UI necesita detalle, se suma a C-24 (corrección al final).

## Migration Plan

Sin migraciones. Rollback: revertir el commit del change.

## Correcciones de CHANGES.md para la autora

- Sumar al scope de C-24 `GET /api/appointments/{id}` si la UI necesita consultar un turno puntual. En C-22 no se implementa. **No se editó `CHANGES.md`.**
