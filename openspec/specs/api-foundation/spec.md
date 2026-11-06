# api-foundation Specification

## Purpose

Base HTTP de la API REST: una factory `create_app` arma la aplicación con todas
las rutas bajo el prefijo `/api`. `GET /api/health` comprueba la base con una
consulta real y responde `200` o `503`. Una tabla total, sin valor por defecto,
asigna a cada `ViolationCode` el status `409`, `422` o `403`; con códigos
mixtos rige la precedencia `403`, luego `422`, luego `409`. Los rechazos del
dominio responden con el cuerpo `{ "violations": [...] }` en camelCase y la
entrada malformada responde `400`, sin devolver los valores enviados. CORS queda
limitado al origen de `CORS_ORIGIN`. Cada request recibe su propia sesión de
base, sin `commit` implícito. Swagger se sirve en `/api/docs`.

## Requirements

### Requirement: Salud del servicio con chequeo de la base

`GET /api/health` SHALL comprobar la base con una consulta real. SHALL responder `200` con `{ "status": "ok", "database": "ok" }` si la base responde, y `503` con `{ "status": "unavailable", "database": "unavailable" }` si no responde, sin exponer el texto del error.

#### Scenario: Health 200 con la base disponible

- **GIVEN** una app configurada contra la base de test en PostgreSQL
- **WHEN** se invoca `GET /api/health`
- **THEN** el status es `200`
- **AND** el cuerpo es `{ "status": "ok", "database": "ok" }`

#### Scenario: Health 503 con la base caída

- **GIVEN** una app configurada contra un puerto local realmente cerrado
- **WHEN** se invoca `GET /api/health`
- **THEN** el status es `503`
- **AND** el cuerpo es `{ "status": "unavailable", "database": "unavailable" }`

### Requirement: Entrada malformada responde 400

Una entrada que no cumple el esquema de la ruta SHALL responder `400` con `{ "errors": [{ "field", "type", "message" }] }`, con `message` en español. La respuesta MUST NOT incluir los valores enviados. El `422` queda reservado a las reglas de validez del dominio.

#### Scenario: JSON sintácticamente inválido

- **GIVEN** una ruta que recibe un cuerpo JSON
- **WHEN** se envía un cuerpo que no es JSON válido
- **THEN** el status es `400`
- **AND** `errors[0]` tiene `field` nulo, `type` `json_invalid` y `message` "El cuerpo no es JSON válido."

#### Scenario: Campo obligatorio faltante

- **GIVEN** una ruta que exige el campo `startAt`
- **WHEN** se envía un cuerpo sin `startAt`
- **THEN** el status es `400`
- **AND** `errors[0]` tiene `field` `startAt`, `type` `missing` y `message` "Falta este dato."

#### Scenario: El valor enviado no se devuelve

- **GIVEN** una ruta que exige un entero en el campo `count`
- **WHEN** se envía `count` con el texto `valor-marcado-c18`
- **THEN** el status es `400`
- **AND** el texto `valor-marcado-c18` no aparece en la respuesta

#### Scenario: Parámetro de consulta inválido

- **GIVEN** una ruta que exige un UUID en el parámetro de consulta `professionalId`
- **WHEN** se envía `professionalId=no-es-uuid`
- **THEN** el status es `400`
- **AND** `errors[0]` tiene `field` `professionalId`

### Requirement: Violaciones de conflicto responden 409

Un rechazo cuyas violaciones sean todas de conflicto SHALL responder `409` con `{ "violations": [...] }`. Son de conflicto `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `OUTSIDE_WORKING_HOURS`, `BLOCKED_TIME`, `DUPLICATE_DNI` y `DUPLICATE_NAME`.

#### Scenario: PROFESSIONAL_OVERLAP responde 409

- **GIVEN** una ruta que rechaza con una sola violación `PROFESSIONAL_OVERLAP`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `PROFESSIONAL_OVERLAP`

#### Scenario: CHAIR_OVERLAP responde 409

- **GIVEN** una ruta que rechaza con una sola violación `CHAIR_OVERLAP`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `CHAIR_OVERLAP`

#### Scenario: OUTSIDE_WORKING_HOURS responde 409

- **GIVEN** una ruta que rechaza con una sola violación `OUTSIDE_WORKING_HOURS`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `OUTSIDE_WORKING_HOURS`

#### Scenario: BLOCKED_TIME responde 409

- **GIVEN** una ruta que rechaza con una sola violación `BLOCKED_TIME`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `BLOCKED_TIME`

#### Scenario: DUPLICATE_DNI responde 409

- **GIVEN** una ruta que rechaza con una sola violación `DUPLICATE_DNI`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `DUPLICATE_DNI`

#### Scenario: DUPLICATE_NAME responde 409

- **GIVEN** una ruta que rechaza con una sola violación `DUPLICATE_NAME`
- **WHEN** se invoca la ruta
- **THEN** el status es `409`
- **AND** `violations[0].code` es `DUPLICATE_NAME`

### Requirement: Violaciones de validez responden 422

Un rechazo con una violación de validez SHALL responder `422`. Son de validez `UNKNOWN_REFERENCE`, `INACTIVE_REFERENCE`, `INVALID_DURATION`, `INVALID_START_TIME`, `CROSSES_MIDNIGHT`, `IN_THE_PAST`, `INVALID_WORKING_HOURS`, `OVERLAPPING_WORKING_HOURS`, `INVALID_BLOCK`, `INVALID_DNI`, `EMPTY_NAME`, `STATUS_CHANGE_TOO_EARLY` e `INVALID_TRANSITION`.

#### Scenario: UNKNOWN_REFERENCE responde 422

- **GIVEN** una ruta que rechaza con una sola violación `UNKNOWN_REFERENCE`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `UNKNOWN_REFERENCE`

#### Scenario: INACTIVE_REFERENCE responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INACTIVE_REFERENCE`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INACTIVE_REFERENCE`

#### Scenario: INVALID_DURATION responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_DURATION`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_DURATION`

#### Scenario: INVALID_START_TIME responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_START_TIME`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_START_TIME`

#### Scenario: CROSSES_MIDNIGHT responde 422

- **GIVEN** una ruta que rechaza con una sola violación `CROSSES_MIDNIGHT`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `CROSSES_MIDNIGHT`

#### Scenario: IN_THE_PAST responde 422

- **GIVEN** una ruta que rechaza con una sola violación `IN_THE_PAST`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `IN_THE_PAST`

#### Scenario: INVALID_WORKING_HOURS responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_WORKING_HOURS`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_WORKING_HOURS`

#### Scenario: OVERLAPPING_WORKING_HOURS responde 422

- **GIVEN** una ruta que rechaza con una sola violación `OVERLAPPING_WORKING_HOURS`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `OVERLAPPING_WORKING_HOURS`

#### Scenario: INVALID_BLOCK responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_BLOCK`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_BLOCK`

#### Scenario: INVALID_DNI responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_DNI`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_DNI`

#### Scenario: EMPTY_NAME responde 422

- **GIVEN** una ruta que rechaza con una sola violación `EMPTY_NAME`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `EMPTY_NAME`

#### Scenario: STATUS_CHANGE_TOO_EARLY responde 422

- **GIVEN** una ruta que rechaza con una sola violación `STATUS_CHANGE_TOO_EARLY`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `STATUS_CHANGE_TOO_EARLY`

#### Scenario: INVALID_TRANSITION responde 422

- **GIVEN** una ruta que rechaza con una sola violación `INVALID_TRANSITION`
- **WHEN** se invoca la ruta
- **THEN** el status es `422`
- **AND** `violations[0].code` es `INVALID_TRANSITION`

### Requirement: Operación prohibida responde 403

Un rechazo con `FORBIDDEN_OPERATION` SHALL responder `403` con `{ "violations": [...] }`, conservando el mensaje en español del dominio.

#### Scenario: FORBIDDEN_OPERATION responde 403

- **GIVEN** una ruta que rechaza con una sola violación `FORBIDDEN_OPERATION`
- **WHEN** se invoca la ruta
- **THEN** el status es `403`
- **AND** `violations[0].code` es `FORBIDDEN_OPERATION`

### Requirement: Precedencia de status con códigos mixtos

Un rechazo con códigos de distinto status SHALL responder según la precedencia `403`, luego `422`, luego `409`. El cuerpo SHALL contener todas las violaciones, en el orden que devolvió el dominio.

#### Scenario: Nombre vacío y DNI duplicado responden 422

- **GIVEN** un rechazo con `EMPTY_NAME` seguido de `DUPLICATE_DNI`
- **WHEN** la API lo traduce
- **THEN** el status es `422`
- **AND** `violations` contiene `EMPTY_NAME` y `DUPLICATE_DNI`, en ese orden

#### Scenario: Nombre duplicado y duración inválida responden 422

- **GIVEN** un rechazo con `DUPLICATE_NAME` seguido de `INVALID_DURATION`
- **WHEN** la API lo traduce
- **THEN** el status es `422`
- **AND** `violations` contiene `DUPLICATE_NAME` e `INVALID_DURATION`, en ese orden

#### Scenario: Operación prohibida prevalece sobre validez

- **GIVEN** un rechazo con `IN_THE_PAST` seguido de `FORBIDDEN_OPERATION`
- **WHEN** la API lo traduce
- **THEN** el status es `403`
- **AND** `violations` contiene `IN_THE_PAST` y `FORBIDDEN_OPERATION`, en ese orden

### Requirement: Clasificación total de los códigos de violación

Todo `ViolationCode` SHALL tener un status HTTP asignado explícitamente, sin valor por defecto. La suite SHALL fallar si un código queda sin clasificar.

#### Scenario: Todos los códigos están clasificados

- **GIVEN** la clasificación vigente y el enum `ViolationCode`
- **WHEN** se buscan códigos sin clasificar
- **THEN** el resultado es vacío

#### Scenario: Un código sin clasificar se detecta

- **GIVEN** una clasificación sin `CHAIR_OVERLAP`
- **WHEN** se buscan códigos sin clasificar
- **THEN** el resultado contiene exactamente `CHAIR_OVERLAP`

### Requirement: Forma de cada violación en la respuesta

Cada violación SHALL serializarse en camelCase con `code` y `message` siempre presentes. `conflictingAppointmentId`, `conflictingBlockId`, `conflictingInterval` y `referenceKind` SHALL aparecer solo cuando tienen valor; los vacíos se omiten, no se envían como `null`.

#### Scenario: Violación de solapamiento

- **GIVEN** una violación `PROFESSIONAL_OVERLAP` con turno e intervalo en conflicto
- **WHEN** la API la serializa
- **THEN** el objeto tiene exactamente `code`, `message`, `conflictingAppointmentId` y `conflictingInterval`
- **AND** `conflictingInterval` es `{ "startAt": "2026-10-20T13:00:00Z", "endAt": "2026-10-20T13:30:00Z" }`

#### Scenario: Violación de bloqueo

- **GIVEN** una violación `BLOCKED_TIME` con bloqueo e intervalo en conflicto
- **WHEN** la API la serializa
- **THEN** el objeto tiene exactamente `code`, `message`, `conflictingBlockId` y `conflictingInterval`

#### Scenario: Violación de referencia

- **GIVEN** una violación `UNKNOWN_REFERENCE` del tipo `PROFESSIONAL`
- **WHEN** la API la serializa
- **THEN** el objeto tiene exactamente `code`, `message` y `referenceKind`
- **AND** `referenceKind` es `PROFESSIONAL`

#### Scenario: Violación sin datos adicionales

- **GIVEN** una violación `EMPTY_NAME` sin datos adicionales
- **WHEN** la API la serializa
- **THEN** el objeto tiene exactamente `code` y `message`

### Requirement: CORS limitado al origen configurado

La API SHALL permitir solo el origen de `CORS_ORIGIN`, sin credenciales, con los métodos `GET`, `POST`, `PUT`, `PATCH` y `DELETE` y los headers `Authorization` y `Content-Type`.

#### Scenario: Preflight permitido desde CORS_ORIGIN

- **GIVEN** `CORS_ORIGIN` igual a `http://localhost:5173`
- **WHEN** llega un preflight `POST` desde `http://localhost:5173`
- **THEN** `access-control-allow-origin` es `http://localhost:5173`
- **AND** `access-control-allow-credentials` no aparece en la respuesta

#### Scenario: Respuesta simple permitida desde CORS_ORIGIN

- **GIVEN** `CORS_ORIGIN` igual a `http://localhost:5173`
- **WHEN** llega `GET /api/health` desde `http://localhost:5173`
- **THEN** `access-control-allow-origin` es `http://localhost:5173`

#### Scenario: Preflight rechazado desde otro origen

- **GIVEN** `CORS_ORIGIN` igual a `http://localhost:5173`
- **WHEN** llega un preflight `POST` desde `http://otro-origen.test`
- **THEN** `access-control-allow-origin` no aparece en la respuesta

### Requirement: Documentación OpenAPI con las respuestas de error

Swagger SHALL servirse en `/api/docs` y el esquema en `/api/openapi.json`. El esquema MUST NOT incluir el `422` automático de FastAPI. Toda ruta con entrada SHALL documentar el `400`, y las rutas que rechazan SHALL documentar sus status con el esquema de violaciones.

#### Scenario: Swagger disponible en /api/docs

- **GIVEN** la app sin rutas de prueba
- **WHEN** se invoca `GET /api/docs`
- **THEN** el status es `200`
- **AND** la respuesta es HTML

#### Scenario: Sin el 422 automático

- **GIVEN** una ruta con cuerpo que no declara `422`
- **WHEN** se lee `/api/openapi.json`
- **THEN** esa ruta no documenta `422`
- **AND** `HTTPValidationError` no aparece en el esquema

#### Scenario: 400 documentado en una ruta con entrada

- **GIVEN** una ruta con cuerpo
- **WHEN** se lee `/api/openapi.json`
- **THEN** esa ruta documenta `400` con el esquema de entrada malformada

#### Scenario: 409 documentado en una ruta que rechaza

- **GIVEN** una ruta que declara el rechazo `409`
- **WHEN** se lee `/api/openapi.json`
- **THEN** esa ruta documenta `409` con el esquema de violaciones

#### Scenario: 422 documentado en una ruta que rechaza

- **GIVEN** una ruta que declara el rechazo `422`
- **WHEN** se lee `/api/openapi.json`
- **THEN** esa ruta documenta `422` con el esquema de violaciones

#### Scenario: El esquema lista todos los códigos de violación

- **GIVEN** una ruta que declara un rechazo
- **WHEN** se lee `/api/openapi.json`
- **THEN** el enum de `code` contiene todos los valores de `ViolationCode`

#### Scenario: Salud documenta 200 y 503

- **GIVEN** la app sin rutas de prueba
- **WHEN** se lee `/api/openapi.json`
- **THEN** `GET /api/health` documenta `200` y `503`

### Requirement: Sesión de base por request sin confirmación implícita

Cada request SHALL recibir su propia sesión, que se revierte ante una excepción y se cierra al terminar. La sesión MUST NOT confirmar por su cuenta: una escritura persiste solo si quien es dueño de ella la confirma de forma explícita.

#### Scenario: Una escritura confirmada persiste

- **GIVEN** una ruta que escribe con la sesión del request y la confirma
- **WHEN** se invoca la ruta
- **THEN** la fila existe al leerla desde otra conexión

#### Scenario: Una escritura sin confirmar no persiste

- **GIVEN** una ruta que escribe con la sesión del request y responde sin confirmar
- **WHEN** se invoca la ruta
- **THEN** el status es `200`
- **AND** la fila no existe al leerla desde otra conexión

#### Scenario: Una excepción revierte la escritura

- **GIVEN** una ruta que escribe con la sesión del request y lanza un rechazo del dominio
- **WHEN** se invoca la ruta
- **THEN** el status es el del rechazo
- **AND** la fila no existe al leerla desde otra conexión
