# Proposal

## Why

El dominio ya da turnos válidos (C-02 a C-08) y maneja el ciclo de vida ordinario (C-10: cancelar y cambiar estado con actor, permisos y copias inmutables), pero todavía no permite mover un turno existente. C-11 incorpora la operación de reprogramar: revalida todas las reglas RN-AG del turno nuevo excluyendo al propio turno, solo desde `reservado` o `confirmado`, con el turno vuelto a `reservado` y el mismo id, reutilizando `validate_new_appointment` sin duplicar ninguna regla. Prepara el historial de transiciones (C-12).

## What Changes

- Nueva operación pura `reschedule_appointment`: revalida todas las RN-AG llamando a `validate_new_appointment` con el turno propio **excluido por id** de los existentes; solo desde `reservado` o `confirmado` (los tres terminales → `INVALID_TRANSITION` con mensaje dedicado de reprogramar); el turno aceptado vuelve a `reservado` y conserva su id; el inicio es obligatorio y el profesional, el sillón y la duración son opcionales (`None` = conservar el valor actual); el paciente y la prestación no se cambian.
- Permisos: el odontólogo nunca reprograma (ni propios) → `FORBIDDEN_OPERATION` que corta; recepción y administración reprograman todos. La política RBAC de KB 03 prevalece (fila "reprogramar / cancelar" = `—` para odontólogo).
- Orden de evaluación: permiso corta; estado corta; luego la revalidación del turno nuevo en sus dos grupos (validez del pedido y, si pasa, conflictos de agenda) según RN-AG-12.
- Se parametriza el verbo del mensaje de `IN_THE_PAST` (`check_not_in_the_past`): el alta conserva exactamente "no se pueden dar turnos en el pasado" y reprogramar usa "no se pueden reprogramar turnos en el pasado". Precedente: `check_duration` ya acepta un `subject` parametrizable.
- Los mensajes de conflicto del turno nuevo (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, etc.) se reutilizan con sus textos vigentes; no se redactan de nuevo.
- Sin historial (lo agrega C-12), sin códigos `ViolationCode` nuevos, sin cambios en `OCCUPYING_STATUSES`, en las reglas de alta ni en el catálogo.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-lifecycle`: se agregan requisitos de la operación de reprogramar (reschedule): revalidación de todas las RN-AG excluyendo al propio turno, precondición de estado `reservado`/`confirmado` con mensaje dedicado, permisos (odontólogo no reprograma), orden de evaluación (permiso corta, estado corta), resultado en `reservado` con el mismo id, conservación de paciente y prestación, duración efectiva conservada si no se indica, errores de contrato (`now` naive) e inmutabilidad del original.
- `appointment-scheduling`: se modifica el requisito "Mensaje de un turno en el pasado" para que el verbo del mensaje de `IN_THE_PAST` sea parametrizable por operación; el alta conserva el texto exacto "no se pueden dar turnos en el pasado" y se agrega la variante de reprogramar "no se pueden reprogramar turnos en el pasado".

## Impact

- Apply futuro: nuevo `backend/app/domain/appointment/reschedule.py`; `model.py` agrega `RescheduleRequest`; `validate_new_appointment` agrega un parámetro opcional `operation` con valor por defecto "dar turnos", que pasa a `check_not_in_the_past` (que también lo recibe con el mismo nombre y el mismo default y lo usa en el mensaje de `IN_THE_PAST`); el alta no pasa el parámetro (conserva "dar turnos") y `reschedule_appointment` le pasa "reprogramar turnos"; `appointment/__init__.py` exporta `reschedule_appointment`; nuevos tests de reprograma y una tarea de regresión que prueba que el mensaje del alta no cambió.
- Sin cambios en `rules/overlap.py`, `OCCUPYING_STATUSES`, `rules/working_hours.py`, `rules/blocks.py`, `rules/references.py`, `rules/duration.py`, reglas de alta ni catálogo. El cambio a `past.py` es retrocompatible (parámetro con valor por defecto).
- Dependencias C-08 y C-10 cumplidas. Gobernanza MEDIO; decisiones D1–D9 cerradas por la autora, sin punto de control.
- Fuera de alcance: historial (C-12), JWT/autenticación (C-19), API (C-22/C-23), UI (C-29/C-30), persistencia y migraciones. Este propose solo crea artefactos en este change; no modifica `openspec/specs/`, `CHANGES.md`, `AGENTS.md`, `CLAUDE.md`, `knowledge-base/` ni `.active-orchestrator-state.json`.
