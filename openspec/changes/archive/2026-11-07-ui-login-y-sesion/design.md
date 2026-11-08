# Design — C-26 `ui-login-y-sesion`

## Context

C-26 implementa login, sesión, rutas protegidas, menú por rol y logout sobre la base de C-25 y la autenticación de C-19. Parte de `docs/evidencias/explore-C-26.md`; la autora aceptó **D1–D14** y las sugerencias **P1–P10**. Governance **ALTO**: la decisión de dónde se guarda el token se resuelve acá antes de escribir código.

C-25 está **propuesto pero no implementado** (`frontend/` no existe). Su `design.md` es el contrato: cliente con `fetch` inyectado (D7), costura `setAuthProvider({ getToken })` (D7) y regla **C1** (prohibido `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global). El apply de C-26 verifica que C-25 haya respetado ese contrato.

La API es la única autoridad: `POST /api/auth/login` responde exactamente `accessToken` y `tokenType: "bearer"`; `GET /api/auth/me` responde exactamente `id`, `username`, `displayName`, `role` y `professionalId`; el `401` de credenciales es `{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }` y el de sesión es `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }`. El login **no** devuelve `expiresIn`.

## Goals / Non-Goals

**Goals**: `TokenStore` con `sessionStorage` confinado; login accesible con error genérico; contexto `checking`/`authenticated`/`anonymous`; `/me` al arrancar con reintento ante error de red; guards con `from` validado; `401` central que limpia sesión y `403` que no; menú por rol con “Próximamente”; logout directo; header `Bearer`; tests sin mocks y evidencias RED/mutaciones/trazabilidad/manual.

**Non-Goals**: cambio de contraseña, recuperación, alta/ABM de usuarios, MFA, SSO, bloqueo por intentos, rate limiting; refresh tokens, revocación, logout del servidor; cookies, CSRF, `HttpOnly`, “recordarme” o persistencia entre reinicios; decodificar el JWT para autorizar; reglas RN-AG/RN-TU en el front; pantallas de negocio C-27..C-33; cambios en `backend/`, `openspec/specs/`, KB, `CHANGES.md`, `docker-compose.yml` o `.env`; tests E2E con navegador real.

## Decisions

### D1 — Almacenamiento del token (decisión ALTO)

**Contexto**: el backend entrega un JWT en el cuerpo y no emite cookie; hay que decidir dónde vive en el navegador, qué sobrevive a la recarga y cuánto expone a XSS.

**Decisión**: **`sessionStorage` detrás de una interfaz `TokenStore`**, clave `turnos.auth.accessToken`, con espejo en memoria y fallback a memoria si el almacenamiento lanza (modo privado o cuota). La producción usa `createSessionTokenStore()`; los tests usan `createMemoryTokenStore()` o el `sessionStorage` real de jsdom. Sobrevive la recarga (lo que más se hace en una agenda), se limpia al cerrar la pestaña y no requiere backend.

**Alternativas descartadas**: solo memoria (obliga a loguearse en cada recarga); `localStorage` (persiste entre reinicios y deja la sesión abierta en una máquina compartida); cookie `HttpOnly` (exige cambiar el login, CORS con credenciales y CSRF: es una extensión de C-19, no de C-26).

### D2 — `401` durante el uso y `401` del login

**Contexto**: el `401` significa dos cosas distintas: credenciales inválidas en el login y sesión inválida en una ruta protegida. No hay refresh.

**Decisión**: **manejo central en la capa de auth**, una sola vez. Un `401` de una request protegida descarta el token, limpia el usuario, marca `anonymous` con motivo `expired`, y el guard navega a `/login` con `replace`, `state.from` y el mensaje “La sesión venció. Iniciá sesión de nuevo.”. No se reintenta automáticamente. El `401` de `POST /api/auth/login` se excluye explícitamente: es error de formulario, no limpia sesión ni redirige.

**Alternativas descartadas**: manejo por pantalla (duplica lógica y alguna pantalla se olvida); decodificar `exp` para logout proactivo (el token deja de ser opaco, el reloj puede estar desfasado y no cubre usuario desactivado ni cambio de rol).

### D3 — Contexto de sesión y arranque con `/me`

**Contexto**: la UI necesita saber si hay sesión, quién es el usuario y qué rol tiene antes de renderizar el menú o redirigir.

**Decisión**: **React Context** (`AuthProvider` + `useAuth`) con `status: "checking" | "authenticated" | "anonymous"` y `lastEvent: "expired" | "manual" | null`. Al arrancar, si hay token se llama `GET /api/auth/me`; mientras tanto se muestra `LoadingState` y no se redirige. `/me` es la única fuente del usuario y del rol. Un error de red o `5xx` en `/me` **conserva** el token y muestra `ErrorState` con reintento; solo `401` limpia.

**Alternativas descartadas**: cada pantalla llama a `/me` (requests duplicadas y menú inconsistente); guardar el usuario en storage (rol y `professionalId` quedan viejos y se duplica la fuente de verdad).

### D4 — Rutas protegidas y `from` validado

**Contexto**: C-25 deja un router mínimo (`/` y `*`); C-26 necesita `/login`, proteger el resto y conservar el destino sin abrir un redirect abierto.

**Decisión**: **guards como componentes de layout con `<Outlet />`**. `/login` va en `PublicOnlyRoute`; el resto en `RequireAuth` + `AppShell`. El `from` viaja en `location.state` (no en la URL ni en storage) y se valida con `safeInternalPath`: debe empezar con `/`, no con `//`, no ser `/login` ni una URL absoluta; si no, `/`. Se exportan las `routes` separadas de `createBrowserRouter` para testear con `createMemoryRouter`.

**Alternativas descartadas**: guards en `loader` (el estado de auth es del cliente y los loaders corren antes del contexto); condicionales sin router (URLs no compartibles y back/forward roto).

### D5 — Menú por rol y `403`

**Contexto**: la UI debe mostrar un menú coherente con el rol sin duplicar la matriz RBAC ni convertirse en la autoridad.

**Decisión**: el rol sale de `user.role` de `/me`; `menuFor(role)` devuelve los ítems visibles según la matriz de KB 03. En C-26 ninguna pantalla de negocio existe todavía, así que **todos los ítems de negocio se muestran deshabilitados con “Próximamente”**; el rol solo decide cuáles aparecen. La API sigue rechazando con `401`/`403`; ocultar un botón no es seguridad. Un `403` muestra las `violations` tal cual y no limpia la sesión.

**Alternativas descartadas**: decodificar el `role` del JWT (token opaco y rol potencialmente viejo); mostrar todas las acciones y dejar que la API rechace (el `403` se vuelve la experiencia normal).

Matriz de visibilidad del menú en C-26:

| Ítem | Odontólogo | Recepción | Administrador |
|------|------------|-----------|---------------|
| Agenda | Sí | Sí | Sí |
| Turnos (dar, reprogramar, cancelar) | **No** | Sí | Sí |
| Horarios y bloqueos | Sí | Sí | Sí |
| Catálogos (profesionales, sillones, prestaciones) | Sí | Sí | Sí |
| Pacientes | Sí | Sí | Sí |
| Usuarios y roles | **No** | **No** | Sí |

### D6 — Pantalla de login

**Contexto**: el login es la primera pantalla y va en el video; debe ser accesible, clara y no filtrar qué credencial falló.

**Decisión**: tarjeta centrada sobre los tokens de C-25. Campos **Usuario** (`text`, `autocomplete="username"`, `maxLength=150`, `required`) y **Contraseña** (`password`, `autocomplete="current-password"`, `maxLength=128`, `required`), con `<label>` visible y `htmlFor`. Validación local solo de vacíos. El `401` muestra el mensaje textual del backend en `role="alert"` con `aria-live="polite"`, sin resaltar campos. Estado de envío: botón deshabilitado, “Ingresando…”, `aria-busy="true"`, sin doble submit. Foco inicial en Usuario, Enter envía, foco visible AA. **Sin “ver contraseña” y sin “recordar usuario”**; la contraseña se limpia después del intento y nunca va en la URL ni en logs.

**Alternativas descartadas**: formulario HTML sin estilos (no cumple “frontend cuidado” ni accesibilidad); librería de componentes (dependencia pesada y estética ajena a C-25).

### D7 — Logout

**Contexto**: cerrar sesión debe dejar el cliente sin token ni usuario, sin endpoint de servidor y sin dejar rastros.

**Decisión**: **logout solo en el cliente, directo y sin confirmación**. Quita la clave propia del `TokenStore` (nunca `clear()` global), deja el `authProvider` en `null`, limpia el usuario y las cachés, pasa a `anonymous` con motivo `manual` y navega a `/login` con `replace` sin conservar `from` ni mostrar “sesión vencida”. No llama al backend: el token sigue válido hasta `exp` y se documenta en `verify-C-26.md`.

**Alternativas descartadas**: endpoint de logout/revocación (no existe y excede SU-06/DD-11); solo navegar sin limpiar (el guard volvería a entrar y la sesión quedaría abierta).

### D8 — Módulo de auth y costura `setAuthProvider`

**Contexto**: C-25 deja la costura `setAuthProvider({ getToken })` pero no un módulo de auth; el cliente de transporte no debe conocer `sessionStorage`.

**Decisión**: `src/features/auth/tokenStore.ts` (interfaz + `createSessionTokenStore` + `createMemoryTokenStore`); `authApi.ts` (`login` sin `Authorization`, `fetchMe` con token); `AuthContext.tsx` (máquina de estados de D3, recibe `tokenStore` y cliente/`fetch` por props con defaults de producción); `RequireAuth.tsx`, `PublicOnlyRoute.tsx`, `safeInternalPath.ts` y `menuFor.ts`; `features/login/LoginPage.tsx` y `LoginForm.tsx`; wiring en `main.tsx`/`App.tsx`. El cliente de C-25 solo llama a `getToken`; no importa `sessionStorage` ni el módulo de auth.

**Alternativas descartadas**: todo en un solo `auth.ts` (mezcla responsabilidades y crece con C-27..C-33); que `client.ts` lea `sessionStorage` (viola la costura, esconde la decisión ALTO y mezcla capas).

### D9 — Semántica de errores de autenticación

**Contexto**: hay `400`, `401` de login, `401` de sesión, `403`, `409/422`, `404`, red y `5xx`; la UI no puede tratarlos todos igual.

**Decisión**: mapear **por situación**:

| Situación | Status | UI | ¿Descarta token? |
|-----------|--------|----|------------------|
| Credenciales inválidas en login | `401 /auth/login` | Mensaje textual genérico | No |
| Datos faltantes en login | `400 /auth/login` | Mensajes de `errors[]` o validación local | No |
| Token vencido en ruta protegida | `401` | Vuelve al login con “La sesión venció…” | **Sí** |
| `/me` del arranque con token inválido | `401` | Va al login sin mensaje de vencimiento | **Sí** |
| Rol sin permiso | `403` | Mensajes de `violations[]` tal cual | No |
| Conflicto o regla de validez | `409/422` | Mensajes de `violations[]` tal cual | No |
| No encontrado | `404` | `message` | No |
| Red caída o `5xx` | — | “No se pudo conectar…” con reintento | No |

Solo el `401` protegido limpia el token. El `403` no cierra sesión ni refresca `/me`.

**Alternativas descartadas**: mostrar el cuerpo crudo (puede filtrar JSON o detalles internos); un único mensaje genérico para todo (pierde los mensajes del dominio).

### D10 — Tests sin mocks

**Contexto**: el proyecto prohíbe mocks de colaboradores internos y C1 prohíbe `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos y MSW.

**Decisión**: `fetch` **inyectado**: los tests pasan una función real `async (input, init) => new Response(...)` que guarda `init` en un array del propio test para inspeccionar método y headers. `TokenStore` en memoria o el `sessionStorage` real de jsdom, limpiado en `afterEach`. Router con `createMemoryRouter(routes, { initialEntries })` y aserciones sobre `router.state.location`. Interacción con `@testing-library/user-event`; sin timers falsos.

**Alternativas descartadas**: MSW (prohibido por C1 y agrega setup); `vi.mock`/`vi.spyOn`/`vi.fn` (prohibidos por C1 y ocultan el comportamiento real).

### D11 — Mutaciones y trazabilidad adaptadas a Vitest

**Contexto**: C-20..C-25 tienen `mutaciones-C-XX.py` y `trazabilidad-C-XX.py`; `mutaciones-C-23.py` detecta mutaciones inválidas. El front necesita el equivalente con la salida de Vitest.

**Decisión**: `docs/evidencias/mutaciones-C-26.py` espeja la estructura de `mutaciones-C-25.py` o, si todavía no existe, de `mutaciones-C-23.py` adaptada a Vitest. Una mutación por cada test nuevo, siempre sobre `frontend/src`, comprobando que el original aparezca exactamente una vez, normalizando CRLF, abortando si el mutante no cambia el archivo, restaurando en `finally` y comparando SHA-256 al final. El **detector de inválidas** considera inválida una mutación si el fallo no viene de una afirmación del test: `ReferenceError`, `SyntaxError`, `Cannot find module`, `Failed to resolve import`, un `TypeError` del código mutado sin aserción o una guarda de producción. `trazabilidad-C-26.py` mapea cada escenario del spec a un test con `vitest list --json` y termina en “N escenarios, 0 problemas”.

**Alternativas descartadas**: StrykerJS (dependencia y configuración extra, distinto del resto del repo); no hacer mutaciones ni trazabilidad (rompe la paridad de evidencias).

### D12 — Qué NO hace C-26

**Contexto**: evitar que el login se convierta en “toda la seguridad” o invada C-27..C-33 y el backlog.

**Decisión**: alcance estricto. C-26 no hace cambio de contraseña, recuperación, alta/ABM de usuarios, MFA, SSO, bloqueo por intentos ni rate limiting; no hace refresh, revocación ni logout del servidor; no usa cookies, CSRF ni `HttpOnly`; no implementa “recordarme”; no decodifica el JWT para autorizar ni duplica RN-AG/RN-TU; no crea pantallas de negocio; no toca `backend/`, migraciones, specs existentes, KB, `CHANGES.md`, `docker-compose.yml` ni `.env`; no hace tests E2E con navegador real.

**Alternativas descartadas**: adelantar cambio de contraseña (no hay endpoint y SU-06 lo excluye); adelantar ABM de usuarios (no existe `/api/users` y suma backend y seguridad).

### D13 — Variables, CORS y frontera con el backend

**Contexto**: el login toca la seguridad; hay que confirmar que C-26 no agrega secretos ni cambia el contrato.

**Decisión**: no se agregan variables: se reutilizan `VITE_API_URL` y `CORS_ORIGIN`. El navegador llama a `http://localhost:8000/api` y el CORS ya permite `http://localhost:5173`. Se usa `Authorization: Bearer` en el header, sin cookies ni `credentials: "include"`, así que no hay CSRF que mitigar. `JWT_SECRET` nunca llega al navegador. No se usa `dangerouslySetInnerHTML` ni `eval`; una CSP `script-src 'self'` queda como mejora futura.

**Alternativas descartadas**: variables de configuración de auth (`VITE_AUTH_STORAGE`): una decisión de seguridad no debe depender de una variable pública del bundle; pasar a cookie/`HttpOnly`: es una extensión de C-19 con CORS de credenciales y CSRF.

### D14 — Convivencia con el test guardián de C-25

**Contexto**: el spec de C-25 afirma que ningún archivo de `frontend/src` accede a `localStorage`, `sessionStorage` ni cookies para el token. C-26 agrega `sessionStorage` a propósito.

**Decisión**: **acotar el guardián con una allowlist**: se permite `sessionStorage` **solo** en `src/features/auth/tokenStore.ts` (y su test) y se sigue prohibiendo `localStorage`, cookies y cualquier otro acceso en el resto de `frontend/src`. C-26 agrega su propio test de confinamiento y documenta el ajuste en `verify-C-26.md`. No se borra el escenario de C-25.

**Alternativas descartadas**: borrar el test de C-25 (pierde la garantía); poner el storage fuera de `frontend/src` (artificial y rompe la estructura de la feature).

## Seguridad

### XSS y `sessionStorage`

El token queda legible por JavaScript del mismo origen, así que un XSS podría exfiltrarlo. Se acota el riesgo con: dependencias mínimas, `package-lock.json` versionado, sin `dangerouslySetInnerHTML`, sin `eval`, sin scripts de terceros, token de vida corta (`JWT_EXPIRES_MIN`) y `sessionStorage` por pestaña (no persiste al cerrar el navegador). La CSP `script-src 'self'` queda como mejora futura documentada. El riesgo residual se acepta y se registra en `verify-C-26.md`.

### Qué no se guarda

- No se guarda el usuario, el rol, el `professionalId`, la contraseña ni el último usuario en storage: el rol y el usuario salen siempre de `/me`.
- No se guarda el token en `localStorage`, en cookies, en la URL, en el historial ni en el state del router.
- No se implementa “recordarme” ni persistencia entre reinicios del navegador.

### Qué no se loguea

- No se loguean credenciales, contraseñas, tokens, cuerpos de respuesta ni headers `Authorization`.
- Los mensajes de error de la UI no muestran el token ni JSON crudo.
- El formulario usa `POST` conceptual (nunca `GET`) y no pone usuario ni contraseña en la URL.

### Por qué no cookies

El backend actual devuelve `accessToken` en el JSON y no emite cookie. Una cookie puesta por JavaScript no es `HttpOnly` y no aporta sobre `sessionStorage`; una cookie `HttpOnly` real exige cambiar el login, habilitar CORS con credenciales y agregar protección CSRF, lo que toca C-19 y excede C-26. Queda como extensión futura.

## Reglas duras del frontend (heredadas de C-25)

- **Sin mocks ni reemplazos globales (C1)**: prohibido `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. `fetch` inyectado con `new Response(...)` real.
- **Sin `any` explícito ni `@ts-ignore`/`@ts-expect-error`**: `unknown` + narrowing; `tsconfig` en `strict`.
- **Mensajes del dominio tal cual**: `getApiErrorMessages` no traduce ni reformula.
- **Solo datos ficticios**: usuarios del seed y `<contraseña de prueba>`; nunca contraseñas reales.
- **Storage confinado**: `sessionStorage` solo en `tokenStore.ts`.
- **No commitear**: sin `git add`, `commit`, `push`, `restore`, `checkout` ni `stash`.
- **Calidad obligatoria**: `tsc --noEmit` sin errores y ESLint sin warnings antes de cerrar.

## Risks

| Riesgo | Mitigación |
|--------|------------|
| XSS lee el token de `sessionStorage` y lo exfiltra | Sin `dangerouslySetInnerHTML` ni scripts de terceros, dependencias mínimas, token corto, CSP futura; riesgo residual documentado. |
| El `401` del login se confunde con sesión vencida y genera un bucle | El manejador global excluye `POST /api/auth/login`; el login fallido es error de formulario; test explícito. |
| Open redirect con `from=//evil.com` o una URL absoluta | `safeInternalPath` solo acepta `/...`, rechaza `//`, URLs absolutas y `/login`; tests. |
| Un `401` en segundo plano saca al usuario de un formulario | Se conserva `from` y se muestra el mensaje; C-29+ puede agregar borradores. |
| Error de red en `/me` se trata como logout y se pierde la sesión | Solo `401` limpia; red/`5xx` conserva el token y ofrece reintento; test. |
| Ocultar botones se confunde con autorización | `menuFor` es solo visibilidad; la API sigue rechazando con `403`; test de `403`. |
| El rol del menú queda viejo si cambia en la base | El rol sale de `/me`; el request siguiente da `401` y se limpia la sesión; no se decodifica el JWT. |
| Logout no invalida el token en el servidor | Trade-off de SU-06; token corto; se documenta que un token robado vive hasta `exp`. |
| Token o contraseña en logs, URL o mensajes | No se loguean; no van en la URL; el cliente no muestra cuerpos crudos; `Cache-Control: no-store` ya viene del backend. |
| `sessionStorage` lanza en modo privado o por cuota | El adaptador cae a memoria y lo informa en `verify-C-26.md`; el login sigue funcionando en esa pestaña. |
| El test guardián de C-25 se rompe o se borra | D14: allowlist de un solo archivo y test propio de C-26. |
| Tests con mocks ocultan fallos | C1: `fetch` inyectado, `TokenStore` en memoria, router en memoria; mutaciones y trazabilidad. |
| C-26 toca `backend/` y choca con C-24 en curso | D12/D13: C-26 solo escribe bajo `frontend/` y evidencias; no toca `backend/`. |
| `frontend/` no existe porque C-25 no está archivado | Task 0.1 verifica GATE 16 y se detiene si C-25 no está archivado. |
