from __future__ import annotations

from app.core.config import settings
from app.domain.policy import (
    CHECKLIST_SCENARIO_REGISTRY,
    ChecklistScenarioDefinition,
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.schemas.retrieval import AnswerCitation, RetrievalSearchRequest, RetrievalSearchResponse
from app.services.policy_rule_retrieval.contracts import RetrievalSearcher, RuleRetrievalRequest
from app.services.policy_rule_retrieval.models import RulePack


class PolicyRuleRetrievalService:
    """面向业务场景消费检索能力，并输出统一规则包。"""

    def __init__(
        self,
        retrieval_service: RetrievalSearcher,
        *,
        scenario_registry: ChecklistScenarioRegistry | None = None,
        checklist_policy: RuleDrivenChecklistPolicy | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.scenario_registry = scenario_registry or CHECKLIST_SCENARIO_REGISTRY
        self.checklist_policy = checklist_policy or RuleDrivenChecklistPolicy()

    def retrieve_rule_pack(self, request: RuleRetrievalRequest) -> RulePack:
        """按场景编码获取规则证据，并收口成统一 RulePack。"""
        scenario = self.scenario_registry.get(request.scenario_code)
        search_response = self.retrieval_service.search(
            self._build_search_request(request=request, scenario=scenario)
        )
        checklist_rule_pack = self.checklist_policy.build_rule_pack(
            scenario=scenario,
            rule_texts=[hit.chunk_text for hit in search_response.hits],
        )
        insufficient_reason = self._build_insufficient_reason(
            search_response=search_response,
            matched_requirement_count=checklist_rule_pack.matched_requirement_count,
            min_rule_match_count=scenario.min_rule_match_count,
        )
        return RulePack(
            scenario=scenario,
            original_query=scenario.retrieval_query,
            matched_rule_chunks=tuple(search_response.hits),
            citations=tuple(self._build_citations(search_response)),
            retrieval_debug=search_response.debug,
            matched_requirement_count=checklist_rule_pack.matched_requirement_count,
            is_sufficient=checklist_rule_pack.is_sufficient,
            insufficient_reason=insufficient_reason,
            checklist_rule_pack=checklist_rule_pack,
        )

    def _build_search_request(
        self,
        *,
        request: RuleRetrievalRequest,
        scenario: ChecklistScenarioDefinition,
    ) -> RetrievalSearchRequest:
        """把场景自带的规则查询语义与外部过滤条件组装成检索请求。"""
        return RetrievalSearchRequest(
            query=scenario.retrieval_query,
            top_k=request.top_k,
            policy_category=scenario.policy_category,
            document_id=request.document_id,
            include_history=request.include_history,
        )

    def _build_citations(
        self,
        search_response: RetrievalSearchResponse,
    ) -> list[AnswerCitation]:
        """将命中的规则片段转成统一引用对象，避免决策层重复拼装。"""
        citations: list[AnswerCitation] = []
        for index, hit in enumerate(search_response.hits[: settings.rag_answer_top_k], start=1):
            citations.append(
                AnswerCitation(
                    ref_no=index,
                    document_id=hit.document_id,
                    version_id=hit.version_id,
                    chunk_id=hit.chunk_id,
                    policy_name=hit.policy_name,
                    section_title=hit.section_title,
                    page_no=hit.page_no,
                    quote=hit.chunk_text[: settings.rag_max_context_chars_per_chunk],
                )
            )
        return citations

    def _build_insufficient_reason(
        self,
        *,
        search_response: RetrievalSearchResponse,
        matched_requirement_count: int,
        min_rule_match_count: int,
    ) -> str | None:
        """统一收口规则证据不足的原因说明，便于后续继续透传。"""
        if not search_response.hits:
            return "当前未检索到可用于该场景判断的规则片段。"
        if matched_requirement_count < min_rule_match_count:
            return (
                "当前命中的规则片段不足以稳定提取完整规则清单，"
                f"仅识别出 {matched_requirement_count} 项要求，低于最小阈值 {min_rule_match_count}。"
            )
        return None
