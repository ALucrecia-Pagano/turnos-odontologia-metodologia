# Explore C-15

El explore lo hizo Copilot y las decisiones D1 a D10 las cerró la autora el
2026-11-03. Este documento registra el alcance acordado para C-15; no
implementa código, tests, modelos, migraciones ni el seed.

## Inventario

- C-09 está archivado y dejó los tipos puros `Professional`, `Chair`,
  `Service` y `Patient`, junto con sus altas, activación, normalización de
  nombres y normalización/validación de DNI.
- `backend/app/domain` no importa SQLAlchemy ni conoce persistencia.
- `backend/app/demo_data.py` contiene datos ficticios reutilizables, pero
  actualmente solo un profesional, un sillón, una prestación y un paciente.
- C-14 está archivado y dejó `backend/app/db/base.py`, la sesión SQLAlchemy
  síncrona en UTC, Alembic y la revisión
  `20261103_01_baseline`.
- La fixture de integración crea/reutiliza `<POSTGRES_DB>_test`, ejecuta
  migraciones y revierte la transacción de cada test.
- Existe la spec vigente `catalog-and-patients` para el comportamiento puro
  del dominio y `database-infrastructure` para PostgreSQL, Alembic, metadata
  y aislamiento de integración.
- No existen modelos SQLAlchemy de negocio, repositorios, `seed.py`, una
  migración posterior a la baseline ni tests de integración de C-15.

## Decisiones

### D1 — Modelos y repositorios

Los modelos SQLAlchemy vivirán en `backend/app/db/models.py`, sobre `Base` de
`base.py`. Los repositorios vivirán en
`backend/app/repositories/catalog.py` y `patients.py`. Recibirán y devolverán
tipos del dominio, nunca filas SQLAlchemy, y usarán consultas con parámetros
ligados.

### D2 — Unicidad normalizada de nombres

`Chair` y `Service` conservarán `name` original y `name_normalized`, calculado
con la misma normalización de C-09. El índice único será sobre
`name_normalized`; profesionales y pacientes no tendrán unicidad por nombre.
Una violación de ese índice se traducirá a `Rejected` con `DUPLICATE_NAME` y el
mismo mensaje de C-09. Otros errores de base se propagarán.

### D3 — DNI

`Patient.dni` será `VARCHAR(8)`, almacenado solo con dígitos, con índice único
y un `CHECK` explícitamente nombrado que exija 7 u 8 dígitos. Un conflicto
concurrente de DNI se traducirá a `DUPLICATE_DNI` con el mensaje de C-09.

### D4 — Tipos y auditoría

Los ids serán UUID nativos. Los nombres y la obra social serán
`VARCHAR(255)`; el teléfono, `VARCHAR(50)`; `active` será `BOOLEAN NOT NULL
DEFAULT TRUE` solo en profesionales, sillones y prestaciones. No se
agregarán columnas de auditoría.

### D5 — Migración

Se creará una sola migración con las cuatro tablas, encadenada a
`20261103_01_baseline`, con nombre
`20261103_02_catalogos_y_pacientes`. Sus constraints usarán la
`naming_convention` vigente.

### D6 — Matrícula profesional

`license_number` existirá solo en la base como columna nullable de
`professional`, sin cambiar el dominio. El seed cargará matrículas ficticias
desde un mapa propio de persistencia. Si la API la necesita, se decidirá en
C-20.

### D7 — Datos y seed

`demo_data.py` se ampliará a tres profesionales, tres sillones, cinco
prestaciones y cinco pacientes, todos ficticios y con ids fijos.
`backend/app/db/seed.py` los insertará mediante repositorios, de forma
idempotente por id: solo inserta los faltantes, sin actualizar ni borrar.
Se ejecutará manualmente con `python -m app.db.seed` desde `backend/` y no al
iniciar la aplicación.

### D8 — Operaciones y validación

Profesionales, sillones y prestaciones tendrán `create`, `deactivate`,
`reactivate`, `get_by_id` y `list`. Pacientes tendrán `create`, `get_by_id` y
`list`. Las altas validarán primero con las funciones de C-09 y la lista de
existentes; solo un `Ok` se persistirá. No habrá edición y los pacientes no
se desactivarán.

### D9 — Integración

Los tests usarán `<POSTGRES_DB>_test` y una transacción revertida por test.
Cubrirán ida y vuelta a tipos del dominio, altas, lectura, listado,
activación, duplicados por nombre y DNI, traducción de violaciones de índice,
seed ejecutado dos veces sin duplicar filas y upgrade/downgrade de la nueva
migración.

### D10 — Gobernanza

No se agregará un punto de control en `tasks.md`.

## Riesgos y pendientes

- La base debe conservar exactamente la normalización del dominio; no se
  duplicará una regla distinta en SQL.
- Los conflictos de unicidad deben distinguirse de errores generales de
  PostgreSQL para no ocultar fallas.
- El ciclo de migración debe dejar la base de test en `head`.
- La columna `license_number` no debe filtrarse accidentalmente al dominio ni
  anticipar decisiones de la API.
