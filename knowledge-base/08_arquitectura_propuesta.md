# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|--------------|---------|
| Dominio puro (functional core, imperative shell) | `packages/domain` | Reglas RN-AG testeables sin base de datos ni reloj; encaja con Strict TDD |
| Resultado tipado (`Result<T, Violation[]>`) | API pública del dominio | Devuelve todas las violaciones con código y mensaje, sin excepciones para flujo normal |
| Inyección de reloj (`now`) | Todas las reglas dependientes del tiempo | Tests deterministas (RN-GL-04) |
| Reglas componibles | `packages/domain/src/rules/*` | Cada regla es una función `(input, ctx) => Violation[]`; agregar RN-PA-03 o sobreturnos luego no reescribe el motor |
| Repositorio | `apps/api/src/repositories` | Aísla SQLite; el dominio no conoce la BD |
| Caso de uso / servicio de aplicación | `apps/api/src/usecases` | Orquesta: transacción → cargar contexto → dominio → persistir |
| Transacción `BEGIN IMMEDIATE` | Altas y reprogramaciones | Evita que dos escrituras concurrentes burlen la validación |
| Máquina de estados tabular | `domain/src/appointment/transitions.ts` | Tabla de RN-TU-02 en un solo lugar, probada exhaustivamente |
| Feature folders | `apps/web/src/features` | Organización por funcionalidad en el frontend |

## Estructura de directorios

Estructura tipo monorepo con npm workspaces (decisión DD-05):

```
turnos-odontologia/
├── package.json                 # workspaces: packages/*, apps/*
├── tsconfig.base.json           # strict, target ES2022
├── vitest.workspace.ts
├── .env.example                 # sin secretos reales
├── packages/
│   └── domain/                  # TypeScript puro, sin dependencias de framework
│       ├── src/
│       │   ├── model/           # tipos: Appointment, Block, WorkingHours, Service...
│       │   ├── time/            # intervalos [a,b), hora local, conversión a minutos
│       │   ├── rules/           # una regla por archivo (overlap, hours, block, past, duration)
│       │   ├── appointment/     # validateNewAppointment, reschedule, transitions
│       │   ├── violations.ts    # códigos y mensajes en español
│       │   └── index.ts
│       └── test/                # Vitest: un test por escenario del spec
├── apps/
│   ├── api/                     # Fastify + SQLite
│   │   ├── src/
│   │   │   ├── server.ts
│   │   │   ├── routes/
│   │   │   ├── usecases/
│   │   │   ├── repositories/
│   │   │   ├── db/              # conexión, migrations/*.sql, seed.ts
│   │   │   └── config.ts        # lectura de variables de entorno
│   │   └── test/                # tests de integración (inyección de Fastify + SQLite en memoria)
│   └── web/                     # React + Vite
│       └── src/
│           ├── features/        # agenda, turnos, configuracion
│           ├── shared/          # componentes UI, cliente API, tokens de diseño
│           ├── pages/
│           └── main.tsx
├── knowledge-base/              # esta KB
├── openspec/                    # specs y changes (CLI de OpenSpec)
└── docs/                        # documentos fuente (discovery); no escribir KB acá
```

Regla de dependencias: `apps/*` → `packages/domain`; **`domain` no importa nada** de `apps/*`, ni de Fastify, ni de SQLite, ni de React.

## Estrategia de tests (Strict TDD)

| Capa | Herramienta | Qué cubre |
|------|-------------|-----------|
| Dominio (unit) | Vitest | Todos los escenarios de 06 (en el primer change: US-001 acotada, US-002, US-003 y US-007 CA-1 parcial); tablas de casos; reloj inyectado |
| API (integración) | Vitest + `fastify.inject` + SQLite `:memory:` | Contratos HTTP, transacciones, códigos 400/401/403/409/422 |
| UI (componentes) | Vitest + Testing Library | Formularios y mensajes de error (changes de UI) |

Ciclo obligatorio: RED → GREEN → TRIANGULATE → REFACTOR; mínimo 2 casos por comportamiento. Cobertura medida por escenarios, no solo por líneas.

## Seguridad

- **Autenticación**: MVP sin autenticación real; rol simulado (SU-06). Autenticación real = change posterior, gobernanza CRITICAL (aprobación humana previa).
- **Autorización**: matriz RBAC de 03, aplicada en un *preHandler* de Fastify; el dominio recibe el actor para las reglas de propiedad (RN-AC-01).
- **Validación de input**: Zod en el borde de la API; el dominio revalida sus invariantes.
- **Inyección SQL**: solo sentencias preparadas (`better-sqlite3`), nunca concatenación.
- **Secrets**: no hay secretos en el MVP; `.env` en `.gitignore`; solo `.env.example` sin valores sensibles.
- **Datos**: únicamente datos ficticios (RN-PA-02). El archivo `.sqlite` local se ignora en git.
- **CORS**: solo el origen del frontend en desarrollo (`http://localhost:5173`).
- **Normativa**: un producto real exigiría Ley 25.326 (datos personales) y Ley 26.529 (derechos del paciente); fuera del alcance del MVP, documentado como riesgo.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|----------|-------------|---------|----------|
| `NODE_ENV` | Entorno de ejecución | `development` | N |
| `PORT` | Puerto de la API | `3000` | N |
| `DATABASE_PATH` | Ruta del archivo SQLite | `./data/turnos.sqlite` | N |
| `APP_TIMEZONE` | Zona horaria de las reglas de horario | `America/Argentina/Buenos_Aires` | N |
| `CORS_ORIGIN` | Origen permitido para el frontend | `http://localhost:5173` | N |
| `ALLOW_DEV_ROLE_HEADER` | Habilita rol simulado por cabecera (solo desarrollo) | `true` | N |
| `VITE_API_URL` | URL base de la API para el frontend | `http://localhost:3000/api` | N |

## Frontend cuidado

Lineamientos para el change de UI (el discovery exige "frontend cuidado" y lo señala como riesgo por quedar al final del plazo; la UI llega después del avance del 2026-10-08, salvo que se decida lo contrario):

- Sistema de diseño mínimo con tokens (color, espaciado, tipografía) en `shared/`; estados por color consistentes con el estado del turno.
- Estados de carga, vacío y error en toda vista; mensajes de conflicto del dominio mostrados tal cual y con contexto.
- Accesibilidad básica: foco visible, contraste, navegación por teclado en el formulario de turno.
- Responsive básico (escritorio y tablet).
- Referencias de interacción del discovery: Odonthia (columna y color por profesional, modo compacto), Open Dental (vistas por operatorio, Pinboard), DentalBox (vista por box, arrastre).

## Plan de contingencia de plazo

Hitos: **avance el 2026-10-08** y **entrega final la semana siguiente (fecha a confirmar)**. Para el avance, lo mínimo es el primer change terminado; el resto se ordena hacia la entrega final.

Si el plazo aprieta: priorizar (1) dominio completo con tests, (2) API mínima de turnos, (3) UI con agenda diaria y formulario de turno. Postergar vista semanal y vista por sillón antes que recortar tests.
