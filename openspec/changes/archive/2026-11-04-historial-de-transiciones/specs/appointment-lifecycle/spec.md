## ADDED Requirements

### Requirement: Modelo inmutable de entrada de historial y detalle de reprogramación
`AppointmentStatusChange` y `RescheduleDetail` SHALL ser dataclasses inmutables (`frozen=True`, `slots=True`). `AppointmentStatusChange` SHALL tener `appointment_id`, `from_status` (`None` solo en el alta), `to_status`, `changed_by`, `changed_at` y `reschedule` opcional (`None` por defecto). `RescheduleDetail` SHALL tener los intervalos, profesionales y sillones anteriores y nuevos. Reasignar atributos MUST lanzar `FrozenInstanceError`.

#### Scenario: Inmutabilidad de AppointmentStatusChange
- **GIVEN** una entrada `AppointmentStatusChange` válida para el turno `T1` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`) con `from_status=reservado`, `to_status=confirmado`, `changed_by=U2` y `changed_at=2026-10-20T12:00:00Z` (09:00 hora local)
- **WHEN** se intenta modificar cualquiera de sus atributos (`appointment_id`, `from_status`, `to_status`, `changed_by`, `changed_at` o `reschedule`) mediante `setattr`
- **THEN** lanza `FrozenInstanceError` y la entrada conserva todos sus valores originales

#### Scenario: Inmutabilidad de RescheduleDetail
- **GIVEN** un `RescheduleDetail` válido con intervalo anterior de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), intervalo nuevo de 11:00 a 11:30 hora local (`2026-10-20T14:00:00Z` a `2026-10-20T14:30:00Z`), profesional `P1` y sillón `S1`
- **WHEN** se intenta modificar cualquiera de sus seis atributos mediante `setattr`
- **THEN** lanza `FrozenInstanceError` y el detalle conserva todos sus valores originales

### Requirement: Invariantes de zona horaria y transición en AppointmentStatusChange
Al construir `AppointmentStatusChange`, `changed_at` MUST tener zona horaria y SHALL normalizarse a UTC; un `changed_at` sin zona (*naive*) MUST lanzar `ValueError`. Si `from_status` es igual a `to_status` y `reschedule` es `None`, la construcción MUST lanzar `ValueError`, de modo que la única entrada válida con el mismo estado de origen y destino sea la de una reprogramación desde `reservado`.

#### Scenario: changed_at sin zona horaria lanza ValueError
- **GIVEN** los datos de una transición de `reservado` a `confirmado` para `T1` por `U2`
- **WHEN** se construye `AppointmentStatusChange` con `changed_at` `2026-10-20T09:00:00` sin zona horaria (*naive*)
- **THEN** lanza `ValueError` indicando que `changed_at` requiere zona horaria

#### Scenario: changed_at con zona horaria distinta se normaliza a UTC
- **GIVEN** los datos de una transición de `reservado` a `confirmado` para `T1` por `U2`
- **WHEN** se construye `AppointmentStatusChange` con `changed_at` el martes 20/10/2026 a las `09:00-03:00` (hora local `America/Argentina/Buenos_Aires`)
- **THEN** la entrada queda construida con `changed_at` normalizado a `2026-10-20T12:00:00Z` en UTC

#### Scenario: Misma transición sin detalle de reprogramación lanza ValueError
- **GIVEN** un mismo estado en `from_status` y `to_status` (por ejemplo, `reservado` a `reservado` o `confirmado` a `confirmado`) y `changed_at` `2026-10-20T12:00:00Z` (09:00 hora local)
- **WHEN** se construye `AppointmentStatusChange` con `reschedule=None`
- **THEN** lanza `ValueError` porque una entrada con el mismo estado de origen y destino requiere `RescheduleDetail`

### Requirement: Entrada de historial en cambios de estado y cancelación
Cuando `change_status` o `cancel_appointment` aceptan la operación, SHALL devolver `Ok(appointment, status_change)` cuya entrada `AppointmentStatusChange` registra `appointment_id` igual a `appointment.id`, `from_status` igual al estado previo del turno, `to_status` igual al estado destino (`confirmado`, `atendido`, `ausente` o `cancelado`), `changed_by` igual a `actor.user_id`, `changed_at` igual a `now` en UTC y `reschedule` en `None` (RN-TU-06, US-030 CA-3).

#### Scenario: Entrada al confirmar un turno reservado
- **GIVEN** `T1` en `reservado` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), recepción `U2` y `now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** `change_status` solicita pasar `T1` a `confirmado`
- **THEN** devuelve `Ok(appointment, status_change)` con `appointment.status == confirmado` y `status_change` con `appointment_id=T1.id`, `from_status=reservado`, `to_status=confirmado`, `changed_by=U2`, `changed_at=2026-10-20T12:00:00Z` y `reschedule=None`

#### Scenario: Entrada al marcar como atendido
- **GIVEN** `T1` en `confirmado` de P1 ("Dra. Laura Quiroga"), el actor odontólogo `U1` vinculado a `P1` y `now` el martes 20/10/2026 a las 10:00 hora local (`2026-10-20T13:00:00Z`)
- **WHEN** `change_status` solicita pasar `T1` a `atendido`
- **THEN** devuelve `Ok(appointment, status_change)` con `appointment.status == atendido` y `status_change` con `appointment_id=T1.id`, `from_status=confirmado`, `to_status=atendido`, `changed_by=U1`, `changed_at=2026-10-20T13:00:00Z` y `reschedule=None`

#### Scenario: Entrada al marcar como ausente
- **GIVEN** `T1` en `reservado` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), recepción `U2` y `now` a las 10:15 hora local (`2026-10-20T13:15:00Z`)
- **WHEN** `change_status` solicita pasar `T1` a `ausente`
- **THEN** devuelve `Ok(appointment, status_change)` con `appointment.status == ausente` y `status_change` con `appointment_id=T1.id`, `from_status=reservado`, `to_status=ausente`, `changed_by=U2`, `changed_at=2026-10-20T13:15:00Z` y `reschedule=None`

#### Scenario: Entrada al cancelar un turno
- **GIVEN** `T1` en `confirmado` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), administración `U3` y `now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** se invoca `cancel_appointment` sobre `T1`
- **THEN** devuelve `Ok(appointment, status_change)` con `appointment.status == cancelado` y `status_change` con `appointment_id=T1.id`, `from_status=confirmado`, `to_status=cancelado`, `changed_by=U3`, `changed_at=2026-10-20T12:00:00Z` y `reschedule=None`

### Requirement: Entrada única con detalle al reprogramar un turno
Cuando `reschedule_appointment` acepta la reprogramación, SHALL devolver `Ok(appointment, status_change)` con una única entrada `AppointmentStatusChange`: `from_status` igual al estado real del turno original (`reservado` o `confirmado`), `to_status` en `reservado`, `changed_by` igual a `actor.user_id`, `changed_at` igual a `context.now` en UTC y `reschedule` con `RescheduleDetail` poblado. MUST NOT dejar la entrada de alta (`from_status` `None`) de la revalidación interna (US-031 CA-5, US-033).

#### Scenario: Reprogramar desde reservado registra reservado a reservado con detalle
- **GIVEN** `T1` en `reservado` el martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`) con `P1` y `S1`, recepción `U2` y `context.now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** se reprograma `T1` a las 11:00 hora local (`2026-10-20T14:00:00Z` a `2026-10-20T14:30:00Z`) conservando `P1`, `S1` y duración 30
- **THEN** devuelve `Ok(appointment, status_change)` donde `status_change` tiene `appointment_id=T1.id`, `from_status=reservado`, `to_status=reservado`, `changed_by=U2` y `changed_at=2026-10-20T12:00:00Z`
- **AND** `status_change.reschedule` tiene `previous_interval` `13:00–13:30 UTC`, `new_interval` `14:00–14:30 UTC`, `previous_professional_id=P1`, `new_professional_id=P1`, `previous_chair_id=S1` y `new_chair_id=S1`

#### Scenario: Reprogramar desde confirmado registra confirmado a reservado con detalle
- **GIVEN** `T1` en `confirmado` el martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`) con `P1` y `S1`, administración `U3` y `context.now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** se reprograma `T1` a las 11:00 hora local (`2026-10-20T14:00:00Z` a `2026-10-20T14:30:00Z`) cambiando el profesional a `P2` y el sillón a `S2`
- **THEN** devuelve `Ok(appointment, status_change)` donde `appointment.status == reservado` y `status_change` tiene `appointment_id=T1.id`, `from_status=confirmado`, `to_status=reservado`, `changed_by=U3` y `changed_at=2026-10-20T12:00:00Z`
- **AND** `status_change.reschedule` tiene `previous_interval` `13:00–13:30 UTC`, `new_interval` `14:00–14:30 UTC`, `previous_professional_id=P1`, `new_professional_id=P2`, `previous_chair_id=S1` y `new_chair_id=S2`

#### Scenario: Reprogramar no deja la entrada de alta de la validación interna
- **GIVEN** `T1` en `reservado` el martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), recepción `U2` y `context.now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** se reprograma `T1` a las 11:00 hora local (`2026-10-20T14:00:00Z`)
- **THEN** el resultado `Ok` contiene una sola entrada en `status_change` cuyo `from_status` es `reservado` (nunca `None`) y cuyo `reschedule` no es `None`

### Requirement: Rechazos de ciclo de vida y reprogramación sin entrada de historial
Cuando `change_status`, `cancel_appointment` o `reschedule_appointment` devuelven `Rejected` por cualquier violación de permiso, estado, tiempo o regla de agenda, el resultado MUST ser únicamente `Rejected(violations=...)` y MUST NOT generar ni adjuntar ninguna instancia de `AppointmentStatusChange`.

#### Scenario: Rechazo en change_status no genera entrada
- **GIVEN** `T1` en `reservado` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), recepción `U2` y `now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** `change_status` solicita pasar `T1` a `atendido` antes del inicio
- **THEN** devuelve `Rejected` con `STATUS_CHANGE_TOO_EARLY` y no devuelve `Ok` ni entrada `AppointmentStatusChange` alguna

#### Scenario: Rechazo en cancel_appointment no genera entrada
- **GIVEN** `T1` en `atendido` del martes 20/10/2026 de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), recepción `U2` y `now` a las 10:30 hora local (`2026-10-20T13:30:00Z`)
- **WHEN** se invoca `cancel_appointment` sobre `T1`
- **THEN** devuelve `Rejected` con `INVALID_TRANSITION` y no devuelve `Ok` ni entrada `AppointmentStatusChange` alguna

#### Scenario: Rechazo en reschedule_appointment no genera entrada
- **GIVEN** `T1` en `reservado` de 10:00 a 10:30 hora local (`2026-10-20T13:00:00Z` a `2026-10-20T13:30:00Z`), otro turno `T3` de `P1` de 11:00 a 11:30 hora local (`2026-10-20T14:00:00Z` a `2026-10-20T14:30:00Z`), recepción `U2` y `context.now` a las 09:00 hora local (`2026-10-20T12:00:00Z`)
- **WHEN** se intenta reprogramar `T1` a las 11:00 hora local (`2026-10-20T14:00:00Z`) chocando con `T3`
- **THEN** devuelve `Rejected` con `PROFESSIONAL_OVERLAP` y no devuelve `Ok` ni entrada `AppointmentStatusChange` alguna

## MODIFIED Requirements

### Requirement: Operaciones con resultado de agenda y copia
cancel_appointment SHALL recibir appointment, actor, now, professional_name y tz. change_status SHALL recibir appointment, target, actor, now, professional_name y tz. Ambas SHALL devolver ValidationResult, con el Ok de agenda y sus campos appointment y status_change, o Rejected no vacío de Violation. En éxito SHALL devolver copia cambiando solo status; en rechazo SHALL conservar el original sin cambios. Los ids y el reloj se reciben; no se generan. El Ok de catálogo y los contratos previos MUST permanecer compatibles.

#### Scenario: Cancelar reservado
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se llama cancel_appointment
- **THEN** devuelve Ok.appointment con copia cancelada, mismo id, paciente, profesional, sillón, prestación e intervalo UTC, Ok.status_change de reservado a cancelado y original reservado

#### Scenario: Confirmar reservado
- **GIVEN** T1 reservado y administración U3, now 09:00 local
- **WHEN** change_status solicita CONFIRMED
- **THEN** devuelve Ok.appointment con copia confirmada, demás campos intactos, Ok.status_change de reservado a confirmado y original reservado

#### Scenario: Rechazo no altera turno
- **GIVEN** T1 atendido y T2 cancelado, recepción autorizada
- **WHEN** se pide cancelar T1 y confirmar T2 por separado
- **THEN** cada resultado es Rejected y todos los campos de ambos originales siguen iguales

### Requirement: Pureza y compatibilidad
Las operaciones SHALL ser síncronas, totalmente tipadas y sin Any, reloj global, generación de ids, I/O, Pydantic, FastAPI, SQLAlchemy o Redis. SHALL pasar las guardias vigentes sin modificar la guardia de dependencias ni su allowlist. La creación de turnos y el catálogo MUST conservar mensajes, y el Ok de catálogo MUST permanecer separado del Ok de agenda con historial.

#### Scenario: Guardias sobre dominio real
- **GIVEN** todos los módulos reales de app/domain, incluyendo transitions
- **WHEN** se analizan con guardia de imports y reloj existentes
- **THEN** no hay imports prohibidos ni accesos de reloj; la allowlist de dependencias permanece sin cambios

#### Scenario: Alta y catálogo conservan payload
- **GIVEN** una nueva reserva válida con changed_by y un alta de profesional válida con literales ficticios
- **WHEN** se ejecutan sus operaciones públicas vigentes
- **THEN** agenda devuelve Ok con appointment reservado y status_change inicial, mientras catálogo conserva su Ok.entity sin historial ni actor

### Requirement: Pureza y compatibilidad de reprogramar
La operación de reprogramar SHALL reutilizar `validate_new_appointment` sin duplicar reglas RN-AG. SHALL pasar las guardias vigentes sin modificar la guardia de dependencias ni su allowlist. No SHALL añadirse códigos `ViolationCode` nuevos ni cambios en `OCCUPYING_STATUSES`. El alta de turnos y el catálogo MUST conservar mensajes y contratos; en particular, el mensaje de `IN_THE_PAST` del alta conserva exactamente "no se pueden dar turnos en el pasado".

#### Scenario: El alta conserva el mensaje del pasado
- **GIVEN** un alta de turno con inicio en el pasado, now 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC)
- **THEN** el mensaje de `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado." (sin "reprogramar")

#### Scenario: Sin códigos nuevos ni cambios de ocupación
- **WHEN** se inspecciona `ViolationCode` y `OCCUPYING_STATUSES`
- **THEN** no se agregan códigos de violación y el conjunto de ocupación sigue exactamente `reservado`, `confirmado`, `atendido`
