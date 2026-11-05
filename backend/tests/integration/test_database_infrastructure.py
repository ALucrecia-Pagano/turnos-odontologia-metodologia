from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import (
    CheckConstraint,
    Column,
    Connection,
    ForeignKey,
    Index,
    Integer,
    Engine,
    MetaData,
    Table,
    UniqueConstraint,
    inspect,
    text,
)
from sqlalchemy.engine import URL

from app.db.base import Base
from app.config import Settings
from tests.integration.conftest import migration_config


pytestmark = pytest.mark.integration


def test_database_connection_and_select_one(connection: Connection) -> None:
    assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_connection_timezone_is_utc(connection: Connection) -> None:
    assert connection.execute(text("SHOW TIME ZONE")).scalar_one() == "UTC"


def test_timestamptz_round_trip_preserves_instant(
    connection: Connection,
) -> None:
    connection.execute(
        text(
            "CREATE TEMPORARY TABLE c13_instants "
            "(value timestamptz NOT NULL)"
        )
    )
    original = datetime(
        2026,
        10,
        20,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-3)),
    )
    connection.execute(
        text("INSERT INTO c13_instants (value) VALUES (:value)"),
        {"value": original},
    )
    returned = connection.execute(
        text("SELECT value FROM c13_instants")
    ).scalar_one()

    assert returned.astimezone(timezone.utc) == datetime(
        2026, 10, 20, 13, 0, tzinfo=timezone.utc
    )


def test_test_database_is_distinct_from_real_database(
    integration_settings: Settings,
    test_database_url: URL,
) -> None:
    assert integration_settings.postgres_db != test_database_url.database


def test_transaction_fixture_rolls_back_rows(
    connection: Connection,
    test_table: None,
) -> None:
    connection.execute(text("INSERT INTO c13_test (value) VALUES (1)"))
    assert connection.execute(text("SELECT count(*) FROM c13_test")).scalar_one() == 1


def test_migration_cycle_restores_test_database_to_head(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )

    command.downgrade(config, "base")
    with test_engine.connect() as connection:
        table_names = inspect(connection).get_table_names()
        assert {
            "professional",
            "chair",
            "service",
            "patient",
            "working_hours",
            "block",
        }.isdisjoint(table_names)

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )


def test_availability_migration_downgrade_minus_one_cycle(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )

    command.downgrade(config, "-1")
    with test_engine.connect() as connection:
        table_names = inspect(connection).get_table_names()
        assert {"working_hours", "block"}.isdisjoint(table_names)
        assert {"professional", "chair", "service", "patient"}.issubset(table_names)
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261103_02_catalogos_y_pacientes"
        )

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )


def test_autogenerate_finds_no_differences_after_migration(
    connection: Connection,
) -> None:
    migration_context = MigrationContext.configure(connection)

    assert compare_metadata(migration_context, Base.metadata) == []
    assert "alembic_version" not in Base.metadata.tables


def test_declarative_metadata_uses_stable_constraint_names() -> None:
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    Table("other", metadata, Column("id", Integer, primary_key=True))
    example = Table(
        "example",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("code", Integer),
        Column("ref_id", Integer, ForeignKey("other.id")),
        UniqueConstraint("code"),
        CheckConstraint("code > 0", name="positive_code"),
        Index(None, "code"),
    )

    assert example.primary_key.name == "pk_example"
    assert next(
        constraint
        for constraint in example.constraints
        if isinstance(constraint, UniqueConstraint)
    ).name == "uq_example_code"
    assert next(
        constraint
        for constraint in example.constraints
        if isinstance(constraint, CheckConstraint)
    ).name == "ck_example_positive_code"
    assert next(
        constraint
        for constraint in example.foreign_key_constraints
    ).name == "fk_example_ref_id_other"
    assert next(iter(example.indexes)).name == "ix_example_code"
