from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import ProgrammingError

from app.api.deps import get_policy_capability_bridge
from app.bridges import PolicyCapabilityBridge
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error
from app.schemas.policy_decision import (
    PolicyDecisionChecklistRequest,
    PolicyDecisionChecklistResponse,
)
from app.services.exceptions import UpstreamServiceError

router = APIRouter()


@router.post(
    "/policy-decisions/court-evaluation-materials/review",
    response_model=PolicyDecisionChecklistResponse,
)
async def review_court_evaluation_materials(
    request: PolicyDecisionChecklistRequest,
    bridge: PolicyCapabilityBridge = Depends(get_policy_capability_bridge),
) -> PolicyDecisionChecklistResponse:
    """通过统一桥接层暴露当前材料核验能力。"""
    try:
        return bridge.review_court_evaluation_materials(request)
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
