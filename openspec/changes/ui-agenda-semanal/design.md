# Design

## Context

C-27 proveyó la infraestructura central de visualización de agenda en el frontend: `agendaTime.ts` (manejo de zona horaria, instantes UTC y funciones de fechas locales), `agendaLayout.ts` (cálculo de escala horaria con `computeAxis` y posicionamiento de carriles con `assignLanes`), `AgendaToolbar.tsx` (filtros y navegación), `AgendaGrid.tsx` (grilla con bandas de horario, bloques y tarjetas accesibles) y `useAgenda.ts` (hook de carga coordinada).

Este diseño define cómo extender dicha base para soportar la vista semanal por profesional (`US-040 CA-2`) en `/agenda?view=week`, manteniendo una estricta condición de regresión: los 127 tests existentes de C-27 deben seguir pasando sin modificación alguna.

## Goals / Non-Goals

**Goals:**
- Implementar la vista semanal por profesional mostrando 7 columnas (lunes a domingo) correspondientes a la semana del `date` de anclaje.
- Conectar la alternancia día/semana en `AgendaToolbar` preservando `date`, `professionalId` y `chairId`.
- Implementar preselección automática de profesional si no se especifica en la URL (odontólogo a su propio ID; recepción/administrador al primer profesional activo en orden alfabético).
- Proveer navegación semanal con etiquetas explícitas ("Semana anterior", "Semana siguiente") que operen con saltos de `+/- 7` días calendarios.
- Marcar la cabecera del día actual con texto visible "Hoy" y el atributo `aria-current="date"`.
- Manejar el estado vacío semanal mostrando la grilla con horarios/bloqueos y el aviso "No hay turnos esta semana para [profesional]".
- Asegurar comportamiento responsive en tablet (768 px) con scroll horizontal y formato compacto en dos líneas (< 260 px).

**Non-Goals:**
- Modificar el backend o endpoints de la API (`GET /api/agenda` ya cubre rangos de hasta 31 días).
- Implementar operaciones de creación, edición o reprogramación de turnos (C-29 y C-30).
- Vista por sillón con columnas por sillón (C-31).
- Agregar librerías externas o dependencias npm.

## Decisions

### D1 — Representación de la semana en la URL y días de la semana
- **Decisión**: Mantener `date=AAAA-MM-DD` como fecha de anclaje y agregar `view=week`. La semana se calcula canónicamente de lunes (1) a domingo (7) usando `weekdayOf` y `addDays` existentes en `agendaTime.ts`:
  `monday = addDays(date, 1 - weekdayOf(date))` y `sunday = addDays(monday, 6)`.
- **Alternativas consideradas**:
  - Parámetros `from` y `to` explícitos en la URL: descartado porque obligaría a reescribir o borrar parámetros al alternar con la vista diaria.
  - Inicio de semana en domingo: descartado por ser contrario a la norma ISO-8601 y a la convención del dominio en `knowledge-base/05_reglas_de_negocio.md` (`WorkingHours`).
- **Comportamiento ante error**: Un valor de `view` desconocido o ausente cae de forma transparente a la vista diaria (`view=day`).

### D2 — Control de alternancia día/semana y navegación
- **Decisión**: Agregar en `AgendaToolbar` un selector segmentado `[ Día | Semana ]`. Al pulsar "Semana" o "Día", se navega con `setSearchParams` actualizando `view` y conservando intactos `date`, `professionalId` y `chairId`.
- En vista semanal, los botones de navegación anterior y siguiente adoptan el texto visible y accesible "Semana anterior" y "Semana siguiente", sumando o restando 7 días mediante `addDays(date, -7)` y `addDays(date, 7)`.
- **Alternativas consideradas**:
  - Rutas separadas `/agenda` y `/agenda/semanal`: descartado porque divide innecesariamente componentes y rompe el patrón REST/SPA del frontend.

### D3 — Layout semanal y preselección de profesional
- **Decisión**: La vista semanal despliega 7 columnas (lunes a domingo) para **un** profesional seleccionado (US-040 CA-2). Si no hay `professionalId` en la URL:
  - Rol `odontologo`: se toma automáticamente el `professionalId` del usuario autenticado en la sesión.
  - Roles `recepcion` y `administrador`: se selecciona el primer profesional activo en orden alfabético utilizando la función existente `compareProfessionals`.
  - El selector en `AgendaToolbar` permanece siempre habilitado para todos los roles (la autorización `READ_AGENDA` no restringe lectura entre profesionales).
- En escritorio (1440 px), las 7 columnas se renderizan simultáneamente. En tablet (768 px), se utiliza el contenedor con scroll horizontal (`overflow-x: auto`) con canal de horas y cabeceras fijas (`position: sticky`), y las tarjetas activan el formato en 2 líneas (`HH:MM · Paciente` + `StatusBadge`) mediante container query (< 260 px).

### D4 — Reutilización de arquitectura de C-27 y abstracción de columnas
- **Decisión**: Generalizar el modelo de columna en `agendaLayout.ts` mediante la función `groupByDayForProfessional`:
  - Entrada: `date` (lunes), `timezone`, `workingHours`, `blocks`, `appointments` y el profesional seleccionado.
  - Salida: 7 columnas donde cada columna representa un día calendario de la semana con sus respectivos turnos, horarios correspondientes a ese día de la semana y bloqueos activos.
  - Ambas vistas (diaria y semanal) comparten `assignLanes` para la asignación de carriles superpuestos y `computeAxis` para calcular el eje temporal unificado.
  - El hook `useAgenda` se amplía de manera retrocompatible: si se especifica `from` y `to` (o `viewMode === "week"`), solicita el rango semanal completo; en caso contrario, mantiene la solicitud diaria `from: date, to: date`.
- **Condición dura**: Los 127 tests existentes de C-27 deben seguir pasando sin modificaciones.

### D5 — Casos borde de tiempo, cancelados y marca "Hoy"
- **Navegación entre meses/años**: `addDays` opera con instantes normalizados a mediodía UTC, asegurando cálculos calendarios exactos que cruzan fin de mes (ej. 28 de diciembre a 4 de enero) y años bisiestos.
- **Turnos cancelados**: Se renderizan en la columna del día correspondiente, atenuados (`styles.appointmentCancelled`) y con la etiqueta de texto visible "Cancelado" (accesibilidad AA).
- **Días sin horarios (ej. domingos)**: Se dibujan con el fondo de horario no laboral (`--agenda-offhours-bg`); si contienen turnos o bloqueos se renderizan sin impedimentos; si no hay turnos, exponen la leyenda "Sin turnos".
- **Identificador de día actual**: Si la fecha de hoy según el `Clock` inyectado pertenece a la semana en pantalla, la cabecera de la columna correspondiente incluye el texto visible "Hoy" y el atributo semántico `aria-current="date"`, cumpliendo la regla de no depender únicamente del color.

### D6 — Estados de carga, vacío y errores
- **Carga**: `LoadingState` inicial; indicador no intrusivo (`aria-busy="true"`, "Actualizando…") durante la navegación semanal.
- **Estado vacío**: En vista semanal, el profesional seleccionado **no** se considera un filtro que vacíe la pantalla. La grilla siempre se dibuja con sus horarios y bloqueos (relevante para consultar disponibilidad), mostrando arriba el aviso informativo "No hay turnos esta semana para [profesional]". Si además hay un filtro de sillón activo que elimina turnos, se muestra el aviso de filtro.
- **Errores y autenticación**: Errores 5xx/red con `ErrorState` y reintento. El error 401 se delega a `TokenStore` (limpieza de sesión y redirección al login); el error 403 muestra las violaciones de la API sin cerrar sesión.

## Skill y MCP

Este diseño fue elaborado siguiendo estrictamente la skill del proyecto y las evidencias del MCP Context7:
- **Skill `appointment-frontend-ux`** (documentada en `docs/evidencias/explore-C-28.md`):
  - §Stack exacto: React Router DOM 6.30.6 (APIs v6, nunca v7).
  - §Tokens de diseño: uso exclusivo de variables de `tokens.css` y `APPOINTMENT_STATUS_TOKENS`.
  - §Accesibilidad: estado siempre con texto visible, marca "Hoy" visible más `aria-current="date"`, controles interactivos >= 44x44 px, `aria-label` descriptivos.
  - §Prioridad en tarjetas angostas: formato en dos líneas para columnas de menos de 260 px.
  - §Zona horaria: instantes UTC transformados con el `timezone` de la respuesta de la API.
  - §Token de sesión: sin acceso a storage desde componentes (delegado en `TokenStore`).
  - §Regla C1 de tests: sin `vi.mock`, `vi.spyOn` ni fake timers; inyección de `fetchFn`, `Clock` y `createMemoryRouter`.
  - §Verificación visual obligatoria: capturas en escritorio (1440 px) y tablet (768 px) antes de archivar.
- **MCP Context7** (documentado en `docs/skills-mcp/evidencias/04-uso-context7.md`):
  - Uso correcto del hook `useSearchParams` desde `"react-router-dom"`.
  - Actualización de parámetros con `setSearchParams` en modo objeto, preservando la estabilidad de referencias y la sincronización con el router.
  - Cero consultas pendientes: todas las APIs propuestas están verificadas en el código existente o en la evidencia 04.

## Risks / Trade-offs

- **[Riesgo: Regresión en tests existentes de C-27]** → *Mitigación*: La suite completa de 127 tests de C-27 se ejecuta como primer paso del safety net y no se modifica ningún archivo de test previo. Las nuevas capacidades de C-28 se integran de forma aditiva.
- **[Riesgo: Colapso de ancho de columnas en tablet al pasar a 7 días]** → *Mitigación*: Se fija un ancho mínimo por columna (`--agenda-column-min-width`) dentro de un contenedor con scroll horizontal y se activan container queries para la vista compacta en dos líneas.
- **[Riesgo: Ambigüedad cuando no hay profesional en la URL]** → *Mitigación*: Preselección determinista basada en el rol del usuario (propio para odontólogo, primer activo alfabético para recepción/administrador).
