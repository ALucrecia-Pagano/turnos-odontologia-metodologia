# Spec Delta: appointment-lifecycle

## MODIFIED Requirements

### Requirement: Tabla única de transiciones ordinarias
El dominio SHALL definir RN-TU-02 una vez en `appointment/transitions.py` como dict privado `Mapping[AppointmentStatus, frozenset[AppointmentStatus]]` (`collections.abc`/`typing`, inmutable en mypy) y exponer `can_transition(origin, target)`. `RESERVED` permite `CONFIRMED`, `ATTENDED`, `NO_SHOW`, `CANCELLED`; `CONFIRMED`, los tres últimos; `ATTENDED`, `NO_SHOW` y `CANCELLED`, ninguno (7 aristas, SU-03). Diagonales y destino `RESERVED` MUST ser inválidos; reprogramar es aparte.

#### Scenario: Todos los pares de estados
- **GIVEN** los cinco estados, con producto cartesiano de origen y destino
- **WHEN** se consulta cada uno de los 25 pares mediante can_transition
- **THEN** se aceptan exactamente las siete aristas descritas, según un oráculo independiente de la tabla productiva
- **AND** reservado a confirmado y confirmado a ausente son verdaderos; confirmado a reservado y atendido a confirmado son falsos

#### Scenario: Mapa y destinos no mutables
- **GIVEN** el dict privado del módulo declarado como Mapping[AppointmentStatus, frozenset[AppointmentStatus]]
- **WHEN** mypy comprueba un intento de asignar otro conjunto a RESERVED o mutar el conjunto de destinos de CONFIRMED
- **THEN** ambos intentos son rechazados por el contrato de tipos; no se exige que el dict rechace asignaciones en ejecución

### Requirement: Operaciones con resultado de agenda y copia
`cancel_appointment(appointment, actor, now, professional_name, tz)` y `change_status(appointment, target, actor, now, professional_name, tz)` SHALL devolver `ValidationResult`: `Ok` de agenda (con `appointment` y `status_change`) o `Rejected` no vacío de `Violation`. En éxito SHALL devolver copia cambiando solo `status`; en rechazo SHALL conservar el original sin cambios. Los ids y el reloj se reciben sin generarse. El `Ok` de catálogo y los contratos previos MUST permanecer compatibles.

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

### Requirement: Mensajes exactos y metadatos
Las tres violaciones SHALL usar las plantillas en español de los escenarios, con el nombre recortado con `strip` sin colapsar espacios internos (`el profesional` si queda vacío), fecha `dd/mm/aaaa` e intervalo en hora local inyectada (`HH:MM` o `HH:MM:SS` con segundos/fracciones; `now` siempre con fecha y segundos). Los metadatos `reference_kind`, `conflicting_appointment_id`, `conflicting_block_id` y `conflicting_interval` MUST ser `None`.

#### Scenario: Texto de transición inválida
- **GIVEN** T1 atendido, recepción U2 y now 09:00 local
- **WHEN** se cancela
- **THEN** mensaje exacto: `El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".`

#### Scenario: Texto de atención temprana
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** pide atendido
- **THEN** mensaje exacto: `El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "atendido" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).`

#### Scenario: Texto de ausencia temprana
- **GIVEN** T1 confirmado y recepción U2, now 09:00 local
- **WHEN** pide ausente
- **THEN** mensaje exacto: `El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "ausente" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).`

#### Scenario: Texto de cambio ajeno
- **GIVEN** actor odontólogo de P2 y T1 reservado, now 09:00 local
- **WHEN** pide confirmado
- **THEN** mensaje exacto: `No tiene permiso para cambiar el estado del turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): un odontólogo solo puede cambiar el estado de sus propios turnos.`

#### Scenario: Texto de cancelación prohibida
- **GIVEN** Laura U1/P1 y T1 reservado, now 09:00 local
- **WHEN** pide cancelar
- **THEN** mensaje exacto: `No tiene permiso para cancelar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden cancelar turnos.`

#### Scenario: Nombre con espacios y fallback
- **GIVEN** T1 atendido y recepción U2
- **WHEN** se cancela con professional_name `"  Dra. Laura Quiroga  "`, `""` y `"   "` por separado
- **THEN** el primer texto coincide exactamente con «Texto de transición inválida»; los otros dos son `El turno de el profesional del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".`
- **AND** para nombre `"Dra. Laura  Quiroga"` se conservan ambos espacios internos en el mensaje

#### Scenario: Fecha local distinta de UTC
- **GIVEN** turno de Laura del 20/10/2026 de 22:00 a 22:30 local (21/10 de 01:00 a 01:30 UTC), atendido y recepción U2
- **WHEN** se cancela
- **THEN** mensaje exacto: `El turno de Dra. Laura Quiroga del 20/10/2026 de 22:00 a 22:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".`

#### Scenario: Now con segundos conservados
- **GIVEN** T1 reservado, recepción U2 y now 09:59:30 local
- **WHEN** pide atendido
- **THEN** mensaje exacto: `El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "atendido" antes del inicio (momento actual: 20/10/2026 09:59:30, hora local).`

#### Scenario: Metadatos sin falso conflicto
- **GIVEN** rechazos independientes por transición, tiempo y cada permiso anterior
- **WHEN** se inspeccionan sus violaciones
- **THEN** código/mensaje coinciden con el caso y todos los metadatos de referencia/conflicto son None; T1 no se usa como conflicting_appointment_id
