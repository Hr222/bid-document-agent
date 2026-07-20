from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, INTEGER, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.policy_chunk import PolicyChunk
    from app.infrastructure.persistence.models.policy_version import PolicyVersion


class PolicySection(Base):
    """按章、节、条拆分后的结构化章节实体。"""

    __tablename__ = "kb_policy_section"

    # 章节主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 所属版本 ID
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 父章节 ID；当前首版 MVP 暂未真正构建树关系
    parent_section_id: Mapped[int | None] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_section.id", ondelete="CASCADE"),
    )

    # 章节编号，例如“第一章”“第三条”
    section_no: Mapped[str | None] = mapped_column(Text)

    # 章节标题，例如“总则”
    section_title: Mapped[str | None] = mapped_column(Text)

    # 章节层级，1=章，2=节，3=条
    section_level: Mapped[int] = mapped_column(INTEGER, nullable=False, default=1)

    # 章节路径，例如“总则 / 第一条”
    section_path: Mapped[str | None] = mapped_column(Text)

    # 章节顺序号，用于保证按原文顺序输出
    section_order: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)

    # 起始页码；当前 MVP 有值时直接沿解析结果落库
    page_start: Mapped[int | None] = mapped_column(INTEGER)

    # 结束页码
    page_end: Mapped[int | None] = mapped_column(INTEGER)

    # 当前章节对应的正文文本
    section_text: Mapped[str] = mapped_column(Text, nullable=False)

    # 审核状态，首版统一落为 pending
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")

    # 审核备注，首版 MVP 暂未使用
    review_note: Mapped[str | None] = mapped_column(Text)

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

    version: Mapped["PolicyVersion"] = relationship(back_populates="sections")
    chunks: Mapped[list["PolicyChunk"]] = relationship(back_populates="section")
