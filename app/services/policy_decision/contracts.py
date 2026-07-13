from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.policy_decision import PolicyDecisionChecklistRequest
from app.schemas.retrieval import RetrievalSearchRequest, RetrievalSearchResponse


class RetrievalSearcher(Protocol):
    """抽象检索能力，便于复用现有检索服务或测试替身。"""

    def search(self, request: RetrievalSearchRequest) -> RetrievalSearchResponse: ...


@dataclass(slots=True, frozen=True)
class ChecklistSubmissionPayload:
    """统一承载待核验的提交材料列表。"""

    submitted_materials: list[str]


class ChecklistDataProvider(Protocol):
    """抽象材料来源，允许后续接入 Agent 或外部表单。"""

    provider_name: str

    def collect(self, request: PolicyDecisionChecklistRequest) -> ChecklistSubmissionPayload: ...
