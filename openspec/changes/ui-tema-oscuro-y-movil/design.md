# Design: ui-tema-oscuro-y-movil

## Context

La portada pública y el diálogo de acceso se adaptaron completamente a móvil y tema oscuro en C-35. Sin embargo, la aplicación autenticada (`/agenda`) fue diseñada primordialmente para escritorio y tablet. Al ejecutarse en pantallas móviles (390 px, típico en teléfonos inteligentes), la interfaz colapsa visualmente: la barra superior `AppShell` ocupa 3 renglones con navegación horizontal truncada, la barra de herramientas `AgendaToolbar` se quiebra en 5 renglones consumiendo más del 60% del alto visible, la grilla `AgendaGrid` solo deja visible 1.25 columnas cortando nombres a la mitad, y los modales flotantes centrados sufren de compresión lateral y desborde vertical que corta botones de acción en el borde inferior.

Ver motivación completa en `proposal.md` y diagnóstico detallado con citas exactas de código en `docs/evidencias/explore-C-36.md`.

## Goals / Non-Goals

**Goals:**
- Adaptar `AppShell` a pantallas móviles (<= 640 px) con cabecera compacta de una sola fila y menú desplegable accesible.
- Compactar `AgendaToolbar` en dos filas principales con filtros plegables mediante botón "Filtros" con contador de filtros activos.
- Implementar desplazamiento horizontal asistido con `scroll-snap-type: x mandatory` y columna de horas fija (`position: sticky`) en `AgendaGrid`, dimensionando cada columna al ancho útil.
- Transformar la primitiva `Dialog` y los 3 modales de turnos (`AppointmentFormDialog`, `AppointmentDetailDialog`, `AppointmentRescheduleDialog`) en hojas inferiores (bottom sheet) a ancho completo en pantallas <= 640 px.
- Mantener 100% intactos los tests existentes de `AppShell.test.tsx`, `menuFor.test.ts`, `AgendaToolbar.test.tsx`, `AgendaView.test.tsx` y modales.

**Non-Goals:**
- Tema oscuro de la aplicación autenticada: Queda explícitamente fuera de alcance (backlog post-entrega). Respeta la Decisión A de C-35 de mantener superficies claras suaves para la agenda operativa y sus modales. La portada y el acceso ya son oscuros.
- Modificar endpoints de backend, modelos de base de datos ni contratos de API REST.
- Nuevas dependencias externas o paquetes de npm (se resuelve 100% con CSS nativo y React 18).

## Decisions

### D1 — Scope Reenfocado en Celular de la App (Decisión B)
- **Decisión**: C-36 se reenfoca en la adaptabilidad móvil de la aplicación autenticada. El tema oscuro de la app queda fuera y se traslada al backlog post-entrega.
- **Justificación**: En C-35 se estableció la Decisión A (modales y agenda claros suaves), y la portada y el login ya son oscuros por diseño. El dolor real evidenciado en las capturas es la inoperabilidad de la agenda en celular.
- **Alternativas consideradas**: Incluir tema oscuro en este change (descartado por sobrecarga de alcance y contradicción visual con la decisión A de C-35); dividir en dos changes C-36 y C-37 (descartado para no alterar el roadmap antes de la entrega).

### D2 — Barra Superior en Celular (`AppShell`, Decisión B)
- **Decisión**: En pantallas móviles (<= 640 px), la cabecera agrupa la marca Aqua y el bloque de sesión en una fila compacta. Se incorpora un botón interactivo "Menú" (`aria-expanded`, `aria-controls="main-menu"`) ubicado **estrictamente FUERA de `<nav>`**. Al activarse, muestra u oculta el elemento `<nav id="main-menu">`; la tecla `Escape` cierra el menú y devuelve el foco al botón.
- **Justificación**: `AppShell.test.tsx:67` ejecuta `within(nav).getAllByRole("button")` esperando exactamente 5 botones ("Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes", "Usuarios y roles"). Si se colocara un botón dentro de `<nav>`, el test fallaría con longitud 6. Ubicándolo en `<header>` fuera de `<nav>`, y manteniendo `<nav>` en el DOM, los tests existentes pasan intactos sin modificación. En escritorio (> 640 px), el botón "Menú" se oculta con `display: none` y `<nav>` se muestra horizontal como siempre.
- **Alternativas consideradas**: Scroll horizontal de navegación sin botón (descartado: no resuelve el desborde ni la altura excesiva); Bottom navigation bar (descartado: requeriría iconos nuevos y reestructuración de rutas).

### D3 — Toolbar de la Agenda en Celular (`AgendaToolbar`, Decisión A)
- **Decisión**: En pantallas <= 640 px, `AgendaToolbar` se organiza en dos filas principales: Fila 1 = selector [Día | Semana] + botones temporales [Anterior | Hoy | Siguiente]; Fila 2 = campo Fecha + botón [Nuevo turno] (si el rol lo permite). Los selectores de Profesional, Sillón y Limpiar filtros se agrupan en un panel plegable controlado por un botón "Filtros" con `aria-expanded` y contador en texto (por ej. `"Filtros (1)"` si hay un sillón o profesional filtrado).
- **Justificación**: En el DOM, los elementos `<select>` de Profesional y Sillón y el botón "Limpiar filtros" siguen siempre presentes. En escritorio y en jsdom por defecto, la sección de filtros permanece visible y expandida (`display: flex`), garantizando que `AgendaToolbar.test.tsx` continúe encontrando `screen.queryByLabelText("Profesional")` y probando sus opciones sin romper ningún test.
- **Alternativas consideradas**: Dejar los 5 renglones con paddings más pequeños (descartado: sigue ocupando demasiada altura); Botón flotante para nuevo turno (descartado: oculta turnos en la grilla inferior).

### D4 — Grilla con Scroll-Snap y Ancho Útil en Celular (`AgendaGrid`, Decisión A sin selector nuevo)
- **Decisión**: En pantallas <= 640 px, `.gridScrollContainer` incorpora `scroll-snap-type: x mandatory` y `scroll-padding-left: var(--agenda-time-gutter-width)`. La columna de horas (`timeGutter`) se mantiene fija a la izquierda (`position: sticky; left: 0; z-index: 2`). Cada columna de profesional (o día) se dimensiona al ancho útil de la pantalla (`min-width: calc(100vw - var(--agenda-time-gutter-width) - 2 * var(--space-4))`), de modo que cada deslizamiento encaja magnéticamente mostrando una columna completa. El modo por defecto de `AgendaView` sigue siendo `"grid"`.
- **Justificación**: No se añade un selector de profesional nuevo porque el filtro de Profesional de la toolbar ya cubre la selección específica. El scroll-snap nativo permite deslizar entre profesionales con suavidad táctil sin cortar nombres. Al mantener `"grid"` como modo por defecto, se preservan intactos todos los tests de `AgendaView.test.tsx`.
- **Alternativas consideradas**: Forzar la vista de lista `AgendaTable` en móvil (descartado: rompería las aserciones de `AgendaView.test.tsx` en jsdom y perdería la visualización de solapamientos); Achicar columnas a 100 px (descartado: ilegible).

### D5 — Modales como Hoja Inferior (Bottom Sheet, Decisión A)
- **Decisión**: En pantallas <= 640 px, la primitiva `Dialog` ([Dialog.module.css](file:///c:/Users/hp/METODOLOGIA_TPS/turnos-odontologia/frontend/src/shared/components/Dialog.module.css)) y los modales derivados (`AppointmentDetailDialog`, `AppointmentFormDialog`, `AppointmentRescheduleDialog`) se presentan como hoja inferior (bottom sheet):
  - `.dialog[open]` aplica `align-items: flex-end; padding: 0;`.
  - El contenedor aplica `width: 100%; max-width: 100%; border-radius: var(--radius-lg, 16px) var(--radius-lg, 16px) 0 0; border-bottom: 0; max-height: 90dvh; overflow-y: auto;`.
  - En `AppointmentDetailDialog`, las acciones se organizan para que sean cómodas al tacto (44 px) sin quedar cortadas por el borde inferior.
  - En pantallas de 768 px y superiores, se conserva el modal centrado flotante de 580 px con bordes completos.
- **Justificación**: Resuelve el defecto visible en `C-30-detalle-390.png` donde los botones de acción se cortaban en la parte inferior, y aprovecha el 100% del ancho del teléfono (390 px) eliminando los 64 px de márgenes desperdiciados.
- **Alternativas consideradas**: Mantener modal flotante achicando márgenes (descartado: sigue viéndose como una tarjeta comprimida y no resuelve la ergonomía del pulgar).

## Risks / Trade-offs

- **[Riesgo: jsdom no evalúa Media Queries ni CSS layout]** → **Mitigación**: Los tests unitarios con Vitest validan atributos de accesibilidad (`aria-expanded`, `aria-controls`), presencia de elementos en el DOM, clases CSS asignadas y estados de React. La geometría real y la ausencia de desbordes se validan obligatoriamente mediante verificación visual con capturas reales a 1440 px, 768 px y 390 px a cargo de Claude.
- **[Riesgo: Romper `within(nav).getAllByRole("button")` en `AppShell.test.tsx`]** → **Mitigación**: El botón "Menú" se ubica en `<header>` fuera de `<nav>`. `<nav>` mantiene exactamente su estructura de lista y botones existentes.
- **[Riesgo: Romper `AgendaView.test.tsx` si se cambia el modo por defecto]** → **Mitigación**: `AgendaView` mantiene `const [viewMode, setViewMode] = useState<"grid" | "list">("grid")` inalterado.
- **[Riesgo: Safe-area en dispositivos móviles modernos]** → **Mitigación**: Se incorpora soporte de `env(safe-area-inset-bottom)` en el padding inferior de la hoja modal para evitar colisiones con barras de navegación nativas de iOS/Android.

## Migration Plan

No requiere migraciones de base de datos ni modificaciones en el backend. Los cambios se confinan exclusivamente a CSS Modules y componentes TSX de `frontend/src/shared/` y `frontend/src/features/agenda/` y `frontend/src/features/appointments/`.
Rollback directo revirtiendo los archivos modificados.

## Open Questions

*(Ninguna. Todas las decisiones D1–D6 quedaron resueltas en explore-C-36.md).*
