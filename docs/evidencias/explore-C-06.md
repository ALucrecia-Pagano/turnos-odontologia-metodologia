# Explore de C-06 bloqueos-de-agenda

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-28 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02 a C-05 ya estaban archivados. `validate_new_appointment(request, references, existing_appointments, context)` evalúa en dos grupos. El grupo 1, validez del pedido, tiene referencias → duración → inicio en la grilla → medianoche; si hay alguna violación, corta ahí. El grupo 2, conflictos de agenda, tiene horario → profesional → sillón, todo junto. El docstring de `_agenda_conflict_violations` ya anunciaba que C-06 suma ahí los bloqueos.
- `ScheduleContext` tenía `tz` y `working_hours`, sin valores por defecto, y su docstring ya anunciaba los bloqueos.
- No existía nada de `Block`: ni el modelo, ni `rules/blocks.py`, ni `BLOCKED_TIME` en `ViolationCode` (sí en el catálogo de KB 07). El catálogo no tiene código para un bloqueo con `inicio >= fin` (RN-DI-03). `Violation` solo tiene `conflicting_appointment_id`; C-08 nombra `conflicting_block_id`, pero US-004 CA-4 ya pide el id del bloqueo.
- Se pueden reusar `_to_utc` de `model.py` (normaliza a UTC y rechaza instantes naive), `Interval` y `overlaps` de `intervals.py`, y `OCCUPYING_STATUSES` y el orden `(start_at, str(id))` de `rules/overlap.py`.
- Solo `CTX` y `_ctx()` de `test_validate_new_appointment.py` construyen un `ScheduleContext`: sumar un campo cambia esas dos líneas.
- En el `.venv`, `zoneinfo` confirma que Buenos Aires es UTC−3 fijo en estas fechas (sin horario de verano), que el 2026-10-19 y el 2026-10-26 son lunes, que el 2026-10-18 y el 2026-10-25 son domingos, y que el domingo 25 a las 23:30 locales es el lunes 26 a las 02:30 UTC.
- No había changes activos. La spec `appointment-scheduling` tiene 17 requisitos.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿Cómo llegan los bloqueos al dominio? | En `ScheduleContext.blocks: tuple[Block, ...]`, sin valor por defecto. El dominio filtra por el profesional del pedido. | Es la decisión 1 de C-05 y lo que anunciaba el docstring: la firma no cambia. Sin default, mypy avisa si un llamador se olvida de pasarlos; con `()` un olvido sería "no hay bloqueos" sin ningún aviso. El resultado no depende de que el llamador haya filtrado. |
| 2 | ¿En qué grupo va la regla y en qué orden? | En el grupo 2: horario → bloqueo → profesional → sillón, todo junto y sin cortar. | Es el orden de RN-AG-12 y el grupo 2 informa todo junto desde C-02. El bloqueo es un conflicto de agenda, no un problema del pedido. Hay que actualizar "Todas las violaciones, en orden estable" y el docstring de `validate_new_appointment`. |
| 3 | ¿Un bloqueo con `inicio >= fin` es una violación o un error de programación? | Violación. `Block` no valida el orden al construirse; `validate_block(block) -> list[Violation]` devuelve `INVALID_BLOCK`. Un instante naive sí es `ValueError` (vía `_to_utc`). `validate_new_appointment` no revalida los bloqueos. | El bloqueo lo carga el usuario por `POST /blocks` y US-011 CA-2 es un criterio de negocio: resultado tipado, `422` en la API. Validar en el constructor haría imposible construir el bloqueo que la función tiene que rechazar. `INVALID_BLOCK` se suma a KB 07. La KB no pide grilla de 5 minutos ni prohíbe bloqueos que se pisan entre sí: no se agregan esas reglas (confirmado por la autora). |
| 4 | ¿Se comparan en instantes UTC o en hora local? | En instantes UTC, con `overlaps(Interval, Interval)`. La hora local se usa solo para el mensaje. | El bloqueo es un intervalo de instantes (`timestamptz`, KB 04). Pasar de UTC a hora local conserva el orden, así que solaparse en UTC es solaparse en hora local. Un bloqueo de varios días no necesita tratamiento especial, y la regla no depende de `tz`. |
| 5 | ¿Qué pasa si un turno pisa varios bloqueos? | Una `BLOCKED_TIME` por bloqueo, ordenadas por `(start_at, str(id))`, con el id en el campo nuevo `Violation.conflicting_block_id: UUID | None = None`. | Es el patrón de `PROFESSIONAL_OVERLAP`: cada violación lleva un id y el orden no depende de la lista recibida. El mensaje da el rango del turno y el del bloqueo en hora local con fecha (puede durar varios días) y el motivo si existe; el texto final sigue a cargo de C-08. |
| 6 | ¿Cómo devuelve RN-DI-04 los turnos afectados? | `appointments_affected_by_block(block, appointments) -> list[Appointment]`: mismo profesional, estado que ocupa agenda (`OCCUPYING_STATUSES`) y solapamiento, ordenados por `(start_at, str(id))`. Devuelve los mismos objetos, sin modificarlos. | La respuesta de la API tiene que mostrar los turnos para reprogramarlos (Flujo 4); con solo los ids habría que buscarlos de nuevo. Es pura, así que "no cancela ni mueve" se cumple solo. El borde compone `validate_block` y después esta función. |
| 7 | ¿Se confirma Q-04 / SU-05? | Sí: crear un bloqueo no cancela ni mueve los turnos que pisa; solo los lista. | Confirmado por la autora el 2026-10-28. Se baja la "Suposición" en KB 05, 09 y 10. |

## Pedidos para el propose

- `model.py`: `Block` (id, profesional, `start_at`, `end_at`, `reason: str | None`), con instantes normalizados a UTC y sin validar el orden; el campo `blocks` en `ScheduleContext`.
- `violations.py`: `BLOCKED_TIME` e `INVALID_BLOCK` en `ViolationCode`; `conflicting_block_id` en `Violation`.
- `rules/blocks.py`: `check_blocks`, `validate_block` y `appointments_affected_by_block`.
- `appointment/validate.py`: cableado de `check_blocks` entre el horario y el solapamiento del profesional.
- Tests (P1 con semana completa salvo que se indique otra cosa; B1 = P1, martes 20/10 de 10:00 a 12:00 local = 13:00 a 15:00 UTC):
  - `BLOCKED_TIME`: 10:30–11:00 rechazado; 09:30–10:00 y 12:00–12:30 válidos (bordes); 09:45–10:15 y 11:45–12:15 rechazados; bloqueo de P2 no afecta.
  - Varios días (BV = lunes 19 00:00 a lunes 26 00:00 local = 19 03:00 a 26 03:00 UTC): martes 20 10:00–10:30 rechazado; domingo 25 23:30–23:55 (lunes 26 02:30–02:55 UTC) rechazado; lunes 26 00:00–00:30 válido; domingo 18 23:30–00:00 válido.
  - Varios bloqueos (B2 = 11:00–13:00 local): 11:30–12:30 da B1 y B2, en el mismo orden aunque lleguen invertidos.
  - Orden del grupo 2 (horario → bloqueo → profesional → sillón) y grupo 1 que corta antes del bloqueo.
  - `validate_block`: válido, inicio = fin, inicio > fin, bloqueo de 1 minuto válido, normalización a UTC, instante naive → `ValueError`.
  - Turnos afectados: de siete turnos (bordes, cancelado, ausente, otro profesional) solo quedan B y C, en orden, sin cambiar su estado; sin solapamientos → vacía.
- En la spec, agregar los requisitos de bloqueos, validez del bloqueo y turnos afectados, y actualizar "Alta de un turno válido" y "Todas las violaciones, en orden estable".
