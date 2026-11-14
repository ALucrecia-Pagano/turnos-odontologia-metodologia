# Evidencia de Consulta a Context7 y Skill appointment-frontend-ux — Change C-36

> **Fecha**: 2026-11-14  
> **Change**: `ui-tema-oscuro-y-movil` (C-36)  
> **Rama**: `c36-apply`  

---

## 1. Skill `appointment-frontend-ux`

Se aplicó la skill `.agents/skills/appointment-frontend-ux/SKILL.md` para guiar la implementación de las interfaces móviles de la agenda. Principios aplicados:
1. **Regla C1 de pruebas**: Sin mocks de módulo (`vi.mock`), sin espías (`vi.spyOn`), sin stubs globales (`vi.stubGlobal`), sin fake timers (`vi.useFakeTimers`), sin MSW. Inyección de dependencias (`createApiClient`, `createFixedClock`, `createMemoryRouter`).
2. **Tokens de diseño**: Cero HEX ni `rgb()` sueltos en el código de producción. Toda dimensión y color proviene de `frontend/src/shared/styles/tokens.css` (incluyendo `--breakpoint-mobile: 640px`).
3. **Accesibilidad estricta**:
   - Estados con texto visible (`StatusBadge`), nunca únicamente mediante color.
   - Foco visible `:focus-visible` en todos los controles interactivos (botón "Menú", botón "Filtros", tarjetas de turno y botones de acción).
   - Área táctil mínima de 44×44 px en celular para todos los botones, selectores e inputs.
   - Tecla `Escape` cierra menús y modales retornando el foco al disparador.
4. **Prioridad en tarjetas angostas**:
   - Hora y paciente con prioridad sobre el estado.
   - Formato en dos líneas cuando la columna o carril es angosto.
5. **Verificación visual obligatoria**:
   - Capturas en navegador real a 1440 px, 768 px y 390 px antes de archivar.

---

## 2. Consulta a MCP Context7

Se consultó la documentación oficial de MDN Web Docs mediante el servidor MCP Context7:
- **Librería resuelta**: `/mdn/content` (MDN Web Docs)
- **Consulta**: `CSS scroll-snap-type mandatory with position sticky time gutter and dynamic viewport height dvh`

### Hallazgos Técnicos y Aplicación en C-36

1. **`scroll-snap-type: x mandatory`**:
   - *Documentación*: `mandatory` asegura que el contenedor de scroll siempre encaje en un snap point al detenerse el desplazamiento.
   - *Aplicación*: Se aplica a `.gridScrollContainer` en pantallas `<= 640px` junto con `scroll-snap-align: start` en cada columna (`.columnTrack` y `.columnHeader`). Esto asegura que el usuario en celular siempre vea una columna completa (profesional o día) y nunca quede recortada en una posición intermedia.

2. **Interacción de `scroll-snap` con `position: sticky`**:
   - *Documentación*: Un elemento hijo con `position: sticky; left: 0` flota sobre el contenido desplazado pero reduce el área visible efectiva del contenedor.
   - *Aplicación*: Se configura `scroll-padding-left: var(--agenda-time-gutter-width)` en `.gridScrollContainer` para que las columnas al encajar no queden solapadas debajo del canal horario de horas.

3. **Unidades de Viewport Dinámico (`dvh`)**:
   - *Documentación*: `dvh` (Dynamic Viewport Height) se recalcula automáticamente cuando las barras de navegación y dirección del navegador móvil se expanden o retraen.
   - *Aplicación*: Para la hoja inferior (bottom sheet) en `Dialog.module.css` y los modales de appointments, se utiliza `max-height: 90dvh` (con fallback de `90vh`) en lugar de `100vh`, evitando que los botones de acción ("Cancelar turno", "Guardar") queden tapados por la barra inferior de navegación en Safari iOS y Chrome Android.
