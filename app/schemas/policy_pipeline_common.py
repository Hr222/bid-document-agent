from typing import Literal

from pydantic import BaseModel, Field

PipelineStageName = Literal[
    "file_registration",
    "intake_validation",
    "format_normalization",
    "parse_routing",
    "document_parsing",
    "ocr_processing",
    "text_assembly",
    "ingest_guard",
    "text_cleaning",
    "section_splitting",
    "chunk_splitting",
    "embedding_generation",
    "chunk_persistence",
    "document_persistence",
]

PipelineStatus = Literal["pending", "skipped", "success", "failed"]
ParserStatus = Literal["parsed", "failed"]
DocumentFileType = Literal["docx", "pdf"]
ParseMethod = Literal["direct", "ocr", "mixed"]
BlockType = Literal["text", "table", "image", "page_break"]
BlockSource = Literal["direct", "ocr", "mixed"]


class PipelineStageResult(BaseModel):
    """单个流水线阶段的执行结果。"""

    stage: PipelineStageName = Field(description="阶段名称。")
    status: PipelineStatus = Field(description="阶段状态。")
    message: str = Field(description="阶段说明。")
