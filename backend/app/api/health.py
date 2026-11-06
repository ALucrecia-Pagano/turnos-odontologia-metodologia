from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.api.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "Servicio y base de datos disponibles",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {"status": "ok", "database": "ok"}
                }
            },
        },
        503: {
            "description": "Base de datos no disponible",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {"status": "unavailable", "database": "unavailable"}
                }
            },
        },
    },
)
def health_check(request: Request) -> JSONResponse:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok", "database": "ok"},
        )
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "unavailable"},
        )
