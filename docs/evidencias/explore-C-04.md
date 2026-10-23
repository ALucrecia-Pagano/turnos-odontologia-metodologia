# Explore de C-04 hora-local-y-turno-en-un-dia

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-23 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02 y C-03 ya estaban archivados. `validate_new_appointment(request, references, existing_appointments)` evalúa en dos grupos. El grupo 1, validez del pedido, tiene referencias y duración, informadas todas juntas; si hay alguna violación, corta ahí. El grupo 2, conflictos de agenda, tiene los solapamientos por profesional y por sillón.
- `intervals.py` tenía solo el `Interval` semiabierto y `overlaps`, sin nada de hora local. `NewAppointmentRequest` ya rechaza un `start_at` sin zona (*naive*) y lo normaliza a UTC.
- La granularidad de 5 minutos vivía como `DURATION_STEP_MIN` en `rules/duration.py` y solo se usaba para la duración.
- La guardia de dependencias ya permite `zoneinfo` y `tzdata`, y `tzdata` está en `pyproject.toml`. En el `.venv`, `zoneinfo` resuelve `America/Argentina/Buenos_Aires` (02:30 UTC del 20/10 da 19/10 23:30 local).
- El catálogo de KB 07 no tiene código ni para el cruce de medianoche ni para el inicio fuera de la grilla: faltan dos códigos, no uno, como decía `CHANGES.md`.
- Los tests existentes usan inicios de 13:00 UTC (10:00 local), en la grilla y lejos de la medianoche, así que las reglas nuevas no rompen ninguno. Solo cambia la firma (decisión 3).
- No había changes activos. La spec `appointment-scheduling` tiene 12 requisitos.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿Qué código usa el turno que cruza la medianoche local? | `CROSSES_MIDNIGHT`, un código propio. | No es un problema de un solo campo, sino del intervalo que forman el inicio y la duración. Reusar `OUTSIDE_WORKING_HOURS` mezclaría dos reglas y depende de C-05, que todavía no existe. |
| 2 | ¿Qué código usa el inicio fuera de la grilla de 5 minutos? | `INVALID_START_TIME`, con una sola violación aunque fallen los minutos y los segundos. | Es el paralelo de `INVALID_DURATION`: el código describe el campo, no cada subregla (como la decisión 5 de C-03). |
| 3 | ¿Cómo recibe el dominio la zona horaria? | Con un `ScheduleContext` que por ahora tiene solo `tz: ZoneInfo`. C-05 a C-07 le suman lo suyo (horarios, bloqueos, `now`). | La firma cambia una sola vez y no en cada change. El texto de `APP_TIMEZONE` se convierte en `ZoneInfo` en el borde: el dominio no lee variables de entorno ni fija la zona. |
| 4 | ¿En qué grupo van las reglas nuevas y en qué orden? | En el grupo 1, en este orden: referencias → duración → inicio → medianoche. La medianoche solo se evalúa si la duración es válida. | Ninguna de las dos depende de la agenda: son reglas de validez del pedido (`422`), no conflictos (`409`). Con una duración inválida, decir "cruza la medianoche" es ruido sobre un valor que ya está mal. |
| 5 | ¿Un turno que termina justo a las 00:00 cruza la medianoche? | No: es válido y tiene su propio escenario. | El intervalo `[23:30, 00:00)` es semiabierto (DD-07) y no ocupa nada del día siguiente. En minutos locales, el fin vale 1440, lo que encaja con los tramos de C-05. |
| 6 | ¿Dónde vive la granularidad de 5 minutos? | En una sola constante, compartida por la duración y el inicio. | SU-02 habla de "constante configurable", en singular: si la granularidad cambia, cambia en un solo lugar para las dos reglas. |
| 7 | ¿Hace falta un test con otra zona para probar que la grilla se evalúa en hora local? | No: se testea solo con `America/Argentina/Buenos_Aires`. | Todas las zonas actuales tienen offsets múltiplos de 15 minutos (incluso +05:30 o +05:45), así que para la grilla de 5 minutos UTC y hora local dan siempre lo mismo, y un test con otra zona no demuestra nada. La hora local sí importa para la medianoche, y eso ya lo cubre el test del instante UTC que en hora local cae en otro día. |

## Pedidos para el propose

- `intervals.py`: conversión de un instante UTC a día local y minutos desde las 00:00 con la zona recibida, y formateo `HH:MM` de la hora local para los mensajes. Los mensajes completos con nombres siguen siendo de C-08.
- Agregar `CROSSES_MIDNIGHT` e `INVALID_START_TIME` a `ViolationCode` y al catálogo de códigos de KB 07.
- Tests: el instante UTC que en hora local cae en otro día; 23:30–00:30 rechazado; 23:00–23:55 válido; 23:30–00:00 válido; inicio 10:03 rechazado; 10:05 válido; inicio con segundos rechazado; duración inválida que cruzaría la medianoche (solo `INVALID_DURATION`).
- En la spec, agregar los requisitos de medianoche y de inicio en la grilla, y actualizar "Todas las violaciones, en orden estable" con el orden del grupo 1.
