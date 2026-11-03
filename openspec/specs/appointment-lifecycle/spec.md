# appointment-lifecycle Specification

## Purpose

Convenciones de los escenarios de reprogramar: datos ficticios. T1 pertenece a P1, Dra. Laura Quiroga, en S1 Sillón 1, martes 20/10/2026 de 10:00 a 10:30 hora local (13:00–13:30 UTC), estado `reservado` salvo que se indique. T2 pertenece a P2, Dra. Inés Molina, en S2, de 11:00 a 11:30 hora local (14:00–14:30 UTC). Actor Laura: user_id U1 distinto de P1, rol ODONTOLOGO y professional_id P1. Recepción U2 y administración U3 tienen professional_id None. La prestación de T1 tiene `default_duration_min` 45, salvo que se indique otra; la duración efectiva de T1 es 30 minutos. El reprograma por defecto mueve T1 a las 11:00 hora local (14:00 UTC) y queda de 11:00 a 11:30 hora local (14:00–14:30 UTC), conservando P1/S1 y duración 30. now habitual 20/10/2026 09:00 hora local (12:00 UTC). Zona inyectada America/Argentina/Buenos_Aires. El llamador pasa la agenda completa, incluido el turno a reprogramar; el dominio lo excluye por id. Donde se revalida, paciente y referencias existen y están activos, horario de día completo y sin bloqueos ni otros turnos salvo que se indique.

Transiciones de estado del turno según una tabla única (RN-TU-02); cancelación sin anticipación mínima; atendido y ausente solo desde el inicio del turno con el reloj inyectado; permisos por rol y propiedad (el odontólogo no cancela); la transición al mismo estado es inválida; las operaciones devuelven copias inmutables. Reprogramación solo desde reservado o confirmado, vuelve a reservado con el mismo id, revalida todas las reglas del turno nuevo excluyendo al propio turno y no puede hacerla el odontólogo. Sin historial (C-12).

## Requirements


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

### Requirement: Operación de reprogramar un turno
El dominio SHALL ofrecer `reschedule_appointment`, que revalida el turno nuevo con `validate_new_appointment` y devuelve `ValidationResult`. El turno aceptado SHALL conservar su id y volver a `reservado`. El inicio es obligatorio; profesional, sillón y duración son opcionales (`None` conserva el valor actual). El paciente y la prestación MUST NOT cambiar. Sin duración, SHALL usarse la duración real del turno (fin menos inicio), no la de la prestación.

#### Scenario: Reprogramar válido conserva id y vuelve a reservado
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Ok` y el turno devuelto tiene el mismo id que T1, va de 11:00 a 11:30 hora local (14:00–14:30 UTC) y está en estado `reservado`

#### Scenario: Desde confirmado vuelve a reservado
- **GIVEN** T1 confirmado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Ok` con el turno en estado `reservado` (ya no `confirmado`)

#### Scenario: No choca consigo mismo en su mismo intervalo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 10:00 hora local (13:00 UTC), mismo P1/S1 y duración 30 (su propio intervalo), con T1 incluido en la agenda recibida
- **THEN** el resultado es `Ok`, sin `PROFESSIONAL_OVERLAP` ni `CHAIR_OVERLAP`

#### Scenario: No choca consigo mismo al solapar su intervalo viejo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local, con T1 incluido en la agenda recibida
- **WHEN** se reprograma T1 a las 10:15 hora local (13:15 UTC), mismo P1/S1 y duración 30 (solapa su intervalo viejo 10:00–10:30)
- **THEN** el resultado es `Ok`, sin `PROFESSIONAL_OVERLAP` ni `CHAIR_OVERLAP`

#### Scenario: Cambia solo el profesional y no choca por sillón consigo mismo
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local en S1, sin turnos de P2 en S1 a esa hora, recepción U2 y now 09:00 local, con T1 incluido en la agenda recibida
- **WHEN** se reprograma T1 a las 10:00 hora local (13:00 UTC) cambiando el profesional a P2 y conservando S1 y duración 30
- **THEN** el resultado es `Ok`, sin `CHAIR_OVERLAP` contra T1 (el propio queda excluido) y con profesional P2

#### Scenario: Conserva la duración real si no se indica
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local (duración efectiva 30) con una prestación de default 45, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) sin indicar duración, conservando P1/S1
- **THEN** el resultado es `Ok` con un turno de 11:00 a 11:30 hora local (14:00–14:30 UTC), no de 11:00 a 11:45

#### Scenario: Cambia la duración indicada
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local (duración efectiva 30), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) con duración 60, conservando P1/S1
- **THEN** el resultado es `Ok` con un turno de 11:00 a 12:00 hora local (14:00–15:00 UTC)

#### Scenario: El original no cambia al reprogramar
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado es `Ok` y el T1 original conserva su inicio 13:00 UTC, su fin 13:30 UTC y su estado `reservado`

### Requirement: Auto-exclusión del propio turno al revalidar
El dominio SHALL excluir de la lista de turnos existentes, antes de revalidar, al turno que se reprograma, comparando por id. La corrección de la revalidación MUST NOT depender de que el llamador haya filtrado la lista: el llamador pasa la agenda completa, incluido el turno a reprogramar, y el dominio lo excluye. La exclusión por id es universal y cubre el caso en que solo cambia el profesional y el propio turno seguiría coincidiendo por sillón.

#### Scenario: El dominio excluye al propio aunque el llamador lo incluya
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local, recepción U2, now 09:00 local, y la agenda recibida incluye a T1
- **WHEN** se reprograma T1 a las 10:15 hora local (13:15 UTC), mismo P1/S1 y duración 30
- **THEN** el resultado es `Ok`, porque T1 se excluye antes de evaluar los solapamientos

### Requirement: Precondición de estado de reprogramar
Reprogramar SHALL aceptarse solo desde `reservado` o `confirmado`. Los tres estados terminales (`atendido`, `ausente`, `cancelado`) SHALL rechazarse con una sola violación `INVALID_TRANSITION` y un mensaje dedicado de reprogramar que nombra al profesional, la fecha y el intervalo local del turno, y el estado terminal. La reprogramación no forma parte de la tabla ordinaria RN-TU-02 y MUST NOT usar `can_transition` como precondición.

#### Scenario: Desde cada estado terminal
- **GIVEN** T1 en `atendido` (primer caso), `ausente` (segundo) o `cancelado` (tercero), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** cada resultado es `Rejected` con una sola violación `INVALID_TRANSITION` cuyo mensaje es, respectivamente, "El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no se puede reprogramar porque está en estado terminal "atendido".", "...terminal "ausente"." y "...terminal "cancelado"."

#### Scenario: El turno terminal no se altera
- **GIVEN** T1 atendido y recepción U2, now 09:00 local
- **WHEN** se intenta reprogramar T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado es `Rejected` con `INVALID_TRANSITION` y T1 conserva su estado `atendido` y su intervalo 13:00–13:30 UTC

### Requirement: Permisos de reprogramar
El odontólogo MUST NOT reprogramar ningún turno, ni propio ni ajeno; el intento SHALL devolver una sola violación `FORBIDDEN_OPERATION` con mensaje dedicado de reprogramar. Recepción y administración SHALL poder reprogramar todos los turnos. La política específica RBAC de KB 03 (fila "reprogramar / cancelar") prevalece sobre el disparador de Flujo 2. La propiedad se compara por `professional_id`, nunca `user_id`.

#### Scenario: Odontólogo propio y ajeno no reprograman
- **GIVEN** Laura U1/P1 y T1 propio reservado (primer caso), y Laura U1/P1 con T2 reservado de P2 (segundo caso), now 09:00 local
- **WHEN** Laura intenta reprogramar cada turno a las 11:00 hora local (14:00 UTC)
- **THEN** cada resultado es `Rejected` con una sola violación `FORBIDDEN_OPERATION` cuyo mensaje es "No tiene permiso para reprogramar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden reprogramar turnos." en el primer caso, y "No tiene permiso para reprogramar el turno de Dra. Inés Molina del 20/10/2026 de 11:00 a 11:30 (hora local): solo recepción y administración pueden reprogramar turnos." en el segundo

#### Scenario: Recepción y administración reprograman
- **GIVEN** T1 reservado y now 09:00 local
- **WHEN** recepción U2 (primer caso) y administración U3 (segundo caso) reprograman T1 a las 11:00 hora local (14:00 UTC)
- **THEN** ambos resultados son `Ok` con el turno en `reservado` y ningún permiso depende de `professional_id`

### Requirement: Orden de evaluación de reprogramar
Tras los errores de contrato, el dominio SHALL evaluar permiso, estado y turno nuevo, en ese orden, con cortocircuito. Un actor no autorizado devuelve solo `FORBIDDEN_OPERATION`; un estado terminal, solo `INVALID_TRANSITION`; en otro caso devuelve las violaciones del turno nuevo en el orden RN-AG-12.

#### Scenario: El permiso corta y oculta el resto
- **GIVEN** Laura U1/P1, T1 propio atendido y now 10:30 local (posterior al inicio)
- **WHEN** Laura intenta reprogramar T1 a las 09:00 hora local (12:00 UTC), un slot en el pasado
- **THEN** el resultado contiene solo `FORBIDDEN_OPERATION`, sin `INVALID_TRANSITION` ni `IN_THE_PAST`

#### Scenario: El estado corta y oculta los conflictos del slot
- **GIVEN** T1 cancelado, recepción U2, now 09:00 local y un slot destino 11:00 que chocaría con otro turno
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC)
- **THEN** el resultado contiene solo `INVALID_TRANSITION`, sin `PROFESSIONAL_OVERLAP`

### Requirement: Reprogramar revalida todas las reglas del turno nuevo
Al reprogramar, el dominio SHALL revalidar todas las RN-AG del turno nuevo, incluida la actividad del paciente y de la prestación aunque no cambien. Un profesional o sillón inexistente SHALL dar `UNKNOWN_REFERENCE`, e inactivo, `INACTIVE_REFERENCE`. El pasado SHALL dar `IN_THE_PAST` con el verbo de reprogramar. Las demás violaciones reutilizan los códigos y textos vigentes del alta.

#### Scenario: Choca con otro turno del mismo profesional
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local, un turno T3 de P1 en S2 de 11:00 a 11:30 hora local (14:00–14:30 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `PROFESSIONAL_OVERLAP` cuyo mensaje es exactamente "Dra. Laura Quiroga ya tiene un turno de 11:00 a 11:30 (hora local) que se superpone (turno {id de T3})."

#### Scenario: Choca con otro turno del mismo sillón
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local en S1, un turno T4 de P2 en S1 de 11:00 a 11:30 hora local (14:00–14:30 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `CHAIR_OVERLAP` cuyo mensaje es exactamente "Sillón 1 está ocupado de 11:00 a 11:30 (hora local) por un turno que se superpone (turno {id de T4})."

#### Scenario: Fuera de horario
- **GIVEN** T1 reservado, P1 atiende el martes solo de 09:00 a 11:00 hora local (sin tramo a las 11:00), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `OUTSIDE_WORKING_HOURS`, con el mismo texto exacto que al dar un turno nuevo en ese slot

#### Scenario: Bloqueado
- **GIVEN** T1 reservado, un bloqueo BL1 de P1 de 11:00 a 12:00 hora local (14:00–15:00 UTC), recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `BLOCKED_TIME` con el id de BL1, con el mismo texto exacto que al dar un turno nuevo en ese slot

#### Scenario: Al pasado con verbo de reprogramar
- **GIVEN** T1 reservado y now 10:00:00 hora local (13:00 UTC)
- **WHEN** se reprograma T1 a las 09:00 hora local (12:00 UTC), conservando P1/S1 y duración 30
- **THEN** el resultado es `Rejected` con una violación `IN_THE_PAST` cuyo mensaje es exactamente "El inicio del turno (20/10/2026 09:00, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden reprogramar turnos en el pasado."

#### Scenario: Profesional nuevo inexistente
- **GIVEN** T1 reservado y recepción U2, now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) cambiando el profesional a P3, que no existe
- **THEN** el resultado es `Rejected` con una violación `UNKNOWN_REFERENCE` de tipo `PROFESSIONAL`

#### Scenario: Prestación inactiva al reprogramar
- **GIVEN** T1 reservado y la prestación de T1 está inactiva, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC), conservando P1/S1 y sin indicar duración
- **THEN** el resultado es `Rejected` con una violación `INACTIVE_REFERENCE` de tipo `SERVICE`

### Requirement: Errores de contrato e inmutabilidad de reprogramar
Un `now` sin zona (*naive*) en el contexto MUST rechazarse con `ValueError` al construir el contexto, como en el alta. Los errores de negocio MUST devolverse como `Violation`, nunca como excepción. El turno original MUST permanecer sin cambios ante cualquier rechazo. La operación SHALL ser síncrona, totalmente tipada y sin `Any`, reloj global, generación de ids, I/O, Pydantic, FastAPI, SQLAlchemy ni Redis.

#### Scenario: now naive en el contexto
- **GIVEN** T1 reservado y recepción U2
- **WHEN** se reprograma T1 con un contexto cuyo `now` es 2026-10-20T09:00:00 sin zona
- **THEN** la construcción del contexto lanza `ValueError` que indica que `now` necesita zona

#### Scenario: El original no cambia ante un rechazo de slot
- **GIVEN** T1 reservado de 10:00 a 10:30 hora local y un turno T3 de P1 en S2 de 11:00 a 11:30 hora local, recepción U2 y now 09:00 local
- **WHEN** se reprograma T1 a las 11:00 hora local (14:00 UTC) y choca con T3
- **THEN** el resultado es `Rejected` y T1 conserva su inicio 13:00 UTC, su fin 13:30 UTC y su estado `reservado`

### Requirement: Pureza y compatibilidad de reprogramar
La operación de reprogramar SHALL reutilizar `validate_new_appointment` sin duplicar reglas RN-AG. SHALL pasar las guardias vigentes sin modificar la guardia de dependencias ni su allowlist. No SHALL añadirse historial (C-12), códigos `ViolationCode` nuevos ni cambios en `OCCUPYING_STATUSES`. El alta de turnos y el catálogo MUST conservar mensajes y contratos; en particular, el mensaje de `IN_THE_PAST` del alta conserva exactamente "no se pueden dar turnos en el pasado".

#### Scenario: El alta conserva el mensaje del pasado
- **GIVEN** un alta de turno con inicio en el pasado, now 10:00 hora local (13:00 UTC)
- **WHEN** se pide un turno a las 09:55 hora local (12:55 UTC)
- **THEN** el mensaje de `IN_THE_PAST` es exactamente "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado." (sin "reprogramar")

#### Scenario: Sin códigos nuevos ni cambios de ocupación
- **WHEN** se inspecciona `ViolationCode` y `OCCUPYING_STATUSES`
- **THEN** no se agregan códigos de violación y el conjunto de ocupación sigue exactamente `reservado`, `confirmado`, `atendido`
