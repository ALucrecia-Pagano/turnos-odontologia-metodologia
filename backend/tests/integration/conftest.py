from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
import psycopg
import pytest
from psycopg import sql
from sqlalchemy import Connection, Engine, text
from sqlalchemy.engine import URL, make_url

from app.config import Settings, load_settings
from app.db.session import create_database_engine


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def migration_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.attributes["database_url"] = database_url
    return config


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def test_database_url(integration_settings: Settings) -> Iterator[URL]:
    source_url = make_url(integration_settings.database_url)
    test_database = f"{integration_settings.postgres_db}_test"
    admin_url = source_url.set(database="postgres", drivername="postgresql")
    with psycopg.connect(admin_url.render_as_string(hide_password=False)) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (test_database,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "CREATE DATABASE "
                    + sql.Identifier(test_database).as_string(connection)
                )
    yield source_url.set(database=test_database)


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database(test_database_url: URL) -> Iterator[None]:
    config = migration_config(test_database_url.render_as_string(hide_password=False))
    command.upgrade(config, "head")
    yield


@pytest.fixture
def test_engine(test_database_url: URL) -> Iterator[Engine]:
    settings = load_settings()
    test_settings = settings.model_copy(
        update={
            "database_url": test_database_url.render_as_string(
                hide_password=False
            )
        }
    )
    engine = create_database_engine(test_settings)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def connection(test_engine: Engine) -> Iterator[Connection]:
    with test_engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()


@pytest.fixture
def test_table(connection: Connection) -> Iterator[None]:
    connection.execute(text("CREATE TABLE IF NOT EXISTS c13_test (value integer)"))
    yield


def clean_database_tables(engine: Engine) -> None:
    """Limpia las tablas de la base de prueba respetando el trigger append-only.

    La tabla appointment_status_change cuenta con triggers de base de datos que
    impiden UPDATE, DELETE y TRUNCATE para garantizar la inmutabilidad fisica
    del historial funcional. Para que las pruebas de integracion que realizan commit
    directo sobre test_engine puedan restablecer el estado entre casos de prueba
    sin alterar el esquema ni requerir reinicio del contenedor, este helper
    deshabilita temporalmente los triggers de usuario durante el vaciado y los
    reactiva de forma incondicional dentro de un bloque finally.
    """
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE appointment_status_change DISABLE TRIGGER USER"))
            conn.execute(
                text(
                    "TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE"
                )
            )
            conn.execute(text("DELETE FROM patient"))
            conn.execute(text("DELETE FROM service"))
            conn.execute(text("DELETE FROM chair"))
            conn.execute(text("DELETE FROM professional"))
        finally:
            conn.execute(text("ALTER TABLE appointment_status_change ENABLE TRIGGER USER"))
