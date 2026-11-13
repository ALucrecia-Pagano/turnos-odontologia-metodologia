# Tasks

## Reglas obligatorias y marco de trabajo

- **Regla C1 estricta**: Prohibido el uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers`, MSW o esperas largas (`waitFor` mayor a 1000 ms). Las solicitudes HTTP se prueban inyectando un cliente real mediante `createApiClient({ fetchFn })` que retorne instancias reales de `Response`. El tiempo se fija exclusivamente con `createFixedClock`. El enrutamiento se evalúa con `createMemoryRouter + RouterProvider`. Queda estrictamente prohibido asignar o borrar globals en `window` o `globalThis`.
- **Prohibición de supresiones de tipos o linter**: Queda prohibido el uso de `@ts-ignore`, `@ts-expect-error`, `type: ignore` o comentarios `eslint-disable`.
- **Preservación estricta de tests existentes**: Todos los archivos de test preexistentes de `main` deben permanecer intactos. `git diff main --stat -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'` con `--diff-filter=M` debe resultar estrictamente vacío. Los tests nuevos se ubican en archivos dedicados.
- **Strict TDD y Trazabilidad 1:1**: Un escenario = un test = una mutación desde el inicio. Cada test nuevo debe contar con su evidencia RED antes de implementar y su evidencia GREEN posterior en las carpetas `docs/evidencias/red-C-30/` y `docs/evidencias/green-C-30/`.
- **Script de mutaciones con detector de inválidas**: Normalización CRLF/LF, verificación de que el mutante efectivamente altere el código ("SHA-256 sin cambios: si"), 0 mutaciones inválidas y 0 sobrevivientes.
- **Herramientas de calidad**: `tsc --noEmit`, `eslint .` y `npm run build` deben finalizar con código de salida 0.
- **Evidencias en UTF-8**: Todas las evidencias se capturan con codificación UTF-8 en Git Bash.
- **Navegación principal**: El ítem "Turnos" en `menuFor.ts` permanece deshabilitado con "Próximamente".
- **Rama de trabajo**: `c30-apply`.

---

## 1. Línea base y preparación

- [x] 1.1 Capturar la línea base de la suite de pruebas (191 tests pasando) en `docs/evidencias/baseline-C-30.txt` y verificar tooling inicial (`tsc`, `eslint`).
- [x] 1.2 Definir los tipos de datos y clientes tipados en `frontend/src/features/appointments/appointmentApi.ts` para los endpoints de ciclo de vida (`status`, `cancel`, `reschedule`, `history`).

## 2. Turnos accionables en la agenda

- [x] 2.1 Implementar cada turno en `AgendaGrid` como `<button type="button">` accesible con `aria-label` completo, foco visible mediante `--color-focus` y sin alterar la escala porcentual. Evidencias: `docs/evidencias/red-C-30/01-grid-button.txt` y `docs/evidencias/green-C-30/01-grid-button.txt`.
- [x] 2.2 Conectar el evento de selección en `AgendaGrid` para invocar el callback `onSelectAppointment`. Evidencias: `docs/evidencias/red-C-30/02-grid-select.txt` y `docs/evidencias/green-C-30/02-grid-select.txt`.
- [x] 2.3 Proveer la acción accesible "Ver turno" por fila en `AgendaTable` cuando se suministra `onSelectAppointment`. Evidencias: `docs/evidencias/red-C-30/03-table-button.txt` y `docs/evidencias/green-C-30/03-table-button.txt`.
- [x] 2.4 Asegurar la compatibilidad regresiva en `AgendaTable` para renderizar exactamente 6 columnas y celdas cuando `onSelectAppointment` no está definido. Evidencias: `docs/evidencias/red-C-30/04-table-compat.txt` y `docs/evidencias/green-C-30/04-table-compat.txt`.

## 3. Diálogo modal de detalle e historial de cambios

- [x] 3.1 Construir `AppointmentDetailDialog.tsx` sobre `Dialog.tsx`, mostrando datos completos en hora local con `StatusBadge` y retorno de foco al disparador al cerrar con botón o Escape. Evidencias: `docs/evidencias/red-C-30/05-detail-render.txt` y `docs/evidencias/green-C-30/05-detail-render.txt`.
- [x] 3.2 Construir `AppointmentHistoryList.tsx` consultando `GET /api/appointments/{id}/history` y renderizando transiciones cronológicas con autor, estados y hora local. Evidencias: `docs/evidencias/red-C-30/06-history-list.txt` y `docs/evidencias/green-C-30/06-history-list.txt`.
- [x] 3.3 Renderizar en el historial el desglose de reprogramación mostrando intervalo anterior y nuevo en hora local cuando `reschedule` está presente. Evidencias: `docs/evidencias/red-C-30/07-history-reschedule.txt` y `docs/evidencias/green-C-30/07-history-reschedule.txt`.
- [x] 3.4 Manejar estados de error de carga en el historial mostrando un aviso accesible sin romper la vista del detalle. Evidencias: `docs/evidencias/red-C-30/08-history-error.txt` y `docs/evidencias/green-C-30/08-history-error.txt`.

## 4. Cambios de estado ordinarios

- [x] 4.1 Renderizar botones contextuales de acción según estado y rol: en `reservado` (Confirmar turno, Marcar atendido, Marcar ausente, Reprogramar, Cancelar turno); en `confirmado` (Marcar atendido, Marcar ausente, Reprogramar, Cancelar turno); en terminales mostrar texto "Este turno ya no admite cambios.". Evidencias: `docs/evidencias/red-C-30/09-status-buttons.txt` y `docs/evidencias/green-C-30/09-status-buttons.txt`.
- [x] 4.2 Conectar la acción "Confirmar turno" para enviar `POST /api/appointments/{id}/status` con `{ toStatus: "confirmado" }` y cerrar modal ante 200 OK. Evidencias: `docs/evidencias/red-C-30/10-confirm-ok.txt` y `docs/evidencias/green-C-30/10-confirm-ok.txt`.
- [x] 4.3 Conectar la acción "Marcar atendido" para enviar `{ toStatus: "atendido" }` y cerrar modal ante 200 OK. Evidencias: `docs/evidencias/red-C-30/11-attend-ok.txt` y `docs/evidencias/green-C-30/11-attend-ok.txt`.
- [x] 4.4 Conectar la acción "Marcar ausente" para enviar `{ toStatus: "ausente" }` y cerrar modal ante 200 OK. Evidencias: `docs/evidencias/red-C-30/12-noshow-ok.txt` y `docs/evidencias/green-C-30/12-noshow-ok.txt`.
- [x] 4.5 Manejar el rechazo 422 `STATUS_CHANGE_TOO_EARLY` exponiendo código y mensaje del dominio en alert accesible `role="alert"` con foco automático. Evidencias: `docs/evidencias/red-C-30/13-status-too-early.txt` y `docs/evidencias/green-C-30/13-status-too-early.txt`.
- [x] 4.6 Manejar el rechazo 422 `INVALID_TRANSITION` exponiendo el mensaje explicativo en el alert superior con foco automático. Evidencias: `docs/evidencias/red-C-30/14-status-invalid-transition.txt` y `docs/evidencias/green-C-30/14-status-invalid-transition.txt`.

## 5. Cancelación con confirmación in-dialog

- [x] 5.1 Desplegar subvista de confirmación dentro del diálogo al pulsar "Cancelar turno" con advertencia, botón destructivo y "Volver al detalle". Evidencias: `docs/evidencias/red-C-30/15-cancel-prompt.txt` y `docs/evidencias/green-C-30/15-cancel-prompt.txt`.
- [x] 5.2 Restaurar la vista de detalle al presionar "Volver al detalle" o Escape sin enviar solicitudes. Evidencias: `docs/evidencias/red-C-30/16-cancel-dismiss.txt` y `docs/evidencias/green-C-30/16-cancel-dismiss.txt`.
- [x] 5.3 Enviar `POST /api/appointments/{id}/cancel` sin cuerpo al confirmar y cerrar modal ante 200 OK. Evidencias: `docs/evidencias/red-C-30/17-cancel-ok.txt` y `docs/evidencias/green-C-30/17-cancel-ok.txt`.
- [x] 5.4 Procesar el error 422 `INVALID_TRANSITION` en cancelación mostrando el alert con foco. Evidencias: `docs/evidencias/red-C-30/18-cancel-error.txt` y `docs/evidencias/green-C-30/18-cancel-error.txt`.

## 6. Formulario y flujo de reprogramación

- [x] 6.1 Construir `AppointmentRescheduleDialog.tsx` con paciente y prestación fijos en solo lectura y prellenado de fecha, hora, profesional, sillón y duración actual. Evidencias: `docs/evidencias/red-C-30/19-reschedule-open.txt` y `docs/evidencias/green-C-30/19-reschedule-open.txt`.
- [x] 6.2 Enviar `POST /api/appointments/{id}/reschedule` con nuevo `startAt` formateado con offset exacto y cerrar modal ante 200 OK en estado reservado. Evidencias: `docs/evidencias/red-C-30/20-reschedule-ok.txt` y `docs/evidencias/green-C-30/20-reschedule-ok.txt`.
- [x] 6.3 Procesar el rechazo 409 con violaciones múltiples de solapamiento mostrando badges y referencias en el alert superior. Evidencias: `docs/evidencias/red-C-30/21-reschedule-overlap.txt` y `docs/evidencias/green-C-30/21-reschedule-overlap.txt`.
- [x] 6.4 Procesar el rechazo 422 `IN_THE_PAST` mostrando el mensaje del dominio en el alert superior. Evidencias: `docs/evidencias/red-C-30/22-reschedule-past.txt` y `docs/evidencias/green-C-30/22-reschedule-past.txt`.
- [x] 6.5 Mapear respuestas 400 a los campos del formulario con `aria-invalid="true"` y mensaje de error inline. Evidencias: `docs/evidencias/red-C-30/23-reschedule-400.txt` y `docs/evidencias/green-C-30/23-reschedule-400.txt`.
- [x] 6.6 Cancelar la reprogramación al pulsar "Cancelar" o Escape cerrando el diálogo y retornando foco al disparador. Evidencias: `docs/evidencias/red-C-30/24-reschedule-cancel.txt` y `docs/evidencias/green-C-30/24-reschedule-cancel.txt`.

## 7. Integración, control de acceso y anuncios accesibles

- [x] 7.1 Restringir acciones del rol Odontólogo en turnos propios a cambios de estado e historial, manteniendo ocultos reprogramar y cancelar. Evidencias: `docs/evidencias/red-C-30/25-rbac-dentist-own.txt` y `docs/evidencias/green-C-30/25-rbac-dentist-own.txt`.
- [x] 7.2 Bloquear acciones e historial para el rol Odontólogo sobre turnos de otros profesionales presentando vista de solo lectura. Evidencias: `docs/evidencias/red-C-30/26-rbac-dentist-other.txt` y `docs/evidencias/green-C-30/26-rbac-dentist-other.txt`.
- [x] 7.3 Procesar respuestas 403 `FORBIDDEN_OPERATION` mostrando el mensaje en alert de error sin cerrar sesión. Evidencias: `docs/evidencias/red-C-30/27-rbac-403.txt` y `docs/evidencias/green-C-30/27-rbac-403.txt`.
- [x] 7.4 Integrar la apertura modal en `AgendaPage.tsx` y certificar que cada mutación exitosa invoca `useAgenda().refresh()`. Evidencias: `docs/evidencias/red-C-30/28-refresh-agenda.txt` y `docs/evidencias/green-C-30/28-refresh-agenda.txt`.
- [x] 7.5 Emitir el anuncio "Turno confirmado." en la región permanente con `role="status"` tras confirmar. Evidencias: `docs/evidencias/red-C-30/29-announce-confirm.txt` y `docs/evidencias/green-C-30/29-announce-confirm.txt`.
- [x] 7.6 Emitir el anuncio "Turno marcado como atendido." en la región permanente con `role="status"` tras marcar atendido. Evidencias: `docs/evidencias/red-C-30/30-announce-attend.txt` y `docs/evidencias/green-C-30/30-announce-attend.txt`.
- [x] 7.7 Emitir el anuncio "Turno marcado como ausente." en la región permanente con `role="status"` tras marcar ausente. Evidencias: `docs/evidencias/red-C-30/31-announce-noshow.txt` y `docs/evidencias/green-C-30/31-announce-noshow.txt`.
- [x] 7.8 Emitir el anuncio "Turno cancelado." en la región permanente con `role="status"` tras cancelar. Evidencias: `docs/evidencias/red-C-30/32-announce-cancel.txt` y `docs/evidencias/green-C-30/32-announce-cancel.txt`.
- [x] 7.9 Emitir el anuncio "Turno reprogramado para el DD/MM/AAAA a las HH:MM." en la región permanente con `role="status"` tras reprogramar. Evidencias: `docs/evidencias/red-C-30/33-announce-reschedule.txt` y `docs/evidencias/green-C-30/33-announce-reschedule.txt`.

## 8. Verificación integral, mutaciones, trazabilidad y tooling

- [x] 8.1 Ejecutar suite completa de Vitest (línea base de 191 intactos + 33 tests nuevos = 224 tests en verde) y registrar salida en `docs/evidencias/test-suite-C-30.txt`.
- [x] 8.2 Ejecutar `tsc --noEmit` y `eslint .` verificando código de salida 0 en `docs/evidencias/tooling-C-30.txt`.
- [x] 8.3 Ejecutar `npm run build` verificando compilación de producción exitosa en `docs/evidencias/build-C-30.txt`.
- [x] 8.4 Ejecutar script de mutaciones `mutaciones-C-30.py` garantizando un mutante por test nuevo (33/33 muertos, 0 inválidas, 0 sobrevivientes, SHA-256 intacto) en `docs/evidencias/mutaciones-C-30.txt`.
- [x] 8.5 Ejecutar script de trazabilidad `trazabilidad-C-30.py` certificando relación 1:1 estricta entre escenarios y tests en `docs/evidencias/trazabilidad-C-30.txt`.
- [x] 8.6 Verificar ausencia de modificaciones en tests existentes (`git diff main --stat -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'` con `--diff-filter=M` vacío) en `docs/evidencias/diff-tests-existentes-C-30.txt`.
- [x] 8.7 Consolidar informe de verificación en `docs/evidencias/verify-C-30.md`.

## 9. Capturas visuales independientes a cargo de Claude

- [ ] 9.1 Inspección visual y capturas en escritorio a 1440 px: `C-30-detalle-turno-1440.png`, `C-30-historial-1440.png`, `C-30-reprogramar-1440.png`, `C-30-error-409-1440.png`.
- [ ] 9.2 Inspección visual y capturas en tablet a 768 px: `C-30-detalle-turno-768.png`, `C-30-confirmacion-cancelar-768.png`.
- [ ] 9.3 Inspección visual y capturas en móvil a 390 px: `C-30-detalle-turno-390.png`, `C-30-reprogramar-390.png`.

## Workflow follow-up

- Archivar el change mediante `/opsx:archive ui-reprogramar-cancelar-y-estados` tras la aprobación de evidencias y capturas.
- Marcar `[x]` en CHANGES.md sección [C-30].
