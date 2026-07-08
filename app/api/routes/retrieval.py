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
from app.services.retrieval import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    KnowledgeRetrievalService,
    RagAnswerService,
)

router = APIRouter()


def _is_insufficient_evidence_answer(answer: str) -> bool:
    # 统一收口“证据不足”判断，避免不同模型表述导致 ask 链路分支不一致。
    normalized = answer.strip()
    return normalized == INSUFFICIENT_EVIDENCE_ANSWER or "足够依据" in normalized


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
async def search_knowledge_base(
    request: RetrievalSearchRequest,
    session: Session = Depends(get_db_session),
) -> RetrievalSearchResponse:
    # search 只负责参数接收与错误映射，具体检索编排放在 service / pipeline 中。
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
    # ask 先复用与 search 完全相同的检索链路，再决定是否进入问答生成。
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
            # 没有召回结果时直接返回证据不足，并把检索 debug 透传给前端。
            return RagAskResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                model=None,
                citations=[],
                hits=[],
                debug=search_response.debug,
            )

        answer_service = RagAnswerService()
        answer_response = answer_service.answer(query=request.query, hits=search_response.hits)
        if _is_insufficient_evidence_answer(answer_response.answer):
            # 如果模型判断证据不足，则隐藏命中和引用，但保留检索 debug 方便排查。
            return answer_response.model_copy(
                update={"citations": [], "hits": [], "debug": search_response.debug}
            )
        # 正常回答时也附带检索 debug，保证 search / ask 两条链路的可解释性一致。
        return answer_response.model_copy(update={"debug": search_response.debug})
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
