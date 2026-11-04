# Tasks

## 1. Datos ficticios y contratos de persistencia

- [x] 1.1 Ampliar `backend/app/demo_data.py` a tres profesionales, tres
  sillones, cinco prestaciones y cinco pacientes con ids fijos; verificar con
  los tests de C-09 que todos siguen siendo ficticios, válidos e inmutables.
- [x] 1.2 Crear el contrato tipado de repositorios y sus errores/resultados
  esperados sin exponer modelos ORM; verificar mediante type-check y una
  prueba que las interfaces usan tipos del dominio.

## 2. Modelos SQLAlchemy y migración

- [x] 2.1 Escribir primero tests de metadata para UUID nativo, largos de
  columnas, `active`, `license_number`, nombres normalizados, DNI único y
  constraints explícitos; verificar que fallen antes de implementar los
  modelos.
- [x] 2.2 Implementar `backend/app/db/models.py` sobre `Base`, registrar los
  cuatro modelos y satisfacer los tests de metadata; verificar también que el
  dominio no importe SQLAlchemy.
- [x] 2.3 Escribir el test de migración que exige la revisión
  `20261103_02_catalogos_y_pacientes`, sus cuatro tablas y su reversibilidad;
  verificar que falle contra la baseline.
- [x] 2.4 Crear la migración única encadenada a
  `20261103_01_baseline`, ejecutar `upgrade head` y `downgrade base`, y
  verificar que el ciclo termina nuevamente en `head` sin tablas residuales.
- [x] 2.5 Comparar la metadata declarativa con `MigrationContext` después de
  migrar; verificar que autogenerate no encuentre diferencias y que
  `alembic_version` no se trate como tabla de negocio.

## 3. Repositorios de catálogo

- [x] 3.1 Escribir tests de repositorio para alta, `get_by_id`, `list` e ida y
  vuelta de `Professional`, `Chair` y `Service`; verificar primero el RED
  sobre PostgreSQL de test.
- [x] 3.2 Implementar el mapeo SQLAlchemy-dominio y las altas de catálogo con
  consultas parametrizadas; verificar los tests de ida y vuelta sin devolver
  filas ORM.
- [x] 3.3 Escribir tests de validación previa, desactivación y reactivación
  idempotentes para los tres recursos; verificar que una alta rechazada no
  cree filas y que los cambios no alteren otros campos.
- [x] 3.4 Implementar las operaciones de activación usando `create_*`,
  `deactivate` y `reactivate` del dominio; verificar los escenarios de
  estados repetidos y referencias inactivas.
- [x] 3.5 Escribir tests de nombres duplicados exactos, con mayúsculas,
  espacios colapsables, tildes y registros inactivos; verificar el mensaje
  exacto de C-09 y que profesionales/pacientes puedan repetir nombre.
- [x] 3.6 Implementar `name_normalized`, su índice único y la traducción
  exclusiva de la violación esperada a `DUPLICATE_NAME`; verificar que otros
  errores de base se propaguen.

## 4. Repositorio de pacientes

- [x] 4.1 Escribir tests de alta, `get_by_id`, `list`, ida y vuelta de
  opcionales y rechazo de validaciones de C-09; verificar RED antes de la
  implementación.
- [x] 4.2 Implementar `patients.py` con DNI normalizado, `VARCHAR(8)`,
  índice único y mapeo tipado; verificar que teléfono y obra social conserven
  texto libre y que no aparezcan campos clínicos.
- [x] 4.3 Escribir tests de DNI duplicado y de violación concurrente traducida
  a `DUPLICATE_DNI`; verificar que una inserción inválida o duplicada no deje
  una fila parcial.
- [x] 4.4 Implementar la traducción específica del conflicto de DNI y el
  `CHECK` nombrado de 7/8 dígitos; verificar que errores no relacionados se
  propaguen sin catches amplios.

## 5. Seed idempotente

- [x] 5.1 Escribir tests que ejecuten el seed sobre una base migrada vacía y
  dos veces consecutivas; verificar cantidades, ids fijos, matrículas
  ficticias y ausencia de duplicados.
- [x] 5.2 Implementar `backend/app/db/seed.py` usando `demo_data.py`, el mapa
  privado de matrículas y los repositorios; verificar que inserte solo
  faltantes, no actualice ni borre y no corra al importar la aplicación.
- [x] 5.3 Documentar la ejecución manual `python -m app.db.seed` desde
  `backend/` y la exigencia de datos ficticios; verificar que el comando
  documentado sea reproducible con la base migrada.

## 6. Integración y verificación final

- [x] 6.1 Verificar que todas las pruebas de integración usan
  `<POSTGRES_DB>_test`, rollback por test y conexiones nuevas al comprobar
  cambios de esquema; ejecutar el ciclo de migración y confirmar que termina
  en `head`.
- [x] 6.2 Ejecutar desde la raíz `docker compose up -d`; verificar que
  PostgreSQL y Redis estén saludables antes de continuar.
- [x] 6.3 Desde `backend/`, ejecutar `alembic upgrade head`,
  `python -m app.db.seed` dos veces, `pytest` y `pytest -m integration`;
  conservar la salida completa y verificar todos los escenarios del delta.
- [x] 6.4 Ejecutar `alembic downgrade base` y `alembic upgrade head` desde
  `backend/`; verificar reversibilidad y revisión final
  `20261103_02_catalogos_y_pacientes`.
- [x] 6.5 Ejecutar `mypy --strict` desde `backend/` y verificar que modelos,
  repositorios, seed y tests mantengan tipado estricto sin `Any`.
- [x] 6.6 Ejecutar `openspec validate persistencia-catalogos-y-pacientes
  --strict` y `git diff --check`; conservar ambas salidas completas como
  evidencia del change.
