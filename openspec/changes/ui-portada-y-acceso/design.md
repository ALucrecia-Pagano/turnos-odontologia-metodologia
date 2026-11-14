# Design

## Context

El change C-34 estableció la base tipográfica autoalojada (`Jost Variable` y `Manrope Variable`), el logo claro y el carrusel de fotografías. Posteriormente se ejecutaron y archivaron en `main` los changes C-29 (`ui-formulario-nuevo-turno`) y C-30 (`ui-acciones-turno-y-estados`), los cuales crearon y consolidaron la primitiva `<dialog>` nativa en `frontend/src/shared/components/Dialog.tsx`.

Una iteración previa en la rama `c35-apply` (commit `cea858b`) planteó abrir el login en un diálogo modal sobre `/login`. Dicha rama quedó **descartada** por basarse en un estado anterior a C-29/C-30, duplicar la primitiva de diálogo e introducir fricción modal innecesaria. El presente diseño implementa una **arquitectura de rutas limpias** y una **estética oscura editorial** inspirada en el estándar de cuidado de interfaces de referencia (tipo Luti, sin copiar), distribuyendo la experiencia en:

1. `/`: Portada pública a pantalla completa para usuarios anónimos (con carrusel de fondo bajo overlay navy oscuro, navegación superior de texto sin cajas, logo claro, eslogan, CTA primario, badge de demo, franja de estado y cuatro secciones editoriales con reveal lateral). Con sesión autenticada, conserva el comportamiento actual de redirección a `/agenda`.
2. `/acceso`: Página intermedia de selección de rol con tres tarjetas oscuras.
3. `/login`: Formulario translúcido sobre carrusel difuminado con soporte de `?rol`, conservando todas las redirecciones seguras y el aviso literal de sesión vencida.
4. Modales de la agenda (Decisión A): Adopción de una superficie clara suave marfil-hielo en `Dialog`, `AppointmentFormDialog`, `AppointmentDetailDialog` y `AppointmentRescheduleDialog`.
5. Barra de la aplicación (`AppShell`): Navegación sin cajas contenedoras con la etiqueta "Próximamente" en texto secundario plano y bloque de sesión en la misma línea a 1440 px.

---

## Reutilización desde c35-apply

La rama `c35-apply` (`cea858b`) no se rebasa ni se mezcla. El nuevo apply se ejecutará en la rama limpia `c35-apply2` a partir de `main` y reutilizará mediante `git show cea858b:<ruta>` únicamente los siguientes archivos.

**Codificación al recuperar**: los comandos se ejecutan **desde Git Bash** (`git show cea858b:<ruta> > <ruta>`) y **nunca** con la redirección `>` de PowerShell, que guarda en UTF-16. Alternativa en PowerShell: `git show cea858b:<ruta> | Out-File -Encoding utf8 <ruta>`. Antes de seguir, se verifica con `file <ruta>` (o leyendo los primeros bytes) que ningún archivo recuperado tenga BOM ni esté en UTF-16 (tarea 2.6).

| Archivo en `c35-apply` | Destino en `c35-apply2` | Adaptaciones requeridas |
|------------------------|-------------------------|-------------------------|
| `frontend/src/features/landing/RevealSection.tsx` | Mismo destino | Se mantiene la lógica del observador y reduced motion; se ajustan los estilos CSS. |
| `frontend/src/features/landing/RevealSection.module.css` | Mismo destino | Se actualiza la animación de `translateY` (500 ms) a desplazamiento lateral `translateX` (200-250 ms) y opacidad. |
| `frontend/src/features/landing/RevealSection.test.tsx` | Mismo destino | Se mantiene intacto para verificar reveal con observador, sin observador y con reduced motion. |
| `frontend/src/features/landing/revealObserver.ts` | Mismo destino | Reutilizado íntegramente (fábrica de `IntersectionObserver` y detector de `prefers-reduced-motion`). |
| `frontend/src/features/landing/landingContent.ts` | Mismo destino | Reutilizado íntegramente (datos del seed, servicios, equipo, horarios y teléfono `(0261) 555-0101`). |
| `frontend/src/features/landing/landingContent.test.ts` | Mismo destino | Reutilizado íntegramente (validación de datos ficticios del consultorio). |
| `frontend/src/features/login/carouselTicker.ts` | Mismo destino | Reutilizado íntegramente (ticker desacoplado de timers de jsdom). |
| `frontend/src/shared/styles/landingTokens.test.ts` | Mismo destino | Reutilizado para comprobar estáticamente `--landing-hero-min-height` y `--landing-content-max-width`; su lista de colores permitidos se amplía con los tokens de superficie y se le agrega el test del escenario 10 (contraste AA). |
| Tokens en `tokens.css` | `frontend/src/shared/styles/tokens.css` | Incorporación de `--landing-hero-min-height: 60vh;` y `--landing-content-max-width: 1120px;`. |

**Archivos descartados de `c35-apply`**:
- `frontend/src/features/landing/LoginDialog.*`: Descartado; el formulario de login no se renderiza dentro de un modal.
- `frontend/src/shared/components/Dialog.*` de esa rama: Descartado; la primitiva canónica ya fue creada en C-29 y vive en `frontend/src/shared/components/Dialog.tsx`.

---

## Sistema de Diseño y Tokens: Estética Oscura Editorial

### Paleta y Pares de Contraste AA (WCAG 2.1)

El diseño de la portada, `/acceso` y `/login` utiliza una estética oscura editorial basada en la paleta semántica de Aqua, garantizando contraste accesible de al menos 4.5:1 en todo el texto:

| Elemento / Rol | Color de Texto | Color de Fondo | Ratio de Contraste | Nivel WCAG |
|---|---|---|---|---|
| Texto principal (login/hero) | `#FFFFFF` (Blanco) | `#011C40` (Navy oscuro base) | **16.92:1** | AAA (>= 7:1) |
| Acentos e isotipo | `#A7EBF2` (`--color-ice`) | `#011C40` (Navy oscuro base) | **12.73:1** | AAA (>= 7:1) |
| Textos secundarios y bordes claros | `#C9DDE4` (`--color-border`) | `#011C40` (Navy oscuro base) | **12.04:1** | AAA (>= 7:1) |
| Enlaces y acentos activos | `#54ACBF` (`--color-accent`) | `#011C40` (Navy oscuro base) | **6.47:1** | AA (>= 4.5:1) |
| Botón primario ("Ingresar" / CTA) | `#FFFFFF` (`--color-primary-contrast`) | `#26658C` (`--color-primary`) | **6.32:1** | AA (>= 4.5:1) |
| Textos en modales (Decisión A) | `#011C40` (`--color-text`) | `rgba(243, 247, 250, 0.95)` (Marfil-hielo) | **15.70:1** | AAA (>= 7:1) |
| Texto secundario en modales | `#4A5F78` (`--color-text-muted`) | `rgba(243, 247, 250, 0.95)` (Marfil-hielo) | **6.09:1** | AA (>= 4.5:1) |

> **Corrección de cifras (apply C-35)**: los ratios de contraste sobre navy `#011C40` de la primera versión de esta tabla (16.05, 12.35, 9.85 y 6.55) no coincidían con el cálculo WCAG. Los valores de arriba son los calculados y los verifica el test del escenario 10 (`landingTokens.test.ts`). Todas las conclusiones de nivel (AAA o AA) se mantienen.

### Decisión: uso del accent `#54ACBF` según la superficie

- **Sobre superficies oscuras (navy `#011C40`)**, el accent `#54ACBF` se permite como **texto o línea** (enlaces activos, subrayados, bordes en hover/focus), porque alcanza **6,47:1** (AA).
- **Sobre fondo claro** (blanco, `--color-background`, marfil-hielo de los modales), el accent **sigue siendo solo decorativo**, como estableció la identidad de C-34: no se usa para texto ni para indicadores que dependan de su contraste.

### Superficies y Fallbacks

1. **Superficie oscura translúcida (Login y tarjetas)**:
   ```css
   background: rgba(1, 28, 64, 0.82);
   border: 1px solid rgba(167, 235, 242, 0.22);
   backdrop-filter: blur(12px);
   -webkit-backdrop-filter: blur(12px);
   box-shadow: 0 16px 40px rgba(1, 28, 64, 0.45);
   ```
   **Fallback sólido** (para navegadores o contextos sin soporte de `backdrop-filter`):
   ```css
   @supports not (backdrop-filter: blur(1px)) {
     background: #011C40;
     border-color: rgba(167, 235, 242, 0.35);
   }
   ```

2. **Superficie clara suave para modales de la agenda (Decisión A)**:
   Aplicada a `Dialog.module.css`, `AppointmentFormDialog.module.css`, `AppointmentDetailDialog.module.css` y `AppointmentRescheduleDialog.module.css`:
   ```css
   background: rgba(243, 247, 250, 0.96);
   border: 1px solid var(--color-border);
   box-shadow: var(--shadow-md);
   backdrop-filter: blur(4px);
   -webkit-backdrop-filter: blur(4px);
   border-radius: var(--radius-md);
   ```
   El `::backdrop` del `<dialog>` se estiliza con:
   ```css
   background: rgba(1, 28, 64, 0.45);
   backdrop-filter: blur(4px);
   -webkit-backdrop-filter: blur(4px);
   ```

### Overlay del carrusel y botón de pausa (tokens, mismos valores de C-34)

Los seis `rgba(...)` que `LoginPage.module.css` tenía escritos a mano se movieron a `tokens.css` sin cambiar ningún valor: el degradé del overlay usa `--login-overlay-start`, `--login-overlay-mid` y `--login-overlay-end`, y el botón de pausa usa `--carousel-toggle-bg`, `--carousel-toggle-bg-hover` y `--carousel-toggle-border` (valores en la tabla "Tokens nuevos de C-35"). Ningún CSS Module de C-35 conserva HEX ni `rgba`.

### Tokens nuevos de C-35 (`frontend/src/shared/styles/tokens.css`)

Todo color, sombra y medida de la portada, `/acceso`, `/login`, los modales y el `AppShell` sale de estas variables; los CSS Modules no llevan HEX ni `rgba` propios (sin excepciones: el overlay del carrusel y el botón de pausa heredados de C-34 también pasaron a tokens con los mismos valores).

| Token | Valor | Uso |
|---|---|---|
| `--landing-hero-min-height` | `60vh` | Altura mínima del hero de la portada |
| `--landing-content-max-width` | `1120px` | Ancho máximo del contenido de portada y `/acceso` |
| `--landing-reveal-offset` | `20px` | Desplazamiento lateral inicial de `RevealSection` (`translateX`) |
| `--landing-carousel-blur` | `6px` | Desenfoque del carrusel de fondo en `/login` |
| `--blur-surface` | `12px` | `backdrop-filter` de la tarjeta de login |
| `--blur-backdrop` | `4px` | `backdrop-filter` del `::backdrop` y de las superficies de los modales |
| `--font-size-display` | `clamp(32px, 6vw, 56px)` | Eslogan de la portada y título de `/acceso` |
| `--color-navy-deep` | `#011C40` | Navy base (fondos oscuros y fallback sólido de la tarjeta de login) |
| `--surface-navy` | `rgba(1, 28, 64, 0.82)` | Tarjeta de login y tarjetas de `/acceso` |
| `--surface-ivory-ice` | `rgba(243, 247, 250, 0.96)` | Superficie de los cuatro modales de la agenda |
| `--border-on-navy` | `rgba(167, 235, 242, 0.22)` | Borde de 1 px sobre navy |
| `--border-on-navy-strong` | `rgba(167, 235, 242, 0.35)` | Borde del fallback sin `backdrop-filter` |
| `--field-on-navy` | `rgba(1, 28, 64, 0.6)` | Fondo de los campos oscuros del login |
| `--scrim-navy` | `rgba(1, 28, 64, 0.45)` | `::backdrop` de los diálogos |
| `--scrim-navy-strong` | `rgba(1, 28, 64, 0.7)` | `::backdrop` sin soporte de `backdrop-filter` |
| `--overlay-hero` | degradé navy `0.55 → 0.82` | Capa de legibilidad sobre el carrusel de la portada y fondo de `/acceso` |
| `--shadow-on-navy` | `0 16px 40px rgba(1, 28, 64, 0.45)` | Sombra de la tarjeta de login |
| `--login-overlay-start` | `rgba(1, 28, 64, 0.92)` | Primer tramo (0 %) del degradé que oscurece el carrusel de `/login` |
| `--login-overlay-mid` | `rgba(2, 56, 89, 0.78)` | Tramo medio (55 %) del mismo degradé |
| `--login-overlay-end` | `rgba(38, 101, 140, 0.62)` | Último tramo (100 %) del mismo degradé |
| `--carousel-toggle-bg` | `rgba(1, 28, 64, 0.55)` | Fondo del botón "Pausar animación" |
| `--carousel-toggle-bg-hover` | `rgba(1, 28, 64, 0.75)` | Fondo del botón de pausa en `:hover` |
| `--carousel-toggle-border` | `rgba(255, 255, 255, 0.45)` | Borde de 1 px del botón de pausa |

El fallback sólido de los modales reutiliza `--color-background` (`#F3F7FA`) y el del login usa `--color-navy-deep`, ambos opacos.

---

## Decisiones de Arquitectura e Interfaz

### D1 — Portada a pantalla completa en `/` para usuarios anónimos

- **Ubicación y comportamiento**: La portada pública vive en la ruta raíz `/`. Si el usuario no tiene sesión autenticada (`anonymous`), se renderiza la portada completa. Si el usuario ya está autenticado, `/` ejecuta `RootRedirect` redirigiendo inmediatamente con `replace` a `/agenda?date=<hoy>` según el `Clock` inyectado.
- **Hero**: Ocupa la pantalla completa (`100vh`, con mínimo `--landing-hero-min-height: 60vh`). El fondo reproduce el carrusel de fotografías (`LoginCarousel`) atenuado bajo un overlay navy oscuro.
- **Navegación superior**: Ubicada arriba a la derecha con enlaces de texto plano: "Inicio", "La clínica", "Acceder". Sin cajas, sin botones con borde. El enlace de la sección activa lleva una línea inferior de 1 px en `--color-accent` y `aria-current="page"`.
- **Encabezado y marca**: `<h1>` con el logo claro informativo (`alt="Aqua — Clínica Odontológica"`). El nombre accesible del heading proviene del `alt`, evitando redundancia textual. Debajo, eslogan editorial destacado "Claridad en cada cuidado.", lead explicativo breve, badge "Sitio de demostración", línea fina horizontal en color accent y CTA primario "Explorar la clínica →" (único botón primario de la página).
- **Secciones editoriales**: "01 / Quiénes somos", "02 / Servicios", "03 / Equipo" y "04 / Horarios y contacto" diagramadas en dos columnas asimétricas. Entran desde el lateral (`translateX(24px) → translateX(0)` y opacidad `0 → 1` en 200-250 ms) al hacer scroll con `RevealSection`.
- **Franja de estado y contacto**: Indicador visible de sistema de demostración ("Estado actual: demostración funcional") y teléfono ficticio `(0261) 555-0101`.

### D2 — Selección visual de rol en `/acceso`

- **Encabezado**: "¿Cómo querés ingresar?".
- **Tarjetas de rol**: Tres tarjetas-enlace oscuras con borde fino de 1 px:
  1. "Recepción" → `/login?rol=recepcion`
  2. "Odontología" → `/login?rol=odontologo`
  3. "Administración" → `/login?rol=administrador`
  El borde de 1 px se ilumina con `--color-accent` en estado `:hover` y `:focus-visible`.
- **Aclaración**: Texto secundario visible: *"El rol se confirma al ingresar"*. (Se documenta que el parámetro `?rol` es exclusivamente de presentación y no otorga privilegios; el backend autentica y asigna el rol real a través del JWT).
- **Retorno**: Enlace de texto plano "← Volver a Aqua" que navega a `/` sin caja ni fondo.

### D3 — Página de login translúcida en `/login`

- **Estructura visual**: Página limpia centrada sobre el carrusel difuminado de fondo. Enlace "← Volver" (a `/acceso` o `/`), logo claro, bajada visible "Claridad en cada cuidado." y heading accesible `<h1>` o `<h2>` con el nombre exacto "Turnos Odontología".
- **Etiqueta de rol**: Si la URL contiene `?rol=recepcion|odontologo|administrador`, se despliega una pastilla editorial en la cabecera del formulario (ej. "Recepción", "Odontología", "Administración"). Si el parámetro no está presente o contiene un valor desconocido, el formulario se renderiza sin etiqueta de rol sin emitir errores.
- **Campos del formulario**: Entradas de texto ("Usuario" y "Contraseña") con fondo oscuro semi-opaco, texto claro, borde fino de 1 px que transiciona a `--color-accent` en foco (`:focus-visible`), etiquetas en mayúsculas con `letter-spacing: 0.05em` y `font-family: inherit`.
- **Botón "Ingresar"**: Botón primario con flecha indicadora `→` que experimenta un micro-desplazamiento lateral de 4 px en `:hover`.
- **Transición de entrada**: Fade-in con ligero ascenso vertical (200-250 ms, `cubic-bezier(0.16, 1, 0.3, 1)`), desactivado totalmente ante `prefers-reduced-motion`.
- **Manejo de errores y sesión vencida**: Mantiene intacto el manejo de credenciales inválidas (401 de login muestra mensaje genérico en `role="alert"`) y, ante expiración de token en rutas protegidas, despliega fielmente el mensaje literal `SESSION_EXPIRED_MESSAGE`: *"La sesión venció. Iniciá sesión de nuevo."*.

### D4 — Modales de la agenda claros suaves (Decisión A)

- **Unificación visual**: Los diálogos modales de la agenda (`Dialog.tsx` como primitiva, `AppointmentFormDialog`, `AppointmentDetailDialog` y `AppointmentRescheduleDialog`) adoptan una superficie clara suave marfil-hielo apenas translúcida (`rgba(243, 247, 250, 0.96)`), manteniendo tipografía Jost en títulos, etiquetas editoriales en Manrope, borde fino de 1 px y `::backdrop` con desenfoque leve (`backdrop-filter: blur(4px)`).
- **Compatibilidad**: No se altera el árbol DOM, las props ni los identificadores accesibles (`labelledBy`, `open`, botones de acción, etc.) garantizando que todos los tests de C-29 y C-30 continúen pasando sin cambios.

### D5 — Barra de la aplicación (`AppShell`) con navegación sin cajas

- **Navegación**: Enlaces de navegación renderizados como texto plano sin fondos de botón ni cajas rectangulares. El enlace de la página activa ("Agenda") muestra una línea fina inferior de 2 px en color primario/acento y el atributo `aria-current="page"`.
- **Etiqueta "Próximamente"**: Los ítems del menú correspondientes a funcionalidades futuras muestran "Próximamente" como texto secundario atenuado (`color: var(--color-text-muted)`), eliminando el borde y el fondo de pastilla.
- **Bloque de sesión**: En resoluciones de escritorio (1440 px), el nombre de usuario y el botón "Cerrar sesión" se sitúan en la misma línea horizontal que la marca y la navegación principal (`display: flex; align-items: center; justify-content: space-between;`).
- **Análisis de compatibilidad de tests de `AppShell.test.tsx` y `menuFor.test.ts`**:
  Los tests existentes en `frontend/src/shared/components/AppShell.test.tsx` (líneas 67-79) ejecutan:
  ```tsx
  const adminButtons = within(nav).getAllByRole("button");
  expect(adminButtons).toHaveLength(5);
  expect(adminButtons.map((btn) => btn.getAttribute("data-menu-item"))).toEqual([
    "Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes", "Usuarios y roles",
  ]);
  for (const button of adminButtons) {
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("Próximamente");
  }
  ```
  *Resolución técnica sin modificar tests*: Para cumplir la especificación de "navegación sin cajas" sin alterar el contrato de los tests existentes, los ítems deshabilitados se mantienen como elementos `<button type="button" disabled data-menu-item={item.label} className={styles.menuButton}>` en el JSX. En `AppShell.module.css`, se eliminan sus propiedades de caja (`background: transparent; border: none; box-shadow: none; padding: ...; cursor: default;`) y el `.badge` interior se estiliza como texto secundario plano sin borde (`background: none; border: none; color: var(--color-text-muted); font-size: var(--font-size-xs);`). De este modo, la interfaz es 100% fiel al diseño sin cajas y `AppShell.test.tsx` y `menuFor.test.ts` siguen pasando en verde.

### D6 — RevealSection con desplazamiento lateral

- `RevealSection.tsx` recibe `children`, `observer?: RevealObserverFactory` y `reducedMotion?: boolean`.
- En `RevealSection.module.css`, la animación de entrada utiliza `transform: translateX(20px)` y `opacity: 0` para el estado `data-reveal="pending"`, transicionando a `transform: none` y `opacity: 1` en 200-250 ms `ease-out`.
- Ante `@media (prefers-reduced-motion: reduce)` o cuando `reducedMotion === true`, la transición se desactiva (`transition: none; transform: none; opacity: 1;`), renderizando el contenido visible de inmediato.

### D7 — Orden de rutas en `createAppRoutes`

En `frontend/src/App.tsx`:
```tsx
export function createAppRoutes(clock: Clock = systemClock): RouteObject[] {
  return [
    {
      path: "/login",
      element: <PublicOnlyRoute />,
      children: [{ index: true, element: <LoginPage /> }],
    },
    {
      path: "/",
      element: <RootGate />,
      children: [
        {
          element: <AppShell />,
          children: [
            { index: true, element: <RootRedirect clock={clock} /> },
            { path: "agenda", element: <AgendaPage clock={clock} /> },
            { path: "*", element: <NotFoundPage /> },
          ],
        },
      ],
    },
    {
      path: "/acceso",
      element: <AccesoPage />,
    },
  ];
}
```
- `routes[0]` sigue siendo `/login`.
- `routes[1]` sigue teniendo `path: "/"`. El componente `RootGate` evalúa la ruta y el estado de autenticación:
  - Si `location.pathname === "/"` y la sesión es anónima, renderiza `<LandingPage />`; si la sesión se está comprobando (`checking`), `<LoadingState />`.
  - En cualquier otro caso (sesión autenticada en `/`, o cualquier otra ruta como el test de request protegida `App.test.tsx:186-192`, que reemplaza los hijos), `RootGate` actúa como el guardia `RequireAuth` y renderiza su `Outlet`. Así, el `/` autenticado conserva exactamente el árbol anterior (`AppShell` → índice `RootRedirect` con replace a `/agenda?date=<hoy>`), y un anónimo en `/agenda` sigue yendo a `/login` con `state: { from, expired }`.
  - *Nota de apply*: una primera versión hacía que `RootGate` redirigiera él mismo y quitaba el `AppShell` del `/` autenticado; eso rompía la carrera que usa `Logout.test.tsx` (esperar el nombre de usuario en `/` antes de que la agenda pida datos). Se conservó el índice `RootRedirect` bajo `AppShell` para dejar ese test intacto.
- Las rutas nuevas (como `/acceso`) se ubican **al final** (`routes[2]`), preservando con exactitud quirúrgica los índices `routes[0]` y `routes[1]` que consumen los tests de `App.test.tsx`.

### D8 — Desvío documentado: `frontend/src/test/smoke.test.tsx`

El único test existente que se modifica en todo el repositorio es `frontend/src/test/smoke.test.tsx`.
- **Comportamiento anterior**: el test montaba `<App />` en la raíz `/` sin sesión; como `/` redirigía a `/login`, esperaba encontrar el heading "Turnos Odontología".
- **Comportamiento nuevo**: al visitar `/` sin sesión, `<App />` monta la portada pública de la clínica. El heading principal de la portada es el `<h1>` con el logo claro (`alt="Aqua — Clínica Odontológica"`). Por tanto, `smoke.test.tsx` se actualiza para verificar:
  ```tsx
  expect(screen.queryByRole("heading", { name: "Aqua — Clínica Odontológica" })).toBeInTheDocument();
  ```
  Este cambio de requisito queda explícitamente documentado como el único desvío autorizado.

---

## Análisis de Tests Existentes de `LoginPage`

`LoginPage.test.tsx`, `LoginBrand.test.tsx` y `LoginCarousel.test.tsx` se mantienen **100% intactos**. La nueva implementación de `LoginPage` preserva todos sus contratos:
1. `screen.getByRole("heading", { name: "Turnos Odontología" })` sigue existiendo como el heading accesible del formulario.
2. `screen.queryByRole("img", { name: "Aqua — Clínica Odontológica" })` sigue existiendo con la imagen `logo-aqua-claro.png`.
3. `screen.getByText("Claridad en cada cuidado.")` sigue siendo visible.
4. `getByLabelText("Usuario")` y `getByLabelText("Contraseña")` siguen vinculados a sus inputs accesibles.
5. `getByRole("button", { name: "Ingresar" })` sigue siendo el submit único del formulario.
6. `SESSION_EXPIRED_MESSAGE` ("La sesión venció. Iniciá sesión de nuevo.") sigue mostrándose ante `state.expired === true` o `lastEvent === "expired"`.
7. `LoginCarousel` y su botón "Pausar animación" siguen operativos.

---

## Dudas y Aclaraciones Documentadas

1. **Ruta del archivo smoke**: En el enunciado se menciona `frontend/src/app/smoke.test.tsx`, pero en el árbol real del proyecto el archivo se ubica en `frontend/src/test/smoke.test.tsx`. Se cita y trabaja sobre su ruta física real verificada.
2. **Preservación de elementos `<button>` en `AppShell`**: Como `AppShell.test.tsx` realiza una consulta estricta `within(nav).getAllByRole("button")` y valida `btn.getAttribute("data-menu-item")`, la exigencia de "navegación sin cajas" se resuelve 100% mediante CSS (eliminando fondos, bordes y estilos de pastilla en `.menuButton` y `.badge`) sin cambiar las etiquetas HTML a `<span>`, lo que rompería la suite de pruebas.
