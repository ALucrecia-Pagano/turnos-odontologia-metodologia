from pathlib import Path


def _compose_text() -> str:
    return (Path(__file__).parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )


def test_compose_defines_only_postgres_and_redis_without_secrets() -> None:
    content = _compose_text()

    assert "postgres:" in content
    assert "redis:" in content
    assert "postgres:16" in content
    assert "redis:7" in content
    assert '"5432:5432"' in content
    assert '"6379:6379"' in content
    assert "turnos_pgdata:" in content
    assert "pg_isready" in content
    assert "redis-cli" in content
    assert "backend:" not in content
    assert "frontend:" not in content
    assert "turnos_local_dev" not in content
    assert "postgresql://" not in content
    assert "postgresql+psycopg://" not in content


def test_compose_reads_postgres_values_from_environment() -> None:
    content = _compose_text()

    assert "POSTGRES_USER: ${POSTGRES_USER}" in content
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}" in content
    assert "POSTGRES_DB: ${POSTGRES_DB}" in content
