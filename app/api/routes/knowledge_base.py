from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.knowledge_base import (
    KnowledgeBaseOverview,
    PolicyDocumentOptionList,
    RagMvpStatus,
)
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter()


@router.get("/overview", response_model=KnowledgeBaseOverview)
async def get_knowledge_base_overview() -> KnowledgeBaseOverview:
    return KnowledgeBaseService().get_overview()


@router.get("/mvp-status", response_model=RagMvpStatus)
async def get_rag_mvp_status() -> RagMvpStatus:
    return KnowledgeBaseService().get_rag_mvp_status()


@router.get("/documents", response_model=PolicyDocumentOptionList)
async def list_policy_documents(
    search: str | None = Query(default=None, description="按制度名称模糊搜索。"),
    policy_category: str | None = Query(default=None, description="按制度分类过滤。"),
    limit: int = Query(default=50, ge=1, le=200, description="返回数量上限。"),
    session: Session = Depends(get_db_session),
) -> PolicyDocumentOptionList:
    return KnowledgeBaseService().list_documents(
        session,
        search=search,
        policy_category=policy_category,
        limit=limit,
    )
