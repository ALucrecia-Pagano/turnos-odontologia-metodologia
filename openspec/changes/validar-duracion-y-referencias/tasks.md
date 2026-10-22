# Tasks

> Strict TDD: cada comportamiento sigue RED → GREEN → TRIANGULATE → REFACTOR, con al menos 2 casos y sin aserciones triviales. Ejecutar los tests en cada paso y anotar el resultado. Comandos desde `backend/` con el venv activo. **No commitear.**
>
> Skills a cargar antes de escribir código: `tdd`, `python-testing-patterns` y `python-pro` (compact rules en `.atl/skill-registry.md`; la regla dura del proyecto prevalece: sin mocks en el dominio y las reglas de negocio devuelven violaciones, no excepciones).
>
> Reglas para todos los tests de dominio (design D11, igual que en C-02): datos literales (UUIDs fijos en constantes con nombre `PATIENT`, `P1`, `S1`, `SVC_30`, `APPT_A`, …; instantes del 2026-10-20 en UTC); sin `Mock`, `patch`, `monkeypatch` ni `freezegun`; nombres `test_<unidad>_<escenario>_<esperado>`; tablas con `@pytest.mark.parametrize`; aserciones sobre la lista completa de violaciones (código, `reference_kind` o id en conflicto, y orden). `pytest.raises` solo para errores de programación (`ValueError`).
>
> Governance **MEDIO**: la tarea **3.4** es un punto de control. No se implementa ninguna regla (grupos 4 en adelante) sin la aprobación de la autora.

## 1. Red de seguridad

- [x] 1.1 SAFETY NET: correr `pytest` y `mypy` antes de tocar nada y anotar el baseline ("N tests pasando", `Success: no issues found`). Si algo falla, DETENERSE y reportarlo como falla previa, sin arreglarlo.

## 2. Violaciones: códigos nuevos y tipo de referencia (`violations.py`)

> Tests en `tests/domain/test_violations.py`. Design D4.

- [x] 2.1 RED: agregar a la tabla de `ViolationCode` → valor serializado los casos `UNKNOWN_REFERENCE` → `"UNKNOWN_REFERENCE"` e `INACTIVE_REFERENCE` → `"INACTIVE_REFERENCE"`; agregar una tabla `ReferenceKind` → valor (`"PATIENT"`, `"PROFESSIONAL"`, `"CHAIR"`, `"SERVICE"`). Verificar que fallan porque los miembros no existen.
- [x] 2.2 GREEN: sumar los dos códigos a `ViolationCode` y crear `ReferenceKind` (valor igual al nombre). Verificar en verde.
- [x] 2.3 RED → GREEN: test de `Violation` construida sin `reference_kind` (como en C-02) → `reference_kind is None`, y con `reference_kind=ReferenceKind.CHAIR` → lo conserva (2 casos); agregar el campo `reference_kind: ReferenceKind | None = None` al final de `Violation`. Verificar `pytest` (todo C-02 sigue verde) y `mypy` en verde.

## 3. Firma nueva, modelos mínimos y punto de control

> Tests en `tests/domain/test_validate_new_appointment.py`. Design D1, D2, D8, D10 y D11.

- [x] 3.1 RED: escenario **"Todas las referencias existen y están activas"**: agregar la fábrica `_refs(...)` (por defecto `Patient(PATIENT)`, `Professional(P1, active=True)`, `Chair(S1, active=True)`, `Service(SVC_30, 30)`, con parámetros con nombre para reemplazar cada una) y llamar `validate_new_appointment(_request(_at(13)), _refs(), [])` → `Ok` con el turno literal esperado (incluye `service_id=SVC_30`). Verificar que falla porque `Professional`, `Chair`, `Patient` y `AppointmentReferences` no existen.
- [x] 3.2 GREEN: en `model.py` agregar `Professional(id, active)`, `Chair(id, active)`, `Patient(id)`, `Service.active: bool = True`, `NewAppointmentRequest.service_id` (antes de `start_at`) y `AppointmentReferences(patient, professional, chair, service)`, todos *frozen* con slots (design D2 y D10). Cambiar la firma a `validate_new_appointment(request, references, existing_appointments)` y tomar `service_id` del pedido (design D8). Para la prestación `None` dejar solo la rama mínima que exige `mypy` (sin duración → no se valida), que cubren los tests del grupo 6. Actualizar `_request` con `service_id=SVC_30`. Verificar que 3.1 pasa y que `test_domain_dependencies.py` sigue en verde.
- [x] 3.3 Adaptar las llamadas de los tests de C-02 a la firma nueva: cada `validate_new_appointment(req, service, existing)` pasa a `validate_new_appointment(req, _refs(service=service, professional=..., chair=...), existing)` con el profesional y el sillón del pedido. No cambiar ninguna aserción. Verificar que `pytest` vuelve a tener al menos el baseline de 1.1 más los tests nuevos, todo en verde, y `mypy` en verde. Actualizar el ejemplo de `backend/README.md` §Dominio con la firma nueva y verificar que coincide con la firma real (si es ejecutable, correrlo una vez en el venv).
- [x] 3.4 ⛔ **PUNTO DE CONTROL — revisión de la autora. DETENERSE AQUÍ.** No seguir con el grupo 4 hasta que la autora apruebe. Presentarle: (a) los tipos nuevos de `model.py` y `violations.py` (`Professional`, `Chair`, `Patient`, `Service.active`, `NewAppointmentRequest.service_id`, `AppointmentReferences`, `ReferenceKind`, los dos códigos y `Violation.reference_kind`); (b) la firma nueva de `validate_new_appointment`; (c) el texto de los mensajes (design D5 y D7), que es lo único del design que sigue pendiente (D8, D9 y D10 ya los confirmó la autora en el propose); (d) el diff de la adaptación de los tests de C-02 (solo cambian las llamadas); (e) la salida de `pytest` y `mypy`. Si la autora pide cambios, aplicarlos con su test, actualizar `design.md` y volver a presentarlos. Marcar esta tarea solo con la aprobación explícita de la autora y anotar la fecha. Aprobada por la autora el 2026-10-22.

## 4. Coherencia de ids de las referencias (design D9)

> Solo si la autora la aprobó en 3.4. Si la descartó, marcar las tareas como no aplicables con la fecha de la decisión.

- [x] 4.1 RED: test parametrizado con 4 casos: `_refs` con un `Patient`, `Professional`, `Chair` o `Service` cuyo id no coincide con el del pedido → `pytest.raises(ValueError)` con un mensaje que nombra el campo. Verificar que falla.
- [x] 4.2 GREEN: función privada `_check_reference_ids(request, references)` en `appointment/validate.py`, llamada al principio; una referencia `None` no se compara. Verificar en verde.
- [x] 4.3 TRIANGULATE: con todas las referencias `None` y los ids del pedido cualesquiera no hay `ValueError` (el resultado es `Rejected`, no excepción). Verificar `pytest` y `mypy` en verde.

## 5. Referencias existentes y activas (`rules/references.py`, RN-AG-11)

> Spec: requisito "Referencias existentes y activas" y escenarios de referencias de "Todas las violaciones, en orden estable" y "Contenido de cada violación". Design D3, D4 y D7.

- [x] 5.1 RED: escenario "Referencia inexistente", caso profesional: `_refs(professional=None)`, pedido de 30 minutos para P1/S1 a las 13:00 → `Rejected` con exactamente `[(UNKNOWN_REFERENCE, ReferenceKind.PROFESSIONAL)]`. Verificar que falla (hoy devuelve `Ok`).
- [x] 5.2 GREEN: crear `rules/references.py` con `check_references(request, references) -> list[Violation]` (solo el profesional) y llamarla en `validate_new_appointment` **antes** de la duración: si devuelve violaciones, `Rejected` sin evaluar nada más. Verificar en verde.
- [x] 5.3 TRIANGULATE: tabla completa del escenario "Referencia inexistente" (paciente, profesional, sillón y prestación con duración explícita de 30 → `[(UNKNOWN_REFERENCE, kind)]` con el `ReferenceKind` correspondiente). Generalizar `check_references` a las cuatro referencias en el orden de design D7. Verificar en verde.
- [x] 5.4 RED: tabla del escenario "Referencia inactiva" (profesional, sillón y prestación con `active=False` → `[(INACTIVE_REFERENCE, kind)]`). Verificar que falla.
- [x] 5.5 GREEN: rama de inactivo para profesional, sillón y prestación (el paciente no tiene `active`). Verificar en verde.
- [x] 5.6 TRIANGULATE: escenario "Varias referencias que fallan a la vez" (paciente `None`, profesional inactivo, sillón `None`, prestación inactiva → exactamente `[(UNKNOWN_REFERENCE, PATIENT), (INACTIVE_REFERENCE, PROFESSIONAL), (UNKNOWN_REFERENCE, CHAIR), (INACTIVE_REFERENCE, SERVICE)]`). Escenario "Violación de validez en un horario ocupado" (A existente y S1 inactivo → solo `[(INACTIVE_REFERENCE, CHAIR)]`); si pasa de entrada por el corte de 5.2, quitar el corte temporalmente para verlo fallar con violaciones de solapamiento y después restaurarlo. Verificar en verde.
- [x] 5.7 Escenario "Tipo de referencia en las violaciones de referencias" (S2 inexistente → `UNKNOWN_REFERENCE`, `CHAIR`, mensaje que contiene `str(S2)`; P1 inactivo → `INACTIVE_REFERENCE`, `PROFESSIONAL`, mensaje que contiene `str(P1)`; en ambos `conflicting_appointment_id is None`). Mensajes de design D7. Verificar en verde.
- [x] 5.8 REFACTOR: evitar la repetición de las ramas por referencia (por ejemplo, una función privada tipada por referencia con su `ReferenceKind` y sus textos), sin `Any`; docstrings estilo Google en `check_references`. Verificar `pytest` y `mypy` en verde después de cada paso.

## 6. Validez completa de la duración (`rules/duration.py`, RN-AG-09)

> Spec: requisito "Validez de la duración". Design D5.

- [x] 6.1 RED: escenario "Duración que no es múltiplo de 5" (explícitas 7 y 32 → exactamente `[(INVALID_DURATION, None)]`). Verificar que falla (hoy devuelve `Ok`).
- [x] 6.2 GREEN: reemplazar `check_positive_duration` por `check_duration` (actualizar el import en `validate.py`) con la constante `DURATION_STEP_MIN = 5`. Verificar que 6.1 pasa y que los escenarios de duración no positiva de C-02 siguen en verde (incluido el mensaje que contiene `-15`).
- [x] 6.3 RED → GREEN: escenario "Duración mayor que el máximo" (explícita 490 → `[(INVALID_DURATION, None)]`); agregar `MAX_DURATION_MIN = 480`. Verificar en verde.
- [x] 6.4 TRIANGULATE: tabla de aceptaciones: **"Duración máxima válida"** (480 a las 08:00 → `Ok` de 08:00 a 16:00), **"Duración mínima válida"** (5 → `Ok` de 13:00 a 13:05) y "Duración explícita válida que reemplaza una por defecto inválida" (prestación 485, explícita 30 → `Ok` hasta 13:30). Tabla de rechazos: "Duración por defecto de la prestación que no es múltiplo de 5" (32 sin explícita). Verificar en verde.
- [x] 6.5 RED → GREEN: escenarios "Duración que rompe dos condiciones" y "Mensaje de duración que rompe dos condiciones" (487 → exactamente una `INVALID_DURATION`, con un mensaje que contiene `487`, `múltiplo de 5` y `480`). Implementar el armado del mensaje con todas las razones de design D5. Verificar que falla antes (por el texto o por dos violaciones) y en verde después.
- [x] 6.6 REFACTOR: constantes con `Final`, docstring del módulo citando SU-02 ("constante configurable") y docstring de `check_duration`. Verificar `pytest` y `mypy` en verde.

## 7. Dos grupos: validez del pedido y conflictos de agenda (RN-AG-12)

> Spec: requisito "Todas las violaciones, en orden estable" y casos borde de "Validez de la duración". Design D3.

- [x] 7.1 RED: escenario "Referencia y duración inválidas a la vez" (profesional `None`, explícita 7 → exactamente `[(UNKNOWN_REFERENCE, PROFESSIONAL), (INVALID_DURATION, None)]`). Verificar que falla porque el corte de 5.2 devuelve solo la referencia.
- [x] 7.2 GREEN: armar el grupo 1 acumulando referencias y después duración, y cortar solo si el grupo 1 no está vacío (design D3, paso 2). Verificar en verde.
- [x] 7.3 RED → GREEN: escenario "Prestación inexistente sin duración explícita" (prestación `None`, sin explícita → exactamente `[(UNKNOWN_REFERENCE, SERVICE)]`). Si pasa de entrada por la rama mínima de 3.2, anotar por qué y seguir con la triangulación. Verificar en verde.
- [x] 7.4 TRIANGULATE: "Prestación inexistente con duración explícita inválida" (prestación `None`, explícita 7 → `[(UNKNOWN_REFERENCE, SERVICE), (INVALID_DURATION, None)]`) y "Prestación inactiva con duración por defecto inválida" (prestación inactiva de 485, sin explícita → `[(INACTIVE_REFERENCE, SERVICE), (INVALID_DURATION, None)]`). Confirmar que "Duración inválida en un horario ocupado" (C-02) sigue en verde. Verificar en verde.
- [x] 7.5 Escenario "Violaciones sin tipo de referencia" (A existente y pedido P1/S1 13:15–13:45 → las dos violaciones de solapamiento con `reference_kind is None`; explícita 7 → la `INVALID_DURATION` con `reference_kind is None`). Verificar en verde.
- [x] 7.6 REFACTOR: separar en `validate.py` el grupo 1 y el grupo 2 en funciones privadas tipadas (por ejemplo, `_request_validity_violations` y `_agenda_conflict_violations`), con un comentario que diga que C-05 a C-07 suman sus reglas al grupo que corresponda; docstring de `validate_new_appointment` con los dos grupos. Verificar `pytest` y `mypy` en verde después de cada paso.

## 8. Documentación

- [x] 8.1 Revisar `backend/README.md` §Dominio: agregar `rules/references.py` a la tabla de módulos y una línea sobre los dos grupos de violaciones. Verificar que el ejemplo sigue coincidiendo con la firma real.
- [x] 8.2 Verificar que `CHANGES.md` §[C-03] coincide con lo implementado (`rules/duration.py` con múltiplo de 5 y máximo 480, `rules/references.py`, códigos `UNKNOWN_REFERENCE` / `INACTIVE_REFERENCE`). Ajustar solo si el apply se desvió. El estado `[x]` se marca en el archive, no acá.

## 9. Verificación integral

- [x] 9.1 Desde `backend/`: `pytest` en verde (más tests que el baseline de 1.1) y `mypy` con `Success: no issues found` sobre `app` y `tests`.
- [x] 9.2 Trazabilidad: cada uno de los 29 escenarios de `specs/appointment-scheduling/spec.md` de este change tiene al menos un test (función o caso parametrizado) que lo cubre, y los escenarios de C-02 que no toca este change siguen cubiertos. Dejar la tabla escenario → test en el resumen del apply.
- [x] 9.3 Pureza del dominio: buscar en `app/domain` `datetime.now`, `utcnow`, `time.time`, `uuid1`, `uuid4`, `Any` y `raise`. No debe haber ninguna coincidencia, salvo los `raise ValueError` de las invariantes de `model.py`, `violations.py` e `intervals.py` y el de la coherencia de ids en `appointment/validate.py` (si se aprobó en 3.4). `test_domain_dependencies.py` en verde (la allowlist no cambia).
- [x] 9.4 `git status` desde la raíz: solo cambiaron los archivos listados en el Impact del proposal y no se hizo ningún commit.
