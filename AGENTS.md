# turnos-odontologia — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

Sistema web de agenda de turnos para consultorios odontológicos de Argentina con 2 a 5 profesionales y varios sillones. Su diferencial: rechazar, desde un dominio TypeScript puro y con mensajes explicativos, todo turno que se solape por profesional o por sillón, caiga fuera de horario o bloqueos, o esté en el pasado. Trabajo individual; avance el 2026-10-08 (solo Discovery, ya hecho) y entrega final el jueves 2026-10-15.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima | Notas |
|------|------------|----------------|-------|
| Lenguaje | TypeScript (modo `strict`) | 5.x | En todos los paquetes |
| Runtime | Node.js LTS | 20 | **Suposición:** 20 o superior |
| Dominio | TypeScript puro, sin dependencias de framework | — | Sin I/O, sin reloj global: `now` se inyecta |
| Tests | Vitest | 1.x | Strict TDD: cada escenario del spec tiene test automatizado |
| Backend | Node.js + **Fastify** (API REST) | 4.x | Elegido sobre Express (DD-02) |
| Persistencia | **SQLite** vía `better-sqlite3` | — | Archivo local; migraciones SQL versionadas (DD-03) |
| Validación de borde | Zod | 3.x | Solo en la API; el dominio valida sus propias reglas |
| Frontend | **React + Vite** (SPA) | React 18 / Vite 5 | "Frontend cuidado" (DD-04) |
| Gestión de paquetes | npm workspaces | — | `packages/domain`, `apps/api`, `apps/web` |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [README.md](knowledge-base/README.md) | Resumen ejecutivo e índice de la KB |
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito, alcance y métricas de éxito |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura, API REST, zona horaria |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Roles y permisos (rol simulado, sin auth real en el MVP) |
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
| **Dominio** | `packages/domain`: reglas de agenda en TS puro, Strict TDD | `tdd`, `vitest` |
| **Backend API** | `apps/api`: Fastify, Zod, repositorios SQLite | `tdd`, `vitest` (las skills de Fastify/Node se evalúan al llegar a C-16) |
| **Frontend** | `apps/web`: React + Vite | `vitest` (las skills de React/diseño se evalúan al llegar a C-22) |
| **Orquestación** | OPSX + fundación del proyecto | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `discovery-research`, `web-scraper`, `find-skill`, `skill-creator` |

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; versionado está en el repo).

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 29 changes en 6 fases (fundación → dominio: validaciones → dominio: ciclo de vida → persistencia SQLite → API REST → interfaz web), 15 gates.
- **Camino crítico** (14): `C-01 → C-02 → C-04 → C-05 → C-08 → C-11 → C-12 → C-15 → C-19 → C-20 → C-22 → C-23 → C-25 → C-26`.
- **Primer change**: `C-01` (`fundacion-monorepo-y-dominio`), prerrequisito técnico de **`C-02` (`crear-turno-sin-solapamientos`)**, el change evaluado en el ciclo OPSX del TP.
- **Recortables si aprieta el plazo** (en este orden): C-27, C-24, C-28, C-29, C-18. Los tests no se recortan.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** + las universales que el global no cubre.

Son contrato; romperlas es un defecto.

### Dominio

- **NUNCA** importar Fastify, SQLite, React ni ningún I/O en `packages/domain`, ni llamar `Date.now()` / `new Date()` sin argumentos → inyectar `now` y recibir el contexto (profesional, sillón, prestación, horarios, bloqueos, turnos relevantes) como parámetro.
- **NUNCA** duplicar una regla RN-AG / RN-TU en la API o en la UI → la UI puede anticipar errores, pero el rechazo definitivo es del dominio.
- **NUNCA** guardar horas locales → los instantes se guardan en UTC (epoch ms); el horario laboral se evalúa en `America/Argentina/Buenos_Aires`.
- **NUNCA** lanzar excepciones genéricas por una regla de negocio → devolver un resultado tipado (`ok` o lista de violaciones) con código estable y mensaje en español que identifique el turno o bloqueo en conflicto. En la API: `409` conflicto de agenda, `422` regla de validez, `400` entrada malformada.
- **NUNCA** aceptar un turno que se solapa con otro del mismo profesional o del mismo sillón → el sistema rechaza, no avisa y deja pasar. Los turnos cancelados o ausentes no ocupan agenda. (Regla agregada a mano por la autora, a partir del Discovery.)

### TypeScript y tests

- **NUNCA** usar `any` ni desactivar `strict` → `unknown` + narrowing; `tsconfig` estricto en todos los paquetes.
- **NUNCA** mockear colaboradores internos en los tests de dominio → datos literales tomados del spec; el tiempo se fija con el `now` inyectado.

### Datos y código

- **NUNCA** usar datos reales de pacientes (nombres, DNI, teléfonos) en seeds, tests ni ejemplos → solo datos ficticios.
- **NUNCA** commitear claves, tokens ni archivos `.env` → `.env` en `.gitignore`; `.env.example` sin valores.
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
