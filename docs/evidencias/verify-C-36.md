# Verificación de C-36 — ui-tema-oscuro-y-movil

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 6 implementadas y verificadas de forma autónoma según [tasks.md](../../openspec/changes/ui-tema-oscuro-y-movil/tasks.md); fase 7 (capturas visuales multi-resolución) preparada y delegada a Claude.
- **Vitest**: Línea base de **260 tests en 64 archivos**; suite final de **268 tests en 68 archivos**, todos en verde ([test-suite-C-36.txt](test-suite-C-36.txt)). Los 8 tests nuevos se encuentran en 4 archivos aislados (`AppShell.mobile.test.tsx`, `AgendaToolbar.mobile.test.tsx`, `AgendaGrid.mobile.test.tsx`, `Dialog.bottomSheet.test.tsx`); cada uno cuenta con su par RED/GREEN documentado.
- **Mutaciones**: **8 de 8 mutaciones eliminadas** (M01–M08) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 sin cambios: sí** ([mutaciones-C-36.txt](mutaciones-C-36.txt), generado por [mutaciones-C-36.py](mutaciones-C-36.py)).
- **Trazabilidad**: **12 escenarios** declarados en specs delta (8 testeables 1:1 + 4 visuales a cargo de Claude), 0 inconsistencias ([trazabilidad-C-36.txt](trazabilidad-C-36.txt), generado por [trazabilidad-C-36.py](trazabilidad-C-36.py)).
- **Calidad y Tooling**:
  - `npx tsc --noEmit` exit 0 (0 errores de tipos).
  - `npx eslint .` exit 0 (0 errores, 3 advertencias preexistentes heredadas de C-29/C-30 documentadas en Desvíos; ver [tooling-C-36.txt](tooling-C-36.txt)).
  - `npm run build` exit 0 ([build-C-36.txt](build-C-36.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 con 19 especificaciones válidas ([validate-C-36.txt](validate-C-36.txt)).
- **Tests existentes intocables**: `git diff main --diff-filter=M --stat -- "*.test.ts" "*.test.tsx"` devuelve vacío ([diff-tests-existentes-C-36.txt](diff-tests-existentes-C-36.txt)).
- **Skill y Context7**: Consulta documentada en [C-36-context7.md](../skills-mcp/evidencias/C-36-context7.md) sobre soporte de `scroll-snap-type: x mandatory`, `scroll-padding-left` y `90dvh`. Aplicada la skill `appointment-frontend-ux`.

---

## Matriz Escenario → Test → Evidencias → Mutación

<!-- trazabilidad:inicio -->
| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |
|---|---|---|---|---|---|---|---|---|
| 01 | `frontend-foundation` | Cabecera compacta y apertura de menú en celular | Testeable | `AppShell.mobile.test.tsx` | `01-cabecera-compacta-y-apertura-menu` | `01-appshell-menu-red.txt` | `01-appshell-menu-green.txt` | `M01` |
| 02 | `frontend-foundation` | Cierre del menú con Escape y retorno de foco al botón | Testeable | `AppShell.mobile.test.tsx` | `02-cierre-menu-escape-y-retorno-foco` | `02-appshell-escape-red.txt` | `02-appshell-escape-green.txt` | `M02` |
| V01 | `frontend-foundation` | Navegación de AppShell y menú verificados a 1440, 768 y 390 px | Visual | — | — | — | — | — |
| 07 | `frontend-foundation` | Hoja inferior a ancho completo con scroll interno en celular | Testeable | `Dialog.bottomSheet.test.tsx` | `07-dialog-bottom-sheet-mobile` | `07-dialog-bottom-sheet-red.txt` | `07-dialog-bottom-sheet-green.txt` | `M07` |
| 08 | `frontend-foundation` | Preservación de modal centrado flotante en tablet y escritorio | Testeable | `Dialog.bottomSheet.test.tsx` | `08-dialog-modal-centrado-desktop` | `08-dialog-centrado-desktop-red.txt` | `08-dialog-centrado-desktop-green.txt` | `M08` |
| V02 | `frontend-foundation` | Modales de turnos verificados a 1440, 768 y 390 px | Visual | — | — | — | — | — |
| 03 | `frontend-agenda` | Organización compacta de navegación y fecha en celular | Testeable | `AgendaToolbar.mobile.test.tsx` | `03-toolbar-distribucion-compacta` | `03-toolbar-compacta-red.txt` | `03-toolbar-compacta-green.txt` | `M03` |
| 04 | `frontend-agenda` | Botón Filtros con contador de filtros activos y panel accesible | Testeable | `AgendaToolbar.mobile.test.tsx` | `04-toolbar-boton-filtros-con-contador` | `04-toolbar-filtros-red.txt` | `04-toolbar-filtros-green.txt` | `M04` |
| V03 | `frontend-agenda` | Toolbar de agenda verificada a 1440, 768 y 390 px | Visual | — | — | — | — | — |
| 05 | `frontend-agenda` | Desplazamiento horizontal fluido con scroll-snap y horas fijas | Testeable | `AgendaGrid.mobile.test.tsx` | `05-grilla-scroll-snap-y-horas-sticky` | `05-grilla-scroll-snap-red.txt` | `05-grilla-scroll-snap-green.txt` | `M05` |
| 06 | `frontend-agenda` | Columna completa al ancho útil y preservación de grilla por defecto | Testeable | `AgendaGrid.mobile.test.tsx` | `06-grilla-ancho-util-y-default-grid` | `06-grilla-ancho-util-red.txt` | `06-grilla-ancho-util-green.txt` | `M06` |
| V04 | `frontend-agenda` | Grilla de agenda verificada a 1440, 768 y 390 px | Visual | — | — | — | — | — |
<!-- trazabilidad:fin -->

---

## Tabla de Mutaciones (M01–M08)

<!-- mutaciones:inicio -->
| ID | Archivo de test | Test | Estado | Mensaje de fallo |
|---|---|---|---|---|
| M01 | `AppShell.mobile.test.tsx` | `01-cabecera-compacta-y-apertura-menu` | ELIMINADA | `Error: expect(element).toHaveAttribute("aria-controls", "main-menu") // element.getAttribute("aria-controls") === "main-menu"` |
| M02 | `AppShell.mobile.test.tsx` | `02-cierre-menu-escape-y-retorno-foco` | ELIMINADA | `AssertionError: expected <a data-menu-item="Agenda" …(3)></a> to be <button type="button" …(3)>…(2)</button> // Object.is equality` |
| M03 | `AgendaToolbar.mobile.test.tsx` | `03-toolbar-distribucion-compacta` | ELIMINADA | `AssertionError: expected null not to be null` |
| M04 | `AgendaToolbar.mobile.test.tsx` | `04-toolbar-boton-filtros-con-contador` | ELIMINADA | `Error: expect(element).toHaveTextContent()` |
| M05 | `AgendaGrid.mobile.test.tsx` | `05-grilla-scroll-snap-y-horas-sticky` | ELIMINADA | `Error: expect(element).toHaveAttribute("data-scroll-snap", "mandatory") // element.getAttribute("data-scroll-snap") === "mandatory"` |
| M06 | `AgendaGrid.mobile.test.tsx` | `06-grilla-ancho-util-y-default-grid` | ELIMINADA | `AssertionError: expected null not to be null` |
| M07 | `Dialog.bottomSheet.test.tsx` | `07-dialog-bottom-sheet-mobile` | ELIMINADA | `Error: expect(element).toHaveAttribute("data-mobile-sheet", "true") // element.getAttribute("data-mobile-sheet") === "true"` |
| M08 | `Dialog.bottomSheet.test.tsx` | `08-dialog-modal-centrado-desktop` | ELIMINADA | `Error: expect(element).not.toHaveAttribute("data-mobile-sheet") // element.hasAttribute("data-mobile-sheet")` |
<!-- mutaciones:fin -->

---

## Desvíos y Hallazgos Analizados

1. **Reenfoque de C-36 en celular de la aplicación autenticada**:
   - *Causa*: La portada y el acceso ya fueron resueltos como superficies oscuras en C-35, mientras que la decisión A de C-35 fijó la aplicación como superficie clara con modales claros. Extender un tema oscuro arbitrario dentro de la agenda requería invertir la decisión de diseño de C-35. Siguiendo las instrucciones explícitas y la exploración previa (`docs/evidencias/explore-C-36.md`), C-36 se reenfoca en resolver las fallas reales de usabilidad móvil en la app (AppShell, Toolbar, Grilla y Modales), postergando el tema oscuro de la app al backlog post-entrega.
2. **Preservación estructural de `AppShell.tsx` para compatibilidad de tests**:
   - *Causa*: `AppShellNavigation.test.tsx:53` asume estrictamente que `logout.parentElement.parentElement` es el elemento `<header>`. Envolver los controles de sesión en un contenedor intermedio `topBarActions` rompía esta aserción.
   - *Resolución*: Se eliminó el envoltorio intermedio y se ubicaron `.sessionControls` y `menuToggleButton` como hijos directos del `<header>`, aplicando `order` de CSS Flexbox para ordenar visualmente los elementos en móvil (marca primero, controles de sesión y menú en la misma fila a la derecha, navegación replegada o desplegada debajo a ancho completo).
3. **Orden de media queries en `AgendaGrid.module.css`**:
   - *Causa*: `agendaStyles.test.ts:102` realiza una búsqueda no codiciosa por regex (`/\.weekColumnHeader[^{]*\{([^}]*)\}/`) esperando encontrar la regla base con `var(--agenda-week-column-min-width)`. Al colocar la regla `@media (max-width: 640px)` al inicio del archivo, la regex capturaba la regla móvil en vez de la regla base.
   - *Resolución*: Se trasladó la media query `@media (max-width: 640px)` al pie del archivo, siguiendo las buenas prácticas de arquitectura CSS y manteniendo los tests preexistentes verdes.
4. **Advertencias preexistentes de ESLint**:
   - *Causa*: Existen 3 advertencias preexistentes heredadas de C-29 y C-30 (`AppointmentFormDialog.tsx:36` por exportar `buildStartAtIso` junto con el componente, y 2 en `Dialog.tsx` por el ref `returnFocusRef`).
   - *Resolución*: Dado que la regla dura del proyecto prohíbe modificar código o tests ajenos al change sin justificación estricta, estas advertencias se mantienen y documentan; `npx eslint .` finaliza con código 0 y 0 errores.
5. **Detección de foco en `AppShell.mobile.test.tsx` (M02)**:
   - *Causa*: En el test inicial de Escape, al abrir el menú mediante click, el botón Menú conservaba el foco activo en JSDOM, por lo que comentar el retorno de foco no hacía fallar el test.
   - *Resolución*: Se movió explícitamente el foco a un enlace dentro del menú (`screen.getByRole("link", { name: "Agenda" }).focus()`) antes de disparar la tecla `Escape`. Al pulsar Escape, se verifica que el foco regrese efectivamente al botón Menú, eliminando la mutación M02 estrictamente por aserción.

---

## Verificación Visual Multi-Resolución a cargo de Claude (Fase 7)

Checklist preparado para validación con capturas reales a 1440 px, 768 px y 390 px:

- [ ] 7.1 Tomar capturas reales a 1440 px, 768 px y 390 px de `AppShell` y Menú móvil desplegado.
- [ ] 7.2 Tomar capturas reales a 1440 px, 768 px y 390 px de `AgendaToolbar` compacta y panel de filtros.
- [ ] 7.3 Tomar capturas reales a 1440 px, 768 px y 390 px de `AgendaGrid` con scroll-snap en vista diaria y semanal.
- [ ] 7.4 Tomar capturas reales a 1440 px, 768 px y 390 px de los modales de turnos como hoja inferior sin botones cortados.
- [ ] 7.5 Consolidar capturas en `docs/evidencias/capturas/` y registrar enlaces definitivos.
