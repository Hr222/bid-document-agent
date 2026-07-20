from pydantic import BaseModel, Field


class KnowledgeBaseOverview(BaseModel):
    """知识库概览信息。"""

    phase: str = Field(description="当前阶段。")
    mvp_scope: list[str] = Field(description="当前 MVP 范围。")
    current_categories: list[str] = Field(description="当前已覆盖的资料分类。")
    current_focus: str = Field(description="当前工作重点。")
    next_focus: str = Field(description="下一步工作重点。")


class RagMvpStatus(BaseModel):
    """RAG MVP 状态摘要。"""

    indexing_table_ready: bool = Field(description="索引表是否已准备好。")
    sample_categories: list[str] = Field(description="示例资料分类。")
    backend_goal: str = Field(description="后端当前目标。")
    frontend_goal: str = Field(description="前端当前目标。")
    evaluation_goal: str = Field(description="验收或评估目标。")


class PolicyDocumentOption(BaseModel):
    """前端选择已有制度时使用的下拉项。"""

    document_id: int = Field(description="制度主档 ID。")
    policy_name: str = Field(description="制度名称。")
    policy_category: str = Field(description="制度分类。")
    responsible_department: str | None = Field(default=None, description="责任部门。")
    latest_version_id: int | None = Field(default=None, description="最新版本 ID。")
    latest_version_label: str | None = Field(default=None, description="最新版本标签。")


class PolicyDocumentOptionList(BaseModel):
    """制度下拉列表响应。"""

    items: list[PolicyDocumentOption] = Field(default_factory=list)
