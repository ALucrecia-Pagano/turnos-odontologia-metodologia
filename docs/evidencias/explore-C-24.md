# Explore C-24 — `api-consulta-de-agenda`

Fecha: 2026-11-06
Fase: 5 — API REST FastAPI y JWT
Governance: **BAJO** (según `CHANGES.md` §[C-24], línea 564)
Dependencias en `CHANGES.md`: `C-17`, `C-20`.

> Este explore es analítico: no ejecutó docker, pytest, alembic ni pip; no tocó código, tests, migraciones, specs, `CHANGES.md`, la KB ni creó la carpeta del change. Se hizo con C-21 **archivado**, C-22 y C-23 **no archivados** (sus `design.md` son la fuente de verdad) y `backend/app/api/appointments.py` con un `POST /api/appointments` a medio hacer que **no se tomó como fuente de verdad**. El apply de C-24 espera a C-21, C-22 y C-23 archivados y verdes.

---

## 1. Alcance de C-24 según `CHANGES.md` y qué queda afuera

### Qué entra en C-24

1. **`GET /api/agenda?from&to&professionalId&chairId`**: turnos del rango (día o semana) en hora local `APP_TIMEZONE`, filtrables por profesional y por sillón.
2. **Horarios de atención del rango**: la plantilla semanal por profesional para que la UI dibuje las columnas.
3. **Bloqueos del rango**: los bloqueos que se solapan con el rango, con su motivo, para que la UI los pinte.
4. **Respuesta enriquecida**: nombre del paciente, del profesional, del sillón y de la prestación en cada turno, sin que el front tenga que resolver ids con cuatro llamadas.
5. **RBAC**: `APPOINTMENT / READ_AGENDA` para los tres roles; el odontólogo lee **toda** la agenda en solo lectura (KB 03:22 y 36; C-19), sin filtro de propiedad.
6. **Traducción de errores**: `400` por parámetros inválidos o faltantes; `401` sin token; `403` por rol (teórico: los tres roles tienen la celda); `404` solo si se agrega `GET /api/appointments/{id}`. No hay `409` ni `422` de dominio en una lectura.
7. **Tests de integración**: filtros combinados, rango que cruza semanas, cancelados incluidos con su estado, borde de medianoche local.
8. **Opcional recomendado**: `GET /api/appointments/{id}` con el mismo alcance de agenda, para cerrar la deuda que dejaron C-22 y C-23.

### Qué queda explícitamente afuera

- **Altas, cancelaciones, reprogramaciones y cambios de estado**: son C-22 y C-23; C-24 es solo lectura.
- **Cálculo de disponibilidad**: C-24 dibuja la agenda y los bloqueos, no calcula huecos libres ni ofrece "próximo turno disponible".
- **Filtro por estado, paginación, exportación o búsqueda**: no están en el scope; el rango de un día o una semana es acotado. Un `includeCancelled` o `status` puede sumarse después.
- **`GET /api/appointments` como listado alternativo**: la ruta de C-24 es `/api/agenda` (ver D1); un alias con query params duplicaría contrato y tests.
- **Pantallas**: C-25 en adelante.
- **Cambios de dominio, esquema, migraciones o RBAC**: no hacen falta; la lectura reutiliza los modelos, repositorios y reglas ya cerrados.
- **ABM de usuarios**: C-19 lo cerró; la agenda no resuelve usuarios, solo profesionales, sillones, servicios y pacientes.
- **WebSockets, notificaciones o refresco en vivo**: el front refresca por polling; no está en el scope.
- **`note` en turnos o bloqueos**: no está modelado; C-24 no lo expone.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-24 reutiliza

| Pieza | Dónde | Qué ofrece |
|-------|-------|------------|
| `AppointmentRepository.list_for_professional_in_range` | `backend/app/repositories/appointment.py:134` | Turnos de un profesional en un rango, con solapamiento semiabierto y orden `(start_at, id)`; incluye todos los estados. |
| `AppointmentRepository.list_for_chair_in_range` | `backend/app/repositories/appointment.py:144` | Lo mismo por sillón. |
| `AppointmentRepository.get_by_id` | `backend/app/repositories/appointment.py:130` | Turno o `None`; sirve para el detalle. |
| `AppointmentModel` | `backend/app/db/models.py:123` | `patient_id`, `professional_id`, `chair_id`, `service_id`, `start_at`, `end_at`, `status`, `created_at`, `updated_at`; índices por `(professional_id, start_at)`, `(chair_id, start_at)` y `(status, start_at)`. |
| `BlockRepository.list_by_professional_in_range` | `backend/app/repositories/blocks.py:75` | Bloqueos de un profesional que se solapan con el rango, orden `(start_at, id)`. |
| `BlockRepository.list` | `backend/app/repositories/blocks.py:90` | Todos los bloqueos, orden `(start_at, id)`; sirve de base para el rango sin filtro. |
| `WorkingHoursRepository.list` | `backend/app/repositories/working_hours.py:73` | Plantilla semanal de todos los profesionales, orden `(professional_id, weekday, start_minute)`. |
| `WorkingHoursRepository.list_by_professional` | `backend/app/repositories/working_hours.py:65` | Plantilla semanal de un profesional, mismo orden. |
| `BlockModel`, `WorkingHoursModel`, `PatientModel` | `backend/app/db/models.py:100`, `:72`, `:55` | `reason`, `start_minute`/`end_minute` (0–1440), `full_name` del paciente; FKs no nulas. |
| `router` de turnos | `backend/app/api/appointments.py:19` | Prefijo `/appointments`, tag "Turnos", `POST` de C-22; es donde vive el detalle si se incluye. |
| `router` de horarios | `backend/app/api/working_hours.py:24` | Prefijo `/professionals`, tag "Horarios"; el patrón de GET con `Query` y `format_utc_iso`. |
| `router` de bloqueos | `backend/app/api/blocks.py:22` | GET/POST/DELETE con `BlockResponse`; el patrón de query params y de serialización. |
| `protected_router`, `require_permission` | `backend/app/api/deps.py:61`, `:105` | Autenticación común y autorización por celda de la matriz; `RequirePermission` es visible para los guardianes. |
| Matriz RBAC | `backend/app/auth/permissions.py:49` | `APPOINTMENT / READ_AGENDA` = `{odontólogo: ALL, recepción: ALL, admin: ALL}`; mensaje `"No tiene permiso para leer la agenda."` en `:86`. |
| `NotFoundError`, manejadores | `backend/app/api/errors.py:60`, `:66` | `404` con `{ "code": "NOT_FOUND", "message": ... }`; base del detalle. |
| `request_validation_handler` | `backend/app/api/errors.py:117` | `400` con `{ "errors": [{field, type, message}] }`; hoy mapea `missing` y `json_invalid` y cae a `"Dato inválido."`. |
| `permission_responses`, `not_found_responses` | `backend/app/api/openapi.py:75`, `:106` | Ejemplos y modelos de `403` y `404`; `setup_openapi` agrega `400` si hay parámetros y `401` si hay seguridad (`:123`). |
| `BlockResponse`, `WorkingHoursSlotResponse`, `BlocksQuery`, `AppointmentResponse`, `format_utc_iso` | `backend/app/api/schemas.py:232`, `:188`, `:251`, `:283`, `:13` | Formas camelCase, alias y serialización UTC con `Z`; C-24 reutiliza `BlockResponse` y el formateador. |
| `Settings.app_timezone` | `backend/app/config.py:26` | Zona configurada (`America/Argentina/Buenos_Aires`). |
| `main.py` | `backend/app/main.py:34-40` | Los routers de negocio se cuelgan de `protected_router` al importar; C-24 tiene que sumar el suyo ahí. |
| Harness de integración | `backend/tests/integration/conftest.py`, `auth_support.py`, `test_api_appointments.py:50-128` | PostgreSQL real, tokens reales, lunes futuro relativo, fixture de datos demo y `TRUNCATE` con el trigger de historial deshabilitado. |
| Contratos de C-21/C-22/C-23 | `openspec/changes/archive/2026-11-06-api-horarios-y-bloqueos/design.md`, `openspec/changes/api-dar-turno/design.md`, `openspec/changes/api-ciclo-de-vida-del-turno/design.md` | Fuente de verdad de horarios, bloqueos, alta y ciclo de vida; C-22 D7 y C-23 (`:263`) derivan el detalle puntual a C-24. |

### 2.2. Qué le falta a la base para servir `GET /api/agenda`

1. Una consulta de turnos **sin filtro** de profesional/sillón y una **combinada** (las dos actuales son excluyentes).
2. Los **nombres** de paciente, profesional, sillón y prestación con joins, para no hacer N+1 ni obligar al front a resolver cuatro catálogos.
3. Una consulta de bloqueos **sin filtro** de profesional (hoy solo hay "por profesional" o "todos", sin rango).
4. Un esquema de query con `from`/`to` locales obligatorios, rango máximo y filtros opcionales, y un esquema de respuesta con el sobre de la agenda.
5. Un servicio de lectura y un router nuevos; el detalle, si se incluye, en el router de turnos.
6. La validación de `400` para fechas inválidas, rango invertido y rango demasiado largo.
7. OpenAPI, guardianes de rutas y tests de integración/contrato.
8. La decisión de si el detalle `GET /api/appointments/{id}` entra en C-24.

### 2.3. Observaciones que condicionan el diseño

- **La agenda es de todos, incluso para el odontólogo.** `permissions.py:49` da `Scope.ALL` a los tres roles; KB 03:22 dice "R (todos, solo lectura)" y KB 03:36 explica que la agenda incluye horarios y bloqueos ajenos. No va `ensure_own_professional`.
- **El odontólogo ve la agenda completa pero no puede modificarla.** El `403` de `READ_AGENDA` es teórico porque los tres roles tienen la celda; el guardián sigue siendo obligatorio para que la ruta no nazca sin permiso.
- **KB 07 Flujo 5 dice `GET /api/appointments?from=&to=&professionalId=&chairId=`**, pero `CHANGES.md` §[C-24] fija `GET /api/agenda?...`. Hay que decidir y documentar la diferencia (D1); la KB no se edita en este explore.
- **Los turnos cancelados ya están en las consultas de rango**: las de C-17/C-21 no filtran por estado. La agenda los incluye con `status`; no hace falta una consulta nueva por estado.
- **El borde de medianoche está resuelto en el dominio**: `CROSSES_MIDNIGHT` compara el fin completo contra las 00:00 locales del día siguiente y **permite** un fin exacto a las 00:00 (`backend/app/domain/rules/same_day.py:16-45`; test `test_validate_new_appointment.py:982-998`). El horario de atención también admite `end_minute = 1440` (`backend/app/domain/rules/working_hours.py:206-218`). El test de borde puede crear un turno 23:30–00:00 por la API de C-22.
- **El rango se interpreta en hora local, no en UTC.** Si se usaran fechas UTC, un "día" en Buenos Aires empezaría a las 21:00 UTC del día anterior; la UI y KB 07 hablan de día/semana local (`APP_TIMEZONE`).
- **La agenda no necesita `now`.** El rango lo fija el cliente y la zona es configuración; no hay regla de pasado en una lectura. Eso hace los tests deterministas y evita `monkeypatch`.
- **La plantilla de horarios ya está ordenada** por `(professional_id, weekday, start_minute)`; no hace falta reordenar en el servicio.
- **Los bloqueos pueden cruzar la medianoche**; el predicado de solapamiento semiabierto los incluye en los dos días que tocan. Los turnos no pueden cruzar la medianoche, así que el borde solo importa para el fin a las 00:00 y el inicio a las 00:00.
- **No hay endpoint de detalle**: C-22 D7 y C-23 lo derivan explícitamente a C-24. Si no entra, el front tiene que contentarse con el `201`/`200` de las mutaciones y refrescar la agenda.
- **El `403` de la agenda no se puede probar con los roles actuales**: los tres tienen `READ_AGENDA`. El test de guardianes verifica que la ruta declare la celda; no hay un test de `403` real.
- **La privacidad ya está aceptada**: la agenda expone el nombre del paciente y los motivos de bloqueo de todos los profesionales al odontólogo; KB 03:36 y la decisión de C-19 lo aceptan. No se agregan DNI, teléfono ni historia clínica.

---

## 3. Decisiones de diseño (`D1`–`D18`)

### D1 — Endpoints, rutas, RBAC y la diferencia con KB 07

**Problema**: definir las rutas de C-24, colgarlas del guardián correcto y resolver el choque entre KB 07 (`/api/appointments`) y `CHANGES.md` (`/api/agenda`).

| # | Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores posibles |
|---|--------|------|------------------|------------|-----------|-------|-------|------------------|
| 1 | `GET` | `/api/agenda` | `APPOINTMENT` / `READ_AGENDA` | todos (solo lectura) | todos | todos | `200` | `400`, `401`, `403` |
| 2 | `GET` | `/api/appointments/{id}` (opcional, D9) | `APPOINTMENT` / `READ_AGENDA` | todos (solo lectura) | todos | todos | `200` | `400`, `401`, `403`, `404` |

- **Opción A (recomendada)**: `GET /api/agenda` para la vista compuesta y, si se acepta D9, `GET /api/appointments/{id}` para el detalle. Ambas con `require_permission(APPOINTMENT, READ_AGENDA)` y **sin** `ensure_own_professional`: el `Scope.ALL` de la celda es deliberado y coincide con KB 03:22/36 y C-19.
  - *Pros*: `/api/agenda` describe una vista que no es un simple listado de turnos (incluye horarios y bloqueos); evita la ambigüedad con `/api/appointments/{id}`; respeta `CHANGES.md`; el detalle reutiliza el mismo read model.
  - *Contras*: se aparta de la ruta que muestra KB 07 Flujo 5; hay que actualizar la KB en un change documental posterior (no en C-24).
- **Opción B**: `GET /api/appointments?from=&to=&professionalId=&chairId=`. Es la ruta de KB 07, pero "appointments" sugiere solo turnos, no el sobre con horarios y bloqueos; además convive mal con `GET /api/appointments/{id}` (el mismo prefijo para un listado y un detalle) y con el `POST` de C-22.
- **Opción C**: exponer las dos rutas como alias. Duplica contrato, OpenAPI, tests y superficie de error sin aportar; no se recomienda.
- **Recomendación**: **A**. `GET /api/agenda` con tag "Agenda"; el detalle, si entra, con tag "Turnos" en `backend/app/api/appointments.py` (D9). La diferencia con KB 07 se documenta acá y se corrige en la KB cuando la autora lo pida; no se edita `knowledge-base/`.

### D2 — Ventana temporal: fechas locales obligatorias, `to` inclusivo, máximo 31 días

**Problema**: definir qué significan `from` y `to`, si son fechas o instantes, si `to` es inclusivo y qué rango se acepta.

- **Opción A (recomendada)**:
  - `from` y `to` son **fechas locales** `YYYY-MM-DD` en `APP_TIMEZONE`, **obligatorias**.
  - `to` es **inclusivo**: `from=2026-11-09&to=2026-11-15` son los 7 días locales del 9 al 15.
  - El servidor calcula el rango de instantes `[from 00:00 local, (to + 1 día) 00:00 local)` con `datetime.combine(..., tzinfo=tz)`.
  - Rango máximo: **31 días inclusivos** (`(to - from).days + 1 <= 31`). Un día, una semana y un mes entran; un rango mayor se rechaza con `400`.
  - `to < from` → `400 invalid_range_order` ("La fecha final no puede ser anterior a la inicial."); más de 31 días → `400 invalid_range_length` ("El rango no puede superar los 31 días.").
  - Fecha con formato distinto de `YYYY-MM-DD` o calendario inválido → `400 invalid_date_format` ("La fecha debe tener formato AAAA-MM-DD."). Un instante ISO completo (`2026-11-09T00:00:00-03:00`) se rechaza para no interpretar la hora en dos zonas.
  - Falta `from` o `to` → `400 missing` ("Falta este dato.").
  - *Pros*: la UI pide "día" o "semana" con la misma semántica que KB 07; el cliente no calcula medianoches ni zonas; el servidor es el único que interpreta `APP_TIMEZONE`; el rango acotado protege la consulta.
  - *Contras*: el contrato no acepta instantes ISO como C-21; un cliente que quiera un rango parcial de horas no puede pedirlo (no está en el scope).
- **Opción B**: `from`/`to` como instantes ISO con offset, estilo C-21. Da máxima flexibilidad, pero obliga al front a calcular las medianoches locales, permite rangos arbitrarios y hace que "día" dependa de la zona que mande el cliente; más errores y tests.
- **Opción C**: `from`/`to` opcionales con defaults (hoy / hoy + 6). Ahorra dos parámetros, pero oculta errores, introduce un reloj en una lectura y hace que los tests dependan de la fecha actual; no se recomienda.
- **Recomendación**: **A**. Es la semántica de KB 07 y de `CHANGES.md` ("día o semana, en hora local"). El máximo de 31 días es una decisión de C-24, fácil de bajar a 7 si la autora prefiere; 31 permite un mes y el test de "rango que cruza semanas".

### D3 — Filtros `professionalId` y `chairId`: opcionales, combinables, id inexistente = lista vacía

**Problema**: decidir si los filtros son obligatorios, cómo se combinan y qué pasa con un id que no existe.

- **Opción A (recomendada)**:
  - `professionalId` y `chairId` son **opcionales** y **combinables con AND**: `professionalId=P1&chairId=S1` devuelve solo los turnos de P1 en S1.
  - Un id **inexistente** no es un error: devuelve `200` con la lista de turnos vacía. Es un filtro, no un recurso de la ruta; el `404` queda para `/api/appointments/{id}`.
  - `professionalId` también filtra los horarios y los bloqueos (son por profesional). `chairId` **no** filtra horarios ni bloqueos (no son por sillón): la vista de un sillón necesita los horarios de todos los profesionales para dibujar.
  - `professionalId` inexistente deja `appointments`, `workingHours` y `blocks` vacíos; `chairId` inexistente deja `appointments` vacío pero mantiene horarios y bloqueos (del profesional si se filtró, de todos si no).
  - UUID malformado → `400` automático de Pydantic, con `field` `"professionalId"`/`"chairId"`.
  - *Pros*: el front puede mantener un filtro "viejo" sin romper la pantalla; el `404` se reserva a recursos; la semántica de cada lista es explícita.
  - *Contras*: un id inexistente no avisa que el catálogo está desactualizado; la UI debe mostrar el vacío.
- **Opción B**: `404` si el profesional o el sillón no existen. Trata un filtro como un recurso de path y obliga a la UI a distinguir "no hay turnos" de "el filtro ya no existe"; no se recomienda.
- **Opción C**: `422 UNKNOWN_REFERENCE`. Es el código de las referencias del **cuerpo** (C-22), no de un filtro de query; confunde dos capas.
- **Recomendación**: **A**. Los filtros son opcionales y combinables; el id inexistente devuelve listas vacías. `extra="forbid"` en el modelo de query es defensivo; FastAPI ignora parámetros de query no declarados, así que **no se promete** un `400` por un nombre desconocido (si se quisiera, haría falta una dependencia que inspeccione `request.query_params`, fuera de scope).

### D4 — Sobre de respuesta y turnos enriquecidos

**Problema**: definir la forma de la respuesta y si los turnos llevan nombres o solo ids.

- **Opción A (recomendada)**: un sobre único:
  ```json
  {
    "from": "2026-11-09",
    "to": "2026-11-15",
    "timezone": "America/Argentina/Buenos_Aires",
    "appointments": [
      {
        "id": "…",
        "patientId": "…",
        "patientName": "Ana Pérez",
        "professionalId": "…",
        "professionalName": "Dra. Laura Quiroga",
        "chairId": "…",
        "chairName": "Sillón 1",
        "serviceId": "…",
        "serviceName": "Control",
        "startAt": "2026-11-09T13:00:00Z",
        "endAt": "2026-11-09T13:30:00Z",
        "status": "reservado"
      }
    ],
    "workingHours": [
      { "professionalId": "…", "weekday": 1, "start": "09:00", "end": "13:00" }
    ],
    "blocks": [
      {
        "id": "…",
        "professionalId": "…",
        "startAt": "2026-11-09T16:00:00Z",
        "endAt": "2026-11-09T17:00:00Z",
        "reason": "Congreso"
      }
    ]
  }
  ```
  - `appointments` usa `AgendaAppointmentResponse` (ids + nombres + `startAt`/`endAt` UTC con `Z` + `status`).
  - `workingHours` usa `AgendaWorkingHoursResponse` (`professionalId`, `weekday` 1–7, `start`/`end` `HH:MM`, con `24:00` posible).
  - `blocks` reutiliza `BlockResponse` de C-21 (`id`, `professionalId`, `startAt`, `endAt`, `reason`).
  - `from`/`to` repiten la ventana pedida y `timezone` dice en qué zona se interpretaron; el front no tiene que adivinar.
  - *Pros*: una sola llamada dibuja la agenda completa; evita N+1 en el cliente; el contrato es autoexplicativo; los nombres salen de un join en el servidor.
  - *Contras*: la respuesta es más grande que un listado de ids; el front que solo quiere turnos ignora dos listas.
- **Opción B**: devolver `AppointmentResponse` de C-22 (ids, sin nombres). El front tendría que cruzar cuatro catálogos y resolver el paciente; más llamadas y más lógica de UI; no cumple "para que la UI los dibuje" con una sola consulta.
- **Opción C**: agrupar por profesional (`{ professional, workingHours, blocks, appointments }`). Se parece a las columnas de la UI, pero acopla el contrato a una disposición visual, complica los filtros y duplica el nombre del profesional en cada grupo; no se recomienda.
- **Recomendación**: **A**. El sobre plano es el más simple de testear y de consumir; los nombres se resuelven con joins (D10), no con consultas por fila. `timezone` es un campo de una palabra, sin camelCase.

### D5 — Horarios de atención: plantilla semanal, filtrada por profesional, no por sillón

**Problema**: decidir si la agenda devuelve la plantilla semanal o los horarios expandidos por día, y de qué profesionales.

- **Opción A (recomendada)**: devolver la **plantilla semanal** de `WorkingHoursRepository.list()` (sin filtro) o `list_by_professional(professionalId)` (con filtro), con `professionalId`, `weekday` (1–7), `start` y `end` (`HH:MM`, `end` puede ser `24:00`). Incluye a todos los profesionales, activos o no; `chairId` no la filtra. El orden ya viene por `(professional_id, weekday, start_minute)`.
  - *Pros*: reutiliza C-21 tal cual; la UI expande una semana o un día; no duplica entradas por fecha; el test es directo.
  - *Contras*: para una vista de un solo día, el front tiene que filtrar por `weekday`; es trivial.
- **Opción B**: expandir por fecha: una entrada por cada día del rango (`date`, `professionalId`, `start`, `end`). Es más directo para un día, pero genera hasta 7×N entradas por semana, duplica la plantilla y obliga a decidir qué hacer con los feriados o excepciones (que no existen en el modelo); no se recomienda.
- **Opción C**: devolver solo los horarios de los profesionales que tienen turnos en el rango. Rompe la vista de una agenda vacía o de una columna sin turnos: la UI no podría dibujar el horario. No se recomienda.
- **Recomendación**: **A**. La plantilla semanal es el contrato de C-21 y es suficiente para dibujar; si la autora prefiere la vista expandida, es un cambio pequeño en el servicio, pero agrega contrato y tests sin necesidad.

### D6 — Bloqueos del rango: solapamiento, todos por defecto, filtrados por profesional, no por sillón

**Problema**: decidir qué bloqueos entran, cómo se filtran y si el motivo se expone.

- **Opción A (recomendada)**:
  - Todos los bloqueos que **se solapan** con `[from, to)` con el predicado semiabierto `start_at < to_end AND end_at > from_start`.
  - Sin filtro, todos los profesionales; con `professionalId`, solo los de ese profesional. `chairId` no los filtra (los bloqueos son por profesional).
  - Un bloqueo que empieza el día anterior y termina dentro del rango **entra** (puede cruzar la medianoche); uno que empieza dentro y termina después, también.
  - Se devuelve `reason` (puede ser `null`) y se reutiliza `BlockResponse`.
  - Incluye bloqueos de profesionales inactivos (D14).
  - *Pros*: la UI puede pintar por qué un tramo no está disponible; el solapamiento es el mismo criterio de C-21; una sola consulta.
  - *Contras*: el odontólogo ve motivos de bloqueos ajenos; ya está aceptado en KB 03:36 y C-19.
- **Opción B**: solo los bloqueos **contenidos** en el rango. Un bloqueo que empieza la noche anterior y cubre la mañana desaparecería de la vista; el dibujo quedaría incompleto.
- **Opción C**: solo los bloqueos del profesional filtrado y ninguno cuando no hay filtro. La vista de un sillón o la agenda global perderían los motivos; no se recomienda.
- **Recomendación**: **A**. Solapamiento semiabierto, filtro por profesional, `reason` visible. El test cubre un bloqueo que cruza la medianoche y un `chairId` que no lo filtra.

### D7 — Estados: todos, incluidos los cancelados, sin filtro de estado; orden estable

**Problema**: decidir si la agenda oculta los cancelados, si agrega un filtro de estado y en qué orden salen turnos, bloqueos y horarios.

- **Opción A (recomendada)**:
  - Incluir **todos** los estados (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`) con el `status` actual; no agregar `status` ni `includeCancelled` en C-24.
  - La UI puede ocultar los cancelados en el cliente si quiere; el contrato de `CHANGES.md` pide "turnos cancelados incluidos con su estado".
  - Orden: `appointments` por `(start_at, id)`; `blocks` por `(start_at, id)`; `workingHours` por `(professionalId, weekday, start)`.
  - *Pros*: una sola llamada muestra la historia del día; los cancelados no ocupan agenda para el alta (C-22) pero sí son parte de la vista; el orden es determinista y testeable.
  - *Contras*: una semana con muchos cancelados puede crecer; el front filtra.
- **Opción B**: excluir los cancelados por defecto. Ahorra filas, pero contradice la consigna y obliga a una segunda llamada para verlos; no se recomienda.
- **Opción C**: agregar `status` o `includeCancelled` ahora. Es un contrato más y más tests; no está en el scope. Se puede sumar después sin romper la respuesta actual.
- **Recomendación**: **A**. Todos los estados, cancelados incluidos, sin filtro; orden estable. Si el volumen lo justifica, un change posterior agrega `includeCancelled=false` por defecto.

### D8 — Borde de medianoche y solapamiento del rango

**Problema**: decidir a qué día pertenece un turno que termina a las 00:00, uno que empieza a las 00:00 y un bloqueo que cruza la medianoche.

- **Opción A (recomendada)**:
  - El rango es semiabierto `[from 00:00 local, to+1 00:00 local)`.
  - Solapamiento: `start_at < to_end AND end_at > from_start`.
  - Un turno que **termina exactamente a las 00:00 locales** pertenece al día anterior: para el día siguiente, `end_at == from_start`, así que `end_at > from_start` es falso y no aparece.
  - Un turno que **empieza a las 00:00 locales** pertenece a ese día: para el día anterior, `start_at == to_end`, así que `start_at < to_end` es falso y no aparece.
  - Un bloqueo que cruza la medianoche aparece en los dos días que toca (el predicado lo incluye en ambos); la UI lo recorta visualmente.
  - El servidor calcula las medianoches locales con `datetime.combine(fecha, time.min, tzinfo=tz)`; no usa UTC para decidir el día.
  - *Pros*: coincide con la regla de dominio (`same_day.py:21-34` permite el fin exacto a las 00:00) y con el intervalo semiabierto de DD-07; el test de borde es directo; no hay doble conteo.
  - *Contras*: el cliente tiene que entender que `to` es inclusivo y que el turno de las 23:30–00:00 se ve en el día que empieza; se documenta en OpenAPI.
- **Opción B**: comparar solo la fecha local de `start_at`. Para turnos es equivalente (no cruzan la medianoche), pero para bloqueos es incorrecto: un bloqueo que empieza la noche anterior no aparecería en el día que cubre. No se recomienda.
- **Opción C**: truncar a minutos. El dominio compara el fin completo, incluidos segundos y fracciones (`same_day.py:19-21`); truncar podría tratar distinto un fin a las `00:00:30` y se aparta de la regla ya probada. No se recomienda.
- **Recomendación**: **A**. Predicado semiabierto y medianoches locales; tests para 23:30–00:00 y 00:00–00:30. El test de la regla de dominio ya existe (`termina-justo-a-la-medianoche`); C-24 prueba el borde en la lectura.

### D9 — `GET /api/appointments/{id}`: incluirlo en C-24

**Problema**: C-22 D7 y C-23 dejaron el detalle puntual fuera y lo derivaron a C-24; hay que decidir si entra y con qué permiso.

- **Opción A (recomendada)**: incluirlo en C-24:
  - `GET /api/appointments/{id}` con `APPOINTMENT / READ_AGENDA` (mismo alcance de agenda, `Scope.ALL`, sin propiedad).
  - `200` con `AgendaAppointmentResponse` (el mismo turno enriquecido del sobre).
  - `404` con `NotFoundError("Turno no encontrado.")` si no existe.
  - `400` por UUID de path inválido; `401` sin token; `403` teórico.
  - Reutiliza el read model y el servicio de agenda; no necesita `now` ni `tz`.
  - *Pros*: cierra la deuda de C-22/C-23; el front puede abrir un detalle o refrescar un turno puntual; el costo es bajo (una consulta con el mismo join).
  - *Contras*: agranda el scope de C-24 y toca `api/appointments.py` (C-22), aunque C-22 ya estará archivado.
- **Opción B**: no incluirlo; C-24 queda solo con `GET /api/agenda`. El front usa el `201`/`200` de las mutaciones y refresca la agenda; no hay deep link ni detalle puntual. Es seguro y no bloquea C-25, pero deja la deuda.
- **Opción C**: incluirlo con `APPOINTMENT_HISTORY / READ` o con comparación de propiedad. Le daría al odontólogo solo sus turnos, contradiciendo la agenda completa (KB 03:22/36) y la observación de C-23 (`design.md:83`). No se recomienda.
- **Recomendación**: **A**. El detalle es barato y consistente con la agenda; si la autora prefiere el scope mínimo, **B** es una salida limpia y nada más depende de la ruta. La recomendación fuerte es A.

### D10 — Repositorios y read model: una consulta con joins, filtros opcionales, sin N+1 ni migración

**Problema**: cómo leer turnos, nombres, bloqueos y horarios sin duplicar consultas ni agregar esquema.

- **Opción A (recomendada)**:
  - En `backend/app/repositories/appointment.py`, un dataclass congelado `AppointmentWithNames` (turno + `patient_name`, `professional_name`, `chair_name`, `service_name`).
  - `AppointmentRepository.list_for_agenda_in_range(start_at, end_at, professional_id=None, chair_id=None)`:
    - `select(AppointmentModel, PatientModel.full_name, ProfessionalModel.full_name, ChairModel.name, ServiceModel.name)` con **inner joins** (las FKs son no nulas, `models.py:136-156`).
    - `where(AppointmentModel.start_at < end_at, AppointmentModel.end_at > start_at)`.
    - `where` opcional por `professional_id` y `chair_id`.
    - `order_by(AppointmentModel.start_at, AppointmentModel.id)`.
  - `AppointmentRepository.get_with_names(identifier)` con el mismo `select` y `where(AppointmentModel.id == identifier)`; `None` si no existe.
  - `BlockRepository.list_in_range(start_at, end_at, professional_id=None)` con el mismo predicado y `order_by(start_at, id)`; `list_by_professional_in_range` puede delegar o quedarse como está para C-21.
  - Horarios: reutilizar `WorkingHoursRepository.list()` / `list_by_professional(id)` sin cambios.
  - Total: **3 consultas** por agenda (turnos, bloqueos, horarios) y **1** por detalle; no hay N+1.
  - *Pros*: una sola consulta por lista; los nombres viajan con el turno; tipado estricto; sin migración; los índices existentes ayudan cuando hay filtro de profesional o sillón.
  - *Contras*: el `select` con cinco columnas es más ancho que un `select(AppointmentModel)`; es el precio de evitar N+1.
- **Opción B**: leer los turnos con las consultas actuales y resolver cada nombre con una consulta por fila. Es N+1, más lento y más código; no se recomienda.
- **Opción C**: crear una vista/materialized view o una consulta con agregación JSON. Da una sola fila y un snapshot, pero agrega esquema, migración y SQL difícil de testear; para 2–5 profesionales y un rango de una semana es overkill. No se recomienda.
- **Recomendación**: **A**. `AppointmentModel` ya tiene los índices `(professional_id, start_at)`, `(chair_id, start_at)` y `(status, start_at)`; la consulta sin filtro hace un scan de una tabla chica. No se agregan índices ni migraciones en C-24. Si el volumen crece, un change posterior puede sumar `ix_appointment_start_at` o un índice GiST de rango.

### D11 — Organización del código y transacción: servicio de lectura y routers delgados

**Problema**: dónde viven la lógica, los esquemas y las rutas, y quién confirma.

- **Opción A (recomendada)**:
  - `backend/app/services/agenda.py`: dataclasses `Agenda` y `AgendaAppointment`; `get_agenda(session, from_date, to_date, professional_id, chair_id, tz)` y `get_agenda_appointment(session, identifier)`.
  - El servicio calcula las medianoches locales, llama a los repositorios, mapea `AppointmentWithNames` → `AgendaAppointment` y devuelve `Agenda` con `WorkingHours`/`Block` del dominio.
  - `backend/app/api/agenda.py`: `APIRouter(prefix="/agenda", tags=["Agenda"])`, `GET ""`, `response_model=AgendaResponse`, `require_permission(APPOINTMENT, READ_AGENDA)`, `ZoneInfo(settings.app_timezone)`, `format_utc_iso` y el formateo `HH:MM`.
  - `GET /api/appointments/{id}` en `backend/app/api/appointments.py` (prefijo `/appointments`, tag "Turnos"), con `NotFoundError("Turno no encontrado.")`.
  - `backend/app/main.py`: `from app.api.agenda import router as agenda_router` y `protected_router.include_router(agenda_router)` junto a los demás (`main.py:34-40`).
  - La ruta **no** hace `commit` ni `rollback`: es solo lectura; `get_db_session` cierra/rollbackea al salir.
  - *Pros*: mantiene el patrón de C-20/C-21 (servicio + router delgado); el servicio se testea sin FastAPI; el router solo serializa; el detalle comparte el read model.
  - *Contras*: agrega un módulo de servicio; es una lectura simple, pero la lógica de ventana y mapeo justifica separarla.
- **Opción B**: todo en el router con los repositorios. Es aceptable para una lectura, pero deja la lógica de fechas, el mapeo y los nombres en la capa HTTP; el test de servicio no existe y el router crece.
- **Opción C**: meter la agenda en `services/availability.py` (C-21). Ese servicio es de escritura de horarios/bloqueos y turnos afectados; la agenda es un read model distinto; mezclarlos confunde responsabilidades. No se recomienda.
- **Recomendación**: **A**. Servicio de lectura `agenda.py`, router `agenda.py`, detalle en `appointments.py`, inclusión en `main.py`, sin transacción de escritura.

### D12 — Errores y validación: `400` con mensajes explicativos, sin `404`/`422` para filtros

**Problema**: traducir fechas inválidas, rango invertido, rango demasiado largo y filtros inexistentes sin romper el contrato de errores de C-20.

- **Opción A (recomendada)**:
  - `AgendaQuery` con `from_date: date` (alias `from`), `to_date: date` (alias `to`), `professional_id: UUID | None` (alias `professionalId`), `chair_id: UUID | None` (alias `chairId`), `extra="forbid"`.
  - Validador de campo `mode="before"` para `from`/`to`: solo `^\d{4}-\d{2}-\d{2}$`, luego `date.fromisoformat`; si falla, `PydanticCustomError("invalid_date_format", "La fecha debe tener formato AAAA-MM-DD.")`.
  - Validador de modelo `mode="after"`: `to < from` → `PydanticCustomError("invalid_range_order", "La fecha final no puede ser anterior a la inicial.")`; `(to - from).days + 1 > 31` → `PydanticCustomError("invalid_range_length", "El rango no puede superar los 31 días.")`.
  - Agregar esas tres claves a `MALFORMED_MESSAGES` en `backend/app/api/errors.py:110`; el handler sigue devolviendo `{ "errors": [{field, type, message}] }` con `400`.
  - Falta `from`/`to` → `missing` ("Falta este dato."); UUID inválido → `400` automático con `field` del filtro.
  - No hay `404` ni `422` para filtros inexistentes (D3); no hay `409`/`422` de dominio en esta lectura.
  - *Pros*: mensajes en español que explican el rango; el contrato de `400` de C-20 no cambia; los errores de campo (fecha/UUID) traen `field`; los de modelo traen `field: null` y el mensaje explica.
  - *Contras*: agregar tres claves a `MALFORMED_MESSAGES` toca un archivo compartido; es un cambio aditivo, sin efecto en las rutas existentes. Los errores de modelo no pueden nombrar un campo único porque afectan a ambos; `field: null` es aceptable.
- **Opción B**: validar en el router y lanzar `NotFoundError`/`DomainRejectedError`. Semánticamente incorrecto: el rango no es un recurso ni una regla de negocio; además mezcla capas.
- **Opción C**: devolver `422` con un `ViolationCode` nuevo. El `422` es para reglas de dominio; un rango de query es entrada malformada; agregar un código de dominio para una preocupación de API ensucia el dominio. No se recomienda.
- **Recomendación**: **A**. Los tres tipos custom + `MALFORMED_MESSAGES`; `400` para todo lo malformado; `404` solo para el detalle. Nota: no se promete un `400` por un parámetro de query desconocido, porque FastAPI lo ignora; `extra="forbid"` es defensivo (D3).

### D13 — Zona horaria y reloj: `APP_TIMEZONE`, sin `now`, UTC `Z` y horas locales `HH:MM`

**Problema**: evitar `datetime` naive, interpretar bien el día local y no depender del reloj en una lectura.

- **Opción A (recomendada)**:
  - `tz = ZoneInfo(settings.app_timezone)` (fallback `"America/Argentina/Buenos_Aires"`, como C-21).
  - `start = datetime.combine(from_date, time.min, tzinfo=tz)`; `end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz)`.
  - Turnos y bloqueos se serializan con `format_utc_iso` (`api/schemas.py:13`), siempre en UTC con `Z`; los horarios de atención se serializan en `HH:MM` local (con `24:00` posible).
  - La respuesta incluye `timezone` para que el front sepa en qué zona se interpretó el rango.
  - No se llama `datetime.now()`; la agenda no tiene regla de pasado y el rango lo fija el cliente.
  - *Pros*: cumple DD-07/SU-01; el día local es el de Buenos Aires, no UTC; los tests no dependen del reloj; los instantes no se guardan ni se devuelven naive.
  - *Contras*: el front tiene que mostrar los instantes en la zona que indica `timezone` (o en la del usuario); es lo esperado.
- **Opción B**: usar fechas UTC para el rango. Un "día" en Buenos Aires empezaría a las 21:00 UTC del día anterior; la vista diaria y KB 07 quedarían mal. No se recomienda.
- **Opción C**: aceptar `tz` o `now` del cliente. El cliente puede mentir y el contrato se vuelve inconsistente; no hace falta. No se recomienda.
- **Recomendación**: **A**. `ZoneInfo`, medianoches locales, UTC `Z`, `HH:MM` local y `timezone` en el sobre; sin reloj.

### D14 — Profesionales y sillones inactivos: incluirlos en la agenda

**Problema**: decidir qué pasa con turnos, horarios y bloqueos de recursos desactivados.

- **Opción A (recomendada)**: incluirlos. Un turno creado antes de desactivar un profesional o un sillón sigue existiendo y debe verse; sus horarios y bloqueos también, para explicar por qué no se puede dar un turno nuevo. La UI puede atenuar u ocultar la columna usando el `active` del catálogo de C-20. No hay filtro de activos en la consulta.
  - *Pros*: no se pierde historia ni se rompe la vista; el `active` es una decisión de presentación; los turnos nuevos para inactivos ya los rechaza C-22 (`INACTIVE_REFERENCE`).
  - *Contras*: la agenda puede mostrar columnas de profesionales inactivos; el front las filtra con el catálogo.
- **Opción B**: excluir a los inactivos por completo. Oculta turnos existentes y motivos de bloqueo; la recepción no puede ver por qué un hueco está ocupado. No se recomienda.
- **Opción C**: incluir turnos pero excluir horarios/bloqueos de inactivos. Inconsistente: un turno aparecería sin su horario o su bloqueo. No se recomienda.
- **Recomendación**: **A**. Incluir todo; el catálogo de C-20 aporta `active` para que la UI decida. Test opcional: crear un turno, desactivar el profesional/sillón y verificar que sigue en la agenda.

### D15 — Consistencia, concurrencia y performance: lectura simple, sin locks ni migración

**Problema**: decidir si las tres consultas necesitan un snapshot único, locks o índices nuevos.

- **Opción A (recomendada)**: una sesión/transacción por request, tres sentencias bajo `READ COMMITTED` (el default), sin locks. Si un turno o un bloqueo se escribe entre la consulta de turnos y la de bloqueos, la respuesta puede reflejar un instante ligeramente distinto; para una agenda de 2–5 profesionales y un día/semana es aceptable y la UI refresca. No se agregan índices ni migraciones: los índices existentes cubren los filtros por profesional/sillón; la consulta sin filtro es un scan de una tabla chica.
  - *Pros*: simple, sin contención, sin migración; el patrón es el de C-20/C-21; los tests de concurrencia de C-17/C-21 siguen siendo la prueba real de las escrituras.
  - *Contras*: no hay snapshot único entre las tres listas; un cambio concurrente puede verse a medias. Se acepta por el volumen y el uso (vista de agenda, no auditoría).
- **Opción B**: `REPEATABLE READ` para el request. Da un snapshot consistente, pero cambia el aislamiento de la sesión (global o por request), agrega complejidad y no es necesario para una lectura que se refresca.
- **Opción C**: una sola consulta con CTEs/JSON o una vista materializada. Un snapshot y una sola ida a la base, pero SQL complejo, específico del motor y difícil de testear; overkill. No se recomienda.
- **Recomendación**: **A**. Lectura simple, sin locks ni migración; documentar el trade-off. Si el volumen crece, un change posterior evalúa `REPEATABLE READ` o índices de rango.

### D16 — Tests: integración con tokens reales, fechas relativas y turnos creados por la API

**Problema**: cómo probar la agenda sin mocks, sin reloj fijo y sin depender de datos reales.

- **Opción A (recomendada)**:
  - `backend/tests/integration/test_api_agenda.py`, con `auth_client`/`test_engine`, `token_for` (login real) y un fixture autouse que:
    - siembra los datos demo (`PROFESSIONALS`, `CHAIRS`, `SERVICES`, `PATIENTS`) y reactiva P1/P2, como `test_api_appointments.py:65-98`;
    - deshabilita el trigger de `appointment_status_change` y trunca `appointment_status_change, appointment, block, working_hours CASCADE` (como `test_api_appointments.py:100-115`);
    - inserta horarios de lunes 00:00–24:00 para P1 y P2 (para el borde de medianoche; el test normal usa las 10:00/11:00/12:00).
  - `get_future_monday()` relativo (copiar/importar el de `test_api_appointments.py:50`); nunca fechas fijas.
  - Turnos de prueba: **API de C-22** (`POST /api/appointments`) con tokens reales; cancelaciones: **API de C-23** (`POST /api/appointments/{id}/cancel`); bloqueos: **API de C-21** (`POST /api/professionals/{id}/blocks`) para probar el `reason`; horarios: el fixture por SQL (setup) o la API de C-21 si se quiere probar el `PUT`.
  - Sin `monkeypatch`, sin `dependency_overrides`, sin mocks; la agenda no usa `now`, así que no hay reloj que fijar.
  - Tests mínimos:
    1. Turno normal: nombres, `startAt`/`endAt` en UTC `Z`, `status`, `from`/`to`/`timezone`.
    2. Filtros combinados: 4 turnos (P1/S1, P2/S2, P1/S2, P2/S1) y las 4 combinaciones de filtros.
    3. Rango que cruza semanas: turno en L y en L+7; `from=L&to=L+7` (8 días); ambos.
    4. Cancelados: crear, cancelar con recepción, ver el turno con `status: "cancelado"`.
    5. Borde de medianoche: 23:30–00:00 y 00:00–00:30; consultar L y L+1; cada uno aparece en el día correcto y no en el otro.
    6. Horarios y bloqueos: plantilla de P1/P2, bloqueo con motivo, filtro por profesional, `chairId` no filtra bloqueos/horarios, bloqueo que cruza la medianoche.
    7. Odontólogo ve todo: turno de P2, token de odontólogo (P1), `200` y el turno aparece.
    8. Inactivos (opcional): crear turno, desactivar profesional/sillón, sigue en la agenda.
    9. Filtro inexistente: `professionalId`/`chairId` aleatorio, `200` con listas vacías según D3.
    10. `400`: falta `from`, falta `to`, fecha inválida, `to < from`, >31 días, UUID inválido; mensajes/tipos.
    11. `401` sin token.
    12. Agenda vacía: `200`, `appointments: []`, horarios/bloqueos presentes.
    13. Detalle (si D9): `200` enriquecido, `404` `"Turno no encontrado."`, `401`, y odontólogo leyendo un turno de P2.
  - Tests unitarios `backend/tests/api/test_agenda_schemas.py`: `AgendaQuery` válido, faltantes, fecha inválida, orden, máximo, alias y `model_dump(by_alias=True)` del sobre.
  - OpenAPI `backend/tests/api/test_agenda_openapi.py`: paths, tags, parámetros requeridos/opcionales, respuestas y `$ref` a `AgendaResponse`/`AgendaAppointmentResponse`.
  - Correr `tests/api/test_route_guards.py` para las rutas nuevas.
  - *Pros*: prueba el contrato HTTP real, el RBAC, los tokens, los `400` y el borde; el harness ya existe; no depende del reloj.
  - *Contras*: los tests de integración son más lentos y requieren PostgreSQL; el fixture tiene que respetar el trigger de historial y el orden de siembra.
- **Opción B**: probar solo repositorios/servicio con una sesión falsa. No prueba OpenAPI, RBAC, `400`, tokens ni el cableado de FastAPI; el proyecto ya tiene el harness de integración. No se recomienda.
- **Opción C**: fechas fijas o `monkeypatch` del reloj. Se rompe cuando pasan las fechas y el proyecto prohíbe `dependency_overrides`/mocks internos; no se recomienda.
- **Recomendación**: **A**. Integración con tokens y fechas relativas; unitarios de esquema y OpenAPI. El test de medianoche es el que más justifica el fixture de horario completo.

### D17 — Documentación OpenAPI y guardianes

**Problema**: documentar las rutas nuevas sin romper los guardianes de C-18/C-19.

- **Opción A (recomendada)**:
  - `GET /api/agenda`: `response_model=AgendaResponse`, `status_code=200`, tag "Agenda", `responses={**permission_responses()}`; los parámetros salen del modelo de query: `from`/`to` requeridos, `professionalId`/`chairId` opcionales. `setup_openapi` agrega `400` (hay parámetros) y `401` (hay seguridad).
  - `GET /api/appointments/{id}`: `response_model=AgendaAppointmentResponse`, tag "Turnos", `responses={**not_found_responses("Turno"), **permission_responses()}`; `400` y `401` automáticos.
  - El `require_permission` debe ser visible para `tests/api/test_route_guards.py` (usar `Depends(require_permission(...))`, como las demás rutas).
  - No se documentan `409`/`422` de dominio; no hay. El `403` es teórico (los tres roles tienen `READ_AGENDA`) pero se mantiene por uniformidad.
  - *Pros*: el contrato queda completo; los guardianes siguen pasando; el front ve los parámetros y los errores.
  - *Contras*: el ejemplo de `403` de `permission_responses()` dice "No tiene permiso para dar turnos." (el genérico de C-22); no se personaliza porque la celda no se rechaza en la práctica.
- **Opción B**: dejar solo los modelos por defecto de FastAPI. El `400`/`401`/`403`/`404` no queda documentado y los guardianes pueden fallar; no se recomienda.
- **Opción C**: documentar solo `200`. Peor; el front no conoce los errores.
- **Recomendación**: **A**. Coherente con C-20/C-21/C-22 y verificable con los tests de OpenAPI.

### D18 — Precondiciones, secuencia y no-goals

**Problema**: decidir cuándo se puede aplicar C-24 y qué no se toca.

- **Opción A (recomendada)**:
  - Dependencias formales de `CHANGES.md`: `C-17` (persistencia de turnos) y `C-20` (API base) archivados y verdes.
  - Precondición de **tests/reutilización**: C-21 (horarios/bloqueos), C-22 (alta) y C-23 (ciclo de vida) archivados y verdes. C-24 reutiliza el router de C-22 para el detalle, los repositorios/modelos de C-21 y las rutas de C-22/C-23 en los tests.
  - Después de C-24, C-25 (frontend base) queda desbloqueado; es el GATE 14 (`C-22`, `C-23`, `C-24`).
  - No se editan `CHANGES.md`, la KB, `AGENTS.md`, `CLAUDE.md`, specs ni migraciones en el explore; el apply solo agrega el servicio, el router, los esquemas y los tests.
  - *Pros*: los tests usan las rutas reales de alta/cancelación/bloqueo; no se duplican fixtures; el detalle reutiliza el router ya probado; el orden del roadmap se respeta.
  - *Contras*: C-24 espera a tres changes; si C-22/C-23 se atrasan, la agenda también. La alternativa es sembrar turnos/bloqueos por repositorios, pero no prueba el alta/cancelación reales.
- **Opción B**: aplicar C-24 ahora sobre el `POST` a medio hacer de C-22. Es frágil: C-22 puede cambiar; los tests no pueden cancelar turnos ni confiar en el contrato; no se recomienda.
- **Opción C**: sembrar todo por repositorios/SQL y aplicar antes de C-22/C-23. Es posible, pero duplica la lógica de alta y no prueba el flujo HTTP; la integración con la UI queda más débil. No se recomienda.
- **Recomendación**: **A**. Esperar C-21/C-22/C-23 archivados y verdes; el apply de C-24 es de solo lectura y no toca dominio ni esquema. Si la autora quiere adelantar, **C** es la única variante razonable, pero no es la recomendada.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| C-22 y C-23 no están archivados y el `POST /api/appointments` a medio hacer no es fuente de verdad | El apply de C-24 empieza solo con C-21, C-22 y C-23 archivados y verdes (D18). Este explore no toma el código parcial como contrato. |
| KB 07 Flujo 5 dice `GET /api/appointments?...` y C-24 usa `GET /api/agenda` | D1: se documenta la diferencia; la KB se actualiza en un change documental posterior, no en C-24. |
| El odontólogo ve la agenda completa, incluidos nombres de pacientes y motivos de bloqueos ajenos | Es una decisión de C-19 y KB 03:22/36 (R todos, solo lectura); se acepta. No se agregan DNI, teléfono ni historia clínica. |
| La consulta sin filtro de profesional/sillón no usa un índice de `start_at` | El volumen es de 2–5 profesionales y un rango de un día/semana; el scan es aceptable. Si crece, un change posterior agrega `ix_appointment_start_at` o un índice de rango (D10, D15). |
| Tres consultas bajo `READ COMMITTED` pueden ver un estado ligeramente distinto si hay una escritura concurrente | Se acepta para una vista de agenda que se refresca; no se usan locks (D15). Si se necesita un snapshot, evaluar `REPEATABLE READ` o una sola consulta. |
| FastAPI ignora parámetros de query desconocidos; `extra="forbid"` no garantiza un `400` por un nombre mal escrito | No se promete ese `400` (D3); si la autora lo quiere, hace falta una dependencia que inspeccione `request.query_params` y no está en el scope. |
| El `403` de `READ_AGENDA` no se puede probar con los tres roles actuales | La celda es `ALL` para los tres; el guardián verifica que la ruta declare el permiso y el OpenAPI documenta el `403` teórico (D17). |
| Un cliente asume que `to` es exclusivo y ve un día de más | `to` es inclusivo y se documenta en OpenAPI y en el sobre (`from`/`to`); el ejemplo del contrato lo deja claro (D2, D4). |
| Un cliente manda un instante ISO completo y espera que se interprete | D2: se rechaza con `400 invalid_date_format`; el contrato solo acepta `YYYY-MM-DD` local. |
| El turno 23:30–00:00 se cuenta dos veces o se pierde | Predicado semiabierto y medianoches locales (D8); tests en L y L+1. |
| Un bloqueo que cruza la medianoche se pierde en uno de los dos días | El solapamiento semiabierto lo incluye en ambos; la UI lo recorta (D6, D8). |
| Los cancelados hacen crecer la respuesta y el front no los oculta | Se incluyen con `status` (D7); la UI los oculta; un `includeCancelled` puede sumarse después. |
| Un profesional/sillón inactivo con turnos existentes no se puede ver | Se incluyen turnos, horarios y bloqueos (D14); el catálogo de C-20 aporta `active` para la UI. |
| El detalle `GET /api/appointments/{id}` agranda C-24 y toca el router de C-22 | Es opcional (D9); la opción B lo deja fuera sin bloquear C-25. |
| `AgendaResponse` con `from`/`to` como alias de `date` puede confundir a Pydantic/FastAPI | Se usa `serialization_alias="from"`/`"to"` y `populate_by_name=True`, como los esquemas de C-22; el test unitario verifica `model_dump(by_alias=True)` y la respuesta real. |
| El test de medianoche no puede crear el turno porque el horario no cubre las 00:00 | El fixture inserta lunes 00:00–24:00 para P1/P2; el dominio permite `end_minute = 1440` y un fin exacto a las 00:00 (D8, D16). |
| Los tests de integración dependen de la fecha actual y se rompen con el tiempo | Se usa `get_future_monday()` relativo y turnos futuros; no hay fechas fijas (D16). |

### Preguntas para la autora

- **P1**: ¿La ruta es `GET /api/agenda` (recomendada) o `GET /api/appointments` como dice KB 07 (D1)? Sugerencia: `/api/agenda`; KB 07 se corrige después.
- **P2**: ¿`from`/`to` son fechas locales obligatorias, `to` inclusivo y máximo 31 días (D2)? Sugerencia: sí; si preferís 7 días, se cambia el límite.
- **P3**: ¿El sobre incluye `timezone` y los turnos enriquecidos con nombres (D4)? Sugerencia: sí; evita N+1 en el front.
- **P4**: ¿Los horarios van como plantilla semanal (recomendada) o expandidos por día (D5)? Sugerencia: plantilla semanal.
- **P5**: ¿La agenda incluye los cancelados con su estado y sin filtro de estado (D7)? Sugerencia: sí; la UI los oculta.
- **P6**: ¿Incluimos `GET /api/appointments/{id}` en C-24 (D9)? Sugerencia: sí; si querés el scope mínimo, se deja para otro change.
- **P7**: ¿Incluimos profesionales y sillones inactivos con sus turnos/horarios/bloqueos (D14)? Sugerencia: sí; el front usa `active` para atenuar.
- **P8**: ¿Los filtros con id inexistente devuelven `200` con listas vacías (D3)? Sugerencia: sí; el `404` queda para el detalle.
- **P9**: ¿El máximo de rango es 31 días (D2)? Sugerencia: sí; permite un mes y el test de semanas; un valor menor es trivial de cambiar.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

0. **Precondición**: C-17 y C-20 archivados (de `CHANGES.md`); C-21, C-22 y C-23 archivados y verdes (para reutilizar rutas/repositorios y probar el alta/cancelación). No tomar el `POST` parcial de C-22 como contrato. No tocar dominio, migraciones, specs, KB, `CHANGES.md` ni `AGENTS.md`.
1. **Esquemas**: `AgendaQuery` (fechas locales estrictas, `professionalId`/`chairId` opcionales, `extra="forbid"`, validadores de orden/máximo); `AgendaAppointmentResponse`; `AgendaWorkingHoursResponse`; `AgendaResponse`; reutilizar `BlockResponse`. Agregar `invalid_date_format`, `invalid_range_order` e `invalid_range_length` a `MALFORMED_MESSAGES` (D2, D3, D4, D12).
2. **Repositorios**: `AppointmentWithNames`; `AppointmentRepository.list_for_agenda_in_range` con joins, filtros opcionales y orden `(start_at, id)`; `get_with_names`; `BlockRepository.list_in_range` con filtro opcional de profesional y orden `(start_at, id)`. Reutilizar `WorkingHoursRepository.list`/`list_by_professional` (D10).
3. **Servicio**: `backend/app/services/agenda.py` con `Agenda`, `AgendaAppointment`, `get_agenda` y `get_agenda_appointment`; medianoches locales con `ZoneInfo`; mapeo de nombres/estados; sin `commit` (D11, D13).
4. **Rutas**: `backend/app/api/agenda.py` (`GET /agenda`, tag "Agenda"); `GET /api/appointments/{id}` en `backend/app/api/appointments.py` (tag "Turnos"); incluir el router en `main.py`; `require_permission(APPOINTMENT, READ_AGENDA)`; `NotFoundError("Turno no encontrado.")`; sin `ensure_own_professional` (D1, D9, D11).
5. **OpenAPI**: `response_model`, tags, `permission_responses()` y `not_found_responses("Turno")`; verificar `400`/`401` automáticos y los guardianes de rutas (D17).
6. **Tests unitarios**: `AgendaQuery` (faltantes, fecha inválida, orden, máximo, alias) y serialización del sobre con `by_alias=True` (D16).
7. **Tests de integración**: fixture de datos demo + `TRUNCATE` con trigger + horarios de lunes 00:00–24:00; `get_future_monday`; turnos por C-22; cancelación por C-23; bloqueos por C-21; los casos de D16 (filtros combinados, semanas, cancelados, medianoche, odontólogo, inactivos, filtro inexistente, `400`, `401`, agenda vacía, detalle).
8. **Tests de OpenAPI**: paths `/api/agenda` y `/api/appointments/{id}`, tags, parámetros, respuestas y `$ref` (D16, D17).
9. **Evidencias**: pytest de integración/unitarios, `mypy --strict`, guardianes de rutas/OpenAPI y `docs/evidencias/verify-C-24.md` con el formato de C-20/C-21/C-22/C-23. Si el proyecto mantiene `mutaciones-C-24.py` y `trazabilidad-C-24.py`, adaptarlos.
