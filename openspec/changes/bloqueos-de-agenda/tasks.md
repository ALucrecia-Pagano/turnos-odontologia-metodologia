# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Skills a cargar antes de escribir código: `tdd`, `python-testing-patterns` y `python-pro` (compact rules en `.atl/skill-registry.md`; la regla dura del proyecto prevalece: sin mocks en el dominio, sin `datetime.now()`, sin `Any`, y las reglas de negocio devuelven violaciones, no excepciones). El proyecto no usa `ruff` ni `black`: la verificación estática es `mypy --strict`.
>
> Reglas para todos los tests de dominio (design D10, igual que en C-02 a C-05): datos literales (UUIDs fijos en constantes con nombre: `BL1`, `BL2`, `BL3`, `BLV`, `T1` a `T7`; `_at` en UTC del 2026-10-20 y `_local` en `America/Argentina/Buenos_Aires`); un `ZoneInfo` real; los instantes UTC esperados se escriben como literales de la spec, sin recalcular la conversión; sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre la lista completa de violaciones (código, id del bloqueo y orden). `pytest.raises` solo para errores de programación (`ValueError`). Si un test pasa de entrada, comprobar que puede fallar con una mutación temporal del código, anotarla y restaurar.
>
> Governance **MEDIO**: la tarea **3.5** es un punto de control. No se implementa ninguna regla (grupos 4 en adelante) sin la aprobación de la autora.

## 1. Red de seguridad

- [ ] 1.1 SAFETY NET: correr `pytest` y `mypy --strict app tests` antes de tocar nada y anotar el baseline (C-05 cerró con `232 passed` y `Success: no issues found in 26 source files`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.

## 2. Códigos nuevos y id del bloqueo en la violación (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Design D5.

- [ ] 2.1 RED: agregar a la tabla de `ViolationCode` → valor serializado los casos `BLOCKED_TIME` e `INVALID_BLOCK` (valor igual al nombre), y un test de que `Violation(code, message)` tiene `conflicting_block_id is None` y que `Violation(..., conflicting_block_id=BL1)` lo conserva. Verificar que fallan porque los miembros y el campo no existen.
- [ ] 2.2 GREEN: sumar los dos códigos a `ViolationCode` y `conflicting_block_id: UUID | None = None` **al final** de los campos de `Violation`, con su línea en el docstring. Verificar `pytest` (baseline + nuevos) y `mypy` en verde: ninguna construcción existente de `Violation` cambia.

## 3. Modelo `Block`, contexto, migración de `CTX` y punto de control

> Tests en `tests/domain/test_model.py` y `tests/domain/test_validate_new_appointment.py`. Spec: "Instantes del bloqueo con zona horaria y normalizados a UTC". Design D1, D3 y D10.

- [ ] 3.1 RED: en `test_model.py`, escenarios "Bloqueo cargado en hora de Buenos Aires" (inicio `2026-10-20T10:00:00-03:00` y fin `2026-10-20T12:00:00-03:00` → `2026-10-20T13:00:00+00:00` y `2026-10-20T15:00:00+00:00`) y "Bloqueo con un instante sin zona" (inicio naive y fin naive, parametrizado → `ValueError` con "zona horaria"), más un test de que un bloqueo con inicio posterior al fin (12:00 a 10:00 hora local) se construye **sin lanzar** (design D3). Verificar que fallan porque `Block` no existe.
- [ ] 3.2 GREEN: en `model.py`, `Block` *frozen* con slots (`id`, `professional_id`, `start_at`, `end_at`, `reason: str | None = None`), con `__post_init__` que solo aplica `_to_utc` a los dos instantes, y docstring estilo Google (RN-DI-03, KB 04; el orden lo valida `validate_block`). Verificar `pytest` y `mypy` en verde.
- [ ] 3.3 Agregar `blocks: tuple[Block, ...]` a `ScheduleContext`, después de `working_hours` y sin valor por defecto (design D1), y actualizar su docstring. Verificar que `mypy` marca `CTX` y `_ctx` en `test_validate_new_appointment.py` (falta el argumento) y anotar los errores.
- [ ] 3.4 Migrar los tests: `CTX = ScheduleContext(tz=BUENOS_AIRES, working_hours=FULL_WEEK, blocks=())` y `_ctx(*slots)` con `blocks=()` (design D10). No cambiar ninguna llamada ni aserción. Verificar con `git diff` que solo cambian esas líneas, `pytest` con el baseline de 1.1 más los tests nuevos, y `mypy` en verde. Actualizar en `backend/README.md` §Dominio el ejemplo (contexto con `blocks=()`) y la fila de `model` (`Block`, `blocks`), y correr el ejemplo una vez en el venv para verificar que coincide con la firma real.
- [ ] 3.5 ⛔ **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** No seguir con el grupo 4 hasta que la autora apruebe. Presentarle: (a) `Block` sin validación del orden al construirse (design D3); (b) `ScheduleContext.blocks` obligatorio (D1); (c) `BLOCKED_TIME`, `INVALID_BLOCK` y `conflicting_block_id` al final de `Violation` (D5); (d) las firmas de `rules/blocks.py` y la comparación directa en vez de `Interval` (D7); (e) los textos de los mensajes y `format_local_date_time` (D8 y D9); (f) los tests de D10 y los escenarios extra de D12; (g) el diff de la migración de `CTX`; (h) la salida de `pytest` y `mypy`. Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` (y la spec si cambia un comportamiento) y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha.

## 4. Validez de un bloqueo (`rules/blocks.py`, RN-DI-03)

> Solo si la autora aprobó en 3.5. Tests en `tests/domain/test_blocks.py` (nuevo). Spec: requisito "Validez de un bloqueo". Design D3 y D9.

- [ ] 4.1 RED: escenario "Bloqueo con inicio igual al fin" (10:00 a 10:00 hora local = 13:00 a 13:00 UTC → exactamente `[INVALID_BLOCK]`). Verificar que falla porque `validate_block` no existe.
- [ ] 4.2 GREEN: crear `rules/blocks.py` con `validate_block(block) -> list[Violation]` (`start_at >= end_at` → `INVALID_BLOCK`). Verificar en verde y que `test_domain_dependencies.py` sigue en verde.
- [ ] 4.3 TRIANGULATE: tabla con "Bloqueo con inicio posterior al fin" (12:00 a 10:00 → `[INVALID_BLOCK]`), "Bloqueo válido" (BL1 → `[]`) y "Bloqueo de un minuto, fuera de la grilla" (10:00 a 10:01 = 13:00 a 13:01 UTC → `[]`). Si `>=` está mal (`>`), el caso de inicio igual al fin falla. Verificar en verde.
- [ ] 4.4 RED → GREEN: mensaje de design D9 (exactamente "El bloqueo no es válido: el inicio debe ser anterior al fin.", sin `conflicting_appointment_id`, `conflicting_block_id` ni `reference_kind`). Verificar que falla antes (mensaje mínimo) y en verde después.
- [ ] 4.5 REFACTOR: docstrings estilo Google en el módulo y en `validate_block` (RN-DI-03, US-011 CA-1 y CA-2; el orden no se valida al construir `Block`); el mensaje como constante `Final`. Agregar `blocks` a la fila de `rules/` de `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 5. Turno fuera de los bloqueos (`check_blocks` y `validate.py`, RN-AG-05)

> Tests en `tests/domain/test_validate_new_appointment.py`, con el helper `_ctx_blocks(*blocks, working_hours=FULL_WEEK)` (design D10). Spec: requisito "Turno fuera de los bloqueos del profesional". Design D2, D4, D5 y D7.

- [ ] 5.1 RED: escenario "Turno dentro de un bloqueo" (BL1; 10:30–11:00 hora local = 13:30–14:00 UTC → exactamente `[BLOCKED_TIME]` con `conflicting_block_id == BL1`). Verificar que falla (hoy devuelve `Ok`).
- [ ] 5.2 GREEN: `check_blocks(professional_id, start_at, end_at, blocks, tz) -> list[Violation]` con el filtro por profesional y el helper `_overlaps` semiabierto (design D7), con un mensaje mínimo. Llamarla en `_agenda_conflict_violations` después de `check_working_hours` y antes de los solapamientos (design D2). Verificar en verde y que la suite completa sigue en verde con `blocks=()`.
- [ ] 5.3 TRIANGULATE: tabla de bordes con BL1: "Turno que termina justo cuando empieza el bloqueo" (09:30–10:00 → `Ok`), "Turno que empieza justo cuando termina el bloqueo" (12:00–12:30 → `Ok`), "Turno que pisa el inicio del bloqueo" (09:45–10:15 → `[BLOCKED_TIME]`) y "Turno que pisa el fin del bloqueo" (11:45–12:15 → `[BLOCKED_TIME]`). Comprobar que los bordes fallan con `<=` en `_overlaps`; anotar y restaurar. Verificar en verde.
- [ ] 5.4 TRIANGULATE: "Bloqueo de otro profesional" (bloqueo de P2 10:00–12:00; pedido de P1 10:30–11:00 → `Ok`). Comprobar que falla sin el filtro por profesional; anotar y restaurar.
- [ ] 5.5 TRIANGULATE: bloqueo de varios días BLV (lunes 2026-10-19 00:00 a lunes 2026-10-26 00:00 hora local = 03:00 UTC del 19 a 03:00 UTC del 26): "Turno dentro de un bloqueo de varios días" (martes 20 10:00–10:30 = 13:00–13:30 UTC → `[BLOCKED_TIME]` con BLV), "Último turno del domingo local dentro de un bloqueo de varios días" (domingo 25 23:30–23:55 = 02:30–02:55 UTC del 26 → `[BLOCKED_TIME]`), "Turno que empieza justo cuando termina un bloqueo de varios días" (lunes 26 00:00–00:30 = 03:00–03:30 UTC → `Ok`) y "Turno que termina justo cuando empieza un bloqueo de varios días" (domingo 18 23:30–00:00 = 02:30–03:00 UTC del 19 → `Ok`). Con los instantes escritos como literales UTC. Comprobar que el domingo 25 falla si se compara por fecha UTC (mutación temporal); anotar y restaurar.
- [ ] 5.6 RED → GREEN: "Turno que pisa dos bloqueos" (BL1 y BL2 = 11:00–13:00 hora local, 14:00–16:00 UTC; turno 11:30–12:30 = 14:30–15:30 UTC → exactamente `[BLOCKED_TIME (BL1), BLOCKED_TIME (BL2)]`) y "Orden de los bloqueos independiente del orden recibido" (BL2 primero → mismo orden). Si el segundo falla, ordenar por `(start_at, str(id))` (design D5). Verificar en verde.
- [ ] 5.7 REFACTOR: docstrings estilo Google en `check_blocks` y `_overlaps` (RN-AG-05, DD-07; un bloqueo inválido nunca se solapa) y en `_agenda_conflict_violations` y `validate_new_appointment` (grupo 2: horario → bloqueo → profesional → sillón; `context.blocks`). Actualizar el párrafo de los grupos en `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 6. Mensaje de `BLOCKED_TIME`

> Tests en `tests/domain/test_intervals.py` y `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Mensaje de un turno bloqueado". Design D8.

- [ ] 6.1 RED → GREEN: `format_local_date_time(instant, tz) -> str` en `intervals.py`: `2026-10-20T13:00:00+00:00` → `"20/10/2026 10:00"` y `2026-10-26T03:00:00+00:00` → `"26/10/2026 00:00"` en Buenos Aires, e instante naive → `ValueError`. Verificar que falla antes y en verde después.
- [ ] 6.2 RED: "Mensaje de un bloqueo sin motivo" (BL1; 10:30–11:00 → mensaje exacto de la spec con el id de BL1, sin `conflicting_appointment_id` ni `reference_kind`). Verificar que falla por el texto mínimo de 5.2.
- [ ] 6.3 GREEN: armar el mensaje de design D8 con `format_local_time` y `format_local_date_time`. Verificar en verde.
- [ ] 6.4 TRIANGULATE: "Mensaje de un bloqueo de varios días con motivo" (BLV con motivo "vacaciones"; domingo 25 23:30–23:55 → mensaje exacto con `del 19/10/2026 00:00 al 26/10/2026 00:00 (hora local). Motivo: vacaciones.` y sin `02:30` ni `03:00`), más un bloqueo con `reason=""` que da el mismo texto que sin motivo (design D8). Verificar en verde.
- [ ] 6.5 REFACTOR: docstring de `format_local_date_time` (SU-01; la zona por parámetro) y el armado del mensaje en un helper privado de `rules/blocks.py`. Verificar `pytest` y `mypy` en verde.

## 7. Orden de las violaciones y corte del grupo 1

> Spec: escenarios nuevos de "Todas las violaciones, en orden estable". Design D2.

- [ ] 7.1 RED → GREEN: "Fuera de horario, bloqueado y solapado a la vez" (`TUESDAY_BASE`; BL3 de P1 12:00–14:00 hora local = 15:00–17:00 UTC; E de P1/S2 12:30–13:00 = 15:30–16:00 UTC; F de P2/S1 12:45–13:15 = 15:45–16:15 UTC; pedido P1/S1 12:30–13:30 = 15:30–16:30 UTC con 60 minutos → exactamente `[OUTSIDE_WORKING_HOURS, BLOCKED_TIME (BL3), PROFESSIONAL_OVERLAP (E), CHAIR_OVERLAP (F)]`). Si pasa de entrada por 5.2, comprobar que falla moviendo temporalmente `check_blocks` antes del horario o después de los solapamientos; anotar y restaurar.
- [ ] 7.2 TRIANGULATE: "Duración inválida dentro de un bloqueo" (BL1; 10:30 hora local = 13:30 UTC, duración explícita 0 → exactamente `[INVALID_DURATION]`). Pasa por el corte del grupo 1; comprobar que falla agregando temporalmente `check_blocks` al grupo 1 con la duración efectiva de 5 minutos, anotar y restaurar.

## 8. Turnos afectados por un bloqueo (`rules/blocks.py`, RN-DI-04)

> Tests en `tests/domain/test_blocks.py`. Spec: requisito "Turnos afectados por un bloqueo". Design D6.

- [ ] 8.1 RED: "Bloqueo que pisa turnos existentes" (BL1 y T1 a T7 de la spec, recibidos en orden inverso → exactamente `[T2, T3]`). Verificar que falla porque `appointments_affected_by_block` no existe.
- [ ] 8.2 GREEN: `appointments_affected_by_block(block, appointments) -> list[Appointment]` con mismo profesional, `OCCUPYING_STATUSES` y `_overlaps`, ordenado por `(start_at, str(id))`. Verificar en verde.
- [ ] 8.3 TRIANGULATE: "Bloqueo que no pisa ningún turno" (solo T1, T6 y T7 → `[]`) y "El bloqueo no cambia los turnos que pisa" (T2 y T3 devueltos son iguales a los recibidos: mismo estado, inicio, fin, profesional y sillón). Comprobar con mutaciones temporales que fallan sin el filtro de estado (T4/T5), sin el filtro de profesional (T6) y con `<=` en `_overlaps` (T1/T7); anotar y restaurar. Sumar un caso con un bloqueo de inicio posterior al fin → `[]` sin excepción (design D7).
- [ ] 8.4 REFACTOR: docstring estilo Google (RN-DI-04, SU-05 confirmada; no cancela ni mueve; el llamador valida antes con `validate_block`). Mencionar la función en la fila de `rules/` de `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 9. Verificación integral y evidencias

- [ ] 9.1 Desde `backend/`: `pytest -v` en verde (más tests que el baseline de 1.1), con la salida completa guardada en `docs/evidencias/pytest-C-06.txt`.
- [ ] 9.2 Desde `backend/`: `mypy --strict app tests` con `Success: no issues found` (dos archivos más que en C-05: `rules/blocks.py` y `tests/domain/test_blocks.py`), con la salida guardada en `docs/evidencias/mypy-C-06.txt`.
- [ ] 9.3 Trazabilidad: cada uno de los 40 escenarios de `specs/appointment-scheduling/spec.md` de este change (25 nuevos y 15 que ya existían en los requisitos modificados) tiene al menos un test, y los escenarios de C-02 a C-05 que no toca este change siguen cubiertos. Dejar la tabla escenario → test en `docs/evidencias/verify-C-06.md`.
- [ ] 9.4 Pureza del dominio: buscar en `app/domain` `datetime.now`, `utcnow`, `time.time`, `uuid1`, `uuid4`, `Any`, `os.environ`, `getenv`, `"America/` y `raise`. No debe haber coincidencias nuevas: `rules/blocks.py` no lanza excepciones (el único `raise` nuevo posible es el `ValueError` de `_to_utc`, que ya existía). `test_domain_dependencies.py` en verde (la allowlist no cambia).
- [ ] 9.5 Verificar que `knowledge-base/05`, `07`, `09` y `10` y `CHANGES.md` §[C-06] coinciden con lo implementado (SU-05 confirmada, `INVALID_BLOCK` en el catálogo). Ajustar solo si el apply se desvió, con el OK de la autora. El estado `[x]` se marca en el archive, no acá.
- [ ] 9.6 `openspec validate bloqueos-de-agenda --strict` desde la raíz → "is valid".
- [ ] 9.7 Escribir `docs/evidencias/verify-C-06.md` con el formato de `verify-C-05.md`: fecha, comandos, resultados de 9.1, 9.2 y 9.6, la tabla de escenarios obligatorios de la consigna con su test (feliz: turno que termina justo cuando empieza el bloqueo; error de negocio: turno dentro de BL1; borde: último turno del domingo local dentro de BLV) y los desvíos del apply.
- [ ] 9.8 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal (más las evidencias) y no se hizo ningún commit.
