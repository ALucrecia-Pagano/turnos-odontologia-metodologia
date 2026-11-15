# Aplicación: skill propia y MCP Context7

**Proyecto:** sistema de turnos odontológicos · **Alumna:** Amanda Pagano · **Fecha:** 2026-11-08
**Integración:** OpenCode 1.19 (ver nota de limitaciones) · **Repo:** turnos-odontologia

> Regla de seguridad respetada: la clave `CONTEXT7_API_KEY` no se escribe ni se imprime en ningún archivo, comando ni salida.

Este documento cuenta qué se instaló, cómo se creó la skill, cómo se usó el MCP y qué salió bien y mal. El detalle paso a paso y las salidas completas están en `docs/skills-mcp/evidencias/`:

- [01-instalacion-skill-creator.txt](evidencias/01-instalacion-skill-creator.txt) — instalación y comparación de `skill-creator`.
- [02-opencode-mcp-list.png](evidencias/02-opencode-mcp-list.png) — `opencode mcp list` con `context7` conectado.
- [03-creacion-skill.md](evidencias/03-creacion-skill.md) — proceso de creación de la skill y comparación de copias.
- [04-uso-context7.md](evidencias/04-uso-context7.md) — llamada real al MCP y evaluación crítica.

---

## 1. Qué se instaló

- **`skill-creator`** (Anthropic, Apache 2.0): instalada a nivel proyecto con el CLI `skills`
  (`npx skills add anthropics/skills --skill skill-creator -a claude-code --copy --yes`) y
  versionada en `.agents/skills/skill-creator/` (copia de `.claude/skills/skill-creator/`).
  Las dos copias son idénticas, y también son idénticas a la que Active Stack tenía a nivel usuario.
- **Skill propia `appointment-frontend-ux`**: creada con `skill-creator` y versionada en
  `.agents/skills/appointment-frontend-ux/` (fuente canónica), espejada en `.claude/skills/`.
- **MCP `context7`**: configurado a nivel proyecto en `opencode.json` (OpenCode) y `.mcp.json`
  (Claude Code), apuntando a `https://mcp.context7.com/mcp`. La credencial vive solo en la variable
  de entorno `CONTEXT7_API_KEY`.

## 2. Cómo se creó la skill

Se siguió el proceso de `skill-creator`:

1. **Intención**: guiar el trabajo de UI de la agenda (C-25 a C-33) para que cada pantalla respete
   tokens, accesibilidad, zona horaria de la API, confinamiento del token de sesión y la regla C1 de
   tests, y para que se verifique visualmente antes de archivar.
2. **Investigación**: se leyó el código y las specs existentes (C-25, C-26, C-27) para que la skill
   no invente reglas: versiones de `package.json`, `tokens.css`, `appointmentStatusTokens.ts`,
   `StatusBadge`, `agendaConfig.ts`, `agendaTime.ts`, `AgendaGrid.tsx`, `clock.ts`, `tokenStore.ts`
   y `docs/evidencias/verify-C-27.md` (§Hallazgo de la revisión visual 2).
3. **`SKILL.md`**: frontmatter con `name` y `description` (descripción "pushy" con disparadores, que
   es el mecanismo principal de activación) y un cuerpo con: stack y versiones exactas y cuándo
   consultar Context7; tokens en `tokens.css`; accesibilidad (estado con texto visible, nunca solo
   color; foco visible; `aria-label` completos); prioridad hora/paciente en tarjetas angostas
   (formato en dos líneas de C-27); zona horaria desde la API (fallback solo en `agendaConfig.ts`);
   token solo en `tokenStore.ts`; regla C1 de tests; verificación visual 1440/768 antes de archivar.
4. **Casos de prueba**: `evals/evals.json` con 5 pedidos reales de UI del proyecto.
5. **Copia y verificación**: `.agents/skills/` → `.claude/skills/`, con `diff -r` y `cmp` idénticos.

## 3. La llamada al MCP y sus resultados

Se usó el MCP `context7` de punta a punta para preparar C-28 (semana en la URL):

1. **`resolve-library-id`** con `libraryName = "react-router"` y
   `query = "React Router useSearchParams hook in version 6"`. Resultado: entre varios candidatos,
   se eligió **`/websites/reactrouter`** porque es el único que indexa la serie **6.30** (6.30.3),
   que es la que usa el repo (`react-router-dom@6.30.6`).
2. **`query-docs`** con `libraryId = "/websites/reactrouter"` sobre `useSearchParams` en la v6.
   Resultado: `useSearchParams(defaultInit?)` devuelve `[URLSearchParams, SetURLSearchParams]`;
   `setSearchParams` navega y acepta string, objeto, arrays, tuplas, `URLSearchParams` o un callback;
   el callback no encola como `setState`; `defaultInit` no cambia la URL en el primer render;
   `searchParams` es una referencia estable pero mutable.

**Evaluación crítica:** el índice sí tiene la 6.30, pero el contenido de la página es el de la
documentación actual (v7): el ejemplo importa desde `"react-router"`. Para la v6.30.6 del repo hay
que importar `useSearchParams` desde `react-router-dom`. La API del hook es la misma, así que el
resultado sirve, con ese ajuste de import. No se detectó nada incorrecto. Detalle en
[04-uso-context7.md](evidencias/04-uso-context7.md).

## 4. Revisión crítica

**Lo que funcionó:**

- `skill-creator` instalada y reconocida; su proceso (intención → investigación → `SKILL.md` con
  frontmatter → casos de prueba) fue claro y suficiente para producir una skill concreta y atada al
  código real.
- La skill quedó portable (formato Agent Skills) y con las dos copias idénticas, verificado con
  `diff -r` y `cmp`.
- Context7 respondió rápido y con documentación correcta de `useSearchParams`, útil para C-28.
- La configuración por variable de entorno evita que la clave quede en el repo.

**Lo que no funcionó o costó:**

- El CLI `skills` quedó esperando un prompt interactivo sin TTY; hubo que reejecutar con `--yes`.
- La documentación de Context7 está redactada para la v7 de React Router (import desde
  `react-router`), aunque el índice tenga la 6.30: hay que leerla con criterio y ajustar el import.
- El límite de uso semanal de Claude Code obligó a hacer la integración con OpenCode 1.19.

**Limitaciones:**

- **Evals automáticos de `skill-creator`**: corren con `claude -p` (Claude Code), así que **no se
  pudieron ejecutar desde OpenCode**. No se simularon: los casos quedan en `evals/evals.json` y la
  evaluación automática queda pendiente para una sesión de Claude Code.
- Las pruebas de disponibilidad de skills en agentes distintos de OpenCode siguen **pendientes**
  (Codex, GitHub Copilot, Google Antigravity); en `investigacion.md` solo OpenCode figura verificado.
- `.mcp.json` queda configurado para Claude Code y `opencode.json` para OpenCode; no se probó el
  servidor desde Claude Code en esta sesión.

## 5. Uso en C-28

En el change `ui-agenda-semanal` (C-28) se aplicaron tanto la skill propia `appointment-frontend-ux` como la evidencia obtenida con el MCP Context7 (`04-uso-context7.md`), guiando el diseño, la implementación y los tests de la vista semanal.

### 5.1. Aplicación de la skill `appointment-frontend-ux`

La skill se cargó como referencia obligatoria antes de escribir código y se ejecutó su checklist paso a paso:

1. **Stack y versiones**:
   - Se respetó el stack del proyecto (React 18.3.1, TypeScript strict, Vite 5, React Router 6.30.6, Vitest 3.2.7) sin añadir dependencias externas ni recurrir a sintaxis de versiones posteriores.

2. **Tokens de diseño**:
   - Todo el diseño visual reutilizó las variables semánticas de `tokens.css`: `--color-surface`, `--color-surface-hover`, `--color-border-subtle`, `--color-primary-subtle`, `--space-sm`, `--space-md`, radios y tipografías.
   - En `AgendaToolbar.module.css` y `AgendaGrid.module.css` no se introdujo ningún valor hardcodeado ni color arbitrario.

3. **Accesibilidad (a11y)**:
   - **Estado del turno visible con texto**: los turnos cancelados en la grilla semanal muestran explícitamente la etiqueta de texto `"Cancelado"`, nunca dependiendo exclusivamente del color atenuado.
   - **Indicador de día actual ("Hoy")**: la cabecera de la columna correspondiente a la fecha de hoy muestra el texto visible `"Hoy"` junto al día y número, acompañado del atributo semántico `aria-current="date"`. No se confía únicamente en un borde o fondo coloreado.
   - **Etiquetas accesibles en navegación**: los botones de navegación anterior/siguiente de `AgendaToolbar` adaptan dinámicamente su texto visible y `aria-label` a `"Semana anterior"` y `"Semana siguiente"` cuando `view=week`, facilitando la navegación por tecnologías asistivas y teclado.
   - **Selector segmentado accesible**: el control `[ Día | Semana ]` en la barra de herramientas utiliza botones semánticos con estados de foco visibles y claros.

4. **Zona horaria y hora local**:
   - En la vista semanal de 7 columnas (lunes a domingo), los turnos y los horarios de atención se distribuyen según la fecha local determinada por el `timezone` devuelto por la API REST (`America/Argentina/Buenos_Aires`). La conversión se realiza de forma pura en `agendaLayout.ts` reutilizando las funciones de `agendaTime.ts`, garantizando que turnos guardados en UTC caigan en el día local correcto.

5. **Confinamiento del token de sesión**:
   - La preselección automática por rol en la vista semanal (odontólogo preselecciona su propio `professionalId`; recepción y administrador preseleccionan al primer profesional activo) consume los datos del usuario autenticado a través del hook `useSession` y `tokenStore.ts`, sin exponer ni almacenar credenciales en componentes de presentación.

6. **Regla C1 de tests (sin mocks globales)**:
   - Los 15 nuevos tests (unitarios en `agendaTime.test.ts`, `agendaLayout.test.ts`, hooks en `useAgenda.test.tsx`, componentes en `AgendaToolbar.test.tsx`, `AgendaView.test.tsx`, `AgendaPage.test.tsx` y verificación de estilos en `agendaStyles.test.ts`) se escribieron bajo la regla C1:
     - Cero uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers`, `vi.setSystemTime` o MSW.
     - Pruebas con `createApiClient({ fetchFn })` inyectando respuestas controladas.
     - Pruebas temporales con `createFixedClock` de `clock.ts`.
     - Enrutamiento y URL simulados con `createMemoryRouter` y `RouterProvider` de `react-router-dom`.
   - Se preservó intacta la suite de 127 tests preexistentes de C-27 sin modificar una sola línea de código previo.

7. **Layout responsive para tablet (768 px)**:
   - Se configuró la grilla semanal con contenedor de desplazamiento horizontal (`overflow-x: auto`), cabeceras sticky y columna horaria con `position: sticky; left: 0; z-index: 2` para mantener la referencia horaria visible mientras se hace scroll en pantallas medianas.
   - Se aplicó el formato en dos líneas para tarjetas de turno en columnas angostas (< 260 px), priorizando hora y paciente conforme lo estipulado en la skill.

---

### 5.2. Aplicación de la evidencia 04 de Context7

La evidencia documentada en `docs/skills-mcp/evidencias/04-uso-context7.md` sirvió de base directa para la implementación de los parámetros de búsqueda en la URL:

1. **Ajuste de import (v6 vs v7)**:
   - La consulta a Context7 alertó en su evaluación crítica que los ejemplos de la documentación indexada importaban desde `"react-router"` (estilo v7). En `AgendaPage.tsx` se aplicó la recomendación estricta de importar `useSearchParams` desde `"react-router-dom"` para garantizar compatibilidad total con la versión instalada (`react-router-dom@6.30.6`).

2. **Lectura y sincronización funcional de URL**:
   - Siguiendo las directrices obtenidas sobre la API del hook:
     - Se extrajeron `date` y `view` mediante `searchParams.get("date")` y `searchParams.get("view")`.
     - Las transiciones de vista (alternar entre día y semana) y la navegación temporal se realizaron actualizando los parámetros de búsqueda mediante el callback de `setSearchParams(prev => ...)` o instanciando nuevos `URLSearchParams`, asegurando la preservación de los filtros activos (`date`, `professionalId`, `chairId`) y evitando desincronizaciones del historial del navegador.

El change quedó verificado y archivado exitosamente el 2026-11-08; el reporte completo con sus métricas, trazabilidad y capturas de pantalla se encuentra en [docs/evidencias/verify-C-28.md](../evidencias/verify-C-28.md).

---

## 6. Uso en C-31

En el change `ui-vista-de-recepcion-por-sillon` (C-31) se aplicó la skill propia `appointment-frontend-ux` para guiar el diseño, la implementación y las pruebas de la vista de recepción por sillón (`view=chair`).

### 6.1. Qué se pidió
La incorporación de la vista de recepción por sillón para recepcionistas y administradores, agrupando la agenda del día por columnas de sillón, con visualización accesible de los turnos asignados (destacando el profesional a cargo) y de las bandas de disponibilidad (huecos libres y tramos fuera de horario).

### 6.2. Qué herramienta se utilizó
Se aplicó la skill propia `appointment-frontend-ux` (`.agents/skills/appointment-frontend-ux/SKILL.md`) junto con las skills de apoyo resueltas en `.atl/skill-registry.md` (`tdd`, `frontend-design`, `vitest`, `vercel-react-best-practices`). **No se utilizó Context7**, ya que la funcionalidad reutilizó las primitivas y contratos del andamiaje frontend preexistente sin introducir APIs externas nuevas.

### 6.3. Qué resultado se obtuvo
- **Tokens únicamente**: Creación de tokens semánticos en `tokens.css` para bloques de disponibilidad (`--agenda-free-bg`, `--agenda-free-border`, `--agenda-free-color`, `--agenda-outside-bg`, `--agenda-outside-border`, `--agenda-outside-color`, `--agenda-card-chair-second-row-color`). Cero valores HEX o `rgb()` arbitrarios en código de producción.
- **Accesibilidad estricta**: Estados con texto visible (`StatusBadge`); bandas de disponibilidad con horario en texto visible (`Libre HH:MM–HH:MM` o `Fuera de horario HH:MM–HH:MM`) y `aria-label` descriptivo; tarjetas de turno con `aria-label` completo (hora, paciente, prestación, profesional, sillón, estado) y foco visible `:focus-visible`.
- **Prioridad hora/paciente y profesional**: En la columna de sillón se muestra el nombre del profesional a cargo en el cuerpo de la tarjeta (`.cardProfessional`), preservando la jerarquía hora > paciente > profesional > estado sin truncar en columnas angostas.
- **Reutilización y responsive**: Reutilización de `AgendaGrid` con `scroll-snap-type: x mandatory` y canal horario sticky a la izquierda; reorganización de la barra de herramientas a 390 px para que los controles de navegación entren sin desborde horizontal de la página.
- **Confinamiento del token**: El token de sesión vive únicamente en `tokenStore.ts`, probado mediante `createMemoryTokenStore`.
- **Zona horaria de la API**: Conversión horaria centralizada bajo `America/Argentina/Buenos_Aires` (`DEFAULT_AGENDA_TIMEZONE`) y reloj inyectado mediante `createFixedClock`.
- **Regla C1 de pruebas**: Suite de tests sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` ni MSW, inyectando `createApiClient`, `createFixedClock` y `createMemoryRouter`.

### 6.4. Cómo se revisó y enlace a la evidencia
Se validó con la suite completa de tests de frontend (13 escenarios de C-31), comprobación de tooling (`npm run lint`, `typecheck`, `build`) y verificación visual multi-resolución en 1440 px, 768 px y 390 px.
Evidencia documentada en [docs/skills-mcp/evidencias/C-31-skill-appointment-frontend-ux.md](evidencias/C-31-skill-appointment-frontend-ux.md) y reporte de cierre en [docs/evidencias/verify-C-31.md](../evidencias/verify-C-31.md).

---

## 7. Uso en C-32

En el change `ui-horarios-y-bloqueos` (C-32) se aplicaron tanto la skill propia `appointment-frontend-ux` como el servidor MCP `context7` para el desarrollo de la pantalla de configuración de horarios y bloqueos (`/horarios`).

### 7.1. Qué se pidió
Una pantalla para configurar los tramos semanales de atención por profesional y registrar o eliminar bloqueos de agenda puntuales, con visualización inmediata de los turnos afectados ante modificaciones que acorten el horario o bloqueos que pisen turnos existentes.

### 7.2. Qué herramientas se utilizaron
- **Skill propia `appointment-frontend-ux`**: marco rector de diseño accesible, tokens, confinamiento de credenciales y regla C1.
- **MCP `context7`**: consulta oficial a la documentación de **React Router v6** (`react-router-dom@6.30.6`).

### 7.3. Qué resultado se obtuvo
- **De Context7**:
  - `resolve-library-id` con `libraryName: "react-router-dom"` y `query: "useSearchParams and createMemoryRouter in React Router v6"`, seleccionando `/websites/reactrouter/6.30.3`.
  - `query-docs` para confirmar la firma de `useSearchParams()` y el uso de `setSearchParams(nextInit, { replace: true })`, lo que permitió actualizar el query string `?professionalId=...` sincronizando la URL sin apilar entradas redundantes en el historial del navegador.
  - Confirmación del uso de `createMemoryRouter(routes, { initialEntries })` con `<RouterProvider />` para evaluar rutas protegidas bajo la Regla C1.
- **De la skill**:
  - **Tokens de diseño**: Reutilización estricta de variables de `tokens.css`; `font-family: inherit` en inputs y selects; cero valores HEX o `rgb()` sueltos.
  - **Accesibilidad**: Estados de turnos afectados comunicados con texto visible (`StatusBadge`); días de atención agrupados semánticamente con `<fieldset>` y `<legend>`; controles interactivos con área táctil ≥ 44×44 px y `:focus-visible`; alertas de error y de turnos afectados con `role="alert"` y traslado de foco; confirmaciones de éxito en región `role="status"`.
  - **Zona horaria desde la API**: Lectura de `timezone` consultando una única vez `GET /api/agenda` al cargar la pantalla, formateando fechas y horas locales con `Intl.DateTimeFormat` y generando el offset ISO mediante `buildStartAtIso` para el envío de bloqueos.
  - **Confinamiento del token**: Acceso al token exclusivamente a través de `features/auth/tokenStore.ts`.
  - **Adaptabilidad móvil**: Distribución en 2 columnas en 1440 px y 1 columna en 768 px y 390 px; modales `BlockFormDialog` y `BlockDeleteDialog` como hoja inferior (*bottom sheet*) a ≤ 640 px mediante `Dialog.tsx`.
  - **Regla C1 de pruebas**: Cero uso de mocks de módulo, espías o temporizadores falsos.

### 7.4. Cómo se revisó y enlace a la evidencia
Se comprobó mediante la suite de tests unitarios y de componentes de `features/horarios/`, ejecución de tooling y verificación responsive en 1440 px, 768 px y 390 px.
Evidencia documentada en [docs/skills-mcp/evidencias/C-32-skill-mcp.md](evidencias/C-32-skill-mcp.md) y reporte de verificación en [docs/evidencias/verify-C-32.md](../evidencias/verify-C-32.md).

---

## 8. Uso en C-33

En el change `ui-catalogos-y-pacientes` (C-33) se aplicó la skill propia `appointment-frontend-ux` para la construcción de las pantallas de gestión de catálogos y pacientes.

### 8.1. Qué se pidió
Implementar las pantallas de administración de pacientes (`/pacientes`, búsqueda en vivo por DNI/apellido, alta y edición) y de catálogos (`/catalogos`, pestañas para profesionales, sillones y prestaciones, con altas, edición y desactivación/reactivación según rol).

### 8.2. Qué herramientas se utilizaron
- **Skill propia `appointment-frontend-ux`** (con `tdd`, `frontend-design`, `vitest`, `vercel-react-best-practices`).
- **MCP `context7`**: Tal como consta explícitamente en la evidencia, **no se requirieron consultas adicionales a Context7**, puesto que todas las APIs de React Router v6, React 18 y Testing Library necesarias ya estaban en uso comprobado en el proyecto.

### 8.3. Qué resultado se obtuvo
- **Tokens únicamente**: Consumo exclusivo de tokens de `tokens.css` para superficies claras, respetando la prohibición de tokens oscuros (`--color-ice`, `*-on-navy`); `font-family: inherit` en inputs y selects; cero colores arbitrarios.
- **Accesibilidad estricta**: Estado de catálogo comunicado con texto visible mediante `ActiveBadge` ("Activo" / "Inactivo"); tablas semánticas con `<caption>` y `<th scope="col">`; controles táctiles ≥ 44×44 px con `:focus-visible`; alertas de error con `role="alert"` y foco trasladado; región de confirmación persistente con `role="status"`.
- **Confinamiento del token**: Aislamiento estricto del token en `tokenStore.ts` y pruebas con `createMemoryTokenStore`.
- **Regla C1 de pruebas**: Suite de tests sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` ni MSW; inyección de dependencias mediante `createApiClient` y `createMemoryRouter`.
- **Adaptabilidad responsive**: Tablas transformadas en tarjetas apiladas en celular con `data-label` a ≤ 640 px sin scroll horizontal; modales `PatientFormDialog` y `CatalogFormDialog` operando como hoja inferior (*bottom sheet*) sobre `Dialog.tsx`.

### 8.4. Cómo se revisó y enlace a la evidencia
Se validó con la suite completa de tests de pacientes y catálogos, ejecución de tooling (`npm run lint`, `typecheck`, `build`) y verificación visual multi-resolución en 1440 px, 768 px y 390 px.
Evidencia documentada en [docs/skills-mcp/evidencias/C-33-skill-mcp.md](evidencias/C-33-skill-mcp.md) y reporte de cierre en [docs/evidencias/verify-C-33.md](../evidencias/verify-C-33.md).

---

## 9. Uso en C-35

En el change `ui-portada-y-acceso` (C-35) se combinaron consultas específicas al MCP `context7` y la aplicación rigurosa de la skill `appointment-frontend-ux`.

### 9.1. Qué se pidió
Desarrollar la portada pública del consultorio (`/`), la pantalla de selección de rol (`/acceso`), el rediseño translúcido del formulario de login (`/login`) sobre el carrusel fotográfico y la estandarización de modales con fondo claro sobre la agenda.

### 9.2. Qué herramientas se utilizaron
- **MCP `context7`**: Consultas técnicas a la documentación de React Router v6 y MDN Web Docs CSS.
- **Skill propia `appointment-frontend-ux`** (junto con `tdd`, `frontend-design`, `vercel-react-best-practices` y `vitest`).

### 9.3. Qué resultado se obtuvo
- **De Context7**:
  - `resolve-library-id` (`libraryName: "React Router"`) → `/websites/reactrouter` (v6.30.3). `query-docs` sobre rutas de layout sin `path`, rutas índice, `createMemoryRouter` y `useSearchParams`. Se aplicó `useSearchParams()` estilo v6 para leer el parámetro `?rol` en `LoginPage.tsx` sin dependencias de APIs v7.
  - `resolve-library-id` (`libraryName: "MDN Web Docs CSS"`) → `/mdn/content`. `query-docs` sobre `backdrop-filter` con fallback y `prefers-reduced-motion`. Se aplicó el bloque `@supports not (backdrop-filter: blur(1px))` para un fondo sólido alternativo y `@media (prefers-reduced-motion: reduce)` ubicado al final de los archivos CSS Modules para respetar el orden de cascada.
- **De la skill**:
  - **Tokens de diseño**: Nuevos tokens en `tokens.css` (`--surface-navy`, `--surface-ivory-ice`, elevaciones) sin valores HEX ni `rgb()` sueltos.
  - **Accesibilidad**: Focos visibles `:focus-visible` diferenciados por superficie (`--color-ice` sobre navy, `--color-focus` sobre claro); áreas interactivas ≥ 44×44 px; tarjetas de rol con `aria-labelledby` y `aria-describedby`; flechas decorativas con `aria-hidden`.
  - **Superficie propia en diálogos**: Siguiendo las lecciones de C-30, los modales poseen superficie propia (`--surface-ivory-ice`) y `Dialog.tsx` provee únicamente el backdrop, garantizando que el foco no caiga al `<body>`.
  - **Regla C1**: Inyección de `fetch`, `Clock`, ticker del carrusel y observador de intersección mediante props, sin asignar ni alterar variables globales.

### 9.4. Cómo se revisó y enlace a la evidencia
Se comprobó mediante suite de tests unitarios y de integración de rutas, tooling completo y 35 capturas de pantalla cubriendo 1440 px, 768 px y 390 px en estados normales, de foco y de movimiento reducido.
Evidencias documentadas en [docs/skills-mcp/evidencias/C-35-mcp-context7.md](evidencias/C-35-mcp-context7.md) y [docs/skills-mcp/evidencias/C-35-skill-appointment-frontend-ux.md](evidencias/C-35-skill-appointment-frontend-ux.md); reporte de cierre en [docs/evidencias/verify-C-35.md](../evidencias/verify-C-35.md).

---

## 10. Uso en C-36

En el change `ui-tema-oscuro-y-movil` (C-36) se recurrió al MCP `context7` para investigar patrones CSS avanzados y a la skill `appointment-frontend-ux` para la adaptación móvil de la agenda.

### 10.1. Qué se pidió
Hacer que toda la aplicación sea plenamente usable en dispositivos móviles (pantallas ≤ 640 px), implementando menú colapsable tipo hamburguesa, barra de herramientas compacta en dos filas, grilla de agenda con desplazamiento horizontal fluido por columnas completas y modales desplegados como hoja inferior (*bottom sheet*).

### 10.2. Qué herramientas se utilizaron
- **MCP `context7`**: Consulta a la documentación oficial de MDN Web Docs (`/mdn/content`).
- **Skill propia `appointment-frontend-ux`**: Directivas de tokens, accesibilidad móvil, prioridad de contenido y verificación obligatoria.

### 10.3. Qué resultado se obtuvo
- **De Context7**:
  - Consulta sobre `scroll-snap-type mandatory with position sticky time gutter and dynamic viewport height dvh`.
  - Aplicación de `scroll-snap-type: x mandatory` en `.gridScrollContainer` junto con `scroll-snap-align: start` en las columnas para que el desplazamiento móvil encaje exactamente en una columna completa (día o profesional).
  - Aplicación de `scroll-padding-left: var(--agenda-time-gutter-width)` para que las columnas no queden ocultas debajo de la columna fija de horas (`position: sticky; left: 0`).
  - Uso de unidades dinámicas `max-height: 90dvh` (con fallback de `90vh`) en `Dialog.module.css` para la hoja inferior, impidiendo que la barra de navegación del navegador móvil tape los botones de acción.
- **De la skill**:
  - **Tokens**: Token `--breakpoint-mobile: 640px` y variables de espaciado y tipografía sin dimensiones hardcodeadas.
  - **Accesibilidad móvil**: Botones "Menú" y "Filtros" con atributos accesibles `aria-expanded` y `aria-controls`; controles táctiles con tamaño mínimo de 44×44 px; tecla `Escape` cerrando menús y modales retornando el foco al disparador.
  - **Prioridad en tarjetas**: Formato en dos líneas priorizando hora y paciente cuando el ancho de columna es reducido.
  - **Regla C1**: Pruebas sin mocks globales, validando el comportamiento móvil inyectando eventos y tamaños.

### 10.4. Cómo se revisó y enlace a la evidencia
Se comprobó mediante la suite de tests de componentes móviles, ejecución de tooling y 15 capturas en navegador real a 1440 px, 768 px y 390 px.
Evidencia documentada en [docs/skills-mcp/evidencias/C-36-context7.md](evidencias/C-36-context7.md) y reporte de cierre en [docs/evidencias/verify-C-36.md](../evidencias/verify-C-36.md).
