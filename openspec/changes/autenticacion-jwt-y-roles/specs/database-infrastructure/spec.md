## ADDED Requirements

### Requirement: Tabla de usuarios con restricciones en la base

La tabla `app_user` SHALL guardar `id`, `username`, `display_name`, `password_hash`, `role`, `professional_id` y `active`, con `active` verdadero por defecto. `username` SHALL ser único y cumplir `^[a-z0-9._-]{3,150}$`. `role` SHALL ser uno de `odontologo`, `recepcion` y `administrador`. El borrado de un profesional con usuario SHALL rechazarse.

#### Scenario: Usuario duplicado

- **GIVEN** un usuario con `username` igual a `recepcion`
- **WHEN** se inserta directamente otra fila con ese `username`
- **THEN** PostgreSQL la rechaza por `ux_app_user_username`

#### Scenario: Usuario con mayúsculas

- **WHEN** se inserta directamente una fila con `username` igual a `Recepcion`
- **THEN** PostgreSQL la rechaza por `ck_app_user_username_format`

#### Scenario: Rol desconocido

- **WHEN** se inserta directamente una fila con `role` igual a `superusuario`
- **THEN** PostgreSQL la rechaza por `ck_app_user_role`

#### Scenario: Activo por defecto

- **WHEN** se inserta directamente una fila válida sin indicar `active`
- **THEN** la fila queda con `active` verdadero

#### Scenario: Profesional inexistente

- **WHEN** se inserta directamente un odontólogo con un `professional_id` que no existe
- **THEN** PostgreSQL la rechaza por `fk_app_user_professional_id_professional`

#### Scenario: Borrar un profesional con usuario

- **GIVEN** un odontólogo vinculado a un profesional
- **WHEN** se borra directamente ese profesional
- **THEN** PostgreSQL lo rechaza por `fk_app_user_professional_id_professional`

### Requirement: El odontólogo tiene profesional y los demás roles no

La restricción `ck_app_user_professional_by_role` SHALL exigir `professional_id` en todo usuario de rol `odontologo` y SHALL prohibirlo en los demás roles. Cada profesional SHALL tener como máximo un usuario, por `ux_app_user_professional_id`.

#### Scenario: Odontólogo con profesional

- **WHEN** se inserta directamente un odontólogo con un `professional_id` existente
- **THEN** la fila se acepta

#### Scenario: Odontólogo sin profesional

- **WHEN** se inserta directamente un odontólogo con `professional_id` nulo
- **THEN** PostgreSQL la rechaza por `ck_app_user_professional_by_role`

#### Scenario: Recepción sin profesional

- **WHEN** se inserta directamente un usuario de rol `recepcion` con `professional_id` nulo
- **THEN** la fila se acepta

#### Scenario: Recepción con profesional

- **WHEN** se inserta directamente un usuario de rol `recepcion` con un `professional_id` existente
- **THEN** PostgreSQL la rechaza por `ck_app_user_professional_by_role`

#### Scenario: Administrador con profesional

- **WHEN** se inserta directamente un usuario de rol `administrador` con un `professional_id` existente
- **THEN** PostgreSQL la rechaza por `ck_app_user_professional_by_role`

#### Scenario: Cambiar a recepción sin quitar el profesional

- **GIVEN** un odontólogo con `professional_id`
- **WHEN** se actualiza directamente su `role` a `recepcion` sin cambiar `professional_id`
- **THEN** PostgreSQL lo rechaza por `ck_app_user_professional_by_role`

#### Scenario: Dos usuarios para el mismo profesional

- **GIVEN** un odontólogo vinculado a un profesional
- **WHEN** se inserta directamente otro odontólogo vinculado al mismo profesional
- **THEN** PostgreSQL lo rechaza por `ux_app_user_professional_id`

#### Scenario: Varios usuarios sin profesional

- **GIVEN** un usuario de rol `recepcion` con `professional_id` nulo
- **WHEN** se inserta directamente un usuario de rol `administrador` con `professional_id` nulo
- **THEN** la fila se acepta

### Requirement: Migración reversible de usuarios

La revisión `20261106_06_usuarios` SHALL crear `app_user` con sus restricciones e índices, y SHALL revertirse eliminando solo esa tabla. El ciclo de downgrade de su test SHALL usar revisiones explícitas, sin `-1` ni `head`, para no romperse con migraciones futuras.

#### Scenario: Downgrade a la revisión anterior

- **GIVEN** la base en `20261106_06_usuarios`
- **WHEN** se ejecuta `downgrade` a `20261105_05_historial_sin_truncate`
- **THEN** la tabla `app_user` no existe
- **AND** siguen existiendo `professional`, `appointment` y `appointment_status_change`
- **AND** la base está en `20261105_05_historial_sin_truncate`

#### Scenario: Upgrade a la revisión de usuarios

- **GIVEN** la base en `20261105_05_historial_sin_truncate`
- **WHEN** se ejecuta `upgrade` a `20261106_06_usuarios`
- **THEN** la tabla `app_user` existe
- **AND** la base está en `20261106_06_usuarios`

#### Scenario: Sin diferencias con la metadata

- **GIVEN** la base en `head`
- **WHEN** se compara el esquema con la metadata de los modelos
- **THEN** no hay diferencias

### Requirement: Seed de un usuario por rol

El seed SHALL crear con ids fijos los usuarios ficticios `administrador`, `recepcion` y `odontologo`, este último vinculado al primer profesional, con el hash de `SEED_USER_PASSWORD`. SHALL insertar solo los faltantes por id, sin actualizar contraseñas existentes. Su salida MUST NOT mostrar la contraseña.

#### Scenario: Primera ejecución crea los tres usuarios

- **GIVEN** una base migrada y `SEED_USER_PASSWORD` válida
- **WHEN** se ejecuta el seed
- **THEN** existen exactamente tres filas en `app_user`, una por rol
- **AND** el resultado informa `app_user` igual a `3`

#### Scenario: Cada usuario del seed inicia sesión

- **GIVEN** el seed ejecutado con `SEED_USER_PASSWORD` válida
- **WHEN** se invoca el login de los tres usuarios con esa contraseña
- **THEN** los tres responden `200`

#### Scenario: Segunda ejecución no inserta

- **GIVEN** el seed ya ejecutado
- **WHEN** se ejecuta otra vez
- **THEN** siguen existiendo tres filas en `app_user`
- **AND** `password_hash` de cada fila no cambió

#### Scenario: Una contraseña distinta no cambia a los usuarios existentes

- **GIVEN** el seed ya ejecutado
- **WHEN** se ejecuta otra vez con un `SEED_USER_PASSWORD` distinto
- **THEN** `password_hash` de cada fila no cambió

#### Scenario: El seed guarda hash Argon2id

- **GIVEN** el seed ejecutado con `SEED_USER_PASSWORD` válida
- **WHEN** se lee `password_hash` de cada fila
- **THEN** empieza con `$argon2id$v=19$m=65536,t=3,p=4$`
- **AND** no contiene la contraseña

#### Scenario: El usuario y el profesional tienen ids distintos

- **GIVEN** el usuario `odontologo` del seed
- **WHEN** se compara su `id` con su `professional_id`
- **THEN** son distintos

#### Scenario: La salida del seed no muestra la contraseña

- **GIVEN** una `SEED_USER_PASSWORD` válida y reconocible
- **WHEN** se ejecuta el comando manual del seed y se captura su salida
- **THEN** la contraseña no aparece en la salida

### Requirement: El seed exige una contraseña válida antes de escribir

`SEED_USER_PASSWORD` SHALL existir y tener al menos 8 caracteres, sin contar una cadena de solo espacios como válida. Si no cumple, el seed SHALL fallar con un error en español que nombre la variable, sin mostrar el valor y antes de abrir una transacción. MUST NOT quedar ninguna fila nueva en ninguna tabla.

#### Scenario: Falta la contraseña

- **GIVEN** una base migrada y vacía, sin `SEED_USER_PASSWORD`
- **WHEN** se ejecuta el seed
- **THEN** falla con un error que nombra `SEED_USER_PASSWORD`
- **AND** todas las tablas de negocio siguen vacías

#### Scenario: Contraseña vacía

- **GIVEN** una base migrada y vacía, con `SEED_USER_PASSWORD` vacía
- **WHEN** se ejecuta el seed
- **THEN** falla con un error que nombra `SEED_USER_PASSWORD`
- **AND** todas las tablas de negocio siguen vacías

#### Scenario: Contraseña de solo espacios

- **GIVEN** una base migrada y vacía, con `SEED_USER_PASSWORD` de ocho espacios
- **WHEN** se ejecuta el seed
- **THEN** falla con un error que nombra `SEED_USER_PASSWORD`
- **AND** todas las tablas de negocio siguen vacías

#### Scenario: Contraseña de 7 caracteres

- **GIVEN** una base migrada y vacía, con `SEED_USER_PASSWORD` de 7 caracteres reconocibles
- **WHEN** se ejecuta el seed
- **THEN** falla con un error que nombra `SEED_USER_PASSWORD`
- **AND** el texto reconocible no aparece en el error
- **AND** todas las tablas de negocio siguen vacías

#### Scenario: Contraseña de 8 caracteres

- **GIVEN** una base migrada y vacía, con `SEED_USER_PASSWORD` de 8 caracteres
- **WHEN** se ejecuta el seed
- **THEN** existen tres filas en `app_user`

#### Scenario: El comando manual termina con error

- **GIVEN** un proceso con `SEED_USER_PASSWORD` vacía en su entorno
- **WHEN** se ejecuta el comando manual del seed
- **THEN** el código de salida es distinto de `0`

### Requirement: El seed se niega a correr en producción

Con `APP_ENV` igual a `production`, el seed SHALL fallar con un error en español antes de abrir una transacción, aunque `SEED_USER_PASSWORD` sea válida. MUST NOT quedar ninguna fila nueva.

#### Scenario: Seed con APP_ENV production

- **GIVEN** una base migrada y vacía, `APP_ENV` igual a `production` y `SEED_USER_PASSWORD` válida
- **WHEN** se ejecuta el seed
- **THEN** falla con un error que nombra `APP_ENV`
- **AND** todas las tablas de negocio siguen vacías

#### Scenario: Seed con APP_ENV development

- **GIVEN** una base migrada y vacía, `APP_ENV` igual a `development` y `SEED_USER_PASSWORD` válida
- **WHEN** se ejecuta el seed
- **THEN** existen tres filas en `app_user`

## MODIFIED Requirements

### Requirement: Configuración completa y errores explícitos

El sistema SHALL leer la configuración mediante `pydantic-settings` desde
`.env`. Las variables obligatorias SHALL producir un error claro que nombre la
variable faltante; secretos y `DATABASE_URL` MUST NOT tener valores por defecto.
`SEED_USER_PASSWORD` es la única excepción: es opcional para cargar la
configuración, sin valor utilizable por defecto, y la exige el seed.

#### Scenario: Falta DATABASE_URL

- **GIVEN** un entorno sin `DATABASE_URL`
- **WHEN** se carga la configuración
- **THEN** falla con un error explícito que nombra `DATABASE_URL`

#### Scenario: Configuración completa

- **GIVEN** todas las variables requeridas con valores ficticios válidos
- **WHEN** se carga la configuración
- **THEN** se obtienen los valores tipados de aplicación, PostgreSQL, Redis,
  JWT, zona horaria, CORS y frontend

#### Scenario: Falta SEED_USER_PASSWORD

- **GIVEN** un entorno completo sin `SEED_USER_PASSWORD`
- **WHEN** se carga la configuración
- **THEN** la configuración se carga
- **AND** `seed_user_password` es nulo

### Requirement: Migración reversible de horarios y bloqueos
La migración `20261104_03_horarios_y_bloqueos` SHALL ser reversible y el autogenerate SHALL no reportar diferencias después de recrear las tablas.

#### Scenario: Ciclo upgrade y downgrade reversible de la migración
- **WHEN** se ejecuta `downgrade` a `20261104_03_horarios_y_bloqueos`, después `downgrade -1` y después `upgrade head` sobre `<POSTGRES_DB>_test`
- **THEN** después del `downgrade -1` no existen `working_hours` ni `block`, siguen existiendo `professional`, `chair`, `service` y `patient`, y la base está en `20261103_02_catalogos_y_pacientes`; después del upgrade final, la base está en `head` y la comparación de metadata no reporta diferencias

### Requirement: Migración reversible de turnos e historial
La revisión de base de datos `20261105_04_turnos_e_historial` SHALL crear las tablas `appointment` y `appointment_status_change` con sus índices, constraints y trigger append-only, y SHALL poder revertirse a `20261104_03_horarios_y_bloqueos` eliminando ambas tablas y el trigger sin alterar las tablas previas de catálogo, horarios y bloqueos.

#### Scenario: Ciclo upgrade y downgrade menos uno de la migración de turnos
- **WHEN** se ejecuta `downgrade` a `20261104_03_horarios_y_bloqueos`, `upgrade` a `20261105_04_turnos_e_historial`, `downgrade -1` y nuevamente `upgrade head` sobre la base de integración
- **THEN** tras el `downgrade -1` desaparecen las tablas `appointment`, `appointment_status_change` y el trigger, conservando las tablas de catálogo y horarios, y al volver a `head` la comparación de metadata no encuentra diferencias
