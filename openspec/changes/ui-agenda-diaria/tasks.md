# Tasks

> **Regla para todas las tareas de los grupos 1 a 15: test ANTES del código.**
>
> 1. Escribir los tests nombrados y correrlos **antes del código**, redirigiendo la salida a `docs/evidencias/red-C-27/<tarea>.txt`. Desde `frontend/`: `npm run test:run -- <archivo> > ../docs/evidencias/red-C-27/<tarea>.txt 2>&1`.
> 2. Verificar en ese archivo que fallan por la causa esperada.
> 3. **Si un test pasa de entrada, mutación obligatoria**: romper el código de producción, ver fallar el test, restaurar y redirigir la salida a `red-C-27/<tarea>-mutacion.txt`.
> 4. Escribir el código mínimo, refactorizar, volver a correr los tests y marcar la tarea.
>
> **Regla C1 (sin mocks ni reemplazos globales).** Prohibido en los tests del front: `vi.mock`, `vi.spyOn`, `vi.stubGlobal`, `vi.fn` como reemplazo de módulos, MSW y cualquier reemplazo global. El cliente de API recibe la función `fetch` **por parámetro** y los tests le pasan una función real que devuelve `new Response(...)`. El reloj se inyecta con la interfaz `Clock`; no se usan timers falsos. Es el equivalente de la regla "sin mock, patch ni monkeypatch" del backend.
>
> **Regla de aserciones.** Usar `queryBy*`/`findBy*` combinados con `expect(...)` para presencia y ausencia; no usar `getBy*` como única aserción. Sin `any` explícito ni `@ts-ignore`/`@ts-expect-error`. Solo datos ficticios del seed (`Dra. Laura Quiroga`, `Dr. Martín Sosa`, `Dra. Paula Benítez`, `Sillón 1`, `Sillón 2`, `Control`, `Ana Pérez`, `Bruno Acosta`). `tsc --noEmit` y ESLint son obligatorios. No se commitea. Las evidencias se generan siempre redirigiendo la salida a archivo, nunca pegadas ni redactadas a mano.

## 0. Precondiciones

- [ ] 0.1 Verificar GATE 16: C-26 (`ui-login-y-sesion`) **implementado, verde y ARCHIVADO** y sus dependencias (`C-25`, `C-24`, `C-22`/`C-23`, `C-19`) archivadas. Redirigir a `docs/evidencias/precondicion-C-27.txt` la salida de `openspec list`, `openspec list --specs` y de `ls openspec/changes/archive`. Confirmar que `frontend/` existe con el cliente de `fetch` inyectado, `AuthContext`, `RequireAuth`, el shell y la regla C1. **Si C-26 no está archivado o `frontend/` no existe, detenerse** (D15, D19).
- [ ] 0.2 Línea de base desde `frontend/`: `npm run test:run`, `npm run typecheck` y `npm run lint`, redirigidos a `docs/evidencias/baseline-C-27.txt`. Todo tiene que estar en verde.

## 1. R3 — Conversión a hora local con el timezone de la respuesta (C1)

- [ ] 1.1 Test en `src/features/agenda/agendaTime.test.ts` de un módulo puro con `Intl` y `timeZone` explícito (D1, C1): `13:00Z` → `10:00` en `America/Argentina/Buenos_Aires`; `2026-11-16T02:30:00Z` → día `2026-11-15` a las `23:30`; `2026-11-16T03:30:00Z` → `2026-11-16` a las `00:30`; `addDays` cruza mes y año; `weekdayOf` devuelve ISO con domingo `7`; `24:00` → 1440; `appointmentRange` con medianoche; una zona con DST (`America/New_York`) no altera la hora de Buenos Aires. Implementar `frontend/src/features/agenda/agendaTime.ts`. RED archivado en `red-C-27/1.1-tiempo.txt`.
- [ ] 1.2 Tests en `src/features/agenda/clock.test.ts` y `src/features/agenda/agendaConfig.test.ts` (D2, C1): `Clock { now(): Date }` con `systemClock`; el valor de respaldo `America/Argentina/Buenos_Aires` vive en un único archivo y solo se usa antes de la primera respuesta; `new Date()` aparece únicamente en `clock.ts`. Implementar `frontend/src/features/agenda/clock.ts` y `frontend/src/features/agenda/agendaConfig.ts`. RED archivado en `red-C-27/1.2-clock-config.txt`.
- [ ] 1.3 Test guardián en `src/features/agenda/agendaTimeGuard.test.ts` (D1, D17, C1): escanea `src/features/agenda` y prohíbe `getHours`, `getMinutes`, `getDate`, `getDay`, `getMonth`, `getFullYear`, `getTimezoneOffset` y `toLocale*` sin `timeZone`; permite `getUTC*`, `Date.UTC` y `new Date()` solo en `clock.ts`. Correr `agendaTime.test.ts` con `TZ=Asia/Tokyo` desde `frontend/` y archivar la salida en `red-C-27/1.3-tz-tokyo.txt`: el turno `13:00Z` sigue siendo `10:00` y la fecha `2026-11-16`.

## 2. R4 — Eje de horas

- [ ] 2.1 Tests en `src/features/agenda/agendaLayout.test.ts` de `computeAxis`/`clampRange` (D4): lunes `2026-11-16` con horarios `09:00–13:00` y `15:00–19:00`, bloqueo `12:00–13:00` y turnos → eje `08:00–20:00`; día vacío `2026-11-15` → `08:00–20:00`; rango menor a 4 horas se expande; bloqueo `23:00–01:00` y turno `23:30–00:00` se clampean a `[0, 1440]`. Implementar `computeAxis` y `clampRange` en `frontend/src/features/agenda/agendaLayout.ts`. RED archivado en `red-C-27/2.1-eje.txt`.

## 3. R5 — Columnas por profesional

- [ ] 3.1 Tests en `src/features/agenda/agendaLayout.test.ts` de `groupByProfessional`/`compareProfessionals` (D6): columnas desde el catálogo, unión defensiva con la agenda, inactivos con marca `(inactivo)`, orden estable con `localeCompare("es", { sensitivity: "base" })` y desempate por `id`, columna vacía conservada y `professionalId` que deja una sola columna. Implementar las funciones. RED archivado en `red-C-27/3.1-columnas.txt`.

## 4. R6 — Posición, alto y carriles

- [ ] 4.1 Tests en `src/features/agenda/agendaLayout.test.ts` de `assignLanes`/`appointmentRange` (D5): turnos sin solape, cancelado + activo a las `09:00–09:30`, tres turnos en cadena, turno de 5 minutos con alto mínimo, turno que empieza antes del eje (clampeado) y turno que termina a las `00:00`. Implementar las funciones. RED archivado en `red-C-27/4.1-carriles.txt`.

## 5. R2 — Carga con fetch y Clock inyectados

- [ ] 5.1 Tests en `src/features/agenda/agendaApi.test.ts` con `fetch` inyectado y `new Response(...)` real (D16, C1): tipos y parser mínimo de `AgendaResponse`/`AgendaAppointment`/`AgendaWorkingHours`/`AgendaBlock`/`Professional`/`Chair`; `fetchAgenda` pide `GET /api/agenda?from=2026-11-16&to=2026-11-16`; 200 completo, 400 con `errors[]`, 401, 403, 500, error de red y JSON malformado; `fetchProfessionals` y `fetchChairs`; `signal` se pasa a `init.signal`. Agregar `signal?: AbortSignal` aditivo a `RequestOptions` en `frontend/src/shared/api/client.ts`. Implementar `frontend/src/features/agenda/agendaApi.ts`. RED archivado en `red-C-27/5.1-api.txt`.
- [ ] 5.2 Tests en `src/features/agenda/useAgenda.test.tsx` con un componente de prueba y fetch real (D10, D16): las tres requests salen en paralelo; `Promise.allSettled` permite que falle el catálogo sin bloquear la agenda; estados `loading`/`refreshing`/`success`/`error`; `refresh` manual; una promesa pendiente y un cambio de fecha demuestran que la respuesta vieja se ignora con `AbortController` + id. Implementar `frontend/src/features/agenda/useAgenda.ts`. RED archivado en `red-C-27/5.2-hook.txt`.

## 6. R1 — Ruta /agenda, redirección de / y menú

- [ ] 6.1 Tests en `src/App.test.tsx`, `src/features/auth/menuFor.test.ts` y `src/shared/components/AppShell.test.tsx` (D15): con sesión, `/` redirige con `replace` a `/agenda?date=2026-11-16` según el `Clock`; `Agenda` queda habilitada para `administrador`, `recepcion` y `odontologo`; los demás ítems siguen deshabilitados con `"Próximamente"`; el logout sigue funcionando. Implementar la ruta hija `agenda`, el `Navigate` del `index`, `menuFor` con Agenda habilitada y `NavLink` en `AppShell`. RED archivado en `red-C-27/6.1-ruta-menu.txt`.

## 7. R4/R5/R6 UI — Grilla, eje, columnas, tarjetas y carriles

- [ ] 7.1 Tests en `src/features/agenda/AgendaView.test.tsx` como componente presentacional sin `useAuth` (D6–D13): eje `08:00–20:00`; tres columnas en orden estable; inactivo con marca; columna vacía con `Sin turnos`; turno de Quiroga de `10:00–10:30` posicionado 120 minutos desde el inicio y 30 de alto; cancelado + activo en dos carriles; turno de 5 minutos con alto mínimo. Implementar `AgendaView.tsx`, `AgendaGrid.tsx` y estilos. RED archivado en `red-C-27/7.1-grilla.txt`.

## 8. R7 — Horarios de atención, bloqueos y cancelados

- [ ] 8.1 Tests en `src/features/agenda/AgendaView.test.tsx` (D7): bandas de horario de Quiroga `09:00–13:00` y `15:00–19:00`; bloqueo `12:00–13:00` con motivo `Congreso` y etiqueta `Bloqueo: Congreso, de 12:00 a 13:00`; el cancelado de Sosa de `09:00–09:30` sigue visible, atenuado y con el texto `Cancelado`. Implementar las bandas y capas. RED archivado en `red-C-27/8.1-capas.txt`.

## 9. R8 — Color por estado más texto

- [ ] 9.1 Tests en `src/features/agenda/AgendaView.test.tsx` (D7, D13): `Reservado` y `Cancelado` visibles como texto y con los tokens AA de `APPOINTMENT_STATUS_TOKENS`; sin HEX en TSX; el nombre accesible de la tarjeta incluye `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control` y `Reservado`. Implementar el uso de `StatusBadge` y el `aria-label` completo. RED archivado en `red-C-27/9.1-estado.txt`.

## 10. R9 — Filtros por profesional y sillón con estado en la URL

- [ ] 10.1 Tests en `src/features/agenda/AgendaPage.test.tsx` y `src/features/agenda/AgendaToolbar.test.tsx` con `AuthProvider` real y `createMemoryRouter` (D8, D9): elegir Sillón 2 deja `chairId=00000000-0000-0000-0000-0000000000b2` en la URL, pide `chairId`, muestra solo el turno de Sosa y conserva el bloqueo `Congreso` y los horarios con la ayuda visible; elegir Quiroga deja `professionalId=00000000-0000-0000-0000-000000000001` y filtra las tres colecciones; combinados sin turnos muestran `Sin turnos para este filtro`; `Limpiar filtros` conserva la fecha. Implementar filtros en `AgendaPage.tsx`/`AgendaToolbar.tsx`. RED archivado en `red-C-27/10.1-filtros.txt`.

## 11. R10 — Navegación anterior, siguiente, Hoy y selector

- [ ] 11.1 Tests en `src/features/agenda/AgendaPage.test.tsx` (D3): desde `2026-11-16`, `Anterior` deja `2026-11-15` con `push` y pide ese día; `Siguiente` vuelve a `2026-11-16`; `Hoy` con `Clock` fijo en `2026-11-16T12:00:00Z` deja `2026-11-16`; el selector acepta `2026-12-01`; una fecha inválida se normaliza con `replace` y muestra el aviso. Implementar la barra de navegación. RED archivado en `red-C-27/11.1-navegacion.txt`.

## 12. R11 — Estados de carga, vacío y error

- [ ] 12.1 Tests en `src/features/agenda/AgendaPage.test.tsx` y `src/features/agenda/AgendaView.test.tsx` (D10): carga inicial con `role="status"` y `Cargando...`; día `2026-11-16` sin turnos con la grilla y `No hay turnos para este día`; error de red o `5xx` con `ErrorState` y `Reintentar`; al reintentar con `200` se renderiza la agenda; actualización manual con `Actualizar agenda` y sin polling. Implementar los estados. RED archivado en `red-C-27/12.1-estados.txt`.

## 13. R12 — 401 delegado en C-26 y 403 visible

- [ ] 13.1 Tests en `src/features/agenda/AgendaPage.test.tsx` (D10): un `401` de `GET /api/agenda` descarta el token, redirige a `/login` con `La sesión venció. Iniciá sesión de nuevo.` y no muestra error local; un `403` con `No tiene permiso para leer la agenda.` muestra la violación, conserva la sesión, no redirige y no duplica el banner global. Implementar el manejo en `useAgenda`/`AgendaPage`. RED archivado en `red-C-27/13.1-401-403.txt`.

## 14. R13 — Vista en lista accesible

- [ ] 14.1 Tests en `src/features/agenda/AgendaTable.test.tsx` y `src/features/agenda/AgendaView.test.tsx` (D11): el toggle visible `Ver como lista` muestra la tabla con caption `Turnos del lunes 16 de noviembre de 2026`; encabezados `Hora`, `Paciente`, `Profesional`, `Sillón`, `Prestación` y `Estado`; fila de Quiroga `10:00–10:30`, `Ana Pérez`, `Dra. Laura Quiroga`, `Sillón 1`, `Control`, `Reservado`; mismos datos y orden que la grilla; `aria-live` anuncia `Turnos del lunes 16 de noviembre de 2026: 2`. Implementar `AgendaTable.tsx` y el toggle. RED archivado en `red-C-27/14.1-lista.txt`.

## 15. R14 — Responsive para escritorio y tablet

- [ ] 15.1 Test en `src/features/agenda/agendaStyles.test.ts` (D12, D13): el contenedor de grilla expone scroll horizontal, encabezado y columna de horas con clases `sticky`, ancho mínimo por columna y controles de al menos 44×44 px; los tokens de agenda existen en `tokens.css`. Implementar tokens y CSS Modules. La comprobación visual a 1024×768 y 768×1024 se completa en la tarea 16.6. RED archivado en `red-C-27/15.1-responsive.txt`.

## 16. Verificación y evidencias

- [ ] 16.1 `npm run typecheck > ../docs/evidencias/tsc-C-27.txt 2>&1` desde `frontend/`, sin errores.
- [ ] 16.2 `npm run lint > ../docs/evidencias/eslint-C-27.txt 2>&1` desde `frontend/`, sin warnings.
- [ ] 16.3 `npm run test:run > ../docs/evidencias/vitest-C-27.txt 2>&1` desde `frontend/`, con todos los tests en verde.
- [ ] 16.4 `docs/evidencias/mutaciones-C-27.py`: copiar la estructura de `mutaciones-C-26.py`. **Una mutación por cada test nuevo**, siempre sobre código de producción de `frontend/src`, corriendo Vitest solo para ese test. Comprobar que el texto original aparezca exactamente una vez, **normalizar CRLF**, **abortar si el mutante no cambia el archivo**, restaurar en un `finally` y comparar SHA-256 al final. **Detector de mutaciones inválidas**: el fallo tiene que venir de una afirmación del test, no de un `ReferenceError`/`TypeError` del mutante ni de una guarda de producción; una mutación inválida no cuenta como detectada. El resumen tiene que terminar en `mutaciones inválidas: 0` y la salida cruda va a `mutaciones-C-27.txt`. Ninguna mutación sobrevive (D17).
- [ ] 16.5 `docs/evidencias/trazabilidad-C-27.py`: cada escenario de `specs/frontend-agenda/spec.md` mapeado a un test, comprobado con `vitest list --json` (o el reporte JSON de Vitest); salida a `trazabilidad-C-27.txt` terminada en `N escenarios, 0 problemas` (D17).
- [ ] 16.6 `docs/evidencias/manual-C-27.py`: script que toma la contraseña de `SEED_USER_PASSWORD`, inicia sesión con `recepcion` y crea por la API de C-22, para el lunes futuro `2026-11-16`, Quiroga `10:00` `Control` en Sillón 1 con Ana Pérez, Sosa `09:00` `Control` en Sillón 2 con Bruno Acosta, cancela el de Sosa y vuelve a crear Sosa `09:00` para tener cancelado + activo, y crea un bloqueo de Quiroga `12:00–13:00` con motivo `Congreso`. Salida a `manual-C-27.txt` y respuestas reales a `http-C-27.txt`. Verificar columnas/orden, hora local, estados, carriles, horarios, bloqueo, filtros (incluida la asimetría del sillón), navegación, URL, domingo `2026-11-15` vacío, responsive 1024×768 y 768×1024, y el `401` **durante el uso** (token inválido en `sessionStorage` y “Actualizar”), que cierra el pendiente de C-26. Capturas de la autora: `C-27-agenda-dia.png`, `C-27-filtro-profesional.png`, `C-27-filtro-sillon.png`, `C-27-solapamiento-cancelado.png`, `C-27-vacio.png`, `C-27-sesion-vencida.png` y `C-27-tablet.png`. El `403` manual no es alcanzable porque los tres roles leen la agenda; se documenta la limitación (D18).
- [ ] 16.7 `docs/evidencias/verify-C-27.md` con referencias a cada `.txt`, la nota de C1 (zona horaria de la respuesta, respaldo en un solo archivo y prueba con `TZ=Asia/Tokyo`), el cierre del pendiente de `401` de C-26, las capturas, la limitación del `403` manual y la confirmación de que no se tocó `backend/`, `openspec/specs/`, `docs/evidencias/` preexistente, KB, `CHANGES.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.env` ni `docker-compose.yml`.
- [ ] 16.8 `openspec validate ui-agenda-diaria --strict` y `git diff --check`, redirigidos a `docs/evidencias/validate-C-27.txt`.

## Workflow follow-up

- Archivar C-27 con `/opsx:archive ui-agenda-diaria` solo cuando todas las tareas estén verdes y la autora lo pida.
- No commitear: el change queda en el árbol de trabajo hasta que la autora lo solicite.
