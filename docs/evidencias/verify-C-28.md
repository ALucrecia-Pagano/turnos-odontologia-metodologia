# Verificación de C-28 — ui-agenda-semanal

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 22/23 en [tasks.md](../../openspec/changes/ui-agenda-semanal/tasks.md) (tarea 5.3 de capturas manuales pendiente para la autora).
- Vitest: 35 archivos, 148 tests en verde (127 preexistentes de C-27 + 21 nuevos de C-28); `tsc` y ESLint sin errores ni warnings.
- Mutaciones: 21/21 hicieron fallar su test (una por cada test nuevo de C-28); mutaciones inválidas: 0; SHA-256 de producción intacto.
- Trazabilidad: 19 escenarios, 0 problemas.
- Línea de base desde `frontend/`: [baseline-C-28.txt](baseline-C-28.txt) (127 passed, 35 archivos).
- `tsc --noEmit` (strict): [tsc-C-28.txt](tsc-C-28.txt).
- ESLint (`--max-warnings 0`): [eslint-C-28.txt](eslint-C-28.txt).
- Vitest: [vitest-C-28.txt](vitest-C-28.txt).
- Mutaciones: [mutaciones-C-28.txt](mutaciones-C-28.txt), generado por [mutaciones-C-28.py](mutaciones-C-28.py).
- Trazabilidad: [trazabilidad-C-28.txt](trazabilidad-C-28.txt), generado por [trazabilidad-C-28.py](trazabilidad-C-28.py).
- Validación OpenSpec y `git diff --check`: [validate-C-28.txt](validate-C-28.txt).
- Rojos (TDD): carpeta [red-C-28/](red-C-28/), incluyendo [revision-visual.txt](red-C-28/revision-visual.txt) y [revision-visual-2.txt](red-C-28/revision-visual-2.txt).

## Hallazgos de la revisión visual

Tras la inspección en pantalla con datos reales en escritorio (1440 px) y tablet (768 px), se identificaron hallazgos que no habían sido advertidos por la suite inicial de tests:

1. **H1 — Preselección automática sin professionalId en la llamada a la API**:
   - *Hallazgo*: Al ingresar a la vista semanal sin `professionalId` en la URL, la llamada a `GET /api/agenda` se ejecutaba sin `professionalId`. Aunque la grilla semanal filtraba al profesional preseleccionado, el contador anunciaba turnos de todos los profesionales y la vista de lista mezclaba turnos de otros profesionales.
   - *Causa*: Los tests iniciales pasaban `professionalId` explícito en los parámetros o la URL. Además, en `AgendaPage.tsx` y `useAgenda.ts` las solicitudes se disparaban antes de que el catálogo de profesionales estuviera cargado, enviando `professionalId: null`.
   - *Arreglo*: Se refactorizó `useAgenda.ts` para que, en vista semanal sin `professionalId`, cargue primero los catálogos (`fetchProfessionals`), preseleccione al primer profesional activo (`sorted[0].id` según `compareProfessionals`) y recién entonces dispare la única llamada a `fetchAgenda` enviando dicho `professionalId`. El contador y la vista de lista filtran exclusivamente los turnos del profesional.

2. **H2 — Textos y encabezados en vista semanal**:
   - *Hallazgo*: En vista semanal, el encabezado mostraba un día único ("miércoles 18 de noviembre de 2026"), el contador decía "Turnos del miércoles 18...: N" y el título de la página mostraba "Agenda diaria".
   - *Causa*: Los componentes reutilizaban directamente `dayLabel` y `PageShell title="Agenda diaria"` sin alternancia condicional según `view`.
   - *Arreglo*: Se implementó la función pura `formatWeekLabel` en `agendaTime.ts`, soportando rango semanal dentro del mismo mes ("Semana del 16 al 22 de noviembre de 2026"), con cruce de mes ("Semana del 30 de noviembre al 6 de diciembre de 2026") y con cruce de año ("Semana del 28 de diciembre de 2026 al 3 de enero de 2027"). Se actualizó el título de `PageShell` a "Agenda semanal" y el contador a "Turnos de la semana: N".

3. **H3 — "Ver como lista" en vista semanal**:
   - *Hallazgo*: Al alternar a lista en vista semanal, el caption decía "Turnos del [día]", no existía columna de fecha para saber a qué día correspondía cada turno y los turnos aparecían sin orden cronológico de la semana.
   - *Causa*: `AgendaTable.tsx` estaba diseñado únicamente para la vista diaria, asumiendo que todos los turnos pertenecían a una misma fecha.
   - *Arreglo*: Se extendió `AgendaTable.tsx` para aceptar `view="week"`, mostrando el caption con el rango semanal, incorporando la columna "Fecha" con formato abreviado (ej. "lun 16/11") y ordenando los turnos cronológicamente por fecha y hora de inicio.

4. **H4 — Ancho de columnas en escritorio y scroll en tablet**:
   - *Hallazgo*: A 1440 px solo se visualizaban de lunes a viernes, quedando sábado y domingo ocultos tras un scroll horizontal innecesario y cortando la tarjeta del viernes. Si hoy caía en fin de semana, la marca "Hoy" no se visualizaba.
   - *Causa*: `jsdom` no calcula medidas de layout ni renderiza anchos reales, por lo que los tests de componentes no detectaron que `min-width: 220px` por 7 columnas requería más de 1540 px de espacio.
   - *Arreglo*: Se creó el token semántico `--agenda-week-column-min-width: 140px;` en `tokens.css`. Se añadieron las clases `.weekColumnHeader` y `.weekColumnTrack` en `AgendaGrid.module.css` con `flex: 1 1 var(--agenda-week-column-min-width, 140px); min-width: var(--agenda-week-column-min-width, 140px);` sin el límite de 220 px de la vista diaria. Con esto, en pantallas de escritorio (≥ 1280 px) las 7 columnas se muestran visibles simultáneamente sin scroll, mientras que en tablet (< 1044 px / 768 px) se preserva el scroll horizontal con columna de horas sticky y las tarjetas adaptadas en dos líneas mediante la container query existente.

5. **H5 — Desborde de la etiqueta de estado en carriles divididos (~70 px)**:
   - *Hallazgo*: En carriles divididos (~70 px de ancho) de la vista semanal, la etiqueta de estado de los turnos cancelados ("Cancelado") desbordaba el borde lateral de la tarjeta.
   - *Causa*: La etiqueta de estado en `.cardCompactStacked .statusBadgeWrap > span` no tenía acotado su ancho máximo ni recorte de desborde.
   - *Arreglo*: Se añadieron `max-width: 100%; overflow: hidden; text-overflow: ellipsis; box-sizing: border-box;` a `.cardCompactStacked .statusBadgeWrap > span` y a `.appointmentSplit .cardTopRow > span:last-child, .appointmentSplit .statusBadgeWrap > span` en `AgendaGrid.module.css`.

6. **H6 — Tamaño de etiqueta y recorte de líneas en tarjetas no compactas dentro de columnas angostas (< 260 px)**:
   - *Hallazgo*: En tarjetas no compactas (45 y 60 min) en columnas de menos de 260 px (~145 px en vista semanal), la etiqueta de estado quedaba en tamaño normal en su propio renglón y empujaba la línea de prestación fuera de la tarjeta, cortándola verticalmente a mitad de las letras.
   - *Causa*: La container query `@container agenda-column (width < 260px)` solo contemplaba las tarjetas compactas (< 45 min), sin reducir la etiqueta ni fijar el alto de línea en las tarjetas de 45–60 min.
   - *Arreglo*: Dentro de la container query `@container agenda-column (width < 260px)` en `AgendaGrid.module.css`, se configuró `.cardTopRow > span:last-child` para usar el tamaño reducido (`font-size: var(--font-size-xs); padding: 1px var(--space-1); max-width: 100%; overflow: hidden; text-overflow: ellipsis;`), y se estableció `line-height: 1.2` con `white-space: nowrap` y `text-overflow: ellipsis` en `.cardPatient` y `.cardMeta`. Con ello, las tarjetas no compactas conservan espacio para todas las líneas y recortan horizontalmente con puntos suspensivos en un solo renglón sin cortarse verticalmente.

## Regla C1 y diseño accesible (D1 a D6)

- **Sin mocks ni reemplazos globales (Regla C1)**: todo el código de test usa funciones `fetch` inyectadas que devuelven instancias reales de `Response` y `createApiClient({ fetchFn })`. Prohibidos `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` y MSW. El tiempo se fija exclusivamente inyectando la interfaz `Clock { now(): Date }`.
- **Una sola llamada para la semana**: `useAgenda` y `fetchAgenda` admiten `toDate`, solicitando la semana completa de lunes a domingo en una única llamada a `GET /api/agenda?from=...&to=...&professionalId=...`.
- **Zona horaria explícita desde la respuesta**: todas las fechas y horas se formatean en base al `timezone` de la respuesta, colocando turnos en su día local correspondiente (e.g. `2026-11-17T01:30:00Z` en Buenos Aires es lunes `2026-11-16` a las 22:30).
- **Accesibilidad y tokens**: "Hoy" se resalta con texto visible y atributo semántico `aria-current="date"`, nunca únicamente con color. Los turnos cancelados muestran el texto visible "Cancelado". Los botones de navegación dicen explícitamente "Semana anterior" y "Semana siguiente" con texto visible y accesible.
- **Preselección por rol sin professionalId**: para rol `odontologo` se selecciona automáticamente su propio `professionalId`; para `recepcion` y `administrador`, el primer profesional activo según `compareProfessionals` ("Dr. Martín Sosa"), manteniendo el selector habilitado para alternar.

## Capturas planificadas (5.3)

La tarea 5.3 se deja desmarcada en `tasks.md` para que la autora tome las capturas correspondientes en el navegador:
- `docs/evidencias/capturas/C-28-semana-desktop.png`: vista semanal completa de 7 columnas en escritorio (1440 px).
- `docs/evidencias/capturas/C-28-semana-tablet.png`: vista semanal en tablet (768 px) con scroll horizontal, horas sticky y tarjetas compactas.
- `docs/evidencias/capturas/C-28-semana-vacia.png`: semana vacía con aviso informativo y grilla visible.
- `docs/evidencias/capturas/C-28-filtro-sillon.png`: semana vacía con filtro de sillón activo y aviso de filtro.

## Inmutabilidad fuera de frontend/

Se confirma expresamente que:
- No se modificó ningún archivo dentro de `backend/`.
- No se modificó `docker-compose.yml`.
- No se modificó `.env` ni se incluyeron secretos en ningún archivo.
- No se modificaron `openspec/specs/`, `knowledge-base/`, `CHANGES.md`, `README.md`, `AGENTS.md` ni `CLAUDE.md`.
- No se modificaron evidencias archivadas preexistentes de otros changes.
- Los 127 tests originales de C-27 permanecen 100% inalterados y pasando.

## Desvíos

- **Limitación de legibilidad del nombre del paciente en carriles divididos (~70 px)**: en carriles divididos dentro de la vista semanal (~70 px de ancho), el nombre del paciente no entra en su totalidad en la tarjeta gráfica y se trunca tempranamente con ellipsis debido a la extrema estrechez del carril disponible. Esta limitación se acepta como desvío visual documentado, dado que el nombre y los datos completos del turno están garantizados tanto en el `aria-label` accesible de la tarjeta como en la vista de lista ("Ver como lista").

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `weekRangeOf calcula lunes a domingo de la semana y getWeekDates genera los 7 días admitiendo cruce de mes y año` | `frontend/src/features/agenda/agendaTime.ts` | `-  const sunday = addDays(monday, 6); +  const sunday = addDays(monday, 5);` | `AssertionError: expected { monday: '2026-11-16', …(1) } to deeply equal { monday: '2026-11` |
| 2 | `groupByDayForProfessional genera 7 columnas de lunes a domingo para un profesional, distribuye turnos, horarios y bloqueos en hora local y marca isToday` | `frontend/src/features/agenda/agendaLayout.ts` | `-    const weekday = i + 1; +    const weekday = i + 2;` | `AssertionError: expected [ 2, 3, 4, 5, 6, 7, 8 ] to deeply equal [ 1, 2, 3, 4, 5, 6, 7 ]` |
| 3 | `pide la semana completa en una sola llamada a GET /api/agenda cuando se especifica toDate` | `frontend/src/features/agenda/useAgenda.ts` | `-  const effectiveTo = toDate ?? date; +  const effectiveTo = date;` | `AssertionError: expected '/api/agenda?from=2026-11-16&to=2026-1…' to contain 'to=2026-11-2` |
| 4 | `renderiza el selector de vista [ Día \| Semana ], dispara onSelectView y adapta los botones de navegación a Semana anterior y Semana siguiente` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-  const prevLabel = isWeekView ? "Semana anterior" : "Anterior"; +  const prevLabel = isW` | `AssertionError: expected null not to be null` |
| 5 | `verifica estáticamente los estilos de tablet y el tag de Hoy para la vista semanal (C-28)` | `frontend/src/features/agenda/AgendaGrid.module.css` | `-  border-radius: var(--radius-pill); +  border-radius: var(--radius-md);` | `AssertionError: expected '.gridScrollContainer {\n  overflow-x:…' to contain 'border-radiu` |
| 6 | `renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                aria-current={isToday ? "date" : undefined} +                aria-current` | `Error: expect(element).toHaveAttribute("aria-current", "date") // element.getAttribute("ar` |
| 7 | `muestra grilla y aviso informativo cuando la semana está vacía sin turnos para la profesional` | `frontend/src/features/agenda/AgendaView.tsx` | `-                : 'No hay turnos esta semana para ${professionalName}'} +                ` | `AssertionError: expected null not to be null` |
| 8 | `muestra grilla y aviso de filtro cuando la semana está vacía con filtro de sillón activo` | `frontend/src/features/agenda/AgendaView.tsx` | `-                ? "Sin turnos para este filtro" +                ? "Sin turnos"` | `AssertionError: expected null not to be null` |
| 9 | `alterna de día a semana conservando fecha y filtros` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-              onClick={() => onSelectView?.("week")} +              onClick={() => onSele` | `AssertionError: expected '?date=2026-11-18&professionalId=00000…' to contain 'view=week'` |
| 10 | `alterna de semana a día conservando el día exacto de anclaje y filtros` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    setSearchParams(buildParams({ view: nextView }), { replace: false }); +    void nextV` | `AssertionError: expected '?date=2026-11-18&view=week&profession…' not to contain 'view=wee` |
| 11 | `un view desconocido o ausente cae a vista diaria con botón Día seleccionado` | `frontend/src/features/agenda/AgendaPage.tsx` | `-  const view: "day" \| "week" = rawView === "week" ? "week" : "day"; +  const view: "day" ` | `Error: expect(element).toHaveAttribute("aria-pressed", "true") // element.getAttribute("ar` |
| 12 | `preselecciona automáticamente por rol odontólogo su propio professionalId` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    (isWeek && user?.role === "odontologo" ? user.professionalId : null); +    (isWeek &&` | `AssertionError: expected null not to be null` |
| 13 | `preselecciona automáticamente por rol recepción al primer profesional activo en el orden del selector` | `frontend/src/features/agenda/AgendaPage.tsx` | `-      const first = sorted[0]; +      const first = sorted[1];` | `AssertionError: expected '00000000-0000-0000-0000-000000000001' to be '00000000-0000-0000-` |
| 14 | `navegación semanal avanza y retrocede 7 días cruzando mes y año` | `frontend/src/features/agenda/AgendaPage.tsx` | `-        onPrevDay={() => navigateToDate(addDays(effectiveDate, isWeek ? -7 : -1))} -     ` | `AssertionError: expected '?date=2026-12-29&view=week&profession…' to contain 'date=2027-01` |
| 15 | `botón Hoy en vista semanal navega a la fecha actual del Clock` | `frontend/src/features/agenda/AgendaPage.tsx` | `-        onToday={() => navigateToDate(todayInTimeZone(clock.now(), state.timezone))} +   ` | `AssertionError: expected '?date=2026-11-19&view=week' to contain 'date=2026-11-18'` |
| 16 | `preselección automática en vista semanal envía professionalId en la única llamada y el contador solo incluye sus turnos` | `frontend/src/features/agenda/useAgenda.ts` | `-    const needsPreselectedProfessional = -      isWeekly && (professionalId === null \|\| p` | `AssertionError: expected 'http://localhost:8000/api/agenda?from…' to contain 'professional` |
| 17 | `vista semanal muestra Agenda semanal como título, rango de semana en encabezado y Turnos de la semana en contador` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    <PageShell title={isWeek ? "Agenda semanal" : "Agenda diaria"}> +    <PageShell title` | `AssertionError: expected null not to be null` |
| 18 | `ver como lista en vista semanal incluye caption de semana, columna Fecha y orden cronológico` | `frontend/src/features/agenda/AgendaTable.tsx` | `-  const isWeek = view === "week"; +  const isWeek = false;` | `AssertionError: expected null not to be null` |
| 19 | `las columnas semanales usan token de ancho sin min-width de 220px y en tablet mantienen scroll horizontal` | `frontend/src/shared/styles/tokens.css` | `-  --agenda-week-column-min-width: 140px; +  --agenda-week-min-width: 140px;` | `AssertionError: expected ':root {\n  /* Espaciado */\n  --space…' to contain '--agenda-wee` |
| 20 | `en carriles divididos y tarjetas apiladas la etiqueta de estado no desborda la tarjeta con max-width 100%, overflow hidden y text-overflow ellipsis (H5)` | `frontend/src/features/agenda/AgendaGrid.module.css` | `-  max-width: 100%; +  max-width: 200%;` | `AssertionError: expected '\n  font-size: var(--font-size-xs);\n…' to contain 'max-width: 1` |
| 21 | `en columnas menores a 260 px las tarjetas no compactas usan etiqueta reducida y líneas con ellipsis en una línea (H6)` | `frontend/src/features/agenda/AgendaGrid.module.css` | `-    font-size: var(--font-size-xs); +    font-size: var(--font-size-sm);` | `AssertionError: expected '@container agenda-column (width < 260…' to match /\.cardTopRow >` |
<!-- mutaciones:fin -->

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Requisito | Escenario | Test |
|---|---|---|---|
| 1 | Alternancia entre vista diaria y semanal | Alternancia de día a semana conservando fecha y filtros | `src/features/agenda/AgendaPage.test.tsx > alterna de día a semana conservando fecha y filtros` |
| 2 | Alternancia entre vista diaria y semanal | Alternancia de semana a día conservando el día exacto | `src/features/agenda/AgendaPage.test.tsx > alterna de semana a día conservando el día exacto de anclaje y filtros` |
| 3 | Alternancia entre vista diaria y semanal | Un view desconocido o ausente cae a vista diaria | `src/features/agenda/AgendaPage.test.tsx > un view desconocido o ausente cae a vista diaria con botón Día seleccionado` |
| 4 | Vista semanal por profesional y grilla de siete días | Grilla de siete días de lunes a domingo | `src/features/agenda/AgendaView.test.tsx > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles` |
| 5 | Vista semanal por profesional y grilla de siete días | La semana se pide en una sola llamada | `src/features/agenda/useAgenda.test.tsx > pide la semana completa en una sola llamada a GET /api/agenda cuando se especifica toDate` |
| 6 | Vista semanal por profesional y grilla de siete días | Turno en el día local correcto según timezone | `src/features/agenda/agendaLayout.test.ts > groupByDayForProfessional genera 7 columnas de lunes a domingo para un profesional, distribuye turnos, horarios y bloqueos en hora local y marca isToday` |
| 7 | Vista semanal por profesional y grilla de siete días | Preselección por rol odontólogo | `src/features/agenda/AgendaPage.test.tsx > preselecciona automáticamente por rol odontólogo su propio professionalId` |
| 8 | Vista semanal por profesional y grilla de siete días | Preselección por rol recepción o administrador | `src/features/agenda/AgendaPage.test.tsx > preselecciona automáticamente por rol recepción al primer profesional activo en el orden del selector` |
| 9 | Vista semanal por profesional y grilla de siete días | Turno cancelado visible con texto en vista semanal | `src/features/agenda/AgendaView.test.tsx > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles` |
| 10 | Navegación semanal | Navegación semanal que cruza mes y año | `src/features/agenda/AgendaPage.test.tsx > navegación semanal avanza y retrocede 7 días cruzando mes y año` |
| 11 | Navegación semanal | Botón Hoy en vista semanal | `src/features/agenda/AgendaPage.test.tsx > botón Hoy en vista semanal navega a la fecha actual del Clock` |
| 12 | Indicador accesible de día actual | Marca Hoy con texto visible y aria-current | `src/features/agenda/AgendaView.test.tsx > renderiza 7 columnas de lunes a domingo con turno en el día local correcto según timezone y cancelados visibles` |
| 13 | Estado vacío y visualización en tablet para vista semanal | Semana vacía con grilla y aviso informativo | `src/features/agenda/AgendaView.test.tsx > muestra grilla y aviso informativo cuando la semana está vacía sin turnos para la profesional` |
| 14 | Estado vacío y visualización en tablet para vista semanal | Semana vacía con filtro de sillón | `src/features/agenda/AgendaView.test.tsx > muestra grilla y aviso de filtro cuando la semana está vacía con filtro de sillón activo` |
| 15 | Estado vacío y visualización en tablet para vista semanal | Tarjetas en dos líneas en tablet | `src/features/agenda/agendaStyles.test.ts > verifica estáticamente los estilos de tablet y el tag de Hoy para la vista semanal (C-28)` |
| 16 | Llamada semanal con profesional preseleccionado y alcance de turnos | Preselección automática envía professionalId en la única llamada semanal | `src/features/agenda/AgendaPage.test.tsx > preselección automática en vista semanal envía professionalId en la única llamada y el contador solo incluye sus turnos` |
| 17 | Encabezado, título y contador en vista semanal | Textos y encabezados en vista semanal con cruce de año | `src/features/agenda/AgendaPage.test.tsx > vista semanal muestra Agenda semanal como título, rango de semana en encabezado y Turnos de la semana en contador` |
| 18 | Vista de lista en modo semanal | Tabla de turnos semanal con columna de fecha y orden cronológico | `src/features/agenda/AgendaView.test.tsx > ver como lista en vista semanal incluye caption de semana, columna Fecha y orden cronológico` |
| 19 | Ancho de columnas semanales en escritorio y tablet | Columnas semanales visibles en escritorio y adaptables en tablet | `src/features/agenda/agendaStyles.test.ts > las columnas semanales usan token de ancho sin min-width de 220px y en tablet mantienen scroll horizontal` |
<!-- trazabilidad:fin -->
