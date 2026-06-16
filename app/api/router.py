from fastapi import APIRouter

from app.api.routes import health, knowledge_base

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(knowledge_base.router, prefix="/kb", tags=["knowledge-base"])
