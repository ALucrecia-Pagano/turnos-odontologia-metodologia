import re
from pathlib import Path

import pytest
import yaml

SECRET_VARIABLES = ("POSTGRES_PASSWORD", "JWT_SECRET", "SEED_USER_PASSWORD")
ENV_REFERENCE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")
URL_CREDENTIALS = re.compile(r"://(.*)@")


def _compose_text() -> str:
    return (Path(__file__).parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )


def _as_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return {str(key): item for key, item in value.items()}


def _services(compose_text: str) -> dict[str, object]:
    return _as_mapping(_as_mapping(yaml.safe_load(compose_text))["services"])


def _environment(service: dict[str, object]) -> dict[str, str]:
    environment = service.get("environment", {})
    if isinstance(environment, list):
        entries = [str(entry).partition("=") for entry in environment]
        return {name: value for name, separator, value in entries if separator}
    return {
        name: str(value)
        for name, value in _as_mapping(environment).items()
        if value is not None
    }


def _has_literal_credentials(url: str) -> bool:
    credentials = URL_CREDENTIALS.search(url)
    if credentials is None:
        return False
    return not all(
        ENV_REFERENCE.fullmatch(part) for part in credentials.group(1).split(":")
    )


def _literal_secrets(compose_text: str) -> list[str]:
    found: list[str] = []
    for service_name, service in _services(compose_text).items():
        for name, value in _environment(_as_mapping(service)).items():
            literal_secret = name in SECRET_VARIABLES and not ENV_REFERENCE.fullmatch(
                value
            )
            literal_url = name == "DATABASE_URL" and _has_literal_credentials(value)
            if literal_secret or literal_url:
                found.append(f"{service_name}.{name}")
    return found


def _compose_with_environment(environment: str) -> str:
    return f"services:\n  app:\n    environment:\n{environment}\n"


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
    assert _literal_secrets(content) == []


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ("      POSTGRES_PASSWORD: valor-ficticio", "app.POSTGRES_PASSWORD"),
        ("      JWT_SECRET: valor-ficticio", "app.JWT_SECRET"),
        ("      SEED_USER_PASSWORD: valor-ficticio", "app.SEED_USER_PASSWORD"),
        ('      POSTGRES_PASSWORD: ""', "app.POSTGRES_PASSWORD"),
        ("      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ficticio}", "app.POSTGRES_PASSWORD"),
        ("      - JWT_SECRET=valor-ficticio", "app.JWT_SECRET"),
        (
            "      DATABASE_URL: postgresql://${POSTGRES_USER}:ficticio@postgres:5432/db",
            "app.DATABASE_URL",
        ),
        (
            "      DATABASE_URL: postgresql://ficticio:${POSTGRES_PASSWORD}@postgres:5432/db",
            "app.DATABASE_URL",
        ),
        ("      DATABASE_URL: postgresql://ficticio@postgres:5432/db", "app.DATABASE_URL"),
    ],
)
def test_literal_secret_is_detected(environment: str, expected: str) -> None:
    assert _literal_secrets(_compose_with_environment(environment)) == [expected]


@pytest.mark.parametrize(
    "environment",
    [
        "      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}",
        "      - JWT_SECRET=${JWT_SECRET}",
        "      SEED_USER_PASSWORD:",
        "      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/db",
        "      REDIS_URL: redis://redis:6379/0",
    ],
)
def test_env_reference_is_accepted(environment: str) -> None:
    assert _literal_secrets(_compose_with_environment(environment)) == []


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
    backend = _as_mapping(_services(_compose_text())["backend"])
    healthcheck = _as_mapping(backend["healthcheck"])
    command = healthcheck["test"]
    assert isinstance(command, list)
    assert re.search(r"/api/health\b", " ".join(str(part) for part in command))


def _backend_dir() -> Path:
    return Path(__file__).parents[1]


def test_dockerfile_migrates_before_uvicorn() -> None:
    dockerfile = (_backend_dir() / "Dockerfile").read_text(encoding="utf-8")
    commands = [line for line in dockerfile.splitlines() if line.startswith("CMD")]
    assert len(commands) == 1
    assert re.search(r"alembic upgrade head && (exec )?uvicorn", commands[0])


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
