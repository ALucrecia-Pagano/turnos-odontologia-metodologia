# Design

## Context

C-12 modeló las entradas funcionales inmutables de historial `AppointmentStatusChange` y `RescheduleDetail`, garantizando que `validate_new_appointment`, `change_status`, `cancel_appointment` y `reschedule_appointment` devuelvan `Ok(appointment, status_change)`. C-15 y C-16 resolvieron la persistencia de catálogos, pacientes, horarios de atención y bloqueos. La motivación y alcance se describen en `proposal.md`; los contratos verificables están en el delta de `database-infrastructure`.

## Goals / Non-Goals

**Goals:**

- Persistir `appointment` y `appointment_status_change` en PostgreSQL manteniendo al dominio 100% puro y aislado.
- Garantizar atomicidad estricta (RN-GL-02): turno e historial se guardan juntos en la misma transacción o se revierte todo.
- Implementar la serialización pesimista con `SELECT ... FOR UPDATE` sobre profesional y sillón en orden fijo anti-deadlock (DD-03, D4) y sobre la fila del turno existente con relectura de estado para prevenir transiciones duplicadas concurrentes (D11).
- Encapsular la orquestación transaccional en `backend/app/services/appointments.py` (D5), dejando a los repositorios libres de commits.
- Garantizar que el historial sea estrictamente append-only mediante contrato de repositorio y trigger `BEFORE UPDATE OR DELETE` en PostgreSQL (D6).
- Implementar el lector SQL `AppointmentReader` de C-16 (D8) para turnos reales.
- Proveer la migración reversible `20261105_04_turnos_e_historial` y tests de concurrencia real sin `time.sleep` ni mocks (D9).

**Non-Goals:**

- Modificar el dataclass `Appointment` ni el dominio puro (`created_at` y `updated_at` viven solo en la base; D12).
- Crear endpoints REST HTTP FastAPI ni autenticación JWT (corresponden a C-18, C-19, C-22 y C-23).
- Sembrar turnos en `seed_database()` (la agenda inicia limpia según KB 04; D10).
- Usar extensiones no estándar ni constraints `EXCLUDE USING gist` (DD-03, D7).

## Decisions

### D1 — Tablas, columnas y restricciones de `appointment` y `appointment_status_change`

En `backend/app/db/models.py`:

1. `AppointmentModel` (`__tablename__ = "appointment"`):
   - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` (toma el id del dominio).
   - `patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("patient.id", ondelete="RESTRICT"), nullable=False)`.
   - `professional_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id", ondelete="RESTRICT"), nullable=False)`.
   - `chair_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("chair.id", ondelete="RESTRICT"), nullable=False)`.
   - `service_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("service.id", ondelete="RESTRICT"), nullable=False)`.
   - `start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
   - `end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
   - `status: Mapped[str] = mapped_column(String(20), nullable=False)`.
   - `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
   - `updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
   - Constraints e índices en `__table_args__`:
     - `CheckConstraint("status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status")`.
     - `CheckConstraint("start_at < end_at", name="ck_appointment_interval_order")`.
     - `Index("ix_appointment_professional_id_start_at", "professional_id", "start_at")`.
     - `Index("ix_appointment_chair_id_start_at", "chair_id", "start_at")`.
     - `Index("ix_appointment_status_start_at", "status", "start_at")`.

2. `AppointmentStatusChangeModel` (`__tablename__ = "appointment_status_change"`):
   - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` (generado con `uuid4()` en el repositorio; el dominio no tiene `id`).
   - `appointment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("appointment.id", ondelete="RESTRICT"), nullable=False)`.
   - `from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)`.
   - `to_status: Mapped[str] = mapped_column(String(20), nullable=False)`.
   - `changed_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)` (sin FK; la tabla `user` pertenece a C-19).
   - `changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
   - `note: Mapped[str | None] = mapped_column(String(500), nullable=True)`.
   - 8 columnas dedicadas para `RescheduleDetail` (ver D2).
   - Constraints e índices en `__table_args__`:
     - `CheckConstraint("from_status IS NULL OR from_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status_change_from_status")`.
     - `CheckConstraint("to_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status_change_to_status")`.
     - `Index("ix_appointment_status_change_appointment_id_changed_at", "appointment_id", "changed_at")`.

### D2 — Persistencia de `RescheduleDetail` con columnas dedicadas y CHECK todo-o-nada

`RescheduleDetail` se persiste mediante 8 columnas dedicadas en `appointment_status_change`:
- `reschedule_previous_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
- `reschedule_previous_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
- `reschedule_new_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
- `reschedule_new_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
- `reschedule_previous_professional_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id", ondelete="RESTRICT"), nullable=True)`
- `reschedule_new_professional_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id", ondelete="RESTRICT"), nullable=True)`
- `reschedule_previous_chair_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("chair.id", ondelete="RESTRICT"), nullable=True)`
- `reschedule_new_chair_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("chair.id", ondelete="RESTRICT"), nullable=True)`

Se añade la restricción nombrada:
```sql
CheckConstraint(
    "(reschedule_previous_start_at IS NULL AND reschedule_previous_end_at IS NULL AND "
    "reschedule_new_start_at IS NULL AND reschedule_new_end_at IS NULL AND "
    "reschedule_previous_professional_id IS NULL AND reschedule_new_professional_id IS NULL AND "
    "reschedule_previous_chair_id IS NULL AND reschedule_new_chair_id IS NULL) "
    "OR "
    "(reschedule_previous_start_at IS NOT NULL AND reschedule_previous_end_at IS NOT NULL AND "
    "reschedule_new_start_at IS NOT NULL AND reschedule_new_end_at IS NOT NULL AND "
    "reschedule_previous_professional_id IS NOT NULL AND reschedule_new_professional_id IS NOT NULL AND "
    "reschedule_previous_chair_id IS NOT NULL AND reschedule_new_chair_id IS NOT NULL)",
    name="ck_appointment_status_change_reschedule_all_or_none"
)
```
Garantiza integridad relacional estricta, tipos `timestamptz`/UUID nativos y validación por base sin datos parciales.

### D3 — Asignación estricta de `created_at` y `updated_at` sin `server_default`

No se usa `server_default` en `created_at` ni `updated_at`. La fuente única de verdad es `status_change.changed_at`:
- En el alta inicial (`book_appointment`): `created_at = updated_at = status_change.changed_at`.
- En cada cambio de estado, cancelación o reprogramación: `updated_at = status_change.changed_at` (preservando el `created_at` original del turno).
Ambas columnas son `NOT NULL` sin default: si el código omitiera pasar un valor, PostgreSQL falla fuerte de inmediato.

### D4 — Orden global de bloqueo pesimista anti-deadlock (`SELECT ... FOR UPDATE`)

Para serializar concurrentes sin deadlocks (DD-03), el servicio adquiere bloqueos en este orden global estricto:
1. La fila del propio `appointment` mediante `SELECT id, status FROM appointment WHERE id = :id FOR UPDATE` (únicamente si la operación actúa sobre un turno existente: cambio de estado, cancelación o reprogramación).
2. Las filas de `professional` involucradas, ordenadas por `id` en orden lexicográfico ascendente (`SELECT id FROM professional WHERE id IN (...) ORDER BY id FOR UPDATE`). En reprogramaciones con cambio de profesional, se bloquean tanto el anterior como el nuevo.
3. Las filas de `chair` involucradas, ordenadas por `id` en orden lexicográfico ascendente (`SELECT id FROM chair WHERE id IN (...) ORDER BY id FOR UPDATE`). En reprogramaciones con cambio de sillón, se bloquean ambos.

**El contexto de agenda (turnos activos en rango del profesional y del sillón) se consulta estrictamente DESPUÉS de haber tomado todos los bloqueos.**

### D5 — Capa de servicios transaccionales en `backend/app/services/appointments.py`

Se crea el módulo de servicios `backend/app/services/appointments.py` con las siguientes funciones:
- `book_appointment(session, request, references, schedule_context, now, tz, auto_commit=True) -> Ok | Rejected`
- `change_appointment_status(session, appointment_id, target_status, actor, now, professional_name, tz, auto_commit=True) -> Ok | Rejected | None`
- `cancel_appointment(session, appointment_id, actor, now, professional_name, tz, auto_commit=True) -> Ok | Rejected | None`
- `reschedule_appointment(session, appointment_id, request, actor, schedule_context, now, tz, auto_commit=True) -> Ok | Rejected | None`

Cada función:
1. Abre una única transacción (`with session.begin_nested():` o bloque transaccional).
2. Adquiere los locks según D4 y D11.
3. Carga referencias, horarios, bloqueos y turnos activos de la base.
4. Invoca la función pura de dominio (`validate_new_appointment`, `change_status`, `cancel_appointment` o `reschedule_appointment`).
5. Si el dominio devuelve `Ok`: persiste/actualiza `AppointmentModel`, persiste `AppointmentStatusChangeModel`, hace commit de la transacción (si `auto_commit=True`) y devuelve `Ok`.
6. Si el dominio devuelve `Rejected`: revierte la transacción (`rollback`) y devuelve `Rejected` sin escribir nada en disco.
7. Los repositorios son componentes de acceso a datos y **nunca hacen commit**. La API REST de C-22 y C-23 consumirá directamente estos servicios.
8. **Prueba de falla de historial sin mocks**: El test crea dentro de la base de test una función y un trigger temporales `BEFORE INSERT ON appointment_status_change` que lanzan una excepción cuando `NEW.appointment_id = '00000000-0000-0000-0000-000000000a02'`; ejecuta `book_appointment` para `a02`; comprueba que el servicio propaga la excepción y que no queda ninguna fila en `appointment` ni en `appointment_status_change` para `a02`; y en un bloque `finally` elimina el trigger y la función. Queda estrictamente prohibido usar `unittest.mock`, `patch` o `monkeypatch`.

### D6 — Historial append-only: repositorio sin mutaciones y trigger PostgreSQL

1. El repositorio de historial (`AppointmentStatusChangeRepository` o métodos en `AppointmentRepository`) expone únicamente lecturas (`list_by_appointment_id`, `get_by_id`) e inserciones internas durante la transacción de turno. No existen métodos `update`, `delete` ni `bulk_delete`.
2. En la migración de base de datos se crea una función PL/pgSQL y un trigger defensivo:
   ```sql
   CREATE OR REPLACE FUNCTION prevent_appointment_status_change_modification()
   RETURNS TRIGGER AS $$
   BEGIN
       RAISE EXCEPTION 'appointment_status_change is append-only: updates and deletes are forbidden';
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER tr_appointment_status_change_append_only
   BEFORE UPDATE OR DELETE ON appointment_status_change
   FOR EACH ROW EXECUTE FUNCTION prevent_appointment_status_change_modification();
   ```
3. El `downgrade` de la migración elimina el trigger y la función.

### D7 — Sin restricciones `EXCLUDE` en PostgreSQL (DD-03)

No se agregan constraints `EXCLUDE USING gist` ni se instala la extensión `btree_gist`. El bloqueo pesimista `SELECT ... FOR UPDATE` (D4) previene colisiones concurrentes y permite que el dominio puro sea la autoridad (RN-GL-01) emitiendo mensajes de conflicto ricos con IDs de turno en conflicto (RN-AG-12).

### D8 — Implementación SQL de `AppointmentReader` de C-16

En `backend/app/repositories/appointment.py`, la clase `SqlAppointmentReader` (o `AppointmentRepository`) implementa el protocolo `AppointmentReader`:
```python
def list_for_professional_in_range(
    self, professional_id: UUID, start_at: datetime, end_at: datetime
) -> Sequence[Appointment]:
```
Ejecuta una consulta SQL con `WHERE professional_id = :prof_id AND start_at < :end_at AND end_at > :start_at`, mapea las filas a `Appointment` del dominio con instantes en UTC y las devuelve ordenadas por `(start_at, id)`. Conecta `BlockRepository.list_affected_appointments(block)` directamente a PostgreSQL.

### D9 — Prueba de concurrencia real sin `time.sleep`, con sondeo en `pg_locks` y `lock_timeout`

Para probar la serialización concurrente sin mocks, sin monkeypatch y de forma determinista y rápida:
1. En las sesiones del test de integración se ejecuta `SET lock_timeout = '5s'` para evitar que ningún test quede colgado si ocurriera una falla imprevista.
2. Dos hilos ejecutan transacciones contra `<POSTGRES_DB>_test` usando conexiones separadas (conexión A y conexión B).
3. **Control del bloqueo sin sleep**: La conexión A ejecuta la operación pasando `auto_commit=False` al servicio (o iniciando una transacción explícita sobre la sesión), de modo que toma el lock `FOR UPDATE` sobre profesional, sillón o turno y realiza el flush, pero retiene la transacción y el bloqueo abiertos.
4. Para confirmar que la conexión B está efectivamente bloqueada esperando por el lock de A antes de que A confirme, el test realiza un sondeo acotado (bucle `poll` de hasta 2 segundos con intervalos de 20 ms) consultando la vista del sistema `pg_locks` / `pg_stat_activity` verificando que la transacción de B se encuentra en espera de bloqueo (`wait_event_type = 'Lock'`).
5. Una vez comprobado en PostgreSQL que B está en espera, el test ejecuta `session_a.commit()`, liberando el lock para que B se desbloquee sin recurrir a `time.sleep` ciego. B procede, relee el estado actualizado de la base y el dominio lo rechaza con `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` o `INVALID_TRANSITION`.

### D10 — Revisión de Alembic y seed de desarrollo

- Migración única: `20261105_04_turnos_e_historial` encadenada a `20261104_03_horarios_y_bloqueos`.
- `seed_database()` no carga turnos de ejemplo: la agenda permanece limpia según KB 04 §Seed data inicial.

### D11 — Relectura bloqueada de turno en transiciones concurrentes

En `change_appointment_status`, `cancel_appointment` y `reschedule_appointment`, el servicio ejecuta primero `SELECT id, status FROM appointment WHERE id = :id FOR UPDATE` y reconstruye el estado actual del turno **dentro del bloqueo** antes de llamar al dominio:
- **Motivo**: Si dos recepcionistas intentan confirmar y cancelar el mismo turno a la vez, ambas leerían previamente `reservado`. Al serializarse por el lock de fila, la primera cambia el turno a `cancelado`; la segunda relee el turno (ahora en `cancelado`), llama al dominio con ese estado y el dominio rechaza la confirmación con `INVALID_TRANSITION`, dejando exactamente una sola entrada en el historial en lugar de dos transiciones divergentes desde el mismo estado.
- Si el turno no existe en la base, el servicio devuelve `None` inmediatamente sin lanzar excepciones.

### D12 — Aislamiento de metadatos de persistencia (`created_at` y `updated_at`)

`created_at` y `updated_at` son columnas de la tabla `appointment` requeridas por la base relacional, pero no forman parte del tipo de dominio `Appointment`. El repositorio no los expone en `Appointment` y mapea limpiamente entre la fila y el dataclass inmutable del dominio.

## Risks / Trade-offs

- **[Riesgo] Deadlocks por concurrencia entre profesional y sillón** → **Mitigación**: Ordenar lexicográficamente por UUID todas las claves a bloquear antes de ejecutar `SELECT ... FOR UPDATE` (D4).
- **[Riesgo] Transición concurrente conflictiva en el mismo turno** → **Mitigación**: Bloquear la fila del turno y releer su estado dentro del lock antes de evaluar la regla de transición (D11).
- **[Riesgo] Test de concurrencia colgado por fallo de conexión** → **Mitigación**: `SET lock_timeout = '5s'` en cada conexión de test de integración y sondeo acotado sobre `pg_locks` sin `time.sleep` (D9).
- **[Riesgo] Modificación accidental del historial por queries directas** → **Mitigación**: Trigger `tr_appointment_status_change_append_only` en PostgreSQL (D6).

## Migration Plan

1. Crear modelos declarativos `AppointmentModel` y `AppointmentStatusChangeModel`.
2. Crear migración `20261105_04_turnos_e_historial` con índices, constraints y trigger append-only.
3. Implementar `AppointmentRepository` y `SqlAppointmentReader`.
4. Implementar servicios transaccionales en `backend/app/services/appointments.py`.
5. Probar ciclo de migración (`upgrade head` → `downgrade -1` → `upgrade head`) y suite de integración con concurrencia real.

## Verificación manual

```powershell
alembic upgrade head
pytest
pytest -m integration
alembic downgrade -1
alembic upgrade head
mypy --strict app tests
openspec validate persistencia-turnos-e-historial --strict
git diff --check
```
