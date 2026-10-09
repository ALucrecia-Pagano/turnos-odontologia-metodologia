# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Reglas para todos los tests de dominio (design D8): datos literales (UUIDs fijos en constantes con nombre `P1`, `P2`, `S1`, `S2`, `S3`, `APPT_A`, …; instantes del 2026-10-20 en UTC); sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre código, id y orden completo de las violaciones. `pytest.raises` solo para errores de programación (`ValueError`).
>
> Governance **ALTO**: la tarea **4.3** es un punto de control obligatorio. No se implementa ninguna regla (grupos 5 en adelante) sin la aprobación de la autora.

## 1. Guardia de dependencias: `uuid` en la allowlist

- [x] 1.1 SAFETY NET: correr `pytest` y `mypy` antes de tocar nada y anotar el baseline ("N tests pasando", `Success: no issues found`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.
- [x] 1.2 RED: en `tests/domain/test_import_guard.py`, agregar `import uuid` y `from uuid import UUID` a la tabla parametrizada de imports permitidos (spec `domain-dependency-guard`, escenario "Import del tipo de identificador"); verificar que esos 2 casos fallan con una violación `uuid`.
- [x] 1.3 GREEN: agregar `"uuid"` a `DOMAIN_ALLOWED_MODULES` en `tests/domain/import_guard.py`, en orden alfabético (design D2); verificar que los casos nuevos pasan y que el baseline sigue verde.
- [x] 1.4 TRIANGULATE: agregar `import uuid_utils` a la tabla de prohibidos (exactamente una violación con `module == "uuid_utils"`, para comprobar que se compara el primer segmento exacto); verificar `pytest` y `mypy` en verde.

## 2. Modelo: instantes con zona horaria (`model.py`)

> Tests en `tests/domain/test_model.py`. Spec: requisito "Instantes con zona horaria y normalizados a UTC". Design D3 y D4.

- [x] 2.1 RED: test `NewAppointmentRequest` con `start_at=datetime(2026, 10, 20, 13, 0)` (sin zona) → `pytest.raises(ValueError, match="zona horaria")`; verificar que falla porque `app.domain.model` no existe.
- [x] 2.2 GREEN: crear `app/domain/model.py` con `AppointmentStatus` (miembros en inglés y valores `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`), `NewAppointmentRequest` *frozen* con slots (`id`, `patient_id`, `professional_id`, `chair_id`, `start_at`, `duration_min: int | None = None`) y `_to_utc` aplicado en `__post_init__`; verificar en verde.
- [x] 2.3 RED → GREEN: test `Appointment` con `start_at` sin zona y con `end_at` sin zona (parametrizado, 2 casos) → `ValueError`; agregar `Appointment` *frozen* con slots (`id`, `patient_id`, `professional_id`, `chair_id`, `service_id`, `start_at`, `end_at`, `status`) aplicando `_to_utc` a ambos instantes; verificar en verde.
- [x] 2.4 TRIANGULATE (normalización): tabla con el pedido y con el turno, con instantes en `-03:00` (`2026-10-20T10:00-03:00` → `2026-10-20T13:00+00:00`) y en UTC (sin cambios). Aserta el valor exacto **y** que `utcoffset() == timedelta(0)`; verificar en verde.
- [x] 2.5 RED → GREEN: `Appointment` con `start_at == end_at` y con `start_at > end_at` (2 casos) → `ValueError` (invariante de D4); verificar en verde.
- [x] 2.6 REFACTOR: docstrings estilo Google en las clases públicas. El docstring del módulo dice que los ids los inyecta el llamador y que el dominio nunca llama a `uuid4()` (design D2). Verificar `pytest` y `mypy` en verde.

## 3. Violaciones y resultado tipado (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Design D5.

- [x] 3.1 RED: test `Rejected(violations=())` → `pytest.raises(ValueError)`; verificar que falla porque `app.domain.violations` no existe.
- [x] 3.2 GREEN: crear `violations.py` con `ViolationCode` (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, cada valor igual a su nombre), `Violation` (`code`, `message`, `conflicting_appointment_id: UUID | None = None`), `Ok(appointment)`, `Rejected(violations: tuple[Violation, ...])` con la invariante de no vacío y `ValidationResult: TypeAlias = Ok | Rejected`, todos *frozen* con slots; verificar en verde.
- [x] 3.3 TRIANGULATE: `Rejected` con una y con dos violaciones conserva la tupla en el mismo orden; tabla de `ViolationCode` → valor serializado (`"PROFESSIONAL_OVERLAP"`, `"CHAIR_OVERLAP"`, `"INVALID_DURATION"`), que es el código estable que expone la API; verificar `pytest` y `mypy` en verde.

## 4. API pública: camino feliz y punto de control

> Tests en `tests/domain/test_validate_new_appointment.py`. Design D7. Fábricas tipadas `_existing(...)` y `_request(...)` dentro del archivo de test.

- [x] 4.1 RED: escenario **"Turno válido con profesional y sillón libres"**: prestación de 30 minutos, sin turnos existentes, pedido `T-NUEVO` para P1/S1 a las 13:00 sin duración explícita → `Ok` con un `Appointment` igual al literal esperado (mismo id, paciente, profesional, sillón, `service_id`, de 13:00 a 13:30 UTC, estado `AppointmentStatus.RESERVED`). Verificar que falla porque `app.domain.appointment` no existe.
- [x] 4.2 GREEN: agregar `Service` (`id`, `default_duration_min`) a `model.py`; crear `app/domain/appointment/__init__.py` (re-exporta) y `appointment/validate.py` con la firma de design D7, `validate_new_appointment(request, service, existing_appointments) -> ValidationResult`, y la implementación mínima: duración de la prestación y `Ok` con el turno en `reservado`. Verificar que el test pasa, que `mypy` está en verde y que `test_domain_dependencies.py` sigue en verde (los imports nuevos son `uuid`, `datetime`, `dataclasses`, `enum`, `typing` y `collections.abc`).
- [x] 4.3 ⛔ **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** No seguir con el grupo 5 hasta que la autora apruebe. Presentarle: (a) los tipos públicos de `model.py` y `violations.py` (campos, nombres de los miembros del Enum y sus valores, invariantes de `__post_init__`); (b) la firma de `validate_new_appointment` y el módulo desde donde se importa; (c) los dos puntos marcados como "a revisar en el punto de control" en el design: el pedido sin `service_id` (D3) y la invariante `start_at < end_at` de `Appointment` (D4); (d) la salida de `pytest` y `mypy`. Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha. **Aprobado por la autora el 2026-10-08**: tipos y API pública sin cambios; D3, D4 y los desvíos menores de 1.4 (`uuid_utils` en la tabla existente, orden alfabético de la allowlist) confirmados; mensajes al usuario con tildes desde el grupo 7, docstrings sin cambios.

## 5. Duración del turno (RN-AG-07)

- [x] 5.1 RED: escenario "Duración explícita que reemplaza la de la prestación" (prestación de 45, explícita de 20 → fin 13:20); verificar que falla con la implementación mínima de 4.2.
- [x] 5.2 GREEN: duración efectiva = explícita si no es `None`, si no la de la prestación; `end_at = start_at + timedelta(minutes=duración)`; verificar en verde.
- [x] 5.3 TRIANGULATE: tabla (prestación 45 sin explícita → 13:45; prestación 45 con explícita de 20 → 13:20; **"Duración explícita válida con una prestación de duración no positiva"**: prestación 0 con explícita de 30 → `Ok` con fin 13:30). Agregar el escenario **"Inicio en hora de Buenos Aires"** (pedido `10:00-03:00` → turno de 13:00 a 13:30 UTC). Verificar en verde.

## 6. Intervalos semiabiertos (`intervals.py`)

> Tests en `tests/domain/test_intervals.py`. Design D6.

- [x] 6.1 RED: test parametrizado de `overlaps` con la tabla de design D8 (contiene, contenido, cruce por izquierda, cruce por derecha, igual → `True`; consecutivo por izquierda, consecutivo por derecha, disjunto → `False`); verificar que falla porque `app.domain.intervals` no existe.
- [x] 6.2 GREEN: crear `Interval` *frozen* con slots y `overlaps(a, b)` con comparaciones estrictas; verificar en verde.
- [x] 6.3 TRIANGULATE: `Interval` con `start == end` y con `start > end` → `ValueError` (2 casos); `overlaps` es simétrica (la tabla evaluada con los argumentos en ambos órdenes da el mismo resultado). Verificar en verde.
- [x] 6.4 REFACTOR: agregar la propiedad `Appointment.interval` y reemplazar la cuenta del fin en `validate.py` si corresponde; verificar `pytest` y `mypy` en verde.

## 7. Duración no positiva (`rules/duration.py`, RN-AG-09 parcial)

- [x] 7.1 RED: escenario "Duración explícita de cero minutos" → `Rejected` con exactamente `[(INVALID_DURATION, None)]`; verificar que falla.
- [x] 7.2 GREEN: crear `rules/__init__.py` y `rules/duration.py` con `check_positive_duration(duration_min: int) -> list[Violation]`. En `validate_new_appointment`, si hay violaciones de duración se devuelve `Rejected` antes de construir el turno (design D7, paso 2). Verificar en verde.
- [x] 7.3 TRIANGULATE: tabla con explícita -15, prestación 0 sin explícita y prestación -30 sin explícita → exactamente una `INVALID_DURATION` sin id. Escenario "Mensaje de duración inválida": el mensaje contiene `-15`. Verificar en verde.

## 8. Solapamiento de profesional (`rules/overlap.py`, RN-AG-01 y RN-AG-08)

- [x] 8.1 RED: escenario **"Solapamiento con un turno del mismo profesional"**: turno existente A (P1, S1, 13:00–13:30) y pedido para P1 en S2 a las 13:15 de 30 minutos → `Rejected` con exactamente `[(PROFESSIONAL_OVERLAP, APPT_A)]` y un mensaje que contiene `str(APPT_A)`. Verificar que falla.
- [x] 8.2 GREEN: crear `rules/overlap.py` con `check_professional_overlap(candidate, existing) -> list[Violation]` (filtra por `professional_id` y `overlaps`) y conectarla en `validate.py`; verificar en verde.
- [x] 8.3 TRIANGULATE (geometría): tabla de rechazos para P1/S2 con fin dentro (12:45–13:15), contiene (12:45–13:45), mismo intervalo (13:00–13:30) y contenido dentro de un turno de 13:00–14:00 (13:15–13:30), todos con el id esperado. Tabla de aceptaciones: **"Turno que empieza exactamente cuando termina otro"** (P1/S1 a las 13:30), "Turno que termina exactamente cuando empieza otro" (P1/S1 a las 12:30), "Otro profesional a la misma hora y en otro sillón" (P2/S2 13:00–13:30) y "Turno válido con otros turnos que no chocan" (P1/S1 15:00). Verificar en verde.
- [x] 8.4 RED: escenario "Turno cancelado no bloquea" (existente P1/S2 13:00–13:30 en `cancelado`, pedido P1/S1 13:00–13:30 → `Ok`); verificar que falla porque todavía no se filtra por estado.
- [x] 8.5 GREEN: constante `OCCUPYING_STATUSES = frozenset({RESERVED, CONFIRMED, ATTENDED})` aplicada en el filtro (design D7, SU-07); verificar en verde.
- [x] 8.6 TRIANGULATE (estados): tabla por estado del turno existente de P1 en S2: `ausente` → `Ok`; `reservado`, `confirmado` y `atendido` → `[(PROFESSIONAL_OVERLAP, id)]`. Verificar en verde.
- [x] 8.7 Escenario "Duración inválida en un horario ocupado" (A existente y pedido P1/S1 a las 13:00 con duración 0 → solo `[(INVALID_DURATION, None)]`). Si pasa de entrada por el corte de 7.2, quitar el corte temporalmente para verlo fallar con violaciones de solapamiento y después restaurarlo. Verificar en verde.

## 9. Solapamiento de sillón (RN-AG-02)

- [x] 9.1 RED: escenario "Mismo sillón con otro profesional" (A existente y pedido P2/S1 13:15–13:45 → exactamente `[(CHAIR_OVERLAP, APPT_A)]`); verificar que falla.
- [x] 9.2 GREEN: `check_chair_overlap` (mismo filtro de estado y `overlaps`, por `chair_id`), concatenada **después** de la de profesional en `validate.py`; verificar en verde.
- [x] 9.3 TRIANGULATE: "Mismo profesional y mismo sillón solapados" (P1/S1 13:15–13:45 → `[(PROFESSIONAL_OVERLAP, APPT_A), (CHAIR_OVERLAP, APPT_A)]`); "Otro sillón a la misma hora" (P2/S2 → `Ok`); "Turnos confirmados y atendidos sí bloquean" (tabla con 2 estados → ambas violaciones); "Turno ausente no bloquea" (P1/S1 sobre un turno `ausente` de P1/S1 → `Ok`); "Lista con turnos de otros profesionales y otros sillones" (turnos de P2/S2 que solapan más un cancelado de P1/S1 → `Ok`). Verificar en verde.

## 10. Todas las violaciones, orden y contenido (RN-AG-12, DD-08)

- [x] 10.1 RED: escenario "Varios conflictos de ambos tipos" con la lista recibida en el orden B, C, D (B: P1/S2 13:30–14:00; C: P1/S3 13:00–13:30; D: P2/S1 13:45–14:15), pedido P1/S1 13:00–14:00 → exactamente `[(PROFESSIONAL_OVERLAP, C), (PROFESSIONAL_OVERLAP, B), (CHAIR_OVERLAP, D)]`. Verificar que falla porque las violaciones siguen el orden de la lista.
- [x] 10.2 GREEN: ordenar cada grupo por `(start_at, str(id))` (design D7); verificar en verde.
- [x] 10.3 TRIANGULATE: "Orden independiente del orden de la lista recibida" (lista D, C, B → mismo resultado); caso de desempate con dos turnos de P1 que empiezan a la misma hora en distintos sillones → orden por id. Verificar en verde.
- [x] 10.4 Escenario "Mensajes de las violaciones de solapamiento": las dos violaciones sobre A contienen `str(APPT_A)`; la de profesional contiene "profesional" y la de sillón contiene "sillón". Escenario "Turno existente en otra zona que choca" (existente cargado en `-03:00`, pedido 13:15–13:45 UTC en P1/S2 → `[(PROFESSIONAL_OVERLAP, id)]`). Verificar en verde.
- [x] 10.5 REFACTOR: extraer la lógica común de las dos reglas de solapamiento (filtro por estado, `overlaps` y orden) a una función privada tipada sin `Any`; docstrings estilo Google en `validate_new_appointment`, `check_*` y `overlaps`. Verificar `pytest` y `mypy` en verde después de cada paso.

## 11. Documentación

- [x] 11.1 Actualizar `backend/README.md`: reemplazar "sin lógica todavía" por una sección corta "Dominio" con los módulos (`model`, `violations`, `intervals`, `rules/`, `appointment/`), un ejemplo de uso de `validate_new_appointment` con `match` sobre `Ok` / `Rejected` y una línea sobre `uuid` en la allowlist (solo como tipo; el dominio no genera ids). Verificar que el ejemplo del README coincide con la firma real; si es código ejecutable, correrlo una vez en el venv.
- [x] 11.2 Verificar que `CHANGES.md` §[C-02] coincide con lo implementado (ids `UUID` inyectados, `uuid` en la allowlist, `rules/duration.py`, corte en `INVALID_DURATION`). Ajustar solo si el apply se desvió. El estado `[x]` se marca en el archive, no acá.

## 12. Verificación integral

- [x] 12.1 Desde `backend/`: `pytest` en verde (más tests que el baseline de 1.1) y `mypy` con `Success: no issues found` sobre `app` y `tests`.
- [x] 12.2 Trazabilidad: cada uno de los 31 escenarios de `specs/appointment-scheduling/spec.md` y el escenario nuevo de `specs/domain-dependency-guard/spec.md` tiene al menos un test (función o caso parametrizado) que lo cubre. Dejar la tabla escenario → test en el resumen del apply.
- [x] 12.3 Pureza del dominio: buscar en `app/domain` `datetime.now`, `utcnow`, `time.time`, `uuid1`, `uuid4`, `Any` y `raise`. No debe haber ninguna coincidencia, salvo los `raise ValueError` de las invariantes de `model.py`, `violations.py` e `intervals.py`. `test_domain_dependencies.py` en verde.
- [x] 12.4 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal y no se hizo ningún commit.
