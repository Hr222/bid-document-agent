from app.schemas.knowledge_base import KnowledgeBaseOverview, RagMvpStatus


class KnowledgeBaseService:
    def get_overview(self) -> KnowledgeBaseOverview:
        return KnowledgeBaseOverview(
            phase="rag-mvp",
            mvp_scope=[
                "sample document ingestion",
                "chunk retrieval",
                "llm question answering",
                "knowledge base maintenance ui",
                "retrieval evaluation",
            ],
            current_categories=["company_policy", "pricing_standard"],
            current_focus="Build the first RAG MVP around policy and pricing samples.",
            next_focus="Add ingestion workflow, maintenance UI, and retrieval evaluation set.",
        )

    def get_rag_mvp_status(self) -> RagMvpStatus:
        return RagMvpStatus(
            indexing_table_ready=True,
            sample_categories=["18-company-policy", "pricing-standard"],
            backend_goal="Complete the ingest -> chunk -> retrieve -> answer pipeline.",
            frontend_goal="Provide document list, detail, retrieval debug, and QA screens.",
            evaluation_goal="Prepare a small benchmark set for retrieval relevance checks.",
        )
