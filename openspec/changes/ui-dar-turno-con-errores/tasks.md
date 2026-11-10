# Tasks

> **Importante para la fase de Apply**: La implementación de C-29 requiere la primitiva `frontend/src/shared/components/Dialog.tsx` introducida en C-35 (`ui-portada-y-acceso`). Por lo tanto, el apply de C-29 debe ejecutarse una vez que C-35 esté archivado en la rama o cuando dicho archivo esté disponible.

## 1. Línea base y preparación

- [ ] 1.1 Confirmar que la rama activa es `main` y que `git status --short` no muestra cambios inesperados; `.codex/` es untracked preexistente. No tocar `.env`, `AGENTS.md`, `CLAUDE.md` ni `openspec/changes/ui-portada-y-acceso/`.
- [ ] 1.2 Ejecutar la suite completa de tests desde `frontend/` con `npm run test:run` y guardar la salida en `docs/evidencias/baseline-C-29.txt`. Anotar el total de tests pasando y verificar que no existan fallos preexistentes.
- [ ] 1.3 Confirmar la presencia de `frontend/src/shared/components/Dialog.tsx` (proveniente de C-35). No instalar dependencias ni librerías nuevas.
- [ ] 1.4 Releer `docs/evidencias/explore-C-29.md`, `openspec/changes/ui-dar-turno-con-errores/design.md` y los specs del change antes de escribir código.
- [ ] 1.5 Registrar el estado inicial de los tests que no se pueden modificar (`menuFor.test.ts`, `AppShell.test.tsx`, `AgendaToolbar.test.tsx`, `AgendaView.test.tsx` y `client.test.ts`).

## 2. Contratos y tipos de API (`shared/api`)

- [ ] 2.1 **RED** — Agregar en `frontend/src/shared/api/client.test.ts` (al final, sin modificar los tests existentes) un test que verifique que `Violation` captura los campos opcionales `conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval` y `referenceKind`. Guardar salida RED en `docs/evidencias/red-C-29/api-violations-opcionales.txt`.
- [ ] 2.2 **GREEN** — Extender la interfaz `Violation` en `frontend/src/shared/api/types.ts` y actualizar la función `asViolations` en `frontend/src/shared/api/client.ts`. Ejecutar el test y guardar salida GREEN en `docs/evidencias/green-C-29/api-violations-opcionales.txt`.

## 3. Búsqueda de pacientes (`PatientSearchGroup`)

- [ ] 3.1 **RED** — Crear `frontend/src/features/appointments/PatientSearchGroup.test.tsx` con un test de renderizado inicial que exija el input de búsqueda, el botón "Buscar paciente" habilitado y ausencia de radio buttons iniciales. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-inicial.txt`.
- [ ] 3.2 **GREEN** — Crear `frontend/src/features/appointments/PatientSearchGroup.tsx` y `PatientSearchGroup.module.css`. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-inicial.txt`.
- [ ] 3.3 **RED** — Agregar un test de búsqueda con resultados: al tipear "Pérez" y accionar el botón (o presionar Enter), se invoca `GET /api/patients?query=P%C3%A9rez` y se muestra un grupo de radio buttons (`name="patientId"`) con nombre completo y DNI formateado. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-resultados.txt`.
- [ ] 3.4 **GREEN** — Implementar la llamada a la API y el renderizado del listado de radio buttons. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-resultados.txt`.
- [ ] 3.5 **RED** — Agregar un test de búsqueda sin resultados que verifique la aparición del mensaje accesible "No se encontraron pacientes" y la ausencia de radio buttons. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-vacio.txt`.
- [ ] 3.6 **GREEN** — Implementar el mensaje de estado vacío accesible. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-vacio.txt`.
- [ ] 3.7 **RED** — Agregar un test de selección por teclado y clic que verifique que seleccionar un radio button invoca `onSelectPatient(patient.id)`. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-seleccion.txt`.
- [ ] 3.8 **GREEN** — Conectar el evento `onChange` del radio button con el callback de selección. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-seleccion.txt`.

## 4. Formulario modal de alta de turno (`AppointmentFormDialog`)

- [ ] 4.1 **RED** — Crear `frontend/src/features/appointments/AppointmentFormDialog.test.tsx` con un test de prellenado contextual: fecha efectiva de la agenda, profesional preseleccionado si viene en props, sillón preseleccionado si viene en props, y foco en el input de búsqueda de pacientes. Guardar salida RED en `docs/evidencias/red-C-29/form-prellenado.txt`.
- [ ] 4.2 **GREEN** — Crear `frontend/src/features/appointments/AppointmentFormDialog.tsx` y `AppointmentFormDialog.module.css` componiendo `Dialog` de C-35. Implementar el estado inicial y el prellenado. Guardar salida GREEN en `docs/evidencias/green-C-29/form-prellenado.txt`.
- [ ] 4.3 **RED** — Agregar un test de sugerencia de duración: al seleccionar la prestación "Extracción" (60 min) el campo se inicializa con 60; al modificar manualmente el valor a 45 min se conserva 45. Guardar salida RED en `docs/evidencias/red-C-29/form-duracion.txt`.
- [ ] 4.4 **GREEN** — Conectar la selección de prestación con la actualización de `durationMin` permitiendo edición libre. Guardar salida GREEN en `docs/evidencias/green-C-29/form-duracion.txt`.
- [ ] 4.5 **RED** — Agregar un test que verifique el armado de `startAt` mediante `Intl.DateTimeFormat` nativo con el offset local para la fecha y hora elegidas según el `timezone` de la API. Guardar salida RED en `docs/evidencias/red-C-29/form-startat-offset.txt`.
- [ ] 4.6 **GREEN** — Implementar la función `buildStartAtIso` y el armado del payload de envío. Guardar salida GREEN en `docs/evidencias/green-C-29/form-startat-offset.txt`.
- [ ] 4.7 **RED** — Agregar un test de envío exitoso (201): invoca `POST /api/appointments`, cierra el modal, llama al callback `onSuccess`, emite anuncio con `role="status"` y retorna el foco al disparador. Guardar salida RED en `docs/evidencias/red-C-29/form-exito-201.txt`.
- [ ] 4.8 **GREEN** — Implementar el flujo de submit exitoso y confirmación accesible. Guardar salida GREEN en `docs/evidencias/green-C-29/form-exito-201.txt`.
- [ ] 4.9 **RED** — Agregar un test de respuesta 409 con violaciones múltiples (`PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`): verifica que ambas se muestran en el alert superior (`role="alert"`), los textos del backend quedan intactos con las referencias de choque, el foco va al alert y los campos no tienen `aria-invalid`. Guardar salida RED en `docs/evidencias/red-C-29/form-violaciones-409.txt`.
- [ ] 4.10 **GREEN** — Implementar el contenedor de alertas de violaciones y la traslación de foco programático. Guardar salida GREEN en `docs/evidencias/green-C-29/form-violaciones-409.txt`.
- [ ] 4.11 **RED** — Agregar un test de rechazo 422 (`IN_THE_PAST` y `UNKNOWN_REFERENCE`): verifica que se muestran en el alert superior sin mapearse a campos. Guardar salida RED en `docs/evidencias/red-C-29/form-violaciones-422.txt`.
- [ ] 4.12 **GREEN** — Soportar respuestas 422 en el alert de resumen. Guardar salida GREEN en `docs/evidencias/green-C-29/form-violaciones-422.txt`.
- [ ] 4.13 **RED** — Agregar un test de error de entrada 400 (`{ errors: [{ field: "durationMin", message: "Dato inválido." }] }`): marca únicamente el campo correspondiente con `aria-invalid="true"` y muestra el mensaje inline. Guardar salida RED en `docs/evidencias/red-C-29/form-error-400.txt`.
- [ ] 4.14 **GREEN** — Implementar mapeo de errores 400 a los campos del formulario. Guardar salida GREEN en `docs/evidencias/green-C-29/form-error-400.txt`.
- [ ] 4.15 **RED** — Agregar un test de respuesta 403 (`FORBIDDEN_OPERATION`): muestra el mensaje de permiso denegado en el alert sin cerrar sesión. Guardar salida RED en `docs/evidencias/red-C-29/form-error-403.txt`.
- [ ] 4.16 **GREEN** — Manejar respuestas 403 en el formulario. Guardar salida GREEN en `docs/evidencias/green-C-29/form-error-403.txt`.
- [ ] 4.17 **RED** — Agregar un test de cancelación: pulsar "Cancelar" o presionar Escape cierra el diálogo y devuelve el foco al botón de apertura. Guardar salida RED en `docs/evidencias/red-C-29/form-cancelar.txt`.
- [ ] 4.18 **GREEN** — Conectar la cancelación y el cierre con `returnFocusRef`. Guardar salida GREEN en `docs/evidencias/green-C-29/form-cancelar.txt`.

## 5. Integración con la barra y página de agenda (`AgendaToolbar` y `AgendaPage`)

- [ ] 5.1 **RED** — Agregar tests en `frontend/src/features/agenda/AgendaToolbar.test.tsx` (al final, sin tocar los tests existentes) que comprueben que la prop opcional `onNewAppointment` renderiza el botón "Nuevo turno" para recepción y admin, y no lo renderiza para odontólogo. Guardar salida RED en `docs/evidencias/red-C-29/toolbar-nuevo-turno.txt`.
- [ ] 5.2 **GREEN** — Añadir la prop opcional `onNewAppointment?: () => void` en `AgendaToolbarProps` y renderizar el botón accesible con estilos existentes de toolbar. Guardar salida GREEN en `docs/evidencias/green-C-29/toolbar-nuevo-turno.txt`.
- [ ] 5.3 **RED** — Agregar test en `frontend/src/features/agenda/AgendaPage.test.tsx` (al final, sin tocar los tests existentes) que compruebe que al activar "Nuevo turno" se abre `AppointmentFormDialog` y al completar el alta se invoca `refresh` de `useAgenda`. Guardar salida RED en `docs/evidencias/red-C-29/page-integracion-dialog.txt`.
- [ ] 5.4 **GREEN** — Conectar `AppointmentFormDialog` en `AgendaPage.tsx` pasando `onSuccess={state.refresh}` y los filtros activos. Guardar salida GREEN en `docs/evidencias/green-C-29/page-integracion-dialog.txt`.

## 6. Mutaciones y verificación de calidad (Strict TDD)

- [ ] 6.1 Crear el script de mutaciones `docs/evidencias/mutaciones-C-29.py` con una mutación por cada test nuevo implementado (prellenado, radio buttons de pacientes, offset horario con Intl, sugerencia de duración, 409 con múltiples choques, 422, 400 con `aria-invalid`, 403, 201 con refresco y retorno de foco).
- [ ] 6.2 Ejecutar `python docs/evidencias/mutaciones-C-29.py` con detector de mutaciones inválidas (CRLF, restauración garantizada, verificación "SHA-256 sin cambios: si" y resumen con 0 inválidas). Guardar salida en `docs/evidencias/mutaciones-C-29.txt`.
- [ ] 6.3 Ejecutar diff de tests existentes para confirmar cero modificaciones en tests preexistentes: `git diff frontend/src/features/auth/menuFor.test.ts frontend/src/shared/components/AppShell.test.tsx frontend/src/features/agenda/AgendaView.test.tsx`. Guardar salida en `docs/evidencias/diff-tests-existentes-C-29.txt` (debe ser vacía).
- [ ] 6.4 Ejecutar `npx tsc --noEmit` y `npx eslint .` desde `frontend/` y registrar código de salida 0 en `docs/evidencias/tooling-C-29.txt`.
- [ ] 6.5 Ejecutar `npm run build` desde `frontend/` y confirmar generación de bundle sin errores. Guardar salida en `docs/evidencias/build-C-29.txt`.
- [ ] 6.6 Documentar tabla de trazabilidad escenario -> test -> mutación y la sección "Desvíos" en `docs/evidencias/verify-C-29.md`.

## 7. Verificación visual independiente

- [ ] 7.1 **Capturas 1440, 768 y 390 px — A CARGO DE CLAUDE**: Esta tarea NO la ejecuta el apply. Se reserva para la verificación independiente con navegador real / Playwright al auditar el cambio en escritorio, tablet y móvil.
