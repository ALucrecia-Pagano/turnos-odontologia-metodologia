# Design

## Context

El sistema cuenta con persistencia y endpoints REST completos para la gestión de horarios semanales y bloqueos de agenda de los profesionales (`GET/PUT /api/professionals/{id}/working-hours`, `GET/POST /api/professionals/{id}/blocks`, `DELETE /api/blocks/{id}`), implementados en C-16 y C-21. En el frontend, la barra de navegación `AppShell` y la función `menuFor(role)` definen el ítem "Horarios y bloqueos", pero permanece deshabilitado con el distintivo "Próximamente" porque la ruta no existía en `App.tsx`.

Para habilitar esta funcionalidad en C-32, se diseña la página `/horarios` asegurando accesibilidad, diseño adaptable para escritorio (1440 px), tablet (768 px) y celular (390 px) heredando las primitivas de C-36 (hojas inferiores en ≤ 640 px), y respetando la regla arquitectónica de que la autorización definitiva reside en el backend.

## Goals / Non-Goals

**Goals:**
- Implementar la ruta `/horarios` dentro del contenedor `AppShell`.
- Habilitar el ítem "Horarios y bloqueos" en el menú para los roles `administrador`, `recepcion` y `odontologo`, actualizando las aserciones de los tests existentes de menú como cambio de requisito legítimo.
- Permitir al odontólogo consultar y editar sus propios horarios y bloqueos sin selector de profesional, mostrando el error 403 del backend si intenta forzar un ID ajeno por URL.
- Permitir al administrador y a recepción seleccionar a cualquier profesional activo mediante un selector sincronizado con `?professionalId=`.
- Restringir al rol recepción a un modo de estricta solo lectura, ocultando todos los controles de mutación.
- Proveer edición de tramos semanales con inputs de texto `HH:MM` (admitiendo `24:00` en fin), enviando la semana completa mediante `PUT` en el orden visual de la interfaz.
- Proveer creación de bloqueos con `Dialog.tsx` convirtiendo fecha/hora local a instantes ISO con offset de zona horaria mediante `buildStartAtIso`.
- Proveer eliminación de bloqueos con confirmación interna in-dialog (patrón de cancelación de C-30), cancelable con Escape o botón "Volver".
- Exponer avisos de turnos afectados al guardar horarios o bloqueos en un contenedor accesible con `role="alert"`, indicando con texto visible que los turnos no se cancelan automáticamente.
- Obtener la zona horaria de la API consultando una sola vez `GET /api/agenda` al cargar la pantalla, sin hardcodear constantes de timezone en el código productivo.

**Non-Goals:**
- Modificar esquemas, servicios, migraciones o endpoints del backend.
- Duplicar en el cliente las reglas de negocio del dominio sobre solapamiento de tramos u orden de instantes (el backend valida y responde 422 con mensajes explicativos).
- Cancelar o modificar automáticamente turnos afectados por cambios de horario o bloqueos.
- Implementar paginación o filtrado por fechas en la lista de bloqueos (se pospone al backlog).
- Incorporar librerías externas de UI, calendarios o datepickers.

## Decisions

### D1 — Ruta y Menú: `/horarios` con Cambio de Requisito en Tests Preexistentes
- **Decisión**: Se registra la ruta `/horarios` en `App.tsx` y se habilita el ítem "Horarios y bloqueos" en `menuFor.ts` para los tres roles autorizados (`item.id === "agenda" || item.id === "horarios-y-bloqueos"`), apuntando a `/horarios`.
- **Tratamiento de tests preexistentes**: Se descarta expresamente la opción de un seam artificial (`enabledMenuIds`), ya que ocultaría el comportamiento real del menú en producción y agregaría complejidad espuria. Al ser un cambio legítimo de requerimiento (la funcionalidad deja de ser futura y pasa a estar disponible), se modifican únicamente las 4 aserciones específicas de "Horarios y bloqueos" en `menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y `AppShell.mobile.test.tsx` (una aserción por archivo, exactamente el mismo criterio aplicado a `smoke.test.tsx` en C-35).
- **Alternativas consideradas**:
  - *Opción A (Ruta sin menú)*: Registrar `/horarios` pero dejar el menú con "Próximamente". Se descartó porque la funcionalidad no sería descubrible en la navegación ni evaluable en el TP.
  - *Opción B (Seam enabledMenuIds)*: Parametrizar `menuFor(role, enabledIds = ["agenda"])` para no tocar los tests existentes. Se descartó porque falsea las pruebas unitarias y genera código muerto en producción.

### D2 — Roles y Selección de Profesional
- **Odontólogo**: Target fijado en `user.professionalId`. No se renderiza selector de profesionales. Si el usuario fuerza `?professionalId=Q` (ajeno), la pantalla realiza la petición a la API y el backend responde 403 `FORBIDDEN_OPERATION` ("No tiene permiso para leer horarios."); la interfaz muestra el error literal en `role="alert"` sin controles de edición y sin cerrar la sesión.
- **Administrador**: Selector desplegable con profesionales activos (obtenidos de `fetchProfessionals` con filtro `active: true`). La selección sincroniza la URL con `?professionalId=`.
- **Recepción**: Selector de profesionales activos idéntico al administrador, pero con la pantalla en modo de **estricta solo lectura** (se omiten los botones "Agregar tramo", "Quitar", "Guardar horario", "Nuevo bloqueo" y "Eliminar bloqueo").
- **Alternativas consideradas**: Ocultar el selector para recepción forzando el primer profesional. Se descartó porque recepción necesita consultar la disponibilidad de todos los odontólogos en el mostrador.

### D3 — Tramos Semanales por Día y Formato de Hora
- **Estructura visual**: Lista de días de la semana (lunes a domingo, o los admitidos por el backend) en orden correlativo, cada día agrupado bajo un `<fieldset>` semántico con `<legend>`.
- **Campos de hora**: Inputs de texto (`type="text"`, `inputMode="numeric"`, `placeholder="HH:MM"`). No se utiliza `<input type="time">` porque no garantiza el soporte de `24:00` requerido por el backend para el cierre de jornada.
- **Acciones**: Botones accesibles "Agregar tramo" (añade una fila con inputs vacíos) y "Quitar" (elimina la fila respectiva).
- **Envío**: Botón "Guardar horario" envía toda la semana en un arreglo crudo mediante `PUT /api/professionals/{id}/working-hours`, preservando el orden visual exacto de la interfaz para que las referencias posicionales de los mensajes del backend ("El tramo N...") coincidan fielmente.
- **Validación de solapamiento**: Se delega por completo al backend. Ante respuesta 422 `OVERLAPPING_WORKING_HOURS` o `INVALID_WORKING_HOURS`, el frontend muestra el mensaje literal en `role="alert"` y enfoca el mensaje; los errores 400 por formato de campo marcan `aria-invalid="true"`.

### D4 — Bloqueos de Agenda y Confirmación in-dialog
- **Lista**: Bloqueos del profesional ordenados por fecha/hora de inicio, renderizados en hora local.
- **Alta de bloqueo**: Diálogo modal `BlockFormDialog` construido sobre la primitiva `Dialog.tsx`. En celulares (≤ 640 px) se visualiza automáticamente como hoja inferior fijada al fondo de pantalla. Inputs de inicio y fin convertidos a instantes ISO con offset mediante `buildStartAtIso(date, time, timezone)`.
- **Eliminación**: Diálogo de confirmación `BlockDeleteDialog` dentro del mismo modal (patrón de cancelación de C-30). Mensaje: "¿Eliminar este bloqueo del [fecha] de [inicio] a [fin]?". Botones: "Sí, eliminar bloqueo" (destructivo) y "Volver" (secundario). Cerrar con Escape o "Volver" no envía peticiones. Al confirmar, envía `DELETE /api/blocks/{id}` y anuncia "Bloqueo eliminado." en `role="status"`.

### D5 — Aviso de Turnos Afectados sin Cancelación
- **Componente**: `AffectedAppointments`, utilizado tanto para `appointmentsOutsideHours` de horarios como para `affectedAppointments` de bloqueos.
- **Presentación**: Contenedor con `role="alert"` que lista los turnos comprometidos informando: fecha, horario local (`HH:MM–HH:MM`), nombre del paciente, nombre del profesional y `StatusBadge` con texto visible.
- **Regla fundamental**: El mensaje aclara que los turnos **no** se cancelan automáticamente y deben reprogramarse o gestionarse desde la agenda.

### D6 — Celular y Responsive
- **Distribución**: Dos columnas en 1440 px (horarios a la izquierda, bloqueos a la derecha); una columna apilada en 768 px y 390 px.
- **Móvil (390 px)**: Filas de tramo con inputs y botón "Quitar" adaptables sin generar scroll horizontal. Los modales aplican `@media (max-width: 640px)` presentándose como hojas inferiores con botones táctiles ≥ 44 px.

### D7 — Límite de Tamaño y Backlog
- Se acota el diseño a ~16-18 tests unitarios esenciales (tramos, bloqueos, afectados, roles, menú, timezone).
- Las funcionalidades secundarias (paginación de bloqueos, filtros por fecha, selector mensual) se relegan al backlog en `proposal.md`.

### D8 — Zona Horaria desde la API
- La pantalla realiza una única llamada inicial a `GET /api/agenda` para obtener `timezone: string` de la clínica y la reutiliza en todas las conversiones de fecha y hora local.
- Queda prohibido hardcodear constantes de zona horaria en código productivo de la funcionalidad.

## Desvío Documentado: Actualización de Aserciones de Menú en Tests Existentes

En cumplimiento de la regla de pruebas y la decisión D1, se documenta el desvío controlado en los tests preexistentes del menú:
1. `frontend/src/features/auth/menuFor.test.ts`: Las aserciones que comprobaban que todos los ítems posteriores a Agenda estaban deshabilitados con "Próximamente" (`items.slice(1).every(...)`) se actualizan para reflejar que "Horarios y bloqueos" está habilitado (`disabled: false`, `badge: null`), mientras que los 4 ítems restantes siguen deshabilitados.
2. `frontend/src/shared/components/AppShell.test.tsx`: La aserción que esperaba 5 botones deshabilitados para administrador se actualiza a 4 botones deshabilitados, ya que "Horarios y bloqueos" ahora se renderiza como un `<NavLink>` interactivo con `href="/horarios"`.
3. `frontend/src/shared/components/AppShellNavigation.test.tsx`: La aserción de cantidad de botones con texto "Próximamente" se actualiza de 5 a 4.
4. `frontend/src/shared/components/AppShell.mobile.test.tsx`: Se verifica si alguna aserción evalúa la lista de botones deshabilitados en móvil; de existir, se actualiza en consecuencia.

Este desvío sigue exactamente el mismo criterio y justificación técnica que la actualización de `smoke.test.tsx` en C-35, garantizando que los tests describan la realidad productiva sin introducir flags ni costuras encubiertas.

## Dudas y Alternativas

### Duda 1: Atributo `professionalName` en `AffectedAppointmentResponse`
- **Hallazgo**: La inspección del esquema del backend (`backend/app/api/schemas.py:200-210`) evidencia que `AffectedAppointmentResponse` serializa `id`, `patientId`, `patientName`, `chairId`, `startAt`, `endAt` y `status`. No contiene `professionalId` ni `professionalName`.
- **Alternativa adoptada**: Dado que el endpoint consultado es `/professionals/{id}/working-hours` o `/professionals/{id}/blocks`, la pantalla ya conoce la identidad del profesional sobre el cual se está operando (sea el usuario autenticado o el profesional seleccionado en el desplegable). En el componente `AffectedAppointments`, el nombre del profesional se obtiene directamente del contexto de la pantalla, evitando realizar peticiones redundantes.

### Duda 2: Aserción en `AppShell.mobile.test.tsx`
- **Hallazgo**: `AppShell.mobile.test.tsx` actualmente busca `a[data-menu-item='Agenda']` y comprueba la apertura/cierre del menú y el foco del botón "Menú", sin realizar aserciones de conteo sobre los botones deshabilitados.
- **Alternativa adoptada**: Durante la fase de aplicación, se verificará la ejecución de `AppShell.mobile.test.tsx`. Si no falla, permanecerá completamente intacto; si alguna comprobación implícita de botones lo requiere, se actualizará únicamente la línea necesaria.

## Componentes y Arquitectura de Frontend

```
frontend/src/features/horarios/
├── horariosApi.ts             # Cliente tipado: getWorkingHours, replaceWorkingHours, listBlocks, createBlock, deleteBlock
├── horariosTime.ts            # Helpers de formateo en hora local y definición de días de la semana
├── HorariosPage.tsx           # Contenedor principal: resolución de rol/profesional, carga inicial, layout 2 cols
├── HorariosPage.module.css
├── WorkingHoursSection.tsx    # Grilla de 7 días, inputs HH:MM, agregar/quitar tramo, guardar
├── WorkingHoursSection.module.css
├── BlocksSection.tsx          # Lista de bloqueos, apertura de diálogos de alta y confirmación de borrado
├── BlocksSection.module.css
├── BlockFormDialog.tsx        # Modal Dialog para creación de bloqueo con offset y hoja inferior móvil
├── BlockFormDialog.module.css
├── BlockDeleteDialog.tsx      # Modal Dialog de confirmación in-dialog para borrado
├── BlockDeleteDialog.module.css
└── AffectedAppointments.tsx   # Alerta accesible role="alert" con detalle de turnos fuera de horario / solapados
```

## Risks / Trade-offs

- **[Riesgo: Formato de hora 24:00]** → Mitigación: El backend acepta `24:00` en fin de jornada (`schemas.py:160,188`). Se emplean inputs de texto con validación de expresión regular `^([01]\d|2[0-3]):[0-5]\d$` para inicio y `^(([01]\d|2[0-3]):[0-5]\d|24:00)$` para fin, con mensaje de ayuda accesible visible.
- **[Riesgo: Desincronización posicional de tramos]** → Mitigación: El backend reporta errores citando la posición del tramo recibido ("El tramo N..."). El frontend envía la lista serializada en el mismo orden correlativo en que se muestra en pantalla.
- **[Riesgo: Zona horaria en entornos desconectados]** → Mitigación: Se consulta `GET /api/agenda` en la carga inicial y se reutiliza la propiedad `timezone`. Si la llamada falla, la pantalla entra en `ErrorState` con opción "Reintentar", garantizando consistencia absoluta con el servidor.
- **[Riesgo: Regresiones en tests existentes de AppShell]** → Mitigación: El cambio se acota estrictamente a las 4 líneas de aserción identificadas, garantizando que el resto de las suites sigan ejecutándose al 100%.
