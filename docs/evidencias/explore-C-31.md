# Explore C-31 — `ui-vista-de-recepcion-por-sillon`

> Exploración en solo lectura sobre `main @ 59ddd2e` (C-29, C-30 y C-35 archivados). C-31 está pensado para implementarse sin tocar el backend; C-36 (`ui-adaptabilidad-movil`) se implementa antes que C-31 y define el contenedor móvil (scroll-snap y columna completa), que C-31 reutiliza. Este documento no modifica C-36.
>
> Entregable único de esta sesión: este archivo. No se ejecutó `propose`, no se escribió código y no se tocó `docs/evidencias/explore-C-36.md`.

---

## 1. Qué da la API para esta vista y qué falta

### 1.1. Lo que ya existe (verificado en el código, no en la KB)

| Necesidad de la vista | Qué da la API | Dónde |
|---|---|---|
| Turnos del día, de todos los profesionales | `GET /api/agenda` devuelve `AgendaResponse` con `appointments`, `workingHours`, `blocks`, `timezone` | `backend/app/api/agenda.py:41-89`, `backend/app/api/schemas.py:426-434` |
| Identificar el sillón de cada turno | `AgendaAppointmentResponse` serializa `chairId` y `chairName` (además de `professionalId`/`professionalName`, tiempos y estado) | `backend/app/api/schemas.py:400-434`; tipo espejo en `frontend/src/features/agenda/agendaApi.ts:10-23` |
| Listar sillones (columnas) | `GET /api/chairs` devuelve `ChairResponse { id, name, active }` | `backend/app/api/chairs.py:41-56`, `backend/app/api/schemas.py:109-114`; `fetchChairs` en `agendaApi.ts:303-323` |
| Permiso para ver la agenda y los sillones | `READ_AGENDA` y `CHAIR READ` están concedidos a los tres roles | `backend/app/auth/permissions.py:49` y `:67` |
| Filtrar por sillón | `AgendaQuery.chairId` — **filtra solo los turnos del sillón**, no horarios ni bloqueos | `backend/app/api/schemas.py:364-368`; `backend/app/services/agenda.py:79-90` |
| Filtrar por profesional | `AgendaQuery.professionalId` — filtra turnos, horarios y bloqueos de ese profesional | `backend/app/api/schemas.py:359-363` |
| Zona horaria de la respuesta | `AgendaResponse.timezone` (por defecto `America/Argentina/Buenos_Aires`) | `backend/app/api/agenda.py:69`, `backend/app/api/schemas.py:429` |
| Clic en tarjeta → detalle | C-30 ya dejó `AppointmentDetailDialog` reutilizable y `AgendaPage` ya cablea `onSelectAppointment` | `frontend/src/features/appointments/AppointmentDetailDialog.tsx:16-27`, `AgendaPage.tsx:274-299` |

Con esto, **el contrato alcanza para pintar columnas por sillón, turnos de varios profesionales en la misma columna y el detalle al hacer clic**.

### 1.2. Lo que falta y obliga a derivar en el frontend

- **No existe horario de atención por sillón.** `workingHours` es por profesional (`backend/app/services/agenda.py:86-90`; endpoints en `backend/app/api/working_hours.py:27-50`). Para una columna de sillón hay que **unir** los horarios de los profesionales que atienden ese día.
- **No existe bloqueo por sillón.** Los bloqueos son por profesional (`backend/app/api/blocks.py:25-51`; el servicio solo filtra por `professional_id`, no por `chair_id`). Un bloqueo profesional **no reserva el sillón**; por lo tanto, no se debe pintar como banda de indisponibilidad del sillón.
- **No existe endpoint de huecos libres.** El "Libre HH:MM–HH:MM" se calcula en el frontend restando a la unión de horarios los turnos que ocupan el sillón.
- `workingHours` y `blocks` no se filtran por `chairId`: si se pide `chairId`, la respuesta sigue trayendo **todos** los profesionales. Es correcto para la vista (el sillón recibe a cualquiera), pero el frontend no puede asumir que `workingHours` viene acotado por el filtro de sillón.

### 1.3. Regla de ocupación (crítica para los huecos libres)

`RN-AG-08` (`knowledge-base/05_reglas_de_negocio.md:20`): ocupan agenda **reservado, confirmado y atendido**; **cancelado y ausente liberan el horario**. Entonces los huecos libres se calculan restando **solo** los estados que ocupan. Un turno cancelado puede quedar dibujado dentro de una banda "Libre": es coherente (el estado visible dice "Cancelado"), pero hay que resolver el orden de capas para que el texto no quede tapado (ver D9).

---

## 2. Qué se puede reutilizar de la grilla actual y qué tests dependen de esa estructura

### 2.1. Reutilizable tal cual

| Pieza | Qué aporta | Dónde |
|---|---|---|
| `AgendaGrid` | Cabeceras, gutter de horas, bandas de horario, bandas de bloqueo, tarjetas accionables y lanes; recibe `columns` genéricas | `frontend/src/features/agenda/AgendaGrid.tsx:41-59`, `:56-69`, `:104-134`, `:136-181`, `:183-256` |
| `ProfessionalColumn` | Ya es una interfaz estructural (`id`, `label`, `fullName`, `workingHours`, `blocks`, `appointments`) y se puede extender con un campo opcional | `frontend/src/features/agenda/agendaLayout.ts:47-61` |
| Tarjeta accionable de C-30 | `<button>` con foco visible, `aria-label` con hora, paciente, profesional, servicio y estado; `onClick` → detalle | `AgendaGrid.tsx:194-224` |
| `assignLanes` | Resuelve solapamientos (p. ej. cancelado + activo en el mismo sillón) sin cambiar nada | `agendaLayout.ts:400-495` |
| `agendaTime` | `formatLocalTime`, `parseHHMM`, `formatMinutesToHHMM`, `appointmentRange`, `todayInTimeZone` | `frontend/src/features/agenda/agendaTime.ts:68-81`, `:181-202`, `:219-233`, `:89-91` |
| Constantes del eje | `AGENDA_DEFAULT_START_MINUTE=480`, `AGENDA_DEFAULT_END_MINUTE=1200`, `AGENDA_MIN_AXIS_MINUTES=240`, `AGENDA_MIN_APPOINTMENT_MINUTES=15` | `agendaLayout.ts:13-16` |
| Filtros y navegación | `AgendaToolbar` (fecha, profesional, sillón, Día/Semana) y `AgendaPage` (URL, carga, refresco, diálogo) | `AgendaToolbar.tsx:56-204`, `AgendaPage.tsx:45-299` |
| Tokens y contenedor de grilla | `--agenda-column-min-width: 220px`, `--agenda-hour-height`, `--agenda-offhours-bg`; C-31 reutiliza el mismo contenedor de día/semana que deja C-36 (scroll-snap y columna completa en celular) | `frontend/src/shared/styles/tokens.css:83-90`, `AgendaGrid.module.css:1-2`, `:16-18`, `:78-80` |
| `Clock` inyectado | `createFixedClock` para tests deterministas de "hoy" | `frontend/src/shared/clock.ts:11-17` |

**No reutilizar** como si fueran del sillón: `col.blocks` (son por profesional) ni `col.workingHours` de un solo profesional (hay que unirlos).

### 2.2. Qué tests existentes dependen de la estructura por profesional (no se tocan)

| Test | Dependencia |
|---|---|
| `frontend/src/features/agenda/agendaLayout.test.ts:141-224` | `groupByProfessional` (incluye :343 `groupByDayForProfessional`) |
| `frontend/src/features/agenda/AgendaView.test.tsx:121-144` | Cabeceras `agenda-column-header` y `agenda-column-<id>` con nombres de profesionales |
| `frontend/src/features/agenda/AgendaPage.test.tsx:203-208` | Nombres de profesionales en las cabeceras al cargar el día |
| `AgendaPage.test.tsx:542-573` | Toggle Día → Semana conserva filtros y renderiza 7 cabeceras |
| `AgendaPage.test.tsx` (~:607-624) | `view` inválido cae a Día y la URL no conserva `view` |
| `AgendaToolbar.test.tsx:108-164` | Renderiza `[Día, Semana]` sin prop `userRole`; si se agrega un tercer botón, debe quedar **oculto** en ese caso |
| `AgendaGrid.accionable.test.tsx:32-100` | Usa `groupByProfessional` y espera tarjetas accionables |
| `AgendaTable.test.tsx` | Columnas de tabla (incluye Profesional y Sillón) |
| `agendaStyles.test.ts:15-31` | Tokens requeridos; `:50-60` cero HEX en TSX; `:63-80` container query |

**Estrategia:** los cambios son aditivos. `view` pasa a `"day" | "week" | "chair"`; el tercer botón se renderiza solo si `userRole` es recepción/administrador (el test del toolbar no pasa `userRole`, así que no lo ve); `AgendaGrid` recibe props opcionales (`freeSlots`, `showProfessional`) cuyo default reproduce el comportamiento actual. Los tests nuevos van en archivos nuevos y con la Regla C1 (sin `vi.mock`/`vi.spyOn`/fake timers/MSW/`waitFor` largos; `fetch` con `createApiClient({ fetchFn })`; `Clock` con `createFixedClock`).

---

## 3. Decisiones (todas juntas, numeradas, con opciones y recomendación)

### D1 — (a) Cómo se entra a la vista: modo, ruta o filtro

- **A. Tercer modo en `/agenda` con `view=chair`** (recomendada): conserva fecha, filtros, carga y diálogo; el toolbar ya maneja `view` y `useSearchParams`; no agrega entrada de menú ni ruta nueva. `view` inválido sigue cayendo a Día.
- **B. Ruta propia `/agenda/por-sillon`**: separa responsabilidades, pero duplica navegación, carga y el manejo de `date`/filtros; además obliga a decidir qué pasa con "Día/Semana" en esa ruta.
- **C. Solo filtro `chairId` sobre la grilla de profesionales**: no cumple US-041 CA-1 (columnas por sillón); el filtro actual solo oculta columnas de profesionales.

**Recomendación: A.** `onSelectView` y `view` se amplían; `AgendaPage` sigue siendo el dueño del estado de URL. La etiqueta visible es "Por sillón"; el título de la página pasa a "Agenda por sillón" en ese modo.

### D2 — (b) Roles que ven la vista

- **A. Recepción y administración** (recomendada): coincide con la persona de US-041 (recepción) y con el uso de mostrador; el odontólogo conserva la agenda por profesional de C-28.
- **B. También odontólogo, en solo lectura**: la API lo permite (`READ_AGENDA` y `CHAIR READ` a los tres roles), pero agrega superficie y un modo que no está en la historia.
- **C. Todos con acciones**: no; las acciones ya viven en el detalle (C-30) y el sillón no cambia permisos.

**Recomendación: A.** El botón "Por sillón" se renderiza solo para `recepcion` y `administrador`. Si un odontólogo entra por URL con `view=chair`, se normaliza a Día (se quita `view=chair` de la URL) para que el botón activo y la vista no se contradigan. Nota: el gating es de UI; el backend sigue autorizando a los tres roles.

### D3 — (c) Cómo se muestran los huecos libres

- **A. Bloques explícitos con texto "Libre HH:MM–HH:MM"** (recomendada): dentro de la unión de horarios de atención del sillón, restando turnos que ocupan (`reservado`, `confirmado`, `atendido`). Texto visible + `aria-label` ("Sillón 1 libre de 10:30 a 11:00"); nunca solo color. Fuera de la unión se rotula **"Fuera de horario HH:MM–HH:MM"** (también con texto). Los **bloqueos no se pintan** en columnas de sillón (son por profesional y no reservan el sillón).
- **B. Solo fondo de color para "libre"**: viola accesibilidad (nada solo por color).
- **C. Pintar bloqueos profesionales como indisponibilidad del sillón**: engañoso: un profesional bloqueado no inhabilita el sillón para otro.

**Recomendación: A.** Umbral mínimo de hueco visible: **15 minutos** (`AGENDA_MIN_APPOINTMENT_MINUTES`, `agendaLayout.ts:15`); huecos menores no se rotulan para no saturar. El cálculo vive en un módulo puro nuevo (`agendaChairLayout.ts`) y se testea por unidad. Si el negocio necesita bloqueos u horarios **por sillón**, es otro change con backend; C-31 no los inventa.

### D4 — (d) Cómo se ve el turno en una columna de sillón

- **A. Reutilizar la tarjeta de `AgendaGrid` y mostrar el profesional en el cuerpo** (recomendada):
  - No compacta (≥45 min): fila 1 hora + `StatusBadge`; fila 2 paciente; fila 3 **nombre del profesional** (reemplaza `serviceName`; el servicio sigue en el `aria-label` y en el detalle).
  - Compacta (<45 min o columna angosta): fila 1 `HH:MM · Paciente`; fila 2 **profesional + `StatusBadge`** (el profesional trunca con ellipsis; el badge no se trunca). Entra en 56 px con la misma aritmética que ya documenta `AgendaGrid.module.css:246-250`.
  - Sigue siendo `<button>` con `onClick` → `AppointmentDetailDialog` (C-30), conservando `returnFocusRef` y foco visible.
- **B. Profesional solo en el `aria-label`**: no cumple "se lee el profesional en cada tarjeta" para quien ve la pantalla.
- **C. Componente de tarjeta nuevo solo para sillón**: duplica comportamiento y tests de accesibilidad.

**Recomendación: A.** Se implementa con una prop opcional `showProfessional` (default `false`), así los tests y el modo día/semana no cambian. En el modo sillón, el nombre del sillón ya está en la cabecera; la tarjeta prioriza hora y paciente y suma profesional, como pide la skill (`appointment-frontend-ux`).

### D5 — (e) Compatibilidad con C-36 (adaptabilidad móvil)

- **A. Reutilizar el MISMO contenedor de grilla que día y semana** (recomendada): C-36 se implementa antes y deja el contenedor con scroll-snap y columna completa en celular; la vista por sillón solo le pasa las columnas de `groupByChair` (1..N) y hereda ese comportamiento, sin crear un contenedor, un scroll ni un selector móvil propios.
- **B. Crear un contenedor o un selector de sillón mobile-only para C-31**: duplica lo que C-36 ya define y abre la puerta a dos comportamientos móviles distintos.
- **C. Ocultar la vista por sillón en móvil**: pierde la funcionalidad de recepción, que es justamente de mostrador.

**Recomendación: A.** Dependencia explícita: **C-36 antes que C-31**. C-31 consume el contenedor existente de `AgendaGrid` y no toca sus reglas de scroll-snap; el filtro `chairId` sigue disponible para acotar columnas, pero no es la estrategia móvil.

### D6 — (f) Rango horario y día por defecto

- **A. Eje = unión de horarios de atención del día, sin margen artificial de 1 h** (recomendada): si hay horarios, el eje va del mínimo inicio al máximo fin de la unión (incluyendo turnos existentes fuera de horario, si los hubiera); los huecos internos (p. ej. 13:00–15:00) se rotulan "Fuera de horario". Día por defecto = **hoy** según `Clock` (`todayInTimeZone(clock.now(), timezone)`), navegación ±1 día. Fin de semana o día sin horarios: banner "No hay horarios de atención para este día", eje de fallback 08:00–20:00, sin bloques "Libre" inventados.
- **B. Reutilizar `computeAxis` con su margen de 1 h (08:00–20:00)**: rotula como "Fuera de horario" los márgenes artificiales 08–09 y 19–20; confunde.
- **C. Eje fijo 08:00–20:00 siempre**: muestra horas que la clínica no atiende y alarga la grilla.

**Recomendación: A.** `computeChairAxis` se apoya en `parseHHMM`, `appointmentRange` y `formatMinutesToHHMM` (`agendaTime.ts`), y en `AGENDA_MIN_AXIS_MINUTES`/`AGENDA_DEFAULT_*` (`agendaLayout.ts:13-16`). **Corrección importante al enunciado del change:** en el seed, el horario L–V 09:00–13:00 y 15:00–19:00 aplica solo a **Quiroga y Benítez**; **Sosa atiende solo 09:00–13:00** (`backend/app/demo_data.py:61-70`, `morning_only=True` para `PROFESSIONALS[1]`). Los tests y la vista deben usar los datos literales, no asumir 9–13/15–19 para los tres. El seed **no** crea turnos ni bloqueos.

### D7 — Dónde vive el cálculo y cómo se reutiliza la grilla

- **A. Módulo puro nuevo `agendaChairLayout.ts` + extender `AgendaView` con `view="chair"`** (recomendada): `groupByChair`, `attentionIntervals`, `freeSlots`, `computeChairAxis` puros y testeables; `AgendaView` ya concentra cabecera, contador, toggle y `AgendaGrid`, así que una rama `isChairView` evita duplicar esa estructura.
- **B. `ChairAgendaView.tsx` separado**: más aislamiento, pero duplica cabecera/controles y puede divergir de Día/Semana.
- **C. Meter la lógica dentro de `AgendaGrid`**: mezcla cálculo de dominio de agenda con presentación y dificulta el test unitario.

**Recomendación: A.** Si la rama `chair` de `AgendaView` crece demasiado durante el apply, se extrae a `ChairAgendaView` sin cambiar el contrato. `AgendaGrid` solo recibe `columns` con `freeSlots` opcional y `showProfessional`.

### D8 — Origen de las columnas de sillón

- **A. Catálogo `GET /chairs` + unión defensiva con sillones que aparecen en turnos** (recomendada): muestra inactivos que aún tienen turnos, marcados "Sillón N (inactivo)"; si el catálogo falla, `useAgenda` ya avisa con `CATALOG_FALLBACK_WARNING` y los turnos siguen pintándose.
- **B. Solo sillones con turnos**: oculta sillones libres, que es justo lo que la recepción necesita ver.
- **C. Solo `active=true`**: puede ocultar un turno histórico de un sillón desactivado.

**Recomendación: A.** Orden por `name`; el filtro `chairId` reduce a una sola columna. `fetchChairs` no filtra por activo (`agendaApi.ts:303-323`), así que el catálogo completo ya está disponible.

### D9 — Estados y capas

- **A. Turnos cancelados/ausentes no ocupan (RN-AG-08) y las bandas "Libre"/"Fuera de horario" van detrás de las tarjetas** (recomendada): `workingHourBand` en z-index 0 (`AgendaGrid.module.css:122`), bloqueos en z-index 1 (`:132`) y tarjetas en z-index 2 (`:146`); las bandas nuevas siguen el mismo orden. Un cancelado puede quedar sobre una banda "Libre"; el texto del estado explica la situación.
- **B. Descontar también cancelados/ausentes para que no se superpongan**: contradice RN-AG-08 y oculta disponibilidad real.
- **C. No dibujar bandas donde hay cualquier tarjeta**: pierde el hueco libre real.

**Recomendación: A.**

### D10 — Filtros dentro de la vista por sillón

- **A. Mantener ambos filtros** (recomendada): `chairId` reduce columnas; `professionalId` filtra los turnos y **recalcula la unión de horarios** con ese profesional (sirve para responder "¿qué sillón puede usar el Dr. X?"). En modo sillón se oculta el texto de ayuda actual del filtro de sillón (`CHAIR_FILTER_HELP_TEXT`, `AgendaToolbar.tsx:6-7`) porque la columna ya es el sillón, y se reemplaza por una leyenda de la vista.
- **B. Ocultar filtros en modo sillón**: menos control para recepción y rompe la promesa de conservar estado.
- **C. Dejar el texto de ayuda actual**: dice que el filtro "solo afecta los turnos", falso en esta vista (también reduce columnas).

**Recomendación: A.** Al cambiar de modo se conservan `date`, `professionalId` y `chairId` (D1), igual que hace hoy el toggle Día/Semana (`AgendaPage.tsx:216-218`).

### D11 — Toggle grilla/lista y estado vacío

- **A. Mantener "Ver como lista" y adaptar el vacío** (recomendada): el toggle sigue disponible en la vista por sillón porque `AgendaTable` ya muestra la columna Sillón y es la alternativa accesible de C-27; no se oculta. El vacío "No hay turnos" se adapta a la vista por sillón: mensaje informativo ("No hay turnos para este día; los sillones se muestran libres") y la grilla con las bandas "Libre" sigue visible; el único vacío real es "No hay sillones configurados" cuando el catálogo está vacío.
- **B. Ocultar la lista en modo sillón**: quita la alternativa accesible de C-27 y la comparación con la tabla.
- **C. Mantener el vacío actual tal cual**: `AgendaView.tsx:143-147` oculta la grilla cuando no hay turnos y no hay filtros; en sillón eso borra la información de disponibilidad.

**Recomendación: A.** El contador `aria-live` se mantiene ("Turnos del [día]: N"); opcionalmente se agrega "Sillones con huecos libres: N" si no satura.

### D12 — Alcance del backend y de los tests

- **A. Cero cambios de backend en C-31; tests nuevos en archivos nuevos y un escenario = un test = una mutación** (recomendada). Si más adelante se piden horarios/bloqueos por sillón, va en un change aparte (hoy no existen en el modelo).
- **B. Agregar `chairId` a `workingHours`/`blocks` ahora**: cambio de dominio + migración + API, fuera del alcance y de la governance BAJO de C-31.
- **C. Tocar tests existentes para "acomodar" el tercer botón**: rompe la red de seguridad y oculta regresiones.

**Recomendación: A.** Archivos de test previstos: `agendaChairLayout.test.ts`, `AgendaView.chair.test.tsx` (o `ChairAgendaView.test.tsx` si se extrae), `AgendaPage.porSillon.test.tsx`, `agendaChairStyles.test.ts`. Se respeta la Regla C1 de la skill.

---

## 4. Escenarios propuestos (Dado / Cuando / Entonces)

> Cada escenario funcional se implementa como **un test** en un archivo nuevo (Regla C1). El escenario visual se verifica con capturas, no con jsdom.

### Funcionamiento esperado

**Escenario 1 — Turnos de distintos profesionales en la misma columna**
- **Dado** el lunes 2026-11-16 con Sillón 1/2/3 y dos turnos en Sillón 1: Quiroga 10:00–10:30 y Sosa 11:00–11:30; `Clock` fijo y `view=chair`.
- **Cuando** termina la carga de la agenda.
- **Entonces** se ven tres columnas ("Sillón 1", "Sillón 2", "Sillón 3"); la columna Sillón 1 contiene las dos tarjetas; cada tarjeta muestra en texto el profesional ("Dra. Laura Quiroga" / "Dr. Martín Sosa"); al hacer clic en una tarjeta se abre `AppointmentDetailDialog` con ese turno.

**Escenario 2 — Hueco libre entre dos turnos**
- **Dado** Sillón 1 con Quiroga 10:00–10:30 y Sosa 11:00–11:30, dentro del horario de atención.
- **Cuando** se renderiza la columna.
- **Entonces** se ve un bloque con texto "Libre 10:30–11:00" y `aria-label` "Sillón 1 libre de 10:30 a 11:00"; la información no depende solo del color.

**Escenario 3 — Sillón sin turnos**
- **Dado** Sillón 2 sin turnos, lunes con horarios de Quiroga/Benítez 09:00–13:00 y 15:00–19:00 y de Sosa 09:00–13:00.
- **Cuando** se renderiza la columna.
- **Entonces** se ven "Libre 09:00–13:00" y "Libre 15:00–19:00" y el tramo "Fuera de horario 13:00–15:00"; la columna no se oculta ni muestra solo "Sin turnos".

**Escenario 4 — Borde del corte del mediodía**
- **Dado** Sillón 1 con Quiroga 12:30–13:00 y Sosa 15:00–15:30 (el seed no tiene tramo 13:00–15:00).
- **Cuando** se renderiza.
- **Entonces** no hay "Libre" superpuesto a esos turnos y el tramo 13:00–15:00 se rotula "Fuera de horario". Un turno 12:45–13:15 no existe porque el dominio lo rechaza (`check_working_hours` exige que el turno quede contenido en un tramo; `backend/app/domain/rules/working_hours.py:177-217`). Si en el futuro se cargara un tramo contiguo 13:00–15:00, el turno que cruza sería válido y se vería como una tarjeta normal: **con el seed actual el "cruce" no aplica**, el borde real es terminar exacto a las 13:00 o empezar exacto a las 15:00.

**Escenario 5 — Filtro de un solo sillón**
- **Dado** `view=chair&chairId=<Sillón 2>`.
- **Cuando** se renderiza.
- **Entonces** solo se ve la columna Sillón 2; las demás no se renderizan; la URL conserva `date`, `chairId` y `professionalId`.

**Escenario 6 — Cambio de modo conserva fecha y filtros**
- **Dado** `/agenda?date=2026-11-18&professionalId=<Quiroga>&chairId=<Sillón 1>` en Día.
- **Cuando** se pulsa "Por sillón".
- **Entonces** la URL pasa a `...&view=chair` conservando `date`, `professionalId` y `chairId`; se pide la agenda del 2026-11-18 en una sola llamada (`from=to=2026-11-18`) y se ven las columnas por sillón. Al volver a "Día" se conserva todo y se quita `view=chair`.

**Escenario 7 — Rol con acceso**
- **Dado** una sesión de recepción o administración.
- **Cuando** se abre `/agenda`.
- **Entonces** se ve el botón "Por sillón" junto a "Día" y "Semana".

**Escenario 8 — Rol sin acceso**
- **Dado** una sesión de odontólogo.
- **Cuando** se abre `/agenda?view=chair`.
- **Entonces** no se ve el botón "Por sillón" y la vista cae a Día con la URL normalizada (sin `view=chair`).

**Escenario 9 — Día por defecto desde el Clock**
- **Dado** `Clock` fijo en `2026-11-16T12:00:00Z` y `/agenda?view=chair` sin `date`.
- **Cuando** se monta la página.
- **Entonces** se pide `from=2026-11-16&to=2026-11-16` y se muestra el lunes 16 (misma lógica de `todayInTimeZone` que usa la vista diaria).

**Escenario 10 — Día sin horarios de atención**
- **Dado** sábado 2026-11-21, sin `workingHours` (el seed solo carga lunes a viernes).
- **Cuando** se renderiza.
- **Entonces** se muestra el banner "No hay horarios de atención para este día", el eje de fallback 08:00–20:00 y **no** se inventan bloques "Libre".

### Adaptabilidad (capturas a cargo de Claude)

**Escenario 11 — 1440 / 768 / 390**
- **Dado** la vista por sillón con tres sillones.
- **Cuando** se toman capturas a 1440, 768 y 390 px.
- **Entonces** a 1440 entran las tres columnas y el gutter; a 768 la toolbar se envuelve y entran las tres columnas (3×220+64 = 724 ≤ 768) dentro del contenedor heredado; a 390 el contenedor de C-36 muestra una columna completa con scroll-snap y las tarjetas compactas mantienen legibles hora, paciente, profesional y estado, sin desbordes. Las capturas se guardan en `docs/evidencias/capturas/` y la verificación es visual (jsdom no mide layout).

---

## 5. Tamaño estimado y riesgos

### 5.1. Volumen estimado

| Tipo | Archivos | Líneas aproximadas |
|---|---|---|
| Producción nueva | `agendaChairLayout.ts` (puro) | ~140 |
| Producción modificada | `AgendaView.tsx` (+~40), `AgendaGrid.tsx` (+~50), `AgendaGrid.module.css` (+~35), `AgendaPage.tsx` (+~25), `AgendaToolbar.tsx` (+~15), `tokens.css` (+~6) | ~170 |
| Tests nuevos | `agendaChairLayout.test.ts` (~8 casos), `AgendaView.chair.test.tsx` (~6), `AgendaPage.porSillon.test.tsx` (~5), `agendaChairStyles.test.ts` (~2) | ~650-800 |
| **Total** | **~10-13 archivos** | **~1.000-1.200 líneas con tests** |

Estimación: **1 día de trabajo** (governance BAJO, sin backend, con Strict TDD). Los tests son la mayor parte del volumen.

### 5.2. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Ambigüedad de "atención del sillón" (unión de profesionales) | Medio: la disponibilidad puede no coincidir con la expectativa del negocio si en el futuro hay horarios/bloqueos por sillón | Documentarlo como decisión D3/D6; si se necesita por sillón, change aparte con backend |
| Bloqueos profesionales no reservan el sillón | Medio: la recepción podría asumir que un sillón está libre cuando el profesional está bloqueado | No pintar bloqueos en columnas de sillón; el turno del profesional bloqueado no existe, pero otro profesional sí puede usar el sillón (es correcto) |
| Diferencia del seed (Sosa solo mañana) | Bajo: tests que asuman 9–13/15–19 para todos fallarían | Usar datos literales del seed y citar `demo_data.py:61-70`; el hueco de la tarde solo existe por Quiroga/Benítez |
| Tarjeta compacta con profesional + estado | Bajo: desborde en columnas angostas | Profesional con ellipsis, badge sin truncar; verificación visual a 768/390 |
| Tercer botón rompe `AgendaToolbar.test.tsx` | Bajo | Renderizarlo solo con `userRole` recepción/administrador; el test existente no pasa `userRole` |
| `view` inválido y roles | Bajo | Mantener el fallback a Día y normalizar `view=chair` para odontólogo |
| Solapamiento cancelado/activo dentro de "Libre" | Bajo | Bandas detrás de tarjetas + lanes existentes; RN-AG-08 |
| C-36 se implementa antes y define el contenedor de grilla | Medio: si su contrato de scroll-snap/columna completa cambia, C-31 hereda el cambio | C-31 solo pasa `groupByChair` (1..N) al contenedor existente; no crea contenedor ni selector móvil propio; el contrato se fija en C-36 |
| Verificación visual no automatizable | Bajo | Capturas 1440/768/390 antes de archivar, como exige la skill |

---

## 6. Skill y MCP

- **Skill consultada:** `.agents/skills/appointment-frontend-ux/SKILL.md` (completa). De allí salen: Regla C1 de tests, uso de tokens (cero HEX en TSX), zona horaria desde la respuesta de la API, prioridad hora/paciente en tarjetas angostas, estado con texto visible (nunca solo color) y verificación visual 1440/768/390 antes de archivar.
- **Context7:** **no se consultó** en este explore. Las decisiones no introducen APIs nuevas de React Router: `useSearchParams` ya se usa en `AgendaPage`; si el apply necesita un detalle de la v6, se consultará antes de escribir código (primero `resolve-library-id`, luego `query-docs`).

---

## 7. Resumen y estado

- La API alcanza para columnas por sillón y turnos de varios profesionales; **no** hay horarios ni bloqueos por sillón ni endpoint de huecos: el "Libre" se deriva en el frontend.
- La grilla, la tarjeta accionable de C-30, `agendaTime`, `assignLanes` y los filtros se reutilizan; `AgendaGrid`/`AgendaView` se extienden de forma aditiva y los tests existentes quedan intactos.
- Quedan aceptadas D1 a D12 con dos ajustes: **D5** reutiliza el mismo contenedor de grilla que día/semana (heredado de C-36, que se implementa antes) y **D11** mantiene "Ver como lista" disponible y adapta el vacío "No hay turnos" en la vista por sillón. El detalle está en §8.

---

## 8. Decisiones tomadas

Se aceptan D1 a D12 de §3 con estas dos salvedades:

| Decisión | Estado | Detalle acordado |
|---|---|---|
| D1 | Aceptada | `view=chair` dentro de `/agenda`. |
| D2 | Aceptada | Recepción y administración; odontólogo cae a Día. |
| D3 | Aceptada | "Libre"/"Fuera de horario" con texto; sin bloqueos por sillón; umbral 15 min. |
| D4 | Aceptada | Profesional visible en la tarjeta; clic abre el detalle de C-30. |
| D5 | Aceptada con ajuste | La vista por sillón reutiliza el MISMO contenedor de grilla que día y semana, para heredar el scroll-snap y la columna completa en celular que define C-36. C-36 se implementa antes que C-31; C-31 no crea contenedor ni selector móvil propios. |
| D6 | Aceptada | Eje = unión de horarios; hoy desde `Clock`; navegación ±1 día. |
| D7 | Aceptada | `agendaChairLayout.ts` puro + `AgendaView` extendido. |
| D8 | Aceptada | Catálogo de sillones + unión defensiva con turnos. |
| D9 | Aceptada | Cancelados/ausentes no ocupan; bandas detrás de tarjetas. |
| D10 | Aceptada | Ambos filtros; ayuda del filtro de sillón adaptada. |
| D11 | Aceptada con ajuste | "Ver como lista" sigue disponible en la vista por sillón: la tabla ya muestra la columna Sillón y es la alternativa accesible de C-27; no se oculta. El vacío "No hay turnos" se adapta a la vista por sillón, sin borrar la grilla con los huecos libres. |
| D12 | Aceptada | Cero backend; tests nuevos en archivos nuevos (Regla C1). |

**Estado:** explore cerrado con estas decisiones. No se ejecuta `propose` hasta que la autora lo pida.
