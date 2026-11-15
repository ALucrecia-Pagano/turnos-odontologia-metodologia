# Verificación de C-32 — ui-horarios-y-bloqueos

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 8 y Fase 10 (corrección post-verificación A–E) implementadas y verificadas según [tasks.md](../../openspec/changes/ui-horarios-y-bloqueos/tasks.md); Fase 9 (capturas visuales multi-resolución a 1440 px, 768 px y 390 px a cargo de Claude) queda pendiente (`[ ]` en `tasks.md`) para la nueva revisión visual.
- **Línea base unificada**: [baseline-C-32.txt](baseline-C-32.txt) (74 archivos de test, 297 tests pasados, exit 0).
- **Vitest**: Suite final con todos los tests en verde ([test-suite-C-32.txt](test-suite-C-32.txt)): **82 archivos de test pasados (321 tests en total: 297 heredados + 24 tests nuevos de C-32)**. Los **24 tests nuevos** se componen de **18 tests del apply inicial** (16 de escenario + 2 auxiliares) más **6 tests nuevos de la corrección post-verificación** (puntos A, B, C, D1, D2 y E), distribuidos en 8 archivos dedicados bajo `frontend/src/features/horarios/` (`horariosApi.test.ts` [1], `HorariosRoute.test.tsx` [1], `WorkingHoursSection.test.tsx` [4], `BlocksSection.test.tsx` [5], `BlockFormDialog.mobile.test.tsx` [1], `AffectedAppointments.test.tsx` [3], `HorariosPage.test.tsx` [7], `horariosStyles.test.ts` [2]); cada uno cuenta con su par RED/GREEN en `red-C-32/` (`01`..`25`) y `green-C-32/` (`01`..`25`).
- **Mutaciones**: **26 de 26 mutaciones eliminadas** (`M01`–`M26`: 24 tests nuevos [22 de escenario + 2 auxiliares] más 2 tests existentes modificados con mutación en `AppShellNavigation.test.tsx`) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 sin cambios: sí** ([mutaciones-C-32.txt](mutaciones-C-32.txt), generado por [mutaciones-C-32.py](mutaciones-C-32.py)). Pre-check: [mutaciones-check-C-32.txt](mutaciones-check-C-32.txt).
- **Trazabilidad**: **26 escenarios** declarados en las specs delta (24 testeables 1:1 numerados de corrido `01`..`24` + 2 visuales `V01`, `V02` a cargo de Claude) más **2 tests auxiliares** (`horariosApi.test.ts` [`M19`] y `HorariosRoute.test.tsx` [`M20`]), 0 inconsistencias, 0 tests compartidos ([trazabilidad-C-32.txt](trazabilidad-C-32.txt), generado por [trazabilidad-C-32.py](trazabilidad-C-32.py)).
- **Calidad y Tooling**:
  - `npx tsc --noEmit` exit 0 (0 errores de tipos).
  - `npx eslint .` exit 0 (0 errores, 0 advertencias en archivos de C-32; 3 advertencias preexistentes heredadas de C-29/C-30 en `AppointmentFormDialog.tsx` y `Dialog.tsx`, documentadas en Desvíos; ver [tooling-C-32.txt](tooling-C-32.txt)).
  - `npm run build` exit 0 ([build-C-32.txt](build-C-32.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 (18 passed, 0 failed; ver [validate-C-32.txt](validate-C-32.txt)).
- **Diff de tests existentes (D1 autorizado)**: [diff-tests-existentes-C-32.txt](diff-tests-existentes-C-32.txt) (generado con `2>/dev/null` sin warnings de CRLF) muestra únicamente las **11 aserciones en 3 archivos** (`menuFor.test.ts`: 4, `AppShell.test.tsx`: 4, `AppShellNavigation.test.tsx`: 3) autorizadas por el cambio de requisito D1 (`AppShell.mobile.test.tsx` no requirió cambios).
- **Skill y MCP**: Consulta documentada en [docs/skills-mcp/evidencias/C-32-skill-mcp.md](../skills-mcp/evidencias/C-32-skill-mcp.md). Aplicada la skill `appointment-frontend-ux` y consultado el MCP `context7` (`/remix-run/react-router`).

---

## Matriz Escenario → Test → Evidencias → Mutación

<!-- trazabilidad:inicio -->
| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |
|---|---|---|---|---|---|---|---|---|
| 01 | `frontend-working-hours-and-blocks` | Odontólogo accede a sus propios horarios | Testeable | `HorariosPage.test.tsx` | `Odontólogo accede a sus propios horarios` | `15-role-dentist-own.txt` | `15-role-dentist-own.txt` | `M01` |
| 02 | `frontend-working-hours-and-blocks` | Administrador selecciona profesional activo | Testeable | `HorariosPage.test.tsx` | `Administrador selecciona profesional activo` | `16-role-admin-selector.txt` | `16-role-admin-selector.txt` | `M02` |
| 03 | `frontend-working-hours-and-blocks` | Odontólogo consulta profesional ajeno y recibe 403 | Testeable | `HorariosPage.test.tsx` | `Odontólogo consulta profesional ajeno y recibe 403` | `17-role-dentist-403.txt` | `17-role-dentist-403.txt` | `M03` |
| 04 | `frontend-working-hours-and-blocks` | Guardado exitoso de tramos semanales | Testeable | `WorkingHoursSection.test.tsx` | `Guardado exitoso de tramos semanales` | `04-hours-save-ok.txt` | `04-hours-save-ok.txt` | `M04` |
| 05 | `frontend-working-hours-and-blocks` | Edición interactiva de tramos en la interfaz | Testeable | `WorkingHoursSection.test.tsx` | `Edición interactiva de tramos en la interfaz` | `05-hours-add-remove.txt` | `05-hours-add-remove.txt` | `M05` |
| 06 | `frontend-working-hours-and-blocks` | Rechazo por tramos solapados muestra mensaje literal del backend | Testeable | `WorkingHoursSection.test.tsx` | `Rechazo por tramos solapados muestra mensaje literal del backend` | `06-hours-overlap-422.txt` | `06-hours-overlap-422.txt` | `M06` |
| 07 | `frontend-working-hours-and-blocks` | Error 400 marca campos con aria-invalid | Testeable | `WorkingHoursSection.test.tsx` | `Error 400 marca campos con aria-invalid` | `07-hours-format-400.txt` | `07-hours-format-400.txt` | `M07` |
| 08 | `frontend-working-hours-and-blocks` | Turnos futuros fuera del horario al guardar tramos | Testeable | `AffectedAppointments.test.tsx` | `Turnos futuros fuera del horario al guardar tramos` | `13-affected-hours.txt` | `13-affected-hours.txt` | `M08` |
| 09 | `frontend-working-hours-and-blocks` | Turnos solapados al crear un bloqueo | Testeable | `AffectedAppointments.test.tsx` | `Turnos solapados al crear un bloqueo` | `14-affected-block.txt` | `14-affected-block.txt` | `M09` |
| 10 | `frontend-working-hours-and-blocks` | Creación exitosa de bloqueo con offset | Testeable | `BlocksSection.test.tsx` | `Creación exitosa de bloqueo con offset` | `08-block-create-ok.txt` | `08-block-create-ok.txt` | `M10` |
| 11 | `frontend-working-hours-and-blocks` | Eliminación de bloqueo con confirmación in-dialog | Testeable | `BlocksSection.test.tsx` | `Eliminación de bloqueo con confirmación in-dialog` | `09-block-delete-ok.txt` | `09-block-delete-ok.txt` | `M11` |
| 12 | `frontend-working-hours-and-blocks` | Cancelación del borrado con Escape | Testeable | `BlocksSection.test.tsx` | `Cancelación del borrado con Escape` | `10-block-delete-escape.txt` | `10-block-delete-escape.txt` | `M12` |
| 13 | `frontend-working-hours-and-blocks` | Bloqueo inválido muestra mensaje literal del backend | Testeable | `BlocksSection.test.tsx` | `Bloqueo inválido muestra mensaje literal del backend` | `11-block-invalid-422.txt` | `11-block-invalid-422.txt` | `M13` |
| 14 | `frontend-working-hours-and-blocks` | Recepción visualiza información completa sin controles de edición | Testeable | `HorariosPage.test.tsx` | `Recepción visualiza información completa sin controles de edición` | `18-role-reception-readonly.txt` | `18-role-reception-readonly.txt` | `M14` |
| 15 | `frontend-working-hours-and-blocks` | Zona horaria leída desde GET /api/agenda | Testeable | `HorariosPage.test.tsx` | `Zona horaria leída desde GET /api/agenda` | `19-timezone-api.txt` | `19-timezone-api.txt` | `M15` |
| 16 | `frontend-working-hours-and-blocks` | Presentación de modal como hoja inferior en móvil | Testeable | `BlockFormDialog.mobile.test.tsx` | `Presentación de modal como hoja inferior en móvil` | `12-block-bottom-sheet.txt` | `12-block-bottom-sheet.txt` | `M16` |
| 17 | `frontend-foundation` | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Testeable | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | `03-menu-pre.txt` | `03-menu-ok.txt` | `M17` |
| 18 | `frontend-foundation` | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Testeable | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | `03-menu-pre.txt` | `03-menu-ok.txt` | `M18` |
| 19 | `frontend-working-hours-and-blocks` | Todas las variables CSS de horarios existen en tokens.css | Testeable | `horariosStyles.test.ts` | `Todas las variables CSS de horarios existen en tokens.css` | `20-css-tokens-exist.txt` | `20-css-tokens-exist.txt` | `M21` |
| 20 | `frontend-working-hours-and-blocks` | Encabezado y estilos de HorariosPage sin tokens de fondo oscuro | Testeable | `horariosStyles.test.ts` | `Encabezado y estilos de HorariosPage sin tokens de fondo oscuro` | `21-css-header-light-tokens.txt` | `21-css-header-light-tokens.txt` | `M22` |
| 21 | `frontend-working-hours-and-blocks` | Título de PageShell Horarios y bloqueos con único h1 | Testeable | `HorariosPage.test.tsx` | `Título de PageShell Horarios y bloqueos con único h1` | `22-pageshell-title-h1.txt` | `22-pageshell-title-h1.txt` | `M23` |
| 22 | `frontend-working-hours-and-blocks` | Eliminar bloqueo oculta su panel de turnos afectados | Testeable | `BlocksSection.test.tsx` | `Eliminar bloqueo oculta su panel de turnos afectados` | `23-delete-block-clears-affected.txt` | `23-delete-block-clears-affected.txt` | `M24` |
| 23 | `frontend-working-hours-and-blocks` | Un solo mensaje de estado vigente entre acciones sin desmontar la región | Testeable | `HorariosPage.test.tsx` | `Un solo mensaje de estado vigente entre acciones sin desmontar la región` | `24-single-status-message.txt` | `24-single-status-message.txt` | `M25` |
| 24 | `frontend-working-hours-and-blocks` | Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar | Testeable | `AffectedAppointments.test.tsx` | `Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar` | `25-dates-local-format.txt` | `25-dates-local-format.txt` | `M26` |
| V01 | `frontend-working-hours-and-blocks` | Verificación visual multi-resolución en 1440, 768 y 390 px | Visual | `C-32-horarios-{1440,768,390}.png` | — | — | — | — |
| V02 | `frontend-foundation` | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | `C-32-appshell-{768,390}.png` | — | — | — | — |

Tests auxiliares de contrato y enrutamiento (con par RED/GREEN y mutación propia):

| Mutación | Archivo de test | Test | Evidencia RED | Evidencia GREEN |
|---|---|---|---|---|
| `M19` | `horariosApi.test.ts` | `parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock` | `01-api-ok.txt` | `01-api-ok.txt` |
| `M20` | `HorariosRoute.test.tsx` | `renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo` | `02-route.txt` | `02-route.txt` |
<!-- trazabilidad:fin -->

---

## Tabla de Mutaciones (M01–M26)

<!-- mutaciones:inicio -->
| ID | Archivo de test | Test | Estado | Mensaje de fallo |
|---|---|---|---|---|
| M01 | `HorariosPage.test.tsx` | `Odontólogo accede a sus propios horarios` | Matada | `AssertionError: expected <select …(3)></select> to be null` |
| M02 | `HorariosPage.test.tsx` | `Administrador selecciona profesional activo` | Matada | `AssertionError: expected [ 'Dra. Laura Quiroga', …(2) ] to deeply equal [ 'Dra. Laura Quiroga', …(1) ]` |
| M03 | `HorariosPage.test.tsx` | `Odontólogo consulta profesional ajeno y recibe 403` | Matada | `AssertionError: expected 'Error genérico' to contain 'No tiene permiso para leer horarios.'` |
| M04 | `WorkingHoursSection.test.tsx` | `Guardado exitoso de tramos semanales` | Matada | `Error: expect(element).toHaveTextContent()` |
| M05 | `WorkingHoursSection.test.tsx` | `Edición interactiva de tramos en la interfaz` | Matada | `AssertionError: expected <input type="text" …(5)></input> to be null` |
| M06 | `WorkingHoursSection.test.tsx` | `Rechazo por tramos solapados muestra mensaje literal del backend` | Matada | `AssertionError: expected <button type="button" …(1)></button> to be <div role="alert" …(2)>…(1)</div> // Object.is equality` |
| M07 | `WorkingHoursSection.test.tsx` | `Error 400 marca campos con aria-invalid` | Matada | `Error: expect(element).toHaveAttribute("aria-invalid", "true") // element.getAttribute("aria-invalid") === "true"` |
| M08 | `AffectedAppointments.test.tsx` | `Turnos futuros fuera del horario al guardar tramos` | Matada | `AssertionError: expected null not to be null` |
| M09 | `AffectedAppointments.test.tsx` | `Turnos solapados al crear un bloqueo` | Matada | `AssertionError: expected null not to be null` |
| M10 | `BlocksSection.test.tsx` | `Creación exitosa de bloqueo con offset` | Matada | `Error: expect(element).toHaveTextContent()` |
| M11 | `BlocksSection.test.tsx` | `Eliminación de bloqueo con confirmación in-dialog` | Matada | `Error: expect(element).toHaveTextContent()` |
| M12 | `BlocksSection.test.tsx` | `Cancelación del borrado con Escape` | Matada | `AssertionError: expected <dialog …(4)>…(1)</dialog> to be null` |
| M13 | `BlocksSection.test.tsx` | `Bloqueo inválido muestra mensaje literal del backend` | Matada | `AssertionError: expected null not to be null` |
| M14 | `HorariosPage.test.tsx` | `Recepción visualiza información completa sin controles de edición` | Matada | `AssertionError: expected [ <button …(3)></button>, …(6) ] to have a length of +0 but got 7` |
| M15 | `HorariosPage.test.tsx` | `Zona horaria leída desde GET /api/agenda` | Matada | `AssertionError: expected null not to be null` |
| M16 | `BlockFormDialog.mobile.test.tsx` | `Presentación de modal como hoja inferior en móvil` | Matada | `AssertionError: expected '.modalContent {\n  background-color: …' to contain 'border-radius: var(--radius-lg, 16px)…'` |
| M17 | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | Matada | `AssertionError: expected [ Array(1) ] to have a length of 2 but got 1` |
| M18 | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | Matada | `AssertionError: expected [ 'Agenda', 'Turnos', …(4) ] to deeply equal [ 'Turnos', 'Catálogos', …(2) ]` |
| M19 | `horariosApi.test.ts` | `parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock` | Matada | `AssertionError: expected false to be true // Object.is equality` |
| M20 | `HorariosRoute.test.tsx` | `renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo` | Matada | `AssertionError: expected null not to be null` |
| M21 | `horariosStyles.test.ts` | `Todas las variables CSS de horarios existen en tokens.css` | Matada | `AssertionError: expected [ Array(1) ] to deeply equal []` |
| M22 | `horariosStyles.test.ts` | `Encabezado y estilos de HorariosPage sin tokens de fondo oscuro` | Matada | `AssertionError: expected '.page {\n  width: 100%;\n  max-width:…' not to match /--color-ice/` |
| M23 | `HorariosPage.test.tsx` | `Título de PageShell Horarios y bloqueos con único h1` | Matada | `AssertionError: expected [] to have a length of 1 but got +0` |
| M24 | `BlocksSection.test.tsx` | `Eliminar bloqueo oculta su panel de turnos afectados` | Matada | `AssertionError: expected <strong></strong> to be null` |
| M25 | `HorariosPage.test.tsx` | `Un solo mensaje de estado vigente entre acciones sin desmontar la región` | Matada | `AssertionError: expected [ Array(2) ] to have a length of 1 but got 2` |
| M26 | `AffectedAppointments.test.tsx` | `Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar` | Matada | `Error: expect(element).toHaveTextContent()` |
<!-- mutaciones:fin -->

---

## Corrección post-verificación

Durante la verificación manual en navegador con la API real se detectaron 5 puntos en `frontend/src/features/horarios/`, resueltos mediante Strict TDD (6 escenarios nuevos en `spec.md`, 6 pares RED/GREEN `20`–`25`, 6 tests nuevos y 6 mutaciones `M21`–`M26`):

1. **A) Tokens CSS inexistentes en `.module.css` de horarios**:
   - *Problema*: `WorkingHoursSection.module.css`, `BlocksSection.module.css`, `BlockFormDialog.module.css` y `BlockDeleteDialog.module.css` usaban variables ausentes en `frontend/src/shared/styles/tokens.css` (`--focus-ring-color`, `--focus-ring-width`, `--focus-ring-offset`, `--color-border-strong`, `--color-danger-bg`, `--color-success-bg`, `--color-success-border`, `--color-success-text`, `--color-primary-hover`, `--color-primary-soft`, `--color-surface-muted`, `--shadow-xs`, `--font-weight-semibold`), provocando `outline: none` en foco y campos de hora sin borde.
   - *Solución*: Se reemplazaron exclusivamente por tokens existentes en `tokens.css` sin agregar variables nuevas: foco con `outline: 2px solid var(--color-focus); outline-offset: 2px;` (igual que `features/agenda`), `--color-border`, `--color-danger-background`, `--color-background`, `--color-navy`, `--shadow-sm`, `--font-weight-bold` y `--font-weight-medium`. Para el banner de estado exitoso (`role="status"`), al no existir un token dedicado `--color-success-*` en `tokens.css`, se eligieron los tokens de superficie clara con borde de acento que ya emplea la paleta de `tokens.css` (`background: var(--color-background)`, `color: var(--color-text)`, `border: 1px solid var(--color-accent)`).
   - *Test y mutación*: `horariosStyles.test.ts` :: `"Todas las variables CSS de horarios existen en tokens.css"` ([red-C-32/20-css-tokens-exist.txt](red-C-32/20-css-tokens-exist.txt), [green-C-32/20-css-tokens-exist.txt](green-C-32/20-css-tokens-exist.txt), mutación `M21`).

2. **B) Encabezado con tokens de fondo oscuro en `HorariosPage.module.css`**:
   - *Problema*: `HorariosPage.module.css` utilizaba `--color-ice`, `--field-on-navy`, `--border-on-navy-strong` y `--alert-on-navy-*` en `.title`, `.subtitle`, `.selectorLabel`, `.selector` y `.alertBanner` sobre el fondo claro de `PageShell`, haciendo ilegible el contraste.
   - *Solución*: Se reemplazaron por los tokens de superficie clara que usan `AgendaToolbar.module.css` y `AgendaView.module.css`: `--color-text`, `--color-text-muted`, `--color-background`, `--color-border`, `--color-danger-background`, `--color-danger-border`, `--color-danger-text` y `--color-focus`.
   - *Test y mutación*: `horariosStyles.test.ts` :: `"Encabezado y estilos de HorariosPage sin tokens de fondo oscuro"` ([red-C-32/21-css-header-light-tokens.txt](red-C-32/21-css-header-light-tokens.txt), [green-C-32/21-css-header-light-tokens.txt](green-C-32/21-css-header-light-tokens.txt), mutación `M22`).

3. **C) Título de `PageShell` en `HorariosPage.tsx`**:
   - *Problema*: `HorariosPage.tsx` pasaba `title="Turnos Odontología"` a `PageShell`.
   - *Solución*: Se actualizó a `<PageShell title="Horarios y bloqueos">` (igual que `AgendaPage` pasa su título) manteniendo un único `<h1>` en la página.
   - *Test y mutación*: `HorariosPage.test.tsx` :: `"Título de PageShell Horarios y bloqueos con único h1"` ([red-C-32/22-pageshell-title-h1.txt](red-C-32/22-pageshell-title-h1.txt), [green-C-32/22-pageshell-title-h1.txt](green-C-32/22-pageshell-title-h1.txt), mutación `M23`).

4. **D) Limpieza de paneles y mensajes viejos entre acciones (D1 y D2)**:
   - *Problema*: (D1) Al eliminar un bloqueo, el panel `"Turnos existentes solapados con el bloqueo creado"` permanecía visible. (D2) Cada sección tenía su propio estado `role="status"` que se montaba/desmontaba condicionalmente y permitía que coexistieran dos mensajes de acciones distintas (`"Horario guardado."` y `"Bloqueo creado."` / `"Bloqueo eliminado."`).
   - *Solución*: (D1) En `BlocksSection.tsx`, `handleConfirmDelete` limpia `setAffectedAppointments([])` tras confirmar el `DELETE`. (D2) `HorariosPage.tsx` mantiene montada permanentemente una única región `role="status"` `aria-live="polite"` y coordina el mensaje mediante `onStatusChange={setStatusMessage}` en `WorkingHoursSection.tsx` y `BlocksSection.tsx`, limpiándolo al iniciar otra acción y reemplazándolo al completarla (cuando `WorkingHoursSection` o `BlocksSection` se montan aislados en tests unitarios sin `onStatusChange`, mantienen igualmente montada su propia región `role="status"`).
   - *Tests y mutaciones*:
     - D1: `BlocksSection.test.tsx` :: `"Eliminar bloqueo oculta su panel de turnos afectados"` ([red-C-32/23-delete-block-clears-affected.txt](red-C-32/23-delete-block-clears-affected.txt), [green-C-32/23-delete-block-clears-affected.txt](green-C-32/23-delete-block-clears-affected.txt), mutación `M24`).
     - D2: `HorariosPage.test.tsx` :: `"Un solo mensaje de estado vigente entre acciones sin desmontar la región"` ([red-C-32/24-single-status-message.txt](red-C-32/24-single-status-message.txt), [green-C-32/24-single-status-message.txt](green-C-32/24-single-status-message.txt), mutación `M25`).

5. **E) Fechas en formato local `es-AR` en lugar de ISO `YYYY-MM-DD`**:
   - *Problema*: En la lista de turnos afectados (`AffectedAppointments.tsx`), la lista de bloqueos (`BlocksSection.tsx`) y el modal de eliminar (`BlockDeleteDialog.tsx`), la fecha se mostraba en ISO (`"2026-11-17"`).
   - *Solución*: En `horariosTime.ts`, `formatLocalRangeInZone` ahora formatea las fechas con `new Intl.DateTimeFormat("es-AR", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric", timeZone }).format(new Date(instant))` (`formatDisplayDateInZone`), reutilizando la `timezone` obtenida de `GET /api/agenda` sin constantes hardcodeadas (`"mar, 17/11/2026"` para `"2026-11-17T15:00:00Z"` en `America/Argentina/Buenos_Aires`).
   - *Test y mutación*: `AffectedAppointments.test.tsx` :: `"Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar"` ([red-C-32/25-dates-local-format.txt](red-C-32/25-dates-local-format.txt), [green-C-32/25-dates-local-format.txt](green-C-32/25-dates-local-format.txt), mutación `M26`).

---

## Desvíos y Hallazgos Analizados

1. **Cambio de requisito explícito en el menú de navegación (Decisión D1 — 11 aserciones en 3 archivos)**:
   - *Causa*: En C-25 y C-35, las pruebas `menuFor.test.ts`, `AppShell.test.tsx` y `AppShellNavigation.test.tsx` verificaban que todos los ítems posteriores a `"Agenda"` (incluido `"Horarios y bloqueos"`) estuvieran deshabilitados (`disabled: true`) con badge `"Próximamente"`. Al habilitarse el módulo `"Horarios y bloqueos"` hacia `/horarios` en C-32 para los roles `administrador`, `recepcion` y `odontologo`, dichas aserciones reflejan el nuevo contrato real del menú sin introducir seams artificiales (`enabledMenuIds`). Los títulos históricos de los tests en `menuFor.test.ts` y `AppShell.test.tsx` se mantuvieron intactos deliberadamente para no tocar más líneas de tests existentes y conservar la trazabilidad exacta con los changes C-25 y C-35 archivados.
   - *Conteo real de aserciones modificadas*: **11 aserciones en 3 archivos: `menuFor.test.ts` (4), `AppShell.test.tsx` (4), `AppShellNavigation.test.tsx` (3)** (registradas íntegramente en [diff-tests-existentes-C-32.txt](diff-tests-existentes-C-32.txt)):
     - `frontend/src/features/auth/menuFor.test.ts` (**4 aserciones**): líneas 11–12 (2 aserciones en rol `administrador`), línea 21 (1 aserción en rol `recepcion`) y línea 30 (1 aserción en rol `odontologo`), verificando que `item.id === "horarios-y-bloqueos"` tenga `disabled: false`, `path: "/horarios"` y `badge: null`, mientras el resto conserva `disabled: true` y `badge: "Próximamente"`.
     - `frontend/src/shared/components/AppShell.test.tsx` (**4 aserciones**): líneas 43 y 44–50 (2 aserciones en `adminButtons`, que pasa de longitud 5 a 4 sin `"Horarios y bloqueos"`), línea 55 (1 aserción en `recepcionNav`, que pasa a `["Turnos", "Catálogos", "Pacientes"]`) y línea 64 (1 aserción en `odontologoNav`, que pasa a `["Catálogos", "Pacientes"]`).
     - `frontend/src/shared/components/AppShellNavigation.test.tsx` (**3 aserciones**): línea 77 (1 aserción: `queryAllByRole("link")` pasa de longitud 1 a 2), línea 86 (1 aserción: `queryAllByRole("button", { name: /Próximamente/ })` pasa de 5 a 4) y líneas 90–95 (1 aserción: lista de `data-menu-item` en botones deshabilitados sin `"Horarios y bloqueos"`).
     - `frontend/src/shared/components/AppShell.mobile.test.tsx`: **0 aserciones modificadas** (sus aserciones de apertura/cierre de menú móvil no dependían del listado de botones deshabilitados).

2. **Advertencias preexistentes de ESLint en `npm run lint`**:
   - *Causa*: Existen 3 advertencias preexistentes heredadas de C-29 y C-30 (`AppointmentFormDialog.tsx:36` por `react-refresh/only-export-components` al exportar `buildStartAtIso` junto al componente, y `Dialog.tsx:78` y `Dialog.tsx:100` por `react-hooks/exhaustive-deps` en `returnFocusRef`). Como `package.json` define `"lint": "eslint . --max-warnings 0"`, `npm run lint` devuelve código 1 por esas 3 advertencias ajenas a C-32, mientras que `npx eslint .` finaliza con código 0 y 0 errores (y 0 advertencias en todos los archivos de C-32).
   - *Resolución*: Se mantienen sin tocar `AppointmentFormDialog.tsx` y `Dialog.tsx` cumpliendo la regla dura de no modificar código fuera del alcance del change (mismo criterio documentado en `verify-C-31.md`).

3. **Limpieza de `actionErrors` de `AuthContext` ante rechazo 403 en `/horarios`**:
   - *Causa*: El cliente con sesión de `AuthContext` registra automáticamente cualquier respuesta `403` en `actionErrors`, lo que hace que `AppShell` renderice un segundo banner `role="alert"` además de la alerta propia de `HorariosPage`.
   - *Resolución*: Al igual que `AgendaPage.tsx`, `HorariosPage.tsx` invoca `clearActionErrors()` y extrae los mensajes literales mediante `getApiErrorMessages(hoursRes.error)` cuando recibe un error al cargar horarios o bloqueos, garantizando un único contenedor `role="alert"` con el mensaje literal del backend y manteniendo la sesión activa.
