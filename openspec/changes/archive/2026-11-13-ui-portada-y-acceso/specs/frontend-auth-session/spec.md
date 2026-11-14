# frontend-auth-session Specification

## Purpose

Actualizar los requisitos de la pantalla `/login` para reflejar la página limpia con superficie navy translúcida (`backdrop-filter: blur`), fallback sólido, campos oscuros con borde fino, botón "Ingresar" con flecha en hover, etiqueta opcional de rol proveniente de `?rol` (sin afectar la autorización del backend), conservación de redirecciones seguras y despliegue del mensaje literal de sesión vencida `SESSION_EXPIRED_MESSAGE`.

## MODIFIED Requirements

### Requirement: Login

La pantalla `/login` SHALL ser una vista limpia con "← Volver", logo claro, bajada "Claridad en cada cuidado.", heading "Turnos Odontología" y etiqueta de rol si `?rol` es recepcion, odontologo o administrador. El formulario sobre carrusel difuminado SHALL usar superficie navy translúcida con `backdrop-filter: blur` (o fallback sólido). MUST enviar credenciales a la API, autenticar con 200, rechazar con mensaje genérico ante 401, conservar redirecciones y reflejar `SESSION_EXPIRED_MESSAGE`.

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

#### Scenario: Formulario translúcido en /login con etiqueta de rol y envío de credenciales

- **GIVEN** un usuario que navega a `/login?rol=recepcion`
- **WHEN** la pantalla de login monta sobre el carrusel difuminado
- **THEN** se muestra la superficie navy translúcida con `backdrop-filter: blur`, borde ice/accent y texto con contraste AA
- **AND** se exhibe la etiqueta visual de rol "Recepción", el enlace "← Volver", el logo claro y el heading accesible "Turnos Odontología"
- **AND** al ingresar credenciales válidas envía `POST /api/auth/login`, guarda el token y redirige a la vista correspondiente

#### Scenario: Parámetro rol inválido o ausente no muestra etiqueta y fallback sólido sin backdrop-filter

- **GIVEN** un usuario en `/login` sin parámetro `?rol` o con un valor inválido como `?rol=desconocido`
- **WHEN** se renderiza la pantalla de login en un navegador sin soporte de `backdrop-filter`
- **THEN** no se renderiza ninguna etiqueta de rol en el formulario
- **AND** la tarjeta del formulario aplica el fallback de fondo sólido navy preservando la legibilidad y contraste AA
- **AND** el formulario permanece 100% funcional y accesible

#### Scenario: Cierre de sesión y preservación del mensaje literal de sesión vencida

- **GIVEN** una sesión que expiró por un 401 en una ruta protegida
- **WHEN** la aplicación redirige a `/login` con `state.expired = true`
- **THEN** se renderiza en un contenedor `role="alert"` el mensaje exacto "La sesión venció. Iniciá sesión de nuevo."
- **AND** el foco inicia en el campo Usuario sin perder la referencia del destino original `state.from`

#### Scenario: Adaptabilidad de /login en 1440, 768 y 390 px

- **GIVEN** la página `/login` en un navegador real
- **WHEN** se evalúa en resoluciones de 1440 px, 768 px y 390 px
- **THEN** la tarjeta translúcida se centra armónicamente, los campos de entrada mantienen el área mínima táctil de 44 px y no hay desbordes horizontales
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)
