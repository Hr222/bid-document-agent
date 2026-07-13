from __future__ import annotations

from typing import Protocol

from app.repositories.policy_repository import RetrievedPolicyChunk


class RetrievalRepository(Protocol):
    """约束检索 pipeline 依赖的仓储能力，避免直接耦合具体实现细节。"""

    def search_chunks_exact(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]: ...

    def search_chunks_hnsw(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]: ...

    def search_chunks(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]: ...

    def search_chunks_by_keywords(
        self,
        *,
        focus_query: str | None,
        keywords: list[str],
        priority_keywords: list[str] | None = None,
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]: ...


class QueryEmbeddingService(Protocol):
    """约束查询向量服务，只保留 pipeline 真正关心的接口。"""

    def embed_query(self, query: str) -> list[float]: ...
