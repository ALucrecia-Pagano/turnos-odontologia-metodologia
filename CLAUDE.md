# turnos-odontologia — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

Sistema web de agenda de turnos para consultorios odontológicos de Argentina con 2 a 5 profesionales y varios sillones. Su diferencial: rechazar, desde un dominio Python puro y con mensajes explicativos, todo turno que se solape por profesional o por sillón, caiga fuera de horario o bloqueos, o esté en el pasado. Trabajo individual; avance el 2026-10-08 (solo Discovery, ya hecho) y entrega final el jueves 2026-10-15.

---

## Stack Tecnológico

Stack fijado por la **cátedra (2026-10-08)**, obligatorio (DD-01).

| Capa | Tecnología | Versión mínima | Notas |
|------|------------|----------------|-------|
| Lenguaje backend | Python con type hints | 3.12 | **Suposición:** 3.12 o superior; `mypy --strict` (SU-10) |
| Dominio | Python puro en `backend/app/domain` | — | No importa FastAPI, SQLAlchemy, Redis ni Pydantic. Sin I/O, sin reloj global: `now` se inyecta |
| Tests | **pytest** | 8.x | Strict TDD: cada escenario del spec tiene test automatizado |
| Backend | **FastAPI** (API REST) + Pydantic en el borde | 0.110+ / Pydantic 2 | DD-02 |
| Autenticación | **JWT** (token Bearer) | — | Reemplaza al rol simulado; C-19 (DD-11) |
| ORM y migraciones | **SQLAlchemy** + **Alembic** | 2.x / 1.x | Alembic es **Suposición** (SU-10); ORM solo en repositorios (DD-03) |
| Persistencia | **PostgreSQL** | 16 | Instantes en `timestamptz` (UTC) (DD-03, DD-07) |
| Asincronía | **Redis** | 7 | **Suposición:** sin uso en el MVP (DD-10, SU-11) |
| Zona horaria | `zoneinfo` + paquete `tzdata` | — | **Suposición:** `tzdata` para que `zoneinfo` funcione en Windows (SU-10) |
| Frontend | **React + TypeScript (`strict`) + Vite** (SPA) | React 18 / TS 5 / Vite 5 | "Frontend cuidado" (DD-04) |
| Contenedores | **Docker / Docker Compose** | Compose v2 | Servicios `backend`, `frontend`, `postgres`, `redis` (DD-05) |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [README.md](knowledge-base/README.md) | Resumen ejecutivo e índice de la KB |
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito, alcance y métricas de éxito |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura, API REST, zona horaria |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Roles y permisos (autenticación JWT, tres roles) |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, relaciones, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-AG-xx, RN-TU-xx) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E, contratos y códigos de error |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Estructura, patrones, plan de contingencia |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones (DD-xx) y suposiciones (SU-xx) |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Preguntas abiertas y riesgos |

> ⚠️ Preguntas de prioridad **Alta** en `10_preguntas_abiertas.md`, todas con una **Suposición** por defecto. Confirmalas o ajustalas antes del change que las usa:
> - **Q-06** zona horaria y granularidad (5 min, duración 5–480 min) → C-03 y C-04.
> - **Q-03** transiciones de estado válidas → C-10.
> - **Q-04** turnos existentes al crear un bloqueo que los pisa → C-06.

---

## Skills Disponibles

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Dominio** | `backend/app/domain`: reglas de agenda en Python puro, Strict TDD con pytest | `tdd` |
| **Backend API** | `backend/app`: FastAPI, Pydantic, JWT, repositorios SQLAlchemy, Alembic | `tdd` (las skills de Python/FastAPI se evalúan aparte) |
| **Frontend** | `frontend/`: React + TypeScript + Vite | `vitest` (desde C-25; las skills de React/diseño se evalúan al llegar a C-25) |
| **Orquestación** | OPSX + fundación del proyecto | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `discovery-research`, `web-scraper`, `find-skill`, `skill-creator` |

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; versionado en el repo).

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 33 changes en 6 fases (fundación → dominio: validaciones → dominio: ciclo de vida → infraestructura y persistencia: Docker Compose, PostgreSQL, SQLAlchemy, Alembic → API REST FastAPI y JWT → interfaz web React + TS + Vite), 19 gates.
- **Camino crítico** (15): `C-01 → C-02 → C-04 → C-05 → C-08 → C-11 → C-12 → C-17 → C-22 → C-23 → C-25 → C-26 → C-27 → C-29 → C-30`.
- **Primer change**: `C-01` (`fundacion-backend-y-dominio`), prerrequisito técnico de **`C-02` (`crear-turno-sin-solapamientos`)**, el change evaluado en el ciclo OPSX del TP.
- **Infraestructura** (C-13 Docker Compose + PostgreSQL, C-14 Alembic, C-19 JWT, C-25 frontend base) corre en paralelo con el dominio y no está en el camino crítico. Redis no tiene change propio (SU-11).
- **Recortables si aprieta el plazo** (en este orden): C-31, C-28, C-32, C-33, C-21. Los tests no se recortan.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** + las universales que el global no cubre.

Son contrato; romperlas es un defecto.

### Dominio

- **NUNCA** importar FastAPI, SQLAlchemy, Redis, Pydantic ni ningún I/O en `backend/app/domain`, ni llamar `datetime.now()` / `datetime.utcnow()` / `time.time()` → inyectar `now` (`datetime` con zona, UTC) y recibir el contexto (profesional, sillón, prestación, horarios, bloqueos, turnos relevantes) como parámetro.
- **NUNCA** duplicar una regla RN-AG / RN-TU en la API o en la UI → la UI puede anticipar errores, pero el rechazo definitivo es del dominio.
- **NUNCA** guardar horas locales ni usar `datetime` sin zona (*naive*) → los instantes se guardan en UTC (`timestamptz` en PostgreSQL); el horario laboral se evalúa con `zoneinfo` en `America/Argentina/Buenos_Aires`.
- **NUNCA** lanzar excepciones genéricas por una regla de negocio → devolver un resultado tipado (`Ok` o lista de violaciones) con código estable (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, …) y mensaje en español que identifique el turno o bloqueo en conflicto. En la API: `409` conflicto de agenda, `422` regla de validez, `400` entrada malformada.
- **NUNCA** aceptar un turno que se solapa con otro del mismo profesional o del mismo sillón → el sistema rechaza, no avisa y deja pasar. Los turnos cancelados o ausentes no ocupan agenda. (Regla agregada a mano por la autora, a partir del Discovery.)

### Tipos y tests

- **NUNCA** usar `Any` en Python ni dejar funciones sin type hints → type hints en todo el backend; `mypy --strict` sin errores.
- **NUNCA** usar `any` ni desactivar `strict` en el frontend TypeScript → `unknown` + narrowing; `tsconfig` estricto.
- **NUNCA** mockear colaboradores internos en los tests de dominio (pytest) → datos literales tomados del spec; el tiempo se fija con el `now` inyectado.

### Datos y código

- **NUNCA** usar datos reales de pacientes (nombres, DNI, teléfonos) en seeds, tests ni ejemplos → solo datos ficticios.
- **NUNCA** commitear claves, tokens ni archivos `.env` → el secreto de JWT (`JWT_SECRET`), la contraseña de PostgreSQL (`POSTGRES_PASSWORD`, también dentro de `DATABASE_URL`) y las contraseñas del seed van **solo** en `.env`, que está en `.gitignore`; `.env.example` lista los nombres sin valores. Nunca en `docker-compose.yml`, `Dockerfile` ni código.
- Identificadores, tipos y endpoints en **inglés** (como define la KB); mensajes al usuario, documentación y specs en **español**.

### Git

- **NUNCA** commitear ni pushear sin pedido explícito de la autora.
- Mensajes con **conventional commits en español**: `tipo: descripción` (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`).
- Cada change OPSX (C-NN) va en su propio commit; no mezclar changes.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias y gates
3. /opsx:explore                                 → explorar el change antes de proponer
4. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
5. /opsx:apply  (Strict TDD, cargando skills)    → respetando las reglas duras
6. Verify: correr los tests de cada escenario    → comprobar antes de archivar
7. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
