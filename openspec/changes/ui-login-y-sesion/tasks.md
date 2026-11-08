# Tasks

> **Regla para todas las tareas de los grupos 1 a 7: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-26/<tarea>.txt`. Desde `frontend/`: `npm run test:run -- <archivo> > ../docs/evidencias/red-C-26/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-26/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> **Regla C1 (sin mocks ni reemplazos globales).** Prohibido en los tests del front: `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. El cliente de API recibe la función `fetch` **por parámetro** y los tests le pasan una función real que devuelve `new Response(...)`. Es el equivalente de la regla "sin mock, patch ni monkeypatch" del backend.
>
> Sin `any` explícito ni `@ts-ignore`/`@ts-expect-error`. Solo datos ficticios: usuarios del seed (`administrador`, `recepcion`, `odontologo`), `<contraseña de prueba>` y nombres tipo "Dra. Laura Quiroga". `tsc --noEmit` y ESLint son obligatorios. No se commitea. Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano.

## 0. Precondiciones

- [x] 0.1 Verificar GATE 16: C-25 (`frontend-base-react-vite`) **implementado, verde y ARCHIVADO** y C-19 archivado. Redirigir a `docs/evidencias/precondicion-C-26.txt` la salida de `openspec list` y de `ls openspec/changes/archive`. Confirmar que `frontend/` existe y que C-25 respetó el cliente con `fetch` inyectado, la costura `setAuthProvider({ getToken })` y la regla C1. **Si C-25 no está archivado o `frontend/` no existe, detenerse** (D12, D13).
- [x] 0.2 Línea de base desde `frontend/`: `npm run test:run`, `npm run typecheck` y `npm run lint`, redirigidos a `docs/evidencias/baseline-C-26.txt`. Todo tiene que estar en verde.

## 1. TokenStore y confinamiento del storage

- [x] 1.1 Test en `src/features/auth/tokenStore.test.ts` de `TokenStore` (D1, D8): `setToken`/`getToken`/`clear` con la clave `turnos.auth.accessToken`; el valor sobrevive a una nueva lectura; `clear` borra la clave; con un `sessionStorage` cuyo `setItem` lanza, el adaptador cae a memoria sin propagar la excepción y `getToken` devuelve el token; `createMemoryTokenStore` aísla cada test. Implementar `src/features/auth/tokenStore.ts` con `TokenStore`, `createSessionTokenStore` y `createMemoryTokenStore`. RED archivado.
- [x] 1.2 Test guardián en `src/features/auth/storageGuard.test.ts` de que el único acceso a `sessionStorage` en `frontend/src` está en `src/features/auth/tokenStore.ts`, que no hay `localStorage` ni cookies y que el cliente de API no importa `sessionStorage` (D14). Ajustar el test guardián de C-25 con la allowlist de `tokenStore.ts` sin borrar el escenario. RED archivado.

## 2. API de autenticación y header Bearer

- [x] 2.1 Tests en `src/features/auth/authApi.test.ts` de `login` y `fetchMe` con `fetch` inyectado y `new Response(...)` real (D8, D9, D10, C1): `login` envía `POST /api/auth/login` con `{ "username": "recepcion", "password": "<contraseña de prueba>" }`; `200 { "accessToken": "token-ficticio-123", "tokenType": "bearer" }` devuelve el token; `401 { "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }`, `400 { "errors": [...] }`, `401` de `/me` con `INVALID_TOKEN`, error de red y `5xx`; el login no manda `Authorization` aunque el store tenga `"token-viejo"`; `fetchMe` manda `Authorization: Bearer token-ficticio-123`. Implementar `src/features/auth/authApi.ts` sobre el cliente de C-25. RED archivado.

## 3. Contexto y arranque de sesión

- [x] 3.1 Tests en `src/features/auth/AuthContext.test.tsx` de la máquina `checking`/`authenticated`/`anonymous` (D3): con token y `/me` pendiente se muestra `LoadingState` y no se redirige; `/me` `200` deja `authenticated` con `displayName` "Dra. Laura Quiroga", `role` "odontologo" y `professionalId` `00000000-0000-0000-0000-000000000001`; `/me` `401` limpia el token y queda `anonymous` sin mensaje de vencimiento; error de red en `/me` conserva el token, muestra `ErrorState` con reintento y al reintentar `200` queda `authenticated`; `lastEvent` `"expired"` y `"manual"`. Implementar `src/features/auth/AuthContext.tsx` con `AuthProvider`/`useAuth`, recibiendo `tokenStore` y el cliente/`fetch` por props. RED archivado.

## 4. Rutas y guards

- [x] 4.1 Test en `src/features/auth/safeInternalPath.test.ts` (D4): acepta `/agenda?date=2026-11-07`; rechaza `"//evil.com"`, `"https://evil.example"` y `"/login"` devolviendo `/`. Implementar `src/features/auth/safeInternalPath.ts`. RED archivado.
- [x] 4.2 Tests en `src/App.test.tsx` con `createMemoryRouter(routes, { initialEntries })` (D4): sin sesión, `/agenda?date=2026-11-07` redirige a `/login` con `state.from` y `replace`; con sesión, `/login` redirige al `from` válido; con token y `/me` pendiente, `/login` muestra `LoadingState` y no el formulario. Implementar `RequireAuth.tsx`, `PublicOnlyRoute.tsx`, la exportación de `routes` y el wiring en `App.tsx`/`main.tsx`. RED archivado.

## 5. Pantalla de login

- [x] 5.1 Tests en `src/features/login/LoginPage.test.tsx` con `user-event` (D6): login correcto de `administrador` guarda el token, llama a `/me` y redirige a `/`; login correcto de `recepcion` y de `odontologo` deja el usuario de `/me`; credenciales inválidas muestran exactamente "Usuario o contraseña incorrectos." en `role="alert"`, no guardan token, no redirigen y vacían la contraseña; envío en curso deshabilita el botón con "Ingresando…" y `aria-busy="true"` sin doble submit; etiquetas "Usuario"/"Contraseña", `autocomplete`, Enter envía, error con `aria-live`, foco visible; no hay "ver contraseña" ni "recordar usuario". Implementar `LoginPage.tsx`, `LoginForm.tsx` y `LoginPage.module.css` con los tokens de C-25. RED archivado.

## 6. Menú por rol y 403

- [x] 6.1 Test en `src/features/auth/menuFor.test.ts` (D5): `administrador` ve "Agenda", "Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes" y "Usuarios y roles"; `recepcion` no ve "Usuarios y roles"; `odontologo` no ve "Turnos" ni "Usuarios y roles"; todos los ítems de pantallas futuras están deshabilitados con "Próximamente". Implementar `src/features/auth/menuFor.ts`. RED archivado.
- [x] 6.2 Tests en `src/shared/components/AppShell.test.tsx` y `src/features/auth/AuthContext.test.tsx` (D5, D9): el shell renderiza el menú del rol; un `403` con `{ "violations": [{ "code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para dar turnos." }] }` muestra el mensaje exacto, conserva el token, sigue `authenticated` y no vuelve a llamar a `/me`. Implementar el menú en `AppShell` y el manejo de `403` en la capa de auth/errores. RED archivado.

## 7. Logout

- [x] 7.1 Test en `src/features/auth/Logout.test.tsx` (D7): desde una sesión `authenticated` de `recepcion`, la acción "Cerrar sesión" descarta token y usuario, deja `anonymous` con motivo `"manual"`, navega a `/login` con `replace`, no pide confirmación, no llama a ningún endpoint de logout y no muestra "La sesión venció. Iniciá sesión de nuevo.". Implementar el logout en `AuthContext` y el botón accesible en `AppShell`. RED archivado.

## 8. Verificación y evidencias

- [x] 8.1 `npm run typecheck > ../docs/evidencias/tsc-C-26.txt 2>&1` desde `frontend/`, sin errores.
- [x] 8.2 `npm run lint > ../docs/evidencias/eslint-C-26.txt 2>&1` desde `frontend/`, sin warnings.
- [x] 8.3 `npm run test:run > ../docs/evidencias/vitest-C-26.txt 2>&1` desde `frontend/`, con todos los tests en verde.
- [x] 8.4 `docs/evidencias/mutaciones-C-26.py`: copiar la estructura de `mutaciones-C-25.py` o, si todavía no existe, adaptar `mutaciones-C-23.py` a la salida de Vitest. **Una mutación por cada test nuevo**, siempre sobre código de producción de `frontend/src`, corriendo Vitest solo para ese test (`npm run test:run -- <archivo>`). Comprobar que el texto original aparezca exactamente una vez, **normalizar CRLF**, **abortar si el mutante no cambia el archivo**, restaurar en un `finally` y comparar SHA-256 al final. **Detector de mutaciones inválidas**: el fallo tiene que venir de una afirmación del test, no de un `ReferenceError`/`TypeError` del mutante ni de una guarda de producción; una mutación inválida no cuenta como detectada. El resumen tiene que terminar en "mutaciones inválidas: 0" y la salida cruda va a `mutaciones-C-26.txt`. Ninguna mutación sobrevive (D11).
- [x] 8.5 `docs/evidencias/trazabilidad-C-26.py`: cada escenario de `specs/frontend-auth-session/spec.md` mapeado a un test, comprobado con `vitest list --json` (o el reporte JSON de Vitest); salida a `trazabilidad-C-26.txt` terminada en "N escenarios, 0 problemas" (D11).
- [x] 8.6 Verificación manual con el backend real, redirigida a `docs/evidencias/manual-C-26.txt`: con `VITE_API_URL=http://localhost:8000/api`, iniciar sesión con los tres usuarios del seed (`administrador`, `recepcion`, `odontologo`), verificar el menú de cada rol, forzar un `401` venciendo o borrando el token y comprobar la vuelta a `/login` con "La sesión venció. Iniciá sesión de nuevo.", y ejecutar el logout directo. No tocar `.env`.
- [x] 8.7 `docs/evidencias/verify-C-26.md` con referencias a cada `.txt`, la nota de seguridad (XSS y `sessionStorage`, qué no se loguea, qué no se guarda, por qué no cookies), el ajuste del guardián de C-25 (D14) y la confirmación de que no se tocó `backend/`, `openspec/specs/`, KB, `CHANGES.md`, `.env` ni `docker-compose.yml`.
- [x] 8.8 `openspec validate ui-login-y-sesion --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-26.txt`.
