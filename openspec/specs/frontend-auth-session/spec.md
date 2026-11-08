# frontend-auth-session Specification

## Purpose
Autenticación y sesión en el frontend SPA (`frontend/`): confinamiento del token de acceso detrás de `TokenStore` en `src/features/auth/tokenStore.ts` (`sessionStorage` bajo `turnos.auth.accessToken` con fallback en memoria), pantalla `/login` accesible contra `POST /api/auth/login` con mensaje genérico ante `401` y limpieza inmediata de la contraseña, verificación inicial contra `GET /api/auth/me` con estados `checking`, `authenticated` y `anonymous` y reintento ante error de red, rutas protegidas (`RequireAuth` y `PublicOnlyRoute`) con validación de destino interno (`safeInternalPath`), envío de `Authorization: Bearer <token>`, cierre de sesión con mensaje de vencimiento ante `401` en rutas protegidas, preservación de la sesión ante `403`, menú por rol derivado de `/me` con ítems futuros deshabilitados bajo `"Próximamente"` y cierre de sesión directo en `AppShell`.

## Requirements

### Requirement: TokenStore

El token de acceso SHALL guardarse detrás de una interfaz `TokenStore` con `getToken`, `setToken` y `clear`. La implementación de producción MUST usar `sessionStorage` bajo la clave `turnos.auth.accessToken` y MUST caer a memoria si el almacenamiento lanza. Solo `src/features/auth/tokenStore.ts` MUST tocar `sessionStorage`; el resto del front MUST NOT usar `localStorage`, cookies ni `sessionStorage` para el token.

#### Scenario: Guardar y leer el token de la pestaña

- **GIVEN** un `createSessionTokenStore()` sobre el `sessionStorage` real de jsdom
- **WHEN** se ejecuta `setToken("token-ficticio-123")` y después `getToken()`
- **THEN** `getToken()` devuelve `"token-ficticio-123"`
- **AND** `sessionStorage.getItem("turnos.auth.accessToken")` devuelve `"token-ficticio-123"`

#### Scenario: Limpiar el token

- **GIVEN** un `TokenStore` con `setToken("token-ficticio-123")`
- **WHEN** se ejecuta `clear()`
- **THEN** `getToken()` devuelve `null`
- **AND** la clave `turnos.auth.accessToken` ya no existe en `sessionStorage`

#### Scenario: Fallback a memoria si el almacenamiento falla

- **GIVEN** un `sessionStorage` cuyo `setItem` lanza una excepción
- **WHEN** se ejecuta `setToken("token-ficticio-123")`
- **THEN** no se propaga la excepción
- **AND** `getToken()` devuelve `"token-ficticio-123"` desde memoria para esa pestaña

#### Scenario: El storage está confinado a un solo archivo

- **GIVEN** el código de `frontend/src`
- **WHEN** se busca cualquier acceso a `localStorage`, `sessionStorage` o cookies
- **THEN** el único archivo con `sessionStorage` es `src/features/auth/tokenStore.ts`
- **AND** no hay `localStorage` ni cookies, y el cliente de API no importa `sessionStorage`

### Requirement: Login

La pantalla de login SHALL enviar `username` y `password` a `POST /api/auth/login`. Con `200 { "accessToken": "...", "tokenType": "bearer" }` MUST guardar el token, consultar `GET /api/auth/me` y dejar la sesión autenticada. Con `401 { "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }` MUST mostrar ese mensaje genérico sin guardar token ni redirigir.

#### Scenario: Login correcto del administrador

- **GIVEN** el usuario del seed `administrador` y la contraseña ficticia `"<contraseña de prueba>"`
- **WHEN** se completa el formulario y se envía
- **THEN** la request es `POST /api/auth/login` con `{ "username": "administrador", "password": "<contraseña de prueba>" }`
- **AND** el `TokenStore` guarda el `accessToken` y se consulta `GET /api/auth/me`
- **AND** la sesión queda autenticada con `displayName` `"Administración Demo"` y `role` `"administrador"`

#### Scenario: Login correcto de recepción y del odontólogo

- **GIVEN** los usuarios del seed `recepcion` y `odontologo` con `"<contraseña de prueba>"`
- **WHEN** cada uno inicia sesión
- **THEN** recepción queda autenticada con `displayName` `"Recepción Demo"` y `role` `"recepcion"`
- **AND** el odontólogo queda autenticado con `displayName` `"Dra. Laura Quiroga"`, `role` `"odontologo"` y `professionalId` `"00000000-0000-0000-0000-000000000001"`

#### Scenario: Credenciales inválidas con mensaje genérico

- **GIVEN** el usuario `recepcion` y una contraseña incorrecta
- **WHEN** la API responde `401` con `{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }`
- **THEN** se muestra exactamente `"Usuario o contraseña incorrectos."` en un contenedor `role="alert"`
- **AND** no se guarda ningún token, no se redirige y el campo de contraseña queda vacío
- **AND** no se indica si falló el usuario o la contraseña

#### Scenario: Envío en curso y doble submit

- **GIVEN** el formulario de login completo
- **WHEN** se envía y la respuesta todavía no llegó
- **THEN** el botón queda deshabilitado con el texto `"Ingresando…"` y `aria-busy="true"`
- **AND** un segundo envío no dispara otra request

#### Scenario: Accesibilidad del formulario

- **GIVEN** la pantalla de login renderizada
- **WHEN** se consulta el DOM y se navega con teclado
- **THEN** existen las etiquetas visibles `"Usuario"` y `"Contraseña"` con `autocomplete` `username` y `current-password`
- **AND** `Enter` envía el formulario, el error se anuncia con `aria-live` y el foco es visible
- **AND** no existe un botón “ver contraseña” ni una casilla “recordar usuario”

### Requirement: Carga inicial de la sesión con /me

Al arrancar con token, la app SHALL consultar `GET /api/auth/me` y MUST permanecer en `checking` mostrando `LoadingState` sin redirigir. Con `200` MUST pasar a `authenticated` con el usuario; con `401` MUST limpiar el token y quedar `anonymous`; con error de red o `5xx` MUST conservar el token y ofrecer reintento.

#### Scenario: Estado checking mientras se verifica la sesión

- **GIVEN** un token guardado y `GET /api/auth/me` pendiente
- **WHEN** la aplicación monta
- **THEN** se muestra un elemento `role="status"` con `"Cargando..."`
- **AND** no se redirige ni se muestra el formulario de login

#### Scenario: Sesión autenticada con el usuario de /me

- **GIVEN** un token guardado y `GET /api/auth/me` responde `200` con `{ "id": "00000000-0000-0000-0000-0000000000e3", "username": "odontologo", "displayName": "Dra. Laura Quiroga", "role": "odontologo", "professionalId": "00000000-0000-0000-0000-000000000001" }`
- **WHEN** termina la carga inicial
- **THEN** la sesión queda `authenticated`
- **AND** el usuario en memoria es `"Dra. Laura Quiroga"` con `role` `"odontologo"` y ese `professionalId`

#### Scenario: /me responde 401 y limpia la sesión

- **GIVEN** un token guardado y `GET /api/auth/me` responde `401` con `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }`
- **WHEN** termina la carga inicial
- **THEN** el token se descarta y la sesión queda `anonymous`
- **AND** se redirige a `/login` sin mostrar el mensaje de sesión vencida

#### Scenario: Error de red en /me conserva el token y permite reintentar

- **GIVEN** un token guardado y `GET /api/auth/me` falla por red
- **WHEN** termina la carga inicial
- **THEN** el token se conserva y se muestra `ErrorState` con una acción de reintento
- **AND** no se redirige a `/login`
- **AND** al reintentar, `GET /api/auth/me` responde `200` y la sesión queda `authenticated`

### Requirement: Rutas protegidas y redirección con from validado

Una ruta protegida sin sesión MUST redirigir a `/login` con `from` en el state y `replace`. El login MUST volver a `from` solo si es una ruta interna: empezar con `/`, no con `//`, no ser `/login` ni una URL absoluta; si no, MUST volver a `/`. Con sesión, `/login` MUST redirigir a `from` válido o `/`.

#### Scenario: Ruta protegida sin sesión conserva el destino

- **GIVEN** una sesión `anonymous`
- **WHEN** se navega a `/agenda?date=2026-11-07`
- **THEN** se redirige a `/login` con `state.from` igual a `/agenda?date=2026-11-07`
- **AND** la entrada de la ruta protegida no queda en el historial (`replace`)

#### Scenario: Login con sesión vuelve al destino válido

- **GIVEN** una sesión `authenticated` y `from` igual a `/agenda?date=2026-11-07`
- **WHEN** se navega a `/login`
- **THEN** se redirige a `/agenda?date=2026-11-07` sin mostrar el formulario

#### Scenario: Se rechaza una ruta protocol-relative

- **GIVEN** un `from` igual a `"//evil.com"`
- **WHEN** se valida el destino
- **THEN** el destino seguro es `/`

#### Scenario: Se rechaza una URL absoluta

- **GIVEN** un `from` igual a `"https://evil.example"`
- **WHEN** se valida el destino
- **THEN** el destino seguro es `/`

#### Scenario: Se rechaza volver al propio login

- **GIVEN** un `from` igual a `"/login"`
- **WHEN** se valida el destino
- **THEN** el destino seguro es `/`

#### Scenario: Sin parpadeo de login a home

- **GIVEN** un token guardado y `GET /api/auth/me` pendiente
- **WHEN** se navega a `/login`
- **THEN** se muestra `LoadingState` y no el formulario
- **AND** no se redirige hasta conocer el estado de la sesión

### Requirement: 401 durante el uso

Ante un `401` de una request protegida, la app MUST descartar el token, limpiar el usuario y volver a `/login` con `replace`, conservando `from` y mostrando `"La sesión venció. Iniciá sesión de nuevo."`. El `401` de `POST /api/auth/login` MUST NOT limpiar la sesión ni redirigir.

#### Scenario: Token vencido en una request protegida

- **GIVEN** una sesión `authenticated` con token y `from` igual a `/agenda?date=2026-11-07`
- **WHEN** una request protegida responde `401` con `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }`
- **THEN** el token y el usuario se descartan y la sesión queda `anonymous` con motivo `expired`
- **AND** se redirige a `/login` con `replace` y `state.from` igual a `/agenda?date=2026-11-07`
- **AND** se muestra `"La sesión venció. Iniciá sesión de nuevo."`

#### Scenario: El 401 del login no es sesión vencida

- **GIVEN** la pantalla de login sin sesión
- **WHEN** `POST /api/auth/login` responde `401` con `{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }`
- **THEN** se permanece en `/login` sin redirección
- **AND** se muestra el mensaje genérico del formulario y no `"La sesión venció. Iniciá sesión de nuevo."`

### Requirement: 403 sin cerrar sesión

Ante un `403` con `violations`, la app MUST mostrar los mensajes del dominio tal cual y MUST NOT descartar el token, MUST NOT cerrar la sesión y MUST NOT refrescar `/me`.

#### Scenario: Rol sin permiso muestra la violación

- **GIVEN** una sesión `authenticated` del usuario `odontologo`
- **WHEN** una acción responde `403` con `{ "violations": [{ "code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para dar turnos." }] }`
- **THEN** se muestra exactamente `"No tiene permiso para dar turnos."`
- **AND** el token sigue guardado y la sesión sigue `authenticated`
- **AND** no se vuelve a llamar a `GET /api/auth/me`

### Requirement: Menú por rol

El menú SHALL derivarse del `role` de `/me` y de la matriz RBAC, sin decodificar el JWT. Los ítems cuyas pantallas todavía no existen MUST mostrarse deshabilitados con la etiqueta `"Próximamente"`. El rol MUST NOT ser la autorización: la API sigue rechazando con `403`.

#### Scenario: Menú del administrador

- **GIVEN** una sesión `authenticated` con `role` `"administrador"`
- **WHEN** se renderiza el menú
- **THEN** aparecen los ítems `"Agenda"`, `"Turnos"`, `"Horarios y bloqueos"`, `"Catálogos"`, `"Pacientes"` y `"Usuarios y roles"`
- **AND** todos los ítems de pantallas futuras están deshabilitados con `"Próximamente"`

#### Scenario: Menú de recepción

- **GIVEN** una sesión `authenticated` con `role` `"recepcion"`
- **WHEN** se renderiza el menú
- **THEN** aparecen `"Agenda"`, `"Turnos"`, `"Horarios y bloqueos"`, `"Catálogos"` y `"Pacientes"`
- **AND** no aparece `"Usuarios y roles"`

#### Scenario: Menú del odontólogo

- **GIVEN** una sesión `authenticated` con `role` `"odontologo"`
- **WHEN** se renderiza el menú
- **THEN** aparecen `"Agenda"`, `"Horarios y bloqueos"`, `"Catálogos"` y `"Pacientes"`
- **AND** no aparecen `"Turnos"` ni `"Usuarios y roles"`

### Requirement: Logout

El cierre de sesión MUST descartar el token y el usuario, MUST NOT llamar a ningún endpoint del backend, MUST navegar a `/login` con `replace` y MUST NOT pedir confirmación ni mostrar el mensaje de sesión vencida.

#### Scenario: Cerrar sesión desde el shell

- **GIVEN** una sesión `authenticated` del usuario `recepcion` con token guardado
- **WHEN** se activa la acción `"Cerrar sesión"`
- **THEN** el token y el usuario se descartan y la sesión queda `anonymous`
- **AND** se navega a `/login` con `replace` sin diálogo de confirmación
- **AND** no se llama a ningún endpoint de logout ni se muestra `"La sesión venció. Iniciá sesión de nuevo."`

### Requirement: Header Authorization Bearer

El cliente de API SHALL agregar `Authorization: Bearer <token>` a las peticiones autenticadas cuando el `TokenStore` tiene token. El login MUST NOT enviar `Authorization` aunque exista un token viejo. Sin token, MUST NOT enviar el header.

#### Scenario: Petición autenticada con Bearer

- **GIVEN** un `TokenStore` con `"token-ficticio-123"`
- **WHEN** se invoca `GET /api/auth/me`
- **THEN** la request incluye `Authorization` con el valor `"Bearer token-ficticio-123"`

#### Scenario: El login no manda un token viejo

- **GIVEN** un `TokenStore` con `"token-viejo"`
- **WHEN** se invoca `POST /api/auth/login`
- **THEN** la request no incluye el header `Authorization`

#### Scenario: Sin token no se envía Authorization

- **GIVEN** un `TokenStore` vacío
- **WHEN** se invoca una request
- **THEN** la request no incluye el header `Authorization`
