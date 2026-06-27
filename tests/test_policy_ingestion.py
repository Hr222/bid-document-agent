import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db_session
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models import PolicyChunk, PolicyDocument, PolicySection, PolicyVersion
from app.schemas.policy_pipeline import ParsedTextResult, SectionSplitItem, SectionSplitResult
from app.services.step.policy_chunking import PolicyChunkingService
from app.services.step.policy_embedding import PolicyEmbeddingService
from app.services.step.policy_parser import PolicyParserService
from app.domain.policy import PolicyChunkingPolicy


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
) -> ParsedTextResult:
    paragraphs = [line.strip() for line in raw_text.splitlines() if line.strip()]
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
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
    conn.execute(text("DROP TABLE IF EXISTS kb_policy_chunk CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS kb_policy_section CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS kb_policy_version CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS kb_policy_document CASCADE"))

Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def _reset_tables() -> None:
    _truncate_tables()


@pytest.fixture(autouse=True)
def _fake_embedding_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_embeddings(monkeypatch)



def override_get_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db_session] = override_get_db_session
client = TestClient(app)



def _install_fake_embeddings(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "success",
) -> None:
    def fake_init(self, client=None) -> None:
        return None

    def fake_embed_chunks(self, chunks):
        if mode == "failure":
            raise RuntimeError("向量生成失败")
        if mode == "dimension_mismatch":
            raise RuntimeError(
                f"向量维度不匹配：期望 {settings.vector_dimensions}，实际 8。"
            )
        embedded = []
        for chunk in chunks:
            vector = [float(chunk.chunk_index + 1)] * settings.vector_dimensions
            embedded.append(chunk.model_copy(update={"embedding": vector}))
        return embedded

    monkeypatch.setattr(PolicyEmbeddingService, "__init__", fake_init)
    monkeypatch.setattr(PolicyEmbeddingService, "embed_chunks", fake_embed_chunks)



def _truncate_tables() -> None:
    with TEST_ENGINE.begin() as conn:
        conn.execute(text("TRUNCATE TABLE kb_policy_chunk, kb_policy_section, kb_policy_version, kb_policy_document RESTART IDENTITY CASCADE"))



def _counts() -> tuple[int, int, int, int]:
    with TestingSessionLocal() as session:
        return (
            session.query(PolicyDocument).count(),
            session.query(PolicyVersion).count(),
            session.query(PolicySection).count(),
            session.query(PolicyChunk).count(),
        )



def _stage_status(payload: dict, stage_name: str) -> str | None:
    for stage in payload["stages"]:
        if stage["stage"] == stage_name:
            return stage["status"]
    return None


def _stage_message(payload: dict, stage_name: str) -> str | None:
    for stage in payload["stages"]:
        if stage["stage"] == stage_name:
            return stage["message"]
    return None



def test_policy_ingestion_scan_filters_unsupported_and_template(tmp_path: Path) -> None:
    (tmp_path / "资产评估-报告审核制度.docx").write_bytes(b"docx-placeholder")
    (tmp_path / "保密承诺-模板.docx").write_bytes(b"template")
    (tmp_path / "旧制度.doc").write_bytes(b"legacy")
    (tmp_path / "制度说明.txt").write_text("说明", encoding="utf-8")
    (tmp_path / "盖章件.pdf").write_bytes(b"pdf-placeholder")

    response = client.post(
        "/api/v1/kb/policy-ingestion/scan",
        json={"source_root": str(tmp_path), "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    by_name = {item["file_name"]: item for item in payload["candidates"]}
    assert by_name["资产评估-报告审核制度.docx"]["recommended_action"] == "include"
    assert by_name["保密承诺-模板.docx"]["recommended_action"] == "exclude"
    assert by_name["旧制度.doc"]["recommended_action"] == "exclude"
    assert by_name["制度说明.txt"]["recommended_action"] == "exclude"
    assert by_name["盖章件.pdf"]["parse_method"] == "skip"



def test_policy_pipeline_preview_docx_returns_chunk_summary_and_no_persistence(tmp_path: Path) -> None:
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(
        sample,
        [
            "信息安全及保密制度",
            "第一章 总则",
            "第一条 为了加强信息安全管理，建立统一的保密责任机制。",
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
    assert payload["chunk_result"]["total_chunks"] >= 1
    assert payload["chunk_result"]["sample_chunks"]
    assert payload["chunk_result"].get("chunks") == []
    assert payload["persistence"]["persisted"] is False
    assert payload["persistence"]["chunk_count"] == payload["chunk_result"]["total_chunks"]
    assert _stage_status(payload, "chunk_splitting") == "success"
    assert _stage_message(payload, "parse_routing") == "已选择解析器：DocxParser。"
    assert _stage_message(payload, "text_parsing") == "已完成原始文本提取。"
    assert _stage_message(payload, "text_cleaning") == "已完成文本清洗。"
    assert _stage_status(payload, "embedding_generation") == "skipped"
    assert _stage_status(payload, "chunk_persistence") == "skipped"
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_docx_persists_chunks_and_embeddings(tmp_path: Path) -> None:
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(
        sample,
        [
            "信息安全及保密制度",
            "第一章 总则",
            "第一条 为了加强信息安全管理，建立统一的保密责任机制。",
            "第二条 员工离职后仍应承担保密义务。",
            "第三条 涉及商业秘密的数据应按照分级授权进行访问。",
        ],
    )

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["persistence"]["persisted"] is True
    assert payload["persistence"]["section_count"] >= 1
    assert payload["persistence"]["chunk_count"] > 0
    assert _stage_status(payload, "embedding_generation") == "success"
    assert _stage_status(payload, "chunk_persistence") == "success"

    with TestingSessionLocal() as session:
        document = session.query(PolicyDocument).one()
        version = session.query(PolicyVersion).one()
        sections = session.query(PolicySection).order_by(PolicySection.section_order).all()
        chunks = session.query(PolicyChunk).order_by(PolicyChunk.chunk_index).all()

        assert document.status == "draft"
        assert document.current_version_id is None
        assert document.latest_version_id == version.id
        assert version.version_status == "draft"
        assert version.version_seq == 1
        assert version.revision_type == "initial"
        assert version.parser_status == "parsed"
        assert len(sections) >= 1
        assert len(chunks) == payload["persistence"]["chunk_count"]
        assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
        assert all(chunk.section_id is not None for chunk in chunks)
        assert all(len(chunk.embedding) == settings.vector_dimensions for chunk in chunks)

        first_chunk = chunks[0]
        assert first_chunk.chunk_metadata["section_id"] == first_chunk.section_id
        assert "section_order" in first_chunk.chunk_metadata
        assert "section_title" in first_chunk.chunk_metadata
        assert "section_path" in first_chunk.chunk_metadata
        assert "chunk_in_section" in first_chunk.chunk_metadata
        assert "chunk_start_offset" in first_chunk.chunk_metadata
        assert "chunk_end_offset" in first_chunk.chunk_metadata



def test_policy_pipeline_ingest_same_policy_reuses_document_and_separates_versions(tmp_path: Path) -> None:
    sample = tmp_path / "信息安全及保密制度.docx"
    _create_docx(
        sample,
        ["第一章 总则", "第一条 第一版内容。", "第二条 第一版补充要求。"],
    )

    first = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )
    assert first.status_code == 200

    _create_docx(
        sample,
        ["第一章 总则", "第一条 第二版内容。", "第二条 第二版补充要求。"],
    )
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
        chunks = session.query(PolicyChunk).order_by(PolicyChunk.version_id, PolicyChunk.chunk_index).all()

        assert len(versions) == 2
        assert versions[1].version_seq == 2
        assert versions[1].previous_version_id == versions[0].id
        assert versions[1].version_label == "20260621"
        assert {chunk.version_id for chunk in chunks} == {versions[0].id, versions[1].id}
        assert sum(1 for chunk in chunks if chunk.version_id == versions[0].id) > 0
        assert sum(1 for chunk in chunks if chunk.version_id == versions[1].id) > 0



def test_policy_pipeline_ingest_pdf_persists_document_version_sections_and_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = tmp_path / "采购管理制度.pdf"
    _create_pdf_placeholder(sample)

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
    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["persistence"]["persisted"] is True
    assert payload["persistence"]["chunk_count"] > 0

    with TestingSessionLocal() as session:
        document = session.query(PolicyDocument).one()
        version = session.query(PolicyVersion).one()
        sections = session.query(PolicySection).all()
        chunks = session.query(PolicyChunk).all()

        assert document.latest_version_id == version.id
        assert version.parse_method == "pdf"
        assert version.file_ext == ".pdf"
        assert version.page_count == 2
        assert len(sections) >= 1
        assert len(chunks) >= 1



def test_policy_pipeline_preview_scanned_pdf_marks_suspected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = tmp_path / "扫描制度.pdf"
    _create_pdf_placeholder(sample)

    def fake_parse_pdf(self, source_path: str):
        return _build_pdf_parse_result(
            source_path,
            raw_text="图片 扫描",
            suspected_scanned=True,
        )

    monkeypatch.setattr(PolicyParserService, "_parse_pdf", fake_parse_pdf)
    response = client.post(
        "/api/v1/kb/policy-pipeline/preview",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_text"]["suspected_scanned"] is True
    assert payload["parsed_text"]["notes"]
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_scanned_pdf_stops_before_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = tmp_path / "扫描制度.pdf"
    _create_pdf_placeholder(sample)

    def fake_parse_pdf(self, source_path: str):
        return _build_pdf_parse_result(
            source_path,
            raw_text="图片 扫描",
            suspected_scanned=True,
        )

    monkeypatch.setattr(PolicyParserService, "_parse_pdf", fake_parse_pdf)
    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["persistence"]["persisted"] is False
    assert _stage_status(payload, "document_persistence") == "failed"
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_without_headings_creates_full_text_section(tmp_path: Path) -> None:
    sample = tmp_path / "员工行为规范.docx"
    _create_docx(sample, ["这是一份没有明显章节标题的制度正文。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200

    with TestingSessionLocal() as session:
        section = session.query(PolicySection).one()
        chunk = session.query(PolicyChunk).one()
        assert section.section_title == "全文"
        assert chunk.chunk_metadata["section_title"] == "全文"


def test_policy_pipeline_ingest_article_heading_uses_short_title_and_skips_cover_noise(
    tmp_path: Path,
) -> None:
    sample = tmp_path / "质量管理制度.docx"
    _create_docx(
        sample,
        [
            "估",
            "价",
            "质",
            "量",
            "质量控制和管理制度",
            "第一章 总则",
            "第一条 为了加强资产评估业务管理，保证资产评估工作质量，规避资产评估风险。",
            "第二条 本制度适用于全体员工。",
        ],
    )

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200

    with TestingSessionLocal() as session:
        sections = session.query(PolicySection).order_by(PolicySection.section_order).all()
        chunks = session.query(PolicyChunk).order_by(PolicyChunk.chunk_index).all()

        assert sections[0].section_no == "第一章"
        assert sections[0].section_title == "总则"
        assert sections[1].section_no == "第一条"
        assert sections[1].section_title == "第一条"
        assert "估\n价\n质\n量" not in sections[0].section_text
        assert chunks[0].chunk_metadata["section_title"] == "总则"
        assert chunks[1].chunk_metadata["section_title"] == "第一条"



def test_policy_pipeline_ingest_excluded_keyword_file_fails_before_persistence(tmp_path: Path) -> None:
    sample = tmp_path / "保密制度-模板.docx"
    _create_docx(sample, ["第一章 总则", "第一条 仅供模板参考。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["is_allowed"] is False
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_rolls_back_when_embedding_generation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_embeddings(monkeypatch, mode="failure")
    sample = tmp_path / "事务回滚制度.docx"
    _create_docx(sample, ["第一章 总则", "第一条 需要测试 embedding 失败后的回滚。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 400
    assert "向量生成失败" in response.json()["detail"]
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_rolls_back_when_embedding_dimension_mismatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_embeddings(monkeypatch, mode="dimension_mismatch")
    sample = tmp_path / "向量维度校验制度.docx"
    _create_docx(sample, ["第一章 总则", "第一条 需要测试 embedding 维度不匹配时的回滚。"])

    response = client.post(
        "/api/v1/kb/policy-pipeline/ingest",
        json={"source_path": str(sample), "policy_category": "管理制度"},
    )

    assert response.status_code == 400
    assert "向量维度不匹配" in response.json()["detail"]
    assert _counts() == (0, 0, 0, 0)



def test_policy_chunking_service_splits_long_section_into_multiple_chunks() -> None:
    section_result = SectionSplitResult(
        total_sections=1,
        strategy="chapter-article",
        notes=[],
        sections=[
            SectionSplitItem(
                section_no="第一条",
                section_title="总则",
                section_level=1,
                section_path="第一章 / 总则",
                section_order=0,
                section_text=("为测试长文本切块。" * 30),
            )
        ],
    )
    service = PolicyChunkingService(
        chunking_policy=PolicyChunkingPolicy(target_chars=40, overlap_chars=10)
    )

    result = service.split(section_result)

    assert result.total_chunks > 1
    assert [item.chunk_index for item in result.chunks] == list(range(result.total_chunks))
    assert all(item.section_order == 0 for item in result.chunks)
    assert all(item.char_count <= 40 for item in result.chunks)



def test_policy_chunking_service_keeps_short_section_as_single_chunk() -> None:
    section_result = SectionSplitResult(
        total_sections=1,
        strategy="chapter-article",
        notes=[],
        sections=[
            SectionSplitItem(
                section_no="第一条",
                section_title="总则",
                section_level=1,
                section_path="第一章 / 总则",
                section_order=0,
                section_text="这是一个较短的 section。",
            )
        ],
    )
    service = PolicyChunkingService(
        chunking_policy=PolicyChunkingPolicy(target_chars=80, overlap_chars=10)
    )

    result = service.split(section_result)

    assert result.total_chunks == 1
    assert result.chunks[0].chunk_in_section == 0
    assert result.chunks[0].chunk_start_offset == 0
    assert result.chunks[0].chunk_end_offset == len("这是一个较短的 section。")



def test_policy_pipeline_preview_upload_returns_upload_id_chunk_summary_and_no_persistence(
    tmp_path: Path,
) -> None:
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
    assert payload["chunk_result"]["total_chunks"] >= 1
    assert _counts() == (0, 0, 0, 0)



def test_policy_pipeline_ingest_upload_uses_staged_file(tmp_path: Path) -> None:
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
    assert payload["persistence"]["chunk_count"] > 0

    with TestingSessionLocal() as session:
        document = session.query(PolicyDocument).one()
        version = session.query(PolicyVersion).one()
        chunks = session.query(PolicyChunk).all()
        assert document.policy_name == "上传入库制度"
        assert version.version_label == "20260621"
        assert len(chunks) > 0
