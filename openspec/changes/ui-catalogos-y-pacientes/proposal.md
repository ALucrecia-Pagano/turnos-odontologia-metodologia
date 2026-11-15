# Proposal

## Why

La API de catálogos y pacientes (C-20) está completa y testeada, pero el frontend no tiene pantallas para usarla: "Catálogos" y "Pacientes" siguen en el menú como botones deshabilitados con "Próximamente" y las rutas `/catalogos` y `/pacientes` caen en `NotFoundPage`. Hoy la recepción no puede buscar ni dar de alta un paciente desde la web, y el administrador solo puede mantener profesionales, sillones y prestaciones por API o por seed. C-33 (`CHANGES.md`, `[C-33] ui-catalogos-y-pacientes`) cierra US-020, US-021 y US-022 del lado de la interfaz.

## What Changes

- **Pantalla `/pacientes`** (nueva, propia):
  - Listado en tabla con nombre, DNI, teléfono y obra social (texto libre; un dato ausente se muestra como "Sin dato").
  - Búsqueda propia de la pantalla con `GET /api/patients?query=` (por nombre o DNI, como ya resuelve el backend). No se reutiliza `PatientSearchGroup` (es un selector de radio del formulario de turno; ver design.md D5).
  - Alta y edición en `Dialog` con exactamente cuatro campos: nombre, DNI, teléfono y obra social. Sin campos clínicos (RN-PA-01).
- **Pantalla `/catalogos?seccion=profesionales|sillones|prestaciones`** (nueva):
  - Un componente genérico de catálogo, configurado por entidad, para las tres secciones. Sección ausente o desconocida: profesionales.
  - Tabla con el estado como texto visible "Activo"/"Inactivo" (se listan también los inactivos).
  - Alta y edición en `Dialog`; desactivar y reactivar con confirmación dentro del diálogo.
- **Permisos por rol**: los del RBAC del backend (`backend/app/auth/permissions.py:62-77`). Lo que un rol no puede hacer no se muestra:
  - Catálogos: administrador escribe; recepción y odontólogo, solo lectura.
  - Pacientes: administrador y recepción crean y editan; odontólogo, solo lectura.
- **Errores**: 409 y 422 con el mensaje literal del backend en `role="alert"`, sin `aria-invalid` en campos ante un 409; 400 por campo con `aria-invalid="true"`.
- **Menú**: "Catálogos" y "Pacientes" pasan de "Próximamente" a enlaces habilitados para los tres roles. Es un **cambio de requisito** sobre tests existentes del menú (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y los que correspondan), sin seams. El conteo real de aserciones modificadas por archivo se mide con `git diff` en el apply y se declara como desvío en `verify-C-33.md` (design.md D9).
- **Rutas**: `/catalogos` y `/pacientes` dentro de `AppShell` en `App.tsx`.
- **Orden de entrega con recorte**: (1) pacientes, listado y búsqueda; (2) catálogos en solo lectura y menú; (3) formularios de alta y edición en `Dialog`; (4) desactivar y reactivar en catálogos. **Plan B** si el 17/11 no llega: se entrega hasta el paso (2) (design.md, "Plan B").

### Fuera de alcance

- **Desactivar, reactivar o borrar pacientes**: el backend no lo permite. `PatientInput` y `PatientResponse` no tienen `active` (`backend/app/api/schemas.py:91-97` y `126-133`); no existe ruta `/patients/{id}/deactivate` (`backend/app/api/patients.py`); y `(Resource.PATIENT, Action.DELETE): {}` (`backend/app/auth/permissions.py:77`). La pantalla de pacientes no ofrece esas acciones. El "desactivar" de `CHANGES.md` aplica solo a profesionales, sillones y prestaciones.
- Cambios en backend (endpoints, esquemas, `max_length`, paginación de `GET /patients`).
- Catálogo de obras sociales o validación de cobertura (backlog post-MVP).
- Validar en el cliente las reglas del dominio (DNI de 7 u 8 dígitos, duración múltiplo de 5 y hasta 480). El backend responde y la UI muestra su mensaje literal. Única excepción: la duración que no es un número entero no se envía.
- Gestión de usuarios y el ítem "Turnos" del menú (siguen con "Próximamente").

## Capabilities

### New Capabilities

- `frontend-catalogs-and-patients`: pantallas web `/pacientes` (listado, búsqueda, alta y edición, sin datos clínicos) y `/catalogos` (profesionales, sillones y prestaciones con estado visible, alta, edición, desactivar y reactivar con confirmación). Incluye permisos por rol según el RBAC del backend, errores literales del backend, un solo mensaje de estado vigente, solo tokens existentes y diseño adaptable a 1440, 768 y 390 px.

### Modified Capabilities

- `frontend-foundation`: el requisito "Navegación de AppShell sin cajas" pasa a tener "Catálogos" y "Pacientes" como enlaces activos a `/catalogos` y `/pacientes` para los tres roles. Solo "Turnos" y "Usuarios y roles" quedan como ítems futuros con "Próximamente".

## Impact

- **Frontend**:
  - Nuevo: `frontend/src/features/pacientes/` (capa de API, página, diálogo de formulario, estilos y tests).
  - Nuevo: `frontend/src/features/catalogos/` (capa de API, configuración por entidad, página, sección genérica, diálogos de formulario y confirmación, etiqueta Activo/Inactivo, estilos y tests).
  - Modificado: `frontend/src/App.tsx` (2 rutas) y `frontend/src/features/auth/menuFor.ts` (habilitación de 2 ítems).
  - Tests existentes: aserciones de los tests de menú (cambio de requisito, design.md D9), con el conteo real por archivo medido con `git diff` en el apply. No se renombran títulos de tests.
- **Backend**: sin cambios. Se consumen los contratos de C-20 tal como están (design.md, "Contratos del backend usados").
- **Sin dependencias nuevas.**
- **Governance**: BAJO (`CHANGES.md`, C-33). Datos de prueba y capturas solo ficticios (RN-PA-02).
