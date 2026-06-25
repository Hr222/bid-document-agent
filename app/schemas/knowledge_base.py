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
