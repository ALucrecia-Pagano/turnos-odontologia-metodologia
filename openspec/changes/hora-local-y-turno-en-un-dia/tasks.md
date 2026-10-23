# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Skills a cargar antes de escribir código: `tdd`, `python-testing-patterns` y `python-pro` (compact rules en `.atl/skill-registry.md`; la regla dura del proyecto prevalece: sin mocks en el dominio, sin `datetime.now()` y las reglas de negocio devuelven violaciones, no excepciones).
>
> Reglas para todos los tests de dominio (design D12, igual que en C-02 y C-03): datos literales (UUIDs fijos en constantes con nombre; `_at` en UTC del 2026-10-20 y `_local` en `America/Argentina/Buenos_Aires`); un `ZoneInfo` real, nunca `timezone(timedelta(hours=-3))` en los tests nuevos; los instantes UTC esperados se escriben como literales de la spec, sin recalcular la conversión; sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre la lista completa de violaciones (código y orden). `pytest.raises` solo para errores de programación (`ValueError`).
>
> Governance **MEDIO**: la tarea **4.4** es un punto de control. No se implementa ninguna regla (grupos 5 en adelante) sin la aprobación de la autora.

## 1. Red de seguridad

- [x] 1.1 SAFETY NET: correr `pytest` y `mypy` antes de tocar nada y anotar el baseline (C-03 cerró con 149 tests y `Success: no issues found in 21 source files`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.

## 2. Códigos nuevos (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Design D1 y D2.

- [x] 2.1 RED: agregar a la tabla de `ViolationCode` → valor serializado los casos `CROSSES_MIDNIGHT` → `"CROSSES_MIDNIGHT"` e `INVALID_START_TIME` → `"INVALID_START_TIME"`. Verificar que fallan porque los miembros no existen.
- [x] 2.2 GREEN: sumar los dos códigos a `ViolationCode` (valor igual al nombre). Verificar `pytest` y `mypy` en verde.

## 3. Hora local (`intervals.py`)

> Tests en `tests/domain/test_intervals.py`. Design D9.

- [x] 3.1 RED: test de `local_day_and_minutes(instant, tz)` con `ZoneInfo("America/Argentina/Buenos_Aires")`: 2026-10-20 02:30 UTC → `(date(2026, 10, 19), 1410)` (el instante UTC que en hora local cae en otro día). Verificar que falla porque la función no existe.
- [x] 3.2 GREEN: implementar `local_day_and_minutes` con `instant.astimezone(tz)` y la constante `MINUTES_PER_DAY = 1440` (eliminada después, ver Desvíos). Verificar en verde y que `test_domain_dependencies.py` sigue en verde (`zoneinfo` ya está en la allowlist).
- [x] 3.3 TRIANGULATE: tabla con 2026-10-21 03:00 UTC → `(date(2026, 10, 21), 0)` (medianoche local), 2026-10-20 13:00 UTC → `(date(2026, 10, 20), 600)` y 2026-10-20 13:05:30 UTC → `(date(2026, 10, 20), 605)` (los segundos se descartan). Un instante *naive* → `pytest.raises(ValueError)`. Verificar en verde.
- [x] 3.4 RED → GREEN: `format_local_time(instant, tz)`: 2026-10-21 02:30 UTC → `"23:30"`, 2026-10-21 03:30 UTC → `"00:30"` y 2026-10-20 12:05 UTC → `"09:05"` (ceros a la izquierda). Verificar que falla antes y en verde después.
- [x] 3.5 TRIANGULATE: `format_local_time` con segundos: 2026-10-20 13:05:30 UTC → `"10:05:30"` y 2026-10-20 13:05:00.250000 UTC → `"10:05:00"` (solo microsegundos: se muestran los segundos en cero, no los microsegundos; design D11). Verificar que falla antes (devolvía `HH:MM`) y en verde después.
- [x] 3.6 REFACTOR: docstrings estilo Google (citar DD-07 y SU-01: la zona se recibe por parámetro) y `Final` en `MINUTES_PER_DAY` (eliminada después, ver Desvíos). Verificar `pytest` y `mypy` en verde.

## 4. Contexto de agenda, firma nueva y punto de control

> Tests en `tests/domain/test_validate_new_appointment.py`. Design D3, D8 y D12.

- [x] 4.1 RED: agregar `BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")`, `CTX = ScheduleContext(tz=BUENOS_AIRES)` y el helper `_local(day, hour, minute, second=0, microsecond=0)`. Escenario **"Inicio en la grilla"**: `validate_new_appointment(_request(_local(20, 10, 5)), _refs(), [], CTX)` → `Ok` con el turno de `2026-10-20T13:05:00+00:00` a `2026-10-20T13:35:00+00:00` (literales UTC). Verificar que falla porque `ScheduleContext` no existe.
- [x] 4.2 GREEN: en `model.py` agregar `ScheduleContext(tz: ZoneInfo)`, *frozen* con slots (design D3 y D8). Cambiar la firma a `validate_new_appointment(request, references, existing_appointments, context)`, sin valor por defecto en `context`, y pasar el contexto a `_request_validity_violations` aunque todavía no lo use ninguna regla. Verificar que 4.1 pasa.
- [x] 4.3 Adaptar las 28 llamadas existentes de `test_validate_new_appointment.py`: cada `validate_new_appointment(req, refs, existing)` pasa a `validate_new_appointment(req, refs, existing, CTX)`. No cambiar ninguna aserción. Verificar que `pytest` tiene al menos el baseline de 1.1 más los tests nuevos, todo en verde, y `mypy` en verde. Actualizar el ejemplo de `backend/README.md` §Dominio con `ScheduleContext` y la firma nueva y correrlo una vez en el venv para verificar que coincide con la firma real.
- [x] 4.4 ⛔ **Aprobado por la autora el 2026-10-23**, con dos ajustes: redacción de `INVALID_START_TIME` (design D11) y `ValueError` de `format_local_time` con un instante *naive* (ver "Desvíos durante el apply"). **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** No seguir con el grupo 5 hasta que la autora apruebe. Presentarle: (a) `ScheduleContext` y su ubicación en `model.py` (design D3 y D8); (b) la firma nueva de `validate_new_appointment`, con `context` al final y sin valor por defecto; (c) los dos códigos nuevos (`CROSSES_MIDNIGHT`, `INVALID_START_TIME`); (d) la API de `intervals.py` (`local_day_and_minutes`, `format_local_time`, `MINUTES_PER_DAY` —eliminada después, ver Desvíos—, design D9) y los nombres de `GRID_STEP_MIN` / `rules/grid.py`, `rules/start_time.py` y `rules/same_day.py` (design D6 y D10); (e) el texto de los mensajes (design D11, ya ajustado con los segundos, el caso de solo microsegundos `10:05:00` y la razón "no puede tener segundos ni fracciones de segundo"); (f) el diff de la adaptación de los tests (solo suman `CTX`); (g) la salida de `pytest` y `mypy`. Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha.

## 5. Granularidad compartida (`rules/grid.py`)

> Design D6. Es un refactor sin comportamiento nuevo: la suite tiene que estar en verde antes y después.

- [x] 5.1 REFACTOR: crear `rules/grid.py` con `GRID_STEP_MIN: Final = 5` y un docstring que cite SU-02 ("constante configurable", una sola para la duración y el inicio). En `rules/duration.py`, quitar `DURATION_STEP_MIN` y usar `GRID_STEP_MIN`. Verificar con `pytest` que los escenarios de duración de C-03 siguen en verde (incluidos los mensajes de 487 con "múltiplo de 5") y `mypy` en verde. Buscar `DURATION_STEP_MIN` en `backend/`: no debe quedar ninguna coincidencia.

## 6. Inicio en la grilla de 5 minutos (`rules/start_time.py`, RN-DI-05)

> Solo si la autora aprobó en 4.4. Spec: requisito "Inicio en la grilla de 5 minutos" y escenarios de inicio de "Todas las violaciones, en orden estable" y "Contenido de cada violación". Design D2, D4, D10 y D11.

- [x] 6.1 RED: escenario "Inicio con minutos fuera de la grilla": pedido a las `_local(20, 10, 3)` → `Rejected` con exactamente `[INVALID_START_TIME]`. Verificar que falla (hoy devuelve `Ok`).
- [x] 6.2 GREEN: crear `rules/start_time.py` con `check_start_time(start_at, tz) -> list[Violation]` (minutos múltiplo de `GRID_STEP_MIN`) y llamarla en el grupo 1 después de la duración (design D4, paso 3). Verificar en verde y que "Inicio en la grilla" (4.1) sigue en verde.
- [x] 6.3 TRIANGULATE: tabla de "Inicio con segundos o microsegundos" (`_local(20, 10, 5, 30)` → `[INVALID_START_TIME]` con un mensaje que contiene `"10:05:30"`, y `_local(20, 10, 5, 0, 250000)` → `[INVALID_START_TIME]` con un mensaje que contiene `"10:05:00"`). Si falla, sumar la razón de segundos y microsegundos y armar la hora con `format_local_time` (design D11). Verificar en verde.
- [x] 6.4 RED → GREEN: escenarios "Inicio que rompe dos condiciones" (`_local(20, 10, 3, 30)` → exactamente una `INVALID_START_TIME`, no dos) y "Mensaje de inicio fuera de la grilla" (10:03 → mensaje que contiene `"10:03, hora local"` y `"debe caer en un minuto múltiplo de 5"`; 10:03:30 → mensaje exacto de la spec, `conflicting_appointment_id is None` y `reference_kind is None`). Armar el mensaje con todas las razones y la hora con `format_local_time` (design D11). Verificar que falla antes (por el texto o por dos violaciones) y en verde después.
- [x] 6.5 TRIANGULATE: escenarios "Referencia, duración e inicio inválidos a la vez" (profesional `None`, explícita 7, `_local(20, 10, 3)` → exactamente `[UNKNOWN_REFERENCE, INVALID_DURATION, INVALID_START_TIME]`) e "Inicio fuera de la grilla en un horario ocupado" (A existente, `_local(20, 10, 3)` de 30 minutos para P1/S1 → solo `[INVALID_START_TIME]`). Si el segundo pasa de entrada por el corte del grupo 1, quitar el corte temporalmente para verlo fallar con violaciones de solapamiento y después restaurarlo. Verificar en verde.
- [x] 6.6 REFACTOR: docstrings estilo Google en el módulo y en `check_start_time` (citar RN-DI-05 y SU-02). Verificar `pytest` y `mypy` en verde.

## 7. Turno dentro de un solo día local (`rules/same_day.py`, RN-AG-10)

> Spec: requisitos "Turno dentro de un solo día local" y "Hora local en la zona horaria recibida", y escenarios de medianoche de "Todas las violaciones, en orden estable" y "Contenido de cada violación". Design D4, D5, D7, D9, D10 y D11.

- [x] 7.1 RED: escenario "Turno que cruza la medianoche local": `_local(20, 23, 30)` con explícita 60 → `Rejected` con exactamente `[CROSSES_MIDNIGHT]`. Verificar que falla (hoy devuelve `Ok`).
- [x] 7.2 GREEN: crear `rules/same_day.py` con `check_same_local_day(start_at, end_at, tz) -> list[Violation]` usando `local_day_and_minutes` y la cuenta en minutos de design D9, y llamarla en el grupo 1 después del inicio, solo si hay duración efectiva sin violaciones (design D4, paso 4). Verificar en verde.
- [x] 7.3 TRIANGULATE: tabla de aceptaciones: "Turno que termina antes de la medianoche local" (`_local(20, 23, 0)` con 55 → `Ok` de `2026-10-21T02:00:00+00:00` a `2026-10-21T02:55:00+00:00`) y "Turno que termina justo a la medianoche local" (`_local(20, 23, 30)` sin explícita, prestación de 30 → `Ok` hasta `2026-10-21T03:00:00+00:00`, design D5). Si 23:30–00:00 falla, corregir la comparación para que el fin igual a 1440 sea válido. Verificar en verde.
- [x] 7.4 TRIANGULATE: escenarios de "Hora local en la zona horaria recibida": "Instante UTC que en hora local cae en otro día" (`2026-10-20T02:30:00+00:00` con 60 → `[CROSSES_MIDNIGHT]`) y "Turno que cruza la medianoche UTC pero no la local" (`2026-10-20T23:30:00+00:00` con 60 → `Ok`). Los dos fallarían si la regla se evaluara en UTC (design D7); anotar en el resumen del apply que se comprobó cambiando temporalmente la zona del test a UTC, y restaurarla. Verificar en verde.
- [x] 7.5 RED → GREEN: escenario "Duración inválida en un turno que cruzaría la medianoche" (`_local(20, 23, 30)` con explícita 62 → exactamente `[INVALID_DURATION]`, sin `CROSSES_MIDNIGHT`). Si pasa de entrada por la condición de 7.2, quitarla temporalmente para verlo fallar con las dos violaciones y después restaurarla. Verificar en verde.
- [x] 7.6 TRIANGULATE: caso borde pedido por la autora, "Inicio fuera de la grilla en un turno que cruza la medianoche" (`_local(20, 23, 33)` con explícita 60 → exactamente `[INVALID_START_TIME, CROSSES_MIDNIGHT]`, en ese orden). Verificar en verde.
- [x] 7.7 RED → GREEN: escenario "Mensaje de cruce de medianoche" (`_local(20, 23, 30)` con 60 → mensaje que contiene `"23:30"` y `"00:30"` y no contiene `"02:30"`; `conflicting_appointment_id is None` y `reference_kind is None`). Mensaje de design D11 con `format_local_time`. Verificar en verde.
- [x] 7.8 REFACTOR: en `validate.py`, calcular el fin una sola vez (duración efectiva → fin) y usarlo en el grupo 1 y en el candidato; actualizar el docstring de `_request_validity_violations` y de `validate_new_appointment` con el orden referencias → duración → inicio → medianoche y el nuevo parámetro `context`. Docstrings estilo Google en `rules/same_day.py` (citar RN-AG-10, SU-09 y DD-07). Verificar `pytest` y `mypy` en verde después de cada paso.

## 8. Documentación

- [x] 8.1 `backend/README.md` §Dominio: sumar `ScheduleContext` a la fila de `model`, la hora local a la de `intervals`, `grid`, `start_time` y `same_day` a la de `rules/`, y una línea con el orden del grupo 1 (referencias → duración → inicio → medianoche). Verificar que el ejemplo sigue coincidiendo con la firma real (correrlo una vez en el venv).
- [x] 8.2 Verificar que `knowledge-base/07_flujos_principales.md` tiene `CROSSES_MIDNIGHT` e `INVALID_START_TIME` en el catálogo de códigos (se agregaron en el propose) y que `CHANGES.md` §[C-04] coincide con lo implementado (`intervals.py`, `rules/same_day.py`, `rules/start_time.py`, `rules/grid.py`, los dos códigos). Ajustar solo si el apply se desvió. El estado `[x]` se marca en el archive, no acá.
- [x] 8.3 Verificar que RN-AG-12 en `knowledge-base/05_reglas_de_negocio.md` tiene el orden referencias → duración → inicio → medianoche → pasado → … (se actualizó en el propose con el OK de la autora). Proponerle a la autora actualizar en el archive el Purpose de `openspec/specs/appointment-scheduling/spec.md` (inicio en la grilla, un solo día local y la convención de hora local). Editar solo con su aprobación y anotar la decisión.

## 9. Verificación integral y evidencias

- [x] 9.1 Desde `backend/`: `pytest -v` en verde (más tests que el baseline de 1.1), con la salida completa guardada en `docs/evidencias/pytest-C-04.txt`.
- [x] 9.2 Desde `backend/`: `mypy` con `Success: no issues found` sobre `app` y `tests` (tres archivos más que en C-03: `rules/grid.py`, `rules/start_time.py` y `rules/same_day.py`), con la salida guardada en `docs/evidencias/mypy-C-04.txt`.
- [x] 9.3 Trazabilidad: cada uno de los 28 escenarios de `specs/appointment-scheduling/spec.md` de este change (15 nuevos y 13 que ya existían en los requisitos modificados) tiene al menos un test (función o caso parametrizado), y los escenarios de C-02 y C-03 que no toca este change siguen cubiertos. Dejar la tabla escenario → test en el resumen del apply.
- [x] 9.4 Pureza del dominio: buscar en `app/domain` `datetime.now`, `utcnow`, `time.time`, `uuid1`, `uuid4`, `Any`, `os.environ`, `getenv`, `"America/` y `raise`. No debe haber ninguna coincidencia, salvo los `raise ValueError` de las invariantes de `model.py`, `violations.py` e `intervals.py` (incluido el instante *naive* de `local_day_and_minutes`) y el de la coherencia de ids en `appointment/validate.py`. `test_domain_dependencies.py` en verde (la allowlist no cambia).
- [x] 9.5 `openspec validate hora-local-y-turno-en-un-dia --strict` desde la raíz → "is valid".
- [x] 9.6 Escribir `docs/evidencias/verify-C-04.md` con el mismo formato que `verify-C-03.md`: fecha, comandos, resultados de 9.1, 9.2 y 9.5, la tabla de escenarios obligatorios de la consigna con su test (al menos uno feliz, uno de error de negocio y uno de borde: 23:30–00:00 o 23:33 con 60 minutos) y los desvíos del apply.
- [x] 9.7 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal (más las evidencias) y no se hizo ningún commit.

## 10. Hallazgo del apply: medianoche con segundos (volvió a la spec)

> Hallazgo de la revisión del apply (2026-10-23), aprobado por la autora para este change: `check_same_local_day` truncaba el fin a minutos, así que 23:30:30 con 30 minutos (fin 00:00:30) daba 1440 y no informaba `CROSSES_MIDNIGHT`, contra D4. Spec: escenario "Inicio con segundos en un turno que cruza la medianoche por segundos" y el texto del requisito "Turno dentro de un solo día local".

- [x] 10.1 RED: escenario "Inicio con segundos en un turno que cruza la medianoche por segundos" (`_local(20, 23, 30, 30)` con explícita 30 → exactamente `[INVALID_START_TIME, CROSSES_MIDNIGHT]`). Verificar que falla (hoy devuelve solo `[INVALID_START_TIME]`) y anotar el motivo.
- [x] 10.2 GREEN: en `rules/same_day.py`, comparar con el instante completo del fin, no con los minutos truncados: el turno cruza la medianoche si el fin, en hora local, es posterior a las 00:00 del día local siguiente al del inicio. Verificar en verde, incluidos 23:30–00:00 válido, 23:00–23:55 válido y los dos escenarios de hora local.
- [x] 10.3 REFACTOR: docstrings de `rules/same_day.py` (y de `MINUTES_PER_DAY` / `local_day_and_minutes` si dejaron de describir el uso real). Si `MINUTES_PER_DAY` o `local_day_and_minutes` quedan sin uso en el dominio, no borrarlos sin avisar: C-05 los necesita (design D9); anotarlo. (Después la autora decidió eliminar `MINUTES_PER_DAY`, ver Desvíos.) Verificar `pytest` y `mypy` en verde.
- [x] 10.4 Anotar el hallazgo en "Desvíos durante el apply" de `design.md` (hallazgo del apply que volvió a la spec) y ajustar D9 si cambia la forma de la cuenta.
- [x] 10.5 Rehacer la verificación: `pytest -v` → `docs/evidencias/pytest-C-04.txt`, `mypy` → `docs/evidencias/mypy-C-04.txt`, `openspec validate --strict`, y actualizar `docs/evidencias/verify-C-04.md` (resultados, 29 escenarios en la trazabilidad, el escenario nuevo y el desvío). `git status` sin commits.
