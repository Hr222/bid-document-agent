"""Agent 应用能力的 Composition Root。"""

from app.infrastructure.llm.langchain_glm_adapter import LangChainGlmStructuredLlm
from app.infrastructure.llm.openai_client_factory import OpenAICompatibleClientFactory
from app.modules.agent.tender.ports.llm_port import StructuredLlmPort


def build_tender_structured_llm(
    client_factory: OpenAICompatibleClientFactory,
) -> StructuredLlmPort:
    """组装当前阶段使用的智谱 GLM 结构化 LLM 适配器。"""

    return LangChainGlmStructuredLlm(client_factory=client_factory)
