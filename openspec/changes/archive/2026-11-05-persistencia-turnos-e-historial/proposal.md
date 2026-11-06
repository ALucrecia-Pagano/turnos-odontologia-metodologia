# Proposal

## Why

C-12 modeló de forma pura el historial funcional inmutable (`AppointmentStatusChange`, `RescheduleDetail`) en todas las transiciones del turno, y C-15 junto con C-16 resolvieron la persistencia de catálogos, pacientes, horarios y bloqueos en PostgreSQL. Sin embargo, los turnos y sus entradas de historial no cuentan aún con tablas relacionales ni persistencia atómica. C-17 conecta los turnos y su trazabilidad con PostgreSQL garantizando que turno e historial se guarden juntos o ninguno (RN-GL-02), serializando altas y reprogramaciones con `SELECT ... FOR UPDATE` sobre profesional y sillón (DD-03), protegiendo las transiciones concurrentes mediante relectura bloqueada de la fila del turno (D11), forzando el historial estrictamente append-only mediante triggers de base de datos e implementando el lector SQL `AppointmentReader` de C-16 antes de construir la API de turnos (C-22 y C-23).

## What Changes

- Agregar los modelos declarativos SQLAlchemy `AppointmentModel` (`appointment`) y `AppointmentStatusChangeModel` (`appointment_status_change`) en `backend/app/db/models.py`, separados de los tipos del dominio.
- Persistir `RescheduleDetail` mediante 8 columnas dedicadas en `appointment_status_change` con una restricción `CHECK` todo-o-nada y claves foráneas opcionales a `professional` y `chair`.
- Asignar `created_at` y `updated_at` exclusivamente en persistencia usando `status_change.changed_at` (sin `server_default`, `NOT NULL`, sin exponerlos en el tipo `Appointment` del dominio).
- Crear la capa de servicios de aplicación en `backend/app/services/appointments.py` con `book_appointment`, `change_appointment_status`, `cancel_appointment` y `reschedule_appointment`, gestionando una única transacción, el orden global de bloqueo (`appointment` si existe → `professional` ordenados por id → `chair` ordenados por id), la carga de contexto dentro del bloqueo, la relectura del estado actual del turno para prevenir carreras, y el guardado/rollback atómico.
- Implementar `AppointmentRepository` en `backend/app/repositories/appointment.py` y proveer la implementación SQL de `AppointmentReader` para que `BlockRepository.list_affected_appointments` consulte turnos activos reales en PostgreSQL.
- Crear la migración reversible `20261105_04_turnos_e_historial` encadenada a `20261104_03_horarios_y_bloqueos`, incluyendo índices compuestos, restricciones `CHECK` de estado, intervalo y reprogramación, y la función/trigger `BEFORE UPDATE OR DELETE` que garantiza que el historial sea append-only en la base.
- Agregar tests unitarios de metadata/contratos y tests de integración sobre `<POSTGRES_DB>_test` que verifiquen atomicidad, restricciones, trigger append-only, reversibilidad de migración y concurrencia real multi-conexión con sondeo acotado sobre bloqueos de PostgreSQL y `lock_timeout`.

## Capabilities

### New Capabilities

- Ninguna. Se conserva la frontera existente de `database-infrastructure`: la persistencia de turnos e historial, la serialización concurrente y el lector SQL extienden la infraestructura de base de datos y repositorios.

### Modified Capabilities

- `database-infrastructure`: agrega las tablas `appointment` y `appointment_status_change`, sus restricciones `CHECK`, índices y trigger append-only, los servicios transaccionales de turnos con serialización pesimista, la implementación SQL de `AppointmentReader` y la migración `20261105_04_turnos_e_historial`.

## Impact

- `backend/app/db/models.py`, `backend/app/repositories/appointment.py`, `backend/app/repositories/contracts.py` y nuevo módulo `backend/app/services/appointments.py`.
- Nueva migración `backend/alembic/versions/20261105_04_turnos_e_historial.py`.
- Tests unitarios (`tests/test_persistence_metadata.py`, `tests/test_repository_contracts.py`) y de integración (`tests/integration/test_appointment_persistence.py`, `tests/integration/test_database_infrastructure.py`).
- El paquete de dominio en `backend/app/domain/` permanece 100% puro e inmutable; la API REST HTTP (C-22 a C-24) y la autenticación JWT (C-19) no se modifican.

