# Verificación C-35 — ui-portada-y-acceso

## Estado

- Change: `ui-portada-y-acceso`
- Rama: `c35-apply`
- Tasks 1.1 a 10.4: completadas. Task 11.1 (capturas 1440, 768 y 390 px) queda pendiente a cargo de Claude; sin capturas aprobadas no se archiva C-35.
- Tests nuevos: 24 (7 `LandingPage`, 5 `LoginDialog`, 3 `Dialog`, 3 `RevealSection`, 3 `landingContent`, 3 `landingTokens`), sobre 41 archivos y 164 tests de baseline; la suite final tiene 47 archivos y 188 tests.
- Tests existentes intocables: `LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `App.test.tsx` y `smoke.test.tsx`; los cinco quedaron verdes y sin cambios.
- Datos de pacientes: no se usan datos reales; la portada usa únicamente datos ficticios del seed.

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `el equipo coincide con el seed` | `frontend/src/features/landing/landingContent.ts` | `-    name: "Dr. Martín Sosa", +    name: "Dr. Martín Sosa ",` | `AssertionError: expected [ 'Dr. Martín Sosa ', …(2) ] to deeply equal [ 'Dr. Martín Sosa',` |
| 2 | `los servicios y duraciones coinciden con el seed` | `frontend/src/features/landing/landingContent.ts` | `-    durationMinutes: 45, +    durationMinutes: 46,` | `AssertionError: expected [ [ 'Limpieza', 46 ], …(4) ] to deeply equal [ [ 'Limpieza', 45 ]` |
| 3 | `horarios y contacto son ficticios y coinciden con el seed` | `frontend/src/features/landing/landingContent.ts` | `-  phone: "(0261) 555-0101", +  phone: "(0261) 555-0102",` | `AssertionError: expected { …(3) } to deeply equal { …(3) }` |
| 4 | `define los dos tokens de layout` | `frontend/src/shared/styles/tokens.css` | `-  --landing-hero-min-height: 60vh; +  --landing-hero-min-height: 61vh;` | `AssertionError: expected '61vh' to be '60vh' // Object.is equality` |
| 5 | `la portada usa los tokens de layout` | `frontend/src/features/landing/LandingPage.module.css` | `-  min-height: var(--landing-hero-min-height); +  min-height: 60vh;` | `AssertionError: expected '.page {\n  min-height: 100vh;\n  colo…' to contain 'var(--landin` |
| 6 | `no agrega colores nuevos` | `frontend/src/shared/styles/tokens.css` | `+  --landing-danger: #ff0000;` | `AssertionError: expected [ '--landing-danger' ] to deeply equal []` |
| 7 | `muestra la marca una sola vez, la bajada, el lead y el CTA` | `frontend/src/features/landing/LandingPage.tsx` | `-          <p className={styles.tagline}>Claridad en cada cuidado.</p> +          <p class` | `Error: expect(element).toBeVisible()` |
| 8 | `marca el sitio y los datos de contacto como demostración` | `frontend/src/features/landing/LandingPage.tsx` | `-          <p className={styles.demoNote}>{demoContactNote}</p> +          <p className={s` | `Error: expect(element).toBeVisible()` |
| 9 | `muestra las cuatro secciones informativas visibles sin IntersectionObserver` | `frontend/src/features/landing/RevealSection.tsx` | `-  const [revealed, setRevealed] = useState(!canAnimate); +  const [revealed, setRevealed]` | `AssertionError: expected …(4) to have a length of +0 but got 4` |
| 10 | `reutiliza el carrusel de cinco fotos y su botón de pausa` | `frontend/src/features/login/LoginCarousel.tsx` | `-const SLIDES = [hero1, hero2, hero3, hero4, hero5]; +const SLIDES = [hero1, hero2, hero3,` | `AssertionError: expected <img …(6)></img>` |
| 11 | `abre el acceso al entrar y lo reabre con el CTA` | `frontend/src/features/landing/LandingPage.tsx` | `-          setIsLoginOpen(false); +          setIsLoginOpen(true);` | `Error: expect(element).not.toHaveAttribute("open") // element.hasAttribute("open")` |
| 12 | `mantiene un único botón Ingresar y un CTA accesible sin ocultar` | `frontend/src/features/landing/LandingPage.tsx` | `+            tabIndex={-1}` | `Error: expect(element).not.toHaveAttribute("tabindex", "-1") // element.getAttribute("tabi` |
| 13 | `LoginPage monta la portada y conserva el aviso de sesión vencida` | `frontend/src/features/login/LoginPage.tsx` | `-      initialNotice={showExpiredMessage ? SESSION_EXPIRED_MESSAGE : null} +      initialN` | `Error: expect(element).toHaveTextContent()` |
| 14 | `abre con el diálogo, el heading, el formulario y el botón para recorrer la clínica` | `frontend/src/shared/components/Dialog.tsx` | `-      aria-labelledby={labelledBy} +      aria-labelledby={undefined}` | `Error: expect(element).toHaveAttribute("aria-labelledby", "login-heading") // element.getA` |
| 15 | `cierra el diálogo con el botón Ver la clínica` | `frontend/src/features/landing/LoginDialog.tsx` | `-          <button type="button" className={styles.close} onClick={onClose}> +          <b` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| 16 | `muestra el aviso de sesión vencida dentro del formulario` | `frontend/src/features/landing/LoginDialog.tsx` | `-          <LoginForm onSubmit={onLogin} initialNotice={initialNotice} /> +          <Logi` | `Error: expect(element).toHaveTextContent()` |
| 17 | `enfoca Usuario al abrir` | `frontend/src/features/landing/LoginDialog.tsx` | `-    document.getElementById("login-username")?.focus(); +    void document.getElementById` | `Error: expect(element).toHaveFocus()` |
| 18 | `bloquea el overflow del body mientras está abierto y lo restaura al cerrar` | `frontend/src/features/landing/LoginDialog.tsx` | `-    document.body.style.overflow = "hidden"; +    document.body.style.overflow = "visible` | `AssertionError: expected 'visible' to be 'hidden' // Object.is equality` |
| 19 | `se renderiza abierto sin depender de showModal y expone sus atributos accesibles` | `frontend/src/shared/components/Dialog.tsx` | `-      aria-modal="true" +      aria-modal="false"` | `Error: expect(element).toHaveAttribute("aria-modal", "true") // element.getAttribute("aria` |
| 20 | `cierra con Escape y devuelve el foco al disparador` | `frontend/src/shared/components/Dialog.tsx` | `-    if (event.key !== "Escape") { +    if (event.key === "Escape") {` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| 21 | `atiende cancel y refleja el cierre sin close() nativo` | `frontend/src/shared/components/Dialog.tsx` | `-      onCancel={handleCancel} +      onCancel={() => undefined}` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| 22 | `sin IntersectionObserver queda revelada y su contenido es visible` | `frontend/src/features/landing/RevealSection.tsx` | `-  const [revealed, setRevealed] = useState(!canAnimate); +  const [revealed, setRevealed]` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
| 23 | `con observador inyectado pasa de pendiente a revelada y limpia al desmontar` | `frontend/src/features/landing/RevealSection.tsx` | `-    return instance.observe(section, () => { -      setRevealed(true); -    }); +    retu` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
| 24 | `con movimiento reducido no queda pendiente y el contenido está en el DOM` | `frontend/src/features/landing/RevealSection.tsx` | `-  const [revealed, setRevealed] = useState(!canAnimate); +  const [revealed, setRevealed]` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
<!-- mutaciones:fin -->

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Requisito | Escenario | Test | Mutación |
|---|---|---|---|---|
| 1 | Bajada y tarjeta del login | La bajada es visible | `src/features/login/LoginBrand.test.tsx > muestra el logo claro, el heading accesible y la bajada` | — (test existente) |
| 2 | Bajada y tarjeta del login | La tarjeta tipo vidrio sobre overlay navy | `— (verificación visual)` | — |
| 3 | Tokens de layout de la portada | Los tokens de layout existen | `src/shared/styles/landingTokens.test.ts > define los dos tokens de layout` | 4 |
| 4 | Tokens de layout de la portada | La portada usa los tokens de layout | `src/shared/styles/landingTokens.test.ts > la portada usa los tokens de layout` | 5 |
| 5 | Tokens de layout de la portada | No se agregan colores nuevos | `src/shared/styles/landingTokens.test.ts > no agrega colores nuevos` | 6 |
| 6 | Diálogo modal reutilizable | Sin showModal el diálogo usa el atributo open | `src/shared/components/Dialog.test.tsx > se renderiza abierto sin depender de showModal y expone sus atributos accesibles` | 19 |
| 7 | Diálogo modal reutilizable | Escape cierra y devuelve el foco | `src/shared/components/Dialog.test.tsx > cierra con Escape y devuelve el foco al disparador` | 20 |
| 8 | Diálogo modal reutilizable | El evento cancel cierra | `src/shared/components/Dialog.test.tsx > atiende cancel y refleja el cierre sin close() nativo` | 21 |
| 9 | Portada pública en /login | La portada se muestra en /login | `src/features/landing/LandingPage.test.tsx > LoginPage monta la portada y conserva el aviso de sesión vencida` | 13 |
| 10 | Portada pública en /login | El anónimo en / sigue llegando a la portada | `src/App.test.tsx > ruta protegida sin sesión conserva el destino` | — (test existente) |
| 11 | Portada pública en /login | El autenticado en /login no ve la portada | `src/App.test.tsx > login con sesión vuelve al destino válido` | — (test existente) |
| 12 | Hero con marca, carrusel y llamada a la acción | La marca se anuncia una sola vez | `src/features/landing/LandingPage.test.tsx > muestra la marca una sola vez, la bajada, el lead y el CTA` | 7 |
| 13 | Hero con marca, carrusel y llamada a la acción | El CTA y el submit tienen nombres distintos | `src/features/landing/LandingPage.test.tsx > mantiene un único botón Ingresar y un CTA accesible sin ocultar` | 12 |
| 14 | Hero con marca, carrusel y llamada a la acción | El carrusel del hero se reutiliza | `src/features/landing/LandingPage.test.tsx > reutiliza el carrusel de cinco fotos y su botón de pausa` | 10 |
| 15 | Hero con marca, carrusel y llamada a la acción | El hero mide al menos 60vh | `— (verificación visual)` | — |
| 16 | Hero con marca, carrusel y llamada a la acción | El badge de demostración es visible | `src/features/landing/LandingPage.test.tsx > marca el sitio y los datos de contacto como demostración` | 8 |
| 17 | Secciones informativas con datos ficticios | Las cuatro secciones están en el DOM | `src/features/landing/LandingPage.test.tsx > muestra las cuatro secciones informativas visibles sin IntersectionObserver` | 9 |
| 18 | Secciones informativas con datos ficticios | El equipo coincide con el seed | `src/features/landing/landingContent.test.ts > el equipo coincide con el seed` | 1 |
| 19 | Secciones informativas con datos ficticios | Los servicios y duraciones coinciden con el seed | `src/features/landing/landingContent.test.ts > los servicios y duraciones coinciden con el seed` | 2 |
| 20 | Secciones informativas con datos ficticios | Los horarios coinciden con el seed | `src/features/landing/landingContent.test.ts > horarios y contacto son ficticios y coinciden con el seed` | 3 |
| 21 | Secciones informativas con datos ficticios | Los datos ficticios se marcan visiblemente | `src/features/landing/LandingPage.test.tsx > marca el sitio y los datos de contacto como demostración ; src/features/landing/landingContent.test.ts > horarios y contacto son ficticios y coinciden con el seed` | 8 ; 3 |
| 22 | Diálogo de acceso | El diálogo se abre al entrar | `src/features/landing/LoginDialog.test.tsx > abre con el diálogo, el heading, el formulario y el botón para recorrer la clínica` | 14 |
| 23 | Diálogo de acceso | Ver la clínica cierra el diálogo | `src/features/landing/LandingPage.test.tsx > abre el acceso al entrar y lo reabre con el CTA` | 11 |
| 24 | Diálogo de acceso | El mensaje de sesión vencida cae en el formulario | `src/features/landing/LoginDialog.test.tsx > muestra el aviso de sesión vencida dentro del formulario` | 16 |
| 25 | Diálogo de acceso | Los nombres de los botones no colisionan | `src/features/landing/LandingPage.test.tsx > mantiene un único botón Ingresar y un CTA accesible sin ocultar` | 12 |
| 26 | Diálogo de acceso | El diálogo tiene backdrop y tarjeta tipo vidrio | `— (verificación visual)` | — |
| 27 | Diálogo de acceso | El foco queda atrapado en el diálogo | `— (verificación visual)` | — |
| 28 | Foco y scroll del diálogo de acceso | El foco inicia en Usuario | `src/features/landing/LoginDialog.test.tsx > enfoca Usuario al abrir` | 17 |
| 29 | Foco y scroll del diálogo de acceso | El scroll del fondo queda bloqueado | `src/features/landing/LoginDialog.test.tsx > bloquea el overflow del body mientras está abierto y lo restaura al cerrar` | 18 |
| 30 | Reveal accesible de secciones | Sin IntersectionObserver las secciones quedan visibles | `src/features/landing/RevealSection.test.tsx > sin IntersectionObserver queda revelada y su contenido es visible` | 22 |
| 31 | Reveal accesible de secciones | Con observador inyectado pasa a revelado y limpia | `src/features/landing/RevealSection.test.tsx > con observador inyectado pasa de pendiente a revelada y limpia al desmontar` | 23 |
| 32 | Reveal accesible de secciones | Reduced motion evita el estado pendiente | `src/features/landing/RevealSection.test.tsx > con movimiento reducido no queda pendiente y el contenido está en el DOM` | 24 |
| 33 | Reveal accesible de secciones | El contenido sigue en el DOM durante la animación | `src/features/landing/RevealSection.test.tsx > con observador inyectado pasa de pendiente a revelada y limpia al desmontar` | 23 |
| 34 | Reveal accesible de secciones | La animación de reveal es visual | `— (verificación CSS/grep)` | — |
<!-- trazabilidad:fin -->

## Verificación visual y CSS

| Escenario | Verificación |
|---|---|
| El hero mide al menos 60vh | Pendiente: captura 1440/768/390 px (task 11.1) |
| El diálogo tiene backdrop y tarjeta tipo vidrio | Pendiente: captura 1440/768/390 px (task 11.1) |
| El foco queda atrapado en el diálogo | Pendiente: captura con `showModal` (task 11.1) |
| El scroll del fondo queda bloqueado | Test de `LoginDialog` (overflow `hidden` y restauración) + captura pendiente (task 11.1) |
| La animación de reveal es visual | Pendiente: captura con scroll (task 11.1) |
| La tarjeta tipo vidrio sobre overlay navy | Pendiente: captura (task 11.1) |
| CSS del reveal y reduced motion | `RevealSection.module.css` y `prefers-reduced-motion`; test de reduced motion |

## Desvíos

1. **D4 — CTA del hero.** El explore proponía “Ingresar” oculto con `aria-hidden` y `tabIndex={-1}`. La implementación usa “Ingresar al sistema”, visible y accesible, para que el submit conserve el nombre único “Ingresar” sin quitar el CTA del árbol de accesibilidad.
2. **D5 — `<h1>` con logo.** El explore proponía un `<h1>` con texto “Aqua — Clínica Odontológica”. La implementación pone el logo claro dentro del `<h1>` con `alt="Aqua — Clínica Odontológica"`; la marca se anuncia una sola vez y el diálogo conserva `<h2>Turnos Odontología</h2>`.
3. **“Ver la clínica”.** No estaba en el explore. Se agrega como cierre visible del diálogo para recorrer la portada sin depender de Escape; el CTA “Ingresar al sistema” lo reabre.
4. **Ajuste técnico de lint (L1).** `LoginCarousel.tsx` exportaba `createIntervalTicker` junto al componente, lo que producía un warning preexistente de `react-refresh/only-export-components` y hacía fallar `npm run lint --max-warnings 0`. Se movió el helper y su tipo a `carouselTicker.ts`; `LoginCarousel` reexporta solo el tipo. No cambia comportamiento; los tests del carrusel siguen verdes.

## Comandos

| Comando | Código | Evidencia |
|---|---|---|
| `npm run test:run` (baseline) | 1 | 41 archivos y 164 tests verdes; el proceso sale 1 por `[vitest-worker]: Timeout calling "onTaskUpdate"`, anomalía preexistente; `baseline-C-35.txt` |
| `npm run test:run` (C-35) | 0 | 47 archivos y 188 tests verdes; `suite-C-35.txt` |
| `npm run typecheck` | 0 | `typecheck-C-35.txt` |
| `npm run lint` | 0 | 0 errores, 0 warnings tras L1; `lint-C-35.txt` y `eslint-C-35.txt` |
| `npm run build` | 0 | `build-C-35.txt`; assets y fuentes empaquetados por Vite |
| `python docs/evidencias/mutaciones-C-35.py --check` | 0 | 24 mutaciones bien definidas |
| `python docs/evidencias/mutaciones-C-35.py` | 0 | 24/24 mutaciones muertas, 0 inválidas, SHA-256 sin cambios: si; `mutaciones-C-35.txt` |
| `python docs/evidencias/trazabilidad-C-35.py` | 0 | 34 escenarios, 0 problemas; `trazabilidad-C-35.txt` |
| `openspec validate --all --strict` | 0 | 16 elementos (14 specs + 2 changes), 0 fallos; `openspec-C-35.txt` |
| Regresión de tests intocables | 0 | 5 archivos, 20 tests; `regresion-cinco.txt` |
| `git diff --stat` de tests intocables | 0 | sin cambios |
| UTF-8 de evidencias C-35 | 0 | 55 archivos `.txt`, `.md` y `.py` en UTF-8; 0 no UTF-8 |

## Notas

- El baseline `npm run test:run` terminó con código 1 por un timeout del worker de Vitest al reportar tareas, aunque los 41 archivos y 164 tests pasaron. La anomalía es previa a C-35 y no se modificó.
- `App.tsx` no se tocó: `routes[0]` sigue siendo `/login` y `routes[1]` `/`. La portada se monta desde `LoginPage`.
- La validación global incluye el change ajeno `ui-dar-turno-con-errores`; por eso son 16 elementos y no 15. No se tocó ese change.
- Las capturas de 11.1 se harán después, con el build levantado; no se ejecutaron en este apply.
- No se agregaron dependencias. No se tocaron `.env`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, el backend, Docker ni el cliente de API.
