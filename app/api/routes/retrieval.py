from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError

from app.api.deps import get_policy_capability_bridge
from app.bridges import PolicyCapabilityBridge
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error
from app.schemas import (
    RagAskRequest,
    RagAskResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.exceptions import ServiceNotConfiguredError, UpstreamServiceError

router = APIRouter()


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
async def search_knowledge_base(
    request: RetrievalSearchRequest,
    bridge: PolicyCapabilityBridge = Depends(get_policy_capability_bridge),
) -> RetrievalSearchResponse:
    """通过统一桥接层执行知识库检索。"""
    try:
        return bridge.search(request)
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
    bridge: PolicyCapabilityBridge = Depends(get_policy_capability_bridge),
) -> RagAskResponse:
    """通过统一桥接层执行先检索后问答的链路。"""
    try:
        return bridge.ask(request)
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
