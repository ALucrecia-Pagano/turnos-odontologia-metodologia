# Verificación de C-29 — ui-dar-turno-con-errores

## Resultado

Todos los números provienen de las ejecuciones reales y archivos de evidencia enlazados.

- Tareas: implementadas según [tasks.md](../../openspec/changes/ui-dar-turno-con-errores/tasks.md).
- Vitest: suite completa pasando en verde (línea base de 164 tests intactos + 19 tests nuevos de C-29 = 183 tests en verde); `tsc --noEmit` y `eslint .` con código 0 y sin warnings.
- Mutaciones: 19/19 hicieron fallar su test respectivo (una mutación por cada test nuevo de C-29); mutaciones inválidas: 0; 0 sobrevivientes; SHA-256 de producción intacto.
- Trazabilidad: 16 escenarios probados mediante Vitest y 3 escenarios de adaptabilidad visual verificados visualmente (capturas independientes a cargo de Claude).
- Línea de base desde `frontend/`: [baseline-C-29.txt](baseline-C-29.txt) (164 tests pasando en 41 archivos).
- `tsc --noEmit` y `eslint .`: [tooling-C-29.txt](tooling-C-29.txt).
- `npm run build`: [build-C-29.txt](build-C-29.txt).
- Mutaciones: [mutaciones-C-29.txt](mutaciones-C-29.txt), generado por [mutaciones-C-29.py](mutaciones-C-29.py).
- Trazabilidad: [trazabilidad-C-29.txt](trazabilidad-C-29.txt), generado por [trazabilidad-C-29.py](trazabilidad-C-29.py).
- Diff de tests existentes: [diff-tests-existentes-C-29.txt](diff-tests-existentes-C-29.txt) (estrictamente vacío, solo archivos nuevos agregados).
- Evidencias RED/GREEN (TDD): carpetas [red-C-29/](red-C-29/) y [green-C-29/](green-C-29/).

---

## Regla C1 y diseño accesible (D1 a D5)

- **Sin mocks ni reemplazos globales (Regla C1)**: todo el código de test utiliza funciones `fetch` inyectadas que devuelven instancias reales de `Response` a través de `createApiClient({ fetchFn })`. Prohibidos `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` y MSW. El tiempo se fija mediante `createFixedClock`.
- **Primitiva Dialog accesible**: elemento `<dialog>` nativo sin atributo redundante `role="dialog"`, con `aria-labelledby` obligatorio y `aria-modal="true"` solo en fallback (jsdom). Soporte de apertura con atributo `open` y método `showModal()`.
- **Búsqueda de pacientes con radio group**: radiogroup accesible con `role="radiogroup"` y `aria-label="Pacientes encontrados"`, selección por clic o teclado con soporte de flechas nativo.
- **Formulario y gestión de errores de dominio**:
  - 400: errores de entrada mapeados con `aria-invalid="true"` únicamente a los campos afectados (`durationMin`, etc.) y mensaje inline de error.
  - 409 y 422: violaciones de agenda presentadas en el contenedor superior de alertas con `role="alert"` y `aria-live="assertive"`, conservando textualmente los códigos y mensajes del backend con sus referencias de colisión (`conflictingAppointmentId`, `conflictingBlockId`, etc.), sin marcar `aria-invalid` en los inputs.
  - 403: permisos denegados mostrados en el alert superior sin desloguear la sesión.
  - Foco programático trasladado inmediatamente al resumen de alerta ante rechazos.
  - 201: confirmación mediante anuncio accesible con `role="status"` y retorno de foco al elemento disparador ("Nuevo turno").
- **Zona horaria y cálculo de offset**: `startAt` formateado con `Intl.DateTimeFormat` nativo con `longOffset` para la fecha elegida y la zona horaria dinámica de la API (`America/Argentina/Buenos_Aires`).

---

## Desvíos y notas técnicas

1. **Guarda de cierre para tecla Escape en navegadores reales vs jsdom**:
   - *Comportamiento*: En un navegador real, al presionar Escape sobre un elemento `<dialog>` modal, el motor dispara un evento `keydown` y luego el evento nativo `cancel`.
   - *Implementación*: En `Dialog.tsx`, se implementó una guarda mediante `closeHandledRef`: el manejador de `keydown` efectúa `preventDefault()` e invoca `onClose()` marcando `closeHandledRef.current = true`. El manejador `onCancel` hace siempre `preventDefault()` y llama a `onClose()` únicamente si la guarda no estaba marcada. Al abrir el diálogo, la guarda se restablece en `false`. En `useLayoutEffect`, al pasar `open` de `true` a `false` (o al desmontar), el foco se retorna una sola vez a `returnFocusRef`. En `jsdom`, el evento nativo `cancel` no es despachado automáticamente por el entorno sintético, por lo que el cierre por Escape se valida en tests a través de `fireEvent.keyDown(dialog, { key: "Escape" })`.

2. **Verificación visual independiente de adaptabilidad**:
   - Los 3 escenarios de adaptabilidad visual del formulario (1440 px, 768 px y 390 px) no se comprueban con tests sintéticos de Vitest ni mutaciones, sino que quedan a cargo de la verificación visual independiente con capturas de pantalla (`docs/evidencias/capturas/C-29-*.png`) documentadas en la tarea 8.1.

---

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby` | `frontend/src/shared/components/Dialog.tsx` | `-        dialog.setAttribute("open", ""); +        // dialog.setAttribute("open", "");` | `AssertionError: expected null not to be null` |
| 2 | `Escape llama onClose exactamente una vez` | `frontend/src/shared/components/Dialog.tsx` | `-    if (event.key !== "Escape") { +    if (event.key !== "Enter") {` | `AssertionError: expected +0 to be 1 // Object.is equality` |
| 3 | `al pasar open de true a false el foco vuelve a returnFocusRef` | `frontend/src/shared/components/Dialog.tsx` | `-      returnFocusRef?.current?.focus(); +      // returnFocusRef?.current?.focus();` | `Error: expect(element).toHaveFocus()` |
| 4 | `captura conflictingAppointmentId, conflictingBlockId, conflictingInterval y referenceKind` | `frontend/src/shared/api/client.ts` | `-      violation.referenceKind = item.referenceKind; +      // violation.referenceKind = i` | `AssertionError: expected undefined to be 'PATIENT' // Object.is equality` |
| 5 | `renderizado inicial: input de búsqueda, botón Buscar paciente habilitado y sin radio buttons` | `frontend/src/features/appointments/PatientSearchGroup.tsx` | `-          disabled={isLoading} +          disabled={true}` | `Error: expect(element).toBeEnabled()` |
| 6 | `búsqueda con resultados muestra radio buttons con nombre y DNI` | `frontend/src/features/appointments/PatientSearchGroup.tsx` | `-                {p.fullName} (DNI {p.dni}) +                {p.fullName}` | `AssertionError: expected null not to be null` |
| 7 | `búsqueda sin resultados muestra aviso accesible y sin radio buttons` | `frontend/src/features/appointments/PatientSearchGroup.tsx` | `-          No se encontraron pacientes +          Sin resultados` | `AssertionError: expected null not to be null` |
| 8 | `selección por clic o teclado invoca onSelectPatient con el id correspondiente` | `frontend/src/features/appointments/PatientSearchGroup.tsx` | `-                onChange={() => onSelectPatient(p.id)} +                onChange={() => u` | `AssertionError: expected null to be '00000000-0000-0000-0000-0000000000c1' // Object.is eq` |
| 9 | `apertura y foco inicial con prellenado contextual` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      patientSearchInputRef.current?.focus(); +      // patientSearchInputRef.current?.fo` | `Error: expect(element).toHaveFocus()` |
| 10 | `sugerencia y edición de duración según prestación` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      setDurationMin(s.defaultDurationMin); +      setDurationMin(15);` | `AssertionError: expected '15' to be '60' // Object.is equality` |
| 11 | `armado de startAt con offset exacto para la fecha elegida y timezone de la API` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-  return '${dateStr}T${timeStr}:00${offset}'; +  return '${dateStr}T${timeStr}:00Z';` | `AssertionError: expected '2026-11-16T10:00:00Z' to be '2026-11-16T10:00:00-03:00' // Objec` |
| 12 | `envío exitoso 201 cierra el modal, llama onSuccess, emite anuncio y devuelve foco` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      onSuccess?.(); +      // onSuccess?.();` | `AssertionError: expected false to be true // Object.is equality` |
| 13 | `respuesta 409 con violaciones múltiples muestra alert superior intacto, foco al alert y campos sin aria-invalid` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-                  <span className={styles.codeBadge}>{v.code}</span> +                  {` | `AssertionError: expected null not to be null` |
| 14 | `rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        result.error.kind === "unprocessable" \|\| +        // result.error.kind === "unpro` | `AssertionError: expected null not to be null` |
| 15 | `mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        setFieldErrors(mappedErrors); +        // setFieldErrors(mappedErrors);` | `Error: expect(element).toHaveAttribute("aria-invalid", "true") // element.getAttribute("ar` |
| 16 | `respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        result.error.kind === "forbidden" +        result.error.kind === "unknown"` | `AssertionError: expected null not to be null` |
| 17 | `pulsar Cancelar cierra el diálogo y devuelve el foco al elemento de apertura` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-              onClick={onClose} +              onClick={() => undefined}` | `AssertionError: expected true to be false // Object.is equality` |
| 18 | `controla la visibilidad por rol del botón Nuevo turno y dispara onNewAppointment al clickear` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-    (userRole === "recepcion" \|\| userRole === "administrador") && +    (userRole === "adm` | `AssertionError: expected null not to be null` |
| 19 | `al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda` | `frontend/src/features/agenda/AgendaPage.tsx` | `-          onSuccess={state.refresh} +          // onSuccess={state.refresh}` | `AssertionError: expected 1 to be greater than 1` |
<!-- mutaciones:fin -->

---

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Capacidad | Requisito | Escenario | Test Vitest / Verificación | Mutación asociada |
|---|---|---|---|---|---|
| 1 | `frontend-agenda` | Acción Nuevo turno en la agenda | Visible para recepción | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > controla la visibilidad por rol del botón Nuevo turno y dispara onNewAppointment al clickear | M18: restricción de botón Nuevo turno solo a rol administrador |
| 2 | `frontend-agenda` | Acción Nuevo turno en la agenda | Visible para administrador | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > controla la visibilidad por rol del botón Nuevo turno y dispara onNewAppointment al clickear | M18: restricción de botón Nuevo turno solo a rol administrador |
| 3 | `frontend-agenda` | Acción Nuevo turno en la agenda | No visible para odontólogo | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > controla la visibilidad por rol del botón Nuevo turno y dispara onNewAppointment al clickear | M18: restricción de botón Nuevo turno solo a rol administrador |
| 4 | `frontend-agenda` | Acción Nuevo turno en la agenda | Refresco tras alta | src/features/agenda/AgendaPage.nuevoTurno.test.tsx > al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda | M19: omisión de refresh en onSuccess de AppointmentFormDialog |
| 5 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby | src/shared/components/Dialog.test.tsx > abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby | M1: eliminación de dialog.setAttribute('open', '') |
| 6 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Escape llama onClose exactamente una vez | src/shared/components/Dialog.test.tsx > Escape llama onClose exactamente una vez | M2: cambio de condición event.key !== 'Escape' por 'Enter' |
| 7 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Al pasar open de true a false el foco vuelve a returnFocusRef | src/shared/components/Dialog.test.tsx > al pasar open de true a false el foco vuelve a returnFocusRef | M3: eliminación de llamada returnFocusRef?.current?.focus() |
| 8 | `frontend-appointment-form` | Apertura y foco inicial | Apertura y foco inicial | src/features/appointments/AppointmentFormDialog.test.tsx > apertura y foco inicial con prellenado contextual | M9: omisión de foco automático en patientSearchInputRef |
| 9 | `frontend-appointment-form` | Prellenado contextual desde la agenda | Prellenado con fecha y filtros activos | src/features/appointments/AppointmentFormDialog.test.tsx > apertura y foco inicial con prellenado contextual | M9: omisión de foco automático en patientSearchInputRef |
| 10 | `frontend-appointment-form` | Prellenado contextual desde la agenda | Sin filtros activos los selectores quedan sin selección | src/features/appointments/AppointmentFormDialog.test.tsx > apertura y foco inicial con prellenado contextual | M9: omisión de foco automático en patientSearchInputRef |
| 11 | `frontend-appointment-form` | Búsqueda y selección de paciente | Búsqueda con resultados muestra radio buttons | src/features/appointments/PatientSearchGroup.test.tsx > búsqueda con resultados muestra radio buttons con nombre y DNI | M6: omisión de DNI en etiqueta accesible de paciente |
| 12 | `frontend-appointment-form` | Búsqueda y selección de paciente | Búsqueda sin coincidencias muestra aviso | src/features/appointments/PatientSearchGroup.test.tsx > búsqueda sin resultados muestra aviso accesible y sin radio buttons | M7: alteración de texto 'No se encontraron pacientes' |
| 13 | `frontend-appointment-form` | Búsqueda y selección de paciente | Selección de radio button asigna patientId | src/features/appointments/PatientSearchGroup.test.tsx > selección por clic o teclado invoca onSelectPatient con el id correspondiente | M8: omisión de llamada a onSelectPatient en radio onChange |
| 14 | `frontend-appointment-form` | Sugerencia y edición de duración | Duración sugerida al elegir prestación | src/features/appointments/AppointmentFormDialog.test.tsx > sugerencia y edición de duración según prestación | M10: asignación de duración hardcodeada a 15 min |
| 15 | `frontend-appointment-form` | Sugerencia y edición de duración | Edición manual de duración | src/features/appointments/AppointmentFormDialog.test.tsx > sugerencia y edición de duración según prestación | M10: asignación de duración hardcodeada a 15 min |
| 16 | `frontend-appointment-form` | Composición de fecha, hora y timezone | startAt incluye offset horario exacto para la fecha elegida | src/features/appointments/AppointmentFormDialog.test.tsx > armado de startAt con offset exacto para la fecha elegida y timezone de la API | M11: hardcodeo de sufijo 'Z' en lugar de offset local calculado |
| 17 | `frontend-appointment-form` | Renderizado de violaciones de dominio 409 y 422 | Conflicto múltiple 409 muestra todas las violaciones con sus referencias | src/features/appointments/AppointmentFormDialog.test.tsx > respuesta 409 con violaciones múltiples muestra alert superior intacto, foco al alert y campos sin aria-invalid ; src/shared/api/client.violations.test.ts > captura conflictingAppointmentId, conflictingBlockId, conflictingInterval y referenceKind | M13: omisión de renderizado de badge con code de violación ; M4: omisión de mapeo de referenceKind en violation |
| 18 | `frontend-appointment-form` | Renderizado de violaciones de dominio 409 y 422 | Rechazo 422 muestra violaciones en el resumen | src/features/appointments/AppointmentFormDialog.test.tsx > rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos | M14: desactivación de manejo de kind unprocessable |
| 19 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Error 400 marca campo con aria-invalid | src/features/appointments/AppointmentFormDialog.test.tsx > mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline | M15: omisión de actualización de setFieldErrors ante error 400 |
| 20 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Error 403 muestra mensaje de rechazo | src/features/appointments/AppointmentFormDialog.test.tsx > respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión | M16: alteración de condición de kind forbidden |
| 21 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Foco se traslada al resumen de alerta ante fallo | src/features/appointments/AppointmentFormDialog.test.tsx > respuesta 409 con violaciones múltiples muestra alert superior intacto, foco al alert y campos sin aria-invalid | M13: omisión de renderizado de badge con code de violación |
| 22 | `frontend-appointment-form` | Éxito, refresco de agenda y retorno de foco | Alta exitosa 201 refresca agenda y anuncia resultado | src/features/appointments/AppointmentFormDialog.test.tsx > envío exitoso 201 cierra el modal, llama onSuccess, emite anuncio y devuelve foco | M12: omisión de invocación a onSuccess tras 201 |
| 23 | `frontend-appointment-form` | Éxito, refresco de agenda y retorno de foco | Cancelación retorna el foco | src/features/appointments/AppointmentFormDialog.test.tsx > pulsar Cancelar cierra el diálogo y devuelve el foco al elemento de apertura | M17: no-op en onClick de botón Cancelar |
| 24 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en escritorio a 1440 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-1440.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
| 25 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en tablet a 768 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-768.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
| 26 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en móvil a 390 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-390.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
<!-- trazabilidad:fin -->
