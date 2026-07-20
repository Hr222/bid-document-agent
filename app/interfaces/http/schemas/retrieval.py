from __future__ import annotations

from pydantic import BaseModel, Field

from app.shared.config import settings


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户查询。")
    top_k: int = Field(
        default=settings.retrieval_top_k_default,
        ge=1,
        le=settings.retrieval_top_k_max,
        description="召回数量。",
    )
    policy_category: str | None = Field(default=None, description="制度分类过滤。")
    responsible_department: str | None = Field(default=None, description="责任部门过滤。")
    document_id: int | None = Field(default=None, ge=1, description="制度主档过滤。")
    include_history: bool = Field(default=False, description="是否包含历史版本。")


class RetrievalFilters(BaseModel):
    policy_category: str | None = None
    responsible_department: str | None = None
    document_id: int | None = None
    include_history: bool


class RetrievalHit(BaseModel):
    """单条检索命中结果，包含展示字段和调试字段。"""

    document_id: int
    version_id: int
    chunk_id: int
    policy_name: str
    policy_category: str
    responsible_department: str | None = None
    version_label: str
    section_title: str | None = None
    section_path: str | None = None
    page_no: int | None = None
    chunk_text: str
    score: float
    rank: int
    retrieval_source: str = Field(description="命中结果来源，例如 vector / keyword / hybrid。")
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="各阶段分数拆解，便于调试融合与重排效果。",
    )


class RetrievalStageDebug(BaseModel):
    """单个检索阶段的调试快照。"""

    name: str
    source: str | None = None
    input_count: int | None = None
    output_count: int | None = None
    details: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RetrievalDebugInfo(BaseModel):
    """完整检索链路的调试信息。"""

    pipeline: str
    strategy: str
    min_score: float
    stages: list[RetrievalStageDebug]


class RetrievalSearchResponse(BaseModel):
    """search 接口响应，返回命中结果与检索调试信息。"""

    query: str
    top_k: int
    filters: RetrievalFilters
    hits: list[RetrievalHit]
    debug: RetrievalDebugInfo


class RagAskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户问题。")
    top_k: int = Field(
        default=settings.rag_answer_top_k,
        ge=1,
        le=settings.retrieval_top_k_max,
        description="回答前召回数量。",
    )
    policy_category: str | None = Field(default=None, description="制度分类过滤。")
    responsible_department: str | None = Field(default=None, description="责任部门过滤。")
    document_id: int | None = Field(default=None, ge=1, description="制度主档过滤。")
    include_history: bool = Field(default=False, description="是否包含历史版本。")


class AnswerCitation(BaseModel):
    """问答结果中的单条引用。"""

    ref_no: int
    document_id: int
    version_id: int
    chunk_id: int
    policy_name: str
    section_title: str | None = None
    page_no: int | None = None
    quote: str


class RagAskResponse(BaseModel):
    """ask 接口响应，返回答案、引用、命中结果与可选调试信息。"""

    query: str
    answer: str
    model: str | None
    citations: list[AnswerCitation]
    hits: list[RetrievalHit]
    debug: RetrievalDebugInfo | None = None
