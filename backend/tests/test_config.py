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
        "jwt_secret": "secreto-ficticio-de-32-caractere",
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


SECRET_MARK = "MARCA-RECONOCIBLE"


def test_short_secret_error_hides_value() -> None:
    values = _complete_settings()
    values["jwt_secret"] = SECRET_MARK.ljust(31, "x")

    with pytest.raises(ValidationError, match="JWT_SECRET") as error:
        Settings.model_validate(values)

    assert SECRET_MARK not in str(error.value)


def test_secret_of_32_characters_loads() -> None:
    values = _complete_settings()
    values["jwt_secret"] = "x" * 32

    settings = Settings.model_validate(values)

    assert settings.jwt_secret.get_secret_value() == "x" * 32


def test_empty_secret_names_variable() -> None:
    values = _complete_settings()
    values["jwt_secret"] = ""

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings.model_validate(values)


def test_algorithm_none_is_rejected() -> None:
    values = _complete_settings()
    values["jwt_algorithm"] = "none"

    with pytest.raises(ValidationError, match="jwt_algorithm"):
        Settings.model_validate(values)


def test_asymmetric_algorithm_is_rejected() -> None:
    values = _complete_settings()
    values["jwt_algorithm"] = "RS256"

    with pytest.raises(ValidationError, match="jwt_algorithm"):
        Settings.model_validate(values)


def test_zero_expiration_is_rejected() -> None:
    values = _complete_settings()
    values["jwt_expires_min"] = "0"

    with pytest.raises(ValidationError, match="jwt_expires_min"):
        Settings.model_validate(values)


def test_settings_repr_hides_secrets() -> None:
    values = _complete_settings()
    values["jwt_secret"] = SECRET_MARK.ljust(32, "x")
    values["seed_user_password"] = "MARCA-DE-SEMILLA"

    settings = Settings.model_validate(values)

    assert SECRET_MARK not in repr(settings)
    assert "MARCA-DE-SEMILLA" not in repr(settings)
    assert SECRET_MARK not in str(settings)


def test_settings_repr_hides_database_password() -> None:
    values = _complete_settings()
    values["postgres_password"] = "MARCA-DE-POSTGRES"
    values["database_url"] = "postgresql+psycopg://turnos:MARCA-DE-POSTGRES@localhost:5432/turnos"

    settings = Settings.model_validate(values)

    assert "MARCA-DE-POSTGRES" not in repr(settings)
    assert "MARCA-DE-POSTGRES" not in str(settings)
    assert settings.postgres_password == "MARCA-DE-POSTGRES"


def test_missing_seed_password_loads_as_none() -> None:
    values = _complete_settings()
    values.pop("seed_user_password")

    settings = Settings.model_validate(values)

    assert settings.seed_user_password is None
