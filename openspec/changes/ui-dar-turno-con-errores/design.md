# Design

## Context

C-27 y C-28 implementaron la visualización de la agenda diaria y semanal en `frontend/src/features/agenda/`. La API de turnos (`backend/app/api/appointments.py`, implementada en C-22) valida en el dominio todas las reglas de solapamiento por profesional y sillón, horarios de atención, bloqueos, turnos pasados y referencias activas, devolviendo respuestas tipadas con códigos estables y mensajes en español. C-35 propone la primitiva compartida `frontend/src/shared/components/Dialog.tsx` con `<dialog>` nativo y fallback para jsdom.

C-29 implementa la interfaz de usuario para dar turnos desde la agenda mediante un modal sobre `AgendaPage`, mostrando fielmente los rechazos de dominio.

Restricciones que rigen este diseño:
- Regla de no modificar tests existentes: `menuFor.test.ts` y `AppShell.test.tsx` verifican estrictamente que el ítem "Turnos" del menú principal esté deshabilitado con "Próximamente" (5 botones para admin, 4 para recepción). Habilitarlo allí rompería 3 tests existentes.
- `AgendaGrid.tsx` es una grilla continua porcentual sin elementos de celda discretos, y `jsdom` no mide coordenadas de clic (`getBoundingClientRect` retorna 0). No se pueden inyectar clics a huecos en la grilla sin arriesgar los 15 tests existentes de `AgendaView.test.tsx`.
- Regla C1: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers ni MSW. Todo se testea con clientes inyectados (`createApiClient({ fetchFn })`), `createFixedClock` y `createMemoryRouter`.
- Cero librerías nuevas: el cálculo de zona horaria y armado de `startAt` se realiza exclusivamente con APIs nativas de `Intl`.
- Paleta Aqua de C-34: sin colores nuevos; se utilizan los tokens semánticos existentes de `tokens.css`.

## Goals / Non-goals

**Goals:**
- Formulario de alta modal sobre la agenda, abierto desde `AgendaToolbar` para recepción y administrador.
- Reutilización de `shared/components/Dialog.tsx` de C-35 (sin focus trap manual redundante).
- Búsqueda determinística de pacientes por texto + botón "Buscar paciente" con radio buttons, sin timers ni debounce.
- Prellenado contextual con fecha, profesional y sillón activos en la toolbar.
- Duración sugerida desde la prestación y editable en múltiplos de 5 min.
- Cálculo exacto de offset con `Intl` nativo para la fecha y hora elegidas según `timezone` de la API.
- Renderizado fiel de violaciones 409 y 422 en alerta superior con `role="alert"` y foco programático, sin mapeo de campos.
- Mapeo de `aria-invalid` únicamente para errores de entrada 400 (`{ errors }`).
- Cierre, refresco de agenda y anuncio con `role="status"` ante 201 Created.

**Non-goals:**
- Reprogramar, cancelar o cambiar estado (corresponde a C-30).
- Habilitar "Turnos" en el menú principal (`menuFor.ts`).
- Validación de solapamientos o reglas de negocio en el cliente.
- Creación de nuevos pacientes o prestaciones desde este formulario.

## Decisions

### D1 — Ubicación del formulario: `<dialog>` modal sobre `AgendaPage`

El formulario vive en el componente `frontend/src/features/appointments/AppointmentFormDialog.tsx`, montado sobre `AgendaPage.tsx`. Se dispara mediante el botón accesible `"Nuevo turno"` en `AgendaToolbar.tsx` (a través de la prop opcional `onNewAppointment`), visible y habilitado solo cuando el usuario tiene rol `recepcion` o `administrador`.

*Alternativa descartada:* Una ruta propia `/turnos/nuevo` desconectaría visualmente al usuario del día y la semana que está organizando y dejaría una ruta huérfana mientras "Turnos" en el menú principal permanece deshabilitado.

### D2 — Reutilización de `shared/components/Dialog.tsx` de C-35

Se reutiliza la primitiva modal compartida `shared/components/Dialog.tsx` introducida en C-35. En un navegador real, `dialog.showModal()` provee el focus trap nativo, la inercia del fondo y el oscurecimiento del backdrop. En el entorno `jsdom` de Vitest, el componente aplica el atributo `open` (`<dialog open>`), permitiendo que el contenido sea accesible en Testing Library sin stubs globales. No se agrega focus trap manual redundante.

*Alternativa descartada:* Crear un componente modal propio duplicado en `features/appointments`, lo que violaría la reutilización de componentes base.

### D3 — Búsqueda de pacientes con radio buttons, sin combobox ni timers

El paciente se selecciona mediante un campo de texto `<input type="search">` junto con un botón explícito `<button type="button">Buscar paciente</button>` (disparable también pulsando `Enter` en el input). Al activarse, invoca `GET /api/patients?query={texto}`. Los resultados devueltos se listan como un grupo de radio buttons con `name="patientId"`, donde cada opción muestra el nombre del paciente y su DNI formateado. Si no hay resultados, se muestra un mensaje informativo accesible.

*Alternativa descartada:* Un combobox con debounce y timers (`setTimeout`), descartado porque introduce asincronía oculta difícil de predecir en tests y viola la simplicidad exigida por la cátedra.

### D4 — Prellenado contextual desde la barra de agenda

Al abrirse el formulario, se inicializa automáticamente:
1. `date`: con la fecha efectiva de la agenda (`effectiveDate`).
2. `professionalId`: con el profesional activo en el filtro de la toolbar o en la vista semanal (si no hay filtro, queda en blanco para que el usuario elija).
3. `chairId`: con el sillón activo en el filtro de la toolbar (si no hay filtro, queda en blanco).
4. `time`: vacío o primer horario sugerido, requiriendo selección explícita del operador.

*Alternativa descartada:* Detección de clics por coordenadas sobre `AgendaGrid`. Como la grilla es un lienzo continuo porcentual y jsdom devuelve 0 en las mediciones de pantalla, calcular clics por pixel es inviable y alteraría `AgendaGrid.tsx` poniendo en riesgo sus tests existentes.

### D5 — Cálculo de fecha, hora y timezone con `Intl` nativo

El backend exige obligatoriamente zona horaria en el campo `startAt` de `POST /api/appointments` (400 si falta). El formulario expone `<input type="date">` e `<input type="time" step="300">`. Al enviar el formulario, se construye el instante combinando la fecha y la hora elegidas con el offset local correspondiente:

```typescript
function buildStartAtIso(dateStr: string, timeStr: string, timeZone: string): string {
  // Se crea una fecha aproximada en UTC con la fecha y hora elegidas
  const [year, month, day] = dateStr.split("-").map(Number);
  const [hours, minutes] = timeStr.split(":").map(Number);
  const probeDate = new Date(Date.UTC(year, month - 1, day, hours, minutes));

  // Se extrae el offset real con Intl para la zona horaria de la API
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "longOffset",
  }).formatToParts(probeDate);
  const rawOffset = parts.find((p) => p.type === "timeZoneName")?.value ?? "GMT";
  const offset = rawOffset.replace("GMT", "") || "+00:00";

  return `${dateStr}T${timeStr}:00${offset}`;
}
```

*Alternativa descartada:* Convertir a UTC fijo con sufijo `Z` en el cliente o instalar `date-fns-tz`/`dayjs` (prohibido por la regla de no instalar librerías).

### D6 — Duración sugerida desde la prestación

Al seleccionar una prestación del desplegable (cargado desde `GET /api/services?active=true`), el campo **Duración (minutos)** se actualiza automáticamente con `service.defaultDurationMin`. El usuario puede modificar manualmente el valor mediante un `<input type="number" step="5" min="5" max="480">`.

*Alternativa descartada:* Duración fija no editable, que incumpliría US-042 CA-2.

### D7 — Renderizado de violaciones y mapeo de errores

- **Violaciones de dominio (409 y 422)**: Se renderizan en un contenedor superior con `role="alert"` y `aria-live="assertive"`. Cada violación muestra su `message` tal cual lo devolvió la API (con el turno o bloqueo en conflicto ya incorporado en el texto por el backend) junto con su `code` en un badge. Al recibir la respuesta de error, el foco se traslada programáticamente al contenedor de alerta. Las violaciones 409 y 422 **no se mapean a campos individuales con `aria-invalid`**.
- **Errores de validación (400)**: Si la API responde 400 `{ errors: [...] }`, se marca con `aria-invalid="true"` únicamente el control correspondiente a cada `field` informado y se muestra el mensaje de error inline, además de listarse en el resumen.
- **Permisos (403)**: Muestra la violación `FORBIDDEN_OPERATION` en el resumen de alertas.
- **Sesión vencida (401)**: Interceptado por `AuthContext`, cerrando el diálogo y redirigiendo al login.

*Alternativa descartada:* Mapeo heurístico de violaciones 409 a campos individuales (ej. marcar el input de hora ante `PROFESSIONAL_OVERLAP`), descartado porque un solapamiento involucra al profesional, al sillón y al horario en conjunto, no a un único campo de entrada.

### D8 — Éxito, refresco de agenda y anuncio accesible

Al recibir `201 Created`:
1. Se limpia el estado interno del formulario.
2. Se cierra el modal `<dialog>`.
3. Se invoca `refresh()` del hook `useAgenda`.
4. Se emite un anuncio para lectores de pantalla mediante un elemento con `role="status"` y `aria-live="polite"`: `"Turno creado con éxito para el [fecha] a las [hora]"`.
5. El foco retorna al botón `"Nuevo turno"`.

### D9 — "Turnos" en `menuFor.ts` permanece deshabilitado

Para no violar la regla dura que prohíbe modificar tests existentes (`menuFor.test.ts:22-23,38-40` y `AppShell.test.tsx:68-79,101-105`), el ítem "Turnos" del menú principal se mantiene con `disabled: true` y `badge: "Próximamente"`. El acceso a dar turno se canaliza íntegramente a través de la barra de herramientas de la agenda.

### D10 — Nueva capability `frontend-appointment-form` y delta de `frontend-agenda`

Se crea la capability principal `openspec/specs/frontend-appointment-form/spec.md` para albergar todos los requisitos y escenarios del formulario de alta de turnos (que C-30 reutilizará directamente para reprogramación). La capability existente `frontend-agenda` solo recibe un delta `MODIFIED` en el requisito de navegación de la barra para registrar el botón `"Nuevo turno"` y la invocación de `refresh()`.

---

## Contrato de API (`POST /api/appointments`)

### Solicitud (Request)
- **Método**: `POST /api/appointments`
- **Headers**:
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `Authorization: Bearer <access_token>`
- **Cuerpo (`AppointmentInput`)**:
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

### Respuestas reales según el backend

#### 1. Éxito (`201 Created`)
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

#### 2. Conflicto de Agenda (`409 Conflict`) — Violaciones múltiples con referencia
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

#### 3. Validez del Pedido (`422 Unprocessable Entity`) — Turno en el pasado y referencia inválida
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

#### 4. Validación de Entrada (`400 Bad Request`)
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

#### 5. Operación Prohibida (`403 Forbidden`)
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

## Estructura de componentes y archivos

```
frontend/src/
├── features/
│   ├── appointments/
│   │   ├── AppointmentFormDialog.tsx         # Modal <dialog> con el formulario
│   │   ├── AppointmentFormDialog.module.css  # Estilos con tokens de diseño Aqua
│   │   ├── AppointmentFormDialog.test.tsx    # Tests C1 de integración del formulario
│   │   ├── PatientSearchGroup.tsx            # Búsqueda de pacientes con radio buttons
│   │   ├── PatientSearchGroup.module.css     # Estilos de búsqueda y lista de pacientes
│   │   └── PatientSearchGroup.test.tsx       # Tests C1 unitarios del componente de pacientes
│   └── agenda/
│       ├── AgendaToolbar.tsx                 # Incorpora prop onNewAppointment y botón
│       ├── AgendaToolbar.test.tsx            # Se preservan tests y se prueba prop opcional
│       └── AgendaPage.tsx                    # Renderiza AppointmentFormDialog conectado a useAgenda
└── shared/
    └── api/
        ├── types.ts                          # Extiende Violation con campos opcionales
        └── client.ts                         # asViolations captura campos opcionales de conflicto
```
