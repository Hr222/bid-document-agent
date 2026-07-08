"""检索链路职责包导出。

这里集中暴露当前检索主链路涉及的核心对象，方便调用方按职责引用：
- `HybridRetrievalPipeline`：负责整体检索编排
- `HybridHitFusionService`：负责双路召回结果融合
- `HeuristicRetrievalReranker`：负责启发式重排
- `KnowledgeRetrievalService`：负责检索结果到接口响应的映射
- `RagAnswerService`：负责基于检索命中的最小问答生成
"""

from app.services.retrieval.answer_service import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    RagAnswerService,
)
from app.services.retrieval.fusion import HybridHitFusionService
from app.services.retrieval.models import RetrievalPipelineResult, RetrievalStageTrace
from app.services.retrieval.pipeline import (
    ExactVectorRetrievalPipeline,
    HybridRetrievalPipeline,
)
from app.services.retrieval.rerank import HeuristicRetrievalReranker
from app.services.retrieval.service import KnowledgeRetrievalService
from app.services.retrieval.vector_search import (
    ExactVectorSearchStrategy,
    HnswVectorSearchStrategy,
    build_vector_search_strategy,
)

__all__ = [
    "ExactVectorRetrievalPipeline",
    "ExactVectorSearchStrategy",
    "HeuristicRetrievalReranker",
    "HybridHitFusionService",
    "HybridRetrievalPipeline",
    "HnswVectorSearchStrategy",
    "INSUFFICIENT_EVIDENCE_ANSWER",
    "KnowledgeRetrievalService",
    "RagAnswerService",
    "RetrievalPipelineResult",
    "RetrievalStageTrace",
    "build_vector_search_strategy",
]
