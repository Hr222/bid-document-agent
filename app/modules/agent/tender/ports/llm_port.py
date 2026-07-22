from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


@dataclass(slots=True, frozen=True)
class StructuredLlmRequest:
    """结构化 LLM 调用的应用层请求，不暴露具体模型 SDK。"""

    system_prompt: str
    user_prompt: str
    prompt_version: str


@dataclass(slots=True, frozen=True)
class StructuredLlmResult(Generic[StructuredModel]):
    """结构化 LLM 调用结果，保留模型和 Prompt 版本信息。"""

    value: StructuredModel
    model: str
    prompt_version: str


class StructuredLlmPort(Protocol):
    """招标书 Agent 应用依赖的结构化 LLM 能力端口。"""

    def invoke(
        self,
        request: StructuredLlmRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredLlmResult[StructuredModel]: ...
