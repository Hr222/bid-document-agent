from app.schemas.knowledge_base import KnowledgeBaseOverview, RagMvpStatus


class KnowledgeBaseService:
    """知识库概览服务，用于返回项目阶段信息，不参与制度入库主流水线。"""

    def get_overview(self) -> KnowledgeBaseOverview:
        return KnowledgeBaseOverview(
            phase="rag-mvp",
            mvp_scope=[
                "样本文档入库",
                "切块检索",
                "LLM 问答",
                "知识库维护界面",
                "检索评估",
            ],
            current_categories=["company_policy", "pricing_standard"],
            current_focus="围绕制度样本和价格样本搭建第一版 RAG MVP。",
            next_focus="补齐入库流程、维护界面和检索评估样本集。",
        )

    def get_rag_mvp_status(self) -> RagMvpStatus:
        return RagMvpStatus(
            indexing_table_ready=True,
            sample_categories=["18-company-policy", "pricing-standard"],
            backend_goal="打通入库、切块、检索、回答整条链路。",
            frontend_goal="提供文档列表、详情、检索调试和问答界面。",
            evaluation_goal="准备一套小规模检索相关性基准集。",
        )
