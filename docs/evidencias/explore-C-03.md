# Explore de C-03 validar-duracion-y-referencias

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-22 con `/opsx:explore`, en conversación con el agente y sin escribir código. Las decisiones tienen que quedar después en el `design.md` del change.

## Punto de partida

- C-02 ya estaba archivado. `validate_new_appointment(request, service, existing_appointments)` valida la duración positiva y los solapamientos por profesional y por sillón. Si la duración falla, corta ahí y no evalúa solapamientos.
- `Service` tenía solo `id` y `default_duration_min`, sin `active`. No existían `Professional`, `Chair` ni `Patient`. `NewAppointmentRequest` no tenía `service_id`, porque la prestación llegaba como objeto aparte. Con esa firma no se podía representar una prestación inexistente, y RN-AG-11 quedaba del lado de la API, lo que rompe la regla de no duplicar reglas fuera del dominio.
- `ViolationCode` tenía tres códigos (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` e `INVALID_DURATION`). Faltaban `UNKNOWN_REFERENCE` e `INACTIVE_REFERENCE`.
- No había changes activos. La spec `appointment-scheduling` tiene 11 requisitos, y "Rechazo de duración no positiva" se tiene que ampliar a la validez completa de la duración.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿Cómo sabe un dominio sin base de datos si una referencia existe y está activa? | Quien llama busca cada id y pasa la entidad o `None` (profesional, sillón, prestación y paciente). `None` da `UNKNOWN_REFERENCE` y `active=False` da `INACTIVE_REFERENCE`. El request suma `service_id`. | Coincide con el Flujo 1 de KB 07: la API carga el contexto y el dominio decide. El repositorio solo hace `get_by_id`, la regla queda en el dominio y los tests usan datos literales, sin mocks. |
| 2 | ¿Los modelos de referencia entran en C-03 o esperan a C-09? | Modelos mínimos en C-03: `Professional(id, active)`, `Chair(id, active)`, `Patient(id)` y `active` en `Service`, con valor por defecto `True`. C-09 agrega nombres y validaciones. | No se mezclan changes. Con el valor por defecto, los tests de C-02 no cambian. |
| 3 | ¿Cuándo se corta y cuándo se acumulan violaciones? | En dos grupos. Primero va la validez del pedido: referencias y duración, informadas todas juntas. Si hay alguna, se corta. Recién después se evalúan los conflictos de agenda. Si la prestación no existe y no hay duración explícita, la duración no se valida. | Muestra de una vez todo lo que está mal en el pedido (RN-AG-12), mantiene el corte de C-02 y separa los `422` de los `409`, así una respuesta nunca mezcla los dos. Sin prestación ni duración explícita, no hay duración que validar. |
| 4 | ¿Cómo dice la violación qué referencia falló? | Con un campo opcional `reference_kind` en `Violation` (paciente, profesional, sillón o prestación). | El frontend tiene que poder marcar el campo del formulario sin interpretar el texto del mensaje. Es un campo opcional y no rompe C-02. |
| 5 | Si la duración rompe dos reglas (por ejemplo 485), ¿una violación o dos? | Una sola `INVALID_DURATION`, con un mensaje que nombra las dos razones. | El código describe el campo, no cada subregla. Dos violaciones iguales se verían repetidas en la interfaz. |
| 6 | ¿El inicio múltiplo de 5 minutos (RN-DI-05) entra en C-03? | No: pasa a C-04, y el scope de C-04 en `CHANGES.md` ya está actualizado. | La grilla de 5 minutos tiene sentido en hora local, que vive en C-04, y C-03 no crece. El código de violación para el inicio se define en C-04. |
| 7 | ¿En qué orden van las violaciones de referencias? | Paciente, profesional, sillón, prestación. | Es el orden de los campos de `POST /api/appointments` (KB 07): un orden estable y fácil de testear. |

> Nota (2026-10-22, apply): 485 es múltiplo de 5 (5 × 97), así que solo rompe el máximo. El ejemplo correcto de una duración que rompe las dos condiciones es 487. El error lo detectó el test de la tarea 6.5 y se corrigió en la spec, el design, el proposal y tasks.

## Pedidos para el propose

- Los límites de duración (granularidad de 5 y máximo de 480) quedan como constantes del módulo `rules/duration.py`, como dice SU-02 ("constante configurable").
- Tests de US-007 CA-1 (no múltiplo de 5, 485, 480 válido y 5 válido) y CA-2 con una tabla de casos por cada tipo de referencia (inexistente e inactiva; el paciente solo inexistente).
- En la spec, ampliar "Rechazo de duración no positiva" a la validez completa de la duración, agregar el requisito de referencias y actualizar "Todas las violaciones, en orden estable" con los dos grupos.
