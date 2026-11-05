# Spec Delta

## ADDED Requirements

### Requirement: Persistencia atómica de alta de turnos e historial inicial
El servicio de turnos SHALL persistir en una única transacción atómica el turno en `appointment` y su entrada inicial en `appointment_status_change` con `from_status` nulo, asignando `created_at` y `updated_at` iguales a `status_change.changed_at`. Si el dominio rechaza el alta o si la inserción del historial falla, el servicio SHALL revertir la transacción completa y no SHALL persistir ninguna fila.

#### Scenario: Alta aceptada persiste turno e historial con marcas de tiempo sincronizadas
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001`, el sillón `00000000-0000-0000-0000-0000000000b1`, la prestación `00000000-0000-0000-0000-0000000000d4` de 30 minutos y el paciente `00000000-0000-0000-0000-0000000000c1` persistidos
- **WHEN** se solicita el alta del turno `00000000-0000-0000-0000-000000000a01` para el lunes `2026-11-09T13:00:00Z` con `changed_by=00000000-0000-0000-0000-000000000099` y `now=2026-11-05T12:00:00Z`
- **THEN** se confirman exactamente una fila en `appointment` con estado `reservado` y `created_at = updated_at = 2026-11-05T12:00:00Z` y una fila en `appointment_status_change` con `from_status` nulo, `to_status = 'reservado'`, `changed_by = 00000000-0000-0000-0000-000000000099` y `changed_at = 2026-11-05T12:00:00Z`

#### Scenario: Alta rechazada por solapamiento no escribe en la base
- **GIVEN** el turno `00000000-0000-0000-0000-000000000a01` persistido para el profesional `00000000-0000-0000-0000-000000000001` de `13:00:00Z` a `13:30:00Z`
- **WHEN** se solicita otra alta para el mismo profesional que ocupa de `13:15:00Z` a `13:45:00Z`
- **THEN** la operación devuelve `Rejected` con código `PROFESSIONAL_OVERLAP` y el conteo de filas en `appointment` no aumenta

#### Scenario: Falla en inserción de historial revierte el turno
- **GIVEN** una solicitud de alta válida para el turno `00000000-0000-0000-0000-000000000a02`
- **WHEN** ocurre una falla de integridad provocada durante la inserción de su fila de historial
- **THEN** la transacción revierte por completo y la consulta de `appointment` para `00000000-0000-0000-0000-000000000a02` devuelve vacío

### Requirement: Persistencia transaccional de cambios de estado y cancelaciones
El servicio de turnos SHALL actualizar transaccionalmente el estado del turno en `appointment`, actualizar `updated_at` al valor de `status_change.changed_at` preservando el `created_at` original, e insertar la entrada en `appointment_status_change`. Una operación sobre un turno que no existe en la base SHALL devolver `None`.

#### Scenario: Confirmación de turno actualiza estado y registra historial
- **GIVEN** el turno `00000000-0000-0000-0000-000000000a01` en estado `reservado` con `created_at = updated_at = 2026-11-05T12:00:00Z`
- **WHEN** se confirma el turno en el instante `2026-11-06T10:00:00Z` por el usuario `00000000-0000-0000-0000-000000000099`
- **THEN** la fila en `appointment` pasa a estado `confirmado` con `updated_at = 2026-11-06T10:00:00Z` conservando `created_at = 2026-11-05T12:00:00Z` y se inserta una fila de historial con `from_status = 'reservado'` y `to_status = 'confirmado'`

#### Scenario: Cancelación de turno actualiza estado a cancelado y registra historial
- **GIVEN** el turno `00000000-0000-0000-0000-000000000a01` en estado `reservado` persistido
- **WHEN** se cancela el turno en el instante `2026-11-06T11:00:00Z` por el usuario `00000000-0000-0000-0000-000000000099`
- **THEN** la fila en `appointment` pasa a estado `cancelado` con `updated_at = 2026-11-06T11:00:00Z` y se inserta una fila de historial con `from_status = 'reservado'` y `to_status = 'cancelado'`

#### Scenario: Operación de estado sobre turno inexistente devuelve None
- **WHEN** se intenta cambiar el estado del turno inexistente `00000000-0000-0000-0000-000000000a99`
- **THEN** el servicio devuelve `None` sin lanzar excepción y sin alterar la base

### Requirement: Persistencia de reprogramaciones con detalle tipado
El servicio de turnos SHALL actualizar los campos de agenda del turno reprogramado, actualizar `updated_at` a `status_change.changed_at`, e insertar la entrada de historial con las 8 columnas dedicadas de `RescheduleDetail` conteniendo los intervalos y las referencias anteriores y nuevas.

#### Scenario: Reprogramación de turno persiste ocho columnas del detalle
- **GIVEN** el turno `00000000-0000-0000-0000-000000000a01` con el profesional `00000000-0000-0000-0000-000000000001` y sillón `00000000-0000-0000-0000-0000000000b1` de `13:00:00Z` a `13:30:00Z`
- **WHEN** se reprograma el turno al profesional `00000000-0000-0000-0000-000000000002` y sillón `00000000-0000-0000-0000-0000000000b2` de `15:00:00Z` a `15:30:00Z` en el instante `2026-11-06T14:00:00Z`
- **THEN** la fila en `appointment` actualiza profesional, sillón, inicio, fin y `updated_at = 2026-11-06T14:00:00Z`, y la fila en `appointment_status_change` contiene `from_status = 'reservado'`, `to_status = 'reservado'`, `previous_start_at = 13:00:00Z`, `new_start_at = 15:00:00Z`, `previous_professional_id = 00000000-0000-0000-0000-000000000001`, `new_professional_id = 00000000-0000-0000-0000-000000000002`, `previous_chair_id = 00000000-0000-0000-0000-0000000000b1` y `new_chair_id = 00000000-0000-0000-0000-0000000000b2`

### Requirement: Restricciones CHECK en tablas de turnos e historial
La tabla `appointment` SHALL rechazar mediante restricciones `CHECK` nombradas cualquier inserción con estado ajeno a la lista permitida o con inicio no anterior al fin. La tabla `appointment_status_change` SHALL rechazar mediante una restricción `CHECK` nombrada cualquier inserción donde las ocho columnas del detalle de reprogramación no sean todas nulas o todas no nulas.

#### Scenario: CHECK de estado de turno rechaza valor inválido
- **WHEN** una inserción directa en `appointment` intenta guardar `status = 'en_espera'`
- **THEN** PostgreSQL rechaza la fila con error de restricción identificando `ck_appointment_status`

#### Scenario: CHECK de intervalo rechaza fin anterior al inicio
- **WHEN** una inserción directa en `appointment` intenta guardar `start_at = 2026-11-09T14:00:00Z` y `end_at = 2026-11-09T13:00:00Z`
- **THEN** PostgreSQL rechaza la fila con error de restricción identificando `ck_appointment_interval_order`

#### Scenario: CHECK todo o nada rechaza detalle de reprogramación parcial
- **WHEN** una inserción directa en `appointment_status_change` asigna `previous_start_at` con valor y deja `previous_end_at` nulo
- **THEN** PostgreSQL rechaza la fila con error de restricción identificando `ck_appointment_status_change_reschedule_all_or_none`

### Requirement: Historial de turnos append-only protegido por trigger
La tabla `appointment_status_change` SHALL estar protegida por un trigger de base de datos que impida cualquier operación de actualización o borrado directo, garantizando la inmutabilidad física del historial funcional.

#### Scenario: Trigger de base rechaza UPDATE directo en historial
- **GIVEN** una fila de historial persistida en `appointment_status_change`
- **WHEN** se ejecuta una sentencia `UPDATE` directa sobre esa fila
- **THEN** el trigger de PostgreSQL aborta la operación con excepción que indica que la tabla es solo de inserción

#### Scenario: Trigger de base rechaza DELETE directo en historial
- **GIVEN** una fila de historial persistida en `appointment_status_change`
- **WHEN** se ejecuta una sentencia `DELETE` directa sobre esa fila
- **THEN** el trigger de PostgreSQL aborta la operación con excepción que indica que la tabla es solo de inserción

### Requirement: Lector SQL de turnos en rango para disponibilidad
El repositorio SHALL proveer la implementación SQL del protocolo `AppointmentReader` devolviendo exclusivamente los turnos del profesional cuyo intervalo semiabierto se solapa con el rango consultado, con instantes en UTC y ordenados por inicio e id.

#### Scenario: Lector SQL filtra turnos del profesional que solapan el rango
- **GIVEN** un turno del profesional `00000000-0000-0000-0000-000000000001` de `10:00:00Z` a `11:00:00Z` y otro turno de `12:00:00Z` a `13:00:00Z`
- **WHEN** se consulta el lector SQL para ese profesional en el rango de `10:30:00Z` a `11:30:00Z`
- **THEN** devuelve únicamente el primer turno con instantes en UTC, excluyendo el turno que inicia a las `12:00:00Z`

### Requirement: Serialización pesimista ante colisiones concurrentes
El servicio SHALL bloquear con `SELECT ... FOR UPDATE` las filas de profesional y sillón ordenadas lexicográficamente antes de consultar el contexto en altas, y SHALL bloquear la fila de turno antes de evaluar transiciones. Dos operaciones simultáneas sobre el mismo recurso físico SHALL ejecutarse de forma secuencial, y la segunda SHALL observar los cambios confirmados por la primera.

#### Scenario: Dos altas simultáneas del mismo profesional son serializadas
- **GIVEN** dos conexiones que intentan reservar simultáneamente el turno de `10:00:00Z` a `10:30:00Z` para el profesional `00000000-0000-0000-0000-000000000001` con sillones distintos
- **WHEN** ambas ejecutan concurrentemente con tiempo límite de bloqueo configurado
- **THEN** la primera conexión confirma con `Ok` y la segunda espera el bloqueo y es rechazada con `PROFESSIONAL_OVERLAP`

#### Scenario: Dos altas simultáneas del mismo sillón son serializadas
- **GIVEN** dos conexiones que intentan reservar simultáneamente el turno de `11:00:00Z` a `11:30:00Z` para el sillón `00000000-0000-0000-0000-0000000000b1` con profesionales distintos
- **WHEN** ambas ejecutan concurrentemente con tiempo límite de bloqueo configurado
- **THEN** la primera conexión confirma con `Ok` y la segunda espera el bloqueo y es rechazada con `CHAIR_OVERLAP`

#### Scenario: Transición concurrente conflictiva sobre el mismo turno es serializada con relectura
- **GIVEN** el turno `00000000-0000-0000-0000-000000000a01` en estado `reservado`
- **WHEN** dos conexiones intentan simultáneamente una confirmar y la otra cancelar ese mismo turno
- **THEN** una operación confirma su cambio con `Ok` y la otra relee el nuevo estado dentro del bloqueo y es rechazada con `INVALID_TRANSITION`, dejando exactamente una sola entrada nueva en el historial

### Requirement: Migración reversible de turnos e historial
La revisión de base de datos `20261105_04_turnos_e_historial` SHALL crear las tablas `appointment` y `appointment_status_change` con sus índices, constraints y trigger append-only, y SHALL poder revertirse con `downgrade -1` eliminando ambas tablas y el trigger sin alterar las tablas previas de catálogo, horarios y bloqueos.

#### Scenario: Ciclo upgrade y downgrade menos uno de la migración de turnos
- **WHEN** se ejecuta `upgrade head`, seguido de `downgrade -1` y nuevamente `upgrade head` sobre la base de integración
- **THEN** tras el downgrade desaparecen las tablas `appointment`, `appointment_status_change` y el trigger, conservando las tablas de catálogo y horarios, y al volver a `head` la comparación de metadata no encuentra diferencias

