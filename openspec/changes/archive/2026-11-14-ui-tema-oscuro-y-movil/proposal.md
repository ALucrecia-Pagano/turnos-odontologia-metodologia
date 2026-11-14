# Proposal: ui-tema-oscuro-y-movil

## Why

La portada pública, la página de acceso y el diálogo de login ya quedaron completamente adaptados a celulares (390 px) y con estética oscura en C-35, pero la aplicación autenticada de la agenda presenta graves problemas de usabilidad móvil: la barra superior (`AppShell`) se quiebra en tres renglones con scroll horizontal truncado en el menú, la barra de herramientas (`AgendaToolbar`) ocupa más del 60% del alto visible con 5 renglones de controles, la grilla (`AgendaGrid`) corta las columnas de profesionales a la mitad, y los modales de turnos flotan comprimidos cortando botones de acción en el borde inferior. Es necesario optimizar la aplicación para su uso en teléfonos móviles (<= 640 px) y tablets (768 px) en el consultorio.

## What Changes

- **Reenfoque de C-36 en la aplicación móvil**: Se concentra el alcance en la adaptabilidad móvil de la aplicación autenticada de la agenda (`AppShell`, `AgendaToolbar`, `AgendaGrid` y modales de `appointments`).
- **Tema oscuro de la app fuera de alcance**: El tema oscuro para la app autenticada se posterga al backlog post-entrega (evita contradecir la decisión A de C-35 de mantener superficies claras suaves para la agenda y sus modales; la portada y el login ya son oscuros). El nombre del change (`ui-tema-oscuro-y-movil`) se preserva por coherencia con el roadmap, y `CHANGES.md` se actualizará al archivar.
- **Cabecera compacta y menú móvil accesible en `AppShell`**: Para anchos <= 640 px, la cabecera agrupa la marca y la sesión en una fila, incorporando un botón interactivo "Menú" (`aria-expanded`, `aria-controls="main-menu"`) ubicado fuera de `<nav>`. El botón abre y cierra el menú accesible sin alterar la estructura DOM de `<nav>` requerida por los tests existentes; la tecla `Escape` cierra el menú y devuelve el foco.
- **Toolbar compacta con filtros plegables en `AgendaToolbar`**: Para anchos <= 640 px, los controles se distribuyen en dos filas principales (navegación/vista y fecha/nuevo turno), y los filtros de Profesional y Sillón se pliegan bajo un botón accesible "Filtros" que exhibe el conteo de filtros activos ("Filtros (N)"). En escritorio y jsdom, los filtros permanecen visibles en el DOM.
- **Grilla móvil con desplazamiento fluido `scroll-snap` en `AgendaGrid`**: En pantallas <= 640 px, el contenedor de la grilla incorpora `scroll-snap-type: x mandatory`, la columna de horas se mantiene fija a la izquierda (`position: sticky`), y cada columna de profesional o día se ajusta al ancho útil de la pantalla para permitir lectura completa de una columna a la vez. El modo por defecto de `AgendaView` sigue siendo `"grid"`.
- **Modales como hoja inferior (bottom sheet) en `Dialog` y `appointments`**: Para anchos <= 640 px, la primitiva `Dialog` y los modales de turnos (`AppointmentFormDialog`, `AppointmentDetailDialog`, `AppointmentRescheduleDialog`) se anclan al fondo como hoja inferior a ancho completo (100%), con esquinas superiores redondeadas, altura máxima de 90dvh, scroll interno y botones táctiles al alcance del pulgar sin cortes. En >= 768 px se preserva el modal centrado flotante de 580 px.

## Capabilities

### New Capabilities

*(Ninguna. Se modifican capacidades existentes de frontend).*

### Modified Capabilities

- `frontend-foundation`: Adaptación móvil de `AppShell` con cabecera compacta y botón "Menú" accesible fuera de `<nav>`, y adaptación de `Dialog` (y modales de turnos) como hoja inferior (bottom sheet) a ancho completo en <= 640 px.
- `frontend-agenda`: Compactación de `AgendaToolbar` en <= 640 px con panel de filtros plegable y contador activo, y desplazamiento horizontal asistido en `AgendaGrid` con `scroll-snap-type: x mandatory`, columna horaria sticky y ancho útil completo por columna.

## Impact

- **Código afectado**:
  - `frontend/src/shared/styles/tokens.css` (definición de `--breakpoint-mobile: 640px` y variables de bottom sheet).
  - `frontend/src/shared/components/AppShell.tsx` y `AppShell.module.css`.
  - `frontend/src/features/agenda/AgendaToolbar.tsx` y `AgendaToolbar.module.css`.
  - `frontend/src/features/agenda/AgendaGrid.tsx` y `AgendaGrid.module.css`.
  - `frontend/src/features/agenda/AgendaView.module.css`.
  - `frontend/src/shared/components/Dialog.module.css`.
  - `frontend/src/features/appointments/AppointmentDetailDialog.module.css`.
  - `frontend/src/features/appointments/AppointmentFormDialog.module.css`.
  - `frontend/src/features/appointments/AppointmentRescheduleDialog.module.css`.
- **Tests existentes**: Se mantienen 100% intactos y verdes (`AppShell.test.tsx`, `menuFor.test.ts`, `AgendaToolbar.test.tsx`, `AgendaToolbar.nuevoTurno.test.tsx`, `AgendaView.test.tsx`, `AgendaGrid.accionable.test.tsx`, `AgendaTable.test.tsx`, `Dialog.test.tsx`, etc.).
- **Tests nuevos**: Se agregan archivos específicos aislados para el comportamiento móvil (`AppShell.mobile.test.tsx`, `AgendaToolbar.mobile.test.tsx`, `AgendaGrid.mobile.test.tsx`, `Dialog.bottomSheet.test.tsx`).
- **Dependencias y APIs**: Sin librerías nuevas; uso de CSS nativo estándar (`scroll-snap`, `position: sticky`, `100dvh`).
