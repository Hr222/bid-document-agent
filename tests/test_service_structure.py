from app.services.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.services.retrieval import KnowledgeRetrievalService, RagAnswerService


def test_ingestion_services_are_exported_from_new_package() -> None:
    assert PolicyIngestionService.__name__ == "PolicyIngestionService"
    assert PolicyUploadService.__name__ == "PolicyUploadService"
    assert PolicyPipelineService.__name__ == "PolicyPipelineService"


def test_retrieval_services_are_exported_from_new_package() -> None:
    assert KnowledgeRetrievalService.__name__ == "KnowledgeRetrievalService"
    assert RagAnswerService.__name__ == "RagAnswerService"
