# Exploración C-36: Adaptabilidad Móvil de la Aplicación y Tema Oscuro (`ui-tema-oscuro-y-movil`)

> **Fecha**: 2026-11-14  
> **Rama**: `main` (commit `59ddd2e`)  
> **Estado previo**: C-29, C-30 y C-35 archivados y sincronizados.  
> **Modo**: Solo lectura del código base y diseño previo; único archivo redactado: `docs/evidencias/explore-C-36.md`.  
> **Skills y MCPs consultados**:  
> - **Skill `appointment-frontend-ux`** (`.agents/skills/appointment-frontend-ux/SKILL.md`): consultada exhaustivamente en cuanto a versiones exactas (React 18.3.1, React Router 6.30.6, Vite 5, Vitest 3, jsdom 31.0.0), regla C1 de tests (sin mocks de módulo, `fetch` y `Clock` inyectados, sin fake timers), confinamiento de tokens en `tokens.css`, accesibilidad (estados con texto visible, contraste AA), prioridad de hora/paciente sobre estado en tarjetas angostas (< 260 px), zona horaria desde la API y verificación visual obligatoria a 1440 px, 768 px y 390 px antes de archivar.  
> - **MCP Context7**: **No fue necesario consultar librerías externas** en esta exploración, ya que las primitivas requeridas (React Router DOM v6, `<dialog>` nativo, CSS Grid/Flexbox/Container Queries) ya están completamente estandarizadas y probadas en el repositorio.

---

## 0. Contexto y Justificación del Reenfoque

El alcance original redactado en [CHANGES.md](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/CHANGES.md#L687-L701) §C-36 incluía:
> *"Responsive para celular de la portada y del diálogo de acceso: hero, secciones, equipo, contacto y formulario legibles y sin overflow horizontal a 390 px."*

Sin embargo, la inspección de los artefactos de C-35 y las capturas reales demuestra que:
1. **La portada pública, la página de acceso y el diálogo de login ya están 100% resueltos y verificados para móvil a 390 px** en C-35:
   - [docs/evidencias/capturas/C-35-portada-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-portada-390.png): Navegación "Inicio / La clínica / Acceder" sin saltos ni desborde, logo centrado, overlay y tipografía adaptados, sin scroll horizontal.
   - [docs/evidencias/capturas/C-35-acceso-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-acceso-390.png): Tres tarjetas de roles apiladas en columna única con espaciado limpio.
   - [docs/evidencias/capturas/C-35-login-recepcion-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-login-recepcion-390.png): Formulario de acceso en tarjeta translúcida, inputs legibles, sin desbordes.
   - Además, la portada y el login **ya son oscuros** por diseño (paleta Aqua Navy `#011C40`, `#023859`, Ice `#A7EBF2`, Accent `#54ACBF`).
2. **Lo que actualmente falla en celular a 390 px es la APLICACIÓN AUTENTICADA DE LA AGENDA**, tal como se comprueba en las capturas reales:
   - [docs/evidencias/capturas/C-35-agenda-nav-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-390.png): La barra superior (`AppShell`) se quiebra en 3 renglones verticales, el menú de navegación queda truncado con scroll horizontal oculto ("Cá... Próx..."), la toolbar de agenda ocupa más de 280 px (5 renglones de botones e inputs), y la grilla corta las columnas de profesionales a la mitad.
   - [docs/evidencias/capturas/C-30-detalle-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-30-detalle-390.png): El modal de detalle del turno flota centrado con doble margen, y la barra de 4 acciones apiladas a 44 px provoca que el botón inferior ("Cancelar turno") quede cortado por el borde de la pantalla.
   - [docs/evidencias/capturas/C-29-form-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-29-form-390.png): El diálogo "Nuevo turno" aparece como tarjeta flotante reducida (310 px de ancho útil), revelando detrás la grilla cortada.
3. **Existencia de "Leer antes" de C-36**:
   - `docs/evidencias/explore-portada-y-acceso.md`: **SÍ existe** en el repositorio.
   - `openspec/changes/archive/2026-11-13-ui-portada-y-acceso/design.md`: **SÍ existe** (D4 sobre modales claros suaves, D5 sobre AppShell sin cajas, D7 sobre rutas).
   - Componente `AgendaWeekGrid.tsx`: **NO existe** en el árbol de código (la vista semanal se implementó reutilizando `AgendaGrid.tsx` y `groupByDayForProfessional`).
   - Ubicación de modales de turnos: viven en `frontend/src/features/appointments/` (no en `frontend/src/features/agenda/appointments/`).

**Conclusión y propuesta de reenfoque**:
C-36 debe centrarse prioritariamente en la **adaptabilidad móvil de la aplicación web** (la agenda operativa de uso diario en tablet y celular para recepción y odontólogos), tratando el **tema oscuro de la app** como segunda parte (modular o recortable).

---

## 1. Diagnóstico de la Aplicación a 390 px y 768 px

### 1.1 Barra Principal de Navegación (`AppShell`)
* Archivos reales:
  - Componente: [frontend/src/shared/components/AppShell.tsx:24-69](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.tsx#L24-L69)
  - Estilos: [frontend/src/shared/components/AppShell.module.css:10-20](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L10-L20) y [AppShell.module.css:194-227](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L194-L227)
  - Evidencia visual: [C-35-agenda-nav-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-390.png) vs [C-35-agenda-nav-768.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-768.png)

* **Comportamiento en Tablet (768 px)**:
  - En `AppShell.module.css:194-210`, `.topBar` tiene `justify-content: space-between;`.
  - La marca (`.brand`, orden 1) y los controles de sesión (`.sessionControls`, orden 2) comparten limpiamente el renglón 1.
  - La navegación (`.nav`, orden 3) ocupa el renglón 2 (`width: 100%`) y en 768 px todos los ítems ("Agenda", "Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes") entran sin desbordar.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. `.topBar` tiene `padding: var(--space-3) var(--space-6)` ([AppShell.module.css:17](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L17)), donde `--space-6` es 32 px. Con 32 px a izquierda y derecha, se consumen 64 px solo en márgenes internos, dejando únicamente 326 px de ancho disponible.
    2. En ese espacio de 326 px, `.brand` mide ~100 px, pero `.sessionControls` ([AppShell.module.css:133-137](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L133-L137)) contiene el nombre del usuario ("Recepción Demo", ~115 px) más una brecha de 12 px más el botón "Cerrar sesión" (~110 px con padding y bordes). La suma supera los 326 px.
    3. Al tener `flex-wrap: wrap` ([AppShell.module.css:12](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L12)), `.sessionControls` baja a un **segundo renglón**.
    4. `.nav` ([AppShell.module.css:211-218](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/AppShell.module.css#L211-L218)) baja a un **tercer renglón** con `overflow-x: auto; flex-wrap: nowrap;`.
    5. Como se observa en la captura real `C-35-agenda-nav-390.png`, la barra consume ~140 px de altura en tres renglones apelotonados, y la navegación horizontal se corta en "Cá... Próx..." sin ninguna pista visual de que continúa hacia la derecha.

---

### 1.2 Barra de Herramientas de la Agenda (`AgendaToolbar`)
* Archivos reales:
  - Componente: [frontend/src/features/agenda/AgendaToolbar.tsx:71-213](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaToolbar.tsx#L71-L213)
  - Estilos: [frontend/src/features/agenda/AgendaToolbar.module.css:1-32](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaToolbar.module.css#L1-L32)
  - Evidencia visual: [C-35-agenda-nav-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-390.png) vs [C-35-agenda-nav-768.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-768.png)

* **Comportamiento en Tablet (768 px)**:
  - Los controles se ordenan en 3 renglones: navegación y vista en renglón 1, botón "Nuevo turno" en renglón 2, y filtros de profesional y sillón en renglón 3. Ocupa unos 170 px de altura.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. En `AgendaToolbar.module.css`, **no existe ninguna regla responsive `@media`**.
    2. `.controlsRow`, `.navGroup` y `.filterGroup` tienen `display: flex; flex-wrap: wrap;` ([AgendaToolbar.module.css:11-31](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaToolbar.module.css#L11-L31)).
    3. Todos los botones e inputs imponen `min-height: 44px; min-width: 44px;` por accesibilidad táctil ([AgendaToolbar.module.css:48-49](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaToolbar.module.css#L48-L49)).
    4. En 390 px de pantalla (342 px dentro del contenedor principal), los elementos se quiebran en **5 renglones distintos**:
       - Renglón 1: Toggle [Día | Semana] (130 px), botón [Anterior] (80 px), botón [Hoy] (60 px).
       - Renglón 2: Botón [Siguiente] (85 px), campo Fecha [YYYY-MM-DD] (150 px).
       - Renglón 3: Botón [Actualizar agenda] (140 px), botón [Nuevo turno] (115 px).
       - Renglón 4: Select Profesional [Todos ▾] (150 px), Select Sillón [Todos ▾] (120 px).
       - Renglón 5: Botón [Limpiar filtros] (120 px).
    5. Sumado al título `PageShell` y al encabezado de fecha (`AgendaView.tsx`), **la toolbar ocupa más del 60% del alto visible de la pantalla**, empujando la grilla de turnos por debajo del pliegue.

---

### 1.3 Grilla de Turnos en Modo Diario (`AgendaGrid`)
* Archivos reales:
  - Componente: [frontend/src/features/agenda/AgendaGrid.tsx:52-100](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaGrid.tsx#L52-L100)
  - Estilos: [frontend/src/features/agenda/AgendaGrid.module.css:23-53,98-105](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaGrid.module.css#L23-L53)
  - Tokens: [frontend/src/shared/styles/tokens.css:83-85](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/styles/tokens.css#L83-L85)
  - Evidencia visual: [C-35-agenda-nav-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-agenda-nav-390.png) vs [C-27-tablet.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-27-tablet.png)

* **Comportamiento en Tablet (768 px)**:
  - El canal horario (`timeGutter`) mide 64 px (`--agenda-time-gutter-width`).
  - Las 3 columnas de profesionales miden 220 px cada una (`--agenda-column-min-width: 220px`).
  - Ancho total: 64 px + (3 × 220 px) = 724 px. Entra en 768 px con mínimo margen lateral.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. Ancho disponible en pantalla móvil: 390 px − 48 px (padding de `PageShell.module.css:25`) = 342 px.
    2. El gutter fijo de horas consume 64 px.
    3. La columna 1 ("Dr. Martín Sosa") consume 220 px.
    4. 64 px + 220 px = 284 px. Quedan solo 58 px de ancho visible.
    5. La columna 2 ("Dra. Laura Quiroga") queda **mutilada** (se lee solo "Dra. La..."), y la columna 3 queda totalmente oculta a la derecha.
    6. Aunque `.gridScrollContainer` tiene `overflow-x: auto;` y la columna de horas es `position: sticky; left: 0;` ([AgendaGrid.module.css:78](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaGrid.module.css#L78)), el desplazamiento bidimensional (scrollear horizontalmente para ver profesionales y verticalmente para ver las horas) resulta incómodo y desorientador en pantallas táctiles pequeñas.

---

### 1.4 Grilla de Turnos en Modo Semanal (`AgendaGrid` en modo semana)
* Archivos reales:
  - Componente: [frontend/src/features/agenda/AgendaGrid.tsx:55-68,97-110](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaGrid.tsx#L55-L68) (Nota: no existe `AgendaWeekGrid.tsx`, se gestiona mediante la prop `isWeek` o `view="week"`).
  - Estilos: [frontend/src/features/agenda/AgendaGrid.module.css:55-59,107-110](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaGrid.module.css#L55-L59)
  - Tokens: [frontend/src/shared/styles/tokens.css:86](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/styles/tokens.css#L86) (`--agenda-week-column-min-width: 140px`)
  - Evidencia visual: [C-28-semana.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-28-semana.png) vs [C-28-tablet.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-28-tablet.png)

* **Comportamiento en Tablet (768 px)**:
  - 64 px + (7 días × 140 px) = 1044 px. Requiere scroll horizontal, pero en 768 px se visualizan entre 4 y 5 días simultáneamente.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. 64 px de gutter + 140 px del lunes = 204 px.
    2. En 342 px útiles, el martes se corta a mitad de columna (138 px visibles) y 5 días de la semana quedan fuera de la pantalla.
    3. Combinado con un alto de grilla de 1344 px (12 horas × 112 px), navegar 7 columnas semanales en un teléfono genera frustración visual severa.

---

### 1.5 Vista de Lista Accesible (`AgendaTable`)
* Archivos reales:
  - Componente: [frontend/src/features/agenda/AgendaTable.tsx:51-85](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaTable.tsx#L51-L85)
  - Estilos: [frontend/src/features/agenda/AgendaTable.module.css:1-38](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaTable.module.css#L1-L38)
  - Evidencia visual: [C-27-lista.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-27-lista.png)

* **Comportamiento en Tablet (768 px)**:
  - La tabla semántica de 7 u 8 columnas (Fecha, Hora, Paciente, Profesional, Sillón, Prestación, Estado, Acción) entra cómodamente o con mínimo desplazamiento.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. La tabla requiere un ancho mínimo intrínseco de más de 650 px para desplegar los 7 encabezados sin quebrar palabras.
    2. `.tableContainer` tiene `overflow-x: auto;` ([AgendaTable.module.css:2](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/agenda/AgendaTable.module.css#L2)), lo que evita que rompa la pantalla, pero obliga a hacer scroll horizontal dentro de la tabla para ver el profesional, el sillón, el estado o el botón "Ver turno".

---

### 1.6 Diálogos Modales de Turnos (`Dialog` y componentes de `appointments`)
* Archivos reales:
  - Primitiva: [frontend/src/shared/components/Dialog.tsx:100-110](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/Dialog.tsx#L100-L110) y [Dialog.module.css:19-26](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/Dialog.module.css#L19-L26)
  - Diálogo de alta: [frontend/src/features/appointments/AppointmentFormDialog.tsx](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentFormDialog.tsx) y [AppointmentFormDialog.module.css:1-18,181-194](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentFormDialog.module.css#L1-L18)
  - Diálogo de detalle: [frontend/src/features/appointments/AppointmentDetailDialog.tsx](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentDetailDialog.tsx) y [AppointmentDetailDialog.module.css:1-18,214-229](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentDetailDialog.module.css#L1-L18)
  - Diálogo de reprogramación: [frontend/src/features/appointments/AppointmentRescheduleDialog.tsx](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentRescheduleDialog.tsx) y [AppointmentRescheduleDialog.module.css:1-18,206-223](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentRescheduleDialog.module.css#L1-L18)
  - Evidencia visual: [C-30-detalle-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-30-detalle-390.png), [C-29-form-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-29-form-390.png) y [C-35-modal-detalle-390.png](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/docs/evidencias/capturas/C-35-modal-detalle-390.png)

* **Comportamiento en Tablet (768 px)**:
  - Los diálogos flotan centrados con ancho máximo de 580 px, tarjeta con borde fino y backdrop desenfocado. Funcionamiento óptimo.

* **Comportamiento en Celular (390 px)**:
  - **Causa en CSS/Markup**:
    1. `.dialog[open]` impone `padding: var(--space-4);` (16 px en los cuatro bordes) y `align-items: safe center;` ([Dialog.module.css:19-26](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/Dialog.module.css#L19-L26)).
    2. El contenedor interior impone `padding: var(--space-5);` (24 px) y bordes redondeados cerrados ([AppointmentDetailDialog.module.css:13](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentDetailDialog.module.css#L13)).
    3. Ancho útil interior: 390 px − (2 × 16 px) − (2 × 24 px) = **310 px**.
    4. En `AppointmentDetailDialog`, la sección de acciones (`.actionsBar`) apila verticalmente hasta 4 botones ("Marcar atendido", "Marcar ausente", "Reprogramar", "Cancelar turno"), cada uno con `min-height: 44px` y brecha ([AppointmentDetailDialog.module.css:221-228](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/features/appointments/AppointmentDetailDialog.module.css#L221-L228)). Esto suma más de 200 px solo para las acciones.
    5. Como se observa en la captura real `C-30-detalle-390.png`, la tarjeta excede la altura visible y el botón "Cancelar turno" queda **cortado por el borde inferior de la pantalla**, requiriendo scroll interno forzado dentro de una caja flotante angosta.

---

## 2. Dependencias de Tests Existentes (Intocables)

Para respetar la **Regla C1** y la restricción estricta de **no modificar tests existentes**, analizamos qué contratos de DOM y selectores asumen los tests actuales:

| Archivo de test existente | Selector / Aserción estricta que NO debe romperse | Impacto en la solución de C-36 |
|---|---|---|
| `frontend/src/shared/components/AppShell.test.tsx` (L67–79) | `const adminButtons = within(nav).getAllByRole("button");`<br>`expect(adminButtons).toHaveLength(5);`<br>`expect(btn.getAttribute("data-menu-item"))` | **CRÍTICO**: Ningún botón nuevo (por ej. botón hamburguesa o toggle "Menú") puede colocarse **DENTRO** del `<nav aria-label="Menú principal">`. Si se crea un botón de apertura, debe residir en el `<header>` fuera de `<nav>`. |
| `frontend/src/shared/components/AppShell.test.tsx` (L62, 101, 127) | `within(nav).queryByRole("link", { name: "Agenda" })`<br>4 botones para recepción y 3 para odontólogo en `within(nav)` | Todos los enlaces y botones deshabilitados ("Próximamente") deben seguir existiendo en el DOM dentro de `<nav>`. En jsdom no se debe ocultar el `<nav>` con `display: none` incondicional sin clase. |
| `frontend/src/shared/components/AppShell.test.tsx` (L80, 175, 182) | `screen.queryByText("Administrador Demo")`<br>`screen.queryByRole("alert")` | El nombre de usuario y el banner de alerta de sesión / error 403 deben conservar sus textos y roles semánticos. |
| `frontend/src/features/auth/menuFor.test.ts` (L1–59) | Pruebas de lógica pura de los ítems por rol | Sin impacto en UI; no interactúa con el DOM. |
| `frontend/src/features/agenda/AgendaToolbar.test.tsx` (L49–52, 99, 129–137) | `screen.queryByLabelText("Profesional")`<br>`screen.queryByLabelText("Sillón")`<br>`screen.queryByRole("button", { name: "Limpiar filtros" })`<br>`screen.queryByRole("button", { name: "Día" })`<br>`screen.queryByRole("button", { name: "Semana" })`<br>`screen.queryByRole("button", { name: "Anterior" })` | **CRÍTICO**: Los selectores y botones deben estar presentes y accesibles en el DOM por defecto. Si los filtros se hacen colapsables en móvil, en el entorno de pruebas de escritorio / jsdom deben permanecer desplegados o ser consultables sin romper estos tests. |
| `frontend/src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx` (L39) | `screen.queryByRole("button", { name: "Nuevo turno" })` | El botón "Nuevo turno" debe conservar su nombre accesible exacto y su visibilidad según el rol. |
| `frontend/src/features/agenda/AgendaView.test.tsx` (L94–100+) | `screen.getByTestId("agenda-grid-scroll")`<br>`screen.getAllByTestId("agenda-column-header")`<br>`screen.getByTestId("agenda-time-gutter")`<br>`screen.getAllByTestId("agenda-axis-hour")`<br>`screen.getByRole("button", { name: "Ver como lista" })` | **CRÍTICO**: `AgendaView` **NO debe cambiar su modo por defecto a "list" de forma incondicional**, porque rompería decenas de pruebas que esperan encontrar `AgendaGrid` (`agenda-grid-scroll`). Cualquier adaptación a lista debe ser mediante viewport CSS o inyección explícita sin alterar el default `"grid"`. |
| `frontend/src/features/agenda/AgendaGrid.accionable.test.tsx` (L59–65) | `screen.getByTestId("agenda-appointment-...")`<br>espera `tagName === "BUTTON"`, `type="button"` y `aria-label` completo | Las tarjetas de turnos deben seguir siendo botones con el formato de `aria-label` auditado en C-27 y C-30. |
| `frontend/src/features/agenda/AgendaTable.test.tsx` (L47–63) | `screen.queryByRole("table")`<br>`within(table).queryAllByRole("columnheader")` con `scope="col"` | La estructura de la tabla accesible no debe alterarse. |
| `frontend/src/shared/components/Dialog.test.tsx` (L1–70) | `<dialog>` nativo, `aria-labelledby`, atributo `open`, evento `Escape` y retorno de foco | Las propiedades del diálogo modal deben mantenerse 100% compatibles. |
| `frontend/src/features/appointments/Appointment*.test.tsx` | Verificación de campos, selectores, errores de validación, badges y transiciones de estado | Los formularios y el modal de detalle conservan todos sus identificadores y jerarquía de accesibilidad. |

---

## 3. Decisiones de Diseño y Arquitectura

A continuación se presentan todas las decisiones numeradas (`D1` a `D6`), con sus opciones analizadas y la recomendación técnica por defecto:

### D1 — Alcance y Reenfoque de C-36
* **Contexto**: Como se demostró, la portada y el acceso ya son responsive y oscuros en C-35. La agenda autenticada es la que requiere adaptación urgente a celular.
* **Opciones**:
  - **Opción A (Recomendada)**: Reenfocar C-36 en la **adaptabilidad móvil completa de la aplicación** (AppShell, Toolbar, Grilla/Lista, Modales) como núcleo indispensable (Fase 1 a 4), y estructurar el **Tema Oscuro de la app** como segunda parte modular/recortable (Fase 5 y 6).
  - **Opción B**: Excluir el tema oscuro completamente de C-36 y enviarlo al backlog o a un C-37 posterior, dejando C-36 dedicado exclusivamente a "ui-movil-app".
  - **Opción C**: Mantener tema oscuro y móvil de la app al mismo nivel de alcance.
* **Recomendación**: **Opción A**. Permite resolver el problema funcional real de la agenda en celular sin renunciar a la promesa de tema oscuro de CHANGES.md, dejándolo claramente delimitado como una fase que no bloquea la entrega si los tiempos aprietan.

---

### D2 — Barra Superior en Celular (`AppShell`)
* **Contexto**: En 390 px, la barra se descompone en 3 renglones verticales y el menú queda truncado horizontalmente.
* **Opciones**:
  - **Opción A**: Barra de una sola fila compacta con botón "Menú" accesible (`aria-expanded`, `aria-controls="main-menu"`), que despliega un cajón lateral (drawer) o menú desplegable sobre la pantalla con fondo Aqua Navy, foco atrapado y tecla Escape.
  - **Opción B (Recomendada)**: Reorganización en dos filas estrictas y elegantes mediante CSS y botón "Menú" opcional:
    - *Fila 1 (Cabecera fija)*: Marca Aqua compacta a la izquierda; controles de sesión ("Recepción Demo" atenuado + botón icono/compacto "Cerrar sesión") y botón toggle "Menú" a la derecha.
    - *Fila 2 (Navegación móvil)*: En móvil `<= 768px`, el `<nav>` se presenta como panel colapsable o barra con scroll táctil mejorado (`-webkit-overflow-scrolling: touch; scroll-padding: var(--space-3); mask-image: linear-gradient(...)` para indicar desvanecimiento en los bordes).
    - Para no romper `AppShell.test.tsx` (que hace `within(nav).getAllByRole("button")` y espera 5 botones): el botón "Menú" se ubica en el `<header>` **fuera de `<nav>`**, y en tests de escritorio o por defecto `<nav>` permanece visible en el DOM.
  - **Opción C**: Barra de navegación fija en la parte inferior de la pantalla (Bottom Navigation Bar) con iconos.
* **Recomendación**: **Opción B** con menú desplegable accesible. Garantiza que en celular la barra ocupe solo 56 px de altura, despejando la pantalla, mientras el menú se abre a pantalla completa o modal táctil al pulsar "Menú".

---

### D3 — Barra de Herramientas de la Agenda (`AgendaToolbar`)
* **Contexto**: En 390 px, los 10 controles ocupan 5 renglones y más de 280 px de altura.
* **Opciones**:
  - **Opción A (Recomendada)**: Compactación en dos bloques organizados y filtros plegables:
    - *Bloque 1 (Navegación principal)*: Toggle [Día | Semana] + Flechas compactas [◀ | Hoy | ▶] + Botón prominente [Nuevo turno] en dos líneas limpias.
    - *Bloque 2 (Fecha y Filtros)*: Selector nativo de fecha junto a un botón toggle `[Filtros]` que incluye un indicador si hay filtros activos (`chairId` o `professionalId`). Al presionar `[Filtros]`, se despliegan Profesional, Sillón y [Limpiar filtros].
    - *Compatibilidad con tests*: En el DOM, los `<select>` de Profesional y Sillón están siempre presentes. En escritorio / jsdom el bloque de filtros se muestra expandido (`display: flex`), garantizando que `AgendaToolbar.test.tsx` siga pasando sin alterar los tests.
  - **Opción B**: Solo compactación por CSS (reducir paddings y gaps a `--space-1` y `--space-2`), manteniendo los 5 renglones visibles pero con altura de 180 px.
  - **Opción C**: Mover el botón [Nuevo turno] a un botón flotante (FAB) en la esquina inferior derecha.
* **Recomendación**: **Opción A**. Reduce la altura ocupada en móvil a menos de 110 px y le da al usuario control sobre si desea ver u ocultar los filtros de sillón y profesional.

---

### D4 — Grilla y Visualización de Turnos en Celular (`AgendaGrid` / `AgendaTable`)
* **Contexto**: A 390 px, la grilla diaria muestra solo 1.25 columnas de profesionales, y la semanal muestra solo 1.5 días.
* **Opciones**:
  - **Opción A (Recomendada)**: Grilla móvil optimizada con desplazamiento asistido y selector rápido de profesional:
    - *En Modo Día*: Añadir un selector por pestañas o chip horizontal (`[Dr. Sosa] [Dra. Quiroga] [Dra. Benítez]`) en móvil que permite centrar/desplazar la columna correspondiente con `scroll-into-view` o `scroll-snap-type: x mandatory`, manteniendo la columna de horas `position: sticky; left: 0;` con sombra suave.
    - *En Modo Semana*: `scroll-snap-type: x mandatory` por día para que cada día ocupe un ancho cómodo (~160 px) y encaje limpiamente al deslizar.
    - Mantener el botón prominente "Ver como lista" en el encabezado de `AgendaView` para quienes prefieran la lectura secuencial de turnos.
  - **Opción B**: Forzar automáticamente la vista de lista (`AgendaTable`) por defecto cuando el ancho es `<= 480px`.
    - *Problema*: Como jsdom no evalúa media queries y la Regla C1 prohíbe `vi.mock` o `window.matchMedia` no inyectado, cambiar el default rompería decenas de pruebas de `AgendaView.test.tsx` que esperan `agenda-grid-scroll`.
  - **Opción C**: Reducir el ancho mínimo de columna a 100 px para forzar que entren 3 columnas en 390 px.
    - *Problema*: Las tarjetas de turno quedarían completamente ilegibles, violando la regla de accesibilidad de la skill `appointment-frontend-ux` (la hora y el paciente deben leerse claramente).
* **Recomendación**: **Opción A**. Preserva el valor visual de la grilla de turnos (identificación inmediata de solapamientos, horas libres y bloqueos), resuelve el desplazamiento con `scroll-snap` táctil fluido, y mantiene los tests existentes 100% intactos.

---

### D5 — Diálogos Modales en Celular (`Dialog` como Bottom Sheet)
* **Contexto**: A 390 px, los modales flotantes centrados sufren de compresión horizontal (310 px útiles) y desborde vertical que corta botones de acción (`C-30-detalle-390.png`).
* **Opciones**:
  - **Opción A (Recomendada)**: Hoja inferior accesible (Bottom Sheet) en pantallas móviles (`@media (max-width: 768px)`):
    - En móvil, el `<dialog>` ancla el contenido en la parte inferior (`align-items: flex-end; padding: 0;`).
    - El contenedor ocupa el 100% del ancho (`width: 100%; max-width: 100%; border-radius: var(--radius-lg) var(--radius-lg) 0 0;`).
    - Altura máxima: `max-height: 90dvh; overflow-y: auto;`.
    - Tirador visual accesible superior (drag handle / pill indicador) y barra de acciones inferior fija o con scroll ergonómico.
    - En escritorio (> 768 px), se mantiene intacto como modal centrado de 580 px con bordes redondeados completos.
  - **Opción B**: Mantener el modal centrado pero achicar paddings exteriores e interiores (de 16 px y 24 px a 8 px y 12 px).
* **Recomendación**: **Opción A**. La hoja inferior es el estándar de oro en aplicaciones móviles web (ergonomía táctil para el pulgar, máximo ancho disponible sin desperdicio de márgenes, y cierre natural hacia abajo o con botón accesible).

---

### D6 — Tema Oscuro de la Aplicación
* **Contexto**: Portada y login ya son oscuros. La app autenticada usa superficies claras (`--color-background: #F3F7FA`, `--color-surface: #FFFFFF`).
* **Opciones**:
  - **Opción A (Recomendada si se incluye)**: Tema oscuro con tokens dedicados, detección automática por `prefers-color-scheme: dark` y alternancia manual mediante botón en `AppShell` **sin persistencia** (según requerimiento de CHANGES.md §C-36):
    - Se definen tokens semánticos en `tokens.css` bajo `:root[data-theme="dark"]` y `@media (prefers-color-scheme: dark)`:
      - `--color-background: #011C40;` (Navy deep)
      - `--color-surface: #023859;` (Navy intermedio)
      - `--color-text: #F3F7FA;` (Ivory ice)
      - `--color-text-muted: #A7EBF2;` (Ice)
      - `--color-border: rgba(167, 235, 242, 0.22);`
      - Superficies de agenda: `--agenda-working-bg: #023859;`, `--agenda-offhours-bg: #011C40;`, `--agenda-grid-line: rgba(167, 235, 242, 0.15);`
    - Contraste AA garantizado en textos (ratios > 7:1) y en los 5 estados de `StatusBadge`.
    - Botón "Cambiar tema" en `AppShell` (en `sessionControls` o cabecera), que alterna el atributo `data-theme` en memoria en el elemento raíz sin escribir en `localStorage` ni cookies.
  - **Opción B**: Solo soporte automático por CSS con `@media (prefers-color-scheme: dark)` sin botón manual ni estado React.
  - **Opción C**: Recortar tema oscuro de la app y declararlo completado con la portada/login oscuros de C-35.
* **Recomendación**: **Opción A**. Cumple de forma limpia y rigurosa la especificación de C-36 en CHANGES.md, garantiza accesibilidad AA, y se implementa como la fase final de C-36 una vez asegurada la adaptabilidad móvil.

---

## 4. Escenarios Propuestos por Requisito (Dado / Cuando / Entonces)

### Requisito 1: Adaptabilidad de la Barra Principal (`AppShell`) en Pantallas Angostas
* **Escenario 1.1 (Móvil — Cabecera compacta a 390 px)**:
  - **Dado** que un usuario autenticado accede a la aplicación con un viewport móvil de 390 px,
  - **Cuando** se renderiza la cabecera `AppShell`,
  - **Entonces** la marca Aqua y los controles de sesión se ajustan en la cabecera sin saltos desordenados de 3 renglones, y el botón toggle "Menú" expone `aria-expanded="false"` y `aria-controls="main-menu"`.
* **Escenario 1.2 (Móvil — Apertura y cierre accesible del menú)**:
  - **Dado** que el menú móvil está cerrado (`aria-expanded="false"`),
  - **Cuando** el usuario activa el botón "Menú",
  - **Entonces** el menú se despliega exponiendo `aria-expanded="true"`, el foco se traslada al primer elemento interactivo ("Agenda"), y al presionar la tecla `Escape` el menú se cierra devolviendo el foco al botón "Menú".
* **Escenario 1.3 (Regresión — Estructura semántica intacta en escritorio)**:
  - **Dado** un entorno de prueba estándar o de escritorio,
  - **Cuando** se monta `AppShell`,
  - **Entonces** `<nav aria-label="Menú principal">` contiene exactamente los enlaces y botones esperados por `AppShell.test.tsx` sin nuevos botones en su interior.

### Requisito 2: Barra de Herramientas de Agenda (`AgendaToolbar`) Compacta en Móvil
* **Escenario 2.1 (Móvil — Agrupación ergonómica de navegación y fecha)**:
  - **Dado** que la agenda se visualiza en un viewport móvil de 390 px,
  - **Cuando** se renderiza `AgendaToolbar`,
  - **Entonces** los controles de cambio de vista [Día | Semana] y navegación temporal se agrupan en una botonera compacta contigua, y el selector de fecha ocupa una fila dedicada accesible con altura mínima de 44 px.
* **Escenario 2.2 (Móvil — Despliegue de filtros secundarios)**:
  - **Dado** que el usuario desea filtrar por profesional o sillón en celular,
  - **Cuando** pulsa el botón accesible "Filtros",
  - **Entonces** se despliegan los selectores de "Profesional", "Sillón" y el botón "Limpiar filtros" sin empujar el contenido de la grilla de forma desmedida.
* **Escenario 2.3 (Borde — Indicador de filtros activos)**:
  - **Dado** que hay un filtro activo (por ej. `chairId` o `professionalId`),
  - **Cuando** la sección de filtros está colapsada en móvil,
  - **Entonces** el botón "Filtros" muestra un distintivo visual y accesible de que hay filtros aplicados.

### Requisito 3: Navegación y Grilla de Turnos en Móvil (`AgendaGrid`)
* **Escenario 3.1 (Móvil diario — Columna de horas sticky y scroll horizontal asistido)**:
  - **Dado** que se muestran 3 profesionales en la agenda diaria a 390 px,
  - **Cuando** el usuario se desplaza horizontalmente por la grilla,
  - **Entonces** la columna de horas (`timeGutter`) permanece fija a la izquierda (`position: sticky`), las columnas de profesionales se alinean mediante `scroll-snap`, y las tarjetas de turno mantienen visibles la hora y el paciente con prioridad.
* **Escenario 3.2 (Móvil semanal — Desplazamiento por días en semana)**:
  - **Dado** que la agenda está en modo semanal a 390 px,
  - **Cuando** se visualizan los 7 días de la semana,
  - **Entonces** cada día se presenta con un ancho mínimo cómodo (~160 px) permitiendo deslizar de día en día con encaje magnético (`scroll-snap`), visualizando claramente el indicador del día actual ("Hoy").
* **Escenario 3.3 (Alternancia a lista)**:
  - **Dado** que el usuario en móvil prefiere una vista vertical continua,
  - **Cuando** pulsa el botón "Ver como lista",
  - **Entonces** se monta `AgendaTable` en formato accesible permitiendo consultar los turnos cronológicamente y acceder a "Ver turno".

### Requisito 4: Modales de Turnos como Hoja Inferior (Bottom Sheet) en Móvil
* **Escenario 4.1 (Móvil — Presentación como Bottom Sheet)**:
  - **Dado** que se abre `AppointmentDetailDialog`, `AppointmentFormDialog` o `AppointmentRescheduleDialog` en un viewport `<= 768px`,
  - **Cuando** el diálogo pasa a estado `open`,
  - **Entonces** el contenedor se ancla en la parte inferior de la pantalla a ancho completo (100%), con esquinas superiores redondeadas, altura máxima de 90dvh y scroll vertical interno.
* **Escenario 4.2 (Móvil — Visibilidad de botones de acción sin cortes)**:
  - **Dado** que `AppointmentDetailDialog` muestra múltiples acciones ("Marcar atendido", "Marcar ausente", "Reprogramar", "Cancelar turno") a 390 px,
  - **Cuando** se presenta la hoja inferior,
  - **Entonces** los botones de acción cuentan con un área táctil mínima de 44 px, no quedan recortados por el borde de la pantalla y son accesibles mediante scroll suave o barra fija inferior.
* **Escenario 4.3 (Escritorio — Preservación de modal centrado)**:
  - **Dado** un viewport de escritorio (1440 px),
  - **Cuando** se abre cualquier diálogo de turnos,
  - **Entonces** el diálogo se presenta flotante y centrado en la pantalla con ancho máximo de 580 px y desenfoque de fondo.

### Requisito 5: Soporte de Tema Oscuro en la Aplicación
* **Escenario 5.1 (Tema oscuro por preferencia del sistema)**:
  - **Dado** que el sistema operativo o navegador tiene activado `prefers-color-scheme: dark`,
  - **Cuando** el usuario navega por la agenda sin alternar manualmente el tema,
  - **Entonces** las superficies adoptan los tonos oscuros de la paleta Aqua Navy (`#011C40`, `#023859`), los textos adoptan `#F3F7FA`, y los bordes usan `rgba(167, 235, 242, 0.22)`.
* **Escenario 5.2 (Alternancia manual sin persistencia)**:
  - **Dado** que el usuario se encuentra en la agenda,
  - **Cuando** pulsa el botón "Alternar tema" en `AppShell`,
  - **Entonces** el tema cambia inmediatamente de claro a oscuro (o viceversa) modificando el atributo en memoria, y al recargar la página o cerrar sesión no se conserva la elección en `localStorage` ni en cookies.
* **Escenario 5.3 (Contraste AA en tema oscuro)**:
  - **Dado** el tema oscuro activado,
  - **Cuando** se renderizan textos principales, secundarios, campos de formulario y los 5 estados de turnos en `StatusBadge`,
  - **Entonces** todas las combinaciones de color superan el ratio de contraste 4.5:1 (AA) de WCAG 2.1.

### Requisito 6: Verificación Visual Multi-Resolución (1440 px, 768 px, 390 px)
* **Escenario 6.1 (Capturas de escritorio 1440 px)**: Verificación visual de AppShell horizontal, AgendaToolbar en línea, AgendaGrid con 3 columnas holgadas, y diálogos centrados de 580 px.
* **Escenario 6.2 (Capturas de tablet 768 px)**: Verificación visual de AppShell en dos renglones, AgendaToolbar compacta, AgendaGrid sin scroll desmedido y modales adaptados.
* **Escenario 6.3 (Capturas de celular 390 px)**: Verificación visual de AppShell compacta sin wrap caótico, AgendaToolbar optimizada (< 110 px), AgendaGrid con scroll-snap y horas fijas, y modales como hojas inferiores (Bottom Sheet) sin botones cortados.

---

## 5. Tamaño Estimado y Gestión de Riesgos

### 5.1 Archivos Involucrados
* **Archivos a Modificar (código y CSS de producción)**:
  1. `frontend/src/shared/styles/tokens.css` (variables de tema oscuro y tokens de layout móvil).
  2. `frontend/src/shared/components/AppShell.tsx` (soporte de botón menú y tema fuera de `<nav>`).
  3. `frontend/src/shared/components/AppShell.module.css` (estilos móviles y drawer/colapso).
  4. `frontend/src/features/agenda/AgendaToolbar.tsx` (agrupamiento y disclosure de filtros).
  5. `frontend/src/features/agenda/AgendaToolbar.module.css` (media queries para 768 px y 390 px).
  6. `frontend/src/features/agenda/AgendaGrid.tsx` (asistente de snapping/pestañas de profesional).
  7. `frontend/src/features/agenda/AgendaGrid.module.css` (scroll-snap y anchos móviles).
  8. `frontend/src/features/agenda/AgendaView.module.css` (encabezado compacto).
  9. `frontend/src/shared/components/Dialog.module.css` (modo bottom sheet en `@media (max-width: 768px)`).
  10. `frontend/src/features/appointments/AppointmentDetailDialog.module.css` (ajuste de padding y acciones).
  11. `frontend/src/features/appointments/AppointmentFormDialog.module.css` (ajuste de padding en bottom sheet).
  12. `frontend/src/features/appointments/AppointmentRescheduleDialog.module.css` (ajuste en bottom sheet).

* **Archivos Nuevos de Test (Regla C1 — Tests existentes intactos)**:
  1. `frontend/src/shared/components/AppShell.mobile.test.tsx` (pruebas de toggle de menú móvil y tema).
  2. `frontend/src/features/agenda/AgendaToolbar.mobile.test.tsx` (pruebas de colapso/expansión de filtros).
  3. `frontend/src/features/agenda/AgendaGrid.mobile.test.tsx` (pruebas de estructura de scroll-snap y etiquetas).
  4. `frontend/src/shared/components/Dialog.bottomSheet.test.tsx` (pruebas de clases y accesibilidad de hoja inferior).
  5. `frontend/src/shared/styles/darkThemeTokens.test.ts` (verificación estática de tokens oscuros y ratios de contraste).

* **Volumen Estimado**:
  - ~14 a 18 tests nuevos en total (estricto 1 escenario = 1 test = 1 mutación).
  - 0 tests existentes modificados.

---

### 5.2 Lo que jsdom NO puede medir y Mitigaciones
| Limitación de jsdom 31.0 | Riesgo asociado | Mitigación rigurosa |
|---|---|---|
| **No calcula layout (`box model`)** | No detecta si un texto se corta con ellipsis o si una columna mide exactamente 220 px o 140 px. | Tests unitarios verifican atributos `data-*`, clases CSS aplicadas y presencia de elementos en el DOM; la geometría real se audita mediante verificación visual con capturas reales a 1440 px, 768 px y 390 px. |
| **No evalúa Media Queries reales** | Los bloques `@media (max-width: 768px)` se ignoran en los tests comunes de Vitest. | La lógica condicional de componentes interactivos (por ej. disclosure) se controla mediante estado React / props inyectadas o atributos de datos (`data-mobile`, `open`), evaluables en jsdom. Los estilos se verifican estáticamente en tests de tokens/CSS y visualmente con navegador. |
| **No evalúa Container Queries (`@container`)** | Las reglas `@container agenda-column (width < 260px)` no se disparan en jsdom. | Documentado y probado en C-27 y C-34 mediante tests de CSS estático (`agendaStyles.test.ts`) y capturas de pantalla. |
| **No implementa `position: sticky` ni `scroll-snap`** | No valida físicamente si la columna de horas se queda fija al hacer scroll. | Verificación visual interactiva en navegador antes de archivar. |
| **No simula safe-area en iPhone** | Barras de navegación nativas o bordes inferiores pueden tapar botones. | Uso de `env(safe-area-inset-bottom)` y `100dvh` en los tokens y CSS de producción. |

---

## 6. Resumen y Pasos Siguientes

La exploración confirma que **C-36 debe reenfocarse en resolver la adaptabilidad móvil de la aplicación autenticada (AppShell, Toolbar, Grilla y Modales)**, aprovechando que la portada y el login ya son responsive y oscuros desde C-35. El tema oscuro de la aplicación se estructura como la segunda parte del change, respetando la regla de no persistir en `localStorage` ni cookies.

**Decisiones clave recomendadas**:
1. **D1 (Scope)**: App móvil primero (Fases 1–4); Tema oscuro de la app como Parte 2 (Fases 5–6).
2. **D2 (Barra)**: Menú móvil desplegable con botón fuera de `<nav>` para no romper `AppShell.test.tsx`.
3. **D3 (Toolbar)**: Compactación en 2 filas y filtros desplegables mediante botón "Filtros", manteniéndolos en el DOM para tests existentes.
4. **D4 (Grilla)**: Scroll horizontal fluido con `scroll-snap`, columna de horas fija y preservación del default `"grid"`.
5. **D5 (Modales)**: Hoja inferior (Bottom Sheet) a ancho completo en celular con scroll vertical interno.
6. **D6 (Tema oscuro)**: Tokens de paleta Aqua Navy/Ice en `tokens.css`, soporte `prefers-color-scheme` y botón toggle en `AppShell` sin persistencia.

*Frenamos aquí sin ejecutar `/opsx:propose` conforme a las instrucciones.*
