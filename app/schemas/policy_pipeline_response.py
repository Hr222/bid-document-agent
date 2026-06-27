from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.policy_pipeline_common import PipelineStageResult
from app.schemas.policy_pipeline_content import (
    ChunkSplitResult,
    PersistenceResult,
    SectionSplitResult,
)
from app.schemas.policy_pipeline_document import (
    CleanedTextResult,
    FormatNormalizationResult,
    IntakeValidationResult,
    ParseRoutingResult,
    ParsedTextResult,
    RegisteredFileInfo,
)


class PolicyPipelineResponse(BaseModel):
    """制度流水线响应。"""

    mode: Literal["preview", "ingest"] = Field(description="当前模式。")
    source_path: str = Field(description="源文件路径。")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="开始时间。")
    stages: list[PipelineStageResult] = Field(default_factory=list, description="阶段执行记录。")
    policy_name_guess: str | None = Field(default=None, description="猜测的制度名称。")
    derived_version_label: str | None = Field(default=None, description="推导出的版本标签。")
    registered_file: RegisteredFileInfo | None = Field(default=None, description="文件登记结果。")
    validation: IntakeValidationResult | None = Field(default=None, description="准入校验结果。")
    normalization: FormatNormalizationResult | None = Field(default=None, description="格式归一化结果。")
    parse_routing: ParseRoutingResult | None = Field(default=None, description="解析器选择结果。")
    parsed_text: ParsedTextResult | None = Field(default=None, description="全文解析结果。")
    cleaned_text: CleanedTextResult | None = Field(default=None, description="文本清洗结果。")
    section_result: SectionSplitResult | None = Field(default=None, description="章节拆分结果。")
    chunk_result: ChunkSplitResult | None = Field(default=None, description="切块结果。")
    persistence: PersistenceResult | None = Field(default=None, description="落库结果。")
