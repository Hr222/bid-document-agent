from __future__ import annotations

from dataclasses import dataclass

from app.domain.policy import ChecklistRulePack, ChecklistScenarioDefinition
from app.schemas.retrieval import AnswerCitation, RetrievalDebugInfo, RetrievalHit


@dataclass(slots=True, frozen=True)
class RulePack:
    """统一承载规则层输出，供后续数据层与决策层复用。"""

    scenario: ChecklistScenarioDefinition
    original_query: str
    matched_rule_chunks: tuple[RetrievalHit, ...]
    citations: tuple[AnswerCitation, ...]
    retrieval_debug: RetrievalDebugInfo
    matched_requirement_count: int
    is_sufficient: bool
    insufficient_reason: str | None
    checklist_rule_pack: ChecklistRulePack

    @property
    def scenario_code(self) -> str:
        return self.scenario.scenario_code

    @property
    def scenario_name(self) -> str:
        return self.scenario.scenario_name

    @property
    def rule_hit_count(self) -> int:
        return len(self.matched_rule_chunks)
