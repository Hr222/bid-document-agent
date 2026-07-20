from __future__ import annotations

from app.infrastructure.persistence.repositories.policy_repository import PolicyRepository


class KnowledgeWriteRepository(PolicyRepository):
    """知识写仓储。

    复用统一 PostgreSQL 仓储实现，作为入库应用的写端口适配器。
    """

    pass
