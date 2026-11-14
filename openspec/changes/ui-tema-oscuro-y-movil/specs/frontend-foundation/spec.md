# Spec Delta: frontend-foundation

## ADDED Requirements

### Requirement: AppShell en celular con botón Menú

En pantallas con ancho menor o igual a 640 px, la cabecera de AppShell SHALL presentar una disposición compacta con la marca y la sesión en una fila y un botón interactivo "Menú" ubicado fuera de <nav>. El botón SHALL controlar la visibilidad del menú principal mediante aria-expanded y aria-controls. Al estar expandido, la tecla Escape MUST cerrar el menú y devolver el foco al botón "Menú". En pantallas mayores a 640 px y en entornos sin emulación móvil, el menú SHALL permanecer visible.

#### Scenario: Cabecera compacta y apertura de menú en celular

- **GIVEN** un usuario autenticado en un viewport móvil de 390 px (<= 640 px)
- **WHEN** se monta `AppShell`
- **THEN** la marca y el bloque de sesión comparten una sola fila superior
- **AND** se expone un botón "Menú" con atributo `aria-expanded="false"` y `aria-controls="main-menu"` fuera del elemento `<nav>`
- **WHEN** el usuario activa el botón "Menú"
- **THEN** el botón pasa a `aria-expanded="true"` y el menú principal resulta visible en pantalla

#### Scenario: Cierre del menú con Escape y retorno de foco al botón

- **GIVEN** el menú principal abierto en vista móvil con `aria-expanded="true"`
- **WHEN** el usuario presiona la tecla `Escape`
- **THEN** el menú se cierra pasando a `aria-expanded="false"`
- **AND** el foco del teclado retorna inmediatamente al botón "Menú"
- **AND** el foco no queda atrapado en el menú oculto

#### Scenario: Navegación de AppShell y menú verificados a 1440, 768 y 390 px

- **GIVEN** la aplicación en ejecución con datos reales de demostración
- **WHEN** se inspecciona la barra de navegación en escritorio (1440 px), tablet (768 px) y móvil (390 px)
- **THEN** en 1440 px la barra es horizontal completa, en 768 px no supera dos filas, y en 390 px la cabecera es de fila única con menú desplegable
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)

### Requirement: Modales de la aplicación como hoja inferior en celular

En pantallas con ancho menor o igual a 640 px, la primitiva Dialog y los diálogos modales de appointments SHALL renderizarse como una hoja inferior (bottom sheet) fijada al borde inferior de la pantalla a ancho completo, con esquinas superiores redondeadas, altura máxima de 90dvh y desplazamiento vertical interno. Los botones de acción MUST disponer de un área táctil mínima de 44 px. En pantallas de 768 px o superiores, el diálogo SHALL mantenerse como un modal centrado flotante.

#### Scenario: Hoja inferior a ancho completo con scroll interno en celular

- **GIVEN** cualquiera de los diálogos modales (`AppointmentFormDialog`, `AppointmentDetailDialog` o `AppointmentRescheduleDialog`) abierto en un viewport móvil <= 640 px
- **WHEN** se evalúa la presentación del diálogo en el DOM
- **THEN** el modal se ancla a la parte inferior de la pantalla ocupando el 100% del ancho útil
- **AND** las esquinas superiores presentan bordes redondeados y la altura máxima no excede `90dvh` con scroll vertical interno
- **AND** todos los botones de acción preservan un área táctil mínima de 44 px sin quedar recortados por el borde inferior

#### Scenario: Preservación de modal centrado flotante en tablet y escritorio

- **GIVEN** un diálogo modal abierto en una pantalla con ancho mayor a 640 px (por ejemplo, tablet a 768 px o escritorio a 1440 px)
- **WHEN** se visualiza el diálogo
- **THEN** el diálogo se renderiza como una tarjeta flotante centrada con ancho máximo de 580 px, bordes redondeados completos y backdrop con desenfoque suave

#### Scenario: Modales de turnos verificados a 1440, 768 y 390 px

- **GIVEN** los tres modales de turnos abiertos en navegador
- **WHEN** se capturan en resoluciones de 1440 px, 768 px y 390 px
- **THEN** en 1440 y 768 px se comprueba el centrado y legibilidad, y en 390 px la disposición como hoja inferior con acciones accesibles
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)
