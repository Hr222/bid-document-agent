from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BIGINT, BOOLEAN, DATE, INTEGER, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base


class PolicyDocument(Base):
    """制度类知识源的主档实体。"""

    __tablename__ = "kb_policy_document"

    # 主档主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 制度编码，首版 MVP 允许为空
    policy_code: Mapped[str | None] = mapped_column(Text, unique=True)

    # 制度名称，当前首版直接取清洗后的文件名
    policy_name: Mapped[str] = mapped_column(Text, nullable=False)

    # 制度分类，例如“管理制度”
    policy_category: Mapped[str] = mapped_column(Text, nullable=False)

    # 归口负责部门，可为空
    responsible_department: Mapped[str | None] = mapped_column(Text)

    # 当前生效版本 ID，首版导入时固定为空
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


class PolicyVersion(Base):
    """制度主档下某个具体源文件对应的版本实体。"""

    __tablename__ = "kb_policy_version"

    # 版本主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 所属主档 ID
    policy_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_document.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 同一主档下的递增版本序号，例如 1、2、3
    version_seq: Mapped[int] = mapped_column(INTEGER, nullable=False)

    # 版本标签，优先取请求值，否则取源文件最后修改日
    version_label: Mapped[str] = mapped_column(Text, nullable=False)

    # 源文件年份，通常取文件最后修改时间的年份
    source_year: Mapped[int | None] = mapped_column(INTEGER)

    # 源文件正文中的制度日期，首版 MVP 暂不抽取
    source_document_date: Mapped[date | None] = mapped_column(DATE)

    # 发布日期，首版 MVP 暂不抽取
    issued_at: Mapped[date | None] = mapped_column(DATE)

    # 生效日期，首版 MVP 暂不抽取
    effective_date: Mapped[date | None] = mapped_column(DATE)

    # 失效日期，首版 MVP 暂不抽取
    expired_at: Mapped[date | None] = mapped_column(DATE)

    # 上一个版本 ID，用于串起版本链
    previous_version_id: Mapped[int | None] = mapped_column(BIGINT)

    # 修订类型：首版为 initial，后续通常为 revise
    revision_type: Mapped[str] = mapped_column(Text, nullable=False, default="revise")

    # 版本状态，首版 MVP 默认使用 draft
    version_status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")

    # 与上一版相比的变更摘要，首版 MVP 暂不填写
    change_summary: Mapped[str | None] = mapped_column(Text)

    # 本次修订原因，首版 MVP 暂不填写
    change_reason: Mapped[str | None] = mapped_column(Text)

    # 源文件原始路径
    source_path: Mapped[str] = mapped_column(Text, nullable=False)

    # 源文件文件名
    file_name: Mapped[str] = mapped_column(Text, nullable=False)

    # 源文件扩展名，例如 .docx / .pdf
    file_ext: Mapped[str | None] = mapped_column(Text)

    # 源文件哈希，用于去重和追踪
    file_hash: Mapped[str | None] = mapped_column(Text)

    # 是否疑似扫描件
    is_scanned: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=False)

    # 解析方式，例如 docx / pdf / direct / ocr 等
    parse_method: Mapped[str] = mapped_column(Text, nullable=False, default="direct")

    # 原始抽取文本
    raw_text: Mapped[str | None] = mapped_column(Text)

    # 清洗后的全文文本
    clean_text: Mapped[str | None] = mapped_column(Text)

    # 页数；DOCX 可能为空，PDF 一般有值
    page_count: Mapped[int | None] = mapped_column(INTEGER)

    # 解析状态，例如 pending / parsed / failed
    parser_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")

    # 版本入库时间
    ingested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # 审核完成时间，首版 MVP 暂未使用
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # 审批通过时间，首版 MVP 暂未使用
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

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

    document: Mapped["PolicyDocument"] = relationship(back_populates="versions")
    sections: Mapped[list["PolicySection"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
    )


class PolicySection(Base):
    """按章/节/条拆分后的结构化章节实体。"""

    __tablename__ = "kb_policy_section"

    # 章节主键 ID
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    # 所属版本 ID
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 父章节 ID，当前首版 MVP 暂未真正构建树关系
    parent_section_id: Mapped[int | None] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_section.id", ondelete="CASCADE"),
    )

    # 章节编号，例如“第一章”“第三条”
    section_no: Mapped[str | None] = mapped_column(Text)

    # 章节标题，例如“总则”
    section_title: Mapped[str | None] = mapped_column(Text)

    # 章节层级：1=章，2=节，3=条
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


class PolicyChunk(Base):
    """Retrieval-oriented chunk with embedding and metadata."""

    __tablename__ = "kb_policy_chunk"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[int | None] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_section.id", ondelete="SET NULL"),
    )
    chunk_index: Mapped[int] = mapped_column(INTEGER, nullable=False)
    page_no: Mapped[int | None] = mapped_column(INTEGER)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.vector_dimensions),
        nullable=False,
    )
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    version: Mapped["PolicyVersion"] = relationship(back_populates="chunks")
    section: Mapped["PolicySection | None"] = relationship(back_populates="chunks")
