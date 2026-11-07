# Design — C-24 `api-consulta-de-agenda`

## Context

C-24 expone la lectura de la agenda que falta entre la API de turnos de C-22/C-23 y el frontend de C-25. Parte de `docs/evidencias/explore-C-24.md`; las decisiones D1–D18 y las preguntas P1–P9 son las recomendadas por el explore y aprobadas por la autora, con las correcciones C1–C3 incorporadas en este documento. Ver `proposal.md` para la motivación.

La base que se reutiliza ya existe y está archivada: turnos e historial persistidos (C-17), API base con errores y OpenAPI (C-20), horarios y bloqueos con sus repositorios y esquemas (C-21), alta de turnos (C-22), ciclo de vida y cancelación (C-23), matriz RBAC y `require_permission` (C-19), y el harness de integración con tokens reales. C-24 no agrega dominio, migraciones ni permisos: es una vista de solo lectura.

**Diferencia con KB 07 Flujo 5 (D1).** La KB describe `GET /api/appointments?from=&to=&professionalId=&chairId=`, pero `CHANGES.md` §[C-24] fija `GET /api/agenda?...`. Se implementa `/api/agenda` porque la respuesta no es un simple listado de turnos: incluye horarios y bloqueos, y convive con `GET /api/appointments/{id}` y `POST /api/appointments` sin ambigüedad de prefijo. La KB se corrige en un change documental posterior, no en C-24.

## Goals / Non-Goals

**Goals**: exponer `GET /api/agenda` y `GET /api/appointments/{id}`; interpretar la ventana en `APP_TIMEZONE`; devolver turnos enriquecidos, plantilla de horarios y bloqueos en un sobre; filtrar por profesional y sillón; incluir cancelados con su estado; resolver los bordes de medianoche; validar la entrada con `400`; documentar y probar cada contrato.

**Non-Goals**: calcular disponibilidad o huecos libres; filtrar por estado, paginar, exportar o buscar; alias `GET /api/appointments`; pantallas (C-25 en adelante); ABM de usuarios; WebSockets o refresco en vivo; `note`; cambios de dominio, esquema, migraciones, RBAC, índices o Docker.

## Decisions

### D1 — Endpoints, rutas, RBAC y la diferencia con KB 07

**Problema**: definir las rutas, colgarlas del guardián correcto y resolver el choque entre KB 07 y `CHANGES.md`.

| # | Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores |
|---|--------|------|------------------|------------|-----------|-------|-------|---------|
| 1 | `GET` | `/api/agenda` | `APPOINTMENT` / `READ_AGENDA` | todos (solo lectura) | todos | todos | `200` | `400`, `401`, `403` |
| 2 | `GET` | `/api/appointments/{id}` | `APPOINTMENT` / `READ_AGENDA` | todos (solo lectura) | todos | todos | `200` | `400`, `401`, `403`, `404` |

- **Opción A (recomendada)**: `/api/agenda` para la vista compuesta y `/api/appointments/{id}` para el detalle, ambas con `require_permission(APPOINTMENT, READ_AGENDA)` y **sin** `ensure_own_professional`; el `Scope.ALL` de la celda es deliberado (KB 03:22/36, C-19).
- **Opción B**: `GET /api/appointments?from&to...` como dice KB 07; "appointments" sugiere solo turnos y choca con el detalle y el `POST`. Descartada.
- **Opción C**: exponer las dos rutas como alias; duplica contrato, OpenAPI, tests y errores. Descartada.
- **Decisión**: **A**. Tag "Agenda" para la vista y tag "Turnos" para el detalle, en `backend/app/api/agenda.py` y `backend/app/api/appointments.py` respectivamente.

### D2 — Ventana temporal: fechas locales obligatorias, `to` inclusivo, máximo 31 días

**Problema**: definir qué significan `from` y `to`, su inclusividad y el rango aceptado.

- **Opción A (recomendada)**: `from` y `to` son fechas locales `YYYY-MM-DD` obligatorias en `APP_TIMEZONE`; `to` es inclusivo; el servidor calcula `[from 00:00 local, (to + 1 día) 00:00 local)`; máximo 31 días inclusivos (`(to - from).days + 1 <= 31`).
- **Opción B**: instantes ISO con offset como C-21; obliga al front a calcular medianoches locales y permite rangos arbitrarios. Descartada.
- **Opción C**: `from`/`to` opcionales con defaults "hoy"/"hoy + 6"; oculta errores e introduce un reloj en una lectura. Descartada.
- **Decisión**: **A**. Los errores son `400`: fecha con formato distinto de `YYYY-MM-DD` → `invalid_date_format`; `to < from` → `invalid_range_order`; más de 31 días → `invalid_range_length`; falta el parámetro → `missing`. Un instante ISO completo se rechaza para no interpretar la hora en dos zonas.

### D3 — Filtros `professionalId` y `chairId`: opcionales, combinables, id inexistente = lista vacía (corrección C1)

**Problema**: decidir si los filtros son obligatorios, cómo se combinan y qué pasa con un id inexistente.

- **Opción A (recomendada)**: `professionalId` y `chairId` opcionales y combinables con AND. Un id inexistente devuelve `200` con las listas filtradas vacías, no `404`. `professionalId` filtra turnos, horarios y bloqueos; `chairId` filtra solo turnos porque los horarios y bloqueos no son por sillón. UUID malformado → `400`.
- **Opción B**: `404` si el profesional o el sillón no existen; trata un filtro como un recurso de path. Descartada.
- **Opción C**: `422 UNKNOWN_REFERENCE` para un filtro inexistente; es el código de las referencias del cuerpo (C-22), no de un query. Descartada.
- **Decisión**: **A**, con la corrección de la autora: `AgendaQuery` es un modelo Pydantic usado como `Annotated[AgendaQuery, Query()]`, igual que `BlocksQuery` de C-21, y `extra="forbid"` **sí** hace que FastAPI rechace un parámetro de query no declarado; el proyecto lo traduce a `400` con `type: "extra_forbidden"`. El explore se equivocaba al afirmar que FastAPI lo ignora.

### D4 — Sobre de respuesta y turnos enriquecidos

**Problema**: definir la forma de la respuesta y si los turnos llevan nombres o solo ids.

- **Opción A (recomendada)**: un sobre plano `{ from, to, timezone, appointments, workingHours, blocks }`. `appointments` usa `AgendaAppointmentResponse` (ids + `patientName`, `professionalName`, `chairName`, `serviceName` + `startAt`/`endAt` UTC con `Z` + `status`); `workingHours` usa `AgendaWorkingHoursResponse`; `blocks` reutiliza `BlockResponse` de C-21. `from`/`to` repiten la ventana y `timezone` dice en qué zona se interpretó.
- **Opción B**: devolver `AppointmentResponse` de C-22 sin nombres; obliga al front a cruzar cuatro catálogos. Descartada.
- **Opción C**: agrupar por profesional; acopla el contrato a una disposición visual y complica filtros. Descartada.
- **Decisión**: **A**. Una sola llamada dibuja la agenda y no hay N+1 en el cliente.

### D5 — Horarios de atención: plantilla semanal, filtrada por profesional, no por sillón

**Problema**: decidir si se devuelve la plantilla semanal o los horarios expandidos por día.

- **Opción A (recomendada)**: la plantilla semanal de `WorkingHoursRepository.list()` o `list_by_professional(id)`, con `professionalId`, `weekday` 1–7, `start`/`end` `HH:MM` y `24:00` posible. Orden `(professionalId, weekday, start)`. `chairId` no la filtra.
- **Opción B**: expandir una entrada por fecha; multiplica filas y obliga a decidir feriados/excepciones que no existen. Descartada.
- **Opción C**: solo horarios de profesionales con turnos; una agenda vacía no se podría dibujar. Descartada.
- **Decisión**: **A**. Reutiliza C-21 sin cambios; la UI filtra por `weekday` si muestra un solo día.

### D6 — Bloqueos del rango: solapamiento, todos por defecto, filtrados por profesional

**Problema**: decidir qué bloqueos entran, cómo se filtran y si el motivo se expone.

- **Opción A (recomendada)**: todos los bloqueos que se solapan con `[from, to)` con `start_at < to_end AND end_at > from_start`; sin filtro, todos los profesionales; con `professionalId`, solo los de ese profesional; `chairId` no los filtra; se devuelve `reason`; los bloqueos que cruzan la medianoche entran en los dos días.
- **Opción B**: solo bloqueos contenidos en el rango; un bloqueo que empieza la noche anterior desaparecería. Descartada.
- **Opción C**: solo bloqueos del profesional filtrado y ninguno sin filtro; la vista global pierde motivos. Descartada.
- **Decisión**: **A**. Solapamiento semiabierto y `reason` visible; el odontólogo ve motivos ajenos, ya aceptado por C-19 y KB 03:36.

### D7 — Estados: todos, incluidos los cancelados, sin filtro de estado; orden estable

**Problema**: decidir si la agenda oculta cancelados, si agrega filtro de estado y en qué orden salen las listas.

- **Opción A (recomendada)**: incluir todos los estados con su `status`, sin `status` ni `includeCancelled` en C-24; orden `appointments` por `(start_at, id)`, `blocks` por `(start_at, id)` y `workingHours` por `(professional_id, weekday, start_minute)`.
- **Opción B**: excluir cancelados por defecto; contradice la consigna y obliga a otra llamada. Descartada.
- **Opción C**: agregar `status`/`includeCancelled` ahora; contrato y tests extra fuera de scope. Descartada.
- **Decisión**: **A**. La UI puede ocultar cancelados en el cliente; un change posterior puede agregar `includeCancelled=false`.

### D8 — Borde de medianoche y solapamiento del rango

**Problema**: decidir a qué día pertenece un turno que termina a las 00:00, uno que empieza a las 00:00 y un bloqueo que cruza la medianoche.

- **Opción A (recomendada)**: rango semiabierto `[from 00:00 local, to+1 00:00 local)` y solapamiento `start_at < to_end AND end_at > from_start`. Un turno que termina a las 00:00 pertenece al día anterior; uno que empieza a las 00:00 pertenece a ese día; un bloqueo que cruza aparece en los dos días. Medianoches con `datetime.combine(fecha, time.min, tzinfo=tz)`.
- **Opción B**: comparar solo la fecha local de `start_at`; para bloqueos es incorrecto y pierde los que empiezan antes. Descartada.
- **Opción C**: truncar a minutos; se aparta de la regla de dominio que compara el fin completo. Descartada.
- **Decisión**: **A**. Coincide con `same_day.py` y con DD-07; los tests cubren 23:30–00:00 y 00:00–00:30.

### D9 — `GET /api/appointments/{id}` incluido en C-24

**Problema**: C-22 D7 y C-23 derivaron el detalle puntual a C-24; hay que decidir si entra y con qué permiso.

- **Opción A (recomendada)**: incluirlo con `APPOINTMENT / READ_AGENDA` (`Scope.ALL`, sin propiedad), `200` con `AgendaAppointmentResponse` y `404` con `NotFoundError("Turno no encontrado.")`. Reutiliza el read model y el servicio de agenda.
- **Opción B**: no incluirlo; el front usa el `201`/`200` de las mutaciones y refresca la agenda, pero deja la deuda y no hay deep link. Descartada por la autora.
- **Opción C**: incluirlo con `APPOINTMENT_HISTORY / READ` o comparación de propiedad; contradice la agenda completa. Descartada.
- **Decisión**: **A**. El costo es una consulta con el mismo join; cierra la deuda de C-22/C-23.

### D10 — Repositorios y read model: una consulta con joins, filtros opcionales, sin N+1 ni migración

**Problema**: cómo leer turnos, nombres, bloqueos y horarios sin duplicar consultas ni agregar esquema.

- **Opción A (recomendada)**: `AppointmentWithNames` (turno + cuatro nombres); `AppointmentRepository.list_for_agenda_in_range(start_at, end_at, professional_id=None, chair_id=None)` con `select` de `AppointmentModel` + `PatientModel.full_name` + `ProfessionalModel.full_name` + `ChairModel.name` + `ServiceModel.name`, inner joins, predicado semiabierto, filtros opcionales y `order_by(start_at, id)`; `get_with_names(identifier)` con el mismo `select`; `BlockRepository.list_in_range(start_at, end_at, professional_id=None)` reutilizando el predicado. Horarios con `WorkingHoursRepository.list()`/`list_by_professional(id)`. Total: 3 consultas por agenda y 1 por detalle.
- **Opción B**: resolver cada nombre con una consulta por fila; N+1. Descartada.
- **Opción C**: vista/materialized view o agregación JSON; agrega esquema, migración y SQL difícil de testear. Descartada.
- **Decisión**: **A**. Sin índices ni migraciones; los índices existentes `(professional_id, start_at)` y `(chair_id, start_at)` ayudan cuando hay filtro. La consulta sin filtro es un scan de una tabla chica.

### D11 — Organización del código y transacción: servicio de lectura y routers delgados

**Problema**: dónde viven la lógica, los esquemas y las rutas, y quién confirma.

- **Opción A (recomendada)**: `backend/app/services/agenda.py` con `Agenda`, `AgendaAppointment`, `get_agenda(session, from_date, to_date, professional_id, chair_id, tz)` y `get_agenda_appointment(session, identifier)`; `backend/app/api/agenda.py` con `GET ""`; el detalle en `backend/app/api/appointments.py`; el router se incluye en `main.py`. La lectura no hace `commit` ni `rollback`.
- **Opción B**: todo en el router con los repositorios; deja la lógica de fechas y el mapeo en HTTP. Descartada.
- **Opción C**: meter la agenda en `services/availability.py`; mezcla escritura de horarios/bloqueos con un read model distinto. Descartada.
- **Decisión**: **A**. Mantiene el patrón servicio + router delgado de C-20/C-21; el servicio se testea sin FastAPI.

### D12 — Errores y validación: `400` con mensajes explicativos (corrección C1)

**Problema**: traducir fechas inválidas, rango invertido, rango largo, UUID malformado y parámetro desconocido sin romper el contrato de errores de C-20.

- **Opción A (recomendada)**: `AgendaQuery` con `from_date: date` (alias `from`), `to_date: date` (alias `to`), `professional_id: UUID | None` (alias `professionalId`), `chair_id: UUID | None` (alias `chairId`), `extra="forbid"`. Validador de campo `mode="before"` para `from`/`to` con `^\d{4}-\d{2}-\d{2}$` y `date.fromisoformat`; si falla, `PydanticCustomError("invalid_date_format", "La fecha debe tener formato AAAA-MM-DD.")`. Validador de modelo `mode="after"` para `invalid_range_order` e `invalid_range_length`. Agregar esas tres claves a `MALFORMED_MESSAGES`.
- **Opción B**: validar en el router y lanzar `NotFoundError`/`DomainRejectedError`; el rango no es un recurso ni una regla de negocio. Descartada.
- **Opción C**: `422` con un `ViolationCode` nuevo; el `422` es para reglas de dominio. Descartada.
- **Decisión**: **A**. La corrección C1 confirma el `400` por parámetro desconocido vía `extra="forbid"` en el modelo de query, igual que C-21; no hace falta inspeccionar `request.query_params`. El handler devuelve `{ "errors": [{field, type, message}] }`.

### D13 — Zona horaria y reloj: `APP_TIMEZONE`, sin `now`, UTC `Z` y horas locales `HH:MM`

**Problema**: evitar `datetime` naive, interpretar bien el día local y no depender del reloj en una lectura.

- **Opción A (recomendada)**: `tz = ZoneInfo(settings.app_timezone)` (fallback `"America/Argentina/Buenos_Aires"`); `start = datetime.combine(from_date, time.min, tzinfo=tz)` y `end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz)`. Turnos y bloqueos con `format_utc_iso` (UTC con `Z`); horarios en `HH:MM` local (`24:00` posible); `timezone` en el sobre. Sin `datetime.now()`.
- **Opción B**: fechas UTC; un día de Buenos Aires empezaría a las 21:00 UTC del día anterior. Descartada.
- **Opción C**: aceptar `tz`/`now` del cliente; el cliente puede mentir. Descartada.
- **Decisión**: **A**. Cumple DD-07/SU-01, el día local es el de Buenos Aires y los tests no dependen del reloj.

### D14 — Profesionales y sillones inactivos: incluirlos en la agenda

**Problema**: decidir qué pasa con turnos, horarios y bloqueos de recursos desactivados.

- **Opción A (recomendada)**: incluirlos. Un turno creado antes de desactivar un recurso sigue existiendo; sus horarios y bloqueos explican por qué no se puede dar un turno nuevo. El `active` del catálogo de C-20 queda para la presentación.
- **Opción B**: excluirlos; oculta historia y motivos. Descartada.
- **Opción C**: incluir turnos pero excluir horarios/bloqueos; inconsistente. Descartada.
- **Decisión**: **A**. Sin filtro de activos en la consulta; C-22 ya rechaza turnos nuevos para inactivos con `INACTIVE_REFERENCE`.

### D15 — Consistencia, concurrencia y performance: lectura simple, sin locks ni migración

**Problema**: decidir si las tres consultas necesitan un snapshot único, locks o índices nuevos.

- **Opción A (recomendada)**: una sesión por request, tres sentencias bajo `READ COMMITTED`, sin locks. Una escritura concurrente puede verse a medias entre listas; para una agenda de 2–5 profesionales que se refresca es aceptable. Sin índices ni migraciones.
- **Opción B**: `REPEATABLE READ` por request; cambia el aislamiento y agrega complejidad sin necesidad. Descartada.
- **Opción C**: una sola consulta con CTEs/JSON o vista materializada; SQL complejo y específico del motor. Descartada.
- **Decisión**: **A**. Se documenta el trade-off; si el volumen crece, un change posterior evalúa `REPEATABLE READ` o índices de rango.

### D16 — Tests: integración con tokens reales, fechas relativas y turnos creados por la API (corrección C2)

**Problema**: cómo probar la agenda sin mocks, sin reloj fijo y sin depender de datos reales.

- **Opción A (recomendada)**: `backend/tests/integration/test_api_agenda.py` con `auth_client`/`test_engine`, `token_for` y un fixture autouse que siembra los datos demo, reactiva P1/P2, deshabilita el trigger de historial y trunca `appointment_status_change, appointment, block, working_hours CASCADE`; `get_future_monday()` relativo. Turnos por `POST /api/appointments` (C-22), cancelaciones por `POST /api/appointments/{id}/cancel` (C-23), bloqueos por `POST /api/professionals/{id}/blocks` (C-21), horarios por `PUT /api/professionals/{id}/working-hours` (C-21) o por SQL de setup. Sin `monkeypatch`, `dependency_overrides` ni mocks.
- **Opción B**: probar solo repositorios/servicio; no cubre OpenAPI, RBAC, `400`, tokens ni el cableado. Descartada.
- **Opción C**: fechas fijas o `monkeypatch` del reloj; se rompen con el tiempo y el proyecto los prohíbe. Descartada.
- **Decisión**: **A**, con la corrección C2: el test de medianoche **no** depende del horario demo de la Dra. Quiroga (termina a las 19:00). Primero reemplaza el horario semanal de P1 por `PUT /api/professionals/{id}/working-hours` con un tramo del lunes que termina en `"24:00"` y un tramo del martes que empieza en `"00:00"`; recién entonces crea el turno de 23:30 a 00:00 del lunes L y el de 00:00 a 00:30 del martes L+1 con `POST /api/appointments`. Se agregan unitarios de `AgendaQuery` y tests de OpenAPI.

### D17 — Documentación OpenAPI y guardianes

**Problema**: documentar las rutas nuevas sin romper los guardianes de C-18/C-19.

- **Opción A (recomendada)**: `/api/agenda` con `response_model=AgendaResponse`, `status_code=200`, tag "Agenda", `responses={**permission_responses()}`; parámetros tomados del modelo de query (`from`/`to` requeridos, `professionalId`/`chairId` opcionales). El detalle con `response_model=AgendaAppointmentResponse`, tag "Turnos", `responses={**not_found_responses("Turno"), **permission_responses()}`. `setup_openapi` agrega `400` (hay parámetros) y `401` (hay seguridad). `require_permission` visible para `tests/api/test_route_guards.py`.
- **Opción B**: dejar solo los modelos por defecto; el `400`/`401`/`403`/`404` no queda documentado. Descartada.
- **Opción C**: documentar solo `200`; peor. Descartada.
- **Decisión**: **A**. No se documentan `409`/`422` de dominio porque no existen en una lectura; el `403` es teórico pero se mantiene por uniformidad.

### D18 — Precondiciones, secuencia y no-goals (corrección C3)

**Problema**: decidir cuándo se puede aplicar C-24 y qué no se toca.

- **Opción A (recomendada)**: dependencias formales de `CHANGES.md`: C-17 y C-20 archivados. Precondición de tests/reutilización: C-21, C-22 y C-23 archivados y verdes (C3). Después de C-24 se desbloquea C-25 y se cierra el GATE 14 (`C-22`, `C-23`, `C-24`). No se editan `CHANGES.md`, la KB, `AGENTS.md`, `CLAUDE.md`, `openspec/specs/` ni migraciones.
- **Opción B**: aplicar sobre el `POST` a medio hacer de C-22; frágil y no permite cancelar en los tests. Descartada.
- **Opción C**: sembrar todo por repositorios/SQL antes de C-22/C-23; duplica la lógica de alta y no prueba el flujo HTTP. Descartada.
- **Decisión**: **A**, con C3: el apply empieza solo con C-21, C-22 y **C-23** archivados; si C-23 no está archivado, se detiene.

## Decisiones registradas de la autora

- **D1–D18** y **P1–P9**: aprobadas con la recomendación del explore, con las correcciones **C1–C3** incorporadas en este documento.
- **C1 (D3, D12)**: el `400` por un parámetro de query desconocido **sí** se puede dar con el patrón de C-21 (`Annotated[AgendaQuery, Query()]` + `extra="forbid"`); la agenda usa el mismo patrón y tiene un escenario de `400` por un parámetro inventado.
- **C2 (D16)**: el test de medianoche carga antes, por `PUT /api/professionals/{id}/working-hours` de C-21, un tramo del lunes que termina en `"24:00"` y un tramo del martes que empieza en `"00:00"`; recién entonces crea los turnos 23:30–00:00 y 00:00–00:30 con `POST /api/appointments`.
- **C3 (D18)**: precondición del apply (tarea 0.1): C-21, C-22 y C-23 **archivados**, porque los tests cancelan turnos con `POST /api/appointments/{id}/cancel` de C-23. Si C-23 no está archivado, detenerse.
- **P1** (ruta `/api/agenda`): sí, D1.
- **P2** (fechas locales, `to` inclusivo, máximo 31 días): sí, D2.
- **P3** (sobre con `timezone` y turnos enriquecidos): sí, D4.
- **P4** (plantilla semanal): sí, D5.
- **P5** (cancelados incluidos con estado): sí, D7.
- **P6** (`GET /api/appointments/{id}` en C-24): sí, D9.
- **P7** (incluir inactivos): sí, D14.
- **P8** (filtro inexistente = `200` con listas vacías): sí, D3.
- **P9** (máximo de 31 días): sí, D2.

## Risks / Trade-offs

- **[Riesgo] C-23 no está archivado y los tests no pueden cancelar turnos** → tarea 0.1 (C3): detenerse si falta C-21, C-22 o C-23.
- **[Riesgo] KB 07 Flujo 5 muestra `/api/appointments` y la API usa `/api/agenda`** → D1: se documenta la diferencia; la KB se corrige en un change documental posterior.
- **[Riesgo] FastAPI ignora el parámetro desconocido y no devuelve `400`** → C1/D3/D12: el patrón `Annotated[AgendaQuery, Query()]` con `extra="forbid"` lo rechaza, igual que C-21; test explícito.
- **[Riesgo] El odontólogo ve nombres de pacientes y motivos de bloqueos ajenos** → decisión de C-19 y KB 03:22/36; se acepta, sin DNI, teléfono ni historia clínica.
- **[Riesgo] La consulta sin filtro no usa un índice de `start_at`** → volumen de 2–5 profesionales y una semana; scan aceptable (D10, D15).
- **[Riesgo] Tres consultas bajo `READ COMMITTED` ven estados ligeramente distintos** → se acepta para una vista que se refresca; sin locks (D15).
- **[Riesgo] El `403` de `READ_AGENDA` no se puede probar con los roles actuales** → la celda es `ALL` para los tres; el guardián verifica que la ruta declare el permiso y OpenAPI documenta el `403` teórico (D17).
- **[Riesgo] Un cliente asume que `to` es exclusivo y ve un día de más** → `to` inclusivo documentado en OpenAPI y en el sobre (D2, D4).
- **[Riesgo] Un cliente manda un instante ISO completo** → `400 invalid_date_format`; el contrato solo acepta `YYYY-MM-DD` local (D2).
- **[Riesgo] El turno 23:30–00:00 se cuenta dos veces o se pierde** → predicado semiabierto y medianoches locales; tests en L y L+1 (D8).
- **[Riesgo] Un bloqueo que cruza la medianoche se pierde en uno de los dos días** → el solapamiento semiabierto lo incluye en ambos (D6, D8).
- **[Riesgo] El escenario de medianoche no puede crear turnos porque el horario demo termina a las 19:00** → C2/D16: reemplazar el horario por `PUT` con un tramo que termina en `24:00` y otro que empieza en `00:00`.
- **[Riesgo] `AgendaResponse` con `from`/`to` como alias de `date` confunde a Pydantic/FastAPI** → `serialization_alias="from"`/`"to"` y `populate_by_name=True`; test unitario con `model_dump(by_alias=True)` y test de integración real.
- **[Trade-off] El detalle toca `backend/app/api/appointments.py` de C-22** → se hace recién con C-23 archivado y comparte el read model (D9, C3).

## Migration Plan

Sin migraciones. Rollback: revertir el commit del change. El apply es de solo lectura y no altera datos.

## Correcciones aplicadas de la autora (C1–C3)

- **C1**: el `400` por parámetro de query desconocido es real con el modelo de query de C-21 y `extra="forbid"`; se corrigió D3/D12 y se agregó el escenario.
- **C2**: el test de medianoche reemplaza el horario semanal por `PUT` con `24:00` y `00:00`, y crea los turnos por `POST` de C-22; se corrigió D16.
- **C3**: la precondición del apply exige C-21, C-22 y C-23 archivados; si C-23 falta, detenerse. Se corrigió D18 y la tarea 0.1.
