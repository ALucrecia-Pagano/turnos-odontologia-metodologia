# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

Domain skills (relevant to code in this project):

| Trigger | Skill | Path |
|---------|-------|------|
| Build features or fix bugs test-first, "red-green-refactor", integration tests | tdd | C:\Users\hp\.agents\skills\tdd\SKILL.md |
| Writing Python tests, pytest suites, fixtures, parametrization, TDD in Python | python-testing-patterns | C:\Users\hp\.agents\skills\python-testing-patterns\SKILL.md |
| Python 3.11+ type safety, mypy strict, dataclasses, async, structured error handling | python-pro | C:\Users\hp\.agents\skills\python-pro\SKILL.md |
| Writing tests, mocking, coverage config, test filtering, fixtures (Vitest) | vitest | C:\Users\hp\.agents\skills\vitest\SKILL.md |

Foundation / workflow skills (not for domain code; listed for completeness):

| Trigger | Skill | Path |
|---------|-------|------|
| Start project foundation flow | active-orchestrator | C:\Users\hp\.agents\skills\active-orchestrator\SKILL.md |
| Generate AGENTS.md / CLAUDE.md | agent-instruction | C:\Users\hp\.agents\skills\agent-instruction\SKILL.md |
| Discovery / market research before KB | discovery-research | C:\Users\hp\.agents\skills\discovery-research\SKILL.md |
| Find / install skills | find-skill | C:\Users\hp\.agents\skills\find-skill\SKILL.md |
| Find / install skills (alias) | find-skills | C:\Users\hp\.agents\skills\find-skills\SKILL.md |
| Create knowledge-base/ | kb-creator | C:\Users\hp\.agents\skills\kb-creator\SKILL.md |
| Generate CHANGES.md roadmap | roadmap-generator | C:\Users\hp\.agents\skills\roadmap-generator\SKILL.md |
| Create / improve skills | skill-creator | C:\Users\hp\.agents\skills\skill-creator\SKILL.md |
| Research a competitor from a URL | web-scraper | C:\Users\hp\.agents\skills\web-scraper\SKILL.md |

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
| Backend API | `backend/app` | tdd, python-testing-patterns, python-pro |
| Frontend | `frontend/` (from C-25) | vitest |
| Orquestacion | OPSX + foundation | active-orchestrator, kb-creator, roadmap-generator, agent-instruction, discovery-research, web-scraper, find-skill, skill-creator |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted; no need to read index files to discover more.
