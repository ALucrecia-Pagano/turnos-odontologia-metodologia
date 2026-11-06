from fastapi import FastAPI
from app.config import Settings
import app.db.session as session_module
from app.main import create_app


def test_create_app_accepts_literal_settings(api_settings: Settings) -> None:
    app = create_app(api_settings)
    assert isinstance(app, FastAPI)
    assert app.state.settings == api_settings


def test_create_app_keeps_one_session_factory(api_settings: Settings) -> None:
    app = create_app(api_settings)
    assert hasattr(app.state, "session_factory")
    assert callable(app.state.session_factory)


def test_get_session_helper_is_removed() -> None:
    assert not hasattr(session_module, "get_session")

