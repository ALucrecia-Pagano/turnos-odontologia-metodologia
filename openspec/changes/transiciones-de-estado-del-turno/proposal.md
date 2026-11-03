# Proposal

## Why

El dominio ya crea turnos válidos y distingue qué estados ocupan agenda, pero todavía permite construir estados sin una operación que controle las transiciones, el actor y el momento. C-10 incorpora cancelar y cambiar estado con rechazos explicativos y copias inmutables, preparando reprogramación (C-11) e historial (C-12).

## What Changes

- Política única de RN-TU-02 en `appointment/transitions.py`: siete aristas permitidas; atendido, ausente y cancelado terminales; repetir cualquiera de los cinco estados es inválido.
- Operaciones puras `cancel_appointment` y `change_status`, con actor y reloj inyectados; éxito mediante el `Ok.appointment` vigente y rechazo mediante `Rejected`/`Violation`.
- Actor tipado e inmutable con identidad de usuario, rol y vínculo opcional al profesional. El odontólogo cambia estados de turnos propios, pero nunca cancela; recepción y administración operan sobre todos.
- `INVALID_TRANSITION`, `STATUS_CHANGE_TOO_EARLY` y `FORBIDDEN_OPERATION`, con mensajes exactos que identifican profesional, fecha e intervalo local.
- Atendido/ausente requieren `now >= inicio`; cancelación sin anticipación mínima. Permiso corta; después se acumulan transición y tiempo en ese orden.
- Cancelar devuelve una copia cancelada que deja de ocupar ambos recursos mediante el conjunto existente, sin modificar `OCCUPYING_STATUSES`.

## Capabilities

### New Capabilities

- `appointment-lifecycle`: transiciones y cancelación puras con permisos, tiempo, mensajes y resultados inmutables.

### Modified Capabilities

Ninguna. `domain-dependency-guard` conserva su guardia y allowlist sin cambios; `appointment-scheduling` conserva alta, ocupación y sus contratos.

## Impact

- Apply futuro: `backend/app/domain/model.py` (Actor/Role), `violations.py` (tres códigos y documentación de Ok), nuevo `appointment/transitions.py`, exportaciones de `appointment/__init__.py` y nuevos tests de ciclo de vida/integración. La tabla usa un dict privado declarado como Mapping[AppointmentStatus, frozenset[AppointmentStatus]], con garantía de inmutabilidad por tipo para mypy y sin cambios en la guardia de dependencias. Sin dependencias nuevas ni cambios en catálogo, reglas de alta o conjunto de ocupación.
- Dependencia C-02 cumplida; C-08 y C-09 archivados. Gobernanza MEDIO, D1–D10 cerradas por la autora, sin punto de control.
- Fuera de alcance: reprogramación, historial, JWT/autenticación, API, UI, persistencia y migraciones. La corrección documental registra SU-03/SU-08 en la KB y el explore en docs/evidencias; no modificar CHANGES, AGENTS, CLAUDE ni estado del orquestador.
- Este propose solo crea artefactos en este change. Por instrucción expresa de la autora se omite el CLI y se usa el esquema local `spec-driven` y los precedentes; no se afirma validación ni estado obtenido mediante OpenSpec.
