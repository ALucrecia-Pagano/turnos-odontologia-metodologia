# Verificación de C-36 — ui-tema-oscuro-y-movil

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 7 implementadas y verificadas según [tasks.md](../../openspec/changes/archive/2026-11-14-ui-tema-oscuro-y-movil/tasks.md); fase 7 (verificación visual multi-resolución a 1440 px, 768 px y 390 px) completada con 15 capturas reales en [capturas/](capturas/).
- **Vitest**: Línea base de **260 tests en 64 archivos**; suite final de **272 tests en 69 archivos**, todos en verde ([test-suite-C-36.txt](test-suite-C-36.txt)). Los 12 tests nuevos se encuentran en 5 archivos aislados (`AppShell.mobile.test.tsx`, `AgendaToolbar.mobile.test.tsx`, `AgendaGrid.mobile.test.tsx`, `Dialog.bottomSheet.test.tsx`, `AgendaSpacing.mobile.test.tsx`); cada uno cuenta con su par RED/GREEN documentado.
- **Mutaciones**: **12 de 12 mutaciones eliminadas** (M01–M12) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 sin cambios: sí** ([mutaciones-C-36.txt](mutaciones-C-36.txt), generado por [mutaciones-C-36.py](mutaciones-C-36.py)).
- **Trazabilidad**: **12 escenarios** declarados en specs delta (8 testeables 1:1 + 4 visuales a cargo de Claude), 0 inconsistencias ([trazabilidad-C-36.txt](trazabilidad-C-36.txt), generado por [trazabilidad-C-36.py](trazabilidad-C-36.py)).
- **Calidad y Tooling**:
  - `npx tsc --noEmit` exit 0 (0 errores de tipos).
  - `npx eslint .` exit 0 (0 errores, 3 advertencias preexistentes heredadas de C-29/C-30 documentadas en Desvíos; ver [tooling-C-36.txt](tooling-C-36.txt)).
  - `npm run build` exit 0 ([build-C-36.txt](build-C-36.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 con 18 elementos válidos (17 specs + 1 change activo; [validate-C-36.txt](validate-C-36.txt)).
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

## Tabla de Mutaciones (M01–M12)

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
| M09 | `AgendaGrid.mobile.test.tsx` | `09-grilla-columna-cqi` | ELIMINADA | `AssertionError: expected '.gridScrollContainer {\r\n  overflow-…' not to match /\.columnHeaderMobile[^{]*\{[^}]*100vw/` |
| M10 | `AgendaToolbar.mobile.test.tsx` | `10-toolbar-compacta-tres-filas` | ELIMINADA | `AssertionError: expected 'Anterior' to be '‹' // Object.is equality` |
| M11 | `AgendaSpacing.mobile.test.tsx` | `11-espaciado-agenda` | ELIMINADA | `AssertionError: expected '.agendaView {\r\n  display: flex;\r\n…' to match /\.headerBar\s*\{[^}]*margin-top:\s*va…/` |
| M12 | `AgendaGrid.mobile.test.tsx` | `12-grilla-horas-sticky-superficie-y-zindex` | ELIMINADA | `AssertionError: expected '.gridScrollContainer {\r\n  overflow-…' to match /@media\s*\(max-width:\s*640px\)[\s\S]…/` |
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
6. **Defectos detectados en captura real: columna cortada por cálculo con 100vw, toolbar en 4 filas, espaciado, tarjetas sobre la columna de horas al deslizar**:
   - *Columna cortada por cálculo con 100vw*: Al restar 64 px y padding de `2 * var(--space-4)` a `100vw`, no se consideraba el padding del PageShell y el borde, dando 294 px en lugar de 276 px (ancho útil real dentro de la grilla), cortando la columna 18 px e impidiendo que el snap mostrara una columna entera. Corregido aplicando `container-type: inline-size` a `.gridScrollContainer` (modo móvil) y dimensionando columnas con `calc(100cqi - var(--agenda-time-gutter-width, 64px))` suprimendo totalmente el cálculo con `100vw` (test 09 en `AgendaGrid.mobile.test.tsx`, mutación M09).
   - *Toolbar en 4 filas*: La toolbar en móvil ocupaba excesiva altura vertical y rompía controles. Corregido reestructurándola estrictamente en 3 filas: Fila 1 con [Día | Semana] + Anterior ('‹') + Hoy + Siguiente ('›') con `flex-wrap: nowrap` y preservación de los nombres accesibles ("Anterior" / "Siguiente"); Fila 2 con Fecha a ancho disponible + 'Nuevo turno'; Fila 3 con 'Filtros' + 'Actualizar agenda' ('↻'). Paddings y gaps compactados mediante tokens (test 10 en `AgendaToolbar.mobile.test.tsx`, mutación M10).
   - *Espaciado*: Había excesiva separación entre el título "Agenda diaria" y la toolbar, mientras que el encabezado de fecha ("miércoles 18 de noviembre de 2026") quedaba pegado al borde inferior de la toolbar. Corregido reduciendo el padding de `PageShell.module.css` mediante tokens (`var(--space-3)` en escritorio y `var(--space-2)` en móvil) y asignando `margin-top: var(--space-4)` a `.headerBar` en `AgendaView.module.css` (test 11 en `AgendaSpacing.mobile.test.tsx`, mutación M11).
   - *Tarjetas sobre la columna de horas al deslizar, detectado en captura real*: Al deslizar horizontalmente la grilla a 390 px, las tarjetas de las columnas anteriores se montaban por encima de la columna de horas fija (`timeGutter`), mostrando texto superpuesto (por ejemplo 'ervado' sobre '10:00'). Corregido asignando `z-index: 5` y background de superficie a `.timeGutter` (y `.timeGutterMobile`), y `z-index: 6` y background de superficie a `.cornerCell` (y `.cornerCellMobile`) en pantallas móviles (<= 640 px), manteniendo intacto el z-index base de escritorio (2 y 4) (test 12 en `AgendaGrid.mobile.test.tsx`, mutación M12).

---

## Verificación en navegador real (Claude)

Se validaron en navegador real (Chromium contra la API local de backend y frontend) todas las pantallas, componentes e interacciones visuales del change a 1440 px, 768 px y 390 px, con un total de 15 capturas en [capturas/](capturas/):

- **Navegación y cabecera (`AppShell`)**: en celular (390 px), cabecera compacta en una sola fila con marca a la izquierda y controles de sesión a la derecha; botón "Menú" fuera de `<nav>` con `aria-expanded` y `aria-controls="main-menu"`. Al pulsar despliega la navegación vertical a ancho completo; al presionar `Escape` el menú se cierra y el foco regresa al botón "Menú". Con el menú cerrado, los enlaces de la navegación no reciben foco mediante Tab (`inert`). En tablet (768 px) y escritorio (1440 px), la navegación permanece visible en línea sin botón de menú (`C-36-menu-abierto-390.png`, `C-36-agenda-dia-{1440,768,390}.png`).
- **Toolbar de agenda (`AgendaToolbar`)**: en celular (390 px), organizada estrictamente en 3 filas sin saltos indeseados:
  - Fila 1: selectores de vista `[Día | Semana]` + controles de navegación Anterior (`‹`), Hoy y Siguiente (`›`), conservando su nombre accesible intacto ("Anterior" / "Siguiente") para lectores de pantalla y tests;
  - Fila 2: fecha actual visible ocupando el ancho disponible junto al botón "Nuevo turno";
  - Fila 3: botón "Filtros" con contador de filtros activos en texto (`Filtros (1)`) y botón de refresco "Actualizar agenda" (`↻`), conservando su nombre accesible. En escritorio (1440 px) y tablet (768 px), la toolbar se mantiene en su distribución horizontal tradicional (`C-36-agenda-dia-390.png`, `C-36-filtros-abiertos-390.png`).
- **Grilla de turnos (`AgendaGrid`)**:
  - En celular (390 px), columnas de 292 px iguales al ancho útil real de la grilla (356 px - 64 px de eje horario) mediante container queries (`100cqi`), con desplazamiento horizontal fluido y `scroll-snap-type: x mandatory` que alinea exactamente una columna completa por paso, tanto en vista diaria por sillones como en vista semanal;
  - La columna fija del eje horario (`timeGutter` y `cornerCell`) cuenta con fondo de superficie sólido y `z-index` elevado, garantizando que al deslizar horizontalmente las tarjetas de la columna anterior no pasen por encima de las horas fijas (`C-36-agenda-dia-snap-390.png`, `C-36-agenda-semana-{1440,768,390}.png`).
- **Modales de turnos (`Dialog`)**:
  - En celular (390 px), se despliegan como hoja inferior (*bottom sheet*) a ancho completo (390 px), pegados al borde inferior de la pantalla con bordes superiores redondeados, scroll interno accesible y botones de acción a 44 px de altura mínima sin recortes;
  - En tablet (768 px) y escritorio (1440 px), se preserva el modal centrado flotante de 580 px con desenfoque marfil-hielo (`C-36-detalle-{1440,768,390}.png`, `C-36-nuevo-turno-{1440,768,390}.png`).
- **Adaptabilidad y desbordes**: `scrollWidth` exactamente igual al ancho de la ventana (`innerWidth`) en los tres anchos de pantalla (1440 px, 768 px y 390 px), sin desbordes horizontales globales en la ventana.
- **Escritorio intacto**: la interfaz de escritorio a 1440 px y tablet a 768 px no presenta alteraciones visuales ni regresiones funcionales respecto a C-30/C-35.

### Defectos encontrados y corregidos

1. **Columna cortada por cálculo con 100vw**: La regla original utilizaba `calc(100vw - 64px - 2 * var(--space-4)) = 294 px`, pero el ancho útil dentro de la grilla es 340 - 64 = 276 px (sin considerar padding y borde de la página). La columna quedaba cortada 18 px y el snap no mostraba una columna entera. Se corrigió estableciendo `container-type: inline-size` en `.gridScrollContainer` y dimensionando las columnas con `calc(100cqi - var(--agenda-time-gutter-width, 64px))`, eliminando `100vw`.
2. **Toolbar en 4 filas**: La distribución anterior en móvil colapsaba en 4 filas desordenadas. Se reestructuró en 3 filas compactas: Fila 1 (navegación y vistas), Fila 2 (fecha y nuevo turno), Fila 3 (filtros y actualizar) con botones compactos "‹", "›" y "↻" que preservan su nombre accesible.
3. **Espaciado de la página**: Exceso de separación vertical entre título y toolbar y falta de margen sobre la fecha. Se compactaron los paddings de `PageShell.module.css` con tokens (`var(--space-2)` en móvil) y se agregó margen superior a la barra de fecha en `AgendaView.module.css`.
4. **Tarjetas sobre la columna de horas al deslizar**: Al scrollear horizontalmente, las tarjetas de las columnas anteriores se montaban sobre el eje de horas. Se asignó fondo de superficie y `z-index: 5` a `.timeGutter` y `z-index: 6` a `.cornerCell` en móvil.

> **Nota sobre historial Git**: El archivo `docs/evidencias/explore-C-31.md` entró por error en el commit `1e1d7f9` de C-36; es evidencia de C-31 y no afecta a este change.
