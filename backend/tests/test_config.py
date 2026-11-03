from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def _complete_settings() -> dict[str, str]:
    return {
        "app_env": "development",
        "api_port": "8000",
        "postgres_user": "turnos",
        "postgres_password": "turnos_local_dev",
        "postgres_db": "turnos",
        "database_url": "postgresql+psycopg://turnos:turnos_local_dev@localhost:5432/turnos",
        "redis_url": "redis://localhost:6379/0",
        "jwt_secret": "jwt_local_dev_secret",
        "jwt_algorithm": "HS256",
        "jwt_expires_min": "60",
        "seed_user_password": "seed_local_dev",
        "app_timezone": "America/Argentina/Buenos_Aires",
        "cors_origin": "http://localhost:5173",
        "vite_api_url": "http://localhost:8000/api",
    }


def test_missing_database_url_names_variable() -> None:
    values = _complete_settings()
    values.pop("database_url")

    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings.model_validate(values)


def test_complete_configuration_exposes_typed_values() -> None:
    settings = Settings.model_validate(_complete_settings())

    assert settings.app_env == "development"
    assert settings.api_port == 8000
    assert settings.postgres_db == "turnos"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.jwt_expires_min == 60
    assert settings.app_timezone == "America/Argentina/Buenos_Aires"


def test_missing_secret_has_no_default() -> None:
    values = _complete_settings()
    values.pop("jwt_secret")

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings.model_validate(values)


def test_env_example_has_all_documented_names_without_assignments() -> None:
    path = Path(__file__).parents[2] / ".env.example"
    content = path.read_text(encoding="utf-8")
    names = (
        "APP_ENV",
        "API_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET",
        "JWT_ALGORITHM",
        "JWT_EXPIRES_MIN",
        "SEED_USER_PASSWORD",
        "APP_TIMEZONE",
        "CORS_ORIGIN",
        "VITE_API_URL",
    )

    assert all(f"{name}=" in content for name in names)
    assert all(f"{name}=\n" in content for name in names)
