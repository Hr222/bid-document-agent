from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.bridges import PolicyCapabilityBridge
from app.core.config import settings
from app.domain.policy import (
    CHECKLIST_SCENARIO_REGISTRY,
    COURT_EVALUATION_MATERIALS_SCENARIO,
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.repositories.policy_repository import PolicyRepository
from app.services.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.services.knowledge_base import KnowledgeBaseService
from app.services.policy_data_acquisition import (
    ChecklistDataProviderRegistry,
    InlineChecklistDataProvider,
    PolicyDataAcquisitionService,
)
from app.services.policy_decision import RuleDrivenChecklistDecisionService
from app.services.policy_rule_retrieval import PolicyRuleRetrievalService
from app.services.retrieval import KnowledgeRetrievalService, RagAnswerService


class ApplicationContainer:
    """统一收口当前阶段服务装配，避免路由层继续散落 new 依赖。"""

    def __init__(
        self,
        session: Session | None = None,
        *,
        scenario_registry: ChecklistScenarioRegistry | None = None,
        checklist_policy: RuleDrivenChecklistPolicy | None = None,
        data_provider_registry: ChecklistDataProviderRegistry | None = None,
        answer_service: RagAnswerService | None = None,
    ) -> None:
        self.session = session
        self.scenario_registry = scenario_registry or CHECKLIST_SCENARIO_REGISTRY
        self.checklist_policy = checklist_policy or RuleDrivenChecklistPolicy()
        self._data_provider_registry = data_provider_registry
        self._answer_service = answer_service

        self._repository: PolicyRepository | None = None
        self._retrieval_service: KnowledgeRetrievalService | None = None
        self._rule_retrieval_service: PolicyRuleRetrievalService | None = None
        self._data_acquisition_service: PolicyDataAcquisitionService | None = None
        self._decision_service: RuleDrivenChecklistDecisionService | None = None
        self._capability_bridge: PolicyCapabilityBridge | None = None
        self._knowledge_base_service: KnowledgeBaseService | None = None
        self._pipeline_preview_service: PolicyPipelineService | None = None
        self._pipeline_ingest_service: PolicyPipelineService | None = None
        self._policy_upload_service: PolicyUploadService | None = None
        self._policy_ingestion_service: PolicyIngestionService | None = None

    def policy_repository(self) -> PolicyRepository:
        """获取当前请求作用域下的仓储实例。"""
        if self.session is None:
            raise RuntimeError("当前能力需要数据库会话，但容器未提供 session。")
        if self._repository is None:
            self._repository = PolicyRepository(self.session)
        return self._repository

    def knowledge_retrieval_service(self) -> KnowledgeRetrievalService:
        """获取统一检索服务实例。"""
        if self._retrieval_service is None:
            self._retrieval_service = KnowledgeRetrievalService(self.policy_repository())
        return self._retrieval_service

    def rag_answer_service(self) -> RagAnswerService:
        """获取问答生成服务实例。"""
        if self._answer_service is None:
            self._answer_service = RagAnswerService()
        return self._answer_service

    def checklist_data_provider_registry(self) -> ChecklistDataProviderRegistry:
        """获取数据 Provider 注册点，并挂上当前默认 Provider。"""
        if self._data_provider_registry is None:
            provider = InlineChecklistDataProvider()
            registry = ChecklistDataProviderRegistry(
                default_provider=provider
            )
            registry.register(COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code, provider)
            self._data_provider_registry = registry
        return self._data_provider_registry

    def policy_rule_retrieval_service(self) -> PolicyRuleRetrievalService:
        """获取规则获取服务实例。"""
        if self._rule_retrieval_service is None:
            self._rule_retrieval_service = PolicyRuleRetrievalService(
                self.knowledge_retrieval_service(),
                scenario_registry=self.scenario_registry,
                checklist_policy=self.checklist_policy,
            )
        return self._rule_retrieval_service

    def policy_data_acquisition_service(self) -> PolicyDataAcquisitionService:
        """获取数据获取服务实例。"""
        if self._data_acquisition_service is None:
            self._data_acquisition_service = PolicyDataAcquisitionService(
                self.checklist_data_provider_registry()
            )
        return self._data_acquisition_service

    def checklist_decision_service(self) -> RuleDrivenChecklistDecisionService:
        """获取当前阶段的规则驱动判定服务实例。"""
        if self._decision_service is None:
            self._decision_service = RuleDrivenChecklistDecisionService(
                self.knowledge_retrieval_service(),
                decision_policy=self.checklist_policy,
                scenario_registry=self.scenario_registry,
                rule_retrieval_service=self.policy_rule_retrieval_service(),
                data_acquisition_service=self.policy_data_acquisition_service(),
            )
        return self._decision_service

    def policy_capability_bridge(self) -> PolicyCapabilityBridge:
        """获取对外桥接层实例。"""
        if self._capability_bridge is None:
            self._capability_bridge = PolicyCapabilityBridge(
                retrieval_service=self.knowledge_retrieval_service(),
                answer_service_factory=self.rag_answer_service,
                rule_retrieval_service=self.policy_rule_retrieval_service(),
                data_acquisition_service=self.policy_data_acquisition_service(),
                checklist_decision_service=self.checklist_decision_service(),
            )
        return self._capability_bridge

    def policy_pipeline_preview_service(self) -> PolicyPipelineService:
        """获取预览模式的入库流水线服务。"""
        if self._pipeline_preview_service is None:
            self._pipeline_preview_service = PolicyPipelineService()
        return self._pipeline_preview_service

    def policy_pipeline_ingest_service(self) -> PolicyPipelineService:
        """获取入库模式的流水线服务。"""
        if self._pipeline_ingest_service is None:
            self._pipeline_ingest_service = PolicyPipelineService(
                repository=self.policy_repository()
            )
        return self._pipeline_ingest_service

    def policy_upload_service(self) -> PolicyUploadService:
        """获取上传暂存服务。"""
        if self._policy_upload_service is None:
            self._policy_upload_service = PolicyUploadService(
                Path(settings.policy_pipeline_workspace)
            )
        return self._policy_upload_service

    def policy_ingestion_service(self) -> PolicyIngestionService:
        """获取扫描候选文件服务。"""
        if self._policy_ingestion_service is None:
            self._policy_ingestion_service = PolicyIngestionService()
        return self._policy_ingestion_service

    def knowledge_base_service(self) -> KnowledgeBaseService:
        """获取知识库轻量管理服务。"""
        if self._knowledge_base_service is None:
            repository = self.policy_repository() if self.session is not None else None
            self._knowledge_base_service = KnowledgeBaseService(repository=repository)
        return self._knowledge_base_service
