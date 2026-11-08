# Explore C-27 — `ui-agenda-diaria`

Fecha: 2026-11-07
Fase: 6 — Interfaz web (React + TypeScript + Vite), sobre la API probada
Governance: **BAJO** (vista de solo lectura; no escribe datos ni toca seguridad, según `CHANGES.md` §[C-27])
Dependencias en `CHANGES.md`: `C-26` (y, por transitividad, `C-25`, `C-24`, `C-22`/`C-23`, `C-19`).

> Este explore es analítico: **no** ejecutó docker, `npm install`, `npx`, pytest, alembic ni pip; **no** tocó `backend/`, `frontend/`, código, tests, migraciones, specs, `docker-compose.yml`, `.env`, la KB, `AGENTS.md`, `CLAUDE.md` ni creó la carpeta del change. C-26 está implementado y su archive se está moviendo en el árbol de trabajo (`openspec/changes/archive/2026-11-07-ui-login-y-sesion/`); el contrato vigente se leyó de `openspec/specs/frontend-auth-session/spec.md`. C-25, C-24, C-23 y C-22 están archivados; sus specs y el código real de `frontend/` son la fuente de verdad.
>
> Comandos read-only ejecutados: `git status --short`, `ls`, `read`, `grep`, `sed`, `wc`. No se corrieron tests, builds, migraciones ni contenedores.

---

## 1. Alcance de C-27 según `CHANGES.md` y qué queda afuera

### Qué entra en C-27

1. **Ruta `/agenda` protegida**, visible para los tres roles, que reemplaza el placeholder del menú.
2. **Vista diaria** con una columna por profesional y una grilla temporal (eje de horas).
3. **Navegación de día**: anterior, siguiente, “Hoy” y selector de fecha; la fecha vive en la URL.
4. **Turnos posicionados por hora local** con `startAt`/`endAt` UTC, sin convertir la fecha local a UTC.
5. **Color por estado** con la paleta AA ya existente (`APPOINTMENT_STATUS_TOKENS`) y texto de estado, no solo color.
6. **Turnos cancelados visibles y atenuados**, sin ocultarlos: la API los incluye y C-27 no agrega filtro de estado.
7. **Horarios de atención** como bandas de fondo por profesional y día de la semana (`workingHours`).
8. **Bloqueos** como bandas rayadas con motivo y etiqueta accesible (`blocks`).
9. **Filtros por profesional y por sillón**, combinables, con la asimetría de la API explicada en la UI:
   - `professionalId` filtra turnos, horarios y bloqueos.
   - `chairId` filtra **solo turnos**; los horarios y bloqueos siguen visibles.
10. **Estados de carga, vacío, error, reintento y actualización manual**, sin polling.
11. **Manejo de `401` delegado a C-26** (limpieza de sesión y redirección al login) y **`403` mostrado con los mensajes de la API**.
12. **Responsive básico para escritorio y tablet**: scroll horizontal controlado, encabezado de columnas fijo y columna de horas fija.
13. **Accesibilidad**: etiquetas, foco visible, contraste AA, leyenda, `aria-live` y una **vista alternativa de lista/tabla** para la grilla absoluta.
14. **Tests de componentes** de columnas por profesional, color por estado, filtro por sillón, estado vacío, navegación, URL, solapamientos, zona horaria y accesibilidad.
15. **Evidencias espejo**: RED, Vitest, `tsc --noEmit`, ESLint, mutaciones, trazabilidad, verificación manual con capturas y `verify-C-27.md`.

### Qué queda explícitamente afuera

- **Vista semanal**: C-28. C-27 prepara la grilla y los módulos puros, pero no agrega el selector día/semana ni siete columnas.
- **Crear turno**: C-29. C-27 no tiene formulario ni envía `POST /api/appointments`.
- **Reprogramar, cancelar, cambiar estado e historial**: C-30. C-27 no abre un panel de detalle ni llama a `GET /api/appointments/{id}`.
- **Vista por sillón con columnas por sillón**: C-31. En C-27 el sillón es un filtro, no una columna.
- **ABM de horarios, bloqueos, profesionales, sillones, prestaciones y pacientes**: C-32/C-33.
- **Cambios en `backend/`, dominio, migraciones, specs existentes, KB, `CHANGES.md` o `.env`**: no.
- **Cambios en autenticación**: se reutiliza C-26 tal cual; no se toca el token, el login ni el menú por rol más allá de habilitar Agenda.
- **Identidad visual nueva** (logo, tema, tipografía remota): fuera de alcance; se reutilizan tokens y componentes de C-25.
- **Drag & drop, tiempo real, notificaciones, polling, WebSocket**: fuera de alcance.
- **Línea de “ahora”** en la grilla: no la pide el scope; se deja como mejora futura. Si se agrega, debe usar el `Clock` inyectado y no un `setInterval` global.
- **Filtro “ocultar cancelados”**: la KB 07 dice que “se pueden ocultar con un filtro”, pero el scope de C-27 no lo pide y la API no acepta `status`. Recomendación: mostrar siempre los cancelados, atenuados; el toggle queda como pregunta P9.
- **Pruebas E2E con navegador real**: el scope pide tests de componentes; la prueba manual contra el backend va en `verify-C-27.md`.

### Frontera de archivos

- C-27 implementa **solo** bajo `frontend/` (preferentemente `src/features/agenda/`, la página de agenda, tokens de agenda y los ajustes mínimos de router/menú) y, cuando se proponga, sus artefactos de change en `openspec/changes/ui-agenda-diaria/` y sus evidencias `docs/evidencias/*-C-27.*`.
- Este explore solo crea `docs/evidencias/explore-C-27.md`. No crea la carpeta del change ni `tasks.md`.
- Precondición del apply: **GATE 16** (C-26 implementado, verde y archivado) y **GATE 17** (C-27 habilita C-28, C-29 y C-31). Hoy `frontend/` existe, C-26 está implementado (23 archivos, 85 tests) y su archive está en curso; no se debe tocar el archive ni el spec de C-26 durante este explore.

---

## 2. Estado actual

### 2.1. Lo que ya existe y C-27 reutiliza

| Pieza | Dónde | Qué aporta a C-27 |
|-------|-------|-------------------|
| Agenda API | `openspec/specs/agenda-api/spec.md`; `backend/app/api/agenda.py` | `GET /api/agenda?from=&to=&professionalId=&chairId=` con sobre `{ from, to, timezone, appointments, workingHours, blocks }`; `from`/`to` locales, `to` inclusivo, máximo 31 días; turnos enriquecidos, cancelados incluidos; orden estable. |
| Filtros | Spec de agenda; C-24 design D3/D14 | `professionalId` y `chairId` opcionales y combinables; id inexistente = `200` con listas vacías; `professionalId` filtra turnos, horarios y bloqueos; `chairId` solo turnos; inactivos incluidos en la agenda. |
| Horarios | Spec de agenda | Plantilla semanal con `professionalId`, `weekday` ISO 1–7, `start`/`end` `HH:MM`, `24:00` admitido como fin. |
| Bloqueos | Spec de agenda | `id`, `professionalId`, `startAt`/`endAt` UTC `Z`, `reason`; se incluyen los que cruzan medianoche o empiezan antes del rango. |
| Detalle de turno | `openspec/specs/appointments-api/spec.md` | `GET /api/appointments/{id}` enriquecido; **C-27 no lo usa** (lo usará C-30). |
| Profesionales | `openspec/specs/catalog-and-patients/spec.md` ~376+ | `GET /api/professionals` lista todos; sin `active` incluye inactivos en orden alfabético; `ProfessionalResponse { id, fullName, licenseNumber?, active }`. |
| Sillones | `openspec/specs/catalog-and-patients/spec.md` ~481+ | `GET /api/chairs` lista todos; sin `active` incluye inactivos; `ChairResponse { id, name, active }`. |
| Sesión | `frontend/src/features/auth/AuthContext.tsx` | `status`, `user`, `lastEvent`, `actionErrors`, `client`, `login`, `logout`, `clearActionErrors`; `SESSION_EXPIRED_MESSAGE` y `NETWORK_ERROR_MESSAGE`. |
| Cliente de API | `frontend/src/shared/api/client.ts` | `createApiClient({ baseUrl, fetchFn })`, `FetchFn`, `ApiResult`, `API_BASE_URL`, `Authorization` automático y `notifyUnauthorized` en `401`. |
| Errores | `frontend/src/shared/api/errors.ts` | `getApiErrorMessages` devuelve los mensajes del backend tal cual; `unknown` recibe “Ocurrió un error inesperado (HTTP N).”. |
| Router | `frontend/src/App.tsx` | `routes` exportadas; `/login` con `PublicOnlyRoute`; layout `RequireAuth` + `AppShell`; `index` con `HomePage`; `*` con `NotFoundPage`. |
| Shell y menú | `frontend/src/shared/components/AppShell.tsx`; `frontend/src/features/auth/menuFor.ts` | Header con menú, usuario, logout, banner de `actionErrors`; hoy **todos** los ítems están deshabilitados con “Próximamente”. |
| Componentes base | `LoadingState`, `EmptyState`, `ErrorState`, `PageShell`, `StatusBadge` | Estados de carga/vacío/error, layout de página, badge de estado con tokens AA. |
| Tokens | `frontend/src/shared/styles/tokens.css`; `appointmentStatusTokens.ts` | Espaciado, tipografía, colores, radios, sombras; estados `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado` con contraste AA. |
| Seed ficticio | `backend/app/demo_data.py` | Quiroga `…0001`, Sosa `…0002`, Benítez `…0003`; Sillón 1/2/3 `…b1/b2/b3`; Control `…d4` 30 min; Ana Pérez `…c1`; Bruno Acosta `…c2`; horarios 09–13 y 15–19 (Quiroga y Benítez) y 09–13 (Sosa). |
| Evidencias | `docs/evidencias/http-C-24.txt`, `http-C-22.sh`, `http-C-24.sh`, `mutaciones-C-26.py`, `trazabilidad-C-26.py`, `verify-C-26.md` | Formato de respuestas reales, creación de turnos, mutaciones y verificación a espejar. |
| Test guardián | `frontend/src/features/auth/storageGuard.test.ts` | Escanea `frontend/src` y exige que `sessionStorage` viva solo en `tokenStore.ts`; C-27 no debe agregar storage. |

### 2.2. Qué le falta a la base para C-27

1. **No existe la ruta `/agenda`**: `App.tsx` solo tiene `/login`, `/` con `HomePage` y `*`.
2. **El menú está completamente deshabilitado**: `menuFor` devuelve `disabled: true` y `badge: "Próximamente"` para todos; `AppShell` renderiza `<button>` para todos.
3. **No hay módulo de agenda**: no hay tipos de la respuesta, parser, fetch ni hook.
4. **No hay módulo de tiempo/zona horaria**: todo el front hoy usa el navegador y no hay conversión controlada de UTC a `America/Argentina/Buenos_Aires`.
5. **No hay lógica de grilla**: eje de horas, posiciones, solapamientos, carriles, bandas de horarios y bloqueos.
6. **No hay tokens de agenda**: la grilla necesita alturas, anchos, líneas y fondos propios; `tokens.css` no los tiene.
7. **No hay tests de agenda** ni evidencia RED/mutaciones/trazabilidad de C-27.
8. **Los tests de C-26 asumen el menú todo deshabilitado y `/` con `HomePage`**: `AppShell.test.tsx`, `menuFor.test.ts`, `App.test.tsx` tendrán que actualizarse cuando Agenda se habilite y `/` redirija.
9. **No hay `Clock` inyectable**: “Hoy” y la fecha inicial dependen de `new Date()`, que no es determinista en tests.
10. **El cliente no acepta `AbortSignal`**: para cancelar requests al cambiar de día/filtro hay que agregar una costura mínima o usar un id de request.

### 2.3. Observaciones que condicionan el diseño

- **C-26 ya resolvió el `401`**: `sessionClient` limpia la sesión y `RequireAuth` redirige al login con `expired`. C-27 **no** debe duplicar ese manejo; solo debe evitar mostrar un error local cuando la request devuelve `401`.
- **C-26 ya resolvió el `403`**: `sessionClient` guarda los mensajes en `actionErrors` y `AppShell` los muestra en un banner. Si C-27 muestra además un `ErrorState` local, hay que limpiar el banner para no duplicar el mensaje.
- **La agenda incluye cancelados**: la API no acepta `status` y C-24 decidió no filtrar. Ocultarlos en el cliente sería una decisión de producto no pedida; se muestran atenuados y con badge.
- **La asimetría del filtro por sillón es el mayor riesgo de UX**: el usuario puede esperar que al filtrar por sillón desaparezcan horarios y bloqueos. La UI debe decirlo explícitamente y el test debe fijarlo.
- **`from`/`to` son fechas locales, no instantes**: no se convierten a UTC para pedirlas. El `timezone` de la respuesta es la autoridad después de la primera carga; el valor inicial es `America/Argentina/Buenos_Aires`.
- **El navegador puede estar en otra zona horaria**: un test o una demo en una máquina con `TZ=UTC` debe seguir mostrando el día y la hora de Buenos Aires. No se puede usar `getHours()`/`getDate()` locales.
- **La API ya está probada con `24:00` y medianoche**: la grilla debe clampear un bloqueo que cruza el día y no romper con un turno que termina a las `00:00`.
- **La API no pagina y el volumen es chico**: 2–5 profesionales y un día; no hace falta virtualización. La vista semanal (C-28) sí deberá revisar performance.
- **No hay TanStack Query**: C-26 la mencionó como posibilidad futura, pero el proyecto no la tiene instalada. C-27 no debe agregar una dependencia por una sola pantalla.
- **Inactivos**: la agenda y los catálogos los incluyen. La UI debe mostrarlos con una marca `(inactivo)` y no esconderlos, porque pueden tener turnos históricos o bloqueos.
- **El test manual pendiente de C-26**: `verify-C-26.md` dice que el mensaje “La sesión venció…” durante el uso se verificará a mano en C-27. C-27 debe ejecutar esa prueba y registrarla en `verify-C-27.md`.
- **El menú de C-26 tiene un escenario que dice “todos los ítems futuros deshabilitados”**: al habilitar Agenda, C-27 debe agregar un delta spec que distinga “Agenda habilitada” del resto de ítems futuros. No se edita el spec archivado en este explore.

---

## 3. Decisiones de diseño (`D1`–`D19`)

### D1 — Zona horaria y tratamiento de fechas locales

**Problema**: la API devuelve instantes UTC (`startAt`/`endAt` con `Z`) y fechas locales (`from`/`to` y `workingHours`). El navegador puede estar en otra zona horaria; usar la zona del sistema haría que un turno de las 10:00 en Buenos Aires se vea a otra hora en un CI con `TZ=UTC` o en una notebook configurada en otro país. Hay que decidir cómo se convierte y cómo se testea.

- **Opción A (recomendada)**: módulo puro `agendaTime.ts` con `Intl.DateTimeFormat` y una zona **explícita**:
  - `DEFAULT_TIMEZONE = "America/Argentina/Buenos_Aires"` solo como valor inicial; después de la primera respuesta, se usa el `timezone` que devuelve la API.
  - Para obtener la fecha local de un instante: `formatToParts` con `{ timeZone, year, month, day }`; nunca `getFullYear()`, `getMonth()` ni `getDate()`.
  - Para obtener la hora local: `formatToParts` con `{ timeZone, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }`.
  - Para etiquetas de fecha (“lunes 16 de noviembre de 2026”): se construye un mediodía UTC con `Date.UTC(y, m - 1, d, 12)` y se formatea con `timeZone: "UTC"`, porque la etiqueta representa un día calendario, no un instante.
  - Para sumar o restar días: `Date.UTC(y, m - 1, d + delta)` y extraer con `getUTC*`; evita los saltos de DST.
  - Para el día de la semana ISO: `getUTCDay()` sobre el mediodía UTC, convirtiendo domingo `0` a `7`.
  - `from`/`to` se envían como `YYYY-MM-DD` local; **nunca** se convierten a UTC.
  - Tests con dos zonas (`America/Argentina/Buenos_Aires` y una con DST, por ejemplo `America/New_York`) y un test guardián de código fuente que prohíbe los getters locales y los `toLocale*` sin `timeZone`.
  - *Pros*: correcto en cualquier máquina; el día y la hora son los del consultorio; testeable y determinista; no depende de la zona del runner; prepara C-28.
  - *Contras*: hay que escribir un módulo chico y un guardián; `Intl` requiere ICU completo (Node 20+ y navegadores modernos lo tienen).
- **Opción B — usar la zona del navegador**: `new Date(startAt).getHours()` y `getDate()`.
  - *Pros*: una línea; no hay módulo.
  - *Contras*: si el navegador o el CI no están en Buenos Aires, la agenda muestra otro día/hora; el bug es invisible en una máquina argentina y aparece en la defensa o en otro equipo; no se puede testear de forma estable. Descartada.
- **Opción C — offset fijo `-03:00`**: sumar/restar tres horas a mano.
  - *Pros*: no depende de `Intl`.
  - *Contras*: duplica la regla del backend; se rompe si cambia el `APP_TIMEZONE` o si se mira una fecha histórica con otro offset; no maneja DST de otras zonas; no se recomienda.
- **Recomendación**: **A**. El módulo es la única puerta de conversión; el resto de la feature no llama a `Date` para horas/días. `timezone` de la respuesta manda. El guardián permite `getUTC*` y `Date.UTC` dentro del módulo, y prohíbe `getHours`, `getMinutes`, `getDate`, `getDay`, `getMonth`, `getFullYear`, `getTimezoneOffset`, `toLocaleDateString`, `toLocaleTimeString` y `toLocaleString` en `src/features/agenda` (salvo el `systemClock` en `clock.ts`, que solo usa `new Date()`).

### D2 — Reloj inyectable para “Hoy” y la fecha inicial

**Problema**: la fecha inicial y el botón “Hoy” dependen del reloj. Si se usa `new Date()` dentro del componente, el test no puede fijar el día y la vista cambia según cuándo se ejecute.

- **Opción A (recomendada)**: interfaz `Clock { now(): Date }`, implementación `systemClock` y un `Clock` inyectable en `AgendaPage` (prop con default). Las funciones puras reciben `now` como parámetro. Los tests pasan un reloj fijo.
  - *Pros*: determinista; no se usan timers falsos ni mocks globales; el día se prueba en el borde de medianoche; el mismo reloj sirve para una futura línea de “ahora”.
  - *Contras*: un parámetro más en la página; es mínimo y explícito.
- **Opción B — `new Date()` directo en la página**:
  - *Pros*: menos cableado.
  - *Contras*: tests dependientes del día real; no se puede probar “Hoy” ni el cambio de día; no se recomienda.
- **Opción C — `vi.useFakeTimers()`**:
  - *Pros*: cambia el reloj global sin tocar la firma.
  - *Contras*: es un reemplazo global, va contra el espíritu de C1 y afecta a React/Testing Library; no se recomienda pudiendo inyectar.
- **Recomendación**: **A**. `AgendaPage({ clock = systemClock })`; `todayInTimeZone(clock.now(), timezone)` produce la fecha inicial. Tests: `2026-11-16T02:30:00Z` → fecha ART `2026-11-15` (23:30 del domingo) y `2026-11-16T03:30:00Z` → `2026-11-16` (00:30 del lunes). El reloj no se usa para decidir si un turno es pasado: la agenda es de solo lectura y muestra lo que la API devuelve.

### D3 — Navegación de día: anterior, siguiente, “Hoy” y selector de fecha

**Problema**: el usuario debe moverse día a día sin perder filtros, y la fecha debe poder compartirse o recargarse. Hay que decidir el estado, el formato y el historial.

- **Opción A (recomendada)**: la fecha vive en la URL (`?date=YYYY-MM-DD`) y se manipula con funciones puras:
  - “Anterior” y “Siguiente” suman/restan un día calendario con `addDays` (UTC), no 24 horas.
  - “Hoy” usa el `Clock` y la zona horaria.
  - Un `<input type="date">` permite saltar a una fecha; su valor es `YYYY-MM-DD`.
  - La etiqueta visible se arma con `Intl` en `es-AR` (por ejemplo “lunes 16 de noviembre de 2026”) y se muestra junto al selector.
  - Los cambios de fecha del usuario hacen `push`; la normalización de una URL inválida hace `replace`.
  - *Pros*: recarga y enlace compartible; back/forward funciona; los filtros se preservan; es testeable con `createMemoryRouter`.
  - *Contras*: hay que validar la fecha y sincronizar URL/estado; es una función pura y un hook.
- **Opción B — estado local del componente**:
  - *Pros*: simple.
  - *Contras*: recargar vuelve a hoy; no se puede compartir un día; el botón atrás no navega; no se recomienda.
- **Opción C — ruta `/agenda/2026-11-16`**:
  - *Pros*: URL más “limpia”.
  - *Contras*: hay que agregar un parámetro de ruta y combinar con los filtros; no aporta sobre el query; C-28 tendrá que cambiar la ruta. Descartada para C-27.
- **Recomendación**: **A**. Una fecha inválida (`2026-02-30`, `16-11-2026`, texto) se descarta, se usa hoy y se muestra un aviso discreto “La fecha del enlace no era válida; se muestra hoy.”, con `replace`. No se aceptan fechas fuera de un rango razonable (por ejemplo, año < 2000 o > 2100) para evitar que la API reciba basura; el rango exacto queda como validación local, no como regla de negocio.

### D4 — Rango del eje temporal de la grilla

**Problema**: hay que decidir qué horas se dibujan. Un rango fijo `00:00–24:00` obliga a scrollear 1440 px; un rango fijo `08:00–20:00` puede ocultar un bloqueo que empieza a las 23:00 o un turno fuera de horario (aunque el dominio no debería permitirlo). Los horarios del seed son 09–13 y 15–19.

- **Opción A (recomendada)**: rango **dinámico** por día:
  - Unión de los `workingHours` del `weekday` seleccionado (de todos los profesionales visibles), los `blocks` del día y los turnos.
  - Se convierte a minutos, se clampea a `[0, 1440]`, se redondea hacia abajo/arriba a la hora y se agrega un margen de una hora si hay datos.
  - Si no hay datos, se usa `08:00–20:00` como rango por defecto; si el rango resultante dura menos de 4 horas, se expande a 4 horas para que la grilla no quede diminuta.
  - La altura de una hora es un token (`--agenda-hour-height`, por defecto 64 px); las posiciones se calculan en porcentaje para que el rango sea independiente de la altura.
  - *Pros*: muestra exactamente lo que hay; no desperdicia scroll; soporta bloqueos nocturnos; testeable con una función pura.
  - *Contras*: el rango cambia entre días; el usuario puede notar que la grilla “salta”; se mitiga con una transición suave o sin animación.
- **Opción B — `00:00–24:00` fijo**:
  - *Pros*: nunca oculta nada; simple.
  - *Contras*: 24 horas de scroll para un consultorio que atiende 8; la vista diaria se vuelve incómoda; no se recomienda.
- **Opción C — `08:00–20:00` fijo**:
  - *Pros*: predecible y simple.
  - *Contras*: oculta bloqueos/turnos fuera de ese rango; la API admite `24:00` y bloqueos que cruzan medianoche; no se recomienda.
- **Recomendación**: **A**. La función pura `computeAxis({ workingHours, blocks, appointments, date, timezone })` devuelve `{ startMinute, endMinute, hours }`; se prueba con un día con horario 09–13/15–19, con un bloqueo 23–01, con un turno que termina a las 00:00, con un día vacío y con `24:00`. No se dibuja una línea de “ahora” en C-27.

### D5 — Posición de los turnos y carriles de solapamiento

**Problema**: los turnos se posicionan por hora local. Aunque el dominio prohíbe que dos turnos activos del mismo profesional se solapen, un turno cancelado no ocupa agenda y puede convivir en el mismo horario con uno activo; además, la UI no debe romperse si la API devuelve datos inconsistentes. Hay que decidir si las tarjetas se superponen o se reparten en carriles.

- **Opción A — posición absoluta sin carriles**: cada turno se posiciona por `top`/`height` y, si hay solapamiento, una tarjeta tapa a la otra.
  - *Pros*: simple; el caso normal no tiene solapamientos.
  - *Contras*: un cancelado y un activo a la misma hora se tapan; se pierde información; no es robusto.
- **Opción B (recomendada)**: posición absoluta **más** asignación de carriles:
  - Se calculan los minutos locales de inicio/fin y se clampean al día.
  - `assignLanes` ordena por inicio, fin e `id` (estable), agrupa por solapamiento transitivo y asigna el primer carril libre; devuelve `lane`, `laneCount`.
  - El ancho de cada tarjeta es `100% / laneCount` con un gap pequeño; las tarjetas del mismo grupo se reparten lado a lado.
  - Un turno cancelado se incluye; si comparte horario con uno activo, se ven ambos.
  - Altura mínima para turnos de 5 minutos; el texto completo va en la vista de lista y en el `aria-label`.
  - *Pros*: robusto; no oculta información; el caso normal no cambia; prepara C-31 (columnas por sillón) y C-28.
  - *Contras*: más lógica; se resuelve con una función pura y tests de solapamiento.
- **Opción C — apilar todo en una lista vertical**: cada turno ocupa una fila, sin posición temporal.
  - *Pros*: accesible y simple.
  - *Contras*: pierde la lectura de “hueco libre” y la grilla diaria; no cumple el objetivo de la vista; se usa solo como vista alternativa (D11).
- **Recomendación**: **B**. `appointmentRange(startAt, endAt, date, timezone)` devuelve `{ startMinute, endMinute }` con las reglas de medianoche; `assignLanes(appointments)` devuelve los carriles. Tests: sin solapamiento, dos cancelados solapados, cancelado + activo, tres turnos en cadena, turno de 5 minutos, turno que termina a las 00:00, turno que empieza antes del rango visible (clampeado). La UI no usa `opacity` sobre el texto para atenuar cancelados; usa borde discontinuo, fondo más claro y badge.

### D6 — Columnas: qué profesionales se muestran, en qué orden y qué pasa con los inactivos

**Problema**: la vista diaria necesita una columna por profesional. La respuesta de agenda trae `workingHours` y turnos, pero un profesional sin horario ni turnos en el día no aparecería. Además, los profesionales inactivos pueden tener turnos o bloqueos históricos.

- **Opción A (recomendada)**: columnas desde `GET /api/professionals` (sin `active`) + unión defensiva con los `professionalId` que aparezcan en la agenda:
  - Se muestran todos los profesionales del catálogo, incluso sin turnos, para que la columna vacía sea visible.
  - Los inactivos se muestran con la marca `(inactivo)` y no se ocultan.
  - Orden alfabético por `fullName` con `localeCompare("es", { sensitivity: "base" })` y desempate por `id` para que sea determinista.
  - Si hay `professionalId` en el filtro, se muestra solo esa columna (aunque esté inactiva).
  - Si el catálogo falla, se usan los profesionales que aparezcan en `workingHours` + `appointments` + `blocks` y se muestra un aviso “No se pudo cargar el listado de profesionales”; la grilla sigue funcionando.
  - Si un `professionalId` del filtro no existe en el catálogo, se muestra un estado vacío con “No se encontró el profesional seleccionado” y un botón para limpiar el filtro.
  - *Pros*: columnas completas y estables; no desaparecen profesionales con el día libre; los inactivos no se pierden; el orden no depende del orden de la API.
  - *Contras*: una request más; se mitiga con paralelismo y fallback.
- **Opción B — derivar columnas solo de la agenda**:
  - *Pros*: una sola request.
  - *Contras*: un profesional sin horario ni turnos no tiene columna; el día libre de un profesional no se ve; no se recomienda.
- **Opción C — mostrar solo activos**:
  - *Pros*: menos ruido.
  - *Contras*: oculta turnos históricos de un profesional inactivo; la agenda ya decidió incluir inactivos (C-24 D14); no se recomienda.
- **Recomendación**: **A**. La columna se identifica por `professionalId`; el encabezado muestra `fullName` y, debajo, un resumen de horario del día (“09:00–13:00 y 15:00–19:00”) o “Sin horario”. Las columnas vacías muestran la grilla de fondo y un texto “Sin turnos” para no confundir “vacío” con “no cargó”.

### D7 — Horarios, bloqueos y turnos cancelados en la grilla

**Problema**: hay que mostrar tres capas distintas sin que se tapen: horarios de atención (contexto), bloqueos (indisponibilidad) y turnos (contenido). Los cancelados siguen en la respuesta y no deben confundirse con turnos activos.

- **Opción A (recomendada)**: capas con jerarquía visual clara:
  - **Horarios**: bandas de fondo suaves por profesional y `weekday`; se dibujan primero, por detrás de todo; `aria-label` con el rango (“Horario de atención: 09:00 a 13:00”).
  - **Bloqueos**: bandas rayadas (patrón CSS) con borde y motivo; se dibujan por encima del horario y por debajo de los turnos; `aria-label` “Bloqueo: Congreso, de 12:00 a 13:00”. Si el motivo es vacío, “Bloqueo”.
  - **Turnos**: tarjetas por encima, con color de estado y borde; `StatusBadge` con texto; el estado nunca se comunica solo por color.
  - **Cancelados**: fondo atenuado, borde discontinuo y badge “Cancelado”; el texto mantiene contraste AA; no se usa `opacity` sobre el texto.
  - Los segmentos de horario y bloqueo se pueden solapar; se dibujan todos, sin fusionar, salvo que se decida fusionar horarios contiguos (opcional).
  - *Pros*: se entiende qué es contexto, qué es bloqueo y qué es turno; cumple el scope; accesible.
  - *Contras*: hay que cuidar el contraste de las bandas y el z-index; es CSS acotado.
- **Opción B — bloqueo como overlay rojo sobre todo**: una capa roja semitransparente sobre el horario.
  - *Pros*: muy visible.
  - *Contras*: tapa turnos y baja el contraste; no se recomienda.
- **Opción C — solo turnos, sin horarios ni bloqueos**:
  - *Pros*: menos trabajo.
  - *Contras*: no cumple el scope (horarios y bloqueos visibles); no se recomienda.
- **Recomendación**: **A**. El horario se filtra por `professionalId` y `weekday`; el bloqueo se filtra por `professionalId` y se clampea al día; el turno se posiciona con D5. Un bloqueo que cruza medianoche se recorta al rango visible y se marca visualmente si continúa; no se parte en dos tarjetas dentro del mismo día.

### D8 — Filtros por profesional y por sillón, con la asimetría explicada

**Problema**: la API trata distinto los dos filtros. `professionalId` filtra turnos, horarios y bloqueos; `chairId` filtra solo turnos. Si la UI no lo explica, el usuario cree que el filtro por sillón está roto porque siguen apareciendo franjas de horario y bloqueos.

- **Opción A (recomendada)**: dos `<select>` en la barra de herramientas, con etiqueta visible y una ayuda contextual:
  - **Profesional**: opciones del catálogo (incluye inactivos con `(inactivo)`) + “Todos”. Al elegir uno, la API devuelve solo sus turnos, horarios y bloqueos; la grilla muestra una sola columna.
  - **Sillón**: opciones del catálogo (incluye inactivos) + “Todos”. Al elegir uno, la API devuelve todos los horarios y bloqueos y solo los turnos de ese sillón; la grilla conserva todas las columnas y muestra un aviso: “El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.”
  - Ambos filtros se combinan con AND; si el resultado no tiene turnos pero sí horarios/bloqueos, se muestra un aviso de “Sin turnos para este filtro” sin borrar las bandas.
  - “Limpiar filtros” vuelve a “Todos” y conserva la fecha.
  - *Pros*: honesto con el contrato; evita falsos bugs; el usuario entiende por qué siguen las bandas; testeable.
  - *Contras*: hay que redactar bien la ayuda y no esconderla en un tooltip; se muestra como texto secundario.
- **Opción B — filtrar en el cliente todo el resultado por sillón**: al elegir un sillón, ocultar horarios y bloqueos de los profesionales sin turnos en ese sillón.
  - *Pros*: la vista “parece” más filtrada.
  - *Contras*: miente sobre el contrato y sobre la disponibilidad; un profesional puede tener un bloqueo aunque no tenga turnos en ese sillón; no se recomienda.
- **Opción C — solo filtro por profesional**:
  - *Pros*: sin ambigüedad.
  - *Contras*: no cumple el scope (filtro por sillón, US-040 CA-1/CA-4); no se recomienda.
- **Recomendación**: **A**. Los valores viven en la URL (D9). Un `professionalId` o `chairId` inexistente se detecta contra el catálogo y se muestra un aviso con opción de limpiar; si el catálogo falló, se deja que la API devuelva listas vacías y se muestra el aviso genérico. No se agrega un filtro de estado.

### D9 — Estado en la URL: fecha y filtros compartibles

**Problema**: recargar, compartir un enlace y usar atrás/adelante deben conservar el día y los filtros. También hay que decidir qué hacer con valores inválidos.

- **Opción A (recomendada)**: `useSearchParams` con tres claves:
  - `date=YYYY-MM-DD` (validada y real; default: hoy en la zona de la agenda).
  - `professionalId=<uuid>` (opcional; validado con regex UUID).
  - `chairId=<uuid>` (opcional; validado con regex UUID).
  - Los cambios del usuario hacen `push`; la normalización de valores inválidos o faltantes hace `replace`.
  - Los parámetros desconocidos se ignoran para armar la request; no se envían a la API.
  - *Pros*: enlace compartible; recarga y back/forward; sin estado global; testeable con `createMemoryRouter`.
  - *Contras*: hay que validar y normalizar; es un hook chico.
- **Opción B — guardar el estado en `sessionStorage`**:
  - *Pros*: no ensucia la URL.
  - *Contras*: no es compartible; el test guardián de C-26 prohíbe storage fuera de `tokenStore.ts`; no se recomienda.
- **Opción C — estado en un contexto global de agenda**:
  - *Pros*: acceso desde cualquier componente.
  - *Contras*: no es compartible por URL; más código; no se necesita para una sola página. Descartada.
- **Recomendación**: **A**. La URL es la fuente de verdad. Si la fecha falta, se usa hoy y se hace `replace` para dejarla explícita; si es inválida, se usa hoy, se muestra el aviso y se hace `replace`. Si un filtro es inválido, se descarta, se avisa y se hace `replace`. No se valida la existencia de un UUID en la URL hasta que llegue el catálogo; si no existe, se muestra el estado vacío de D6/D8.

### D10 — Carga, vacío, error, `401`, `403` y actualización manual

**Problema**: la vista tiene que comportarse bien en el arranque, al cambiar de día/filtro, cuando no hay turnos, cuando la API falla y cuando la sesión venció o no hay permiso. C-26 ya centralizó parte del manejo; C-27 no debe duplicarlo ni contradecirlo.

- **Opción A (recomendada)**: una máquina de estados en el hook de datos, con estados visuales claros:
  - **Carga inicial**: `LoadingState` en el área de la grilla, con `role="status"`; los filtros se pueden mostrar deshabilitados mientras carga.
  - **Actualización** (cambio de día/filtro o “Actualizar”): se conserva la grilla anterior con `aria-busy="true"` y un texto “Actualizando…”; no se borra la vista; evita el parpadeo.
  - **Vacío**: si hay profesionales pero no turnos, se sigue mostrando la grilla con horarios/bloqueos y un aviso “No hay turnos para este día”; si no hay profesionales, `EmptyState` “No hay profesionales para mostrar”; si el filtro no tiene resultados, aviso con “Limpiar filtros”.
  - **Error de red/5xx**: `ErrorState` con el mensaje de `getApiErrorMessages` (o “Ocurrió un error inesperado…”) y botón “Reintentar”; no se descarta la sesión.
  - **`400`**: `ErrorState` con los mensajes de validación de la API; no debería ocurrir si la URL está validada, pero se muestra sin romper.
  - **`401`**: no se muestra un error local; `sessionClient` ya limpia la sesión y `RequireAuth` redirige al login con “La sesión venció…”. El hook ignora el resultado para no competir con la redirección.
  - **`403`**: se muestra un `ErrorState` local con los mensajes de `violations` y se llama `clearActionErrors()` para que el banner global de C-26 no duplique el mismo texto; la sesión sigue abierta.
  - **Actualización manual**: botón “Actualizar” con `aria-label="Actualizar agenda"`; no hay polling ni `setInterval`.
  - *Pros*: cubre todos los estados; respeta C-26; no parpadea; es testeable.
  - *Contras*: hay que cuidar la carrera entre la redirección por `401` y el estado local; se resuelve ignorando `401` en el hook y limpiando en el desmontaje.
- **Opción B — mostrar un `LoadingState` en cada cambio y desmontar la grilla**:
  - *Pros*: simple.
  - *Contras*: parpadeo en cada navegación; se pierde el contexto; no se recomienda.
- **Opción C — manejar `401` localmente con un mensaje**:
  - *Pros*: control local.
  - *Contras*: duplica C-26, puede dejar la sesión a medias y mostrar dos mensajes; no se recomienda.
- **Recomendación**: **A**. El hook recibe el `client` de `useAuth` para que el `401` y el `403` sigan el camino de C-26. El `403` local limpia el banner global una vez; el test verifica que no haya dos mensajes iguales. El error de red no cierra sesión.

### D11 — Accesibilidad de una grilla posicionada en absolute

**Problema**: una grilla con posiciones absolutas y columnas no es navegable ni legible por un lector de pantalla. El proyecto exige accesibilidad básica (foco visible, contraste, teclado) y C-27 tiene una vista densa.

- **Opción A (recomendada)**: **grilla visual + vista alternativa de lista/tabla**:
  - La grilla es la vista por defecto; cada tarjeta es un `<article>` (o `<li>`) con texto completo y `aria-label` que incluye hora, paciente, profesional, sillón, prestación y estado.
  - Un botón “Ver como lista” / “Ver como grilla” cambia a una tabla semántica:
    - `<caption>` “Turnos del lunes 16 de noviembre de 2026”.
    - Encabezados `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación`, `Estado` con `scope="col"`.
    - Filas en el mismo orden de la API (inicio, id); si no hay turnos, una fila o párrafo “No hay turnos”.
  - La tabla es la alternativa accesible; no se intenta hacer `role="grid"` con navegación de celdas en C-27.
  - Leyenda de estados visible, con `StatusBadge` y texto; no solo color.
  - Foco visible en filtros, navegación de fecha, “Hoy”, “Actualizar” y el toggle; orden de tabulación natural; sin `tabIndex` en tarjetas sin acción.
  - `aria-live="polite"` anuncia “Turnos del …: N” al cargar o cambiar de día/filtro; el aviso de vacío también.
  - Los bloques y horarios tienen `aria-label`; las bandas decorativas pueden ser `aria-hidden` si el texto ya está en el encabezado de la columna.
  - *Pros*: cumple accesibilidad sin convertir la grilla en un componente complejo; la tabla es útil también en tablet; testeable con roles y nombres.
  - *Contras*: hay que mantener dos representaciones; comparten los mismos datos y el mismo orden.
- **Opción B — solo grilla con `role="grid"`/`gridcell` y navegación por flechas**:
  - *Pros*: una sola vista.
  - *Contras*: hay que implementar navegación de celdas, foco y anuncios; es mucho para C-27 y fácil de hacer mal; no se recomienda.
- **Opción C — solo lista/tabla**:
  - *Pros*: accesible y simple.
  - *Contras*: pierde la vista diaria y la lectura de huecos; no cumple el objetivo visual; no se recomienda.
- **Recomendación**: **A**. La tabla no es un “modo accesible oculto”: es un toggle visible que cualquier usuario puede usar. La grilla no tiene tarjetas clickeables en C-27 (D14), así que no hay foco perdido en elementos sin acción.

### D12 — Responsive para escritorio y tablet

**Problema**: con 3–5 profesionales, las columnas no entran en un tablet si se achican; la grilla necesita scroll horizontal y cabeceras fijas para no perder la referencia.

- **Opción A (recomendada)**: un contenedor de scroll único:
  - Ancho mínimo por columna (`--agenda-column-min-width`, ~220 px) y columna de horas fija (`--agenda-time-gutter-width`, ~64 px).
  - Scroll horizontal del bloque de grilla; el encabezado de profesionales queda `sticky` arriba y la columna de horas `sticky` a la izquierda; la esquina queda fija con ambos `sticky`.
  - Altura máxima del contenedor (`max-height: calc(100vh - …)`) para que el scroll vertical sea interno y no se pierda el encabezado.
  - Barra de herramientas (`flex-wrap`) con fecha, filtros, “Hoy” y “Actualizar”; en pantallas angostas, los controles ocupan el ancho y la grilla sigue con scroll.
  - Objetivos táctiles de al menos 44×44 px; sin información solo en `hover`.
  - *Pros*: usable en 768 y 1024 sin rehacer el layout; mantiene la lectura de columnas; el scroll es explícito.
  - *Contras*: hay que cuidar `z-index` y fondos de las celdas sticky; el test de layout es manual (jsdom no calcula).
- **Opción B — columnas flexibles que se achican**:
  - *Pros*: sin scroll horizontal.
  - *Contras*: con 5 profesionales las tarjetas quedan ilegibles; no se recomienda.
- **Opción C — layout móvil separado**:
  - *Pros*: experiencia móvil óptima.
  - *Contras*: el scope pide escritorio y tablet, no móvil; suma trabajo; no se recomienda en C-27.
- **Recomendación**: **A**. `PageShell` tiene `max-width: 1120px`; alcanza para 3 columnas y para 5 con scroll interno. Si la autora quiere aprovechar todo el ancho, se agrega un `variant="wide"` aditivo a `PageShell`; no es obligatorio para C-27.

### D13 — Diseño visual, tokens y reutilización de la paleta de estados

**Problema**: la agenda debe verse cuidada y consistente con C-25/C-26, sin introducir una librería ni colores hardcodeados. La grilla necesita medidas que no existen en los tokens actuales.

- **Opción A (recomendada)**: extender `tokens.css` con tokens de agenda y reutilizar los de estado:
  - `--agenda-hour-height`, `--agenda-time-gutter-width`, `--agenda-column-min-width`, `--agenda-column-header-height`.
  - `--agenda-grid-line`, `--agenda-working-background`, `--agenda-outside-background`, `--agenda-header-background`.
  - `--agenda-block-background`, `--agenda-block-border`, `--agenda-block-text`, `--agenda-block-stripe`.
  - `--agenda-card-min-height`, `--agenda-card-gap`, `--agenda-card-radius`.
  - Los colores de estado salen de `APPOINTMENT_STATUS_TOKENS` y `StatusBadge`; no se duplican HEX en TSX.
  - CSS Modules en `features/agenda`; constantes de layout puras en TS (`AGENDA_DEFAULT_START`, etc.) con tests.
  - Tipografía y espaciado de C-25; sombras suaves; sin fuentes remotas.
  - *Pros*: consistente; el tema se cambia en un lugar; los tests de tokens pueden leer el CSS; no agrega dependencias.
  - *Contras*: hay que mantener nombres y valores; es acotado.
- **Opción B — estilos inline o HEX en los componentes**:
  - *Pros*: rápido.
  - *Contras*: rompe el sistema de diseño; difícil de testear; no se recomienda.
- **Opción C — librería de componentes (MUI, Chakra) o un calendario de terceros**:
  - *Pros*: funcionalidad y look inmediatos.
  - *Contras*: dependencia pesada, estética ajena, bundle grande y choque con C-25; no se recomienda.
- **Recomendación**: **A**. La identidad visual propia (logo, tema, modo oscuro) queda para otro change. C-27 invierte en una grilla legible, una leyenda clara y tarjetas con jerarquía, no en una librería.

### D14 — Qué pasa al hacer clic o tocar un turno

**Problema**: el scope de C-27 no menciona interacción con el turno. C-29 crea, C-30 reprograma/cancela/cambia estado y muestra historial. Hay que decidir si C-27 adelanta un panel de detalle o deja las tarjetas como información.

- **Opción A (recomendada)**: **nada**: la tarjeta es informativa, no clickeable, sin panel ni request extra. Toda la información visible está en la tarjeta y en la lista. C-30 agrega el detalle, las acciones y el historial.
  - *Pros*: scope mínimo; no duplica C-30; no agrega `GET /api/appointments/{id}`; no hay botones muertos; no hay foco en elementos sin acción.
  - *Contras*: el usuario no puede ver más detalle todavía; es lo esperado para C-27.
- **Opción B — panel de vista previa de solo lectura** con `GET /api/appointments/{id}`:
  - *Pros*: más información sin salir de la agenda.
  - *Contras*: adelanta C-30, suma endpoint, estados y tests; el scope no lo pide; se puede hacer después.
- **Opción C — navegar a `/turnos/{id}`**:
  - *Pros*: URL de detalle.
  - *Contras*: no existe la ruta ni la pantalla; pertenece a C-29/C-30; no se recomienda.
- **Recomendación**: **A**. Si la autora quiere una vista previa, se acota a un panel de solo lectura sin acciones, pero eso conviene hacerlo en C-30, donde ya existe el detalle. La tarjeta se estructura como componente presentacional para que C-30 le agregue un `onSelect` sin reescribirla.

### D15 — Router, menú y pantalla inicial

**Problema**: hoy `/` muestra `HomePage` y el menú tiene todo deshabilitado. C-27 necesita `/agenda`, habilitar Agenda y decidir qué ve el usuario después del login.

- **Opción A (recomendada)**: `/agenda` como pantalla principal:
  - Agregar la ruta hija `agenda` dentro del layout protegido: `{ path: "agenda", element: <AgendaPage /> }`.
  - Cambiar el `index` de `/` por `<Navigate to="/agenda" replace />`; el login, al no tener `from`, vuelve a `/` y termina en `/agenda`.
  - `menuFor` devuelve Agenda con `disabled: false` y `badge: null`; el resto sigue `disabled: true` con “Próximamente”.
  - `AppShell` renderiza `NavLink` para los ítems habilitados (con `aria-current`) y `<button disabled>` para los futuros.
  - El tipo `MenuItem.badge` pasa a `"Próximamente" | null`.
  - Se actualizan los tests de C-26: `menuFor.test.ts`, `AppShell.test.tsx` y `App.test.tsx`; el delta spec de C-27 ajusta el escenario del menú (“Agenda habilitada; los demás futuros deshabilitados”).
  - La leyenda de estados de `HomePage` se reutiliza en la agenda (componente `StatusLegend`); `HomePage` puede quedar sin ruta o eliminarse en el apply.
  - *Pros*: después del login el usuario cae en la pantalla que usa todo el día; el menú refleja la realidad; el flujo del video es directo.
  - *Contras*: hay que actualizar tests de C-26 y el delta spec; es un cambio pequeño y esperado en un GATE.
- **Opción B — mantener `HomePage` en `/` y agregar `/agenda`**:
  - *Pros*: no se rompe el test de C-26 que espera `HomePage`; menos churn.
  - *Contras*: un clic extra para llegar a la agenda; la pantalla de bienvenida deja de aportar; el menú igual hay que habilitarlo. Es el fallback si la autora prefiere minimizar cambios.
- **Opción C — hacer que todos los ítems del menú sean rutas**:
  - *Pros*: menú completo.
  - *Contras*: C-28..C-33 todavía no existen; se crearían pantallas vacías; no se recomienda.
- **Recomendación**: **A**, con B como fallback de bajo riesgo. El `AppShell` sigue siendo el mismo; solo cambia cómo renderiza los ítems habilitados. El logout no cambia.

### D16 — Fetching de datos, tipos y ausencia de una librería de queries

**Problema**: hay que pedir agenda, profesionales y sillones; manejar carreras al cambiar de día/filtro; tipar la respuesta; y no agregar una dependencia grande por una sola pantalla.

- **Opción A (recomendada)**: módulo propio + hook con cancelación:
  - `features/agenda/agendaApi.ts`: tipos `AgendaResponse`, `AgendaAppointment`, `AgendaWorkingHours`, `AgendaBlock`, `Professional`, `Chair`; parser mínimo de la forma de la respuesta (arrays y campos obligatorios) que devuelve `null` si no cumple; `fetchAgenda`, `fetchProfessionals`, `fetchChairs` reciben un `ApiClient`.
  - `features/agenda/useAgenda.ts`: `useEffect` que dispara las tres requests en paralelo; `AbortController` + id de request para ignorar respuestas viejas; estados `loading`, `refreshing`, `success`, `error`; catálogos con `Promise.allSettled` para que un fallo de catálogo no bloquee la agenda.
  - Se agrega `signal?: AbortSignal` a `RequestOptions` en `shared/api/client.ts` y se pasa a `init.signal` (cambio aditivo, con test). Si se prefiere no tocar el cliente, se usa solo el id de request; la recomendación es agregar la señal porque C-28 la va a necesitar.
  - No se agrega TanStack Query ni otra librería.
  - *Pros*: control total; sin dependencias; testeable con `fetch` inyectado; cancelación real; los tipos viven cerca de la feature.
  - *Contras*: hay que escribir el hook y el parser; es acotado y explícito.
- **Opción B — TanStack Query**:
  - *Pros*: caché, reintentos, estados y cancelación listos.
  - *Contras*: dependencia nueva, configuración y conceptos para una sola pantalla; C-26 no la dejó instalada; no se recomienda en C-27.
- **Opción C — fetch dentro de cada componente**:
  - *Pros*: menos archivos.
  - *Contras*: requests duplicadas, carreras, estados inconsistentes; no se recomienda.
- **Recomendación**: **A**. La respuesta de la API es un contrato probado; el parser valida la forma mínima y, si no coincide, se muestra “Respuesta inesperada del servidor.” en lugar de romper. El `timezone` de la respuesta actualiza el valor usado por la grilla. No hay polling; “Actualizar” y los cambios de fecha/filtro disparan el fetch.

### D17 — Tests sin mocks: `fetch` inyectado, reloj inyectado y router en memoria

**Problema**: C1 prohíbe `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos y MSW. C-27 necesita probar tiempo, grilla, filtros, navegación, estados y accesibilidad sin simular módulos.

- **Opción A (recomendada)**:
  - **Unitarios puros**: `agendaTime.test.ts` y `agendaLayout.test.ts` no necesitan React ni fetch; se prueban con datos literales y un `Clock` fijo.
  - **API**: `agendaApi.test.ts` usa una `FetchFn` real que devuelve `new Response(...)`; se inspeccionan `init.method`, `init.headers` y `init.signal` guardándolos en un array del test (closure), no con un mock.
  - **Hook**: `useAgenda.test.tsx` con un componente de prueba que muestra el estado; `fetch` real responde agenda/profesionales/sillones; se prueba la cancelación con una promesa pendiente y un cambio de fecha.
  - **Presentacional**: `AgendaView.test.tsx` recibe props (datos, estado, handlers) y no usa `useAuth`; se prueban columnas, orden, estado, cancelados, horarios, bloqueos, filtros, vacío, lista/tabla y accesibilidad.
  - **Contenedor**: `AgendaPage.test.tsx` con `AuthProvider` real, `createMemoryTokenStore`, `createMemoryRouter` y un `fetch` que responde `/auth/me`, `/agenda`, `/professionals` y `/chairs`; se prueban URL, navegación, `401`, `403` y reintento.
  - **App**: `App.test.tsx` actualizado para `/` → `/agenda`; `AppShell.test.tsx` actualizado para Agenda habilitada; `menuFor.test.ts` actualizado.
  - **Guardián de tiempo**: `agendaTimeGuard.test.ts` escanea `src/features/agenda` y prohíbe getters locales y `toLocale*` sin `timeZone`; permite `getUTC*`, `Date.UTC` y `new Date()` solo en `clock.ts`.
  - *Pros*: cumple C1; prueba el borde real; determinista; cubre accesibilidad y estados.
  - *Contras*: hay que escribir fixtures de respuesta; es el mismo patrón de C-26.
- **Opción B — MSW**: interceptar a nivel de red.
  - *Pros*: realista y reutilizable.
  - *Contras*: C1 lo prohíbe; agrega dependencia y setup; no se recomienda.
- **Opción C — `vi.mock`/`vi.spyOn`/`vi.fn`**: reemplazar módulos o el reloj.
  - *Pros*: rápido.
  - *Contras*: prohibido por C1; oculta el comportamiento real; no se recomienda.
- **Recomendación**: **A**. Fixtures mínimos:
  - `AGENDA_LUNES`: Quiroga `10:00` Control (`13:00Z`), Sosa `09:00` Control (`12:00Z`), un cancelado de Sosa a las `09:00`, un bloqueo de Quiroga `12:00–13:00` (`15:00Z–16:00Z`), `workingHours` con `weekday: 1`.
  - Reloj fijo `2026-11-16T12:00:00Z` (09:00 ART) para la mayoría; `2026-11-16T02:30:00Z` para el borde de fecha.
  - Tests de tabla:
    | Capa | Escenarios |
    |------|------------|
    | `agendaTime` | `13:00Z` → 10:00 ART; `02:30Z` → día anterior 23:30; `03:30Z` → 00:30; `addDays` cruza mes/año; `weekday` ISO; `24:00`; DST en otra zona. |
    | `agendaLayout` | eje con horarios/bloqueos/turnos; default 08–20; mínimo 4 h; bloqueo 23–01; turno 23:30–00:00; carriles sin solape, cancelado+activo, tres en cadena, 5 min. |
    | `agendaApi` | 200 completo; 400; 401; 403; 500; red; JSON malformado; `signal` pasado al fetch. |
    | `AgendaView` | columnas y orden; inactivos; estado y cancelado; horarios; bloqueos; filtro por sillón conserva columnas/horarios; vacío; lista/tabla; `aria-live`; leyenda. |
    | `AgendaPage` | fecha default; URL inválida normalizada; prev/next/Hoy; filtros en URL; 401 redirige; 403 local sin duplicar banner; reintento. |
    | `App`/`AppShell`/`menuFor` | `/` redirige a `/agenda`; Agenda habilitada; resto deshabilitado; logout sigue funcionando. |
  - Evidencias: `red-C-27/`, `baseline-C-27.txt`, `precondicion-C-27.txt`, `vitest-C-27.txt`, `tsc-C-27.txt`, `eslint-C-27.txt`, `mutaciones-C-27.py`/`.txt`, `trazabilidad-C-27.py`/`.txt`, `verify-C-27.md`.

### D18 — Verificación manual con backend real, capturas y el pendiente de C-26

**Problema**: los tests de jsdom no validan layout, responsive, colores reales ni el `401` durante el uso. `verify-C-26.md` dejó explícito que esa prueba se hace en C-27. Hay que planificarla con datos ficticios y dejar evidencia reproducible.

- **Opción A (recomendada)**: guion manual con seed y scripts existentes:
  1. Levantar backend, PostgreSQL y frontend (docker compose); login con `recepcion` (seed ficticio).
  2. Sobre el lunes **2026-11-16** (día hábil), crear con `http-C-22.sh`:
     - Quiroga `10:00` Control, Ana Pérez, Sillón 1.
     - Sosa `09:00` Control, Bruno Acosta, Sillón 2.
     - Cancelar el turno de Sosa y volver a crear Sosa `09:00` Control para tener **cancelado + activo** en la misma columna y ver los carriles.
  3. Crear un bloqueo de Quiroga `12:00–13:00` con el flujo de C-21 y verificar la banda rayada con motivo.
  4. Verificar: 3 columnas, orden alfabético estable, turnos en la hora local correcta, colores y badges por estado, cancelado atenuado, horarios 09–13/15–19, bloqueo visible, carriles del solapamiento.
  5. Probar filtros: profesional (una columna), sillón (todas las columnas, solo turnos del sillón, aviso visible), ambos combinados; “Limpiar filtros”.
  6. Probar navegación: anterior/siguiente, “Hoy”, selector de fecha, recarga y enlace compartido; verificar que la URL conserva fecha y filtros.
  7. Probar día vacío: domingo **2026-11-15**; grilla con aviso “No hay turnos” (o `EmptyState` si no hay profesionales).
  8. Probar `401` durante el uso (pendiente de C-26): con la sesión iniciada, reemplazar a mano el valor de `sessionStorage["turnos.auth.accessToken"]` por un token inválido, pulsar “Actualizar” o navegar; debe limpiar la sesión, ir a `/login` y mostrar “La sesión venció. Iniciá sesión de nuevo.”. Registrar en `verify-C-27.md` y referenciar el pendiente de `verify-C-26.md`.
  9. Probar `403`: no es alcanzable a mano porque los tres roles tienen `APPEARMENT READ_AGENDA`; se cubre con un test de componente con `fetch` que responde `403` y se documenta la limitación.
  10. Responsive: DevTools en 1024×768 y 768×1024; verificar scroll horizontal, encabezado de columnas fijo, columna de horas fija, controles táctiles y ausencia de información solo por `hover`.
  11. Capturas: `C-27-agenda-dia.png`, `C-27-filtro-profesional.png`, `C-27-filtro-sillon.png`, `C-27-solapamiento-cancelado.png`, `C-27-vacio.png`, `C-27-sesion-vencida.png`, `C-27-tablet.png`.
  12. Evidencias: `http-C-27.txt` (respuestas de agenda reales), `manual-C-27.txt`, `verify-C-27.md`; no commit.
  - *Pros*: prueba lo que jsdom no puede; deja evidencia para la cátedra; cierra el pendiente de C-26; usa datos ficticios.
  - *Contras*: requiere levantar el stack; es el mismo costo que C-24/C-26.
- **Opción B — solo tests automatizados**:
  - *Pros*: rápido.
  - *Contras*: no valida responsive, colores reales ni el `401` manual; deja el pendiente de C-26 sin cerrar; no se recomienda.
- **Opción C — E2E automatizado con Playwright**:
  - *Pros*: repetible.
  - *Contras*: dependencia y tiempo; el proyecto no lo usa; fuera de scope. Se documenta como mejora futura.
- **Recomendación**: **A**. Las capturas y el `manual-C-27.txt` son parte de la evidencia; el `401` manual se registra también como cierre del pendiente de C-26.

### D19 — Qué NO hace C-27 y cómo se evita el solapamiento con C-28..C-33

**Problema**: la agenda es la pantalla central y es fácil que absorba el formulario de turno, la vista semanal, las acciones y los catálogos. Hay que fijar la frontera.

- **Opción A (recomendada)**: alcance estricto:
  - C-27 **no** hace vista semanal (C-28), formulario de turno (C-29), reprogramar/cancelar/estados/historial (C-30), columnas por sillón (C-31), ABM de horarios/bloqueos (C-32) ni catálogos/pacientes (C-33).
  - C-27 **no** modifica el backend, el dominio, las migraciones, los specs archivados, la KB, `CHANGES.md`, `docker-compose.yml` ni `.env`.
  - C-27 **no** agrega autenticación, storage, refresh, polling, drag & drop, notificaciones ni una librería de UI/query.
  - C-27 **no** agrega un filtro de estado ni oculta cancelados por defecto.
  - C-27 **no** usa datos reales de pacientes; todo sale del seed ficticio.
  - *Pros*: change terminable; governance BAJO; el camino crítico avanza; C-28..C-33 reciben una base limpia.
  - *Contras*: la agenda no permite operar todavía; es lo esperado en este GATE.
- **Opción B — adelantar “crear turno desde un hueco”**:
  - *Pros*: útil.
  - *Contras*: es C-29; toca formulario, validaciones y API; mezcla governance MEDIO; no se recomienda.
- **Opción C — adelantar el toggle día/semana**:
  - *Pros*: la agenda se siente completa.
  - *Contras*: es C-28 y duplica el trabajo de grilla semanal; no se recomienda.
- **Recomendación**: **A**. C-27 entrega una agenda diaria de solo lectura, con filtros, estados, accesibilidad, responsive y tests. La interacción con el turno llega en C-29/C-30.

---

## 4. Riesgos y preguntas para la autora

### Riesgos

| Riesgo | Mitigación |
|--------|------------|
| El navegador o el CI están en otra zona horaria y la agenda muestra otro día/hora | D1: `Intl` con `timeZone` explícito; `timezone` de la respuesta; tests con dos zonas; guardián que prohíbe getters locales. |
| Se usa un offset fijo `-03:00` y se rompe con otro `APP_TIMEZONE` o una fecha histórica | D1: prohibido el offset manual; todo pasa por `Intl`; el backend sigue siendo la autoridad. |
| Off-by-one en la etiqueta de fecha o en el `weekday` | D1/D3: etiquetas sobre mediodía UTC con `timeZone: "UTC"`; `weekday` con `getUTCDay()`; tests de borde de medianoche. |
| Un bloqueo que cruza medianoche o un turno que termina a las `00:00` rompe la grilla | D4/D5/D7: clampeo a `[0, 1440]`; `24:00` → 1440; tests de bloqueo 23–01 y turno 23:30–00:00. |
| Un turno de 5 minutos queda ilegible | D5/D11: altura mínima, texto corto, `title`/`aria-label` completo y vista de lista/tabla. |
| Cancelado + activo en el mismo horario se tapan | D5: carriles; test específico; cancelado con borde discontinuo y badge. |
| El filtro por sillón “parece roto” porque siguen horarios y bloqueos | D8: ayuda visible; test; prueba manual; no se filtra en el cliente lo que la API no filtra. |
| Profesionales inactivos desaparecen o se mezclan con los activos | D6/D8: catálogo sin `active`, marca `(inactivo)`, orden estable; test. |
| El catálogo de profesionales falla y la grilla queda sin columnas | D6/D16: fallback a la unión de la agenda + aviso; la agenda sigue visible. |
| Un `professionalId`/`chairId` inexistente en la URL deja una vista vacía sin explicación | D6/D8/D9: aviso y “Limpiar filtros”; si el catálogo falló, aviso genérico. |
| Los tests de C-26 se rompen al habilitar Agenda o al redirigir `/` | D15: actualizar `menuFor.test.ts`, `AppShell.test.tsx`, `App.test.tsx` y el delta spec; no tocar el archive. |
| El `401` del arranque o de una request se mezcla con un error local y muestra dos mensajes | D10: el hook ignora `401`; `sessionClient`/`RequireAuth` hacen la redirección; test. |
| El `403` se muestra dos veces (banner global + `ErrorState` local) | D10: `clearActionErrors()` al mostrar el error local; test de un solo mensaje. |
| Respuestas viejas pisan a las nuevas al cambiar de día/filtro rápido | D16: `AbortController` + id de request; test con promesa pendiente. |
| La grilla absoluta no es accesible por teclado/lector | D11: tabla alternativa, `aria-label`, `aria-live`, leyenda, foco visible; test por roles. |
| El layout no entra en tablet o el scroll pierde el encabezado | D12: ancho mínimo, `sticky`, scroll interno; prueba manual 768/1024; jsdom no valida layout. |
| `PageShell` con `max-width: 1120px` limita 5 columnas | D12: scroll interno; si hace falta, `variant="wide"` aditivo; no es bloqueante. |
| La línea de “ahora” se implementa con `setInterval` y rompe tests | D2/D4: no se implementa en C-27; si se agrega, usa el `Clock` inyectado y no un timer global. |
| Se agrega TanStack Query o una librería de calendario y crece el bundle | D16/D13: prohibido en C-27; se usa el cliente y CSS Modules existentes. |
| Se usan datos reales de pacientes en capturas o tests | D18: solo seed ficticio (`Ana Pérez`, `Bruno Acosta`, etc.); no hay datos reales. |
| El `403` manual no es alcanzable porque todos los roles leen la agenda | D18: se cubre con test de componente y se documenta la limitación; no se modifica el backend. |
| El pendiente de `401` de C-26 queda sin cerrar | D18: se prueba a mano en C-27 y se registra en `verify-C-27.md` con referencia a `verify-C-26.md`. |

### Preguntas para la autora

- **P1**: ¿La pantalla inicial después del login debe ser `/agenda` (recomendado), con `/` redirigiendo, o preferís mantener `HomePage` en `/` y agregar `/agenda` (menos cambios en tests de C-26) (D15)?
- **P2**: ¿Mostramos profesionales y sillones inactivos en columnas/filtros con la marca `(inactivo)` (recomendado), o solo los activos (D6/D8)?
- **P3**: ¿La tarjeta de turno no hace nada en C-27 (recomendado) o querés una vista previa de solo lectura que adelante parte de C-30 (D14)?
- **P4**: ¿El rango por defecto de la grilla puede ser `08:00–20:00` cuando el día no tiene datos, y expandirse a un mínimo de 4 horas (recomendado) (D4)?
- **P5**: ¿Confirmás que no hay línea de “ahora”, no hay polling y la actualización es manual (recomendado) (D2/D10)?
- **P6**: ¿Mostramos la ayuda “El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando” como texto visible (recomendado) o preferís un tooltip (D8)?
- **P7**: ¿El odontólogo entra viendo toda la agenda o filtrado por su propio `professionalId`? *Sugerencia: toda la agenda; el filtro es una acción voluntaria (la API le permite leer todo).*
- **P8**: ¿El `403` se cubre solo con test de componente y se documenta que a mano no es alcanzable (recomendado), o querés que agreguemos una forma de probarlo sin tocar el backend (D18)?
- **P9**: ¿Siempre mostramos los cancelados atenuados (recomendado) o querés un toggle “Ocultar cancelados” en C-27? La API no tiene filtro de estado; el toggle sería cliente (D7/D19).
- **P10**: ¿La vista de lista/tabla es un toggle visible para todos (recomendado) o solo una alternativa para lectores de pantalla (D11)?
- **P11**: ¿Los cambios de fecha/filtro hacen `push` en el historial (recomendado) y solo la normalización de URL inválida hace `replace` (D3/D9)?
- **P12**: ¿La leyenda de estados va en la barra de herramientas de la agenda (recomendado) o se mantiene solo en una pantalla de bienvenida (D13/D15)?

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md`)

> Estos son los tasks que el `apply` de C-27 debería crear; **no** se crea `tasks.md` en este explore ni la carpeta del change.

0. **Precondición y baseline**: verificar GATE 16 (C-26 implementado, verde y archivado) y GATE 17; confirmar que `frontend/` existe con 23 archivos/85 tests, `tsc` y ESLint limpios; archivar `baseline-C-27.txt` y `precondicion-C-27.txt`; leer `openspec/specs/frontend-auth-session/spec.md`, `agenda-api`, el cliente y los tests de C-26. No tocar el archive de C-26.
1. **Módulo de tiempo y reloj** (D1/D2): `agendaTime.ts` con `formatLocalDate`, `formatLocalTime`, `todayInTimeZone`, `addDays`, `weekdayOf`, `parseLocalDate`, `parseHHMM`, `minutesOfDay`, `appointmentRange`; `clock.ts` con `Clock`/`systemClock`; tests con dos zonas, borde de medianoche, mes/año, `24:00`, DST; guardián de fuente. RED archivado.
2. **Módulo de layout** (D4/D5/D6): `agendaLayout.ts` con `computeAxis`, `clampRange`, `assignLanes`, `groupByProfessional`, `compareProfessionals`; tests de eje, default 08–20, mínimo 4 h, bloqueo 23–01, turno 23:30–00:00, solapamientos, cancelado+activo, 5 min. RED archivado.
3. **API de agenda y catálogos** (D16): `agendaApi.ts` con tipos, parser mínimo, `fetchAgenda`, `fetchProfessionals`, `fetchChairs`; `signal` opcional en `RequestOptions` y `client.ts`; tests con `Response` real para 200/400/401/403/500/red/JSON inválido y `signal`. RED archivado.
4. **Hook de datos** (D10/D16): `useAgenda` con fetch paralelo, `AbortController` + id, estados `loading/refreshing/success/error`, fallback de catálogos, `refresh`; tests con `fetch` inyectado y cancelación. RED archivado.
5. **Contenedor y URL** (D3/D8/D9): `AgendaPage` con `useSearchParams`, `useAuth`, `clock`, fecha default, prev/next/Hoy, filtros, normalización y avisos; tests con `AuthProvider` + `createMemoryRouter`. RED archivado.
6. **UI presentacional** (D6–D13): barra de herramientas, leyenda, grilla, eje de horas, columnas, bandas de horario, bloqueos, tarjetas, carriles, estados vacío/carga/error y toggle lista/tabla; tokens y CSS Modules; tests de columnas/orden/inactivos/estado/cancelado/horarios/bloqueos/filtro por sillón/vacío/accesibilidad. RED archivado.
7. **Router y menú** (D15): ruta `/agenda`; `/` → `Navigate` a `/agenda`; `menuFor` con Agenda habilitada; `AppShell` con `NavLink`; actualizar `menuFor.test.ts`, `AppShell.test.tsx`, `App.test.tsx`; tests de regresión. RED archivado.
8. **Verificación y evidencias** (D17/D18): `red-C-27/`, `vitest-C-27.txt`, `tsc-C-27.txt`, `eslint-C-27.txt`, `mutaciones-C-27.py`/`.txt`, `trazabilidad-C-27.py`/`.txt`, `verify-C-27.md`, `manual-C-27.txt`, `http-C-27.txt` y capturas; prueba manual con seed, bloqueo y el `401` pendiente de C-26; confirmar que no se tocó `backend/`, specs archivados, KB, `CHANGES.md`, `docker-compose.yml` ni `.env`; `git diff --check`; no commit.

---

## 6. Resumen de recomendaciones (una línea cada una)

- **D1**: módulo puro con `Intl` y `timeZone` explícito (`America/Argentina/Buenos_Aires` como default, `timezone` de la API como autoridad), fechas locales `YYYY-MM-DD`, sin getters locales ni offset fijo.
- **D2**: `Clock { now(): Date }` inyectable, `systemClock` por defecto y tests con reloj fijo; sin timers falsos.
- **D3**: fecha en la URL, `addDays` por UTC, anterior/siguiente/“Hoy” y `<input type="date">`; normalización con `replace`.
- **D4**: eje dinámico por unión de horarios, bloqueos y turnos, clampeado a `[0,1440]`, default 08–20 y mínimo 4 h; sin línea de “ahora”.
- **D5**: posiciones por minutos locales y `assignLanes` para solapamientos; cancelado + activo lado a lado; altura mínima y vista de lista.
- **D6**: columnas desde `GET /api/professionals` (incluye inactivos con marca) + unión con la agenda, orden alfabético estable y fallback si falla el catálogo.
- **D7**: horarios como bandas suaves, bloqueos rayados con motivo y accesibles, turnos por encima y cancelados atenuados con borde discontinuo y badge.
- **D8**: filtros de profesional y sillón; el sillón solo filtra turnos, con ayuda visible; combinables y con “Limpiar filtros”.
- **D9**: `date`, `professionalId` y `chairId` en la URL, validados y normalizados; `push` para el usuario y `replace` para corregir.
- **D10**: carga inicial, actualización sin parpadeo, vacío, error con reintento, `401` delegado a C-26 y `403` local sin duplicar el banner; actualización manual.
- **D11**: grilla visual + toggle a tabla semántica, `aria-label` en tarjetas, leyenda, `aria-live`, foco visible y estado con texto, no solo color.
- **D12**: scroll horizontal con ancho mínimo por columna, encabezado y columna de horas `sticky`, altura interna y controles táctiles; tablet 768/1024.
- **D13**: tokens de agenda en `tokens.css`, CSS Modules, paleta AA existente y `StatusBadge`; sin librería de UI ni HEX en TSX.
- **D14**: tarjeta informativa, sin clic, panel ni request extra; C-30 agrega el detalle y las acciones.
- **D15**: `/agenda` como pantalla principal, `/` redirige, Agenda habilitada en `menuFor`, `NavLink` para habilitados y `button` para futuros; actualizar tests de C-26.
- **D16**: `agendaApi` + `useAgenda` con fetch paralelo, parser mínimo, `AbortController`/id y fallback de catálogos; sin TanStack Query ni dependencias nuevas.
- **D17**: tests sin mocks con `fetch` real/`Response`, reloj inyectado, `createMemoryRouter` y guardián de tiempo; fixtures de 2026-11-16; mutaciones y trazabilidad.
- **D18**: verificación manual con seed ficticio, turnos cancelado+activo, bloqueo, filtros, vacío, responsive y el `401` pendiente de C-26; capturas y evidencias.
- **D19**: C-27 es solo lectura y no absorbe C-28..C-33, backend, autenticación, polling, drag & drop ni filtros de estado.

---

## 7. Estado del repo al cierre del explore

| Ítem | Resultado |
|------|-----------|
| `frontend/` | existe; C-25 y C-26 implementados |
| C-26 | implementado (23 archivos, 85 tests; `tsc` y ESLint limpios); archive en curso en el árbol de trabajo |
| C-25 / C-24 / C-23 / C-22 | archivados; sus specs son la fuente de verdad |
| `openspec/changes/` | solo `archive/`; C-26 se está moviendo a `archive/2026-11-07-ui-login-y-sesion/` |
| `openspec/specs/frontend-auth-session/` | presente en el árbol de trabajo, sin commitear |
| `GET /api/agenda` | probado y documentado en `docs/evidencias/http-C-24.txt` |
| `GET /api/professionals` / `GET /api/chairs` | disponibles desde C-20, con inactivos si no se pasa `active` |
| Archivos creados por este explore | **solo** `docs/evidencias/explore-C-27.md` |
| Tests/builds ejecutados por este explore | ninguno |

`git status --short` al cierre (los cambios de C-26, `CHANGES.md`, `README.md`, la KB y las capturas son preexistentes de otros agentes; este explore no los tocó):

```
 M CHANGES.md
 M README.md
 M docs/evidencias/trazabilidad-C-26.py
 M docs/evidencias/verify-C-26.md
 M knowledge-base/06_funcionalidades.md
 D openspec/changes/ui-login-y-sesion/.openspec.yaml
 D openspec/changes/ui-login-y-sesion/design.md
 D openspec/changes/ui-login-y-sesion/proposal.md
 D openspec/changes/ui-login-y-sesion/specs/frontend-auth-session/spec.md
 D openspec/changes/ui-login-y-sesion/tasks.md
?? docs/evidencias/capturas/C-26-administrador.png
?? docs/evidencias/capturas/C-26-error.png
?? docs/evidencias/capturas/C-26-odontologo.png
?? docs/evidencias/capturas/C-26-recepcion.png
?? docs/evidencias/capturas/C-26-sesion-vencida.png
?? openspec/changes/archive/2026-11-07-ui-login-y-sesion/
?? openspec/specs/frontend-auth-session/
```
