from __future__ import annotations

from datetime import datetime

from sqlalchemy import BIGINT, BOOLEAN, DATE, INTEGER, JSON, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyDocument(Base):
    """Knowledge-source root entity for one policy or制度主档."""

    __tablename__ = "kb_policy_document"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    policy_code: Mapped[str | None] = mapped_column(Text, unique=True)
    policy_name: Mapped[str] = mapped_column(Text, nullable=False)
    policy_category: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_department: Mapped[str | None] = mapped_column(Text)
    current_version_id: Mapped[int | None] = mapped_column(BIGINT)
    latest_version_id: Mapped[int | None] = mapped_column(BIGINT)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
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

    versions: Mapped[list["PolicyVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class PolicyVersion(Base):
    """Version entity for one concrete source file under a policy document."""

    __tablename__ = "kb_policy_version"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    policy_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_document.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_seq: Mapped[int] = mapped_column(INTEGER, nullable=False)
    version_label: Mapped[str] = mapped_column(Text, nullable=False)
    source_year: Mapped[int | None] = mapped_column(INTEGER)
    source_document_date: Mapped[datetime | None] = mapped_column(DATE)
    issued_at: Mapped[datetime | None] = mapped_column(DATE)
    effective_date: Mapped[datetime | None] = mapped_column(DATE)
    expired_at: Mapped[datetime | None] = mapped_column(DATE)
    previous_version_id: Mapped[int | None] = mapped_column(BIGINT)
    revision_type: Mapped[str] = mapped_column(Text, nullable=False, default="revise")
    version_status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    change_summary: Mapped[str | None] = mapped_column(Text)
    change_reason: Mapped[str | None] = mapped_column(Text)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_ext: Mapped[str | None] = mapped_column(Text)
    file_hash: Mapped[str | None] = mapped_column(Text)
    is_scanned: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=False)
    parse_method: Mapped[str] = mapped_column(Text, nullable=False, default="direct")
    raw_text: Mapped[str | None] = mapped_column(Text)
    clean_text: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(INTEGER)
    parser_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    ingested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
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

    document: Mapped["PolicyDocument"] = relationship(back_populates="versions")
    sections: Mapped[list["PolicySection"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
    )


class PolicySection(Base):
    """Structured section entity after chapter/article splitting."""

    __tablename__ = "kb_policy_section"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_section_id: Mapped[int | None] = mapped_column(
        BIGINT,
        ForeignKey("kb_policy_section.id", ondelete="CASCADE"),
    )
    section_no: Mapped[str | None] = mapped_column(Text)
    section_title: Mapped[str | None] = mapped_column(Text)
    section_level: Mapped[int] = mapped_column(INTEGER, nullable=False, default=1)
    section_path: Mapped[str | None] = mapped_column(Text)
    section_order: Mapped[int] = mapped_column(INTEGER, nullable=False, default=0)
    page_start: Mapped[int | None] = mapped_column(INTEGER)
    page_end: Mapped[int | None] = mapped_column(INTEGER)
    section_text: Mapped[str] = mapped_column(Text, nullable=False)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    review_note: Mapped[str | None] = mapped_column(Text)
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

    version: Mapped["PolicyVersion"] = relationship(back_populates="sections")
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )
