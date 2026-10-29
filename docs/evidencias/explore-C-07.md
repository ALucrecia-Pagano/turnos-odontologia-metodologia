# Explore de C-07 no-turnos-en-el-pasado

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-29 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02 a C-06 ya estaban archivados. `validate_new_appointment(request, references, existing_appointments, context)` evalúa en dos grupos. El grupo 1, validez del pedido, tiene referencias → duración → inicio en la grilla → medianoche; si hay alguna violación, corta ahí. El grupo 2, conflictos de agenda, tiene horario → bloqueo → profesional → sillón, todo junto. RN-AG-12 pone "pasado" justo entre la medianoche y el horario, es decir, en el borde entre los dos grupos; los docstrings de los dos grupos dejaban abierto dónde iba.
- `ScheduleContext` tenía `tz`, `working_hours` y `blocks`, sin valores por defecto ni `__post_init__`, y su docstring ya anunciaba que C-07 suma `now` sin cambiar la firma (decisión 3 de C-04).
- Se puede reusar `_to_utc` de `model.py` (normaliza a UTC y rechaza instantes naive) y `format_local_date_time` de `intervals.py` para el mensaje.
- No existía `IN_THE_PAST` en `ViolationCode` (sí en el catálogo de KB 07). KB 07 asignaba `409` a horario y solapamientos y `422` a la validez del pedido, sin decir nada del pasado.
- La guardia de C-01 (`tests/domain/import_guard.py`) usa una lista de módulos **permitidos** y `time` no está en ella: `import time` y `from time import time` ya se reportan como import prohibido, así que `time.time`, `time.monotonic` y parecidos ya están cubiertos. Falta detectar `datetime.now`, `datetime.utcnow`, `datetime.today` y `date.today`, porque `datetime` sí está permitido.
- Ningún módulo del dominio llama hoy al reloj: `now` aparece solo en docstrings, que `ast` no mira.
- Solo `CTX` y `_ctx()` de `test_validate_new_appointment.py` construyen un `ScheduleContext`. Sus fechas van del 19/10 al 26/10/2026, que para la fecha real del explore ya son pasado; con el reloj inyectado alcanza con un `now` fijo anterior.
- En el `.venv`, `zoneinfo` confirma que Buenos Aires es UTC−3 fijo en octubre de 2026, que el 2026-10-20 es martes, que el martes 20 a las 10:00 locales es 13:00 UTC y que el martes 20 a las 23:30 locales es el miércoles 21 a las 02:30 UTC.
- No había changes activos. La spec `appointment-scheduling` tiene 22 requisitos y `domain-dependency-guard` tiene 6.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿En qué grupo va `IN_THE_PAST` y qué código HTTP le corresponde? | Al final del grupo 1, después de la medianoche, y se evalúa siempre (solo necesita el inicio y `now`, no la duración). Es validez del pedido: `422`. | Es una propiedad del pedido frente al reloj, no un choque con la agenda; US-005 habla de "errores de carga". Informar solapamientos o bloqueos de un horario que ya pasó es ruido, y el grupo 2 supone un pedido válido (explore de C-05). Respeta el orden de RN-AG-12. Se suma `IN_THE_PAST → 422` a KB 07. |
| 2 | ¿Cómo se compara un `now` con segundos contra un inicio en la grilla? | Comparación estricta de instantes: `start_at < now` es `IN_THE_PAST`; `start_at == now` es válido. No se trunca `now` ni hay tolerancia. Con `now` 10:00:30, un inicio 10:00 se rechaza. | Es literal a RN-AG-06 y US-005 CA-1/CA-2. Truncar o dar margen sería una política que la KB no pide. Como todo inicio válido tiene segundos en cero, `start == now` solo se da si `now` también los tiene. El mensaje muestra el inicio con fecha (`dd/mm/aaaa HH:MM`) y `now` con segundos, para no decir "10:00 es anterior a 10:00". |
| 3 | ¿Qué pasa si `now` llega naive o en otra zona? | `ScheduleContext.now: datetime`, sin valor por defecto; `__post_init__` aplica `_to_utc("now", ...)`: naive → `ValueError` (error de programación) y otra zona → mismo instante en UTC. | Es el criterio de `start_at`, de los turnos y de los bloqueos. Una violación no sirve porque `now` no lo carga el usuario, y asumir UTC rompería la regla dura de no usar `datetime` naive. Sin default, mypy avisa si un llamador se olvida de pasarlo. |
| 4 | ¿Cómo se extiende la guardia de `ast`? | Función nueva `find_global_clock_calls(domain_dir)` en `import_guard.py`, que resuelve por archivo qué denota cada nombre importado (`import datetime as X`, `from datetime import datetime as Y`, `from datetime import date as Z`) y reporta todo acceso de atributo (no solo la llamada) a `now`, `utcnow` o `today` sobre la clase `datetime`, a `today` sobre la clase `date`, y a `X.datetime.now` / `X.date.today` por el módulo; `from datetime import *` se reporta. `time` sigue a cargo de la lista de permitidos, con tests explícitos. Comparte con la guardia de imports solo el recorrido de los archivos. | Filtrar por nombre de atributo daría falso positivo con `context.now`, que es justo lo que agrega C-07. Detectarlo en ejecución (monkeypatch, freezegun) usa mocks y una dependencia nueva. Una función aparte no toca los tests de C-01 y entra como delta de `domain-dependency-guard`. Límites documentados (confirmados por la autora): no detecta `getattr(datetime, "now")` ni reasignaciones como `d = datetime; d.now()`, y un parámetro llamado `datetime` daría un falso positivo aceptable. |
| 5 | ¿Cómo sobreviven los tests existentes? | `CTX` y `_ctx()` pasan `now = 2026-10-01T00:00Z`. | Es anterior a todas las fechas de los tests (19/10 a 26/10). Cambian dos líneas. |

## Pedidos para el propose

- `model.py`: campo `now` en `ScheduleContext` y `__post_init__` que lo normaliza con `_to_utc`.
- `violations.py`: `IN_THE_PAST` en `ViolationCode`.
- `rules/past.py`: `check_not_in_the_past(start_at, now, tz)`, con el mensaje en hora local (inicio con fecha, `now` con segundos).
- `appointment/validate.py`: cableado al final del grupo 1, evaluado siempre.
- `tests/domain/import_guard.py`: `find_global_clock_calls` y su formato de mensaje; test sobre el árbol real.
- Tests (martes 20/10/2026, hora local = UTC−3; `NOW` = 10:00 local = 13:00 UTC salvo que se indique otra cosa):
  1. Inicio 09:55 (12:55 UTC) → `[IN_THE_PAST]`.
  2. Inicio 10:00 (13:00 UTC) = `now` → `Ok`.
  3. Inicio 10:05 (13:05 UTC) → `Ok`.
  4. `now` 10:00:30 (13:00:30 UTC), inicio 10:00 → `[IN_THE_PAST]`.
  5. `now` 10:00:30, inicio 10:05 (13:05 UTC) → `Ok`.
  6. `now` 13:00:00.000001 UTC, inicio 10:00 (13:00 UTC) → `[IN_THE_PAST]`.
  7. `now` martes 23:30 (miércoles 21 02:30 UTC), inicio miércoles 21 00:00 (21 03:00 UTC) → `Ok`.
  8. `now` martes 23:30 (21 02:30 UTC), inicio martes 23:00 (21 02:00 UTC) → `[IN_THE_PAST]`.
  9. Inicio 09:52 (12:52 UTC, fuera de grilla) → `[INVALID_START_TIME, IN_THE_PAST]`.
  10. `now` 23:45 (21 02:45 UTC), inicio 23:30 (21 02:30 UTC) con 60 min → `[CROSSES_MIDNIGHT, IN_THE_PAST]`.
  11. Inicio 09:00 (12:00 UTC) con duración 7 → `[INVALID_DURATION, IN_THE_PAST]`.
  12. Inicio 09:00, prestación inexistente y sin duración → `[UNKNOWN_REFERENCE (SERVICE), IN_THE_PAST]`.
  13. Inicio 09:00 con un turno reservado de P1 de 09:00 a 09:30 → solo `[IN_THE_PAST]`.
  14. Inicio 08:00 (11:00 UTC) con los tramos del martes desde las 09:00 → solo `[IN_THE_PAST]`.
  15. `now` 10:00-03:00 → se guarda como 13:00 UTC.
  16. `now` 14:00+01:00 → se guarda como 13:00 UTC.
  17. `now` naive → `ValueError`.
  - Guardia del reloj: se reportan `datetime.now()`, `datetime.utcnow()`, `datetime.today()`, `date.today()`, `datetime.datetime.now()`, `datetime.date.today()`, los alias (`dt.datetime.now()`, `D.now()`), la referencia sin llamada (`reloj = datetime.now`), la llamada dentro de una función y `from datetime import *`; no se reportan `context.now`, un parámetro `now`, `datetime(2026, 10, 20, tzinfo=...)`, `timedelta(...)` ni "now" en un docstring; `import time` y `from time import time as t` los reporta la guardia de imports; `getattr(datetime, "now")` no se detecta (límite); el dominio real no llama al reloj.
- En la spec, agregar los requisitos del pasado y de `now` en el contexto, y actualizar "Alta de un turno válido" y el de los dos grupos; en `domain-dependency-guard`, agregar el requisito del reloj global.
