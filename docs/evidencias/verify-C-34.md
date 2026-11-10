# Verificación C-34 — ui-identidad-visual

## Estado

- Change: `ui-identidad-visual`
- Tasks 8.1 a 8.4 y 8.6 a 8.9: completadas. Task 8.5: no ejecutada por decisión del alcance.
- Evidencias: `docs/evidencias/red-C-34/`, `baseline-C-34.txt`, `ratios-C-34.txt`, `mutaciones-C-34.txt`, `trazabilidad-C-34.txt`, `test-C-34-final.txt`.
- Tests existentes modificados: solo `StatusBadge.test.tsx` y `appointmentStatusTokens.test.ts`, únicamente valores de color/ratio.
- Datos de pacientes: no se usan datos reales; las menciones a DNI de la evidencia son texto de documentación/roadmap, sin datos personales.

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `define los tokens semánticos con los valores del design` | `frontend/src/shared/styles/tokens.css` | `-  --color-primary: #26658C; +  --color-primary: #26658D;` | `AssertionError: expected '#26658D' to be '#26658C' // Object.is equality` |
| 2 | `mantiene los contrastes de texto del design` | `frontend/src/shared/styles/tokens.css` | `-  --color-text: #011C40; +  --color-text: #011C41;` | `AssertionError: expected '15.68' to be '15.70' // Object.is equality` |
| 3 | `define Jost para títulos y Manrope para texto con fallback al system stack` | `frontend/src/shared/styles/tokens.css` | `-  --font-family-heading: "Jost Variable", system-ui, -apple-system, "Segoe UI", Roboto, "` | `AssertionError: expected '"Jost", system-ui, -apple-system, "Se…' to contain '"Jost Variab` |
| 4 | `el body conserva la base y usa Manrope después` | `frontend/src/shared/styles/reset.css` | `-  font-family: var(--font-family-base);` | `AssertionError: expected '*,\n*::before,\n*::after {\n  box-siz…' to match /body\s*\{[\s\S` |
| 5 | `declara las dependencias y las importa antes de los estilos en el entry point` | `frontend/src/main.tsx` | `+import "./shared/styles/tokens.css"; -import "./shared/styles/tokens.css";` | `AssertionError: expected 120 to be greater than 193` |
| 6 | `no usa URLs de Google Fonts ni CDNs externos en src` | `frontend/src/main.tsx` | `-import "@fontsource-variable/jost"; +import "https://fonts.googleapis.com/css2?family=Jos` | `AssertionError: expected [ Array(1) ] to deeply equal []` |
| 7 | `muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica` | `frontend/src/shared/components/AppShell.tsx` | `-          <img src={isotipoAqua} alt="" className={styles.brandLogo} /> +          <img s` | `AssertionError: expected null not to be null` |
| 8 | `ubica logo, Aqua y subtítulo en la marca y el subtítulo usa la clase oculta en 768 px` | `frontend/src/shared/components/AppShell.tsx` | `-        <div className={styles.brand} data-brand="aqua"> +        <div className={styles.` | `AssertionError: expected null not to be null` |
| 9 | `muestra el logo claro, el heading accesible y la bajada` | `frontend/src/features/login/LoginPage.tsx` | `-          <img src={logoAquaClaro} alt="Aqua — Clínica Odontológica" className={styles.lo` | `AssertionError: expected null not to be null` |
| 10 | `renderiza sin window.matchMedia, usa reduced motion falso y permite avanzar el carrusel` | `frontend/src/features/login/LoginCarousel.tsx` | `-    return false; +    return true;` | `AssertionError: expected '0' to be '1' // Object.is equality` |
| 11 | `inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta` | `frontend/src/features/login/LoginCarousel.tsx` | `-      setActiveIndex((current) => (current + 1) % SLIDES.length); +      setActiveIndex((` | `AssertionError: expected '2' to be '1' // Object.is equality` |
| 12 | `pausa y reanuda el avance sin aria-pressed` | `frontend/src/features/login/LoginCarousel.tsx` | `-    if (paused \|\| reducedMotion) { +    if (reducedMotion) {` | `AssertionError: expected '1' to be '0' // Object.is equality` |
| 13 | `reduced motion desactiva la rotación y el Ken Burns` | `frontend/src/features/login/LoginCarousel.tsx` | `-  const reducedMotion = prefersReducedMotion ?? detectPrefersReducedMotion(); +  const re` | `AssertionError: expected '1' to be '0' // Object.is equality` |
| 14 | `cancela el ticker al desmontar` | `frontend/src/features/login/LoginCarousel.tsx` | `-    return ticker(() => { +    ticker(() => {` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| 15 | `muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa` | `frontend/src/features/login/LoginCarousel.tsx` | `-            aria-hidden="true" +            aria-hidden="false"` | `Error: expect(element).toHaveAttribute("aria-hidden", "true") // element.getAttribute("ari` |
| 16 | `documenta las fotografías, el logo y la licencia de las tipografías` | `README.md` | `-\| Tipografías Jost y Manrope \| Paquetes '@fontsource-variable/jost' y '@fontsource-variab` | `AssertionError: expected '# turnos-odontologia\n\nSistema web d…' to contain 'SIL Open Fon` |
<!-- mutaciones:fin -->

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Requisito | Escenario | Test | Mutación |
|---|---|---|---|---|
| 1 | Tokens de diseño y colores por estado | El mapa cubre los cinco estados sin undefined | `src/shared/styles/appointmentStatusTokens.test.ts > el mapa cubre los cinco estados sin undefined` | — (test existente actualizado) |
| 2 | Tokens de diseño y colores por estado | Cada par texto y fondo cumple contraste AA | `src/shared/styles/appointmentStatusTokens.test.ts > cada par texto y fondo cumple contraste AA` | — (test existente actualizado) |
| 3 | Tokens de diseño y colores por estado | Los tokens de paleta usados como texto cumplen contraste AA | `src/shared/styles/aquaPalette.test.ts > mantiene los contrastes de texto del design` | 2 |
| 4 | Tokens de diseño y colores por estado | El foco es visible | `src/shared/styles/tokens.test.ts > el foco es visible` | — (test existente actualizado) |
| 5 | Tokens de diseño y colores por estado | La familia base del sistema se conserva como fallback | `src/shared/styles/tokens.test.ts > usa el system font stack en el reset ; src/shared/styles/fonts.test.ts > el body conserva la base y usa Manrope después` | 4 |
| 6 | Tipografías autoalojadas sin CDN | Las dependencias y los imports de fuentes están en el frontend | `src/shared/styles/fonts.test.ts > declara las dependencias y las importa antes de los estilos en el entry point` | 5 |
| 7 | Tipografías autoalojadas sin CDN | No hay fuentes externas ni CDN | `src/shared/styles/fonts.test.ts > no usa URLs de Google Fonts ni CDNs externos en src` | 6 |
| 8 | Tipografías autoalojadas sin CDN | Las familias se aplican con tokens y fallback | `src/shared/styles/fonts.test.ts > define Jost para títulos y Manrope para texto con fallback al system stack` | 3 |
| 9 | Barra única con la marca Aqua | Barra de escritorio con la marca completa | `src/shared/components/AppShellBrand.test.tsx > muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica` | 7 |
| 10 | Barra única con la marca Aqua | Barra de tablet con solo Aqua y máximo dos renglones | `— (verificación visual)` | — |
| 11 | Barra única con la marca Aqua | La barra usa el isotipo oscuro | `src/shared/components/AppShellBrand.test.tsx > muestra una sola barra con logo decorativo, Aqua y Clínica Odontológica` | 7 |
| 12 | Barra única con la marca Aqua | El título de página no se ve como una segunda barra | `— (verificación visual)` | — |
| 13 | Créditos de assets y tipografías | El README acredita fotos, logo y tipografías | `src/test/readmeCredits.test.ts > documenta las fotografías, el logo y la licencia de las tipografías` | 16 |
| 14 | Logo del login sobre fondo oscuro | El login muestra la variante de logo clara | `src/features/login/LoginBrand.test.tsx > muestra el logo claro, el heading accesible y la bajada` | 9 |
| 15 | Logo del login sobre fondo oscuro | El fondo inmediato del logo es oscuro | `— (verificación visual)` | — |
| 16 | Logo del login sobre fondo oscuro | El encabezado accesible del login se conserva | `src/features/login/LoginBrand.test.tsx > muestra el logo claro, el heading accesible y la bajada ; src/test/smoke.test.tsx > monta App y muestra el título` | 9 |
| 17 | Bajada y tarjeta del login | La bajada es visible | `src/features/login/LoginBrand.test.tsx > muestra el logo claro, el heading accesible y la bajada` | 9 |
| 18 | Bajada y tarjeta del login | La tarjeta tipo vidrio sobre overlay navy | `— (verificación visual)` | — |
| 19 | Carrusel decorativo del login | Avanza al llamar al ticker y vuelve a la primera tras la quinta | `src/features/login/LoginCarousel.test.tsx > inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta` | 11 |
| 20 | Pausa y ciclo de vida del carrusel | La pausa detiene el avance | `src/features/login/LoginCarousel.test.tsx > pausa y reanuda el avance sin aria-pressed` | 12 |
| 21 | Pausa y ciclo de vida del carrusel | Reduced motion desactiva rotación y Ken Burns | `src/features/login/LoginCarousel.test.tsx > reduced motion desactiva la rotación y el Ken Burns` | 13 |
| 22 | Pausa y ciclo de vida del carrusel | El ticker se cancela al desmontar | `src/features/login/LoginCarousel.test.tsx > cancela el ticker al desmontar` | 14 |
| 23 | Detección de reduced motion en producción | Sin matchMedia el login renderiza sin error | `src/features/login/LoginBrand.test.tsx > renderiza sin window.matchMedia, usa reduced motion falso y permite avanzar el carrusel` | 10 |
| 24 | Detección de reduced motion en producción | El CSS desactiva Ken Burns y fundido con reduced motion | `— (verificación CSS/grep)` | — |
| 25 | Fotos decorativas y Ken Burns | Las fotos son decorativas y accesibles | `src/features/login/LoginCarousel.test.tsx > muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa` | 15 |
| 26 | Fotos decorativas y Ken Burns | La clase de Ken Burns está solo en la foto activa | `src/features/login/LoginCarousel.test.tsx > muestra cinco fotos decorativas y la clase de Ken Burns solo en la activa` | 15 |
| 27 | Fotos decorativas y Ken Burns | Reduced motion quita la clase de Ken Burns | `src/features/login/LoginCarousel.test.tsx > reduced motion desactiva la rotación y el Ken Burns` | 13 |
| 28 | Fotos decorativas y Ken Burns | Duración y reinicio del Ken Burns | `— (verificación CSS/grep)` | — |
<!-- trazabilidad:fin -->

## Verificación visual y CSS

| Escenario | Verificación |
|---|---|
| Barra de tablet con solo Aqua y máximo dos renglones | Captura a 768 px (task 8.5, no ejecutada) |
| El título de página no se ve como una segunda barra | Captura a 1440/768 px (task 8.5, no ejecutada) |
| Fondo inmediato del logo oscuro | Inspección visual del login |
| Tarjeta tipo vidrio sobre overlay navy | Inspección visual del login |
| CSS desactiva Ken Burns y fundido con reduced motion | `grep` en `LoginPage.module.css` |
| Duración y reinicio del Ken Burns | `grep` en `LoginPage.module.css` |

## Desvíos

1. **RED de task 6.3**: El fallo inicial (RED) al escribir el test del carrusel ocurrió por resolución de módulo al importar `LoginCarousel` antes de que el archivo existiera, en lugar de una aserción fallida de un componente existente. El comportamiento funcional de rotación y ciclo está cubierto y validado por la mutación 11 (`inicia en hero-1-sala-de-espera, avanza con el ticker y vuelve a la primera tras la quinta`).
2. **Test 16 adicional de dependencias e imports de fuentes**: Se agregó un test adicional (`declara las dependencias y las importa antes de los estilos en el entry point` en `fonts.test.ts`) para garantizar a nivel de código que `@fontsource-variable/jost` y `@fontsource-variable/manrope` están declarados en `dependencies` e importados en `main.tsx` antes de `tokens.css`, cubierto por la mutación 5.
3. **Hallazgos de verificación visual H1-H3 y su corrección**:
   - **H1 (PageShell como segunda barra)**: El encabezado `<header>` de `PageShell` renderizaba fondo `var(--color-surface)`, borde inferior y sombra, aparentando una segunda barra redundante debajo de la barra de `AppShell`. Se corrigió en `PageShell.module.css` eliminando fondo, borde y sombra, dejando solo el título con `var(--font-family-heading)` y su padding. `PageShell.tsx` y su test unitario se mantuvieron sin cambios.
   - **H2 (Distribución en tablet <= 768 px)**: En viewport <= 768 px la barra no distribuía limpiamente los elementos. Se corrigió en `AppShell.module.css` reorganizando con `@media (max-width: 768px)`: la marca (`order: 1`) y los controles de sesión (`order: 2`) comparten el primer renglón con `justify-content: space-between`, y la navegación (`order: 3`) pasa al segundo renglón completo (`width: 100%`) en una sola fila con scroll horizontal (`flex-wrap: nowrap; overflow-x: auto`), sin scroll horizontal a nivel de página ni superar dos renglones.
   - **H3 (Isotipo oscuro en barra en vez de logo completo)**: `logo-aqua-oscuro.png` contiene texto integrado de la marca ("Aqua Clínica Odontológica"), que al renderizarse junto a los textos de la barra provocaba duplicación e ilegibilidad. Se corrigió reemplazando el asset por el isotipo `frontend/src/assets/brand/isotipo-aqua.png` con `alt=""`, ajustando `AppShellBrand.test.tsx` (con ciclo RED/GREEN) y la mutación 7 en `mutaciones-C-34.py`.

## Comandos

| Comando | Código | Evidencia |
|---|---|---|
| `python docs/evidencias/mutaciones-C-34.py --check` | 0 | 16 mutaciones bien definidas |
| `python docs/evidencias/mutaciones-C-34.py` | 0 | 16/16 mutaciones muertas, 0 inválidas, SHA-256 sin cambios: si; `mutaciones-C-34.txt` |
| `python docs/evidencias/trazabilidad-C-34.py` | 0 | 28 escenarios, 0 problemas; `trazabilidad-C-34.txt` |
| `npm test -- --run` | 0 | 41 archivos, 164 tests verdes; baseline 148 + 16 nuevos; `test-C-34-final.txt` |
| `npx tsc --noEmit` | 0 | `tsc-C-34.txt` |
| `npx eslint .` | 0 | 0 errores, 1 warning `react-refresh/only-export-components` en `LoginCarousel.tsx`; `eslint-C-34.txt` |
| `npm run build` | 0 | `build-C-34-final.txt`; fuentes y assets empaquetados por Vite |
| UTF-8 de evidencias C-34 | 0 | 20 archivos, 0 no UTF-8 |
| Verificación visual 1440/768 px | no ejecutada | task 8.5, a cargo de Claude |
