# Proposal

## Why

El caso de uso de alta de turnos ya existe y está probado en el dominio y en la capa de servicios (C-08, C-17): `book_appointment` bloquea profesional y sillón, valida referencias, horarios, bloqueos, pasado y solapamientos, y persiste el turno con su entrada de historial. Pero todavía no se puede invocar por HTTP. Sin `POST /api/appointments`, la recepcionista no puede dar turnos desde la interfaz, y el front de agenda no tiene cómo crear el recurso que después va a consultar.

## What Changes

- `POST /api/appointments`, autorizado con `APPOINTMENT CREATE`: recepción y administrador crean turnos; el odontólogo recibe `403`.
- Cuerpo con `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt` (ISO 8601 con zona horaria obligatoria) y `durationMin` opcional. El servidor genera `id`, `changedBy`, `status` y `endAt`; si falta `durationMin`, usa la duración de la prestación.
- Respuesta `201` con el turno creado en camelCase y tiempos UTC. El historial se persiste en la misma transacción, pero no se devuelve.
- `now` real en UTC y `APP_TIMEZONE` inyectados desde el borde de la API; `changedBy` sale del JWT, nunca del cuerpo.
- Rechazo de dominio traducido con `DomainRejectedError`: `409` para conflictos de agenda y `422` para reglas de validez, conservando todas las violaciones. Las referencias inexistentes del cuerpo responden `422 UNKNOWN_REFERENCE`, no `404`.
- Tests de integración con usuarios y tokens reales, fechas relativas al reloj real, y un test HTTP de dos altas del mismo hueco. La concurrencia real sigue verificándose en C-17.
- Sin migraciones, sin cambios de dominio y sin claves de idempotencia en el MVP.

## Capabilities

### New Capabilities
- `appointments-api`: alta de turnos por HTTP, autorización por rol, validación y traducción de violaciones, persistencia atómica del turno y su historial, y documentación OpenAPI.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo**: `backend/app/api/appointments.py` y tests de integración en `backend/tests/integration/`.
- **Código modificado**: `backend/app/api/schemas.py` (esquemas del alta y de la respuesta) y `backend/app/main.py` (registro del router bajo `protected_router`).
- **Sin cambios**: dominio, servicios de C-17, migraciones de Alembic, matriz RBAC, `docker-compose.yml` y variables de entorno.
- **Precondición**: C-20 (`api-catalogos-y-pacientes`) archivado, porque C-22 reutiliza su patrón de esquemas, servicios y tests.
