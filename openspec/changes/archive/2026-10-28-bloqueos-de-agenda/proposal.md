# Proposal

## Why

Después de C-05, el dominio sabe cuándo atiende cada profesional por semana, pero no conoce las excepciones: acepta un turno en medio de unas vacaciones, un feriado o una ausencia cargada como bloqueo. US-004 (CA-4 y CA-5) y RN-AG-05 piden rechazar todo turno que se superponga con un bloqueo del profesional, con el id del bloqueo. Además, los bloqueos los carga el usuario (US-011), así que el dominio tiene que decir si un bloqueo es válido (RN-DI-03) y qué turnos ya dados pisa, sin cancelarlos ni moverlos (RN-DI-04, SU-05, confirmada por la autora el 2026-10-28).

Este change va ahora porque C-08 (mensajes completos) necesita todas las reglas del grupo 2, y la base ya está: `ScheduleContext` recibe la agenda del profesional y el grupo 2 informa los conflictos todos juntos. Depende de C-02. Las decisiones salen del explore del 2026-10-28 (`docs/evidencias/explore-C-06.md`).

## What Changes

- **Turno fuera de los bloqueos** (RN-AG-05; US-004 CA-4 y CA-5): si el turno nuevo se superpone con un bloqueo del profesional del pedido, código nuevo `BLOCKED_TIME` con el id del bloqueo, una violación por bloqueo, ordenadas por el inicio del bloqueo. Un turno que termina justo cuando empieza el bloqueo, o que empieza justo cuando termina, es válido (intervalo semiabierto, DD-07). Los bloqueos de otro profesional no cuentan. La comparación es entre instantes, así que un bloqueo puede durar varios días sin ningún tratamiento especial.
- **Bloqueos en el contexto**: `ScheduleContext` suma `blocks`, la lista de bloqueos, **sin valor por defecto**. El dominio filtra por sí mismo los del profesional del pedido. **BREAKING** (solo interno): construir el contexto exige los bloqueos; el `CTX` de los tests y el helper `_ctx` pasan `blocks=()`, y ningún test existente cambia lo que verifica.
- **Modelo `Block`** (id, profesional, `start_at`, `end_at` con zona y normalizados a UTC, motivo opcional). Un instante sin zona es `ValueError` (error de programación), pero `inicio >= fin` no se valida al construirse.
- **Validez de un bloqueo** (RN-DI-03; US-011 CA-1 y CA-2): una función de dominio devuelve las violaciones de un bloqueo, con el código nuevo `INVALID_BLOCK` si `inicio >= fin`. No se exige la grilla de 5 minutos ni se prohíben bloqueos que se pisan entre sí (confirmado por la autora). `validate_new_appointment` no revalida los bloqueos que recibe.
- **Turnos afectados por un bloqueo** (RN-DI-04; US-011 CA-3): una función de dominio devuelve, dado un bloqueo, los turnos existentes del mismo profesional que ocupan agenda (`reservado`, `confirmado`, `atendido`) y se solapan con él, ordenados por inicio y sin modificarlos.
- **Id del bloqueo en la violación**: `Violation` suma `conflicting_block_id`, `None` salvo en `BLOCKED_TIME`.
- **Orden de las violaciones**: `BLOCKED_TIME` va en el grupo 2, entre el horario y los solapamientos: horario → bloqueo → profesional → sillón (RN-AG-12), todo junto. El grupo 1 sigue cortando antes.
- **Mensaje de `BLOCKED_TIME`**: el turno y el bloqueo en hora local, el bloqueo con fecha (puede durar varios días), el motivo si lo hay y el id del bloqueo. Los mensajes con nombres siguen en C-08.

### Fuera de alcance

- Persistencia de los bloqueos y su constraint en PostgreSQL → C-16. Endpoints `GET/POST /professionals/:id/blocks` y `DELETE /blocks/:id` → C-21; US-011 CA-4 (eliminar un bloqueo libera el horario) se cubre acá solo como "sin el bloqueo en el contexto, el turno es válido".
- Turnos en el pasado → C-07. Mensajes completos con nombres → C-08.
- Bloqueos por sillón o de todo el consultorio: el bloqueo es por profesional (RN-DI-03).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: se agregan los requisitos de turno fuera de los bloqueos del profesional, mensaje de un turno bloqueado, validez de un bloqueo y turnos afectados por un bloqueo; el alta de un turno válido exige no pisar ningún bloqueo; "Todas las violaciones, en orden estable" suma `BLOCKED_TIME` entre el horario y los solapamientos.

## Impact

- **Código modificado** en `backend/app/domain/`: `model.py` (`Block` y `ScheduleContext.blocks`), `violations.py` (`BLOCKED_TIME`, `INVALID_BLOCK` y `Violation.conflicting_block_id`), `intervals.py` (formato de fecha y hora local para el mensaje) y `appointment/validate.py` (la regla en el grupo 2, después del horario).
- **Código nuevo**: `backend/app/domain/rules/blocks.py` (regla del bloqueo, validez del bloqueo y turnos afectados).
- **Tests**: `backend/tests/domain/test_validate_new_appointment.py` (escenarios nuevos; `CTX` y `_ctx` con `blocks=()`), `test_blocks.py` (nuevo: validez del bloqueo y turnos afectados), `test_violations.py`, `test_model.py` y `test_intervals.py`.
- **Documentación**: `backend/README.md` (módulos, orden del grupo 2 y ejemplo con `blocks`) y evidencias en `docs/evidencias/`. `knowledge-base/05`, `07`, `09` y `10` ya se actualizaron después del explore (SU-05 confirmada, `INVALID_BLOCK` en el catálogo).
- **Dependencias**: ninguna nueva; la allowlist del dominio no cambia.
- **Governance**: MEDIO. Hay un punto de control antes de implementar las reglas: la autora revisa `Block`, `ScheduleContext.blocks`, los códigos nuevos, `conflicting_block_id`, las firmas de `rules/blocks.py` y la migración del `CTX` de los tests.
