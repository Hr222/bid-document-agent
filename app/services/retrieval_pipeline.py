from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings
from app.repositories.policy_repository import PolicyRepository, RetrievedPolicyChunk
from app.schemas import RetrievalSearchRequest
from app.services.step.policy_embedding import PolicyEmbeddingService


@dataclass(slots=True)
class RetrievalStageTrace:
    name: str
    source: str | None = None
    input_count: int | None = None
    output_count: int | None = None
    details: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalPipelineResult:
    hits: list[RetrievedPolicyChunk]
    pipeline: str
    strategy: str
    min_score: float
    traces: list[RetrievalStageTrace]


class ExactVectorRetrievalPipeline:
    """当前阶段的默认检索 pipeline：查询向量化 -> 精确向量召回 -> 阈值过滤。"""

    pipeline_name = "knowledge-retrieval-v1"
    strategy_name = "vector-only-exact"

    def __init__(
        self,
        repository: PolicyRepository,
        embedding_service: PolicyEmbeddingService | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service or PolicyEmbeddingService()

    def run(self, request: RetrievalSearchRequest) -> RetrievalPipelineResult:
        query_embedding = self.embedding_service.embed_query(request.query)
        recalled_hits = self.repository.search_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
            document_id=request.document_id,
            include_history=request.include_history,
        )
        filtered_hits = [
            item for item in recalled_hits if item.score >= settings.retrieval_min_score
        ]

        traces = [
            RetrievalStageTrace(
                name="query_embedding",
                source="gitee_embedding",
                input_count=1,
                output_count=1,
                details={"dimensions": len(query_embedding)},
            ),
            RetrievalStageTrace(
                name="vector_recall",
                source="pgvector_cosine_exact",
                input_count=None,
                output_count=len(recalled_hits),
                details={
                    "top_k": request.top_k,
                    "include_history": request.include_history,
                    "document_filter": request.document_id,
                    "policy_category_filter": request.policy_category,
                    "department_filter": request.responsible_department,
                },
            ),
            RetrievalStageTrace(
                name="score_filter",
                source="min_score_threshold",
                input_count=len(recalled_hits),
                output_count=len(filtered_hits),
                details={"min_score": settings.retrieval_min_score},
            ),
        ]

        return RetrievalPipelineResult(
            hits=filtered_hits,
            pipeline=self.pipeline_name,
            strategy=self.strategy_name,
            min_score=settings.retrieval_min_score,
            traces=traces,
        )
