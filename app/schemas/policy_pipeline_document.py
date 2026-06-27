from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.policy_pipeline_common import (
    BlockSource,
    BlockType,
    DocumentFileType,
    ParseMethod,
    ParserStatus,
    PipelineStatus,
)


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
    warnings: list[str] = Field(description="校验警告。")


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


class ParsedBlock(BaseModel):
    """文档中按顺序排列的原子内容块。"""

    block_id: str = Field(description="块唯一标识。")
    order: int = Field(description="块顺序号。")
    page_no: int | None = Field(default=None, description="页码。")
    block_type: BlockType = Field(description="块类型。")
    source: BlockSource = Field(description="当前块文本来源。")
    text: str | None = Field(default=None, description="块文本。")
    layout_hint: dict[str, Any] = Field(
        default_factory=dict,
        description="布局提示，例如坐标、尺寸或宿主段落信息。",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据。")


class AssembledLine(BaseModel):
    """组装后的单行文本及其来源信息。"""

    text: str = Field(description="行文本。")
    page_no: int | None = Field(default=None, description="来源页码。")
    source_block_order: int | None = Field(default=None, description="来源块顺序号。")


class ParsedDocumentResult(BaseModel):
    """结构化文档解析结果，供 OCR 和全文组装使用。"""

    parser_status: ParserStatus = Field(description="解析状态。")
    source_path: str = Field(description="解析的文件路径。")
    file_type: DocumentFileType = Field(description="文件类型。")
    suspected_scanned: bool = Field(default=False, description="是否疑似扫描件。")
    blocks: list[ParsedBlock] = Field(description="顺序块列表。")
    notes: list[str] = Field(description="解析补充说明。")


class OcrProcessResult(BaseModel):
    """OCR 处理阶段结果。"""

    applied: bool = Field(description="是否实际触发了 OCR。")
    parse_method: ParseMethod = Field(description="OCR 处理后的实际解析方式。")
    blocks: list[ParsedBlock] = Field(description="OCR 回填后的顺序块列表。")
    notes: list[str] = Field(description="OCR 处理说明。")
    failed_blocks: int = Field(default=0, description="OCR 失败块数量。")


class ParsedTextResult(BaseModel):
    """全文解析结果。"""

    parser_status: ParserStatus = Field(description="解析状态。")
    source_path: str = Field(description="解析的文件路径。")
    parse_method: ParseMethod = Field(description="实际解析方式。")
    raw_text: str = Field(description="原始组装文本。")
    page_count: int | None = Field(default=None, description="页数。")
    suspected_scanned: bool = Field(default=False, description="是否疑似扫描件。")
    lines: list[AssembledLine] = Field(default_factory=list, description="组装后的行列表。")
    paragraphs: list[str] = Field(default_factory=list, description="提取出的段落列表。")
    tables: list[str] = Field(default_factory=list, description="提取出的表格文本。")
    title_candidates: list[str] = Field(default_factory=list, description="识别到的标题候选。")
    notes: list[str] = Field(default_factory=list, description="解析补充说明。")


class CleanedTextResult(BaseModel):
    """文本清洗结果。"""

    clean_text: str = Field(description="清洗后的文本。")
    page_count: int | None = Field(default=None, description="页数。")
    lines: list[AssembledLine] = Field(default_factory=list, description="清洗后的行列表。")
    removed_noise_examples: list[str] = Field(default_factory=list, description="被移除的噪音示例。")
    notes: list[str] = Field(default_factory=list, description="清洗说明。")
