# Spec Delta

## ADDED Requirements

### Requirement: Persistencia e ida y vuelta de horarios de atención y bloqueos
La base SHALL persistir `WorkingHours` en `working_hours` (con `id` UUID solo en persistencia, `professional_id`, `weekday` ISO 1..7 y minutos locales `start_minute` y `end_minute` sin conversión) y `Block` en `block` (con `id` UUID, `professional_id`, `start_at` y `end_at` en `timestamptz` UTC y `reason` opcional), devolviendo tipos del dominio.

#### Scenario: Ida y vuelta de tramos horarios semanales
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se guardan los tramos `WorkingHours` del lunes (`weekday=1`) de `540` a `780` y de `900` a `1140`, y del miércoles (`weekday=3`) de `540` a `1440` (`24:00`)
- **THEN** la lectura por profesional y el listado general devuelven instancias `WorkingHours` con esos mismos `professional_id`, `weekday`, `start_minute` y `end_minute`, ordenadas por día e inicio, sin exponer el `id` de la fila

#### Scenario: Ida y vuelta de bloqueos en UTC con y sin motivo
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se guardan el bloqueo `00000000-0000-0000-0000-000000000b01` de `2026-11-10T09:00:00-03:00` a `2026-11-10T12:00:00-03:00` con motivo `"Congreso"` y el bloqueo `00000000-0000-0000-0000-000000000b02` de `2026-11-11T14:00:00-03:00` a `2026-11-11T18:00:00-03:00` con `reason=None`
- **THEN** la lectura por id, por profesional y general devuelve `Block` con instantes en UTC (`12:00` a `15:00` y `17:00` a `21:00` UTC) y conserva `"Congreso"` y `None` respectivamente

### Requirement: Reemplazo transaccional del horario semanal por profesional
El repositorio de horarios SHALL reemplazar en una sola transacción todos los tramos de un profesional tras validar el conjunto completo con `validate_working_hours`. Reemplazar por la secuencia vacía SHALL dejar al profesional sin atención, sin alterar los tramos de otros profesionales.

#### Scenario: Reemplazo de tramos de un profesional sin afectar a otro
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` con tramo el lunes (`weekday=1`, `540` a `780`) y el profesional `00000000-0000-0000-0000-000000000002` con tramo el martes (`weekday=2`, `540` a `780`)
- **WHEN** se reemplaza el horario de `00000000-0000-0000-0000-000000000001` por el jueves (`weekday=4`, `840` a `1080`)
- **THEN** la consulta de `00000000-0000-0000-0000-000000000001` devuelve solo el tramo del jueves (`840` a `1080`) y la de `00000000-0000-0000-0000-000000000002` conserva el martes (`540` a `780`)

#### Scenario: Reemplazo por lista vacía deja al profesional sin horario
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` con tramos persistidos el lunes (`weekday=1`, `540` a `780`)
- **WHEN** se reemplaza su horario por la secuencia vacía `()`
- **THEN** la operación devuelve `Ok(())` y la consulta de tramos del profesional devuelve `()`

### Requirement: Rechazo previo de horarios y bloqueos inválidos sin persistir cambios
Antes de escribir en la base, el repositorio de horarios SHALL validar el conjunto con `validate_working_hours` y el de bloqueos SHALL validar con `validate_block`. Si hay violaciones, SHALL devolver `Rejected` con esas violaciones sin insertar filas nuevas ni modificar ni borrar los datos existentes.

#### Scenario: Rechazo de tramos solapados conserva el horario previo
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` con un tramo persistido el lunes (`weekday=1`, `540` a `780`)
- **WHEN** se intenta reemplazar su horario por dos tramos solapados el martes (`weekday=2`, de `540` a `780` y de `720` a `960`)
- **THEN** el repositorio devuelve `Rejected` con `OVERLAPPING_WORKING_HOURS` y el profesional conserva en la base su tramo del lunes (`540` a `780`)

#### Scenario: Rechazo de tramo inválido conserva el horario previo
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` con un tramo persistido el lunes (`weekday=1`, `540` a `780`)
- **WHEN** se intenta reemplazar su horario por un tramo inválido (`weekday=8`, de `600` a `540`)
- **THEN** el repositorio devuelve `Rejected` con `INVALID_WORKING_HOURS` y el profesional conserva en la base su tramo del lunes (`540` a `780`)

#### Scenario: Rechazo de bloqueo con inicio mayor o igual al fin
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se intenta crear el bloqueo `00000000-0000-0000-0000-000000000b03` con `start_at=2026-11-12T15:00:00Z` y `end_at=2026-11-12T15:00:00Z`
- **THEN** el repositorio devuelve `Rejected` con `INVALID_BLOCK` y no se crea ninguna fila para `00000000-0000-0000-0000-000000000b03`

### Requirement: Restricciones CHECK y de integridad en working_hours y block
Las tablas `working_hours` y `block` SHALL declarar restricciones `CHECK` nombradas para el rango de `weekday` (`1..7`), el rango y orden de minutos (`0 <= start_minute < end_minute <= 1440`) y el orden temporal del bloqueo (`start_at < end_at`). Cualquier `IntegrityError` ajeno a la FK del profesional SHALL propagarse.

#### Scenario: CHECK de base rechaza weekday inválido en working_hours
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se ejecuta un `INSERT` directo en `working_hours` con `weekday=0`
- **THEN** PostgreSQL rechaza la inserción con `IntegrityError` identificando `ck_working_hours_weekday_range`, sin guardar una fila inválida

#### Scenario: CHECK de base rechaza minutos inválidos en working_hours
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se ejecuta un `INSERT` directo en `working_hours` con `start_minute=780` y `end_minute=540`
- **THEN** PostgreSQL rechaza la inserción con `IntegrityError` identificando `ck_working_hours_minute_range`, sin guardar una fila inválida

#### Scenario: CHECK de base rechaza intervalo inválido en block
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` persistido
- **WHEN** se ejecuta un `INSERT` directo en `block` con `start_at=2026-11-12T16:00:00Z` y `end_at=2026-11-12T15:00:00Z`
- **THEN** PostgreSQL rechaza la inserción con `IntegrityError` identificando `ck_block_interval_order`, sin guardar una fila inválida

#### Scenario: Error de integridad no relacionado se propaga
- **GIVEN** el bloqueo `00000000-0000-0000-0000-000000000b04` ya persistido para el profesional `00000000-0000-0000-0000-000000000001`
- **WHEN** se intenta crear otro bloqueo válido con el mismo id `00000000-0000-0000-0000-000000000b04`
- **THEN** el repositorio propaga el `IntegrityError` de la clave primaria `pk_block` sin traducirlo a una violación de negocio

### Requirement: Referencia al profesional en horarios y bloqueos
Guardar horarios o un bloqueo para un `professional_id` inexistente SHALL traducir la violación de clave foránea de la base a `Rejected` con `UNKNOWN_REFERENCE` y `ReferenceKind.PROFESSIONAL`. Un profesional existente con `active=False` SHALL poder guardar y conservar horarios de atención y bloqueos.

#### Scenario: Profesional inexistente al reemplazar horarios devuelve UNKNOWN_REFERENCE
- **WHEN** se intenta reemplazar los horarios del profesional inexistente `00000000-0000-0000-0000-000000000999` por el tramo del lunes (`weekday=1`, `540` a `780`)
- **THEN** la violación de la clave foránea `fk_working_hours_professional_id_professional` se traduce a `Rejected` con código `UNKNOWN_REFERENCE`, `reference_kind=ReferenceKind.PROFESSIONAL` y mensaje `"El profesional indicado no existe (id 00000000-0000-0000-0000-000000000999)."`

#### Scenario: Profesional inexistente al crear un bloqueo devuelve UNKNOWN_REFERENCE
- **WHEN** se intenta crear el bloqueo `00000000-0000-0000-0000-000000000b05` para el profesional inexistente `00000000-0000-0000-0000-000000000999`
- **THEN** la violación de la clave foránea `fk_block_professional_id_professional` se traduce a `Rejected` con código `UNKNOWN_REFERENCE`, `reference_kind=ReferenceKind.PROFESSIONAL` y mensaje `"El profesional indicado no existe (id 00000000-0000-0000-0000-000000000999)."`

#### Scenario: Profesional inactivo puede guardar horarios y bloqueos
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000003` persistido con `active=False`
- **WHEN** se guarda para ese profesional el tramo del viernes (`weekday=5`, `540` a `780`) y el bloqueo `00000000-0000-0000-0000-000000000b06` de `2026-11-13T12:00:00Z` a `2026-11-13T14:00:00Z`
- **THEN** ambas operaciones devuelven `Ok` y los registros quedan persistidos

### Requirement: Eliminación de bloqueos y liberación del horario
`BlockRepository.delete(id)` SHALL eliminar el bloqueo de la base y devolver el `Block` eliminado si existía, o `None` si no existía. Una vez eliminado, el bloqueo NO SHALL figurar en las lecturas del repositorio y el horario correspondiente SHALL quedar disponible.

#### Scenario: Borrar un bloqueo existente devuelve el bloqueo y libera el horario
- **GIVEN** el profesional `00000000-0000-0000-0000-000000000001` con horario el lunes (`weekday=1`, `540` a `780`) y el bloqueo `00000000-0000-0000-0000-000000000b07` de `2026-11-16T13:00:00Z` a `2026-11-16T14:00:00Z` (`10:00` a `11:00` hora local) que rechaza un turno en ese rango con `BLOCKED_TIME`
- **WHEN** se invoca `delete(UUID("00000000-0000-0000-0000-000000000b07"))` y se vuelve a validar el mismo turno con los bloqueos leídos del repositorio
- **THEN** `delete` devuelve el `Block` eliminado, `get_by_id` pasa a devolver `None` y el turno es aceptado con `Ok`

#### Scenario: Borrar un bloqueo inexistente devuelve None
- **WHEN** se invoca `delete(UUID("00000000-0000-0000-0000-000000000b99"))` para un id que no existe en `block`
- **THEN** el repositorio devuelve `None` sin lanzar excepción

### Requirement: Consulta de turnos afectados por un bloqueo mediante AppointmentReader
`BlockRepository.list_affected_appointments(block)` SHALL obtener los turnos del profesional en el rango del bloqueo a través del protocolo `AppointmentReader` inyectado y delegar el filtrado en `appointments_affected_by_block` del dominio, devolviendo los turnos afectados sin cancelarlos ni modificarlos.

#### Scenario: Listado de turnos afectados con lector fake sin modificar turnos
- **GIVEN** un `AppointmentReader` fake que provee para el profesional `00000000-0000-0000-0000-000000000001` un turno `reservado` (`00000000-0000-0000-0000-000000000a01`, `13:00` a `13:30` UTC), un turno `confirmado` (`00000000-0000-0000-0000-000000000a02`, `13:30` a `14:00` UTC) y un turno `cancelado` (`00000000-0000-0000-0000-000000000a03`, `13:00` a `13:30` UTC)
- **WHEN** se consulta `list_affected_appointments` para el bloqueo `00000000-0000-0000-0000-000000000b08` de `2026-11-16T13:00:00Z` a `2026-11-16T15:00:00Z`
- **THEN** devuelve exactamente la tupla ordenada con los turnos `00000000-0000-0000-0000-000000000a01` y `00000000-0000-0000-0000-000000000a02`, excluyendo el `cancelado`, y conserva intactos los estados e intervalos de todos los turnos

### Requirement: Seed idempotente de horarios de atención
El seed SHALL cargar 25 tramos ficticios de `WorkingHours` de lunes a viernes para los tres profesionales, sin sembrar bloqueos. Si un profesional ya tiene al menos un tramo, no SHALL insertar ni modificar nada para ese profesional; la segunda ejecución SHALL insertar 0 tramos.

#### Scenario: Primera y segunda ejecución idempotente del seed con horarios
- **WHEN** se ejecuta dos veces consecutivas `seed_database` sobre la base migrada
- **THEN** tras ambas ejecuciones existen `25` tramos en `working_hours` (`10` para `00000000-0000-0000-0000-000000000001`, `5` de `540` a `780` para `00000000-0000-0000-0000-000000000002` y `10` para `00000000-0000-0000-0000-000000000003`), `0` filas sembradas en `block`, y la segunda ejecución inserta `0` tramos sin modificar horarios existentes

### Requirement: Migración reversible de horarios y bloqueos
La migración `20261104_03_horarios_y_bloqueos` SHALL ser reversible y el autogenerate SHALL no reportar diferencias después de recrear las tablas.

#### Scenario: Ciclo upgrade y downgrade reversible de la migración
- **WHEN** se ejecuta `upgrade head`, después `downgrade -1` y después `upgrade head` sobre `<POSTGRES_DB>_test`
- **THEN** después del `downgrade -1` no existen `working_hours` ni `block`, siguen existiendo `professional`, `chair`, `service` y `patient`, y la base está en `20261103_02_catalogos_y_pacientes`; después del upgrade final, la base está en `20261104_03_horarios_y_bloqueos` y la comparación de metadata no reporta diferencias
