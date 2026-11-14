# C-35 — Consultas a Context7

Se consultó Context7 antes de escribir código sensible a la versión de las APIs (tarea 1.3). Consultas exactas:

| # | Herramienta | Entrada | Resultado usado |
|---|-------------|---------|-----------------|
| 1 | `resolve-library-id` | `libraryName: "React Router"`, `query: "React Router v6 index routes, nested routes, useSearchParams, createMemoryRouter"` | Se eligió `/websites/reactrouter` (incluye la versión 6.30.3, la API v6 que usa el proyecto con 6.30.6) |
| 2 | `query-docs` | `libraryId: "/websites/reactrouter"`, `query: "v6 useSearchParams read query param; route with element and children without path (layout route) and index route; createMemoryRouter"` | Rutas de layout sin `path`, rutas índice, firma de `createMemoryRouter` (`initialEntries`) y `useSearchParams` como par `[searchParams, setSearchParams]` |
| 3 | `resolve-library-id` | `libraryName: "MDN Web Docs CSS"`, `query: "backdrop-filter @supports not fallback and prefers-reduced-motion"` | Se eligió `/mdn/content` |
| 4 | `query-docs` | `libraryId: "/mdn/content"`, `query: "CSS backdrop-filter with @supports not (backdrop-filter: blur(1px)) solid fallback; prefers-reduced-motion: reduce media query"` | `@supports not (...)` para el fallback; `@media (prefers-reduced-motion: reduce)` con la regla posterior que gana por orden de fuente; `backdrop-filter` solo se ve si el fondo es translúcido |

## Qué cambió por las consultas

- **`useSearchParams` (v6)**: `LoginPage` lee `?rol` con `const [searchParams] = useSearchParams()` y `searchParams.get("rol")`; no se usa ninguna API de v7 (sin `useSearchParams` con `NavigateOptions` nuevas ni loaders).
- **Rutas**: el `/` conserva `routes[1]` con `path: "/"` y se mantiene como ruta de layout con hijos (`AppShell` sin `path` + índice `RootRedirect`); la ruta nueva `/acceso` se agrega al final. Los tests usan `createMemoryRouter(createAppRoutes(clock), { initialEntries })` según la firma consultada.
- **`@supports not`**: el fallback sólido se escribe como bloque `@supports not (backdrop-filter: blur(1px))` dentro del mismo CSS Module (login: `.card`; modales: `.dialog::backdrop` y la superficie de cada diálogo), después de la regla base, y los tests lo leen con un parser de bloques (`src/test/cssText.ts`).
- **`prefers-reduced-motion`**: los bloques `@media (prefers-reduced-motion: reduce)` van al final del archivo para ganar por orden de fuente (entrada del login, `RevealSection`, flechas y transiciones de la portada, `/acceso` y `AppShell`).
- **Por qué el blur importa solo con fondo translúcido**: de ahí que la tarjeta de login y los modales usen fondos `rgba(...)` (tokens `--surface-navy` y `--surface-ivory-ice`) y que el fallback sea un fondo opaco.
