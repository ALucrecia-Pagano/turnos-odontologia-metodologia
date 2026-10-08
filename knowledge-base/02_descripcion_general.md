# Descripción General

## Stack tecnológico

**Decisión de la cátedra (2026-10-08), obligatoria**: backend en **Python + FastAPI** con JWT, SQLAlchemy y PostgreSQL; Redis para lo asincrónico; Docker Compose; frontend **React + TypeScript + Vite**. Reemplaza al stack TypeScript full-stack que había elegido la autora. Ver DD-01 a DD-05, DD-10 y DD-11 en [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) (las decisiones anteriores quedan allí marcadas como reemplazadas).

| Capa | Tecnología | Versión mínima | Notas |
|------|------------|----------------|-------|
| Lenguaje backend | Python con type hints | 3.12 | **Suposición:** 3.12 o superior; chequeo estático con `mypy --strict` (SU-10) |
| Dominio | Python puro, sin dependencias de framework | — | Paquete dentro del backend; no importa FastAPI, SQLAlchemy ni Redis. Sin I/O, sin reloj global: `now` se inyecta |
| Tests | **pytest** | 8.x | Strict TDD: cada escenario del spec tiene test automatizado |
| Backend | **FastAPI** (API REST) | 0.110+ | Decisión de la cátedra (DD-02) |
| Validación de borde | Pydantic (incluido en FastAPI) | 2.x | Solo en la API; el dominio valida sus propias reglas |
| Autenticación | **JWT** (token Bearer) | — | Reemplaza al rol simulado; change posterior a C-02 (DD-11) |
| ORM | **SQLAlchemy** | 2.x | Solo en repositorios y modelos de persistencia (DD-03) |
| Migraciones | Alembic | 1.x | **Suposición:** la herramienta de migraciones de SQLAlchemy (SU-10) |
| Persistencia | **PostgreSQL** | 16 | Instantes en `timestamptz` (UTC) (DD-03, DD-07) |
| Asincronía | **Redis** | 7 | **Suposición:** sin funcionalidad asincrónica en el MVP (DD-10, SU-11) |
| Frontend | **React + TypeScript + Vite** (SPA) | React 18 / TS 5 / Vite 5 | "Frontend cuidado" (DD-04) |
| Contenedores | **Docker / Docker Compose** | Compose v2 | Servicios `backend`, `frontend`, `postgres`, `redis` (DD-05) |

## Arquitectura general

```
                 ┌──────────────────────────────────┐
                 │ frontend (React + TS + Vite)     │   SPA: agenda, ABM, vista recepción
                 └────────────────┬─────────────────┘
                                  │ HTTP/JSON (REST) + Authorization: Bearer <JWT>
                 ┌────────────────▼─────────────────┐
                 │ backend (FastAPI)                │   rutas, validación Pydantic, JWT,
                 │   ├─ casos de uso                │   mapeo de errores; cargan contexto,
                 │   └─ repositorios SQLAlchemy     │   llaman al dominio, persisten
                 └──┬──────────────┬─────────────┬──┘
                    │              │             │
       ┌────────────▼───┐  ┌───────▼──────┐  ┌───▼──────────────────────┐
       │ app/domain     │  │ PostgreSQL   │  │ Redis (sin uso en el MVP;│
       │ (Python puro)  │  │ (timestamptz)│  │ asincronía futura)       │
       └────────────────┘  └──────────────┘  └──────────────────────────┘

       Todo corre con Docker Compose: backend · frontend · postgres · redis
```

Principios:

1. **El dominio es la fuente de verdad de las reglas.** Las reglas de agenda (RN-AG-xx) viven en el paquete de dominio del backend (`backend/app/domain`) y no se duplican en la capa HTTP ni en la UI. La UI puede anticipar errores, pero el rechazo definitivo es del dominio.
2. **Dominio puro.** Funciones que reciben un *contexto* (profesional, sillón, prestación, horarios, bloqueos, turnos existentes relevantes, `now`) y devuelven un resultado tipado (`ok` o lista de violaciones con código estable: `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP`, `INVALID_DURATION`, etc.). Sin base de datos, sin `datetime.now()`.
3. **Persistencia como borde.** Los casos de uso cargan el contexto desde PostgreSQL vía SQLAlchemy, invocan al dominio y, si es válido, guardan dentro de una transacción. El dominio no conoce los modelos de SQLAlchemy: los repositorios los traducen a tipos del dominio.
4. **Concurrencia.** Dos solicitudes simultáneas no deben burlar la validación: la creación/reprogramación corre en una transacción que primero toma `SELECT ... FOR UPDATE` sobre las filas del profesional y del sillón (siempre en el mismo orden, para evitar deadlocks), recarga el contexto y valida dentro de ella (DD-03).

## Integraciones externas

**Ninguna en el MVP.** WhatsApp, Google Calendar, Mercado Pago y ARCA quedan como etapas posteriores (ver [06_funcionalidades.md](06_funcionalidades.md), épica 7). Redis queda disponible para cuando esas integraciones necesiten procesamiento asincrónico (DD-10).

## API REST (resumen)

Prefijo `/api`. Formato JSON. Errores de regla de negocio: HTTP `409` (conflicto de agenda) o `422` (regla de validez); entrada malformada: `400`. Detalle de contratos y códigos de error en [07_flujos_principales.md](07_flujos_principales.md).

| Recurso | Endpoints principales |
|---------|-----------------------|
| Profesionales | `GET/POST /professionals`, `GET/PATCH /professionals/:id` |
| Horarios de atención | `GET/PUT /professionals/:id/working-hours` |
| Bloqueos | `GET/POST /professionals/:id/blocks`, `DELETE /blocks/:id` |
| Sillones | `GET/POST /chairs`, `PATCH /chairs/:id` |
| Prestaciones | `GET/POST /services`, `PATCH /services/:id` |
| Pacientes (ficticios) | `GET/POST /patients`, `GET/PATCH /patients/:id` |
| Turnos | `GET /appointments?from&to&professionalId&chairId`, `POST /appointments`, `POST /appointments/:id/reschedule`, `POST /appointments/:id/status`, `GET /appointments/:id/history` |
| Autenticación | `POST /auth/login` (devuelve el JWT), `GET /auth/me` |
| Salud | `GET /health` |

## Zona horaria

`America/Argentina/Buenos_Aires` (UTC-3, sin horario de verano). Los instantes se guardan en UTC en columnas `timestamptz` de PostgreSQL; en el dominio son `datetime` con zona (*aware*) en UTC. Las reglas de horario laboral se evalúan en hora local con `zoneinfo.ZoneInfo`, recibiendo la zona por parámetro. En Windows, `zoneinfo` necesita el paquete `tzdata` para conocer la zona. Ver SU-01 y [10_preguntas_abiertas.md](10_preguntas_abiertas.md).
