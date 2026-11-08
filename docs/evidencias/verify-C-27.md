# Verificación de C-27 — ui-agenda-diaria

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 28/28 en [tasks.md](../../openspec/changes/ui-agenda-diaria/tasks.md).
- Vitest: 35 archivos, 127 tests en verde (85 preexistentes + 42 nuevos de C-27); `tsc` y ESLint sin errores ni warnings.
- Mutaciones: 47/47 hicieron fallar su test (una por cada test nuevo o actualizado de C-27); mutaciones inválidas: 0; SHA-256 de producción intacto.
- Trazabilidad: 32 escenarios, 0 problemas.
- Precondición (GATE 16): [precondicion-C-27.txt](precondicion-C-27.txt); C-26 y dependencias archivadas.
- Línea de base desde `frontend/`: [baseline-C-27.txt](baseline-C-27.txt) (85 passed, `tsc` y ESLint limpios).
- `tsc --noEmit` (strict): [tsc-C-27.txt](tsc-C-27.txt).
- ESLint (`--max-warnings 0`): [eslint-C-27.txt](eslint-C-27.txt).
- Vitest: [vitest-C-27.txt](vitest-C-27.txt).
- Mutaciones: [mutaciones-C-27.txt](mutaciones-C-27.txt), generado por [mutaciones-C-27.py](mutaciones-C-27.py).
- Trazabilidad: [trazabilidad-C-27.txt](trazabilidad-C-27.txt), generado por [trazabilidad-C-27.py](trazabilidad-C-27.py).
- Verificación manual y HTTP contra backend real: [manual-C-27.txt](manual-C-27.txt) y [http-C-27.txt](http-C-27.txt).
- Validación OpenSpec y `git diff --check`: [validate-C-27.txt](validate-C-27.txt).
- Rojos (TDD): carpeta [red-C-27/](red-C-27/).

## Regla C1 y zona horaria (D1, D2, D17)

- **Sin mocks ni reemplazos globales**: todo el código de test usa funciones `fetch` inyectadas que devuelven instancias reales de `Response` y `createApiClient({ fetchFn })`. Prohibidos `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.useFakeTimers` y MSW. El tiempo se fija exclusivamente inyectando la interfaz `Clock { now(): Date }`.
- **Zona horaria explícita desde la respuesta**: ningún componente ni función de presentación escribe `"America/Argentina/Buenos_Aires"` a mano. Todas las horas y fechas mostradas se formatean con el `timezone` que devuelve `GET /api/agenda`.
- **Respaldo en un único archivo**: la constante `DEFAULT_AGENDA_TIMEZONE` vive únicamente en `frontend/src/features/agenda/agendaConfig.ts` y solo se utiliza antes de recibir la primera respuesta del servidor. Un grep de `"Buenos_Aires"` en `frontend/src` fuera de los archivos de test devuelve exactamente esa única línea en `agendaConfig.ts`.
- **Independencia del entorno local (`TZ=Asia/Tokyo`)**: se comprobó ejecutando `agendaTime.test.ts` con `TZ=Asia/Tokyo` (archivado en [red-C-27/1.3-tz-tokyo.txt](red-C-27/1.3-tz-tokyo.txt)), verificando que `13:00Z` se formatea inequívocamente como `10:00` en Buenos Aires y la fecha como `2026-11-16`, sin verse afectada por la zona horaria del host o del proceso Node.
- **Guardián de Date**: el test guardián en `src/features/agenda/agendaTimeGuard.test.ts` prohíbe getters locales de `Date` (`getHours`, `getMinutes`, `getDate`, etc.) y `toLocale*` sin `timeZone`, y confina `new Date()` sin argumentos a `src/features/agenda/clock.ts`.

## Cierre del pendiente de 401 de C-26 (D10, D18)

- En C-26 se documentó que la verificación manual del mensaje `"La sesión venció. Iniciá sesión de nuevo."` ante una petición protegida que responde `401` durante el uso se completaría en C-27, al contar con una pantalla operativa.
- En la tarea 16.6 se comprobó manualmente en el navegador adulterando el token en `sessionStorage` a `"token-invalido"` y presionando el botón "Actualizar agenda": `GET /api/agenda` respondió `401 INVALID_TOKEN`, la sesión se cerró, se redirigió a `/login` y se mostró el banner `"La sesión venció. Iniciá sesión de nuevo."`, cerrando formalmente el pendiente de C-26.

## Limitación del 403 manual (D18)

- La especificación de permisos de la agenda establece que los tres roles del sistema (`administrador`, `recepcion`, `odontologo`) tienen permiso para consultar la agenda diaria (`GET /api/agenda`).
- Por este motivo, un error HTTP `403 FORBIDDEN` no es alcanzable manualmente en la interfaz con un usuario autenticado legítimo. No obstante, el comportamiento ante `403` está completamente implementado y verificado mediante tests automáticos en `AgendaPage.test.tsx`, demostrando que ante un `403` se muestra la violación específica en el error local sin cerrar la sesión ni duplicar el banner global.

## Verificación manual en el navegador (16.6)

Con backend y frontend levantados con Docker Compose, se ejecutó [manual-C-27.py](manual-C-27.py), generando datos ficticios del seed para el lunes futuro `2026-11-16` y registrando las respuestas HTTP en [http-C-27.txt](http-C-27.txt) y el resumen en [manual-C-27.txt](manual-C-27.txt).

Capturas tomadas por la autora en `docs/evidencias/capturas/`:
- `C-27-agenda-dia.png`: vista general de la agenda del lunes 2026-11-16 con Quiroga y Sosa, horarios laborales y bloqueos.
- `C-27-filtro-profesional.png`: filtro aplicado a Dra. Laura Quiroga mostrando solo su columna y colecciones.
- `C-27-filtro-sillon.png`: filtro por Sillón 2 mostrando la ayuda informativa y preservando horarios y bloqueos.
- `C-27-solapamiento-cancelado.png`: carril compartido de 09:00 a 09:30 con turno activo y turno cancelado sin solaparse.
- `C-27-vacio.png`: domingo 2026-11-15 sin turnos con el mensaje "No hay turnos para este día" y grilla 08:00–20:00.
- `C-27-sesion-vencida.png`: redirección a `/login` con mensaje de sesión vencida tras token alterado y actualización manual.
- `C-27-tablet.png`: vista responsive en viewport tablet (768×1024) con scroll horizontal y encabezados sticky.

## Inmutabilidad fuera de frontend/

Se confirma expresamente que:
- No se modificó ningún archivo dentro de `backend/`.
- No se modificó `docker-compose.yml`.
- No se modificó `.env` ni se incluyeron secretos en ningún archivo.
- No se modificaron `openspec/specs/`, `knowledge-base/`, `CHANGES.md`, `README.md`, `AGENTS.md` ni `CLAUDE.md`.
- No se modificaron evidencias archivadas preexistentes de otros changes.

## Desvíos

- **Estilos en `tokens.css`**: Se agregaron tokens específicos de agenda (`--agenda-hour-height`, `--agenda-time-gutter-width`, `--agenda-column-min-width`, `--agenda-column-header-height`, `--agenda-grid-line`, `--agenda-working-bg`, `--agenda-offhours-bg`, `--agenda-block-bg`, `--agenda-block-border`, `--agenda-card-radius`, `--agenda-card-min-height`, `--agenda-cancelled-bg`) en `frontend/src/shared/styles/tokens.css`, tal como exigió la tarea 15.1 y D12/D13, asegurando cero valores HEX o tamaños fijos hardcodeados en los componentes TSX.
- **Normalización de hooks para ESLint v5**: En `AgendaPage.tsx` y `useAgenda.ts` se adecuaron las llamadas a estados para cumplir estrictamente con `react-hooks/set-state-in-effect` y `react-hooks/refs` de `eslint-plugin-react-hooks` v5, derivando `isPending` durante el renderizado y sincronizando refs en `useEffect`.
- **Revisión visual de la autora**: La revisión visual de la autora detectó tarjetas recortadas sin paciente visible y una tabla vacía duplicada; los tests pasaban porque el texto estaba en el DOM. Se corrigió y se agregaron tests.
## Hallazgo de la revisión visual 2

**Problema.** En las capturas se vieron dos casos:

- Cuando dos turnos se superponen y la columna se divide en carriles, la tarjeta compacta (menos de 45 min) mostraba la etiqueta completa ("Reservado", "Cancelado"). La etiqueta ocupaba casi todo el ancho del carril: el paciente quedaba como "09:00…", y en tablet (768 px) ni siquiera se veía la hora.
- En tablet, un turno de un solo carril también quedaba como "10:00 · Ana Pér…".

La regla que tiene que cumplirse es que la hora y el paciente tienen prioridad sobre el estado, y que el estado nunca tapa al paciente.

**Causa.** La fila compacta ponía `StatusBadge` en la misma línea que la hora y el paciente. La etiqueta mide 14 px, tiene 12 px de relleno por lado, `white-space: nowrap` y `flex: 0 0 auto`, así que no se achica. El único elemento que se encogía era el texto de hora y paciente. Con la mitad del ancho de la columna, la etiqueta se quedaba con casi todo el espacio.

Los tests no lo detectaron porque jsdom no calcula el layout ni mide anchos. El texto del paciente estaba en el DOM y `toHaveTextContent` pasaba aunque en pantalla se viera recortado. Solo la captura lo mostró.

### Iteración 1: punto de color (descartada)

En carriles divididos y en columnas de menos de 260 px, la etiqueta se reemplazaba por un punto de color con los mismos tokens. El nombre del estado quedaba como texto visualmente oculto y en el `title`.

Se descartó porque incumple el requisito "Color por estado más texto": el estado MUST leerse con texto visible y MUST NOT depender solo del color.

- El `title` no cuenta, porque en tablet no hay `hover`.
- El texto oculto solo sirve para lectores de pantalla.

La spec no se cambió.

### Iteración 2: tarjeta compacta en dos líneas (vigente)

1. **Carriles divididos** (`laneCount > 1`). La fila compacta suma la clase `.cardCompactStacked` y pasa a dos líneas:
   - línea 1: "HH:MM · Paciente", con ellipsis y todo el ancho de la tarjeta;
   - línea 2: `StatusBadge` con texto visible, en tamaño reducido (`--font-size-xs`, 12 px, con relleno de `1px var(--space-1)`).

   La etiqueta nunca comparte línea con el paciente. Los colores son los mismos tokens AA de `APPOINTMENT_STATUS_TOKENS`, y el `aria-label` completo de la tarjeta no cambia. La tarjeta dividida reduce además el relleno horizontal a `--space-1`.
2. **Columnas angostas sin superposición.** `.columnTrack` es un contenedor (`container: agenda-column / inline-size`). Con `@container agenda-column (width < 260px)`, la fila compacta toma el mismo formato en dos líneas con la etiqueta reducida.
3. **Umbral de 260 px.** Es el ancho mínimo en el que todo entra en una sola línea sin recortar a un paciente de largo típico:

   | Elemento | Ancho |
   |---|---|
   | Relleno y bordes de la tarjeta (2 × 8 + 2) | 18 px |
   | Etiqueta más ancha, "Confirmado", a 14 px con 12 px de relleno por lado | unos 96 px |
   | Separación | 4 px |
   | "10:00 · " a 12 px | unos 48 px |
   | **Total fijo** | **unos 166 px** |

   Quedan unos 94 px para el paciente, alrededor de 15 caracteres a 12 px. Por debajo de 260 px, un nombre típico ("Nombre Apellido") ya se recorta, y por eso la tarjeta pasa a dos líneas. En dos líneas, la línea 1 dispone de todo el ancho útil: 220 − 18 = 202 px con la columna en su mínimo (`--agenda-column-min-width`).

   En tablet (768 px, columnas en el mínimo de 220 px) se usan dos líneas. En escritorio, con tres columnas de unos 300 px, se mantiene una línea. Los anchos de texto son estimaciones con la fuente del sistema.
4. **La etiqueta reducida entra en un carril.** "Confirmado" a 12 px mide unos 62 px de texto, más 2 × 4 de relleno y 2 de borde: unos 72 px. En tablet, con dos carriles, cada uno mide 110 px, menos 4 + 4 de relleno y 2 de borde, o sea 100 px útiles. Entra.
5. **El formato en dos líneas entra en un turno de 30 min.** Con `--agenda-hour-height: 112px`, 30 min equivalen a 56 px:

   | Elemento | Alto |
   |---|---|
   | Relleno vertical de la tarjeta (`--space-1` × 2) | 8 px |
   | Borde (1 × 2) | 2 px |
   | Línea 1: 12 px × `--line-height-base` 1,5 | 18 px |
   | Separación entre líneas (`--space-1`) | 4 px |
   | Línea 2, etiqueta: 12 px × 1,2 + 1 × 2 de relleno + 1 × 2 de borde | 18,4 px |
   | **Total** | **50,4 px ≤ 56 px** (sobran 5,6 px) |

6. **Turnos de menos de 30 min: no se implementó el punto.** El catálogo de prestaciones ([backend/app/demo_data.py](../../backend/app/demo_data.py)) no tiene ninguna de menos de 30 min; la mínima es Control, con 30 min. Por eso no se implementó el punto con abreviatura.

   **Riesgo abierto:** RN-AG-09 permite que un turno indique su propia duración (`duration_min`, de 5 a 480 min), distinta de la de su prestación. Un turno así se dibuja con el alto mínimo de 15 min (28 px), y ahí solo entra la línea 1. En carriles divididos o en columnas angostas, la etiqueta quedaría recortada.

Falta confirmar los anchos y altos con una captura nueva de la autora, porque jsdom no los mide.

**Tests (TDD).** Los rojos de la iteración 2 están en [red-C-27/revision-visual-2.txt](red-C-27/revision-visual-2.txt), que reemplaza al rojo de la iteración 1: 3 fallos por `AssertionError`.

- `AgendaView.test.tsx > en un solapamiento de dos carriles la tarjeta muestra en dos líneas el paciente y el nombre del estado como texto visible`
- `AgendaView.test.tsx > un turno de un solo carril conserva el formato de una línea con la etiqueta de estado`
- `agendaStyles.test.ts > la columna es un contenedor y por debajo de 260 px la tarjeta compacta pasa a dos líneas con la etiqueta reducida`. Es una comprobación estática del CSS, porque jsdom no evalúa container queries.

Ninguno usa `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, fake timers ni MSW (regla C1). Cada uno tiene su mutación en [mutaciones-C-27.py](mutaciones-C-27.py):

- `laneCount > 1` → `> 2`;
- `laneCount > 1` → `> 0`;
- en la container query, `.cardCompactRow { flex-direction: column` → `row`.

## Artefactos

- [proposal.md](../../openspec/changes/ui-agenda-diaria/proposal.md)
- [design.md](../../openspec/changes/ui-agenda-diaria/design.md)
- [tasks.md](../../openspec/changes/ui-agenda-diaria/tasks.md)
- [spec.md (frontend-agenda)](../../openspec/changes/ui-agenda-diaria/specs/frontend-agenda/spec.md)

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `13:00Z se convierte a 10:00 y 2026-11-16 en Buenos Aires y formatea la etiqueta del día` | `frontend/src/features/agenda/agendaTime.ts` | `-  return '${start}–${end}'; +  return '${start}-${end}';` | `AssertionError: expected '10:00-10:30' to be '10:00–10:30' // Object.is equality` |
| 2 | `respeta el borde de medianoche entre 02:30Z y 03:30Z en Buenos Aires` | `frontend/src/features/agenda/agendaTime.ts` | `-  return formatLocalDate(now, timeZone); +  void timeZone; +  return formatLocalDate(now,` | `AssertionError: expected '2026-11-16' to be '2026-11-15' // Object.is equality` |
| 3 | `addDays suma y resta días calendario cruzando mes y año y weekdayOf devuelve ISO con domingo 7` | `frontend/src/features/agenda/agendaTime.ts` | `-  return day === 0 ? 7 : day; +  return day === 0 ? 0 : day;` | `AssertionError: expected +0 to be 7 // Object.is equality` |
| 4 | `parseHHMM convierte 24:00 a 1440 y appointmentRange maneja el cruce de medianoche` | `frontend/src/features/agenda/agendaTime.ts` | `-    return 1440; +    return 0;` | `AssertionError: expected +0 to be 1440 // Object.is equality` |
| 5 | `una zona con DST como America/New_York no altera la hora de Buenos Aires y el resultado no depende del proceso` | `frontend/src/features/agenda/agendaTime.ts` | `-  return parseLocalDate(value) !== null; +  return parseLocalDate(value) === null;` | `AssertionError: expected false to be true // Object.is equality` |
| 6 | `systemClock devuelve el instante actual y createFixedClock inyecta un reloj determinista con new Date() solo en clock.ts` | `frontend/src/features/agenda/clock.ts` | `-      return new Date(fixedTime); +      return new Date(fixedTime + 1000);` | `AssertionError: expected '2026-11-16T12:00:01.000Z' to be '2026-11-16T12:00:00.000Z' // Ob` |
| 7 | `DEFAULT_AGENDA_TIMEZONE vive en un único archivo de configuración y resolveAgendaTimezone prioriza el timezone de la respuesta` | `frontend/src/features/agenda/agendaConfig.ts` | `-export const DEFAULT_AGENDA_TIMEZONE = "America/Argentina/Buenos_Aires"; +export const DE` | `AssertionError: expected 'UTC' to be 'America/Argentina/Buenos_Aires' // Object.is equalit` |
| 8 | `prohíbe getters locales de Date y toLocale* sin timeZone y confina new Date() a clock.ts` | `frontend/src/features/agenda/agendaTime.ts` | `-function toDate(instant: Date \| string): Date { +function toDate(instant: Date \| string):` | `AssertionError: expected [ 'agendaTime.ts' ] to deeply equal []` |
| 9 | `calcula el eje 08:00 a 20:00 para el lunes 2026-11-16 con horarios 09:00–13:00 y 15:00–19:00, bloqueo y turnos` | `frontend/src/features/agenda/agendaLayout.ts` | `-  let startMinute = Math.max(0, Math.floor(minStart / 60) * 60 - 60); +  let startMinute ` | `AssertionError: expected 540 to be 480 // Object.is equality` |
| 10 | `usa 08:00–20:00 en día vacío, expande rangos menores a 4 horas y clampea bloqueos y turnos en medianoche a [0, 1440]` | `frontend/src/features/agenda/agendaLayout.ts` | `-export const AGENDA_DEFAULT_START_MINUTE = 480; +export const AGENDA_DEFAULT_START_MINUTE` | `AssertionError: expected 540 to be 480 // Object.is equality` |
| 11 | `ordena las columnas de forma alfabética estable con desempate por id, conserva columnas vacías y une defensivamente la agenda` | `frontend/src/features/agenda/agendaLayout.ts` | `-  return a.id.localeCompare(b.id); +  return b.id.localeCompare(a.id);` | `AssertionError: expected -1 to be greater than 0` |
| 12 | `marca profesionales inactivos con (inactivo) y el filtro professionalId deja una sola columna` | `frontend/src/features/agenda/agendaLayout.ts` | `-  return professional.active ? professional.fullName : '${professional.fullName} (inactiv` | `AssertionError: expected [ 'Dra. Laura Quiroga', …(1) ] to deeply equal [ 'Dra. Laura Quir` |
| 13 | `asigna carriles a turnos sin solape, a un cancelado y un activo superpuestos y a tres turnos en cadena` | `frontend/src/features/agenda/agendaLayout.ts` | `-    const laneCount = Math.max(1, laneEnds.length); +    const laneCount = Math.max(2, la` | `AssertionError: expected [ …(2) ] to deeply equal [ …(2) ]` |
| 14 | `aplica alto mínimo a un turno de 5 minutos, clampea el inicio al eje y soporta un turno que termina a las 00:00` | `frontend/src/features/agenda/agendaLayout.ts` | `-export const AGENDA_MIN_APPOINTMENT_MINUTES = 15; +export const AGENDA_MIN_APPOINTMENT_MI` | `AssertionError: expected 5 to be 15 // Object.is equality` |
| 15 | `fetchAgenda pide GET /api/agenda con from y to locales sin sufijo Z, filtros opcionales y signal, y parsea el 200 completo` | `frontend/src/features/agenda/agendaApi.ts` | `-  search.set("from", params.from); +  search.set("from", '${params.from}Z');` | `AssertionError: expected 'http://localhost:8000/api/agenda?from…' to be 'http://localhost:` |
| 16 | `fetchAgenda propaga errores 400, 401, 403, 500, red y rechaza una respuesta 200 con JSON o forma inválida` | `frontend/src/features/agenda/agendaApi.ts` | `-      error: { kind: "unknown", status: result.status, rawText: UNEXPECTED_RESPONSE_MESSA` | `AssertionError: expected { ok: false, status: 200, …(1) } to deeply equal { ok: false, sta` |
| 17 | `fetchProfessionals y fetchChairs cargan los catálogos con activos e inactivos y validan la respuesta` | `frontend/src/features/agenda/agendaApi.ts` | `-  const result = await client.request("/chairs", { +  const result = await client.request` | `AssertionError: expected [ …(2) ] to deeply equal [ …(2) ]` |
| 18 | `dispara las tres requests en paralelo, pasa por loading/refreshing/success y tolera fallo del catálogo con Promise.allSettled` | `frontend/src/features/agenda/useAgenda.ts` | `-  "No se pudo cargar el catálogo completo; las columnas se armaron con los datos de la ag` | `Error: expect(element).toHaveTextContent()` |
| 19 | `aborta e ignora respuestas viejas al cambiar de fecha y expone error cuando falla la agenda` | `frontend/src/features/agenda/useAgenda.ts` | `-      controller.abort(); +      void controller;` | `AssertionError: expected false to be true // Object.is equality` |
| 20 | `la ruta raíz redirige con replace a /agenda según el Clock y no renderiza HomePage` | `frontend/src/App.tsx` | `-  return <Navigate to={'/agenda?date=${today}'} replace />; +  return <Navigate to={'/age` | `AssertionError: expected 'PUSH' to be 'REPLACE' // Object.is equality` |
| 21 | `menú del administrador incluye Agenda habilitada y los otros 5 ítems deshabilitados con Próximamente` | `frontend/src/features/auth/menuFor.ts` | `-    const enabled = item.id === "agenda"; +    const enabled = false;` | `AssertionError: expected { id: 'agenda', label: 'Agenda', …(3) } to deeply equal { id: 'ag` |
| 22 | `menú de recepción habilita Agenda y no incluye Usuarios y roles` | `frontend/src/features/auth/menuFor.ts` | `-      badge: enabled ? null : ("Próximamente" as const), +      badge: "Próximamente" as ` | `AssertionError: expected 'Próximamente' to be null` |
| 23 | `menú del odontólogo habilita Agenda y no incluye Turnos ni Usuarios y roles` | `frontend/src/features/auth/menuFor.ts` | `-      disabled: !enabled, +      disabled: true,` | `AssertionError: expected true to be false // Object.is equality` |
| 24 | `renderiza Agenda como enlace habilitado en los tres roles y el resto deshabilitado con Próximamente` | `frontend/src/shared/components/AppShell.tsx` | `-                    to={item.path} +                    to="/otra-ruta"` | `Error: expect(element).toHaveAttribute("href", "/agenda") // element.getAttribute("href") ` |
| 25 | `dibuja el eje 08:00–20:00 y las tres columnas en orden alfabético estable con inactivo y columna vacía` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                  <div className={styles.emptyColumnNote}>Sin turnos</div> +             ` | `Error: expect(received).toBeInTheDocument()` |
| 26 | `posiciona el turno de Quiroga 10:00–10:30 a 120 minutos del inicio con 30 minutos de alto y muestra la fecha local` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                      data-offset-minutes={item.offsetMinutes} +                      dat` | `Error: expect(element).toHaveAttribute("data-offset-minutes", "120") // element.getAttribu` |
| 27 | `reparte un turno cancelado y uno activo superpuestos en dos carriles y da alto mínimo al turno de cinco minutos` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                      data-lane-count={item.laneCount} +                      data-lane-c` | `Error: expect(element).toHaveAttribute("data-lane-count", "2") // element.getAttribute("da` |
| 28 | `dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                      ? 'Bloqueo: ${block.reason}, de ${startLabel} a ${endLabel}' +     ` | `AssertionError: expected null not to be null` |
| 29 | `muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                  const cardAriaLabel = '${timeLabel}, ${appt.patientName}, ${appt.servic` | `AssertionError: expected '10:00–10:30, Ana Pérez' to contain 'Dra. Laura Quiroga'` |
| 30 | `en un día sin turnos muestra SOLO el EmptyState sin grilla en modo grilla ni tabla en modo lista` | `frontend/src/features/agenda/AgendaView.tsx` | `-          title="No hay turnos para este día" +          title="Agenda sin registros"` | `AssertionError: expected null not to be null` |
| 31 | `la tarjeta de 30 minutos muestra el nombre del paciente en su texto visible y el aria-label completo` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                  const isCompact = item.durationMinutes < 45; +                  const i` | `Error: expect(element).toHaveTextContent()` |
| 32 | `la tarjeta de 60 minutos muestra la prestación en su texto visible en una línea separada` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                          <div className={styles.cardMeta}>{appt.serviceName}</div> +    ` | `Error: expect(element).toHaveTextContent()` |
| 33 | `en un solapamiento de dos carriles la tarjeta muestra en dos líneas el paciente y el nombre del estado como texto visible` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                  const isSplitLane = item.laneCount > 1; +                  const isSpli` | `AssertionError: expected 'cardCompactRow' to contain 'cardCompactStacked'` |
| 34 | `un turno de un solo carril conserva el formato de una línea con la etiqueta de estado` | `frontend/src/features/agenda/AgendaGrid.tsx` | `-                  const isSplitLane = item.laneCount > 1; +                  const isSpli` | `AssertionError: expected 'cardCompactRow cardCompactStacked' not to contain 'cardCompactSt` |
| 35 | `anuncia la cantidad de turnos con aria-live y alterna a la vista en lista con Ver como lista` | `frontend/src/features/agenda/AgendaView.tsx` | `-            {'Turnos del ${dayLabel}: ${agenda.appointments.length}'} +            {'Turn` | `Error: expect(element).toHaveTextContent()` |
| 36 | `renderiza selectores de Profesional y Sillón con opción Todos, marca (inactivo), ayuda de sillón y Limpiar filtros` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-                  {chair.active ? chair.name : '${chair.name} (inactivo)'} +             ` | `AssertionError: expected [ 'Todos', 'Sillón 1', 'Sillón 2' ] to deeply equal [ 'Todos', 'S` |
| 37 | `carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible` | `frontend/src/features/agenda/AgendaToolbar.tsx` | `-  "El filtro por sillón solo afecta los turnos; los horarios y bloqueos se siguen mostran` | `Error: expect(received).toBeInTheDocument()` |
| 38 | `filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    setSearchParams(buildParams({ professionalId: null, chairId: null }), { replace: fals` | `AssertionError: expected '?date=2026-11-16&professionalId=00000…' to be '?date=2026-11-16'` |
| 39 | `navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL` | `frontend/src/features/agenda/AgendaPage.tsx` | `-        onPrevDay={() => navigateToDate(addDays(effectiveDate, -1))} +        onPrevDay={` | `AssertionError: expected '/agenda?date=2026-11-17' to be '/agenda?date=2026-11-15' // Obje` |
| 40 | `respeta el borde de medianoche en la fecha inicial y normaliza una fecha inválida con replace mostrando aviso` | `frontend/src/features/agenda/AgendaPage.tsx` | `-export const INVALID_DATE_NOTICE = "La fecha del enlace no era válida; se muestra hoy."; ` | `Error: expect(received).toBeInTheDocument()` |
| 41 | `muestra Cargando... con role=status en la carga inicial sin mostrar error` | `frontend/src/features/agenda/AgendaPage.tsx` | `-      {state.phase === "loading" && state.agenda === null && <LoadingState />} +      {st` | `Error: expect(received).toHaveTextContent()` |
| 42 | `muestra ErrorState con Reintentar ante error de red, al reintentar con 200 renderiza la agenda y Actualizar agenda refresca manualmente` | `frontend/src/features/agenda/AgendaPage.tsx` | `-        onRefresh={state.refresh} +        onRefresh={undefined}` | `AssertionError: expected null not to be null` |
| 43 | `delega el 401 de GET /api/agenda en C-26 descartando el token y redirigiendo a /login sin mostrar error local` | `frontend/src/features/agenda/agendaApi.ts` | `+    auth: "omit",` | `AssertionError: expected '/agenda' to be '/login' // Object.is equality` |
| 44 | `muestra la violación de un 403 en el error local sin cerrar sesión ni duplicar el banner global` | `frontend/src/features/agenda/AgendaPage.tsx` | `-    onForbidden: clearActionErrors, +    onForbidden: undefined,` | `AssertionError: expected [ …(2) ] to have a length of 1 but got 2` |
| 45 | `renderiza la tabla semántica con caption, encabezados con scope=col y filas en el mismo orden de la agenda` | `frontend/src/features/agenda/AgendaTable.tsx` | `-        <caption className={styles.caption}>{'Turnos del ${dayLabel}'}</caption> +       ` | `AssertionError: expected null not to be null` |
| 46 | `define los tokens de agenda en tokens.css, scroll horizontal, sticky, controles >= 44x44 px y cero HEX en TSX` | `frontend/src/features/agenda/AgendaGrid.module.css` | `-  overflow-x: auto; +  overflow-x: hidden;` | `AssertionError: expected '.gridScrollContainer {\n  overflow-x:…' to contain 'overflow-x: ` |
| 47 | `la columna es un contenedor y por debajo de 260 px la tarjeta compacta pasa a dos líneas con la etiqueta reducida` | `frontend/src/features/agenda/AgendaGrid.module.css` | `-    flex-direction: column; +    flex-direction: row;` | `AssertionError: expected '@container agenda-column (width < 260…' to match /\.cardCompactR` |
<!-- mutaciones:fin -->

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Requisito | Escenario | Test |
|---|---|---|---|
| 1 | Ruta /agenda y pantalla principal | / redirige a /agenda | `src/App.test.tsx > la ruta raíz redirige con replace a /agenda según el Clock y no renderiza HomePage` |
| 2 | Ruta /agenda y pantalla principal | Agenda habilitada en el menú de los tres roles | `src/features/auth/menuFor.test.ts > menú del administrador incluye Agenda habilitada y los otros 5 ítems deshabilitados con Próximamente ; src/shared/components/AppShell.test.tsx > renderiza Agenda como enlace habilitado en los tres roles y el resto deshabilitado con Próximamente` |
| 3 | Carga con fetch y Clock inyectados | Carga con fetch y Clock inyectados | `src/features/agenda/AgendaPage.test.tsx > carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible` |
| 4 | Carga con fetch y Clock inyectados | La fecha inicial respeta el borde de medianoche | `src/features/agenda/AgendaPage.test.tsx > respeta el borde de medianoche en la fecha inicial y normaliza una fecha inválida con replace mostrando aviso` |
| 5 | Conversión a hora local con el timezone de la respuesta | 13:00Z se muestra como 10:00 en Buenos Aires | `src/features/agenda/agendaTime.test.ts > 13:00Z se convierte a 10:00 y 2026-11-16 en Buenos Aires y formatea la etiqueta del día` |
| 6 | Conversión a hora local con el timezone de la respuesta | El resultado es independiente de la zona del proceso | `src/features/agenda/agendaTime.test.ts > una zona con DST como America/New_York no altera la hora de Buenos Aires y el resultado no depende del proceso` |
| 7 | Conversión a hora local con el timezone de la respuesta | Las fechas de la request son locales | `src/features/agenda/agendaApi.test.ts > fetchAgenda pide GET /api/agenda con from y to locales sin sufijo Z, filtros opcionales y signal, y parsea el 200 completo` |
| 8 | Eje de horas | Eje del lunes con datos | `src/features/agenda/agendaLayout.test.ts > calcula el eje 08:00 a 20:00 para el lunes 2026-11-16 con horarios 09:00–13:00 y 15:00–19:00, bloqueo y turnos` |
| 9 | Eje de horas | Eje de un día vacío | `src/features/agenda/agendaLayout.test.ts > usa 08:00–20:00 en día vacío, expande rangos menores a 4 horas y clampea bloqueos y turnos en medianoche a [0, 1440]` |
| 10 | Columnas por profesional | Tres columnas en orden estable | `src/features/agenda/AgendaView.test.tsx > dibuja el eje 08:00–20:00 y las tres columnas en orden alfabético estable con inactivo y columna vacía` |
| 11 | Columnas por profesional | Profesional inactivo visible | `src/features/agenda/agendaLayout.test.ts > marca profesionales inactivos con (inactivo) y el filtro professionalId deja una sola columna` |
| 12 | Columnas por profesional | Filtro por profesional deja una sola columna | `src/features/agenda/AgendaPage.test.tsx > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha` |
| 13 | Posición, alto y carriles de turnos superpuestos | Posición y alto del turno de Quiroga | `src/features/agenda/AgendaView.test.tsx > posiciona el turno de Quiroga 10:00–10:30 a 120 minutos del inicio con 30 minutos de alto y muestra la fecha local` |
| 14 | Posición, alto y carriles de turnos superpuestos | Carriles para un cancelado y un activo superpuestos | `src/features/agenda/AgendaView.test.tsx > reparte un turno cancelado y uno activo superpuestos en dos carriles y da alto mínimo al turno de cinco minutos` |
| 15 | Posición, alto y carriles de turnos superpuestos | Turno de cinco minutos con alto mínimo | `src/features/agenda/agendaLayout.test.ts > aplica alto mínimo a un turno de 5 minutos, clampea el inicio al eje y soporta un turno que termina a las 00:00` |
| 16 | Horarios de atención, bloqueos y cancelados | Horarios y bloqueo del lunes | `src/features/agenda/AgendaView.test.tsx > dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado` |
| 17 | Horarios de atención, bloqueos y cancelados | El cancelado permanece visible | `src/features/agenda/AgendaView.test.tsx > dibuja las bandas de horario de Quiroga, el bloqueo Congreso de 12:00 a 13:00 y conserva visible y atenuado el turno cancelado` |
| 18 | Color por estado más texto | Reservado y cancelado se distinguen por texto | `src/features/agenda/AgendaView.test.tsx > muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta` |
| 19 | Color por estado más texto | Nombre accesible completo | `src/features/agenda/AgendaView.test.tsx > muestra Reservado y Cancelado con StatusBadge AA y expone el nombre accesible completo en cada tarjeta` |
| 20 | Filtros por profesional y sillón con estado en la URL | El filtro por sillón conserva horarios y bloqueos | `src/features/agenda/AgendaPage.test.tsx > carga con fetch y Clock inyectados y al filtrar por Sillón 2 conserva horarios y bloqueos con ayuda visible` |
| 21 | Filtros por profesional y sillón con estado en la URL | El filtro por profesional filtra las tres colecciones | `src/features/agenda/AgendaPage.test.tsx > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha` |
| 22 | Filtros por profesional y sillón con estado en la URL | Filtros combinados sin turnos | `src/features/agenda/AgendaPage.test.tsx > filtra las tres colecciones por profesional, muestra Sin turnos para este filtro al combinar y Limpiar filtros conserva la fecha` |
| 23 | Navegación anterior, siguiente, Hoy y selector | Anterior y siguiente | `src/features/agenda/AgendaPage.test.tsx > navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL` |
| 24 | Navegación anterior, siguiente, Hoy y selector | Hoy y selector de fecha | `src/features/agenda/AgendaPage.test.tsx > navega con Anterior, Siguiente, Hoy y el selector de fecha usando push en la URL` |
| 25 | Estados de carga, vacío y error | Carga inicial | `src/features/agenda/AgendaPage.test.tsx > muestra Cargando... con role=status en la carga inicial sin mostrar error` |
| 26 | Estados de carga, vacío y error | Día sin turnos | `src/features/agenda/AgendaView.test.tsx > en un día sin turnos muestra SOLO el EmptyState sin grilla en modo grilla ni tabla en modo lista` |
| 27 | Estados de carga, vacío y error | Error de red con reintento | `src/features/agenda/AgendaPage.test.tsx > muestra ErrorState con Reintentar ante error de red, al reintentar con 200 renderiza la agenda y Actualizar agenda refresca manualmente` |
| 28 | 401 delegado en C-26 y 403 visible | 401 durante el uso | `src/features/agenda/AgendaPage.test.tsx > delega el 401 de GET /api/agenda en C-26 descartando el token y redirigiendo a /login sin mostrar error local` |
| 29 | 401 delegado en C-26 y 403 visible | 403 con la violación visible | `src/features/agenda/AgendaPage.test.tsx > muestra la violación de un 403 en el error local sin cerrar sesión ni duplicar el banner global` |
| 30 | Vista en lista accesible | Tabla accesible del lunes | `src/features/agenda/AgendaTable.test.tsx > renderiza la tabla semántica con caption, encabezados con scope=col y filas en el mismo orden de la agenda` |
| 31 | Vista en lista accesible | Anuncio de la cantidad de turnos | `src/features/agenda/AgendaView.test.tsx > anuncia la cantidad de turnos con aria-live y alterna a la vista en lista con Ver como lista` |
| 32 | Responsive para escritorio y tablet | Tablet de 768 por 1024 | `src/features/agenda/agendaStyles.test.ts > define los tokens de agenda en tokens.css, scroll horizontal, sticky, controles >= 44x44 px y cero HEX en TSX` |
<!-- trazabilidad:fin -->
