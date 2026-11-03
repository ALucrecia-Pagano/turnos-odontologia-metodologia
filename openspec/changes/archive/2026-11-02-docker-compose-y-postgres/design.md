# Design

## Contexto

El backend actual es Python puro y solo prueba el dominio. C-13 agrega la
primera frontera de infraestructura sin mezclarla con `backend/app/domain`.
PostgreSQL es real, Redis queda levantado por decisión de la cátedra pero sin
uso funcional en el MVP. C-14 será responsable de Alembic y C-18 de integrar
FastAPI y el servicio backend.

## Objetivos y fuera de alcance

### Objetivos

- Entorno local reproducible en Windows con Docker Desktop y WSL 2.
- Configuración explícita y segura.
- Sesión SQLAlchemy síncrona sobre psycopg 3.
- Conversión consistente de instantes mediante UTC.
- Tests de integración aislados de la base real y excluidos de pytest por
  defecto.

### Fuera de alcance

- Modelos de negocio, repositorios y migraciones Alembic.
- Servicios Compose `backend` y `frontend`.
- Redis como cola o funcionalidad de aplicación.
- Cambios en el dominio o en su allowlist.
- JWT, FastAPI y endpoints.

## Decisiones cerradas

### D1 — Driver y sesión

Usar `psycopg[binary]>=3,<4` con SQLAlchemy `>=2,<3` y sesión síncrona.

### D2 — Configuración

Usar `pydantic-settings>=2,<3`. La configuración debe fallar al cargar si
falta una variable obligatoria y mencionar su nombre. Secretos y
`DATABASE_URL` no tendrán defaults.

### D3 — Entorno

Crear `.env.example` raíz con exactamente los catorce nombres de KB 08, sin
valores. `.env` ya está ignorado y debe verificarse sin cambiar esa regla.

### D4 — Base de test

La fixture de sesión deriva `<POSTGRES_DB>_test`, la crea si no existe, la
reutiliza y jamás opera sobre `POSTGRES_DB`. Cada test abre una transacción y
la revierte.

### D5 — Marca

Registrar `integration` y configurar `addopts = "-m \"not integration\""`.
La ejecución explícita es `pytest -m integration`.

### D6 — UTC

Registrar un listener de conexión SQLAlchemy que ejecute `SET TIME ZONE
'UTC'`. Usar `timestamptz` para instantes. El test debe comprobar que un
instante `-03:00` vuelve como el mismo instante UTC.

### D7 — Compose

Solo dos servicios:

```text
postgres: postgres:16, 5432:5432, volumen turnos_pgdata, pg_isready
redis:    redis:7,    6379:6379, redis-cli ping
```

Las credenciales y el nombre de la base se interpolan desde `.env`; nunca se
escriben valores sensibles en el YAML.

### D8 — Dependencias

Las tres dependencias de infraestructura son runtime, no opcionales de
desarrollo, porque la sesión y la configuración forman parte del backend
ejecutable. Sus rangos son los cerrados en D8.

### D9 — Host de tests

Los tests de integración usan `localhost:5432` y se ejecutan desde Windows,
no dentro de un contenedor backend.

### D10 — Guardia

La infraestructura se ubica en `backend/app/config.py` y `backend/app/db/`.
No se importa nada desde `backend/app/domain` y no se cambia la guardia.

### D11 — Verificación de secretos

No se agrega checkpoint. El grupo final de tareas buscará contraseñas y URLs
con credenciales en todos los archivos versionados y fallará ante hallazgos.

### D12 — Spec

La capacidad nueva es `database-infrastructure`; las specs existentes no se
modifican.

## Flujo de datos

```text
.env --> pydantic-settings --> config.py --> SQLAlchemy Engine
                                         |
                                         v
                              SET TIME ZONE 'UTC'
                                         |
                                         v
                              PostgreSQL localhost:5432
```

La base de test se deriva desde `POSTGRES_DB`, pero su URL usa otro nombre:

```text
POSTGRES_DB=turnos
        |
        +--> base real: turnos
        `--> base de integración: turnos_test
```

## Verificación manual para la autora

Desde Git Bash, en la raíz del repositorio:

```bash
cp .env.example .env
```

Completar `.env` con valores ficticios locales. No versionar `.env`.

```bash
docker compose up -d
docker compose ps
docker compose exec postgres pg_isready
docker compose exec redis redis-cli ping
```

La comprobación de Redis debe devolver `PONG`; PostgreSQL debe indicar que
acepta conexiones.

Desde `backend/`, con el entorno virtual existente:

```bash
cd backend
.venv/Scripts/python -m pytest
.venv/Scripts/python -m pytest -m integration
cd ..
```

Finalmente, detener los servicios sin borrar el volumen:

```bash
docker compose down
```

No usar `docker compose down -v` para esta verificación.

Si se cambian las credenciales de .env después de crear el volumen,
PostgreSQL no las toma: hay que recrear el volumen con docker compose down -v
(borra los datos locales).

Si hay un PostgreSQL instalado en Windows, detenerlo antes de levantar el
compose: los dos usan el puerto 5432.

## Desvíos del apply

- La primera ejecución de integración no encontró `.env` porque la
  configuración buscaba el archivo dentro de `backend/`; se corrigió para
  resolver el `.env` de la raíz.
- La primera conexión administrativa intentó usar directamente una URL con
  driver `postgresql+psycopg`; se corrigió para usar el driver `postgresql`
  al conectar con psycopg.
- La integración inicialmente falló con autenticación. El diagnóstico
  inicial equivocado fue que el volumen `turnos_pgdata` conservaba
  credenciales anteriores; la autora recreó el volumen sin resolver el
  problema. El síntoma persistió porque otro PostgreSQL instalado en Windows
  también escuchaba en el puerto 5432. Se detectó por el idioma castellano y
  la codificación de Windows del mensaje, diferente del PostgreSQL del
  contenedor. La solución fue detener el servicio local de Windows y dejar el
  puerto 5432 exclusivamente para Docker.
