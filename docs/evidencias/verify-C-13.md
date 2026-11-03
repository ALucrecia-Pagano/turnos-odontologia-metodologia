# Verify de C-13 docker-compose-y-postgres

## Resultado

- Fecha: 2026-11-02.
- Aplicación sobre propose aprobado y commiteado por la autora; gobernanza
  MEDIO sin checkpoint.
- Tareas completadas: 21/21.
- Suite por defecto: **609 passed, 5 deselected**.
- Integración: **5 passed, 609 deselected**.
- Mypy estricto: **Success: no issues found in 58 source files**.
- OpenSpec estricto: **Change 'docker-compose-y-postgres' is valid**.
- `git diff --check`: sin errores.
- Docker Compose: PostgreSQL y Redis `healthy`; `pg_isready` aceptó
  conexiones y Redis devolvió `PONG`.
- Búsqueda de secretos: sin contraseñas, tokens ni URLs con credenciales en
  archivos versionados; `.env` permanece ignorado.

Los artefactos archivados son [design.md](../../openspec/changes/archive/2026-11-02-docker-compose-y-postgres/design.md)
y [tasks.md](../../openspec/changes/archive/2026-11-02-docker-compose-y-postgres/tasks.md).

Las salidas completas de pytest están en
[pytest-C-13.txt](pytest-C-13.txt), la salida de mypy en
[mypy-C-13.txt](mypy-C-13.txt) y la salida de integración aislada también se
conserva en [pytest-integration-C-13.txt](pytest-integration-C-13.txt).

## Trazabilidad: 10/10 escenarios

| Nº | Escenario de la spec | Test o evidencia |
|---|---|---|
| 1 | Falta `DATABASE_URL` y el error nombra la variable | `tests/test_config.py::test_missing_database_url_names_variable` |
| 2 | Configuración completa con valores tipados | `tests/test_config.py::test_complete_configuration_exposes_typed_values` |
| 3 | Conexión y `SELECT 1` | `tests/integration/test_database_infrastructure.py::test_database_connection_and_select_one` |
| 4 | Ida y vuelta de `timestamptz` conserva el instante `-03:00` | `tests/integration/test_database_infrastructure.py::test_timestamptz_round_trip_preserves_instant` |
| 5 | La sesión trabaja en UTC | `tests/integration/test_database_infrastructure.py::test_connection_timezone_is_utc` |
| 6 | La base de test es distinta de la real | `tests/integration/test_database_infrastructure.py::test_test_database_is_distinct_from_real_database` |
| 7 | La fixture revierte la transacción de cada caso | `tests/integration/test_database_infrastructure.py::test_transaction_fixture_rolls_back_rows` |
| 8 | pytest por defecto excluye integración | Salida de `pytest`: 609 ejecutados y 5 deseleccionados; configuración `addopts = "-m \"not integration\""` en `backend/pyproject.toml` |
| 9 | `.env.example` contiene los nombres documentados sin valores | `tests/test_config.py::test_env_example_has_all_documented_names_without_assignments` |
| 10 | Compose no contiene secretos y el dominio no importa infraestructura | `tests/test_compose.py::test_compose_defines_only_postgres_and_redis_without_secrets`; `tests/domain/test_import_guard.py` |

## Ciclo TDD y desvíos

Se conservaron los ciclos RED/GREEN/TRIANGULATE/REFACTOR del apply. Los
tests unitarios de configuración y Compose pasaron después de su
implementación; los tests de integración pasaron con Docker healthy. La
configuración fue ajustada tras detectar que el `.env` local hacía que
`Settings.model_validate` completara variables faltantes; `load_settings`
mantiene la única lectura explícita del archivo y los tests vuelven a
verificar errores por variables ausentes.

### Incidente de autenticación

- **Síntoma:** autenticación fallida para el usuario `turnos`.
- **Causa real:** un PostgreSQL instalado en Windows también escuchaba en el
  puerto 5432.
- **Detección:** el mensaje apareció en castellano con codificación de
  Windows, mientras que el PostgreSQL de Docker responde en inglés.
- **Diagnóstico equivocado previo:** se atribuyó el error a un volumen
  inicializado con otra contraseña y se recreó el volumen, sin efecto.
- **Solución:** detener el servicio PostgreSQL local de Windows y dejar el
  puerto 5432 exclusivamente para el contenedor.

Otros desvíos corregidos durante el apply fueron la resolución inicial del
`.env` dentro de `backend/` y la conversión de la URL `postgresql+psycopg`
para la conexión administrativa directa con psycopg. Están detallados en [design.md](../../openspec/changes/archive/2026-11-02-docker-compose-y-postgres/design.md).

## Verificación manual ejecutada

Desde la raíz:

```bash
cp .env.example .env
docker compose up -d
docker compose ps
docker compose exec postgres pg_isready
docker compose exec redis redis-cli ping
```

Desde `backend/`:

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m pytest -m integration
```

Finalmente:

```bash
docker compose down
```

No se ejecutó `docker compose down -v` durante este apply.
