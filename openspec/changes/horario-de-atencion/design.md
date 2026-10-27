# Design

## Context

C-04 dejó `validate_new_appointment(request, references, existing_appointments, context) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`, con dos grupos. `_request_validity_violations` (grupo 1: referencias → duración → inicio en la grilla → medianoche) corta si encuentra algo. `_agenda_conflict_violations(candidate, existing_appointments)` (grupo 2) hoy solo suma `check_professional_overlap` y `check_chair_overlap`. El fin del turno se calcula una sola vez en `validate_new_appointment` y el candidato (`Appointment`) existe recién en el grupo 2.

`ScheduleContext` (en `model.py`) tiene solo `tz: ZoneInfo`, *frozen* con slots, y su docstring ya anuncia que C-05 a C-07 le suman campos. `intervals.py` tiene `local_day_and_minutes(instant, tz) -> (date, int)` y `format_local_time(instant, tz) -> str`; `MINUTES_PER_DAY` se eliminó en C-04 (se agrega acá solo si hace falta, con su test). `ViolationCode` tiene siete códigos; no hay nada de `WorkingHours` ni `OUTSIDE_WORKING_HOURS` en el código (sí en el catálogo de KB 07, que ya suma `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS`). La allowlist del dominio (`tests/domain/import_guard.py`) alcanza: `dataclasses`, `datetime`, `collections`, `uuid`, `zoneinfo`.

`test_validate_new_appointment.py` construye `CTX = ScheduleContext(tz=BUENOS_AIRES)` en una sola línea (línea 36) y lo usa en todas las llamadas, con pedidos de P1 y de P2 en fechas del 2026-10-19 al 2026-10-21 en hora local. La suite de C-04 cerró con 181 tests y `mypy` sin errores en 24 archivos. El proyecto no usa `ruff` ni `black` (no están en `pyproject.toml`).

La motivación está en `proposal.md` y los requisitos en `specs/appointment-scheduling/spec.md`. D1 a D6 salen del explore del 2026-10-26 (`docs/evidencias/explore-C-05.md`) y la autora las confirmó. D7 a D13 surgieron en el propose y la autora las confirmó el 2026-10-26, en la revisión del propose.

## Goals / Non-Goals

**Goals:**
- Rechazar el turno fuera del horario de atención en hora local, con los tramos recibidos en el contexto y sin que el resultado dependa del filtrado del llamador.
- Que la validez de un conjunto de tramos sea una función pura del dominio que C-16 y C-21 puedan usar antes de guardar.
- Que los tests de C-02 a C-04 sigan verificando lo mismo: solo cambia la construcción de `CTX`.

**Non-Goals:**
- Revalidar los tramos dentro de `validate_new_appointment` (D10).
- Persistencia, constraint en PostgreSQL y `PUT` del horario (C-16, C-21), incluido US-010 CA-3 (turnos que quedan fuera al cambiar el horario).
- Feriados o excepciones por fecha, y zonas con horario de verano más allá de lo que da `zoneinfo` (Argentina no lo usa, SU-01).
- Mensajes con el nombre del profesional (C-08).

## Decisions

### D1 — Los tramos llegan en `ScheduleContext.working_hours`, sin valor por defecto (explore, decisión 1)

```python
@dataclass(frozen=True, slots=True)
class ScheduleContext:
    tz: ZoneInfo
    working_hours: tuple[WorkingHours, ...]
```

El dominio elige los tramos del profesional del pedido (`professional_id`) y del día de la semana local del inicio (`date.isoweekday()`, 1 = lunes … 7 = domingo, la convención de KB 04).

**Por qué**: la firma de `validate_new_appointment` no cambia (decisión 3 de C-04). Sin valor por defecto, mypy marca a cualquier llamador que se olvide los tramos; un default vacío rechazaría todo en silencio y uno "todo el día" escondería un horario en el dominio. Filtrar adentro es el mismo criterio que "El dominio filtra los turnos que recibe". `tuple` y no `list` porque el contexto es *frozen* y hashable.

**Alternativas descartadas**: un parámetro `working_hours` suelto (vuelve a cambiar la firma); un `dict[UUID, ...]` por profesional (obliga al llamador a armar la estructura y no evita filtrar por día).

### D2 — La regla va primera en el grupo 2, junto con los solapamientos (explore, decisión 2)

`_agenda_conflict_violations` pasa a recibir el contexto:

```python
def _agenda_conflict_violations(
    candidate: Appointment, existing_appointments: Sequence[Appointment], context: ScheduleContext
) -> list[Violation]:
    return (
        check_working_hours(candidate.professional_id, candidate.start_at, candidate.end_at,
                            context.working_hours, context.tz)
        + check_professional_overlap(candidate, existing_appointments)
        + check_chair_overlap(candidate, existing_appointments)
    )
```

El orden queda horario → (bloqueo, C-06) → profesional → sillón. El grupo 1 sigue cortando antes.

**Por qué**: en el grupo 2 la duración es válida, el inicio está en la grilla y el turno cabe en un día local, así que la regla no necesita guardas (D4). Es una pregunta sobre la agenda del profesional, como el solapamiento, y respeta el orden de RN-AG-12 (horario laboral antes que los solapamientos). La API va a responder `409` para el grupo 2. "Todas las violaciones, en orden estable" se actualiza: el grupo 2 es "conflictos de agenda", no solo solapamientos.

**Alternativa descartada**: en el grupo 1. Un turno fuera de horario no es un pedido malformado; además, en el grupo 1 habría que repetir las guardas de duración y medianoche.

### D3 — Los tramos contiguos se unen antes de evaluar (explore, decisión 3)

Para el profesional y el día, se ordenan los tramos por `start_minute` y se unen los que se tocan: si el siguiente empieza en el fin del anterior **o antes**, se extiende el fin al máximo de los dos. El turno es válido si algún tramo unido cumple `inicio_tramo <= inicio_turno` y `fin_turno <= fin_tramo`.

**Por qué**: RN-AG-04 (ya actualizada en KB 05) cuenta los tramos contiguos como uno; rechazar 12:30–13:30 con 9–13 y 13–17 sería sorprendente, porque no hay ningún minuto sin atención. Unir también los que se solapan (`<=` y no solo `==`) es defensivo: `validate_new_appointment` no revalida los tramos (D10), y con un conjunto solapado el resultado sigue siendo el razonable (el profesional atiende en la unión). La unión ordenada también da los tramos del mensaje (D6).

**Alternativa descartada**: exigir que el turno caiga en un solo tramo recibido. Es lo que decía RN-AG-04 antes del explore; la autora lo descartó.

### D4 — Minutos locales del turno; el fin a la medianoche es 1440 (explore, nota técnica)

Con `local_day_and_minutes`: `(día, inicio) = local_day_and_minutes(start_at, tz)` y `(día_fin, fin) = local_day_and_minutes(end_at, tz)`. Si `día_fin` es el día siguiente a `día` (solo pasa cuando el fin es exactamente las 00:00, porque el grupo 1 ya rechazó el cruce de medianoche), el fin vale 1440. El día de la semana es `día.isoweekday()`.

**Por qué**: los tramos se guardan en minutos locales (`0 <= start_minute < end_minute <= 1440`, KB 04), así que la comparación es entre enteros del mismo día. El fin se calcula convirtiendo `end_at` y no como `inicio + duración`, como hizo C-04 con la medianoche: no supone que la hora local avanza igual que la UTC. Los segundos no importan: en el grupo 2 el inicio está en la grilla y la duración es entera en minutos.

**Alternativa descartada**: comparar `datetime` locales armados con los minutos del tramo. Más conversiones para el mismo resultado y un caso especial para 24:00.

### D5 — `WorkingHours` sin reglas al construirse; la validez del conjunto es una función aparte (explore, decisión 4)

```python
@dataclass(frozen=True, slots=True)
class WorkingHours:
    professional_id: UUID
    weekday: int        # ISO: 1 = lunes … 7 = domingo
    start_minute: int   # minutos locales desde las 00:00
    end_minute: int     # 1440 = 24:00
```

Sin `__post_init__`: construir `WorkingHours(P1, 0, 800, 700)` no lanza. La validez la decide `validate_working_hours(slots: Sequence[WorkingHours]) -> list[Violation]`, con `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` (D8 fija el orden y D9 los mensajes).

**Por qué**: los tramos los carga el usuario por el `PUT` (C-21), así que un tramo inválido es una regla de negocio y va como resultado tipado, no como `ValueError` (regla dura). Devuelve `list[Violation]` y no `ValidationResult` porque `Ok` está atado a `Appointment`. `validate_new_appointment` no la llama (D10).

**Alternativa descartada**: validar en `__post_init__` con `ValueError`, como `Appointment` con `start_at >= end_at`. Ahí es un error de programación; acá es un dato que escribe el usuario y tiene que llegar a la UI con su código.

### D6 — Mensaje de `OUTSIDE_WORKING_HOURS` con los tramos del día (explore, decisión 5; formato fino en el propose)

- Con tramos ese día: `"El turno de {inicio} a {fin} (hora local) queda fuera del horario de atención del profesional: el {día} atiende de {a} a {b}[, de {c} a {d}…] y de {y} a {z}."`. Sin tramos: `"… del profesional: no atiende los {día en plural}."` (la autora sacó la repetición de "el profesional" en el punto de control 3.5, 2026-10-26).
- `{inicio}` y `{fin}` del turno con `format_local_time` (el fin de las 00:00 sale `"00:00"`).
- Los tramos son los **unidos** de D3, ordenados por inicio, y sus horas se formatean desde los minutos con `HH:MM`; el minuto 1440 se muestra `"24:00"` (decisión del propose: `"00:00"` como fin de un tramo se leería como un tramo vacío).
- Días: dos tuplas constantes en `rules/working_hours.py`, una en singular (`"lunes"` … `"sábado"`, `"domingo"`) y otra en plural (`"lunes"` … `"sábados"`, `"domingos"`), indexadas por `isoweekday() - 1`.
- Sin `conflicting_appointment_id` ni `reference_kind`.

**Por qué**: explica el rechazo sin esperar a C-08 (que suma el nombre del profesional). Mostrar los tramos unidos es lo que la secretaria necesita: cuándo hay atención, no cómo se cargó.

### D7 — `rules/working_hours.py` con dos funciones públicas (surgió en el propose)

```python
def check_working_hours(professional_id: UUID, start_at: datetime, end_at: datetime,
                        working_hours: Sequence[WorkingHours], tz: ZoneInfo) -> list[Violation]
def validate_working_hours(slots: Sequence[WorkingHours]) -> list[Violation]
```

Más helpers privados: `_merged_slots(slots) -> list[tuple[int, int]]` (D3) y `_format_minute(minute) -> str` (D6).

**Por qué**: una regla por módulo, función pura que recibe solo lo que usa, como `rules/same_day.py` (decisión D10 de C-04). Las dos funciones comparten los nombres de los días y el formateo de minutos; separarlas en dos módulos duplicaría eso. `check_working_hours` recibe el id y los instantes, no el `Appointment`, para que no cambie si el candidato crece.

**Alternativa descartada**: `rules/working_hours_set.py` aparte para la validez del conjunto. Un archivo más para compartir constantes con el primero.

### D8 — Códigos y orden de `validate_working_hours` (orden: decisión del propose)

Se agregan `OUTSIDE_WORKING_HOURS`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` a `ViolationCode` (valor igual al nombre).

`validate_working_hours`:

1. Recorre los tramos en el orden recibido (posición 1, 2, …) y emite **una** `INVALID_WORKING_HOURS` por tramo con día fuera de `1..7`, `start_minute` o `end_minute` fuera de `0..1440` o `start_minute >= end_minute`, aunque falle más de una condición (como `INVALID_DURATION` en C-03).
2. Con los tramos válidos, recorre los pares `(i, j)` con `i < j` en orden de posición (`i` primero, después `j`) y emite una `OVERLAPPING_WORKING_HOURS` si tienen el mismo profesional, el mismo día y `a.start < b.end and b.start < a.end` (semiabiertos: los contiguos no se solapan).

Resultado: todas las `INVALID_WORKING_HOURS` y después todas las `OVERLAPPING_WORKING_HOURS`. Un tramo inválido no entra en los pares.

**Por qué**: el orden recibido es el de las filas del formulario, así que el usuario encuentra cada error donde lo cargó; ordenar por profesional y día cambiaría las posiciones que nombra el mensaje. Primero los inválidos porque un tramo mal formado hace ruido en cualquier solapamiento. Excluirlos de los pares evita informar un solapamiento de un tramo que igual hay que corregir (por ejemplo `[750, 750)` dentro de `[540, 780)`). La cuenta por pares es O(n²), irrelevante para unos pocos tramos por profesional.

**Alternativas descartadas**: una sola violación por grupo de tramos solapados (pierde qué par chocó); reusar `Interval` de `intervals.py` (es de `datetime`, no de minutos, y su `__post_init__` lanza con `start >= end`).

### D9 — Mensajes de los códigos de tramos (surgió en el propose)

- `INVALID_WORKING_HOURS`: `"El tramo {n} no es válido: {razones unidas con ', ' y ' y '}."`. Razones: `"el día de la semana debe estar entre 1 (lunes) y 7 (domingo)"`, `"el inicio y el fin deben estar entre 00:00 y 24:00"`, `"el inicio debe ser anterior al fin"`. Ejemplo: `"El tramo 2 no es válido: el inicio debe ser anterior al fin."`.
- `OVERLAPPING_WORKING_HOURS`: `"Los tramos {i} y {j} del {día} se solapan: de {a} a {b} y de {c} a {d}."`. Ejemplo: `"Los tramos 1 y 2 del martes se solapan: de 09:00 a 13:00 y de 12:00 a 15:00."`.

La spec solo exige las posiciones (y el día en el solapamiento); la autora confirmó este texto el 2026-10-26.

**Por qué**: el tramo inválido puede tener valores que no se pueden formatear como hora (`-5`, día 8), así que se identifica por posición. Las razones siguen el estilo de `INVALID_DURATION`.

### D10 — `validate_new_appointment` no revalida los tramos (explore, decisión 4)

Los tramos que llegan en el contexto se suponen válidos (los validó el `PUT` antes de guardarlos). La regla del turno no llama a `validate_working_hours` y no informa `INVALID_WORKING_HOURS` ni `OVERLAPPING_WORKING_HOURS`. Con tramos solapados, la unión de D3 da un resultado razonable; con un tramo inválido (`start >= end`), la unión lo ignora en la práctica porque ningún turno cabe en él.

**Por qué**: un turno no es el lugar para informar errores de configuración del horario, y la respuesta `409` no tendría sentido para eso.

### D11 — Tests (surgió en el propose)

- Estilo de C-02 a C-04: datos literales, UUIDs fijos, `ZoneInfo` real, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, `@pytest.mark.parametrize` y aserciones sobre la lista completa de códigos.
- `test_validate_new_appointment.py`: `FULL_WEEK = tuple(WorkingHours(p, d, 0, 1440) for p in (P1, P2) for d in range(1, 8))` y `CTX = ScheduleContext(tz=BUENOS_AIRES, working_hours=FULL_WEEK)` (explore, decisión 6). Para los escenarios nuevos, `TUESDAY_BASE = (WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 900, 1140))` y un helper `_ctx(*slots)` que arma un contexto con esos tramos. Los escenarios se escriben con `_local` y, donde la spec da el UTC, se compara contra el literal UTC.
- `test_working_hours.py` (nuevo): `validate_working_hours` con los escenarios del requisito "Validez de un conjunto de tramos".
- `test_model.py`: `WorkingHours` con valores inválidos se construye sin lanzar (D5) y `ScheduleContext` exige `working_hours` (lo verifica mypy; no hace falta test de runtime).
- `test_violations.py`: los tres códigos nuevos en la tabla de valores serializados.

**Por qué**: un tramo de día completo hace que el horario nunca intervenga en los escenarios viejos (incluido 23:30–00:00, que termina en 1440). Un contexto aparte para los nuevos deja claro qué horario usa cada escenario.

### D12 — "Hora local en la zona horaria recibida" incluye el horario (surgió en el propose)

El texto del requisito pasa de "grilla del inicio y medianoche" a "grilla del inicio, medianoche y horario de atención". Sus dos escenarios no cambian; los de CA-7 (06:00 y 18:00 locales) van en el requisito del horario.

**Por qué**: el requisito es el que prohíbe evaluar en UTC; si no nombra el horario, la spec queda incompleta.

### D13 — El mensaje de `OUTSIDE_WORKING_HOURS` va en su requisito y no en "Contenido de cada violación" (surgió en el propose)

**Por qué**: "Contenido de cada violación" ya dice lo común (código estable, mensaje en español, sin tipo de referencia salvo en referencias). Poner el formato en el requisito nuevo evita modificar un requisito largo con siete escenarios que no cambian.

## Decisiones confirmadas por la autora

**Fecha: 2026-10-26.** Todas las decisiones de este diseño, D1 a D13, están confirmadas por la autora:

- En el explore: D1 a D6 y D10, tal como están en `docs/evidencias/explore-C-05.md`, incluida la decisión 6 (`CTX` con tramos `[0, 1440)` los 7 días, en D11).
- En la revisión del propose: el `24:00` y los tramos unidos en el mensaje (D6), D7, el orden y la exclusión de D8, D9, D11 a D13, y en la spec, los tramos solapados de profesionales distintos como válidos. En la misma revisión, la autora pidió alinear KB 07 con D2: `409` para los conflictos de agenda (horario de atención y solapamientos) y `422` para la validez del pedido.

## Risks / Trade-offs

- [`ScheduleContext` con un campo obligatorio nuevo rompe a los llamadores] → Hoy solo lo construyen los tests de dominio (una línea) y el ejemplo de `backend/README.md`; todavía no hay API (C-22).
- [El `CTX` de día completo hace que ningún test viejo ejercite el horario] → Es lo buscado: el horario tiene sus propios escenarios con `TUESDAY_BASE`, y el escenario "Fuera de horario y solapado a la vez" verifica la integración con los solapamientos.
- [Unir tramos solapados en la regla del turno esconde un conjunto inválido] → El conjunto se valida al cargarlo (`validate_working_hours`, C-21); D10.
- [Las posiciones de los mensajes de tramos dependen del orden en que llegan] → Es deliberado (D8): son las filas del formulario. C-21 debe pasar los tramos en el orden del pedido.
- [RN-AG-12 pone "pasado" entre la medianoche y el horario] → No afecta este change; C-07 decide el grupo de `IN_THE_PAST`.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain`, de los tests de dominio y de la documentación (un solo commit del change, a pedido de la autora).

## Open Questions

Ninguna que cambie el alcance.

## Desvíos durante el apply

- **Tareas 1.1 a 3.4 (2026-10-26).** Sin desvíos de fondo; el orden y el contenido siguieron `tasks.md`.
- **Tareas 2.1 y 3.1 (RED).** Los rojos fueron errores de colección (`AttributeError` por los miembros de `ViolationCode` que se nombran en el `parametrize`, e `ImportError` de `WorkingHours`), no casos individuales en rojo. La razón es la pedida (el miembro o el tipo no existe).
- **Tarea 3.3 (RED por mypy).** Además de mypy, `pytest` también falla (la colección de `test_validate_new_appointment.py` lanza `TypeError` en la línea de `CTX`); se anotó el error de mypy como pedía la tarea.
- **Tarea 3.4.** El README solo actualizó el ejemplo de §Dominio; la tabla de módulos y el párrafo de los grupos quedan para 8.1. El ejemplo ya construye `WorkingHours` y el contexto con tramos, pero todavía no hay ninguna regla que los use.
- **Punto de control 3.5 (aprobado por la autora el 2026-10-26, con dos ajustes).** (1) El mensaje de `OUTSIDE_WORKING_HOURS` sin tramos ese día termina en ": no atiende los {día en plural}." en lugar de ": el profesional no atiende…", para no repetir "el profesional"; se actualizaron D6 y la spec (los mensajes de D9 no tenían esa frase). (2) Se saca de `test_model.py` el test que solo comprobaba que `WorkingHours` guarda los valores (casi tautológico); queda el parametrizado de valores inválidos, que documenta D5.
- **Tareas 4.1 a 9.7 (2026-10-26).** Sin cambios de comportamiento respecto de la spec y el diseño. Desvíos de proceso:
- **Tareas 4.7 y 4.8 (unidas).** Se implementaron juntas la redacción de los mensajes de D9 y el refactor (docstrings, constantes `Final`, helper `_join_with_and`). El rojo de 4.7 se vio (6 tests en rojo).
- **Tarea 4.7 (tests extra).** Además de los tests pedidos (las posiciones en los mensajes, sin `conflicting_appointment_id` ni `reference_kind`), se agregaron los mensajes exactos de D9 (una razón, dos razones, rangos y solapamiento) y un caso con tres razones, para cubrir la unión `", "` / `" y "`. No cambian la spec.
- **Tareas 4.3, 4.5, 4.6, 5.3 a 5.7, 7.1 y 7.2 (pasaron de entrada).** Cada una pasó de entrada o con pocos casos en rojo; se comprobó que puede fallar con mutaciones temporales (quitar el día, el profesional, `<=`/`<`, evaluar en UTC, mover la regla, excluir el tramo inválido de los pares, invertir el orden de los pares), y se restauró el código.
- **Tarea 5.6 (hallazgo del apply que volvió a la spec).** Quitar el fin 1440 de D4 no hacía fallar ningún escenario de la spec: con el tramo `[1200, 1440)`, un fin de 0 también cabe. Se agregó el test `ending_at_local_midnight_after_slot_end_is_rejected` (tramo `[1200, 1380)`, turno 23:30–00:00 hora local = 02:30–03:00 UTC del 2026-10-21 → `OUTSIDE_WORKING_HOURS`), que sí falla sin el 1440. En la revisión del apply (2026-10-26), la autora decidió que es comportamiento que la spec no cubría: se agregó el escenario "Turno que termina a la medianoche local, después del fin del tramo".
- **Tarea 5.8 (hallazgo del apply que volvió a la spec).** Se agregó el test `slot_nested_in_another_does_not_shorten_the_merged_slot` (`[600, 700)` dentro de `[540, 780)`; turno 12:00–12:30 hora local = 15:00–15:30 UTC → `Ok`), que falla si la unión de D3 toma el fin del último tramo en lugar del máximo. En la revisión del apply (2026-10-26), la autora decidió que es comportamiento que la spec no cubría: se agregó el escenario "Tramo contenido en otro" y el texto del requisito ahora dice que los tramos que se pisan también se unen, desde el menor inicio hasta el mayor fin.
- **Tareas 6.1 a 6.4 (un solo GREEN).** Los tres mensajes (tramos del día, día sin tramos, tramos unidos con `24:00`) se escribieron en rojo juntos y se implementaron en un solo paso con `_outside_message`; los días en plural se agregaron en ese paso porque el escenario del domingo los pide. El refactor de 6.4 no necesitó cambios extra.
- **Tarea 8.1 / 8.2 / 8.3.** `README.md` actualizado (tabla `model` y `rules/`, párrafo de los grupos). KB 05, KB 07 y `CHANGES.md` §[C-05] ya coincidían: no se editaron. La actualización del Purpose de la spec principal queda propuesta para el archive, a decisión de la autora.
- **Nota de conteo.** El baseline de 3.5 es 186 tests (se quitó un test de `test_model.py`); el total final es 232 (46 nuevos: 21 en `test_working_hours.py`, 25 en `test_validate_new_appointment.py`).
