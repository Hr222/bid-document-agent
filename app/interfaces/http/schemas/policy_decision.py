from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.interfaces.http.schemas.retrieval import AnswerCitation, RetrievalDebugInfo
from app.shared.config import settings


class PolicyDecisionRequest(BaseModel):
    """规则决策接口的通用请求结构。"""

    submitted_materials: list[str] = Field(
        default_factory=list,
        description="本次已准备或已提交的材料名称列表。",
    )
    top_k: int = Field(
        default=settings.retrieval_top_k_default,
        ge=1,
        le=settings.retrieval_top_k_max,
        description="规则检索时保留的候选条数。",
    )
    document_id: int | None = Field(
        default=None,
        ge=1,
        description="可选的制度文档过滤条件。",
    )
    include_history: bool = Field(default=False, description="是否包含历史版本。")


class PolicyDecisionRequirementStatus(BaseModel):
    """单项材料要求的命中、提交与缺失状态。"""

    field_key: str
    label: str
    rule_matched: bool
    submitted: bool
    matched_rule_keywords: list[str] = Field(default_factory=list)
    matched_submission_items: list[str] = Field(default_factory=list)
    matched_components: list[str] = Field(default_factory=list)
    missing_components: list[str] = Field(default_factory=list)


class PolicyDecisionDebugInfo(BaseModel):
    """调试视角下的检索与判定摘要。"""

    retrieval_query: str
    policy_category: str | None = None
    provider: str
    rule_hit_count: int
    matched_rule_requirement_count: int
    submitted_material_count: int
    data_acquisition: "PolicyDecisionDataAcquisitionDebug"
    retrieval: RetrievalDebugInfo


class PolicyDecisionDataFieldTrace(BaseModel):
    """单个业务输入字段的来源与供给情况。"""

    field_key: str
    label: str
    source: str
    provided: bool
    value_count: int


class PolicyDecisionDataAcquisitionDebug(BaseModel):
    """数据获取阶段的调试摘要。"""

    provider: str
    provided_input_fields: list[str] = Field(default_factory=list)
    missing_input_fields: list[str] = Field(default_factory=list)
    field_traces: list[PolicyDecisionDataFieldTrace] = Field(default_factory=list)


class PolicyDecisionResponse(BaseModel):
    """规则决策接口的通用响应结构。"""

    scenario_code: str
    scenario_name: str
    decision: Literal["pass", "fail", "insufficient_evidence"]
    reasoning: list[str]
    citations: list[AnswerCitation]
    used_fields: list[str]
    missing_input_fields: list[str]
    missing_fields: list[str]
    requirement_statuses: list[PolicyDecisionRequirementStatus]
    debug: PolicyDecisionDebugInfo


# 保留旧名称，避免已有调用方因 D4 通用化改名而中断。
PolicyDecisionChecklistRequest = PolicyDecisionRequest
PolicyDecisionChecklistResponse = PolicyDecisionResponse
