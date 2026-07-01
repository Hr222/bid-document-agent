from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    PolicyBlock,
    PolicyChunk,
    PolicyDocument,
    PolicySection,
    PolicyVersion,
)
from app.schemas import (
    ChunkItem,
    CleanedTextResult,
    ParsedBlock,
    RegisteredFileInfo,
    SectionSplitItem,
)


@dataclass(slots=True)
class PersistedPolicyRecords:
    """聚合返回本次落库产生的记录。"""

    document: PolicyDocument
    version: PolicyVersion
    blocks: list[PolicyBlock]
    sections: list[PolicySection]
    chunks: list[PolicyChunk]


@dataclass(slots=True)
class RetrievedPolicyChunk:
    document_id: int
    version_id: int
    chunk_id: int
    policy_name: str
    policy_category: str
    responsible_department: str | None
    version_label: str
    section_title: str | None
    section_path: str | None
    page_no: int | None
    chunk_text: str
    score: float


@dataclass(slots=True)
class PolicyDocumentListItem:
    document_id: int
    policy_name: str
    policy_category: str
    responsible_department: str | None
    latest_version_id: int | None
    latest_version_label: str | None


class PolicyRepository:
    """制度知识库落库仓储。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def document_exists(self, document_id: int) -> bool:
        return self.session.get(PolicyDocument, document_id) is not None

    def save_document_version_blocks_sections_and_chunks(
        self,
        *,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
        target_document_id: int | None,
        registered_file: RegisteredFileInfo,
        version_label: str,
        parse_method: str,
        parser_status: str,
        is_scanned: bool,
        raw_text: str,
        cleaned_text: CleanedTextResult,
        blocks: list[ParsedBlock],
        sections: list[SectionSplitItem],
        chunks: list[ChunkItem],
    ) -> PersistedPolicyRecords:
        """在一个事务里保存 document、version、block、section、chunk。"""
        try:
            document = self._get_or_create_document(
                target_document_id=target_document_id,
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
            persisted_blocks = self._create_blocks(version=version, blocks=blocks)
            persisted_sections = self._create_sections(version=version, sections=sections)
            persisted_chunks = self._create_chunks(
                version=version,
                blocks=persisted_blocks,
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
                blocks=persisted_blocks,
                sections=persisted_sections,
                chunks=persisted_chunks,
            )
        except Exception:
            self.session.rollback()
            raise

    def list_documents(
        self,
        *,
        search: str | None = None,
        policy_category: str | None = None,
        limit: int = 50,
    ) -> list[PolicyDocumentListItem]:
        statement = (
            select(
                PolicyDocument.id.label("document_id"),
                PolicyDocument.policy_name.label("policy_name"),
                PolicyDocument.policy_category.label("policy_category"),
                PolicyDocument.responsible_department.label("responsible_department"),
                PolicyDocument.latest_version_id.label("latest_version_id"),
                PolicyVersion.version_label.label("latest_version_label"),
            )
            .outerjoin(PolicyVersion, PolicyVersion.id == PolicyDocument.latest_version_id)
            .order_by(PolicyDocument.updated_at.desc(), PolicyDocument.id.desc())
            .limit(limit)
        )

        if policy_category:
            statement = statement.where(PolicyDocument.policy_category == policy_category)
        if search and search.strip():
            statement = statement.where(PolicyDocument.policy_name.ilike(f"%{search.strip()}%"))

        rows = self.session.execute(statement).all()
        return [
            PolicyDocumentListItem(
                document_id=row.document_id,
                policy_name=row.policy_name,
                policy_category=row.policy_category,
                responsible_department=row.responsible_department,
                latest_version_id=row.latest_version_id,
                latest_version_label=row.latest_version_label,
            )
            for row in rows
        ]

    def search_chunks(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]:
        distance_expr = PolicyChunk.embedding.cosine_distance(query_embedding)

        statement = (
            select(
                PolicyDocument.id.label("document_id"),
                PolicyVersion.id.label("version_id"),
                PolicyChunk.id.label("chunk_id"),
                PolicyDocument.policy_name.label("policy_name"),
                PolicyDocument.policy_category.label("policy_category"),
                PolicyDocument.responsible_department.label("responsible_department"),
                PolicyVersion.version_label.label("version_label"),
                PolicySection.section_title.label("section_title"),
                PolicySection.section_path.label("section_path"),
                PolicyChunk.page_no.label("page_no"),
                PolicyChunk.chunk_text.label("chunk_text"),
                distance_expr.label("distance"),
            )
            .join(PolicyVersion, PolicyVersion.id == PolicyChunk.version_id)
            .join(PolicyDocument, PolicyDocument.id == PolicyVersion.policy_id)
            .outerjoin(PolicySection, PolicySection.id == PolicyChunk.section_id)
            .where(PolicyVersion.version_status.in_(("draft", "approved", "active")))
        )

        if not include_history:
            statement = statement.where(PolicyDocument.latest_version_id == PolicyVersion.id)
        if policy_category:
            statement = statement.where(PolicyDocument.policy_category == policy_category)
        if responsible_department:
            statement = statement.where(
                PolicyDocument.responsible_department == responsible_department
            )
        if document_id is not None:
            statement = statement.where(PolicyDocument.id == document_id)

        rows = self.session.execute(statement.order_by(distance_expr.asc()).limit(top_k)).all()

        results: list[RetrievedPolicyChunk] = []
        for row in rows:
            distance = float(row.distance)
            score = max(0.0, 1.0 - distance)
            results.append(
                RetrievedPolicyChunk(
                    document_id=row.document_id,
                    version_id=row.version_id,
                    chunk_id=row.chunk_id,
                    policy_name=row.policy_name,
                    policy_category=row.policy_category,
                    responsible_department=row.responsible_department,
                    version_label=row.version_label,
                    section_title=row.section_title,
                    section_path=row.section_path,
                    page_no=row.page_no,
                    chunk_text=row.chunk_text,
                    score=score,
                )
            )
        return results

    def _get_or_create_document(
        self,
        *,
        target_document_id: int | None,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
    ) -> PolicyDocument:
        if target_document_id is not None:
            document = self.session.get(PolicyDocument, target_document_id)
            if document is None:
                raise ValueError(f"指定的制度主档不存在：{target_document_id}")
            return document

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

    def _create_blocks(
        self,
        *,
        version: PolicyVersion,
        blocks: list[ParsedBlock],
    ) -> list[PolicyBlock]:
        persisted_blocks: list[PolicyBlock] = []
        for item in blocks:
            block = PolicyBlock(
                version_id=version.id,
                block_index=item.order,
                page_no=item.page_no,
                block_type=item.block_type,
                source_method=item.source,
                text=item.text,
                layout_hint=item.layout_hint,
                block_metadata=self._sanitize_block_metadata(item.metadata),
            )
            self.session.add(block)
            persisted_blocks.append(block)

        self.session.flush()
        return persisted_blocks

    def _sanitize_block_metadata(self, metadata: dict) -> dict:
        # 图像原始字节和 PDF 渲染标记仅用于运行期 OCR，不进入正式存储。
        return {
            key: value
            for key, value in metadata.items()
            if key not in {"image_bytes", "pdf_page_render"}
        }

    def _create_chunks(
        self,
        *,
        version: PolicyVersion,
        blocks: list[PolicyBlock],
        sections: list[PolicySection],
        chunks: list[ChunkItem],
    ) -> list[PolicyChunk]:
        # 先拿到 section / block 的真实主键，再补进 chunk metadata。
        block_by_index = {block.block_index: block for block in blocks}
        section_by_order = {section.section_order: section for section in sections}
        persisted_chunks: list[PolicyChunk] = []

        for item in chunks:
            if item.embedding is None:
                raise RuntimeError("切块在落库前缺少向量。")

            section = section_by_order.get(item.section_order)
            start_block = (
                block_by_index.get(item.source_block_start)
                if item.source_block_start is not None
                else None
            )
            end_block = (
                block_by_index.get(item.source_block_end)
                if item.source_block_end is not None
                else None
            )
            metadata = {
                **item.metadata,
                "section_id": section.id if section is not None else None,
                "source_block_start": start_block.id if start_block is not None else None,
                "source_block_end": end_block.id if end_block is not None else None,
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
