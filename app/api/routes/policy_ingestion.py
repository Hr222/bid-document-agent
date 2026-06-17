from fastapi import APIRouter, HTTPException

from app.schemas.policy_ingestion import (
    PolicyPreviewRequest,
    PolicyPreviewResponse,
    PolicyScanRequest,
    PolicyScanResponse,
)
from app.services.policy_ingestion import PolicyIngestionService

router = APIRouter()


@router.post("/policy-ingestion/scan", response_model=PolicyScanResponse)
async def scan_policy_candidates(request: PolicyScanRequest) -> PolicyScanResponse:
    service = PolicyIngestionService()
    try:
        return service.scan_candidates(request)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/policy-ingestion/preview", response_model=PolicyPreviewResponse)
async def preview_policy_parse(request: PolicyPreviewRequest) -> PolicyPreviewResponse:
    service = PolicyIngestionService()
    try:
        return service.preview_parse(request.source_path)
    except (FileNotFoundError, IsADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
