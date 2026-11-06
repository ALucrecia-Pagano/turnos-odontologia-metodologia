# Proposal

## Why

C-17 ya tiene los servicios de cancelar, reprogramar y cambiar estado con el historial persistido en la misma transacción, y C-21 dejó el helper de propiedad que reutiliza la API. Pero todavía no existen las rutas HTTP del ciclo de vida. Sin C-23, la recepcionista y el odontólogo no pueden cancelar, reprogramar, marcar un turno como atendido o ausente, ni consultar el historial desde la interfaz.

## What Changes

- `POST /api/appointments/{id}/cancel`, autorizado con `APPOINTMENT CANCEL`: recepción y administración cancelan turnos `reservado` o `confirmado`; el odontólogo recibe `403`.
- `POST /api/appointments/{id}/reschedule`, autorizado con `APPOINTMENT RESCHEDULE`: recepción y administración mueven inicio, profesional, sillón y/o duración; revalida todas las RN-AG, conserva la duración real si no se manda `durationMin`, excluye al propio turno y vuelve a `reservado`; el odontólogo recibe `403`.
- `POST /api/appointments/{id}/status`, autorizado con `APPOINTMENT CHANGE_STATUS`: acepta solo `confirmado`, `atendido` y `ausente`; `cancelado` y `reservado` se rechazan con `400` por esquema. El odontólogo solo opera sus turnos y el `403` por propiedad lo decide el dominio.
- `GET /api/appointments/{id}/history`, autorizado con `APPOINTMENT_HISTORY READ`: devuelve el historial inmutable y ascendente, con `from`, `to`, `changedBy`, `changedByName`, `changedAt` y `reschedule`. El odontólogo solo lee el historial de sus turnos; recepción y administración leen todos.
- Respuestas de mutación `200` con el mismo `AppointmentResponse` de C-22. Turno inexistente `404` con `"Turno no encontrado."`; choques, bloqueos y fuera de horario `409`; reglas de validez y transiciones inválidas `422`; entrada malformada `400`.
- `now` UTC y `APP_TIMEZONE` inyectados en el borde; `changedBy` sale del JWT. Se reutilizan los servicios de C-17, la matriz RBAC de C-19, los errores de C-20, el router y los esquemas de C-22 y el helper `ensure_own_professional` de C-21. No se crea `ownership.py` ni se duplica la comparación.
- `changedByName` se resuelve con una sola lectura de `UserRepository`, sin exponer otros campos del usuario.
- Sin migraciones, sin cambios de dominio, sin cambios en RBAC ni en Docker, y sin soporte de `note`.

## Capabilities

### New Capabilities
- `appointments-api`: ciclo de vida del turno por HTTP (cancelar, reprogramar, cambiar estado y leer el historial), autorización por rol y por propiedad, traducción de violaciones, y documentación OpenAPI.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo**: extensión de `backend/app/api/appointments.py` con las cuatro rutas y tests de integración en `backend/tests/integration/`.
- **Código modificado**: `backend/app/api/schemas.py` (esquemas de entrada y de historial), `backend/app/services/appointments.py` (lectura de historial), `backend/app/repositories/users.py` (`get_display_names`) y `backend/app/main.py` si hace falta registrar o ajustar el router.
- **Sin cambios**: dominio, migraciones de Alembic, matriz RBAC, `docker-compose.yml` y variables de entorno.
- **Precondición**: C-21 (`api-horarios-y-bloqueos`) y C-22 (`api-dar-turno`) archivados y verdes antes de empezar el apply, porque C-23 reutiliza el router, los esquemas, el patrón de tests y el helper de propiedad.
