import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_env: str
    api_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: str = Field(validation_alias="DATABASE_URL")
    redis_url: str
    jwt_secret: str = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: str
    jwt_expires_min: int
    seed_user_password: str
    app_timezone: str
    cors_origin: str
    vite_api_url: str

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


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
