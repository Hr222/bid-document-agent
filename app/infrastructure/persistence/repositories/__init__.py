"""知识库仓储具体实现。"""

from app.infrastructure.persistence.repositories.knowledge_publication_repository import (
    KnowledgePublicationRepository,
)
from app.infrastructure.persistence.repositories.knowledge_read_repository import (
    KnowledgeReadRepository,
)
from app.infrastructure.persistence.repositories.knowledge_write_repository import (
    KnowledgeWriteRepository,
)

__all__ = [
    "KnowledgePublicationRepository",
    "KnowledgeReadRepository",
    "KnowledgeWriteRepository",
]
