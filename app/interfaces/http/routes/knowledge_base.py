from fastapi import APIRouter, Depends, Query

from app.composition import ApplicationContainer
from app.interfaces.http.assemblers.knowledge_base import (
    documents_response,
    overview_response,
    status_response,
)
from app.interfaces.http.dependencies import (
    get_application_container,
    get_stateless_application_container,
)
from app.interfaces.http.schemas.knowledge_base import (
    KnowledgeBaseOverview,
    PolicyDocumentOptionList,
    RagMvpStatus,
)

router = APIRouter()


@router.get("/overview", response_model=KnowledgeBaseOverview)
async def get_knowledge_base_overview(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> KnowledgeBaseOverview:
    """获取知识库概览信息。"""
    return overview_response(container.knowledge_base_service().get_overview())


@router.get("/mvp-status", response_model=RagMvpStatus)
async def get_rag_mvp_status(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> RagMvpStatus:
    """获取当前 RAG MVP 状态。"""
    return status_response(container.knowledge_base_service().get_rag_mvp_status())


@router.get("/documents", response_model=PolicyDocumentOptionList)
async def list_policy_documents(
    search: str | None = Query(default=None, description="按制度名称模糊搜索。"),
    policy_category: str | None = Query(default=None, description="按制度分类过滤。"),
    limit: int = Query(default=50, ge=1, le=200, description="返回数量上限。"),
    container: ApplicationContainer = Depends(get_application_container),
) -> PolicyDocumentOptionList:
    """列出当前知识库中的制度文档。"""
    return documents_response(
        container.knowledge_base_service().list_documents(
            search=search,
            policy_category=policy_category,
            limit=limit,
        )
    )
