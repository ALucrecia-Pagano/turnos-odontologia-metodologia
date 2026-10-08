# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Stack TypeScript full-stack
**Decisión**: TypeScript en todas las capas: dominio puro, API Node.js, frontend React + Vite, tests con Vitest.
**Contexto**: el discovery dejó el stack libre ("lo define la autora"); la autora lo confirmó. Trabajo individual; el avance del 2026-10-08 solo pide el Discovery (ya hecho) y la entrega final es el jueves 2026-10-15.
**Alternativas consideradas**: Python/FastAPI + React; Java/Spring + React.
**Justificación**: un solo lenguaje permite compartir el dominio entre API y UI (tipos y pre-validación) y reduce el cambio de contexto en trabajo individual con plazo acotado.
**Trade-offs aceptados**: menos "enterprise" que Java; el tipado de TS no es una garantía en runtime (por eso Zod en el borde).
**Origen**: decisión confirmada por el usuario.

### DD-02 — Fastify como framework HTTP (sobre Express)
**Decisión**: API REST con **Fastify**.
**Contexto**: había que elegir entre Express y Fastify (indicado por el encargo).
**Alternativas consideradas**: Express (más difundido, menos tipado nativo); Fastify.
**Justificación**: tipado TypeScript de primera clase, validación por esquema integrable, `fastify.inject` permite tests de integración rápidos sin abrir puertos, buen rendimiento por defecto.
**Trade-offs aceptados**: ecosistema algo menor que Express; curva leve de plugins/hooks.

### DD-03 — SQLite con `better-sqlite3` y migraciones SQL
**Decisión**: persistencia en SQLite (archivo local) con `better-sqlite3` (API síncrona) y migraciones `.sql` versionadas.
**Contexto**: consultorio pequeño, un solo nodo, sin infraestructura externa; plazo acotado.
**Alternativas consideradas**: PostgreSQL (más robusto, requiere servicio); `sqlite3` asíncrono; ORM (Prisma/Drizzle).
**Justificación**: cero infraestructura, tests con `:memory:`, escrituras serializadas que simplifican la garantía anti-solapamiento con `BEGIN IMMEDIATE`. Sin ORM para mantener control del SQL y reducir dependencias.
**Trade-offs aceptados**: un único escritor; migrar a Postgres requerirá portar queries (aislados en repositorios).

### DD-04 — React + Vite SPA
**Decisión**: frontend como SPA con React 18 y Vite.
**Justificación**: arranque rápido, HMR, ecosistema conocido; "frontend cuidado" se logra con sistema de diseño mínimo y cobertura de estados, no con un framework más pesado.
**Trade-offs aceptados**: sin SSR (no se necesita).

### DD-05 — Estructura de monorepo con npm workspaces
**Decisión**: `packages/domain`, `apps/api`, `apps/web` en un solo repo con npm workspaces.
**Justificación**: el dominio se versiona y prueba aislado y lo consumen API y UI; evita herramientas extra (Nx, Turborepo).
**Trade-offs aceptados**: configuración inicial de workspaces/tsconfig; sin caché de builds.

### DD-06 — El dominio es la autoridad de las reglas y es puro
**Decisión**: las reglas RN-AG viven en `packages/domain`, sin I/O ni reloj global; reciben un contexto y devuelven `Result` con violaciones.
**Justificación**: pedido del discovery ("validada en el dominio, no solo en la interfaz") y requisito de Strict TDD.
**Trade-offs aceptados**: la capa de aplicación debe cargar el contexto antes de validar (más código de orquestación).

### DD-07 — Intervalos semiabiertos `[inicio, fin)` e instantes en UTC
**Decisión**: todo intervalo es semiabierto; los instantes se guardan como epoch ms UTC; los horarios laborales como minutos locales.
**Justificación**: elimina ambigüedad de turnos consecutivos; evita problemas de DST (Argentina no lo usa, pero el dominio recibe la zona como parámetro).
**Trade-offs aceptados**: conversión a hora local en la regla de horario laboral.

### DD-08 — El dominio devuelve todas las violaciones
**Decisión**: no se corta en la primera violación; se devuelven todas, ordenadas (RN-AG-12).
**Justificación**: sostiene el diferenciador "mensajes de conflicto claros" (la secretaria ve todo lo que debe corregir).
**Trade-offs aceptados**: ligera redundancia de mensajes.

### DD-09 — C-02 = solo "crear un turno sin solapamientos por profesional y por sillón"
**Decisión**: el change evaluado en el ciclo OPSX del TP es C-02 `crear-turno-sin-solapamientos` (C-01 `fundacion-monorepo-y-dominio` es su prerrequisito técnico: monorepo y paquete de dominio vacío, sin lógica de negocio). C-02 cubre únicamente la regla de no solapamiento: solapamiento por profesional (RN-AG-01), solapamiento por sillón (RN-AG-02), duración del turno según la prestación (RN-AG-07), rechazo de duración no positiva (`INVALID_DURATION`, parte mínima de RN-AG-09 / US-007 CA-1: un intervalo con fin <= inicio rompe la lógica de solapamiento semiabierto) y el caso borde de turnos consecutivos (fin == inicio no es solapamiento; intervalos semiabiertos). Corresponde a US-001 (acotada), US-002, US-003 y el criterio de duración positiva de US-007, en `packages/domain`; sin API, sin BD, sin UI. Horario de atención y bloqueos (US-004), no en el pasado (US-005), mensajes completos (US-006) y el resto de US-007 (granularidad de 5 min, referencias, medianoche) pasan a C-03 a C-08 (`validar-duracion-y-referencias`, `hora-local-y-turno-en-un-dia`, `horario-de-atencion`, `bloqueos-de-agenda`, `no-turnos-en-el-pasado`, `mensajes-de-conflicto-en-espanol`); la zona horaria queda en C-04.
**Contexto**: C-02 debe ser chico y terminable; la regla de solapamiento es el diferenciador del producto y se puede probar sin ninguna otra regla.
**Origen**: decisión del usuario en el Discovery; checklist §5 y restricciones de la cátedra (change chico y terminable). Alcance de reglas adicionales decidido en Q-13 (resuelta 2026-10-07) en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

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

### SU-06 — Sin autenticación real en el MVP
**Suposición:** el rol se simula con sesión de desarrollo; sin contraseñas ni JWT.
**Origen**: restricción "sin credenciales en el repo" + plazo acotado; el discovery define roles pero no autenticación.
**Riesgo si es falso**: la cátedra puede esperar login real.
**Cómo validar**: confirmar con la cátedra/autora. Si se pide, es un change de gobernanza CRITICAL.

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

### SU-10 — Node.js 20+ y versiones mayores listadas en 02
**Suposición:** Node.js 20 LTS o superior; Fastify 4, React 18, Vite 5, Vitest 1.
**Origen**: versiones estables al momento; la KB no las fija como contrato.
**Riesgo si es falso**: ajuste menor de dependencias.
**Cómo validar**: confirmar al inicializar `package.json`.
