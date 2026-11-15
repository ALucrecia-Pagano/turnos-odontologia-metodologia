# Exploración C-32: UI de Horarios y Bloqueos (`ui-horarios-y-bloqueos`)

> **Fecha**: 2026-11-14  
> **Rama**: `c31-apply` (con el archivado de C-31 en curso en el mismo árbol de trabajo).  
> **Estado previo**: C-21 (API de horarios y bloqueos) cerrado; C-26 a C-31 disponibles en el frontend.  
> **Modo**: Solo lectura del código base. Único archivo redactado: `docs/evidencias/explore-C-32.md`.  
> **Skills y MCPs consultados**:
> - **Skill `appointment-frontend-ux`** (`.agents/skills/appointment-frontend-ux/SKILL.md`): regla C1 (fetch y `Clock` inyectados, sin mocks de módulo ni fake timers), tokens de diseño, accesibilidad con estado por texto visible, zona horaria de la API, verificación visual a 1440 / 768 / 390 px y autoridad final del dominio.
> - **MCP Context7**: **no fue necesario**. C-32 no introduce librerías nuevas; reutiliza React 18.3.1, React Router 6.30.6, Vitest 3.2.7 y el `<dialog>` nativo ya encapsulado en `Dialog.tsx`.
> - **Aviso de concurrencia**: no se tocaron `CHANGES.md`, `openspec/specs/frontend-agenda/spec.md`, `docs/evidencias/verify-C-31.md`, las capturas `C-31-*` ni el directorio de archivo de C-31 porque el otro agente los está modificando.

---

## 1. Contratos reales y turnos afectados

Todo lo que necesita la UI ya existe en el backend. **C-32 no requiere cambios de API ni de dominio.**

### 1.1 Endpoints

| Uso en la pantalla | Endpoint | Permiso y scope | Entrada | Respuesta exitosa | Errores relevantes |
|---|---|---|---|---|---|
| Leer tramos semanales | `GET /api/professionals/{id}/working-hours` | `WORKING_HOURS READ`: odontólogo `OWN`, recepción y admin `ALL` (`backend/app/auth/permissions.py:48-50`) | Sin cuerpo | `200` con `list[WorkingHoursSlotResponse]`: `[{weekday, start, end}]`, ordenado por día y hora de inicio | `401`; `403` `FORBIDDEN_OPERATION`; `404 NOT_FOUND` (`Profesional no encontrado.`) |
| Reemplazar la semana completa | `PUT /api/professionals/{id}/working-hours` | `WORKING_HOURS UPDATE`: odontólogo `OWN`, admin `ALL` | **Array crudo** `[{weekday, start, end}]`, no un objeto envoltorio (`backend/app/api/working_hours.py:55-117`) | `200` `{workingHours, appointmentsOutsideHours}` | `400` formato/estructura; `403`; `404`; `422 INVALID_WORKING_HOURS`; `422 OVERLAPPING_WORKING_HOURS` |
| Listar bloqueos | `GET /api/professionals/{id}/blocks?from=&to=` | `BLOCK READ`: odontólogo `OWN`, recepción y admin `ALL` | `from` y `to` opcionales; si vienen, ISO con offset (`BlocksQuery`, `backend/app/api/schemas.py:255-266`). Sin rango devuelve **todos** | `200` `list[BlockResponse]`: `[{id, professionalId, startAt, endAt, reason}]`, ordenado por inicio e id | `400` fecha sin zona o rango malformado; `403`; `404` |
| Crear bloqueo | `POST /api/professionals/{id}/blocks` | `BLOCK CREATE`: odontólogo `OWN`, admin `ALL` | `{startAt, endAt, reason?}`; instantes ISO **con offset obligatorio** (`BlockInput`, `schemas.py:221-234`) | `201` `{block, affectedAppointments}` | `400` fecha sin zona; `403`; `404`; `422 INVALID_BLOCK` |
| Eliminar bloqueo | `DELETE /api/blocks/{block_id}` | `BLOCK DELETE`: odontólogo `OWN`, admin `ALL` | Path UUID | `200` con el `BlockResponse` eliminado | `400` UUID malformado; `403`; `404` (`Bloqueo no encontrado.`) |
| Selector de profesional | `GET /api/professionals` | `PROFESSIONAL READ`: los tres roles `ALL` | Query opcional `active=true` | `200` `[{id, fullName, licenseNumber, active}]` | `401` |

Detalles que condicionan la UI:

- **`GET` de horarios resuelve el 404 antes del 403**: primero llama `get_working_hours(...)` y después `ensure_own_professional(...)` (`backend/app/api/working_hours.py:39-40`). Un profesional inexistente da `404`; uno existente ajeno a un odontólogo da `403`.
- **`PUT` y `POST` validan la existencia del profesional antes del permiso** (`working_hours.py:80-84`, `blocks.py:69-73`); `DELETE` busca el bloqueo y recién después valida el scope con `Resource.BLOCK, Action.DELETE` (`blocks.py:122-126`).
- **`start` admite `00:00`–`23:59`; `end` admite `00:00`–`24:00`** (`schemas.py:163-190`). El dominio también acepta `24:00` como fin (`_format_minute`, `backend/app/domain/rules/working_hours.py:45-47`). Un `<input type="time">` no es confiable para `24:00`; ver D3.
- **`PUT` reemplaza toda la semana**, no hace merge. Enviar una lista vacía deja al profesional sin horario; el dominio lo acepta.
- **Los tramos se identifican por posición desde 1 en el orden recibido** (`validate_working_hours`, `working_hours.py:81-125`). Si la UI agrupa y ordena distinto de lo que envía, el mensaje “El tramo 3…” puede no coincidir con lo que ve el usuario. La UI debe enviar en el mismo orden visible.
- **Los bloqueos de `GET` sin `from/to` vuelven todos**; no hay paginación. Es aceptable para el MVP, pero la pantalla debe evitar tablas gigantes (ver D6).
- **`GET /api/professionals`** ya es consumido por `fetchProfessionals` (`frontend/src/features/agenda/agendaApi.ts:281-301`) y devuelve `licenseNumber` y `active`. Para el selector alcanza con filtrar `active` en el cliente; no hace falta query nueva.

### 1.2 Forma exacta de los turnos afectados

Ambas respuestas usan la misma pieza (`AffectedAppointmentResponse`, `schemas.py:200-210`), serializada en camelCase:

```json
{
  "id": "uuid",
  "patientId": "uuid",
  "patientName": "Ana Pérez",
  "chairId": "uuid",
  "startAt": "2026-11-16T13:00:00Z",
  "endAt": "2026-11-16T13:30:00Z",
  "status": "confirmado"
}
```

- **Horario**: el campo contenedor es **`appointmentsOutsideHours`** (`WorkingHoursResponse`, `schemas.py:212-219`). Significa “turnos **futuros** que quedan **fuera** del horario nuevo”, no “turnos pisados”. Se calculan desde `now` hasta `now + 90 días`, solo con estados que ocupan agenda y con inicio `>= now` (`backend/app/domain/rules/working_hours.py:227-267`). No se cancelan ni se mueven.
- **Bloqueo**: el campo contenedor es **`affectedAppointments`** (`BlockCreateResponse`, `schemas.py:246-252`). Significa “turnos que se **solapan** con el bloqueo”, del mismo profesional y en estado que ocupa agenda, sin filtro de futuro (`backend/app/domain/rules/blocks.py:134-162`). Tampoco se cancelan.
- **No incluye** `professionalId`, `professionalName` ni `chairName`. Sí incluye `chairId`, pero para el aviso alcanza con paciente, fecha/hora local y estado; mostrar el sillón exigiría otra llamada a `/chairs`.
- Orden estable: `(start_at, str(id))` en ambos casos.
- `startAt`/`endAt` son UTC con formato `YYYY-MM-DDTHH:MM:SSZ` (`format_utc_iso`, `schemas.py:14-17`). La UI **debe** convertirlos con la zona de la aplicación, nunca con la del navegador.
- Los estados son los mismos del dominio (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`) y encajan con `StatusBadge`.

### 1.3 Mensajes literales que la UI debe mostrar sin reformular

- Tramo inválido: `El tramo {posición} no es válido: {razones}.`  
  Razones (`working_hours.py:40-67`): `el día de la semana debe estar entre 1 (lunes) y 7 (domingo)`, `el inicio y el fin deben estar entre 00:00 y 24:00`, `el inicio debe ser anterior al fin`.
- Solapamiento: `Los tramos {a} y {b} del {día} se solapan: de {inicio1} a {fin1} y de {inicio2} a {fin2}.` (`working_hours.py:111-122`). Ejemplo real:
  `Los tramos 1 y 2 del lunes se solapan: de 09:00 a 12:00 y de 11:00 a 13:00.`
- Bloqueo inválido: `El bloqueo no es válido: el inicio debe ser anterior al fin.` (`backend/app/domain/rules/blocks.py:21`).
- Sin permiso: `No tiene permiso para leer horarios.` / `No tiene permiso para actualizar horarios.` / `No tiene permiso para crear bloqueos.` / `No tiene permiso para borrar bloqueos.` (`backend/app/auth/permissions.py:91-98`).
- Lo ideal es renderizar los mensajes con `getApiErrorMessages` (`frontend/src/shared/api/errors.ts:7-23`) dentro de `ErrorState` (`role="alert"`), tal como ya hacen la agenda y los diálogos de turnos.

### 1.4 Códigos HTTP

- `400`: cuerpo/query malformado (`{errors:[{field,type,message}]}`).
- `401`: lo maneja `AuthContext`; la pantalla no debe duplicar el mensaje.
- `403`: `{violations:[{code:"FORBIDDEN_OPERATION", message}]}`; se muestra sin cerrar sesión.
- `404`: `{code:"NOT_FOUND", message}`.
- `409`: no aplica a estos endpoints (horarios/bloqueos usan `422`).
- `422`: `{violations:[...]}` para `INVALID_WORKING_HOURS`, `OVERLAPPING_WORKING_HOURS`, `INVALID_BLOCK` (`backend/app/api/errors.py:11-35`).

---

## 2. Reutilización real y faltantes

### 2.1 Lo que ya existe y conviene reutilizar

| Necesidad | Pieza existente | Uso en C-32 |
|---|---|---|
| Llamadas HTTP y parseo de errores | `frontend/src/shared/api/client.ts`, `shared/api/errors.ts`, `shared/api/types.ts` | Mismo `ApiClient` de `AuthContext`; `getApiErrorMessages` |
| Estado de carga / error / vacío | `LoadingState.tsx` (`role="status"`, `aria-live="polite"`), `ErrorState.tsx` (`role="alert"`), `EmptyState.tsx` | Carga inicial, fallo con “Reintentar”, listas vacías |
| Diálogo | `shared/components/Dialog.tsx` y `Dialog.module.css` | Alta de bloqueo y confirmación de borrado; en ≤640 px ya se comporta como hoja inferior |
| Estado del turno afectado | `StatusBadge.tsx` + `APPOINTMENT_STATUS_TOKENS` | Mostrar el estado del turno afectado con texto visible |
| Fecha/hora local | `agendaTime.ts`: `formatLocalDate`, `formatLocalTime`, `formatMinutesToHHMM`, `parseHHMM` | Formatear `startAt/endAt` del aviso y bloques |
| Zona horaria de respaldo | `agendaConfig.ts`: `DEFAULT_AGENDA_TIMEZONE = "America/Argentina/Buenos_Aires"` | Ver D6; el backend no expone `timezone` en estos endpoints |
| Conversión local → instante con offset | `buildStartAtIso(dateStr, timeStr, timeZone)` exportado desde `AppointmentFormDialog.tsx:34-56` (ya reutilizado por `AppointmentRescheduleDialog.tsx:12,100`) | Alta de bloqueo desde `datetime-local` |
| Confirmación dentro del diálogo | Patrón C-30 en `AppointmentDetailDialog.tsx:250-265`: “¿Confirma que desea cancelar…?”, “Confirmar cancelación”, “Volver al detalle” | Confirmación de borrado de bloqueo |
| Catálogo de profesionales | `agendaApi.ts:281-301` (`fetchProfessionals`) | Selector de admin/recepción; filtrar `active` |
| Patrón de pantalla | `PageShell`, `AgendaPage` (loading/error/status) | Estructura de la página y anuncios `aria-live` |
| Patrón de tests | `AuthProvider` + `createMemoryTokenStore` + `fetchFn` inyectado, usado en `App.test.tsx` y tests de agenda | Regla C1, sin mocks de módulo |

### 2.2 Lo que falta

- No existe ruta `/horarios-y-bloqueos` en `frontend/src/App.tsx:17-43`.
- No existe ningún módulo de API para horarios ni bloqueos en el frontend.
- No existe pantalla, hook, componentes ni estilos para esta funcionalidad.
- **El ítem de menú ya existe pero está deshabilitado**: `menuFor.ts:44-49` define “Horarios y bloqueos” con path `/horarios-y-bloqueos` y roles de los tres actores, pero `menuFor.ts:57-67` habilita únicamente `item.id === "agenda"`; el resto queda `disabled: true` con badge `"Próximamente"`.

### 2.3 Tests existentes que dependen de “Próximamente” (restricción dura)

| Archivo | Aserción que se rompería si se habilita el ítem sin más |
|---|---|
| `frontend/src/features/auth/menuFor.test.ts:22-23` | Admin: `items.slice(1).every(item => item.disabled === true)` y badge `"Próximamente"` |
| `frontend/src/features/auth/menuFor.test.ts:38-40` | Recepción: todos los ítems posteriores a Agenda deshabilitados |
| `frontend/src/features/auth/menuFor.test.ts:55-57` | Odontólogo: ídem |
| `frontend/src/shared/components/AppShell.test.tsx:67-79` | Admin: 5 botones deshabilitados con `data-menu-item` “Turnos”, “Horarios y bloqueos”, “Catálogos”, “Pacientes”, “Usuarios y roles” |
| `frontend/src/shared/components/AppShell.test.tsx:101-129` | Recepción: 4 botones deshabilitados; odontólogo: 3 |
| `frontend/src/shared/components/AppShellNavigation.test.tsx:70-102` | `within(nav).queryAllByRole("link")` tiene largo 1; los 5 botones deshabilitados conservan `Próximamente` |
| `frontend/src/shared/components/AppShell.mobile.test.tsx` | Menú móvil con los mismos ítems deshabilitados |

**Conclusión**: con la firma actual `menuFor(role)` es **imposible** habilitar “Horarios y bloqueos” y mantener esos tests sin modificarlos. Las alternativas están en D1 y se dejan como duda explícita.

### 2.4 Impacto de agregar la ruta

Agregar `{ path: "horarios-y-bloqueos", element: <HorariosPage /> }` dentro del `AppShell` de `App.tsx` **no rompe** los tests actuales:

- `App.test.tsx:97-106` prueba una ruta desconocida distinta (`/ruta-que-no-existe`) y sigue cayendo en `NotFoundPage`.
- Los tests de `AppShell` renderizan `AppShell` directamente, no `createAppRoutes`.
- Los tests de landing usan `createAppRoutes` pero no inspeccionan el menú.

---

## 3. Decisiones de diseño (opciones y recomendación por defecto)

### D1 — Ruta y habilitación del ítem de menú

**Contexto**: la ruta no existe y el ítem de menú está bloqueado por tests que exigen “Próximamente”.

**Opciones**:

- **A — Solo ruta, menú sigue deshabilitado.** Se agrega `/horarios-y-bloqueos` dentro del `AppShell`; la pantalla se alcanza por URL directa y desde un change posterior que habilite el menú. No se toca ningún test existente.
  - Ventaja: cero riesgo de regresión y cero tests que mientan.
  - Desventaja: la funcionalidad no es descubrible desde la navegación; para el TP queda “escondida”.
- **B — Seam de configuración sin tocar tests.** `menuFor(role, enabledIds = ["agenda"])` y `AppShell({ enabledMenuIds = ["agenda"] })`; `createAppRoutes` pasa `["agenda", "horarios-y-bloqueos"]`. Los tests que renderizan `AppShell` sin la prop siguen viendo “Próximamente”; un test **nuevo** que monta `createAppRoutes` verifica el enlace real.
  - Ventaja: la pantalla es alcanzable en la app y no se modifica ningún test existente.
  - Desventaja: los tests unitarios del shell dejan de describir el menú real; es una bandera de features encubierta.
- **C — Habilitar en `menuFor` y actualizar los tests.** Es la solución conceptualmente más limpia, pero **viola la regla de “tests existentes intactos”**: obliga a editar `menuFor.test.ts`, `AppShell.test.tsx`, `AppShellNavigation.test.tsx` (y probablemente `AppShell.mobile.test.tsx`).

**Recomendación por defecto**: **B**, dejando constancia de la duda. Es la única forma de que la pantalla sea alcanzable sin romper los tests. Si la autora autoriza modificar los tests, **C** es preferible a largo plazo; si no quiere ningún seam, **A** es el fallback más conservador. **No** se recomienda un flag por `import.meta.env` porque el menú real dependería del modo de build y los tests dejarían de representar producción.

### D2 — Quién ve qué y selección de profesional

**Contexto**: RBAC de la KB (`03_actores_y_roles.md:26-27`): odontólogo CRU/CRUD de lo propio, recepción lectura, admin CRUD.

**Opciones**:

- **A (recomendada)**:
  - **Odontólogo**: target = `user.professionalId`; **sin selector**; edición habilitada.
  - **Administrador**: selector de profesionales **activos**; edición habilitada sobre el seleccionado.
  - **Recepción**: selector de profesionales activos; **solo lectura** (sin agregar/quitar/guardar/crear/eliminar).
  - `?professionalId=` se refleja en la URL con `replace` para que el enlace sea compartible. Si falta, admin/recepción usan el primer profesional activo.
  - **Odontólogo con `?professionalId=` ajeno**: la página **no reescribe** el target; hace la request y deja que el backend responda `403`, mostrando el error sin ofrecer edición. Así el dominio sigue siendo la autoridad y se cubre el escenario pedido.
- **B**: selector solo para admin; recepción ve el primero y no puede cambiar. Más simple, pero peor para recepción, que necesita consultar a cualquiera.
- **C**: odontólogo también con selector, pero deshabilitando los ajenos en el cliente. Duplica la regla y puede divergir del backend.

**Recomendación**: **A**. Si `user.professionalId` es `null` para un odontólogo, mostrar `ErrorState` con un mensaje local (“Tu usuario no tiene un profesional asociado.”) y no llamar a la API.

### D3 — Edición de los tramos semanales

**Contexto**: `PUT` reemplaza toda la semana; el dominio identifica los tramos por posición.

**Opciones**:

- **A (recomendada)**:
  - Siete secciones fijas, lunes a domingo (weekday 1..7), en ese orden, cada una con `<fieldset><legend>`.
  - Cada tramo es una fila con **inicio** y **fin**; “Agregar tramo” agrega al final del día; “Quitar” elimina esa fila.
  - Inputs de **texto** con `inputMode="numeric"`, placeholder `HH:MM` y ayuda “Formato HH:MM; el fin puede ser 24:00”. Evitar `type="time"` porque no garantiza `24:00`.
  - Un único botón “Guardar horario” envía **toda** la semana como array crudo, en el orden visible (lunes→domingo y, dentro de cada día, el orden de las filas).
  - Los tramos se muestran en el orden que devuelve `GET`; no se reordenan silenciosamente.
- **B**: guardar por día con un `PUT` parcial. **No existe** endpoint parcial; obligaría a enviar toda la semana igual. Se descarta.
- **C**: usar `type="time"` y perder el soporte de `24:00`. Se descarta por incompatibilidad con el contrato.

**Recomendación**: **A**. Permitir guardar una semana vacía (sin horarios) es válido para el dominio; si se quiere evitar el error humano, mostrar una confirmación “El profesional quedará sin horario de atención”, pero no bloquearlo en el cliente.

### D4 — Validación de solapes: cliente vs. backend

**Contexto**: el backend ya devuelve `422` con mensajes explicativos y posiciones.

**Opciones**:

- **A (recomendada)**: **no duplicar** la validación de solapes ni la de `inicio >= fin` en el cliente. El cliente solo evita enviar filas completamente vacías (validación de formulario) y muestra los `violations` del backend tal cual, dentro de `ErrorState` (`role="alert"`). Se conserva el orden de envío para que “tramo N” coincida.
- **B**: validar solapes en el cliente antes de enviar. Da feedback más rápido, pero duplica RN-DI-02 y puede divergir (por ejemplo, tramos contiguos que no se solapan, o `24:00`).
- **C**: validar en cliente y además en backend. La duplicación sigue siendo un riesgo de mantenimiento.

**Recomendación**: **A**, alineado con la regla dura “la UI puede anticipar errores, pero el rechazo definitivo es del dominio”. El test de solapamiento debe usar el mensaje literal del backend, no un texto propio del frontend.

### D5 — Aviso de turnos afectados (horario y bloqueo)

**Contexto**: guardar un horario o crear un bloqueo **no** cancela turnos; hay que informar cuáles quedan comprometidos.

**Opciones**:

- **A (recomendada)**: un componente compartido `AffectedAppointments` para ambas respuestas.
  - Horario: título **“Turnos futuros fuera del horario (N)”**; usa `appointmentsOutsideHours`.
  - Bloqueo: título **“Turnos que pisan el bloqueo (N)”**; usa `affectedAppointments`.
  - Contenedor `role="status"` con `aria-live="polite"` (es una advertencia informativa, no un error). Errores de API siguen en `role="alert"`.
  - Cada ítem: fecha y hora local (`dd/mm/aaaa HH:MM–HH:MM`), nombre del paciente y `StatusBadge`; texto visible, nunca solo color.
  - Nota fija: “El turno sigue reservado; reprogramalo desde la agenda.” (el backend no cancela).
  - Si la lista viene vacía, no se renderiza la sección; solo el mensaje de éxito (“Horario guardado.” / “Bloqueo creado.”).
- **B**: usar `role="alert"` también para la lista. Más intrusivo y semánticamente incorrecto: no hubo error.
- **C**: mostrar la lista en un modal aparte. Agrega fricción y otro diálogo; no se justifica.

**Recomendación**: **A**. El test de “aviso de afectados” debe verificar el título, el paciente, la hora local convertida y el estado, y que **no** aparezca “Turno cancelado” ni una acción de cancelación.

### D6 — Lista y alta de bloqueos

**Contexto**: `GET` sin rango devuelve todos los bloqueos; el alta requiere convertir `datetime-local` a un instante con offset.

**Opciones**:

- **A (recomendada)**:
  - Lista de todos los bloqueos del profesional, en el orden del backend (inicio ascendente), con fecha/hora local, motivo y botón “Eliminar bloqueo”. Sin paginación en el MVP.
  - Los bloqueos pasados se muestran igual, con la etiqueta textual “Finalizado” (no solo color); se pueden eliminar.
  - “Nuevo bloqueo” abre el `Dialog` existente con **inicio** y **fin** `datetime-local` y **motivo** opcional.
  - La conversión local→UTC usa `buildStartAtIso(fecha, hora, timeZone)`; la UI envía `startAt`/`endAt` con offset (`-03:00`), que el backend acepta.
  - Validación en cliente: solo campos obligatorios y formato del `datetime-local`; `inicio >= fin` lo rechaza el backend con `422 INVALID_BLOCK`.
  - Al crear: cerrar el diálogo, recargar la lista y mostrar el aviso de afectados (D5) y “Bloqueo creado.”.
- **B**: listar solo bloqueos futuros (`from=now`). Más corto, pero impide ver/eliminar los pasados y complica el test.
- **C**: usar dos inputs separados de fecha y hora. Más control, más campos y más errores; `datetime-local` alcanza.

**Zona horaria**: no hay endpoint que devuelva `timezone` en estos contratos. Opciones:
- **A (recomendada para C-32)**: aceptar una prop `timezone` con `DEFAULT_AGENDA_TIMEZONE` por defecto (el backend fija `APP_TIMEZONE` en `America/Argentina/Buenos_Aires`, DD-07) y usarla para mostrar y convertir. Los tests inyectan el valor.
- **B**: pedir `GET /api/agenda` solo para leer `timezone`. Cumple literalmente “timezone de la API”, pero agrega una request y un estado de error ajenos a la pantalla.
- **C**: agregar `timezone` a las respuestas de horarios/bloqueos. Es un cambio de backend fuera del alcance de C-32 (C-21 ya está cerrado).

**Recomendación**: **A**, dejando anotado el riesgo de que un cambio de `APP_TIMEZONE` en el backend no se refleje automáticamente. Si la autora exige la zona desde la API, **B** es la alternativa sin tocar backend.

### D7 — Eliminar un bloqueo

**Contexto**: `DELETE` no devuelve afectados y es irreversible.

**Opciones**:

- **A (recomendada)**: confirmación dentro del `Dialog`, con el patrón de C-30 (`AppointmentDetailDialog.tsx:250-265`):
  - Pregunta: “¿Eliminar este bloqueo del {fecha} de {inicio} a {fin}?”
  - Acciones: “Sí, eliminar bloqueo” (principal) y “Volver” (secundaria).
  - Al confirmar: `DELETE`; si `200`, cerrar el diálogo, quitar la fila y anunciar “Bloqueo eliminado.” en `role="status"`; si `403/404`, mantener el diálogo abierto y mostrar `ErrorState` (`role="alert"`).
  - Recepción no ve el botón.
- **B**: borrar sin confirmación. Riesgo de pérdida accidental; se descarta.
- **C**: `window.confirm`. Rompe el patrón visual y la accesibilidad probada; se descarta.

**Recomendación**: **A**. El test debe verificar que el `DELETE` **no** se dispara hasta confirmar, y que la fila desaparece y se anuncia el éxito.

### D8 — Carga, vacío, error y reintento

**Opciones**:

- **A (recomendada)**:
  - `LoadingState` mientras se cargan profesionales/horarios/bloqueos.
  - `ErrorState` con “Reintentar” para fallos de red o `5xx`; mensajes de la API tal cual para `403/404/422`.
  - `401` se delega en `AuthContext` (no se muestra error local).
  - `403` se muestra sin cerrar sesión.
  - Listas vacías: “Sin tramos cargados para este día.” / “No hay bloqueos para este profesional.”
  - Botones de mutación deshabilitados y con texto “Guardando…” / “Creando…” mientras hay request; sin mutaciones optimistas.
- **B**: un único estado global de error para toda la pantalla. Pierde granularidad y mezcla fallos de horarios con bloqueos.
- **C**: no ofrecer reintento. Peor UX ante fallos transitorios.

**Recomendación**: **A**. Mantener los estados de horarios y bloqueos separados para que un fallo de bloqueos no oculte el horario ya cargado.

### D9 — Accesibilidad

**Opciones**:

- **A (recomendada)**: `fieldset/legend` por día; labels explícitos (“Inicio lunes”, “Fin lunes”); botones con el día en el nombre accesible (“Agregar tramo del lunes”, “Quitar tramo 2 del lunes”); foco visible; áreas táctiles ≥44 px; errores asociados con `aria-describedby`; `role="alert"` solo para errores; `role="status"` para éxito/afectados; estados con texto (incluido `StatusBadge` y “Finalizado”).
- **B**: una tabla editable. Más compacta en escritorio, pero difícil de operar con teclado y de adaptar a 390 px.

**Recomendación**: **A**. La tabla editable se descarta por accesibilidad y responsividad.

### D10 — Adaptabilidad 1440 / 768 / 390

**Opciones**:

- **A (recomendada)**:
  - 1440 px: dos columnas (horarios a la izquierda, bloqueos a la derecha); los siete días en grilla de 2–3 columnas.
  - 768 px: una columna; días en grilla de 2; bloques debajo.
  - 390 px: una columna; cada día apilado; filas de tramo con inputs y botón “Quitar” en dos líneas sin overflow horizontal; el `Dialog` ya es hoja inferior a ≤640 px (`Dialog.module.css:28-38`).
  - Solo tokens de `tokens.css`; sin colores crudos nuevos. Verificación visual real con capturas a las tres resoluciones antes de archivar.
- **B**: una sola columna en todas las resoluciones. Simple, pero desperdicia 1440 px.
- **C**: tabla con scroll horizontal a 390 px. Viola la comodidad táctil y la prioridad de lectura.

**Recomendación**: **A**. Los tests de jsdom no miden layout; la verificación visual es obligatoria (skill `appointment-frontend-ux`).

---

## 4. Escenarios propuestos (Dado / Cuando / Entonces)

> Regla: un escenario = un test = una mutación. Los tests nuevos van en archivos nuevos; no se modifica ningún test existente.

### E1 — Alta de tramos del odontólogo (camino feliz)

- **Dado** un odontólogo autenticado con `professionalId = P` y `GET /professionals/P/working-hours` devuelve `[]`,
- **Cuando** agrega el tramo “lunes 09:00–13:00” y presiona “Guardar horario”,
- **Entonces** se envía `PUT /professionals/P/working-hours` con `[{weekday:1,start:"09:00",end:"13:00"}]`, se muestra “Horario guardado.” en `role="status"` y la lista queda con ese tramo.

### E2 — Selección de profesional del administrador

- **Dado** un administrador con dos profesionales (uno activo y uno inactivo),
- **Cuando** abre la pantalla sin `professionalId`,
- **Entonces** el selector ofrece **solo el activo**, se carga su horario y, al cambiar de profesional, la URL y los datos se actualizan sin recargar la página.

### E3 — Error por tramos solapados (mensaje literal del backend)

- **Dado** que el usuario carga dos tramos del lunes que se pisan,
- **Cuando** guarda y el backend responde `422` con `OVERLAPPING_WORKING_HOURS`,
- **Entonces** se muestra en `role="alert"` el texto exacto:
  `Los tramos 1 y 2 del lunes se solapan: de 09:00 a 12:00 y de 11:00 a 13:00.`,
  no aparece “Horario guardado.” y no se modifica la lista local.

### E4 — Aviso de turnos afectados al guardar horario

- **Dado** un `PUT` exitoso cuyo `appointmentsOutsideHours` contiene el turno de Ana Pérez (10:00–10:30 local, `confirmado`),
- **Cuando** se guarda el horario,
- **Entonces** se muestra “Turnos futuros fuera del horario (1)” en `role="status"`, el ítem “16/11/2026 10:00–10:30 · Ana Pérez · Confirmado” y la nota “El turno sigue reservado; reprogramalo desde la agenda.”, sin ninguna acción de cancelar.

### E5 — Alta de bloqueo con turnos afectados

- **Dado** el diálogo “Nuevo bloqueo” con inicio `16/11/2026 10:00`, fin `12:00` y motivo “Congreso”,
- **Cuando** se envía y el backend responde `201` con `affectedAppointments` que incluye a Ana Pérez,
- **Entonces** el cuerpo enviado contiene `startAt`/`endAt` con offset (`2026-11-16T10:00:00-03:00` / `2026-11-16T12:00:00-03:00`), el diálogo se cierra, la lista muestra el bloqueo y se anuncia “Turnos que pisan el bloqueo (1)” con el turno afectado.

### E6 — Eliminar bloqueo con confirmación

- **Dado** un bloqueo existente y el usuario con permiso,
- **Cuando** presiona “Eliminar bloqueo” y confirma “Sí, eliminar bloqueo”,
- **Entonces** recién ahí se envía `DELETE /blocks/{id}`, la fila desaparece y se anuncia “Bloqueo eliminado.”; si se elige “Volver”, no se envía ninguna request.

### E7 — Recepción solo lectura

- **Dado** una recepcionista autenticada,
- **Cuando** abre la pantalla de un profesional,
- **Entonces** ve el selector de profesional, los tramos y los bloqueos, pero **no** existen “Agregar tramo”, “Quitar”, “Guardar horario”, “Nuevo bloqueo” ni “Eliminar bloqueo”; los datos se muestran completos.

### E8 — Odontólogo que intenta ver otro profesional (403)

- **Dado** un odontólogo autenticado como `P` que abre `/horarios-y-bloqueos?professionalId=Q` (Q ≠ P),
- **Cuando** la página consulta `GET /professionals/Q/working-hours`,
- **Entonces** el backend responde `403` con `No tiene permiso para leer horarios.`, la página muestra ese mensaje en `role="alert"`, no ofrece controles de edición y no cierra la sesión.

### E9 — Adaptabilidad visual (no automatizable en jsdom)

- **Dado** la pantalla con datos de ejemplo,
- **Cuando** se verifica a 1440, 768 y 390 px,
- **Entonces** no hay overflow horizontal, los días se apilan sin cortar inputs ni botones, el diálogo de bloqueo se presenta como hoja inferior a 390 px y los estados se distinguen por texto además de color. Se guardan capturas reales antes de archivar.

### Escenarios adicionales sugeridos (si el presupuesto de 6 tests lo permite)

- **E10 — Bloqueo inválido**: el backend responde `422 INVALID_BLOCK` y se muestra el mensaje literal; el diálogo no se cierra.
- **E11 — Fallo de red con reintento**: `GET` falla, aparece `ErrorState` con “Reintentar”; al reintentar, se cargan los datos.
- **E12 — Listas vacías**: sin tramos y sin bloqueos se muestran los `EmptyState` correspondientes.

---

## 5. Tamaño estimado, riesgos y posible split

### 5.1 Archivos nuevos y modificados

**Producción (nuevos)**:

1. `frontend/src/features/horarios/horariosApi.ts` — tipos, parseo estricto, `getWorkingHours`, `replaceWorkingHours`, `listBlocks`, `createBlock`, `deleteBlock` (~250 líneas).
2. `frontend/src/features/horarios/horariosTime.ts` — conversión/etiquetas de fecha y hora local (~60 líneas).
3. `frontend/src/features/horarios/HorariosPage.tsx` — resolución de rol/target, carga, estados y composición (~220 líneas).
4. `frontend/src/features/horarios/WorkingHoursSection.tsx` — siete días, alta/edición/eliminación de tramos y guardado (~220 líneas).
5. `frontend/src/features/horarios/BlocksSection.tsx` — lista, creación y borrado (~160 líneas).
6. `frontend/src/features/horarios/BlockFormDialog.tsx` — formulario de alta (~180 líneas).
7. `frontend/src/features/horarios/AffectedAppointments.tsx` — aviso compartido (~90 líneas).
8. `frontend/src/features/horarios/*.module.css` — 3 o 4 módulos (~300 líneas).
9. `frontend/src/features/horarios/useHorarios.ts` — carga y mutaciones (~180 líneas), si se separa de la página.

**Producción (modificados)**:

- `frontend/src/App.tsx` — una ruta nueva (~2 líneas).
- `frontend/src/features/auth/menuFor.ts` y `frontend/src/shared/components/AppShell.tsx` — **solo si se elige D1-B** (parámetro/prop opcional, defaults actuales).
- `frontend/src/shared/styles/tokens.css` — **solo si** hacen falta tokens de layout; idealmente ninguno nuevo.

**Tests nuevos** (archivos nuevos; ninguno existente se toca):

1. `frontend/src/features/horarios/horariosApi.test.ts` — parseo de contratos y errores (2–3 tests).
2. `frontend/src/features/horarios/WorkingHoursSection.test.tsx` — E1, E3, E4 (3 tests).
3. `frontend/src/features/horarios/BlocksSection.test.tsx` — E5, E6, E10 (3 tests).
4. `frontend/src/features/horarios/HorariosPage.test.tsx` — E2, E7, E8, E11, E12 (4–5 tests).
5. `frontend/src/features/horarios/horariosStyles.test.ts` — tokens, media queries y ausencia de colores crudos (1–2 tests).
6. `frontend/src/features/horarios/HorariosRoute.test.tsx` — ruta protegida y enlace de menú si se elige D1-B (1 test).

**Volumen**: 6 a 8 archivos de producción, 5 a 6 archivos de test, **~12–14 tests nuevos** si se cubren todos los escenarios; **6 tests** si se recorta a los exigidos por CHANGES.md (E1, E3, E4 o E5, E6, E7, E8). Estimo **1.200–1.600 líneas** de producción + tests. Es un change **mediano**, similar a C-31 pero con menos superficie visual.

### 5.2 Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Habilitar el menú rompe 3–4 tests existentes | Alto | D1-B (seam) o D1-A (no habilitar); **no** tocar los tests sin autorización |
| `24:00` no se puede cargar con `type="time"` | Medio | Inputs de texto `HH:MM` y ayuda visible; el backend ya acepta `24:00` |
| Mensajes de solapamiento por posición no coinciden con la UI | Medio | Enviar en el orden visible; no reordenar; test con el mensaje literal |
| Zona horaria de bloqueos sin endpoint | Medio | Prop `timezone` con `DEFAULT_AGENDA_TIMEZONE` (D6-A) o `GET /api/agenda` (D6-B); documentar |
| Afectados de horario solo cubren 90 días | Bajo | Etiquetar “Turnos futuros fuera del horario”; no prometer “todos” |
| Afectados no traen `chairName` | Bajo | Mostrar paciente, hora y estado; omitir sillón o pedir `/chairs` si se decide incluirlo |
| `GET` de bloqueos sin paginación | Bajo | MVP con pocos bloqueos; lista ordenada y sin tabla gigante |
| Recepción con formularios visibles por error | Medio | Render condicional por rol + test E7 que verifica ausencia de controles |
| `PUT` reemplaza toda la semana | Medio | Enviar siempre el estado completo visible; confirmar si queda vacío |
| Tests de jsdom no miden layout | Medio | Verificación visual 1440/768/390 antes de archivar (skill) |
| C-31 en curso en el mismo árbol | Bajo | No tocar archivos de C-31; aplicar C-32 después de que cierre el archivado |

### 5.3 Posible split

Si el presupuesto de la semana aprieta, dividir en dos changes secuenciales, no en dos ramas paralelas:

- **C-32a — `ui-horarios-atencion`**: ruta + shell de página + selector de profesional + sección de horarios (`GET`/`PUT`) + aviso de `appointmentsOutsideHours`. Tests: E1, E3, E4, E7, E8. Es el núcleo de US-010 y ya deja la pantalla navegable.
- **C-32b — `ui-bloqueos`**: sección de bloqueos (`GET`/`POST`/`DELETE`) + diálogo de alta + confirmación de borrado + aviso de `affectedAppointments`. Tests: E5, E6, E10. Reutiliza el shell y el componente de afectados de C-32a.

**Recomendación**: mantener **un solo C-32** si se aceptan ~12 tests y D1-B; si se quiere respetar el presupuesto de **6 tests** de CHANGES.md, hacer el split y dejar C-32b como recortable (igual que C-33). En ambos casos, los tests no se recortan.

---

## 6. Resumen y decisiones para la autora

La API de C-21 alcanza sin cambios. La pantalla puede construirse reutilizando `Dialog`, `StatusBadge`, `LoadingState`, `ErrorState`, `EmptyState`, `agendaTime` y `buildStartAtIso`. El único conflicto real es el menú “Próximamente”: **no se puede habilitar sin tocar tests existentes** con la firma actual de `menuFor`.

**Decisiones recomendadas por defecto**:

1. **D1 (ruta/menú)**: agregar `/horarios-y-bloqueos`; para habilitar el ítem, usar el seam `enabledMenuIds` (B) y dejar la duda abierta; si no se acepta el seam, dejar el ítem deshabilitado (A). No modificar tests existentes sin autorización.
2. **D2 (roles)**: odontólogo propio sin selector; admin y recepción con selector de activos; recepción solo lectura; un `?professionalId=` ajeno en odontólogo se deja responder por el backend con `403`.
3. **D3 (tramos)**: siete días, filas de inicio/fin en texto `HH:MM` (fin admite `24:00`), orden visible, `PUT` de toda la semana.
4. **D4 (solapes)**: sin validación duplicada en el cliente; mostrar el `422` literal del backend.
5. **D5 (afectados)**: componente compartido, `role="status"`, títulos distintos para horario y bloqueo, paciente + hora local + estado, nota de que el turno no se cancela.
6. **D6 (bloqueos)**: lista completa, alta con `datetime-local`, `buildStartAtIso` y `timezone` inyectada con `DEFAULT_AGENDA_TIMEZONE`.
7. **D7 (borrado)**: confirmación dentro del `Dialog` con el patrón de C-30; sin `window.confirm`.
8. **D8/D9 (estados y accesibilidad)**: `LoadingState`/`ErrorState`/`EmptyState`, `fieldset/legend`, foco visible, texto además de color.
9. **D10 (responsive)**: dos columnas a 1440, una a 768 y 390; capturas reales obligatorias.
10. **Tamaño**: 6–8 archivos de producción y 6–12 tests nuevos; si se respeta el límite de 6 tests, dividir en C-32a (horarios) y C-32b (bloqueos).

*Frenamos aquí sin ejecutar `/opsx:propose`, conforme a las instrucciones.*
