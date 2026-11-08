# Evidencia 03 — Creación de la skill `appointment-frontend-ux` con skill-creator

Fecha: 2026-11-08
Repo: turnos-odontologia
Skill: `.agents/skills/appointment-frontend-ux/` (fuente canónica), espejada en `.claude/skills/appointment-frontend-ux/`
Método: proceso de `skill-creator` (Anthropic), cargado desde `.agents/skills/skill-creator/SKILL.md`.

> Regla de seguridad respetada: la clave `CONTEXT7_API_KEY` no se escribe ni se imprime en ningún archivo, comando ni salida.

---

## 0. Comprobación previa (requisito para seguir)

**Skills disponibles.** En la lista de skills de la sesión de OpenCode figura `skill-creator` (además de las skills del proyecto: `tdd`, `python-testing-patterns`, `python-pro`, `fastapi`, `auth-implementation-patterns`, `sqlalchemy-alembic-expert-best-practices-code-review`, `supabase-postgres-best-practices`, `docker-patterns`, `frontend-design`, `vercel-react-best-practices`, `web-design-guidelines`, `vitest`, y las de orquestación). Confirmado: **`skill-creator` presente**.

**Herramientas MCP de context7.** La sesión expone `context7_resolve-library-id` y `context7_query-docs`. Confirmado: **ambas presentes**.

Como ambas comprobaciones pasan, se continúa con la creación.

---

## 1. Intención (paso "Capture Intent" de skill-creator)

Se extrajo la intención de `docs/skills-mcp/investigacion.md` §4 y del estado real del repo
(C-25, C-26, C-27 ya implementados; C-28 a C-33 pendientes):

1. **Qué debe permitir hacer la skill:** guiar el trabajo de UI de la agenda (C-25 a C-33)
   para que cada pantalla respete tokens, accesibilidad, zona horaria de la API, confinamiento
   del token de sesión y la regla C1 de tests, y para que se verifique visualmente antes de archivar.
2. **Cuándo debe dispararse:** al preparar, revisar o implementar un change de UI de la agenda;
   pedidos como "revisá los escenarios de la agenda", "¿falta algún caso en esta pantalla?",
   "implementá la vista semanal", "las tarjetas se recortan en tablet", "el estado tapa el paciente",
   "consultá la documentación de React Router", "antes de archivar, verificá visualmente".
3. **Formato de salida esperado:** para una revisión, una tabla de hallazgos con respaldo en la KB
   y escenarios GIVEN/WHEN/THEN propuestos; para implementación, código que cumpla el checklist.
4. **Casos de prueba:** sí, la skill tiene salidas objetivamente verificables (archivos, tests,
   capturas), así que se arman casos de prueba (ver §3).

## 2. Entrevista e investigación (paso "Interview and Research")

No hubo entrevista adicional: la intención, el alcance y las reglas ya estaban fijados en
`docs/skills-mcp/investigacion.md` y en el repo. Se investigó el estado real del código y las specs
para que la skill no invente reglas:

- `frontend/package.json` → versiones exactas: React 18.3.1, react-router-dom 6.30.6, Vite 5.4.21,
  Vitest 3.2.7, TypeScript 5.9.3, jsdom 31.0.0.
- `frontend/src/shared/styles/tokens.css` → tokens de diseño y tokens de agenda.
- `frontend/src/shared/styles/appointmentStatusTokens.ts` + `StatusBadge.tsx` → estado con texto y color.
- `frontend/src/features/agenda/agendaConfig.ts` → único fallback de zona horaria.
- `frontend/src/features/agenda/agendaTime.ts` → `Intl.DateTimeFormat` con `timeZone` explícito.
- `frontend/src/features/agenda/AgendaGrid.tsx` + `AgendaGrid.module.css` → formato compacto en dos líneas.
- `frontend/src/features/agenda/clock.ts` → inyección de `Clock` (`createFixedClock`).
- `frontend/src/features/auth/tokenStore.ts` → confinamiento del token.
- `docs/evidencias/verify-C-27.md` §Hallazgo de la revisión visual 2 → lección "el estado nunca
  depende solo del color" y prioridad hora/paciente sobre estado; jsdom no mide anchos.
- `openspec/changes/archive/2026-11-08-ui-agenda-diaria/` → escenarios y decisiones de C-27.
- Tests de `frontend/src/features/agenda/` → patrón C1: `fetch` inyectado, `Clock` inyectado,
  `createMemoryRouter`; sin `vi.mock`/`vi.spyOn`/`vi.stubGlobal`/fake timers/MSW.

## 3. SKILL.md (paso "Write the SKILL.md")

Archivo creado: `.agents/skills/appointment-frontend-ux/SKILL.md`.

Frontmatter:

```yaml
---
name: appointment-frontend-ux
description: Guía el trabajo de interfaz de la agenda de turnos odontológicos de este repo
  (React 18.3.1 + TypeScript strict + Vite 5 + React Router 6.30.6 + Vitest 3.2.7) ...
  Usala siempre que prepares, revises o implementes un change de UI de la agenda (C-25 a C-33) ...
---
```

La descripción es "pushy" a propósito (recomendación de skill-creator) e incluye los disparadores,
porque la descripción es el mecanismo principal de activación. El cuerpo (menos de 500 líneas)
incluye, sacado del código y las specs existentes:

- stack y versiones exactas, y **cuándo** consultar Context7 (React Router v6, React 18, Vite 5 / Vitest 3);
- tokens de diseño en `tokens.css`, nunca colores sueltos;
- accesibilidad: estado con texto visible, nunca solo color (revisión visual 2 de C-27), foco visible
  y `aria-label` completos;
- prioridad hora y paciente antes que estado, con el formato en dos líneas de C-27;
- zona horaria desde la respuesta de la API, fallback solo en `agendaConfig.ts`;
- token solo dentro de `features/auth/tokenStore.ts`;
- regla C1 de tests (sin `vi.mock`/`vi.spyOn`/`vi.stubGlobal`/fake timers/MSW; `fetch` y `Clock`
  inyectados; `MemoryRouter`);
- verificación visual obligatoria antes de archivar: capturas en escritorio (1440) y tablet (768),
  porque jsdom no mide anchos.

## 4. Casos de prueba (paso "Test Cases")

Archivo creado: `.agents/skills/appointment-frontend-ux/evals/evals.json`, con **5** casos
(mínimo pedido: 3), tomados de pedidos reales de UI de este proyecto:

1. Preparar la vista semanal C-28 (7 días, hora local, alternancia día/semana).
2. Corregir tarjetas angostas en tablet (el estado tapa hora y paciente).
3. Implementar el formulario de dar turno C-29 (mensajes del dominio, teclado).
4. Filtro por sillón en la URL, conservado al navegar los días (React Router 6).
5. Revisar accesibilidad: estado sin depender solo del color y `aria-label` completo.

Cada caso tiene `id`, `prompt`, `expected_output` y `files` (vacío), según el esquema de
`skill-creator/references/schemas.md`.

## 5. Evaluación automática: limitación (no se simula)

`skill-creator` corre los casos con `claude -p` (Claude Code) y arma el benchmark con
`scripts/aggregate_benchmark.py` y el visor `eval-viewer/generate_review.py`. **Esta sesión es
OpenCode 1.19, no Claude Code.** Los scripts que dependen de `claude -p` no se pueden ejecutar
desde acá. Por indicación del TP, **no se simularon**: se dejan los casos en `evals/evals.json`
y se anota la limitación. No se generaron `benchmark.json` ni capturas del visor.

## 6. Copia versionada y comparación de copias

Se copió la carpeta canónica a `.claude/skills/` (en Windows se usa copia porque los symlinks no
son confiables, como ya hace el repo):

```
$ cp -R .agents/skills/appointment-frontend-ux .claude/skills/appointment-frontend-ux
copiado
```

### Comparación de carpetas (`diff -r`)

```
$ diff -r .agents/skills/appointment-frontend-ux .claude/skills/appointment-frontend-ux
diff exit=0
```

`diff -r` sin diferencias (exit 0).

### Comparación archivo por archivo (`cmp`)

```
$ cmp -s .agents/skills/appointment-frontend-ux/SKILL.md            .claude/skills/appointment-frontend-ux/SKILL.md
IDENTICAL: SKILL.md
$ cmp -s .agents/skills/appointment-frontend-ux/evals/evals.json    .claude/skills/appointment-frontend-ux/evals/evals.json
IDENTICAL: evals/evals.json
```

Conclusión: las dos copias de la skill son idénticas.

## 7. Resultado

- Skill creada en la fuente canónica `.agents/skills/appointment-frontend-ux/` y espejada en
  `.claude/skills/appointment-frontend-ux/`.
- Contiene `SKILL.md` (frontmatter con `name` y `description`) y `evals/evals.json` (5 casos).
- Copias verificadas idénticas con `diff -r` y `cmp`.
- Limitación documentada: la evaluación automática con `claude -p` no se ejecuta desde OpenCode.
