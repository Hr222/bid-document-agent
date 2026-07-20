from __future__ import annotations

from app.modules.knowledge.ports.read_port import KnowledgeQueryResult
from app.modules.online.application.rag_facade import RagApplicationFacade
from app.modules.online.contracts import AnswerResult, AskKnowledgeCommand


class AskKnowledgeUseCase:
    """在线知识问答用例入口。"""

    def __init__(self, facade: RagApplicationFacade) -> None:
        self.facade = facade

    def execute(self, command: AskKnowledgeCommand) -> AnswerResult:
        """执行检索后问答链路。"""
        return self.facade.ask(command)

    def search(self, command: AskKnowledgeCommand) -> KnowledgeQueryResult:
        """只执行知识检索，不触发回答模型调用。"""
        return self.facade.search(command)
