# Modelo de Datos

Convenciones: base **PostgreSQL**, mapeada con **SQLAlchemy 2.x** (modelos en `backend/app/db/`, separados de los tipos del dominio); esquema versionado con migraciones (**Suposición:** Alembic, SU-10). Ids `UUID` (v4, generado en la aplicación); instantes como `timestamptz` en **UTC** (en Python, `datetime` con zona); booleanos `boolean`; horarios laborales como minutos (`integer`) desde las 00:00 **hora local** (`America/Argentina/Buenos_Aires`). Todos los datos de pacientes son **ficticios**.

## Dominios

| Dominio | Entidades |
|---------|-----------|
| Configuración del consultorio | `Professional`, `Chair`, `Service` |
| Disponibilidad | `WorkingHours`, `Block` |
| Agenda | `Appointment`, `AppointmentStatusChange` |
| Pacientes | `Patient` |
| Acceso | `User` (autenticación JWT, ver 03) |

## ERD

```
Professional 1───* WorkingHours
Professional 1───* Block
Professional 1───* Appointment
Chair        1───* Appointment
Service      1───* Appointment
Patient      1───* Appointment
Appointment  1───* AppointmentStatusChange
User         0..1─1 Professional        (un usuario Odontólogo apunta a su profesional)
User         1───* AppointmentStatusChange (changed_by)
```

Un turno referencia **exactamente** un profesional, un sillón, una prestación y un paciente.

## Entidades

### Professional
- `id` UUID PK · `full_name` TEXT NOT NULL · `license_number` TEXT NULL (matrícula ficticia) · `active` BOOLEAN DEFAULT true.
- Relaciones: 1─* `WorkingHours`, `Block`, `Appointment`.
- Constraint: `full_name` no vacío.

### Chair (sillón / box)
- `id` UUID PK · `name` TEXT NOT NULL UNIQUE · `active` BOOLEAN DEFAULT true.
- **Suposición:** sin vínculo prestación↔sillón en el MVP (SU-04).

### Service (prestación)
- `id` UUID PK · `name` TEXT NOT NULL UNIQUE · `default_duration_min` INTEGER NOT NULL · `active` BOOLEAN DEFAULT true.
- Constraint: `default_duration_min > 0`, múltiplo de la granularidad (5 min, SU-02) y `<= 480`.

### WorkingHours (horario de atención semanal)
- `id` UUID PK · `professional_id` FK · `weekday` INTEGER (1=lunes … 7=domingo, ISO) · `start_minute` INTEGER · `end_minute` INTEGER.
- Un profesional puede tener **varios tramos por día** (p. ej. 09:00–13:00 y 15:00–19:00).
- Constraints: `0 <= start_minute < end_minute <= 1440`; tramos del mismo profesional y día no se solapan.
- Índice: `(professional_id, weekday)`.

### Block (bloqueo)
- `id` UUID PK · `professional_id` FK · `start_at` TIMESTAMPTZ · `end_at` TIMESTAMPTZ · `reason` TEXT NULL (vacaciones, feriado, ausencia).
- Constraint: `start_at < end_at`.
- Índice: `(professional_id, start_at, end_at)`.
- **Suposición:** crear un bloqueo que pisa turnos existentes **no** los cancela (SU-05).

### Patient (datos mínimos, ficticios)
- `id` UUID PK · `full_name` TEXT NOT NULL · `dni` TEXT NOT NULL UNIQUE · `phone` TEXT NULL · `health_insurance` TEXT NULL (obra social como texto libre).
- **Sin** información clínica. DNI y teléfonos del seed son claramente ficticios.

### Appointment (turno)
- `id` UUID PK
- `patient_id`, `professional_id`, `chair_id`, `service_id` FK NOT NULL
- `start_at` TIMESTAMPTZ NOT NULL · `end_at` TIMESTAMPTZ NOT NULL (intervalo semiabierto `[start_at, end_at)`)
- `status` TEXT NOT NULL CHECK IN (`reservado`,`confirmado`,`atendido`,`ausente`,`cancelado`)
- `created_at` TIMESTAMPTZ · `updated_at` TIMESTAMPTZ
- Constraints: `start_at < end_at`; duración = `end_at - start_at` es múltiplo de 5 min.
- Índices: `(professional_id, start_at)`, `(chair_id, start_at)`, `(status, start_at)`.
- **Invariante de agenda** (garantizada por el dominio, no por la BD): para estados que ocupan agenda (`reservado`, `confirmado`, `atendido`; ver RN-AG-08) no existen dos turnos con el mismo `professional_id` ni con el mismo `chair_id` cuyos intervalos se solapen. Como red de seguridad concurrente, la transacción de alta o reprogramación toma `SELECT ... FOR UPDATE` sobre las filas del profesional y del sillón antes de validar (ver 02 y DD-03).

### AppointmentStatusChange (historial)
- `id` UUID PK · `appointment_id` FK · `from_status` TEXT NULL (NULL en la creación) · `to_status` TEXT NOT NULL · `changed_by` UUID (id de usuario) · `changed_at` TIMESTAMPTZ · `note` TEXT NULL.
- Solo inserción (append-only). Índice: `(appointment_id, changed_at)`.
- También registra reprogramaciones (`note` con el intervalo anterior).

### User (acceso con JWT)
- `id` UUID PK · `username` TEXT NOT NULL UNIQUE · `display_name` TEXT · `password_hash` TEXT NOT NULL · `role` TEXT CHECK IN (`odontologo`,`recepcion`,`administrador`) · `professional_id` FK NULL (solo para `odontologo`) · `active` BOOLEAN DEFAULT true.
- La contraseña se guarda **solo como hash** (bcrypt o argon2, SU-06); nunca en texto plano ni en el repo. El JWT no se persiste (DD-11).

## Seed data inicial (todo ficticio)

| Entidad | Datos |
|---------|-------|
| Professional | "Dra. Laura Quiroga (ficticia)", "Dr. Martín Ferrer (ficticio)", "Dra. Sofía Benítez (ficticia)" |
| Chair | "Sillón 1", "Sillón 2", "Sillón 3" |
| Service | Consulta 30 min · Limpieza 45 min · Extracción 60 min · Control de ortodoncia 30 min · Endodoncia 90 min |
| WorkingHours | Lun–Vie 09:00–13:00 y 15:00–19:00 para los tres (variar uno para pruebas, p. ej. Dr. Ferrer solo mañanas) |
| Patient | 5 pacientes con DNI ficticios (`10000001` a `10000005`) y teléfonos `11-5555-000X` |
| User | Un usuario por rol (`administrador`, `recepcion`, `odontologo` asociado a un profesional); contraseña tomada de `SEED_USER_PASSWORD` en `.env` |

El seed vive en un script (`backend/app/db/seed.py`) y **nunca** incluye datos reales ni contraseñas escritas en el código.
