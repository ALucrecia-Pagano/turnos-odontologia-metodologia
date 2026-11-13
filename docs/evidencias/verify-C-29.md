# Verificación de C-29 — ui-dar-turno-con-errores

## Resultado

Todos los números provienen de las ejecuciones reales y archivos de evidencia enlazados.

- Tareas: implementadas según [tasks.md](../../openspec/changes/archive/2026-11-13-ui-dar-turno-con-errores/tasks.md).
- Vitest: suite completa pasando en verde (línea base de 164 tests intactos + 27 tests nuevos de C-29 = 191 tests en verde); `tsc --noEmit` y `eslint .` con código 0.
- Mutaciones: 27/27 hicieron fallar su test respectivo (una mutación por cada test nuevo de C-29); mutaciones inválidas: 0; 0 sobrevivientes; SHA-256 de producción intacto.
- Trazabilidad: 23 escenarios probados mediante Vitest (mapeo 1:1 a tests distintos) y 3 escenarios de adaptabilidad visual verificados visualmente (capturas independientes a cargo de Claude).
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

3. **Tests añadidos sobre comportamiento preexistente con RED demostrado por mutación**:
   - Durante la separación de escenarios (un escenario = un test = una mutación), los siguientes tests cubrieron lógica que ya estaba en el código de producción pero carecía de test unitario aislado. Su RED se evidenció mediante la mutación programática que hizo fallar la aserción correspondiente:
     - `sin filtros activos los selectores quedan sin selección`: mutación M11.
     - `edición manual de duración se conserva`: mutación M13.
     - `foco al resumen de alerta ante fallo`: mutación M20.
     - `Escape cierra sin enviar solicitudes y devuelve el foco`: mutación M22.

4. **Región accesible de estado en AgendaPage**:
   - Se montó una región siempre presente con `aria-live="polite"` y estilos `.srOnly` en `AgendaPage.tsx` para anunciar "Turno creado para el DD/MM/AAAA a las HH:MM.". Para convivir armónicamente con el `role="status"` existente de `LoadingState` y evitar colisiones en tests durante la fase de carga inicial (`state.phase === "loading"`), se define `role={state.phase === "loading" ? undefined : "status"}`.

5. **Logout.test.tsx fuera de alcance**:
   - En entornos Linux puede reportar desvío por prefijo `/agenda` duplicado en navegación sintética; en Windows ejecuta 1/1 passed. Permanece intacto según regla de no modificar tests de main.

6. **Corrección visual post-captura (centrado del modal, wrap del buscador en 390 px, font-family inherit)**:
   - CSS no verificable en jsdom; verificado con capturas C-29-*.png.

---

## Verificación manual contra la API real

Se realizaron pruebas interactivas con navegador real contra la API local activa, verificadas con las capturas en `docs/evidencias/capturas/C-29-*.png`:

1. **Alta exitosa (201)**:
   - Al completar el formulario y confirmar, el turno se crea correctamente.
   - El diálogo se cierra, la agenda se refresca y la región accesible permanente anuncia: `"Turno creado para el 13/11/2026 a las 10:00."`.
   - El foco retorna programáticamente al botón `"Nuevo turno"`.
   - Evidencia: `C-29-alta-exitosa-1440.png` y `C-29-form-completo-1440.png`.

2. **Conflicto de dominio (409)**:
   - Al intentar crear un turno que solapa agenda o sillón, la API responde 409 con violaciones múltiples (`PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`).
   - El alert superior de error muestra los códigos y los mensajes textuales del backend intactos con sus referencias correspondientes.
   - Foco trasladado automáticamente al contenedor de alerta.
   - Evidencia: `C-29-error-409-1440.png` y `C-29-error-409-390.png` (verificando wrap accesible en pantallas angostas).

3. **Cierre accesible con Escape**:
   - Al pulsar la tecla Escape, el modal se cierra sin enviar solicitudes y retorna el foco al disparador.

4. **Defectos visuales detectados en primera captura y corregidos en ca28ad5**:
   - Modal ubicado arriba a la izquierda por falta de centrado en `<dialog>`: corregido con flexbox (`align-items: center; justify-content: center;`) y padding en `Dialog.module.css`.
   - Botón de búsqueda desbordado en viewport de 390 px: corregido con `flex-wrap: wrap;` y ancho al 100% en pantallas móviles en `PatientSearchGroup.module.css`.
   - Tipografía Arial / genérica en campos y selectores: corregido con `font-family: inherit;` para heredar Manrope de los tokens.

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
| 9 | `apertura y foco inicial` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      patientSearchInputRef.current?.focus(); +      // patientSearchInputRef.current?.fo` | `Error: expect(element).toHaveFocus()` |
| 10 | `prellenado con fecha y filtros activos` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-  const [professionalId, setProfessionalId] = useState(initialProfessionalId ?? ""); +  c` | `AssertionError: expected '' to be '00000000-0000-0000-0000-000000000001' // Object.is equa` |
| 11 | `sin filtros activos los selectores quedan sin selección` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-  const [chairId, setChairId] = useState(initialChairId ?? ""); +  const [chairId, setCha` | `AssertionError: expected '00000000-0000-0000-0000-0000000000b1' to be '' // Object.is equa` |
| 12 | `duración sugerida al elegir prestación` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      setDurationMin(s.defaultDurationMin); +      setDurationMin(15);` | `AssertionError: expected '15' to be '60' // Object.is equality` |
| 13 | `edición manual de duración se conserva` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-                  setDurationMin(val === "" ? "" : Number(val)); +                  setDu` | `AssertionError: expected '60' to be '45' // Object.is equality` |
| 14 | `armado de startAt con offset exacto para la fecha elegida y timezone de la API` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-  return '${dateStr}T${timeStr}:00${offset}'; +  return '${dateStr}T${timeStr}:00Z';` | `AssertionError: expected '2026-11-16T10:00:00Z' to be '2026-11-16T10:00:00-03:00' // Objec` |
| 15 | `envío exitoso 201 cierra el modal, llama onSuccess con los datos del turno y devuelve foco` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-      onSuccess?.({ date, time }); +      // onSuccess?.({ date, time });` | `AssertionError: expected false to be true // Object.is equality` |
| 16 | `respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-                  <span className={styles.codeBadge}>{v.code}</span> +                  {` | `AssertionError: expected null not to be null` |
| 17 | `rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        result.error.kind === "unprocessable" \|\| +        // result.error.kind === "unpro` | `AssertionError: expected null not to be null` |
| 18 | `mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        setFieldErrors(mappedErrors); +        // setFieldErrors(mappedErrors);` | `Error: expect(element).toHaveAttribute("aria-invalid", "true") // element.getAttribute("ar` |
| 19 | `respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        result.error.kind === "forbidden" +        result.error.kind === ("unknown" as st` | `AssertionError: expected null not to be null` |
| 20 | `foco al resumen de alerta ante fallo` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-        setTimeout(() => alertRef.current?.focus(), 0); +        // setTimeout(() => aler` | `Error: expect(element).toHaveFocus()` |
| 21 | `pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-              onClick={onClose} +              onClick={() => undefined}` | `AssertionError: expected true to be false // Object.is equality` |
| 22 | `Escape cierra sin enviar solicitudes y devuelve el foco` | `frontend/src/features/appointments/AppointmentFormDialog.tsx` | `-    onClose(); +    // onClose();` | `AssertionError: expected true to be false // Object.is equality` |
| 23 | `visible para recepción y dispara onNewAppointment al clic` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-    (userRole === "recepcion" \|\| userRole === "administrador") && +    (userRole === "adm` | `AssertionError: expected null not to be null` |
| 24 | `visible para administrador` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-    (userRole === "recepcion" \|\| userRole === "administrador") && +    (userRole === "rec` | `AssertionError: expected null not to be null` |
| 25 | `no visible para odontólogo` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-    (userRole === "recepcion" \|\| userRole === "administrador") && +    (userRole !== null` | `AssertionError: expected <button type="button" …(1)></button> to be null` |
| 26 | `al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    void state.refresh(); +    // void state.refresh();` | `AssertionError: expected 1 to be greater than 1` |
| 27 | `tras alta exitosa (201) anuncia el turno creado en una región de estado accesible` | `frontend/src/features/agenda/AgendaPage.tsx` | `-      setStatusMessage('Turno creado para el ${day}/${month}/${year} a las ${info.time}.'` | `Error: expect(element).toHaveTextContent()` |
<!-- mutaciones:fin -->

---

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Capacidad | Requisito | Escenario | Test Vitest / Verificación | Mutación asociada |
|---|---|---|---|---|---|
| 1 | `frontend-agenda` | Acción Nuevo turno en la agenda | Visible para recepción | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > visible para recepción y dispara onNewAppointment al clic | M23: restricción de botón Nuevo turno solo a rol administrador |
| 2 | `frontend-agenda` | Acción Nuevo turno en la agenda | Visible para administrador | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > visible para administrador | M24: restricción de botón Nuevo turno solo a rol recepcion |
| 3 | `frontend-agenda` | Acción Nuevo turno en la agenda | No visible para odontólogo | src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx > no visible para odontólogo | M25: mostrar botón Nuevo turno para todos los roles |
| 4 | `frontend-agenda` | Acción Nuevo turno en la agenda | Refresco tras alta | src/features/agenda/AgendaPage.nuevoTurno.test.tsx > al pulsar Nuevo turno abre el diálogo y tras alta exitosa (201) cierra y refresca la agenda | M26: omisión de refresh en onSuccess de AppointmentFormDialog |
| 5 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby | src/shared/components/Dialog.test.tsx > abre con atributo open en jsdom y expone el nombre accesible por aria-labelledby | M1: eliminación de dialog.setAttribute('open', '') |
| 6 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Escape llama onClose exactamente una vez | src/shared/components/Dialog.test.tsx > Escape llama onClose exactamente una vez | M2: cambio de condición event.key !== 'Escape' por 'Enter' |
| 7 | `frontend-appointment-form` | Primitiva de diálogo modal accesible | Al pasar open de true a false el foco vuelve a returnFocusRef | src/shared/components/Dialog.test.tsx > al pasar open de true a false el foco vuelve a returnFocusRef | M3: eliminación de llamada returnFocusRef?.current?.focus() |
| 8 | `frontend-appointment-form` | Apertura y foco inicial | Apertura y foco inicial | src/features/appointments/AppointmentFormDialog.test.tsx > apertura y foco inicial | M9: omisión de foco automático en patientSearchInputRef |
| 9 | `frontend-appointment-form` | Prellenado contextual desde la agenda | Prellenado con fecha y filtros activos | src/features/appointments/AppointmentFormDialog.test.tsx > prellenado con fecha y filtros activos | M10: inicialización de professionalId sin valor por defecto |
| 10 | `frontend-appointment-form` | Prellenado contextual desde la agenda | Sin filtros activos los selectores quedan sin selección | src/features/appointments/AppointmentFormDialog.test.tsx > sin filtros activos los selectores quedan sin selección | M11: inicialización de chairId con valor por defecto cuando initialChairId es nulo |
| 11 | `frontend-appointment-form` | Búsqueda y selección de paciente | Búsqueda con resultados muestra radio buttons | src/features/appointments/PatientSearchGroup.test.tsx > búsqueda con resultados muestra radio buttons con nombre y DNI | M6: omisión de DNI en etiqueta accesible de paciente |
| 12 | `frontend-appointment-form` | Búsqueda y selección de paciente | Búsqueda sin coincidencias muestra aviso | src/features/appointments/PatientSearchGroup.test.tsx > búsqueda sin resultados muestra aviso accesible y sin radio buttons | M7: alteración de texto 'No se encontraron pacientes' |
| 13 | `frontend-appointment-form` | Búsqueda y selección de paciente | Selección de radio button asigna patientId | src/features/appointments/PatientSearchGroup.test.tsx > selección por clic o teclado invoca onSelectPatient con el id correspondiente | M8: omisión de llamada a onSelectPatient en radio onChange |
| 14 | `frontend-appointment-form` | Sugerencia y edición de duración | Duración sugerida al elegir prestación | src/features/appointments/AppointmentFormDialog.test.tsx > duración sugerida al elegir prestación | M12: asignación de duración fija 15 min en lugar de sugerida |
| 15 | `frontend-appointment-form` | Sugerencia y edición de duración | Edición manual de duración | src/features/appointments/AppointmentFormDialog.test.tsx > edición manual de duración se conserva | M13: forzar duración fija 60 min en onChange de duración |
| 16 | `frontend-appointment-form` | Composición de fecha, hora y timezone | startAt incluye offset horario exacto para la fecha elegida | src/features/appointments/AppointmentFormDialog.test.tsx > armado de startAt con offset exacto para la fecha elegida y timezone de la API | M14: hardcodeo de sufijo 'Z' en lugar de offset local calculado |
| 17 | `frontend-appointment-form` | Renderizado de violaciones de dominio 409 y 422 | Conflicto múltiple 409 muestra todas las violaciones con sus referencias | src/features/appointments/AppointmentFormDialog.test.tsx > respuesta 409 con violaciones múltiples muestra alert superior intacto con badges y referencias | M16: omisión de renderizado de badge con code de violación |
| 18 | `frontend-appointment-form` | Renderizado de violaciones de dominio 409 y 422 | Rechazo 422 muestra violaciones en el resumen | src/features/appointments/AppointmentFormDialog.test.tsx > rechazo 422 con IN_THE_PAST y UNKNOWN_REFERENCE muestra violaciones en alert superior sin mapeo a campos | M17: desactivación de manejo de kind unprocessable |
| 19 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Error 400 marca campo con aria-invalid | src/features/appointments/AppointmentFormDialog.test.tsx > mapea errores 400 a los campos del formulario con aria-invalid y mensaje inline | M18: omisión de actualización de setFieldErrors ante error 400 |
| 20 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Error 403 muestra mensaje de rechazo | src/features/appointments/AppointmentFormDialog.test.tsx > respuesta 403 FORBIDDEN_OPERATION muestra mensaje de permiso denegado en alert sin cerrar sesión | M19: alteración de condición de kind forbidden |
| 21 | `frontend-appointment-form` | Errores de validación 400 y permisos 403 | Foco se traslada al resumen de alerta ante fallo | src/features/appointments/AppointmentFormDialog.test.tsx > foco al resumen de alerta ante fallo | M20: omisión de foco al alert ante violaciones |
| 22 | `frontend-appointment-form` | Éxito, refresco de agenda y retorno de foco | Alta exitosa 201 refresca agenda y anuncia resultado | src/features/agenda/AgendaPage.nuevoTurno.test.tsx > tras alta exitosa (201) anuncia el turno creado en una región de estado accesible | M27: alteración del mensaje de anuncio en AgendaPage |
| 23 | `frontend-appointment-form` | Éxito, refresco de agenda y retorno de foco | Cancelación retorna el foco | src/features/appointments/AppointmentFormDialog.test.tsx > pulsar Cancelar cierra el diálogo sin enviar solicitudes y devuelve el foco al elemento de apertura | M21: no-op en onClick de botón Cancelar |
| 24 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en escritorio a 1440 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-form-1440.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
| 25 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en tablet a 768 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-form-768.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
| 26 | `frontend-appointment-form` | Adaptabilidad visual del formulario | Visualización en móvil a 390 px | Captura a cargo de Claude (`docs/evidencias/capturas/C-29-form-390.png`, `docs/evidencias/capturas/C-29-error-409-390.png`) | Sin mutación (verificación visual independiente a cargo de Claude) |
<!-- trazabilidad:fin -->
