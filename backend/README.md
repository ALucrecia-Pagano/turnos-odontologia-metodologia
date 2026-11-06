# Backend — turnos-odontologia

Backend en Python del sistema de agenda de turnos: proyecto instalable, `pytest`,
`mypy --strict`, validación de agenda y altas/activación de catálogo en el paquete
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

## Migraciones

Con PostgreSQL y Redis iniciados desde la raíz:

```powershell
docker compose up -d
```

Desde `backend/`, Alembic obtiene `DATABASE_URL` de la configuración de la
aplicación y no de `alembic.ini`:

```powershell
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m alembic current
.\.venv\Scripts\python -m alembic downgrade base
.\.venv\Scripts\python -m alembic upgrade head
pytest
pytest -m integration
```

Para cargar los catálogos y pacientes ficticios de forma idempotente:

```powershell
.\.venv\Scripts\python -m app.db.seed
```

El comando se ejecuta manualmente después de migrar la base y solo usa los
datos ficticios definidos en `app.demo_data`.

El seed también crea un usuario ficticio por rol: `administrador`, `recepcion` y
`odontologo` (vinculado al primer profesional). Su contraseña sale de
`SEED_USER_PASSWORD`, que el seed exige con al menos 8 caracteres; si falta, o con
`APP_ENV=production`, termina con error sin escribir nada. Solo inserta los usuarios
que faltan: cambiar la variable no cambia a los usuarios existentes. Para que tome
una contraseña nueva hay que borrar antes esas filas de `app_user`.

`JWT_SECRET` debe tener al menos 32 caracteres, o la API no arranca. Para generar
uno y pegarlo en `.env`:

```powershell
.\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Al finalizar el trabajo local se puede detener Compose sin eliminar volúmenes:

```powershell
docker compose down
```

## API y Contenedores

Para levantar la API en un contenedor junto con PostgreSQL y Redis (construye la imagen, corre `alembic upgrade head` y levanta uvicorn en `API_PORT`):

```powershell
docker compose up --build -d backend
```

Documentación interactiva disponible en `http://localhost:<API_PORT>/api/docs` (Swagger UI) y verificación de salud en `http://localhost:<API_PORT>/api/health`.

> **Aviso sobre POSTGRES_PASSWORD**: la variable `DATABASE_URL` del servicio backend se interpola en Compose como `postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}`. Si `POSTGRES_PASSWORD` contiene caracteres reservados para URLs (como `@`, `:`, `/`, `?` o `#`), la URL resultante quedará malformada a menos que se use una contraseña sin caracteres especiales o se codifique para URL.

## Dominio

`app/domain` es Python puro: sin I/O, sin reloj global y sin generar ids (se inyectan).

| Módulo | Contenido |
|---|---|
| `model` | `AppointmentStatus`, `Professional` (con `full_name`) y `Chair` (con `name`), nombres que los constructores no validan y que usan los mensajes de conflicto; el alta sí los valida, `Patient` (cinco campos sin clínica), `Service` (nombre y duración), `Appointment`, `NewAppointmentRequest`, `AppointmentReferences`, `WorkingHours` (un tramo del horario de atención de un profesional), `Block` (un bloqueo de la agenda de un profesional, `[inicio, fin)` con motivo opcional) y `ScheduleContext` (la zona horaria, los tramos `working_hours`, los bloqueos `blocks` y el momento actual `now` que recibe el dominio); los instantes llevan zona y se normalizan a UTC |
| `violations` | `ViolationCode`, `ReferenceKind`, `Violation` (con `conflicting_interval`, en UTC), `Ok`, `Rejected`, `ValidationResult` |
| `intervals` | `Interval` semiabierto `[inicio, fin)`, `overlaps` y la hora local: `local_day_and_minutes`, `format_local_time`, `format_local_date_time` y `format_local_date_time_with_seconds` (fecha y hora local siempre con segundos, para el mensaje de `IN_THE_PAST`) |
| `rules/` | `grid` (`GRID_STEP_MIN`, la granularidad de 5 min compartida), `duration` (positiva, múltiplo de 5 y máximo 480 min), `references` (existentes y activas), `start_time` (inicio en la grilla, en hora local), `same_day` (un solo día local), `working_hours` (horario de atención del turno y validez de un conjunto de tramos), `blocks` (turno que pisa un bloqueo, validez de un bloqueo y `appointments_affected_by_block`, los turnos que pisa un bloqueo nuevo sin cancelarlos), `names` (el nombre del profesional o del sillón como sujeto de un mensaje, con un sustantivo genérico si está vacío), `overlap` (profesional y sillón) y `past` (el turno no empieza antes de `now`, comparando instantes sin truncar) |
| `appointment/` | `validate_new_appointment` |

`validate_new_appointment` evalúa en dos grupos y nunca los mezcla: primero la validez del
pedido (referencias, duración, inicio en la grilla, medianoche local y que el inicio no sea
anterior a `now`, todas juntas, en ese orden) y, solo si no hay ninguna, los conflictos de agenda (grupo 2: horario de atención,
bloqueos del profesional y después solapamientos del profesional y del sillón, todos
juntos). La grilla del inicio, la medianoche y el horario de atención se evalúan en la
zona de `ScheduleContext`, que el llamador pasa siempre junto con los tramos y los
bloqueos (sin valor por defecto). Los bloqueos se comparan como instantes, aunque duren
varios días. Los mensajes de conflicto identifican al profesional o al sillón por su
nombre recortado (o un sustituto genérico) y muestran el rango en hora local. Las
violaciones de solapamiento y bloqueo incluyen `conflicting_interval` en UTC, el
intervalo completo del turno existente o del bloqueo; las demás no llevan intervalo.

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
    patient=Patient(id=UUID(int=2), full_name="Ana Pérez", dni="30111222"),
    professional=Professional(id=UUID(int=3), full_name="Dra. Laura Quiroga", active=True),
    chair=Chair(id=UUID(int=4), name="Sillón 1", active=True),
    service=Service(id=UUID(int=5), name="Limpieza", default_duration_min=30),
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

## Catálogo

`catalog.result.Ok.entity` acepta entidades; `violations.Ok.appointment` de agenda conserva su contrato. Ambos comparten `Rejected` y `Violation`.

Las altas reciben candidatas inmutables e ids del llamador. El profesional conserva su nombre original; vacío o blanco produce EMPTY_NAME con mensaje explicativo.

Sillones y prestaciones comparan nombres con espacios colapsados y casefold, conservando tildes. Los duplicados muestran el nombre ingresado con espacios colapsados y mayúsculas originales; también participan existentes inactivos.

Las prestaciones reutilizan check_duration con sujeto «de la prestación». El valor predeterminado «del turno» mantiene idénticos los mensajes de agenda; las razones y sus límites no cambian.

El alta de pacientes copia el DNI quitando puntos y espacios; valida 7 u 8 dígitos y unicidad por dígitos. Los errores muestran el original o el DNI duplicado con puntos de miles. Patient tiene exactamente cinco campos sin clínica; teléfono y obra social son texto libre opcional.

Las altas acumulan violaciones aplicables en orden: EMPTY_NAME, INVALID_DNI, duplicado y duración. Por ejemplo, un paciente sin nombre y con DNI inválido recibe ambos errores; los duplicados dependientes de un campo inválido no se evalúan.

`deactivate` y `reactivate` usan copias con el mismo tipo y campos, cambiando solo active. Son idempotentes por valores y no reciben turnos. No existen códigos de ya activo/inactivo.

Desactivar no altera turnos existentes. Los turnos nuevos conservan el rechazo INACTIVE_REFERENCE con los textos originales; reactivar permite aceptar nuevos turnos y mantiene Ok.appointment de agenda.

`app.demo_data` contiene tuplas de ejemplos exclusivamente ficticios para tests y un futuro seed; no ejecuta I/O ni contiene secretos. Importa entidades del dominio; el dominio nunca lo importa.
