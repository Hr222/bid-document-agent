from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.infrastructure.persistence.models import (
    PolicyChunk,
    PolicyDocument,
    PolicySection,
    PolicyVersion,
)
from app.infrastructure.persistence.repositories.policy_persistence_gateway import (
    PolicyPersistenceGateway,
)
from app.shared.config import settings
from tests.support.db_test_utils import SchemaHarness


def _embedding(primary_index: int, magnitude: float = 1.0) -> list[float]:
    values = [0.0] * settings.vector_dimensions
    values[primary_index] = magnitude
    return values


def _apply_hnsw_index_script(harness: SchemaHarness) -> None:
    script_path = (
        Path(__file__).resolve().parents[2]
        / "sql"
        / "004_kb_policy_chunk_embedding_hnsw.sql"
    )
    script = script_path.read_text(encoding="utf-8")
    with harness.test_engine.begin() as conn:
        conn.exec_driver_sql(script)


def _seed_policy_chunks(harness: SchemaHarness) -> None:
    session = harness.session_local()
    try:
        document = PolicyDocument(
            policy_name="人事管理制度",
            policy_category="人事制度",
            responsible_department="人力资源部",
            status="draft",
        )
        session.add(document)
        session.flush()

        version = PolicyVersion(
            policy_id=document.id,
            version_seq=1,
            version_label="2025",
            source_year=2025,
            revision_type="initial",
            version_status="draft",
            source_path="/tmp/hr-policy.docx",
            file_name="hr-policy.docx",
            file_ext=".docx",
            file_hash="hash-hr-policy",
            is_scanned=False,
            parse_method="direct",
            raw_text="raw",
            clean_text="clean",
            parser_status="parsed",
        )
        session.add(version)
        session.flush()

        document.latest_version_id = version.id

        section = PolicySection(
            version_id=version.id,
            section_title="第二条",
            section_path="总则 / 第二条",
            section_level=1,
            section_order=1,
            section_text="本制度适用于公司全体员工。",
            review_status="pending",
        )
        session.add(section)
        session.flush()

        session.add_all(
            [
                PolicyChunk(
                    version_id=version.id,
                    section_id=section.id,
                    chunk_index=0,
                    page_no=1,
                    chunk_text="本制度适用于公司全体员工。",
                    embedding=_embedding(0, 1.0),
                    chunk_metadata={},
                ),
                PolicyChunk(
                    version_id=version.id,
                    section_id=section.id,
                    chunk_index=1,
                    page_no=1,
                    chunk_text="员工试用期为六个月。",
                    embedding=_embedding(1, 1.0),
                    chunk_metadata={},
                ),
            ]
        )
        session.commit()
    finally:
        session.close()


def test_hnsw_index_script_creates_embedding_index() -> None:
    harness = SchemaHarness("retrieval_hnsw_idx")
    harness.create_schema()
    try:
        _apply_hnsw_index_script(harness)
        with harness.test_engine.connect() as conn:
            index_name = conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = current_schema()
                      AND indexname = 'idx_kb_policy_chunk_embedding_hnsw_cosine'
                    """
                )
            ).scalar()
        assert index_name == "idx_kb_policy_chunk_embedding_hnsw_cosine"
    finally:
        harness.drop_schema()


def test_repository_search_chunks_hnsw_returns_hits_and_sets_ef_search() -> None:
    harness = SchemaHarness("retrieval_hnsw_query")
    harness.create_schema()
    try:
        _apply_hnsw_index_script(harness)
        _seed_policy_chunks(harness)

        session = harness.session_local()
        try:
            repository = PolicyPersistenceGateway(session)
            hits = repository.search_chunks_hnsw(
                query_embedding=_embedding(0, 1.0),
                top_k=2,
            )
            current_ef_search = session.execute(
                text("SELECT current_setting('hnsw.ef_search')")
            ).scalar_one()
        finally:
            session.close()

        assert [hit.chunk_text for hit in hits] == [
            "本制度适用于公司全体员工。",
            "员工试用期为六个月。",
        ]
        assert hits[0].score >= hits[1].score
        assert current_ef_search == str(settings.vector_search_hnsw_ef_search)
    finally:
        harness.drop_schema()
