# Proposal

## Why

Después de C-06, el dominio acepta un turno con inicio en el pasado: no conoce el instante actual. US-005 (CA-1 a CA-3) y RN-AG-06 piden rechazar todo turno que empiece antes de `now` con el código `IN_THE_PAST`, y aceptar el que empieza exactamente en `now` o después. US-005 CA-4 y RN-GL-04 piden que ese `now` se inyecte: ninguna regla puede leer el reloj del sistema, y eso tiene que quedar verificado por un test, no solo por convención.

Este change va ahora porque C-08 (mensajes completos) necesita todas las reglas del pedido y de la agenda, y la base ya está: `ScheduleContext` recibe la zona, los tramos y los bloqueos, y su docstring anuncia `now` desde C-04. Depende de C-02. Las decisiones salen del explore del 2026-10-29 (`docs/evidencias/explore-C-07.md`), confirmadas por la autora.

## What Changes

- **Turno que no empieza en el pasado** (RN-AG-06; US-005 CA-1 a CA-3): si el inicio del turno es anterior a `now`, código nuevo `IN_THE_PAST`. La comparación es estricta entre instantes: un inicio igual a `now` es válido, sin truncar `now` ni dar tolerancia (con `now` a las 10:00:30, un inicio a las 10:00 se rechaza).
- **Grupo de la regla**: `IN_THE_PAST` va **al final del grupo 1** (validez del pedido), después de la medianoche, y se evalúa siempre, porque solo necesita el inicio y `now`. El orden del grupo 1 queda referencias → duración → inicio en la grilla → medianoche → pasado (RN-AG-12). Como el grupo 1 corta, un turno en el pasado no informa horario, bloqueos ni solapamientos. En la API será `422` (KB 07 ya lo dice).
- **`now` en el contexto**: `ScheduleContext` suma `now: datetime`, **sin valor por defecto**, y lo normaliza a UTC al construirse; un `now` sin zona es `ValueError` (error de programación). **BREAKING** (solo interno): construir el contexto exige `now`; los helpers de contexto de los tests pasan un `now` fijo del 2026-10-01 a las 00:00 UTC, anterior a todas sus fechas, y ningún test existente cambia lo que verifica.
- **Mensaje de `IN_THE_PAST`**: el inicio del turno con fecha (`dd/mm/aaaa HH:MM`) y el momento actual con fecha y segundos (`dd/mm/aaaa HH:MM:SS`), ambos en hora local, para que nunca diga "10:00 es anterior a 10:00". Los mensajes con nombres siguen en C-08.
- **Guardia del reloj global** (RN-GL-04; US-005 CA-4): una verificación con `ast`, nueva y separada de la guardia de imports de C-01, reporta todo acceso a `now`, `utcnow` o `today` de la clase `datetime` y a `today` de la clase `date`, también por el módulo (`datetime.datetime.now`) y con alias, aunque no se llame; `from datetime import *` también se reporta. `time.time` ya lo cubre la lista de permitidos de C-01 (`time` no está). Un test la aplica al `app/domain` real.

### Fuera de alcance

- Reprogramar un turno a un inicio en el pasado (RN-AG-06 lo menciona) → C-11 reutiliza esta regla.
- Leer el reloj real en el borde (la API construye `now` con la hora del servidor) → C-22.
- Mensajes completos con nombres → C-08.
- Detección dinámica del reloj (`getattr(datetime, "now")`, reasignaciones como `d = datetime; d.now()`): límite documentado de la guardia.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-scheduling`: se agregan los requisitos de turno que no empieza en el pasado, mensaje de un turno en el pasado y momento actual inyectado en el contexto; el alta de un turno válido exige que el inicio no sea anterior a `now`; "Todas las violaciones, en orden estable" suma `IN_THE_PAST` al final del grupo 1, evaluado siempre; "Contenido de cada violación" deja fuera de su formato de horas el momento actual del mensaje de `IN_THE_PAST`, que siempre lleva segundos.
- `domain-dependency-guard`: se agrega el requisito de que el dominio no lea el reloj global, con su verificación sobre el dominio real y sus límites documentados.

## Impact

- **Código modificado** en `backend/app/domain/`: `model.py` (`ScheduleContext.now` y su `__post_init__`), `violations.py` (`IN_THE_PAST`), `intervals.py` (formato de fecha y hora local con segundos para el mensaje) y `appointment/validate.py` (la regla al final del grupo 1 y los docstrings de los dos grupos).
- **Código nuevo**: `backend/app/domain/rules/past.py` (`check_not_in_the_past`).
- **Tests**: `backend/tests/domain/import_guard.py` (`find_global_clock_calls` y su formato), `test_clock_guard.py` (nuevo), `test_domain_dependencies.py` (dominio real sin reloj global), `test_past.py` (nuevo), `test_validate_new_appointment.py` (escenarios nuevos; `CTX`, `_ctx` y `_ctx_blocks` con `now`), `test_model.py`, `test_violations.py` y `test_intervals.py`.
- **Documentación**: `backend/README.md` (ejemplo con `now`, módulos y orden del grupo 1) y evidencias en `docs/evidencias/`. `knowledge-base/07` ya se actualizó después del explore (`IN_THE_PAST → 422`).
- **Dependencias**: ninguna nueva (sin `freezegun`); la allowlist del dominio no cambia.
- **Governance**: MEDIO. Hay un punto de control antes de implementar la regla: la autora revisa `ScheduleContext.now`, la migración de los helpers de los tests, la guardia del reloj y los tests en rojo de `rules/past.py` y de `validate_new_appointment`.
