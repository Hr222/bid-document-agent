from __future__ import annotations

from datetime import datetime

from sqlalchemy import BIGINT, TIMESTAMP, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyDocument(Base):
    """制度类知识源的主档实体。"""

    __tablename__ = "kb_policy_document"

    # 主档主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 制度编码；首版 MVP 允许为空
    policy_code: Mapped[str | None] = mapped_column(Text, unique=True)

    # 制度名称；当前首版直接取清洗后的文件名
    policy_name: Mapped[str] = mapped_column(Text, nullable=False)

    # 制度分类，例如“管理制度”
    policy_category: Mapped[str] = mapped_column(Text, nullable=False)

    # 归口责任部门，可为空
    responsible_department: Mapped[str | None] = mapped_column(Text)

    # 当前生效版本 ID；首版导入时固定为空
    current_version_id: Mapped[int | None] = mapped_column(BIGINT)

    # 当前最新收录版本 ID，不要求已经生效
    latest_version_id: Mapped[int | None] = mapped_column(BIGINT)

    # 主档状态，首版 MVP 默认使用 draft
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")

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

    versions: Mapped[list["PolicyVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
