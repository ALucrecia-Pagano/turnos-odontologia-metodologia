# Tasks

Gobernanza MEDIO; D1-D12 están cerradas por la autora y no hay checkpoint
intermedio. Este archivo planifica el apply: nada se ejecuta durante propose.
Aplicar Strict TDD: RED reproducible antes de cada GREEN, triangulación con al
menos dos casos por comportamiento y ejecución después de cada refactor.
No modificar el dominio ni su allowlist.

## 1. Safety Net

- [ ] 1.1 Revisar el estado de trabajo y ejecutar la suite existente y mypy
  desde `backend/` sin tocar los cambios ajenos de C-10; registrar resultados
  antes de agregar infraestructura.
- [ ] 1.2 Confirmar el contrato actual de `backend-toolchain`,
  `domain-dependency-guard`, `.gitignore` y `pyproject.toml`; detenerse ante
  fallos preexistentes.

## 2. Configuración y dependencias

- [ ] 2.1 RED: test de configuración que falla al faltar `DATABASE_URL` y
  nombra la variable; GREEN: agregar dependencias runtime y
  `backend/app/config.py` con `pydantic-settings`.
- [ ] 2.2 RED: test de configuración completa; GREEN: exponer valores tipados
  y variables obligatorias de KB 08 sin defaults de secretos.
- [ ] 2.3 TRIANGULAR configuración con valores ficticios, ausencia de otra
  variable obligatoria y zona horaria; ejecutar pytest y mypy.

## 3. Compose y entorno

- [ ] 3.1 RED: test estático de `.env.example`; GREEN: crear el archivo raíz
  con los catorce nombres exactos, sin valores; confirmar que `.env` sigue
  ignorado.
- [ ] 3.2 RED: test estático de servicios y secretos; GREEN: crear
  `docker-compose.yml` solo con `postgres:16`, `redis:7`, puertos,
  `turnos_pgdata` y healthchecks, sin secretos.
- [ ] 3.3 TRIANGULAR el parseo del Compose, la ausencia de backend/frontend y
  la interpolación de variables sin ejecutar Docker en los tests unitarios.

## 4. Sesión SQLAlchemy y UTC

- [ ] 4.1 RED: test de conexión y `SELECT 1`; GREEN: crear
  `backend/app/db/session.py` con engine y sesión síncrona psycopg 3.
- [ ] 4.2 RED: test de zona de sesión; GREEN: registrar el evento que ejecuta
  `SET TIME ZONE 'UTC'`.
- [ ] 4.3 RED: test de ida y vuelta `timestamptz` con instante `-03:00`; GREEN:
  configurar la columna temporal y verificar el mismo instante UTC.
- [ ] 4.4 TRIANGULAR conexión repetida, consulta de zona y microsegundos sin
  introducir lecturas de reloj global.

## 5. Fixture y marca de integración

- [ ] 5.1 RED: test de selección de pytest; GREEN: registrar `integration` y
  `addopts = "-m \"not integration\""`.
- [ ] 5.2 RED: test de derivación de base; GREEN: crear fixture de sesión que
  derive `<POSTGRES_DB>_test`, la cree si no existe y nunca use la base real.
- [ ] 5.3 RED: test de rollback por caso; GREEN: envolver cada test en una
  transacción revertida.
- [ ] 5.4 TRIANGULAR base real distinta, reutilización de la base de test y
  dos tests consecutivos sin datos persistentes entre ellos.

## 6. Guardia y regresión

- [ ] 6.1 RED: test que inspecciona imports del dominio; GREEN: mantener
  configuración y `db/` fuera de `backend/app/domain` sin cambiar la
  allowlist.
- [ ] 6.2 Ejecutar pytest por defecto, pytest de integración y mypy estricto;
  registrar que los tests de dominio continúan pasando sin Docker.

## 7. Verificación final y evidencias

- [ ] 7.1 Ejecutar los comandos manuales documentados en `design.md` con
  Docker Desktop, registrar salud de PostgreSQL y Redis y ejecutar ambos
  modos de pytest.
- [ ] 7.2 Buscar en todo lo versionado contraseñas, tokens y URLs con
  credenciales; la tarea MUST fallar si encuentra un secreto. Revisar además
  que `.env` no esté versionado.
- [ ] 7.3 Guardar evidencia del ciclo RED/GREEN/TRIANGULATE/REFACTOR, comandos,
  resultados y `git diff --check`; no marcar tareas sin evidencia real.
