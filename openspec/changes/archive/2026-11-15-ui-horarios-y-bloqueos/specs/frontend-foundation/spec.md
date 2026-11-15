# Spec Delta

## MODIFIED Requirements

### Requirement: Navegación de AppShell sin cajas

La barra de `AppShell` SHALL presentar navegación de texto sin cajas ni fondos de botón, con línea fina inferior en el enlace activo (`aria-current="page"`). El ítem "Horarios y bloqueos" SHALL ser un enlace activo hacia `/horarios` para roles autorizados (administrador, recepción y odontólogo). Los ítems futuros SHALL ser botones deshabilitados con `data-menu-item`, `border: 0` y la etiqueta "Próximamente" en texto plano. En 1440 px, la sesión MUST compartir línea con la navegación.

#### Scenario: Enlaces de navegación activos y bloque de sesión en misma línea en 1440 px

- **GIVEN** una sesión autenticada en escritorio (1440 px)
- **WHEN** se renderiza `AppShell`
- **THEN** los enlaces de navegación se muestran como texto limpio sin cajas de fondo
- **AND** el enlace de la ruta activa ("Agenda") exhibe una línea fina inferior de acento y `aria-current="page"`
- **AND** el bloque de sesión (nombre de usuario y botón "Cerrar sesión") comparte la misma línea horizontal con la marca y la navegación

#### Scenario: Ítems deshabilitados con Próximamente conservan semántica y accesibilidad

- **GIVEN** el menú de navegación renderizado para cualquier rol autenticado
- **WHEN** se evalúa el DOM de los ítems de menú de funcionalidades futuras
- **THEN** los ítems de pantallas no implementadas ("Turnos", "Catálogos", "Pacientes", "Usuarios y roles") siguen siendo botones deshabilitados con `data-menu-item` y la etiqueta "Próximamente"
- **AND** "Horarios y bloqueos" se renderiza como un enlace interactivo sin etiqueta "Próximamente"

#### Scenario: Navegación de AppShell adaptada a tablet (768 px) y móvil (390 px)

- **GIVEN** `AppShell` renderizado en viewports de 768 px y 390 px
- **WHEN** se inspecciona la barra superior
- **THEN** no supera los dos renglones máximos permitidos en 768 px y la navegación de texto permite desplazamiento horizontal fluido
- **AND** esta verificación es visual (capturas a 768 px y 390 px a cargo de Claude)
