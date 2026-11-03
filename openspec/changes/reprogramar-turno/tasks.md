# Tasks

Gobernanza MEDIO; decisiones D1–D9 cerradas por la autora, sin checkpoint ni aprobación intermedia. Este archivo planifica el apply: nada se ejecuta durante propose. Antes de modificar existentes correr Safety Net; fallos previos obligan detener y reportar sin arreglos fuera de alcance. Cada tarea de producción exige RED escrito y ejecutado con fallo esperado antes de GREEN mínimo; agregar casos de triangulación uno por ciclo (mínimo dos por comportamiento) y ejecutar después de cada refactor. No escribir todos los tests primero. Regresiones que ya pasan se registran como tales; una mutación restaurada demuestra sensibilidad, pero no sustituye el RED obligatorio de comportamiento nuevo.

Seams definidas por contratos cerrados: `RescheduleRequest`, `reschedule_appointment`, `validate_new_appointment` (reutilizado sin cambios) y la regla del pasado parametrizada. Datos literales del spec, UUID distintos para usuario/profesional y `now` UTC; sin mocks/patch/monkeypatch/freezegun/Any. Cargar `tdd`, `python-testing-patterns` y `python-pro` en apply con overlay de reglas duras. No tocar `rules/overlap.py`, `OCCUPYING_STATUSES`, `rules/working_hours.py`, `rules/blocks.py`, `rules/references.py`, `rules/duration.py`, reglas de alta ni catálogo. No modificar `openspec/specs/`, `CHANGES.md`, `AGENTS.md`, `CLAUDE.md`, `knowledge-base/` ni `.active-orchestrator-state.json`.

## 1. Safety Net

- [ ] 1.1 Inspeccionar diff/estado y ejecutar desde `backend` la suite pytest existente y mypy estricto con el intérprete del venv disponible; registrar comandos, número real y resultados. Detener ante fallo preexistente. No asumir conteos de archivos anteriores ni instalar dependencias. Verificar con `openspec validate reprogramar-turno --strict`.
- [ ] 1.2 Identificar expectativas/imports vigentes de `validate_new_appointment`, `check_not_in_the_past`, `Ok.appointment` y la guardia. Conservar trabajo ajeno (C-13 corre en paralelo: no tocar `docker-compose.yml`, `.env` ni `backend/app/db`). Preparar evidencia por tarea con columnas Test File, Layer, Safety Net, RED, GREEN, TRIANGULATE, REFACTOR; no marcar tareas sin evidencia real.

## 2. Pedido de reprograma y verbo del pasado

- [ ] 2.1 RED `RescheduleRequest` en test de modelo: construir con `start_at` obligatorio (con zona) y `professional_id`/`chair_id`/`duration_min` en `None`; GREEN mínimo `RescheduleRequest` frozen/slots en `model.py` con `start_at` normalizado a UTC. TRIANGULATE inicio en hora de Buenos Aires (`-03:00`) que normaliza a UTC y verificación de que `None` conserva el sentido de "conservar". Ejecutar tests de modelo y mypy tras cada cambio.
- [ ] 2.2 RED: `validate_new_appointment` recibe un parámetro `operation` con valor por defecto "dar turnos" que pasa a `check_not_in_the_past` (que también lo recibe con el mismo nombre y el mismo default). GREEN: añadir `operation: str = "dar turnos"` a `check_not_in_the_past` (mensaje `f"no se pueden {operation} en el pasado."`) y a `validate_new_appointment`, que lo reenvía a la regla; el alta llama sin el parámetro (default "dar turnos"), sin cambiar su mensaje. TRIANGULATE: el alta sigue diciendo "no se pueden dar turnos en el pasado." (cubre la regresión 3.1) y al pasar `operation="reprogramar turnos"` a `validate_new_appointment` el mensaje dice "no se pueden reprogramar turnos en el pasado." REFACTOR sin alterar la comparación estricta de instantes; ejecutar tests de `past`, de `validate` y mypy.

## 3. Regresión del alta

- [ ] 3.1 RED de regresión: un alta de turno en el pasado (`now` 10:00 local, inicio 09:55 local) produce `IN_THE_PAST` con el mensaje exacto "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado." (sin "reprogramar"). Si ya pasa por composición, registrar como verde y demostrar sensibilidad mutando el verbo por defecto a "reprogramar turnos", ver el fallo y restaurar. Este test protege que el alta no cambió y NO sustituye el RED obligatorio de reprogramar.

## 4. Reprogramar válido

- [ ] 4.1 RED `reschedule_appointment` con T1 reservado, recepción U2, now 09:00 local, reprograma a 11:00 local (14:00 UTC), mismo P1/S1 y duración 30; GREEN mínimo en `appointment/reschedule.py` que reutilice `validate_new_appointment` con el propio excluido y devuelva `Ok.appointment`. Afirmar mismo id, intervalo 14:00–14:30 UTC y estado `reservado`. TRIANGULATE desde confirmado (vuelve a reservado) y que el original no cambia. Exportar en `appointment/__init__.py`.
- [ ] 4.2 RED: reprogramar conservando la duración real (T1 duración efectiva 30, prestación default 45, sin indicar duración) queda 11:00–11:30, no 11:00–11:45. GREEN: la duración efectiva al omitir `duration_min` es `appointment.end_at − appointment.start_at`. TRIANGULATE cambiar la duración a 60 (queda 11:00–12:00) y reprogramar cambiando solo el inicio a 10:00 (conserva P1/S1/duración). Ejecutar tests y mypy.

## 5. Auto-exclusión del propio turno

- [ ] 5.1 RED: T1 reservado de 10:00–10:30, reprograma a 10:15 (solapa su intervalo viejo), con T1 incluido en la agenda recibida; sin el filtro, aparecería `PROFESSIONAL_OVERLAP` contra T1. GREEN: excluir por id (`a.id != appointment.id`) antes de llamar a `validate_new_appointment`. TRIANGULATE reprogramar a su mismo intervalo 10:00 (Ok) y el caso de cambiar solo el profesional a P2 conservando S1 y 10:00 (no choca por sillón consigo mismo: el propio queda excluido y no hay turnos de P2 en S1 a esa hora). Verificar que la corrección no depende de que el llamador filtre: el dominio excluye aunque la agenda incluya al propio.

## 6. Precondición de estado

- [ ] 6.1 RED: reprogramar T1 `atendido` → una sola `INVALID_TRANSITION` con mensaje dedicado "El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no se puede reprogramar porque está en estado terminal "atendido"." GREEN: precondición `status in {RESERVED, CONFIRMED}` con mensaje dedicado (no `can_transition`). TRIANGULATE `ausente` y `cancelado` con su texto correspondiente, en casos independientes, y comprobar que el original conserva su estado e intervalo. No usar el mensaje "no puede pasar del estado X al estado Y".

## 7. Permisos

- [ ] 7.1 RED: odontólogo Laura U1/P1 intenta reprogramar T1 propio → una sola `FORBIDDEN_OPERATION` "No tiene permiso para reprogramar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden reprogramar turnos." GREEN: permiso primero y corta. TRIANGULATE odontólogo ajeno (T2 de P2) con su mensaje (Dra. Inés Molina, 11:00–11:30) y recepción/administración que reprograman con Ok. Comparar `professional_id`, no `user_id`; sin JWT ni consultas externas.

## 8. Orden de evaluación

- [ ] 8.1 RED: odontólogo con T1 propio terminal y un slot destino en el pasado → solo `FORBIDDEN_OPERATION` (el estado y el pasado no se evalúan). GREEN: permiso corta. TRIANGULATE recepción con T1 cancelado y un slot destino que chocaría → solo `INVALID_TRANSITION` (los conflictos del slot no se evalúan). Verificar que un resultado nunca mezcla permiso/estado con violaciones del turno nuevo. REFACTOR orden de guardas: contrato → permiso → estado → turno nuevo; ejecutar tras cada cambio y mypy.

## 9. Revalidación completa del turno nuevo

- [ ] 9.1 RED: reprogramar a 11:00 chocando con otro turno T3 de P1 en S2 a 11:00–11:30 → `PROFESSIONAL_OVERLAP` con mensaje exacto "Dra. Laura Quiroga ya tiene un turno de 11:00 a 11:30 (hora local) que se superpone (turno {id de T3})." GREEN: la revalidación reutiliza `validate_new_appointment` y devuelve sus violaciones. TRIANGULATE choque de sillón con T4 de P2 en S1 a 11:00–11:30 → `CHAIR_OVERLAP` con mensaje exacto "Sillón 1 está ocupado de 11:00 a 11:30 (hora local) por un turno que se superpone (turno {id de T4})." (sin "El"). Los textos se copian de `openspec/specs/appointment-scheduling/spec.md`, no se redactan.
- [ ] 9.2 RED: reprogramar a 11:00 fuera del horario de P1 (solo atiende hasta 11:00) → `OUTSIDE_WORKING_HOURS` con el mismo texto exacto que al dar un turno nuevo en ese slot. GREEN reutilizando la regla vigente. TRIANGULATE reprogramar a 11:0 0 sobre un bloqueo BL1 de P1 de 11:00–12:00 → `BLOCKED_TIME` con el id de BL1 y el texto exacto del alta. No modificar `rules/working_hours.py` ni `rules/blocks.py`.
- [ ] 9.3 RED: reprogramar al pasado (now 10:00 local, destino 09:00 local) → `IN_THE_PAST` con "no se pueden reprogramar turnos en el pasado." GREEN: `reschedule_appointment` pasa `operation="reprogramar turnos"` a `validate_new_appointment`, que lo reenvía a `check_not_in_the_past` (no llama a la regla directo). TRIANGULATE now con segundos (10:00:30) y destino 10:00 (mismo minuto) → `IN_THE_PAST` con el texto exacto "no se pueden reprogramar turnos en el pasado." Verificar que el alta sigue diciendo "dar turnos" (regresión 3.1 sigue verde).
- [ ] 9.4 RED: reprogramar cambiando el profesional a P3 inexistente → `UNKNOWN_REFERENCE` de tipo `PROFESSIONAL`. GREEN reutilizando `check_references`. TRIANGULATE reprogramar con la prestación de T1 inactiva → `INACTIVE_REFERENCE` de tipo `SERVICE` (la actividad de la prestación se revalida aunque no cambie). Verificar que un profesional/sillón nuevo inactivo da `INACTIVE_REFERENCE`. El paciente y la prestación no se cambian: se toman del original.

## 10. Contrato e inmutabilidad

- [ ] 10.1 RED: reprogramar con un contexto cuyo `now` es 2026-10-20T09:00:00 sin zona → la construcción del `ScheduleContext` lanza `ValueError` que indica que `now` necesita zona. GREEN: la validación ya existe en el contexto; sin lógica nueva. TRIANGULATE reprogramar que rechaza por conflicto (T3 en el slot destino) y comprobar que el original T1 conserva inicio 13:00 UTC, fin 13:30 UTC y estado `reservado`. Los errores de negocio nunca se lanzan.

## 11. Pureza y compatibilidad

- [ ] 11.1 Verificar que `reschedule_appointment` es síncrona, totalmente tipada y sin `Any`, reloj global, generación de ids, I/O, Pydantic, FastAPI, SQLAlchemy ni Redis. Pasar las guardias vigentes de imports y reloj sin modificar la allowlist. No se agregan `ViolationCode` y `OCCUPYING_STATUSES` sigue exactamente `reservado`, `confirmado`, `atendido`. El alta y el catálogo conservan mensajes y contratos; el mensaje del pasado del alta sigue siendo "dar turnos". REFACTOR de tipos/exportaciones y ejecutar tests/mypy.

## 12. Verificación final del apply

- [ ] 12.1 Ejecutar suite completa pytest y mypy estricto desde `backend`; guardias reales de imports/reloj limpias, sin modificar su allowlist. Revisar no `Any`, I/O, generación de UUID, reloj global, historial, dependencias nuevas ni cambios en `OCCUPYING_STATUSES`/reglas de alta. Revisar estilo/docstrings sin instalar herramientas.
- [ ] 12.2 Trazar cada escenario del delta `appointment-lifecycle` (reprogramar) y del delta `appointment-scheduling` (mensaje del pasado, alta y reprogramar) a tests concretos PASSED; completar tabla TDD y registrar baseline, RED/GREEN, triangulación, refactor y mutaciones restauradas, sin evidencias inventadas. Reportar cualquier desvío real.
- [ ] 12.3 Revisar diff y `git diff --check`: cambios limitados a `backend/app/domain/appointment/reschedule.py`, `backend/app/domain/model.py` (`RescheduleRequest`), `backend/app/domain/rules/past.py` (parámetro de operación), `backend/app/domain/appointment/validate.py` (valor por defecto) y `backend/app/domain/appointment/__init__.py`, más tests nuevos. Sin stage/commit/push/archive; sin tocar `openspec/specs/`, `CHANGES.md`, `AGENTS.md`, `CLAUDE.md`, `knowledge-base/`, `.active-orchestrator-state.json`, `docker-compose.yml` ni `.env`. Ejecutar `openspec validate reprogramar-turno --strict` y reportar el resultado.
