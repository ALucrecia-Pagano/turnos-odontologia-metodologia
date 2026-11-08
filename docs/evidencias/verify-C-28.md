# Verificación de C-28 — ui-agenda-semanal

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 22/23 en [tasks.md](../../openspec/changes/ui-agenda-semanal/tasks.md) (tarea 5.3 de capturas manuales pendiente para la autora).
- Vitest: 35 archivos, 142 tests en verde (127 preexistentes de C-27 + 15 nuevos de C-28); `tsc` y ESLint sin errores ni warnings.
- Mutaciones: 15/15 hicieron fallar su test (una por cada test nuevo de C-28); mutaciones inválidas: 0; SHA-256 de producción intacto.
- Trazabilidad: 15 escenarios, 0 problemas.
- Línea de base desde `frontend/`: [baseline-C-28.txt](baseline-C-28.txt) (127 passed, 35 archivos).
- `tsc --noEmit` (strict): [tsc-C-28.txt](tsc-C-28.txt).
- ESLint (`--max-warnings 0`): [eslint-C-28.txt](eslint-C-28.txt).
- Vitest: [vitest-C-28.txt](vitest-C-28.txt).
- Mutaciones: [mutaciones-C-28.txt](mutaciones-C-28.txt), generado por [mutaciones-C-28.py](mutaciones-C-28.py).
- Trazabilidad: [trazabilidad-C-28.txt](trazabilidad-C-28.txt), generado por [trazabilidad-C-28.py](trazabilidad-C-28.py).
- Validación OpenSpec y `git diff --check`: [validate-C-28.txt](validate-C-28.txt).
- Rojos (TDD): carpeta [red-C-28/](red-C-28/).

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

Ninguno.

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
<!-- trazabilidad:fin -->
