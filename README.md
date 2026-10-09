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
  dependencias del dominio) y C-02 (crear un turno sin solapamientos por
  profesional y por sillón).
- **Planificado:** la API REST, la base de datos y el frontend. El plan completo
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

### PowerShell

```powershell
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m mypy
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
| Implementación (equivale a `src/`) | [backend/app/domain/](backend/app/domain/) |
| Tests (equivale a `tests/`) | [backend/tests/](backend/tests/) |

Todos los datos de ejemplo y de prueba son ficticios, y el repositorio no
contiene credenciales.
