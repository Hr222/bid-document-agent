from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

PipelineStageName = Literal[
    "file_registration",
    "intake_validation",
    "format_normalization",
    "parse_routing",
    "text_parsing",
    "text_cleaning",
    "section_splitting",
    "document_persistence",
]

PipelineStatus = Literal["pending", "skipped", "success", "failed"]
ParserStatus = Literal["parsed", "failed"]


class PipelineStageResult(BaseModel):
    """一次流水线阶段执行结果快照。"""

    stage: PipelineStageName
    status: PipelineStatus
    message: str


class PolicyPipelineRequest(BaseModel):
    """单文件制度入库流水线的 API 请求。"""

    source_path: str = Field(..., min_length=1)
    policy_category: str = Field(default="管理制度", min_length=1)
    responsible_department: str | None = None
    version_label: str | None = None


class RegisteredFileInfo(BaseModel):
    """步骤 1：文件登记结果。"""

    source_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256: str
    source_modified_at: datetime


class IntakeValidationResult(BaseModel):
    """步骤 2：文件是否允许进入流水线的校验结果。"""

    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class FormatNormalizationResult(BaseModel):
    """步骤 3：格式标准化结果。"""

    status: PipelineStatus
    source_path: str
    normalized_path: str
    output_extension: str
    converter: str
    message: str


class ParseRoutingResult(BaseModel):
    """步骤 4：解析器选择结果。"""

    parser_name: str
    parse_method: str
    suspected_scanned_pdf: bool
    notes: list[str]


class ParsedTextResult(BaseModel):
    """步骤 5：文本清洗前的原始抽取结果。"""

    parser_status: ParserStatus
    source_path: str
    raw_text: str
    page_count: int | None = None
    suspected_scanned: bool = False
    paragraphs: list[str]
    tables: list[str]
    title_candidates: list[str]
    notes: list[str]


class CleanedTextResult(BaseModel):
    """步骤 6：在尽量保留原意前提下得到的清洗文本。"""

    clean_text: str
    page_count: int | None = None
    removed_noise_examples: list[str]
    notes: list[str]


class PersistenceResult(BaseModel):
    """步骤 7：document/version/section 落库结果。"""

    persisted: bool
    document_id: int | None = None
    version_id: int | None = None
    version_seq: int | None = None
    version_label: str | None = None
    section_count: int = 0
    message: str


class SectionSplitItem(BaseModel):
    """拆分器为单个章/节/条节点生成的 section 对象。"""

    section_no: str | None = None
    section_title: str | None = None
    section_level: int
    section_path: str | None = None
    section_order: int
    section_text: str
    page_start: int | None = None
    page_end: int | None = None


class SectionSplitResult(BaseModel):
    """步骤 8：供后续落库使用的结构化章节结果。"""

    total_sections: int
    strategy: str
    sections: list[SectionSplitItem]
    notes: list[str]


class PolicyPipelineResponse(BaseModel):
    """单文件制度流水线的聚合响应。"""

    mode: Literal["preview", "ingest"]
    source_path: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stages: list[PipelineStageResult]
    policy_name_guess: str | None = None
    derived_version_label: str | None = None
    registered_file: RegisteredFileInfo | None = None
    validation: IntakeValidationResult | None = None
    normalization: FormatNormalizationResult | None = None
    parse_routing: ParseRoutingResult | None = None
    parsed_text: ParsedTextResult | None = None
    cleaned_text: CleanedTextResult | None = None
    section_result: SectionSplitResult | None = None
    persistence: PersistenceResult | None = None
