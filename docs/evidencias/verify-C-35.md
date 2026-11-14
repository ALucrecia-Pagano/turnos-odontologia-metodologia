# Verificación de C-35 — ui-portada-y-acceso

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8, sin BOM).

- **Tareas**: fases 1 a 8 y 10 (ajustes de diseño) implementadas según [tasks.md](../../openspec/changes/ui-portada-y-acceso/tasks.md). La fase 9 (capturas en navegador real a 1440, 768 y 390 px) queda sin marcar, a cargo de Claude/la orquestación.
- **Vitest**: línea base de 232 tests en 55 archivos ([baseline-C-35.txt](baseline-C-35.txt)); suite final de **258 tests en 64 archivos**, todos en verde ([test-suite-C-35.txt](test-suite-C-35.txt)). 258 = 232 + 26: 13 tests de escenario nuevos, 9 auxiliares recuperados de `cea858b` (3 de `landingContent.test.ts`, 3 de `RevealSection.test.tsx`, 3 de `landingTokens.test.ts`) y 4 tests adicionales del ajuste de diseño (nuevos de esta ronda: 1 en `AppShellNavigation.test.tsx`, 1 en `RevealSection.test.tsx` y 2 en `LandingPage.test.tsx`); los 26 llevan mutación propia.
- **Mutaciones**: 26 de 26 (M01-M13 de escenarios, A01-A09 de los 9 auxiliares y M14-M17 de los 4 tests del ajuste de diseño) hicieron fallar su test por aserción; sobrevivientes 0; inválidas 0; SHA-256 sin cambios: sí ([mutaciones-C-35.txt](mutaciones-C-35.txt), generado por [mutaciones-C-35.py](mutaciones-C-35.py)).
- **Trazabilidad**: 24 escenarios = 13 nuevos + 5 históricos + 6 visuales, más 13 tests auxiliares/adicionales listados con su mutación (A01-A09 y M14-M17), 0 problemas ([trazabilidad-C-35.txt](trazabilidad-C-35.txt), generado por [trazabilidad-C-35.py](trazabilidad-C-35.py)).
- **Calidad**: `tsc --noEmit` exit 0; `npx eslint .` exit 0 (0 errores, 3 advertencias previas); `npm run lint` exit 1 por esas 3 advertencias (ver Desvíos); `npm run build` exit 0 ([tooling-C-35.txt](tooling-C-35.txt), [build-C-35.txt](build-C-35.txt)).
- **OpenSpec**: `openspec validate ui-portada-y-acceso --strict` y `openspec validate --all --strict` exit 0 ([validate-C-35.txt](validate-C-35.txt)).
- **Tests existentes**: único modificado `frontend/src/test/smoke.test.tsx` ([diff-tests-existentes-C-35.txt](diff-tests-existentes-C-35.txt)).
- **Skill y MCP**: [C-35-mcp-context7.md](../skills-mcp/evidencias/C-35-mcp-context7.md) y [C-35-skill-appointment-frontend-ux.md](../skills-mcp/evidencias/C-35-skill-appointment-frontend-ux.md).
- **Encoding de lo recuperado de `cea858b`**: [C-35-encoding-recuperados.txt](C-35-encoding-recuperados.txt) (todos ASCII o UTF-8, sin BOM ni UTF-16).

## Matriz escenario → test → mutación

<!-- trazabilidad:inicio -->
| # | Spec | Escenario | Tipo | Test | Mutación | Evidencia |
|---|------|-----------|------|------|----------|-----------|
| 01 | frontend-landing | Portada completa para anónimo en / | nuevo | `src/features/landing/LandingPage.test.tsx` > portada completa para anónimo en / | M01 | red/green-C-35/01-portada-anonimo.txt |
| 02 | frontend-landing | Usuario autenticado en / redirige a agenda | nuevo | `src/features/landing/RootGate.test.tsx` > usuario autenticado en / redirige a agenda | M02 | red/green-C-35/02-portada-autenticado-redirect.txt |
| 03 | frontend-landing | Secciones editoriales entran con animación lateral al scrollear | nuevo | `src/features/landing/LandingPage.test.tsx` > secciones editoriales entran con animación lateral al scrollear | M03 | red/green-C-35/03-secciones-reveal-lateral.txt |
| 04 | frontend-landing | Reduced motion desactiva la animación lateral y deja el contenido visible | nuevo | `src/features/landing/LandingPage.test.tsx` > reduced motion desactiva la animación lateral y deja el contenido visible | M04 | red/green-C-35/04-reduced-motion.txt |
| 05 | frontend-landing | Navegación desde las tres tarjetas de rol hacia login | nuevo | `src/features/landing/AccesoPage.test.tsx` > navegación desde las tres tarjetas de rol hacia login | M05 | red/green-C-35/05-acceso-tarjetas.txt |
| 06 | frontend-landing | Navegación de retorno con el enlace Volver a Aqua | nuevo | `src/features/landing/AccesoPage.test.tsx` > navegación de retorno con el enlace Volver a Aqua | M06 | red/green-C-35/06-acceso-volver.txt |
| 07 | frontend-auth-session | Formulario translúcido en /login con etiqueta de rol y envío de credenciales | nuevo | `src/features/login/LoginPage.translucido.test.tsx` > formulario translúcido en /login con etiqueta de rol y envío de credenciales | M07 | red/green-C-35/07-login-translucido-rol.txt |
| 08 | frontend-auth-session | Parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter | nuevo | `src/features/login/LoginPage.translucido.test.tsx` > parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter | M08 | red/green-C-35/08-login-rol-invalido-fallback.txt |
| 09 | frontend-auth-session | Cierre de sesión y preservación del mensaje literal de sesión vencida | nuevo | `src/features/login/LoginPage.translucido.test.tsx` > cierre de sesión y preservación del mensaje literal de sesión vencida | M09 | red/green-C-35/09-login-sesion-vencida.txt |
| 10 | frontend-foundation | Tokens de layout y contraste AA de superficies | nuevo | `src/shared/styles/landingTokens.test.ts` > tokens de layout y contraste AA de superficies | M10 | red/green-C-35/10-tokens-contraste.txt |
| 11 | frontend-foundation | Fallback sólido sin soporte de backdrop-filter | nuevo | `src/shared/components/DialogTheme.test.ts` > fallback sólido sin soporte de backdrop-filter | M11 | red/green-C-35/11-fallback-solido-modales.txt |
| 12 | frontend-foundation | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | nuevo | `src/shared/components/AppShellNavigation.test.tsx` > enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | M12 | red/green-C-35/12-appshell-nav-activa.txt |
| 13 | frontend-foundation | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | nuevo | `src/shared/components/AppShellNavigation.test.tsx` > ítems deshabilitados con Próximamente conservan semántica y accesibilidad | M13 | red/green-C-35/13-appshell-proximamente.txt |
| H1 | frontend-auth-session | Login correcto del administrador | historico | `src/features/login/LoginPage.test.tsx` > login correcto del administrador | — (test existente) | green-C-35/login-regresion.txt |
| H2 | frontend-auth-session | Login correcto de recepción y del odontólogo | historico | `src/features/login/LoginPage.test.tsx` > login correcto de recepción y del odontólogo | — (test existente) | green-C-35/login-regresion.txt |
| H3 | frontend-auth-session | Credenciales inválidas con mensaje genérico | historico | `src/features/login/LoginPage.test.tsx` > credenciales inválidas con mensaje genérico | — (test existente) | green-C-35/login-regresion.txt |
| H4 | frontend-auth-session | Envío en curso y doble submit | historico | `src/features/login/LoginPage.test.tsx` > envío en curso y doble submit | — (test existente) | green-C-35/login-regresion.txt |
| H5 | frontend-auth-session | Accesibilidad del formulario | historico | `src/features/login/LoginPage.test.tsx` > accesibilidad del formulario | — (test existente) | green-C-35/login-regresion.txt |
| V1 | frontend-landing | Adaptabilidad de la portada en 1440, 768 y 390 px | visual | Captura (fase 9) | — | capturas/C-35-portada-*.png |
| V2 | frontend-landing | Secciones editoriales intercaladas a ancho parcial en 1440 px y a ancho completo en 768 y 390 px | visual | Captura (fase 9) | — | capturas/C-35-secciones-*.png |
| V3 | frontend-landing | Adaptabilidad de las tarjetas de acceso en 1440, 768 y 390 px | visual | Captura (fase 9) | — | capturas/C-35-acceso-*.png |
| V4 | frontend-auth-session | Adaptabilidad de /login en 1440, 768 y 390 px | visual | Captura (fase 9) | — | capturas/C-35-login-*.png |
| V5 | frontend-foundation | Superficie clara suave de modales verificada a 1440, 768 y 390 px | visual | Captura (fase 9) | — | capturas/C-35-modales-*.png |
| V6 | frontend-foundation | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | visual | Captura (fase 9) | — | capturas/C-35-appshell-*.png |

Tests auxiliares y adicionales (no son escenarios; 24 = 13 + 5 + 6 no cambia):

| Mutación | Archivo | Test |
|----------|---------|------|
| A01 | `src/shared/styles/landingTokens.test.ts` | define los dos tokens de layout |
| A02 | `src/shared/styles/landingTokens.test.ts` | la portada usa los tokens de layout |
| A03 | `src/shared/styles/landingTokens.test.ts` | no agrega colores nuevos |
| A04 | `src/features/landing/landingContent.test.ts` | el equipo coincide con el seed |
| A05 | `src/features/landing/landingContent.test.ts` | los servicios y duraciones coinciden con el seed |
| A06 | `src/features/landing/landingContent.test.ts` | horarios y contacto son ficticios y coinciden con el seed |
| A07 | `src/features/landing/RevealSection.test.tsx` | sin IntersectionObserver queda revelada y su contenido es visible |
| A08 | `src/features/landing/RevealSection.test.tsx` | con observador inyectado pasa de pendiente a revelada y limpia al desmontar |
| A09 | `src/features/landing/RevealSection.test.tsx` | con movimiento reducido no queda pendiente y el contenido está en el DOM |
| M14 | `src/shared/components/AppShellNavigation.test.tsx` | los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces |
| M15 | `src/features/landing/RevealSection.test.tsx` | from=right desplaza en positivo y from=left en negativo |
| M16 | `src/features/landing/LandingPage.test.tsx` | las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha |
| M17 | `src/features/landing/LandingPage.test.tsx` | el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único |
<!-- trazabilidad:fin -->

## Mutaciones (M01–M13, A01–A09, M14–M17)

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| M01 | `portada completa para anónimo en /` | `frontend/src/features/landing/LandingPage.tsx` | `-              <Link to="/" className={styles.navLink} aria-current="page"> +             ` | `Error: expect(element).toHaveAttribute("aria-current", "page") // element.getAttribute("ar` |
| M02 | `usuario autenticado en / redirige a agenda` | `frontend/src/features/landing/RootGate.tsx` | `-    if (status === "anonymous") { +    if (status === "anonymous" \|\| status === "authenti` | `AssertionError: expected '/' to be '/agenda?date=2026-11-16' // Object.is equality` |
| M03 | `secciones editoriales entran con animación lateral al scrollear` | `frontend/src/features/landing/RevealSection.module.css` | `-  transform: translateX(var(--landing-reveal-offset)); +  transform: translateY(var(--lan` | `AssertionError: expected 'opacity: 0;\n  transform: translateY(…' to contain 'translateX('` |
| M04 | `reduced motion desactiva la animación lateral y deja el contenido visible` | `frontend/src/features/landing/RevealSection.tsx` | `-  const canAnimate = !reducedMotion && (observer !== undefined \|\| typeof IntersectionObse` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
| M05 | `navegación desde las tres tarjetas de rol hacia login` | `frontend/src/features/landing/AccesoPage.tsx` | `-  { id: "odontologo", title: "Odontología", description: "Tu agenda como profesional.", t` | `Error: expect(element).toHaveAttribute("href", "/login?rol=odontologo") // element.getAttr` |
| M06 | `navegación de retorno con el enlace Volver a Aqua` | `frontend/src/features/landing/AccesoPage.tsx` | `-        <Link to="/" className={styles.backLink}> +        <Link to="/login" className={s` | `AssertionError: expected '/login' to be '/' // Object.is equality` |
| M07 | `formulario translúcido en /login con etiqueta de rol y envío de credenciales` | `frontend/src/features/login/LoginPage.tsx` | `-  const roleLabel = roleParam !== null ? (ROLE_LABELS.get(roleParam) ?? null) : null; +  ` | `Error: expect(received).toBeInTheDocument()` |
| M08 | `parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter` | `frontend/src/features/login/LoginPage.tsx` | `-  const roleLabel = roleParam !== null ? (ROLE_LABELS.get(roleParam) ?? null) : null; +  ` | `AssertionError: expected <p class="roleLabel" data-role-label></p> to be null` |
| M09 | `cierre de sesión y preservación del mensaje literal de sesión vencida` | `frontend/src/features/login/LoginPage.tsx` | `-    return (state as { expired?: unknown }).expired === true; +    return (state as { exp` | `Error: expect(received).toBeInTheDocument()` |
| M10 | `tokens de layout y contraste AA de superficies` | `frontend/src/shared/styles/tokens.css` | `-  --landing-hero-min-height: 60vh; +  --landing-hero-min-height: 50vh;` | `AssertionError: expected '50vh' to be '60vh' // Object.is equality` |
| M11 | `fallback sólido sin soporte de backdrop-filter` | `frontend/src/shared/components/Dialog.module.css` | `-@supports not (backdrop-filter: blur(1px)) { -  .dialog::backdrop { -    background: var(` | `AssertionError: expected '' to contain 'background: var(--scrim-navy-strong);'` |
| M12 | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | `frontend/src/shared/components/AppShell.tsx` | `+                    aria-current="false"` | `Error: expect(element).toHaveAttribute("aria-current", "page") // element.getAttribute("ar` |
| M13 | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | `frontend/src/shared/components/AppShell.module.css` | `+  border: 1px solid var(--color-border);` | `AssertionError: .badge: expected 'display: block;\n  border: 1px solid …' not to match /(^` |
| A01 | `define los dos tokens de layout` | `frontend/src/shared/styles/tokens.css` | `-  --landing-content-max-width: 1120px; +  --landing-content-max-width: 1120;` | `AssertionError: expected '1120' to match /^\d+(\.\d+)?(px\|rem\|em\|vw\|%)$/` |
| A02 | `la portada usa los tokens de layout` | `frontend/src/features/landing/LandingPage.module.css` | `-  min-height: max(var(--landing-hero-min-height), 100svh); +  min-height: max(60vh, 100sv` | `AssertionError: expected '.page {\n  display: flex;\n  align-it…' to contain 'var(--landin` |
| A03 | `no agrega colores nuevos` | `frontend/src/shared/styles/tokens.css` | `+  --color-extra: #123456;` | `AssertionError: expected [ '--color-extra' ] to deeply equal []` |
| A04 | `el equipo coincide con el seed` | `frontend/src/features/landing/landingContent.ts` | `-    name: "Dra. Paula Benítez", +    name: "Dra. Paula Benitez",` | `AssertionError: expected [ 'Dr. Martín Sosa', …(2) ] to deeply equal [ 'Dr. Martín Sosa', ` |
| A05 | `los servicios y duraciones coinciden con el seed` | `frontend/src/features/landing/landingContent.ts` | `-    durationMinutes: 90, +    durationMinutes: 80,` | `AssertionError: expected [ [ 'Limpieza', 45 ], …(4) ] to deeply equal [ [ 'Limpieza', 45 ]` |
| A06 | `horarios y contacto son ficticios y coinciden con el seed` | `frontend/src/features/landing/landingContent.ts` | `-  phone: "(0261) 555-0101", +  phone: "(0261) 555-0102",` | `AssertionError: expected { …(3) } to deeply equal { …(3) }` |
| A07 | `sin IntersectionObserver queda revelada y su contenido es visible` | `frontend/src/features/landing/RevealSection.tsx` | `-  const [revealed, setRevealed] = useState(!canAnimate); +  const [revealed, setRevealed]` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
| A08 | `con observador inyectado pasa de pendiente a revelada y limpia al desmontar` | `frontend/src/features/landing/RevealSection.tsx` | `-    return instance.observe(section, () => { +    instance.observe(section, () => {` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| A09 | `con movimiento reducido no queda pendiente y el contenido está en el DOM` | `frontend/src/features/landing/RevealSection.tsx` | `-      data-reveal={revealed ? "revealed" : "pending"} +      data-reveal={revealed && !re` | `Error: expect(element).toHaveAttribute("data-reveal", "revealed") // element.getAttribute(` |
| M14 | `los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces` | `frontend/src/shared/components/AppShell.module.css` | `-  border: 0;` | `AssertionError: expected 'display: inline-flex;\n  flex-directi…' to contain 'border: 0;'` |
| M15 | `from=right desplaza en positivo y from=left en negativo` | `frontend/src/features/landing/RevealSection.module.css` | `-  transform: translateX(calc(-1 * var(--landing-reveal-offset))); +  transform: translate` | `AssertionError: expected 'transform: translateX(var(--landing-r…' to contain 'translateX(c` |
| M16 | `las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha` | `frontend/src/features/landing/LandingPage.tsx` | `-          <RevealSection observer={observer} reducedMotion={motionReduced} from="right"> ` | `AssertionError: expected [ 'left', 'left', 'left', 'right' ] to deeply equal [ 'left', 'ri` |
| M17 | `el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único` | `frontend/src/features/landing/LandingPage.module.css` | `-  background: transparent; +  background: var(--color-primary);` | `AssertionError: expected 'display: inline-flex;\n  align-items:…' to contain 'background: ` |
<!-- mutaciones:fin -->

## Tokens nuevos (de `tokens.css`)

| Token | Valor |
|---|---|
| `--landing-hero-min-height` | `60vh` |
| `--landing-content-max-width` | `1120px` |
| `--landing-reveal-offset` | `20px` |
| `--landing-logo-width` (nuevo en esta ronda) | `min(520px, 72vw)` |
| `--landing-carousel-blur` / `--blur-surface` / `--blur-backdrop` | `6px` / `12px` / `4px` |
| `--font-size-display` | `clamp(32px, 6vw, 56px)` |
| `--color-navy-deep` | `#011C40` |
| `--surface-navy` / `--surface-ivory-ice` | `rgba(1, 28, 64, 0.82)` / `rgba(243, 247, 250, 0.96)` |
| `--border-on-navy` / `--border-on-navy-strong` | `rgba(167, 235, 242, 0.22)` / `rgba(167, 235, 242, 0.35)` |
| `--field-on-navy` | `rgba(1, 28, 64, 0.6)` |
| `--scrim-navy` / `--scrim-navy-strong` | `rgba(1, 28, 64, 0.45)` / `rgba(1, 28, 64, 0.7)` |
| `--overlay-hero` | `linear-gradient(180deg, rgba(1, 28, 64, 0.55) 0%, rgba(1, 28, 64, 0.82) 100%)` |
| `--shadow-on-navy` | `0 16px 40px rgba(1, 28, 64, 0.45)` |
| `--login-overlay-start` / `-mid` / `-end` | `rgba(1, 28, 64, 0.92)` / `rgba(2, 56, 89, 0.78)` / `rgba(38, 101, 140, 0.62)` |
| `--carousel-toggle-bg` / `-bg-hover` / `-border` | `rgba(1, 28, 64, 0.55)` / `rgba(1, 28, 64, 0.75)` / `rgba(255, 255, 255, 0.45)` |

Color hardcodeado restante en los CSS Modules de C-35 y en `LoginPage.module.css`: ninguno (`grep` de HEX y `rgb(a)` sin resultados).

## Ciclo TDD (RED / GREEN por escenario)

| # | RED | GREEN | Cómo se obtuvo el RED |
|---|-----|-------|------------------------|
| 01 | [red](red-C-35/01-portada-anonimo.txt) | [green](green-C-35/01-portada-anonimo.txt) | Por aserción: `/` redirigía a `/login` |
| 02 | [red](red-C-35/02-portada-autenticado-redirect.txt) | [green](green-C-35/02-portada-autenticado-redirect.txt) | Por mutación M02 (el comportamiento ya existía) |
| 03 | [red](red-C-35/03-secciones-reveal-lateral.txt) | [green](green-C-35/03-secciones-reveal-lateral.txt) | Por aserción: sin secciones y CSS `translateY` de 500 ms |
| 04 | [red](red-C-35/04-reduced-motion.txt) | [green](green-C-35/04-reduced-motion.txt) | Por mutación M04 (la propagación de `reducedMotion` ya estaba en `RevealSection`) |
| 05 | [red](red-C-35/05-acceso-tarjetas.txt) | [green](green-C-35/05-acceso-tarjetas.txt) | Por aserción: `/acceso` no existía |
| 06 | [red](red-C-35/06-acceso-volver.txt) | [green](green-C-35/06-acceso-volver.txt) | Por mutación M06 (el enlace se implementó junto con la página) |
| 07 | [red](red-C-35/07-login-translucido-rol.txt) | [green](green-C-35/07-login-translucido-rol.txt) | Por aserción: sin etiqueta de rol ni "← Volver" |
| 08 | [red](red-C-35/08-login-rol-invalido-fallback.txt) | [green](green-C-35/08-login-rol-invalido-fallback.txt) | Por aserción: faltaba el bloque `@supports not` |
| 09 | [red](red-C-35/09-login-sesion-vencida.txt) | [green](green-C-35/09-login-sesion-vencida.txt) | Por mutación M09 (comportamiento ya existente, tarea 5.5) |
| 10 | [red](red-C-35/10-tokens-contraste.txt) | [green](green-C-35/10-tokens-contraste.txt) | Por aserción: faltaban los tokens de superficie |
| 11 | [red](red-C-35/11-fallback-solido-modales.txt) | [green](green-C-35/11-fallback-solido-modales.txt) | Por aserción: backdrop sin blur ni fallback |
| 12 | [red](red-C-35/12-appshell-nav-activa.txt) | [green](green-C-35/12-appshell-nav-activa.txt) | Por aserción: `.menuLink` con caja de fondo y borde |
| 13 | [red](red-C-35/13-appshell-proximamente.txt) | [green](green-C-35/13-appshell-proximamente.txt) | Por aserción: `.menuButton` con borde |

| 14 | [red](red-C-35/14-appshell-menubutton-borde.txt) | [green](green-C-35/14-appshell-menubutton-borde.txt) | Por aserción: `.menuButton` sin `border: 0` (adicional, M14) |
| 15 | [red](red-C-35/15-reveal-lado.txt) | [green](green-C-35/15-reveal-lado.txt) | Por aserción: sin `data-side` (adicional, M15) |
| 16 | [red](red-C-35/16-secciones-alternan-lado.txt) | [green](green-C-35/16-secciones-alternan-lado.txt) | Por aserción: las 4 secciones eran `right` (adicional, M16) |
| 17 | [red](red-C-35/17-cta-fantasma.txt) | [green](green-C-35/17-cta-fantasma.txt) | Por aserción: el CTA no tenía `data-cta` ni variante fantasma (adicional, M17) |

Regresiones sin par nuevo: [login](green-C-35/login-regresion.txt), [modales](green-C-35/modales-regresion.txt), [appshell](green-C-35/appshell-regresion.txt), [smoke](green-C-35/smoke.txt); auxiliares: [contenido](green-C-35/aux-contenido-datos.txt) y [reveal](green-C-35/aux-reveal-section.txt).

## Desvíos

1. **Orden de recuperación (2.4)**: `RevealSection.tsx` y `RevealSection.test.tsx` se recuperaron en el mismo paso (la tarea pedía el test primero). Son tests auxiliares sin escenario, así que no afecta ningún RED.
2. **Tokens (2.5, 6.2)**: `--landing-hero-min-height`, `--landing-content-max-width`, `--landing-reveal-offset`, `--font-size-display` y `--color-navy-deep` se agregaron en las fases 3 y 5 porque el CSS y el test del fallback del login (08) los necesitan para quedar en verde. En la fase 6 se agregaron solo los de superficie; por eso el RED del escenario 10 falla por la ausencia de `--surface-navy` y `--surface-ivory-ice`. La lista del test auxiliar "no agrega colores nuevos" se amplió en cada paso con exactamente los tokens agregados.
3. **Cifras de contraste del design y del spec**: sobre navy `#011C40` los ratios reales son blanco 16,92, ice 12,73, borde `#C9DDE4` 12,04 y accent 6,47; el design y el spec decían 16,05, 12,35, 9,85 y 6,55. El test del escenario 10 verifica los valores calculados. Se corrigió la tabla de `design.md` y la orquestación corrigió también `specs/frontend-foundation/spec.md` (16,92 / 12,73 / 6,47). La superficie marfil-hielo usa alfa 0,96 (design) y no 0,95 (spec); el 15,70 se calcula sobre su RGB.
4. **`RootGate` (D7)**: el design indicaba que `RootGate` redirigía él mismo y que se quitaba el índice. Eso hacía fallar `Logout.test.tsx` (existente), que espera el nombre de usuario en `/` antes de que la agenda pida datos. Se conservó el índice `RootRedirect` bajo `AppShell`: `RootGate` muestra la portada solo al anónimo en `/` y, en el resto de los casos, actúa como `RequireAuth`. Se actualizó D7 en `design.md`. `routes[0]` y `routes[1]` no cambiaron de posición.
5. **Escenario 06**: el enlace "← Volver a Aqua" se implementó junto con la página de `/acceso` (escenario 05), así que el test 06 ya pasaba; su RED se documentó con la mutación M06.
6. **Test del escenario 11**: el `::backdrop` con `backdrop-filter` solo existe en `Dialog.module.css` (los otros tres CSS no son dueños del `<dialog>`); por eso el test exige blur en el `::backdrop` de `Dialog.module.css` y, en cada uno de los tres diálogos de turnos, la superficie marfil-hielo con borde de 1 px, blur propio y el fallback `@supports not` con `--color-background`.
7. **Tests 03 y 04** renderizan `LandingPage` directo dentro de `MemoryRouter` con observador, ticker y `reducedMotion` inyectados por props (`createAppRoutes` no los expone); 01, 02 y 05-09 usan `createMemoryRouter` + `createAppRoutes`.
8. **`npm run lint`**: devuelve exit 1 porque hay 3 advertencias que ya existen en `main` (`AppointmentFormDialog.tsx:36` y 2 en `Dialog.tsx`), de código de C-29/C-30 que C-35 no debe tocar. `npx eslint .` termina con exit 0 y 0 errores. Se eliminó una cuarta advertencia heredada (`LoginCarousel.tsx`) moviendo `createIntervalTicker` a `carouselTicker.ts`.
9. **`openspec validate`**: se ejecutó directamente (`openspec validate ... --strict`) y no con `cmd /c`, que abre una consola interactiva y no ejecuta el comando.
10. **Cambios de CSS fuera de la lista literal de tasks**: botón de pausa del carrusel movido abajo a la derecha (en la portada chocaba con la navegación superior) y con `min-height: 44px`; contenedor del formulario de turno con `max-height: calc(100dvh - 2 * var(--space-4))` en lugar de `90vh`; ítems de menú deshabilitados con "Próximamente" apilado bajo la etiqueta para que el `AppShell` entre en una línea a 1440 px. Se agregó la prop opcional `blurred` a `LoginCarousel` (carrusel difuminado de `/login`).
11. **Sin verificación visual**: no se levantó navegador; el layout a 1440/768/390 px, el desborde horizontal, el título de los modales a 390 px y el foco visible quedan para la fase 9.
12. **Auxiliar nuevo**: `frontend/src/test/cssText.ts` (parser de bloques CSS para las lecturas estáticas de los tests); no es un test ni lleva mutación.
13. **Fin de línea**: algunos archivos CSS que estaban en CRLF quedaron en LF tras editarlos; git los normaliza (`core.autocrlf=true`) y el diff no muestra ruido.
14. **Overlay del login a tokens**: los 6 `rgba(...)` heredados de C-34 en `LoginPage.module.css` (overlay del carrusel y botón de pausa) pasaron a `--login-overlay-start/-mid/-end` y `--carousel-toggle-bg/-bg-hover/-border`, con los mismos valores; se documentaron en `design.md` y se agregaron a la lista del test nuevo `landingTokens.test.ts`. Ningún test preexistente cambió.
15. **Mutaciones de los auxiliares**: los 9 tests recuperados de `cea858b` son tests nuevos del change y llevan mutación propia (A01-A09); en la trazabilidad siguen siendo auxiliares (24 = 13 + 5 + 6 no cambia).
16. **Fase 9**: no se hizo; las capturas las hará la usuaria en un navegador real contra la API. Queda sin marcar.
17. **Ajustes de diseño pedidos tras la revisión visual: hero centrado, nav y CTA a la izquierda, secciones intercaladas.** Logo grande en el centro, eslogan más chico y lead discreto debajo, navegación arriba a la izquierda, CTA "Explorar la clínica →" como enlace fantasma abajo a la izquierda junto al badge, "Pausar animación" abajo a la derecha; secciones 01 y 03 a la izquierda, 02 y 04 a la derecha (bloques del 60 %, entrada desde su lado, ancho completo y mitad de desplazamiento hasta 768 px). Se actualizaron `specs/frontend-landing/spec.md` (requisitos de 491 y 450 caracteres; título del escenario visual V2), `specs/frontend-foundation/spec.md` (requisito de AppShell, 450 caracteres), `design.md` (D1, D5, D6) y `tasks.md` (fase 10 y tabla). Nuevo token `--landing-logo-width`. Los 4 tests nuevos no son escenarios: se listan como adicionales con mutación M14-M17; 24 = 13 + 5 + 6 no cambia.
18. **Corrección de `.menuButton`**: el `<button>` heredaba el borde por defecto del navegador; ahora `border: 0; border-bottom: 2px solid transparent;`, alineado con `.menuLink` (test 14, M14).
19. **Disposición sin comprobar a ojo**: la composición del hero y las secciones intercaladas solo está cubierta por tests de estructura y CSS; las capturas a 1440/768/390 px (fase 9) las hará la usuaria.
