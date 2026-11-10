# Tasks

## 1. Línea base y preparación

- [x] 1.1 Confirmar que la rama es `c35-apply` y que el único untracked esperado es `.codex/`; no tocar `.env`, `.codex/`, `AGENTS.md` ni `CLAUDE.md`.
- [x] 1.2 Ejecutar la suite completa desde `frontend/` con `npm run test:run` y guardar la salida en `docs/evidencias/baseline-C-35.txt`. Anotar el total de tests y confirmar que no hay fallos preexistentes. Si aparece uno, registrarlo y no modificarlo; si afecta un archivo que C-35 toca, frenar y reportar.
- [x] 1.3 Confirmar que existen `frontend/src/assets/brand/logo-aqua-claro.png` y las cinco fotos `hero-*.webp`; no instalar dependencias nuevas.
- [x] 1.4 Releer `docs/evidencias/explore-portada-y-acceso.md`, `openspec/changes/ui-portada-y-acceso/design.md` y los specs del change antes de escribir código.
- [x] 1.5 Registrar el estado inicial de los tests que no se pueden modificar: `LoginPage.test.tsx`, `LoginBrand.test.tsx`, `LoginCarousel.test.tsx`, `App.test.tsx` y `smoke.test.tsx`.

## 2. Tokens de layout (`frontend-foundation`)

- [x] 2.1 **RED** — Crear `frontend/src/shared/styles/landingTokens.test.ts` con un test que lea `tokens.css` y exija `--landing-hero-min-height: 60vh` y `--landing-content-max-width` con valor de longitud. Ejecutar `npx vitest run src/shared/styles/landingTokens.test.ts -t "tokens de layout"` desde `frontend/`; guardar la salida en `docs/evidencias/red-C-35/tokens-layout.txt` y confirmar que falla por el token ausente.
- [x] 2.2 **GREEN** — Agregar los dos tokens a `frontend/src/shared/styles/tokens.css`. Ejecutar el test y guardar la salida en `docs/evidencias/green-C-35/tokens-layout.txt`; debe pasar.
- [x] 2.3 **RED** — Agregar al mismo archivo un test que verifique que los CSS modules de `frontend/src/features/landing/` usan `var(--landing-hero-min-height)` y `var(--landing-content-max-width)`. Guardar la salida RED en `docs/evidencias/red-C-35/tokens-uso.txt`.
- [x] 2.4 **GREEN** — Usar los tokens en `LandingPage.module.css` (se crea en la tarea 4). Guardar la salida GREEN en `docs/evidencias/green-C-35/tokens-uso.txt`.
- [x] 2.5 **RED** — Agregar un test que compare las custom properties de color de `tokens.css` antes y después de C-35 y exija cero colores nuevos. Guardar la salida RED en `docs/evidencias/red-C-35/tokens-colores.txt`.
- [x] 2.6 **GREEN** — Confirmar que no se agregó ningún color; el test pasa. Guardar la salida en `docs/evidencias/green-C-35/tokens-colores.txt`.

## 3. Contenido ficticio (`landingContent.ts`)

- [x] 3.1 **RED** — Crear `frontend/src/features/landing/landingContent.test.ts` con un test que exija los tres profesionales del seed y sus horarios (Sosa solo mañana). Ejecutar y guardar la salida RED en `docs/evidencias/red-C-35/contenido-equipo.txt`.
- [x] 3.2 **GREEN** — Crear `frontend/src/features/landing/landingContent.ts` con los datos tipados y hacer pasar el test. Guardar la salida GREEN.
- [x] 3.3 **RED** — Agregar un test de los cinco servicios con sus duraciones (45, 60, 60, 30, 90). Guardar la salida RED en `docs/evidencias/red-C-35/contenido-servicios.txt`.
- [x] 3.4 **GREEN** — Completar los servicios en `landingContent.ts`; guardar la salida GREEN.
- [x] 3.5 **RED** — Agregar un test de horarios (lunes a viernes 9:00-13:00 y 15:00-19:00), contacto ficticio (dirección “Av. Ejemplo 1234, Ciudad Demo”, teléfono “(0261) 555-0101”, correo “turnos@aqua-demo.example”) y nota de datos ficticios. Guardar la salida RED en `docs/evidencias/red-C-35/contenido-contacto.txt`.
- [x] 3.6 **GREEN** — Completar los datos de horarios y contacto; guardar la salida GREEN.

## 4. Portada, hero y secciones (`LandingPage`)

- [x] 4.1 **RED** — Crear `frontend/src/features/landing/LandingPage.test.tsx` con un test que renderice `LandingPage` y exija el `h1` cuyo nombre accesible es “Aqua — Clínica Odontológica” (logo dentro del `h1`), la bajada exacta “Claridad en cada cuidado.”, el lead del explore y el CTA “Ingresar al sistema”. Guardar la salida RED en `docs/evidencias/red-C-35/hero-marca.txt`.
- [x] 4.2 **GREEN** — Crear `LandingPage.tsx` y `LandingPage.module.css` con el hero; usar `var(--landing-hero-min-height)` y `var(--landing-content-max-width)`. Guardar la salida GREEN.
- [x] 4.3 **RED** — Agregar un test del badge “Sitio de demostración” y de la nota visible de datos ficticios en “Horarios y contacto”. Guardar la salida RED en `docs/evidencias/red-C-35/demo-marcas.txt`.
- [x] 4.4 **GREEN** — Agregar el badge y la nota; guardar la salida GREEN.
- [x] 4.5 **RED** — Agregar un test de las cuatro secciones con sus `h2` (“Quiénes somos”, “Servicios”, “Equipo”, “Horarios y contacto”) y de que están visibles sin `IntersectionObserver`. Guardar la salida RED en `docs/evidencias/red-C-35/secciones.txt`.
- [x] 4.6 **GREEN** — Implementar las cuatro secciones; guardar la salida GREEN.
- [x] 4.7 **RED** — Agregar un test de que el carrusel de C-34 se reutiliza (cinco imágenes decorativas y botón “Pausar animación”). Guardar la salida RED en `docs/evidencias/red-C-35/carrusel.txt`.
- [x] 4.8 **GREEN** — Montar `LoginCarousel` en el hero con `carouselTicker` y `prefersReducedMotion`; guardar la salida GREEN.

## 5. Primitiva `Dialog` compartida (`frontend-foundation`)

- [x] 5.1 **RED** — Crear `frontend/src/shared/components/Dialog.test.tsx` con un test de que `Dialog` abre en jsdom sin `showModal`, deja el atributo `open`, aplica `role="dialog"`, `aria-modal="true"`, `aria-labelledby={labelledBy}` y renderiza `children`. Guardar la salida RED en `docs/evidencias/red-C-35/dialog-primitiva-abre.txt`.
- [x] 5.2 **GREEN** — Crear `frontend/src/shared/components/Dialog.tsx` y `Dialog.module.css` sin estilos de la portada; implementar props, atributos y fallback por atributo `open`. Guardar la salida GREEN.
- [x] 5.3 **RED** — Agregar un test de que Escape llama a `onClose` y devuelve el foco a `returnFocusRef`. Guardar la salida RED en `docs/evidencias/red-C-35/dialog-primitiva-escape.txt`.
- [x] 5.4 **GREEN** — Implementar `onKeyDown` de Escape y el retorno de foco; guardar la salida GREEN.
- [x] 5.5 **RED** — Agregar un test de que el evento `cancel` llama a `onClose` y de que cerrar usa `close()` cuando existe o `removeAttribute("open")` cuando no, sin stubs. Guardar la salida RED en `docs/evidencias/red-C-35/dialog-primitiva-cancel.txt`.
- [x] 5.6 **GREEN** — Implementar `onCancel` y el cierre por capacidad; guardar la salida GREEN.
- [x] 5.7 Agregar a `docs/evidencias/mutaciones-C-35.py` una mutación por cada test de `Dialog` (fallback `open`, Escape/retorno de foco, cancel/cierre, `labelledBy`/`children`) y verificar que todas fallan su test, con 0 inválidas y SHA-256 restaurado.

## 6. Diálogo de acceso (`LoginDialog` compone `Dialog`)

- [x] 6.1 **RED** — Crear `frontend/src/features/landing/LoginDialog.test.tsx` con un test de que el diálogo abre al entrar, expone `role="dialog"`, el heading “Turnos Odontología”, el form “Iniciar sesión” y el botón “Ver la clínica”. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-abre.txt`.
- [x] 6.2 **GREEN** — Crear `LoginDialog.tsx` y `LoginDialog.module.css`; componer `Dialog` con `labelledBy="login-heading"` y `returnFocusRef`, montar `LoginForm` y el botón “Ver la clínica”. No reimplementar apertura/cierre, Escape, `cancel` ni retorno de foco. Guardar la salida GREEN.
- [x] 6.3 **RED** — Agregar un test de que “Ver la clínica” cierra el diálogo. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-cierra.txt`.
- [x] 6.4 **GREEN** — Implementar el cierre a través de `onClose` de `Dialog`; guardar la salida GREEN.
- [x] 6.5 **RED** — Agregar un test de que `SESSION_EXPIRED_MESSAGE` (importado desde `features/auth/AuthContext.tsx`) se muestra dentro del formulario como `role="alert"`, sin copiar el texto. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-vencida.txt`.
- [x] 6.6 **GREEN** — Pasar `initialNotice` desde `LoginPage`/`LandingPage` a `LoginDialog`/`LoginForm`; guardar la salida GREEN.
- [x] 6.7 **RED** — Agregar un test de nombres únicos: con el diálogo abierto, un solo botón “Ingresar” y un botón “Ingresar al sistema” sin `aria-hidden` ni `tabIndex={-1}`. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-nombres.txt`.
- [x] 6.8 **GREEN** — Ajustar el CTA y el submit; guardar la salida GREEN.
- [x] 6.9 **RED** — Agregar un test de foco inicial en “Usuario” al abrir el diálogo. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-foco.txt`.
- [x] 6.10 **GREEN** — En `LoginDialog`, enfocar `document.getElementById("login-username")` en un `useLayoutEffect` sobre `open`; guardar la salida GREEN.
- [x] 6.11 **RED** — Agregar un test de que el `overflow` del body queda en `hidden` con el diálogo abierto y se restaura al cerrar. Guardar la salida RED en `docs/evidencias/red-C-35/dialogo-scroll.txt`.
- [x] 6.12 **GREEN** — Implementar el bloqueo y el cleanup en `LoginDialog` (no en `Dialog`); guardar la salida GREEN.
- [x] 6.13 Verificar que `LoginDialog` no duplica la lógica genérica: los escenarios de fallback, Escape y `cancel` están cubiertos por `Dialog.test.tsx`, y `LoginDialog.test.tsx` solo prueba lo específico de la portada.

## 7. Reveal accesible

- [x] 7.1 **RED** — Crear `frontend/src/features/landing/RevealSection.test.tsx` con un test de que sin `IntersectionObserver` la sección no queda pendiente y su contenido es visible. Guardar la salida RED en `docs/evidencias/red-C-35/reveal-sin-observador.txt`.
- [x] 7.2 **GREEN** — Crear `RevealSection.tsx` y `RevealSection.module.css`; guardar la salida GREEN.
- [x] 7.3 **RED** — Agregar un test con observador inyectado: estado `pending` al montar, `revealed` al disparar el callback y cleanup al desmontar. Guardar la salida RED en `docs/evidencias/red-C-35/reveal-observador.txt`.
- [x] 7.4 **GREEN** — Crear `revealObserver.ts` e implementar la suscripción/cleanup; guardar la salida GREEN.
- [x] 7.5 **RED** — Agregar un test de reduced motion (sin estado pendiente) y de que el contenido sigue en el DOM durante la animación. Guardar la salida RED en `docs/evidencias/red-C-35/reveal-reduced.txt`.
- [x] 7.6 **GREEN** — Implementar la detección de reduced motion y el estado inicial revelado; guardar la salida GREEN.
- [x] 7.7 **GREEN** — Envolver las cuatro secciones con `RevealSection` y ajustar el CSS; correr todos los tests de la feature.

## 8. Wrapper `LoginPage` y regresión

- [x] 8.1 **RED** — Agregar a `LandingPage.test.tsx` un test de que `LoginPage` renderiza la portada y calcula el aviso de sesión vencida. Guardar la salida RED en `docs/evidencias/red-C-35/loginpage-wrapper.txt`.
- [x] 8.2 **GREEN** — Convertir `LoginPage.tsx` en wrapper delgado de `LandingPage`, conservando `LoginPageProps` y el cálculo `lastEvent`/`location.state`; guardar la salida GREEN.
- [x] 8.3 Ejecutar sin modificar: `npx vitest run src/features/login/LoginPage.test.tsx src/features/login/LoginBrand.test.tsx src/features/login/LoginCarousel.test.tsx src/App.test.tsx src/test/smoke.test.tsx` desde `frontend/`; los cinco archivos deben quedar en verde.
- [x] 8.4 Verificar con `git diff --stat` que los cinco archivos de test existentes no tienen cambios; el diff debe estar vacío. Si un escenario obliga a modificarlos, frenar y reportar en vez de editar el test.
- [x] 8.5 Ejecutar la suite completa `npm run test:run` y guardar `docs/evidencias/suite-C-35.txt`; comparar con `baseline-C-35.txt` y confirmar que no hay regresiones.

## 9. Evidencias, mutaciones y trazabilidad

- [x] 9.1 Revisar que cada test nuevo tiene su salida RED y GREEN guardada en `docs/evidencias/red-C-35/` y `docs/evidencias/green-C-35/`; completar las que falten.
- [x] 9.2 Crear `docs/evidencias/mutaciones-C-35.py` tomando como base `mutaciones-C-34.py`: una mutación por cada test nuevo de la tabla de trazabilidad, incluidas las de la primitiva `Dialog`, aplicada una sola vez, restaurada en `finally`, preservando LF/CRLF. El detector de inválidas debe marcar inválida una mutación si el archivo de test no carga, si el test exacto no se ejecuta, si el error no es de aserción o si el primer frame fuera de `node_modules` no es `*.test.ts(x)`.
- [x] 9.3 Ejecutar `python docs/evidencias/mutaciones-C-35.py` desde la raíz; generar `docs/evidencias/mutaciones-C-35.txt` y regenerar la tabla de `verify-C-35.md` entre `<!-- mutaciones:inicio -->` y `<!-- mutaciones:fin -->`. El script debe salir 0 solo si todas las mutaciones hacen fallar su test, hay 0 inválidas y el SHA-256 del código de producción queda igual (`SHA-256 sin cambios: si`). El `RESUMEN` final debe mostrar 0 inválidas.
- [x] 9.4 Crear `docs/evidencias/trazabilidad-C-35.py` y usarlo para completar la tabla escenario → test → mutación en `verify-C-35.md`; los escenarios marcados “verificación visual (captura)” van sin mutación y con la captura pendiente a cargo de Claude.
- [x] 9.5 Crear `docs/evidencias/verify-C-35.md` con el encabezado, el estado, la tabla de mutaciones y una sección **“Desvíos”** que registre D4, D5 y “Ver la clínica” respecto del explore. Verificar que todos los archivos de evidencia estén en UTF-8 y que no contengan datos reales de pacientes.
- [x] 9.6 Ejecutar `cmd /c openspec validate --all --strict` y guardar la salida en `docs/evidencias/openspec-C-35.txt`; deben validar 15 elementos (14 specs + este change) con 0 fallos.

## 10. Calidad

- [x] 10.1 Ejecutar `npm run typecheck` desde `frontend/`; registrar el comando y el código de salida en `verify-C-35.md`. Debe salir 0.
- [x] 10.2 Ejecutar `npm run lint` desde `frontend/`; registrar el comando y el código de salida en `verify-C-35.md`. Debe salir 0.
- [x] 10.3 Ejecutar `npm run build` desde `frontend/`; registrar el comando y el código de salida en `verify-C-35.md`. Debe salir 0.
- [x] 10.4 Confirmar que no se agregaron dependencias ni se tocaron `App.tsx`, `AuthContext`, `tokenStore`, el cliente de API, el backend, Docker o `.env`.

## 11. Verificación visual independiente (no la ejecuta apply)

- [ ] 11.1 **Capturas 1440, 768 y 390 px — A CARGO DE CLAUDE (verificación independiente).** NO ejecutar en apply; se completa después, con el build levantado, para revisar hero de 60vh, carrusel sin recortes, overlay legible, backdrop y tarjeta vidrio, focus trap nativo, scroll bloqueado, reveal suave, reduced motion, jerarquía de las cuatro secciones, marcas de demo y cero overflow horizontal. Sin capturas aprobadas no se archiva C-35.

## Workflow Follow-up

- Archivar C-35 (`/opsx:archive ui-portada-y-acceso`) solo después de las capturas de 11.1 y de la aprobación de la autora; no commitear ni pushear sin pedido explícito.
- Si aparece un choque con un test existente, frenar y reportar antes de modificar cualquier test.
