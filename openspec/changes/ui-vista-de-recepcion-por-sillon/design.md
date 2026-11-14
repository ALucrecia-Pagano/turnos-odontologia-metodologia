# Design

## Context

Ver `proposal.md` para el motivo. Estado actual relevante, verificado en el código:

- `AgendaPage` es dueña del estado de URL (`date`, `view`, `professionalId`, `chairId`), de la carga con `useAgenda` y del diálogo de detalle (`frontend/src/features/agenda/AgendaPage.tsx:41-343`). Hoy `view` sólo admite `"day" | "week"` (`:50-52`).
- `AgendaView` decide eje y columnas (`computeAxis`/`computeWeekAxis`, `groupByProfessional`/`groupByDayForProfessional`) y renderiza `AgendaGrid` o `AgendaTable` (`AgendaView.tsx:44-188`).
- `AgendaGrid` recibe `columns` estructurales (`ProfessionalColumn`), dibuja cabeceras, gutter, bandas de horario, bloqueos y tarjetas accionables; las tarjetas ya abren el detalle de C-30 (`AgendaGrid.tsx:17-29`, `:85-257`).
- La API entrega `chairId`/`chairName` por turno (`agendaApi.ts:10-23`), el catálogo `GET /chairs` (`agendaApi.ts:303-323`) y `timezone` en `AgendaResponse` (`agendaApi.ts:40-47`). No existe horario de atención por sillón ni bloqueo por sillón ni endpoint de huecos: `workingHours` y `blocks` son por profesional (`backend/app/services/agenda.py:79-96`).
- C-36 (en curso) define el contenedor de grilla móvil. Este change lo consume, no lo redefine.

## Goals / Non-Goals

**Goals:**
- Leer la agenda del día por sillón para recepción y administración, con disponibilidad explícita derivada en el frontend.
- Extender la grilla y el toolbar de forma aditiva, sin romper día/semana ni sus tests.
- Mantener una sola llamada diaria a `GET /api/agenda`, el `Clock` inyectado y el `timezone` de la respuesta como fuentes de verdad.

**Non-Goals:**
- Horarios de atención o bloqueos por sillón (no existen en el modelo; exigirían dominio, migración y API).
- Contenedor móvil, scroll-snap o selector de sillón propios (contrato de C-36).
- Persistir la última vista, menú nuevo, ruta nueva o polling.
- Cambios de backend, seeds, `CHANGES.md`, `README.md`, `AGENTS.md` o `CLAUDE.md`.

## Contrato heredado de C-36

C-31 se aplica **después** de que C-36 esté archivado. Hereda y NO redefine:

1. El MISMO contenedor de grilla que usan día y semana, con scroll-snap y columna completa en celular (≤ 640 px).
2. La toolbar compacta con "Filtros (N)".

C-31 sólo le pasa al contenedor existente las columnas por sillón (1..N). No crea contenedor, scroll, selector móvil ni media query de celular propios. Si C-36 renombra clases o props del contenedor, el apply adapta el punto de montaje de `AgendaGrid`, no el contrato.

## Decisions

### D1 — Entrada por `view=chair` dentro de `/agenda`

Se extiende `view` a `"day" | "week" | "chair"` y se conserva la URL como única fuente de estado. Alternativa descartada: ruta `/agenda/por-sillon` (duplica carga, navegación y filtros) y filtro `chairId` sobre columnas de profesional (no cumple columnas por sillón).

`buildParams` escribe `view=chair` sólo en ese modo; `view=day` sigue sin parámetro. Al cambiar de modo se conservan `date`, `professionalId` y `chairId`.

### D2 — Sólo recepción y administración

`AgendaToolbar` renderiza el botón "Sillones" si `userRole` es `recepcion` o `administrador`. `AgendaPage` normaliza `view=chair` a Día (con `replace`) cuando el rol es `odontologo`, para que URL y vista no se contradigan. El backend sigue autorizando a los tres roles (`READ_AGENDA` y `CHAIR READ`: `backend/app/auth/permissions.py:49`, `:67`); el gating es sólo de UI.

### D3 — "Libre" y "Fuera de horario" con texto, umbral 15 min

Dentro de la unión de horarios del día, los huecos se rotulan "Libre HH:MM–HH:MM" con `aria-label` "Sillón N libre de HH:MM a HH:MM". Los tramos internos sin atención se rotulan "Fuera de horario HH:MM–HH:MM". Los huecos menores a 15 minutos (`AGENDA_MIN_APPOINTMENT_MINUTES`, `agendaLayout.ts:16`) no se rotulan. Ocupan `reservado`, `confirmado` y `atendido`; liberan `cancelado` y `ausente` (RN-AG-08). No se pintan bloqueos profesionales como indisponibilidad del sillón.

### D4 — Profesional visible en la tarjeta y clic al detalle

Se agrega `showProfessional` a `AgendaGrid` (default `false`). En modo sillón, la tarjeta no compacta muestra hora + estado, paciente y nombre del profesional (el servicio queda en el `aria-label` y en el detalle). La compacta usa siempre dos líneas: "HH:MM · Paciente" y "Profesional + badge", con ellipsis en el profesional y badge sin truncar. Sigue siendo `<button type="button">` con `onClick` al `AppointmentDetailDialog` de C-30 y foco visible.

### D5 — Mismo contenedor de C-36

Ver "Contrato heredado". C-31 no agrega contenedor ni comportamiento móvil.

### D6 — Eje = unión de horarios, hoy desde `Clock`, navegación ±1 día

`computeChairAxis` usa el mínimo inicio y el máximo fin de la unión de horarios del día (más los turnos existentes, por si quedaran fuera de horario), redondeados a la hora, **sin** el margen artificial de 1 h de `computeAxis`. Los huecos internos se rotulan "Fuera de horario". Sin horarios: aviso "No hay horarios de atención para este día", eje 08:00–20:00 y ningún "Libre" inventado. La fecha inicial es `todayInTimeZone(clock.now(), DEFAULT_AGENDA_TIMEZONE)` si falta `date`; `Anterior`/`Siguiente` restan/suman un día con `addDays`.

### D7 — Módulo puro nuevo + `AgendaView` extendido

`agendaChairLayout.ts` puro (sin React, sin I/O, sin reloj global) con `groupByChair`, `unionAttentionIntervals`, `computeChairFreeSlots` y `computeChairAxis`. `AgendaView` gana una rama `isChairView`; si crece demasiado en el apply, se extrae `ChairAgendaView` sin cambiar contrato. `AgendaGrid` sólo recibe columnas con `freeSlots` opcional y `showProfessional`.

### D8 — Catálogo de sillones + unión defensiva

Columnas = catálogo `GET /chairs` (`useAgenda` ya lo carga) unido con los `chairId`/`chairName` que aparezcan en turnos del día. Orden por nombre (`localeCompare` es, desempate por id). Inactivos se muestran "Sillón N (inactivo)". Si el catálogo falla, `CATALOG_FALLBACK_WARNING` ya avisa y los turnos igual se pintan. Con `chairId` en la URL queda una sola columna.

### D9 — Capas y estados

Bandas de atención y disponibilidad en `z-index: 0`, bloqueos en `1` (no existen en columnas de sillón) y tarjetas en `2`; el foco de tarjeta sube a `3`. Un cancelado puede quedar sobre una banda "Libre" y su texto "Cancelado" explica el estado. No se descuentan cancelados/ausentes del hueco.

### D10 — Filtros y ayuda adaptada

Ambos filtros siguen disponibles. `chairId` reduce columnas; `professionalId` filtra turnos y recalcula la unión de horarios (sirve para "¿qué sillón puede usar el Dr. X?"). En modo sillón no se muestra `CHAIR_FILTER_HELP_TEXT`; se muestra una leyenda nueva, por ejemplo: "Cada columna es un sillón; el filtro de sillón reduce las columnas y el de profesional recalcula los horarios."

### D11 — Lista disponible y vacío adaptado

"Ver como lista" sigue visible y `AgendaTable` ya tiene columna Sillón. Un día sin turnos **no** usa `EmptyState`: se mantiene la grilla con bandas "Libre" y un aviso informativo ("No hay turnos para este día; los sillones se muestran libres"). El único vacío real es "No hay sillones configurados" cuando el catálogo y los turnos no aportan ningún sillón.

### D12 — Cero backend, tests nuevos en archivos nuevos

Sin cambios en `backend/`. Tests nuevos, un escenario = un test = una mutación, con la Regla C1 (detalle abajo). No se tocan tests existentes.

## Funciones puras de `agendaChairLayout.ts`

Tipos de entrada: `Chair`, `AgendaAppointment`, `AgendaWorkingHours` y `timezone`/`date` de la respuesta. Se reutilizan `parseHHMM`, `formatMinutesToHHMM`, `appointmentRange`, `weekdayOf` de `agendaTime.ts` y las constantes de `agendaLayout.ts`.

- `unionAttentionIntervals({ workingHours, weekday, professionalId? })`: filtra horarios del día (y del profesional si hay filtro), parsea `HH:MM`, clampea a `[0,1440]`, ordena por inicio y fusiona tramos contiguos o superpuestos (`slot.start <= last.end`). Devuelve `MinuteRange[]` semiabiertos.
- `computeChairFreeSlots({ attention, appointments, date, timezone, minMinutes = AGENDA_MIN_APPOINTMENT_MINUTES })`: calcula ocupación con `appointmentRange` sólo para estados que ocupan (`reservado`, `confirmado`, `atendido`), clampea y resta de cada tramo de atención. Emite huecos `kind: "free"` con duración ≥ `minMinutes` y los gaps internos de la unión como `kind: "outside"`. Devuelve `ChairFreeSlot[]` ordenados.
- `computeChairAxis({ workingHours, weekday, appointments, date, timezone })`: arma rangos con atención + turnos, clampea, redondea inicio hacia abajo y fin hacia arriba a la hora, sin margen; si no hay rangos devuelve `08:00–20:00`; si el span es menor a `AGENDA_MIN_AXIS_MINUTES`, extiende el fin (sin inventar horas hacia atrás). Construye `hours` con `formatMinutesToHHMM`.
- `groupByChair({ chairs, appointments, workingHours, date, timezone, weekday, filterChairId?, filterProfessionalId? })`: construye el mapa catálogo + turnos (id, nombre, activo), ordena, filtra por `chairId`, y por cada sillón devuelve `ChairColumn` con: turnos del sillón (y del profesional si hay filtro) que caen en el día, `blocks: []` (los bloqueos son por profesional), `workingHours` sintéticos de la unión (para el fondo) y `freeSlots`. El `displayLabel` agrega "(inactivo)" cuando corresponde.

`ChairColumn` extiende estructuralmente `ProfessionalColumn<AgendaAppointment, AgendaWorkingHours, AgendaBlock>` y agrega `freeSlots`. Así `AgendaGrid` sigue recibiendo el mismo tipo de columnas.

## Cambios por archivo

- `agendaChairLayout.ts` (nuevo, puro): tipos y funciones de la sección anterior.
- `AgendaToolbar.tsx`:
  - `view?: "day" | "week" | "chair"`, `onSelectView?: (view: "day" | "week" | "chair") => void`.
  - `isChairView = view === "chair"`.
  - **Cambio obligatorio**: "Día" pasa de `aria-pressed={!isWeekView}` y `className={isWeekView ? ... : ...}` (`frontend/src/features/agenda/AgendaToolbar.tsx:115-116`; líneas actuales con C-36 en curso) a `view === "day"`, para que en `view=chair` "Día" no quede presionado.
  - Tercer botón "Sillones" dentro del mismo `div role="group" aria-label="Modo de vista"`, visible sólo si `userRole` es `recepcion`/`administrador`; `aria-pressed={isChairView}`.
  - `prevLabel`/`nextLabel` ya usan "Anterior"/"Siguiente" cuando no es semana; se mantiene.
  - Ayuda: `hasChairFilter && !isChairView` muestra `CHAIR_FILTER_HELP_TEXT`; en `isChairView` muestra `CHAIR_VIEW_HELP_TEXT` (constante exportada).
  - La toolbar compacta y "Filtros (N)" son de C-36; no se recrean.
- `AgendaView.tsx`: `view` incluye `"chair"`; `isChairView`; `aria-label` "Vista de agenda por sillón"; eje con `computeChairAxis`; columnas con `groupByChair`; contador `Turnos del <día>: N`; vacío propio; `showProfessional={isChairView}`. La lista sigue con `AgendaTable`.
- `AgendaGrid.tsx`: `showProfessional?: boolean` (default `false`); render de bandas de disponibilidad por columna detrás de las tarjetas, con texto y `aria-label`, usando `freeSlots`; tarjeta con profesional cuando `showProfessional`; `aria-label` existente intacto.
- `AgendaGrid.module.css`: clases `.availabilityBand`, `.availabilityFree`, `.availabilityOutside` (z-index 0, texto visible, tokens) y `.cardProfessional` / ajuste de la fila compacta; sin HEX.
- `AgendaPage.tsx`: `view` incluye `"chair"`; parseo de `view=chair` con gating de rol; normalización de URL; `handleSelectView`; `buildParams`; título "Agenda por sillón"; navegación ±1 día ya soportada.
- `AgendaTable.tsx`: `view` admite `"chair"` (se trata como día; la columna Sillón ya existe). Cambio sólo de tipo.
- `tokens.css`: tokens nuevos para las bandas de disponibilidad (por ejemplo `--agenda-free-bg`, `--agenda-free-border`, `--agenda-outside-bg`, `--agenda-outside-border`), sin HEX en TSX.

## URL y roles

- `view=chair` se escribe sólo cuando el modo está permitido. `odontologo` con `view=chair` cae a Día y la normalización de `AgendaPage` reescribe la URL sin `view` con `replace`.
- Un `view` desconocido sigue cayendo a Día (comportamiento actual).
- Alternar Día → Sillones → Semana conserva `date`, `professionalId` y `chairId`.
- `professionalId` inválido se sigue limpiando con `sanitizeUuidParam`; `chairId` inválido también.

## Zona horaria y `Clock`

- `date` es una fecha local `YYYY-MM-DD`; no se convierte a UTC.
- Las horas visibles y las posiciones usan `formatLocalTime`/`appointmentRange` con `agenda.timezone` de la respuesta.
- Los horarios de atención llegan como `HH:MM` local y se comparan con la unión y los turnos en minutos locales del día.
- La fecha inicial y "Hoy" usan `todayInTimeZone(clock.now(), timezone)`; los tests fijan el tiempo con `createFixedClock`.
- No se usa `new Date()` ni el reloj del navegador para decisiones de fecha.

## Seed y datos de prueba

`backend/app/demo_data.py:61-70`: Quiroga (`PROFESSIONALS[0]`) y Benítez (`PROFESSIONALS[2]`) lunes a viernes 09:00–13:00 y 15:00–19:00; Sosa (`PROFESSIONALS[1]`) sólo 09:00–13:00. El seed no crea turnos ni bloqueos. Los tests usan datos literales y pacientes ficticios; ningún escenario asume tarde para Sosa.

## Estrategia de tests (Regla C1)

Archivos nuevos, sin tocar los existentes:

- `agendaChairLayout.test.ts` (unidad): unión de horarios, huecos libres, huecos < 15 min, cancelado/ausente que liberan, gaps "Fuera de horario", eje con y sin horarios, unión defensiva de sillones, orden y filtros.
- `AgendaToolbar.chair.test.tsx`: botón visible para recepción/administrador, ausente para odontólogo, `aria-pressed` de Día en `view=chair`, ayuda adaptada.
- `AgendaView.chair.test.tsx`: columnas por sillón, profesional en tarjeta, clic al detalle, lista disponible, vacío adaptado, bandas "Libre"/"Fuera de horario".
- `AgendaPage.porSillon.test.tsx`: `view=chair` en URL, día por defecto desde `Clock`, una sola llamada `from=to`, navegación ±1 día, gating de rol, persistencia de filtros.
- `agendaChairStyles.test.ts` (estático): tokens requeridos, cero HEX en TSX, foco visible y que las bandas no dependan sólo del color.

Reglas obligatorias:

- Sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers, MSW ni `waitFor` largos.
- `fetch` con `createApiClient({ fetchFn })` (la firma es `createApiClient({ baseUrl, fetchFn })`, `frontend/src/shared/api/client.ts:119`).
- `Clock` con `createFixedClock` (`frontend/src/features/agenda/clock.ts:11-17`).
- Router con `createMemoryRouter` + `RouterProvider` (patrón de `frontend/src/features/agenda/AgendaPage.test.tsx:172-173`).
- Sin `@ts-ignore` ni `eslint-disable`.
- Un escenario = un test = una mutación; el detector de mutaciones inválidas y la trazabilidad fallan si dos escenarios comparten test.
- Colores sólo por tokens; foco visible; estado nunca sólo por color.
- Evidencias en UTF-8 generadas desde Git Bash.

## Plan de archivos

| Archivo | Acción |
|---|---|
| `frontend/src/features/agenda/agendaChairLayout.ts` | nuevo (puro) |
| `frontend/src/features/agenda/agendaChairLayout.test.ts` | nuevo |
| `frontend/src/features/agenda/AgendaToolbar.tsx` | modificar |
| `frontend/src/features/agenda/AgendaToolbar.chair.test.tsx` | nuevo |
| `frontend/src/features/agenda/AgendaView.tsx` | modificar |
| `frontend/src/features/agenda/AgendaView.chair.test.tsx` | nuevo |
| `frontend/src/features/agenda/AgendaGrid.tsx` | modificar |
| `frontend/src/features/agenda/AgendaGrid.module.css` | modificar |
| `frontend/src/features/agenda/AgendaPage.tsx` | modificar |
| `frontend/src/features/agenda/AgendaPage.porSillon.test.tsx` | nuevo |
| `frontend/src/features/agenda/AgendaTable.tsx` | modificar (tipo `view`) |
| `frontend/src/features/agenda/agendaChairStyles.test.ts` | nuevo |
| `frontend/src/shared/styles/tokens.css` | modificar (tokens) |

## Análisis obligatorio de `AgendaToolbar.test.tsx`

Verificado con `grep` en el árbol actual (C-36 en curso; si sus ediciones desplazan líneas, buscar el símbolo):

- `frontend/src/features/agenda/AgendaToolbar.test.tsx:129-134` consulta `screen.queryByRole("button", { name: "Día" })` y `"Semana"` y comprueba `aria-pressed`; **no** cuenta botones (`getAllByRole` no se usa). Un tercer botón no altera esas aserciones.
- El test de `:108-164` no pasa `userRole` (`:111-126`). Como el default es `userRole = null` (`frontend/src/features/agenda/AgendaToolbar.tsx:58`), el botón "Sillones" queda oculto y el DOM de ese test no cambia.
- El primer test (`:33-106`) espera el texto de ayuda del filtro de sillón sólo cuando `chairId` está seteado: ausente en `:69-73` y presente en `:93-97`. En día/semana ese comportamiento se mantiene porque la ayuda actual se conserva para `!isChairView`; el default `view="day"` y el rerender no cambian `view`.
- `frontend/src/features/agenda/AgendaToolbar.tsx:115-116` usa `aria-pressed={!isWeekView}` para "Día". En C-31 debe pasar a `view === "day"`; es cambio de código de producción en el apply, no de tests, y no afecta el test existente porque allí `view` es `"day"` o `"week"`.
- Si en el apply apareciera otra rotura por el tercer botón, la alternativa es renderizarlo como botón separado fuera del grupo `[Día | Semana]`; queda anotada como duda, sin tocar tests.

## Risks / Trade-offs

- [Unión de horarios no equivale a "horario del sillón"] → Documentado en D3/D6; si el negocio pide horarios o bloqueos por sillón, va en un change con backend.
- [Bloqueos profesionales no reservan el sillón] → No se pintan en columnas de sillón; es correcto para disponibilidad física.
- [Seed asimétrico: Sosa sólo mañana] → Tests con datos literales de `backend/app/demo_data.py:61-70`; nunca asumir 09–13/15–19 para los tres.
- [Desborde de la tarjeta compacta con profesional + estado] → Profesional con ellipsis, badge sin truncar, verificación con capturas a 768/390.
- [Tercer botón rompe el toolbar] → Análisis de arriba: no lo rompe; gating por rol y query por nombre.
- [C-36 cambia el contenedor antes del apply] → C-31 se monta sobre el contenedor vigente; no crea uno propio.
- [Verificación visual no automatizable] → Capturas 1440/768/390 antes de archivar.

## Open Questions

- Ninguna que cambie el alcance. La única duda de implementación es la ubicación exacta del tercer botón si C-36 reestructura la toolbar; se resuelve en el apply respetando el contrato (mismo grupo de Día/Semana) sin tocar tests.
