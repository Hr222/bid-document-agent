from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import settings
from app.core.logging import get_logger
from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error
from app.repositories.policy_repository import PolicyRepository
from app.schemas import PolicyPipelineRequest, PolicyPipelineResponse
from app.schemas.policy_upload import PolicyUploadIngestRequest, PolicyUploadPreviewResponse
from app.services.pipeline import PolicyPipelineService
from app.services.policy_upload_service import PolicyUploadService

router = APIRouter()
logger = get_logger("app.api.policy_pipeline")


def _upload_service() -> PolicyUploadService:
    return PolicyUploadService(Path(settings.policy_pipeline_workspace))


def _validate_target_document_id(
    repository: PolicyRepository,
    target_document_id: int | None,
) -> None:
    if target_document_id is None:
        return
    if repository.document_exists(target_document_id):
        return
    raise HTTPException(
        status_code=400,
        detail="指定的已有关联制度不存在，可能是数据库已重建或记录已被删除，请重新选择后再试。",
    )


@router.post("/policy-pipeline/preview", response_model=PolicyPipelineResponse)
async def preview_policy_pipeline(request: PolicyPipelineRequest) -> PolicyPipelineResponse:
    """执行预览流水线，不写入数据库。"""
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
    """执行完整流水线，并写入制度文档、版本、章节和切块。"""
    repository = PolicyRepository(session)
    _validate_target_document_id(repository, request.target_document_id)
    service = PolicyPipelineService(repository=repository)
    try:
        return service.ingest(request)
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            logger.exception("Knowledge base schema missing during ingest path=%s", request.source_path)
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
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
                target_document_id=None,
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
    repository = PolicyRepository(session)
    _validate_target_document_id(repository, request.target_document_id)
    service = PolicyPipelineService(repository=repository)
    try:
        source_path = upload_service.resolve_upload(request.upload_id)
        return service.ingest(
            PolicyPipelineRequest(
                source_path=source_path,
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                version_label=request.version_label,
                target_document_id=request.target_document_id,
            )
        )
    except ProgrammingError as exc:
        if is_missing_kb_schema_error(exc):
            logger.exception(
                "Knowledge base schema missing during ingest upload upload_id=%s",
                request.upload_id,
            )
            raise HTTPException(status_code=503, detail=KB_SCHEMA_SETUP_GUIDE) from exc
        raise
    except (FileNotFoundError, IsADirectoryError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
