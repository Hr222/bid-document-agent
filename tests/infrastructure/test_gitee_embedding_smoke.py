from __future__ import annotations

import pytest
from click import echo
from openai import APIConnectionError, OpenAI

from app.shared.config import settings


@pytest.mark.skipif(
    not settings.gitee_api_key,
    reason="未配置 GITEE_API_KEY，跳过 Gitee embedding 在线验证。",
)
def test_gitee_embedding_qwen3_0_6b_matches_openapi_shape() -> None:
    client = OpenAI(
        api_key=settings.gitee_api_key,
        base_url=settings.gitee_base_url,
        default_headers={"X-Failover-Enabled": "true"},
    )

    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input="Today is a sunny day and I will get some ice cream.",
            dimensions=settings.vector_dimensions,
        )
    except APIConnectionError as exc:
        pytest.skip(f"Gitee embedding service unreachable in current environment: {exc}")

    echo(response.data)

    assert response.object == "list"
    assert response.model == settings.embedding_model
    assert isinstance(response.data, list)
    assert len(response.data) == 1

    item = response.data[0]
    assert item.object == "embedding"
    assert isinstance(item.embedding, list)
    assert len(item.embedding) == settings.vector_dimensions
    assert isinstance(item.index, int)

    usage = response.usage
    assert usage is not None
    assert isinstance(usage.prompt_tokens, int)
    assert isinstance(usage.total_tokens, int)
    assert usage.prompt_tokens >= 0
    assert usage.total_tokens >= usage.prompt_tokens
