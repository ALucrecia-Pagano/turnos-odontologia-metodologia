# Explore C-21 — `api-horarios-y-bloqueos`

Fecha: 2026-11-06
Fase: 5 — API REST FastAPI y JWT
Governance: **MEDIO** (según `CHANGES.md` §[C-21])
Dependencias en `CHANGES.md`: `C-16` (`persistencia-horarios-y-bloqueos`), `C-17` (`persistencia-turnos-e-historial`), `C-20` (`api-catalogos-y-pacientes`).

> Este explore es analítico: no ejecutó docker, pytest, alembic ni pip, y no tocó código, tests ni specs. Se hizo sobre el repositorio en el commit `a263f64` (propose de C-20). C-20 todavía no está implementado: sus decisiones se toman de `openspec/changes/api-catalogos-y-pacientes/design.md`.

---

## 1. Alcance de C-21 según `CHANGES.md` y qué queda afuera

### Qué entra en C-21

1. **Horario de atención por profesional**: `GET` y `PUT /api/professionals/{id}/working-hours`. El `PUT` reemplaza la semana completa (Flujo 4 de KB 07).
2. **Bloqueos por profesional**: crear, listar y eliminar (`POST`, `GET` y `DELETE`).
3. **RBAC (RN-AC-01)**: el odontólogo opera solo sobre **su** profesional; recepción solo lee; el administrador opera sobre todos.
4. **Turnos afectados sin cancelar**: crear un bloqueo o cambiar el horario se guarda igual, y la respuesta lista los turnos existentes que quedan pisados o fuera de horario (US-010 CA-3, US-011 CA-3, RN-DI-04). No se cancelan ni se mueven.
5. **Tests de integración**: 403 del odontólogo sobre otro profesional, bloqueo con turnos afectados, tramos solapados → 422.

### Qué queda explícitamente afuera

- **Editar un bloqueo** (`PUT`/`PATCH`): `CHANGES.md` dice "crear, listar, eliminar". La fila `BLOCK UPDATE` de la matriz existe, pero ninguna ruta la usa en C-21 (ver D6).
- **Reprogramar los turnos afectados**: es C-23. C-21 solo los informa.
- **Agenda y disponibilidad** (`GET /api/appointments`, huecos libres): es C-24.
- **Pantallas**: C-25 en adelante.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-21 reutiliza

| Pieza | Dónde | Qué ofrece |
|-------|-------|------------|
| `WorkingHours(professional_id, weekday, start_minute, end_minute)` | `app/domain/model.py` | Weekday ISO 1..7 y minutos locales; 1440 = 24:00. |
| `validate_working_hours(slots)` | `app/domain/rules/working_hours.py` | `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS`. |
| `check_working_hours(professional_id, start_at, end_at, working_hours, tz, professional_name)` | mismo archivo | `OUTSIDE_WORKING_HOURS` para **un** turno. |
| `Block(id, professional_id, start_at, end_at, reason)` | `app/domain/model.py` | Instantes normalizados a UTC; `ValueError` si llegan sin zona. |
| `validate_block(block)` | `app/domain/rules/blocks.py` | `INVALID_BLOCK` si `inicio >= fin`. |
| `appointments_affected_by_block(block, appointments)` | mismo archivo | Turnos del profesional, en estado que ocupa agenda, que se solapan; ordenados. |
| `WorkingHoursRepository.replace_for_professional(professional_id, slots)` | `app/repositories/working_hours.py` | Valida, borra e inserta en un savepoint; `UNKNOWN_REFERENCE` si el profesional no existe; no hace commit. |
| `BlockRepository(session, appointment_reader)` | `app/repositories/blocks.py` | `create`, `delete` (devuelve el bloqueo o `None`), `get_by_id`, `list_by_professional`, `list_affected_appointments(block)`. |
| `SqlAppointmentReader` | `app/repositories/appointment.py` | `list_for_professional_in_range(professional_id, start_at, end_at)`. |
| Matriz RBAC, filas 7 a 14 | `app/auth/permissions.py` | Ver la tabla de abajo. |
| `_lock_resources(session, professional_ids, chair_ids)` | `app/services/appointments.py` | `SELECT ... FOR UPDATE` sobre `professional` y `chair`, en orden. |

Filas de la matriz RBAC de C-19 (D9) que usa C-21, copiadas tal cual:

| # | Recurso | Acción | Odontólogo | Recepción | Administrador |
|---|---------|--------|------------|-----------|---------------|
| 7 | `WORKING_HOURS` | `CREATE` | propio | — | todos |
| 8 | `WORKING_HOURS` | `READ` | propio | todos | todos |
| 9 | `WORKING_HOURS` | `UPDATE` | propio | — | todos |
| 10 | `WORKING_HOURS` | `DELETE` | — | — | todos |
| 11 | `BLOCK` | `CREATE` | propio | — | todos |
| 12 | `BLOCK` | `READ` | propio | todos | todos |
| 13 | `BLOCK` | `UPDATE` | propio | — | todos |
| 14 | `BLOCK` | `DELETE` | propio | — | todos |

### 2.2. Lo que falta

1. **No existe una función del dominio para "turnos fuera del nuevo horario"** (US-010 CA-3). Para los bloqueos está `appointments_affected_by_block`, pero para el horario solo está `check_working_hours`, que evalúa **un** turno. Ver D5.
2. **Nadie compara el `professional_id` de la ruta con el del `Actor`.** `require_permission` devuelve `Permission(actor, scope)`, y el comentario de `permissions.py` aclara que en turnos "decide el dominio". En horarios y bloqueos no hay regla del dominio que lo haga: lo tiene que hacer la API. Ver D3.
3. **Crear un bloqueo no bloquea la fila del profesional.** `book_appointment` de C-17 toma `SELECT ... FOR UPDATE` sobre el profesional y después lee los bloqueos. Si la creación del bloqueo no toma el mismo lock, un turno y un bloqueo simultáneos pueden cruzarse. Ver D9.
4. Routers, servicios y esquemas de horarios y bloqueos.

---

## 3. Decisiones de diseño (`D1`–`D12`)

### D1 — Lista completa de endpoints

| # | Método | Ruta | Recurso / Acción | Odontólogo | Recepción | Admin | Éxito | Errores |
|---|--------|------|------------------|------------|-----------|-------|-------|---------|
| 1 | `GET` | `/api/professionals/{id}/working-hours` | `WORKING_HOURS` / `READ` | propio | todos | todos | 200 | 401, 403, 404 |
| 2 | `PUT` | `/api/professionals/{id}/working-hours` | `WORKING_HOURS` / `UPDATE` | propio | — | todos | 200 | 400, 401, 403, 404, 422 |
| 3 | `GET` | `/api/professionals/{id}/blocks` | `BLOCK` / `READ` | propio | todos | todos | 200 | 400, 401, 403, 404 |
| 4 | `POST` | `/api/professionals/{id}/blocks` | `BLOCK` / `CREATE` | propio | — | todos | 201 | 400, 401, 403, 404, 422 |
| 5 | `DELETE` | `/api/blocks/{block_id}` | `BLOCK` / `DELETE` | propio | — | todos | 200 | 401, 403, 404 |

- **Opción A (recomendada)**: rutas anidadas bajo el profesional para listar y crear, como KB 07 Flujo 4, y `DELETE /api/blocks/{block_id}` plano, porque el id del bloqueo ya identifica al profesional.
- **Opción B**: todo anidado (`DELETE /api/professionals/{id}/blocks/{block_id}`). Más simétrico, pero obliga a validar que el bloqueo sea de ese profesional y a decidir qué responder si no coincide (404 o 403).
- **Recomendación**: **A**. Es la que indica la knowledge base y evita una validación de coherencia extra.

### D2 — Acción RBAC del `PUT` de horarios

El `PUT` reemplaza la semana: puede crear tramos (si no había), cambiarlos o dejarla vacía. La matriz tiene `CREATE`, `UPDATE` y `DELETE` separados, con permisos distintos (`DELETE` solo para el administrador).

- **Opción A (recomendada)**: el `PUT` se autoriza siempre con `UPDATE`. Enviar `[]` está permitido para quien puede actualizar, y significa "el profesional no atiende" (C-16 D4). Las filas `CREATE` y `DELETE` de horarios quedan sin ruta en C-21, igual que `BLOCK UPDATE`.
- **Opción B**: elegir la acción según el contenido (sin tramos previos → `CREATE`; lista vacía → `DELETE`). Respeta la letra de la matriz, pero la misma ruta tendría permisos distintos según el cuerpo, y el odontólogo no podría vaciar su propia semana.
- **Recomendación**: **A**, con una línea en el design que explique por qué `DELETE` de horarios no tiene ruta.

### D3 — Cómo se aplica `Scope.OWN` (odontólogo sobre otro profesional)

- **Opción A (recomendada)**: un único helper en `app/api/` (por ejemplo, `ensure_own_professional(permission, professional_id)`): si el scope es `OWN` y `professional_id != actor.professional_id`, lanza el mismo `403` de C-19, con `FORBIDDEN_OPERATION` y el mensaje de la matriz (`"No tiene permiso para ..."`). Para `DELETE /api/blocks/{id}`, primero se carga el bloqueo y se compara su `professional_id`.
- **Opción B**: devolver `404` para no revelar que el recurso existe. No aporta, porque los profesionales son visibles para todos los roles (`PROFESSIONAL READ` = todos).
- **Recomendación**: **A**. El orden es: `401` (token) → `403` por rol (matriz) → `404` si el profesional o el bloqueo no existe → `403` por propiedad. Revisar el 404 antes del 403 de propiedad deja saber que un id existe, pero los profesionales ya son públicos y los bloqueos ajenos no exponen nada más que su existencia.

### D4 — Formato de horas en la API

- **Horarios (opción A, recomendada)**: tramos como `{ "weekday": 1, "start": "09:00", "end": "13:00" }`, en hora local del consultorio. Se acepta `"24:00"` como fin (= minuto 1440). Un texto que no cumple `HH:MM` → `400` (Pydantic). Un tramo con formato válido pero inválido para el dominio (por ejemplo, inicio ≥ fin) → `422`, con la violación del dominio.
- **Horarios (opción B)**: en minutos (`startMinute: 540`). Es más simple de convertir, pero menos legible en Swagger y en el front.
- **Bloqueos**: `startAt` y `endAt` en ISO 8601 **con zona horaria obligatoria** (por ejemplo `2026-11-10T09:00:00-03:00`). Sin zona → `400`, antes de llegar al dominio, que lanzaría `ValueError` (un 500). Las respuestas devuelven UTC (`Z`), como el resto de la API.
- **Recomendación**: **A** para horarios y zona obligatoria para bloqueos.

### D5 — Turnos fuera del nuevo horario (US-010 CA-3)

No hay función que liste qué turnos quedan fuera de un horario nuevo.

- **Opción A (recomendada)**: función pura nueva en `app/domain/rules/working_hours.py`, `appointments_outside_working_hours(appointments, working_hours, tz)`, que reutiliza `check_working_hours` por cada turno y devuelve los que dan `OUTSIDE_WORKING_HOURS`, ordenados igual que `appointments_affected_by_block`. Solo cuentan los turnos en estado que ocupa agenda (`OCCUPYING_STATUSES`) y con `start_at >= now`, porque un turno pasado no "queda fuera" de nada.
- **Opción B**: hacer el bucle en el servicio, sin función de dominio. Es más rápido de escribir, pero la regla queda fuera del dominio y sin tests unitarios.
- **Recomendación**: **A**. Es una regla de negocio y va con su test unitario en `tests/domain/`.
- Para cargar los turnos: `AppointmentRepository.list_for_professional_in_range(professional_id, now, <fin>)`. El fin del rango es una decisión abierta (P2).

### D6 — Bloqueos: sin edición, borrado real

- `POST` crea con `id` generado en el servidor (`uuid4`). El cliente no manda el id.
- `DELETE` borra de verdad (C-16 D4: los bloqueos se borran; US-011 CA-4: liberar el horario). Responde `200` con el bloqueo borrado, que es lo que devuelve `BlockRepository.delete`. Borrar un bloqueo inexistente → `404 NOT_FOUND` (formato de C-20 D8).
- **Sin `PUT` de bloqueos**: para cambiarlo se borra y se crea otro.
- **Recomendación**: así. Alternativa descartada: `204 No Content` en el `DELETE`, que pierde el dato para el front ("se liberó tal bloqueo").

### D7 — Respuestas con turnos afectados

- **`POST /api/professionals/{id}/blocks` → `201`**:

```json
{
  "block": { "id": "...", "professionalId": "...", "startAt": "...Z", "endAt": "...Z", "reason": "Congreso" },
  "affectedAppointments": [
    { "id": "...", "patientId": "...", "patientName": "Ana Pérez", "chairId": "...",
      "startAt": "...Z", "endAt": "...Z", "status": "reservado" }
  ]
}
```

- **`PUT /api/professionals/{id}/working-hours` → `200`**:

```json
{
  "workingHours": [ { "weekday": 1, "start": "09:00", "end": "13:00" } ],
  "appointmentsOutsideHours": [ { "...mismo resumen de turno..." } ]
}
```

- Una lista vacía significa que no hay turnos afectados. El status no cambia por tener afectados: **guardar siempre es éxito** (RN-DI-04).
- `patientName` le ahorra al front una consulta por cada turno, y es justo lo que recepción necesita para llamar al paciente. El odontólogo puede leer pacientes (`PATIENT READ` = todos), así que no hay fuga.
- **Alternativa descartada**: `207 Multi-Status` o `409` cuando hay afectados. La regla dice explícitamente que se guarda.

### D8 — Profesional inexistente o inactivo

- **Inexistente**: `404 NOT_FOUND` (C-20 D8), porque el id está en la ruta. Se verifica antes de llamar al repositorio, así no aparece el `422 UNKNOWN_REFERENCE` de C-16.
- **Inactivo**: se permite leer y guardar horarios y bloqueos (C-16 D5: inactivo impide dar turnos, no configurar la agenda).
- **Recomendación**: así.

### D9 — Transacción y bloqueo de la fila del profesional (concurrencia)

`book_appointment` toma `SELECT ... FOR UPDATE` sobre el profesional y **después** lee horarios y bloqueos. Si `PUT working-hours` o `POST blocks` no toman el mismo lock, puede pasar esto:

1. Recepción da un turno el martes a las 10:00. Lee los bloqueos: no hay ninguno.
2. Al mismo tiempo, la odontóloga crea un bloqueo del martes de 9:00 a 13:00. Calcula los afectados: todavía no hay turno.
3. Los dos hacen commit. Resultado: un turno dentro de un bloqueo, y la respuesta del bloqueo dijo "sin afectados".

- **Opción A (recomendada)**: el servicio de horarios y bloqueos toma `SELECT ... FOR UPDATE` sobre la fila del profesional **antes** de escribir y de calcular los afectados, reutilizando `_lock_resources` de C-17 (o moviéndolo a un módulo común). Así, las dos operaciones se serializan: o el turno ve el bloqueo, o el bloqueo ve el turno.
- **Opción B**: aceptar la carrera y documentarla. Es la ventana más chica de todas, pero es justo la clase de bug que C-17 ya resolvió para los turnos.
- **Recomendación**: **A**, más un test de concurrencia con el mismo patrón de C-17 (dos sesiones, `pg_locks`, `lock_timeout`): un bloqueo y un turno simultáneos sobre el mismo profesional terminan con el turno rechazado por `BLOCKED_TIME` o con el turno listado en `affectedAppointments`, nunca con ninguna de las dos cosas.
- Commit: lo hace el servicio, como C-17 y C-20 (la dependencia de sesión de C-18 no hace commit).

### D10 — Organización del código

- `app/services/availability.py`: `get_working_hours`, `replace_working_hours`, `list_blocks`, `create_block`, `delete_block`.
- `app/api/working_hours.py` y `app/api/blocks.py`: routers con tags de Swagger "Horarios" y "Bloqueos".
- Esquemas en `app/api/schemas.py`, en camelCase con `extra="forbid"` (como C-20).
- **Recomendación**: así, coherente con C-17 y C-20.

### D11 — Listado de bloqueos

- **Opción A (recomendada)**: `GET /api/professionals/{id}/blocks` devuelve todos los bloqueos del profesional, ordenados por `startAt`, con filtros opcionales `from` y `to` (ISO 8601 con zona) para traer solo los que se solapan con un rango. El front de C-27 va a mostrar una semana o un mes, no toda la historia.
- **Opción B**: sin filtros. Más simple, pero devuelve años de bloqueos viejos.
- **Recomendación**: **A**. Si se elige, hace falta un método de repositorio nuevo o filtrar en el servicio.

### D12 — Tests de integración sin mocks

- Usuarios y tokens reales, igual que C-20: `POST /api/auth/login` con los helpers de hash barato de C-19.
- **Turnos afectados reales**: los turnos se crean con `book_appointment` de C-17 (con horario, paciente, sillón y prestación cargados), y después se crea el bloqueo o se cambia el horario por HTTP. Se verifica que el turno aparece en la respuesta **y** que sigue en `reservado` en la base.
- **403 por propiedad**: la odontóloga (vinculada a la Dra. Quiroga, `...0001`) intenta leer o cambiar el horario del Dr. Sosa (`...0002`) y borrar un bloqueo del Dr. Sosa.
- **Mutaciones y trazabilidad con scripts** (`mutaciones-C-21.py` y `trazabilidad-C-21.py`), con el formato de C-19 y C-20.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Carrera entre un turno nuevo y un bloqueo nuevo (D9) | Lock de la fila del profesional y test de concurrencia. |
| Bloqueo sin zona horaria que llega al dominio y da `500` | Validación en el esquema → `400` (D4). |
| El odontólogo modifica otro profesional por error en el front | `403` por propiedad en la API, con test (D3). |
| `appointmentsOutsideHours` con miles de turnos futuros | Rango acotado (P2). |
| Las filas `WORKING_HOURS CREATE/DELETE` y `BLOCK UPDATE` quedan sin ruta | Documentarlo en el design (D2, D6) para que el guardián de rutas de C-19 no lo marque como hueco. |

### Preguntas para la autora

- **P1**: ¿Aprobás el lock de la fila del profesional en horarios y bloqueos (D9)? Agrega un test de concurrencia, pero evita un turno dentro de un bloqueo.
- **P2**: ¿Hasta cuándo se buscan los turnos que quedan fuera del horario nuevo? Sugerencia: desde `now` hasta 90 días. Un horario cambia la semana tipo, así que en teoría afecta a todos los turnos futuros, pero sin límite la consulta crece sin control.
- **P3**: ¿El listado de bloqueos lleva filtros `from` y `to` (D11)? Sugerencia: sí, opcionales.
- **P4**: ¿Incluir `patientName` en los turnos afectados (D7)? Sugerencia: sí.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

1. **Dominio**: `appointments_outside_working_hours` (D5), con tests unitarios y casos de turnos pasados, cancelados y de otro profesional.
2. **Esquemas**: tramos `HH:MM` con `24:00`, bloqueos con zona obligatoria, respuestas con turnos afectados (D4, D7).
3. **Servicio**: `app/services/availability.py`, con lock del profesional, commit y cálculo de afectados (D9, D5).
4. **Helper de propiedad**: `ensure_own_professional` y sus tests de 403 (D3).
5. **Routers**: horarios (D1 #1 y #2) y bloqueos (D1 #3 a #5), registrados en `main.py` y con documentación de errores en Swagger.
6. **Integración**: RBAC por rol y por propiedad, 404, 400, 422, turnos afectados reales y que siguen sin cancelar.
7. **Concurrencia**: test de bloqueo y turno simultáneos (D9).
8. **Evidencias**: `mutaciones-C-21.py`, `trazabilidad-C-21.py`, pytest, integración, mypy y `verify-C-21.md`.