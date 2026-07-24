from pydantic import BaseModel, Field


class LlmChatRequest(BaseModel):
    """独立 LLM 单轮调用请求。"""

    message: str = Field(min_length=1, max_length=10_000)


class LlmUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class LlmChatResponse(BaseModel):
    """独立 LLM 单轮调用响应。"""

    answer: str
    model: str
    prompt_version: str
    usage: LlmUsage
