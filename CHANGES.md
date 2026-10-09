# CHANGES — Secuencia de Implementación

> El change evaluado en el ciclo OPSX del TP es **C-02 `crear-turno-sin-solapamientos`**; **C-01 `fundacion-backend-y-dominio`** es su prerrequisito técnico.
> Índice canónico de todos los changes del MVP de **turnos-odontologia** (agenda de turnos para consultorios odontológicos de 2 a 5 profesionales).
> Cada change es chico: una sola funcionalidad, terminable en una sesión de trabajo.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
> Alcance: solo el MVP de la sección D.3 de `docs/discovery/informe-discovery.md`. Lo diferido está en la sección **Backlog (post-MVP)**, al final.
> Stack: **decisión de la cátedra (2026-10-08)**. Backend en Python + FastAPI con JWT, SQLAlchemy, PostgreSQL y Alembic; Redis sin uso en el MVP; Docker Compose. Frontend en React + TypeScript + Vite. El dominio es un paquete de Python puro dentro del backend, probado con pytest (KB 09 §DD-01).
> No hay fechas por change. La entrega final es el jueves 2026-10-15 (el avance del 2026-10-08 solo pide el Discovery, ya hecho); el roadmap no se arma alrededor de ninguna fecha intermedia.

---

## Cómo usar este documento

1. **Identificá el change**: buscá el próximo `[ ]` cuyas dependencias estén todas en `[x]` (usá el árbol y los GATES).
2. **Leé la KB**: abrí cada archivo de "Leer antes" del change, en especial las reglas `RN-*` y los escenarios `US-*` que cita el Scope.
3. **Proponé**: `/opsx:propose C-NN-nombre-del-change` (el slug en kebab-case es el que figura en el título del change).
4. **Implementá y archivá**: `/opsx:apply` con Strict TDD (todo escenario de la KB tiene un test automatizado de pytest) y luego `/opsx:archive`.
5. **Marcá el checkbox**: pasá `Estado` de `[ ]` a `[x]` en este archivo. Si el change tiene nivel ALTO o CRITICO, frená y esperá la revisión antes de escribir código.

Convenciones: intervalos semiabiertos `[inicio, fin)`; instantes en UTC (`timestamptz` en PostgreSQL y `datetime` con zona en Python); hora local `America/Argentina/Buenos_Aires`; `now` inyectado; solo datos ficticios; el dominio es la autoridad de las reglas y no importa FastAPI, SQLAlchemy ni Redis (DD-06, DD-07). Secretos solo en `.env`; en el repo, `.env.example` sin valores.

---

## Árbol de dependencias

```
C-01 fundacion-backend-y-dominio
 ├── C-02 crear-turno-sin-solapamientos
 │    ├── C-03 validar-duracion-y-referencias
 │    ├── C-04 hora-local-y-turno-en-un-dia
 │    │    └── C-05 horario-de-atencion
 │    ├── C-06 bloqueos-de-agenda
 │    ├── C-07 no-turnos-en-el-pasado
 │    ├── C-09 catalogo-y-pacientes-dominio
 │    └── C-10 transiciones-de-estado-del-turno
 │
 │    C-03 + C-05 + C-06 + C-07
 │    └── C-08 mensajes-de-conflicto-en-espanol
 │         └── (+ C-10) C-11 reprogramar-turno
 │              └── C-12 historial-de-transiciones
 │
 └── C-13 docker-compose-y-postgres
      └── C-14 migraciones-alembic
           ├── C-18 api-base-fastapi
           └── C-15 persistencia-catalogos-y-pacientes      (también requiere C-09)
                ├── C-16 persistencia-horarios-y-bloqueos   (también C-05, C-06)
                ├── C-17 persistencia-turnos-e-historial    (también C-12)
                └── C-19 autenticacion-jwt-y-roles          (también C-18)
                     └── C-20 api-catalogos-y-pacientes     (también C-09)
                          ├── C-21 api-horarios-y-bloqueos  (también C-16, C-17)
                          ├── C-22 api-dar-turno            (también C-08, C-16, C-17)
                          │    └── C-23 api-ciclo-de-vida-del-turno   (también C-11, C-12)
                          └── C-24 api-consulta-de-agenda   (también C-17)

C-22 + C-23 + C-24
 └── C-25 frontend-base-react-vite
      └── C-26 ui-login-y-sesion                 (también C-19)
           ├── C-27 ui-agenda-diaria
           │    ├── C-28 ui-agenda-semanal
           │    ├── C-29 ui-dar-turno-con-errores
           │    │    └── C-30 ui-reprogramar-cancelar-y-estados
           │    └── C-31 ui-vista-de-recepcion-por-sillon
           ├── C-32 ui-horarios-y-bloqueos       (también C-21)
           └── C-33 ui-catalogos-y-pacientes     (también C-20)
```

### Paralelismo por fase

Los "agentes" son agentes de IA que la autora lanza en paralelo; el trabajo es individual y puede hacerse de forma secuencial siguiendo el mismo orden.

```
GATE 0: (inicio)
  → C-01 fundacion-backend-y-dominio             [Agente A]

GATE 1: C-01 ✓
  → C-02 crear-turno-sin-solapamientos           [Agente A]
  → C-13 docker-compose-y-postgres               [Agente B]

GATE 2: C-02 ✓                                    ← FORK (reglas de dominio independientes)
  → C-04 hora-local-y-turno-en-un-dia            [Agente A]
  → C-06 bloqueos-de-agenda                      [Agente C]
  → C-07 no-turnos-en-el-pasado                  [Agente C — cuando termine C-06]
  → C-03 validar-duracion-y-referencias          [Agente B — cuando termine C-14]
  → C-09 catalogo-y-pacientes-dominio            [Agente B — cuando termine C-03]
  → C-10 transiciones-de-estado-del-turno        [Agente C — cuando termine C-07]

GATE 3: C-13 ✓
  → C-14 migraciones-alembic                     [Agente B]

GATE 4: C-04 ✓
  → C-05 horario-de-atencion                     [Agente A]

GATE 5: C-03, C-05, C-06, C-07 ✓
  → C-08 mensajes-de-conflicto-en-espanol        [Agente A]

GATE 6: C-09 ✓ y C-14 ✓
  → C-15 persistencia-catalogos-y-pacientes      [Agente B]
  → C-18 api-base-fastapi                        [Agente C — cuando termine C-10]

GATE 7: C-08 ✓ y C-10 ✓
  → C-11 reprogramar-turno                       [Agente A]

GATE 8: C-15 ✓                                    ← FORK
  → C-16 persistencia-horarios-y-bloqueos        [Agente B — si C-05 ✓ y C-06 ✓]
  → C-19 autenticacion-jwt-y-roles               [Agente C — si C-18 ✓]

GATE 9: C-11 ✓
  → C-12 historial-de-transiciones               [Agente A]

GATE 10: C-19 ✓
  → C-20 api-catalogos-y-pacientes               [Agente C]

GATE 11: C-12 ✓ y C-15 ✓
  → C-17 persistencia-turnos-e-historial         [Agente A]

GATE 12: C-16, C-17, C-20 ✓                       ← FORK
  → C-22 api-dar-turno                           [Agente A]
  → C-21 api-horarios-y-bloqueos                 [Agente B]
  → C-24 api-consulta-de-agenda                  [Agente C]

GATE 13: C-22 ✓
  → C-23 api-ciclo-de-vida-del-turno             [Agente A]

GATE 14: C-22, C-23, C-24 ✓  (API de turnos completa; recién ahora arranca la UI)
  → C-25 frontend-base-react-vite                [Agente A]

GATE 15: C-25 ✓
  → C-26 ui-login-y-sesion                       [Agente A]

GATE 16: C-26 ✓                                   ← FORK
  → C-27 ui-agenda-diaria                        [Agente A]
  → C-32 ui-horarios-y-bloqueos                  [Agente B — si C-21 ✓]
  → C-33 ui-catalogos-y-pacientes                [Agente C]

GATE 17: C-27 ✓                                   ← FORK
  → C-29 ui-dar-turno-con-errores                [Agente A]
  → C-28 ui-agenda-semanal                       [Agente B]
  → C-31 ui-vista-de-recepcion-por-sillon        [Agente C]

GATE 18: C-29 ✓
  → C-30 ui-reprogramar-cancelar-y-estados       [Agente A]
```

### Camino crítico (15 changes — mínimo irreducible)

```
C-01 → C-02 → C-04 → C-05 → C-08 → C-11 → C-12 → C-17 → C-22 → C-23 → C-25 → C-26 → C-27 → C-29 → C-30*
```

- `C-30*` cierra el camino: con ese change se puede iniciar sesión y dar, ver, reprogramar, cancelar y marcar estados de turnos desde la UI sobre la API ya probada.
- La infraestructura (C-13, C-14, C-15, C-18, C-19, C-20) no está en el camino crítico: corre en paralelo con el dominio y termina antes de que se la necesite (GATE 12).
- Fuera del camino crítico (se pueden hacer en paralelo o recortar en este orden si el plazo aprieta): `C-31` (vista por sillón, diferenciador), `C-28` (vista semanal), `C-32` y `C-33` (con seeds y la API alcanza para operar; la UI de configuración es lo más postergable), `C-21` (API de horarios, los horarios pueden venir de seeds).
- **No** se recorta ningún test: la regla de contingencia de la KB es postergar vistas antes que tests (08 §Plan de contingencia).
- Redis no tiene change propio: el MVP no tiene funcionalidades asincrónicas (SU-11). Su servicio se levanta en C-13 y no se usa hasta el backlog.

### Plan óptimo con 3 agentes

| Paso | Agente A (Dominio — turnos) | Agente B (Infra + persistencia + API aux) | Agente C (Reglas de dominio + API + UI aux) |
|------|------------------------------|-------------------------------------------|---------------------------------------------|
| 1 | C-01 fundacion-backend-y-dominio | — | — |
| 2 | C-02 crear-turno-sin-solapamientos | C-13 docker-compose-y-postgres | — |
| 3 | C-04 hora-local-y-turno-en-un-dia | C-14 migraciones-alembic | C-06 bloqueos-de-agenda |
| 4 | C-05 horario-de-atencion | C-03 validar-duracion-y-referencias | C-07 no-turnos-en-el-pasado |
| 5 | C-08 mensajes-de-conflicto-en-espanol | C-09 catalogo-y-pacientes-dominio | C-10 transiciones-de-estado-del-turno |
| 6 | C-11 reprogramar-turno | C-15 persistencia-catalogos-y-pacientes | C-18 api-base-fastapi |
| 7 | C-12 historial-de-transiciones | C-16 persistencia-horarios-y-bloqueos | C-19 autenticacion-jwt-y-roles |
| 8 | C-17 persistencia-turnos-e-historial | — | C-20 api-catalogos-y-pacientes |
| 9 | C-22 api-dar-turno | C-21 api-horarios-y-bloqueos | C-24 api-consulta-de-agenda |
| 10 | C-23 api-ciclo-de-vida-del-turno | — | — |
| 11 | C-25 frontend-base-react-vite | — | — |
| 12 | C-26 ui-login-y-sesion | — | — |
| 13 | C-27 ui-agenda-diaria | C-32 ui-horarios-y-bloqueos | C-33 ui-catalogos-y-pacientes |
| 14 | C-29 ui-dar-turno-con-errores | C-28 ui-agenda-semanal | C-31 ui-vista-de-recepcion-por-sillon |
| 15 | C-30 ui-reprogramar-cancelar-y-estados | — | — |

---

## FASE 1 — Fundación y primer change

### [C-01] `fundacion-backend-y-dominio`
- **Estado**: `[x]` completado (archivado el 2026-10-08)
- **Scope**: fundación mínima en Python. Sin lógica de negocio, sin Docker, sin PostgreSQL, sin Redis y sin frontend (van en C-13, C-14 y C-25).
  - `backend/pyproject.toml`: paquete instalable (`[build-system]` con hatchling; `pip install -e ".[dev]"` en un venv local), `requires-python = ">=3.12"`, extras `dev` (pytest 8, mypy), dependencia `tzdata` (para que `zoneinfo` funcione en Windows), configuración de pytest (`testpaths = ["tests"]`) y de `mypy --strict` con `python_version = "3.12"` sobre `app` y `tests` (SU-10).
  - Paquete `backend/app/` con `backend/app/domain/__init__.py` vacío.
  - `backend/tests/domain/test_smoke.py`: test de humo que comprueba que `app.domain` es un paquete y que se resuelve al directorio `backend/app/domain` del repo.
  - Guardia de dependencias del dominio por **lista permitida** (DD-06, KB 08 §Regla de dependencias): un helper de tests analiza con `ast` todos los módulos de `app/domain` y reporta todo import cuyo primer segmento (comparado exacto, no por prefijo) no sea `__future__`, `collections`, `dataclasses`, `datetime`, `enum`, `typing`, `zoneinfo` o `tzdata`, salvo imports relativos y `app.domain.*`. Quedan prohibidos frameworks (`fastapi`, `sqlalchemy`, `redis`, `pydantic`), módulos de I/O (`os`, `pathlib`, …) y otras capas de `app`. El mensaje nombra archivo, línea e import ofensivo. Imports dinámicos: limitación documentada.
  - `.gitignore` raíz: se agregan `.venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/` (ya tenía `node_modules/` y `.env`).
  - README corto de `backend/` con cómo crear el entorno virtual, instalar y correr `pytest` y `mypy`.
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Estrategia de tests
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01, §DD-05, §DD-06, §SU-10
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico

### [C-02] `crear-turno-sin-solapamientos`
- **Estado**: `[x]` completado (archivado el 2026-10-08)
- **Scope**: es el "change 1" de la KB (DD-09). Dominio puro en Python en `backend/app/domain`, sin API, sin BD, sin JWT, sin UI. Tests con pytest.
  - `model.py`: `@dataclass(frozen=True)` `Appointment` y `Service` (con `default_duration_min`); `AppointmentStatus` (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`); instantes como `datetime` con zona (UTC).
  - `violations.py`: `ViolationCode` (`Enum`) con `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`; `Violation` (código, mensaje, id del turno que choca); resultado tipado `Ok` o lista de violaciones.
  - `intervals.py`: intervalo semiabierto `[inicio, fin)` y función de solapamiento (DD-07).
  - `rules/overlap.py`: `PROFESSIONAL_OVERLAP` (RN-AG-01) y `CHAIR_OVERLAP` (RN-AG-02) con el id del turno que choca; los estados `cancelado` y `ausente` no ocupan agenda (RN-AG-08); ambas violaciones se reportan juntas (US-003 CA-2).
  - `appointment/validate_new_appointment`: duración por defecto de la prestación o explícita (RN-AG-07); `end = start + duración`; turnos consecutivos válidos (fin == inicio); el turno nuevo nace en `reservado`.
  - Parte mínima de RN-AG-09 en `rules/duration.py`: duración <= 0 → `INVALID_DURATION` (US-007 CA-1 parcial); si hay violación de duración se devuelve `Rejected` sin evaluar solapamientos.
  - Los ids son `uuid.UUID` inyectados por el llamador (el dominio nunca genera ids); `uuid` se agrega a la allowlist de la guardia de dependencias.
  - Tests (pytest, todo escenario es un test; tablas con `@pytest.mark.parametrize`): US-001 CA-1 a CA-4, US-002 CA-1 a CA-6, US-003 CA-1 a CA-3, `INVALID_DURATION` con 0 y negativo, turno cancelado y turno ausente que no bloquean; mínimo 2 casos por comportamiento.
  - Queda afuera: horario, bloqueos, pasado, múltiplo de 5, máximo 480, referencias, medianoche, texto en español completo (van a C-03 a C-08).
- **Dependencias**: `C-01`
- **Governance**: ALTO (modelo core que todo lo demás referencia: checkpoint de revisión sobre tipos y API pública antes de seguir)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001, §US-002, §US-003, §US-007 (CA-1 parcial)
  - `knowledge-base/05_reglas_de_negocio.md` §Agenda / solapamientos (RN-AG-01, 02, 07, 08, parte de 09)
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-06, §DD-07, §DD-08, §DD-09, §SU-07
  - `knowledge-base/04_modelo_de_datos.md` §Appointment, §Service

---

## FASE 2 — Dominio: validaciones del turno

> Estos changes salen de partir en cinco el "change 2" `horarios-y-bloqueos` de la KB (decisión Q-13 + regla de tamaño: un change = una funcionalidad). Todos extienden `validate_new_appointment` agregando una regla componible en `rules/`, por lo que, salvo C-05 (que usa C-04), son independientes entre sí.

### [C-03] `validar-duracion-y-referencias`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `rules/duration.py`: duración múltiplo de 5 y máximo 480 min → `INVALID_DURATION` (RN-AG-09 completa, RN-DI-05; el caso <= 0 ya está en C-02).
  - `rules/references.py`: profesional, sillón o prestación inexistentes → `UNKNOWN_REFERENCE`; inactivos → `INACTIVE_REFERENCE`; paciente inexistente (RN-AG-11).
  - Tests: US-007 CA-1 (no múltiplo de 5, 485, 480 válido, 5 válido) y CA-2 con tablas de casos por cada tipo de referencia.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-007
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-09, §RN-AG-11, §RN-DI-05
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-02

### [C-04] `hora-local-y-turno-en-un-dia`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `intervals.py`: conversión de instante UTC a día y minutos desde las 00:00 en `America/Argentina/Buenos_Aires` con `zoneinfo.ZoneInfo` (zona recibida por parámetro, sin dependencias de framework); formateo de hora local para los mensajes.
  - `rules/same_day.py`: turno que cruza la medianoche local → rechazo (RN-AG-10, US-007 CA-3).
  - Tests: un instante UTC que en hora local cae en otro día; turno 23:30–00:30 rechazado; 23:00–23:55 válido.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-10, §RN-GL-03
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01, §SU-09, §DD-07
  - `knowledge-base/06_funcionalidades.md` §US-007 (CA-3)
  - `knowledge-base/02_descripcion_general.md` §Zona horaria

### [C-05] `horario-de-atencion`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelo `WorkingHours` (profesional, día de la semana, tramo `[inicio, fin)` en minutos locales) y validación de un conjunto de tramos: sin solapamiento ni `inicio >= fin` (RN-DI-01, RN-DI-02; US-010 CA-1 y CA-2).
  - `rules/working_hours.py`: el turno debe caer completo dentro de un tramo → `OUTSIDE_WORKING_HOURS` (RN-AG-04).
  - Tests: US-004 CA-1, CA-2, CA-3, CA-6, CA-7 (instante UTC que en hora local queda fuera); varios tramos por día; día sin tramos.
- **Dependencias**: `C-04`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004, §US-010
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-04, §RN-DI-01, §RN-DI-02, §RN-GL-03
  - `knowledge-base/04_modelo_de_datos.md` §WorkingHours

### [C-06] `bloqueos-de-agenda`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelo `Block` (profesional, `[inicio, fin)`, motivo opcional); validación `inicio < fin` (RN-DI-03; US-011 CA-1 y CA-2).
  - `rules/blocks.py`: turno que se superpone con un bloqueo → `BLOCKED_TIME` con el id del bloqueo; justo antes o justo después es válido (RN-AG-05; US-004 CA-4 y CA-5).
  - Función de dominio que, dado un bloqueo nuevo, lista los turnos activos que pisa sin cancelarlos ni moverlos (RN-DI-04; US-011 CA-3).
  - Tests: los casos anteriores más bloqueo de otro profesional (no afecta).
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004 (CA-4, CA-5), §US-011
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-05, §RN-DI-03, §RN-DI-04
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-05
  - `knowledge-base/04_modelo_de_datos.md` §Block

### [C-07] `no-turnos-en-el-pasado`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Reloj inyectado `now: datetime` (UTC) en el contexto del dominio; ninguna regla llama a `datetime.now()` (RN-GL-04, US-005 CA-4).
  - `rules/past.py`: inicio < `now` → `IN_THE_PAST`; inicio == `now` y > `now` válidos (RN-AG-06; US-005 CA-1 a CA-3).
  - Tests: los tres casos de borde con relojes fijos; un test que verifica (con `ast`) que ningún módulo de `app/domain` llama a `datetime.now`, `datetime.utcnow` ni `time.time`.
  - Idea (del explore de C-01): implementar esa detección de reloj global extendiendo el helper `ast` de la guardia de dependencias de C-01 (`tests/domain/import_guard.py`), en vez de un recorrido nuevo; C-01 no la incluye a propósito.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-06, §RN-GL-04
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Inyección de reloj)

### [C-08] `mensajes-de-conflicto-en-espanol`
- **Estado**: `[ ]` pendiente
- **Scope**: diferenciador del MVP (D.3).
  - `violations.py`: todas las violaciones llevan `code`, `message` en español, `conflicting_appointment_id` / `conflicting_block_id` y el intervalo que choca (US-006 CA-1).
  - El mensaje incluye el nombre del profesional o sillón y el rango en hora local (US-006 CA-3), usando las funciones de hora local de C-04.
  - `validate_new_appointment` compone todas las reglas (C-02, C-03, C-04, C-05, C-06, C-07) y devuelve **todas** las violaciones en el orden de RN-AG-12: referencias, duración, medianoche, pasado, horario, bloqueos, profesional, sillón (US-006 CA-2).
  - Tests: casos con varias violaciones a la vez, orden estable, texto exacto de cada mensaje.
- **Dependencias**: `C-03, C-05, C-06, C-07`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-006
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-12
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-08
  - `knowledge-base/07_flujos_principales.md` §Flujo 1

### [C-09] `catalogo-y-pacientes-dominio`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelos y validaciones puras: `Professional`, `Chair`, `Service` (nombre único, duración válida según RN-AG-09, desactivar no afecta turnos existentes), `Patient` (nombre, DNI, teléfono, obra social como texto; sin campos clínicos).
  - Alta y desactivación de profesionales y sillones (US-021 CA-1 y CA-2); prestaciones con duración (US-020 CA-1 a CA-3); paciente con DNI único y sin campos clínicos (US-022 CA-1 y CA-2).
  - Datos de ejemplo ficticios reutilizables por tests y seeds (RN-PA-02, US-022 CA-3).
  - Tests: nombre vacío, nombre duplicado, DNI duplicado, desactivación, duración inválida.
- **Dependencias**: `C-02`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021, §US-022
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PA-01, §RN-PA-02, §RN-AG-09
  - `knowledge-base/04_modelo_de_datos.md` §Professional, §Chair, §Service, §Patient, §Seed data inicial

---

## FASE 3 — Dominio: ciclo de vida del turno

### [C-10] `transiciones-de-estado-del-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `appointment/transitions.py`: tabla de RN-TU-02 en un solo lugar; terminales `atendido`, `ausente`, `cancelado`.
  - `cancel_appointment` (US-030 CA-1 y CA-2: libera profesional y sillón; desde estado terminal → `INVALID_TRANSITION`) y `change_status` a confirmado, atendido o ausente (US-032).
  - Reglas de tiempo: `atendido` y `ausente` solo con `now >= inicio` (RN-TU-05, `now` inyectado); sin anticipación mínima para cancelar (RN-TU-04).
  - Propiedad: el odontólogo solo modifica turnos propios; recepción y administrador, todos (RN-AC-01, US-032 CA-3; el actor entra como parámetro).
  - Tests exhaustivos de la tabla de transiciones (todas las combinaciones origen/destino con `parametrize`) y de los casos de actor.
  - Todavía sin historial (lo agrega C-12).
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-032
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-02, §RN-TU-04, §RN-TU-05, §RN-AC-01
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-03, §SU-08
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/07_flujos_principales.md` §Flujo 3

### [C-11] `reprogramar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `appointment/reschedule`: cambiar inicio, profesional, sillón y/o duración; revalida **todas** las reglas de `validate_new_appointment` excluyendo al propio turno (RN-TU-03, US-031 CA-1).
  - No se puede reprogramar al pasado (CA-2); solo desde `reservado` o `confirmado` (CA-3); el turno vuelve a `reservado` (CA-4).
  - Tests: reprogramar sobre su propio intervalo (no choca consigo mismo), choque con otro turno, al pasado, desde estado terminal, cambio de profesional y de sillón.
  - El registro en historial (CA-5) lo agrega C-12.
- **Dependencias**: `C-08, C-10`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-031
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-03, §RN-AG-06, §RN-AG-12
  - `knowledge-base/07_flujos_principales.md` §Flujo 2

### [C-12] `historial-de-transiciones`
- **Estado**: `[ ]` pendiente
- **Scope**: historial de transiciones del turno, aceptado dentro del MVP en el ciclo de vida (D.3 imprescindible 8).
  - Modelo `AppointmentStatusChange` (dataclass inmutable) con `from_status` (nulo al crear), `to_status`, `changed_by`, `changed_at` (+ detalle de reprogramación); sin operación de edición ni borrado en el dominio (RN-TU-06, US-033 CA-2).
  - `validate_new_appointment`, `cancel_appointment`, `change_status` y `reschedule` devuelven, además del turno, la entrada de historial correspondiente (RN-TU-01, US-030 CA-3, US-031 CA-5, US-033 CA-1).
  - Tests: una entrada por cada tipo de transición, `from` nulo al crear, intento de mutar una entrada rechazado (`FrozenInstanceError`), `changed_by` y `changed_at` (reloj inyectado) presentes.
- **Dependencias**: `C-10, C-11`
- **Governance**: ALTO (trazabilidad inmutable; no es un registro de auditoría de seguridad sino el historial funcional del turno con datos ficticios, por eso no se sube a CRITICO. Describir el diseño y esperar revisión antes de escribir código)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-033, §US-030 (CA-3), §US-031 (CA-5)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-01, §RN-TU-06
  - `knowledge-base/04_modelo_de_datos.md` §AppointmentStatusChange
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-03

---

## FASE 4 — Infraestructura y persistencia (Docker Compose + PostgreSQL + SQLAlchemy + Alembic)

> Corre en paralelo con las FASES 2 y 3 desde que existe C-01. Los tests de esta fase son de integración contra un PostgreSQL real (servicio de Compose) y llevan una marca de pytest (`integration`) para que los tests de dominio sigan corriendo sin Docker. Las migraciones de Alembic se encadenan por `down_revision` en el orden en que se archivan los changes: si dos changes paralelos agregan migraciones, el segundo en archivarse ajusta su `down_revision`.

### [C-13] `docker-compose-y-postgres`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `docker-compose.yml` con los servicios `postgres` (`postgres:16`, volumen nombrado, healthcheck `pg_isready`) y `redis` (`redis:7`, healthcheck `redis-cli ping`, sin uso funcional en el MVP: DD-10, SU-11). Los servicios `backend` y `frontend` los agregan C-18 y C-25.
  - Usuario, contraseña y base de PostgreSQL leídos de `.env`; ningún secreto en `docker-compose.yml`. `.env.example` con **todos** los nombres de variables de 08 §Variables de entorno, sin valores.
  - `backend/app/config.py`: lectura de variables de entorno (`DATABASE_URL`, `APP_TIMEZONE`, `REDIS_URL`, …) con error claro si falta una obligatoria.
  - `backend/app/db/session.py`: engine y sesión de SQLAlchemy 2.x a partir de `DATABASE_URL`; la sesión de BD trabaja en UTC.
  - Fixture de pytest para una base de test (`<base>_test`) y marca `integration`.
  - Tests de integración: conexión y `SELECT 1`; ida y vuelta de un `timestamptz` que conserva el instante UTC; falla clara si falta `DATABASE_URL`.
- **Dependencias**: `C-01`
- **Governance**: MEDIO (manejo de secretos por `.env`; revisar que ningún valor sensible quede versionado)
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Docker Compose, §Variables de entorno, §Seguridad
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03, §DD-05, §DD-10, §SU-11
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico, §Zona horaria

### [C-14] `migraciones-alembic`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `backend/alembic.ini` y `backend/alembic/env.py` que leen `DATABASE_URL` de la configuración (no del `.ini`) y usan el `metadata` de la base declarativa.
  - `backend/app/db/base.py`: base declarativa de SQLAlchemy con convención de nombres para constraints e índices.
  - Migración inicial (línea de base, sin tablas de negocio) y comandos documentados para `upgrade head` y `downgrade base`.
  - Tests de integración: `upgrade head` y `downgrade base` sobre la base de test sin errores; chequeo de que los modelos y las migraciones no divergen (comparación de autogenerate vacía).
- **Dependencias**: `C-13`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (convenciones)
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03, §SU-10

### [C-15] `persistencia-catalogos-y-pacientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelos SQLAlchemy `Professional`, `Chair`, `Service`, `Patient` (ids `UUID`, `boolean` para `active`, DNI único) y su migración de Alembic.
  - Repositorios de catálogos y pacientes que devuelven tipos del dominio (C-09), nunca modelos de SQLAlchemy; solo consultas con parámetros ligados.
  - `backend/app/db/seed.py` con datos 100% ficticios (profesionales, sillones, prestaciones, pacientes de 04 §Seed data inicial).
  - Tests de integración: alta, desactivación, unicidad de nombre y DNI, lectura, el seed es idempotente.
- **Dependencias**: `C-09, C-14`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (convenciones, §Professional, §Chair, §Service, §Patient, §Seed data inicial)
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Repositorio), §Seguridad
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PA-01, §RN-PA-02

### [C-16] `persistencia-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelos y migración de `working_hours` (minutos locales desde las 00:00) y `block` (`start_at`, `end_at` en `timestamptz`).
  - Repositorios de horarios y bloqueos; el guardado pasa por la validación de dominio de C-05 y C-06 (tramos válidos, `inicio < fin`).
  - Consulta de turnos afectados al crear un bloqueo (se completa con C-17; acá se expone la interfaz y se prueba con datos de prueba).
  - Tests de integración: ida y vuelta de tramos y bloqueos, rechazo de tramos solapados, eliminar un bloqueo libera el horario (US-011 CA-4).
- **Dependencias**: `C-15, C-05, C-06`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §WorkingHours, §Block
  - `knowledge-base/05_reglas_de_negocio.md` §RN-DI-01 a RN-DI-04
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011

### [C-17] `persistencia-turnos-e-historial`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelos y migración de `appointment` (`start_at`, `end_at`, `created_at`, `updated_at` en `timestamptz`; `CHECK` de estado) y `appointment_status_change` (historial solo de inserción).
  - Repositorio de turnos: carga de contexto (turnos activos del profesional y del sillón en el rango), inserción, actualización de estado y reprogramación; historial en la misma transacción (RN-GL-02).
  - Altas y reprogramaciones en una transacción que toma `SELECT ... FOR UPDATE` sobre la fila del profesional y la del sillón, siempre en el mismo orden, antes de cargar el contexto y validar (DD-03).
  - Tests de integración: turno + historial atómicos (si falla uno, no queda ninguno); dos conexiones concurrentes que intentan solapar el mismo profesional o el mismo sillón (la segunda espera el bloqueo y recibe el conflicto); el historial no se puede actualizar ni borrar a nivel repositorio.
- **Dependencias**: `C-12, C-15`
- **Governance**: ALTO (integridad de datos y concurrencia; confirmar el diseño de transacción y bloqueo de filas antes de implementar)
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Appointment, §AppointmentStatusChange
  - `knowledge-base/05_reglas_de_negocio.md` §RN-GL-01, §RN-GL-02, §RN-TU-06
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Repositorio, Transacción con `SELECT ... FOR UPDATE`)
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03

---

## FASE 5 — API REST (FastAPI) y autenticación JWT

### [C-18] `api-base-fastapi`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `backend/app/main.py` (FastAPI) con prefijo `/api`, CORS solo para `CORS_ORIGIN`, `GET /api/health` (incluye chequeo de la BD).
  - Manejo de errores uniforme: violaciones del dominio → `409` (conflicto de agenda) o `422` (regla de validez) con `{ "violations": [...] }`; entrada malformada → `400` (se reemplaza el `422` por defecto de FastAPI para errores de validación de Pydantic).
  - Dependencia de sesión de BD por request (`Depends`).
  - `backend/Dockerfile` y servicio `backend` en `docker-compose.yml`: espera a `postgres` y `redis` sanos, corre `alembic upgrade head` y levanta la app en el puerto `API_PORT`.
  - Tests con `TestClient`: salud, `400` por cuerpo malformado, mapeo de una violación de prueba a `409` y a `422`, CORS.
- **Dependencias**: `C-14`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §API REST (resumen)
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 (contrato de error y casos de error)
  - `knowledge-base/08_arquitectura_propuesta.md` §Docker Compose, §Seguridad, §Variables de entorno
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-02

### [C-19] `autenticacion-jwt-y-roles`
- **Estado**: `[ ]` pendiente
- **Scope**: reemplaza al rol simulado (DD-11). Se mantienen los tres roles y la matriz RBAC de 03.
  - Modelo y migración de `user` (`username` único, `display_name`, `password_hash`, `role` con `CHECK`, `professional_id` FK nulo, `active`).
  - Hash de contraseñas con un algoritmo lento estándar (bcrypt o argon2, SU-06); nunca texto plano.
  - `POST /api/auth/login` → token de acceso firmado con `JWT_SECRET` (`JWT_ALGORITHM`, vencimiento `JWT_EXPIRES_MIN`; claims `sub`, `role`, `exp`); `GET /api/auth/me`. Sin refresh tokens ni revocación (SU-06).
  - Dependencias `get_current_user` (Bearer, firma y vencimiento → `401`) y `require_permission(recurso, acción)` con la matriz de 03 como tabla (→ `403`) (US-050 CA-1 y CA-2).
  - Seed de un usuario por rol con contraseña tomada de `SEED_USER_PASSWORD` (ninguna credencial en el repo).
  - Tests: login correcto; contraseña incorrecta y usuario inexistente → mismo `401`; token vencido, alterado o ausente → `401`; cada rol contra rutas de prueba de la matriz (`200`/`403`); el hash ni la contraseña aparecen en respuestas.
- **Dependencias**: `C-15, C-18`
- **Governance**: CRITICO (autenticación: describir el diseño y esperar aprobación humana explícita antes de escribir código)
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC, §Autenticación en el MVP, §Rutas públicas
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AC-01, §RN-AC-02
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-11, §SU-06
  - `knowledge-base/04_modelo_de_datos.md` §User
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad, §Variables de entorno

### [C-20] `api-catalogos-y-pacientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoints `/api/professionals`, `/api/chairs`, `/api/services`, `/api/patients` (alta, edición, desactivación, listado) respetando la matriz RBAC (administrador CRUD, recepción alta/edición de pacientes, odontólogo lectura) con el usuario del JWT.
  - Casos de uso en `usecases/` que llaman al dominio (C-09) y a los repositorios (C-15); esquemas Pydantic en el borde.
  - Tests de integración (`TestClient` + PostgreSQL de test): 201/200, 400 por validación, 401 sin token, 403 por rol, 409 por nombre o DNI duplicado.
- **Dependencias**: `C-09, C-15, C-19`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021, §US-022
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Caso de uso)

### [C-21] `api-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoints de horario de atención por profesional (`GET/PUT /api/professionals/:id/working-hours`) y de bloqueos (crear, listar, eliminar), con RBAC: odontólogo CRUD sobre lo propio, recepción lectura, administrador CRUD (RN-AC-01).
  - Crear un bloqueo o cambiar un horario que pisa turnos existentes se guarda y responde la lista de turnos afectados sin cancelarlos (US-010 CA-3, US-011 CA-3).
  - Tests de integración: 403 si el odontólogo toca horarios de otro, bloqueo con turnos afectados, tramos solapados → 422.
- **Dependencias**: `C-16, C-17, C-20`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §RN-DI-04, §RN-AC-01

### [C-22] `api-dar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `POST /api/appointments`: caso de uso que abre la transacción, toma `SELECT ... FOR UPDATE` sobre profesional y sillón, carga el contexto (turnos, horarios, bloqueos, referencias), llama a `validate_new_appointment` y persiste turno + historial; el reloj es el `now` real (UTC) inyectado en el borde y `changed_by` sale del JWT.
  - Rechazo de dominio → `409`/`422` con la lista completa de violaciones (código + mensaje en español) tal como las devuelve el dominio.
  - RBAC: recepción y administrador crean; odontólogo `403`.
  - Tests de integración: turno válido (201 + entrada de historial), choque de profesional, choque de sillón, ambas violaciones juntas, fuera de horario, en bloqueo, en el pasado, y carrera de dos altas simultáneas sobre el mismo hueco.
- **Dependencias**: `C-08, C-16, C-17, C-20`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/05_reglas_de_negocio.md` §RN-GL-01, §RN-GL-02, §RN-AG-12
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados, §Estrategia de tests
  - `knowledge-base/06_funcionalidades.md` §US-001, §US-006

### [C-23] `api-ciclo-de-vida-del-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `POST /api/appointments/:id/cancel`, `POST /api/appointments/:id/reschedule`, `POST /api/appointments/:id/status` (confirmado, atendido, ausente) y `GET /api/appointments/:id/history`.
  - Transaccional con historial (turno + entrada en una sola transacción); `INVALID_TRANSITION` → `409`; odontólogo solo sobre sus turnos y con historial propio de solo lectura (RN-AC-01).
  - El historial se expone solo en lectura: no hay endpoints de edición ni borrado.
  - Tests de integración: cada transición válida e inválida, reprogramar con choque, reprogramar al pasado, `403` por rol y por propiedad, historial ordenado con `from`, `to`, `changed_by`, `changed_at`.
- **Dependencias**: `C-11, C-12, C-22`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-031, §US-032, §US-033
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-02, §RN-TU-03, §RN-TU-06
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-24] `api-consulta-de-agenda`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /api/agenda?from&to&professionalId&chairId`: turnos del rango (día o semana, en hora local `APP_TIMEZONE`) filtrables por profesional y por sillón; incluye horarios de atención y bloqueos del rango para que la UI los dibuje.
  - RBAC: odontólogo ve su agenda (y el resto en solo lectura según 03), recepción y administrador ven todo.
  - Tests de integración: filtros combinados, rango que cruza semanas, turnos cancelados incluidos con su estado, borde de medianoche local.
- **Dependencias**: `C-17, C-20`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 5
  - `knowledge-base/06_funcionalidades.md` §US-040, §US-041
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01

---

## FASE 6 — Interfaz web (React + TypeScript + Vite), al final y sobre la API probada

> La UI recién arranca con la API de turnos completa (GATE 14). Lineamientos comunes de 08 §Frontend cuidado: tokens de diseño mínimos, estados de carga/vacío/error en toda vista, mensajes del dominio mostrados tal cual, accesibilidad básica y responsive para escritorio y tablet. Los tests de componentes usan la herramienta que se elige en C-25 (SU-10).

### [C-25] `frontend-base-react-vite`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `frontend/` con Vite + React 18 + TypeScript en modo `strict`; `main.tsx`, router mínimo, estructura `features/`, `shared/` y `pages/`.
  - `shared/`: tokens de diseño (color, espaciado, tipografía), colores por estado del turno y componentes base de carga, vacío y error.
  - Cliente de API tipado con `VITE_API_URL` y manejo uniforme de `{ "violations": [...] }` (el token lo agrega C-26).
  - Elección y configuración de la herramienta de tests de componentes (SU-10), con un test de humo.
  - `frontend/Dockerfile` y servicio `frontend` en `docker-compose.yml` (puerto 5173).
  - Tests de componentes: el estado de error muestra el mensaje recibido; el estado vacío y el de carga se renderizan.
- **Dependencias**: `C-22, C-23, C-24`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado, §Estructura de directorios, §Docker Compose
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04, §SU-10
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico

### [C-26] `ui-login-y-sesion`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Pantalla de login (usuario y contraseña) contra `POST /api/auth/login`; error genérico ante credenciales inválidas.
  - El cliente de API envía `Authorization: Bearer <token>`; ante `401` se descarta el token y se vuelve al login; cierre de sesión que descarta el token.
  - Navegación y acciones visibles según el rol del usuario (`GET /api/auth/me`) (US-050); la API sigue siendo la que rechaza con `403`.
  - Tests de componentes: login correcto guarda la sesión y redirige, credenciales inválidas muestran el error, `401` devuelve al login, menú según rol.
- **Dependencias**: `C-25, C-19`
- **Governance**: ALTO (manejo del token en el cliente; acordar dónde se guarda antes de implementar)
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Autenticación en el MVP, §RBAC
  - `knowledge-base/06_funcionalidades.md` §US-050
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-11, §SU-06
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad

### [C-27] `ui-agenda-diaria`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Vista diaria con una columna por profesional, turnos coloreados por estado, horarios de atención y bloqueos visibles; filtros por profesional y por sillón (US-040 CA-1, CA-3, CA-4).
  - Navegación de día anterior/siguiente; consume `GET /api/agenda`.
  - Tests de componentes: columnas por profesional, color por estado, filtro por sillón, estado vacío.
- **Dependencias**: `C-26`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado
  - `knowledge-base/07_flujos_principales.md` §Flujo 5

### [C-28] `ui-agenda-semanal`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Vista semanal por profesional (selector de profesional) con turnos por día; alternar día/semana desde la agenda (US-040 CA-2).
  - Tests de componentes: 7 días, turnos en el día correcto en hora local, filtro por profesional.
- **Dependencias**: `C-27`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040 (CA-2)
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado, §Plan de contingencia de plazo

### [C-29] `ui-dar-turno-con-errores`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Formulario de turno: paciente, profesional, sillón, prestación, inicio, duración (sugiere la duración por defecto de la prestación; US-042 CA-2). Navegable por teclado, foco visible.
  - Muestra las violaciones del dominio tal cual (código + mensaje en español, con el turno o bloqueo que choca; US-042 CA-1); no repite las reglas en el cliente.
  - Visible solo para recepción y administrador (el odontólogo no da turnos).
  - Tests de componentes: duración sugerida, múltiples violaciones renderizadas, éxito refresca la agenda.
- **Dependencias**: `C-27`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-042, §US-006
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-30] `ui-reprogramar-cancelar-y-estados`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Acciones sobre un turno: reprogramar (reutiliza el formulario de C-29 con los errores del dominio), cancelar y cambiar estado (confirmado, atendido, ausente) solo con las transiciones válidas habilitadas.
  - Panel de historial del turno (`from`, `to`, quién, cuándo) en solo lectura.
  - Tests de componentes: botones según estado y rol, error de transición inválida mostrado, historial ordenado.
- **Dependencias**: `C-29`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-031, §US-032, §US-033, §US-042
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-02

### [C-31] `ui-vista-de-recepcion-por-sillon`
- **Estado**: `[ ]` pendiente
- **Scope**: diferenciador del MVP (D.3).
  - Vista de recepción con una columna por sillón con los turnos de todos los profesionales; los huecos libres son visibles (US-041 CA-1 y CA-2).
  - Tests de componentes: turnos de distintos profesionales en la misma columna, hueco libre entre dos turnos.
- **Dependencias**: `C-27`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-041
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado (referencias DentalBox y Open Dental)
  - `knowledge-base/01_vision_y_objetivos.md`

### [C-32] `ui-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Pantalla para que el odontólogo (y el administrador) cargue sus tramos por día de la semana y sus bloqueos; recepción solo lectura.
  - Al guardar un bloqueo o un horario que pisa turnos, muestra la lista de turnos afectados (US-010 CA-3, US-011 CA-3).
  - Tests de componentes: alta de tramos, error por tramos solapados, aviso de turnos afectados, eliminar bloqueo.
- **Dependencias**: `C-26, C-21`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-33] `ui-catalogos-y-pacientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Pantallas del administrador para profesionales, sillones y prestaciones (con duración) y de recepción/administrador para pacientes (nombre, DNI, teléfono, obra social como texto); sin campos clínicos.
  - Tests de componentes: validaciones mostradas, DNI duplicado, desactivar.
- **Dependencias**: `C-26, C-20`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021, §US-022
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PA-01, §RN-PA-02

---

## Backlog (post-MVP)

Fuera del alcance del MVP (D.3 y KB 06 §Épica 7). **No tienen C-NN y no se implementan** hasta que se decida abrir una nueva etapa; el diseño actual deja el hueco para varios de ellos (reglas componibles, `Appointment` sin acoplarse a un canal, Redis ya levantado en Compose).

| Ítem | Nota |
|------|------|
| Confirmación y recordatorio por enlace de WhatsApp (texto precargado, sin API) | Luego, API oficial de WhatsApp. Primer uso asincrónico de Redis (DD-10) |
| Reserva online del paciente con aprobación del consultorio | Requiere usuario paciente |
| Lista de espera para cubrir cancelaciones | Aviso asincrónico vía Redis (DD-10) |
| Sobreturnos controlados (con alerta, marca y autorización) | Hoy prohibidos (RN-AG-03); la regla es componible para habilitarlos |
| Regla de no solapamiento del mismo paciente (RN-PA-03) | Se agrega como una regla más en `rules/` |
| Búsqueda del primer hueco disponible (profesional + sillón + duración) | |
| Señas y cobros con Mercado Pago | |
| Facturación ARCA | |
| Obras sociales (validación de cobertura) | Hoy es solo texto en el paciente |
| Ficha clínica y odontograma | Prohibida información clínica en el MVP (RN-PA-01) |
| Multisede | |
| Reportes (p. ej. ausentismo) y exportación de datos | |
| Gestión de usuarios desde la API/UI (alta, baja, cambio de contraseña), refresh tokens y revocación de JWT | En el MVP los usuarios vienen del seed (SU-06). Gobernanza CRITICO: requiere aprobación humana explícita antes de escribir código |

---

## Resumen

| ID | Change | Fase | Depende de | Governance |
|----|--------|------|------------|------------|
| C-01 | `fundacion-backend-y-dominio` | 1 | — | BAJO |
| C-02 | `crear-turno-sin-solapamientos` | 1 | C-01 | ALTO |
| C-03 | `validar-duracion-y-referencias` | 2 | C-02 | MEDIO |
| C-04 | `hora-local-y-turno-en-un-dia` | 2 | C-02 | MEDIO |
| C-05 | `horario-de-atencion` | 2 | C-04 | MEDIO |
| C-06 | `bloqueos-de-agenda` | 2 | C-02 | MEDIO |
| C-07 | `no-turnos-en-el-pasado` | 2 | C-02 | MEDIO |
| C-08 | `mensajes-de-conflicto-en-espanol` | 2 | C-03, C-05, C-06, C-07 | MEDIO |
| C-09 | `catalogo-y-pacientes-dominio` | 2 | C-02 | BAJO |
| C-10 | `transiciones-de-estado-del-turno` | 3 | C-02 | MEDIO |
| C-11 | `reprogramar-turno` | 3 | C-08, C-10 | MEDIO |
| C-12 | `historial-de-transiciones` | 3 | C-10, C-11 | ALTO |
| C-13 | `docker-compose-y-postgres` | 4 | C-01 | MEDIO |
| C-14 | `migraciones-alembic` | 4 | C-13 | MEDIO |
| C-15 | `persistencia-catalogos-y-pacientes` | 4 | C-09, C-14 | MEDIO |
| C-16 | `persistencia-horarios-y-bloqueos` | 4 | C-15, C-05, C-06 | MEDIO |
| C-17 | `persistencia-turnos-e-historial` | 4 | C-12, C-15 | ALTO |
| C-18 | `api-base-fastapi` | 5 | C-14 | MEDIO |
| C-19 | `autenticacion-jwt-y-roles` | 5 | C-15, C-18 | CRITICO |
| C-20 | `api-catalogos-y-pacientes` | 5 | C-09, C-15, C-19 | BAJO |
| C-21 | `api-horarios-y-bloqueos` | 5 | C-16, C-17, C-20 | MEDIO |
| C-22 | `api-dar-turno` | 5 | C-08, C-16, C-17, C-20 | MEDIO |
| C-23 | `api-ciclo-de-vida-del-turno` | 5 | C-11, C-12, C-22 | MEDIO |
| C-24 | `api-consulta-de-agenda` | 5 | C-17, C-20 | BAJO |
| C-25 | `frontend-base-react-vite` | 6 | C-22, C-23, C-24 | BAJO |
| C-26 | `ui-login-y-sesion` | 6 | C-25, C-19 | ALTO |
| C-27 | `ui-agenda-diaria` | 6 | C-26 | BAJO |
| C-28 | `ui-agenda-semanal` | 6 | C-27 | BAJO |
| C-29 | `ui-dar-turno-con-errores` | 6 | C-27 | MEDIO |
| C-30 | `ui-reprogramar-cancelar-y-estados` | 6 | C-29 | MEDIO |
| C-31 | `ui-vista-de-recepcion-por-sillon` | 6 | C-27 | BAJO |
| C-32 | `ui-horarios-y-bloqueos` | 6 | C-26, C-21 | BAJO |
| C-33 | `ui-catalogos-y-pacientes` | 6 | C-26, C-20 | BAJO |

**Totales**: 33 changes en 6 fases, 19 gates (GATE 0 a GATE 18), camino crítico de 15 changes.

**Primer change recomendado**: `C-01` (`fundacion-backend-y-dominio`), y enseguida `C-02` (`crear-turno-sin-solapamientos`, el "change 1" de la KB).

Para arrancar: `/opsx:propose C-01-fundacion-backend-y-dominio`
