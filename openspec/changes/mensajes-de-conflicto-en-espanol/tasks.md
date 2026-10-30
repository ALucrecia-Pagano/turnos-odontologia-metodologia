# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Skills a cargar antes de escribir código: `tdd`, `python-testing-patterns` y `python-pro` (compact rules en `.atl/skill-registry.md`; la regla dura del proyecto prevalece: sin mocks en el dominio, sin `datetime.now()`, sin `Any`, y las reglas de negocio devuelven violaciones, no excepciones). El proyecto no usa `ruff` ni `black`: la verificación estática es `mypy --strict` (design D12).
>
> Reglas para todos los tests de dominio (design D10, igual que en C-02 a C-07): datos literales y ficticios (UUIDs fijos en constantes con nombre; `P1_NAME = "Dra. Laura Quiroga"`, `S1_NAME = "Sillón 1"`; `_at` en UTC del 2026-10-20 y `_local` en `America/Argentina/Buenos_Aires`); un `ZoneInfo` real; `now` siempre literal e inyectado; los instantes UTC de los intervalos esperados se escriben como literales de la spec, sin recalcular la conversión; sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre la lista completa de violaciones y sobre el texto exacto del mensaje. `pytest.raises` solo para errores de programación. Si un test pasa de entrada, comprobar que puede fallar con una mutación temporal del código, anotarla y restaurar.
>
> Governance **MEDIO**: el change tiene dos bloques. El **bloque A** (grupos 2 a 5) agrega el intervalo en conflicto sin cambiar ningún mensaje. La tarea **6.1** es un punto de control: no se empieza el **bloque B** (grupos 7 a 12: nombres y textos) sin la aprobación de la autora.

## 1. Red de seguridad

- [ ] 1.1 SAFETY NET: correr `pytest` y `mypy --strict app tests` antes de tocar nada y anotar el baseline (C-07 cerró con `330 passed` y `Success: no issues found in 31 source files`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.

## Bloque A — Intervalo en conflicto (sin cambiar mensajes)

## 2. `Violation.conflicting_interval` (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Spec: requisito "Contenido de cada violación" (regla del intervalo). Design D1.

- [ ] 2.1 RED: tabla en `test_violations.py` con `Violation(ViolationCode.CHAIR_OVERLAP, "choca")` → `conflicting_interval is None`, y con `conflicting_interval=Interval(_at(13), _at(13, 30))` → conserva ese intervalo (y con `Interval(2026-10-19T03:00:00+00:00, 2026-10-26T03:00:00+00:00)` → lo conserva sin recortar). Verificar que falla porque `Violation` no acepta el argumento (anotar el error).
- [ ] 2.2 GREEN: agregar `conflicting_interval: Interval | None = None` al final de `Violation`, importando `Interval` de `app.domain.intervals` (design D1). Verificar que pasan los tests nuevos, que la suite completa sigue en verde sin tocar ningún otro test y que `mypy` no tiene errores.
- [ ] 2.3 REFACTOR: docstring de `Violation` (`conflicting_interval`: en UTC, solo en `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` y `BLOCKED_TIME`, invariante "si y solo si hay id de turno o de bloqueo"; va al final para no cambiar las construcciones existentes) y fila de `violations` en `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 3. Intervalo en los solapamientos (`rules/overlap.py`)

> Tests en `tests/domain/test_validate_new_appointment.py`, con el helper `_conflicts(result)` (design D10). Spec: requisitos "Rechazo por solapamiento de profesional" y "Rechazo por solapamiento de sillón". Design D1.

- [ ] 3.1 RED: helper `_conflicts(result)` y escenario "Intervalo del turno con el que choca el profesional" en tabla: turno A (13:00–13:30 UTC) → `Interval(2026-10-20T13:00:00+00:00, 2026-10-20T13:30:00+00:00)`; turno de P1 en S1 de 13:00 a 14:00 → `Interval(2026-10-20T13:00:00+00:00, 2026-10-20T14:00:00+00:00)`; pedido de 30 minutos para P1 en S2 a las 13:15. Verificar que falla porque el intervalo es `None` (anotar la salida).
- [ ] 3.2 GREEN: `conflicting_interval=other.interval` en `check_professional_overlap`. Verificar que pasan los tests de 3.1 y que la suite sigue en verde.
- [ ] 3.3 RED → GREEN: escenarios "Intervalo del turno con el que choca el sillón" (P2 en S1 de 13:15 a 13:45 → `CHAIR_OVERLAP` con el id de A y `Interval(13:00, 13:30 UTC)`) y "Cada violación de solapamiento lleva el intervalo de su turno" (turnos B, C y D; pedido P1 en S1 de 13:00 a 14:00 → C `13:00–13:30`, B `13:30–14:00` y D `13:45–14:15`, en ese orden). Verificar que fallan en `CHAIR_OVERLAP` (anotar), cargar `conflicting_interval=other.interval` en `check_chair_overlap` y verificar en verde.
- [ ] 3.4 TRIANGULATE: escenario "Intervalo en UTC de un turno existente cargado en hora de Buenos Aires" (turno cargado `2026-10-20T10:00:00-03:00` a `10:30:00-03:00` → intervalo `2026-10-20T13:00:00+00:00` a `13:30:00+00:00`, con `utcoffset() == timedelta(0)` en los dos extremos). Comprobar con una mutación temporal (`candidate.interval` en lugar de `other.interval`) que fallan los tests de 3.1 a 3.4; anotar y restaurar. Verificar en verde.

## 4. Intervalo en los bloqueos (`rules/blocks.py`)

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Turno fuera de los bloqueos del profesional". Design D1 y D9.

- [ ] 4.1 RED: escenario "Intervalo del bloqueo con el que choca" (BL1; turno de 10:30 a 11:00 hora local = 13:30–14:00 UTC → `BLOCKED_TIME` con el id de BL1 e `Interval(2026-10-20T13:00:00+00:00, 2026-10-20T15:00:00+00:00)`). Verificar que falla porque el intervalo es `None`.
- [ ] 4.2 GREEN: en `check_blocks`, `conflicting_interval=Interval(block.start_at, block.end_at)` para cada bloqueo de `_overlapping_blocks`, sin agregar `Block.interval` (design D9). Verificar en verde, incluido el escenario "Bloqueo inválido recibido con la agenda" (`Ok`, sin excepción).
- [ ] 4.3 TRIANGULATE: escenarios "Intervalo de un bloqueo de varios días" (BLV; turno del martes de 10:00 a 10:30 hora local → `Interval(2026-10-19T03:00:00+00:00, 2026-10-26T03:00:00+00:00)`) y "Cada bloqueo con su intervalo" (BL1 y BL2; turno de 11:30 a 12:30 hora local → BL1 `13:00–15:00` y BL2 `14:00–16:00` UTC). Comprobar con una mutación temporal (recortar el intervalo al turno: `Interval(max(inicios), min(fines))`) que fallan los de BLV y de dos bloqueos; anotar y restaurar. Verificar en verde.
- [ ] 4.4 REFACTOR: docstring de `check_blocks` (`Returns`: con `conflicting_block_id` y `conflicting_interval` en UTC, completo aunque dure varios días) y de `check_professional_overlap` / `check_chair_overlap` (`Returns` con el intervalo del turno existente). Verificar `pytest` y `mypy` en verde.

## 5. Invariante y violaciones sin intervalo

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Contenido de cada violación". Design D1.

- [ ] 5.1 TRIANGULATE: escenario "Violaciones sin intervalo en conflicto" en tabla con sus siete casos (`OUTSIDE_WORKING_HOURS` con `TUESDAY_BASE` de 12:30 a 13:30 hora local; `INVALID_DURATION` con 7 minutos; `INVALID_START_TIME` a las 10:03 hora local; `CROSSES_MIDNIGHT` a las 23:30 hora local con 60 minutos; `IN_THE_PAST` con `now` 10:00 hora local e inicio 09:55; `UNKNOWN_REFERENCE` con S2 inexistente; `INACTIVE_REFERENCE` con P1 inactivo) → cada una sin intervalo ni ids en conflicto. Pasan de entrada: comprobar con una mutación temporal (cargar `Interval(start_at, end_at)` del turno en `OUTSIDE_WORKING_HOURS`) que falla el primer caso; anotar y restaurar.
- [ ] 5.2 TRIANGULATE: escenario "Intervalo si y solo si hay un turno o un bloqueo en conflicto" (`TUESDAY_BASE`, BL3, E y F; pedido de 12:30 a 13:30 hora local, 60 minutos) → cuatro violaciones en orden con sus ids e intervalos (`BLOCKED_TIME` BL3 `15:00–17:00`, `PROFESSIONAL_OVERLAP` E `15:30–16:00`, `CHAIR_OVERLAP` F `15:45–16:15` UTC; `OUTSIDE_WORKING_HOURS` sin intervalo), más la aserción general de la invariante sobre cada violación. Comprobar con una mutación temporal (sin intervalo en `CHAIR_OVERLAP`) que falla; anotar y restaurar. Verificar `pytest` y `mypy` en verde.

## 6. Punto de control

- [ ] 6.1 ⛔ **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** Correr la suite completa y `mypy --strict app tests` y anotar la salida. Comprobar con `git diff` que el bloque A no cambió ningún mensaje ni ningún test de texto exacto existente. Presentarle a la autora: (a) `Violation.conflicting_interval` y su docstring (design D1); (b) dónde se carga y dónde no, con la invariante (D1, D9); (c) el intervalo completo del bloqueo de varios días (D9); (d) los tests de los grupos 2 a 5, con sus rojos y sus mutaciones; (e) la salida de `pytest` y `mypy`; y (f) para confirmar antes del bloque B: el orden de los campos de `Professional` y `Chair` (D2), el nombre sin recortar en los mensajes (D6 y Risks), las firmas de las reglas (D7) y la verificación solo con `mypy` (D12). Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` (y la spec si cambia un comportamiento) y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha.

## Bloque B — Nombres y textos (solo con la aprobación de 6.1)

## 7. Nombres en el modelo y migración de los tests (`model.py`)

> Tests en `tests/domain/test_model.py` y `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Nombre del profesional y del sillón". Design D2 y D10.

- [ ] 7.1 RED: en `test_model.py`, escenarios "Profesional y sillón con nombre" (`Professional(P1, full_name="Dra. Laura Quiroga", active=True)` y `Chair(S1, name="Sillón 1", active=True)` conservan nombre, id y `active`) y "Nombre vacío o en blanco al construir" (tabla con `""` y `"   "` para los dos: no lanza y conserva el valor sin recortar). Verificar que fallan porque las entidades no aceptan el argumento (anotar el error).
- [ ] 7.2 GREEN: agregar `full_name: str` a `Professional` y `name: str` a `Chair`, entre `id` y `active` y sin valor por defecto (design D2). Verificar que pasan los tests de 7.1 y que `mypy` marca los 12 constructores de `test_validate_new_appointment.py` (falta el argumento); anotar los errores.
- [ ] 7.3 Migrar los tests: constantes `P1_NAME = "Dra. Laura Quiroga"`, `S1_NAME = "Sillón 1"`, `OTHER_PROFESSIONAL_NAME = "Dr. Martín Sosa"` y `OTHER_CHAIR_NAME = "Sillón 2"`, y el nombre en los 6 `Professional(...)` y los 6 `Chair(...)` (los de `_refs` con `P1_NAME` y `S1_NAME`). No cambiar ninguna llamada ni aserción. Verificar con `git diff` que solo cambian esas líneas y las constantes, `pytest` con el baseline del punto de control más los tests nuevos (los mensajes todavía no cambian) y `mypy` en verde. Actualizar el ejemplo de `backend/README.md` §Dominio (`full_name` y `name`, con nombres ficticios) y correrlo una vez en el venv para verificar que coincide con la firma real.
- [ ] 7.4 REFACTOR: docstrings de `Professional` y `Chair` (`full_name` / `name`: obligatorios, sin valor por defecto, no se validan ni se recortan al construir; los usa el mensaje de los conflictos de agenda; la validez del nombre es del alta del catálogo) y fila de `model` en `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 8. Sustituto genérico del nombre (`rules/names.py`)

> Tests en `tests/domain/test_names.py` (nuevo). Spec: requisito "Contenido de cada violación" (nombre vacío o en blanco). Design D6.

- [ ] 8.1 RED: `subject_name("Dra. Laura Quiroga", "El profesional") == "Dra. Laura Quiroga"` y `subject_name("", "El profesional") == "El profesional"`. Verificar que falla porque `app.domain.rules.names` no existe (anotar el error).
- [ ] 8.2 GREEN → TRIANGULATE: crear `rules/names.py` con `subject_name(name, generic) -> str` (`name` si `name.strip()`, si no `generic`). Sumar a la tabla `"   "` → genérico, `"\t \n"` → genérico, `"Sillón 1"` con `"El sillón"` → `"Sillón 1"`, `""` con `"el profesional"` → `"el profesional"` y `"  Dra. Laura Quiroga "` → el mismo texto, sin recortar. Comprobar con una mutación temporal (`if name` en lugar de `if name.strip()`) que fallan los casos en blanco; anotar y restaurar. Verificar en verde y que `test_domain_dependencies.py` sigue en verde.
- [ ] 8.3 REFACTOR: docstrings estilo Google del módulo y de `subject_name` (US-006 CA-3; el nombre se muestra tal como se cargó; el genérico lo elige el llamador según el lugar en la oración). Agregar `names` a la fila de `rules/` de `backend/README.md`. Verificar `pytest` y `mypy` en verde.

## 9. Mensajes de solapamiento (`rules/overlap.py` y cableado en `validate.py`)

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Contenido de cada violación". Design D3, D6, D7 y D8.

- [ ] 9.1 RED: reescribir `test_validate_new_appointment_overlap_messages_name_resource_and_conflicting_id` con el escenario "Mensajes de las violaciones de solapamiento": textos exactos `f"Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno {APPT_A})."` y `f"Sillón 1 está ocupado de 10:00 a 10:30 (hora local) por un turno que se superpone (turno {APPT_A})."`, sin `13:00`, `13:30` ni `10:15`. Verificar que falla con el mensaje viejo (anotar la salida).
- [ ] 9.2 GREEN: firmas de design D7 en `check_professional_overlap` y `check_chair_overlap` (`tz` y el nombre al final, sin default) y mensajes de design D3 con `format_local_time` sobre el turno existente. En `validate.py`, `_agenda_conflict_violations` recibe `professional_name` y `chair_name` y pasa `context.tz`; `validate_new_appointment` acota `references.professional` y `references.chair` con la condición de design D8 y pasa `full_name` y `name`. Verificar que pasa 9.1, que la suite sigue en verde y que `mypy` no tiene errores.
- [ ] 9.3 TRIANGULATE: escenario "Mensaje de solapamiento con un turno existente con segundos" (turno G de P1 en S2 de 13:00:30 a 13:30:30 UTC → `"Dra. Laura Quiroga ya tiene un turno de 10:00:30 a 10:30:30 (hora local) que se superpone (turno {G})."`). Comprobar con mutaciones temporales que fallan los tests de 9.1 y 9.3 si el rango es el del turno pedido (`candidate`) y si se formatea en UTC; anotar y restaurar. Verificar en verde.
- [ ] 9.4 RED → GREEN: escenario "Mensajes de solapamiento con el nombre vacío o en blanco" (tabla con `""` y `"   "` en P1 y S1 → `"El profesional ya tiene un turno de 10:00 a 10:30 (hora local) …"` y `"El sillón está ocupado de 10:00 a 10:30 (hora local) …"`). Verificar que falla (anotar), usar `subject_name` con `"El profesional"` / `"El sillón"` como constantes `Final` y verificar en verde.
- [ ] 9.5 REFACTOR: el armado de cada mensaje en un helper privado si mejora la lectura; docstrings de las dos reglas (`Args` con `tz` y el nombre) y de `_agenda_conflict_violations` y `validate_new_appointment` (nombres que salen de `references`; comentario de la condición de D8). Verificar `pytest` y `mypy` en verde.

## 10. Mensaje fuera de horario (`rules/working_hours.py`)

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Turno dentro del horario de atención". Design D3, D6 y D7.

- [ ] 10.1 RED: reescribir los tres tests de texto exacto de C-05 (líneas 1134, 1148 y 1159) con los escenarios "Mensaje de un turno fuera de los tramos del día" (`"…queda fuera del horario de atención: Dra. Laura Quiroga atiende el martes de 09:00 a 13:00 y de 15:00 a 19:00."`, sin intervalo ni ids en conflicto), "Mensaje de un turno en un día sin tramos" (`"…: Dra. Laura Quiroga no atiende los domingos."`) y "Mensaje con tramos contiguos y un tramo hasta la medianoche" (`"…: Dra. Laura Quiroga atiende el martes de 09:00 a 17:00 y de 20:00 a 24:00."`). Verificar que fallan con el texto viejo (anotar).
- [ ] 10.2 GREEN: `check_working_hours` recibe `professional_name` al final (design D7) y `_outside_message` arma el texto de design D3; `validate.py` le pasa `full_name`. Verificar que pasan los tres y que la suite sigue en verde.
- [ ] 10.3 RED → GREEN: escenarios "Mensaje fuera de horario con el nombre vacío o en blanco" y "Mensaje de un día sin tramos con el nombre vacío o en blanco" (tabla con `""` y `"   "` → `"…: el profesional atiende el martes …"` y `"…: el profesional no atiende los domingos."`, en minúscula). Verificar que fallan (anotar), usar `subject_name` con `"el profesional"` y verificar en verde. Comprobar con una mutación temporal (genérico con mayúscula) que fallan; anotar y restaurar.
- [ ] 10.4 REFACTOR: docstrings de `check_working_hours` y `_outside_message` (nombre como sujeto, sustituto en minúscula). Verificar `pytest` y `mypy` en verde.

## 11. Mensaje de bloqueo (`rules/blocks.py`)

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Mensaje de un turno bloqueado". Design D3, D6 y D7.

- [ ] 11.1 RED: reescribir los tres tests de texto exacto de C-06 (líneas 1353, 1368 y 1384) con los escenarios "Mensaje de un bloqueo sin motivo" (`f"…se superpone con un bloqueo de agenda: Dra. Laura Quiroga tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {BL1})."`), "Mensaje de un bloqueo de varios días con motivo" (`f"…del 19/10/2026 00:00 al 26/10/2026 00:00 (hora local) (bloqueo {BLV}). Motivo: vacaciones."`, sin `02:30` ni `03:00`) y "Mensaje de un bloqueo con motivo vacío o en blanco" (igual al sin motivo, terminado en `(bloqueo {BL1}).`). Verificar que fallan con el texto viejo (anotar).
- [ ] 11.2 GREEN: `check_blocks` recibe `professional_name` al final (design D7) y `_blocked_message` arma el texto de design D3, con la misma regla del motivo; `validate.py` le pasa `full_name`. Verificar que pasan los tres y que la suite sigue en verde.
- [ ] 11.3 RED → GREEN: escenario "Mensaje de un bloqueo con el nombre vacío o en blanco" (tabla con `""` y `"   "` → `"…: el profesional tiene la agenda bloqueada del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local) (bloqueo {BL1})."`). Verificar que falla (anotar), usar `subject_name` con `"el profesional"` y verificar en verde.
- [ ] 11.4 REFACTOR: docstrings de `check_blocks` y `_blocked_message` (nombre como sujeto; id del bloqueo al final; motivo sin cambios). Verificar `pytest` y `mypy` en verde.

## 12. Composición y mensajes que no cambian

> Tests en `tests/domain/test_validate_new_appointment.py`. Spec: requisito "Contenido de cada violación". Design D3 y D8.

- [ ] 12.1 TRIANGULATE: escenario "Mensajes completos de un rechazo con todos los conflictos de agenda" (`TUESDAY_BASE`, BL3, E y F; pedido de 12:30 a 13:30 hora local → los cuatro textos exactos de la spec, en orden). Pasa de entrada: comprobar con una mutación temporal (pasar `chair_name` como nombre del profesional en `validate.py`) que falla; anotar y restaurar.
- [ ] 12.2 TRIANGULATE: escenario "Mensaje de una referencia inactiva con nombre" (P1 inactivo → `f"El profesional indicado está inactivo (id {P1})."`; S1 inactivo → `f"El sillón indicado está inactivo (id {S1})."`; sin `"Dra. Laura Quiroga"` ni `"Sillón 1"`). Pasa de entrada porque `rules/references.py` no cambia: comprobar con una mutación temporal (agregar el nombre al mensaje de `INACTIVE_REFERENCE`) que falla; anotar y restaurar. Verificar con `git diff` que `rules/references.py`, `duration.py`, `start_time.py`, `same_day.py` y `past.py` no cambiaron.
- [ ] 12.3 REFACTOR: buscar en `app/domain` y `tests/domain` menciones a "C-08" como trabajo futuro y quitarlas; actualizar en `backend/README.md` el párrafo de los grupos (mensajes con nombre y rango local, intervalo en conflicto). Verificar `pytest` y `mypy` en verde.

## 13. Verificación integral y evidencias

- [ ] 13.1 Desde `backend/`: `pytest -v` en verde (más tests que el baseline de 1.1), con la salida completa guardada en `docs/evidencias/pytest-C-08.txt`.
- [ ] 13.2 Desde `backend/`: `mypy --strict app tests` con `Success: no issues found` (dos archivos más que en C-07: `rules/names.py` y `tests/domain/test_names.py`), con la salida guardada en `docs/evidencias/mypy-C-08.txt`.
- [ ] 13.3 Trazabilidad: cada uno de los 96 escenarios de `specs/appointment-scheduling/spec.md` de este change (18 nuevos, 7 con texto modificado y 71 que ya existían en los requisitos modificados) tiene al menos un test, y los escenarios de C-01 a C-07 que no toca este change siguen cubiertos. Dejar la tabla escenario → test en `docs/evidencias/verify-C-08.md`, con los seis textos exactos de C-05 y C-06 que cambiaron marcados.
- [ ] 13.4 Pureza del dominio: `find_forbidden_imports` y `find_global_clock_calls` sin resultados sobre `app/domain` (tests de C-01 y C-07 en verde); buscar además en `app/domain` `uuid1`, `uuid4`, `Any`, `os.environ`, `getenv`, `"America/` y `raise`. No debe haber coincidencias nuevas: `rules/names.py` no lanza y `check_blocks` solo construye `Interval` con bloqueos que se solapan (design D9).
- [ ] 13.5 Verificar que `knowledge-base/04`, `05`, `06` y `09` y `CHANGES.md` §[C-08] coinciden con lo implementado (`full_name` y `name` de KB 04, RN-AG-12, US-006 CA-1 a CA-3, DD-08). Ajustar solo si el apply se desvió, con el OK de la autora. El estado `[x]` se marca en el archive, no acá.
- [ ] 13.6 `openspec validate mensajes-de-conflicto-en-espanol --strict` desde la raíz → "is valid".
- [ ] 13.7 Escribir `docs/evidencias/verify-C-08.md` con el formato de `verify-C-07.md`: fecha, comandos, resultados de 13.1, 13.2 y 13.6, la tabla de escenarios obligatorios de la consigna con su test (feliz: "Mensajes de las violaciones de solapamiento"; error de negocio: "Mensajes completos de un rechazo con todos los conflictos de agenda"; borde: "Mensajes de solapamiento con el nombre vacío o en blanco"), la tabla de 13.3 y los desvíos del apply.
- [ ] 13.8 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal (más las evidencias) y no se hizo ningún commit.
