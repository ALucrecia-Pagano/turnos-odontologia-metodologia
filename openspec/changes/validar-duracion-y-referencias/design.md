# Design

## Context

C-02 dejó `validate_new_appointment(request, service, existing_appointments) -> Ok | Rejected` en `backend/app/domain/appointment/validate.py`. El orden actual es: calcula la duración efectiva (explícita o de la prestación), llama a `check_positive_duration` y, si hay violación, devuelve `Rejected` sin evaluar solapamientos (un test de C-02, "Duración inválida en un horario ocupado", depende de ese corte). Después arma el `Appointment` candidato con `service_id=service.id` y suma las violaciones de profesional y de sillón.

Estado del modelo: `Service(id, default_duration_min)` sin `active`; no existen `Professional`, `Chair` ni `Patient`; `NewAppointmentRequest` no tiene `service_id`. `ViolationCode` tiene `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` e `INVALID_DURATION`, y `Violation(code, message, conflicting_appointment_id=None)`. La allowlist del dominio ya incluye `uuid`, `dataclasses`, `enum` y `typing`, así que este change no la toca.

La motivación está en `proposal.md` y los requisitos en `specs/appointment-scheduling/spec.md`. Las decisiones D1 a D7 salen del explore del 2026-10-22 (`docs/evidencias/explore-C-03.md`). D8, D9 y D10 surgieron en el propose, no en el explore. La autora confirmó las diez el 2026-10-22.

## Goals / Non-Goals

**Goals:**
- Que RN-AG-09 y RN-AG-11 se decidan solo en el dominio, sin que la API tenga que pre-validar nada.
- Una firma que C-04 a C-07 puedan extender (horarios, bloqueos, `now`) sin volver a romper a los llamadores en cada change.
- Que los tests de C-02 sigan verificando lo mismo: solo cambia cómo se llama a la función.

**Non-Goals:**
- Un contexto completo con horarios, bloqueos y `now`: cada change suma lo suyo.
- Nombres de profesional, sillón o prestación en los mensajes (C-08) y modelos completos de catálogo (C-09).
- Traducir los grupos a `422` / `409` (C-22) y cargar las entidades desde la base (C-23).

## Decisions

### D1 — Quien llama resuelve cada referencia y le pasa al dominio la entidad o `None`

La capa de aplicación busca por id el paciente, el profesional, el sillón y la prestación (con un `get_by_id` del repositorio) y le pasa al dominio lo que encontró, o `None` si no existe. El dominio decide: `None` → `UNKNOWN_REFERENCE`; `active=False` → `INACTIVE_REFERENCE`. El pedido suma `service_id`, porque ahora la prestación puede no existir y su id tiene que venir de algún lado.

**Por qué**: coincide con el Flujo 1 de KB 07 (la API carga el contexto y el dominio decide). El repositorio no tiene lógica de negocio, la regla vive en un solo lugar y los tests usan datos literales (`None` o una entidad con `active=False`), sin mocks.

La forma concreta de la firma está en D8 y la verificación de que los ids coinciden, en D9.

**Alternativas descartadas**:
- *Dominio con un puerto de repositorio (`Protocol` con `get_professional(id)`)*: los tests necesitarían dobles del puerto y el dominio pasaría a "consultar", lo que acerca el I/O a `app/domain`.
- *La API valida las referencias y el dominio recibe siempre entidades*: es lo que hacía C-02 y duplica RN-AG-11 fuera del dominio, en contra de la regla dura.

### D2 — Modelos mínimos en C-03

En `model.py`, todos `@dataclass(frozen=True, slots=True)`:

```python
class Professional: id: UUID; active: bool
class Chair:        id: UUID; active: bool
class Patient:      id: UUID
class Service:      id: UUID; default_duration_min: int; active: bool = True
class NewAppointmentRequest:
    id: UUID; patient_id: UUID; professional_id: UUID; chair_id: UUID; service_id: UUID
    start_at: datetime; duration_min: int | None = None
```

**Por qué**: solo entran los campos que usa una regla de este change. `Service.active` tiene valor por defecto `True` para que las construcciones de `Service` en los tests de C-02 no cambien. `Professional` y `Chair` no tienen valor por defecto en `active` (D10). `Patient` no tiene `active` porque RN-AG-11 solo pide que exista. C-09 agrega nombres, DNI y sus validaciones. `service_id` va antes de `start_at` para mantener juntos los ids y dejar `duration_min` (con default) al final.

**Alternativa descartada**: esperar a C-09 para crear los modelos y usar `bool | None` sueltos. Sería un modelo provisorio que C-09 tendría que reemplazar entero, y los tests de C-03 quedarían escritos contra tipos que van a desaparecer.

### D3 — Dos grupos de violaciones

`validate_new_appointment` sigue estos pasos:

1. `_check_reference_ids(request, references)` → `ValueError` si algún id no coincide (D9).
2. **Grupo 1, validez del pedido**:
   - `violations = check_references(request, references)` (nuevo `rules/references.py`).
   - Duración efectiva: `request.duration_min` si no es `None`; si no, `references.service.default_duration_min` si la prestación no es `None`; si no, **no hay duración** y no se valida.
   - Si hay duración efectiva: `violations += check_duration(duration)`.
   - Si `violations` no está vacía → `Rejected(tuple(violations))`.
3. **Grupo 2, conflictos de agenda**: se arma el candidato (con `service_id=request.service_id`) y se suman las violaciones de profesional y de sillón, como en C-02. En C-05 a C-07 se agregan acá horario laboral, bloqueos y pasado.

Casos borde: una prestación **inactiva** igual aporta su duración por defecto, así que se valida (puede dar `INACTIVE_REFERENCE` + `INVALID_DURATION`). Una prestación **inexistente** sin duración explícita no da `INVALID_DURATION`: no hay nada que validar, y el error útil ya está en `UNKNOWN_REFERENCE`.

**Por qué**: muestra de una vez todo lo que está mal en el formulario (RN-AG-12, DD-08), mantiene el corte de C-02 (sin un pedido válido no tiene sentido buscar conflictos) y separa limpio los dos tipos de respuesta: el grupo 1 se traduce a `422` y el grupo 2 a `409` (C-22), y un resultado nunca mezcla los dos. Cuando C-07 agregue "en el pasado", decide en su propose a qué grupo pertenece.

**Alternativas descartadas**:
- *Acumular todo en una sola lista*: un pedido con un sillón inexistente informaría además solapamientos sobre un sillón que no existe, y la API no sabría si responder `409` o `422`.
- *Cortar en la primera violación de referencia*: obliga al usuario a corregir de a un error por vez, en contra de DD-08.

### D4 — `reference_kind` opcional en `Violation`

En `violations.py`:

```python
class ReferenceKind(Enum):
    PATIENT = "PATIENT"; PROFESSIONAL = "PROFESSIONAL"; CHAIR = "CHAIR"; SERVICE = "SERVICE"

class ViolationCode(Enum):
    ...  # los tres de C-02
    UNKNOWN_REFERENCE = "UNKNOWN_REFERENCE"; INACTIVE_REFERENCE = "INACTIVE_REFERENCE"

class Violation:
    code: ViolationCode; message: str
    conflicting_appointment_id: UUID | None = None
    reference_kind: ReferenceKind | None = None
```

Como en `ViolationCode`, el valor de cada miembro es su nombre: es lo que expondrá la API. Las violaciones que no son de referencias dejan `reference_kind=None`.

**Por qué**: el frontend tiene que marcar el campo del formulario que falló sin interpretar el texto del mensaje, que además cambia en C-08. Al ser opcional y al final, no rompe ninguna construcción de `Violation` de C-02.

**Alternativas descartadas**:
- *Un código por referencia (`UNKNOWN_PROFESSIONAL`, `INACTIVE_CHAIR`, …)*: siete códigos en vez de dos, y KB 05/07 ya fijan `UNKNOWN_REFERENCE` / `INACTIVE_REFERENCE` como catálogo.
- *Un campo genérico `field: str`*: texto libre sin tipo; mypy no protege los valores.

### D5 — Una sola `INVALID_DURATION` aunque se rompan varias condiciones

`rules/duration.py` reemplaza `check_positive_duration` por `check_duration(duration_min: int) -> list[Violation]` y define las constantes del módulo:

```python
DURATION_STEP_MIN: Final = 5
MAX_DURATION_MIN: Final = 480
```

Reúne las razones incumplidas y, si hay alguna, devuelve **una** violación cuyo mensaje las nombra todas:

- Si `duration_min <= 0`: solo la razón "debe ser mayor que cero minutos". El múltiplo de 5 no aporta nada para un valor no positivo (0 y -15 ya son múltiplos de 5).
- Si no: "debe ser múltiplo de 5 minutos" si `duration_min % DURATION_STEP_MIN != 0`, y "no puede superar los 480 minutos" si `duration_min > MAX_DURATION_MIN`.
- Mensaje: `"La duración del turno no es válida (se recibió {n} minutos): {razones unidas con ' y '}."`. Ejemplo para 487: `"La duración del turno no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos."`. Sigue conteniendo el valor recibido, como pide el escenario de C-02 con -15.

**Por qué**: el código describe el campo inválido, no cada subregla, y dos violaciones iguales se verían repetidas en el formulario. Los límites son constantes del módulo porque SU-02 dice "constante configurable": si el catálogo real necesita otro máximo, se cambia en un solo lugar.

**Alternativa descartada**: una violación por condición. Duplica el código en la respuesta y obliga al frontend a deduplicar.

### D6 — El inicio en la grilla de 5 minutos queda fuera (va a C-04)

RN-DI-05 pide que inicio **y** duración sean múltiplos de 5. C-03 implementa solo la duración. El inicio se evalúa en hora local (los minutos de un instante dependen de la zona en offsets no enteros), y la conversión a hora local vive en C-04, que ya tiene ese punto en su scope de `CHANGES.md`. El código de violación del inicio lo define C-04.

**Por qué**: C-03 no crece y no se implementa una regla de hora local sin la infraestructura de zona horaria.

**Alternativa descartada**: validar `start_at.minute % 5` en UTC. Coincide con Buenos Aires hoy (offset entero), pero dejaría una regla de hora local escrita sobre UTC, que es justo lo que DD-07 y la regla dura de zona horaria evitan.

### D7 — Orden de las violaciones del grupo 1

`check_references` evalúa en este orden fijo: paciente, profesional, sillón, prestación (el orden de los campos de `POST /api/appointments` en KB 07 y de `AppointmentReferences`). Dentro del grupo 1 van primero todas las de referencias y después la de duración (RN-AG-12: referencias → duración).

Mensajes mínimos (C-08 los reemplaza por textos con nombres), con el id de la referencia para que se pueda identificar:

| Tipo | `UNKNOWN_REFERENCE` | `INACTIVE_REFERENCE` |
|---|---|---|
| `PATIENT` | `"El paciente indicado no existe (id {id})."` | — |
| `PROFESSIONAL` | `"El profesional indicado no existe (id {id})."` | `"El profesional indicado está inactivo (id {id})."` |
| `CHAIR` | `"El sillón indicado no existe (id {id})."` | `"El sillón indicado está inactivo (id {id})."` |
| `SERVICE` | `"La prestación indicada no existe (id {id})."` | `"La prestación indicada está inactiva (id {id})."` |

El id que se informa es el del pedido (para `UNKNOWN_REFERENCE` no hay entidad).

**Por qué**: un orden estable que no depende de nada externo es fácil de testear con una igualdad de listas, y coincide con el orden visual del formulario.

**Alternativa descartada**: ordenar por gravedad (inexistentes antes que inactivas). Agrega una regla de orden más sin beneficio claro para el usuario, que ve todos los errores juntos.

### D8 — Las referencias van juntas en `AppointmentReferences` (surgió en el propose)

En `model.py` y `appointment/validate.py`:

```python
@dataclass(frozen=True, slots=True)
class AppointmentReferences:
    patient: Patient | None
    professional: Professional | None
    chair: Chair | None
    service: Service | None

def validate_new_appointment(
    request: NewAppointmentRequest,
    references: AppointmentReferences,
    existing_appointments: Sequence[Appointment],
) -> ValidationResult
```

- Los campos no tienen valor por defecto, así el llamador no puede olvidarse una referencia sin que mypy lo marque.
- El turno devuelto toma `service_id` del pedido (`request.service_id`), no de la entidad.
- Los tests de C-02 cambian solo la forma de llamar a la función; sus aserciones quedan iguales.

**Por qué**: las cuatro referencias van juntas en un objeto con nombre. Así la firma no crece de 3 a 6 argumentos, y el orden de los campos es el mismo en que se informan las violaciones (D7). Esto lo decidió el propose, porque el explore (D1) definió qué recibe el dominio pero no la forma de la firma.

**Alternativas descartadas**:
- *Cuatro parámetros sueltos*: la firma queda larga y es fácil pasar los argumentos en otro orden. Los cuatro son `X | None`, así que mypy no se da cuenta si alguien pone `None` en la posición equivocada.
- *Un `AppointmentContext` con todo (referencias, horarios, bloqueos, `now`) desde ya*: agrega campos que ninguna regla usa todavía. C-05 a C-07 pueden sumar sus parámetros o envolver `AppointmentReferences` en un contexto mayor cuando los necesiten.

### D9 — Ids que no coinciden: `ValueError` (surgió en el propose)

Si una entidad recibida no es `None` y su `id` no coincide con el id del pedido (por ejemplo, `references.service.id != request.service_id`), `validate_new_appointment` lanza `ValueError`.

**Por qué**: es un error de programación del llamador, que cargó la entidad equivocada, y no una regla de negocio. Es el mismo criterio que el `datetime` sin zona de C-02. Sin esta verificación, una prestación equivocada aportaría en silencio una duración por defecto equivocada. Cuesta una función privada y un test parametrizado.

**Alternativa descartada**: no verificar y confiar en el llamador. El error aparecería como un turno con una duración rara, lejos de su causa.

### D10 — `Professional.active` y `Chair.active` sin valor por defecto (surgió en el propose)

Solo `Service.active` tiene valor por defecto (`True`, decidido en el explore, D2). En `Professional` y `Chair`, `active` es obligatorio.

**Por qué**: son clases nuevas y no hay código anterior que las construya, así que no hace falta un valor por defecto para no romper nada. Con un valor explícito, cada test y cada llamador dice si la referencia está activa, y un `Professional(P1)` no queda activo sin que nadie lo haya decidido.

**Alternativa descartada**: `active: bool = True` en las cuatro clases para que sean uniformes. Ahorraría unos caracteres en los tests, pero ocultaría el estado en el caso que esta regla evalúa.

### D11 — Tests

- Se sigue el estilo de C-02 (design D8 de C-02): datos literales, UUIDs fijos en constantes con nombre, día 2026-10-20 en UTC, sin `Mock`, `patch`, `monkeypatch` ni `freezegun`, tablas con `@pytest.mark.parametrize` y aserciones sobre la lista completa `[(v.code, v.reference_kind) ...]` o `[(v.code, v.conflicting_appointment_id) ...]`.
- En `test_validate_new_appointment.py` se agrega una fábrica `_refs(...)` que por defecto devuelve todas las referencias existentes y activas (`Patient(PATIENT)`, `Professional(P1, active=True)`, `Chair(S1, active=True)`, `Service(SVC_30, 30)`), con parámetros con nombre para reemplazar cualquiera por `None` o por una inactiva. `_request` suma `service_id=SVC_30`.
- **Adaptación de los tests de C-02**: cada llamada `validate_new_appointment(req, service, existing)` pasa a `validate_new_appointment(req, _refs(service=service, professional=..., chair=...), existing)`, con el profesional y el sillón del pedido. Lo que cada test verifica no cambia. Se hace en un paso propio, con la suite en verde antes y después.
- `pytest.raises(ValueError)` solo para la coherencia de ids (D9).

## Decisiones confirmadas por la autora

**Fecha: 2026-10-22.** D1 a D7 en el explore, tal como están en `docs/evidencias/explore-C-03.md`. D8, D9 y D10 en la revisión del propose. Queda para el punto de control el texto de los mensajes (D5 y D7).

## Desvíos durante el apply

- Se modificó una aserción de un test de C-02 (`test_validate_new_appointment.py`, mensaje de -15). Comparaba el texto exacto, el formato de D5 lo cambia y la spec solo pide que el mensaje mencione el valor recibido. Lo aprobó la autora en el punto de control 3.4 (2026-10-22).
- En la tarea 3.3 se tocó `tests/domain/test_model.py`, que la tarea no nombraba: se sumó `service_id` a una construcción de `NewAppointmentRequest`. Sin eso fallaban 3 tests y mypy. No cambió ninguna aserción.
- **Corrección 485 → 487.** El explore (decisión 5) y de ahí el proposal, la spec y el design D5 daban 485 como ejemplo de una duración que rompe dos condiciones, pero 485 es múltiplo de 5 (5 × 97) y solo supera el máximo. Lo detectó el test de la tarea 6.5 (falló porque el mensaje no contenía "múltiplo de 5"). La autora aprobó el cambio el 2026-10-22; se corrigió en `spec.md` (dos escenarios), `design.md` (D5), `proposal.md` y `tasks.md` (6.5), y se dejó una nota en `docs/evidencias/explore-C-03.md` sin borrar el 485 original. El 485 se mantiene donde solo debe superar el máximo (spec, tareas 6.4 y 7.4, `CHANGES.md`).
- **Tarea 4.3.** El test usa `duration_min=0` en vez de 30: con 30 el `Rejected` dependía de la regla de referencias del grupo 5, que todavía no existía; con 0 el rechazo viene de la duración y sigue valiendo después. Además pasó de entrada (sin rojo), porque la verificación de ids de 4.2 ya cubre el caso de referencias `None`.
- **Tarea 6.4 (aceptaciones y rechazo de 32 por defecto) y 6.5 (487)** pasaron en verde de entrada, sin verse en rojo: `check_duration` ya tenía la lógica de múltiplo de 5, máximo y mensaje con todas las razones desde 6.2/6.3.
- **Tareas 7.2 a 7.5.** Solo 7.1 se vio en rojo. Al hacer 7.2 se armaron de una vez los dos grupos (`_request_validity_violations`, `_agenda_conflict_violations`) y se sacó el `NotImplementedError`, de modo que 7.3 (cubierta antes por un test escrito en 5.3, que sí falló por esa rama), 7.4, 7.5 y el refactor 7.6 pasaron de entrada. En `validate_new_appointment` la condición `duration is None` solo acota el tipo: sin duración efectiva siempre hay `UNKNOWN_REFERENCE`, así que no hay un `raise` nuevo en el dominio.
- **Tarea 5.6.** El test de "horario ocupado" pasó de entrada por el corte; se quitó el corte temporalmente y fallaron 13 tests, y se restauró.

## Risks / Trade-offs

- [Cambiar la firma de `validate_new_appointment` rompe a todos los llamadores] → Hoy solo la llaman los tests de dominio y el ejemplo de `backend/README.md`; todavía no hay API (C-22). Es el momento más barato para cambiarla.
- [El llamador carga la entidad equivocada] → La verificación de coherencia de ids (D9) lo detecta como error de programación.
- [C-05 a C-07 necesitan más contexto y vuelven a tocar la firma] → `AppointmentReferences` agrupa solo las referencias. Si esos changes necesitan un contexto mayor, pueden envolverlo sin cambiar `check_references`.
- [Prestación inexistente sin duración: no se informa nada sobre la duración] → Es deliberado (D3). Al corregir la prestación, la duración por defecto se valida.
- [Mensajes mínimos con ids en vez de nombres] → Solo los consume la suite hasta C-08. `reference_kind` ya le alcanza al frontend para marcar el campo.
- [`ReferenceKind` duplica en parte la idea de "campo del formulario"] → Es el tipo del dominio; la API lo traduce al nombre del campo JSON en C-22.

## Migration Plan

No aplica: no hay datos ni API. Rollback: revertir los cambios de `app/domain` y de los tests de dominio (un solo commit del change).

## Open Questions

Ninguna que cambie el alcance. El texto de los mensajes (D5 y D7) se confirma o se ajusta en la tarea ⛔ antes de implementar las reglas.
