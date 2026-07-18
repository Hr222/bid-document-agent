from __future__ import annotations

from app.core.config import settings
from app.domain.policy import ChecklistEvaluationResult, ChecklistRulePack, ChecklistScenarioDefinition
from app.schemas.policy_decision import (
    PolicyDecisionDataAcquisitionDebug,
    PolicyDecisionDataFieldTrace,
    PolicyDecisionChecklistResponse,
    PolicyDecisionDebugInfo,
    PolicyDecisionRequirementStatus,
)
from app.schemas.retrieval import AnswerCitation, RetrievalDebugInfo, RetrievalSearchResponse
from app.services.policy_data_acquisition.models import ChecklistDataPack


class PolicyDecisionResponseBuilder:
    """统一组装材料核验接口的响应结构。"""

    def __init__(self, *, scenario: ChecklistScenarioDefinition) -> None:
        self.scenario = scenario

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
        retrieval_debug: RetrievalDebugInfo,
        rule_hit_count: int,
        rule_match_count: int,
        data_pack: ChecklistDataPack,
    ) -> PolicyDecisionDebugInfo:
        """补充检索与判定阶段的调试信息。"""
        return PolicyDecisionDebugInfo(
            retrieval_query=self.scenario.retrieval_query,
            policy_category=self.scenario.policy_category,
            provider=data_pack.provider_name,
            rule_hit_count=rule_hit_count,
            matched_rule_requirement_count=rule_match_count,
            submitted_material_count=len(data_pack.submitted_materials),
            data_acquisition=self.build_data_acquisition_debug(data_pack),
            retrieval=retrieval_debug,
        )

    def build_data_acquisition_debug(
        self,
        data_pack: ChecklistDataPack,
    ) -> PolicyDecisionDataAcquisitionDebug:
        """将数据层 trace 转成接口调试对象。"""
        return PolicyDecisionDataAcquisitionDebug(
            provider=data_pack.provider_name,
            provided_input_fields=list(data_pack.provided_input_fields),
            missing_input_fields=list(data_pack.missing_input_fields),
            field_traces=[
                PolicyDecisionDataFieldTrace(
                    field_key=item.field_key,
                    label=item.label,
                    source=item.source,
                    provided=item.provided,
                    value_count=item.value_count,
                )
                for item in data_pack.field_traces
            ],
        )

    def build_response(
        self,
        *,
        decision: str,
        reasoning: list[str],
        citations: list[AnswerCitation],
        used_fields: list[str],
        missing_input_fields: list[str],
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
            missing_input_fields=missing_input_fields,
            missing_fields=missing_fields,
            requirement_statuses=requirement_statuses,
            debug=debug,
        )
