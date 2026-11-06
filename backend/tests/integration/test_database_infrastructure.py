from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.script import ScriptDirectory
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


def current_head(config: Config) -> str | None:
    return ScriptDirectory.from_config(config).get_current_head()


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
            == current_head(config)
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
            "appointment",
            "appointment_status_change",
            "app_user",
        }.isdisjoint(table_names)

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == current_head(config)
        )


def test_availability_migration_downgrade_minus_one_cycle(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.downgrade(config, "20261104_03_horarios_y_bloqueos")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )

    command.downgrade(config, "-1")
    with test_engine.connect() as connection:
        table_names = inspect(connection).get_table_names()
        assert {"working_hours", "block", "appointment", "appointment_status_change"}.isdisjoint(table_names)
        assert {"professional", "chair", "service", "patient"}.issubset(table_names)
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261103_02_catalogos_y_pacientes"
        )

    command.upgrade(config, "head")


def test_appointment_migration_downgrade_minus_one_cycle(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.downgrade(config, "20261104_03_horarios_y_bloqueos")
    command.upgrade(config, "20261105_04_turnos_e_historial")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261105_04_turnos_e_historial"
        )
        table_names = inspect(connection).get_table_names()
        assert {"appointment", "appointment_status_change"}.issubset(table_names)
        trigger_count = connection.execute(
            text(
                "SELECT count(DISTINCT tgname) FROM pg_trigger "
                "WHERE tgrelid = 'appointment_status_change'::regclass "
                "AND tgname = 'tr_appointment_status_change_append_only'"
            )
        ).scalar_one()
        assert trigger_count == 1

    command.downgrade(config, "-1")
    with test_engine.connect() as connection:
        table_names = inspect(connection).get_table_names()
        assert {"appointment", "appointment_status_change"}.isdisjoint(table_names)
        assert {
            "professional",
            "chair",
            "service",
            "patient",
            "working_hours",
            "block",
        }.issubset(table_names)
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261104_03_horarios_y_bloqueos"
        )

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == current_head(config)
        )


def test_appointment_history_no_truncate_migration_downgrade_minus_one_cycle(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == current_head(config)
        )
        triggers = connection.execute(
            text(
                "SELECT tgname FROM pg_trigger "
                "WHERE tgrelid = 'appointment_status_change'::regclass "
                "AND NOT tgisinternal"
            )
        ).scalars().all()
        assert "tr_appointment_status_change_no_truncate" in triggers
        assert "tr_appointment_status_change_append_only" in triggers

    command.downgrade(config, "20261105_05_historial_sin_truncate")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261105_05_historial_sin_truncate"
        )
        triggers = connection.execute(
            text(
                "SELECT tgname FROM pg_trigger "
                "WHERE tgrelid = 'appointment_status_change'::regclass "
                "AND NOT tgisinternal"
            )
        ).scalars().all()
        assert "tr_appointment_status_change_no_truncate" in triggers
        assert "tr_appointment_status_change_append_only" in triggers

    command.downgrade(config, "20261105_04_turnos_e_historial")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261105_04_turnos_e_historial"
        )
        triggers = connection.execute(
            text(
                "SELECT tgname FROM pg_trigger "
                "WHERE tgrelid = 'appointment_status_change'::regclass "
                "AND NOT tgisinternal"
            )
        ).scalars().all()
        assert "tr_appointment_status_change_no_truncate" not in triggers
        assert "tr_appointment_status_change_append_only" in triggers

    command.upgrade(config, "head")
    with test_engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == current_head(config)
        )



def test_user_migration_explicit_downgrade_cycle(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.upgrade(config, "20261106_06_usuarios")
    command.downgrade(config, "20261105_05_historial_sin_truncate")
    with test_engine.connect() as connection:
        table_names = inspect(connection).get_table_names()
        assert "app_user" not in table_names
        assert {"professional", "appointment", "appointment_status_change"}.issubset(
            table_names
        )
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261105_05_historial_sin_truncate"
        )

    # Solo deja la base como la encontro: el ciclo verificado usa revisiones explicitas.
    command.upgrade(config, "head")


def test_user_migration_explicit_upgrade(
    test_engine: Engine,
    test_database_url: URL,
) -> None:
    config = migration_config(test_database_url.render_as_string(hide_password=False))

    command.downgrade(config, "20261105_05_historial_sin_truncate")
    command.upgrade(config, "20261106_06_usuarios")
    with test_engine.connect() as connection:
        assert "app_user" in inspect(connection).get_table_names()
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version"))
            .scalar_one()
            == "20261106_06_usuarios"
        )

    # Solo deja la base como la encontro: el ciclo verificado usa revisiones explicitas.
    command.upgrade(config, "head")


def test_metadata_has_no_differences_with_users(connection: Connection) -> None:
    assert "app_user" in inspect(connection).get_table_names()
    assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


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
