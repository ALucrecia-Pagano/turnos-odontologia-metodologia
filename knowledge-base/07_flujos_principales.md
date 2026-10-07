# Flujos Principales

## Flujo 1: Dar un turno

> Flujo completo del MVP. C-02 implementa solo el núcleo de dominio `validateNewAppointment` con las reglas de solapamiento por profesional y por sillón (RN-AG-01, RN-AG-02), la duración por prestación, el rechazo de duración no positiva (`INVALID_DURATION`) y el caso de turnos consecutivos; no incluye API, transacción ni los códigos de horario, bloqueo, pasado ni referencias (`OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `IN_THE_PAST`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`), que van en C-03 a C-08 (el flujo completo con mensajes en español se cierra en C-08).

**Disparador**: la secretaria completa el formulario de turno.
**Actor**: secretaria / recepción (o administrador).

**Pasos**:
1. La UI envía `POST /api/appointments` con `{ patientId, professionalId, chairId, serviceId, startAt, durationMin? }` (`startAt` en ISO-8601 con offset; `durationMin` opcional).
2. La API valida la forma de la entrada (Zod) y el rol (RN-AC-01).
3. La API abre una transacción `BEGIN IMMEDIATE`.
4. Carga el **contexto**: profesional, sillón, prestación, paciente, tramos laborales del profesional, bloqueos del día, turnos activos del profesional y del sillón que puedan solaparse, y `now`.
5. Llama a `validateNewAppointment(input, context)` del dominio (puro).
6. Si el resultado es `ok`: inserta el turno en `reservado` y la entrada de historial (`from_status` nulo) en la misma transacción; `COMMIT`; responde `201` con el turno.
7. Si hay violaciones: `ROLLBACK`; responde `409` (solapamiento) o `422` (regla de validez) con la lista de violaciones.

```
Recepción → UI → API ──(contexto)──► SQLite
                  │  validateNewAppointment (dominio puro)
                  │◄─ ok | violaciones[]
                  ├─ ok  → INSERT turno + historial → 201
                  └─ err → 409/422 { violations: [...] }
```

**Contrato de error** (ejemplo):

```json
{
  "violations": [
    { "code": "PROFESSIONAL_OVERLAP",
      "message": "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (turno a1b2).",
      "conflictingAppointmentId": "a1b2" },
    { "code": "CHAIR_OVERLAP",
      "message": "El Sillón 2 está ocupado de 10:00 a 10:30 (turno c3d4).",
      "conflictingAppointmentId": "c3d4" }
  ]
}
```

**Códigos de violación**: `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `IN_THE_PAST`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_TRANSITION`.

**Casos de error**:
- Entrada malformada → `400`.
- Rol sin permiso → `403`; sin rol → `401`.
- Referencia inexistente → `422 UNKNOWN_REFERENCE`.
- Carrera entre dos altas simultáneas → la segunda se valida tras la primera dentro de su transacción y recibe el conflicto.

## Flujo 2: Reprogramar un turno

**Disparador**: la secretaria mueve un turno.
**Actor**: recepción / administrador.

**Pasos**:
1. `POST /api/appointments/:id/reschedule` con nuevos `startAt`, `professionalId?`, `chairId?`, `durationMin?`.
2. Transacción: carga el turno y el contexto del **nuevo** destino.
3. El dominio verifica que el estado sea `reservado` o `confirmado` (RN-TU-03) y revalida RN-AG **excluyendo al propio turno** de los solapamientos.
4. Si es válido: actualiza el turno, lo pasa a `reservado` y agrega historial con el intervalo anterior en `note`.

**Casos de error**: estado terminal → `422 INVALID_TRANSITION`; destino en el pasado, fuera de horario, bloqueado o solapado → violaciones como en el Flujo 1.

## Flujo 3: Cambiar estado / cancelar

**Disparador**: recepción u odontólogo marca confirmado, atendido, ausente o cancelado.

**Pasos**:
1. `POST /api/appointments/:id/status` con `{ toStatus, note? }`.
2. El dominio aplica la tabla de transiciones (RN-TU-02) y las precondiciones de tiempo (RN-TU-05).
3. Si es válido: actualiza el estado e inserta historial (`changed_by`, `changed_at`). Si pasa a `cancelado` o `ausente`, el hueco queda libre.

**Casos de error**: transición inválida → `422 INVALID_TRANSITION`; `atendido`/`ausente` antes del inicio → `422`; odontólogo sobre turno ajeno → `403`.

## Flujo 4: Configurar horarios y bloqueos

**Actor**: odontólogo (propios) o administrador.

**Pasos**: `PUT /api/professionals/:id/working-hours` reemplaza los tramos semanales (valida RN-DI-02); `POST /api/professionals/:id/blocks` crea un bloqueo (RN-DI-03). La respuesta de creación de bloqueo incluye la lista de **turnos existentes afectados** (RN-DI-04); no se cancelan.

## Flujo 5: Consultar agenda

**Actor**: recepción u odontólogo.

**Pasos**: `GET /api/appointments?from=&to=&professionalId=&chairId=` devuelve turnos del rango (incluye el estado). La UI arma la vista diaria/semanal por profesional o por sillón. Los turnos `cancelado` se pueden ocultar con un filtro.

## Flujo 6: Desarrollo guiado por tests (proceso)

Cada escenario de [06_funcionalidades.md](06_funcionalidades.md) → un test Vitest en `packages/domain/test/` **antes** de escribir la regla (RED → GREEN → TRIANGULATE → REFACTOR). El dominio se prueba con tablas de casos y reloj fijo inyectado.
