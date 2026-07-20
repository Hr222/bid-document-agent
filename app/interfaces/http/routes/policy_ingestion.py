from fastapi import APIRouter, Depends, HTTPException

from app.interfaces.http.dependencies import get_policy_ingestion_service
from app.interfaces.http.schemas.policy_ingestion import PolicyScanRequest, PolicyScanResponse
from app.modules.ingestion import PolicyIngestionService

router = APIRouter()


@router.post("/policy-ingestion/scan", response_model=PolicyScanResponse)
async def scan_policy_candidates(
    request: PolicyScanRequest,
    service: PolicyIngestionService = Depends(get_policy_ingestion_service),
) -> PolicyScanResponse:
    """通过统一依赖入口执行候选制度文件扫描。"""
    try:
        return service.scan_candidates(request)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
