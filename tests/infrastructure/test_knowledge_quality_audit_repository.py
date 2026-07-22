from __future__ import annotations

from app.infrastructure.persistence.models import (
    PolicyBlock,
    PolicyChunk,
    PolicyDocument,
    PolicySection,
    PolicyVersion,
)
from app.infrastructure.persistence.repositories.knowledge_quality_audit_repository import (
    KnowledgeQualityAuditRepository,
)
from app.shared.config import settings
from tests.support.db_test_utils import SchemaHarness


def _embedding() -> list[float]:
    values = [0.0] * settings.vector_dimensions
    values[0] = 1.0
    return values


def test_quality_audit_repository_reports_issues_without_writing(tmp_path) -> None:  # noqa: ANN001
    existing_file = tmp_path / "existing.docx"
    existing_file.write_bytes(b"fixture")

    harness = SchemaHarness("knowledge_audit")
    harness.create_schema()
    try:
        session = harness.session_local()
        try:
            document = PolicyDocument(
                policy_name="审计样例",
                policy_category="证明材料",
                status="draft",
            )
            session.add(document)
            session.flush()

            valid_version = PolicyVersion(
                policy_id=document.id,
                version_seq=1,
                version_label="2025",
                version_status="draft",
                source_path=str(existing_file),
                file_name=existing_file.name,
                file_ext=".docx",
                file_hash="same-hash",
                parse_method="direct",
                raw_text="原文",
                clean_text="清洗文本",
                parser_status="parsed",
            )
            invalid_version = PolicyVersion(
                policy_id=document.id,
                version_seq=2,
                version_label="2025",
                version_status="draft",
                source_path=str(tmp_path / "missing.pdf"),
                file_name="missing.pdf",
                file_ext=".pdf",
                file_hash="same-hash",
                parse_method="ocr",
                raw_text="",
                clean_text=None,
                parser_status="failed",
            )
            session.add_all([valid_version, invalid_version])
            session.flush()
            document.latest_version_id = invalid_version.id

            good_section = PolicySection(
                version_id=valid_version.id,
                section_no="第一条",
                section_title="总则",
                section_path="总则",
                section_text="有效正文",
            )
            bad_section = PolicySection(
                version_id=invalid_version.id,
                section_text="仍有正文但缺少章节标识",
            )
            session.add_all([good_section, bad_section])
            session.flush()
            session.add(
                PolicyBlock(
                    version_id=invalid_version.id,
                    block_index=0,
                    page_no=1,
                    block_type="text",
                    source_method="direct",
                    text="",
                    layout_hint={},
                    block_metadata={},
                )
            )
            session.add_all(
                [
                    PolicyChunk(
                        version_id=valid_version.id,
                        section_id=good_section.id,
                        chunk_index=0,
                        page_no=1,
                        chunk_text="有效切块",
                        embedding=_embedding(),
                        chunk_metadata={},
                    ),
                    PolicyChunk(
                        version_id=invalid_version.id,
                        section_id=None,
                        chunk_index=0,
                        page_no=1,
                        chunk_text="",
                        embedding=_embedding(),
                        chunk_metadata={},
                    ),
                ]
            )
            session.commit()

            report = KnowledgeQualityAuditRepository(session).audit()

            assert report.document_count == 1
            assert report.version_count == 2
            assert report.section_count == 2
            assert report.block_count == 1
            assert report.chunk_count == 2
            assert report.latest_version_count == 1
            assert report.current_version_count == 0
            assert report.issue_counts == {
                "duplicate_file_hash": 2,
                "duplicate_version_label": 2,
                "empty_clean_text": 1,
                "empty_raw_text": 1,
                "empty_text_block": 1,
                "parser_not_parsed": 1,
                "section_missing_identifier": 1,
                "source_file_missing": 1,
                "chunk_missing_section": 1,
                "empty_chunk_text": 1,
            }
            assert not session.dirty
            assert not session.new
        finally:
            session.close()
    finally:
        harness.drop_schema()
