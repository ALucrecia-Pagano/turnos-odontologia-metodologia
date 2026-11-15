# Evidencia de Aplicación de Skill appointment-frontend-ux y MCP Context7 — Change C-32

> **Fecha**: 2026-11-14  
> **Change**: `ui-horarios-y-bloqueos` (C-32)  
> **Rama**: `c32-apply`  

---

## 1. Skill `appointment-frontend-ux`

Se aplicó la skill `.agents/skills/appointment-frontend-ux/SKILL.md` (junto con `tdd`, `frontend-design`, `vitest` y `vercel-react-best-practices`) para guiar la implementación completa de la pantalla de horarios y bloqueos (`/horarios`).

### Principios y directivas aplicadas

| Directiva de la skill | Cómo se aplicó en C-32 | Dónde se verifica |
|---|---|---|
| **Tokens únicamente** | Todos los colores, radios, espaciados, bordes y tipografías consumen variables de `tokens.css` (`var(--color-*)`, `var(--space-*)`, `var(--radius-*)`, `var(--font-*)`). Inputs y selects declaran `font-family: inherit`. Cero valores HEX o `rgb()` sueltos en TSX o CSS Modules. | `frontend/src/features/horarios/*.module.css` |
| **Accesibilidad estricta** | Estado de los turnos afectados comunicado siempre con texto visible (`StatusBadge`), nunca solo por color. Agrupación por día con `<fieldset>` y `<legend>`. Controles interactivos con foco visible `:focus-visible` y área táctil mínima de 44×44 px. Alertas de error y de turnos afectados con `role="alert"` y traslado de foco; confirmaciones de éxito en región `role="status"`. | `HorariosPage.tsx`, `WorkingHoursSection.tsx`, `BlocksSection.tsx`, `AffectedAppointments.tsx` |
| **Zona horaria desde la API** | La pantalla obtiene `timezone` consultando una sola vez `GET /api/agenda` en la carga inicial y la reutiliza para formatear fechas y horas locales (`Intl.DateTimeFormat` con `timeZone` explícito) y calcular el offset ISO (`buildStartAtIso`) al crear bloqueos. Cero constantes de timezone hardcodeadas en código productivo de `features/horarios/`. | `HorariosPage.tsx`, `horariosTime.ts`, test 15 en `HorariosPage.test.tsx` |
| **Confinamiento del token de sesión** | Ningún componente o módulo de `features/horarios/` toca `localStorage` ni `sessionStorage`. El token vive únicamente en `features/auth/tokenStore.ts` y las pruebas usan `createMemoryTokenStore`. | `HorariosPage.test.tsx`, `HorariosRoute.test.tsx` |
| **Regla C1 de pruebas** | Cero uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` ni MSW. Dependencias inyectadas por parámetro/prop: `createApiClient({ fetchFn })`, `createFixedClock`, `createMemoryRouter + RouterProvider`. | Suite completa de tests nuevos de C-32 (`src/features/horarios/*.test.ts(x)`) |
| **Adaptabilidad 1440 / 768 / 390 px** | Layout en 2 columnas a 1440 px y 1 columna apilada en 768 px y 390 px sin scroll horizontal. Modal `BlockFormDialog` y `BlockDeleteDialog` sobre `Dialog.tsx` funcionando como hoja inferior (*bottom sheet*) a ≤ 640 px. | `HorariosPage.module.css`, `BlockFormDialog.module.css`, `BlockFormDialog.mobile.test.tsx` |

---

## 2. Consulta al MCP `context7`

Siguiendo el procedimiento de la skill (`resolve-library-id` → `query-docs`), se consultó la documentación oficial de **React Router v6** (`react-router-dom@6.30.6`):

1. **`resolve-library-id`**:
   - `libraryName`: `"react-router-dom"`
   - `query`: `"useSearchParams and createMemoryRouter in React Router v6"`
   - **Resultado**: ID seleccionado `/websites/reactrouter/6.30.3` (reputación High, versión v6 correspondiente a `6.30.x`).
2. **`query-docs`**:
   - `libraryId`: `"/websites/reactrouter/6.30.3"`
   - `query`: `"useSearchParams setSearchParams replace option and createMemoryRouter in React Router v6"`
   - **Confirmación técnica**:
     - `useSearchParams()` devuelve `[URLSearchParams, SetURLSearchParams]`, donde `setSearchParams(nextInit, { replace: true })` actualiza el query string (`?professionalId=...`) sincronizando la URL sin apilar entradas redundantes o según la navegación del selector.
     - `createMemoryRouter(routes, { initialEntries })` junto con `<RouterProvider router={router} />` permite evaluar la ruta protegida `/horarios` y los parámetros de búsqueda en pruebas bajo la Regla C1 sin mocks de módulo.
