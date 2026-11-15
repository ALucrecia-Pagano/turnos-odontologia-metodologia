# Tasks: ui-horarios-y-bloqueos

## Reglas obligatorias y marco de trabajo

- **Regla C1 estricta**: Prohibido el uso de `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers`, MSW o esperas largas (`waitFor` mayor a 1000 ms). Las solicitudes HTTP se prueban inyectando un cliente real mediante `createApiClient({ fetchFn })` que retorne instancias reales de `Response`. El tiempo se fija exclusivamente con `createFixedClock`. El enrutamiento se evalúa con `createMemoryRouter + RouterProvider`. Queda estrictamente prohibido asignar o borrar globals en `window` o `globalThis`.
- **Prohibición de supresiones de tipos o linter**: Queda estrictamente prohibido el uso de `@ts-ignore`, `@ts-expect-error`, `type: ignore` o comentarios `eslint-disable`.
- **Preservación de tests existentes y desvío autorizado D1**: Los archivos de test preexistentes de `main` deben permanecer intactos, a excepción de las **11 aserciones en 3 archivos** del menú en `menuFor.test.ts` (4), `AppShell.test.tsx` (4) y `AppShellNavigation.test.tsx` (3), cuyo ajuste responde a un cambio de requisito explícito (D1; `AppShell.mobile.test.tsx` no requirió cambios). El diff de tests existentes del apply debe limitarse estrictamente a esas líneas. Todos los tests nuevos se ubican en archivos dedicados.
- **Strict TDD y Trazabilidad 1:1**: Un escenario = un test = una mutación eliminada. Cada test nuevo debe contar con su evidencia RED antes de implementar y su evidencia GREEN posterior en las carpetas `docs/evidencias/red-C-32/` y `docs/evidencias/green-C-32/`.
- **Script de mutaciones con detector de inválidas**: Normalización CRLF/LF, verificación de que el mutante efectivamente altere el código ("SHA-256 sin cambios: si"), 0 mutaciones inválidas y 0 supervivientes.
- **Trazabilidad estricta**: El script de trazabilidad debe fallar si dos escenarios comparten test o si algún escenario carece de prueba asociada.
- **Tokens de diseño**: Todos los colores, radios, espaciados y sombras se consumen exclusivamente desde `tokens.css`. Foco visible (`:focus-visible`), contraste AA y cero comunicación de estado basada únicamente en color.
- **Herramientas de calidad**: `tsc --noEmit`, `npm run lint` y `npm run build` deben finalizar con código de salida 0.
- **Evidencias en UTF-8**: Todas las evidencias se capturan con codificación UTF-8 desde Git Bash.
- **Rama de trabajo**: `c32-apply`.

---

## 1. Línea base y preparación

- [x] 1.1 Crear la rama `c32-apply` desde `main` y verificar que la suite completa de frontend pasa intacta (línea base de 297 tests pasando en 74 archivos) guardando salida en `docs/evidencias/baseline-C-32.txt`.
- [x] 1.2 Aplicar skill `appointment-frontend-ux` y consultar MCP `context7` (documentación pública sobre formularios y validaciones en React Router v6) registrando la justificación y consultas en `docs/skills-mcp/evidencias/C-32-skill-mcp.md`.
- [x] 1.3 Crear la estructura de carpetas `frontend/src/features/horarios/` y definir los tipos del contrato de horarios y bloqueos en `frontend/src/features/horarios/horariosApi.ts`.

## 2. Cliente de API de horarios y bloqueos

- [x] 2.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/horariosApi.test.ts` para parseo estricto de respuestas exitosas de `getWorkingHours`, `replaceWorkingHours`, `listBlocks`, `createBlock` y `deleteBlock`. Evidencia: `docs/evidencias/red-C-32/01-api-ok.txt`.
- [x] 2.2 **GREEN**: Implementar funciones tipadas en `horariosApi.ts` consumiendo `ApiClient` y gestionando errores HTTP (`400`, `403`, `422`). Evidencia: `docs/evidencias/green-C-32/01-api-ok.txt`.
- [x] 2.3 **REFACTOR**: Limpiar parseo y verificar que los tests pasan sin `any`.

## 3. Enrutamiento, página y menú

- [x] 3.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosRoute.test.tsx` verificando que `/horarios` renderiza el contenedor principal bajo `AppShell` para usuarios autenticados y redirige a login si es anónimo. Evidencia: `docs/evidencias/red-C-32/02-route.txt`.
- [x] 3.2 **GREEN**: Registrar la ruta `horarios` en `frontend/src/App.tsx` y conectar `HorariosPage`. Evidencia: `docs/evidencias/green-C-32/02-route.txt`.
- [x] 3.3 **RED**: Ejecutar tests de menú (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx`) comprobando el fallo esperado al habilitar "Horarios y bloqueos". Evidencia: `docs/evidencias/red-C-32/03-menu-pre.txt`.
- [x] 3.4 **GREEN**: Actualizar `menuFor.ts` (`path: "/horarios"`, habilitado para administrador, recepción y odontólogo) y actualizar las 11 aserciones específicas en 3 archivos (`menuFor.test.ts`: 4, `AppShell.test.tsx`: 4, `AppShellNavigation.test.tsx`: 3). Evidencia: `docs/evidencias/green-C-32/03-menu-ok.txt`.
- [x] 3.5 **REFACTOR**: Confirmar que el diff de tests existentes muestra únicamente las 11 aserciones en 3 archivos autorizadas por el cambio de requerimiento D1.

## 4. Tramos semanales y validación de solapes

- [x] 4.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/WorkingHoursSection.test.tsx` para el guardado exitoso de tramos semanales enviando `PUT` crudo y anunciando "Horario guardado." en `role="status"`. Evidencia: `docs/evidencias/red-C-32/04-hours-save-ok.txt`.
- [x] 4.2 **GREEN**: Implementar `WorkingHoursSection.tsx` con grilla de 7 días, inputs de texto `HH:MM`, soporte de `24:00` en fin y botón "Guardar horario". Evidencia: `docs/evidencias/green-C-32/04-hours-save-ok.txt`.
- [x] 4.3 **RED**: Escribir test unitario en `frontend/src/features/horarios/WorkingHoursSection.test.tsx` para la adición y eliminación dinámica de tramos con los botones "Agregar tramo" y "Quitar". Evidencia: `docs/evidencias/red-C-32/05-hours-add-remove.txt`.
- [x] 4.4 **GREEN**: Implementar handlers locales de agregado y borrado de filas en `WorkingHoursSection.tsx`. Evidencia: `docs/evidencias/green-C-32/05-hours-add-remove.txt`.
- [x] 4.5 **RED**: Escribir test unitario en `frontend/src/features/horarios/WorkingHoursSection.test.tsx` para el rechazo 422 `OVERLAPPING_WORKING_HOURS` mostrando el mensaje literal del backend en `role="alert"` con foco automático. Evidencia: `docs/evidencias/red-C-32/06-hours-overlap-422.txt`.
- [x] 4.6 **GREEN**: Manejar violaciones 422 en `WorkingHoursSection.tsx` renderizando el mensaje en alerta accesible y trasladando el foco con `ref`. Evidencia: `docs/evidencias/green-C-32/06-hours-overlap-422.txt`.
- [x] 4.7 **RED**: Escribir test unitario en `frontend/src/features/horarios/WorkingHoursSection.test.tsx` para errores 400 de formato marcando inputs con `aria-invalid="true"`. Evidencia: `docs/evidencias/red-C-32/07-hours-format-400.txt`.
- [x] 4.8 **GREEN**: Conectar marcado accesible `aria-invalid` ante respuestas 400. Evidencia: `docs/evidencias/green-C-32/07-hours-format-400.txt`.

## 5. Bloqueos de agenda y confirmación in-dialog

- [x] 5.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/BlocksSection.test.tsx` para creación exitosa de bloqueo enviando `POST` con instantes ISO con offset (`buildStartAtIso`), cierre de diálogo y anuncio "Bloqueo creado." en `role="status"`. Evidencia: `docs/evidencias/red-C-32/08-block-create-ok.txt`.
- [x] 5.2 **GREEN**: Construir `BlocksSection.tsx` y `BlockFormDialog.tsx` sobre `Dialog.tsx`. Evidencia: `docs/evidencias/green-C-32/08-block-create-ok.txt`.
- [x] 5.3 **RED**: Escribir test unitario en `frontend/src/features/horarios/BlocksSection.test.tsx` para eliminación de bloqueo con confirmación in-dialog enviando `DELETE` tras confirmar y anunciando "Bloqueo eliminado." en `role="status"`. Evidencia: `docs/evidencias/red-C-32/09-block-delete-ok.txt`.
- [x] 5.4 **GREEN**: Construir `BlockDeleteDialog.tsx` con confirmación destructiva y feedback accesible. Evidencia: `docs/evidencias/green-C-32/09-block-delete-ok.txt`.
- [x] 5.5 **RED**: Escribir test unitario en `frontend/src/features/horarios/BlocksSection.test.tsx` verificando que presionar Escape o pulsar "Volver" en el diálogo de eliminación no envía ninguna petición `DELETE` y conserva el bloqueo. Evidencia: `docs/evidencias/red-C-32/10-block-delete-escape.txt`.
- [x] 5.6 **GREEN**: Conectar manejo de Escape y cancelación en `BlockDeleteDialog.tsx`. Evidencia: `docs/evidencias/green-C-32/10-block-delete-escape.txt`.
- [x] 5.7 **RED**: Escribir test unitario en `frontend/src/features/horarios/BlocksSection.test.tsx` para bloqueo inválido rechazado con 422 `INVALID_BLOCK` manteniendo el diálogo abierto con el mensaje literal en `role="alert"`. Evidencia: `docs/evidencias/red-C-32/11-block-invalid-422.txt`.
- [x] 5.8 **GREEN**: Procesar respuesta 422 en `BlockFormDialog.tsx` sin cerrar el diálogo. Evidencia: `docs/evidencias/green-C-32/11-block-invalid-422.txt`.
- [x] 5.9 **RED**: Escribir test unitario en `frontend/src/features/horarios/BlockFormDialog.mobile.test.tsx` comprobando que a ≤ 640 px el modal adopta la clase y estilos de hoja inferior (bottom sheet). Evidencia: `docs/evidencias/red-C-32/12-block-bottom-sheet.txt`.
- [x] 5.10 **GREEN**: Aplicar estilos responsivos en `BlockFormDialog.module.css` heredando la hoja inferior de C-36. Evidencia: `docs/evidencias/green-C-32/12-block-bottom-sheet.txt`.

## 6. Aviso de turnos afectados

- [x] 6.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/AffectedAppointments.test.tsx` para aviso de turnos futuros fuera de horario al guardar tramos (`appointmentsOutsideHours`), verificando renderizado de fecha, hora local, paciente, profesional, `StatusBadge` y nota de no cancelación en `role="alert"`. Evidencia: `docs/evidencias/red-C-32/13-affected-hours.txt`.
- [x] 6.2 **GREEN**: Implementar componente `AffectedAppointments.tsx` y formateadores de fecha en `horariosTime.ts`. Evidencia: `docs/evidencias/green-C-32/13-affected-hours.txt`.
- [x] 6.3 **RED**: Escribir test unitario en `frontend/src/features/horarios/AffectedAppointments.test.tsx` para aviso de turnos solapados al crear un bloqueo (`affectedAppointments`). Evidencia: `docs/evidencias/red-C-32/14-affected-block.txt`.
- [x] 6.4 **GREEN**: Conectar `AffectedAppointments` a `BlocksSection.tsx` tras el alta de bloqueos. Evidencia: `docs/evidencias/green-C-32/14-affected-block.txt`.

## 7. Roles, permisos y control de acceso

- [x] 7.1 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosPage.test.tsx` para odontólogo accediendo a sus propios horarios (`user.professionalId`) sin selector visible. Evidencia: `docs/evidencias/red-C-32/15-role-dentist-own.txt`.
- [x] 7.2 **GREEN**: Conectar resolución de target en `HorariosPage.tsx` para el rol odontólogo. Evidencia: `docs/evidencias/green-C-32/15-role-dentist-own.txt`.
- [x] 7.3 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosPage.test.tsx` para administrador seleccionando profesional activo en el desplegable y sincronizando `?professionalId=`. Evidencia: `docs/evidencias/red-C-32/16-role-admin-selector.txt`.
- [x] 7.4 **GREEN**: Implementar selector de profesionales activos para administrador en `HorariosPage.tsx`. Evidencia: `docs/evidencias/green-C-32/16-role-admin-selector.txt`.
- [x] 7.5 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosPage.test.tsx` para odontólogo intentando consultar profesional ajeno por URL recibiendo 403 `FORBIDDEN_OPERATION` y mostrando el error literal en `role="alert"` sin cerrar sesión. Evidencia: `docs/evidencias/red-C-32/17-role-dentist-403.txt`.
- [x] 7.6 **GREEN**: Gestionar rechazo 403 en `HorariosPage.tsx` manteniendo la sesión activa. Evidencia: `docs/evidencias/green-C-32/17-role-dentist-403.txt`.
- [x] 7.7 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosPage.test.tsx` para rol recepción verificando modo de solo lectura (selector y listas visibles; botones "Agregar tramo", "Quitar", "Guardar horario", "Nuevo bloqueo" y "Eliminar bloqueo" ausentes). Evidencia: `docs/evidencias/red-C-32/18-role-reception-readonly.txt`.
- [x] 7.8 **GREEN**: Condicionar visibilidad de acciones de mutación según rol en `HorariosPage.tsx`, `WorkingHoursSection.tsx` y `BlocksSection.tsx`. Evidencia: `docs/evidencias/green-C-32/18-role-reception-readonly.txt`.
- [x] 7.9 **RED**: Escribir test unitario en `frontend/src/features/horarios/HorariosPage.test.tsx` verificando la lectura de `timezone` desde `GET /api/agenda` una sola vez y su reutilización. Evidencia: `docs/evidencias/red-C-32/19-timezone-api.txt`.
- [x] 7.10 **GREEN**: Implementar consulta inicial a `GET /api/agenda` en `HorariosPage.tsx` y propagar la zona horaria a los submódulos. Evidencia: `docs/evidencias/green-C-32/19-timezone-api.txt`.

## 8. Verificación integral, mutaciones y trazabilidad

- [x] 8.1 Ejecutar suite completa de Vitest (línea base de 297 tests + nuevos tests = tests en verde) y registrar salida en `docs/evidencias/test-suite-C-32.txt`.
- [x] 8.2 Ejecutar `tsc --noEmit` y `npm run lint` verificando código de salida 0 en `docs/evidencias/tooling-C-32.txt`.
- [x] 8.3 Ejecutar `npm run build` verificando compilación de producción limpia en `docs/evidencias/build-C-32.txt`.
- [x] 8.4 Implementar y ejecutar script de mutaciones `docs/evidencias/mutaciones-C-32.py` garantizando que cada mutación sea eliminada por su test asociado (0 supervivientes, 0 inválidas) en `docs/evidencias/mutaciones-C-32.txt`.
- [x] 8.5 Implementar y ejecutar script de trazabilidad `docs/evidencias/trazabilidad-C-32.py` certificando relación 1:1 estricta entre escenarios y tests en `docs/evidencias/trazabilidad-C-32.txt`.
- [x] 8.6 Verificar que el diff de tests existentes (`git diff main --diff-filter=M -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'`) refleje estrictamente las 11 aserciones en 3 archivos del cambio de requerimiento del menú en `docs/evidencias/diff-tests-existentes-C-32.txt`.
- [x] 8.7 Consolidar informe de verificación en `docs/evidencias/verify-C-32.md`.

## 9. Capturas visuales multi-resolución a cargo de Claude

- [ ] 9.1 Tomar capturas reales en escritorio a 1440 px: vista en 2 columnas con horarios y bloqueos (`docs/evidencias/capturas/C-32-horarios-1440.png`), diálogo de nuevo bloqueo (`docs/evidencias/capturas/C-32-nuevo-bloqueo-1440.png`), diálogo de confirmación de eliminación (`docs/evidencias/capturas/C-32-eliminar-bloqueo-1440.png`), aviso de turnos afectados (`docs/evidencias/capturas/C-32-turnos-afectados-1440.png`) y vista de recepción solo lectura (`docs/evidencias/capturas/C-32-recepcion-1440.png`).
- [ ] 9.2 Tomar capturas reales en tablet a 768 px: vista en columna única apilada (`docs/evidencias/capturas/C-32-horarios-768.png`).
- [ ] 9.3 Tomar capturas reales en móvil a 390 px: vista apilada sin scroll horizontal (`docs/evidencias/capturas/C-32-horarios-390.png`) y diálogo de bloqueo como hoja inferior (`docs/evidencias/capturas/C-32-nuevo-bloqueo-390.png`).

## 10. Corrección post-verificación (A–E)

- [x] 10.1 **RED (A)**: Escribir test en `frontend/src/features/horarios/horariosStyles.test.ts` verificando con `readSrcFile` que todas las variables `var(--x)` en los `.module.css` de `features/horarios/` existen en `frontend/src/shared/styles/tokens.css`. Evidencia: `docs/evidencias/red-C-32/20-css-tokens-exist.txt`.
- [x] 10.2 **GREEN (A)**: Reemplazar los tokens inexistentes en los `.module.css` de `features/horarios/` únicamente por tokens definidos en `tokens.css` (sin agregar nuevos a `tokens.css`). Evidencia: `docs/evidencias/green-C-32/20-css-tokens-exist.txt`.
- [x] 10.3 **RED (B)**: Escribir test en `frontend/src/features/horarios/horariosStyles.test.ts` verificando que `HorariosPage.module.css` no use `--color-ice` ni tokens `*-on-navy` y emplee tokens de superficie clara. Evidencia: `docs/evidencias/red-C-32/21-css-header-light-tokens.txt`.
- [x] 10.4 **GREEN (B)**: Reemplazar en `HorariosPage.module.css` los tokens de cabecera oscura (`--color-ice`, `--field-on-navy`, `--border-on-navy-strong`, `--alert-on-navy-*`) por tokens de fondo claro (`--color-text`, `--color-text-muted`, `--color-background`, `--color-border`, `--color-danger-*`). Evidencia: `docs/evidencias/green-C-32/21-css-header-light-tokens.txt`.
- [x] 10.5 **RED (C)**: Escribir test en `frontend/src/features/horarios/HorariosPage.test.tsx` verificando que `HorariosPage` pase `title="Horarios y bloqueos"` a `PageShell` y mantenga un único `<h1>`. Evidencia: `docs/evidencias/red-C-32/22-pageshell-title-h1.txt`.
- [x] 10.6 **GREEN (C)**: Actualizar `title="Horarios y bloqueos"` en `HorariosPage.tsx` manteniendo un solo `<h1>`. Evidencia: `docs/evidencias/green-C-32/22-pageshell-title-h1.txt`.
- [x] 10.7 **RED (D1)**: Escribir test en `frontend/src/features/horarios/BlocksSection.test.tsx` verificando que al eliminar un bloqueo desaparezca el panel `"Turnos existentes solapados con el bloqueo creado"`. Evidencia: `docs/evidencias/red-C-32/23-delete-block-clears-affected.txt`.
- [x] 10.8 **GREEN (D1)**: Limpiar `affectedAppointments` en `BlocksSection.tsx` al confirmar la eliminación de un bloqueo. Evidencia: `docs/evidencias/green-C-32/23-delete-block-clears-affected.txt`.
- [x] 10.9 **RED (D2)**: Escribir test en `frontend/src/features/horarios/HorariosPage.test.tsx` verificando que el mensaje de estado (`"Horario guardado."`, `"Bloqueo creado."`, `"Bloqueo eliminado."`) se reemplace o limpie cuando empieza otra acción sin que coexistan dos mensajes distintos y manteniendo la región `role="status"` montada. Evidencia: `docs/evidencias/red-C-32/24-single-status-message.txt`.
- [x] 10.10 **GREEN (D2)**: Unificar el estado `role="status"` en `HorariosPage.tsx`, `WorkingHoursSection.tsx` y `BlocksSection.tsx` manteniendo la región siempre montada y reemplazando el mensaje entre acciones. Evidencia: `docs/evidencias/green-C-32/24-single-status-message.txt`.
- [x] 10.11 **RED (E)**: Escribir test en `frontend/src/features/horarios/AffectedAppointments.test.tsx` verificando que las fechas en turnos afectados, lista de bloqueos y modal de eliminar se muestren en formato local con `Intl.DateTimeFormat("es-AR", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric", timeZone })` (`"mar, 17/11/2026"` para `"2026-11-17T15:00:00Z"`) y no en ISO `"2026-11-17"`. Evidencia: `docs/evidencias/red-C-32/25-dates-local-format.txt`.
- [x] 10.12 **GREEN (E)**: Actualizar `formatLocalRangeInZone` en `horariosTime.ts` para formatear la fecha con `Intl.DateTimeFormat("es-AR", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric", timeZone })` usando la zona horaria leída de `GET /api/agenda`. Evidencia: `docs/evidencias/green-C-32/25-dates-local-format.txt`.
- [x] 10.13 Actualizar `mutaciones-C-32.py` (26 mutaciones M01–M26, 0 supervivientes, 0 inválidas), `trazabilidad-C-32.py` (numeración continua 01..24 + V01, V02 sin saltos), regenerar `test-suite-C-32.txt`, `tooling-C-32.txt`, `build-C-32.txt`, `validate-C-32.txt`, `diff-tests-existentes-C-32.txt` (con `2>/dev/null`) y actualizar `docs/evidencias/verify-C-32.md`.

---

## Tabla final: Escenario → Test → Mutación

| # | Spec | Requisito | Escenario | Tipo | Archivo de Test | Mutación Asociada |
|---|---|---|---|---|---|---|
| 01 | `frontend-working-hours-and-blocks` | Ruta y resolución de profesional por rol | Odontólogo accede a sus propios horarios | Testeable | `HorariosPage.test.tsx` | M01: Renderizar selector de profesionales para odontólogo |
| 02 | `frontend-working-hours-and-blocks` | Ruta y resolución de profesional por rol | Administrador selecciona profesional activo | Testeable | `HorariosPage.test.tsx` | M02: Incluir profesionales inactivos en el selector de admin |
| 03 | `frontend-working-hours-and-blocks` | Ruta y resolución de profesional por rol | Odontólogo consulta profesional ajeno y recibe 403 | Testeable | `HorariosPage.test.tsx` | M03: Omitir alerta role="alert" o desloguear ante error 403 |
| 04 | `frontend-working-hours-and-blocks` | Gestión y guardado de tramos semanales | Guardado exitoso de tramos semanales | Testeable | `WorkingHoursSection.test.tsx` | M04: No enviar PUT o cambiar el orden visual de los tramos |
| 05 | `frontend-working-hours-and-blocks` | Gestión y guardado de tramos semanales | Edición interactiva de tramos en la interfaz | Testeable | `WorkingHoursSection.test.tsx` | M05: No agregar o no remover la fila editable al pulsar los botones |
| 06 | `frontend-working-hours-and-blocks` | Validación de tramos y errores de solapamiento | Rechazo por tramos solapados muestra mensaje literal del backend | Testeable | `WorkingHoursSection.test.tsx` | M06: Reformular mensaje del backend o no trasladar foco al alert |
| 07 | `frontend-working-hours-and-blocks` | Validación de tramos y errores de solapamiento | Error 400 marca campos con aria-invalid | Testeable | `WorkingHoursSection.test.tsx` | M07: Omitir aria-invalid="true" en campos con error 400 |
| 08 | `frontend-working-hours-and-blocks` | Aviso de turnos afectados sin cancelación | Turnos futuros fuera del horario al guardar tramos | Testeable | `AffectedAppointments.test.tsx` | M08: Omitir lista de afectados o emitir acción de cancelación automática |
| 09 | `frontend-working-hours-and-blocks` | Aviso de turnos afectados sin cancelación | Turnos solapados al crear un bloqueo | Testeable | `AffectedAppointments.test.tsx` | M09: Omitir advertencia de turnos solapados en BlocksSection |
| 10 | `frontend-working-hours-and-blocks` | Creación y eliminación de bloqueos con hora local | Creación exitosa de bloqueo con offset | Testeable | `BlocksSection.test.tsx` | M10: Enviar ISO sin offset de zona horaria o no cerrar modal |
| 11 | `frontend-working-hours-and-blocks` | Creación y eliminación de bloqueos con hora local | Eliminación de bloqueo con confirmación in-dialog | Testeable | `BlocksSection.test.tsx` | M11: Enviar DELETE antes de que el usuario confirme en el diálogo |
| 12 | `frontend-working-hours-and-blocks` | Creación y eliminación de bloqueos con hora local | Cancelación del borrado con Escape | Testeable | `BlocksSection.test.tsx` | M12: Enviar DELETE o cerrar pantalla al pulsar Escape en confirmación |
| 13 | `frontend-working-hours-and-blocks` | Creación y eliminación de bloqueos con hora local | Bloqueo inválido muestra mensaje literal del backend | Testeable | `BlocksSection.test.tsx` | M13: Cerrar diálogo ante error 422 de bloqueo inválido |
| 14 | `frontend-working-hours-and-blocks` | Modo solo lectura para rol recepción | Recepción visualiza información completa sin controles de edición | Testeable | `HorariosPage.test.tsx` | M14: Renderizar botones de edición/borrado para rol recepción |
| 15 | `frontend-working-hours-and-blocks` | Obtención y reutilización de zona horaria desde la API | Zona horaria leída desde GET /api/agenda | Testeable | `HorariosPage.test.tsx` | M15: Hardcodear timezone fija en lugar de leerla de GET /api/agenda |
| 16 | `frontend-working-hours-and-blocks` | Adaptabilidad móvil y responsive en 1440, 768 y 390 px | Presentación de modal como hoja inferior en móvil | Testeable | `BlockFormDialog.mobile.test.tsx` | M16: Omitir clase de hoja inferior en Dialog a ≤ 640 px |
| 17 | `frontend-foundation` | Navegación de AppShell sin cajas | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Testeable | `AppShellNavigation.test.tsx` | M17: Omitir enlace activo a /horarios en la barra de navegación |
| 18 | `frontend-foundation` | Navegación de AppShell sin cajas | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Testeable | `AppShellNavigation.test.tsx` | M18: Mantener "Próximamente" en Horarios y bloqueos para roles activos |
| 19 | `frontend-working-hours-and-blocks` | Uso exclusivo de tokens definidos y superficie clara en estilos de horarios | Todas las variables CSS de horarios existen en tokens.css | Testeable | `horariosStyles.test.ts` | M21: Introducir variable CSS inexistente en estilos de horarios |
| 20 | `frontend-working-hours-and-blocks` | Uso exclusivo de tokens definidos y superficie clara en estilos de horarios | Encabezado y estilos de HorariosPage sin tokens de fondo oscuro | Testeable | `horariosStyles.test.ts` | M22: Usar token de cabecera oscura (--color-ice) en HorariosPage.module.css |
| 21 | `frontend-working-hours-and-blocks` | Ruta y resolución de profesional por rol | Título de PageShell Horarios y bloqueos con único h1 | Testeable | `HorariosPage.test.tsx` | M23: Pasar title="Turnos Odontología" a PageShell en HorariosPage.tsx |
| 22 | `frontend-working-hours-and-blocks` | Aviso de turnos afectados sin cancelación | Eliminar bloqueo oculta su panel de turnos afectados | Testeable | `BlocksSection.test.tsx` | M24: No limpiar affectedAppointments al confirmar eliminación de bloqueo |
| 23 | `frontend-working-hours-and-blocks` | Gestión y guardado de tramos semanales | Un solo mensaje de estado vigente entre acciones sin desmontar la región | Testeable | `HorariosPage.test.tsx` | M25: No propagar el reemplazo de mensaje de estado compartido en HorariosPage |
| 24 | `frontend-working-hours-and-blocks` | Obtención y reutilización de zona horaria desde la API | Fechas en formato local es-AR en turnos afectados, bloqueos y modal de eliminar | Testeable | `AffectedAppointments.test.tsx` | M26: Mostrar fecha en formato ISO YYYY-MM-DD en formatLocalRangeInZone |
| V01 | `frontend-working-hours-and-blocks` | Adaptabilidad móvil y responsive en 1440, 768 y 390 px | Verificación visual multi-resolución en 1440, 768 y 390 px | Visual | `C-32-horarios-{1440,768,390}.png` | V01: Recorte o desbordamiento horizontal en capturas reales |
| V02 | `frontend-foundation` | Navegación de AppShell sin cajas | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | `C-32-appshell-{768,390}.png` | V02: Barra de navegación supera 2 renglones en tablet en captura |

---

## Workflow follow-up

- Archivar el change mediante `/opsx:archive ui-horarios-y-bloqueos` una vez verificadas todas las tareas y aprobadas las capturas visuales.
- Marcar `[x]` en `CHANGES.md` para el change C-32.
- Sincronizar las delta specs hacia las specs principales en `openspec/specs/`.
