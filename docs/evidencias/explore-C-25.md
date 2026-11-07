# Explore C-25 — `frontend-base-react-vite`

Fecha: 2026-11-06
Fase: 6 — Interfaz web (React + TypeScript + Vite), al final y sobre la API probada
Governance: **BAJO** (según `CHANGES.md` §[C-25])
Dependencias en `CHANGES.md`: `C-22`, `C-23`, `C-24`.

> Este explore es analítico: **no** ejecutó docker, `npm install`, `npx`, pytest, alembic ni pip; **no** tocó código, tests, migraciones, specs, `CHANGES.md`, la KB, `docker-compose.yml`, `.env.example` ni creó `frontend/` ni la carpeta del change. Se leyó C-22 (archivado), C-23 **en curso** (`backend/` tiene cambios sin commitear: **no se tomó ese código a medio hacer como fuente de verdad**) y C-24 **propuesto pero no implementado** (`design.md` es la fuente de verdad). C-25 es el GATE 15: el apply espera C-22, C-23 y C-24 archivados y verdes.
>
> Sólo se ejecutaron comandos de versión: `node --version` → **v24.19.0**, `npm --version` → **11.17.0**, `docker --version` → **29.9.2**. `frontend/` **no existe todavía**.

---

## 1. Alcance de C-25 según `CHANGES.md` y qué queda afuera

### Qué entra en C-25

1. **`frontend/` con Vite + React 18 + TypeScript `strict`**: `main.tsx`, router mínimo, estructura `features/`, `shared/` y `pages/`.
2. **`shared/`**: tokens de diseño (color, espaciado, tipografía), colores por estado del turno y componentes base de **carga**, **vacío** y **error**.
3. **Cliente de API tipado** con `VITE_API_URL` y manejo uniforme de `{ "violations": [...] }` (el token lo agrega C-26).
4. **Herramienta de tests de componentes** elegida y configurada (SU-10), con un **test de humo**.
5. **`frontend/Dockerfile`** y servicio `frontend` en `docker-compose.yml` (puerto **5173**).
6. **Tests de componentes**: el estado de error muestra el mensaje recibido; el vacío y el de carga se renderizan.

### Qué queda explícitamente afuera

- **Login, sesión y envío del `Bearer`**: C-26 (governance **ALTO**; decidir dónde se guarda el token es de C-26). C-25 solo deja el **punto de enganche**.
- **Pantallas de negocio** (agenda diaria/semanal, formulario de turno, vista por sillón, horarios y bloqueos, catálogos y pacientes): C-27 a C-33.
- **Consumo real de endpoints de agenda/turnos/catálogos**: C-25 no pide pantallas; el cliente queda listo pero sin features que lo usen.
- **Librería de estado global, SSR, i18n, PWA, service workers**: no están en el scope; el estado local de cada pantalla y el router alcanzan.
- **UI kit o framework de componentes** (MUI, Chakra, shadcn): la KB pide "frontend cuidado" con un sistema mínimo, no un framework pesado (DD-04).
- **Tests E2E (Playwright/Cypress)**: el scope pide tests de componentes; E2E no está previsto en el roadmap.
- **Backend, CORS, JWT, migraciones**: ya existen; C-25 **no** modifica `backend/` ni el contrato de la API.
- **Nuevas variables sensibles**: C-25 no agrega secretos; `VITE_API_URL` y `CORS_ORIGIN` ya están en `.env.example`.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-25 reutiliza

| Pieza | Dónde | Qué aporta a C-25 |
|-------|-------|-------------------|
| Contrato HTTP base | `openspec/specs/api-foundation/spec.md` | Cuatro cuerpos de error estables: `400 {errors:[{field,type,message}]}`, `401 {code,message}`, `403/409/422 {violations:[...]}`, `404 {code,message}`; JSON camelCase. |
| Login y sesión | `openspec/specs/authentication-and-rbac/spec.md` | `POST /api/auth/login` devuelve exactamente `accessToken` + `tokenType: "bearer"`; `/me` devuelve `id`, `username`, `displayName`, `role`, `professionalId`. C-25 **no** lo implementa, solo tipa el contrato para no bloquear C-26. |
| Agenda | `openspec/changes/api-consulta-de-agenda/design.md` | `GET /api/agenda` con sobre `{from,to,timezone,appointments,workingHours,blocks}`; C-27+ lo consumirán. |
| Servicio backend | `docker-compose.yml` | Servicios `postgres`, `redis`, `backend`; **falta `frontend`**. `backend` corre en `${API_PORT}` y ya tiene healthcheck. |
| Variables de entorno | `.env.example` | 14 nombres; **`CORS_ORIGIN`** y **`VITE_API_URL`** ya existen (sin valores). No hace falta agregar ninguna. |
| CORS | `backend/app/main.py`, `backend/app/config.py` | `CORSMiddleware` con `settings.cors_origin`; `vite_api_url` ya está en `Settings`. No se toca el backend. |
| Disciplina de evidencias | `docs/evidencias/verify-C-22.md`, `mutaciones-C-22.py`, `trazabilidad-C-22.py`, `red-C-19..23/` | Formato a espejar: RED antes del código, mutaciones, trazabilidad, `verify-C-XX.md`. |
| Herramientas instaladas | Entorno | Node **v24.19.0**, npm **11.17.0**, Docker **29.9.2**. |
| KB de frontend | `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado, §Estructura, §Docker, §Variables; `09` §DD-04, §SU-10; `02` §Stack | Lineamientos de tokens, estados, accesibilidad, responsive y versiones. |

### 2.2. Qué le falta a la base para C-25

1. **Crear `frontend/`** desde cero (no existe): `package.json`, `tsconfig`, `vite.config.ts`, `index.html`, `src/`.
2. **Elegir y fijar versiones** de React/TS/Vite y de la herramienta de tests (SU-10 lo deja abierto).
3. **Elegir el gestor de paquetes** y versionar el lockfile.
4. **Definir la estructura** `features/shared/pages` y el router mínimo.
5. **Definir tokens de diseño** y la paleta de estados del turno con contraste accesible.
6. **Definir la estrategia de estilos** (CSS Modules vs Tailwind vs CSS-in-JS).
7. **Escribir el cliente de API tipado** y el modelo de los cuatro cuerpos de error.
8. **Definir el punto de enganche del token** sin implementar C-26.
9. **Componentes base** de carga, vacío y error.
10. **`frontend/Dockerfile`** y el servicio `frontend` en Compose con hot reload en Windows.
11. **Configurar Vitest + Testing Library** y el test de humo.
12. **Definir la disciplina de calidad** (test-first, `tsc --noEmit`, ESLint, mutaciones, trazabilidad).

### 2.3. Observaciones que condicionan el diseño

- **`frontend/` no existe**: el primer task es andamiaje, no una feature. El ciclo RED→GREEN tiene un arranque: primero el esqueleto mínimo ejecutable, después test-first por componente.
- **Node del host es 24.19.0**, pero SU-10 fija React 18 / TS 5 / Vite 5. Vite 5 soporta Node `^18 || >=20`, así que Node 24 es compatible; conviene **fijar la imagen base del contenedor** para que no dependa del host.
- **La API es la única fuente de verdad de las reglas** (DD-06, reglas duras). La UI **puede anticipar** errores pero **no** los define: los mensajes de `violations` se muestran tal cual (KB 08 §Frontend cuidado).
- **El backend tiene cuatro formas de error**, no una: `errors[]` (400 de esquema), `code/message` (401/404), `violations[]` (403/409/422). El cliente debe modelar las cuatro; asumir solo `violations` rompería login y rutas inexistentes.
- **C-25 no puede probar el `Bearer`**: C-26 lo agrega. Si C-25 "adivina" storage (localStorage), invade governance ALTO ajeno. Debe dejar una **costura** (`getToken`) sin implementación.
- **`VITE_API_URL` se resuelve en el navegador, no en el contenedor**: el browser del host no resuelve el hostname `backend`. En desarrollo debe ser `http://localhost:8000/api`; dentro de la red de Compose, el backend se llama `backend`. Mezclar ambos es el error clásico de este change.
- **Hot reload en Windows + Docker**: los eventos de filesystem del bind mount no siempre llegan; Vite necesita polling (`usePolling`) o el contenedor no ve los cambios.
- **El proyecto prohíbe mocks de colaboradores en tests de dominio**. En el front, el equivalente sano es: componentes **presentacionales** que reciben props (sin red) y un cliente testeado con `fetch` stubbeado en **sus** tests; nada de mockear componentes internos.
- **Strict TDD exige evidencia RED**: hay que guardar la salida del test fallando en `docs/evidencias/red-C-25/` antes de escribir el código, igual que en C-20..C-24.
- **`type` y `any` prohibidos**: TypeScript `strict` y `unknown` + narrowing; `tsc --noEmit` es el equivalente frontend de `mypy --strict`.
- **C-25 es BAJO**: se puede implementar con autonomía si los tests pasan; no hay decisión de seguridad propia (esa es C-26, ALTO).

---

## 3. Decisiones de diseño (`D1`–`D16`)

### D1 — Versiones: respetar SU-10 (React 18 / TS 5 / Vite 5) y fijar Node del contenedor

**Problema**: SU-10 dice React 18, TypeScript 5 y Vite 5, pero a la fecha hay versiones mayores (React 19, Vite 6/7). El host tiene Node 24. Hay que decidir qué se pinta en `package.json` y con qué Node corre.

- **Opción A (recomendada)**: respetar SU-10 como **contrato del TP**: `react@18.3.x`, `react-dom@18.3.x`, `typescript@5.x`, `vite@5.4.x`, `@vitejs/plugin-react@4.x`. Fijar versiones exactas en `package.json` y en `package-lock.json`. Imagen Docker `node:24-alpine` para alinear con el host (Node 24 es LTS desde 2025 y Vite 5 lo soporta).
  - *Pros*: coincide con la KB, la cátedra y DD-04; reproducible en cualquier máquina con el lockfile; evita migraciones no pedidas; Node 24 cumple el engine de Vite 5.
  - *Contras*: no se estrena React 19 ni Vite 7; sus mejoras no son necesarias para el MVP.
- **Opción B**: ir a lo último estable (React 19 + Vite 7). *Pros*: APIs más nuevas. *Contras*: contradice SU-10, roza un cambio de stack no autorizado, obliga a validar compatibilidad de Testing Library y plugin-react; riesgo sin beneficio para el TP.
- **Opción C**: mezclar (React 18 + Vite 7). *Pros*: ninguna real. *Contras*: combinación no fijada por nadie, más superficie de fallos.
- **Recomendación**: **A**. Versiones exactas + lockfile; Node `24-alpine` en el contenedor, pero **declarar `engines.node: ">=20"`** para no atar el repo al host. Si la autora quiere, React 19 es un cambio de una línea más adelante, pero no en C-25.

### D2 — Gestor de paquetes: npm con lockfile versionado

**Problema**: elegir npm, pnpm o yarn y decidir si el lockfile se versiona.

- **Opción A (recomendada)**: **npm** (ya instalado, v11.17.0) y **`package-lock.json` versionado**. Scripts en `package.json`: `dev`, `build`, `preview`, `test`, `test:run`, `typecheck`, `lint`.
  - *Pros*: cero instalaciones extra (el entorno ya lo trae); Docker y CI reproducibles con `npm ci`; una sola herramienta para scripts y lockfile.
  - *Contras*: algo más lento que pnpm en árboles grandes; irrelevante para este tamaño.
- **Opción B**: pnpm. *Pros*: instalación más rápida y `node_modules` compacto. *Contras*: hay que instalar Corepack/pnpm en el host y en la imagen; una dependencia de tooling más para un proyecto individual.
- **Opción C**: yarn. *Pros*: ninguno frente a npm acá. *Contras*: otra herramienta, otro lockfile, sin ganancia.
- **Recomendación**: **A**. `npm ci` en Docker, `npm install` en local; lockfile versionado (nunca en `.gitignore`).

### D3 — Estructura `features/shared/pages` y router mínimo con React Router

**Problema**: fijar la organización de carpetas y cómo se navega entre pantallas futuras sin implementarlas.

- **Opción A (recomendada)**:
  - Estructura de KB 08: `src/features/{agenda,appointments,configuration,login,patients}/`, `src/shared/{components,api,styles,lib}/`, `src/pages/`, `src/main.tsx`, `src/App.tsx`.
  - Cada feature expone componentes y (más adelante) hooks; lo transversal va a `shared/`.
  - **React Router 6.x (`react-router-dom`)** con `createBrowserRouter` y una ruta raíz de layout. En C-25 solo hay una ruta `/` que renderiza un `HomePage` de bienvenida y una ruta `*` de "no encontrada".
  - *Pros*: coincide con la KB y con la forma en que crecerán C-27..C-33; el router queda listo para C-26 (login/redirect); una sola ruta hoy evita sobre-ingeniería.
  - *Contras*: agrega `react-router-dom` como dependencia; es estándar y barata.
- **Opción B**: React Router 7. *Pros*: última versión. *Contras*: cambios de API/paquete y documentación en transición; no aporta al MVP.
- **Opción C**: sin router (una sola página, condicionales). *Pros*: cero dependencias. *Contras*: C-26..C-33 necesitan rutas; habría que introducirlo después y reescribir el shell.
- **Recomendación**: **A**. Estructura de la KB + React Router 6 con `createBrowserRouter`, ruta raíz y `*` de 404. No se crean las features vacías de negocio todavía; sí la carpeta `features/` con un `README` o un placeholder mínimo sólo si aporta claridad (evitar archivos muertos).

### D4 — Tests de componentes: Vitest + Testing Library + jsdom

**Problema**: SU-10 deja abierta la herramienta de tests de componentes; hay que elegirla y configurarla.

- **Opción A (recomendada)**: **Vitest** + `@testing-library/react` + `@testing-library/user-event` + `@testing-library/jest-dom` + **jsdom** como entorno. Configuración en `vite.config.ts` (`test: { environment: "jsdom", globals: true, setupFiles: "./src/test/setup.ts" }`).
  - *Pros*: comparte configuración y transformación con Vite (mismo pipeline TS/ESM); arranque rápido; compatible con React 18; Testing Library fomenta tests por comportamiento (accesibles por rol/texto), no por implementación; `user-event` cubre teclado (accesibilidad de C-29).
  - *Contras*: jsdom no es un navegador real (no layout ni CSS); para C-25 alcanza porque los componentes son presentacionales.
- **Opción B**: Jest + ts-jest + Testing Library + jsdom. *Pros*: conocido. *Contras*: configuración ESM/TS más pesada, transformación duplicada con Vite, más lento; sin ganancia.
- **Opción C**: Vitest + **happy-dom**. *Pros*: más rápido que jsdom. *Contras*: DOM menos completo; diferencias en APIs (p. ej. eventos/foco) que ya importan en C-29; no se recomienda para accesibilidad.
- **Recomendación**: **A**. Vitest + RTL + jsdom. `globals: true` para escribir `describe/it/expect` sin imports (y tipar con `types: ["vitest/globals"]`), `setupFiles` con `@testing-library/jest-dom`.

### D5 — Disciplina de calidad frontend: test-first con evidencia, `tsc --noEmit`, ESLint y mutaciones

**Problema**: el proyecto exige Strict TDD y `mypy --strict` en el backend; hay que definir el equivalente frontend y cómo se prueba (el backend tiene `mutaciones-C-XX.py` y `trazabilidad-C-XX.py`).

- **Opción A (recomendada)**:
  - **Scaffold primero, mínimo**: un task 0 crea `package.json`, `tsconfig`, `vite.config.ts`, `index.html` y un `App` trivial; esto habilita el runner. A partir de ahí, **cada componente/cliente se escribe test-first**.
  - **RED** guardado: la salida de `npm run test:run -- <archivo>` fallando se redirige a `docs/evidencias/red-C-25/<n>-<caso>.txt` **antes** de escribir el código (igual que C-20..C-24). Si el test pasa de entrada, se muta el código o el test para forzar el rojo y se documenta.
  - **`tsc --noEmit`** con `strict` (equivalente a `mypy --strict`); además `noUncheckedIndexedAccess`, `noImplicitOverride`, `exactOptionalPropertyTypes` si no molesta, `verbatimModuleSyntax`.
  - **ESLint** flat config con `typescript-eslint`, `eslint-plugin-react-hooks` y `eslint-plugin-react-refresh`; `npm run lint` sin warnings.
  - **Mutaciones**: `docs/evidencias/mutaciones-C-25.py` propio (mutar fuente TS/TSX y verificar que el test falla), espejo de `mutaciones-C-22.py`, en vez de Stryker.
  - **Trazabilidad**: `docs/evidencias/trazabilidad-C-25.py` que mapea cada escenario del scope (carga, vacío, error, smoke, cliente) a su test.
  - *Pros*: paridad con la disciplina backend que la cátedra ya evalúa; evidencia verificable; detecta tests que no prueban nada; sin dependencias pesadas.
  - *Contras*: el arranque (task 0) no puede ser test-first puro; se documenta como andamiaje.
- **Opción B**: **StrykerJS** para mutaciones. *Pros*: mutation testing real y reporte. *Contras*: dependencia y configuración extra, mucho más lento en un proyecto chico, y el resto del repo no lo usa.
- **Opción C**: sólo Vitest + `tsc`, sin mutaciones ni trazabilidad. *Pros*: menos trabajo. *Contras*: rompe la paridad de evidencias con C-20..C-24 que la autora ya viene manteniendo; no se recomienda.
- **Recomendación**: **A**. Scripts de mutación/trazabilidad livianos y propios, `tsc --noEmit` + ESLint obligatorios, RED archivado. El task 0 de andamiaje se documenta explícitamente como excepción al ciclo.

### D6 — Tokens de diseño, paleta de estados y estrategia de estilos

**Problema**: definir cómo se implementa "frontend cuidado" (tokens, estados por color, tipografía, accesibilidad) sin adoptar un framework pesado.

- **Opción A (recomendada)**:
  - **CSS custom properties** en `src/shared/styles/tokens.css`: color, espaciado (escala 4/8/12/16/24/32/48 px), tipografía (12/14/16/20/24/32 px), radios, sombras y foco.
  - **CSS Modules** (`*.module.css`) por componente; sin utilidades mágicas ni CSS global salvo el reset y los tokens.
  - **Tipografía con system font stack** (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`): sin red ni FOUT; opción de fuente local más adelante.
  - **Paleta de estados** (texto sobre fondo tenue, con borde; contraste AA ≥ 4.5:1):

    | Estado | Texto | Fondo | Borde | Nota |
    |--------|-------|-------|-------|------|
    | `reservado` | `#1D4ED8` | `#DBEAFE` | `#93C5FD` | azul, estado inicial |
    | `confirmado` | `#15803D` | `#DCFCE7` | `#86EFAC` | verde |
    | `atendido` | `#374151` | `#E5E7EB` | `#9CA3AF` | gris, terminal |
    | `ausente` | `#B45309` | `#FEF3C7` | `#FCD34D` | ámbar |
    | `cancelado` | `#B91C1C` | `#FEE2E2` | `#FCA5A5` | rojo, tachado/muted |

  - Un mapa TypeScript `APPOINTMENT_STATUS_TOKENS` que devuelve el nombre de la clase/variable por estado, para que C-27 pinte sin hardcodear colores.
  - Foco visible (`outline` de 2 px con `--color-focus`) y `:focus-visible`; contrastes documentados.
  - *Pros*: cero dependencias de UI; control total del look; tokens reutilizables y testeables; cumple DD-04 ("sistema de diseño mínimo"); accesible.
  - *Contras*: hay que escribir estilos a mano; el equipo debe respetar los tokens.
- **Opción B**: **Tailwind CSS**. *Pros*: velocidad de maqueta y consistencia por clases. *Contras*: suma build/config y disciplina de clases; los colores de estado quedan dispersos en el markup; el "cuidado" se logra igual con tokens; no hace falta para el MVP.
- **Opción C**: **CSS-in-JS** (styled-components/emotion). *Pros*: estilos co-localizados con tipos. *Contras*: runtime extra, SSR/streaming (aunque no hay SSR), y una dependencia más; no se recomienda.
- **Recomendación**: **A**. `tokens.css` + CSS Modules + system font stack + mapa de estados. La paleta es una propuesta; se valida con una tabla de contraste en `verify-C-25.md` (no se agrega una herramienta de contraste al build).

### D7 — Cliente de API: `fetch` nativo con un wrapper tipado y costura de token

**Problema**: elegir `fetch`, axios o TanStack Query, y dónde deja C-25 el enganche del `Bearer` sin pisar C-26.

- **Opción A (recomendada)**:
  - `src/shared/api/client.ts`: wrapper sobre **`fetch`** que compone `${VITE_API_URL}${path}`, serializa JSON, parsea la respuesta y devuelve un **resultado discriminado** (no lanza por errores HTTP): `{ ok: true, status, data } | { ok: false, status, error }`.
  - `ApiErrorPayload` normaliza las cuatro formas (D9).
  - **Costura de auth**: opción de configuración `setAuthProvider({ getToken })` o un parámetro `auth?: { token }` que, si está, agrega `Authorization: Bearer`. En C-25 el provider es `null`; **no** se lee ni se guarda ningún token. C-26 implementa el storage (decisión suya, ALTO).
  - Sin caché ni estado global: C-25 no consume datos; C-27 decidirá si suma TanStack Query.
  - *Pros*: cero dependencias; `fetch` es estándar y testeable con `vi.stubGlobal("fetch", ...)`; el contrato de error queda en un solo lugar; la costura desacopla C-26.
  - *Contras*: hay que escribir el parseo de errores y (si hiciera falta) timeouts/abort, que axios trae; es poco código y controlado.
- **Opción B**: **axios**. *Pros*: interceptores, timeouts, amplia adopción. *Contras*: dependencia extra, tipado de errores menos directo, y el interceptor de `401` ya es lógica de C-26 (ALTO).
- **Opción C**: **TanStack Query** ahora. *Pros*: caché/refetch para C-27. *Contras*: introduce estado de servidor antes de tener pantallas; C-25 no consulta nada; se puede sumar en C-27 sin rehacer el cliente.
- **Recomendación**: **A**. `fetch` + wrapper tipado + `authProvider` nulo. Documentar que C-26 reemplaza el provider y maneja el `401` en un solo lugar; C-27 evalúa TanStack Query.

### D8 — Tipos de la API: escritos a mano, mínimos y explícitos (codegen más adelante)

**Problema**: decidir si los tipos del contrato se escriben a mano o se generan con `openapi-typescript`.

- **Opción A (recomendada)**: escribir a mano **sólo lo que C-25 usa**: `ApiErrorPayload` (cuatro formas), `Violation`, `FieldError`, `AuthToken` (`accessToken`, `tokenType`), `CurrentUser` (`id`, `username`, `displayName`, `role`, `professionalId`) y un `Json` genérico. Nada de tipos de agenda/turnos todavía.
  - *Pros*: el contrato es chico y estable; cero tooling; sin depender de un backend corriendo para compilar; fácil de leer y testear; evita que el front conozca endpoints que no usa.
  - *Contras*: riesgo de deriva manual cuando C-27..C-33 consuman muchos endpoints.
- **Opción B**: `openapi-typescript` contra `/api/openapi.json`. *Pros*: deriva cero, tipos completos. *Contras*: exige backend corriendo o un schema versionado; agrega paso de generación y tipos enormes; C-25 no lo necesita.
- **Opción C**: `zod` para validar en runtime. *Pros*: valida datos dudosos. *Contras*: otra dependencia; el backend ya valida y el front sólo presenta; no se recomienda en C-25.
- **Recomendación**: **A**. Tipos a mano, acotados a lo que C-25 usa. Revisar codegen en C-27, cuando el volumen de endpoints lo justifique; no se introduce antes.

### D9 — Modelo de errores: las cuatro formas normalizadas y mensajes del dominio tal cual

**Problema**: la API responde cuatro cuerpos distintos; el front debe mostrar los mensajes de dominio sin reescribirlos y sin romperse con `400`/`401`/`404`.

- **Opción A (recomendada)**:
  - `ApiErrorPayload` como unión discriminada:
    - `{ kind: "validation", status: 400, errors: FieldError[] }` ← `{errors:[...]}`.
    - `{ kind: "auth", status: 401, code, message }` ← login inválido o token inválido.
    - `{ kind: "forbidden" | "conflict" | "unprocessable", status: 403|409|422, violations: Violation[] }` ← `{violations:[...]}`.
    - `{ kind: "not_found", status: 404, code, message }` ← `{code,message}`.
    - `{ kind: "unknown", status, rawText }` para cualquier otra cosa.
  - Helper `getApiErrorMessages(payload): string[]` que devuelve, en orden: `errors[].message` (400), `violations[].message` (403/409/422), `message` (401/404). Es lo único que las pantallas renderizan.
  - **Los mensajes del dominio se muestran textuales** (KB 08): no se traducen ni reformulan. La UI puede anteponer contexto ("No se pudo dar el turno:") pero no altera el mensaje.
  - *Pros*: una sola puerta para todos los errores; login (`401`) y `404` no quedan sin modelar; respeta la regla dura de no duplicar reglas ni mensajes en la UI; `getApiErrorMessages` es trivial de testear.
  - *Contras*: hay que mantener cuatro ramas; cada una tiene un test unitario que la fija.
- **Opción B**: asumir siempre `violations[]`. *Pros*: menos código. *Contras*: un `400` o un `404` rompería el parseo; no cubre login.
- **Opción C**: devolver el string crudo al usuario. *Pros*: simple. *Contras*: puede mostrar el JSON; no es "frontend cuidado".
- **Recomendación**: **A**. Unión discriminada + `getApiErrorMessages`; tests para las cuatro formas y para `unknown`. El `ErrorState` recibe `messages: string[]`, no un objeto de error.

### D10 — Componentes base de carga/vacío/error y tests sin mocks de red

**Problema**: definir los componentes base y cómo se testean sin caer en mocks de colaboradores internos (la regla del proyecto prohíbe mocks en el dominio).

- **Opción A (recomendada)**:
  - `src/shared/components/LoadingState.tsx` (spinner + texto `role="status"`), `EmptyState.tsx` (título, descripción, acción opcional), `ErrorState.tsx` (`role="alert"`, lista de mensajes, reintento opcional), `PageShell.tsx` (header + main + footer) y `StatusBadge.tsx` (usa `APPOINTMENT_STATUS_TOKENS`).
  - Son **presentacionales**: reciben todo por props; no hacen fetch ni leen store.
  - Tests con RTL sobre el DOM accesible (roles/texto), sin red: se pasa `messages={["El profesional ya tiene un turno en ese horario."]}` y se verifica que se muestre. `LoadingState` verifica `role="status"`; `EmptyState` verifica título/acción; `StatusBadge` verifica la clase/variante por estado.
  - **Cliente** (`client.ts`): test unitario con `vi.stubGlobal("fetch", ...)` para las cuatro formas de error y el éxito. Ese es el único punto donde se simula red, y es el **borde** (no un colaborador interno), análogo a probar un repositorio contra un doble de HTTP.
  - **Sin MSW** en C-25: no hay componentes que disparen requests, así que MSW no aportaría y sería infraestructura sin uso.
  - *Pros*: cumple el espíritu de "no mockear colaboradores internos"; cada componente es puro y testeable; los tests de accesibilidad detectan roles faltantes; el cliente cubre el contrato de error de verdad.
  - *Contras*: cuando C-27+ hagan fetch, habrá que decidir MSW o un servidor de test; se difiere.
- **Opción B**: MSW desde C-25. *Pros*: intercepción realista para el futuro. *Contras*: dependencia y setup sin ningún consumidor todavía; no se justifica.
- **Opción C**: mockear los componentes base en los tests de pantallas. *Pros*: tests de pantalla rápidos. *Contras*: viola el principio de no mockear colaboradores internos y oculta fallos de accesibilidad.
- **Recomendación**: **A**. Componentes presentacionales + cliente testeado con `fetch` stubbeado; MSW se evalúa recién cuando existan features que consulten.

### D11 — Docker del frontend: dev server, puerto 5173, volumen y hot reload en Windows

**Problema**: agregar `frontend` a Compose sin romper el flujo de desarrollo en Windows ni confundir la URL de la API.

- **Opción A (recomendada)**:
  - `frontend/Dockerfile` para desarrollo: `FROM node:24-alpine`, `WORKDIR /app`, copiar `package*.json`, `npm ci`, copiar el resto, `EXPOSE 5173`, `CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]`. (Un Dockerfile de producción con build + nginx queda fuera del scope; C-25 pide dev server.)
  - Servicio en `docker-compose.yml`:
    ```yaml
    frontend:
      build: ./frontend
      env_file: .env
      environment:
        VITE_API_URL: ${VITE_API_URL}
      ports:
        - "5173:5173"
      volumes:
        - ./frontend:/app
        - /app/node_modules
      depends_on:
        - backend
    ```
  - **`VITE_API_URL` en el navegador** debe ser `http://localhost:8000/api` (el browser corre en el host, no en la red de Compose). Se documenta explícitamente; el nombre `backend` sólo sirve para llamadas server-side, que el front no hace.
  - **Windows**: `vite.config.ts` con `server: { host: true, port: 5173, watch: { usePolling: true, interval: 300 } }` (o `CHOKIDAR_USEPOLLING=true` en el servicio) para que el HMR vea los cambios del bind mount.
  - `node_modules` en un volumen anónimo (`/app/node_modules`) para que el bind mount del host no lo pise.
  - *Pros*: hot reload confiable en Windows; una sola URL de API clara; el contenedor no instala en cada arranque si el lockfile no cambia; Compose reproducible.
  - *Contras*: polling consume algo de CPU; el volumen anónimo exige `docker compose down -v` si se corrompe; es el precio del desarrollo en Windows.
- **Opción B**: build estático + nginx. *Pros*: se parece a producción. *Contras*: no hay hot reload; no es lo que pide C-25 ("servidor de desarrollo de Vite", KB 08). No se recomienda.
- **Opción C**: correr Vite en el host y no dockerizar el front. *Pros*: HMR nativo sin polling. *Contras*: contradice KB 08/DD-05 (cuatro servicios) y el scope de C-25 (servicio `frontend`). Se puede usar como atajo local, pero el repo debe tener el servicio.
- **Recomendación**: **A**. Dockerfile de dev, puerto 5173, volumen de código + volumen anónimo de `node_modules`, polling en Windows y `VITE_API_URL=http://localhost:8000/api` para el navegador. Documentar en `verify-C-25.md` la prueba de que el HMR ve un cambio.

### D12 — Variables de entorno y tipado de `import.meta.env`

**Problema**: cómo llega `VITE_API_URL` al bundle y cómo se tipa, sin agregar secretos ni variables nuevas.

- **Opción A (recomendada)**:
  - No se agregan variables: `.env.example` ya tiene `VITE_API_URL` y `CORS_ORIGIN`. C-25 sólo **consume** `VITE_API_URL`.
  - `src/vite-env.d.ts` declara `interface ImportMetaEnv { readonly VITE_API_URL: string }` e `interface ImportMeta { readonly env: ImportMetaEnv }`.
  - En Docker, Compose pasa `VITE_API_URL` por `environment`; en local, Vite lee el `.env` de la raíz configurando `envDir: ".."` en `vite.config.ts` (o un `frontend/.env` propio; ver pregunta P4).
  - Valor por defecto defensivo en el cliente: `import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"`, para que un `.env` incompleto no rompa el arranque (no es un secreto).
  - *Pros*: sin secretos nuevos; el contrato de variables de KB 08 queda igual; `import.meta.env` tipado evita `any`.
  - *Contras*: `envDir: ".."` acopla el front a la raíz del repo; la alternativa es un `.env` en `frontend/`. Se documenta.
- **Opción B**: agregar `FRONTEND_PORT` y parametrizar el puerto. *Pros*: flexibilidad. *Contras*: no está pedido; el scope fija 5173 y CORS ya apunta a `http://localhost:5173`.
- **Opción C**: usar `VITE_API_URL` sin tipar (`as string`). *Pros*: menos archivos. *Contras*: casteo inseguro; el proyecto prohíbe `any`/asserts innecesarios.
- **Recomendación**: **A**. Reutilizar `VITE_API_URL`, tipar `ImportMetaEnv`, `envDir: ".."` con fallback documentado. Si la autora prefiere `frontend/.env`, es un cambio de una línea.

### D13 — CORS y frontera con el backend: C-25 no toca `backend/`

**Problema**: confirmar que el front puede llamar a la API sin cambiar nada del backend y sin invadir C-23 (en curso).

- **Opción A (recomendada)**:
  - No se modifica `backend/`, `docker-compose.yml` (salvo agregar el servicio `frontend`, que es parte de C-25) ni `.env.example`.
  - El CORS ya está configurado con `settings.cors_origin` (`http://localhost:5173` en `.env`), que es exactamente el origen del dev server.
  - Si en el futuro el front corre en otro puerto, se cambia `CORS_ORIGIN` en `.env` (no en el código).
  - *Pros*: C-25 queda aislado; no colisiona con C-23 (que Antigravity está implementando); el contrato de seguridad de C-19 se respeta.
  - *Contras*: el apply de C-25 tiene que editar `docker-compose.yml` (agregar el servicio) y eso es lo único compartido; se hace cuando C-22/C-23/C-24 estén archivados.
- **Opción B**: tocar `main.py` para permitir más orígenes o métodos. *Pros*: flexibilidad. *Contras*: amplía CORS sin necesidad y toca un archivo de C-18/C-19; riesgo de seguridad. No se recomienda.
- **Opción C**: proxy de Vite (`server.proxy`) para evitar CORS. *Pros*: no depende de CORS. *Contras*: oculta el origen real, complica las URLs y no es necesario porque CORS ya está; además el contrato de `VITE_API_URL` apunta directo. Se puede usar como atajo, no como contrato.
- **Recomendación**: **A**. Sin cambios en backend; sólo el servicio `frontend` en Compose y la variable ya existente. Verificar el preflight de CORS en `verify-C-25.md` cuando el backend esté levantado.

### D14 — Límites de scope y no-goals de C-25

**Problema**: evitar que el change base se convierta en "media app" y se solape con C-26..C-33.

- **Opción A (recomendada)**: C-25 entrega **andamiaje + sistema de diseño + cliente + estados base + Docker + tests de humo**. No entrega:
  - login ni manejo de sesión (C-26);
  - ninguna feature de agenda/turnos/catálogos (C-27..C-33);
  - consumo real de endpoints (sólo tipos y cliente listos);
  - estado global ni librería de datos (se decide en C-27).
  - *Pros*: change chico y terminable; el camino crítico avanza; BAJO governance.
  - *Contras*: al terminar, la app es una cáscara; es lo esperado.
- **Opción B**: adelantar el login "porque es poco". *Pros*: se ve algo útil. *Contras*: invade C-26 (ALTO, storage del token) y mezcla changes.
- **Opción C**: adelantar la agenda. *Pros*: demo temprana. *Contras*: depende de C-24 y de decisiones de C-27; rompe el roadmap.
- **Recomendación**: **A**. Respetar el alcance literal de `CHANGES.md` §[C-25]. El `HomePage` es sólo un shell que demuestra tokens y componentes base.

### D15 — Tests exigidos por C-25 (humo + tres componentes + cliente)

**Problema**: definir exactamente qué tests debe dejar C-25 para cumplir el scope y no quedarse corto.

- **Opción A (recomendada)**:
  1. **Humo** (`src/App.test.tsx` o `src/test/smoke.test.tsx`): renderiza `App` con el router y muestra el `HomePage`; no lanza.
  2. **`ErrorState`**: recibe `messages={["El profesional ya tiene un turno en ese horario."]}` y el texto aparece; con varios mensajes, aparecen todos; `role="alert"`.
  3. **`EmptyState`**: renderiza título/descripción y la acción opcional; sin acción, no hay botón.
  4. **`LoadingState`**: renderiza `role="status"` y el texto de carga.
  5. **`StatusBadge`** (si entra en C-25): un caso por estado con su variante.
  6. **`client.ts`**: éxito + las cuatro formas de error (`400`, `401`, `403/409/422`, `404`) + `unknown`; `getApiErrorMessages` devuelve los textos correctos; el `Authorization` sólo aparece si hay provider.
  7. **`APPOINTMENT_STATUS_TOKENS`**: cubre los cinco estados y no devuelve `undefined`.
  - *Pros*: cubre el scope ("el estado de error muestra el mensaje; vacío y carga se renderizan") y fija el contrato de errores desde el día uno; todo sin red real.
  - *Contras*: el cliente agrega un puñado de casos; es barato y evita retrabajo en C-26/C-27.
- **Opción B**: sólo el test de humo y los tres componentes. *Pros*: mínimo. *Contras*: el cliente de API queda sin cobertura justo cuando define el manejo uniforme de errores; se paga en C-26.
- **Opción C**: agregar también tests de accesibilidad con `jest-axe`. *Pros*: refuerza "frontend cuidado". *Contras*: dependencia extra; los roles/textos de RTL ya cubren lo básico. Se puede sumar después.
- **Recomendación**: **A**. Humo + tres estados + badge + cliente. Mantener cada test en su archivo y con datos literales del contrato (nada de datos reales de pacientes: sólo nombres ficticios).

### D16 — Evidencias y verificación: espejo del flujo backend

**Problema**: dejar rastro verificable del apply, como en C-20..C-24, sin inventar un proceso nuevo.

- **Opción A (recomendada)**: al aplicar C-25, generar:
  - `docs/evidencias/red-C-25/` con la salida RED de cada test antes del código.
  - `docs/evidencias/baseline-C-25.txt` (estado inicial de tests/typecheck, si hay algo antes).
  - `docs/evidencias/pytest-C-25.txt` **no aplica**; en su lugar `vitest-C-25.txt` con `npm run test:run`.
  - `docs/evidencias/typecheck-C-25.txt` con `npm run typecheck` (`tsc --noEmit`).
  - `docs/evidencias/lint-C-25.txt` con `npm run lint`.
  - `docs/evidencias/mutaciones-C-25.py` y `.txt`, `trazabilidad-C-25.py` y `.txt`.
  - `docs/evidencias/verify-C-25.md` con el formato de `verify-C-22.md`/`verify-C-23.md`: precondición, comandos, resultados, cobertura de escenarios y riesgos residuales.
  - *Pros*: consistencia con el resto del repo; la autora puede auditar el change; el "test ANTES del código" queda probado.
  - *Contras*: varios archivos de evidencia; es el estándar que el proyecto ya adoptó.
- **Opción B**: sólo `verify-C-25.md`. *Pros*: menos archivos. *Contras*: pierde la prueba RED y la trazabilidad que el resto de los changes sí tienen.
- **Opción C**: nada de evidencias. *Pros*: rápido. *Contras*: incumple la disciplina del proyecto.
- **Recomendación**: **A**. Nombrar los archivos con el prefijo `-C-25` y no mezclar con los del backend.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| `frontend/` no existe y el ciclo RED→GREEN no puede empezar sin runner | Task 0 de andamiaje mínimo (D5); se documenta como excepción y desde ahí todo es test-first. |
| Se adopta una versión mayor (React 19 / Vite 7) fuera de SU-10 | D1 fija React 18 / TS 5 / Vite 5; cualquier salto es un change aparte. |
| `VITE_API_URL` apunta a `http://backend:8000` y el navegador no resuelve `backend` | D11: en el browser es `http://localhost:8000/api`; el hostname `backend` es sólo para la red de Compose. |
| El HMR no ve cambios en Windows con Docker | D11: `watch.usePolling`/`CHOKIDAR_USEPOLLING`; verificación explícita en `verify-C-25.md`. |
| El bind mount pisa `node_modules` del contenedor | D11: volumen anónimo `/app/node_modules`. |
| El cliente solo modela `violations[]` y rompe con `400`/`401`/`404` | D9: unión discriminada con las cuatro formas; tests por forma. |
| La UI reescribe o traduce mensajes del dominio | D9/regla dura: `getApiErrorMessages` devuelve el mensaje textual; la UI sólo agrega contexto. |
| C-25 implementa storage del token e invade C-26 (ALTO) | D7/D14: sólo `authProvider` nulo; C-26 decide localStorage vs memoria. |
| Se mockean componentes internos en los tests | D10: componentes presentacionales por props; sólo se stubbea `fetch` en el test del cliente (borde). |
| Los tests de componentes dependen de CSS/layout y son frágiles | RTL por rol/texto, no por clases ni estilos; el color se prueba como variante lógica, no computada. |
| jsdom no valida contraste real | D6: la paleta se valida con una tabla de contraste (AA) en `verify-C-25.md`; el test unitario sólo fija la variante. |
| La paleta de estados no cumple accesibilidad | D6: tokens con texto oscuro sobre fondo tenue y borde; ratios ≥ 4.5:1 documentados. |
| `tsc --noEmit` con `strict` frena el andamiaje por tipos de Vite | D12: `vite-env.d.ts` tipado; `@types/react`/`@types/react-dom`; no se usa `any` ni `@ts-ignore`. |
| Se adelanta login o agenda y se mezclan changes | D14: no-goals explícitos; el `HomePage` es sólo shell. |
| El apply toca `backend/` y choca con C-23 en curso | D13: C-25 sólo agrega el servicio `frontend` a Compose cuando C-22/C-23/C-24 estén archivados. |
| El lockfile no se versiona y las instalaciones divergen | D2: `package-lock.json` versionado; `npm ci` en Docker. |
| La deprecación de `react-router-dom` v6 obliga a migrar | D3: v6 es estable y suficiente; v7 se evalúa en un change posterior. |
| El test de humo pasa "porque sí" (assert trivial) | D5/D15: los tests verifican roles/textos concretos y el cliente verifica el contrato; mutaciones para detectar tests vacíos. |

### Preguntas para la autora

- **P1**: ¿Se respetan React 18 / TS 5 / Vite 5 de SU-10, o querés que C-25 estrene React 19 / Vite 7 (D1)? Sugerencia: respetar SU-10.
- **P2**: ¿Node del contenedor `24-alpine` (alineado con tu host) o `20-alpine`/`22-alpine` LTS (D1)? Sugerencia: `24-alpine` con `engines.node >=20`.
- **P3**: ¿React Router 6 (recomendado) o esperamos a React Router 7 (D3)? Sugerencia: 6.
- **P4**: ¿Vite lee el `.env` de la raíz (`envDir: ".."`) o preferís un `frontend/.env` propio (D12)? Sugerencia: `.env` de la raíz, para no duplicar `VITE_API_URL`.
- **P5**: ¿La paleta de estados de D6 te sirve (azul/verde/gris/ámbar/rojo) o tenés colores de marca? Sugerencia: la propuesta, ajustable sin tocar la estructura.
- **P6**: ¿CSS Modules + tokens (recomendado) o querés Tailwind (D6)? Sugerencia: CSS Modules.
- **P7**: ¿Tests con Vitest + Testing Library + jsdom (recomendado) o Jest (D4)? Sugerencia: Vitest.
- **P8**: ¿Mutaciones con un script propio (`mutaciones-C-25.py`) o adoptamos StrykerJS (D5)? Sugerencia: script propio, por paridad con el backend.
- **P9**: ¿Confirmás que C-25 no implementa login ni storage del token y que eso es de C-26 (D7/D14)? Sugerencia: sí; sólo la costura `authProvider`.
- **P10**: ¿Incluimos `StatusBadge` (color por estado) en C-25 o lo dejamos para C-27 (D15)? Sugerencia: incluirlo; es el puente entre los tokens y la agenda.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

> Estos son los tasks que el `apply` de C-25 debería crear; **no** se crea `tasks.md` en este explore.

0. **Precondición y andamiaje**: C-22, C-23 y C-24 archivados y verdes (GATE 15). No tomar el `backend/` a medio hacer de C-23 como contrato. Crear el esqueleto mínimo: `frontend/package.json` (versiones de D1), `package-lock.json`, `tsconfig.json` (`strict`, `noUncheckedIndexedAccess`), `tsconfig.node.json`, `vite.config.ts` (plugin-react, Vitest/jsdom, `envDir`, `server.watch.usePolling`), `index.html`, `src/main.tsx`, `src/App.tsx`, `src/vite-env.d.ts`, ESLint flat config. Verificar `npm run test:run`, `npm run typecheck` y `npm run lint` con un test de humo trivial. Documentar el task 0 como excepción al ciclo RED.
1. **Tokens y estilos base** (D6): `src/shared/styles/tokens.css` (color, espaciado, tipografía, foco), reset mínimo, `APPOINTMENT_STATUS_TOKENS` con los cinco estados. Test unitario del mapa (cubre los cinco).
2. **Componentes base** (D10): `LoadingState`, `EmptyState`, `ErrorState`, `PageShell` y `StatusBadge`, presentacionales, con CSS Modules. Test-first por componente (rol/texto/variante); RED archivado en `docs/evidencias/red-C-25/`.
3. **Cliente de API** (D7/D9): `src/shared/api/client.ts` con `VITE_API_URL`, `fetch`, resultado discriminado, `ApiErrorPayload` (cuatro formas), `getApiErrorMessages` y `authProvider` nulo. Tests con `vi.stubGlobal("fetch", ...)` para éxito + `400`/`401`/`403`/`409`/`422`/`404`/`unknown` y para el header `Authorization` ausente/presente.
4. **Router y shell** (D3): `react-router-dom` v6 con `createBrowserRouter`, ruta `/` (`HomePage` que muestra tokens/estados base) y `*` (404). Test de humo sobre `App` con router.
5. **Docker** (D11): `frontend/Dockerfile` (`node:24-alpine`, `npm ci`, `dev --host 0.0.0.0`), servicio `frontend` en `docker-compose.yml` (puerto 5173, `env_file`, `VITE_API_URL`, volúmenes de código y `node_modules`, `depends_on: backend`). No tocar los servicios existentes. Probar HMR en Windows.
6. **Configuración de calidad** (D5/D16): scripts `dev`, `build`, `preview`, `test`, `test:run`, `typecheck`, `lint`; `docs/evidencias/mutaciones-C-25.py` y `trazabilidad-C-25.py`.
7. **Verificación y evidencias** (D16): `vitest-C-25.txt`, `typecheck-C-25.txt`, `lint-C-25.txt`, `mutaciones-C-25.txt`, `trazabilidad-C-25.txt` y `verify-C-25.md` (precondición, comandos, resultados, escenarios cubiertos, riesgos residuales). Confirmar que C-25 no tocó `backend/`, specs, KB ni `CHANGES.md`.

---

## 6. Resumen de recomendaciones (una línea cada una)

- **D1**: React 18 / TS 5 / Vite 5 (SU-10), versiones exactas + lockfile; Node `24-alpine` con `engines >=20`.
- **D2**: npm + `package-lock.json` versionado; `npm ci` en Docker.
- **D3**: estructura `features/shared/pages` de la KB + React Router 6 con `createBrowserRouter`, `/` y `*`.
- **D4**: Vitest + Testing Library + `user-event` + `jest-dom` sobre jsdom.
- **D5**: RED archivado + `tsc --noEmit` strict + ESLint + `mutaciones-C-25.py` y `trazabilidad-C-25.py` propios.
- **D6**: CSS custom properties + CSS Modules, system font stack y paleta de estados AA (azul/verde/gris/ámbar/rojo).
- **D7**: `fetch` nativo con wrapper tipado y `authProvider` nulo (token = C-26).
- **D8**: tipos de API a mano, mínimos; codegen recién en C-27.
- **D9**: unión discriminada de las cuatro formas de error + `getApiErrorMessages` con mensajes textuales.
- **D10**: componentes presentacionales; sólo se stubbea `fetch` en el test del cliente; sin MSW por ahora.
- **D11**: Dockerfile de dev, puerto 5173, volumen de código + `node_modules` anónimo, polling en Windows y `VITE_API_URL=http://localhost:8000/api`.
- **D12**: reutilizar `VITE_API_URL`/`CORS_ORIGIN`; `ImportMetaEnv` tipado; `envDir: ".."` con fallback.
- **D13**: no tocar `backend/`; sólo agregar el servicio `frontend` a Compose.
- **D14**: C-25 = andamiaje + diseño + cliente + estados + Docker; login y pantallas no entran.
- **D15**: humo + `ErrorState`/`EmptyState`/`LoadingState` + `StatusBadge` + tests del cliente.
- **D16**: evidencias `red-C-25/`, `vitest-C-25.txt`, `typecheck-C-25.txt`, `lint-C-25.txt`, mutaciones, trazabilidad y `verify-C-25.md`.

---

## 7. Versiones encontradas y estado del repo (al cierre del explore)

| Comando | Resultado |
|---------|-----------|
| `node --version` | **v24.19.0** |
| `npm --version` | **11.17.0** |
| `docker --version` | **Docker version 29.9.2, build a82e528** |
| `frontend/` | **no existe** |
| Rama | `main` |

`git status --short` (sin cambios realizados por este explore):

```
 M backend/app/api/appointments.py
 M backend/app/api/schemas.py
 M backend/app/repositories/users.py
 M backend/app/services/appointments.py
 M backend/tests/integration/test_user_repository.py
 M openspec/changes/api-ciclo-de-vida-del-turno/tasks.md
?? backend/tests/api/test_appointment_lifecycle_schemas.py
?? backend/tests/integration/test_api_appointment_cancel.py
?? backend/tests/integration/test_api_appointment_history.py
?? backend/tests/integration/test_api_appointment_reschedule.py
?? backend/tests/integration/test_api_appointment_status.py
?? backend/tests/integration/test_appointment_lifecycle_openapi.py
?? backend/tests/integration/test_appointment_lifecycle_services.py
?? docs/evidencias/baseline-C-23.txt
?? docs/evidencias/precondicion-C-23.txt
?? docs/evidencias/red-C-23/
?? docs/evidencias/trazabilidad-C-23.py
?? docs/evidencias/trazabilidad-C-23.txt
?? docs/evidencias/verify-C-23.md
```

> Los cambios de `backend/` corresponden a C-23 en curso (no son de este explore). El único archivo creado por este explore es **`docs/evidencias/explore-C-25.md`**.
