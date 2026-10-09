# Design

## Context

C-01 dejó `backend/` instalable, con pytest 8, `mypy --strict` (objetivo 3.12, sobre `app` y `tests`), el paquete vacío `backend/app/domain/__init__.py` y la guardia de dependencias (`backend/tests/domain/import_guard.py`). La allowlist de esa guardia (`__future__`, `collections`, `dataclasses`, `datetime`, `enum`, `typing`, `zoneinfo`, `tzdata`) excluyó `uuid` a propósito, con la condición de que lo agregue el change que lo necesite (C-01 design D5, decisión 2 de la autora). Las pruebas se corren desde `backend/` con el venv local (Python 3.13). La motivación está en `proposal.md` y los requisitos en `specs/appointment-scheduling/spec.md` y `specs/domain-dependency-guard/spec.md`.

Las decisiones 1 a 7 de la sección Decisions fueron confirmadas por la autora en el explore. Las que están marcadas como "a revisar en el punto de control" las tomó el propose y se revisan en la tarea ⛔ de `tasks.md`.

## Goals / Non-Goals

**Goals:**
- Una API pública chica y tipada (`validate_new_appointment` más los tipos del modelo y del resultado) que C-03 a C-08 puedan extender agregando reglas en `rules/` sin cambiar su forma.
- Reglas deterministas: el resultado depende solo de los argumentos (sin reloj, sin generar ids, sin depender del orden de la lista recibida).
- Que cada escenario del spec tenga un test de pytest sobre la API pública, con datos literales.

**Non-Goals:**
- Recibir `now`: ninguna regla de C-02 lo usa. Se agrega en C-07 (`no-turnos-en-el-pasado`). No se agrega un parámetro sin uso.
- Un contexto completo (horarios, bloqueos, catálogos): cada change agrega lo que necesita.
- Mensajes finales: en C-02 los mensajes son mínimos y C-08 los reemplaza.
- `exclude_id` y la reprogramación: van en C-11.

## Decisions

### D1 — Estructura de módulos

```
backend/app/domain/
├── __init__.py                 # vacío (sin re-exports, igual que en C-01)
├── model.py                    # AppointmentStatus, Service, Appointment, NewAppointmentRequest
├── violations.py               # ViolationCode, Violation, Ok, Rejected, ValidationResult
├── intervals.py                # Interval, overlaps
├── rules/
│   ├── __init__.py
│   ├── duration.py             # check_positive_duration
│   └── overlap.py              # OCCUPYING_STATUSES, check_professional_overlap, check_chair_overlap
└── appointment/
    ├── __init__.py             # re-exporta validate_new_appointment
    └── validate.py             # validate_new_appointment
backend/tests/domain/
├── test_model.py               # invariantes de instantes y de Appointment
├── test_violations.py          # invariante de Rejected
├── test_intervals.py           # semiabierto: overlaps
└── test_validate_new_appointment.py   # escenarios del spec por la API pública
```

Sigue el árbol de KB 08 (§Estructura de directorios: `rules/` con una regla por módulo y `appointment/` con `validate_new_appointment`). C-03 amplía `rules/duration.py` (múltiplo de 5, máximo 480). Por eso la regla mínima se llama `duration.py` y no `positive_duration.py`.

### D2 — Ids `uuid.UUID` inyectados; `uuid` entra en la allowlist (decisión 1)

Todos los ids (turno, paciente, profesional, sillón, prestación) son `uuid.UUID`, como las PK de KB 04. El id del turno nuevo lo genera el llamador (la capa de aplicación, en C-22/C-23) y llega en el pedido. **El dominio usa `UUID` solo como tipo y nunca llama a `uuid4()` ni a otra función que genere ids**, por la misma razón por la que `now` se inyecta: si el dominio generara ids, el resultado no sería determinista y los tests no podrían comparar el turno devuelto con un valor literal.

Por eso se agrega `"uuid"` a `DOMAIN_ALLOWED_MODULES`. `uuid` es biblioteca estándar y su uso como tipo no hace I/O. La guardia no puede impedir que alguien llame a `uuid4()`, porque mira imports y no llamadas. Esa disciplina se deja escrita en el docstring de `model.py` y se controla en la revisión. **Alternativa descartada**: `NewType("AppointmentId", str)` sin `uuid`. Evita tocar la allowlist, pero el dominio aceptaría cualquier texto como id y la conversión pasaría a otra capa sin que los tipos lo garanticen.

### D3 — Modelo (`model.py`)

Todas las clases son `@dataclass(frozen=True, slots=True)`.

```python
class AppointmentStatus(Enum):
    RESERVED = "reservado"; CONFIRMED = "confirmado"; ATTENDED = "atendido"
    NO_SHOW = "ausente";   CANCELLED = "cancelado"

class Service:           id: UUID; default_duration_min: int
class Appointment:       id: UUID; patient_id: UUID; professional_id: UUID; chair_id: UUID
                         service_id: UUID; start_at: datetime; end_at: datetime; status: AppointmentStatus
class NewAppointmentRequest:
                         id: UUID; patient_id: UUID; professional_id: UUID; chair_id: UUID
                         start_at: datetime; duration_min: int | None = None
```

- Los nombres de los miembros del Enum están en inglés (convención de identificadores) y los valores son los estados en español de KB 04 (el `CHECK` de la columna `status`).
- `Service` no valida `default_duration_min` (decisión 7: `INVALID_DURATION` se decide en un solo lugar, `rules/duration.py`). Tampoco tiene `name` ni `active`: no los usa ninguna regla de C-02, los suma C-03 (referencias) o C-08 (mensajes).
- El pedido no lleva `service_id`. La prestación llega como argumento `service` y el turno devuelto usa `service.id`, así no puede haber dos fuentes de verdad que no coincidan. **A revisar en el punto de control.**

### D4 — Invariantes de los instantes (decisión 5)

Una función privada `_to_utc(field_name: str, value: datetime) -> datetime` en `model.py`:
- si `value.tzinfo is None or value.utcoffset() is None` → `ValueError(f"{field_name} necesita zona horaria (datetime naive)")`;
- si no, devuelve `value.astimezone(timezone.utc)`.

`Appointment.__post_init__` y `NewAppointmentRequest.__post_init__` la aplican a cada instante y reasignan el valor con `object.__setattr__` (la dataclass es *frozen*). Es un error de programación del llamador, no una regla de negocio: por eso es una excepción y no una `Violation`. La API valida `datetime` con zona antes de llegar al dominio (C-22), así que este caso no debería ocurrir en producción.

Invariante adicional de `Appointment`: `start_at < end_at`, o `ValueError`. Es el `CHECK` de KB 04 y hace que todo turno ya construido tenga un intervalo válido. No choca con la decisión 7, porque `validate_new_appointment` decide `INVALID_DURATION` **antes** de construir el `Appointment` (D7). **A revisar en el punto de control.**

### D5 — Violaciones y resultado (`violations.py`, decisión 6)

```python
class ViolationCode(Enum):
    PROFESSIONAL_OVERLAP = "PROFESSIONAL_OVERLAP"; CHAIR_OVERLAP = "CHAIR_OVERLAP"
    INVALID_DURATION = "INVALID_DURATION"

class Violation:  code: ViolationCode; message: str; conflicting_appointment_id: UUID | None = None
class Ok:         appointment: Appointment
class Rejected:   violations: tuple[Violation, ...]     # __post_init__: vacío → ValueError
ValidationResult: TypeAlias = Ok | Rejected
```

- Un resultado con clases discriminadas (no un `bool` con una lista) permite usar `match result: case Ok(appointment): … case Rejected(violations): …` y que mypy verifique que se cubrieron todos los casos con `assert_never`. Se usa `tuple` y no `list` para que el resultado sea inmutable de verdad.
- `Rejected` sin violaciones sería un estado imposible, así que el constructor lo rechaza con `ValueError`.
- El valor de cada código es su nombre: es el código estable que expondrá la API (C-22).
- Mensajes mínimos (C-08 los reemplaza por el texto con nombres y rango local):
  - `PROFESSIONAL_OVERLAP`: `"El profesional ya tiene un turno que se superpone (turno {id})."`
  - `CHAIR_OVERLAP`: `"El sillón ya está ocupado por un turno que se superpone (turno {id})."`
  - `INVALID_DURATION`: `"La duración del turno debe ser mayor que cero minutos (se recibió {n})."`
- **Alternativa descartada**: excepciones de dominio (`OverlapError`). Cortan en la primera violación, en contra de DD-08, y la regla dura del proyecto las prohíbe para reglas de negocio.

### D6 — Intervalos (`intervals.py`)

`Interval(start: datetime, end: datetime)` *frozen*, con `start < end` como invariante, y `overlaps(a: Interval, b: Interval) -> bool` que devuelve `a.start < b.end and b.start < a.end` (semiabierto, DD-07). Que un intervalo termine cuando empieza otro **no** es solapamiento, porque las comparaciones son estrictas. `Appointment` expone la propiedad `interval`. `Interval` no valida la zona: le llegan instantes ya normalizados por el modelo. C-04 agrega en este módulo la conversión a hora local.

### D7 — Algoritmo de `validate_new_appointment` (decisiones 3, 4 y 7)

```python
def validate_new_appointment(
    request: NewAppointmentRequest,
    service: Service,
    existing_appointments: Sequence[Appointment],
) -> ValidationResult
```

1. `duration = request.duration_min if request.duration_min is not None else service.default_duration_min`.
2. `duration_violations = check_positive_duration(duration)`. Si no está vacía, se devuelve `Rejected(duration_violations)` **sin evaluar solapamientos**: un intervalo con `fin <= inicio` no existe. Es la única excepción a DD-08 ("devolver todas"), escrita así en el spec. Cuando C-03 a C-07 agreguen reglas que no dependen del intervalo (referencias, pasado), esas sí se acumulan junto con `INVALID_DURATION`. Lo único que queda condicionado a una duración válida es lo que necesita el intervalo.
3. Se arma el candidato `Appointment(..., start_at=request.start_at, end_at=request.start_at + timedelta(minutes=duration), status=AppointmentStatus.RESERVED, service_id=service.id)`.
4. `violations = check_professional_overlap(candidate, existing) + check_chair_overlap(candidate, existing)`: primero todas las de profesional y después todas las de sillón (RN-AG-12).
5. Sin violaciones → `Ok(candidate)`; con violaciones → `Rejected(tuple(violations))`.

Cada regla de solapamiento **filtra por su cuenta** (decisión 4): se queda con los turnos con el mismo `professional_id` (o `chair_id`) cuyo `status` está en `OCCUPYING_STATUSES = frozenset({RESERVED, CONFIRMED, ATTENDED})` (RN-AG-08, SU-07: una sola constante) y que cumplen `overlaps(candidate.interval, existing.interval)`. Los ordena por `(start_at, str(id))`, donde el id solo desempata dos turnos con el mismo inicio para que el orden no dependa de la lista recibida, y devuelve una `Violation` por cada uno (decisión 2). Un mismo turno existente puede aparecer en las dos listas (US-003 CA-2).

La lista de turnos existentes llega sin filtrar. El llamador puede reducirla por eficiencia (consulta por profesional, sillón y rango en C-23), pero la corrección no depende de eso.

**Alternativa descartada**: una sola pasada que intercale las violaciones por turno. Rompe el orden por prioridad de RN-AG-12 (todas las de profesional antes que las de sillón).

### D8 — Tests

- Un archivo de tests por la API pública (`test_validate_new_appointment.py`) donde cada escenario del spec es un test o un caso de `@pytest.mark.parametrize`. Los datos son literales: UUIDs fijos como `UUID("00000000-0000-0000-0000-0000000000a1")` en constantes con nombre (`P1`, `S1`, `APPT_A`, …) y el día 2026-10-20 en UTC. No hay mocks, `patch`, `monkeypatch` ni `freezegun`.
- Para construir los datos se usan funciones de fábrica tipadas dentro del archivo de test (`_existing(id, professional, chair, start, end, status=RESERVED)`, `_request(...)`). No son *fixtures* con estado.
- Las aserciones comparan códigos, ids y el orden completo (`[(v.code, v.conflicting_appointment_id) for v in violations] == [...]`), nunca solo la cantidad. `pytest.raises(ValueError)` se usa solo para los instantes *naive*, `Rejected(())` y `start_at >= end_at`.
- `test_intervals.py` triangula `overlaps` con una tabla (contiene, contenido, cruce por izquierda, cruce por derecha, igual, consecutivo por izquierda, consecutivo por derecha, disjunto).

## Decisiones confirmadas por la autora

**Fecha: 2026-10-08.** La autora revisó el propose y aceptó las decisiones que había tomado el propose:

1. **Pedido sin `service_id`** (D3): `NewAppointmentRequest` no lleva `service_id`. La prestación llega como argumento `service` y el turno devuelto usa `service.id`.
2. **`ValueError` si `start_at >= end_at`** (D4): es una invariante de `Appointment`. No choca con la decisión 7, porque `INVALID_DURATION` se decide antes de construir el turno (D7).

También aceptó estas elecciones menores:

- `now` no es parámetro de `validate_new_appointment` en C-02. Se agrega en C-07 (Non-Goals).
- Firma pública: `validate_new_appointment(request, service, existing_appointments) -> Ok | Rejected`, en `app/domain/appointment/validate.py` (D7).
- Los miembros del Enum `AppointmentStatus` se nombran en inglés y sus valores son los estados en español (`NO_SHOW = "ausente"`) (D3).
- Si dos turnos en conflicto empiezan a la misma hora, se ordenan por `(start_at, str(id))`, así el resultado no depende del orden de la lista (D7).
- Las convenciones de los escenarios (fecha fija y nombres `P1`, `S1`, `A`) quedan en el Purpose del spec, así sobreviven al archivado.

## Risks / Trade-offs

- [Alguien llama a `uuid4()` en el dominio y la guardia no lo detecta, porque solo mira imports] → Queda escrito en el docstring de `model.py` y en este diseño. C-07 evaluará detectar llamadas prohibidas (ya tiene registrada la idea para `datetime.now()`) y puede sumar `uuid.uuid*`.
- [Cortar en `INVALID_DURATION` oculta conflictos de agenda] → La secretaria ve igual el error que tiene que corregir primero. Al corregir la duración recibe los solapamientos. El intervalo inválido no permite otra cosa.
- [Mensajes mínimos poco útiles para el usuario final] → Solo los consume la suite hasta C-08. El id ya permite identificar el turno.
- [Recorrer toda la lista de turnos es O(n)] → n es la agenda de un consultorio chico, y el llamador puede prefiltrar (C-23). No se optimiza.
- [Dos turnos existentes que ya se solapan entre sí (datos inconsistentes)] → Se informa una violación por cada uno. El dominio no repara datos previos.
- [`Service` sin validar `default_duration_min`] → Es deliberado (decisión 7). La restricción de la base de datos (KB 04) la suma C-14, y el dominio la cubre igual con `INVALID_DURATION`.

## Migration Plan

No aplica: código nuevo sin datos. Rollback: borrar los módulos nuevos de `app/domain` y sus tests, y quitar `uuid` de la allowlist.

## Open Questions

Ninguna que cambie el alcance. Lo marcado como "a revisar en el punto de control" (D3: el pedido sin `service_id`; D4: la invariante `start_at < end_at`) se confirma o se ajusta en la tarea ⛔ antes de implementar las reglas.
