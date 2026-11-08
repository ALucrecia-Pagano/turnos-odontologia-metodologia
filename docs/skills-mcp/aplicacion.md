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
