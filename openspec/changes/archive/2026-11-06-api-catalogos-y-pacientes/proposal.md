# Proposal

## Why

La API REST cuenta con su infraestructura HTTP y autenticación JWT con roles RBAC (C-18 y C-19), pero no expone endpoints para administrar los datos maestros del consultorio. Los changes de agenda (C-21 a C-24) requieren que los profesionales, sillones, prestaciones y pacientes puedan gestionarse vía HTTP respetando los permisos por rol y las reglas de unicidad e integridad del dominio.

## What Changes

- Endpoints `/api/professionals` para alta, edición, desactivación, reactivación, listado y detalle bajo la matriz RBAC, incluyendo el campo opcional `licenseNumber`.
- Endpoints `/api/chairs` para alta, edición, desactivación, reactivación, listado y detalle bajo la matriz RBAC.
- Endpoints `/api/services` para alta, edición, desactivación, reactivación, listado y detalle bajo la matriz RBAC.
- Endpoints `/api/patients` para alta, edición, listado con búsqueda por texto y detalle bajo la matriz RBAC, sin rutas de desactivación ni borrado.
- Matriz RBAC aplicada por celda: administrador gestiona catálogos y pacientes; recepción gestiona pacientes y lee catálogos; odontólogo únicamente lee catálogos y pacientes.
- Desactivación mediante `POST /api/{recurso}/{id}/deactivate` (autorizado con acción `DELETE`) y reactivación mediante `POST /api/{recurso}/{id}/reactivate` (autorizado con acción `UPDATE`), respondiendo `200` con la entidad actualizada de forma idempotente.
- Edición mediante `PUT /api/{recurso}/{id}` completo e idempotente con validación de unicidad que excluye a la propia entidad.
- Respuesta `404` unificada con cuerpo `{ "code": "NOT_FOUND", "message": "<recurso> no encontrado." }` cuando el identificador no existe en rutas con `{id}`.
- Servicios de aplicación en `backend/app/services/catalog.py` y `backend/app/services/patients.py` con transaccionalidad explícita (`auto_commit=True`).
- Esquemas Pydantic V2 en `camelCase` con `extra="forbid"`.

## Capabilities

### Modified Capabilities
- `catalog-and-patients`: endpoints REST de profesionales, sillones, prestaciones y pacientes, matriz RBAC, edición y ciclo de vida de recursos.

## Impact

- **Código nuevo**: `backend/app/services/catalog.py`, `backend/app/services/patients.py`, `backend/app/api/professionals.py`, `backend/app/api/chairs.py`, `backend/app/api/services.py`, `backend/app/api/patients.py`, `backend/app/domain/catalog/update.py` y tests de integración en `backend/tests/integration/`.
- **Código modificado**: `backend/app/main.py` (inclusión de routers en `protected_router`), `backend/app/api/schemas.py`, `backend/app/api/errors.py` (manejador de 404 unificado), `backend/app/repositories/catalog.py` y `backend/app/repositories/patients.py` (métodos de actualización y soporte de `license_number`).
- **Sin cambios**: migraciones de Alembic, modelo relacional existente, `docker-compose.yml`, configuración de entorno.
