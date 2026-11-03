# appointment-lifecycle

## Purpose

Cancelar y cambiar estados mediante funciones puras con actor, tiempo, tabla única y mensajes explicativos, sin historial ni reprogramación.

## ADDED Requirements

Convenciones: datos ficticios. T1 pertenece a P1, Dra. Laura Quiroga, en S1 Sillón 1, martes 20/10/2026 de 10:00 a 10:30 Buenos Aires (13:00–13:30 UTC). T2 pertenece a P2, Dra. Inés Molina, en S2, de 11:00 a 11:30 local (14:00–14:30 UTC). Actor Laura: user_id U1 distinto de P1, rol ODONTOLOGO y professional_id P1. Recepción U2 y administración U3 tienen professional_id None. Todos los identificadores se concretan como UUID literales y distintos en tests. now habitual 20/10/2026 09:00 local (12:00 UTC); escenarios de operaciones que aíslan la política usan actor autorizado y now igual al inicio de su turno (13:00 UTC para T1, 14:00 UTC para T2); can_transition no recibe contexto. Zona inyectada America/Argentina/Buenos_Aires. Donde corresponda usar validate_new_appointment, paciente y referencias existen/activos, duración30 válida, horario de día completo y sin bloqueos ni otros turnos.

### Requirement: Tabla única de transiciones ordinarias
El dominio SHALL representar RN-TU-02 una sola vez en appointment/transitions.py como dict privado del módulo declarado `Mapping[AppointmentStatus, frozenset[AppointmentStatus]]`, con Mapping de collections.abc o typing ya permitidos e inmutabilidad del mapa garantizada por el tipo para mypy y SHALL ofrecer consulta pública can_transition(origin, target). RESERVED permite CONFIRMED, ATTENDED, NO_SHOW, CANCELLED; CONFIRMED permite ATTENDED, NO_SHOW, CANCELLED; ATTENDED, NO_SHOW, CANCELLED no permiten destinos. Son exactamente siete aristas. Toda diagonal y todo destino RESERVED MUST ser inválido. SU-03 queda confirmada por la autora para este change. La reprogramación no forma parte de esta tabla.

#### Scenario: Todos los pares de estados
- **GIVEN** los cinco estados, con producto cartesiano de origen y destino
- **WHEN** se consulta cada uno de los 25 pares mediante can_transition
- **THEN** se aceptan exactamente las siete aristas descritas, según un oráculo independiente de la tabla productiva
- **AND** reservado a confirmado y confirmado a ausente son verdaderos; confirmado a reservado y atendido a confirmado son falsos

#### Scenario: Mapa y destinos no mutables
- **GIVEN** el dict privado del módulo declarado como Mapping[AppointmentStatus, frozenset[AppointmentStatus]]
- **WHEN** mypy comprueba un intento de asignar otro conjunto a RESERVED o mutar el conjunto de destinos de CONFIRMED
- **THEN** ambos intentos son rechazados por el contrato de tipos; no se exige que el dict rechace asignaciones en ejecución

### Requirement: Actor tipado con identidad profesional explícita
Actor SHALL ser dataclass frozen/slots con user_id UUID, role Role y professional_id UUID opcional por defecto None. Role SHALL contener ODONTOLOGO, RECEPCION y ADMINISTRADOR. ODONTOLOGO sin professional_id MUST lanzar ValueError al construir por incoherencia de programación. Los otros roles MUST poder construirse sin vínculo profesional. La propiedad SHALL compararse mediante professional_id, nunca user_id. El dominio MUST NOT autenticar JWT ni consultar usuarios.

#### Scenario: Odontólogo vinculado
- **GIVEN** U1 distinto de P1 y rol ODONTOLOGO con professional_id P1
- **WHEN** se construye el actor y se intenta cambiar role o professional_id
- **THEN** conserva sus tres campos y las mutaciones fallan por inmutabilidad

#### Scenario: Odontólogo sin vínculo
- **WHEN** se construye ODONTOLOGO omitiendo professional_id o pasándolo como None
- **THEN** en ambos casos lanza ValueError de programación, no Rejected

#### Scenario: Roles de gestión sin profesional
- **WHEN** se construyen RECEPCION U2 y ADMINISTRADOR U3 sin professional_id
- **THEN** ambos actores son válidos y conservan None

### Requirement: Operaciones con resultado de agenda y copia
cancel_appointment SHALL recibir appointment, actor, now, professional_name y tz. change_status SHALL recibir appointment, target, actor, now, professional_name y tz. Ambas SHALL devolver ValidationResult, con el Ok de agenda y su campo appointment vigente, o Rejected no vacío de Violation. En éxito SHALL devolver copia cambiando solo status; en rechazo SHALL conservar el original sin cambios. Los ids y el reloj se reciben; no se generan. MUST NOT devolver historial. El Ok de catálogo y los contratos previos MUST permanecer compatibles.

#### Scenario: Cancelar reservado
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se llama cancel_appointment
- **THEN** devuelve Ok.appointment con copia cancelada, mismo id, paciente, profesional, sillón, prestación e intervalo UTC; original reservado

#### Scenario: Confirmar reservado
- **GIVEN** T1 reservado y administración U3, now 09:00 local
- **WHEN** change_status solicita CONFIRMED
- **THEN** devuelve Ok.appointment con copia confirmada, demás campos intactos y original reservado, sin historial

#### Scenario: Rechazo no altera turno
- **GIVEN** T1 atendido y T2 cancelado, recepción autorizada
- **WHEN** se pide cancelar T1 y confirmar T2 por separado
- **THEN** cada resultado es Rejected y todos los campos de ambos originales siguen iguales

### Requirement: Errores de contrato separados del negocio
Un now sin zona MUST lanzar ValueError en ambas operaciones. Un now aware SHALL normalizarse a UTC conservando su instante. change_status con target CANCELLED MUST lanzar ValueError que indique usar cancel_appointment; esta guarda de programación precede los permisos. target RESERVED MUST devolver INVALID_TRANSITION para actor autorizado, incluso desde RESERVED; no debe lanzar ni reprogramar. Otros fallos de negocio MUST devolverse como Violation.

#### Scenario: Now naive en ambas operaciones
- **GIVEN** T1 reservado y recepción U2
- **WHEN** cancelar o confirmar reciben now 2026-10-20T09:00:00 sin zona
- **THEN** cada llamada lanza ValueError que indica que now necesita zona

#### Scenario: Now equivalente en otra zona
- **GIVEN** T1 confirmado y recepción U2
- **WHEN** se marca atendido con now 10:00-03:00 en un caso y now 14:00+01:00 en otro, el mismo 20/10/2026
- **THEN** ambos instantes equivalen a 13:00 UTC y se aceptan con la misma copia atendida

#### Scenario: Cancelar por función incorrecta
- **GIVEN** T1 reservado y recepción U2 en un caso, odontólogo ajeno en otro
- **WHEN** change_status recibe CANCELLED
- **THEN** ambos casos lanzan ValueError indicando usar cancel_appointment, sin producir FORBIDDEN_OPERATION ni cambiar T1

#### Scenario: Destino reservado no reprograma
- **GIVEN** T1 reservado en un caso y confirmado en otro, recepción U2
- **WHEN** change_status recibe RESERVED
- **THEN** devuelve solo INVALID_TRANSITION y conserva estado e intervalo originales

### Requirement: Permisos por operación y propiedad
Para CONFIRMED, ATTENDED, NO_SHOW, ODONTOLOGO SHALL poder cambiar solo turnos cuyo professional_id coincida con actor.professional_id. ODONTOLOGO MUST NOT cancelar ningún turno, ni propio. RECEPCION y ADMINISTRADOR SHALL poder usar ambas operaciones sobre todos. La política específica de RBAC prevalece sobre la frase general de CHANGES y el disparador de Flujo3. Permiso fallido SHALL producir FORBIDDEN_OPERATION.

#### Scenario: Odontólogo cambia propios
- **GIVEN** Laura U1/P1 y T1 reservado
- **WHEN** confirma a las 09:00, marca atendido desde reservado a las 10:00 y marca ausente desde confirmado a las 10:00, en casos independientes
- **THEN** los tres resultados son Ok, aun siendo U1 distinto de P1

#### Scenario: Odontólogo no cambia ajenos
- **GIVEN** Laura U1/P1 y T2 reservado de P2
- **WHEN** solicita confirmado o atendido, con tiempo suficiente en cada caso
- **THEN** cada resultado contiene solo FORBIDDEN_OPERATION, sin alterar T2

#### Scenario: Odontólogo nunca cancela
- **GIVEN** Laura U1/P1, T1 propio reservado y T2 ajeno confirmado
- **WHEN** intenta cancelar cada uno por cancel_appointment
- **THEN** ambos producen solo FORBIDDEN_OPERATION

#### Scenario: Gestión opera todos
- **GIVEN** recepción U2 y administración U3, T1 y T2 reservados
- **WHEN** cada actor confirma y cancela cada turno en casos independientes
- **THEN** todos los resultados son Ok y ningún permiso depende de professional_id

### Requirement: Cancelación sin anticipación y estados terminales
cancel_appointment SHALL usar como destino CANCELLED y aceptar únicamente RESERVED/CONFIRMED. No SHALL imponer anticipación mínima ni rechazar por haber pasado inicio o fin. Los tres estados terminales MUST producir INVALID_TRANSITION para actor autorizado. SU-08 queda confirmada por la autora para este change.

#### Scenario: Cancelar confirmado antes del inicio
- **GIVEN** T1 confirmado, administración U3 y now 09:59:59 local
- **WHEN** se cancela
- **THEN** devuelve Ok con copia cancelada

#### Scenario: Cancelar después del inicio y fin
- **GIVEN** T1 reservado con now 10:15 local en un caso y confirmado con now 11:00 local en otro, recepción U2
- **WHEN** se cancela cada uno
- **THEN** ambos son Ok sin error temporal

#### Scenario: Cancelar terminales
- **GIVEN** T1 en atendido, ausente o cancelado, en casos separados, recepción U2
- **WHEN** se cancela
- **THEN** cada resultado contiene solo INVALID_TRANSITION

### Requirement: Tiempo para atendido y ausente
Marcar ATTENDED o NO_SHOW SHALL exigir now >= appointment.start_at, con comparación de instantes completos, incluidos segundos y microsegundos, sin tolerancia ni truncado; el fin MUST NOT intervenir. Si now < start_at SHALL devolver STATUS_CHANGE_TOO_EARLY. CONFIRMED MUST NOT tener restricción temporal. El dominio MUST recibir now y MUST NOT leer el reloj global.

#### Scenario: Ambos destinos antes de inicio
- **GIVEN** T1 reservado, recepción U2, now 09:00 local
- **WHEN** se pide atendido o ausente por separado
- **THEN** cada resultado contiene solo STATUS_CHANGE_TOO_EARLY con el destino solicitado

#### Scenario: Igualdad exacta con inicio
- **GIVEN** T1 confirmado, recepción U2, now 10:00 local/13:00 UTC
- **WHEN** se pide atendido o ausente por separado
- **THEN** ambos son Ok

#### Scenario: Un microsegundo antes
- **GIVEN** T1 reservado y now 12:59:59.999999 UTC
- **WHEN** recepción pide atendido o ausente
- **THEN** ambos producen STATUS_CHANGE_TOO_EARLY

#### Scenario: Desde inicio sin esperar fin
- **GIVEN** T1 reservado y now 13:00:00.000001 UTC en un caso,13:15 UTC en otro
- **WHEN** recepción marca atendido y ausente en casos independientes
- **THEN** todos son Ok, aunque now sea anterior al fin13:30 UTC

#### Scenario: Confirmar sin regla temporal
- **GIVEN** T1 reservado, recepción U2, now 09:00 local en un caso y11:00 local en otro
- **WHEN** confirma
- **THEN** ambos son Ok

### Requirement: Diagonales inválidas
Los cinco pedidos de permanecer en el estado actual MUST rechazarse como INVALID_TRANSITION para actor autorizado. Para cancelado SHALL usarse cancel_appointment; los otros cuatro destinos SHALL evaluarse por change_status. No SHALL aplicarse la idempotencia del catálogo al ciclo de vida.

#### Scenario: Diagonales de cambio de estado
- **GIVEN** T1 en reservado, confirmado, atendido y ausente, casos independientes, recepción U2 y now 13:30 UTC
- **WHEN** change_status solicita el mismo estado
- **THEN** cada caso devuelve solo INVALID_TRANSITION

#### Scenario: Cancelación repetida
- **GIVEN** T1 cancelado y administración U3
- **WHEN** se llama cancel_appointment
- **THEN** devuelve solo INVALID_TRANSITION, sin copia aceptada ni historial

### Requirement: Composición de violaciones con prioridad
Tras verificar errores de contrato, el dominio SHALL evaluar permiso primero y cortar si falla, devolviendo exclusivamente FORBIDDEN_OPERATION. Para actor autorizado SHALL acumular todas las aplicables en orden INVALID_TRANSITION y STATUS_CHANGE_TOO_EARLY. El tiempo SHALL evaluarse para ATTENDED/NO_SHOW aunque la arista sea inválida. Rejected SHALL contener tuple no vacío y MUST NOT modificar turno.

#### Scenario: Permiso oculta fallos posteriores
- **GIVEN** Laura U1/P1, T2 ajeno cancelado, now 09:00 local
- **WHEN** pide atendido o ausente por separado
- **THEN** cada resultado contiene solo FORBIDDEN_OPERATION, sin errores de transición ni tiempo

#### Scenario: Transición y tiempo juntos
- **GIVEN** T1 cancelado y recepción U2, now 09:00 local
- **WHEN** pide atendido o ausente por separado
- **THEN** cada resultado contiene exactamente INVALID_TRANSITION y STATUS_CHANGE_TOO_EARLY, en ese orden

#### Scenario: Solo transición con tiempo cumplido
- **GIVEN** T1 atendido y now 13:30 UTC, recepción U2
- **WHEN** pide ausente o confirmado por separado
- **THEN** cada caso produce solo INVALID_TRANSITION

### Requirement: Mensajes exactos y metadatos
Las tres violaciones SHALL incluir mensajes en español con nombre recortado mediante strip (sin colapsar espacios internos), fecha del inicio e intervalo en hora local inyectada. Nombre vacío/blanco SHALL usar `el profesional`. SHALL reutilizar formatos locales vigentes: fecha dd/mm/aaaa, horas HH:MM o HH:MM:SS si hay segundos/fracciones; now con fecha y segundos siempre. Los metadatos reference_kind, conflicting_appointment_id, conflicting_block_id y conflicting_interval MUST ser None. Los textos exactos son los siguientes escenarios; variar estados/datos según el caso conservando plantilla.

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

### Requirement: Liberación por estado con agenda existente
Una cancelación aceptada SHALL liberar profesional y sillón mediante la exclusión ya existente de CANCELLED de OCCUPYING_STATUSES. El conjunto SHALL conservar exactamente RESERVED, CONFIRMED, ATTENDED. MUST NOT borrar turno, quitar recursos ni modificar reglas de creación. La composición SHALL usar la copia devuelta en lugar de la versión previa. NO_SHOW SHALL seguir sin ocupar y ATTENDED SHALL seguir ocupando.

#### Scenario: Cancelar y volver a reservar ambos recursos
- **GIVEN** T1 reservado en un caso y confirmado en otro, recepción U2, now 09:00 local y contexto válido
- **WHEN** se cancela, se reemplaza en existentes por Ok.appointment y se pide otro turno P1/S1 de 10:00 a 10:30 local
- **THEN** la nueva reserva es Ok; T1 devuelto sigue existiendo cancelado con mismos recursos/intervalo

#### Scenario: Antes de cancelar ocupa ambos recursos
- **GIVEN** T1 reservado en un caso y confirmado en otro, contexto válido
- **WHEN** se pide otro turno P1/S1 en el mismo intervalo con la versión original aún en existentes
- **THEN** aparecen PROFESSIONAL_OVERLAP y CHAIR_OVERLAP, en el orden vigente

#### Scenario: Regresión de estados ocupantes
- **GIVEN** T1 atendido en un caso y ausente en otro y contexto de nueva reserva válido con now previo
- **WHEN** se pide otro turno P1/S1 en el mismo intervalo
- **THEN** atendido produce ambos solapamientos y ausente no produce ninguno, como antes de C-10

### Requirement: Pureza y compatibilidad
Las operaciones SHALL ser síncronas, totalmente tipadas y sin Any, reloj global, generación de ids, I/O, Pydantic, FastAPI, SQLAlchemy o Redis. SHALL pasar las guardias vigentes sin modificar la guardia de dependencias ni su allowlist. La creación de turnos y el catálogo MUST conservar mensajes y contratos. No SHALL añadirse historial ni reprogramación.

#### Scenario: Guardias sobre dominio real
- **GIVEN** todos los módulos reales de app/domain, incluyendo transitions
- **WHEN** se analizan con guardia de imports y reloj existentes
- **THEN** no hay imports prohibidos ni accesos de reloj; la allowlist de dependencias permanece sin cambios

#### Scenario: Alta y catálogo conservan payload
- **GIVEN** una nueva reserva válida y un alta de profesional válida con literales ficticios
- **WHEN** se ejecutan sus operaciones públicas vigentes
- **THEN** agenda conserva Ok.appointment reservado y catálogo su Ok.entity; no reciben historial ni actor obligatorio nuevo
