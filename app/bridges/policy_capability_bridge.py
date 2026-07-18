from __future__ import annotations

from collections.abc import Callable

from app.schemas import (
    RagAskRequest,
    RagAskResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.schemas.policy_decision import (
    PolicyDecisionChecklistRequest,
    PolicyDecisionChecklistResponse,
)
from app.services.policy_data_acquisition import (
    ChecklistDataAcquisitionRequest,
    PolicyDataAcquisitionService,
)
from app.services.policy_decision import RuleDrivenChecklistDecisionService
from app.services.policy_rule_retrieval import (
    PolicyRuleRetrievalService,
    RulePack,
    RuleRetrievalRequest,
)
from app.services.retrieval import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    KnowledgeRetrievalService,
    RagAnswerService,
)


def _is_insufficient_evidence_answer(answer: str) -> bool:
    """统一收口“证据不足”回答判断，保持 API 与桥接层分支一致。"""
    normalized = answer.strip()
    return normalized == INSUFFICIENT_EVIDENCE_ANSWER or "足够依据" in normalized


class PolicyCapabilityBridge:
    """为后续 LangChain / LangGraph 暴露稳定能力接口的桥接层。"""

    def __init__(
        self,
        *,
        retrieval_service: KnowledgeRetrievalService,
        answer_service: RagAnswerService | None = None,
        answer_service_factory: Callable[[], RagAnswerService] | None = None,
        rule_retrieval_service: PolicyRuleRetrievalService,
        data_acquisition_service: PolicyDataAcquisitionService,
        checklist_decision_service: RuleDrivenChecklistDecisionService,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.answer_service = answer_service
        self.answer_service_factory = answer_service_factory
        self.rule_retrieval_service = rule_retrieval_service
        self.data_acquisition_service = data_acquisition_service
        self.checklist_decision_service = checklist_decision_service

    def search(self, request: RetrievalSearchRequest) -> RetrievalSearchResponse:
        """对外暴露统一检索能力。"""
        return self.retrieval_service.search(request)

    def ask(self, request: RagAskRequest) -> RagAskResponse:
        """先复用 search，再决定是否进入答案生成，避免链路分叉。"""
        search_response = self.search(
            RetrievalSearchRequest(
                query=request.query,
                top_k=request.top_k,
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                document_id=request.document_id,
                include_history=request.include_history,
            )
        )
        if not search_response.hits:
            return RagAskResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                model=None,
                citations=[],
                hits=[],
                debug=search_response.debug,
            )

        answer_response = self._get_answer_service().answer(
            query=request.query,
            hits=search_response.hits,
        )
        if _is_insufficient_evidence_answer(answer_response.answer):
            return answer_response.model_copy(
                update={"citations": [], "hits": [], "debug": search_response.debug}
            )
        return answer_response.model_copy(update={"debug": search_response.debug})

    def retrieve_rule_pack(self, request: RuleRetrievalRequest) -> RulePack:
        """对外暴露规则获取能力，供后续编排层直接复用。"""
        return self.rule_retrieval_service.retrieve_rule_pack(request)

    def acquire_checklist_data(self, request: ChecklistDataAcquisitionRequest):
        """对外暴露数据获取能力，保持规则层与数据层彼此独立。"""
        return self.data_acquisition_service.acquire_checklist_data(request)

    def review_court_evaluation_materials(
        self,
        request: PolicyDecisionChecklistRequest,
    ) -> PolicyDecisionChecklistResponse:
        """对外暴露当前 D1/D2/D3 PoC 的完整判定能力。"""
        return self.checklist_decision_service.review_court_evaluation_materials(request)

    def _get_answer_service(self) -> RagAnswerService:
        """延迟初始化问答生成器，避免在无须问答时提前触发配置校验。"""
        if self.answer_service is None:
            if self.answer_service_factory is None:
                raise RuntimeError("桥接层未配置可用的问答生成服务。")
            self.answer_service = self.answer_service_factory()
        return self.answer_service
