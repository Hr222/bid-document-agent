from __future__ import annotations

from app.modules.ingestion.contracts import PolicyPipelineRequest, PolicyPipelineResponse
from app.modules.ingestion.pipeline import PolicyPipelineService


class IngestionUseCase:
    """独立文档入库应用用例。"""

    def __init__(self, pipeline: PolicyPipelineService) -> None:
        self.pipeline = pipeline

    def preview(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        return self.pipeline.preview(request)

    def ingest(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        return self.pipeline.ingest(request)
