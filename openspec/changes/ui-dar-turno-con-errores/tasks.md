# Tasks

## Reglas obligatorias para la implementación

- **Regla C1**: Prohibido el uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers, MSW ni `waitFor` largos. El cliente API se inyecta mediante `createApiClient({ fetchFn })`, el tiempo mediante `createFixedClock` y la navegación con `createMemoryRouter` + `RouterProvider`. No borrar ni asignar globals en `window` ni en el entorno. El token de sesión se confina exclusivamente en `tokenStore.ts`. La zona horaria se toma dinámicamente de la respuesta de la API.
- **Sin excepciones de tipado o linting**: Prohibido `type: ignore`, `@ts-ignore`, `eslint-disable`, mocks, patch o monkeypatch.
- **Mutaciones estrictas (1 por test nuevo)**: Una mutación por cada test nuevo agregado (incluyendo los de `Dialog`), mediante script con detector de inválidas (respeto estricto de CRLF, aborta si un mutante no cambia nada, verificación "SHA-256 sin cambios: si", y RESUMEN con "mutaciones inválidas: 0").
- **Evidencias y tooling**: Ejecución de `tsc`, `eslint` y `build` con comando explícito y código de salida; evidencias guardadas en UTF-8 usando Git Bash (nunca el operador `>` de PowerShell).
- **Menú principal y tests existentes**: El ítem "Turnos" del menú principal permanece con `disabled: true` y `badge: "Próximamente"`. `Logout.test.tsx` queda fuera de alcance. Todos los archivos de test preexistentes (`client.test.ts`, `AgendaToolbar.test.tsx`, `AgendaPage.test.tsx`, `menuFor.test.ts`, `AppShell.test.tsx`, etc.) permanecen 100% intactos; los tests nuevos se implementan en archivos `.test.ts` y `.test.tsx` nuevos.
- **Fidelidad de mensajes**: Todos los mensajes y textos de violaciones se copian textualmente del backend real (`backend/app/...`), nunca de memoria.

---

## 1. Línea base y preparación

- [ ] 1.1 Crear y usar la rama `c29-apply` desde `main` actualizado; `git status --short` solo con `.codex/` sin trackear. No tocar `.env`, `AGENTS.md`, `CLAUDE.md` ni `openspec/changes/ui-portada-y-acceso/`.
- [ ] 1.2 Ejecutar la suite completa de tests desde `frontend/` con `npm run test:run` y guardar la salida en `docs/evidencias/baseline-C-29.txt`. Anotar el total de tests pasando; en Windows todos deben pasar y no deben existir fallos preexistentes vinculados.
- [ ] 1.3 Releer `docs/evidencias/explore-C-29.md`, `openspec/changes/ui-dar-turno-con-errores/design.md` y los specs del change antes de escribir código. No instalar dependencias ni librerías nuevas.
- [ ] 1.4 Registrar el estado inicial de los tests que no se pueden modificar (`menuFor.test.ts`, `AppShell.test.tsx`, `AgendaToolbar.test.tsx`, `AgendaPage.test.tsx`, `AgendaView.test.tsx` y `client.test.ts`).

## 2. Primitiva Dialog (`shared/components/Dialog`)

- [ ] 2.1 **RED** — Crear un componente `frontend/src/shared/components/Dialog.tsx` mínimo que compile y crear `frontend/src/shared/components/Dialog.test.tsx` con el test: abre con atributo `open` en jsdom y expone el nombre accesible por `aria-labelledby` sin atributo `role="dialog"` redundante (fallo por aserción). Guardar salida RED en `docs/evidencias/red-C-29/dialog-render-jsdom.txt`.
- [ ] 2.2 **GREEN** — Implementar `Dialog.tsx` y `Dialog.module.css` con `<dialog>` nativo, `aria-labelledby` obligatorio, `aria-modal="true"` solo cuando no hay `showModal` (fallback), y apertura con `open` attribute si `showModal` no es función. Guardar salida GREEN en `docs/evidencias/green-C-29/dialog-render-jsdom.txt`.
- [ ] 2.3 **RED** — Agregar test en `Dialog.test.tsx`: al presionar Escape, `onClose` se invoca exactamente una vez (fallo por aserción). Guardar salida RED en `docs/evidencias/red-C-29/dialog-escape-once.txt`.
- [ ] 2.4 **GREEN** — Implementar listeners de `cancel` y tecla `Escape` en `Dialog.tsx` asegurando que `onClose` se invoque una sola vez por cierre. Guardar salida GREEN en `docs/evidencias/green-C-29/dialog-escape-once.txt`.
- [ ] 2.5 **RED** — Agregar test en `Dialog.test.tsx`: al pasar `open` de `true` a `false`, el foco retorna exactamente una vez al elemento referenciado por `returnFocusRef` (fallo por aserción). Guardar salida RED en `docs/evidencias/red-C-29/dialog-return-focus.txt`.
- [ ] 2.6 **GREEN** — Implementar retorno de foco único a `returnFocusRef` en el efecto de cierre de `Dialog.tsx`. Guardar salida GREEN en `docs/evidencias/green-C-29/dialog-return-focus.txt`.

## 3. Contratos y tipos de API (`shared/api`)

- [ ] 3.1 **RED** — Crear `frontend/src/shared/api/client.violations.test.ts` con un test aislado (sin modificar `client.test.ts`) que verifique que `Violation` captura los campos opcionales `conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval` y `referenceKind`. Guardar salida RED en `docs/evidencias/red-C-29/api-violations-opcionales.txt`.
- [ ] 3.2 **GREEN** — Extender la interfaz `Violation` en `frontend/src/shared/api/types.ts` y actualizar la función `asViolations` en `frontend/src/shared/api/client.ts`. Ejecutar el test y guardar salida GREEN en `docs/evidencias/green-C-29/api-violations-opcionales.txt`.

## 4. Búsqueda de pacientes (`PatientSearchGroup`)

- [ ] 4.1 **RED** — Crear `frontend/src/features/appointments/PatientSearchGroup.test.tsx` con un test de renderizado inicial que exija el input de búsqueda, el botón "Buscar paciente" habilitado y ausencia de radio buttons iniciales. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-inicial.txt`.
- [ ] 4.2 **GREEN** — Crear `frontend/src/features/appointments/PatientSearchGroup.tsx` y `PatientSearchGroup.module.css`. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-inicial.txt`.
- [ ] 4.3 **RED** — Agregar test de búsqueda con resultados en `PatientSearchGroup.test.tsx`: al tipear "Pérez" y accionar el botón (o presionar Enter), se invoca `GET /api/patients?query=P%C3%A9rez` y se muestra un grupo de radio buttons (`name="patientId"`) con nombre completo y DNI formateado. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-resultados.txt`.
- [ ] 4.4 **GREEN** — Implementar la llamada a la API y el renderizado del listado de radio buttons. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-resultados.txt`.
- [ ] 4.5 **RED** — Agregar test de búsqueda sin resultados en `PatientSearchGroup.test.tsx` que verifique la aparición del mensaje accesible "No se encontraron pacientes" y la ausencia de radio buttons. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-vacio.txt`.
- [ ] 4.6 **GREEN** — Implementar el mensaje de estado vacío accesible. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-vacio.txt`.
- [ ] 4.7 **RED** — Agregar test de selección por teclado y clic en `PatientSearchGroup.test.tsx` que verifique que seleccionar un radio button invoca `onSelectPatient(patient.id)`. Guardar salida RED en `docs/evidencias/red-C-29/pacientes-seleccion.txt`.
- [ ] 4.8 **GREEN** — Conectar el evento `onChange` del radio button con el callback de selección. Guardar salida GREEN en `docs/evidencias/green-C-29/pacientes-seleccion.txt`.

## 5. Formulario modal de alta de turno (`AppointmentFormDialog`)

- [ ] 5.1 **RED** — Crear `frontend/src/features/appointments/AppointmentFormDialog.test.tsx` con test de apertura y foco inicial: foco en el input de búsqueda de pacientes, y prellenado contextual con fecha efectiva de la agenda, profesional preseleccionado si viene en props, sillón preseleccionado si viene en props. Guardar salida RED en `docs/evidencias/red-C-29/form-prellenado.txt`.
- [ ] 5.2 **GREEN** — Crear `frontend/src/features/appointments/AppointmentFormDialog.tsx` y `AppointmentFormDialog.module.css` componiendo `Dialog`. Implementar el estado inicial y el prellenado. Guardar salida GREEN en `docs/evidencias/green-C-29/form-prellenado.txt`.
- [ ] 5.3 **RED** — Agregar test de sugerencia de duración: al seleccionar la prestación "Extracción" (60 min) el campo se inicializa con 60; al modificar manualmente el valor a 45 min se conserva 45. Guardar salida RED en `docs/evidencias/red-C-29/form-duracion.txt`.
- [ ] 5.4 **GREEN** — Conectar la selección de prestación con la actualización de `durationMin` permitiendo edición libre. Guardar salida GREEN en `docs/evidencias/green-C-29/form-duracion.txt`.
- [ ] 5.5 **RED** — Agregar test que verifique el armado de `startAt` mediante `Intl.DateTimeFormat` nativo con el offset local para la fecha y hora elegidas según el `timezone` de la API. Guardar salida RED en `docs/evidencias/red-C-29/form-startat-offset.txt`.
- [ ] 5.6 **GREEN** — Implementar la función `buildStartAtIso` y el armado del payload de envío. Guardar salida GREEN en `docs/evidencias/green-C-29/form-startat-offset.txt`.
- [ ] 5.7 **RED** — Agregar test de envío exitoso (201): invoca `POST /api/appointments`, cierra el modal, llama al callback `onSuccess`, emite anuncio con `role="status"` y retorna el foco al disparador. Guardar salida RED en `docs/evidencias/red-C-29/form-exito-201.txt`.
- [ ] 5.8 **GREEN** — Implementar el flujo de submit exitoso y confirmación accesible. Guardar salida GREEN en `docs/evidencias/green-C-29/form-exito-201.txt`.
- [ ] 5.9 **RED** — Agregar test de respuesta 409 con violaciones múltiples (`PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP`): verifica que ambas se muestran en el alert superior (`role="alert"`), los textos del backend quedan intactos con las referencias de choque copiados textualmente del backend, el foco va al alert y los campos no tienen `aria-invalid`. Guardar salida RED en `docs/evidencias/red-C-29/form-violaciones-409.txt`.
- [ ] 5.10 **GREEN** — Implementar el contenedor de alertas de violaciones y la traslación de foco programático. Guardar salida GREEN en `docs/evidencias/green-C-29/form-violaciones-409.txt`.
- [ ] 5.11 **RED** — Agregar test de rechazo 422 (`IN_THE_PAST` y `UNKNOWN_REFERENCE`): verifica que se muestran en el alert superior con mensajes literales copiados del backend sin mapearse a campos. Guardar salida RED en `docs/evidencias/red-C-29/form-violaciones-422.txt`.
- [ ] 5.12 **GREEN** — Soportar respuestas 422 en el alert de resumen. Guardar salida GREEN en `docs/evidencias/green-C-29/form-violaciones-422.txt`.
- [ ] 5.13 **RED** — Agregar test de error de entrada 400 (`{ errors: [{ field: "durationMin", message: "La fecha y hora debe incluir zona horaria." }] }`): marca únicamente el campo correspondiente con `aria-invalid="true"` y muestra el mensaje inline. Guardar salida RED en `docs/evidencias/red-C-29/form-error-400.txt`.
- [ ] 5.14 **GREEN** — Implementar mapeo de errores 400 a los campos del formulario. Guardar salida GREEN en `docs/evidencias/green-C-29/form-error-400.txt`.
- [ ] 5.15 **RED** — Agregar test de respuesta 403 (`FORBIDDEN_OPERATION` con mensaje `"No tiene permiso para dar turnos."` copiado de `PERMISSION_MESSAGES`): muestra el mensaje de permiso denegado en el alert sin cerrar sesión. Guardar salida RED en `docs/evidencias/red-C-29/form-error-403.txt`.
- [ ] 5.16 **GREEN** — Manejar respuestas 403 en el formulario. Guardar salida GREEN en `docs/evidencias/green-C-29/form-error-403.txt`.
- [ ] 5.17 **RED** — Agregar test de cancelación: pulsar "Cancelar" o presionar Escape cierra el diálogo y devuelve el foco al botón de apertura. Guardar salida RED en `docs/evidencias/red-C-29/form-cancelar.txt`.
- [ ] 5.18 **GREEN** — Conectar la cancelación y el cierre con `returnFocusRef`. Guardar salida GREEN en `docs/evidencias/green-C-29/form-cancelar.txt`.

## 6. Integración con la barra y página de agenda (`AgendaToolbar` y `AgendaPage`)

- [ ] 6.1 **RED** — Crear `frontend/src/features/agenda/AgendaToolbar.nuevoTurno.test.tsx` (archivo separado, sin modificar `AgendaToolbar.test.tsx`) con tests que comprueben que la prop opcional `onNewAppointment` renderiza el botón "Nuevo turno" para recepción y admin, y no lo renderiza para odontólogo. Guardar salida RED en `docs/evidencias/red-C-29/toolbar-nuevo-turno.txt`.
- [ ] 6.2 **GREEN** — Añadir la prop opcional `onNewAppointment?: () => void` en `AgendaToolbarProps` y renderizar el botón accesible con estilos existentes de toolbar. Guardar salida GREEN en `docs/evidencias/green-C-29/toolbar-nuevo-turno.txt`.
- [ ] 6.3 **RED** — Crear `frontend/src/features/agenda/AgendaPage.nuevoTurno.test.tsx` (archivo separado, sin modificar `AgendaPage.test.tsx`) que compruebe que al activar "Nuevo turno" se abre `AppointmentFormDialog` y al completar el alta se invoca `refresh` de `useAgenda`. Guardar salida RED en `docs/evidencias/red-C-29/page-integracion-dialog.txt`.
- [ ] 6.4 **GREEN** — Conectar `AppointmentFormDialog` en `AgendaPage.tsx` pasando `onSuccess={state.refresh}` y los filtros activos. Guardar salida GREEN en `docs/evidencias/green-C-29/page-integracion-dialog.txt`.

## 7. Mutaciones y verificación de calidad (Strict TDD)

- [ ] 7.1 Crear el script de mutaciones `docs/evidencias/mutaciones-C-29.py` con una mutación por cada test nuevo implementado (19 mutaciones en total: 3 de Dialog, 1 de API violations opcionales, 4 de pacientes, 9 de formulario, 1 de toolbar nuevo turno, 1 de page integración dialog).
- [ ] 7.2 Ejecutar `python docs/evidencias/mutaciones-C-29.py` con detector de mutaciones inválidas (CRLF respetado, restauración garantizada, verificación "SHA-256 sin cambios: si", aborta si un mutante no cambia nada, y resumen con "mutaciones inválidas: 0"). Guardar salida en `docs/evidencias/mutaciones-C-29.txt`.
- [ ] 7.3 Ejecutar verificación de diff de tests existentes: `git diff main --stat -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'` con `--diff-filter=M` debe salir estrictamente VACÍO (solo se permiten archivos de test agregados, filtro A). Guardar salida en `docs/evidencias/diff-tests-existentes-C-29.txt`.
- [ ] 7.4 Ejecutar `npx tsc --noEmit` y `npx eslint .` desde `frontend/` y registrar comando y código de salida 0 en `docs/evidencias/tooling-C-29.txt` (UTF-8, Git Bash).
- [ ] 7.5 Ejecutar `npm run build` desde `frontend/` y confirmar generación de bundle con código de salida 0. Guardar salida en `docs/evidencias/build-C-29.txt` (UTF-8, Git Bash).
- [ ] 7.6 Documentar tabla de trazabilidad escenario -> test -> mutación y la sección "Desvíos" en `docs/evidencias/verify-C-29.md`. Incluir explícitamente en la tabla que los 3 escenarios de "Adaptabilidad visual" (1440 px, 768 px y 390 px) se verifican mediante capturas de pantalla a cargo de Claude (`docs/evidencias/capturas/C-29-*.png`) y no mediante tests de Vitest ni mutaciones.

## 8. Verificación visual independiente

- [ ] 8.1 **Capturas 1440, 768 y 390 px — A CARGO DE CLAUDE**: Esta tarea NO la ejecuta el apply. Se reserva para la verificación independiente con navegador real / Playwright al auditar el cambio en escritorio (`docs/evidencias/capturas/C-29-1440.png`), tablet (`docs/evidencias/capturas/C-29-768.png`) y móvil (`docs/evidencias/capturas/C-29-390.png`). Los 3 escenarios de adaptabilidad visual no tienen test de Vitest ni mutaciones en el apply.
