import pytest
from pydantic import SecretStr

from app.config import Settings


@pytest.fixture
def api_settings() -> Settings:
    return Settings(
        app_env="test",
        api_port=8000,
        postgres_user="test_user",
        postgres_password="test_password",
        postgres_db="test_db",
        database_url="postgresql+psycopg://test_user:test_password@localhost:5432/test_db",
        redis_url="redis://localhost:6379/0",
        jwt_secret=SecretStr("0123456789abcdef0123456789abcdef"),
        jwt_algorithm="HS256",
        jwt_expires_min=60,
        seed_user_password=SecretStr("test_password_123"),
        app_timezone="America/Argentina/Buenos_Aires",
        cors_origin="http://localhost:5173",
        vite_api_url="http://localhost:8000/api",
    )

