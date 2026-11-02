# Spec Delta

## Purpose

Dar de alta profesionales, sillones, prestaciones y pacientes con reglas puras, datos mínimos ficticios y errores explicativos, y activar o desactivar recursos sin alterar los turnos existentes.

## ADDED Requirements

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
