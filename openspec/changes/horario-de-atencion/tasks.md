# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Skills a cargar antes de escribir código: `tdd`, `python-testing-patterns` y `python-pro` (compact rules en `.atl/skill-registry.md`; la regla dura del proyecto prevalece: sin mocks en el dominio, sin `datetime.now()`, sin `Any`, y las reglas de negocio devuelven violaciones, no excepciones). El proyecto no usa `ruff` ni `black`: la verificación estática es `mypy --strict`.
>
> Reglas para todos los tests de dominio (design D11, igual que en C-02 a C-04): datos literales (UUIDs fijos en constantes con nombre; `_at` en UTC del 2026-10-20 y `_local` en `America/Argentina/Buenos_Aires`); un `ZoneInfo` real; los instantes UTC esperados se escriben como literales de la spec, sin recalcular la conversión; los tramos en minutos literales (`540`, no `9 * 60`); sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre la lista completa de violaciones (código y orden). `pytest.raises` solo para errores de programación (`ValueError`).
>
> Governance **MEDIO**: la tarea **3.5** es un punto de control. No se implementa ninguna regla (grupos 4 en adelante) sin la aprobación de la autora.

## 1. Red de seguridad

- [ ] 1.1 SAFETY NET: correr `pytest` y `mypy` antes de tocar nada y anotar el baseline (C-04 cerró con 181 tests y `Success: no issues found in 24 source files`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.

## 2. Códigos nuevos (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Design D8.

- [ ] 2.1 RED: agregar a la tabla de `ViolationCode` → valor serializado los casos `OUTSIDE_WORKING_HOURS`, `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` (valor igual al nombre). Verificar que fallan porque los miembros no existen.
- [ ] 2.2 GREEN: sumar los tres códigos a `ViolationCode`. Verificar `pytest` y `mypy` en verde.

## 3. Modelo de tramos, contexto, migración de `CTX` y punto de control

> Tests en `tests/domain/test_model.py` y `tests/domain/test_validate_new_appointment.py`. Design D1, D5 y D11.

- [ ] 3.1 RED: en `test_model.py`, test de `WorkingHours(professional_id, weekday, start_minute, end_minute)`: se construye con `(P1, 2, 540, 780)` y conserva los cuatro valores, y se construye **sin lanzar** con valores inválidos (`(P1, 0, 800, 700)` y `(P1, 8, -5, 1445)`), porque la validez es de `validate_working_hours` (design D5). Verificar que falla porque `WorkingHours` no existe.
- [ ] 3.2 GREEN: en `model.py`, agregar `WorkingHours` *frozen* con slots, sin `__post_init__`, con docstring estilo Google (día ISO 1 = lunes … 7 = domingo, minutos locales, 1440 = 24:00; citar RN-DI-01 y KB 04). Verificar en verde y `mypy` en verde.
- [ ] 3.3 Agregar `working_hours: tuple[WorkingHours, ...]` a `ScheduleContext`, después de `tz` y sin valor por defecto (design D1), y actualizar su docstring. Verificar que `mypy` marca la construcción actual de `CTX` en `test_validate_new_appointment.py` (falta el argumento) y anotar el error.
- [ ] 3.4 Migrar `CTX` en `test_validate_new_appointment.py`: `FULL_WEEK = tuple(WorkingHours(p, d, 0, 1440) for p in (P1, P2) for d in range(1, 8))` y `CTX = ScheduleContext(tz=BUENOS_AIRES, working_hours=FULL_WEEK)` (design D11, decisión 6 del explore). No cambiar ninguna llamada ni aserción. Verificar con `git diff` que solo cambian el import y esas líneas, `pytest` con el baseline de 1.1 más los tests nuevos, todo en verde, y `mypy` en verde. Actualizar el ejemplo de `backend/README.md` §Dominio con `WorkingHours` y el contexto con tramos, y correrlo una vez en el venv para verificar que coincide con la firma real.
- [ ] 3.5 ⛔ **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** No seguir con el grupo 4 hasta que la autora apruebe. Presentarle: (a) `WorkingHours` y su ubicación en `model.py`, sin validación al construirse (design D5); (b) `ScheduleContext` con `working_hours` obligatorio (design D1); (c) los tres códigos nuevos (design D8); (d) las firmas de `check_working_hours` y `validate_working_hours` y el módulo `rules/working_hours.py` (design D7); (e) el orden y la exclusión de `validate_working_hours` (design D8); (f) el texto de los mensajes, incluidos los tramos unidos y el `24:00` (design D6 y D9); (g) el diff de la migración de `CTX`; (h) la salida de `pytest` y `mypy`. Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` (y la spec si cambia un comportamiento) y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha.

## 4. Validez de un conjunto de tramos (`rules/working_hours.py`, RN-DI-01, RN-DI-02)

> Solo si la autora aprobó en 3.5. Tests en `tests/domain/test_working_hours.py` (nuevo). Spec: requisito "Validez de un conjunto de tramos". Design D5, D8 y D9.

- [ ] 4.1 RED: escenario "Tramos con inicio igual o posterior al fin" (`[780, 780)` y `[800, 700)` del martes → exactamente `[INVALID_WORKING_HOURS, INVALID_WORKING_HOURS]`). Verificar que falla porque `validate_working_hours` no existe.
- [ ] 4.2 GREEN: crear `rules/working_hours.py` con `validate_working_hours(slots) -> list[Violation]` que informa `inicio >= fin` (con un mensaje mínimo). Verificar en verde y que `test_domain_dependencies.py` sigue en verde.
- [ ] 4.3 TRIANGULATE: tabla de "Varios tramos válidos el mismo día" (`[540, 780)` y `[900, 1140)` → `[]`) y "Límites del día y valores fuera de rango" (`[1200, 1440)` → `[]`; `[-5, 60)`, `[0, 1445)`, `[540, 780)` con día 0 y con día 8 → exactamente una `INVALID_WORKING_HOURS` cada uno). Un tramo que rompe dos condiciones (día 8 y `[800, 700)`) → una sola violación. Verificar que falla antes (los rangos) y en verde después.
- [ ] 4.4 RED → GREEN: escenario "Tramos solapados el mismo día" (`[540, 780)` y `[720, 900)` → exactamente `[OVERLAPPING_WORKING_HOURS]`). Implementar la búsqueda por pares de design D8 (mismo profesional, mismo día, semiabiertos). Verificar que falla antes y en verde después.
- [ ] 4.5 TRIANGULATE: tabla de "Los mismos tramos en días distintos", "Tramos contiguos" (`[540, 780)` y `[780, 1020)`) y "Tramos solapados de profesionales distintos" → `[]` los tres. Verificar en verde; si alguno pasa de entrada, comprobar que puede fallar quitando temporalmente la condición correspondiente (día, `<` estricto o profesional), anotarlo y restaurar.
- [ ] 4.6 RED → GREEN: escenario "Orden de las violaciones de un conjunto" (`[540, 780)`, `[750, 750)`, `[720, 900)`, `[600, 660)` → exactamente `[INVALID_WORKING_HOURS (tramo 2), OVERLAPPING_WORKING_HOURS (1 y 3), OVERLAPPING_WORKING_HOURS (1 y 4)]`, verificando las posiciones por el mensaje). Si falla por el orden o porque el tramo 2 aparece en un par, ajustar según design D8. Verificar en verde.
- [ ] 4.7 RED → GREEN: mensajes de design D9: en "Tramos con inicio igual o posterior al fin", el primer mensaje contiene `"tramo 1"` y el segundo `"tramo 2"`, sin `conflicting_appointment_id` ni `reference_kind`; en "Tramos solapados el mismo día", el mensaje contiene `"tramos 1 y 2"` y `"martes"`. Verificar que falla antes (mensaje mínimo) y en verde después.
- [ ] 4.8 REFACTOR: docstrings estilo Google en el módulo y en `validate_working_hours` (citar RN-DI-01, RN-DI-02 y US-010), nombres de los días como constantes `Final`, y razones como constantes si se repiten. Verificar `pytest` y `mypy` en verde.

## 5. Turno dentro del horario de atención (`rules/working_hours.py` y `validate.py`, RN-AG-04)

> Tests en `tests/domain/test_validate_new_appointment.py`, con `TUESDAY_BASE` y el helper `_ctx(*slots)` (design D11). Spec: requisito "Turno dentro del horario de atención". Design D2, D3, D4 y D7.

- [ ] 5.1 RED: escenario "Turno que empieza dentro y termina después del fin del tramo" (`_local(20, 12, 30)`, explícita 60, `_ctx(*TUESDAY_BASE)` → exactamente `[OUTSIDE_WORKING_HOURS]`). Verificar que falla (hoy devuelve `Ok`).
- [ ] 5.2 GREEN: en `rules/working_hours.py`, `check_working_hours(professional_id, start_at, end_at, working_hours, tz) -> list[Violation]` con el filtro por profesional y día local, los minutos de design D4 y la contención en un tramo (todavía sin unir contiguos). Llamarla primera en `_agenda_conflict_violations`, que pasa a recibir el contexto (design D2). Verificar en verde y que la suite completa sigue en verde con `CTX` de día completo.
- [ ] 5.3 TRIANGULATE: tabla de aceptaciones con `TUESDAY_BASE`: "Turno completo dentro de un tramo" (10:00–10:30 → `Ok` de `2026-10-20T13:00:00+00:00` a `2026-10-20T13:30:00+00:00`), "Turno que empieza justo al inicio del tramo" (09:00), "Turno que termina justo al fin del tramo de la mañana" (12:30–13:00) y "…de la tarde" (18:30–19:00). Si un borde falla, corregir `<` / `<=`. Verificar en verde.
- [ ] 5.4 TRIANGULATE: tabla de rechazos con `TUESDAY_BASE`: 08:30–09:30, 13:00–15:00, 14:00–14:30, 12:30–15:30 y el domingo `_local(25, 10, 0)` 10:00–10:30 → exactamente `[OUTSIDE_WORKING_HOURS]` cada uno. Verificar en verde.
- [ ] 5.5 TRIANGULATE: hora local (US-004 CA-7): "Instante UTC dentro del tramo que en hora local queda fuera" (06:00 local, `2026-10-20T09:00:00+00:00` → rechazo) y "Instante UTC fuera del tramo que en hora local queda dentro" (18:00 local, `2026-10-20T21:00:00+00:00` → `Ok`), con los instantes escritos como literales UTC. Anotar en el resumen del apply que se comprobó que fallan evaluando en UTC (cambiar temporalmente la zona de `_ctx` a UTC) y restaurar. Verificar en verde.
- [ ] 5.6 TRIANGULATE: día de la semana local y medianoche: "El día de la semana es el local, no el de UTC" (tramo `[1200, 1380)` el miércoles; martes 22:00 local → rechazo), "Turno del martes local que en UTC cae el miércoles" (el mismo tramo el martes → `Ok`) y "Turno que termina a la medianoche local, al fin del tramo" (`[1200, 1440)` el martes; 23:30–00:00 → `Ok` hasta `2026-10-21T03:00:00+00:00`). Si el último falla, aplicar el fin 1440 de design D4. Verificar en verde.
- [ ] 5.7 TRIANGULATE: "Tramo de otro profesional" (tramo de P2 `[540, 780)` el martes, pedido de P1 10:00–10:30 → rechazo). Comprobar que falla si se quita temporalmente el filtro por profesional; anotarlo y restaurar. Verificar en verde.
- [ ] 5.8 RED → GREEN: "Turno que pasa de un tramo a otro contiguo" (`[540, 780)` y `[780, 1020)`; 12:30–13:30 → `Ok`). Verificar que falla antes (rechazo) e implementar la unión de design D3 (`_merged_slots`). Verificar en verde, incluidos 5.3 a 5.7.
- [ ] 5.9 REFACTOR: docstrings estilo Google en `check_working_hours` y `_merged_slots` (citar RN-AG-04, RN-GL-03 y DD-07) y en `_agenda_conflict_violations` y `validate_new_appointment` (el grupo 2 es "conflictos de agenda": horario → profesional → sillón; `context.working_hours`). Verificar `pytest` y `mypy` en verde después de cada paso.

## 6. Mensaje de `OUTSIDE_WORKING_HOURS`

> Spec: escenarios de mensaje del requisito "Turno dentro del horario de atención". Design D6.

- [ ] 6.1 RED: "Mensaje de un turno fuera de los tramos del día" (12:30–13:30 con `TUESDAY_BASE` → mensaje exacto de la spec, `conflicting_appointment_id is None` y `reference_kind is None`). Verificar que falla por el texto.
- [ ] 6.2 GREEN: armar el mensaje con `format_local_time` para el turno, `_format_minute` para los tramos y la tupla de días en singular. Verificar en verde.
- [ ] 6.3 TRIANGULATE: "Mensaje de un turno en un día sin tramos" (domingo 10:00–10:30 → mensaje exacto con `"no atiende los domingos"`, tupla en plural) y "Mensaje con tramos contiguos y un tramo hasta la medianoche" (tramos recibidos desordenados; 17:30–18:00 → mensaje exacto con `"de 09:00 a 17:00 y de 20:00 a 24:00"`). Si falla, mostrar los tramos unidos y ordenados y el minuto 1440 como `24:00`. Verificar en verde.
- [ ] 6.4 REFACTOR: unir los tramos con `", "` y `" y "` en un helper privado; constantes `Final` para los días. Verificar `pytest` y `mypy` en verde.

## 7. Orden de las violaciones y corte del grupo 1

> Spec: escenarios nuevos de "Todas las violaciones, en orden estable". Design D2.

- [ ] 7.1 RED → GREEN: "Fuera de horario y solapado a la vez" (B de P1/S1 de 12:30 a 13:30 local; pedido P1/S1 12:45–13:15 local con `TUESDAY_BASE` → exactamente `[OUTSIDE_WORKING_HOURS, PROFESSIONAL_OVERLAP (B), CHAIR_OVERLAP (B)]`). Si pasa de entrada por la llamada de 5.2, comprobar que puede fallar moviendo temporalmente la regla al final del grupo 2, anotarlo y restaurar. Verificar en verde.
- [ ] 7.2 TRIANGULATE: "Duración inválida en un día sin horario" (domingo 10:00 local, explícita 7 → exactamente `[INVALID_DURATION]`) e "Inicio fuera de la grilla en un día sin horario" (domingo 10:03 local → exactamente `[INVALID_START_TIME]`), con `TUESDAY_BASE`. Pasan por el corte del grupo 1; anotarlo. Verificar en verde.

## 8. Documentación

- [ ] 8.1 `backend/README.md` §Dominio: sumar `WorkingHours` y `working_hours` a la fila de `model`, `working_hours` (horario y validez de los tramos) a la de `rules/`, y actualizar el párrafo de los grupos (grupo 2, conflictos de agenda: horario → profesional → sillón). Verificar que el ejemplo sigue coincidiendo con la firma real (correrlo una vez en el venv).
- [ ] 8.2 Verificar que `knowledge-base/07_flujos_principales.md` tiene `INVALID_WORKING_HOURS` y `OVERLAPPING_WORKING_HOURS` en el catálogo, que RN-AG-04 de `knowledge-base/05_reglas_de_negocio.md` habla de los tramos contiguos y que `CHANGES.md` §[C-05] coincide con lo implementado (se actualizaron después del explore). Ajustar solo si el apply se desvió, con el OK de la autora. El estado `[x]` se marca en el archive, no acá.
- [ ] 8.3 Proponerle a la autora actualizar en el archive el Purpose de `openspec/specs/appointment-scheduling/spec.md` (horario de atención, validez de los tramos y la convención de días ISO y tramos en minutos). Editar solo con su aprobación y anotar la decisión.

## 9. Verificación integral y evidencias

- [ ] 9.1 Desde `backend/`: `pytest -v` en verde (más tests que el baseline de 1.1), con la salida completa guardada en `docs/evidencias/pytest-C-05.txt`.
- [ ] 9.2 Desde `backend/`: `mypy` con `Success: no issues found` sobre `app` y `tests` (dos archivos más que en C-04: `rules/working_hours.py` y `tests/domain/test_working_hours.py`), con la salida guardada en `docs/evidencias/mypy-C-05.txt`.
- [ ] 9.3 Trazabilidad: cada uno de los 45 escenarios de `specs/appointment-scheduling/spec.md` de este change (31 nuevos y 14 que ya existían en los requisitos modificados) tiene al menos un test (función o caso parametrizado), y los escenarios de C-02 a C-04 que no toca este change siguen cubiertos. Dejar la tabla escenario → test en el resumen del apply.
- [ ] 9.4 Pureza del dominio: buscar en `app/domain` `datetime.now`, `utcnow`, `time.time`, `uuid1`, `uuid4`, `Any`, `os.environ`, `getenv`, `"America/` y `raise`. No debe haber ninguna coincidencia nueva: `rules/working_hours.py` no lanza excepciones (las reglas de tramos son violaciones). `test_domain_dependencies.py` en verde (la allowlist no cambia).
- [ ] 9.5 `openspec validate horario-de-atencion --strict` desde la raíz → "is valid".
- [ ] 9.6 Escribir `docs/evidencias/verify-C-05.md` con el mismo formato que `verify-C-04.md`: fecha, comandos, resultados de 9.1, 9.2 y 9.5, la tabla de escenarios obligatorios de la consigna con su test (al menos uno feliz: 10:00–10:30; uno de error de negocio: 12:30–13:30 fuera de horario; y uno de borde: 06:00 local que en UTC parecería dentro, o tramos contiguos) y los desvíos del apply.
- [ ] 9.7 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal (más las evidencias) y no se hizo ningún commit.
