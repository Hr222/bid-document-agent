"""知识库管理工作台 HTTP 接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.interfaces.http.assemblers.knowledge_management import (
    categories_response,
    detail_response,
    documents_response,
    management_query,
    overview_response,
    recent_management_query,
)
from app.interfaces.http.dependencies import get_knowledge_management_service
from app.interfaces.http.schemas.knowledge_management import (
    KnowledgeManagementCategoryListResponse,
    KnowledgeManagementDocumentDetailResponse,
    KnowledgeManagementDocumentListQuery,
    KnowledgeManagementDocumentListResponse,
    KnowledgeManagementOverviewResponse,
    KnowledgeManagementRecentDocumentQuery,
)
from app.modules.knowledge.application.management_service import KnowledgeManagementService

router = APIRouter()


@router.get("/management/overview", response_model=KnowledgeManagementOverviewResponse)
async def get_management_overview(
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeManagementOverviewResponse:
    return overview_response(service.get_overview())


@router.get(
    "/management/categories",
    response_model=KnowledgeManagementCategoryListResponse,
)
async def list_management_categories(
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeManagementCategoryListResponse:
    return categories_response(service.list_categories())


@router.get(
    "/management/documents",
    response_model=KnowledgeManagementDocumentListResponse,
)
async def list_management_documents(
    query: Annotated[KnowledgeManagementDocumentListQuery, Query()],
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeManagementDocumentListResponse:
    return documents_response(service.list_documents(management_query(query)))


@router.get(
    "/management/recent-documents",
    response_model=KnowledgeManagementDocumentListResponse,
)
async def list_recent_management_documents(
    query: Annotated[KnowledgeManagementRecentDocumentQuery, Query()],
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeManagementDocumentListResponse:
    return documents_response(
        service.list_recent_documents(recent_management_query(query))
    )


@router.get(
    "/management/documents/{document_id}",
    response_model=KnowledgeManagementDocumentDetailResponse,
)
async def get_management_document(
    document_id: int,
    service: KnowledgeManagementService = Depends(get_knowledge_management_service),
) -> KnowledgeManagementDocumentDetailResponse:
    try:
        return detail_response(service.get_document(document_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
