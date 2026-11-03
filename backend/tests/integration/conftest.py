from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import Connection, Engine, text
from sqlalchemy.engine import URL, make_url

from app.config import Settings, load_settings
from app.db.session import create_database_engine


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
