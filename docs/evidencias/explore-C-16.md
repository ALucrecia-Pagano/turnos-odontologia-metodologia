# Explore C-16 — `persistencia-horarios-y-bloqueos`

Fecha: 2026-11-04
Fase: 4 — Infraestructura y persistencia (Docker Compose, PostgreSQL, SQLAlchemy, Alembic) · Grupo 4C
Governance: **MEDIO** (implementar con puntos de control; presentar decisiones no obvias para revisión)
Dependencias en `CHANGES.md`: `C-15` (`persistencia-catalogos-y-pacientes`), `C-05` (`horario-atencion-profesional`) y `C-06` (`bloqueos-de-agenda`) — todas completadas y archivadas.

---

## 1. Alcance de C-16 según `CHANGES.md` y qué queda afuera

### Qué entra en C-16

El objetivo de C-16 es conectar las reglas y entidades de disponibilidad del dominio puro (`WorkingHours` de C-05 y `Block` de C-06) con PostgreSQL mediante modelos declarativos SQLAlchemy 2.x, una migración reversible de Alembic y repositorios tipados que mantengan al dominio como única autoridad de validación (RN-GL-01, DD-03).

En concreto, C-16 comprende:

1. **Modelos SQLAlchemy 2.x en `backend/app/db/models.py`**:
   - Tabla `working_hours` vinculada a `professional.id`, almacenando el día de la semana ISO (`1..7`) y el tramo `[start_minute, end_minute)` en minutos desde las `00:00` en hora local (`America/Argentina/Buenos_Aires`, DD-07).
   - Tabla `block` vinculada a `professional.id`, almacenando el intervalo semiabierto `[start_at, end_at)` en `timestamptz` (UTC, DD-07) y el motivo opcional (`reason`).
2. **Migración Alembic reversible en `backend/alembic/versions/`**:
   - Revisión encadenada a `20261103_02_catalogos_y_pacientes` (C-15) que crea `working_hours` y `block` con sus claves primarias, claves foráneas a `professional.id`, restricciones `CHECK` e índices respetando `NAMING_CONVENTION` de `Base.metadata`, y cuyo `downgrade` revierte limpiamente el esquema.
3. **Repositorios de horarios y bloqueos en `backend/app/repositories/`**:
   - Reciben y devuelven exclusivamente tipos del dominio (`WorkingHours`, `Block`, resultados tipados `Ok` / `Rejected` con `Violation`), sin filtrar filas ORM hacia afuera.
   - Todo guardado pasa primero por la validación pura del dominio: `validate_working_hours` (C-05: RN-DI-01, RN-DI-02) para los horarios y `validate_block` (C-06: RN-DI-03, `start_at < end_at`) para los bloqueos.
   - Soporte para eliminar un bloqueo existente (`delete`), de modo que deje de participar en `check_blocks` y libere el horario (US-011 CA-4).
4. **Interfaz de consulta de turnos afectados al crear un bloqueo (`appointments_affected_by_block` de C-06)**:
   - Según `CHANGES.md` §[C-16], la consulta contra la tabla `appointment` se completa en C-17, pero en C-16 queda expuesta la interfaz en el repositorio/contrato y se prueba con datos de prueba (reutilizando `appointments_affected_by_block` de C-06 para verificar RN-DI-04 / SU-05 / US-011 CA-3).
5. **Datos ficticios y seed idempotente (`backend/app/demo_data.py` y `backend/app/db/seed.py`)**:
   - Extensión con los horarios de atención semanales ficticios previstos en `knowledge-base/04_modelo_de_datos.md` (§Seed data inicial), manteniendo la ejecución manual e idempotente de `python -m app.db.seed`.
6. **Tests automatizados (unitarios de metadata/contratos + integración sobre `<POSTGRES_DB>_test`)**:
   - Ida y vuelta (`round-trip`) de horarios y bloqueos, rechazo de horarios inválidos o solapados, rechazo de bloqueo inválido, liberación del horario al eliminar un bloqueo (US-011 CA-4), prueba de la interfaz de turnos afectados, idempotencia del seed y ciclo completo de migración (`upgrade head` → `downgrade` → `upgrade head`) con `compare_metadata` vacío.

### Qué queda explícitamente afuera

- **De C-17 (`persistencia-turnos-e-historial`)**:
  - Tablas `appointment` y `appointment_status_change` y su migración Alembic.
  - Repositorio de turnos e historial (`AppointmentRepository`), transacción atómica turno + `AppointmentStatusChange` (RN-GL-02) y bloqueo pesimista `SELECT ... FOR UPDATE` sobre las filas de `professional` y `chair` (DD-03).
  - La consulta SQL real contra la tabla `appointment` para obtener los turnos activos que pisa un bloqueo nuevo (en C-16 se expone el contrato y se prueba con turnos en memoria/datos de prueba; en C-17 se conecta a la tabla `appointment`).
- **De C-18 (`persistencia-usuarios`)**:
  - Tabla `user`, hash de contraseñas y repositorio de usuarios para autenticación JWT.
- **De C-21 (`api-horarios-bloqueos-y-disponibilidad`)**:
  - Endpoints HTTP FastAPI (`PUT/GET /api/professionals/{id}/working-hours`, `POST/GET/DELETE /api/professionals/{id}/blocks`, `GET /api/availability`), esquemas Pydantic de entrada/salida, traducción a códigos HTTP (`409` / `422` / `404`), control de acceso por rol JWT (`Actor` / `Role`, donde un Odontólogo solo edita su propia disponibilidad según RN-AC-01) y cálculo de huecos libres.
- **Del paquete de dominio (`backend/app/domain/`)**:
  - No se modifican las dataclasses `WorkingHours` ni `Block`, ni las funciones de `backend/app/domain/rules/working_hours.py` y `backend/app/domain/rules/blocks.py`, ni la guardia de dependencias/reloj (`domain-dependency-guard`).

---

## 2. Estado actual

### 2.1. Tipos y reglas del dominio a persistir

| Elemento en `app.domain` | Ubicación | Campos / Firma | Invariantes y comportamiento actual |
|--------------------------|-----------|----------------|-------------------------------------|
| `WorkingHours` | `app/domain/model.py:210-229` | `professional_id: UUID`, `weekday: int`, `start_minute: int`, `end_minute: int` (`@dataclass(frozen=True, slots=True)`) | **No tiene campo `id` en el dominio.** No valida en `__post_init__` porque los tramos los carga el usuario y los evalúa `validate_working_hours`. `weekday` usa ISO (`1` = lunes … `7` = domingo); `start_minute` y `end_minute` son minutos locales desde las `00:00` (`540` = `09:00`, `1440` = `24:00`). |
| `validate_working_hours(slots)` | `app/domain/rules/working_hours.py:80-126` | `slots: Sequence[WorkingHours] -> list[Violation]` | Primero emite una `INVALID_WORKING_HOURS` por cada tramo inválido (`weekday` fuera de `1..7`, minutos fuera de `0..1440` o `start_minute >= end_minute`), numerando desde 1 según el orden recibido (`"El tramo {pos} no es válido: ..."`). Luego, entre los tramos válidos del mismo `professional_id` y `weekday`, emite una `OVERLAPPING_WORKING_HOURS` por cada par que comparta algún minuto (`start_a < end_b and start_b < end_a`). Tramos contiguos (`end_a == start_b`) son válidos. |
| `check_working_hours(...)` | `app/domain/rules/working_hours.py:176-222` | `(professional_id, start_at, end_at, working_hours, tz, professional_name) -> list[Violation]` | Filtra los tramos del `professional_id` y del `weekday` local del turno, une tramos contiguos (`_merged_slots`) y devuelve `OUTSIDE_WORKING_HOURS` si el turno no cabe completo en ningún tramo unido. |
| `Block` | `app/domain/model.py:232-260` | `id: UUID`, `professional_id: UUID`, `start_at: datetime`, `end_at: datetime`, `reason: str \| None = None` (`@dataclass(frozen=True, slots=True)`) | En `__post_init__` exige que `start_at` y `end_at` tengan zona horaria (`ValueError` si son *naive*) y los normaliza a UTC con `_to_utc`. **No** valida `start_at < end_at` en `__post_init__`: esa regla de negocio la decide `validate_block`. |
| `validate_block(block)` | `app/domain/rules/blocks.py:24-39` | `block: Block -> list[Violation]` | Si `block.start_at >= block.end_at`, devuelve `[Violation(code=ViolationCode.INVALID_BLOCK, message="El bloqueo no es válido: el inicio debe ser anterior al fin.")]`; si no, `[]`. No exige grilla de 5 minutos y permite que dos bloqueos del mismo profesional se solapen. |
| `check_blocks(...)` | `app/domain/rules/blocks.py:71-108` | `(professional_id, start_at, end_at, blocks, tz, professional_name) -> list[Violation]` | Filtra los bloqueos válidos (`start_at < end_at`) del profesional que se solapan con `[start_at, end_at)`, ordenados por `(start_at, str(id))`, y devuelve una `BLOCKED_TIME` por cada uno con `conflicting_block_id` y `conflicting_interval`. |
| `appointments_affected_by_block(block, appointments)` | `app/domain/rules/blocks.py:134-162` | `(block: Block, appointments: Sequence[Appointment]) -> list[Appointment]` | Devuelve, ordenados por `(start_at, str(id))`, los turnos del mismo `professional_id` cuyo estado está en `OCCUPYING_STATUSES` (`reservado`, `confirmado`, `atendido`) y cuyo intervalo se solapa con `[block.start_at, block.end_at)`. No modifica ni cancela los turnos (RN-DI-04, SU-05). Si `block.start_at >= block.end_at`, devuelve `[]`. |

### 2.2. Qué ya existe en la base de datos y en la capa de persistencia (C-13, C-14 y C-15)

- **Motor y sesiones (`backend/app/db/session.py`)**:
  - `create_database_engine(settings)` registra un listener `connect` que ejecuta `SET TIME ZONE 'UTC'` en cada conexión PostgreSQL.
  - `database_url_for_test(settings)` apunta a `<POSTGRES_DB>_test` en `localhost:5432`.
- **Metadata y convención de nombres (`backend/app/db/base.py`)**:
  - `Base.metadata` define `NAMING_CONVENTION`:
    - `ix`: `ix_%(column_0_label)s`
    - `uq`: `uq_%(table_name)s_%(column_0_name)s`
    - `ck`: `ck_%(table_name)s_%(constraint_name)s`
    - `fk`: `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`
    - `pk`: `pk_%(table_name)s`
- **Modelos actuales (`backend/app/db/models.py`)**:
  - `ProfessionalModel` (`professional`), `ChairModel` (`chair`), `ServiceModel` (`service`) y `PatientModel` (`patient`).
  - `professional.id` ya existe como `Uuid(as_uuid=True)` PK (`pk_professional`), listo para ser referenciado por `ForeignKey("professional.id")` desde `working_hours` y `block`.
- **Migraciones Alembic (`backend/alembic/versions/`)**:
  - `20261103_01_baseline.py` (revisión base vacía).
  - `20261103_02_catalogos_y_pacientes.py` (amplía `alembic_version.version_num` a `VARCHAR(64)` y crea `professional`, `chair`, `service` y `patient`).
- **Repositorios y resultados (`backend/app/repositories/` y `backend/app/domain/catalog/result.py`)**:
  - `CatalogResult[T] = Ok[T] | Rejected`, donde `T` está restringido hoy a `TypeVar("T", Professional, Chair, Service, Patient)`.
  - `contracts.py` define `Protocol` para cada repositorio y `test_repository_contracts.py` verifica con `get_type_hints` que los métodos usan tipos del dominio.
  - `catalog.py` y `patients.py` usan `session.begin_nested()` (savepoints) al insertar con restricciones únicas e inspeccionan `error.orig.diag.constraint_name` para traducir únicamente la constraint esperada y propagar cualquier otro `IntegrityError`.
- **Datos ficticios y seed (`backend/app/demo_data.py` y `backend/app/db/seed.py`)**:
  - `demo_data.py` define `PROFESSIONALS` (3), `CHAIRS` (3), `SERVICES` (5) y `PATIENTS` (5) con UUIDs fijos (`00000000-0000-0000-0000-000000000001..003`, etc.).
  - `seed.py` expone `seed_database(settings)` y `python -m app.db.seed`, insertando de forma idempotente solo las filas faltantes dentro de `with session.begin():`.

---

## 3. Decisiones abiertas (`D1`–`D9`)

### D1 — Esquema de tablas, columnas y clave primaria de `working_hours` y `block`

- **Problema**: En `knowledge-base/04_modelo_de_datos.md`, tanto `WorkingHours` como `Block` figuran con `id UUID PK` y `professional_id FK`. Sin embargo, en `backend/app/domain/model.py`, `Block` tiene `id: UUID` mientras que `WorkingHours` es un valor inmutable `(professional_id, weekday, start_minute, end_minute)` **sin campo `id`**. Hay que definir cómo se modelan ambas tablas en `backend/app/db/models.py` sin contaminar el dominio con detalles de persistencia ni romper la paridad con la KB.
- **Opciones**:
  - **Opción A**:
    - `WorkingHoursModel` (`__tablename__ = "working_hours"`):
      - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` (clave primaria UUID generada con `uuid4()` en el repositorio al insertar cada fila, exclusiva de persistencia igual que `ProfessionalModel.license_number` y `ChairModel.name_normalized` en C-15).
      - `professional_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id"), nullable=False)`.
      - `weekday: Mapped[int] = mapped_column(Integer, nullable=False)`.
      - `start_minute: Mapped[int] = mapped_column(Integer, nullable=False)`.
      - `end_minute: Mapped[int] = mapped_column(Integer, nullable=False)`.
    - `BlockModel` (`__tablename__ = "block"`):
      - `id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)` (toma `block.id` del dominio).
      - `professional_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("professional.id"), nullable=False)`.
      - `start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
      - `end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)`.
      - `reason: Mapped[str | None] = mapped_column(String(255), nullable=True)`.
    - *Pros*: Cumple literalmente `knowledge-base/04_modelo_de_datos.md` (`id UUID PK` en ambas tablas), mantiene intacto `WorkingHours` en `app/domain/model.py` (sin tocar tests de C-05/C-08/C-11/C-12) y sigue el mismo patrón de aislamiento dominio-persistencia que aprobó C-15.
    - *Contras*: El repositorio genera `uuid4()` internamente al persistir filas de `working_hours`.
  - **Opción B**: Usar clave primaria compuesta `(professional_id, weekday, start_minute)` en `working_hours` sin columna `id`.
    - *Pros*: No requiere generar un UUID en el repositorio para `working_hours`.
    - *Contras*: Se aparta de `knowledge-base/04_modelo_de_datos.md` (§WorkingHours especifica `id UUID PK`).
  - **Opción C**: Agregar `id: UUID` al dataclass `WorkingHours` en `backend/app/domain/model.py`.
    - *Pros*: Simetría 1:1 entre columnas y campos del dataclass.
    - *Contras*: Rompe todos los constructores de `WorkingHours(prof_id, weekday, start, end)` en la suite de tests existente (C-05, C-08, C-11, C-12) y viola la decisión de diseño de C-05 donde un tramo horario es un valor sin identidad propia.
- **Recomendación**: **Opción A**. Respeta la KB (`id UUID PK` en `working_hours` y `block`), conserva `WorkingHours` inmutable y sin `id` en el dominio, y reutiliza el patrón de C-15 para columnas exclusivas de persistencia.

---

### D2 — Representación de horarios (`working_hours`) e instantes de bloqueos (`block`) en PostgreSQL

- **Problema**: Definir cómo se almacenan las horas de los tramos semanales (hora local en minutos vs. `TIME` o UTC) y los extremos de un bloqueo (`TIMESTAMPTZ` en UTC), garantizando que la lectura desde PostgreSQL reconstruya `WorkingHours` y `Block` con los valores exactos que esperan `check_working_hours` y `check_blocks`.
- **Opciones**:
  - **Opción A**:
    - En `working_hours`: guardar `weekday` como `INTEGER` ISO (`1` = lunes … `7` = domingo) y `start_minute` / `end_minute` como `INTEGER` en minutos desde las `00:00` de la hora local del consultorio (`0..1440`, donde `1440` representa las `24:00`), sin conversión a UTC.
    - En `block`: guardar `start_at` y `end_at` como `TIMESTAMPTZ` (`DateTime(timezone=True)`), que `Block.__post_init__` ya normaliza a UTC y que la sesión SQLAlchemy lee y escribe en UTC gracias al evento `SET TIME ZONE 'UTC'` de `session.py`. Al reconstruir `Block` desde la fila, asegurar `tzinfo=timezone.utc`.
    - *Pros*: Coincide con `CHANGES.md` §[C-16], KB 02/04, DD-07 y RN-GL-03; soporta `end_minute = 1440` (`24:00`) sin fricción con `datetime.time` de Python.
    - *Contras*: Ninguno.
  - **Opción B**: Guardar `start_minute` y `end_minute` como columnas `TIME WITHOUT TIME ZONE` en PostgreSQL.
    - *Pros*: Legibilidad directa en consultas SQL manuales (`09:00:00`).
    - *Contras*: `datetime.time` en Python no admite `24:00:00` (el máximo es `23:59:59`), por lo que rompería los escenarios de C-05 donde un tramo termina a las `24:00` (`end_minute = 1440`), además de contradecir KB 04 y `CHANGES.md` §[C-16].
  - **Opción C**: Convertir `start_minute` y `end_minute` a minutos UTC al guardar.
    - *Pros*: Todo el esquema estaría en UTC.
    - *Contras*: Contradice explícitamente DD-07, RN-GL-03 y KB 04, y un tramo como `21:00–24:00` hora Argentina cruzaría al día siguiente en UTC, rompiendo la correspondencia por `weekday`.
- **Recomendación**: **Opción A**. Es el diseño fijado por DD-07, RN-GL-03, KB 04 y `CHANGES.md` §[C-16].

---

### D3 — Restricciones en la base de datos (`CHECK`, `UNIQUE`, `FOREIGN KEY`, índices) vs. validación en el dominio

- **Problema**: Definir qué invariantes de `working_hours` y `block` se declaran como constraints e índices en PostgreSQL además de las validaciones puras `validate_working_hours` y `validate_block` del dominio.
- **Opciones**:
  - **Opción A**: Ejecutar siempre primero la validación del dominio en el repositorio y declarar en PostgreSQL las restricciones estructurales y de rango junto con los índices de la KB:
    1. En `working_hours`:
       - `ForeignKey("professional.id", ondelete="RESTRICT")` con nombre por convención `fk_working_hours_professional_id_professional`.
       - `CheckConstraint("weekday >= 1 AND weekday <= 7", name="weekday_range")` → `ck_working_hours_weekday_range`.
       - `CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND start_minute < end_minute", name="minute_range")` → `ck_working_hours_minute_range`.
       - `UniqueConstraint("professional_id", "weekday", "start_minute", name="uq_working_hours_professional_weekday_start")` (impide duplicar dos tramos con el mismo inicio para el mismo profesional y día e implícitamente indexa `(professional_id, weekday)`), más el índice `Index("ix_working_hours_professional_id_weekday", "professional_id", "weekday")` pedido en KB 04.
       - El no-solapamiento entre tramos distintos del mismo día (`start_a < end_b AND start_b < end_a`) lo garantiza `validate_working_hours` al guardar el conjunto completo del profesional en una única transacción.
    2. En `block`:
       - `ForeignKey("professional.id", ondelete="RESTRICT")` con nombre por convención `fk_block_professional_id_professional`.
       - `CheckConstraint("start_at < end_at", name="interval_order")` → `ck_block_interval_order`.
       - Índice compuesto `Index("ix_block_professional_id_start_at_end_at", "professional_id", "start_at", "end_at")` pedido en KB 04.
    - *Pros*: Protege la integridad referencial y los rangos/órdenes en la propia base (como hizo C-15 con `ck_patient_dni_format`), respeta los índices de KB 04 y no requiere extensiones de PostgreSQL fuera del estándar.
    - *Contras*: El solapamiento parcial entre dos tramos de `working_hours` (p. ej. `09:00–13:00` y `12:00–16:00`) se rechaza en el dominio/repositorio y no mediante un constraint de exclusión SQL.
  - **Opción B**: Agregar además un `ExcludeConstraint` con `int4range(start_minute, end_minute)` y la extensión `btree_gist` en PostgreSQL para impedir solapamientos de `working_hours` a nivel SQL.
    - *Pros*: Imposibilita tramos solapados incluso ante un `INSERT` manual directo en SQL.
    - *Contras*: Requiere `CREATE EXTENSION btree_gist` (no contemplada en C-13/C-14), complejiza el `compare_metadata` de Alembic y duplica la regla RN-DI-02 fuera del dominio.
  - **Opción C**: No declarar `CHECK` ni `UniqueConstraint` en PostgreSQL y dejar solo `PRIMARY KEY` y `FOREIGN KEY`.
    - *Pros*: Modelo SQL mínimo.
    - *Contras*: Contradice KB 04 (§WorkingHours y §Block documentan explícitamente los constraints `0 <= start_minute < end_minute <= 1440`, `start_at < end_at` y sus índices) y se aparta del criterio de C-15.
- **Recomendación**: **Opción A**. Combina la autoridad del dominio (RN-GL-01) con constraints `CHECK`, `FOREIGN KEY`, `UNIQUE` e índices explícitos y verificables con Alembic `compare_metadata`, sin requerir extensiones adicionales en PostgreSQL.

---

### D4 — Operaciones, semántica de guardado y tipos de retorno de `WorkingHoursRepository` y `BlockRepository`

- **Problema**:
  1. `validate_working_hours(slots: Sequence[WorkingHours])` valida el **conjunto** de tramos horarios como una unidad y numera los errores por posición desde 1 (`"El tramo 1 no es válido..."`, `"Los tramos 1 y 2 del lunes se solapan..."`). En la historia US-010 (y futuro endpoint `PUT /api/professionals/{id}/working-hours` de C-21), el horario semanal de un profesional se configura o actualiza como un conjunto de tramos. En cambio, los bloqueos (`Block`) tienen `id` propio, se dan de alta uno por uno (`POST`), se listan (`GET`) y se eliminan por `id` (`DELETE`, US-011 CA-4).
  2. Además, en `backend/app/domain/catalog/result.py`, `CatalogResult[T] = Ok[T] | Rejected` tiene hoy un `TypeVar("T", Professional, Chair, Service, Patient)` cerrado a las cuatro entidades de C-09. Hay que definir qué tipo devuelven las escrituras de `WorkingHoursRepository` y `BlockRepository`.
- **Opciones**:
  - **Opción A**:
    - **Tipo de resultado**: Ampliar `T` en `app/domain/catalog/result.py` (o relajar `T = TypeVar("T")` manteniendo el alias `CatalogResult` / exportando `RepositoryResult[T] = Ok[T] | Rejected`) para poder devolver `Ok[tuple[WorkingHours, ...]] | Rejected` y `Ok[Block] | Rejected` con el mismo `Ok(entity)` y `Rejected(violations)` ya usados en C-09 y C-15.
    - **`WorkingHoursRepository(session)`**:
      - `replace_for_professional(professional_id: UUID, slots: Sequence[WorkingHours]) -> CatalogResult[tuple[WorkingHours, ...]]`:
        1. Verifica que todos los elementos de `slots` tengan `slot.professional_id == professional_id` (si alguno tiene otro `professional_id`, lanza `ValueError` por precondición del llamador).
        2. Ejecuta `validate_working_hours(slots)`. Si devuelve violaciones, retorna `Rejected(tuple(violations))` sin tocar la base.
        3. Verifica que `professional_id` exista en `professional` (si no existe, retorna `Rejected` con `UNKNOWN_REFERENCE`, ver D5).
        4. En un bloque atómico (`begin_nested()`), elimina las filas previas de `working_hours` para ese `professional_id` e inserta los nuevos tramos (permitiendo `slots` vacío `()` si un profesional deja de tener horario semanal), y devuelve `Ok(tuple(slots_ordenados))` ordenados por `(weekday, start_minute)`.
      - `list_by_professional(professional_id: UUID) -> tuple[WorkingHours, ...]`: devuelve los tramos del profesional ordenados por `(weekday, start_minute)`.
      - `list() -> tuple[WorkingHours, ...]`: devuelve todos los tramos persistidos ordenados por `(professional_id, weekday, start_minute)` (útil para poblar `ScheduleContext.working_hours`).
    - **`BlockRepository(session)`**:
      - `create(candidate: Block) -> CatalogResult[Block]`:
        1. Ejecuta `validate_block(candidate)`. Si devuelve violaciones, retorna `Rejected(tuple(violations))` sin tocar la base.
        2. Verifica que `candidate.professional_id` exista en `professional` (si no existe, retorna `Rejected` con `UNKNOWN_REFERENCE`, ver D5).
        3. Inserta `BlockModel` y devuelve `Ok(candidate)`.
      - `delete(identifier: UUID) -> bool`: busca la fila por `id`; si existe la elimina (`session.delete(row)` + `session.flush()`) y devuelve `True`; si no existe devuelve `False`.
      - `get_by_id(identifier: UUID) -> Block | None`: devuelve el `Block` con `start_at` y `end_at` en UTC, o `None`.
      - `list_by_professional(professional_id: UUID) -> tuple[Block, ...]`: devuelve los bloqueos del profesional ordenados por `(start_at, id)`.
      - `list() -> tuple[Block, ...]`: devuelve todos los bloqueos ordenados por `(start_at, id)` (útil para poblar `ScheduleContext.blocks`).
      - `list_affected_appointments(block: Block, appointments: Sequence[Appointment]) -> tuple[Appointment, ...]`: interfaz para turnos afectados (ver D6).
    - *Pros*: Se alinea con US-010, US-011 y C-21 (`PUT .../working-hours`, `POST/GET/DELETE .../blocks`), preserva las posiciones `1..N` de los mensajes de `validate_working_hours`, evita estados intermedios corruptos al actualizar horarios y mantiene la misma ergonomía `Ok | Rejected` que C-15.
    - *Contras*: Requiere relajar `TypeVar("T")` en `app/domain/catalog/result.py` (cambio de 1 línea totalmente retrocompatible con `mypy --strict` y con los tests de C-09 y C-15).
  - **Opción B**: En `WorkingHoursRepository`, exponer `add(slot: WorkingHours)` unitario en lugar de `replace_for_professional(professional_id, slots)`.
    - *Pros*: Se parece más a `create` de catálogos.
    - *Contras*: No permite reemplazar ni vaciar tramos de un día sin métodos extra de borrado por tramo, y al validar contra filas ya guardadas en la base las posiciones `"El tramo 1 y 2..."` de `validate_working_hours` no coincidirían con el orden enviado por el usuario.
  - **Opción C**: Crear una clase `AvailabilityResult` nueva e incompatible con `Ok` de `catalog/result.py`.
    - *Pros*: No toca `catalog/result.py`.
    - *Contras*: Introduce un tercer tipo `Ok` en el proyecto (además de `domain.violations.Ok` y `domain.catalog.result.Ok`), complicando innecesariamente los imports en `seed.py` y en la futura API.
- **Recomendación**: **Opción A**. Es consistente con C-05, C-06, C-15 y los endpoints previstos en C-21.

---

### D5 — Existencia del profesional referenciado y traducción de errores de integridad (`IntegrityError`)

- **Problema**: Tantear qué sucede cuando se intenta guardar un horario o un bloqueo cuyo `professional_id` no existe en la tabla `professional`, o cuando PostgreSQL lanza un `IntegrityError` (por FK, PK duplicada en `block` o `CHECK` en inserción directa).
- **Opciones**:
  - **Opción A**:
    1. En `WorkingHoursRepository.replace_for_professional` y `BlockRepository.create`, tras pasar `validate_working_hours` / `validate_block`, comprobar si el profesional existe (`session.get(ProfessionalModel, professional_id)` — o capturar específicamente la violación de `fk_working_hours_professional_id_professional` / `fk_block_professional_id_professional` en un `begin_nested()`). Si no existe, devolver:
       ```python
       Rejected(
           (
               Violation(
                   code=ViolationCode.UNKNOWN_REFERENCE,
                   message="El profesional indicado no existe.",
                   reference_kind=ReferenceKind.PROFESSIONAL,
               ),
           )
       )
       ```
       (mismo código, `ReferenceKind` y mensaje en español que `rules/references.py` de C-03).
    2. Si ocurre una carrera concurrente donde el profesional se borra justo antes del `flush`, traducir únicamente `fk_working_hours_professional_id_professional` y `fk_block_professional_id_professional` a ese mismo `Rejected(UNKNOWN_REFERENCE)`.
    3. Cualquier otro `IntegrityError` (por ejemplo, `pk_block` por repetir `block.id` o violación de `uq_working_hours_...`) **no** se captura y se propaga, siguiendo el mismo contrato de C-15 (`test_patient_unrelated_primary_key_error_is_propagated`).
    4. Permitir configurar horarios y bloqueos tanto para profesionales activos como inactivos (la actividad del profesional se exige al asignar/reprogramar turnos en RN-AG-11, no en RN-DI-01..04).
    - *Pros*: Mantiene respuestas de negocio tipadas (`Rejected`) con el vocabulario exacto del dominio (`UNKNOWN_REFERENCE` + `ReferenceKind.PROFESSIONAL`), evita catches amplios y prepara el terreno para C-21.
    - *Contras*: Ninguno.
  - **Opción B**: Dejar que un `professional_id` inexistente dispare `IntegrityError` sin traducir.
    - *Pros*: Menos código en el repositorio.
    - *Contras*: Obligaría a la API en C-21 a consultar aparte el profesional o a atrapar excepciones SQLAlchemy en los routers HTTP.
  - **Opción C**: Rechazar también con `INACTIVE_REFERENCE` si el profesional tiene `active=False`.
    - *Pros*: Impide editar agendas de profesionales dados de baja.
    - *Contras*: No figura en RN-DI-01..04 ni en US-010/US-011 y dificultaría preparar la agenda de un profesional antes de activarlo.
- **Recomendación**: **Opción A**. Reutiliza `UNKNOWN_REFERENCE` + `ReferenceKind.PROFESSIONAL` de C-03 para profesionales inexistentes y propaga cualquier otro `IntegrityError` inesperado sin catches amplios.

---

### D6 — Interfaz y prueba de turnos afectados al crear un bloqueo (`appointments_affected_by_block`) antes de C-17

- **Problema**: `CHANGES.md` §[C-16] establece: *"Consulta de turnos afectados al crear un bloqueo (`appointments_affected_by_block` de C-06): se completa con `appointment` en C-17; acá queda la interfaz expuesta y probada con datos de prueba."* En C-16 todavía no existe `AppointmentModel` ni la tabla `appointment` (que se crean en C-17). Necesitamos definir la firma exacta en `BlockRepository` (y `contracts.py`) para que hoy funcione con datos de prueba (`Sequence[Appointment]`) y en C-17 pueda leer de la tabla `appointment` sin romper a los llamadores.
- **Opciones**:
  - **Opción A**:
    - En `BlockRepository` (y en el `Protocol` de `backend/app/repositories/contracts.py`), exponer el método:
      ```python
      def list_affected_appointments(
          self,
          block: Block,
          appointments: Sequence[Appointment] = (),
      ) -> tuple[Appointment, ...]:
      ```
      En C-16, delega en `tuple(appointments_affected_by_block(block, appointments))` usando la secuencia de `Appointment` recibida (datos de prueba). En C-17, cuando exista la tabla `appointment` y `appointments` no se pase (o sea `None`), el método consultará los turnos del profesional en la base y los filtrará con `appointments_affected_by_block`.
    - Además, verificar en el test de integración de C-16 que crear y persistir un bloqueo con `BlockRepository.create(block)` y consultar `BlockRepository.list_affected_appointments(block, sample_appointments)` devuelve exactamente los turnos en estado `reservado`, `confirmado` y `atendido` del mismo profesional que se solapan con el bloqueo, excluyendo `cancelado` y `ausente`, y que los objetos `Appointment` no se cancelan ni modifican (RN-DI-04, SU-05, US-011 CA-3).
    - *Pros*: `BlockRepository.create(block) -> CatalogResult[Block]` mantiene una firma limpia y homogénea con los demás repositorios, mientras `list_affected_appointments` deja la interfaz explícita en el contrato del repositorio y lista para conectarse a SQL en C-17.
    - *Contras*: El llamador que quiera ambos datos invoca `create(block)` y luego `list_affected_appointments(block, ...)`.
  - **Opción B**: Hacer que `BlockRepository.create(candidate: Block, existing_appointments: Sequence[Appointment] = ())` devuelva `CatalogResult[BlockCreationResult]` donde `BlockCreationResult(block: Block, affected_appointments: tuple[Appointment, ...])` es un dataclass nuevo.
    - *Pros*: Una sola llamada devuelve el bloqueo persistido y la lista de turnos afectados (como hará `POST /api/professionals/{id}/blocks` en C-21).
    - *Contras*: Hace que `BlockRepository.create` no devuelva `CatalogResult[Block]` sino un wrapper adicional, incluso cuando se inserta un bloqueo sin necesidad de listar turnos (p. ej. en fixtures o seeds). *(Nota: se pueden combinar A y B exponiendo tanto `create(block) -> CatalogResult[Block]` como `list_affected_appointments(block, appointments)`).*
  - **Opción C**: No exponer ningún método en `BlockRepository` y llamar directamente a la función de dominio `appointments_affected_by_block` desde el test.
    - *Pros*: Cero código nuevo en el repositorio.
    - *Contras*: Incumple `CHANGES.md` §[C-16], que pide que la interfaz de consulta quede expuesta en la capa de persistencia/repositorios y probada con datos de prueba.
- **Recomendación**: **Opción A** (manteniendo `create(block) -> CatalogResult[Block]` y exponiendo `list_affected_appointments(block, appointments=()) -> tuple[Appointment, ...]` en `BlockRepository` y `contracts.py`). Si se prefiere que `create` devuelva ambos en un único método o tener un helper `create_and_list_affected`, es trivial ajustarlo.

---

### D7 — Datos ficticios en `demo_data.py` y extensión del seed idempotente en `seed.py`

- **Problema**: `knowledge-base/04_modelo_de_datos.md` (§Seed data inicial) especifica:
  - `WorkingHours`: *"Lun–Vie 09:00–13:00 y 15:00–19:00 para los tres (variar uno para pruebas, p. ej. Dr. Ferrer solo mañanas)"* (en `demo_data.py` de C-09/C-15 los tres profesionales se llaman Dra. Laura Quiroga `...001`, Dr. Martín Sosa `...002` y Dra. Paula Benítez `...003`).
  - Hay que definir los tramos exactos en `backend/app/demo_data.py`, cómo los carga `backend/app/db/seed.py` de forma idempotente y si el diccionario de conteos devuelto por `seed_database()` incorpora `"working_hours"` (o si mantiene las 4 claves de C-15 o las amplía a 5).
- **Opciones**:
  - **Opción A**:
    1. En `backend/app/demo_data.py`, agregar `WORKING_HOURS: tuple[WorkingHours, ...]` con 25 tramos válidos (lunes a viernes, `weekday` `1..5`):
       - Dra. Laura Quiroga (`00000000-0000-0000-0000-000000000001`): `540..780` (`09:00–13:00`) y `900..1140` (`15:00–19:00`) de lunes a viernes (10 tramos).
       - Dr. Martín Sosa (`00000000-0000-0000-0000-000000000002`): solo mañanas `540..780` (`09:00–13:00`) de lunes a viernes (5 tramos, cumpliendo la variación para pruebas de KB 04).
       - Dra. Paula Benítez (`00000000-0000-0000-0000-000000000003`): `540..780` (`09:00–13:00`) y `900..1140` (`15:00–19:00`) de lunes a viernes (10 tramos).
    2. En `backend/app/db/seed.py`, agregar `_seed_working_hours(session)`: para cada profesional de `PROFESSIONALS`, si `working_hours_repository.list_by_professional(professional.id)` está vacío, guarda sus tramos de `WORKING_HOURS` usando `replace_for_professional`. Si el profesional ya tiene tramos en la base, no los modifica ni los borra (idempotencia estricta, igual que en C-15).
    3. En `seed_database(settings)`, agregar `"working_hours": len(WorkingHoursRepository(session).list())` al diccionario de conteos devuelto (`{"professional": 3, "chair": 3, "service": 5, "patient": 5, "working_hours": 25}`) y actualizar el test de seed para esperar esa clave adicional (o mantener las 4 claves si no se quiere tocar `test_catalog_persistence.py` — ver comparación con Opción B).
    4. No precargar bloqueos en el seed (o dejar `BLOCKS: tuple[Block, ...] = ()`), ya que KB 04 (§Seed data inicial) no lista `Block` en la tabla del seed y cualquier fecha fija podría interferir con pruebas manuales.
    - *Pros*: Cumple exactamente KB 04 (§Seed data inicial), mantiene idempotencia sin pisar horarios editados por el usuario y deja `python -m app.db.seed` informando las 5 tablas pobladas.
    - *Contras*: Agregar `"working_hours": 25` al dict de `seed_database()` requiere actualizar la aserción `expected` en `tests/integration/test_catalog_persistence.py:217-222` (y limpiar `working_hours` antes de `professional` en el cleanup de ese test por la FK `fk_working_hours_professional_id_professional`).
  - **Opción B**: Igual que la Opción A en `demo_data.py` y `_seed_working_hours(session)`, pero también agregar un bloqueo ficticio fijo en `demo_data.py` (`BLOCKS`) y en el seed (`"block": 1`).
    - *Pros*: Ejercita también `BlockRepository` durante `python -m app.db.seed`.
    - *Contras*: KB 04 no incluye `Block` en la tabla de Seed data inicial.
  - **Opción C**: Agregar `WORKING_HOURS` en `demo_data.py` y una función `seed_working_hours(session)` separada sin llamarla dentro de `seed_database()` de C-15 para no tocar `test_catalog_persistence.py`.
    - *Pros*: No toca ni una línea de `test_catalog_persistence.py`.
    - *Contras*: `python -m app.db.seed` no cargaría los horarios de atención por defecto, contradiciendo KB 04 y lo que espera el resto del sistema al levantar el entorno de desarrollo.
- **Recomendación**: **Opción A**. Cumple KB 04 (§Seed data inicial) con los 25 tramos (incluyendo el profesional que atiende solo de mañana). Como `working_hours` tiene FK a `professional`, el cleanup de `test_catalog_persistence.py` que hace `DELETE FROM professional` igualmente debe borrar antes `working_hours` (y `block`), por lo que es limpio y coherente actualizar el cleanup y el conteo esperado del seed.

---

### D8 — Revisión de Alembic y orden de borrado en tests de integración

- **Problema**: Definir el identificador y alcance de la migración Alembic de C-16 y cómo interactúa con los tests de integración existentes (`test_database_infrastructure.py` y `test_catalog_persistence.py`).
- **Opciones**:
  - **Opción A**:
    - Crear la revisión `20261104_03_horarios_y_bloqueos` (archivo `backend/alembic/versions/20261104_03_horarios_y_bloqueos.py`) con `down_revision = "20261103_02_catalogos_y_pacientes"`.
    - En `upgrade()`: crear las tablas `working_hours` y `block` con sus PK, FK a `professional.id`, `CHECK`, `UniqueConstraint` e índices.
    - En `downgrade()`: eliminar los índices y las tablas `block` y `working_hours`.
    - Actualizar en `tests/integration/test_database_infrastructure.py` la revisión `head` esperada a `"20261104_03_horarios_y_bloqueos"`, y en `tests/test_persistence_metadata.py` el conjunto de tablas esperadas en `Base.metadata.tables` para incluir `"working_hours"` y `"block"`.
    - *Pros*: Sigue la convención `YYYYMMDD_NN_descripcion` de C-14 (`20261103_01_baseline`) y C-15 (`20261103_02_catalogos_y_pacientes`), mantiene `compare_metadata` vacío y verifica el ciclo completo hasta el nuevo `head`.
    - *Contras*: Requiere actualizar la constante del `head` actual en `test_database_infrastructure.py` y el `set(Base.metadata.tables)` en `test_persistence_metadata.py` (exactamente igual que hizo C-15 respecto de C-14).
  - **Opción B**: Modificar la migración `20261103_02_catalogos_y_pacientes.py` de C-15 en lugar de crear una tercera revisión.
    - *Pros*: Menos archivos en `alembic/versions/`.
    - *Contras*: Rompe la trazabilidad por change (C-15 ya está archivado y commiteado) e incumple `CHANGES.md` §[C-16] (*"Modelos SQLAlchemy y migración Alembic para `working_hours` y `block`"*).
- **Recomendación**: **Opción A**. Una migración nueva `20261104_03_horarios_y_bloqueos` encadenada a `20261103_02_catalogos_y_pacientes`.

---

### D9 — Cobertura de tests unitarios y de integración

- **Problema**: Determinar qué tests unitarios (sin Docker) y qué tests de integración (con `-m integration` sobre `<POSTGRES_DB>_test`) hacen falta para cubrir todos los requisitos de C-16 en modo Strict TDD.
- **Opciones**:
  - **Opción A**:
    1. **Tests unitarios (corren por defecto en `pytest` sin base de datos)**:
       - `tests/test_persistence_metadata.py`: verificar que `Base.metadata.tables` registra `working_hours` y `block`, tipos de columna (`Uuid`, `Integer`, `DateTime(timezone=True)`, `String`), FKs `fk_working_hours_professional_id_professional` y `fk_block_professional_id_professional`, `CHECK` nombrados (`ck_working_hours_weekday_range`, `ck_working_hours_minute_range`, `ck_block_interval_order`), `uq_working_hours_professional_weekday_start` e índices `ix_working_hours_professional_id_weekday` e `ix_block_professional_id_start_at_end_at`.
       - `tests/test_repository_contracts.py`: verificar que los protocolos `WorkingHoursRepository` y `BlockRepository` en `app/repositories/contracts.py` usan exclusivamente tipos del dominio (`WorkingHours`, `Block`, `Appointment`, `CatalogResult`).
       - `tests/domain/test_catalog.py` (o test de `demo_data.py`): verificar que `WORKING_HOURS` en `demo_data.py` pasa `validate_working_hours(WORKING_HOURS) == []` y cubre a los 3 profesionales de `PROFESSIONALS`.
    2. **Tests de integración (`tests/integration/test_availability_persistence.py`, con `pytestmark = pytest.mark.integration` sobre `<POSTGRES_DB>_test`)**:
       - **Ida y vuelta (`round-trip`) de `WorkingHours`**: guardar múltiples tramos (mañana y tarde, varios días) para un profesional y leerlos con `list_by_professional` y `list`, obteniendo instancias `WorkingHours` idénticas y ordenadas.
       - **Reemplazo atómico de horarios por profesional**: actualizar los horarios de un profesional reemplaza sus tramos anteriores sin alterar los de otros profesionales.
       - **Rechazo de horarios inválidos y solapados**: intentar guardar tramos con `weekday` fuera de `1..7`, minutos fuera de `0..1440`, `start_minute >= end_minute` (`INVALID_WORKING_HOURS`) o dos tramos del mismo día que se pisan (`OVERLAPPING_WORKING_HOURS`) devuelve `Rejected` con los mensajes exactos de C-05 y **no** modifica ni borra los tramos previamente persistidos del profesional.
       - **Ida y vuelta (`round-trip`) de `Block`**: guardar bloqueos con `start_at` y `end_at` en zona `-03:00` (con y sin `reason`), leerlos con `get_by_id`, `list_by_professional` y `list`, y comprobar que vuelven como `Block` con instantes en UTC equivalentes.
       - **Rechazo de bloqueo inválido**: intentar guardar un bloqueo con `start_at >= end_at` devuelve `Rejected` con `INVALID_BLOCK` (mensaje de C-06) y no inserta ninguna fila en `block`.
       - **Rechazo por profesional inexistente**: guardar horarios o un bloqueo con un `professional_id` que no existe en `professional` devuelve `Rejected` con `UNKNOWN_REFERENCE` (`ReferenceKind.PROFESSIONAL`).
       - **Eliminar un bloqueo libera el horario (US-011 CA-4)**:
         1. Persistir profesional, sillón, prestación, paciente, horario de atención y un bloqueo que cubre `10:00–11:00` local.
         2. Evaluar `validate_new_appointment` (o `check_blocks`) construyendo `ScheduleContext` con los horarios y bloqueos leídos del repositorio → se rechaza con `BLOCKED_TIME`.
         3. Eliminar el bloqueo con `BlockRepository.delete(block.id)` (devuelve `True`, y una segunda llamada devuelve `False`).
         4. Volver a leer los bloqueos del repositorio y evaluar el mismo turno → se acepta con `Ok(appointment, status_change)`.
       - **Interfaz de turnos afectados al crear un bloqueo (RN-DI-04, SU-05, US-011 CA-3)**: persistir un bloqueo nuevo y llamar a `BlockRepository.list_affected_appointments(block, sample_appointments)` con turnos de prueba; comprobar que devuelve en orden `(start_at, str(id))` solo los turnos del mismo profesional en estado `reservado`, `confirmado` o `atendido` que se solapan con el bloqueo, y que esos turnos conservan su estado e intervalo sin cambios.
       - **`CHECK` persistentes en PostgreSQL**: verificar con `insert(WorkingHoursModel)` e `insert(BlockModel)` directos que PostgreSQL rechaza `weekday = 0` / `8`, `start_minute >= end_minute` o fuera de `0..1440`, y `start_at >= end_at` con `IntegrityError` nombrando la constraint correspondiente.
       - **Propagación de errores de integridad no relacionados**: verificar que insertar dos bloqueos con el mismo `id` propaga `IntegrityError` (`pk_block`) sin ocultarlo.
       - **Seed idempotente y ciclo de migración**: verificar dos corridas consecutivas de `seed_database` y el ciclo `upgrade head` → `downgrade base` → `upgrade head` más `compare_metadata == []`.
    - *Pros*: Cubre el 100 % de los ítems de `CHANGES.md` §[C-16], KB 04/05/06 y mantiene el estándar de trazabilidad de C-15 y C-12.
    - *Contras*: Ninguno.
  - **Opción B**: Omitir los tests de `CHECK` por inserción directa dado que el repositorio ya valida antes en el dominio.
    - *Pros*: Menos tests de integración.
    - *Contras*: En C-15 se exigió explícitamente probar el `CHECK` de base mediante inserción directa (`test_patient_dni_check_rejects_invalid_direct_insert`) para demostrar que la constraint SQL está activa en PostgreSQL.
- **Recomendación**: **Opción A**. Aplica exactamente el mismo rigor de pruebas unitarias y de integración que C-15.

---

## 4. Riesgos y preguntas para la autora

### Riesgos identificados

1. **Orden de limpieza (`DELETE`) en los tests de integración de C-15 (`test_catalog_persistence.py`)**:
   - *Riesgo*: Al agregar las claves foráneas `working_hours.professional_id -> professional.id` y `block.professional_id -> professional.id` y poblar `working_hours` en `seed_database()`, los tests existentes en `test_catalog_persistence.py` que limpian tablas con `DELETE FROM professional` fallarán por violación de FK si antes no se ejecuta `DELETE FROM working_hours` y `DELETE FROM block`.
   - *Mitigación*: Actualizar el bloque de limpieza y el diccionario `expected` en `test_catalog_persistence.py` (o borrar primero las tablas hijas `block` y `working_hours` antes de `professional`).
2. **Transaccionalidad al reemplazar horarios (`replace_for_professional`)**:
   - *Riesgo*: Si se borraran los tramos anteriores de un profesional antes de validar los nuevos y la validación fallara, el profesional perdería su horario previo.
   - *Mitigación*: Ejecutar `validate_working_hours(slots)` y verificar la existencia del profesional **antes** de hacer el `DELETE` e `INSERT`, y envolver la escritura en `with self._session.begin_nested():`.
3. **Normalización de zona horaria al leer `TIMESTAMPTZ` desde PostgreSQL**:
   - *Riesgo*: Aunque `session.py` configura `SET TIME ZONE 'UTC'`, cualquier desajuste de `tzinfo` al construir `Block` podría alterar comparaciones en los tests.
   - *Mitigación*: `Block.__post_init__` ya normaliza `start_at` y `end_at` a `timezone.utc` con `_to_utc` y rechaza instantes *naive* con `ValueError`, garantizando que todo `Block` devuelto por `BlockRepository` tenga `tzinfo=timezone.utc`.

### Preguntas para la autora

Todas las preguntas están formuladas como las decisiones **D1 a D9** de la sección 3 para que puedas confirmarlas o ajustarlas en un único mensaje (por ejemplo: *"Aprobadas D1–D9 con las opciones recomendadas"* o indicando la opción elegida en cada una). En particular, confirmá si estás de acuerdo con:

- **D4 / D6**: Exponer `WorkingHoursRepository.replace_for_professional(professional_id, slots)` para el guardado del conjunto horario semanal y `BlockRepository.list_affected_appointments(block, appointments=())` para la consulta de turnos afectados antes de C-17.
- **D7**: Incluir los 25 tramos de `WORKING_HOURS` en `demo_data.py` y `seed.py` (con el Dr. Martín Sosa atendiendo solo de mañana como variación para pruebas, según KB 04) sin precargar bloqueos en el seed.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md` del propose)

> Nota: Esta lista es solo una propuesta dentro del explore; no se creó `openspec/changes/persistencia-horarios-y-bloqueos/` ni `tasks.md`.

### Grupo 1 — Datos ficticios y contratos de persistencia
- **1.1** Ampliar `backend/app/demo_data.py` con `WORKING_HOURS` (25 tramos Lun–Vie para los 3 profesionales de `PROFESSIONALS`, con el segundo profesional solo en turno mañana según KB 04) y verificar con un test unitario que todos los tramos son válidos según `validate_working_hours`.
- **1.2** Generalizar `CatalogResult[T]` en `backend/app/domain/catalog/result.py` y ampliar `backend/app/repositories/contracts.py` con los protocolos `WorkingHoursRepository` y `BlockRepository`; verificar con `tests/test_repository_contracts.py` y `mypy --strict` que solo exponen tipos del dominio.

### Grupo 2 — Modelos SQLAlchemy y migración Alembic
- **2.1** Escribir primero en `tests/test_persistence_metadata.py` los tests (RED) para `WorkingHoursModel` (`working_hours`) y `BlockModel` (`block`): columnas, tipos `Uuid`/`Integer`/`DateTime(timezone=True)`, claves foráneas a `professional.id`, constraints `ck_working_hours_weekday_range`, `ck_working_hours_minute_range`, `ck_block_interval_order`, `uq_working_hours_professional_weekday_start` e índices `ix_working_hours_professional_id_weekday` e `ix_block_professional_id_start_at_end_at`.
- **2.2** Implementar `WorkingHoursModel` y `BlockModel` en `backend/app/db/models.py` (GREEN) y verificar que `tests/test_persistence_metadata.py` y la guardia de dependencias del dominio pasen.
- **2.3** Actualizar el test de integración de migraciones en `tests/integration/test_database_infrastructure.py` (RED) para exigir la revisión `20261104_03_horarios_y_bloqueos`, la presencia de `working_hours` y `block`, su reversibilidad y `compare_metadata` vacío.
- **2.4** Crear la migración `backend/alembic/versions/20261104_03_horarios_y_bloqueos.py` encadenada a `20261103_02_catalogos_y_pacientes` (GREEN) y verificar el ciclo `upgrade head` → `downgrade base` → `upgrade head` y `compare_metadata == []`.

### Grupo 3 — Repositorio de horarios de atención (`WorkingHoursRepository`)
- **3.1** Escribir en `tests/integration/test_availability_persistence.py` los tests de integración (RED) para `WorkingHoursRepository`: ida y vuelta (`replace_for_professional`, `list_by_professional`, `list`), reemplazo de tramos de un profesional sin afectar a otros, rechazo previo de horarios inválidos (`INVALID_WORKING_HOURS`) y solapados (`OVERLAPPING_WORKING_HOURS`) sin alterar filas existentes, rechazo por profesional inexistente (`UNKNOWN_REFERENCE`) y verificación de los `CHECK` de base (`ck_working_hours_weekday_range`, `ck_working_hours_minute_range`) ante inserción directa.
- **3.2** Implementar `WorkingHoursRepository` en `backend/app/repositories/working_hours.py` (o `availability.py`) (GREEN + REFACTOR) pasando todos los tests de 3.1.

### Grupo 4 — Repositorio de bloqueos (`BlockRepository`) y turnos afectados
- **4.1** Escribir en `tests/integration/test_availability_persistence.py` los tests de integración (RED) para `BlockRepository`: ida y vuelta en UTC (`create`, `get_by_id`, `list_by_professional`, `list`), rechazo previo de bloqueo con `start_at >= end_at` (`INVALID_BLOCK`), rechazo por profesional inexistente (`UNKNOWN_REFERENCE`), verificación del `CHECK` `ck_block_interval_order` y propagación de `pk_block` duplicado.
- **4.2** Escribir los tests de integración (RED) para el borrado de un bloqueo que libera el horario en la validación de un turno nuevo (`US-011 CA-4`) y para la interfaz `list_affected_appointments(block, appointments)` con datos de prueba (`US-011 CA-3`, `RN-DI-04`, `SU-05`).
- **4.3** Implementar `BlockRepository` (GREEN + REFACTOR) y verificar todos los escenarios de 4.1 y 4.2.

### Grupo 5 — Seed idempotente y verificación final
- **5.1** Escribir/actualizar los tests del seed idempotente (RED) para incluir la carga de `WORKING_HOURS` y el orden de limpieza respetando las FKs a `professional`.
- **5.2** Ampliar `backend/app/db/seed.py` con `_seed_working_hours` (GREEN) y verificar que dos ejecuciones consecutivas producen conteos idénticos sin duplicar ni pisar filas.
- **5.3** Ejecutar la verificación completa del change (`pytest`, `pytest -m integration`, `mypy --strict`, ciclo de Alembic, doble ejecución del seed, `openspec validate persistencia-horarios-y-bloqueos --strict` y `git diff --check`) y registrar las evidencias en `docs/evidencias/`.

