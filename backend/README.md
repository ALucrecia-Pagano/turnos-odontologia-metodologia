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
| `model` | `AppointmentStatus`, `Professional`, `Chair`, `Patient`, `Service`, `Appointment`, `NewAppointmentRequest`, `AppointmentReferences` y `ScheduleContext` (la zona horaria que recibe el dominio); los instantes llevan zona y se normalizan a UTC |
| `violations` | `ViolationCode`, `ReferenceKind`, `Violation`, `Ok`, `Rejected`, `ValidationResult` |
| `intervals` | `Interval` semiabierto `[inicio, fin)`, `overlaps` y la hora local: `local_day_and_minutes` y `format_local_time` |
| `rules/` | `grid` (`GRID_STEP_MIN`, la granularidad de 5 min compartida), `duration` (positiva, múltiplo de 5 y máximo 480 min), `references` (existentes y activas), `start_time` (inicio en la grilla, en hora local), `same_day` (un solo día local) y `overlap` (profesional y sillón) |
| `appointment/` | `validate_new_appointment` |

`validate_new_appointment` evalúa en dos grupos y nunca los mezcla: primero la validez del
pedido (referencias, duración, inicio en la grilla y medianoche local, todas juntas, en ese
orden) y, solo si no hay ninguna, los conflictos de agenda (solapamientos). La grilla del
inicio y la medianoche se evalúan en la zona de `ScheduleContext`, que el llamador pasa
siempre (sin valor por defecto).

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
context = ScheduleContext(tz=ZoneInfo("America/Argentina/Buenos_Aires"))

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
