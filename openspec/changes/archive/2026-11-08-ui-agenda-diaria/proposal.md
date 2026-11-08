# Proposal

## Why

C-26 dejó login, sesión y un shell con todo el menú deshabilitado; el usuario todavía no tiene una pantalla donde ver la agenda del consultorio. C-27 es el primer change de negocio del frontend: convierte `GET /api/agenda` (probada en C-24 con `http-C-24.txt`) en una agenda diaria legible, con columnas por profesional, turnos posicionados en hora local, horarios, bloqueos, filtros y estados. Sin esta vista, C-28, C-29, C-30 y C-31 no tienen base visual. Governance **BAJO**: vista de solo lectura, no escribe datos ni toca seguridad.

## What Changes

- **Ruta `/agenda`**: ruta protegida visible para los tres roles; `/` redirige a `/agenda`; el menú habilita `Agenda` y mantiene el resto de los ítems futuros deshabilitados con `"Próximamente"`.
- **Carga inyectable**: la página recibe el `fetch`/cliente por parámetro y un `Clock` inyectado; el día inicial y `Hoy` no dependen del reloj global.
- **Zona horaria (C1)**: `from`/`to` viajan como fechas locales `YYYY-MM-DD`; todas las horas y fechas visibles se formatean con el `timezone` que devuelve `GET /api/agenda`; ningún componente escribe una zona a mano. El respaldo vive en un único archivo de configuración y se usa solo antes de la primera respuesta.
- **Grilla diaria**: eje de horas dinámico, una columna por profesional (incluye inactivos con marca), posición y alto por minutos locales, carriles para turnos superpuestos y altura mínima legible.
- **Capas**: bandas de horarios de atención, bloqueos rayados con motivo y etiqueta accesible, turnos con color de estado más texto y cancelados atenuados sin ocultarlos.
- **Filtros**: profesional y sillón, combinables, con estado en la URL y la asimetría visible: `professionalId` filtra turnos, horarios y bloqueos; `chairId` filtra solo turnos.
- **Navegación**: `Anterior`, `Siguiente`, `Hoy` y selector de fecha, con `date` en la URL y `push` para acciones del usuario.
- **Estados**: carga, actualización sin parpadeo, vacío, error con reintento; `401` delegado a C-26 y `403` mostrado con las `violations` sin cerrar sesión.
- **Accesibilidad y responsive**: leyenda, nombres accesibles, `aria-live`, toggle a tabla semántica y scroll horizontal con encabezado y columna de horas fijos en escritorio/tablet.
- **Evidencias**: RED en `docs/evidencias/red-C-27/`, Vitest, `tsc`, ESLint, mutaciones, trazabilidad, verificación manual con datos ficticios y capturas, `verify-C-27.md`.

## Capabilities

### New Capabilities

- `frontend-agenda`: agenda diaria de solo lectura sobre `GET /api/agenda`; ruta y menú, carga inyectable, hora local según la respuesta, grilla con eje/columnas/carriles, horarios, bloqueos, cancelados, estados, filtros por profesional y sillón en la URL, navegación de día, accesibilidad y responsive.

### Modified Capabilities

- Ninguna. C-27 agrega una capacidad nueva y ajusta tests de C-26 dentro del apply (menú y `/`); el contrato de `frontend-auth-session` no cambia y no se editan specs archivados.

## Impact

- **Código nuevo**: `frontend/src/features/agenda/` (`agendaConfig.ts`, `agendaTime.ts`, `clock.ts`, `agendaLayout.ts`, `agendaApi.ts`, `useAgenda.ts`, `AgendaPage.tsx`, `AgendaView.tsx`, `AgendaToolbar.tsx`, `AgendaGrid.tsx`, `AgendaTable.tsx`, estilos) y los ajustes de router/menú en `frontend/src/App.tsx` y `frontend/src/features/auth/menuFor.ts`.
- **Código modificado**: `frontend/src/shared/components/AppShell.tsx` (ítems habilitados como `NavLink`), `frontend/src/shared/api/client.ts` (solo si se agrega `signal` aditivo) y los tests de C-26 impactados por habilitar Agenda y redirigir `/`.
- **Sin cambios**: `backend/`, `openspec/specs/`, `CHANGES.md`, `README.md`, `knowledge-base/`, `AGENTS.md`, `CLAUDE.md`, `.env`, `docker-compose.yml` y los demás changes. No se agregan dependencias, variables ni secretos.
- **Precondición**: C-26 implementado, verde y **ARCHIVADO**. Si no lo está, el apply se detiene (tarea 0.1).
- **Governance**: BAJO; vista de solo lectura con datos ficticios del seed y sin operaciones de escritura.
