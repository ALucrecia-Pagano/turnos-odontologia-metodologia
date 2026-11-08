# frontend-agenda Specification

## Purpose
Agenda diaria de solo lectura sobre `GET /api/agenda` en el frontend SPA (`frontend/`): ruta protegida `/agenda` para los tres roles y redirección con `replace` desde `/` según el `Clock` inyectado; carga inyectable de turnos, profesionales y sillones sin reloj global; eje de horas y posicionamiento por minutos en hora local usando el `timezone` de la respuesta; bandas de horarios de atención y bloqueos rayados; tarjetas de turnos con color por estado y texto accesible, con cancelados atenuados pero visibles; filtros combinables por profesional y sillón reflejados en la URL; navegación por días con `Anterior`, `Siguiente`, `Hoy` y selector de fecha; estados de carga, vacío y error con reintento; delegación del `401` en C-26 y `403` visible sin cerrar sesión; vista alternativa en tabla semántica accesible y diseño responsive con scroll horizontal para escritorio y tablet.

## Requirements

### Requirement: Ruta /agenda y pantalla principal

La aplicación SHALL exponer la ruta protegida `/agenda` para los tres roles. La ruta `/` MUST redirigir con `replace` a `/agenda` con la fecha de hoy según el `Clock` inyectado. El menú MUST mostrar `Agenda` habilitada y MUST mantener el resto de los ítems futuros deshabilitados con `"Próximamente"`.

#### Scenario: / redirige a /agenda

- **GIVEN** una sesión autenticada y un `Clock` fijo en `2026-11-16T12:00:00Z`
- **WHEN** se navega a `/`
- **THEN** se redirige con `replace` a `/agenda?date=2026-11-16`
- **AND** no se renderiza `HomePage`

#### Scenario: Agenda habilitada en el menú de los tres roles

- **GIVEN** sesiones de `administrador`, `recepcion` y `odontologo`
- **WHEN** se renderiza el menú
- **THEN** `Agenda` es un enlace habilitado en los tres roles
- **AND** el resto de los ítems futuros sigue deshabilitado con `"Próximamente"`

### Requirement: Carga con fetch y Clock inyectados

Al abrir `/agenda`, la vista SHALL pedir la agenda del día seleccionado y MUST cargar profesionales y sillones con el `fetch` inyectado. La fecha inicial y la acción `Hoy` MUST calcularse con el `Clock` inyectado; la vista MUST NOT usar el reloj global del componente.

#### Scenario: Carga con fetch y Clock inyectados

- **GIVEN** un `Clock` fijo en `2026-11-16T12:00:00Z` y una URL sin `date`
- **AND** un `fetch` inyectado que responde la agenda del lunes con Quiroga y Sosa, el catálogo de profesionales y el de sillones
- **WHEN** se monta `/agenda`
- **THEN** se piden `GET /api/agenda?from=2026-11-16&to=2026-11-16`, `GET /api/professionals` y `GET /api/chairs`
- **AND** se muestran las columnas de Quiroga y Sosa

#### Scenario: La fecha inicial respeta el borde de medianoche

- **GIVEN** un `Clock` fijo en `2026-11-16T02:30:00Z` y la zona de respaldo `America/Argentina/Buenos_Aires`
- **WHEN** se monta `/agenda` sin `date`
- **THEN** la request usa `from=2026-11-15` y `to=2026-11-15`

### Requirement: Conversión a hora local con el timezone de la respuesta

La agenda MUST pedir `from`/`to` como fechas locales `YYYY-MM-DD` sin convertirlas a UTC. Toda hora y fecha visible MUST formatearse con el `timezone` de la respuesta de `GET /api/agenda`, nunca con la zona del navegador o del proceso. El único valor de respaldo MUST vivir en un archivo de configuración y usarse solo antes de la primera respuesta.

#### Scenario: 13:00Z se muestra como 10:00 en Buenos Aires

- **GIVEN** la respuesta de `GET /api/agenda` con `timezone` `"America/Argentina/Buenos_Aires"` y el turno de Quiroga `startAt` `2026-11-16T13:00:00Z` y `endAt` `2026-11-16T13:30:00Z`
- **WHEN** se renderiza la agenda del `2026-11-16`
- **THEN** la tarjeta muestra `10:00–10:30`
- **AND** la etiqueta del día es `lunes 16 de noviembre de 2026`

#### Scenario: El resultado es independiente de la zona del proceso

- **GIVEN** el mismo turno `2026-11-16T13:00:00Z` y la misma respuesta con `timezone` `America/Argentina/Buenos_Aires`
- **WHEN** el proceso de tests corre con `TZ=Asia/Tokyo` o formatea con una zona distinta
- **THEN** la hora mostrada sigue siendo `10:00` y la fecha `2026-11-16`

#### Scenario: Las fechas de la request son locales

- **GIVEN** la fecha `2026-11-16` en la URL
- **WHEN** se pide la agenda
- **THEN** la request usa `from=2026-11-16` y `to=2026-11-16` sin zona ni sufijo `Z`

### Requirement: Eje de horas

La grilla SHALL dibujar un eje de horas que cubra la unión de `workingHours`, `blocks` y turnos del día, clampeada a `[0, 1440]`, redondeada a la hora y con una hora de margen. Sin datos MUST usar `08:00–20:00`; un rango menor a 4 horas MUST expandirse a 4.

#### Scenario: Eje del lunes con datos

- **GIVEN** el día `2026-11-16` con horarios de Quiroga `09:00–13:00` y `15:00–19:00`, el bloqueo `12:00–13:00` y los turnos de Quiroga y Sosa
- **WHEN** se calcula y dibuja el eje
- **THEN** el eje va de `08:00` a `20:00`
- **AND** las horas se muestran una por línea

#### Scenario: Eje de un día vacío

- **GIVEN** el domingo `2026-11-15` sin horarios, bloqueos ni turnos
- **WHEN** se dibuja el eje
- **THEN** el eje va de `08:00` a `20:00`

### Requirement: Columnas por profesional

Cada columna MUST corresponder a un profesional del catálogo, incluidos los inactivos marcados `(inactivo)`, y MUST ordenarse de forma alfabética estable por nombre. Un profesional sin turnos MUST conservar su columna vacía. Con un `professionalId` en la URL MUST mostrarse solo esa columna.

#### Scenario: Tres columnas en orden estable

- **GIVEN** el catálogo con `Dra. Laura Quiroga`, `Dr. Martín Sosa` y `Dra. Paula Benítez` en cualquier orden
- **WHEN** se renderiza la agenda del `2026-11-16`
- **THEN** aparecen las tres columnas con esos nombres en orden alfabético
- **AND** el mismo catálogo en otro orden produce el mismo orden de columnas

#### Scenario: Profesional inactivo visible

- **GIVEN** el catálogo con `Dra. Paula Benítez` y `active: false`
- **WHEN** se renderiza la agenda
- **THEN** la columna muestra `Dra. Paula Benítez (inactivo)`

#### Scenario: Filtro por profesional deja una sola columna

- **GIVEN** la URL `/agenda?date=2026-11-16&professionalId=00000000-0000-0000-0000-000000000001`
- **WHEN** se renderiza la agenda
- **THEN** la única columna es `Dra. Laura Quiroga`

### Requirement: Posición, alto y carriles de turnos superpuestos

Cada turno MUST posicionarse por sus minutos locales de inicio y fin, clampeados al día, con alto proporcional a su duración y un alto mínimo legible. Los turnos superpuestos MUST repartirse en carriles lado a lado, y un cancelado MUST poder compartir horario con un activo sin taparlo.

#### Scenario: Posición y alto del turno de Quiroga

- **GIVEN** el eje `08:00–20:00` y el turno de Quiroga de `13:00Z` a `13:30Z` (10:00–10:30 local)
- **WHEN** se posiciona la tarjeta
- **THEN** la tarjeta ocupa de `10:00` a `10:30`, es decir 120 minutos desde el inicio del eje y 30 minutos de alto

#### Scenario: Carriles para un cancelado y un activo superpuestos

- **GIVEN** un turno cancelado de Sosa y un turno activo de Sosa, ambos de `09:00` a `09:30` del `2026-11-16`
- **WHEN** se asignan los carriles
- **THEN** ambos turnos se ven lado a lado en dos carriles
- **AND** ninguno tapa al otro

#### Scenario: Turno de cinco minutos con alto mínimo

- **GIVEN** un turno de `09:00` a `09:05`
- **WHEN** se posiciona
- **THEN** la tarjeta conserva un alto mínimo legible y su nombre accesible incluye `09:00–09:05`

### Requirement: Horarios de atención, bloqueos y cancelados

Los horarios de atención MUST dibujarse como bandas de fondo por profesional y día de la semana. Los bloqueos MUST dibujarse como bandas con motivo y etiqueta accesible. Los turnos cancelados MUST permanecer visibles, atenuados y con la palabra `Cancelado`, sin reducir el contraste del texto.

#### Scenario: Horarios y bloqueo del lunes

- **GIVEN** los horarios de Quiroga `09:00–13:00` y `15:00–19:00` y el bloqueo `12:00–13:00` con motivo `Congreso`
- **WHEN** se renderiza la columna de Quiroga
- **THEN** se ven las bandas de horario y la banda rayada del bloqueo
- **AND** el bloqueo expone `Bloqueo: Congreso, de 12:00 a 13:00`

#### Scenario: El cancelado permanece visible

- **GIVEN** el turno cancelado de Sosa de `09:00` a `09:30`
- **WHEN** se renderiza la columna de Sosa
- **THEN** el turno se ve atenuado con el texto `Cancelado`
- **AND** no se oculta de la grilla

### Requirement: Color por estado más texto

El estado de cada turno MUST comunicarse con texto visible y MUST usar la paleta AA de estados; MUST NOT depender solo del color. La tarjeta MUST exponer un nombre accesible con hora, paciente, profesional, sillón, prestación y estado.

#### Scenario: Reservado y cancelado se distinguen por texto

- **GIVEN** el turno reservado de Quiroga y el cancelado de Sosa del `2026-11-16`
- **WHEN** se renderizan las tarjetas
- **THEN** una muestra `Reservado` y la otra `Cancelado`
- **AND** ambas usan el color AA de su estado sin depender solo del color

#### Scenario: Nombre accesible completo

- **GIVEN** el turno de Quiroga de `10:00` a `10:30` con Ana Pérez en Sillón 1 y `Control`
- **WHEN** se consulta la tarjeta
- **THEN** su nombre accesible incluye `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control` y `Reservado`

### Requirement: Filtros por profesional y sillón con estado en la URL

Los filtros de profesional y sillón MUST ser combinables y MUST vivir en la URL. `professionalId` MUST filtrar turnos, horarios y bloqueos; `chairId` MUST filtrar solo turnos y MUST mostrar una ayuda visible que aclare que horarios y bloqueos siguen visibles. `Limpiar filtros` MUST volver a `Todos` conservando la fecha.

#### Scenario: El filtro por sillón conserva horarios y bloqueos

- **GIVEN** la agenda del `2026-11-16` y el filtro `chairId` del Sillón 2
- **WHEN** se aplica el filtro
- **THEN** la URL incluye `chairId=00000000-0000-0000-0000-0000000000b2`
- **AND** solo se muestra el turno de Sosa del Sillón 2
- **AND** el bloqueo `Congreso` de Quiroga y los horarios de atención siguen visibles
- **AND** se muestra la ayuda del filtro por sillón

#### Scenario: El filtro por profesional filtra las tres colecciones

- **GIVEN** la agenda del `2026-11-16` y el filtro `professionalId` de Quiroga
- **WHEN** se aplica el filtro
- **THEN** la URL incluye `professionalId=00000000-0000-0000-0000-000000000001`
- **AND** se muestra solo la columna de Quiroga con sus turnos, horarios y bloqueos

#### Scenario: Filtros combinados sin turnos

- **GIVEN** los filtros Quiroga y Sillón 2
- **WHEN** se combinan
- **THEN** no se muestra ningún turno
- **AND** se mantienen las bandas y se muestra `Sin turnos para este filtro`

### Requirement: Navegación anterior, siguiente, Hoy y selector

La barra de navegación MUST ofrecer `Anterior`, `Siguiente`, `Hoy` y un selector de fecha. Cada cambio MUST actualizar `date` en la URL con `push` y MUST pedir ese día. `Anterior` y `Siguiente` MUST sumar o restar un día calendario, no 24 horas.

#### Scenario: Anterior y siguiente

- **GIVEN** la URL `/agenda?date=2026-11-16`
- **WHEN** se activa `Anterior`
- **THEN** la URL pasa a `/agenda?date=2026-11-15` con `push` y se pide ese día
- **AND** al activar `Siguiente` desde esa fecha la URL vuelve a `2026-11-16`

#### Scenario: Hoy y selector de fecha

- **GIVEN** un `Clock` fijo en `2026-11-16T12:00:00Z` y la URL `/agenda?date=2026-11-10`
- **WHEN** se activa `Hoy`
- **THEN** la URL pasa a `/agenda?date=2026-11-16`
- **AND** al elegir `2026-12-01` en el selector la URL pasa a `/agenda?date=2026-12-01`

### Requirement: Estados de carga, vacío y error

La vista MUST mostrar un estado de carga con `role="status"`, MUST conservar la grilla con un aviso cuando el día no tiene turnos y MUST mostrar un `ErrorState` con `Reintentar` ante error de red o `5xx`. La actualización MUST ser manual, sin polling.

#### Scenario: Carga inicial

- **GIVEN** `/agenda` montada y las requests pendientes
- **WHEN** se renderiza
- **THEN** se muestra un elemento `role="status"` con `Cargando...`
- **AND** no se muestra un error

#### Scenario: Día sin turnos

- **GIVEN** la agenda del `2026-11-16` con `appointments` vacío y horarios de atención
- **WHEN** termina la carga
- **THEN** se ve la grilla con `No hay turnos para este día`
- **AND** las bandas de horario siguen visibles

#### Scenario: Error de red con reintento

- **GIVEN** que `GET /api/agenda` falla por red
- **WHEN** termina la carga
- **THEN** se muestra un `ErrorState` con `Reintentar`
- **AND** al reintentar y recibir `200` se renderiza la agenda

### Requirement: 401 delegado en C-26 y 403 visible

Un `401` de una request de agenda MUST delegarse en C-26: MUST limpiar la sesión y redirigir a `/login` con `La sesión venció. Iniciá sesión de nuevo.`, y la vista MUST NOT mostrar un error local. Un `403` MUST mostrar los mensajes de `violations` y MUST NOT cerrar la sesión.

#### Scenario: 401 durante el uso

- **GIVEN** una sesión autenticada y `GET /api/agenda` responde `401` con `{ "code": "INVALID_TOKEN", "message": "La sesión venció o no es válida. Inicie sesión de nuevo." }`
- **WHEN** termina la request
- **THEN** el token se descarta y se redirige a `/login` con `La sesión venció. Iniciá sesión de nuevo.`
- **AND** la agenda no muestra un error local

#### Scenario: 403 con la violación visible

- **GIVEN** una sesión autenticada y `GET /api/agenda` responde `403` con `{ "violations": [{ "code": "FORBIDDEN_OPERATION", "message": "No tiene permiso para leer la agenda." }] }`
- **WHEN** termina la request
- **THEN** se muestra exactamente `No tiene permiso para leer la agenda.`
- **AND** la sesión sigue autenticada y no se redirige

### Requirement: Vista en lista accesible

La vista MUST ofrecer un toggle visible `Ver como lista` que MUST renderizar una tabla semántica con `caption` y encabezados `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado`, con los mismos datos y orden que la grilla. La grilla MUST exponer nombres accesibles y anunciar la cantidad de turnos con `aria-live`.

#### Scenario: Tabla accesible del lunes

- **GIVEN** la agenda del `2026-11-16` con los turnos de Quiroga y Sosa
- **WHEN** se activa `Ver como lista`
- **THEN** la tabla tiene el caption `Turnos del lunes 16 de noviembre de 2026`
- **AND** los encabezados son `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado`
- **AND** la fila de Quiroga es `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control`, `Reservado`

#### Scenario: Anuncio de la cantidad de turnos

- **GIVEN** la agenda del `2026-11-16` con dos turnos
- **WHEN** termina la carga
- **THEN** la región `aria-live` anuncia `Turnos del lunes 16 de noviembre de 2026: 2`

### Requirement: Responsive para escritorio y tablet

La vista MUST ser usable en escritorio y tablet: con varias columnas MUST permitir scroll horizontal, MUST mantener fijos el encabezado de profesionales y la columna de horas, y MUST ofrecer controles de al menos 44×44 px sin información exclusiva de `hover`.

#### Scenario: Tablet de 768 por 1024

- **GIVEN** un viewport de `768×1024` con tres columnas
- **WHEN** se renderiza la agenda
- **THEN** la barra de herramientas se acomoda en varias líneas
- **AND** la grilla permite scroll horizontal con el encabezado de profesionales y la columna de horas fijos
- **AND** los controles miden al menos `44×44` px y no dependen de `hover`
