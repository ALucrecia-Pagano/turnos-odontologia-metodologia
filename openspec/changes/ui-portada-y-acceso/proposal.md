# Proposal

## Why

C-34 dejó la identidad visual y el carrusel, pero `/login` sigue siendo una tarjeta aislada: no presenta la clínica ni explica qué hace el sistema antes de pedir credenciales. La portada pública cierra esa brecha y mantiene el acceso a un clic, sin tocar autenticación, rutas ni reglas de negocio. Se ejecuta ahora porque C-34 está archivado (2026-11-09) y C-35 es el prerrequisito visual de C-36 y del resto de la UI de agenda.

## What Changes

- **Portada pública en `/login`**: `LoginPage` pasa a ser un wrapper delgado de `LandingPage`; el hero reutiliza el carrusel de C-34 y el diálogo de login se abre al entrar. No se agregan rutas ni se altera el orden de `createAppRoutes`.
- **Hero con marca y acceso**: el `<h1>` contiene el logo claro (la marca se anuncia una sola vez por el `alt`), la bajada "Claridad en cada cuidado.", un lead, el badge "Sitio de demostración" y el CTA "Ingresar al sistema".
- **Diálogo de acceso**: `<dialog>` nativo con heading "Turnos Odontología", foco en Usuario, Escape, botón "Ver la clínica", retorno de foco y bloqueo del scroll del fondo. En jsdom se usa el atributo `open` cuando `showModal` no existe, sin stubs de globals.
- **Primitiva `Dialog` compartida**: `frontend/src/shared/components/Dialog.tsx` concentra el `<dialog>` modal (`open`, `onClose`, `labelledBy`, `returnFocusRef`, `children`), el fallback `showModal`/`open`, Escape/`cancel` y el retorno de foco. `LoginDialog` la compone y conserva el scroll lock y el foco en Usuario; C-29 (dar turno) y C-30 (reprogramar) la reutilizan para no duplicar el modal.
- **Cuatro secciones informativas**: Quiénes somos, Servicios, Equipo y Horarios y contacto, con datos ficticios del seed, horarios reales de la demo y marcas visibles de demostración.
- **Reveal accesible**: las secciones se animan al scrollear con un observador inyectable; sin `IntersectionObserver` o con `prefers-reduced-motion` el contenido queda visible.
- **Tokens de layout**: `--landing-hero-min-height` y `--landing-content-max-width` en `tokens.css`, sin colores nuevos.
- **Specs**: nueva capability `frontend-landing`; delta de `frontend-auth-session` para la bajada y la tarjeta que pasan a la portada y al diálogo; delta de `frontend-foundation` por los tokens de layout y la primitiva `Dialog` reutilizable.

**Fuera de alcance:** tema oscuro y responsive para celular (C-36 `ui-tema-oscuro-y-movil`); formulario de dar turno (C-29) y acciones de reprogramar/cancelar/estados (C-30); arreglo del fallo preexistente de `Logout.test.tsx` (va aparte). No se toca la lógica de autenticación, la API ni el dominio.

## Capabilities

### New Capabilities

- `frontend-landing`: portada pública de la clínica en `/login`, hero con marca y carrusel, secciones informativas con datos ficticios, diálogo de acceso y reveal accesible.

### Modified Capabilities

- `frontend-auth-session`: el requisito "Bajada y tarjeta del login" cambia porque la bajada queda en la portada y la tarjeta del formulario pasa al diálogo de acceso.
- `frontend-foundation`: se agregan el requisito de tokens de layout de la portada (`--landing-hero-min-height` y `--landing-content-max-width`) y el requisito de la primitiva `Dialog` modal reutilizable que comparten la portada, C-29 y C-30.

## Impact

- **Código nuevo**: `frontend/src/shared/components/Dialog.tsx` (+ `Dialog.module.css` y `Dialog.test.tsx`) y `frontend/src/features/landing/` (`LandingPage.tsx`, `LandingPage.module.css`, `LoginDialog.tsx` + estilos, `RevealSection.tsx` + estilos, `landingContent.ts`, `revealObserver.ts` y tests).
- **Código modificado**: `frontend/src/features/login/LoginPage.tsx` (wrapper delgado que conserva `carouselTicker` y `prefersReducedMotion`), `frontend/src/shared/styles/tokens.css` (tokens de layout) y, si hace falta, estilos compartidos del carrusel.
- **Sin cambios**: `frontend/src/App.tsx`, `RequireAuth`/`PublicOnlyRoute`, `AuthContext`, `tokenStore`, cliente de API, backend, base de datos, Docker y `.env`.
- **Tests existentes**: `LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `App.test.tsx`, `smoke.test.tsx` y el resto de la suite MUST seguir pasando sin cambios. Si un escenario obliga a modificarlos, se frena y se reporta.
- **Evidencias**: RED por test nuevo, mutaciones con detector de inválidas, trazabilidad escenario → test → mutación (visuales sin mutación), suite, `tsc`, ESLint, build y capturas 1440/768/390 px a cargo de Claude en la verificación independiente.
