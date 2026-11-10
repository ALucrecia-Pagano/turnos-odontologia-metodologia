# Spec Delta

## ADDED Requirements

### Requirement: Tokens de layout de la portada

`tokens.css` SHALL definir `--landing-hero-min-height: 60vh` y `--landing-content-max-width` con un valor de longitud. MUST NOT agregar colores nuevos ni valores de color fuera de la paleta Aqua.

#### Scenario: Los tokens de layout existen

- **GIVEN** el archivo `frontend/src/shared/styles/tokens.css`
- **WHEN** se leen las custom properties de layout
- **THEN** `--landing-hero-min-height` vale `60vh`
- **AND** `--landing-content-max-width` existe con un valor de longitud

#### Scenario: La portada usa los tokens de layout

- **GIVEN** los CSS modules de `frontend/src/features/landing/`
- **WHEN** se buscan los valores de layout
- **THEN** el hero usa `var(--landing-hero-min-height)`
- **AND** el contenido usa `var(--landing-content-max-width)`

#### Scenario: No se agregan colores nuevos

- **GIVEN** los tokens de color existentes de C-34
- **WHEN** se comparan con `tokens.css` después de C-35
- **THEN** no hay custom properties de color nuevas
- **AND** la paleta Aqua no cambia

### Requirement: Diálogo modal reutilizable

La primitiva `Dialog` en `frontend/src/shared/components/Dialog.tsx` SHALL ser un `<dialog>` modal reutilizable con `open`, `onClose`, `labelledBy`, `returnFocusRef` y `children`. MUST abrir con `showModal()` o, en jsdom, con el atributo `open`, cerrar con `close()` o `removeAttribute("open")`, aplicar `aria-labelledby` y devolver el foco a `returnFocusRef`.

#### Scenario: Sin showModal el diálogo usa el atributo open

- **GIVEN** jsdom, donde `HTMLDialogElement.showModal` no existe
- **WHEN** `Dialog` se abre con `open` verdadero
- **THEN** el elemento `<dialog>` tiene el atributo `open`
- **AND** no se reemplazan globals ni se usan stubs de `showModal`

#### Scenario: Escape cierra y devuelve el foco

- **GIVEN** `Dialog` abierto con `returnFocusRef` apuntando a un botón
- **WHEN** se presiona Escape
- **THEN** se llama a `onClose`
- **AND** el foco vuelve al botón de `returnFocusRef`

#### Scenario: El evento cancel cierra

- **GIVEN** `Dialog` abierto
- **WHEN** se dispara el evento `cancel` del `<dialog>`
- **THEN** se llama a `onClose`
