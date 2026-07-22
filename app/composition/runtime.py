"""运行时基础设施检查的 Composition Root 适配。"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.persistence.schema_health import (
    KB_SCHEMA_SETUP_GUIDE,
    safe_find_missing_kb_tables,
)
from app.infrastructure.persistence.session import engine


@dataclass(frozen=True, slots=True)
class KnowledgeBaseSchemaStatus:
    """应用启动阶段可消费的知识库表结构状态。"""

    missing_tables: tuple[str, ...] | None
    setup_guide: str


def inspect_knowledge_base_schema() -> KnowledgeBaseSchemaStatus:
    """在 Composition Root 内执行知识库表结构检查并隐藏具体基础设施。"""

    missing_tables = safe_find_missing_kb_tables(engine)
    return KnowledgeBaseSchemaStatus(
        missing_tables=None if missing_tables is None else tuple(missing_tables),
        setup_guide=KB_SCHEMA_SETUP_GUIDE,
    )
