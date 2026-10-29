# Backend — turnos-odontologia

Backend en Python del sistema de agenda de turnos. Por ahora contiene solo la
fundación: proyecto instalable, `pytest`, `mypy --strict` y el paquete de dominio
`app.domain` (Python puro).

## Requisitos

- Python 3.12 o superior (en esta máquina se usa 3.13).

## Puesta en marcha

Desde `backend/`:

```powershell
py -3.13 -m venv .venv            # alternativa fuera de Windows: python3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1      # activar el entorno en PowerShell
source .venv/Scripts/activate     # activar el entorno en Git Bash
pip install -e ".[dev]"
```

Sin activar el entorno se puede usar directamente `.\.venv\Scripts\python -m pytest`.

## Comandos

```powershell
pytest    # corre los tests de tests/
mypy      # chequeo estricto de app y tests (Python 3.12 como objetivo)
```

## Dominio

`app/domain` es Python puro: sin I/O, sin reloj global y sin generar ids (se inyectan).

| Módulo | Contenido |
|---|---|
| `model` | `AppointmentStatus`, `Professional`, `Chair`, `Patient`, `Service`, `Appointment`, `NewAppointmentRequest`, `AppointmentReferences`, `WorkingHours` (un tramo del horario de atención de un profesional), `Block` (un bloqueo de la agenda de un profesional, `[inicio, fin)` con motivo opcional) y `ScheduleContext` (la zona horaria, los tramos `working_hours`, los bloqueos `blocks` y el momento actual `now` que recibe el dominio); los instantes llevan zona y se normalizan a UTC |
| `violations` | `ViolationCode`, `ReferenceKind`, `Violation`, `Ok`, `Rejected`, `ValidationResult` |
| `intervals` | `Interval` semiabierto `[inicio, fin)`, `overlaps` y la hora local: `local_day_and_minutes`, `format_local_time`, `format_local_date_time` y `format_local_date_time_with_seconds` (fecha y hora local siempre con segundos, para el mensaje de `IN_THE_PAST`) |
| `rules/` | `grid` (`GRID_STEP_MIN`, la granularidad de 5 min compartida), `duration` (positiva, múltiplo de 5 y máximo 480 min), `references` (existentes y activas), `start_time` (inicio en la grilla, en hora local), `same_day` (un solo día local), `working_hours` (horario de atención del turno y validez de un conjunto de tramos), `blocks` (turno que pisa un bloqueo, validez de un bloqueo y `appointments_affected_by_block`, los turnos que pisa un bloqueo nuevo sin cancelarlos), `overlap` (profesional y sillón) y `past` (el turno no empieza antes de `now`, comparando instantes sin truncar) |
| `appointment/` | `validate_new_appointment` |

`validate_new_appointment` evalúa en dos grupos y nunca los mezcla: primero la validez del
pedido (referencias, duración, inicio en la grilla, medianoche local y que el inicio no sea
anterior a `now`, todas juntas, en ese orden) y, solo si no hay ninguna, los conflictos de agenda (grupo 2: horario de atención,
bloqueos del profesional y después solapamientos del profesional y del sillón, todos
juntos). La grilla del inicio, la medianoche y el horario de atención se evalúan en la
zona de `ScheduleContext`, que el llamador pasa siempre junto con los tramos y los
bloqueos (sin valor por defecto). Los bloqueos se comparan como instantes, aunque duren
varios días.

```python
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.appointment import validate_new_appointment
from app.domain.model import (
    AppointmentReferences,
    Chair,
    NewAppointmentRequest,
    Patient,
    Professional,
    ScheduleContext,
    Service,
    WorkingHours,
)
from app.domain.violations import Ok, Rejected

request = NewAppointmentRequest(
    id=UUID(int=1),
    patient_id=UUID(int=2),
    professional_id=UUID(int=3),
    chair_id=UUID(int=4),
    service_id=UUID(int=5),
    start_at=datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
)
# Quien llama resuelve cada referencia (entidad, o None si no existe).
references = AppointmentReferences(
    patient=Patient(id=UUID(int=2)),
    professional=Professional(id=UUID(int=3), active=True),
    chair=Chair(id=UUID(int=4), active=True),
    service=Service(id=UUID(int=5), default_duration_min=30),
)

# La zona la arma el borde (API) a partir de APP_TIMEZONE; el dominio la recibe.
# Los tramos del horario de atencion (dia ISO 1 = lunes ... 7 = domingo, minutos locales
# desde las 00:00; 540 = 09:00, 780 = 13:00) tambien los pasa quien llama, sin valor por
# defecto. El dominio elige los del profesional y del dia local del pedido.
working_hours = (WorkingHours(UUID(int=3), weekday=2, start_minute=540, end_minute=780),)
# Los bloqueos (Block) tambien son obligatorios; sin bloqueos se pasa una tupla vacia.
# El momento actual (now) tambien: lo lee el borde (API) y el dominio lo recibe con zona
# horaria (un datetime naive es un error de programacion); se normaliza a UTC.
context = ScheduleContext(
    tz=ZoneInfo("America/Argentina/Buenos_Aires"),
    working_hours=working_hours,
    blocks=(),
    now=datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc),
)

match validate_new_appointment(request, references, existing_appointments=[], context=context):
    case Ok(appointment):
        print(appointment.end_at)  # 2026-10-20 13:30:00+00:00
    case Rejected(violations):
        for violation in violations:
            print(violation.code.value, violation.message)
```

`uuid` está en la allowlist de la guardia solo como tipo: el dominio no genera ids.

## Guardia de dependencias del dominio

`tests/domain/test_domain_dependencies.py` falla si algún módulo de `app/domain`
importa algo fuera de la lista permitida (`DOMAIN_ALLOWED_MODULES` en
`tests/domain/import_guard.py`: biblioteca estándar acotada, `tzdata` y el propio
`app.domain`). Para ampliar la lista, agregar la entrada a esa constante en el
change que la necesita, justificándola en su `design.md`.

La guardia del reloj (`tests/domain/test_clock_guard.py`, con `ast`) falla si algún
módulo de `app/domain` lee el reloj del sistema (`datetime.now`, `utcnow`, `today` de
`datetime` o `date`, con alias o por el módulo `datetime`): el momento actual se
inyecta como `now`. Solo detecta nombres estáticos; `time` lo cubre la guardia de imports.
