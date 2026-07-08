from __future__ import annotations

from app.repositories.policy_repository import PolicyRepository
from app.schemas import (
    RetrievalDebugInfo,
    RetrievalFilters,
    RetrievalHit,
    RetrievalStageDebug,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.retrieval.pipeline import HybridRetrievalPipeline


class KnowledgeRetrievalService:
    """把 retrieval pipeline 结果映射成接口响应对象。"""

    def __init__(
        self,
        repository: PolicyRepository,
        pipeline: HybridRetrievalPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or HybridRetrievalPipeline(repository)

    def search(self, request: RetrievalSearchRequest) -> RetrievalSearchResponse:
        pipeline_result = self.pipeline.run(request)

        # 这里不重新计算来源和分数，只把 pipeline 已经解释好的结果透传到接口层。
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
                retrieval_source=item.retrieval_source,
                score_breakdown={
                    key: round(value, 6) for key, value in item.score_breakdown.items()
                },
            )
            for index, item in enumerate(pipeline_result.hits, start=1)
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
            debug=RetrievalDebugInfo(
                pipeline=pipeline_result.pipeline,
                strategy=pipeline_result.strategy,
                min_score=pipeline_result.min_score,
                stages=[
                    RetrievalStageDebug(
                        name=trace.name,
                        source=trace.source,
                        input_count=trace.input_count,
                        output_count=trace.output_count,
                        details=trace.details,
                    )
                    for trace in pipeline_result.traces
                ],
            ),
        )
