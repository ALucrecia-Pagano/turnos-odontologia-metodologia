# Explore C-20 — `api-catalogos-y-pacientes`

Fecha: 2026-11-06
Fase: 5 — API REST FastAPI y JWT
Governance: **BAJO** (según `CHANGES.md` §[C-20]: CRUDs y catálogos de datos de soporte; autonomía completa si los tests pasan)
Dependencias en `CHANGES.md`: `C-09` (`catalogo-y-pacientes-puro`), `C-15` (`persistencia-catalogos-y-pacientes`), `C-19` (`autenticacion-jwt-y-roles`).

> Este explore es estrictamente analítico: no ejecutó docker, pytest, alembic ni pip; no tocó código, tests ni specs; y no creó estructuras en `openspec/`. Respeta que Claude Code se encuentra cerrando la implementación de C-19 en `backend/app/auth/` y `backend/app/api/deps.py`.

---

## 1. Alcance de C-20 según `CHANGES.md` y qué queda afuera

### Qué entra en C-20

1. **Endpoints REST completos**:
   - `/api/professionals` (alta, edición, desactivación, reactivación, listado y detalle).
   - `/api/chairs` (alta, edición, desactivación, reactivación, listado y detalle).
   - `/api/services` (alta, edición, desactivación, reactivación, listado y detalle).
   - `/api/patients` (alta, edición, listado, búsqueda y detalle).
2. **Matriz RBAC aplicada por celda**: cada ruta aplica `RequirePermission(Resource, Action)` según la matriz aprobada de C-19 D9.
   - Administrador: CRUD total en catálogos y CRU en pacientes.
   - Recepción: lectura en catálogos; alta, edición y lectura en pacientes.
   - Odontólogo: lectura en catálogos y lectura en pacientes; denegada toda alta o edición de recursos.
3. **Capa de aplicación / servicios**: orquestación entre la validación pura del dominio (C-09) y los repositorios SQLAlchemy (C-15).
4. **Validación de unicidad en edición**: actualización de nombres y DNI sin colisionar con la propia entidad.
5. **Esquemas Pydantic V2 en el borde**: entrada y salida serializadas en `camelCase` con `extra="forbid"`, cumpliendo la spec `api-foundation`.
6. **Mapeo de errores y respuestas Swagger**:
   - `400` para entradas malformadas (manejador de C-18).
   - `401` para tokens ausentes, alterados o vencidos (manejador de C-19).
   - `403` para intentos de mutación por roles no autorizados (`FORBIDDEN_OPERATION`).
   - `404` para recursos no encontrados por ID.
   - `409` para duplicados de unicidad (`DUPLICATE_NAME`, `DUPLICATE_DNI`).
   - `422` para violaciones de validez del dominio (`EMPTY_NAME`, `INVALID_DURATION`, `INVALID_DNI`).
7. **Tests de integración reales**: contra PostgreSQL de prueba con usuarios reales y tokens JWT genuinos (sin mocks ni `dependency_overrides`).

### Qué queda explícitamente afuera

- **C-19 (`autenticacion-jwt-y-roles`)**: emisión de JWT, hash Argon2, endpoints `/api/auth/login` y `/api/auth/me`. C-20 solo consume sus dependencias (`get_current_user`, `RequirePermission`).
- **C-21 (`api-horarios-y-bloqueos`)**: horarios de atención (`/api/professionals/:id/working-hours`) y bloqueos (`/api/blocks`).
- **C-22 (`api-dar-turno`)**: `POST /api/appointments`, validaciones de agenda anti-solapamiento y bloqueo pesimista `SELECT ... FOR UPDATE`.
- **C-23 y C-24**: ciclo de vida de turnos y lectura de agenda combinada.
- **Borrado o desactivación de pacientes**: ni la KB (KB 03, KB 04, KB 06 US-022) ni la matriz RBAC (fila 30 denegada a todos los roles) permiten borrar o desactivar pacientes en el MVP.

---

## 2. Estado actual

### 2.1. Backend existente

| Capa / Componente | Ubicación | Estado actual y relevancia para C-20 |
|-------------------|-----------|--------------------------------------|
| **Dominio puro (C-09)** | `app/domain/catalog/` | `create_professional`, `create_chair`, `create_service`, `create_patient` validan altas; `deactivate` y `reactivate` en `activation.py` son funciones puras idempotentes. Falta formalizar validación de edición. |
| **Reglas de dominio** | `app/domain/rules/` | `catalog_names.py` (unicidad normalizada y nombres no vacíos), `dni.py` (7 u 8 dígitos, sin puntos ni espacios), `duration.py` (múltiplo de 5, 5 a 480 min). |
| **Repositorios (C-15)** | `app/repositories/catalog.py`, `patients.py` | Implementan `create`, `get_by_id`, `list`, `deactivate`, `reactivate`. Ninguno implementa `update` todavía; ninguno hace `commit` (solo `flush` y `begin_nested`). |
| **Servicios de C-17** | `app/services/appointments.py` | Estableció el precedente de la capa de servicios de aplicación en `app/services/` con transaccionalidad `auto_commit=True`. |
| **Infraestructura API (C-18)** | `app/main.py`, `app/api/deps.py`, `app/api/errors.py` | `create_app` con prefijo `/api`; inyección de sesión `get_db_session` (sin commit); manejadores globales de `DomainRejectedError` (`409`/`422`/`403`) y `RequestValidationError` (`400`). |
| **Seguridad y RBAC (C-19)** | `app/auth/`, `app/api/deps.py` | `RequirePermission(Resource, Action)` inyecta `Permission` o lanza `DomainRejectedError(FORBIDDEN_OPERATION)`. Guardián `routes_without_permission` exige que toda ruta protegida declare su celda RBAC. |
| **Base de datos de prueba** | `tests/integration/conftest.py`, `auth_support.py` | Fixtures `test_engine`, `auth_client`, `auth_users` (con `administrador`, `recepcion`, `odontologo`) y helper `clean_database_tables`. |

---

## 3. Decisiones de diseño (`D1`–`D14`)

### D1 — Estructura de capas de aplicación: `services/` vs `usecases/`

- **Problema**: `CHANGES.md` §[C-20] y KB 08 mencionan "Casos de uso en `usecases/`", pero C-17 ya introdujo `backend/app/services/appointments.py`. Tener dos directorios (`app/services/` y `app/usecases/`) para la misma responsabilidad arquitectónica (orquestar dominio, repositorios y transacciones) fragmenta la base de código.
- **Opciones**:
  - *Opción A*: Consolidar en `app/services/` (`services/catalog.py` y `services/patients.py`), siguiendo el precedente establecido por C-17.
  - *Opción B*: Crear `app/usecases/` (`usecases/catalog.py` y `usecases/patients.py`) de forma literal a `CHANGES.md`, dejando `services/` y `usecases/` coexistiendo.
  - *Opción C*: Renombrar `services/` a `usecases/` moviendo también el código de C-17.
- **Recomendación**: **Opción A (`services/`)**. C-17 ya cuenta con 436 líneas probadas y validadas en `backend/app/services/appointments.py`. La Opción B introduce dos carpetas paralelas para la misma capa de aplicación, generando ambigüedad sobre dónde ubicar futuros servicios (C-21, C-22). La Opción C implicaría modificar archivos de C-17 fuera del alcance de C-20. Documentar la unificación en `services/` como decisión de coherencia arquitectónica.

---

### D2 — Organización de módulos: servicios por dominio y routers por recurso

- **Problema**: Cómo estructurar los archivos de servicios y los endpoints en `backend/app/api/`.
- **Opciones**:
  - *Opción A*: Dos archivos de servicios (`services/catalog.py` y `services/patients.py`) espejando los repositorios existentes (`repositories/catalog.py` y `repositories/patients.py`). En `app/api/`, cuatro routers independientes: `professionals.py`, `chairs.py`, `services.py` y `patients.py`.
  - *Opción B*: Un único archivo de servicio `services/catalog_and_patients.py` y un único router `api/catalog.py` con todas las rutas mezcladas.
  - *Opción C*: Cuatro servicios y cuatro routers (un par por cada entidad).
- **Recomendación**: **Opción A**. Espeja la cohesión de los repositorios existentes (los catálogos físicos y de prestaciones del consultorio comparten ciclo de vida y activación en `catalog.py`; pacientes es un agregado independiente en `patients.py`). En la API REST, tener cuatro routers modulares permite asignar a cada uno su propio tag de Swagger (`Profesionales`, `Sillones`, `Prestaciones`, `Pacientes`), manteniendo los archivos pequeños, claros y de fácil mantenimiento.

---

### D3 — Lista completa de endpoints, contratos HTTP y matriz RBAC

- **Problema**: Definir unívocamente todos los endpoints, sus verbos HTTP, la celda exacta de la matriz RBAC de D9 de C-19, status de éxito y todos los códigos de error posibles.
- **Recomendación**: Los 22 endpoints descritos en la siguiente tabla normativa:

| # | Método | Ruta | Recurso RBAC | Acción RBAC | Admin | Recep | Odont | Status Éxito | Errores Posibles |
|---|--------|------|--------------|-------------|:-----:|:-----:|:-----:|:------------:|------------------|
| 1 | `GET` | `/api/professionals` | `PROFESSIONAL` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 2 | `GET` | `/api/professionals/{id}` | `PROFESSIONAL` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 3 | `POST` | `/api/professionals` | `PROFESSIONAL` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `422` (`EMPTY_NAME`) |
| 4 | `PUT` | `/api/professionals/{id}` | `PROFESSIONAL` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `422` (`EMPTY_NAME`) |
| 5 | `DELETE` | `/api/professionals/{id}` | `PROFESSIONAL` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 6 | `POST` | `/api/professionals/{id}` `/reactivate` | `PROFESSIONAL` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 7 | `GET` | `/api/chairs` | `CHAIR` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 8 | `GET` | `/api/chairs/{id}` | `CHAIR` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 9 | `POST` | `/api/chairs` | `CHAIR` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`) |
| 10 | `PUT` | `/api/chairs/{id}` | `CHAIR` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`) |
| 11 | `DELETE` | `/api/chairs/{id}` | `CHAIR` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 12 | `POST` | `/api/chairs/{id}` `/reactivate` | `CHAIR` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 13 | `GET` | `/api/services` | `SERVICE` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 14 | `GET` | `/api/services/{id}` | `SERVICE` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 15 | `POST` | `/api/services` | `SERVICE` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`, `INVALID_DURATION`) |
| 16 | `PUT` | `/api/services/{id}` | `SERVICE` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`, `INVALID_DURATION`) |
| 17 | `DELETE` | `/api/services/{id}` | `SERVICE` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 18 | `POST` | `/api/services/{id}` `/reactivate` | `SERVICE` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 19 | `GET` | `/api/patients` | `PATIENT` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 20 | `GET` | `/api/patients/{id}` | `PATIENT` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 21 | `POST` | `/api/patients` | `PATIENT` | `CREATE` | todos | todos | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_DNI`), `422` (`EMPTY_NAME`, `INVALID_DNI`) |
| 22 | `PUT` | `/api/patients/{id}` | `PATIENT` | `UPDATE` | todos | todos | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_DNI`), `422` (`EMPTY_NAME`, `INVALID_DNI`) |

*Notas sobre la tabla*:
- Las columnas *Admin*, *Recep* y *Odont* reflejan la matriz RBAC de D9 de C-19: `todos` = permitido; `—` = denegado (`403` con mensaje exacto de D9).
- Paciente **no** tiene fila de desactivación ni borrado (ver D14).
- Toda ruta protegida valida automáticamente el token Bearer (`401` si falta o no es válido).
- Toda ruta que recibe JSON o path parameters valida el esquema (`400` si es inválido).

---

### D4 — Desactivación y reactivación: `DELETE` y endpoint explícito `POST .../reactivate`

- **Problema**: Cómo modelar la desactivación lógica y la reactivación en la API REST y cómo mapearlas a la matriz RBAC.
- **Opciones**:
  - *Opción A*: `DELETE /api/{recurso}/{id}` desactiva el recurso (`active=False`), mapeando a `Action.DELETE` de RBAC. Para reactivar, `POST /api/{recurso}/{id}/reactivate` (`active=True`), mapeando a `Action.UPDATE`. Ambos devuelven `200 OK` con la entidad actualizada.
  - *Opción B*: Dos endpoints de acción RPC: `POST /api/{recurso}/{id}/deactivate` y `POST /api/{recurso}/{id}/reactivate`.
  - *Opción C*: `PATCH /api/{recurso}/{id}` enviando `{ "active": false }` o `{ "active": true }`.
- **Recomendación**: **Opción A**. 
  1. `DELETE /api/{recurso}/{id}` es el estándar REST universal para borrado lógico (soft delete). En C-19 D9 se explicitó textualmente: *"Filas 18, 22 y 26: 'borrar' es desactivar (C-20)"*. Mapear `DELETE` a `Action.DELETE` respeta al 100% esa decisión.
  2. Responder `200 OK` con la entidad actualizada (en lugar de `204 No Content`) le entrega a la UI de React el nuevo estado inmediatamente sin requerir un `GET` adicional.
  3. Para reactivar, `POST /api/{recurso}/{id}/reactivate` es un endpoint semántico claro y seguro, que evita ambigüedades en `PUT`/`PATCH` y mapea naturalmente a `Action.UPDATE`.
  4. Ambas operaciones son idempotentes en el dominio (`activation.py`).

---

### D5 — Edición: `PUT` completo vs `PATCH` parcial

- **Problema**: Qué método HTTP y semántica utilizar para editar profesionales, sillones, prestaciones y pacientes.
- **Opciones**:
  - *Opción A*: `PUT /api/{recurso}/{id}` completo e idempotente. Exige enviar todos los campos editables del recurso.
  - *Opción B*: `PATCH /api/{recurso}/{id}` parcial con campos opcionales.
  - *Opción C*: Soportar `PUT` completo y además `PATCH` parcial.
- **Recomendación**: **Opción A (`PUT` completo)**.
  1. Las entidades de catálogo tienen apenas 1 o 2 campos editables (`fullName` en profesionales; `name` en sillones; `name` y `defaultDurationMin` en prestaciones; `fullName`, `dni`, `phone`, `healthInsurance` en pacientes).
  2. `PUT` completo garantiza que el cliente envíe la totalidad de los datos requeridos por las reglas del dominio, evitando estados intermedios ambiguos (ej. diferenciar entre omitir un campo y querer ponerlo en `null` o vacío).
  3. La validación en el dominio se mantiene limpia y determinista.

---

### D6 — Validación de unicidad en edición sin colisión con la propia entidad

- **Problema**: En `create_chair`, `create_service` y `create_patient`, la validación de unicidad de nombre (`DUPLICATE_NAME`) o DNI (`DUPLICATE_DNI`) compara contra la colección de entidades existentes. Si se edita una entidad conservando su nombre o DNI (o cambiando solo otro campo, como el teléfono de un paciente), la verificación no debe rechazar la operación por duplicado consigo misma.
- **Opciones**:
  - *Opción A*: En el dominio, crear funciones de actualización pura (`update_chair`, `update_service`, `update_patient`, `update_professional`) o parametrizar las existentes con `exclude_id: UUID | None = None`. En el repositorio / servicio, filtrar la colección de existentes para excluir la entidad que se está editando (`item.id != target_id`).
  - *Opción B*: No chequear unicidad en el dominio durante la edición y delegar el chequeo exclusivamente en las restricciones de base de datos (`IntegrityError`).
  - *Opción C*: Comparar si el campo clave cambió respecto al registro en base de datos; si no cambió, omitir el llamado al dominio.
- **Recomendación**: **Opción A**. La regla dura del proyecto prohíbe delegar reglas de negocio a la base de datos o saltear el dominio. Al proveer funciones de validación en `domain/catalog/update.py` (o filtrar la colección pasada a la regla excluyendo el `id` actual), el dominio se mantiene puro, testeable con pytest sin base de datos y respetando Strict TDD. El repositorio además captura `IntegrityError` en `begin_nested()` como salvaguarda concurrente secundaria (patrón de C-15).

---

### D7 — Listados: filtrado por estado activo, ordenamiento alfabético y búsqueda

- **Problema**: En `GET /api/professionals`, `/api/chairs`, `/api/services`, `/api/patients`: ¿se listan todos? ¿cómo se filtra por activos/inactivos? ¿cómo se ordenan los resultados? ¿se incluye paginación?
- **Opciones**:
  - *Opción A*: 
    - Catálogos (`professionals`, `chairs`, `services`): soportan parámetro de consulta opcional `active: bool | None = None`. Si se omite (`None`), devuelve todos (útil para administración); si `true`, solo activos (útil para agenda C-22); si `false`, solo inactivos.
    - Ordenamiento: alfabético por defecto (`ORDER BY name` / `full_name ASC`).
    - Pacientes: no tiene campo `active`; soporta búsqueda opcional por texto `query: str | None = None` (coincidencia de prefijo/parcial en DNI o nombre).
    - Sin paginación en el MVP.
  - *Opción B*: Listados fijos sin parámetros de consulta; el frontend filtra todo en memoria.
  - *Opción C*: Paginación obligatoria con `page` y `limit` en todos los recursos.
- **Recomendación**: **Opción A**.
  1. En consultorios odontológicos de 2 a 5 profesionales, un puñado de sillones y pocas decenas de prestaciones, la paginación agrega complejidad innecesaria.
  2. El parámetro `active` permite a la pantalla de configuración ver y reactivar elementos inactivos, y a los selectores de turnos (C-22) traer solo los activos sin filtrar en el cliente.
  3. El orden alfabético (`ORDER BY full_name / name ASC`) es muy superior para la experiencia de usuario frente al orden por `id` actual de los repositorios.
  4. La búsqueda básica en pacientes (`query`) es vital para la secretaria en recepción al registrar turnos (US-022).

---

### D8 — Manejo de entidad no encontrada: `404 Not Found` vs `422 UNKNOWN_REFERENCE`

- **Problema**: Cuando un cliente invoca `GET`, `PUT` o `DELETE` sobre `/api/{recurso}/{id}` y ese `id` no existe en la base, ¿qué status y cuerpo debe retornar la API?
- **Opciones**:
  - *Opción A*: `404 Not Found` con cuerpo estándar `{ "detail": "Profesional no encontrado." }` (o mensaje específico por entidad).
  - *Opción B*: `422` con violación `UNKNOWN_REFERENCE` en `{ "violations": [...] }`.
  - *Opción C*: `404` con `{ "violations": [{ "code": "UNKNOWN_REFERENCE", "message": "..." }] }`.
- **Recomendación**: **Opción A (`404 Not Found`)**.
  1. `UNKNOWN_REFERENCE: 422` es una regla de validez del dominio cuando una entidad compuesta hace referencia a una clave foránea inexistente (ej. dar un turno con un `chair_id` inexistente, tal como fijó C-18 D1).
  2. Cuando el endpoint REST puntual opera directamente sobre una ruta cuyo ID no existe (`/api/chairs/{id}`), el estándar HTTP universal y la convención de FastAPI es `404 Not Found`.

---

### D9 — Transaccionalidad: `commit` explícito en la capa de servicios

- **Problema**: La dependencia `get_db_session` de C-18 no hace commit automático (diseñada deliberadamente así en C-18 D10 y la spec `api-foundation`). ¿Dónde debe ejecutarse el `session.commit()` de las altas, ediciones y desactivaciones?
- **Opciones**:
  - *Opción A*: En la capa de servicios de aplicación (`services/catalog.py` y `services/patients.py`), con parámetro `auto_commit: bool = True` (idéntico al patrón establecido por C-17 en `appointments.py`).
  - *Opción B*: En el cuerpo del endpoint de FastAPI en `app/api/` antes de retornar.
  - *Opción C*: Modificar `get_db_session` para que haga commit automático al salir del generador.
- **Recomendación**: **Opción A**.
  1. Sigue exactamente el patrón ya implementado y testeado en `services/appointments.py:158` (`if auto_commit: session.commit()`).
  2. Encapsula la frontera transaccional en la capa de aplicación, permitiendo que scripts de seed o fixtures de test utilicen los servicios directamente garantizando consistencia.
  3. Modificar `get_db_session` (Opción C) violaría la spec vigente `api-foundation` ("Cada request recibe su propia sesión de base, sin commit implícito") y podría provocar commits no deseados en lecturas o transacciones fallidas.

---

### D10 — Esquemas Pydantic y serialización estricta en camelCase

- **Problema**: Definir los esquemas de entrada y salida cumpliendo la regla de serialización camelCase de `api-foundation`.
- **Opciones**:
  - *Opción A*: Esquemas Pydantic V2 en `app/api/schemas.py` (o submódulo `app/api/catalog_schemas.py`) con `ConfigDict(populate_by_name=True, extra="forbid")` y alias camelCase explícitos (`serialization_alias` y `validation_alias`).
  - *Opción B*: Usar `snake_case` en los contratos JSON de la API.
- **Recomendación**: **Opción A**. Toda la API (`api-foundation`, `auth.py`, `errors.py`) utiliza camelCase en los contratos JSON externos.

#### Esquemas propuestos

```python
# Entradas (Requests) con extra="forbid"
class ProfessionalInput(BaseModel):
    full_name: str = Field(validation_alias="fullName", min_length=1, max_length=255)
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

class ChairInput(BaseModel):
    name: str = Field(validation_alias="name", min_length=1, max_length=100)
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

class ServiceInput(BaseModel):
    name: str = Field(validation_alias="name", min_length=1, max_length=100)
    default_duration_min: int = Field(validation_alias="defaultDurationMin")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

class PatientInput(BaseModel):
    full_name: str = Field(validation_alias="fullName", min_length=1, max_length=255)
    dni: str = Field(validation_alias="dni", min_length=1, max_length=20)
    phone: str | None = Field(default=None, validation_alias="phone", max_length=50)
    health_insurance: str | None = Field(default=None, validation_alias="healthInsurance", max_length=100)
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

# Salidas (Responses)
class ProfessionalResponse(BaseModel):
    id: UUID
    full_name: str = Field(serialization_alias="fullName")
    active: bool
    model_config = ConfigDict(populate_by_name=True)

class ChairResponse(BaseModel):
    id: UUID
    name: str
    active: bool
    model_config = ConfigDict(populate_by_name=True)

class ServiceResponse(BaseModel):
    id: UUID
    name: str
    default_duration_min: int = Field(serialization_alias="defaultDurationMin")
    active: bool
    model_config = ConfigDict(populate_by_name=True)

class PatientResponse(BaseModel):
    id: UUID
    full_name: str = Field(serialization_alias="fullName")
    dni: str
    phone: str | None = None
    health_insurance: str | None = Field(default=None, serialization_alias="healthInsurance")
    model_config = ConfigDict(populate_by_name=True)
```

---

### D11 — Estrategia de tests de integración con usuarios y tokens reales

- **Problema**: Probar la matriz RBAC completa y todos los códigos de retorno sin utilizar mocks ni `dependency_overrides`.
- **Opciones**:
  - *Opción A*: Reutilizar el harness existente de C-19: los 3 usuarios de prueba (`administrador`, `recepcion`, `odontologo`) insertados con `cheap_hash`, y una fixture `client_for_role(role)` o helper que ejecuta el login real (`POST /api/auth/login`) contra `TestClient` para obtener los tokens JWT genuinos. Vaciar tablas entre tests con `clean_database_tables(engine)`.
  - *Opción B*: Generar los tokens directamente en memoria con `create_access_token` sin pasar por el endpoint de login.
  - *Opción C*: Usar `dependency_overrides` en FastAPI para simular el usuario autenticado.
- **Recomendación**: **Opción A**.
  1. Las reglas duras prohíben estrictamente `dependency_overrides` y mocks en tests de dominio o integración.
  2. El login real garantiza que todo el pipeline (PostgreSQL -> `UserRepository` -> Argon2 `verify` -> JWT encode -> HTTP header Bearer -> JWT decode -> verificación de usuario activo) se ejecuta exactamente igual que en producción.
  3. Al utilizar `cheap_hash` (costos mínimos para test), la suite completa de tests de integración se ejecuta en pocos segundos.

---

### D12 — Documentación OpenAPI / Swagger y modelos de error

- **Problema**: Documentar cada endpoint en Swagger con sus tags, descripciones, seguridad JWT y respuestas de error precisas.
- **Opciones**:
  - *Opción A*: En cada decorador de ruta de FastAPI, declarar explícitamente `response_model`, `status_code`, `tags`, y en `responses` asociar `violation_responses(...)`, `permission_responses()` y `404`. `setup_openapi` de C-18 ya inyecta automáticamente `400` y `401`.
  - *Opción B*: Confiar únicamente en lo que FastAPI infiere por defecto.
- **Recomendación**: **Opción A**. Asegura que Swagger UI (`/api/docs`) muestre los esquemas de error exactos (`ViolationResponseSchema` con ejemplos de `DUPLICATE_NAME`, `EMPTY_NAME`, `DUPLICATE_DNI`, `INVALID_DNI`), permitiendo su verificación visual durante la defensa del TP.

---

### D13 — Endpoints de detalle individual `GET /api/{recurso}/{id}`

- **Problema**: ¿Deben incluirse endpoints para obtener una entidad individual por su ID?
- **Opciones**:
  - *Opción A*: Sí, proveer `GET /api/professionals/{id}`, `GET /api/chairs/{id}`, `GET /api/services/{id}` y `GET /api/patients/{id}`. Permiso: `Action.READ`.
  - *Opción B*: No, exponer únicamente listados generales.
- **Recomendación**: **Opción A**. Son indispensables para que el frontend (C-25 a C-30) pueda consultar o recargar una entidad antes de editarla o al navegar a una vista de detalle, y completan el contrato REST canónico. Responden `200 OK` si existe o `404 Not Found` si no existe.

---

### D14 — Inmutabilidad del ciclo de vida de pacientes: sin borrado ni desactivación

- **Problema**: Si `Patient` debe tener endpoint de borrado o desactivación.
- **Opciones**:
  - *Opción A*: No exponer ningún endpoint `DELETE` ni desactivación para pacientes.
  - *Opción B*: Crear un endpoint `DELETE /api/patients/{id}` que desactive al paciente agregando un campo `active` en la base de datos y una nueva migración Alembic.
- **Recomendación**: **Opción A**.
  1. En la matriz RBAC normativa (C-19 D9, fila 30), `Action.DELETE` sobre `PATIENT` está denegado (`—`) para todos los roles.
  2. En el modelo de dominio `Patient` y en la tabla `patient` de PostgreSQL (C-09 y C-14), `Patient` no tiene campo `active` ni estado de desactivación.
  3. Los pacientes constituyen el registro clínico histórico del consultorio; en el MVP no se eliminan físicamente para proteger la integridad referencial histórica de los turnos (RN-PA-01).

---

## 4. Riesgos y preguntas para la autora

### Riesgos identificados y mitigaciones

1. **Colisión con trabajo en curso de C-19**: Claude Code está finalizando la implementación de C-19 en `app/auth/` y `app/api/deps.py`.
   - *Mitigación*: C-20 no comenzará su implementación (`/opsx:apply`) hasta que C-19 esté formalmente completado y verificado.
2. **Validación de unicidad en edición**: Si la consulta de duplicados incluye a la propia entidad, cualquier edición que conserve el nombre o DNI fallará con `409`.
   - *Mitigación*: El servicio y repositorio filtran explícitamente `id != target_id` al verificar unicidad, y se valida con tests unitarios y de integración con casos idénticos (D6).
3. **Guardias de seguridad de C-19**: Si alguna ruta olvida declarar su celda RBAC, el guardián `test_route_guards.py` de C-19 fallará.
   - *Mitigación*: Toda ruta se monta con `permission: Annotated[Permission, Depends(RequirePermission(Resource, Action))]`.

### Preguntas para la autora

Todas las preguntas están formuladas como las decisiones **D1 a D14** para responderlas en un único mensaje (por ejemplo: *"Aprobadas D1–D14 con las opciones recomendadas"*, o indicando las variantes deseadas). Las decisiones principales a validar son:

- **D1**: Consolidar en `app/services/` (alineado a C-17) en lugar de crear una carpeta paralela `app/usecases/`.
- **D4**: Desactivación vía `DELETE /api/{recurso}/{id}` y reactivación vía `POST /api/{recurso}/{id}/reactivate`, ambos con `200 OK`.
- **D5**: Edición vía `PUT` completo e idempotente.
- **D7**: Catálogos con filtro opcional `active: bool | None = None` y orden alfabético; pacientes con búsqueda opcional `query`.
- **D8**: `404 Not Found` estándar cuando el ID de la URL no existe.
- **D9**: `commit` explícito en la capa de servicios con `auto_commit=True`.
- **D14**: Confirmación de que `Patient` no expone endpoint de borrado ni desactivación.

---

## 5. Propuesta de división en tareas (para el futuro `tasks.md` del propose)

> Nota: esta lista es preliminar dentro del explore; no se creó la carpeta del change ni `tasks.md`.

### Grupo 1 — Dominio y Repositorios: Soporte de Edición y Búsqueda
- **1.1** Dominio: Funciones puras de validación de edición en `domain/catalog/update.py` con exclusión de la propia entidad para unicidad.
- **1.2** Repositorios: Métodos `update` en `ProfessionalRepository`, `ChairRepository`, `ServiceRepository` y `PatientRepository` con soporte transaccional `flush()` y captura de `IntegrityError`.
- **1.3** Repositorios: Soporte de filtrado por `active` y ordenamiento alfabético en catálogos, y búsqueda por texto en `PatientRepository`.

### Grupo 2 — Capa de Servicios de Aplicación
- **2.1** `app/services/catalog.py`: Servicios de alta, edición, desactivación, reactivación, listado y detalle para profesionales, sillones y prestaciones, con `auto_commit=True`.
- **2.2** `app/services/patients.py`: Servicios de alta, edición, listado, búsqueda y detalle para pacientes, con `auto_commit=True`.

### Grupo 3 — Esquemas Pydantic y Routers de Catálogo
- **3.1** Esquemas de entrada y salida en `app/api/schemas.py` en `camelCase` con `extra="forbid"`.
- **3.2** `app/api/professionals.py`: Router con sus 6 endpoints, dependencias `RequirePermission` y documentación de errores.
- **3.3** `app/api/chairs.py`: Router con sus 6 endpoints y dependencias RBAC.
- **3.4** `app/api/services.py`: Router con sus 6 endpoints y dependencias RBAC.

### Grupo 4 — Router de Pacientes y Registro en la Aplicación
- **4.1** `app/api/patients.py`: Router con sus 4 endpoints y dependencias RBAC (recepción/admin).
- **4.2** Inclusión de los cuatro routers en `main.py` bajo `protected_router`.

### Grupo 5 — Tests de Integración y Matriz RBAC
- **5.1** Tests de endpoints exitosos (200 / 201) para cada recurso con los roles permitidos.
- **5.2** Tests de permisos RBAC (403 `FORBIDDEN_OPERATION`) para cada rol denegado (ej. odontólogo intentando crear sillón o paciente).
- **5.3** Tests de rechazos de dominio: 409 por duplicado de nombre y DNI, 422 por nombre vacío, duración inválida o DNI inválido.
- **5.4** Tests de entrada malformada (400), token inválido/ausente (401) y recurso no encontrado (404).

### Grupo 6 — Verificación, OpenAPI y Documentación
- **6.1** Verificación de Swagger UI y OpenAPI (`/api/docs` y `/api/openapi.json`) con guardianes de rutas.
- **6.2** Ejecución de suite completa de tests, integración, type checking con `mypy --strict` y generación de evidencias.
