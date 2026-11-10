# Proposal

## Why

Las secretarias y los administradores del consultorio necesitan dar turnos mientras visualizan la agenda diaria o semanal. Hoy la interfaz (`frontend/`) solo expone la consulta de agenda de solo lectura (C-27 y C-28). La especificación del sistema (US-042, Flujo 1 en KB 07 y lineamientos de Frontend Cuidado en KB 08) exige que el formulario de alta permita elegir paciente, profesional, sillón, prestación, fecha, hora y duración, y que ante cualquier rechazo del dominio muestre las violaciones tal cual las devuelve la API (código estable, mensaje en español y referencia al turno o bloqueo en conflicto). C-29 implementa este formulario modal sobre la agenda sin repetir reglas de negocio en el cliente, respetando estrictamente los roles de acceso (recepción y administrador) y la regla de no modificar tests existentes.

## What Changes

- **Acceso modal desde la agenda**: Se agrega un botón principal accesible `"Nuevo turno"` en `AgendaToolbar` (mediante prop opcional `onNewAppointment`), visible y habilitado únicamente para los roles con permiso (`recepcion` y `administrador`), montando el formulario en un `<dialog>` modal sobre `AgendaPage`.
- **Reutilización de la primitiva `Dialog`**: Se utiliza `frontend/src/shared/components/Dialog.tsx` creado en C-35, que provee `<dialog>` nativo con `showModal()`, tecla Escape, backdrop nativo y fallback con atributo `open` para el entorno `jsdom` de Vitest, sin focus trap manual redundante.
- **Búsqueda accesible de pacientes**: Campo de búsqueda textual con botón explícito `"Buscar paciente"` (y tecla `Enter`) que consulta `GET /api/patients?query=`, sin combobox, sin debounce ni timers. Despliega los resultados como un grupo de radio buttons (`name="patientId"`) con nombre y DNI formateado. Si no hay coincidencias, muestra un aviso accesible.
- **Prellenado contextual**: Al abrirse, el formulario preselecciona la fecha activa de la agenda (`effectiveDate`), el profesional activo en el filtro (o en la vista semanal) y el sillón activo en el filtro.
- **Sugerencia y edición de duración**: Al elegir una prestación de `GET /api/services`, el campo de duración se inicializa con `defaultDurationMin` de dicha prestación y puede editarse libremente en múltiplos de 5 minutos (rango 5 a 480 min).
- **Entrada de fecha, hora y zona horaria**: Inputs nativos `<input type="date">` e `<input type="time" step="300">`. Al enviar, se compone `startAt` en formato ISO con el offset exacto (`-03:00`) calculado mediante `Intl.DateTimeFormat` nativo para la fecha y hora elegidas y el `timezone` provisto por la API, sin dependencias externas.
- **Renderizado fiel de violaciones**: Resumen superior con `role="alert"` y foco programático al fallar. Presenta íntegramente los mensajes textuales del backend (US-042 CA-1) junto con sus códigos estables y las referencias al turno o bloqueo que colisiona (`conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval`).
- **Mapeo de errores 400**: Errores de entrada malformada (`400 { errors: [...] }`) marcan con `aria-invalid="true"` únicamente los campos correspondientes. Las violaciones de dominio (`409` y `422`) se muestran en el alert de resumen y no se mapean a campos individuales.
- **Éxito y actualización accesible**: Al recibir `201 Created`, el diálogo se cierra, se invoca `refresh` de `useAgenda`, se anuncia el éxito con `role="status"` (`aria-live="polite"`) y el foco retorna al botón `"Nuevo turno"`.
- **Extensión de contratos de API**: Se actualizan las interfaces en `shared/api/types.ts` y el parser `asViolations` en `client.ts` para capturar campos opcionales de conflicto de las violaciones sin alterar tests existentes.

## Capabilities

### New Capabilities

- `frontend-appointment-form`: Formulario modal de alta de turnos para recepción y administración con búsqueda de pacientes por radio buttons, duración sugerida, cálculo de offset horario, renderizado íntegro de violaciones del dominio y actualización accesible.

### Modified Capabilities

- `frontend-agenda`: La barra de navegación de la agenda (`AgendaToolbar`) incorpora la acción `"Nuevo turno"` para recepción y administrador, y la vista refresca su contenido al completarse el alta.

## Out of Scope

- Reprogramación de turnos, cancelación y transiciones de estado (`confirmado`, `atendido`, `ausente`), que corresponden a C-30 (`ui-reprogramar-cancelar-y-estados`).
- Habilitar el ítem "Turnos" en el menú principal: `menuFor.ts` conserva "Turnos" deshabilitado con `"Próximamente"` para no romper los tests existentes de `menuFor.test.ts` y `AppShell.test.tsx`.
- Arreglo de fallos preexistentes en tests no vinculados (ej. `Logout.test.tsx`).
- Creación de nuevos pacientes, profesionales, sillones o prestaciones desde este formulario (corresponde a C-33).
- Validación de reglas de solapamiento o de horarios en el cliente: el frontend no duplica la lógica del dominio puro.

## Impact

- **Código nuevo**:
  - `frontend/src/features/appointments/AppointmentFormDialog.tsx` (+ `AppointmentFormDialog.module.css` y `AppointmentFormDialog.test.tsx`)
  - `frontend/src/features/appointments/PatientSearchGroup.tsx` (+ `PatientSearchGroup.module.css` y `PatientSearchGroup.test.tsx`)
- **Código modificado**:
  - `frontend/src/features/agenda/AgendaToolbar.tsx` (prop opcional `onNewAppointment` y botón visible según rol)
  - `frontend/src/features/agenda/AgendaPage.tsx` (integración del modal con el estado de `useAgenda`)
  - `frontend/src/shared/api/types.ts` (extensión de `Violation` con campos opcionales de conflicto)
  - `frontend/src/shared/api/client.ts` (captura de campos opcionales en `asViolations`)
- **Sin cambios**: `frontend/src/features/auth/menuFor.ts`, `frontend/src/shared/components/AppShell.tsx`, `frontend/src/features/agenda/AgendaGrid.tsx`, `frontend/src/App.tsx`, backend, base de datos y variables de entorno.
- **Tests existentes**: Se preservan intactos todos los tests existentes (`menuFor.test.ts`, `AppShell.test.tsx`, `AgendaToolbar.test.tsx`, `AgendaView.test.tsx`, `client.test.ts`, etc.).
