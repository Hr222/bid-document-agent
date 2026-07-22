from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.infrastructure.llm.langchain_glm_adapter import LangChainGlmStructuredLlm
from app.infrastructure.llm.openai_client_factory import OpenAICompatibleClientFactory
from app.modules.agent.tender.ports.llm_port import StructuredLlmRequest
from app.shared.config import Settings
from app.shared.exceptions import ServiceNotConfiguredError, UpstreamServiceError


class ProbeResult(BaseModel):
    status: str
    message: str


class FakeStructuredModel:
    def __init__(self, value: object) -> None:
        self.value = value
        self.messages: object | None = None

    def invoke(self, messages: object) -> object:
        self.messages = messages
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class FakeChatModel:
    def __init__(self, value: object) -> None:
        self.structured_model = FakeStructuredModel(value)
        self.output_schema: type[BaseModel] | None = None

    def with_structured_output(self, output_schema: type[BaseModel]) -> FakeStructuredModel:
        self.output_schema = output_schema
        return self.structured_model


def _request() -> StructuredLlmRequest:
    return StructuredLlmRequest(
        system_prompt="你是技术验证助手。",
        user_prompt="返回固定的结构化验证结果。",
        prompt_version="f1-llm-probe-v1",
    )


def test_langchain_glm_adapter_returns_validated_structured_result() -> None:
    fake_model = FakeChatModel({"status": "ok", "message": "GLM adapter ready"})
    adapter = LangChainGlmStructuredLlm(
        configuration=Settings(zhipu_chat_model="glm-test"),
        chat_model=fake_model,
    )

    result = adapter.invoke(_request(), ProbeResult)

    assert result.value == ProbeResult(status="ok", message="GLM adapter ready")
    assert result.model == "glm-test"
    assert result.prompt_version == "f1-llm-probe-v1"
    assert fake_model.output_schema is ProbeResult
    assert fake_model.structured_model.messages is not None


def test_langchain_glm_adapter_maps_model_failures() -> None:
    adapter = LangChainGlmStructuredLlm(
        configuration=Settings(zhipu_chat_model="glm-test"),
        chat_model=FakeChatModel(RuntimeError("provider unavailable")),
    )

    with pytest.raises(UpstreamServiceError, match="GLM 结构化调用失败"):
        adapter.invoke(_request(), ProbeResult)


def test_langchain_glm_adapter_rejects_missing_configuration() -> None:
    with pytest.raises(ServiceNotConfiguredError, match="ZHIPU_API_KEY"):
        LangChainGlmStructuredLlm(
            configuration=Settings(zhipu_api_key=None, zhipu_chat_model="glm-test"),
            client_factory=OpenAICompatibleClientFactory(
                configuration=Settings(zhipu_api_key=None, zhipu_chat_model="glm-test")
            ),
        )
