from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.models import (
    PolicyBlock,
    PolicyChunk,
    PolicyDocument,
    PolicySection,
    PolicyVersion,
)
from app.modules.ingestion.contracts import (
    ChunkItem,
    CleanedTextResult,
    ParsedBlock,
    RegisteredFileInfo,
    SectionSplitItem,
)
from app.modules.knowledge.retrieval.contracts import RetrievedPolicyChunk
from app.shared.config import settings


@dataclass(slots=True)
class PersistedPolicyRecords:
    """聚合返回本次落库产生的记录。"""

    document: PolicyDocument
    version: PolicyVersion
    blocks: list[PolicyBlock]
    sections: list[PolicySection]
    chunks: list[PolicyChunk]


@dataclass(slots=True)
class PolicyDocumentListItem:
    document_id: int
    policy_name: str
    policy_category: str
    responsible_department: str | None
    latest_version_id: int | None
    latest_version_label: str | None


class PolicyPersistenceGateway:
    """PostgreSQL/pgvector 的内部持久化网关。

    读写仓储分别组合本网关，对外只暴露各自的知识端口。
    """

    def __init__(self, session: Session) -> None:
        self.session = session

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
        # 兼容旧调用入口；Milestone C 起主链路应改走显式策略方法。
        return self.search_chunks_exact(
            query_embedding=query_embedding,
            top_k=top_k,
            policy_category=policy_category,
            responsible_department=responsible_department,
            document_id=document_id,
            include_history=include_history,
        )

    def search_chunks_exact(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]:
        return self._search_chunks_by_vector_distance(
            query_embedding=query_embedding,
            top_k=top_k,
            policy_category=policy_category,
            responsible_department=responsible_department,
            document_id=document_id,
            include_history=include_history,
        )

    def search_chunks_hnsw(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]:
        # 对当前事务局部设置 ef_search，避免把实验参数写死在 SQL 或全局会话里。
        self.session.execute(
            select(
                func.set_config(
                    "hnsw.ef_search",
                    str(settings.vector_search_hnsw_ef_search),
                    True,
                )
            )
        )
        return self._search_chunks_by_vector_distance(
            query_embedding=query_embedding,
            top_k=top_k,
            policy_category=policy_category,
            responsible_department=responsible_department,
            document_id=document_id,
            include_history=include_history,
        )

    def search_chunks_by_keywords(
        self,
        *,
        focus_query: str | None,
        keywords: list[str],
        priority_keywords: list[str] | None = None,
        top_k: int,
        policy_category: str | None = None,
        responsible_department: str | None = None,
        document_id: int | None = None,
        include_history: bool = False,
    ) -> list[RetrievedPolicyChunk]:
        # 关键词召回先走最小可用版本：不引入 BM25，仅基于命中位置做轻量打分。
        normalized_focus_query = (focus_query or "").strip().lower()
        normalized_keywords = [keyword.strip().lower() for keyword in keywords if keyword.strip()]
        normalized_priority_keywords = [
            keyword.strip().lower() for keyword in (priority_keywords or []) if keyword.strip()
        ]
        priority_keyword_set = set(normalized_priority_keywords)
        if not normalized_focus_query and not normalized_keywords:
            return []

        # 同时检查正文、制度名、章节标题、章节路径，尽量覆盖条款类问法。
        chunk_text_expr = func.lower(PolicyChunk.chunk_text)
        policy_name_expr = func.lower(PolicyDocument.policy_name)
        section_title_expr = func.lower(func.coalesce(PolicySection.section_title, ""))
        section_path_expr = func.lower(func.coalesce(PolicySection.section_path, ""))

        raw_score_expr = literal(0.0)

        if normalized_focus_query:
            raw_score_expr = raw_score_expr + case(
                (chunk_text_expr.contains(normalized_focus_query), 0.42),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (policy_name_expr.contains(normalized_focus_query), 0.25),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (section_title_expr.contains(normalized_focus_query), 0.20),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (section_path_expr.contains(normalized_focus_query), 0.15),
                else_=0.0,
            )

        for keyword in normalized_keywords:
            # 词越长通常语义越完整，因此给更高权重；短词只保留较弱加分，避免噪声过大。
            keyword_weights = self._resolve_keyword_weights(
                keyword,
                is_priority=keyword in priority_keyword_set,
            )

            raw_score_expr = raw_score_expr + case(
                (chunk_text_expr.contains(keyword), keyword_weights["chunk_text"]),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (policy_name_expr.contains(keyword), keyword_weights["policy_name"]),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (section_title_expr.contains(keyword), keyword_weights["section_title"]),
                else_=0.0,
            )
            raw_score_expr = raw_score_expr + case(
                (section_path_expr.contains(keyword), keyword_weights["section_path"]),
                else_=0.0,
            )

        statement = (
            select(
                PolicyDocument.id.label("document_id"),
                PolicyVersion.id.label("version_id"),
                PolicyChunk.id.label("chunk_id"),
                PolicyDocument.policy_name.label("policy_name"),
                PolicyDocument.policy_category.label("policy_category"),
                PolicyDocument.responsible_department.label("responsible_department"),
                PolicyVersion.version_label.label("version_label"),
                PolicyVersion.source_path.label("source_path"),
                PolicyVersion.file_name.label("file_name"),
                PolicySection.section_title.label("section_title"),
                PolicySection.section_path.label("section_path"),
                PolicyChunk.page_no.label("page_no"),
                PolicyChunk.chunk_text.label("chunk_text"),
                raw_score_expr.label("raw_score"),
            )
            .join(PolicyVersion, PolicyVersion.id == PolicyChunk.version_id)
            .join(PolicyDocument, PolicyDocument.id == PolicyVersion.policy_id)
            .outerjoin(PolicySection, PolicySection.id == PolicyChunk.section_id)
            .where(
                PolicyVersion.version_status.in_(("draft", "approved", "active"))
            )
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

        # 只返回真正命中过关键词的切块，并按关键词分数稳定排序。
        rows = self.session.execute(
            statement.where(raw_score_expr > 0.0)
            .order_by(raw_score_expr.desc(), PolicyChunk.id.asc())
            .limit(top_k)
        ).all()

        results: list[RetrievedPolicyChunk] = []
        for row in rows:
            score = min(1.0, float(row.raw_score))
            debug_details = self._build_keyword_match_debug_details(
                chunk_text=row.chunk_text,
                policy_name=row.policy_name,
                section_title=row.section_title,
                section_path=row.section_path,
                focus_query=normalized_focus_query,
                keywords=normalized_keywords,
                priority_keywords=normalized_priority_keywords,
            )
            results.append(
                RetrievedPolicyChunk(
                    document_id=row.document_id,
                    version_id=row.version_id,
                    chunk_id=row.chunk_id,
                    policy_name=row.policy_name,
                    policy_category=row.policy_category,
                    responsible_department=row.responsible_department,
                    version_label=row.version_label,
                    source_path=row.source_path,
                    file_name=row.file_name,
                    section_title=row.section_title,
                    section_path=row.section_path,
                    page_no=row.page_no,
                    chunk_text=row.chunk_text,
                    score=score,
                    retrieval_source="keyword",
                    score_breakdown={"keyword": score},
                    debug_details=debug_details,
                )
            )
        return results

    def _search_chunks_by_vector_distance(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        policy_category: str | None,
        responsible_department: str | None,
        document_id: int | None,
        include_history: bool,
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
                PolicyVersion.source_path.label("source_path"),
                PolicyVersion.file_name.label("file_name"),
                PolicySection.section_title.label("section_title"),
                PolicySection.section_path.label("section_path"),
                PolicyChunk.page_no.label("page_no"),
                PolicyChunk.chunk_text.label("chunk_text"),
                distance_expr.label("distance"),
            )
            .join(PolicyVersion, PolicyVersion.id == PolicyChunk.version_id)
            .join(PolicyDocument, PolicyDocument.id == PolicyVersion.policy_id)
            .outerjoin(PolicySection, PolicySection.id == PolicyChunk.section_id)
            .where(
                PolicyVersion.version_status.in_(("draft", "approved", "active"))
            )
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
        return self._build_vector_search_results(rows)

    def _build_vector_search_results(self, rows: list) -> list[RetrievedPolicyChunk]:
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
                    source_path=row.source_path,
                    file_name=row.file_name,
                    section_title=row.section_title,
                    section_path=row.section_path,
                    page_no=row.page_no,
                    chunk_text=row.chunk_text,
                    score=score,
                    retrieval_source="vector",
                    score_breakdown={"vector": score},
                    debug_details={},
                )
            )
        return results

    def _build_keyword_match_debug_details(
        self,
        *,
        chunk_text: str,
        policy_name: str,
        section_title: str | None,
        section_path: str | None,
        focus_query: str,
        keywords: list[str],
        priority_keywords: list[str],
    ) -> dict[str, str | int | float | bool | None]:
        lower_chunk_text = chunk_text.lower()
        lower_policy_name = policy_name.lower()
        lower_section_title = (section_title or "").lower()
        lower_section_path = (section_path or "").lower()
        priority_keyword_set = set(priority_keywords)

        matched_fields: list[str] = []
        matched_keywords: list[str] = []
        matched_priority_keywords: list[str] = []
        score_terms: list[str] = []

        def append_field(field_name: str) -> None:
            if field_name not in matched_fields:
                matched_fields.append(field_name)

        if focus_query:
            if focus_query in lower_chunk_text:
                append_field("chunk_text")
                score_terms.append("focus@chunk_text=0.42")
            if focus_query in lower_policy_name:
                append_field("policy_name")
                score_terms.append("focus@policy_name=0.25")
            if focus_query in lower_section_title:
                append_field("section_title")
                score_terms.append("focus@section_title=0.20")
            if focus_query in lower_section_path:
                append_field("section_path")
                score_terms.append("focus@section_path=0.15")

        for keyword in keywords:
            keyword_weights = self._resolve_keyword_weights(
                keyword,
                is_priority=keyword in priority_keyword_set,
            )
            keyword_matched = False
            if keyword in lower_chunk_text:
                append_field("chunk_text")
                score_terms.append(
                    f"{keyword}@chunk_text={keyword_weights['chunk_text']:.2f}"
                )
                keyword_matched = True
            if keyword in lower_policy_name:
                append_field("policy_name")
                score_terms.append(
                    f"{keyword}@policy_name={keyword_weights['policy_name']:.2f}"
                )
                keyword_matched = True
            if keyword in lower_section_title:
                append_field("section_title")
                score_terms.append(
                    f"{keyword}@section_title={keyword_weights['section_title']:.2f}"
                )
                keyword_matched = True
            if keyword in lower_section_path:
                append_field("section_path")
                score_terms.append(
                    f"{keyword}@section_path={keyword_weights['section_path']:.2f}"
                )
                keyword_matched = True
            if keyword_matched and keyword not in matched_keywords:
                matched_keywords.append(keyword)
            if (
                keyword_matched
                and keyword in priority_keyword_set
                and keyword not in matched_priority_keywords
            ):
                matched_priority_keywords.append(keyword)

        return {
            "matched_fields": ", ".join(matched_fields) or None,
            "matched_keywords": ", ".join(matched_keywords[:8]) or None,
            "matched_priority_keywords": ", ".join(matched_priority_keywords[:8]) or None,
            "keyword_score_terms": "; ".join(score_terms[:10]) or None,
        }

    def _resolve_keyword_weights(
        self,
        keyword: str,
        *,
        is_priority: bool = False,
    ) -> dict[str, float]:
        if len(keyword) >= 4:
            weights = {
                "chunk_text": 0.28,
                "policy_name": 0.18,
                "section_title": 0.14,
                "section_path": 0.10,
            }
        elif len(keyword) == 3:
            weights = {
                "chunk_text": 0.22,
                "policy_name": 0.14,
                "section_title": 0.12,
                "section_path": 0.08,
            }
        else:
            weights = {
                "chunk_text": 0.16,
                "policy_name": 0.10,
                "section_title": 0.08,
                "section_path": 0.06,
            }

        if not is_priority:
            return weights

        return {
            "chunk_text": round(min(0.42, weights["chunk_text"] + 0.08), 3),
            "policy_name": round(min(0.30, weights["policy_name"] + 0.08), 3),
            "section_title": round(min(0.24, weights["section_title"] + 0.05), 3),
            "section_path": round(min(0.20, weights["section_path"] + 0.04), 3),
        }

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
