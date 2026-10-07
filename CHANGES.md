# CHANGES — Secuencia de Implementación

> El change evaluado en el ciclo OPSX del TP es **C-02 `crear-turno-sin-solapamientos`**; **C-01 `fundacion-monorepo-y-dominio`** es su prerrequisito técnico.
> Índice canónico de todos los changes del MVP de **turnos-odontologia** (agenda de turnos para consultorios odontológicos de 2 a 5 profesionales).
> Cada change es chico: una sola funcionalidad, terminable en una sesión de trabajo.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
> Alcance: solo el MVP de la sección D.3 de `docs/discovery/informe-discovery.md`. Lo diferido está en la sección **Backlog (post-MVP)**, al final.
> No hay fechas por change. La entrega final es la semana posterior al 2026-10-08 (fecha a confirmar); el roadmap no se arma alrededor de ninguna fecha intermedia.

---

## Cómo usar este documento

1. **Identificá el change**: buscá el próximo `[ ]` cuyas dependencias estén todas en `[x]` (usá el árbol y los GATES).
2. **Leé la KB**: abrí cada archivo de "Leer antes" del change, en especial las reglas `RN-*` y los escenarios `US-*` que cita el Scope.
3. **Proponé**: `/opsx:propose C-NN-nombre-del-change` (el slug en kebab-case es el que figura en el título del change).
4. **Implementá y archivá**: `/opsx:apply` con Strict TDD (todo escenario de la KB tiene un test automatizado) y luego `/opsx:archive`.
5. **Marcá el checkbox**: pasá `Estado` de `[ ]` a `[x]` en este archivo. Si el change tiene nivel ALTO, frená y esperá la revisión antes de escribir código.

Convenciones: intervalos semiabiertos `[inicio, fin)`, instantes en UTC, hora local `America/Argentina/Buenos_Aires`, `now` inyectado, solo datos ficticios, el dominio es la autoridad de las reglas (DD-06, DD-07).

---

## Árbol de dependencias

```
C-01 fundacion-monorepo-y-dominio
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
 ├── C-16 api-base-y-rol-simulado
 └── C-13 db-sqlite-y-catalogos            (también requiere C-09)
      ├── C-14 persistencia-horarios-y-bloqueos   (también C-05, C-06)
      ├── C-15 persistencia-turnos-e-historial    (también C-12)
      └── C-17 api-catalogos-y-pacientes          (también C-09, C-16)
           ├── C-18 api-horarios-y-bloqueos       (también C-14, C-15)
           ├── C-19 api-dar-turno                 (también C-08, C-14, C-15)
           │    └── C-20 api-ciclo-de-vida-del-turno   (también C-11, C-12)
           └── C-21 api-consulta-de-agenda        (también C-15)

C-19 + C-20 + C-21
 └── C-22 web-base-y-rol-simulado
      ├── C-23 ui-agenda-diaria
      │    ├── C-24 ui-agenda-semanal
      │    ├── C-25 ui-dar-turno-con-errores
      │    │    └── C-26 ui-reprogramar-cancelar-y-estados
      │    └── C-27 ui-vista-de-recepcion-por-sillon
      ├── C-28 ui-horarios-y-bloqueos       (también C-18)
      └── C-29 ui-catalogos-y-pacientes     (también C-17)
```

### Paralelismo por fase

Los "agentes" son agentes de IA que el autor lanza en paralelo; el trabajo es individual y puede hacerse de forma secuencial siguiendo el mismo orden.

```
GATE 0: (inicio)
  → C-01 fundacion-monorepo-y-dominio            [Agente A]

GATE 1: C-01 ✓
  → C-02 crear-turno-sin-solapamientos           [Agente A]
  → C-16 api-base-y-rol-simulado                 [Agente B]

GATE 2: C-02 ✓                                    ← FORK (reglas de dominio independientes)
  → C-04 hora-local-y-turno-en-un-dia            [Agente A]
  → C-06 bloqueos-de-agenda                      [Agente B]
  → C-07 no-turnos-en-el-pasado                  [Agente C]
  → C-03 validar-duracion-y-referencias          [Agente B — cuando termine C-06]
  → C-10 transiciones-de-estado-del-turno        [Agente C — cuando termine C-07]
  → C-09 catalogo-y-pacientes-dominio            [Agente B — cuando termine C-03]

GATE 3: C-04 ✓
  → C-05 horario-de-atencion                     [Agente A]

GATE 4: C-03, C-05, C-06, C-07 ✓
  → C-08 mensajes-de-conflicto-en-espanol        [Agente A]

GATE 5: C-09 ✓
  → C-13 db-sqlite-y-catalogos                   [Agente B]

GATE 6: C-08 ✓ y C-10 ✓
  → C-11 reprogramar-turno                       [Agente A]
  → C-14 persistencia-horarios-y-bloqueos        [Agente B — si C-13 ✓, C-05 ✓ y C-06 ✓]
  → C-17 api-catalogos-y-pacientes               [Agente C — si C-13 ✓, C-09 ✓ y C-16 ✓]

GATE 7: C-11 ✓
  → C-12 historial-de-transiciones               [Agente A]

GATE 8: C-12 ✓ y C-13 ✓
  → C-15 persistencia-turnos-e-historial         [Agente A]

GATE 9: C-14, C-15, C-17 ✓                        ← FORK
  → C-19 api-dar-turno                           [Agente A]
  → C-18 api-horarios-y-bloqueos                 [Agente B]
  → C-21 api-consulta-de-agenda                  [Agente C]

GATE 10: C-19 ✓
  → C-20 api-ciclo-de-vida-del-turno             [Agente A]

GATE 11: C-19, C-20, C-21 ✓  (API completa; recién ahora arranca la UI)
  → C-22 web-base-y-rol-simulado                 [Agente A]

GATE 12: C-22 ✓                                   ← FORK
  → C-23 ui-agenda-diaria                        [Agente A]
  → C-28 ui-horarios-y-bloqueos                  [Agente B — si C-18 ✓]
  → C-29 ui-catalogos-y-pacientes                [Agente C — si C-17 ✓]

GATE 13: C-23 ✓                                   ← FORK
  → C-25 ui-dar-turno-con-errores                [Agente A]
  → C-24 ui-agenda-semanal                       [Agente B]
  → C-27 ui-vista-de-recepcion-por-sillon        [Agente C]

GATE 14: C-25 ✓
  → C-26 ui-reprogramar-cancelar-y-estados       [Agente A]
```

### Camino crítico (14 changes — mínimo irreducible)

```
C-01 → C-02 → C-04 → C-05 → C-08 → C-11 → C-12 → C-15 → C-19 → C-20 → C-22 → C-23 → C-25 → C-26*
```

- `C-26*` cierra el camino: con ese change se puede dar, ver, reprogramar, cancelar y marcar estados de turnos desde la UI sobre la API ya probada.
- Fuera del camino crítico (se pueden hacer en paralelo o recortar en este orden si el plazo aprieta): `C-27` (vista por sillón, diferenciador), `C-24` (vista semanal), `C-28` y `C-29` (con seeds y la API alcanza para operar; la UI de configuración es lo más postergable), `C-18` (API de horarios, los horarios pueden venir de seeds).
- **No** se recorta ningún test: la regla de contingencia de la KB es postergar vistas antes que tests (08 §Plan de contingencia).

### Plan óptimo con 3 agentes

| Paso | Agente A (Dominio — turnos) | Agente B (Dominio aux + persistencia + API aux) | Agente C (Reglas de dominio + API + UI aux) |
|------|------------------------------|--------------------------------------------------|-----------------------------------------------|
| 1 | C-01 fundacion-monorepo-y-dominio | — | — |
| 2 | C-02 crear-turno-sin-solapamientos | C-16 api-base-y-rol-simulado | — |
| 3 | C-04 hora-local-y-turno-en-un-dia | C-06 bloqueos-de-agenda | C-07 no-turnos-en-el-pasado |
| 4 | C-05 horario-de-atencion | C-03 validar-duracion-y-referencias | C-10 transiciones-de-estado-del-turno |
| 5 | C-08 mensajes-de-conflicto-en-espanol | C-09 catalogo-y-pacientes-dominio | — |
| 6 | C-11 reprogramar-turno | C-13 db-sqlite-y-catalogos | — |
| 7 | C-12 historial-de-transiciones | C-14 persistencia-horarios-y-bloqueos | C-17 api-catalogos-y-pacientes |
| 8 | C-15 persistencia-turnos-e-historial | — | — |
| 9 | C-19 api-dar-turno | C-18 api-horarios-y-bloqueos | C-21 api-consulta-de-agenda |
| 10 | C-20 api-ciclo-de-vida-del-turno | — | — |
| 11 | C-22 web-base-y-rol-simulado | — | — |
| 12 | C-23 ui-agenda-diaria | C-28 ui-horarios-y-bloqueos | C-29 ui-catalogos-y-pacientes |
| 13 | C-25 ui-dar-turno-con-errores | C-24 ui-agenda-semanal | C-27 ui-vista-de-recepcion-por-sillon |
| 14 | C-26 ui-reprogramar-cancelar-y-estados | — | — |

---

## FASE 1 — Fundación y primer change

### [C-01] `fundacion-monorepo-y-dominio`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `package.json` raíz con workspaces `packages/*` y `apps/*`; `tsconfig.base.json` (strict, target ES2022); `vitest.workspace.ts`; `.gitignore` (`.env`, `*.sqlite`, `node_modules`); `.env.example` con las variables de 08 sin secretos.
  - Paquete `packages/domain` vacío pero compilable (`src/index.ts`, `test/`), con un test de humo de Vitest que corre en verde.
  - Scripts `npm test`, `npm run typecheck` y `npm run build` a nivel raíz.
  - Regla de dependencias documentada en el README del paquete: `domain` no importa de `apps/*`, ni de Fastify, ni de SQLite, ni de React (se verifica con un test de dependencias o un chequeo de `package.json`).
  - Sin lógica de negocio, sin `apps/api`, sin `apps/web` (los crean sus propios changes).
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Estrategia de tests, §Variables de entorno
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01, §DD-05, §DD-06, §SU-10
  - `knowledge-base/02_descripcion_general.md`

### [C-02] `crear-turno-sin-solapamientos`
- **Estado**: `[ ]` pendiente
- **Scope**: es el "change 1" de la KB (DD-09). Dominio puro en `packages/domain`, sin API, sin BD, sin UI.
  - Modelos: `Appointment`, `Service` (con `default_duration_min`), tipos de `Violation` y `Result<T, Violation[]>`; estados del turno (`reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`).
  - `time/`: intervalo semiabierto `[inicio, fin)` y función de solapamiento (RN-AG, DD-07).
  - `rules/overlap`: `PROFESSIONAL_OVERLAP` (RN-AG-01) y `CHAIR_OVERLAP` (RN-AG-02) con el id del turno que choca; los estados `cancelado` y `ausente` no ocupan agenda (RN-AG-08); ambas violaciones se reportan juntas (US-003 CA-2).
  - `appointment/validateNewAppointment`: duración por defecto de la prestación o explícita (RN-AG-07); `end = start + duración`; turnos consecutivos válidos (fin == inicio); turno nuevo nace en `reservado`.
  - Parte mínima de RN-AG-09: duración <= 0 → `INVALID_DURATION` (US-007 CA-1 parcial).
  - Tests (Vitest, todo escenario es un test): US-001 CA-1 a CA-4, US-002 CA-1 a CA-6, US-003 CA-1 a CA-3, `INVALID_DURATION` con 0 y negativo; mínimo 2 casos por comportamiento.
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

> Estos changes salen de partir en cinco el "change 2" `horarios-y-bloqueos` de la KB (decisión Q-13 + regla de tamaño: un change = una funcionalidad). Todos extienden `validateNewAppointment` agregando una regla componible en `rules/`, por lo que, salvo C-05 (que usa C-04), son independientes entre sí.

### [C-03] `validar-duracion-y-referencias`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `rules/duration`: duración múltiplo de 5 y máximo 480 min → `INVALID_DURATION` (RN-AG-09 completa, RN-DI-05; el caso <= 0 ya está en C-02).
  - `rules/references`: profesional, sillón o prestación inexistentes → `UNKNOWN_REFERENCE`; inactivos → `INACTIVE_REFERENCE`; paciente inexistente (RN-AG-11).
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
  - `time/`: conversión instante UTC a día y minutos desde las 00:00 en `America/Argentina/Buenos_Aires` (usando `Intl`, sin dependencias de framework); formateo de hora local para los mensajes.
  - `rules/same-day`: turno que cruza la medianoche local → rechazo (RN-AG-10, US-007 CA-3).
  - Tests: un instante UTC que local cae en otro día; turno 23:30–00:30 rechazado; 23:00–23:55 válido.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-10, §RN-GL-03
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01, §SU-09, §DD-07
  - `knowledge-base/06_funcionalidades.md` §US-007 (CA-3)

### [C-05] `horario-de-atencion`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Modelo `WorkingHours` (profesional, día de la semana, tramo `[inicio, fin)` en minutos locales) y validación de un conjunto de tramos: sin solapamiento ni `inicio >= fin` (RN-DI-01, RN-DI-02; US-010 CA-1 y CA-2).
  - `rules/working-hours`: el turno debe caer completo dentro de un tramo → `OUTSIDE_WORKING_HOURS` (RN-AG-04).
  - Tests: US-004 CA-1, CA-2, CA-3, CA-6, CA-7 (instante UTC que local queda fuera); varios tramos por día; día sin tramos.
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
  - `rules/blocks`: turno que se superpone con un bloqueo → `BLOCKED_TIME` con el id del bloqueo; justo antes o justo después es válido (RN-AG-05; US-004 CA-4 y CA-5).
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
  - Reloj inyectado `now` en el contexto del dominio (ninguna regla llama a `Date.now()`; RN-GL-04, US-005 CA-4).
  - `rules/past`: inicio < `now` → `IN_THE_PAST`; inicio == `now` y > `now` válidos (RN-AG-06; US-005 CA-1 a CA-3).
  - Tests: los tres casos de borde con relojes fijos; un test que verifica que el módulo no referencia el reloj del sistema.
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-06, §RN-GL-04
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Inyección de reloj)

### [C-08] `mensajes-de-conflicto-en-espanol`
- **Estado**: `[ ]` pendiente
- **Scope**: diferenciador del MVP (D.3).
  - `violations.ts`: todas las violaciones llevan `code`, `message` en español, `conflictingAppointmentId` / `conflictingBlockId` y el intervalo que choca (US-006 CA-1).
  - El mensaje incluye el nombre del profesional o sillón y el rango en hora local (US-006 CA-3), usando `time/` de C-04.
  - `validateNewAppointment` compone todas las reglas (C-02, C-03, C-04, C-05, C-06, C-07) y devuelve **todas** las violaciones en el orden de RN-AG-12: referencias, duración, medianoche, pasado, horario, bloqueos, profesional, sillón (US-006 CA-2).
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
  - `appointment/transitions.ts`: tabla tabular de RN-TU-02 en un solo lugar; terminales `atendido`, `ausente`, `cancelado`.
  - `cancelAppointment` (US-030 CA-1 y CA-2: libera profesional y sillón; desde estado terminal → `INVALID_TRANSITION`) y `changeStatus` a confirmado, atendido o ausente (US-032).
  - Reglas de tiempo: `atendido` y `ausente` solo con `now >= inicio` (RN-TU-05, `now` inyectado); sin anticipación mínima para cancelar (RN-TU-04).
  - Propiedad: el odontólogo solo modifica turnos propios; recepción y administrador, todos (RN-AC-01, US-032 CA-3; el actor entra como parámetro).
  - Tests exhaustivos de la tabla de transiciones (todas las combinaciones origen/destino) y de los casos de actor.
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
  - `appointment/reschedule`: cambiar inicio, profesional, sillón y/o duración; revalida **todas** las reglas de `validateNewAppointment` excluyendo al propio turno (RN-TU-03, US-031 CA-1).
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
  - Modelo `AppointmentStatusChange` con `from_status` (nulo al crear), `to_status`, `changed_by`, `changed_at` (+ detalle de reprogramación); inmutable: sin operación de edición ni borrado en el dominio (RN-TU-06, US-033 CA-2).
  - `validateNewAppointment`, `cancelAppointment`, `changeStatus` y `reschedule` devuelven, además del turno, la entrada de historial correspondiente (RN-TU-01, US-030 CA-3, US-031 CA-5, US-033 CA-1).
  - Tests: una entrada por cada tipo de transición, `from` nulo al crear, intento de mutar una entrada rechazado, `changed_by` y `changed_at` (reloj inyectado) presentes.
- **Dependencias**: `C-10, C-11`
- **Governance**: ALTO (trazabilidad inmutable; no es un registro de auditoría de seguridad sino el historial funcional del turno con datos ficticios, por eso no se sube a CRITICO. Describir el diseño y esperar revisión antes de escribir código)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-033, §US-030 (CA-3), §US-031 (CA-5)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-01, §RN-TU-06
  - `knowledge-base/04_modelo_de_datos.md` §AppointmentStatusChange
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-03

---

## FASE 4 — Persistencia SQLite

> Corre en paralelo con la FASE 3 a partir de que existan los catálogos de dominio (C-09).

### [C-13] `db-sqlite-y-catalogos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `apps/api` (workspace) con conexión `better-sqlite3` leyendo `DATABASE_PATH`, ejecutor de migraciones `db/migrations/*.sql` y soporte de `:memory:` para tests.
  - Migración 001: tablas `professional`, `chair`, `service`, `patient` (ids UUID `TEXT`, instantes `INTEGER` epoch ms UTC, DNI único).
  - Repositorios de catálogos y pacientes con sentencias preparadas (nunca concatenación).
  - `db/seed.ts` con datos 100% ficticios (profesionales, sillones, prestaciones, pacientes).
  - Tests de integración con SQLite `:memory:`: alta, desactivación, unicidad, lectura.
- **Dependencias**: `C-01, C-09`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (convenciones, §Professional, §Chair, §Service, §Patient, §Seed data inicial)
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Seguridad
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03

### [C-14] `persistencia-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Migración 002: tablas `working_hours` (minutos locales desde las 00:00) y `block`.
  - Repositorios de horarios y bloqueos; el guardado pasa por la validación de dominio de C-05 y C-06 (tramos válidos, `inicio < fin`).
  - Consulta de turnos afectados al crear un bloqueo (se completa con C-15; acá se expone la interfaz y se prueba con datos de prueba).
  - Tests de integración: ida y vuelta de tramos y bloqueos, rechazo de tramos solapados, eliminar un bloqueo libera el horario (US-011 CA-4).
- **Dependencias**: `C-13, C-05, C-06`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §WorkingHours, §Block
  - `knowledge-base/05_reglas_de_negocio.md` §RN-DI-01 a RN-DI-04
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011

### [C-15] `persistencia-turnos-e-historial`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Migración 003: tablas `appointment` y `appointment_status_change` (historial solo de inserción).
  - Repositorio de turnos: carga de contexto (turnos activos del profesional y del sillón en el rango), inserción, actualización de estado y reprogramación; historial en la misma transacción (RN-GL-02).
  - Transacción `BEGIN IMMEDIATE` para altas y reprogramaciones, de modo que dos escrituras concurrentes no burlen la validación.
  - Tests de integración: turno + historial atómicos (si falla uno, no queda ninguno), escritura concurrente que intenta solapar, el historial no se puede actualizar ni borrar a nivel repositorio.
- **Dependencias**: `C-12, C-13`
- **Governance**: ALTO (integridad de datos y transacciones; confirmar el diseño de transacción antes de implementar)
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Appointment, §AppointmentStatusChange
  - `knowledge-base/05_reglas_de_negocio.md` §RN-GL-01, §RN-GL-02, §RN-TU-06
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Repositorio, Transacción `BEGIN IMMEDIATE`)

---

## FASE 5 — API REST (Fastify)

### [C-16] `api-base-y-rol-simulado`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `apps/api/src/server.ts` (Fastify), `config.ts` (lee `PORT`, `NODE_ENV`, `APP_TIMEZONE`, `CORS_ORIGIN`, `ALLOW_DEV_ROLE_HEADER`), CORS solo para `CORS_ORIGIN`, ruta de salud, manejo de errores uniforme (400/401/403/409/422), validación de entrada con Zod en el borde.
  - `preHandler` de RBAC con rol simulado por cabeceras `X-Role` / `X-User-Id`, activo solo con `NODE_ENV != production`; matriz de 03 como tabla de permisos por recurso y acción; sin rol → `401`, rol sin permiso → `403` (US-050 CA-1 y CA-2).
  - Tests con `fastify.inject`: cada rol contra rutas de prueba de la matriz; cabecera ausente; producción deshabilita el header.
  - Autenticación real queda en el Backlog (CRITICO).
- **Dependencias**: `C-01`
- **Governance**: ALTO (roles y acceso; sin credenciales reales en el MVP, pero la matriz RBAC se revisa antes de implementar)
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC, §Autenticación en el MVP
  - `knowledge-base/06_funcionalidades.md` §US-050
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AC-01, §RN-AC-02
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad, §Variables de entorno
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-02, §SU-06

### [C-17] `api-catalogos-y-pacientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoints `/api/professionals`, `/api/chairs`, `/api/services`, `/api/patients` (alta, edición, desactivación, listado) respetando la matriz RBAC (administrador CRUD, recepción alta/edición de pacientes, odontólogo lectura).
  - Casos de uso en `usecases/` que llaman al dominio (C-09) y a los repositorios (C-13); validación Zod en el borde.
  - Tests de integración (`fastify.inject` + SQLite `:memory:`): 201/200, 400 por validación, 403 por rol, 409 por nombre o DNI duplicado.
- **Dependencias**: `C-09, C-13, C-16`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021, §US-022
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados (Caso de uso)

### [C-18] `api-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Endpoints de horario de atención por profesional (alta, edición, lectura) y de bloqueos (crear, listar, eliminar), con RBAC: odontólogo CRUD sobre lo propio, recepción lectura, administrador CRUD (RN-AC-01).
  - Crear un bloqueo o cambiar un horario que pisa turnos existentes se guarda y responde la lista de turnos afectados sin cancelarlos (US-010 CA-3, US-011 CA-3).
  - Tests de integración: 403 si el odontólogo toca horarios de otro, bloqueo con turnos afectados, tramos solapados → 422.
- **Dependencias**: `C-14, C-15, C-17`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §RN-DI-04, §RN-AC-01

### [C-19] `api-dar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `POST /api/appointments`: caso de uso que abre la transacción `BEGIN IMMEDIATE`, carga el contexto (turnos, horarios, bloqueos, referencias), llama a `validateNewAppointment` y persiste turno + historial; el reloj es `now` real inyectado en el borde.
  - Rechazo de dominio → `409`/`422` con la lista completa de violaciones (código + mensaje en español) tal como las devuelve el dominio.
  - RBAC: recepción y administrador crean; odontólogo `403`.
  - Tests de integración: turno válido (201 + entrada de historial), choque de profesional, choque de sillón, ambas violaciones juntas, fuera de horario, en bloqueo, en el pasado, y carrera de dos altas simultáneas sobre el mismo hueco.
- **Dependencias**: `C-08, C-14, C-15, C-17`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/05_reglas_de_negocio.md` §RN-GL-01, §RN-GL-02, §RN-AG-12
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados, §Estrategia de tests
  - `knowledge-base/06_funcionalidades.md` §US-001, §US-006

### [C-20] `api-ciclo-de-vida-del-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `POST /api/appointments/:id/cancel`, `POST /api/appointments/:id/reschedule`, `POST /api/appointments/:id/status` (confirmado, atendido, ausente) y `GET /api/appointments/:id/history`.
  - Transaccional con historial (turno + entrada en una sola transacción); `INVALID_TRANSITION` → `409`; odontólogo solo sobre sus turnos y con historial propio de solo lectura (RN-AC-01).
  - El historial se expone solo en lectura: no hay endpoints de edición ni borrado.
  - Tests de integración: cada transición válida e inválida, reprogramar con choque, reprogramar al pasado, `403` por rol y por propiedad, historial ordenado con `from`, `to`, `changed_by`, `changed_at`.
- **Dependencias**: `C-11, C-12, C-19`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-031, §US-032, §US-033
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-02, §RN-TU-03, §RN-TU-06
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-21] `api-consulta-de-agenda`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /api/agenda?from&to&professionalId&chairId`: turnos del rango (día o semana, en hora local `APP_TIMEZONE`) filtrables por profesional y por sillón; incluye horarios de atención y bloqueos del rango para que la UI los dibuje.
  - RBAC: odontólogo ve su agenda (y el resto en solo lectura según 03), recepción y administrador ven todo.
  - Tests de integración: filtros combinados, rango que cruza semanas, turnos cancelados incluidos con su estado, borde de medianoche local.
- **Dependencias**: `C-15, C-17`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 5
  - `knowledge-base/06_funcionalidades.md` §US-040, §US-041
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01

---

## FASE 6 — Interfaz web (React + Vite), al final y sobre la API probada

> La UI recién arranca con la API completa (GATE 11). Lineamientos comunes de 08 §Frontend cuidado: tokens de diseño mínimos, estados de carga/vacío/error en toda vista, mensajes del dominio mostrados tal cual, accesibilidad básica y responsive para escritorio y tablet. Tests con Vitest + Testing Library.

### [C-22] `web-base-y-rol-simulado`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `apps/web` (Vite + React + TypeScript), `main.tsx`, router mínimo, `shared/` con tokens de diseño (color, espaciado, tipografía) y colores por estado del turno.
  - Cliente de API tipado con `VITE_API_URL` que envía `X-Role` / `X-User-Id`; selector de rol simulado en la barra superior (US-050).
  - Componentes base de carga, vacío y error; estructura `features/` y `pages/`.
  - Tests de componentes: el selector de rol cambia las cabeceras, el estado de error muestra el mensaje recibido.
- **Dependencias**: `C-19, C-20, C-21`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado, §Estructura de directorios
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04, §SU-06
  - `knowledge-base/06_funcionalidades.md` §US-050
  - `knowledge-base/03_actores_y_roles.md` §Autenticación en el MVP

### [C-23] `ui-agenda-diaria`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Vista diaria con una columna por profesional, turnos coloreados por estado, horarios de atención y bloqueos visibles; filtros por profesional y por sillón (US-040 CA-1, CA-3, CA-4).
  - Navegación de día anterior/siguiente; consume `GET /api/agenda`.
  - Tests de componentes: columnas por profesional, color por estado, filtro por sillón, estado vacío.
- **Dependencias**: `C-22`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado
  - `knowledge-base/07_flujos_principales.md` §Flujo 5

### [C-24] `ui-agenda-semanal`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Vista semanal por profesional (selector de profesional) con turnos por día; alternar día/semana desde la agenda (US-040 CA-2).
  - Tests de componentes: 7 días, turnos en el día correcto en hora local, filtro por profesional.
- **Dependencias**: `C-23`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040 (CA-2)
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado, §Plan de contingencia de plazo

### [C-25] `ui-dar-turno-con-errores`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Formulario de turno: paciente, profesional, sillón, prestación, inicio, duración (sugiere la duración por defecto de la prestación; US-042 CA-2). Navegable por teclado, foco visible.
  - Muestra las violaciones del dominio tal cual (código + mensaje en español, con el turno o bloqueo que choca; US-042 CA-1); no repite las reglas en el cliente.
  - Visible solo para recepción y administrador (el odontólogo no da turnos).
  - Tests de componentes: duración sugerida, múltiples violaciones renderizadas, éxito refresca la agenda.
- **Dependencias**: `C-23`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-042, §US-006
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-26] `ui-reprogramar-cancelar-y-estados`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Acciones sobre un turno: reprogramar (reutiliza el formulario de C-25 con los errores del dominio), cancelar y cambiar estado (confirmado, atendido, ausente) solo con las transiciones válidas habilitadas.
  - Panel de historial del turno (`from`, `to`, quién, cuándo) en solo lectura.
  - Tests de componentes: botones según estado y rol, error de transición inválida mostrado, historial ordenado.
- **Dependencias**: `C-25`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-031, §US-032, §US-033, §US-042
  - `knowledge-base/07_flujos_principales.md` §Flujo 2, §Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TU-02

### [C-27] `ui-vista-de-recepcion-por-sillon`
- **Estado**: `[ ]` pendiente
- **Scope**: diferenciador del MVP (D.3).
  - Vista de recepción con una columna por sillón con los turnos de todos los profesionales; los huecos libres son visibles (US-041 CA-1 y CA-2).
  - Tests de componentes: turnos de distintos profesionales en la misma columna, hueco libre entre dos turnos.
- **Dependencias**: `C-23`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-041
  - `knowledge-base/08_arquitectura_propuesta.md` §Frontend cuidado (referencias DentalBox y Open Dental)
  - `knowledge-base/01_vision_y_objetivos.md`

### [C-28] `ui-horarios-y-bloqueos`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Pantalla para que el odontólogo (y el administrador) cargue sus tramos por día de la semana y sus bloqueos; recepción solo lectura.
  - Al guardar un bloqueo o un horario que pisa turnos, muestra la lista de turnos afectados (US-010 CA-3, US-011 CA-3).
  - Tests de componentes: alta de tramos, error por tramos solapados, aviso de turnos afectados, eliminar bloqueo.
- **Dependencias**: `C-22, C-18`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010, §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-29] `ui-catalogos-y-pacientes`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - Pantallas del administrador para profesionales, sillones y prestaciones (con duración) y de recepción/administrador para pacientes (nombre, DNI, teléfono, obra social como texto); sin campos clínicos.
  - Tests de componentes: validaciones mostradas, DNI duplicado, desactivar.
- **Dependencias**: `C-22, C-17`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021, §US-022
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PA-01, §RN-PA-02

---

## Backlog (post-MVP)

Fuera del alcance del MVP (D.3 y KB 06 §Épica 7). **No tienen C-NN y no se implementan** hasta que se decida abrir una nueva etapa; el diseño actual deja el hueco para varios de ellos (reglas componibles, `Appointment` sin acoplarse a un canal).

| Ítem | Nota |
|------|------|
| Confirmación y recordatorio por enlace de WhatsApp (texto precargado, sin API) | Luego, API oficial de WhatsApp |
| Reserva online del paciente con aprobación del consultorio | Requiere usuario paciente |
| Lista de espera para cubrir cancelaciones | |
| Sobreturnos controlados (con alerta, marca y autorización) | Hoy prohibidos (RN-AG-03); la regla es componible para habilitarlos |
| Regla de no solapamiento del mismo paciente (RN-PA-03) | Se agrega como una regla más en `rules/` |
| Búsqueda del primer hueco disponible (profesional + sillón + duración) | |
| Señas y cobros con Mercado Pago | |
| Facturación ARCA | |
| Obras sociales (validación de cobertura) | Hoy es solo texto en el paciente |
| Ficha clínica y odontograma | Prohibida información clínica en el MVP (RN-PA-01) |
| Multisede | |
| Reportes (p. ej. ausentismo) y exportación de datos | |
| Autenticación real y gestión de usuarios y roles | Gobernanza CRITICO: requiere aprobación humana explícita antes de escribir código |

---

## Resumen

| ID | Change | Fase | Depende de | Governance |
|----|--------|------|------------|------------|
| C-01 | `fundacion-monorepo-y-dominio` | 1 | — | BAJO |
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
| C-13 | `db-sqlite-y-catalogos` | 4 | C-01, C-09 | MEDIO |
| C-14 | `persistencia-horarios-y-bloqueos` | 4 | C-13, C-05, C-06 | MEDIO |
| C-15 | `persistencia-turnos-e-historial` | 4 | C-12, C-13 | ALTO |
| C-16 | `api-base-y-rol-simulado` | 5 | C-01 | ALTO |
| C-17 | `api-catalogos-y-pacientes` | 5 | C-09, C-13, C-16 | BAJO |
| C-18 | `api-horarios-y-bloqueos` | 5 | C-14, C-15, C-17 | MEDIO |
| C-19 | `api-dar-turno` | 5 | C-08, C-14, C-15, C-17 | MEDIO |
| C-20 | `api-ciclo-de-vida-del-turno` | 5 | C-11, C-12, C-19 | MEDIO |
| C-21 | `api-consulta-de-agenda` | 5 | C-15, C-17 | BAJO |
| C-22 | `web-base-y-rol-simulado` | 6 | C-19, C-20, C-21 | BAJO |
| C-23 | `ui-agenda-diaria` | 6 | C-22 | BAJO |
| C-24 | `ui-agenda-semanal` | 6 | C-23 | BAJO |
| C-25 | `ui-dar-turno-con-errores` | 6 | C-23 | MEDIO |
| C-26 | `ui-reprogramar-cancelar-y-estados` | 6 | C-25 | MEDIO |
| C-27 | `ui-vista-de-recepcion-por-sillon` | 6 | C-23 | BAJO |
| C-28 | `ui-horarios-y-bloqueos` | 6 | C-22, C-18 | BAJO |
| C-29 | `ui-catalogos-y-pacientes` | 6 | C-22, C-17 | BAJO |

**Totales**: 29 changes en 6 fases, 15 gates (GATE 0 a GATE 14), camino crítico de 14 changes.

**Primer change recomendado**: `C-01` (`fundacion-monorepo-y-dominio`), y enseguida `C-02` (`crear-turno-sin-solapamientos`, el "change 1" de la KB).

Para arrancar: `/opsx:propose C-01-fundacion-monorepo-y-dominio`
