# Explore de C-02 crear-turno-sin-solapamientos

La consigna pide guardar el resultado o un resumen del relevamiento del explore. El explore se hizo el 2026-10-08 con `/opsx:explore`, en conversación con el agente y sin escribir archivos. Las decisiones quedaron después en el `design.md` del change, que dice que las decisiones 1 a 7 salieron del explore.

## Punto de partida

- C-01 ya estaba archivado: había un proyecto Python con pytest, mypy estricto y la guardia de dependencias, pero el paquete `app/domain` estaba vacío.
- No había changes activos. C-02 tenía que definir el modelo central del que dependen C-03 a C-12, por eso su governance es ALTO.

## Decisiones

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| 1 | ¿De dónde sale el id del turno nuevo? | Lo pasa quien llama; el dominio nunca lo genera. Tipo `UUID`, y se agrega `uuid` a la lista de permitidos de la guardia. | Igual que el `now` inyectado: así el dominio es determinista y los tests usan valores fijos. |
| 2 | Si un turno choca con dos turnos, ¿una violación o dos? | Una por cada turno en conflicto: primero las de profesional y después las de sillón, cada grupo ordenado por inicio. | Muestra todo lo que hay que corregir, que es el diferencial del producto. |
| 3 | Con una duración inválida, ¿se evalúan los solapamientos? | No: se informa solo `INVALID_DURATION`. | Con duración 0 o negativa el intervalo no existe y comparar no tiene sentido. Queda como excepción a DD-08. |
| 4 | ¿Quién filtra los turnos relevantes? | El dominio, por profesional y por sillón. | La regla no depende de que la capa de datos arme bien la consulta. |
| 5 | ¿Qué pasa con una fecha sin zona horaria? | `ValueError`; si viene en otra zona, se normaliza a UTC. | Es un error de programación, no una regla de negocio: las reglas de negocio devuelven un resultado con código, no excepciones. |
| 6 | ¿Qué queda afuera? | `exclude_id` (va en C-11). El mensaje en C-02 es mínimo y en español; el texto completo va en C-08. El resultado es `Ok` o `Rejected`. | Mantener el change chico. |
| 7 | ¿Dónde se valida la duración por defecto de la prestación? | En la misma regla de duración. | Un solo lugar para `INVALID_DURATION`. |

## Pedidos para el propose

- Los 3 escenarios que exige la consigna: feliz, error de negocio y borde (un turno que empieza justo cuando termina otro).
- La justificación de la elección del change en `proposal.md`.
- Un punto de control después de definir los tipos y la API pública, para revisarlos antes de implementar las reglas (tarea 4.3 de `tasks.md`).

## Anexo: explore de C-01 (2026-10-08)

En C-01, la fundación técnica, el explore detectó que `CHANGES.md` pedía una guardia con lista de **prohibidos** y la knowledge-base una con lista de **permitidos**. Se eligió la de permitidos porque con la otra pasarían `os`, `pathlib` o imports de otras capas. Se dejó afuera la detección de `datetime.now()` para que el change siguiera chico (quedó anotada para C-07), y se eligió un entorno virtual con Python 3.13 y el proyecto como paquete instalable.