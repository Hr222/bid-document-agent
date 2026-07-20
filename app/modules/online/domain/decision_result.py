from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.modules.knowledge.ports.read_port import KnowledgeQueryTrace
from app.modules.online.contracts import AnswerCitationResult


@dataclass(slots=True, frozen=True)
class DecisionReviewCommand:
    submitted_materials: tuple[str, ...] = ()
    top_k: int = 5
    document_id: int | None = None
    include_history: bool = False
    submitted_materials_provided: bool = True


@dataclass(slots=True, frozen=True)
class RequirementStatusResult:
    field_key: str
    label: str
    rule_matched: bool
    submitted: bool
    matched_rule_keywords: tuple[str, ...] = ()
    matched_submission_items: tuple[str, ...] = ()
    matched_components: tuple[str, ...] = ()
    missing_components: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class DataFieldTraceResult:
    field_key: str
    label: str
    source: str
    provided: bool
    value_count: int


@dataclass(slots=True, frozen=True)
class DataAcquisitionDebugResult:
    provider: str
    provided_input_fields: tuple[str, ...] = ()
    missing_input_fields: tuple[str, ...] = ()
    field_traces: tuple[DataFieldTraceResult, ...] = ()


@dataclass(slots=True, frozen=True)
class DecisionDebugResult:
    retrieval_query: str
    policy_category: str | None
    provider: str
    rule_hit_count: int
    matched_rule_requirement_count: int
    submitted_material_count: int
    data_acquisition: DataAcquisitionDebugResult
    retrieval_pipeline: str
    retrieval_strategy: str
    retrieval_min_score: float
    retrieval: tuple[KnowledgeQueryTrace, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class DecisionResult:
    scenario_code: str
    scenario_name: str
    decision: Literal["pass", "fail", "insufficient_evidence"]
    reasoning: tuple[str, ...]
    citations: tuple[AnswerCitationResult, ...]
    used_fields: tuple[str, ...]
    missing_input_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    requirement_statuses: tuple[RequirementStatusResult, ...]
    debug: DecisionDebugResult
