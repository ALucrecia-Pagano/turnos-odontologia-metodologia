# Explore C-28 — `ui-agenda-semanal`

Fecha: 2026-11-08  
Fase: 6 — Interfaz web (React + TypeScript + Vite), sobre la API probada  
Governance: **BAJO** (vista de solo lectura; no modifica datos ni altera seguridad, según `CHANGES.md` §[C-28])  
Dependencias en `CHANGES.md`: `C-27` (y por transitividad `C-26`, `C-25`, `C-24`, `C-23`, `C-22`, `C-19`).

> Este explore es estrictamente analítico y de planificación: **no** ejecutó commits, no leyó ni modificó `.env`, no usó comandos de orchestrator prohibidos, no configuró servidores MCP y no creó la carpeta del change ni el proposal (reservado para `/opsx:propose`).
> Fuentes consultadas: `CHANGES.md`, `knowledge-base/` (03, 04, 05, 06, 07, 08, 09), `openspec/specs/agenda-api/spec.md`, `openspec/specs/frontend-agenda/spec.md`, código de C-27 en `frontend/src/features/agenda/`, la skill `appointment-frontend-ux` y la evidencia de consulta a Context7 en `docs/skills-mcp/evidencias/04-uso-context7.md`.

---

## 1. Alcance de C-28 según `CHANGES.md` y qué queda afuera

### Qué entra en C-28

1. **Vista semanal por profesional** con turnos organizados por día (7 columnas: lunes a domingo) para un profesional seleccionado (US-040 CA-2).
2. **Alternancia fluida entre vista diaria y semanal** desde la agenda (`[ Día | Semana ]`), preservando fecha y filtros aplicables.
3. **Navegación semanal**: semana anterior (`-7` días), semana siguiente (`+7` días), "Hoy" (semana que contiene la fecha actual según `Clock`), y selector de fecha.
4. **Una sola llamada a la API**: `GET /api/agenda?from=Lunes&to=Domingo&professionalId=...` obteniendo turnos, horarios y bloqueos del rango de 7 días en un único sobre.
5. **Reutilización de componentes y módulos de C-27**: cálculo de eje temporal (`computeAxis`), asignación de carriles (`assignLanes`), formateo de instantes con zona horaria de la API (`agendaTime.ts`), badges y tokens (`tokens.css`).
6. **Manejo responsivo (1440 px y 768 px)**: grilla con scroll horizontal, canal de horas sticky, cabeceras sticky y tarjetas adaptadas a columnas estrechas (< 260 px) mediante container queries.
7. **Accesibilidad completa**: anuncios `aria-live` de cantidad de turnos en la semana, `aria-label` completo por tarjeta, texto visible para estados, foco visible y alternativa accesible en tabla/lista.
8. **Estados de pantalla**: carga, vacío (semana sin turnos), error con reintento, `401` delegado en `TokenStore` (C-26) y `403` con mensaje visible.
9. **Tests de componentes bajo regla C1**: sin mocks de módulo, inyectando `fetch` y `Clock`, testeando los 7 días, turnos en el día correcto en hora local y selector de profesional.

### Qué queda explícitamente afuera

- **Modificaciones en el backend o en la API**: `GET /api/agenda` ya soporta rangos de hasta 31 días y filtros; no se toca nada de `backend/`.
- **Crear turno**: scope de C-29 (formulario de alta con reporte de violaciones).
- **Reprogramar, cancelar y cambiar estado**: scope de C-30.
- **Vista de recepción por sillón**: scope de C-31 (diferenciador con columnas por sillón).
- **ABM de horarios y bloqueos**: scope de C-32.
- **ABM de profesionales, sillones, prestaciones y pacientes**: scope de C-33.
- **Librerías externas nuevas**: no se agregan paquetes de calendario ni librerías de estado.

---

## 2. Hechos ya verificados

1. **Rango de hasta 31 días en `GET /api/agenda`**:
   - Spec `agenda-api`: Requirement *Parámetros y validación de la agenda* establece que `from` y `to` son fechas locales obligatorias (`AAAA-MM-DD`, `to` inclusivo) con un rango permitido de hasta 31 días.
   - Escenarios verificados en spec: *La agenda de una semana devuelve los turnos del rango* (`from` lunes L y `to` L+6), *Un rango de ocho días cruza dos semanas*, *Un rango de 31 días cruza meses*.
2. **Capacidad del cliente frontend (`agendaApi.ts`)**:
   - `fetchAgenda(client, params: FetchAgendaParams)` ya recibe `from` y `to` arbitrarios, serializándolos en query string junto con `professionalId` y `chairId`.
   - Por ende, la semana de 7 días se obtiene en **una sola llamada HTTP**, sin requerir endpoints adicionales ni transformaciones en el servidor.

---

## 3. Plan de Decisiones (`D1` a `D6`)

### D1 — Representación de la semana en la URL y primer día de la semana

**Problema**: La vista diaria usa `/agenda?date=YYYY-MM-DD`. En vista semanal, el usuario debe poder compartir el enlace, recargar la página o volver atrás en el historial y ver la misma semana. Hay que definir qué parámetros se agregan y cuál es el día de inicio de la semana.

- **Opción A (Recomendada)**: Mantener `date=YYYY-MM-DD` como fecha de anclaje y agregar `view=week` (con `view=day` como valor por defecto cuando no está presente). La semana se define canónicamente de **lunes (día 1) a domingo (día 7)** (norma ISO-8601 y convención en Argentina).
  - Si la URL tiene `/agenda?date=2026-11-18&view=week` (miércoles), la vista calcula el lunes previo `2026-11-16` y el domingo `2026-11-22`.
  - La función helper `weekRangeOf(dateStr)` en `agendaTime.ts` calcula:
    `monday = addDays(dateStr, 1 - weekdayOf(dateStr))` y `sunday = addDays(monday, 6)`.
- **Opción B**: Reemplazar `date` por dos parámetros explícitos `from=YYYY-MM-DD&to=YYYY-MM-DD&view=week`.
- **Opción C**: Iniciar la semana en domingo (convención estadounidense).

**Recomendación**: **Opción A**.  
**Respaldo**:
- Convención argentina y de la cátedra: en `knowledge-base/05_reglas_de_negocio.md` y `knowledge-base/04_modelo_de_datos.md` (`WorkingHours`), los días de la semana van de 1 (lunes) a 7 (domingo).
- `agendaTime.ts` ya implementa `weekdayOf(dateStr)` devolviendo `1` para lunes y `7` para domingo.
- Mantener `date` uniforme simplifica la alternancia con la vista diaria: no hay que reescribir ni borrar parámetros de fecha al cambiar de vista.
- Context7 evidencia 04 ratifica que `useSearchParams` de `react-router-dom@6.30.6` administra fluidamente múltiples parámetros (`date`, `view`, `professionalId`, `chairId`).

---

### D2 — Alternancia entre vista diaria y semanal y preservación de estado

**Problema**: ¿Cómo conmuta el usuario entre día y semana y qué ocurre con los filtros y la fecha al alternar?

- **Opción A (Recomendada)**: Agregar un control segmentado `[ Día | Semana ]` en `AgendaToolbar`.
  - Al hacer clic en "Semana": se navega con `setSearchParams` estableciendo `view: "week"`. Se **conserva la fecha actual** `date` (la semana mostrada contiene ese día), se **conserva el `professionalId`** y se **conserva el `chairId`**.
  - Al hacer clic en "Día": se navega con `setSearchParams` removiendo `view` (o `view: "day"`). Se **conserva la fecha `date`** (se aterriza exactamente en el día que se estaba visualizando o en el ancla), y se conservan los filtros.
- **Opción B**: Crear rutas independientes `/agenda/diaria` y `/agenda/semanal`.
- **Opción C**: Restablecer la fecha a "hoy" y limpiar filtros cada vez que se cambia de vista.

**Recomendación**: **Opción A**.  
**Respaldo**:
- `knowledge-base/06_funcionalidades.md` §US-040: "alternar día/semana desde la agenda".
- Una única ruta `/agenda` con parámetros de consulta refleja el patrón idiomático de React Router v6 documentado en la evidencia 04 de Context7 (`useSearchParams`).
- Preservar la fecha y los filtros garantiza la continuidad de la tarea del operador (recepción u odontólogo).

---

### D3 — Layout de 7 días en escritorio y tablet (768 px), y selector de profesional

**Problema**: En la vista diaria hay 1 columna por profesional (para un solo día). En la vista semanal (US-040 CA-2: "vista semanal por profesional (selector de profesional)"), las columnas representan los **7 días** de la semana para **un** profesional. ¿Qué ocurre si no hay un profesional seleccionado? ¿Cómo se acomodan 7 columnas en escritorio (1440 px) y en tablet (768 px)?

- **Selector de profesional**:
  - **Opción A (Recomendada)**: La vista semanal requiere un profesional en foco. Si en la URL no viene `professionalId` (o viene vacío):
    - Si el usuario es de rol `odontologo`, se selecciona automáticamente su propio `professionalId` (conforme a su identidad en el token).
    - Si el usuario es `recepcion` o `administrador`, se selecciona por defecto el primer profesional activo en orden alfabético (ej. `Dra. Laura Quiroga`), actualizando la URL de forma transparente (`replace: true`).
    - El selector en `AgendaToolbar` destaca que en vista semanal se visualiza la semana del profesional elegido.
  - **Opción B**: Mostrar una pantalla intermedia "Por favor seleccione un profesional" con un selector grande.
  - **Opción C**: Mostrar los 7 días multiplicados por todos los profesionales (21+ columnas).

- **Layout y Responsive**:
  - **Escritorio (1440 px)**: Las 7 columnas (lunes a domingo) más el canal de horas (`64 px`) disponen de aproximadamente `180–195 px` de ancho por día. Con este ancho entran perfectamente en la pantalla sin solapamiento destructivo.
  - **Tablet (768 px)**: 7 columnas con ancho mínimo de legibilidad (`--agenda-column-min-width: 180px` o `220px`) totalizan más de `1300 px`, lo que supera los `768 px`.
    - Se reutiliza la arquitectura de `AgendaGrid.module.css`: contenedor con scroll horizontal (`overflow-x: auto`), canal de horas sticky a la izquierda (`position: sticky; left: 0; z-index: 2`) y fila de cabeceras sticky arriba (`position: sticky; top: 0; z-index: 3`).
    - En columnas de ancho menor a `260 px`, la container query `@container agenda-column (width < 260px)` (definida en C-27 y exigida por la skill `appointment-frontend-ux`) conmuta las tarjetas compactas (< 45 min) a dos líneas:
      - Línea 1: `HH:MM · Paciente` con ellipsis.
      - Línea 2: `StatusBadge` con texto visible en `--font-size-xs`.
      - De este modo, el estado nunca tapa al paciente ni a la hora.

**Recomendación**: **Opción A**.  
**Respaldo**:
- US-040 CA-2 explicita: "vista semanal por profesional (selector de profesional)".
- Skill `appointment-frontend-ux` §Prioridad de la información en tarjetas angostas y §Tokens de diseño.
- Validación de accesibilidad de C-27 (revisión visual en 1440 y 768 px).

---

### D4 — Reutilización de la arquitectura de C-27 sin duplicación de código

**Problema**: C-27 construyó módulos robustos (`agendaTime.ts`, `agendaLayout.ts`, `AgendaGrid.tsx`, `AgendaToolbar.tsx`, `useAgenda.ts`). ¿Cómo incorporamos la vista semanal sin duplicar componentes ni lógica matemática?

- **Opción A (Recomendada — Abstracción común de columnas)**:
  - En `agendaLayout.ts`: Generalizar la interfaz de columna a un modelo unificado `AgendaLayoutColumn`:
    - En vista diaria: Cada columna representa un **profesional** en una fecha fija (`id = professional.id`, `title = professional.fullName`, `date = activeDate`).
    - En vista semanal: Cada columna representa un **día** para el profesional seleccionado (`id = dateStr`, `title = "Lunes 16/11"`, `date = dateStr`).
    - Ambas columnas poseen la misma estructura de datos: `workingHours` aplicables al día/profesional, `blocks` solapados con ese día, y `appointments` de esa columna.
  - `assignLanes`: Ya recibe `(appointments, { date, timezone, axisStartMinute, axisEndMinute })`. Funciona idénticamente para cada columna pasándole su fecha correspondiente.
  - `computeAxis`: Se calcula sobre la unión de horarios, bloqueos y turnos de toda la semana para que las 7 columnas compartan una misma escala horaria y un mismo canal de horas.
  - `useAgenda.ts`: Ampliar los parámetros para admitir `from` y `to` (o `date` y `viewMode`), disparando un único `fetchAgenda(client, { from: monday, to: sunday, professionalId, chairId })`.
  - `AgendaGrid.tsx`: Consume la lista de columnas genéricas, renderizando las bandas de horario, bloques y tarjetas de turno con los mismos estilos y tokens.
- **Opción B**: Crear componentes paralelos duplicados: `WeeklyAgendaGrid.tsx`, `weeklyLayout.ts`, `useWeeklyAgenda.ts`.

**Recomendación**: **Opción A**.  
**Respaldo**:
- Principio DRY y arquitectura limpia (`knowledge-base/08_arquitectura_propuesta.md`).
- La regla C1 de tests y los tests de regresión de C-27 seguirán protegiendo la vista diaria mientras validan la semanal.

---

### D5 — Casos borde: navegación, cancelados, días sin horario, zona horaria y "hoy"

1. **Navegación semanal (cambio de semana)**:
   - Los botones `Anterior` y `Siguiente` en modo semanal desplazan `+/- 7` días calendarios (`addDays(effectiveDate, -7)` y `addDays(effectiveDate, 7)`).
   - "Hoy" salta a la semana que contiene la fecha actual según el `Clock` inyectado.
   - Si la semana cruza fin de mes o fin de año (ej. 28 de diciembre a 3 de enero), `addDays` (que usa `Date.UTC` a las 12:00) maneja los cambios de mes/año de forma exacta sin desfasajes de huso horario.
2. **Turnos cancelados**:
   - Se incluyen en la columna del día correspondiente, atenuados (`styles.appointmentCancelled`), con la etiqueta de texto `"Cancelado"` y compartiendo carriles con turnos activos mediante `assignLanes`.
3. **Días sin horario de atención (ej. domingos o francos)**:
   - La columna del día sin horarios muestra el fondo de horas no laborales (`--agenda-offhours-bg`). Si tiene turnos asignados (o bloqueos), estos se dibujan visiblemente; si no tiene turnos, muestra el indicador `"Sin turnos"`.
4. **Zona horaria y medianoche**:
   - Cada turno se asigna a su día local según `formatLocalDate(appt.startAt, timezone)` (usando el `timezone` de la respuesta de la API).
   - Un turno que finaliza a las `00:00` pertenece exclusivamente al día de inicio (conforme a la spec `agenda-api` y `agendaTime.ts`).
5. **Semana con el día de hoy**:
   - Si la fecha de hoy (según el `Clock` inyectado) cae dentro de la semana visible, la cabecera del día de hoy se resalta con un estilo distintivo accesible (usando `--color-primary` o badge `"Hoy"`), mejorando la orientación del usuario.

**Respaldo**:
- `appointment-frontend-ux` (§Zona horaria, §Accesibilidad, §Tokens).
- Spec `frontend-agenda` y spec `agenda-api`.

---

### D6 — Estados de pantalla: carga, vacío, error y 401/403

1. **Carga (`loading` y `refreshing`)**:
   - Carga inicial: `LoadingState` con `role="status"` y mensaje accesible.
   - Refresco/cambio de semana con datos previos: indicador no bloqueante en la cabecera (`aria-busy="true"`, "Actualizando…").
2. **Vacío**:
   - Si en toda la semana no hay ningún turno para el profesional/filtros seleccionados: mensaje `EmptyState` ("No hay turnos para esta semana"). Si hay filtro activo de sillón: banner "Sin turnos para este filtro".
3. **Error y reintento**:
   - Ante falla de red o error 5xx: `ErrorState` con los mensajes correspondientes y botón `Reintentar` conectado a `refresh()`.
4. **Sesión (401 y 403)**:
   - `401`: Delegado a C-26; `TokenStore` descarta el token y redirige a `/login` con aviso de sesión vencida. La vista no muestra error local.
   - `403`: Muestra las violaciones devueltas por la API en un `ErrorState` sin cerrar la sesión.

**Respaldo**:
- `appointment-frontend-ux` (§Checklist, §Token de sesión).
- Manejo uniforme de errores en `frontend/src/shared/api/errors.ts` y C-26.

---

## 4. Uso de la skill y del MCP

### 4.1. Detección y carga de la skill `appointment-frontend-ux`
- **Confirmación**: La skill **fue detectada como skill registrada** en el entorno (`appointment-frontend-ux`, ubicada en `.agents/skills/appointment-frontend-ux/SKILL.md`).
- Adicionalmente, se leyó su archivo canónico `SKILL.md` en su totalidad para seguir de manera rigurosa su checklist "al preparar o revisar un change de UI".

### 4.2. Influencia de las reglas de la skill en las decisiones
| Sección de la skill `appointment-frontend-ux` | Decisión influenciada | Aplicación concreta en C-28 |
|---|---|---|
| **§Stack exacto y cuándo consultar Context7** | D1, D2 | Respeto estricto a las versiones fijadas (`react-router-dom@6.30.6`, React 18, Vite 5, Vitest 3). El hook `useSearchParams` se consume desde `react-router-dom` y no desde `react-router`. |
| **§Tokens de diseño: nunca colores sueltos** | D3, D5 | Ningún color o tamaño hardcodeado. Reutilización de `--agenda-offhours-bg`, `--agenda-working-bg`, `--agenda-column-min-width`, `--agenda-hour-height`, `--agenda-card-min-height`, y `APPOINTMENT_STATUS_TOKENS`. |
| **§Accesibilidad** | D3, D5, D6 | Todo estado de turno se comunica con **texto visible** (`StatusBadge`), nunca solo con color. Se mantienen `aria-label` completos en tarjetas, controles interactivos con tamaño mínimo 44×44 px, foco visible y región `aria-live` para anunciar turnos de la semana. |
| **§Prioridad de la información en tarjetas angostas** | D3 | En la vista de 7 días, las columnas tienen anchos reducidos (< 260 px); se aplica el formato en dos líneas (línea 1: hora y paciente con ellipsis; línea 2: status badge con texto). La hora y el paciente siempre mandan. |
| **§Zona horaria: siempre desde la respuesta de la API** | D1, D5 | El parámetro `timezone` proviene del sobre de `GET /api/agenda` con fallback inicial en `DEFAULT_AGENDA_TIMEZONE`. Los instantes UTC se proyectan a hora local mediante `agendaTime.ts`. |
| **§Token de sesión: solo en features/auth/tokenStore.ts** | D6 | C-28 no almacena ni lee tokens en almacenamiento local; la autenticación y el manejo de 401 quedan completamente delegados en la capa de auth de C-26. |
| **§Regla C1 de tests: sin mocks de módulo** | Scope de tests | En los tests de C-28 queda prohibido `vi.mock`, `vi.spyOn` o fake timers. Se inyecta `fetchFn` con `createApiClient`, se inyecta `createFixedClock` y se montan las rutas con `createMemoryRouter` y `RouterProvider`. |
| **§Verificación visual obligatoria antes de archivar** | Scope de verificación | Planificación de capturas en escritorio (1440 px) y tablet (768 px) para verificar la grilla de 7 días y la ausencia de recortes de texto previo al archivo del change. |

### 4.3. Decisiones apoyadas en la Evidencia 04 de Context7
- La evidencia en `docs/skills-mcp/evidencias/04-uso-context7.md` documenta la consulta a Context7 sobre `useSearchParams` en React Router v6:
  - **Decisión D1 y D2**: Se confirmó que `useSearchParams` devuelve `[searchParams, setSearchParams]`, que `setSearchParams(newParams)` dispara la navegación en el router, y que acepta objetos simples o instancias de `URLSearchParams`.
  - **Manejo de imports**: La evidencia alertó que la documentación genérica de Context7 para react-router muestra imports de la v7 (`import { useSearchParams } from "react-router"`), mientras que en este proyecto con `react-router-dom@6.30.6` el import canónico y seguro es:
    ```tsx
    import { useSearchParams } from "react-router-dom";
    ```
  - **Sincronización de parámetros**: Se aplica la forma de objeto o `URLSearchParams` para alternar entre día y semana (`view="week"`), cambiar de semana y mantener filtros (`date`, `professionalId`, `chairId`).

### 4.4. Consultas pendientes a Context7
- **Ninguna consulta pendiente**: Todas las APIs requeridas para este change (`useSearchParams`, `createMemoryRouter`, `RouterProvider` de `react-router-dom@6.30.6`, hooks estándar de React 18 como `useState`/`useEffect`/`useCallback`, y utilidades de `Intl.DateTimeFormat`) ya existen en el código del repositorio o fueron confirmadas de forma fehaciente en la evidencia 04. No se introduce ninguna API no comprobada.

### 4.5. Revisión crítica de la skill y del MCP
1. **En qué ayudó la skill**:
   - Evitó desviaciones de diseño recordando la lección aprendida en C-27: nunca usar puntos de color sin texto para los estados.
   - Proveyó la solución probada para la disposición responsive de columnas angostas (< 260 px), crucial al pasar de 2–3 columnas en vista diaria a 7 columnas en vista semanal.
   - Recordó la regla C1 de testing, previniendo el uso indebido de `vi.mock` o timers falsos que invalidarían los tests del TP.
2. **En qué se quedó corta la skill**:
   - El checklist y los ejemplos de la skill están muy orientados a la vista diaria (`groupByProfessional`, columnas por profesional).
   - No especificaba cómo modelar la vista semanal de un profesional individual dividida en 7 días calendario. Esta abstracción tuvo que ser resuelta en este explore (Decisión D4: generalización a `AgendaLayoutColumn`).
3. **Discrepancias entre la skill y el código**:
   - La skill referencia `APPOINTMENT_STATUS_TOKENS` y `StatusBadge`, pero no menciona el diccionario complementario `STATUS_LABELS` que C-27 debió crear en `AgendaGrid.tsx` para los textos accesibles en español de los `aria-label`.
   - La tabla de stacks de la skill destaca `React Router DOM 6.30.6 (API de la v6, no la v7)`. La consulta a Context7 (Evidencia 04) demostró que el servidor de documentación de React Router mezcla documentación con sintaxis v7 (import desde `"react-router"`), validando la advertencia de la skill de no importar desde `"react-router"`.

---

## 5. Resumen del Explore y Estado de Preparación

El change `C-28` (`ui-agenda-semanal`) está completamente analizado y acotado:
- La API de agenda ya soporta la consulta semanal sin tocar el backend.
- Se reutiliza la matemática temporal, el cálculo de ejes, la asignación de carriles y los estilos de C-27.
- La alternancia día/semana y la navegación se gestionan de forma elegante en la URL con `useSearchParams` (`react-router-dom@6.30.6`).
- Se garantiza total conformidad con la accesibilidad, responsive en 1440 y 768 px, y la estricta regla de testing C1.

Queda a la espera de la revisión y confirmación de las decisiones planteadas antes de proceder con `/opsx:propose`.
