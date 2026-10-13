# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

Domain skills, PROJECT level (copies versioned in the repo; mirrored in `.agents/skills/`):

| Trigger | Skill | Path |
|---------|-------|------|
| Build features or fix bugs test-first, "red-green-refactor", integration tests | tdd | .claude/skills/tdd/SKILL.md |
| Writing Python tests, pytest suites, fixtures, parametrization, TDD in Python | python-testing-patterns | .claude/skills/python-testing-patterns/SKILL.md |
| Python 3.11+ type safety, mypy strict, dataclasses, async, structured error handling | python-pro | .claude/skills/python-pro/SKILL.md |
| FastAPI APIs, Pydantic models, dependencies, routers, response models | fastapi | .claude/skills/fastapi/SKILL.md |
| JWT/OAuth2/session auth, RBAC, securing APIs | auth-implementation-patterns | .claude/skills/auth-implementation-patterns/SKILL.md |
| SQLAlchemy models/queries, Alembic migrations, schema changes | sqlalchemy-alembic-expert-best-practices-code-review | .claude/skills/sqlalchemy-alembic-expert-best-practices-code-review/SKILL.md |
| Postgres schema, column types, migrations, indexes, constraints, slow queries | supabase-postgres-best-practices | .claude/skills/supabase-postgres-best-practices/SKILL.md |
| Dockerfiles, Docker Compose services, container security | docker-patterns | .claude/skills/docker-patterns/SKILL.md |
| Building/reshaping UI with intentional visual design | frontend-design | .claude/skills/frontend-design/SKILL.md |
| Writing/reviewing React components, performance patterns | vercel-react-best-practices | .claude/skills/vercel-react-best-practices/SKILL.md |
| Review UI for accessibility / UX / Web Interface Guidelines | web-design-guidelines | .claude/skills/web-design-guidelines/SKILL.md |
| Writing frontend tests, mocking, coverage (Vitest) | vitest | .claude/skills/vitest/SKILL.md |

Foundation / workflow skills (user level, NOT in the project; not for domain code):

> These are Active Stack skills, installed by Active Stack in the user's home (`~/.claude/skills/`), not in this repo. Using them requires Active Stack to be installed.

| Trigger | Skill | Path |
|---------|-------|------|
| Start project foundation flow | active-orchestrator | ~/.claude/skills/active-orchestrator/SKILL.md |
| Generate AGENTS.md / CLAUDE.md | agent-instruction | ~/.claude/skills/agent-instruction/SKILL.md |
| Discovery / market research before KB | discovery-research | ~/.claude/skills/discovery-research/SKILL.md |
| Find / install skills | find-skill | ~/.claude/skills/find-skill/SKILL.md |
| Find / install skills (alias) | find-skills | ~/.claude/skills/find-skills/SKILL.md |
| Create knowledge-base/ | kb-creator | ~/.claude/skills/kb-creator/SKILL.md |
| Generate CHANGES.md roadmap | roadmap-generator | ~/.claude/skills/roadmap-generator/SKILL.md |
| Create / improve skills | skill-creator | ~/.claude/skills/skill-creator/SKILL.md |
| Research a competitor from a URL | web-scraper | ~/.claude/skills/web-scraper/SKILL.md |

Project-level OPSX command skills (`.agents/skills/`): source-command-opsx-apply, -archive, -explore, -propose, -sync, -update.

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### tdd
- Red before green: write the failing test first, then only enough code to pass it; no speculative features.
- Work in vertical slices: one seam, one test, one minimal implementation per cycle (tracer bullet). Never write all tests first.
- Test only at pre-agreed seams (public interfaces). Before writing any test, state the seams under test (with a one-line note on what each catches/misses) and confirm them with the user.
- Test behavior through the public interface, never implementation details: no mocking internal collaborators, no testing private methods, no verifying via side channels (e.g. querying the DB instead of the interface).
- No tautological tests: expected values must come from an independent source (literal, worked example, spec), never recomputed like the code (`expect(add(a,b)).toBe(a+b)`).
- Test names read like specs ("user can checkout with valid cart") and use domain vocabulary; read GLOSSARY.md if present and respect ADRs.
- Refactoring is not part of the red-green loop; it belongs to the review stage.
- If the interface shape is in question, consult the `codebase-design` skill (reference only).
- Project overlay (Strict TDD): also triangulate with at least 2 cases per behavior and run the safety-net baseline before modifying existing files.

### python-testing-patterns
> Applies to BACKEND only (`backend/`). **PROJECT HARD RULE OVERRIDES THIS SKILL: NEVER mock internal collaborators in `backend/app/domain` tests. Do NOT use `Mock`/`MagicMock`/`patch`/`monkeypatch` of domain code, and do NOT use freezegun. Use literal data taken from the spec and the injected `now` (tz-aware UTC datetime). Mocking is allowed only at true external boundaries (e.g. API/repository tests), never in the domain.**
- AAA structure (Arrange/Act/Assert); tests independent, no shared state, each cleans up after itself.
- Names: `test_<unit>_<scenario>_<expected>`; descriptive, never `test_1`/`test_user`.
- Layout: `tests/` with `conftest.py` for shared fixtures; separate unit / integration / e2e folders.
- Use `@pytest.fixture` for setup (`tmp_path` for files) and `@pytest.mark.parametrize` for the 2+ cases per behavior (triangulation).
- In the domain, business rules return typed results (Ok / violations with stable codes), so assert on the returned code and Spanish message; use `pytest.raises` only for true programming errors.
- Time: skip freezegun; pass `now` as a parameter (domain has no global clock).
- Aim for meaningful coverage, not a percentage; no tautological assertions.
- Details in `references/details.md` (async tests, DB tests, property-based) when needed for API/repository layers.

### python-pro
> Applies to BACKEND only (`backend/`). **PROJECT HARD RULE OVERRIDES THIS SKILL where they differ: no mocks of internal collaborators in `backend/app/domain` tests (use literal spec data + injected `now`); no `datetime.now()`/`utcnow()` in domain; business-rule failures are typed results with stable codes, NOT exceptions (ignore the skill's `raise ValueError` style for domain rules); never use `Any`.**
- Full type hints on every signature and class attribute; `mypy --strict` must pass with zero errors before a task is done (set `python_version = "3.12"`).
- Use `X | None`, not `Optional[X]`; builtin generics (`list[str]`, `dict[str, int]`); `collections.abc` for abstract types; `Protocol` for interfaces.
- Prefer `@dataclass` (`frozen=True`, `slots=True` for domain values) over hand-written `__init__`; `field(default_factory=...)`, never mutable defaults.
- Use `pathlib` not `os.path`; context managers for resources; no bare `except`; no hardcoded secrets/config (env vars via `.env`).
- Async/await only for I/O-bound code (FastAPI handlers, DB); never mix sync and async improperly. Domain stays sync and pure.
- Google-style docstrings on public APIs; format with `black`, lint with `ruff`; apply auto-fixes then re-validate.
- Workflow: analyze, design interfaces (protocols/dataclasses), implement, test (pytest), validate (mypy --strict, black, ruff).
- Load `references/type-system.md`, `testing.md`, `async-patterns.md` only when the task needs them.

### fastapi
> Applies to BACKEND API only (`backend/app`, not the domain). Business rules stay in the domain; handlers map typed results to 409 (agenda conflict) / 422 (validity) / 400 (malformed).
- Use `Annotated[...]` for params and dependencies (`Path`, `Query`, `Depends`); define reusable aliases (`CurrentUserDep = Annotated[User, Depends(get_current_user)]`).
- Never use `...` (Ellipsis) as default for required params/fields; no `RootModel`.
- Declare return types or `response_model` (filters sensitive fields, serializes in Rust). Do NOT use `ORJSONResponse`/`UJSONResponse` (deprecated).
- Put `prefix`, `tags`, shared `dependencies` on the `APIRouter`, not in `include_router()`.
- Pydantic 2 models only at the HTTP edge; never leak them into `app/domain`.
- Run with the `fastapi` CLI (`fastapi dev` / `fastapi run`); entrypoint in `pyproject.toml` `[tool.fastapi]`.
- Details in `references/` (dependencies, pydantic, responses, path-operations) when needed.

### auth-implementation-patterns
> Applies to BACKEND API (C-19 JWT, 3 roles). Secrets only in `.env` (`JWT_SECRET`), never committed.
- Hash passwords with bcrypt/argon2; never store plain text.
- Short-lived access tokens (15-30 min) with expiration (`exp`); rotate secrets.
- Always authorize server-side (role check per endpoint via dependency); never trust client-side checks or client data.
- Rate limit auth endpoints; log failed logins and security events; use HTTPS.
- JWT in localStorage is XSS-prone; prefer httpOnly secure cookies, or document the tradeoff for the Bearer SPA.
- Validate all input (email format, password strength); secure password-reset tokens with expiry.
- Details in `references/details.md`.

### sqlalchemy-alembic-expert-best-practices-code-review
> Applies to infrastructure (C-13/C-14+). ORM only in repositories, never in `app/domain`.
- Create indexes with `postgresql_concurrently=True` inside an autocommit block (`op.get_context().autocommit_block()`).
- Every query pattern must be backed by an index; do not add indexes already covered by a composite index; max 3 columns on non-unique indexes.
- Unique constraints: create a unique index concurrently first, then attach the constraint using it.
- Foreign keys and CHECK constraints: add `NOT VALID` first, then `VALIDATE CONSTRAINT` in a separate step.
- Column type changes: multi-step (add new column, backfill, swap) to avoid table locks.
- Details per rule in `rules/*.md`.

### supabase-postgres-best-practices
> Applies to PostgreSQL 16 schema/migrations/queries (instants as `timestamptz`, UTC).
- Priority order: query performance, connection management, security/RLS, schema design, locking, data access, monitoring.
- Index columns used in WHERE/JOIN/ORDER BY; use partial and composite indexes where they fit; verify with EXPLAIN.
- Schema design: correct column types (`timestamptz`, not `timestamp`), explicit constraints (NOT NULL, FK, CHECK), index every foreign key.
- Overlap protection may be backed by DB constraints, but the definitive rule lives in the domain.
- Use a connection pool; keep transactions short to limit locking.
- Read `references/<prefix>-*.md` (e.g. `query-missing-indexes.md`, `_sections.md`) for the specific rule.

### docker-patterns
> Applies to C-13 (services `backend`, `frontend`, `postgres`, `redis`). Secrets NEVER in `docker-compose.yml`/Dockerfile (project hard rule): use `.env` + `.env.example` with names only.
- Pin image tags (never `:latest`); `postgres:16`, `redis:7`.
- Multi-stage Dockerfiles (deps, dev, build, production); production image minimal, run as non-root user.
- Compose: `healthcheck` + `depends_on: condition: service_healthy` for postgres; named volumes for DB data; `docker-compose.override.yml` for dev-only settings.
- Expose only needed ports; custom network, services reach each other by service name.
- Keep a `.dockerignore`; no secrets baked in image layers; drop capabilities / read-only rootfs where possible.
- Ignore the "Hardened CLI Installer Harnesses" section (not relevant here).

### frontend-design
> Applies to `frontend/` (C-25+). "Frontend cuidado" is a project requirement.
- Make deliberate, subject-specific choices of palette, type and layout; avoid templated defaults (cream + terracotta, SaaS card kit, tracked ALL-CAPS eyebrows, arrow on every button).
- Plan first (4-6 named hex colors, type roles, layout, principles), review against the brief, then build.
- One or two type families, clear type scale, line length under 80 characters; no accent-on-single-word headlines.
- Motion only to draw attention or answer a user action; respect reduced motion.
- Quality floor: responsive to mobile, visible keyboard focus, accessible contrast.
- Copy: plain user-facing language (Spanish here), active verbs ("Guardar turno"); errors say what failed and how to fix it.

### vercel-react-best-practices
> Applies to `frontend/` (React 18 + Vite SPA). Ignore Next.js/RSC/server-* rules (not applicable).
- Eliminate waterfalls: `Promise.all()` for independent fetches; defer `await` into the branch that uses it.
- Bundle: import directly, avoid barrel files; lazy-load heavy components (`React.lazy`) and defer third-party code.
- Dedupe client fetching (SWR-style); passive listeners for scroll.
- Re-renders: derive state during render (not effects); functional `setState`; primitive effect deps; `useState(() => ...)` lazy init; never define components inside components.
- Memoize only expensive work; `startTransition`/`useDeferredValue` for non-urgent updates.
- Conditional render with ternary, not `&&` on possibly falsy numbers; hoist static JSX; `content-visibility` for long lists (agenda grids).
- JS: build a `Map` for repeated lookups; batch DOM/CSS changes.

### web-design-guidelines
> Review skill for `frontend/`: fetch the latest rules with WebFetch from `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` before reviewing.
- Read the target files, apply all fetched rules, output terse `file:line` findings in the fetched format.
- If no files are given, ask which files/pattern to review.

### vitest
> Applies to FRONTEND only (`frontend/`, from C-25). Not for backend/domain Python tests.
- Config in `vitest.config.ts` (`import { defineConfig } from 'vitest/config'`) or a `test` key in `vite.config.ts` (add `/// <reference types="vitest/config" />`).
- Jest-compatible API: `describe/it/test/expect`, `vi.fn`, `vi.spyOn`, `vi.mock`; import from `vitest` explicitly unless `globals: true`.
- Environment: default `node` (use for domain and API tests); `jsdom`/`happy-dom` only for React component tests.
- Mocking via `vi` (`vi.mock` is hoisted; use `vi.hoisted` for shared vars); fake timers/dates with `vi.useFakeTimers()` / `vi.setSystemTime()`, restore after use. Useful for time-based agenda rules.
- Fixtures via `test.extend` (test context); hooks `beforeEach/afterEach/beforeAll/afterAll`.
- Filtering: `-t "name"`, file patterns, `.only/.skip/.todo`; run once with `vitest run` (CI/agents), watch mode is default otherwise.
- Coverage: `--coverage` with provider `v8` (default) or `istanbul`; needs the matching `@vitest/coverage-*` package.
- Type-level tests with `expectTypeOf` / `assertType`; multi-package setups via `projects`.
- Skill is based on Vitest 5.x: check `references/*.md` under the skill dir for details when a rule above is not enough.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | AGENTS.md | Index: stack, KB, skills per agent role, roadmap, hard rules. Copy of CLAUDE.md |
| CLAUDE.md | CLAUDE.md | Project-level instructions (same content as AGENTS.md); hard rules prevail over KB on conflict |
| CHANGES.md | CHANGES.md | Roadmap of 33 changes (C-01..C-33), 19 gates; read before any `/opsx:propose` |
| KB index | knowledge-base/README.md | Referenced by AGENTS.md |
| Vision | knowledge-base/01_vision_y_objetivos.md | Referenced by AGENTS.md |
| Overview / stack / API | knowledge-base/02_descripcion_general.md | Referenced by AGENTS.md |
| Actors and roles | knowledge-base/03_actores_y_roles.md | Referenced by AGENTS.md |
| Data model | knowledge-base/04_modelo_de_datos.md | Referenced by AGENTS.md |
| Business rules | knowledge-base/05_reglas_de_negocio.md | RN-AG-xx, RN-TU-xx |
| Features | knowledge-base/06_funcionalidades.md | Referenced by AGENTS.md |
| Main flows / error codes | knowledge-base/07_flujos_principales.md | Referenced by AGENTS.md |
| Architecture | knowledge-base/08_arquitectura_propuesta.md | Referenced by AGENTS.md |
| Decisions and assumptions | knowledge-base/09_decisiones_y_supuestos.md | DD-xx, SU-xx |
| Open questions | knowledge-base/10_preguntas_abiertas.md | Q-06, Q-03, Q-04 are high priority |

### Hard rules digest (from CLAUDE.md / AGENTS.md; they override any skill)
- Domain (`backend/app/domain`): pure Python; no FastAPI/SQLAlchemy/Redis/Pydantic/I/O; no `datetime.now()`/`utcnow()`/`time.time()` (inject `now`, tz-aware UTC); never naive datetimes; working hours via `zoneinfo` `America/Argentina/Buenos_Aires`.
- Business-rule failures return typed results (Ok or violations) with stable codes (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, ...) and Spanish messages naming the conflicting turno/bloqueo; never generic exceptions. API: 409 agenda conflict, 422 validity rule, 400 malformed input.
- Never accept overlapping turnos per professional or chair; cancelled/absent turnos do not occupy the agenda. Never duplicate RN-AG/RN-TU rules in API/UI.
- Types: no `Any` in Python, `mypy --strict`; no `any` in TS, `strict` on.
- Tests: pytest Strict TDD; NEVER mock internal collaborators in domain tests (literal spec data + injected `now`).
- Data: no real patient data; never commit secrets/`.env` (`JWT_SECRET`, `POSTGRES_PASSWORD` only in `.env`).
- Identifiers/endpoints in English; user messages, docs and specs in Spanish.
- Git: no commit/push without explicit request; conventional commits in Spanish; one commit per C-NN change.

### Skill-to-agent-role mapping (from AGENTS.md)
| Role | Scope | Skills |
|------|-------|--------|
| Dominio | `backend/app/domain` | tdd, python-testing-patterns, python-pro (with no-mock override) |
| Backend API | `backend/app` | tdd, python-testing-patterns, python-pro, fastapi, auth-implementation-patterns, sqlalchemy-alembic-expert-best-practices-code-review, supabase-postgres-best-practices |
| Infraestructura | `docker-compose.yml`, Dockerfiles, Alembic (C-13/C-14) | docker-patterns, sqlalchemy-alembic-expert-best-practices-code-review, supabase-postgres-best-practices |
| Frontend | `frontend/` (from C-25) | vitest, frontend-design, vercel-react-best-practices, web-design-guidelines |
| Orquestacion | OPSX + foundation | active-orchestrator, kb-creator, roadmap-generator, agent-instruction, discovery-research, web-scraper, find-skill, skill-creator |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted; no need to read index files to discover more.
