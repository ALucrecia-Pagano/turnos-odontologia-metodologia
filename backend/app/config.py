import os
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
JWT_SECRET_MIN_LENGTH = 32


class Settings(BaseSettings):
    app_env: str
    api_port: int
    postgres_user: str
    postgres_password: str = Field(repr=False)
    postgres_db: str
    database_url: str = Field(validation_alias="DATABASE_URL", repr=False)
    redis_url: str
    jwt_secret: SecretStr = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: Literal["HS256"]
    jwt_expires_min: int = Field(gt=0)
    seed_user_password: SecretStr | None = None
    app_timezone: str
    cors_origin: str
    vite_api_url: str

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
        hide_input_in_errors=True,
    )

    @field_validator("jwt_secret")
    @classmethod
    def _secret_has_minimum_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < JWT_SECRET_MIN_LENGTH:
            raise ValueError(
                f"JWT_SECRET debe tener al menos {JWT_SECRET_MIN_LENGTH} caracteres"
            )
        return value


def load_settings() -> Settings:
    values = {
        key.lower(): value
        for key, value in {
            **dotenv_values(ROOT_ENV_FILE),
            **os.environ,
        }.items()
        if value is not None
    }
    return Settings.model_validate(values)
