# frontend-appointment-actions Specification

## Purpose
Gestión interactiva del ciclo de vida del turno desde la agenda del frontend: diálogo modal de detalle, consulta de historial con horas locales, transiciones de estado ordinarias, cancelación con confirmación interna, formulario de reprogramación con revalidación de solapamientos, matriz RBAC por rol, anuncios accesibles con `role="status"` y adaptabilidad responsive en escritorio, tablet y móvil.

## Requirements

### Requirement: Diálogo de detalle del turno

El sistema SHALL presentar un diálogo modal accesible `AppointmentDetailDialog` al seleccionar un turno de la agenda. El diálogo MUST exhibir los datos del turno en hora local según el `timezone` de la API: paciente, profesional, sillón, prestación, horario y `StatusBadge`. Al cerrarse mediante botón o la tecla Escape, el foco MUST retornar al elemento disparador.

#### Scenario: Apertura con datos completos y formato horario local

- **GIVEN** la agenda diaria con un turno de "Ana Pérez" con la "Dra. Laura Quiroga" de 10:00 a 10:30
- **WHEN** el usuario activa la selección de dicho turno
- **THEN** se abre el diálogo modal `AppointmentDetailDialog`
- **AND** se muestran los nombres del paciente, profesional, sillón, prestación, el horario "10:00–10:30" y el badge de estado
- **AND** el foco se traslada al diálogo

#### Scenario: Retorno de foco al cerrar el detalle

- **GIVEN** el diálogo modal de detalle abierto asociado a un disparador en la agenda
- **WHEN** el usuario presiona el botón "Cerrar" o la tecla Escape
- **THEN** el diálogo se cierra sin enviar solicitudes
- **AND** el foco regresa al botón del turno que abrió el diálogo

### Requirement: Consulta y visualización del historial de cambios

El diálogo de detalle SHALL consultar `GET /api/appointments/{id}/history` y renderizar la lista cronológica de transiciones. Cada entrada MUST presentar el autor (`changedByName`), la transición (`from → to`), la fecha y la hora formateadas en hora local. Si la entrada incluye `reschedule`, MUST detallar el horario previo y el nuevo.

#### Scenario: Historial renderiza transiciones cronológicas con hora local

- **GIVEN** un turno con dos cambios registrados en `GET /api/appointments/{id}/history`
- **WHEN** se renderiza la sección de historial en el detalle del turno
- **THEN** se exhibe cada entrada ordenada cronológicamente con su autor y estado
- **AND** las marcas temporales se presentan en la zona horaria provista por la API

#### Scenario: Historial renderiza desglose de reprogramación con horario previo y nuevo

- **GIVEN** una entrada de historial con objeto `reschedule`
- **WHEN** se visualiza la entrada en el panel de historial
- **THEN** se exhibe el horario previo y el horario nuevo en hora local

#### Scenario: Error al cargar historial muestra aviso accesible

- **GIVEN** una falla de red o respuesta de error al pedir el historial
- **WHEN** la solicitud a `GET /api/appointments/{id}/history` falla
- **THEN** se muestra un aviso accesible de error en la sección de historial sin romper el diálogo

### Requirement: Cambios de estado ordinarios

El diálogo SHALL permitir cambiar el estado de turnos no terminales enviando `POST /api/appointments/{id}/status` con `{ toStatus }` según las opciones: "Confirmar turno", "Marcar atendido" y "Marcar ausente". Los botones MUST ajustarse al estado y rol sin lógica temporal en el cliente. En estados terminales MUST mostrar "Este turno ya no admite cambios." sin acciones.

#### Scenario: Confirmación exitosa de turno reservado

- **GIVEN** un turno en estado `reservado` y un usuario de recepción
- **WHEN** el usuario pulsa "Confirmar turno"
- **THEN** se envía `POST /api/appointments/{id}/status` con `{ toStatus: "confirmado" }`
- **AND** ante respuesta 200 OK el diálogo se cierra y la agenda se actualiza

#### Scenario: Rechazo 422 por marcar atendido antes del inicio

- **GIVEN** un turno con horario de inicio futuro respecto del reloj del servidor
- **WHEN** el usuario pulsa "Marcar atendido"
- **THEN** la API responde 422 con código `STATUS_CHANGE_TOO_EARLY`
- **AND** el alert superior del diálogo expone el mensaje textual devuelto por el backend
- **AND** el foco se traslada al alert de error

#### Scenario: Rechazo 422 por transición desde estado terminal

- **GIVEN** un turno que pasó a estado terminal concurrentemente
- **WHEN** se envía una solicitud de cambio de estado y la API responde 422 `INVALID_TRANSITION`
- **THEN** el alert superior del diálogo muestra el mensaje explicativo del dominio

### Requirement: Cancelación de turnos con confirmación interna

El sistema SHALL permitir la cancelación de turnos en `reservado` o `confirmado` mediante el botón "Cancelar turno". Al pulsarlo, MUST desplegarse una confirmación interna in-dialog sin recurrir a `window.confirm`. Al confirmar, MUST enviarse `POST /api/appointments/{id}/cancel` sin cuerpo. Al desestimar, MUST retornarse al detalle sin enviar peticiones.

#### Scenario: Cancelación confirmada pasa turno a cancelado

- **GIVEN** un turno en estado `confirmado` en el diálogo de detalle
- **WHEN** el usuario pulsa "Cancelar turno" y confirma la operación
- **THEN** se envía `POST /api/appointments/{id}/cancel` sin cuerpo
- **AND** ante respuesta 200 OK el diálogo se cierra y el turno queda cancelado

#### Scenario: Desestimar confirmación retorna al detalle

- **GIVEN** la vista de confirmación de cancelación activa dentro del diálogo
- **WHEN** el usuario pulsa "Volver al detalle" o presiona Escape
- **THEN** no se envía ninguna solicitud HTTP
- **AND** se restablece la vista principal del detalle del turno

#### Scenario: Error 422 al intentar cancelar turno terminal

- **GIVEN** un turno en estado terminal y un intento de cancelación
- **WHEN** la API responde 422 con violación `INVALID_TRANSITION`
- **THEN** el alert superior presenta el mensaje de error del dominio

### Requirement: Formulario y flujo de reprogramación

El sistema SHALL proveer el diálogo modal `AppointmentRescheduleDialog` con paciente y prestación en solo lectura, y campos editables para fecha, hora, profesional, sillón y duración (múltiplos de 5 min, entre 5 y 480). La solicitud MUST enviarse a `POST /api/appointments/{id}/reschedule` revalidando las reglas de agenda del dominio y devolviendo el turno a reservado.

#### Scenario: Reprogramación exitosa revalida agenda y vuelve a reservado

- **GIVEN** un turno en estado `confirmado`
- **WHEN** el usuario abre el diálogo de reprogramación, ingresa un nuevo horario libre y confirma
- **THEN** se envía `POST /api/appointments/{id}/reschedule` con el nuevo `startAt`
- **AND** ante respuesta 200 OK con estado `reservado` el modal se cierra y la agenda se refresca

#### Scenario: Conflicto 409 por solapamiento de agenda

- **GIVEN** un intento de reprogramar a un intervalo con profesional o sillón ocupado
- **WHEN** la API responde 409 con violaciones como `PROFESSIONAL_OVERLAP` o `CHAIR_OVERLAP`
- **THEN** el diálogo muestra las violaciones íntegras en el alert superior con `role="alert"`
- **AND** el foco se traslada al alert de error

#### Scenario: Rechazo 422 por reprogramar al pasado

- **GIVEN** una fecha u hora seleccionada anterior al instante actual del servidor
- **WHEN** la API responde 422 con violación `IN_THE_PAST`
- **THEN** el formulario expone el mensaje explicativo del dominio en el alert superior

#### Scenario: Error de entrada 400 marca campos con aria-invalid

- **GIVEN** una respuesta 400 con lista de errores de campo
- **WHEN** se procesa la respuesta en el formulario de reprogramación
- **THEN** los campos involucrados se marcan con `aria-invalid="true"` y mensaje inline

### Requirement: Control de acceso por rol en las acciones

Recepción y Administrador SHALL tener acceso a todas las acciones de turnos. El Odontólogo MUST tener acceso a cambiar estado ("Confirmar turno", "Marcar atendido", "Marcar ausente") únicamente en turnos propios (`user.professionalId === appointment.professionalId`). En turnos ajenos, MUST tener vista de solo lectura sin acciones ni consulta de historial.

#### Scenario: Odontólogo cambia estado de turno propio exitosamente

- **GIVEN** un usuario autenticado con rol `odontologo` cuyo `professionalId` coincide con el turno
- **WHEN** accede al detalle de su turno
- **THEN** se muestran habilitados los botones de estado permitidos
- **AND** puede efectuar el cambio de estado exitosamente

#### Scenario: Odontólogo en turno ajeno tiene vista de solo lectura

- **GIVEN** un usuario autenticado con rol `odontologo` sobre un turno de otro profesional
- **WHEN** se renderiza el diálogo de detalle
- **THEN** no se presentan botones de cambio de estado, reprogramación ni cancelación
- **AND** no se envía la consulta de historial del turno

#### Scenario: Rechazo 403 muestra mensaje de permiso denegado

- **GIVEN** una respuesta 403 con violación `FORBIDDEN_OPERATION`
- **WHEN** se recibe la respuesta de la API
- **THEN** el mensaje de permiso denegado se muestra en el alert de resumen sin cerrar la sesión

### Requirement: Gestión de errores del dominio en alertas accesibles

Toda respuesta 409, 422 o 403 devuelta por la API SHALL presentarse en un contenedor superior de alertas con `role="alert"` y `aria-live="assertive"`. El resumen MUST incluir el código de la violación y el mensaje textual en español íntegro devuelto por el backend. Al producirse el rechazo, el foco del navegador MUST trasladarse automáticamente al contenedor de alerta.

#### Scenario: Alert muestra código estable y mensaje textual en español

- **GIVEN** una solicitud rechazada por el dominio con violaciones tipadas
- **WHEN** se renderiza la respuesta de error en el diálogo
- **THEN** el contenedor `role="alert"` expone cada violación con su código y mensaje en español
- **AND** no se enmascaran ni alteran los textos del backend

#### Scenario: Foco automático al alert de error

- **GIVEN** un formulario enviado que culmina en error 409, 422 o 403
- **WHEN** se procesa el fallo
- **THEN** el foco del navegador se traslada inmediatamente al contenedor `role="alert"`

### Requirement: Anuncios accesibles y refresco de agenda

Tras completar exitosamente cualquier acción de mutación (cambio de estado, cancelación o reprogramación), el sistema SHALL cerrar el diálogo activo, invocar el refresco de datos mediante `useAgenda().refresh()` y emitir un anuncio en la región permanente con `role="status"` de la página de agenda con el mensaje exacto según la operación realizada.

#### Scenario: Anuncio accesible y refresco tras confirmar turno

- **GIVEN** la confirmación exitosa de un turno
- **WHEN** culmina la operación
- **THEN** se cierra el diálogo, se refresca la agenda y la región `role="status"` anuncia "Turno confirmado."

#### Scenario: Anuncio accesible y refresco tras marcar atendido

- **GIVEN** la marcación exitosa de un turno como atendido
- **WHEN** culmina la operación
- **THEN** se cierra el diálogo, se refresca la agenda y la región `role="status"` anuncia "Turno marcado como atendido."

#### Scenario: Anuncio accesible y refresco tras marcar ausente

- **GIVEN** la marcación exitosa de un turno como ausente
- **WHEN** culmina la operación
- **THEN** se cierra el diálogo, se refresca la agenda y la región `role="status"` anuncia "Turno marcado como ausente."

#### Scenario: Anuncio accesible y refresco tras cancelar turno

- **GIVEN** la cancelación exitosa de un turno
- **WHEN** culmina la operación
- **THEN** se cierra el diálogo, se refresca la agenda y la región `role="status"` anuncia "Turno cancelado."

#### Scenario: Anuncio accesible y refresco tras reprogramar turno

- **GIVEN** la reprogramación exitosa de un turno para una fecha y hora determinadas
- **WHEN** culmina la operación
- **THEN** se cierra el diálogo, se refresca la agenda y la región `role="status"` anuncia "Turno reprogramado para el DD/MM/AAAA a las HH:MM."

### Requirement: Adaptabilidad visual de las interfaces de turno

Los diálogos modales de detalle y reprogramación SHALL adaptarse a pantallas de escritorio (1440 px), tablet (768 px) y móvil (390 px). En todas las resoluciones, los textos MUST ser legibles sin desbordes horizontales y los controles táctiles en tablet y móvil MUST cumplir con una altura mínima de 44 px. Esta verificación se valida mediante capturas independientes.

#### Scenario: Visualización en escritorio a 1440 px

- **GIVEN** el diálogo de detalle o reprogramación abierto en viewport de 1440 px
- **WHEN** se visualiza el contenido del modal
- **THEN** los campos, botones e historial se presentan alineados sin desbordes
- **AND** esta verificación es visual mediante captura de pantalla

#### Scenario: Visualización en tablet a 768 px

- **GIVEN** el diálogo de detalle o confirmación de cancelación en viewport de 768 px
- **WHEN** se evalúa la botonera y controles interactivos
- **THEN** los elementos táctiles presentan al menos 44 px de altura sin solapamientos
- **AND** esta verificación es visual mediante captura de pantalla

#### Scenario: Visualización en móvil a 390 px

- **GIVEN** el diálogo de detalle o formulario de reprogramación en viewport de 390 px
- **WHEN** se evalúa la disposición de la interfaz
- **THEN** los controles adoptan disposición vertical de columna única sin scroll horizontal
- **AND** esta verificación es visual mediante captura de pantalla
