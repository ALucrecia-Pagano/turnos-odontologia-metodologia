# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

Domain skills (relevant to code in this project):

| Trigger | Skill | Path |
|---------|-------|------|
| Build features or fix bugs test-first, "red-green-refactor", integration tests | tdd | C:\Users\hp\.agents\skills\tdd\SKILL.md |
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

### vitest
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
| (none found) | - | No AGENTS.md / CLAUDE.md / .cursorrules at project root yet; generated later by agent-instruction |

Related project context: `knowledge-base/` (10 canonical files), `CHANGES.md` (roadmap), `openspec/`.

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
