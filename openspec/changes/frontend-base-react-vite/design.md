# Design — C-25 `frontend-base-react-vite`

## Context

C-25 arranca la Fase 6 (interfaz web) sobre la API ya probada por C-20..C-24. Parte de `docs/evidencias/explore-C-25.md`; las decisiones D1–D16 y las preguntas P1–P10 son las recomendadas por el explore y aprobadas por la autora, con dos correcciones obligatorias incorporadas en este documento:

- **C1 (corrige D10)**: nada de stubbear el `fetch` global. El cliente de API recibe la función `fetch` por parámetro (inyección de dependencia), con el `fetch` del navegador por defecto. Los tests le pasan una función real que devuelve `new Response(...)`. Queda prohibido en los tests del front `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global; es el equivalente de la regla "sin mock, patch ni monkeypatch" del backend.
- **C2 (corrige D1)**: el design no fija números de versión inventados. En el apply se instalan las últimas versiones de las majors elegidas, se fijan exactas en `package.json` con `package-lock.json` versionado, y la salida de `npm ls --depth=0` se archiva en `docs/evidencias/versiones-C-25.txt`.

La base que se reutiliza: contrato HTTP con cuatro cuerpos de error (`openspec/specs/api-foundation/spec.md`), login con `accessToken` + `tokenType: "bearer"` y `/api/auth/me` (`openspec/specs/authentication-and-rbac/spec.md`), `GET /api/agenda` de C-24, `docker-compose.yml` con `postgres`, `redis` y `backend`, y `VITE_API_URL`/`CORS_ORIGIN` ya presentes en `.env.example`. C-25 no toca `backend/`.

## Goals / Non-Goals

**Goals**: crear `frontend/` con Vite + React 18 + TS `strict`; fijar estructura `features/shared/pages` y router mínimo; definir tokens y paleta de 5 estados con contraste AA; construir `LoadingState`, `EmptyState`, `ErrorState`, `StatusBadge` y `PageShell` presentacionales; escribir el cliente de API tipado con las cuatro formas de error y `fetch` inyectado; dejar la costura de token para C-26; agregar el servicio `frontend` a Docker Compose con HMR en Windows; montar Vitest + RTL + jsdom con test-first y evidencias espejo del backend.

**Non-Goals**: login, sesión y storage del token (C-26, ALTO); pantallas de agenda, turnos, catálogos o pacientes (C-27..C-33); consumo real de endpoints; estado global o librería de datos (se decide en C-27); UI kit o framework de componentes; tests E2E; SSR, i18n, PWA; cambios en `backend/`, `.env.example`, dominio, migraciones o specs existentes.

## Decisions

### D1 — Versiones y Node del contenedor (corrección C2)

**Problema**: SU-10 fija React 18 / TypeScript 5 / Vite 5, pero hoy existen majors más nuevas; hay que decidir qué se declara y con qué Node corre.

- **Opción A (recomendada)**: respetar SU-10 como contrato del TP con las majors **react 18**, **react-dom 18**, **typescript 5**, **vite 5**, `@vitejs/plugin-react` compatible, **react-router-dom 6** y Vitest + Testing Library compatibles con Vite 5 y React 18. Imagen Docker `node:24-alpine` y `engines.node >= 20`. En el apply se instalan las últimas versiones de esas majors, se fijan **exactas** en `package.json` con `package-lock.json` versionado y se archiva `npm ls --depth=0` en `docs/evidencias/versiones-C-25.txt`.
- **Opción B**: ir a lo último estable (React 19 + Vite 7). Contradice SU-10 y obliga a revalidar compatibilidad sin beneficio para el MVP. Descartada.
- **Opción C**: mezclar majors (React 18 + Vite 7). Combinación no fijada por nadie, más superficie de fallos. Descartada.
- **Decisión**: **A**. No se inventan números de versión en este documento: las majors están fijadas y las versiones exactas se capturan en el apply (C2). Node 24 es LTS y cumple el engine de Vite 5.

### D2 — Gestor de paquetes y lockfile

**Problema**: elegir npm, pnpm o yarn y decidir si el lockfile se versiona.

- **Opción A (recomendada)**: **npm** (ya instalado) con **`package-lock.json` versionado**; `npm install` en local y `npm ci` en Docker.
- **Opción B**: pnpm. Requiere instalar Corepack/pnpm en host e imagen; dependencia extra para un proyecto individual. Descartada.
- **Opción C**: yarn. Otra herramienta y otro lockfile sin ganancia. Descartada.
- **Decisión**: **A**. El lockfile nunca va a `.gitignore`; `npm ci` en el contenedor garantiza reproducibilidad.

### D3 — Estructura de carpetas y router mínimo

**Problema**: fijar la organización del código y cómo se navega entre pantallas futuras sin implementarlas.

- **Opción A (recomendada)**: estructura de KB 08 con `src/features/{agenda,appointments,configuration,login,patients}/`, `src/shared/{components,api,styles,lib}/`, `src/pages/`, `src/main.tsx` y `src/App.tsx`. **React Router 6** con `createBrowserRouter`, ruta `/` (`HomePage`) y ruta `*` de no encontrada.
- **Opción B**: React Router 7. Cambios de API/paquete y documentación en transición; no aporta al MVP. Descartada.
- **Opción C**: sin router, condicionales. C-26..C-33 necesitan rutas y habría que reescribir el shell. Descartada.
- **Decisión**: **A**. No se crean features vacías de negocio: solo la carpeta `features/` cuando aporte claridad, evitando archivos muertos.

### D4 — Herramienta de tests de componentes

**Problema**: SU-10 deja abierta la herramienta de tests de componentes.

- **Opción A (recomendada)**: **Vitest** + `@testing-library/react` + `@testing-library/user-event` + `@testing-library/jest-dom` sobre **jsdom**, configurado en `vite.config.ts` (`test: { environment: "jsdom", globals: true, setupFiles: "./src/test/setup.ts" }`).
- **Opción B**: Jest + ts-jest + RTL. Configuración ESM/TS más pesada y transformación duplicada con Vite. Descartada.
- **Opción C**: Vitest + happy-dom. DOM menos completo y APIs de foco/eventos menos fieles, justo lo que importa en accesibilidad. Descartada.
- **Decisión**: **A**. Testing Library fuerza tests por rol/texto, no por implementación; jsdom alcanza para componentes presentacionales.

### D5 — Disciplina de calidad frontend

**Problema**: el proyecto exige Strict TDD y `mypy --strict` en el backend; hay que definir el equivalente frontend y sus evidencias.

- **Opción A (recomendada)**: scaffold mínimo documentado como **excepción** al ciclo; luego test-first por componente/cliente. RED archivado en `docs/evidencias/red-C-25/<tarea>.txt`; si un test pasa de entrada, mutación obligatoria. `tsc --noEmit` con `strict` (equivalente a `mypy --strict`), además `noUncheckedIndexedAccess` y `verbatimModuleSyntax`. ESLint flat config con `typescript-eslint`, `eslint-plugin-react-hooks` y `eslint-plugin-react-refresh`, sin warnings. `mutaciones-C-25.py` y `trazabilidad-C-25.py` propios.
- **Opción B**: StrykerJS. Dependencia y configuración extra, mucho más lento y distinto del resto del repo. Descartada.
- **Opción C**: solo Vitest + `tsc`, sin mutaciones ni trazabilidad. Rompe la paridad de evidencias con C-20..C-24. Descartada.
- **Decisión**: **A**. El task 0 de andamiaje se documenta explícitamente como excepción; desde ahí todo es test-first.

### D6 — Tokens, paleta de estados y estrategia de estilos

**Problema**: implementar "frontend cuidado" sin un framework pesado.

- **Opción A (recomendada)**: CSS custom properties en `src/shared/styles/tokens.css` (color, espaciado 4/8/12/16/24/32/48 px, tipografía 12/14/16/20/24/32 px, radios, sombras, foco), CSS Modules por componente, system font stack, foco visible con `:focus-visible` y el mapa `APPOINTMENT_STATUS_TOKENS`. Paleta AA:

  | Estado | Texto | Fondo | Borde | Contraste texto/fondo |
  |--------|-------|-------|-------|----------------------|
  | `reservado` | `#1D4ED8` | `#DBEAFE` | `#93C5FD` | 5.49:1 |
  | `confirmado` | `#15803D` | `#DCFCE7` | `#86EFAC` | 4.57:1 |
  | `atendido` | `#374151` | `#E5E7EB` | `#9CA3AF` | 8.33:1 |
  | `ausente` | `#B45309` | `#FEF3C7` | `#FCD34D` | 4.51:1 |
  | `cancelado` | `#B91C1C` | `#FEE2E2` | `#FCA5A5` | 5.30:1 |

- **Opción B**: Tailwind CSS. Suma build/config y dispersa los colores de estado en el markup. Descartada.
- **Opción C**: CSS-in-JS. Runtime extra y una dependencia más sin necesidad. Descartada.
- **Decisión**: **A**. El contraste se valida con una tabla en `verify-C-25.md`, no con una herramienta en el build.

### D7 — Cliente de API: `fetch` nativo con wrapper tipado y costura de token (corrección C1)

**Problema**: elegir `fetch`, axios o TanStack Query, y dónde dejar el enganche del `Bearer` sin invadir C-26.

- **Opción A (recomendada)**: `src/shared/api/client.ts` recibe la función `fetch` **por parámetro** (default `fetch` del navegador), compone `${VITE_API_URL}${path}`, serializa JSON y devuelve un resultado discriminado `{ ok: true, status, data } | { ok: false, status, error }` sin lanzar por errores HTTP. Costura `setAuthProvider({ getToken })` por defecto `null`; si hay provider agrega `Authorization: Bearer`. C-25 no lee ni guarda ningún token.
- **Opción B**: axios. Dependencia extra y el interceptor de `401` ya es lógica de C-26 (ALTO). Descartada.
- **Opción C**: TanStack Query ahora. Introduce estado de servidor sin pantallas que lo usen. Descartada.
- **Decisión**: **A**. La inyección de `fetch` (C1) es lo que permite testear el borde sin tocar globals; C-26 reemplaza el provider y centraliza el `401`, C-27 evalúa TanStack Query.

### D8 — Tipos de la API escritos a mano

**Problema**: decidir entre tipos manuales y codegen con `openapi-typescript`.

- **Opción A (recomendada)**: escribir a mano solo lo que C-25 usa: `ApiErrorPayload` (cuatro formas), `Violation`, `FieldError`, `AuthToken` (`accessToken`, `tokenType`), `CurrentUser` (`id`, `username`, `displayName`, `role`, `professionalId`) y un `Json` genérico. Sin tipos de agenda/turnos todavía.
- **Opción B**: `openapi-typescript` contra `/api/openapi.json`. Exige backend corriendo o schema versionado, agrega paso de generación y tipos enormes. Descartada.
- **Opción C**: `zod` para validar en runtime. Otra dependencia; el backend ya valida y el front solo presenta. Descartada.
- **Decisión**: **A**. Codegen se reevalúa en C-27 cuando el volumen de endpoints lo justifique.

### D9 — Modelo de errores: cuatro formas normalizadas y mensajes textuales

**Problema**: la API responde cuatro cuerpos distintos y el front no debe reescribir los mensajes del dominio.

- **Opción A (recomendada)**: `ApiErrorPayload` como unión discriminada: `{ kind: "validation", status: 400, errors }`, `{ kind: "auth", status: 401, code, message }`, `{ kind: "forbidden" | "conflict" | "unprocessable", status: 403|409|422, violations }`, `{ kind: "not_found", status: 404, code, message }` y `{ kind: "unknown", status, rawText }`. `getApiErrorMessages(payload)` devuelve, en orden, `errors[].message`, `violations[].message` o `message`. Los mensajes del dominio se muestran textuales.
- **Opción B**: asumir siempre `violations[]`. Un `400`, `401` o `404` rompería el parseo. Descartada.
- **Opción C**: devolver el string crudo al usuario. Puede mostrar JSON crudo. Descartada.
- **Decisión**: **A**. `ErrorState` recibe `messages: string[]`, nunca un objeto de error; la UI puede anteponer contexto pero no altera el mensaje.

### D10 — Componentes base presentacionales y tests sin mocks globales (corrección C1)

**Problema**: definir los componentes base y cómo testear el cliente sin caer en mocks de colaboradores ni en reemplazos globales.

- **Opción A (recomendada)**: `LoadingState` (spinner + texto, `role="status"`), `EmptyState` (título, descripción, acción opcional), `ErrorState` (`role="alert"`, lista de mensajes, reintento opcional), `PageShell` (header + main + footer) y `StatusBadge` (usa `APPOINTMENT_STATUS_TOKENS`). Son presentacionales: todo por props, sin fetch ni store. El cliente recibe `fetch` por parámetro y los tests le pasan una función real que devuelve `new Response(...)`.
- **Opción B**: MSW desde C-25. Dependencia y setup sin ningún consumidor todavía. Descartada.
- **Opción C**: mockear los componentes base en tests de pantallas. Viola "no mockear colaboradores internos" y oculta fallos de accesibilidad. Descartada.
- **Decisión**: **A**, con **C1** como regla explícita. **Prohibido en los tests del front**: `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. El cliente se prueba inyectándole una función `fetch` real que devuelve `new Response(...)`; es el equivalente frontend de "sin mock, patch ni monkeypatch" del backend.

### D11 — Docker del frontend, puerto 5173 y HMR en Windows

**Problema**: agregar `frontend` a Compose sin romper el desarrollo en Windows ni confundir la URL de la API.

- **Opción A (recomendada)**: `frontend/Dockerfile` de desarrollo `FROM node:24-alpine`, `npm ci`, `EXPOSE 5173`, `CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]`. Servicio `frontend` con `build: ./frontend`, `env_file: .env`, `VITE_API_URL`, `ports: "5173:5173"`, volúmenes `./frontend:/app` + `/app/node_modules` anónimo, `depends_on: backend` y polling (`server.watch.usePolling` / `CHOKIDAR_USEPOLLING`) para HMR en Windows.
- **Opción B**: build estático + nginx. Sin hot reload; no es lo que pide C-25. Descartada.
- **Opción C**: correr Vite solo en el host. Contradice KB 08/DD-05 (cuatro servicios) y el scope. Descartada.
- **Decisión**: **A**. `VITE_API_URL` en el navegador es `http://localhost:8000/api` (el browser no resuelve el hostname `backend`). Se documenta y se verifica en `verify-C-25.md`.

### D12 — Variables de entorno y tipado de `import.meta.env`

**Problema**: cómo llega `VITE_API_URL` al bundle y cómo se tipa sin agregar secretos.

- **Opción A (recomendada)**: no se agregan variables; `.env.example` ya tiene `VITE_API_URL` y `CORS_ORIGIN`. `src/vite-env.d.ts` declara `ImportMetaEnv` con `readonly VITE_API_URL: string`. Local: `envDir: ".."` en `vite.config.ts` con fallback; Docker: Compose pasa `VITE_API_URL`. Fallback defensivo `import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"`.
- **Opción B**: agregar `FRONTEND_PORT` y parametrizar el puerto. No está pedido y el scope fija 5173. Descartada.
- **Opción C**: usar `VITE_API_URL` sin tipar (`as string`). Casteo inseguro y prohibido por las reglas duras. Descartada.
- **Decisión**: **A**. C-25 solo consume variables existentes; ninguna sensible.

### D13 — Frontera con el backend: C-25 no toca `backend/`

**Problema**: confirmar que el front puede llamar a la API sin cambiar el backend ni invadir C-23.

- **Opción A (recomendada)**: no se modifica `backend/` ni `.env.example`; de Compose solo se agrega el servicio `frontend`. CORS ya apunta a `http://localhost:5173`. Si el front cambia de puerto, se ajusta `CORS_ORIGIN` en `.env`, no en código.
- **Opción B**: tocar `main.py` para ampliar CORS. Amplía seguridad sin necesidad y toca archivos de C-18/C-19. Descartada.
- **Opción C**: proxy de Vite para evitar CORS. Oculta el origen real y complica URLs; CORS ya está. Descartada.
- **Decisión**: **A**. El único archivo compartido es `docker-compose.yml`, y se edita solo con C-22/C-23/C-24 archivados.

### D14 — Límites de scope

**Problema**: evitar que el change base se convierta en "media app".

- **Opción A (recomendada)**: C-25 entrega andamiaje + sistema de diseño + cliente + estados base + Docker + tests. No entrega login (C-26), pantallas de negocio (C-27..C-33), consumo real de endpoints ni librería de datos.
- **Opción B**: adelantar el login "porque es poco". Invade C-26 (ALTO, storage del token) y mezcla changes. Descartada.
- **Opción C**: adelantar la agenda. Depende de decisiones de C-27 y rompe el roadmap. Descartada.
- **Decisión**: **A**. El `HomePage` es solo un shell que demuestra tokens y componentes base.

### D15 — Tests exigidos por C-25

**Problema**: definir los tests mínimos que cumplen el scope sin quedarse corto.

- **Opción A (recomendada)**: humo sobre `App` con router; `ErrorState` (uno y varios mensajes, `role="alert"`); `EmptyState` (con y sin acción); `LoadingState` (`role="status"`); `StatusBadge` (un caso por estado); `client.ts` (éxito + `400`/`401`/`403`/`409`/`422`/`404`/`unknown` + `Authorization` ausente/presente); `APPOINTMENT_STATUS_TOKENS` (cinco estados).
- **Opción B**: solo humo y tres componentes. Deja el cliente sin cobertura justo cuando define el manejo de errores. Descartada.
- **Opción C**: sumar `jest-axe`. Dependencia extra; roles/textos de RTL ya cubren lo básico. Descartada.
- **Decisión**: **A**. Cada test en su archivo y con datos literales del contrato, solo nombres ficticios.

### D16 — Evidencias y verificación espejo del backend

**Problema**: dejar rastro verificable del apply sin inventar un proceso nuevo.

- **Opción A (recomendada)**: `docs/evidencias/red-C-25/`, `versiones-C-25.txt`, `tsc-C-25.txt`, `eslint-C-25.txt`, `vitest-C-25.txt`, `mutaciones-C-25.py`/`.txt`, `trazabilidad-C-25.py`/`.txt`, `docker-C-25.txt` y `verify-C-25.md` con el formato de `verify-C-22.md`/`verify-C-23.md`.
- **Opción B**: solo `verify-C-25.md`. Pierde la prueba RED y la trazabilidad del resto de los changes. Descartada.
- **Opción C**: nada de evidencias. Incumple la disciplina del proyecto. Descartada.
- **Decisión**: **A**. Prefijo `-C-25` para no mezclar con las evidencias del backend.

## Reglas duras del frontend

Son contrato; romperlas es un defecto.

- **Sin mocks ni reemplazos globales (C1)**: prohibido `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. El cliente recibe `fetch` por parámetro y los tests pasan una función real que devuelve `new Response(...)`. Equivale a "sin mock, patch ni monkeypatch" del backend.
- **Sin `any` explícito**: usar `unknown` + narrowing; `tsconfig` en `strict` con `noUncheckedIndexedAccess` y `verbatimModuleSyntax`.
- **Sin `@ts-ignore` ni `@ts-expect-error`**: si un tipo no cierra, se corrige el tipo, no se silencia.
- **Mensajes del dominio tal cual**: `getApiErrorMessages` devuelve el texto del backend sin traducir ni reformular; la UI solo puede anteponer contexto.
- **Solo datos ficticios**: nombres tipo "Dra. Laura Quiroga" y "Ana Pérez", ids de ejemplo; nunca datos reales de pacientes.
- **No commitear**: el apply no hace `git add`, `commit`, `push`, `restore`, `checkout` ni `stash`.
- **Calidad obligatoria**: `tsc --noEmit` sin errores y ESLint sin warnings antes de cerrar el change.

## Risks

| Riesgo | Mitigación |
|--------|------------|
| `frontend/` no existe y el ciclo RED→GREEN no puede empezar sin runner | Task 0 de andamiaje mínimo (D5), documentado como excepción; desde ahí todo es test-first. |
| Se adopta una version mayor (React 19 / Vite 7) fuera de SU-10 | D1/C2: solo las majors elegidas; cualquier salto es un change aparte. |
| Se inventan versiones exactas en el design y quedan desactualizadas | D1/C2: el design nombra majors; las versiones exactas se fijan en el apply y se archivan en `versiones-C-25.txt`. |
| El test del cliente stubea `fetch` global y contamina otros tests o simula de más | D10/C1: `fetch` inyectado por parámetro; los tests pasan una función real con `new Response(...)`; prohibido `vi.stubGlobal`/MSW. |
| `VITE_API_URL` apunta a `http://backend:8000` y el navegador no resuelve `backend` | D11: en el browser es `http://localhost:8000/api`; el hostname `backend` es solo de la red de Compose. |
| El HMR no ve cambios en Windows con Docker | D11: polling (`usePolling`/`CHOKIDAR_USEPOLLING`); verificación explícita en `verify-C-25.md`. |
| El bind mount pisa `node_modules` del contenedor | D11: volumen anónimo `/app/node_modules`. |
| El cliente solo modela `violations[]` y rompe con `400`/`401`/`404` | D9: unión discriminada con las cuatro formas y un caso `unknown`; tests por forma. |
| La UI reescribe o traduce mensajes del dominio | D9/reglas duras: `getApiErrorMessages` devuelve el mensaje textual; la UI solo agrega contexto. |
| C-25 implementa storage del token e invade C-26 (ALTO) | D7/D14: solo `authProvider` nulo; C-26 decide localStorage vs memoria. |
| Los tests dependen de CSS/layout y son frágiles | D10/D15: RTL por rol/texto; el color se prueba como variante lógica, no computada. |
| jsdom no valida contraste real | D6: tabla de contraste AA en `verify-C-25.md`; el test solo fija la variante. |
| `tsc --noEmit` con `strict` frena el andamiaje por tipos de Vite | D12: `vite-env.d.ts` tipado, `@types/react`/`@types/react-dom`, sin `any` ni supresiones. |
| Se adelanta login o agenda y se mezclan changes | D14: non-goals explícitos; el `HomePage` es solo shell. |
| El apply toca `backend/` y choca con C-23 en curso | D13: solo se agrega el servicio `frontend` a Compose, con C-22/C-23/C-24 archivados. |
| El lockfile no se versiona y las instalaciones divergen | D2: `package-lock.json` versionado y `npm ci` en Docker. |
| El test de humo pasa con un assert trivial | D5/D15: roles/textos concretos, cliente con contrato completo y mutaciones para detectar tests vacíos. |
| La deprecación de `react-router-dom` v6 obliga a migrar | D3: v6 es estable y suficiente; v7 se evalúa en un change posterior. |
