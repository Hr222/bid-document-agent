from __future__ import annotations

from typing import TypedDict


class AskKnowledgeToolArguments(TypedDict, total=False):
    """Agent 工具调用允许传入的参数。"""

    query: str
    top_k: int
    policy_category: str
    responsible_department: str
    document_id: int
    include_history: bool


class FunctionCallingResult(TypedDict):
    """Agent 工具调用统一返回的可序列化结果。"""

    query: str
    answer: str
    model: str | None
    citations: list[dict[str, object]]
