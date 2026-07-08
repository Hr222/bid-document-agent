from app.services.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.services.policy_ingestion import PolicyIngestionService as CompatIngestionService
from app.services.policy_upload_service import (
    PolicyUploadService as CompatUploadService,
)
from app.services.rag_answer_service import RagAnswerService as CompatAnswerService
from app.services.retrieval import KnowledgeRetrievalService, RagAnswerService
from app.services.retrieval_service import (
    KnowledgeRetrievalService as CompatRetrievalService,
)


def test_ingestion_services_are_exported_from_new_package() -> None:
    # 新包路径应直接表达“这是入库链路能力”，避免继续从 services 根目录散落导入。
    assert PolicyIngestionService is CompatIngestionService
    assert PolicyUploadService is CompatUploadService
    assert PolicyPipelineService.__name__ == "PolicyPipelineService"


def test_retrieval_services_keep_new_and_legacy_exports() -> None:
    # 检索主入口迁入 retrieval 包后，旧路径仍需可用，保证脚本和调用方兼容。
    assert KnowledgeRetrievalService is CompatRetrievalService
    assert RagAnswerService is CompatAnswerService
