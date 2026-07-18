from app.application import ApplicationContainer
from app.bridges import PolicyCapabilityBridge
from app.services.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.services.policy_data_acquisition import (
    ChecklistDataProviderRegistry,
    PolicyDataAcquisitionService,
)
from app.services.policy_rule_retrieval import PolicyRuleRetrievalService
from app.services.retrieval import KnowledgeRetrievalService, RagAnswerService


def test_ingestion_services_are_exported_from_new_package() -> None:
    assert PolicyIngestionService.__name__ == "PolicyIngestionService"
    assert PolicyUploadService.__name__ == "PolicyUploadService"
    assert PolicyPipelineService.__name__ == "PolicyPipelineService"


def test_retrieval_services_are_exported_from_new_package() -> None:
    assert KnowledgeRetrievalService.__name__ == "KnowledgeRetrievalService"
    assert RagAnswerService.__name__ == "RagAnswerService"


def test_rule_retrieval_services_are_exported_from_new_package() -> None:
    assert PolicyRuleRetrievalService.__name__ == "PolicyRuleRetrievalService"


def test_data_acquisition_services_are_exported_from_new_package() -> None:
    assert PolicyDataAcquisitionService.__name__ == "PolicyDataAcquisitionService"
    assert ChecklistDataProviderRegistry.__name__ == "ChecklistDataProviderRegistry"


def test_application_and_bridge_exports_are_available() -> None:
    assert ApplicationContainer.__name__ == "ApplicationContainer"
    assert PolicyCapabilityBridge.__name__ == "PolicyCapabilityBridge"
