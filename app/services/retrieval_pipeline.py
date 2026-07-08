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
    rerank_base_weight = 0.6
    rerank_signal_weight = 0.4

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
        reranked_hits = self._rerank_hits(
            query=request.query,
            keyword_plan=keyword_plan,
            hits=fused_hits,
        )
        # 阈值过滤放在融合后执行，避免单一路分数偏低但双路共同命中的结果被提前过滤掉。
        filtered_hits = [
            item for item in reranked_hits if item.score >= settings.retrieval_min_score
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
                name="rerank",
                source="heuristic_lexical_alignment",
                input_count=len(fused_hits),
                output_count=len(reranked_hits),
                details=self._build_rerank_trace_details(
                    query=request.query,
                    keyword_plan=keyword_plan,
                    before_hits=fused_hits,
                    after_hits=reranked_hits,
                ),
            ),
            RetrievalStageTrace(
                name="score_filter",
                source="min_score_threshold",
                input_count=len(reranked_hits),
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

    def _build_rerank_trace_details(
        self,
        *,
        query: str,
        keyword_plan: RetrievalKeywordPlan,
        before_hits: list[RetrievedPolicyChunk],
        after_hits: list[RetrievedPolicyChunk],
    ) -> dict[str, str | int | float | bool | None]:
        # rerank 阶段要能解释“为什么顺序变了”，因此这里记录前后名次与命中原因。
        details: dict[str, str | int | float | bool | None] = {
            "query": query,
            "focus_query": keyword_plan.focus_query or None,
            "formula": (
                f"final={self.rerank_base_weight:.2f}*fusion+"
                f"{self.rerank_signal_weight:.2f}*rerank"
            ),
        }

        before_rank = {
            hit.chunk_id: index for index, hit in enumerate(before_hits, start=1)
        }
        for index, hit in enumerate(after_hits[:3], start=1):
            matched_keywords = hit.debug_details.get("rerank_matched_keywords") or "-"
            matched_fields = hit.debug_details.get("rerank_matched_fields") or "-"
            rerank_score = hit.score_breakdown.get("rerank", 0.0)
            details[f"sample_hit_{index}"] = (
                f"before_rank={before_rank.get(hit.chunk_id, '-')} "
                f"after_rank={index} "
                f"chunk={hit.chunk_id} "
                f"final={hit.score:.4f} "
                f"rerank={rerank_score:.4f} "
                f"fields={matched_fields} "
                f"keywords={matched_keywords}"
            )

        changed_chunks = [
            str(hit.chunk_id)
            for index, hit in enumerate(after_hits[:5], start=1)
            if before_rank.get(hit.chunk_id) != index
        ]
        details["changed_top5_chunks"] = ", ".join(changed_chunks) or None
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

    def _rerank_hits(
        self,
        *,
        query: str,
        keyword_plan: RetrievalKeywordPlan,
        hits: list[RetrievedPolicyChunk],
    ) -> list[RetrievedPolicyChunk]:
        if not hits:
            return []

        # rerank 只处理“候选已召回，但顺序还不够准”的问题，因此在融合结果上做增量重排。
        reranked_hits: list[RetrievedPolicyChunk] = []
        normalized_query = self.query_policy.normalize_query(query)
        for hit in hits:
            rerank_score, rerank_details = self._compute_rerank_signal(
                hit=hit,
                normalized_query=normalized_query,
                keyword_plan=keyword_plan,
            )
            reranked_hits.append(
                replace(
                    hit,
                    score=round(
                        hit.score * self.rerank_base_weight
                        + rerank_score * self.rerank_signal_weight,
                        6,
                    ),
                    score_breakdown={
                        **hit.score_breakdown,
                        "rerank": rerank_score,
                    },
                    debug_details={
                        **hit.debug_details,
                        **rerank_details,
                    },
                )
            )

        reranked_hits.sort(
            key=lambda item: (
                -item.score,
                -item.score_breakdown.get("rerank", 0.0),
                -item.score_breakdown.get("keyword", 0.0),
                -item.score_breakdown.get("vector", 0.0),
                item.chunk_id,
            )
        )
        return reranked_hits

    def _compute_rerank_signal(
        self,
        *,
        hit: RetrievedPolicyChunk,
        normalized_query: str,
        keyword_plan: RetrievalKeywordPlan,
    ) -> tuple[float, dict[str, str | int | float | bool | None]]:
        # 这里先把不同字段做统一归一化，后续所有 rerank 判断都只基于归一化文本进行。
        normalized_chunk_text = self.query_policy.normalize_query(hit.chunk_text)
        normalized_policy_name = self.query_policy.normalize_query(hit.policy_name)
        normalized_section_title = self.query_policy.normalize_query(hit.section_title or "")
        normalized_section_path = self.query_policy.normalize_query(hit.section_path or "")

        score = 0.0
        matched_fields: list[str] = []
        matched_keywords: list[str] = []

        def append_field(field_name: str) -> None:
            if field_name not in matched_fields:
                matched_fields.append(field_name)

        def add_match(
            term: str,
            *,
            chunk_weight: float,
            section_title_weight: float,
            section_path_weight: float,
            policy_name_weight: float,
        ) -> None:
            nonlocal score
            if not term:
                return

            matched = False
            if term in normalized_chunk_text:
                score += chunk_weight
                append_field("chunk_text")
                matched = True
            if term in normalized_section_title:
                score += section_title_weight
                append_field("section_title")
                matched = True
            if term in normalized_section_path:
                score += section_path_weight
                append_field("section_path")
                matched = True
            if term in normalized_policy_name:
                score += policy_name_weight
                append_field("policy_name")
                matched = True
            if matched and term not in matched_keywords:
                matched_keywords.append(term)

        if normalized_query:
            add_match(
                normalized_query,
                chunk_weight=0.08,
                section_title_weight=0.03,
                section_path_weight=0.02,
                policy_name_weight=0.01,
            )

        if keyword_plan.focus_query:
            # focus_query 是去掉问法词后的核心表达，优先级高于一般关键词。
            add_match(
                keyword_plan.focus_query,
                chunk_weight=0.32,
                section_title_weight=0.12,
                section_path_weight=0.08,
                policy_name_weight=0.02,
            )
            focus_position = normalized_chunk_text.find(keyword_plan.focus_query)
            if 0 <= focus_position <= 24:
                # 如果核心表达在正文前部出现，通常说明这条更像在直接定义该问题。
                score += 0.08
            for priority_term in self._build_priority_terms(keyword_plan.focus_query):
                if len(priority_term) >= 3:
                    add_match(
                        priority_term,
                        chunk_weight=0.16,
                        section_title_weight=0.08,
                        section_path_weight=0.05,
                        policy_name_weight=0.0,
                    )
                else:
                    add_match(
                        priority_term,
                        chunk_weight=0.10,
                        section_title_weight=0.05,
                        section_path_weight=0.03,
                        policy_name_weight=0.0,
                    )

        for keyword in keyword_plan.keywords:
            if len(keyword) >= 4:
                add_match(
                    keyword,
                    chunk_weight=0.09,
                    section_title_weight=0.05,
                    section_path_weight=0.035,
                    policy_name_weight=0.01,
                )
            elif len(keyword) == 3:
                add_match(
                    keyword,
                    chunk_weight=0.07,
                    section_title_weight=0.04,
                    section_path_weight=0.03,
                    policy_name_weight=0.008,
                )
            else:
                add_match(
                    keyword,
                    chunk_weight=0.045,
                    section_title_weight=0.025,
                    section_path_weight=0.02,
                    policy_name_weight=0.005,
                    )

        if matched_keywords:
            # 命中关键词越多，通常越可能是直接相关条款，但加成上限需要控制，避免覆盖融合分。
            score += min(
                0.18,
                len(matched_keywords) / max(1, min(6, len(keyword_plan.keywords))) * 0.18,
            )

        rerank_score = round(min(1.0, score), 6)
        return rerank_score, {
            "rerank_matched_fields": ", ".join(matched_fields) or None,
            "rerank_matched_keywords": ", ".join(matched_keywords[:8]) or None,
        }

    def _build_priority_terms(self, focus_query: str) -> list[str]:
        # 当前先取 focus_query 尾部的 4/3/2 字符片段，强化“适用于/试用期”这类决定条款意图的短语。
        priority_terms: list[str] = []
        normalized_focus_query = self.query_policy.normalize_query(focus_query)
        for size in (4, 3, 2):
            if len(normalized_focus_query) < size:
                continue
            term = normalized_focus_query[-size:]
            if not self.query_policy.should_keep_keyword(term):
                continue
            if term not in priority_terms:
                priority_terms.append(term)
        return priority_terms

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
