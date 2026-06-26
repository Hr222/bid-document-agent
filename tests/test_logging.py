import logging

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.policy_pipeline import ChunkItem
from app.services.step.policy_embedding import PolicyEmbeddingService


def test_http_request_logging_emits_access_log(caplog) -> None:
    with TestClient(app) as client:
        with caplog.at_level(logging.INFO):
            response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "HTTP request method=GET path=/api/v1/health" in caplog.text


class _FakeEmbeddingItem:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.data = [_FakeEmbeddingItem(embedding) for embedding in embeddings]


class _FakeEmbeddingsApi:
    def create(
        self,
        *,
        model: str,
        input: list[str],
        dimensions: int,
    ) -> _FakeEmbeddingResponse:
        return _FakeEmbeddingResponse(
            [[float(index + 1)] * dimensions for index, _ in enumerate(input)]
        )


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddingsApi()


def test_embedding_logging_emits_batch_details(caplog) -> None:
    chunks = [
        ChunkItem(
            chunk_index=index,
            section_order=0,
            section_title="section",
            section_path="section",
            chunk_text=f"chunk-{index}",
            chunk_in_section=index,
            chunk_start_offset=0,
            chunk_end_offset=7,
            char_count=7,
            metadata={},
        )
        for index in range(3)
    ]

    with caplog.at_level(logging.INFO):
        service = PolicyEmbeddingService(client=_FakeOpenAIClient())
        service.embed_chunks(chunks)

    assert "Embedding generation started total_chunks=3" in caplog.text
    assert "Embedding batch finished batch_index=1" in caplog.text
    assert "Embedding generation finished embedded_chunks=3" in caplog.text
