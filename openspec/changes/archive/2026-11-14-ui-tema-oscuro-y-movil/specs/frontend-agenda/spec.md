# Spec Delta: frontend-agenda

## ADDED Requirements

### Requirement: Toolbar de agenda compacta con filtros plegables

En pantallas con ancho menor o igual a 640 px, AgendaToolbar SHALL estructurarse en dos filas: el selector de vista con la navegación temporal en una fila, y la fecha con la acción Nuevo turno en otra. Los selectores de Profesional, Sillón y Limpiar filtros SHALL agruparse en una sección plegable controlada por un botón "Filtros" con aria-expanded, que SHALL exponer en su texto la cantidad de filtros activos ("Filtros (N)"). En escritorio, los filtros MUST permanecer visibles.

#### Scenario: Organización compacta de navegación y fecha en celular

- **GIVEN** `AgendaToolbar` renderizado en un viewport móvil <= 640 px
- **WHEN** se evalúa la distribución de los controles
- **THEN** los controles de vista [Día | Semana] y navegación temporal [Anterior | Hoy | Siguiente] ocupan la primera fila
- **AND** el selector de fecha y el botón de acción "Nuevo turno" (si el rol tiene permisos) ocupan la segunda fila
- **AND** la altura total de los controles principales no supera los 110 px

#### Scenario: Botón Filtros con contador de filtros activos y panel accesible

- **GIVEN** `AgendaToolbar` con filtros activos (por ejemplo, sillón preseleccionado) en celular
- **WHEN** se examina el botón de acceso a filtros
- **THEN** el botón expone el texto "Filtros (1)" reflejando la cantidad exacta de filtros aplicados
- **AND** presenta el atributo `aria-expanded="false"` y `aria-controls="agenda-filters-panel"`
- **WHEN** el usuario activa el botón "Filtros"
- **THEN** el panel se expande pasando a `aria-expanded="true"` permitiendo cambiar los selectores de "Profesional", "Sillón" y accionar "Limpiar filtros"

#### Scenario: Toolbar de agenda verificada a 1440, 768 y 390 px

- **GIVEN** la barra de herramientas de la agenda montada con roles autorizados
- **WHEN** se capturan pantallas en 1440 px, 768 px y 390 px
- **THEN** en 1440 px todos los controles se muestran en línea amplia, en 768 px en tres filas balanceadas, y en 390 px compactada en dos filas con filtros plegados
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)

### Requirement: Grilla de agenda con scroll-snap y columna completa en celular

En pantallas con ancho menor o igual a 640 px, AgendaGrid SHALL estructurar el contenedor de grilla con scroll-snap-type: x mandatory, conservando la columna de horas fija con position: sticky a la izquierda. Cada columna de profesional (en modo diario) o día (en modo semanal) SHALL dimensionarse al ancho útil de la pantalla para mostrar una columna completa por vista de desplazamiento. El modo inicial de visualización en AgendaView MUST seguir siendo la grilla.

#### Scenario: Desplazamiento horizontal fluido con scroll-snap y horas fijas

- **GIVEN** `AgendaGrid` con múltiples columnas en un viewport móvil <= 640 px
- **WHEN** el usuario se desplaza horizontalmente por el contenedor de la grilla
- **THEN** el contenedor aplica `scroll-snap-type: x mandatory` alineando cada columna al desplazamiento
- **AND** la columna del eje de horas (`timeGutter`) se mantiene fija a la izquierda con `position: sticky; left: 0;` y z-index superior
- **AND** las tarjetas de turno mantienen visibles la hora y el paciente con prioridad

#### Scenario: Columna completa al ancho útil y preservación de grilla por defecto

- **GIVEN** la vista principal `AgendaView` montada en la aplicación
- **WHEN** se monta el componente sin interacción de usuario
- **THEN** el modo de vista por defecto sigue siendo `"grid"` renderizando `AgendaGrid`
- **AND** en pantallas <= 640 px cada columna de profesional (o día) ocupa el ancho útil disponible del viewport asegurando legibilidad sin truncar nombres

#### Scenario: Grilla de agenda verificada a 1440, 768 y 390 px

- **GIVEN** la grilla de agenda diaria y semanal con turnos y bloqueos cargados
- **WHEN** se inspecciona visualmente en 1440 px, 768 px y 390 px
- **THEN** en 1440 y 768 px se aprecian las columnas simultáneas, y en 390 px se comprueba la columna completa con deslizamiento asistido
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)
