## MODIFIED Requirements

### Requirement: Compose reproducible

El Compose raíz SHALL definir `postgres:16`, `redis:7` y el servicio `backend`, publicar
5432:5432 y 6379:6379 y el puerto `API_PORT` del backend, usar el volumen `turnos_pgdata` para PostgreSQL y
declarar los healthchecks acordados. Los servicios SHALL leer las credenciales
y la base desde `.env`, sin secretos literales. El backend SHALL arrancar con las dependencias sanas y el esquema migrado.

#### Scenario: Compose sin secretos

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el YAML
- **THEN** aparecen los servicios `postgres`, `redis` y `backend`, sus healthchecks, puertos y volumen
- **AND** no aparecen contraseñas, tokens ni URLs con credenciales literales

#### Scenario: Backend conecta a la base por el nombre del servicio

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el servicio `backend`
- **THEN** `DATABASE_URL` se arma con `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}` y `${POSTGRES_DB}` sobre el host `postgres`

#### Scenario: Backend espera a postgres sano

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el servicio `backend`
- **THEN** `depends_on` exige `service_healthy` para `postgres`

#### Scenario: Backend espera a redis sano

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el servicio `backend`
- **THEN** `depends_on` exige `service_healthy` para `redis`

#### Scenario: Backend migra antes de levantar la app

- **GIVEN** `backend/Dockerfile`
- **WHEN** se inspecciona el comando de arranque
- **THEN** corre `alembic upgrade head` antes de uvicorn
- **AND** uvicorn solo arranca si la migración terminó bien

#### Scenario: Healthcheck del backend contra la API

- **GIVEN** `docker-compose.yml`
- **WHEN** se inspecciona el servicio `backend`
- **THEN** su healthcheck consulta `/api/health`
