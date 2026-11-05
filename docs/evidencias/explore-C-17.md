# Explore C-17 — `persistencia-turnos-e-historial`

Fecha: 2026-11-05
Fase: 4 — Infraestructura y persistencia (Docker Compose + PostgreSQL + SQLAlchemy + Alembic)
Governance: **ALTO** (integridad de datos y concurrencia; describir el diseño y esperar confirmación explícita de la autora antes de implementar)
Dependencias en `CHANGES.md`: `C-12` (`historial-de-transiciones`, archivado) y `C-15` (`persistencia-catalogos-y-pacientes`, archivado); en paralelo con `C-16` (`persistencia-horarios-y-bloqueos`).

---

## 1. Alcance de C-17 según `CHANGES.md` y qué queda afuera

### Qué entra en C-17

El objetivo central de C-17 es persistir el ciclo de vida completo de los turnos de la agenda y su trazabilidad funcional en PostgreSQL, garantizando la atomicidad entre el turno y su entrada de historial (RN-GL-02) y la serialización estricta ante accesos concurrentes (DD-03, RN-GL-01).

En concreto, C-17 comprende:

1. **Modelos declarativos SQLAlchemy 2.x en `backend/app/db/models.py`**:
   - `AppointmentModel` (`appointment`): `id` (UUID PK), `patient_id` (FK), `professional_id` (FK), `chair_id` (FK), `service_id` (FK), `start_at` y `end_at` en `timestamptz` (UTC), `status` con `CHECK` de los 5 estados válidos (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`), `created_at` y `updated_at` en `timestamptz` (UTC), restricción `start_at < end_at` e índices por profesional, sillón y estado.
   - `AppointmentStatusChangeModel` (`appointment_status_change`): `id` (UUID PK), `appointment_id` (FK), `from_status` (nullable), `to_status` (NOT NULL), `changed_by` (UUID), `changed_at` (TIMESTAMPTZ UTC), almacenamiento de `RescheduleDetail` para reprogramaciones y `note` opcional.
2. **Migración Alembic reversible en `backend/alembic/versions/`**:
   - Revisión encadenada a `20261104_03_horarios_y_bloqueos` (C-16), creando ambas tablas con sus claves foráneas a `professional`, `chair`, `service`, `patient` y `appointment`, restricciones `CHECK` e índices según `NAMING_CONVENTION`.
3. **Repositorio de turnos e historial en `backend/app/repositories/`**:
   - Recibe y devuelve tipos del dominio (`Appointment`, `AppointmentStatusChange`, resultados tipados `Ok` / `Rejected`).
   - Persistencia atómica de alta, cambio de estado ordinario, cancelación y reprogramación: si se guarda el turno, se guarda su `status_change` en la misma transacción; si alguno falla, no queda ninguno (RN-GL-02).
   - Bloqueo pesimista `SELECT ... FOR UPDATE` sobre la fila del profesional y la del sillón, **siempre en orden lexicográfico fijo por UUID**, antes de cargar el contexto de turnos activos y evaluar la regla en el dominio puro (DD-03).
   - En reprogramaciones que cambian de profesional o sillón, bloqueo ordenado de todos los recursos involucrados (origen y destino) para prevenir carreras y deadlocks.
   - Historial funcional estrictamente append-only: sin métodos de modificación ni borrado en la interfaz del repositorio.
4. **Implementación concreta de `AppointmentReader`**:
   - Implementación SQL del protocolo `AppointmentReader` definido en `backend/app/repositories/contracts.py` (C-16) para que `BlockRepository.list_affected_appointments` consulte turnos activos reales en la base.
5. **Tests de integración con PostgreSQL real (`<POSTGRES_DB>_test`)**:
   - Ida y vuelta de turnos e historial con mapeo exacto a tipos del dominio.
   - Atomicidad turno + historial: verificación de rollback ante fallos en uno de los dos.
   - Concurrencia real: dos conexiones paralelas que intentan solapar el mismo profesional o el mismo sillón; la segunda espera a que la primera termine y recibe el rechazo de conflicto (`PROFESSIONAL_OVERLAP` o `CHAIR_OVERLAP`), sin mocks ni monkeypatch.
   - Ausencia de métodos de edición o borrado de historial y ciclo de migración upgrade/downgrade.

### Qué queda explícitamente afuera

- **De C-18 (`api-base-fastapi`)**: servidor FastAPI, manejo global de excepciones HTTP, middleware CORS y endpoint de salud `/api/health`.
- **De C-19 (`autenticacion-jwt-y-roles`)**: tabla `user`, hash de contraseñas, login JWT y validación de tokens Bearer. En C-17, `changed_by` se recibe como `UUID` inyectado por el llamador.
- **De C-21 (`api-horarios-y-bloqueos`)**: endpoints REST de horarios y bloqueos.
- **De C-22 (`api-dar-turno`)**: endpoint `POST /api/appointments`, esquemas Pydantic HTTP y mapeo de errores a `409` / `422` / `400`.
- **De C-23 (`api-ciclo-de-vida-del-turno`)**: endpoints `POST /api/appointments/:id/cancel`, `POST /api/appointments/:id/reschedule`, `POST /api/appointments/:id/status` y `GET /api/appointments/:id/history`.
- **De C-24 (`api-consulta-de-agenda`)**: endpoint `GET /api/agenda` con filtros combinados para la vista de agenda.
- **Del subdominio de negocio (`backend/app/domain/`)**: no se modifican las dataclasses de dominio ni las funciones puras en `appointment/validate.py`, `appointment/transitions.py` ni `appointment/reschedule.py`.

---

## 2. Estado actual

### 2.1. Tipos del dominio a persistir

| Tipo de dominio | Ubicación | Campos e invariantes |
|-----------------|-----------|----------------------|
| `Appointment` | `backend/app/domain/model.py:297-334` | - `id: UUID`<br>- `patient_id: UUID`<br>- `professional_id: UUID`<br>- `chair_id: UUID`<br>- `service_id: UUID`<br>- `start_at: datetime` (normalizado a UTC en `__post_init__`, no naive)<br>- `end_at: datetime` (normalizado a UTC en `__post_init__`, no naive)<br>- `status: AppointmentStatus` (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`)<br>- Invariante: `start_at < end_at` (`ValueError` si no se cumple).<br>- Property `interval -> Interval`.<br>- **Nota clave**: `Appointment` en el dominio **no tiene** `created_at` ni `updated_at`. |
| `AppointmentStatusChange` | `backend/app/domain/model.py:357-382` | - `appointment_id: UUID`<br>- `from_status: AppointmentStatus | None` (`None` solo en alta)<br>- `to_status: AppointmentStatus`<br>- `changed_by: UUID`<br>- `changed_at: datetime` (normalizado a UTC en `__post_init__`, no naive)<br>- `reschedule: RescheduleDetail | None = None`<br>- Invariante: si `from_status == to_status` y `reschedule is None`, lanza `ValueError`.<br>- **Nota clave**: en el dominio **no tiene** `id: UUID` propio (se difirió la PK a C-17 en C-12 D1). |
| `RescheduleDetail` | `backend/app/domain/model.py:336-354` | - `previous_interval: Interval`<br>- `new_interval: Interval`<br>- `previous_professional_id: UUID`<br>- `new_professional_id: UUID`<br>- `previous_chair_id: UUID`<br>- `new_chair_id: UUID` |

### 2.2. Qué devuelven hoy las operaciones del dominio

Desde C-12, las cuatro operaciones del dominio devuelven el resultado tipado `Ok` definido en `backend/app/domain/violations.py:82-93`:

```python
@dataclass(frozen=True, slots=True)
class Ok:
    appointment: Appointment
    status_change: AppointmentStatusChange
```

1. `validate_new_appointment(...) -> Ok | Rejected`:
   - En éxito: `Ok.appointment` en `AppointmentStatus.RESERVED` y `Ok.status_change` con `from_status=None`, `to_status=RESERVED`, `reschedule=None` y `changed_at=context.now`.
2. `change_status(appointment, target_status, actor, now, ...) -> Ok | Rejected`:
   - En éxito: `Ok.appointment` con el nuevo estado y `Ok.status_change` con `from_status=original.status`, `to_status=target_status`, `reschedule=None` y `changed_at=now`.
3. `cancel_appointment(appointment, actor, now, ...) -> Ok | Rejected`:
   - En éxito: `Ok.appointment` en `AppointmentStatus.CANCELLED` y `Ok.status_change` con `from_status=original.status`, `to_status=CANCELLED`, `reschedule=None` y `changed_at=now`.
4. `reschedule_appointment(appointment, request, actor, context, ...) -> Ok | Rejected`:
   - En éxito: `Ok.appointment` en `AppointmentStatus.RESERVED` (con nuevos parámetros) y `Ok.status_change` con `from_status=original.status`, `to_status=RESERVED`, `changed_at=context.now` y `reschedule=RescheduleDetail(...)` tipado.

### 2.3. Qué existe ya en la base de datos

- Tablas de C-15: `professional`, `chair`, `service`, `patient`.
- Tablas de C-16: `working_hours`, `block`.
- Convención de nombres (`NAMING_CONVENTION`) en `backend/app/db/base.py`.
- Configuración de conexión síncrona en UTC (`session.py`).
- Protocolo `AppointmentReader` en `backend/app/repositories/contracts.py`:
  ```python
  class AppointmentReader(Protocol):
      def list_for_professional_in_range(
          self, professional_id: UUID, start_at: datetime, end_at: datetime
      ) -> Sequence[Appointment]: ...
  ```

---

## 3. Decisiones abiertas (`D1`–`D10`)

### D1 — Tablas y columnas de `appointment` y `appointment_status_change`, claves y restricciones
*(Decisión de integridad)*

- **Problema**: Diseñar las tablas relacionales para `appointment` y `appointment_status_change` respetando `knowledge-base/04_modelo_de_datos.md`, asegurando integridad referencial, estados válidos y compatibilidad con los tipos del dominio.
- **Opciones**:
  - **Opción A**:
    - `appointment`:
      - `id`: `Uuid(as_uuid=True)`, PK (`pk_appointment`).
      - `patient_id`: `Uuid(as_uuid=True)`, FK a `patient.id` (`ondelete="RESTRICT"`), NOT NULL.
      - `professional_id`: `Uuid(as_uuid=True)`, FK a `professional.id` (`ondelete="RESTRICT"`), NOT NULL.
      - `chair_id`: `Uuid(as_uuid=True)`, FK a `chair.id` (`ondelete="RESTRICT"`), NOT NULL.
      - `service_id`: `Uuid(as_uuid=True)`, FK a `service.id` (`ondelete="RESTRICT"`), NOT NULL.
      - `start_at`: `DateTime(timezone=True)`, NOT NULL.
      - `end_at`: `DateTime(timezone=True)`, NOT NULL.
      - `status`: `String(20)`, NOT NULL, con `CheckConstraint("status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status")`.
      - `created_at`: `DateTime(timezone=True)`, NOT NULL.
      - `updated_at`: `DateTime(timezone=True)`, NOT NULL.
      - `CheckConstraint("start_at < end_at", name="ck_appointment_interval_order")`.
      - Índices: `ix_appointment_professional_id_start_at` en `(professional_id, start_at)`, `ix_appointment_chair_id_start_at` en `(chair_id, start_at)` e `ix_appointment_status_start_at` en `(status, start_at)`.
    - `appointment_status_change`:
      - `id`: `Uuid(as_uuid=True)`, PK (`pk_appointment_status_change`), generado con `uuid4()` por la capa de persistencia (el dominio no tiene `id` en `AppointmentStatusChange`).
      - `appointment_id`: `Uuid(as_uuid=True)`, FK a `appointment.id` (`ondelete="RESTRICT"`), NOT NULL.
      - `from_status`: `String(20)`, NULL (solo en alta), con `CheckConstraint("from_status IS NULL OR from_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status_change_from_status")`.
      - `to_status`: `String(20)`, NOT NULL, con `CheckConstraint("to_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')", name="ck_appointment_status_change_to_status")`.
      - `changed_by`: `Uuid(as_uuid=True)`, NOT NULL.
      - `changed_at`: `DateTime(timezone=True)`, NOT NULL.
      - `note`: `String(500)`, NULL (para texto opcional según KB 04).
      - Persistencia de `RescheduleDetail` (ver D2).
      - Índice: `ix_appointment_status_change_appointment_id_changed_at` en `(appointment_id, changed_at)`.
    - *Pros*: Modela fielmente KB 04, valida estados en la base con CHECKs nombrados, define índices para las consultas frecuentes de agenda y garantiza integridad referencial estricta.
    - *Contras*: Ninguno relevante.
  - **Opción B**: Usar tipos `Enum` nativos de PostgreSQL para `status` en lugar de `String(20)` con `CheckConstraint`.
    - *Pros*: Validación a nivel de tipo de datos nativo en PostgreSQL.
    - *Contras*: Los tipos `ENUM` de PostgreSQL complican migraciones futuras si se agrega un estado (exigen `ALTER TYPE ... ADD VALUE`), mientras que un `CheckConstraint` es más portable y alineado con Alembic y el resto del proyecto.
  - **Opción C**: Omitir índices compuestos en `appointment`.
    - *Pros*: Menor número de índices en inserción.
    - *Contras*: Degradaría el rendimiento de las consultas por profesional, sillón y rango de agenda requeridas en DD-03 y C-24.
- **Recomendación**: **Opción A**. Es robusta, sigue la convención de Alembic y KB 04, y preserva la integridad de datos con constraints explícitos.

---

### D2 — Persistencia de `RescheduleDetail` (D9 de C-12)
*(Decisión de integridad)*

- **Problema**: En C-12 D9 se difirió a C-17 cómo persistir el detalle tipado de reprogramación `RescheduleDetail` (`previous_interval`, `new_interval`, `previous_professional_id`, `new_professional_id`, `previous_chair_id`, `new_chair_id`).
- **Opciones**:
  - **Opción A (Columnas dedicadas en `appointment_status_change`)**:
    Agregar en la tabla `appointment_status_change`:
    - `previous_start_at`: `DateTime(timezone=True)`, NULL.
    - `previous_end_at`: `DateTime(timezone=True)`, NULL.
    - `new_start_at`: `DateTime(timezone=True)`, NULL.
    - `new_end_at`: `DateTime(timezone=True)`, NULL.
    - `previous_professional_id`: `Uuid(as_uuid=True)`, FK opcional a `professional.id`, NULL.
    - `new_professional_id`: `Uuid(as_uuid=True)`, FK opcional a `professional.id`, NULL.
    - `previous_chair_id`: `Uuid(as_uuid=True)`, FK opcional a `chair.id`, NULL.
    - `new_chair_id`: `Uuid(as_uuid=True)`, FK opcional a `chair.id`, NULL.
    - *Pros*: Tipado estricto a nivel relacional, integridad referencial con FKs a `professional` y `chair`, consultas SQL directas sobre turnos reprogramados sin parseo.
    - *Contras*: Agrega 8 columnas anulables en la tabla de historial (solo se pueblan cuando la entrada es de reprogramación).
  - **Opción B (JSONB en `appointment_status_change`)**:
    Agregar una columna `reschedule_detail: JSONB NULL` que almacena:
    `{"previous_interval": ["...", "..."], "new_interval": ["...", "..."], "previous_professional_id": "...", "new_professional_id": "...", "previous_chair_id": "...", "new_chair_id": "..."}`.
    - *Pros*: Esquema relacional limpio (una sola columna adicional).
    - *Contras*: Pierde claves foráneas en la base para los profesionales y sillones involucrados, requiere serialización/deserialización manual en el repositorio y rompe homogeneidad con el resto de las tablas de C-15/C-16.
  - **Opción C (Tabla separada `appointment_reschedule_detail`)**:
    Crear una tabla 1:1 vinculada a `appointment_status_change_id`.
    - *Pros*: Normalización relacional pura.
    - *Contras*: Añade una tabla extra, migración adicional y un JOIN obligatorio para leer el historial de reprogramaciones.
- **Recomendación**: **Opción A**. Proporciona tipado estricto, integridad referencial en PostgreSQL para los profesionales y sillones del intervalo anterior y nuevo, y mapeo directo e inequívoco hacia el dataclass `RescheduleDetail` del dominio.

---

### D3 — Quién asigna `created_at` y `updated_at` sin leer el reloj en el dominio (RN-GL-04)
*(Decisión de integridad)*

- **Problema**: `knowledge-base/04_modelo_de_datos.md` exige `created_at` y `updated_at` en `appointment`. Sin embargo, el dataclass de dominio `Appointment` no contiene esos campos y `RN-GL-04` prohíbe que el dominio lea el reloj del sistema (`datetime.now()`). Hay que definir cómo se establecen esos valores en la capa de persistencia.
- **Opciones**:
  - **Opción A (Asignación en el repositorio con el `now` inyectado + `server_default` en PostgreSQL)**:
    El repositorio recibe el `now: datetime` inyectado (el mismo que el llamador inyectó al dominio o que figura en `status_change.changed_at`):
    - En inserción: `created_at = now`, `updated_at = now`.
    - En actualización (cambio de estado o reprogramación): `updated_at = now`.
    - En el modelo SQLAlchemy: `server_default=sa.func.now()` como salvaguarda en la base.
    - *Pros*: Cumple estrictamente RN-GL-04 (el reloj se inyecta desde el borde de la aplicación), permite tests unitarios y de integración 100% deterministas donde se verifican fechas exactas, y no modifica el dataclass `Appointment` del dominio.
    - *Contras*: El llamador del repositorio debe proveer `now` (o se extrae de `status_change.changed_at`).
  - **Opción B (Delegar exclusivamente en PostgreSQL con triggers o `clock_timestamp()`)**:
    - *Pros*: Cero código en Python para fechas de auditoría.
    - *Contras*: En los tests, `created_at` y `updated_at` siempre tendrían la hora del servidor de base de datos en tiempo real, imposibilitando aserciones deterministas basadas en el `now` inyectado por el escenario.
  - **Opción C (Agregar `created_at` y `updated_at` al dataclass `Appointment` en `model.py`)**:
    - *Pros*: Los campos pasan a ser visibles en el objeto de dominio.
    - *Contras*: Viola la frontera de responsabilidad (son metadatos de persistencia, no reglas de agenda) y rompería los constructores de `Appointment` en decenas de tests de dominio de C-02 a C-12.
- **Recomendación**: **Opción A**. Mantiene la pureza del dominio, garantiza determinismo en los tests y respeta RN-GL-04.

---

### D4 — Transacción y serialización con `SELECT ... FOR UPDATE` en altas y reprogramaciones (DD-03)
*(Decisión de concurrencia e integridad)*

- **Problema**: Para cumplir el diferencial del sistema (rechazar solapamientos sin sobreturnos bajo concurrencia), DD-03 prescribe: *"Las altas y reprogramaciones corren en una transacción que toma SELECT ... FOR UPDATE sobre la fila del profesional y la del sillón, siempre en el mismo orden, antes de cargar el contexto y validar"*. Hay que definir la mecánica exacta de quién gestiona la transacción, en qué orden se toman los locks y cómo se arma el contexto dentro del bloqueo.
- **Opciones**:
  - **Opción A (Métodos orquestados transaccionales en `AppointmentRepository`)**:
    `AppointmentRepository` opera sobre la `session: Session` de SQLAlchemy y ofrece métodos atómicos:
    - Para alta: `create(request: NewAppointmentRequest, references: AppointmentReferences, schedule_context: ScheduleContext, ...) -> CatalogResult[Appointment]` (o helper de transacción dentro del repositorio/caso de uso).
    - Mecánica de bloqueo:
      1. Se determina el conjunto de recursos a bloquear: `professional_id` y `chair_id`. En reprogramaciones donde cambian profesional o sillón, se toman tanto los anteriores como los nuevos (hasta 2 profesionales y hasta 2 sillones).
      2. Se ordenan todos los UUIDs en orden lexicográfico ascendente (`sorted([id_1, id_2, ...])`) para garantizar un orden determinista global y prevenir **deadlocks** entre transacciones concurrentes.
      3. Dentro de `with session.begin_nested():` (o transacción abierta): se ejecuta `SELECT id FROM professional WHERE id IN (...) ORDER BY id FOR UPDATE` y `SELECT id FROM chair WHERE id IN (...) ORDER BY id FOR UPDATE`.
      4. **Dentro del bloqueo**, se consultan los turnos activos existentes en la base (`AppointmentReader`) que intersecan el rango para el profesional y para el sillón.
      5. Se invoca la función pura de dominio (`validate_new_appointment` o `reschedule_appointment`).
      6. Si el dominio devuelve `Rejected`: se revierte el savepoint (liberando locks al completar o rollback) y se devuelve el `Rejected` con todas las violaciones del dominio.
      7. Si el dominio devuelve `Ok`: se persiste `AppointmentModel` y `AppointmentStatusChangeModel`, se hace `flush()`, y se devuelve `Ok(appointment, status_change)`.
    - *Pros*: Cumple estrictamente DD-03, encapsula la serialización evitando condiciones de carrera entre el momento de leer los turnos y el momento de escribir, y garantiza orden anti-deadlock.
    - *Contras*: El repositorio necesita orquestar la consulta de turnos activos y la llamada al dominio dentro de la transacción protegida.
  - **Opción B (Nivel de aislamiento SERIALIZABLE sin bloqueo de filas)**:
    - *Pros*: Código SQL más simple sin sentencias `FOR UPDATE`.
    - *Contras*: PostgreSQL lanza `serialization_failure` (código 40001) ante conflictos, lo que exigiría implementar un middleware complejo de reintentos con backoff exponencial y contradice la decisión explícita DD-03 fijada en la KB.
  - **Opción C (Bloqueo pesimista solo sobre la tabla de turnos)**:
    - *Pros*: Bloquea filas de turnos en vez de profesionales/sillones.
    - *Contras*: No previene el "phantom read" de un hueco libre donde aún no existe ningún turno para bloquear. Bloquear las filas maestras de `professional` y `chair` serializa el acceso al recurso físico (el odontólogo y el consultorio) sin importar si el hueco está vacío.
- **Recomendación**: **Opción A**. Es exactamente el patrón establecido en DD-03 y KB 08, evita deadlocks mediante ordenación de IDs y previene cualquier solapamiento concurrente.

---

### D5 — Garantía de atomicidad turno + historial (RN-GL-02)
*(Decisión de integridad)*

- **Problema**: RN-GL-02 establece: *"Las operaciones de escritura de turnos son atómicas: o se valida y guarda todo (turno + historial) o nada"*.
- **Opciones**:
  - **Opción A (Inserción en la misma sesión/savepoint SQLAlchemy)**:
    En cada operación de escritura (`create`, `reschedule`, `change_status`, `cancel`):
    - Se crea o actualiza `AppointmentModel` y simultáneamente se crea `AppointmentStatusChangeModel` en la misma sesión.
    - Se ejecutan dentro de `with session.begin_nested():`. Si la inserción del historial o del turno falla por cualquier motivo (ej. error de integridad o desconexión), la sesión efectúa rollback completo.
    - Nunca se expone un método que inserte `AppointmentModel` sin su correspondiente `AppointmentStatusChangeModel`.
    - *Pros*: Control explícito en Python, sin dependencias de extensiones o triggers, 100% testeable en integración.
    - *Contras*: Ninguno.
  - **Opción B (Trigger en PostgreSQL que inserte el historial automáticamente)**:
    - *Pros*: La base fuerza la inserción del historial.
    - *Contras*: Duplica la lógica que el dominio ya resolvió en C-12 (donde cada función pura produce el `AppointmentStatusChange` exacto con su `changed_by`, `reschedule`, etc.) y violaría la regla dura de que el dominio es la autoridad (RN-GL-01).
- **Recomendación**: **Opción A**. Preserva al dominio como generador de la entrada de historial y asegura atomicidad estricta en la unidad de trabajo de SQLAlchemy.

---

### D6 — Inmutabilidad del historial en persistencia (RN-TU-06)
*(Decisión de integridad)*

- **Problema**: RN-TU-06 prescribe que el historial funcional es estrictamente inmutable y append-only (sin edición ni borrado).
- **Opciones**:
  - **Opción A (Contrato de repositorio append-only + trigger defensivo en PostgreSQL)**:
    1. A nivel repositorio: `AppointmentStatusChangeRepository` (o la interfaz en `AppointmentRepository`) solo expone métodos de lectura (`list_by_appointment_id`, `get_by_id`) y el método interno de inserción atómica durante las transiciones de turno. No existen métodos `update`, `delete` ni `bulk_delete`.
    2. A nivel base de datos: agregar un trigger en PostgreSQL `BEFORE UPDATE OR DELETE ON appointment_status_change` que lance una excepción (`RAISE EXCEPTION 'appointment_status_change is append-only'`).
    - *Pros*: Defensa en profundidad absoluta: ni siquiera un script accidental o consulta manual en la base puede alterar o borrar el historial.
    - *Contras*: Requiere una función PL/pgSQL y trigger en la migración de Alembic.
  - **Opción B (Solo contrato de repositorio sin trigger en la base)**:
    - *Pros*: Migración Alembic puramente declarativa sin funciones PL/pgSQL.
    - *Contras*: Si alguien ejecuta un `UPDATE` o `DELETE` directo por SQL fuera del repositorio, la base lo permitiría.
  - **Opción C (Revocación de permisos SQL a nivel usuario de BD)**:
    - *Pros*: Seguridad a nivel de roles de base de datos.
    - *Contras*: Complejiza el setup local y Docker de desarrollo donde la aplicación usa el mismo usuario `POSTGRES_USER`.
- **Recomendación**: **Opción A** (o como mínimo Opción B con contrato estricto de repositorio y trigger opcional en migración si la autora lo prefiere). Recomendamos **Opción A** por alinearse con governance ALTO y garantizar inmutabilidad funcional irrevocable.

---

### D7 — Restricción extra en la base contra solapamientos (EXCLUDE con btree_gist) vs. bloqueo de filas (DD-03)
*(Decisión de concurrencia e integridad)*

- **Problema**: Evaluar si conviene agregar en PostgreSQL un constraint `EXCLUDE USING gist` sobre `tstzrange(start_at, end_at, '[)')` con `professional_id` y con `chair_id` (para estados que ocupan agenda) o si alcanza con el bloqueo de filas `SELECT ... FOR UPDATE` de DD-03.
- **Opciones**:
  - **Opción A (Alcanza con el bloqueo de filas `SELECT ... FOR UPDATE` + validación de dominio)**:
    - *Pros*:
      1. Es el diseño oficial fijado en DD-03 y KB 08.
      2. No requiere `CREATE EXTENSION btree_gist` (que en algunos entornos gestionados requiere privilegios de superusuario).
      3. El dominio genera mensajes de conflicto ricos y explicativos (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` con nombre del profesional/sillón y turno en conflicto) según RN-AG-12; un error de `EXCLUDE` solo devolvería un error de integridad genérico de PostgreSQL.
      4. Maneja de forma natural los estados que ocupan y liberan agenda (`reservado`, `confirmado`, `atendido` vs `cancelado`, `ausente`) según RN-AG-08, sin predicados parciales complejos en SQL.
    - *Contras*: Si alguien inserta turnos directamente por SQL puenteando el backend, la base no detectaría el solapamiento.
  - **Opción B (Agregar `EXCLUDE USING gist` en PostgreSQL como doble red)**:
    - *Pros*: Imposibilidad matemática de solapamiento incluso ante inserciones SQL directas externas.
    - *Contras*: Requiere extensión `btree_gist`, índices GiST adicionales con sobrecarga de escritura, y si llega a dispararse en concurrencia oculta el mensaje de negocio explicativo que exige el proyecto.
- **Recomendación**: **Opción A**. La serialización por `SELECT ... FOR UPDATE` de DD-03 previene el problema antes de que ocurra y permite que sea el dominio quien rechace con el mensaje en español y el id del turno en conflicto.

---

### D8 — Implementación SQL de `AppointmentReader` de C-16
*(Decisión de arquitectura)*

- **Problema**: C-16 definió en `backend/app/repositories/contracts.py`:
  ```python
  class AppointmentReader(Protocol):
      def list_for_professional_in_range(
          self, professional_id: UUID, start_at: datetime, end_at: datetime
      ) -> Sequence[Appointment]: ...
  ```
  En C-16 se prueba con un fake en memoria. C-17 debe proveer la implementación SQL real conectada a la tabla `appointment`.
- **Opciones**:
  - **Opción A (`SqlAppointmentReader` que implementa el protocolo o `AppointmentRepository` que satisface la interfaz)**:
    El repositorio `AppointmentRepository` (o una clase `SqlAppointmentReader` delegada) implementa `list_for_professional_in_range(professional_id, start_at, end_at) -> Sequence[Appointment]`.
    Consulta SQL:
    ```sql
    SELECT * FROM appointment
    WHERE professional_id = :professional_id
      AND start_at < :end_at
      AND end_at > :start_at
    ORDER BY start_at, id
    ```
    Mapea las filas a instancias `Appointment` del dominio en UTC y las devuelve.
    - *Pros*: Satisface exactamente el protocolo de C-16, permite a `BlockRepository.list_affected_appointments` operar contra la base real de turnos y se reutiliza para la carga de contexto de agenda.
    - *Contras*: Ninguno.
  - **Opción B (Consulta no filtrada en SQL y filtrada en memoria)**:
    - *Pros*: Menos lógica SQL.
    - *Contras*: Ineficiente al crecer el volumen histórico de turnos.
- **Recomendación**: **Opción A**. Filtra en PostgreSQL por intersección de intervalos semiabiertos y mapea limpiamente a tipos del dominio.

---

### D9 — Estrategia de prueba de concurrencia real sin mocks ni patch
*(Decisión de concurrencia)*

- **Problema**: Probar de forma determinista y real que dos transacciones simultáneas que intentan reservar el mismo hueco para el mismo profesional o el mismo sillón son serializadas correctamente, de modo que la primera gana y la segunda es rechazada con `PROFESSIONAL_OVERLAP` o `CHAIR_OVERLAP`.
- **Opciones**:
  - **Opción A (Test de integración multi-hilo con dos conexiones de base de datos reales y barrera de sincronización)**:
    En `backend/tests/integration/test_appointment_concurrency.py`:
    1. Se obtienen dos conexiones/sesiones independientes contra `<POSTGRES_DB>_test` desde `test_engine`.
    2. Se utiliza un `threading.Barrier(2)` o `threading.Event`:
       - Hilo A: inicia transacción, bloquea profesional/sillón con `FOR UPDATE`, valida en el dominio (sin conflicto), avisa al Hilo B mediante el evento de que ya tomó el lock, y duerme brevemente (ej. 150 ms) para asegurar que el Hilo B intente ejecutar mientras el lock sigue tomado. Luego Hilo A persiste el turno y confirma (`commit`).
       - Hilo B: espera que Hilo A tenga el lock, e intenta inmediatamente crear un turno solapado. PostgreSQL bloquea al Hilo B en el `SELECT ... FOR UPDATE`.
       - Al hacer commit Hilo A, el lock se libera; Hilo B se desbloquea, lee los turnos activos actualizados (que ahora incluyen el turno de Hilo A), y el dominio lo rechaza devolviendo `Rejected` con `PROFESSIONAL_OVERLAP` (o `CHAIR_OVERLAP`).
    3. Se verifica que Hilo A tiene `Ok`, Hilo B tiene `Rejected`, y en la base quedó exactamente 1 turno y 1 entrada de historial.
    - *Pros*: Prueba 100% real de la serialización en PostgreSQL y del comportamiento del dominio, sin ningún mock ni monkeypatch, verificando la ausencia de sobreturnos bajo contención.
    - *Contras*: Requiere coordinar hilos con cuidado para evitar timeouts o carreras en el test.
  - **Opción B (Simular el orden secuencialmente sin hilos)**:
    - *Pros*: Test secuencial simple.
    - *Contras*: No prueba la espera ni el bloqueo real de `SELECT ... FOR UPDATE` en el motor de PostgreSQL.
- **Recomendación**: **Opción A**. Es la prueba irrefutable de que la arquitectura de concurrencia de DD-03 funciona en PostgreSQL.

---

### D10 — Nombre de la migración y turnos en el seed
*(Decisión de diseño)*

- **Problema**: Definir el identificador de la migración Alembic de C-17 y si el script `backend/app/db/seed.py` debe cargar turnos de ejemplo.
- **Opciones**:
  - **Opción A**:
    - Migración: `20261105_04_turnos_e_historial` (encadenada a `20261104_03_horarios_y_bloqueos`).
    - Seed: `seed_database()` **no** carga turnos por defecto. En `knowledge-base/04_modelo_de_datos.md` (§Seed data inicial), la tabla de seed especifica profesionales, sillones, prestaciones, horarios, pacientes y usuarios, pero **no** turnos. La agenda debe iniciar vacía para que el consultorio arranque limpio en desarrollo. Opcionalmente, se pueden proveer fixtures de prueba o un helper `seed_demo_appointments()` exclusivo para demostraciones manuales si se solicita.
    - *Pros*: Respeta literalmente la KB y permite que los tests de integración y la futura UI arranquen con una agenda limpia y predecible.
    - *Contras*: Ninguno.
  - **Opción B**: Cargar 3 o 4 turnos ficticios en `seed_database()`.
    - *Pros*: Al abrir la app en C-27 ya hay turnos visibles.
    - *Contras*: Como los turnos se definen para fechas específicas, al pasar los días esos turnos quedarían en el pasado, requiriendo lógica dinámica en el seed o interfiriendo con los horarios laborales.
- **Recomendación**: **Opción A**. La migración `20261105_04_turnos_e_historial` y `seed_database()` sin turnos pregrabados.

---

## 4. Riesgos y preguntas para la autora

### Riesgos identificados y mitigaciones

1. **Deadlocks por orden de adquisición de bloqueos**
   - *Riesgo*: Si la Transacción 1 bloquea primero al Profesional P1 y luego al Sillón S1, mientras la Transacción 2 bloquea primero al Sillón S1 y luego al Profesional P1, PostgreSQL detectará un deadlock y abortará una de las dos.
   - *Mitigación*: Ordenar **todos** los identificadores a bloquear en orden lexicográfico ascendente por UUID antes de emitir la sentencia `FOR UPDATE`, tanto en altas como en reprogramaciones (donde pueden participar hasta 2 profesionales y 2 sillones).
2. **Desconexión entre el contexto leído y la escritura si se consulta fuera del lock**
   - *Riesgo*: Si se consultan los turnos activos antes de adquirir el lock sobre el profesional o sillón, otra transacción podría insertar un turno en ese intervalo y la validación no lo vería.
   - *Mitigación*: Adquirir primero el lock `FOR UPDATE` sobre profesional y sillón, y **recién después** ejecutar la consulta de turnos activos dentro de la misma transacción.
3. **Pérdida de la inmutabilidad del historial ante modificaciones accidentales**
   - *Riesgo*: Que un futuro caso de uso modifique una fila de `appointment_status_change`.
   - *Mitigación*: Repositorio sin métodos de update/delete y trigger defensivo en PostgreSQL que bloquea cualquier `UPDATE` o `DELETE` sobre la tabla.
4. **Manejo de fechas con zona horaria (`timestamptz`) al deserializar**
   - *Riesgo*: Que al leer de PostgreSQL un instante se reciba como naive o en hora local, rompiendo los invariantes del dominio.
   - *Mitigación*: La sesión de PostgreSQL fuerza `SET TIME ZONE 'UTC'`, y el repositorio asegura `tzinfo=timezone.utc` en cada `datetime` antes de construir los objetos del dominio.

### Preguntas para la autora (Puntos de control de Governance ALTO)

1. **Decisión D2 (`RescheduleDetail`)**: ¿Confirmás la Opción A (columnas dedicadas en `appointment_status_change` con claves foráneas opcionales a profesional y sillón) o preferís la Opción B (columna `JSONB`)?
2. **Decisión D4 (Transacción y Bloqueo)**: ¿Confirmás la Opción A con bloqueo ordenado por UUID de profesional y sillón dentro del repositorio/unidad de trabajo antes de validar?
3. **Decisión D6 (Inmutabilidad del Historial)**: ¿Confirmás agregar el trigger `BEFORE UPDATE OR DELETE` en PostgreSQL para forzar que sea append-only en la base además del repositorio (Opción A), o preferís dejarlo solo a nivel contrato de repositorio (Opción B)?
4. **Decisión D7 (Restricción en BD vs Bloqueo)**: ¿Confirmás la Opción A (bloqueo `SELECT ... FOR UPDATE` + dominio puro como autoridad, sin `EXCLUDE` ni `btree_gist`)?
5. **Decisión D10 (Seed)**: ¿Confirmás que `seed_database` no siembre turnos por defecto para mantener la agenda limpia según KB 04?

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md` del propose)

> Nota: Esta propuesta es únicamente preliminar dentro del explore; no se creó la carpeta de change en `openspec/` ni archivos de tasks.

### Grupo 1 — Contratos y modelos SQLAlchemy
- **1.1** Escribir tests unitarios en `tests/test_repository_contracts.py` (RED) para los contratos de `AppointmentRepository` y la implementación de `AppointmentReader`.
- **1.2** Escribir tests de metadata en `tests/test_persistence_metadata.py` (RED) exigiendo las tablas `appointment` y `appointment_status_change`, columnas, FKs, CHECKs nombrados de estado e intervalo, e índices.
- **1.3** Implementar `AppointmentModel` y `AppointmentStatusChangeModel` en `backend/app/db/models.py` (GREEN) y verificar que pasan los tests de metadata sin violar la guardia de dependencias del dominio.

### Grupo 2 — Migración Alembic
- **2.1** Escribir test de migración en `tests/integration/test_database_infrastructure.py` (RED) exigiendo la revisión `20261105_04_turnos_e_historial`, las dos tablas nuevas y la reversibilidad completa.
- **2.2** Crear la migración `backend/alembic/versions/20261105_04_turnos_e_historial.py` encadenada a `20261104_03_horarios_y_bloqueos` (GREEN) con las tablas, índices, constraints y trigger append-only; verificar ciclo `upgrade head` → `downgrade` → `upgrade head` y `compare_metadata == []`.

### Grupo 3 — Lector SQL de turnos (`AppointmentReader`) y consultas básicas
- **3.1** Escribir tests de integración en `tests/integration/test_appointment_persistence.py` (RED) para `list_for_professional_in_range` y `get_by_id`, verificando el mapeo bidireccional a tipos inmutables del dominio en UTC.
- **3.2** Implementar el lector SQL y métodos de consulta en `backend/app/repositories/appointment.py` (GREEN).
- **3.3** Conectar la implementación real de `AppointmentReader` con `BlockRepository.list_affected_appointments` de C-16 y verificar que los turnos afectados se leen de la base real.

### Grupo 4 — Altas atómicas, cambios de estado y cancelaciones con historial
- **4.1** Escribir tests de integración (RED) para el alta de turnos: persistencia atómica de `Appointment` y `AppointmentStatusChange` inicial (`from_status=None`), rollback si falla alguna inserción, y rechazo de profesional/paciente/sillón inexistente.
- **4.2** Implementar el método atómico de creación en `AppointmentRepository` (GREEN).
- **4.3** Escribir tests de integración (RED) para transiciones de estado ordinarias (`change_status`) y cancelaciones (`cancel_appointment`): actualización de estado, inserción de historial con `from_status` y `to_status`, y preservación del histórico.
- **4.4** Implementar las operaciones de ciclo de vida en `AppointmentRepository` (GREEN).

### Grupo 5 — Reprogramación y serialización concurrente (`SELECT ... FOR UPDATE`)
- **5.1** Escribir tests de integración (RED) para reprogramación: actualización de horario/profesional/sillón y persistencia atómica del historial con `RescheduleDetail` completo.
- **5.2** Implementar la reprogramación en `AppointmentRepository` con bloqueo ordenado de todos los recursos involucrados (GREEN).
- **5.3** Escribir tests de integración de concurrencia real (RED) con dos hilos y conexiones independientes: dos reservas simultáneas para el mismo profesional o el mismo sillón; verificar que la segunda espera el bloqueo y es rechazada con `PROFESSIONAL_OVERLAP` o `CHAIR_OVERLAP` sin crear sobreturnos.
- **5.4** Implementar el bloqueo ordenado `SELECT ... FOR UPDATE` (GREEN) y verificar que los tests de concurrencia pasan de forma consistente.

### Grupo 6 — Inmutabilidad del historial, verificación final y evidencias
- **6.1** Escribir tests de integración (RED) verificando que el repositorio no expone operaciones de modificación o borrado de historial, y que cualquier intento de `UPDATE` o `DELETE` directo en `appointment_status_change` es rechazado por la base.
- **6.2** Ejecutar la suite completa (`pytest`, `pytest -m integration`, `mypy --strict`, ciclo de Alembic, `git diff --check`) y generar evidencias en `docs/evidencias/verify-C-17.md`, `pytest-C-17.txt`, etc.

