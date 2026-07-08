from __future__ import annotations

from math import ceil

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas import ChunkItem
from app.services.exceptions import UpstreamServiceError

logger = get_logger("app.embedding.policy")


class PolicyEmbeddingService:
    """负责流水线步骤 12：为 chunk 批量生成向量。"""

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

    def embed_chunks(self, chunks: list[ChunkItem]) -> list[ChunkItem]:
        """
        步骤 12：按批次调用 embedding，并校验返回向量维度。
        这里只负责生成向量，不负责落库；落库仍由 pipeline 统一处理。
        """
        if not chunks:
            logger.info("向量生成已跳过：当前没有需要处理的切块。")
            return []

        embedded: list[ChunkItem] = []
        batch_size = max(1, settings.embedding_batch_size)
        total_batches = ceil(len(chunks) / batch_size)
        logger.info(
            "向量生成开始 total_chunks=%s batch_size=%s total_batches=%s model=%s dimensions=%s",
            len(chunks),
            batch_size,
            total_batches,
            settings.embedding_model,
            settings.vector_dimensions,
        )
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            batch_index = start // batch_size + 1
            vectors = self._embed_texts([item.chunk_text for item in batch])
            if len(vectors) != len(batch):
                raise RuntimeError("向量返回数量与切块数量不一致。")

            for chunk, vector in zip(batch, vectors, strict=True):
                if len(vector) != settings.vector_dimensions:
                    raise RuntimeError(
                        f"向量维度不匹配：期望 {settings.vector_dimensions}，实际 {len(vector)}。"
                    )
                embedded.append(chunk.model_copy(update={"embedding": vector}))
            logger.info(
                "向量批次完成 batch_index=%s total_batches=%s batch_chunks=%s embedded_total=%s",
                batch_index,
                total_batches,
                len(batch),
                len(embedded),
            )
        logger.info("向量生成完成 embedded_chunks=%s", len(embedded))
        return embedded

    def embed_query(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ValueError("检索查询不能为空。")

        vectors = self._embed_texts([normalized])
        if len(vectors) != 1:
            raise RuntimeError("查询向量返回数量异常。")

        vector = vectors[0]
        if len(vector) != settings.vector_dimensions:
            raise RuntimeError(
                f"查询向量维度不匹配：期望 {settings.vector_dimensions}，实际 {len(vector)}。"
            )
        return vector

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
