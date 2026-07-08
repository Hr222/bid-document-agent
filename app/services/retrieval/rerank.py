from __future__ import annotations

from dataclasses import replace

from app.domain.policy import PolicyRetrievalQueryPolicy, RetrievalKeywordPlan
from app.repositories.policy_repository import RetrievedPolicyChunk


class HeuristicRetrievalReranker:
    """负责当前启发式 rerank 规则，避免 pipeline 混入过多排序细节。"""

    source_name = "heuristic_lexical_alignment"

    def __init__(
        self,
        *,
        query_policy: PolicyRetrievalQueryPolicy,
        base_weight: float = 0.6,
        signal_weight: float = 0.4,
    ) -> None:
        self.query_policy = query_policy
        self.base_weight = base_weight
        self.signal_weight = signal_weight

    def rerank_hits(
        self,
        *,
        query: str,
        keyword_plan: RetrievalKeywordPlan,
        hits: list[RetrievedPolicyChunk],
    ) -> list[RetrievedPolicyChunk]:
        if not hits:
            return []

        # rerank 只处理“候选已召回，但顺序还不够准”的问题，因此只做增量重排。
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
                        hit.score * self.base_weight
                        + rerank_score * self.signal_weight,
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

    def build_trace_details(
        self,
        *,
        query: str,
        keyword_plan: RetrievalKeywordPlan,
        before_hits: list[RetrievedPolicyChunk],
        after_hits: list[RetrievedPolicyChunk],
    ) -> dict[str, str | int | float | bool | None]:
        # rerank 阶段需要解释“为什么顺序变了”，因此记录前后名次与命中原因。
        details: dict[str, str | int | float | bool | None] = {
            "query": query,
            "focus_query": keyword_plan.focus_query or None,
            "formula": (
                f"final={self.base_weight:.2f}*fusion+"
                f"{self.signal_weight:.2f}*rerank"
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

    def _compute_rerank_signal(
        self,
        *,
        hit: RetrievedPolicyChunk,
        normalized_query: str,
        keyword_plan: RetrievalKeywordPlan,
    ) -> tuple[float, dict[str, str | int | float | bool | None]]:
        # 先把不同字段统一归一化，后续所有 rerank 判断都只基于归一化文本进行。
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
            # focus_query 是去掉问句外壳后的核心表达，优先级高于一般关键词。
            add_match(
                keyword_plan.focus_query,
                chunk_weight=0.32,
                section_title_weight=0.12,
                section_path_weight=0.08,
                policy_name_weight=0.02,
            )
            focus_position = normalized_chunk_text.find(keyword_plan.focus_query)
            if 0 <= focus_position <= 24:
                # 关键词出现在文本前部时，通常更可能是直接回答问题的条款。
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
            # 命中的关键词越多，通常越接近问题主旨，但加成需要上限避免覆盖融合分。
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
        # 当前只取 focus_query 尾部的 4/3/2 字符片段，强化“适用人/试用期”等短语末尾语义。
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
