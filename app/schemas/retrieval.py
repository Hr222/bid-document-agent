from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.config import settings


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


class RetrievalSearchResponse(BaseModel):
    query: str
    top_k: int
    filters: RetrievalFilters
    hits: list[RetrievalHit]


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
    ref_no: int
    document_id: int
    version_id: int
    chunk_id: int
    policy_name: str
    section_title: str | None = None
    page_no: int | None = None
    quote: str


class RagAskResponse(BaseModel):
    query: str
    answer: str
    model: str | None
    citations: list[AnswerCitation]
    hits: list[RetrievalHit]
