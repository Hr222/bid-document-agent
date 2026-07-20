from __future__ import annotations

from app.modules.online.application.rag_facade import RagApplicationFacade
from app.modules.online.contracts import AnswerResult, AskKnowledgeCommand


class AskKnowledgeUseCase:
    """在线知识问答用例入口。"""

    def __init__(self, facade: RagApplicationFacade) -> None:
        self.facade = facade

    def execute(self, command: AskKnowledgeCommand) -> AnswerResult:
        return self.facade.ask(command)
