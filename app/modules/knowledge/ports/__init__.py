"""知识模块对外依赖的端口。"""

from app.modules.knowledge.ports.publication_port import (
    KnowledgePublicationPort,
    KnowledgePublicationRecord,
)
from app.modules.knowledge.ports.quality_audit import (
    KnowledgeAuditIssue,
    KnowledgeQualityAuditPort,
    KnowledgeQualityAuditReport,
)
from app.modules.knowledge.ports.read_port import (
    KnowledgeDocument,
    KnowledgeQuery,
    KnowledgeQueryResult,
    KnowledgeReadPort,
    KnowledgeSearchHit,
)
from app.modules.knowledge.ports.write_port import KnowledgeWritePort, KnowledgeWriteResult

__all__ = [
    "KnowledgeDocument",
    "KnowledgePublicationPort",
    "KnowledgePublicationRecord",
    "KnowledgeQuery",
    "KnowledgeQueryResult",
    "KnowledgeReadPort",
    "KnowledgeSearchHit",
    "KnowledgeWritePort",
    "KnowledgeWriteResult",
    "KnowledgeAuditIssue",
    "KnowledgeQualityAuditPort",
    "KnowledgeQualityAuditReport",
]
