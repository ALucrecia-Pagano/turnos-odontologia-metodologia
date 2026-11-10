# Proposal

## Why

La aplicación ya funciona (login, agenda diaria y semanal) pero su interfaz todavía usa el stack tipográfico del sistema y una paleta genérica que no representa la marca **Aqua — Clínica Odontológica**. Este change aplica una identidad visual coherente y accesible a las pantallas existentes, sin tocar el dominio ni la API: paleta semántica con contraste AA, tipografías autoalojadas (sin CDN), logo en login y barra, una sola barra de navegación y un carrusel decorativo en el login. Se ejecuta después de C-28 (`ui-agenda-semanal`) y antes de C-29, para que las pantallas de agenda que faltan hereden la identidad desde el inicio. Governance **BAJO**: solo estilos, assets y presentación; no hay reglas de negocio, seguridad ni persistencia involucradas.

## What Changes

- **Paleta de identidad**: se reemplazan los valores de `tokens.css` por la paleta Aqua (ink, navy, primary, accent, ice, fondo, texto secundario, foco) manteniendo los nombres semánticos existentes y agregando tokens nuevos para navy, accent e ice. Los pares texto/fondo usados como texto MUST cumplir contraste ≥ 4.5:1; los colores puramente decorativos quedan excluidos de esa exigencia.
- **Colores de estado**: se actualizan los cinco pares de `APPOINTMENT_STATUS_TOKENS` (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`) con la nueva paleta, conservando contraste AA ≥ 4.5:1 y el texto visible de cada estado.
- **Tipografías autoalojadas**: se incorporan las familias `"Jost Variable"` (títulos) y `"Manrope Variable"` (texto) mediante `@fontsource-variable` (paquetes npm), importados desde el entry point de Vite y con fallback al system font stack. Sin CDN, sin `<link>` remoto y sin depender de Google Fonts.
- **Logo y barra única**: el logo de Aqua se integra en el login (variante clara sobre fondo oscuro, informativa con `alt="Aqua — Clínica Odontológica"`) y en la barra de la aplicación (variante oscura sobre fondo claro, con `alt=""` porque el texto "Aqua" está al lado), sin lógica dinámica de selección. La barra muestra logo + "Aqua" + "Clínica Odontológica"; en tablet (≤ 768 px) muestra solo "Aqua" y no supera dos renglones. Se mantiene una única barra de encabezado.
- **Login**: se agrega la bajada "Claridad en cada cuidado." y una tarjeta tipo vidrio sobre un overlay degradado navy; se conserva el heading "Turnos Odontología".
- **Carrusel del login**: cinco fotos decorativas de la clínica rotan cada 7 s con efecto Ken Burns de 7 s `ease-out` que se reinicia en cada foto. Incluye botón "Pausar animación"/"Reanudar animación" sin `aria-pressed`, respeta `prefers-reduced-motion` (sin rotación ni Ken Burns; el default lee `window.matchMedia` con guarda para jsdom y el CSS desactiva Ken Burns y fundido) y cancela su ticker al desmontar. El ticker y `prefersReducedMotion` se inyectan como dependencias para poder testearlos sin timers reales.
- **Créditos**: el `README.md` incorpora una sección de créditos que nombra las fotografías, el logo y la licencia de las tipografías.
- **Condición dura de regresión**: solo pueden cambiar los valores de color de `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`. Cualquier otro test existente debe seguir pasando sin modificación; en particular se conserva el encabezado accesible "Turnos Odontología" del login que verifica `smoke.test.tsx`.

## Capabilities

### New Capabilities

Ninguna. La identidad visual se expresa como requisitos de capacidades existentes.

### Modified Capabilities

- `frontend-foundation`: cambia el requisito de tokens de diseño y colores por estado (nueva paleta con contraste AA y borde no-texto), y agrega requisitos de tipografías autoalojadas, barra única con marca y créditos en el README.
- `frontend-auth-session`: agrega el requisito de marca, bajada, tarjeta y carrusel decorativo en la pantalla de login (variante de logo y alt, rotación con ticker inyectado, pausa sin `aria-pressed`, reduced motion con default de `matchMedia`, Ken Burns y cancelación al desmontar).

## Impact

- **Código de frontend modificado**: `frontend/src/shared/styles/tokens.css`, `frontend/src/shared/styles/reset.css`, `frontend/src/shared/styles/appointmentStatusTokens.ts`, `frontend/src/shared/components/AppShell.tsx`, `frontend/src/shared/components/AppShell.module.css`, `frontend/src/features/login/LoginPage.tsx`, `frontend/src/features/login/LoginPage.module.css`, `frontend/src/main.tsx`.
- **Código nuevo**: carrusel del login y su ticker inyectable en `frontend/src/features/login/` (componente, estilos y tests), más los tests de identidad visual y contraste.
- **Dependencias nuevas**: `@fontsource-variable/jost` y `@fontsource-variable/manrope` (5.3.0), autoalojadas; no se agregan librerías de UI ni de carrusel.
- **Assets**: `frontend/src/assets/brand/` (logos) y `frontend/src/assets/images/` (cinco fotos) ya presentes en el repo; se usan con imports estáticos de Vite.
- **Sin cambios**: `backend/`, base de datos, APIs REST, autenticación JWT, Docker Compose, `.env`, reglas de dominio y tests de dominio.
- **Tests existentes**: solo se actualizan valores de color en `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`. El resto de la suite (incluidos `tokens.test.ts`, `agendaStyles.test.ts`, `AppShell.test.tsx`, `LoginPage.test.tsx`, `App.test.tsx` y `smoke.test.tsx`) debe quedar verde sin cambios.
- **Evidencias requeridas**: suite RED en `docs/evidencias/red-C-34/`, ratios recalculados con `contrastRatio` en `docs/evidencias/ratios-C-34.txt`, mutaciones con el detector del repo, trazabilidad de escenarios (los visuales o de CSS marcados y sin mutación), verificación visual en 1440 y 768 px (Playwright, a cargo de Claude en la verificación independiente) y archivos de evidencia en UTF-8.
