# Evidencia de Aplicación de Skill appointment-frontend-ux — Change C-31

> **Fecha**: 2026-11-14  
> **Change**: `ui-vista-de-recepcion-por-sillon` (C-31)  
> **Rama**: `c31-apply`  

---

## 1. Skill `appointment-frontend-ux`

Se aplicó la skill `.agents/skills/appointment-frontend-ux/SKILL.md` (y las skills de apoyo resueltas en `.atl/skill-registry.md`: `tdd`, `frontend-design`, `vitest`, `vercel-react-best-practices`) para guiar la implementación completa del modo de recepción por sillón (`view=chair`).

### Principios y directivas aplicadas

| Directiva de la skill | Cómo se aplicó en C-31 | Dónde se verifica |
|---|---|---|
| **Tokens únicamente** | Nuevos tokens en `tokens.css`: `--agenda-free-bg`, `--agenda-free-border`, `--agenda-free-color`, `--agenda-outside-bg`, `--agenda-outside-border`, `--agenda-outside-color`, `--agenda-card-chair-second-row-color`. Cero valores HEX o `rgb()` arbitrarios en TSX ni CSS Modules. | `frontend/src/shared/styles/tokens.css`, `AgendaGrid.module.css`; test `agendaChairStyles.test.ts` (escenario 09) |
| **Accesibilidad estricta** | Estado con texto visible (`StatusBadge`), nunca solo por color. Bloques de disponibilidad con texto visible dentro de la banda (`Libre HH:MM–HH:MM` o `Fuera de horario HH:MM–HH:MM`) y `aria-label` descriptivo. Tarjetas de turno con `aria-label` completo: hora, paciente, prestación, profesional, sillón y estado. Foco visible `:focus-visible` en tarjetas y botones. | `AgendaGrid.tsx`, `AgendaView.chair.test.tsx` (escenarios 09, 14, 15) |
| **Prioridad hora/paciente y profesional visible** | En la vista por sillón (`isChairView`), la tarjeta muestra el nombre del profesional a cargo en el cuerpo de la tarjeta (`.cardProfessional`), manteniendo la jerarquía hora > paciente > profesional > estado sin recortar en columnas angostas (`cqi`). | `AgendaGrid.tsx`, `AgendaGrid.module.css`, `AgendaView.chair.test.tsx` (escenario 03) |
| **Mismo contenedor de grilla de día/semana** | La vista por sillón reutiliza `AgendaGrid` (`.gridScrollContainer`), heredando el comportamiento responsive de C-36: `scroll-snap-type: x mandatory`, columna completa con `cqi`, canal de horas sticky a la izquierda con `z-index: 5` por encima de las tarjetas y `scroll-padding-left`. | `AgendaView.tsx`, `AgendaGrid.tsx`, `AgendaGrid.module.css` |
| **Confinamiento del token de sesión** | Ningún componente o módulo nuevo accede a `localStorage`, `sessionStorage` o al JWT directamente. El token se confina en `features/auth/tokenStore.ts`. Las pruebas usan `createMemoryTokenStore`. | `grep` de storage/token; tests en `AgendaPage.porSillon.test.tsx` |
| **Zona horaria de la API** | Toda conversión de instantes ISO UTC a minutos y etiquetas de hora local se realiza con `America/Argentina/Buenos_Aires` (`DEFAULT_AGENDA_TIMEZONE`). El reloj se inyecta mediante `createFixedClock`. | `agendaChairLayout.ts`, `AgendaPage.tsx`, tests de layout y página |
| **Regla C1 de pruebas** | Sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers`, fake timers ni MSW. Dependencias inyectadas: `createApiClient({ fetchFn })`, `createFixedClock(nowIso)`, `createMemoryRouter + RouterProvider`. | Suite completa de tests nuevos de C-31 |
| **Verificación visual responsive (1440 / 768 / 390 px)** | Reorganización de la toolbar en 390 px: los controles de navegación entran en el ancho disponible sin scroll horizontal de la página. El modo Sillones no rompe la distribución en móvil ni los tests de C-36. | `AgendaToolbar.tsx`, `AgendaToolbar.chair.test.tsx`, capturas pendientes para la fase visual |

---

## 2. Lecciones y decisiones de diseño de C-31

1. **Reutilización del contenedor de grilla**:
   En lugar de crear una grilla separada, la vista Sillones alimenta `AgendaGrid` con columnas agrupadas por sillón (`groupByChair`), garantizando consistencia visual, eje horario compartido y scroll fluido con snap en móviles.
2. **Bandas de disponibilidad vs tarjetas de turno**:
   Los huecos libres y tramos fuera de horario se renderizan como bandas de disponibilidad no interactivas (`aria-hidden="false"`, con texto explícito de horario), posicionadas de forma absoluta en el track de la columna de manera análoga a los turnos, respetando el cálculo de minutos del eje horario.
3. **Distribución en pantallas angostas (390 px)**:
   A 390 px, el grupo de botones `[Día | Semana | Sillones]` y `‹ Hoy ›` se mantiene en la primera fila con espaciados compactos basados en tokens (`--space-2`), ocupando ~308 px dentro de los 374 px útiles de la pantalla, sin provocar desbordamiento horizontal ni requerir scroll dentro de la barra de herramientas.
