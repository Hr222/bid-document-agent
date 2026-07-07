from __future__ import annotations

from dataclasses import dataclass, field, replace

from app.core.config import settings
from app.domain.policy import PolicyRetrievalQueryPolicy, RetrievalKeywordPlan
from app.repositories.policy_repository import PolicyRepository, RetrievedPolicyChunk
from app.schemas import RetrievalSearchRequest
from app.services.step.policy_embedding import PolicyEmbeddingService


@dataclass(slots=True)
class RetrievalStageTrace:
    """记录单个检索阶段的输入、输出与调试细节。"""

    name: str
    source: str | None = None
    input_count: int | None = None
    output_count: int | None = None
    details: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalPipelineResult:
    """聚合检索 pipeline 的最终结果与调试轨迹。"""

    hits: list[RetrievedPolicyChunk]
    pipeline: str
    strategy: str
    min_score: float
    traces: list[RetrievalStageTrace]


class HybridRetrievalPipeline:
    """Milestone B 第一版检索 pipeline：向量召回 + 关键词召回 + 简单融合。"""

    pipeline_name = "knowledge-retrieval-v2"
    strategy_name = "hybrid-vector-keyword"

    def __init__(
        self,
        repository: PolicyRepository,
        embedding_service: PolicyEmbeddingService | None = None,
        query_policy: PolicyRetrievalQueryPolicy | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service or PolicyEmbeddingService()
        self.query_policy = query_policy or PolicyRetrievalQueryPolicy()

    def run(self, request: RetrievalSearchRequest) -> RetrievalPipelineResult:
        # 双路召回时，每一路先多取一些候选，给后续融合留下空间。
        per_source_top_k = min(
            settings.retrieval_top_k_max,
            max(request.top_k, request.top_k * 2),
        )
        # 先把问句拆成更适合关键词召回的查询片段，避免“多久/哪些人”这类问法词干扰命中。
        keyword_plan = self.query_policy.build_keyword_plan(request.query)
        query_embedding = self.embedding_service.embed_query(request.query)

        vector_hits = self.repository.search_chunks(
            query_embedding=query_embedding,
            top_k=per_source_top_k,
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
            document_id=request.document_id,
            include_history=request.include_history,
        )
        keyword_hits = self.repository.search_chunks_by_keywords(
            focus_query=keyword_plan.focus_query,
            keywords=keyword_plan.keywords,
            top_k=per_source_top_k,
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
            document_id=request.document_id,
            include_history=request.include_history,
        )
        fused_hits = self._merge_hits(vector_hits=vector_hits, keyword_hits=keyword_hits)
        # 阈值过滤放在融合后执行，避免单一路分数偏低但双路共同命中的结果被提前过滤掉。
        filtered_hits = [
            item for item in fused_hits if item.score >= settings.retrieval_min_score
        ][: request.top_k]

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
                output_count=len(vector_hits),
                details={
                    "top_k": per_source_top_k,
                    "include_history": request.include_history,
                    "document_filter": request.document_id,
                    "policy_category_filter": request.policy_category,
                    "department_filter": request.responsible_department,
                },
            ),
            RetrievalStageTrace(
                name="keyword_recall",
                source="like_keyword_match",
                input_count=len(keyword_plan.keywords),
                output_count=len(keyword_hits),
                details=self._build_keyword_recall_trace_details(
                    per_source_top_k=per_source_top_k,
                    keyword_plan=keyword_plan,
                    keyword_hits=keyword_hits,
                ),
            ),
            RetrievalStageTrace(
                name="result_fusion",
                source="chunk_id_dedup",
                input_count=len(vector_hits) + len(keyword_hits),
                output_count=len(fused_hits),
                details={
                    "duplicate_chunk_count": (
                        len(vector_hits) + len(keyword_hits) - len(fused_hits)
                    ),
                },
            ),
            RetrievalStageTrace(
                name="score_filter",
                source="min_score_threshold",
                input_count=len(fused_hits),
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

    def _build_keyword_recall_trace_details(
        self,
        *,
        per_source_top_k: int,
        keyword_plan: RetrievalKeywordPlan,
        keyword_hits: list[RetrievedPolicyChunk],
    ) -> dict[str, str | int | float | bool | None]:
        details: dict[str, str | int | float | bool | None] = {
            "top_k": per_source_top_k,
            "focus_query": keyword_plan.focus_query or None,
            "keyword_count": len(keyword_plan.keywords),
            "keywords_preview": ", ".join(keyword_plan.keywords[:6]) or None,
        }

        # MVP 阶段先把前几条命中的关键词原因压成字符串输出，便于人工审查效果。
        for index, hit in enumerate(keyword_hits[:3], start=1):
            matched_fields = hit.debug_details.get("matched_fields") or "-"
            matched_keywords = hit.debug_details.get("matched_keywords") or "-"
            score_terms = hit.debug_details.get("keyword_score_terms") or "-"
            details[f"sample_hit_{index}"] = (
                f"chunk={hit.chunk_id} "
                f"fields={matched_fields} "
                f"keywords={matched_keywords} "
                f"terms={score_terms}"
            )

        return details

    def _merge_hits(
        self,
        *,
        vector_hits: list[RetrievedPolicyChunk],
        keyword_hits: list[RetrievedPolicyChunk],
    ) -> list[RetrievedPolicyChunk]:
        # 以 chunk_id 作为融合主键，保证同一切块不会重复展示。
        merged_by_chunk: dict[int, RetrievedPolicyChunk] = {}

        for hit in vector_hits + keyword_hits:
            existing = merged_by_chunk.get(hit.chunk_id)
            if existing is None:
                merged_by_chunk[hit.chunk_id] = replace(
                    hit,
                    score_breakdown=dict(hit.score_breakdown),
                )
                continue

            # 命中同一切块时，分别保留两路的最高分，再计算融合分。
            vector_score = max(
                existing.score_breakdown.get("vector", 0.0),
                hit.score_breakdown.get("vector", 0.0),
            )
            keyword_score = max(
                existing.score_breakdown.get("keyword", 0.0),
                hit.score_breakdown.get("keyword", 0.0),
            )
            existing.score_breakdown = {
                key: round(value, 6)
                for key, value in {
                    "vector": vector_score,
                    "keyword": keyword_score,
                }.items()
                if value > 0.0
            }
            existing.score = self._fuse_score(vector_score=vector_score, keyword_score=keyword_score)
            existing.retrieval_source = self._resolve_retrieval_source(
                vector_score=vector_score,
                keyword_score=keyword_score,
            )

        ranked_hits = list(merged_by_chunk.values())
        # 排序先看融合分，再用关键词分和向量分做稳定 tie-break。
        ranked_hits.sort(
            key=lambda item: (
                -item.score,
                -item.score_breakdown.get("keyword", 0.0),
                -item.score_breakdown.get("vector", 0.0),
                item.chunk_id,
            )
        )
        return ranked_hits

    def _fuse_score(self, *, vector_score: float, keyword_score: float) -> float:
        # 第一版融合规则保持可解释：
        # 双路都命中时，以主分为主、辅分做少量加成；单路命中时直接沿用该路分数。
        if vector_score > 0.0 and keyword_score > 0.0:
            return round(
                min(1.0, max(vector_score, keyword_score) + min(vector_score, keyword_score) * 0.25),
                6,
            )
        return round(max(vector_score, keyword_score), 6)

    def _resolve_retrieval_source(self, *, vector_score: float, keyword_score: float) -> str:
        if vector_score > 0.0 and keyword_score > 0.0:
            return "hybrid"
        if keyword_score > 0.0:
            return "keyword"
        return "vector"


ExactVectorRetrievalPipeline = HybridRetrievalPipeline
