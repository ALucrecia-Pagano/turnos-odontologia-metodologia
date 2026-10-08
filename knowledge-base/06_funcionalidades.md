# Funcionalidades

Organizadas por épica e historia de usuario (US-NNN). Cada criterio de aceptación (CA) es un **escenario con test automatizado** (pytest en el dominio y la API). El change C-02 `crear-turno-sin-solapamientos` cubre únicamente la regla "crear un turno sin solapamientos por profesional y por sillón" (US-001 acotada, US-002, US-003 y el criterio mínimo de duración positiva de US-007; dominio puro; C-01 es su prerrequisito técnico). El resto de la Épica 1 (US-004, US-005, US-006 y el resto de US-007) pasa a C-03 a C-08: ver las marcas **Change** en cada historia.

## Orden de changes

| Change | Slug | Historias | Capa |
|---|---------------------------|--------|------|
| C-01 | `fundacion-backend-y-dominio` | — (prerrequisito técnico) | `backend/` con pytest y paquete de dominio Python vacío (`backend/app/domain`) |
| C-02 | `crear-turno-sin-solapamientos` | 1 (solo US-001, US-002, US-003 y US-007 CA-1 parcial: duración positiva) | Dominio puro en Python (`backend/app/domain`, pytest) |
| C-03 a C-08 | `validar-duracion-y-referencias`, `hora-local-y-turno-en-un-dia`, `horario-de-atencion`, `bloqueos-de-agenda`, `no-turnos-en-el-pasado`, `mensajes-de-conflicto-en-espanol` | 1 (US-004, US-005, US-006, resto de US-007) y 2 | Dominio |
| C-09 | `catalogo-y-pacientes-dominio` | 3 | Dominio |
| C-10 a C-12 | `transiciones-de-estado-del-turno`, `reprogramar-turno`, `historial-de-transiciones` | 4 | Dominio |
| C-13 a C-14 | `docker-compose-y-postgres`, `migraciones-alembic` | — (infraestructura) | Docker Compose (PostgreSQL + Redis sin uso) y Alembic |
| C-15 a C-17 | `persistencia-catalogos-y-pacientes`, `persistencia-horarios-y-bloqueos`, `persistencia-turnos-e-historial` | 1–5 | Persistencia PostgreSQL + SQLAlchemy |
| C-18 a C-24 | `api-base-fastapi`, `autenticacion-jwt-y-roles` (6) a `api-consulta-de-agenda` | 1–6 | API REST FastAPI (C-19: autenticación JWT) |
| C-25 a C-33 | `frontend-base-react-vite`, `ui-login-y-sesion` (6) a `ui-catalogos-y-pacientes` | 5, 6 | React + TypeScript + Vite (C-26: login) |

**Decisión de la autora (Q-13, 2026-10-07):** US-005 (no dar turnos en el pasado), US-006 (mensajes de conflicto completos) y el resto de US-007 (granularidad, referencias, medianoche) van a C-03 a C-08, porque "no en el pasado" y los mensajes en hora local necesitan la zona horaria, que vive en C-04. De C-02 solo entra el criterio de duración positiva de US-007. No se renumera ninguna historia.

La fuente de verdad del orden, las dependencias y el detalle de cada change es `CHANGES.md`; esta tabla es solo un resumen.

## Épica 1: Creación de turnos sin conflictos

C-02 es **solo** la regla de no solapamiento por profesional y por sillón, con la duración del turno (por prestación), el rechazo de duración no positiva y el caso borde de turnos consecutivos (intervalos semiabiertos). Horario de atención, bloqueos y el resto de las validaciones del turno pasan a C-03 a C-08.

### US-001 — Dar un turno válido
**Change:** C-02 (`crear-turno-sin-solapamientos`), acotada a solapamientos, duración (positiva) y turnos consecutivos.

**Como** secretaria
**Quiero** dar un turno eligiendo paciente, profesional, sillón y prestación
**Para** que quede registrado solo si es válido

**Criterios de aceptación**:
- [ ] CA-1: con profesional libre y sillón libre, el dominio devuelve `ok` con el turno en estado `reservado`. (Las condiciones de horario, bloqueos y pasado se agregan en los changes posteriores.)
- [ ] CA-2: la duración por defecto es la de la prestación; si se informa duración explícita, se usa esa.
- [ ] CA-3: `end = start + duración`; el intervalo es semiabierto.
- [ ] CA-4: dos turnos consecutivos (uno termina cuando empieza el otro) del mismo profesional y sillón **son válidos**.

**Reglas relacionadas**: RN-AG-07, RN-TU-01 (la validez de la duración, RN-AG-09, entra solo en su parte mínima: ver US-007; RN-AG-10 va a C-04)

### US-002 — Rechazar solapamiento de profesional
**Change:** C-02.

**Como** secretaria
**Quiero** que el sistema rechace un turno que pisa otro del mismo profesional
**Para** no generar conflictos de agenda

- [ ] CA-1: inicio dentro de un turno existente → `PROFESSIONAL_OVERLAP` con el id del turno que choca.
- [ ] CA-2: fin dentro de un turno existente → rechazo.
- [ ] CA-3: nuevo turno que contiene por completo a uno existente → rechazo.
- [ ] CA-4: mismo intervalo exacto → rechazo.
- [ ] CA-5: turno existente `cancelado` o `ausente` **no** genera conflicto.
- [ ] CA-6: otro profesional a la misma hora y distinto sillón → válido.

**Reglas**: RN-AG-01, RN-AG-03, RN-AG-08, RN-AG-12

### US-003 — Rechazar solapamiento de sillón
**Change:** C-02.

**Como** secretaria
**Quiero** que el sistema rechace un turno que usa un sillón ya ocupado
**Para** no asignar dos pacientes al mismo sillón

- [ ] CA-1: mismo sillón, intervalo solapado, **otro** profesional → `CHAIR_OVERLAP` con el id del turno que choca.
- [ ] CA-2: mismo profesional y mismo sillón solapados → se reportan **ambas** violaciones (profesional y sillón).
- [ ] CA-3: distinto sillón a la misma hora → válido.

**Reglas**: RN-AG-02, RN-AG-12

### US-004 — Respetar horario de atención y bloqueos
**Change:** C-05 (`horario-de-atencion`: CA-1 a CA-3, CA-6, CA-7) y C-06 (`bloqueos-de-agenda`: CA-4, CA-5); sale de C-02.

**Como** odontólogo
**Quiero** que no me asignen turnos fuera de mi horario ni en mis bloqueos
**Para** no recibir pacientes cuando no atiendo

- [ ] CA-1: turno completo dentro de un tramo laboral → válido.
- [ ] CA-2: turno que empieza dentro pero termina después del fin del tramo → `OUTSIDE_WORKING_HOURS`.
- [ ] CA-3: turno en un día sin tramos (p. ej. domingo) → `OUTSIDE_WORKING_HOURS`.
- [ ] CA-4: turno que se superpone con un bloqueo → `BLOCKED_TIME` con el id del bloqueo.
- [ ] CA-5: turno justo antes o justo después de un bloqueo (sin solapar) → válido.
- [ ] CA-6: turno que cae entre dos tramos (p. ej. 13:00–15:00 con tramos 9–13 y 15–19) → rechazo.
- [ ] CA-7: la evaluación usa hora local `America/Argentina/Buenos_Aires` (un instante UTC que local cae fuera de horario se rechaza).

**Reglas**: RN-AG-04, RN-AG-05, RN-DI-01, RN-GL-03

### US-005 — No dar turnos en el pasado
**Change:** C-07 (`no-turnos-en-el-pasado`); necesita el reloj inyectado y la zona horaria de C-04 (Q-13).

**Como** secretaria
**Quiero** que el sistema rechace turnos con fecha/hora pasada
**Para** evitar errores de carga

- [ ] CA-1: inicio < `now` → `IN_THE_PAST`.
- [ ] CA-2: inicio == `now` → válido.
- [ ] CA-3: inicio > `now` → válido.
- [ ] CA-4: el reloj se inyecta; el dominio no llama a `datetime.now()`.

**Reglas**: RN-AG-06, RN-GL-04

### US-006 — Mensajes de conflicto claros
**Change:** C-08 (`mensajes-de-conflicto-en-espanol`); los mensajes en hora local necesitan la zona horaria de C-04 (Q-13). C-02 igual devuelve `code` y el id del turno que choca (US-002 CA-1, US-003 CA-1) y todas las violaciones de solapamiento (US-003 CA-2); el texto en español con nombres y rango horario local queda para este change.

**Como** secretaria
**Quiero** saber qué turno o bloqueo causa el rechazo
**Para** resolverlo rápido (diferenciador del MVP)

- [ ] CA-1: cada violación trae `code`, `message` en español y, si aplica, `conflictingAppointmentId` / `conflictingBlockId` con el intervalo que choca.
- [ ] CA-2: si hay varias violaciones, se devuelven todas en el orden de RN-AG-12.
- [ ] CA-3: el mensaje incluye el nombre del profesional/sillón y el rango horario en hora local.

**Reglas**: RN-AG-12

### US-007 — Validar referencias y duración
**Change:** dividida (Q-13). CA-1 **parcial** (duración 0 o negativa → `INVALID_DURATION`) en C-02: un intervalo con `fin <= inicio` rompe la lógica de solapamiento semiabierto. El resto de CA-1 (múltiplo de 5, máximo 480) y CA-2 en C-03 (`validar-duracion-y-referencias`); CA-3 en C-04 (`hora-local-y-turno-en-un-dia`).

**Como** sistema
**Quiero** rechazar entradas inválidas
**Para** proteger la integridad

- [ ] CA-1: duración 0, negativa, no múltiplo de 5 o > 480 → `INVALID_DURATION`.
- [ ] CA-2: profesional, sillón o prestación inactivos o inexistentes → `INACTIVE_REFERENCE` / `UNKNOWN_REFERENCE`.
- [ ] CA-3: turno que cruza la medianoche → rechazo.

**Reglas**: RN-AG-09, RN-AG-10, RN-AG-11

## Épica 2: Horarios y bloqueos

### US-010 — Cargar horario de atención
**Como** odontólogo / administrador, **quiero** definir mis tramos por día de la semana, **para** que solo se den turnos cuando atiendo.
- [ ] CA-1: varios tramos por día permitidos. CA-2: tramos solapados o `inicio >= fin` se rechazan. CA-3: cambiar horario no altera turnos ya dados (se informa cuáles quedan fuera).

**Reglas**: RN-DI-01, RN-DI-02

### US-011 — Gestionar bloqueos
**Como** odontólogo, **quiero** cargar bloqueos (vacaciones, feriados, ausencias), **para** que no me asignen turnos en esos períodos.
- [ ] CA-1: bloqueo válido se guarda. CA-2: `inicio >= fin` se rechaza. CA-3: bloqueo que pisa turnos existentes se guarda y **no** cancela esos turnos; la respuesta lista los turnos afectados. CA-4: eliminar un bloqueo libera el horario.

**Reglas**: RN-DI-03, RN-DI-04

## Épica 3: Catálogo de prestaciones y configuración

### US-020 — Administrar prestaciones con duración
**Como** administrador, **quiero** crear y editar prestaciones con duración por defecto, **para** que cada turno ocupe el tiempo correcto.
- [ ] CA-1: duración válida (RN-AG-09). CA-2: nombre único. CA-3: desactivar una prestación no afecta turnos existentes.

### US-021 — Administrar profesionales y sillones
**Como** administrador, **quiero** dar de alta y desactivar profesionales y sillones, **para** reflejar la realidad del consultorio.
- [ ] CA-1: alta con nombre válido. CA-2: desactivar impide nuevos turnos pero conserva el historial.

### US-022 — Pacientes con datos mínimos
**Como** recepción, **quiero** registrar paciente con nombre, DNI, teléfono y obra social (texto), **para** asociarlo a turnos.
- [ ] CA-1: DNI único. CA-2: no existen campos clínicos. CA-3: seeds y tests usan solo datos ficticios.

**Reglas**: RN-PA-01, RN-PA-02

## Épica 4: Ciclo de vida del turno

### US-030 — Cancelar turno
**Como** secretaria, **quiero** cancelar un turno, **para** mantener la agenda al día.
- [ ] CA-1: `reservado`/`confirmado` → `cancelado` libera profesional y sillón. CA-2: desde estado terminal → `INVALID_TRANSITION`. CA-3: queda entrada de historial.

### US-031 — Reprogramar turno
**Como** secretaria, **quiero** mover un turno a otro horario, profesional o sillón, **para** reorganizar la agenda.
- [ ] CA-1: se revalidan todas las RN-AG excluyendo al propio turno. CA-2: no se puede reprogramar al pasado. CA-3: solo en `reservado`/`confirmado`. CA-4: el turno vuelve a `reservado`. CA-5: se registra en el historial.

**Reglas**: RN-TU-03, RN-AG-06

### US-032 — Cambiar estado
**Como** recepción u odontólogo, **quiero** marcar un turno como confirmado, atendido o ausente, **para** reflejar lo ocurrido.
- [ ] CA-1: solo transiciones de la tabla RN-TU-02. CA-2: `atendido`/`ausente` solo con `now >= inicio`. CA-3: odontólogo solo modifica turnos propios.

**Reglas**: RN-TU-02, RN-TU-05, RN-AC-01

### US-033 — Historial de cambios
**Como** administrador, **quiero** ver quién cambió qué y cuándo, **para** tener trazabilidad.
- [ ] CA-1: cada transición/reprogramación genera una entrada con `from`, `to`, `changed_by`, `changed_at`. CA-2: el historial no se edita ni se borra.

**Reglas**: RN-TU-06

## Épica 5: Interfaz web de agenda

### US-040 — Agenda diaria y semanal
**Como** recepción u odontólogo, **quiero** ver la agenda por día y por semana, filtrable por profesional y por sillón, **para** operar el consultorio.
- [ ] CA-1: vista diaria con columna por profesional. CA-2: vista semanal por profesional. CA-3: los turnos se colorean por estado. CA-4: usable en pantallas de escritorio y tablet; responsive básico.

### US-041 — Vista de recepción por sillón (diferenciador)
**Como** recepción, **quiero** ver la agenda con una columna por sillón, **para** saber qué sillón está libre.
- [ ] CA-1: columnas por sillón con turnos de todos los profesionales. CA-2: los huecos libres son visibles.

### US-042 — Dar y reprogramar turno desde la UI con errores explicados
**Como** secretaria, **quiero** que el formulario muestre el motivo del rechazo, **para** corregirlo sin adivinar.
- [ ] CA-1: se muestran los mensajes del dominio tal cual (código + texto). CA-2: el formulario sugiere duración por defecto de la prestación.

## Épica 6: Roles y acceso

### US-050 — Sesión con rol (JWT)
**Como** usuario del consultorio, **quiero** iniciar sesión y operar con mi rol, **para** que la API aplique mis permisos.
- [ ] CA-1: la API aplica la matriz RBAC de 03 según el rol. CA-2: sin rol → `401`; rol sin permiso → `403`.
- *El rol sale del JWT (DD-11), que reemplaza al rol simulado por decisión de la cátedra (2026-10-08). Los criterios de aceptación no cambian: "sin rol" = sin JWT válido.*

## Épica 7: Backlog posterior al MVP (no implementar)

Búsqueda del primer hueco · sobreturnos con marca y límite · paciente sin turnos simultáneos (RN-PA-03) · confirmación/recordatorio por enlace de WhatsApp y luego API oficial · reserva online con aprobación · lista de espera · seña con Mercado Pago · facturación ARCA y obras sociales · ficha clínica y odontograma · múltiples sedes, reportes y exportación.
