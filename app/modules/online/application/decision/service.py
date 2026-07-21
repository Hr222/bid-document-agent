from __future__ import annotations

from app.modules.online.application.data_acquisition import (
    ChecklistDataAcquisitionRequest,
    ChecklistDataProvider,
    ChecklistDataProviderRegistry,
    ChecklistInput,
    InlineChecklistDataProvider,
    PolicyDataAcquisitionService,
)
from app.modules.online.application.decision.result_builder import DecisionResultBuilder
from app.modules.online.application.rule_retrieval import (
    PolicyRuleRetrievalService,
    RetrievalSearcher,
    RuleRetrievalRequest,
)
from app.modules.online.domain.checklist import (
    CHECKLIST_SCENARIO_REGISTRY,
    ChecklistScenarioDefinition,
    ChecklistScenarioRegistry,
    RuleDrivenChecklistPolicy,
)
from app.modules.online.domain.decision_result import DecisionResult, DecisionReviewCommand


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
        self.rule_retrieval_service = rule_retrieval_service or PolicyRuleRetrievalService(
            retrieval_service,
            scenario_registry=self.scenario_registry,
            checklist_policy=self.decision_policy,
        )
        self.data_acquisition_service = data_acquisition_service or (
            self._build_data_acquisition_service(data_provider)
        )

    def review(self, command: DecisionReviewCommand) -> DecisionResult:
        scenario = self._resolve_scenario(command.scenario_code)
        builder = DecisionResultBuilder(scenario=scenario)
        rule_pack = self.rule_retrieval_service.retrieve_rule_pack(
            RuleRetrievalRequest(
                scenario_code=scenario.scenario_code,
                top_k=command.top_k,
                document_id=command.document_id,
                include_history=command.include_history,
            )
        )
        data_pack = self.data_acquisition_service.acquire_checklist_data(
            ChecklistDataAcquisitionRequest(
                scenario_code=scenario.scenario_code,
                checklist_request=ChecklistInput(
                    submitted_materials=command.submitted_materials,
                    provided_fields=(
                        frozenset({scenario.input_field_key})
                        if command.submitted_materials_provided
                        else frozenset()
                    ),
                ),
                input_field_key=scenario.input_field_key,
                input_field_label=scenario.input_field_label,
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
                reasoning=builder.build_rule_insufficient_reasoning(
                    rule_pack.insufficient_reason
                ),
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
                reasoning=builder.build_data_insufficient_reasoning(
                    data_pack.insufficient_reason
                ),
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
            reasoning=builder.build_reasoning(
                matched_requirement_count=rule_pack.matched_requirement_count,
                submitted_value_count=len(data_pack.submitted_materials),
                missing_fields=list(missing_fields),
            ),
            citations=rule_pack.citations,
            used_fields=tuple(evaluation.used_field_labels),
            missing_input_fields=(),
            missing_fields=missing_fields,
            requirement_statuses=builder.build_requirement_statuses_from_evaluation(evaluation),
            debug=debug,
        )

    def _resolve_scenario(self, scenario_code: str | None) -> ChecklistScenarioDefinition:
        normalized_code = (scenario_code or "").strip()
        if not normalized_code:
            return self.scenario_registry.default()
        return self.scenario_registry.get(normalized_code)

    def _build_data_acquisition_service(
        self,
        data_provider: ChecklistDataProvider | None,
    ) -> PolicyDataAcquisitionService:
        provider = data_provider or InlineChecklistDataProvider()
        registry = ChecklistDataProviderRegistry(default_provider=provider)
        for scenario in self.scenario_registry.list_all():
            registry.register(scenario.scenario_code, provider)
        return PolicyDataAcquisitionService(registry)
