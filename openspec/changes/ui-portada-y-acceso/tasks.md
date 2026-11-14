# Tasks

## Reglas Mandatorias de Implementación y Testeo

> **Reglas Obligatorias para la fase de Apply (Strict TDD & Active Stack):**
>
> 1. **Regla C1 (Sin mocks de módulo ni stubs globales)**:
>    - Prohibido el uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers (`vi.useFakeTimers`, `vi.setSystemTime`), MSW o `waitFor` con tiempos largos (> 1000 ms).
>    - Enrutamiento con `createMemoryRouter` + `RouterProvider` pasando `createAppRoutes(clock)`.
>    - Temporizadores (`ticker`), detección de `prefers-reduced-motion` e `IntersectionObserver` **inyectados** por props o parámetros (jsdom no implementa `matchMedia` ni `IntersectionObserver`).
> 2. **Sin excepciones al linter ni al compilador**: Cero directivas `@ts-ignore`, `@ts-nocheck` o `eslint-disable` en código nuevo o editado.
> 3. **Preservación estricta de tests existentes**: Ningún test preexistente puede ser modificado, con la **única excepción documentada** de `frontend/src/test/smoke.test.tsx` (que pasa a esperar el heading accesible `"Aqua — Clínica Odontológica"` en `/`).
> 4. **Trazabilidad 1:1**: Un escenario testeable nuevo = un par RED/GREEN = un test distinto = una mutación en `mutaciones-C-35.py`, con evidencias `red-C-35/NN-nombre.txt` y `green-C-35/NN-nombre.txt`. Los escenarios históricos del login se mapean a su test existente en `main` (sin par ni mutación nuevos) y los visuales se verifican por captura a cargo de Claude. El script de trazabilidad debe fallar si dos escenarios comparten test o si falta cobertura (ver tabla final).
> 5. **Mutaciones con detector de inválidas**: Cada mutación debe provocar el fallo de su test asociado por aserción, sin romper la carga del módulo ni lanzar errores sintácticos. Cero mutaciones inválidas y SHA-256 restaurado.
> 6. **Calidad con exit code**: `npm run typecheck`, `npm run lint` y `npm run build` deben terminar con código de salida `0`.
> 7. **Evidencias legibles en UTF-8**: Todas las salidas se guardan en `docs/evidencias/` en texto plano UTF-8, sin datos reales de pacientes.
> 8. **Control de versiones**: La implementación partirá de la rama `c35-apply2` nacida de `main`.

---

## 1. Línea Base y Preparación

- [x] 1.1 Crear y posicionarse en la rama `c35-apply2` a partir de `main` (con C-29 y C-30 ya archivados). Confirmar que `git status --short` no muestra cambios inesperados; `.codex/` es untracked y no se toca. Prohibido tocar `.env`, `AGENTS.md`, `CLAUDE.md` ni `CHANGES.md`.
- [x] 1.2 Ejecutar la suite completa desde `frontend/` con `npm run test:run` y volcar la salida a `docs/evidencias/baseline-C-35.txt`. Anotar el total exacto de tests en verde y confirmar que no existen fallos preexistentes.
- [x] 1.3 **Skill y MCP (Context7 y appointment-frontend-ux)**:
  - Aplicar las directivas de `appointment-frontend-ux` sobre accesibilidad, tokens semánticos y preservación de C1.
  - Consultar en Context7 la documentación oficial de React Router 6.30.6 (anidamiento de rutas e índices) y CSS (`backdrop-filter` con fallback y `prefers-reduced-motion`).
  - Registrar las consultas y su impacto técnico en `docs/skills-mcp/evidencias/C-35-mcp-context7.md`.
- [x] 1.4 Registrar el estado base de los tests existentes que no se pueden modificar: `frontend/src/features/login/LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `frontend/src/App.test.tsx`, `frontend/src/shared/components/AppShell.test.tsx`, `AppShellBrand.test.tsx` y `frontend/src/features/auth/menuFor.test.ts`.

---

## 2. Reutilización desde c35-apply (sin checkout)

> **Cómo recuperar archivos de `cea858b` (obligatorio en todas las tareas de esta fase):**
>
> - Ejecutar **desde Git Bash**: `git show cea858b:<ruta> > <ruta>`.
> - **NUNCA** usar la redirección `>` de PowerShell: guarda el archivo en UTF-16 y rompe Vite, Vitest y los scripts de evidencias.
> - Alternativa en PowerShell: `git show cea858b:<ruta> | Out-File -Encoding utf8 <ruta>` (y verificar después que no haya quedado BOM, tarea 2.6).
> - Los archivos de test recuperados se recuperan **antes** que su código de producción, para que el RED de su escenario sea real.

- [x] 2.1 Recuperar desde Git Bash `frontend/src/features/login/carouselTicker.ts` (`git show cea858b:frontend/src/features/login/carouselTicker.ts > frontend/src/features/login/carouselTicker.ts`).
- [x] 2.2 Recuperar desde Git Bash `frontend/src/features/landing/revealObserver.ts` (crear antes la carpeta `frontend/src/features/landing/`).
- [x] 2.3 Recuperar desde Git Bash `frontend/src/features/landing/landingContent.ts` y `landingContent.test.ts`. Son **tests auxiliares** (datos del seed y teléfono `(0261) 555-0101`): no cubren ningún escenario de la matriz ni llevan mutación. Correr `npx vitest run src/features/landing/landingContent.test.ts` y guardar en `docs/evidencias/green-C-35/aux-contenido-datos.txt`.
- [x] 2.4 Recuperar desde Git Bash `frontend/src/features/landing/RevealSection.test.tsx` y, **después**, `RevealSection.tsx` y `RevealSection.module.css`. Adaptar `RevealSection.module.css` a `transform: translateX(20px)` + `opacity: 0` en `data-reveal="pending"`, transición de 200-250 ms hacia `transform: none` + `opacity: 1`, y `transition: none; transform: none; opacity: 1` ante `prefers-reduced-motion: reduce`. Los 3 tests de `RevealSection.test.tsx` son **auxiliares** (sin escenario ni mutación); correrlos y guardar en `docs/evidencias/green-C-35/aux-reveal-section.txt`.
- [x] 2.5 Recuperar desde Git Bash `frontend/src/shared/styles/landingTokens.test.ts`. Sus 3 tests originales son **auxiliares**. Como el archivo no existe en `main`, no está alcanzado por la regla 3: la lista `EXISTING_COLOR_PROPERTIES` del test "no agrega colores nuevos" se amplía únicamente con los tokens de superficie que exige el escenario 10 (navy translúcida y marfil-hielo). El test del escenario 10 se agrega en la tarea 6.1.
- [x] 2.6 **Verificación de codificación (antes de seguir)**: desde Git Bash, ejecutar `file <ruta>` sobre cada archivo recuperado en 2.1-2.5 y confirmar que todos reportan `UTF-8` o `ASCII` (nunca `UTF-16` ni `with BOM`). Alternativa: `head -c 3 <ruta> | od -An -tx1` no debe mostrar `ef bb bf` (BOM UTF-8) ni `ff fe` / `fe ff` (UTF-16). Guardar la salida en `docs/evidencias/C-35-encoding-recuperados.txt`. Si algún archivo falla, volver a recuperarlo desde Git Bash antes de continuar con la fase 3.

---

## 3. Portada Pública en `/` (`frontend-landing`, escenarios 01-04)

- [x] 3.1 **RED 01** — Crear `frontend/src/features/landing/LandingPage.test.tsx` con el test `"portada completa para anónimo en /"`: monta `createAppRoutes(clock)` en `/` sin sesión y verifica `<h1>` con nombre accesible `"Aqua — Clínica Odontológica"` (por el `alt` del logo claro), carrusel bajo overlay, eslogan `"Claridad en cada cuidado."`, CTA `"Explorar la clínica →"`, badge `"Sitio de demostración"`, enlaces de texto `"Inicio"`, `"La clínica"`, `"Acceder"` y `aria-current="page"` en el activo. Guardar en `docs/evidencias/red-C-35/01-portada-anonimo.txt`.
- [x] 3.2 **GREEN 01** — Implementar `LandingPage.tsx` + `LandingPage.module.css` (hero a pantalla completa con `var(--landing-hero-min-height)`, overlay navy sobre `LoginCarousel`, navegación de texto, CTA) y `RootGate` en `frontend/src/App.tsx` para que el anónimo vea la portada en `/`. Guardar en `docs/evidencias/green-C-35/01-portada-anonimo.txt`.
- [x] 3.3 **RED 02** — Crear `frontend/src/features/landing/RootGate.test.tsx` con el test `"usuario autenticado en / redirige a agenda"`: con sesión autenticada y `Clock` fijo inyectado, `/` termina en `/agenda?date=<hoy>` con replace y la portada no se renderiza. Guardar en `docs/evidencias/red-C-35/02-portada-autenticado-redirect.txt`.
- [x] 3.4 **GREEN 02** — Completar la bifurcación de `RootGate` (`RootRedirect` con replace para sesión autenticada; guardia `RequireAuth` cuando `pathname !== "/"`, según D7). Guardar en `docs/evidencias/green-C-35/02-portada-autenticado-redirect.txt`.
- [x] 3.5 **RED 03** — Agregar a `LandingPage.test.tsx` el test `"secciones editoriales entran con animación lateral al scrollear"`: con observador inyectado, cada sección pasa de `data-reveal="pending"` a `"revealed"`; muestra `"01 / Quiénes somos"`, `"02 / Servicios"`, `"03 / Equipo"`, `"04 / Horarios y contacto"`, el teléfono `"(0261) 555-0101"` y la franja de estado; y lectura estática de `RevealSection.module.css` con `translateX` y duración entre 200 y 250 ms. Guardar en `docs/evidencias/red-C-35/03-secciones-reveal-lateral.txt`.
- [x] 3.6 **GREEN 03** — Integrar las cuatro secciones en `LandingPage.tsx` envueltas en `RevealSection`, con el observador inyectable por props. Guardar en `docs/evidencias/green-C-35/03-secciones-reveal-lateral.txt`.
- [x] 3.7 **RED 04** — Agregar a `LandingPage.test.tsx` el test `"reduced motion desactiva la animación lateral y deja el contenido visible"`: con `reducedMotion` inyectado en `true` y, en otro montaje dentro del mismo test, sin `IntersectionObserver`, todas las secciones quedan en `"revealed"` desde el montaje y su contenido está en el DOM; lectura estática de `@media (prefers-reduced-motion: reduce)` con `transform: none` y `transition: none`. Guardar en `docs/evidencias/red-C-35/04-reduced-motion.txt`.
- [x] 3.8 **GREEN 04** — Propagar `reducedMotion` desde `LandingPage` hasta cada `RevealSection` y completar la regla CSS. Guardar en `docs/evidencias/green-C-35/04-reduced-motion.txt`.

---

## 4. Página de Selección de Rol en `/acceso` (`frontend-landing`, escenarios 05-06)

- [x] 4.1 **RED 05** — Crear `frontend/src/features/landing/AccesoPage.test.tsx` con el test `"navegación desde las tres tarjetas de rol hacia login"`: título `"¿Cómo querés ingresar?"`, enlaces `"Recepción"` → `/login?rol=recepcion`, `"Odontología"` → `/login?rol=odontologo`, `"Administración"` → `/login?rol=administrador`, texto `"El rol se confirma al ingresar"` y lectura estática de `AccesoPage.module.css` (superficie oscura, `border: 1px`, regla `:hover` / `:focus-visible` que aclara el borde). Guardar en `docs/evidencias/red-C-35/05-acceso-tarjetas.txt`.
- [x] 4.2 **GREEN 05** — Crear `AccesoPage.tsx` y `AccesoPage.module.css`; registrar `/acceso` al **final** de `createAppRoutes` (`routes[2]`). Guardar en `docs/evidencias/green-C-35/05-acceso-tarjetas.txt`.
- [x] 4.3 **RED 06** — Agregar a `AccesoPage.test.tsx` el test `"navegación de retorno con el enlace Volver a Aqua"`: al activar `"← Volver a Aqua"` la ubicación pasa a `/` y se ve la portada; lectura estática de la clase del enlace sin `border` ni `background` de botón. Guardar en `docs/evidencias/red-C-35/06-acceso-volver.txt`.
- [x] 4.4 **GREEN 06** — Implementar el enlace de texto `"← Volver a Aqua"` y su estilo. Guardar en `docs/evidencias/green-C-35/06-acceso-volver.txt`.

---

## 5. Login Translúcido en `/login` (`frontend-auth-session`, escenarios 07-09)

> `LoginPage.test.tsx` **no se modifica** (regla 3). Los tests nuevos van en el archivo dedicado `frontend/src/features/login/LoginPage.translucido.test.tsx`. Los 5 escenarios históricos del login quedan cubiertos por los tests existentes (ver tabla final).

- [x] 5.1 **RED 07** — Crear `LoginPage.translucido.test.tsx` con el test `"formulario translúcido en /login con etiqueta de rol y envío de credenciales"`: en `/login?rol=recepcion` se ven la etiqueta `"Recepción"`, `"← Volver"`, el logo claro y el heading `"Turnos Odontología"`; lectura estática de `LoginPage.module.css` con `backdrop-filter: blur(` y borde ice/accent; con credenciales válidas se envía `POST /api/auth/login`, se guarda el token y se redirige. Guardar en `docs/evidencias/red-C-35/07-login-translucido-rol.txt`.
- [x] 5.2 **GREEN 07** — Actualizar `LoginPage.tsx` y `LoginPage.module.css` (y `LoginForm.tsx` si aplica): `useSearchParams()` para `?rol`, superficie navy translúcida, borde ice/accent, campos oscuros, flecha del botón `"Ingresar"`, entrada fade + desplazamiento desactivable ante reduced motion. Guardar en `docs/evidencias/green-C-35/07-login-translucido-rol.txt`.
- [x] 5.3 **RED 08** — Agregar el test `"parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter"`: en `/login` y en `/login?rol=desconocido` no hay etiqueta de rol y el formulario sigue enviando; lectura estática de `LoginPage.module.css` con `@supports not (backdrop-filter: blur(1px))` y fondo opaco `#011C40`. Guardar en `docs/evidencias/red-C-35/08-login-rol-invalido-fallback.txt`.
- [x] 5.4 **GREEN 08** — Mapa cerrado de roles válidos (cualquier otro valor → sin etiqueta) y bloque `@supports not` en `LoginPage.module.css`. Guardar en `docs/evidencias/green-C-35/08-login-rol-invalido-fallback.txt`.
- [x] 5.5 **RED 09** — Agregar el test `"cierre de sesión y preservación del mensaje literal de sesión vencida"`: al llegar a `/login` con `state.expired = true` y `state.from`, se muestra en `role="alert"` exactamente `"La sesión venció. Iniciá sesión de nuevo."`, el foco inicia en `"Usuario"` y tras ingresar se vuelve a `state.from`. Guardar en `docs/evidencias/red-C-35/09-login-sesion-vencida.txt`. Si el test pasa sin cambios (comportamiento ya existente), registrar en la evidencia que el RED se obtiene con la mutación 09 aplicada y no con código faltante.
- [x] 5.6 **GREEN 09** — Asegurar que el rediseño conserva `SESSION_EXPIRED_MESSAGE`, el foco inicial y `state.from`. Guardar en `docs/evidencias/green-C-35/09-login-sesion-vencida.txt`.
- [x] 5.7 **Regresión Login** (sin par nuevo): `npx vitest run src/features/login/LoginPage.test.tsx src/features/login/LoginBrand.test.tsx src/features/login/LoginCarousel.test.tsx`; los 5 escenarios históricos deben seguir en verde con sus tests intactos. Guardar en `docs/evidencias/green-C-35/login-regresion.txt`.

---

## 6. Tokens y Superficies (`frontend-foundation`, escenarios 10-11)

- [x] 6.1 **RED 10** — Agregar a `frontend/src/shared/styles/landingTokens.test.ts` el test `"tokens de layout y contraste AA de superficies"`: `--landing-hero-min-height` = `60vh`, `--landing-content-max-width` = `1120px`, existencia de los tokens de superficie navy translúcida y marfil-hielo, y cálculo de contraste WCAG en el test (blanco, ice `#A7EBF2` y accent `#54ACBF` sobre `#011C40` >= 4.5:1; `--color-text` sobre marfil-hielo >= 4.5:1). Guardar en `docs/evidencias/red-C-35/10-tokens-contraste.txt`.
- [x] 6.2 **GREEN 10** — Agregar a `frontend/src/shared/styles/tokens.css` `--landing-hero-min-height: 60vh;`, `--landing-content-max-width: 1120px;` y los tokens de superficie (actualizando la lista del test auxiliar, tarea 2.5). Guardar en `docs/evidencias/green-C-35/10-tokens-contraste.txt`.
- [x] 6.3 **RED 11** — Crear `frontend/src/shared/components/DialogTheme.test.ts` con el test `"fallback sólido sin soporte de backdrop-filter"`: lectura estática de `Dialog.module.css`, `AppointmentFormDialog.module.css`, `AppointmentDetailDialog.module.css` y `AppointmentRescheduleDialog.module.css`; cada superficie usa marfil-hielo translúcido con borde de 1 px, `::backdrop` con `backdrop-filter: blur(` y un bloque `@supports not (backdrop-filter: blur(1px))` con fondo opaco. Guardar en `docs/evidencias/red-C-35/11-fallback-solido-modales.txt`.
- [x] 6.4 **GREEN 11** — Actualizar los cuatro CSS modules con la superficie marfil-hielo y su fallback, sin tocar markup ni props. Guardar en `docs/evidencias/green-C-35/11-fallback-solido-modales.txt`.
- [x] 6.5 **Regresión Modales** (sin par nuevo): `npx vitest run src/shared/components/Dialog.test.tsx src/features/appointments/`; todos los tests de C-29 y C-30 en verde. Guardar en `docs/evidencias/green-C-35/modales-regresion.txt`.

---

## 7. AppShell con Navegación sin Cajas (`frontend-foundation`, escenarios 12-13)

- [x] 7.1 **RED 12** — Crear `frontend/src/shared/components/AppShellNavigation.test.tsx` con el test `"enlaces de navegación activos y bloque de sesión en misma línea en 1440 px"`: el enlace `"Agenda"` tiene `aria-current="page"`; marca, `<nav>` y bloque de sesión (nombre + `"Cerrar sesión"`) son hijos del mismo contenedor de barra; lectura estática de `AppShell.module.css` (enlaces sin `background`/`border` de caja, línea inferior en el activo, `.topBar` con `display: flex` y `align-items: center`). jsdom no mide layout: la alineación real a 1440 px se confirma en la captura de la fase 9. Guardar en `docs/evidencias/red-C-35/12-appshell-nav-activa.txt`.
- [x] 7.2 **GREEN 12** — Ajustar `AppShell.module.css` (y `AppShell.tsx` solo si hace falta para la estructura). Guardar en `docs/evidencias/green-C-35/12-appshell-nav-activa.txt`.
- [x] 7.3 **RED 13** — Agregar el test `"ítems deshabilitados con Próximamente conservan semántica y accesibilidad"`: cada ítem futuro sigue siendo `<button disabled data-menu-item="...">` con el texto `"Próximamente"`; lectura estática de `.menuButton` y `.badge` sin `border`, sin fondo de pastilla y con `color: var(--color-text-muted)`. Guardar en `docs/evidencias/red-C-35/13-appshell-proximamente.txt`.
- [x] 7.4 **GREEN 13** — Resetear en CSS bordes y fondos de `.menuButton` y `.badge` conservando los `<button disabled data-menu-item>`. Guardar en `docs/evidencias/green-C-35/13-appshell-proximamente.txt`.
- [x] 7.5 **Regresión AppShell** (sin par nuevo): `npx vitest run src/shared/components/AppShell.test.tsx src/shared/components/AppShellBrand.test.tsx src/features/auth/menuFor.test.ts`. Guardar en `docs/evidencias/green-C-35/appshell-regresion.txt`.

---

## 8. Verificación, Suite de Regresión y Calidad

- [x] 8.1 **Actualizar `smoke.test.tsx` (único desvío autorizado)**: esperar el heading `"Aqua — Clínica Odontológica"` en lugar de `"Turnos Odontología"`. Correr `npx vitest run src/test/smoke.test.tsx` y guardar en `docs/evidencias/green-C-35/smoke.txt`. No es un escenario de la matriz ni lleva mutación.
- [x] 8.2 **Inmutabilidad de tests existentes**: `git diff --stat main -- '*.test.ts' '*.test.tsx'` debe mostrar como único archivo preexistente modificado `frontend/src/test/smoke.test.tsx` (los archivos recuperados de `cea858b` y los nuevos no existen en `main`). Guardar en `docs/evidencias/C-35-inmutabilidad-tests.txt`.
- [x] 8.3 **Suite completa**: `npm run test:run` desde `frontend/` → `docs/evidencias/suite-C-35.txt`; comparar con `baseline-C-35.txt` (sin regresiones; total = baseline + tests nuevos y auxiliares).
- [x] 8.4 **Mutaciones (13, una por escenario testeable nuevo)**: crear `docs/evidencias/mutaciones-C-35.py` con exactamente las 13 mutaciones de la tabla final (M01-M13). Cada una debe hacer fallar **por aserción** el test de su escenario; detector de mutaciones inválidas (error de carga o sintaxis = inválida); restauración verificada por SHA-256. Los tests históricos, auxiliares y `smoke.test.tsx` no llevan mutación. Volcar a `docs/evidencias/mutaciones-C-35.txt`.
- [x] 8.5 **Trazabilidad**: crear `docs/evidencias/trazabilidad-C-35.py` que lea los tres `spec.md` del change, cuente 24 escenarios y genere en `docs/evidencias/verify-C-35.md` la matriz escenario → test → mutación. El script **debe terminar con exit code distinto de 0** si: (a) dos escenarios comparten el mismo test (archivo + nombre); (b) un escenario testeable nuevo no tiene test, evidencia `red-C-35/NN-*.txt` y `green-C-35/NN-*.txt`, o mutación; (c) un escenario histórico no encuentra con búsqueda literal su test en `LoginPage.test.tsx`; (d) el total no es 13 nuevos + 5 históricos + 6 visuales = 24.
- [x] 8.6 **Calidad y OpenSpec** (nota: `npm run lint` estricto devuelve 1 por 3 advertencias previas de `main`; `npx eslint .` devuelve 0, ver Desvío 8 de `verify-C-35.md`): `npm run typecheck`, `npm run lint` y `npm run build` con exit code 0; `cmd /c openspec validate ui-portada-y-acceso --strict` y `cmd /c openspec validate --all --strict` con exit code 0. Volcar a `docs/evidencias/openspec-C-35.txt`.

---

## 9. Verificación Visual Independiente (A Cargo de Claude)

- [ ] 9.1 **Capturas en navegador real a 1440 px, 768 px y 390 px**:
  - Levantar el servidor de desarrollo (`npm run dev`) con datos de demostración del seed.
  - Capturar portada pública `/` en escritorio (1440 px), tablet (768 px) y móvil (390 px): validar hero de al menos 60vh, carrusel atenuado, enlaces de texto sin cajas, franja de demo y dos columnas editoriales.
  - Capturar animación de reveal lateral y comprobación con `prefers-reduced-motion`.
  - Capturar pantalla `/acceso` en 1440, 768 y 390 px: validar tres tarjetas oscuras con borde que se aclara en hover/focus.
  - Capturar pantalla `/login` en 1440, 768 y 390 px: validar formulario translúcido con `backdrop-filter: blur`, fallback sólido, contraste AA y etiqueta de rol cuando se pasa `?rol`.
  - Capturar modales de la agenda (`AppointmentFormDialog`, etc.): validar superficie clara suave marfil-hielo y desenfoque leve en backdrop.
  - Capturar `AppShell`: validar navegación sin cajas y alineación en una sola línea a 1440 px.
  - Guardar todas las capturas en `docs/evidencias/capturas/C-35-*.png` e incorporarlas al reporte final en `verify-C-35.md`.

---

## 10. Ajustes de Diseño tras la Revisión Visual (la fase 9 sigue pendiente)

> Cada test nuevo de esta fase tiene RED por aserción (`red-C-35/NN-*.txt`), GREEN (`green-C-35/NN-*.txt`) y su propia mutación en `mutaciones-C-35.py`. No son escenarios del spec: se listan como tests adicionales en la trazabilidad (24 = 13 + 5 + 6 no cambia).

- [x] 10.1 Actualizar `specs/frontend-landing/spec.md`, `specs/frontend-foundation/spec.md` y `design.md` (D1, D5, D6, tabla de tokens) con el hero centrado, la navegación y el CTA a la izquierda y las secciones intercaladas. Cada requisito editado queda por debajo de 500 caracteres. Se cambió el título del escenario visual V2.
- [x] 10.2 **Test 14 / M14** — `.menuButton` anula el borde por defecto del navegador (`border: 0; border-bottom: 2px solid transparent;`), en `AppShellNavigation.test.tsx`. Evidencia `14-appshell-menubutton-borde`.
- [x] 10.3 **Test 15 / M15** — `RevealSection` recibe `from="left" | "right"`, expone `data-side` y el CSS usa `translateX` negativo a la izquierda y positivo a la derecha (mitad del desplazamiento hasta 768 px). Test en `RevealSection.test.tsx`. Evidencia `15-reveal-lado`.
- [x] 10.4 **Test 16 / M16** — las secciones 01-04 alternan izquierda, derecha, izquierda, derecha en bloques del 60 % del ancho. Test en `LandingPage.test.tsx`. Evidencia `16-secciones-alternan-lado`.
- [x] 10.5 **Test 17 / M17** — el CTA "Explorar la clínica →" pasa a enlace fantasma (`data-cta`, `data-variant="ghost"`, sin relleno, línea inferior fina) y sigue siendo el único. Test en `LandingPage.test.tsx`. Evidencia `17-cta-fantasma`.
- [x] 10.6 Hero de la portada: logo centrado y grande (`--landing-logo-width`), eslogan más chico debajo con el lead discreto, navegación arriba a la izquierda, CTA y badge abajo a la izquierda y "Pausar animación" abajo a la derecha.

---

## Workflow Follow-up

- No archivar C-35 (`/opsx:archive ui-portada-y-acceso`) hasta que todas las tareas y capturas de la fase 9 estén completas y aprobadas por la autora.
- No commitear ni hacer `git push` sin instrucción explícita de la usuaria.

---

## Escenario → test → mutación

Totales: **24 escenarios** = **13 testeables nuevos** (13 pares RED/GREEN, 13 tests distintos, 13 mutaciones) + **5 históricos** (cubiertos por tests existentes en `main`, sin par ni mutación nuevos) + **6 visuales** (captura a cargo de Claude, fase 9).

| # | Spec | Escenario | Tipo | Test (archivo > nombre) | Mutación | Evidencia |
|---|------|-----------|------|-------------------------|----------|-----------|
| 01 | frontend-landing | Portada completa para anónimo en / | Nuevo | `features/landing/LandingPage.test.tsx` > "portada completa para anónimo en /" | M01: quitar `aria-current="page"` del enlace activo de la portada | `red/green-C-35/01-portada-anonimo.txt` |
| 02 | frontend-landing | Usuario autenticado en / redirige a agenda | Nuevo | `features/landing/RootGate.test.tsx` > "usuario autenticado en / redirige a agenda" | M02: `RootGate` renderiza `LandingPage` también con sesión autenticada | `red/green-C-35/02-portada-autenticado-redirect.txt` |
| 03 | frontend-landing | Secciones editoriales entran con animación lateral al scrollear | Nuevo | `features/landing/LandingPage.test.tsx` > "secciones editoriales entran con animación lateral al scrollear" | M03: `translateX(20px)` → `translateY(20px)` en `RevealSection.module.css` | `red/green-C-35/03-secciones-reveal-lateral.txt` |
| 04 | frontend-landing | Reduced motion desactiva la animación lateral y deja el contenido visible | Nuevo | `features/landing/LandingPage.test.tsx` > "reduced motion desactiva la animación lateral y deja el contenido visible" | M04: `RevealSection` ignora `reducedMotion` y arranca en `pending` | `red/green-C-35/04-reduced-motion.txt` |
| 05 | frontend-landing | Navegación desde las tres tarjetas de rol hacia login | Nuevo | `features/landing/AccesoPage.test.tsx` > "navegación desde las tres tarjetas de rol hacia login" | M05: `?rol=odontologo` → `?rol=odontologia` en la tarjeta | `red/green-C-35/05-acceso-tarjetas.txt` |
| 06 | frontend-landing | Navegación de retorno con el enlace Volver a Aqua | Nuevo | `features/landing/AccesoPage.test.tsx` > "navegación de retorno con el enlace Volver a Aqua" | M06: destino de "← Volver a Aqua" `/` → `/login` | `red/green-C-35/06-acceso-volver.txt` |
| 07 | frontend-auth-session | Formulario translúcido en /login con etiqueta de rol y envío de credenciales | Nuevo | `features/login/LoginPage.translucido.test.tsx` > "formulario translúcido en /login con etiqueta de rol y envío de credenciales" | M07: no renderizar la etiqueta de rol para valores válidos | `red/green-C-35/07-login-translucido-rol.txt` |
| 08 | frontend-auth-session | Parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter | Nuevo | `features/login/LoginPage.translucido.test.tsx` > "parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter" | M08: un `?rol` desconocido muestra su valor crudo como etiqueta | `red/green-C-35/08-login-rol-invalido-fallback.txt` |
| 09 | frontend-auth-session | Cierre de sesión y preservación del mensaje literal de sesión vencida | Nuevo | `features/login/LoginPage.translucido.test.tsx` > "cierre de sesión y preservación del mensaje literal de sesión vencida" | M09: no mostrar el aviso cuando `state.expired === true` | `red/green-C-35/09-login-sesion-vencida.txt` |
| 10 | frontend-foundation | Tokens de layout y contraste AA de superficies | Nuevo | `shared/styles/landingTokens.test.ts` > "tokens de layout y contraste AA de superficies" | M10: `--landing-hero-min-height: 60vh` → `50vh` | `red/green-C-35/10-tokens-contraste.txt` |
| 11 | frontend-foundation | Fallback sólido sin soporte de backdrop-filter | Nuevo | `shared/components/DialogTheme.test.ts` > "fallback sólido sin soporte de backdrop-filter" | M11: eliminar el bloque `@supports not (backdrop-filter: blur(1px))` de `Dialog.module.css` | `red/green-C-35/11-fallback-solido-modales.txt` |
| 12 | frontend-foundation | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Nuevo | `shared/components/AppShellNavigation.test.tsx` > "enlaces de navegación activos y bloque de sesión en misma línea en 1440 px" | M12: quitar `aria-current="page"` del enlace "Agenda" | `red/green-C-35/12-appshell-nav-activa.txt` |
| 13 | frontend-foundation | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Nuevo | `shared/components/AppShellNavigation.test.tsx` > "ítems deshabilitados con Próximamente conservan semántica y accesibilidad" | M13: restaurar `border: 1px solid` en `.badge` | `red/green-C-35/13-appshell-proximamente.txt` |
| H1 | frontend-auth-session | Login correcto del administrador | Histórico | Cubierto por test existente: `features/login/LoginPage.test.tsx` > "login correcto del administrador" | Test existente (sin mutación nueva) | `green-C-35/login-regresion.txt` |
| H2 | frontend-auth-session | Login correcto de recepción y del odontólogo | Histórico | Cubierto por test existente: `features/login/LoginPage.test.tsx` > "login correcto de recepción y del odontólogo" | Test existente (sin mutación nueva) | `green-C-35/login-regresion.txt` |
| H3 | frontend-auth-session | Credenciales inválidas con mensaje genérico | Histórico | Cubierto por test existente: `features/login/LoginPage.test.tsx` > "credenciales inválidas con mensaje genérico" | Test existente (sin mutación nueva) | `green-C-35/login-regresion.txt` |
| H4 | frontend-auth-session | Envío en curso y doble submit | Histórico | Cubierto por test existente: `features/login/LoginPage.test.tsx` > "envío en curso y doble submit" | Test existente (sin mutación nueva) | `green-C-35/login-regresion.txt` |
| H5 | frontend-auth-session | Accesibilidad del formulario | Histórico | Cubierto por test existente: `features/login/LoginPage.test.tsx` > "accesibilidad del formulario" | Test existente (sin mutación nueva) | `green-C-35/login-regresion.txt` |
| V1 | frontend-landing | Adaptabilidad de la portada en 1440, 768 y 390 px | Visual | Captura a cargo de Claude | — | `capturas/C-35-portada-*.png` |
| V2 | frontend-landing | Secciones editoriales intercaladas a ancho parcial en 1440 px y a ancho completo en 768 y 390 px | Visual | Captura a cargo de Claude | — | `capturas/C-35-secciones-*.png` |
| V3 | frontend-landing | Adaptabilidad de las tarjetas de acceso en 1440, 768 y 390 px | Visual | Captura a cargo de Claude | — | `capturas/C-35-acceso-*.png` |
| V4 | frontend-auth-session | Adaptabilidad de /login en 1440, 768 y 390 px | Visual | Captura a cargo de Claude | — | `capturas/C-35-login-*.png` |
| V5 | frontend-foundation | Superficie clara suave de modales verificada a 1440, 768 y 390 px | Visual | Captura a cargo de Claude | — | `capturas/C-35-modales-*.png` |
| V6 | frontend-foundation | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | Captura a cargo de Claude | — | `capturas/C-35-appshell-*.png` |
| E14 | frontend-foundation | (adicional, no es escenario) `.menuButton` sin borde por defecto | Adicional | `shared/components/AppShellNavigation.test.tsx` > "los ítems deshabilitados anulan el borde por defecto del navegador y alinean la línea inferior con los enlaces" | M14: quitar `border: 0` de `.menuButton` | `red/green-C-35/14-appshell-menubutton-borde.txt` |
| E15 | frontend-landing | (adicional) `RevealSection` desde su lado | Adicional | `features/landing/RevealSection.test.tsx` > "from=right desplaza en positivo y from=left en negativo" | M15: `translateX` izquierdo en positivo | `red/green-C-35/15-reveal-lado.txt` |
| E16 | frontend-landing | (adicional) secciones intercaladas | Adicional | `features/landing/LandingPage.test.tsx` > "las secciones editoriales alternan de lado: 01 izquierda, 02 derecha, 03 izquierda, 04 derecha" | M16: la sección 02 entra desde la izquierda | `red/green-C-35/16-secciones-alternan-lado.txt` |
| E17 | frontend-landing | (adicional) CTA fantasma | Adicional | `features/landing/LandingPage.test.tsx` > "el CTA de la portada es un enlace fantasma sin relleno y sigue siendo el único" | M17: `.cta` con fondo `--color-primary` | `red/green-C-35/17-cta-fantasma.txt` |

Rutas de test relativas a `frontend/src/`; evidencias relativas a `docs/evidencias/`. Los nombres de los 5 tests históricos se verificaron con `grep` sobre `frontend/src/features/login/LoginPage.test.tsx` de `main` (líneas 75, 118, 176, 233 y 283). El test existente `"el 401 del login no es sesión vencida"` (línea 208) no está asignado a ningún escenario.
