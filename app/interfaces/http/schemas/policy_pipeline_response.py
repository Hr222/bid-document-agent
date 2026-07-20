from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.interfaces.http.schemas.policy_pipeline_common import PipelineStageResult
from app.interfaces.http.schemas.policy_pipeline_content import (
    ChunkSplitResult,
    PersistenceResult,
    SectionSplitResult,
)
from app.interfaces.http.schemas.policy_pipeline_document import (
    CleanedTextResult,
    FormatNormalizationResult,
    IntakeValidationResult,
    ParsedTextResult,
    ParseRoutingResult,
    RegisteredFileInfo,
)


class PolicyPipelineResponse(BaseModel):
    mode: Literal["preview", "ingest"]
    source_path: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stages: list[PipelineStageResult] = Field(default_factory=list)
    policy_name_guess: str | None = None
    derived_version_label: str | None = None
    target_document_id: int | None = None
    registered_file: RegisteredFileInfo | None = None
    validation: IntakeValidationResult | None = None
    normalization: FormatNormalizationResult | None = None
    parse_routing: ParseRoutingResult | None = None
    parsed_text: ParsedTextResult | None = None
    cleaned_text: CleanedTextResult | None = None
    section_result: SectionSplitResult | None = None
    chunk_result: ChunkSplitResult | None = None
    persistence: PersistenceResult | None = None

__all__ = ["PolicyPipelineResponse"]
