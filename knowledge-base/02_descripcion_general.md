# Descripción General

## Stack tecnológico

Decisión confirmada por la autora: **TypeScript full-stack**. Ver DD-01 a DD-04 en [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md).

| Capa | Tecnología | Versión mínima | Notas |
|------|------------|----------------|-------|
| Lenguaje | TypeScript (modo `strict`) | 5.x | En todos los paquetes |
| Runtime | Node.js LTS | 20 | **Suposición:** 20 o superior |
| Dominio | TypeScript puro, sin dependencias de framework | — | Sin I/O, sin reloj global: `now` se inyecta |
| Tests | Vitest | 1.x | Strict TDD: cada escenario del spec tiene test automatizado |
| Backend | Node.js + **Fastify** (API REST) | 4.x | Elegido sobre Express (DD-02) |
| Persistencia | **SQLite** vía `better-sqlite3` | — | Archivo local; migraciones SQL versionadas (DD-03) |
| Validación de borde | Zod | 3.x | Solo en la API; el dominio valida sus propias reglas |
| Frontend | **React + Vite** (SPA) | React 18 / Vite 5 | "Frontend cuidado" (DD-04) |
| Gestión de paquetes | npm workspaces | — | Estructura tipo monorepo (ver 08) |

## Arquitectura general

```
                 ┌────────────────────────────┐
                 │  apps/web (React + Vite)   │   SPA: agenda, ABM, vista recepción
                 └─────────────┬──────────────┘
                               │ HTTP/JSON (REST)
                 ┌─────────────▼──────────────┐
                 │  apps/api (Fastify)        │   rutas, validación Zod, mapeo de errores
                 │   ├─ casos de uso          │   cargan contexto, llaman al dominio, persisten
                 │   └─ repositorios SQLite   │
                 └───────┬───────────┬────────┘
                         │           │
              ┌──────────▼───┐   ┌───▼─────────────┐
              │ packages/    │   │  SQLite (archivo)│
              │ domain (TS   │   └─────────────────┘
              │ puro)        │
              └──────────────┘
```

Principios:

1. **El dominio es la fuente de verdad de las reglas.** Las reglas de agenda (RN-AG-xx) viven en `packages/domain` y no se duplican en la API ni en la UI. La UI puede anticipar errores, pero el rechazo definitivo es del dominio.
2. **Dominio puro.** Funciones que reciben un *contexto* (profesional, sillón, prestación, horarios, bloqueos, turnos existentes relevantes, `now`) y devuelven un resultado tipado (`ok` o lista de violaciones). Sin base de datos, sin `Date.now()`.
3. **Persistencia como borde.** La API carga el contexto desde SQLite, invoca al dominio y, si es válido, guarda dentro de una transacción.
4. **Concurrencia.** Dos solicitudes simultáneas no deben burlar la validación: la creación/reprogramación corre en una transacción `BEGIN IMMEDIATE` (SQLite serializa escritores) que recarga el contexto y valida dentro de ella.

## Integraciones externas

**Ninguna en el MVP.** WhatsApp, Google Calendar, Mercado Pago y ARCA quedan como etapas posteriores (ver [06_funcionalidades.md](06_funcionalidades.md), épica 7).

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
| Salud | `GET /health` |

## Zona horaria

`America/Argentina/Buenos_Aires` (UTC-3, sin horario de verano). Los instantes se guardan en UTC (epoch ms); las reglas de horario laboral se evalúan en hora local. Ver SU-01 y [10_preguntas_abiertas.md](10_preguntas_abiertas.md).
