from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

PipelineStageName = Literal[
    "file_registration",
    "intake_validation",
    "format_normalization",
    "parse_routing",
    "text_parsing",
    "text_cleaning",
    "section_splitting",
    "chunk_splitting",
    "embedding_generation",
    "chunk_persistence",
    "document_persistence",
]

PipelineStatus = Literal["pending", "skipped", "success", "failed"]
ParserStatus = Literal["parsed", "failed"]


class PipelineStageResult(BaseModel):
    """单个流水线阶段的执行结果。"""

    stage: PipelineStageName = Field(description="阶段名称。")
    status: PipelineStatus = Field(description="阶段状态。")
    message: str = Field(description="阶段说明。")


class PolicyPipelineRequest(BaseModel):
    """制度流水线请求。"""

    source_path: str = Field(..., min_length=1, description="源文件路径。")
    policy_category: str = Field(default="管理制度", min_length=1, description="资料分类。")
    responsible_department: str | None = Field(default=None, description="责任部门。")
    version_label: str | None = Field(default=None, description="手工指定的版本标签。")


class RegisteredFileInfo(BaseModel):
    """文件登记结果。"""

    source_path: str = Field(description="源文件路径。")
    file_name: str = Field(description="文件名。")
    extension: str = Field(description="文件扩展名。")
    size_bytes: int = Field(description="文件大小，单位字节。")
    sha256: str = Field(description="文件 SHA-256 摘要。")
    source_modified_at: datetime = Field(description="源文件最后修改时间。")


class IntakeValidationResult(BaseModel):
    """准入校验结果。"""

    is_allowed: bool = Field(description="是否允许进入流水线。")
    detected_file_kind: str = Field(description="识别出的文件类型。")
    needs_normalization: bool = Field(description="是否需要格式归一化。")
    recommended_parse_method: str = Field(description="建议的解析方式。")
    warnings: list[str] = Field(description="校验告警。")


class FormatNormalizationResult(BaseModel):
    """格式归一化结果。"""

    status: PipelineStatus = Field(description="归一化阶段状态。")
    source_path: str = Field(description="原始文件路径。")
    normalized_path: str = Field(description="归一化后的文件路径。")
    output_extension: str = Field(description="归一化后的扩展名。")
    converter: str = Field(description="使用的转换器。")
    message: str = Field(description="阶段说明。")


class ParseRoutingResult(BaseModel):
    """解析器选择结果。"""

    parser_name: str = Field(description="解析器名称。")
    parse_method: str = Field(description="解析方法。")
    suspected_scanned_pdf: bool = Field(description="是否预判为扫描 PDF。")
    notes: list[str] = Field(description="解析路由说明。")


class ParsedTextResult(BaseModel):
    """原文解析结果。"""

    parser_status: ParserStatus = Field(description="解析状态。")
    source_path: str = Field(description="解析的文件路径。")
    raw_text: str = Field(description="原始抽取文本。")
    page_count: int | None = Field(default=None, description="页数。")
    suspected_scanned: bool = Field(default=False, description="是否疑似扫描件。")
    paragraphs: list[str] = Field(description="抽取出的段落列表。")
    tables: list[str] = Field(description="抽取出的表格文本。")
    title_candidates: list[str] = Field(description="识别到的标题候选。")
    notes: list[str] = Field(description="解析补充说明。")


class CleanedTextResult(BaseModel):
    """文本清洗结果。"""

    clean_text: str = Field(description="清洗后的文本。")
    page_count: int | None = Field(default=None, description="页数。")
    removed_noise_examples: list[str] = Field(description="被移除的噪音示例。")
    notes: list[str] = Field(description="清洗说明。")


class PersistenceResult(BaseModel):
    """落库结果。"""

    persisted: bool = Field(description="是否已成功落库。")
    document_id: int | None = Field(default=None, description="制度主表 ID。")
    version_id: int | None = Field(default=None, description="版本表 ID。")
    version_seq: int | None = Field(default=None, description="版本序号。")
    version_label: str | None = Field(default=None, description="版本标签。")
    section_count: int = Field(default=0, description="落库的章节数量。")
    chunk_count: int = Field(default=0, description="落库的切块数量。")
    message: str = Field(description="落库说明。")


class SectionSplitItem(BaseModel):
    """单个章节项。"""

    section_no: str | None = Field(default=None, description="章节编号，如第一章、第一条。")
    section_title: str | None = Field(default=None, description="章节标题。")
    section_level: int = Field(description="章节层级。")
    section_path: str | None = Field(default=None, description="章节路径。")
    section_order: int = Field(description="章节顺序号。")
    section_text: str = Field(description="章节正文。")
    page_start: int | None = Field(default=None, description="起始页码。")
    page_end: int | None = Field(default=None, description="结束页码。")


class SectionSplitResult(BaseModel):
    """章节拆分结果。"""

    total_sections: int = Field(description="章节总数。")
    strategy: str = Field(description="使用的拆分策略。")
    sections: list[SectionSplitItem] = Field(description="章节列表。")
    notes: list[str] = Field(description="拆分说明。")


class ChunkItem(BaseModel):
    """单个检索切块。"""

    chunk_index: int = Field(description="当前版本内的全局切块序号。")
    section_order: int = Field(description="所属章节顺序号。")
    section_title: str | None = Field(default=None, description="所属章节标题。")
    section_path: str | None = Field(default=None, description="所属章节路径。")
    section_id: int | None = Field(default=None, description="所属章节 ID。")
    page_no: int | None = Field(default=None, description="页码。")
    chunk_text: str = Field(description="切块正文。")
    chunk_in_section: int = Field(description="在当前章节内的切块序号。")
    chunk_start_offset: int = Field(description="在章节文本内的起始偏移。")
    chunk_end_offset: int = Field(description="在章节文本内的结束偏移。")
    char_count: int = Field(description="字符数。")
    metadata: dict[str, Any] = Field(description="检索元数据。")
    embedding: list[float] | None = Field(default=None, description="文本向量。")


class ChunkSampleItem(BaseModel):
    """切块摘要样例。"""

    section_title: str | None = Field(default=None, description="所属章节标题。")
    section_path: str | None = Field(default=None, description="所属章节路径。")
    chunk_preview: str = Field(description="切块摘要预览。")
    char_count: int = Field(description="字符数。")


class ChunkSplitResult(BaseModel):
    """切块结果。"""

    total_chunks: int = Field(description="切块总数。")
    strategy: str = Field(description="使用的切块策略。")
    notes: list[str] = Field(description="切块说明。")
    chunks: list[ChunkItem] = Field(default_factory=list, description="完整切块列表。")
    sample_chunks: list[ChunkSampleItem] = Field(default_factory=list, description="切块样例列表。")


class PolicyPipelineResponse(BaseModel):
    """制度流水线响应。"""

    mode: Literal["preview", "ingest"] = Field(description="当前模式。")
    source_path: str = Field(description="源文件路径。")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="开始时间。")
    stages: list[PipelineStageResult] = Field(description="阶段执行记录。")
    policy_name_guess: str | None = Field(default=None, description="猜测的制度名称。")
    derived_version_label: str | None = Field(default=None, description="推导出的版本标签。")
    registered_file: RegisteredFileInfo | None = Field(default=None, description="文件登记结果。")
    validation: IntakeValidationResult | None = Field(default=None, description="准入校验结果。")
    normalization: FormatNormalizationResult | None = Field(default=None, description="格式归一化结果。")
    parse_routing: ParseRoutingResult | None = Field(default=None, description="解析器选择结果。")
    parsed_text: ParsedTextResult | None = Field(default=None, description="原文解析结果。")
    cleaned_text: CleanedTextResult | None = Field(default=None, description="文本清洗结果。")
    section_result: SectionSplitResult | None = Field(default=None, description="章节拆分结果。")
    chunk_result: ChunkSplitResult | None = Field(default=None, description="切块结果。")
    persistence: PersistenceResult | None = Field(default=None, description="落库结果。")
