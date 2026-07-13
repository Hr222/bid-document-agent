"""
接口与内部传输对象包。

这里放 Pydantic Schema，也就是“数据在模块之间、接口之间长什么样”。
常见用途包括：
1. API 请求参数
2. API 响应结果
3. 流水线阶段之间传递的结构化对象

这一层不负责数据库映射，也不负责业务规则判断。
"""

# 流水线通用类型与阶段状态
from app.schemas.policy_pipeline_common import (
    BlockSource,
    BlockType,
    DocumentFileType,
    ParseMethod,
    ParserStatus,
    PipelineStageName,
    PipelineStageResult,
    PipelineStatus,
)

# 文档解析、OCR、清洗相关 Schema
from app.schemas.policy_pipeline_document import (
    AssembledLine,
    CleanedTextResult,
    FormatNormalizationResult,
    IntakeValidationResult,
    OcrProcessResult,
    ParseRoutingResult,
    ParsedBlock,
    ParsedDocumentResult,
    ParsedTextResult,
    PolicyPipelineRequest,
    RegisteredFileInfo,
)

# 章节、切块、落库相关 Schema
from app.schemas.policy_pipeline_content import (
    ChunkItem,
    ChunkSampleItem,
    ChunkSplitResult,
    PersistenceResult,
    SectionSplitItem,
    SectionSplitResult,
)

# 流水线最终响应 Schema
from app.schemas.policy_pipeline_response import PolicyPipelineResponse
from app.schemas.policy_decision import (
    PolicyDecisionChecklistRequest,
    PolicyDecisionChecklistResponse,
    PolicyDecisionDebugInfo,
    PolicyDecisionRequirementStatus,
)
from app.schemas.retrieval import (
    AnswerCitation,
    RagAskRequest,
    RagAskResponse,
    RetrievalDebugInfo,
    RetrievalFilters,
    RetrievalHit,
    RetrievalStageDebug,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.schemas.knowledge_base import (
    KnowledgeBaseOverview,
    PolicyDocumentOption,
    PolicyDocumentOptionList,
    RagMvpStatus,
)

__all__ = [
    "PipelineStageName",
    "PipelineStageResult",
    "PipelineStatus",
    "ParserStatus",
    "DocumentFileType",
    "ParseMethod",
    "BlockType",
    "BlockSource",
    "PolicyPipelineRequest",
    "RegisteredFileInfo",
    "IntakeValidationResult",
    "FormatNormalizationResult",
    "ParseRoutingResult",
    "ParsedBlock",
    "AssembledLine",
    "ParsedDocumentResult",
    "OcrProcessResult",
    "ParsedTextResult",
    "CleanedTextResult",
    "PersistenceResult",
    "SectionSplitItem",
    "SectionSplitResult",
    "ChunkItem",
    "ChunkSampleItem",
    "ChunkSplitResult",
    "PolicyPipelineResponse",
    "PolicyDecisionChecklistRequest",
    "PolicyDecisionChecklistResponse",
    "PolicyDecisionDebugInfo",
    "PolicyDecisionRequirementStatus",
    "RetrievalSearchRequest",
    "RetrievalFilters",
    "RetrievalHit",
    "RetrievalStageDebug",
    "RetrievalDebugInfo",
    "RetrievalSearchResponse",
    "RagAskRequest",
    "AnswerCitation",
    "RagAskResponse",
    "KnowledgeBaseOverview",
    "RagMvpStatus",
    "PolicyDocumentOption",
    "PolicyDocumentOptionList",
]
