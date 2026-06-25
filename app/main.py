from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @application.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "message": "投标文档助手接口",
            "phase": "rag-mvp",
            "frontend": "/frontend",
        }

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
