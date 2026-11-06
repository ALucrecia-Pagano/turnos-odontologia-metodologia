## ADDED Requirements

### Requirement: Endpoints de profesionales
La API SHALL exponer endpoints bajo /api/professionals para consultar y administrar profesionales. GET /api/professionals lista los profesionales y admite el filtro opcional active. GET /api/professionals/{id} devuelve el detalle de un profesional. POST /api/professionals crea un profesional. PUT /api/professionals/{id} actualiza sus datos. Los esquemas admiten el campo opcional licenseNumber.

#### Scenario: Alta exitosa de profesional con matrícula responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con fullName "Dra. Laura Quiroga" y licenseNumber "MN-12345"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "Dra. Laura Quiroga", licenseNumber "MN-12345" y active verdadero

#### Scenario: Edición exitosa de profesional responde 200
- **GIVEN** un profesional existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dra. Laura Quiroga Modificada" y licenseNumber "MN-99999"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo fullName y licenseNumber conservando el mismo id

#### Scenario: Edición de profesional conservando su propio nombre responde 200
- **GIVEN** un profesional existente con fullName "Dra. Laura Quiroga" y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dra. Laura Quiroga" y licenseNumber "MN-88888"
- **THEN** el status es 200
- **AND** el cuerpo conserva fullName "Dra. Laura Quiroga" con licenseNumber "MN-88888"

#### Scenario: Edición de profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/professionals/{id} con fullName "Dr. Inexistente"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Listado de profesionales con filtro active verdadero
- **GIVEN** profesionales activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/professionals con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de profesionales sin filtro incluye inactivos en orden alfabético
- **GIVEN** profesionales activos e inactivos persistidos y un usuario autenticado
- **WHEN** invoca GET /api/professionals sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye profesionales inactivos ordenados por nombre ascendente

#### Scenario: Recepción lista profesionales y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 200
- **AND** recibe la lista de profesionales

#### Scenario: El odontólogo lista profesionales y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 200
- **AND** recibe la lista de profesionales

#### Scenario: Detalle de profesional existente responde 200
- **GIVEN** un profesional existente con id P1 y un usuario autenticado
- **WHEN** invoca GET /api/professionals/P1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de P1

#### Scenario: Detalle de profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario autenticado
- **WHEN** invoca GET /api/professionals/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Consulta de profesionales sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/professionals
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de profesional rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de profesional rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de profesional rechazada para rol recepción con 403
- **GIVEN** un profesional existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/professionals/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de profesional rechazada para rol odontólogo con 403
- **GIVEN** un profesional existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/professionals/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de profesional con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con fullName vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de profesional con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals con un JSON sin el campo obligatorio fullName
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de sillones
La API SHALL exponer endpoints bajo /api/chairs para consultar y administrar sillones odontológicos. GET /api/chairs lista los sillones y admite el filtro opcional active. GET /api/chairs/{id} devuelve el detalle de un sillón. POST /api/chairs crea un sillón. PUT /api/chairs/{id} actualiza el nombre del sillón. El nombre del sillón debe ser único en el sistema.

#### Scenario: Alta exitosa de sillón responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name "Sillón Azul"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, name "Sillón Azul" y active verdadero

#### Scenario: Edición exitosa de sillón responde 200
- **GIVEN** un sillón existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón Verde"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo name conservando el mismo id

#### Scenario: Edición de sillón conservando su propio nombre responde 200
- **GIVEN** un sillón existente con name "Sillón 1" y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón 1"
- **THEN** el status es 200
- **AND** el cuerpo conserva name "Sillón 1" sin emitir violación de duplicado

#### Scenario: Edición de sillón con el nombre de otro sillón responde 409
- **GIVEN** un sillón existente S1 llamado "Sillón 1", otro sillón S2 llamado "Sillón 2", y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/S2 con name "Sillón 1"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Edición de sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/chairs/{id} con name "Sillón Fantasma"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Listado de sillones con filtro active verdadero
- **GIVEN** sillones activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/chairs con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de sillones con filtro active falso devuelve solo inactivos
- **GIVEN** sillones activos e inactivos y un usuario autenticado
- **WHEN** invoca GET /api/chairs con active=false
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active falso

#### Scenario: Listado de sillones sin filtro incluye inactivos en orden alfabético
- **GIVEN** sillones activos e inactivos persistidos y un usuario autenticado
- **WHEN** invoca GET /api/chairs sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye sillones inactivos ordenados por nombre ascendente

#### Scenario: Recepción lista sillones y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 200
- **AND** recibe la lista de sillones

#### Scenario: El odontólogo lista sillones y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 200
- **AND** recibe la lista de sillones

#### Scenario: Detalle de sillón existente responde 200
- **GIVEN** un sillón existente con id S1 y un usuario autenticado
- **WHEN** invoca GET /api/chairs/S1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de S1

#### Scenario: Detalle de sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario autenticado
- **WHEN** invoca GET /api/chairs/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Consulta de sillones sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/chairs
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de sillón rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de sillón rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de sillón rechazada para rol recepción con 403
- **GIVEN** un sillón existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/chairs/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de sillón rechazada para rol odontólogo con 403
- **GIVEN** un sillón existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/chairs/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de sillón con nombre duplicado responde 409
- **GIVEN** un sillón existente llamado "Sillón 1" y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name "Sillón 1"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Alta de sillón con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con name vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de sillón con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs con un JSON sin el campo obligatorio name
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de prestaciones
La API SHALL exponer endpoints bajo /api/services para consultar y administrar prestaciones. GET /api/services lista las prestaciones y admite el filtro opcional active. GET /api/services/{id} devuelve el detalle de una prestación. POST /api/services crea una prestación con nombre y duración en minutos. PUT /api/services/{id} actualiza sus datos. El nombre debe ser único y la duración múltiplo de 5 entre 5 y 480 minutos.

#### Scenario: Alta exitosa de prestación responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Consulta General" y defaultDurationMin 30
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, name "Consulta General", defaultDurationMin 30 y active verdadero

#### Scenario: Edición exitosa de prestación responde 200
- **GIVEN** una prestación existente y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Consulta Prolongada" y defaultDurationMin 45
- **THEN** el status es 200
- **AND** el cuerpo refleja los nuevos valores conservando el mismo id

#### Scenario: Edición de prestación conservando su propio nombre responde 200
- **GIVEN** una prestación existente con name "Limpieza" y duración 45, y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Limpieza" y defaultDurationMin 60
- **THEN** el status es 200
- **AND** el cuerpo refleja defaultDurationMin 60 conservando name "Limpieza" sin error de duplicado

#### Scenario: Edición de prestación con el nombre de otra prestación responde 409
- **GIVEN** una prestación existente SV1 llamada "Limpieza", otra prestación SV2 llamada "Control", y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/SV2 con name "Limpieza" y defaultDurationMin 30
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Edición de prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca PUT /api/services/{id} con name "Prestación Fantasma" y defaultDurationMin 30
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Listado de prestaciones con filtro active verdadero
- **GIVEN** prestaciones activas e inactivas y un usuario autenticado
- **WHEN** invoca GET /api/services con active=true
- **THEN** el status es 200
- **AND** todos los elementos devueltos tienen active verdadero

#### Scenario: Listado de prestaciones sin filtro incluye inactivos en orden alfabético
- **GIVEN** prestaciones activas e inactivas persistidas y un usuario autenticado
- **WHEN** invoca GET /api/services sin parámetro active
- **THEN** el status es 200
- **AND** la lista incluye prestaciones inactivas ordenadas por nombre ascendente

#### Scenario: Recepción lista prestaciones y responde 200
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca GET /api/services
- **THEN** el status es 200
- **AND** recibe la lista de prestaciones

#### Scenario: El odontólogo lista prestaciones y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/services
- **THEN** el status es 200
- **AND** recibe la lista de prestaciones

#### Scenario: Detalle de prestación existente responde 200
- **GIVEN** una prestación existente con id SV1 y un usuario autenticado
- **WHEN** invoca GET /api/services/SV1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de SV1

#### Scenario: Detalle de prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario autenticado
- **WHEN** invoca GET /api/services/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Consulta de prestaciones sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/services
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de prestación rechazada para rol recepción con 403
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de prestación rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de prestación rechazada para rol recepción con 403
- **GIVEN** una prestación existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/services/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/services/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de prestación con nombre duplicado responde 409
- **GIVEN** una prestación existente llamada "Limpieza" y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Limpieza" y defaultDurationMin 30
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_NAME

#### Scenario: Alta de prestación con duración inválida responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name "Extracción" y defaultDurationMin 7
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación INVALID_DURATION

#### Scenario: Alta de prestación con nombre vacío responde 422
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con name vacío y defaultDurationMin 30
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de prestación con cuerpo malformado responde 400
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services con un JSON sin el campo obligatorio defaultDurationMin
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

### Requirement: Endpoints de pacientes
La API SHALL exponer endpoints bajo /api/patients para consultar y administrar pacientes. GET /api/patients lista los pacientes y admite el parámetro de búsqueda textual query. GET /api/patients/{id} devuelve el detalle de un paciente. POST /api/patients crea un paciente. PUT /api/patients/{id} actualiza sus datos. Los pacientes no poseen rutas de desactivación ni borrado.

#### Scenario: Alta exitosa de paciente por recepción responde 201
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con fullName "Carlos Gómez", dni "32.111.222", phone "11-4444-5555" y healthInsurance "OSDE"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "Carlos Gómez", dni normalizado "32111222", phone "11-4444-5555" y healthInsurance "OSDE"

#### Scenario: Alta exitosa de paciente por administrador responde 201
- **GIVEN** un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/patients con fullName "María López", dni "33.222.333", phone "11-6666-7777" y healthInsurance "Swiss Medical"
- **THEN** el status es 201
- **AND** el cuerpo incluye id generado, fullName "María López" y dni normalizado "33222333"

#### Scenario: Edición exitosa de paciente responde 200
- **GIVEN** un paciente existente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Carlos Gómez Editado", dni "32.111.222", phone "11-9999-8888" y healthInsurance "Particular"
- **THEN** el status es 200
- **AND** el cuerpo refleja los nuevos datos conservando el mismo id

#### Scenario: Edición de paciente conservando su propio DNI responde 200
- **GIVEN** un paciente existente con DNI "30111222" y teléfono anterior, y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Ana Pérez" y dni "30.111.222" y nuevo teléfono "11-1234-5678"
- **THEN** el status es 200
- **AND** el cuerpo refleja el nuevo teléfono conservando DNI "30111222" sin error de duplicado

#### Scenario: Edición de paciente con el DNI de otro paciente responde 409
- **GIVEN** un paciente PA1 con DNI "30111222", otro paciente PA2 con DNI "28444555", y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/PA2 con fullName "Bruno Acosta" y dni "30.111.222"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_DNI

#### Scenario: Edición de paciente inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún paciente y un usuario con rol recepción autenticado
- **WHEN** invoca PUT /api/patients/{id} con fullName "Paciente Fantasma" y dni "30111222"
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Paciente no encontrado."

#### Scenario: Búsqueda de pacientes por parte del nombre
- **GIVEN** el paciente ficticio "Ana Pérez" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "pérez"
- **THEN** el status es 200
- **AND** la lista devuelta incluye a "Ana Pérez"

#### Scenario: Búsqueda de pacientes sin tilde no encuentra el nombre con tilde
- **GIVEN** el paciente ficticio "Ana Pérez" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "perez"
- **THEN** el status es 200
- **AND** la lista devuelta no incluye a "Ana Pérez"

#### Scenario: Búsqueda de pacientes por inicio del DNI
- **GIVEN** el paciente ficticio "Ana Pérez" con DNI "30111222" persistido y un usuario autenticado
- **WHEN** invoca GET /api/patients con query "3011"
- **THEN** el status es 200
- **AND** la lista devuelta incluye a "Ana Pérez"

#### Scenario: El odontólogo lista pacientes y responde 200
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca GET /api/patients
- **THEN** el status es 200
- **AND** recibe la lista de pacientes

#### Scenario: Detalle de paciente existente responde 200
- **GIVEN** un paciente existente con id PA1 y un usuario autenticado
- **WHEN** invoca GET /api/patients/PA1
- **THEN** el status es 200
- **AND** el cuerpo contiene los datos de PA1

#### Scenario: Detalle de paciente inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún paciente y un usuario autenticado
- **WHEN** invoca GET /api/patients/{id}
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Paciente no encontrado."

#### Scenario: Consulta de pacientes sin token responde 401
- **GIVEN** una solicitud sin cabecera de autorización
- **WHEN** invoca GET /api/patients
- **THEN** el status es 401
- **AND** el cuerpo contiene code "INVALID_TOKEN"

#### Scenario: Alta de paciente rechazada para rol odontólogo con 403
- **GIVEN** un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/patients con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Edición de paciente rechazada para rol odontólogo con 403
- **GIVEN** un paciente existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca PUT /api/patients/{id} con cuerpo válido
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Alta de paciente con DNI duplicado responde 409
- **GIVEN** un paciente existente con DNI "30111222" y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "30.111.222" y fullName "Otro Paciente"
- **THEN** el status es 409
- **AND** el cuerpo contiene la violación DUPLICATE_DNI

#### Scenario: Alta de paciente con DNI de formato inválido responde 422
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "12345" y fullName "Paciente Inválido"
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación INVALID_DNI

#### Scenario: Alta de paciente con nombre vacío responde 422
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con dni "30111222" y fullName vacío
- **THEN** el status es 422
- **AND** el cuerpo contiene la violación EMPTY_NAME

#### Scenario: Alta de paciente con cuerpo malformado responde 400
- **GIVEN** un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/patients con un JSON sin el campo obligatorio dni
- **THEN** el status es 400
- **AND** el cuerpo contiene el detalle del campo faltante

#### Scenario: Desactivación de paciente no existe en la API
- **GIVEN** un paciente existente y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/patients/{id}/deactivate
- **THEN** el status es 404

#### Scenario: Borrado de paciente no existe en la API
- **GIVEN** un paciente existente y un usuario con rol administrador autenticado
- **WHEN** invoca DELETE /api/patients/{id}
- **THEN** el status es 405

### Requirement: Desactivación y reactivación en la API
La API SHALL exponer rutas POST /api/{recurso}/{id}/deactivate y POST /api/{recurso}/{id}/reactivate para profesionales, sillones y prestaciones. La desactivación SHALL autorizarse bajo la acción DELETE y la reactivación bajo la acción UPDATE en RBAC. Ambas responden 200 con la entidad actualizada y son idempotentes.

#### Scenario: Desactivar profesional activo responde 200
- **GIVEN** un profesional activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar profesional inactivo responde 200
- **GIVEN** un profesional inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar profesional ya inactivo responde 200 sin cambios
- **GIVEN** un profesional inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar profesional ya activo responde 200 sin cambios
- **GIVEN** un profesional activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Reactivar profesional inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún profesional y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Profesional no encontrado."

#### Scenario: Desactivar profesional rechazado para rol recepción con 403
- **GIVEN** un profesional existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar profesional rechazado para rol odontólogo con 403
- **GIVEN** un profesional existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar profesional rechazado para rol recepción con 403
- **GIVEN** un profesional inactivo y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar profesional rechazado para rol odontólogo con 403
- **GIVEN** un profesional inactivo y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/professionals/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar sillón activo responde 200
- **GIVEN** un sillón activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar sillón inactivo responde 200
- **GIVEN** un sillón inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar sillón ya inactivo responde 200 sin cambios
- **GIVEN** un sillón inactivo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar sillón ya activo responde 200 sin cambios
- **GIVEN** un sillón activo y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Reactivar sillón inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ningún sillón y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Sillón no encontrado."

#### Scenario: Desactivar sillón rechazado para rol recepción con 403
- **GIVEN** un sillón existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar sillón rechazado para rol odontólogo con 403
- **GIVEN** un sillón existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar sillón rechazado para rol recepción con 403
- **GIVEN** un sillón inactivo y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar sillón rechazado para rol odontólogo con 403
- **GIVEN** un sillón inactivo y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/chairs/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar prestación activa responde 200
- **GIVEN** una prestación activa y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active falso

#### Scenario: Reactivar prestación inactiva responde 200
- **GIVEN** una prestación inactiva y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto tiene active verdadero

#### Scenario: Desactivar prestación ya inactiva responde 200 sin cambios
- **GIVEN** una prestación inactiva y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active falso

#### Scenario: Reactivar prestación ya activa responde 200 sin cambios
- **GIVEN** una prestación activa y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 200
- **AND** el cuerpo devuelto conserva active verdadero

#### Scenario: Desactivar prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Reactivar prestación inexistente responde 404
- **GIVEN** un identificador UUID que no pertenece a ninguna prestación y un usuario con rol administrador autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 404
- **AND** el cuerpo contiene code "NOT_FOUND" y message "Prestación no encontrada."

#### Scenario: Desactivar prestación rechazada para rol recepción con 403
- **GIVEN** una prestación existente y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Desactivar prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación existente y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services/{id}/deactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar prestación rechazada para rol recepción con 403
- **GIVEN** una prestación inactiva y un usuario con rol recepción autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"

#### Scenario: Reactivar prestación rechazada para rol odontólogo con 403
- **GIVEN** una prestación inactiva y un usuario con rol odontólogo autenticado
- **WHEN** invoca POST /api/services/{id}/reactivate
- **THEN** el status es 403
- **AND** el cuerpo contiene code "FORBIDDEN_OPERATION"
