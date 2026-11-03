# turnos-odontologia

Sistema web de agenda de turnos para consultorios odontológicos de Argentina con
2 a 5 profesionales y varios sillones. Rechaza, con un mensaje que explica el
motivo, todo turno que se solape con otro del mismo profesional o del mismo
sillón.

Trabajo práctico individual de **Metodología I**, UTN FRM.

## Stack

Fijado por la cátedra:

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12+ con type hints (`mypy --strict`), FastAPI, Pydantic |
| Dominio | Python puro en `backend/app/domain`, tests con pytest |
| Autenticación | JWT |
| Persistencia | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Asincronía | Redis 7 |
| Frontend | React + TypeScript (`strict`) + Vite |
| Contenedores | Docker / Docker Compose |

## Estado actual

- **Implementado:** el dominio de C-01 (fundación del backend y guardia de
  dependencias del dominio), C-02 (crear un turno sin solapamientos por
  profesional y por sillón), C-03 (validar la duración completa y que el
  paciente, el profesional, el sillón y la prestación existan y estén activos),
  C-04 (hora local: inicio en la grilla de 5 minutos y turno dentro de un
  solo día local, evaluados en la zona horaria recibida), C-05 (horario de
  atención: el turno cae completo dentro de los tramos del profesional para su
  día local, y validación del conjunto de tramos) y C-06 (bloqueos de agenda: el
  turno no pisa ningún bloqueo del profesional, comparado en instantes; validación
  de un bloqueo y lista de los turnos que pisa, sin cancelarlos) y C-07 (no dar
  turnos en el pasado: el inicio no puede ser anterior al momento actual
  inyectado; la guardia verifica que el dominio no lee el reloj del sistema), C-08
  (mensajes en español con el nombre del profesional o sillón y el rango en hora
  local, intervalo en conflicto en UTC y todas las violaciones del primer grupo
  que falla) y C-09 (altas puras de catálogo y pacientes, validación de nombres
  y DNI, activación inmutable y datos ficticios reutilizables) y C-10
  (transiciones de estado con tabla única, cancelación sin anticipación mínima,
  atendido y ausente desde el inicio con reloj inyectado, permisos por rol y
  propiedad y copias inmutables; sin historial), C-11 (reprogramación de
  turnos en el dominio, con revalidación completa, auto-exclusión, permisos y
  retorno a reservado), C-13
  (Docker Compose con PostgreSQL, Redis, configuración segura, sesión SQLAlchemy
  síncrona en UTC y tests de integración aislados) y C-14 (migraciones Alembic
  con línea de base, configuración segura, metadata con convención estable y
  ciclo reversible probado).
- **Planificado:** la API REST, la persistencia de entidades y el frontend. El
  plan completo
  está en [CHANGES.md](CHANGES.md).

## Requisitos

- Git
- Python 3.12 o superior

## Puesta en marcha

Los comandos usan el Python del entorno virtual directamente, así que no hace
falta activarlo. Si `python` no apunta a 3.12 o superior, usá `py -3.12` (o la
versión que tengas instalada) para crear el entorno.

### Git Bash

```bash
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia/backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/python -m mypy
```

### Base de datos local

Desde la raíz, copiá `.env.example` a `.env` y completalo con valores
ficticios:

```bash
cp .env.example .env
docker compose up -d
docker compose ps
```

Desde `backend/`, ejecutá los tests de integración:

```bash
.venv/Scripts/python -m pytest -m integration
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m alembic current
```

Al terminar, desde la raíz:

```bash
docker compose down
```

Si hay un PostgreSQL instalado en Windows, detenelo antes de levantar el
compose: los dos usan el puerto 5432.

### PowerShell

```powershell
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m mypy
```
### Linux / macOS

```bash
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia/backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m mypy
```

Para ver los detalles del backend (módulos del dominio, un ejemplo de uso y
cómo funciona la guardia de dependencias), leé
[backend/README.md](backend/README.md).

## Dónde está cada entregable

| Entregable | Ubicación |
|---|---|
| Informe de Discovery | [docs/discovery/informe-discovery.md](docs/discovery/informe-discovery.md) (checklist y fichas de competidores en [docs/discovery/](docs/discovery/)) |
| Informe de Discovery (PDF) | [docs/discovery/informe-discovery.pdf](docs/discovery/informe-discovery.pdf) |
| Knowledge base | [knowledge-base/](knowledge-base/) (índice en [knowledge-base/README.md](knowledge-base/README.md)) |
| Roadmap de changes | [CHANGES.md](CHANGES.md) |
| Instrucciones para agentes | [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md) |
| Skill registry | [.atl/skill-registry.md](.atl/skill-registry.md) |
| Specs vigentes | [openspec/specs/](openspec/specs/) |
| Change archivado de C-02 | [openspec/changes/archive/2026-10-08-crear-turno-sin-solapamientos/](openspec/changes/archive/2026-10-08-crear-turno-sin-solapamientos/) |
| Change archivado de C-03 | [openspec/changes/archive/2026-10-22-validar-duracion-y-referencias/](openspec/changes/archive/2026-10-22-validar-duracion-y-referencias/) |
| Change archivado de C-04 | [openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/](openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/) |
| Change archivado de C-05 | [openspec/changes/archive/2026-10-26-horario-de-atencion/](openspec/changes/archive/2026-10-26-horario-de-atencion/) |
| Change archivado de C-06 | [openspec/changes/archive/2026-10-28-bloqueos-de-agenda/](openspec/changes/archive/2026-10-28-bloqueos-de-agenda/) |
| Change archivado de C-07 | [openspec/changes/archive/2026-10-29-no-turnos-en-el-pasado/](openspec/changes/archive/2026-10-29-no-turnos-en-el-pasado/) |
| Change archivado de C-08 | [openspec/changes/archive/2026-11-01-mensajes-de-conflicto-en-espanol/](openspec/changes/archive/2026-11-01-mensajes-de-conflicto-en-espanol/) |
| Change archivado de C-09 | [openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/](openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/) |
| Change archivado de C-10 | [openspec/changes/archive/2026-11-02-transiciones-de-estado-del-turno/](openspec/changes/archive/2026-11-02-transiciones-de-estado-del-turno/) |
| Change archivado de C-11 | [openspec/changes/archive/2026-11-03-reprogramar-turno/](openspec/changes/archive/2026-11-03-reprogramar-turno/) |
| Change archivado de C-13 | [openspec/changes/archive/2026-11-02-docker-compose-y-postgres/](openspec/changes/archive/2026-11-02-docker-compose-y-postgres/) |
| Change archivado de C-14 | [openspec/changes/archive/2026-11-03-migraciones-alembic/](openspec/changes/archive/2026-11-03-migraciones-alembic/) |
| Implementación (equivale a `src/`) | [backend/app/domain/](backend/app/domain/) |
| Tests (equivale a `tests/`) | [backend/tests/](backend/tests/) |
| Evidencias (verify de C-02, explore, skills y capturas) | [docs/evidencias/](docs/evidencias/) |
| Evidencias de C-03 (explore, verify y salidas de pytest y mypy) | [explore-C-03.md](docs/evidencias/explore-C-03.md), [verify-C-03.md](docs/evidencias/verify-C-03.md), [pytest-C-03.txt](docs/evidencias/pytest-C-03.txt) y [mypy-C-03.txt](docs/evidencias/mypy-C-03.txt) |
| Evidencias de C-04 (explore, verify y salidas de pytest y mypy) | [explore-C-04.md](docs/evidencias/explore-C-04.md), [verify-C-04.md](docs/evidencias/verify-C-04.md), [pytest-C-04.txt](docs/evidencias/pytest-C-04.txt) y [mypy-C-04.txt](docs/evidencias/mypy-C-04.txt) |
| Evidencias de C-05 (explore, verify y salidas de pytest y mypy) | [explore-C-05.md](docs/evidencias/explore-C-05.md), [verify-C-05.md](docs/evidencias/verify-C-05.md), [pytest-C-05.txt](docs/evidencias/pytest-C-05.txt) y [mypy-C-05.txt](docs/evidencias/mypy-C-05.txt) |
| Evidencias de C-06 (explore, verify y salidas de pytest y mypy) | [explore-C-06.md](docs/evidencias/explore-C-06.md), [verify-C-06.md](docs/evidencias/verify-C-06.md), [pytest-C-06.txt](docs/evidencias/pytest-C-06.txt) y [mypy-C-06.txt](docs/evidencias/mypy-C-06.txt) |
| Evidencias de C-07 (explore, verify y salidas de pytest y mypy) | [explore-C-07.md](docs/evidencias/explore-C-07.md), [verify-C-07.md](docs/evidencias/verify-C-07.md), [pytest-C-07.txt](docs/evidencias/pytest-C-07.txt) y [mypy-C-07.txt](docs/evidencias/mypy-C-07.txt) |
| Evidencias de C-08 (explore, verify y salidas de pytest y mypy) | [explore-C-08.md](docs/evidencias/explore-C-08.md), [verify-C-08.md](docs/evidencias/verify-C-08.md), [pytest-C-08.txt](docs/evidencias/pytest-C-08.txt) y [mypy-C-08.txt](docs/evidencias/mypy-C-08.txt) |
| Evidencias de C-09 (explore, verify y salidas de pytest y mypy) | [explore-C-09.md](docs/evidencias/explore-C-09.md), [verify-C-09.md](docs/evidencias/verify-C-09.md), [pytest-C-09.txt](docs/evidencias/pytest-C-09.txt) y [mypy-C-09.txt](docs/evidencias/mypy-C-09.txt) |
| Evidencias de C-10 (explore, verify y salidas de pytest, mypy y TDD) | [explore-C-10.md](docs/evidencias/explore-C-10.md), [verify-C-10.md](docs/evidencias/verify-C-10.md), [pytest-C-10.txt](docs/evidencias/pytest-C-10.txt), [mypy-C-10.txt](docs/evidencias/mypy-C-10.txt) y [tdd-C-10.txt](docs/evidencias/tdd-C-10.txt) |
| Evidencias de C-11 (explore, pytest, mypy, OpenSpec y verify) | [explore-C-11.md](docs/evidencias/explore-C-11.md), [pytest-C-11.txt](docs/evidencias/pytest-C-11.txt), [mypy-C-11.txt](docs/evidencias/mypy-C-11.txt), [openspec-C-11.txt](docs/evidencias/openspec-C-11.txt) y [verify-C-11.md](docs/evidencias/verify-C-11.md) |
| Evidencias de C-13 (explore, pytest, integración, mypy y verify) | [explore-C-13.md](docs/evidencias/explore-C-13.md), [pytest-C-13.txt](docs/evidencias/pytest-C-13.txt), [pytest-integration-C-13.txt](docs/evidencias/pytest-integration-C-13.txt), [mypy-C-13.txt](docs/evidencias/mypy-C-13.txt) y [verify-C-13.md](docs/evidencias/verify-C-13.md) |
| Evidencias de C-14 (explore, pytest, integración, mypy, alembic y verify) | [explore-C-14.md](docs/evidencias/explore-C-14.md), [pytest-C-14.txt](docs/evidencias/pytest-C-14.txt), [pytest-integration-C-14.txt](docs/evidencias/pytest-integration-C-14.txt), [mypy-C-14.txt](docs/evidencias/mypy-C-14.txt), [alembic-C-14.txt](docs/evidencias/alembic-C-14.txt) y [verify-C-14.md](docs/evidencias/verify-C-14.md) |
| Reflexión final | [docs/reflexion.pdf](docs/reflexion.pdf) |

Todos los datos de ejemplo y de prueba son ficticios, y el repositorio no
contiene credenciales.
