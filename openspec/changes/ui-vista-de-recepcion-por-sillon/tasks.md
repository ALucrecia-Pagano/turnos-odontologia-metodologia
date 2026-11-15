# Tasks

## Reglas de la aplicación (C-31)

- **Regla C1 de tests**: prohibido `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers, MSW y `waitFor` largos. `fetch` se inyecta con `createApiClient({ fetchFn })`; el tiempo con `createFixedClock`; el router con `createMemoryRouter` + `RouterProvider`.
- Sin `@ts-ignore` ni `eslint-disable`.
- Los tests existentes quedan **intactos**; todo test nuevo va en archivo nuevo.
- Un escenario = un test = una mutación. El detector de mutaciones inválidas debe marcar inválida cualquier mutación que no ponga el test en RED; la trazabilidad falla si dos escenarios comparten un mismo test.
- Colores sólo por tokens (`tokens.css`); foco visible; ningún estado se comunica sólo por color.
- Evidencias (tablas, capturas, salidas) en UTF-8 generadas desde Git Bash.
- Rama de trabajo: `c31-apply`, creada desde `main` con C-36 ya archivado.
- No se toca `backend/`, `openspec/specs/`, `CHANGES.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.env`, `.codex/` ni el change `ui-tema-oscuro-y-movil`.

## 1. Preflight y línea base

- [x] 1.1 Confirmar que C-36 (`ui-tema-oscuro-y-movil`) está archivado en `openspec/changes/archive/` y que `main` no tiene cambios sin commitear; verificar con `openspec list --json` y `git status`. Si C-36 no está archivado, detenerse y reportar.
- [x] 1.2 Crear la rama `c31-apply` desde `main` y verificar con `git branch --show-current`.
- [x] 1.3 Correr la línea base en `frontend/` con `npm run test:run`, `npm run typecheck` y `npm run lint`; registrar el número de tests que pasan y confirmar que no hay fallos preexistentes. Si hay fallos, detenerse y reportarlos sin corregirlos.
- [x] 1.4 Confirmar el contrato heredado de C-36 leyendo el contenedor de grilla vigente y la toolbar compacta; anotar en la evidencia qué clases/props se reutilizan y verificar que C-31 no crea contenedor, scroll ni selector móvil propios.

## 2. Módulo puro `agendaChairLayout.ts`

- [x] 2.1 RED: escribir `agendaChairLayout.test.ts` con los casos de unión de horarios (Quiroga/Benítez 09:00–13:00 y 15:00–19:00; Sosa sólo 09:00–13:00), ejecutar `npm run test:run -- agendaChairLayout` y confirmar que falla porque el módulo no existe.
- [x] 2.2 GREEN: crear `agendaChairLayout.ts` con `unionAttentionIntervals`, `computeChairFreeSlots`, `computeChairAxis` y los tipos `ChairFreeSlot`/`ChairColumn`; ejecutar el test y confirmar que pasa.
- [x] 2.3 RED: agregar casos de huecos libres entre turnos, huecos menores a 15 minutos, `cancelado`/`ausente` que liberan agenda y gaps internos "Fuera de horario"; confirmar RED con la implementación incompleta.
- [x] 2.4 GREEN: completar la resta de ocupación y los gaps; verificar que los casos nuevos y los anteriores pasan.
- [x] 2.5 RED: agregar casos de eje (unión 09:00–19:00; día sin horarios → 08:00–20:00) y verificar RED.
- [x] 2.6 GREEN: implementar `computeChairAxis` sin margen artificial y con fallback de 08:00–20:00; verificar GREEN.
- [x] 2.7 RED: agregar casos de `groupByChair` (unión defensiva catálogo + turnos, orden por nombre, "(inactivo)", filtro `chairId`, filtro `professionalId`, `blocks: []`) y verificar RED.
- [x] 2.8 GREEN: implementar `groupByChair`; verificar todos los tests del módulo y correr `npm run typecheck` sin errores.

## 3. Modo "Sillones" en la toolbar

- [x] 3.1 RED: crear `AgendaToolbar.chair.test.tsx` y verificar que falla: "Sillones" visible para `recepcion` y `administrador`, ausente para `odontologo`, y en `view=chair` el botón "Día" no está presionado (`aria-pressed="false"`, "Sillones" `true`).
- [x] 3.2 GREEN: extender `view` y `onSelectView` a `"chair"` en `AgendaToolbar.tsx`, agregar el tercer botón con gating de rol y cambiar "Día" a `view === "day"`; verificar el archivo nuevo y correr el test existente `AgendaToolbar.test.tsx` sin modificarlo.
- [x] 3.3 RED: agregar el caso de ayuda adaptada (sin `CHAIR_FILTER_HELP_TEXT` en `view=chair`, con `CHAIR_VIEW_HELP_TEXT`) y la conservación de "Anterior"/"Siguiente"; verificar RED.
- [x] 3.4 GREEN: implementar la ayuda adaptada y exportar `CHAIR_VIEW_HELP_TEXT`; verificar que el test nuevo y el existente pasan, y correr `npm run typecheck`.

## 4. Render de columnas por sillón reusando el contenedor de grilla

- [x] 4.1 RED: crear `AgendaView.chair.test.tsx` con un caso que verifica tres columnas ("Sillón 1", "Sillón 2", "Sillón 3"), dos turnos de profesionales distintos en la misma columna y el profesional visible en cada tarjeta; verificar RED.
- [x] 4.2 GREEN: extender `AgendaView` con `view="chair"`, `groupByChair`, `computeChairAxis`, título/aria-label y contador; verificar el test nuevo y que `AgendaView.test.tsx` y `AgendaPage.test.tsx` siguen pasando sin cambios.
- [x] 4.3 RED: agregar casos de sillón sin turnos ("Libre 09:00–13:00", "Libre 15:00–19:00", "Fuera de horario 13:00–15:00") y de hueco libre entre turnos con texto y `aria-label`; verificar RED.
- [x] 4.4 GREEN: extender `AgendaGrid` con `freeSlots` y las bandas de disponibilidad detrás de las tarjetas; agregar las clases y tokens en `AgendaGrid.module.css` y `tokens.css`; verificar GREEN y que no se modificó el comportamiento por defecto (`showProfessional` ausente).
- [x] 4.5 RED: agregar el caso de cancelado que no ocupa (tramo "Libre") y el caso de "Fuera de horario" en el eje; verificar RED.
- [x] 4.6 GREEN: ajustar el cálculo de huecos y el render de bandas; verificar GREEN.
- [x] 4.7 RED: agregar casos de filtros (`chairId` deja una columna; `professionalId` de Sosa recalcula a 09:00–13:00 y sin "Libre" de tarde) y de sillón inactivo; verificar RED.
- [x] 4.8 GREEN: cablear `filterChairId`/`filterProfessionalId` en `groupByChair`; verificar GREEN y correr `npm run typecheck`.
- [x] 4.9 RED: crear `AgendaPage.porSillon.test.tsx` con `view=chair`, día por defecto desde `Clock`, una única llamada `from=to=2026-11-16`, navegación ±1 día, gating de rol (odontólogo cae a Día y URL sin `view=chair`) y persistencia de `date`/filtros al alternar; verificar RED.
- [x] 4.10 GREEN: extender `AgendaPage` (`view`, parseo/gating, normalización, `buildParams`, título) y `AgendaTable` (tipo `view`); verificar el test nuevo y que `AgendaPage.test.tsx` sigue pasando sin cambios.

## 5. Integración con detalle, lista y estado vacío

- [x] 5.1 RED: agregar al test de `AgendaView.chair.test.tsx` el clic en la tarjeta que abre `AppointmentDetailDialog`, el nombre accesible completo y el formato compacto con profesional + estado; verificar RED donde corresponda.
- [x] 5.2 GREEN: cablear `onSelectAppointment` en la vista por sillón y el formato de tarjeta con `showProfessional`; verificar GREEN y que el detalle de C-30 se abre con el turno correcto.
- [x] 5.3 RED: agregar casos de "Ver como lista" con columna Sillón, día sin turnos con grilla y bandas "Libre" (aviso informativo, sin `EmptyState`) y catálogo vacío ("No hay sillones configurados"); verificar RED.
- [x] 5.4 GREEN: implementar el vacío adaptado y la lista en modo sillón; verificar GREEN y correr `npm run typecheck`.
- [x] 5.5 Crear `agendaChairStyles.test.ts` (RED/GREEN) para exigir los tokens nuevos, cero HEX en TSX, foco visible y que la disponibilidad no dependa sólo del color; ejecutar y verificar.
- [x] 5.6 RED/GREEN: verificar apilamiento de capas en modo sillón (`.availabilityBand` con z-index superior a `.workingHourBand` y menor a tarjeta y horas; omisión de `workingHourBand` en sillones).
- [x] 5.7 RED/GREEN: verificar distinción visual de disponibilidad libre con fondo de tinte claro (`--agenda-free-bg` a `var(--color-background)`) y borde discontinuo; cálculo de contraste WCAG AA documentado.

## 6. Verificación

- [x] 6.1 Correr `npm run test:run` completo en `frontend/` y confirmar que la línea base más los tests nuevos pasan, sin tests existentes modificados.
- [x] 6.2 Correr `npm run typecheck` y `npm run lint` (`--max-warnings 0`) y confirmar cero errores y cero warnings.
- [x] 6.3 Verificar la trazabilidad escenario → test → mutación: cada escenario del delta tiene un único test y cada mutación de la tabla final pone ese test en RED (detector de mutaciones inválidas sin casos aceptados por error).
- [x] 6.4 Verificar con `git diff --stat` que sólo se tocaron los archivos del plan y que no se modificaron tests existentes, `backend/`, `openspec/specs/`, `CHANGES.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.env` ni `.codex/`.
- [x] 6.5 Correr `openspec validate ui-vista-de-recepcion-por-sillon --strict` y confirmar que pasa.

## 7. Capturas (a cargo de Claude)

- [ ] 7.1 Levantar la app y tomar capturas de la vista por sillón a 1440, 768 y 390 px; guardarlas en `docs/evidencias/capturas/` en UTF-8 y verificar visualmente: tres columnas y gutter a 1440, toolbar envuelta y tres columnas a 768, columna completa con scroll-snap y tarjetas legibles a 390.
- [ ] 7.2 Registrar el resultado de la verificación visual en la evidencia del change (sin tocar `docs/evidencias/explore-C-31.md`).

## Workflow follow-up

- Sincronizar la spec al archivar (`openspec archive`) y marcar C-31 en `CHANGES.md` (fuera de este change).
- No commitear ni pushear sin pedido explícito de la autora.

## Escenario → test → mutación (pares RED/GREEN)

| Escenario | Test | Mutación que pone RED | GREEN esperado |
|---|---|---|---|
| Activar Sillones conserva fecha y filtros | `AgendaPage.porSillon.test.tsx` — "activar Sillones conserva fecha y filtros" | No escribir `view=chair` en `buildParams` | Revertir: URL con `view=chair` y filtros intactos → verde |
| Un view desconocido sigue cayendo a Día | `AgendaPage.porSillon.test.tsx` — "view desconocido cae a Día" | Tratar cualquier `view` distinto de `week` como `chair` | Revertir: `view=otro` → Día → verde |
| Turnos de distintos profesionales en la misma columna | `AgendaView.chair.test.tsx` — "dos profesionales en una columna de sillón" | Agrupar por profesional en vez de por sillón | Revertir: `groupByChair` → tres columnas y dos tarjetas en Sillón 1 → verde |
| Sillón sin turnos | `AgendaView.chair.test.tsx` — "sillón sin turnos muestra Libre y Fuera de horario" | Ocultar columnas sin turnos | Revertir: columna visible con bandas → verde |
| Filtro de un solo sillón | `AgendaPage.porSillon.test.tsx` — "chairId deja una sola columna" | Ignorar `chairId` en `groupByChair` | Revertir: sólo Sillón 2 → verde |
| Sillón inactivo visible | `agendaChairLayout.test.ts` — "sillón inactivo con sufijo (inactivo)" | No aplicar `formatProfessionalLabel`-like al sillón | Revertir: "Sillón 2 (inactivo)" → verde |
| Hueco libre entre dos turnos | `agendaChairLayout.test.ts` — "hueco 10:30–11:00 entre dos turnos" | No restar los turnos que ocupan | Revertir: bloque "Libre 10:30–11:00" → verde |
| Un cancelado no ocupa el sillón | `agendaChairLayout.test.ts` — "cancelado libera el tramo" | Incluir `cancelado` en los estados que ocupan | Revertir: "Libre 09:00–09:30" y tarjeta Cancelado → verde |
| La disponibilidad no depende sólo del color | `agendaChairStyles.test.ts` — "bandas con texto y sin HEX" | Quitar el texto visible de la banda | Revertir: banda con texto y aria → verde |
| Eje con la unión de horarios del día | `agendaChairLayout.test.ts` — "eje 09:00–19:00 y gap 13:00–15:00" | Usar sólo el horario de un profesional | Revertir: unión 09:00–19:00 → verde |
| Día sin horarios de atención | `agendaChairLayout.test.ts` — "sin horarios usa 08:00–20:00 sin Libre" | Emitir huecos libres con unión vacía | Revertir: fallback 08:00–20:00 y sin "Libre" → verde |
| Día por defecto desde el Clock | `AgendaPage.porSillon.test.tsx` — "view=chair sin date usa el Clock" | Usar `new Date()` en vez de `todayInTimeZone(clock.now())` | Revertir: `from=to=2026-11-16` → verde |
| Navegación de un día | `AgendaPage.porSillon.test.tsx` — "Siguiente suma un día en view=chair" | Sumar 7 días también en modo sillón | Revertir: 2026-11-17 → verde |
| Clic en la tarjeta abre el detalle | `AgendaView.chair.test.tsx` — "clic en tarjeta abre AppointmentDetailDialog" | No pasar `onSelectAppointment` a `AgendaGrid` en sillón | Revertir: se abre el detalle del turno → verde |
| Nombre accesible completo en la tarjeta | `AgendaView.chair.test.tsx` — "aria-label incluye hora, paciente, profesional, sillón, prestación y estado" | Quitar el profesional del `aria-label` | Revertir: aria completo → verde |
| Recepción y administración ven el control | `AgendaToolbar.chair.test.tsx` — "Sillones visible para recepcion y administrador" | Ocultar el botón para todos los roles | Revertir: botón visible en ambos roles → verde |
| Odontólogo sin acceso | `AgendaPage.porSillon.test.tsx` — "odontólogo con view=chair cae a Día" | No normalizar el rol en `AgendaPage` | Revertir: sin botón y URL sin `view=chair` → verde |
| El filtro de sillón reduce las columnas | `AgendaPage.porSillon.test.tsx` — "aplicar el filtro Sillón 2 actualiza la URL y reduce a una columna" | No actualizar `chairId` en la URL al aplicar el filtro | Revertir: URL con `chairId` y sólo Sillón 2 → verde |
| El filtro de profesional recalcula los horarios | `agendaChairLayout.test.ts` — "professionalId de Sosa deja unión 09:00–13:00" | No filtrar horarios por profesional | Revertir: unión 09:00–13:00 y sin Libre de tarde → verde |
| La ayuda del filtro de sillón se adapta | `AgendaToolbar.chair.test.tsx` — "en view=chair muestra CHAIR_VIEW_HELP_TEXT" | Seguir mostrando `CHAIR_FILTER_HELP_TEXT` | Revertir: leyenda adaptada → verde |
| La lista sigue disponible | `AgendaView.chair.test.tsx` — "Ver como lista con columna Sillón" | Ocultar el toggle en modo sillón | Revertir: tabla con columna Sillón → verde |
| Un día sin turnos conserva la grilla | `AgendaView.chair.test.tsx` — "día sin turnos mantiene grilla y aviso" | Reutilizar el `EmptyState` de día | Revertir: grilla con bandas y aviso → verde |
| Catálogo de sillones vacío | `AgendaView.chair.test.tsx` — "sin sillones muestra No hay sillones configurados" | Mostrar grilla vacía en vez del vacío | Revertir: EmptyState correcto → verde |
| Apilamiento de disponibilidad | `agendaChairStyles.test.ts` — "apilamiento de disponibilidad: z-index superior a workingHourBand y menor a tarjeta y horas" | Cambiar `z-index: 1` a `z-index: 0` en `.availabilityBand` | Revertir: z-index 1 > 0 y omisión de workingHourBand en sillones → verde |
| Distinción visual de disponibilidad | `agendaChairStyles.test.ts` — "distinción visual de disponibilidad: libre con fondo de tinte y borde discontinuo" | Cambiar borde `dashed` a `solid` en `.availabilityFree` | Revertir: borde dashed y fondo `--agenda-free-bg` → verde |
| Capturas a 1440, 768 y 390 px | — (verificación manual; no es test) | — (no aplica) | Capturas en `docs/evidencias/capturas/`; contenedor heredado y tarjetas legibles |

> La fila de capturas es verificación manual, no test ni mutación; se adjunta en `docs/evidencias/capturas/` antes de archivar.
