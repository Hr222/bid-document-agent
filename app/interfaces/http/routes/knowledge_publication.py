from fastapi import APIRouter, Depends, HTTPException

from app.interfaces.http.dependencies import get_knowledge_publication_service
from app.interfaces.http.schemas.publication import (
    KnowledgePublicationRequest,
    KnowledgePublicationResponse,
)
from app.modules.knowledge.application.publication_service import KnowledgePublicationService

router = APIRouter()


@router.post("/publication/activate", response_model=KnowledgePublicationResponse)
async def activate_knowledge_version(
    request: KnowledgePublicationRequest,
    service: KnowledgePublicationService = Depends(get_knowledge_publication_service),
) -> KnowledgePublicationResponse:
    """发布一个已入库版本，使其进入在线知识读模型。"""
    try:
        result = service.publish(
            document_id=request.document_id,
            version_id=request.version_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgePublicationResponse(
        document_id=result.document_id,
        version_id=result.version_id,
        version_status=result.version_status,
    )
