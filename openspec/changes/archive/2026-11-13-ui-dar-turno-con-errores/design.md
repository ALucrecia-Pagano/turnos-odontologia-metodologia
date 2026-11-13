# Design

## Context

C-27 y C-28 implementaron la visualización de la agenda diaria y semanal en `frontend/src/features/agenda/`. La API de turnos (`backend/app/api/appointments.py`, implementada en C-22) valida en el dominio todas las reglas de solapamiento por profesional y sillón, horarios de atención, bloqueos, turnos pasados y referencias activas, devolviendo respuestas tipadas con códigos estables y mensajes en español.

C-29 implementa la interfaz de usuario para dar turnos desde la agenda mediante un modal sobre `AgendaPage`, mostrando fielmente los rechazos de dominio. Para ello, C-29 crea la primitiva compartida `frontend/src/shared/components/Dialog.tsx` con `<dialog>` nativo accesible y fallback para `jsdom`.

Restricciones que rigen este diseño:
- Regla de no modificar tests existentes: `menuFor.test.ts` y `AppShell.test.tsx` verifican estrictamente que el ítem "Turnos" del menú principal esté deshabilitado con "Próximamente" (5 botones para admin, 4 para recepción). Habilitarlo allí rompería 3 tests existentes.
- Los tests nuevos se ubican en archivos separados (`client.violations.test.ts`, `AgendaToolbar.nuevoTurno.test.tsx`, `AgendaPage.nuevoTurno.test.tsx`), garantizando que `git diff main --stat -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'` con `--diff-filter=M` resulte estrictamente vacío.
- `AgendaGrid.tsx` es una grilla continua porcentual sin elementos de celda discretos, y `jsdom` no mide coordenadas de clic (`getBoundingClientRect` retorna 0). No se pueden inyectar clics a huecos en la grilla sin arriesgar los 15 tests existentes de `AgendaView.test.tsx`.
- Regla C1: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers ni MSW. Todo se testea con clientes inyectados (`createApiClient({ fetchFn })`), `createFixedClock` y `createMemoryRouter`. No se asignan ni borran globals.
- Cero librerías nuevas: el cálculo de zona horaria y armado de `startAt` se realiza exclusivamente con APIs nativas de `Intl`.
- Paleta Aqua de C-34: sin colores nuevos; se utilizan los tokens semánticos existentes de `tokens.css`.

## Goals / Non-goals

**Goals:**
- Formulario de alta modal sobre la agenda, abierto desde `AgendaToolbar` para recepción y administrador.
- Primitiva compartida accesible `shared/components/Dialog.tsx` (`<dialog>` nativo accesible, sin role redundante ni focus trap manual superfluo).
- Búsqueda determinística de pacientes por texto + botón "Buscar paciente" con radio buttons, sin timers ni debounce.
- Prellenado contextual con fecha, profesional y sillón activos en la toolbar.
- Duración sugerida desde la prestación y editable en múltiplos de 5 min.
- Cálculo exacto de offset con `Intl` nativo para la fecha y hora elegidas según `timezone` de la API.
- Renderizado fiel de violaciones 409 y 422 en alerta superior con `role="alert"` y foco programático, sin mapeo de campos.
- Mapeo de `aria-invalid` únicamente para errores de entrada 400 (`{ errors }`).
- Cierre, refresco de agenda y anuncio con `role="status"` ante 201 Created.
- Preservar intactos todos los archivos de test preexistentes.

**Non-goals:**
- Reprogramar, cancelar o cambiar estado (corresponde a C-30).
- Habilitar "Turnos" en el menú principal (`menuFor.ts`).
- Validación de solapamientos o reglas de negocio en el cliente.
- Creación de nuevos pacientes o prestaciones desde este formulario.

## Decisions

### D1 — Ubicación del formulario: `<dialog>` modal sobre `AgendaPage`

El formulario vive en el componente `frontend/src/features/appointments/AppointmentFormDialog.tsx`, montado sobre `AgendaPage.tsx`. Se dispara mediante el botón accesible `"Nuevo turno"` en `AgendaToolbar.tsx` (a través de la prop opcional `onNewAppointment`), visible y habilitado solo cuando el usuario tiene rol `recepcion` o `administrador`.

*Alternativa descartada:* Una ruta propia `/turnos/nuevo` desconectaría visualmente al usuario del día y la semana que está organizando y dejaría una ruta huérfana mientras "Turnos" en el menú principal permanece deshabilitado.

### D2 — Primitiva compartida `shared/components/Dialog.tsx`

Se crea la primitiva modal compartida `frontend/src/shared/components/Dialog.tsx` (+ `Dialog.module.css` y `Dialog.test.tsx`):
1. **Elemento nativo sin redundancias**: Utiliza `<dialog>` nativo sin el atributo `role="dialog"` redundante (el tag `<dialog>` ya tiene rol semántico implícito dialog según W3C ARIA).
2. **Atributos de accesibilidad**: Exige obligatoriamente la propiedad `labelledBy` (`aria-labelledby={labelledBy}`). Aplica `aria-modal="true"` únicamente como fallback en entornos donde `showModal` no exista.
3. **Apertura y detección de entorno**: Si `typeof dialog.showModal === "function"`, invoca `showModal()`. En entornos de prueba como `jsdom` (donde `showModal` no está implementado), aplica el atributo nativo `open` (`<dialog open>`). Esta guarda condicional es código de soporte nativo y no un stub: no asigna ni borra globals en el entorno ni en `window`.
4. **Cierre y tecla Escape**: En navegadores reales, la tecla Escape o el cierre nativo disparan el evento `cancel`; el componente escucha `onCancel`, ejecuta `preventDefault()` y llama a `onClose()`. En `jsdom`, un listener `onKeyDown` de la tecla `"Escape"` invoca `onClose()`. `onClose` se invoca exactamente una sola vez por evento de cierre.
5. **Retorno de foco**: El foco vuelve a `returnFocusRef` una sola vez en el efecto de cierre (cuando `open` pasa de `true` a `false`). No se traslada foco en los handlers de tecla o cancelación para evitar ejecuciones duplicadas de foco.
6. **Sin focus trap manual**: No se implementa focus trap con listeners manuales ni librerías externas; se confía plenamente en la semántica modal nativa de `<dialog>`.
7. **Estilos con tokens Aqua**: Diseñado con variables de diseño existentes de `tokens.css` (`--color-surface`, `--color-text`, `--radius-md`, `--shadow-md`, `--space-4`, etc.).

*Alternativa descartada:* Modificar prototipos globales de `HTMLDialogElement` en `setupFiles` de Vitest (prohibido por la Regla C1).

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
- **Permisos (403)**: Muestra la violación `FORBIDDEN_OPERATION` en el resumen de alertas ("No tiene permiso para dar turnos.").
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

### D10 — Nueva capability `frontend-appointment-form` y requisito ADDED en `frontend-agenda`

Se crea la capability principal `openspec/specs/frontend-appointment-form/spec.md` para albergar la primitiva compartida `Dialog` y todos los requisitos y escenarios del formulario de alta de turnos (que C-30 reutilizará directamente para reprogramación). La capability existente `frontend-agenda` incorpora el requisito `ADDED` ("Acción Nuevo turno en la agenda") para registrar el botón `"Nuevo turno"` restringido a roles autorizados (`recepcion` y `administrador`) y la invocación de `refresh()`.

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

#### 2. Conflicto de Agenda (`409 Conflict`) — Violaciones múltiples con referencia copiadas del backend
```json
{
  "violations": [
    {
      "code": "PROFESSIONAL_OVERLAP",
      "message": "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1).",
      "conflictingAppointmentId": "00000000-0000-0000-0000-0000000000a1",
      "conflictingInterval": {
        "startAt": "2026-11-16T13:00:00Z",
        "endAt": "2026-11-16T13:30:00Z"
      }
    },
    {
      "code": "CHAIR_OVERLAP",
      "message": "El Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno 00000000-0000-0000-0000-0000000000a1).",
      "conflictingAppointmentId": "00000000-0000-0000-0000-0000000000a1",
      "conflictingInterval": {
        "startAt": "2026-11-16T13:00:00Z",
        "endAt": "2026-11-16T13:30:00Z"
      }
    }
  ]
}
```

#### 3. Validez del Pedido (`422 Unprocessable Entity`) — Turno en el pasado y referencia inválida copiadas del backend
```json
{
  "violations": [
    {
      "code": "IN_THE_PAST",
      "message": "El inicio del turno (16/11/2026 10:00, hora local) es anterior al momento actual (16/11/2026 10:00:30, hora local): no se pueden dar turnos en el pasado."
    },
    {
      "code": "UNKNOWN_REFERENCE",
      "message": "El paciente indicado no existe (id 00000000-0000-0000-0000-0000000000c1).",
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

#### 5. Operación Prohibida (`403 Forbidden`) — Mensaje copiado de PERMISSION_MESSAGES
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
│       ├── AgendaToolbar.tsx                 # Incorpora prop opcional onNewAppointment y botón
│       ├── AgendaToolbar.nuevoTurno.test.tsx # Tests aislados para acción Nuevo turno en toolbar
│       ├── AgendaPage.tsx                    # Renderiza AppointmentFormDialog conectado a useAgenda
│       └── AgendaPage.nuevoTurno.test.tsx    # Tests aislados para integración modal en página
└── shared/
    ├── components/
    │   ├── Dialog.tsx                        # Primitiva modal <dialog> accesible
    │   ├── Dialog.module.css                 # Estilos base con tokens Aqua
    │   └── Dialog.test.tsx                   # Tests C1 de la primitiva Dialog
    └── api/
        ├── types.ts                          # Extiende Violation con campos opcionales
        ├── client.ts                         # asViolations captura campos opcionales de conflicto
        └── client.violations.test.ts         # Tests aislados para campos opcionales de violaciones
```
