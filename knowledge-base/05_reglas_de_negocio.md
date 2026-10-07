# Reglas de Negocio

Cada regla tiene un código único `RN-{DOMINIO}-{NN}`. Cada una debe tener al menos un test automatizado (Strict TDD, mínimo happy path + un caso borde). Las reglas marcadas **Suposición:** no vienen del discovery: son defaults propuestos para el MVP y están abiertos en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

Convención de intervalos: todo turno o bloqueo es un intervalo **semiabierto** `[inicio, fin)`. Dos intervalos se solapan si `inicioA < finB` **y** `inicioB < finA`. Turnos consecutivos (uno termina a las 10:00 y otro empieza a las 10:00) **no** se solapan.

## Dominio: Agenda / solapamientos (RN-AG)

Origen: checklist §7, reglas 1 a 6 (vigentes en el MVP). Estas reglas se validan en el dominio puro.

**Primer change (`crear-turno-sin-solapamientos`)**: solo RN-AG-01, RN-AG-02, RN-AG-07 (duración por prestación), RN-AG-08 (qué estados ocupan agenda) y la parte mínima de RN-AG-09 (duración mayor que cero, `INVALID_DURATION`), más la convención de intervalos semiabiertos. Van en `horarios-y-bloqueos` (change 2): RN-AG-04, RN-AG-05, RN-AG-06, el resto de RN-AG-09 (múltiplo de 5, máximo 480), RN-AG-10, RN-AG-11 y el formato completo de RN-AG-12 (decisión Q-13).

- **RN-AG-01**: Un profesional no puede tener dos turnos activos superpuestos. *(Checklist 7.1)* Código de rechazo: `PROFESSIONAL_OVERLAP`.
- **RN-AG-02**: Un sillón/box no puede asignarse a dos turnos activos superpuestos. *(Checklist 7.2)* Código: `CHAIR_OVERLAP`.
- **RN-AG-03**: Los sobreturnos están prohibidos: todo solapamiento se rechaza, sin opción de forzar. *(Checklist 7.3)* El modelo debe permitir habilitarlos luego (riesgo 9 del checklist).
- **RN-AG-04**: El turno debe caer **completo** dentro de un tramo del horario de atención del profesional (evaluado en hora local) para el día correspondiente. Un turno que empieza dentro pero termina fuera se rechaza. *(Checklist 7.4)* Código: `OUTSIDE_WORKING_HOURS`.
- **RN-AG-05**: El turno no puede solaparse con ningún bloqueo del profesional. *(Checklist 7.4)* Código: `BLOCKED_TIME`.
- **RN-AG-06**: No se puede dar ni reprogramar un turno con inicio anterior al instante actual (`now` inyectado). Inicio exactamente igual a `now` es válido. *(Checklist 7.5)* Código: `IN_THE_PAST`.
- **RN-AG-07**: La duración del turno es variable: por defecto la `default_duration_min` de la prestación, editable al dar el turno. *(Checklist 7.6)* Código de rechazo: `INVALID_DURATION` (ver RN-AG-09).
- **RN-AG-08**: Ocupan agenda (cuentan para RN-AG-01 y RN-AG-02) los turnos en estado `reservado`, `confirmado` y `atendido`. Los turnos `cancelado` y `ausente` **liberan** el horario. **Suposición:** `ausente` libera el hueco aunque sea del pasado, porque nunca se evalúa contra turnos nuevos (que no pueden estar en el pasado); definición pendiente (SU-07).
- **RN-AG-09**: Validez de la duración: entero positivo, múltiplo de 5 minutos y como máximo 480 minutos (8 h). **Suposición** (SU-02).
- **RN-AG-10**: Un turno no cruza la medianoche: inicio y fin caen en el mismo día local. **Suposición** (simplifica RN-AG-04).
- **RN-AG-11**: El profesional, el sillón y la prestación del turno deben existir y estar activos; el paciente debe existir. Código: `UNKNOWN_REFERENCE` / `INACTIVE_REFERENCE`.
- **RN-AG-12**: El dominio devuelve **todas** las violaciones detectadas (no solo la primera), ordenadas por prioridad: referencias → duración → pasado → horario laboral → bloqueo → solapamiento de profesional → solapamiento de sillón. Cada violación incluye código, mensaje en español y, si aplica, el id del turno o bloqueo que choca. *(Diferenciador: mensajes de rechazo explicativos.)*
- **RN-AG-13**: Servicios sin sillón específico: cualquier prestación puede darse en cualquier sillón activo. **Suposición** (SU-04); pregunta abierta Q-05.

## Dominio: Ciclo de vida del turno (RN-TU)

Estados: `reservado`, `confirmado`, `atendido`, `ausente`, `cancelado`. Origen: checklist §5 y D.3 (transiciones explícitas). Las transiciones concretas son **Suposición** (SU-03; pregunta abierta Q-03).

- **RN-TU-01**: Todo turno nuevo nace en estado `reservado` y registra una entrada de historial (`from_status` nulo).
- **RN-TU-02**: Transiciones válidas (**Suposición**):

| Desde \ Hacia | reservado | confirmado | atendido | ausente | cancelado |
|---------------|-----------|------------|----------|---------|-----------|
| reservado | — | sí | sí | sí | sí |
| confirmado | no | — | sí | sí | sí |
| atendido | no | no | — | no | no |
| ausente | no | no | no | — | no |
| cancelado | no | no | no | no | — |

`atendido`, `ausente` y `cancelado` son **terminales**. Cualquier otra transición se rechaza con `INVALID_TRANSITION`.
- **RN-TU-03**: Reprogramar (cambiar inicio, profesional, sillón y/o duración) solo es posible en `reservado` o `confirmado`. Revalida **todas** las reglas RN-AG excluyendo al propio turno de la comprobación de solapamiento. **Suposición:** el turno reprogramado vuelve a `reservado` (la confirmación previa deja de valer) y se registra en el historial.
- **RN-TU-04**: Cancelar no exige anticipación mínima en el MVP (**Suposición**; Q-01). Un turno puede cancelarse en cualquier momento mientras esté en `reservado` o `confirmado`.
- **RN-TU-05**: Marcar `ausente` solo es válido si `now >= inicio` del turno (**Suposición**; Q-02). Marcar `atendido` también exige `now >= inicio`.
- **RN-TU-06**: Cada cambio de estado o reprogramación genera una entrada **inmutable** de historial: quién (`changed_by`), cuándo (`changed_at`), de qué estado a cuál. El historial es append-only. *(Checklist §5; se implementa en el change del ciclo de vida, no en el primero.)*

## Dominio: Disponibilidad (RN-DI)

- **RN-DI-01**: Un horario de atención se define por profesional, día de la semana y tramo `[inicio, fin)` en hora local; puede haber varios tramos por día.
- **RN-DI-02**: Los tramos de un mismo profesional y día no pueden solaparse entre sí ni tener `inicio >= fin`.
- **RN-DI-03**: Un bloqueo es un intervalo `[inicio, fin)` por profesional con motivo opcional; `inicio < fin`.
- **RN-DI-04**: Crear un bloqueo que pisa turnos ya existentes **no** los cancela ni los mueve; los turnos quedan visibles para que recepción los reprograme. **Suposición** (SU-05; Q-04). Referencia de mercado: Odonthia hace lo mismo.
- **RN-DI-05**: Granularidad de agenda de 5 minutos: inicio y duración de los turnos son múltiplos de 5 min. **Suposición** (SU-02; Q-06).

## Dominio: Pacientes y privacidad (RN-PA)

- **RN-PA-01**: El paciente tiene solo datos mínimos: nombre, DNI, teléfono, obra social (texto). Prohibida información clínica en el MVP.
- **RN-PA-02**: Todo dato de paciente en el repositorio, seeds, tests y capturas es **ficticio**. Nunca datos reales.
- **RN-PA-03**: **Diferida:** un paciente no puede tener dos turnos activos simultáneos. El diseño (función de reglas componible) debe permitir agregarla sin reescribir el motor.

## Dominio: Acceso (RN-AC)

- **RN-AC-01**: Permisos por rol según la matriz de [03_actores_y_roles.md](03_actores_y_roles.md); un Odontólogo solo modifica horarios, bloqueos y estados de **sus propios** turnos.
- **RN-AC-02**: El MVP no guarda credenciales; la identificación de rol es simulada (SU-06).

## Dominio: Excepciones globales (RN-GL)

- **RN-GL-01**: El **dominio es la autoridad**: la UI y la API pueden pre-validar, pero toda creación o reprogramación pasa por las reglas RN-AG en el dominio.
- **RN-GL-02**: Las operaciones de escritura de turnos son atómicas: o se valida y guarda todo (turno + historial) o nada.
- **RN-GL-03**: Hora y zona: los instantes se almacenan en UTC; las comparaciones de horario laboral usan `America/Argentina/Buenos_Aires` (SU-01).
- **RN-GL-04**: Ninguna regla debe leer el reloj del sistema directamente: `now` se inyecta (permite tests deterministas).

## Trazabilidad con el checklist

| Checklist §7 | Regla |
|--------------|-------|
| 1 | RN-AG-01 |
| 2 | RN-AG-02 |
| 3 | RN-AG-03 |
| 4 | RN-AG-04, RN-AG-05 |
| 5 | RN-AG-06 |
| 6 | RN-AG-07, RN-AG-09 |
| Diferida (paciente simultáneo) | RN-PA-03 |
