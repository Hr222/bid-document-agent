from __future__ import annotations

from typing import Protocol

from app.modules.knowledge.ports.read_port import KnowledgeSearchHit
from app.modules.online.contracts import AnswerResult


class AnswerGenerator(Protocol):
    """在线应用依赖的回答生成端口。"""

    def answer(self, *, query: str, hits: list[KnowledgeSearchHit]) -> AnswerResult: ...
