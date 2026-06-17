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
    "document_persistence",
    "section_splitting",
]

PipelineStatus = Literal["pending", "skipped", "success", "failed"]


class PipelineStageResult(BaseModel):
    """Execution snapshot for one pipeline stage."""

    stage: PipelineStageName
    status: PipelineStatus
    message: str


class PolicyPipelineRequest(BaseModel):
    """API request for running steps 1-8 of the policy ingestion pipeline."""

    source_path: str = Field(..., min_length=1)
    policy_category: str = Field(default="管理制度", min_length=1)
    responsible_department: str | None = None
    version_label: str | None = None


class RegisteredFileInfo(BaseModel):
    """Result of step 1: source file registration."""

    source_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256: str
    source_modified_at: datetime


class IntakeValidationResult(BaseModel):
    """Result of step 2: decide whether the file may enter the pipeline."""

    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class FormatNormalizationResult(BaseModel):
    """Result of step 3: convert legacy .doc into normalized .docx."""

    status: PipelineStatus
    source_path: str
    normalized_path: str
    output_extension: str
    converter: str
    message: str


class ParseRoutingResult(BaseModel):
    """Result of step 4: select the parser implementation."""

    parser_name: str
    parse_method: str
    suspected_scanned_pdf: bool
    notes: list[str]


class ParsedTextResult(BaseModel):
    """Result of step 5: raw extraction output before cleaning."""

    parser_status: PipelineStatus
    source_path: str
    raw_text: str
    page_count: int | None = None
    paragraphs: list[str]
    tables: list[str]
    title_candidates: list[str]
    notes: list[str]


class CleanedTextResult(BaseModel):
    """Result of step 6: cleaned text that still preserves source meaning."""

    clean_text: str
    page_count: int | None = None
    removed_noise_examples: list[str]
    notes: list[str]


class PersistenceResult(BaseModel):
    """Result of step 7: document/version persistence status."""

    persisted: bool
    document_id: int | None = None
    version_id: int | None = None
    version_seq: int | None = None
    version_label: str | None = None
    message: str


class SectionSplitItem(BaseModel):
    """Section object produced by the splitter for one chapter/article node."""

    section_no: str | None = None
    section_title: str | None = None
    section_level: int
    section_path: str | None = None
    section_order: int
    section_text: str
    page_start: int | None = None
    page_end: int | None = None
    metadata: dict[str, str | int | None] = Field(default_factory=dict)


class SectionSplitResult(BaseModel):
    """Result of step 8: structured sections for downstream chunking."""

    total_sections: int
    strategy: str
    sections: list[SectionSplitItem]
    notes: list[str]


class PolicyPipelineResponse(BaseModel):
    """Aggregated response for the first eight pipeline stages."""

    mode: Literal["preview", "ingest"]
    source_path: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stages: list[PipelineStageResult]
    registered_file: RegisteredFileInfo | None = None
    validation: IntakeValidationResult | None = None
    normalization: FormatNormalizationResult | None = None
    parse_routing: ParseRoutingResult | None = None
    parsed_text: ParsedTextResult | None = None
    cleaned_text: CleanedTextResult | None = None
    persistence: PersistenceResult | None = None
    section_result: SectionSplitResult | None = None
