# Explore de C-08 mensajes-de-conflicto-en-espanol

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-30 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02 a C-07 ya estaban archivados. `validate_new_appointment(request, references, existing_appointments, context)` (en `backend/app/domain/appointment/validate.py`) evalúa en dos grupos. El grupo 1, validez del pedido, tiene referencias → duración → inicio en la grilla → medianoche → pasado; si hay alguna violación, corta ahí. El grupo 2, conflictos de agenda, tiene horario → bloqueo → profesional → sillón, todo junto.
- Inventario del alcance de C-08 que **ya estaba cumplido**:
  - Toda violación tiene `code` y `message` en español (requisito "Contenido de cada violación").
  - `conflicting_appointment_id` en `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` desde C-02; `conflicting_block_id` en `BLOCKED_TIME` desde C-06 (requisito "Turno fuera de los bloqueos del profesional").
  - Hora local en los mensajes de `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT` e `IN_THE_PAST`, con las funciones `format_local_*` de C-04 y textos exactos en el spec.
  - Composición de todas las reglas y orden de RN-AG-12, con escenarios de varias violaciones a la vez y orden independiente de la lista recibida (requisito "Todas las violaciones, en orden estable").
- Lo que **faltaba de verdad**:
  - `Violation` no tiene el intervalo que choca (US-006 CA-1).
  - `Professional` y `Chair` del dominio solo tienen `id` y `active`: no hay nombre para el mensaje (US-006 CA-3). KB 04 ya define `Professional.full_name` y `Chair.name`.
  - Los mensajes de solapamiento no tienen ni nombre ni rango horario ("El profesional ya tiene un turno que se superpone (turno {id}).") y no tienen test de texto exacto.
  - El spec arrastra tres frases "queda para C-08" (requisitos "Contenido de cada violación", "Turno dentro del horario de atención" y "Mensaje de un turno bloqueado").
  - RN-AG-12, DD-08, US-006 CA-2 y CHANGES §[C-08] describen un único orden de nueve pasos con "todas", pero el dominio corta después del grupo 1.
- En el grupo 2 las referencias ya pasaron el grupo 1: `references.professional` y `references.chair` existen y están activos. El profesional y el sillón del conflicto son siempre los del pedido (el turno que choca comparte ese recurso), así que no hace falta el nombre de otras entidades.
- Solo `test_validate_new_appointment.py` construye `Professional` (6 veces) y `Chair` (6 veces).
- `check_blocks` ignora los bloqueos con `inicio >= fin`, así que todo bloqueo en conflicto puede representarse con `Interval` sin lanzar.
- No había changes activos. La spec `appointment-scheduling` tiene 25 requisitos.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿De dónde sale el nombre del profesional y del sillón, y qué pasa si falta? | Campos nuevos `Professional.full_name: str` y `Chair.name: str` (los nombres de KB 04), obligatorios y sin valor por defecto. La entidad no los valida al construirse. Con el nombre vacío o solo espacios, el mensaje usa el sustantivo genérico "El profesional" / "El sillón". `validate.py` pasa el nombre a cada regla del grupo 2 como `str`. | El dato vive en su entidad y C-15 lo mapea directo a la columna. Sin default, mypy avisa si un llamador se olvida de pasarlo (mismo criterio que `ScheduleContext.now`). Un nombre vacío es un dato del usuario, no un error de programación: C-09 lo va a rechazar en el alta con una violación, así que no se lanza `ValueError`. Los 12 constructores de los tests cambian de forma mecánica. |
| 2 | ¿Cómo se representa el intervalo que choca? | Campo nuevo `Violation.conflicting_interval: Interval \| None = None`, al final del dataclass, en UTC. Se carga en `PROFESSIONAL_OVERLAP` y `CHAIR_OVERLAP` (intervalo del turno existente) y en `BLOCKED_TIME` (intervalo del bloqueo); en el resto es `None`. Invariante: hay intervalo si y solo si hay id de turno o de bloqueo. | Un solo campo no permite estados imposibles (inicio sin fin). El dominio guarda instantes en UTC (DD-07); la API los serializa en ISO con offset y la hora local legible ya está en el mensaje. `OUTSIDE_WORKING_HOURS` choca con la ausencia de un tramo, no con un intervalo. Al final del dataclass no cambia ninguna construcción existente. |
| 3 | ¿Qué mensajes cambian y cómo quedan? | Cambian cuatro. El nombre va siempre como sujeto, sin artículo y nunca después de "de" (ajuste de la autora). Los textos están abajo. No cambian `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE` ni las violaciones de tramos y bloqueos inválidos. | El dominio no sabe si corresponde "la Dra." o "el Dr.": sin artículo y como sujeto, la frase nunca queda mal. Los seis textos exactos aprobados que cambian (tres de horario, tres de bloqueo) se marcan como `MODIFIED` en el delta, no se cambian en silencio. |
| 4 | ¿Cómo conviven "devuelve todas" y el corte después del grupo 1? | El dominio devuelve **todas las violaciones del primer grupo que falla**, nunca solo la primera. "Todas" se entiende dentro de un grupo: si el pedido no es válido, no hay un turno contra el cual evaluar los conflictos de agenda. Se aclara en el spec y se sincroniza en RN-AG-12, DD-08, US-006 CA-2 y CHANGES §[C-08]. | El corte ya está implementado y probado ("Violación de validez en un horario ocupado", "Turno en el pasado en un horario ocupado"); lo que estaba desalineado era la documentación. |
| 5 | ¿Conviene dividir el change? | No. Un solo change, con dos bloques de tareas y un punto de control entre el intervalo (estructural, sin tocar textos) y los nombres y textos. | El tamaño es comparable a C-06. Dividirlo obliga a reescribir las dependencias y los gates de C-11 y C-22 en CHANGES por una diferencia chica. |

### Textos de los cuatro mensajes

Datos ficticios: P1 = "Dra. Laura Quiroga", S1 = "Sillón 1", martes 20/10/2026, turno existente A de 10:00 a 10:30 hora local.

| Código | Antes | Después | Con el nombre vacío |
|---|---|---|---|
| `PROFESSIONAL_OVERLAP` | El profesional ya tiene un turno que se superpone (turno {A}). | Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {A}). | El profesional ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {A}). |
| `CHAIR_OVERLAP` | El sillón ya está ocupado por un turno que se superpone (turno {A}). | Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {A}). | El sillón está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {A}). |
| `OUTSIDE_WORKING_HOURS` | El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención del profesional: el martes atiende de 09:00 a 13:00 y de 15:00 a 19:00. | El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00. | …queda fuera del horario de atención: el profesional atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00. |
| `OUTSIDE_WORKING_HOURS` (día sin tramos) | El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención del profesional: no atiende los domingos. | El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención: Dra. Laura Quiroga no atiende los domingos. | …queda fuera del horario de atención: el profesional no atiende los domingos. |
| `BLOCKED_TIME` | El turno de 10:30 a 11:00 (hora local) se superpone con el bloqueo {BL1} del profesional, del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local). | El turno de 10:30 a 11:00 (hora local) se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {BL1}). | …se superpone con un bloqueo de agenda: el profesional tiene la agenda bloqueada del … (bloqueo {BL1}). |

Con motivo, `BLOCKED_TIME` agrega " Motivo: vacaciones." al final, igual que antes. En los dos mensajes en los que el sustituto va después de dos puntos (`OUTSIDE_WORKING_HOURS` y `BLOCKED_TIME`) se escribe en minúscula ("el profesional"), como el texto anterior ("…: el martes atiende…"); en los de solapamiento abre la oración y va con mayúscula.

## Pedidos para el propose

- `model.py`: `full_name` en `Professional` y `name` en `Chair`, obligatorios, sin validar al construir.
- `violations.py`: `conflicting_interval: Interval | None = None` al final de `Violation`.
- `rules/overlap.py`: las dos reglas reciben el nombre y `tz`, cargan el intervalo del turno existente y arman el mensaje nuevo.
- `rules/blocks.py`: `check_blocks` recibe el nombre, carga el intervalo del bloqueo y arma el mensaje nuevo.
- `rules/working_hours.py`: `check_working_hours` recibe el nombre y arma el mensaje nuevo.
- `appointment/validate.py`: pasa los nombres desde `references` a las reglas del grupo 2.
- Tests (martes 20/10/2026, hora local = UTC−3; P1 = "Dra. Laura Quiroga", S1 = "Sillón 1"):
  1. Solapamiento de profesional con A → `conflicting_interval` = intervalo de A en UTC.
  2. Solapamiento de sillón con A → `conflicting_interval` = intervalo de A en UTC.
  3. Bloqueo BL1 → `conflicting_interval` = intervalo de BL1 en UTC; un bloqueo de varios días conserva sus extremos.
  4. `OUTSIDE_WORKING_HOURS`, violaciones del grupo 1 → `conflicting_interval` es `None`.
  5. Invariante: en un rechazo con horario, bloqueo y solapamientos, cada violación tiene intervalo si y solo si tiene id de turno o de bloqueo.
  6. Texto exacto de `PROFESSIONAL_OVERLAP` y de `CHAIR_OVERLAP` con nombre.
  7. Texto exacto de los cuatro mensajes con el nombre vacío y con el nombre solo de espacios.
  8. Los seis textos exactos de horario y bloqueo, reescritos con el nombre como sujeto.
  9. `INACTIVE_REFERENCE` no cambia aunque la entidad tenga nombre.
- En la spec: modificar "Contenido de cada violación", "Todas las violaciones, en orden estable", "Turno dentro del horario de atención", "Turno fuera de los bloqueos del profesional" y "Mensaje de un turno bloqueado"; borrar las frases "queda para C-08".
