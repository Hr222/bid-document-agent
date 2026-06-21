import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db_session
from app.core.config import settings
from app.main import app
from app.models import PolicyDocument, PolicySection, PolicyVersion


def _create_docx(path: Path, paragraphs: list[str]) -> None:
    from docx import Document

    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    document.save(path)


def _create_pdf_placeholder(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4 test")


def _build_pdf_parse_result(
    source_path: str,
    *,
    raw_text: str,
    page_count: int = 1,
    suspected_scanned: bool = False,
):
    from app.schemas.policy_pipeline import ParsedTextResult

    paragraphs = [line for line in raw_text.splitlines() if line.strip()]
    notes: list[str] = []
    if suspected_scanned:
        notes.append(
            "Extracted text is too short; this PDF is treated as a likely scan in MVP."
        )

    return ParsedTextResult(
        parser_status="parsed",
        source_path=source_path,
        raw_text=raw_text,
        page_count=page_count,
        suspected_scanned=suspected_scanned,
        paragraphs=paragraphs,
        tables=[],
        title_candidates=[line for line in paragraphs if line.startswith("第")],
        notes=notes,
    )


TEST_SCHEMA = f"test_policy_ingestion_{uuid.uuid4().hex[:8]}"
TEST_ENGINE = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args={"options": f"-csearch_path={TEST_SCHEMA},public"},
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)

with TEST_ENGINE.begin() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
    conn.execute(text("SET search_path TO public"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_policy_document (
                id BIGSERIAL PRIMARY KEY,
                policy_code TEXT UNIQUE,
                policy_name TEXT NOT NULL,
                policy_category TEXT NOT NULL,
                responsible_department TEXT,
                current_version_id BIGINT,
                latest_version_id BIGINT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT chk_kb_policy_document_status
                    CHECK (status IN ('draft', 'active', 'archived'))
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_policy_version (
                id BIGSERIAL PRIMARY KEY,
                policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
                version_seq INTEGER NOT NULL,
                version_label TEXT NOT NULL,
                source_year INTEGER,
                source_document_date DATE,
                issued_at DATE,
                effective_date DATE,
                expired_at DATE,
                previous_version_id BIGINT,
                revision_type TEXT NOT NULL DEFAULT 'revise',
                version_status TEXT NOT NULL DEFAULT 'draft',
                change_summary TEXT,
                change_reason TEXT,
                source_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_ext TEXT,
                file_hash TEXT,
                is_scanned BOOLEAN NOT NULL DEFAULT FALSE,
                parse_method TEXT NOT NULL DEFAULT 'direct',
                raw_text TEXT,
                clean_text TEXT,
                page_count INTEGER,
                parser_status TEXT NOT NULL DEFAULT 'pending',
                ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ,
                approved_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_kb_policy_version_id_policy UNIQUE (id, policy_id),
                CONSTRAINT uq_kb_policy_version_seq UNIQUE (policy_id, version_seq),
                CONSTRAINT uq_kb_policy_version_label UNIQUE (policy_id, version_label),
                CONSTRAINT uq_kb_policy_version_file_hash UNIQUE (policy_id, file_hash),
                CONSTRAINT chk_kb_policy_version_seq_positive CHECK (version_seq > 0),
                CONSTRAINT chk_kb_policy_version_year CHECK (
                    source_year IS NULL OR source_year BETWEEN 1900 AND 2100
                ),
                CONSTRAINT chk_kb_policy_version_dates CHECK (
                    expired_at IS NULL
                    OR effective_date IS NULL
                    OR expired_at >= effective_date
                ),
                CONSTRAINT chk_kb_policy_version_revision_type CHECK (
                    revision_type IN ('initial', 'revise', 'replace', 'supplement', 'abolish')
                ),
                CONSTRAINT chk_kb_policy_version_status CHECK (
                    version_status IN (
                        'draft',
                        'reviewing',
                        'approved',
                        'active',
                        'superseded',
                        'retired'
                    )
                ),
                CONSTRAINT chk_kb_policy_version_parser_status CHECK (
                    parser_status IN ('pending', 'processing', 'parsed', 'failed')
                ),
                CONSTRAINT chk_kb_policy_version_previous_self CHECK (
                    previous_version_id IS NULL OR previous_version_id <> id
                ),
                CONSTRAINT chk_kb_policy_version_hash_not_blank CHECK (
                    file_hash IS NULL OR btrim(file_hash) <> ''
                ),
                CONSTRAINT fk_kb_policy_version_previous_same_policy
                    FOREIGN KEY (previous_version_id, policy_id)
                    REFERENCES kb_policy_version(id, policy_id)
                    ON DELETE RESTRICT
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_policy_section (
                id BIGSERIAL PRIMARY KEY,
                version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
                parent_section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE CASCADE,
                section_no TEXT,
                section_title TEXT,
                section_level INTEGER NOT NULL DEFAULT 1,
                section_path TEXT,
                section_order INTEGER NOT NULL DEFAULT 0,
                page_start INTEGER,
                page_end INTEGER,
                section_text TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending',
                review_note TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT chk_kb_policy_section_level CHECK (section_level > 0),
                CONSTRAINT chk_kb_policy_section_page_range CHECK (
                    page_end IS NULL OR page_start IS NULL OR page_end >= page_start
                ),
                CONSTRAINT chk_kb_policy_section_review_status CHECK (
                    review_status IN ('pending', 'reviewing', 'passed', 'rejected')
                )
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_policy_chunk (
                id BIGSERIAL PRIMARY KEY,
                version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
                section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE SET NULL,
                chunk_index INTEGER NOT NULL,
                page_no INTEGER,
                chunk_text TEXT NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_kb_policy_chunk UNIQUE (version_id, chunk_index),
                CONSTRAINT chk_kb_policy_chunk_index_positive CHECK (chunk_index >= 0)
            )
            """
        )
    )


def override_get_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db_session] = override_get_db_session
client = TestClient(app)


def _truncate_tables() -> None:
    with TEST_ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE kb_policy_document
                SET current_version_id = NULL,
                    latest_version_id = NULL
                """
            )
        )
        conn.execute(text("DELETE FROM kb_policy_section"))
        conn.execute(text("DELETE FROM kb_policy_version"))
        conn.execute(text("DELETE FROM kb_policy_document"))


def _counts() -> tuple[int, int, int]:
    with TestingSessionLocal() as session:
        return (
            session.query(PolicyDocument).count(),
            session.query(PolicyVersion).count(),
            session.query(PolicySection).count(),
        )


def test_policy_ingestion_scan_filters_unsupported_and_template(
    tmp_path: Path,
) -> None:
    (tmp_path / "资产评估--报告审核制度.docx").write_bytes(b"docx-placeholder")
    (tmp_path / "保密承诺 - 模板.docx").write_bytes(b"template")
    (tmp_path / "旧制度.doc").write_bytes(b"legacy")
    (tmp_path / "制度说明.txt").write_bytes("说明".encode("utf-8"))
    (tmp_path / "盖章版.pdf").write_bytes(b"pdf-placeholder")

    response = client.post(
        "/api/v1/kb/policy-ingestion/scan",
        json={"source_root": str(tmp_path), "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    by_name = {item["file_name"]: item for item in payload["candidates"]}
    assert by_name["资产评估--报告审核制度.docx"]["recommended_action"] == "include"
    assert by_name["保密承诺 - 模板.docx"]["recommended_action"] == "exclude"
    assert by_name["旧制度.doc"]["recommended_action"] == "exclude"
    assert by_name["制度说明.txt"]["recommended_action"] == "exclude"
    assert by_name["盖章版.pdf"]["parse_method"] == "skip"


def test_policy_pipeline_preview_docx_does_not_persist(tmp_path: Path) -> None:
    _truncate_tables()
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(
        sample,
        [
            "信息安全及保密制度",
            "第一章 总则",
            "第一条 为了加强信息安全管理。",
            "第二条 员工离职后仍应承担保密义务。",
        ],
    )

    response = client.post(
        "/api/v1/kb/policy-pipeline/preview",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_name_guess"] == "信息安全及保密制度"
    assert payload["derived_version_label"]
    assert payload["parsed_text"]["parser_status"] == "parsed"
    assert payload["parsed_text"]["suspected_scanned"] is False
    assert payload["cleaned_text"]["clean_text"]
    assert payload["section_result"]["total_sections"] >= 1
    assert _counts() == (0, 0, 0)


def test_policy_pipeline_ingest_docx_persists_document_version_and_sections(tmp_path: Path) -> None:
    _truncate_tables()
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(
        sample,
        [
            "信息安全及保密制度",
            "第一章 总则",
            "第一条 为了加强信息安全管理。",
            "第二条 员工离职后仍应承担保密义务。",
        ],
    )

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["persistence"]["persisted"] is True

    with TestingSessionLocal() as session:
        document = session.query(PolicyDocument).one()
        version = session.query(PolicyVersion).one()
        sections = session.query(PolicySection).order_by(PolicySection.section_order).all()

        assert document.status == "draft"
        assert document.current_version_id is None
        assert document.latest_version_id == version.id
        assert version.version_status == "draft"
        assert version.version_seq == 1
        assert version.revision_type == "initial"
        assert version.parser_status == "parsed"
        assert len(sections) >= 1


def test_policy_pipeline_ingest_same_policy_reuses_document(
    tmp_path: Path,
) -> None:
    _truncate_tables()
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(sample, ["第一章 总则", "第一条 第一版内容。"])

    first = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )
    assert first.status_code == 200

    _create_docx(sample, ["第一章 总则", "第一条 第二版内容。"])
    second = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={
            "source_path": str(sample),
            "policy_category": "管理制度",
            "version_label": "20260621",
        },
    )
    assert second.status_code == 200

    with TestingSessionLocal() as session:
        assert session.query(PolicyDocument).count() == 1
        versions = session.query(PolicyVersion).order_by(PolicyVersion.version_seq).all()
        assert len(versions) == 2
        assert versions[1].version_seq == 2
        assert versions[1].previous_version_id == versions[0].id
        assert versions[1].version_label == "20260621-2"


def test_policy_pipeline_ingest_pdf_persists_document_version_and_sections(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _truncate_tables()
    sample = tmp_path / "采购管理制度.pdf"
    _create_pdf_placeholder(sample)

    from app.services.policy_parser import PolicyParserService

    original = PolicyParserService._parse_pdf

    def fake_parse_pdf(self, source_path: str):
        return _build_pdf_parse_result(
            source_path,
            raw_text=(
                "第一章 总则\n"
                "第一条 为了加强采购管理。\n"
                "第二条 本制度适用于公司的采购活动。"
            ),
            page_count=2,
        )

    monkeypatch.setattr(PolicyParserService, "_parse_pdf", fake_parse_pdf)
    try:
        response = client.post(
            "/api/v1/kb/policy-pipeline/ingest",
            json={"source_path": str(sample), "policy_category": "管理制度"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["persistence"]["persisted"] is True

        with TestingSessionLocal() as session:
            document = session.query(PolicyDocument).one()
            version = session.query(PolicyVersion).one()
            sections = session.query(PolicySection).all()

            assert document.status == "draft"
            assert document.current_version_id is None
            assert document.latest_version_id == version.id
            assert version.version_status == "draft"
            assert version.parse_method == "pdf"
            assert version.file_ext == ".pdf"
            assert version.page_count == 2
            assert len(sections) >= 1
    finally:
        monkeypatch.setattr(PolicyParserService, "_parse_pdf", original)


def test_policy_pipeline_preview_scanned_pdf_marks_suspected(tmp_path: Path, monkeypatch) -> None:
    _truncate_tables()
    sample = tmp_path / "扫描制度.pdf"
    _create_pdf_placeholder(sample)

    from app.services.policy_parser import PolicyParserService

    original = PolicyParserService._parse_pdf

    def fake_parse_pdf(self, source_path: str):
        return _build_pdf_parse_result(
            source_path,
            raw_text="图像 扫描",
            suspected_scanned=True,
        )

    monkeypatch.setattr(PolicyParserService, "_parse_pdf", fake_parse_pdf)
    try:
        response = client.post(
            "/api/v1/kb/policy-pipeline/preview",
            json={"source_path": str(sample), "policy_category": "管理制度"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["parsed_text"]["suspected_scanned"] is True
        assert payload["parsed_text"]["notes"]
        assert _counts() == (0, 0, 0)
    finally:
        monkeypatch.setattr(PolicyParserService, "_parse_pdf", original)


def test_policy_pipeline_ingest_scanned_pdf_stops_before_persistence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _truncate_tables()
    sample = tmp_path / "扫描制度.pdf"
    _create_pdf_placeholder(sample)

    from app.services.policy_parser import PolicyParserService

    original = PolicyParserService._parse_pdf

    def fake_parse_pdf(self, source_path: str):
        return _build_pdf_parse_result(
            source_path,
            raw_text="图像 扫描",
            suspected_scanned=True,
        )

    monkeypatch.setattr(PolicyParserService, "_parse_pdf", fake_parse_pdf)
    try:
        response = client.post(
            "/api/v1/kb/policy-pipeline/ingest",
            json={"source_path": str(sample), "policy_category": "管理制度"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["persistence"]["persisted"] is False
        assert _counts() == (0, 0, 0)
    finally:
        monkeypatch.setattr(PolicyParserService, "_parse_pdf", original)


def test_policy_pipeline_ingest_without_headings_creates_full_text_section(tmp_path: Path) -> None:
    _truncate_tables()
    sample = tmp_path / "员工行为规范.docx"
    _create_docx(sample, ["这是一个没有明确章条标题的制度正文。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200

    with TestingSessionLocal() as session:
        section = session.query(PolicySection).one()
        assert section.section_title == "全文"


def test_policy_pipeline_ingest_excluded_keyword_file_fails_before_persistence(
    tmp_path: Path,
) -> None:
    _truncate_tables()
    sample = tmp_path / "保密制度-模板.docx"
    _create_docx(sample, ["第一章 总则", "第一条 仅供模板参考。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["is_allowed"] is False
    assert _counts() == (0, 0, 0)


def test_policy_pipeline_ingest_rolls_back_when_section_persistence_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _truncate_tables()
    sample = tmp_path / "事务回滚制度.docx"
    _create_docx(sample, ["第一章 总则", "第一条 需要测试事务回滚。"])

    from app.repositories.policy_repository import PolicyRepository

    original = PolicyRepository._create_sections

    def broken_create_sections(self, *, version, sections):
        raise RuntimeError("section persistence failed")

    monkeypatch.setattr(PolicyRepository, "_create_sections", broken_create_sections)
    try:
        response = client.post(
            "/api/v1/kb/policy-pipeline/ingest",
            json={"source_path": str(sample), "policy_category": "管理制度"},
        )
        assert response.status_code == 400
        assert _counts() == (0, 0, 0)
    finally:
        monkeypatch.setattr(PolicyRepository, "_create_sections", original)


def test_policy_pipeline_does_not_create_chunk_records(tmp_path: Path) -> None:
    _truncate_tables()
    sample = tmp_path / "不生成切块制度.docx"
    _create_docx(sample, ["第一章 总则", "第一条 本阶段不生成 chunk。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    with TEST_ENGINE.begin() as conn:
        chunk_count = conn.execute(text("SELECT COUNT(*) FROM kb_policy_chunk")).scalar_one()
    assert chunk_count == 0


def test_policy_pipeline_preview_upload_returns_upload_id_and_no_persistence(
    tmp_path: Path,
) -> None:
    _truncate_tables()
    sample = tmp_path / "上传预览制度.docx"
    _create_docx(
        sample,
        [
            "上传预览制度",
            "第一章 总则",
            "第一条 为了测试上传预览。",
        ],
    )

    with sample.open("rb") as handle:
        response = client.post(
            "/api/v1/kb/policy-pipeline/preview-upload",
            data={"policy_category": "管理制度", "responsible_department": "综合管理部"},
            files={
                "file": (
                    sample.name,
                    handle,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["upload_id"]
    assert payload["parsed_text"]["parser_status"] == "parsed"
    assert _counts() == (0, 0, 0)


def test_policy_pipeline_ingest_upload_uses_staged_file(tmp_path: Path) -> None:
    _truncate_tables()
    sample = tmp_path / "上传入库制度.docx"
    _create_docx(
        sample,
        [
            "上传入库制度",
            "第一章 总则",
            "第一条 上传入库链路成功。",
        ],
    )

    with sample.open("rb") as handle:
        preview_response = client.post(
            "/api/v1/kb/policy-pipeline/preview-upload",
            data={"policy_category": "管理制度"},
            files={
                "file": (
                    sample.name,
                    handle,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert preview_response.status_code == 200
    upload_id = preview_response.json()["upload_id"]

    ingest_response = client.post(
        "/api/v1/kb/policy-pipeline/ingest-upload",
        json={
            "upload_id": upload_id,
            "policy_category": "管理制度",
            "responsible_department": "综合管理部",
            "version_label": "20260621",
        },
    )

    assert ingest_response.status_code == 200
    payload = ingest_response.json()
    assert payload["persistence"]["persisted"] is True

    with TestingSessionLocal() as session:
        document = session.query(PolicyDocument).one()
        version = session.query(PolicyVersion).one()
        assert document.policy_name == "上传入库制度"
        assert version.version_label == "20260621"
