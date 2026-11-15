# turnos-odontologia

Sistema web de agenda de turnos para consultorios odontológicos de Argentina con
2 a 5 profesionales y varios sillones. Rechaza, con un mensaje que explica el
motivo, todo turno que se solape con otro del mismo profesional o del mismo
sillón.

Trabajo práctico individual de **Metodología I**, UTN FRM.

## Stack

Fijado por la cátedra:

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12+ con type hints (`mypy --strict`), FastAPI, Pydantic |
| Dominio | Python puro en `backend/app/domain`, tests con pytest |
| Autenticación | JWT |
| Persistencia | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Asincronía | Redis 7 |
| Frontend | React + TypeScript (`strict`) + Vite |
| Contenedores | Docker / Docker Compose |

## Skill y MCP

El repo trae una skill propia, `appointment-frontend-ux`, y usa el MCP `context7` para consultar
documentación actualizada del frontend.

### Requisitos

- Node.js 20+ (para el frontend).
- Una API key gratuita de Context7, creada en `https://context7.com/dashboard`. La key **nunca** se
  guarda en el repo: vive solo como variable de entorno `CONTEXT7_API_KEY`.

### Definir la variable `CONTEXT7_API_KEY` (sin escribir el valor en el repo)

Definí la key en el entorno de tu máquina, no en un archivo del repo:

- **Windows (PowerShell o CMD):** `setx CONTEXT7_API_KEY "tu-clave"`. Después **cerrá y reabrí la
  terminal** para que la variable quede disponible en las sesiones nuevas.
- **Linux / macOS (bash/zsh):** `export CONTEXT7_API_KEY="tu-clave"` (agregalo a `~/.bashrc` o
  `~/.zshrc` si querés que persista) y **reabrí la terminal**.

No escribas la key en archivos del repo. `.env` está en `.gitignore`; `.env.example` lista solo los
nombres, sin valores.

### Configuración

- `opencode.json`: servidor MCP `context7` remoto (`https://mcp.context7.com/mcp`) con el header
  `Authorization: Bearer {env:CONTEXT7_API_KEY}`.
- `.mcp.json` (Claude Code): el mismo servidor con el header
  `Authorization: Bearer ${CONTEXT7_API_KEY}`.

Ambos archivos referencian la variable de entorno; ninguno contiene la key.

### Verificar

- **OpenCode:** `opencode mcp list` (tiene que mostrar `context7` conectado). En la sesión, las
  herramientas son `context7_resolve-library-id` y `context7_query-docs`.
- **Claude Code:** `claude mcp list` (tiene que mostrar `context7` con `✔ Connected`). La primera
  vez, Claude Code pide aprobación para el servidor de `.mcp.json`.

### Nota de seguridad

La clave `CONTEXT7_API_KEY` **nunca** se escribe en el repo, en un comando versionado ni en la salida
de un comando. Solo se define en el entorno de la máquina.

### Evidencias de uso

- **C-31**: aplicación de la skill `appointment-frontend-ux` (tokens, accesibilidad, huecos libres y regla C1) en [docs/skills-mcp/evidencias/C-31-skill-appointment-frontend-ux.md](docs/skills-mcp/evidencias/C-31-skill-appointment-frontend-ux.md).
- **C-32**: consultas a Context7 (React Router v6 useSearchParams y createMemoryRouter) y aplicación de la skill `appointment-frontend-ux` (tokens, accesibilidad, zona horaria y regla C1) en [docs/skills-mcp/evidencias/C-32-skill-mcp.md](docs/skills-mcp/evidencias/C-32-skill-mcp.md).
- **C-33**: aplicación de la skill `appointment-frontend-ux` (tokens claros, accesibilidad con texto visible, confinamiento del token y regla C1; sin consultas nuevas a Context7 por APIs ya existentes) en [docs/skills-mcp/evidencias/C-33-skill-mcp.md](docs/skills-mcp/evidencias/C-33-skill-mcp.md).
- **C-35**: consultas a Context7 (React Router v6 y CSS) en [docs/skills-mcp/evidencias/C-35-mcp-context7.md](docs/skills-mcp/evidencias/C-35-mcp-context7.md) y aplicación de la skill `appointment-frontend-ux` (tokens, accesibilidad y regla C1) en [docs/skills-mcp/evidencias/C-35-skill-appointment-frontend-ux.md](docs/skills-mcp/evidencias/C-35-skill-appointment-frontend-ux.md).
- **C-36**: consultas a Context7 (CSS Container Queries, Scroll Snap y altura dinámica) en [docs/skills-mcp/evidencias/C-36-context7.md](docs/skills-mcp/evidencias/C-36-context7.md) y aplicación de la skill `appointment-frontend-ux` (tokens, accesibilidad móvil, regla C1 y verificación visual multi-resolución).

## Estado actual

**36 changes archivados** (C-01 a C-36). El detalle de cada uno está en
[CHANGES.md](CHANGES.md) y en su carpeta de [openspec/changes/archive/](openspec/changes/archive/).

### Dominio (reglas de negocio puras, sin base ni HTTP)

| Change | Qué resuelve |
|---|---|
| C-01 | Fundación del backend y guardia de dependencias del dominio |
| C-02 | Crear un turno sin solapamientos por profesional ni por sillón |
| C-03 | Duración completa y paciente, profesional, sillón y prestación existentes y activos |
| C-04 | Hora local: inicio en la grilla de 5 minutos y turno dentro de un solo día |
| C-05 | El turno cae completo dentro del horario de atención del profesional |
| C-06 | El turno no pisa ningún bloqueo de agenda del profesional |
| C-07 | No se dan turnos en el pasado (reloj inyectado, nunca el del sistema) |
| C-08 | Mensajes de error en español con nombres y rangos en hora local |
| C-09 | Altas de catálogo y pacientes con validación de nombres y DNI |
| C-10 | Transiciones de estado del turno con tabla única y permisos por rol |
| C-11 | Reprogramación con revalidación completa y retorno a "reservado" |
| C-12 | Historial inmutable de cambios de estado y reprogramaciones |

### Infraestructura y persistencia

| Change | Qué resuelve |
|---|---|
| C-13 | Docker Compose con PostgreSQL y Redis, configuración segura, sesión en UTC |
| C-14 | Migraciones Alembic con ciclo reversible probado |
| C-15 | Persistencia de catálogos y pacientes, con seed idempotente |
| C-16 | Persistencia de horarios de atención y bloqueos |
| C-17 | Persistencia de turnos e historial transaccional, protegido por triggers |

### API REST (FastAPI)

| Change | Qué resuelve |
|---|---|
| C-18 | API base: `/api/health`, errores uniformes (400, 403, 409, 422), CORS y Swagger |
| C-19 | Login con JWT y Argon2id, `/api/auth/me` y matriz RBAC por rol |
| C-20 | Endpoints de profesionales, sillones, prestaciones y pacientes |
| C-21 | Endpoints de horarios de atención y bloqueos por profesional |
| C-22 | `POST /api/appointments`: dar turnos con todas las violaciones del dominio |
| C-23 | Cancelar, reprogramar, cambiar estado e historial del turno |
| C-24 | `GET /api/agenda` con filtros y `GET /api/appointments/{id}` |

### Frontend (React 18 + TypeScript + Vite)

| Change | Qué resuelve |
|---|---|
| C-25 | Base del frontend: tokens de diseño, componentes de estado y cliente HTTP tipado |
| C-26 | Login, sesión, rutas protegidas y menú por rol |
| C-27 | Agenda diaria con horarios, bloqueos, filtros y vista de lista accesible |
| C-28 | Agenda semanal por profesional |
| C-34 | Identidad visual Aqua: paleta, tipografías, logo y carrusel del login |
| C-29 | Dar turnos desde la agenda, con los errores del dominio en pantalla |
| C-30 | Detalle e historial del turno; confirmar, atender, ausente, cancelar y reprogramar |
| C-31 | Vista de recepción por sillón con huecos libres visibles |
| C-35 | Portada pública, acceso por rol, login translúcido y modales claros |
| C-36 | App usable en celular: menú, toolbar compacta, grilla deslizable y modales como hoja inferior |
| C-32 | Pantalla de horarios semanales y bloqueos por profesional, con turnos afectados |
| C-33 | Pantallas de catálogos —profesionales, sillones y prestaciones— y pacientes, con alta, edición y desactivación según rol |


## Alcance: completo y fuera de alcance

### Completo

- **Dominio**: 12 changes (C-01 a C-12) en Python puro sin I/O ni reloj del sistema; solapamientos por profesional y sillón, duración, grilla de 5 min, horarios, bloqueos, fecha en pasado con reloj inyectado, catálogos, estados, reprogramación e historial inmutable.
- **Infraestructura y persistencia**: 5 changes (C-13 a C-17) con Docker Compose (PostgreSQL 16 y Redis 7), migraciones Alembic reversibles y persistencia de catálogos, horarios, bloqueos, turnos e historial protegido por triggers.
- **API REST**: 7 changes (C-18 a C-24) con FastAPI, Pydantic, autenticación JWT con Argon2id, RBAC por rol, endpoints de catálogos, horarios, bloqueos, turnos, ciclo de vida y agenda con filtros.
- **Frontend**: 12 changes (C-25 a C-36) en React 18, TypeScript strict y Vite; tokens de diseño Aqua, login translúcido, agenda diaria, semanal y por sillón con huecos libres, alta de turnos, reprogramación, cancelación, portada pública, adaptación móvil completa, horarios y bloqueos con turnos afectados, y catálogos y pacientes.
- **Mantenimiento**: Change `specs-requisitos-concisos` para concisión y trazabilidad de las especificaciones vigentes.

### Fuera del alcance de este TPI

Las siguientes funcionalidades no forman parte del alcance de este TPI (no son changes pendientes):
- Opciones de menú "Turnos" y "Usuarios y roles", que se muestran deliberadamente como "Próximamente" en la navegación.
- Desactivar pacientes (el dominio y la API no disponen de endpoint para desactivación o baja de pacientes).
- Deploy público (el proyecto está configurado para entorno local y desarrollo con Docker Compose).

### Limitaciones conocidas

- `Logout.test.tsx` (C-26) es intermitente en Linux y estable en Windows.

## Inicio rápido

### 1. Requisitos

- Git
- Python 3.12 o superior
- Node.js 20 o superior
- Docker Desktop

> **Nota sobre PostgreSQL local**: Si tenés un servicio PostgreSQL instalado y ejecutándose en el sistema operativo, detenelo antes de iniciar Docker Compose, ya que ambos compiten por el puerto `5432`.

### 2. Clonar

```bash
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia
```

### 3. Variables de entorno

Copiá `.env.example` a `.env` y cambiá los tres placeholders por valores locales propios (sin subir los valores reales al repositorio):

```bash
cp .env.example .env
```

Los tres placeholders a cambiar son:
- `cambiar-por-una-clave-local` (en `POSTGRES_PASSWORD` y en `DATABASE_URL`).
- `cambiar-por-una-cadena-larga-y-aleatoria` (en `JWT_SECRET`).
- `cambiar-por-una-clave-de-demo` (en `SEED_USER_PASSWORD`).

### 4. Levantar servicios en Docker

Desde la raíz:

```bash
docker compose up -d postgres redis backend
docker compose ps
```

### 5. Backend en venv

Crear venv, instalar dependencias, aplicar migraciones Alembic y ejecutar el seed de usuarios y catálogos:

#### Git Bash (Windows)

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m app.db.seed
```

#### Variante PowerShell (Windows)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m app.db.seed
```

#### Variante Linux / macOS

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.db.seed
```

### 6. Frontend local

Desde la raíz, o abriendo otra terminal:

```bash
cd frontend
npm install
npm run dev
```

> **Aclaración**: Se recomienda ejecutar el frontend de forma local con `npm run dev` (aprovechando Vite y HMR nativo en el host) y no utilizar el contenedor `frontend` de Docker Compose.

### 7. URLs

- Aplicación web: [http://localhost:5173](http://localhost:5173)
- Documentación Swagger de la API: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- Chequeo de salud: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 8. Tests

Totales actuales verificados: **895 de unidad**, **524 de integración** y **353 de frontend**.

#### Backend (desde `backend/`, usando el python del venv)

- **Unidad**: `pytest` (895 tests unitarios verificados).
  - Git Bash / Linux / macOS: `.venv/Scripts/python -m pytest` (o `.venv/bin/python -m pytest`)
  - PowerShell: `.\.venv\Scripts\python -m pytest`
- **Integración**: `pytest -m integration` (524 tests de integración verificados; requiere servicios `postgres` y `redis` levantados).
  - Git Bash / Linux / macOS: `.venv/Scripts/python -m pytest -m integration` (o `.venv/bin/python -m pytest -m integration`)
  - PowerShell: `.\.venv\Scripts\python -m pytest -m integration`
- **Tipos**: `mypy`.
  - Git Bash / Linux / macOS: `.venv/Scripts/python -m mypy` (o `.venv/bin/python -m mypy`)
  - PowerShell: `.\.venv\Scripts\python -m mypy`

#### Frontend (desde `frontend/`)

- **Tests unitarios y de componentes**:
  ```bash
  npm run test:run
  ```
  *(353 tests de frontend verificados en 93 archivos)*
- **Tipos**:
  ```bash
  npm run typecheck
  ```
- **Build**:
  ```bash
  npm run build
  ```

### 9. Apagar

- Detener frontend: `Ctrl+C` en la terminal de `npm run dev`.
- Detener servicios de Docker: desde la raíz, ejecutar:
  ```bash
  docker compose stop
  ```

> ⚠️ **Advertencia**: `docker compose down -v` borra el volumen persistente y toda la base de datos (`turnos_pgdata`). Para apagar sin perder datos, utilizá `docker compose stop` o `docker compose down` sin la opción `-v`.

Para ver los detalles del backend (módulos del dominio, un ejemplo de uso y
cómo funciona la guardia de dependencias), leé
[backend/README.md](backend/README.md).

## Usuarios de prueba

El seed (`python -m app.db.seed`, desde `backend/`) crea un usuario ficticio por rol:

| Usuario | Rol |
|---------|-----|
| `administrador` | Administrador |
| `recepcion` | Recepción |
| `odontologo` | Odontólogo, vinculado al primer profesional |

La contraseña de los tres es el valor de `SEED_USER_PASSWORD` en tu `.env`, que no
está en el repositorio.

## Créditos

| Recurso | Ubicación | Crédito y licencia |
|---|---|---|
| Fotografía `hero-1-sala-de-espera.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Foto de Bipin Kumar Pal en Unsplash. |
| Fotografía `hero-2-consultorio.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Foto de D Dental Office en Unsplash. |
| Fotografía `hero-3-dentista.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Foto de Ozkan Guner en Unsplash. |
| Fotografía `hero-4-instrumental.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Foto de Pavel Danilyuk en Pexels. |
| Fotografía `hero-5-sillon.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Foto de Ozkan Guner en Unsplash. |
| Logo de Aqua (`logo-aqua-claro.png`, `logo-aqua-oscuro.png`, `isotipo-aqua.png` e `isotipo-aqua-claro.png`) | [frontend/src/assets/brand/](frontend/src/assets/brand/) | Provisto por la autora del TP. |
| Tipografías Jost y Manrope | Paquetes `@fontsource-variable/jost` y `@fontsource-variable/manrope` | SIL Open Font License 1.1, distribuidas por Fontsource. |

Las fotos de Unsplash se usan bajo la Licencia Unsplash (https://unsplash.com/license) y la de Pexels bajo la Licencia Pexels (https://www.pexels.com/license/). Ambas permiten el uso gratuito; la atribución es una cortesía.

## Dónde está cada entregable

| Entregable | Ubicación |
|---|---|
| Informe de Discovery | [docs/discovery/informe-discovery.md](docs/discovery/informe-discovery.md) (checklist y fichas de competidores en [docs/discovery/](docs/discovery/)) |
| Informe de Discovery (PDF) | [docs/discovery/informe-discovery.pdf](docs/discovery/informe-discovery.pdf) |
| Knowledge base | [knowledge-base/](knowledge-base/) (índice en [knowledge-base/README.md](knowledge-base/README.md)) |
| Roadmap de changes | [CHANGES.md](CHANGES.md) |
| Instrucciones para agentes | [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md) |
| Skill registry | [.atl/skill-registry.md](.atl/skill-registry.md) |
| Specs vigentes | [openspec/specs/](openspec/specs/) |
| Change archivado de C-01 | [openspec/changes/archive/2026-10-08-fundacion-backend-y-dominio/](openspec/changes/archive/2026-10-08-fundacion-backend-y-dominio/) |
| Change archivado de C-02 | [openspec/changes/archive/2026-10-08-crear-turno-sin-solapamientos/](openspec/changes/archive/2026-10-08-crear-turno-sin-solapamientos/) |
| Change archivado de C-03 | [openspec/changes/archive/2026-10-22-validar-duracion-y-referencias/](openspec/changes/archive/2026-10-22-validar-duracion-y-referencias/) |
| Change archivado de C-04 | [openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/](openspec/changes/archive/2026-10-23-hora-local-y-turno-en-un-dia/) |
| Change archivado de C-05 | [openspec/changes/archive/2026-10-26-horario-de-atencion/](openspec/changes/archive/2026-10-26-horario-de-atencion/) |
| Change archivado de C-06 | [openspec/changes/archive/2026-10-28-bloqueos-de-agenda/](openspec/changes/archive/2026-10-28-bloqueos-de-agenda/) |
| Change archivado de C-07 | [openspec/changes/archive/2026-10-29-no-turnos-en-el-pasado/](openspec/changes/archive/2026-10-29-no-turnos-en-el-pasado/) |
| Change archivado de C-08 | [openspec/changes/archive/2026-11-01-mensajes-de-conflicto-en-espanol/](openspec/changes/archive/2026-11-01-mensajes-de-conflicto-en-espanol/) |
| Change archivado de C-09 | [openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/](openspec/changes/archive/2026-11-01-catalogo-y-pacientes-dominio/) |
| Change archivado de C-10 | [openspec/changes/archive/2026-11-02-transiciones-de-estado-del-turno/](openspec/changes/archive/2026-11-02-transiciones-de-estado-del-turno/) |
| Change archivado de C-11 | [openspec/changes/archive/2026-11-03-reprogramar-turno/](openspec/changes/archive/2026-11-03-reprogramar-turno/) |
| Change archivado de C-12 | [openspec/changes/archive/2026-11-04-historial-de-transiciones/](openspec/changes/archive/2026-11-04-historial-de-transiciones/) |
| Change archivado de C-13 | [openspec/changes/archive/2026-11-02-docker-compose-y-postgres/](openspec/changes/archive/2026-11-02-docker-compose-y-postgres/) |
| Change archivado de C-14 | [openspec/changes/archive/2026-11-03-migraciones-alembic/](openspec/changes/archive/2026-11-03-migraciones-alembic/) |
| Change archivado de C-15 | [openspec/changes/archive/2026-11-04-persistencia-catalogos-y-pacientes/](openspec/changes/archive/2026-11-04-persistencia-catalogos-y-pacientes/) |
| Change archivado de C-16 | [openspec/changes/archive/2026-11-05-persistencia-horarios-y-bloqueos/](openspec/changes/archive/2026-11-05-persistencia-horarios-y-bloqueos/) |
| Change archivado de C-17 | [openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/](openspec/changes/archive/2026-11-05-persistencia-turnos-e-historial/) |
| Change archivado de C-18 | [openspec/changes/archive/2026-11-06-api-base-fastapi/](openspec/changes/archive/2026-11-06-api-base-fastapi/) |
| Change archivado de C-19 | [openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/](openspec/changes/archive/2026-11-06-autenticacion-jwt-y-roles/) |
| Change archivado de C-20 | [openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/](openspec/changes/archive/2026-11-06-api-catalogos-y-pacientes/) |
| Change archivado de C-21 | [openspec/changes/archive/2026-11-06-api-horarios-y-bloqueos/](openspec/changes/archive/2026-11-06-api-horarios-y-bloqueos/) |
| Change archivado de C-22 | [openspec/changes/archive/2026-11-06-api-dar-turno/](openspec/changes/archive/2026-11-06-api-dar-turno/) |
| Change archivado de C-23 | [openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/](openspec/changes/archive/2026-11-07-api-ciclo-de-vida-del-turno/) |
| Change archivado de C-24 | [openspec/changes/archive/2026-11-07-api-consulta-de-agenda/](openspec/changes/archive/2026-11-07-api-consulta-de-agenda/) |
| Change archivado de mantenimiento: specs-requisitos-concisos | [openspec/changes/archive/2026-11-07-specs-requisitos-concisos/](openspec/changes/archive/2026-11-07-specs-requisitos-concisos/) |
| Change archivado de C-25 | [openspec/changes/archive/2026-11-07-frontend-base-react-vite/](openspec/changes/archive/2026-11-07-frontend-base-react-vite/) |
| Change archivado de C-26 | [openspec/changes/archive/2026-11-07-ui-login-y-sesion/](openspec/changes/archive/2026-11-07-ui-login-y-sesion/) |
| Change archivado de C-27 | [openspec/changes/archive/2026-11-08-ui-agenda-diaria/](openspec/changes/archive/2026-11-08-ui-agenda-diaria/) |
| Change archivado de C-28 | [openspec/changes/archive/2026-11-08-ui-agenda-semanal/](openspec/changes/archive/2026-11-08-ui-agenda-semanal/) |
| Change archivado de C-29 | [openspec/changes/archive/2026-11-13-ui-dar-turno-con-errores/](openspec/changes/archive/2026-11-13-ui-dar-turno-con-errores/) |
| Change archivado de C-30 | [openspec/changes/archive/2026-11-13-ui-reprogramar-cancelar-y-estados/](openspec/changes/archive/2026-11-13-ui-reprogramar-cancelar-y-estados/) |
| Change archivado de C-31 | [openspec/changes/archive/2026-11-14-ui-vista-de-recepcion-por-sillon/](openspec/changes/archive/2026-11-14-ui-vista-de-recepcion-por-sillon/) |
| Change archivado de C-32 | [openspec/changes/archive/2026-11-15-ui-horarios-y-bloqueos/](openspec/changes/archive/2026-11-15-ui-horarios-y-bloqueos/) |
| Change archivado de C-33 | [openspec/changes/archive/2026-11-15-ui-catalogos-y-pacientes/](openspec/changes/archive/2026-11-15-ui-catalogos-y-pacientes/) |
| Change archivado de C-34 | [openspec/changes/archive/2026-11-09-ui-identidad-visual/](openspec/changes/archive/2026-11-09-ui-identidad-visual/) |
| Change archivado de C-35 | [openspec/changes/archive/2026-11-13-ui-portada-y-acceso/](openspec/changes/archive/2026-11-13-ui-portada-y-acceso/) |
| Change archivado de C-36 | [openspec/changes/archive/2026-11-14-ui-tema-oscuro-y-movil/](openspec/changes/archive/2026-11-14-ui-tema-oscuro-y-movil/) |
| Implementación (equivale a `src/`) | [backend/app/domain/](backend/app/domain/) |
| Tests (equivale a `tests/`) | [backend/tests/](backend/tests/) |
| Evidencias (verify de C-02, explore, skills y capturas) | [docs/evidencias/](docs/evidencias/) |
| Evidencias de C-03 (explore, verify y salidas de pytest y mypy) | [explore-C-03.md](docs/evidencias/explore-C-03.md), [verify-C-03.md](docs/evidencias/verify-C-03.md), [pytest-C-03.txt](docs/evidencias/pytest-C-03.txt) y [mypy-C-03.txt](docs/evidencias/mypy-C-03.txt) |
| Evidencias de C-04 (explore, verify y salidas de pytest y mypy) | [explore-C-04.md](docs/evidencias/explore-C-04.md), [verify-C-04.md](docs/evidencias/verify-C-04.md), [pytest-C-04.txt](docs/evidencias/pytest-C-04.txt) y [mypy-C-04.txt](docs/evidencias/mypy-C-04.txt) |
| Evidencias de C-05 (explore, verify y salidas de pytest y mypy) | [explore-C-05.md](docs/evidencias/explore-C-05.md), [verify-C-05.md](docs/evidencias/verify-C-05.md), [pytest-C-05.txt](docs/evidencias/pytest-C-05.txt) y [mypy-C-05.txt](docs/evidencias/mypy-C-05.txt) |
| Evidencias de C-06 (explore, verify y salidas de pytest y mypy) | [explore-C-06.md](docs/evidencias/explore-C-06.md), [verify-C-06.md](docs/evidencias/verify-C-06.md), [pytest-C-06.txt](docs/evidencias/pytest-C-06.txt) y [mypy-C-06.txt](docs/evidencias/mypy-C-06.txt) |
| Evidencias de C-07 (explore, verify y salidas de pytest y mypy) | [explore-C-07.md](docs/evidencias/explore-C-07.md), [verify-C-07.md](docs/evidencias/verify-C-07.md), [pytest-C-07.txt](docs/evidencias/pytest-C-07.txt) y [mypy-C-07.txt](docs/evidencias/mypy-C-07.txt) |
| Evidencias de C-08 (explore, verify y salidas de pytest y mypy) | [explore-C-08.md](docs/evidencias/explore-C-08.md), [verify-C-08.md](docs/evidencias/verify-C-08.md), [pytest-C-08.txt](docs/evidencias/pytest-C-08.txt) y [mypy-C-08.txt](docs/evidencias/mypy-C-08.txt) |
| Evidencias de C-09 (explore, verify y salidas de pytest y mypy) | [explore-C-09.md](docs/evidencias/explore-C-09.md), [verify-C-09.md](docs/evidencias/verify-C-09.md), [pytest-C-09.txt](docs/evidencias/pytest-C-09.txt) y [mypy-C-09.txt](docs/evidencias/mypy-C-09.txt) |
| Evidencias de C-10 (explore, verify y salidas de pytest, mypy y TDD) | [explore-C-10.md](docs/evidencias/explore-C-10.md), [verify-C-10.md](docs/evidencias/verify-C-10.md), [pytest-C-10.txt](docs/evidencias/pytest-C-10.txt), [mypy-C-10.txt](docs/evidencias/mypy-C-10.txt) y [tdd-C-10.txt](docs/evidencias/tdd-C-10.txt) |
| Evidencias de C-11 (explore, pytest, mypy, OpenSpec y verify) | [explore-C-11.md](docs/evidencias/explore-C-11.md), [pytest-C-11.txt](docs/evidencias/pytest-C-11.txt), [mypy-C-11.txt](docs/evidencias/mypy-C-11.txt), [openspec-C-11.txt](docs/evidencias/openspec-C-11.txt) y [verify-C-11.md](docs/evidencias/verify-C-11.md) |
| Evidencias de C-12 (explore, pytest, mypy y verify) | [explore-C-12.md](docs/evidencias/explore-C-12.md), [pytest-C-12.txt](docs/evidencias/pytest-C-12.txt), [mypy-C-12.txt](docs/evidencias/mypy-C-12.txt) y [verify-C-12.md](docs/evidencias/verify-C-12.md) |
| Evidencias de C-13 (explore, pytest, integración, mypy y verify) | [explore-C-13.md](docs/evidencias/explore-C-13.md), [pytest-C-13.txt](docs/evidencias/pytest-C-13.txt), [pytest-integration-C-13.txt](docs/evidencias/pytest-integration-C-13.txt), [mypy-C-13.txt](docs/evidencias/mypy-C-13.txt) y [verify-C-13.md](docs/evidencias/verify-C-13.md) |
| Evidencias de C-14 (explore, pytest, integración, mypy, alembic y verify) | [explore-C-14.md](docs/evidencias/explore-C-14.md), [pytest-C-14.txt](docs/evidencias/pytest-C-14.txt), [pytest-integration-C-14.txt](docs/evidencias/pytest-integration-C-14.txt), [mypy-C-14.txt](docs/evidencias/mypy-C-14.txt), [alembic-C-14.txt](docs/evidencias/alembic-C-14.txt) y [verify-C-14.md](docs/evidencias/verify-C-14.md) |
| Evidencias de C-15 (explore, pytest, integración, mypy, alembic, seed y verify) | [explore-C-15.md](docs/evidencias/explore-C-15.md), [pytest-C-15.txt](docs/evidencias/pytest-C-15.txt), [pytest-integration-C-15.txt](docs/evidencias/pytest-integration-C-15.txt), [mypy-C-15.txt](docs/evidencias/mypy-C-15.txt), [alembic-C-15.txt](docs/evidencias/alembic-C-15.txt), [seed-C-15.txt](docs/evidencias/seed-C-15.txt) y [verify-C-15.md](docs/evidencias/verify-C-15.md) |
| Evidencias de C-16 (explore, pytest, integración, mypy, alembic, seed y verify) | [explore-C-16.md](docs/evidencias/explore-C-16.md), [pytest-C-16.txt](docs/evidencias/pytest-C-16.txt), [pytest-integration-C-16.txt](docs/evidencias/pytest-integration-C-16.txt), [mypy-C-16.txt](docs/evidencias/mypy-C-16.txt), [alembic-C-16.txt](docs/evidencias/alembic-C-16.txt), [seed-C-16.txt](docs/evidencias/seed-C-16.txt) y [verify-C-16.md](docs/evidencias/verify-C-16.md) |
| Evidencias de C-17 (explore, pytest, integración, mypy, alembic, mutaciones y verify) | [explore-C-17.md](docs/evidencias/explore-C-17.md), [pytest-C-17.txt](docs/evidencias/pytest-C-17.txt), [pytest-integration-C-17.txt](docs/evidencias/pytest-integration-C-17.txt), [mypy-C-17.txt](docs/evidencias/mypy-C-17.txt), [alembic-C-17.txt](docs/evidencias/alembic-C-17.txt), [mutaciones-C-17.py](docs/evidencias/mutaciones-C-17.py), [mutaciones-C-17.txt](docs/evidencias/mutaciones-C-17.txt) y [verify-C-17.md](docs/evidencias/verify-C-17.md) |
| Evidencias de C-18 (explore, pytest, mypy, docker, mutaciones y verify) | [explore-C-18.md](docs/evidencias/explore-C-18.md), [pytest-C-18.txt](docs/evidencias/pytest-C-18.txt), [mypy-C-18.txt](docs/evidencias/mypy-C-18.txt), [docker-C-18.txt](docs/evidencias/docker-C-18.txt), [mutaciones-C-18.py](docs/evidencias/mutaciones-C-18.py), [mutaciones-C-18.txt](docs/evidencias/mutaciones-C-18.txt) y [verify-C-18.md](docs/evidencias/verify-C-18.md) |
| Evidencias de C-19 (explore, verify, pytest, integración, mypy, alembic, seed, docker, e2e, mutaciones, matriz, trazabilidad, secretos, validate y RED) | [explore-C-19.md](docs/evidencias/explore-C-19.md), [verify-C-19.md](docs/evidencias/verify-C-19.md), [pytest-C-19.txt](docs/evidencias/pytest-C-19.txt), [pytest-integration-C-19.txt](docs/evidencias/pytest-integration-C-19.txt), [mypy-C-19.txt](docs/evidencias/mypy-C-19.txt), [alembic-C-19.txt](docs/evidencias/alembic-C-19.txt), [seed-C-19.txt](docs/evidencias/seed-C-19.txt), [docker-C-19.txt](docs/evidencias/docker-C-19.txt), [e2e-C-19.txt](docs/evidencias/e2e-C-19.txt), [mutaciones-C-19.txt](docs/evidencias/mutaciones-C-19.txt), [matriz-C-19.txt](docs/evidencias/matriz-C-19.txt), [trazabilidad-C-19.txt](docs/evidencias/trazabilidad-C-19.txt), [secretos-C-19.txt](docs/evidencias/secretos-C-19.txt), [validate-C-19.txt](docs/evidencias/validate-C-19.txt), [red-C-19/](docs/evidencias/red-C-19/) |
| Evidencias de C-20 (explore, verify, baseline, pytest, integración, mypy, mutaciones, trazabilidad, validate, verificación HTTP y RED) | [explore-C-20.md](docs/evidencias/explore-C-20.md), [verify-C-20.md](docs/evidencias/verify-C-20.md), [baseline-C-20.txt](docs/evidencias/baseline-C-20.txt), [pytest-C-20.txt](docs/evidencias/pytest-C-20.txt), [pytest-integration-C-20.txt](docs/evidencias/pytest-integration-C-20.txt), [mypy-C-20.txt](docs/evidencias/mypy-C-20.txt), [mutaciones-C-20.py](docs/evidencias/mutaciones-C-20.py), [mutaciones-C-20.txt](docs/evidencias/mutaciones-C-20.txt), [trazabilidad-C-20.py](docs/evidencias/trazabilidad-C-20.py), [trazabilidad-C-20.txt](docs/evidencias/trazabilidad-C-20.txt), [validate-C-20.txt](docs/evidencias/validate-C-20.txt), [http-C-20.sh](docs/evidencias/http-C-20.sh), [http-C-20.txt](docs/evidencias/http-C-20.txt), [red-C-20/](docs/evidencias/red-C-20/) |
| Evidencias de C-21 (explore, verify, precondición, baseline, pytest, integración, mypy, concurrencia, mutaciones, trazabilidad, validate y RED) | [explore-C-21.md](docs/evidencias/explore-C-21.md), [verify-C-21.md](docs/evidencias/verify-C-21.md), [precondicion-C-21.txt](docs/evidencias/precondicion-C-21.txt), [baseline-C-21.txt](docs/evidencias/baseline-C-21.txt), [pytest-C-21.txt](docs/evidencias/pytest-C-21.txt), [pytest-integration-C-21.txt](docs/evidencias/pytest-integration-C-21.txt), [mypy-C-21.txt](docs/evidencias/mypy-C-21.txt), [concurrencia-C-21.txt](docs/evidencias/concurrencia-C-21.txt), [mutaciones-C-21.py](docs/evidencias/mutaciones-C-21.py), [mutaciones-C-21.txt](docs/evidencias/mutaciones-C-21.txt), [trazabilidad-C-21.py](docs/evidencias/trazabilidad-C-21.py), [trazabilidad-C-21.txt](docs/evidencias/trazabilidad-C-21.txt), [validate-C-21.txt](docs/evidencias/validate-C-21.txt), [red-C-21/](docs/evidencias/red-C-21/) |
| Evidencias de C-22 (explore, verify, precondición, baseline, pytest, integración, mypy, concurrencia, mutaciones, trazabilidad, validate, verificación HTTP y RED) | [explore-C-22.md](docs/evidencias/explore-C-22.md), [verify-C-22.md](docs/evidencias/verify-C-22.md), [precondicion-C-22.txt](docs/evidencias/precondicion-C-22.txt), [baseline-C-22.txt](docs/evidencias/baseline-C-22.txt), [pytest-C-22.txt](docs/evidencias/pytest-C-22.txt), [pytest-integration-C-22.txt](docs/evidencias/pytest-integration-C-22.txt), [mypy-C-22.txt](docs/evidencias/mypy-C-22.txt), [concurrencia-C-22.txt](docs/evidencias/concurrencia-C-22.txt), [mutaciones-C-22.py](docs/evidencias/mutaciones-C-22.py), [mutaciones-C-22.txt](docs/evidencias/mutaciones-C-22.txt), [trazabilidad-C-22.py](docs/evidencias/trazabilidad-C-22.py), [trazabilidad-C-22.txt](docs/evidencias/trazabilidad-C-22.txt), [validate-C-22.txt](docs/evidencias/validate-C-22.txt), [http-C-22.sh](docs/evidencias/http-C-22.sh), [http-C-22.txt](docs/evidencias/http-C-22.txt), [red-C-22/](docs/evidencias/red-C-22/) |
| Evidencias de C-23 (explore, verify, precondición, baseline, pytest, integración, mypy, mutaciones, trazabilidad, validate, verificación HTTP y RED) | [explore-C-23.md](docs/evidencias/explore-C-23.md), [verify-C-23.md](docs/evidencias/verify-C-23.md), [precondicion-C-23.txt](docs/evidencias/precondicion-C-23.txt), [baseline-C-23.txt](docs/evidencias/baseline-C-23.txt), [pytest-C-23.txt](docs/evidencias/pytest-C-23.txt), [pytest-integration-C-23.txt](docs/evidencias/pytest-integration-C-23.txt), [mypy-C-23.txt](docs/evidencias/mypy-C-23.txt), [mutaciones-C-23.py](docs/evidencias/mutaciones-C-23.py), [mutaciones-C-23.txt](docs/evidencias/mutaciones-C-23.txt), [trazabilidad-C-23.py](docs/evidencias/trazabilidad-C-23.py), [trazabilidad-C-23.txt](docs/evidencias/trazabilidad-C-23.txt), [validate-C-23.txt](docs/evidencias/validate-C-23.txt), [http-C-23.sh](docs/evidencias/http-C-23.sh), [http-C-23.txt](docs/evidencias/http-C-23.txt), [red-C-23/](docs/evidencias/red-C-23/) |
| Evidencias de C-24 (explore, verify, precondición, baseline, pytest, integración, mypy, mutaciones, trazabilidad, validate, verificación HTTP y RED) | [explore-C-24.md](docs/evidencias/explore-C-24.md), [verify-C-24.md](docs/evidencias/verify-C-24.md), [precondicion-C-24.txt](docs/evidencias/precondicion-C-24.txt), [baseline-C-24.txt](docs/evidencias/baseline-C-24.txt), [pytest-C-24.txt](docs/evidencias/pytest-C-24.txt), [pytest-integration-C-24.txt](docs/evidencias/pytest-integration-C-24.txt), [mypy-C-24.txt](docs/evidencias/mypy-C-24.txt), [mutaciones-C-24.py](docs/evidencias/mutaciones-C-24.py), [mutaciones-C-24.txt](docs/evidencias/mutaciones-C-24.txt), [trazabilidad-C-24.py](docs/evidencias/trazabilidad-C-24.py), [trazabilidad-C-24.txt](docs/evidencias/trazabilidad-C-24.txt), [validate-C-24.txt](docs/evidencias/validate-C-24.txt), [http-C-24.sh](docs/evidencias/http-C-24.sh), [http-C-24.txt](docs/evidencias/http-C-24.txt), [red-C-24/](docs/evidencias/red-C-24/) |
| Evidencias de specs-requisitos-concisos (verify, validate antes y después, simulación del archive, escenarios, pytest, integración y mypy) | [verify-specs-requisitos-concisos.md](docs/evidencias/verify-specs-requisitos-concisos.md), [validate-antes-specs.txt](docs/evidencias/validate-antes-specs.txt), [validate-despues-specs.txt](docs/evidencias/validate-despues-specs.txt), [validate-simulacion-archive-specs.txt](docs/evidencias/validate-simulacion-archive-specs.txt), [escenarios-specs.py](docs/evidencias/escenarios-specs.py), [escenarios-specs.txt](docs/evidencias/escenarios-specs.txt), [pytest-specs.txt](docs/evidencias/pytest-specs.txt), [pytest-integration-specs.txt](docs/evidencias/pytest-integration-specs.txt) y [mypy-specs.txt](docs/evidencias/mypy-specs.txt) |
| Evidencias de C-25 (explore, verify, precondición, versiones, tsc, eslint, vitest, mutaciones, trazabilidad, docker, backend, validate, captura y RED) | [explore-C-25.md](docs/evidencias/explore-C-25.md), [verify-C-25.md](docs/evidencias/verify-C-25.md), [precondicion-C-25.txt](docs/evidencias/precondicion-C-25.txt), [versiones-C-25.txt](docs/evidencias/versiones-C-25.txt), [tsc-C-25.txt](docs/evidencias/tsc-C-25.txt), [eslint-C-25.txt](docs/evidencias/eslint-C-25.txt), [vitest-C-25.txt](docs/evidencias/vitest-C-25.txt), [mutaciones-C-25.py](docs/evidencias/mutaciones-C-25.py), [mutaciones-C-25.txt](docs/evidencias/mutaciones-C-25.txt), [trazabilidad-C-25.py](docs/evidencias/trazabilidad-C-25.py), [trazabilidad-C-25.txt](docs/evidencias/trazabilidad-C-25.txt), [docker-C-25.sh](docs/evidencias/docker-C-25.sh), [docker-C-25.txt](docs/evidencias/docker-C-25.txt), [backend-C-25.txt](docs/evidencias/backend-C-25.txt), [validate-C-25.txt](docs/evidencias/validate-C-25.txt), [capturas/C-25-home.png](docs/evidencias/capturas/C-25-home.png), [red-C-25/](docs/evidencias/red-C-25/) |
| Evidencias de C-26 (explore, verify, precondición, baseline, tsc, eslint, vitest, mutaciones, trazabilidad, verificación HTTP y manual, validate, capturas y RED) | [explore-C-26.md](docs/evidencias/explore-C-26.md), [verify-C-26.md](docs/evidencias/verify-C-26.md), [precondicion-C-26.txt](docs/evidencias/precondicion-C-26.txt), [baseline-C-26.txt](docs/evidencias/baseline-C-26.txt), [tsc-C-26.txt](docs/evidencias/tsc-C-26.txt), [eslint-C-26.txt](docs/evidencias/eslint-C-26.txt), [vitest-C-26.txt](docs/evidencias/vitest-C-26.txt), [mutaciones-C-26.py](docs/evidencias/mutaciones-C-26.py), [mutaciones-C-26.txt](docs/evidencias/mutaciones-C-26.txt), [trazabilidad-C-26.py](docs/evidencias/trazabilidad-C-26.py), [trazabilidad-C-26.txt](docs/evidencias/trazabilidad-C-26.txt), [http-C-26.txt](docs/evidencias/http-C-26.txt), [manual-C-26.txt](docs/evidencias/manual-C-26.txt), [validate-C-26.txt](docs/evidencias/validate-C-26.txt), [capturas/C-26-error.png](docs/evidencias/capturas/C-26-error.png), [capturas/C-26-administrador.png](docs/evidencias/capturas/C-26-administrador.png), [capturas/C-26-odontologo.png](docs/evidencias/capturas/C-26-odontologo.png), [capturas/C-26-recepcion.png](docs/evidencias/capturas/C-26-recepcion.png), [capturas/C-26-sesion-vencida.png](docs/evidencias/capturas/C-26-sesion-vencida.png), [red-C-26/](docs/evidencias/red-C-26/) |
| Evidencias de C-27 (explore, verify, precondición, baseline, tsc, eslint, vitest, mutaciones, trazabilidad, verificación HTTP y manual, validate, capturas y RED) | [explore-C-27.md](docs/evidencias/explore-C-27.md), [verify-C-27.md](docs/evidencias/verify-C-27.md), [precondicion-C-27.txt](docs/evidencias/precondicion-C-27.txt), [baseline-C-27.txt](docs/evidencias/baseline-C-27.txt), [tsc-C-27.txt](docs/evidencias/tsc-C-27.txt), [eslint-C-27.txt](docs/evidencias/eslint-C-27.txt), [vitest-C-27.txt](docs/evidencias/vitest-C-27.txt), [mutaciones-C-27.py](docs/evidencias/mutaciones-C-27.py), [mutaciones-C-27.txt](docs/evidencias/mutaciones-C-27.txt), [trazabilidad-C-27.py](docs/evidencias/trazabilidad-C-27.py), [trazabilidad-C-27.txt](docs/evidencias/trazabilidad-C-27.txt), [http-C-27.txt](docs/evidencias/http-C-27.txt), [manual-C-27.py](docs/evidencias/manual-C-27.py), [manual-C-27.txt](docs/evidencias/manual-C-27.txt), [validate-C-27.txt](docs/evidencias/validate-C-27.txt), [validate-C-27-archive.txt](docs/evidencias/validate-C-27-archive.txt), [capturas/C-27-agenda-dia.png](docs/evidencias/capturas/C-27-agenda-dia.png), [capturas/C-27-filtro-profesional.png](docs/evidencias/capturas/C-27-filtro-profesional.png), [capturas/C-27-filtro-sillon.png](docs/evidencias/capturas/C-27-filtro-sillon.png), [capturas/C-27-solapamiento-cancelado.png](docs/evidencias/capturas/C-27-solapamiento-cancelado.png), [capturas/C-27-sesion-vencida.png](docs/evidencias/capturas/C-27-sesion-vencida.png), [capturas/C-27-tablet.png](docs/evidencias/capturas/C-27-tablet.png), [capturas/C-27-vacio.png](docs/evidencias/capturas/C-27-vacio.png), [capturas/C-27-lista.png](docs/evidencias/capturas/C-27-lista.png), [red-C-27/](docs/evidencias/red-C-27/) |
| Evidencias de C-28 (explore, verify, baseline, tsc, eslint, vitest, mutaciones .py/.txt, trazabilidad .py/.txt, validate, las 7 capturas y RED) | [explore-C-28.md](docs/evidencias/explore-C-28.md), [verify-C-28.md](docs/evidencias/verify-C-28.md), [baseline-C-28.txt](docs/evidencias/baseline-C-28.txt), [tsc-C-28.txt](docs/evidencias/tsc-C-28.txt), [eslint-C-28.txt](docs/evidencias/eslint-C-28.txt), [vitest-C-28.txt](docs/evidencias/vitest-C-28.txt), [mutaciones-C-28.py](docs/evidencias/mutaciones-C-28.py), [mutaciones-C-28.txt](docs/evidencias/mutaciones-C-28.txt), [trazabilidad-C-28.py](docs/evidencias/trazabilidad-C-28.py), [trazabilidad-C-28.txt](docs/evidencias/trazabilidad-C-28.txt), [validate-C-28.txt](docs/evidencias/validate-C-28.txt), [validate-C-28-archive.txt](docs/evidencias/validate-C-28-archive.txt), [capturas/C-28-semana.png](docs/evidencias/capturas/C-28-semana.png), [capturas/C-28-hoy.png](docs/evidencias/capturas/C-28-hoy.png), [capturas/C-28-semana-vacia.png](docs/evidencias/capturas/C-28-semana-vacia.png), [capturas/C-28-filtro-sillon.png](docs/evidencias/capturas/C-28-filtro-sillon.png), [capturas/C-28-tablet.png](docs/evidencias/capturas/C-28-tablet.png), [capturas/C-28-alternancia-dia.png](docs/evidencias/capturas/C-28-alternancia-dia.png), [capturas/C-28-lista.png](docs/evidencias/capturas/C-28-lista.png), [red-C-28/](docs/evidencias/red-C-28/) |
| Evidencias de C-29 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, validate y las 7 capturas) | [explore-C-29.md](docs/evidencias/explore-C-29.md), [verify-C-29.md](docs/evidencias/verify-C-29.md), [baseline-C-29.txt](docs/evidencias/baseline-C-29.txt), [red-C-29/](docs/evidencias/red-C-29/), [green-C-29/](docs/evidencias/green-C-29/), [mutaciones-C-29.py](docs/evidencias/mutaciones-C-29.py), [mutaciones-C-29.txt](docs/evidencias/mutaciones-C-29.txt), [trazabilidad-C-29.py](docs/evidencias/trazabilidad-C-29.py), [trazabilidad-C-29.txt](docs/evidencias/trazabilidad-C-29.txt), [tooling-C-29.txt](docs/evidencias/tooling-C-29.txt), [test-suite-C-29.txt](docs/evidencias/test-suite-C-29.txt), [build-C-29.txt](docs/evidencias/build-C-29.txt), [validate-C-29.txt](docs/evidencias/validate-C-29.txt), [capturas/C-29-form-1440.png](docs/evidencias/capturas/C-29-form-1440.png), [capturas/C-29-form-768.png](docs/evidencias/capturas/C-29-form-768.png), [capturas/C-29-form-390.png](docs/evidencias/capturas/C-29-form-390.png), [capturas/C-29-form-completo-1440.png](docs/evidencias/capturas/C-29-form-completo-1440.png), [capturas/C-29-alta-exitosa-1440.png](docs/evidencias/capturas/C-29-alta-exitosa-1440.png), [capturas/C-29-error-409-1440.png](docs/evidencias/capturas/C-29-error-409-1440.png) y [capturas/C-29-error-409-390.png](docs/evidencias/capturas/C-29-error-409-390.png) |
| Evidencias de C-30 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate y las 14 capturas) | [explore-C-30.md](docs/evidencias/explore-C-30.md), [verify-C-30.md](docs/evidencias/verify-C-30.md), [baseline-C-30.txt](docs/evidencias/baseline-C-30.txt), [red-C-30/](docs/evidencias/red-C-30/), [green-C-30/](docs/evidencias/green-C-30/), [mutaciones-C-30.py](docs/evidencias/mutaciones-C-30.py), [mutaciones-C-30.txt](docs/evidencias/mutaciones-C-30.txt), [trazabilidad-C-30.py](docs/evidencias/trazabilidad-C-30.py), [trazabilidad-C-30.txt](docs/evidencias/trazabilidad-C-30.txt), [tooling-C-30.txt](docs/evidencias/tooling-C-30.txt), [test-suite-C-30.txt](docs/evidencias/test-suite-C-30.txt), [build-C-30.txt](docs/evidencias/build-C-30.txt), [diff-tests-existentes-C-30.txt](docs/evidencias/diff-tests-existentes-C-30.txt), [validate-C-30.txt](docs/evidencias/validate-C-30.txt), [capturas/C-30-detalle-1440.png](docs/evidencias/capturas/C-30-detalle-1440.png), [capturas/C-30-confirmar-cancelacion-1440.png](docs/evidencias/capturas/C-30-confirmar-cancelacion-1440.png), [capturas/C-30-cancelado-1440.png](docs/evidencias/capturas/C-30-cancelado-1440.png), [capturas/C-30-reprogramar-1440.png](docs/evidencias/capturas/C-30-reprogramar-1440.png), [capturas/C-30-reprogramar-409-1440.png](docs/evidencias/capturas/C-30-reprogramar-409-1440.png), [capturas/C-30-reprogramado-1440.png](docs/evidencias/capturas/C-30-reprogramado-1440.png), [capturas/C-30-historial-reprogramacion-1440.png](docs/evidencias/capturas/C-30-historial-reprogramacion-1440.png), [capturas/C-30-error-422-atendido-1440.png](docs/evidencias/capturas/C-30-error-422-atendido-1440.png), [capturas/C-30-odontologo-propio-1440.png](docs/evidencias/capturas/C-30-odontologo-propio-1440.png), [capturas/C-30-odontologo-ajeno-1440.png](docs/evidencias/capturas/C-30-odontologo-ajeno-1440.png), [capturas/C-30-lista-ver-turno-1440.png](docs/evidencias/capturas/C-30-lista-ver-turno-1440.png), [capturas/C-30-detalle-768.png](docs/evidencias/capturas/C-30-detalle-768.png), [capturas/C-30-detalle-390.png](docs/evidencias/capturas/C-30-detalle-390.png) y [capturas/C-30-reprogramar-409-390.png](docs/evidencias/capturas/C-30-reprogramar-409-390.png) |
| Evidencias de C-31 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate y las 7 capturas) | [explore-C-31.md](docs/evidencias/explore-C-31.md), [verify-C-31.md](docs/evidencias/verify-C-31.md), [baseline-C-31.txt](docs/evidencias/baseline-C-31.txt), [red-C-31/](docs/evidencias/red-C-31/), [green-C-31/](docs/evidencias/green-C-31/), [mutaciones-C-31.py](docs/evidencias/mutaciones-C-31.py), [mutaciones-C-31.txt](docs/evidencias/mutaciones-C-31.txt), [mutaciones-check-C-31.txt](docs/evidencias/mutaciones-check-C-31.txt), [trazabilidad-C-31.py](docs/evidencias/trazabilidad-C-31.py), [trazabilidad-C-31.txt](docs/evidencias/trazabilidad-C-31.txt), [tooling-C-31.txt](docs/evidencias/tooling-C-31.txt), [test-suite-C-31.txt](docs/evidencias/test-suite-C-31.txt), [build-C-31.txt](docs/evidencias/build-C-31.txt), [diff-tests-existentes-C-31.txt](docs/evidencias/diff-tests-existentes-C-31.txt), [validate-C-31.txt](docs/evidencias/validate-C-31.txt), [capturas/C-31-sillones-1440.png](docs/evidencias/capturas/C-31-sillones-1440.png), [capturas/C-31-sillones-768.png](docs/evidencias/capturas/C-31-sillones-768.png), [capturas/C-31-sillones-390.png](docs/evidencias/capturas/C-31-sillones-390.png), [capturas/C-31-sillones-snap-390.png](docs/evidencias/capturas/C-31-sillones-snap-390.png), [capturas/C-31-sillones-detalle-1440.png](docs/evidencias/capturas/C-31-sillones-detalle-1440.png), [capturas/C-31-sillones-lista-1440.png](docs/evidencias/capturas/C-31-sillones-lista-1440.png) y [capturas/C-31-odontologo-sin-sillones-1440.png](docs/evidencias/capturas/C-31-odontologo-sin-sillones-1440.png) |
| Evidencias de C-32 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate y las 13 capturas) | [explore-C-32.md](docs/evidencias/explore-C-32.md), [verify-C-32.md](docs/evidencias/verify-C-32.md), [baseline-C-32.txt](docs/evidencias/baseline-C-32.txt), [red-C-32/](docs/evidencias/red-C-32/), [green-C-32/](docs/evidencias/green-C-32/), [mutaciones-C-32.py](docs/evidencias/mutaciones-C-32.py), [mutaciones-C-32.txt](docs/evidencias/mutaciones-C-32.txt), [mutaciones-check-C-32.txt](docs/evidencias/mutaciones-check-C-32.txt), [trazabilidad-C-32.py](docs/evidencias/trazabilidad-C-32.py), [trazabilidad-C-32.txt](docs/evidencias/trazabilidad-C-32.txt), [tooling-C-32.txt](docs/evidencias/tooling-C-32.txt), [test-suite-C-32.txt](docs/evidencias/test-suite-C-32.txt), [build-C-32.txt](docs/evidencias/build-C-32.txt), [diff-tests-existentes-C-32.txt](docs/evidencias/diff-tests-existentes-C-32.txt), [validate-C-32.txt](docs/evidencias/validate-C-32.txt), [capturas/C-32-admin-selector-1440.png](docs/evidencias/capturas/C-32-admin-selector-1440.png), [capturas/C-32-appshell-390.png](docs/evidencias/capturas/C-32-appshell-390.png), [capturas/C-32-appshell-768.png](docs/evidencias/capturas/C-32-appshell-768.png), [capturas/C-32-bloqueo-eliminar-1440.png](docs/evidencias/capturas/C-32-bloqueo-eliminar-1440.png), [capturas/C-32-bloqueo-form-1440.png](docs/evidencias/capturas/C-32-bloqueo-form-1440.png), [capturas/C-32-bloqueo-hoja-390.png](docs/evidencias/capturas/C-32-bloqueo-hoja-390.png), [capturas/C-32-bloqueo-invalido-1440.png](docs/evidencias/capturas/C-32-bloqueo-invalido-1440.png), [capturas/C-32-guardado-1440.png](docs/evidencias/capturas/C-32-guardado-1440.png), [capturas/C-32-horarios-1440.png](docs/evidencias/capturas/C-32-horarios-1440.png), [capturas/C-32-horarios-390.png](docs/evidencias/capturas/C-32-horarios-390.png), [capturas/C-32-horarios-768.png](docs/evidencias/capturas/C-32-horarios-768.png), [capturas/C-32-solapamiento-1440.png](docs/evidencias/capturas/C-32-solapamiento-1440.png) y [capturas/C-32-turnos-afectados-1440.png](docs/evidencias/capturas/C-32-turnos-afectados-1440.png) |
| Evidencias de C-33 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate, corte de fase y las 15 capturas) | [explore-C-33.md](docs/evidencias/explore-C-33.md), [verify-C-33.md](docs/evidencias/verify-C-33.md), [baseline-C-33.txt](docs/evidencias/baseline-C-33.txt), [red-C-33/](docs/evidencias/red-C-33/), [green-C-33/](docs/evidencias/green-C-33/), [mutaciones-C-33.py](docs/evidencias/mutaciones-C-33.py), [mutaciones-C-33.txt](docs/evidencias/mutaciones-C-33.txt), [trazabilidad-C-33.py](docs/evidencias/trazabilidad-C-33.py), [trazabilidad-C-33.txt](docs/evidencias/trazabilidad-C-33.txt), [tooling-C-33.txt](docs/evidencias/tooling-C-33.txt), [test-suite-C-33.txt](docs/evidencias/test-suite-C-33.txt), [build-C-33.txt](docs/evidencias/build-C-33.txt), [diff-tests-existentes-C-33.txt](docs/evidencias/diff-tests-existentes-C-33.txt), [validate-C-33.txt](docs/evidencias/validate-C-33.txt), [validate-propose-C-33.txt](docs/evidencias/validate-propose-C-33.txt), [corte-fase2-C-33.txt](docs/evidencias/corte-fase2-C-33.txt), [capturas/C-33-appshell-390.png](docs/evidencias/capturas/C-33-appshell-390.png), [capturas/C-33-appshell-768.png](docs/evidencias/capturas/C-33-appshell-768.png), [capturas/C-33-catalogos-390.png](docs/evidencias/capturas/C-33-catalogos-390.png), [capturas/C-33-catalogos-768.png](docs/evidencias/capturas/C-33-catalogos-768.png), [capturas/C-33-catalogos-inactivo-1440.png](docs/evidencias/capturas/C-33-catalogos-inactivo-1440.png), [capturas/C-33-paciente-409-1440.png](docs/evidencias/capturas/C-33-paciente-409-1440.png), [capturas/C-33-paciente-422-1440.png](docs/evidencias/capturas/C-33-paciente-422-1440.png), [capturas/C-33-paciente-dialogo-390.png](docs/evidencias/capturas/C-33-paciente-dialogo-390.png), [capturas/C-33-paciente-editado-1440.png](docs/evidencias/capturas/C-33-paciente-editado-1440.png), [capturas/C-33-pacientes-1440.png](docs/evidencias/capturas/C-33-pacientes-1440.png), [capturas/C-33-pacientes-390.png](docs/evidencias/capturas/C-33-pacientes-390.png), [capturas/C-33-pacientes-768.png](docs/evidencias/capturas/C-33-pacientes-768.png), [capturas/C-33-prestacion-409-1440.png](docs/evidencias/capturas/C-33-prestacion-409-1440.png), [capturas/C-33-prestacion-dialogo-390.png](docs/evidencias/capturas/C-33-prestacion-dialogo-390.png) y [capturas/C-33-sillon-confirmar-1440.png](docs/evidencias/capturas/C-33-sillon-confirmar-1440.png) |
| Evidencias de C-35 (explore, verify, baseline, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate y las 35 capturas) | [explore-portada-y-acceso.md](docs/evidencias/explore-portada-y-acceso.md), [verify-C-35.md](docs/evidencias/verify-C-35.md), [baseline-C-35.txt](docs/evidencias/baseline-C-35.txt), [red-C-35/](docs/evidencias/red-C-35/), [green-C-35/](docs/evidencias/green-C-35/), [mutaciones-C-35.py](docs/evidencias/mutaciones-C-35.py), [mutaciones-C-35.txt](docs/evidencias/mutaciones-C-35.txt), [trazabilidad-C-35.py](docs/evidencias/trazabilidad-C-35.py), [trazabilidad-C-35.txt](docs/evidencias/trazabilidad-C-35.txt), [tooling-C-35.txt](docs/evidencias/tooling-C-35.txt), [test-suite-C-35.txt](docs/evidencias/test-suite-C-35.txt), [build-C-35.txt](docs/evidencias/build-C-35.txt), [diff-tests-existentes-C-35.txt](docs/evidencias/diff-tests-existentes-C-35.txt), [validate-C-35.txt](docs/evidencias/validate-C-35.txt), [capturas/C-35-acceso-1440.png](docs/evidencias/capturas/C-35-acceso-1440.png), [capturas/C-35-acceso-390.png](docs/evidencias/capturas/C-35-acceso-390.png), [capturas/C-35-acceso-768.png](docs/evidencias/capturas/C-35-acceso-768.png), [capturas/C-35-acceso-foco-1440.png](docs/evidencias/capturas/C-35-acceso-foco-1440.png), [capturas/C-35-agenda-nav-1440.png](docs/evidencias/capturas/C-35-agenda-nav-1440.png), [capturas/C-35-agenda-nav-390.png](docs/evidencias/capturas/C-35-agenda-nav-390.png), [capturas/C-35-agenda-nav-768.png](docs/evidencias/capturas/C-35-agenda-nav-768.png), [capturas/C-35-login-autofill-1440.png](docs/evidencias/capturas/C-35-login-autofill-1440.png), [capturas/C-35-login-campos-1440.png](docs/evidencias/capturas/C-35-login-campos-1440.png), [capturas/C-35-login-error-credenciales-1440.png](docs/evidencias/capturas/C-35-login-error-credenciales-1440.png), [capturas/C-35-login-error-credenciales-390.png](docs/evidencias/capturas/C-35-login-error-credenciales-390.png), [capturas/C-35-login-error-credenciales-768.png](docs/evidencias/capturas/C-35-login-error-credenciales-768.png), [capturas/C-35-login-error-servidor.png](docs/evidencias/capturas/C-35-login-error-servidor.png), [capturas/C-35-login-recepcion-1440.png](docs/evidencias/capturas/C-35-login-recepcion-1440.png), [capturas/C-35-login-recepcion-390.png](docs/evidencias/capturas/C-35-login-recepcion-390.png), [capturas/C-35-login-recepcion-768.png](docs/evidencias/capturas/C-35-login-recepcion-768.png), [capturas/C-35-login-sin-rol-1440.png](docs/evidencias/capturas/C-35-login-sin-rol-1440.png), [capturas/C-35-modal-detalle-1440.png](docs/evidencias/capturas/C-35-modal-detalle-1440.png), [capturas/C-35-modal-detalle-390.png](docs/evidencias/capturas/C-35-modal-detalle-390.png), [capturas/C-35-modal-detalle-768.png](docs/evidencias/capturas/C-35-modal-detalle-768.png), [capturas/C-35-modal-nuevo-turno-1440.png](docs/evidencias/capturas/C-35-modal-nuevo-turno-1440.png), [capturas/C-35-modal-reprogramar-1440.png](docs/evidencias/capturas/C-35-modal-reprogramar-1440.png), [capturas/C-35-portada-1440.png](docs/evidencias/capturas/C-35-portada-1440.png), [capturas/C-35-portada-390.png](docs/evidencias/capturas/C-35-portada-390.png), [capturas/C-35-portada-768.png](docs/evidencias/capturas/C-35-portada-768.png), [capturas/C-35-portada-completa-1440.png](docs/evidencias/capturas/C-35-portada-completa-1440.png), [capturas/C-35-portada-completa-390.png](docs/evidencias/capturas/C-35-portada-completa-390.png), [capturas/C-35-portada-completa-768.png](docs/evidencias/capturas/C-35-portada-completa-768.png), [capturas/C-35-secciones-1440.png](docs/evidencias/capturas/C-35-secciones-1440.png), [capturas/C-35-secciones-390.png](docs/evidencias/capturas/C-35-secciones-390.png), [capturas/C-35-secciones-768.png](docs/evidencias/capturas/C-35-secciones-768.png), [capturas/C-35-secciones-b-1440.png](docs/evidencias/capturas/C-35-secciones-b-1440.png), [capturas/C-35-secciones-b-390.png](docs/evidencias/capturas/C-35-secciones-b-390.png), [capturas/C-35-secciones-b-768.png](docs/evidencias/capturas/C-35-secciones-b-768.png) y [capturas/C-35-secciones-reduced-motion-1440.png](docs/evidencias/capturas/C-35-secciones-reduced-motion-1440.png) |
| Evidencias de C-36 (explore, verify, red/green, mutaciones .py/.txt, trazabilidad .py/.txt, tooling, test-suite, build, diff de tests existentes, validate y las 15 capturas) | [explore-C-36.md](docs/evidencias/explore-C-36.md), [verify-C-36.md](docs/evidencias/verify-C-36.md), [red-C-36/](docs/evidencias/red-C-36/), [green-C-36/](docs/evidencias/green-C-36/), [mutaciones-C-36.py](docs/evidencias/mutaciones-C-36.py), [mutaciones-C-36.txt](docs/evidencias/mutaciones-C-36.txt), [trazabilidad-C-36.py](docs/evidencias/trazabilidad-C-36.py), [trazabilidad-C-36.txt](docs/evidencias/trazabilidad-C-36.txt), [tooling-C-36.txt](docs/evidencias/tooling-C-36.txt), [test-suite-C-36.txt](docs/evidencias/test-suite-C-36.txt), [build-C-36.txt](docs/evidencias/build-C-36.txt), [diff-tests-existentes-C-36.txt](docs/evidencias/diff-tests-existentes-C-36.txt), [validate-C-36.txt](docs/evidencias/validate-C-36.txt), [capturas/C-36-menu-abierto-390.png](docs/evidencias/capturas/C-36-menu-abierto-390.png), [capturas/C-36-agenda-dia-1440.png](docs/evidencias/capturas/C-36-agenda-dia-1440.png), [capturas/C-36-agenda-dia-768.png](docs/evidencias/capturas/C-36-agenda-dia-768.png), [capturas/C-36-agenda-dia-390.png](docs/evidencias/capturas/C-36-agenda-dia-390.png), [capturas/C-36-agenda-dia-snap-390.png](docs/evidencias/capturas/C-36-agenda-dia-snap-390.png), [capturas/C-36-agenda-semana-1440.png](docs/evidencias/capturas/C-36-agenda-semana-1440.png), [capturas/C-36-agenda-semana-768.png](docs/evidencias/capturas/C-36-agenda-semana-768.png), [capturas/C-36-agenda-semana-390.png](docs/evidencias/capturas/C-36-agenda-semana-390.png), [capturas/C-36-filtros-abiertos-390.png](docs/evidencias/capturas/C-36-filtros-abiertos-390.png), [capturas/C-36-detalle-1440.png](docs/evidencias/capturas/C-36-detalle-1440.png), [capturas/C-36-detalle-768.png](docs/evidencias/capturas/C-36-detalle-768.png), [capturas/C-36-detalle-390.png](docs/evidencias/capturas/C-36-detalle-390.png), [capturas/C-36-nuevo-turno-1440.png](docs/evidencias/capturas/C-36-nuevo-turno-1440.png), [capturas/C-36-nuevo-turno-768.png](docs/evidencias/capturas/C-36-nuevo-turno-768.png) y [capturas/C-36-nuevo-turno-390.png](docs/evidencias/capturas/C-36-nuevo-turno-390.png) |
| Reflexión final | [docs/reflexion.pdf](docs/reflexion.pdf) |

Todos los datos de ejemplo y de prueba son ficticios, y el repositorio no
contiene credenciales.
