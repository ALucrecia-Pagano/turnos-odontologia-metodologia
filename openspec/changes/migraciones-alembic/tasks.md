# Tasks

## 1. Dependencia y estructura

- [ ] 1.1 Agregar `alembic>=1.13,<2` como dependencia de runtime en
  `backend/pyproject.toml` y verificar que el proyecto resuelve la
  dependencia sin cambiar las exclusiones existentes de pytest.
- [ ] 1.2 Crear `backend/alembic.ini`, `backend/alembic/`,
  `backend/alembic/script.py.mako` y `backend/alembic/versions/`, con
  `file_template` para `YYYYMMDD_NN_slug`, y verificar que no haya una URL de
  conexión en el INI.
- [ ] 1.3 Crear `backend/app/db/base.py` con `DeclarativeBase` y la
  `naming_convention` exacta de D3; verificarla con un test de constraint de
  ejemplo sin agregar una tabla de negocio versionada.

## 2. Contexto de Alembic y línea de base

- [ ] 2.1 Implementar `env.py` para cargar `Settings` mediante
  `load_settings()`, apuntar al `Base.metadata` y soportar modo offline/online;
  verificar que la URL efectiva proviene de la configuración y no del INI.
- [ ] 2.2 Crear la migración `20261103_01_baseline` con `upgrade` y
  `downgrade` vacíos; verificar que no crea ni elimina tablas de negocio.
- [ ] 2.3 Verificar con una prueba de integración que `upgrade head` termina
  sin errores y que la revisión registrada es `head` en `<POSTGRES_DB>_test`.

## 3. Tests de ciclo de migración

- [ ] 3.1 Extender las fixtures de integración con una fixture de alcance de
  sesión que ejecute `upgrade head` sobre `<POSTGRES_DB>_test` antes de la
  suite; verificar que la base de desarrollo nunca es seleccionada.
- [ ] 3.2 Implementar el escenario `upgrade head` → comprobación de revisión →
  `downgrade base` → comprobación de ausencia de tablas de negocio →
  `upgrade head`; verificar que la base de test queda en `head` al finalizar.
- [ ] 3.3 Verificar que la fixture existente de C-13 mantiene la transacción
  reversible por test y que los tests de integración siguen marcados.

## 4. Autogenerate y guardias

- [ ] 4.1 Implementar el test con `MigrationContext` y `compare_metadata`
  contra la base de test migrada; verificar que las diferencias son vacías y
  que `alembic_version` no se trata como tabla de negocio.
- [ ] 4.2 Verificar la convención de nombres con constraints de ejemplo
  (`ix`, `uq`, `ck`, `fk` y `pk`) y exigir nombre explícito en el check;
  comprobar los nombres esperados sin generar tablas de negocio.
- [ ] 4.3 Extender o conservar la guardia del dominio para verificar que
  `backend/app/domain` no importa Alembic ni la infraestructura de
  migraciones; ejecutar la guardia sin Docker.

## 5. Documentación y verificación final

- [ ] 5.1 Documentar en el README o evidencia operativa el flujo manual
  acordado desde Git Bash, incluyendo `docker compose up -d`, los comandos
  Alembic desde `backend/`, `pytest`, `pytest -m integration` y
  `docker compose down` sin `-v`; verificar que no se documente el borrado
  del volumen como flujo normal.
- [ ] 5.2 Ejecutar `pytest` sin selector y verificar que no necesita Docker ni
  ejecuta tests de integración.
- [ ] 5.3 Ejecutar `pytest -m integration` con PostgreSQL disponible y
  verificar todos los escenarios de migración, aislamiento, autogenerate,
  naming convention y guardia del dominio.
- [ ] 5.4 Ejecutar `mypy --strict` sobre el backend y verificar que la nueva
  infraestructura conserva el tipado estricto.

## 6. Verificación del change y evidencias

- [ ] 6.1 Revisar que todos los archivos de C-14 estén versionables, que no
  haya URLs con credenciales ni secretos y que C-15 pueda encontrar la base
  en `head`; verificar el resultado con una inspección de archivos.
- [ ] 6.2 Ejecutar `openspec validate migraciones-alembic --strict` y
  `git diff --check`; conservar la salida completa como evidencia del change.
