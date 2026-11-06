from collections.abc import Iterator
import os
import subprocess
import sys

from fastapi.testclient import TestClient
from pydantic import SecretStr
import pytest
from sqlalchemy import Engine, text

from app.config import Settings
from app.db.seed import SeedConfigurationError, seed_database
from app.main import create_app
from tests.integration.conftest import BACKEND_ROOT, clean_database_tables


pytestmark = pytest.mark.integration

SEED_PASSWORD = "clave-ficticia-del-seed"
ARGON2_PREFIX = "$argon2id$v=19$m=65536,t=3,p=4$"
BUSINESS_TABLES = (
    "app_user",
    "professional",
    "chair",
    "service",
    "patient",
    "working_hours",
    "block",
    "appointment",
    "appointment_status_change",
)


@pytest.fixture
def empty_database(test_engine: Engine) -> Iterator[None]:
    clean_database_tables(test_engine)
    try:
        yield
    finally:
        clean_database_tables(test_engine)


def settings_with(settings: Settings, **updates: object) -> Settings:
    return settings.model_copy(update=updates)


def valid_settings(auth_settings: Settings) -> Settings:
    return settings_with(auth_settings, seed_user_password=SecretStr(SEED_PASSWORD))


def row_counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            table: connection.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
            for table in BUSINESS_TABLES
        }


def assert_all_tables_empty(engine: Engine) -> None:
    assert row_counts(engine) == dict.fromkeys(BUSINESS_TABLES, 0)


def password_hashes(engine: Engine) -> dict[str, str]:
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT username, password_hash FROM app_user"))
        return {row.username: row.password_hash for row in rows}


def run_seed_command(
    auth_settings: Settings, password: str
) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "DATABASE_URL": auth_settings.database_url,
        "SEED_USER_PASSWORD": password,
        "PYTHONUTF8": "1",
    }
    return subprocess.run(
        [sys.executable, "-m", "app.db.seed"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def test_seed_creates_one_user_per_role(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    result = seed_database(valid_settings(auth_settings))

    assert result["app_user"] == 3
    with test_engine.connect() as connection:
        roles = connection.execute(text("SELECT role FROM app_user")).scalars().all()
    assert sorted(roles) == ["administrador", "odontologo", "recepcion"]


def test_seed_users_can_log_in(auth_settings: Settings, empty_database: None) -> None:
    settings = valid_settings(auth_settings)
    seed_database(settings)
    app = create_app(settings)
    client = TestClient(app)

    try:
        for username in ("administrador", "recepcion", "odontologo"):
            response = client.post(
                "/api/auth/login", json={"username": username, "password": SEED_PASSWORD}
            )
            assert response.status_code == 200, username
    finally:
        app.state.engine.dispose()


def test_second_seed_inserts_nothing(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    settings = valid_settings(auth_settings)
    seed_database(settings)
    before = password_hashes(test_engine)

    result = seed_database(settings)

    assert result["app_user"] == 3
    assert password_hashes(test_engine) == before


def test_seed_does_not_change_existing_password(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    seed_database(valid_settings(auth_settings))
    before = password_hashes(test_engine)
    assert len(before) == 3

    seed_database(settings_with(auth_settings, seed_user_password=SecretStr("otra-clave-ficticia")))

    assert password_hashes(test_engine) == before


def test_seed_stores_argon2id_hash(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    seed_database(valid_settings(auth_settings))

    hashes = password_hashes(test_engine)
    assert len(hashes) == 3
    for stored in hashes.values():
        assert stored.startswith(ARGON2_PREFIX)
        assert SEED_PASSWORD not in stored


def test_seed_user_id_differs_from_professional_id(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    seed_database(valid_settings(auth_settings))

    with test_engine.connect() as connection:
        row = connection.execute(
            text("SELECT id, professional_id FROM app_user WHERE username = 'odontologo'")
        ).one()
    assert row.professional_id is not None
    assert row.id != row.professional_id


def test_seed_output_hides_password(auth_settings: Settings, empty_database: None) -> None:
    completed = run_seed_command(auth_settings, SEED_PASSWORD)

    assert completed.returncode == 0, completed.stderr[-300:]
    assert "app_user: 3" in completed.stdout
    assert SEED_PASSWORD not in completed.stdout + completed.stderr


def assert_seed_rejects_password(
    auth_settings: Settings, test_engine: Engine, password: SecretStr | None
) -> SeedConfigurationError:
    with pytest.raises(SeedConfigurationError, match="SEED_USER_PASSWORD") as error:
        seed_database(settings_with(auth_settings, seed_user_password=password))
    assert_all_tables_empty(test_engine)
    return error.value


def test_seed_rejects_missing_password(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    assert_seed_rejects_password(auth_settings, test_engine, None)


def test_seed_rejects_empty_password(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    assert_seed_rejects_password(auth_settings, test_engine, SecretStr(""))


def test_seed_rejects_blank_password(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    assert_seed_rejects_password(auth_settings, test_engine, SecretStr(" " * 8))


def test_seed_rejects_short_password(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    error = assert_seed_rejects_password(auth_settings, test_engine, SecretStr("MARCA12"))

    assert "MARCA12" not in str(error)


def test_seed_accepts_eight_characters(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    result = seed_database(settings_with(auth_settings, seed_user_password=SecretStr("ocho1234")))

    assert result["app_user"] == 3
    assert row_counts(test_engine)["app_user"] == 3


def test_seed_command_exits_with_error(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    completed = run_seed_command(auth_settings, "")

    assert completed.returncode != 0
    assert "SEED_USER_PASSWORD" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert_all_tables_empty(test_engine)


def test_seed_refuses_production(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    with pytest.raises(SeedConfigurationError, match="APP_ENV"):
        seed_database(
            settings_with(
                auth_settings,
                app_env="production",
                seed_user_password=SecretStr(SEED_PASSWORD),
            )
        )
    assert_all_tables_empty(test_engine)


def test_seed_runs_in_development(
    auth_settings: Settings, test_engine: Engine, empty_database: None
) -> None:
    result = seed_database(
        settings_with(
            auth_settings,
            app_env="development",
            seed_user_password=SecretStr(SEED_PASSWORD),
        )
    )

    assert result["app_user"] == 3
    assert row_counts(test_engine)["app_user"] == 3
