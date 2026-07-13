from __future__ import annotations

from app.core.config import settings
from app.domain.policy import ChecklistEvaluationResult, ChecklistRulePack, ChecklistScenarioDefinition
from app.schemas.policy_decision import (
    PolicyDecisionChecklistResponse,
    PolicyDecisionDebugInfo,
    PolicyDecisionRequirementStatus,
)
from app.schemas.retrieval import AnswerCitation, RetrievalSearchResponse


class PolicyDecisionResponseBuilder:
    """统一组装材料核验接口的响应结构。"""

    def __init__(self, *, scenario: ChecklistScenarioDefinition, provider_name: str) -> None:
        self.scenario = scenario
        self.provider_name = provider_name

    def build_requirement_statuses_from_rule_pack(
        self,
        rule_pack: ChecklistRulePack,
    ) -> list[PolicyDecisionRequirementStatus]:
        """在规则证据不足时，仍返回当前已识别出的要求状态。"""
        return [
            PolicyDecisionRequirementStatus(
                field_key=item.definition.field_key,
                label=item.definition.label,
                rule_matched=item.rule_matched,
                submitted=False,
                matched_rule_keywords=list(item.matched_rule_keywords),
                matched_submission_items=[],
                matched_components=[],
                missing_components=[],
            )
            for item in rule_pack.requirements
        ]

    def build_requirement_statuses_from_evaluation(
        self,
        evaluation: ChecklistEvaluationResult,
    ) -> list[PolicyDecisionRequirementStatus]:
        """将核验结果转换成前端可直接消费的字段状态。"""
        return [
            PolicyDecisionRequirementStatus(
                field_key=item.evidence.definition.field_key,
                label=item.evidence.definition.label,
                rule_matched=item.evidence.rule_matched,
                submitted=item.submitted,
                matched_rule_keywords=list(item.evidence.matched_rule_keywords),
                matched_submission_items=list(item.matched_submission_items),
                matched_components=list(item.matched_components),
                missing_components=list(item.missing_components),
            )
            for item in evaluation.decisions
        ]

    def build_citations(self, search_response: RetrievalSearchResponse) -> list[AnswerCitation]:
        """截取命中片段并生成引用列表。"""
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

    def build_debug_info(
        self,
        *,
        search_response: RetrievalSearchResponse,
        rule_match_count: int,
        submitted_material_count: int,
    ) -> PolicyDecisionDebugInfo:
        """补充检索与判定阶段的调试信息。"""
        return PolicyDecisionDebugInfo(
            retrieval_query=self.scenario.retrieval_query,
            policy_category=self.scenario.policy_category,
            provider=self.provider_name,
            rule_hit_count=len(search_response.hits),
            matched_rule_requirement_count=rule_match_count,
            submitted_material_count=submitted_material_count,
            retrieval=search_response.debug,
        )

    def build_response(
        self,
        *,
        decision: str,
        reasoning: list[str],
        citations: list[AnswerCitation],
        used_fields: list[str],
        missing_fields: list[str],
        requirement_statuses: list[PolicyDecisionRequirementStatus],
        debug: PolicyDecisionDebugInfo,
    ) -> PolicyDecisionChecklistResponse:
        """输出最终的核验响应对象。"""
        return PolicyDecisionChecklistResponse(
            scenario_code=self.scenario.scenario_code,
            scenario_name=self.scenario.scenario_name,
            decision=decision,
            reasoning=reasoning,
            citations=citations,
            used_fields=used_fields,
            missing_fields=missing_fields,
            requirement_statuses=requirement_statuses,
            debug=debug,
        )
