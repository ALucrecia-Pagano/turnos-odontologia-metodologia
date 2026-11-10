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

## Estado actual

- **Implementado:** el dominio de C-01 (fundación del backend y guardia de
  dependencias del dominio), C-02 (crear un turno sin solapamientos por
  profesional y por sillón), C-03 (validar la duración completa y que el
  paciente, el profesional, el sillón y la prestación existan y estén activos),
  C-04 (hora local: inicio en la grilla de 5 minutos y turno dentro de un
  solo día local, evaluados en la zona horaria recibida), C-05 (horario de
  atención: el turno cae completo dentro de los tramos del profesional para su
  día local, y validación del conjunto de tramos) y C-06 (bloqueos de agenda: el
  turno no pisa ningún bloqueo del profesional, comparado en instantes; validación
  de un bloqueo y lista de los turnos que pisa, sin cancelarlos) y C-07 (no dar
  turnos en el pasado: el inicio no puede ser anterior al momento actual
  inyectado; la guardia verifica que el dominio no lee el reloj del sistema), C-08
  (mensajes en español con el nombre del profesional o sillón y el rango en hora
  local, intervalo en conflicto en UTC y todas las violaciones del primer grupo
  que falla) y C-09 (altas puras de catálogo y pacientes, validación de nombres
  y DNI, activación inmutable y datos ficticios reutilizables) y C-10
  (transiciones de estado con tabla única, cancelación sin anticipación mínima,
  atendido y ausente desde el inicio con reloj inyectado, permisos por rol y
  propiedad y copias inmutables; sin historial), C-11 (reprogramación de
  turnos en el dominio, con revalidación completa, auto-exclusión, permisos y
  retorno a reservado), C-12 (historial funcional inmutable de transiciones de
  estado del turno en el dominio, con detalle de reprogramación), C-13
  (Docker Compose con PostgreSQL, Redis, configuración segura, sesión SQLAlchemy
  síncrona en UTC y tests de integración aislados), C-14 (migraciones Alembic
  con línea de base, configuración segura, metadata con convención estable y
  ciclo reversible probado) y C-15 (persistencia de catálogos y pacientes,
  repositorios tipados, índices normalizados, CHECK de DNI y seed idempotente),
  C-16 (persistencia de horarios de atención y bloqueos, repositorios tipados,
  validación previa, reemplazo transaccional, turnos afectados y seed idempotente),
  C-17 (persistencia de turnos e historial con servicios transaccionales, bloqueo
  de filas en orden fijo, historial de solo inserción protegido por triggers y
  lector SQL de turnos),
  C-18 (API base con FastAPI: `GET /api/health` con chequeo de la base, errores
  uniformes `409`, `422`, `403` y `400`, CORS limitado a `CORS_ORIGIN`, sesión
  por request sin `commit` implícito, Swagger en `/api/docs` y servicio
  `backend` en el Compose),
  C-19 (autenticación con JWT y Argon2id: `POST /api/auth/login`,
  `GET /api/auth/me`, mismo `401` ante credenciales inválidas, usuario releído en
  cada request, matriz RBAC como tabla de datos con rechazo por defecto y un
  usuario ficticio por rol en el seed),
  C-20 (endpoints de catálogos y pacientes: profesionales, sillones, prestaciones y
  pacientes con la matriz RBAC, edición con unicidad que excluye al propio
  registro, desactivación y reactivación por POST, 404 NOT_FOUND y búsqueda de
  pacientes por nombre y por prefijo de DNI),
  C-21 (endpoints de horario de atención y bloqueos: `GET/PUT
  /api/professionals/{id}/working-hours` y `GET/POST
  /api/professionals/{id}/blocks`, `DELETE /api/blocks/{block_id}`, con RBAC por
  profesional, horarios en `HH:MM` local y bloqueos en UTC, turnos fuera de
  horario y afectados informados sin cancelar, y bloqueo de la fila del
  profesional para serializar con el alta de turnos),
  C-22 (endpoint para dar turnos: `POST /api/appointments` para recepción y
  administrador, duración informada o la de la prestación, conflictos de agenda
  en 409 y reglas de validez en 422 con todas las violaciones del dominio,
  turno e historial en una sola transacción y un solo turno cuando dos altas
  simultáneas piden el mismo hueco),
  C-23 (ciclo de vida del turno por API: `POST /api/appointments/{id}/cancel`,
  `/reschedule` y `/status` y `GET /api/appointments/{id}/history`, con
  cancelación y reprogramación solo para recepción y administrador, cambio de
  estado del odontólogo solo sobre sus turnos, historial propio de solo lectura
  y rechazos del dominio en 409 y 422),
  C-24 (consulta de agenda y detalle de turno por API: `GET /api/agenda` con
  ventana local en `APP_TIMEZONE` de hasta 31 días, filtros combinables por
  profesional y por sillón, sobre único con turnos enriquecidos con nombres —
  incluidos los cancelados —, plantilla semanal de horarios y bloqueos del
  rango, y `GET /api/appointments/{id}` con `200`/`404`, ambos en solo lectura
  para los tres roles),
  C-25 (base del frontend en React 18 + TypeScript `strict` + Vite 5: estructura
  `features/shared/pages`, router mínimo, tokens de diseño y paleta con
  contraste AA para los cinco estados del turno, `StatusBadge`, `LoadingState`,
  `EmptyState`, `ErrorState` y `PageShell` presentacionales, cliente HTTP tipado
  con `fetch` inyectado por parámetro y las cuatro formas de error sin
  reformular mensajes del dominio, costura de token para C-26, servicio
  `frontend` en Docker Compose en el puerto `5173` con HMR en Windows y sin
  recibir secretos del `.env`, y suite Vitest + Testing Library con mutaciones y
  trazabilidad) y
  C-26 (login y sesión en el frontend con gobernanza ALTO: `TokenStore`
  confinado a `src/features/auth/tokenStore.ts` sobre `sessionStorage` con
  fallback en memoria, pantalla `/login` accesible contra `POST /api/auth/login`
  con mensaje genérico en `401` y limpieza inmediata de contraseña, arranque de
  sesión contra `GET /api/auth/me` con estados `checking`/`authenticated`/
  `anonymous` y reintento ante fallo de red, rutas protegidas con `RequireAuth`
  y `PublicOnlyRoute` validando el destino interno con `safeInternalPath`,
  header `Authorization: Bearer <token>`, cierre automático con mensaje de
  sesión vencida ante `401` protegido, preservación de sesión ante `403`,
  menú por rol derivado de `/me` con ítems futuros deshabilitados bajo
  `"Próximamente"` y cierre de sesión directo en `AppShell`) y
  C-27 (agenda diaria de solo lectura sobre `GET /api/agenda` con gobernanza
  BAJO: ruta `/agenda` protegida para los tres roles y `/` redirigiendo a
  `/agenda`, carga inyectable de turnos, profesionales y sillones con `Clock`
  inyectado, formateo en hora local según el `timezone` de la respuesta del
  servidor, grilla diaria con eje de horas y minutos proporcionales, bandas de
  horarios de atención y bloqueos rayados, tarjetas coloreadas por estado con
  cancelados atenuados pero visibles y formato compacto en dos líneas ante
  carriles divididos o columnas angostas, filtros combinables por profesional y
  sillón en la URL con ayuda informativa, navegación por días con
  `Anterior`/`Siguiente`/`Hoy`/selector, estados de carga, vacío y error con
  reintento, delegación de `401` en C-26 y `403` visible sin cerrar sesión, y
  alternancia a tabla semántica accesible con anuncio `aria-live`) y
  C-28 (agenda semanal por profesional sobre `GET /api/agenda` con rango de 7
  días en una sola llamada y gobernanza BAJO: alternancia entre vista diaria y
  semanal mediante control `[ Día | Semana ]` en `AgendaToolbar` preservando fecha
  y filtros, 7 columnas de lunes a domingo distribuidas simultáneamente en escritorio
  a 1440 px sin scroll horizontal gracias al token `--agenda-week-column-min-width: 140px;`,
  scroll horizontal en tablet con columna de horas sticky, preselección automática
  por rol enviando `professionalId` a la API sin mezclar profesionales en contador
  ni en lista, encabezado con rango semanal y cruce de mes/año con `formatWeekLabel`,
  indicador accesible "Hoy" con texto visible y `aria-current="date"`, semana vacía
  con grilla y avisos informativos según filtros activos, tarjetas compactas en 2
  líneas con etiquetas y textos acotados con ellipsis para carriles estrechos de hasta
  ~70 px, y vista de lista con columna Fecha y orden cronológico).
- **Planificado:** el resto de las pantallas del frontend (C-29 a C-33). La persistencia de
  entidades y la API REST ya están implementadas. El plan completo
  está en [CHANGES.md](CHANGES.md).

## Requisitos

- Git
- Python 3.12 o superior

## Puesta en marcha

Los comandos usan el Python del entorno virtual directamente, así que no hace
falta activarlo. Si `python` no apunta a 3.12 o superior, usá `py -3.12` (o la
versión que tengas instalada) para crear el entorno.

### Git Bash

```bash
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia/backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/python -m mypy
```

### Base de datos local

Desde la raíz, copiá `.env.example` a `.env` y completalo con valores
ficticios:

```bash
cp .env.example .env
docker compose up -d postgres redis
docker compose ps
```

Desde `backend/`, ejecutá los tests de integración:

```bash
.venv/Scripts/python -m pytest -m integration
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m alembic current
python -m app.db.seed
```

Las migraciones llegan hasta `20261105_05_historial_sin_truncate`.

Al terminar, desde la raíz:

```bash
docker compose down
```

Si hay un PostgreSQL instalado en Windows, detenelo antes de levantar el
compose: los dos usan el puerto 5432.

### Levantar la API

Con `.env` completo, desde la raíz:

```bash
docker compose up --build
```

`<API_PORT>` es el valor definido en `.env`:

- Swagger: `http://localhost:<API_PORT>/api/docs`
- Salud: `GET http://localhost:<API_PORT>/api/health`
- Frontend: `http://localhost:5173`

### PowerShell

```powershell
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m mypy
```
### Linux / macOS

```bash
git clone https://github.com/ALucrecia-Pagano/turnos-odontologia-metodologia.git
cd turnos-odontologia-metodologia/backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m mypy
```

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
| Fotografías `hero-1-sala-de-espera.webp`, `hero-2-consultorio.webp`, `hero-3-dentista.webp`, `hero-4-instrumental.webp` y `hero-5-sillon.webp` | [frontend/src/assets/images/](frontend/src/assets/images/) | Material de demostración provisto para este TP. No se identifican autores porque no se dispone de ese dato. |
| Logo de Aqua (`logo-aqua-claro.png`, `logo-aqua-oscuro.png`, `isotipo-aqua.png` e `isotipo-aqua-claro.png`) | [frontend/src/assets/brand/](frontend/src/assets/brand/) | Provisto por la autora del TP. |
| Tipografías Jost y Manrope | Paquetes `@fontsource-variable/jost` y `@fontsource-variable/manrope` | SIL Open Font License 1.1, distribuidas por Fontsource. |

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
| Reflexión final | [docs/reflexion.pdf](docs/reflexion.pdf) |

Todos los datos de ejemplo y de prueba son ficticios, y el repositorio no
contiene credenciales.
