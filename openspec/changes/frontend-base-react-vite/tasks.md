# Tasks

> **Regla para todas las tareas de los grupos 1 a 6: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-25/<tarea>.txt`. Desde `frontend/`: `npm run test:run -- <archivo> > ../docs/evidencias/red-C-25/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-25/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> **Regla C1 (sin mocks ni reemplazos globales).** Prohibido en los tests del front: `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. El cliente de API recibe la función `fetch` **por parámetro** y los tests le pasan una función real que devuelve `new Response(...)`. Es el equivalente de la regla "sin mock, patch ni monkeypatch" del backend.
>
> Sin `any` explícito ni `@ts-ignore`/`@ts-expect-error`. Solo datos ficticios (nombres tipo "Dra. Laura Quiroga" y "Ana Pérez", ids de ejemplo). `tsc --noEmit` y ESLint son obligatorios. No se commitea. Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano.

## 0. Precondiciones y andamiaje

- [x] 0.1 Verificar que C-22 (`api-dar-turno`), C-23 (`api-ciclo-de-vida-del-turno`) y C-24 (`api-consulta-de-agenda`) están archivados y verdes (GATE 15). Redirigir a `docs/evidencias/precondicion-C-25.txt` la salida de `openspec list` y de `ls openspec/changes/archive`. **Si falta alguno, detenerse** (D1, C2).
- [x] 0.2 Andamiaje como **excepción documentada** al ciclo rojo-verde (D2, D4, D5, D12): crear `frontend/package.json` con las majors de D1 y los scripts `dev`, `build`, `preview`, `test`, `test:run`, `typecheck`, `lint`; `package-lock.json`; `tsconfig.json` con `strict`, `noUncheckedIndexedAccess` y `verbatimModuleSyntax`; `tsconfig.node.json`; `vite.config.ts` con `@vitejs/plugin-react`, Vitest/jsdom, `envDir: ".."` y `server.watch.usePolling`; `index.html`; `src/main.tsx`; `src/App.tsx`; `src/vite-env.d.ts`; `src/test/setup.ts` con `@testing-library/jest-dom`; ESLint flat config; `.gitignore` con `node_modules` y `dist`. Instalar las últimas versiones de las majors elegidas, fijarlas exactas y generar `npm ls --depth=0 > ../docs/evidencias/versiones-C-25.txt` (C2). Verificar `npm run test:run`, `npm run typecheck` y `npm run lint` con un smoke trivial en `src/test/smoke.test.tsx`.

## 1. Tokens y estilos base

- [x] 1.1 Test en `src/shared/styles/appointmentStatusTokens.test.ts` del mapa `APPOINTMENT_STATUS_TOKENS`: las cinco claves `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado` devuelven `text`, `background` y `border`, y ninguna devuelve `undefined` (D6, D15). Implementar el mapa y los tipos en `src/shared/styles/appointmentStatusTokens.ts`.
- [x] 1.2 Test en `src/shared/styles/tokens.test.ts` de la escala de espaciado 4/8/12/16/24/32/48 px, la tipografía 12/14/16/20/24/32 px, el system font stack y el foco visible con `:focus-visible` y `--color-focus`. Implementar `src/shared/styles/tokens.css` y el reset mínimo en `src/shared/styles/reset.css` (D6). Documentar los pares de la paleta para la tabla de contraste AA de `verify-C-25.md` (D6, D16).

## 2. StatusBadge

- [x] 2.1 Test en `src/shared/components/StatusBadge.test.tsx` con un caso por estado (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`): cada uno muestra el texto en español y aplica la variante/clase esperada (D6, D10, D15). Implementar `src/shared/components/StatusBadge.tsx` y `StatusBadge.module.css` usando `APPOINTMENT_STATUS_TOKENS`, con datos ficticios.

## 3. Estados base de carga, vacío y error

- [x] 3.1 Test en `src/shared/components/LoadingState.test.tsx`: renderiza un elemento con `role="status"` y el texto "Cargando..." (D10, D15). Implementar `src/shared/components/LoadingState.tsx` y `LoadingState.module.css`.
- [x] 3.2 Test en `src/shared/components/EmptyState.test.tsx`: con título, descripción y acción muestra el botón; sin acción no muestra ningún botón (D10, D15). Implementar `src/shared/components/EmptyState.tsx` y `EmptyState.module.css`.
- [x] 3.3 Test en `src/shared/components/ErrorState.test.tsx`: `role="alert"`, un mensaje y varios mensajes en la lista, y reintento opcional; incluir el caso 409 con `violations: [{ code: "PROFESSIONAL_OVERLAP", message: "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1)." }]` y verificar que el mensaje se muestra exactamente, sin reformular (D9, D10, D15). Implementar `src/shared/components/ErrorState.tsx` y `ErrorState.module.css`.
- [x] 3.4 Test en `src/shared/components/PageShell.test.tsx`: envuelve header, main y footer con semántica accesible y renderiza sus hijos (D10, D15). Implementar `src/shared/components/PageShell.tsx` y `PageShell.module.css`.

## 4. Cliente de API y errores

- [x] 4.1 Test en `src/shared/api/client.test.ts` del resultado discriminado y las cuatro formas de error, inyectando `fetch` por parámetro con funciones reales que devuelven `new Response(...)` (D7, D8, D9, C1): éxito 200; `400 {errors:[{field,type,message}]}`; `401 {code,message}`; `403/409/422 {violations}` con `PROFESSIONAL_OVERLAP` y el mensaje exacto; `404 {code,message}`; y `unknown` (status 500 con texto crudo). Implementar `src/shared/api/client.ts` y los tipos en `src/shared/api/types.ts`.
- [x] 4.2 Test en `src/shared/api/errors.test.ts` de `getApiErrorMessages`: devuelve `errors[].message` (400), `violations[].message` (403/409/422) y `message` (401/404) en orden, tal cual, sin traducir (D9, D15). Implementar `src/shared/api/errors.ts`.
- [x] 4.3 Test en `src/shared/api/auth.test.ts` de la costura `setAuthProvider({ getToken })`: sin provider no hay header `Authorization`; con provider el header es `Bearer <token>`; el código de C-25 no usa `localStorage`, `sessionStorage` ni cookies para token (D7, D14, C1). Implementar el provider nulo y su integración en `src/shared/api/client.ts`. Verificar que el `fetch` inyectado en los tests es una función real con `new Response(...)`.

## 5. Router y HomePage

- [x] 5.1 Test de humo en `src/App.test.tsx`: monta `App` con el router, renderiza el `HomePage` de bienvenida y la ruta desconocida muestra la página de no encontrada, sin lanzar (D3, D15). Implementar `src/App.tsx` con `createBrowserRouter`, la ruta `/`, la ruta `*` y `src/pages/HomePage.tsx`, y conectar `src/main.tsx`.

## 6. Docker Compose

- [x] 6.1 Crear `frontend/Dockerfile` de desarrollo con `node:24-alpine`, `npm ci`, `EXPOSE 5173` y `CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]`, y agregar el servicio `frontend` a `docker-compose.yml` con puerto `5173`, `env_file: .env`, `VITE_API_URL`, volúmenes `./frontend:/app` + `/app/node_modules` anónimo, `depends_on: backend` y polling para Windows (D11, D13). No tocar los servicios `postgres`, `redis` ni `backend`, ni `backend/`, ni `.env.example`. Verificar que `VITE_API_URL` del navegador sea `http://localhost:8000/api` y redirigir la prueba a `docs/evidencias/docker-C-25.txt`.

## 7. Verificación y evidencias

- [x] 7.1 `npm run typecheck > ../docs/evidencias/tsc-C-25.txt 2>&1` desde `frontend/`, sin errores (D5).
- [x] 7.2 `npm run lint > ../docs/evidencias/eslint-C-25.txt 2>&1` desde `frontend/`, sin warnings (D5).
- [x] 7.3 `npm run test:run > ../docs/evidencias/vitest-C-25.txt 2>&1` desde `frontend/`, con todos los tests en verde (D5, D15).
- [x] 7.4 `docs/evidencias/mutaciones-C-25.py`: **una mutación por cada test nuevo**, siempre en código de producción de `frontend/src`, corriendo Vitest solo para ese test (`npm run test:run -- <archivo>`), abortando si el texto original no aparece exactamente una vez y restaurando en un `finally`; salida cruda a `mutaciones-C-25.txt`. Ninguna mutación sobrevive (D5, D16).
- [x] 7.5 `docs/evidencias/trazabilidad-C-25.py`: cada escenario de `specs/frontend-foundation/spec.md` mapeado a un test, comprobado con la lista de tests de Vitest; salida a `trazabilidad-C-25.txt` terminada en "28 escenarios, 0 problemas" (D5, D16).
- [x] 7.6 `docs/evidencias/docker-C-25.txt`: `docker compose` levanta `frontend` en 5173 y el HMR ve un cambio de archivo en Windows (D11, D16).
- [x] 7.7 `docs/evidencias/verify-C-25.md` con la tabla de contraste de los 5 estados y referencias a cada `.txt` (D6, D16).
- [x] 7.8 `openspec validate frontend-base-react-vite --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-25.txt` (D16).
