# frontend-catalogs-and-patients Specification

## Purpose
Pantallas web para consultar y mantener pacientes (`/pacientes`) y los catálogos de profesionales, sillones y prestaciones (`/catalogos`), con los permisos por rol del backend, sus mensajes de error literales, sin datos clínicos y adaptables a 1440, 768 y 390 px.

## Requirements

### Requirement: Listado de pacientes

La ruta `/pacientes` SHALL mostrar, para los tres roles, una tabla con nombre, DNI, teléfono y obra social de los pacientes que devuelve `GET /api/patients`. Un teléfono u obra social `null` MUST mostrarse como el texto "Sin dato". Si la carga falla, la pantalla MUST mostrar un error con el botón "Reintentar", que vuelve a pedir la lista.

#### Scenario: Listado de pacientes con sus cuatro datos

- **Dado (GIVEN)** un usuario con rol `recepcion` y la API con los pacientes ficticios "Ana Pérez" (DNI `30111222`, teléfono `11-4444-5555`, obra social `OSDE`) y "Bruno Acosta" (DNI `28444555`, sin teléfono ni obra social)
- **Cuando (WHEN)** navega a `/pacientes`
- **Entonces (THEN)** ve una tabla con las columnas "Nombre", "DNI", "Teléfono" y "Obra social"
- **Y** la fila de "Ana Pérez" muestra `30111222`, `11-4444-5555` y `OSDE`
- **Y** la fila de "Bruno Acosta" muestra "Sin dato" en teléfono y en obra social

#### Scenario: Error de carga de pacientes con reintento

- **Dado (GIVEN)** un usuario con rol `recepcion` y una API que responde `500` a la primera llamada a `GET /api/patients` y la lista a la segunda
- **Cuando (WHEN)** navega a `/pacientes` y pulsa "Reintentar"
- **Entonces (THEN)** primero ve un error en `role="alert"` con el botón "Reintentar"
- **Y** después del reintento se hizo una segunda llamada a `GET /api/patients` y ve la tabla de pacientes

### Requirement: Búsqueda de pacientes en la pantalla

La pantalla de pacientes SHALL tener un campo con etiqueta visible "Buscar por nombre o DNI" y un botón "Buscar". Al enviar, MUST pedir `GET /api/patients?query=<texto codificado>` y reemplazar la tabla por el resultado. Si el resultado está vacío, MUST mostrar "No se encontraron pacientes." sin filas anteriores.

#### Scenario: Búsqueda envía la consulta codificada y muestra el resultado

- **Dado (GIVEN)** un usuario con rol `recepcion` en `/pacientes` con la lista completa cargada
- **Cuando (WHEN)** escribe "Ana Pérez" en "Buscar por nombre o DNI" y pulsa "Buscar"
- **Entonces (THEN)** se pide `GET /api/patients?query=Ana%20P%C3%A9rez`
- **Y** la tabla muestra solo la fila de "Ana Pérez" que devolvió la API

#### Scenario: Búsqueda sin resultados

- **Dado (GIVEN)** un usuario con rol `recepcion` en `/pacientes` con la fila de "Ana Pérez" visible
- **Cuando (WHEN)** busca "zzz" y la API responde `[]`
- **Entonces (THEN)** se muestra "No se encontraron pacientes."
- **Y** ya no se muestra ninguna fila de paciente

### Requirement: Catálogos por sección

La ruta `/catalogos` SHALL mostrar una sección por vez, elegida con `?seccion=profesionales|sillones|prestaciones` mediante enlaces "Profesionales", "Sillones" y "Prestaciones" con `aria-current="page"` en el activo. Sin sección o con una desconocida MUST mostrar profesionales. Cada tabla MUST listar activos e inactivos con el estado como texto "Activo" o "Inactivo".

#### Scenario: Profesionales por defecto con estado en texto

- **Dado (GIVEN)** un usuario con rol `administrador` y la API con un profesional activo "Dra. Laura Quiroga" (matrícula `MN 1234`) y uno inactivo "Dr. Pablo Ferreyra" (sin matrícula)
- **Cuando (WHEN)** navega a `/catalogos` y luego a `/catalogos?seccion=desconocida`
- **Entonces (THEN)** en ambos casos se pide `GET /api/professionals` sin el parámetro `active` y el enlace "Profesionales" tiene `aria-current="page"`
- **Y** la tabla tiene las columnas "Nombre", "Matrícula" y "Estado"
- **Y** "Dra. Laura Quiroga" muestra "Activo" y "Dr. Pablo Ferreyra" muestra "Sin dato" en matrícula e "Inactivo" en estado

#### Scenario: Cambio a la sección de prestaciones

- **Dado (GIVEN)** un usuario con rol `administrador` en `/catalogos`
- **Cuando (WHEN)** pulsa el enlace "Prestaciones"
- **Entonces (THEN)** la URL pasa a `/catalogos?seccion=prestaciones` y se pide `GET /api/services`
- **Y** la tabla tiene las columnas "Nombre", "Duración (min)" y "Estado" y la fila "Limpieza" muestra `45`
- **Y** el enlace "Prestaciones" tiene `aria-current="page"`

### Requirement: Título de pantalla con un solo h1

Las pantallas de pacientes y catálogos SHALL pasar a `PageShell` el título de la pantalla ("Pacientes" y "Catálogos") y MUST tener exactamente un elemento `<h1>` con ese mismo texto.

#### Scenario: Pacientes y Catálogos con su título y un único h1

- **Dado (GIVEN)** un usuario autenticado con rol `administrador`
- **Cuando (WHEN)** navega a `/pacientes` y, en otro render, a `/catalogos`
- **Entonces (THEN)** el encabezado de `PageShell` muestra "Pacientes" y "Catálogos" respectivamente
- **Y** cada pantalla tiene un único `<h1>`, con el texto "Pacientes" y "Catálogos" respectivamente

### Requirement: Alta y edición de pacientes sin datos clínicos

Administración y recepción SHALL dar de alta con "Nuevo paciente" y editar con "Editar" en un `Dialog` con exactamente cuatro campos: nombre, DNI, teléfono y obra social (texto libre). Teléfono u obra social vacíos MUST enviarse como `null`. Tras guardar, el diálogo MUST cerrarse y la lista refrescarse. La pantalla MUST NOT ofrecer desactivar ni borrar pacientes.

#### Scenario: Alta de paciente

- **Dado (GIVEN)** un usuario con rol `recepcion` en `/pacientes`
- **Cuando (WHEN)** pulsa "Nuevo paciente", completa nombre "Carla Medina" y DNI "27.123.456", deja teléfono y obra social vacíos y pulsa "Guardar"
- **Entonces (THEN)** se envía `POST /api/patients` con `{"fullName": "Carla Medina", "dni": "27.123.456", "phone": null, "healthInsurance": null}`
- **Y** el diálogo se cierra, se vuelve a pedir `GET /api/patients` y se anuncia "Paciente creado." en `role="status"`

#### Scenario: El formulario de paciente tiene solo los cuatro datos mínimos

- **Dado (GIVEN)** un usuario con rol `administrador` en `/pacientes`
- **Cuando (WHEN)** abre "Nuevo paciente"
- **Entonces (THEN)** el formulario tiene exactamente cuatro campos editables, con las etiquetas "Nombre y apellido", "DNI", "Teléfono" y "Obra social"
- **Y** ni el diálogo ni las filas de la tabla ofrecen acciones "Desactivar", "Reactivar" ni "Eliminar"

#### Scenario: Edición de paciente con valores precargados

- **Dado (GIVEN)** un usuario con rol `recepcion` en `/pacientes` con la fila de "Ana Pérez" (DNI `30111222`, teléfono `11-4444-5555`, obra social `OSDE`)
- **Cuando (WHEN)** pulsa "Editar" en esa fila
- **Entonces (THEN)** el diálogo "Editar paciente" muestra los cuatro valores actuales
- **Y** al cambiar el teléfono a "11-1234-5678" y pulsar "Guardar" se envía `PUT /api/patients/{id}` con `{"fullName": "Ana Pérez", "dni": "30111222", "phone": "11-1234-5678", "healthInsurance": "OSDE"}` y se anuncia "Paciente actualizado." en `role="status"`

### Requirement: Errores del backend en los formularios

Ante un 409 o 422, el diálogo SHALL seguir abierto con lo tipeado y MUST mostrar cada `message` del backend, sin reformular, en un contenedor `role="alert"` que recibe el foco; un 409 MUST NOT marcar campos con `aria-invalid`. Ante un 400 con `field`, el campo indicado MUST tener `aria-invalid="true"` y su mensaje asociado.

#### Scenario: DNI duplicado muestra el mensaje literal del backend

- **Dado (GIVEN)** un usuario con rol `recepcion` con el diálogo "Nuevo paciente" con DNI "30111222"
- **Cuando (WHEN)** pulsa "Guardar" y la API responde `409` con la violación `DUPLICATE_DNI` y el mensaje "Ya existe un paciente con el DNI 30.111.222."
- **Entonces (THEN)** el diálogo sigue abierto con los datos tipeados y un `role="alert"` con foco muestra exactamente "Ya existe un paciente con el DNI 30.111.222."
- **Y** el campo "DNI" no tiene `aria-invalid`

#### Scenario: DNI inválido muestra el mensaje literal del backend (422 INVALID_DNI)

- **Dado (GIVEN)** un usuario con rol `recepcion` con el diálogo "Nuevo paciente" con nombre "Diego Ríos" y DNI "1234"
- **Cuando (WHEN)** pulsa "Guardar" y la API responde `422` con la violación `INVALID_DNI` y el mensaje `El DNI no es válido (se recibió "1234"): debe tener 7 u 8 dígitos, con o sin puntos.`
- **Entonces (THEN)** el diálogo sigue abierto con los datos tipeados y un `role="alert"` con foco muestra exactamente ese mensaje
- **Y** se envió exactamente un `POST /api/patients` con `"dni": "1234"`, porque el cliente no valida el DNI

#### Scenario: Error 400 por campo marca el campo con aria-invalid

- **Dado (GIVEN)** un usuario con rol `recepcion` con el diálogo "Nuevo paciente" abierto
- **Cuando (WHEN)** pulsa "Guardar" y la API responde `400` con `{"errors": [{"field": "fullName", "type": "missing", "message": "Falta este dato."}]}`
- **Entonces (THEN)** el campo "Nombre y apellido" tiene `aria-invalid="true"`
- **Y** el texto "Falta este dato." está asociado al campo con `aria-describedby`

#### Scenario: Duración inválida muestra el mensaje literal del backend

- **Dado (GIVEN)** un usuario con rol `administrador` con el diálogo "Nueva prestación" con nombre "Control" y duración "7"
- **Cuando (WHEN)** pulsa "Guardar" y la API responde `422` con la violación `INVALID_DURATION` y el mensaje "La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos."
- **Entonces (THEN)** el diálogo sigue abierto y un `role="alert"` con foco muestra exactamente ese mensaje

#### Scenario: Nombre duplicado en el catálogo genérico muestra el mensaje literal del backend (409 DUPLICATE_NAME)

- **Dado (GIVEN)** un usuario con rol `administrador` con el diálogo "Nueva prestación" del componente genérico de catálogo, con nombre "Limpieza" y duración "45"
- **Cuando (WHEN)** pulsa "Guardar" y la API responde `409` con la violación `DUPLICATE_NAME` y el mensaje `Ya existe una prestación con el nombre "Limpieza".`
- **Entonces (THEN)** el diálogo sigue abierto con los datos tipeados y un `role="alert"` con foco muestra exactamente ese mensaje
- **Y** el campo "Nombre" no tiene `aria-invalid`

### Requirement: Acciones visibles según el rol

La UI SHALL mostrar solo las acciones que el RBAC del backend permite al rol. Catálogos: solo `administrador` ve "Nuevo …", "Editar", "Desactivar" y "Reactivar"; `recepcion` y `odontologo` ven las tablas y el texto "Solo lectura". Pacientes: `administrador` y `recepcion` ven "Nuevo paciente" y "Editar"; `odontologo` ve la lista y la búsqueda sin esas acciones.

#### Scenario: Odontólogo consulta pacientes en solo lectura

- **Dado (GIVEN)** un usuario con rol `odontologo`
- **Cuando (WHEN)** navega a `/pacientes`
- **Entonces (THEN)** ve la tabla de pacientes y el buscador
- **Y** no hay botones "Nuevo paciente" ni "Editar"

#### Scenario: Recepción y odontólogo consultan catálogos en solo lectura

- **Dado (GIVEN)** un usuario con rol `recepcion` y, en otro render, uno con rol `odontologo`
- **Cuando (WHEN)** navegan a `/catalogos?seccion=sillones`
- **Entonces (THEN)** ven la tabla de sillones y el texto "Solo lectura"
- **Y** no hay botones "Nuevo sillón", "Editar", "Desactivar" ni "Reactivar"

### Requirement: Un solo mensaje de estado vigente

Cada pantalla SHALL tener una sola región `role="status"`, montada todo el tiempo, para anunciar el resultado de las acciones. Al empezar una acción nueva, el mensaje anterior MUST borrarse o reemplazarse; nunca coexisten dos mensajes de estado.

#### Scenario: El mensaje de estado se reemplaza entre acciones sin desmontar la región

- **Dado (GIVEN)** un usuario con rol `recepcion` en `/pacientes` que acaba de crear un paciente y ve "Paciente creado." en `role="status"`
- **Cuando (WHEN)** abre "Editar" en otra fila, cambia el teléfono y guarda
- **Entonces (THEN)** la misma región `role="status"` sigue montada y muestra solo "Paciente actualizado."
- **Y** el texto "Paciente creado." ya no aparece en la pantalla

### Requirement: Alta y edición de catálogos

El administrador SHALL crear con "Nuevo profesional", "Nuevo sillón" o "Nueva prestación" y editar con "Editar" en un `Dialog`: profesional (nombre y matrícula opcional), sillón (nombre), prestación (nombre y duración en minutos). La duración MUST enviarse como número entero; si no lo es, no se envía y se muestra "La duración debe ser un número entero de minutos.". Una matrícula vacía MUST enviarse como `null`.

#### Scenario: Alta de prestación con duración numérica

- **Dado (GIVEN)** un usuario con rol `administrador` en `/catalogos?seccion=prestaciones`
- **Cuando (WHEN)** pulsa "Nueva prestación", completa nombre "Extracción" y duración "30" y pulsa "Guardar"
- **Entonces (THEN)** se envía `POST /api/services` con `{"name": "Extracción", "defaultDurationMin": 30}`, con `30` como número
- **Y** el diálogo se cierra, se vuelve a pedir `GET /api/services` y se anuncia "Prestación creada." en `role="status"`

#### Scenario: Duración no entera no se envía

- **Dado (GIVEN)** un usuario con rol `administrador` con el diálogo "Nueva prestación" con nombre "Control"
- **Cuando (WHEN)** deja la duración vacía, pulsa "Guardar", luego escribe "abc" y vuelve a pulsar "Guardar"
- **Entonces (THEN)** no se envía ninguna petición `POST /api/services`
- **Y** el campo "Duración (min)" tiene `aria-invalid="true"` y muestra "La duración debe ser un número entero de minutos."

#### Scenario: Edición de profesional con matrícula vacía

- **Dado (GIVEN)** un usuario con rol `administrador` en `/catalogos` con el profesional "Dra. Laura Quiroga" (matrícula `MN 1234`)
- **Cuando (WHEN)** pulsa "Editar" en esa fila, borra la matrícula y pulsa "Guardar"
- **Entonces (THEN)** se envía `PUT /api/professionals/{id}` con `{"fullName": "Dra. Laura Quiroga", "licenseNumber": null}`
- **Y** se anuncia "Profesional actualizado." en `role="status"`

### Requirement: Desactivar y reactivar con confirmación

El administrador SHALL desactivar un ítem activo y reactivar uno inactivo de cualquier catálogo con confirmación dentro de un `Dialog`, sin `window.confirm`. "Volver" o Escape MUST cerrar sin enviar nada. Confirmar MUST enviar `POST /api/<recurso>/{id}/deactivate` o `/reactivate`, refrescar la lista y anunciar el resultado. El texto MUST aclarar que los turnos ya dados no cambian.

#### Scenario: Desactivar un sillón exige confirmación interna

- **Dado (GIVEN)** un usuario con rol `administrador` en `/catalogos?seccion=sillones` con el sillón activo "Sillón 2"
- **Cuando (WHEN)** pulsa "Desactivar" en esa fila y luego "Volver"
- **Entonces (THEN)** el diálogo de confirmación aclara que los turnos ya dados no cambian y, al pulsar "Volver", se cierra sin ninguna petición `POST`
- **Y** al pulsar de nuevo "Desactivar" y luego "Sí, desactivar" se envía `POST /api/chairs/{id}/deactivate`, la fila de "Sillón 2" muestra "Inactivo" y se anuncia "Sillón desactivado." en `role="status"`

#### Scenario: Reactivar una prestación inactiva

- **Dado (GIVEN)** un usuario con rol `administrador` en `/catalogos?seccion=prestaciones` con la prestación inactiva "Blanqueamiento"
- **Cuando (WHEN)** pulsa "Reactivar" en esa fila y luego "Sí, reactivar"
- **Entonces (THEN)** se envía `POST /api/services/{id}/reactivate`
- **Y** la fila de "Blanqueamiento" muestra "Activo" y se anuncia "Prestación reactivada." en `role="status"`

### Requirement: Estilos solo con tokens existentes y superficie clara

Los `.module.css` de pacientes y catálogos SHALL usar solo custom properties definidas en `frontend/src/shared/styles/tokens.css`, sin colores HEX ni `rgb()` sueltos. Como son pantallas sobre fondo claro, MUST NOT usar `--color-ice` ni tokens `*-on-navy`.

#### Scenario: Toda variable CSS de las pantallas existe en tokens.css

- **Dado (GIVEN)** los archivos `.module.css` de `frontend/src/features/pacientes/` y `frontend/src/features/catalogos/`
- **Cuando (WHEN)** se extrae cada `var(--x)`, con o sin valor de respaldo
- **Entonces (THEN)** cada `--x` está definido en `tokens.css`
- **Y** ningún archivo contiene colores HEX ni `rgb()`

#### Scenario: Sin tokens de fondo oscuro en las pantallas

- **Dado (GIVEN)** los mismos archivos `.module.css`
- **Cuando (WHEN)** se buscan tokens de superficie oscura
- **Entonces (THEN)** ningún archivo contiene `--color-ice` ni un token que termine en `on-navy` u `on-navy-*`

### Requirement: Diseño adaptable a 1440, 768 y 390 px

Las tablas SHALL ser `<table>` con `<caption>` y `scope="col"`. Hasta 640 px, cada fila MUST apilarse con la etiqueta de cada dato, sin scroll horizontal de página a 390 px. Los controles MUST medir al menos 44 px y tener `:focus-visible`. Los diálogos de formulario MUST verse como hoja inferior hasta 640 px.

#### Scenario: Tablas apiladas en celular, controles táctiles y foco visible

- **Dado (GIVEN)** los `.module.css` de las tablas de pacientes y de catálogos
- **Cuando (WHEN)** se leen sus reglas
- **Entonces (THEN)** existe un bloque `@media (max-width: 640px)` que apila las filas de la tabla y muestra la etiqueta de cada celda
- **Y** los botones de acción declaran `min-height: 44px` y una regla `:focus-visible`

#### Scenario: Formulario de catálogo como hoja inferior en celular

- **Dado (GIVEN)** el diálogo de formulario de catálogo abierto con `isMobile`
- **Cuando (WHEN)** se evalúa el DOM
- **Entonces (THEN)** el `<dialog>` tiene `data-mobile-sheet="true"` y la clase de hoja inferior de `Dialog`

### Requirement: Tarjeta de diálogo para modales

Los tres diálogos de la interfaz (`PatientFormDialog`, `CatalogFormDialog`, `CatalogConfirmDialog`) SHALL envolver su contenido en una tarjeta con fondo propio, borde, sombra y ancho máximo, identificada con `data-modal-card="<nombre>"`. En pantallas móviles (hasta 640 px), la tarjeta MUST ocupar el ancho completo adaptándose como hoja inferior.

#### Scenario: Los tres diálogos muestran su contenido en una tarjeta

- **Dado (GIVEN)** los tres diálogos de la interfaz (`PatientFormDialog`, `CatalogFormDialog` y `CatalogConfirmDialog`)
- **Cuando (WHEN)** cada diálogo se abre
- **Entonces (THEN)** dentro del elemento `<dialog>` existe un contenedor con el atributo `data-modal-card`
- **Y** los estilos de `.modalContent` definen `background-color`, `border` y `max-width`

### Requirement: Encabezado para la columna de acciones

Las tablas de pacientes y de catálogos SHALL incluir un encabezado `<th scope="col">Acciones</th>` visible siempre que las filas ofrezcan acciones de edición, desactivación o reactivación, garantizando que el encabezado cubra la totalidad de las columnas de la tabla.

#### Scenario: Las tablas tienen encabezado para la columna de acciones

- **Dado (GIVEN)** las pantallas `/pacientes` y `/catalogos` consultadas por un usuario con permisos de edición (`administrador` o `recepcion`)
- **Cuando (WHEN)** se visualiza la tabla con filas que contienen botones de acción
- **Entonces (THEN)** el elemento `<thead>` contiene un `<th scope="col">` con el texto visible "Acciones" alineado con la columna correspondiente

### Requirement: Adaptación accesible de tablas en celular

En pantallas estrechas (hasta 640 px), las tablas de pacientes y catálogos SHALL mostrar su `<caption>` a todo el ancho del contenedor. El encabezado `<thead>` MUST ocultarse de forma accesible mediante el patrón visually-hidden (sin `display: none`) y sin líneas o bordes sueltos residuales.

#### Scenario: Tabla apilada en celular con el título a todo el ancho y el encabezado oculto de forma accesible

- **Dado (GIVEN)** los archivos `.module.css` de las tablas de pacientes y de catálogos
- **Cuando (WHEN)** se evalúa el bloque `@media (max-width: 640px)`
- **Entonces (THEN)** la clase `.caption` declara `display: block` y `width: 100%`
- **Y** el encabezado `<thead>` se oculta mediante posicionamiento absoluto y recorte accesible (patrón visually-hidden, no `display: none`) sin bordes sueltos

### Requirement: Mensaje único en búsqueda de pacientes

Cuando una búsqueda en `/pacientes` no arroja resultados, la pantalla SHALL mostrar un único mensaje de estado indicando "No se encontraron pacientes.", sin superponer ni concatenar mensajes descriptivos secundarios.

#### Scenario: Búsqueda sin resultados muestra un único mensaje

- **Dado (GIVEN)** un usuario en `/pacientes` que busca una consulta sin coincidencias
- **Cuando (WHEN)** la API devuelve una lista vacía de pacientes
- **Entonces (THEN)** la pantalla muestra únicamente "No se encontraron pacientes."
- **Y** no se muestra el mensaje secundario "No hay resultados para la búsqueda realizada."

#### Scenario: Pantallas verificadas a 1440, 768 y 390 px

- **Dado (GIVEN)** la aplicación en ejecución con datos ficticios del seed
- **Cuando (WHEN)** se capturan `/pacientes`, `/catalogos` (con un ítem inactivo), un formulario con un error 409 y la confirmación de desactivar a 1440, 768 y 390 px
- **Entonces (THEN)** no hay scroll horizontal de página en ningún ancho y la tabla se ve apilada a 390 px
- **Y** esta verificación es visual (capturas a cargo de Claude)

#### Scenario: Diálogo como hoja inferior verificado a 390 px

- **Dado (GIVEN)** la aplicación en ejecución en un viewport de 390 px
- **Cuando (WHEN)** se abre "Nuevo paciente" y "Nueva prestación"
- **Entonces (THEN)** cada diálogo aparece como hoja inferior a ancho completo con los botones visibles
- **Y** esta verificación es visual (capturas a cargo de Claude)
