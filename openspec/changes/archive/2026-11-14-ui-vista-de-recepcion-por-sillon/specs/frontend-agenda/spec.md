# Spec Delta

## ADDED Requirements

### Requirement: Vista de recepción por sillón

La aplicación SHALL ofrecer un modo de vista `view=chair` en `/agenda` con la etiqueta visible «Sillones». Al activarlo, la aplicación MUST renderizar columnas por sillón y MUST conservar `date`, `professionalId` y `chairId`. `view=day`, un valor desconocido o la ausencia de `view` MUST seguir mostrando la vista diaria por profesional.

#### Scenario: Activar Sillones conserva fecha y filtros

- **GIVEN** una sesión de `recepcion` en `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1` en vista diaria
- **WHEN** el usuario pulsa el control «Sillones»
- **THEN** la URL pasa a `/agenda?date=2026-11-18&professionalId=00000000-0000-0000-0000-000000000001&chairId=00000000-0000-0000-0000-0000000000b1&view=chair`
- **AND** se muestra la vista por sillón del 18 de noviembre de 2026

#### Scenario: Un view desconocido sigue cayendo a Día

- **GIVEN** una sesión autenticada en `/agenda?date=2026-11-16&view=otro`
- **WHEN** se renderiza la página
- **THEN** la vista activa es la vista diaria por profesional
- **AND** el botón «Día» figura seleccionado

### Requirement: Columnas por sillón

En `view=chair`, cada columna MUST corresponder a un sillón del catálogo `GET /api/chairs` y MUST incluir además los sillones que aparezcan en turnos del día aunque falten del catálogo. Las columnas MUST ordenarse por nombre y los inactivos MUST mostrarse como «Sillón N (inactivo)». Con `chairId` en la URL MUST mostrarse solo esa columna.

#### Scenario: Turnos de distintos profesionales en la misma columna

- **GIVEN** el lunes 2026-11-16 con Sillón 1, Sillón 2 y Sillón 3, y dos turnos en Sillón 1: Quiroga 10:00–10:30 y Sosa 11:00–11:30
- **WHEN** termina la carga de la vista `view=chair`
- **THEN** se ven tres columnas «Sillón 1», «Sillón 2» y «Sillón 3»
- **AND** la columna Sillón 1 contiene las dos tarjetas
- **AND** cada tarjeta muestra en texto su profesional («Dra. Laura Quiroga» y «Dr. Martín Sosa»)

#### Scenario: Sillón sin turnos

- **GIVEN** el lunes 2026-11-16 con horarios de Quiroga y Benítez 09:00–13:00 y 15:00–19:00, y de Sosa solo 09:00–13:00
- **AND** el Sillón 2 sin turnos
- **WHEN** se renderiza la columna del Sillón 2
- **THEN** se ven «Libre 09:00–13:00» y «Libre 15:00–19:00»
- **AND** se rotula «Fuera de horario 13:00–15:00»
- **AND** la columna no se oculta

#### Scenario: Filtro de un solo sillón

- **GIVEN** la URL `/agenda?date=2026-11-16&view=chair&chairId=00000000-0000-0000-0000-0000000000b2`
- **WHEN** se renderiza la vista
- **THEN** solo se ve la columna «Sillón 2»
- **AND** las demás columnas no se renderizan

#### Scenario: Sillón inactivo visible

- **GIVEN** el catálogo con «Sillón 2» y `active: false`, y un turno del día en ese sillón
- **WHEN** se renderiza la vista por sillón
- **THEN** la columna muestra «Sillón 2 (inactivo)»
- **AND** el turno sigue visible en esa columna

### Requirement: Disponibilidad por sillón con texto

En `view=chair`, la aplicación SHALL mostrar los huecos libres como bloques con texto visible «Libre HH:MM–HH:MM» y nombre accesible, y los tramos sin atención como «Fuera de horario HH:MM–HH:MM». Los huecos menores a 15 minutos MUST NOT rotularse. `reservado`, `confirmado` y `atendido` MUST ocupar agenda; `cancelado` y `ausente` MUST liberarla.

#### Scenario: Hueco libre entre dos turnos

- **GIVEN** el Sillón 1 con Quiroga 10:00–10:30 y Sosa 11:00–11:30, dentro del horario de atención
- **WHEN** se renderiza la columna
- **THEN** se ve un bloque con texto «Libre 10:30–11:00»
- **AND** el bloque expone el nombre accesible «Sillón 1 libre de 10:30 a 11:00»

#### Scenario: Un cancelado no ocupa el sillón

- **GIVEN** el Sillón 1 con un turno cancelado de Sosa de 09:00 a 09:30 y sin otros turnos en ese tramo
- **WHEN** se renderiza la columna
- **THEN** el tramo 09:00–09:30 aparece como «Libre 09:00–09:30»
- **AND** el turno cancelado permanece visible con el texto «Cancelado»

#### Scenario: La disponibilidad no depende solo del color

- **GIVEN** la vista por sillón con huecos libres y tramos fuera de horario
- **WHEN** se consultan los bloques de disponibilidad
- **THEN** cada bloque comunica su estado con texto visible
- **AND** no depende únicamente del color de fondo

### Requirement: Eje horario y día de la vista por sillón

El eje de la vista por sillón SHALL cubrir la unión de horarios de atención del día, desde el mínimo inicio al máximo fin, sin margen artificial. Los huecos internos MUST rotularse «Fuera de horario». Un día sin horarios MUST mostrar «No hay horarios de atención para este día», eje de respaldo 08:00–20:00 y ningún bloque «Libre» inventado.

#### Scenario: Eje con la unión de horarios del día

- **GIVEN** el lunes 2026-11-16 con Quiroga y Benítez 09:00–13:00 y 15:00–19:00, y Sosa 09:00–13:00
- **WHEN** se calcula el eje de la vista por sillón
- **THEN** el eje va de 09:00 a 19:00
- **AND** el tramo 13:00–15:00 se rotula «Fuera de horario»

#### Scenario: Día sin horarios de atención

- **GIVEN** el sábado 2026-11-21 sin horarios de atención
- **WHEN** se renderiza la vista por sillón
- **THEN** se muestra el aviso «No hay horarios de atención para este día»
- **AND** el eje va de 08:00 a 20:00
- **AND** no se muestran bloques «Libre»

### Requirement: Día por defecto y navegación en vista por sillón

La fecha inicial MUST calcularse con el `Clock` inyectado, igual que la vista diaria, y `Anterior`/`Siguiente` MUST desplazar exactamente un día calendario. La consulta MUST usar `from=to=<fecha>` en una sola llamada a `GET /api/agenda`.

#### Scenario: Día por defecto desde el Clock

- **GIVEN** un `Clock` fijo en `2026-11-16T12:00:00Z` y `/agenda?view=chair` sin `date`
- **WHEN** se monta la página
- **THEN** se pide `GET /api/agenda?from=2026-11-16&to=2026-11-16`
- **AND** se muestra el lunes 16 de noviembre de 2026

#### Scenario: Navegación de un día

- **GIVEN** la URL `/agenda?date=2026-11-16&view=chair`
- **WHEN** se pulsa «Siguiente»
- **THEN** la URL pasa a `/agenda?date=2026-11-17&view=chair`
- **AND** se pide la agenda del 2026-11-17

### Requirement: Tarjeta de turno con profesional y detalle

En `view=chair`, cada tarjeta MUST mostrar en texto el nombre del profesional además de hora, paciente y estado, y MUST seguir siendo un `<button type="button">` con foco visible. Al activarla MUST abrirse `AppointmentDetailDialog` con ese turno. El nombre accesible MUST incluir hora, paciente, profesional, sillón, prestación y estado.

#### Scenario: Clic en la tarjeta abre el detalle

- **GIVEN** la vista por sillón del 2026-11-16 con el turno de Quiroga 10:00–10:30 en Sillón 1
- **WHEN** el usuario hace clic en la tarjeta del turno
- **THEN** se abre `AppointmentDetailDialog` con ese turno
- **AND** la tarjeta muestra en texto «Dra. Laura Quiroga»

#### Scenario: Nombre accesible completo en la tarjeta

- **GIVEN** el turno de Quiroga de 10:00 a 10:30 con Ana Pérez en Sillón 1 y «Control»
- **WHEN** se consulta la tarjeta en la vista por sillón
- **THEN** su nombre accesible incluye «10:00–10:30», «Ana Pérez», «Dra. Laura Quiroga», «Sillón 1», «Control» y «Reservado»

### Requirement: Acceso por rol a la vista por sillón

El control «Sillones» MUST renderizarse solo para sesiones con rol `recepcion` o `administrador`. El rol `odontologo` MUST NOT ver el control y, si accede con `view=chair` en la URL, la vista MUST caer a Día y la URL MUST normalizarse sin `view=chair`.

#### Scenario: Recepción y administración ven el control

- **GIVEN** una sesión con rol `recepcion` o `administrador`
- **WHEN** se renderiza la barra de herramientas de `/agenda`
- **THEN** se ve el botón «Sillones» junto a «Día» y «Semana»

#### Scenario: Odontólogo sin acceso

- **GIVEN** una sesión con rol `odontologo`
- **WHEN** se abre `/agenda?view=chair`
- **THEN** el botón «Sillones» no está en el DOM
- **AND** la vista activa es Día y la URL no conserva `view=chair`

### Requirement: Filtros en la vista por sillón

En `view=chair`, los filtros `professionalId` y `chairId` MUST seguir disponibles y combinables en la URL. `chairId` MUST reducir las columnas a ese sillón; `professionalId` MUST filtrar los turnos y recalcular la unión de horarios con ese profesional. La ayuda del filtro de sillón MUST adaptarse porque la columna ya es el sillón.

#### Scenario: El filtro de sillón reduce las columnas

- **GIVEN** la vista por sillón del 2026-11-16 con el filtro del Sillón 2
- **WHEN** se aplica el filtro
- **THEN** la URL incluye `chairId=00000000-0000-0000-0000-0000000000b2`
- **AND** solo se renderiza la columna «Sillón 2»

#### Scenario: El filtro de profesional recalcula los horarios

- **GIVEN** la vista por sillón del 2026-11-16 con el filtro de Sosa, que atiende solo 09:00–13:00
- **WHEN** se aplica el filtro
- **THEN** solo se muestran los turnos de Sosa
- **AND** la unión de horarios de atención se recalcula a 09:00–13:00
- **AND** no se muestran bloques «Libre» de la tarde

#### Scenario: La ayuda del filtro de sillón se adapta

- **GIVEN** la vista por sillón con `chairId` activo
- **WHEN** se renderiza la barra de herramientas
- **THEN** no se muestra el texto que dice que el filtro solo afecta los turnos
- **AND** se muestra una leyenda adaptada a la vista por sillón

### Requirement: Lista y estado vacío en la vista por sillón

En `view=chair`, el toggle «Ver como lista» MUST seguir visible y la tabla MUST incluir la columna Sillón. Un día sin turnos MUST mantener visible la grilla con las bandas «Libre» y un aviso informativo; el único vacío real MUST ser «No hay sillones configurados» cuando el catálogo está vacío.

#### Scenario: La lista sigue disponible

- **GIVEN** la vista por sillón del 2026-11-16 con turnos en distintos sillones
- **WHEN** el usuario pulsa «Ver como lista»
- **THEN** se renderiza la tabla con la columna «Sillón»
- **AND** cada fila muestra su sillón y su profesional

#### Scenario: Un día sin turnos conserva la grilla

- **GIVEN** la vista por sillón de un día con horarios de atención pero sin turnos
- **WHEN** termina la carga
- **THEN** se mantiene la grilla con las bandas «Libre»
- **AND** se muestra un aviso informativo de que no hay turnos para ese día

#### Scenario: Catálogo de sillones vacío

- **GIVEN** la vista por sillón sin sillones en el catálogo y sin turnos
- **WHEN** termina la carga
- **THEN** se muestra el vacío «No hay sillones configurados»

### Requirement: Adaptabilidad de la vista por sillón

La vista por sillón MUST usar el mismo contenedor de grilla de día y semana definido por C-36, con scroll-snap y columna completa en celular (≤ 640 px). C-31 MUST NOT crear un contenedor, un scroll ni un selector de sillón móvil propios. La verificación MUST incluir capturas a 1440, 768 y 390 px antes de archivar.

#### Scenario: Capturas a 1440, 768 y 390 px

- **GIVEN** la vista por sillón con tres sillones
- **WHEN** se toman capturas a 1440, 768 y 390 px
- **THEN** a 1440 entran las tres columnas y el gutter
- **AND** a 768 la barra de herramientas se envuelve y las tres columnas entran en el contenedor heredado
- **AND** a 390 el contenedor de C-36 muestra una columna completa con scroll-snap y las tarjetas compactas mantienen legibles hora, paciente, profesional y estado
