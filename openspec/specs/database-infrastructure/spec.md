# database-infrastructure Specification

## Purpose

PostgreSQL 16 y Redis 7 en Docker Compose con healthchecks y volumen
nombrado; configuración por variables de entorno sin secretos versionados;
sesión SQLAlchemy sincrónica con psycopg 3 en UTC; base de test separada;
tests de integración marcados y excluidos por defecto; el dominio no depende
de nada de esto. También incluye migraciones versionadas con Alembic desde
`backend/`, configuración sin URL de conexión en `alembic.ini`, una
convención estable de nombres para constraints e índices, una línea de base
sin tablas de negocio, ciclos de `upgrade` y `downgrade` probados sobre la
base de test y un chequeo de autogenerate vacío.
También incluye persistencia de catálogos y pacientes con repositorios que
devuelven tipos del dominio, nombres normalizados con índice único, DNI con
`CHECK`, matrícula solo en la base y un seed idempotente con datos ficticios.

## Requirements

### Requirement: Configuración completa y errores explícitos

El sistema SHALL leer la configuración mediante `pydantic-settings` desde
`.env`. Las variables obligatorias SHALL producir un error claro que nombre la
variable faltante; secretos y `DATABASE_URL` MUST NOT tener valores por defecto.

#### Scenario: Falta DATABASE_URL

- **GIVEN** un entorno sin `DATABASE_URL`
- **WHEN** se carga la configuración
- **THEN** falla con un error explícito que nombra `DATABASE_URL`

#### Scenario: Configuración completa

- **GIVEN** todas las variables requeridas con valores ficticios válidos
- **WHEN** se carga la configuración
- **THEN** se obtienen los valores tipados de aplicación, PostgreSQL, Redis,
  JWT, zona horaria, CORS y frontend

### Requirement: Variables documentadas sin secretos

`.env.example` SHALL existir en la raíz y SHALL contener exactamente los
nombres de KB 08, sin valores ni credenciales. `.env` SHALL estar excluido
por `.gitignore`.

#### Scenario: Nombres de variables

- **GIVEN** `.env.example`
- **WHEN** se inspecciona su contenido
- **THEN** aparecen `APP_ENV`, `API_PORT`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`, `REDIS_URL`,
  `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MIN`, `SEED_USER_PASSWORD`,
  `APP_TIMEZONE`, `CORS_ORIGIN` y `VITE_API_URL`
- **AND** no hay valores sensibles

### Requirement: Compose reproducible

El Compose raíz SHALL definir solo `postgres:16` y `redis:7`, publicar
5432:5432 y 6379:6379, usar el volumen `turnos_pgdata` para PostgreSQL y
declarar los healthchecks acordados. Los servicios SHALL leer las credenciales
y la base desde `.env`, sin secretos literales.

#### Scenario: Compose sin secretos

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el YAML
- **THEN** aparecen los dos servicios, sus healthchecks, puertos y volumen
- **AND** no aparecen contraseñas, tokens ni URLs con credenciales

### Requirement: Sesión SQLAlchemy síncrona en UTC

La sesión SHALL usar SQLAlchemy 2.x con psycopg 3. Cada conexión SHALL ejecutar
`SET TIME ZONE 'UTC'`. Los instantes persistidos SHALL usar `timestamptz`.

#### Scenario: Conexión y SELECT 1

- **GIVEN** PostgreSQL saludable y configuración válida
- **WHEN** un test de integración abre la sesión y ejecuta `SELECT 1`
- **THEN** obtiene `1`

#### Scenario: Ida y vuelta timestamptz

- **GIVEN** un instante con zona `-03:00`
- **WHEN** se persiste y se lee mediante una columna `timestamptz`
- **THEN** vuelve el mismo instante normalizado a UTC

#### Scenario: Sesión en UTC

- **GIVEN** una conexión nueva
- **WHEN** se consulta la zona horaria de la sesión
- **THEN** el resultado es `UTC`

### Requirement: Base de integración aislada

La fixture SHALL derivar `<POSTGRES_DB>_test`, crearla si no existe y
reutilizarla. Cada test SHALL ejecutarse dentro de una transacción revertida.
La fixture MUST NOT borrar ni modificar la base real.

#### Scenario: Base distinta de la real

- **GIVEN** `POSTGRES_DB=turnos`
- **WHEN** la fixture prepara la integración
- **THEN** usa `turnos_test` y la URL de test no apunta a `turnos`

### Requirement: Integración excluida por defecto

La configuración de pytest SHALL registrar la marca `integration` y excluirla
por defecto mediante `addopts`. La ejecución explícita SHALL usar
`pytest -m integration`.

#### Scenario: Pytest por defecto

- **GIVEN** tests unitarios y tests marcados `integration`
- **WHEN** se ejecuta pytest sin selector
- **THEN** los tests de integración no se recolectan para ejecución

### Requirement: Guardia del dominio

La infraestructura SHALL vivir fuera de `backend/app/domain`, y la suite SHALL
confirmar que el dominio no importa SQLAlchemy.

#### Scenario: Dominio sin SQLAlchemy

- **GIVEN** el código real de `backend/app/domain`
- **WHEN** se ejecuta la guardia de dependencias
- **THEN** no se reporta ningún import de SQLAlchemy

### Requirement: Migraciones versionadas y configuración segura

El backend SHALL ejecutar migraciones versionadas desde `backend/` y SHALL
obtener `DATABASE_URL` de la configuración de la aplicación; ningún archivo
INI SHALL contener una URL de conexión.

#### Scenario: Configuración sin URL en alembic.ini

- **WHEN** se inspecciona la configuración y se inicia Alembic con un entorno válido
- **THEN** la URL efectiva proviene de `DATABASE_URL` cargada por la aplicación
- **AND** `alembic.ini` no contiene una URL de conexión

#### Scenario: Migración inicial

- **WHEN** se ejecuta `upgrade head` sobre una base de test vacía
- **THEN** termina sin errores y registra la revisión inicial
- **AND** no crea tablas de negocio

### Requirement: Reversibilidad de la línea de base

La línea de base SHALL poder revertirse hasta `base` sin errores y SHALL
dejar la base sin tablas de negocio.

#### Scenario: Downgrade a base

- **WHEN** se ejecuta `downgrade base` después de `upgrade head`
- **THEN** termina sin errores
- **AND** no quedan tablas de negocio

### Requirement: Aislamiento de migraciones de integración

Los tests de migraciones SHALL usar exclusivamente `<POSTGRES_DB>_test`,
nunca la base de desarrollo, y SHALL dejar la base de test en `head` al
finalizar la sesión de integración.

#### Scenario: Base de test restaurada en head

- **WHEN** la suite de migraciones ejecuta upgrade, downgrade y upgrade final
- **THEN** todas las operaciones se realizan sobre `<POSTGRES_DB>_test`
- **AND** la revisión final es `head`

### Requirement: Metadata consistente con las migraciones

La metadata declarativa SHALL usar una convención estable para constraints e
índices, y una comparación de autogenerate sobre una base migrada SHALL no
encontrar diferencias.

#### Scenario: Autogenerate vacío

- **WHEN** se compara la metadata con `MigrationContext` contra la base de
  test migrada
- **THEN** la lista de diferencias es vacía
- **AND** `alembic_version` no se interpreta como tabla de negocio

#### Scenario: Convención de nombres

- **WHEN** un test crea un constraint de ejemplo usando la metadata declarativa
- **THEN** el nombre generado respeta la convención acordada
- **AND** el test no agrega una tabla de negocio a la migración inicial

### Requirement: Separación de infraestructura y dominio

La infraestructura de migraciones SHALL permanecer fuera de
`backend/app/domain`, y el dominio SHALL poder verificarse sin importar
Alembic.

#### Scenario: Dominio sin Alembic

- **WHEN** se ejecuta la guardia de dependencias sobre `backend/app/domain`
- **THEN** no se reporta ningún import de Alembic

### Requirement: Verificación no destructiva por defecto

La ejecución de pytest sin el selector `integration` SHALL seguir excluyendo
los tests que requieren PostgreSQL, Docker o Alembic aplicado.

#### Scenario: Pytest unitario sin infraestructura

- **WHEN** se ejecuta `pytest` sin `-m integration`
- **THEN** los tests de integración no se ejecutan
- **AND** la suite no requiere Docker

### Requirement: Persistencia de catálogos y pacientes
La base SHALL persistir `Professional`, `Chair`, `Service` y `Patient` con ids UUID nativos y los campos definidos por el modelo de datos. `Professional` SHALL incluir `license_number` nullable solo en persistencia; `Patient` SHALL carecer de campos clínicos.

#### Scenario: Filas de catálogo y paciente

- **WHEN** se insertan entidades válidas de las cuatro clases
- **THEN** se almacenan sus ids, nombres, datos propios y estado, y una lectura devuelve el tipo correspondiente del dominio

#### Scenario: Matrícula fuera del dominio

- **WHEN** se lee un profesional con matrícula persistida
- **THEN** el tipo `Professional` devuelto conserva solo `id`, `full_name` y `active`

### Requirement: Unicidad persistente de nombres normalizados
La base SHALL conservar el nombre original y una representación normalizada de cada sillón y prestación, y SHALL impedir duplicados por esa representación. Los nombres de profesionales y pacientes NO SHALL ser únicos.

#### Scenario: Duplicado de sillón con espacios y mayúsculas

- **GIVEN** un sillón existente llamado `Sillón 1`
- **WHEN** se intenta guardar `  SILLÓN   1  `
- **THEN** el alta se rechaza como `DUPLICATE_NAME` con el mismo mensaje definido por C-09

#### Scenario: Tildes significativas

- **GIVEN** una prestación existente llamada `Extracción`
- **WHEN** se intenta guardar `Extraccion`
- **THEN** la segunda prestación no se rechaza por nombre duplicado

#### Scenario: Nombre repetido permitido

- **GIVEN** un profesional o paciente existente
- **WHEN** se guarda otra entidad de la misma clase con el mismo nombre y una clave distinta
- **THEN** el alta se acepta si las demás validaciones son correctas

### Requirement: Persistencia normalizada y única del DNI
El DNI SHALL almacenarse como texto de 7 u 8 dígitos, sin puntos ni espacios, con unicidad persistente y una restricción de base explícitamente nombrada que rechace otros formatos. Un conflicto concurrente SHALL producir `DUPLICATE_DNI` con el mensaje de C-09.

#### Scenario: DNI con formato de entrada

- **WHEN** se valida y guarda un paciente con DNI `30.111.222`
- **THEN** la fila contiene `30111222` y una lectura devuelve ese valor normalizado

#### Scenario: DNI duplicado

- **GIVEN** un paciente existente con DNI `30111222`
- **WHEN** se intenta guardar otro paciente con el mismo DNI normalizado
- **THEN** el alta se rechaza con una sola `DUPLICATE_DNI` y el mensaje de C-09

#### Scenario: DNI inválido por acceso persistente

- **WHEN** una inserción intenta guardar un DNI que no tiene 7 u 8 dígitos
- **THEN** la restricción de la base rechaza la fila y no se guarda un paciente parcial

### Requirement: Repositorios tipados de catálogos y pacientes
Los repositorios SHALL recibir y devolver únicamente tipos del dominio y SHALL usar consultas parametrizadas. Catálogos SHALL soportar alta, desactivación, reactivación, obtención por id y listado; pacientes SHALL soportar alta, obtención por id y listado.

#### Scenario: Alta validada antes de guardar

- **WHEN** una candidata de catálogo o paciente falla una validación de C-09
- **THEN** el repositorio devuelve el rechazo tipado y no crea una fila

#### Scenario: Lectura y listado

- **WHEN** se solicita una entidad por id o se lista una colección
- **THEN** se devuelven tipos del dominio, no modelos ORM, con los valores persistidos

#### Scenario: Activación idempotente

- **WHEN** se desactiva o reactiva dos veces un profesional, sillón o prestación
- **THEN** el resultado conserva el estado solicitado, no modifica otros campos y no genera una segunda violación

### Requirement: Seed ficticio e idempotente
El seed SHALL cargar tres profesionales, tres sillones, cinco prestaciones y cinco pacientes ficticios con ids fijos, y SHALL insertar solo entidades faltantes por id. No SHALL actualizar ni borrar filas existentes, ni SHALL ejecutarse automáticamente al iniciar la aplicación.

#### Scenario: Primera ejecución del seed

- **WHEN** se ejecuta el comando manual del seed sobre la base migrada
- **THEN** quedan disponibles exactamente los datos ficticios definidos para C-15, incluidas matrículas ficticias de persistencia

#### Scenario: Segunda ejecución del seed

- **WHEN** se ejecuta nuevamente el mismo seed sin limpiar la base
- **THEN** los conteos de las cuatro tablas no aumentan y los datos existentes no se actualizan ni borran

### Requirement: Integración aislada de la persistencia
Los tests de persistencia SHALL usar exclusivamente `<POSTGRES_DB>_test`, revertir la transacción de cada test y dejar la base de integración en la revisión Alembic `head` después de verificar upgrade y downgrade.

#### Scenario: Test sin contaminación

- **WHEN** un test inserta entidades y termina
- **THEN** otro test comienza sin observar esas filas

#### Scenario: Ciclo de la migración de catálogos

- **WHEN** se ejecuta `upgrade head`, `downgrade base` y `upgrade head`
- **THEN** las cuatro tablas aparecen y desaparecen según corresponda, y la base termina en `20261103_02_catalogos_y_pacientes`

#### Scenario: Violación de índice bajo concurrencia

- **WHEN** dos altas concurrentes intentan guardar el mismo nombre normalizado o DNI
- **THEN** una alta se confirma y la otra se traduce al rechazo de dominio correspondiente, sin ocultar errores de otra naturaleza
