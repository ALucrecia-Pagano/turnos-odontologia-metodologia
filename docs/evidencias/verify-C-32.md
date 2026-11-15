# Verificación de C-32 — ui-horarios-y-bloqueos

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 8 implementadas y verificadas según [tasks.md](../../openspec/changes/ui-horarios-y-bloqueos/tasks.md); fase 9 (capturas visuales multi-resolución a 1440 px, 768 px y 390 px a cargo de Claude) queda pendiente de ejecución (`[ ]` en `tasks.md`).
- **Línea base unificada**: [baseline-C-32.txt](baseline-C-32.txt) (74 archivos de test, 297 tests pasados, exit 0).
- **Vitest**: Suite final con todos los tests en verde ([test-suite-C-32.txt](test-suite-C-32.txt)): **81 archivos de test pasados (315 tests en total: 297 heredados + 18 tests nuevos de C-32)**. Los 18 tests nuevos viven en 7 archivos dedicados bajo `frontend/src/features/horarios/` (`horariosApi.test.ts` [1], `HorariosRoute.test.tsx` [1], `WorkingHoursSection.test.tsx` [4], `BlocksSection.test.tsx` [4], `BlockFormDialog.mobile.test.tsx` [1], `AffectedAppointments.test.tsx` [2], `HorariosPage.test.tsx` [5]); cada uno cuenta con su par RED/GREEN en `red-C-32/` y `green-C-32/`.
- **Mutaciones**: **20 de 20 mutaciones eliminadas** (M01–M20: 18 de escenarios testeables + 2 de tests auxiliares) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 sin cambios: sí** ([mutaciones-C-32.txt](mutaciones-C-32.txt), generado por [mutaciones-C-32.py](mutaciones-C-32.py)). Pre-check: [mutaciones-check-C-32.txt](mutaciones-check-C-32.txt).
- **Trazabilidad**: **20 escenarios** declarados en las specs delta (18 testeables 1:1 + 2 visuales a cargo de Claude) más **2 tests auxiliares** (`horariosApi.test.ts` y `HorariosRoute.test.tsx`), 0 inconsistencias, 0 tests compartidos ([trazabilidad-C-32.txt](trazabilidad-C-32.txt), generado por [trazabilidad-C-32.py](trazabilidad-C-32.py)).
- **Calidad y Tooling**:
  - `npx tsc --noEmit` exit 0 (0 errores de tipos).
  - `npx eslint .` exit 0 (0 errores, 0 advertencias en archivos de C-32; 3 advertencias preexistentes heredadas de C-29/C-30 en `AppointmentFormDialog.tsx` y `Dialog.tsx`, documentadas en Desvíos; ver [tooling-C-32.txt](tooling-C-32.txt)).
  - `npm run build` exit 0 ([build-C-32.txt](build-C-32.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 (18 passed, 0 failed; ver [validate-C-32.txt](validate-C-32.txt)).
- **Diff de tests existentes (D1 autorizado)**: [diff-tests-existentes-C-32.txt](diff-tests-existentes-C-32.txt) muestra únicamente las líneas autorizadas por el cambio de requisito D1 (habilitación de `"Horarios y bloqueos"` hacia `/horarios` en `menuFor.test.ts`, `AppShell.test.tsx` y `AppShellNavigation.test.tsx`; `AppShell.mobile.test.tsx` no requirió cambios).
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
| V01 | `frontend-working-hours-and-blocks` | Verificación visual multi-resolución en 1440, 768 y 390 px | Visual | `C-32-horarios-{1440,768,390}.png` | — | — | — | — |
| 18 | `frontend-foundation` | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Testeable | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | `03-menu-pre.txt` | `03-menu-ok.txt` | `M17` |
| 19 | `frontend-foundation` | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Testeable | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | `03-menu-pre.txt` | `03-menu-ok.txt` | `M18` |
| V02 | `frontend-foundation` | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | `C-32-appshell-{768,390}.png` | — | — | — | — |

Tests auxiliares de contrato y enrutamiento (con par RED/GREEN y mutación propia):

| Mutación | Archivo de test | Test | Evidencia RED | Evidencia GREEN |
|---|---|---|---|---|
| `M19` | `horariosApi.test.ts` | `parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock` | `01-api-ok.txt` | `01-api-ok.txt` |
| `M20` | `HorariosRoute.test.tsx` | `renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo` | `02-route.txt` | `02-route.txt` |
<!-- trazabilidad:fin -->

---

## Tabla de Mutaciones (M01–M20)

<!-- mutaciones:inicio -->
| ID | Archivo de test | Test | Estado | Mensaje de fallo |
|---|---|---|---|---|
| M01 | `HorariosPage.test.tsx` | `Odontólogo accede a sus propios horarios` | Matada | `AssertionError: expected <select …(3)></select> to be null` |
| M02 | `HorariosPage.test.tsx` | `Administrador selecciona profesional activo` | Matada | `AssertionError: expected [ 'Dra. Laura Quiroga', …(2) ] to deeply equal [ 'Dra. Laura Quiroga', …(1) ]` |
| M03 | `HorariosPage.test.tsx` | `Odontólogo consulta profesional ajeno y recibe 403` | Matada | `AssertionError: expected 'Error genérico' to contain 'No tiene permiso para leer horarios.'` |
| M04 | `WorkingHoursSection.test.tsx` | `Guardado exitoso de tramos semanales` | Matada | `Error: expect(received).toHaveTextContent()` |
| M05 | `WorkingHoursSection.test.tsx` | `Edición interactiva de tramos en la interfaz` | Matada | `AssertionError: expected <input type="text" …(5)></input> to be null` |
| M06 | `WorkingHoursSection.test.tsx` | `Rechazo por tramos solapados muestra mensaje literal del backend` | Matada | `AssertionError: expected <button type="button" …(1)></button> to be <div role="alert" …(2)>…(1)</div> // Object.is equality` |
| M07 | `WorkingHoursSection.test.tsx` | `Error 400 marca campos con aria-invalid` | Matada | `Error: expect(element).toHaveAttribute("aria-invalid", "true") // element.getAttribute("aria-invalid") === "true"` |
| M08 | `AffectedAppointments.test.tsx` | `Turnos futuros fuera del horario al guardar tramos` | Matada | `AssertionError: expected null not to be null` |
| M09 | `AffectedAppointments.test.tsx` | `Turnos solapados al crear un bloqueo` | Matada | `AssertionError: expected null not to be null` |
| M10 | `BlocksSection.test.tsx` | `Creación exitosa de bloqueo con offset` | Matada | `Error: expect(received).toHaveTextContent()` |
| M11 | `BlocksSection.test.tsx` | `Eliminación de bloqueo con confirmación in-dialog` | Matada | `Error: expect(received).toHaveTextContent()` |
| M12 | `BlocksSection.test.tsx` | `Cancelación del borrado con Escape` | Matada | `AssertionError: expected <dialog …(4)>…(1)</dialog> to be null` |
| M13 | `BlocksSection.test.tsx` | `Bloqueo inválido muestra mensaje literal del backend` | Matada | `AssertionError: expected null not to be null` |
| M14 | `HorariosPage.test.tsx` | `Recepción visualiza información completa sin controles de edición` | Matada | `AssertionError: expected [ <button …(3)></button>, …(6) ] to have a length of +0 but got 7` |
| M15 | `HorariosPage.test.tsx` | `Zona horaria leída desde GET /api/agenda` | Matada | `AssertionError: expected null not to be null` |
| M16 | `BlockFormDialog.mobile.test.tsx` | `Presentación de modal como hoja inferior en móvil` | Matada | `AssertionError: expected '.modalContent {\n  background-color: …' to contain 'border-radius: var(--radius-lg, 16px)…'` |
| M17 | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | Matada | `AssertionError: expected [ Array(1) ] to have a length of 2 but got 1` |
| M18 | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | Matada | `AssertionError: expected [ 'Agenda', 'Turnos', …(4) ] to deeply equal [ 'Turnos', 'Catálogos', …(2) ]` |
| M19 | `horariosApi.test.ts` | `parsea respuestas exitosas de getWorkingHours, replaceWorkingHours, listBlocks, createBlock y deleteBlock` | Matada | `AssertionError: expected false to be true // Object.is equality` |
| M20 | `HorariosRoute.test.tsx` | `renderiza el contenedor principal de Horarios y bloqueos en /horarios para usuario autenticado y redirige a /login si es anónimo` | Matada | `AssertionError: expected null not to be null` |
<!-- mutaciones:fin -->

---

## Desvíos y Hallazgos Analizados

1. **Cambio de requisito explícito en el menú de navegación (Decisión D1)**:
   - *Causa*: En C-25 y C-35, las pruebas `menuFor.test.ts`, `AppShell.test.tsx` y `AppShellNavigation.test.tsx` verificaban que todos los ítems posteriores a `"Agenda"` (incluido `"Horarios y bloqueos"`) estuvieran deshabilitados (`disabled: true`) con badge `"Próximamente"`. Al habilitarse el módulo `"Horarios y bloqueos"` hacia `/horarios` en C-32 para los roles `administrador`, `recepcion` y `odontologo`, dichas aserciones reflejan el nuevo contrato real del menú sin introducir seams artificiales (`enabledMenuIds`).
   - *Líneas exactas modificadas en tests existentes* (registradas íntegramente en [diff-tests-existentes-C-32.txt](diff-tests-existentes-C-32.txt)):
     - `frontend/src/features/auth/menuFor.test.ts`: líneas 13–14 (rol `administrador`), línea 23 (rol `recepcion`) y línea 32 (rol `odontologo`), verificando que `item.id === "horarios-y-bloqueos"` tenga `disabled: false`, `path: "/horarios"` y `badge: null`, mientras el resto conserva `disabled: true` y `badge: "Próximamente"`.
     - `frontend/src/shared/components/AppShell.test.tsx`: líneas 45–51 (`adminButtons` pasa de longitud 5 a 4 sin `"Horarios y bloqueos"`), línea 56 (`recepcionNav` pasa a `["Turnos", "Catálogos", "Pacientes"]`) y línea 65 (`odontologoNav` pasa a `["Catálogos", "Pacientes"]`).
     - `frontend/src/shared/components/AppShellNavigation.test.tsx`: línea 56 (`queryAllByRole("link")` pasa de longitud 1 a 2) y líneas 77 y 81–86 (`queryAllByRole("button", { name: /Próximamente/ })` pasa de 5 a 4 sin `"Horarios y bloqueos"`).
     - `frontend/src/shared/components/AppShell.mobile.test.tsx`: 0 líneas modificadas (sus aserciones de apertura/cierre de menú móvil no dependían del listado de botones deshabilitados).

2. **Advertencias preexistentes de ESLint en `npm run lint`**:
   - *Causa*: Existen 3 advertencias preexistentes heredadas de C-29 y C-30 (`AppointmentFormDialog.tsx:36` por `react-refresh/only-export-components` al exportar `buildStartAtIso` junto al componente, y `Dialog.tsx:78` y `Dialog.tsx:100` por `react-hooks/exhaustive-deps` en `returnFocusRef`). Como `package.json` define `"lint": "eslint . --max-warnings 0"`, `npm run lint` devuelve código 1 por esas 3 advertencias ajenas a C-32, mientras que `npx eslint .` finaliza con código 0 y 0 errores (y 0 advertencias en todos los archivos de C-32).
   - *Resolución*: Se mantienen sin tocar `AppointmentFormDialog.tsx` y `Dialog.tsx` cumpliendo la regla dura de no modificar código fuera del alcance del change (mismo criterio documentado en `verify-C-31.md`).

3. **Limpieza de `actionErrors` de `AuthContext` ante rechazo 403 en `/horarios`**:
   - *Causa*: El cliente con sesión de `AuthContext` registra automáticamente cualquier respuesta `403` en `actionErrors`, lo que hace que `AppShell` renderice un segundo banner `role="alert"` además de la alerta propia de `HorariosPage`.
   - *Resolución*: Al igual que `AgendaPage.tsx`, `HorariosPage.tsx` invoca `clearActionErrors()` y extrae los mensajes literales mediante `getApiErrorMessages(hoursRes.error)` cuando recibe un error al cargar horarios o bloqueos, garantizando un único contenedor `role="alert"` con el mensaje literal del backend y manteniendo la sesión activa.
