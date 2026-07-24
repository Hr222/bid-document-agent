from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.infrastructure.llm.openai_client_factory import OpenAICompatibleClientFactory
from app.modules.llm.contracts import (
    StructuredLlmPort,
    StructuredLlmRequest,
    StructuredLlmResult,
)
from app.shared.config import Settings, settings
from app.shared.exceptions import ServiceNotConfiguredError, UpstreamServiceError


class LangChainGlmStructuredLlm(StructuredLlmPort):
    """使用智谱 GLM 的 OpenAI-compatible 接口执行 LangChain 结构化调用。"""

    def __init__(
        self,
        *,
        configuration: Settings = settings,
        client_factory: OpenAICompatibleClientFactory | None = None,
        chat_model: Any | None = None,
    ) -> None:
        self.model = configuration.zhipu_chat_model
        if chat_model is not None:
            self._chat_model = chat_model
            return

        if not configuration.zhipu_chat_model:
            raise ServiceNotConfiguredError(
                "未配置 ZHIPU_CHAT_MODEL，无法执行 Agent LLM 调用。"
            )
        if client_factory is None:
            raise RuntimeError(
                "LangChain GLM Adapter 必须由 Composition Root 注入 Client Factory。"
            )
        self._client_factory = client_factory
        self._chat_model = self._client_factory.create_chat_model(
            model=configuration.zhipu_chat_model
        )

    def invoke(
        self,
        request: StructuredLlmRequest,
        output_schema: type[BaseModel],
    ) -> StructuredLlmResult[BaseModel]:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", request.system_prompt),
                ("human", request.user_prompt),
            ]
        )

        try:
            structured_model = self._chat_model.with_structured_output(output_schema)
            raw_value = structured_model.invoke(prompt.format_messages())
            value = (
                raw_value
                if isinstance(raw_value, output_schema)
                else output_schema.model_validate(raw_value)
            )
        except Exception as exc:
            raise UpstreamServiceError(
                f"GLM 结构化调用失败（Prompt 版本：{request.prompt_version}）：{exc}"
            ) from exc

        return StructuredLlmResult(
            value=value,
            model=self.model or "unknown",
            prompt_version=request.prompt_version,
        )
