# Proposal

## Why

Después de C-04, el dominio sabe qué hora es en el consultorio, pero todavía no sabe cuándo atiende cada profesional: acepta un turno un domingo, a las 06:00 o en el hueco del mediodía entre dos tramos. US-004 (CA-1 a CA-3, CA-6 y CA-7) y RN-AG-04 piden rechazar todo turno que no caiga **completo** dentro de un tramo del horario de atención del profesional, evaluado en hora local (`America/Argentina/Buenos_Aires`, SU-01, RN-GL-03). Además, los tramos los carga el usuario (US-010), así que el dominio tiene que poder decir si un conjunto de tramos es válido (RN-DI-01, RN-DI-02) antes de que C-16 y C-21 los guarden.

Este change va ahora porque está en el camino crítico (C-04 → C-05 → C-08) y C-04 ya dejó la base: `ScheduleContext`, la zona recibida por parámetro y la conversión a día local y minutos (`local_day_and_minutes`). Depende de C-04. Las decisiones salen del explore del 2026-10-26 (`docs/evidencias/explore-C-05.md`).

## What Changes

- **Turno dentro del horario de atención** (RN-AG-04; US-004 CA-1, CA-2, CA-3, CA-6 y CA-7): el turno se acepta solo si, en hora local, cae completo dentro de un tramo del profesional del pedido para el día de la semana local del turno. Si no, código nuevo `OUTSIDE_WORKING_HOURS`, sin id de turno en conflicto. Un turno que termina justo cuando termina el tramo es válido (intervalo semiabierto, DD-07), y un turno que termina a las 00:00 locales tiene su fin en el minuto 1440.
- **Tramos contiguos**: los tramos del mismo profesional y día que se tocan (uno termina justo donde empieza el otro, 09:00–13:00 y 13:00–17:00) cuentan como uno solo: 12:30–13:30 es válido. Con un hueco (09:00–13:00 y 15:00–19:00) se rechaza (RN-AG-04, ya actualizada en KB 05).
- **Horarios en el contexto**: `ScheduleContext` suma `working_hours`, la lista de tramos, **sin valor por defecto**. El dominio filtra por sí mismo los tramos del profesional del pedido y del día local, igual que filtra los turnos existentes. **BREAKING** (solo interno): construir el contexto exige los tramos; el `CTX` de los tests pasa a tener tramos de día completo los 7 días para P1 y P2, y ningún test existente cambia lo que verifica.
- **Modelo `WorkingHours`** (profesional, día de la semana ISO 1 = lunes … 7 = domingo, `start_minute`, `end_minute` en minutos locales), sin reglas de negocio al construirse.
- **Validez de un conjunto de tramos** (RN-DI-01, RN-DI-02; US-010 CA-1 y CA-2): una función de dominio devuelve la lista de violaciones de un conjunto de tramos, con dos códigos nuevos: `INVALID_WORKING_HOURS` (un tramo con `inicio >= fin`, minutos fuera de `0..1440` o día fuera de `1..7`) y `OVERLAPPING_WORKING_HOURS` (dos tramos del mismo profesional y día que se solapan). Varios tramos por día y tramos contiguos son válidos. `validate_new_appointment` no revalida los tramos que recibe.
- **Orden de las violaciones**: la regla de horario va en el grupo 2, que pasa a llamarse "conflictos de agenda" y no solo "solapamientos", y va **primera**: horario → (bloqueo, C-06) → profesional → sillón (RN-AG-12). Se informa junto con los solapamientos. El grupo 1 (validez del pedido) sigue cortando antes: un turno de 7 minutos un domingo da solo `INVALID_DURATION`.
- **Mensaje de `OUTSIDE_WORKING_HOURS`**: la hora local del turno y los tramos de ese día ("…el martes atiende de 09:00 a 13:00 y de 15:00 a 19:00."), o que el profesional no atiende ese día ("…no atiende los domingos."). Los mensajes con nombres siguen en C-08.

### Fuera de alcance

- Persistencia de los tramos y su constraint en PostgreSQL → C-16. Endpoint `PUT` del horario → C-21.
- US-010 CA-3 (cambiar el horario no altera turnos ya dados e informa cuáles quedan fuera) → C-21; acá solo se valida el conjunto de tramos.
- Bloqueos (`BLOCKED_TIME`, US-004 CA-4 y CA-5) → C-06. Turnos en el pasado → C-07.
- Mensajes completos con nombres del profesional → C-08.
- Feriados y excepciones por fecha: el horario es semanal (RN-DI-01).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: se agregan los requisitos de turno dentro del horario de atención y de validez de un conjunto de tramos; el alta de un turno válido exige caer completo dentro del horario; "Todas las violaciones, en orden estable" pasa a tener un grupo 2 de conflictos de agenda con el horario primero, antes de los solapamientos.

## Impact

- **Código modificado** en `backend/app/domain/`: `model.py` (`WorkingHours` y `ScheduleContext.working_hours`), `violations.py` (`OUTSIDE_WORKING_HOURS`, `INVALID_WORKING_HOURS`, `OVERLAPPING_WORKING_HOURS`) y `appointment/validate.py` (la regla primera en el grupo 2).
- **Código nuevo**: `backend/app/domain/rules/working_hours.py` (regla del horario y validez de los tramos).
- **Tests**: `backend/tests/domain/test_validate_new_appointment.py` (escenarios nuevos y `CTX` con tramos de día completo), `test_working_hours.py` (nuevo, validez de los tramos), `test_violations.py` y `test_model.py`.
- **Documentación**: `backend/README.md` (módulos, orden de los grupos y ejemplo con los tramos) y evidencias en `docs/evidencias/`. `knowledge-base/05_reglas_de_negocio.md` (RN-AG-04, tramos contiguos), `knowledge-base/07_flujos_principales.md` (los dos códigos de tramos) y `CHANGES.md` §[C-05] ya se actualizaron después del explore.
- **Dependencias**: ninguna nueva; la allowlist del dominio no cambia.
- **Governance**: MEDIO. Hay un punto de control antes de implementar las reglas: la autora revisa `WorkingHours`, `ScheduleContext`, los códigos nuevos y la migración del `CTX` de los tests.
