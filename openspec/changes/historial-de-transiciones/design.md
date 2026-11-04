# Design

## Context

El dominio de turnos en `backend/app/domain` ya cuenta con el alta validada (`validate_new_appointment` en `appointment/validate.py`), las transiciones de estado y cancelaciones (`change_status` y `cancel_appointment` en `appointment/transitions.py`) y la reprogramación con trazabilidad (`reschedule_appointment` en `appointment/reschedule.py`). Hasta C-11, las cuatro operaciones devolvían `Ok(appointment=...) | Rejected(violations=...)`, dejando explícitamente fuera de alcance el historial funcional (`AppointmentStatusChange`) exigido por **RN-TU-06**, **US-033**, **US-030 CA-3** y **US-031 CA-5**.

Ver `proposal.md` para la motivación y alcance general, y `docs/evidencias/explore-C-12.md` para el inventario detallado y las opciones evaluadas en el explore.

## Goals / Non-Goals

**Goals:**
- Modelar de forma pura e inmutable en `backend/app/domain/model.py` la entrada de historial `AppointmentStatusChange` y el detalle tipado de reprogramación `RescheduleDetail`.
- Ampliar `Ok` en `backend/app/domain/violations.py` a `Ok(appointment, status_change)` con ambos campos obligatorios para garantizar por sistema de tipos (`mypy --strict`) que ninguna operación exitosa de agenda o ciclo de vida omita su entrada de historial.
- Incorporar `changed_by: UUID` obligatorio en `NewAppointmentRequest` sin romper el orden de los 7 argumentos posicionales actuales.
- Generar exactamente una entrada `AppointmentStatusChange` en cada llamada exitosa a `validate_new_appointment`, `change_status`, `cancel_appointment` y `reschedule_appointment`, y ninguna entrada cuando devuelven `Rejected`.
- Mantener intactos los mensajes, códigos de violación, reglas de negocio y la pureza del dominio (`test_domain_purity.py`).

**Non-Goals:**
- Persistir `AppointmentStatusChange` o `RescheduleDetail` en PostgreSQL / SQLAlchemy (corresponde a **C-17** `persistencia-turnos-y-bloqueos`; cómo se mapea `RescheduleDetail` —ya sea serializado en la columna `note` de KB `04_modelo_de_datos.md` o en columnas dedicadas— se decide en C-17, según **D9**).
- Exponer endpoints HTTP para consultar o producir el historial (corresponde a **C-22** y **C-23**).
- Modificar el `Ok(entity=...)` del subdominio de catálogo (`backend/app/domain/catalog/result.py`).
- Agregar campos de auditoría técnica (IP, user-agent) o permitir edición/borrado de entradas del historial (**RN-TU-06**).

## Decisions

### D1 — Modelo inmutable `AppointmentStatusChange` y `RescheduleDetail` (Opción A)

Se definen en `backend/app/domain/model.py` dos dataclasses inmutables (`@dataclass(frozen=True, slots=True)`):

1. `RescheduleDetail`:
   - `previous_interval: Interval` (tipo `Interval` de `backend/app/domain/intervals.py`, que ya valida UTC, no *naive* y `start < end`).
   - `new_interval: Interval`.
   - `previous_professional_id: UUID`.
   - `new_professional_id: UUID`.
   - `previous_chair_id: UUID`.
   - `new_chair_id: UUID`.
2. `AppointmentStatusChange` (sin `id` propio en el dominio; la PK de persistencia pertenece a C-17):
   - `appointment_id: UUID` (en una reprogramación, el `id` del turno original sobre el cual se registra la transición hacia `reservado`).
   - `from_status: AppointmentStatus | None` (`None` únicamente en el alta inicial).
   - `to_status: AppointmentStatus`.
   - `changed_by: UUID`.
   - `changed_at: datetime` (con zona horaria obligatoria, normalizado a UTC mediante `_to_utc` en `__post_init__`; si es *naive* lanza `ValueError`).
   - `reschedule: RescheduleDetail | None = None`.

**Invariante adicional en `AppointmentStatusChange.__post_init__`**: si `self.from_status == self.to_status` y `self.reschedule is None`, se lanza `ValueError`. De esta manera, la única entrada válida donde el estado previo y el nuevo coinciden (`reservado -> reservado`) es la producida por una reprogramación con su `RescheduleDetail`.

**Alternativas descartadas**:
- *Opción B* (incluir `id: UUID` propio en `AppointmentStatusChange`): obligaría a inyectar un generador de UUIDs o un `status_change_id` extra en las cuatro funciones puras del dominio sin necesidad funcional previa a la persistencia.
- *Opción C* (guardar `note: str | None` con texto libre en el dominio): pierde tipado estricto sobre los intervalos, profesional y sillón anteriores y nuevos.

### D2 — Retorno `Ok(appointment, status_change)` en `violations.py` (Opción A)

En `backend/app/domain/violations.py`, `Ok` pasa a ser:

```python
@dataclass(frozen=True, slots=True)
class Ok:
    appointment: Appointment
    status_change: AppointmentStatusChange
```

Ambos campos son obligatorios (sin valor por defecto). `Rejected` no cambia, y el `Ok` del catálogo (`app.domain.catalog.result.Ok`) permanece independiente.

**Por qué esta opción**: hace imposible construir un `Ok` de turno sin su entrada de historial (`mypy --strict` lo impide en tiempo de chequeo estático). Las aserciones existentes en los tests de C-02 a C-11 hacen `isinstance(result, Ok)` y leen `result.appointment`, por lo que siguen funcionando sin cambios; solo se actualiza `backend/tests/domain/test_violations.py` en los 2 tests que instancian `Ok(appointment=...)` directamente.

**Alternativas descartadas**:
- *Opción B* (`status_change: AppointmentStatusChange | None = None`): debilitaría el contrato de tipos permitiendo olvidar la entrada.
- *Opción C* (nuevo tipo `AppointmentResult` o tupla `(Appointment, AppointmentStatusChange)`): rompería decenas de `isinstance(result, Ok)` y `result.appointment` en la suite existente.

### D3 — `changed_by: UUID` en `NewAppointmentRequest` con `field(kw_only=True)` (Opción A1)

`NewAppointmentRequest` en `backend/app/domain/model.py` tiene hoy 6 campos posicionales obligatorios (`id`, `patient_id`, `professional_id`, `chair_id`, `service_id`, `start_at`) seguidos de `duration_min: int | None = None`. En Python `dataclasses`, un campo posicional sin valor por defecto no puede declararse después de un campo con valor por defecto (`TypeError: non-default argument 'changed_by' follows default argument`), y ubicar `changed_by` antes de `duration_min` desplazaría el 7.º argumento posicional en las llamadas que pasan `duration_min` por posición (`30`, que es `int`, pasaría a ligarse a `changed_by: UUID`).

Se resuelve declarando `changed_by` al final con `field(kw_only=True)`:

```python
@dataclass(frozen=True, slots=True)
class NewAppointmentRequest:
    id: UUID
    patient_id: UUID
    professional_id: UUID
    chair_id: UUID
    service_id: UUID
    start_at: datetime
    duration_min: int | None = None
    changed_by: UUID = field(kw_only=True)
```

**Ventajas de elegir `field(kw_only=True)`**:
1. Es obligatorio y no tiene valor por defecto (cumple estrictamente D3 Opción A1).
2. Preserva intactas las 7 posiciones posicionales actuales (`id`, `patient_id`, `professional_id`, `chair_id`, `service_id`, `start_at`, `duration_min`), por lo que el `30` posicional sigue ligándose a `duration_min`.
3. Exige pasar `changed_by=...` por nombre, evitando confusiones accidentales entre los 5 campos `UUID` (`id`, `patient_id`, `professional_id`, `chair_id`, ` service_id`) y el nuevo `changed_by`.

**Constructores existentes que se actualizan** (5 sitios en total en todo el repositorio: 1 en producción y 4 en tests):
1. `backend/app/domain/appointment/reschedule.py` (`_build_request`, línea 103): pasa `changed_by=actor.user_id`.
2. `backend/tests/domain/test_model.py` (`_request`, línea 32): agrega `changed_by=UUID("00000000-0000-0000-0000-000000000099")` (o constante de actor ficticio).
3. `backend/tests/domain/test_validate_new_appointment.py` (`_request`, línea 111): agrega parámetro `changed_by: UUID = ACTOR_RECEPTION_ID` y lo pasa a `NewAppointmentRequest(..., changed_by=changed_by)`.
4. `backend/tests/domain/test_catalog_agenda.py` (`test_agenda_uses_catalog_created_entities`, línea 39): mantiene los 7 argumentos posicionales `(T1, PA1, P1, S1, SV1, datetime(...), 30)` y añade `, changed_by=U_RECEPTION`.
5. `backend/tests/domain/test_lifecycle_agenda.py` (`_new_appointment`, línea 44): mantiene los 7 argumentos posicionales `(T2, PA1, P1, S1, SV1, START, 30)` y añade `, changed_by=ACTOR_RECEPTION.user_id`.

### D4 — Entrada única en `reschedule_appointment` (Opción A)

Cuando `reschedule_appointment` tiene éxito:
1. Delega internamente la validación de disponibilidad en `validate_new_appointment` (que construye un `Ok` interno con `from_status=None`).
2. Descarta esa entrada interna de alta y construye en el `Ok` devuelto al llamador una **única** entrada `AppointmentStatusChange` con:
   - `appointment_id=appointment.id` (el `id` del turno original reprogramado).
   - `from_status=appointment.status` (el estado real previo del turno original: `AppointmentStatus.RESERVED` o `AppointmentStatus.CONFIRMED`).
   - `to_status=AppointmentStatus.RESERVED`.
   - `changed_by=actor.user_id`.
   - `changed_at=context.now` (ya normalizado a UTC por `SchedulingContext`).
   - `reschedule=RescheduleDetail(previous_interval=appointment.interval, new_interval=created.interval, previous_professional_id=appointment.professional_id, new_professional_id=created.professional_id, previous_chair_id=appointment.chair_id, new_chair_id=created.chair_id)`.

### D5 — Ausencia de entrada ante `Rejected` (Opción A)

Si cualquiera de las cuatro operaciones (`validate_new_appointment`, `change_status`, `cancel_appointment`, `reschedule_appointment`) devuelve `Rejected(violations=...)`, no construye ni devuelve `AppointmentStatusChange`.

### D6 — Verificación de inmutabilidad sin `type: ignore` (Opción A)

Tanto `AppointmentStatusChange` como `RescheduleDetail` se declaran con `@dataclass(frozen=True, slots=True)`. Su inmutabilidad se verifica en pytest con `pytest.raises(FrozenInstanceError)` invocando `setattr(instance, "campo", valor)` (igual que en `backend/tests/domain/test_model.py`), cumpliendo la prohibición de usar `# type: ignore` bajo `mypy --strict`.

### D7 — Un solo change y punto de control de governance ALTO (Opción A)

El alcance completo de C-12 se implementa en este único change. De acuerdo con la decisión de la autora, el punto de control de **governance ALTO** es la revisión y aprobación de este propose antes de ejecutar el apply; no se incluye un punto de control intermedio dentro de `tasks.md`.

### D8 — Fuente de `changed_at` en cada operación

- En `validate_new_appointment` y `reschedule_appointment`: `changed_at` toma `context.now` (que `SchedulingContext.__post_init__` ya valida como *aware* y normaliza a UTC).
- En `change_status` y `cancel_appointment`: `changed_at` toma el instante `now` validado y normalizado a UTC con `_require_utc_now(now, "now")` (y reasegurado por `AppointmentStatusChange.__post_init__`).

### D9 — Persistencia de `RescheduleDetail` fuera de alcance (hacia C-17)

La decisión de cómo persistir `RescheduleDetail` en la tabla de historial (ya sea formateado en la columna `note` de `knowledge-base/04_modelo_de_datos.md` o mediante columnas específicas en el modelo SQLAlchemy/Alembic) queda explícitamente fuera de alcance de C-12 y se resolverá en **C-17 (`persistencia-turnos-y-bloqueos`)**.

## Risks / Trade-offs

- **[Risk] Impacto del cambio de firma en `NewAppointmentRequest` y `Ok` sobre tests existentes** → **Mitigation**: Usar `changed_by: UUID = field(kw_only=True)` acota el cambio en `NewAppointmentRequest` a 4 archivos de tests y 1 helper interno (`reschedule.py`); mantener `Ok.appointment` como primer atributo preserva todas las aserciones existentes salvo las 2 instancias directas de `Ok(...)` en `test_violations.py`.
- **[Risk] Filtración accidental de la entrada `from_status=None` que genera `validate_new_appointment` cuando es invocada desde `reschedule_appointment`** → **Mitigation**: `reschedule_appointment` construye explícitamente un nuevo `Ok(appointment=rescheduled, status_change=reschedule_entry)` reemplazando el `Ok` interno, y se incluye un escenario específico en la spec y en `test_status_history.py` que verifica que `result.status_change.from_status` nunca sea `None` al reprogramar.
- **[Risk] Entradas de historial con `from_status == to_status` fuera de una reprogramación** → **Mitigation**: `AppointmentStatusChange.__post_init__` rechaza con `ValueError` cualquier construcción donde `from_status == to_status` y `reschedule is None`.

## Migration Plan

No aplica migración de base de datos ni de API (cambio puro en memoria dentro de `backend/app/domain`). C-17 consumirá `result.status_change` al persistir las operaciones de turno en PostgreSQL.

## Convenciones de los escenarios de `specs/appointment-lifecycle/spec.md` y `specs/appointment-scheduling/spec.md`

Para mantener los escenarios autocontenidos y evitar texto libre antes del primer `### Requirement:` de cada sección (que `openspec archive` descarta en OpenSpec 1.16), rigen las siguientes convenciones sobre datos ficticios en todos los escenarios de este change:

- Zona horaria del consultorio: `America/Argentina/Buenos_Aires` (UTC-3 fija). Todos los instantes se expresan con su hora local y su equivalente UTC (`Z`).
- `NOW`: `2026-10-19T14:00:00Z` (lunes `2026-10-19 11:00` local).
- Profesionales ficticios:
  - `P1`: `"Dra. Laura Quiroga"` (activa, atiende martes de `09:00` a `13:00` local, prestaciones `SV1` y `SV2`).
  - `P2`: `"Dr. Martín Pereyra"` (activo, atiende martes de `09:00` a `18:00` local, prestaciones `SV1` y `SV2`).
- Sillones ficticios:
  - `S1`: `"Sillón 1"` (activo).
  - `S2`: `"Sillón 2"` (activo).
- Prestaciones ficticias:
  - `SV1`: `"Consulta y diagnóstico"`, `30` min, activa.
- Paciente ficticio: `PA1` (`" Sofía Méndez"`).
- Actores ficticios:
  - Recepción `U2`: `Actor(user_id=U2, role=Role.RECEPTION)`.
  - Odontólogo `U_P1`: `Actor(user_id=U_P1, role=Role.DENTIST, professional_id=P1)`.
  - Odontólogo `U_P2`: `Actor(user_id=U_P2, role=Role.DENTIST, professional_id=P2)`.
  - Administrador `U_ADMIN`: `Actor(user_id=U_ADMIN, role=Role.ADMIN)`.
- Turno base `T1`: martes `2026-10-20` de `10:00` a `10:30` local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), paciente `PA1`, profesional `P1`, sillón `S1`, prestación `SV1`, creado en `CREATED_AT = 2026-10-18T12:00:00Z` (`09:00` local).

