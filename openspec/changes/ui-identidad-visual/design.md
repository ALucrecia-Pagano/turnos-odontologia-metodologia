# Design

## Context

Ver `proposal.md` para la motivación. El frontend ya existe (C-25 a C-28): React 18.3.1 + TypeScript strict + Vite 5 + React Router 6.30.6 + Vitest 3.2.7, con CSS Modules y tokens en `frontend/src/shared/styles/tokens.css`. Hay dos capas de tests que condicionan el diseño:

- `tokens.test.ts` exige que `--font-family-base` sea exactamente el system font stack y que `body` en `reset.css` declare `font-family: var(--font-family-base)`; también exige `--color-focus` en hex.
- `smoke.test.tsx` exige un heading accesible "Turnos Odontología" en el login.
- `agendaStyles.test.ts` exige los tokens de agenda y que `.todayTag` use `var(--color-primary)` y `var(--color-primary-contrast)`.
- `AppShell.test.tsx` consulta los botones con `within(nav)`, por lo que la marca debe quedar fuera de `nav`.

Los assets ya están en el repo: `frontend/src/assets/brand/` (logos e isotipos) y `frontend/src/assets/images/` (cinco hero webp). El login vive en `frontend/src/features/login/LoginPage.tsx` (ruta `/login` en `App.tsx`) y el shell en `frontend/src/shared/components/AppShell.tsx`.

## Goals / Non-Goals

**Goals:**
- Aplicar la identidad Aqua a login, shell y agenda existentes sin cambiar comportamiento funcional.
- Lograr contraste AA >= 4.5:1 en todo texto real, con tokens semánticos estables.
- Autoalojar las tipografías y eliminar cualquier dependencia de CDN.
- Dejar una barra única con marca responsive y un carrusel decorativo testeable sin timers reales.
- Mantener verde toda la suite existente salvo los dos tests de color autorizados.

**Non-Goals:**
- No se rediseñan flujos, formularios, rutas ni reglas de agenda.
- No se agregan librerías de UI, carrusel, animación ni iconos.
- No se implementa detección dinámica de tema claro/oscuro para elegir el logo.
- No se tocan backend, API, JWT, base de datos ni Docker.
- No se cargan fotos nuevas: se usan las cinco existentes.

## Decisions

### 1. Paleta por tokens semánticos, conservando nombres existentes
Se mantienen los nombres de tokens actuales y se agregan `--color-navy`, `--color-accent` e `--color-ice`. Valores y ratios calculados:

| Token | Valor | Uso | Contraste |
|-------|-------|-----|-----------|
| `--color-text` | `#011C40` | texto principal | 15.70:1 sobre `--color-background` |
| `--color-text-muted` | `#4A5F78` | texto secundario | 6.09:1 sobre fondo |
| `--color-background` | `#F3F7FA` | fondo de app | — |
| `--color-surface` | `#FFFFFF` | tarjetas | — |
| `--color-border` | `#C9DDE4` | bordes | no-texto |
| `--color-primary` | `#26658C` | acción | 6.32:1 con blanco |
| `--color-primary-contrast` | `#FFFFFF` | texto sobre primary | 6.32:1 |
| `--color-focus` | `#26658C` | foco visible | 5.87:1 sobre fondo |
| `--color-navy` | `#023859` | fondos oscuros | — |
| `--color-accent` | `#54ACBF` | acento decorativo | 2.43:1 sobre fondo (excluido) |
| `--color-ice` | `#A7EBF2` | fondo suave | — |

`--color-accent` es solo decorativo y `--color-border` es no-texto; ninguno se usa como texto. Alternativa considerada: renombrar todos los tokens a una nomenclatura nueva; se descartó porque rompe `agendaStyles.test.ts` y multiplica el diff sin beneficio.

### 2. Colores de estado con contraste verificado
Se actualizan solo los valores de `APPOINTMENT_STATUS_TOKENS`; las claves y la forma `{ text, background, border }` no cambian.

| Estado | text | background | border | Ratio |
|--------|------|------------|--------|-------|
| reservado | `#1F5F86` | `#E4F2F8` | `#9CC7D8` | 6.04:1 |
| confirmado | `#146C43` | `#DDF3E7` | `#86EFAC` | 5.54:1 |
| atendido | `#3D4A5C` | `#E6EBF1` | `#94A3B8` | 7.51:1 |
| ausente | `#9A5B00` | `#FDF0D5` | `#F0C36D` | 4.81:1 |
| cancelado | `#A8242C` | `#FBE4E6` | `#EFA3A3` | 5.87:1 |

Los bordes de estado quedan a criterio y se expresan en hex; no se usan como texto. El estado se comunica siempre con texto visible, no solo con color (regla de `appointment-frontend-ux`). Alternativa: mantener la paleta anterior; se descartó porque no armoniza con la marca.

### 3. Tipografías autoalojadas con `@fontsource-variable`
Se agregan `@fontsource-variable/jost` y `@fontsource-variable/manrope` 5.3.0 (versiones confirmadas con `npm view`). Se importan una sola vez en `frontend/src/main.tsx`; Vite las empaqueta y sirve como assets locales.

- `tokens.css` agrega `--font-family-heading: "Jost Variable", <system stack>` y `--font-family-body: "Manrope Variable", <system stack>`.
- `--font-family-base` se conserva exactamente como está (system stack) para `tokens.test.ts`.
- `reset.css` conserva la declaración `font-family: var(--font-family-base)` en `body` y agrega, después, `font-family: var(--font-family-body)`. El regex de `tokens.test.ts` sigue encontrando la primera.
- Títulos con `var(--font-family-heading)`; texto corrido con `var(--font-family-body)`.

Alternativas: Google Fonts por `<link>` (rechazada: dependencia de CDN y privacidad); descargar los `.woff2` a mano (rechazada: Fontsource ya resuelve versionado y licencia); una sola familia (rechazada: se pierde la jerarquía visual pedida).

### 4. Logo estático por contexto, sin detección de tema
Se decodificaron los PNG y se midió la luminancia media de los píxeles opacos (sin visor de imágenes disponible para el modelo):

- `logo-aqua-claro.png` (1124x278, luminancia media 202): logo claro para fondos oscuros -> login, informativo con `alt="Aqua — Clínica Odontológica"`.
- `logo-aqua-oscuro.png` (1124x278, luminancia media 78.8): logo oscuro para fondos claros -> barra, decorativo con `alt=""` porque el texto "Aqua" está al lado.
- `isotipo-aqua-claro.png` claro e `isotipo-aqua.png` oscuro; `logo-variantes.png` es una lámina de referencia, no un asset de UI.

La elección es estática por componente; no hay `prefers-color-scheme` ni lógica condicional. Alternativa: un solo logo con filtro CSS; se descartó porque degrada el trazo de la marca.

El login además muestra la bajada "Claridad en cada cuidado." y una tarjeta tipo vidrio sobre un overlay degradado navy; se conserva el heading "Turnos Odontología". El fondo oscuro y la tarjeta se verifican visualmente (captura), no con jsdom.

### 5. Barra única con la marca fuera de `nav`
La barra se implementa en `AppShell`: logo (fuera de `nav`), "Aqua" y "Clínica Odontológica". El subtítulo se oculta con CSS en `max-width: 768px`; la barra usa `flex-wrap` y un máximo de dos renglones. No se agrega una segunda barra en login ni en agenda. Alternativa: dos barras (una de marca y una de navegación); se descartó por la restricción explícita de una sola barra.

### 6. Carrusel con ticker inyectado y CSS puro
Se implementa un componente de login que recibe `ticker?: (callback: () => void) => () => void` y `prefersReducedMotion?: boolean`, con default `createIntervalTicker(7000)` y un default de `prefersReducedMotion` que lee `window.matchMedia("(prefers-reduced-motion: reduce)").matches`; si `matchMedia` no existe (jsdom), devuelve `false` sin lanzar error. Esto replica el patrón de inyección de `Clock` y permite tests deterministas.

- Estado: índice activo, empezando en `hero-1-sala-de-espera`.
- Rotación: al llamar al callback, avanza y vuelve a 0 después de la quinta foto.
- Ken Burns: animación CSS de 7 s `ease-out`; se reinicia al cambiar la foto activa (la imagen activa monta la animación). El test de jsdom solo verifica la clase en la foto activa; la duración y el reinicio se verifican por CSS (grep del `.module.css`) o captura visual.
- Fotos: `alt=""`, `aria-hidden="true"`, `data-slide-index`, `data-active` en la activa.
- Pausa: botón con texto "Pausar animación"/"Reanudar animación", sin `aria-pressed` (WAI-ARIA APG: el estado va en el nombre o en `aria-pressed`, no en ambos); al pausar se cancela el ticker y al reanudar se recrea.
- Reduced motion: sin rotación automática ni Ken Burns; `@media (prefers-reduced-motion: reduce)` desactiva el Ken Burns y el fundido.
- Limpieza: `useEffect` devuelve la cancelación del ticker al desmontar.

Alternativas: Swiper/Embla (rechazadas: dependencia extra para algo decorativo); `setInterval` directo en el componente (rechazada: tests con timers reales, lentos y frágiles); carrusel solo CSS (rechazada: no se puede testear la pausa ni el avance).

### 7. Evidencias y trazabilidad
Cada test nuevo se acompaña de una mutación con el detector del repo (patrón `docs/evidencias/mutaciones-C-28.py`): una mutación por test, inválida si no falla por la aserción propia. Antes de tocar los tests se recalculan los ratios con la función `contrastRatio` del test existente y se registra la salida en `docs/evidencias/ratios-C-34.txt`. Se generan `red-C-34/`, `mutaciones-C-34.txt`, `verify-C-34.md` y `trazabilidad-C-34.py`, todo en UTF-8. La verificación visual en 1440 y 768 px la realiza Claude con Playwright en la verificación independiente; el apply no la ejecuta.

## Desvíos respecto del explore

El explore original proponía `@fontsource`; se usa `@fontsource-variable` (5.3.0) porque los paquetes variables incluyen todos los pesos en un solo archivo, exponen las familias `"Jost Variable"` y `"Manrope Variable"` y reducen la cantidad de imports. El paquete y las familias se aplican igual en proposal, design, tasks y specs.

El explore proponía un botón de pausa con `aria-pressed` y texto "Pausar"/"Reanudar"; se usa "Pausar animación"/"Reanudar animación" sin `aria-pressed`, porque WAI-ARIA APG indica que el estado va en el nombre accesible o en `aria-pressed`, no en ambos.

El explore proponía `prefersReducedMotion` por defecto en `false`; se cambia a leer `window.matchMedia("(prefers-reduced-motion: reduce)").matches` con guarda para jsdom, para respetar la preferencia real del sistema en producción sin romper los tests.

## Risks / Trade-offs

- **`tokens.test.ts` es sensible al texto exacto** -> Se conserva `--font-family-base` y la primera declaración de `body`; la familia nueva va en una segunda declaración y en tokens nuevos.
- **`smoke.test.tsx` depende del heading del login** -> Se mantiene el heading "Turnos Odontología" y se agrega el logo como decoración.
- **Contraste de estados** -> Los ratios se calcularon antes de escribir; si un ajuste visual cambia un valor, el test de contraste falla y obliga a recalcular.
- **Ken Burns que no se reinicia** -> La animación se ata a la foto activa (montaje por índice); el test de jsdom verifica la clase solo en la activa y la duración/reinicio se valida por CSS (grep) o captura visual.
- **Carrusel frágil en tests** -> Ticker y reduced motion inyectados; no se usan fake timers, `waitFor` largos ni mocks.
- **Barra que excede dos renglones en 768** -> `flex-wrap` + ocultar subtítulo; se valida con captura visual además del test de estructura.
- **Assets pesados** -> Las cinco fotos ya existen; se importan estáticamente y Vite las optimiza en build; no se agregan nuevas.
- **Regresión fuera de alcance** -> Si cualquier test distinto de `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts` falla, se frena y se reporta antes de tocar código.

## Migration Plan

1. Agregar dependencias de Fontsource e imports en `main.tsx`; verificar build.
2. Actualizar tokens, reset y colores de estado; correr la suite y confirmar que solo cambian los dos tests autorizados.
3. Integrar logo y barra en `AppShell`; correr `AppShell.test.tsx`.
4. Implementar carrusel y logo del login con sus tests; correr `LoginPage.test.tsx` y `smoke.test.tsx`.
5. Agregar créditos al README.
6. Ejecutar suite completa, mutaciones, trazabilidad y verificación visual 1440/768 (Playwright, a cargo de Claude).
7. Rollback: revertir el commit único de C-34; no hay migraciones de datos ni cambios de API.

## Open Questions

Ninguna. Las decisiones de assets, paleta, fuentes, ticker y alcance quedaron cerradas en el explore y en este diseño.
