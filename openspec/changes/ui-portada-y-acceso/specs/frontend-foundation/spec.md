# frontend-foundation Specification

## Purpose

Definir los tokens de layout y superficies de la portada, login y modales de la agenda (superficie navy oscura translúcida y superficie clara suave marfil-hielo para `Dialog`, `AppointmentFormDialog`, `AppointmentDetailDialog` y `AppointmentRescheduleDialog`) y la navegación de `AppShell` estilizada sin cajas contenedoras con la etiqueta "Próximamente" como texto secundario sin pastilla.

## ADDED Requirements

### Requirement: Tokens de layout y superficies

`tokens.css` SHALL definir `--landing-hero-min-height: 60vh`, `--landing-content-max-width: 1120px` y tokens de superficie: navy translúcida para login/portada y marfil-hielo para los modales de la agenda. MUST asegurar contraste AA (>= 4.5:1) en todo texto y fallback sólido sin `backdrop-filter`. El accent `#54ACBF` MAY usarse como texto o línea solo sobre navy `#011C40` (6,47:1); sobre fondo claro MUST seguir siendo decorativo.

#### Scenario: Tokens de layout y contraste AA de superficies

- **GIVEN** `tokens.css` y los estilos de portada, login y modales
- **WHEN** se inspeccionan las custom properties y los ratios de contraste
- **THEN** `--landing-hero-min-height` vale `60vh` y `--landing-content-max-width` vale `1120px`
- **AND** los textos claros sobre fondo navy `#011C40` (blanco `16,92:1`, ice `#A7EBF2` `12,73:1`, accent `#54ACBF` `6,47:1`) superan el umbral AA de 4.5:1
- **AND** el texto `--color-text` `#011C40` sobre la superficie marfil-hielo translúcida `rgba(243, 247, 250, 0.95)` alcanza un contraste de `15.70:1` (AA / AAA)
- **AND** el accent `#54ACBF` solo aparece como texto o línea sobre superficies navy y nunca como texto sobre fondo claro

#### Scenario: Fallback sólido sin soporte de backdrop-filter

- **GIVEN** un navegador que no soporta la propiedad CSS `backdrop-filter`
- **WHEN** se renderiza la superficie del formulario de login o de un modal
- **THEN** se aplica la regla `@supports not (backdrop-filter: blur(1px))` (o background sólido de base)
- **AND** la superficie provee fondo opaco navy o marfil-hielo sin transparencias rotas ni pérdida de legibilidad

#### Scenario: Superficie clara suave de modales verificada a 1440, 768 y 390 px

- **GIVEN** cualquiera de los diálogos modales de la agenda (`AppointmentFormDialog`, `AppointmentDetailDialog` o `AppointmentRescheduleDialog`) abierto sobre la vista
- **WHEN** se inspecciona en navegador real a 1440 px, 768 px y 390 px
- **THEN** la superficie exhibe el fondo marfil-hielo translúcido, `::backdrop` con desenfoque suave, borde fino de 1 px y sombra sutil
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)

### Requirement: Navegación de AppShell sin cajas

La barra de `AppShell` SHALL presentar navegación de texto sin cajas contenedoras ni fondos de botón, con línea fina inferior en el enlace activo (`aria-current="page"`) y la etiqueta "Próximamente" como texto secundario plano sin pastilla ni borde. En 1440 px, el bloque de sesión MUST alinearse en la misma línea que la marca y navegación. Los ítems deshabilitados MUST conservar la semántica accesible de botón deshabilitado con `data-menu-item` para no alterar tests existentes.

#### Scenario: Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px

- **GIVEN** una sesión autenticada en escritorio (1440 px)
- **WHEN** se renderiza `AppShell`
- **THEN** los enlaces de navegación se muestran como texto limpio sin cajas de fondo
- **AND** el enlace de la ruta activa ("Agenda") exhibe una línea fina inferior de acento y `aria-current="page"`
- **AND** el bloque de sesión (nombre de usuario y botón "Cerrar sesión") comparte la misma línea horizontal con la marca y la navegación

#### Scenario: Ítems deshabilitados con Próximamente conservan semántica y accesibilidad

- **GIVEN** el menú de navegación renderizado para cualquier rol autenticado
- **WHEN** se evalúa el DOM de los ítems de menú de funcionalidades futuras
- **THEN** cada ítem sigue siendo un elemento `<button disabled data-menu-item="...">` accesible por teclado y Testing Library
- **AND** la etiqueta "Próximamente" se renderiza con estilos de texto secundario atenuado, sin borde exterior ni caja de pastilla

#### Scenario: Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px)

- **GIVEN** `AppShell` renderizado en viewports de 768 px y 390 px
- **WHEN** se inspecciona la barra superior
- **THEN** no supera los dos renglones máximos permitidos en 768 px y la navegación de texto permite desplazamiento horizontal fluido
- **AND** esta verificación es visual (capturas a 768 px y 390 px a cargo de Claude)
