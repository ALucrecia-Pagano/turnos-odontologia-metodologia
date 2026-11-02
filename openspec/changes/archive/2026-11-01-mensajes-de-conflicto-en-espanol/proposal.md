# Proposal

## Why

Después de C-07, el dominio ya rechaza todo lo que pide la KB y cada violación trae `code`, `message` en español y el id del turno o del bloqueo que choca, pero el rechazo todavía no explica el problema como pide el diferenciador del MVP. US-006 CA-1 pide que la violación traiga además **el intervalo que choca**, y CA-3 que el mensaje diga **el nombre del profesional o del sillón y el rango en hora local**. Hoy los mensajes de solapamiento no tienen ni nombre ni horario ("El profesional ya tiene un turno que se superpone (turno {id}).") y no tienen test de texto exacto; `Professional` y `Chair` del dominio solo tienen `id` y `active`, así que no hay nombre que mostrar. La spec arrastra frases "queda para C-08" en cuatro requisitos, y "devuelve todas" (RN-AG-12, DD-08, US-006 CA-2) no decía que "todas" es dentro del primer grupo que falla.

Este change va ahora porque ya están todas las reglas que producen mensajes (C-02 a C-07) y porque C-11 (reprogramar) y C-22 (API de turnos) reutilizan las violaciones tal como queden acá. Depende de C-03, C-05, C-06 y C-07. Las decisiones salen del explore del 2026-10-30 (`docs/evidencias/explore-C-08.md`), confirmadas por la autora.

## What Changes

- **Intervalo que choca** (US-006 CA-1): `Violation` suma `conflicting_interval`, el intervalo en UTC del turno existente en `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` y el del bloqueo en `BLOCKED_TIME` (un bloqueo de varios días conserva sus extremos). En el resto de las violaciones no hay intervalo. Invariante: hay intervalo si y solo si hay id de turno o de bloqueo en conflicto. Es un campo nuevo al final, con valor por defecto, así que ninguna construcción existente cambia.
- **Nombre del profesional y del sillón** (US-006 CA-3; KB 04): `Professional.full_name` y `Chair.name`, **obligatorios y sin valor por defecto**. El dominio no los valida al construir la entidad (la validez del catálogo es de C-09). **BREAKING** (solo interno): construir un `Professional` o un `Chair` exige el nombre; cambian de forma mecánica los 12 constructores de `test_validate_new_appointment.py` y el ejemplo de `backend/README.md`.
- **Cuatro mensajes nuevos**, con el nombre siempre como sujeto, sin artículo y nunca después de "de" (P1 = "Dra. Laura Quiroga", S1 = "Sillón 1", turno A de 10:00 a 10:30 hora local):
  - `PROFESSIONAL_OVERLAP`: "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {A})."
  - `CHAIR_OVERLAP`: "Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {A})."
  - `OUTSIDE_WORKING_HOURS`: "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00." (o "…: Dra. Laura Quiroga no atiende los domingos.").
  - `BLOCKED_TIME`: "El turno de 10:30 a 11:00 (hora local) se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {BL1})." y, si hay motivo, " Motivo: vacaciones." al final, como hoy.
- **Nombre vacío o en blanco**: el mensaje usa el sustantivo genérico, "El profesional" / "El sillón" al principio de la oración (solapamientos) y "el profesional" después de dos puntos (horario y bloqueo). No es una excepción: un nombre vacío es un dato del usuario.
- **Textos exactos aprobados que cambian**: los tres escenarios de texto exacto de "Turno dentro del horario de atención" y los tres de "Mensaje de un turno bloqueado" se reescriben con el nombre como sujeto (`MODIFIED` en el delta, no en silencio).
- **Mensajes que no cambian**: `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE` (aunque la entidad tenga nombre), `INVALID_BLOCK`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS`.
- **"Todas" dentro del primer grupo que falla** (RN-AG-12, US-006 CA-2): el dominio devuelve todas las violaciones del primer grupo que falla, nunca solo la primera; con un pedido inválido no se evalúan los conflictos de agenda. Ya está implementado y probado; se aclara en la spec.
- Se quitan de la spec todas las frases "queda para C-08".

### Fuera de alcance

- Validar el nombre al dar de alta un profesional o un sillón (vacío, solo espacios, único) → C-09.
- Serializar el intervalo y los ids en la respuesta HTTP (`conflictingAppointmentId`, `conflictingBlockId`, intervalo en ISO con offset) → C-22.
- Mapear `full_name` y `name` a columnas → C-15.
- Artículo o tratamiento según el profesional ("la Dra.", "el Dr."): el dominio no lo sabe y el nombre va sin artículo.
- Cambiar el orden de RN-AG-12 o el corte después del grupo 1.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: los requisitos de solapamiento de profesional y de sillón y "Turno fuera de los bloqueos del profesional" suman el intervalo que choca; "Contenido de cada violación" define el texto exacto de los solapamientos con nombre y rango local, el sustituto genérico del nombre, la regla del intervalo y los mensajes que no cambian; "Turno dentro del horario de atención" y "Mensaje de un turno bloqueado" cambian su plantilla y sus tres textos exactos; "Todas las violaciones, en orden estable" aclara que "todas" es dentro del primer grupo que falla; "Mensaje de un turno en el pasado" pierde la frase "queda para C-08". Se agrega el requisito del nombre del profesional y del sillón en el modelo.

## Impact

- **Código modificado** en `backend/app/domain/`: `model.py` (`Professional.full_name`, `Chair.name`), `violations.py` (`Violation.conflicting_interval`), `rules/overlap.py` (intervalo, nombre, `tz` y mensaje nuevo), `rules/blocks.py` (intervalo, nombre y mensaje nuevo), `rules/working_hours.py` (nombre y mensaje nuevo) y `appointment/validate.py` (pasa los nombres de `references` al grupo 2).
- **Código nuevo**: `backend/app/domain/rules/names.py` (sustituto genérico del nombre vacío; design D6).
- **Tests**: `test_validate_new_appointment.py` (constructores con nombre, escenarios nuevos y los seis textos exactos reescritos), `test_model.py`, `test_violations.py` y `test_names.py` (nuevo).
- **Documentación**: `backend/README.md` (ejemplo con nombres, fila de `violations` y de `rules/`) y evidencias en `docs/evidencias/`. La KB (05, 06, 09) y `CHANGES.md` §[C-08] ya se sincronizaron después del explore.
- **Dependencias**: ninguna nueva; la allowlist del dominio no cambia.
- **Governance**: MEDIO. Hay un punto de control entre el bloque A (intervalo, estructural, sin tocar textos) y el bloque B (nombres y textos): la autora revisa el intervalo y aprueba antes de cambiar mensajes.
