from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.composition.ingestion import build_ingestion_service, build_pipeline, build_upload_service
from app.composition.knowledge import (
    build_knowledge_base_service,
    build_persistence_gateway,
    build_publication_service,
    build_query_capability,
    build_read_repository,
    build_write_repository,
)
from app.composition.online import (
    build_decision_service,
    build_policy_decision_application_service,
    build_rag_facade,
    build_rule_retrieval_service,
)
from app.infrastructure.filesystem.policy_file_service import PolicyFileService
from app.infrastructure.filesystem.upload_service import PolicyUploadService
from app.infrastructure.llm.embedding_client import GiteeEmbeddingClient
from app.infrastructure.llm.llm_client import LazyRagAnswerGenerator, RagAnswerGenerator
from app.infrastructure.ocr.tencent_ocr import PolicyOcrService
from app.infrastructure.persistence.repositories.knowledge_read_repository import (
    KnowledgeReadRepository,
)
from app.infrastructure.persistence.repositories.knowledge_write_repository import (
    KnowledgeWriteRepository,
)
from app.infrastructure.persistence.repositories.policy_persistence_gateway import (
    PolicyPersistenceGateway,
)
from app.interfaces.agent import FunctionCallingAdapter
from app.modules.ingestion.pipeline import (
    PolicyIngestionService,
    PolicyPipelineService,
)
from app.modules.knowledge import KnowledgeBaseQueryCapability, KnowledgePublicationService
from app.modules.knowledge.application.knowledge_base import KnowledgeBaseService
from app.modules.online.application.data_acquisition import (
    ChecklistDataProviderRegistry,
    InlineChecklistDataProvider,
    PolicyDataAcquisitionService,
)
from app.modules.online.application.decision import (
    RuleDrivenChecklistDecisionService,
)
from app.modules.online.application.policy_decision import PolicyDecisionApplicationService
from app.modules.online.application.rag_facade import RagApplicationFacade
from app.modules.online.application.rule_retrieval import PolicyRuleRetrievalService
from app.modules.online.domain.checklist import (
    CHECKLIST_SCENARIO_REGISTRY,
    COURT_EVALUATION_MATERIALS_SCENARIO,
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.shared.config import settings


class ApplicationContainer:
    """Composition Root，只负责装配端口、适配器与应用用例。"""

    def __init__(
        self,
        session: Session | None = None,
        *,
        scenario_registry: ChecklistScenarioRegistry | None = None,
        checklist_policy: RuleDrivenChecklistPolicy | None = None,
        data_provider_registry: ChecklistDataProviderRegistry | None = None,
        answer_service: RagAnswerGenerator | None = None,
    ) -> None:
        self.session = session
        self.scenario_registry = scenario_registry or CHECKLIST_SCENARIO_REGISTRY
        self.checklist_policy = checklist_policy or RuleDrivenChecklistPolicy()
        self._data_provider_registry = data_provider_registry
        self._answer_service = answer_service
        self._persistence_gateway: PolicyPersistenceGateway | None = None
        self._write_repository: KnowledgeWriteRepository | None = None
        self._read_repository: KnowledgeReadRepository | None = None
        self._rule_retrieval_service: PolicyRuleRetrievalService | None = None
        self._data_acquisition_service: PolicyDataAcquisitionService | None = None
        self._decision_service: RuleDrivenChecklistDecisionService | None = None
        self._decision_application_service: PolicyDecisionApplicationService | None = None
        self._knowledge_query: KnowledgeBaseQueryCapability | None = None
        self._rag_facade: RagApplicationFacade | None = None
        self._publication_service: KnowledgePublicationService | None = None
        self._pipeline_preview_service: PolicyPipelineService | None = None
        self._pipeline_ingest_service: PolicyPipelineService | None = None
        self._policy_upload_service: PolicyUploadService | None = None
        self._policy_ingestion_service: PolicyIngestionService | None = None
        self._knowledge_base_service: KnowledgeBaseService | None = None
        self._embedding_service: GiteeEmbeddingClient | None = None
        self._file_service: PolicyFileService | None = None
        self._ocr_service: PolicyOcrService | None = None

    def embedding_service(self) -> GiteeEmbeddingClient:
        if self._embedding_service is None:
            self._embedding_service = GiteeEmbeddingClient()
        return self._embedding_service

    def file_service(self) -> PolicyFileService:
        if self._file_service is None:
            self._file_service = PolicyFileService()
        return self._file_service

    def ocr_service(self) -> PolicyOcrService:
        if self._ocr_service is None:
            self._ocr_service = PolicyOcrService()
        return self._ocr_service

    def persistence_gateway(self) -> PolicyPersistenceGateway:
        if self.session is None:
            raise RuntimeError("当前能力需要数据库会话，但容器未提供 session。")
        if self._persistence_gateway is None:
            self._persistence_gateway = build_persistence_gateway(self.session)
        return self._persistence_gateway

    def knowledge_document_exists(self, document_id: int) -> bool:
        return self.persistence_gateway().document_exists(document_id)

    def knowledge_write_repository(self) -> KnowledgeWriteRepository:
        if self._write_repository is None:
            self._write_repository = build_write_repository(self.persistence_gateway())
        return self._write_repository

    def knowledge_read_repository(self) -> KnowledgeReadRepository:
        if self._read_repository is None:
            self._read_repository = build_read_repository(
                self.persistence_gateway(),
                embedding_service=self.embedding_service(),
            )
        return self._read_repository

    def knowledge_query_capability(self) -> KnowledgeBaseQueryCapability:
        if self._knowledge_query is None:
            self._knowledge_query = build_query_capability(self.knowledge_read_repository())
        return self._knowledge_query

    def rag_answer_service(self) -> RagAnswerGenerator:
        if self._answer_service is None:
            self._answer_service = RagAnswerGenerator()
        return self._answer_service

    def rag_application_facade(self) -> RagApplicationFacade:
        if self._rag_facade is None:
            if self._answer_service is not None:
                answer_generator = self._answer_service
            else:
                answer_generator = LazyRagAnswerGenerator(self.rag_answer_service)
            self._rag_facade = build_rag_facade(self.knowledge_query_capability(), answer_generator)
        return self._rag_facade

    def function_calling_adapter(self) -> FunctionCallingAdapter:
        return FunctionCallingAdapter(self.rag_application_facade())

    def checklist_data_provider_registry(self) -> ChecklistDataProviderRegistry:
        if self._data_provider_registry is None:
            provider = InlineChecklistDataProvider()
            registry = ChecklistDataProviderRegistry(default_provider=provider)
            registry.register(COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code, provider)
            self._data_provider_registry = registry
        return self._data_provider_registry

    def policy_rule_retrieval_service(self) -> PolicyRuleRetrievalService:
        if self._rule_retrieval_service is None:
            self._rule_retrieval_service = build_rule_retrieval_service(
                self.knowledge_query_capability(),
                scenario_registry=self.scenario_registry,
                checklist_policy=self.checklist_policy,
            )
        return self._rule_retrieval_service

    def policy_data_acquisition_service(self) -> PolicyDataAcquisitionService:
        if self._data_acquisition_service is None:
            self._data_acquisition_service = PolicyDataAcquisitionService(
                self.checklist_data_provider_registry()
            )
        return self._data_acquisition_service

    def checklist_decision_service(self) -> RuleDrivenChecklistDecisionService:
        if self._decision_service is None:
            self._decision_service = build_decision_service(
                self.knowledge_query_capability(),
                checklist_policy=self.checklist_policy,
                scenario_registry=self.scenario_registry,
                rule_retrieval_service=self.policy_rule_retrieval_service(),
                data_acquisition_service=self.policy_data_acquisition_service(),
            )
        return self._decision_service

    def policy_decision_application_service(self) -> PolicyDecisionApplicationService:
        if self._decision_application_service is None:
            self._decision_application_service = build_policy_decision_application_service(
                self.checklist_decision_service()
            )
        return self._decision_application_service

    def knowledge_publication_service(self) -> KnowledgePublicationService:
        if self._publication_service is None:
            self._publication_service = build_publication_service(
                self.persistence_gateway().session
            )
        return self._publication_service

    def policy_pipeline_preview_service(self) -> PolicyPipelineService:
        if self._pipeline_preview_service is None:
            self._pipeline_preview_service = build_pipeline(
                file_service=self.file_service(),
                ocr_service=self.ocr_service(),
            )
        return self._pipeline_preview_service

    def policy_pipeline_ingest_service(self) -> PolicyPipelineService:
        if self._pipeline_ingest_service is None:
            self._pipeline_ingest_service = build_pipeline(
                repository=self.knowledge_write_repository(),
                embedding_service=self.embedding_service(),
                file_service=self.file_service(),
                ocr_service=self.ocr_service(),
            )
        return self._pipeline_ingest_service

    def policy_upload_service(self) -> PolicyUploadService:
        if self._policy_upload_service is None:
            self._policy_upload_service = build_upload_service(
                Path(settings.policy_pipeline_workspace)
            )
        return self._policy_upload_service

    def policy_ingestion_service(self) -> PolicyIngestionService:
        if self._policy_ingestion_service is None:
            self._policy_ingestion_service = build_ingestion_service()
        return self._policy_ingestion_service

    def knowledge_base_service(self) -> KnowledgeBaseService:
        if self._knowledge_base_service is None:
            self._knowledge_base_service = build_knowledge_base_service(
                self.knowledge_read_repository()
            )
        return self._knowledge_base_service
