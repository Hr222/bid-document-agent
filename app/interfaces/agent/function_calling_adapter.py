from __future__ import annotations

from app.interfaces.agent.contracts import AskKnowledgeToolArguments, FunctionCallingResult
from app.modules.online.application.rag_facade import RagApplicationFacade
from app.modules.online.contracts import AskKnowledgeCommand


class FunctionCallingAdapter:
    """向 LangChain/LangGraph 暴露稳定的工具调用入口。"""

    def __init__(self, facade: RagApplicationFacade) -> None:
        self.facade = facade

    def ask_knowledge(self, arguments: AskKnowledgeToolArguments) -> FunctionCallingResult:
        command = AskKnowledgeCommand(
            query=str(arguments.get("query", "")),
            top_k=int(arguments.get("top_k", 5)),
            policy_category=_optional_string(arguments.get("policy_category")),
            responsible_department=_optional_string(arguments.get("responsible_department")),
            document_id=_optional_int(arguments.get("document_id")),
            include_history=bool(arguments.get("include_history", False)),
        )
        result = self.facade.ask(command)
        return {
            "query": result.query,
            "answer": result.answer,
            "model": result.model,
            "citations": [
                {
                    "ref_no": item.ref_no,
                    "document_id": item.document_id,
                    "version_id": item.version_id,
                    "chunk_id": item.chunk_id,
                    "policy_name": item.policy_name,
                    "section_title": item.section_title,
                    "page_no": item.page_no,
                    "quote": item.quote,
                }
                for item in result.citations
            ],
        }


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
