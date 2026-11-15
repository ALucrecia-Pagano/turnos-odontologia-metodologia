# Verificación de C-33 — ui-catalogos-y-pacientes

## Resultado

Todos los números provienen de ejecuciones reales y de los archivos de evidencia enlazados (texto plano UTF-8).

- **Tareas**: Fases 1 a 6, Fase 7 (15 capturas visuales multi-resolución a 1440 px, 768 px y 390 px a cargo de Claude con Playwright contra la API real en [capturas/](capturas/)) y Fase 8 implementadas y verificadas según [tasks.md](../../openspec/changes/ui-catalogos-y-pacientes/tasks.md).
- **Plan B**: No se aplicó. Se completaron íntegramente las Fases 1 a 4 sin recortes de alcance.
- **Línea base unificada**: [baseline-C-33.txt](baseline-C-33.txt) (82 archivos de test, 321 tests pasados, exit 0).
- **Vitest**: Suite final con todos los tests en verde ([test-suite-C-33.txt](test-suite-C-33.txt)): **93 archivos de test pasados (353 tests en total: 321 heredados + 32 tests nuevos de C-33)**. En el conteo se distinguen **32 tests nuevos** y **2 tests existentes modificados (12 y 13)**, distribuidos en 11 archivos dedicados (`PacientesPage.test.tsx` [6], `PatientFormDialog.test.tsx` [7], `CatalogosPage.test.tsx` [3], `CatalogFormDialog.test.tsx` [5], `CatalogFormDialog.mobile.test.tsx` [1], `CatalogConfirmDialog.test.tsx` [2], `CatalogosPacientesRoutes.test.tsx` [1], `catalogosPacientesStyles.test.ts` [4], `AppShellCatalogosPacientes.test.tsx` [1], `DialogModalCard.test.tsx` [1], `TableActionsHeader.test.tsx` [1]), más las aserciones de menú adaptadas en `AppShellNavigation.test.tsx`. Cada escenario testeable cuenta con su par RED/GREEN en `red-C-33/` (`01`..`34`) y `green-C-33/` (`01`..`34`).
- **Mutaciones**: **34 de 34 mutaciones eliminadas** (`M01`–`M34`: 32 tests nuevos y 2 tests existentes modificados [12 y 13]) por aserción; 0 supervivientes; 0 inválidas; **SHA-256 inicial: 14ee465f9447e6eefdbe8f2f9b94a683dedebd2b5fe6fd791ed7c39a11480e00**, **SHA-256 final: 14ee465f9447e6eefdbe8f2f9b94a683dedebd2b5fe6fd791ed7c39a11480e00**, **SHA-256 sin cambios: sí** ([mutaciones-C-33.txt](mutaciones-C-33.txt), generado por [mutaciones-C-33.py](mutaciones-C-33.py)).
- **Trazabilidad**: **37 escenarios** declarados en las specs delta (34 testeables 1:1 numerados de corrido `01`..`34` [32 tests nuevos y 2 tests existentes modificados (12 y 13)] + 3 visuales `V01`, `V02`, `V03` con sus capturas enlazadas), 0 inconsistencias, 0 tests compartidos ([trazabilidad-C-33.txt](trazabilidad-C-33.txt), generado por [trazabilidad-C-33.py](trazabilidad-C-33.py)).
- **Calidad y Tooling**:
  - `npm run typecheck` exit 0 (0 errores de tipos).
  - `npx eslint src/features/pacientes src/features/catalogos src/features/auth/menuFor.ts src/shared/components/AppShellNavigation.test.tsx src/shared/components/AppShellCatalogosPacientes.test.tsx` exit 0 (0 errores, 0 warnings en archivos de C-33; ver [tooling-C-33.txt](tooling-C-33.txt)).
  - `npm run lint` (`eslint . --max-warnings 0`) sale con código 1 debido a 3 warnings preexistentes heredadas de C-29/C-30 en `AppointmentFormDialog.tsx:36` y `Dialog.tsx:98,101`, documentadas en Desvíos y respetadas sin modificación.
  - `npm run build` exit 0 ([build-C-33.txt](build-C-33.txt)).
- **OpenSpec**: `openspec validate --all --strict` exit 0 (19 passed, 0 failed; ver [validate-C-33.txt](validate-C-33.txt)).
- **Diff de tests existentes**: [diff-tests-existentes-C-33.txt](diff-tests-existentes-C-33.txt) (generado con `2>/dev/null` sin warnings) muestra únicamente las **11 aserciones en 3 archivos** (`menuFor.test.ts`: 4, `AppShell.test.tsx`: 4, `AppShellNavigation.test.tsx`: 3) autorizadas por la habilitación de Catálogos y Pacientes en el menú.
- **Skill y MCP**: Consultada la skill `appointment-frontend-ux` para tokens de diseño en `tokens.css`, accesibilidad (`StatusBadge` con texto visible, foco visible con `outline-offset`, región de estado único sin desmontar), y respeto de la zona horaria de la API.

---

## Matriz Escenario → Test → Evidencias → Mutación

<!-- trazabilidad:inicio -->
| # | Spec | Escenario | Tipo | Archivo de test | Test | Evidencia RED | Evidencia GREEN | Mutación |
|---|---|---|---|---|---|---|---|---|
| 01 | `frontend-catalogs-and-patients` | Listado de pacientes con sus cuatro datos | Testeable | `PacientesPage.test.tsx` | `Listado de pacientes con sus cuatro datos` | `01-pacientes-listado.txt` | `01-pacientes-listado.txt` | `M01` |
| 02 | `frontend-catalogs-and-patients` | Búsqueda envía la consulta codificada y muestra el resultado | Testeable | `PacientesPage.test.tsx` | `Búsqueda envía la consulta codificada y muestra el resultado` | `02-pacientes-busqueda.txt` | `02-pacientes-busqueda.txt` | `M02` |
| 03 | `frontend-catalogs-and-patients` | Búsqueda sin resultados | Testeable | `PacientesPage.test.tsx` | `Búsqueda sin resultados` | `03-pacientes-sin-resultados.txt` | `03-pacientes-sin-resultados.txt` | `M03` |
| 04 | `frontend-catalogs-and-patients` | Error de carga de pacientes con reintento | Testeable | `PacientesPage.test.tsx` | `Error de carga de pacientes con reintento` | `04-pacientes-reintento.txt` | `04-pacientes-reintento.txt` | `M04` |
| 05 | `frontend-catalogs-and-patients` | Toda variable CSS de las pantallas existe en tokens.css | Testeable | `catalogosPacientesStyles.test.ts` | `Toda variable CSS de las pantallas existe en tokens.css` | `05-css-tokens-existen.txt` | `05-css-tokens-existen.txt` | `M05` |
| 06 | `frontend-catalogs-and-patients` | Sin tokens de fondo oscuro en las pantallas | Testeable | `catalogosPacientesStyles.test.ts` | `Sin tokens de fondo oscuro en las pantallas` | `06-css-superficie-clara.txt` | `06-css-superficie-clara.txt` | `M06` |
| 07 | `frontend-catalogs-and-patients` | Profesionales por defecto con estado en texto | Testeable | `CatalogosPage.test.tsx` | `Profesionales por defecto con estado en texto` | `07-catalogos-profesionales-defecto.txt` | `07-catalogos-profesionales-defecto.txt` | `M07` |
| 08 | `frontend-catalogs-and-patients` | Cambio a la sección de prestaciones | Testeable | `CatalogosPage.test.tsx` | `Cambio a la sección de prestaciones` | `08-catalogos-cambio-seccion.txt` | `08-catalogos-cambio-seccion.txt` | `M08` |
| 09 | `frontend-catalogs-and-patients` | Pacientes y Catálogos con su título y un único h1 | Testeable | `CatalogosPacientesRoutes.test.tsx` | `Pacientes y Catálogos con su título y un único h1` | `09-titulo-h1.txt` | `09-titulo-h1.txt` | `M09` |
| 10 | `frontend-catalogs-and-patients` | Tablas apiladas en celular, controles táctiles y foco visible | Testeable | `catalogosPacientesStyles.test.ts` | `Tablas apiladas en celular, controles táctiles y foco visible` | `10-css-tablas-adaptables.txt` | `10-css-tablas-adaptables.txt` | `M10` |
| 11 | `frontend-foundation` | Catálogos y Pacientes habilitados para los tres roles | Testeable | `AppShellCatalogosPacientes.test.tsx` | `Catálogos y Pacientes habilitados para los tres roles` | `11-menu-habilitado.txt` | `11-menu-habilitado.txt` | `M11` |
| 12 | `frontend-foundation` | Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px | Testeable | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | `12-13-menu-existentes.txt` | `12-13-menu-existentes.txt` | `M12` |
| 13 | `frontend-foundation` | Ítems deshabilitados con Próximamente conservan semántica y accesibilidad | Testeable | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | `12-13-menu-existentes.txt` | `12-13-menu-existentes.txt` | `M13` |
| 14 | `frontend-catalogs-and-patients` | Alta de paciente | Testeable | `PatientFormDialog.test.tsx` | `Alta de paciente` | `14-paciente-alta.txt` | `14-paciente-alta.txt` | `M14` |
| 15 | `frontend-catalogs-and-patients` | El formulario de paciente tiene solo los cuatro datos mínimos | Testeable | `PatientFormDialog.test.tsx` | `El formulario de paciente tiene solo los cuatro datos mínimos` | `15-paciente-cuatro-campos.txt` | `15-paciente-cuatro-campos.txt` | `M15` |
| 16 | `frontend-catalogs-and-patients` | Edición de paciente con valores precargados | Testeable | `PatientFormDialog.test.tsx` | `Edición de paciente con valores precargados` | `16-paciente-edicion.txt` | `16-paciente-edicion.txt` | `M16` |
| 17 | `frontend-catalogs-and-patients` | DNI duplicado muestra el mensaje literal del backend | Testeable | `PatientFormDialog.test.tsx` | `DNI duplicado muestra el mensaje literal del backend` | `17-paciente-dni-duplicado.txt` | `17-paciente-dni-duplicado.txt` | `M17` |
| 18 | `frontend-catalogs-and-patients` | DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI) | Testeable | `PatientFormDialog.test.tsx` | `DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)` | `18-paciente-dni-invalido.txt` | `18-paciente-dni-invalido.txt` | `M18` |
| 19 | `frontend-catalogs-and-patients` | Error 400 por campo marca el campo con aria-invalid | Testeable | `PatientFormDialog.test.tsx` | `Error 400 por campo marca el campo con aria-invalid` | `19-paciente-400-campo.txt` | `19-paciente-400-campo.txt` | `M19` |
| 20 | `frontend-catalogs-and-patients` | Odontólogo consulta pacientes en solo lectura | Testeable | `PacientesPage.test.tsx` | `Odontólogo consulta pacientes en solo lectura` | `20-pacientes-odontologo-lectura.txt` | `20-pacientes-odontologo-lectura.txt` | `M20` |
| 21 | `frontend-catalogs-and-patients` | El mensaje de estado se reemplaza entre acciones sin desmontar la región | Testeable | `PatientFormDialog.test.tsx` | `El mensaje de estado se reemplaza entre acciones sin desmontar la región` | `21-status-unico.txt` | `21-status-unico.txt` | `M21` |
| 22 | `frontend-catalogs-and-patients` | Alta de prestación con duración numérica | Testeable | `CatalogFormDialog.test.tsx` | `Alta de prestación con duración numérica` | `22-prestacion-alta.txt` | `22-prestacion-alta.txt` | `M22` |
| 23 | `frontend-catalogs-and-patients` | Duración no entera no se envía | Testeable | `CatalogFormDialog.test.tsx` | `Duración no entera no se envía` | `23-duracion-no-entera.txt` | `23-duracion-no-entera.txt` | `M23` |
| 24 | `frontend-catalogs-and-patients` | Duración inválida muestra el mensaje literal del backend | Testeable | `CatalogFormDialog.test.tsx` | `Duración inválida muestra el mensaje literal del backend` | `24-duracion-422.txt` | `24-duracion-422.txt` | `M24` |
| 25 | `frontend-catalogs-and-patients` | Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME) | Testeable | `CatalogFormDialog.test.tsx` | `Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)` | `25-catalogo-nombre-duplicado.txt` | `25-catalogo-nombre-duplicado.txt` | `M25` |
| 26 | `frontend-catalogs-and-patients` | Edición de profesional con matrícula vacía | Testeable | `CatalogFormDialog.test.tsx` | `Edición de profesional con matrícula vacía` | `26-profesional-edicion.txt` | `26-profesional-edicion.txt` | `M26` |
| 27 | `frontend-catalogs-and-patients` | Recepción y odontólogo consultan catálogos en solo lectura | Testeable | `CatalogosPage.test.tsx` | `Recepción y odontólogo consultan catálogos en solo lectura` | `27-catalogos-solo-lectura.txt` | `27-catalogos-solo-lectura.txt` | `M27` |
| 28 | `frontend-catalogs-and-patients` | Formulario de catálogo como hoja inferior en celular | Testeable | `CatalogFormDialog.mobile.test.tsx` | `Formulario de catálogo como hoja inferior en celular` | `28-catalogo-hoja-inferior.txt` | `28-catalogo-hoja-inferior.txt` | `M28` |
| 29 | `frontend-catalogs-and-patients` | Desactivar un sillón exige confirmación interna | Testeable | `CatalogConfirmDialog.test.tsx` | `Desactivar un sillón exige confirmación interna` | `29-sillon-desactivar.txt` | `29-sillon-desactivar.txt` | `M29` |
| 30 | `frontend-catalogs-and-patients` | Reactivar una prestación inactiva | Testeable | `CatalogConfirmDialog.test.tsx` | `Reactivar una prestación inactiva` | `30-prestacion-reactivar.txt` | `30-prestacion-reactivar.txt` | `M30` |
| 31 | `frontend-catalogs-and-patients` | Los tres diálogos muestran su contenido en una tarjeta | Testeable | `DialogModalCard.test.tsx` | `Los tres diálogos muestran su contenido en una tarjeta` | `31-dialogo-tarjeta.txt` | `31-dialogo-tarjeta.txt` | `M31` |
| 32 | `frontend-catalogs-and-patients` | Las tablas tienen encabezado para la columna de acciones | Testeable | `TableActionsHeader.test.tsx` | `Las tablas tienen encabezado para la columna de acciones` | `32-tablas-header-acciones.txt` | `32-tablas-header-acciones.txt` | `M32` |
| 33 | `frontend-catalogs-and-patients` | Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible | Testeable | `catalogosPacientesStyles.test.ts` | `Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible` | `33-tabla-apilada-caption-thead.txt` | `33-tabla-apilada-caption-thead.txt` | `M33` |
| 34 | `frontend-catalogs-and-patients` | Búsqueda sin resultados muestra un único mensaje | Testeable | `PacientesPage.test.tsx` | `Búsqueda sin resultados muestra un único mensaje` | `34-pacientes-busqueda-mensaje-unico.txt` | `34-pacientes-busqueda-mensaje-unico.txt` | `M34` |
| V01 | `frontend-catalogs-and-patients` | Pantallas verificadas a 1440, 768 y 390 px | Visual | [C-33-pacientes-1440.png](capturas/C-33-pacientes-1440.png), [C-33-paciente-editado-1440.png](capturas/C-33-paciente-editado-1440.png), [C-33-paciente-409-1440.png](capturas/C-33-paciente-409-1440.png), [C-33-paciente-422-1440.png](capturas/C-33-paciente-422-1440.png), [C-33-prestacion-409-1440.png](capturas/C-33-prestacion-409-1440.png), [C-33-sillon-confirmar-1440.png](capturas/C-33-sillon-confirmar-1440.png), [C-33-catalogos-inactivo-1440.png](capturas/C-33-catalogos-inactivo-1440.png), [C-33-pacientes-768.png](capturas/C-33-pacientes-768.png), [C-33-catalogos-768.png](capturas/C-33-catalogos-768.png), [C-33-pacientes-390.png](capturas/C-33-pacientes-390.png), [C-33-catalogos-390.png](capturas/C-33-catalogos-390.png) | — | — | — | — |
| V02 | `frontend-catalogs-and-patients` | Diálogo como hoja inferior verificado a 390 px | Visual | [C-33-paciente-dialogo-390.png](capturas/C-33-paciente-dialogo-390.png), [C-33-prestacion-dialogo-390.png](capturas/C-33-prestacion-dialogo-390.png) | — | — | — | — |
| V03 | `frontend-foundation` | Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px) | Visual | [C-33-appshell-768.png](capturas/C-33-appshell-768.png), [C-33-appshell-390.png](capturas/C-33-appshell-390.png) | — | — | — | — |
<!-- trazabilidad:fin -->

---

## Tabla de Mutaciones (M01–M30)

<!-- mutaciones:inicio -->
| ID | Archivo de test | Test | Estado | Mensaje de fallo |
|---|---|---|---|---|
| M01 | `PacientesPage.test.tsx` | `Listado de pacientes con sus cuatro datos` | Matada | `AssertionError: expected [ 'Nombre', 'DNI', 'Teléfono', …(1) ] to deeply equal [ 'Nombre', 'DNI', 'Teléfono', …(2) ]` |
| M02 | `PacientesPage.test.tsx` | `Búsqueda envía la consulta codificada y muestra el resultado` | Matada | `AssertionError: expected [ …(3) ] to include 'http://localhost:8000/api/patients?qu…'` |
| M03 | `PacientesPage.test.tsx` | `Búsqueda sin resultados` | Matada | `Error: expect(received).toBeInTheDocument()` |
| M04 | `PacientesPage.test.tsx` | `Error de carga de pacientes con reintento` | Matada | `Error: expect(received).toBeInTheDocument()` |
| M05 | `catalogosPacientesStyles.test.ts` | `Toda variable CSS de las pantallas existe en tokens.css` | Matada | `AssertionError: expected [ Array(1) ] to deeply equal []` |
| M06 | `catalogosPacientesStyles.test.ts` | `Sin tokens de fondo oscuro en las pantallas` | Matada | `AssertionError: expected [ Array(1) ] to deeply equal []` |
| M07 | `CatalogosPage.test.tsx` | `Profesionales por defecto con estado en texto` | Matada | `AssertionError: expected [ …(2) ] to include 'http://localhost:8000/api/professiona…'` |
| M08 | `CatalogosPage.test.tsx` | `Cambio a la sección de prestaciones` | Matada | `AssertionError: expected [ …(2) ] to include 'http://localhost:8000/api/services'` |
| M09 | `CatalogosPacientesRoutes.test.tsx` | `Pacientes y Catálogos con su título y un único h1` | Matada | `Error: expect(element).toHaveTextContent()` |
| M10 | `catalogosPacientesStyles.test.ts` | `Tablas apiladas en celular, controles táctiles y foco visible` | Matada | `AssertionError: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\frontend\src\features\catalogos\CatalogosPage.module.css debe tener media query a 640px: expected '.page {\n  width: 100%;\n  box-sizing…' to match /@media\s*\(\s*max-width\s*:\s*640px\s…/` |
| M11 | `AppShellCatalogosPacientes.test.tsx` | `Catálogos y Pacientes habilitados para los tres roles` | Matada | `AssertionError: Catálogos debe ser un enlace para administrador: expected null not to be null` |
| M12 | `AppShellNavigation.test.tsx` | `enlaces de navegación activos y bloque de sesión en misma línea en 1440 px` | Matada | `AssertionError: expected [ <a …(4)></a>, <a …(3)></a>, …(1) ] to have a length of 4 but got 3` |
| M13 | `AppShellNavigation.test.tsx` | `ítems deshabilitados con Próximamente conservan semántica y accesibilidad` | Matada | `AssertionError: expected [ …(1) ] to have a length of 2 but got 1` |
| M14 | `PatientFormDialog.test.tsx` | `Alta de paciente` | Matada | `AssertionError: expected { fullName: 'Carla Medina', …(3) } to deeply equal { fullName: 'Carla Medina', …(3) }` |
| M15 | `PatientFormDialog.test.tsx` | `El formulario de paciente tiene solo los cuatro datos mínimos` | Matada | `AssertionError: expected <input …(5)></input>` |
| M16 | `PatientFormDialog.test.tsx` | `Edición de paciente con valores precargados` | Matada | `Error: expect(element).toHaveValue(OSDE)` |
| M17 | `PatientFormDialog.test.tsx` | `DNI duplicado muestra el mensaje literal del backend` | Matada | `Error: expect(element).not.toHaveAttribute("aria-invalid") // element.hasAttribute("aria-invalid")` |
| M18 | `PatientFormDialog.test.tsx` | `DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)` | Matada | `Error: expect(element).toHaveTextContent()` |
| M19 | `PatientFormDialog.test.tsx` | `Error 400 por campo marca el campo con aria-invalid` | Matada | `Error: expect(element).toHaveAttribute("aria-invalid", "true") // element.getAttribute("aria-invalid") === "true"` |
| M20 | `PacientesPage.test.tsx` | `Odontólogo consulta pacientes en solo lectura` | Matada | `Error: expect(element).not.toBeInTheDocument()` |
| M21 | `PatientFormDialog.test.tsx` | `El mensaje de estado se reemplaza entre acciones sin desmontar la región` | Matada | `AssertionError: expected 'Paciente creado. Paciente actualizado.' to be 'Paciente actualizado.' // Object.is equality` |
| M22 | `CatalogFormDialog.test.tsx` | `Alta de prestación con duración numérica` | Matada | `AssertionError: expected { name: 'Extracción', …(1) } to deeply equal { name: 'Extracción', …(1) }` |
| M23 | `CatalogFormDialog.test.tsx` | `Duración no entera no se envía` | Matada | `AssertionError: expected true to be false // Object.is equality` |
| M24 | `CatalogFormDialog.test.tsx` | `Duración inválida muestra el mensaje literal del backend` | Matada | `Error: expect(received).toBeInTheDocument()` |
| M25 | `CatalogFormDialog.test.tsx` | `Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)` | Matada | `Error: expect(element).not.toHaveAttribute("aria-invalid", "true") // element.getAttribute("aria-invalid") === "true"` |
| M26 | `CatalogFormDialog.test.tsx` | `Edición de profesional con matrícula vacía` | Matada | `AssertionError: expected { Object (fullName, licenseNumber) } to deeply equal { Object (fullName, licenseNumber) }` |
| M27 | `CatalogosPage.test.tsx` | `Recepción y odontólogo consultan catálogos en solo lectura` | Matada | `Error: expect(received).toBeInTheDocument()` |
| M28 | `CatalogFormDialog.mobile.test.tsx` | `Formulario de catálogo como hoja inferior en celular` | Matada | `Error: expect(element).toHaveAttribute("data-mobile-sheet", "true") // element.getAttribute("data-mobile-sheet") === "true"` |
| M29 | `CatalogConfirmDialog.test.tsx` | `Desactivar un sillón exige confirmación interna` | Matada | `AssertionError: expected 1 to be +0 // Object.is equality` |
| M30 | `CatalogConfirmDialog.test.tsx` | `Reactivar una prestación inactiva` | Matada | `Error: expect(element).not.toBeInTheDocument()` |
| M31 | `DialogModalCard.test.tsx` | `Los tres diálogos muestran su contenido en una tarjeta` | Matada | `AssertionError: PatientFormDialog debe contener un elemento con [data-modal-card]: expected null not to be null` |
| M32 | `TableActionsHeader.test.tsx` | `Las tablas tienen encabezado para la columna de acciones` | Matada | `AssertionError: La tabla de catálogos debe incluir encabezado Acciones: expected [ 'Nombre', 'Matrícula', 'Estado' ] to include 'Acciones'` |
| M33 | `catalogosPacientesStyles.test.ts` | `Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible` | Matada | `AssertionError: C:\Users\hp\METODOLOGIA_TPS\turnos-odontologia\frontend\src\features\pacientes\PacientesPage.module.css debe ocultar thead de forma accesible con position: absolute: expected '.page {\n  width: 100%;\n  box-sizing…' to match /thead[\s\S]*?position:\s*absolute/` |
| M34 | `PacientesPage.test.tsx` | `Búsqueda sin resultados muestra un único mensaje` | Matada | `Error: expect(element).not.toBeInTheDocument()` |
<!-- mutaciones:fin -->

---

## Desvíos y Hallazgos Analizados

1. **Habilitación de Catálogos y Pacientes en el menú de navegación (11 aserciones modificadas en 3 archivos)**:
   - *Causa*: En C-25, C-32 y C-35, las pruebas `menuFor.test.ts`, `AppShell.test.tsx` y `AppShellNavigation.test.tsx` verificaban que los ítems `"Catálogos"` y `"Pacientes"` estuvieran deshabilitados (`disabled: true`) con el badge `"Próximamente"`. Al implementarse y habilitarse ambos módulos en C-33 para los tres roles (`administrador`, `recepcion`, `odontologo`), dichas aserciones se actualizaron para reflejar el estado activo hacia `/catalogos` y `/pacientes`.
   - *Conteo real por archivo (extraído de `diff-tests-existentes-C-33.txt`)*:
     - `frontend/src/features/auth/menuFor.test.ts` (**4 aserciones**): líneas 19–20 (2 aserciones para `administrador`), línea 35 (1 aserción para `recepcion`) y línea 52 (1 aserción para `odontologo`), verificando que `"horarios-y-bloqueos"`, `"catalogos"` y `"pacientes"` tengan `disabled: false`, sus rutas correspondientes y `badge: null`.
     - `frontend/src/shared/components/AppShell.test.tsx` (**4 aserciones**): líneas 65–72 (2 aserciones en `adminButtons`, que pasa a longitud 2: `["Turnos", "Usuarios y roles"]`), línea 99–102 (1 aserción en `recepcionNav`, que pasa a `["Turnos"]`) y líneas 123–127 (1 aserción en `odontologoNav`, que pasa a `[]`).
     - `frontend/src/shared/components/AppShellNavigation.test.tsx` (**3 aserciones**): línea 56 (1 aserción: `queryAllByRole("link")` pasa a longitud 4) — escenario 12; líneas 77 y 81–84 (2 aserciones: botones con `Próximamente` pasa a longitud 2: `["Turnos", "Usuarios y roles"]`) — escenario 13.
     - `frontend/src/shared/components/AppShell.mobile.test.tsx`: **0 aserciones modificadas**.

2. **Advertencias preexistentes de ESLint en `npm run lint`**:
   - *Causa*: Existen 3 advertencias preexistentes heredadas de C-29 y C-30 (`AppointmentFormDialog.tsx:36` por `react-refresh/only-export-components`, y `Dialog.tsx:98,101` por `react-hooks/exhaustive-deps` en `returnFocusRef`). Como `package.json` define `"lint": "eslint . --max-warnings 0"`, `npm run lint` devuelve código 1 por esas 3 advertencias ajenas a C-33. En contraste, `npx eslint` sobre todos los archivos creados o modificados por C-33 finaliza con 0 errores y 0 advertencias.
   - *Resolución*: Se mantienen intactas las líneas preexistentes cumpliendo la regla de no alterar código fuera del scope.

3. **Sección 7 (Capturas visuales reales a 1440, 768 y 390 px)**:
   - *Estado*: Las tareas 7.1, 7.2 y 7.3 fueron completadas por Claude mediante Playwright contra la API backend en ejecución (`[x]` en `tasks.md`), generando las 15 capturas en `docs/evidencias/capturas/C-33-*.png`.

---

## Corrección post-verificación

Tras la verificación con la API real, se identificaron y corrigieron cuatro aspectos mediante Strict TDD (escenarios 31 a 34, mutaciones `M31` a `M34`):

- **A) Tarjeta contenedora en los tres diálogos (`PatientFormDialog`, `CatalogFormDialog`, `CatalogConfirmDialog`)**:
  - *Causa*: El componente compartido `Dialog` actúa únicamente como primitivo modal (`<dialog>`), sin aportar superficie ni fondo visual. Cada feature debe envolver su contenido en una tarjeta (`data-modal-card="<nombre>"` y `.modalContent`). Al faltar este contenedor, los tres modales ocupaban todo el ancho sobre el fondo sin borde, radio ni padding, y a 390 px no se manifestaba visualmente la hoja inferior.
  - *Solución*: Siguiendo el patrón de `BlockFormDialog.tsx`, se extrajo la tarjeta compartida a `frontend/src/features/catalogos/modalCard.module.css` (con fondo `--surface-ivory-ice`, borde `--color-border`, sombra `--shadow-md`, `max-width: 520px` y hoja inferior en `@media (max-width: 640px)`). Los tres diálogos envuelven ahora su formulario/contenido con `data-modal-card="patient-form"`, `data-modal-card="catalog-form"` y `data-modal-card="catalog-confirm"`.
  - *Evidencia*: Escenario 31 (`31-dialogo-tarjeta.txt`, `DialogModalCard.test.tsx`, mutación `M31`).

- **B) Encabezado para la columna de acciones en tablas de pacientes y catálogos**:
  - *Causa*: Las tablas generaban `<td data-label="Acciones">` para cada fila con botones de acción ("Editar", "Desactivar", "Reactivar"), pero el `<thead>` carecía del `<th scope="col">` correspondiente. El encabezado gris se cortaba antes de la última columna.
  - *Solución*: Se agregó `<th scope="col" className={styles.th}>Acciones</th>` condicionado a los permisos de edición (`canEdit` en pacientes, `isAdmin` en catálogos), garantizando que el encabezado cubra la totalidad de las columnas.
  - *Evidencia*: Escenario 32 (`32-tablas-header-acciones.txt`, `TableActionsHeader.test.tsx`, mutación `M32`).

- **C) Tabla apilada en celular con caption a ancho completo y thead oculto de forma accesible**:
  - *Causa*: En viewport móvil (390 px), el `<caption>` de la tabla se comprimía en una columna angosta de tres renglones por no tener `display: block; width: 100%`, mientras que el `<thead>` se ocultaba con `display: none` perdiendo semántica accesible y dejando líneas sueltas de bordes.
  - *Solución*: En el bloque `@media (max-width: 640px)` de `PacientesPage.module.css` y `CatalogosPage.module.css`, la clase `.caption` declara `display: block; width: 100%; box-sizing: border-box;`, y `thead` se oculta mediante el patrón estándar visually-hidden (`position: absolute; width: 1px; height: 1px; clip: rect(0, 0, 0, 0); overflow: hidden; border: 0`).
  - *Evidencia*: Escenario 33 (`33-tabla-apilada-caption-thead.txt`, `catalogosPacientesStyles.test.ts`, mutación `M33`).

- **D) Búsqueda de pacientes sin resultados con mensaje único**:
  - *Causa*: Al buscar un paciente sin coincidencias, la pantalla renderizaba simultáneamente el título "No se encontraron pacientes." y la descripción secundaria "No hay resultados para la búsqueda realizada.", contraviniendo el texto exacto de la spec.
  - *Solución*: En `PacientesPage.tsx`, cuando la búsqueda no arroja resultados (`activeQuery` activo y lista vacía), se omite la descripción secundaria en `EmptyState`, mostrando única y exclusivamente el mensaje "No se encontraron pacientes.".
  - *Evidencia*: Escenario 34 (`34-pacientes-busqueda-mensaje-unico.txt`, `PacientesPage.test.tsx`, mutación `M34`).

---

## Verificación visual en navegador real (Claude / Playwright)

Verificación visual e interactiva realizada sobre Chromium real contra la API backend en ejecución, documentada en las 15 capturas de [docs/evidencias/capturas/](capturas/):

1. `C-33-pacientes-1440.png`: Desktop (1440 px) con listado de pacientes, barra de búsqueda y botón "Nuevo paciente".
2. `C-33-paciente-editado-1440.png`: Desktop (1440 px) con formulario de edición de paciente con datos precargados.
3. `C-33-paciente-409-1440.png`: Desktop (1440 px) con rechazo por DNI duplicado mostrando el mensaje literal del backend en alerta accesible.
4. `C-33-paciente-422-1440.png`: Desktop (1440 px) con rechazo por DNI inválido (422) mostrando el mensaje literal del backend.
5. `C-33-prestacion-409-1440.png`: Desktop (1440 px) con rechazo por nombre duplicado en el catálogo de prestaciones (409) mostrando mensaje literal del backend.
6. `C-33-sillon-confirmar-1440.png`: Desktop (1440 px) con diálogo de confirmación interna para desactivar un sillón.
7. `C-33-catalogos-inactivo-1440.png`: Desktop (1440 px) con catálogo mostrando ítem con estado "Inactivo" en texto visible y botón de reactivación.
8. `C-33-pacientes-768.png`: Tablet (768 px) con listado de pacientes adaptado sin scroll horizontal.
9. `C-33-catalogos-768.png`: Tablet (768 px) con vista de catálogos y pestañas de sección adaptadas a tablet.
10. `C-33-appshell-768.png`: Tablet (768 px) con barra de navegación de AppShell mostrando enlaces activos a "Catálogos" y "Pacientes" en dos renglones como máximo.
11. `C-33-pacientes-390.png`: Celular (390 px) con tabla apilada verticalmente, caption a todo el ancho y thead oculto accesible, sin scroll horizontal.
12. `C-33-catalogos-390.png`: Celular (390 px) con tabla de catálogo apilada verticalmente con foco visible y controles táctiles, sin scroll horizontal.
13. `C-33-appshell-390.png`: Celular (390 px) con navegación móvil de AppShell desplegada incluyendo accesos a "Catálogos" y "Pacientes".
14. `C-33-paciente-dialogo-390.png`: Celular (390 px) con diálogo de paciente presentado como hoja inferior (bottom sheet) con tarjeta contenedora y botones táctiles accesibles.
15. `C-33-prestacion-dialogo-390.png`: Celular (390 px) con diálogo de prestación presentado como hoja inferior (bottom sheet) con tarjeta contenedora y botones táctiles accesibles.

Aclaraciones clave de la verificación visual:
- **Admin con todas las acciones**: dispone de alta, edición y desactivación/reactivación tanto en pacientes como en los tres catálogos (profesionales, sillones, prestaciones).
- **Recepción edita pacientes y ve catálogos en "Solo lectura"**: puede dar de alta y editar pacientes, pero en catálogos visualiza las tablas con etiqueta de "Solo lectura" y sin botones de nuevo/editar/desactivar.
- **Odontóloga sin botones de escritura**: consulta pacientes y catálogos en solo lectura, sin botones de nuevo ni acciones de modificación.
- **Mensajes literales de 409 (DNI y nombre) y 422 (DNI)**: los rechazos del backend se presentan íntegros y textuales en contenedores accesibles con `role="alert"`.
- **Desactivar con confirmación y estado "Inactivo"**: la desactivación requiere confirmación explícita mediante diálogo modal dedicado, reflejando el estado "Inactivo" en texto visible (sin depender solo de color).
- **Diálogos con tarjeta centrada a 1440 y hoja inferior a 390**: los tres diálogos (`PatientFormDialog`, `CatalogFormDialog`, `CatalogConfirmDialog`) cuentan con tarjeta contenedora (`data-modal-card` y `.modalContent`), centrados en desktop y como bottom sheet en viewport móvil (390 px).
- **Tabla apilada a 390 px**: a 390 px las tablas se apilan verticalmente con `data-label` por celda, caption a ancho completo (100%) y thead oculto de forma accesible con patrón visually-hidden.
- **Sin scroll horizontal en 1440/768/390**: en los tres viewports evaluados no existe desbordamiento horizontal (`scrollWidth <= innerWidth`).

