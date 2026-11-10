# Exploración — C-35 `ui-portada-y-acceso`

Fecha: 2026-11-09
Repo: turnos-odontologia
Rama leída: `c34-apply`
Change explorado: **C-35 `ui-portada-y-acceso`** (portada pública de “Aqua — Clínica Odontológica” que reemplaza la pantalla de login actual)
Depende de: **C-34 `ui-identidad-visual`** (en curso en `c34-apply`)
Alcance de este paso: **solo explore**. Único archivo creado: este documento. No se tocó código, tests, `CHANGES.md`, `.env`, `.codex/` ni se instaló nada.

---

## 1. Contexto: archivos y specs leídos

### Login (estado actual)
- `frontend/src/features/login/LoginPage.tsx` — pantalla `/login`: `<main class=page>` con carrusel de fondo, logo claro, bajada “Claridad en cada cuidado.”, tarjeta vidrio y `<h1 id="login-heading">Turnos Odontología</h1>`.
- `frontend/src/features/login/LoginCarousel.tsx` — 5 fotos, `createIntervalTicker(7000)`, Ken Burns, pausa sin `aria-pressed`, reduced motion con guarda para jsdom y ticker inyectable.
- `frontend/src/features/login/LoginForm.tsx` — form `aria-label="Iniciar sesión"`, campos `Usuario`/`Contraseña` (el usuario con `autoFocus`), submit “Ingresar” / “Ingresando…”.
- `frontend/src/features/login/LoginPage.module.css` — overlay navy, `.carousel`, `.slide`, `.kenBurns`, `.card`, `.form`, `.alert`, `@media (prefers-reduced-motion: reduce)`.
- `frontend/src/features/login/LoginPage.test.tsx` — 6 escenarios de auth; usa `getByRole("button", { name: "Ingresar" })` en las líneas 101, 138, 195, 224 y 259; exige foco en `Usuario` al montar (línea 312); exige `getByRole("form", { name: "Iniciar sesión" })` (línea 267); prohíbe checkbox y “recordar” (líneas 314-316).
- `frontend/src/features/login/LoginBrand.test.tsx` — logo `role="img"` con nombre `Aqua — Clínica Odontológica` (líneas 56-61), heading “Turnos Odontología” (línea 62), bajada visible (línea 63) y botón “Pausar animación” (línea 71).
- `frontend/src/features/login/LoginCarousel.test.tsx` — 5 fotos, avance por ticker inyectado, pausa, reduced motion, cancelación al desmontar.

### Router y guards
- `frontend/src/App.tsx` — `createAppRoutes(clock)` devuelve **`routes[0] = "/login"`** (`PublicOnlyRoute` → `LoginPage`) y **`routes[1] = "/"`** (`RequireAuth` → `AppShell` → `RootRedirect` a `/agenda?date=hoy`, `agenda`, `*` → `NotFoundPage`).
- `frontend/src/features/auth/RequireAuth.tsx` — `checking` → `LoadingState`; `anonymous` → `Navigate` a `/login` con `state.from` y `state.expired`.
- `frontend/src/features/auth/PublicOnlyRoute.tsx` — `checking` → `LoadingState`; `authenticated` → `Navigate` a `safeInternalPath(state.from)` o `/`.
- `frontend/src/features/auth/AuthContext.tsx` — `status`, `lastEvent`, `SESSION_EXPIRED_MESSAGE`, login/logout y manejo del 401.
- `frontend/src/features/auth/safeInternalPath.ts` — rechaza `//`, `/login` y URLs absolutas.
- `frontend/src/App.test.tsx` — **encontrado además de los pedidos y es crítico**: `routes.slice(0, 1)` + `routes[1]?.element` (líneas 186-192) asume el orden de rutas; y el escenario de sesión vencida consulta `role="alert"` con el mensaje (líneas 219-221).
- `frontend/src/test/smoke.test.tsx` — renderiza `<App />` (sin URL) y exige `heading` “Turnos Odontología”.

### Auth, estilos y tooling
- `frontend/src/features/auth/storageGuard.test.ts` — el `sessionStorage` debe quedar confinado a `features/auth/tokenStore.ts`; prohíbe `localStorage` y cookies.
- `frontend/src/shared/styles/tokens.css` — paleta Aqua y tokens de agenda; **no hay colores de portada nuevos**.
- `frontend/src/shared/styles/tokens.test.ts` — verifica tokens puntuales (no prohíbe agregar tokens).
- `frontend/vite.config.ts` — `environment: "jsdom"`, `globals: true`, `setupFiles: ./src/test/setup.ts`, CSS Modules `non-scoped`.
- `frontend/src/test/setup.ts` — solo ajusta `AbortController`/`AbortSignal` y hace `cleanup`; **no polyfillea** `matchMedia`, `IntersectionObserver` ni `HTMLDialogElement.showModal`.
- `frontend/package.json` — React 18.3.1, React Router DOM 6.30.6, Vite 5.4.21, Vitest 3.2.7, jsdom 31.0.0, Testing Library 16.3.3.
- `frontend/src/pages/HomePage.tsx` / `NotFoundPage.tsx` — las páginas actuales del shell; `HomePage` no se usa en el router.
- `frontend/src/shared/components/AppShell.tsx` — barra única con marca; el logo de la barra queda fuera de `nav`.
- `backend/app/demo_data.py` — profesionales ficticios del seed: **Dr. Martín Sosa**, **Dra. Laura Quiroga**, **Dra. Paula Benítez**; prestaciones `Limpieza` (45), `Extracción` (60), `Restauración` (60), `Control` (30), `Blanqueamiento` (90); horario base lunes a viernes 9:00–13:00 y 15:00–19:00 (Sosa solo por la mañana).

### Specs
- `openspec/specs/frontend-auth-session/spec.md` — requisitos de Login, rutas con `from`, 401, 403, menú y logout.
- `openspec/specs/frontend-foundation/spec.md` — estructura, tokens, estados base, cliente de API y Docker.
- `openspec/changes/ui-identidad-visual/` — `proposal.md`, `design.md`, `tasks.md` y deltas de `frontend-auth-session` y `frontend-foundation` (marca, logo claro, bajada, carrusel, tipografías, paleta).
- No existe `openspec/specs/frontend-landing/` todavía.

---

## 2. Hallazgos verificados (evidencia empírica)

Ejecuté pruebas puntuales con el `jsdom@31.0.0` ya instalado (no se instaló nada) y revisé las expectativas de los tests:

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| H1 | jsdom 31 **expone `HTMLDialogElement`** pero **no implementa** `showModal()` ni `close()`: son `undefined`. Llamarlos lanza `TypeError: dialog.showModal is not a function`. | Prueba directa con `new JSDOM(...)`. |
| H2 | Un `<dialog>` **sin `open`** computa `display: none`; con `open` computa `display: block`. | `getComputedStyle(dialog).display`. |
| H3 | Testing Library excluye de `getByRole`/`queryByRole` lo que está en `display: none` o bajo `aria-hidden="true"`. Combinado con H2, **el contenido de un `<dialog>` cerrado no se encuentra por rol**. | `App.test.tsx:219-221` consulta `role="alert"` después de redirigir a `/login`; si el diálogo estuviera cerrado, el alert sería `display:none`. |
| H4 | `IntersectionObserver` **no existe** en jsdom. | Prueba directa. |
| H5 | `window.matchMedia` **no existe** en jsdom (el código de C-34 lo contempla con guarda). | Prueba directa; `LoginCarousel.tsx:28-33`. |
| H6 | jest-dom `toBeVisible` considera **`opacity: 0` como no visible** (mira `display`, `visibility` y `opacity`). | `node_modules/@testing-library/jest-dom/dist/matchers-*.mjs`. |
| H7 | Vitest/jsdom entra por defecto en **`pathname = "/"`**. | URL por defecto `http://localhost:3000/`. Por eso `smoke.test.tsx` depende del redirect de `/` a `/login`. |
| H8 | `App.test.tsx` depende del **orden de `createAppRoutes`**: usa `routes.slice(0, 1)` y `routes[1]?.element`. Insertar o reordenar rutas rompe ese test. | `frontend/src/App.test.tsx:186-192`. |
| H9 | `LoginPage.test.tsx` busca **un único** botón `"Ingresar"`. Un segundo botón con el mismo nombre accesible hace fallar `getByRole` por múltiples coincidencias. | `LoginPage.test.tsx:101,138,195,224,259`. |
| H10 | `LoginBrand.test.tsx` exige, en el mismo render, el **logo** (`role="img"`) y el botón **“Pausar animación”**. Si se oculta todo el bloque del hero con `aria-hidden`, esos queries fallan. | `LoginBrand.test.tsx:56-63,71`. |
| H11 | El heading “Turnos Odontología” se busca por **rol + nombre**, no por nivel (`h1`/`h2` son indistintos para el test). | `smoke.test.tsx:7`; `LoginBrand.test.tsx:62`. |

---

## 3. Decisiones a confirmar (todas juntas)

> Recomendación pensada para **no modificar ningún test existente**. La autora puede aceptar la columna “Recomendada” en bloque o pedir cambios puntuales.

| # | Tema | Opción recomendada | Alternativas | Motivo |
|---|------|--------------------|--------------|--------|
| D1 | Apertura del `<dialog>` en jsdom | `<dialog>` nativo. Abrir en un efecto con detección de capacidad: si `typeof dialog.showModal === "function"` → `showModal()`; si no (jsdom 31) → `setAttribute("open", "")`. Cerrar con `close()` si existe; si no → `removeAttribute("open")`. Sin stubs de globals. | (a) Modal con `<div role="dialog" aria-modal="true">` y focus trap manual. (b) `vi.stubGlobal("HTMLDialogElement", …)` (prohibido por C1). | H1/H2: el fallback deja el formulario accesible (`<dialog open>` = `display:block`) y evita `TypeError`, sin mocks. Respeta la decisión ya tomada de usar `<dialog>`. |
| D2 | Ruta donde vive la portada | La portada vive en `LoginPage` y se sirve en **`/login`** bajo `PublicOnlyRoute`. **No cambiar `App.tsx`.** `/` sigue con `RequireAuth`: anónimo → `/login` (portada con modal abierto); autenticado → `/agenda?date=hoy`. Autenticado en `/login` → `PublicOnlyRoute` redirige a `from` válido o `/`. | (a) Hacer `/` la portada pública con modal cerrado. (b) Agregar una ruta nueva tipo `/bienvenida`. | H7/H8: `smoke.test.tsx` entra por `/` y depende del redirect a `/login`; `App.test.tsx` depende del orden `routes[0]=/login`, `routes[1]=/`. Cambiar rutas rompe tests que no se pueden tocar. La portada igual “reemplaza la pantalla de login”: es lo primero que ve un anónimo. |
| D3 | Estructura de componentes | Crear `frontend/src/features/landing/` con `LandingPage.tsx` + `LandingPage.module.css`, `LoginDialog.tsx` (+ estilos), `RevealSection.tsx` + `RevealSection.module.css`, `landingContent.ts` (datos tipados y ficticios) y `revealObserver.ts` (factory de `IntersectionObserver` con guarda). Tests nuevos en la misma carpeta. `LoginPage.tsx` queda como wrapper delgado que renderiza `LandingPage` con `initialLoginOpen`. | (a) Meter todo en `features/login/`. (b) Crear `pages/LandingPage.tsx`. | `LoginPage` debe seguir existiendo con la misma firma (`carouselTicker`, `prefersReducedMotion`) para no tocar `LoginPage.test.tsx` ni `LoginBrand.test.tsx`. `features/landing` separa presentación pública de sesión. |
| D4 | Colisión del botón “Ingresar” | El hero muestra un botón “Ingresar”. Mientras el modal está abierto, ese botón se marca `aria-hidden="true"` y `tabIndex={-1}` (en jsdom no hay inercia nativa como en `showModal`). Así `getByRole("button", { name: "Ingresar" })` resuelve solo al submit del form. | (a) `aria-label="Ingresar a mi cuenta"` en el botón del hero (la etiqueta visible queda contenida; evita la coincidencia exacta). (b) No renderizar el botón del hero mientras el modal está abierto. | H9: el test existente usa el nombre exacto “Ingresar” en 5 lugares. Con el modal abierto por defecto en `/login`, dos botones con ese nombre rompen `getByRole`. La opción recomendada refleja que el fondo está inactivo bajo un modal. |
| D5 | Jerarquía de headings | Hero: **`<h1>Aqua — Clínica Odontológica</h1>`**. Diálogo: **`<h2 id="login-heading">Turnos Odontología</h2>`** (el nombre que exigen `smoke` y `LoginBrand`). Secciones: `<h2>` cada una. | (a) Dejar `h1` “Turnos Odontología” en el diálogo y el hero con `<p>` estilizado. (b) Dos `h1`. | H11: los tests buscan por rol + nombre, no por nivel. Así queda un solo `h1` y no hay dos headings con el mismo nombre. |
| D6 | Reveal de las 4 secciones | `RevealSection` recibe un observador **inyectable** (misma idea que el `ticker`). Default: crea `IntersectionObserver` **solo si existe**; si no existe (jsdom) o hay `prefers-reduced-motion`, **no aplica clase pendiente** y el contenido queda visible. El contenido siempre está en el DOM; la clase `data-reveal="pending"` solo se aplica cuando hay observador y no hay reduced motion; al intersectar pasa a `revealed`. | (a) CSS-only con `animation-timeline: view()` (soporte dispar, no testeable). (b) Estado inicial `opacity:0` fijo (rompe `toBeVisible`). | H4/H6: jsdom no tiene `IntersectionObserver` y jest-dom trata `opacity:0` como invisible. El default visible mantiene los tests de contenido verdes y el observador inyectado permite testear la animación sin globals. |
| D7 | Foco, Esc y retorno de foco | Al abrir, foco a `#login-username` en un `useLayoutEffect` (el `autoFocus` del input puede fallar si el diálogo aún estaba cerrado). Esc: handler explícito `onKeyDown` + `onCancel` para cerrar. Al cerrar, foco al botón “Ingresar” del hero (ref). En navegador, `showModal()` aporta focus trap, backdrop e inercia. | (a) Depender solo del `cancel`/Esc nativo (no se puede testear en jsdom). (b) Focus trap manual propio. | jsdom no dispara `cancel` ni Esc nativo del diálogo; el handler explícito permite testear sin stubs. En navegador se conserva la semántica nativa. |
| D8 | Scroll con el modal abierto | Mientras el modal está abierto, bloquear el scroll del fondo (`document.body` con `overflow: hidden`, con cleanup) y, si hace falta, compensar el ancho de la barra de scroll. En navegador, `showModal()` ya hace inerte el resto. | (a) No bloquear scroll (riesgo de scroll del fondo, sobre todo en tablet). | Evita el doble scroll; se verifica visualmente en 1440 y 768. |
| D9 | Tokens de layout | Agregar a `tokens.css` tokens semánticos de portada (por ejemplo `--landing-hero-min-height: 60vh` y `--landing-content-max-width`). Cero colores nuevos: todo sale de la paleta de C-34. | (a) Usar `60vh` y anchos literales en el CSS module. | `tokens.test.ts` no prohíbe agregar tokens; mantiene la regla de no dejar tamaños sueltos y no toca la paleta. |
| D10 | Specs | **Nueva capability `frontend-landing`** con: portada pública en `/login`, hero con carrusel reutilizado, 4 secciones con datos ficticios marcados, diálogo de login (apertura/foco/Esc/retorno), reveal inyectable y reduced motion. **MODIFIED `frontend-auth-session`**: solo una nota de que `/login` hospeda la portada con el diálogo abierto y conserva el mensaje de vencimiento. `frontend-foundation` recibe un delta mínimo **solo si** se agregan tokens de portada (D9). | (a) Meter todo en `frontend-auth-session`. (b) Nueva capability y no tocar auth. | Separa presentación pública de la lógica de sesión (que no cambia). El comportamiento de auth queda igual y sus escenarios siguen trazables. |
| D11 | Marcas de demo | Badge visible **“Sitio de demostración”** en el hero y nota visible en “Horarios y contacto”: “Datos ficticios, solo para la demostración”. Nombres y prestaciones tomados del seed. | (a) Un texto pequeño solo al pie. | El requisito pide marcar visiblemente que los datos de contacto son ficticios. |
| D12 | Contenido de “Horarios” | Alinear con el seed: **lunes a viernes 9:00–13:00 y 15:00–19:00**; Dr. Sosa solo por la mañana. | (a) Horarios genéricos sin relación con el seed. | Evita contradicciones entre la portada y los datos de demo que usa la agenda. |

---

## 4. Textos propuestos (breves, rioplatense neutro, datos ficticios)

> Textos originales; no copiados de ningún sitio.

### Hero
- Logo claro (`logo-aqua-claro.png`, `alt="Aqua — Clínica Odontológica"`).
- `<h1>` **Aqua — Clínica Odontológica**
- Bajada (se conserva exacta para `LoginBrand`): **Claridad en cada cuidado.**
- Lead: “Turnos ordenados para que la atención fluya: elegí profesional, sillón y prestación, y el sistema evita superposiciones.”
- CTA: **Ingresar** (abre el diálogo; `aria-hidden` mientras está abierto, ver D4).
- Badge: **Sitio de demostración**

### Quiénes somos
“Aqua es una clínica odontológica de demostración. Coordinamos la agenda entre profesionales y sillones para que cada consulta tenga su tiempo y no haya superposiciones. Todos los nombres, horarios y datos de contacto de este sitio son ficticios.”

### Servicios
Intro: “Prestaciones de la demo, con la duración con la que el sistema reserva cada turno.”
- **Limpieza** — 45 min — “Profilaxis y control de sarro.”
- **Extracción** — 60 min — “Extracciones simples con indicaciones de cuidado.”
- **Restauración** — 60 min — “Recuperación de piezas dañadas.”
- **Control** — 30 min — “Revisión general y seguimiento.”
- **Blanqueamiento** — 90 min — “Tratamiento estético.”

### Equipo
- **Dr. Martín Sosa** — “Atiende de lunes a viernes por la mañana.”
- **Dra. Laura Quiroga** — “Atiende de lunes a viernes, mañana y tarde.”
- **Dra. Paula Benítez** — “Atiende de lunes a viernes, mañana y tarde.”
- Nota: “Nombres ficticios tomados de los datos de demostración.”

### Horarios y contacto
- “Lunes a viernes: 9:00 a 13:00 y 15:00 a 19:00.”
- “Dirección: Av. Ejemplo 1234, Ciudad Demo.”
- “Teléfono: (011) 5555-0101.”
- “Correo: turnos@aqua-demo.example.”
- Nota visible: “Datos de contacto ficticios, solo para la demostración. No agendar turnos reales.”

---

## 5. Rutas: qué pasa en cada caso (detalle de D2)

| URL | Sesión | Resultado |
|-----|--------|-----------|
| `/login` | anónima | Portada completa con el `<dialog>` de login **abierto** (heading “Turnos Odontología”, form y foco en `Usuario`). Es el destino del redirect de sesión vencida; el mensaje cae en el form. |
| `/login` | `checking` | `PublicOnlyRoute` muestra `LoadingState`; **no** se muestra el form (conserva “sin parpadeo de login a home”). |
| `/login` | autenticada | `PublicOnlyRoute` redirige a `state.from` válido o `/`. |
| `/` | anónima | `RequireAuth` redirige con `replace` a `/login` con `from` y `expired`; el usuario ve la portada. |
| `/` | autenticada | `RootRedirect` → `/agenda?date=<hoy>`. |
| `/agenda?date=…` | anónima | Redirect a `/login` con `from`; luego de loguear vuelve al destino. |
| ruta desconocida | autenticada | `NotFoundPage` dentro de `AppShell` (sin cambios). |
| ruta desconocida | anónima | El `*` vive bajo `/` (`RequireAuth`), así que primero redirige a `/login`. |

No se propone ninguna ruta nueva. La portada “pública” se obtiene porque `/login` está bajo `PublicOnlyRoute` y todo anónimo que entra a `/` termina ahí.

---

## 6. Escenarios candidatos

### 6.1 Testeables en jsdom (Vitest + Testing Library, regla C1)
- **T1 — Portada en `/login`**: renderiza hero (logo claro, `<h1>` de marca, bajada exacta), las 4 secciones y el diálogo abierto con heading “Turnos Odontología” y form accesible.
- **T2 — Abrir el diálogo**: con el diálogo cerrado, el botón “Ingresar” del hero lo abre; al abrir, `Usuario` tiene el foco.
- **T3 — Esc cierra y devuelve el foco**: `keydown` Escape cierra el diálogo y el foco vuelve al botón “Ingresar”.
- **T4 — Heading accesible del diálogo**: el `<dialog>` referencia el heading (`aria-labelledby`) y expone rol `dialog` (si hace falta, `role="dialog"` explícito).
- **T5 — Sin colisión de “Ingresar”**: con el modal abierto, `getByRole("button", { name: "Ingresar" })` es único (submit del form).
- **T6 — Secciones siempre en el DOM**: con el entorno por defecto (sin `IntersectionObserver`) las 4 secciones y sus headings son visibles, sin clase pendiente.
- **T7 — Reveal con observador inyectado**: estado `data-reveal="pending"` al montar con observador; al disparar la intersección pasa a `revealed`; el cleanup se llama al desmontar.
- **T8 — Reduced motion / sin observador**: no se aplica clase pendiente; todo visible.
- **T9 — Datos demo**: aparece el badge “Sitio de demostración”, la nota de datos ficticios y los tres profesionales del seed.
- **T10 — Regresión de ruteo**: anónimo en `/` termina en `/login` con la portada (ya cubierto por `smoke`); autenticado en `/login` redirige (ya cubierto por `App.test`). No se duplican.
- **T11 — Regresión completa**: `LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `App.test.tsx` y `smoke.test.tsx` sin modificar y en verde.

### 6.2 Verificación visual (1440 px y 768 px; no medible en jsdom)
- **V1** Hero ≈ 60vh en escritorio; carrusel de C-34 sin recortes; overlay legible; CTA visible.
- **V2** Modal centrado, backdrop, tarjeta vidrio, foco visible; sin overflow horizontal a 768.
- **V3** Cuatro secciones con jerarquía y espaciado; reveal suave al scrollear; sin saltos de layout.
- **V4** Responsive: hero, equipo y contacto legibles a 768; el modal entra completo.
- **V5** Reduced motion: sin reveal ni Ken Burns; contenido visible.
- **V6** Marcas de demo y contacto ficticio visibles.
- **V7** Cero colores fuera de tokens (grep + inspección visual).

---

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Dos botones “Ingresar” (hero + submit) | `LoginPage.test.tsx` falla por múltiples coincidencias | D4: `aria-hidden` + `tabIndex={-1}` en el CTA del hero mientras el modal está abierto. |
| `smoke.test.tsx` entra por `/` y el heading podría quedar dentro de un diálogo cerrado (`display:none`) | El heading no se encuentra por rol | D2 + D5: `/` sigue redirigiendo a `/login`, que monta el diálogo abierto; el heading es “Turnos Odontología”. No montar la portada con modal cerrado en `/`. |
| `App.test.tsx` depende del orden de rutas y del alert de sesión vencida | Tests de auth y de ruteo rotos | D2: no reordenar ni insertar rutas antes de `/`; el diálogo abierto en `/login` mantiene el `role="alert"` accesible (H3). |
| jsdom sin `showModal()`/`close()` | `TypeError` al abrir/cerrar | D1: detección de capacidad + atributo `open` como fallback; sin `vi.stubGlobal`. |
| jsdom sin `IntersectionObserver` y `toBeVisible` con `opacity:0` | Secciones invisibles o tests frágiles | D6: default visible sin observador; el observador se inyecta solo en los tests de reveal. |
| `autoFocus` del input con el diálogo aún cerrado | El foco no queda en `Usuario` (test línea 312) | D7: foco explícito en el efecto de apertura (`useLayoutEffect`). |
| Focus trap y Esc solo reales con `showModal()` | En jsdom no se prueba el atrapado nativo | D7: handler explícito de Esc y de retorno de foco; el focus trap nativo se valida visual/manualmente en navegador. |
| Bloquear el scroll del body | Salto de layout al ocultar la barra de scroll | D8: aplicar `overflow:hidden` con compensación opcional; verificar en 1440/768. |
| Ocultar todo el hero con `aria-hidden` para resolver D4 | `LoginBrand` no encontraría el logo ni “Pausar animación” (H10) | Ocultar **solo** el CTA del hero, nunca el hero completo. |
| Textos prohibidos por tests existentes | `LoginPage.test` prohíbe checkbox y “recordar”; `App.test` prohíbe “Bienvenida” | No incluir “recordar”, checkboxes, “Bienvenida” ni un segundo `<form>` en la portada. |
| Fotos del hero (5 webp) | Peso y posible CLS | Ya existen desde C-34; fijar `aspect-ratio`/dimensiones del hero, medir build y revisar red en la verificación visual. No se agregan fotos nuevas. |
| Dependencia de C-34 en curso | Tokens, carrusel y reduced motion podrían cambiar | C-35 se implementa **después** de archivar/sincronizar C-34; este explore se apoyó en la rama `c34-apply`. |
| Context7 | — | Se consultó React Router v6 (`/websites/reactrouter/6.30.3`): confirma rutas anidadas con `<Outlet />` y `Navigate` con `replace`/`state`. No se enviaron datos sensibles. |

---

## 8. Resumen para la autora

- **No hace falta tocar `App.tsx`**: la portada reemplaza la pantalla de `/login`; `/` sigue protegido y manda al anónimo a la portada. Esto evita romper `smoke` y `App.test`.
- **El modal se puede usar sin stubs**: jsdom 31 no tiene `showModal()`, pero sí el elemento `<dialog>`; abrir con `showModal()` cuando existe y con el atributo `open` cuando no, deja el form accesible.
- **Dos ajustes finos evitan regresiones**: el CTA “Ingresar” del hero se oculta a los queries mientras el modal está abierto, y el heading “Turnos Odontología” se conserva como heading del diálogo.
- **El reveal no puede depender de jsdom**: sin `IntersectionObserver` o con reduced motion, las 4 secciones se muestran sin animación; el observador se inyecta para testear.
- **Specs**: nueva `frontend-landing`; delta mínimo en `frontend-auth-session`; `frontend-foundation` solo si se agregan tokens de portada.

Freno acá. No sigo al propose hasta que confirmes la tabla de decisiones.
