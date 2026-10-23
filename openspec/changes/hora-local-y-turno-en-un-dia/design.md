# Design

## Context

C-03 dejó `validate_new_appointment(request, references, existing_appointments) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`, con dos grupos: `_request_validity_violations` (grupo 1: referencias y después duración, todas juntas) y `_agenda_conflict_violations` (grupo 2: solapamientos por profesional y por sillón). Si el grupo 1 tiene alguna violación, se devuelve `Rejected` sin evaluar el grupo 2. El fin del turno se calcula recién al armar el candidato, después del grupo 1.

`intervals.py` tiene solo el `Interval` semiabierto y `overlaps`, sin nada de hora local. `model.py` normaliza todo instante a UTC y rechaza los *naive* con `ValueError`. La granularidad de 5 minutos vive como `DURATION_STEP_MIN` en `rules/duration.py` y solo la usa la duración (ningún test la importa). `ViolationCode` tiene `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, `UNKNOWN_REFERENCE` e `INACTIVE_REFERENCE`. La allowlist del dominio (`tests/domain/import_guard.py`) ya incluye `zoneinfo` y `tzdata`, y `tzdata` está en `pyproject.toml`.

Los tests de dominio usan instantes del 2026-10-20 entre las 08:00 y las 16:00 UTC (05:00 a 13:00 hora local), todos con minutos múltiplos de 5: las reglas nuevas no cambian el resultado de ninguno. Solo cambia la forma de llamar a la función (28 llamadas en `test_validate_new_appointment.py`).

La motivación está en `proposal.md` y los requisitos en `specs/appointment-scheduling/spec.md`. Las decisiones D1 a D7 salen del explore del 2026-10-23 (`docs/evidencias/explore-C-04.md`) y la autora las confirmó. D6 fija en el propose el nombre y el módulo de la constante, que el explore dejó abiertos. D8 a D12 surgieron en el propose, no en el explore, y quedan para que la autora las confirme en la revisión del propose.

## Goals / Non-Goals

**Goals:**
- Que la grilla del inicio y la medianoche se decidan en hora local, con la zona recibida por parámetro, sin `datetime.now()` ni zona fija en el dominio.
- Una conversión a hora local que C-05 pueda reusar tal cual para comparar el turno con los tramos en minutos locales (fin = 1440 a la medianoche).
- Que la firma cambie una sola vez: C-05 a C-07 suman campos al contexto, no parámetros.
- Que los tests de C-02 y C-03 sigan verificando lo mismo: solo cambia la llamada.

**Non-Goals:**
- Horario laboral, bloqueos y `now` en el contexto (C-05 a C-07).
- Validar el texto de `APP_TIMEZONE` ni armar el contexto en la API (C-22 / C-23).
- Mensajes con nombres (C-08).
- Soportar zonas con horario de verano más allá de lo que da `zoneinfo`: Argentina no lo usa (SU-01). Igual, la regla de medianoche se calcula sobre la hora local del fin y no sobre la duración, así que no depende de eso (D9).

## Decisions

### D1 — `CROSSES_MIDNIGHT`, un código propio para el turno que cruza la medianoche local

Se agrega `CROSSES_MIDNIGHT = "CROSSES_MIDNIGHT"` a `ViolationCode` (valor igual al nombre, como el resto).

**Por qué**: no es un problema de un solo campo, sino del intervalo que forman el inicio y la duración.

**Alternativa descartada**: reusar `OUTSIDE_WORKING_HOURS`. Mezclaría dos reglas y depende de C-05, que todavía no existe.

### D2 — `INVALID_START_TIME`, con una sola violación aunque fallen minutos y segundos

Se agrega `INVALID_START_TIME = "INVALID_START_TIME"`. Si el inicio local tiene minutos que no son múltiplo de 5 **y** segundos o microsegundos distintos de cero (por ejemplo 10:03:30), se informa una sola violación cuyo mensaje nombra las dos razones (D11).

**Por qué**: es el paralelo de `INVALID_DURATION` (decisión 5 de C-03): el código describe el campo inválido, no cada subregla.

**Alternativa descartada**: una violación por condición. El formulario mostraría dos errores sobre el mismo campo.

### D3 — `ScheduleContext` con solo `tz: ZoneInfo`

```python
@dataclass(frozen=True, slots=True)
class ScheduleContext:
    tz: ZoneInfo
```

Es un parámetro nuevo de `validate_new_appointment` (la posición, en D8). C-05 suma los horarios, C-06 los bloqueos y C-07 el `now`. El texto de `APP_TIMEZONE` (KB 08) se convierte en `ZoneInfo` en el borde (C-22 / C-23): el dominio no lee variables de entorno ni fija la zona.

**Por qué**: la firma cambia una sola vez y no en cada change. El campo es `ZoneInfo` y no `str` para que un nombre de zona inválido falle en el borde (al construir `ZoneInfo`) y no dentro de una regla.

**Alternativas descartadas**:
- *Un parámetro `tz: ZoneInfo` suelto*: C-05 a C-07 tendrían que volver a cambiar la firma, cada uno con su parámetro.
- *Una constante con la zona en el dominio*: contradice SU-01 ("el dominio recibe la zona por parámetro") y la regla dura de no fijar configuración en el código.

### D4 — Las dos reglas en el grupo 1, en el orden referencias → duración → inicio → medianoche

`_request_validity_violations` pasa a recibir el contexto y sigue estos pasos:

1. `violations = check_references(request, references)`.
2. Duración efectiva (como en C-03). Si existe: `duration_violations = check_duration(duration)` y `violations += duration_violations`.
3. `violations += check_start_time(request.start_at, context.tz)`. El inicio siempre existe, así que siempre se evalúa.
4. Solo si hay duración efectiva **y** `duration_violations` está vacía: `violations += check_same_local_day(request.start_at, request.start_at + timedelta(minutes=duration), context.tz)`.

La medianoche se evalúa aunque el inicio esté fuera de la grilla: el caso borde 23:33 con 60 minutos da `INVALID_START_TIME` y `CROSSES_MIDNIGHT`, en ese orden.

**Por qué**: ninguna de las dos reglas depende de la agenda, así que son de validez del pedido (`422`), no conflictos (`409`). Con una duración inválida, decir "cruza la medianoche" es ruido sobre un valor que ya está mal. El inicio fuera de la grilla, en cambio, no impide calcular un fin con sentido.

**Alternativa descartada**: ponerlas en el grupo 2. Un pedido podría salir con una violación de medianoche junto con solapamientos, y la API no sabría si responder `409` o `422`.

### D5 — Un turno que termina justo a las 00:00 locales es válido

El intervalo `[23:30, 00:00)` es semiabierto (DD-07) y no ocupa nada del día siguiente. En minutos locales medidos desde las 00:00 del día del inicio, el fin vale 1440 (D9). Tiene su propio escenario en la spec.

**Por qué**: es la misma convención que los turnos consecutivos, y 1440 encaja con los tramos `[inicio, fin)` en minutos locales de C-05 (un tramo que termina a la medianoche).

### D6 — Una sola granularidad: `GRID_STEP_MIN` en `rules/grid.py` (nombre y módulo decididos en el propose)

```python
# app/domain/rules/grid.py
GRID_STEP_MIN: Final = 5
```

`rules/duration.py` deja de definir `DURATION_STEP_MIN` y usa `GRID_STEP_MIN`; `rules/start_time.py` también. `MAX_DURATION_MIN` queda en `rules/duration.py`, porque es solo de la duración.

**Por qué**: SU-02 habla de una "constante configurable", en singular: si la granularidad cambia, cambia en un solo lugar para las dos reglas (decisión 6 del explore). El explore no fijó el nombre ni el módulo. Un módulo propio evita que `start_time.py` importe una constante de `duration.py` (o al revés), como si una regla dependiera de la otra. El nombre `GRID_STEP_MIN` dice que es el paso de la grilla de la agenda y no algo de la duración.

**Alternativas descartadas**:
- *Dejar `DURATION_STEP_MIN` en `duration.py` e importarla desde `start_time.py`*: el nombre engaña para el inicio y crea un acoplamiento entre reglas.
- *Ponerla en `intervals.py`*: `intervals.py` es infraestructura de tiempo (intervalos y conversión) y no tiene reglas de negocio; la granularidad es una suposición de negocio (SU-02).
- *Dos constantes con el mismo valor*: justo lo que SU-02 evita.

### D7 — Los tests usan solo `America/Argentina/Buenos_Aires`

Todas las zonas vigentes tienen offsets múltiplos de 15 minutos (incluso +05:30 o +05:45), así que para la grilla de 5 minutos UTC y hora local dan lo mismo, y un test con otra zona no demuestra nada. La hora local sí importa para la medianoche, y eso lo cubren los dos escenarios de "Hora local en la zona horaria recibida": un instante UTC que en hora local cae en otro día (rechazado) y un turno que cruza la medianoche UTC pero no la local (válido).

**Por qué**: un test que pasa igual con la implementación equivocada (evaluar en UTC) no aporta. Los dos escenarios de medianoche sí fallan si la regla se evalúa en UTC.

### D8 — `ScheduleContext` vive en `model.py` y va como último parámetro (surgió en el propose)

```python
def validate_new_appointment(
    request: NewAppointmentRequest,
    references: AppointmentReferences,
    existing_appointments: Sequence[Appointment],
    context: ScheduleContext,
) -> ValidationResult
```

- `ScheduleContext` va en `model.py`, junto a `AppointmentReferences`: es otro valor de entrada del dominio. `model.py` suma `from zoneinfo import ZoneInfo` (permitido por la allowlist).
- El contexto va al final, sin valor por defecto: el llamador no puede olvidarse la zona sin que mypy lo marque.

**Por qué**: el explore definió qué recibe el dominio, pero no dónde vive el tipo ni la posición del parámetro. Al final, cada llamada existente solo suma un argumento (`..., existing, CTX)`), así el diff de la adaptación de los tests es mínimo y fácil de revisar. Sin valor por defecto, no hay una zona escondida en el dominio (D3).

**Alternativas descartadas**:
- *Un módulo nuevo `schedule.py`*: un archivo más para un tipo de un campo; si C-05 a C-07 lo hacen crecer mucho, se puede mover.
- *`context` entre `references` y `existing_appointments`*: más prolijo de leer, pero cambia la posición de un argumento en las 28 llamadas.
- *`context: ScheduleContext | None = None` con Buenos Aires por defecto*: fija la zona en el dominio.

### D9 — Hora local en `intervals.py` (surgió en el propose)

```python
MINUTES_PER_DAY: Final = 1440

def local_day_and_minutes(instant: datetime, tz: ZoneInfo) -> tuple[date, int]
def format_local_time(instant: datetime, tz: ZoneInfo) -> str
```

- `local_day_and_minutes` convierte el instante a la zona (`instant.astimezone(tz)`) y devuelve el día local y los minutos desde las 00:00 de ese día (`hour * 60 + minute`; los segundos se descartan, porque la grilla del inicio los controla aparte). Un instante *naive* lanza `ValueError`, como en `model.py`: es un error de programación, no una regla de negocio.
- `format_local_time` devuelve la hora local con formato `HH:MM` (por ejemplo `"00:30"`), o `HH:MM:SS` si tiene segundos o microsegundos distintos de cero (por ejemplo `"10:05:30"`; los microsegundos no se muestran). Ver D11.
- **Medianoche** (`rules/same_day.py`): con `(start_day, start_min)` y `(end_day, end_min)`, el fin medido desde las 00:00 del día del inicio es `(end_day - start_day).days * MINUTES_PER_DAY + end_min`. El turno cruza la medianoche si ese valor es mayor que `MINUTES_PER_DAY`. 23:30–00:00 da exactamente 1440 y es válido (D5).
- **Grilla** (`rules/start_time.py`): se evalúa sobre `instant.astimezone(tz)`: `minute % GRID_STEP_MIN != 0` es una razón; `second != 0 or microsecond != 0` es otra.

**Por qué**: el explore pidió la conversión a día local y minutos y el formateo, pero no la forma de la API. Devolver `(día, minutos)` es justo lo que necesita C-05 para buscar el tramo del día de la semana y compararlo en minutos locales. Calcular la medianoche con la hora local del fin, y no con `start_min + duración`, no supone que la hora local avanza igual que la UTC (no depende de horarios de verano).

**Alternativas descartadas**:
- *Un dataclass `LocalTime(day, minutes)`*: más ceremonia sin un uso que lo necesite todavía; C-05 lo puede introducir si le sirve.
- *Comparar solo `end_day != start_day`*: rechazaría el turno que termina justo a las 00:00 (D5) si no se agrega el caso especial; la cuenta en minutos lo resuelve sin excepción.

### D10 — Una regla por módulo: `rules/start_time.py` y `rules/same_day.py` (surgió en el propose)

```python
def check_start_time(start_at: datetime, tz: ZoneInfo) -> list[Violation]
def check_same_local_day(start_at: datetime, end_at: datetime, tz: ZoneInfo) -> list[Violation]
```

Reciben instantes y la zona, no el pedido ni el contexto completo, y devuelven una lista vacía o una sola violación.

**Por qué**: sigue el patrón de `rules/duration.py` y `rules/overlap.py` (una regla por módulo, función pura). `same_day.py` es el nombre que ya usa `CHANGES.md` §[C-04]. Recibir solo lo que usan hace que no cambien cuando el contexto crezca.

**Alternativa descartada**: un solo `rules/local_time.py` con las dos reglas. Junta dos reglas con códigos distintos en un módulo, a diferencia del resto de `rules/`.

### D11 — Mensajes de los códigos nuevos (surgió en el propose; se confirma en el punto de control)

- Las horas se formatean con `format_local_time` (D9): `HH:MM` si la hora no tiene segundos ni microsegundos, y `HH:MM:SS` si tiene alguno distinto de cero. Los microsegundos no se muestran.
- `INVALID_START_TIME`: `"El inicio del turno no es válido (se recibió {hora} hora local): {razones unidas con ' y '}."`. Razones: `"los minutos deben ser múltiplo de 5"` (con `GRID_STEP_MIN`) y `"los segundos y microsegundos deben ser cero"`. Ejemplos: para 10:03, `"... (se recibió 10:03 hora local): los minutos deben ser múltiplo de 5."`; para 10:03:30, `"El inicio del turno no es válido (se recibió 10:03:30 hora local): los minutos deben ser múltiplo de 5 y los segundos y microsegundos deben ser cero."`; para 10:05:00.25, `"... (se recibió 10:05:00 hora local): los segundos y microsegundos deben ser cero."`.
- `CROSSES_MIDNIGHT`: `"El turno no puede cruzar la medianoche: empieza a las {hora} y termina a las {hora} del día siguiente (hora local)."`. Ejemplo: `"... empieza a las 23:30 y termina a las 00:30 del día siguiente (hora local)."`.

Las dos violaciones dejan `conflicting_appointment_id=None` y `reference_kind=None`.

**Por qué**: el mismo formato que `INVALID_DURATION` (valor recibido y razones), en hora local, que es lo que ve la secretaria. **Ajuste de la autora (2026-10-23, OK del propose):** si el inicio tiene segundos, el mensaje los muestra (`10:05:30`), para que la hora recibida se vea tal como llegó; sin segundos sigue en `HH:MM`. C-08 reemplaza los textos por los completos con nombres.

**Decisión nueva (surgió al aplicar el ajuste)**: un inicio con microsegundos y segundos en cero (10:05:00.25) se muestra como `10:05:00`, sin microsegundos. Mostrar `10:05` haría que el mensaje pareciera un inicio válido; mostrar los microsegundos agrega un tercer formato para un caso que solo produce un llamador mal escrito. El `:00` y la razón alcanzan para explicar el rechazo.

**Alternativa descartada**: mostrar siempre `HH:MM`, como proponía la primera versión de este design: un inicio de 10:05:30 se veía como 10:05 y solo la razón explicaba el rechazo.

### D12 — Tests (surgió en el propose)

- Estilo de C-02 y C-03: datos literales, UUIDs fijos, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, tablas con `@pytest.mark.parametrize` y aserciones sobre la lista completa de códigos.
- En `test_validate_new_appointment.py`: `BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")`, `CTX = ScheduleContext(tz=BUENOS_AIRES)` y un helper `_local(day, hour, minute, second=0, microsecond=0)` que arma un `datetime` con `tzinfo=BUENOS_AIRES`. Los escenarios nuevos se escriben en hora local con `_local` y, donde la spec da también el instante UTC, se compara contra un literal UTC (sin recalcular la conversión, para que no sea tautológico). `_at` sigue siendo UTC.
- En `test_intervals.py`: `local_day_and_minutes` (02:30 UTC del 20/10 → `(2026-10-19, 1410)`; 03:00 UTC del 21/10 → `(2026-10-21, 0)`; instante *naive* → `ValueError`) y `format_local_time` (`"23:30"`, `"00:30"`, ceros a la izquierda, `"10:05:30"` con segundos y `"10:05:00"` con solo microsegundos).
- Adaptación de los tests de C-02 y C-03: cada llamada suma `CTX` al final; ninguna aserción cambia. Se hace en un paso propio, con la suite en verde antes y después.

**Por qué**: comparar con literales UTC de la spec prueba la conversión sin repetir la cuenta del código. Un `ZoneInfo` real (y no `timezone(timedelta(hours=-3))`, como usa `test_model.py`) es lo que va a recibir el dominio en producción.

## Decisiones confirmadas por la autora

**Fecha: 2026-10-23.** D1 a D7 en el explore, tal como están en `docs/evidencias/explore-C-04.md`. Con el OK del propose (2026-10-23): el nombre y el módulo de la constante (D6) y D8 a D12, con un ajuste en D11 (la hora del inicio muestra los segundos si los tiene). También con ese OK, RN-AG-12 de `knowledge-base/05_reglas_de_negocio.md` se actualizó en este propose con el orden referencias → duración → inicio → medianoche. Pendiente de confirmar: el caso de solo microsegundos de D11 (`10:05:00`), que surgió al aplicar el ajuste. El texto de los mensajes se vuelve a mostrar en la tarea ⛔ antes de implementar las reglas.

## Risks / Trade-offs

- [Cambiar la firma de `validate_new_appointment` rompe a los llamadores] → Hoy solo la llaman los tests de dominio y el ejemplo de `backend/README.md`; todavía no hay API (C-22). La adaptación es sumar un argumento al final (D8).
- [`ZoneInfo` sin `tzdata` en Windows falla al construirse] → `tzdata` ya es dependencia y el explore verificó que el `.venv` resuelve la zona. Un fallo aparecería al construir `CTX` en los tests, no en el dominio.
- [Los escenarios mezclan horas UTC (los de C-02 y C-03) con horas locales (los nuevos)] → La spec delta abre con una convención y cada escenario nuevo da las dos horas. El Purpose de la spec principal se actualiza en el archive.
- [RN-AG-12 en KB 05 no mencionaba el inicio ni la medianoche en su orden de prioridad] → Se actualizó en este propose, con el OK de la autora, para que la KB no quede desincronizada.
- [Un inicio con solo microsegundos se muestra como `10:05:00`, sin los microsegundos] → La razón del mensaje explica el rechazo (D11); C-08 puede cambiar el formato.
- [`ScheduleContext` con un solo campo parece ceremonia] → Es deliberado (D3): C-05 a C-07 lo llenan sin volver a tocar la firma.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain`, de los tests de dominio y de la documentación (un solo commit del change, a pedido de la autora).

## Open Questions

Ninguna que cambie el alcance. Falta confirmar el caso de solo microsegundos de D11; el texto de los mensajes se vuelve a mostrar en la tarea ⛔ antes de implementar las reglas.
