from fastapi import APIRouter

from app.api.routes import health, knowledge_base, policy_ingestion, policy_pipeline, retrieval

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(knowledge_base.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(policy_ingestion.router, prefix="/kb", tags=["policy-ingestion"])
api_router.include_router(policy_pipeline.router, prefix="/kb", tags=["policy-pipeline"])
api_router.include_router(retrieval.router, prefix="/kb", tags=["retrieval"])
