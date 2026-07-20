from __future__ import annotations

from app.infrastructure.persistence.repositories.policy_persistence_gateway import (
    PolicyPersistenceGateway,
)
from app.modules.knowledge.ports.read_port import (
    KnowledgeDocument,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeReadPort,
)
from app.modules.knowledge.retrieval import KnowledgeRetrievalService
from app.modules.knowledge.retrieval.contracts import QueryEmbeddingService


class KnowledgeReadRepository(KnowledgeReadPort):
    """PostgreSQL/pgvector 读仓储适配器。

    现阶段复用已经稳定的混合检索实现，外部只看到知识端口，不再直接拿到旧仓储。
    """

    def __init__(
        self,
        gateway: PolicyPersistenceGateway,
        *,
        embedding_service: QueryEmbeddingService | None = None,
    ) -> None:
        self.gateway = gateway
        self.retrieval_service = KnowledgeRetrievalService(
            gateway,
            embedding_service=embedding_service,
        )

    def search(self, query: KnowledgeQuery) -> KnowledgeQueryResult:
        return self.retrieval_service.search(query)

    def list_documents(
        self,
        *,
        search: str | None = None,
        policy_category: str | None = None,
        limit: int = 50,
    ) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(
                document_id=item.document_id,
                policy_name=item.policy_name,
                policy_category=item.policy_category,
                responsible_department=item.responsible_department,
                latest_version_id=item.latest_version_id,
                latest_version_label=item.latest_version_label,
            )
            for item in self.gateway.list_documents(
                search=search,
                policy_category=policy_category,
                limit=limit,
            )
        ]
