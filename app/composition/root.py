from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.infrastructure.llm.embedding_client import GiteeEmbeddingClient
from app.infrastructure.llm.rag_answer_generator import LazyRagAnswerGenerator, RagAnswerGenerator
from app.infrastructure.persistence.repositories.knowledge_publication_repository import (
    KnowledgePublicationRepository,
)
from app.infrastructure.persistence.repositories.knowledge_read_repository import (
    KnowledgeReadRepository,
)
from app.infrastructure.persistence.repositories.knowledge_write_repository import (
    KnowledgeWriteRepository,
)
from app.infrastructure.persistence.repositories.policy_repository import PolicyRepository
from app.interfaces.agent import FunctionCallingAdapter
from app.modules.ingestion.pipeline import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.modules.knowledge import KnowledgeBaseQueryCapability, KnowledgePublicationService
from app.modules.knowledge.application.knowledge_base import KnowledgeBaseService
from app.modules.knowledge.retrieval import KnowledgeRetrievalService
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
from app.modules.online.domain.policy import (
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
        self._repository: PolicyRepository | None = None
        self._read_repository: KnowledgeReadRepository | None = None
        self._retrieval_service: KnowledgeRetrievalService | None = None
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

    def embedding_service(self) -> GiteeEmbeddingClient:
        if self._embedding_service is None:
            self._embedding_service = GiteeEmbeddingClient()
        return self._embedding_service

    def policy_repository(self) -> PolicyRepository:
        if self.session is None:
            raise RuntimeError("当前能力需要数据库会话，但容器未提供 session。")
        if self._repository is None:
            self._repository = PolicyRepository(self.session)
        return self._repository

    def knowledge_document_exists(self, document_id: int) -> bool:
        return self.policy_repository().document_exists(document_id)

    def knowledge_write_repository(self) -> KnowledgeWriteRepository:
        return KnowledgeWriteRepository(self.policy_repository().session)

    def knowledge_read_repository(self) -> KnowledgeReadRepository:
        if self._read_repository is None:
            self._read_repository = KnowledgeReadRepository(
                self.policy_repository(),
                embedding_service=self.embedding_service(),
            )
        return self._read_repository

    def knowledge_retrieval_service(self) -> KnowledgeRetrievalService:
        if self._retrieval_service is None:
            self._retrieval_service = KnowledgeRetrievalService(self.policy_repository())
        return self._retrieval_service

    def knowledge_query_capability(self) -> KnowledgeBaseQueryCapability:
        if self._knowledge_query is None:
            self._knowledge_query = KnowledgeBaseQueryCapability(self.knowledge_read_repository())
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
            self._rag_facade = RagApplicationFacade(
                knowledge_query=self.knowledge_query_capability(),
                answer_generator=answer_generator,
            )
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
            self._rule_retrieval_service = PolicyRuleRetrievalService(
                self.knowledge_retrieval_service(),
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
            self._decision_service = RuleDrivenChecklistDecisionService(
                self.knowledge_retrieval_service(),
                decision_policy=self.checklist_policy,
                scenario_registry=self.scenario_registry,
                rule_retrieval_service=self.policy_rule_retrieval_service(),
                data_acquisition_service=self.policy_data_acquisition_service(),
            )
        return self._decision_service

    def policy_decision_application_service(self) -> PolicyDecisionApplicationService:
        if self._decision_application_service is None:
            self._decision_application_service = PolicyDecisionApplicationService(
                self.checklist_decision_service()
            )
        return self._decision_application_service

    def knowledge_publication_service(self) -> KnowledgePublicationService:
        if self._publication_service is None:
            self._publication_service = KnowledgePublicationService(
                KnowledgePublicationRepository(self.policy_repository().session)
            )
        return self._publication_service

    def policy_pipeline_preview_service(self) -> PolicyPipelineService:
        if self._pipeline_preview_service is None:
            self._pipeline_preview_service = PolicyPipelineService()
        return self._pipeline_preview_service

    def policy_pipeline_ingest_service(self) -> PolicyPipelineService:
        if self._pipeline_ingest_service is None:
            self._pipeline_ingest_service = PolicyPipelineService(
                repository=self.knowledge_write_repository(),
                embedding_service=self.embedding_service(),
            )
        return self._pipeline_ingest_service

    def policy_upload_service(self) -> PolicyUploadService:
        if self._policy_upload_service is None:
            self._policy_upload_service = PolicyUploadService(
                Path(settings.policy_pipeline_workspace)
            )
        return self._policy_upload_service

    def policy_ingestion_service(self) -> PolicyIngestionService:
        if self._policy_ingestion_service is None:
            self._policy_ingestion_service = PolicyIngestionService()
        return self._policy_ingestion_service

    def knowledge_base_service(self) -> KnowledgeBaseService:
        if self._knowledge_base_service is None:
            self._knowledge_base_service = KnowledgeBaseService(
                read_port=self.knowledge_read_repository()
            )
        return self._knowledge_base_service
