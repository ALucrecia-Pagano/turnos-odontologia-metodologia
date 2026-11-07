from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.auth import router as auth_router
from app.api.deps import protected_router
from app.api.errors import (
    AuthenticationError,
    DomainRejectedError,
    NotFoundError,
    authentication_error_handler,
    domain_rejected_handler,
    not_found_error_handler,
    request_validation_handler,
)
from app.api.appointments import router as appointments_router
from app.api.blocks import router as blocks_router
from app.api.chairs import router as chairs_router
from app.api.health import router as health_router
from app.api.openapi import setup_openapi
from app.api.patients import router as patients_router
from app.api.professionals import router as professionals_router
from app.api.services import router as services_router
from app.api.working_hours import router as working_hours_router
from app.auth.passwords import dummy_password_hash
from app.config import Settings, load_settings
from app.db.session import create_database_engine

protected_router.include_router(professionals_router)
protected_router.include_router(chairs_router)
protected_router.include_router(services_router)
protected_router.include_router(patients_router)
protected_router.include_router(working_hours_router)
protected_router.include_router(blocks_router)
protected_router.include_router(appointments_router)







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
        swagger_ui_parameters={"persistAuthorization": True},
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

    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(DomainRejectedError, domain_rejected_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)

    api_router = APIRouter(prefix="/api")
    api_router.include_router(health_router)
    api_router.include_router(auth_router)
    api_router.include_router(protected_router)
    app.include_router(api_router)

    setup_openapi(app)

    dummy_password_hash()

    return app
