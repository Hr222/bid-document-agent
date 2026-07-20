from __future__ import annotations

from pathlib import Path

from app.infrastructure.filesystem.policy_file_service import PolicyFileService
from app.infrastructure.filesystem.upload_service import PolicyUploadService
from app.infrastructure.ocr.tencent_ocr import PolicyOcrService
from app.modules.ingestion import PolicyIngestionService, PolicyPipelineService
from app.modules.ingestion.ports import ChunkEmbeddingPort
from app.modules.knowledge.ports.write_port import KnowledgeWritePort


def build_pipeline(
    *,
    file_service: PolicyFileService,
    ocr_service: PolicyOcrService,
    repository: KnowledgeWritePort | None = None,
    embedding_service: ChunkEmbeddingPort | None = None,
) -> PolicyPipelineService:
    return PolicyPipelineService(
        repository=repository,
        embedding_service=embedding_service,
        file_service=file_service,
        ocr_service=ocr_service,
    )


def build_upload_service(workspace_root: Path) -> PolicyUploadService:
    return PolicyUploadService(workspace_root)


def build_ingestion_service() -> PolicyIngestionService:
    return PolicyIngestionService()
