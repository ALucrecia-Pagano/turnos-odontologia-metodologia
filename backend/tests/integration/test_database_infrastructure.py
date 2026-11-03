from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.engine import URL

from app.config import Settings


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
