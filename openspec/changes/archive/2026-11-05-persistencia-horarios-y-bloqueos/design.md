# Design

## Context

C-05 y C-06 proveen las entidades inmutables `WorkingHours` y `Block` y las funciones puras `validate_working_hours`, `validate_block`, `check_working_hours`, `check_blocks` y `appointments_affected_by_block`. C-14 y C-15 proveen `Base` con `NAMING_CONVENTION`, la sesión SQLAlchemy 2.x en UTC, la migración `20261103_02_catalogos_y_pacientes`, los repositorios de catálogos y pacientes, `CatalogResult[T]`, `demo_data.py`, `seed.py` y las fixtures de integración sobre `<POSTGRES_DB>_test`. La motivación y el alcance se describen en `proposal.md`; los contratos verificables están en el delta de `database-infrastructure`.

## Goals / Non-Goals

**Goals:**

- Mantener aislados el dominio, los modelos declarativos SQLAlchemy y los repositorios.
- Persistir `working_hours` (minutos locales desde las `00:00` y `weekday` ISO `1..7`) y `block` (`start_at` y `end_at` en `timestamptz` UTC, `reason` opcional) con restricciones de integridad y claves foráneas a `professional.id`.
- Ejecutar siempre primero `validate_working_hours` y `validate_block` antes de escribir en la base.
- Exponer `AppointmentReader` en `contracts.py` y `BlockRepository.list_affected_appointments(block: Block) -> tuple[Appointment, ...]` sin acoplar C-16 a la tabla `appointment` de C-17.
- Proveer la migración reversible `20261104_03_horarios_y_bloqueos` y extender el seed idempotente con 25 tramos horarios ficticios.
- Cubrir todos los escenarios con tests unitarios y de integración real sobre `<POSTGRES_DB>_test`.

**Non-Goals:**

- Modificar `WorkingHours`, `Block` o las reglas de `backend/app/domain/rules/` (únicamente se agregan `Block` y `tuple[WorkingHours, ...]` a las restricciones del `TypeVar` `T` en `backend/app/domain/catalog/result.py`).
- Crear las tablas `appointment` o `appointment_status_change` (pertenecen a C-17).
- Implementar el lector SQL de turnos para `AppointmentReader` (pertenece a C-17).
- Agregar endpoints FastAPI, esquemas Pydantic HTTP o autenticación JWT (pertenecen a C-21).
- Precargar bloqueos en `seed.py`.

## Decisions

### D1 — Esquema de tablas, columnas y clave primaria de `working_hours` y `block`

En `backend/app/db/models.py` se agregarán dos modelos declarativos sobre `Base`:

- `WorkingHoursModel` (`__tablename__ = "working_hours"`):
  - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` — clave primaria UUID subrogada exclusiva de persistencia, generada con `uuid4()` en el repositorio al insertar cada fila. El tipo del dominio `WorkingHours(professional_id, weekday, start_minute, end_minute)` permanece sin campo `id`.
  - `professional_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id"), nullable=False)`.
  - `weekday: Mapped[int] = mapped_column(Integer, nullable=False)`.
  - `start_minute: Mapped[int] = mapped_column(Integer, nullable=False)`.
  - `end_minute: Mapped[int] = mapped_column(Integer, nullable=False)`.
- `BlockModel` (`__tablename__ = "block"`):
  - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` — toma `block.id` del dominio.
  - `professional_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id"), nullable=False)`.
  - `start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
  - `end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
  - `reason: Mapped[str | None] = mapped_column(String(255), nullable=True)`.

Se descarta una clave primaria compuesta en `working_hours` porque se aparta de `knowledge-base/04_modelo_de_datos.md` (`id UUID PK`), y se descarta agregar `id` a `WorkingHours` en el dominio porque es un objeto de valor sin identidad propia en las reglas de C-05.

### D2 — Representación de horarios (`working_hours`) e instantes de bloqueos (`block`)

En `working_hours`, `weekday` se guarda como `INTEGER` ISO (`1` = lunes … `7` = domingo) y `start_minute` / `end_minute` como `INTEGER` en minutos locales desde las `00:00` (`0..1440`, donde `1440` = `24:00`): es exactamente la misma representación que `WorkingHours` en el dominio y la base no convierte nada.

En `block`, `start_at` y `end_at` se guardan en `TIMESTAMPTZ` (`DateTime(timezone=True)`). `Block.__post_init__` ya normaliza los instantes a UTC y la sesión PostgreSQL opera en `TIME ZONE 'UTC'`. Al reconstruir `Block` desde una fila, los instantes conservan zona UTC.

Se descarta `TIME WITHOUT TIME ZONE` en `working_hours` porque `datetime.time` en Python no admite `24:00` (`1440`), y se descarta convertir los minutos laborales a UTC porque contradice DD-07 y RN-GL-03.

### D3 — Restricciones en la base de datos (`CHECK`, `UNIQUE`, `FOREIGN KEY`, índices) vs. validación en el dominio

Los repositorios ejecutarán siempre primero la validación del dominio (`validate_working_hours` y `validate_block`) y además la base declarará las siguientes restricciones e índices con `NAMING_CONVENTION`:

1. En `working_hours`:
   - `ForeignKey("professional.id")` → `fk_working_hours_professional_id_professional`.
   - `CheckConstraint("weekday >= 1 AND weekday <= 7", name="weekday_range")` → `ck_working_hours_weekday_range`.
   - `CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND start_minute < end_minute", name="minute_range")` → `ck_working_hours_minute_range`.
   - `UniqueConstraint("professional_id", "weekday", "start_minute", name="uq_working_hours_professional_weekday_start")`.
   - `Index("ix_working_hours_professional_id_weekday", "professional_id", "weekday")`.
2. En `block`:
   - `ForeignKey("professional.id")` → `fk_block_professional_id_professional`.
   - `CheckConstraint("start_at < end_at", name="interval_order")` → `ck_block_interval_order`.
   - `Index("ix_block_professional_id_start_at_end_at", "professional_id", "start_at", "end_at")`.

El no-solapamiento entre tramos del mismo profesional y día lo garantiza `validate_working_hours` al reemplazar el conjunto completo en una sola transacción.

### D4 — Operaciones, semántica de guardado y tipos de retorno de `WorkingHoursRepository` y `BlockRepository`

La generalización de `CatalogResult` se limita estrictamente a sumar `Block` y `tuple[WorkingHours, ...]` a las restricciones del `TypeVar` `T` en `backend/app/domain/catalog/result.py`:

```python
T = TypeVar(
    "T",
    Professional,
    Chair,
    Service,
    Patient,
    Block,
    tuple[WorkingHours, ...],
)
```

Ningún otro código de C-09 ni de C-15 cambia.

- `WorkingHoursRepository`:
  - `replace_for_professional(professional_id: UUID, slots: Sequence[WorkingHours]) -> CatalogResult[tuple[WorkingHours, ...]]`: verifica que ningún elemento de `slots` tenga un `professional_id` distinto del parámetro (`ValueError` si difiere), valida el conjunto nuevo completo con `validate_working_hours(slots)` antes de escribir (si hay violaciones, devuelve `Rejected(tuple(violations))` sin borrar ni insertar nada), y dentro de una sola transacción (`begin_nested()`) borra los tramos anteriores del profesional e inserta los nuevos. Acepta la secuencia vacía `()` (el profesional no atiende ningún día, devolviendo `Ok(())`). Devuelve `Ok` con la tupla ordenada por `(weekday, start_minute)`.
  - `list_by_professional(professional_id: UUID) -> tuple[WorkingHours, ...]`: devuelve los tramos del profesional ordenados por `(weekday, start_minute)`.
  - `list() -> tuple[WorkingHours, ...]`: devuelve todos los tramos ordenados por `(professional_id, weekday, start_minute)`.
- `BlockRepository`:
  - `create(candidate: Block) -> CatalogResult[Block]`: valida primero con `validate_block(candidate)` (si hay violaciones, devuelve `Rejected(tuple(violations))` sin escribir), inserta la fila en `begin_nested()` y devuelve `Ok(candidate)`.
  - `delete(identifier: UUID) -> Block | None`: busca la fila por `id`; si no existe devuelve `None` (igual que `deactivate` en C-15); si existe, construye el `Block` del dominio, elimina la fila con `flush()` y devuelve el `Block` borrado.
  - `get_by_id(identifier: UUID) -> Block | None`.
  - `list_by_professional(professional_id: UUID) -> tuple[Block, ...]`: ordenado por `(start_at, id)`.
  - `list() -> tuple[Block, ...]`: ordenado por `(start_at, id)`.
  - `list_affected_appointments(block: Block) -> tuple[Appointment, ...]` (ver D6).

### D5 — Existencia del profesional y traducción de errores de integridad

1. Un profesional inactivo (`active=False`) **sí** puede tener horarios de atención y bloqueos guardados y conservados en la base.
2. El rechazo `UNKNOWN_REFERENCE` se detecta por el nombre de la constraint de clave foránea en el `IntegrityError` de PostgreSQL (`_constraint_name(error) == "fk_working_hours_professional_id_professional"` en `WorkingHoursRepository` y `_constraint_name(error) == "fk_block_professional_id_professional"` en `BlockRepository`), siguiendo el mismo mecanismo de C-15:
   ```python
   Rejected(
       (
           Violation(
               code=ViolationCode.UNKNOWN_REFERENCE,
               message=(
                   "El profesional indicado no existe "
                   f"(id {professional_id})."
               ),
               reference_kind=ReferenceKind.PROFESSIONAL,
           ),
       )
   )
   ```
   El repositorio produce exactamente ese texto, con el mismo formato que `references.py`, y el test compara el mensaje completo.
   En `replace_for_professional(professional_id, ())` con lista vacía —donde un `DELETE` + `0 INSERT` no dispararía la FK por sí solo—, el repositorio verifica la existencia de la fila en `professional` (o rechaza con ese mismo `UNKNOWN_REFERENCE` si no existe) para mantener el mismo contrato incluso cuando `slots` es vacío.
3. Cualquier otro `IntegrityError` (por ejemplo, `pk_block` duplicado o una violación de `CHECK`) se propaga sin `catch` amplio.

### D6 — Contrato `AppointmentReader` y consulta de turnos afectados (`list_affected_appointments`)

En `backend/app/repositories/contracts.py`:

- Se agrega el protocolo `AppointmentReader` con un único método:
  ```python
  class AppointmentReader(Protocol):
      def list_for_professional_in_range(
          self,
          professional_id: UUID,
          start_at: datetime,
          end_at: datetime,
      ) -> Sequence[Appointment]: ...
  ```
- La firma definitiva en `BlockRepository` (tanto en `contracts.py` como en la implementación SQL) es:
  ```python
  def list_affected_appointments(self, block: Block) -> tuple[Appointment, ...]: ...
  ```
  **sin** parámetro `appointments`.
- La implementación SQL de `BlockRepository` recibe obligatoriamente `appointment_reader: AppointmentReader` en `__init__(self, session: Session, appointment_reader: AppointmentReader)`, sin lector vacío implícito. Un lector vacío por defecto haría que `list_affected_appointments` respondiera silenciosamente `"sin turnos afectados"` si alguien olvida pasarlo. Al invocar `list_affected_appointments(block)`, si `block.start_at >= block.end_at` devuelve `()`; en caso contrario pide candidatos a `appointment_reader.list_for_professional_in_range(block.professional_id, block.start_at, block.end_at)` y filtra y ordena con `appointments_affected_by_block(block, candidates)` del dominio. Los tests que solo hacen CRUD de bloqueos pasan explícitamente un fake cuyo lector devuelve `()`.
- En C-16 los tests usan un fake escrito a mano en `tests/` (una clase que implementa `AppointmentReader` y devuelve una tupla fija de `Appointment`, sin `unittest.mock` ni `monkeypatch`). La implementación SQL de `AppointmentReader` pertenece a C-17 y la firma de `list_affected_appointments(block: Block) -> tuple[Appointment, ...]` no cambiará.

### D7 — Datos ficticios en `demo_data.py` y extensión del seed idempotente en `seed.py`

En `backend/app/demo_data.py` se agrega `WORKING_HOURS: tuple[WorkingHours, ...]` con 25 tramos ficticios de lunes a viernes (`weekday` `1..5`):

- `00000000-0000-0000-0000-000000000001` (Dra. Laura Quiroga): `540..780` (`09:00–13:00`) y `900..1140` (`15:00–19:00`) de lunes a viernes (10 tramos).
- `00000000-0000-0000-0000-000000000002` (Dr. Martín Sosa): solo mañanas `540..780` (`09:00–13:00`) de lunes a viernes (5 tramos, cumpliendo la variación para pruebas de KB 04).
- `00000000-0000-0000-0000-000000000003` (Dra. Paula Benítez): `540..780` (`09:00–13:00`) y `900..1140` (`15:00–19:00`) de lunes a viernes (10 tramos).

No se siembran bloqueos. En `backend/app/db/seed.py`, `_seed_working_hours(session)` verifica para cada profesional de `PROFESSIONALS` si `working_hours_repository.list_by_professional(professional.id)` está vacío; solo en ese caso inserta sus tramos de `WORKING_HOURS` mediante `replace_for_professional`. Si un profesional ya tiene al menos un tramo en `working_hours`, el seed no le inserta ni le modifica nada; la segunda ejecución inserta `0` tramos. `seed_database` incluye `"working_hours": len(WorkingHoursRepository(session).list())` en el diccionario de conteos devuelto.

### D8 — Revisión de Alembic

Se creará una única migración `20261104_03_horarios_y_bloqueos` en `backend/alembic/versions/20261104_03_horarios_y_bloqueos.py` con `down_revision = "20261103_02_catalogos_y_pacientes"`. Su `upgrade()` creará `working_hours` y `block` con todas sus constraints e índices; su `downgrade()` eliminará los índices y ambas tablas en orden inverso.

### D9 — Estrategia de tests unitarios y de integración

- Suite unitaria por defecto (`pytest`):
  - `tests/test_persistence_metadata.py`: tablas `working_hours` y `block`, tipos de columnas, claves foráneas, `CHECK`, `UNIQUE` e índices.
  - `tests/test_repository_contracts.py`: firmas tipadas de `AppointmentReader`, `WorkingHoursRepository` y `BlockRepository` con tipos del dominio.
  - `tests/domain/test_catalog.py`: validez de los 25 tramos de `WORKING_HOURS` en `demo_data.py` con `validate_working_hours`.
- Suite de integración (`pytest -m integration` sobre `<POSTGRES_DB>_test` con rollback por test):
  - `tests/integration/test_availability_persistence.py`: todos los escenarios del delta de `database-infrastructure`, incluyendo el fake manual de `AppointmentReader` para US-011 CA-3 y la liberación del horario al borrar un bloqueo para US-011 CA-4.
  - Ajuste de la revisión `head` esperada en `tests/integration/test_database_infrastructure.py` (`20261104_03_horarios_y_bloqueos`) y del cleanup/conteo del seed en `tests/integration/test_catalog_persistence.py`.

## Risks / Trade-offs

- **[Riesgo]** Al reemplazar horarios de un profesional para un `professional_id` inexistente con `slots = ()` (lista vacía), no se ejecuta ningún `INSERT` y PostgreSQL no dispararía la FK por sí solo.
  **Mitigación:** Cuando `slots` es vacío, comprobar que el profesional exista en `professional` antes de confirmar el reemplazo; cuando `slots` no es vacío, el `INSERT` dentro del savepoint dispara `fk_working_hours_professional_id_professional` y se traduce a `UNKNOWN_REFERENCE`.
- **[Riesgo]** Los tests de integración de C-15 que ejecutan `DELETE FROM professional` pueden fallar por clave foránea una vez que `seed_database` inserta filas en `working_hours`.
  **Mitigación:** Incluir `DELETE FROM block` y `DELETE FROM working_hours` antes de `DELETE FROM professional` en los helpers de limpieza del seed.
- **[Riesgo]** Si `replace_for_professional` borrara los tramos previos y fallara un `INSERT` posterior, el profesional perdería sus horarios anteriores.
  **Mitigación:** Validar primero todo el lote con `validate_working_hours` y envolver el `DELETE` + `INSERT` en `with self._session.begin_nested():`.

## Migration Plan

1. Ampliar `demo_data.py`, `result.py` y `contracts.py` siguiendo ciclos TDD (RED → GREEN → REFACTOR).
2. Agregar `WorkingHoursModel` y `BlockModel` en `backend/app/db/models.py` y crear la migración `20261104_03_horarios_y_bloqueos`.
3. Implementar `WorkingHoursRepository` y `BlockRepository` y sus tests de integración sobre `<POSTGRES_DB>_test`.
4. Extender `seed.py` con `_seed_working_hours` y verificar su idempotencia en dos ejecuciones consecutivas.
5. Verificar el ciclo `upgrade head`, `downgrade base` y `upgrade head` dejando la base en `20261104_03_horarios_y_bloqueos`.

## Verificación manual

Desde la raíz:

```powershell
docker compose up -d
```

Desde `backend/`:

```powershell
alembic upgrade head
python -m app.db.seed
python -m app.db.seed
pytest
pytest -m integration
alembic downgrade base
alembic upgrade head
mypy --strict app tests
```

Desde la raíz:

```powershell
openspec validate persistencia-horarios-y-bloqueos --strict
git diff --check
```

## Desvíos del apply

- La primera ejecución de las nuevas pruebas unitarias quedó en RED por las
  ausencias esperadas de `WORKING_HOURS`, los protocolos y los modelos de
  disponibilidad; luego pasó en GREEN con la implementación mínima.
- Se realizó una ronda posterior de mutación sobre los 19 escenarios. Cada
  mutación se aplicó solo en producción, se ejecutó únicamente el test
  correspondiente y se restauró antes de continuar. Las mutaciones cubrieron
  orden y UTC, reemplazo y rollback, validaciones, CHECK y FK, propagación de
  errores, profesionales inactivos, eliminación, filtrado de turnos, seed y
  migración reversible.
- La mutación de reemplazo aislado no falló en la primera versión del test
  porque solo verificaba al profesional P2. Se reforzó con la aserción del
  listado final de P1; al repetir la mutación, el test falló. Las 19
  mutaciones finales fallaron y todas fueron restauradas.
- No se modificó el dominio fuera del `TypeVar` de `result.py` y la extracción de `unknown_reference_violation` en `references.py`; no se usó `type: ignore`, ni mocks, `patch` o `monkeypatch`.
- Correcciones posteriores de la autora:
  1. Separación de tests de migración en `test_database_infrastructure.py`: `test_migration_cycle_restores_test_database_to_head` recuperó la cobertura de `downgrade "base"` (verificando que no queda ninguna tabla de la aplicación: `professional`, `chair`, `service`, `patient`, `working_hours` ni `block`), y se agregó `test_availability_migration_downgrade_minus_one_cycle` como test específico para el ciclo reversible de un paso (`downgrade "-1"`).
  2. Eliminación de código muerto en `BlockRepository`: se removió `_as_aware_datetime` usando `row.start_at` y `row.end_at` directamente; se repitió la mutación del escenario 2 forzando `reason=None` en `_to_domain`, registrando el fallo en `AssertionError` y restaurando.
  3. Fuente única para violaciones y nombres de constraint: se extrajo `unknown_reference_violation(kind, reference_id)` en `backend/app/domain/rules/references.py` (usada por `_check_reference`, `blocks.py` y `working_hours.py`), y se centralizó `constraint_name` en `backend/app/repositories/_integrity.py` eliminando las cuatro copias locales en `catalog.py`, `patients.py`, `blocks.py` y `working_hours.py`.
