# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Stack fijado por la cátedra (2026-10-08)
**Decisión**: **decisión de la cátedra (2026-10-08), obligatoria.** Backend en Python con FastAPI, autenticación JWT, ORM SQLAlchemy, persistencia en PostgreSQL, Redis para las funcionalidades asincrónicas que correspondan y Docker / Docker Compose. Frontend en React + TypeScript + Vite. El dominio pasa a ser un paquete de Python puro dentro del backend, probado con pytest.
**Contexto**: la autora había elegido TypeScript full-stack (ver DD-01 v1, reemplazada, al final de este archivo). El 2026-10-08 la cátedra fijó el stack para todos los proyectos. Trabajo individual; la entrega final es el jueves 2026-10-15.
**Qué no cambia**: reglas de negocio (RN-AG, RN-TU, RN-DI, RN-PA), historias de usuario, alcance del MVP y C-02 `crear-turno-sin-solapamientos` con sus mismos escenarios. Se conservan el dominio puro con `now` inyectado, el resultado con violaciones tipadas y los mismos códigos (`PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, etc.), los instantes en UTC y la evaluación del horario en `America/Argentina/Buenos_Aires`.
**Trade-offs aceptados**: el dominio ya no se comparte con la UI (dos lenguajes); la UI puede anticipar errores, pero sin reutilizar código del dominio. Más infraestructura local (PostgreSQL, Redis y contenedores) con el mismo plazo (R10).
**Origen**: decisión de la cátedra (2026-10-08).

### DD-02 — FastAPI como framework HTTP
**Decisión**: API REST con **FastAPI**; validación de entrada con los modelos Pydantic que integra.
**Contexto**: impuesto por la cátedra (DD-01). Reemplaza a DD-02 v1 (Fastify).
**Justificación**: tipado con type hints, validación por esquema incorporada, inyección de dependencias (`Depends`) para sesión de BD, usuario autenticado y rol; `TestClient` permite tests de integración sin levantar un servidor.
**Trade-offs aceptados**: Pydantic en el borde y dataclasses en el dominio son dos modelos distintos que hay que mapear (a cambio, el dominio no depende de Pydantic).
**Origen**: decisión de la cátedra (2026-10-08).

### DD-03 — PostgreSQL con SQLAlchemy
**Decisión**: persistencia en **PostgreSQL** con **SQLAlchemy 2.x** como ORM, solo en `repositories/` y `db/`; migraciones versionadas (**Suposición:** Alembic, SU-10). Instantes en `timestamptz`. Las altas y reprogramaciones corren en una transacción que toma `SELECT ... FOR UPDATE` sobre la fila del profesional y la del sillón, siempre en el mismo orden, antes de cargar el contexto y validar.
**Contexto**: impuesto por la cátedra (DD-01). Reemplaza a DD-03 v1 (SQLite).
**Justificación**: el bloqueo de esas dos filas serializa las escrituras que podrían solaparse entre sí (mismo profesional o mismo sillón) sin serializar toda la base; el orden fijo evita deadlocks. El ORM se queda en el borde: los repositorios devuelven tipos del dominio, no modelos de SQLAlchemy.
**Alternativas consideradas**: nivel de aislamiento `SERIALIZABLE` con reintentos (más simple de escribir, exige manejar fallos de serialización); restricción `EXCLUDE USING gist` sobre `tstzrange(start_at, end_at, '[)')` como red de seguridad en la BD (posible mejora posterior; la autoridad sigue siendo el dominio, RN-GL-01).
**Trade-offs aceptados**: los tests de integración necesitan un PostgreSQL real (servicio de Compose).
**Origen**: decisión de la cátedra (2026-10-08); la estrategia de concurrencia es una propuesta de la KB.

### DD-04 — React + TypeScript + Vite SPA
**Decisión**: frontend como SPA con React 18, TypeScript en modo `strict` y Vite.
**Justificación**: coincide con lo que fija la cátedra; arranque rápido, HMR, ecosistema conocido; "frontend cuidado" se logra con sistema de diseño mínimo y cobertura de estados, no con un framework más pesado.
**Trade-offs aceptados**: sin SSR (no se necesita).
**Origen**: confirmado por la decisión de la cátedra (2026-10-08).

### DD-05 — Repositorio con `backend/` y `frontend/` orquestados con Docker Compose
**Decisión**: un solo repo con `backend/` (FastAPI; el dominio en `backend/app/domain`) y `frontend/` (React + TS + Vite). `docker-compose.yml` levanta cuatro servicios: `backend`, `frontend`, `postgres` y `redis`. Claves y contraseñas solo en `.env` (fuera de git); en el repo, `.env.example` sin valores.
**Contexto**: impuesto por la cátedra (DD-01). Reemplaza a DD-05 v1 (workspaces de npm).
**Justificación**: el dominio sigue aislado y se prueba sin infraestructura (pytest puro); Compose da un entorno reproducible con un solo comando.
**Trade-offs aceptados**: hace falta Docker para correr el sistema completo y los tests de integración.
**Origen**: decisión de la cátedra (2026-10-08).

### DD-06 — El dominio es la autoridad de las reglas y es puro
**Decisión**: las reglas RN-AG viven en el paquete de dominio de Python (`backend/app/domain`), sin I/O ni reloj global y sin importar FastAPI, SQLAlchemy ni Redis; reciben un contexto y `now` y devuelven un resultado tipado (`Ok` o lista de violaciones con código estable).
**Justificación**: pedido del discovery ("validada en el dominio, no solo en la interfaz") y requisito de Strict TDD.
**Trade-offs aceptados**: la capa de aplicación debe cargar el contexto antes de validar (más código de orquestación).

### DD-07 — Intervalos semiabiertos `[inicio, fin)` e instantes en UTC
**Decisión**: todo intervalo es semiabierto; los instantes se guardan en UTC en columnas `timestamptz` de PostgreSQL y en el dominio son `datetime` con zona (UTC); los horarios laborales, como minutos locales. El horario se evalúa en `America/Argentina/Buenos_Aires` con `zoneinfo`.
**Justificación**: elimina ambigüedad de turnos consecutivos; evita problemas de DST (Argentina no lo usa, pero el dominio recibe la zona como parámetro).
**Trade-offs aceptados**: conversión a hora local en la regla de horario laboral; el dominio trabaja solo con `datetime` con zona (nunca *naive*), para no mezclar horas locales con UTC.

### DD-08 — El dominio devuelve todas las violaciones
**Decisión**: no se corta en la primera violación; se devuelven todas, ordenadas (RN-AG-12).
**Justificación**: sostiene el diferenciador "mensajes de conflicto claros" (la secretaria ve todo lo que debe corregir).
**Trade-offs aceptados**: ligera redundancia de mensajes.

### DD-09 — C-02 = solo "crear un turno sin solapamientos por profesional y por sillón"
**Decisión**: el change evaluado en el ciclo OPSX del TP es C-02 `crear-turno-sin-solapamientos` (C-01 `fundacion-monorepo-y-dominio` es su prerrequisito técnico: estructura del repo y paquete de dominio vacío, sin lógica de negocio). C-02 cubre únicamente la regla de no solapamiento: solapamiento por profesional (RN-AG-01), solapamiento por sillón (RN-AG-02), duración del turno según la prestación (RN-AG-07), rechazo de duración no positiva (`INVALID_DURATION`, parte mínima de RN-AG-09 / US-007 CA-1: un intervalo con fin <= inicio rompe la lógica de solapamiento semiabierto) y el caso borde de turnos consecutivos (fin == inicio no es solapamiento; intervalos semiabiertos). Corresponde a US-001 (acotada), US-002, US-003 y el criterio de duración positiva de US-007, en el paquete de dominio de Python (`backend/app/domain`, tests con pytest); sin API, sin BD, sin JWT, sin UI. El cambio de stack de DD-01 no modifica este alcance ni sus escenarios. Horario de atención y bloqueos (US-004), no en el pasado (US-005), mensajes completos (US-006) y el resto de US-007 (granularidad de 5 min, referencias, medianoche) pasan a C-03 a C-08 (`validar-duracion-y-referencias`, `hora-local-y-turno-en-un-dia`, `horario-de-atencion`, `bloqueos-de-agenda`, `no-turnos-en-el-pasado`, `mensajes-de-conflicto-en-espanol`); la zona horaria queda en C-04.
**Contexto**: C-02 debe ser chico y terminable; la regla de solapamiento es el diferenciador del producto y se puede probar sin ninguna otra regla.
**Origen**: decisión del usuario en el Discovery; checklist §5 y restricciones de la cátedra (change chico y terminable). Alcance de reglas adicionales decidido en Q-13 (resuelta 2026-10-07) en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

### DD-10 — Redis reservado para funcionalidades asincrónicas
**Decisión**: Redis forma parte de Docker Compose (servicio `redis`) y se usará solo para procesamiento asincrónico (colas de tareas diferidas). **Suposición:** el MVP no tiene ninguna funcionalidad asincrónica (SU-11), así que Redis queda levantado y sin uso funcional.
**Contexto**: la cátedra exige Redis "para las funcionalidades asincrónicas que correspondan" (DD-01).
**Usos previstos (posteriores al MVP)**: recordatorios de turno (WhatsApp o e-mail) programados antes del turno; pedido y procesamiento de confirmaciones del paciente; avisos diferidos de turnos afectados por un bloqueo (RN-DI-04); lista de espera que avisa cuando se libera un hueco. Detalle en [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md).
**Regla**: Redis nunca participa de la validación de agenda; el dominio no lo importa.
**Trade-offs aceptados**: un servicio más en Compose sin uso en el MVP, a cambio de no cambiar la infraestructura cuando lleguen los recordatorios.
**Origen**: decisión de la cátedra (2026-10-08); el alcance de uso es una propuesta de la KB.

### DD-11 — Autenticación con JWT (reemplaza al rol simulado)
**Decisión**: la autenticación usa **JWT**. `POST /api/auth/login` recibe usuario y contraseña y devuelve un token de acceso firmado con `JWT_SECRET` (claims `sub`, `role`, `exp`); las rutas protegidas exigen `Authorization: Bearer <token>`. Las contraseñas se guardan solo como hash. Se mantienen los tres roles (`odontologo`, `recepcion`, `administrador`) y la matriz RBAC de [03_actores_y_roles.md](03_actores_y_roles.md).
**Contexto**: impuesto por la cátedra (DD-01). Reemplaza a SU-06 v1 (rol simulado sin autenticación).
**Alcance**: es un change posterior a C-02, en la API base (C-16) y el login de la web (C-22). **No** es parte de C-02, que es solo dominio. Gobernanza **CRITICAL**: aprobación humana explícita antes de escribir código.
**Trade-offs aceptados**: hay que manejar secretos (`JWT_SECRET`, contraseñas del seed) solo por `.env`; sin refresh tokens ni revocación en el MVP (**Suposición:** un token de acceso con vencimiento corto alcanza, SU-06).
**Origen**: decisión de la cátedra (2026-10-08).

## Supuestos inferidos

Los marcados **Suposición:** son defaults propuestos para el MVP; se confirman en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

### SU-01 — Zona horaria `America/Argentina/Buenos_Aires`
**Suposición:** todas las reglas de horario laboral se evalúan en esa zona (UTC-3, sin DST).
**Origen**: propuesta del checklist §11.6.
**Riesgo si es falso**: turnos fuera de horario mal evaluados.
**Cómo validar**: confirmar con la autora; el dominio recibe la zona por parámetro.

### SU-02 — Granularidad de 5 minutos, duración 5–480 min
**Suposición:** inicio y duración son múltiplos de 5 min; la duración máxima es 480 min.
**Origen**: inferido (el discovery no la define; Q-06).
**Riesgo si es falso**: prestaciones de duración atípica rechazadas.
**Cómo validar**: revisar el catálogo real de prestaciones; la granularidad es una constante configurable.

### SU-03 — Transiciones de estado
**Suposición:** tabla de RN-TU-02 (terminales: atendido, ausente, cancelado; reprogramar devuelve a `reservado`).
**Origen**: inferido de D.3 ("transiciones válidas explícitas") y Q-03.
**Riesgo si es falso**: se bloquean correcciones legítimas (p. ej. reactivar un cancelado).
**Cómo validar**: confirmar con la autora; la tabla es un dato, fácil de cambiar con test.

### SU-04 — Sin vínculo prestación↔sillón
**Suposición:** cualquier prestación puede darse en cualquier sillón activo.
**Origen**: Q-05 sin respuesta; es lo más simple para el MVP.
**Riesgo si es falso**: se podrían asignar prestaciones a sillones inadecuados (p. ej. con equipo de radiografía).
**Cómo validar**: confirmar; extensión prevista: `Service.requiredChairId` o lista de sillones permitidos.

### SU-05 — Bloqueo no cancela turnos existentes
**Suposición:** crear un bloqueo sobre turnos ya dados no los cancela; se informan para reprogramar.
**Origen**: Q-04; referencia de mercado (Odonthia).
**Riesgo si es falso**: turnos "huérfanos" en horarios bloqueados.
**Cómo validar**: confirmar con la autora.

### SU-06 — Alcance de la autenticación JWT en el MVP
**Suposición:** un solo token de acceso con vencimiento corto (`JWT_EXPIRES_MIN`); sin refresh tokens, sin revocación, sin recuperación de contraseña ni alta de usuarios por autoservicio (los usuarios los crea el administrador o el seed). Hash de contraseñas con un algoritmo lento estándar (bcrypt o argon2).
**Origen**: DD-11 (JWT exigido por la cátedra) + plazo acotado.
**Riesgo si es falso**: la cátedra puede esperar cierre de sesión con revocación o refresh tokens.
**Cómo validar**: confirmar con la cátedra al llegar a C-16. Es dominio de gobernanza CRITICAL.
**Reemplaza a**: SU-06 v1 — "Sin autenticación real en el MVP: el rol se simula con sesión de desarrollo; sin contraseñas ni JWT". **Reemplazada por la decisión de la cátedra (2026-10-08)**; ver DD-11.

### SU-07 — Qué estados ocupan agenda
**Suposición:** ocupan `reservado`, `confirmado` y `atendido`; liberan `cancelado` y `ausente`.
**Origen**: inferido.
**Riesgo si es falso**: dobles reservas sobre horarios que se consideraban libres (o viceversa).
**Cómo validar**: confirmar; es un solo conjunto de constantes en el dominio.

### SU-08 — Sin anticipación mínima de cancelación y `ausente` solo desde el inicio
**Suposición:** se puede cancelar en cualquier momento; `atendido`/`ausente` solo si `now >= inicio`.
**Origen**: Q-01 y Q-02.
**Riesgo si es falso**: reglas de negocio reales más estrictas.
**Cómo validar**: confirmar con la autora.

### SU-09 — Turno dentro de un solo día local
**Suposición:** un turno no cruza la medianoche.
**Origen**: inferido (horarios laborales por día).
**Riesgo si es falso**: casi nulo en consultorios diurnos.

### SU-10 — Versiones y herramientas complementarias del stack de la cátedra
**Suposición:** Python 3.12 o superior; FastAPI 0.110+, Pydantic 2, SQLAlchemy 2, PostgreSQL 16, Redis 7, pytest 8; React 18, TypeScript 5 (`strict`), Vite 5; Docker Compose v2. Herramientas que la cátedra no nombra y la KB propone: **Alembic** para migraciones (la de SQLAlchemy), **mypy `--strict`** para el chequeo de tipos del backend, el paquete `tzdata` para que `zoneinfo` funcione en Windows. La herramienta de tests de componentes del frontend se elige al llegar a C-22.
**Origen**: versiones estables al momento; la KB no las fija como contrato.
**Riesgo si es falso**: ajuste menor de dependencias.
**Cómo validar**: confirmar al inicializar `backend/pyproject.toml` y `frontend/package.json` (C-01).

### SU-11 — Sin funcionalidades asincrónicas en el MVP
**Suposición:** ninguna funcionalidad del MVP es asincrónica; Redis se levanta en Compose pero no se usa hasta los recordatorios u otras funcionalidades de la épica 7 (DD-10).
**Origen**: el alcance del MVP (01 y 06) no incluye recordatorios, notificaciones ni lista de espera; todas las operaciones son síncronas y transaccionales.
**Riesgo si es falso**: la cátedra puede esperar al menos un uso real de Redis en la entrega.
**Cómo validar**: confirmar con la cátedra. Si se pide un uso concreto, el candidato más chico es avisar de forma diferida los turnos afectados por un bloqueo (RN-DI-04), sin integraciones externas.

## Decisiones reemplazadas (trazabilidad)

Se conservan tal como estaban antes del cambio de stack. **No aplican**: rige la versión vigente indicada en cada una.

### DD-01 v1 — Stack TypeScript full-stack *(REEMPLAZADA)*
**Estado**: **reemplazada por DD-01, decisión de la cátedra (2026-10-08).**
**Decisión**: TypeScript en todas las capas: dominio puro, API Node.js, frontend React + Vite, tests con Vitest.
**Contexto**: el discovery dejó el stack libre ("lo define la autora"); la autora lo confirmó. Trabajo individual; el avance del 2026-10-08 solo pide el Discovery (ya hecho) y la entrega final es el jueves 2026-10-15.
**Alternativas consideradas**: Python/FastAPI + React; Java/Spring + React.
**Justificación**: un solo lenguaje permite compartir el dominio entre API y UI (tipos y pre-validación) y reduce el cambio de contexto en trabajo individual con plazo acotado.
**Trade-offs aceptados**: menos "enterprise" que Java; el tipado de TS no es una garantía en runtime (por eso Zod en el borde).
**Origen**: decisión confirmada por el usuario.

### DD-02 v1 — Fastify como framework HTTP (sobre Express) *(REEMPLAZADA)*
**Estado**: **reemplazada por DD-02 (FastAPI), decisión de la cátedra (2026-10-08).**
**Decisión**: API REST con **Fastify**.
**Contexto**: había que elegir entre Express y Fastify (indicado por el encargo).
**Alternativas consideradas**: Express (más difundido, menos tipado nativo); Fastify.
**Justificación**: tipado TypeScript de primera clase, validación por esquema integrable, `fastify.inject` permite tests de integración rápidos sin abrir puertos, buen rendimiento por defecto.
**Trade-offs aceptados**: ecosistema algo menor que Express; curva leve de plugins/hooks.

### DD-03 v1 — SQLite con `better-sqlite3` y migraciones SQL *(REEMPLAZADA)*
**Estado**: **reemplazada por DD-03 (PostgreSQL + SQLAlchemy), decisión de la cátedra (2026-10-08).**
**Decisión**: persistencia en SQLite (archivo local) con `better-sqlite3` (API síncrona) y migraciones `.sql` versionadas.
**Contexto**: consultorio pequeño, un solo nodo, sin infraestructura externa; plazo acotado.
**Alternativas consideradas**: PostgreSQL (más robusto, requiere servicio); `sqlite3` asíncrono; ORM (Prisma/Drizzle).
**Justificación**: cero infraestructura, tests con `:memory:`, escrituras serializadas que simplifican la garantía anti-solapamiento con `BEGIN IMMEDIATE`. Sin ORM para mantener control del SQL y reducir dependencias.
**Trade-offs aceptados**: un único escritor; migrar a Postgres requerirá portar queries (aislados en repositorios).

### DD-05 v1 — Estructura de monorepo con npm workspaces *(REEMPLAZADA)*
**Estado**: **reemplazada por DD-05 (`backend/` + `frontend/` con Docker Compose), decisión de la cátedra (2026-10-08).**
**Decisión**: `packages/domain`, `apps/api`, `apps/web` en un solo repo con npm workspaces.
**Justificación**: el dominio se versiona y prueba aislado y lo consumen API y UI; evita herramientas extra (Nx, Turborepo).
**Trade-offs aceptados**: configuración inicial de workspaces/tsconfig; sin caché de builds.

### SU-10 v1 — Node.js 20+ y versiones mayores *(REEMPLAZADA)*
**Estado**: **reemplazada por SU-10 (versiones del stack de la cátedra).**
**Suposición:** Node.js 20 LTS o superior; Fastify 4, React 18, Vite 5, Vitest 1.
