# Design — C-27 `ui-agenda-diaria`

## Context

C-27 construye la agenda diaria sobre la base ya probada de C-25 (frontend React + TypeScript + Vite) y C-26 (login, sesión, guards, shell y menú). El contrato de datos es `GET /api/agenda?from=&to=&professionalId=&chairId=` de `agenda-api`: sobre `{ from, to, timezone, appointments, workingHours, blocks }`, `from`/`to` locales e inclusivos, turnos enriquecidos con `startAt`/`endAt` en UTC (`Z`), cancelados incluidos y orden estable. Los catálogos vienen de `GET /api/professionals` y `GET /api/chairs` (sin `active` incluyen inactivos). Las respuestas reales y los valores de los escenarios salen de `docs/evidencias/http-C-24.txt`: lunes **2026-11-16**, Quiroga `2026-11-16T13:00:00Z` (10:00 local) y Sosa `2026-11-16T12:00:00Z` (09:00 local), Sillón 1/2, `Control` de 30 min, `timezone: "America/Argentina/Buenos_Aires"` y un bloqueo de Quiroga de 12:00 a 13:00.

El change parte de `docs/evidencias/explore-C-27.md`; la autora aceptó **D1–D19** y las sugerencias **P1–P12**, con la precisión **C1** sobre zona horaria. Governance **BAJO**: solo lectura.

## Goals / Non-Goals

**Goals**: ruta `/agenda` y `/` redirigiendo; carga con `fetch` y `Clock` inyectados; hora local con el `timezone` de la respuesta; grilla con eje, columnas, carriles, horarios, bloqueos y cancelados; filtros y navegación en la URL; estados de carga/vacío/error con `401` delegado y `403` visible; vista de lista accesible y responsive de escritorio/tablet; tests sin mocks y evidencias RED/mutaciones/trazabilidad/manual.

**Non-Goals**: vista semanal (C-28), crear turno (C-29), reprogramar/cancelar/cambiar estado/historial (C-30), columnas por sillón (C-31), ABM de horarios/bloqueos/profesionales/sillones/prestaciones/pacientes (C-32/C-33); línea de “ahora”, polling, tiempo real, drag & drop, notificaciones, filtro de estado, librería de UI o de queries; cambios en `backend/`, dominio, migraciones, specs existentes, KB, `CHANGES.md`, `docker-compose.yml` o `.env`; tests E2E con navegador real.

## Decisions

### D1 — Zona horaria y fechas locales (incluye C1)

**Contexto**: la API devuelve instantes UTC y fechas locales. El navegador, el runner de Vitest o una notebook pueden estar en otra zona; usar la zona del sistema mostraría otro día u otra hora.

**Decisión**: un módulo puro `agendaTime.ts` es la **única puerta** de conversión. Usa `Intl.DateTimeFormat` con `timeZone` **explícito** y nunca `getFullYear`/`getMonth`/`getDate`/`getHours`/`getDay` ni `toLocale*` sin `timeZone`. La fuente de la zona es el `timezone` de la respuesta de `GET /api/agenda`; `from`/`to` se envían como `YYYY-MM-DD` local y **nunca** se convierten a UTC. Las etiquetas de día se formatean sobre un mediodía UTC con `timeZone: "UTC"`; `addDays` y `weekdayOf` usan `Date.UTC` y `getUTC*`. Tests con dos zonas y guardián de código fuente.

**Precisión C1 (autora)**: ningún componente escribe la zona horaria a mano. La agenda se pide con fechas locales `from`/`to` `YYYY-MM-DD` (no necesitan zona) y **todas** las horas que se muestran se formatean con el `timezone` de la respuesta. Si hace falta un valor de respaldo, vive en un **único** archivo de configuración (`frontend/src/features/agenda/agendaConfig.ts`, `DEFAULT_AGENDA_TIMEZONE = "America/Argentina/Buenos_Aires"`) y se usa **solo** antes de la primera respuesta. Un escenario obligatorio prueba que el resultado es el mismo aunque el proceso corra con `TZ=Asia/Tokyo`: el turno `2026-11-16T13:00:00Z` se muestra `10:00` y la fecha `2026-11-16` en ambas zonas.

**Alternativas descartadas**: usar la zona del navegador (`getHours()`/`getDate()`) porque el bug es invisible en Argentina y aparece en la defensa o en otro equipo; offset fijo `-03:00` porque duplica la regla del backend y se rompe con `APP_TIMEZONE` o fechas históricas.

### D2 — Reloj inyectable para “Hoy” y la fecha inicial

**Contexto**: la fecha inicial y el botón “Hoy” dependen del reloj; `new Date()` dentro del componente vuelve la vista no determinista.

**Decisión**: interfaz `Clock { now(): Date }`, implementación `systemClock` en `clock.ts` y `Clock` inyectable en `AgendaPage` (prop con default). Las funciones puras reciben `now` como parámetro; los tests pasan un reloj fijo (`2026-11-16T12:00:00Z`; borde `2026-11-16T02:30:00Z` → `2026-11-15` en Buenos Aires). No se usa el reloj para decidir si un turno es pasado.

**Alternativas descartadas**: `new Date()` directo en la página porque no se puede probar “Hoy”; `vi.useFakeTimers()` porque es un reemplazo global y va contra C1.

### D3 — Navegación de día con la fecha en la URL

**Contexto**: el usuario debe moverse día a día sin perder filtros y poder compartir o recargar la vista.

**Decisión**: `date=YYYY-MM-DD` en la URL. `Anterior`/`Siguiente` usan `addDays` calendario (UTC), `Hoy` usa `Clock` + zona, y un `<input type="date">` permite saltar. Las acciones del usuario hacen `push`; la normalización de una fecha ausente, inválida o fuera de `[2000, 2100]` usa hoy y `replace` con un aviso discreto.

**Alternativas descartadas**: estado local del componente porque recargar vuelve a hoy y no se comparte; ruta `/agenda/2026-11-16` porque complica los filtros y C-28 tendría que cambiarla.

### D4 — Rango dinámico del eje de horas

**Contexto**: un rango `00:00–24:00` obliga a scrollear 1440 px y un `08:00–20:00` fijo puede ocultar bloqueos o turnos fuera de horario.

**Decisión**: `computeAxis({ workingHours, blocks, appointments, date, timezone })` toma la unión de los `workingHours` del `weekday`, los bloqueos y los turnos; convierte a minutos, clampea a `[0, 1440]`, redondea hacia afuera a la hora y agrega una hora de margen si hay datos. Sin datos usa `08:00–20:00`; un rango menor a 4 horas se expande a 4. Las posiciones se calculan en proporción al rango; la altura por hora es un token (`--agenda-hour-height`, 64 px). No se dibuja línea de “ahora”.

**Alternativas descartadas**: `00:00–24:00` fijo porque la vista diaria se vuelve incómoda; `08:00–20:00` fijo porque oculta datos válidos y la API admite `24:00` y bloqueos que cruzan medianoche.

### D5 — Posición, alto y carriles de solapamiento

**Contexto**: el dominio prohíbe solapamientos activos del mismo profesional, pero un cancelado no ocupa agenda y puede convivir con un activo; además la UI no debe romperse con datos inconsistentes.

**Decisión**: `appointmentRange` calcula minutos locales de inicio/fin y los clampea al día (`24:00` → 1440). `assignLanes` ordena por inicio, fin e `id`, agrupa por solapamiento transitivo y asigna el primer carril libre, devolviendo `lane`/`laneCount`. El ancho es `100% / laneCount` con un gap; hay altura mínima para turnos de 5 minutos. Un cancelado y un activo a la misma hora se ven lado a lado.

**Alternativas descartadas**: posición absoluta sin carriles porque una tarjeta tapa a la otra y se pierde información; apilar todo en lista vertical porque pierde la lectura de huecos y no cumple la vista diaria (se usa como alternativa accesible en D11).

### D6 — Columnas por profesional

**Contexto**: la agenda trae datos por profesional, pero un profesional sin horario ni turnos no aparecería; los inactivos pueden tener turnos o bloqueos históricos.

**Decisión**: las columnas se arman desde `GET /api/professionals` (sin `active`) más una unión defensiva con los `professionalId` de horarios, bloqueos y turnos. Se muestran todos, incluidos los inactivos con la marca `(inactivo)`, ordenados con `localeCompare("es", { sensitivity: "base" })` y desempate por `id`. Las columnas vacías muestran “Sin turnos”. Con `professionalId` en la URL se muestra solo esa columna. Si el catálogo falla, se usa la unión de la agenda y un aviso; la grilla sigue visible.

**Alternativas descartadas**: derivar columnas solo de la agenda porque un profesional con el día libre desaparece; mostrar solo activos porque oculta turnos históricos y contradice la decisión de C-24.

### D7 — Horarios, bloqueos y cancelados como capas

**Contexto**: hay que mostrar contexto (horarios), indisponibilidad (bloqueos) y contenido (turnos) sin que se tapen; los cancelados siguen en la respuesta.

**Decisión**: tres capas con jerarquía visual. **Horarios**: bandas de fondo suaves por profesional y `weekday`, con `aria-label` (“Horario de atención: 09:00 a 13:00”). **Bloqueos**: bandas rayadas por encima del horario y por debajo de los turnos, con borde, motivo y etiqueta (“Bloqueo: Congreso, de 12:00 a 13:00”); sin motivo, “Bloqueo”. Un bloqueo que cruza medianoche se recorta al rango visible. **Turnos**: tarjetas por encima con color de estado y `StatusBadge`. **Cancelados**: fondo atenuado, borde discontinuo y badge “Cancelado”, sin `opacity` sobre el texto.

**Alternativas descartadas**: overlay rojo semitransparente sobre todo porque tapa turnos y baja el contraste; mostrar solo turnos porque no cumple el scope de horarios y bloqueos.

### D8 — Filtros por profesional y sillón con la asimetría visible

**Contexto**: `professionalId` filtra turnos, horarios y bloqueos; `chairId` filtra solo turnos. Si no se explica, el usuario cree que el filtro por sillón está roto.

**Decisión**: dos `<select>` con etiqueta visible y opción “Todos”. Profesional: al elegir uno, la API devuelve solo sus turnos, horarios y bloqueos y la grilla muestra una columna. Sillón: conserva todas las columnas, horarios y bloqueos, y muestra la ayuda visible “El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostrando.”. Ambos se combinan con AND; “Limpiar filtros” vuelve a “Todos” conservando la fecha. Si no hay turnos pero sí bandas, se muestra “Sin turnos para este filtro” sin borrar las bandas.

**Alternativas descartadas**: filtrar en el cliente horarios y bloqueos por sillón porque miente sobre el contrato y sobre la disponibilidad; ofrecer solo el filtro por profesional porque no cumple el scope.

### D9 — Estado en la URL

**Contexto**: recargar, compartir y usar atrás/adelante deben conservar día y filtros.

**Decisión**: `useSearchParams` con `date` (validada y real), `professionalId` y `chairId` (UUID opcional). Los cambios del usuario hacen `push`; valores inválidos, faltantes o desconocidos se descartan y se normalizan con `replace` (los desconocidos no se envían a la API). Un UUID inexistente se detecta contra el catálogo y muestra aviso con “Limpiar filtros”.

**Alternativas descartadas**: `sessionStorage` porque no es compartible y el guardián de C-26 prohíbe storage fuera de `tokenStore.ts`; contexto global porque no es compartible por URL y suma código innecesario.

### D10 — Carga, actualización, vacío, error, 401 y 403

**Contexto**: la vista debe comportarse bien al arrancar, al cambiar día/filtro y ante fallos; C-26 ya centralizó el `401` y el `403`.

**Decisión**: máquina de estados en el hook. **Carga inicial**: `LoadingState` con `role="status"`. **Actualización**: se conserva la grilla anterior con `aria-busy="true"` y “Actualizando…”, sin parpadeo. **Vacío**: grilla visible con “No hay turnos para este día”; sin profesionales, `EmptyState`. **Error de red/5xx**: `ErrorState` con mensajes de `getApiErrorMessages` y “Reintentar”; no cierra sesión. **400**: mensajes de validación. **401**: no se muestra error local; `sessionClient` limpia y `RequireAuth` redirige al login. **403**: `ErrorState` local con las `violations` y `clearActionErrors()` para no duplicar el banner de C-26. **Actualización manual** con botón “Actualizar agenda”; sin polling.

**Alternativas descartadas**: `LoadingState` en cada cambio porque parpadea y pierde contexto; manejar `401` localmente porque duplica C-26 y puede dejar dos mensajes.

### D11 — Accesibilidad de la grilla posicionada

**Contexto**: una grilla absoluta no es navegable ni legible por lector de pantalla; el proyecto exige accesibilidad básica.

**Decisión**: grilla visual por defecto más **toggle visible** “Ver como lista” que renderiza una tabla semántica con `<caption>` “Turnos del lunes 16 de noviembre de 2026”, encabezados `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado` con `scope="col"`, y filas en el mismo orden de la API. Cada tarjeta es un `<article>` con `aria-label` completo (hora, paciente, profesional, sillón, prestación, estado). Leyenda de estados visible. `aria-live="polite"` anuncia “Turnos del …: N”. Foco visible, orden de tabulación natural y sin `tabIndex` en tarjetas sin acción. No se implementa `role="grid"` con navegación de celdas.

**Alternativas descartadas**: solo `role="grid"` con flechas porque es mucho para C-27 y fácil de hacer mal; solo lista/tabla porque pierde la vista diaria y la lectura de huecos.

### D12 — Responsive para escritorio y tablet

**Contexto**: con 3–5 profesionales las columnas no entran en un tablet si se achican; hace falta scroll horizontal y referencias fijas.

**Decisión**: contenedor de scroll único con ancho mínimo por columna (`--agenda-column-min-width`, ~220 px) y columna de horas fija (`--agenda-time-gutter-width`, ~64 px). Encabezado de profesionales `sticky` arriba y columna de horas `sticky` a la izquierda; la esquina queda fija. Altura máxima del contenedor con scroll vertical interno. Barra de herramientas con `flex-wrap`, controles de al menos 44×44 px y sin información exclusiva de `hover`. `PageShell` puede ganar un `variant="wide"` aditivo si hace falta; no es obligatorio.

**Alternativas descartadas**: columnas que se achican porque con 5 profesionales quedan ilegibles; layout móvil separado porque el scope pide escritorio y tablet, no móvil.

### D13 — Tokens, CSS Modules y paleta existente

**Contexto**: la grilla necesita medidas que no existen y la agenda debe verse consistente con C-25/C-26.

**Decisión**: extender `tokens.css` con tokens de agenda (`--agenda-hour-height`, `--agenda-time-gutter-width`, `--agenda-column-min-width`, `--agenda-column-header-height`, líneas de grilla, fondos, bloqueo y tarjeta). Los colores de estado salen de `APPOINTMENT_STATUS_TOKENS` y `StatusBadge`; no se escriben HEX en TSX. Estilos con CSS Modules en `features/agenda`; constantes de layout puras en TS con tests. Sin fuentes remotas ni librería de UI.

**Alternativas descartadas**: estilos inline o HEX en componentes porque rompe el sistema de diseño y es difícil de testear; MUI/Chakra o un calendario de terceros porque agrega dependencia pesada, estética ajena y choque con C-25.

### D14 — La tarjeta de turno no hace nada

**Contexto**: el scope no pide interacción; C-29 crea y C-30 reprograma/cancela/cambia estado/muestra historial.

**Decisión**: la tarjeta es informativa, no clickeable, sin panel y sin `GET /api/appointments/{id}`. Toda la información está en la tarjeta y en la lista. El componente queda preparado para que C-30 le agregue un `onSelect` sin reescribirlo.

**Alternativas descartadas**: vista previa con detalle porque adelanta C-30 y suma endpoint/estados; navegar a `/turnos/{id}` porque la ruta no existe y pertenece a C-29/C-30.

### D15 — Router, menú y pantalla inicial

**Contexto**: hoy `/` muestra `HomePage` y el menú tiene todo deshabilitado; C-27 necesita `/agenda` y una pantalla inicial útil.

**Decisión**: ruta hija `agenda` dentro del layout protegido; el `index` de `/` pasa a `<Navigate to="/agenda" replace />` conservando la fecha; `menuFor` devuelve Agenda con `disabled: false` y `badge: null`, y el resto sigue deshabilitado con “Próximamente”. `AppShell` renderiza `NavLink` para los habilitados (con `aria-current`) y `<button disabled>` para los futuros. Se actualizan `menuFor.test.ts`, `AppShell.test.tsx` y `App.test.tsx`; no se toca el archive de C-26.

**Alternativas descartadas**: mantener `HomePage` en `/` porque suma un clic y deja una pantalla de bienvenida sin valor (fallback de bajo riesgo); convertir todo el menú en rutas porque C-28..C-33 todavía no existen.

### D16 — Datos, tipos y ausencia de librería de queries

**Contexto**: hay que pedir agenda, profesionales y sillones, manejar carreras y tipar la respuesta sin sumar una dependencia por una pantalla.

**Decisión**: `agendaApi.ts` define tipos y un parser mínimo de la forma de la respuesta (arrays y campos obligatorios; si no cumple, “Respuesta inesperada del servidor.”), y `fetchAgenda`, `fetchProfessionals` y `fetchChairs` reciben el `ApiClient`/`fetch` inyectado. `useAgenda.ts` dispara las tres requests en paralelo, usa `AbortController` más un id de request para ignorar respuestas viejas y `Promise.allSettled` para que un fallo de catálogo no bloquee la agenda. Se agrega `signal?: AbortSignal` aditivo a `RequestOptions` del cliente. No se agrega TanStack Query. El `timezone` de la respuesta actualiza el valor usado por la grilla.

**Alternativas descartadas**: TanStack Query porque es una dependencia y conceptos nuevos para una sola pantalla; fetch dentro de cada componente porque duplica requests, carreras y estados.

### D17 — Tests sin mocks

**Contexto**: C1 prohíbe `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos y MSW.

**Decisión**: unitarios puros para `agendaTime` y `agendaLayout` con datos literales y `Clock` fijo; `agendaApi` con `FetchFn` real que devuelve `new Response(...)` y guarda `init` en un array del test; `useAgenda` con un componente de prueba y fetch real (incluida una promesa pendiente para cancelación); `AgendaView` presentacional sin `useAuth`; `AgendaPage` con `AuthProvider` real, `createMemoryTokenStore`, `createMemoryRouter` y fetch que responde `/auth/me`, `/agenda`, `/professionals` y `/chairs`; `App`/`AppShell`/`menuFor` actualizados. Guardián de tiempo que escanea `src/features/agenda` y prohíbe getters locales y `toLocale*` sin `timeZone`; permite `getUTC*`, `Date.UTC` y `new Date()` solo en `clock.ts`. El test de zona bajo `TZ=Asia/Tokyo` se corre con el script de Vitest y se archiva como evidencia.

**Alternativas descartadas**: MSW porque C1 lo prohíbe y suma setup; `vi.mock`/`vi.spyOn`/`vi.fn` porque ocultan el comportamiento real.

### D18 — Verificación manual con backend real

**Contexto**: jsdom no valida layout, colores reales ni el `401` durante el uso; `verify-C-26.md` dejó ese `401` pendiente para C-27.

**Decisión**: script `docs/evidencias/manual-C-27.py` (o `.sh`) que toma la contraseña de `SEED_USER_PASSWORD`, inicia sesión con `recepcion` y crea por la API de C-22, para el lunes futuro **2026-11-16**: Quiroga 10:00 `Control` en Sillón 1, Sosa 09:00 `Control` en Sillón 2, cancela el de Sosa y vuelve a crear Sosa 09:00 para tener cancelado + activo, y crea un bloqueo de Quiroga 12:00–13:00 con motivo. Se verifican columnas/orden, hora local, estados, carriles, horarios, bloqueo, filtros (incluida la asimetría del sillón), navegación, URL, día vacío (domingo 2026-11-15), responsive 1024×768 y 768×1024 y el `401` durante el uso (token inválido en `sessionStorage` y “Actualizar”). Capturas de la autora: `C-27-agenda-dia.png`, `C-27-filtro-profesional.png`, `C-27-filtro-sillon.png`, `C-27-solapamiento-cancelado.png`, `C-27-vacio.png`, `C-27-sesion-vencida.png` y `C-27-tablet.png`. El `403` no es alcanzable a mano porque los tres roles leen la agenda; se cubre con test y se documenta.

**Alternativas descartadas**: solo tests automatizados porque no valida layout/colores ni cierra el pendiente de C-26; Playwright porque suma dependencia y queda fuera de scope.

### D19 — Frontera con C-28..C-33

**Contexto**: la agenda es la pantalla central y es fácil que absorba formularios, vista semanal, acciones y catálogos.

**Decisión**: alcance estricto de solo lectura. C-27 no hace vista semanal, crear/reprogramar/cancelar/cambiar estado/historial, columnas por sillón, ABM ni catálogos; no toca backend, dominio, migraciones, specs archivados, KB, `CHANGES.md`, `docker-compose.yml` ni `.env`; no agrega autenticación, storage, refresh, polling, drag & drop, notificaciones, filtro de estado ni librerías de UI/query; usa solo datos ficticios del seed.

**Alternativas descartadas**: adelantar “crear turno desde un hueco” porque es C-29 y mezcla governance MEDIO; adelantar el toggle día/semana porque es C-28 y duplica la grilla semanal.

## Reglas duras del frontend (heredadas de C-25/C-26)

- **C1, sin mocks ni reemplazos globales**: prohibido `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. `fetch` inyectado con `new Response(...)` real y `Clock` inyectado.
- **Sin `any` explícito ni `@ts-ignore`/`@ts-expect-error`**: `unknown` + narrowing; `tsconfig` en `strict`.
- **Mensajes del dominio tal cual**: `getApiErrorMessages` no traduce ni reformula.
- **Solo datos ficticios**: Quiroga, Sosa, Benítez, Ana Pérez, Bruno Acosta; nunca datos reales.
- **Storage confinado**: `sessionStorage` solo en `tokenStore.ts`; C-27 no agrega storage.
- **No commitear**: sin `git add`, `commit`, `push`, `restore`, `checkout` ni `stash`.
- **Calidad obligatoria**: `tsc --noEmit` sin errores y ESLint sin warnings antes de cerrar.

## Risks

| Riesgo | Mitigación |
|--------|------------|
| El navegador o el CI están en otra zona y la agenda muestra otro día/hora | D1/C1: `Intl` con `timeZone` explícito, `timezone` de la respuesta, tests con `TZ=Asia/Tokyo` y guardián de fuente. |
| Se usa un offset fijo `-03:00` y se rompe con otro `APP_TIMEZONE` o una fecha histórica | D1: prohibido el offset manual; todo pasa por `Intl`; el backend sigue siendo la autoridad. |
| Off-by-one en la etiqueta de fecha o en el `weekday` | D1/D3: etiquetas sobre mediodía UTC, `getUTCDay()`, tests de borde de medianoche. |
| Un bloqueo que cruza medianoche o un turno que termina a las `00:00` rompe la grilla | D4/D5/D7: clampeo a `[0, 1440]`, `24:00` → 1440, tests de 23–01 y 23:30–00:00. |
| Un turno de 5 minutos queda ilegible | D5/D11: altura mínima, texto corto, `aria-label` completo y vista de lista. |
| Cancelado + activo en el mismo horario se tapan | D5: carriles, test específico, borde discontinuo y badge. |
| El filtro por sillón “parece roto” porque siguen horarios y bloqueos | D8: ayuda visible, test y prueba manual; no se filtra en el cliente lo que la API no filtra. |
| Profesionales inactivos desaparecen o se mezclan | D6/D8: catálogo sin `active`, marca `(inactivo)` y orden estable. |
| El catálogo de profesionales falla y la grilla queda sin columnas | D6/D16: fallback a la unión de la agenda + aviso; la grilla sigue visible. |
| Un `professionalId`/`chairId` inexistente deja una vista vacía sin explicación | D6/D8/D9: aviso y “Limpiar filtros”; si el catálogo falló, aviso genérico. |
| Los tests de C-26 se rompen al habilitar Agenda o redirigir `/` | D15: actualizar `menuFor.test.ts`, `AppShell.test.tsx` y `App.test.tsx`; no tocar el archive. |
| El `401` se mezcla con un error local y muestra dos mensajes | D10: el hook ignora `401`; C-26 redirige; test. |
| El `403` se muestra dos veces (banner global + error local) | D10: `clearActionErrors()` al mostrar el error local; test de un solo mensaje. |
| Respuestas viejas pisan a las nuevas al cambiar día/filtro rápido | D16: `AbortController` + id de request; test con promesa pendiente. |
| La grilla absoluta no es accesible por teclado/lector | D11: tabla alternativa, `aria-label`, `aria-live`, leyenda y foco visible. |
| El layout no entra en tablet o el scroll pierde el encabezado | D12: ancho mínimo, `sticky`, scroll interno; prueba manual 768/1024. |
| `PageShell` con `max-width: 1120px` limita 5 columnas | D12: scroll interno; `variant="wide"` aditivo si hace falta; no bloqueante. |
| Se agrega TanStack Query o una librería de calendario y crece el bundle | D16/D13: prohibido en C-27; cliente y CSS Modules existentes. |
| Se usan datos reales de pacientes en capturas o tests | D18: solo seed ficticio. |
| El `403` manual no es alcanzable porque todos los roles leen la agenda | D18: test de componente y limitación documentada; no se toca el backend. |
| El pendiente de `401` de C-26 queda sin cerrar | D18: prueba manual durante el uso y registro en `verify-C-27.md`. |
