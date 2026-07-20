from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError

from app.infrastructure.persistence.schema_health import (
    KB_SCHEMA_SETUP_GUIDE,
    is_missing_kb_schema_error,
)
from app.interfaces.http.assemblers.rag import (
    ask_command,
    ask_response,
    search_command,
    search_response,
)
from app.interfaces.http.dependencies import get_ask_knowledge_use_case
from app.interfaces.http.schemas import (
    RagAskRequest,
    RagAskResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.modules.online.application.ask_knowledge import AskKnowledgeUseCase
from app.shared.exceptions import ServiceNotConfiguredError, UpstreamServiceError

router = APIRouter()


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
async def search_knowledge_base(
    request: RetrievalSearchRequest,
    use_case: AskKnowledgeUseCase = Depends(get_ask_knowledge_use_case),
) -> RetrievalSearchResponse:
    """通过在线 RAG 外观层执行知识库检索。"""
    try:
        return search_response(use_case.search(search_command(request)))
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
    use_case: AskKnowledgeUseCase = Depends(get_ask_knowledge_use_case),
) -> RagAskResponse:
    """通过在线 RAG 外观层执行先检索后问答的链路。"""
    try:
        return ask_response(use_case.execute(ask_command(request)))
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
