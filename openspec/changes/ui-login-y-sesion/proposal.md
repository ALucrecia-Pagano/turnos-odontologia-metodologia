# Proposal

## Why

C-26 entrega el login y la sesión del frontend sobre la API de C-19 y la base de C-25. Sin login no hay forma de obtener el token, proteger las rutas, mostrar el menú por rol ni cerrar sesión; sin esa pieza, C-27..C-33 no pueden consumir la API autenticada. C-26 es governance ALTO porque decide dónde se guarda el token en el cliente.

## What Changes

- **TokenStore**: el token vive detrás de una interfaz `TokenStore`; la implementación de producción usa `sessionStorage` bajo `turnos.auth.accessToken`, con fallback a memoria si el almacenamiento falla. Es el **único** archivo de `frontend/src` que toca `sessionStorage`; no hay `localStorage`, cookies ni “recordarme”.
- **Login**: pantalla con usuario y contraseña contra `POST /api/auth/login`; éxito guarda el token y consulta `/me`; credenciales inválidas muestran el mensaje genérico del backend; estado de envío, accesibilidad AA, sin “ver contraseña” ni “recordar usuario”.
- **Sesión y `/me`**: contexto con `checking`, `authenticated` y `anonymous`; al arrancar, con token, se consulta `GET /api/auth/me`; un error de red conserva el token y ofrece reintento.
- **Rutas y guards**: `/login`, `RequireAuth`, `PublicOnlyRoute` y shell protegido; redirección con `from` validado (solo rutas internas; se rechazan `//evil.com` y URLs absolutas).
- **`401` y `403`**: un `401` de una request protegida limpia la sesión y vuelve a `/login` con el mensaje de sesión vencida; el `401` del login es error de formulario y no redirige; un `403` muestra las `violations` sin limpiar la sesión ni refrescar `/me`.
- **Menú por rol**: ítems derivados del `role` de `/me` y de la matriz RBAC; los ítems de pantallas futuras se muestran deshabilitados con “Próximamente”; la API sigue siendo la que rechaza.
- **Logout**: descarta token y usuario, navega a `/login` con `replace`, sin confirmación y sin endpoint de servidor.
- **`Authorization: Bearer`**: el cliente agrega el header solo con token; el login nunca manda un token viejo.
- **Tests y evidencias**: Vitest con `fetch` inyectado y `Response` real, RED en `docs/evidencias/red-C-26/`, mutaciones y trazabilidad adaptadas a Vitest, verificación manual contra el backend y `verify-C-26.md`.
- **Guardián de C-25**: su test de “no persiste el token” se ajusta con una allowlist que permite `sessionStorage` solo en `src/features/auth/tokenStore.ts`.

## Capabilities

### New Capabilities

- `frontend-auth-session`: almacenamiento del token en el cliente, login contra la API, arranque de sesión con `/me`, rutas protegidas con redirección segura, manejo de `401` y `403`, menú por rol, logout y envío del header `Authorization: Bearer`.

### Modified Capabilities

- Ninguna. C-26 no cambia el contrato de la API ni de las specs existentes; el ajuste del test guardián de C-25 es un cambio de test dentro del apply y se documenta en `verify-C-26.md`.

## Impact

- **Código nuevo**: `frontend/src/features/auth/` (`tokenStore.ts`, `authApi.ts`, `AuthContext.tsx`, `RequireAuth.tsx`, `PublicOnlyRoute.tsx`, `safeInternalPath.ts`, `menuFor.ts`), `frontend/src/features/login/` (`LoginPage.tsx`, `LoginForm.tsx`, estilos) y el wiring en `frontend/src/App.tsx`/`main.tsx`.
- **Código modificado**: el test guardián de storage de C-25 (allowlist de un solo archivo); el shell/router de C-25 para montar `/login`, los guards y el menú.
- **Sin cambios**: `backend/`, `openspec/specs/`, `CHANGES.md`, `knowledge-base/`, `AGENTS.md`, `CLAUDE.md`, `.env`, `docker-compose.yml` y los demás changes. C-26 no agrega variables ni secretos y no migra a cookies.
- **Precondición**: C-25 implementado, verde y **ARCHIVADO** (GATE 16), con `frontend/` existente. Si no está archivado, el apply se detiene.
- **Governance**: ALTO; la decisión de almacenamiento del token queda resuelta en `design.md` (D1) antes de implementar.
