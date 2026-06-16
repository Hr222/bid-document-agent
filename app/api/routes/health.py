from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_version=settings.app_version,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    return HealthResponse(
        status="ready",
        app_name=settings.app_name,
        app_version=settings.app_version,
        timestamp=datetime.now(UTC),
    )
