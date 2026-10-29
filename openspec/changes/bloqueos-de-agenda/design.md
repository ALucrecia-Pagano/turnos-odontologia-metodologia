# Design

## Context

C-05 dejó `validate_new_appointment(request, references, existing_appointments, context) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`. `_request_validity_violations` (grupo 1: referencias → duración → inicio en la grilla → medianoche) corta si encuentra algo. `_agenda_conflict_violations(candidate, existing_appointments, context)` (grupo 2) suma `check_working_hours`, `check_professional_overlap` y `check_chair_overlap`, todo junto. El candidato (`Appointment`, con `start_at < end_at` garantizado) existe recién en el grupo 2.

`ScheduleContext` (en `model.py`, *frozen* con slots) tiene `tz: ZoneInfo` y `working_hours: tuple[WorkingHours, ...]`, sin valores por defecto; su docstring ya anuncia los bloqueos. `model.py` tiene `_to_utc(field_name, value)`, que normaliza a UTC y lanza `ValueError` con un instante naive. `intervals.py` tiene `Interval` (lanza `ValueError` si `start >= end`), `overlaps(a, b)`, `local_day_and_minutes` y `format_local_time` (`HH:MM`). `rules/overlap.py` tiene `OCCUPYING_STATUSES` y ordena por `(start_at, str(id))`. `Violation` tiene `code`, `message`, `conflicting_appointment_id` y `reference_kind`, los dos últimos con `None` por defecto. `ViolationCode` no tiene `BLOCKED_TIME` (sí está en el catálogo de KB 07, que ya suma `INVALID_BLOCK`).

En los tests, solo `CTX` y `_ctx(*slots)` de `test_validate_new_appointment.py` construyen un `ScheduleContext` (además del ejemplo de `backend/README.md`). La suite de C-05 cerró con 232 tests y `mypy --strict` sin errores en 26 archivos.

La motivación está en `proposal.md` y los requisitos en `specs/appointment-scheduling/spec.md`. D1 a D6 salen del explore del 2026-10-28 (`docs/evidencias/explore-C-06.md`) y la autora las confirmó. D7 a D12 surgieron en el propose y la autora las confirmó el 2026-10-28, con un ajuste en D8.

## Goals / Non-Goals

**Goals:**
- Rechazar el turno que pisa un bloqueo del profesional, con el id del bloqueo, sin que el resultado dependa del filtrado del llamador.
- Que la validez de un bloqueo y la lista de turnos afectados sean funciones puras del dominio que C-16 y C-21 puedan usar antes y después de guardar.
- Que los tests de C-02 a C-05 sigan verificando lo mismo: solo cambia la construcción de `CTX` y `_ctx`.

**Non-Goals:**
- Revalidar los bloqueos dentro de `validate_new_appointment` (D3).
- Persistencia, constraint en PostgreSQL y endpoints de bloqueos (C-16, C-21).
- Validar que los bloqueos respeten la grilla o no se pisen entre sí (explore, decisión 3, confirmado por la autora).
- Mensajes con el nombre del profesional (C-08).

## Decisions

### D1 — Los bloqueos llegan en `ScheduleContext.blocks`, sin valor por defecto (explore, decisión 1)

```python
@dataclass(frozen=True, slots=True)
class ScheduleContext:
    tz: ZoneInfo
    working_hours: tuple[WorkingHours, ...]
    blocks: tuple[Block, ...]
```

El dominio elige los bloqueos del profesional del pedido (`professional_id`); el llamador puede mandar bloqueos de cualquier profesional o fecha.

**Por qué**: es D1 de C-05. La firma de `validate_new_appointment` no cambia; sin valor por defecto, mypy marca a cualquier llamador que se olvide los bloqueos, mientras que con `()` un olvido sería "no hay bloqueos" sin aviso. Filtrar adentro es el criterio de "El dominio filtra los turnos que recibe".

**Alternativas descartadas**: un parámetro `blocks` suelto en `validate_new_appointment` (vuelve a cambiar la firma); `blocks: tuple[Block, ...] = ()` (el olvido pasa en silencio).

### D2 — La regla va en el grupo 2, después del horario y antes de los solapamientos (explore, decisión 2)

```python
return (
    check_working_hours(...)
    + check_blocks(candidate.professional_id, candidate.start_at, candidate.end_at,
                   context.blocks, context.tz)
    + check_professional_overlap(candidate, existing_appointments)
    + check_chair_overlap(candidate, existing_appointments)
)
```

El orden queda horario → bloqueo → profesional → sillón, sin cortar. El grupo 1 sigue cortando antes.

**Por qué**: es el orden de RN-AG-12. El bloqueo es un conflicto de agenda (la API responderá `409`), no un pedido malformado. En el grupo 2 el candidato ya tiene `start_at < end_at`, así que la regla no necesita guardas.

**Alternativa descartada**: que el bloqueo corte el grupo 2. Rompe DD-08 (todas las violaciones juntas).

### D3 — `Block` no valida el orden; `validate_block` devuelve `INVALID_BLOCK` (explore, decisión 3)

```python
@dataclass(frozen=True, slots=True)
class Block:
    id: UUID
    professional_id: UUID
    start_at: datetime
    end_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))
        object.__setattr__(self, "end_at", _to_utc("end_at", self.end_at))
```

`__post_init__` solo normaliza a UTC (un instante naive es `ValueError`, error de programación, igual que en el resto del modelo). `Block(..., start_at=12:00, end_at=10:00)` se construye sin lanzar. La validez la decide `validate_block(block) -> list[Violation]`. `validate_new_appointment` no la llama: los bloqueos del contexto se suponen válidos (los validó el `POST` antes de guardarlos).

**Por qué**: el bloqueo lo carga el usuario por `POST /blocks` (C-21), y US-011 CA-2 es un criterio de negocio que tiene que llegar a la UI con su código (`422`), no un `ValueError` (regla dura). Es D5 de C-05. Devuelve `list[Violation]` y no `ValidationResult` porque `Ok` está atado a `Appointment`.

**Alternativas descartadas**: `ValueError` en `__post_init__` (como `Appointment`): haría imposible construir el bloqueo que la función tiene que rechazar; las dos cosas a la vez, por la misma razón.

### D4 — Comparación entre instantes UTC; la hora local solo para el mensaje (explore, decisión 4)

La regla compara `start_at` y `end_at` del bloqueo y del turno, todos en UTC, con la condición semiabierta `a.start < b.end and b.start < a.end`. No se pasa a hora local ni se parte el bloqueo por día.

**Por qué**: el bloqueo es un intervalo de instantes (`timestamptz`, KB 04), no una regla semanal en minutos locales como el horario. La conversión UTC → local conserva el orden, así que solaparse en UTC es solaparse en hora local. Un bloqueo de varios días no necesita tratamiento especial.

**Alternativas descartadas**: comparar en hora local día por día (obliga a partir el bloqueo y no cambia el resultado); guardar fecha y minutos locales (contradice KB 04 y DD-07).

### D5 — Una `BLOCKED_TIME` por bloqueo, con `conflicting_block_id` (explore, decisión 5)

`Violation` suma `conflicting_block_id: UUID | None = None`, **al final** de los campos, para que las construcciones existentes (por nombre o posicionales) no cambien. `check_blocks` emite una `BLOCKED_TIME` por cada bloqueo del profesional que se solapa, ordenadas por `(start_at, str(id))`, con `conflicting_block_id` y sin `conflicting_appointment_id` ni `reference_kind`. Se agregan `BLOCKED_TIME` e `INVALID_BLOCK` a `ViolationCode` (valor igual al nombre).

**Por qué**: es el patrón de `PROFESSIONAL_OVERLAP`: cada violación lleva un id, y el orden no depende de la lista recibida. Un campo aparte del de turnos evita que la API tenga que adivinar a qué entidad apunta el id. C-08 ya nombraba `conflicting_block_id`; se adelanta porque US-004 CA-4 pide el id del bloqueo.

**Alternativas descartadas**: reusar `conflicting_appointment_id` (ambiguo); una sola violación con el primer bloqueo (pierde información) o con todos los ids (no entra en el modelo de `Violation`).

### D6 — `appointments_affected_by_block` devuelve los turnos, sin modificarlos (explore, decisión 6)

```python
def appointments_affected_by_block(block: Block, appointments: Sequence[Appointment]) -> list[Appointment]
```

Filtra mismo profesional, `status in OCCUPYING_STATUSES` (importado de `rules/overlap.py`) y solapamiento semiabierto; ordena por `(start_at, str(id))`; devuelve los mismos objetos recibidos.

**Por qué**: la respuesta del `POST` tiene que mostrar los turnos para reprogramarlos (Flujo 4 de KB 07). La función es pura y los `Appointment` son *frozen*, así que "no cancela ni mueve" (SU-05, confirmada) se cumple por construcción y se verifica en el test. Reusar `OCCUPYING_STATUSES` deja una sola definición de "activo" (RN-AG-08). El borde compone `validate_block` y, si da vacía, esta función.

**Alternativas descartadas**: devolver `list[UUID]` (la API tendría que volver a buscar los turnos); un resultado combinado con la validez (junta dos preguntas que el borde puede componer).

### D7 — `rules/blocks.py` con tres funciones públicas (surgió en el propose)

```python
def check_blocks(professional_id: UUID, start_at: datetime, end_at: datetime,
                 blocks: Sequence[Block], tz: ZoneInfo) -> list[Violation]
def validate_block(block: Block) -> list[Violation]
def appointments_affected_by_block(block: Block, appointments: Sequence[Appointment]) -> list[Appointment]
```

Más un helper privado `_overlaps(start_a, end_a, start_b, end_b) -> bool` con la condición semiabierta.

**Por qué**: un módulo por tema, como `rules/working_hours.py` (D7 de C-05). `check_blocks` recibe el id y los instantes, no el `Appointment`, igual que `check_working_hours`; `tz` es solo para el mensaje. Las tres funciones comparten la condición de solapamiento.

**Alternativa descartada**: usar `overlaps(Interval, Interval)` de `intervals.py`. `Interval` lanza `ValueError` si `start >= end`, y un bloqueo inválido que llegue por error al contexto (D3 no lo revalida) haría explotar la validación del turno. Con la comparación directa, un bloqueo con `inicio >= fin` nunca se solapa con nada: `check_blocks` lo ignora y `appointments_affected_by_block` devuelve vacío, sin excepciones (el mismo criterio que D10 de C-05 con los tramos inválidos).

### D8 — Mensaje de `BLOCKED_TIME` (explore, decisión 5; formato en el propose)

`"El turno de {inicio} a {fin} (hora local) se superpone con el bloqueo {id} del profesional, del {inicio del bloqueo} al {fin del bloqueo} (hora local)."` + `" Motivo: {motivo}."` si `reason` no es `None` ni vacío ni solo espacios (`reason.strip()` vacío; ajuste de la autora en el punto de control 3.5, 2026-10-28). Sin motivo, el mensaje termina en `"(hora local)."` (ajuste de la autora en la revisión del propose, 2026-10-28: el motivo va como oración aparte).

- `{inicio}` y `{fin}` del turno con `format_local_time`.
- Los instantes del bloqueo con una función nueva de `intervals.py`, `format_local_date_time(instant, tz) -> str`, que da `dd/mm/aaaa HH:MM` en la zona recibida (con su test en `test_intervals.py`).
- El id del bloqueo en el mensaje, como los mensajes de solapamiento llevan el id del turno ("Contenido de cada violación").

**Por qué**: el bloqueo puede durar varios días, así que solo la hora sería ambigua; con el año no hay dudas cerca de fin de año. El motivo ("vacaciones", "feriado") es lo que la secretaria necesita para explicar el rechazo. Un `reason` vacío o en blanco se trata como sin motivo para no dejar `" Motivo: ."` ni `" Motivo:    ."`. El motivo que sí se muestra va tal como se cargó (sin `strip`), porque la spec no pide recortarlo.

**Alternativas descartadas**: el formato dentro de `rules/blocks.py` (lo va a usar C-08 para otros mensajes y `intervals.py` ya tiene el formateo de hora local); `dd/mm` sin año.

### D9 — Mensaje de `INVALID_BLOCK` (surgió en el propose)

`"El bloqueo no es válido: el inicio debe ser anterior al fin."`, sin ids en conflicto ni tipo de referencia. `validate_block` no recibe `tz`.

**Por qué**: la spec solo pide decir que el inicio debe ser anterior al fin. El usuario ve en el formulario las fechas que cargó; mostrar las horas obligaría a pasar la zona a una función que no la necesita para decidir. Sigue el estilo de las razones de `INVALID_WORKING_HOURS`.

### D10 — Tests (surgió en el propose)

- Estilo de C-02 a C-05: datos literales, UUIDs fijos en constantes con nombre (`BL1`, `BL2`, `BL3`, `BLV`, `T1` a `T7`), `ZoneInfo` real, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, `@pytest.mark.parametrize` y aserciones sobre la lista completa de códigos y del id del bloqueo.
- `test_validate_new_appointment.py`: `CTX = ScheduleContext(tz=BUENOS_AIRES, working_hours=FULL_WEEK, blocks=())` y `_ctx(*slots)` con `blocks=()`. Para los escenarios nuevos, un helper `_ctx_blocks(*blocks, working_hours=FULL_WEEK)`. Los escenarios se escriben con `_local` y se compara contra el literal UTC donde la spec lo da.
- `test_blocks.py` (nuevo): `validate_block` y `appointments_affected_by_block`.
- `test_model.py`: normalización a UTC, naive → `ValueError` y bloqueo inválido que se construye sin lanzar.
- `test_violations.py`: `BLOCKED_TIME` e `INVALID_BLOCK` en la tabla de valores serializados; `conflicting_block_id` es `None` por defecto.
- `test_intervals.py`: `format_local_date_time`.

**Por qué**: `blocks=()` hace que los bloqueos nunca intervengan en los escenarios viejos. Un helper aparte deja claro qué bloqueos usa cada escenario nuevo.

### D11 — Dos requisitos nuevos para el bloqueo además de la regla (surgió en el propose)

El mensaje de `BLOCKED_TIME` va en su propio requisito ("Mensaje de un turno bloqueado") y los instantes del bloqueo en otro ("Instantes del bloqueo con zona horaria y normalizados a UTC"), en vez de modificar "Contenido de cada violación" e "Instantes con zona horaria y normalizados a UTC".

**Por qué**: es D13 de C-05. Esos dos requisitos son largos y sus escenarios no cambian; un requisito nuevo es más chico de revisar y respeta "un comportamiento por requisito".

### D12 — Escenarios de la spec que no estaban entre los 23 casos del explore (surgió en el propose)

Se suman dos escenarios de mensaje (bloqueo sin motivo; bloqueo de varios días con motivo, que comprueba que el mensaje usa hora local y no UTC). Los 23 casos del explore están todos en la spec; el caso 22 ("no cambia los turnos") queda como un escenario propio.

## Risks / Trade-offs

- [`ScheduleContext` con un campo obligatorio nuevo rompe a los llamadores] → Hoy solo lo construyen los tests de dominio (dos líneas) y el ejemplo de `backend/README.md`; todavía no hay API (C-22).
- [Un bloqueo inválido en el contexto se ignora en silencio] → El bloqueo se valida al cargarlo (`validate_block`, C-21); D3 y D7.
- [`atendido` cuenta como afectado aunque un bloqueo sobre un turno atendido solo puede estar en el pasado] → Da lo mismo en la práctica y deja una sola definición de "activo"; C-07 no impide crear bloqueos en el pasado, y C-21 puede decidir si los permite.
- [La API tiene que componer `validate_block` y `appointments_affected_by_block` en ese orden] → Con un bloqueo inválido la segunda devuelve vacío, así que el orden no puede dar un resultado incorrecto, solo uno incompleto.
- [RN-AG-12 pone "pasado" antes del horario] → No afecta este change; C-07 decide el grupo de `IN_THE_PAST`.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain`, de los tests de dominio y de la documentación (un solo commit del change, a pedido de la autora).

## Decisiones confirmadas por la autora

**Fecha: 2026-10-28.** D1 a D6 en el explore (`docs/evidencias/explore-C-06.md`) y D7 a D12 en la revisión del propose, con un ajuste en D8: el motivo va como oración aparte ("… (hora local). Motivo: vacaciones."). En la misma revisión, la autora pidió alinear KB 04 y el aviso de Q-04 en `AGENTS.md`/`CLAUDE.md` con SU-05 confirmada. El punto de control (tarea 3.5) sigue: la autora revisa el código del modelo antes de las reglas.

## Open Questions

Ninguna que cambie el alcance.

## Desvíos durante el apply

- **Tareas 1.1 a 3.4 (2026-10-28).** Sin desvíos de comportamiento respecto de la spec y el diseño. Desvíos de proceso:
- **Tarea 2.2 (GREEN en dos pasos).** El RED de 2.1 fue un error de colección por los códigos (`AttributeError`), que tapaba el rojo del campo. Se agregaron primero solo los dos códigos, se vieron en rojo los 3 tests de `conflicting_block_id` (`TypeError`/`AttributeError`) y después se agregó el campo.
- **Tarea 3.1 (estilo del test).** `test_model.py` ya usa `timezone(timedelta(hours=-3))` como "Buenos Aires" para los instantes `-03:00`; los tests de `Block` siguen esa convención del archivo, que coincide con el literal `2026-10-20T10:00:00-03:00` de la spec. El test de un bloqueo con inicio posterior al fin también pasa un `reason` para cubrir el campo opcional.
- **Tarea 3.3.** El docstring de `ScheduleContext` ya no anuncia los bloqueos como trabajo futuro: solo queda `now` (C-07).
- **Punto de control 3.5 (aprobado por la autora el 2026-10-28, con un ajuste).** Un motivo con solo espacios (`"   "`) también cuenta como vacío: se actualizó D8, el requisito "Mensaje de un turno bloqueado" y se agregó el escenario "Mensaje de un bloqueo con motivo vacío o en blanco" (su test va en rojo primero, tarea 6.4).
- **Tareas 4.1 a 8.4 (2026-10-28).** Sin cambios de comportamiento respecto de la spec y el diseño, salvo el hallazgo de 8.3. Desvíos de proceso:
- **Tareas 4.3, 5.3 a 5.5, 7.1, 7.2 y 8.3 (pasaron de entrada).** La implementación mínima de cada GREEN ya cubría esos casos. Se comprobó que pueden fallar con mutaciones temporales (`>` en vez de `>=`, grilla de 2 minutos, `<=` en `_overlaps`, sin filtro de profesional o de estado, comparación por fecha UTC, orden invertido, `check_blocks` al final del grupo 2 o en el grupo 1, `Interval` en vez de `_overlaps`) y se restauró el código. El detalle está en cada tarea.
- **Tarea 5.2.** El GREEN mínimo ya incluye el filtro por profesional, como pedía la tarea; 5.4 lo verifica con una mutación.
- **Tarea 5.7 (refactor extra).** El filtro y el orden de `check_blocks` pasaron a un helper privado `_overlapping_blocks`; no cambia la firma pública de D7.
- **Tarea 6.1 (caso extra).** Además de los dos instantes pedidos, `2026-10-21T02:30:00+00:00` → `"20/10/2026 23:30"`: el día local es anterior al de UTC.
- **Tareas 6.3 y 6.4 (GREEN en tres pasos).** Primero el mensaje sin motivo; después el motivo con `if block.reason`, para ver en rojo el caso `"   "` (`... (hora local). Motivo:    .`); al final, el `strip`. Los casos `""` y `"   "` pasaban en el primer paso porque todavía no se mostraba ningún motivo.
- **Tarea 6.5.** El mensaje se arma en el helper privado `_blocked_message`. El motivo que se muestra va tal como se cargó (D8).
- **Tarea 7.1.** Los turnos existentes se pasan como `[F, E]` para que el orden de las violaciones no salga del orden de la lista.
- **Tarea 8.3 (hallazgo del apply que volvió a la spec).** D7 dice que un bloqueo con `inicio >= fin` nunca se solapa: `check_blocks` lo ignora y `appointments_affected_by_block` devuelve vacío, sin excepción. La spec no lo cubría. Se agregaron los escenarios "Bloqueo inválido recibido con la agenda" (requisito "Turno fuera de los bloqueos del profesional") y "Turnos afectados por un bloqueo inválido" (requisito "Turnos afectados por un bloqueo"), con sus tests. Los dos pasaron de entrada; con `Interval` en vez de `_overlaps` (mutación temporal, restaurada) los dos lanzan `ValueError`.
