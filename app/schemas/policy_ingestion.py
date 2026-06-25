from datetime import datetime

from pydantic import BaseModel, Field


class PolicyCandidateItem(BaseModel):
    """候选文件项。"""

    source_path: str = Field(description="文件完整路径。")
    relative_path: str = Field(description="相对扫描目录的路径。")
    file_name: str = Field(description="文件名。")
    extension: str = Field(description="文件扩展名。")
    size_bytes: int = Field(description="文件大小，单位字节。")
    sha256: str = Field(description="文件 SHA-256 摘要。")
    recommended_action: str = Field(description="建议动作，如 include、exclude、review。")
    parse_method: str = Field(description="建议解析方式。")
    suspected_scanned: bool = Field(description="是否疑似扫描件。")
    policy_name_guess: str = Field(description="根据文件名猜测的制度名称。")
    include_reason: str | None = Field(default=None, description="建议纳入的原因。")
    exclude_reason: str | None = Field(default=None, description="建议排除的原因。")


class PolicyScanStats(BaseModel):
    """目录扫描统计。"""

    total_files: int = Field(description="扫描到的文件总数。")
    included_files: int = Field(description="建议纳入的文件数。")
    excluded_files: int = Field(description="建议排除的文件数。")
    review_files: int = Field(description="建议人工复核的文件数。")
    by_extension: dict[str, int] = Field(description="按扩展名统计的文件数量。")


class PolicyScanRequest(BaseModel):
    """目录扫描请求。"""

    source_root: str = Field(..., min_length=1, description="待扫描目录。")
    limit: int = Field(default=50, ge=1, le=500, description="最多返回多少个候选文件。")


class PolicyScanResponse(BaseModel):
    """目录扫描响应。"""

    source_root: str = Field(description="本次扫描的根目录。")
    scanned_at: datetime = Field(description="扫描时间。")
    stats: PolicyScanStats = Field(description="扫描统计信息。")
    candidates: list[PolicyCandidateItem] = Field(description="候选文件列表。")
