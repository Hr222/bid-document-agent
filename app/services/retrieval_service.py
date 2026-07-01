from __future__ import annotations

from app.core.config import settings
from app.repositories.policy_repository import PolicyRepository
from app.schemas import (
    RetrievalFilters,
    RetrievalHit,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.step.policy_embedding import PolicyEmbeddingService


class KnowledgeRetrievalService:
    """Build retrieval hits from query embedding and vector search."""

    def __init__(
        self,
        repository: PolicyRepository,
        embedding_service: PolicyEmbeddingService | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service or PolicyEmbeddingService()

    def search(self, request: RetrievalSearchRequest) -> RetrievalSearchResponse:
        query_embedding = self.embedding_service.embed_query(request.query)
        matches = self.repository.search_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
            document_id=request.document_id,
            include_history=request.include_history,
        )
        matches = [
            item for item in matches if item.score >= settings.retrieval_min_score
        ]

        hits = [
            RetrievalHit(
                document_id=item.document_id,
                version_id=item.version_id,
                chunk_id=item.chunk_id,
                policy_name=item.policy_name,
                policy_category=item.policy_category,
                responsible_department=item.responsible_department,
                version_label=item.version_label,
                section_title=item.section_title,
                section_path=item.section_path,
                page_no=item.page_no,
                chunk_text=item.chunk_text,
                score=round(item.score, 6),
                rank=index,
            )
            for index, item in enumerate(matches, start=1)
        ]

        return RetrievalSearchResponse(
            query=request.query,
            top_k=request.top_k,
            filters=RetrievalFilters(
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                document_id=request.document_id,
                include_history=request.include_history,
            ),
            hits=hits,
        )
