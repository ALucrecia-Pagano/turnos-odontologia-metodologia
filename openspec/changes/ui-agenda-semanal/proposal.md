# Proposal

## Why

C-27 implementó la vista diaria con columnas por profesional, pero recepción y odontología necesitan una perspectiva semanal completa de un profesional para evaluar disponibilidad y coordinar turnos a lo largo de varios días (US-040 CA-2). La API `GET /api/agenda` ya admite rangos de hasta 31 días y filtros por profesional y sillón, por lo que la vista semanal no requiere cambios en el backend. Este change introduce la vista semanal por profesional, el control para alternar fluidamente entre día y semana conservando filtros y fecha, la navegación de 7 días y la adaptación a tablet sin alterar el comportamiento existente de la vista diaria. Governance **BAJO**: vista de solo lectura sin operaciones de escritura ni modificaciones de seguridad.

## What Changes

- **Vista semanal por profesional**: ruta protegida `/agenda?date=AAAA-MM-DD&view=week`, organizando los 7 días de la semana (lunes a domingo) en 7 columnas para un profesional seleccionado.
- **Alternancia día/semana**: control segmentado `[ Día | Semana ]` en `AgendaToolbar` que alterna entre `view=day` (o sin parámetro) y `view=week`, conservando `date`, `professionalId` y `chairId`. Un `view` desconocido o ausente cae a la vista diaria.
- **Preselección de profesional**: si no se pasa `professionalId` en la URL en vista semanal, para rol `odontologo` se selecciona su propio `professionalId` de la sesión; para `recepcion` o `administrador`, se selecciona el primer profesional activo en el mismo orden del selector de profesionales (`compareProfessionals`). El selector de profesional permanece habilitado para todos los roles.
- **Navegación semanal**: en vista semanal, los botones de navegación indican "Semana anterior" y "Semana siguiente" (texto visible y accesible) desplazando la fecha 7 días con `addDays`, admitiendo transiciones entre meses y años. "Hoy" navega a la semana que contiene la fecha actual del `Clock`.
- **Identificador accesible de día actual**: en vista semanal, la cabecera de la columna correspondiente al día de hoy se marca con el texto visible "Hoy" y el atributo `aria-current="date"`, nunca dependiendo exclusivamente del color.
- **Semana vacía con grilla informativa**: en vista semanal, el profesional elegido no cuenta como filtro activo para vaciar la pantalla; si no hay turnos, se mantiene la grilla con horarios y bloqueos y se muestra el aviso "No hay turnos esta semana para [profesional]". Con filtro de sillón activo, se muestra el aviso de filtro.
- **Responsive y accesibilidad**: scroll horizontal en tablet (768 px) con horas y cabeceras fijas; tarjetas en dos líneas (`HH:MM · Paciente` y `StatusBadge`) en columnas angostas (< 260 px); turnos cancelados visibles y atenuados con texto "Cancelado".
- **Condición dura de regresión**: los 127 tests existentes de C-27 deben seguir pasando sin ninguna modificación.

## Capabilities

### Modified Capabilities

- `frontend-agenda`: incorpora la vista semanal por profesional con 7 columnas (lunes a domingo), alternancia día/semana conservando fecha y filtros, preselección de profesional por rol, navegación de semanas que cruza mes y año, indicador accesible "Hoy" (`aria-current="date"`), estado vacío con grilla y aviso informativo, y renderizado adaptado a tablet.

## Impact

- **Código modificado en frontend**: `frontend/src/features/agenda/` (`agendaTime.ts`, `agendaLayout.ts`, `useAgenda.ts`, `AgendaToolbar.tsx`, `AgendaGrid.tsx`, `AgendaView.tsx`, `AgendaPage.tsx`).
- **Código nuevo**: tests unitarios y de componentes de la vista semanal en `frontend/src/features/agenda/`.
- **Sin cambios**: `backend/`, base de datos, APIs REST, autenticación, `.env`, Docker, paquetes npm ni dependencias de terceros.
- **Evidencias requeridas**: suite RED en `docs/evidencias/red-C-28/`, tests verdes en Vitest, mutaciones con detector de mutaciones inválidas, trazabilidad de escenarios, capturas en 1440 y 768 px y actualización de `docs/skills-mcp/aplicacion.md`.
