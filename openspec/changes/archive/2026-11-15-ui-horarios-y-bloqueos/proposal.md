# Proposal

## Why

El consultorio odontológico necesita que cada profesional y la administración puedan configurar los horarios semanales de atención y registrar períodos de bloqueo (congresos, licencias, imprevistos), mientras que la recepción requiere consultar dicha disponibilidad para orientar a los pacientes en el mostrador. Hasta ahora, la persistencia y los endpoints REST de horarios y bloqueos quedaron resueltos y testeados en el backend (C-16, C-21), pero no existe interfaz web en el frontend para gestionarlos: el ítem "Horarios y bloqueos" permanece deshabilitado en el menú con la etiqueta "Próximamente" y la ruta `/horarios` no existe.

Este cambio implementa la pantalla `/horarios` y habilita el ítem correspondiente del menú para los tres roles del sistema, ofreciendo una experiencia accesible, adaptada a dispositivos móviles (heredando las hojas inferiores de C-36), respetando los permisos RBAC (edición para odontólogo y administrador, solo lectura para recepción) y presentando advertencias claras y explicativas sin cancelaciones automáticas cuando se modifican horarios o bloqueos que afectan turnos ya reservados.

## What Changes

- **Ruta y navegación principal**:
  - Se registra la ruta `/horarios` dentro del contenedor `AppShell` en `frontend/src/App.tsx`.
  - El ítem de navegación "Horarios y bloqueos" se habilita en `frontend/src/features/auth/menuFor.ts` apuntando a `/horarios` para los tres roles autorizados (`administrador`, `recepcion`, `odontologo`), eliminando el badge "Próximamente".
  - Se actualizan puntualmente las aserciones en los tests existentes del menú (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx`, `AppShell.mobile.test.tsx`), reflejando el cambio de requisito real del menú sin utilizar costuras artificiales.
- **Resolución de rol y profesional**:
  - Para el rol `odontologo`: gestiona únicamente su propia agenda (`user.professionalId`), sin selector de profesional visible. Si intenta acceder a un profesional ajeno mediante `?professionalId=`, la pantalla delega la verificación al backend y muestra el error 403 retornado en una alerta accesible sin cerrar sesión.
  - Para los roles `administrador` y `recepcion`: se ofrece un selector de profesionales activos (filtrando `active: true` desde `fetchProfessionals`). La selección se sincroniza en la URL con `?professionalId=`.
  - Para el rol `recepcion`: modo de **estricta solo lectura**, ocultando todos los botones de mutación ("Agregar tramo", "Quitar", "Guardar horario", "Nuevo bloqueo", "Eliminar bloqueo").
- **Sección de horarios de atención semanales**:
  - Lista de los días de la semana con sus tramos horarios `HH:MM–HH:MM`.
  - Entradas de hora en campos de texto con validación de formato (el extremo de fin admite `24:00`).
  - Botones "Agregar tramo" y "Quitar" por fila para estructurar la jornada laboral.
  - Botón "Guardar horario": envía la semana completa en un único `PUT /api/professionals/{id}/working-hours` en el orden visual de la pantalla.
  - La validación de solapamientos la realiza el dominio en el backend; el frontend expone los mensajes explicativos literales de error 422 en un contenedor con `role="alert"` y traslada el foco hacia él.
- **Sección de bloqueos de agenda**:
  - Lista de bloqueos ordenados por fecha y horario de inicio en hora local.
  - Diálogo modal "Nuevo bloqueo" montado sobre la primitiva accesible `Dialog.tsx`, que en dispositivos móviles (≤ 640 px) se comporta automáticamente como hoja inferior (bottom sheet).
  - Envío a `POST /api/professionals/{id}/blocks` con instantes ISO que incluyen el offset de zona horaria calculado por `buildStartAtIso`.
  - Acción "Eliminar bloqueo" con confirmación in-dialog (patrón de cancelación de C-30), cerrando con Escape o "Volver" sin enviar peticiones.
- **Aviso de turnos afectados**:
  - Componente de alerta (`role="alert"`) que lista los turnos comprometidos retornados por el backend en `appointmentsOutsideHours` (al guardar horarios) o en `affectedAppointments` (al crear bloqueos).
  - Detalle por turno: fecha, horario en hora local, nombre del paciente, nombre del profesional y `StatusBadge` con texto visible.
  - Nota informativa destacada: los turnos afectados **no** se cancelan ni se modifican automáticamente; deben reprogramarse desde la agenda.
- **Zona horaria de la API**:
  - La pantalla consulta una sola vez `GET /api/agenda` para obtener la zona horaria (`timezone`) de la clínica y la reutiliza en todas las conversiones de hora local, sin hardcodear constantes de timezone en código productivo.
- **Adaptabilidad responsive (1440, 768 y 390 px)**:
  - Diseño en dos columnas en 1440 px y columna única apilada en 768 px y 390 px. Sin desplazamiento horizontal en 390 px.

## Capabilities

### New Capabilities

- `frontend-working-hours-and-blocks`: Interfaz de usuario para la visualización y gestión de horarios semanales de atención y bloqueos de agenda de los profesionales en `/horarios`, con permisos por rol (edición para odontólogo y administrador, solo lectura para recepción), aviso de turnos afectados sin cancelaciones, hora local según la API y diseño adaptable a 1440, 768 y 390 px.

### Modified Capabilities

- `frontend-foundation`: Actualización de la navegación en `AppShell` para que el ítem "Horarios y bloqueos" sea un enlace activo a `/horarios` en lugar de un botón deshabilitado con "Próximamente" para los roles que lo utilizan.

## Impact

- **Código frontend afectado**:
  - `frontend/src/features/auth/menuFor.ts`: actualización de ruta `/horarios` y activación del ítem.
  - `frontend/src/App.tsx`: incorporación de la ruta protegida `/horarios` bajo `AppShell`.
  - Nueva carpeta `frontend/src/features/horarios/` con submódulos de API (`horariosApi.ts`), helpers temporales (`horariosTime.ts`), componentes de interfaz (`HorariosPage.tsx`, `WorkingHoursSection.tsx`, `BlocksSection.tsx`, `BlockFormDialog.tsx`, `BlockDeleteDialog.tsx`, `AffectedAppointments.tsx`) y estilos modulares (`*.module.css`).
  - Tests unitarios nuevos en archivos dedicados bajo `frontend/src/features/horarios/`.
  - Modificación puntual de 4 líneas en tests de menú preexistentes (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx`, `AppShell.mobile.test.tsx`) para validar el nuevo requisito del menú.
- **Backend**: Cero cambios en endpoints, esquemas, servicios, migraciones o reglas de negocio (C-21 y C-16 ya cubren toda la funcionalidad).
- **Governance**: **MEDIO** (gestión de disponibilidad profesional y bloqueos sin impacto en datos clínicos sensibles).

## Backlog post-C-32

Para preservar el alcance en un conjunto acotado y de alta calidad (menos de 25 tests nuevos), se dejan explícitamente para iteraciones futuras las siguientes extensiones no críticas:
1. Paginación o virtualización de la lista histórica de bloqueos cuando supere 100 registros.
2. Filtro por rango de fechas (`from`/`to`) en la sección de visualización de bloqueos.
3. Vista de calendario mensual compacto para selección visual de bloqueos.
4. Exportación o impresión de la planilla de horarios semanales.
