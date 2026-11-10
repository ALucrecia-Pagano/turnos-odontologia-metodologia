# frontend-foundation Specification

## Purpose
Base del frontend SPA en `frontend/` con Vite 5, React 18 y TypeScript 5 `strict` (`noUncheckedIndexedAccess`, `verbatimModuleSyntax`), ESLint y Vitest + Testing Library sobre jsdom. Define la estructura `features/shared/pages`, el router mínimo (`/` y `*`), los tokens de diseño y la paleta de los cinco estados del turno (`APPOINTMENT_STATUS_TOKENS`) con contraste AA, los componentes presentacionales (`LoadingState`, `EmptyState`, `ErrorState`, `StatusBadge` y `PageShell`), el cliente HTTP tipado con `fetch` inyectado por parámetro y las cuatro formas de error sin reformular mensajes del dominio, la costura `setAuthProvider` para el token JWT de C-26 y el servicio `frontend` de desarrollo en Docker Compose (puerto `5173`, HMR con polling en Windows y sin recibir secretos del `.env`).

## Requirements

### Requirement: Estructura y tooling del frontend
El frontend MUST vivir en `frontend/` con Vite, React 18 y TypeScript `strict`. La estructura SHALL incluir `src/features`, `src/shared`, `src/pages`, `src/main.tsx` y `src/App.tsx`. `package.json` SHALL declarar `dev`, `build`, `preview`, `test`, `test:run`, `typecheck` (`tsc --noEmit`) y `lint`, con `engines.node >= 20`, ESLint y `package-lock.json` versionado.

#### Scenario: npm run typecheck falla con un tipo inválido
- **GIVEN** el proyecto `frontend/` con TypeScript `strict`
- **WHEN** se asigna un `number` a una prop declarada `string` y se ejecuta `npm run typecheck`
- **THEN** `tsc --noEmit` termina con código de salida distinto de cero
- **AND** el error reporta la asignación de tipo incompatible

#### Scenario: npm run lint detecta una violación
- **GIVEN** el proyecto `frontend/` con ESLint flat config
- **WHEN** se declara una variable sin usar y se ejecuta `npm run lint`
- **THEN** ESLint reporta al menos una violación
- **AND** el comando termina con código de salida distinto de cero

#### Scenario: La estructura de carpetas y los scripts están presentes
- **GIVEN** el proyecto `frontend/` recién instalado
- **WHEN** se listan `src/`, `src/features/`, `src/shared/`, `src/pages/` y se leen los scripts de `package.json`
- **THEN** existen `src/main.tsx` y `src/App.tsx`
- **AND** `package.json` contiene `dev`, `build`, `preview`, `test`, `test:run`, `typecheck` y `lint`

### Requirement: Tokens de diseño y colores por estado
Los estilos MUST usar CSS custom properties y CSS Modules. `tokens.css` SHALL definir espaciado (4–48 px), tipografía (12–32 px), la familia base del sistema como fallback, la paleta Aqua (ink, navy, primary, accent, ice, fondo y texto secundario) y el foco visible. El token de borde es no-texto. `APPOINTMENT_STATUS_TOKENS` SHALL mapear los cinco estados con colores de texto, fondo y borde, con contraste AA >= 4.5:1 en cada par texto/fondo.

#### Scenario: El mapa cubre los cinco estados sin undefined
- **GIVEN** el mapa `APPOINTMENT_STATUS_TOKENS`
- **WHEN** se consultan las claves `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`
- **THEN** las cinco devuelven un objeto con `text`, `background` y `border`
- **AND** ninguna devuelve `undefined`

#### Scenario: Cada par texto y fondo cumple contraste AA
- **GIVEN** los pares de `APPOINTMENT_STATUS_TOKENS`
- **WHEN** se calcula el ratio de contraste de cada par texto/fondo
- **THEN** `reservado` `#1F5F86` sobre `#E4F2F8` es 6.04:1
- **AND** `confirmado` `#146C43` sobre `#DDF3E7` es 5.54:1, `atendido` `#3D4A5C` sobre `#E6EBF1` es 7.51:1, `ausente` `#9A5B00` sobre `#FDF0D5` es 4.81:1 y `cancelado` `#A8242C` sobre `#FBE4E6` es 5.87:1
- **AND** los cinco ratios son al menos 4.5:1

#### Scenario: Los tokens de paleta usados como texto cumplen contraste AA
- **GIVEN** los tokens de la paleta Aqua que se usan como texto
- **WHEN** se calcula el contraste contra su fondo correspondiente
- **THEN** `--color-text` `#011C40` sobre `--color-background` `#F3F7FA` es 15.70:1
- **AND** `--color-text-muted` `#4A5F78` sobre `--color-background` `#F3F7FA` es 6.09:1
- **AND** `--color-primary-contrast` `#FFFFFF` sobre `--color-primary` `#26658C` es 6.32:1
- **AND** `--color-focus` `#26658C` sobre `--color-background` `#F3F7FA` es 5.87:1
- **AND** `--color-accent` `#54ACBF` sobre `--color-background` `#F3F7FA` es 2.43:1 y queda excluido de la exigencia de texto por ser decorativo
- **AND** `--color-navy`, `--color-ice` y `--color-border` quedan excluidos de la exigencia de texto

#### Scenario: El foco es visible
- **GIVEN** un elemento interactivo con la clase de foco del sistema de tokens
- **WHEN** recibe foco por teclado
- **THEN** se aplica un `outline` de 2 px con `--color-focus`
- **AND** el estilo usa el selector `:focus-visible`

#### Scenario: La familia base del sistema se conserva como fallback
- **GIVEN** el archivo `tokens.css` y el `reset.css`
- **WHEN** se inspecciona `--font-family-base`
- **THEN** su valor es el system font stack existente
- **AND** `body` sigue declarando `font-family: var(--font-family-base)` como fallback

### Requirement: StatusBadge
`StatusBadge` MUST ser presentacional y recibir `status`. SHALL renderizar el texto en español del estado y la variante/clase derivada de `APPOINTMENT_STATUS_TOKENS`, sin fetch ni estado propio. MUST usar solo datos ficticios en sus pruebas.

#### Scenario: El estado reservado muestra su variante
- **GIVEN** un `StatusBadge` renderizado con `status="reservado"`
- **WHEN** se consulta el DOM
- **THEN** muestra el texto "Reservado"
- **AND** aplica la variante `reservado`

#### Scenario: El estado confirmado muestra su variante
- **GIVEN** un `StatusBadge` renderizado con `status="confirmado"`
- **WHEN** se consulta el DOM
- **THEN** muestra el texto "Confirmado"
- **AND** aplica la variante `confirmado`

#### Scenario: El estado atendido muestra su variante
- **GIVEN** un `StatusBadge` renderizado con `status="atendido"`
- **WHEN** se consulta el DOM
- **THEN** muestra el texto "Atendido"
- **AND** aplica la variante `atendido`

#### Scenario: El estado ausente muestra su variante
- **GIVEN** un `StatusBadge` renderizado con `status="ausente"`
- **WHEN** se consulta el DOM
- **THEN** muestra el texto "Ausente"
- **AND** aplica la variante `ausente`

#### Scenario: El estado cancelado muestra su variante
- **GIVEN** un `StatusBadge` renderizado con `status="cancelado"`
- **WHEN** se consulta el DOM
- **THEN** muestra el texto "Cancelado"
- **AND** aplica la variante `cancelado`

### Requirement: Estados base de carga, vacío y error
`LoadingState` SHALL exponer `role="status"` con texto de carga; `EmptyState` SHALL recibir título, descripción y acción opcional; `ErrorState` SHALL exponer `role="alert"` con una lista de mensajes y reintento opcional; `PageShell` SHALL envolver header, main y footer. Todos MUST ser presentacionales y no hacer fetch.

#### Scenario: LoadingState renderiza su rol y su texto
- **GIVEN** un `LoadingState` renderizado
- **WHEN** se consulta el DOM
- **THEN** existe un elemento con `role="status"`
- **AND** muestra el texto "Cargando..."

#### Scenario: EmptyState con acción muestra el botón
- **GIVEN** un `EmptyState` con título "No hay turnos", descripción "La agenda de hoy está vacía." y una acción "Crear turno"
- **WHEN** se consulta el DOM
- **THEN** muestra el título y la descripción
- **AND** existe un botón con el texto "Crear turno"

#### Scenario: EmptyState sin acción no muestra botón
- **GIVEN** un `EmptyState` con título "No hay turnos" y descripción "La agenda de hoy está vacía." y sin acción
- **WHEN** se consulta el DOM
- **THEN** muestra el título y la descripción
- **AND** no existe ningún botón

#### Scenario: ErrorState muestra uno y varios mensajes
- **GIVEN** un `ErrorState` con un mensaje "El profesional ya tiene un turno en ese horario." y luego con dos mensajes
- **WHEN** se consulta el DOM
- **THEN** existe un elemento con `role="alert"`
- **AND** se muestran el mensaje único y, con dos mensajes, ambos en la lista

#### Scenario: ErrorState muestra el mensaje de un 409 textual
- **GIVEN** un `ErrorState` con `messages` igual a `["Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1)."]`
- **WHEN** se consulta el DOM
- **THEN** el texto mostrado es exactamente "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1)."
- **AND** no se reformula ni se traduce

### Requirement: Cliente de API y las cuatro formas de error
`client.ts` MUST envolver un `fetch` recibido por parámetro (default el del navegador) sobre la base `VITE_API_URL` y SHALL devolver `{ok:true,...}|{ok:false,...}` sin lanzar por errores HTTP. SHALL modelar `400 {errors}`, `401 {code,message}`, `403/409/422 {violations}`, `404 {code,message}` y `unknown`. `getApiErrorMessages` SHALL devolver los mensajes del dominio tal cual. Los tests MUST usar una función `fetch` real con `new Response(...)`, sin stubs globales.

#### Scenario: Una respuesta 200 devuelve ok con los datos
- **GIVEN** un cliente con la función `fetch` que devuelve `new Response` con status 200 y cuerpo `{ "status": "ok" }`
- **WHEN** se invoca `GET /health`
- **THEN** el resultado tiene `ok` igual a `true` y `status` 200
- **AND** `data` es `{ "status": "ok" }`

#### Scenario: Un 400 con errors se modela como validation
- **GIVEN** un `fetch` que devuelve `new Response` con status 400 y cuerpo `{ "errors": [{ "field": "startAt", "type": "missing", "message": "Falta este dato." }] }`
- **WHEN** se invoca el cliente
- **THEN** el resultado tiene `ok` igual a `false`
- **AND** `error.kind` es `"validation"` y `getApiErrorMessages` devuelve `["Falta este dato."]`

#### Scenario: Un 401 con code y message se modela como auth
- **GIVEN** un `fetch` que devuelve `new Response` con status 401 y cuerpo `{ "code": "INVALID_CREDENTIALS", "message": "Usuario o contraseña incorrectos." }`
- **WHEN** se invoca el cliente
- **THEN** el resultado tiene `ok` igual a `false`
- **AND** `error.kind` es `"auth"` y `getApiErrorMessages` devuelve `["Usuario o contraseña incorrectos."]`

#### Scenario: Un 409 con PROFESSIONAL_OVERLAP conserva el mensaje exacto
- **GIVEN** un `fetch` que devuelve `new Response` con status 409 y cuerpo `{ "violations": [{ "code": "PROFESSIONAL_OVERLAP", "message": "Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1)." }] }`
- **WHEN** se invoca el cliente
- **THEN** `error.kind` es `"conflict"` y `error.status` es 409
- **AND** `getApiErrorMessages` devuelve `["Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (hora local) que se superpone (turno 00000000-0000-0000-0000-0000000000a1)."]`

#### Scenario: Un 404 con code y message se modela como not_found
- **GIVEN** un `fetch` que devuelve `new Response` con status 404 y cuerpo `{ "code": "NOT_FOUND", "message": "Turno no encontrado." }`
- **WHEN** se invoca el cliente
- **THEN** el resultado tiene `ok` igual a `false`
- **AND** `error.kind` es `"not_found"` y `getApiErrorMessages` devuelve `["Turno no encontrado."]`

#### Scenario: Una respuesta desconocida se modela como unknown
- **GIVEN** un `fetch` que devuelve `new Response` con status 500 y cuerpo `"boom"`
- **WHEN** se invoca el cliente
- **THEN** el resultado tiene `ok` igual a `false`
- **AND** `error.kind` es `"unknown"` y conserva el status 500 y el texto crudo

### Requirement: Punto de enganche del token para C-26
El cliente MUST exponer una costura `setAuthProvider({ getToken })` con valor por defecto nulo. Si hay provider, SHALL agregar `Authorization: Bearer <token>`; sin provider MUST NOT enviar el header. C-25 MUST NOT guardar ni leer ningún token: el storage es de C-26 (governance ALTO).

#### Scenario: Sin provider no se envía Authorization
- **GIVEN** un cliente sin `authProvider` configurado
- **WHEN** se invoca una petición con un `fetch` que registra sus headers
- **THEN** la petición no incluye el header `Authorization`

#### Scenario: Con provider se agrega el Bearer
- **GIVEN** un cliente con `setAuthProvider({ getToken: () => "token-ficticio-123" })`
- **WHEN** se invoca una petición con un `fetch` que registra sus headers
- **THEN** la petición incluye `Authorization` con el valor `Bearer token-ficticio-123`

#### Scenario: C-25 no persiste el token
- **GIVEN** el código de `frontend/src` de C-25
- **WHEN** se busca cualquier acceso a `localStorage`, `sessionStorage` o cookies para guardar o leer un token
- **THEN** no existe ningún acceso de ese tipo
- **AND** el token solo se obtiene del `authProvider` cuando está configurado

### Requirement: Servicio frontend en Docker Compose
`frontend/Dockerfile` MUST ser de desarrollo sobre `node:24-alpine` con `npm ci` y `npm run dev -- --host 0.0.0.0`. El servicio `frontend` en `docker-compose.yml` SHALL exponer el puerto `5173`, pasar `VITE_API_URL`, montar el código con `node_modules` anónimo, depender de `backend` y usar polling para HMR en Windows.

#### Scenario: docker compose up levanta el frontend en 5173
- **GIVEN** el repositorio con el servicio `frontend` en `docker-compose.yml`
- **WHEN** se ejecuta `docker compose up` y se abre `http://localhost:5173`
- **THEN** el servicio `frontend` está corriendo
- **AND** el puerto `5173` responde con la aplicación

#### Scenario: Un cambio de archivo se refleja por HMR en Windows
- **GIVEN** el servicio `frontend` corriendo con polling activo en Windows
- **WHEN** se edita un archivo de `frontend/src` montado por volumen
- **THEN** Vite detecta el cambio
- **AND** el navegador refleja la actualización sin reiniciar el contenedor

#### Scenario: VITE_API_URL del navegador apunta a localhost
- **GIVEN** el servicio `frontend` configurado con `VITE_API_URL` desde `.env`
- **WHEN** el navegador del host consume la aplicación
- **THEN** la base de la API es `http://localhost:8000/api`
- **AND** no se usa `http://backend:8000`

#### Scenario: El servicio frontend no recibe secretos
- **GIVEN** el servicio `frontend` de `docker-compose.yml`
- **WHEN** se inspecciona su configuración
- **THEN** no tiene `env_file` con el `.env` completo
- **AND** su entorno no incluye `JWT_SECRET`, `POSTGRES_PASSWORD`, `POSTGRES_USER`, `DATABASE_URL` ni `SEED_USER_PASSWORD`
- **AND** recibe solo `VITE_API_URL` y `CHOKIDAR_USEPOLLING`

### Requirement: Tipografías autoalojadas sin CDN
La aplicación SHALL cargar Jost para títulos y Manrope para texto desde paquetes npm `@fontsource-variable` importados en el entry point del frontend. MUST NOT cargar fuentes desde un CDN, desde Google Fonts ni mediante un `<link>` remoto. Las familias MUST aplicarse a través de tokens semánticos con fallback al system font stack.

#### Scenario: Las dependencias y los imports de fuentes están en el frontend
- **GIVEN** `frontend/package.json` y `frontend/src/main.tsx`
- **WHEN** se inspeccionan las dependencias y los imports del entry point
- **THEN** `@fontsource-variable/jost` y `@fontsource-variable/manrope` figuran en `dependencies`
- **AND** `main.tsx` importa ambos paquetes antes de los estilos de la aplicación

#### Scenario: No hay fuentes externas ni CDN
- **GIVEN** el código y los estilos de `frontend/src`
- **WHEN** se busca cualquier URL de fuentes externa
- **THEN** no aparece `fonts.googleapis.com`, `fonts.gstatic.com` ni ninguna URL de CDN de fuentes
- **AND** las tipografías se sirven desde los archivos empaquetados por Vite

#### Scenario: Las familias se aplican con tokens y fallback
- **GIVEN** `tokens.css` y `reset.css`
- **WHEN** se renderiza una pantalla
- **THEN** `--font-family-heading` usa `"Jost Variable"` y `--font-family-body` usa `"Manrope Variable"`
- **AND** ambos tokens incluyen el system font stack como fallback
- **AND** los títulos usan `var(--font-family-heading)` y el texto usa `var(--font-family-body)`

### Requirement: Barra única con la marca Aqua
La aplicación SHALL mostrar una única barra con el isotipo oscuro de Aqua (`frontend/src/assets/brand/isotipo-aqua.png`, `alt=""`), "Aqua" y "Clínica Odontológica" (no `logo-aqua-oscuro.png` para no duplicar texto). En tablet (<= 768 px), renglón 1 SHALL mostrar marca, usuario y "Cerrar sesión", y renglón 2 la navegación en una fila con scroll horizontal (máximo dos renglones). El título de PageShell MUST NOT crear una segunda barra.

#### Scenario: Barra de escritorio con la marca completa
- **GIVEN** una sesión autenticada en escritorio (1440 px)
- **WHEN** se renderiza el shell de la aplicación
- **THEN** existe una sola barra de encabezado
- **AND** la barra muestra el logo, "Aqua" y "Clínica Odontológica"

#### Scenario: Barra de tablet con solo Aqua y máximo dos renglones
- **GIVEN** un viewport de 768 px con una sesión autenticada
- **WHEN** se renderiza el shell de la aplicación
- **THEN** la barra muestra el logo y el texto "Aqua"
- **AND** "Clínica Odontológica" no se muestra
- **AND** a <= 768 px, renglón 1 muestra marca + usuario y "Cerrar sesión"
- **AND** renglón 2 muestra la navegación en una sola fila con scroll horizontal
- **AND** la barra ocupa como máximo dos renglones
- **AND** esta verificación es visual (captura a 768 px), no un test de Vitest

#### Scenario: La barra usa el isotipo oscuro
- **GIVEN** la barra de encabezado sobre fondo claro
- **WHEN** se inspecciona la imagen del logo
- **THEN** se usa `frontend/src/assets/brand/isotipo-aqua.png`
- **AND** el isotipo tiene `alt=""` porque el texto "Aqua" está al lado
- **AND** no se usa `logo-aqua-oscuro.png` ni la variante clara en la barra

#### Scenario: El título de página no se ve como una segunda barra
- **GIVEN** una página envuelta en PageShell
- **WHEN** se renderiza el título de la página
- **THEN** el título del PageShell se muestra sin fondo ni borde propios
- **AND** esta verificación es visual, no un test de Vitest

### Requirement: Créditos de assets y tipografías
El `README.md` SHALL incluir una sección de créditos que nombre las cinco fotografías del login, el logo de Aqua y la licencia de las tipografías Jost y Manrope distribuidas por Fontsource.

#### Scenario: El README acredita fotos, logo y tipografías
- **GIVEN** el `README.md` del repositorio
- **WHEN** se busca la sección de créditos
- **THEN** la sección nombra las cinco fotografías y el logo de Aqua
- **AND** indica que Jost y Manrope se distribuyen con licencia SIL Open Font License mediante Fontsource
