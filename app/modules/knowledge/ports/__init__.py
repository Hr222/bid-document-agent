"""知识模块对外依赖的端口。"""

from app.modules.knowledge.ports.publication_port import KnowledgePublicationPort
from app.modules.knowledge.ports.read_port import (
    KnowledgeDocument,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeReadPort,
    KnowledgeSearchHit,
)
from app.modules.knowledge.ports.write_port import KnowledgeWritePort

__all__ = [
    "KnowledgeDocument",
    "KnowledgePublicationPort",
    "KnowledgeQuery",
    "KnowledgeQueryResult",
    "KnowledgeReadPort",
    "KnowledgeSearchHit",
    "KnowledgeWritePort",
]
