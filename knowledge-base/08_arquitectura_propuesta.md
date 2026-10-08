# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|--------------|---------|
| Dominio puro (functional core, imperative shell) | `backend/app/domain` | Reglas RN-AG testeables sin base de datos ni reloj; encaja con Strict TDD |
| Resultado tipado (`Ok` o lista de `Violation`) | API pública del dominio | Devuelve todas las violaciones con código (`Enum` estable) y mensaje, sin excepciones para flujo normal |
| Tipos de dominio inmutables | `backend/app/domain/model.py` | `@dataclass(frozen=True)` para turno, bloqueo, horario, prestación; sin modelos de SQLAlchemy ni de Pydantic |
| Inyección de reloj (`now`) | Todas las reglas dependientes del tiempo | `now: datetime` (aware, UTC) por parámetro; tests deterministas (RN-GL-04) |
| Reglas componibles | `backend/app/domain/rules/*` | Cada regla es una función `(input, ctx) -> list[Violation]`; agregar RN-PA-03 o sobreturnos luego no reescribe el motor |
| Repositorio | `backend/app/repositories` | Aísla SQLAlchemy y PostgreSQL; traduce filas a tipos del dominio; el dominio no conoce la BD |
| Caso de uso / servicio de aplicación | `backend/app/usecases` | Orquesta: transacción → bloqueo de filas → cargar contexto → dominio → persistir |
| Transacción con `SELECT ... FOR UPDATE` | Altas y reprogramaciones | Bloquea las filas del profesional y del sillón (en orden fijo) para que dos escrituras concurrentes no burlen la validación |
| Máquina de estados tabular | `backend/app/domain/appointment/transitions.py` | Tabla de RN-TU-02 en un solo lugar, probada exhaustivamente |
| Dependencias de FastAPI (`Depends`) | `backend/app/api/deps.py` | Sesión de BD, usuario autenticado (JWT) y chequeo de rol por ruta |
| Feature folders | `frontend/src/features` | Organización por funcionalidad en el frontend |

## Estructura de directorios

Repositorio con dos aplicaciones (`backend/` y `frontend/`) orquestadas por Docker Compose (decisión DD-05):

```
turnos-odontologia/
├── docker-compose.yml           # servicios: backend, frontend, postgres, redis
├── .env.example                 # nombres de variables, sin valores sensibles
├── backend/                     # Python + FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml           # dependencias; configuración de pytest y mypy
│   ├── alembic.ini
│   ├── alembic/versions/        # migraciones versionadas
│   ├── app/
│   │   ├── domain/              # Python puro: NO importa FastAPI, SQLAlchemy ni Redis
│   │   │   ├── model.py         # dataclasses: Appointment, Block, WorkingHours, Service...
│   │   │   ├── intervals.py     # intervalos [a,b), hora local, conversión a minutos
│   │   │   ├── rules/           # una regla por módulo (overlap, hours, block, past, duration)
│   │   │   ├── appointment/     # validate_new_appointment, reschedule, transitions
│   │   │   └── violations.py    # códigos (Enum) y mensajes en español
│   │   ├── api/                 # routers FastAPI, esquemas Pydantic, deps (auth, sesión)
│   │   ├── auth/                # emisión y verificación de JWT, hash de contraseñas
│   │   ├── usecases/
│   │   ├── repositories/        # SQLAlchemy → tipos del dominio
│   │   ├── db/                  # modelos SQLAlchemy, sesión, seed.py
│   │   ├── config.py            # lectura de variables de entorno
│   │   └── main.py              # creación de la app FastAPI
│   └── tests/
│       ├── domain/              # pytest: un test por escenario del spec (sin BD, sin red)
│       └── api/                 # tests de integración contra PostgreSQL de test
├── frontend/                    # React + TypeScript + Vite
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json            # strict
│   ├── vite.config.ts
│   └── src/
│       ├── features/            # agenda, turnos, configuracion, login
│       ├── shared/              # componentes UI, cliente API (con el JWT), tokens de diseño
│       ├── pages/
│       └── main.tsx
├── knowledge-base/              # esta KB
├── openspec/                    # specs y changes (CLI de OpenSpec)
└── docs/                        # documentos fuente (discovery); no escribir KB acá
```

Regla de dependencias: `api`, `usecases`, `repositories`, `db` y `auth` → `domain`; **`domain` no importa nada** del resto de `app/`, ni FastAPI, ni SQLAlchemy, ni Redis, ni Pydantic. Solo biblioteca estándar (`dataclasses`, `datetime`, `zoneinfo`, `enum`) y el paquete de datos `tzdata`. El frontend solo habla con el backend por HTTP.

## Estrategia de tests (Strict TDD)

| Capa | Herramienta | Qué cubre |
|------|-------------|-----------|
| Dominio (unit) | pytest (`@pytest.mark.parametrize` para tablas de casos) | Todos los escenarios de 06 (en C-02: US-001 acotada, US-002, US-003 y US-007 CA-1 parcial); reloj inyectado; sin BD ni red |
| API (integración) | pytest + `TestClient` de FastAPI + PostgreSQL de test (servicio de Compose) | Contratos HTTP, JWT, transacciones y bloqueo de filas, códigos 400/401/403/409/422 |
| UI (componentes) | **Suposición:** herramienta a definir al llegar a C-22 (SU-10) | Formularios, login y mensajes de error (changes de UI) |

Los tests de integración usan PostgreSQL real (no un sustituto en memoria) porque el bloqueo de filas y `timestamptz` son parte de lo que se prueba.

Ciclo obligatorio: RED → GREEN → TRIANGULATE → REFACTOR; mínimo 2 casos por comportamiento. Cobertura medida por escenarios, no solo por líneas.

## Seguridad

- **Autenticación**: **JWT** (DD-11). `POST /api/auth/login` valida usuario y contraseña (guardada solo como hash) y devuelve un token de acceso firmado con `JWT_SECRET`, con `sub` (id de usuario), `role` y `exp`. Las rutas protegidas exigen `Authorization: Bearer <token>`. Es un change posterior a C-02 (la API base, C-16) y de gobernanza **CRITICAL**: aprobación humana explícita antes de escribir código.
- **Autorización**: matriz RBAC de 03, aplicada con una dependencia de FastAPI a partir del rol del token; el dominio recibe el actor para las reglas de propiedad (RN-AC-01).
- **Validación de input**: esquemas Pydantic en el borde de la API; el dominio revalida sus invariantes.
- **Inyección SQL**: solo consultas de SQLAlchemy con parámetros ligados, nunca concatenación de SQL.
- **Secrets**: contraseñas de PostgreSQL, `JWT_SECRET` y contraseñas del seed **solo en `.env`**, que está en `.gitignore`; en el repo solo `.env.example` con los nombres y sin valores. Docker Compose lee `.env`; ningún secreto se escribe en `docker-compose.yml` ni en los `Dockerfile`.
- **Datos**: únicamente datos ficticios (RN-PA-02). El volumen de datos de PostgreSQL no se versiona.
- **CORS**: solo el origen del frontend en desarrollo (`http://localhost:5173`).
- **Normativa**: un producto real exigiría Ley 25.326 (datos personales) y Ley 26.529 (derechos del paciente); fuera del alcance del MVP, documentado como riesgo.

## Docker Compose

| Servicio | Imagen / build | Puerto local | Depende de | Notas |
|----------|----------------|--------------|------------|-------|
| `postgres` | `postgres:16` | 5432 | — | Volumen nombrado para los datos; usuario, contraseña y base desde `.env`; healthcheck con `pg_isready` |
| `redis` | `redis:7` | 6379 | — | Sin uso funcional en el MVP (DD-10); healthcheck con `redis-cli ping` |
| `backend` | `backend/Dockerfile` | 8000 | `postgres`, `redis` (healthy) | Corre las migraciones de Alembic al iniciar y levanta FastAPI |
| `frontend` | `frontend/Dockerfile` | 5173 | `backend` | Servidor de desarrollo de Vite |

Los tests de dominio no necesitan Compose (Python puro). Los de integración usan una base de test en el servicio `postgres`.

## Redis y funcionalidades asincrónicas

**Suposición (SU-11):** el MVP **no tiene ninguna funcionalidad asincrónica**. Todas las operaciones (dar, reprogramar, cambiar estado, configurar horarios y bloqueos, consultar agenda) son síncronas y transaccionales. Redis se incluye en Compose porque lo exige la cátedra y queda listo, con healthcheck, para los primeros usos asincrónicos, todos posteriores al MVP (épica 7 de 06):

| Uso previsto | Por qué es asincrónico | Cuándo |
|--------------|------------------------|--------|
| Recordatorios de turno (enlace de WhatsApp primero, API oficial después; o e-mail) | Se programan para N horas antes del turno y se envían fuera del request | Posterior al MVP (R6) |
| Pedido de confirmación al paciente y procesamiento de su respuesta | Depende de un tercero (mensajería) con latencia y reintentos | Posterior al MVP |
| Aviso de turnos afectados al crear un bloqueo (RN-DI-04) a quien corresponda | Notificación diferida, no bloquea la creación del bloqueo | Posterior al MVP (en el MVP solo se devuelve la lista en la respuesta) |
| Lista de espera: avisar cuando se libera un hueco por cancelación o ausencia | Reacciona a un evento y notifica fuera del request | Posterior al MVP |

Redis **nunca** participa de la validación de agenda: el dominio no lo importa y la garantía anti-solapamiento vive en el dominio más la transacción de PostgreSQL.

## Variables de entorno

Todas se leen de `.env` (no versionado). `.env.example` lista los nombres **sin valores**.

| Variable | Descripción | Ejemplo (no sensible) | Sensible |
|----------|-------------|-----------------------|----------|
| `APP_ENV` | Entorno de ejecución | `development` | N |
| `API_PORT` | Puerto del backend | `8000` | N |
| `POSTGRES_USER` | Usuario de PostgreSQL | — | S |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | — | **S** |
| `POSTGRES_DB` | Nombre de la base | `turnos` | N |
| `DATABASE_URL` | URL de conexión de SQLAlchemy (incluye la contraseña) | — | **S** |
| `REDIS_URL` | URL de Redis | `redis://redis:6379/0` | N |
| `JWT_SECRET` | Clave de firma de los JWT | — | **S** |
| `JWT_ALGORITHM` | Algoritmo de firma | `HS256` | N |
| `JWT_EXPIRES_MIN` | Vigencia del token de acceso, en minutos | `60` | N |
| `SEED_USER_PASSWORD` | Contraseña de los usuarios ficticios del seed (solo desarrollo) | — | **S** |
| `APP_TIMEZONE` | Zona horaria de las reglas de horario | `America/Argentina/Buenos_Aires` | N |
| `CORS_ORIGIN` | Origen permitido para el frontend | `http://localhost:5173` | N |
| `VITE_API_URL` | URL base de la API para el frontend | `http://localhost:8000/api` | N |

## Frontend cuidado

Lineamientos para los changes de UI (C-22 a C-29; el discovery exige "frontend cuidado" y lo señala como riesgo por quedar al final del plazo; la UI arranca recién con la API completa, ver CHANGES.md):

- Sistema de diseño mínimo con tokens (color, espaciado, tipografía) en `shared/`; estados por color consistentes con el estado del turno.
- Estados de carga, vacío y error en toda vista; mensajes de conflicto del dominio mostrados tal cual y con contexto.
- Accesibilidad básica: foco visible, contraste, navegación por teclado en el formulario de turno.
- Responsive básico (escritorio y tablet).
- Referencias de interacción del discovery: Odonthia (columna y color por profesional, modo compacto), Open Dental (vistas por operatorio, Pinboard), DentalBox (vista por box, arrastre).

## Plan de contingencia de plazo

Hitos: el avance del 2026-10-08 solo pide el Discovery (ya hecho), y la entrega final es el jueves 2026-10-15. El orden de trabajo lo fija `CHANGES.md` y no se ancla a ninguna fecha intermedia.

Si el plazo aprieta: priorizar el camino crítico de `CHANGES.md` (dominio completo con tests, API de turnos, UI con agenda diaria y formulario de turno). Recortar en este orden los changes fuera del camino crítico: C-24 (vista semanal), C-27 (vista por sillón), C-28 y C-29 (UI de horarios, bloqueos y catálogos; con seeds y la API alcanza para operar) y C-18 (API de horarios; los horarios pueden venir de seeds). Postergar vistas antes que recortar tests.
