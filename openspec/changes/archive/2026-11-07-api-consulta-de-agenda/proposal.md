# Proposal

## Why

C-17, C-20, C-21, C-22 y C-23 ya tienen la persistencia, la API base, los horarios y bloqueos, el alta y el ciclo de vida del turno. Falta la vista de lectura: la UI no puede dibujar un día o una semana con turnos, horarios y bloqueos en una sola consulta, ni abrir un turno puntual enriquecido. C-24 cierra esa deuda y destraba el GATE 14, que habilita el frontend.

## What Changes

- `GET /api/agenda?from&to&professionalId&chairId`: fechas locales `YYYY-MM-DD`, `to` inclusivo y rango máximo de 31 días; filtros `professionalId` y `chairId` opcionales y combinables con AND.
- Respuesta en un sobre `{ from, to, timezone, appointments, workingHours, blocks }`: turnos con `patientName`, `professionalName`, `chairName`, `serviceName`, `startAt`/`endAt` en UTC con `Z` y `status`; horarios como plantilla semanal; bloqueos con `reason`.
- Los turnos cancelados se incluyen con su `status` y sin filtro de estado; los horarios y bloqueos se filtran por profesional, no por sillón.
- `GET /api/appointments/{id}` con el mismo turno enriquecido y `404` con `"Turno no encontrado."`.
- Ambas rutas autorizadas con `APPOINTMENT READ_AGENDA`; el odontólogo lee toda la agenda en solo lectura, sin comparación de propiedad.
- `400` por falta de `from`/`to`, fecha inválida, `to < from`, rango de más de 31 días, UUID malformado y parámetro de query desconocido; `401` sin token.
- Sin cambios de dominio, migraciones, RBAC, índices, Docker ni variables de entorno; sin `note`.

## Capabilities

### New Capabilities

- `agenda-api`: consulta de la agenda diaria y semanal en hora local con turnos enriquecidos, horarios de atención, bloqueos, filtros y validación de la ventana.

### Modified Capabilities

- `appointments-api`: se agrega el requisito de consulta de un turno por id (`GET /api/appointments/{id}`) al ciclo de vida existente.

## Impact

- **Código nuevo**: `backend/app/api/agenda.py`, `backend/app/services/agenda.py` y tests de esquema, integración y OpenAPI en `backend/tests/`.
- **Código modificado**: `backend/app/api/schemas.py` (esquema de query y respuestas de agenda), `backend/app/api/appointments.py` (detalle), `backend/app/repositories/appointment.py` y `backend/app/repositories/blocks.py` (lecturas con nombres y rango), `backend/app/api/errors.py` (tres mensajes de `400`) y `backend/app/main.py` (registro del router).
- **Sin cambios**: dominio, migraciones de Alembic, matriz RBAC, `docker-compose.yml` y variables de entorno.
- **Precondición**: C-21 (`api-horarios-y-bloqueos`), C-22 (`api-dar-turno`) y C-23 (`api-ciclo-de-vida-del-turno`) archivados y verdes antes del apply, porque los tests usan las rutas reales de bloqueo, alta y cancelación (C3).
