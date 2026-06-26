from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

REQUIRED_KB_TABLES = (
    "kb_policy_document",
    "kb_policy_version",
    "kb_policy_section",
    "kb_policy_chunk",
)

KB_SCHEMA_SETUP_GUIDE = (
    "知识库数据表未初始化。请先执行 sql/001_kb_policy_schema.sql，"
    "如需确认 embedding 维度，再执行 sql/002_kb_policy_chunk_embedding_dimension_1024.sql。"
)


def find_missing_kb_tables(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    return [table for table in REQUIRED_KB_TABLES if not inspector.has_table(table)]


def is_kb_schema_ready(engine: Engine) -> bool:
    return not find_missing_kb_tables(engine)


def is_missing_kb_schema_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        ("undefinedtable" in message or "does not exist" in message)
        and "kb_policy_" in message
    )


def safe_find_missing_kb_tables(engine: Engine) -> list[str] | None:
    try:
        return find_missing_kb_tables(engine)
    except SQLAlchemyError:
        return None
