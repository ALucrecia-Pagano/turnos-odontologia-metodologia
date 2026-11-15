# Tasks: ui-catalogos-y-pacientes

## Reglas obligatorias

- **Regla C1**: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers`, MSW ni `waitFor` largos. La red va solo con `createApiClient({ baseUrl, fetchFn })` y `Response` reales. El router, con `createMemoryRouter(createAppRoutes(...))` + `RouterProvider` dentro de `AuthProvider` (`createMemoryTokenStore`). No se asignan ni se borran globals en `window` o `globalThis`.
- **Sin supresiones**: prohibidos `@ts-ignore`, `@ts-expect-error` y `eslint-disable`.
- **Strict TDD**: un escenario = un test = una mutación propia. RED (el test falla por la razón esperada) antes del código de producción y GREEN después, con evidencia en `docs/evidencias/red-C-33/NN-*.txt` y `docs/evidencias/green-C-33/NN-*.txt`. Un test auxiliar que se agregue también lleva su mutación y su número.
- **Tests existentes intactos**, salvo las aserciones del menú afectadas por el cambio de requisito (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y los que correspondan; design.md D9). El conteo real de aserciones modificadas por archivo se mide con `git diff` en el apply y se declara como desvío en `verify-C-33.md`. **Los títulos históricos de tests no se renombran.**
- **Tokens**: solo los de `frontend/src/shared/styles/tokens.css`, sin agregar ninguno. Nada de `--color-ice` ni `*-on-navy`; sin HEX ni `rgb()` sueltos.
- **PageShell** con `title="Pacientes"` / `title="Catálogos"` y un único `<h1>` por pantalla.
- **Una sola región `role="status"`** por pantalla, siempre montada y con un mensaje vigente por vez.
- **Fechas**: estas pantallas no muestran fechas. Si se agregara alguna, `Intl.DateTimeFormat("es-AR", { timeZone })` con la zona de `GET /api/agenda`.
- **Datos ficticios** (RN-PA-02) en tests y capturas.
- **Calidad**: `npm run typecheck`, `npm run lint` y `npm run build` con código de salida 0.
- **Evidencias** en UTF-8 desde Git Bash. Rama de trabajo del apply: `c33-apply`.

---

## 1. Línea base y preparación

- [ ] 1.1 Crear la rama `c33-apply` desde `main` (con C-32 mergeado), correr la suite completa del frontend y guardar la salida en `docs/evidencias/baseline-C-33.txt`. Verificación: todo en verde; se anota el conteo real (la última evidencia de C-32 dice 321 tests en 82 archivos).
- [ ] 1.2 Aplicar la skill `appointment-frontend-ux` y, solo si se usa una API de React Router o Testing Library que no esté ya en el repo, consultar Context7. Registrar qué se consultó y por qué en `docs/skills-mcp/evidencias/C-33-skill-mcp.md`. Verificación: el archivo existe y nombra la skill y las consultas (o declara que no hubo).
- [ ] 1.3 Buscar sobre `main` los tests existentes que dependen de "Catálogos", "Pacientes" o "Próximamente" en el menú (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y cualquier otro que aparezca) y anotar en `docs/evidencias/baseline-C-33.txt` los archivos y las aserciones que el cambio de requisito va a afectar. No se fija un conteo de antemano. Verificación: la lista de archivos y aserciones está en la evidencia.

## 2. Fase 1: pacientes, listado y búsqueda (escenarios 01-06)

- [ ] 2.1 Crear `features/pacientes/pacientesApi.ts` con `listPatients(client, query?)` y su parser estricto, y registrar la ruta `pacientes` en `App.tsx` apuntando a `PacientesPage`. Verificación: se cubre con los escenarios 01-04 (no lleva test propio sin escenario).
- [ ] 2.2 **01 RED/GREEN**: en `features/pacientes/PacientesPage.test.tsx`, "Listado de pacientes con sus cuatro datos" (tabla con 4 columnas y "Sin dato" para `null`). Evidencia `red-C-33/01-pacientes-listado.txt` y `green-C-33/01-pacientes-listado.txt`.
- [ ] 2.3 **02 RED/GREEN**: en `PacientesPage.test.tsx`, "Búsqueda envía la consulta codificada y muestra el resultado" (`GET /api/patients?query=Ana%20P%C3%A9rez`). Evidencia `02-pacientes-busqueda`.
- [ ] 2.4 **03 RED/GREEN**: en `PacientesPage.test.tsx`, "Búsqueda sin resultados" ("No se encontraron pacientes." y sin filas viejas). Evidencia `03-pacientes-sin-resultados`.
- [ ] 2.5 **04 RED/GREEN**: en `PacientesPage.test.tsx`, "Error de carga de pacientes con reintento" (`500` y luego lista; dos llamadas). Evidencia `04-pacientes-reintento`.
- [ ] 2.6 **05 RED/GREEN**: en `features/catalogos/catalogosPacientesStyles.test.ts`, "Toda variable CSS de las pantallas existe en tokens.css". Lista los `.module.css` de `features/pacientes/` y `features/catalogos/` con `readdirSync`, captura `var(` con y sin respaldo, y verifica que no haya HEX ni `rgb()`. Evidencia `05-css-tokens-existen`.
- [ ] 2.7 **06 RED/GREEN**: en `catalogosPacientesStyles.test.ts`, "Sin tokens de fondo oscuro en las pantallas" (sin `--color-ice` ni `on-navy`). Evidencia `06-css-superficie-clara`.
- [ ] 2.8 **REFACTOR fase 1**: limpiar nombres y duplicación. Verificación: `npx vitest run src/features/pacientes src/features/catalogos` en verde y `npm run typecheck` en 0.

## 3. Fase 2: catálogos en solo lectura, título, tablas adaptables y menú (escenarios 07-13)

- [ ] 3.1 Crear `features/catalogos/catalogosApi.ts` (`listCatalog` genérico con parsers por entidad), `catalogConfigs.ts` (solo datos: ruta, columnas, etiquetas) y `ActiveBadge.tsx`, y registrar la ruta `catalogos` en `App.tsx`. Verificación: se cubre con los escenarios 07-09.
- [ ] 3.2 **07 RED/GREEN**: en `features/catalogos/CatalogosPage.test.tsx`, "Profesionales por defecto con estado en texto" (sin `active` en la URL; también con `?seccion=desconocida`). Evidencia `07-catalogos-profesionales-defecto`.
- [ ] 3.3 **08 RED/GREEN**: en `CatalogosPage.test.tsx`, "Cambio a la sección de prestaciones" (`?seccion=prestaciones`, `GET /api/services`, `aria-current`). Evidencia `08-catalogos-cambio-seccion`.
- [ ] 3.4 **09 RED/GREEN**: en `features/catalogos/CatalogosPacientesRoutes.test.tsx`, "Pacientes y Catálogos con su título y un único h1". Evidencia `09-titulo-h1`.
- [ ] 3.5 **10 RED/GREEN**: en `catalogosPacientesStyles.test.ts`, "Tablas apiladas en celular, controles táctiles y foco visible" (`@media (max-width: 640px)`, `min-height: 44px`, `:focus-visible`). Evidencia `10-css-tablas-adaptables`.
- [ ] 3.6 **11 RED**: escribir en el archivo **nuevo** `frontend/src/shared/components/AppShellCatalogosPacientes.test.tsx` el escenario "Catálogos y Pacientes habilitados para los tres roles" y comprobar que falla con `menuFor.ts` sin cambios. Evidencia `red-C-33/11-menu-habilitado.txt`.
- [ ] 3.7 **11 GREEN**: agregar `ENABLED_MENU_IDS` en `menuFor.ts`, sin parámetro nuevo ni seams. Correr también `menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y los demás de la tarea 1.3, y guardar las aserciones que ahora fallan por el cambio de requisito (`red-C-33/12-13-menu-existentes.txt`). Evidencia `green-C-33/11-menu-habilitado.txt`.
- [ ] 3.8 **12 y 13 (tests existentes, cambio de requisito)**: actualizar solo las aserciones que fallaron en 3.7 por el cambio de requisito (si en el odontólogo no quedan botones, `getAllByRole` pasa a `queryAllByRole` con `[]`), sin seams y sin renombrar títulos. Verificación: los archivos tocados en verde (`green-C-33/12-13-menu-existentes.txt`) y `git diff main --stat` solo con los tests de menú identificados en 1.3. El conteo real por archivo se toma de ese diff.
- [ ] 3.9 **REFACTOR fase 2** y **punto de corte del Plan B**: suite completa en verde, `npm run typecheck` y `npm run lint` en 0. Si el 17/11 no hay margen, se saltan las secciones 4 y 5, se aplica el Plan B de design.md D2 y se sigue con las secciones 6 y 7. Evidencia `docs/evidencias/corte-fase2-C-33.txt`.

## 4. Fase 3: formularios de alta y edición en Dialog (escenarios 14-28)

- [ ] 4.1 Agregar `createPatient` y `updatePatient` a `pacientesApi.ts`, y `createCatalogItem` y `updateCatalogItem` a `catalogosApi.ts` (con la duración como número y vacíos como `null`). Verificación: se cubre con los escenarios 14, 16, 22 y 26.
- [ ] 4.2 **14 RED/GREEN**: en `features/pacientes/PatientFormDialog.test.tsx`, "Alta de paciente" (POST camelCase con `null`, cierre, refresco y "Paciente creado."). Evidencia `14-paciente-alta`.
- [ ] 4.3 **15 RED/GREEN**: en `PatientFormDialog.test.tsx`, "El formulario de paciente tiene solo los cuatro datos mínimos" (4 campos; sin "Desactivar", "Reactivar" ni "Eliminar"). Evidencia `15-paciente-cuatro-campos`.
- [ ] 4.4 **16 RED/GREEN**: en `PatientFormDialog.test.tsx`, "Edición de paciente con valores precargados" (PUT con los 4 campos y "Paciente actualizado."). Evidencia `16-paciente-edicion`.
- [ ] 4.5 **17 RED/GREEN**: en `PatientFormDialog.test.tsx`, "DNI duplicado muestra el mensaje literal del backend" (`409`, `role="alert"` con foco, sin `aria-invalid` en DNI). Evidencia `17-paciente-dni-duplicado`.
- [ ] 4.6 **18 RED/GREEN**: en `PatientFormDialog.test.tsx`, "DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)" (DNI "1234" enviado tal cual en un único POST; `422`; `role="alert"` con foco y el mensaje exacto; el diálogo sigue abierto). Evidencia `18-paciente-dni-invalido`.
- [ ] 4.7 **19 RED/GREEN**: en `PatientFormDialog.test.tsx`, "Error 400 por campo marca el campo con aria-invalid" (`fullName`, "Falta este dato.", `aria-describedby`). Evidencia `19-paciente-400-campo`.
- [ ] 4.8 **20 RED/GREEN**: en `PacientesPage.test.tsx`, "Odontólogo consulta pacientes en solo lectura". Evidencia `20-pacientes-odontologo-lectura`.
- [ ] 4.9 **21 RED/GREEN**: en `PatientFormDialog.test.tsx`, "El mensaje de estado se reemplaza entre acciones sin desmontar la región" (misma región `role="status"`; solo "Paciente actualizado."). Evidencia `21-status-unico`.
- [ ] 4.10 **22 RED/GREEN**: en `features/catalogos/CatalogFormDialog.test.tsx`, "Alta de prestación con duración numérica" (`defaultDurationMin: 30` como número y "Prestación creada."). Evidencia `22-prestacion-alta`.
- [ ] 4.11 **23 RED/GREEN**: en `CatalogFormDialog.test.tsx`, "Duración no entera no se envía" (vacío y "abc"; ningún POST; mensaje del cliente con `aria-invalid`). Evidencia `23-duracion-no-entera`.
- [ ] 4.12 **24 RED/GREEN**: en `CatalogFormDialog.test.tsx`, "Duración inválida muestra el mensaje literal del backend" (`422 INVALID_DURATION`; el diálogo sigue abierto). Evidencia `24-duracion-422`.
- [ ] 4.13 **25 RED/GREEN**: en `CatalogFormDialog.test.tsx`, "Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)" (prestación "Limpieza"; `409`; `role="alert"` con foco y el mensaje exacto; sin `aria-invalid` en "Nombre"). Es la única cobertura del 409 de nombre duplicado (design.md D7). Evidencia `25-catalogo-nombre-duplicado`.
- [ ] 4.14 **26 RED/GREEN**: en `CatalogFormDialog.test.tsx`, "Edición de profesional con matrícula vacía" (`licenseNumber: null` y "Profesional actualizado."). Evidencia `26-profesional-edicion`.
- [ ] 4.15 **27 RED/GREEN**: en `CatalogosPage.test.tsx`, "Recepción y odontólogo consultan catálogos en solo lectura" ("Solo lectura" y sin botones de escritura, en los dos roles). Evidencia `27-catalogos-solo-lectura`.
- [ ] 4.16 **28 RED/GREEN**: en `features/catalogos/CatalogFormDialog.mobile.test.tsx`, "Formulario de catálogo como hoja inferior en celular" (`isMobile`, `data-mobile-sheet="true"`, clase de hoja inferior), con `BlockFormDialog.mobile.test.tsx` como modelo. Evidencia `28-catalogo-hoja-inferior`.
- [ ] 4.17 **REFACTOR fase 3**: extraer el contenedor de alerta compartido entre `PatientFormDialog` y `CatalogFormDialog` si reduce duplicación. Verificación: suite completa en verde, `typecheck` y `lint` en 0.

## 5. Fase 4: desactivar y reactivar en catálogos (escenarios 29-30)

- [ ] 5.1 Agregar `deactivateCatalogItem` y `reactivateCatalogItem` a `catalogosApi.ts` y crear `CatalogConfirmDialog.tsx` sobre `Dialog` ("Volver", "Sí, desactivar", "Sí, reactivar", con el aviso de que los turnos ya dados no cambian). Verificación: se cubre con los escenarios 29 y 30.
- [ ] 5.2 **29 RED/GREEN**: en `features/catalogos/CatalogConfirmDialog.test.tsx`, "Desactivar un sillón exige confirmación interna" ("Volver" no envía nada; "Sí, desactivar" envía `POST /api/chairs/{id}/deactivate`; queda "Inactivo"; "Sillón desactivado."). Evidencia `29-sillon-desactivar`.
- [ ] 5.3 **30 RED/GREEN**: en `CatalogConfirmDialog.test.tsx`, "Reactivar una prestación inactiva" (`POST /api/services/{id}/reactivate`, queda "Activo", "Prestación reactivada."). Evidencia `30-prestacion-reactivar`.
- [ ] 5.4 **REFACTOR fase 4**. Verificación: suite completa en verde, `typecheck` y `lint` en 0.

## 6. Verificación integral, mutaciones y trazabilidad

- [ ] 6.1 Correr la suite completa (línea base + nuevos) y guardarla en `docs/evidencias/test-suite-C-33.txt`. Verificación: 0 fallas.
- [ ] 6.2 Correr `npm run typecheck` y `npm run lint` (`docs/evidencias/tooling-C-33.txt`) y `npm run build` (`docs/evidencias/build-C-33.txt`). Verificación: código de salida 0 en los tres.
- [ ] 6.3 Escribir y correr `docs/evidencias/mutaciones-C-33.py`: una mutación por escenario testeable (M01..M30, o hasta M13 con Plan B), con normalización CRLF/LF y detección de mutantes inválidos (hash sin cambios). Salida en `docs/evidencias/mutaciones-C-33.txt`. Verificación: 0 supervivientes y 0 inválidas.
- [ ] 6.4 Escribir y correr `docs/evidencias/trazabilidad-C-33.py`: escenario → test → mutación con numeración corrida 01..30 y V01..V03, leyendo los `#### Scenario` de las dos specs delta y la tabla "ID → spec → título del escenario" de este archivo. Falla si un escenario no tiene ID, si un ID no corresponde a un escenario real, si hay saltos, si dos escenarios comparten test o si alguno testeable no tiene test. Salida en `docs/evidencias/trazabilidad-C-33.txt`. Verificación: sin errores.
- [ ] 6.5 Guardar `git diff main --diff-filter=M -- 'frontend/**/*.test.ts' 'frontend/**/*.test.tsx'` (con `2>/dev/null`) en `docs/evidencias/diff-tests-existentes-C-33.txt`. Verificación: solo los tests de menú identificados en 1.3; el conteo real de aserciones modificadas por archivo sale de este diff y se declara como desvío en `verify-C-33.md`.
- [ ] 6.6 Correr `openspec validate --all --strict` y guardar la salida en `docs/evidencias/validate-C-33.txt`. Verificación: todo válido.
- [ ] 6.7 Consolidar `docs/evidencias/verify-C-33.md` con resultados, el desvío del menú (conteo real por archivo, tomado del diff de 6.5), el Plan B si se aplicó y las capturas de la sección 7.

## 7. Capturas reales a 1440, 768 y 390 px (a cargo de Claude, no del agente)

- [ ] 7.1 Claude toma capturas a 1440 px de `/pacientes`, `/catalogos` con un ítem inactivo, un formulario con un error 409 y la confirmación de desactivar, en `docs/evidencias/capturas/C-33-*-1440.png`. Verificación: archivos presentes y sin scroll horizontal.
- [ ] 7.2 Claude toma capturas a 768 px de `/pacientes` y `/catalogos`, y de la barra de navegación con los nuevos enlaces, en `docs/evidencias/capturas/C-33-*-768.png`. Verificación: archivos presentes, sin scroll horizontal y la barra en dos renglones como máximo.
- [ ] 7.3 Claude toma capturas a 390 px de `/pacientes` y `/catalogos` con las tablas apiladas, y de los diálogos "Nuevo paciente" y "Nueva prestación" como hoja inferior, en `docs/evidencias/capturas/C-33-*-390.png`. Verificación: sin scroll horizontal de página, `Dialog` como hoja inferior con los botones visibles y datos solo ficticios.

---

## Tabla: Escenario → Test → Mutación

| # | Spec | Requisito | Escenario | Tipo | Archivo de test | Mutación |
|---|---|---|---|---|---|---|
| 01 | `frontend-catalogs-and-patients` | Listado de pacientes | Listado de pacientes con sus cuatro datos | Testeable | `PacientesPage.test.tsx` | M01: no renderizar la columna "Obra social" |
| 02 | `frontend-catalogs-and-patients` | Búsqueda de pacientes en la pantalla | Búsqueda envía la consulta codificada y muestra el resultado | Testeable | `PacientesPage.test.tsx` | M02: enviar `query` sin `encodeURIComponent` |
| 03 | `frontend-catalogs-and-patients` | Búsqueda de pacientes en la pantalla | Búsqueda sin resultados | Testeable | `PacientesPage.test.tsx` | M03: conservar las filas anteriores cuando la respuesta es `[]` |
| 04 | `frontend-catalogs-and-patients` | Listado de pacientes | Error de carga de pacientes con reintento | Testeable | `PacientesPage.test.tsx` | M04: "Reintentar" no vuelve a pedir la lista |
| 05 | `frontend-catalogs-and-patients` | Estilos solo con tokens existentes y superficie clara | Toda variable CSS de las pantallas existe en tokens.css | Testeable | `catalogosPacientesStyles.test.ts` | M05: usar `var(--color-inexistente)` en `PacientesPage.module.css` |
| 06 | `frontend-catalogs-and-patients` | Estilos solo con tokens existentes y superficie clara | Sin tokens de fondo oscuro en las pantallas | Testeable | `catalogosPacientesStyles.test.ts` | M06: usar `var(--color-ice)` en `PacientesPage.module.css` |
| 07 | `frontend-catalogs-and-patients` | Catálogos por sección | Profesionales por defecto con estado en texto | Testeable | `CatalogosPage.test.tsx` | M07: pedir `GET /professionals?active=true` (oculta inactivos) |
| 08 | `frontend-catalogs-and-patients` | Catálogos por sección | Cambio a la sección de prestaciones | Testeable | `CatalogosPage.test.tsx` | M08: ignorar `?seccion=` y quedarse en profesionales |
| 09 | `frontend-catalogs-and-patients` | Título de pantalla con un solo h1 | Pacientes y Catálogos con su título y un único h1 | Testeable | `CatalogosPacientesRoutes.test.tsx` | M09: pasar `title="Turnos Odontología"` a `PageShell` en `CatalogosPage.tsx` |
| 10 | `frontend-catalogs-and-patients` | Diseño adaptable a 1440, 768 y 390 px | Tablas apiladas en celular, controles táctiles y foco visible | Testeable | `catalogosPacientesStyles.test.ts` | M10: quitar el bloque `@media (max-width: 640px)` de la tabla de catálogos |
| 11 | `frontend-foundation` | Navegación de AppShell sin cajas | Catálogos y Pacientes habilitados para los tres roles | Testeable | `AppShellCatalogosPacientes.test.tsx` | M11: sacar `"catalogos"` de `ENABLED_MENU_IDS` |
| 12 | `frontend-foundation` | Navegación de AppShell sin cajas | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Testeable (existente, cambio de requisito) | `AppShellNavigation.test.tsx` | M12: sacar `"pacientes"` de `ENABLED_MENU_IDS` |
| 13 | `frontend-foundation` | Navegación de AppShell sin cajas | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Testeable (existente, cambio de requisito) | `AppShellNavigation.test.tsx` | M13: habilitar también `"turnos"` (desaparece su "Próximamente") |
| 14 | `frontend-catalogs-and-patients` | Alta y edición de pacientes sin datos clínicos | Alta de paciente | Testeable | `PatientFormDialog.test.tsx` | M14: enviar `phone: ""` en vez de `null` |
| 15 | `frontend-catalogs-and-patients` | Alta y edición de pacientes sin datos clínicos | El formulario de paciente tiene solo los cuatro datos mínimos | Testeable | `PatientFormDialog.test.tsx` | M15: agregar un campo "Observaciones" al formulario |
| 16 | `frontend-catalogs-and-patients` | Alta y edición de pacientes sin datos clínicos | Edición de paciente con valores precargados | Testeable | `PatientFormDialog.test.tsx` | M16: no precargar `healthInsurance` al editar |
| 17 | `frontend-catalogs-and-patients` | Errores del backend en los formularios | DNI duplicado muestra el mensaje literal del backend | Testeable | `PatientFormDialog.test.tsx` | M17: marcar `aria-invalid` en DNI ante un 409 |
| 18 | `frontend-catalogs-and-patients` | Errores del backend en los formularios | DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI) | Testeable | `PatientFormDialog.test.tsx` | M18: reemplazar el `message` del 422 por un texto propio ("DNI inválido.") en `PatientFormDialog` |
| 19 | `frontend-catalogs-and-patients` | Errores del backend en los formularios | Error 400 por campo marca el campo con aria-invalid | Testeable | `PatientFormDialog.test.tsx` | M19: omitir `aria-invalid` ante un 400 con `field` |
| 20 | `frontend-catalogs-and-patients` | Acciones visibles según el rol | Odontólogo consulta pacientes en solo lectura | Testeable | `PacientesPage.test.tsx` | M20: incluir `odontologo` entre los roles que ven "Nuevo paciente" |
| 21 | `frontend-catalogs-and-patients` | Un solo mensaje de estado vigente | El mensaje de estado se reemplaza entre acciones sin desmontar la región | Testeable | `PatientFormDialog.test.tsx` | M21: acumular mensajes en vez de reemplazarlos |
| 22 | `frontend-catalogs-and-patients` | Alta y edición de catálogos | Alta de prestación con duración numérica | Testeable | `CatalogFormDialog.test.tsx` | M22: enviar `defaultDurationMin` como string |
| 23 | `frontend-catalogs-and-patients` | Alta y edición de catálogos | Duración no entera no se envía | Testeable | `CatalogFormDialog.test.tsx` | M23: enviar igual con `Number(texto)` sin validar |
| 24 | `frontend-catalogs-and-patients` | Errores del backend en los formularios | Duración inválida muestra el mensaje literal del backend | Testeable | `CatalogFormDialog.test.tsx` | M24: cerrar el diálogo ante un 422 |
| 25 | `frontend-catalogs-and-patients` | Errores del backend en los formularios | Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME) | Testeable | `CatalogFormDialog.test.tsx` | M25: marcar `aria-invalid` en "Nombre" ante un 409 en `CatalogFormDialog` |
| 26 | `frontend-catalogs-and-patients` | Alta y edición de catálogos | Edición de profesional con matrícula vacía | Testeable | `CatalogFormDialog.test.tsx` | M26: enviar `licenseNumber: ""` en vez de `null` |
| 27 | `frontend-catalogs-and-patients` | Acciones visibles según el rol | Recepción y odontólogo consultan catálogos en solo lectura | Testeable | `CatalogosPage.test.tsx` | M27: mostrar acciones de escritura a `recepcion` |
| 28 | `frontend-catalogs-and-patients` | Diseño adaptable a 1440, 768 y 390 px | Formulario de catálogo como hoja inferior en celular | Testeable | `CatalogFormDialog.mobile.test.tsx` | M28: no propagar `isMobile` de `CatalogFormDialog` a `Dialog` |
| 29 | `frontend-catalogs-and-patients` | Desactivar y reactivar con confirmación | Desactivar un sillón exige confirmación interna | Testeable | `CatalogConfirmDialog.test.tsx` | M29: enviar el POST al pulsar "Desactivar", sin confirmar |
| 30 | `frontend-catalogs-and-patients` | Desactivar y reactivar con confirmación | Reactivar una prestación inactiva | Testeable | `CatalogConfirmDialog.test.tsx` | M30: llamar a `/deactivate` en vez de `/reactivate` |
| V01 | `frontend-catalogs-and-patients` | Diseño adaptable a 1440, 768 y 390 px | Pantallas verificadas a 1440, 768 y 390 px | Visual | `C-33-*-{1440,768,390}.png` | V01: scroll horizontal o tabla no apilada en una captura |
| V02 | `frontend-catalogs-and-patients` | Diseño adaptable a 1440, 768 y 390 px | Diálogo como hoja inferior verificado a 390 px | Visual | `C-33-*-dialogo-390.png` | V02: diálogo centrado o botones recortados a 390 px |
| V03 | `frontend-foundation` | Navegación de AppShell sin cajas | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | `C-33-appshell-{768,390}.png` | V03: la barra supera dos renglones a 768 px con los enlaces nuevos |

Conteo: 28 tests nuevos (01-11 y 14-30) y 2 tests existentes con cambio de requisito (12 y 13). Las aserciones de `menuFor.test.ts`, `AppShell.test.tsx` y los demás tests de menú afectados no son escenarios propios: su conteo real por archivo sale del `git diff` del apply (tarea 6.5) y se declara como desvío en `verify-C-33.md`. Con Plan B: 11 tests nuevos (01-11), 12-13 y V01/V03 sobre lo entregado.

---

## Tabla: ID → spec → título del escenario

Cada `#### Scenario` de las dos specs delta tiene exactamente un ID, y cada ID corresponde a un escenario real. Numeración corrida, sin saltos: 01..30 testeables y V01..V03 visuales. Totales: `frontend-catalogs-and-patients` 29 escenarios (27 testeables y 2 visuales); `frontend-foundation` 4 escenarios (3 testeables y 1 visual).

| ID | Spec | Título del escenario |
|---|---|---|
| 01 | `frontend-catalogs-and-patients` | Listado de pacientes con sus cuatro datos |
| 02 | `frontend-catalogs-and-patients` | Búsqueda envía la consulta codificada y muestra el resultado |
| 03 | `frontend-catalogs-and-patients` | Búsqueda sin resultados |
| 04 | `frontend-catalogs-and-patients` | Error de carga de pacientes con reintento |
| 05 | `frontend-catalogs-and-patients` | Toda variable CSS de las pantallas existe en tokens.css |
| 06 | `frontend-catalogs-and-patients` | Sin tokens de fondo oscuro en las pantallas |
| 07 | `frontend-catalogs-and-patients` | Profesionales por defecto con estado en texto |
| 08 | `frontend-catalogs-and-patients` | Cambio a la sección de prestaciones |
| 09 | `frontend-catalogs-and-patients` | Pacientes y Catálogos con su título y un único h1 |
| 10 | `frontend-catalogs-and-patients` | Tablas apiladas en celular, controles táctiles y foco visible |
| 11 | `frontend-foundation` | Catálogos y Pacientes habilitados para los tres roles |
| 12 | `frontend-foundation` | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px |
| 13 | `frontend-foundation` | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad |
| 14 | `frontend-catalogs-and-patients` | Alta de paciente |
| 15 | `frontend-catalogs-and-patients` | El formulario de paciente tiene solo los cuatro datos mínimos |
| 16 | `frontend-catalogs-and-patients` | Edición de paciente con valores precargados |
| 17 | `frontend-catalogs-and-patients` | DNI duplicado muestra el mensaje literal del backend |
| 18 | `frontend-catalogs-and-patients` | DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI) |
| 19 | `frontend-catalogs-and-patients` | Error 400 por campo marca el campo con aria-invalid |
| 20 | `frontend-catalogs-and-patients` | Odontólogo consulta pacientes en solo lectura |
| 21 | `frontend-catalogs-and-patients` | El mensaje de estado se reemplaza entre acciones sin desmontar la región |
| 22 | `frontend-catalogs-and-patients` | Alta de prestación con duración numérica |
| 23 | `frontend-catalogs-and-patients` | Duración no entera no se envía |
| 24 | `frontend-catalogs-and-patients` | Duración inválida muestra el mensaje literal del backend |
| 25 | `frontend-catalogs-and-patients` | Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME) |
| 26 | `frontend-catalogs-and-patients` | Edición de profesional con matrícula vacía |
| 27 | `frontend-catalogs-and-patients` | Recepción y odontólogo consultan catálogos en solo lectura |
| 28 | `frontend-catalogs-and-patients` | Formulario de catálogo como hoja inferior en celular |
| 29 | `frontend-catalogs-and-patients` | Desactivar un sillón exige confirmación interna |
| 30 | `frontend-catalogs-and-patients` | Reactivar una prestación inactiva |
| V01 | `frontend-catalogs-and-patients` | Pantallas verificadas a 1440, 768 y 390 px |
| V02 | `frontend-catalogs-and-patients` | Diálogo como hoja inferior verificado a 390 px |
| V03 | `frontend-foundation` | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) |

---

## Workflow follow-up

- Después del apply y la verificación, archivar con `/opsx:archive ui-catalogos-y-pacientes` y marcar `[x]` en `CHANGES.md` para C-33.
- Si se aplicó el Plan B, reducir antes del archive el delta de `frontend-catalogs-and-patients` a los requisitos cubiertos (design.md D2).
