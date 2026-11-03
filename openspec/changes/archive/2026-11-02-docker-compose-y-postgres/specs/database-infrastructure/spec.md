# Database Infrastructure Specification

## Propósito

Proveer configuración segura y tipada, PostgreSQL y Redis locales mediante
Docker Compose, una sesión SQLAlchemy síncrona en UTC y tests de integración
aislados de la base real, sin introducir dependencias en el dominio.

## ADDED Requirements

### Requirement: Configuración completa y errores explícitos

El sistema SHALL leer la configuración mediante `pydantic-settings` desde
`.env`. Las variables obligatorias SHALL producir un error claro que nombre la
variable faltante; secretos y `DATABASE_URL` MUST NOT tener valores por defecto.

#### Escenario: Falta DATABASE_URL

- **GIVEN** un entorno sin `DATABASE_URL`
- **WHEN** se carga la configuración
- **THEN** falla con un error explícito que nombra `DATABASE_URL`

#### Escenario: Configuración completa

- **GIVEN** todas las variables requeridas con valores ficticios válidos
- **WHEN** se carga la configuración
- **THEN** se obtienen los valores tipados de aplicación, PostgreSQL, Redis,
  JWT, zona horaria, CORS y frontend

### Requirement: Variables documentadas sin secretos

`.env.example` SHALL existir en la raíz y SHALL contener exactamente los
nombres de KB 08, sin valores ni credenciales. `.env` SHALL estar excluido
por `.gitignore`.

#### Escenario: Nombres de variables

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

#### Escenario: Compose sin secretos

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el YAML
- **THEN** aparecen los dos servicios, sus healthchecks, puertos y volumen
- **AND** no aparecen contraseñas, tokens ni URLs con credenciales

### Requirement: Sesión SQLAlchemy síncrona en UTC

La sesión SHALL usar SQLAlchemy 2.x con psycopg 3. Cada conexión SHALL ejecutar
`SET TIME ZONE 'UTC'`. Los instantes persistidos SHALL usar `timestamptz`.

#### Escenario: Conexión y SELECT 1

- **GIVEN** PostgreSQL saludable y configuración válida
- **WHEN** un test de integración abre la sesión y ejecuta `SELECT 1`
- **THEN** obtiene `1`

#### Escenario: Ida y vuelta timestamptz

- **GIVEN** un instante con zona `-03:00`
- **WHEN** se persiste y se lee mediante una columna `timestamptz`
- **THEN** vuelve el mismo instante normalizado a UTC

#### Escenario: Sesión en UTC

- **GIVEN** una conexión nueva
- **WHEN** se consulta la zona horaria de la sesión
- **THEN** el resultado es `UTC`

### Requirement: Base de integración aislada

La fixture SHALL derivar `<POSTGRES_DB>_test`, crearla si no existe y
reutilizarla. Cada test SHALL ejecutarse dentro de una transacción revertida.
La fixture MUST NOT borrar ni modificar la base real.

#### Escenario: Base distinta de la real

- **GIVEN** `POSTGRES_DB=turnos`
- **WHEN** la fixture prepara la integración
- **THEN** usa `turnos_test` y la URL de test no apunta a `turnos`

### Requirement: Integración excluida por defecto

La configuración de pytest SHALL registrar la marca `integration` y excluirla
por defecto mediante `addopts`. La ejecución explícita SHALL usar
`pytest -m integration`.

#### Escenario: Pytest por defecto

- **GIVEN** tests unitarios y tests marcados `integration`
- **WHEN** se ejecuta pytest sin selector
- **THEN** los tests de integración no se recolectan para ejecución

### Requirement: Guardia del dominio

La infraestructura SHALL vivir fuera de `backend/app/domain`, y la suite SHALL
confirmar que el dominio no importa SQLAlchemy.

#### Escenario: Dominio sin SQLAlchemy

- **GIVEN** el código real de `backend/app/domain`
- **WHEN** se ejecuta la guardia de dependencias
- **THEN** no se reporta ningún import de SQLAlchemy
