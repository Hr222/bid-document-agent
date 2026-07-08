"""兼容旧导入路径的检索 pipeline 包装层。

当前真正的职责拆分实现已经下沉到 `app.services.retrieval` 包中。
这里保留旧模块名，是为了不打断现有调用方和测试。
"""

from app.services.retrieval import (
    ExactVectorRetrievalPipeline,
    HybridRetrievalPipeline,
    RetrievalPipelineResult,
    RetrievalStageTrace,
)

__all__ = [
    "ExactVectorRetrievalPipeline",
    "HybridRetrievalPipeline",
    "RetrievalPipelineResult",
    "RetrievalStageTrace",
]
