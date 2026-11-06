from pathlib import Path


def _compose_text() -> str:
    return (Path(__file__).parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )


def test_compose_defines_services_without_literal_secrets() -> None:
    content = _compose_text()

    assert "postgres:" in content
    assert "redis:" in content
    assert "backend:" in content
    assert "postgres:16" in content
    assert "redis:7" in content
    assert '"5432:5432"' in content
    assert '"6379:6379"' in content
    assert "turnos_pgdata:" in content
    assert "pg_isready" in content
    assert "redis-cli" in content
    assert "frontend:" not in content
    assert "turnos_local_dev" not in content


def test_compose_reads_postgres_values_from_environment() -> None:
    content = _compose_text()

    assert "POSTGRES_USER: ${POSTGRES_USER}" in content
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}" in content
    assert "POSTGRES_DB: ${POSTGRES_DB}" in content


def test_backend_database_url_uses_postgres_service() -> None:
    content = _compose_text()
    expected = "DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"
    assert expected in content


def test_backend_waits_for_healthy_postgres() -> None:
    content = _compose_text()
    backend_section = content[content.find("backend:") :]
    assert "postgres:\n        condition: service_healthy" in backend_section


def test_backend_waits_for_healthy_redis() -> None:
    content = _compose_text()
    backend_section = content[content.find("backend:") :]
    assert "redis:\n        condition: service_healthy" in backend_section


def test_backend_healthcheck_uses_api_health() -> None:
    content = _compose_text()
    assert "/api/health" in content


def _backend_dir() -> Path:
    return Path(__file__).parents[1]


def test_dockerfile_migrates_before_uvicorn() -> None:
    dockerfile = (_backend_dir() / "Dockerfile").read_text(encoding="utf-8")
    assert "alembic upgrade head" in dockerfile
    assert "uvicorn" in dockerfile
    alembic_pos = dockerfile.find("alembic upgrade head")
    uvicorn_pos = dockerfile.find("uvicorn")
    assert alembic_pos < uvicorn_pos


def test_dockerfile_runs_as_non_root() -> None:
    dockerfile = (_backend_dir() / "Dockerfile").read_text(encoding="utf-8")
    assert "USER appuser" in dockerfile
    assert "useradd" in dockerfile


def test_dockerignore_excludes_local_artifacts() -> None:
    dockerignore = (_backend_dir() / ".dockerignore").read_text(encoding="utf-8")
    assert ".venv" in dockerignore
    assert "tests" in dockerignore
    assert "__pycache__" in dockerignore
    assert ".mypy_cache" in dockerignore
    assert ".pytest_cache" in dockerignore


def test_readme_warns_about_reserved_password_characters() -> None:
    readme = (_backend_dir() / "README.md").read_text(encoding="utf-8")
    assert "POSTGRES_PASSWORD" in readme
    assert "caracteres reservados" in readme.lower()
    assert "docker compose up --build" in readme
