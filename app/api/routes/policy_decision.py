from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_decision import (
    PolicyDecisionChecklistRequest,
    PolicyDecisionChecklistResponse,
)
from app.services.exceptions import UpstreamServiceError
from app.services.policy_decision import RuleDrivenChecklistDecisionService
from app.services.retrieval import KnowledgeRetrievalService

router = APIRouter()


def _decision_service(session: Session = Depends(get_db_session)) -> RuleDrivenChecklistDecisionService:
    """按请求作用域构建材料核验服务。"""
    repository = PolicyRepository(session)
    retrieval_service = KnowledgeRetrievalService(repository)
    return RuleDrivenChecklistDecisionService(retrieval_service)


@router.post(
    "/policy-decisions/court-evaluation-materials/review",
    response_model=PolicyDecisionChecklistResponse,
)
async def review_court_evaluation_materials(
    request: PolicyDecisionChecklistRequest,
    service: RuleDrivenChecklistDecisionService = Depends(_decision_service),
) -> PolicyDecisionChecklistResponse:
    """对外暴露法院委托评估机构材料核验接口。"""
    try:
        return service.review_court_evaluation_materials(request)
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
