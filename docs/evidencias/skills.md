# Skills del proyecto

Las skills de desarrollo están instaladas dentro del repositorio (`.claude/skills/` y `.agents/skills/`), así que cualquiera que lo clone las tiene. Las de Active Stack (orquestación) no están en el repo: requieren tener Active Stack instalado.

Si una skill contradice una regla de `AGENTS.md`, manda la regla del proyecto. Por ejemplo: sin mocks en los tests del dominio y sin `raise ValueError` para reglas de negocio.

## Decisión por skill

| Skill | Origen | Por qué la elegí | Se usa en |
|---|---|---|---|
| `tdd` | mattpocock/skills | El proyecto trabaja con TDD estricto: primero el test que falla, después el código. | Todos los changes |
| `python-testing-patterns` | wshobson/agents | Los tests del backend se escriben con pytest. | Dominio y API |
| `python-pro` | jeffallan/claude-skills | El proyecto exige tipado estricto con mypy y sin `Any`. | Todo el backend |
| `fastapi` | fastapi/fastapi | Es la skill oficial de FastAPI, el framework de la API. | C-18 a C-24 |
| `auth-implementation-patterns` | wshobson/agents | La cátedra pide autenticación con JWT y el sistema tiene tres roles. | C-19 |
| `sqlalchemy-alembic-expert-best-practices-code-review` | wispbit-ai/skills | La persistencia usa SQLAlchemy y las migraciones, Alembic. | C-14 a C-17 |
| `supabase-postgres-best-practices` | supabase/agent-skills | Buenas prácticas de PostgreSQL (índices, restricciones, tipos de fecha). Es de Supabase, así que lo específico de esa plataforma no aplica. | C-13 a C-17 |
| `docker-patterns` | affaan-m/ecc | El entorno se levanta con Docker Compose. | C-13 |
| `vitest` | antfu/skills | Los tests del frontend con Vite se escriben con Vitest. | C-25 en adelante |
| `frontend-design` | anthropics/skills | Quiero una interfaz cuidada y que se vea bien. | C-25 en adelante |
| `vercel-react-best-practices` | vercel-labs/agent-skills | Buenas prácticas de React. Está pensada para Next.js, así que lo de servidor no aplica a React con Vite. | C-25 en adelante |
| `web-design-guidelines` | vercel-labs/agent-skills | Revisión de accesibilidad y usabilidad de la interfaz. | C-25 en adelante |

## Cómo se fue decidiendo

- **2026-10-07**: find-skill recomendó 8 skills para el stack de entonces (TypeScript). Instalé solo `tdd` y `vitest`, porque el primer change era dominio puro con tests, y descarté las de React, Fastify y diseño porque eran de capas que el roadmap dejaba para más adelante.
- **2026-10-08**: con el stack fijado por la cátedra (Python), sumé `python-testing-patterns` y `python-pro`. Dejé `fastapi` y `auth-implementation-patterns` para cuando llegaran sus changes.
- **2026-10-12**: a pedido del profesor, instalé las skills a nivel proyecto para que viajen con el repositorio, y sumé las del resto del stack (API, base de datos, Docker y frontend).