# authentication-and-rbac Specification

## Purpose

Autenticación y control de acceso de la API. El login con usuario y contraseña
verifica hashes Argon2id de parámetros fijos y responde el mismo `401` para un
usuario inexistente, una contraseña incorrecta y un usuario inactivo, verificando
siempre un hash, ficticio si el usuario no existe. El token es un JWT HS256 con
exactamente `sub`, `role` y `exp`. En cada request se relee el usuario: inexistente,
inactivo o con un rol distinto del token responde `401`. Los permisos son una matriz
RBAC como tabla de datos, con rechazo por defecto y `403` para el rol sin permiso, y
tests guardianes sobre todas las rutas. El `Actor` del dominio se arma solo desde el
usuario autenticado. Hash, contraseña y secretos quedan fuera de respuestas, logs y
mensajes de error. Swagger ofrece el botón *Authorize* con el esquema `bearerAuth`.

## Requirements

### Requirement: Login con credenciales válidas

`POST /api/auth/login` SHALL recibir `username` y `password` en JSON. Con credenciales válidas de un usuario activo SHALL responder `200` con exactamente `accessToken` y `tokenType` igual a `bearer`, y el header `Cache-Control: no-store`. El `username` SHALL compararse recortado y en minúsculas.

#### Scenario: Login correcto del administrador

- **GIVEN** el usuario activo `administrador` con su contraseña
- **WHEN** se invoca `POST /api/auth/login` con esas credenciales
- **THEN** el status es `200`
- **AND** el cuerpo tiene exactamente las claves `accessToken` y `tokenType`
- **AND** `tokenType` es `bearer`

#### Scenario: Login correcto de recepción

- **GIVEN** el usuario activo `recepcion` con su contraseña
- **WHEN** se invoca `POST /api/auth/login` con esas credenciales
- **THEN** el status es `200`
- **AND** `tokenType` es `bearer`

#### Scenario: Login correcto del odontólogo

- **GIVEN** el usuario activo `odontologo` con su contraseña
- **WHEN** se invoca `POST /api/auth/login` con esas credenciales
- **THEN** el status es `200`
- **AND** `tokenType` es `bearer`

#### Scenario: La respuesta del login no se guarda en caché

- **GIVEN** el usuario activo `recepcion` con su contraseña
- **WHEN** se invoca `POST /api/auth/login` con esas credenciales
- **THEN** el header `Cache-Control` es `no-store`

#### Scenario: El usuario se normaliza al buscarlo

- **GIVEN** el usuario activo `recepcion` con su contraseña
- **WHEN** se invoca `POST /api/auth/login` con `username` igual a `  Recepcion `
- **THEN** el status es `200`

### Requirement: Mismo 401 ante credenciales inválidas

Toda credencial inválida SHALL responder `401` con `{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }` y el header `WWW-Authenticate: Bearer`. La respuesta MUST NOT permitir distinguir un usuario inexistente, una contraseña incorrecta y un usuario inactivo. Toda autenticación SHALL verificar un hash, ficticio si el usuario no existe.

#### Scenario: Contraseña incorrecta

- **GIVEN** el usuario activo `recepcion`
- **WHEN** se invoca el login con una contraseña incorrecta
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_CREDENTIALS`
- **AND** el header `WWW-Authenticate` es `Bearer`

#### Scenario: Usuario inexistente

- **GIVEN** que no existe el usuario `nadie`
- **WHEN** se invoca el login con `username` igual a `nadie`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_CREDENTIALS`

#### Scenario: Usuario inactivo con contraseña correcta

- **GIVEN** el usuario `recepcion` con `active` en falso
- **WHEN** se invoca el login con su contraseña correcta
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_CREDENTIALS`

#### Scenario: Usuario inactivo con contraseña incorrecta

- **GIVEN** el usuario `recepcion` con `active` en falso
- **WHEN** se invoca el login con una contraseña incorrecta
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_CREDENTIALS`

#### Scenario: Los cuerpos son idénticos byte por byte

- **GIVEN** las respuestas de los cuatro casos de credenciales inválidas
- **WHEN** se comparan sus cuerpos como bytes
- **THEN** los cuatro cuerpos son iguales
- **AND** los cuatro tienen los mismos headers `WWW-Authenticate` y `Content-Type`

#### Scenario: Un usuario inexistente se verifica contra el hash ficticio

- **GIVEN** que no se encontraron credenciales para el usuario pedido
- **WHEN** se elige el hash a verificar
- **THEN** el hash elegido es el hash ficticio
- **AND** el hash ficticio usa los parámetros de producción

#### Scenario: Un hash guardado corrupto cuenta como contraseña incorrecta

- **GIVEN** un usuario activo cuyo `password_hash` no es una cadena Argon2 válida
- **WHEN** se invoca el login con cualquier contraseña
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_CREDENTIALS`

### Requirement: Entrada del login validada

El login SHALL aceptar `username` de 1 a 150 caracteres y `password` de 1 a 128, sin campos adicionales. Un cuerpo fuera de esas reglas SHALL responder `400` según el contrato de entrada malformada, sin consultar el usuario.

#### Scenario: Falta la contraseña

- **GIVEN** un cuerpo con `username` y sin `password`
- **WHEN** se invoca el login
- **THEN** el status es `400`
- **AND** `errors[0].field` es `password`

#### Scenario: Contraseña de más de 128 caracteres

- **GIVEN** un cuerpo con `password` de 129 caracteres
- **WHEN** se invoca el login
- **THEN** el status es `400`

#### Scenario: Campo adicional

- **GIVEN** un cuerpo con `username`, `password` y `role`
- **WHEN** se invoca el login
- **THEN** el status es `400`

### Requirement: Contraseñas guardadas solo como hash Argon2id

Toda contraseña SHALL guardarse como hash Argon2id con `m=65536`, `t=3` y `p=4`. Esos parámetros MUST NOT depender del entorno ni de ninguna configuración. El perfil barato de la librería MUST NOT aparecer en el código de producción.

#### Scenario: El hash usa los parámetros fijados

- **WHEN** se hashea una contraseña
- **THEN** el resultado empieza con `$argon2id$v=19$m=65536,t=3,p=4$`

#### Scenario: Dos hashes de la misma contraseña difieren

- **WHEN** se hashea dos veces la misma contraseña
- **THEN** los dos resultados son distintos

#### Scenario: Una contraseña correcta se verifica

- **GIVEN** el hash de una contraseña
- **WHEN** se verifica esa misma contraseña
- **THEN** el resultado es verdadero

#### Scenario: Una contraseña incorrecta no se verifica

- **GIVEN** el hash de una contraseña
- **WHEN** se verifica otra contraseña
- **THEN** el resultado es falso

#### Scenario: Se verifica con los parámetros guardados en el hash

- **GIVEN** un hash generado con el perfil barato, solo en el test
- **WHEN** se verifica su contraseña con el código de producción
- **THEN** el resultado es verdadero

#### Scenario: El perfil barato no está en producción

- **WHEN** se busca `CHEAPEST` en los archivos de `backend/app`
- **THEN** no hay ninguna coincidencia

### Requirement: Token firmado con exactamente tres claims

El token SHALL firmarse con `JWT_SECRET` y contener exactamente `sub` (id del usuario como texto), `role` y `exp`, igual a `now` más `JWT_EXPIRES_MIN`. `now` SHALL inyectarse al emitir. MUST NOT contener nombres, `professional_id` ni otros datos.

#### Scenario: Claims exactos del token

- **GIVEN** un usuario de rol `recepcion` y `now` igual a `2026-11-05T12:00:00Z`, con `JWT_EXPIRES_MIN` en 60
- **WHEN** se emite el token y se decodifica su contenido
- **THEN** las claves son exactamente `sub`, `role` y `exp`
- **AND** `sub` es el id del usuario, `role` es `recepcion`, y `exp` corresponde a `2026-11-05T13:00:00Z`

#### Scenario: El token del login corresponde al usuario

- **GIVEN** el usuario activo `recepcion` con su contraseña
- **WHEN** se invoca el login y se decodifica `accessToken`
- **THEN** `sub` es el id de ese usuario
- **AND** `role` es `recepcion`

### Requirement: Token ausente y formato inválido responden 401

Una ruta protegida SHALL responder `401` con `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }` y `WWW-Authenticate: Bearer` si no recibe un Bearer legible en el header `Authorization`. El token MUST NOT aceptarse desde la URL.

#### Scenario: Sin header Authorization

- **WHEN** se invoca una ruta protegida sin header `Authorization`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`
- **AND** el header `WWW-Authenticate` es `Bearer`

#### Scenario: Bearer vacío

- **WHEN** se invoca una ruta protegida con `Authorization: Bearer `
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Esquema Basic

- **WHEN** se invoca una ruta protegida con `Authorization: Basic dXN1YXJpbzpjbGF2ZQ==`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Texto que no es un token

- **WHEN** se invoca una ruta protegida con `Authorization: Bearer no-es-un-token`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Token válido en la URL

- **GIVEN** un token válido
- **WHEN** se invoca una ruta protegida con ese token en `?token=` y sin header `Authorization`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

### Requirement: Token vencido responde 401

Un token con firma válida y `exp` en el pasado SHALL responder `401` con el cuerpo de `INVALID_TOKEN`, sin margen de tolerancia y sin consultar la base. El vencimiento SHALL probarse con tokens reales emitidos con un `now` en el pasado.

#### Scenario: Token vencido hace años

- **GIVEN** un token emitido con `now` igual a `2020-01-01T00:00:00Z`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Token vencido hace un segundo

- **GIVEN** un token cuyo `exp` es un segundo anterior al reloj real
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Un token vencido no abre conexión con la base

- **GIVEN** una app configurada contra un puerto local realmente cerrado y un token vencido
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`

### Requirement: Token alterado responde 401

Un token con firma inválida, con un algoritmo distinto de `HS256`, con claims faltantes, y con claims de valores inválidos SHALL responder `401` con el cuerpo de `INVALID_TOKEN`. El algoritmo MUST NOT tomarse del token.

#### Scenario: Payload cambiado con la firma original

- **GIVEN** un token de `recepcion` cuyo payload se reemplazó por uno con `role` igual a `administrador`, sin refirmar
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Firma alterada

- **GIVEN** un token válido con el primer carácter de la firma cambiado
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Firmado con otra clave

- **GIVEN** un token firmado con un secreto distinto de `JWT_SECRET`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Algoritmo none

- **GIVEN** un token con `alg` igual a `none` y sin firma
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Otro algoritmo con la misma clave

- **GIVEN** un token firmado con `HS512` y `JWT_SECRET`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Sin claim exp

- **GIVEN** un token firmado con `JWT_SECRET` que no tiene `exp`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Sin claim sub

- **GIVEN** un token firmado con `JWT_SECRET` que no tiene `sub`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Sin claim role

- **GIVEN** un token firmado con `JWT_SECRET` que no tiene `role`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Claim sub que no es un UUID

- **GIVEN** un token firmado con `JWT_SECRET` cuyo `sub` es `no-es-uuid`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Claim role desconocido

- **GIVEN** un token firmado con `JWT_SECRET` cuyo `role` es `superusuario`
- **WHEN** se invoca una ruta protegida con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

### Requirement: El usuario se confirma contra la base en cada request

Con un token válido, cada request SHALL leer el usuario. Un usuario inexistente, un usuario inactivo, y un rol distinto del claim `role` SHALL responder `401` con el cuerpo de `INVALID_TOKEN`. `professional_id` SHALL salir siempre de la base. Sin revocación por token: cerrar sesión en el cliente no invalida el token.

#### Scenario: Usuario inexistente con token válido

- **GIVEN** un token válido cuyo `sub` no corresponde a ninguna fila
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Usuario desactivado con token vigente

- **GIVEN** un token válido del usuario `recepcion`, que después se desactiva
- **WHEN** se invoca `GET /api/auth/me` con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Usuario con otro rol y token vigente

- **GIVEN** un token válido del usuario `recepcion`, cuyo rol después cambia a `administrador`
- **WHEN** se invoca `GET /api/auth/me` con ese token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

#### Scenario: Después de cambiar el rol, un login nuevo trae el rol nuevo

- **GIVEN** el usuario `recepcion`, cuyo rol cambió a `administrador`
- **WHEN** se invoca el login y después `GET /api/auth/me` con el token nuevo
- **THEN** el status es `200`
- **AND** `role` es `administrador`

#### Scenario: Usuario reactivado con token todavía vigente

- **GIVEN** un token válido de un usuario que se desactivó y después se reactivó
- **WHEN** se invoca `GET /api/auth/me` con ese token
- **THEN** el status es `200`

#### Scenario: Cambio de profesional con token vigente

- **GIVEN** un token válido de un odontólogo, cuyo `professional_id` después cambia a otro profesional
- **WHEN** se invoca `GET /api/auth/me` con ese token
- **THEN** el status es `200`
- **AND** `professionalId` es el del profesional nuevo

### Requirement: Datos del usuario autenticado

`GET /api/auth/me` SHALL responder `200` con exactamente `id`, `username`, `displayName`, `role` y `professionalId`. `professionalId` SHALL ser nulo para recepción y administración.

#### Scenario: Usuario autenticado odontólogo

- **GIVEN** un token válido del usuario `odontologo`, vinculado al profesional `00000000-0000-0000-0000-000000000001`
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** el status es `200`
- **AND** el cuerpo tiene exactamente `id`, `username`, `displayName`, `role` y `professionalId`
- **AND** `professionalId` es `00000000-0000-0000-0000-000000000001`

#### Scenario: Usuario autenticado de recepción

- **GIVEN** un token válido del usuario `recepcion`
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** el status es `200`
- **AND** `professionalId` es nulo

#### Scenario: Usuario autenticado administrador

- **GIVEN** un token válido del usuario `administrador`
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** el status es `200`
- **AND** `professionalId` es nulo

### Requirement: Odontólogo con profesional desactivado

En el MVP, un odontólogo activo cuyo profesional está desactivado SHALL poder iniciar sesión y operar según la matriz. `active` del usuario y del profesional son independientes. El dominio sigue rechazando turnos nuevos para ese profesional.

#### Scenario: Login con el profesional desactivado

- **GIVEN** el usuario activo `odontologo`, cuyo profesional está desactivado
- **WHEN** se invoca el login con su contraseña
- **THEN** el status es `200`

#### Scenario: Consulta con el profesional desactivado

- **GIVEN** un token válido del usuario `odontologo`, cuyo profesional está desactivado
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** el status es `200`

### Requirement: Actor del dominio desde el usuario autenticado

El `Actor` SHALL construirse solo desde el usuario confirmado contra la base: `user_id` con su id, `role` con su rol, y `professional_id` con su vínculo. MUST NOT tomar ningún dato de headers, cuerpo ni parámetros enviados por el cliente.

#### Scenario: Actor del odontólogo

- **GIVEN** un token válido del usuario `odontologo`, y una ruta de prueba que devuelve su `Actor`
- **WHEN** se invoca la ruta
- **THEN** `user_id` es el id del usuario, `role` es `ODONTOLOGO`, y `professional_id` es `00000000-0000-0000-0000-000000000001`
- **AND** `user_id` es distinto de `professional_id`

#### Scenario: Actor de recepción

- **GIVEN** un token válido del usuario `recepcion`, y una ruta de prueba que devuelve su `Actor`
- **WHEN** se invoca la ruta
- **THEN** `role` es `RECEPCION` y `professional_id` es nulo

#### Scenario: Actor del administrador

- **GIVEN** un token válido del usuario `administrador`, y una ruta de prueba que devuelve su `Actor`
- **WHEN** se invoca la ruta
- **THEN** `role` es `ADMINISTRADOR` y `professional_id` es nulo

#### Scenario: Un header del cliente no cambia el Actor

- **GIVEN** un token válido del usuario `recepcion`
- **WHEN** se invoca la ruta de prueba con el header `X-Role: administrador`
- **THEN** `role` del `Actor` es `RECEPCION`

### Requirement: Matriz RBAC completa

Los permisos SHALL ser una tabla de datos con las 34 combinaciones de recurso y acción de la tabla "Matriz RBAC" de `design.md` de este change, derivada de KB 03. Una combinación sin entrada para un rol MUST responder `403`. Un test guardián SHALL recorrer las 102 celdas contra una copia literal independiente.

#### Scenario: La tabla de permisos coincide con la matriz

- **GIVEN** la copia literal de las 34 filas de la matriz en el test guardián
- **WHEN** se compara con la tabla de permisos del código
- **THEN** son iguales en las 102 celdas

#### Scenario: La tabla de permisos cubre todas las combinaciones

- **GIVEN** las 34 combinaciones de recurso y acción de la matriz
- **WHEN** se buscan combinaciones sin entrada en la tabla de permisos
- **THEN** el resultado es vacío

#### Scenario: Una combinación faltante se detecta

- **GIVEN** una tabla de permisos sin la combinación de crear turnos
- **WHEN** se buscan combinaciones sin entrada
- **THEN** el resultado contiene exactamente crear turnos

#### Scenario: Las 102 celdas responden lo esperado por HTTP

- **GIVEN** una ruta de prueba por cada combinación de la matriz, y un token real de cada rol
- **WHEN** el test guardián invoca cada ruta con cada rol
- **THEN** las 61 celdas permitidas responden `200`
- **AND** las 41 celdas denegadas responden `403`

### Requirement: Rol sin permiso responde 403 con violaciones

Un rol sin permiso SHALL recibir `403` con `{ "violations": [...] }`, con una sola violación `FORBIDDEN_OPERATION` y mensaje en español. Sin token válido SHALL recibir `401`, antes de evaluar permisos.

#### Scenario: Odontólogo que da un turno

- **GIVEN** un token válido del usuario `odontologo`, y una ruta que exige crear turnos
- **WHEN** se invoca la ruta
- **THEN** el status es `403`
- **AND** `violations` tiene una sola violación con `code` `FORBIDDEN_OPERATION`
- **AND** `message` es `No tiene permiso para dar turnos.`

#### Scenario: Recepción que crea un profesional

- **GIVEN** un token válido del usuario `recepcion`, y una ruta que exige crear profesionales
- **WHEN** se invoca la ruta
- **THEN** el status es `403`
- **AND** `message` es `No tiene permiso para crear profesionales.`

#### Scenario: Nadie borra pacientes

- **GIVEN** un token válido del usuario `administrador`, y una ruta que exige borrar pacientes
- **WHEN** se invoca la ruta
- **THEN** el status es `403`

#### Scenario: Sin token en una ruta con permiso

- **GIVEN** una ruta que exige crear turnos
- **WHEN** se invoca la ruta sin token
- **THEN** el status es `401`
- **AND** el cuerpo es exactamente el de `INVALID_TOKEN`

### Requirement: Alcance propio informado a la ruta

Una celda permitida SHALL entregar a la ruta el `Actor` y su alcance, total para todos los registros y propio para los del usuario. La propiedad de un turno SHALL decidirla el dominio; la API MUST NOT comparar el propietario de un turno.

#### Scenario: Odontólogo con alcance propio en horarios

- **GIVEN** un token válido del usuario `odontologo`, y una ruta que exige actualizar horarios
- **WHEN** se invoca la ruta
- **THEN** el alcance recibido es propio

#### Scenario: Administrador con alcance total en horarios

- **GIVEN** un token válido del usuario `administrador`, y una ruta que exige actualizar horarios
- **WHEN** se invoca la ruta
- **THEN** el alcance recibido es total

#### Scenario: Odontólogo con alcance total en la agenda

- **GIVEN** un token válido del usuario `odontologo`, y una ruta que exige leer la agenda
- **WHEN** se invoca la ruta
- **THEN** el alcance recibido es total

### Requirement: La matriz coincide con el dominio en los turnos

Las filas de reprogramar, cancelar y cambiar estado SHALL coincidir con lo que aplica el dominio para cada rol, sin duplicar la regla en la API. Un test de paridad SHALL ejecutar las operaciones reales del dominio.

#### Scenario: Paridad al reprogramar

- **GIVEN** un turno válido y un `Actor` de cada rol
- **WHEN** se ejecuta la reprogramación del dominio con cada `Actor`
- **THEN** el rechazo con `FORBIDDEN_OPERATION` ocurre solo en los roles sin permiso en la matriz

#### Scenario: Paridad al cancelar

- **GIVEN** un turno válido y un `Actor` de cada rol
- **WHEN** se ejecuta la cancelación del dominio con cada `Actor`
- **THEN** el rechazo con `FORBIDDEN_OPERATION` ocurre solo en los roles sin permiso en la matriz

#### Scenario: Paridad al cambiar estado de un turno propio

- **GIVEN** un turno del profesional del odontólogo, y un `Actor` de cada rol
- **WHEN** se ejecuta el cambio de estado del dominio con cada `Actor`
- **THEN** ninguno recibe `FORBIDDEN_OPERATION`

#### Scenario: Paridad al cambiar estado de un turno ajeno

- **GIVEN** un turno de otro profesional, y un `Actor` de cada rol
- **WHEN** se ejecuta el cambio de estado del dominio con cada `Actor`
- **THEN** solo el odontólogo recibe `FORBIDDEN_OPERATION`

### Requirement: Rechazo por defecto en todas las rutas

Toda ruta de la API SHALL exigir un token válido, salvo las públicas `GET /api/health` y `POST /api/auth/login`, además de `/api/docs` y `/api/openapi.json`. Toda ruta protegida salvo `GET /api/auth/me` SHALL declarar un permiso de la matriz. Tests guardianes SHALL recorrer todas las rutas.

#### Scenario: Salud sin token

- **WHEN** se invoca `GET /api/health` sin token, con la base disponible
- **THEN** el status es `200`

#### Scenario: Las rutas reales no públicas exigen token

- **GIVEN** la app real y la lista de rutas públicas
- **WHEN** el guardián invoca sin token cada ruta no pública del esquema
- **THEN** cada una responde `401`

#### Scenario: Una ruta sin protección se detecta

- **GIVEN** una app de prueba con una ruta montada fuera del router protegido
- **WHEN** el guardián de rutas revisa esa app
- **THEN** el resultado contiene exactamente esa ruta

#### Scenario: Las rutas protegidas reales declaran permiso

- **GIVEN** la app real
- **WHEN** el guardián de permisos revisa sus rutas protegidas
- **THEN** el resultado es vacío

#### Scenario: Una ruta protegida sin permiso se detecta

- **GIVEN** una app de prueba con una ruta protegida sin permiso declarado
- **WHEN** el guardián de permisos revisa esa app
- **THEN** el resultado contiene exactamente esa ruta

### Requirement: Configuración del token validada al arrancar

`JWT_SECRET` SHALL tener al menos 32 caracteres, `JWT_ALGORITHM` SHALL ser `HS256` y `JWT_EXPIRES_MIN` SHALL ser positivo. Un valor inválido SHALL impedir cargar la configuración con un error que nombre la variable. El error MUST NOT mostrar el valor recibido.

#### Scenario: Secreto de 31 caracteres

- **GIVEN** un `JWT_SECRET` de 31 caracteres marcado con un texto reconocible
- **WHEN** se carga la configuración
- **THEN** falla con un error que nombra `JWT_SECRET`
- **AND** el texto reconocible no aparece en el error

#### Scenario: Secreto de 32 caracteres

- **GIVEN** un `JWT_SECRET` de 32 caracteres
- **WHEN** se carga la configuración
- **THEN** la configuración se carga

#### Scenario: Secreto vacío

- **GIVEN** un `JWT_SECRET` vacío
- **WHEN** se carga la configuración
- **THEN** falla con un error que nombra `JWT_SECRET`

#### Scenario: Algoritmo none

- **GIVEN** `JWT_ALGORITHM` igual a `none`
- **WHEN** se carga la configuración
- **THEN** falla con un error que nombra `jwt_algorithm`

#### Scenario: Algoritmo asimétrico

- **GIVEN** `JWT_ALGORITHM` igual a `RS256`
- **WHEN** se carga la configuración
- **THEN** falla con un error que nombra `jwt_algorithm`

#### Scenario: Vigencia en cero

- **GIVEN** `JWT_EXPIRES_MIN` igual a `0`
- **WHEN** se carga la configuración
- **THEN** falla con un error que nombra `jwt_expires_min`

### Requirement: Secretos fuera de respuestas

Ninguna respuesta ni esquema OpenAPI SHALL contener el hash, la contraseña recibida, ni un campo cuyo nombre empiece con `password` en las respuestas exitosas.

#### Scenario: El login no devuelve hash ni contraseña

- **GIVEN** un login correcto con una contraseña marcada
- **WHEN** se recorre la respuesta completa
- **THEN** no aparecen el hash, la contraseña, ni una clave que empiece con `password`

#### Scenario: La consulta del usuario no devuelve hash

- **GIVEN** un token válido
- **WHEN** se recorre la respuesta completa de `GET /api/auth/me`
- **THEN** no aparecen el hash, ni una clave que empiece con `password`

#### Scenario: Un login malformado no devuelve la contraseña

- **GIVEN** un cuerpo de login con una contraseña marcada y un `username` de 151 caracteres
- **WHEN** se invoca el login
- **THEN** el status es `400`
- **AND** la contraseña marcada no aparece en la respuesta

#### Scenario: Los esquemas de respuesta no tienen hash

- **WHEN** se recorren los esquemas de respuesta de `/api/openapi.json`
- **THEN** ninguno tiene `passwordHash` ni `password_hash`

### Requirement: Secretos fuera de logs y mensajes de error

Los logs, las representaciones de texto y los errores de base MUST NOT contener contraseñas, hashes ni tokens. Los módulos de autenticación MUST NOT escribir logs. Los errores de escritura de usuarios MUST NOT incluir el detalle de la fila.

#### Scenario: Un login correcto no deja secretos en los logs

- **GIVEN** la captura de logs en nivel `DEBUG`
- **WHEN** se ejecuta un login correcto con una contraseña marcada
- **THEN** los logs no contienen la contraseña, el hash ni el token

#### Scenario: Un login fallido no deja secretos en los logs

- **GIVEN** la captura de logs en nivel `DEBUG`
- **WHEN** se ejecuta un login fallido con una contraseña marcada
- **THEN** los logs no contienen la contraseña

#### Scenario: Las credenciales internas no muestran el hash

- **GIVEN** las credenciales internas de un usuario
- **WHEN** se obtiene su representación de texto
- **THEN** no contiene el hash

#### Scenario: La configuración no muestra los secretos

- **GIVEN** una configuración cargada con `JWT_SECRET` y `SEED_USER_PASSWORD`
- **WHEN** se obtiene su representación de texto
- **THEN** no contiene ninguno de los dos valores

#### Scenario: Un usuario duplicado no filtra el hash

- **GIVEN** un usuario existente
- **WHEN** el repositorio inserta otro con el mismo `username`
- **THEN** el texto completo de la excepción no contiene el hash

#### Scenario: Una regla de rol violada no filtra el hash

- **GIVEN** un usuario `recepcion` con `professional_id`
- **WHEN** el repositorio intenta insertarlo
- **THEN** el texto completo de la excepción no contiene el hash

### Requirement: Autorización documentada en Swagger

El esquema OpenAPI SHALL declarar un esquema Bearer llamado `bearerAuth`, y Swagger SHALL conservar la autorización al recargar. Toda operación protegida SHALL documentar `401` con el esquema de autenticación, y las que exigen un permiso SHALL documentar `403` con el esquema de violaciones.

#### Scenario: Esquema bearerAuth declarado

- **WHEN** se lee `/api/openapi.json`
- **THEN** `components.securitySchemes.bearerAuth` tiene `type` `http`, `scheme` `bearer` y `bearerFormat` `JWT`

#### Scenario: La ruta del usuario autenticado tiene candado

- **WHEN** se lee `/api/openapi.json`
- **THEN** `GET /api/auth/me` declara `security` con `bearerAuth`
- **AND** documenta `401` con el esquema de autenticación

#### Scenario: El login no tiene candado

- **WHEN** se lee `/api/openapi.json`
- **THEN** `POST /api/auth/login` no declara `security`
- **AND** documenta `200`, `400` y `401`

#### Scenario: Salud no tiene candado

- **WHEN** se lee `/api/openapi.json`
- **THEN** `GET /api/health` no declara `security`

#### Scenario: Una ruta con permiso documenta 403

- **GIVEN** una ruta de prueba que exige un permiso
- **WHEN** se lee el esquema
- **THEN** esa ruta documenta `403` con el esquema de violaciones

#### Scenario: Swagger conserva la autorización

- **WHEN** se invoca `GET /api/docs`
- **THEN** el HTML contiene `persistAuthorization`
