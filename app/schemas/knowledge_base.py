from pydantic import BaseModel


class KnowledgeBaseOverview(BaseModel):
    phase: str
    mvp_scope: list[str]
    current_categories: list[str]
    current_focus: str
    next_focus: str


class RagMvpStatus(BaseModel):
    indexing_table_ready: bool
    sample_categories: list[str]
    backend_goal: str
    frontend_goal: str
    evaluation_goal: str
