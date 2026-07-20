from __future__ import annotations

from typing import Protocol

from app.modules.ingestion.contracts import ChunkItem


class ChunkEmbeddingPort(Protocol):
    """入库流程生成文本向量所需的最小能力。"""

    def embed_chunks(self, chunks: list[ChunkItem]) -> list[ChunkItem]: ...
