# Design — C-21 `api-horarios-y-bloqueos`

## Context

Este change expone por HTTP los horarios de atención y los bloqueos que C-16 ya guarda. Parte de `docs/evidencias/explore-C-21.md`. Las decisiones de abajo son las del explore, con las respuestas de la autora a P1–P4 (todas en la opción sugerida).

Depende de C-16 (repositorios), C-17 (turnos, `AppointmentReader`, bloqueo de filas), C-19 (matriz RBAC y `require_permission`) y C-20 (404 `NOT_FOUND`, esquemas en camelCase, servicios con commit y tests con tokens reales). **C-20 tiene que estar archivado antes de empezar el apply** (tarea 0.1).

## Goals / Non-Goals

**Goals**: consultar y reemplazar horarios; listar, crear y borrar bloqueos; informar turnos afectados sin cancelarlos; aplicar "solo lo propio" al odontólogo; evitar que un bloqueo y un turno simultáneos se crucen.

**Non-Goals**: editar bloqueos (se borra y se crea otro); reprogramar los turnos afectados (C-23); agenda y disponibilidad (C-24); pantallas (C-25 en adelante).

## Decisions

### D1 — Endpoints

| # | Método | Ruta | Recurso / Acción | Éxito |
|---|--------|------|------------------|-------|
| 1 | `GET` | `/api/professionals/{id}/working-hours` | `WORKING_HOURS` / `READ` | 200 |
| 2 | `PUT` | `/api/professionals/{id}/working-hours` | `WORKING_HOURS` / `UPDATE` | 200 |
| 3 | `GET` | `/api/professionals/{id}/blocks` | `BLOCK` / `READ` | 200 |
| 4 | `POST` | `/api/professionals/{id}/blocks` | `BLOCK` / `CREATE` | 201 |
| 5 | `DELETE` | `/api/blocks/{block_id}` | `BLOCK` / `DELETE` | 200 |

Rutas anidadas bajo el profesional para listar y crear (KB 07, Flujo 4). El `DELETE` es plano porque el id del bloqueo ya identifica al profesional.

### D2 — El `PUT` de horarios se autoriza con `UPDATE`

El `PUT` reemplaza la semana completa, y siempre se autoriza con `WORKING_HOURS UPDATE`, aunque no hubiera tramos antes o aunque se mande una lista vacía. Las filas `WORKING_HOURS CREATE`, `WORKING_HOURS DELETE` y `BLOCK UPDATE` de la matriz **no tienen ruta en C-21**. *Alternativa descartada*: elegir la acción según el cuerpo, que daría permisos distintos a la misma ruta y le impediría a la odontóloga vaciar su propia semana.

### D3 — `Scope.OWN`: el odontólogo solo opera sobre su profesional

Un helper único en `backend/app/api/` (por ejemplo `ensure_own_professional(permission, professional_id)`): si `permission.scope` es `Scope.OWN` y el `professional_id` no es el del `Actor`, lanza el mismo 403 que `RequirePermission` de C-19: `FORBIDDEN_OPERATION` con el mensaje de `PERMISSION_MESSAGES` de esa celda (por ejemplo, `"No tiene permiso para leer horarios."`). En `DELETE /api/blocks/{block_id}` se carga primero el bloqueo y se compara su `professional_id`.

Orden de las respuestas: 401 (token) → 403 por rol (matriz) → 404 si el profesional o el bloqueo no existe → 403 por propiedad. Revisar el 404 antes del 403 de propiedad deja saber que un id existe, pero los profesionales son visibles para todos los roles (`PROFESSIONAL READ`).

### D4 — Formato de horas

- **Horarios**: `{ "weekday": 1, "start": "09:00", "end": "13:00" }`, en hora local. `start` y `end` cumplen `HH:MM` con horas de 00 a 23 y minutos de 00 a 59; `end` además acepta `"24:00"` (minuto 1440). Un texto que no cumple el formato → 400. Un tramo con formato válido pero inválido para el dominio (inicio ≥ fin, solapado) → 422 con la violación del dominio.
- **Bloqueos**: `startAt` y `endAt` en ISO 8601 con zona horaria **obligatoria**. Sin zona → 400 antes de llegar al dominio, que lanzaría `ValueError` (un 500). Las respuestas devuelven UTC con `Z`.
- **Filtros `from` y `to`** del listado de bloqueos: mismo formato que los bloqueos, con zona obligatoria.

### D5 — Turnos fuera del horario nuevo (regla de dominio nueva)

Función pura en `backend/app/domain/rules/working_hours.py`:

```python
def appointments_outside_working_hours(
    professional_id: UUID,
    appointments: Sequence[Appointment],
    working_hours: Sequence[WorkingHours],
    tz: ZoneInfo,
    now: datetime,
) -> list[Appointment]:
```

Filtra los turnos de ese profesional, en `OCCUPYING_STATUSES` y con `start_at >= now`, y devuelve los que `check_working_hours` marca con `OUTSIDE_WORKING_HOURS`, ordenados por `(start_at, str(id))`. No lee el reloj: `now` llega por parámetro (regla dura del proyecto). Las guardias de pureza del dominio tienen que seguir pasando sin tocar su allowlist.

### D6 — Bloqueos: alta con id del servidor, borrado real, sin edición

El `POST` genera el id con `uuid4`; el cliente no lo manda. El `DELETE` borra de verdad (C-16) y responde 200 con el bloqueo borrado, que es lo que devuelve `BlockRepository.delete`. Inexistente → 404 `{ "code": "NOT_FOUND", "message": "Bloqueo no encontrado." }`. No hay `PUT` de bloqueos.

### D7 — Respuestas con turnos afectados

- `POST /api/professionals/{id}/blocks` → 201 `{ "block": {...}, "affectedAppointments": [...] }`.
- `PUT /api/professionals/{id}/working-hours` → 200 `{ "workingHours": [...], "appointmentsOutsideHours": [...] }`.
- Resumen de cada turno: `id`, `patientId`, `patientName`, `chairId`, `startAt`, `endAt` y `status`. `patientName` le ahorra al front una consulta por turno, y el odontólogo ya puede leer pacientes (`PATIENT READ`).
- Guardar siempre es éxito, aunque haya afectados (RN-DI-04).
- Los turnos afectados por un bloqueo salen de `BlockRepository.list_affected_appointments(block)`.
- Los turnos fuera de horario se buscan **desde `now` hasta `now + 90 días`** (respuesta de la autora a P2), con `AppointmentRepository.list_for_professional_in_range`.

### D8 — Profesional inexistente o inactivo

Inexistente → 404 `{ "code": "NOT_FOUND", "message": "Profesional no encontrado." }`, verificado en el servicio antes de llamar al repositorio, así no aparece el 422 `UNKNOWN_REFERENCE` de C-16. Inactivo → se puede leer y guardar (C-16: inactivo impide dar turnos, no configurar la agenda).

### D9 — Bloqueo de la fila del profesional (respuesta de la autora a P1: sí)

`book_appointment` de C-17 toma `SELECT ... FOR UPDATE` sobre el profesional y **después** lee horarios y bloqueos. Sin el mismo lock, un turno y un bloqueo simultáneos pueden guardarse los dos, y el bloqueo informaría "sin afectados".

`replace_working_hours` y `create_block` toman el lock de la fila del profesional **antes** de escribir y de calcular los afectados, reutilizando `_lock_resources` de `backend/app/services/appointments.py`. Si conviene, se mueve a un módulo común de `backend/app/services/` sin cambiar su comportamiento; los tests de C-17 tienen que seguir pasando sin modificarlos. `delete_block` no necesita el lock: borrar solo libera horario.

Se prueba con dos tests de concurrencia, con el mismo patrón de C-17: dos sesiones reales en hilos, espera verificada con `pg_locks` y `SET lock_timeout`, sin `time.sleep`. Los servicios aceptan `auto_commit=False` solo para que el test retenga el lock.

### D10 — Organización del código

- `backend/app/services/availability.py`: `get_working_hours`, `replace_working_hours`, `list_blocks`, `create_block` y `delete_block`, con commit explícito (como C-17 y C-20). Los repositorios nunca hacen commit.
- `backend/app/api/working_hours.py` y `backend/app/api/blocks.py`, con tags de Swagger "Horarios" y "Bloqueos", y cada ruta con `require_permission`. El guardián de rutas de C-19 (`test_route_guards.py`) tiene que pasar sin modificarlo.
- Esquemas en `backend/app/api/schemas.py`, en camelCase con `extra="forbid"`.
- Los errores 400, 403, 404 y 422 se documentan en Swagger en cada ruta.

### D11 — Listado de bloqueos con `from` y `to` (respuesta de la autora a P3: sí)

Sin filtros, devuelve todos los bloqueos del profesional ordenados por `startAt`. Con `from` y `to`, solo los que se solapan con `[from, to)`. Se agrega `BlockRepository.list_by_professional_in_range(professional_id, start_at, end_at)` con su test de integración. Con un solo filtro, el otro extremo queda abierto.

### D12 — Tests sin mocks

- Usuarios y tokens reales: `POST /api/auth/login` con los usuarios del helper de hash barato de C-19. El usuario `odontologo` está vinculado a la profesional `...0001`.
- Los turnos afectados se crean con `book_appointment` de C-17 (con horario, paciente, sillón y prestación cargados) y después se cambia el horario o se crea el bloqueo por HTTP. Se verifica la respuesta **y** que el turno sigue `reservado` en la base.
- PROHIBIDO `unittest.mock`, `patch`, `monkeypatch` y `dependency_overrides`.

### D13 — Fechas de los tests relativas al reloj real

La API toma el momento actual con `datetime.now(UTC)`, como `POST /api/auth/login`, y no se puede reemplazar en los tests (sin `dependency_overrides`). Un test con una fecha fija dejaría de andar cuando esa fecha pase. Por eso los tests de integración calculan el **lunes futuro L**: el primer lunes que esté al menos 7 días después del momento actual, siempre dentro de la ventana de 90 días de D7. Los escenarios de la spec que dicen "el lunes futuro L" se refieren a esa fecha. Los tests unitarios del dominio (D5) sí usan fechas fijas, porque reciben `now` por parámetro.

## Decisiones registradas de la autora

- **P1** (lock de la fila del profesional): sí, D9.
- **P2** (ventana de turnos fuera de horario): 90 días desde el momento actual, D7.
- **P3** (filtros `from` y `to`): sí, D11.
- **P4** (`patientName` en los turnos afectados): sí, D7.

## Risks / Trade-offs

- **[Riesgo] Carrera entre un turno y un bloqueo** → D9, con dos tests de concurrencia.
- **[Riesgo] Un bloqueo sin zona horaria llega al dominio y da 500** → validación en el esquema, 400 (D4).
- **[Riesgo] Turnos fuera de horario más allá de 90 días no se informan** → se acepta y se documenta: un cambio de horario se revisa con la agenda de los próximos meses.
- **[Trade-off] El 404 antes del 403 de propiedad** revela que un id existe → los profesionales ya son públicos para todos los roles.
- **[Trade-off] Tres filas de la matriz sin ruta** (`WORKING_HOURS CREATE/DELETE`, `BLOCK UPDATE`) → documentado en D2 y D6.

## Migration Plan

Sin migraciones. Rollback: revertir el commit del change.
