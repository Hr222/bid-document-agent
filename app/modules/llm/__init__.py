"""通用 LLM 能力模块。"""

from app.modules.llm.contracts import (
    ChatLlmPort,
    ChatLlmRequest,
    ChatLlmResult,
    StructuredLlmPort,
    StructuredLlmRequest,
    StructuredLlmResult,
)

__all__ = [
    "ChatLlmPort",
    "ChatLlmRequest",
    "ChatLlmResult",
    "StructuredLlmPort",
    "StructuredLlmRequest",
    "StructuredLlmResult",
]
