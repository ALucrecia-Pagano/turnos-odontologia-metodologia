---
name: appointment-frontend-ux
description: Guía el trabajo de interfaz de la agenda de turnos odontológicos de este repo (React 18.3.1 + TypeScript strict + Vite 5 + React Router 6.30.6 + Vitest 3.2.7) para que cada pantalla respete los tokens de diseño, la accesibilidad, la zona horaria de la API, el confinamiento del token de sesión y las reglas de test C1. Usala siempre que prepares, revises o implementes un change de UI de la agenda (C-25 a C-33): vistas diaria y semanal, tarjetas de turno, filtros por profesional o sillón, formulario de dar turno, reprogramar/cancelar/estados, vista por sillón, horarios y bloqueos, catálogos y pacientes. Disparadores típicos: "revisá los escenarios de la agenda", "¿falta algún caso en esta pantalla?", "implementá la vista semanal", "las tarjetas se recortan en tablet", "el estado tapa el nombre del paciente", "consultá la documentación de React Router", "antes de archivar, verificá visualmente". Ante la duda de si una pantalla de la agenda cumple accesibilidad, tokens o hora local, consultá esta skill antes de escribir código.
---

# Appointment Frontend UX

Esta skill reúne las reglas de interfaz que hoy están repartidas entre la base de
conocimiento, los specs archivados y las decisiones de C-25, C-26 y C-27. Su
objetivo es que un change de UI de la agenda no repita la misma revisión y no
olvide ninguno de los lineamientos que ya se aprendieron en este repo.

Usala para preparar o revisar un change de UI (C-25 a C-33) y para implementar
la pantalla, no para decidir reglas de negocio: el dominio sigue siendo la
autoridad (DD-06). La UI puede anticipar un error, pero el rechazo definitivo
viene del dominio.

## Stack exacto y cuándo consultar Context7

Versiones fijadas en `frontend/package.json`. No las cambies sin un change que lo
justifique.

| Pieza | Versión | Nota |
|---|---|---|
| React / React DOM | 18.3.1 | SPA, sin SSR (DD-04) |
| React Router DOM | 6.30.6 | API de la v6, no la v7 |
| Vite | 5.4.21 | Vite 5 |
| Vitest | 3.2.7 | entorno `jsdom` para componentes |
| TypeScript | 5.9.3 | `strict`, `noUncheckedIndexedAccess` |
| Testing Library | 16.3.3 | `@testing-library/react` |
| jsdom | 31.0.0 | no mide anchos ni evalúa container queries |

**Cuándo consultar Context7 (MCP).** Antes de usar una API que pueda haber
cambiado entre versiones mayores, consultá la documentación real con el MCP
`context7` en vez de confiar en memoria:

- **React Router**: `useSearchParams`, `createMemoryRouter`, `RouterProvider`,
  rutas anidadas y loaders. Pedí explícitamente la **v6** (este repo usa
  `react-router-dom@6.30.6`); la v7 cambió paquetes y APIs.
- **React 18**: hooks concurrentes (`useTransition`, `useDeferredValue`),
  comportamiento de `StrictMode` y `useSyncExternalStore`.
- **Vite 5 / Vitest 3**: configuración de `vitest.config.ts`, `environment`,
  `globals`, cobertura y APIs de `vi` que sí existen en la 3.x.

Procedimiento: primero `resolve-library-id` con el nombre de la librería; después
`query-docs` con el ID obtenido, la versión cuando importe y una consulta puntual
(un solo concepto). No inventes APIs ni nombres de hooks: si Context7 no lo
confirma, no lo uses. Las consultas son solo de documentación pública: nunca
envíes datos de pacientes, tokens ni código con secretos.

## Tokens de diseño: nunca colores sueltos

Todos los colores, espaciados, tipografía, radios y sombras viven en
`frontend/src/shared/styles/tokens.css`. En TSX y en CSS Modules usá
`var(--token)`; nunca escribas un HEX, un `rgb()` ni un tamaño fijo suelto.

- Colores de estado del turno: usá `APPOINTMENT_STATUS_TOKENS`
  (`frontend/src/shared/styles/appointmentStatusTokens.ts`) y el componente
  `StatusBadge`; no armes badges a mano.
- Tokens de agenda ya existentes: `--agenda-hour-height`,
  `--agenda-time-gutter-width`, `--agenda-column-min-width`,
  `--agenda-column-header-height`, `--agenda-grid-line`,
  `--agenda-working-bg`, `--agenda-offhours-bg`, `--agenda-block-bg`,
  `--agenda-block-border`, `--agenda-card-radius`,
  `--agenda-card-min-height`, `--agenda-cancelled-bg`.
- Si falta un token, agregalo a `tokens.css` con un nombre semántico; no lo
  hardcodees en el componente. Los tests `tokens.test.ts` y
  `appointmentStatusTokens.test.ts` vigilan esto.

## Accesibilidad

- **El estado del turno se comunica con texto visible, nunca solo con color.**
  Es la lección de la revisión visual 2 de C-27: la iteración que reemplazó la
  etiqueta por un punto de color se descartó porque incumple "Color por estado
  más texto". El `title` no cuenta (en tablet no hay hover) y el texto oculto
  solo para lectores de pantalla tampoco alcanza. Mostrá "Reservado",
  "Confirmado", "Atendido", "Ausente" o "Cancelado" como texto.
- **Foco visible** en todo control interactivo; orden de tabulación natural; sin
  `tabIndex` en tarjetas que no tienen acción. Los controles miden al menos
  44×44 px.
- **`aria-label` completos.** Cada tarjeta de turno incluye hora, paciente,
  prestación, profesional, sillón y estado (ver `AgendaGrid.tsx`). Los bloqueos
  incluyen motivo y rango; los horarios, el rango. No uses `aria-label` vacío ni
  redundante con el texto visible.
- Anuncios de cambio de lista con `aria-live="polite"`; tablas semánticas con
  `<caption>` y `scope="col"` cuando ofrezcas vista de lista.
- Contraste AA para los cinco estados (ya resuelto por los tokens).

## Prioridad de la información en tarjetas angostas

La hora y el paciente tienen prioridad sobre el estado; el estado nunca tapa al
paciente. Es el formato en dos líneas de C-27:

- Cuando `laneCount > 1` (carriles divididos) o la columna mide menos de 260 px
  (`@container agenda-column (width < 260px)`), la fila compacta pasa a dos
  líneas:
  - línea 1: `HH:MM · Paciente` con ellipsis y todo el ancho;
  - línea 2: `StatusBadge` con texto visible en `--font-size-xs`.
- La etiqueta nunca comparte línea con el paciente. El `aria-label` completo de
  la tarjeta no cambia.
- Un turno compacto es el de menos de 45 minutos. Ver `AgendaGrid.tsx` y
  `AgendaGrid.module.css`.

## Zona horaria: siempre desde la respuesta de la API

- La zona horaria sale del campo `timezone` de la respuesta de `GET /api/agenda`
  (o de la respuesta correspondiente). No la hardcodees en componentes.
- El único fallback a `America/Argentina/Buenos_Aires` vive en
  `frontend/src/features/agenda/agendaConfig.ts`
  (`resolveAgendaTimezone`). No dupliques esa constante en otros archivos.
- Formateá instantes con `Intl.DateTimeFormat` y `timeZone` explícito
  (`agendaTime.ts`): `formatLocalDate`, `formatLocalTime`, `formatTimeRange`,
  `addDays`, `weekdayOf`. Nunca uses la zona del navegador ni `toLocaleString()`
  sin `timeZone`.
- Los instantes de la API vienen en UTC; mostralos en hora local. Un turno que
  cruza la medianoche pertenece al día local de su inicio.

## Token de sesión: solo en `features/auth/tokenStore.ts`

- El `accessToken` se lee y se escribe **únicamente** a través de
  `TokenStore` (`frontend/src/features/auth/tokenStore.ts`). Ningún componente,
  hook ni cliente HTTP toca `sessionStorage`/`localStorage` para el token.
- El header `Authorization: Bearer <token>` lo arma la capa de API a partir del
  store; no leas el token desde otro lado.
- En tests usá `createMemoryTokenStore` o inyectá el store; no simules
  `sessionStorage` global.

## Regla C1 de tests: sin mocks de módulo

Los tests de UI de este repo siguen la regla C1. **No uses** `vi.mock`,
`vi.spyOn`, `vi.stubGlobal`, fake timers (`vi.useFakeTimers`,
`vi.setSystemTime`) ni MSW. En su lugar:

- **Inyección de `fetch`**: creá el cliente con `createApiClient({ fetchFn })`
  y pasalo a `fetchAgenda`, `fetchProfessionals` o `fetchChairs`. Cada test
  define su `fetchFn` y devuelve respuestas literales tomadas del spec.
- **Inyección de `Clock`**: usá `createFixedClock("2026-11-16T12:00:00Z")` en vez
  de fake timers. El componente recibe el `Clock`; `systemClock` solo en
  producción.
- **`MemoryRouter` / `createMemoryRouter`**: renderizá la ruta con
  `createMemoryRouter(createAppRoutes(clock), { initialEntries: ["/agenda?date=2026-11-16"] })`
  y `RouterProvider`. No mockees `react-router-dom`.
- Los datos de prueba son literales y ficticios, tomados del spec; nunca datos
  reales de pacientes.
- Cada test debe poder fallar por una mutación del código de producción: si no
  falla, no prueba nada. Los tests de CSS son comprobaciones estáticas porque
  jsdom no evalúa container queries.

## Verificación visual obligatoria antes de archivar

jsdom **no mide anchos**: un texto puede estar en el DOM y en pantalla verse
recortado. Por eso, antes de archivar un change de UI:

1. Levantá la app (`npm run dev`) con datos de demo.
2. Tomá capturas en **escritorio (1440 px)** y **tablet (768 px)** al menos de:
   la vista principal, un caso con tarjetas angostas o solapadas, un estado
   vacío y, si aplica, el error.
3. Revisá en las capturas: que el paciente y la hora se lean, que el estado no
   los tape, que el foco se vea, que no haya colores sueltos y que la hora sea
   la local correcta.
4. Guardá las capturas en `docs/evidencias/capturas/` y nombralas en el verify
   del change.

Si una captura muestra un recorte que los tests no detectan, agregá primero un
test que falle (RED) y después corregí (GREEN).

## Checklist al preparar o revisar un change de UI

1. Leé el delta spec y `tasks.md` del change, y las secciones de la KB que
   correspondan: `03` (RBAC), `04` (modelo), `06` (historias), `07` (flujos) y
   `08` (Frontend cuidado).
2. Recorré los estados de toda vista: carga, vacío, error y reintento.
3. Recorré cada código de violación que la API pueda devolver y mostralo tal
   cual (código + mensaje en español), sin reescribir el mensaje del dominio.
4. Verificá permisos por rol: qué ve cada rol y qué acción puede hacer.
5. Revisá teclado, foco visible y `aria-label` completos.
6. Revisá hora local: cambio de día, semana de 7 días, turno que cruza la
   medianoche.
7. Revisá tokens: cero colores sueltos.
8. Revisá la regla C1 en los tests (sin mocks de módulo; `fetch` y `Clock`
   inyectados; `MemoryRouter`).
9. Programá la verificación visual (1440 y 768) antes de archivar.

## Referencias del repo

- `frontend/src/shared/styles/tokens.css`
- `frontend/src/shared/styles/appointmentStatusTokens.ts`
- `frontend/src/shared/components/StatusBadge.tsx`
- `frontend/src/features/agenda/agendaTime.ts`
- `frontend/src/features/agenda/agendaConfig.ts`
- `frontend/src/features/agenda/AgendaGrid.tsx` y `AgendaGrid.module.css`
- `frontend/src/features/agenda/clock.ts`
- `frontend/src/features/auth/tokenStore.ts`
- `docs/evidencias/verify-C-27.md` (§Hallazgo de la revisión visual 2)
- `knowledge-base/08_arquitectura_propuesta.md` (§Frontend cuidado)
