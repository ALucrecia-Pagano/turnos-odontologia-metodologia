import logging
from typing import Protocol

from sqlalchemy import Engine, event
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


class _HideRowValues(logging.Filter):
    """En DEBUG, SQLAlchemy registra cada fila leída; `hide_parameters` no lo cubre."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.msg != "Row %r"


logging.getLogger("sqlalchemy.engine.Engine").addFilter(_HideRowValues())


class _Cursor(Protocol):
    def execute(self, statement: str) -> object:
        ...

    def close(self) -> None:
        ...


class _DbApiConnection(Protocol):
    def cursor(self) -> _Cursor:
        ...


def create_database_engine(settings: Settings) -> Engine:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 3},
    )

    @event.listens_for(engine, "connect")
    def set_utc_timezone(
        dbapi_connection: _DbApiConnection, connection_record: object
    ) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET TIME ZONE 'UTC'")
        finally:
            cursor.close()

    return engine


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_database_engine(settings),
        class_=Session,
        expire_on_commit=False,
    )


def database_url_for_test(settings: Settings) -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host="localhost",
        port=5432,
        database=f"{settings.postgres_db}_test",
    )
