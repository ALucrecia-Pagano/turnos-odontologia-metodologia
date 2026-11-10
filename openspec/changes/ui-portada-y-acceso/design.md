# Design

## Context

C-34 dejó el sistema de tokens, la tipografía autoalojada, el logo claro y el carrusel de cinco fotos. Hoy `LoginPage` (`frontend/src/features/login/LoginPage.tsx`) renderiza el carrusel, la marca y una tarjeta con `LoginForm` en `/login`. C-35 reemplaza esa pantalla por una portada pública y mueve el formulario a un `<dialog>` que se abre al entrar.

Restricciones que mandan sobre el diseño:

- `App.tsx` no se toca: `routes[0]` es `/login` y `routes[1]` es `/`; `App.test.tsx:186-192` depende de ese orden.
- `LoginPage.test.tsx` consulta `getByRole("button", { name: "Ingresar" })` (líneas 101, 138, 195, 224, 259), espera el foco en Usuario (312), un único form “Iniciar sesión” (267) y prohíbe checkbox/“recordar” (314-316).
- `LoginBrand.test.tsx:56-63,71` espera el logo por rol y nombre, el heading “Turnos Odontología”, la bajada exacta y “Pausar animación”.
- `smoke.test.tsx:7` entra por `/`, es redirigido a `/login` y busca el heading “Turnos Odontología”.
- Regla C1: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, timers falsos ni MSW.
- jsdom 31: `HTMLDialogElement` existe, pero `showModal()`/`close()` son `undefined`; `IntersectionObserver` y `matchMedia` no existen.

## Goals / Non-goals

**Goals:** portada pública en `/login`, hero con marca única y CTA, cuatro secciones con datos ficticios, diálogo de acceso abierto al entrar, foco/Escape/retorno, reveal accesible, tokens de layout y cero regresiones en tests existentes.

**Non-goals:** tema oscuro y responsive de celular (C-36), formulario de dar turno (C-29), acciones de agenda (C-30), cambios de autenticación, API, dominio, Docker o `.env`.

## Decisions

### D1 — `<dialog>` nativo con fallback por capacidad

La solución usa un `<dialog>` real. La mecánica de apertura/cierre, el fallback por capacidad y el retorno de foco viven en la primitiva `Dialog` (D13); `LoginDialog` la compone. No se reemplazan globals ni se stubea `showModal`. La guarda `dialog.open` evita dobles llamadas. En jsdom el atributo `open` alcanza para que el formulario sea accesible; en un navegador real `showModal()` aporta el focus trap y el backdrop nativos.

**Alternativa descartada:** un modal propio con `div` + `role="dialog"`; pierde el focus trap y el `cancel` nativos y agrega más código que el fallback.

### D2 — La portada vive en `/login` y el diálogo abre al entrar

`LoginPage` pasa a ser un wrapper delgado de `LandingPage`; no se agregan rutas ni se reordena `createAppRoutes`. `LandingPage` mantiene `const [isLoginOpen, setIsLoginOpen] = useState(true)`, así el anónimo que llega desde `/` ve la portada con el acceso abierto. El diálogo incluye un botón visible **“Ver la clínica”** que lo cierra para recorrer la portada; el CTA del hero **“Ingresar al sistema”** lo reabre.

**Alternativa descartada:** montar la portada con el modal cerrado en `/`; `smoke.test.tsx` dejaría de encontrar el heading “Turnos Odontología” por rol.

### D3 — Estructura de la feature

```
frontend/src/shared/components/
├── Dialog.tsx
├── Dialog.module.css
└── Dialog.test.tsx

frontend/src/features/landing/
├── LandingPage.tsx
├── LandingPage.module.css
├── LoginDialog.tsx
├── LoginDialog.module.css
├── RevealSection.tsx
├── RevealSection.module.css
├── landingContent.ts
├── revealObserver.ts
├── LandingPage.test.tsx
├── LoginDialog.test.tsx
├── RevealSection.test.tsx
└── landingContent.test.ts
```

`LoginPage.tsx` conserva `LoginPageProps` (`carouselTicker`, `prefersReducedMotion`), calcula `showExpiredMessage` igual que hoy y renderiza `<LandingPage ... initialNotice={...} />`. `LoginForm.tsx` y `LoginCarousel.tsx` no se modifican; `LandingPage` importa `LoginCarousel` desde `../login/LoginCarousel` y `LoginDialog` compone `Dialog` (desde `../../shared/components/Dialog`) y `LoginForm` (desde `../login/LoginForm`).

### D4 — CTA “Ingresar al sistema”, sin ocultar el hero

El CTA del hero dice **“Ingresar al sistema”** y el submit del form sigue diciendo **“Ingresar”**. El CTA no lleva `aria-hidden` ni `tabIndex={-1}`. Así `getByRole("button", { name: "Ingresar" })` sigue siendo único (el submit) y el CTA tiene un nombre accesible distinto que describe su acción. Ver “Desvíos respecto del explore”.

### D5 — El `<h1>` contiene el logo y la marca se anuncia una vez

```
<h1 id="hero-heading" className={styles.heroTitle}>
  <img src={logoAquaClaro} alt="Aqua — Clínica Odontológica" className={styles.logo} />
</h1>
```

El nombre accesible del `h1` sale del `alt`; no se repite “Aqua — Clínica Odontológica” en texto al lado. El diálogo conserva `<h2 id="login-heading">Turnos Odontología</h2>`, que es el heading que buscan `LoginBrand`, `smoke` y `LoginPage.test`. Cada sección informativa tiene su `<h2>`. Ver “Desvíos respecto del explore”.

### D6 — Reveal con observador inyectable

`revealObserver.ts` define:

```
export interface RevealObserver {
  observe(element: Element, onReveal: () => void): () => void;
}
export type RevealObserverFactory = () => RevealObserver | null;
export const browserRevealObserver: RevealObserverFactory;
export function detectPrefersReducedMotion(): boolean;
```

`RevealSection` recibe `observer?: RevealObserverFactory`, `reducedMotion?: boolean` y `children`. Calcula `canAnimate = !reducedMotion && (observer !== undefined || typeof IntersectionObserver !== "undefined")`; el estado inicial es `revealed = !canAnimate`. Si `canAnimate`, el `useEffect` crea el observador, observa el elemento y devuelve el cleanup. Si la fábrica devuelve `null`, revela de inmediato. El contenido siempre está en el DOM; el estado se expone con `data-reveal="pending"|"revealed"` y el CSS solo cambia opacidad/transform.

**Alternativa descartada:** leer `IntersectionObserver` solo dentro del efecto y arrancar en `pending`; en jsdom las secciones quedarían con `opacity:0` y `toBeVisible` fallaría.

### D7 — Foco en Usuario y retorno de foco

`LoginDialog` compone `Dialog` con `labelledBy="login-heading"` y `returnFocusRef` apuntando al CTA “Ingresar al sistema”. El foco inicial en Usuario queda en `LoginDialog`: un `useLayoutEffect` sobre `open` busca `document.getElementById("login-username")` y lo enfoca. No se confía en `autoFocus`, que puede ejecutarse antes de que el diálogo esté abierto. Escape, `cancel` y el retorno de foco a `returnFocusRef` los resuelve `Dialog` (D13).

### D8 — Bloqueo del scroll del fondo

Mientras `open`, `LoginDialog` (no `Dialog`) guarda `document.body.style.overflow`, lo pone en `"hidden"` y lo restaura en el cleanup. La compensación de la barra de scroll es opcional y se valida en la captura de 1440/768; no se simula scroll en jsdom.

### D9 — Tokens de layout, cero colores nuevos

Se agregan a `frontend/src/shared/styles/tokens.css`:

```
--landing-hero-min-height: 60vh;
--landing-content-max-width: 1120px;
```

No se agregan custom properties de color. `LandingPage.module.css` usa `var(--landing-hero-min-height)` en el hero y `var(--landing-content-max-width)` en el contenedor; el resto sale de los tokens de C-34 (`--color-navy`, `--color-primary-contrast`, `--space-*`, etc.).

### D10 — Deltas de specs

- `frontend-landing` (nueva): seis requisitos —portada en `/login`, hero con marca/carrusel/CTA, secciones con datos ficticios, diálogo de acceso, apertura/cierre/foco y reveal accesible— con escenarios GIVEN/WHEN/THEN. Los escenarios de alto del hero, backdrop/tarjeta vidrio, focus trap nativo, scroll bloqueado y animación de reveal se marcan “verificación visual (captura)”.
- `frontend-auth-session` (MODIFIED): solo “Bajada y tarjeta del login”, copiado completo con sus dos escenarios y ajustado a que la bajada queda en el hero y la tarjeta en el diálogo. No se toca “Logo del login sobre fondo oscuro”: el logo sigue sobre fondo oscuro, informativo, y el heading “Turnos Odontología” se conserva en el diálogo.
- `frontend-foundation` (ADDED): “Tokens de layout de la portada”, con los dos tokens y la prohibición de colores nuevos.

### D11 — Marcas de demostración

El badge **“Sitio de demostración”** va en el hero. En “Horarios y contacto” se muestra la nota **“Datos de contacto ficticios, solo para la demostración. No agendar turnos reales.”** El teléfono es **(0261) 555-0101**; la dirección y el correo salen del explore (“Av. Ejemplo 1234, Ciudad Demo”, “turnos@aqua-demo.example”).

### D12 — Contenido del seed

Profesionales: Dr. Martín Sosa (solo mañana), Dra. Laura Quiroga y Dra. Paula Benítez. Servicios y duraciones: Limpieza 45, Extracción 60, Restauración 60, Control 30, Blanqueamiento 90. Horarios: lunes a viernes de 9:00 a 13:00 y de 15:00 a 19:00. Los textos salen del explore §4, con el teléfono cambiado a (0261) 555-0101.

### D13 — Primitiva `Dialog` compartida

`frontend/src/shared/components/Dialog.tsx` (+ `Dialog.module.css` y `Dialog.test.tsx`) es la única implementación del `<dialog>` modal. C-29 (dar turno) y C-30 (reprogramar) la reutilizan; no debe haber dos modales.

Props: `open: boolean`, `onClose: () => void`, `labelledBy: string`, `returnFocusRef?: RefObject<HTMLElement>` y `children: ReactNode`.

- Aplica `role="dialog"`, `aria-modal="true"` y `aria-labelledby={labelledBy}`.
- Abre con `showModal()` si es función; si no (jsdom 31), con `setAttribute("open", "")`.
- Cierra con `close()` si existe; si no, `removeAttribute("open")`.
- `onKeyDown` de Escape y `onCancel` (Escape nativo) llaman a `onClose()` con `preventDefault()`.
- Al cerrar, el foco vuelve a `returnFocusRef.current`.
- Sin focus trap manual: con `showModal()` lo hace el navegador.
- Sin estilos de la portada: el backdrop y la tarjeta vidrio son de `LoginDialog`, que compone `Dialog`; el scroll lock y el foco en Usuario también quedan en `LoginDialog`.

**Alternativa descartada:** dejar la lógica del `<dialog>` dentro de `LoginDialog`; C-29 y C-30 tendrían que copiarla y aparecerían dos implementaciones divergentes.

## Rutas (sin cambios)

| URL | Sesión | Resultado |
|-----|--------|-----------|
| `/login` | anónima | Portada completa con el `<dialog>` abierto, heading “Turnos Odontología”, form y foco en Usuario. |
| `/login` | `checking` | `PublicOnlyRoute` muestra `LoadingState`; no se muestra el form. |
| `/login` | autenticada | `PublicOnlyRoute` redirige a `state.from` válido o `/`. |
| `/` | anónima | `RequireAuth` redirige con `replace` a `/login` con `from` y `expired`; se ve la portada. |
| `/` | autenticada | `RootRedirect` → `/agenda?date=<hoy>`. |
| `/agenda?date=…` | anónima | Redirect a `/login` con `from`; después del login vuelve al destino. |
| ruta desconocida | autenticada | `NotFoundPage` dentro de `AppShell`. |
| ruta desconocida | anónima | El `*` vive bajo `/` (`RequireAuth`), así que primero redirige a `/login`. |

## Estrategia para jsdom

- `LoginDialog` no llama `showModal()` si no es función; usa `setAttribute("open", "")`. El `<dialog>` con `open` calcula `display:block` y expone su contenido a Testing Library.
- Se agrega `role="dialog"` y `aria-modal="true"` explícitos para que el rol no dependa de la accesibilidad nativa de jsdom; `aria-labelledby="login-heading"` apunta al `h2`.
- El foco se fuerza con `document.getElementById("login-username")` después de abrir; no se depende de `autoFocus`.
- Escape se prueba en `Dialog` con `fireEvent.keyDown(dialog, { key: "Escape" })`; `cancel` se prueba con `fireEvent(dialog, new Event("cancel"))`.
- `RevealSection` arranca revelado si no hay `IntersectionObserver` ni observador inyectado; el test de reveal pasa una fábrica falsa que captura el callback y un contador de cleanup.
- No se usa `vi.mock`, `vi.spyOn`, `vi.stubGlobal` ni timers falsos. El carrusel ya tiene su ticker inyectable.

## Mapa de componentes

| Archivo | Responsabilidad |
|---------|-----------------|
| `Dialog.tsx` | Primitiva `<dialog>`: open/close, fallback, Escape/cancel y retorno de foco. |
| `LandingPage.tsx` | Estado `isLoginOpen`, CTA, hero, secciones y `LoginDialog`. |
| `LoginDialog.tsx` | Compone `Dialog`; estilos de portada, foco en Usuario, scroll lock y `LoginForm`. |
| `RevealSection.tsx` | Wrapper con `data-reveal`, observador inyectable y cleanup. |
| `landingContent.ts` | Textos y datos ficticios tipados (servicios, equipo, horarios, contacto). |
| `revealObserver.ts` | Fábrica de observador y detección de reduced motion. |
| `LoginPage.tsx` | Wrapper delgado; conserva props y el cálculo de sesión vencida. |

## Desvíos respecto del explore

1. **D4 — CTA del hero.** El explore proponía “Ingresar” oculto con `aria-hidden` y `tabIndex={-1}` mientras el modal estaba abierto. La decisión final es “Ingresar al sistema”, sin ocultarlo. Motivo: WAI-ARIA desaconseja ocultar contenido focusable; dos nombres accesibles únicos (“Ingresar al sistema” vs “Ingresar”) resuelven la colisión de `getByRole` sin quitar el CTA del árbol de accesibilidad. La fila de riesgo “Dos botones Ingresar” del explore queda superada.
2. **D5 — `<h1>` con logo.** El explore proponía un `<h1>` con texto “Aqua — Clínica Odontológica”. La decisión final es un `<h1>` que contiene el logo claro con `alt="Aqua — Clínica Odontológica"`. Motivo: el nombre accesible del heading sale del `alt`, la marca se anuncia una sola vez y no se repite el texto al lado del logo. El diálogo conserva “Turnos Odontología” como `h2`, que es el heading que buscan los tests existentes.
3. **“Ver la clínica”.** No estaba en el explore. Se agrega como cierre visible del diálogo para que el usuario pueda recorrer la portada sin depender de Escape; es el complemento de D2.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| `LoginPage.test` falla por dos “Ingresar” | D4: CTA “Ingresar al sistema”; submit “Ingresar”; sin `aria-hidden`. |
| `smoke.test` no encuentra el heading | D2: `/` redirige a `/login`, que monta el diálogo abierto; el `h2` “Turnos Odontología” está accesible. |
| `App.test` depende del orden de rutas | No se toca `App.tsx` ni `createAppRoutes`. |
| jsdom sin `showModal`/`close` | D1/D13: fallback por atributo `open`, sin stubs. |
| Dos implementaciones del modal | D13: `Dialog` es la única; `LoginDialog` la compone y C-29/C-30 la reutilizan. |
| `LoginBrand` espera logo y “Pausar animación” con el modal abierto | El hero y el carrusel quedan fuera del `<dialog>`; en jsdom el atributo `open` no aplica `inert`. |
| `autoFocus` antes de abrir | D7/D13: foco explícito en el layout effect de apertura. |
| `toBeVisible` con `opacity:0` | D6: sin observador el estado inicial es revelado. |
| Bloqueo del scroll con salto de layout | D8: guardar/restaurar `overflow`; validar en captura 1440/768. |
| Datos reales | Solo datos ficticios del seed y del explore; sin DNI, teléfonos reales ni nombres reales. |

## Orden de implementación

1. Tokens de layout y su test.
2. `landingContent.ts` y su test de datos.
3. `LandingPage` con hero y secciones; test de contenido.
4. `Dialog` compartido: props, fallback jsdom, Escape/cancel y retorno de foco.
5. `LoginDialog` compone `Dialog`; foco en Usuario, scroll lock y “Ver la clínica”.
6. `RevealSection` + `revealObserver`.
7. `LoginPage` wrapper y regresión de la suite existente.
8. Evidencias: RED, mutaciones, trazabilidad, `tsc`, ESLint, build y capturas.

## Preguntas abiertas

Ninguna. Las decisiones D1-D13 están cerradas por la autora; si aparece un choque con un test existente, se frena y se reporta en vez de modificar el test.
