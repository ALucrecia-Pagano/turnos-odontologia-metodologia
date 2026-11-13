# Exploración — C-30 `ui-reprogramar-cancelar-y-estados`

Fecha: 2026-11-13  
Repo: `turnos-odontologia` (TPI Metodología I), rama `main` (`ab33e20`)  
Change explorado: **C-30 `ui-reprogramar-cancelar-y-estados`** (camino crítico)  
Depende de: **C-29 `ui-dar-turno-con-errores`** (archivado el 2026-11-13)  
Estado de cambios concurrentes: C-34 archivado; C-35 y C-36 pendientes de interfaz de acceso; C-30 es el siguiente change del camino crítico en Fase 6.  
Alcance de este paso: **Solo exploración (`/opsx:explore`)**. Único archivo creado: este documento. No se tocan `openspec/changes`, `CHANGES.md`, código fuente, tests, `.env`, `.codex/` ni se realiza `git add` ni commit.  
Skill cargada: `.agents/skills/appointment-frontend-ux`.  
Context7: **No fue consultado**. Toda la evidencia, tipos, endpoints, esquemas y citas provienen del código real existente en el repositorio.

---

## 1. Contratos reales de los 5 endpoints del backend

Fuente directa: `backend/app/api/appointments.py`, `backend/app/api/schemas.py`, `backend/app/auth/permissions.py`, `backend/app/api/deps.py`, `backend/app/api/errors.py`.

| # | Endpoint | Método | Roles autorizados (RBAC) | Payload de solicitud (Body) | Respuesta exitosa (200 OK) | Códigos de error y estructuras de respuesta |
|---|----------|--------|--------------------------|-----------------------------|----------------------------|---------------------------------------------|
| 1 | `/api/appointments/{id}` | `GET` | Recepción (`all`), Administrador (`all`), Odontólogo (`all`). `permissions.py:49` | *Ninguno (vacío)* | `AgendaAppointmentResponse` (`schemas.py:401-415`):<br>`id`: UUID<br>`patientId`: UUID<br>`patientName`: str<br>`professionalId`: UUID<br>`professionalName`: str<br>`chairId`: UUID<br>`chairName`: str<br>`serviceId`: UUID<br>`serviceName`: str<br>`startAt`: ISO-8601 UTC (`...Z`)<br>`endAt`: ISO-8601 UTC (`...Z`)<br>`status`: str | • **401**: `{"code": "INVALID_TOKEN", "message": "..."}`<br>• **403**: `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para leer la agenda."}]}`<br>• **404**: `{"code": "NOT_FOUND", "message": "Turno no encontrado."}` |
| 2 | `/api/appointments/{id}/reschedule` | `POST` | Recepción (`all`), Administrador (`all`). `permissions.py:50`<br>*(Odontólogo: 403 `FORBIDDEN_OPERATION`)* | `RescheduleInput` (`schemas.py:309-323`, `extra="forbid"`):<br>• `startAt`: ISO datetime con zona requerida (ej. `"2026-11-17T10:00:00-03:00"`)<br>• `professionalId?`: UUID \| null *(opcional)*<br>• `chairId?`: UUID \| null *(opcional)*<br>• `durationMin?`: int \| null *(opcional, 5-480 min)*<br>*Nota: NO admite patientId, serviceId ni reason.* | `AppointmentResponse` (`schemas.py:287-298`):<br>`id`: UUID<br>`patientId`: UUID<br>`professionalId`: UUID<br>`chairId`: UUID<br>`serviceId`: UUID<br>`startAt`: ISO-8601 UTC (`...Z`)<br>`endAt`: ISO-8601 UTC (`...Z`)<br>`status`: `"reservado"` *(siempre vuelve a reservado)* | • **400**: `{"errors": [{"field": str, "type": str, "message": str}]}` (falta tz en startAt o campo extra)<br>• **401**: `INVALID_TOKEN`<br>• **403**: `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para reprogramar turnos."}]}`<br>• **404**: `{"code": "NOT_FOUND", "message": "Turno no encontrado."}`<br>• **409**: `{"violations": [...]}` (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`)<br>• **422**: `{"violations": [...]}` (`INVALID_TRANSITION`, `IN_THE_PAST`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`) |
| 3 | `/api/appointments/{id}/cancel` | `POST` | Recepción (`all`), Administrador (`all`). `permissions.py:51`<br>*(Odontólogo: 403 `FORBIDDEN_OPERATION`)* | *Ninguno (vacío)*.<br>La firma no recibe body (`appointments.py:107-115`). | `AppointmentResponse` (`schemas.py:287-298`):<br>`id`: UUID<br>...<br>`status`: `"cancelado"` | • **401**: `INVALID_TOKEN`<br>• **403**: `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para cancelar turnos."}]}`<br>• **404**: `{"code": "NOT_FOUND", "message": "Turno no encontrado."}`<br>• **422**: `{"violations": [{"code": "INVALID_TRANSITION", "message": "El turno de ... no puede pasar del estado \"atendido\" al estado \"cancelado\"."}]}` |
| 4 | `/api/appointments/{id}/status` | `POST` | Recepción (`all`), Administrador (`all`), Odontólogo (`own`). `permissions.py:52`<br>*(Odontólogo sobre turno ajeno: 403 `FORBIDDEN_OPERATION`)* | `StatusChangeInput` (`schemas.py:303-307`, `extra="forbid"`):<br>• `toStatus`: `"confirmado"` \| `"atendido"` \| `"ausente"`<br>*Nota: "cancelado" está prohibido aquí (da 400/422; se cancela por `/cancel`). No admite campo note/reason.* | `AppointmentResponse` (`schemas.py:287-298`):<br>`id`: UUID<br>...<br>`status`: nuevo estado ("confirmado", "atendido" o "ausente") | • **400**: `{"errors": [...]}` si `toStatus` no es uno de los 3 valores literales permitidos.<br>• **401**: `INVALID_TOKEN`<br>• **403**: `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para cambiar el estado del turno de ...: un odontólogo solo puede cambiar el estado de sus propios turnos."}]}` (`transitions.py:85-88`)<br>• **404**: `{"code": "NOT_FOUND", "message": "Turno no encontrado."}`<br>• **422**: `{"violations": [...]}` con:<br>  - `INVALID_TRANSITION`: transición no permitida según tabla RN-TU-02.<br>  - `STATUS_CHANGE_TOO_EARLY`: marcar atendido/ausente antes de `now >= start_at` (`transitions.py:115-120`). |
| 5 | `/api/appointments/{id}/history` | `GET` | Recepción (`all`), Administrador (`all`), Odontólogo (`own`). `permissions.py:53`<br>*(Odontólogo sobre turno ajeno: 403 `FORBIDDEN_OPERATION`)* | *Ninguno (vacío)* | `list[HistoryEntryResponse]` (`schemas.py:338-349`):<br>Array ordenado cronológicamente (`changed_at ASC, id ASC`, `appointment.py:242`).<br>Cada ítem:<br>• `from`: str \| null (null en creación inicial)<br>• `to`: str<br>• `changedBy`: UUID<br>• `changedByName`: str \| null (nombre del usuario)<br>• `changedAt`: ISO-8601 UTC (`...Z`)<br>• `reschedule`: `RescheduleDetailResponse` \| null:<br>  - `previousStartAt`: str<br>  - `previousEndAt`: str<br>  - `newStartAt`: str<br>  - `newEndAt`: str<br>  - `previousProfessionalId`: UUID<br>  - `newProfessionalId`: UUID<br>  - `previousChairId`: UUID<br>  - `newChairId`: UUID | • **401**: `INVALID_TOKEN`<br>• **403**: `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para leer el historial de turnos."}]}` (`deps.py:126,133-139`)<br>• **404**: `{"code": "NOT_FOUND", "message": "Turno no encontrado."}` |

---

## 2. Tabla de transiciones de estado y roles autorizados

Fuentes directas en el código:
- Definición de grafo y aristas: `backend/app/domain/appointment/transitions.py:17-28` (`_TRANSITIONS`).
- Guardas de permisos de cancelación y cambios de estado: `backend/app/domain/appointment/transitions.py:45-53, 81-89`.
- Guarda temporal `STATUS_CHANGE_TOO_EARLY`: `backend/app/domain/appointment/transitions.py:93-97, 115-120`.
- Reglas de reprogramación: `backend/app/domain/appointment/reschedule.py:34-36, 75-78` (`_RESCHEDULABLE = {RESERVED, CONFIRMED}`).
- Matriz RBAC de seguridad: `backend/app/auth/permissions.py:48-53`.

### 2.1 Matriz de transiciones del dominio y permisos por rol

| Estado Actual | Acción / Transición | Endpoint | Condiciones de negocio | Roles autorizados | Código de rechazo si no cumple |
|---------------|---------------------|----------|------------------------|-------------------|--------------------------------|
| **reservado** | Confirmar | `POST /{id}/status` `{ toStatus: "confirmado" }` | Ninguna condición temporal adicional | Recepción, Administrador, Odontólogo *(turno propio)* | • Odontólogo ajeno: `403 FORBIDDEN_OPERATION` |
| **reservado** | Marcar atendido | `POST /{id}/status` `{ toStatus: "atendido" }` | `now >= start_at` (el turno ya inició o pasó) | Recepción, Administrador, Odontólogo *(turno propio)* | • `now < start_at`: `422 STATUS_CHANGE_TOO_EARLY`<br>• Odontólogo ajeno: `403 FORBIDDEN_OPERATION` |
| **reservado** | Marcar ausente | `POST /{id}/status` `{ toStatus: "ausente" }` | `now >= start_at` (el turno ya inició o pasó) | Recepción, Administrador, Odontólogo *(turno propio)* | • `now < start_at`: `422 STATUS_CHANGE_TOO_EARLY`<br>• Odontólogo ajeno: `403 FORBIDDEN_OPERATION` |
| **reservado** | Cancelar | `POST /{id}/cancel` *(sin body)* | Mientras no sea terminal (RN-TU-04) | Recepción, Administrador *(Odontólogo NO)* | • Odontólogo: `403 FORBIDDEN_OPERATION` |
| **reservado** | Reprogramar | `POST /{id}/reschedule` | Revalida RN-AG; nuevo inicio `>= now`; hueco libre; vuelve a `reservado` | Recepción, Administrador *(Odontólogo NO)* | • Odontólogo: `403 FORBIDDEN_OPERATION`<br>• Solapamiento: `409`<br>• Pasado: `422 IN_THE_PAST` |
| **confirmado** | Marcar atendido | `POST /{id}/status` `{ toStatus: "atendido" }` | `now >= start_at` | Recepción, Administrador, Odontólogo *(turno propio)* | • `now < start_at`: `422 STATUS_CHANGE_TOO_EARLY`<br>• Odontólogo ajeno: `403 FORBIDDEN_OPERATION` |
| **confirmado** | Marcar ausente | `POST /{id}/status` `{ toStatus: "ausente" }` | `now >= start_at` | Recepción, Administrador, Odontólogo *(turno propio)* | • `now < start_at`: `422 STATUS_CHANGE_TOO_EARLY`<br>• Odontólogo ajeno: `403 FORBIDDEN_OPERATION` |
| **confirmado** | Cancelar | `POST /{id}/cancel` *(sin body)* | Mientras no sea terminal | Recepción, Administrador *(Odontólogo NO)* | • Odontólogo: `403 FORBIDDEN_OPERATION` |
| **confirmado** | Reprogramar | `POST /{id}/reschedule` | Revalida RN-AG; vuelve a `reservado` | Recepción, Administrador *(Odontólogo NO)* | • Odontólogo: `403 FORBIDDEN_OPERATION`<br>• Solapamiento: `409` |
| **confirmado** | Volver a reservado | *No existe en API ordinaria* | Solo posible vía `reschedule` | — | `422 INVALID_TRANSITION` |
| **atendido** *(terminal)* | *Cualquier acción* | — | Estado terminal inmutable | Ninguno | `422 INVALID_TRANSITION` |
| **ausente** *(terminal)* | *Cualquier acción* | — | Estado terminal inmutable | Ninguno | `422 INVALID_TRANSITION` |
| **cancelado** *(terminal)* | *Cualquier acción* | — | Estado terminal inmutable | Ninguno | `422 INVALID_TRANSITION` |

### 2.2 ¿La API expone las transiciones permitidas o el frontend tendría que replicarlas?

- **Comportamiento real de la API**: La API **NO** expone un endpoint de descubrimiento (tipo `GET /appointments/{id}/allowed-actions`) ni incluye un campo `allowedTransitions` en `AgendaAppointmentResponse` ni en `AppointmentResponse`.
- **Cómo evitar duplicar reglas de negocio en el frontend**:
  - **Propuesta / Recomendación**: Adoptar el principio de **UI Declarativa de Navegación + Dominio como Autoridad Definitiva** (alineado con `RN-GL-01` en `knowledge-base/05_reglas_de_negocio.md:69`).
  - La interfaz define únicamente una tabla de presentación visual (`APPOINTMENT_ACTIONS_MAP`) que muestra u oculta botones para evitar frustración al usuario (por ejemplo, no mostrar botón "Cancelar" si el turno ya está en estado `cancelado` o `atendido`, ni mostrárselo a un odontólogo).
  - El frontend **NO** intenta calcular reglas dinámicas complejas ni duplicar la comprobación temporal `now >= start_at` con clocks locales del cliente (lo cual causaría discrepancias de segundos con el servidor).
  - Si un usuario presiona un botón disponible (ej. "Marcar atendido" antes de hora), la solicitud viaja a la API. Al retornar `422 STATUS_CHANGE_TOO_EARLY`, el frontend captura la respuesta y la renderiza en el contenedor superior de alertas con `role="alert"`, mostrando textualmente el mensaje devuelto por el dominio (`"El turno de ... todavía no empezó: no se puede marcar como \"atendido\" antes del inicio (momento actual: ...)"`). De este modo, la regla vive 100% en Python puro en el backend y el frontend es un canal fiel de interacción.

---

## 3. Qué existe en el frontend para reusar y qué falta

### 3.1 Componentes, módulos y utilidades existentes para reusar
1. **`frontend/src/shared/components/Dialog.tsx`**:
   - Primitiva modal `<dialog>` nativa accesible implementada en C-29.
   - Cuenta con: `open`, `onClose`, `labelledBy`, `returnFocusRef`.
   - Soporta tecla `Escape` (con guarda contra eventos duplicados), detección de entorno para `jsdom` (fallback a `<dialog open>`), y retorno de foco programático al disparador.
2. **`frontend/src/shared/components/StatusBadge.tsx`**:
   - Renderiza badges accesibles con texto visible y tokens de contraste AA para `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`.
3. **`frontend/src/shared/api/client.ts` y `types.ts`**:
   - Soporte nativo para parsear respuestas de error: 400 (`validation`), 401 (`auth`), 403 (`forbidden`), 404 (`not_found`), 409 (`conflict`), 422 (`unprocessable`).
   - Extrae `violations` completas con `code`, `message`, `conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval`, `referenceKind`.
4. **`frontend/src/features/appointments/AppointmentFormDialog.tsx`**:
   - Expone la función pura `buildStartAtIso(dateStr, timeStr, timeZone)` que calcula el offset local exacto empleando exclusivamente la API nativa `Intl.DateTimeFormat` (sin dependencias externas).
   - Estructura probada del contenedor superior de alerta con `role="alert"`, `aria-live="assertive"`, badges de código y traslado de foco programático.
5. **`frontend/src/features/agenda/AgendaPage.tsx`**:
   - Región permanente de anuncio accesible: `<div role={state.phase === "loading" ? undefined : "status"} aria-live="polite" className={styles.srOnly}>{statusMessage}</div>`.
   - `state.refresh()` de `useAgenda` para recargar turnos y estado sin recargar la página.
   - Datos globales disponibles: `state.timezone`, `state.professionals`, `state.chairs`.
   - Objeto `user` de `useAuth()` con `user.role` y `user.professionalId`.

### 3.2 Qué falta implementar
1. **Interactividad en las tarjetas de la agenda (`AgendaGrid.tsx` y `AgendaTable.tsx`)**:
   - En `AgendaGrid.tsx`, las tarjetas son actualmente `<article>` pasivos sin manejador de clic ni foco de teclado. Deben convertirse en elementos accionables (o envolver un `<button type="button">`) con foco visible, manteniendo sus atributos semánticos (`aria-label`, `data-testid`, etc.).
   - En `AgendaTable.tsx`, las filas `<tr>` son estáticas. Se debe proveer una acción accesible (botón "Ver detalle" o fila clickeable accesible) para abrir el detalle del turno.
2. **Diálogo de Detalle y Acciones del Turno (`AppointmentDetailDialog.tsx`)**:
   - Componente modal sobre `Dialog.tsx` que reciba el turno seleccionado y cargue sus datos e historial.
   - Cabecera con datos del turno: paciente, profesional, sillón, prestación, fecha y rango horario en hora local, y `StatusBadge`.
   - Barra de acciones con botones contextuales según estado actual y rol del usuario logueado.
3. **Confirmación accesible para cancelación de turnos**:
   - Subvista o panel de confirmación dentro del mismo diálogo modal: "¿Está seguro de que desea cancelar este turno? Esta acción no se puede deshacer.", con botones "Confirmar cancelación" (destructivo) y "Volver", sin invocar `window.confirm`.
4. **Formulario / Diálogo de Reprogramación (`AppointmentRescheduleDialog.tsx`)**:
   - Componente modal o subvista para mover el turno: muestra paciente y prestación en solo lectura; inputs editables para fecha, hora, selector de profesional, selector de sillón y duración (múltiplo de 5 min).
   - Envío a `POST /api/appointments/{id}/reschedule` y gestión de errores 409/422.
5. **Panel de Historial de Cambios (`AppointmentHistoryList.tsx`)**:
   - Componente que consulta `GET /api/appointments/{id}/history`.
   - Renderiza la lista cronológica con: estado previo -> nuevo estado, nombre del usuario autor (`changedByName`), fecha y hora local formateadas, y desglose de reprogramación (intervalo previo -> intervalo nuevo) si aplica.
   - Manejo accesible de estados de carga, vacío y error.
6. **Contratos tipados del cliente frontend**:
   - Tipos TypeScript para `RescheduleInput`, `StatusChangeInput`, `HistoryEntryResponse`, `RescheduleDetailResponse`.

---

## 4. Tamaño estimado y propuesta de estructuración del Roadmap

### 4.1 Estimación de volumen de implementación y tests
- **Tests unitarios y de integración nuevos**:
  1. *Selección de turno y apertura de diálogo* (grid y table, teclado, foco inicial): ~5 tests.
  2. *Detalle y consulta de historial* (carga, renderizado cronológico con hora local, reprogramación detallada, error 403): ~6 tests.
  3. *Cambios de estado ordinarios* (confirmar, atendido, ausente; visibilidad por rol y estado actual; guardas de horario 422): ~7 tests.
  4. *Cancelación de turno* (subvista de confirmación in-dialog, botón destructivo, llamada a `POST /{id}/cancel`, refresco y anuncio): ~5 tests.
  5. *Reprogramación de turno* (campos editables, conservación de paciente/prestación, revalidación de solapamiento 409, fecha en pasado 422, éxito con retorno a reservado): ~8 tests.
  6. *Accesibilidad, foco y anuncios en AgendaPage*: ~4 tests.
  - **Total estimado**: ~32 a 35 tests nuevos. Siguiendo Strict TDD (un test = un escenario = una mutación), implicará ~32 a 35 mutaciones.
- **Archivos a crear o modificar**:
  - Nuevos: `AppointmentDetailDialog.tsx`, `AppointmentDetailDialog.module.css`, `AppointmentRescheduleDialog.tsx`, `AppointmentRescheduleDialog.module.css`, `AppointmentHistoryList.tsx`, `AppointmentHistoryList.module.css`, `appointmentApi.ts`.
  - Modificados: `AgendaGrid.tsx`, `AgendaGrid.module.css`, `AgendaTable.tsx`, `AgendaTable.module.css`, `AgendaPage.tsx`.
  - Archivos de test nuevos: ~5 archivos (respetando la regla de no tocar tests existentes).

### 4.2 Evaluación: ¿Conviene partir C-30?

- **Opción A (Change único C-30 `ui-reprogramar-cancelar-y-estados`)**:
  - *Ventajas*: Mantiene la estructura de `CHANGES.md` intacta (33 changes, 19 gates). Evita re-indexar números de change posteriores (C-31, C-32, etc.) ni modificar referencias en la KB.
  - *Desventajas*: El apply de ~35 tests es grande y exigirá una ejecución metódica por fases en `tasks.md` para evitar sobrecarga de contexto.
- **Opción B (Partición en C-30A y C-30B)**:
  - C-30A: `ui-detalle-estados-e-historial` (selección en agenda, detalle modal, cambios de estado ordinarios, cancelación in-dialog, historial). ~20 tests.
  - C-30B: `ui-reprogramar-turno` (formulario de reprogramación, revalidación de agenda, errores 409). ~15 tests.
  - *Ventajas*: Dos applys más pequeños y de menor riesgo.
  - *Desventajas*: Requiere modificar `CHANGES.md`, `AGENTS.md` y recalcular el camino crítico y roadmap.

- **Recomendación**: **Mantener C-30 como un change único (Opción A)**, pero organizando estrictamente `tasks.md` en **5 fases secuenciales e independientes**:
  - Fase 1: Interactividad en agenda + Detalle del turno.
  - Fase 2: Consulta y renderizado de Historial.
  - Fase 3: Cambios de estado ordinarios (confirmar, atendido, ausente).
  - Fase 4: Cancelación con confirmación in-dialog.
  - Fase 5: Formulario y flujo de reprogramación.

---

## 5. Decisiones consolidadas (D1 a D10)

### Decisión 1 — Dónde viven las acciones y cómo se accede a ellas desde la agenda
- **Opciones**:
  - *Opción 1.1*: Diálogo modal accesible `AppointmentDetailDialog` que se abre al hacer clic o pulsar `Enter`/`Space` sobre cualquier turno de `AgendaGrid` o `AgendaTable`.
  - *Opción 1.2*: Menú contextual emergente (dropdown / popover) directo sobre la tarjeta del turno.
  - *Opción 1.3*: Página / ruta independiente `/turnos/:id`.
- **Recomendación por defecto**: **Opción 1.1**. Un diálogo modal centrado utilizando la primitiva `Dialog.tsx` de C-29. Permite presentar el contexto completo del turno, su historial y las acciones pertinentes sin perder la posición ni los filtros de la agenda. La opción 1.2 es propensa a desbordes en tarjetas angostas o carriles divididos, y la 1.3 desorienta al operador sacándolo de la vista de agenda.

### Decisión 2 — Reprogramación: Componente dedicado vs. reutilizar `AppointmentFormDialog`
- **Opciones**:
  - *Opción 2.1*: Agregar una prop `mode="create" | "reschedule"` a `AppointmentFormDialog.tsx`.
  - *Opción 2.2*: Crear un componente modal específico `AppointmentRescheduleDialog.tsx` que comparta los helpers puros (`buildStartAtIso`, estilos de alerta y `Dialog.tsx`).
- **Recomendación por defecto**: **Opción 2.2**. El contrato de `POST /appointments/{id}/reschedule` difiere sustancialmente del de alta: el paciente y la prestación **no** se pueden cambiar (el backend los toma del turno original) y no deben ser seleccionables ni buscables. Si se añade un modo a `AppointmentFormDialog`, se llenaría de ramas condicionales que degradarían la mantenibilidad del formulario de alta ya probado. Un diálogo dedicado muestra paciente y prestación como texto de solo lectura y expone únicamente los campos editables: fecha, hora, profesional, sillón y duración.

### Decisión 3 — Cancelación: Confirmación in-dialog sin `window.confirm` ni motivo
- **Opciones**:
  - *Opción 3.1*: Subvista / panel de confirmación inline dentro del propio `AppointmentDetailDialog` ("¿Confirma que desea cancelar el turno de [Paciente]?") con botones "Confirmar cancelación" y "Volver al detalle". Sin campo de motivo.
  - *Opción 3.2*: Modal secundario apilado (`<dialog>` sobre `<dialog>`).
  - *Opción 3.3*: Diálogo con campo de texto obligatorio u opcional para ingresar motivo de cancelación.
  - *Opción 3.4*: Uso de `window.confirm()`.
- **Recomendación por defecto**: **Opción 3.1**. `window.confirm()` (Opción 3.4) está prohibido por accesibilidad y por la regla C1 (exige stub global). La API real `POST /api/appointments/{id}/cancel` no recibe ningún body ni motivo (Opción 3.3). Los modales apilados (Opción 3.2) introducen problemas severos de apilamiento y foco en navegadores y jsdom. La confirmación inline dentro del mismo diálogo es limpia, accesible y previene cancelaciones accidentales.

### Decisión 4 — Botones de estado según estado actual y rol, y manejo de errores 409/422
- **Opciones**:
  - *Opción 4.1*: Mostrar botones de acción contextualmente según el estado actual del turno y el rol del usuario logueado:
    - En `reservado`: botones "Confirmar", "Marcar atendido", "Marcar ausente", "Reprogramar", "Cancelar turno" (estos dos últimos solo para recepción/admin).
    - En `confirmado`: botones "Marcar atendido", "Marcar ausente", "Reprogramar", "Cancelar turno" (estos dos últimos solo para recepción/admin).
    - En `atendido`, `ausente`, `cancelado` (terminales): ningún botón de acción modificatoria; aviso visible de estado terminal.
    - Ante rechazos 409 o 422 (ej. `STATUS_CHANGE_TOO_EARLY` si el turno aún no empezó, o `INVALID_TRANSITION`): se muestra el alert accesible idéntico a C-29 (`role="alert"`), con el mensaje textual en español del backend y foco automático.
  - *Opción 4.2*: Mostrar siempre todos los botones pero deshabilitados (`disabled`) con tooltip explicativo.
- **Recomendación por defecto**: **Opción 4.1**. Deshabilita o no renderiza transiciones imposibles, manteniendo la interfaz despejada. Ante cualquier condición no prevista o desfasaje horario, el alert accesible expone el rechazo del dominio tal cual.

### Decisión 5 — Historial: Visualización, campos, orden y zona horaria
- **Opciones**:
  - *Opción 5.1*: Sección "Historial de cambios" integrada en el `AppointmentDetailDialog`, que consulta `GET /api/appointments/{id}/history`. Muestra una lista cronológica: `from` → `to` (con texto o `StatusBadge`), autor (`changedByName`), fecha y hora formateadas con la `timezone` de la agenda (`Intl.DateTimeFormat`), y detalle de reprogramación si `reschedule` no es nulo.
  - *Opción 5.2*: Pestaña o pantalla independiente dentro del diálogo.
- **Recomendación por defecto**: **Opción 5.1**. Proporciona trazabilidad completa e inmediata en la misma vista de detalle. Las fechas y horas se convierten a hora local utilizando el `timezone` provisto por la agenda (`America/Argentina/Buenos_Aires`).

### Decisión 6 — Refresco de agenda y anuncio accesible tras cada acción
- **Opciones**:
  - *Opción 6.1*: Al confirmarse exitosamente cualquier acción (cambio de estado, cancelación o reprogramación):
    1. Se cierra el modal (`onClose()`).
    2. Se invoca `state.refresh()` de `useAgenda`.
    3. Se actualiza `statusMessage` en `AgendaPage` para que la región existente `<div role={state.phase === "loading" ? undefined : "status"} aria-live="polite">` anuncie la confirmación (ej. `"Turno confirmado."`, `"Turno cancelado."`, `"Turno reprogramado para el 17/11/2026 a las 11:00."`).
    4. El foco regresa a la tarjeta del turno en la agenda.
  - *Opción 6.2*: Notificaciones flotantes tipo Toast con temporizadores.
- **Recomendación por defecto**: **Opción 6.1**. Reutiliza la infraestructura accesible probada en C-29 sin requerir librerías ni timers que compliquen los tests de Vitest.

### Decisión 7 — Comportamiento y restricciones para el rol Odontólogo
- **Opciones**:
  - *Opción 7.1*: El odontólogo puede hacer clic sobre cualquier turno para ver su información en `AppointmentDetailDialog`:
    - Si el turno le pertenece (`user.professionalId === appointment.professionalId`): puede cambiar el estado ("Confirmar", "Atendido", "Ausente") y consultar el historial (`GET /{id}/history`). Los botones "Reprogramar" y "Cancelar turno" están ocultos (la API devolvería 403 `FORBIDDEN_OPERATION`).
    - Si el turno es de **otro** odontólogo: la vista es estrictamente de solo lectura; los botones de acción están ocultos y la sección de historial no se consulta (o muestra aviso accesible de permiso) para evitar un 403 innecesario.
  - *Opción 7.2*: Impedir que el odontólogo abra el detalle de turnos de otros profesionales.
- **Recomendación por defecto**: **Opción 7.1**. Es habitual que un odontólogo consulte la agenda general para ver disponibilidad de sillones o de sus colegas, pero la matriz RBAC protege estrictamente que no pueda alterar estados ni ver historiales ajenos.

### Decisión 8 — Interactividad y accesibilidad en las tarjetas de `AgendaGrid` y `AgendaTable`
- **Opciones**:
  - *Opción 8.1*: En `AgendaGrid`, el elemento `<article>` de cada turno contendrá un botón interactivo accesible que envuelve los datos visibles (o el `<article>` adopta `tabIndex={0}`, `role="button"`, manejadores `onClick` y `onKeyDown` para Enter/Space). En `AgendaTable`, se añade un botón explícito "Ver turno" en una columna de acciones. Foco visible con `--color-focus` preservado.
  - *Opción 8.2*: Agregar un botón pequeño de icono "Opciones" en la esquina de cada tarjeta.
- **Recomendación por defecto**: **Opción 8.1**. Hacer la tarjeta completa interactiva mediante semántica de botón accesible (`aria-label` completo con hora, paciente, prestación, profesional y estado) maximiza el área táctil (mínimo 44 px de altura) en dispositivos táctiles y garantiza navegación cómoda por teclado.

### Decisión 9 — Preservar ítem "Turnos" del menú principal en "Próximamente"
- **Opciones**:
  - *Opción 9.1*: Mantener "Turnos" en `menuFor.ts` con `disabled: true` y `badge: "Próximamente"`.
  - *Opción 9.2*: Habilitar "Turnos" en `menuFor.ts` apuntando a `/agenda`.
- **Recomendación por defecto**: **Opción 9.1**. Habilitar "Turnos" rompería 3 tests existentes en `menuFor.test.ts:22-23,38-40` y `AppShell.test.tsx:68-79,101-105`, violando la regla dura de no modificar tests de main. El acceso a turnos está plenamente resuelto desde la propia agenda.

### Decisión 10 — Regla de un solo botón primario por vista en modales
- **Opciones**:
  - *Opción 10.1*: En `AppointmentDetailDialog`, la acción más frecuente y de avance (ej. "Confirmar" si está en reservado, o "Marcar atendido") adopta la clase `primaryButton`. Las demás acciones ("Marcar ausente", "Reprogramar", "Cerrar") adoptan `secondaryButton`, y "Cancelar turno" adopta `dangerButton`. En ningún caso coexisten dos botones primarios en la misma pantalla.
  - *Opción 10.2*: Todos los botones con el mismo peso visual secundario.
- **Recomendación por defecto**: **Opción 10.1**. Cumple con las directrices de diseño web y accesibilidad, orientando al usuario sin ambigüedad cognitiva.

---

## 6. Escenarios propuestos (Gherkin: Dado / Cuando / Entonces)

### Requisito 1: Apertura y visualización del detalle del turno desde la agenda

#### Escenario: Clic en tarjeta de turno abre diálogo con detalle completo
- **GIVEN** la agenda diaria en `2026-11-16` con un turno reservado de "Carlos Gómez" con la "Dra. Laura Quiroga" en "Sillón 1" de 10:00 a 10:30
- **WHEN** el usuario hace clic o presiona Enter sobre la tarjeta del turno en `AgendaGrid`
- **THEN** se abre el diálogo modal `AppointmentDetailDialog`
- **AND** se muestra el título "Detalle del turno"
- **AND** se visualizan los nombres del paciente, profesional, sillón, prestación, el horario local "10:00–10:30" y el badge de estado "Reservado"
- **AND** el foco se traslada al interior del diálogo

#### Escenario: Apertura desde la vista de tabla alternativa
- **GIVEN** la agenda visualizada en modo tabla semántica (`AgendaTable`)
- **WHEN** el usuario activa la acción "Ver turno" de una fila
- **THEN** se abre el diálogo modal `AppointmentDetailDialog` con los datos de dicho turno

### Requisito 2: Consulta y renderizado del historial de cambios

#### Escenario: Renderizado del historial con fechas y horas locales
- **GIVEN** el diálogo de detalle abierto para un turno que posee dos entradas de historial (creación inicial y cambio a confirmado por "Recepción")
- **WHEN** la API responde exitosamente a `GET /api/appointments/{id}/history`
- **THEN** se lista cada cambio en orden cronológico
- **AND** se exhibe el autor ("Recepción"), la transición "Reservado → Confirmado" y la fecha y hora formateadas en hora local

#### Escenario: Entrada de reprogramación muestra intervalos anterior y nuevo
- **GIVEN** una entrada de historial con detalle de reprogramación (`reschedule` presente)
- **WHEN** se visualiza la entrada en el panel de historial
- **THEN** se detalla el cambio de horario (ej. "10:00–10:30 → 11:00–11:30") en hora local

#### Escenario: Odontólogo sobre turno ajeno no visualiza historial privado
- **GIVEN** un usuario autenticado con rol `odontologo` viendo el detalle de un turno de otro profesional
- **WHEN** se evalúa la sección de historial
- **THEN** no se dispara la consulta `GET /api/appointments/{id}/history`
- **AND** se presenta una indicación informativa de acceso restringido

### Requisito 3: Cambios de estado ordinarios (confirmar, atendido, ausente)

#### Escenario: Confirmar turno reservado
- **GIVEN** un turno en estado `reservado` y un usuario con rol `recepcion`
- **WHEN** el usuario pulsa el botón "Confirmar"
- **THEN** se envía `POST /api/appointments/{id}/status` con `{ toStatus: "confirmado" }`
- **AND** ante respuesta 200 OK, el diálogo se cierra, la agenda se refresca y la región accesible anuncia "Turno confirmado."

#### Escenario: Intento de marcar atendido antes del horario de inicio (error de negocio 422)
- **GIVEN** un turno programado para las 15:00 de hoy y el instante actual es 10:00
- **WHEN** el usuario presiona "Marcar atendido"
- **THEN** la API responde 422 con violación `STATUS_CHANGE_TOO_EARLY`
- **AND** el diálogo permanece abierto y muestra el mensaje textual del dominio en el alert superior con `role="alert"`
- **AND** el foco del navegador se traslada al contenedor de alerta

#### Escenario: Odontólogo modifica estado de turno propio exitosamente
- **GIVEN** un odontólogo autenticado cuyo `professionalId` coincide con el del turno
- **WHEN** marca el turno como "Atendido" en un horario posterior al inicio
- **THEN** la solicitud es aceptada y el estado se actualiza

### Requisito 4: Cancelación de turnos con confirmación interna

#### Escenario: Flujo de cancelación con confirmación in-dialog
- **GIVEN** un turno en estado `confirmado` abierto en el diálogo de detalle por recepción
- **WHEN** el usuario pulsa "Cancelar turno"
- **THEN** se muestra un panel de confirmación dentro del diálogo preguntando si confirma la cancelación
- **WHEN** el usuario confirma la acción
- **THEN** se envía `POST /api/appointments/{id}/cancel` sin cuerpo
- **AND** al recibir 200 OK, el diálogo se cierra, la agenda se refresca y se anuncia "Turno cancelado."

#### Escenario: Cancelación desestimada retorna a la vista de detalle
- **GIVEN** el panel de confirmación de cancelación activo
- **WHEN** el usuario pulsa "Volver" o presiona Escape
- **THEN** no se envía ninguna solicitud HTTP y se regresa a la vista de detalle del turno

#### Escenario: Intento de cancelar un turno ya en estado terminal (caso de borde 422)
- **GIVEN** un turno que pasó a estado terminal concurrentemente
- **WHEN** se envía la cancelación y la API responde 422 `INVALID_TRANSITION`
- **THEN** el alert superior del diálogo expone el mensaje explicativo del dominio

### Requisito 5: Reprogramación de turnos y validación de conflictos

#### Escenario: Reprogramación exitosa revalida agenda y vuelve a reservado
- **GIVEN** un turno en estado `confirmado` y el usuario pulsa "Reprogramar"
- **WHEN** se abre el diálogo de reprogramación mostrando paciente y prestación fijos, y el usuario modifica la fecha al `2026-11-17` a las `11:00`
- **AND** pulsa "Guardar reprogramación"
- **THEN** se envía `POST /api/appointments/{id}/reschedule` con el nuevo `startAt`
- **AND** al recibir 200 OK con estado `reservado`, el modal se cierra, la agenda se refresca y se anuncia la reprogramación

#### Escenario: Reprogramación con conflicto de agenda (error de negocio 409)
- **GIVEN** un intento de reprogramar un turno a un horario donde el profesional ya tiene otro turno asignado
- **WHEN** la API responde 409 con violación `PROFESSIONAL_OVERLAP`
- **THEN** el formulario de reprogramación muestra el alert superior con el código y el mensaje en español que identifica el turno en conflicto
- **AND** el foco se traslada al alert de error

#### Escenario: Reprogramación hacia el pasado (error de negocio 422)
- **GIVEN** una selección de fecha u hora anterior a `now`
- **WHEN** la API responde 422 con violación `IN_THE_PAST`
- **THEN** el formulario muestra el mensaje textual de error devuelto por la API

---

## 7. Riesgos técnicos y verificaciones fuera del alcance de jsdom

### 7.1 Lo que NO se puede verificar con Vitest / jsdom (requiere inspección visual independiente)
1. **Centrado visual y superposición del modal `<dialog>`**:
   - `jsdom` no computa diseño CSS (box-model, flexbox, grid, z-index ni backdrop pseudo-elements `::backdrop`).
   - El centrado vertical/horizontal y la visibilidad del overlay oscuro no pueden comprobarse con aserciones de testing-library.
2. **Dimensiones táctiles mínimas (44 px de altura)**:
   - `getBoundingClientRect()` retorna ceros en `jsdom`. La altura de botones táctiles en tablet y móvil debe validarse mediante capturas visuales reales.
3. **Desborde horizontal y elipsis de texto en viewports angostos (390 px)**:
   - Los textos largos de error o nombres de pacientes y prestaciones en pantallas móviles requieren verificación visual para certificar que no rompen el contenedor modal.
4. **Comportamiento nativo de bloqueo de scroll del fondo**:
   - `jsdom` no simula el bloqueo de scroll del `<body>` que los navegadores reales aplican al abrir un modal nativo.

### 7.2 Plan de capturas visuales independientes (a cargo de Claude antes del archivo)
Se tomarán capturas con navegador real en tres resoluciones estándar:
- **1440 px (Escritorio)**: `C-30-detalle-turno-1440.png`, `C-30-historial-1440.png`, `C-30-reprogramar-1440.png`, `C-30-error-409-1440.png`.
- **768 px (Tablet)**: `C-30-detalle-turno-768.png`, `C-30-confirmacion-cancelar-768.png`.
- **390 px (Móvil)**: `C-30-detalle-turno-390.png`, `C-30-reprogramar-390.png`.

---

## Resumen del Explore y Estado para Propose

1. **Lectura completa realizada**: Se leyeron y cotejaron los 5 endpoints reales en el backend, sus esquemas en Pydantic, la matriz RBAC en `permissions.py`, la política pura de transiciones en `transitions.py` y `reschedule.py`, el frontend existente de C-29 (`Dialog.tsx`, `AppointmentFormDialog.tsx`, `AgendaPage.tsx`, etc.) y las lecciones aprendidas de `verify-C-29.md`.
2. **Cero dependencias nuevas**: Todo el desarrollo se apoyará exclusivamente en React 18, TypeScript strict, CSS Modules con tokens Aqua, `Intl` nativo y la suite de pruebas Vitest bajo la Regla C1.
3. **Decisiones clave tomadas**:
   - Acceso centralizado desde la tarjeta del turno en la agenda a un modal `AppointmentDetailDialog`.
   - Formulario dedicado para reprogramación `AppointmentRescheduleDialog` (paciente y prestación fijos).
   - Cancelación con confirmación in-dialog sin `window.confirm` ni motivo.
   - Odontólogo limitado a sus propios turnos para cambios de estado e historial; lectura restringida de turnos ajenos.
   - Ítem "Turnos" en el menú principal permanece deshabilitado ("Próximamente") para preservar intactos los tests de main.
4. **Siguiente paso**: Con la confirmación de estas decisiones por parte del usuario, se procederá a `/opsx:propose C-30-ui-reprogramar-cancelar-y-estados`.
