# Modelo de Datos

Convenciones: ids `TEXT` (UUID v4 generado en la aplicación); instantes como `INTEGER` epoch en milisegundos UTC; horarios laborales como minutos desde las 00:00 **hora local** (`America/Argentina/Buenos_Aires`). Todos los datos de pacientes son **ficticios**.

## Dominios

| Dominio | Entidades |
|---------|-----------|
| Configuración del consultorio | `Professional`, `Chair`, `Service` |
| Disponibilidad | `WorkingHours`, `Block` |
| Agenda | `Appointment`, `AppointmentStatusChange` |
| Pacientes | `Patient` |
| Acceso | `User` (rol simulado en el MVP, ver 03) |

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
- `id` TEXT PK · `full_name` TEXT NOT NULL · `license_number` TEXT NULL (matrícula ficticia) · `active` INTEGER (0/1) DEFAULT 1.
- Relaciones: 1─* `WorkingHours`, `Block`, `Appointment`.
- Constraint: `full_name` no vacío.

### Chair (sillón / box)
- `id` TEXT PK · `name` TEXT NOT NULL UNIQUE · `active` INTEGER DEFAULT 1.
- **Suposición:** sin vínculo prestación↔sillón en el MVP (SU-04).

### Service (prestación)
- `id` TEXT PK · `name` TEXT NOT NULL UNIQUE · `default_duration_min` INTEGER NOT NULL · `active` INTEGER DEFAULT 1.
- Constraint: `default_duration_min > 0`, múltiplo de la granularidad (5 min, SU-02) y `<= 480`.

### WorkingHours (horario de atención semanal)
- `id` TEXT PK · `professional_id` FK · `weekday` INTEGER (1=lunes … 7=domingo, ISO) · `start_minute` INTEGER · `end_minute` INTEGER.
- Un profesional puede tener **varios tramos por día** (p. ej. 09:00–13:00 y 15:00–19:00).
- Constraints: `0 <= start_minute < end_minute <= 1440`; tramos del mismo profesional y día no se solapan.
- Índice: `(professional_id, weekday)`.

### Block (bloqueo)
- `id` TEXT PK · `professional_id` FK · `start_at` INTEGER · `end_at` INTEGER · `reason` TEXT NULL (vacaciones, feriado, ausencia).
- Constraint: `start_at < end_at`.
- Índice: `(professional_id, start_at, end_at)`.
- **Suposición:** crear un bloqueo que pisa turnos existentes **no** los cancela (SU-05).

### Patient (datos mínimos, ficticios)
- `id` TEXT PK · `full_name` TEXT NOT NULL · `dni` TEXT NOT NULL UNIQUE · `phone` TEXT NULL · `health_insurance` TEXT NULL (obra social como texto libre).
- **Sin** información clínica. DNI y teléfonos del seed son claramente ficticios.

### Appointment (turno)
- `id` TEXT PK
- `patient_id`, `professional_id`, `chair_id`, `service_id` FK NOT NULL
- `start_at` INTEGER NOT NULL · `end_at` INTEGER NOT NULL (intervalo semiabierto `[start_at, end_at)`)
- `status` TEXT NOT NULL CHECK IN (`reservado`,`confirmado`,`atendido`,`ausente`,`cancelado`)
- `created_at` INTEGER · `updated_at` INTEGER
- Constraints: `start_at < end_at`; duración = `end_at - start_at` es múltiplo de 5 min.
- Índices: `(professional_id, start_at)`, `(chair_id, start_at)`, `(status, start_at)`.
- **Invariante de agenda** (garantizada por el dominio, no por la BD): para estados que ocupan agenda (`reservado`, `confirmado`, `atendido`; ver RN-AG-08) no existen dos turnos con el mismo `professional_id` ni con el mismo `chair_id` cuyos intervalos se solapen. La BD añade una transacción `BEGIN IMMEDIATE` como red de seguridad concurrente (ver 02).

### AppointmentStatusChange (historial)
- `id` TEXT PK · `appointment_id` FK · `from_status` TEXT NULL (NULL en la creación) · `to_status` TEXT NOT NULL · `changed_by` TEXT (id de usuario) · `changed_at` INTEGER · `note` TEXT NULL.
- Solo inserción (append-only). Índice: `(appointment_id, changed_at)`.
- También registra reprogramaciones (`note` con el intervalo anterior).

### User (acceso simulado en el MVP)
- `id` TEXT PK · `display_name` TEXT · `role` TEXT CHECK IN (`odontologo`,`recepcion`,`administrador`) · `professional_id` FK NULL (solo para `odontologo`).
- **Sin** contraseñas ni credenciales en el MVP (SU-06).

## Seed data inicial (todo ficticio)

| Entidad | Datos |
|---------|-------|
| Professional | "Dra. Laura Quiroga (ficticia)", "Dr. Martín Ferrer (ficticio)", "Dra. Sofía Benítez (ficticia)" |
| Chair | "Sillón 1", "Sillón 2", "Sillón 3" |
| Service | Consulta 30 min · Limpieza 45 min · Extracción 60 min · Control de ortodoncia 30 min · Endodoncia 90 min |
| WorkingHours | Lun–Vie 09:00–13:00 y 15:00–19:00 para los tres (variar uno para pruebas, p. ej. Dr. Ferrer solo mañanas) |
| Patient | 5 pacientes con DNI ficticios (`10000001` a `10000005`) y teléfonos `11-5555-000X` |
| User | Un usuario por rol (`administrador`, `recepcion`, `odontologo` asociado a un profesional) |

El seed vive en un script (`apps/api/src/db/seed.ts`) y **nunca** incluye datos reales.
