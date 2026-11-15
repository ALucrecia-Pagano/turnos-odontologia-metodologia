# Evidencia de Aplicación de Skill appointment-frontend-ux y MCP Context7 — Change C-33

> **Fecha**: 2026-11-15  
> **Change**: `ui-catalogos-y-pacientes` (C-33)  
> **Rama**: `c33-apply`  

---

## 1. Skill `appointment-frontend-ux`

Se aplicó la skill `.agents/skills/appointment-frontend-ux/SKILL.md` (junto con `tdd`, `frontend-design`, `vitest` y `vercel-react-best-practices`) para guiar la implementación completa de las pantallas de pacientes (`/pacientes`) y catálogos (`/catalogos`).

### Principios y directivas aplicadas

| Directiva de la skill | Cómo se aplica en C-33 | Dónde se verifica |
|---|---|---|
| **Tokens únicamente** | Todos los colores, radios, espaciados, bordes y tipografías consumen variables preexistentes de `tokens.css` (`var(--color-*)`, `var(--space-*)`, `var(--radius-*)`, `var(--font-*)`). Inputs y selects declaran `font-family: inherit`. Cero valores HEX o `rgb()` sueltos en TSX o CSS Modules. Prohibidos `--color-ice` y tokens `*-on-navy` (pantallas sobre fondo claro). | `frontend/src/features/pacientes/*.module.css`, `frontend/src/features/catalogos/*.module.css`, escenarios 05 y 06 (`catalogosPacientesStyles.test.ts`) |
| **Accesibilidad estricta** | Estado de ítems de catálogo comunicado siempre con texto visible mediante `ActiveBadge` ("Activo" / "Inactivo"), nunca solo por color. Tablas semánticas `<table>` con `<caption>` y `<th scope="col">`. Controles interactivos con foco visible `:focus-visible` y área táctil mínima de 44×44 px. Alertas de error con `role="alert"` y foco trasladado; confirmaciones de éxito en una única región `role="status"` siempre montada. | `ActiveBadge.tsx`, `PacientesPage.tsx`, `CatalogosPage.tsx`, `CatalogSection.tsx`, `PatientFormDialog.tsx`, `CatalogFormDialog.tsx`, `CatalogConfirmDialog.tsx` |
| **Sin fechas/horas (o zona horaria de API)** | Las pantallas de pacientes y catálogos no muestran fechas ni horas de turnos. Si en alguna extensión se requiriese formatear una fecha, se utilizará `Intl.DateTimeFormat("es-AR", { timeZone })` con la zona horaria provista por la API. | `pacientesApi.ts`, `catalogosApi.ts` |
| **Confinamiento del token de sesión** | Ningún componente o módulo de `features/pacientes/` ni `features/catalogos/` accede a `localStorage` ni `sessionStorage`. El token vive únicamente en `features/auth/tokenStore.ts` y las pruebas usan `createMemoryTokenStore`. | `PacientesPage.test.tsx`, `CatalogosPage.test.tsx`, `CatalogosPacientesRoutes.test.tsx` |
| **Regla C1 de pruebas** | Cero uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` ni MSW. Dependencias inyectadas por parámetro/prop: `createApiClient({ fetchFn })`, `createMemoryRouter + RouterProvider`, `createMemoryTokenStore`. | Suite completa de tests nuevos de C-33 (`src/features/pacientes/*.test.ts(x)`, `src/features/catalogos/*.test.ts(x)`) |
| **Adaptabilidad 1440 / 768 / 390 px** | Tablas semánticas apiladas en celular con `data-label` a ≤ 640 px sin scroll horizontal de página. Modales de formulario `PatientFormDialog` y `CatalogFormDialog` operando como hoja inferior (*bottom sheet*) a ≤ 640 px mediante `Dialog.tsx`. | `PacientesPage.module.css`, `CatalogSection.module.css`, escenarios 10 y 28 |

---

## 2. Consulta al MCP `context7`

Todas las APIs de **React Router v6** (`react-router-dom@6.30.6`), **React 18** (`react@18.3.1`) y **Testing Library** (`@testing-library/react@16.3.3`) necesarias para C-33 ya se encuentran en uso activo y comprobado en el repositorio (patrones de `useSearchParams` de `AgendaToolbar.tsx` y `HorariosPage.tsx`, `createMemoryRouter` y `RouterProvider` en `HorariosPage.test.tsx`, `createApiClient` en `client.ts`, componentes `Dialog`, `LoadingState`, `ErrorState`, `EmptyState` y `PageShell`).

Por ende, **no se requirieron consultas adicionales al MCP `context7`** en este change, declarándose formalmente que no hubo consultas nuevas ya que no se introducen APIs no cubiertas previamente en el proyecto.
