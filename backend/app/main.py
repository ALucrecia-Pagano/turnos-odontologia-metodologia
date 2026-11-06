from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.errors import (
    DomainRejectedError,
    domain_rejected_handler,
    request_validation_handler,
)
from app.api.health import router as health_router
from app.api.openapi import setup_openapi
from app.config import Settings, load_settings
from app.db.session import create_database_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    engine: Engine = app.state.engine
    engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()
    engine = create_database_engine(resolved_settings)
    session_factory: sessionmaker[Session] = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    app = FastAPI(
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.state.settings = resolved_settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.cors_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.add_exception_handler(DomainRejectedError, domain_rejected_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(health_router)
    app.include_router(api_router)

    setup_openapi(app)

    return app
