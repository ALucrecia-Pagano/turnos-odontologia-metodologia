# Design

## Context

Ver `proposal.md` (Why) para la motivación. Estado actual que condiciona el diseño (rama `c33-propose`, con C-32 ya mergeado en `main`):

- `frontend/src/App.tsx:33-35` solo registra `agenda`, `horarios` y el comodín `*` bajo `AppShell`. `/catalogos` y `/pacientes` caen en `NotFoundPage`.
- `frontend/src/features/auth/menuFor.ts:37-48` ya define los ítems `catalogos` (`/catalogos`) y `pacientes` (`/pacientes`) para los tres roles. La habilitación es por identidad: `const enabled = item.id === "agenda" || item.id === "horarios-y-bloqueos";` (`menuFor.ts:59`).
- Capa de red reutilizable sin cambios: `createApiClient({ fetchFn })` (`frontend/src/shared/api/client.ts`) clasifica 400/401/403/404/409/422 en `ApiErrorPayload` (`frontend/src/shared/api/types.ts:24-30`; `toErrorPayload` en `client.ts:92-115`). Un 401 dispara `notifyUnauthorized()` (`client.ts:151-152`).
- Primitivas reutilizables: `Dialog` (`shared/components/Dialog.tsx`, props `open`, `onClose`, `labelledBy`, `returnFocusRef`, `isMobile`; hoja inferior hasta 640 px por `matchMedia`, `Dialog.tsx:33-40`), `LoadingState` (`role="status"`), `ErrorState` (`role="alert"` con botón "Reintentar"), `EmptyState` y `PageShell` (`title` requerido; lo muestra como marca en un `<span>`, no como `<h1>`, `PageShell.tsx:9-14`).
- Patrones a imitar: manejo de violaciones y `fieldErrors` de `features/appointments/AppointmentFormDialog.tsx:85-86,180-190,215,251`; confirmación interna con "Volver" de `features/horarios/BlockDeleteDialog.tsx:55,63`; región `role="status"` única y siempre montada de `features/horarios/HorariosPage.tsx:164-168`; test de tokens de `features/horarios/horariosStyles.test.ts`.
- Línea base de la suite según la última evidencia de C-32: 321 tests en 82 archivos (`docs/evidencias/test-suite-C-32.txt`). El apply la vuelve a medir (tarea 1.1).

### Contratos del backend usados (C-20, copiados del código)

Todas las rutas cuelgan de `/api` (`backend/app/main.py:90`). Los routers protegidos se incluyen en `main.py:35-38`.

| Recurso | Método y ruta | Cuerpo | Respuesta | Archivo:línea (decorador / ruta) | Permiso (`permissions.py`) |
|---|---|---|---|---|---|
| Profesional | `GET /api/professionals[?active=]` | — | `200` `[{id, fullName, active, licenseNumber}]` | `api/professionals.py:51-52`, `active` en `:63` | READ `_D,_R,_A` `:63` |
| Profesional | `POST /api/professionals` | `{fullName, licenseNumber?}` | `201` | `api/professionals.py:24-26` | CREATE `_A` `:62` |
| Profesional | `PUT /api/professionals/{id}` | `{fullName, licenseNumber?}` | `200` | `api/professionals.py:100-101` | UPDATE `_A` `:64` |
| Profesional | `POST /api/professionals/{id}/deactivate` | — | `200` | `api/professionals.py:133-134`, exige DELETE `:143` | DELETE `_A` `:65` |
| Profesional | `POST /api/professionals/{id}/reactivate` | — | `200` | `api/professionals.py:156-157`, exige UPDATE `:166` | UPDATE `_A` `:64` |
| Sillón | `GET /api/chairs[?active=]` | — | `200` `[{id, name, active}]` | `api/chairs.py:41-42` | READ `_D,_R,_A` `:67` |
| Sillón | `POST /api/chairs` | `{name}` | `201` | `api/chairs.py:23-24` | CREATE `_A` `:66` |
| Sillón | `PUT /api/chairs/{id}` | `{name}` | `200` | `api/chairs.py:77-78` | UPDATE `_A` `:68` |
| Sillón | `POST /api/chairs/{id}/deactivate` | — | `200` | `api/chairs.py:100-101`, DELETE `:110` | DELETE `_A` `:69` |
| Sillón | `POST /api/chairs/{id}/reactivate` | — | `200` | `api/chairs.py:118-119`, UPDATE `:128` | UPDATE `_A` `:68` |
| Prestación | `GET /api/services[?active=]` | — | `200` `[{id, name, defaultDurationMin, active}]` | `api/services.py:46-47`, `active` en `:58` | READ `_D,_R,_A` `:71` |
| Prestación | `POST /api/services` | `{name, defaultDurationMin}` | `201` | `api/services.py:23-24` | CREATE `_A` `:70` |
| Prestación | `PUT /api/services/{id}` | `{name, defaultDurationMin}` | `200` | `api/services.py:95-96` | UPDATE `_A` `:72` |
| Prestación | `POST /api/services/{id}/deactivate` | — | `200` | `api/services.py:125-126`, DELETE `:135` | DELETE `_A` `:73` |
| Prestación | `POST /api/services/{id}/reactivate` | — | `200` | `api/services.py:148-149`, UPDATE `:158` | UPDATE `_A` `:72` |
| Paciente | `GET /api/patients[?query=]` | — | `200` `[{id, fullName, dni, phone, healthInsurance}]` | `api/patients.py:51-52`, `query` en `:63` | READ `_D,_R,_A` `:75` |
| Paciente | `POST /api/patients` | `{fullName, dni, phone?, healthInsurance?}` | `201` | `api/patients.py:21-22` | CREATE `_R,_A` `:74` |
| Paciente | `PUT /api/patients/{id}` | `{fullName, dni, phone?, healthInsurance?}` | `200` | `api/patients.py:102-103` | UPDATE `_R,_A` `:76` |
| Paciente | desactivar / reactivar / borrar | **no existe** | — | sin ruta en `api/patients.py` | DELETE `{}` `:77` |

Leyenda: `_A` administrador, `_R` recepción, `_D` odontólogo. Los archivos de rutas están bajo `backend/app/`; `permissions.py` es `backend/app/auth/permissions.py`.

Esquemas (`backend/app/api/schemas.py`): `ProfessionalInput` `:71-75`, `ChairInput` `:78-81`, `ServiceInput` `:84-88` (`default_duration_min: int`), `PatientInput` `:91-97`, todos con `extra="forbid"` y alias camelCase; respuestas `ProfessionalResponse` `:100-106`, `ChairResponse` `:109-114`, `ServiceResponse` `:117-123`, `PatientResponse` `:126-133` (sin `active`). Ningún esquema tiene `max_length`.

Búsqueda de pacientes (`backend/app/repositories/patients.py:86-98`): `query` se recorta. Si queda vacío, devuelve todos. Si no, busca `full_name ILIKE %q%` y, si `q` tiene dígitos, también DNI que empieza con esos dígitos. Ordena por `lower(full_name)` e `id`. No hay paginación.

Errores y mensajes literales:

| Status | Código | Mensaje literal | Archivo:línea |
|---|---|---|---|
| 409 | `DUPLICATE_DNI` | `Ya existe un paciente con el DNI {d.ddd.ddd}.` | `backend/app/domain/rules/dni.py:29-33`; status en `backend/app/api/errors.py:17` |
| 409 | `DUPLICATE_NAME` | `Ya existe un sillón con el nombre "{nombre}".` / `Ya existe una prestación con el nombre "{nombre}".` | `backend/app/domain/rules/catalog_names.py:23`; sujetos en `backend/app/domain/catalog/create.py:25,35`; status en `errors.py:18` |
| 422 | `EMPTY_NAME` | `El nombre {del profesional\|del sillón\|de la prestación\|del paciente} no puede estar vacío.` | `catalog_names.py:10`; sujetos en `create.py:16,22,32,43`; status en `errors.py:30` |
| 422 | `INVALID_DNI` | `El DNI no es válido (se recibió "{dni}"): debe tener 7 u 8 dígitos, con o sin puntos.` | `dni.py:18-19`; status en `errors.py:29` |
| 422 | `INVALID_DURATION` | `La duración de la prestación no es válida (se recibió {n} minutos): {razones}.` (razones unidas por " y ") | `backend/app/domain/rules/duration.py:31-47`; `GRID_STEP_MIN` en `grid.py:9`, `MAX_DURATION_MIN` en `duration.py:13`; status en `errors.py:22` |
| 403 | `FORBIDDEN_OPERATION` | `No tiene permiso para {crear\|actualizar\|borrar} {profesionales\|sillones\|prestaciones\|pacientes}.` | `permissions.py:99-114`; lanzado en `backend/app/api/deps.py:96-97`; status en `errors.py:34` |
| 404 | `NOT_FOUND` | "Profesional no encontrado." / "Sillón no encontrado." / "Prestación no encontrada." / "Paciente no encontrado." | `backend/app/services/catalog.py:26,120,212`; `backend/app/services/patients.py:21`; handler en `errors.py:66-72` |
| 400 | `errors[]` | `missing`: "Falta este dato."; `json_invalid`: "El cuerpo no es JSON válido."; cualquier otro tipo: "Dato inválido." | `errors.py:110-117` (mensajes), `errors.py:120-138` (handler; `field` = alias camelCase) |

Prioridad cuando hay violaciones mezcladas: 403, luego 422, luego 409 (`errors.py:42-51`). Los profesionales no tienen unicidad de nombre y nunca devuelven 409.

## Goals / Non-Goals

**Goals:**
- Un componente genérico de catálogo para las tres entidades y una pantalla de pacientes separada. Alrededor de 24 tests nuevos; el plan concreto tiene 28, más 2 tests existentes con cambio de requisito (ver la tabla de trazabilidad en `tasks.md`).
- Entrega escalonada en 4 fases con punto de corte explícito (Plan B).
- Cero cambios en backend, `client.ts`, `types.ts`, `Dialog.tsx` y `tokens.css`.

**Non-Goals:**
- Desactivar o borrar pacientes (no hay endpoint; ver `proposal.md`, "Fuera de alcance").
- Paginación, ordenamiento en el cliente, búsqueda al tipear (debounce) y filtros de activos o inactivos.
- Validar en el cliente las reglas del dominio.
- Mostrar fechas u horas: estas pantallas no muestran ninguna. Si el apply llegara a mostrar alguna, MUST usar `Intl.DateTimeFormat("es-AR", { timeZone })` con la zona horaria de la API (`GET /api/agenda`), como C-32.

## Decisions

### D1. Alcance: catálogo genérico más pantalla de pacientes aparte
- **Decisión**: `CatalogSection` es un solo componente, parametrizado por una configuración de datos por entidad (`catalogConfigs.ts`: ruta de API, columnas, campos del formulario, armado del payload y textos). Se usa para profesionales, sillones y prestaciones. Pacientes es una pantalla propia, porque tiene búsqueda, cuatro campos y ninguna activación.
- **Por qué**: las tres entidades comparten `{id, nombre, active}` y las mismas acciones `deactivate`/`reactivate`; solo cambian los campos. Sumar una entidad cuesta una entrada de configuración, y los tests se escriben una vez por comportamiento, con la entidad que más lo ejercita.
- **Alternativas**: cuatro pantallas separadas (unos 36 archivos y 40 tests: no entra en el plazo); solo pacientes y prestaciones (deja US-021 sin UI y ahorra poco).
- **Límite**: la configuración es solo datos, sin render props ni plugins. Si `CatalogSection.tsx` supera unas 250 líneas, se parte en tabla y acciones.

### D2. Orden de tareas y Plan B
Fases, en este orden y sin mezclar:
1. **Pacientes: listado y búsqueda** (ruta `/pacientes`, tabla, búsqueda, error con reintento y tests de estilos).
2. **Catálogos en solo lectura y menú** (ruta `/catalogos`, secciones, estado Activo/Inactivo, título y h1, tablas adaptables, menú habilitado y cambio de requisito en los tests de menú).
3. **Formularios de alta y edición en `Dialog`** (pacientes y catálogos, errores del backend, acciones por rol, mensaje de estado único y hoja inferior).
4. **Desactivar y reactivar en catálogos**.

**Plan B (si el 17/11 no llega)**: se entrega hasta la fase 2 inclusive y se recortan las **fases 3 y 4 completas** (tareas 4.x y 5.x de `tasks.md`, escenarios 14 a 30). En ese caso:
- Pacientes queda en listado y búsqueda; catálogos queda en solo lectura para los tres roles, sin botones de escritura.
- Menú y rutas quedan habilitados (la fase 2 los incluye).
- Los escenarios recortados se marcan como "no implementados (Plan B)" en `tasks.md` y en la trazabilidad. Antes de archivar, el delta de `frontend-catalogs-and-patients` se reduce a los requisitos cubiertos por las fases 1 y 2, para no archivar requisitos sin test.
- La fase 6 (capturas) y la fase 7 (verificación) se hacen igual sobre lo entregado.

### D3. Rutas y navegación interna
- `/pacientes` y `/catalogos` son dos entradas hijas de `AppShell` en `createAppRoutes` (`App.tsx`).
- La sección del catálogo va en `?seccion=profesionales|sillones|prestaciones`, leída con `useSearchParams`, como `?professionalId=` en C-32 y `?view=chair` en C-31. Es un grupo de `Link` con `aria-current="page"` en el activo. Se descarta `role="tab"` para no implementar el teclado de pestañas. Valor ausente o desconocido: `profesionales`.
- **Alternativa descartada**: subrutas `/catalogos/profesionales` (más entradas en el router y una redirección del índice, sin beneficio para el usuario).

### D4. Permisos por rol: exactamente el RBAC del backend
Matriz derivada de `backend/app/auth/permissions.py:62-77`:

| Rol | Profesionales / Sillones / Prestaciones | Pacientes |
|---|---|---|
| administrador | lee, crea, edita, desactiva (DELETE `:65,69,73`) y reactiva (UPDATE `:64,68,72`) | lee, crea (`:74`) y edita (`:76`) |
| recepción | solo lee (`:63,67,71`) | lee, crea (`:74`) y edita (`:76`) |
| odontólogo | solo lee (`:63,67,71`) | solo lee (`:75`) |
| cualquiera | — | nunca desactiva ni borra (`:77`, `{}`) |

- La UI decide con `user.role` de `useAuth()` (`AuthContext.tsx:226`) y **no muestra** lo que el rol no puede hacer. En catálogos, recepción y odontólogo ven el texto "Solo lectura".
- El backend sigue siendo la autoridad: si igual llega un 403, su `message` literal aparece en la alerta del diálogo sin cerrar sesión (mismo camino que 409/422). Ese caso no tiene escenario propio porque usa la misma rama de código que el 409.

### D5. Búsqueda de pacientes propia, sin `PatientSearchGroup`
- **Decisión**: un formulario de la pantalla con `<label>` visible "Buscar por nombre o DNI" y botón "Buscar". Pide `GET /api/patients?query=${encodeURIComponent(texto)}` al enviar (Enter o botón). La carga inicial va sin `query`. Si el texto está vacío, se pide la lista completa.
- **Por qué no `PatientSearchGroup`** (evidencia en `frontend/src/features/appointments/PatientSearchGroup.tsx`):
  - Es un selector de radio para elegir un paciente dentro del formulario de turno.
  - Tiene `id="patient-search-input"` fijo.
  - Usa un tipo local `{id, fullName, dni}`, sin `phone` ni `healthInsurance`.
  - No tiene estado de error: ante una falla de red muestra "No se encontraron pacientes".
  - Etiqueta el campo solo para lectores de pantalla.
  
  Adaptarlo cambiaría un componente con tests existentes. Solo se reutiliza su contrato (`encodeURIComponent` sobre `query`).
- Sin debounce: con la regla C1 no hay fake timers para probarlo, y la API devuelve todo en una sola pasada.

### D6. Formularios en `Dialog` y validación en el cliente
- Un diálogo por pantalla sirve para alta y edición: `PatientFormDialog` y `CatalogFormDialog` (este último arma sus campos desde la configuración).
- Cada diálogo tiene un `labelledBy` único, foco inicial en el primer campo y `returnFocusRef` al botón que lo abrió. La hoja inferior hasta 640 px la da `Dialog.tsx` (C-36), así que no hace falta CSS móvil propio para el modal.
- El cliente solo valida lo que no se puede enviar: una duración que no es entero (`/^\d+$/` sobre el texto recortado) no se envía y muestra "La duración debe ser un número entero de minutos." con `aria-invalid`. Mandar `Number("")` daría un 422 engañoso ("se recibió 0 minutos").
- Nombre vacío, DNI inválido y duración fuera de regla se envían igual, y se muestra el 422 literal del backend.
- `maxLength` en los inputs según las columnas de la base, porque la API no tiene `max_length`: nombres 255, matrícula 50, teléfono 50, obra social 255 y DNI 10 (8 dígitos y 2 puntos).
- Teléfono, obra social y matrícula vacíos viajan como `null`, nunca como `""`. La duración viaja como `number`.

### D7. Errores
- 409, 422 y 403 se muestran en un único contenedor `role="alert"` dentro del diálogo, con el `message` de cada violación sin reformular. Al aparecer recibe el foco. **Ningún campo recibe `aria-invalid` por un 409** (tampoco por un 422: el backend no indica el campo).
- Cobertura de los errores de dominio, sin duplicar caminos:
  - **409 `DUPLICATE_DNI`** (pacientes): escenario 17, en `PatientFormDialog`.
  - **422 `INVALID_DNI`** (pacientes): escenario 18, en `PatientFormDialog`. El cliente no valida el DNI: lo envía tal cual y muestra el mensaje literal.
  - **422 `INVALID_DURATION`** (prestaciones): escenario 24, en `CatalogFormDialog`.
  - **409 `DUPLICATE_NAME`** (sillones y prestaciones): **se cubre una sola vez, en el componente genérico de catálogo** (`CatalogFormDialog`, escenario 25, con una prestación). No hay escenario de 409 por sillón: sillones y prestaciones pasan por el mismo `CatalogFormDialog` y la misma alerta, y solo cambia el sujeto del mensaje del backend (`domain/catalog/create.py:25,35`). Los profesionales no tienen unicidad de nombre.
- 400: `aria-invalid="true"` en el campo cuyo alias coincide con `field` (`fullName`, `dni`, `phone`, `healthInsurance`, `name`, `defaultDurationMin`, `licenseNumber`), con el mensaje enlazado por `aria-describedby`. Un 400 sin `field` va a la alerta.
- 404 en una mutación: su `message` va a la alerta.
- `unknown` (por ejemplo, un 500 por un texto demasiado largo): "No se pudo completar la operación. Intente de nuevo." en la alerta. Es un mensaje del cliente y no reemplaza mensajes del dominio.
- Carga de listas fallida: `ErrorState` con "Reintentar".

### D8. Estado, refresco y una sola región `role="status"`
- Después de cada mutación exitosa la lista se **vuelve a pedir** con `GET`, en vez de parchear el estado local: el orden lo da la API y pacientes se re-consulta con el `query` vigente. El refresco no reemplaza la tabla por `LoadingState`, para no montar una segunda región `role="status"` mientras se anuncia el resultado. `LoadingState` se usa solo en la carga inicial y al cambiar de sección o de búsqueda.
- Cada página tiene **una** región `role="status"` (`aria-live="polite"`) siempre montada, con un único `statusMessage`. Se limpia al abrir cualquier diálogo y se reemplaza al terminar la acción. Es el patrón final de C-32 (`HorariosPage.tsx:164-168`).
- Mensajes literales: "Paciente creado.", "Paciente actualizado.", "Profesional creado.", "Profesional actualizado.", "Sillón creado.", "Sillón actualizado.", "Prestación creada.", "Prestación actualizada.", "Profesional desactivado.", "Sillón desactivado.", "Prestación desactivada.", "Profesional reactivado.", "Sillón reactivado.", "Prestación reactivada.".

### D9. Menú: cambio de requisito sobre tests existentes (desvío anticipado)
- **Producción**: `menuFor.ts` amplía la habilitación por identidad con `ENABLED_MENU_IDS = ["agenda", "horarios-y-bloqueos", "catalogos", "pacientes"]`. **`ENABLED_MENU_IDS` es una constante interna de `menuFor.ts`: no es un parámetro, no es inyectable y no se exporta.** `menuFor(role)` mantiene su firma; los tests solo observan su salida.
- **Sin seams**: se descarta `menuFor(role, enabledIds)`, `enabledMenuIds` o cualquier flag que deje viejos los tests (mismo criterio que C-32 D1).
- **Se declarará como desvío en el apply.** El conteo real de aserciones modificadas por archivo se mide con `git diff` en el apply y se declara como desvío en `verify-C-33.md`; los títulos históricos de tests no se renombran.
- Archivos previstos (sin conteo de antemano; la tarea 1.3 confirma la lista sobre `main`):
  - `frontend/src/features/auth/menuFor.test.ts`: `catalogos` y `pacientes` pasan a habilitados (`disabled === false`, `badge === null`, `path` `/catalogos` y `/pacientes`).
  - `frontend/src/shared/components/AppShell.test.tsx`: las listas de botones "Próximamente" por rol pierden "Catálogos" y "Pacientes". Si al odontólogo no le queda ningún botón, `getAllByRole("button")` lanza, así que pasa a `queryAllByRole("button")`.
  - `frontend/src/shared/components/AppShellNavigation.test.tsx`: más enlaces y menos botones "Próximamente" para el administrador.
- Sin cambios previstos: `AppShell.mobile.test.tsx` (solo usa `a[data-menu-item='Agenda']`) y `smoke.test.tsx`. Una búsqueda de "Catálogos|Pacientes|Próximamente|catalogos|pacientes" en `*.test.*` no encuentra otros dependientes (la única coincidencia ajena es `PatientSearchGroup.test.tsx:92`, sin relación).
- **Los títulos históricos de los tests NO se renombran** (por ejemplo `menuFor.test.ts:5` "…los otros 5 ítems deshabilitados con Próximamente", `AppShell.test.tsx:48`, `AppShellNavigation.test.tsx:70`), aunque queden desactualizados. Las trazabilidades archivadas de C-32 y anteriores los citan por nombre; son descripciones, no aserciones.
- Los bucles `for` sobre botones (`AppShell.test.tsx:75-78`, `AppShellNavigation.test.tsx:87-90`) no se tocan: siguen verificando lo mismo sobre menos elementos.
- Evidencia: `docs/evidencias/diff-tests-existentes-C-33.txt` con `git diff main --stat` y el diff completo de los tests de menú tocados. El conteo que se declare en el apply MUST salir de ese diff.
- El nuevo escenario de menú ("Catálogos y Pacientes habilitados para los tres roles") va en un **archivo de test nuevo**: `frontend/src/shared/components/AppShellCatalogosPacientes.test.tsx`.

### D10. Presentación: tabla semántica, estado en texto y adaptable
- `<table>` con `<caption>` y `<th scope="col">`. Hasta 640 px cada fila se apila y cada `<td>` muestra su etiqueta (`data-label` con `::before`), sin scroll horizontal de página.
- Estado de catálogo con `ActiveBadge`: texto "Activo" o "Inactivo" siempre visible; el estilo solo con tokens existentes (inactivo: `--color-text-muted` y `--color-border`). Nunca se comunica solo por color. `StatusBadge` no sirve: es de estados de turno.
- Dato ausente: "Sin dato".
- Botones de acción con `min-height: 44px` y `:focus-visible` con `--color-focus`.

### D11. Tokens: solo los existentes y de superficie clara
- Solo custom properties ya definidas en `frontend/src/shared/styles/tokens.css`. No se agregan tokens.
- Nada de `--color-ice` ni tokens `*-on-navy`: estas pantallas van sobre fondo claro. Paleta prevista: `--color-text`, `--color-text-muted`, `--color-background`, `--color-surface`, `--color-border`, `--color-primary`, `--color-primary-contrast`, `--color-danger-*`, `--color-focus`, `--space-*`, `--font-size-*`, `--radius-*` y `--shadow-sm`.
- El test de tokens (escenario 05) lista los `.module.css` de `features/pacientes/` y `features/catalogos/` con `readdirSync` (lectura real de disco, sin mocks) y captura `var(\s*(--[a-z0-9-]+)` **también con valor de respaldo**. El regex de C-32 (`var\((--[a-z0-9-]+)\)`) no ve `var(--x, fallback)`.

### D12. Capa de datos
- Archivos nuevos `features/pacientes/pacientesApi.ts` y `features/catalogos/catalogosApi.ts`, a imagen de `features/horarios/horariosApi.ts`, con parsers estrictos que devuelven un error "respuesta inesperada" si el JSON no calza.
- No se amplía `agendaApi.ts` (es de la agenda) ni se tocan `client.ts` ni `types.ts`.

## Componentes previstos

```
frontend/src/features/pacientes/
├── pacientesApi.ts              # listPatients(query?), createPatient, updatePatient + parsers
├── PacientesPage.tsx            # PageShell "Pacientes", h1, búsqueda, tabla, status único
├── PacientesPage.module.css
├── PatientFormDialog.tsx        # alta/edición (4 campos), alerta de violaciones, 400 por campo
├── PatientFormDialog.module.css
├── PacientesPage.test.tsx       # escenarios 01-04, 20
└── PatientFormDialog.test.tsx   # escenarios 14-19, 21
frontend/src/features/catalogos/
├── catalogosApi.ts              # list/create/update/deactivate/reactivate genéricos + parsers
├── catalogConfigs.ts            # profesionales, sillones, prestaciones (solo datos)
├── CatalogosPage.tsx            # PageShell "Catálogos", h1, enlaces de sección, status único
├── CatalogosPage.module.css
├── CatalogSection.tsx           # tabla + acciones por rol
├── CatalogSection.module.css
├── CatalogFormDialog.tsx
├── CatalogFormDialog.module.css
├── CatalogConfirmDialog.tsx     # desactivar/reactivar, "Volver" / "Sí, desactivar" / "Sí, reactivar"
├── ActiveBadge.tsx              # "Activo"/"Inactivo" en texto
├── CatalogosPage.test.tsx       # escenarios 07, 08, 27
├── CatalogFormDialog.test.tsx   # escenarios 22-26
├── CatalogFormDialog.mobile.test.tsx  # escenario 28
├── CatalogConfirmDialog.test.tsx      # escenarios 29-30
├── CatalogosPacientesRoutes.test.tsx  # escenario 09
└── catalogosPacientesStyles.test.ts   # escenarios 05, 06, 10
frontend/src/shared/components/AppShellCatalogosPacientes.test.tsx   # escenario 11
```

Archivos existentes que se tocan: `frontend/src/App.tsx`, `frontend/src/features/auth/menuFor.ts` y los tests de menú de D9.

## Reglas de testing (vinculantes para el apply)

- **Regla C1**: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers ni MSW; sin `waitFor` largos. La red va solo con `createApiClient({ baseUrl, fetchFn })` y `Response` reales; el router, con `createMemoryRouter(createAppRoutes(...))` + `RouterProvider` dentro de `AuthProvider` con `createMemoryTokenStore`. Modelo: `features/horarios/HorariosPage.test.tsx`. Los tests de CSS son estáticos, con `readSrcFile` de `src/test/cssText.ts`.
- **Strict TDD**: un escenario = un test = una mutación propia. Los tests auxiliares que se agreguen también llevan su mutación. RED antes de producción y GREEN después, con evidencia por test en `docs/evidencias/red-C-33/` y `docs/evidencias/green-C-33/`.
- **Trazabilidad**: escenario → test → mutación con numeración corrida (01..30 y V01..V03), sin saltos y 1:1 con los `#### Scenario` de las dos specs delta (tabla "ID → spec → título del escenario" de `tasks.md`). El script falla si un escenario no tiene ID, si un ID no existe en las specs, si dos escenarios comparten test o si alguno testeable no tiene test.
- **Mutaciones**: script con detección de inválidas (normalización CRLF/LF y hash distinto tras mutar); 0 supervivientes y 0 inválidas.
- **Datos ficticios** (RN-PA-02) en tests, seeds y capturas.

## Risks / Trade-offs

- **[Plazo: entrega el 19/11 y corte decidido el 17/11]** → Orden D2 con Plan B. Pacientes va primero porque es el flujo diario de recepción.
- **[Conteo del desvío del menú distinto del real]** → design.md no fija un conteo. El apply lo mide con `git diff` y declara lo que muestre el diff en `verify-C-33.md`. No se repite la frase "una aserción por archivo".
- **[Sin `max_length` en la API: textos largos pueden terminar en un 500 sin cuerpo clasificado]** → `maxLength` en los inputs y mensaje genérico para `unknown`. Queda como deuda de backend fuera de alcance.
- **[`GET /patients` sin paginación]** → Aceptable en el MVP (5 pacientes de seed). La búsqueda acota. No se pagina en C-33.
- **[Un nombre o DNI inactivo sigue reservado y da un 409 que el usuario no espera]** → Las tablas de catálogos listan inactivos. El mensaje del backend nombra el valor repetido.
- **[El genérico tiende a sobre-configurarse]** → Configuración solo de datos y tres entidades fijas (D1).
- **[Una segunda región `role="status"` durante el refresco]** → El refresco no usa `LoadingState` (D8). El escenario 21 lo cubre.
- **[El `setTimeout` de Escape en `Dialog.tsx` es sensible (C-30)]** → No se modifica `Dialog.tsx`. Escape en la confirmación usa el `onClose` existente. El escenario 29 prueba "Volver"; Escape ya lo cubre `Dialog.escape.test.tsx`.

## Migration Plan

No aplica: solo frontend, sin datos ni migraciones. Para volver atrás alcanza con revertir los commits del apply; el backend no cambia.
