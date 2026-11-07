# Proposal

## Why

C-25 es la base del frontend: Vite + React 18 + TypeScript `strict` montado sobre la API ya probada por C-20..C-24. Hoy no existe `frontend/`, así que no hay forma de construir login, agenda ni pantallas de negocio. C-25 destraba el GATE 15 y habilita C-26..C-33 con un andamiaje reproducible, un sistema de diseño mínimo, un cliente de API tipado y el servicio `frontend` en Docker Compose.

## What Changes

- **Andamiaje y tooling**: `frontend/` con Vite 5, React 18, TypeScript 5 `strict`, npm con `package-lock.json` versionado, ESLint, `engines.node >= 20` y scripts `dev`, `build`, `preview`, `test`, `test:run`, `typecheck`, `lint`.
- **Tokens y paleta de 5 estados AA**: CSS custom properties (`tokens.css`), CSS Modules, system font stack, escala de espaciado y tipografía, y el mapa `APPOINTMENT_STATUS_TOKENS` con `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`.
- **Componentes base**: `LoadingState`, `EmptyState`, `ErrorState`, `StatusBadge` y `PageShell` presentacionales, sin fetch.
- **Cliente de API tipado**: wrapper sobre `fetch` inyectado por parámetro (C1), base `VITE_API_URL`, resultado discriminado `{ ok }`, modelado de las cuatro formas de error (`400 {errors}`, `401 {code,message}`, `403/409/422 {violations}`, `404 {code,message}`, `unknown`) y `getApiErrorMessages` que devuelve los mensajes del dominio tal cual.
- **Costura de token para C-26**: `setAuthProvider({ getToken })` por defecto nula; si hay provider agrega `Authorization: Bearer`; C-25 no guarda ni lee el token.
- **Router mínimo + HomePage**: React Router 6 con `createBrowserRouter`, ruta `/` y ruta `*` de no encontrada.
- **Docker Compose**: `frontend/Dockerfile` de desarrollo (`node:24-alpine`, `npm ci`, `npm run dev -- --host 0.0.0.0`), servicio `frontend` en el puerto `5173` con HMR en Windows y `VITE_API_URL` para el navegador.
- **Tests y evidencias**: Vitest + Testing Library + `user-event` + `jest-dom` sobre jsdom, salidas RED, mutaciones, trazabilidad, `verify-C-25.md` y `versiones-C-25.txt`.

## Capabilities

### New Capabilities

- `frontend-foundation`: andamiaje Vite/React/TS strict, tokens y paleta de estados, componentes base de carga/vacío/error y `StatusBadge`, cliente de API con las cuatro formas de error y `fetch` inyectado, punto de enganche del token para C-26 y servicio `frontend` en Docker Compose.

### Modified Capabilities

- Ninguna. C-25 no modifica specs existentes: agrega una capacidad nueva y no toca el contrato de la API, el dominio, las migraciones ni la matriz RBAC.

## Impact

- **Código nuevo**: todo bajo `frontend/` (`package.json`, `package-lock.json`, `tsconfig.json`, `tsconfig.node.json`, `vite.config.ts`, `index.html`, `src/`, `Dockerfile`) y los tests de componentes y del cliente.
- **Código modificado**: `docker-compose.yml`, solo para agregar el servicio `frontend`; no se tocan los servicios `postgres`, `redis` ni `backend`.
- **Sin cambios**: `backend/`, `.env.example` (ya tiene `VITE_API_URL` y `CORS_ORIGIN`), dominio, migraciones de Alembic, `openspec/specs/`, `CHANGES.md` y la base de conocimiento.
- **Precondición**: C-22 (`api-dar-turno`), C-23 (`api-ciclo-de-vida-del-turno`) y C-24 (`api-consulta-de-agenda`) archivados y verdes antes del apply (GATE 15). Si falta alguno, el apply se detiene.
- **Governance**: BAJO; la decisión de dónde se guarda el token queda para C-26 (ALTO) y C-25 solo deja la costura.
