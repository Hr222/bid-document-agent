from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.policy import PolicyChunk, PolicyDocument, PolicySection, PolicyVersion
from app.schemas.policy_pipeline import ChunkItem, CleanedTextResult, RegisteredFileInfo, SectionSplitItem


@dataclass(slots=True)
class PersistedPolicyRecords:
    """聚合返回本次落库产生的记录。"""

    document: PolicyDocument
    version: PolicyVersion
    sections: list[PolicySection]
    chunks: list[PolicyChunk]


class PolicyRepository:
    """制度知识库落库仓储。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_document_version_sections_and_chunks(
        self,
        *,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
        registered_file: RegisteredFileInfo,
        version_label: str,
        parse_method: str,
        parser_status: str,
        is_scanned: bool,
        raw_text: str,
        cleaned_text: CleanedTextResult,
        sections: list[SectionSplitItem],
        chunks: list[ChunkItem],
    ) -> PersistedPolicyRecords:
        """在一个事务里保存 document、version、section、chunk。"""
        try:
            document = self._get_or_create_document(
                policy_name=policy_name,
                policy_category=policy_category,
                responsible_department=responsible_department,
            )
            version = self._create_version(
                document=document,
                registered_file=registered_file,
                version_label=version_label,
                parse_method=parse_method,
                parser_status=parser_status,
                is_scanned=is_scanned,
                raw_text=raw_text,
                cleaned_text=cleaned_text,
            )
            persisted_sections = self._create_sections(version=version, sections=sections)
            persisted_chunks = self._create_chunks(
                version=version,
                sections=persisted_sections,
                chunks=chunks,
            )
            document.latest_version_id = version.id

            self.session.add(document)
            self.session.commit()
            self.session.refresh(document)
            self.session.refresh(version)
            return PersistedPolicyRecords(
                document=document,
                version=version,
                sections=persisted_sections,
                chunks=persisted_chunks,
            )
        except Exception:
            self.session.rollback()
            raise

    def _get_or_create_document(
        self,
        *,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
    ) -> PolicyDocument:
        statement = (
            select(PolicyDocument)
            .where(PolicyDocument.policy_name == policy_name)
            .where(PolicyDocument.policy_category == policy_category)
            .limit(1)
        )
        document = self.session.scalar(statement)
        if document is not None:
            if responsible_department and not document.responsible_department:
                document.responsible_department = responsible_department
            return document

        document = PolicyDocument(
            policy_code=None,
            policy_name=policy_name,
            policy_category=policy_category,
            responsible_department=responsible_department,
            current_version_id=None,
            latest_version_id=None,
            status="draft",
        )
        self.session.add(document)
        self.session.flush()
        return document

    def _create_version(
        self,
        *,
        document: PolicyDocument,
        registered_file: RegisteredFileInfo,
        version_label: str,
        parse_method: str,
        parser_status: str,
        is_scanned: bool,
        raw_text: str,
        cleaned_text: CleanedTextResult,
    ) -> PolicyVersion:
        current_max_seq = self.session.scalar(
            select(func.max(PolicyVersion.version_seq)).where(
                PolicyVersion.policy_id == document.id
            )
        )
        next_seq = (current_max_seq or 0) + 1
        previous_version_id = document.latest_version_id
        resolved_version_label = self._ensure_unique_version_label(
            policy_id=document.id,
            version_label=version_label,
        )

        version = PolicyVersion(
            policy_id=document.id,
            version_seq=next_seq,
            version_label=resolved_version_label,
            source_year=registered_file.source_modified_at.year,
            source_document_date=None,
            issued_at=None,
            effective_date=None,
            expired_at=None,
            previous_version_id=previous_version_id,
            revision_type="initial" if previous_version_id is None else "revise",
            version_status="draft",
            change_summary=None,
            change_reason=None,
            source_path=registered_file.source_path,
            file_name=registered_file.file_name,
            file_ext=registered_file.extension,
            file_hash=registered_file.sha256,
            is_scanned=is_scanned,
            parse_method=parse_method,
            raw_text=raw_text,
            clean_text=cleaned_text.clean_text,
            page_count=cleaned_text.page_count,
            parser_status=parser_status,
        )
        self.session.add(version)
        self.session.flush()
        return version

    def _ensure_unique_version_label(self, *, policy_id: int, version_label: str) -> str:
        normalized = version_label.strip()
        if not normalized:
            raise ValueError("落库前版本标签不能为空。")

        existing_labels = {
            label
            for label in self.session.scalars(
                select(PolicyVersion.version_label).where(PolicyVersion.policy_id == policy_id)
            )
        }
        if normalized not in existing_labels:
            return normalized

        suffix = 2
        while True:
            candidate = f"{normalized}-{suffix}"
            if candidate not in existing_labels:
                return candidate
            suffix += 1

    def _create_sections(
        self,
        *,
        version: PolicyVersion,
        sections: list[SectionSplitItem],
    ) -> list[PolicySection]:
        persisted_sections: list[PolicySection] = []
        for item in sections:
            section = PolicySection(
                version_id=version.id,
                parent_section_id=None,
                section_no=item.section_no,
                section_title=item.section_title,
                section_level=item.section_level,
                section_path=item.section_path,
                section_order=item.section_order,
                page_start=item.page_start,
                page_end=item.page_end,
                section_text=item.section_text,
                review_status="pending",
            )
            self.session.add(section)
            persisted_sections.append(section)

        self.session.flush()
        return persisted_sections

    def _create_chunks(
        self,
        *,
        version: PolicyVersion,
        sections: list[PolicySection],
        chunks: list[ChunkItem],
    ) -> list[PolicyChunk]:
        # 先拿到 section 的真实主键，再补进 chunk metadata。
        section_by_order = {section.section_order: section for section in sections}
        persisted_chunks: list[PolicyChunk] = []

        for item in chunks:
            if item.embedding is None:
                raise RuntimeError("切块在落库前缺少向量。")

            section = section_by_order.get(item.section_order)
            metadata = {
                **item.metadata,
                "section_id": section.id if section is not None else None,
            }
            chunk = PolicyChunk(
                version_id=version.id,
                section_id=section.id if section is not None else None,
                chunk_index=item.chunk_index,
                page_no=item.page_no,
                chunk_text=item.chunk_text,
                embedding=item.embedding,
                chunk_metadata=metadata,
            )
            self.session.add(chunk)
            persisted_chunks.append(chunk)

        self.session.flush()
        return persisted_chunks
