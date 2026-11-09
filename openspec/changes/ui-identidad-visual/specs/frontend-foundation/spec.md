# Spec Delta

## MODIFIED Requirements

### Requirement: Tokens de diseño y colores por estado
Los estilos MUST usar CSS custom properties y CSS Modules. `tokens.css` SHALL definir espaciado (4–48 px), tipografía (12–32 px), la familia base del sistema como fallback, la paleta Aqua (ink, navy, primary, accent, ice, fondo y texto secundario) y el foco visible. `APPOINTMENT_STATUS_TOKENS` SHALL mapear los cinco estados con colores de texto, fondo y borde, con contraste AA >= 4.5:1 en cada par texto/fondo.

#### Scenario: El mapa cubre los cinco estados sin undefined
- **GIVEN** el mapa `APPOINTMENT_STATUS_TOKENS`
- **WHEN** se consultan las claves `reservado`, `confirmado`, `atendido`, `ausente` y `cancelado`
- **THEN** las cinco devuelven un objeto con `text`, `background` y `border`
- **AND** ninguna devuelve `undefined`

#### Scenario: Cada par texto y fondo cumple contraste AA
- **GIVEN** los pares de `APPOINTMENT_STATUS_TOKENS`
- **WHEN** se calcula el ratio de contraste de cada par texto/fondo
- **THEN** `reservado` `#1F5F86` sobre `#E4F2F8` es 6.04:1
- **AND** `confirmado` `#146C43` sobre `#DDF3E4` es 5.53:1, `atendido` `#334155` sobre `#E2E8F0` es 8.40:1, `ausente` `#8A4B08` sobre `#FCEFD6` es 5.97:1 y `cancelado` `#A11D1D` sobre `#FBE3E3` es 6.35:1
- **AND** los cinco ratios son al menos 4.5:1

#### Scenario: Los tokens de paleta usados como texto cumplen contraste AA
- **GIVEN** los tokens de la paleta Aqua que se usan como texto
- **WHEN** se calcula el contraste contra su fondo correspondiente
- **THEN** `--color-text` `#0F2A3D` sobre `--color-background` `#F2F8FA` es 13.80:1
- **AND** `--color-text-muted` `#4A6472` sobre `--color-background` `#F2F8FA` es 5.83:1
- **AND** `--color-primary-contrast` `#FFFFFF` sobre `--color-primary` `#0B6E7F` es 5.91:1
- **AND** los tokens decorativos (`--color-navy`, `--color-accent`, `--color-ice`) quedan excluidos de la exigencia de texto

#### Scenario: El foco es visible
- **GIVEN** un elemento interactivo con la clase de foco del sistema de tokens
- **WHEN** recibe foco por teclado
- **THEN** se aplica un `outline` de 2 px con `--color-focus`
- **AND** el estilo usa el selector `:focus-visible`

#### Scenario: La familia base del sistema se conserva como fallback
- **GIVEN** el archivo `tokens.css` y el `reset.css`
- **WHEN** se inspecciona `--font-family-base`
- **THEN** su valor es el system font stack existente
- **AND** `body` sigue declarando `font-family: var(--font-family-base)` como fallback

## ADDED Requirements

### Requirement: Tipografías autoalojadas sin CDN
La aplicación SHALL cargar Jost para títulos y Manrope para texto desde paquetes npm `@fontsource-variable` importados en el entry point del frontend. MUST NOT cargar fuentes desde un CDN, desde Google Fonts ni mediante un `<link>` remoto. Las familias MUST aplicarse a través de tokens semánticos con fallback al system font stack.

#### Scenario: Las dependencias y los imports de fuentes están en el frontend
- **GIVEN** `frontend/package.json` y `frontend/src/main.tsx`
- **WHEN** se inspeccionan las dependencias y los imports del entry point
- **THEN** `@fontsource-variable/jost` y `@fontsource-variable/manrope` figuran en `dependencies`
- **AND** `main.tsx` importa ambos paquetes antes de los estilos de la aplicación

#### Scenario: No hay fuentes externas ni CDN
- **GIVEN** el código y los estilos de `frontend/src`
- **WHEN** se busca cualquier URL de fuentes externa
- **THEN** no aparece `fonts.googleapis.com`, `fonts.gstatic.com` ni ninguna URL de CDN de fuentes
- **AND** las tipografías se sirven desde los archivos empaquetados por Vite

#### Scenario: Las familias se aplican con tokens y fallback
- **GIVEN** `tokens.css` y `reset.css`
- **WHEN** se renderiza una pantalla
- **THEN** `--font-family-heading` usa `"Jost Variable"` y `--font-family-body` usa `"Manrope Variable"`
- **AND** ambos tokens incluyen el system font stack como fallback
- **AND** los títulos usan `var(--font-family-heading)` y el texto usa `var(--font-family-body)`

### Requirement: Barra única con la marca Aqua
La aplicación SHALL mostrar una única barra de encabezado con el logo de Aqua, el texto "Aqua" y el texto "Clínica Odontológica". En viewport de tablet (<= 768 px) SHALL mostrar solo "Aqua" y MUST NOT superar dos renglones. La barra sobre fondo claro MUST usar la variante de logo pensada para fondo claro y MUST NOT crear una segunda barra.

#### Scenario: Barra de escritorio con la marca completa
- **GIVEN** una sesión autenticada en escritorio (1440 px)
- **WHEN** se renderiza el shell de la aplicación
- **THEN** existe una sola barra de encabezado
- **AND** la barra muestra el logo, "Aqua" y "Clínica Odontológica"

#### Scenario: Barra de tablet con solo Aqua y máximo dos renglones
- **GIVEN** un viewport de 768 px con una sesión autenticada
- **WHEN** se renderiza el shell de la aplicación
- **THEN** la barra muestra el logo y el texto "Aqua"
- **AND** "Clínica Odontológica" no se muestra
- **AND** la barra ocupa como máximo dos renglones
- **AND** esta verificación es visual (captura a 768 px), no un test de Vitest

#### Scenario: La barra clara usa la variante de logo oscura
- **GIVEN** la barra de encabezado sobre fondo claro
- **WHEN** se inspecciona la imagen del logo
- **THEN** se usa `frontend/src/assets/brand/logo-aqua-oscuro.png`
- **AND** no se usa la variante clara en la barra

### Requirement: Créditos de assets y tipografías
El `README.md` SHALL incluir una sección de créditos que nombre las cinco fotografías del login, el logo de Aqua y la licencia de las tipografías Jost y Manrope distribuidas por Fontsource.

#### Scenario: El README acredita fotos, logo y tipografías
- **GIVEN** el `README.md` del repositorio
- **WHEN** se busca la sección de créditos
- **THEN** la sección nombra las cinco fotografías y el logo de Aqua
- **AND** indica que Jost y Manrope se distribuyen con licencia SIL Open Font License mediante Fontsource
