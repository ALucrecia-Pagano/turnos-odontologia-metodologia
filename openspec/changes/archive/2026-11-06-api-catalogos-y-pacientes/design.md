# Design

## Context

La infraestructura base de la API REST (`api-foundation`, C-18) y el sistema de autenticación JWT con roles RBAC (`authentication-and-rbac`, C-19) están implementados. La API cuenta con el manejador de errores de dominio (`DomainRejectedError`), manejador de entradas malformadas (`RequestValidationError` -> 400), manejador de autenticación (401), inyección de sesión por request `get_db_session` (sin commit automático), y el guardián de autorización `RequirePermission(Resource, Action)`.

El dominio puro (`backend/app/domain/catalog/`, C-09) valida altas puras de profesionales, sillones, prestaciones y pacientes, y define `deactivate` y `reactivate` idempotentes por copia. Los repositorios SQLAlchemy (`backend/app/repositories/catalog.py` y `patients.py`, C-15) ofrecen persistencia básica sin commit (`flush` y `begin_nested`). El change C-17 fijó el precedente de la capa de servicios de aplicación en `backend/app/services/` con transaccionalidad explícita (`auto_commit=True`).

## Goals / Non-Goals

**Goals:**
- Exponer los endpoints REST para profesionales, sillones, prestaciones y pacientes.
- Respetar estrictamente la matriz RBAC de D9 de C-19 en todas las operaciones.
- Implementar servicios de aplicación en `backend/app/services/` que orquesten dominio, repositorios y transacciones.
- Proveer validación de unicidad en edición excluyendo al propio registro.
- Soportar desactivación y reactivación mediante rutas `POST` dedicadas e idempotentes.
- Manejar `404 Not Found` unificado con cuerpo `{ "code": "NOT_FOUND", "message": "<recurso> no encontrado." }`.
- Soportar el campo opcional `licenseNumber` en el profesional a nivel de API y persistencia.
- Validar mediante tests de integración con PostgreSQL real, usuarios genuinos y tokens JWT reales (sin mocks ni `dependency_overrides`).

**Non-Goals:**
- ABM o gestión de usuarios (quedó cerrado en C-19).
- Horarios de atención y bloqueos (corresponde a C-21).
- Altas de turnos y validación de solapamiento de agenda (corresponde a C-22).
- Paginación obligatoria en catálogos de consultorio pequeño (2 a 5 profesionales).
- Eliminación física o desactivación de pacientes (fuera del alcance del MVP).

## Decisions

### D1 — Estructura de capas de aplicación: unificación en `app/services/`
- **Problema**: `CHANGES.md:504` menciona `usecases/`, pero C-17 ya implementó `backend/app/services/appointments.py`. Coexistir dos directorios para la misma responsabilidad fragmentaría la arquitectura.
- **Opciones**:
  - *Opción A*: Consolidar en `backend/app/services/` (`services/catalog.py` y `services/patients.py`), alineándose a C-17.
  - *Opción B*: Crear `app/usecases/` de forma literal a CHANGES.md, manteniendo dos capas paralelas.
  - *Opción C*: Renombrar `services/` a `usecases/` tocando archivos de C-17.
- **Decisión**: **Opción A (`services/`)**. Mantiene la coherencia arquitectónica del backend sin alterar el código cerrado de C-17.

### D2 — Organización de módulos: servicios por dominio y routers por recurso
- **Problema**: Granularidad y estructuración de los archivos de servicio y routers de API.
- **Opciones**:
  - *Opción A*: Dos archivos de servicio (`services/catalog.py` y `services/patients.py`) y cuatro routers en `app/api/` (`professionals.py`, `chairs.py`, `services.py`, `patients.py`).
  - *Opción B*: Un único archivo monolítico de servicio y un único router.
  - *Opción C*: Cuatro servicios y cuatro routers individuales.
- **Decisión**: **Opción A**. Espeja la cohesión de los repositorios existentes y provee routers modulares con tags claros en Swagger (`Profesionales`, `Sillones`, `Prestaciones`, `Pacientes`).

### D3 — Lista completa de endpoints, contratos HTTP y matriz RBAC
- **Problema**: Definir unívocamente todos los endpoints y su enlace con la matriz RBAC de D9 de C-19.
- **Decisión**: Los 22 endpoints detallados a continuación:

| # | Método | Ruta | Recurso RBAC | Acción RBAC | Admin | Recep | Odont | Status Éxito | Errores Posibles |
|---|--------|------|--------------|-------------|:-----:|:-----:|:-----:|:------------:|------------------|
| 1 | `GET` | `/api/professionals` | `PROFESSIONAL` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 2 | `GET` | `/api/professionals/{id}` | `PROFESSIONAL` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 3 | `POST` | `/api/professionals` | `PROFESSIONAL` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `422` (`EMPTY_NAME`) |
| 4 | `PUT` | `/api/professionals/{id}` | `PROFESSIONAL` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `422` (`EMPTY_NAME`) |
| 5 | `POST` | `/api/professionals/{id}/deactivate` | `PROFESSIONAL` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 6 | `POST` | `/api/professionals/{id}/reactivate` | `PROFESSIONAL` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 7 | `GET` | `/api/chairs` | `CHAIR` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 8 | `GET` | `/api/chairs/{id}` | `CHAIR` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 9 | `POST` | `/api/chairs` | `CHAIR` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`) |
| 10 | `PUT` | `/api/chairs/{id}` | `CHAIR` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`) |
| 11 | `POST` | `/api/chairs/{id}/deactivate` | `CHAIR` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 12 | `POST` | `/api/chairs/{id}/reactivate` | `CHAIR` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 13 | `GET` | `/api/services` | `SERVICE` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 14 | `GET` | `/api/services/{id}` | `SERVICE` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 15 | `POST` | `/api/services` | `SERVICE` | `CREATE` | todos | — | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`, `INVALID_DURATION`) |
| 16 | `PUT` | `/api/services/{id}` | `SERVICE` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_NAME`), `422` (`EMPTY_NAME`, `INVALID_DURATION`) |
| 17 | `POST` | `/api/services/{id}/deactivate` | `SERVICE` | `DELETE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 18 | `POST` | `/api/services/{id}/reactivate` | `SERVICE` | `UPDATE` | todos | — | — | `200 OK` | `400`, `401`, `403`, `404` |
| 19 | `GET` | `/api/patients` | `PATIENT` | `READ` | todos | todos | todos | `200 OK` | `401` |
| 20 | `GET` | `/api/patients/{id}` | `PATIENT` | `READ` | todos | todos | todos | `200 OK` | `400`, `401`, `404` |
| 21 | `POST` | `/api/patients` | `PATIENT` | `CREATE` | todos | todos | — | `201 Created` | `400`, `401`, `403`, `409` (`DUPLICATE_DNI`), `422` (`EMPTY_NAME`, `INVALID_DNI`) |
| 22 | `PUT` | `/api/patients/{id}` | `PATIENT` | `UPDATE` | todos | todos | — | `200 OK` | `400`, `401`, `403`, `404`, `409` (`DUPLICATE_DNI`), `422` (`EMPTY_NAME`, `INVALID_DNI`) |

### D4 — Desactivación y reactivación: rutas dedicadas `POST` e idempotencia
- **Problema**: Evitar confusiones en Swagger al usar `DELETE` sin borrado físico.
- **Decisión**: Rutas explícitas:
  - `POST /api/{recurso}/{id}/deactivate`: autorizada con acción `DELETE` de RBAC (solo administrador).
  - `POST /api/{recurso}/{id}/reactivate`: autorizada con acción `UPDATE` de RBAC (solo administrador).
  - Ambas retornan `200 OK` con la entidad actualizada.
  - Idempotencia: desactivar un recurso ya inactivo, o reactivar uno ya activo, responde `200 OK` sin error y sin cambios.

### D5 — Estrategia de edición: `PUT` completo e idempotente
- **Problema**: Semántica de edición para recursos de catálogo y pacientes.
- **Decisión**: Se implementa `PUT /api/{recurso}/{id}` completo. En entidades con tan pocos atributos, `PUT` simplifica los esquemas, evita ambigüedades con campos omitidos vs nulos y garantiza que el cliente declare el estado deseado.

### D6 — Validación de unicidad en edición sin colisión con la propia entidad
- **Problema**: La edición de un sillón, prestación o paciente no debe colisionar con su propio nombre o DNI existente al editar otros campos.
- **Confirmación sobre el dominio actual**: Se inspeccionó `backend/app/domain/catalog/` y `rules/`: actualmente solo existen `create.py`, `activation.py` y `result.py`. Las reglas existentes (`check_duplicate_name` y `check_duplicate_dni`) solo comparan contra colecciones de cadenas (`list[str]`) y no tienen conocimiento de identificadores de entidad ni existe ninguna función de edición. Por lo tanto, la regla de unicidad que excluye el propio ID (`id != target_id`) es **nueva** y se incorpora formalmente mediante el módulo `backend/app/domain/catalog/update.py` (creado en la tarea 1.x).
- **Decisión**: Módulo `backend/app/domain/catalog/update.py` con validaciones puras (`update_chair`, `update_service`, `update_patient`, `update_professional`). La verificación de duplicados filtra la colección existente para excluir a la entidad con `id == target_id`. La regla de negocio se valida en Python puro antes de tocar la base de datos, con captura de `IntegrityError` en repositorio como protección concurrente secundaria.

### D7 — Listados: filtro por `active`, ordenamiento alfabético y búsqueda
- **Problema**: Comportamiento de los endpoints de listado `GET`.
- **Decisión**:
  - Catálogos (`professionals`, `chairs`, `services`):
    - Sin parámetro `active` (omitido): devuelve activos e inactivos, ordenados alfabéticamente por nombre (ascendente, sin distinguir mayúsculas).
    - Con `active=true`: devuelve solo activos.
    - Con `active=false`: devuelve solo inactivos (ej. reactivación en administración).
  - Pacientes:
    - Búsqueda textual mediante el parámetro `query: str | None = None`.
    - Busca por nombre como coincidencia de subcadena "contiene", sin distinguir mayúsculas (mediante `ILIKE` en PostgreSQL), donde **las tildes son significativas** (igual que SU-12 para la unicidad de nombres). Esto evita requerir la extensión `unaccent` o nuevas migraciones en la base de datos. Por ejemplo, `query="pérez"` encuentra a `"Ana Pérez"`, pero `query="perez"` no la encuentra.
    - Busca por DNI mediante coincidencia por prefijo de dígitos numéricos (ej. `query="3011"` encuentra `"30111222"`).
  - Sin paginación en el MVP.

### D8 — Manejo de entidad no encontrada: `404 Not Found` unificado
- **Problema**: Formato y manejo de error cuando un `{id}` no existe en la base, tanto en consultas como en operaciones de escritura.
- **Decisión**:
  - Excepción `NotFoundError(message: str)` en `backend/app/api/errors.py`.
  - Manejador global en `app/api/errors.py` que retorna `404` con cuerpo:
    ```json
    {
      "code": "NOT_FOUND",
      "message": "<recurso> no encontrado."
    }
    ```
  - Mismo formato clave-valor que el `401` de C-19.
  - Se aplica uniformemente a:
    - Lecturas: `GET /api/{recurso}/{id}`
    - Ediciones: `PUT /api/{recurso}/{id}`
    - Desactivaciones: `POST /api/{recurso}/{id}/deactivate`
    - Reactivaciones: `POST /api/{recurso}/{id}/reactivate`
  - Documentado en OpenAPI en todas las rutas con parámetro de ruta `{id}`.

### D9 — Transaccionalidad: `commit` explícito en la capa de servicios
- **Problema**: `get_db_session` no hace commit automático (C-18 D10).
- **Decisión**: El commit se ejecuta dentro de cada operación de mutación en `backend/app/services/catalog.py` y `patients.py` con `auto_commit: bool = True`, replicando exactamente el patrón de `services/appointments.py` (C-17).

### D10 — Esquemas Pydantic V2 en `camelCase` con `extra="forbid"`
- **Problema**: Asegurar contratos serializados en camelCase y rechazo de campos desconocidos con 400.
- **Decisión**: Esquemas en `app/api/schemas.py`:
  - `ProfessionalInput`: `fullName`, `licenseNumber: str | None = None`.
  - `ChairInput`: `name`.
  - `ServiceInput`: `name`, `defaultDurationMin`.
  - `PatientInput`: `fullName`, `dni`, `phone: str | None = None`, `healthInsurance: str | None = None`.
  - Salidas: `ProfessionalResponse` (incluye `licenseNumber`), `ChairResponse`, `ServiceResponse`, `PatientResponse`.
  - Configuración: `ConfigDict(populate_by_name=True, extra="forbid")`.

### D11 — Estrategia de tests de integración sin mocks ni overrides
- **Problema**: Probar la matriz RBAC y todos los status HTTP respetando las reglas duras.
- **Decisión**: Reutilizar el harness de C-19: base de prueba migrada en PostgreSQL, usuarios del seed insertados con `cheap_hash`, login HTTP real (`POST /api/auth/login`) para obtener los tokens de cada rol, y limpieza de tablas con `clean_database_tables(engine)` entre tests.

### D12 — Documentación OpenAPI / Swagger y modelos de error
- **Problema**: Reflejar los contratos de error en Swagger UI (`/api/docs`).
- **Decisión**: Cada ruta declara `response_model`, `status_code`, tags y en `responses` combina `violation_responses(...)`, `permission_responses()` y el modelo 404 unificado. `setup_openapi` provee 400 y 401 automáticamente.

### D13 — Endpoints de detalle individual `GET /api/{recurso}/{id}`
- **Problema**: Consulta puntual de recursos por ID.
- **Decisión**: Se implementa `GET` por ID para los cuatro recursos. Responde `200 OK` con la entidad o `404 Not Found` bajo el permiso `Action.READ`.

### D14 — Inmutabilidad del ciclo de vida de pacientes
- **Problema**: Borrado o desactivación de pacientes.
- **Decisión**: No se exponen rutas de desactivación ni de borrado físico para pacientes en el MVP. La fila 30 de la matriz RBAC de D9 de C-19 está denegada (`—`) para todos los roles, y el modelo de datos protege la integridad histórica de turnos (RN-PA-01).

### D15 — Soporte del campo opcional `licenseNumber` en profesionales
- **Problema**: La columna `license_number` existe en la tabla `professional` desde C-15, pero el modelo de dominio `Professional` no la incluye por ser puramente administrativo.
- **Decisión**: La API acepta `licenseNumber` opcional en `ProfessionalInput` y lo devuelve en `ProfessionalResponse`. Para persistirlo y leerlo sin romper la pureza del dominio de C-09:
  - `ProfessionalRepository` (C-15) se amplía con métodos o parámetros opcionales (`license_number: str | None = None` en `create` y `update`) y un método de lectura que retorne el registro completo con matrícula (`ProfessionalWithLicense` o tupla/DTO de repositorio).
  - El servicio `services/catalog.py` mapea este dato entre el esquema de la API y el repositorio.

## Risks / Trade-offs

- [Risk] Colisión con el cierre de C-19 → **Mitigación**: El apply de C-20 se ejecutará únicamente una vez que el commit de archivo de C-19 esté finalizado y verificado.
- [Risk] Falsos positivos de duplicado en edición → **Mitigación**: Las funciones de dominio en `domain/catalog/update.py` reciben y filtran `id != target_id` explícitamente, verificado con tests unitarios e integrados.
- [Risk] Rutas sin guarda RBAC → **Mitigación**: Toda ruta se monta bajo `protected_router` con `Depends(RequirePermission(Resource, Action))`, validado por los guardianes existentes de `test_route_guards.py`.

## Notas para actualizar en CHANGES.md (para la autora)

- `CHANGES.md:503`: Actualizar que la desactivación se realiza vía `POST /api/{recurso}/{id}/deactivate` y la reactivación vía `POST /api/{recurso}/{id}/reactivate` (ambas 200 con la entidad), y que se soporta `licenseNumber` opcional en profesionales.
- `CHANGES.md:504`: Actualizar que los servicios de aplicación viven en `backend/app/services/catalog.py` y `patients.py` para mantener coherencia con C-17.
