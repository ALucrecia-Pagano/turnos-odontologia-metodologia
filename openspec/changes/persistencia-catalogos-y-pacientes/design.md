# Design

## Context

C-09 provee entidades inmutables y validaciones puras para catálogo y
pacientes. C-14 provee `Base`, la convención de nombres, sesión SQLAlchemy en
UTC, Alembic y la base de integración separada. La motivación y el alcance se
describen en `proposal.md`; los contratos verificables están en el delta de
`database-infrastructure`.

## Goals / Non-Goals

**Goals:**

- Mantener aislados el dominio, los modelos SQLAlchemy y los repositorios.
- Persistir las cuatro entidades con restricciones coherentes con C-09.
- Hacer explícita la traducción de filas a tipos del dominio.
- Soportar altas validadas, activación idempotente y lecturas tipadas.
- Proveer una migración reversible y un seed ficticio, determinista e
  idempotente.
- Cubrir los escenarios con integración real sobre PostgreSQL de test.

**Non-Goals:**

- Cambiar `backend/app/domain` o sus reglas.
- Agregar API, casos de uso HTTP o edición de entidades.
- Persistir turnos, horarios, bloqueos, usuarios o auditoría.
- Desactivar pacientes.
- Ejecutar el seed automáticamente al iniciar la aplicación.

## Decisions

### D1 — Separación de capas

Los modelos declarativos se ubicarán en `backend/app/db/models.py` y los
repositorios en `backend/app/repositories/catalog.py` y `patients.py`.
Cada repositorio mapeará explícitamente entre una fila SQLAlchemy y el tipo
del dominio. Se descarta mapear dataclasses directamente con SQLAlchemy porque
rompería la guardia de pureza del dominio y expondría filas ORM a consumidores.

### D2 — Columnas y constraints

Las tablas usarán UUID nativo, `VARCHAR(255)` para nombres y obra social,
`VARCHAR(50)` para teléfono y booleanos no nulos con default `TRUE` en los
tres recursos activables. `professional.license_number` será nullable y
exclusivo de persistencia. No habrá timestamps de auditoría.

`chair.name_normalized` y `service.name_normalized` se calcularán llamando a
la normalización ya definida por C-09 y tendrán índices únicos. El nombre
original permanecerá intacto. `patient.dni` se guardará normalizado en
`VARCHAR(8)`, con índice único y un `CHECK` nombrado para 7 u 8 dígitos.
Profesionales y pacientes no tendrán unicidad por nombre.

Se descarta un índice únicamente sobre el nombre original porque no representa
la igualdad de C-09. Se descarta una expresión SQL como fuente de verdad
porque no garantiza equivalencia exacta con `casefold()` y el colapso de
espacios del dominio.

### D3 — Alta y errores de unicidad

Cada alta cargará los existentes, ejecutará primero `create_*` del dominio y
persistirá solo un resultado `Ok`. El repositorio traducirá únicamente la
violación esperada del índice de nombre a `Rejected(DUPLICATE_NAME)` y la del
índice de DNI a `Rejected(DUPLICATE_DNI)`, conservando exactamente los mensajes
de C-09. Una excepción no identificada se propagará sin captura amplia ni
fallback silencioso.

### D4 — Operaciones

Los repositorios de profesionales, sillones y prestaciones expondrán
`create`, `deactivate`, `reactivate`, `get_by_id` y `list`. El de pacientes
expondrá `create`, `get_by_id` y `list`. Desactivar/reactivar usará el dominio
para construir la copia y luego persistirá el nuevo valor de `active`.
Edición y pacientes desactivables quedan fuera.

### D5 — Migración

Una única revisión `20261103_02_catalogos_y_pacientes` dependerá de
`20261103_01_baseline` y creará las tablas en orden independiente, sin
relaciones entre ellas en C-15. Todos los nombres derivados de la metadata
respetarán la convención existente; el `CHECK` de DNI tendrá nombre explícito.
El downgrade eliminará las cuatro tablas y el upgrade siguiente debe volver a
dejar la base en `head`.

### D6 — Seed

`demo_data.py` será la fuente de las entidades ficticias. `seed.py` mantendrá
un mapa privado de matrículas ficticias para profesionales, abrirá una sesión
y usará los repositorios. Para cada id fijo, consultará primero y solo
insertará si falta; no actualizará ni borrará filas. La entrada será
`python -m app.db.seed` desde `backend/`, nunca una acción de startup.

### D7 — Aislamiento de integración

Los tests se ejecutarán con la fixture existente sobre `<POSTGRES_DB>_test`.
Cada test usará una transacción que se revierte, mientras los escenarios de
migración abrirán conexiones nuevas cuando deban observar cambios de esquema.
El seed se invocará dos veces dentro de una preparación controlada y se
compararán conteos por entidad.

## Risks / Trade-offs

- **[Riesgo]** La normalización de SQL y la del dominio podrían divergir.
  **Mitigación:** calcular `name_normalized` únicamente con la función de
  normalización de C-09 y probar casos de mayúsculas, espacios y tildes.
- **[Riesgo]** Una excepción de integridad puede ocultar un error distinto de
  una duplicación. **Mitigación:** identificar solo las restricciones
  esperadas; propagar cualquier otro error.
- **[Riesgo]** El seed puede dejar datos parciales si falla a mitad de camino.
  **Mitigación:** ejecutarlo en una transacción única y hacer rollback ante
  error.
- **[Riesgo]** La metadata puede no registrar todos los modelos y Alembic
  puede divergir. **Mitigación:** importar los modelos antes de comparar
  metadata y exigir autogenerate vacío en la verificación.
- **[Riesgo]** El DNI almacenado puede aceptar longitud o caracteres inválidos
  por un camino que no pase por el dominio. **Mitigación:** validación previa
  de C-09 más `CHECK` explícito e índice único en PostgreSQL.

## Migration Plan

1. Ampliar datos ficticios y crear modelos, repositorios y tests en ciclo
   RED-GREEN-REFACTOR.
2. Crear la migración `20261103_02_catalogos_y_pacientes`.
3. Ejecutar `upgrade head`, tests de integración y el seed dos veces sobre el
   entorno configurado.
4. Verificar `downgrade base` y `upgrade head`, dejando la base de test en
   `head`.
5. Si se revierte el change, retirar la revisión y los artefactos de
   persistencia junto con sus tests; no modificar la baseline de C-14.

## Verificación manual

Desde la raíz:

```powershell
docker compose up -d
```

Desde `backend/`:

```powershell
alembic upgrade head
python -m app.db.seed
python -m app.db.seed
pytest
pytest -m integration
```

La verificación de reversibilidad se ejecutará además con:

```powershell
alembic downgrade base
alembic upgrade head
```

No se ejecutará `docker compose down -v`.

## Desvíos del apply

- La primera ejecución RED de metadata/contratos falló con `ImportError` de
  `app.db.models` y `ModuleNotFoundError` de `app.repositories`, como se
  esperaba antes de crear esas capas.
- La primera migración GREEN encontró que el identificador de C-15 supera el
  `VARCHAR(32)` heredado de `alembic_version`. La migración amplía esa columna
  a `VARCHAR(64)` antes de escribir la revisión; el downgrade conserva el
  ancho ampliado para poder actualizar la versión a la baseline sin truncar.
- La primera corrida de integración expuso que el downgrade intentaba reducir
  `alembic_version` antes de que Alembic escribiera la revisión anterior. Se
  eliminó ese paso del downgrade y se verificó nuevamente el ciclo completo.
- La evidencia se regeneró con el lanzador `cmd` porque la redirección nativa
  de PowerShell producía archivos UTF-16 con caracteres nulos. No se cambió la
  política de ejecución del sistema.
