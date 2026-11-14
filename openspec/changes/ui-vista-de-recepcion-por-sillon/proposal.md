# Proposal

## Why

La recepción del consultorio trabaja mirando sillones, no profesionales: necesita ver qué sillón está libre, cuál está ocupado y por quién, para dar turno en el mostrador. Hoy `/agenda` solo ofrece columnas por profesional (día y semana), así que responder "¿qué sillón puedo usar ahora?" exige cruzar mentalmente turnos, horarios y bloqueos. C-31 agrega esa lectura sin tocar el backend.

## What Changes

- Nuevo modo de vista `view=chair` dentro de `/agenda` (etiqueta visible "Sillones"), junto a Día y Semana; conserva `date`, `professionalId` y `chairId` al alternar.
- Columnas por sillón: una por cada sillón del catálogo `GET /api/chairs`, más los sillones que aparezcan en turnos (unión defensiva), ordenadas por nombre; los inactivos se marcan `(inactivo)`.
- Disponibilidad derivada en el frontend: bloques con texto "Libre HH:MM–HH:MM" y "Fuera de horario HH:MM–HH:MM" dentro de la unión de horarios de atención del día; los bloqueos profesionales no se pintan como indisponibilidad del sillón.
- La tarjeta del turno muestra el profesional en texto (en modo sillón) y sigue abriendo `AppointmentDetailDialog` (C-30) al hacer clic.
- Acceso restringido a `recepcion` y `administrador`; el `odontologo` no ve el botón y, si entra por URL con `view=chair`, cae a Día con la URL normalizada.
- "Ver como lista" sigue disponible y el vacío "No hay turnos" se adapta para no borrar la grilla con los huecos libres.
- Reutiliza el mismo contenedor de grilla de día/semana definido por C-36 (scroll-snap y columna completa en celular). C-31 solo le pasa las columnas por sillón.
- Cero cambios de backend, de modelo, de API o de migraciones.

## Capabilities

### New Capabilities

Ninguna. La vista extiende una capability existente.

### Modified Capabilities

- `frontend-agenda`: se agregan requisitos de una vista de recepción por sillón (columnas por sillón, disponibilidad "Libre"/"Fuera de horario", acceso por rol, tarjeta con profesional y detalle, filtros, lista y estado vacío, adaptabilidad heredada de C-36).

## Impact

- Frontend únicamente: `frontend/src/features/agenda/` (nuevo módulo puro `agendaChairLayout.ts`, `AgendaView`, `AgendaGrid`, `AgendaGrid.module.css`, `AgendaPage`, `AgendaToolbar`, `tokens.css`) y tests nuevos en archivos nuevos.
- Sin cambios en `backend/`, `openspec/specs/` (la spec se sincroniza al archivar), `CHANGES.md`, `README.md`, `AGENTS.md` ni `CLAUDE.md`.
- Dependencia explícita: C-36 (`ui-tema-oscuro-y-movil`) archivado antes de aplicar C-31, porque C-31 hereda su contenedor de grilla y su toolbar compacta.
- Datos de prueba: se respeta el seed literal (`backend/app/demo_data.py:61-70`); Quiroga y Benítez atienden lunes a viernes 09:00–13:00 y 15:00–19:00, Sosa solo 09:00–13:00, y el seed no crea turnos ni bloqueos.
- Governance: **BAJO** (solo presentación y cálculo puro de UI, sin datos sensibles ni backend).
