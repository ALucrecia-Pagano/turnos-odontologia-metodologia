# Exploración C-33: UI de Catálogos y Pacientes (`ui-catalogos-y-pacientes`)

> **Fecha**: 2026-11-15 (entrega 2026-11-19: quedan 4 días).
> **Rama**: `c32-apply`, con C-32 (`ui-horarios-y-bloqueos`) aplicándose en el mismo árbol de trabajo.
> **Modo**: solo lectura del código y de la documentación (skill `openspec-explore`: sin implementar). No se creó el change, no se corrió `openspec new`, no se ejecutaron tests ni builds. Único archivo escrito: este.
> **Qué se consultó realmente**:
> - **Skill `appointment-frontend-ux`**: SÍ, leída completa (`.agents/skills/appointment-frontend-ux/SKILL.md`). Se usó para la regla C1, los tokens, la accesibilidad (estado por texto, foco, 44 px), la verificación visual y el checklist de revisión.
> - **MCP Context7**: NO se usó. C-33 no introduce librerías ni APIs nuevas de React 18.3.1, React Router 6.30.6 ni Vitest 3.2.7 más allá de lo que ya usan C-31 y C-32 (`useSearchParams` ya está en uso en el repo). Si el apply quisiera `useSearchParams` con una forma que no esté ya en el código, consultar Context7 (React Router v6) entonces.
> - **Aviso de concurrencia**: C-32 está en apply. Nada bajo `frontend/`, `openspec/` ni el resto de `docs/evidencias/` fue tocado. Las líneas de test que se citan para el menú corresponden al estado del árbol de trabajo en este momento (con los cambios sin commitear de C-32) y pueden correrse si C-32 sigue editando.

---

## 0. Qué dice el roadmap y qué dicen los documentos fuente

`CHANGES.md:782-792` ([C-33]):

- Scope: "Pantallas del administrador para profesionales, sillones y prestaciones (con duración) y de recepción/administrador para pacientes (nombre, DNI, teléfono, obra social como texto); sin campos clínicos." Tests: "validaciones mostradas, DNI duplicado, desactivar." Dependencias `C-26, C-20`. Governance BAJO.
- `CHANGES.md:165`: `C-32` y `C-33` están entre lo "postergable" ("con seeds y la API alcanza para operar; la UI de configuración es lo más postergable").

Historias (`knowledge-base/06_funcionalidades.md:144-154`):

- **US-020** (administrador, prestaciones con duración): CA-1 duración válida (RN-AG-09), CA-2 nombre único, CA-3 desactivar no afecta turnos existentes.
- **US-021** (administrador, profesionales y sillones): CA-1 alta con nombre válido, CA-2 desactivar impide nuevos turnos pero conserva el historial.
- **US-022** (recepción, pacientes con datos mínimos): CA-1 DNI único, CA-2 no existen campos clínicos, CA-3 seeds y tests solo con datos ficticios.

Reglas (`knowledge-base/05_reglas_de_negocio.md:58-59`): **RN-PA-01** solo nombre, DNI, teléfono y obra social (texto), sin información clínica; **RN-PA-02** todo dato de paciente (repo, seeds, tests, capturas) es ficticio.

RBAC (`knowledge-base/03_actores_y_roles.md:15-30`): Profesionales, Sillones y Prestaciones: odontólogo R, recepción R, administrador CRUD. Pacientes: odontólogo R, recepción CRU, administrador CRU. Nadie borra pacientes.

**Discrepancia detectada entre el roadmap y la API**: `CHANGES.md:786` pide tests de "desactivar", pero **los pacientes no tienen desactivar/reactivar** (no existe `active` en `PatientInput`/`PatientResponse`, `backend/app/api/schemas.py:91-97` y `126-131`; no hay `/patients/{id}/deactivate`; `(Resource.PATIENT, Action.DELETE): {}` en `backend/app/auth/permissions.py:77`). "Desactivar" aplica solo a profesionales, sillones y prestaciones.

---

## 1. Contratos reales (verificados en el código, no de memoria)

Todos los esquemas de entrada son camelCase con `extra="forbid"` y `populate_by_name=True` (`backend/app/api/schemas.py:71-97`). Todos los routers cuelgan de `/api` (el frontend arma `${API_BASE_URL}${path}`, `frontend/src/shared/api/client.ts:119`).

### 1.1 Tabla de endpoints

Leyenda de roles: **A** administrador, **R** recepción, **O** odontólogo. Permisos de `backend/app/auth/permissions.py:62-77`.

| Entidad | Método y ruta | Payload (JSON) | Respuesta OK | Roles | Archivo |
|---|---|---|---|---|---|
| Profesional | `GET /api/professionals?active=true\|false` (opcional) | sin cuerpo | `200` lista de `{id, fullName, active, licenseNumber}` (`licenseNumber` puede ser `null`) | A, R, O | `backend/app/api/professionals.py:51-74` |
| Profesional | `GET /api/professionals/{id}` | sin cuerpo | `200` el mismo objeto | A, R, O | `professionals.py:77-97` |
| Profesional | `POST /api/professionals` | `{fullName: str, licenseNumber?: str\|null}` | `201` objeto, `active: true` | A | `professionals.py:24-48` |
| Profesional | `PUT /api/professionals/{id}` | `{fullName, licenseNumber?}` (reemplazo completo; **no** acepta `active`) | `200` objeto | A | `professionals.py:100-130` |
| Profesional | `POST /api/professionals/{id}/deactivate` | sin cuerpo | `200` objeto con `active: false` | A (`Action.DELETE`) | `professionals.py:133-153` |
| Profesional | `POST /api/professionals/{id}/reactivate` | sin cuerpo | `200` objeto con `active: true` | A (`Action.UPDATE`) | `professionals.py:156-176` |
| Sillón | `GET /api/chairs?active=` | sin cuerpo | `200` lista de `{id, name, active}` | A, R, O | `backend/app/api/chairs.py:41-56` |
| Sillón | `POST /api/chairs` | `{name: str}` | `201` `{id, name, active: true}` | A | `chairs.py:23-38` |
| Sillón | `PUT /api/chairs/{id}` | `{name}` | `200` objeto | A | `chairs.py:77-97` |
| Sillón | `POST /api/chairs/{id}/deactivate` y `/reactivate` | sin cuerpo | `200` objeto | A | `chairs.py:100-133` |
| Prestación | `GET /api/services?active=` | sin cuerpo | `200` lista de `{id, name, defaultDurationMin, active}` | A, R, O | `backend/app/api/services.py:46-69` |
| Prestación | `POST /api/services` | `{name: str, defaultDurationMin: int}` | `201` objeto, `active: true` | A | `services.py:23-43` |
| Prestación | `PUT /api/services/{id}` | `{name, defaultDurationMin}` | `200` objeto | A | `services.py:95-122` |
| Prestación | `POST /api/services/{id}/deactivate` y `/reactivate` | sin cuerpo | `200` objeto | A | `services.py:125-168` |
| Paciente | `GET /api/patients?query=` | sin cuerpo; `query` opcional | `200` lista de `{id, fullName, dni, phone, healthInsurance}` (`phone` y `healthInsurance` pueden ser `null`) | A, R, O | `backend/app/api/patients.py:51-75` |
| Paciente | `GET /api/patients/{id}` | sin cuerpo | `200` objeto | A, R, O | `patients.py:78-99` |
| Paciente | `POST /api/patients` | `{fullName: str, dni: str, phone?: str\|null, healthInsurance?: str\|null}` | `201` objeto | A, R | `patients.py:21-48` |
| Paciente | `PUT /api/patients/{id}` | `{fullName, dni, phone?, healthInsurance?}` (reemplazo completo) | `200` objeto | A, R | `patients.py:102-135` |
| Paciente | desactivar / reactivar / borrar | **No existe** | - | - | `permissions.py:77` (`DELETE: {}`) |

Verificado y matizado respecto de lo que se esperaba de la memoria:

- Deactivate/reactivate de C-20 **existen** para los tres catálogos y son **idempotentes** (`backend/app/domain/catalog/activation.py:11-19`: "idempotente por valores"; `ProfessionalRepository._set_active`, `backend/app/repositories/catalog.py:121-129`). Desactivar uno ya inactivo devuelve `200` con el mismo objeto.
- La respuesta de `PUT`/`POST` de pacientes y profesionales usa los mismos campos que el `GET`.
- **`GET /api/patients` no tiene paginación** (devuelve todos, ordenados por `lower(full_name)` e `id`, `backend/app/repositories/patients.py:98-100`). El seed tiene 5 pacientes (`backend/app/demo_data.py:29-33`): Ana Pérez 30111222, Bruno Acosta 28444555, Carla Medina 27123456, Diego Ríos 33456789, Eva Molina 38987654. Es suficiente para el MVP, hay que decirlo explícitamente.
- **Búsqueda de pacientes** (`backend/app/repositories/patients.py:86-97`): `query` se recorta; si queda vacío, devuelve todos. Busca por `full_name ILIKE %q%` (con escape de `%`, `_` y `\`) **o**, si `q` contiene dígitos, por `dni` que **empieza con** esos dígitos (se extraen los dígitos de `q`, así que "30.111" también encuentra por DNI). El filtro de nombre es por subcadena, no por prefijo. El DNI se guarda normalizado (sin puntos ni espacios): `normalize_dni` en `backend/app/domain/rules/dni.py:6-8` y `dni: String(8)` en `backend/app/db/models.py:67`.
- **Longitudes de columnas** (`backend/app/db/models.py`): nombre/`full_name` 255, `license_number` 50, `phone` 50, `health_insurance` 255. **Los esquemas Pydantic no tienen `max_length`** (verificado: ningún `max_length` en `schemas.py:71-97`). Un texto más largo que la columna no se rechaza con 4xx en la capa de API. Por eso la UI debe poner `maxLength` en los inputs (ver §4 D6 y §6 R5).

### 1.2 Errores y mensajes literales

Mapa de códigos a status: `backend/app/api/errors.py:11-33`. Las violaciones salen como `{"violations": [{"code", "message", ...}]}` (`errors.py:domain_rejected_handler`); si hay mezcla gana 403, luego 422, luego 409 (`status_for`).

| Status | Cuándo | Cuerpo | Mensajes literales |
|---|---|---|---|
| `400` | JSON inválido, campo faltante, tipo erróneo, campo extra (`extra="forbid"`), UUID malformado | `{"errors": [{"field": "fullName"\|null, "type": "...", "message": "..."}]}` (`errors.py:request_validation_handler`) | `json_invalid`: "El cuerpo no es JSON válido."; `missing`: "Falta este dato."; cualquier otro tipo (p. ej. `extra_forbidden`, `int_parsing`, `string_type`): "Dato inválido." (`MALFORMED_MESSAGES`, `DEFAULT_MALFORMED_MESSAGE`, `errors.py:MALFORMED_MESSAGES`). `field` es el nombre del alias camelCase (p. ej. `fullName`, `defaultDurationMin`) y `null` si es `json_invalid`. |
| `401` | Sin token o token inválido | `{"code": "INVALID_TOKEN", "message": ...}` | "La sesión venció o no es válida. Inicie sesión de nuevo." (`errors.py:AUTH_ERROR_MESSAGES`) |
| `403` | Rol sin permiso | `{"violations": [{"code": "FORBIDDEN_OPERATION", "message": ...}]}` | Por celda de `PERMISSION_MESSAGES` (`permissions.py:84-119`): "No tiene permiso para crear profesionales." / "actualizar profesionales." / "borrar profesionales." (deactivate usa `DELETE`); ídem "sillones", "prestaciones", "pacientes" ("No tiene permiso para crear pacientes.", "No tiene permiso para actualizar pacientes."). El `GET` nunca da 403 para los tres roles. |
| `404` | Id inexistente (GET/PUT/deactivate/reactivate), unificado | `{"code": "NOT_FOUND", "message": ...}` | "Profesional no encontrado." (`backend/app/services/catalog.py:26`), "Sillón no encontrado." (`catalog.py:120`), "Prestación no encontrada." (`catalog.py:212`), "Paciente no encontrado." (`backend/app/services/patients.py:21`). |
| `409` | Duplicado | `{"violations": [...]}` | `DUPLICATE_DNI`: "Ya existe un paciente con el DNI {shown}." donde `shown` es el DNI con puntos de miles, p. ej. `30.111.222` (`backend/app/domain/rules/dni.py:check_duplicate_dni`; el mismo texto sale de la carrera por índice único `ux_patient_dni`, `backend/app/repositories/patients.py:37-50`). `DUPLICATE_NAME`: `Ya existe un sillón con el nombre "{nombre}".` / `Ya existe una prestación con el nombre "{nombre}".` (nombre con espacios colapsados; comparación sin mayúsculas ni espacios extra; las tildes distinguen; `backend/app/domain/rules/catalog_names.py:check_duplicate_name`, `backend/app/repositories/catalog.py:_duplicate_name`). **Los profesionales no tienen unicidad de nombre** (`backend/app/domain/catalog/create.py:create_professional`, `update.py:update_professional`, "El nombre no es único"): nunca devuelven 409. |
| `422` | Regla de validez | `{"violations": [...]}` | `EMPTY_NAME`: `El nombre {del profesional\|del sillón\|de la prestación\|del paciente} no puede estar vacío.` (`catalog_names.py:check_name`). `INVALID_DNI`: `El DNI no es válido (se recibió "{dni}"): debe tener 7 u 8 dígitos, con o sin puntos.` (`dni.py:check_dni`). `INVALID_DURATION`: `La duración de la prestación no es válida (se recibió {n} minutos): {razones}.` con razones unidas por " y ": "debe ser mayor que cero minutos" (si `n <= 0`) o "debe ser múltiplo de 5 minutos", y además "no puede superar los 480 minutos" (`backend/app/domain/rules/duration.py:check_duration`, `GRID_STEP_MIN = 5` en `grid.py:9`, `MAX_DURATION_MIN = 480`). |

Consecuencias para la UI:

- **Un nombre vacío en cualquier entidad vuelve como 422 `EMPTY_NAME` con mensaje literal**, no como 400. El 400 solo aparece con campos faltantes o con tipos mal formados.
- **El cliente de API ya clasifica esto**: `client.ts:toErrorPayload` devuelve `kind: "validation"` (400), `"forbidden"` (403), `"conflict"` (409), `"unprocessable"` (422), `"not_found"` (404), `"auth"` (401) y `"unknown"`; el 401 dispara `notifyUnauthorized()` (`client.ts:128-130`). No hace falta tocar `client.ts` ni `types.ts`.
- `defaultDurationMin` debe viajar como `number` entero; un string da 400 "Dato inválido." con `field: "defaultDurationMin"`.
- El DNI puede viajar con puntos o espacios; el backend lo normaliza (`replace(candidate, dni=normalize_dni(...))`, `create.py`/`update.py`) y la respuesta ya trae el DNI normalizado sin puntos (p. ej. `"30111222"`).
- Al editar, el chequeo de duplicados excluye el propio registro (`update.py:update_chair`, `update_service`, `update_patient`), así que guardar sin cambiar el nombre/DNI no da 409.
- Un sillón o prestación **inactivos siguen reservando su nombre** (`openspec/specs/catalog-and-patients`, escenario "Un existente inactivo conserva su nombre único"); lo mismo con el DNI de un paciente. La UI debería poder mostrar los inactivos para que el administrador entienda un 409.

### 1.3 Quién edita qué campo, por rol

| Rol | Profesionales | Sillones | Prestaciones | Pacientes |
|---|---|---|---|---|
| Administrador | crea; edita `fullName` y `licenseNumber`; desactiva/reactiva | crea; edita `name`; desactiva/reactiva | crea; edita `name` y `defaultDurationMin`; desactiva/reactiva | crea; edita los cuatro campos (`fullName`, `dni`, `phone`, `healthInsurance`) |
| Recepción | solo lectura | solo lectura | solo lectura | crea; edita los cuatro campos |
| Odontólogo | solo lectura | solo lectura | solo lectura | **solo lectura** (el `GET` lo permite: `permissions.py:75`) |

Dos cosas que conviene tener presentes:

1. **El odontólogo SÍ lee pacientes y catálogos** (`PATIENT READ`, `PROFESSIONAL READ`, `CHAIR READ`, `SERVICE READ` incluyen `_D`, `permissions.py:63,67,71,75`). Por eso `menuFor.ts` ya lista "Catálogos" y "Pacientes" para los tres roles (`frontend/src/features/auth/menuFor.ts:36-47`). La pantalla debe existir y funcionar en solo lectura para él, no 404.
2. **`active` no se edita por `PUT`**; solo cambia con los endpoints `deactivate`/`reactivate`.

---

## 2. Qué existe para reutilizar, qué falta, y el menú después de C-32

### 2.1 Reutilizable

| Pieza | Dónde | Cómo se usaría |
|---|---|---|
| Cliente HTTP con `fetchFn` inyectable | `frontend/src/shared/api/client.ts:10-28,95-134` (`createApiClient({ fetchFn })`, `FetchFn`, `ApiResult`) y `types.ts` (`ApiErrorPayload`, `Violation`, `FieldError`) | Base de toda la capa de red. Cubre las cuatro formas de error. Sin cambios. |
| `useAuth()` -> `{ client, user }` | `frontend/src/features/auth/AuthContext.tsx` (consumido en `HorariosPage.tsx:23`) | Obtener `client` y `user.role` para decidir qué botones mostrar. |
| `Dialog` (modal nativo `<dialog>`) | `frontend/src/shared/components/Dialog.tsx` (props `open`, `onClose`, `labelledBy`, `returnFocusRef`, `isMobile`); estilos con hoja inferior `<= 640 px` en `Dialog.module.css:28-38` | Formularios de alta/edición y confirmaciones. **La hoja inferior en celular ya viene gratis** (detecta `matchMedia("(max-width: 640px)")`, `Dialog.tsx:34-39`); C-33 no tiene que implementar nada de móvil en los modales. Foco devuelto al disparador con `returnFocusRef`; Escape cierra. |
| Estados base | `shared/components/LoadingState.tsx` (`role="status"`), `ErrorState.tsx` (`role="alert"`, `onRetry`), `EmptyState.tsx` (`title`, `description`, `action`) | Carga, error con reintento y "sin resultados". |
| `PageShell` | `shared/components/PageShell.tsx` (prop `title` requerida) | Contenedor de página (ver §6 R9 sobre cómo lo usa C-32). |
| `StatusBadge` | `shared/components/StatusBadge.tsx` | Es de estados de **turno**, no sirve para activo/inactivo. Hará falta una etiqueta propia "Activo"/"Inactivo" con texto visible y tokens existentes (`--color-danger-*` está en `tokens.css:35-37`). |
| Patrón "violaciones del dominio literales en alerta" | `frontend/src/features/appointments/AppointmentFormDialog.tsx:174-195` (409/422/403 -> `setViolations`, 400 -> `fieldErrors`, foco al alert) y render `:213-230` (`role="alert"`, `aria-live="assertive"`, `<span>` con `v.code` + `v.message`) | Copiar el patrón de manejo de errores; `aria-invalid` solo con 400 (`fieldErrors`, líneas 251-372). |
| Patrón "confirmación dentro del diálogo" (C-30) | Spec `openspec/specs/frontend-appointment-actions/spec.md:75-97` ("Cancelación de turnos con confirmación interna": sin `window.confirm`, "Volver al detalle" o Escape no envían nada); código en `AppointmentDetailDialog.tsx` (botón "Volver al detalle", ~línea 265). Variante más simple y más reciente en `frontend/src/features/horarios/BlockDeleteDialog.tsx` (C-32, en curso): título "Confirmar eliminación de bloqueo", botones "Volver" y "Sí, eliminar bloqueo". | Modelo directo para desactivar/reactivar. |
| Patrón de capa de API tipada con parsers | `frontend/src/features/horarios/horariosApi.ts` (C-32) y `features/agenda/agendaApi.ts:281-322` (`fetchProfessionals`, `fetchChairs`, `UNEXPECTED_RESPONSE_MESSAGE`) | `agendaApi` ya parsea `GET /professionals` y `GET /chairs` (incluye `licenseNumber`, `active`). **No hay `fetchServices` ni cliente de pacientes ni mutaciones de catálogo.** |
| Estilos | `shared/styles/tokens.css` (`--space-1..7`, `--color-danger-*`, etc.), `shared/styles/reset.css`; CSS Modules por componente | Cero colores sueltos (regla de la skill y del spec `frontend-foundation`). |
| Tests de ejemplo con C1 | Ver §2.4 | Plantilla de test de pantalla con `fetchFn` inyectado. |

### 2.2 Qué falta (hay que crearlo en C-33)

- Rutas `/catalogos` y `/pacientes` en `App.tsx` (hoy solo existen `agenda`, `horarios` y el comodín `*`, `frontend/src/App.tsx:33-35`; cualquier otra ruta cae en `NotFoundPage`).
- Capa de API de los cuatro recursos (listar, crear, editar, desactivar, reactivar) con parsers; `fetchServices` no existe (`AppointmentFormDialog.tsx:116` hace `client.request("/services?active=true")` sin parsear).
- Pantalla de pacientes con búsqueda, tabla/lista, formulario.
- Pantalla de catálogos (sección por entidad) con tabla/lista, formulario, confirmación.
- Etiqueta "Activo"/"Inactivo" con texto visible (no solo color).
- **`PatientSearchGroup` no sirve tal cual**: es un selector de radio para elegir un paciente en el formulario de turno (`frontend/src/features/appointments/PatientSearchGroup.tsx:10-16,63-107`), con `id="patient-search-input"` fijo, tipo local `Patient {id, fullName, dni}` (sin `phone` ni `healthInsurance`), búsqueda solo al pulsar el botón o Enter (`handleKeyDown`), sin estado de error (si falla la red limpia la lista y muestra "No se encontraron pacientes"). Sirve como referencia del contrato `GET /patients?query=` con `encodeURIComponent` (`PatientSearchGroup.tsx:34-36`), no como componente a reutilizar.

### 2.3 Menú después de C-32 y qué tests dependen de "Próximamente" para Catálogos y Pacientes

**`menuFor.ts` hoy (con C-32 en el árbol de trabajo)**: `frontend/src/features/auth/menuFor.ts:36-47` define `catalogos` (`/catalogos`) y `pacientes` (`/pacientes`) para `["administrador","recepcion","odontologo"]`. La función habilita por identidad: `const enabled = item.id === "agenda" || item.id === "horarios-y-bloqueos"` (línea ~59; el `git diff` muestra que C-32 cambió `item.id === "agenda"` por esa expresión y la ruta de `horarios` de `/horarios-y-bloqueos` a `/horarios`). Cualquier ítem no habilitado se devuelve con `disabled: true` y `badge: "Próximamente"`. Después de C-33 solo quedarían "Próximamente": **Turnos** (`/turnos`, admin y recepción; no tiene change asignado en `CHANGES.md`) y **Usuarios y roles** (`/usuarios-y-roles`, solo administrador; sin ABM de usuarios en el MVP según `03_actores_y_roles.md`).

**Cómo habilita C-32 su ítem y qué asertos toca** (`openspec/changes/ui-horarios-y-bloqueos/`):

- `proposal.md`: "Se actualizan puntualmente las aserciones en los tests existentes del menú (`menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx`, `AppShell.mobile.test.tsx`), reflejando el cambio de requisito real del menú sin utilizar costuras artificiales."
- `design.md` D1 (líneas 32-37): se descarta la "Opción B (Seam enabledMenuIds)": "Parametrizar `menuFor(role, enabledIds = ["agenda"])` para no tocar los tests existentes. Se descartó porque falsea las pruebas unitarias y genera código muerto en producción." Y declara "una aserción por archivo, exactamente el mismo criterio aplicado a `smoke.test.tsx` en C-35". Desvío documentado en `design.md:74-82`; `tasks.md:7,34-35,89` exige que el diff de tests existentes se limite a esas líneas y se evidencie en `docs/evidencias/diff-tests-existentes-C-32.txt`.
- Criterio de C-35: `docs/evidencias/diff-tests-existentes-C-35.txt` muestra `frontend/src/test/smoke.test.tsx | 2 +- (1 insertion, 1 deletion)`. Es decir, de verdad una línea en un archivo.

**Hallazgo importante: lo que C-32 dice y lo que el árbol de trabajo hace no coinciden.** El diseño habla de "4 líneas, una por archivo, 4 archivos", pero `AppShell.mobile.test.tsx` **no** se modificó (no tiene aserciones de conteo, solo `a[data-menu-item='Agenda']`, `AppShell.mobile.test.tsx:56`) y los otros tres archivos tienen **varias** aserciones cambiadas (10 sentencias en total, ver abajo). El "una aserción por archivo" de C-32 no es literalmente cierto. Para C-33 conviene que el design **cuente honestamente** (aserciones modificadas por archivo y por qué) en vez de repetir la frase.

**Aserciones que C-33 tendría que modificar como cambio de requisito** (estado del árbol de trabajo, con C-32 aplicado; números de línea del archivo actual):

| # | Archivo:línea | Qué afirma hoy | Cambio por C-33 |
|---|---|---|---|
| 1 | `frontend/src/features/auth/menuFor.test.ts:22` | `items.slice(1).every(...)`: todo ítem excepto "horarios-y-bloqueos" está `disabled === true` (administrador) | "catalogos" y "pacientes" pasan a habilitados con `path` `/catalogos` y `/pacientes` |
| 2 | `menuFor.test.ts:23` | ídem con `badge === "Próximamente"` (administrador) | ídem con `badge === null` |
| 3 | `menuFor.test.ts:38` | ídem para recepción (`!item.disabled && item.badge === null` para horarios, resto `disabled && "Próximamente"`) | idem |
| 4 | `menuFor.test.ts:55` | ídem para odontólogo | idem; tras C-33 el odontólogo no tiene ningún ítem deshabilitado (Agenda, Horarios, Catálogos, Pacientes habilitados) |
| 5 | `frontend/src/shared/components/AppShell.test.tsx:68` | `expect(adminButtons).toHaveLength(4)` | `2` (quedan Turnos y Usuarios y roles) |
| 6 | `AppShell.test.tsx:69-74` | `toEqual(["Turnos","Catálogos","Pacientes","Usuarios y roles"])` para admin | `["Turnos","Usuarios y roles"]` |
| 7 | `AppShell.test.tsx:100-104` | recepción: `.getAllByRole("button")...toEqual(["Turnos","Catálogos","Pacientes"])` | `["Turnos"]` |
| 8 | `AppShell.test.tsx:124-128` | odontólogo: `.getAllByRole("button")...toEqual(["Catálogos","Pacientes"])` | **no es solo un valor**: con cero botones `getAllByRole("button")` **lanza**. Hay que pasar a `queryAllByRole("button")` y esperar `[]` (o afirmar la ausencia). Es un cambio de forma, hay que documentarlo |
| 9 | `frontend/src/shared/components/AppShellNavigation.test.tsx:56` | `queryAllByRole("link")` `toHaveLength(2)` (Agenda + Horarios) para admin | `4` (Agenda, Horarios, Catálogos, Pacientes) |
| 10 | `AppShellNavigation.test.tsx:77` | `queryAllByRole("button", { name: /Próximamente/ })` `toHaveLength(4)` | `2` |
| 11 | `AppShellNavigation.test.tsx:81-86` | `toEqual(["Turnos","Catálogos","Pacientes","Usuarios y roles"])` | `["Turnos","Usuarios y roles"]` |

Total: **11 sentencias de aserción en 3 archivos** (4 en `menuFor.test.ts`, 4 en `AppShell.test.tsx`, 3 en `AppShellNavigation.test.tsx`); `AppShell.mobile.test.tsx` y `smoke.test.tsx` no cambian. Además, los títulos de los tests quedan desactualizados y tienen texto que habría que decidir si se retoca: `menuFor.test.ts:5` ("los otros 5 ítems deshabilitados con Próximamente", ya desactualizado desde C-32), `AppShell.test.tsx:48` ("el resto deshabilitado con Próximamente") y `AppShellNavigation.test.tsx:70`. Son cadenas de descripción, no aserciones; recomendación: no tocarlas (cambiarlas no cambia lo que se verifica) o tocarlas solo si el diff queda trivial, pero decirlo en el design.

Ningún otro test del repo depende de "Catálogos", "Pacientes" o "Próximamente" (verificado con búsqueda: las únicas apariciones fuera de `features/horarios/` están en `menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` y `PatientSearchGroup.tsx:90` que es el `aria-label="Pacientes encontrados"`, sin relación). No hay tests que afirmen que `/catalogos` o `/pacientes` caen en `NotFoundPage`.

Sobre el "sin costuras": la opción que sigue el criterio es la misma que tomó C-32: ampliar la expresión de `menuFor.ts` (o reemplazarla por una constante de módulo `ENABLED_MENU_IDS`, que es un refactor de producción sin parámetro nuevo) y **actualizar los tests porque el requisito cambió**. Descartado, igual que en C-32: `menuFor(role, enabledIds)` u otro parámetro/flag que mantenga viejos los tests.

### 2.4 Cómo inyectan `fetchFn` los tests existentes (regla C1, con ejemplo)

`frontend/src/features/horarios/HorariosPage.test.tsx:19-81`: define `const fetchFn: FetchFn = async (url) => { ... return new Response(JSON.stringify(...), { status: 200, headers: { "Content-Type": "application/json" } }) }`, arma `const client = createApiClient({ baseUrl: "http://localhost:8000/api", fetchFn })` (línea 81), `createMemoryRouter(createAppRoutes(clock), { initialEntries: [...] })` (línea 82) y renderiza `<AuthProvider tokenStore={createMemoryTokenStore("token-odontologo")} client={client}>` con `RouterProvider` (líneas 88-90). El `/auth/me` también se responde desde el mismo `fetchFn` (líneas 21-31). Un grep de `vi.mock|vi.spyOn|vi.stubGlobal|vi.useFakeTimers` en `frontend/src` no devuelve ningún archivo. Hay `waitFor` cortos sobre la UI (líneas 93, 229-246 del mismo archivo): son esperas de render, no polling largo.

---

## 3. Tamaño y recorte

### 3.1 Lo que pide cada pantalla (estimación)

Referencias de tamaño: C-31 = 25 tests nuevos en 5 archivos; C-32 apunta a "menos de 25" (16-18 en el diseño) en ~7 archivos de test y 6-7 componentes. Queda la ventana 15-19/11 con C-32 todavía en apply.

**Corte completo con 4 pantallas escritas por separado**: ~8-10 componentes por pantalla repetidos -> ~30-36 archivos de producción/CSS y ~32-40 tests. No entra.

### 3.2 Cortes propuestos

**Corte A. Componente genérico de catálogo + pacientes separado (los 4 recursos, mínimo de código).**
Un único `CatalogSection` (tabla + botón "Nuevo" + `Dialog` de formulario + confirmación de desactivar/reactivar) parametrizado por una configuración por entidad (`catalogConfigs.ts`: endpoint, columnas, campos del formulario, mapeo de payload, etiquetas). Se usa para profesionales, sillones y prestaciones. Pacientes va aparte (campos y búsqueda propios, sin desactivar).
- Producción (~14 archivos): `catalogosApi.ts` (tipos, parsers, `list/create/update/setActive` genéricos), `catalogConfigs.ts`, `CatalogosPage.tsx`, `CatalogSection.tsx`, `CatalogFormDialog.tsx`, `CatalogConfirmDialog.tsx`, `pacientesApi.ts`, `PacientesPage.tsx`, `PatientFormDialog.tsx`, `ActiveBadge.tsx`; más tocar `App.tsx` y `menuFor.ts`; ~6 CSS Modules.
- Tests: ~24-26 en ~9-10 archivos nuevos (detalle en §5) + 11 sentencias del menú.
- Cubre US-020, US-021, US-022 completas.

**Corte B. Solo pacientes y prestaciones.**
Pacientes completos y un `/catalogos` que solo gestiona prestaciones (es lo que alimenta duración por defecto de los turnos).
- ~10 archivos de producción, ~16-18 tests. Deja US-021 (profesionales y sillones) sin UI. Pierde la demostración de "desactivar un profesional/sillón impide nuevos turnos". Si se hace el genérico igual, sumar profesionales y sillones es una línea de configuración, así que B ahorra poco respecto de A.

**Corte C. Pacientes completos + catálogos de solo lectura.**
Pacientes con alta/edición/búsqueda; `/catalogos` con tres secciones de lectura (tabla con estado Activo/Inactivo), sin formulario ni desactivar.
- ~9-10 archivos de producción, ~14-16 tests. No cumple "Pantallas del administrador para profesionales, sillones y prestaciones" ni el test "desactivar" de `CHANGES.md:786`; US-020/021 quedarían solo por API.

**Corte D (escalonado, es A con orden de entrega)**: construir primero el paso 1 = menú + rutas + pacientes completos (corte C sin los catálogos), después el paso 2 = catálogos de lectura, después el paso 3 = formulario genérico, y el paso 4 = desactivar/reactivar. Si a mitad de camino falta tiempo, se archiva lo ya hecho en verde (equivale a C, o a A parcial).

### 3.3 Recomendación

**Corte A, ejecutado en el orden del corte D con punto de corte explícito.**

Justificación:

1. El costo marginal de profesionales y sillones sobre prestaciones es casi nulo si el componente es genérico (los tres comparten `{id, nombre, active}` y las mismas dos acciones `deactivate/reactivate`; solo cambian campos del formulario). Cortar a B ahorra poco y deja una historia (US-021) sin pantalla.
2. Pacientes es el único flujo operativo diario de recepción (alta, edición, búsqueda, DNI duplicado). Se hace primero y completo (US-022).
3. Los tests por entidad en el genérico se escriben **una vez** con una entidad (por ejemplo la prestación, que además tiene el campo numérico y 409 por nombre) más 1-2 tests de configuración de las otras (profesional con `licenseNumber`, sillón), no triplicados.
4. El orden D protege la entrega: C-33 es "lo más postergable" según `CHANGES.md:165`. Si el 17/11 no hay margen, se corta en el paso 2 (catálogos de lectura) y se documenta el recorte en el design (corte C), conservando el menú y las rutas ya habilitados.
5. Riesgo del genérico: sobre-configurar. Mitigación: la configuración es datos puros (sin render props ni abstracción de formularios); tres entidades fijas.

---

## 4. Decisiones (con opciones y recomendación por defecto)

Reglas que el plan respeta y que el design debe declarar:

- **Regla C1**: sin `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers ni MSW; sin `waitFor` largos; red solo con `createApiClient({ fetchFn })` (ejemplo real: `HorariosPage.test.tsx:19-90`); tests de CSS son estáticos (jsdom no mide anchos).
- **Tests existentes intactos** salvo el cambio de requisito del menú (11 sentencias, §2.3).
- **Un escenario = un test = una mutación** (mutación propia verificable y evidenciada con RED/GREEN).
- **Colores solo por tokens** (`var(--token)`, nunca HEX ni `rgb()`).
- **Foco visible** y controles de al menos 44 x 44 px; **nada comunicado solo por color** (Activo/Inactivo siempre con texto).
- La propuesta cumple todo esto; los puntos de fricción están marcados en cada decisión y en §6.

**D1. Rutas y navegación interna del catálogo.**
- Opciones: (a) `/catalogos` con una sola ruta y la sección elegida por query `?seccion=profesionales|sillones|prestaciones`; (b) subrutas `/catalogos/profesionales`, etc. (con redirección del índice); (c) ARIA `tablist` completo con flechas.
- **Por defecto: (a)**, igual que C-32 con `?professionalId=` y C-31 con `?view=chair`. Un grupo de enlaces `Link` a `?seccion=...` con `aria-current="page"` en el activo (no `role="tab"`: evita implementar teclado de tabs). Sección inválida o ausente = profesionales. Una sola entrada en `App.tsx` para `/catalogos` y otra para `/pacientes`.

**D2. Menú.**
- Opciones: (a) ampliar la expresión `enabled` con `|| catalogos || pacientes`; (b) constante de módulo `ENABLED_MENU_IDS` en `menuFor.ts` (sin parámetro); (c) seam `menuFor(role, enabledIds)` (descartado por C-32 D1 y por el criterio).
- **Por defecto: (b)** o (a) (decisión de estilo; ambas sin seam). Los tests existentes del menú se modifican por cambio de requisito: **11 sentencias en 3 archivos** (§2.3), documentadas en el design y en `docs/evidencias/diff-tests-existentes-C-33.txt`, **contando honestamente** (no repetir "una por archivo" de C-32). Se anota el cambio de forma en `AppShell.test.tsx:124-128` (`getAllByRole` lanza con cero botones). Los nuevos escenarios del menú van en **archivo nuevo** (no se agrega a los existentes).

**D3. Quién ve qué.**
- Opciones: (a) Catálogos y Pacientes visibles para los tres roles (ya lo definen `menuFor.ts:36-47` y la matriz RBAC: R); acciones de escritura según rol; (b) ocultar "Catálogos" a recepción y odontólogo (cambia `menuFor.ts` roles y más aserciones de menú).
- **Por defecto: (a)**. Matriz de UI:
  - Pacientes: administrador y recepción ven "Nuevo paciente" y "Editar"; odontólogo ve la lista y la búsqueda sin botones de escritura.
  - Catálogos: administrador ve "Nuevo", "Editar", "Desactivar/Reactivar"; recepción y odontólogo ven solo la lista, sin botones de escritura y un texto visible que lo indique ("Solo lectura" o equivalente; copy a definir en el spec).
  - La UI usa `user.role` de `useAuth()`; **el backend es la autoridad**: si por algún motivo igual llega un 403, se muestra su `message` literal en alerta sin cerrar sesión (mismo criterio que C-29/C-30 y C-32).

**D4. Contenedor del formulario.**
- Opciones: (a) `Dialog` (modal) para alta y edición; (b) panel inline o página aparte; (c) hoja inferior propia en móvil.
- **Por defecto: (a)**. La hoja inferior en `<= 640 px` ya la da `Dialog.tsx` (C-36). `labelledBy` único por diálogo, foco inicial en el primer campo, `returnFocusRef` al botón que lo abrió. Un solo diálogo sirve para "Nuevo" y "Editar" (título distinto, campos precargados). El test de "hoja inferior" sigue el modelo de `frontend/src/features/horarios/BlockFormDialog.mobile.test.tsx`.

**D5. Qué se valida en el cliente y qué en el backend.**
- Opciones: (a) el cliente solo valida **formato imposible de enviar** (duración no entera) y limita longitudes con `maxLength`; las reglas de negocio las informa el backend con su mensaje literal; (b) el cliente replica las reglas (DNI 7-8 dígitos, múltiplo de 5, etc.).
- **Por defecto: (a)** (`DD-06`: el dominio es la autoridad; criterio de C-29 "no repite las reglas en el cliente"). Concreto:
  - Nombre vacío: **se envía** y se muestra el 422 `EMPTY_NAME` literal ("El nombre del paciente no puede estar vacío."). No se inventa un mensaje propio.
  - DNI: sin validación de longitud ni de dígitos en el cliente; se muestra `INVALID_DNI` literal. El input acepta puntos y espacios (el backend los normaliza).
  - Duración: `inputMode="numeric"`; si el texto no es un entero (o está vacío) el cliente **no envía** y muestra un mensaje de formato propio (texto a fijar en el spec, por ejemplo "La duración debe ser un número entero de minutos.", marcado como mensaje del cliente, no del dominio) porque `Number("")` es `0` y mandarlo daría un 422 engañoso ("se recibió 0 minutos").
  - Múltiplo de 5, > 0 y <= 480: backend (`INVALID_DURATION` literal).
  - `maxLength` en los inputs según las columnas: nombres 255, `licenseNumber` 50, `phone` 50, `healthInsurance` 255, DNI 10 (8 dígitos + 2 puntos; se acepta también con espacios, ver R5).
  - `aria-invalid="true"` **solo** para errores 400 con `field` (misma lógica que `AppointmentFormDialog.tsx:182-188`); los 409/422 van en la alerta del diálogo con `role="alert"` y foco.

**D6. DNI duplicado y nombre duplicado (409).**
- Opciones: (a) alerta del diálogo con el mensaje literal del backend (código + mensaje, como `AppointmentFormDialog.tsx:213-230`) y **sin** `aria-invalid`; (b) marcar el campo DNI como inválido por 409.
- **Por defecto: (a)**. El diálogo queda abierto con los datos tipeados, la alerta recibe el foco y dice literalmente `Ya existe un paciente con el DNI 30.111.222.` (en el escenario de prueba, el DNI del seed). Idem `Ya existe una prestación con el nombre "Limpieza".` (usar nombres ficticios del spec).

**D7. Desactivar y reactivar.**
- Opciones: (a) confirmación **dentro del mismo diálogo** (patrón C-30: sin `window.confirm`, "Volver" o Escape no envían nada) para ambas acciones, con un solo componente `CatalogConfirmDialog` parametrizado; (b) confirmar solo desactivar y reactivar con un clic; (c) sin confirmación.
- **Por defecto: (a)**. Título y botones literales a fijar en el spec (modelo: `BlockDeleteDialog.tsx`: "Volver" y "Sí, ..."). Texto del diálogo de desactivar: dejar claro que no afecta turnos existentes (US-020 CA-3, US-021 CA-2). Tras éxito, cierra y refresca la lista. Errores (404, 403) en alerta dentro del diálogo, sin cerrar sesión. Como `deactivate`/`reactivate` son idempotentes, un doble envío no rompe nada (el botón queda `disabled` mientras envía igual).

**D8. Búsqueda de pacientes.**
- Opciones: (a) componente propio de la pantalla que consulta `GET /patients?query=` (con `encodeURIComponent`) al enviar el formulario (Enter o botón "Buscar"), carga inicial sin `query`; (b) reutilizar `PatientSearchGroup` (ver §2.2: radio picker, no sirve); (c) búsqueda al tipear con debounce.
- **Por defecto: (a)**. Sin debounce (con la regla C1 no hay fake timers para testearlo; además la API devuelve todo en una pasada). Estados: cargando (`LoadingState`), error con reintento (`ErrorState`), vacío ("No se encontraron pacientes" como en `PatientSearchGroup.tsx:75-77`, o `EmptyState`). Un `<label>` visible para el campo (a diferencia del `aria-label` solo-lectura-de-pantalla del picker).

**D9. Obra social y teléfono como texto libre; sin campos clínicos.**
- Por defecto: dos inputs de texto libre opcionales; si quedan vacíos se envía `null` (no `""`) para no persistir cadenas vacías. **No hay** catálogo de obras sociales ni campos clínicos (RN-PA-01, US-022 CA-2): el formulario tiene exactamente `fullName`, `dni`, `phone`, `healthInsurance`. Un test estático/estructural comprueba que el formulario expone solo esos cuatro campos.
- Datos de prueba y capturas: solo ficticios (RN-PA-02): los del seed o inventados claramente (p. ej. "Ana Pérez", "30111222").

**D10. Listado de catálogos: ¿se muestran los inactivos?**
- Opciones: (a) `GET` sin `active` (todos) con etiqueta "Activo"/"Inactivo" en texto; (b) solo activos con interruptor "Mostrar inactivos"; (c) solo activos.
- **Por defecto: (a)** (sin interruptor extra; el administrador necesita ver los inactivos para reactivarlos y para entender un 409 por nombre). La etiqueta combina texto y estilo por tokens, nunca solo color. Orden: el que devuelve la API.

**D11. Capa de datos.**
- **Por defecto**: archivos nuevos `catalogosApi.ts` y `pacientesApi.ts` (a imagen de `horariosApi.ts`), con parsers que devuelven `UNEXPECTED_RESPONSE_MESSAGE` si el JSON no calza (`agendaApi.ts` define `UNEXPECTED_RESPONSE_MESSAGE`). No ampliar `agendaApi.ts` (es de la agenda) ni tocar `client.ts`/`types.ts`. Después de cada mutación, **refrescar con un `GET` de la lista** (la API ordena; para pacientes se re-consulta con el `query` vigente) en vez de parchear estado local: menos lógica, orden correcto, y los tests solo necesitan un `fetchFn` por URL.

**D12. Responsive 1440 / 768 / 390.**
- Opciones: (a) `<table>` con `<caption>` y `scope="col"` en 768+ y filas apiladas en <= 640 px por CSS (celdas con `data-label`); (b) lista de tarjetas en todos los anchos; (c) tabla con scroll horizontal en el contenedor.
- **Por defecto: (a)**, siguiendo la skill ("tablas semánticas con `<caption>` y `scope="col"` cuando ofrezcas vista de lista"). Sin scroll horizontal de página a 390 px. jsdom no mide anchos: se agregan **tests estáticos de CSS** (como `agendaStyles.test.ts`) y **capturas reales a cargo de Claude** a 1440, 768 y 390 px, guardadas en `docs/evidencias/capturas/C-33-*.png` y nombradas en el verify. Controles >= 44 px.

**D13. Alcance del PageShell/título.**
- **Por defecto**: `PageShell` con `title` (es prop requerida, §6 R9) y un `<h1>` por pantalla ("Pacientes", "Catálogos"). Un solo `h1` por página.

**D14. Evidencias y gobernanza.**
- Governance de `CHANGES.md` es BAJO. Se mantienen RED/GREEN por test, mutación propia por escenario, validación OpenSpec estricta, capturas, y `diff-tests-existentes-C-33.txt` con las 11 sentencias del menú. `engram`: guardar `opsx/ui-catalogos-y-pacientes/explore`.

---

## 5. Escenarios propuestos para el corte recomendado (A en orden D)

Notación: **Dado / Cuando / Entonces**. Cada uno = un test = una mutación. Nombres de datos ficticios (RN-PA-02).

### 5.1 Pacientes (`/pacientes`)

1. **Lista y búsqueda**. Dado un paciente `recepcion` y la API con los 5 pacientes del seed, cuando abre `/pacientes`, entonces ve una tabla con nombre, DNI, teléfono y obra social; y cuando busca "Ana" y envía, entonces se pide `GET /patients?query=Ana`.
2. **Sin resultados**. Dado que la API devuelve `[]`, cuando busca "zzz", entonces se muestra "No se encontraron pacientes" (o el `EmptyState` acordado) y no queda la lista anterior.
3. **Alta correcta**. Dado `recepcion`, cuando pulsa "Nuevo paciente", completa nombre, DNI "30.111.999" y envía, entonces se hace `POST /patients` con `{fullName, dni, phone: null, healthInsurance: null}` camelCase, el diálogo se cierra y la lista se refresca.
4. **Edición**. Dado un paciente de la lista, cuando pulsa "Editar", cambia el teléfono y envía, entonces `PUT /patients/{id}` con los cuatro campos y el diálogo precarga los valores originales.
5. **Validación del backend mostrada: DNI inválido**. Dado el alta con DNI "123", cuando el backend responde `422 INVALID_DNI`, entonces la alerta muestra literalmente `El DNI no es válido (se recibió "123"): debe tener 7 u 8 dígitos, con o sin puntos.` y el diálogo sigue abierto.
6. **Validación del backend mostrada: nombre vacío**. Dado nombre en blanco, cuando el backend responde `422 EMPTY_NAME`, entonces se muestra `El nombre del paciente no puede estar vacío.`
7. **DNI duplicado**. Dado el DNI del seed "30111222", cuando el backend responde `409 DUPLICATE_DNI`, entonces la alerta (con `role="alert"` y foco) muestra `Ya existe un paciente con el DNI 30.111.222.` y el campo DNI **no** tiene `aria-invalid`.
8. **400 por campo**. Dado un `400` con `{field: "fullName", message: "Falta este dato."}`, entonces el campo nombre tiene `aria-invalid="true"` y el mensaje visible asociado.
9. **Odontólogo en solo lectura**. Dado `odontologo`, cuando abre `/pacientes`, entonces ve la lista y la búsqueda pero no "Nuevo paciente" ni "Editar".
10. **403 del backend**. Dado `recepcion` y un `403` al guardar, entonces la alerta muestra `No tiene permiso para actualizar pacientes.` sin cerrar sesión.

### 5.2 Catálogos (`/catalogos`)

11. **Sección por defecto y cambio**. Dado `administrador`, cuando abre `/catalogos`, entonces ve Profesionales y `GET /professionals`; cuando elige "Prestaciones" (`?seccion=prestaciones`), entonces ve `GET /services` con la duración por defecto y la etiqueta "Activo"/"Inactivo" en texto.
12. **Alta de prestación**. Dado `administrador`, cuando crea "Limpieza" con duración 30, entonces `POST /services` con `{name, defaultDurationMin: 30}` (número) y la lista se refresca.
13. **Duración inválida**. Dado `defaultDurationMin: 7`, cuando el backend responde `422 INVALID_DURATION`, entonces se muestra el mensaje literal (`La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.`).
14. **Formato de duración en el cliente**. Dada una duración vacía o "abc", cuando envía, entonces no se hace ninguna petición y se muestra el mensaje de formato del cliente.
15. **Nombre repetido (409)**. Dado un sillón nuevo con nombre existente, cuando el backend responde `409 DUPLICATE_NAME`, entonces la alerta muestra `Ya existe un sillón con el nombre "Sillón 1".` (nombre ficticio del seed o del test).
16. **Profesional con matrícula**. Dado `administrador`, cuando edita un profesional y cambia `licenseNumber`, entonces `PUT /professionals/{id}` con `{fullName, licenseNumber}`.
17. **Desactivar con confirmación**. Dado un sillón activo, cuando pulsa "Desactivar", entonces se abre la confirmación dentro del diálogo; "Volver" (o Escape) cierra sin enviar nada; "Sí, ..." envía `POST /chairs/{id}/deactivate` y la fila pasa a "Inactivo".
18. **Reactivar**. Dada una prestación inactiva, cuando confirma "Reactivar", entonces `POST /services/{id}/reactivate` y la fila pasa a "Activo".
19. **Solo lectura para recepción y odontólogo**. Dado `recepcion` (y por separado `odontologo`), cuando abre `/catalogos`, entonces ve las tablas sin "Nuevo", "Editar" ni "Desactivar".
20. **Error de carga con reintento**. Dado un error de red/`500` al listar, entonces se muestra `ErrorState` con "Reintentar" y, al reintentar, carga.

### 5.3 Menú y rutas

21. **Menú habilitado**. Dado cualquier rol, cuando carga el shell, entonces "Catálogos" y "Pacientes" son enlaces a `/catalogos` y `/pacientes` sin "Próximamente" (archivo de test **nuevo**; las 11 sentencias existentes se actualizan aparte).
22. **Rutas**. Dado un usuario autenticado, cuando navega a `/pacientes` y a `/catalogos`, entonces renderiza cada pantalla y no `NotFoundPage`.

### 5.4 Responsive y diseño

23. **Hoja inferior móvil del formulario** (`Dialog` con `isMobile`), modelo `BlockFormDialog.mobile.test.tsx`.
24. **Tests estáticos de CSS**: sin colores sueltos (HEX/`rgb`) en los CSS Modules nuevos, `:focus-visible` presente, objetivo táctil >= 44 px, fila apilada en `@media (max-width: 640px)`.
25. **Capturas reales (a cargo de Claude)** a **1440, 768 y 390 px** de: lista de pacientes, formulario con 409, estado vacío, catálogos con inactivos, confirmación de desactivar, hoja inferior en 390. No son tests.

Cantidad estimada: **~24 tests nuevos** en ~9 archivos de test, más 11 sentencias de aserción modificadas en 3 archivos de menú y ~14 archivos de producción nuevos o tocados.

---

## 6. Riesgos

| # | Riesgo | Probabilidad e impacto | Mitigación |
|---|---|---|---|
| R1 | **Plazo**: 4 días, C-32 aún en apply y compartiendo el árbol; C-33 es "lo más postergable" | Alta / medio | Corte A con orden D (pacientes primero, catálogos de lectura segundo, formulario/desactivar al final) y punto de corte documentado; no arrancar el apply de C-33 hasta que C-32 esté en verde y commiteado (el menú y `App.tsx` los toca C-32). |
| R2 | **Conflicto con C-32 en archivos compartidos** (`App.tsx`, `menuFor.ts`, 3 tests de menú, `tasks.md`) | Alta / medio | Aplicar C-33 sobre el estado commiteado de C-32; las líneas citadas en §2.3 pueden correrse. Re-verificar con `git diff` antes de editar. |
| R3 | **Criterio "una aserción por archivo" no es literal**: C-32 lo declara pero modificó 10 sentencias en 3 archivos (más una condicional por ítem en `menuFor.test.ts:22,23,38,55`). C-33 modifica 11 sentencias en 3 archivos y el caso del odontólogo (`getAllByRole` lanza con cero botones) cambia de forma | Media / medio (honestidad de la evidencia, no de la funcionalidad) | Declarar el conteo real en el design y en `diff-tests-existentes-C-33.txt`; no pretender "una por archivo". Sin seam. Evitar replicar el condicional por id en cada aserto: expresar el esperado directamente (listas explícitas) para que los tests describan el producto real. |
| R4 | **Mensajes en `menuFor.test.ts` desactualizados** (títulos con "5 ítems deshabilitados") | Baja / bajo | No tocar los títulos (no son aserciones) o decidirlo explícitamente en el design. |
| R5 | **Sin `max_length` en la API**: textos largos pueden dar error de base de datos (500 sin cuerpo clasificado) y llegarían al cliente como `kind: "unknown"` | Media / medio | `maxLength` en los inputs (D5) y mostrar un error genérico ("Respuesta inesperada del servidor." / `rawText`) con foco en alerta para cualquier `unknown`. Anotar como deuda del backend (fuera de alcance: C-33 no toca la API). Nota: `maxLength` del DNI debe admitir puntos (10). |
| R6 | **`GET /patients` sin paginación** | Baja en el MVP (5 pacientes de seed) / medio si crece | Declararlo en el design; la búsqueda ya acota. No paginar en C-33. |
| R7 | **Odontólogo en `/catalogos` y `/pacientes`**: el menú los muestra y la matriz RBAC permite leer; si la pantalla le ofrece botones de escritura el backend responderá 403 | Media / bajo | D3: ocultar escritura por rol y, por si acaso, mostrar el 403 literal sin cerrar sesión. Test 9 y 19. |
| R8 | **Mensajes de duplicado dependen de datos** (DNI con puntos de miles, nombre con espacios colapsados) | Baja / bajo | Citar literal desde el código (§1.2) y usar los DNI/nombres ficticios del seed en los tests. |
| R9 | **`PageShell` exige `title`** (`shared/components/PageShell.tsx`, prop `title: string` requerida) pero `HorariosPage.tsx:112` lo usa como `<PageShell>` sin título | Media / bajo (probable error de tipos que ya existe en el árbol de C-32) | No copiar ese patrón: `PageShell title="..."` como `AgendaPage.tsx:247` y `NotFoundPage.tsx:7`. Avisar al orquestador por si la calidad de C-32 (`tsc`) lo detecta. |
| R10 | **Genérico sobre-configurable**: tentación de abstraer el formulario con render props | Media / medio | Configuración de datos puros, tres entidades fijas, sin plugins. Si el componente supera ~250 líneas, partirlo. |
| R11 | **Foco y teclado en el `Dialog`**: `Dialog.tsx` usa `setTimeout` para la bandera de Escape (`Dialog.tsx:109-111`) y la corrección de C-30 (`closeHandledRef`) sigue siendo sensible | Baja / medio | Reusar sin modificar `Dialog.tsx`; tests de Escape solo para la confirmación (que ya cubre `Dialog.escape.test.tsx`). Cualquier cambio a `Dialog.tsx` sería un cambio de requisito sobre tests existentes: evitarlo. |
| R12 | **Datos de prueba reales o ambiguos** | Baja / alto (RN-PA-02) | Solo ficticios; revisar capturas antes de guardarlas. |
| R13 | **Estado inactivo sin texto visible** (solo color) | Baja / medio | Etiqueta "Activo"/"Inactivo" como texto siempre; test de que existe el texto. |
| R14 | **Desfase de roadmap**: `CHANGES.md:786` pide "desactivar" para pacientes pero no existe | Media / bajo | Dejar explícito en proposal/spec que "desactivar" aplica a profesionales, sillones y prestaciones; pacientes no tienen estado ni borrado. |
| R15 | **Tema oscuro**: no aplica (C-36 lo trasladó al backlog y fijó superficies claras en la app) | - | Sin trabajo. Lo que C-36 sí dejó para móvil: `Dialog` como hoja inferior `<= 640 px` con `max-height: 90dvh`, botones táctiles 44 px (spec `frontend-foundation`, "Modales de la aplicación como hoja inferior en celular", líneas 363+), cabecera compacta con botón "Menú" en `AppShell`, `PageShell` con espaciados compactados; C-36 está **completo y archivado** (`CHANGES.md:688`, archive `2026-11-14-ui-tema-oscuro-y-movil`). |

---

## 7. Resumen ejecutivo

- Contratos listos en backend (C-20): no hay que tocar la API. Particularidades: pacientes sin desactivar; profesionales sin 409; DNI/nombres duplicados vuelven `409` con mensaje literal; vacíos, DNI inválido y duración inválida vuelven `422` literal; `400` solo para campos faltantes o mal tipados ("Falta este dato." / "Dato inválido."); sin `max_length` en la API.
- El odontólogo **lee** pacientes y catálogos pero no escribe nada en ellos.
- Reutilizar: `Dialog` (hoja inferior ya resuelta por C-36), `LoadingState`/`ErrorState`/`EmptyState`, patrón de alertas de `AppointmentFormDialog`, patrón de confirmación de C-30 (`BlockDeleteDialog`), `createApiClient({ fetchFn })`. Falta: rutas, capa de API de los cuatro recursos, pantallas, etiqueta Activo/Inactivo. `PatientSearchGroup` no se reutiliza.
- Menú: 11 sentencias de aserción en 3 archivos (`menuFor.test.ts` 22, 23, 38, 55; `AppShell.test.tsx` 68, 69-74, 100-104, 124-128; `AppShellNavigation.test.tsx` 56, 77, 81-86), sin seam; `AppShell.mobile.test.tsx` no cambia.
- Recomendación: corte A (genérico para catálogos + pacientes aparte), ejecutado en el orden de D (pacientes, catálogos de lectura, formulario, desactivar) con punto de corte; ~24 tests nuevos, ~14 archivos de producción.
