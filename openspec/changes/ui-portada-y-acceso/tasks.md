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
> 4. **Trazabilidad 1:1**: Un escenario del spec = un test automatizado = una mutación en `mutaciones-C-35.py` (salvo escenarios marcados expresamente como verificación visual por captura a cargo de Claude). El script de trazabilidad debe fallar si dos escenarios comparten test o si falta cobertura.
> 5. **Mutaciones con detector de inválidas**: Cada mutación debe provocar el fallo de su test asociado por aserción, sin romper la carga del módulo ni lanzar errores sintácticos. Cero mutaciones inválidas y SHA-256 restaurado.
> 6. **Calidad con exit code**: `npm run typecheck`, `npm run lint` y `npm run build` deben terminar con código de salida `0`.
> 7. **Evidencias legibles en UTF-8**: Todas las salidas se guardan en `docs/evidencias/` en texto plano UTF-8, sin datos reales de pacientes.
> 8. **Control de versiones**: La implementación partirá de la rama `c35-apply2` nacida de `main`.

---

## 1. Línea Base y Preparación

- [ ] 1.1 Crear y posicionarse en la rama `c35-apply2` a partir de `main` (con C-29 y C-30 ya archivados). Confirmar que `git status --short` no muestra cambios inesperados; `.codex/` es untracked y no se toca. Prohibido tocar `.env`, `AGENTS.md`, `CLAUDE.md` ni `CHANGES.md`.
- [ ] 1.2 Ejecutar la suite completa desde `frontend/` con `npm run test:run` y volcar la salida a `docs/evidencias/baseline-C-35.txt`. Anotar el total exacto de tests en verde y confirmar que no existen fallos preexistentes.
- [ ] 1.3 **Skill y MCP (Context7 y appointment-frontend-ux)**:
  - Aplicar las directivas de `appointment-frontend-ux` sobre accesibilidad, tokens semánticos y preservación de C1.
  - Consultar en Context7 la documentación oficial de React Router 6.30.6 (anidamiento de rutas e índices) y CSS (`backdrop-filter` con fallback y `prefers-reduced-motion`).
  - Registrar las consultas y su impacto técnico en `docs/skills-mcp/evidencias/C-35-mcp-context7.md`.
- [ ] 1.4 Registrar el estado base de los tests existentes que no se pueden modificar: `frontend/src/features/login/LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `frontend/src/App.test.tsx`, `frontend/src/shared/components/AppShell.test.tsx`, `AppShellBrand.test.tsx` y `frontend/src/features/auth/menuFor.test.ts`.

---

## 2. Reutilización desde c35-apply (sin checkout)

- [ ] 2.1 Reutilizar `landingTokens.test.ts` y tokens de layout:
  - Recuperar el archivo con `git show cea858b:frontend/src/shared/styles/landingTokens.test.ts > frontend/src/shared/styles/landingTokens.test.ts`.
  - **RED**: Ejecutar `npx vitest run src/shared/styles/landingTokens.test.ts` comprobando el fallo por falta de tokens de layout. Guardar en `docs/evidencias/red-C-35/tokens-layout.txt`.
  - **GREEN**: Agregar `--landing-hero-min-height: 60vh;` y `--landing-content-max-width: 1120px;` a `frontend/src/shared/styles/tokens.css`. Correr el test y verificar que pasa en verde. Guardar en `docs/evidencias/green-C-35/tokens-layout.txt`.
- [ ] 2.2 Reutilizar `carouselTicker.ts`:
  - Extraer con `git show cea858b:frontend/src/features/login/carouselTicker.ts > frontend/src/features/login/carouselTicker.ts`.
- [ ] 2.3 Reutilizar `landingContent.ts` y su test:
  - Extraer `landingContent.ts` y `landingContent.test.ts` desde `cea858b:frontend/src/features/landing/`.
  - Ejecutar `npx vitest run src/features/landing/landingContent.test.ts` y confirmar que pasa en verde (validando profesionales, servicios, horarios y teléfono `(0261) 555-0101`). Guardar en `docs/evidencias/green-C-35/contenido-datos.txt`.
- [ ] 2.4 Reutilizar `revealObserver.ts`:
  - Extraer con `git show cea858b:frontend/src/features/landing/revealObserver.ts > frontend/src/features/landing/revealObserver.ts`.
- [ ] 2.5 Reutilizar y adaptar `RevealSection.tsx` (+ `.module.css` + `.test.tsx`):
  - Extraer los 3 archivos desde `cea858b:frontend/src/features/landing/`.
  - Adaptar `RevealSection.module.css` para aplicar `transform: translateX(20px)` y `opacity: 0` en estado `data-reveal="pending"`, con transición de 200-250 ms hacia `transform: none` y `opacity: 1`, y desactivación ante reduced motion.
  - Ejecutar `npx vitest run src/features/landing/RevealSection.test.tsx` y guardar en `docs/evidencias/green-C-35/reveal-section.txt`.

---

## 3. Portada Pública en `/` (`frontend-landing`)

- [ ] 3.1 **RED** — Crear `frontend/src/features/landing/LandingPage.test.tsx` con un test que verifique el montaje de la portada en `/` para usuarios anónimos: `<h1>` con logo claro (`alt="Aqua — Clínica Odontológica"`), eslogan "Claridad en cada cuidado.", CTA "Explorar la clínica →", badge "Sitio de demostración", franja "Estado actual", enlaces de navegación de texto sin cajas ("Inicio", "La clínica", "Acceder") y `aria-current="page"` en el activo. Guardar salida RED en `docs/evidencias/red-C-35/portada-hero.txt`.
- [ ] 3.2 **GREEN** — Implementar `frontend/src/features/landing/LandingPage.tsx` y `LandingPage.module.css` con el hero a pantalla completa, overlay navy oscuro sobre `LoginCarousel`, enlaces de texto superior y CTA. Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/portada-hero.txt`.
- [ ] 3.3 **RED** — Agregar a `LandingPage.test.tsx` un test de las cuatro secciones editoriales ("01 / Quiénes somos", "02 / Servicios", "03 / Equipo", "04 / Horarios y contacto"), teléfono ficticio `(0261) 555-0101` y su integración con `RevealSection`. Guardar salida RED en `docs/evidencias/red-C-35/portada-secciones.txt`.
- [ ] 3.4 **GREEN** — Integrar las secciones editoriales en `LandingPage.tsx` envolviéndolas en `RevealSection`. Verificar que el test pasa. Guardar en `docs/evidencias/green-C-35/portada-secciones.txt`.
- [ ] 3.5 **RED** — Agregar test que verifique que un usuario con sesión autenticada que ingresa a `/` es redirigido con replace a `/agenda?date=<hoy>` y no renderiza la portada. Guardar salida RED en `docs/evidencias/red-C-35/portada-autenticado-redirect.txt`.
- [ ] 3.6 **GREEN** — Configurar `RootGate` en `frontend/src/App.tsx` para coordinar la bifurcación entre `LandingPage` (anónimo) y `RootRedirect` (autenticado) en la ruta `/`. Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/portada-autenticado-redirect.txt`.

---

## 4. Página de Selección de Rol en `/acceso` (`frontend-landing`)

- [ ] 4.1 **RED** — Crear `frontend/src/features/landing/AccesoPage.test.tsx` con tests que comprueben:
  - Título "¿Cómo querés ingresar?".
  - Tres tarjetas-enlace para Recepción (`/login?rol=recepcion`), Odontología (`/login?rol=odontologo`) y Administración (`/login?rol=administrador`).
  - Tarjetas con superficie oscura y borde de 1 px.
  - Texto explicativo "El rol se confirma al ingresar".
  - Enlace "← Volver a Aqua" sin caja hacia `/`.
  - Guardar salida RED en `docs/evidencias/red-C-35/acceso-tarjetas.txt`.
- [ ] 4.2 **GREEN** — Crear `frontend/src/features/landing/AccesoPage.tsx` y `AccesoPage.module.css`. Registrar la ruta `/acceso` al final de `createAppRoutes` en `frontend/src/App.tsx`. Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/acceso-tarjetas.txt`.

---

## 5. Login Translúcido en `/login` (`frontend-auth-session`)

- [ ] 5.1 **RED** — Crear un test en `LoginPage.test.tsx` (o archivo dedicado `LoginPage.translucido.test.tsx`) que verifique:
  - Enlace "← Volver" (hacia `/acceso` o `/`).
  - Etiqueta de rol visible cuando se pasa `?rol=recepcion` ("Recepción"), `?rol=odontologo` ("Odontología") o `?rol=administrador` ("Administración").
  - Ausencia de etiqueta si `?rol` no se proporciona o si es desconocido.
  - Tarjeta del formulario con clase translúcida y fallback sólido.
  - Botón "Ingresar" con flecha indicadora.
  - Guardar salida RED en `docs/evidencias/red-C-35/login-translucido.txt`.
- [ ] 5.2 **GREEN** — Actualizar `frontend/src/features/login/LoginPage.tsx` y `LoginPage.module.css` (y `LoginForm.tsx` si aplica):
  - Incorporar la lectura de `useSearchParams()` para `?rol`.
  - Aplicar superficie navy translúcida (`backdrop-filter: blur(12px)` con fallback sólido), borde ice/accent a baja opacidad y campos oscuros con línea fina.
  - Agregar transición de entrada fade + desplazamiento desactivable ante reduced motion.
  - Asegurar que el aviso de sesión vencida despliega `SESSION_EXPIRED_MESSAGE` ("La sesión venció. Iniciá sesión de nuevo.").
  - Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/login-translucido.txt`.
- [ ] 5.3 **Regresión Login**: Ejecutar la suite original de login: `npx vitest run src/features/login/LoginPage.test.tsx src/features/login/LoginBrand.test.tsx src/features/login/LoginCarousel.test.tsx` y confirmar que todos los tests históricos pasan sin alteraciones. Guardar en `docs/evidencias/green-C-35/login-regresion.txt`.

---

## 6. Modales Claros Suaves de la Agenda (Decisión A, `frontend-foundation`)

- [ ] 6.1 **RED** — Crear `frontend/src/shared/components/DialogTheme.test.tsx` que verifique la presencia de las clases y estilos de superficie clara suave marfil-hielo en `Dialog.module.css`, `AppointmentFormDialog.module.css`, `AppointmentDetailDialog.module.css` y `AppointmentRescheduleDialog.module.css`: fondo marfil-hielo translúcido (`rgba(243, 247, 250, 0.95)`), borde fino de 1 px, `::backdrop` con desenfoque suave y sombra sutil. Guardar salida RED en `docs/evidencias/red-C-35/modales-claros.txt`.
- [ ] 6.2 **GREEN** — Actualizar los CSS modules de los cuatro componentes modales aplicando los tokens y valores de superficie clara suave marfil-hielo, sin alterar markup ni props. Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/modales-claros.txt`.
- [ ] 6.3 **Regresión Modales**: Ejecutar `npx vitest run src/shared/components/Dialog.test.tsx src/features/appointments/` y confirmar que todos los tests de C-29 y C-30 continúan pasando al 100%. Guardar en `docs/evidencias/green-C-35/modales-regresion.txt`.

---

## 7. AppShell con Navegación sin Cajas (`frontend-foundation`)

- [ ] 7.1 **RED** — Crear un test en `frontend/src/shared/components/AppShellNavigation.test.tsx` que valide:
  - Los enlaces de navegación no tienen fondos de caja.
  - El ítem activo ("Agenda") posee línea fina inferior y `aria-current="page"`.
  - El badge "Próximamente" se renderiza sin borde exterior ni caja de pastilla (como texto secundario plano).
  - En viewport de escritorio (1440 px), la barra de encabezado ubica marca, menú y bloque de sesión en la misma fila horizontal.
  - Guardar salida RED en `docs/evidencias/red-C-35/appshell-sin-cajas.txt`.
- [ ] 7.2 **GREEN** — Modificar `frontend/src/shared/components/AppShell.module.css` (y `AppShell.tsx` si es necesario):
  - Mantener los `<button disabled data-menu-item="...">` para preservar compatibilidad con `AppShell.test.tsx`.
  - Resetear en CSS los bordes y fondos de `.menuButton` y `.badge`.
  - Estilizar el enlace activo con línea inferior en `--color-primary` o `--color-accent`.
  - Configurar flexbox en `.topBar` para alinear marca, nav y controles de sesión en una sola línea en 1440 px.
  - Correr el test y verificar verde. Guardar en `docs/evidencias/green-C-35/appshell-sin-cajas.txt`.
- [ ] 7.3 **Regresión AppShell**: Ejecutar `npx vitest run src/shared/components/AppShell.test.tsx src/shared/components/AppShellBrand.test.tsx src/features/auth/menuFor.test.ts` y verificar que todos los tests existentes pasan intactos. Guardar en `docs/evidencias/green-C-35/appshell-regresion.txt`.

---

## 8. Verificación, Suite de Regresión y Calidad

- [ ] 8.1 **Actualizar `smoke.test.tsx` (Único desvío autorizado)**:
  - Modificar `frontend/src/test/smoke.test.tsx` para esperar el heading accesible `"Aqua — Clínica Odontológica"` en lugar de `"Turnos Odontología"`.
  - Ejecutar `npx vitest run src/test/smoke.test.tsx` y confirmar que pasa en verde. Guardar en `docs/evidencias/green-C-35/smoke.txt`.
- [ ] 8.2 **Verificación de inmutabilidad de tests existentes**:
  - Ejecutar `git diff --stat` sobre los archivos de test preexistentes.
  - Verificar que el **único** archivo modificado es `frontend/src/test/smoke.test.tsx`; todos los demás deben mostrar 0 diferencias.
- [ ] 8.3 **Suite de pruebas completa**:
  - Ejecutar `npm run test:run` desde `frontend/` y volcar la salida completa a `docs/evidencias/suite-C-35.txt`.
  - Comparar contra `baseline-C-35.txt` verificando que la totalidad de pruebas pasa y no hay regresiones.
- [ ] 8.4 **Mutaciones y Trazabilidad**:
  - Crear `docs/evidencias/mutaciones-C-35.py` con una mutación por cada test nuevo implementado.
  - Ejecutar `python docs/evidencias/mutaciones-C-35.py` asegurando 0 mutaciones inválidas y restauración íntegra del código. Volcar a `docs/evidencias/mutaciones-C-35.txt`.
  - Crear `docs/evidencias/trazabilidad-C-35.py` y generar la matriz escenario → test → mutación en `docs/evidencias/verify-C-35.md`.
- [ ] 8.5 **Comprobación estricta de calidad y OpenSpec**:
  - Ejecutar `npm run typecheck` (debe terminar con exit code 0).
  - Ejecutar `npm run lint` (debe terminar con exit code 0).
  - Ejecutar `npm run build` (debe terminar con exit code 0).
  - Ejecutar `cmd /c openspec validate ui-portada-y-acceso --strict` y `cmd /c openspec validate --all --strict` (ambos deben terminar con exit code 0). Volcar a `docs/evidencias/openspec-C-35.txt`.

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

## Workflow Follow-up

- No archivar C-35 (`/opsx:archive ui-portada-y-acceso`) hasta que todas las tareas y capturas de la fase 9 estén completas y aprobadas por la autora.
- No commitear ni hacer `git push` sin instrucción explícita de la usuaria.
