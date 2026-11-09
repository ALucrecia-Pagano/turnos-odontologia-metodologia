# Spec Delta

## ADDED Requirements

### Requirement: Logo del login sobre fondo oscuro
La pantalla de login SHALL mostrar el logo de Aqua sobre fondo oscuro usando la variante clara `frontend/src/assets/brand/logo-aqua-claro.png`. MUST conservar un encabezado accesible con el nombre "Turnos Odontología".

#### Scenario: El login muestra la variante de logo clara
- **GIVEN** la pantalla de login renderizada
- **WHEN** se inspecciona la imagen de marca
- **THEN** se usa `logo-aqua-claro.png`
- **AND** el fondo inmediato del logo es oscuro

#### Scenario: El encabezado accesible del login se conserva
- **GIVEN** la pantalla de login renderizada
- **WHEN** se consulta el heading accesible
- **THEN** existe un heading con el nombre "Turnos Odontología"
- **AND** el test `smoke.test.tsx` sigue pasando sin cambios

### Requirement: Carrusel decorativo del login
El login SHALL mostrar un carrusel de cinco fotografías decorativas de la clínica que SHALL iniciar en `hero-1-sala-de-espera` y avanzar cada 7 s, volviendo a la primera después de la quinta. El ticker y `prefersReducedMotion` MUST ser inyectables para testear sin timers reales.

#### Scenario: Avanza al llamar al ticker y vuelve a la primera tras la quinta
- **GIVEN** el carrusel montado en la primera foto con un ticker inyectado
- **WHEN** el test invoca el callback del ticker cinco veces
- **THEN** cada invocación activa la foto siguiente
- **AND** la quinta invocación vuelve a `hero-1-sala-de-espera`

### Requirement: Pausa y ciclo de vida del carrusel
El carrusel SHALL ofrecer un botón Pausar/Reanudar con `aria-pressed` que detiene y reanuda el avance. SHALL respetar `prefers-reduced-motion` desactivando la rotación y el Ken Burns, y SHALL cancelar su ticker al desmontar.

#### Scenario: La pausa detiene el avance
- **GIVEN** el carrusel en reproducción
- **WHEN** se presiona el botón "Pausar"
- **THEN** el botón pasa a `aria-pressed="true"` con texto "Reanudar"
- **AND** las invocaciones del ticker no cambian la foto activa
- **AND** al presionar "Reanudar" el avance se reanuda

#### Scenario: Reduced motion desactiva rotación y Ken Burns
- **GIVEN** el carrusel montado con `prefersReducedMotion` en verdadero
- **WHEN** se invoca el callback del ticker
- **THEN** la foto activa no cambia
- **AND** no se aplica la animación Ken Burns

#### Scenario: El ticker se cancela al desmontar
- **GIVEN** el carrusel montado con un ticker que devuelve su función de cancelación
- **WHEN** el componente se desmonta
- **THEN** la función de cancelación del ticker fue invocada
- **AND** no queda ninguna suscripción activa

### Requirement: Fotos decorativas y Ken Burns
Las cinco fotografías MUST ser decorativas: `alt=""`, `aria-hidden="true"`, `data-slide-index` y `data-active` solo en la activa. Cada foto activa SHALL aplicar un Ken Burns de 7 s `ease-out` que se reinicia al entrar.

#### Scenario: Las fotos son decorativas y accesibles
- **GIVEN** el carrusel renderizado
- **WHEN** se inspeccionan las cinco imágenes
- **THEN** cada imagen tiene `alt=""` y `aria-hidden="true"`
- **AND** cada imagen se identifica por `data-slide-index` y solo la activa tiene `data-active="true"`

#### Scenario: El Ken Burns se reinicia en cada foto
- **GIVEN** el carrusel con la animación Ken Burns activa
- **WHEN** el ticker cambia a la foto siguiente
- **THEN** la nueva foto activa vuelve a aplicar la animación de 7 s `ease-out`
- **AND** la foto anterior deja de tener la animación
