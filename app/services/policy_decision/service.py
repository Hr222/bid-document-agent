from __future__ import annotations

from app.domain.policy import COURT_EVALUATION_MATERIALS_SCENARIO, RuleDrivenChecklistPolicy
from app.schemas.policy_decision import PolicyDecisionChecklistRequest, PolicyDecisionChecklistResponse
from app.schemas.retrieval import RetrievalSearchRequest
from app.services.policy_decision.contracts import ChecklistDataProvider, RetrievalSearcher
from app.services.policy_decision.providers import InlineChecklistDataProvider
from app.services.policy_decision.response_builder import PolicyDecisionResponseBuilder

INSUFFICIENT_EVIDENCE_REASONING = [
    "当前命中的规则片段不足以稳定提取完整申请材料清单。",
    "该场景应先确认规则依据，再继续做材料缺口判断。",
]


class RuleDrivenChecklistDecisionService:
    """编排规则检索与材料核验的应用服务。"""

    def __init__(
        self,
        retrieval_service: RetrievalSearcher,
        *,
        decision_policy: RuleDrivenChecklistPolicy | None = None,
        data_provider: ChecklistDataProvider | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.decision_policy = decision_policy or RuleDrivenChecklistPolicy()
        self.data_provider = data_provider or InlineChecklistDataProvider()
        self.scenario = COURT_EVALUATION_MATERIALS_SCENARIO

    def review_court_evaluation_materials(
        self,
        request: PolicyDecisionChecklistRequest,
    ) -> PolicyDecisionChecklistResponse:
        """核验法院委托评估机构申请材料是否满足制度要求。"""
        response_builder = PolicyDecisionResponseBuilder(
            scenario=self.scenario,
            provider_name=self.data_provider.provider_name,
        )
        search_response = self.retrieval_service.search(self._build_search_request(request))
        citations = response_builder.build_citations(search_response)
        rule_pack = self.decision_policy.build_rule_pack(
            scenario=self.scenario,
            rule_texts=[hit.chunk_text for hit in search_response.hits],
        )
        submission_payload = self.data_provider.collect(request)

        if not search_response.hits or not rule_pack.is_sufficient:
            return response_builder.build_response(
                decision="insufficient_evidence",
                reasoning=INSUFFICIENT_EVIDENCE_REASONING,
                citations=citations,
                used_fields=[],
                missing_fields=[],
                requirement_statuses=response_builder.build_requirement_statuses_from_rule_pack(
                    rule_pack
                ),
                debug=response_builder.build_debug_info(
                    search_response=search_response,
                    rule_match_count=rule_pack.matched_requirement_count,
                    submitted_material_count=len(submission_payload.submitted_materials),
                ),
            )

        evaluation = self.decision_policy.evaluate_submission(
            rule_pack=rule_pack,
            submitted_items=submission_payload.submitted_materials,
        )
        missing_fields = evaluation.missing_field_labels
        decision = "pass" if not missing_fields else "fail"

        return response_builder.build_response(
            decision=decision,
            reasoning=self._build_reasoning(
                matched_rule_requirement_count=rule_pack.matched_requirement_count,
                submitted_material_count=len(submission_payload.submitted_materials),
                missing_fields=missing_fields,
            ),
            citations=citations,
            used_fields=evaluation.used_field_labels,
            missing_fields=missing_fields,
            requirement_statuses=response_builder.build_requirement_statuses_from_evaluation(
                evaluation
            ),
            debug=response_builder.build_debug_info(
                search_response=search_response,
                rule_match_count=rule_pack.matched_requirement_count,
                submitted_material_count=len(submission_payload.submitted_materials),
            ),
        )

    def _build_search_request(
        self,
        request: PolicyDecisionChecklistRequest,
    ) -> RetrievalSearchRequest:
        """将场景固定检索语义与外部过滤条件组装为检索请求。"""
        return RetrievalSearchRequest(
            query=self.scenario.retrieval_query,
            top_k=request.top_k,
            policy_category=self.scenario.policy_category,
            document_id=request.document_id,
            include_history=request.include_history,
        )

    def _build_reasoning(
        self,
        *,
        matched_rule_requirement_count: int,
        submitted_material_count: int,
        missing_fields: list[str],
    ) -> list[str]:
        """生成面向接口返回的中文推理说明。"""
        reasoning = [
            f"已从命中的规则片段中识别出 {matched_rule_requirement_count} 项材料要求。",
            f"本次收到 {submitted_material_count} 项待核材料。",
        ]
        if missing_fields:
            reasoning.append(f"仍缺少 {len(missing_fields)} 项必要材料。")
        else:
            reasoning.append("当前必要材料已覆盖规则清单。")
        return reasoning
