from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError

from app.infrastructure.persistence.schema_health import (
    KB_SCHEMA_SETUP_GUIDE,
    is_missing_kb_schema_error,
)
from app.interfaces.http.assemblers.policy_decision import decision_command, decision_response
from app.interfaces.http.dependencies import get_policy_decision_application_service
from app.interfaces.http.schemas.policy_decision import (
    PolicyDecisionChecklistRequest,
    PolicyDecisionChecklistResponse,
)
from app.modules.online.application.policy_decision import PolicyDecisionApplicationService
from app.shared.exceptions import UpstreamServiceError

router = APIRouter()


@router.post(
    "/policy-decisions/court-evaluation-materials/review",
    response_model=PolicyDecisionChecklistResponse,
)
async def review_court_evaluation_materials(
    request: PolicyDecisionChecklistRequest,
    service: PolicyDecisionApplicationService = Depends(get_policy_decision_application_service),
) -> PolicyDecisionChecklistResponse:
    """通过在线决策应用层暴露当前材料核验能力。"""
    try:
        return decision_response(service.review(decision_command(request)))
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
