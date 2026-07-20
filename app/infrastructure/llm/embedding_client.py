from __future__ import annotations

from math import ceil

from openai import OpenAI

from app.modules.ingestion.contracts import ChunkItem
from app.shared.config import settings
from app.shared.exceptions import UpstreamServiceError
from app.shared.logging import get_logger

logger = get_logger("app.infrastructure.embedding")


class GiteeEmbeddingClient:
    """Gitee embedding 技术适配器，同时支持查询向量和入库向量。"""

    def __init__(self, client: OpenAI | None = None) -> None:
        if client is not None:
            self.client = client
        else:
            if not settings.gitee_api_key:
                raise RuntimeError("执行向量生成前必须先配置 GITEE_API_KEY。")
            self.client = OpenAI(
                api_key=settings.gitee_api_key,
                base_url=settings.gitee_base_url,
                default_headers={"X-Failover-Enabled": "true"},
            )

    def embed_query(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ValueError("检索查询不能为空。")
        vectors = self._embed_texts([normalized])
        if len(vectors) != 1:
            raise RuntimeError("查询向量返回数量异常。")
        self._validate_dimension(vectors[0], "查询")
        return vectors[0]

    def embed_chunks(self, chunks: list[ChunkItem]) -> list[ChunkItem]:
        if not chunks:
            return []

        embedded: list[ChunkItem] = []
        batch_size = max(1, settings.embedding_batch_size)
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = self._embed_texts([item.chunk_text for item in batch])
            if len(vectors) != len(batch):
                raise RuntimeError("向量返回数量与切块数量不一致。")
            for chunk, vector in zip(batch, vectors, strict=True):
                self._validate_dimension(vector, "切块")
                embedded.append(chunk.model_copy(update={"embedding": vector}))
        logger.info(
            "向量生成完成 total_chunks=%s batch_size=%s total_batches=%s",
            len(embedded),
            batch_size,
            ceil(len(chunks) / batch_size),
        )
        return embedded

    def _validate_dimension(self, vector: list[float], subject: str) -> None:
        if len(vector) != settings.vector_dimensions:
            raise RuntimeError(
                f"{subject}向量维度不匹配：期望 {settings.vector_dimensions}，实际 {len(vector)}。"
            )

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
                dimensions=settings.vector_dimensions,
            )
        except Exception as exc:
            raise UpstreamServiceError(f"Gitee embedding 请求失败：{exc}") from exc
        return [item.embedding for item in response.data]
