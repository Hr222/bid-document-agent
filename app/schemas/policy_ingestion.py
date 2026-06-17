from datetime import datetime

from pydantic import BaseModel, Field


class PolicyCandidateItem(BaseModel):
    source_path: str
    relative_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256: str
    recommended_action: str
    parse_method: str
    suspected_scanned: bool
    policy_name_guess: str
    include_reason: str | None = None
    exclude_reason: str | None = None


class PolicyScanStats(BaseModel):
    total_files: int
    included_files: int
    excluded_files: int
    review_files: int
    by_extension: dict[str, int]


class PolicyScanRequest(BaseModel):
    source_root: str = Field(..., min_length=1)
    limit: int = Field(default=50, ge=1, le=500)


class PolicyScanResponse(BaseModel):
    source_root: str
    scanned_at: datetime
    stats: PolicyScanStats
    candidates: list[PolicyCandidateItem]


class PolicyPreviewRequest(BaseModel):
    source_path: str = Field(..., min_length=1)


class PolicyPreviewResponse(BaseModel):
    source_path: str
    file_name: str
    extension: str
    parse_method: str
    parser_status: str
    suspected_scanned: bool
    page_count: int | None = None
    raw_text_chars: int = 0
    clean_text_chars: int = 0
    text_preview: str = ""
    detected_titles: list[str]
    notes: list[str]
