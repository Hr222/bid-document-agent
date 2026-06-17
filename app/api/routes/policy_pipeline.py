from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import PolicyPipelineRequest, PolicyPipelineResponse
from app.services.policy_pipeline import PolicyPipelineService

router = APIRouter()


@router.post("/policy-pipeline/preview", response_model=PolicyPipelineResponse)
async def preview_policy_pipeline(request: PolicyPipelineRequest) -> PolicyPipelineResponse:
    """Run steps 1-8 without touching the database."""
    service = PolicyPipelineService()
    try:
        return service.preview(request)
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/policy-pipeline/ingest", response_model=PolicyPipelineResponse)
async def ingest_policy_pipeline(
    request: PolicyPipelineRequest,
    session: Session = Depends(get_db_session),
) -> PolicyPipelineResponse:
    """Run steps 1-8 and persist document/version/section records."""
    service = PolicyPipelineService(repository=PolicyRepository(session))
    try:
        return service.ingest(request)
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
