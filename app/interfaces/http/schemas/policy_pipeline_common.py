from typing import Literal

from pydantic import BaseModel

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
DocumentFileType = Literal["docx", "pdf", "image"]
ParseMethod = Literal["direct", "ocr", "mixed"]
BlockType = Literal["text", "table", "image", "page_break"]
BlockSource = Literal["direct", "ocr", "mixed"]


class PipelineStageResult(BaseModel):
    stage: PipelineStageName
    status: PipelineStatus
    message: str

__all__ = [
    "BlockSource",
    "BlockType",
    "DocumentFileType",
    "ParseMethod",
    "ParserStatus",
    "PipelineStageName",
    "PipelineStageResult",
    "PipelineStatus",
]
