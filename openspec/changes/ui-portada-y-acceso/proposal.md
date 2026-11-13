# Proposal

## Why

El change C-34 aplicó la identidad visual inicial y el carrusel de fotografías, pero `/login` seguía siendo un formulario aislado sin presentar la clínica ni contextualizar el servicio antes de solicitar credenciales. Una primera versión exploratoria en la rama `c35-apply` (commit `cea858b`) intentó montar la portada en `/login` abriendo el formulario dentro de un diálogo modal propio. Dicha versión quedó **descartada**: partió de `main` antes de que se integraran y archivaran los changes C-29 (`ui-formulario-nuevo-turno`) y C-30 (`ui-acciones-turno-y-estados`), introdujo un `Dialog` redundante y forzó un flujo modal complejo en el acceso.

Con C-29 y C-30 ya archivados en `main`, la primitiva `Dialog` ya existe canónicamente en `frontend/src/shared/components/Dialog.tsx`. Este rediseño completo de C-35 adopta una **estética oscura editorial** refinada (con nivel de cuidado de referencia estilo Luti, sin copiar), distribuye la experiencia en rutas limpias (`/` para la portada pública a pantalla completa, `/acceso` para la selección visual del rol y `/login` para el formulario translúcido), unifica los modales de la agenda bajo una superficie clara suave marfil-hielo (Decisión A) y estrena una barra de navegación en `AppShell` sin cajas contenedoras.

## Reutilización desde c35-apply

La rama `c35-apply` (`cea858b`) **no se rebasa**. El nuevo apply se ejecutará en la rama `c35-apply2` nacida de `main` y reutilizará, leyéndolos exclusivamente con `git show cea858b:<ruta>` desde Git Bash (sin checkout de ramas descartadas y nunca con el `>` de PowerShell, que guarda en UTF-16), los siguientes componentes y utilidades probadas:

1. `frontend/src/features/landing/RevealSection.tsx` (+ `RevealSection.module.css` + `RevealSection.test.tsx`): contenedor con observador inyectable y detección de reduced motion, actualizando su transición CSS a `translateX` (200-250 ms).
2. `frontend/src/features/landing/revealObserver.ts`: contratos de observación por intersección y detección de accesibilidad.
3. `frontend/src/features/landing/landingContent.ts` (+ `landingContent.test.ts`): contenidos tipados de las cuatro secciones editoriales, horarios de atención, servicios del consultorio y teléfono ficticio `(0261) 555-0101`.
4. `frontend/src/features/login/carouselTicker.ts`: temporizador desacoplado de timers globales para el avance del carrusel.
5. `frontend/src/shared/styles/landingTokens.test.ts`: suite de verificación estática de tokens de layout y preservación de paleta.
6. Tokens de layout incorporados a `frontend/src/shared/styles/tokens.css`: `--landing-hero-min-height: 60vh;` y `--landing-content-max-width: 1120px;`.

**Archivos descartados de `c35-apply`**:
- `frontend/src/features/landing/LoginDialog.tsx` (+ `.module.css` y `.test.tsx`): descartado por completo; el login ya no es un diálogo modal.
- `frontend/src/shared/components/Dialog.tsx` de esa rama: descartado; se preserva la primitiva canónica de C-29 ya presente en `main`.

## What Changes

- **Portada pública a pantalla completa en `/`**: para usuarios anónimos, la ruta raíz despliega la portada completa con el carrusel de fotografías bajo un overlay navy oscuro. Incluye navegación superior de texto sin cajas (`Inicio`, `La clínica`, `Acceder`, con línea fina inferior y `aria-current="page"` en el activo), `<h1>` con logo claro informativo (`alt="Aqua — Clínica Odontológica"`), eslogan grande "Claridad en cada cuidado.", lead breve, CTA único "Explorar la clínica →" (único botón primario de la vista), badge "Sitio de demostración", línea fina en color accent, franja de "Estado actual" (demostración) y teléfono ficticio `(0261) 555-0101`. Con sesión iniciada, `/` conserva su comportamiento actual de `RootRedirect` hacia `/agenda?date=<hoy>`.
- **Secciones editoriales con reveal lateral**: "01 / Quiénes somos", "02 / Servicios", "03 / Equipo" y "04 / Horarios y contacto" diagramadas en dos columnas editoriales, que entran desde el lateral al hacer scroll mediante `RevealSection` (`translateX` + opacidad, 200-250 ms, sin animación ante `prefers-reduced-motion`).
- **Página de selección de rol en `/acceso`**: vista limpia con el encabezado "¿Cómo querés ingresar?", tres tarjetas-enlace oscuras con borde de 1 px que se aclara en hover y focus ("Recepción", "Odontología", "Administración" con destino a `/login?rol=recepcion|odontologo|administrador`), el texto explicativo "El rol se confirma al ingresar" (el rol en la URL es meramente presentacional; la autorización real la decide el backend en el JWT) y enlace "← Volver a Aqua" sin caja.
- **Página de login translúcida en `/login`**: página limpia con enlace "← Volver", etiqueta visual de rol si viene el query param `?rol` (sin etiqueta si no viene o si es inválido), logo claro, bajada "Claridad en cada cuidado." y heading accesible "Turnos Odontología". La tarjeta del formulario se posa sobre el carrusel difuminado con superficie navy translúcida (`backdrop-filter: blur(12px)` con fallback sólido si no hay soporte), borde de 1 px ice/accent a baja opacidad, texto claro con contraste AA garantizado, campos oscuros con línea fina que se aclara en focus, etiquetas en mayúsculas con letter-spacing, entrada animada con fade + desplazamiento corto (200-250 ms, desactivada con reduced motion) y botón "Ingresar" con flecha indicadora en hover. Funciona con o sin `?rol`, conserva redirecciones internas seguras y despliega el mensaje literal de sesión vencida `SESSION_EXPIRED_MESSAGE` ("La sesión venció. Iniciá sesión de nuevo.").
- **Modales de la agenda claros suaves (Decisión A)**: `Dialog`, `AppointmentFormDialog`, `AppointmentDetailDialog` y `AppointmentRescheduleDialog` adoptan una superficie clara suave marfil-hielo apenas translúcida (`rgba(243, 247, 250, 0.95)`), `::backdrop` con desenfoque leve (`backdrop-filter: blur(4px)`), borde fino de 1 px, sombra suave, títulos Jost y etiquetas editoriales, sin alterar markup ni comportamiento que usen los tests existentes.
- **Barra de la aplicación (`AppShell`) sin cajas**: navegación con enlaces de texto plano, línea fina inferior en el ítem activo (`aria-current="page"`), "Próximamente" renderizado como texto secundario plano (sin pastilla ni borde) y bloque de sesión en la misma línea a 1440 px. Preserva los `<button disabled data-menu-item="...">` para no alterar los tests existentes de `AppShell.test.tsx`.
- **Rutas y tests existentes**: las rutas nuevas se añaden al final de `createAppRoutes` preservando `routes[0]=/login` y `routes[1]=/` (clave para `App.test.tsx:186-192`). El único test existente modificado es `frontend/src/test/smoke.test.tsx`, que ahora valida el heading accesible "Aqua — Clínica Odontológica" en `/` debido a la incorporación de la portada pública en la raíz.

## Capabilities

### New Capabilities

- `frontend-landing`: portada pública editorial en `/`, secciones con reveal lateral `translateX`, página intermedia `/acceso` con tres roles y navegación de texto sin cajas.

### Modified Capabilities

- `frontend-auth-session`: actualización del requisito `Login` para describir la página `/login` translúcida con `backdrop-filter: blur`, fallback sólido, soporte de etiqueta presentacional `?rol`, botón "Ingresar" con flecha en hover, contraste AA, redirecciones con `from` y despliegue del mensaje literal `SESSION_EXPIRED_MESSAGE`.
- `frontend-foundation`: tokens de layout (`--landing-hero-min-height`, `--landing-content-max-width`), tokens y estilos de superficies (navy oscura translúcida para login/portada y marfil-hielo suave para modales de la agenda), y navegación de `AppShell` sin cajas. Se elimina el requisito de "Diálogo modal reutilizable", ya que la primitiva `Dialog` fue provista canónicamente por C-29.

## Impact

- **Archivos nuevos**:
  - `frontend/src/features/landing/LandingPage.tsx` (+ `.module.css` y `LandingPage.test.tsx`)
  - `frontend/src/features/landing/AccesoPage.tsx` (+ `.module.css` y `AccesoPage.test.tsx`)
  - `frontend/src/features/landing/RevealSection.tsx` (+ `.module.css` y `RevealSection.test.tsx`, adaptados desde `c35-apply`)
  - `frontend/src/features/landing/revealObserver.ts` (reutilizado desde `c35-apply`)
  - `frontend/src/features/landing/landingContent.ts` (+ `landingContent.test.ts`, reutilizados desde `c35-apply`)
  - `frontend/src/features/login/carouselTicker.ts` (reutilizado desde `c35-apply`)
  - `frontend/src/shared/styles/landingTokens.test.ts` (reutilizado desde `c35-apply`)
- **Archivos modificados**:
  - `frontend/src/App.tsx`: configuración de `createAppRoutes` para atender `/` con la portada pública cuando no hay sesión, y agregar `/acceso` al final de la lista de rutas.
  - `frontend/src/features/login/LoginPage.tsx` (+ `LoginPage.module.css` y `LoginForm.tsx`): diseño translúcido oscuro editorial, lectura de `?rol`, enlace "← Volver", animación de entrada.
  - `frontend/src/shared/components/AppShell.tsx` (+ `AppShell.module.css`): navegación sin cajas, badge "Próximamente" plano y bloque de sesión en línea en escritorio.
  - `frontend/src/shared/components/Dialog.module.css`, `AppointmentFormDialog.module.css`, `AppointmentDetailDialog.module.css`, `AppointmentRescheduleDialog.module.css`: superficie clara suave marfil-hielo y desenfoque leve en backdrop.
  - `frontend/src/shared/styles/tokens.css`: adición de `--landing-hero-min-height: 60vh;` y `--landing-content-max-width: 1120px;`.
  - `frontend/src/test/smoke.test.tsx`: única prueba existente actualizada para esperar "Aqua — Clínica Odontológica".
- **Sin impacto / no tocados**:
  - Backend, base de datos, migraciones, Docker y `.env`.
  - Lógica de autenticación (`AuthContext.tsx`, `tokenStore.ts`, `RequireAuth.tsx`, `PublicOnlyRoute.tsx`).
  - Primitiva estructural `Dialog.tsx` (solo se ajustan sus estilos en `.module.css`).
