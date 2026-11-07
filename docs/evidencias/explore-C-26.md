# Explore C-26 — `ui-login-y-sesion`

Fecha: 2026-11-07
Fase: 6 — Interfaz web (React + TypeScript + Vite), sobre la API probada
Governance: **ALTO** (manejo del token en el cliente, según `CHANGES.md` §[C-26])
Dependencias en `CHANGES.md`: `C-25`, `C-19`.

> Este explore es analítico: **no** ejecutó docker, `npm install`, `npx`, pytest, alembic ni pip; **no** tocó `backend/`, `frontend/`, código, tests, migraciones, specs, `docker-compose.yml`, `.env`, la KB, `AGENTS.md`, `CLAUDE.md` ni creó la carpeta del change. Se leyó C-25 **propuesto pero no implementado** (`openspec/changes/frontend-base-react-vite/`): su `design.md` es el contrato, en especial **D7** (cliente con `fetch` inyectado y costura `setAuthProvider`) y **C1** (prohibición de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global). C-24 está **en curso** en `backend/` por otro agente: no se tomó ese código a medio hacer como fuente de verdad. C-19 está archivado y su spec es la fuente de autenticación.
>
> Comandos read-only ejecutados: `openspec list --json`, `git status --short`, lecturas y búsquedas (`read`, `grep`, `ls`). `frontend/` **no existe todavía**.

---

## 1. Alcance de C-26 según `CHANGES.md` y qué queda afuera

### Qué entra en C-26

1. **Pantalla de login** (usuario y contraseña) contra `POST /api/auth/login`.
2. **Error genérico** ante credenciales inválidas, sin decir cuál campo falló y sin permitir enumerar usuarios.
3. **Envío de `Authorization: Bearer <token>`** en el cliente de API, usando la costura `setAuthProvider({ getToken })` que deja C-25.
4. **Manejo de `401`**: descartar el token, limpiar la sesión y volver al login.
5. **Contexto de sesión** con `GET /api/auth/me` y estado de carga inicial.
6. **Rutas protegidas y redirecciones** login ↔ resto con React Router 6.
7. **Menú y acciones visibles según el rol** del usuario (`GET /api/auth/me`), cruzado con la matriz RBAC de KB 03.
8. **Cierre de sesión** que descarta el token en el cliente.
9. **Tests de componentes**: login correcto guarda sesión y redirige; credenciales inválidas muestran el error; `401` vuelve al login; menú según rol.
10. **Evidencias espejo**: RED, Vitest, `tsc --noEmit`, ESLint, mutaciones, trazabilidad y `verify-C-26.md`.

### Qué queda explícitamente afuera

- **Backend**: C-26 no modifica `backend/`, no agrega endpoints, no cambia el contrato de `/api/auth/login` ni `/api/auth/me`.
- **Refresh tokens, revocación y logout del servidor**: SU-06/DD-11 los excluyen del MVP. Cerrar sesión en el cliente descarta el token, que sigue siendo válido hasta `exp`.
- **Cookies, CSRF y `HttpOnly`**: el backend hoy devuelve `accessToken` en el JSON y no emite cookie; cambiarlo es otro change (extensión de C-19), no C-26.
- **Cambio de contraseña, recuperación, alta de usuarios, ABM de usuarios, MFA, SSO, bloqueo por intentos**: fuera del MVP (SU-06; KB 03 §RBAC).
- **“Recordarme” y persistencia entre reinicios del navegador**: no se piden y chocan con la recomendación de seguridad.
- **Pantallas de negocio** (agenda diaria/semanal, formulario de turno, vista por sillón, horarios/bloqueos, catálogos y pacientes): C-27 a C-33.
- **Reglas de dominio**: C-26 no replica RN-AG/RN-TU; solo muestra los mensajes de `violations` tal cual.
- **Decodificar el JWT para autorizar en el front**: el token es opaco para la UI; el rol sale de `/me` y la API decide.
- **Tests E2E con navegador real**: el scope pide tests de componentes; la prueba manual contra el backend va en `verify-C-26.md`.

### Frontera de archivos

- C-26 implementa **solo** bajo `frontend/` y, cuando se proponga, sus artefactos de change en `openspec/changes/ui-login-y-sesion/` y sus evidencias `docs/evidencias/*-C-26.*`.
- Este explore solo crea `docs/evidencias/explore-C-26.md`. No crea `frontend/` ni la carpeta del change.
- Precondición del apply: **GATE 16** — C-25 implementado, verde y archivado; C-19 archivado. Hoy C-25 está propuesto y `frontend/` no existe.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-26 reutiliza

| Pieza | Dónde | Qué aporta a C-26 |
|-------|-------|-------------------|
| Login | `openspec/specs/authentication-and-rbac/spec.md`; `backend/app/api/auth.py` | `POST /api/auth/login` recibe `username` y `password` y devuelve exactamente `accessToken` + `tokenType: "bearer"`; `Cache-Control: no-store`. |
| Credenciales inválidas | Spec de autenticación | Siempre `401 { "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }`, idéntico para usuario inexistente, contraseña incorrecta y usuario inactivo. |
| Usuario autenticado | Spec de autenticación; `backend/app/auth/model.py` | `GET /api/auth/me` devuelve exactamente `id`, `username`, `displayName`, `role`, `professionalId`. `professionalId` es nulo para recepción y administración. |
| Token | `backend/app/auth/tokens.py` | JWT HS256 con exactamente `sub`, `role` y `exp`; `exp = now + JWT_EXPIRES_MIN`. No contiene nombres ni `professional_id`. |
| Relectura del usuario | Spec de autenticación | En cada request se relee el usuario. Inexistente, inactivo o con rol distinto del token → `401 INVALID_TOKEN`. Sin revocación por token. |
| Errores | `openspec/specs/api-foundation/spec.md`; `openspec/changes/frontend-base-react-vite/design.md` D9 | Cuatro cuerpos: `400 {errors:[...]}`, `401 {code,message}`, `403/409/422 {violations:[...]}`, `404 {code,message}`. C-25 ya modela los cuatro y `getApiErrorMessages`. |
| RBAC | `backend/app/auth/permissions.py`; KB 03 §RBAC | Matriz de 34 combinaciones recurso/acción con tres roles. Sin entrada → `403` con `FORBIDDEN_OPERATION` y mensaje en español. |
| Roles | `backend/app/domain/model.py` | Valores `odontologo`, `recepcion`, `administrador`. |
| Cliente de API | C-25 design D7/D9 | `fetch` inyectado por parámetro, resultado discriminado, cuatro formas de error y costura `setAuthProvider({ getToken })` con provider nulo por defecto. |
| Componentes base | C-25 design D10 | `LoadingState`, `EmptyState`, `ErrorState`, `PageShell`, `StatusBadge`; presentacionales, accesibles, con tokens. |
| Tokens de diseño | C-25 design D6 | CSS custom properties, CSS Modules, system font stack, foco visible, contraste AA. |
| Router | C-25 design D3 | React Router 6 con `createBrowserRouter`, ruta `/` y `*`. C-26 agrega `/login` y los guards. |
| Docker y URL | C-25 design D11/D12; `.env.example` | Servicio `frontend` en 5173; `VITE_API_URL` para el navegador (`http://localhost:8000/api`) y `CORS_ORIGIN` ya existen. No se agregan variables ni secretos. |
| Disciplina de evidencias | `docs/evidencias/mutaciones-C-23.py`, `trazabilidad-C-23.py`, `verify-C-22.md`/`verify-C-23.md` | Formato a espejar en el front: RED antes del código, mutaciones, trazabilidad y verificación. |

### 2.2. Qué le falta a la base para C-26

1. **`frontend/` no existe**: C-25 está propuesto y sin implementar. C-26 no puede empezar a codificar hasta el GATE 16.
2. **Decidir dónde se guarda el token** (esta es la decisión ALTO de este explore).
3. **Módulo de autenticación del front**: storage, API de login y `/me`, contexto, guards, menú por rol.
4. **Pantalla de login** con accesibilidad, error genérico, estado de envío y calidad visual.
5. **Manejo central del `401`** sin refresh y sin bucles.
6. **Compatibilizar el test guardián de C-25** que prohíbe `localStorage`/`sessionStorage` en `frontend/src` con el storage que C-26 necesita.
7. **Tests sin mocks** con `fetch` inyectado, router en memoria y almacenamiento inyectado.
8. **Script de mutaciones y trazabilidad del front** con un detector de mutaciones inválidas equivalente al de `mutaciones-C-23.py`.

### 2.3. Observaciones que condicionan el diseño

- **C-25 no está implementado**: todo lo que C-26 asume del cliente, los componentes y el router sale del `design.md` de C-25, no de código real. El apply de C-26 debe verificar que C-25 haya respetado D7 y C1.
- **C1 prohíbe mocks globales**: el cliente recibe `fetch` por parámetro y los tests le pasan una función real que devuelve `new Response(...)`. C-26 no puede usar `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos ni MSW.
- **La API es la única autoridad**: la UI puede ocultar acciones, pero el rechazo definitivo es del backend (`401`/`403`). Ocultar un botón no es seguridad.
- **El `401` del login no es “sesión vencida”**: el login inválido también responde `401`, con el mismo cuerpo `{code,message}`. El manejador global de `401` debe excluir `POST /api/auth/login`; si no, un login fallido dispararía una redirección y un bucle.
- **No hay refresh ni revocación**: el token vence y la única señal es un `401` en la request siguiente. No hay endpoint de logout ni de refresh. El cliente no debe reintentar `401` automáticamente.
- **`/me` es la fuente del rol**: el token contiene `role`, pero el rol de la UI debe salir de `/api/auth/me`. El token es opaco para el front; decodificarlo para autorizar sería duplicar y desactualizar la fuente.
- **Usuario desactivado o rol cambiado**: el spec dice que el request siguiente a `/me` responde `401`. La UI debe tratar ese `401` igual que el vencimiento: limpiar sesión y volver al login.
- **El login solo devuelve el token**: para conocer `displayName`, `role` y `professionalId` hay que llamar a `/me` inmediatamente después del login. El login no puede dejar la UI “a medias” con un token pero sin usuario.
- **`sessionStorage` es por pestaña**: una pestaña nueva normal no comparte el token; algunas variantes de “duplicar pestaña” pueden copiar `sessionStorage` según el navegador. Es un comportamiento a documentar, no a ocultar.
- **El backend no emite cookie**: la opción `HttpOnly` no está disponible sin cambiar C-19 (login que setee cookie, CORS con credenciales, CSRF). Fuera del alcance de C-26.
- **CORS ya está**: `CORS_ORIGIN` apunta a `http://localhost:5173`; el navegador llama a `http://localhost:8000/api`. No hace falta tocar `backend/`.
- **El token es de vida corta pero no infinita**: `JWT_EXPIRES_MIN` es configurable y positivo. C-26 no debe asumir un valor; no decodifica `exp` ni programa un temporizador.
- **Evidencias**: el proyecto exige RED antes del código, mutaciones y trazabilidad. C-26 debe mantener la paridad con C-20..C-25.

---

## 3. Decisiones de diseño (`D1`–`D14`)

### D1 — Dónde se guarda el token (decisión ALTO)

**Problema**: el backend entrega un JWT en el cuerpo del login y no emite cookie. Hay que decidir dónde vive ese token en el navegador, con qué riesgo de XSS, qué pasa al recargar y qué pasa al abrir otra pestaña. Esta decisión condiciona todo C-26 y no puede quedar implícita.

| Criterio | Solo memoria | `sessionStorage` | `localStorage` | Cookie `HttpOnly` |
|----------|--------------|------------------|----------------|-------------------|
| Sobrevive recarga | No | **Sí** | Sí | Sí |
| Sobrevive cierre del navegador | No | No | Sí | Según cookie |
| Se comparte entre pestañas | No | No (salvo duplicar) | Sí | Sí |
| Legible por JavaScript | Sí (mientras vive) | Sí | Sí | **No** |
| Requiere cambio de backend | No | No | No | **Sí** |
| Riesgo ante XSS | Medio (ventana corta) | Medio-alto (persiste en la pestaña) | Alto (persiste al reiniciar) | Bajo (no legible por JS) |
| Complejidad en C-26 | Baja | Baja | Baja | Alta (CORS credenciales + CSRF) |

- **Opción A — solo en memoria (módulo cerrado)**: el token vive en una variable del módulo de auth y desaparece al recargar.
  - *Pros*: la exposición por XSS dura solo mientras la página está abierta; no queda nada escrito en disco; logout trivial; cada pestaña es independiente.
  - *Contras*: recargar la página o abrir otra pestaña obliga a loguearse de nuevo; para una recepcionista que recarga o duplica la agenda es una fricción diaria; el video muestra un login tras cada refresh.
- **Opción B — `sessionStorage` (recomendada)**: el token se guarda bajo una clave propia (`turnos.auth.accessToken`) en el almacenamiento de la pestaña, con un espejo en memoria para acceso rápido.
  - *Pros*: sobrevive a la recarga (lo que más se hace en una agenda); se limpia al cerrar la pestaña o el navegador; no se comparte entre pestañas normales; no requiere backend; es simple y testeable con el `sessionStorage` real de jsdom; el riesgo queda acotado a la pestaña y a la vida corta del token.
  - *Contras*: cualquier script del mismo origen puede leerlo (XSS); una pestaña nueva pide login; “duplicar pestaña” puede copiarlo en algunos navegadores; no sirve para “recordarme” entre reinicios, que no se pide.
- **Opción C — `localStorage`**: el token persiste entre pestañas y reinicios.
  - *Pros*: una sola sesión para todas las pestañas; sobrevive al cierre del navegador.
  - *Contras*: es la peor exposición ante XSS (token robado y persistente); en una máquina compartida de consultorio deja la sesión abierta; no hay “recordarme” en el MVP; no se recomienda.
- **Opción D — cookie `HttpOnly`**: el backend setea el token en una cookie no legible por JavaScript.
  - *Pros*: inmune a lectura por XSS; `SameSite` mitiga CSRF; es la opción más robusta en producción.
  - *Contras*: **hoy el backend no emite cookie**; habría que cambiar el login, CORS con credenciales y agregar CSRF, lo que toca C-19 y excede C-26; el contrato actual devuelve `accessToken` en el cuerpo; una cookie puesta por JavaScript no es `HttpOnly` y no aporta sobre `sessionStorage`.
- **Recomendación**: **B, `sessionStorage` detrás de una interfaz `TokenStore`**. Es el mejor equilibrio para un MVP local de consultorio: sobrevive la recarga, no deja la sesión abierta tras cerrar el navegador y no requiere tocar el backend. Se implementa con un adaptador (`createSessionTokenStore`) y un espejo en memoria; si `sessionStorage` lanza una excepción (modo privado, cuota), el adaptador cae a memoria para esa pestaña y lo informa en `verify-C-26.md`. Se documenta el riesgo de XSS y se mitiga con: dependencias mínimas, sin `dangerouslySetInnerHTML`, sin scripts de terceros, CSP `script-src 'self'` como mejora futura y token de vida corta. Si la autora prioriza seguridad extrema sobre recarga, la opción A es el fallback y es un cambio de una línea en el adaptador.

### D2 — Qué pasa cuando el token vence a mitad de uso (no hay refresh)

**Problema**: el backend no tiene refresh. Cuando el token vence, la request protegida responde `401 INVALID_TOKEN`. Hay que decidir quién detecta ese `401`, qué se descarta, si se conserva la ruta a la que el usuario iba y cómo se evita un bucle con el `401` del login.

- **Opción A (recomendada)**: **manejo central en la capa de auth**, una sola vez:
  1. El cliente de API, ante un `401` de una request **protegida** (no el login), notifica a la capa de auth.
  2. La capa de auth descarta el token del `TokenStore`, limpia el usuario en memoria y marca la sesión como `anonymous` con motivo `expired`.
  3. El guard de ruta (`RequireAuth`) detecta `anonymous` y navega a `/login` con `state: { from, expired }`, usando `replace` para no dejar la página protegida en el historial.
  4. El login muestra “La sesión venció. Iniciá sesión de nuevo.” y, tras un login correcto, vuelve a `from` si es una ruta interna válida; si no, a `/`.
  5. **No se reintenta** la request automáticamente. El usuario decide.
  - *Pros*: comportamiento uniforme en todas las pantallas; una sola puerta; no hay parches por feature; la ruta se conserva; el mensaje explica por qué volvió al login.
  - *Contras*: una request en segundo plano puede sacar al usuario de un formulario a medio completar; se mitiga en C-29+ con borradores, pero en C-26 no hay formularios de negocio.
- **Opción B — manejo por pantalla**: cada componente detecta el `401` y decide.
  - *Pros*: control local; una pantalla podría mostrar un modal en lugar de redirigir.
  - *Contras*: se duplica la lógica, alguna pantalla se olvida, el comportamiento es inconsistente y el `401` del login se confunde con el de sesión; no se recomienda.
- **Opción C — decodificar `exp` y hacer logout proactivo**: el front lee el `exp` del JWT y cierra sesión antes de la request.
  - *Pros*: evita algunas requests condenadas.
  - *Contras*: el token deja de ser opaco; el reloj del cliente puede estar desfasado; no cubre usuario desactivado ni cambio de rol (que también dan `401`); agrega complejidad sin cubrir el caso real. Descartada.
- **Recomendación**: **A**. El `401` es la única señal confiable. El login inválido se excluye explícitamente del manejador global. La ruta se conserva en `location.state`, **no** en la URL ni en `sessionStorage`; se valida que empiece con `/` y no con `//` para evitar open redirect. El login fallido muestra el error del formulario y **no** redirige. El `401` de `/me` en el arranque sigue el mismo camino: limpiar y quedar en login, sin mensaje de “sesión vencida” si el usuario nunca llegó a autenticarse.

```
Request protegida
      |
      v
   status 401? --no--> respuesta normal
      |
     sí
      v
 ¿es POST /api/auth/login? --sí--> error de credenciales en el formulario (no redirige)
      |
     no
      v
 limpiar TokenStore + usuario + cachés
      |
      v
 RequireAuth navega a /login con state.from + expired
      |
      v
 login correcto -> /me -> volver a from validado (o /)
```

### D3 — Contexto de sesión, arranque con `GET /api/auth/me` y estado “cargando sesión”

**Problema**: la UI necesita saber si hay sesión, quién es el usuario y qué rol tiene antes de renderizar el menú o redirigir. Hay que decidir el contenedor del estado, cuándo se consulta `/me` y qué se muestra mientras tanto.

- **Opción A (recomendada)**: **React Context** (`AuthProvider` + `useAuth`) con una máquina de estados mínima:
  - `status: "checking"` al arrancar: si hay token en el `TokenStore`, se llama `GET /api/auth/me`; mientras tanto se muestra `LoadingState` a pantalla completa y **no se redirige**.
  - `status: "authenticated"` con `user` (`id`, `username`, `displayName`, `role`, `professionalId`) cuando `/me` responde `200`.
  - `status: "anonymous"` cuando no hay token o `/me` responde `401`; el guard redirige al login.
  - `login(username, password)` hace `POST /login`, guarda el token y luego `GET /me`; si `/me` da `401`, descarta el token y propaga el error; si `/me` falla por red, conserva el token y ofrece reintentar.
  - `logout()` limpia token, usuario y cachés y pasa a `anonymous`.
  - `lastEvent: "expired" | "manual" | null` para que el login muestre el mensaje correcto.
  - *Pros*: una sola fuente de verdad; el menú y los guards leen lo mismo; el estado `checking` evita el parpadeo de “login → home → login”; es testeable inyectando `tokenStore` y el cliente; no hace falta una librería de estado global.
  - *Contras*: hay que cuidar que el `AuthProvider` esté dentro del router si necesita navegar, o que el guard sea quien navegue (recomendado: el guard navega, el provider solo cambia estado).
- **Opción B — sin contexto, cada pantalla llama a `/me`**: cada página pide el usuario.
  - *Pros*: no hay estado compartido.
  - *Contras*: requests duplicadas, parpadeos, menú inconsistente, cada pantalla maneja `401`; no se recomienda.
- **Opción C — guardar el usuario en `sessionStorage`/`localStorage`**: evitar `/me` al recargar.
  - *Pros*: arranque más rápido.
  - *Contras*: el rol y el `professionalId` pueden quedar viejos; el spec exige releer el usuario; se duplica la fuente de verdad; no se recomienda.
- **Recomendación**: **A**. `AuthProvider` arriba del router o en la ruta raíz; el estado `checking` es obligatorio; `/me` es la única fuente del usuario y del rol. Un error de red en `/me` **no** descarta el token: muestra `ErrorState` con reintento, porque un corte momentáneo no es un `401`. Un `401` en `/me` sí descarta y va al login.

```
                 +-------------+
   arranque ---> |  checking   |
                 +-------------+
                   |         |
        /me 200    |         |  sin token / /me 401
                   v         v
           +---------------+ +-------------+
           | authenticated | |  anonymous  |
           +---------------+ +-------------+
             |         ^         |
       logout|         |login    | login 200 + /me 200
             v         |         v
           +---------------+  (vuelve a authenticated)
           |  anonymous    |
           +---------------+
```

### D4 — Rutas protegidas y redirecciones login ↔ resto con React Router 6

**Problema**: C-25 deja un router mínimo (`/` y `*`). C-26 necesita `/login`, proteger el resto, evitar que un usuario autenticado vea el login y conservar la ruta de destino sin abrir un redirect abierto.

- **Opción A (recomendada)**: **guards como componentes de layout** con `<Outlet />`:
  - `/login` envuelto en `PublicOnlyRoute`: si `status === "authenticated"`, redirige a `from` validado o `/`; si `checking`, muestra `LoadingState`; si `anonymous`, muestra el login.
  - Ruta de layout protegida `RequireAuth` + `AppShell` con `<Outlet />`: si `checking`, `LoadingState`; si `anonymous`, `<Navigate to="/login" replace state={{ from: location, expired: lastEvent === "expired" }} />`; si `authenticated`, renderiza el shell y los hijos.
  - Hijos: `index` con `HomePage` (el shell de C-25) y `*` con `NotFoundPage` dentro del shell.
  - El `from` se valida con una función pura `safeInternalPath(path)`: debe empezar con `/`, no con `//`, no ser `/login`; si no, `/`.
  - Se exportan las **rutas** (`routes`) separadas de `createBrowserRouter`, para que los tests usen `createMemoryRouter` con las mismas rutas.
  - *Pros*: guards declarativos y testeables; una sola regla para todo el shell; la ruta de destino se conserva; el back/forward funciona; no hay loaders que dependan de contexto; encaja con `createBrowserRouter` de C-25.
  - *Contras*: hay que reestructurar el `App` de C-25 para envolver `/` y `*` con el layout; es un cambio pequeño y localizado.
- **Opción B — guards en `loader` de cada ruta**: el loader consulta la sesión antes de renderizar.
  - *Pros*: la decisión ocurre antes del render.
  - *Contras*: el estado de auth es del cliente y no del servidor; los loaders corren antes del contexto; hay que duplicar el guard por ruta o usar un loader padre; más difícil de testear con estado inyectado; no se recomienda.
- **Opción C — condicionales en `App` sin router**: renderizar login o shell según `status`.
  - *Pros*: menos concepto.
  - *Contras*: URLs no compartibles, back/forward roto, C-27+ necesitan rutas; no se recomienda.
- **Recomendación**: **A**. El guard navega; el `AuthProvider` solo cambia estado. Así se evita el problema de usar `useNavigate` en un provider que está por fuera del router. `/login` nunca parpadea para un usuario autenticado porque `checking` muestra carga. El `*` queda dentro del shell protegido: una URL desconocida con sesión muestra el 404 con menú; sin sesión, el guard manda al login.

```
/login  -> PublicOnlyRoute -> LoginPage
/       -> RequireAuth -> AppShell (header + main + footer)
             |- index -> HomePage
             \- *     -> NotFoundPage
```

### D5 — Menú y acciones según rol: de dónde sale el rol y por qué la API sigue decidiendo

**Problema**: la UI debe mostrar un menú y acciones coherentes con el rol, sin duplicar la matriz RBAC ni convertirse en la autoridad. Hay que decidir de dónde sale el rol, qué ve cada rol y cómo se maneja un `403`.

- **Opción A (recomendada)**: **rol desde `GET /api/auth/me`** (`user.role`), con dos funciones puras y chicas:
  - `menuFor(role)` devuelve los ítems de navegación visibles para ese rol, según la matriz de KB 03.
  - `can(role, capability)` decide si se muestra un botón/acción de UI. **No** decide reglas de dominio ni reemplaza al backend.
  - El shell renderiza `menuFor(role)`; los ítems cuyas pantallas todavía no existen (C-27+) se muestran `disabled` con “Próximamente” o se ocultan, según la pregunta P4.
  - Ante un `403`, la UI muestra el mensaje de `violations` tal cual (`FORBIDDEN_OPERATION`) y **no** asume que la acción se hizo. Si el rol pudo haber cambiado, se puede refrescar `/me`; si `/me` da `401`, se aplica D2.
  - *Pros*: una sola fuente del rol; la matriz de visibilidad queda testeada; el menú es consistente; la API sigue siendo la que rechaza; no se duplican RN-AG/RN-TU.
  - *Contras*: hay que mantener `menuFor`/`can` sincronizados con KB 03; se mitiga con una tabla de tests por rol y un comentario que apunte a KB 03.
- **Opción B — decodificar el JWT en el front y leer `role`**: usar el claim del token.
  - *Pros*: no hace falta `/me` para el rol.
  - *Contras*: el token es opaco; el rol puede haber cambiado y el token sigue viejo; el spec dice que `/me` relee el usuario; se fomenta confiar en el cliente; no se recomienda.
- **Opción C — mostrar todas las acciones y dejar que la API rechace**: no ocultar nada.
  - *Pros*: simple; imposible desincronizar la UI.
  - *Contras*: el usuario ve acciones que no puede hacer; el video se ve peor; el `403` se vuelve la experiencia normal; no se recomienda.
- **Recomendación**: **A**. La UI **puede anticipar** y ocultar, pero el rechazo definitivo es de la API (`401` antes de permisos; `403` con `FORBIDDEN_OPERATION`). Ocultar un botón no es una frontera de seguridad: el `fetch` se puede repetir a mano. `menuFor`/`can` no contienen reglas de agenda; solo la matriz RBAC de visibilidad.

Matriz de menú/acciones para C-26 (derivada de KB 03 §RBAC y `backend/app/auth/permissions.py`):

| Pantalla / acción | Odontólogo | Recepción | Administrador | Nota |
|-------------------|------------|-----------|---------------|------|
| Agenda (leer) | Sí (todos) | Sí (todos) | Sí (todos) | C-27 |
| Dar turno | **No** | Sí | Sí | C-29; el odontólogo no da turnos |
| Reprogramar / cancelar | **No** | Sí (todos) | Sí (todos) | C-30 |
| Cambiar estado (confirmado/atendido/ausente) | Sí (propios) | Sí (todos) | Sí (todos) | C-30; el alcance propio lo decide el dominio |
| Historial de turno | Sí (propios) | Sí (todos) | Sí (todos) | C-30 |
| Horarios de atención | CRU propio | Solo lectura | CRUD | C-32 |
| Bloqueos | CRUD propio | Solo lectura | CRUD | C-32 |
| Profesionales | Solo lectura | Solo lectura | CRUD | C-33 |
| Sillones | Solo lectura | Solo lectura | CRUD | C-33 |
| Prestaciones | Solo lectura | Solo lectura | CRUD | C-33 |
| Pacientes | Solo lectura | CRU | CRU | C-33 |
| Usuarios y roles | **No** | **No** | CRUD (backlog) | Sin `/api/users` en el MVP |

> El odontólogo **lee la agenda completa** pero solo modifica estados de sus propios turnos; la UI puede comparar `user.professionalId` con el profesional del turno cuando el dato esté disponible (C-30), pero la decisión final es del dominio/API.

### D6 — Pantalla de login: campos, error genérico, accesibilidad y calidad visual

**Problema**: el login es la primera pantalla que se ve y va en el video. Tiene que ser accesible, clara, no filtrar qué credencial falló y no romper el diseño de C-25.

- **Opción A (recomendada)**: una tarjeta de login propia, centrada, sobre los tokens de C-25:
  - Campos: **Usuario** (`text`, `autocomplete="username"`, `maxLength=150`, `required`) y **Contraseña** (`password`, `autocomplete="current-password"`, `maxLength=128`, `required`), con `<label>` visible y `htmlFor`.
  - **Validación local mínima** solo para vacíos (mensaje de campo), antes de enviar; las credenciales inválidas **no** se validan en el cliente.
  - **Error de credenciales**: `401` del backend → se muestra el mensaje exacto del backend (“Usuario o contraseña incorrectos.”) en un contenedor `role="alert"` con `aria-live="polite"`; **no** se dice si falló el usuario o la contraseña, **no** se resalta un campo, **no** se revela si el usuario existe o está inactivo.
  - **Estado de envío**: botón deshabilitado con texto “Ingresando…” y `aria-busy="true"`; se evita el doble submit; al terminar se restaura.
  - **Errores distintos**: red/servidor caído → “No se pudo conectar con el servidor. Intentá de nuevo.”; sesión vencida → “La sesión venció. Iniciá sesión de nuevo.”; `400` de validación → mensajes de campo del backend o local.
  - **Accesibilidad**: foco inicial en Usuario; orden de tabulación natural; Enter envía; foco visible de C-25; error anunciado; contraste AA; sin texto solo en color; `aria-describedby` para el error; `autoFocus` opcional sin robar foco si hay un mensaje.
  - **Estética**: tarjeta con borde/sombra suave, espaciado de la escala, tipografía del sistema, nombre del consultorio y subtítulo; sin imágenes externas ni fuentes remotas (funciona offline); responsive; sin “recordarme”; sin credenciales precargadas; sin guardar el usuario en storage.
  - **Seguridad del formulario**: `method="post"` conceptual, nunca `GET`; no poner usuario/contraseña en la URL; no loguear; limpiar el campo de contraseña después del intento; permitir gestores de contraseñas.
  - *Pros*: cumple el scope, se ve bien en el video, es accesible, no enumera usuarios, reutiliza tokens/componentes de C-25 y es testeable con `user-event` por rol/etiqueta.
  - *Contras*: hay que escribir estilos y tests de accesibilidad; es acotado y una sola pantalla.
- **Opción B — formulario HTML mínimo sin estilos**: inputs y botón sin tarjeta.
  - *Pros*: rapidísimo.
  - *Contras*: no cumple “frontend cuidado”, se ve pobre en el video, suele fallar accesibilidad (labels, foco, error); no se recomienda.
- **Opción C — librería de componentes/login template**: MUI/Chakra o un template.
  - *Pros*: look inmediato.
  - *Contras*: dependencia pesada, choca con la decisión de C-25 (CSS Modules + tokens), agrega bundle y una estética ajena; no se recomienda.
- **Recomendación**: **A**. La pantalla de login es la vidriera del TP: invertir en una tarjeta simple, prolija y accesible, no en una librería. El mensaje de credenciales inválidas es el del backend, textual, y es el mismo para usuario inexistente, contraseña incorrecta y usuario inactivo.

```
+------------------------------------------+
|  Turnos Odontologia                      |
|  Iniciar sesion                          |
|                                          |
|  Usuario                                 |
|  [____________________________________]  |
|                                          |
|  Contrasena                              |
|  [____________________________________]  |
|                                          |
|  [ Ingresar ]                            |
|                                          |
|  (role=alert) Usuario o contrasena       |
|  incorrectos.                            |
+------------------------------------------+
```

### D7 — Cierre de sesión

**Problema**: cerrar sesión debe dejar el cliente sin token y sin datos del usuario, sin llamar a un endpoint que no existe y sin dejar rastros que permitan volver atrás.

- **Opción A (recomendada)**: **logout solo en el cliente**:
  - Quitar la clave propia del `TokenStore` (nunca `sessionStorage.clear()` ni `localStorage.clear()`, que borrarían datos ajenos).
  - Poner el `authProvider` en `null` o hacer que `getToken()` devuelva `null`, para que las requests siguientes no lleven `Authorization`.
  - Limpiar el usuario y las cachés de datos de la app (hoy no hay TanStack Query; cuando C-27 lo agregue, su caché se limpia acá).
  - Pasar a `anonymous` y navegar a `/login` con `replace`; no conservar `from` ni mostrar “sesión vencida” (el motivo es `manual`).
  - No llamar al backend: no hay `/api/auth/logout` y el token sigue válido hasta `exp`. Se documenta en `verify-C-26.md`.
  - *Pros*: simple, sin backend, consistente con SU-06; el usuario vuelve al login; no deja datos del usuario en la UI.
  - *Contras*: el token robado sigue siendo válido hasta `exp`; no hay revocación global; es el trade-off aceptado del MVP.
- **Opción B — llamar a un endpoint de logout/revocación**: el backend invalida el token.
  - *Pros*: cierra de verdad del lado servidor.
  - *Contras*: **no existe**; requeriría lista negra/revocación y tocar C-19; está fuera de SU-06/DD-11; no se recomienda para C-26.
- **Opción C — solo navegar al login sin limpiar**: dejar el token y el usuario.
  - *Pros*: nada que implementar.
  - *Contras*: el guard vería `authenticated` y volvería a entrar; la sesión queda abierta; es un bug de seguridad; descartada.
- **Recomendación**: **A**. Botón “Cerrar sesión” accesible en el header/menú, sin confirmación (o confirmación opcional, P5). En `sessionStorage` cada pestaña tiene su sesión: cerrar sesión en una pestaña no cierra las otras; se documenta. Si la autora quisiera logout global entre pestañas, habría que pasar a `localStorage` + evento `storage`, lo que sube el riesgo de XSS y no se recomienda en el MVP.

### D8 — Módulo de auth, costura `setAuthProvider` y contrato del token

**Problema**: C-25 deja una costura (`setAuthProvider({ getToken })`) pero no un módulo de auth. Hay que decidir dónde vive el storage, cómo se conecta al cliente y cómo se evita que el cliente de transporte conozca `sessionStorage`.

- **Opción A (recomendada)**:
  - `src/features/auth/tokenStore.ts`: interfaz `TokenStore` con `getToken(): string | null`, `setToken(token: string): void`, `clear(): void`; implementaciones `createSessionTokenStore()` (producción, clave `turnos.auth.accessToken`, con fallback a memoria si `sessionStorage` falla) y `createMemoryTokenStore()` (tests).
  - `src/features/auth/authApi.ts`: `login(username, password)` y `fetchMe()`, construidos sobre el cliente de C-25; `login` usa una variante **sin** `Authorization` (aunque haya un token viejo), `fetchMe` usa el token.
  - `src/features/auth/AuthContext.tsx`: `AuthProvider`, `useAuth`, máquina de estados de D3; recibe `tokenStore` y el cliente/`fetch` por props con defaults de producción (inyección para tests).
  - `src/features/auth/RequireAuth.tsx` y `PublicOnlyRoute.tsx`: guards de D4.
  - `src/features/auth/menuFor.ts`: matriz de visibilidad de D5.
  - `src/features/login/LoginPage.tsx` + `LoginForm.tsx`: pantalla de D6.
  - `main.tsx`/`App.tsx`: crear el `TokenStore`, `setAuthProvider({ getToken: tokenStore.getToken })`, montar `AuthProvider` y el router; en login guardar el token, en logout limpiarlo y volver a `setAuthProvider(null)` (o un provider que devuelva `null`).
  - El cliente de C-25 **no importa** `sessionStorage` ni el módulo de auth: solo llama a `getToken`. Se preserva la costura.
  - *Pros*: separación clara transporte/almacenamiento/sesión; testeable sin mocks; el storage es swappable (memoria/sessionStorage/futuro cookie); el cliente no se contamina.
  - *Contras*: más archivos; es la estructura natural de una feature de auth y no es over-engineering.
- **Opción B — todo en un solo `auth.ts` o en `App.tsx`**: storage, API, contexto y guards juntos.
  - *Pros*: menos archivos.
  - *Contras*: mezcla responsabilidades, difícil de testear por partes, crece con C-27..C-33; no se recomienda.
- **Opción C — que `client.ts` lea `sessionStorage` directamente**: el transporte conoce el storage.
  - *Pros*: menos cableado.
  - *Contras*: viola la costura de C-25, esconde la decisión ALTO en el transporte, impide testear con un store en memoria y mezcla capas; descartada.
- **Recomendación**: **A**. `getToken` es **síncrono** y devuelve `string | null`; el cliente agrega `Authorization: Bearer <token>` solo si no es nulo; el login usa `auth: "omit"` (o un cliente sin provider) para no mandar un token viejo. Si C-25 no expone una factory `createApiClient({ fetchFn })` y solo un singleton, C-26 agrega la factory de forma **aditiva**, sin cambiar el contrato público. El `AuthProvider` debe quedar dentro del router (o el guard navega) para no usar `useNavigate` fuera de contexto.

### D9 — Semántica de errores de autenticación y `403` en la UI

**Problema**: `401` significa dos cosas distintas (credenciales inválidas en login vs. sesión inválida en ruta protegida), y hay `400`, `403`, `409/422`, red y `5xx`. La UI no puede tratarlos todos igual ni filtrar información.

- **Opción A (recomendada)**: mapear por situación, no por status aislado:

  | Situación | Status | Qué muestra la UI | ¿Descarta token? |
  |-----------|--------|-------------------|------------------|
  | Login con credenciales inválidas | `401` en `/auth/login` | Mensaje textual del backend; genérico; sin campo resaltado | No (no hay token nuevo) |
  | Login con datos faltantes/inválidos | `400` en `/auth/login` | Mensajes de `errors[]` o validación local de vacíos | No |
  | Token vencido/inválido en ruta protegida | `401` | Vuelve al login con “La sesión venció…” | **Sí** |
  | `/me` del arranque con token inválido | `401` | Va al login sin mensaje de vencimiento | **Sí** |
  | Rol sin permiso | `403` | Mensaje de `violations[]` tal cual (`FORBIDDEN_OPERATION`) | No |
  | Conflicto de agenda / regla de validez | `409`/`422` | Mensajes de `violations[]` tal cual | No |
  | No encontrado | `404` | Mensaje `message` | No |
  | Red caída / `5xx` | — | “No se pudo conectar…” con reintento | No |
  | Respuesta desconocida | — | Mensaje genérico; nunca JSON crudo | No |

  - *Pros*: respeta el contrato de C-25 (`getApiErrorMessages`); no confunde login con sesión; muestra los mensajes del dominio sin reescribirlos; solo el `401` protegido limpia la sesión; no filtra si el usuario existe.
  - *Contras*: hay que distinguir el endpoint en el manejador; es una condición explícita y testeable.
- **Opción B — mostrar el cuerpo crudo de la API**: volcar el JSON o el `message` sin mapear.
  - *Pros*: simple.
  - *Contras*: puede mostrar JSON, detalles internos o mensajes poco amigables; no cumple “frontend cuidado”; no se recomienda.
- **Opción C — un único mensaje genérico para todo**: “Ocurrió un error”.
  - *Pros*: no filtra nada.
  - *Contras*: pierde los mensajes del dominio y la accesibilidad para corregir; no se recomienda.
- **Recomendación**: **A**. El `401` del login es un error de formulario; el `401` de una ruta protegida es un evento de sesión. El `403` no limpia el token: el usuario sigue autenticado, solo no tiene permiso. No se loguean credenciales, tokens ni cuerpos sensibles.

### D10 — Cómo se testea sin mocks: `fetch` inyectado, router en memoria y el `401`

**Problema**: el proyecto prohíbe mocks de colaboradores internos y C1 prohíbe `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos y MSW. Hay que probar login, sesión, guards, menú y el `401` sin simular módulos.

- **Opción A (recomendada)**:
  - **Cliente**: `createApiClient({ fetchFn, authProvider })` o funciones que reciben el cliente; los tests pasan una función **real** `async (input, init) => new Response(JSON.stringify(body), { status, headers })`. Para inspeccionar método/headers/body, la función real guarda `init` en un array del propio test (closure), no un mock.
  - **TokenStore**: en tests se usa `createMemoryTokenStore()` o el `sessionStorage` real de jsdom; se limpia con `afterEach` (sin `vi.stubGlobal`). La producción usa `createSessionTokenStore()`.
  - **Router**: exportar `routes` y montar `createMemoryRouter(routes, { initialEntries: ["/login"] })` + `RouterProvider`; se afirma `router.state.location.pathname`/`state` para redirecciones, sin tocar `window.history`.
  - **AuthProvider**: recibe `tokenStore` y el cliente/`fetch` por props; no se parchea el singleton global.
  - **Interacción**: `@testing-library/user-event` para tipear, tabular, Enter y click; `jest-dom` para roles/textos; `waitFor` para estados asíncronos.
  - **Sin timers falsos**: no hay expiración proactiva; el `401` se simula con una respuesta real.
  - *Pros*: cumple C1 y la regla de no mockear colaboradores; prueba el borde real (`Response`), la accesibilidad y los flujos completos; los tests son deterministas y no contaminan otros.
  - *Contras*: hay que escribir funciones `fetch` de prueba y cablear el provider; es poco código y explícito.
- **Opción B — MSW**: interceptar a nivel de red.
  - *Pros*: realista y reutilizable.
  - *Contras*: C1 lo prohíbe; agrega dependencia y setup; no se recomienda.
- **Opción C — `vi.mock`/`vi.spyOn`/`vi.fn`**: reemplazar módulos o funciones.
  - *Pros*: rápido de escribir.
  - *Contras*: prohibido por C1; oculta el comportamiento real y contamina; descartada.
- **Recomendación**: **A**. Tests mínimos de C-26:

  | Escenario | Qué se prueba |
  |-----------|---------------|
  | Login correcto | `POST /login` guarda el token, llama `/me`, setea `user` y redirige a `/` o `from` |
  | Credenciales inválidas | `401` del login muestra el mensaje genérico, no guarda token, no redirige |
  | Login `400` | Mensajes de validación sin revelar credenciales |
  | `/me` al arrancar | `checking` muestra `LoadingState`; `200` pasa a autenticado; `401` limpia y va al login |
  | `/me` con error de red | Conserva el token y muestra reintento; no redirige |
  | Ruta protegida sin sesión | Redirige a `/login` con `from` validado |
  | Ruta `/login` con sesión | Redirige a `/` o al `from` válido; no muestra el formulario |
  | `401` en ruta protegida | Limpia token, va al login, muestra “La sesión venció…” |
  | `from` inseguro | `//evil.example` o externo se descarta y se va a `/` |
  | Header `Authorization` | Solo aparece con token; el login no manda token viejo |
  | Menú por rol | `menuFor` devuelve lo esperado para odontólogo, recepción y administrador |
  | `403` | Muestra el mensaje de `violations` y no limpia el token |
  | Logout | Limpia token/usuario, no llama al backend, va al login |
  | TokenStore | Set/get/clear; `sessionStorage` real; fallback a memoria si falla |
  | Sin storage prohibido | No hay `localStorage`, cookies ni token en URL; `sessionStorage` solo en el adaptador de auth |

### D11 — Mutaciones y trazabilidad adaptadas al front: el detector de mutaciones inválidas

**Problema**: C-20..C-25 tienen `mutaciones-C-XX.py` y `trazabilidad-C-XX.py`. `mutaciones-C-23.py` no solo corre la mutación: **detecta mutaciones inválidas** (las que matan el test por `NameError`/`ImportError`, por un frame fuera de `tests/` o por un error que no es una afirmación propia). El front necesita el equivalente, con la salida de Vitest, no la de pytest.

- **Opción A (recomendada)**: crear `docs/evidencias/mutaciones-C-26.py` como espejo adaptado:
  - Una mutación por cada test nuevo, siempre sobre código de producción de `frontend/src` (nunca sobre tests).
  - Comprobar que el texto original aparezca **exactamente una vez**, que la mutación cambie el archivo y que el SHA-256 de `frontend/src` vuelva al original al final.
  - Correr solo el test de esa mutación: `npm run test:run -- <archivo>` (desde `frontend/`), restaurar en `finally` y volver a correr para confirmar verde.
  - **Detector de invalidez** (equivalente al de C-23, adaptado a Vitest): es inválida si
    - la salida contiene `ReferenceError`, `SyntaxError`, `Cannot find module`, `Failed to resolve import` o un `TypeError` de código mutado sin una afirmación del test;
    - el primer fallo no tiene su frame en `frontend/src/**/*.test.ts`/`.test.tsx` (el test que debe detectar);
    - el fallo no es `AssertionError`, `expect(...)`, `TestingLibraryElementError` o un `waitFor` timeout con una aserción dentro;
    - el test queda en timeout sin una aserción propia.
  - Usar `--reporter=json` de Vitest (o parsear texto como fallback) para leer `failureMessages` y los frames; el reporte crudo va a `mutaciones-C-26.txt`.
  - `docs/evidencias/trazabilidad-C-26.py`: cada escenario del spec nuevo (`ui-login-and-session`) mapeado a un test; comprobar que el test exista (`vitest list --json` o el reporte JSON) y terminar en “N escenarios, 0 problemas”; salida a `trazabilidad-C-26.txt`.
  - Evidencias: `red-C-26/`, `baseline-C-26.txt`, `vitest-C-26.txt`, `tsc-C-26.txt`, `eslint-C-26.txt`, `mutaciones-C-26.py`/`.txt`, `trazabilidad-C-26.py`/`.txt`, `verify-C-26.md`.
  - *Pros*: mantiene la paridad con el backend; detecta tests que “pasan porque sí”; el detector de invalidez no se pierde en el front; es un script propio, sin Stryker.
  - *Contras*: hay que adaptar el parseo de la salida de Vitest; es acotado y se prueba con las primeras mutaciones.
- **Opción B — StrykerJS**: mutation testing real.
  - *Pros*: reporte y cobertura de mutantes.
  - *Contras*: dependencia y configuración extra, mucho más lento, distinto del resto del repo; no se recomienda.
- **Opción C — no hacer mutaciones ni trazabilidad**:
  - *Pros*: menos trabajo.
  - *Contras*: rompe la disciplina de C-20..C-25 y la evidencia que la cátedra evalúa; no se recomienda.
- **Recomendación**: **A**. El detector de C-23 **tiene que existir también en el front**: la versión C-26 conserva la idea de “solo vale si el test falla por su propia afirmación”, adaptada a los mensajes y frames de Vitest. La trazabilidad se genera desde el spec, no se escribe a mano.

### D12 — Qué NO hace C-26

**Problema**: evitar que el login se convierta en “toda la seguridad” y se solape con C-27..C-33, C-19 o el backlog.

- **Opción A (recomendada)**: alcance estricto. C-26 **no** hace:
  - cambio de contraseña, recuperación, alta de usuarios, ABM de usuarios, MFA, SSO, bloqueo por intentos, rate limiting;
  - refresh tokens, revocación, logout del servidor, “cerrar sesión en todos los dispositivos”;
  - cookies, CSRF, `HttpOnly`, persistencia entre reinicios, “recordarme”;
  - decodificación del JWT para autorizar, reglas de negocio en el front, duplicación de RN-AG/RN-TU;
  - pantallas de agenda/turnos/horarios/bloqueos/catálogos/pacientes (C-27..C-33);
  - cambios en `backend/`, migraciones, specs existentes, KB, `CHANGES.md`, `docker-compose.yml` o `.env`;
  - tests E2E con navegador real.
  - *Pros*: change chico y terminable; no mezcla governance; el camino crítico avanza; el login queda listo para que C-27+ consuman la sesión.
  - *Contras*: la app al terminar C-26 sigue siendo login + shell; es lo esperado.
- **Opción B — adelantar “cambio de contraseña”**: agregar la pantalla y el endpoint.
  - *Pros*: útil.
  - *Contras*: no hay endpoint, SU-06 lo excluye, toca backend y seguridad; no se recomienda.
- **Opción C — adelantar el ABM de usuarios**: administrar usuarios y roles desde la UI.
  - *Pros*: el administrador podría gestionar altas.
  - *Contras*: no existe `/api/users`; está en backlog; suma backend, migraciones y seguridad; no se recomienda.
- **Recomendación**: **A**. C-26 entrega login, sesión, guards, menú por rol, logout y tests; nada más.

### D13 — Variables, CORS y frontera con el backend: sin cookies ni secretos nuevos

**Problema**: el login toca la seguridad; hay que confirmar que C-26 no agrega secretos, no cambia CORS, no cambia el contrato y no introduce CSRF.

- **Opción A (recomendada)**:
  - No se agregan variables: se reutilizan `VITE_API_URL` y `CORS_ORIGIN` de `.env.example`. No hay secretos en el front (`JWT_SECRET` jamás llega al navegador).
  - El navegador llama a `http://localhost:8000/api`; el CORS ya permite `http://localhost:5173`; no se toca `backend/`.
  - Se usa `Authorization: Bearer` en el header; no se usan cookies ni `credentials: "include"`, así que no hay CSRF que mitigar mientras se mantenga el Bearer.
  - El token no va en la URL, ni en logs, ni en mensajes de error, ni en `localStorage`.
  - Se evita `dangerouslySetInnerHTML`, `eval` y scripts de terceros; una CSP `script-src 'self'` queda como mejora futura documentada.
  - *Pros*: cero cambios de backend; el contrato de C-19 se respeta; no se abren vectores nuevos; el CORS actual alcanza.
  - *Contras*: el token queda legible por JavaScript (ver D1); es el trade-off aceptado del MVP.
- **Opción B — agregar variables de configuración de auth** (`VITE_AUTH_STORAGE`, etc.):
  - *Pros*: cambiar storage sin recompilar.
  - *Contras*: configuración innecesaria que puede quedar mal en producción; una decisión de seguridad no debería depender de una variable pública del bundle; no se recomienda.
- **Opción C — pasar a cookie/`HttpOnly`**:
  - *Pros*: reduce el riesgo de XSS.
  - *Contras*: requiere cambiar el login para setear cookie, CORS con credenciales y protección CSRF; es una extensión de C-19, no de C-26; se documenta como evolución futura.
- **Recomendación**: **A**. C-26 no toca `backend/`, no agrega secretos ni variables y no cambia el contrato. Si en el futuro se quiere `HttpOnly`, se hace en un change de backend con CSRF y se actualiza el spec de autenticación.

### D14 — Convivencia con el test guardián de C-25 que prohíbe storage

**Problema**: el spec de C-25 tiene un escenario que busca en **todo** `frontend/src` y afirma que no hay accesos a `localStorage`, `sessionStorage` ni cookies para token. C-26 agrega `sessionStorage` a propósito. Si el test se deja como está, C-26 lo rompe o tienta a borrarlo; si se borra, se pierde la garantía de que el storage está confinado.

- **Opción A (recomendada)**: **acotar el guardián con una allowlist**:
  - El test de C-25 se ajusta para permitir `sessionStorage` **solo** en `src/features/auth/tokenStore.ts` (y en su test, si lo hay), y seguir prohibiendo `localStorage`, cookies y cualquier otro acceso en el resto de `frontend/src`.
  - C-26 agrega su propio test de que el único acceso a storage es ese adaptador y que el cliente de API no importa `sessionStorage`.
  - Se documenta el cambio en `verify-C-26.md` y, si corresponde, en el delta spec de `frontend-foundation`/`ui-login-and-session`.
  - *Pros*: conserva la garantía de C-25 y la hace más precisa; evita que el storage se disperse; el test sigue siendo útil después de C-26.
  - *Contras*: hay que tocar un test de C-25; es un cambio pequeño y justificado.
- **Opción B — borrar el test de C-25**: eliminar el escenario “C-25 no persiste el token”.
  - *Pros*: no hay que ajustar nada.
  - *Contras*: se pierde la protección contra storage descontrolado; no se recomienda.
- **Opción C — dejar el test y poner el storage fuera de `frontend/src`**: por ejemplo, en un módulo inyectado desde fuera.
  - *Pros*: el test pasa sin cambios.
  - *Contras*: es artificial, rompe la estructura de la feature y no aporta; descartada.
- **Recomendación**: **A**. El storage vive en **un solo archivo** (`tokenStore.ts`) y el resto del front no lo conoce; el guardián de C-25 se vuelve una allowlist explícita. Esto también facilita un futuro cambio a cookie o memoria: se reemplaza el adaptador.

---

## 4. Riesgos y preguntas para la autora

### Riesgos (con foco en seguridad)

| Riesgo | Mitigación |
|--------|------------|
| XSS lee el token de `sessionStorage` y lo exfiltra | Sin `dangerouslySetInnerHTML`, sin scripts de terceros, dependencias mínimas, CSP `script-src 'self'` futura, token de vida corta; riesgo residual aceptado y documentado. |
| `localStorage` deja la sesión abierta en una máquina compartida | Se elige `sessionStorage`; se prohíbe `localStorage` en el guardián de D14. |
| El `401` del login se confunde con sesión vencida y genera un bucle | El manejador global excluye `POST /api/auth/login`; el login fallido es error de formulario; test explícito. |
| El `401` de una request en segundo plano saca al usuario de un formulario | Se conserva `from` y se muestra el mensaje; C-29+ puede agregar borradores; en C-26 no hay formularios de negocio. |
| Open redirect con `from=//evil.example` | `safeInternalPath`: solo `/...`, nunca `//`, nunca externo; test. |
| Ocultar botones se confunde con autorización | `menuFor`/`can` son solo visibilidad; la API sigue devolviendo `401`/`403`; test de `403` y de que un `fetch` manual sigue siendo rechazado. |
| El rol del menú queda viejo si cambia en la base | El rol sale de `/me`; si cambia, el request siguiente da `401` y se limpia la sesión; no se decodifica el JWT. |
| Logout no invalida el token en el servidor | Trade-off de SU-06; token corto; se documenta que un token robado vive hasta `exp`; revocación futura. |
| Token o contraseña en logs, URL o mensajes de error | No se loguean; no se ponen en la URL; el formulario no usa `GET`; el cliente no muestra cuerpos crudos; `Cache-Control: no-store` ya viene del backend. |
| Sesión compartida entre pestañas | `sessionStorage` es por pestaña; una pestaña nueva pide login; se documenta; no hay sincronización por `storage` en el MVP. |
| `sessionStorage` lanza en modo privado/cuota | El adaptador cae a memoria y lo informa; el login sigue funcionando en esa pestaña. |
| Error de red en `/me` se trata como logout y se pierde la sesión | En error de red/`5xx` se conserva el token y se muestra reintento; solo `401` limpia. |
| Tests con mocks ocultan fallos | C1: `fetch` inyectado, `TokenStore` en memoria, router en memoria; mutaciones y trazabilidad. |
| El test guardián de C-25 se rompe o se borra | D14: allowlist de un solo archivo y test propio de C-26. |
| Dependencias del front comprometidas | `package-lock.json` versionado, dependencias mínimas, sin librerías de auth externas; `npm audit` como control manual en `verify`. |
| CSRF si en el futuro se pasa a cookie | Hoy no aplica (Bearer en header); si se cambia, agregar `SameSite` y token CSRF en el mismo change de backend. |
| Fuerza bruta / enumeración de usuarios | El backend ya responde igual para los tres casos; la UI no agrega señales; rate limiting es del backend/backlog, no de C-26. |

### Preguntas para la autora

- **P1**: ¿Confirmás `sessionStorage` (sobrevive recarga, se limpia al cerrar la pestaña) o preferís solo memoria (más seguro, pero pide login en cada recarga) (D1)? *Sugerencia: `sessionStorage`.*
- **P2**: ¿Conservamos la ruta de destino (`from`) después de un `401` y volvemos ahí tras el login (D2)? *Sugerencia: sí, validando que sea interna.*
- **P3**: Si `/me` falla por red al arrancar, ¿mantenemos el token y mostramos reintento, o cerramos sesión (D3)? *Sugerencia: mantener y reintentar; solo `401` cierra.*
- **P4**: ¿El menú muestra los ítems de pantallas futuras como “Próximamente” (para que se vea el menú por rol en el video) o solo los que ya tienen ruta (D5)? *Sugerencia: “Próximamente” deshabilitado, con la matriz testeada.*
- **P5**: ¿El logout pide confirmación o cierra directo (D7)? *Sugerencia: directo, sin diálogo, para una recepcionista.*
- **P6**: ¿Mostramos un botón “ver contraseña” en el login (D6)? *Sugerencia: opcional; si se agrega, con etiqueta accesible; no es necesario para el MVP.*
- **P7**: ¿Un `403` debe refrescar `/me` para actualizar el rol, o solo mostrar el mensaje (D5/D9)? *Sugerencia: mostrar el mensaje; refrescar solo si la autora quiere detectar cambios de rol sin recargar.*
- **P8**: ¿El login recuerda el último usuario en `sessionStorage` para comodidad? *Sugerencia: no; evita datos personales y simplifica.*
- **P9**: ¿Confirmás que C-26 no toca `backend/` ni migra a cookie/`HttpOnly`, y que eso queda como extensión futura (D13)? *Sugerencia: sí.*
- **P10**: ¿El test guardián de C-25 se ajusta con allowlist al `tokenStore.ts` (D14)? *Sugerencia: sí; es la forma de no perder la garantía.*

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

> Estos son los tasks que el `apply` de C-26 debería crear; **no** se crea `tasks.md` en este explore ni la carpeta del change.

0. **Precondición**: verificar GATE 16 (C-25 implementado y archivado; C-19 archivado) y que `frontend/` existe, con `npm run test:run`, `npm run typecheck` y `npm run lint` en verde. Archivar `baseline-C-26.txt` y `precondicion-C-26.txt`. Leer el `design.md` de C-25 D7/C1 y confirmar la factory del cliente y la costura `setAuthProvider`.
1. **TokenStore y contrato del token** (D1/D8/D14): `TokenStore` con `createSessionTokenStore` (fallback a memoria) y `createMemoryTokenStore`; clave `turnos.auth.accessToken`; tests de set/get/clear, sesión por pestaña y fallback; ajustar el guardián de C-25 con allowlist; RED archivado.
2. **API de auth** (D8/D9/D10): `login` y `fetchMe` sobre el cliente de C-25; `login` sin `Authorization`; tests con `fetch` real y `new Response(...)` para `200`, `401` de credenciales, `400`, `401` de `/me`, red y `5xx`; verificar header `Bearer` solo con token. RED archivado.
3. **Contexto y arranque de sesión** (D3): `AuthProvider`/`useAuth` con `checking`/`authenticated`/`anonymous`, `lastEvent`, `login`, `logout`; `/me` al montar; `LoadingState`; error de red con reintento; `401` limpia. Tests con store y cliente inyectados. RED archivado.
4. **Rutas y guards** (D4): exportar `routes`; `PublicOnlyRoute`, `RequireAuth`, `AppShell` con `Outlet`, `/`, `*`; `safeInternalPath`; `createMemoryRouter` en tests; `from` y `expired`; no parpadeo. RED archivado.
5. **Pantalla de login** (D6): `LoginPage`/`LoginForm` con usuario, contraseña, labels, `autocomplete`, validación de vacíos, error genérico `role="alert"`, `aria-busy`, foco inicial, foco visible, responsive y tokens de C-25; tests con `user-event`. RED archivado.
6. **Menú y `403`** (D5/D9): `menuFor(role)` y `can`; shell con header/menú; ítems futuros `disabled`/“Próximamente” (P4); `403` muestra `violations` sin limpiar token; tests de los tres roles y del `403`. RED archivado.
7. **Logout** (D7): botón accesible; limpia token, usuario y cachés; `setAuthProvider(null)`; redirige a `/login` con `replace`; no llama al backend; tests. RED archivado.
8. **Verificación y evidencias** (D10/D11): `red-C-26/`, `vitest-C-26.txt`, `tsc-C-26.txt`, `eslint-C-26.txt`, `mutaciones-C-26.py`/`.txt`, `trazabilidad-C-26.py`/`.txt`, `verify-C-26.md`; probar login real contra el backend con seed ficticio y `VITE_API_URL=http://localhost:8000/api`; confirmar que no se tocó `backend/`, specs, KB, `CHANGES.md` ni `.env`; `git diff --check`; no commit.

---

## 6. Resumen de recomendaciones (una línea cada una)

- **D1**: `sessionStorage` detrás de `TokenStore` (con espejo en memoria y fallback), por pestaña; sin `localStorage`, sin cookie y sin “recordarme”.
- **D2**: `401` protegido → limpiar sesión y volver al login con `from` validado y mensaje de vencimiento; el `401` del login es error de formulario y no redirige.
- **D3**: `AuthProvider` con `checking`/`authenticated`/`anonymous`, `/me` al arrancar, `LoadingState` mientras se verifica y reintento (no logout) ante error de red.
- **D4**: guards con `<RequireAuth>`/`<PublicOnlyRoute>` y `<Outlet>`, `/login`, `/` y `*`; `from` en `location.state` y `safeInternalPath`.
- **D5**: rol desde `/me`; `menuFor`/`can` solo para visibilidad; matriz RBAC completa; la API sigue decidiendo con `403`.
- **D6**: login accesible y prolijo con usuario/contraseña, error genérico del backend, `aria-busy`, foco y AA; sin enumerar usuarios.
- **D7**: logout solo en el cliente (token, usuario y cachés), sin endpoint de revocación; el token sigue válido hasta `exp` y se documenta.
- **D8**: módulo `features/auth` con `TokenStore` inyectado, `authApi`, contexto y guards; `setAuthProvider` en el wiring y el cliente nunca toca `sessionStorage`.
- **D9**: mapeo por situación: `401` de login genérico, `400` de validación, `401` protegido = sesión, `403` muestra `violations`, red/`5xx` reintento; solo `401` limpia el token.
- **D10**: tests con `fetch` inyectado y `Response` real, `TokenStore` en memoria/`sessionStorage` real y `createMemoryRouter`; prohibido `vi.mock`/`vi.spyOn`/`vi.stubGlobal`/`vi.fn`/MSW; cubre login, `/me`, `401`, guards, menú, `403` y logout.
- **D11**: `mutaciones-C-26.py` con el detector de invalidez de C-23 adaptado a Vitest (solo falla por aserción propia), SHA-256 y restauración; `trazabilidad-C-26.py` desde el spec.
- **D12**: C-26 no hace cambio de contraseña, ABM de usuarios, refresh, revocación, MFA, cookies/CSRF ni pantallas de negocio.
- **D13**: sin variables ni secretos nuevos; Bearer en header, sin cookies/`credentials`; no se toca `backend/`; cookie `HttpOnly` queda como extensión futura.
- **D14**: el guardián de C-25 pasa a allowlist de `tokenStore.ts`; C-26 agrega su test de que el storage está confinado.

---

## 7. Estado del repo al cierre del explore

| Ítem | Resultado |
|------|-----------|
| `frontend/` | **no existe** |
| C-25 | **propuesto, sin implementar** (`openspec list` lo muestra `in-progress`, 0/22 tasks) |
| C-24 | **en curso** en `backend/` por otro agente; no se tomó como contrato |
| C-19 | archivado; spec de autenticación vigente |
| `openspec list --json` | `frontend-base-react-vite` y `api-consulta-de-agenda` en progreso |
| Archivos creados por este explore | **solo** `docs/evidencias/explore-C-26.md` |

`git status --short` al cierre (los cambios de `backend/` y `docs/evidencias/` que aparecen son preexistentes de otros agentes; este explore no los tocó):

```
 M docs/evidencias/matriz-C-19.py
 M docs/evidencias/trazabilidad-C-19.py
 M docs/evidencias/trazabilidad-C-20.py
 M docs/evidencias/trazabilidad-C-21.py
 M docs/evidencias/trazabilidad-C-22.py
 M docs/evidencias/trazabilidad-C-23.py
?? docs/evidencias/baseline-C-24.txt
?? docs/evidencias/explore-C-26.md
?? docs/evidencias/precondicion-C-24.txt
```
