# Spec Delta

## Purpose

Interfaz de usuario para la visualización y gestión de horarios semanales de atención y bloqueos de agenda de los profesionales en `/horarios`, con permisos por rol (edición para odontólogo y administrador, solo lectura para recepción), aviso de turnos afectados sin cancelaciones, hora local según la API y diseño adaptable a 1440, 768 y 390 px.

## ADDED Requirements

### Requirement: Ruta y resolución de profesional por rol

La ruta `/horarios` SHALL resolver el profesional según el rol del usuario autenticado. El odontólogo MUST editar únicamente su agenda (`user.professionalId`) sin selector. Administrador y recepción MUST disponer de un selector con profesionales activos. Si un odontólogo intenta consultar a otro profesional mediante `?professionalId=`, la pantalla SHALL enviar la petición a la API y MUST mostrar el error 403 del backend en una alerta accesible `role="alert"` sin cerrar sesión.

#### Scenario: Odontólogo accede a sus propios horarios
- **GIVEN** un usuario autenticado con rol `"odontologo"` y `professionalId = P`
- **WHEN** navega a la ruta `/horarios`
- **THEN** la pantalla carga los horarios y bloqueos del profesional `P` sin mostrar selector de profesional

#### Scenario: Administrador selecciona profesional activo
- **GIVEN** un usuario autenticado con rol `"administrador"`
- **WHEN** abre `/horarios` sin parámetro `professionalId`
- **THEN** el selector lista únicamente profesionales activos y selecciona por defecto al primero
- **AND** al cambiar de profesional se actualizan los datos y la URL refleja `?professionalId=`

#### Scenario: Odontólogo consulta profesional ajeno y recibe 403
- **GIVEN** un usuario odontólogo autenticado como `P`
- **WHEN** accede a `/horarios?professionalId=Q` donde `Q != P`
- **THEN** el backend responde con código 403 y la violación `FORBIDDEN_OPERATION`
- **AND** la pantalla muestra en `role="alert"` el mensaje literal "No tiene permiso para leer horarios." sin controles de edición ni cerrar sesión

### Requirement: Gestión y guardado de tramos semanales

La sección de horarios SHALL listar los días de la semana con sus tramos en formato de texto `HH:MM–HH:MM`. Los usuarios con permiso MUST poder agregar tramos con "Agregar tramo" y quitarlos con "Quitar". El botón "Guardar horario" MUST enviar la semana completa como un arreglo de tramos mediante `PUT /api/professionals/{id}/working-hours` en el orden visual de la pantalla. Tras un guardado exitoso, la pantalla SHALL anunciar "Horario guardado." en una región accesible `role="status"`.

#### Scenario: Guardado exitoso de tramos semanales
- **GIVEN** un odontólogo o administrador editando horarios con un tramo "lunes 09:00 a 13:00"
- **WHEN** pulsa "Guardar horario"
- **THEN** se envía `PUT /api/professionals/{id}/working-hours` con `[{ weekday: 1, start: "09:00", end: "13:00" }]`
- **AND** la pantalla anuncia "Horario guardado." en `role="status"` conservando los tramos guardados

#### Scenario: Edición interactiva de tramos en la interfaz
- **GIVEN** la sección de horarios para un día sin tramos
- **WHEN** el usuario hace clic en "Agregar tramo" para el día martes y luego en "Quitar"
- **THEN** se añade una fila editable con inputs de texto para inicio y fin y se remueve al pulsar "Quitar"

### Requirement: Validación de tramos y errores de solapamiento

La validación de consistencia y solapamiento de tramos SHALL realizarse en el backend. Cuando la API responde con error 422 `OVERLAPPING_WORKING_HOURS` o `INVALID_WORKING_HOURS`, la interfaz MUST mostrar el mensaje literal del backend en una alerta con `role="alert"` y trasladar el foco a dicha alerta. Si la API responde con error 400 por formato de campo, los inputs involucrados MUST marcarse con `aria-invalid="true"`.

#### Scenario: Rechazo por tramos solapados muestra mensaje literal del backend
- **GIVEN** dos tramos del lunes que se superponen entre 09:00–12:00 y 11:00–13:00
- **WHEN** el usuario pulsa "Guardar horario" y el backend responde 422 `OVERLAPPING_WORKING_HOURS`
- **THEN** se muestra en `role="alert"` exactamente "Los tramos 1 y 2 del lunes se solapan: de 09:00 a 12:00 y de 11:00 a 13:00."
- **AND** el foco del teclado se traslada al contenedor del error sin modificar los tramos en pantalla

#### Scenario: Error 400 marca campos con aria-invalid
- **GIVEN** un tramo con formato de hora inválido en inicio
- **WHEN** el backend responde 400 con error de validación en el campo
- **THEN** el input afectado adopta `aria-invalid="true"` y se muestra el mensaje de validación

### Requirement: Aviso de turnos afectados sin cancelación

Cuando el guardado de horarios o el alta de bloqueos devuelve turnos afectados (`appointmentsOutsideHours` o `affectedAppointments`), la pantalla SHALL mostrar una lista con `role="alert"` que detalle fecha, hora local, paciente, profesional y estado con texto visible (`StatusBadge`). La interfaz MUST informar con una nota fija que los turnos afectados no se cancelan automáticamente y deben reprogramarse o gestionarse desde la agenda.

#### Scenario: Turnos futuros fuera del horario al guardar tramos
- **GIVEN** un `PUT` exitoso de horarios que incluye turnos en `appointmentsOutsideHours`
- **WHEN** se completa el guardado
- **THEN** la pantalla muestra en `role="alert"` la lista de turnos con fecha, hora local, paciente, profesional y su `StatusBadge`
- **AND** se incluye el texto informativo "Los turnos no se cancelan automáticamente; deben reprogramarse o cancelarse desde la agenda."

#### Scenario: Turnos solapados al crear un bloqueo
- **GIVEN** la creación de un bloqueo que se superpone con turnos existentes y devuelve `affectedAppointments`
- **WHEN** el backend responde 201
- **THEN** se muestra en `role="alert"` la advertencia de turnos solapados con paciente, fecha, hora local y estado

### Requirement: Creación y eliminación de bloqueos con hora local

La sección de bloqueos SHALL listar los bloqueos del profesional en hora local y permitir crear nuevos mediante un diálogo modal `Dialog`. El formulario MUST convertir las fechas locales a instantes ISO con offset antes de enviar `POST /api/professionals/{id}/blocks`. La eliminación de un bloqueo MUST exigir confirmación explícita dentro del diálogo; presionar Escape o cancelar MUST volver a la lista sin enviar peticiones. Al confirmar, SHALL enviarse `DELETE /api/blocks/{id}`.

#### Scenario: Creación exitosa de bloqueo con offset
- **GIVEN** el diálogo de "Nuevo bloqueo" con fecha y horas en hora local
- **WHEN** el usuario completa inicio, fin y motivo y confirma el formulario
- **THEN** se envía `POST /api/professionals/{id}/blocks` con instantes ISO que incluyen el offset de zona horaria
- **AND** el diálogo se cierra, se recarga la lista y se anuncia "Bloqueo creado." en `role="status"`

#### Scenario: Eliminación de bloqueo con confirmación in-dialog
- **GIVEN** un bloqueo visible en la lista
- **WHEN** el usuario hace clic en "Eliminar bloqueo" y confirma con "Sí, eliminar bloqueo"
- **THEN** se envía `DELETE /api/blocks/{id}`, el bloqueo desaparece de la lista y se anuncia "Bloqueo eliminado." en `role="status"`

#### Scenario: Cancelación del borrado con Escape
- **GIVEN** el diálogo de confirmación de eliminación de bloqueo abierto
- **WHEN** el usuario presiona la tecla Escape o hace clic en "Volver"
- **THEN** el diálogo se cierra sin enviar ninguna solicitud DELETE y el bloqueo permanece en la lista

#### Scenario: Bloqueo inválido muestra mensaje literal del backend
- **GIVEN** un formulario de nuevo bloqueo con fecha de inicio posterior al fin
- **WHEN** se envía el formulario y el backend responde 422 `INVALID_BLOCK`
- **THEN** la pantalla muestra en `role="alert"` el mensaje literal "El bloqueo no es válido: el inicio debe ser anterior al fin."
- **AND** el diálogo permanece abierto con los valores ingresados

### Requirement: Modo solo lectura para rol recepción

El rol recepción SHALL contar con acceso estrictamente de solo lectura a la gestión de horarios y bloqueos en `/horarios`. La pantalla MUST mostrar el selector de profesionales activos, la grilla de tramos de cada día y la lista de bloqueos. La interfaz MUST ocultar o no renderizar los botones "Agregar tramo", "Quitar", "Guardar horario", "Nuevo bloqueo" y "Eliminar bloqueo".

#### Scenario: Recepción visualiza información completa sin controles de edición
- **GIVEN** un usuario autenticado con rol `"recepcion"`
- **WHEN** accede a `/horarios`
- **THEN** puede visualizar el selector de profesional, los tramos semanales y los bloqueos vigentes
- **AND** no se renderizan los botones "Agregar tramo", "Quitar", "Guardar horario", "Nuevo bloqueo" ni "Eliminar bloqueo"

### Requirement: Obtención y reutilización de zona horaria desde la API

La pantalla SHALL obtener la zona horaria de la aplicación consultando una sola vez el endpoint `GET /api/agenda` al cargar. El valor obtenido MUST reutilizarse para todas las conversiones y formateos de fecha y hora local de horarios y bloqueos. El código productivo MUST NOT contener constantes de zona horaria hardcodeadas.

#### Scenario: Zona horaria leída desde GET /api/agenda
- **GIVEN** la carga inicial de `/horarios`
- **WHEN** la pantalla consulta `GET /api/agenda`
- **THEN** extrae el campo `timezone` de la respuesta y formatea todas las fechas y horas locales de acuerdo a ese identificador

### Requirement: Adaptabilidad móvil y responsive en 1440, 768 y 390 px

La pantalla `/horarios` SHALL adaptar su diseño sin scroll horizontal en viewports de 1440 px, 768 px y 390 px. En 1440 px, tramos y bloqueos MUST presentarse en dos columnas principales. En 768 px y 390 px, MUST apilarse en una columna. A 390 px, los inputs de tramo y botones MUST redistribuirse sin desbordamiento. El diálogo de bloqueo MUST desplegarse como hoja inferior fijada al fondo de pantalla en anchos menores o iguales a 640 px.

#### Scenario: Presentación de modal como hoja inferior en móvil
- **GIVEN** un viewport móvil de 390 px (<= 640 px)
- **WHEN** se abre el diálogo de "Nuevo bloqueo"
- **THEN** el diálogo se presenta como hoja inferior fijada al borde inferior ocupando el 100% del ancho útil

#### Scenario: Verificación visual multi-resolución en 1440, 768 y 390 px
- **GIVEN** la pantalla `/horarios` con datos cargados
- **WHEN** se inspecciona en resoluciones de 1440 px, 768 px y 390 px
- **THEN** en 1440 px se comprueba la grilla en dos columnas, en 768 px la columna apilada, y en 390 px la ausencia de scroll horizontal y la hoja inferior
- **AND** esta verificación es visual (capturas a cargo de Claude)
