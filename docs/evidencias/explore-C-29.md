# Exploración — C-29 `ui-dar-turno-con-errores`

Fecha: 2026-11-10  
Repo: `turnos-odontologia` (TPI Metodología I), rama `main`  
Change explorado: **C-29 `ui-dar-turno-con-errores`** (camino crítico)  
Depende de: **C-27 `ui-agenda-diaria`** (archivado)  
Estado de cambios concurrentes: **C-34 `ui-identidad-visual`** archivado en `main`; **C-35 `ui-portada-y-acceso`** en propose en paralelo.  
Alcance de este paso: **Solo explore**. Único archivo creado: este documento. No se tocan `openspec/changes`, `CHANGES.md`, código, tests, `.env`, `.codex/` ni se instala nada.  
Skill cargada: `.agents/skills/appointment-frontend-ux`.  
Context7: no fue consultado en esta fase exploratoria de lectura y diseño (no se inventan APIs; todas las citas provienen del código real del repositorio).

---

## 1. Contexto: Archivos y specs leídos (con evidencia empírica)

### 1.1 Base de Conocimiento (`knowledge-base/`)
- `knowledge-base/06_funcionalidades.md`:
  - **§US-042** (líneas 196-199): Criterios de aceptación para dar turno desde la UI:
    - CA-1: se muestran los mensajes del dominio tal cual (código + texto en español).
    - CA-2: el formulario sugiere la duración por defecto de la prestación seleccionada.
  - **§US-006** (líneas 102-113): Mensajes de conflicto claros con código, mensaje en español y, si aplica, identificación del turno o bloqueo en conflicto (`conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval`).
- `knowledge-base/07_flujos_principales.md`:
  - **§Flujo 1: Dar un turno** (líneas 3-54): Disparado por recepción o administrador. Envía `POST /api/appointments` con `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt` (ISO-8601 con offset) y `durationMin` opcional. Rechazo de dominio responde `409` (conflicto de agenda: horario, bloqueos o solapamientos) o `422` (validez del pedido: referencias, duración, pasado `IN_THE_PAST`).
- `knowledge-base/08_arquitectura_propuesta.md`:
  - **§Frontend cuidado** (líneas 134-143): Tokens semánticos de diseño, estados de carga/vacío/error en toda vista, accesibilidad (foco visible, navegación por teclado), mensajes del dominio mostrados con contexto, diseño responsive escritorio (1440 px), tablet (768 px) y móvil.
- `knowledge-base/03_actores_y_roles.md`:
  - **§RBAC** (líneas 15-34): Matriz de permisos: dar turnos (`Resource.APPOINTMENT, Action.CREATE`) solo está habilitado para **recepción** y **administrador**. El **odontólogo no da turnos** (debe recibir `403 FORBIDDEN_OPERATION`).

### 1.2 Backend API (`backend/app/`)
- `backend/app/api/appointments.py`:
  - Líneas 39-95: Endpoint `POST /appointments`. Exige permiso `require_permission(Resource.APPOINTMENT, Action.CREATE)`. Recibe `AppointmentInput`, toma `now` en UTC y zona `app_timezone`, ejecuta `book_appointment(...)`. Si falla con `Rejected`, lanza `DomainRejectedError(result)` (línea 81). Si es exitoso, responde `201 Created` con `AppointmentResponse` (líneas 85-94).
- `backend/app/api/schemas.py`:
  - Líneas 26-35: `ViolationItemSchema` serializa: `code` (string), `message` (string), `conflictingAppointmentId` (UUID opcional), `conflictingBlockId` (UUID opcional), `conflictingInterval` (`{ startAt: string, endAt: string }` opcional) y `referenceKind` (`PATIENT` | `PROFESSIONAL` | `CHAIR` | `SERVICE` opcional).
  - Líneas 269-285: `AppointmentInput`:
    - `patientId`: UUID obligatorio.
    - `professionalId`: UUID obligatorio.
    - `chairId`: UUID obligatorio.
    - `serviceId`: UUID obligatorio.
    - `startAt`: `datetime` obligatorio con zona horaria requerida (`validate_tz`, línea 282; sin zona horaria responde 400).
    - `durationMin`: `int | None = None` (opcional).
    - `extra="forbid"`: campos adicionales responden 400.
  - Líneas 287-298: `AppointmentResponse`: `id`, `patientId`, `professionalId`, `chairId`, `serviceId`, `startAt`, `endAt`, `status`.
- `backend/app/api/errors.py`:
  - Líneas 11-35: `VIOLATION_STATUS_MAP`: asigna 409 a `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`; asigna 422 a `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`; asigna 403 a `FORBIDDEN_OPERATION`.
  - Líneas 42-51: `status_for(violations)` calcula el código HTTP general: si hay 403 devuelve 403; si hay 422 devuelve 422; de lo contrario devuelve 409.
  - Líneas 77-84: `domain_rejected_handler` responde con `{ "violations": [...] }`.
  - Líneas 120-138: `request_validation_handler` responde `400 Bad Request` con `{ "errors": [{ "field": string | null, "type": string, "message": string }] }`.
- `backend/app/api/patients.py` y `backend/app/repositories/patients.py`:
  - `patients.py` líneas 51-76: `GET /api/patients` recibe `query: str | None = None`.
  - `patients.py` línea 60: Autorizado con `Resource.PATIENT, Action.READ` (recepción, administrador y odontólogo).
  - `repositories/patients.py` líneas 86-100: Si viene `query`, busca con `PatientModel.full_name.ilike(f"%{escaped}%")` o por inicio de DNI (`dni.startswith(digits)`). Ordena por `lower(full_name)`. **No tiene paginación** (devuelve todos los resultados coincidentes).
- `backend/app/api/services.py`:
  - Líneas 46-60: `GET /api/services` admite `active: bool | None = None`. Devuelve `list[ServiceResponse]` donde cada prestación incluye `id`, `name`, `defaultDurationMin` y `active`.
- `backend/app/api/professionals.py` y `backend/app/api/chairs.py`:
  - `professionals.py` líneas 51-60: `GET /api/professionals` devuelve lista de profesionales activos e inactivos (`id`, `fullName`, `active`, `licenseNumber`).
  - `chairs.py` líneas 42-57: `GET /api/chairs` devuelve lista de sillones (`id`, `name`, `active`).
- `backend/app/domain/violations.py`:
  - Líneas 41-51: `ReferenceKind` define `PATIENT`, `PROFESSIONAL`, `CHAIR`, `SERVICE`.
  - Líneas 53-79: `Violation` dataclass.

### 1.3 Specs OpenSpec (`openspec/specs/`)
- `openspec/specs/appointments-api/spec.md`:
  - Líneas 8-36: "Requirement: Alta autorizada de turnos": recepción y admin responden 201; odontólogo responde 403 con `FORBIDDEN_OPERATION` y mensaje `"No tiene permiso para dar turnos."`; sin token responde 401.
  - Líneas 37-63: "Requirement: Duración y validación del cuerpo": `durationMin` explícito prevalece sobre la prestación; si falta, se toma la prestación; `startAt` sin zona responde 400; campo extra responde 400.
  - Líneas 64-100: "Requirement: Conflictos de agenda": 409 con `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`.
  - Líneas 101-132: "Requirement: Referencias y reglas de validez": 422 con `IN_THE_PAST`, `UNKNOWN_REFERENCE` con `referenceKind`, `INACTIVE_REFERENCE`.
- `openspec/specs/catalog-and-patients/spec.md`:
  - Líneas 726-805: `GET /api/patients` admite búsqueda textual con `query`.

### 1.4 Frontend (`frontend/src/`)
- `frontend/src/features/agenda/AgendaPage.tsx`:
  - Líneas 29-203: Controla la fecha y filtros con `useSearchParams` (`date`, `view`, `professionalId`, `chairId`). Invoca `useAgenda` y renderiza `AgendaToolbar` y `AgendaView`.
- `frontend/src/features/agenda/AgendaToolbar.tsx`:
  - Líneas 8-25: `AgendaToolbarProps`. Dispone de navegación (Día/Semana, Anterior, Hoy, Siguiente), input de fecha, botón "Actualizar agenda" y filtros por Profesional y Sillón.
- `frontend/src/features/agenda/AgendaGrid.tsx`:
  - Líneas 38-252: Grilla temporal continua con cálculo porcentual (`topPercent`, `heightPercent`). **No posee slots o celdas interactivas discretas en el DOM**.
- `frontend/src/features/agenda/useAgenda.ts`:
  - Líneas 30-39: Expone `refresh: () => void` (que incrementa `reloadTick`, reejecutando en paralelo `fetchAgenda`, `fetchProfessionals` y `fetchChairs`).
- `frontend/src/features/agenda/agendaTime.ts`:
  - Líneas 53-85: Helpers de fecha y hora local con `Intl.DateTimeFormat` y `timeZone`.
- `frontend/src/features/auth/menuFor.ts` y `menuFor.test.ts`:
  - `menuFor.ts` línea 59: `const enabled = item.id === "agenda";` (todos los demás ítems tienen `disabled: true` y `badge: "Próximamente"`).
  - `menuFor.test.ts` líneas 22-23: `expect(items.slice(1).every((item) => item.disabled === true)).toBe(true);` y `expect(items.slice(1).every((item) => item.badge === "Próximamente")).toBe(true);`.
  - `menuFor.test.ts` líneas 38-40: aserción idéntica para recepción.
- `frontend/src/shared/components/AppShell.test.tsx`:
  - Líneas 67-79: Exige taxativamente que `within(nav).getAllByRole("button")` tenga longitud 5 para admin, con los nombres `["Turnos", "Horarios y bloqueos", "Catálogos", "Pacientes", "Usuarios y roles"]`, todos deshabilitados y con texto `"Próximamente"`.
  - Líneas 101-105: Exige lo mismo para recepción con longitud 4 (incluyendo `"Turnos"` como botón deshabilitado).
- `frontend/src/shared/api/types.ts` y `client.ts`:
  - `types.ts` líneas 10-14: `Violation` solo tipa `{ code: string; message: string; }`.
  - `client.ts` líneas 62-70: `asViolations` solo extrae `code` y `message`. Los campos complementarios (`conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval`, `referenceKind`) no se capturan actualmente.
  - `types.ts` líneas 16-23: `ApiErrorPayload` soporta `validation` (400), `auth` (401), `forbidden` (403), `conflict` (409), `unprocessable` (422) y `not_found` (404).

---

## 2. Hallazgos empíricos verificados

| # | Hallazgo | Evidencia | Impacto en C-29 |
|---|----------|-----------|-----------------|
| **H1** | `menuFor.ts` y `AppShell.test.tsx` verifican estrictamente que el ítem "Turnos" del menú principal esté deshabilitado con "Próximamente". | `frontend/src/features/auth/menuFor.test.ts:22-23,38-40` y `frontend/src/shared/components/AppShell.test.tsx:68-79,101-105`. | Habilitar "Turnos" en `menuFor.ts` **rompe inmediatamente 3 tests existentes** en `menuFor.test.ts` y `AppShell.test.tsx`. Para cumplir la regla dura de "no modificar tests existentes", el acceso a dar turno debe nacer en la agenda (`AgendaToolbar`) y no en el menú principal. |
| **H2** | jsdom 31.0.0 expone `HTMLDialogElement` pero `showModal()` y `close()` son `undefined`. | Verificado en C-35 explore (`docs/evidencias/explore-portada-y-acceso.md` H1). | Si se usa `<dialog>`, al abrirlo en jsdom debe usarse detección de capacidad: `typeof dialog.showModal === "function" ? dialog.showModal() : dialog.setAttribute("open", "")` para no arrojar `TypeError` y permitir renderizado en Vitest sin mocks globales (regla C1). |
| **H3** | `AgendaGrid` no tiene celdas o slots HTML discretos: es un lienzo continuo posicionado con porcentajes CSS (`top: X%`, `height: Y%`). | `frontend/src/features/agenda/AgendaGrid.tsx:81-125,207-212`. | No se puede hacer clic en un "hueco vacío" porque no existe un elemento DOM de hueco. Además, jsdom devuelve coordenadas `0` en `getBoundingClientRect()`, impidiendo medir clics por pixel. El prellenado debe resolverse mediante botón accesible "Nuevo turno" en la toolbar aprovechando los filtros actuales. |
| **H4** | `GET /api/patients` admite búsqueda textual por `query` (nombre o prefijo de DNI) y no implementa paginación en el backend. | `backend/app/api/patients.py:63-65` y `backend/app/repositories/patients.py:86-100`. | La UI puede usar un buscador de pacientes que consulte `GET /api/patients?query={texto}` (con debounce o al tipear ≥ 2 caracteres), mostrando las opciones coincidentes con nombre y DNI formateado. |
| **H5** | `POST /api/appointments` exige obligatoriamente zona horaria en `startAt`. Sin zona horaria responde 400. | `backend/app/api/schemas.py:279-284` (`validate_tz`). | El formulario debe componer la fecha local `YYYY-MM-DD` y hora `HH:MM` agregando el offset de la zona horaria provista por la API (o `DEFAULT_AGENDA_TIMEZONE`). Con `Intl.DateTimeFormat(..., { timeZone, timeZoneName: "longOffset" })` se obtiene el offset exacto (`-03:00`) sin instalar librerías. |
| **H6** | El backend ya formatea los mensajes de conflicto con el nombre del profesional/sillón, el intervalo en hora local y el id del turno/bloqueo que choca. | `backend/app/domain/violations.py:53-79` y `knowledge-base/07_flujos_principales.md:32-39`. | Al renderizar `violation.message` tal cual, la UI ya entrega al usuario toda la información contextual necesaria sin requerir transformaciones complejas en el cliente. |
| **H7** | `types.ts` y `client.ts` actualmente recortan las violaciones a `{ code, message }`. | `frontend/src/shared/api/types.ts:11-14` y `client.ts:62-70`. | Para resaltar el campo con `referenceKind` o asociar identificadores de turno/bloqueo, se debe extender la interfaz `Violation` en `types.ts` con campos opcionales (`conflictingAppointmentId?: string`, `conflictingBlockId?: string`, `referenceKind?: string`), manteniendo compatibilidad total con los tests de `client.test.ts`. |
| **H8** | `useAgenda` ya expone la función `refresh: () => void`. | `frontend/src/features/agenda/useAgenda.ts:38`. | Cuando el alta responde 201, el formulario ejecuta el callback `onSuccess` que invoca `state.refresh()`, actualizando la agenda inmediatamente. |

---

## 3. Plan de decisiones confirmadas

> Las siguientes decisiones fueron revisadas y confirmadas por la autora para orientar el propose y la implementación.

| # | Tema | Decisión confirmada | Detalle / Motivo técnico |
|---|------|---------------------|--------------------------|
| **D1** | **Dónde vive el formulario de dar turno** | **`<dialog>` modal accesible montado sobre `AgendaPage`**, disparado por un botón principal `"Nuevo turno"` en `AgendaToolbar` (solo visible para recepción y administrador). | Mantiene el contexto visual de la agenda (US-042, Flujo 1) y prepara el componente para ser reutilizado en C-30 (reprogramación). |
| **D2** | **Reutilización del `<dialog>` de C-35** | **Se reutiliza `shared/components/Dialog.tsx` creado en C-35 (no se crea otro)**. Sin focus trap manual: en navegador `showModal()` provee el focus trap y la inercia nativa; en `jsdom` alcanza el fallback del atributo `open`. | Evita duplicar componentes modales. Aprovecha el fallback probado en C-35 sin añadir complejidad de focus trap manual innecesaria. |
| **D3** | **Selección de paciente** | **Campo de búsqueda + botón "Buscar paciente" (también con Enter)** contra `GET /api/patients?query=`, sin combobox ni debounce/timers. Los resultados se muestran como un **grupo de radio buttons** (`name="patientId"`, cada opción con nombre y DNI). | Sin timers ni asincronía oculta (100% predecible en tests y en UI). Selección nativa clara con teclado (tab/flechas) y anuncio directo de resultados. |
| **D4** | **Prellenado desde la agenda** | **Prellenar automáticamente desde el estado de la toolbar**: fecha actual de la agenda (`effectiveDate`), profesional seleccionado (si hay filtro activo en toolbar o en vista semanal) y sillón seleccionado (si hay filtro activo). | `AgendaGrid` no tiene celdas discretas (es continuo porcentual) y jsdom no mide coordenadas. Evita alterar la grilla o romper tests de `AgendaView.test.tsx`. |
| **D5** | **Composición de fecha, hora y timezone** | **El offset se calcula con `Intl.DateTimeFormat` para la fecha y hora ELEGIDAS**, con el `timezone` que devuelve la API. Inputs nativos `date` y `time` (paso de 5 min) componiendo `${date}T${time}:00${offset}`. | Cumple la validación estricta de zona horaria del backend (`AppointmentInput`) usando el huso real en el instante elegido, sin librerías externas. |
| **D6** | **Sugerencia y edición de duración** | Al seleccionar una prestación de `GET /api/services`, el campo **Duración (minutos)** se inicializa con `service.defaultDurationMin`. El usuario puede editarlo libremente en múltiplos de 5 minutos (entre 5 y 480). | Cumple exactamente US-042 CA-2 y RN-AG-09: sugiere la duración estándar pero el operador puede ajustarla según el caso. |
| **D7** | **Renderizado de violaciones y errores** | **Resumen superior con `role="alert"` y foco programático al fallar**, con los mensajes de la API intactos y la referencia al turno o bloqueo que choca. `aria-invalid` aplica **solo en los campos de los errores 400 (`{ errors }`)**; las violaciones 409 y 422 **no se mapean a campos individuales**. | Muestra con total fidelidad las violaciones de dominio (US-042 CA-1) sin inventar heurísticas de mapeo de campo para conflictos de agenda, y reserva `aria-invalid` para errores de forma 400. |
| **D8** | **Manejo del éxito y actualización** | Al responder 201: (1) Se cierra el diálogo, (2) Se invoca `useAgenda.refresh()`, (3) Se emite un anuncio con `role="status"` / `aria-live="polite"` (`"Turno creado con éxito para el [fecha] a las [hora]"`), (4) El foco retorna al botón `"Nuevo turno"`. | Ciclo de usuario inmediato y accesible: la agenda se refresca y el nuevo turno queda visible. |
| **D9** | **Ítem "Turnos" en el menú principal (`menuFor.ts`)** | **Conservar "Turnos" deshabilitado con "Próximamente" en `menuFor.ts` durante C-29**. El formulario se abre exclusivamente desde `AgendaToolbar` en `/agenda`. | Habilitar "Turnos" en el menú rompería 3 tests existentes en `menuFor.test.ts` y `AppShell.test.tsx`. Se preserva la regla dura de no modificar tests preexistentes. |
| **D10** | **Estrategia de especificaciones OpenSpec** | **Crear la capability principal `openspec/specs/frontend-appointment-form/spec.md`** y marcar **`frontend-agenda` como MODIFIED** únicamente para registrar el botón de integración en la toolbar y el refresco. | La gestión del formulario de turno es una capacidad independiente que será reutilizada directamente en C-30 (`ui-reprogramar-cancelar-y-estados`). |

---

## 4. Contrato exacto de la API (`POST /api/appointments`)

### 4.1 Solicitud (Request)
- **Método y Ruta**: `POST /api/appointments`
- **Headers**:
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `Authorization: Bearer <access_token>`
- **Cuerpo JSON (`AppointmentInput`)**:
  ```json
  {
    "patientId": "00000000-0000-0000-0000-0000000000c1",
    "professionalId": "00000000-0000-0000-0000-000000000001",
    "chairId": "00000000-0000-0000-0000-0000000000b1",
    "serviceId": "00000000-0000-0000-0000-0000000000d2",
    "startAt": "2026-11-16T10:00:00-03:00",
    "durationMin": 45
  }
  ```
  *Nota*: `durationMin` es opcional; si no se envía, la API utiliza la duración por defecto de la prestación indicada en `serviceId`. `extra="forbid"`: enviar campos ajenos produce `400 Bad Request`.

### 4.2 Respuestas del Servidor

#### A. Éxito (`201 Created`)
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "patientId": "00000000-0000-0000-0000-0000000000c1",
  "professionalId": "00000000-0000-0000-0000-000000000001",
  "chairId": "00000000-0000-0000-0000-0000000000b1",
  "serviceId": "00000000-0000-0000-0000-0000000000d2",
  "startAt": "2026-11-16T13:00:00Z",
  "endAt": "2026-11-16T13:45:00Z",
  "status": "reservado"
}
```

#### B. Conflicto de Agenda (`409 Conflict`) — Ejemplo real con choque múltiple
```json
{
  "violations": [
    {
      "code": "PROFESSIONAL_OVERLAP",
      "message": "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (turno 00000000-0000-0000-0000-0000000000a1).",
      "conflictingAppointmentId": "00000000-0000-0000-0000-0000000000a1",
      "conflictingInterval": {
        "startAt": "2026-11-16T13:00:00Z",
        "endAt": "2026-11-16T13:30:00Z"
      }
    },
    {
      "code": "CHAIR_OVERLAP",
      "message": "El Sillón 1 está ocupado de 10:00 a 10:30 (turno 00000000-0000-0000-0000-0000000000a1).",
      "conflictingAppointmentId": "00000000-0000-0000-0000-0000000000a1",
      "conflictingInterval": {
        "startAt": "2026-11-16T13:00:00Z",
        "endAt": "2026-11-16T13:30:00Z"
      }
    }
  ]
}
```

#### C. Validez del Pedido (`422 Unprocessable Entity`) — Ejemplo turno pasado y referencia inexistente
```json
{
  "violations": [
    {
      "code": "IN_THE_PAST",
      "message": "El turno no puede comenzar en el pasado."
    },
    {
      "code": "UNKNOWN_REFERENCE",
      "message": "El paciente no existe.",
      "referenceKind": "PATIENT"
    }
  ]
}
```

#### D. Error de Validación de Entrada (`400 Bad Request`)
```json
{
  "errors": [
    {
      "field": "startAt",
      "type": "value_error",
      "message": "La fecha y hora debe incluir zona horaria."
    }
  ]
}
```

#### E. Error de Permisos (`403 Forbidden`)
```json
{
  "violations": [
    {
      "code": "FORBIDDEN_OPERATION",
      "message": "No tiene permiso para dar turnos."
    }
  ]
}
```

---

## 5. Escenarios candidatos y pruebas

### 5.1 Pruebas automatizadas de componentes (Vitest + jsdom bajo Regla C1)
*Sin `vi.mock`, `vi.spyOn`, fake timers ni stubs globales. Con `createApiClient({ fetchFn })` y `createFixedClock`.*

1. **Visibilidad y permisos**:
   - Para usuario `recepcion` o `administrador`, el botón `"Nuevo turno"` está presente en `AgendaToolbar` y habilitado.
   - Para usuario `odontologo`, el botón `"Nuevo turno"` no se renderiza.
2. **Ciclo de vida del diálogo**:
   - Al pulsar `"Nuevo turno"`, el diálogo se abre y el foco se coloca en el primer campo interactivo (búsqueda de paciente).
   - Pulsar `"Cancelar"` o presionar tecla `Escape` cierra el diálogo sin enviar ninguna solicitud y retorna el foco al botón `"Nuevo turno"`.
3. **Prellenado contextual**:
   - Al abrirse, la fecha se prellena con la fecha activa de la agenda (`effectiveDate`).
   - Si en la toolbar había seleccionado un profesional o un sillón, vienen preseleccionados en sus respectivos desplegables.
4. **Sugerencia de duración según prestación**:
   - Al cambiar la prestación seleccionada (ej. de `"Limpieza"` 45 min a `"Extracción"` 60 min), el campo de duración se actualiza automáticamente a 60.
   - El usuario puede editar manualmente la duración a otro valor (ej. 40 min).
5. **Búsqueda accesible de pacientes**:
   - Campo de búsqueda textual con botón explícito `"Buscar paciente"` (accionable con clic o presionando `Enter` en el input), sin combobox, sin debounce ni timers.
   - Consulta `GET /api/patients?query=...` y despliega los resultados como un grupo de radio buttons (`name="patientId"`), cada uno mostrando nombre completo y DNI.
   - Seleccionar un radio button asigna el `patientId` al formulario.
   - Si la búsqueda no arroja resultados, se presenta un mensaje de estado accesible `"No se encontraron pacientes"`.
6. **Alta exitosa (201)**:
   - Envío de formulario válido invoca `POST /api/appointments` con el cuerpo tipado y el offset calculado con `Intl.DateTimeFormat` para la fecha y hora elegidas según el `timezone` de la API.
   - Al recibir 201, se cierra el diálogo, se invoca `state.refresh()` y se anuncia la confirmación con `role="status"`.
7. **Renderizado de violaciones 409 y 422**:
   - Al recibir 409 con `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` (o 422 con `IN_THE_PAST` / `UNKNOWN_REFERENCE`), todas las violaciones se muestran en el alert de resumen superior (`role="alert"`) con sus textos íntegros del backend y la referencia al turno o bloqueo que choca.
   - Las violaciones 409 y 422 **no se mapean a campos individuales** con `aria-invalid`.
   - El foco se traslada programáticamente al contenedor de alertas (`role="alert"`).
8. **Validación de errores 400**:
   - Un error 400 con `errors: [{ field, type, message }]` marca únicamente los campos señalados con `aria-invalid="true"` y muestra el mensaje correspondiente junto al campo y en el resumen.
9. **Manejo de 401 y 403**:
   - Un 403 muestra la violación `"No tiene permiso para dar turnos."` en el alerta.
   - Un 401 es interceptado por `AuthContext` delegando en la expiración de sesión.

### 5.2 Verificación visual obligatoria (Capturas reales en navegador)
*Dado que jsdom no calcula layout ni anchos:*
- **1440 px (Escritorio)**: Diálogo modal centrado sobre la grilla con backdrop atenuado; campos alineados en grid de dos columnas; alert de violaciones legible con mensajes largos de solapamiento sin desbordes.
- **768 px (Tablet)**: Diálogo adaptado a pantalla intermedia; lista de resultados de pacientes (radio buttons) cómoda para interacción táctil (mínimo 44 px de altura por fila); botones de acción alineados.
- **390 px (Móvil)**: Formulario colapsado en columna única; botones de acción apilados verticalmente; sin scroll horizontal; selector de fecha y hora nativo cómodo.

---

## 6. Riesgos identificados y mitigaciones

| Riesgo | Probabilidad / Impacto | Mitigación propuesta |
|--------|------------------------|----------------------|
| **R1. Rotura de tests existentes de `menuFor.test.ts` y `AppShell.test.tsx`** | Alta / Crítico | **Decisión D9**: No habilitar el ítem "Turnos" en el menú principal en este change. Dar turnos es una acción directa de la agenda (`AgendaToolbar`). Cero tests existentes modificados. |
| **R2. Incompatibilidad de `<dialog>` en jsdom 31 (`showModal` undefined)** | Alta / Alto | **Decisión D2**: Reutilizar `shared/components/Dialog.tsx` creado en C-35, el cual implementa fallback con atributo `open` en jsdom y `showModal()` en navegador, sin focus trap manual. |
| **R3. Alteración o rotura de tests en `AgendaView.test.tsx`** | Media / Alto | **Decisión D4**: No intervenir la estructura interna de `AgendaGrid.tsx`. El botón de apertura se coloca en `AgendaToolbar.tsx` mediante prop opcional `onNewAppointment`, garantizando que ningún test de grilla o toolbar se vea afectado. |
| **R4. Error 400 por fecha sin zona horaria en el backend** | Media / Medio | **Decisión D5**: Construir el string ISO calculando el offset para la fecha y hora elegidas con `Intl.DateTimeFormat` nativo y el `timezone` de la API antes de emitir la llamada al backend. |
| **R5. Discrepancia de tipos en `types.ts` al omitir metadatos de conflicto** | Baja / Medio | Extender `Violation` en `types.ts` con propiedades opcionales (`conflictingAppointmentId?: string`, `conflictingBlockId?: string`, `conflictingInterval?: { startAt: string, endAt: string }`, `referenceKind?: string`), manteniendo compatibilidad estricta hacia atrás con `client.test.ts`. |
