from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import settings
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import PolicyPipelineRequest, PolicyPipelineResponse
from app.schemas.policy_upload import PolicyUploadIngestRequest, PolicyUploadPreviewResponse
from app.services.policy_pipeline import PolicyPipelineService
from app.services.policy_upload_service import PolicyUploadService

router = APIRouter()


def _upload_service() -> PolicyUploadService:
    return PolicyUploadService(Path(settings.policy_pipeline_workspace))


@router.post("/policy-pipeline/preview", response_model=PolicyPipelineResponse)
async def preview_policy_pipeline(request: PolicyPipelineRequest) -> PolicyPipelineResponse:
    """执行 1 到 8 阶段的流水线，但不写入数据库。"""
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
    """执行 1 到 8 阶段的流水线，并落库 document/version/section。"""
    service = PolicyPipelineService(repository=PolicyRepository(session))
    try:
        return service.ingest(request)
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/policy-pipeline/preview-upload", response_model=PolicyUploadPreviewResponse)
async def preview_policy_pipeline_upload(
    file: UploadFile = File(...),
    policy_category: str = Form("管理制度"),
    responsible_department: str | None = Form(None),
    version_label: str | None = Form(None),
) -> PolicyUploadPreviewResponse:
    upload_service = _upload_service()
    try:
        staged = upload_service.stage_upload(file)
        response = PolicyPipelineService().preview(
            PolicyPipelineRequest(
                source_path=staged.stored_path,
                policy_category=policy_category,
                responsible_department=responsible_department,
                version_label=version_label,
            )
        )
        return PolicyUploadPreviewResponse(**response.model_dump(), upload_id=staged.upload_id)
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@router.post("/policy-pipeline/ingest-upload", response_model=PolicyPipelineResponse)
async def ingest_policy_pipeline_upload(
    request: PolicyUploadIngestRequest,
    session: Session = Depends(get_db_session),
) -> PolicyPipelineResponse:
    upload_service = _upload_service()
    service = PolicyPipelineService(repository=PolicyRepository(session))
    try:
        source_path = upload_service.resolve_upload(request.upload_id)
        return service.ingest(
            PolicyPipelineRequest(
                source_path=source_path,
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                version_label=request.version_label,
            )
        )
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
