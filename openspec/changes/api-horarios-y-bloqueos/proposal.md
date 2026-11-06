# Proposal

## Why

Los horarios de atención y los bloqueos ya se validan en el dominio (C-05, C-06) y se guardan en la base (C-16), pero no se pueden consultar ni cargar por HTTP. Sin esto, la odontóloga no puede cargar sus vacaciones ni su semana de trabajo, y el front de agenda (C-27) no tiene de dónde leerlas. Además, cambiar un horario o crear un bloqueo tiene que avisar qué turnos quedan pisados, sin cancelarlos (US-010 CA-3, US-011 CA-3, RN-DI-04).

## What Changes

- `GET` y `PUT /api/professionals/{id}/working-hours`: consulta y reemplazo de la semana completa, con horas locales `"HH:MM"` y `"24:00"` como fin válido.
- `GET` y `POST /api/professionals/{id}/blocks`, y `DELETE /api/blocks/{block_id}`: listado con filtros `from` y `to`, alta con zona horaria obligatoria y borrado real.
- Las respuestas de `PUT` de horarios y de `POST` de bloqueos informan los turnos afectados (`appointmentsOutsideHours` y `affectedAppointments`), con el nombre del paciente, sin cancelarlos.
- Función pura nueva del dominio, `appointments_outside_working_hours`, para los turnos que quedan fuera de un horario nuevo.
- `Scope.OWN` aplicado por la API: el odontólogo solo opera sobre su propio profesional; si toca otro, `403 FORBIDDEN_OPERATION`.
- Bloqueo de la fila del profesional (`SELECT ... FOR UPDATE`) al crear bloqueos y cambiar horarios, para que no se crucen con un alta de turno simultánea.
- Servicio de aplicación `backend/app/services/availability.py` con commit explícito.

## Capabilities

### New Capabilities
- `working-hours-and-blocks-api`: endpoints de horarios de atención y bloqueos, turnos afectados, permisos por propiedad y serialización con las altas de turnos.

### Modified Capabilities
- `appointment-scheduling`: se suma la regla pura de turnos que quedan fuera de un horario de atención.

## Impact

- **Código nuevo**: `backend/app/services/availability.py`, `backend/app/api/working_hours.py`, `backend/app/api/blocks.py`, la función `appointments_outside_working_hours` en `backend/app/domain/rules/working_hours.py`, y sus tests unitarios y de integración.
- **Código modificado**: `backend/app/main.py` (routers), `backend/app/api/schemas.py`, `backend/app/repositories/blocks.py` (listado por rango), y posiblemente el módulo del bloqueo de filas de C-17 si se mueve a un lugar común (D9).
- **Sin cambios**: migraciones de Alembic, matriz RBAC, `docker-compose.yml` y variables de entorno.
