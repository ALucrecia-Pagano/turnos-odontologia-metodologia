# Design

## Context

El dominio crea turnos válidos con `validate_new_appointment` (C-02 a C-08), que evalúa dos grupos: validez del pedido (referencias, duración, inicio en la grilla, medianoche, pasado) y, si esta pasa, conflictos de agenda (horario, bloqueos, solapamientos). El ciclo de vida ordinario (C-10) ofrece `cancel_appointment` y `change_status` con `Actor`/`Role`, permisos por rol y propiedad, `now` inyectado, copias inmutables y `INVALID_TRANSITION`/`STATUS_CHANGE_TOO_EARLY`/`FORBIDDEN_OPERATION`. Las reglas de solapamiento (`rules/overlap.py`) filtran por `same_resource` y `overlaps` pero **no por id**, así que un turno reprogramado chocaría consigo mismo si quedara en la lista de existentes. La regla del pasado (`rules/past.py`) devuelve `IN_THE_PAST` con el mensaje "... no se pueden dar turnos en el pasado.", pensado para el alta. La reprogramación no forma parte de la tabla ordinaria RN-TU-02 (la spec `appointment-lifecycle` lo deja explícito) y `can_transition` nunca permite destino `reservado`, así que no sirve como precondición.

El explore lo hizo Kiro; las decisiones D1–D9 las cerró la autora con las elecciones: D1 B, D2 B, D3 B (mensaje dedicado de estado terminal), D4 A, D5 A, D6 B con D6.1 (i), D7 B, D8 A, D9 A. La autora confirmó además: al reprogramar se revalidan todas las referencias (incluida la actividad del paciente y de la prestación); un profesional o sillón inexistente da `UNKNOWN_REFERENCE`; la prestación no se puede cambiar; el llamador pasa la agenda completa, incluido el turno a reprogramar, y el dominio lo excluye por id. Este documento registra esas decisiones; no implementa código ni tests.

KB 07 Flujo 2 lista el actor como "recepción / administrador" pero no menciona el rechazo del odontólogo; prevalece la matriz RBAC de KB 03 (fila "reprogramar / cancelar" = `—` para odontólogo). El historial del Flujo 2 corresponde a C-12, no a este change.

## Goals / Non-Goals

Goals: operación pura `reschedule_appointment` que revalida todas las RN-AG reutilizando `validate_new_appointment` sin duplicar reglas; auto-exclusión del propio turno por id; precondición de estado `reservado`/`confirmado` con mensaje dedicado; permisos RBAC (odontólogo no reprograma); orden permiso corta → estado corta → turno nuevo; conservación de id, paciente, prestación y duración real; mensaje del pasado con verbo de reprogramar sin romper el alta; Strict TDD con regresión del alta.

Non-Goals: historial (C-12), nuevos `ViolationCode`, cambios en `OCCUPYING_STATUSES` o en las reglas de alta/solapamiento/horario/bloqueos/referencias/duración, JWT/autenticación, API, BD, dependencias externas nuevas, cambiar el catálogo. Tampoco se reprograma cambiando la prestación ni el paciente.

## Decisions

### D1 — Firma de `reschedule_appointment` (elegida: B)

`reschedule_appointment(appointment: Appointment, request: RescheduleRequest, references: AppointmentReferences, existing_appointments: Sequence[Appointment], actor: Actor, professional_name: str, context: ScheduleContext) -> ValidationResult`.

`RescheduleRequest` (frozen/slots) lleva `start_at: datetime` obligatorio y `professional_id: UUID | None`, `chair_id: UUID | None`, `duration_min: int | None` opcionales, donde `None` conserva el valor actual del turno. `references` son las del **nuevo** destino (profesional/sillón si cambiaron; paciente y prestación del original, siempre revalidados). `professional_name` es el nombre del profesional **original**, para los mensajes de permiso y estado que describen el turno actual. `context` lleva `tz`, `working_hours`, `blocks` y `now` (fuente única del reloj); no se pasa `now` aparte para evitar dos fuentes de verdad. El dominio construye internamente el pedido equivalente al alta con `id = appointment.id`, `patient_id` y `service_id` del original, y los campos del `RescheduleRequest`.

### D2 — Reutilizar `validate_new_appointment` sin duplicar reglas (elegida: B)

`validate_new_appointment` se reutiliza sin duplicar reglas. Se le agrega un parámetro opcional `operation` con valor por defecto "dar turnos", que pasa a `check_not_in_the_past` (misma firma con default): el alta no lo pasa y su comportamiento no cambia. Antes de llamarla, `reschedule_appointment` excluye al propio turno de `existing_appointments` comparando por `id`: `others = [a for a in existing_appointments if a.id != appointment.id]`. El filtro por id es universal: cubre el caso en que solo cambia el profesional y el propio turno seguiría coincidiendo por sillón y solapamiento. La corrección no depende de que el llamador filtre: el llamador pasa la agenda completa, incluido el turno a reprogramar, y el dominio lo excluye. No se añade `exclude_id` a `validate_new_appointment` ni a las reglas de solapamiento: eso cambiaría el contrato del alta, ya probado por `appointment-scheduling`.

### D3 — Estados de origen y destino (elegida: B, mensaje dedicado)

Precondición dedicada: `appointment.status in {RESERVED, CONFIRMED}`. Los tres terminales (`atendido`, `ausente`, `cancelado`) → una sola `INVALID_TRANSITION` con mensaje dedicado de reprogramar que nombra al profesional, la fecha y el intervalo local del turno, y el estado terminal. No se usa `can_transition`: la reprogramación no es arista de la tabla ordinaria y `RESERVED` nunca es destino válido en ella. El turno aceptado vuelve a `reservado`: como se reutiliza `validate_new_appointment`, el candidato vuelve con `status=RESERVED` de fábrica (RN-TU-03, US-031 CA-4).

### D4 — Permisos (elegida: A)

El odontólogo nunca reprograma, ni propios ni ajenos: el intento devuelve una sola `FORBIDDEN_OPERATION` y corta. Recepción y administración reprograman todos. Es la misma fila RBAC que cancelar (KB 03), ya resuelta en C-10. La propiedad se compara por `professional_id`, nunca `user_id`. El dominio no autentica JWT ni consulta usuarios; el actor llega del borde futuro.

### D5 — El id se conserva (elegida: A)

El turno aceptado conserva el mismo `id`: el `Ok.appointment` que devuelve `validate_new_appointment` usa `request.id`, y `reschedule_appointment` lo construye con `id = appointment.id`. RN-TU-03 ("excluyendo al propio turno") implica el mismo turno movido. El historial (C-12) registrará el cambio sobre ese id.

### D6 — Qué se puede cambiar (elegida: B, con D6.1 i)

`start_at` es obligatorio. `professional_id`, `chair_id` y `duration_min` son opcionales (`None` conserva el valor actual). El paciente y la prestación no se cambian: se toman del turno original. La duración efectiva al omitir `duration_min` (D6.1, elegida i) es la duración real actual del turno (`appointment.end_at − appointment.start_at`), no el `default_duration_min` de la prestación: codifica "lo que no se cambia se conserva" y es robusta aunque el default de la prestación haya cambiado desde la creación.

### D7 — Orden de evaluación (elegida: B)

Tres fases en cortocircuito: (1) permiso → si el odontólogo, `Rejected([FORBIDDEN_OPERATION])` y corta; (2) estado → si el turno no está en `reservado`/`confirmado`, `Rejected([INVALID_TRANSITION])` y corta; (3) turno nuevo → se llama a `validate_new_appointment` con el propio excluido y se devuelven sus violaciones en el orden RN-AG-12 (grupo 1 validez; si pasa, grupo 2 conflictos). Un resultado no mezcla el permiso o el estado con las violaciones del turno nuevo: revalidar un slot para un turno que no se puede mover es ruido.

### D8 — Códigos y mensajes (elegida: A, cero códigos nuevos)

No se agrega ningún `ViolationCode`: el permiso es `FORBIDDEN_OPERATION` y el estado terminal es `INVALID_TRANSITION` (ambos reusados de C-10). Lo que cambia son los mensajes (textos nuevos, códigos vigentes) y el verbo del pasado. El verbo del pasado llega a `check_not_in_the_past` a través de `validate_new_appointment`, que recibe un parámetro `operation` con valor por defecto "dar turnos" y se lo pasa a la regla (siguiendo el precedente de `check_duration(subject=...)`): el alta llama a `validate_new_appointment` sin el parámetro (default "dar turnos") y `reschedule_appointment` le pasa "reprogramar turnos". Así el alta conserva "... no se pueden dar turnos en el pasado." y reprogramar produce "... no se pueden reprogramar turnos en el pasado." Los conflictos del turno nuevo (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`) se reutilizan con sus textos exactos vigentes: no se redactan de nuevo.

Mensajes nuevos exactos (estilo vigente, sin voseo, "(hora local)"):
- Permiso (odontólogo): `No tiene permiso para reprogramar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden reprogramar turnos.`
- Estado terminal: `El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no se puede reprogramar porque está en estado terminal "atendido".` (variantes "ausente", "cancelado").
- Pasado (reprogramar): `El inicio del turno (20/10/2026 09:00, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden reprogramar turnos en el pasado.`

Los mensajes de permiso y estado describen el turno **original** (su nombre e intervalo); los conflictos del turno nuevo usan el nombre del profesional/sillón del nuevo pedido y el intervalo del turno existente en conflicto. `reference_kind`, `conflicting_appointment_id`/`conflicting_block_id` y `conflicting_interval` son `None` en `FORBIDDEN_OPERATION` e `INVALID_TRANSITION` de reprogramar.

### D9 — Sin punto de control (elegida: A)

Gobernanza MEDIO, igual que C-10, que no tuvo checkpoint. Las decisiones se cierran en el explore; el apply sigue el ciclo TDD (RED → GREEN → TRIANGULATE → REFACTOR) sin aprobación intermedia. C-12 (ALTO) sí llevará checkpoint, pero modifica `reschedule` después para devolver la entrada de historial; C-11 entrega `Ok(appointment)` sin historial.

## Risks / Trade-offs

- `validate_new_appointment` exige `references.professional` y `references.chair` no-`None` para llegar al grupo 2; un profesional/sillón nuevo inexistente da `UNKNOWN_REFERENCE` en el grupo 1 (correcto). La actividad del paciente y de la prestación se revalidan aunque no cambien.
- El filtro por id depende de que el propio esté en la agenda recibida; si el llamador no lo incluye, el filtro no hace nada pero no es dañino (no puede chocar con un turno ausente). La spec deja explícito que el llamador pasa la agenda completa.
- Cambiar `past.py` toca código compartido con el alta; el parámetro con valor por defecto mantiene el mensaje del alta idéntico. La tarea de regresión prueba que el alta sigue diciendo "no se pueden dar turnos en el pasado".
- `now` vive solo en `context`; no pasarlo aparte evita inconsistencia. Un `now` naive se rechaza al construir el `ScheduleContext` (igual que el alta).
- Reprogramar a un slot donde la prestación quedó inactiva da `INACTIVE_REFERENCE`: reprogramar revalida la actividad de la prestación.
- No cambiar `OCCUPYING_STATUSES`: el turno reprogramado a `reservado` vuelve a ocupar ambos recursos en su nuevo intervalo; el intervalo viejo deja de ocuparse porque el llamador reemplaza la versión anterior por la copia devuelta.

## Migration Plan

Apply futuro: baseline real de suite/mypy, luego ciclos verticales por comportamiento y regresión completa. No hay migración de datos ni despliegue. Reutilizar contratos e imports existentes; nuevo `appointment/reschedule.py`, `RescheduleRequest` en `model.py`, parámetro de operación en `past.py` con valor por defecto, exportaciones nuevas en `appointment/__init__.py`. No ejecutar validaciones ni implementar durante este propose.

## Open Questions

Ninguna que afecte D1–D9: cerradas por la autora. Las confirmaciones adicionales (revalidar referencias incluida paciente/prestación, `UNKNOWN_REFERENCE` para profesional/sillón nuevo inexistente, prestación no se cambia, llamador pasa agenda completa y el dominio excluye por id) quedan registradas en este documento y en la spec delta.

## Desvíos del apply

- El apply fue iniciado por Kiro y se interrumpió por límite de uso. Copilot lo retomó desde los archivos sin commitear, verificó la línea de base y completó la implementación y las pruebas restantes.
- La línea de base observada fue `619 passed, 8 deselected` (no `610 passed`); no había fallos preexistentes.
- Para completar la trazabilidad se agregaron pruebas de dominio en `backend/tests/domain/test_reschedule.py` y las evidencias solicitadas en `docs/evidencias/`. No se modificaron las especificaciones principales ni la allowlist de guardias.

## Reestructuración de la spec antes del archive

## Convenciones de los escenarios

Convenciones: datos ficticios. T1 pertenece a P1, Dra. Laura Quiroga, en S1 Sillón 1, martes 20/10/2026 de 10:00 a 10:30 hora local (13:00–13:30 UTC), estado `reservado` salvo que se indique. T2 pertenece a P2, Dra. Inés Molina, en S2, de 11:00 a 11:30 hora local (14:00–14:30 UTC). Actor Laura: user_id U1 distinto de P1, rol ODONTOLOGO y professional_id P1. Recepción U2 y administración U3 tienen professional_id None. La prestación de T1 tiene `default_duration_min` 45, salvo que se indique otra; la duración efectiva de T1 es 30 minutos. El reprograma por defecto mueve T1 a las 11:00 hora local (14:00 UTC) y queda de 11:00 a 11:30 hora local (14:00–14:30 UTC), conservando P1/S1 y duración 30. now habitual 20/10/2026 09:00 hora local (12:00 UTC). Zona inyectada America/Argentina/Buenos_Aires. El llamador pasa la agenda completa, incluido el turno a reprogramar; el dominio lo excluye por id. Donde se revalida, paciente y referencias existen y están activos, horario de día completo y sin bloqueos ni otros turnos salvo que se indique.

Las convenciones se mantienen en `design.md` para que el archive las agregue a la spec principal. Los tres requisitos advertidos se acortaron sin dividirlos ni alterar sus escenarios.
