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
