# Verificación de C-31 — ui-vista-de-recepcion-por-sillon

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 6 implementadas y verificadas según [tasks.md](../../openspec/changes/ui-vista-de-recepcion-por-sillon/tasks.md).
- **Vitest**: Suite final con todos los tests en verde ([test-suite-C-31.txt](test-suite-C-31.txt)). Los 23 tests nuevos se encuentran en 5 archivos aislados (`agendaChairLayout.test.ts`, `AgendaToolbar.chair.test.tsx`, `AgendaView.chair.test.tsx`, `AgendaPage.porSillon.test.tsx`, `agendaChairStyles.test.ts`); cada uno cuenta con su par RED/GREEN documentado.
- **Mutaciones**: 23 de 23 mutaciones eliminadas (M01–M23) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 sin cambios: sí** ([mutaciones-C-31.txt](mutaciones-C-31.txt), generado por [mutaciones-C-31.py](mutaciones-C-31.py)).
- **Trazabilidad**: **24 escenarios** declarados en specs delta (23 testeables 1:1 + 1 visual a cargo de Claude), 0 inconsistencias ([trazabilidad-C-31.txt](trazabilidad-C-31.txt), generado por [trazabilidad-C-31.py](trazabilidad-C-31.py)).
- **Calidad y Tooling**:
  - `npx tsc --noEmit` exit 0 (0 errores de tipos).
  - `npx eslint .` exit 0 (0 errores, 3 advertencias preexistentes heredadas de C-29/C-30 documentadas en Desvíos; ver [tooling-C-31.txt](tooling-C-31.txt)).
  - `npm run build` exit 0 ([build-C-31.txt](build-C-31.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 ([validate-C-31.txt](validate-C-31.txt)).
- **Tests existentes intocables**: `git diff main --diff-filter=M --stat -- "*.test.ts" "*.test.tsx"` devuelve vacío ([diff-tests-existentes-C-31.txt](diff-tests-existentes-C-31.txt)).
- **Skill y MCP**: Consulta documentada en [docs/skills-mcp/evidencias/C-31-skill-appointment-frontend-ux.md](../skills-mcp/evidencias/C-31-skill-appointment-frontend-ux.md). Aplicada la skill `appointment-frontend-ux`.

---

## Matriz Escenario → Test → Evidencias → Mutación

<!-- trazabilidad:inicio -->
| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |
|---|---|---|---|---|---|---|---|---|
| 01 | `frontend-agenda` | Activar Sillones conserva fecha y filtros | Testeable | `AgendaPage.porSillon.test.tsx` | `Activar Sillones conserva fecha y filtros` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M01` |
| 02 | `frontend-agenda` | Un view desconocido sigue cayendo a Día | Testeable | `AgendaPage.porSillon.test.tsx` | `Un view desconocido sigue cayendo a Día` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M02` |
| 03 | `frontend-agenda` | Turnos de distintos profesionales en la misma columna | Testeable | `AgendaView.chair.test.tsx` | `Turnos de distintos profesionales en la misma columna` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M03` |
| 04 | `frontend-agenda` | Sillón sin turnos | Testeable | `AgendaView.chair.test.tsx` | `Sillón sin turnos` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M04` |
| 05 | `frontend-agenda` | Filtro de un solo sillón | Testeable | `AgendaPage.porSillon.test.tsx` | `Filtro de un solo sillón` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M05` |
| 06 | `frontend-agenda` | Sillón inactivo visible | Testeable | `agendaChairLayout.test.ts` | `Sillón inactivo visible` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M06` |
| 07 | `frontend-agenda` | Hueco libre entre dos turnos | Testeable | `agendaChairLayout.test.ts` | `Hueco libre entre dos turnos` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M07` |
| 08 | `frontend-agenda` | Un cancelado no ocupa el sillón | Testeable | `agendaChairLayout.test.ts` | `Un cancelado no ocupa el sillón` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M08` |
| 09 | `frontend-agenda` | La disponibilidad no depende solo del color | Testeable | `agendaChairStyles.test.ts` | `La disponibilidad no depende sólo del color` | `05-agendaChairStyles-red.txt` | `05-agendaChairStyles-green.txt` | `M09` |
| 10 | `frontend-agenda` | Eje con la unión de horarios del día | Testeable | `agendaChairLayout.test.ts` | `Eje con la unión de horarios del día` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M10` |
| 11 | `frontend-agenda` | Día sin horarios de atención | Testeable | `agendaChairLayout.test.ts` | `Día sin horarios de atención` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M11` |
| 12 | `frontend-agenda` | Día por defecto desde el Clock | Testeable | `AgendaPage.porSillon.test.tsx` | `Día por defecto desde el Clock` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M12` |
| 13 | `frontend-agenda` | Navegación de un día | Testeable | `AgendaPage.porSillon.test.tsx` | `Navegación de un día` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M13` |
| 14 | `frontend-agenda` | Clic en la tarjeta abre el detalle | Testeable | `AgendaView.chair.test.tsx` | `Clic en la tarjeta abre el detalle` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M14` |
| 15 | `frontend-agenda` | Nombre accesible completo en la tarjeta | Testeable | `AgendaView.chair.test.tsx` | `Nombre accesible completo en la tarjeta` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M15` |
| 16 | `frontend-agenda` | Recepción y administración ven el control | Testeable | `AgendaToolbar.chair.test.tsx` | `Recepción y administración ven el control` | `02-agendaToolbarChair-red.txt` | `02-agendaToolbarChair-green.txt` | `M16` |
| 17 | `frontend-agenda` | Odontólogo sin acceso | Testeable | `AgendaPage.porSillon.test.tsx` | `Odontólogo sin acceso` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M17` |
| 18 | `frontend-agenda` | El filtro de sillón reduce las columnas | Testeable | `AgendaPage.porSillon.test.tsx` | `El filtro de sillón reduce las columnas` | `04-agendaPagePorSillon-red.txt` | `04-agendaPagePorSillon-green.txt` | `M18` |
| 19 | `frontend-agenda` | El filtro de profesional recalcula los horarios | Testeable | `agendaChairLayout.test.ts` | `El filtro de profesional recalcula los horarios` | `01-agendaChairLayout-red.txt` | `01-agendaChairLayout-green.txt` | `M19` |
| 20 | `frontend-agenda` | La ayuda del filtro de sillón se adapta | Testeable | `AgendaToolbar.chair.test.tsx` | `La ayuda del filtro de sillón se adapta` | `02-agendaToolbarChair-red.txt` | `02-agendaToolbarChair-green.txt` | `M20` |
| 21 | `frontend-agenda` | La lista sigue disponible | Testeable | `AgendaView.chair.test.tsx` | `La lista sigue disponible` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M21` |
| 22 | `frontend-agenda` | Un día sin turnos conserva la grilla | Testeable | `AgendaView.chair.test.tsx` | `Un día sin turnos conserva la grilla` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M22` |
| 23 | `frontend-agenda` | Catálogo de sillones vacío | Testeable | `AgendaView.chair.test.tsx` | `Catálogo de sillones vacío` | `03-agendaViewChair-red.txt` | `03-agendaViewChair-green.txt` | `M23` |
| V01 | `frontend-agenda` | Capturas a 1440, 768 y 390 px | Visual | — | — | — | — | — |
<!-- trazabilidad:fin -->

---

## Tabla de Mutaciones (M01–M23)

<!-- mutaciones:inicio -->
| ID | Archivo de test | Test | Estado | Mensaje de fallo |
|---|---|---|---|---|
| M01 | `AgendaPage.porSillon.test.tsx` | `Activar Sillones conserva fecha y filtros` | Matada | `AssertionError: expected '?date=2026-11-16&professionalId=00000…' to contain 'view=chair'` |
| M02 | `AgendaPage.porSillon.test.tsx` | `Un view desconocido sigue cayendo a Día` | Matada | `Error: expect(element).toHaveAttribute("aria-pressed", "true") // element.getAttribute("aria-pressed") === "true"` |
| M03 | `AgendaView.chair.test.tsx` | `Turnos de distintos profesionales en la misma columna` | Matada | `AssertionError: expected null not to be null` |
| M04 | `AgendaView.chair.test.tsx` | `Sillón sin turnos` | Matada | `AssertionError: expected null not to be null` |
| M05 | `AgendaPage.porSillon.test.tsx` | `Filtro de un solo sillón` | Matada | `AssertionError: expected [ <div …(2)>…(1)</div>, …(1) ] to have a length of 1 but got 2` |
| M06 | `agendaChairLayout.test.ts` | `Sillón inactivo visible` | Matada | `AssertionError: expected [ 'Sillón A', 'Sillón B', 'Sillón C' ] to deeply equal [ 'Sillón A (inactivo)', …(2) ]` |
| M07 | `agendaChairLayout.test.ts` | `Hueco libre entre dos turnos` | Matada | `AssertionError: expected undefined to be defined` |
| M08 | `agendaChairLayout.test.ts` | `Un cancelado no ocupa el sillón` | Matada | `AssertionError: expected undefined to be defined` |
| M09 | `agendaChairStyles.test.ts` | `La disponibilidad no depende sólo del color` | Matada | `AssertionError: expected 'import { useEffect, useState } from "…' to contain '<span>{slot.label}</span>'` |
| M10 | `agendaChairLayout.test.ts` | `Eje con la unión de horarios del día` | Matada | `AssertionError: expected [ Array(1) ] to deeply equal [ { startMinute: 540, …(1) }, …(1) ]` |
| M11 | `agendaChairLayout.test.ts` | `Día sin horarios de atención` | Matada | `AssertionError: expected 540 to be 480 // Object.is equality` |
| M12 | `AgendaPage.porSillon.test.tsx` | `Día por defecto desde el Clock` | Matada | `AssertionError: expected '?date=2099-01-01&view=chair' to contain 'date=2026-11-16'` |
| M13 | `AgendaPage.porSillon.test.tsx` | `Navegación de un día` | Matada | `AssertionError: expected '?date=2026-11-23&view=chair' to contain 'date=2026-11-17'` |
| M14 | `AgendaView.chair.test.tsx` | `Clic en la tarjeta abre el detalle` | Matada | `AssertionError: expected null not to be null` |
| M15 | `AgendaView.chair.test.tsx` | `Nombre accesible completo en la tarjeta` | Matada | `AssertionError: expected '10:00–10:30, Ana Pérez, Control, Sill…' to contain 'Dra. Laura Quiroga'` |
| M16 | `AgendaToolbar.chair.test.tsx` | `Recepción y administración ven el control` | Matada | `AssertionError: expected null not to be null` |
| M17 | `AgendaPage.porSillon.test.tsx` | `Odontólogo sin acceso` | Matada | `AssertionError: expected '?date=2026-11-16&view=chair' not to contain 'view=chair'` |
| M18 | `AgendaPage.porSillon.test.tsx` | `El filtro de sillón reduce las columnas` | Matada | `AssertionError: expected '?date=2026-11-16&view=chair' to contain 'chairId=00000000-0000-0000-0000-00000…'` |
| M19 | `agendaChairLayout.test.ts` | `El filtro de profesional recalcula los horarios` | Matada | `AssertionError: expected [ { startMinute: 540, …(1) }, …(1) ] to deeply equal [ Array(1) ]` |
| M20 | `AgendaToolbar.chair.test.tsx` | `La ayuda del filtro de sillón se adapta` | Matada | `AssertionError: expected <p class="helpText"></p> to be null` |
| M21 | `AgendaView.chair.test.tsx` | `La lista sigue disponible` | Matada | `AssertionError: expected null not to be null` |
| M22 | `AgendaView.chair.test.tsx` | `Un día sin turnos conserva la grilla` | Matada | `AssertionError: expected null not to be null` |
| M23 | `AgendaView.chair.test.tsx` | `Catálogo de sillones vacío` | Matada | `AssertionError: expected null not to be null` |
<!-- mutaciones:fin -->

---

## Desvíos y Hallazgos Analizados

1. **Toolbar móvil a 390 px con modo Sillones**:
   - *Hallazgo*: A 390 px de ancho, con el selector de 3 botones `[Día | Semana | Sillones]`, la fila 1 de navegación de C-36 (`navRow`) contiene `[Día | Semana | Sillones]` y `‹ Hoy ›`. Para evitar overflow o saltos de línea sin violar los tests existentes de C-36 (`AgendaToolbar.mobile.test.tsx:49`), se mantuvieron los controles en `navRow` aplicando padding compactado mediante tokens (`var(--space-2)`). El ancho resultante del grupo es de ~308 px dentro de los 374 px útiles de la pantalla, sin scroll horizontal de la página.
2. **Advertencias preexistentes de ESLint**:
   - *Causa*: Existen 3 advertencias preexistentes heredadas de C-29 y C-30 (`AppointmentFormDialog.tsx:36` por exportar `buildStartAtIso` junto con el componente, y 2 en `Dialog.tsx` por el ref `returnFocusRef`).
   - *Resolución*: Se mantienen sin tocar según la regla dura de no modificar código fuera del change; `npx eslint .` finaliza con código 0 y 0 errores.
3. **Consolidación de pruebas auxiliares de layout en 6 tests 1:1**:
   - *Causa*: La regla C1 exige correspondencia 1:1 entre escenarios y tests para mantener N tests = N mutaciones (23 vs 23).
   - *Resolución*: Las aserciones auxiliares de intervalos de atención y huecos < 15 min se integraron en los tests de los escenarios de eje horario y huecos libres correspondientes, garantizando exactamente 6 tests en `agendaChairLayout.test.ts` y 23 tests en total.
