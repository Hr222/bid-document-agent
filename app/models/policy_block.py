from __future__ import annotations

from datetime import datetime

from sqlalchemy import BIGINT, INTEGER, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyBlock(Base):
    """文档块实体，保存 OCR 回填前后的原子内容与顺序位置。"""

    __tablename__ = "kb_policy_block"

    # 文档块主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 所属版本 ID
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 文档流中的顺序号，对应 block 流 order
    block_index: Mapped[int] = mapped_column(INTEGER, nullable=False)

    # 块来源页码；DOCX 可能为空
    page_no: Mapped[int | None] = mapped_column(INTEGER)

    # 块类型，例如 text / table / image / page_break
    block_type: Mapped[str] = mapped_column(Text, nullable=False)

    # 文本来源，例如 direct / ocr / mixed
    source_method: Mapped[str] = mapped_column(Text, nullable=False)

    # 当前块正文；图片块在 OCR 前可以为空
    text: Mapped[str | None] = mapped_column(Text)

    # 布局提示，首版用于保留页内位置信息和宿主关系
    layout_hint: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # 扩展元数据；运行期大对象会在入库前剥离
    block_metadata: Mapped[dict] = mapped_column(
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

    version: Mapped["PolicyVersion"] = relationship(back_populates="blocks")
