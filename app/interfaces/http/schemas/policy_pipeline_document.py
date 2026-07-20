from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.interfaces.http.schemas.policy_pipeline_common import (
    BlockSource,
    BlockType,
    DocumentFileType,
    ParseMethod,
    ParserStatus,
    PipelineStatus,
)


class PolicyPipelineRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    policy_category: str = Field(default="管理制度", min_length=1)
    responsible_department: str | None = None
    version_label: str | None = None
    target_document_id: int | None = Field(default=None, ge=1)


class RegisteredFileInfo(BaseModel):
    source_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256: str
    source_modified_at: datetime


class IntakeValidationResult(BaseModel):
    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class FormatNormalizationResult(BaseModel):
    status: PipelineStatus
    source_path: str
    normalized_path: str
    output_extension: str
    converter: str
    message: str


class ParseRoutingResult(BaseModel):
    parser_name: str
    parse_method: str
    suspected_scanned_pdf: bool
    notes: list[str]


class ParsedBlock(BaseModel):
    block_id: str
    order: int
    page_no: int | None = None
    block_type: BlockType
    source: BlockSource
    text: str | None = None
    layout_hint: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssembledLine(BaseModel):
    text: str
    page_no: int | None = None
    source_block_order: int | None = None


class ParsedDocumentResult(BaseModel):
    parser_status: ParserStatus
    source_path: str
    file_type: DocumentFileType
    suspected_scanned: bool = False
    blocks: list[ParsedBlock]
    notes: list[str]


class OcrProcessResult(BaseModel):
    applied: bool
    parse_method: ParseMethod
    blocks: list[ParsedBlock]
    notes: list[str]
    failed_blocks: int = 0


class ParsedTextResult(BaseModel):
    parser_status: ParserStatus
    source_path: str
    parse_method: ParseMethod
    raw_text: str
    page_count: int | None = None
    suspected_scanned: bool = False
    lines: list[AssembledLine] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    title_candidates: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CleanedTextResult(BaseModel):
    clean_text: str
    page_count: int | None = None
    lines: list[AssembledLine] = Field(default_factory=list)
    removed_noise_examples: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

__all__ = [
    "AssembledLine",
    "CleanedTextResult",
    "FormatNormalizationResult",
    "IntakeValidationResult",
    "OcrProcessResult",
    "ParseRoutingResult",
    "ParsedBlock",
    "ParsedDocumentResult",
    "ParsedTextResult",
    "PolicyPipelineRequest",
    "RegisteredFileInfo",
]
