# Proposal

## Why

`openspec validate --all --strict` falla actualmente en 2 especificaciones principales (`appointment-lifecycle` y `appointment-scheduling`) porque 15 requisitos superan el límite estricto de 500 caracteres en su texto descriptivo (antes del primer escenario), producto de haber acumulado cláusulas, plantillas de mensajes y convenciones de escenarios a lo largo de los changes C-02 a C-12. Es necesario acortar o dividir esos textos de requisito sin alterar su semántica, sin renombrar requisitos ni escenarios existentes y sin tocar código productivo, para restablecer la validación estricta en verde de todo el repositorio.

## What Changes

- **Refinamiento sin cambio semántico en `appointment-lifecycle`**:
  - Se condensan a menos de 500 caracteres las descripciones de los 3 requisitos que exceden el límite (`Tabla única de transiciones ordinarias` [705], `Operaciones con resultado de agenda y copia` [523] y `Mensajes exactos y metadatos` [599]), conservando intactos sus títulos y todos sus escenarios originales.
- **Refinamiento y desglose sin cambio semántico en `appointment-scheduling`**:
  - Se condensan a menos de 500 caracteres las descripciones de los 12 requisitos que exceden el límite (`Alta de un turno válido` [1089], `Todas las violaciones, en orden estable` [1520], `Validez de la duración` [572], `Contenido de cada violación` [3213], `Turno dentro de un solo día local` [618], `Turno dentro del horario de atención` [2979], `Validez de un conjunto de tramos` [1757], `Turno fuera de los bloqueos del profesional` [563], `Mensaje de un turno bloqueado` [1107], `Turnos afectados por un bloqueo` [926], `Mensaje de un turno en el pasado` [934] y `Nombre del profesional y del sillón` [576]), manteniendo sus títulos y copiando textualmente todos sus escenarios existentes.
  - Para los 4 requisitos extensos que agrupaban múltiples comportamientos o plantillas (`Todas las violaciones, en orden estable`, `Contenido de cada violación`, `Turno dentro del horario de atención` y `Validez de un conjunto de tramos`), las partes desglosadas se incorporan bajo `## ADDED Requirements` en 6 requisitos complementarios de menos de 500 caracteres, cada uno con su escenario explícito.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `appointment-lifecycle`: Reducción a menos de 500 caracteres del texto descriptivo de 3 requisitos (`Tabla única de transiciones ordinarias`, `Operaciones con resultado de agenda y copia`, `Mensajes exactos y metadatos`) sin alterar su significado ni sus escenarios.
- `appointment-scheduling`: Reducción a menos de 500 caracteres del texto descriptivo de 12 requisitos existentes mediante `MODIFIED Requirements` (conservando títulos y escenarios textuales) y desglose de cláusulas en 6 `ADDED Requirements` (cada uno con menos de 500 caracteres y escenario propio) para preservar el 100 % de las reglas vigentes.

## Impact

- **Especificaciones afectadas**: `openspec/specs/appointment-lifecycle/spec.md` y `openspec/specs/appointment-scheduling/spec.md` (al aplicar/sincronizar los deltas).
- **Código y tests**: Ningún cambio en `backend/`, `frontend/`, migraciones ni tests; cambio exclusivo de mantenimiento de especificaciones OpenSpec.
- **Trazabilidad**: Se preservan todos los títulos de requisitos existentes y los nombres y contenidos de todos los escenarios existentes para no afectar scripts de trazabilidad (`docs/evidencias/trazabilidad-C-*.py`) ni referencias en tests.
