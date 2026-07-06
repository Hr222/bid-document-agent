from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error
from app.repositories.policy_repository import PolicyRepository
from app.schemas import (
    RagAskRequest,
    RagAskResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.exceptions import ServiceNotConfiguredError, UpstreamServiceError
from app.services.rag_answer_service import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    RagAnswerService,
)
from app.services.retrieval_service import KnowledgeRetrievalService

router = APIRouter()


def _is_insufficient_evidence_answer(answer: str) -> bool:
    normalized = answer.strip()
    return normalized == INSUFFICIENT_EVIDENCE_ANSWER or "足够依据" in normalized


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
async def search_knowledge_base(
    request: RetrievalSearchRequest,
    session: Session = Depends(get_db_session),
) -> RetrievalSearchResponse:
    service = KnowledgeRetrievalService(PolicyRepository(session))
    try:
        return service.search(request)
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/retrieval/ask", response_model=RagAskResponse)
async def ask_knowledge_base(
    request: RagAskRequest,
    session: Session = Depends(get_db_session),
) -> RagAskResponse:
    repository = PolicyRepository(session)
    retrieval_service = KnowledgeRetrievalService(repository)
    try:
        search_response = retrieval_service.search(
            RetrievalSearchRequest(
                query=request.query,
                top_k=request.top_k,
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                document_id=request.document_id,
                include_history=request.include_history,
            )
        )
        if not search_response.hits:
            return RagAskResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                model=None,
                citations=[],
                hits=[],
            )

        answer_service = RagAnswerService()
        answer_response = answer_service.answer(query=request.query, hits=search_response.hits)
        if _is_insufficient_evidence_answer(answer_response.answer):
            return answer_response.model_copy(update={"citations": [], "hits": []})
        return answer_response
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
