# Spec Delta

## Purpose

Definir la portada pública de Aqua en `/login`: el hero con marca y carrusel, las secciones informativas con datos ficticios, el diálogo de acceso que se abre al entrar y el reveal accesible. La portada presenta la clínica sin iniciar sesión y deja el formulario a un clic, sin cambiar rutas ni reglas de autenticación.

## ADDED Requirements

### Requirement: Portada pública en /login

La ruta `/login` SHALL mostrar la portada pública de Aqua para usuarios anónimos, con el diálogo de acceso abierto al entrar. MUST NOT agregar rutas nuevas ni cambiar el orden de `createAppRoutes`; `/` sigue redirigiendo al anónimo a `/login`.

#### Scenario: La portada se muestra en /login

- **GIVEN** un usuario anónimo en la ruta `/login`
- **WHEN** se renderiza la aplicación
- **THEN** se ve el hero, las cuatro secciones y el diálogo de acceso abierto
- **AND** `createAppRoutes` conserva la misma cantidad y el mismo orden de rutas

#### Scenario: El anónimo en / sigue llegando a la portada

- **GIVEN** un usuario anónimo en la ruta `/`
- **WHEN** se renderiza la aplicación
- **THEN** la aplicación redirige a `/login`
- **AND** se ve la portada pública con el diálogo abierto

#### Scenario: El autenticado en /login no ve la portada

- **GIVEN** un usuario autenticado
- **WHEN** navega a `/login`
- **THEN** `PublicOnlyRoute` lo redirige a `from` o a `/`
- **AND** la portada no se renderiza

### Requirement: Hero con marca, carrusel y llamada a la acción

El hero SHALL ocupar al menos 60vh y mostrar el logo claro dentro del `<h1>` con `alt="Aqua — Clínica Odontológica"`, la bajada exacta "Claridad en cada cuidado.", un lead, el badge "Sitio de demostración" y el CTA "Ingresar al sistema". La marca MUST anunciarse una sola vez.

#### Scenario: La marca se anuncia una sola vez

- **GIVEN** el hero renderizado
- **WHEN** se consulta el encabezado de nivel 1
- **THEN** su nombre accesible es "Aqua — Clínica Odontológica"
- **AND** el logo está dentro del `<h1>` y no hay un texto de marca duplicado al lado

#### Scenario: El CTA y el submit tienen nombres distintos

- **GIVEN** el diálogo de acceso abierto sobre la portada
- **WHEN** se consultan los botones por rol y nombre
- **THEN** existe un único botón "Ingresar" (submit del formulario)
- **AND** existe un botón "Ingresar al sistema" (CTA del hero)
- **AND** el CTA no está oculto con `aria-hidden` ni excluido con `tabIndex={-1}`

#### Scenario: El carrusel del hero se reutiliza

- **GIVEN** el hero renderizado
- **WHEN** se inspeccionan las imágenes del carrusel
- **THEN** se muestran las cinco fotos decorativas de C-34
- **AND** está disponible el botón "Pausar animación" o "Reanudar animación"

#### Scenario: El hero mide al menos 60vh

- **GIVEN** la portada renderizada en un navegador real
- **WHEN** se mide el alto visible del hero
- **THEN** ocupa al menos el 60% del alto del viewport
- **AND** esta verificación es visual (captura), no un test de Vitest

#### Scenario: El badge de demostración es visible

- **GIVEN** el hero renderizado
- **WHEN** se consulta el texto del hero
- **THEN** se lee "Sitio de demostración"

### Requirement: Secciones informativas con datos ficticios

La portada SHALL incluir cuatro secciones —Quiénes somos, Servicios, Equipo y Horarios y contacto— con datos ficticios del seed y un `<h2>` por sección. MUST mostrar el badge "Sitio de demostración" y una nota visible de datos ficticios en "Horarios y contacto".

#### Scenario: Las cuatro secciones están en el DOM

- **GIVEN** la portada renderizada sin `IntersectionObserver`
- **WHEN** se consultan los encabezados de nivel 2
- **THEN** se leen "Quiénes somos", "Servicios", "Equipo" y "Horarios y contacto"
- **AND** las cuatro secciones están visibles, sin estado pendiente

#### Scenario: El equipo coincide con el seed

- **GIVEN** la sección Equipo
- **WHEN** se consultan los profesionales
- **THEN** aparecen el Dr. Martín Sosa, la Dra. Laura Quiroga y la Dra. Paula Benítez
- **AND** no se usan datos reales de pacientes

#### Scenario: Los servicios y duraciones coinciden con el seed

- **GIVEN** la sección Servicios
- **WHEN** se consultan las prestaciones
- **THEN** aparecen Limpieza (45 min), Extracción (60 min), Restauración (60 min), Control (30 min) y Blanqueamiento (90 min)

#### Scenario: Los horarios coinciden con el seed

- **GIVEN** la sección Horarios y contacto
- **WHEN** se consulta el texto de horarios
- **THEN** se lee lunes a viernes de 9:00 a 13:00 y de 15:00 a 19:00
- **AND** se aclara que el Dr. Sosa atiende solo por la mañana

#### Scenario: Los datos ficticios se marcan visiblemente

- **GIVEN** la portada renderizada
- **WHEN** se recorre el hero y la sección Horarios y contacto
- **THEN** el badge "Sitio de demostración" es visible en el hero
- **AND** la nota de datos ficticios es visible en Horarios y contacto
- **AND** el teléfono de contacto es "(0261) 555-0101"

### Requirement: Diálogo de acceso

El diálogo de acceso SHALL abrirse al entrar a `/login`, con heading "Turnos Odontología", el formulario de login y un botón visible "Ver la clínica" que lo cierra. MUST mostrar el mensaje de sesión vencida dentro del formulario cuando corresponda.

#### Scenario: El diálogo se abre al entrar

- **GIVEN** un usuario anónimo que entra a `/login`
- **WHEN** la portada termina de montar
- **THEN** el diálogo está abierto y expone el rol `dialog`
- **AND** contiene el heading "Turnos Odontología" y el formulario "Iniciar sesión"

#### Scenario: Ver la clínica cierra el diálogo

- **GIVEN** el diálogo abierto sobre la portada
- **WHEN** se activa el botón "Ver la clínica"
- **THEN** el diálogo se cierra
- **AND** la portada queda recorrible y visible

#### Scenario: El mensaje de sesión vencida cae en el formulario

- **GIVEN** un usuario que llega a `/login` con el flag de sesión vencida
- **WHEN** el diálogo se abre
- **THEN** el mensaje de `SESSION_EXPIRED_MESSAGE` se muestra como `role="alert"`
- **AND** el mensaje está dentro del formulario, no en la portada

#### Scenario: Los nombres de los botones no colisionan

- **GIVEN** el diálogo abierto
- **WHEN** se consultan los botones por rol y nombre
- **THEN** hay un único "Ingresar" y un "Ingresar al sistema"
- **AND** "Ver la clínica" es visible y accesible por teclado

#### Scenario: El diálogo tiene backdrop y tarjeta tipo vidrio

- **GIVEN** el diálogo abierto en un navegador real
- **WHEN** se observa la superficie del diálogo
- **THEN** hay un backdrop que oscurece la portada
- **AND** el formulario está en una tarjeta tipo vidrio sobre overlay degradado navy
- **AND** esta verificación es visual (captura), no un test de Vitest

#### Scenario: El foco queda atrapado en el diálogo

- **GIVEN** el diálogo abierto con `showModal` en un navegador real
- **WHEN** se tabula repetidamente
- **THEN** el foco recorre solo los controles del diálogo
- **AND** esta verificación es visual (captura), no un test de Vitest

### Requirement: Foco y scroll del diálogo de acceso

Al abrir el diálogo, el foco SHALL quedar en el campo Usuario. Mientras esté abierto, el scroll del fondo MUST quedar bloqueado y MUST restaurarse al cerrarlo.

#### Scenario: El foco inicia en Usuario

- **GIVEN** el diálogo de acceso recién abierto
- **WHEN** se consulta el elemento activo
- **THEN** el foco está en el campo "Usuario"

#### Scenario: El scroll del fondo queda bloqueado

- **GIVEN** el diálogo abierto en un navegador real
- **WHEN** se intenta scrollear la portada de fondo
- **THEN** el fondo no se mueve mientras el diálogo está abierto
- **AND** al cerrarlo el scroll se restaura
- **AND** esta verificación es visual (captura), no un test de Vitest

### Requirement: Reveal accesible de secciones

`RevealSection` SHALL mantener el contenido en el DOM y recibir un observador inyectable. Sin `IntersectionObserver` o con `prefers-reduced-motion`, MUST quedar visible sin estado pendiente. Con observador, SHALL pasar de pendiente a revelado al intersectar y limpiar la suscripción al desmontar.

#### Scenario: Sin IntersectionObserver las secciones quedan visibles

- **GIVEN** jsdom, donde `IntersectionObserver` no existe
- **WHEN** se renderiza una sección con `RevealSection`
- **THEN** la sección no queda en estado pendiente
- **AND** su contenido es visible

#### Scenario: Con observador inyectado pasa a revelado y limpia

- **GIVEN** una sección con un observador inyectado que captura el callback
- **WHEN** el callback se dispara y luego la sección se desmonta
- **THEN** la sección pasa de pendiente a revelada
- **AND** la suscripción se limpia al desmontar

#### Scenario: Reduced motion evita el estado pendiente

- **GIVEN** una sección con `prefersReducedMotion` verdadero
- **WHEN** se renderiza
- **THEN** no hay estado pendiente
- **AND** el contenido es visible de inmediato

#### Scenario: El contenido sigue en el DOM durante la animación

- **GIVEN** una sección en estado pendiente
- **WHEN** se consulta su contenido
- **THEN** el contenido ya está en el DOM
- **AND** la animación solo cambia la presentación

#### Scenario: La animación de reveal es visual

- **GIVEN** la portada en un navegador real
- **WHEN** se scrollea hasta una sección
- **THEN** la sección aparece con una transición suave
- **AND** esta verificación es visual (captura), no un test de Vitest
