from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BIGINT, INTEGER, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base


class PolicyChunk(Base):
    """面向检索的切块实体，保存向量与检索元数据。"""

    __tablename__ = "kb_policy_chunk"

    # 切块主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 所属版本 ID
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 所属章节 ID；章节不存在时允许置空
    section_id: Mapped[int | None] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_section.id", ondelete="SET NULL"),
    )

    # 版本内切块顺序号
    chunk_index: Mapped[int] = mapped_column(INTEGER, nullable=False)

    # 切块来源页码
    page_no: Mapped[int | None] = mapped_column(INTEGER)

    # 切块正文
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # 向量字段，维度与 embedding 模型配置保持一致
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.vector_dimensions),
        nullable=False,
    )

    # 检索元数据，保存章节、来源 block 等追踪信息
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # 记录创建时间
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # 记录更新时间
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    version: Mapped["PolicyVersion"] = relationship(back_populates="chunks")
    section: Mapped["PolicySection | None"] = relationship(back_populates="chunks")
