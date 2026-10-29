# Design

## Context

C-06 dejó `validate_new_appointment(request, references, existing_appointments, context) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`. `_request_validity_violations` (grupo 1: referencias → duración → inicio en la grilla → medianoche) corta si encuentra algo; el inicio se evalúa siempre y la medianoche solo con una duración efectiva válida. `_agenda_conflict_violations` (grupo 2: horario → bloqueo → profesional → sillón) informa todo junto. Los docstrings de los dos grupos dejan abierto dónde va el pasado ("C-07 suma aca o en el grupo 1 la regla del pasado").

`ScheduleContext` (en `model.py`, *frozen* con slots) tiene `tz`, `working_hours` y `blocks`, sin valores por defecto ni `__post_init__`; su docstring anuncia que C-07 suma `now`. `model.py` tiene `_to_utc(field_name, value)`, que normaliza a UTC y lanza `ValueError` con un instante naive. `intervals.py` tiene `format_local_time` (`HH:MM`, o `HH:MM:SS` si hay segundos o microsegundos) y `format_local_date_time` (`dd/mm/aaaa HH:MM`). `ViolationCode` no tiene `IN_THE_PAST` (sí está en el catálogo de KB 07, que ya dice `IN_THE_PAST → 422`).

La guardia de C-01 (`backend/tests/domain/import_guard.py`) tiene `find_forbidden_imports(domain_dir) -> list[ForbiddenImport]` y `format_violations`, con una lista de módulos **permitidos**: `time` no está, así que `import time` y `from time import time` ya se reportan. `datetime` sí está permitido, y por eso falta detectar `datetime.now`, `utcnow`, `today` y `date.today`. Hoy ningún módulo del dominio lee el reloj (`now` solo aparece en docstrings).

En los tests, `CTX` (línea 45), `_ctx(*slots)` (líneas 49-50) y `_ctx_blocks(*blocks, working_hours=FULL_WEEK)` (línea 1230) de `test_validate_new_appointment.py` construyen un `ScheduleContext`, además del ejemplo de `backend/README.md`. Las fechas de esos tests van del 19/10 al 26/10/2026. La suite de C-06 cerró con 273 tests y `mypy --strict app tests` sin errores en 28 archivos.

La motivación está en `proposal.md` y los requisitos en `specs/`. D1 a D5 salen del explore del 2026-10-29 (`docs/evidencias/explore-C-07.md`) y la autora las confirmó. D6 usa los nombres que se propusieron en el explore y la autora no objetó. D7 a D11 surgieron en el propose.

## Goals / Non-Goals

**Goals:**
- Rechazar el turno que empieza antes de `now` con `IN_THE_PAST`, comparando instantes sin tolerancia, y con un mensaje en hora local que no se contradiga a sí mismo.
- Que `now` llegue solo por el contexto, siempre con zona y en UTC, y que un test con `ast` impida que el dominio lea el reloj.
- Que los tests de C-02 a C-06 sigan verificando lo mismo: solo cambia la construcción de los contextos.

**Non-Goals:**
- Detectar el reloj en ejecución (monkeypatch, `freezegun`) o con accesos dinámicos (D4).
- Leer el reloj en el borde (C-22) y reprogramar (C-11).
- Mensajes con nombres (C-08).

## Decisions

### D1 — `IN_THE_PAST` al final del grupo 1, evaluado siempre (explore, decisión 1)

```python
violations += check_start_time(request.start_at, context.tz)
if end_at is not None and not duration_violations:
    violations += check_same_local_day(request.start_at, end_at, context.tz)
violations += check_not_in_the_past(request.start_at, context.now, context.tz)
return violations
```

El orden del grupo 1 queda referencias → duración → inicio en la grilla → medianoche → pasado, y el grupo 1 sigue cortando antes del grupo 2. La regla no tiene guardas: solo usa el inicio y `now`, así que se evalúa aunque no haya duración efectiva o la duración sea inválida. En la API es `422`.

**Por qué**: un turno en el pasado es una propiedad del pedido frente al reloj, no un choque con la agenda; US-005 habla de "errores de carga". Informar solapamientos, horario o bloqueos de un horario que ya pasó es ruido, y el grupo 2 supone un pedido válido (explore de C-05). Respeta el orden de RN-AG-12 (medianoche → pasado → horario).

**Alternativas descartadas**: al principio del grupo 2 (mezclaría un error de carga con conflictos y daría `409`); evaluar el pasado solo con duración válida (no la necesita y se perdería información).

### D2 — Comparación estricta de instantes, sin truncar ni tolerancia (explore, decisión 2)

`start_at < now` → `IN_THE_PAST`; `start_at == now` es válido. Los dos están en UTC (`request.start_at` y `context.now` se normalizan al construirse), así que se comparan directamente. Con `now` 10:00:30, un inicio 10:00 se rechaza; con `now` 13:00:00.000001 UTC, también.

**Por qué**: es literal a RN-AG-06 y US-005 CA-1/CA-2. Truncar `now` al minuto o dar un margen sería una política que la KB no pide. Como todo inicio válido tiene segundos en cero, `start == now` solo se da si `now` también los tiene.

**Alternativas descartadas**: truncar `now` al minuto o al paso de la grilla; una tolerancia de unos segundos para la latencia del formulario.

### D3 — `ScheduleContext.now`, sin valor por defecto y normalizado a UTC (explore, decisión 3)

```python
@dataclass(frozen=True, slots=True)
class ScheduleContext:
    tz: ZoneInfo
    working_hours: tuple[WorkingHours, ...]
    blocks: tuple[Block, ...]
    now: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "now", _to_utc("now", self.now))
```

Naive → `ValueError("now necesita zona horaria (datetime naive)")`; otra zona → el mismo instante en UTC. `now` va al final; ningún campo tiene valor por defecto, así que el orden no obliga a nada.

**Por qué**: es el criterio de `start_at`, de los turnos y de los bloqueos. Una violación no sirve porque `now` no lo carga el usuario, y asumir UTC rompería la regla dura de no usar `datetime` naive. Sin default, mypy marca a cualquier llamador que se olvide de pasarlo (D1 de C-06). La firma de `validate_new_appointment` no cambia (decisión 3 de C-04).

**Alternativas descartadas**: un parámetro `now` suelto en `validate_new_appointment` (vuelve a cambiar la firma); `now: datetime | None = None` con el reloj del sistema como respaldo (rompe RN-GL-04).

### D4 — Guardia del reloj: `find_global_clock_calls`, separada de la de imports (explore, decisión 4)

```python
@dataclass(frozen=True, slots=True)
class GlobalClockCall:
    path: Path
    line: int
    expression: str

def find_global_clock_calls(domain_dir: Path) -> list[GlobalClockCall]
def format_clock_calls(calls: list[GlobalClockCall], base: Path) -> str
```

Por cada archivo, primero se resuelve qué denota cada nombre importado del módulo `datetime` (en todo el árbol, también dentro de funciones):

- `import datetime [as X]` → `X` es el módulo.
- `from datetime import datetime [as Y]` → `Y` es la clase `datetime`.
- `from datetime import date [as Z]` → `Z` es la clase `date`.
- `from datetime import *` → se reporta con la expresión `from datetime import *`.

Después se reporta todo `ast.Attribute` (accedido, no solo llamado) que sea `Y.now`, `Y.utcnow`, `Y.today`, `Z.today`, `X.datetime.now`, `X.datetime.utcnow`, `X.datetime.today` o `X.date.today`. La expresión es `ast.unparse` del atributo (`datetime.now`, `dt.datetime.now`, `D.now`). Los resultados se ordenan por ruta y línea. `format_clock_calls` da una línea por acceso: `"<ruta relativa>:<línea>: reloj global en el dominio: '<expresión>' (usar el now inyectado)"`, como `format_violations`.

`find_forbidden_imports` y `find_global_clock_calls` comparten solo el recorrido de los archivos (un helper privado que devuelve ruta y árbol de cada `.py`, ordenados por ruta); los tests de C-01 no cambian. `time` sigue a cargo de la lista permitida, con tests explícitos (`import time`, `from time import time as t`).

**Por qué**: filtrar por nombre de atributo daría un falso positivo con `context.now`, que es justo lo que agrega este change. Detectarlo en ejecución usa mocks y una dependencia nueva. Una función aparte no toca los tests de C-01 y entra como requisito nuevo de `domain-dependency-guard`. Reportar el acceso y no solo la llamada atrapa `reloj = datetime.now`.

**Límites documentados** (en el docstring y en la spec; confirmados por la autora): no detecta `getattr(datetime, "now")` ni reasignaciones como `d = datetime; d.now()`; un parámetro llamado `datetime` en un archivo que importa la clase daría un falso positivo, aceptable porque sombrear `datetime` también es un defecto. Los bindings son por archivo, no por ámbito.

**Alternativas descartadas**: sumar `datetime.now` a `find_forbidden_imports` (mezcla dos preguntas y cambia los tests de C-01); buscar el texto `datetime.now` (lo encuentra en docstrings y no ve los alias).

### D5 — Los helpers de contexto de los tests pasan un `now` fijo anterior (explore, decisión 5)

`CTX`, `_ctx(*slots)` y `_ctx_blocks(...)` pasan `now=datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)`, como constante con nombre `EARLY_NOW`. No cambia ninguna llamada ni aserción.

**Por qué**: es anterior a todas las fechas de los tests (19/10 a 26/10/2026), así que el pasado nunca interviene en los escenarios viejos, y no depende de la fecha real en que se corre la suite. El explore nombraba `CTX` y `_ctx`; `_ctx_blocks` (de C-06) también construye un contexto y se migra igual (surgió en el propose).

### D6 — `rules/past.py` con `check_not_in_the_past` (nombres del explore)

```python
def check_not_in_the_past(start_at: datetime, now: datetime, tz: ZoneInfo) -> list[Violation]
```

Devuelve `[]` o una sola `IN_THE_PAST`, sin `conflicting_appointment_id`, `conflicting_block_id` ni `reference_kind`. `IN_THE_PAST` se suma a `ViolationCode` (valor igual al nombre). `tz` es solo para el mensaje.

**Por qué**: un módulo por regla, como `rules/start_time.py`; recibe los instantes y la zona, no el contexto, igual que `check_start_time` y `check_working_hours`, así que se prueba sin construir un contexto.

### D7 — Mensaje de `IN_THE_PAST` (explore, decisión 2; texto en el propose)

`"El inicio del turno ({inicio}, hora local) es anterior al momento actual ({now}, hora local): no se pueden dar turnos en el pasado."`

- `{inicio}` con `format_local_date_time` (`dd/mm/aaaa HH:MM`), que ya existe.
- `{now}` con una función nueva de `intervals.py`, `format_local_date_time_with_seconds(instant, tz) -> str`, que da `dd/mm/aaaa HH:MM:SS` en la zona recibida, sin microsegundos (con su test en `test_intervals.py`).

Como `now` siempre lleva segundos, se modifica "Contenido de cada violación" para exceptuarlo del formato general de horas (`HH:MM`, o `HH:MM:SS` solo con segundos distintos de cero).

**Por qué**: la fecha evita ambigüedad cerca de la medianoche (el caso 8 es del día 20 local y del 21 en UTC). Los segundos de `now` evitan leer "10:00 es anterior a 10:00" en el caso 4. Sigue el estilo "(se recibió {hora}, hora local)" de `INVALID_START_TIME`. El texto final, con nombres, es de C-08.

**Alternativas descartadas**: `now` con el formato general (`HH:MM` si los segundos son cero), que no exigiría modificar "Contenido de cada violación" pero no es lo que pidió la autora; mostrar el inicio con segundos (un inicio con segundos ya lo informa `INVALID_START_TIME`).

### D8 — Tests (surgió en el propose)

- Estilo de C-02 a C-06: datos literales, `ZoneInfo` real, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, `@pytest.mark.parametrize` y aserciones sobre la lista completa de códigos.
- `test_past.py` (nuevo): `check_not_in_the_past` directo (antes, igual, después, segundos, microsegundo y el mensaje).
- `test_validate_new_appointment.py`: los 14 casos de la regla y del orden con un helper `_ctx_now(now, working_hours=FULL_WEEK)`; `now` con `_local(...)` y los literales UTC de la spec donde la spec los da.
- `test_model.py`: los casos 15 a 17 (`now` en `-03:00`, en `+01:00` y naive).
- `test_violations.py`: `IN_THE_PAST` en la tabla de valores serializados. `test_intervals.py`: `format_local_date_time_with_seconds`.
- `test_clock_guard.py` (nuevo): la guardia del reloj sobre módulos escritos en `tmp_path`, con el helper `_write_module` del estilo de `test_import_guard.py`. `test_domain_dependencies.py`: un test nuevo que aplica `find_global_clock_calls` al `app/domain` real.

**Por qué**: `test_import_guard.py` es de C-01 y no cambia; un archivo aparte deja claro qué cubre cada guardia.

### D9 — Requisitos de la spec (surgió en el propose)

En `appointment-scheduling`: tres requisitos nuevos (la regla, su mensaje y `now` en el contexto) en vez de ampliar "Instantes con zona horaria y normalizados a UTC" o "Contenido de cada violación" con escenarios nuevos (D11 de C-06). Los casos 1 a 8 del explore van en "Turno que no empieza en el pasado"; los 9 a 14 (combinaciones con el grupo 1 y el corte) en "Todas las violaciones, en orden estable"; los 15 a 17 en "Momento actual inyectado en el contexto". Se modifican "Alta de un turno válido" (la condición y el `now` por defecto de los escenarios), "Todas las violaciones, en orden estable" y "Contenido de cada violación" (D7). Se suman tres escenarios de mensaje que no estaban entre los 17 casos (casos 1, 4 y 8 con el texto exacto).

### D10 — Recorrido compartido de los archivos del dominio (surgió en el propose)

Un helper privado `_parse_domain_files(domain_dir) -> list[tuple[Path, ast.Module]]` con el `sorted(rglob("*.py"))` y el `ast.parse`, usado por las dos funciones. Es un refactor de `find_forbidden_imports` sin cambio de comportamiento; sus tests de C-01 tienen que seguir en verde sin tocarlos.

### D11 — Orden de los accesos reportados (surgió en el propose)

Ordenados por `(ruta, línea, columna)`. `ast.walk` recorre en anchura, no por línea, así que sin ordenar el reporte de un archivo con varios accesos no sería estable.

## Risks / Trade-offs

- [`ScheduleContext` con un campo obligatorio nuevo rompe a los llamadores] → Hoy solo lo construyen los tres helpers de los tests y el ejemplo de `backend/README.md`; todavía no hay API (C-22).
- [Con `now` a 13:00:00.000001 UTC el mensaje dice "10:00" y "10:00:00"] → Los microsegundos no se muestran (como en el resto de los mensajes); un `now` así solo llega por programa, nunca desde el formulario, y el rechazo es correcto.
- [Un test nuevo que olvide fijar `now` usa `EARLY_NOW` y no ve el pasado] → Los escenarios del pasado usan `_ctx_now` con su `now` explícito.
- [La guardia no ve `getattr(datetime, "now")` ni reasignaciones] → Límite documentado (D4); la revisión de código y la regla dura cubren el resto.
- [Falso positivo con un parámetro llamado `datetime`] → Aceptable: sombrear `datetime` también es un defecto; se renombra el parámetro.
- [La API (C-22) tiene que leer el reloj real] → Lo hace en el borde, fuera de `app/domain`, con `datetime.now(timezone.utc)`; la guardia solo mira el dominio.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain`, de los tests de dominio y de la documentación (un solo commit del change, a pedido de la autora).

## Decisiones confirmadas por la autora

**Fecha: 2026-10-29.** D1 a D5 en el explore (`docs/evidencias/explore-C-07.md`), incluidos los límites de la guardia de D4. Los nombres de D6 (`rules/past.py`, `check_not_in_the_past`, `IN_THE_PAST`) se propusieron en el explore y la autora no los objetó. D7 a D11 surgieron en el propose y quedan para la revisión de la autora (en la revisión del propose o, a más tardar, en el punto de control de la tarea 5.3).

## Open Questions

Ninguna que cambie el alcance.
