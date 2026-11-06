# catalog-and-patients Specification

## Purpose

Altas puras de profesionales, sillones, prestaciones y pacientes; nombres obligatorios; unicidad normalizada de sillones y prestaciones; DNI de 7 u 8 dígitos; activación inmutable e idempotente; sin datos clínicos. La API expone profesionales, sillones, prestaciones y pacientes con la matriz RBAC, edición con unicidad que excluye al propio registro, desactivación y reactivación por POST, 404 NOT_FOUND y búsqueda de pacientes por nombre (ILIKE, las tildes cuentan) y por prefijo de DNI.

## Requirements

### Requirement: Alta de profesionales
El dominio SHALL aceptar un profesional con nombre no vacío y devolver `Ok` con su id, nombre y estado. El nombre MUST conservarse tal como se cargó y MUST NOT ser único (US-021 CA-1). Los ids SHALL recibirse del llamador.

#### Scenario: Profesional válido
- **GIVEN** una candidata con id P1, nombre "Dra. Laura Quiroga" y activa
- **WHEN** se pide el alta del profesional
- **THEN** el resultado es `Ok` con P1, el mismo nombre y `active=True`

#### Scenario: Profesional con nombre repetido permitido
- **GIVEN** que existe P1, "Dra. Laura Quiroga", y una candidata P2 con ese mismo nombre
- **WHEN** se pide el alta de P2, activa
- **THEN** el resultado es `Ok`, sin `DUPLICATE_NAME`, con el id P2

#### Scenario: Nombre original de profesional conservado
- **GIVEN** una candidata P1 activa con nombre `"  Dra. Laura  Quiroga  "`
- **WHEN** se pide su alta
- **THEN** el profesional aceptado conserva exactamente `"  Dra. Laura  Quiroga  "`

### Requirement: Alta de sillones
El dominio SHALL aceptar un sillón con nombre no vacío y no duplicado, devolviendo `Ok` con su id, nombre original y estado (US-021). La colección de sillones existentes SHALL recibirse como contexto, sin I/O.

#### Scenario: Sillón válido
- **GIVEN** una candidata S1 con nombre "Sillón 1", activa, y ningún sillón existente
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` con S1, "Sillón 1" y `active=True`

#### Scenario: Sillón diferente permitido
- **GIVEN** que existe S1, "Sillón 1", y una candidata S2 activa llamada "Sillón 2"
- **WHEN** se pide el alta de S2 con la colección que contiene S1
- **THEN** el resultado es `Ok` con S2 y no se modifica S1 ni la colección

### Requirement: Alta de prestaciones
El dominio SHALL aceptar una prestación con nombre no vacío y único y duración válida, devolviendo `Ok` con id, nombre original, duración y estado (US-020). La colección existente SHALL recibirse por parámetro.

#### Scenario: Prestación válida
- **GIVEN** una candidata con id SV1, nombre "Limpieza", duración 45 minutos y activa, sin prestaciones existentes
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` con esos cuatro valores

#### Scenario: Prestación con estado activo por defecto
- **GIVEN** una candidata SV1, "Limpieza", de 45 minutos construida sin informar estado activo
- **WHEN** se pide su alta sin prestaciones existentes
- **THEN** el resultado es `Ok` con `active=True`

### Requirement: Alta de pacientes
El dominio SHALL aceptar un paciente con nombre no vacío y DNI válido y único y devolver `Ok` con su id, nombre original, DNI solo con dígitos y datos opcionales (US-022). Nombre de paciente MUST NOT ser único. La candidata y la colección existente MUST permanecer sin cambios.

#### Scenario: Paciente válido con DNI con puntos
- **GIVEN** una candidata PA1, "Ana Pérez", DNI "30.111.222", sin teléfono ni obra social y sin pacientes existentes
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` con id PA1, nombre "Ana Pérez", DNI "30111222" y ambos opcionales `None`
- **AND** la candidata sigue teniendo DNI "30.111.222"

#### Scenario: Paciente válido con DNI sin puntos
- **GIVEN** una candidata PA1, "Ana Pérez", DNI "30111222" y ningún paciente existente
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` y el DNI guardado es "30111222"

#### Scenario: Paciente con nombre repetido permitido
- **GIVEN** que existe PA1, "Ana Pérez", DNI "30111222", y una candidata PA2 con el mismo nombre y DNI "30111223"
- **WHEN** se pide el alta de PA2 con PA1 en la colección
- **THEN** el resultado es `Ok`, sin `DUPLICATE_NAME`

#### Scenario: Datos opcionales como texto libre
- **GIVEN** una candidata "Ana Pérez", DNI "30111222", con teléfono ficticio "interno ficticio" y obra social "plan de ejemplo"
- **WHEN** se pide su alta sin pacientes existentes
- **THEN** el resultado es `Ok` y conserva ambos textos sin validar su formato
- **AND** con los opcionales `""` también se acepta y conserva el texto vacío

### Requirement: Nombre obligatorio en todas las altas
Toda alta SHALL rechazar un nombre vacío o solo espacios con una sola `EMPTY_NAME` y el texto de su entidad. Si está vacío, MUST NOT evaluarse su duplicado; las otras reglas independientes SHALL seguir evaluándose (D5).

#### Scenario: Nombre vacío de profesional
- **GIVEN** una candidata a profesional con nombre `""`
- **WHEN** se pide su alta
- **THEN** hay una `EMPTY_NAME` con "El nombre del profesional no puede estar vacío."

#### Scenario: Nombre vacío de sillón
- **GIVEN** una candidata a sillón con nombre `""` y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `EMPTY_NAME` con "El nombre del sillón no puede estar vacío."

#### Scenario: Nombre vacío de prestación
- **GIVEN** una candidata a prestación con nombre `""`, duración 45 y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `EMPTY_NAME` con "El nombre de la prestación no puede estar vacío."

#### Scenario: Nombre vacío de paciente
- **GIVEN** una candidata a paciente con nombre `""`, DNI "30111222" y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `EMPTY_NAME` con "El nombre del paciente no puede estar vacío."

#### Scenario: Nombre solo de espacios en las cuatro entidades
- **GIVEN** las candidatas de los cuatro escenarios anteriores con nombre `"   "` en lugar de `""`
- **WHEN** se pide cada alta por separado
- **THEN** cada resultado es `Rejected` con una sola `EMPTY_NAME` y exactamente el mensaje de su entidad anterior

#### Scenario: Nombre vacío no produce duplicado
- **GIVEN** una candidata a sillón con nombre `""` o `"   "` y otro sillón cuyo nombre es `"   "`
- **WHEN** se pide el alta contra esa colección
- **THEN** el resultado contiene solo `EMPTY_NAME`, nunca `DUPLICATE_NAME`
- **AND** se cumple lo mismo para una prestación de duración 45 con nombre vacío o blanco frente a otra de nombre blanco

### Requirement: Unicidad normalizada de sillones y prestaciones
Los nombres de sillón y prestación SHALL compararse recortando bordes, colapsando espacios internos y aplicando `casefold`, con tildes significativas (SU-12). Un duplicado SHALL producir una sola `DUPLICATE_NAME`; su mensaje muestra el nombre recibido recortado y con espacios internos colapsados a uno, conservando mayúsculas y tildes. Todos los existentes recibidos participan, también inactivos.

#### Scenario: Nombre de sillón duplicado exacto
- **GIVEN** S1 "Sillón 1" y una candidata S2 con ese mismo nombre
- **WHEN** se pide su alta con S1 en la colección
- **THEN** el resultado es `Rejected` con `DUPLICATE_NAME` y mensaje `Ya existe un sillón con el nombre "Sillón 1".`

#### Scenario: Nombre de prestación duplicado exacto
- **GIVEN** SV1 "Limpieza" y una candidata SV2 "Limpieza" de 45 minutos
- **WHEN** se pide su alta con SV1 en la colección
- **THEN** el resultado es `Rejected` con `DUPLICATE_NAME` y mensaje `Ya existe una prestación con el nombre "Limpieza".`

#### Scenario: Sillón duplicado con mayúsculas y espacios
- **GIVEN** S1 con nombre "Sillón 1" y una candidata S2 llamada `"  SILLÓN   1  "`
- **WHEN** se pide su alta con S1 en la colección
- **THEN** hay una `DUPLICATE_NAME` con mensaje exacto `Ya existe un sillón con el nombre "SILLÓN 1".`

#### Scenario: Prestación duplicada con mayúsculas y espacios
- **GIVEN** SV1 con nombre `"  LIMPIEZA  "` y una candidata SV2 llamada `"  Limpieza  "`, de 45 minutos
- **WHEN** se pide su alta con SV1 en la colección
- **THEN** hay una `DUPLICATE_NAME` con mensaje exacto `Ya existe una prestación con el nombre "Limpieza".`
- **AND** para existente "Control de ortodoncia" y candidata `" CONTROL   DE  ORTODONCIA "`, hay una `DUPLICATE_NAME` con mensaje exacto `Ya existe una prestación con el nombre "CONTROL DE ORTODONCIA".`

#### Scenario: Las tildes distinguen prestaciones
- **GIVEN** que existe una prestación "Extracción" y una candidata "Extraccion" de 60 minutos
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok`, porque no son nombres equivalentes

#### Scenario: Las tildes distinguen sillones
- **GIVEN** S1 llamado "Sillón 1" y una candidata S2 "Sillon 1"
- **WHEN** se pide su alta con S1 en la colección
- **THEN** el resultado es `Ok`

#### Scenario: Un existente inactivo conserva su nombre único
- **GIVEN** S1 "Sillón 1" inactivo y una candidata S2 con ese nombre
- **WHEN** se pide su alta
- **THEN** el resultado es `Rejected` con una `DUPLICATE_NAME`
- **AND** una prestación "Limpieza" inactiva también impide otra de nombre equivalente

#### Scenario: Varios existentes equivalentes producen una violación
- **GIVEN** dos sillones existentes con nombres equivalentes a "Sillón 1", recibidos en cualquier orden
- **WHEN** se pide el alta de otro sillón "Sillón 1"
- **THEN** hay exactamente una `DUPLICATE_NAME`, no una por cada existente
- **AND** lo mismo se cumple con dos prestaciones equivalentes a "Limpieza" y una candidata de 45 minutos

### Requirement: Validez y normalización del DNI
El DNI SHALL normalizarse quitando puntos y espacios y MUST tener 7 u 8 dígitos. Un DNI inválido SHALL producir `INVALID_DNI`, mostrando el texto recibido: `El DNI no es válido (se recibió "{dni}"): debe tener 7 u 8 dígitos, con o sin puntos.` Un DNI inválido MUST NOT evaluarse por duplicados. El aceptado SHALL guardarse solo con dígitos (SU-12).

#### Scenario: DNI de siete dígitos válido
- **GIVEN** una candidata "Ana Pérez" con DNI "3.111.222" y colección vacía
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` y el DNI es "3111222"

#### Scenario: DNI con puntos y espacios válido
- **GIVEN** una candidata "Ana Pérez" con DNI `" 30.111.222 "` y colección vacía
- **WHEN** se pide su alta
- **THEN** el resultado es `Ok` y el DNI es "30111222"
- **AND** para `"30 111 222"` se obtiene el mismo DNI

#### Scenario: DNI con guiones inválido
- **GIVEN** una candidata "Ana Pérez" con DNI "30-111-222" y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `INVALID_DNI` con mensaje exacto `El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.`

#### Scenario: DNI de seis dígitos inválido
- **GIVEN** una candidata "Ana Pérez" con DNI "111222" y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `INVALID_DNI` con mensaje exacto `El DNI no es válido (se recibió "111222"): debe tener 7 u 8 dígitos, con o sin puntos.`

#### Scenario: DNI de nueve dígitos inválido
- **GIVEN** una candidata "Ana Pérez" con DNI "301112222" y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `INVALID_DNI` con mensaje exacto `El DNI no es válido (se recibió "301112222"): debe tener 7 u 8 dígitos, con o sin puntos.`

#### Scenario: DNI con letras inválido
- **GIVEN** una candidata "Ana Pérez" con DNI "30111A22" y colección vacía
- **WHEN** se pide su alta
- **THEN** hay una `INVALID_DNI` con mensaje exacto `El DNI no es válido (se recibió "30111A22"): debe tener 7 u 8 dígitos, con o sin puntos.`

#### Scenario: DNI vacío o blanco inválido
- **GIVEN** una candidata "Ana Pérez" con DNI `""` o `"   "` y colección vacía
- **WHEN** se pide su alta
- **THEN** en cada caso hay una sola `INVALID_DNI`, cuyo mensaje conserva entre comillas el texto recibido

#### Scenario: DNI inválido no produce duplicado
- **GIVEN** una candidata "Ana Pérez" con DNI "30-111-222" y un paciente existente con ese mismo texto inválido
- **WHEN** se pide su alta
- **THEN** hay solo `INVALID_DNI`, sin `DUPLICATE_DNI` ni excepción

### Requirement: Unicidad de DNI por sus dígitos
El dominio SHALL comparar DNI válidos por sus dígitos normalizados contra la colección de pacientes recibida. Un duplicado SHALL producir una sola `DUPLICATE_DNI` con `Ya existe un paciente con el DNI {dni con puntos de miles}.`, sin alterar la colección.

#### Scenario: DNI duplicado sin puntos
- **GIVEN** PA1 "Ana Pérez" con DNI "30111222" y una candidata PA2 con el mismo DNI
- **WHEN** se pide su alta
- **THEN** hay una `DUPLICATE_DNI` con mensaje exacto "Ya existe un paciente con el DNI 30.111.222."

#### Scenario: DNI con y sin puntos son iguales
- **GIVEN** PA1 con DNI "30111222" y candidata PA2 con DNI "30.111.222"
- **WHEN** se pide el alta de PA2 con PA1 en la colección
- **THEN** hay una `DUPLICATE_DNI` con el mensaje "Ya existe un paciente con el DNI 30.111.222."
- **AND** se obtiene el mismo rechazo si el existente tiene "30.111.222" y la candidata "30111222"

#### Scenario: DNI duplicado de siete dígitos
- **GIVEN** PA1 con DNI "3111222" y candidata PA2 con DNI "3.111.222"
- **WHEN** se pide su alta
- **THEN** hay una `DUPLICATE_DNI` con mensaje exacto "Ya existe un paciente con el DNI 3.111.222."

#### Scenario: Pacientes recibidos en otro orden
- **GIVEN** una colección con pacientes de DNI "30111223" y "30111222"
- **WHEN** se pide el alta de "Ana Pérez" con DNI "30.111.222", con la colección directa o invertida
- **THEN** ambos resultados contienen exactamente una `DUPLICATE_DNI` con el mismo mensaje y la colección no cambia

### Requirement: Duración de la prestación con la regla vigente
El alta de prestación SHALL usar la misma regla de duración de agenda: entero positivo, múltiplo de 5 y máximo 480. SHALL reutilizar `check_duration` e `INVALID_DURATION`, pasando el sujeto «de la prestación» y conservando las razones y su orden (RN-AG-09). El parámetro de sujeto SHALL tener el valor predeterminado «del turno», de modo que los mensajes existentes de C-03 permanecen idénticos. Una duración que rompe varias condiciones SHALL generar una sola violación con todas sus razones.

#### Scenario: Duraciones límite válidas
- **GIVEN** candidatas "Limpieza" con duración 5 y 480 minutos, sin existentes, en dos altas independientes
- **WHEN** se pide cada alta
- **THEN** ambos resultados son `Ok` con su duración exacta

#### Scenario: Duración cero o negativa
- **GIVEN** una candidata "Limpieza" sin existentes y duración 0 o -5 minutos
- **WHEN** se pide el alta
- **THEN** hay una `INVALID_DURATION` cuyo mensaje es exactamente "La duración de la prestación no es válida (se recibió 0 minutos): debe ser mayor que cero minutos." o "La duración de la prestación no es válida (se recibió -5 minutos): debe ser mayor que cero minutos.", respectivamente

#### Scenario: Duración fuera de la grilla
- **GIVEN** una candidata "Limpieza" de 7 minutos, sin existentes
- **WHEN** se pide el alta
- **THEN** hay una `INVALID_DURATION` con "La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos."

#### Scenario: Duración mayor que el máximo
- **GIVEN** una candidata "Limpieza" de 485 minutos, sin existentes
- **WHEN** se pide el alta
- **THEN** hay una `INVALID_DURATION` con "La duración de la prestación no es válida (se recibió 485 minutos): no puede superar los 480 minutos."

#### Scenario: Duración con dos razones
- **GIVEN** una candidata "Limpieza" de 487 minutos, sin existentes
- **WHEN** se pide el alta
- **THEN** hay exactamente una `INVALID_DURATION` con "La duración de la prestación no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos."

### Requirement: Violaciones de alta completas y ordenadas
Las altas SHALL devolver `Rejected` con todas las violaciones aplicables sin cortar: `EMPTY_NAME`, `INVALID_DNI`, `DUPLICATE_NAME` o `DUPLICATE_DNI`, y finalmente `INVALID_DURATION`. Las guardas del duplicado no impiden validar otros campos. Las violaciones nuevas MUST tener mensaje y MUST NOT llevar tipo de referencia, ids ni intervalo de agenda en conflicto.

#### Scenario: Nombre y DNI inválidos juntos
- **GIVEN** una candidata paciente con nombre `""` y DNI "30-111-222"
- **WHEN** se pide el alta sin pacientes existentes
- **THEN** hay exactamente dos violaciones, `EMPTY_NAME` y `INVALID_DNI`, en ese orden y con los mensajes exactos ya definidos

#### Scenario: Nombre vacío y DNI duplicado
- **GIVEN** PA1 con DNI "30111222" y una candidata paciente con nombre `"   "` y DNI "30.111.222"
- **WHEN** se pide el alta contra PA1
- **THEN** hay exactamente `EMPTY_NAME` y `DUPLICATE_DNI`, en ese orden

#### Scenario: Prestación duplicada y duración inválida
- **GIVEN** que existe "Limpieza" y una candidata del mismo nombre con duración 487
- **WHEN** se pide el alta
- **THEN** hay exactamente `DUPLICATE_NAME` e `INVALID_DURATION`, en ese orden, con sus mensajes exactos

#### Scenario: Nombre vacío no oculta duración inválida
- **GIVEN** una prestación candidata de nombre `""`, duración 0 y otra prestación de nombre vacío
- **WHEN** se pide el alta
- **THEN** hay exactamente `EMPTY_NAME` e `INVALID_DURATION`, en ese orden, sin `DUPLICATE_NAME`

#### Scenario: Metadatos de las violaciones nuevas
- **GIVEN** altas que producen por separado `EMPTY_NAME`, `DUPLICATE_NAME`, `INVALID_DNI` y `DUPLICATE_DNI`
- **WHEN** se inspecciona cada rechazo
- **THEN** cada violación tiene el código y mensaje definidos y sus campos de referencia, ids e intervalo en conflicto son `None`

### Requirement: Activación inmutable e idempotente de recursos
El dominio SHALL desactivar y reactivar profesionales, sillones y prestaciones devolviendo una copia con `active=False` o `True` y conservando el resto de campos. La operación repetida SHALL conservar los valores sin violación ni códigos `ALREADY_INACTIVE`/`ALREADY_ACTIVE`. El objeto original MUST permanecer sin cambios.

#### Scenario: Desactivar cada recurso activo
- **GIVEN** P1 "Dra. Laura Quiroga", S1 "Sillón 1" y SV1 "Limpieza" de 45 minutos, activos
- **WHEN** se desactiva cada recurso por separado
- **THEN** se devuelve una copia del mismo tipo con `active=False`, mismo id y demás campos; los originales siguen activos

#### Scenario: Reactivar cada recurso inactivo
- **GIVEN** P1, S1 y SV1 del escenario anterior, inactivos
- **WHEN** se reactiva cada uno
- **THEN** se devuelve una copia del mismo tipo con `active=True`, conservando campos; los originales siguen inactivos

#### Scenario: Desactivar un recurso ya inactivo
- **GIVEN** P1, S1 y SV1 inactivos
- **WHEN** se desactiva cada uno otra vez
- **THEN** los valores de cada resultado son iguales a los de entrada y no hay violación

#### Scenario: Reactivar un recurso ya activo
- **GIVEN** P1, S1 y SV1 activos
- **WHEN** se reactiva cada uno otra vez
- **THEN** los valores de cada resultado son iguales a los de entrada y no hay violación

### Requirement: Compatibilidad con la agenda al desactivar
Desactivar un recurso MUST NOT cancelar, mover ni alterar turnos existentes. Un nuevo turno con profesional, sillón o prestación desactivados SHALL conservar el rechazo vigente `INACTIVE_REFERENCE`, sin cambiar sus textos ni el contrato `Ok` de agenda (US-020 CA-3, US-021 CA-2).

#### Scenario: Desactivar no modifica turnos existentes
- **GIVEN** P1, S1 y SV1 activos y un turno reservado de P1 en S1 con SV1 del 2026-10-20 de 13:00 a 13:30 UTC
- **WHEN** se desactiva cada recurso por separado
- **THEN** el turno conserva id, paciente, profesional, sillón, prestación, inicio, fin y estado reservado

#### Scenario: Turno nuevo con profesional desactivado
- **GIVEN** P1 "Dra. Laura Quiroga" desactivado mediante la operación de catálogo, paciente existente, S1 y SV1 activos, horario completo, sin bloqueos ni turnos, `now=2026-10-01T00:00:00+00:00`
- **WHEN** se pide un turno para P1 a las 13:00 UTC del 2026-10-20, de 30 minutos
- **THEN** hay solo `INACTIVE_REFERENCE`, tipo `PROFESSIONAL`, con "El profesional indicado está inactivo (id {id de P1}).", sin nombres ni conflictos

#### Scenario: Turno nuevo con sillón o prestación desactivados
- **GIVEN** el contexto válido anterior y S1 desactivado en el primer caso o SV1 desactivada en el segundo, con las demás referencias activas
- **WHEN** se pide el mismo turno nuevo
- **THEN** hay solo `INACTIVE_REFERENCE`, tipo `CHAIR` o `SERVICE` y mensaje "El sillón indicado está inactivo (id {id de S1})." o "La prestación indicada está inactiva (id {id de SV1}).", respectivamente

#### Scenario: Turno nuevo después de reactivar
- **GIVEN** P1 previamente desactivado y luego reactivado, y el contexto válido sin conflictos anterior
- **WHEN** se pide el mismo turno nuevo
- **THEN** el resultado de agenda es `Ok` con su turno en el payload vigente, estado reservado y fin 13:30 UTC

### Requirement: Datos mínimos y construcción del modelo
La prestación SHALL exponer id, nombre, duración y activo por defecto verdadero. El paciente SHALL tener exactamente id, nombre completo, DNI, teléfono y obra social opcionales, sin campos clínicos ni estado activo (RN-PA-01). La construcción MUST NOT validar reglas de negocio; estas pertenecen al alta. Profesional no incorpora matrícula en C-09.

#### Scenario: Campos exactos del paciente
- **GIVEN** la entidad Patient del dominio
- **WHEN** se enumeran sus campos de datos
- **THEN** son exactamente `id`, `full_name`, `dni`, `phone`, `health_insurance`, en ese orden

#### Scenario: Opcionales de paciente ausentes
- **GIVEN** una construcción Patient con id PA1, "Ana Pérez" y DNI "30111222"
- **WHEN** no se informan teléfono ni obra social
- **THEN** ambos son `None`

#### Scenario: Construcción no rechaza datos de negocio inválidos
- **GIVEN** los datos nombre vacío y duración 0 para una prestación, y nombre vacío y DNI "30-111-222" para un paciente
- **WHEN** se construyen las entidades
- **THEN** no hay excepción y conservan sus valores; el alta es la que devuelve las violaciones

#### Scenario: Profesional sin matrícula en el dominio
- **GIVEN** Professional del dominio
- **WHEN** se enumeran sus campos
- **THEN** son exactamente `id`, `full_name`, `active`, sin `license_number`

### Requirement: Ejemplos ficticios reutilizables y aislados
El proyecto SHALL ofrecer datos ficticios reutilizables fuera del dominio para tests y futuro seed, sin contraseñas ni datos clínicos/reales (RN-PA-02). El dominio MUST NOT importarlos ni depender de otras capas. Los datos SHALL ser deterministas y válidos por las altas públicas; no se incluye script de seed ni I/O.

#### Scenario: Catálogo y paciente ficticios disponibles
- **GIVEN** el módulo de ejemplos de la aplicación, fuera del dominio
- **WHEN** se consultan sus colecciones
- **THEN** incluyen "Dra. Laura Quiroga", "Sillón 1", "Limpieza" de 45 minutos y "Ana Pérez" con DNI "30111222", declarados ficticios, con ids literales y sin secretos

#### Scenario: Ejemplos válidos por las altas
- **GIVEN** las entidades ficticias anteriores
- **WHEN** se valida cada alta contra una colección vacía de su tipo
- **THEN** todas son aceptadas sin escribir datos ni modificar las colecciones de ejemplos

#### Scenario: El dominio no importa demo_data
- **GIVEN** todos los módulos reales del dominio, incluidos sus subpaquetes de catálogo y reglas
- **WHEN** se ejecuta la guardia de imports estáticos
- **THEN** no hay imports de `app.demo_data` ni dependencias fuera de la lista permitida
- **AND** una mutación temporal de import estático de `app.demo_data` sería detectada por la guardia y se restaura después de comprobarla

#### Scenario: Dominio sin reloj global ni generación de identificadores
- **GIVEN** las altas y operaciones de catálogo del dominio
- **WHEN** se usan los ids de los ejemplos y se ejecutan las guardias vigentes sobre el dominio real
- **THEN** los resultados usan los ids recibidos y la guardia del reloj no reporta accesos; la revisión no encuentra llamadas a generación de UUID ni I/O

### Requirement: Endpoints de profesionales
La API SHALL exponer endpoints bajo /api/professionals para consultar y administrar profesionales. GET /api/professionals lista los profesionales y admite el filtro opcional active. GET /api/professionals/{id} devuelve el detalle de un profesional. POST /api/professionals crea un profesional. PUT /api/professionals/{id} actualiza sus datos. Los esquemas admiten el campo opcional licenseNumber.

#### Scenario: Alta exitosa de profesional con matrícula responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con fullName "Dra. Laura Quiroga" y licenseNumber "MN-12345"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "Dra. Laura Quiroga", licenseNumber "MN-12345" y active verdadero

#### Scenario: Edición exitosa de profesional responde 200
- **GIVEN** un profesional existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dra. Laura Quiroga Modificada" y licenseNumber "MN-99999"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo fullName y licenseNumber conservando el mismo id

#### Scenario: Edición de profesional conservando su propio nombre responde 200
- **GIVEN** un profesional existente con fullName "Dra. Laura Quiroga" y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dra. Laura Quiroga" y licenseNumber "MN-88888"
- **THEN** el status es 200
- **AND** el cuerpo conserva fullName "Dra. Laura Quiroga" con licenseNumber "MN-88888"

#### Scenario: Edición de profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dr. Inexistente"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Listado de profesionales con filtro active verdadero
- **GIVEN** profesionales activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/professionals con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de profesionales sin filtro incluye inactivos en orden alfabético
- **GIVEN** profesionales activos e inactivos persistidos y un usuario autenticado
- **WHEN** invoca GET /api/professionals sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye profesionales inactivos ordenados por nombre ascendente

#### Scenario: Recepción lista profesionales y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 200
- **AND** recibe la lista de profesionales

#### Scenario: El odontólogo lista profesionales y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 200
- **AND** recibe la lista de profesionales

#### Scenario: Detalle de profesional existente responde 200
- **GIVEN** un profesional existente con id P1 y un usuario autenticado
- **WHEN** invoca GET /api/professionals/P1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de P1

#### Scenario: Detalle de profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario autenticado
- **WHEN** invoca GET /api/professionals/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Consulta de profesionales sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de profesional rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de profesional rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de profesional rechazada para rol recepción con 403
- **GIVEN** un profesional existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/professionals/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de profesional rechazada para rol odontólogo con 403
- **GIVEN** un profesional existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/professionals/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de profesional con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con fullName vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de profesional con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con un JSON sin el campo obligatorio fullName
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de sillones
La API SHALL exponer endpoints bajo /api/chairs para consultar y administrar sillones odontológicos. GET /api/chairs lista los sillones y admite el filtro opcional active. GET /api/chairs/{id} devuelve el detalle de un sillón. POST /api/chairs crea un sillón. PUT /api/chairs/{id} actualiza el nombre del sillón. El nombre del sillón debe ser único en el sistema.

#### Scenario: Alta exitosa de sillón responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name "Sillón Azul"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, name "Sillón Azul" y active verdadero

#### Scenario: Edición exitosa de sillón responde 200
- **GIVEN** un sillón existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón Verde"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo name conservando el mismo id

#### Scenario: Edición de sillón conservando su propio nombre responde 200
- **GIVEN** un sillón existente con name "Sillón 1" y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón 1"
- **THEN** el status es 200
- **AND** el cuerpo conserva name "Sillón 1" sin emitir violación de duplicado

#### Scenario: Edición de sillón con el nombre de otro sillón responde 409
- **GIVEN** un sillón existente S1 llamado "Sillón 1", otro sillón S2 llamado "Sillón 2", y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/S2 con name "Sillón 1"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Edición de sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón Fantasma"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Listado de sillones con filtro active verdadero
- **GIVEN** sillones activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/chairs con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de sillones con filtro active falso devuelve solo inactivos
- **GIVEN** sillones activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/chairs con active=false
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active falso

#### Scenario: Listado de sillones sin filtro incluye inactivos en orden alfabético
- **GIVEN** sillones activos e inactivos persistidos y un usuario autenticado
- **WHEN** invoca GET /api/chairs sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye sillones inactivos ordenados por nombre ascendente

#### Scenario: Recepción lista sillones y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 200
- **AND** recibe la lista de sillones

#### Scenario: El odontólogo lista sillones y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 200
- **AND** recibe la lista de sillones

#### Scenario: Detalle de sillón existente responde 200
- **GIVEN** un sillón existente con id S1 y un usuario autenticado
- **WHEN** invoca GET /api/chairs/S1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de S1

#### Scenario: Detalle de sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario autenticado
- **WHEN** invoca GET /api/chairs/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Consulta de sillones sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de sillón rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de sillón rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de sillón rechazada para rol recepción con 403
- **GIVEN** un sillón existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/chairs/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de sillón rechazada para rol odontólogo con 403
- **GIVEN** un sillón existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/chairs/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de sillón con nombre duplicado responde 409
- **GIVEN** un sillón existente llamado "Sillón 1" y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name "Sillón 1"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Alta de sillón con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de sillón con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con un JSON sin el campo obligatorio name
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de prestaciones
La API SHALL exponer endpoints bajo /api/services para consultar y administrar prestaciones. GET /api/services lista las prestaciones y admite el filtro opcional active. GET /api/services/{id} devuelve el detalle de una prestación. POST /api/services crea una prestación con nombre y duración en minutos. PUT /api/services/{id} actualiza sus datos. El nombre debe ser único y la duración múltiplo de 5 entre 5 y 480 minutos.

#### Scenario: Alta exitosa de prestación responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Consulta General" y defaultDurationMin 30
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, name "Consulta General", defaultDurationMin 30 y active verdadero

#### Scenario: Edición exitosa de prestación responde 200
- **GIVEN** una prestación existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Consulta Prolongada" y defaultDurationMin 45
- **THEN** el status es 200
- **AND** el cuerpo refleja los nuevos valores conservando el mismo id

#### Scenario: Edición de prestación conservando su propio nombre responde 200
- **GIVEN** una prestación existente con name "Limpieza" y duración 45, y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Limpieza" y defaultDurationMin 60
- **THEN** el status es 200
- **AND** el cuerpo refleja defaultDurationMin 60 conservando name "Limpieza" sin error de duplicado

#### Scenario: Edición de prestación con el nombre de otra prestación responde 409
- **GIVEN** una prestación existente SV1 llamada "Limpieza", otra prestación SV2 llamada "Control", y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/SV2 con name "Limpieza" y defaultDurationMin 30
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Edición de prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Prestación Fantasma" y defaultDurationMin 30
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Listado de prestaciones con filtro active verdadero
- **GIVEN** prestaciones activas e inactivas y un usuario autenticado
- **WHEN** invoca GET /api/services con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de prestaciones sin filtro incluye inactivos en orden alfabético
- **GIVEN** prestaciones activas e inactivas persistidas y un usuario autenticado
- **WHEN** invoca GET /api/services sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye prestaciones inactivas ordenadas por nombre ascendente

#### Scenario: Recepción lista prestaciones y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/services
- **THEN** el status es 200
- **AND** recibe la lista de prestaciones

#### Scenario: El odontólogo lista prestaciones y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/services
- **THEN** el status es 200
- **AND** recibe la lista de prestaciones

#### Scenario: Detalle de prestación existente responde 200
- **GIVEN** una prestación existente con id SV1 y un usuario autenticado
- **WHEN** invoca GET /api/services/SV1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de SV1

#### Scenario: Detalle de prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario autenticado
- **WHEN** invoca GET /api/services/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Consulta de prestaciones sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/services
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de prestación rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de prestación rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de prestación rechazada para rol recepción con 403
- **GIVEN** una prestación existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/services/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/services/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de prestación con nombre duplicado responde 409
- **GIVEN** una prestación existente llamada "Limpieza" y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Limpieza" y defaultDurationMin 30
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Alta de prestación con duración inválida responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Extracción" y defaultDurationMin 7
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación INVALID_DURATION

#### Scenario: Alta de prestación con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name vacío y defaultDurationMin 30
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de prestación con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con un JSON sin el campo obligatorio defaultDurationMin
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de pacientes
La API SHALL exponer endpoints bajo /api/patients para consultar y administrar pacientes. GET /api/patients lista los pacientes y admite el parámetro de búsqueda textual query. GET /api/patients/{id} devuelve el detalle de un paciente. POST /api/patients crea un paciente. PUT /api/patients/{id} actualiza sus datos. Los pacientes no poseen rutas de desactivación ni borrado.

#### Scenario: Alta exitosa de paciente por recepción responde 201
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con fullName "Carlos Gómez", dni "32.111.222", phone "11-4444-5555" y healthInsurance "OSDE"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "Carlos Gómez", dni normalizado "32111222", phone "11-4444-5555" y healthInsurance "OSDE"

#### Scenario: Alta exitosa de paciente por administrador responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/patients con fullName "María López", dni "33.222.333", phone "11-6666-7777" y healthInsurance "Swiss Medical"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "María López" y dni normalizado "33222333"

#### Scenario: Edición exitosa de paciente responde 200
- **GIVEN** un paciente existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Carlos Gómez Editado", dni "32.111.222", phone "11-9999-8888" y healthInsurance "Particular"
- **THEN** el status es 200
- **AND** el cuerpo refleja los nuevos datos conservando el mismo id

#### Scenario: Edición de paciente conservando su propio DNI responde 200
- **GIVEN** un paciente existente con DNI "30111222" y teléfono anterior, y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Ana Pérez" y dni "30.111.222" y nuevo teléfono "11-1234-5678"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo teléfono conservando DNI "30111222" sin error de duplicado

#### Scenario: Edición de paciente con el DNI de otro paciente responde 409
- **GIVEN** un paciente PA1 con DNI "30111222", otro paciente PA2 con DNI "28444555", y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/PA2 con fullName "Bruno Acosta" y dni "30.111.222"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_DNI

#### Scenario: Edición de paciente inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún paciente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Paciente Fantasma" y dni "30111222"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Paciente no encontrado."

#### Scenario: Búsqueda de pacientes por parte del nombre
- **GIVEN** el paciente ficticio "Ana Pérez" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "pérez"
- **THEN** el status es 200
- **AND** la lista devuelta incluye a "Ana Pérez"

#### Scenario: Búsqueda de pacientes sin tilde no encuentra el nombre con tilde
- **GIVEN** el paciente ficticio "Ana Pérez" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "perez"
- **THEN** el status es 200
- **AND** la lista devuelta no incluye a "Ana Pérez"

#### Scenario: Búsqueda de pacientes por inicio del DNI
- **GIVEN** el paciente ficticio "Ana Pérez" con DNI "30111222" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "3011"
- **THEN** el status es 200
- **AND** la lista devuelta incluye a "Ana Pérez"

#### Scenario: El odontólogo lista pacientes y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/patients
- **THEN** el status es 200
- **AND** recibe la lista de pacientes

#### Scenario: Detalle de paciente existente responde 200
- **GIVEN** un paciente existente con id PA1 y un usuario autenticado
- **WHEN** invoca GET /api/patients/PA1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de PA1

#### Scenario: Detalle de paciente inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún paciente y un usuario autenticado
- **WHEN** invoca GET /api/patients/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Paciente no encontrado."

#### Scenario: Consulta de pacientes sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/patients
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de paciente rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/patients con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de paciente rechazada para rol odontólogo con 403
- **GIVEN** un paciente existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/patients/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de paciente con DNI duplicado responde 409
- **GIVEN** un paciente existente con DNI "30111222" y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "30.111.222" y fullName "Otro Paciente"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_DNI

#### Scenario: Alta de paciente con DNI de formato inválido responde 422
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "12345" y fullName "Paciente Inválido"
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación INVALID_DNI

#### Scenario: Alta de paciente con nombre vacío responde 422
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "30111222" y fullName vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de paciente con cuerpo malformado responde 400
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con un JSON sin el campo obligatorio dni
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

#### Scenario: Desactivación de paciente no existe en la API
- **GIVEN** un paciente existente y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/patients/{id}/deactivate
- **THEN** el status es 404

#### Scenario: Borrado de paciente no existe en la API
- **GIVEN** un paciente existente y un usuario con rol administrador autenticado
- **WHEN** invoca DELETE /api/patients/{id}
- **THEN** el status es 405

### Requirement: Desactivación y reactivación en la API
La API SHALL exponer rutas POST /api/{recurso}/{id}/deactivate y POST /api/{recurso}/{id}/reactivate para profesionales, sillones y prestaciones. La desactivación SHALL autorizarse bajo la acción DELETE y la reactivación bajo la acción UPDATE en RBAC. Ambas responden 200 con la entidad actualizada y son idempotentes.

#### Scenario: Desactivar profesional activo responde 200
- **GIVEN** un profesional activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar profesional inactivo responde 200
- **GIVEN** un profesional inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar profesional ya inactivo responde 200 sin cambios
- **GIVEN** un profesional inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar profesional ya activo responde 200 sin cambios
- **GIVEN** un profesional activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Reactivar profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Desactivar profesional rechazado para rol recepción con 403
- **GIVEN** un profesional existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar profesional rechazado para rol odontólogo con 403
- **GIVEN** un profesional existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar profesional rechazado para rol recepción con 403
- **GIVEN** un profesional inactivo y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar profesional rechazado para rol odontólogo con 403
- **GIVEN** un profesional inactivo y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar sillón activo responde 200
- **GIVEN** un sillón activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar sillón inactivo responde 200
- **GIVEN** un sillón inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar sillón ya inactivo responde 200 sin cambios
- **GIVEN** un sillón inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar sillón ya activo responde 200 sin cambios
- **GIVEN** un sillón activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Reactivar sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Desactivar sillón rechazado para rol recepción con 403
- **GIVEN** un sillón existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar sillón rechazado para rol odontólogo con 403
- **GIVEN** un sillón existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar sillón rechazado para rol recepción con 403
- **GIVEN** un sillón inactivo y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar sillón rechazado para rol odontólogo con 403
- **GIVEN** un sillón inactivo y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar prestación activa responde 200
- **GIVEN** una prestación activa y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar prestación inactiva responde 200
- **GIVEN** una prestación inactiva y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar prestación ya inactiva responde 200 sin cambios
- **GIVEN** una prestación inactiva y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar prestación ya activa responde 200 sin cambios
- **GIVEN** una prestación activa y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Reactivar prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Desactivar prestación rechazada para rol recepción con 403
- **GIVEN** una prestación existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar prestación rechazada para rol recepción con 403
- **GIVEN** una prestación inactiva y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación inactiva y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"
