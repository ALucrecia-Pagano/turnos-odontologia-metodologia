# Proposal

## Why

Una vez consultada la agenda diaria y semanal en la interfaz web (C-27, C-28) y habilitada la creación de nuevos turnos (C-29), el consultorio odontológico necesita gestionar el ciclo de vida de los turnos existentes directamente desde la agenda: confirmar asistencia, registrar atención o ausencia, cancelar turnos y reprogramarlos cuando surgen imprevistos, con auditoría completa de quién realizó cada cambio.

Actualmente, las tarjetas de turno en la grilla y las filas de la tabla son estáticas y pasivas; no es posible interactuar con ellas ni invocar los endpoints ya provistos por el backend en C-23 (`/{id}/status`, `/{id}/cancel`, `/{id}/reschedule`, `/{id}/history`). Este cambio habilita la interactividad accesible sobre la agenda y expone las acciones operativas con estricto apego al dominio y control de acceso (RBAC).

## What Changes

- **Turnos accionables en la agenda**:
  - En `AgendaGrid`, cada tarjeta de turno se implementa como un `<button type="button">` accesible con foco visible (`--color-focus`) y `aria-label` completo (horario, paciente, prestación, profesional, sillón y estado en texto visible).
  - En `AgendaTable`, cada fila incorpora un botón "Ver turno" al estar disponible la selección.
- **Diálogo modal de detalle del turno (`AppointmentDetailDialog`)**:
  - Montado sobre la primitiva accesible `Dialog.tsx`.
  - Muestra datos completos del turno en hora local según el `timezone` de la API: paciente, profesional, sillón, prestación, fecha, horario y `StatusBadge`.
  - Expone botones contextuales de acción con etiquetas exactas según estado y rol: "Confirmar turno", "Marcar atendido", "Marcar ausente", "Reprogramar" y "Cancelar turno", respetando la regla de un solo botón primario por vista.
  - En turnos en estado terminal (`atendido`, `ausente`, `cancelado`), muestra el texto explicativo: "Este turno ya no admite cambios." sin botones de mutación.
- **Panel de historial de cambios**:
  - Consulta `GET /api/appointments/{id}/history` y renderiza la lista cronológica con autor (`changedByName`), transición (`from → to`), fecha y hora en hora local, y desglose de reprogramación (intervalo anterior y nuevo) si aplica.
- **Cancelación con confirmación in-dialog**:
  - Subvista interna de confirmación ("¿Confirma que desea cancelar el turno de [Paciente]?") con botón destructivo "Confirmar cancelación" y "Volver al detalle", sin `window.confirm` ni campos innecesarios (la API no recibe cuerpo).
- **Reprogramación de turnos (`AppointmentRescheduleDialog`)**:
  - Diálogo modal dedicado con paciente y prestación fijos (solo lectura).
  - Campos editables: fecha, hora, profesional, sillón y duración (múltiplo de 5 min).
  - Envío a `POST /api/appointments/{id}/reschedule` y revalidación de solapamientos (RN-AG) en el dominio.
- **Control de acceso por rol (RBAC)**:
  - Recepción y Administrador: acceso a todas las acciones sobre cualquier turno.
  - Odontólogo: acceso de estado únicamente sobre turnos propios (`user.professionalId === appointment.professionalId`); en turnos ajenos, vista estrictamente de solo lectura sin consulta de historial (evitando 403 innecesarios). No puede cancelar ni reprogramar.
- **Gestión uniforme de errores de dominio**:
  - Respuestas 409, 422 y 403 presentadas en alerta superior con `role="alert"`, preservando el código y el mensaje en español devueltos por el backend, con traslado automático de foco.
  - Respuestas 400 mapeadas con `aria-invalid="true"` a campos específicos en el formulario de reprogramación.
- **Anuncios accesibles y refresco**:
  - Tras cada acción exitosa, se invoca `useAgenda().refresh()` y la región permanente con `role="status"` de `AgendaPage` anuncia la confirmación textual ("Turno confirmado.", "Turno marcado como atendido.", "Turno marcado como ausente.", "Turno cancelado.", "Turno reprogramado para el DD/MM/AAAA a las HH:MM.").

## Capabilities

### New Capabilities
- `frontend-appointment-actions`: Gestión interactiva del ciclo de vida del turno desde el frontend: diálogo modal de detalle, consulta de historial con fechas y horas locales, transiciones de estado ordinarias, cancelación con confirmación interna, formulario de reprogramación con revalidación de solapamientos, matriz RBAC por rol, anuncios accesibles con `role="status"` y adaptabilidad responsive (1440, 768 y 390 px).

### Modified Capabilities
- `frontend-agenda`: Incorporación de interactividad en los turnos de la agenda diaria y semanal mediante elementos `<button type="button">` accesibles con `aria-label` completo en `AgendaGrid` y botón "Ver turno" condicional en `AgendaTable`.

## Impact

- **Código frontend afectado**:
  - `frontend/src/features/agenda/AgendaGrid.tsx` y `AgendaGrid.module.css`: las tarjetas pasan a ser `<button type="button">` accesibles con foco visible.
  - `frontend/src/features/agenda/AgendaTable.tsx`: soporte opcional para callback de selección y botón "Ver turno".
  - `frontend/src/features/agenda/AgendaPage.tsx`: integración de diálogos modales de detalle y reprogramación, y emisión de anuncios en la región `role="status"`.
  - Nuevos componentes en `frontend/src/features/appointments/`: `AppointmentDetailDialog.tsx`, `AppointmentRescheduleDialog.tsx`, `AppointmentHistoryList.tsx` y clientes de API tipados en `appointmentApi.ts`.
- **APIs consumidas**:
  - `GET /api/appointments/{id}`
  - `POST /api/appointments/{id}/status`
  - `POST /api/appointments/{id}/cancel`
  - `POST /api/appointments/{id}/reschedule`
  - `GET /api/appointments/{id}/history`
- **Tests existentes**: Permanecen estrictamente intactos. La suite completa de 191 tests existentes continúa en verde.
