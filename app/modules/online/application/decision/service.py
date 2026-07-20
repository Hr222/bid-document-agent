from __future__ import annotations

from app.modules.online.application.data_acquisition import (
    ChecklistDataAcquisitionRequest,
    ChecklistDataProvider,
    ChecklistDataProviderRegistry,
    ChecklistInput,
    InlineChecklistDataProvider,
    PolicyDataAcquisitionService,
)
from app.modules.online.application.decision.result_builder import PolicyDecisionResultBuilder
from app.modules.online.application.rule_retrieval import (
    PolicyRuleRetrievalService,
    RetrievalSearcher,
    RuleRetrievalRequest,
)
from app.modules.online.domain.checklist import (
    CHECKLIST_SCENARIO_REGISTRY,
    COURT_EVALUATION_MATERIALS_SCENARIO,
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.modules.online.domain.decision_result import DecisionResult, DecisionReviewCommand

INSUFFICIENT_EVIDENCE_REASONING = [
    "当前命中的规则片段不足以稳定提取完整申请材料清单。",
    "该场景应先确认规则依据，再继续做材料缺口判断。",
]
INSUFFICIENT_DATA_REASONING_PREFIX = "当前业务输入不足，暂时无法稳定完成材料核验。"


class RuleDrivenChecklistDecisionService:
    """编排规则检索、材料采集和领域评估，输出在线应用层结果。"""

    def __init__(
        self,
        retrieval_service: RetrievalSearcher,
        *,
        decision_policy: RuleDrivenChecklistPolicy | None = None,
        data_provider: ChecklistDataProvider | None = None,
        scenario_registry: ChecklistScenarioRegistry | None = None,
        rule_retrieval_service: PolicyRuleRetrievalService | None = None,
        data_acquisition_service: PolicyDataAcquisitionService | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.decision_policy = decision_policy or RuleDrivenChecklistPolicy()
        self.scenario_registry = scenario_registry or CHECKLIST_SCENARIO_REGISTRY
        self.scenario = self.scenario_registry.get(
            COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code
        )
        self.rule_retrieval_service = rule_retrieval_service or PolicyRuleRetrievalService(
            retrieval_service,
            scenario_registry=self.scenario_registry,
            checklist_policy=self.decision_policy,
        )
        self.data_acquisition_service = data_acquisition_service or (
            self._build_data_acquisition_service(data_provider)
        )

    def review(self, command: DecisionReviewCommand) -> DecisionResult:
        builder = PolicyDecisionResultBuilder(scenario=self.scenario)
        rule_pack = self.rule_retrieval_service.retrieve_rule_pack(
            RuleRetrievalRequest(
                scenario_code=self.scenario.scenario_code,
                top_k=command.top_k,
                document_id=command.document_id,
                include_history=command.include_history,
            )
        )
        data_pack = self.data_acquisition_service.acquire_checklist_data(
            ChecklistDataAcquisitionRequest(
                scenario_code=self.scenario.scenario_code,
                checklist_request=ChecklistInput(
                    submitted_materials=command.submitted_materials,
                    provided_fields=(
                        frozenset({"submitted_materials"})
                        if command.submitted_materials_provided
                        else frozenset()
                    ),
                ),
            )
        )
        debug = builder.build_debug_info(
            retrieval_debug=rule_pack.retrieval_debug,
            retrieval_pipeline=rule_pack.retrieval_pipeline,
            retrieval_strategy=rule_pack.retrieval_strategy,
            retrieval_min_score=rule_pack.retrieval_min_score,
            rule_hit_count=rule_pack.rule_hit_count,
            rule_match_count=rule_pack.matched_requirement_count,
            data_pack=data_pack,
        )
        requirement_statuses = builder.build_requirement_statuses_from_rule_pack(
            rule_pack.checklist_rule_pack
        )

        if not rule_pack.is_sufficient:
            return builder.build_response(
                decision="insufficient_evidence",
                reasoning=self._build_rule_insufficient_reasoning(rule_pack.insufficient_reason),
                citations=rule_pack.citations,
                used_fields=(),
                missing_input_fields=tuple(data_pack.missing_input_fields),
                missing_fields=(),
                requirement_statuses=requirement_statuses,
                debug=debug,
            )

        if not data_pack.is_sufficient:
            return builder.build_response(
                decision="insufficient_evidence",
                reasoning=self._build_data_insufficient_reasoning(data_pack.insufficient_reason),
                citations=rule_pack.citations,
                used_fields=(),
                missing_input_fields=tuple(data_pack.missing_input_fields),
                missing_fields=(),
                requirement_statuses=requirement_statuses,
                debug=debug,
            )

        evaluation = self.decision_policy.evaluate_submission(
            rule_pack=rule_pack.checklist_rule_pack,
            submitted_items=list(data_pack.submitted_materials),
        )
        missing_fields = tuple(evaluation.missing_field_labels)
        decision = "pass" if not missing_fields else "fail"
        return builder.build_response(
            decision=decision,
            reasoning=self._build_reasoning(
                matched_rule_requirement_count=rule_pack.matched_requirement_count,
                submitted_material_count=len(data_pack.submitted_materials),
                missing_fields=list(missing_fields),
            ),
            citations=rule_pack.citations,
            used_fields=tuple(evaluation.used_field_labels),
            missing_input_fields=(),
            missing_fields=missing_fields,
            requirement_statuses=builder.build_requirement_statuses_from_evaluation(evaluation),
            debug=debug,
        )

    def _build_reasoning(
        self,
        *,
        matched_rule_requirement_count: int,
        submitted_material_count: int,
        missing_fields: list[str],
    ) -> list[str]:
        reasoning = [
            f"已从命中的规则片段中识别出 {matched_rule_requirement_count} 项材料要求。",
            f"本次收到 {submitted_material_count} 项待核材料。",
        ]
        reasoning.append(
            f"仍缺少 {len(missing_fields)} 项必要材料。"
            if missing_fields
            else "当前必要材料已覆盖规则清单。"
        )
        return reasoning

    def _build_rule_insufficient_reasoning(self, insufficient_reason: str | None) -> list[str]:
        reasoning = list(INSUFFICIENT_EVIDENCE_REASONING)
        if insufficient_reason:
            reasoning.insert(1, insufficient_reason)
        return reasoning

    def _build_data_insufficient_reasoning(self, insufficient_reason: str | None) -> list[str]:
        reasoning = [INSUFFICIENT_DATA_REASONING_PREFIX]
        if insufficient_reason:
            reasoning.append(insufficient_reason)
        reasoning.append("请先补齐必要输入字段后，再继续做规则驱动核验。")
        return reasoning

    def _build_data_acquisition_service(
        self,
        data_provider: ChecklistDataProvider | None,
    ) -> PolicyDataAcquisitionService:
        provider = data_provider or InlineChecklistDataProvider()
        registry = ChecklistDataProviderRegistry(default_provider=provider)
        registry.register(self.scenario.scenario_code, provider)
        return PolicyDataAcquisitionService(registry)
