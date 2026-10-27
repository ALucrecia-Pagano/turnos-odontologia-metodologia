# Explore de C-05 horario-de-atencion

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-26 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02, C-03 y C-04 ya estaban archivados. `validate_new_appointment(request, references, existing_appointments, context)` evalúa en dos grupos. El grupo 1, validez del pedido, tiene referencias → duración → inicio en la grilla → medianoche; si hay alguna violación, corta ahí. El grupo 2, conflictos de agenda, tiene los solapamientos por profesional y por sillón.
- `ScheduleContext` tenía solo `tz: ZoneInfo`, sin valor por defecto, y su docstring ya anunciaba que C-05 a C-07 le suman horarios, bloqueos y `now`.
- `intervals.py` ya tenía `local_day_and_minutes` y `format_local_time`. El día de la semana sale de `date.isoweekday()`, la misma convención ISO de KB 04 (1 = lunes … 7 = domingo).
- No existía nada de `WorkingHours`: ni el modelo, ni `rules/working_hours.py`, ni `OUTSIDE_WORKING_HOURS` en `ViolationCode` (sí en el catálogo de KB 07). El catálogo tampoco tiene códigos para un conjunto de tramos inválido (RN-DI-02).
- Las 27 llamadas de `test_validate_new_appointment.py` usan `CTX = ScheduleContext(tz=BUENOS_AIRES)` con fechas del martes 2026-10-20. Las que hoy dan `Ok` (incluidas las de medianoche, a las 23:xx locales) pasarían a dar `OUTSIDE_WORKING_HOURS` si el contexto no trae tramos.
- En el `.venv`, `zoneinfo` confirma que el 2026-10-20 es martes (ISO 2) y el 2026-10-25 domingo (ISO 7), y que `2026-10-21T01:00:00+00:00` es el martes 20 a las 22:00 locales.
- No había changes activos. La spec `appointment-scheduling` tiene 15 requisitos.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿Cómo llegan los horarios al dominio? | En `ScheduleContext.working_hours: tuple[WorkingHours, ...]`, sin valor por defecto. El dominio filtra por el profesional del pedido y por el día de la semana local. | La firma cambia una sola vez (decisión 3 de C-04). Es el mismo criterio que "El dominio filtra los turnos que recibe": el resultado no depende de que el llamador haya filtrado. Sin default, ningún llamador se olvida de pasarlos. |
| 2 | ¿En qué grupo va la regla y en qué orden? | En el grupo 2, primera: horario → (bloqueo, C-06) → profesional → sillón. Se informa junto con los solapamientos. | En el grupo 2 la duración es válida, el inicio está en la grilla y el turno cabe en un día, así que la regla no necesita guardas. Es una pregunta sobre la agenda del profesional, como el solapamiento. Respeta el orden de RN-AG-12. Hay que actualizar el texto de "Todas las violaciones, en orden estable". |
| 3 | ¿Qué pasa con un turno que empieza en un tramo y termina en otro? | Con hueco entre tramos (9–13 y 15–19), 12:30–13:30 se rechaza. Los tramos contiguos (9–13 y 13–17) se fusionan antes de evaluar y cuentan como uno: 12:30–13:30 es válido. | RN-AG-04 pide caer completo dentro de un tramo; con tramos contiguos no hay ningún hueco y rechazar sería sorprendente. Se actualiza RN-AG-04 en KB 05. |
| 4 | ¿Cómo se rechaza un conjunto de tramos inválido? | `WorkingHours` es una dataclass sin reglas de negocio y `validate_working_hours(slots) -> list[Violation]` devuelve `INVALID_WORKING_HOURS` (uno por tramo con `inicio >= fin`, minutos fuera de `0..1440` o día fuera de `1..7`) y `OVERLAPPING_WORKING_HOURS` (uno por par de tramos del mismo día que se solapan). | Los tramos los carga el usuario por el `PUT`: es una regla de negocio y va como resultado tipado, no como `ValueError`. Devuelve `list[Violation]` porque `Ok` está atado a `Appointment`. Los dos códigos se suman a KB 07. `validate_new_appointment` no revalida los tramos que recibe. |
| 5 | ¿Qué dice el mensaje de `OUTSIDE_WORKING_HOURS`? | La hora local del turno y los tramos del día ("…el martes atiende de 09:00 a 13:00 y de 15:00 a 19:00"), o que no atiende ese día ("…no atiende los domingos"). | Explica el rechazo sin esperar a C-08, que sigue a cargo de los mensajes completos con nombres. |
| 6 | ¿Cómo sobreviven los tests existentes? | `CTX` de los tests con tramos de día completo `[0, 1440)` los 7 días para los profesionales de los tests. | Un solo cambio de línea; el tramo hasta 1440 deja pasar el turno de 23:30 a 00:00. |

## Pedidos para el propose

- `model.py`: `WorkingHours` (profesional, día ISO, `start_minute`, `end_minute`) y el campo `working_hours` en `ScheduleContext`.
- `rules/working_hours.py`: `OUTSIDE_WORKING_HOURS` con fusión de tramos contiguos y `validate_working_hours`. El minuto del fin se calcula convirtiendo `end_at` a hora local, con 00:00 del día siguiente = 1440.
- Agregar `OUTSIDE_WORKING_HOURS`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` a `ViolationCode`, y los dos últimos al catálogo de KB 07.
- Tests (P1 atiende el martes `[540, 780)` y `[900, 1140)`; hora local = UTC−3): 10:00–10:30 válido; bordes 09:00, fin 13:00 y fin 19:00 válidos; 12:30–13:30 rechazado; 08:30–09:30 rechazado; 13:00–15:00 y 14:00–14:30 rechazados; 12:30–15:30 rechazado; domingo rechazado; 06:00 local (09:00 UTC) rechazado; 18:00 local (21:00 UTC) válido; día de la semana local (martes 22:00 = miércoles 01:00 UTC); fin a las 00:00 = 1440 válido; tramo de otro profesional no cuenta; contiguos 9–13 y 13–17 con 12:30–13:30 válido; orden horario → profesional → sillón; grupo 1 corta antes del horario. Para los tramos: conjunto válido, `inicio >= fin`, solapados, mismos tramos en días distintos, contiguos válidos, límite 1440 y rangos fuera de límite.
- En la spec, agregar los requisitos de horario de atención y de validez de los tramos, y actualizar "Alta de un turno válido" y "Todas las violaciones, en orden estable".
