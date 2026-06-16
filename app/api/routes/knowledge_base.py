from fastapi import APIRouter

from app.schemas.knowledge_base import KnowledgeBaseOverview, RagMvpStatus
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter()


@router.get("/overview", response_model=KnowledgeBaseOverview)
async def get_knowledge_base_overview() -> KnowledgeBaseOverview:
    return KnowledgeBaseService().get_overview()


@router.get("/mvp-status", response_model=RagMvpStatus)
async def get_rag_mvp_status() -> RagMvpStatus:
    return KnowledgeBaseService().get_rag_mvp_status()
