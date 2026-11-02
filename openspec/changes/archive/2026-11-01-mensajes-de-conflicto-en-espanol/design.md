# Design

## Context

C-07 dejó `validate_new_appointment(request, references, existing_appointments, context) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`. El grupo 1 (`_request_validity_violations`: referencias → duración → inicio → medianoche → pasado) corta si encuentra algo; el grupo 2 (`_agenda_conflict_violations`: horario → bloqueo → profesional → sillón) informa todo junto. El grupo 2 recibe solo el turno candidato, los turnos existentes y el contexto: no recibe `references`, así que no conoce nombres.

`Violation` (en `violations.py`, *frozen* con slots) tiene `code`, `message`, `conflicting_appointment_id`, `reference_kind` y `conflicting_block_id`, los tres últimos con `None` por defecto. `Interval(start, end)` (en `intervals.py`) lanza `ValueError` si `start >= end`; `Appointment.interval` lo devuelve. `Professional` y `Chair` (en `model.py`) solo tienen `id` y `active`.

Los mensajes que cambian se arman hoy así: `rules/overlap.py` con un f-string sin nombre ni horario (las reglas no reciben `tz`); `rules/working_hours.py` en `_outside_message`; `rules/blocks.py` en `_blocked_message`. `check_blocks` solo devuelve bloqueos que se solapan con el turno, y un bloqueo con `inicio >= fin` nunca se solapa (`_overlapping_blocks`), así que todo bloqueo en conflicto tiene un intervalo válido. Ninguna otra prueba llama a estas reglas directamente: `test_blocks.py` y `test_working_hours.py` prueban `validate_block`, `appointments_affected_by_block` y `validate_working_hours`.

Solo `test_validate_new_appointment.py` construye `Professional` (6 veces) y `Chair` (6 veces), más el ejemplo de `backend/README.md`. Los seis textos exactos que cambian están en ese archivo (tests de las líneas 1134, 1148, 1159, 1353, 1368 y 1384), y el test de solapamiento de la línea 468 solo verifica que el mensaje contenga el id. La suite de C-07 cerró con `330 passed` y `mypy --strict` sin errores en 31 archivos. El proyecto no tiene `ruff` ni `black` configurados (`pyproject.toml` solo trae `pytest` y `mypy`).

La motivación está en `proposal.md` y los requisitos en `specs/`. D1 a D5 salen del explore del 2026-10-30 (`docs/evidencias/explore-C-08.md`) y la autora las confirmó. D6 a D12 surgieron en el propose.

## Goals / Non-Goals

**Goals:**
- Que cada violación de conflicto con un turno o un bloqueo lleve su intervalo en UTC, con la invariante "intervalo si y solo si hay id".
- Que los cuatro mensajes de conflicto de agenda digan el nombre del profesional o del sillón y el rango en hora local, sin quedar mal con un nombre vacío.
- Que el bloque A (intervalo) no cambie ningún texto, para que la autora lo revise con la suite de C-07 intacta.

**Non-Goals:**
- Validar nombres (C-09) ni serializar el intervalo (C-22).
- Cambiar los mensajes que no son de conflicto de agenda (D3).
- Cambiar el orden de RN-AG-12 o el corte del grupo 1 (D4).

## Decisions

### D1 — `Violation.conflicting_interval`, al final y en UTC (explore, decisión 2)

```python
@dataclass(frozen=True, slots=True)
class Violation:
    code: ViolationCode
    message: str
    conflicting_appointment_id: UUID | None = None
    reference_kind: ReferenceKind | None = None
    conflicting_block_id: UUID | None = None
    conflicting_interval: Interval | None = None
```

Se carga en `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` con `other.interval` (el turno existente, ya normalizado a UTC) y en `BLOCKED_TIME` con `Interval(block.start_at, block.end_at)` (D9). En el resto queda `None`, incluida `OUTSIDE_WORKING_HOURS`. Invariante: `conflicting_interval is not None` si y solo si `conflicting_appointment_id` o `conflicting_block_id` no son `None`.

**Por qué**: un solo campo no permite estados imposibles (inicio sin fin). El dominio guarda instantes en UTC (DD-07); la hora local legible ya está en el mensaje y la API (C-22) serializa en ISO con offset. `OUTSIDE_WORKING_HOURS` choca con la ausencia de un tramo, no con un intervalo. Al final y con default no cambia ninguna construcción existente, y el bloque A no toca textos.

**Alternativas descartadas**: dos campos `conflicting_start_at` / `conflicting_end_at` (permiten uno sin el otro); el intervalo en hora local (rompe DD-07); el tramo más cercano como intervalo de `OUTSIDE_WORKING_HOURS` (no es "lo que choca").

### D2 — `Professional.full_name` y `Chair.name`, obligatorios y sin validar (explore, decisión 1)

```python
@dataclass(frozen=True, slots=True)
class Professional:
    id: UUID
    full_name: str
    active: bool

@dataclass(frozen=True, slots=True)
class Chair:
    id: UUID
    name: str
    active: bool
```

Sin valor por defecto ni `__post_init__`: el dominio no recorta ni valida el nombre. El campo va entre `id` y `active`, en el orden de KB 04 (orden elegido en el propose).

**Por qué**: el dato vive en su entidad y C-15 lo mapea directo a la columna (nombres de KB 04). Sin default, mypy marca a cualquier llamador que se olvide del nombre (criterio de `ScheduleContext.now`). Un nombre vacío es un dato del usuario, no un error de programación: lo rechaza C-09 en el alta con una violación, así que acá no se lanza `ValueError`. El profesional y el sillón del conflicto son siempre los del pedido (el turno que choca comparte ese recurso), así que no hacen falta nombres de otras entidades.

**Alternativas descartadas**: un mapa de nombres en `ScheduleContext` (separa el dato de su entidad); `full_name: str = ""` (un llamador que se olvida no se entera); validar al construir (mezcla un error del usuario con uno de programación).

### D3 — Cuatro mensajes nuevos con el nombre como sujeto (explore, decisión 3)

| Código | Texto (P1 = "Dra. Laura Quiroga", S1 = "Sillón 1") |
|---|---|
| `PROFESSIONAL_OVERLAP` | `{profesional} ya tiene un turno de {inicio} a {fin} (hora local) que se superpone (turno {id}).` |
| `CHAIR_OVERLAP` | `{sillón} está ocupado de {inicio} a {fin} (hora local) por un turno que se superpone (turno {id}).` |
| `OUTSIDE_WORKING_HOURS` | `El turno de {inicio} a {fin} (hora local) queda fuera del horario de atención: {profesional} atiende el {día} de … y de ….` / `…: {profesional} no atiende los {días}.` |
| `BLOCKED_TIME` | `El turno de {inicio} a {fin} (hora local) se superpone con un bloqueo de agenda: {profesional} tiene la agenda bloqueada del {dd/mm/aaaa HH:MM} al {dd/mm/aaaa HH:MM} (hora local) (bloqueo {id}).` + ` Motivo: {motivo}.` si hay motivo |

- En los solapamientos, `{inicio}` y `{fin}` son los del **turno existente**, con `format_local_time` (`HH:MM`, o `HH:MM:SS` con segundos); por eso las dos reglas reciben `tz`.
- `OUTSIDE_WORKING_HOURS` y `BLOCKED_TIME` conservan sus horas, sus formatos y la regla del motivo; solo cambian la frase y el lugar del id del bloqueo.
- No cambian `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE` (aunque la entidad tenga nombre: identifica por id), `INVALID_BLOCK`, `INVALID_WORKING_HOURS` ni `OVERLAPPING_WORKING_HOURS`. `rules/references.py`, `duration.py`, `start_time.py`, `same_day.py` y `past.py` no se tocan.

**Por qué**: el dominio no sabe si corresponde "la Dra." o "el Dr.": sin artículo y como sujeto, la frase nunca queda mal (ajuste de la autora). Los seis textos exactos aprobados en C-05 y C-06 que cambian se marcan `MODIFIED` en el delta, con la frase que dice qué reemplazan.

**Alternativas descartadas**: "del profesional {nombre}" (con un nombre que ya trae título queda redundante y el sustituto vacío no encaja); nombrar también al paciente (no lo pide US-006).

### D4 — "Todas" es dentro del primer grupo que falla (explore, decisión 4)

Sin cambios de código: el corte después del grupo 1 ya está implementado y probado ("Violación de validez en un horario ocupado", "Turno en el pasado en un horario ocupado"). Se agrega la aclaración al requisito "Todas las violaciones, en orden estable"; la KB (RN-AG-12, DD-08, US-006 CA-2) y `CHANGES.md` §[C-08] ya se sincronizaron. No hace falta un escenario nuevo.

### D5 — Un solo change, dos bloques y un punto de control (explore, decisión 5)

Bloque A: `conflicting_interval` (estructural; ningún mensaje cambia, la suite de C-07 queda verde sin tocar textos). Punto de control con la autora. Bloque B: nombres en el modelo, migración de los tests, sustituto del nombre y los cuatro mensajes.

**Por qué**: el tamaño es comparable a C-06; dividirlo obliga a reescribir las dependencias y los gates de C-11 y C-22 en `CHANGES.md`. El punto de control separa lo que cambia la estructura de lo que cambia textos aprobados.

### D6 — `rules/names.py` con `subject_name` (surgió en el propose)

```python
def subject_name(name: str, generic: str) -> str
```

Devuelve `name.strip()` si no está vacío; si no, `generic`. Los llamadores pasan `"El profesional"` / `"El sillón"` (solapamientos, al principio de la oración) o `"el profesional"` (horario y bloqueo, después de dos puntos), como constantes `Final` en cada regla.

**Por qué**: la misma regla se usa en tres módulos (`overlap`, `working_hours`, `blocks`); un helper público en un módulo propio se prueba directo (`test_names.py`) sin construir un pedido entero. El nombre se muestra recortado (decisión de la autora antes del apply, 2026-10-30): el nombre es el sujeto de la oración, así que un espacio de más al principio o al final deja espacios dobles en el medio del mensaje. La entidad sigue conservando el valor tal como se cargó (D2); solo se recorta al mostrarlo. Es distinto del motivo del bloqueo de C-06: ahí `strip()` solo decide si el motivo está vacío y el motivo se muestra tal como se cargó (D8 de C-06, `_blocked_message`). C-08 no cambia el motivo.

**Alternativas descartadas**: un helper privado repetido en tres módulos (duplica la regla); ponerlo en `intervals.py` (no tiene que ver con intervalos); que el sustituto lo elija el modelo (`Professional.display_name`) (mezcla gramática del mensaje con la entidad).

### D7 — Firmas de las reglas del grupo 2 (surgió en el propose)

```python
def check_professional_overlap(candidate: Appointment, existing: Sequence[Appointment], tz: ZoneInfo, professional_name: str) -> list[Violation]
def check_chair_overlap(candidate: Appointment, existing: Sequence[Appointment], tz: ZoneInfo, chair_name: str) -> list[Violation]
def check_working_hours(professional_id, start_at, end_at, working_hours, tz, professional_name: str) -> list[Violation]
def check_blocks(professional_id, start_at, end_at, blocks, tz, professional_name: str) -> list[Violation]
```

El nombre va al final, sin valor por defecto, como `str` (no la entidad).

**Por qué**: el explore pidió pasar el nombre como `str`; así las reglas no dependen de `Professional` ni de `Chair` ni de su `active`. Al final y sin default, mypy marca al único llamador (`validate.py`) y no cambia el orden de lo que ya existía.

### D8 — `validate.py` acota el tipo de las referencias (surgió en el propose)

`_agenda_conflict_violations(candidate, existing_appointments, context, professional_name, chair_name)` pasa `context.tz` y los nombres a las reglas. En `validate_new_appointment`, la condición que ya acota `end_at` suma las dos referencias:

```python
if (
    validity_violations
    or end_at is None
    or references.professional is None
    or references.chair is None
):
    return Rejected(tuple(validity_violations))
```

con el comentario que ya existe ampliado: una referencia `None` siempre produce `UNKNOWN_REFERENCE` en el grupo 1, así que esas condiciones solo acotan el tipo.

**Por qué**: es el mismo patrón que `end_at`, sin `assert` ni `cast`, y `mypy --strict` queda conforme. Después del grupo 1, el profesional y el sillón existen y están activos.

**Alternativas descartadas**: pasar `references` entero al grupo 2 (el grupo 2 solo necesita dos `str`); `assert references.professional is not None` (se apaga con `-O`).

### D9 — Intervalo del bloqueo armado en la regla (surgió en el propose)

`check_blocks` arma `Interval(block.start_at, block.end_at)` para cada bloqueo que devuelve `_overlapping_blocks`; no se agrega `Block.interval`.

**Por qué**: `Interval` lanza con `inicio >= fin`, y un bloqueo así se puede construir (lo rechaza `validate_block`). Una propiedad en `Block` lanzaría al usarla sobre un bloqueo inválido; dentro de `check_blocks` solo llegan bloqueos que se solapan, que siempre tienen `inicio < fin`. Un bloqueo de varios días conserva sus extremos: no se recorta al día ni al turno.

### D10 — Tests (surgió en el propose)

- Estilo de C-02 a C-07: datos literales, `ZoneInfo` real, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, `@pytest.mark.parametrize`, aserciones sobre la lista completa y textos exactos.
- `test_validate_new_appointment.py`: constantes `P1_NAME = "Dra. Laura Quiroga"` y `S1_NAME = "Sillón 1"` (y `"Dr. Martín Sosa"` / `"Sillón 2"` para las demás entidades); `_refs` usa los nombres por defecto; los 12 constructores cambian de forma mecánica (`git diff` lo comprueba). Un helper `_conflicts(result)` devuelve `(code, conflicting_appointment_id, conflicting_block_id, conflicting_interval)` por violación. Los intervalos esperados se escriben con `_at(...)` o con literales UTC de la spec, sin recalcular la conversión.
- `test_violations.py`: `conflicting_interval` por defecto `None` y conserva el valor. `test_model.py`: nombres de `Professional` y `Chair`. `test_names.py` (nuevo): `subject_name`.
- Los seis tests de texto exacto de C-05 y C-06 y el de solapamiento de la línea 468 se reescriben con los textos nuevos (RED de cada grupo del bloque B).

### D11 — Requisitos de la spec (surgió en el propose)

En `appointment-scheduling`, ocho requisitos `MODIFIED` (los dos de solapamiento, "Todas las violaciones, en orden estable", "Contenido de cada violación", "Turno dentro del horario de atención", "Turno fuera de los bloqueos del profesional", "Mensaje de un turno bloqueado" y "Mensaje de un turno en el pasado") y uno `ADDED` ("Nombre del profesional y del sillón"). Los escenarios del intervalo van en los requisitos de cada regla; la invariante, los textos de solapamiento, el sustituto de los solapamientos y los mensajes que no cambian, en "Contenido de cada violación"; el sustituto del horario y del bloqueo, en sus requisitos de mensaje. "Mensaje de un turno en el pasado" solo pierde la frase "queda para C-08" (no cambia el mensaje). Los nombres de P1 y S1 se dicen en el cuerpo de cada requisito que los usa, porque el archive copia requisitos y no el párrafo de convenciones del delta.

### D12 — Verificación estática: `mypy --strict` (surgió en el propose)

El proyecto no tiene `ruff` ni `black` (ni en `pyproject.toml` ni en el venv), y C-07 cerró solo con `mypy --strict`. Este change sigue ese precedente y no agrega herramientas; el estilo (líneas de hasta 100 caracteres, docstrings estilo Google) se mantiene a mano.

## Risks / Trade-offs

- [Cambian seis textos exactos aprobados en C-05 y C-06] → Van como `MODIFIED`, con la frase que dice qué reemplazan, y sus tests se reescriben en rojo antes de cambiar el código (bloque B). El verify lista los seis.
- [`Professional` y `Chair` con un campo obligatorio nuevo rompen a los llamadores] → Hoy solo los construyen `test_validate_new_appointment.py` y el ejemplo de `backend/README.md`; todavía no hay persistencia (C-15) ni API (C-22).
- [El sustituto genérico ("El profesional") puede ocultar un dato faltante] → Solo pasa con un nombre vacío, que C-09 va a rechazar en el alta; el rechazo sigue siendo correcto y el id del turno o del bloqueo sigue en el mensaje.
- [El intervalo de un bloqueo de varios días puede ser largo] → Es lo que choca; la hora local legible ya está en el mensaje. La API decide cómo mostrarlo (C-22).
- [Construir `Interval` en `check_blocks` lanzaría con un bloqueo inválido] → Solo llegan bloqueos que se solapan, que siempre tienen `inicio < fin` (D9); el escenario "Bloqueo inválido recibido con la agenda" sigue en verde y lo prueba.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain`, de los tests de dominio y de la documentación (un solo commit del change, a pedido de la autora).

## Open Questions

Ninguna que cambie el alcance. La autora confirma en el punto de control D2 (orden de los campos), D7 (firmas) y D12 (sin `ruff` ni `black`). D6 (nombre recortado al mostrarlo) ya lo decidió antes del apply.

## Desvíos del apply

**Estado final del apply:** 49/49 tareas y 102 escenarios trazados. Las entradas 1–9 son el registro histórico de las reanudaciones y detenciones; quedaron resueltas con las autorizaciones posteriores de la autora. Los dos filtros están implementados y todas las verificaciones finales pasan. No se archivó.

8. **Defecto latente de C-06 corregido con autorización de la autora.** `_overlapping_blocks` no excluía bloqueos con inicio posterior al fin; el pedido previo de 10:30–11:00 local pasaba por casualidad. Para BL1 de 12:00 a 10:00 local (15:00 a 13:00 UTC), el pedido de 09:00 a 13:00 local (12:00 a 16:00 UTC), duración explícita de 240 minutos, lanzaba al construir `Interval`. Se agregó el escenario 97 y la tarea 11.5. RED: `1 failed, 181 deselected in 0.40s`, `ValueError: start debe ser anterior a end`. Único GREEN de producción: `and block.start_at < block.end_at` en `_overlapping_blocks`; `374 passed in 0.92s`. Mutación sin filtro: `1 failed, 373 passed in 1.42s`, exclusivamente el test nuevo y el mismo ValueError. Restaurado: `374 passed in 1.27s`. No se cambió `_overlaps` ni se refactorizó. Ambos pedidos del ejemplo ahora devuelven `Ok`.
9. **Nueva detención obligatoria en el paso 6.** Con el mismo bloqueo invertido y un turno reservado de P1 de 09:00 a 13:00 local, `appointments_affected_by_block` devuelve el propio turno (id ficticio `00000000-0000-0000-0000-000000000071`) en vez de `[]`; no lanza. Se comprobó por llamada directa y no se corrigió. Se detuvo sin ejecutar los pasos 7–9 ni continuar 13.3–13.8. En esa detención, `verify-C-08.md` seguía parcial y mypy/OpenSpec aún no se habían vuelto a ejecutar; el cierre actual de la entrada 10 reemplaza ese estado. Baseline de esta reanudación: `373 passed in 1.33s`, `Success: no issues found in 33 source files`.

1. La sesion de Claude Code se corto durante el bloque B y se retomo con Codex el 2026-11-01. Baseline recuperado: `361 passed in 1.32s`; `Success: no issues found in 33 source files`. Las tareas 7 y 8 tenian codigo, tests y documentacion sin marcar; tambien se habian adelantado los textos y el cableado de 9.1/9.2 y el test de 9.3. No se borraron los tests verdes: se recupera evidencia RED mediante mutaciones temporales restauradas.
2. En 7.1 se quitaron temporalmente los campos, por separado: 3 fallos `TypeError` para `Professional.full_name` y 3 para `Chair.name`. En 8.1 se retiro temporalmente el modulo: `ModuleNotFoundError`, 1 error de coleccion. Esto acredita sensibilidad de los tests, no un RED historico de la sesion interrumpida.
3. La comprobacion temporal de 7.2 produjo 13 errores mypy de argumento faltante: los 12 constructores originales y el agregado por el test del grupo 5.1. Se conserva ese caso del bloque A aprobado. El ejemplo del README se ejecuto y dio `2026-10-20 13:30:00+00:00`.
4. Primera mutacion de 8.2 (`return name if name else generic`): 4 fallos (dos blancos y dos nombres con espacios), porque tambien elimina el recorte; segunda (`return name if stripped else generic`): 2 fallos de recorte. Se restauro cada mutacion; suite 361 tests y mypy en verde.

5. Los tests de 9.1 y 9.3 y el GREEN de 9.2 estaban adelantados. RED recuperado con mensaje sin nombre ni rango: 2 fallos. Las mutaciones candidate y UTC dieron 2 fallos cada una; restauradas, 361 passed y mypy sin errores. Se conserva el nombre mas descriptivo del test de 9.1 heredado (`overlap_messages_name_resource_and_local_range_of_existing`).

6. Al revisar las evidencias de 8.2 se precisó la mutación de la condición sin eliminar el recorte (`return stripped if name else generic`): 2 failed, 6 passed, exclusivamente los dos casos en blanco; se restauró. Para 9.1 se precisó el texto anterior con "El profesional": 1 failed en el test de texto exacto; se restauró. Las primeras mutaciones más amplias también quedan registradas como tales, sin atribuirles evidencia histórica.
7. **Apply detenido en la verificación del grupo 13 (2026-11-01)** por una contradicción material entre D9, la garantía de la spec y el comportamiento heredado. `rules/blocks.py::_overlaps` solo compara extremos y no excluye intervalos inválidos. Con BL1 de 12:00 a 10:00 local (el mismo bloqueo inválido del escenario aprobado), un pedido válido de 09:00 a 13:00 local (240 minutos, horario completo) cumple ambas comparaciones y llega a `Interval(block.start_at, block.end_at)`: lanza `ValueError: start debe ser anterior a end`. D9 afirma que los bloqueos devueltos siempre tienen inicio menor que fin y la spec dice que un bloqueo inválido no se superpone con ningún turno. El test existente del pedido de 10:30 a 11:00 pasa, pero no prueba esa garantía general. Se reprodujo por llamada directa sin agregar tests ni cambiar comportamiento. No se corrigió: se respeta la instrucción de detenerse ante contradicciones. Las tareas 13.1 y 13.2 están completas; 13.3 a 13.8 quedan pendientes. `openspec validate --strict` se consultó solo para el informe y pasó; no se marcó 13.6 ni se archivó.

10. **Segundo arreglo del mismo defecto latente de C-06, autorizado por la autora.** `appointments_affected_by_block` también devolvía un turno reservado de P1 de 09:00 a 13:00 local para el bloqueo invertido de 12:00 a 10:00 local, aunque su contrato exige una lista vacía. Se agregó la tarea 11.6 y el test público `test_appointments_affected_by_invalid_block_enclosed_by_appointment_returns_empty`. Baseline: `374 passed in 1.23s`. RED: `1 failed, 9 deselected in 0.25s`, `AssertionError: assert [Appointment(...)] == []`. Único cambio de producción: `and block.start_at < block.end_at` en `appointments_affected_by_block`. GREEN: `375 passed in 1.36s`. Mutación quitando únicamente esa condición: `1 failed, 374 passed in 1.45s`, exclusivamente el nuevo test. Restaurado, evidencia final: `375 passed in 1.02s`; mypy sin errores en 33 archivos; OpenSpec válido. No se modificó `_overlaps` ni se refactorizó producción.
11. **Conteo real del delta y archivo de test adicional.** «Turnos afectados por un bloqueo» no estaba en el delta. Se copió como MODIFIED desde la spec principal sin alterar sus cuatro escenarios existentes y se agregó «Turno que abarca un bloqueo inválido», siguiendo la instrucción explícita. El total es 102, no 98: 97 previos + 4 copiados + 1 nuevo. La trazabilidad cubre los 102. `test_blocks.py` no figuraba en el Impact original, pero su modificación fue autorizada expresamente para el segundo arreglo; se mantiene el requisito principal intacto y no se amplió el cambio de producción.
