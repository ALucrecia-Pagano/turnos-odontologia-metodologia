# frontend-landing Specification

## Purpose

Definir la portada pública editorial de Aqua en `/` para usuarios anónimos (pantalla completa, overlay navy sobre el carrusel, navegación de texto sin cajas, `<h1>` con logo claro, eslogan, CTA primario, badge de demo, secciones editoriales en dos columnas con reveal lateral `translateX` y teléfono ficticio) y la página intermedia `/acceso` con tres tarjetas de rol oscuras hacia `/login`.

## ADDED Requirements

### Requirement: Portada pública en la raíz

La ruta `/` SHALL mostrar para usuarios anónimos la portada a pantalla completa con el carrusel bajo overlay navy, navegación superior de texto sin cajas (`Inicio`, `La clínica`, `Acceder`), `<h1>` con el logo (`alt="Aqua — Clínica Odontológica"`), eslogan "Claridad en cada cuidado.", CTA "Explorar la clínica →", badge "Sitio de demostración" y franja de estado. Con sesión autenticada, `/` MUST conservar la redirección con replace a `/agenda` según el Clock.

#### Scenario: Portada completa para anónimo en /

- **GIVEN** un usuario anónimo navegando a `/`
- **WHEN** la aplicación monta la ruta raíz
- **THEN** se renderiza la portada pública con el carrusel bajo el overlay navy
- **AND** el encabezado de nivel 1 expone el nombre accesible "Aqua — Clínica Odontológica" mediante el `alt` del logo claro
- **AND** son visibles el eslogan "Claridad en cada cuidado.", el CTA "Explorar la clínica →", el badge "Sitio de demostración" y los enlaces de texto de navegación
- **AND** la navegación superior expone `aria-current="page"` en el enlace activo

#### Scenario: Usuario autenticado en / redirige a agenda

- **GIVEN** un usuario con sesión autenticada navegando a `/`
- **WHEN** la aplicación evalúa la ruta raíz
- **THEN** se ejecuta `RootRedirect` con replace hacia `/agenda?date=<fecha_actual>`
- **AND** la portada pública no se renderiza

#### Scenario: Adaptabilidad de la portada en 1440, 768 y 390 px

- **GIVEN** la portada pública montada en un navegador real
- **WHEN** se inspecciona en viewports de 1440 px, 768 px y 390 px
- **THEN** el hero cubre la pantalla completa sin desbordes horizontales
- **AND** los enlaces de texto superiores se mantienen legibles y alineados
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude), no un test de jsdom

### Requirement: Secciones editoriales con reveal lateral

La portada SHALL presentar las cuatro secciones editoriales "01 / Quiénes somos", "02 / Servicios", "03 / Equipo" y "04 / Horarios y contacto" en dos columnas con teléfono ficticio "(0261) 555-0101". `RevealSection` SHALL aplicar animación lateral (`translateX` y opacidad entre 200 y 250 ms) al hacer scroll. Ante `prefers-reduced-motion` o sin `IntersectionObserver`, el contenido MUST mostrarse visible de inmediato sin desplazamiento ni transición.

#### Scenario: Secciones editoriales entran con animación lateral al scrollear

- **GIVEN** la portada pública con un observador de intersección inyectado
- **WHEN** el usuario scrollea hacia las secciones informativas
- **THEN** cada sección transiciona de pendiente a revelada con `translateX` y opacidad en 200-250 ms
- **AND** se muestran los títulos "01 / Quiénes somos", "02 / Servicios", "03 / Equipo" y "04 / Horarios y contacto"
- **AND** la sección de contacto incluye el teléfono ficticio "(0261) 555-0101" y la franja de estado de demostración

#### Scenario: Reduced motion desactiva la animación lateral y deja el contenido visible

- **GIVEN** la portada pública con `prefers-reduced-motion` activado o en un entorno sin `IntersectionObserver`
- **WHEN** se evalúa `RevealSection`
- **THEN** la sección se monta inmediatamente con estado revelado
- **AND** no se aplica desplazamiento lateral `translateX` ni transición temporal
- **AND** todo el contenido editorial permanece accesible y visible en el DOM

#### Scenario: Secciones editoriales se adaptan a dos columnas en 1440 px y una columna en 768 y 390 px

- **GIVEN** la portada pública renderizada en navegador real
- **WHEN** se observa el layout de las secciones editoriales a 1440 px, 768 px y 390 px
- **THEN** en escritorio (1440 px) el contenido se distribuye en dos columnas editoriales
- **AND** en tablet (768 px) y móvil (390 px) se apila en una sola columna con espaciado vertical armonioso
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)

### Requirement: Página de acceso por rol

La ruta `/acceso` SHALL mostrar la vista "¿Cómo querés ingresar?" con tres tarjetas-enlace oscuras con borde de 1 px para Recepción, Odontología y Administración dirigidas a `/login?rol=recepcion|odontologo|administrador`. MUST incluir el texto visible "El rol se confirma al ingresar", el enlace de texto "← Volver a Aqua" sin caja y aclarar el borde en hover y focus. El rol de la URL MUST ser solo presentacional y no otorgar permisos.

#### Scenario: Navegación desde las tres tarjetas de rol hacia login

- **GIVEN** un usuario en `/acceso`
- **WHEN** se examinan las tres tarjetas de rol disponibles
- **THEN** existen enlaces accesibles para "Recepción" (`/login?rol=recepcion`), "Odontología" (`/login?rol=odontologo`) y "Administración" (`/login?rol=administrador`)
- **AND** se muestra el texto explicativo "El rol se confirma al ingresar"
- **AND** las tarjetas presentan superficie oscura con borde sutil de 1 px que resalta al recibir foco o hover

#### Scenario: Navegación de retorno con el enlace Volver a Aqua

- **GIVEN** la pantalla `/acceso`
- **WHEN** se activa el enlace "← Volver a Aqua"
- **THEN** la aplicación navega hacia la portada pública `/`
- **AND** el enlace se renderiza como texto limpio sin contenedor de caja ni bordes tipo botón

#### Scenario: Adaptabilidad de las tarjetas de acceso en 1440, 768 y 390 px

- **GIVEN** la página `/acceso` en un navegador real
- **WHEN** se inspecciona en viewports de 1440 px, 768 px y 390 px
- **THEN** las tres tarjetas se despliegan en fila horizontal en 1440 px y se reorganizan fluidamente en 768 px y 390 px sin recortar textos ni desbordar la ventana
- **AND** esta verificación es visual (capturas a 1440, 768 y 390 px a cargo de Claude)
