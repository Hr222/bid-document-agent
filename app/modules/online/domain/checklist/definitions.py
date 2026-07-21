from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ChecklistRequirementComponent:
    """组成单项材料要求的最小匹配单元。"""

    label: str
    aliases: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ChecklistRequirementDefinition:
    """描述一项材料要求的字段名、展示名与匹配关键词。"""

    field_key: str
    label: str
    components: tuple[ChecklistRequirementComponent, ...]
    evidence_keywords: tuple[str, ...]
    required: bool = True


@dataclass(slots=True, frozen=True)
class ChecklistScenarioDefinition:
    """定义某个核验场景的检索语义与要求清单。"""

    scenario_code: str
    scenario_name: str
    retrieval_query: str
    policy_category: str | None
    requirements: tuple[ChecklistRequirementDefinition, ...]
    min_rule_match_count: int = 1
    input_field_key: str = "submitted_materials"
    input_field_label: str = "已提交材料列表"


@dataclass(slots=True, frozen=True)
class ChecklistRequirementEvidence:
    """记录单项要求在命中规则中的证据情况。"""

    definition: ChecklistRequirementDefinition
    matched_rule_keywords: tuple[str, ...]

    @property
    def rule_matched(self) -> bool:
        return bool(self.matched_rule_keywords)


@dataclass(slots=True, frozen=True)
class ChecklistRulePack:
    """将检索出的规则片段归并为当前场景的规则包。"""

    scenario: ChecklistScenarioDefinition
    requirements: tuple[ChecklistRequirementEvidence, ...]

    @property
    def matched_requirement_count(self) -> int:
        return sum(1 for item in self.requirements if item.rule_matched)

    @property
    def is_sufficient(self) -> bool:
        return self.matched_requirement_count >= self.scenario.min_rule_match_count


@dataclass(slots=True, frozen=True)
class ChecklistRequirementDecision:
    """记录单项材料在本次提交中的命中与缺失情况。"""

    evidence: ChecklistRequirementEvidence
    submitted: bool
    matched_submission_items: tuple[str, ...]
    matched_components: tuple[str, ...]
    missing_components: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ChecklistEvaluationResult:
    """汇总整份材料清单的核验结论。"""

    scenario: ChecklistScenarioDefinition
    decisions: tuple[ChecklistRequirementDecision, ...]

    @property
    def used_field_labels(self) -> list[str]:
        return [
            item.evidence.definition.label
            for item in self.decisions
            if item.evidence.rule_matched and item.submitted
        ]

    @property
    def missing_field_labels(self) -> list[str]:
        return [
            item.evidence.definition.label
            for item in self.decisions
            if item.evidence.rule_matched
            and item.evidence.definition.required
            and not item.submitted
        ]


class RuleDrivenChecklistPolicy:
    """基于规则片段抽取材料清单并完成提交核验。"""

    _normalize_pattern = re.compile(r"[\s\u3000()（）\[\]【】,，。:：;；、\-_]+")

    def build_rule_pack(
        self,
        *,
        scenario: ChecklistScenarioDefinition,
        rule_texts: list[str],
    ) -> ChecklistRulePack:
        """把命中的规则正文归并成结构化材料要求。"""
        normalized_rule_text = self._normalize_text("\n".join(rule_texts))
        requirement_evidences: list[ChecklistRequirementEvidence] = []
        for requirement in scenario.requirements:
            matched_keywords = tuple(
                keyword
                for keyword in requirement.evidence_keywords
                if self._normalize_text(keyword) in normalized_rule_text
            )
            requirement_evidences.append(
                ChecklistRequirementEvidence(
                    definition=requirement,
                    matched_rule_keywords=matched_keywords,
                )
            )

        return ChecklistRulePack(
            scenario=scenario,
            requirements=tuple(requirement_evidences),
        )

    def evaluate_submission(
        self,
        *,
        rule_pack: ChecklistRulePack,
        submitted_items: list[str],
    ) -> ChecklistEvaluationResult:
        """按照材料组件逐项核对本次提交是否完整。"""
        normalized_submitted_items = [
            (item.strip(), self._normalize_text(item))
            for item in submitted_items
            if item and item.strip()
        ]
        decisions: list[ChecklistRequirementDecision] = []
        for evidence in rule_pack.requirements:
            matched_submission_items: list[str] = []
            matched_components: list[str] = []
            missing_components: list[str] = []

            for component in evidence.definition.components:
                component_aliases = [self._normalize_text(alias) for alias in component.aliases]
                matched_raw_items = [
                    raw_item
                    for raw_item, normalized_item in normalized_submitted_items
                    if any(
                        alias in normalized_item or normalized_item in alias
                        for alias in component_aliases
                    )
                ]
                if matched_raw_items:
                    matched_components.append(component.label)
                    for raw_item in matched_raw_items:
                        if raw_item not in matched_submission_items:
                            matched_submission_items.append(raw_item)
                else:
                    missing_components.append(component.label)

            decisions.append(
                ChecklistRequirementDecision(
                    evidence=evidence,
                    submitted=evidence.rule_matched and not missing_components,
                    matched_submission_items=tuple(matched_submission_items),
                    matched_components=tuple(matched_components),
                    missing_components=tuple(missing_components),
                )
            )

        return ChecklistEvaluationResult(
            scenario=rule_pack.scenario,
            decisions=tuple(decisions),
        )

    def _normalize_text(self, value: str) -> str:
        """统一去掉空白与常见标点，降低别名匹配噪声。"""
        lowered = value.lower().strip()
        return self._normalize_pattern.sub("", lowered)


COURT_EVALUATION_MATERIALS_SCENARIO = ChecklistScenarioDefinition(
    # 该场景先以固定清单模式落地，后续可按同一结构扩展到更多制度核验场景。
    scenario_code="court-evaluation-materials-review",
    scenario_name="委托评估机构申请材料核验",
    retrieval_query="申请参与委托评估的机构应提交哪些资料",
    policy_category="收费标准",
    min_rule_match_count=8,
    requirements=(
        ChecklistRequirementDefinition(
            field_key="application_form_and_profile",
            label="申请书（登记表）及机构简介",
            components=(
                ChecklistRequirementComponent(
                    label="申请书或登记表",
                    aliases=("申请书", "登记表"),
                ),
                ChecklistRequirementComponent(
                    label="机构简介",
                    aliases=("机构简介",),
                ),
            ),
            evidence_keywords=("申请书", "登记表", "机构简介"),
        ),
        ChecklistRequirementDefinition(
            field_key="business_license_and_tax_registration",
            label="企业法人营业执照副本和税务登记证副本",
            components=(
                ChecklistRequirementComponent(
                    label="企业法人营业执照副本",
                    aliases=("企业法人营业执照副本", "营业执照副本", "营业执照"),
                ),
                ChecklistRequirementComponent(
                    label="税务登记证副本",
                    aliases=("税务登记证副本", "税务登记证"),
                ),
            ),
            evidence_keywords=("企业法人营业执照副本", "税务登记证副本"),
        ),
        ChecklistRequirementDefinition(
            field_key="institution_qualification",
            label="机构资质、资格证书副本",
            components=(
                ChecklistRequirementComponent(
                    label="机构资质、资格证书副本",
                    aliases=("机构资质", "资质证书副本", "资格证书副本"),
                ),
            ),
            evidence_keywords=("机构资质", "资格证书副本"),
        ),
        ChecklistRequirementDefinition(
            field_key="staff_roster_and_premises_proof",
            label="机构评估（审计）人员名单及其相关资质、机构营业场所证明资料",
            components=(
                ChecklistRequirementComponent(
                    label="评估（审计）人员名单",
                    aliases=("评估人员名单", "审计人员名单", "人员名单"),
                ),
                ChecklistRequirementComponent(
                    label="相关资质",
                    aliases=("相关资质", "人员资质", "人员资格"),
                ),
                ChecklistRequirementComponent(
                    label="机构营业场所证明资料",
                    aliases=("机构营业场所证明资料", "营业场所证明资料", "营业场所证明"),
                ),
            ),
            evidence_keywords=("人员名单", "相关资质", "营业场所证明资料"),
        ),
        ChecklistRequirementDefinition(
            field_key="qualification_certificate_copy",
            label="资格证书副本",
            components=(
                ChecklistRequirementComponent(
                    label="资格证书副本",
                    aliases=("资格证书副本", "资格证书"),
                ),
            ),
            evidence_keywords=("资格证书副本",),
        ),
        ChecklistRequirementDefinition(
            field_key="capital_contribution_and_asset_details",
            label="注资证明及资产明细表",
            components=(
                ChecklistRequirementComponent(
                    label="注资证明",
                    aliases=("注资证明",),
                ),
                ChecklistRequirementComponent(
                    label="资产明细表",
                    aliases=("资产明细表", "资产明细"),
                ),
            ),
            evidence_keywords=("注资证明", "资产明细表"),
        ),
        ChecklistRequirementDefinition(
            field_key="tax_certificate",
            label="税务机关出具的纳税证明",
            components=(
                ChecklistRequirementComponent(
                    label="纳税证明",
                    aliases=("纳税证明",),
                ),
            ),
            evidence_keywords=("纳税证明",),
        ),
        ChecklistRequirementDefinition(
            field_key="other_court_required_materials",
            label="法院指定提交的其他资料",
            components=(
                ChecklistRequirementComponent(
                    label="法院指定提交的其他资料",
                    aliases=("法院指定提交的其他资料", "法院指定资料", "其他资料"),
                ),
            ),
            evidence_keywords=("法院指定提交的其他资料",),
        ),
    ),
)
