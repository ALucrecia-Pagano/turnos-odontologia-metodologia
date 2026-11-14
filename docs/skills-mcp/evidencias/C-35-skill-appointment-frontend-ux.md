# C-35 — Aplicación de `appointment-frontend-ux` (y skills de apoyo)

Skill leída: `.agents/skills/appointment-frontend-ux/SKILL.md`. Skills de apoyo resueltas desde `.atl/skill-registry.md`: `tdd`, `frontend-design`, `vercel-react-best-practices` (solo reglas de SPA), `vitest` (la regla C1 del proyecto prevalece sobre su guía de mocks y fake timers).

| Directiva de la skill | Cómo se aplicó en C-35 | Dónde se verifica |
|---|---|---|
| Tokens únicamente: sin HEX/rgb ni tamaños fijos en TSX ni CSS Modules | Todo color, sombra, desenfoque y medida nueva se define en `tokens.css` (tabla "Tokens nuevos de C-35" en `design.md`). Los CSS Modules nuevos y editados solo usan `var(--token)`; los únicos `rgba` que quedan en `LoginPage.module.css` son el overlay y el botón del carrusel heredados de C-34 | `grep` de HEX/`rgba` en los CSS de C-35 (sin hallazgos nuevos); test del escenario 10 |
| Accesibilidad: foco visible, nombres accesibles completos, controles >= 44x44 px | Enlaces de portada, tarjetas de `/acceso`, campos y botón del login y enlaces del `AppShell` con `min-height: 44px` y `:focus-visible` con contorno `--color-ice` (sobre navy) o `--color-focus` (sobre claro). Las tarjetas de rol usan `aria-labelledby` (nombre = rol) y `aria-describedby` (detalle). La flecha del botón "Ingresar" es `aria-hidden` para que el nombre accesible siga siendo "Ingresar" | Tests 05, 07, 12 y 13; `LoginPage.test.tsx` intacto |
| Confinamiento del token: solo `features/auth/tokenStore.ts` | Ningún archivo nuevo toca `sessionStorage` ni el token; los tests usan `createMemoryTokenStore` | `grep` y `tokenStore.test.ts` |
| Regla C1: sin `vi.mock`/`spyOn`/`stubGlobal`/fake timers/MSW; `fetch` y `Clock` inyectados | Ticker del carrusel, detección de reduced motion y observador de intersección se inyectan por props (`LandingPage`, `RevealSection`); `fetch` por `FetchFn`; reloj por `createFixedClock`. No se asigna ni se borra ningún global | `grep` sobre los tests nuevos |
| `createMemoryRouter`/`MemoryRouter` y datos ficticios literales | Escenarios 01, 02, 05, 06, 07-09 usan `createMemoryRouter`; las páginas aisladas, `MemoryRouter`. Usuarios y contraseñas ficticios (`<contraseña de prueba>`) | Tests de C-35 |
| Context7 antes de APIs sensibles a la versión | Ver `C-35-mcp-context7.md` | — |

## Lecciones de C-30 aplicadas

- **Diálogos sin superficie**: los modales tienen superficie propia (`--surface-ivory-ice` + borde de 1 px + sombra) en cada contenedor; el `Dialog` aporta solo el `::backdrop`. El test del escenario 11 lo exige por archivo.
- **Foco que cae en `<body>`**: no se modificó ningún `Dialog.tsx` ni el manejo de foco; solo CSS. `Dialog.test.tsx`, `Dialog.escape.test.tsx` y los tests de los diálogos de turnos quedaron intactos y en verde.
- **Escape**: sin cambios de comportamiento (solo estilos); la regresión de modales (`green-C-35/modales-regresion.txt`) lo confirma.
- **Títulos cortados en 390 px**: el contenedor del formulario pasó de `max-height: 90vh` a `calc(100dvh - 2 * var(--space-4))` (igual que los otros dos diálogos), con desplazamiento interno; la verificación real a 390 px queda para las capturas de la fase 9.
