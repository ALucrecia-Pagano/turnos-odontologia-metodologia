from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.errors import DomainRejectedError
from app.config import Settings
from app.domain.violations import Rejected, Violation, ViolationCode
from app.main import create_app


@pytest.fixture
def session_test_table(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS test_session_row ("
                "id INT PRIMARY KEY, name VARCHAR(50)"
                ")"
            )
        )
    try:
        yield
    finally:
        with test_engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_session_row"))


@pytest.mark.integration
def test_committed_write_persists(
    integration_settings: Settings,
    test_database_url: URL,
    test_engine: Engine,
    session_test_table: None,
) -> None:
    test_settings = integration_settings.model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )
    app = create_app(test_settings)
    router = APIRouter()

    @router.post("/commit-write")
    def commit_write(session: Session = Depends(get_db_session)) -> dict[str, str]:
        session.execute(text("INSERT INTO test_session_row (id, name) VALUES (1, 'persisted')"))
        session.commit()
        return {"status": "ok"}

    app.include_router(router)
    client = TestClient(app)

    response = client.post("/commit-write")
    assert response.status_code == 200

    with test_engine.connect() as conn:
        row = conn.execute(text("SELECT name FROM test_session_row WHERE id = 1")).fetchone()
        assert row is not None
        assert row[0] == "persisted"


@pytest.mark.integration
def test_uncommitted_write_does_not_persist(
    integration_settings: Settings,
    test_database_url: URL,
    test_engine: Engine,
    session_test_table: None,
) -> None:
    test_settings = integration_settings.model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )
    app = create_app(test_settings)
    router = APIRouter()

    @router.post("/uncommitted-write")
    def uncommitted_write(session: Session = Depends(get_db_session)) -> dict[str, str]:
        session.execute(text("INSERT INTO test_session_row (id, name) VALUES (2, 'uncommitted')"))
        return {"status": "ok"}

    app.include_router(router)
    client = TestClient(app)

    response = client.post("/uncommitted-write")
    assert response.status_code == 200

    with test_engine.connect() as conn:
        row = conn.execute(text("SELECT name FROM test_session_row WHERE id = 2")).fetchone()
        assert row is None


@pytest.mark.integration
def test_exception_rolls_back_write(
    integration_settings: Settings,
    test_database_url: URL,
    test_engine: Engine,
    session_test_table: None,
) -> None:
    test_settings = integration_settings.model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )
    app = create_app(test_settings)
    router = APIRouter()

    @router.post("/exception-write")
    def exception_write(session: Session = Depends(get_db_session)) -> None:
        session.execute(text("INSERT INTO test_session_row (id, name) VALUES (3, 'exception')"))
        raise DomainRejectedError(
            Rejected(violations=(Violation(code=ViolationCode.EMPTY_NAME, message="Nombre vacío"),))
        )

    app.include_router(router)
    client = TestClient(app)

    response = client.post("/exception-write")
    assert response.status_code == 422

    with test_engine.connect() as conn:
        row = conn.execute(text("SELECT name FROM test_session_row WHERE id = 3")).fetchone()
        assert row is None

