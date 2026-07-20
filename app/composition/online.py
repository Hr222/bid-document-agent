"""在线应用模块的 Composition Root，负责组装 RAG 外观和规则决策服务。"""

from __future__ import annotations

from app.modules.knowledge.application.query_capability import KnowledgeBaseQueryCapability
from app.modules.online.application.data_acquisition import PolicyDataAcquisitionService
from app.modules.online.application.decision import RuleDrivenChecklistDecisionService
from app.modules.online.application.policy_decision import PolicyDecisionApplicationService
from app.modules.online.application.rag_facade import RagApplicationFacade
from app.modules.online.application.rule_retrieval import PolicyRuleRetrievalService
from app.modules.online.domain.checklist import (
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.modules.online.ports import AnswerGenerator


def build_rag_facade(
    knowledge_query: KnowledgeBaseQueryCapability,
    answer_generator: AnswerGenerator,
) -> RagApplicationFacade:
    return RagApplicationFacade(
        knowledge_query=knowledge_query,
        answer_generator=answer_generator,
    )


def build_rule_retrieval_service(
    knowledge_query: KnowledgeBaseQueryCapability,
    *,
    scenario_registry: ChecklistScenarioRegistry,
    checklist_policy: RuleDrivenChecklistPolicy,
) -> PolicyRuleRetrievalService:
    return PolicyRuleRetrievalService(
        knowledge_query,
        scenario_registry=scenario_registry,
        checklist_policy=checklist_policy,
    )


def build_decision_service(
    knowledge_query: KnowledgeBaseQueryCapability,
    *,
    scenario_registry: ChecklistScenarioRegistry,
    checklist_policy: RuleDrivenChecklistPolicy,
    rule_retrieval_service: PolicyRuleRetrievalService,
    data_acquisition_service: PolicyDataAcquisitionService,
) -> RuleDrivenChecklistDecisionService:
    return RuleDrivenChecklistDecisionService(
        knowledge_query,
        decision_policy=checklist_policy,
        scenario_registry=scenario_registry,
        rule_retrieval_service=rule_retrieval_service,
        data_acquisition_service=data_acquisition_service,
    )


def build_policy_decision_application_service(
    decision_service: RuleDrivenChecklistDecisionService,
) -> PolicyDecisionApplicationService:
    return PolicyDecisionApplicationService(decision_service)
