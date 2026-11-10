# Spec Delta

## ADDED Requirements

### Requirement: Logo del login sobre fondo oscuro
La pantalla de login SHALL mostrar el logo de Aqua sobre fondo oscuro usando la variante clara `frontend/src/assets/brand/logo-aqua-claro.png`, informativa con `alt="Aqua — Clínica Odontológica"`. MUST conservar un encabezado accesible con el nombre "Turnos Odontología".

#### Scenario: El login muestra la variante de logo clara
- **GIVEN** la pantalla de login renderizada
- **WHEN** se inspecciona la imagen de marca
- **THEN** se usa `logo-aqua-claro.png`
- **AND** el logo tiene `alt="Aqua — Clínica Odontológica"`

#### Scenario: El fondo inmediato del logo es oscuro
- **GIVEN** la pantalla de login renderizada
- **WHEN** se observa el fondo inmediato del logo
- **THEN** el fondo es oscuro
- **AND** esta verificación es visual (captura), no un test de Vitest

#### Scenario: El encabezado accesible del login se conserva
- **GIVEN** la pantalla de login renderizada
- **WHEN** se consulta el heading accesible
- **THEN** existe un heading con el nombre "Turnos Odontología"
- **AND** el test `smoke.test.tsx` sigue pasando sin cambios

### Requirement: Bajada y tarjeta del login
El login SHALL mostrar la bajada "Claridad en cada cuidado." y una tarjeta tipo vidrio sobre un overlay degradado navy. MUST conservar el heading "Turnos Odontología".

#### Scenario: La bajada es visible
- **GIVEN** la pantalla de login renderizada
- **WHEN** se consulta el texto de la pantalla
- **THEN** la bajada "Claridad en cada cuidado." es visible

#### Scenario: La tarjeta tipo vidrio sobre overlay navy
- **GIVEN** la pantalla de login renderizada
- **WHEN** se observa la tarjeta del formulario
- **THEN** la tarjeta tiene efecto vidrio sobre un overlay degradado navy
- **AND** esta verificación es visual (captura), no un test de Vitest

### Requirement: Carrusel decorativo del login
El login SHALL mostrar un carrusel de cinco fotografías decorativas de la clínica que SHALL iniciar en `hero-1-sala-de-espera` y avanzar cada 7 s, volviendo a la primera después de la quinta. El ticker y `prefersReducedMotion` MUST ser inyectables para testear sin timers reales.

#### Scenario: Avanza al llamar al ticker y vuelve a la primera tras la quinta
- **GIVEN** el carrusel montado en la primera foto con un ticker inyectado
- **WHEN** el test invoca el callback del ticker cinco veces
- **THEN** cada invocación activa la foto siguiente
- **AND** la quinta invocación vuelve a `hero-1-sala-de-espera`

### Requirement: Pausa y ciclo de vida del carrusel
El carrusel SHALL ofrecer un botón "Pausar animación"/"Reanudar animación" sin `aria-pressed` que detiene y reanuda el avance. SHALL respetar `prefers-reduced-motion` desactivando la rotación y el Ken Burns, y SHALL cancelar su ticker al desmontar.

#### Scenario: La pausa detiene el avance
- **GIVEN** el carrusel en reproducción
- **WHEN** se presiona el botón "Pausar animación"
- **THEN** el botón pasa a tener el texto "Reanudar animación"
- **AND** el botón no tiene `aria-pressed`
- **AND** las invocaciones del ticker no cambian la foto activa
- **AND** al presionar "Reanudar animación" el avance se reanuda

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

### Requirement: Detección de reduced motion en producción
En producción, el valor por defecto de `prefersReducedMotion` SHALL leerse de `window.matchMedia("(prefers-reduced-motion: reduce)").matches`. Si `matchMedia` no existe, MUST devolver `false` sin lanzar error. Los tests MUST poder inyectar el valor. El CSS SHALL incluir `@media (prefers-reduced-motion: reduce)` que desactive el Ken Burns y el fundido.

#### Scenario: Sin matchMedia el login renderiza sin error
- **GIVEN** un entorno sin `window.matchMedia` (jsdom)
- **WHEN** se renderiza el login sin inyectar `prefersReducedMotion`
- **THEN** el login renderiza sin lanzar errores
- **AND** el carrusel se comporta como si `prefersReducedMotion` fuera `false`

#### Scenario: El CSS desactiva Ken Burns y fundido con reduced motion
- **GIVEN** `LoginPage.module.css`
- **WHEN** se inspecciona por grep
- **THEN** existe `@media (prefers-reduced-motion: reduce)`
- **AND** desactiva la animación Ken Burns y el fundido
- **AND** esta verificación es visual o de CSS (grep), no de jsdom

### Requirement: Fotos decorativas y Ken Burns
Las cinco fotografías MUST ser decorativas: `alt=""`, `aria-hidden="true"`, `data-slide-index` y `data-active` solo en la activa. Cada foto activa SHALL aplicar un Ken Burns de 7 s `ease-out` que se reinicia al entrar.

#### Scenario: Las fotos son decorativas y accesibles
- **GIVEN** el carrusel renderizado
- **WHEN** se inspeccionan las cinco imágenes
- **THEN** cada imagen tiene `alt=""` y `aria-hidden="true"`
- **AND** cada imagen se identifica por `data-slide-index` y solo la activa tiene `data-active="true"`

#### Scenario: La clase de Ken Burns está solo en la foto activa
- **GIVEN** el carrusel renderizado con `prefersReducedMotion` en falso
- **WHEN** se inspeccionan las cinco fotos
- **THEN** la foto activa tiene la clase de Ken Burns
- **AND** las demás fotos no la tienen

#### Scenario: Reduced motion quita la clase de Ken Burns
- **GIVEN** el carrusel renderizado con `prefersReducedMotion` en verdadero
- **WHEN** se inspeccionan las cinco fotos
- **THEN** ninguna foto tiene la clase de Ken Burns

#### Scenario: Duración y reinicio del Ken Burns
- **GIVEN** `LoginPage.module.css`
- **WHEN** se inspecciona por grep
- **THEN** la animación dura 7 s con `ease-out`
- **AND** se reinicia al cambiar la foto activa
- **AND** esta verificación es visual o de CSS (grep), no de jsdom
