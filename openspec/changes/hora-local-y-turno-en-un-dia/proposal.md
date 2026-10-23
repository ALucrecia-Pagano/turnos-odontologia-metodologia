# Proposal

## Why

Después de C-02 y C-03, el dominio valida las referencias, la duración y los solapamientos, pero todavía no sabe qué hora es en el consultorio: trabaja solo con instantes UTC. Por eso acepta un turno de 23:30 a 00:30 hora local, que cruza la medianoche (RN-AG-10, SU-09, US-007 CA-3), y un inicio a las 10:03 o a las 10:05:30, fuera de la grilla de 5 minutos (RN-DI-05 en la parte del inicio, SU-02, que C-03 dejó para este change).

Las dos reglas se evalúan en hora local (`America/Argentina/Buenos_Aires`, SU-01, RN-GL-03), y para eso el dominio tiene que recibir la zona horaria. Este change suma esa base ahora porque C-05 (horario de atención) la necesita para comparar el turno con los tramos en minutos locales, y C-06 y C-07 van a sumar más contexto (bloqueos, `now`) sobre la misma firma.

Depende de C-02 (intervalos, resultado tipado y `validate_new_appointment`) y se apoya en C-03 (los dos grupos de violaciones y la regla de duración). Las decisiones salen del explore del 2026-10-23 (`docs/evidencias/explore-C-04.md`).

## What Changes

- **Turno dentro de un solo día local** (RN-AG-10, SU-09, US-007 CA-3): un turno cuyo inicio y fin caen en días locales distintos se rechaza con un código nuevo, `CROSSES_MIDNIGHT`. Un turno que termina justo a las 00:00 locales **no** cruza la medianoche: el intervalo es semiabierto (DD-07) y es válido.
- **Inicio en la grilla de 5 minutos** (RN-DI-05 en la parte del inicio, SU-02): en hora local, los minutos del inicio tienen que ser múltiplo de 5 y los segundos y microsegundos, cero. Si no, código nuevo `INVALID_START_TIME`, con **una sola** violación aunque fallen los minutos y los segundos a la vez.
- **Una sola granularidad**: la duración y el inicio usan la misma constante de 5 minutos (SU-02, "constante configurable").
- **Contexto de agenda**: `validate_new_appointment` recibe un contexto nuevo que por ahora tiene solo la zona horaria (`ZoneInfo`). C-05 a C-07 le suman horarios, bloqueos y `now`. El texto de `APP_TIMEZONE` se convierte en `ZoneInfo` en el borde: el dominio no lee variables de entorno ni fija la zona. **BREAKING** (solo interno): cambia la firma; los tests de C-02 y C-03 se adaptan en la llamada sin cambiar lo que verifican.
- **Hora local en `intervals.py`**: conversión de un instante UTC a día local y minutos desde las 00:00 con la zona recibida, y formateo de la hora local para los mensajes (`HH:MM`, o `HH:MM:SS` si la hora tiene segundos).
- **Orden del grupo 1** (validez del pedido, `422`): referencias → duración → inicio → medianoche. La medianoche solo se evalúa si hay una duración efectiva válida. Las dos reglas nuevas no dependen de la agenda, así que no son conflictos (`409`).
- **Catálogo de códigos** de KB 07: se suman `CROSSES_MIDNIGHT` e `INVALID_START_TIME`.
- **RN-AG-12** de KB 05: el orden de prioridad suma el inicio y la medianoche después de la duración (referencias → duración → inicio → medianoche → …).

### Fuera de alcance

- Horario laboral en minutos locales (`OUTSIDE_WORKING_HOURS`) → C-05, que reusa la conversión de este change.
- Bloqueos (C-06) y turnos en el pasado (C-07): suman sus campos al contexto en su propio change.
- Mensajes completos con nombres de profesional, sillón o prestación → C-08. Acá los mensajes nuevos solo muestran la hora local.
- Lectura de `APP_TIMEZONE` y armado del contexto en la API → C-22 / C-23.
- Tests con otras zonas horarias (decisión 7 del explore): para la grilla de 5 minutos no prueban nada, porque todos los offsets vigentes son múltiplos de 15 minutos.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: se agregan los requisitos de turno dentro de un solo día local, inicio en la grilla de 5 minutos y evaluación en la zona horaria recibida; el alta de un turno válido exige las dos reglas nuevas; el orden del grupo 1 pasa a referencias → duración → inicio → medianoche; el contenido de cada violación define los mensajes de los dos códigos nuevos.

## Impact

- **Código modificado** en `backend/app/domain/`: `intervals.py` (hora local y formateo), `model.py` (`ScheduleContext`), `violations.py` (`CROSSES_MIDNIGHT`, `INVALID_START_TIME`), `rules/duration.py` (usa la constante compartida), `appointment/validate.py` (firma nueva y orden del grupo 1).
- **Código nuevo**: `backend/app/domain/rules/grid.py` (granularidad), `rules/start_time.py` (inicio en la grilla) y `rules/same_day.py` (medianoche).
- **Tests**: `backend/tests/domain/test_validate_new_appointment.py` (escenarios nuevos y adaptación de la llamada), `test_intervals.py` y `test_violations.py`.
- **Documentación**: `backend/README.md` (módulos y ejemplo con la firma nueva), `knowledge-base/07_flujos_principales.md` (catálogo de códigos) y `knowledge-base/05_reglas_de_negocio.md` (orden de RN-AG-12), los dos ya actualizados en este propose, y evidencias en `docs/evidencias/`.
- **Dependencias**: ninguna nueva. `zoneinfo` y `tzdata` ya están en la allowlist del dominio y `tzdata` ya está en `pyproject.toml`.
- **Governance**: MEDIO. Hay un punto de control antes de implementar las reglas: la autora revisa `ScheduleContext`, los códigos nuevos y la firma.
