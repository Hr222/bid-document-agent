from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.retrieval import RetrievalSearchRequest, RetrievalSearchResponse


class RetrievalSearcher(Protocol):
    """抽象检索能力，便于复用现有检索服务或注入测试替身。"""

    def search(self, request: RetrievalSearchRequest) -> RetrievalSearchResponse: ...


@dataclass(slots=True, frozen=True)
class RuleRetrievalRequest:
    """统一承载规则获取阶段所需的检索条件。"""

    scenario_code: str
    top_k: int
    document_id: int | None
    include_history: bool
