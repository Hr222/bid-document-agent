from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import settings
from app.domain.policy import PolicyRetrievalQueryPolicy
from app.main import app
from app.models import PolicyChunk, PolicyDocument, PolicySection, PolicyVersion
from app.repositories.policy_repository import PolicyRepository
from app.schemas import AnswerCitation, RagAskResponse
from app.services.exceptions import UpstreamServiceError
from app.services.rag_answer_service import RagAnswerService
from app.services.step.policy_embedding import PolicyEmbeddingService
from tests.db_test_utils import SchemaHarness

TEST_DB = SchemaHarness("test_retrieval")
TestingSessionLocal = TEST_DB.session_local


@pytest.fixture(scope="module", autouse=True)
def _test_schema_lifecycle() -> Iterator[None]:
    previous_override = app.dependency_overrides.get(get_db_session)
    TEST_DB.create_schema()
    app.dependency_overrides[get_db_session] = TEST_DB.override_get_db_session
    try:
        yield
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db_session, None)
        else:
            app.dependency_overrides[get_db_session] = previous_override
        TEST_DB.drop_schema()


@pytest.fixture(autouse=True)
def _reset_tables() -> None:
    TEST_DB.truncate_tables(
        "kb_policy_chunk",
        "kb_policy_section",
        "kb_policy_version",
        "kb_policy_document",
    )


@pytest.fixture
def db_session() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _vector(first: float, second: float = 0.0) -> list[float]:
    values = [0.0] * settings.vector_dimensions
    values[0] = first
    values[1] = second
    return values


def _create_policy_document(
    session: Session,
    *,
    policy_name: str,
    policy_category: str,
    responsible_department: str | None,
    versions: list[dict],
) -> PolicyDocument:
    document = PolicyDocument(
        policy_code=None,
        policy_name=policy_name,
        policy_category=policy_category,
        responsible_department=responsible_department,
        current_version_id=None,
        latest_version_id=None,
        status="draft",
    )
    session.add(document)
    session.flush()

    created_versions: list[PolicyVersion] = []
    for version_index, version_data in enumerate(versions, start=1):
        version = PolicyVersion(
            policy_id=document.id,
            version_seq=version_index,
            version_label=version_data["version_label"],
            source_year=2026,
            source_document_date=None,
            issued_at=None,
            effective_date=None,
            expired_at=None,
            previous_version_id=created_versions[-1].id if created_versions else None,
            revision_type="initial" if version_index == 1 else "revise",
            version_status=version_data.get("version_status", "draft"),
            change_summary=None,
            change_reason=None,
            source_path=f"/tmp/{policy_name}-{version_index}.docx",
            file_name=f"{policy_name}-{version_index}.docx",
            file_ext=".docx",
            file_hash=f"hash-{policy_name}-{version_index}",
            is_scanned=False,
            parse_method="direct",
            raw_text=version_data.get("raw_text", version_data["chunk_text"]),
            clean_text=version_data.get("clean_text", version_data["chunk_text"]),
            page_count=version_data.get("page_count", 1),
            parser_status="parsed",
        )
        session.add(version)
        session.flush()

        section = PolicySection(
            version_id=version.id,
            parent_section_id=None,
            section_no=version_data.get("section_no"),
            section_title=version_data.get("section_title"),
            section_level=1,
            section_path=version_data.get("section_path"),
            section_order=0,
            page_start=version_data.get("page_no", 1),
            page_end=version_data.get("page_no", 1),
            section_text=version_data["chunk_text"],
            review_status="pending",
            review_note=None,
        )
        session.add(section)
        session.flush()

        chunk = PolicyChunk(
            version_id=version.id,
            section_id=section.id,
            chunk_index=0,
            page_no=version_data.get("page_no", 1),
            chunk_text=version_data["chunk_text"],
            embedding=version_data["embedding"],
            chunk_metadata={
                "section_title": version_data.get("section_title"),
                "section_path": version_data.get("section_path"),
            },
        )
        session.add(chunk)
        created_versions.append(version)

    document.latest_version_id = created_versions[-1].id
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def _install_fake_query_embedding(
    monkeypatch: pytest.MonkeyPatch,
    *,
    vector: list[float] | None = None,
    error: Exception | None = None,
) -> None:
    def fake_init(self, client=None) -> None:
        return None

    def fake_embed_query(self, text: str) -> list[float]:
        if error is not None:
            raise error
        assert text.strip()
        return vector or _vector(1.0, 0.0)

    monkeypatch.setattr(PolicyEmbeddingService, "__init__", fake_init)
    monkeypatch.setattr(PolicyEmbeddingService, "embed_query", fake_embed_query)


def test_embed_query_returns_single_vector() -> None:
    class FakeEmbeddingsAPI:
        def create(self, *, model, input, dimensions):
            assert model == settings.embedding_model
            assert input == ["采购审批要求"]
            assert dimensions == settings.vector_dimensions
            return type(
                "FakeResponse",
                (),
                {"data": [type("FakeItem", (), {"embedding": _vector(0.9, 0.1)})()]},
            )()

    fake_client = type("FakeClient", (), {"embeddings": FakeEmbeddingsAPI()})()
    service = PolicyEmbeddingService(client=fake_client)

    vector = service.embed_query("采购审批要求")

    assert len(vector) == settings.vector_dimensions
    assert vector[:2] == [0.9, 0.1]


def test_embed_query_wraps_upstream_error() -> None:
    class FailingEmbeddingsAPI:
        def create(self, *, model, input, dimensions):
            raise RuntimeError("provider unavailable")

    fake_client = type("FakeClient", (), {"embeddings": FailingEmbeddingsAPI()})()
    service = PolicyEmbeddingService(client=fake_client)

    with pytest.raises(UpstreamServiceError) as exc_info:
        service.embed_query("供应商失败")

    assert "Gitee embedding" in str(exc_info.value)


def test_repository_search_defaults_to_latest_version_only(db_session: Session) -> None:
    document = _create_policy_document(
        db_session,
        policy_name="采购管理制度",
        policy_category="管理制度",
        responsible_department="采购部",
        versions=[
            {
                "version_label": "2024",
                "section_title": "历史版本",
                "section_path": "第一章 / 历史版本",
                "chunk_text": "历史版本要求两级审批。",
                "embedding": _vector(1.0, 0.0),
                "page_no": 2,
            },
            {
                "version_label": "2025",
                "section_title": "最新版本",
                "section_path": "第一章 / 最新版本",
                "chunk_text": "最新版本要求三级审批。",
                "embedding": _vector(0.0, 1.0),
                "page_no": 3,
            },
        ],
    )
    repository = PolicyRepository(db_session)

    hits = repository.search_chunks(query_embedding=_vector(1.0, 0.0), top_k=5)

    assert len(hits) == 1
    assert hits[0].document_id == document.id
    assert hits[0].version_label == "2025"
    assert hits[0].chunk_text == "最新版本要求三级审批。"


def test_repository_search_include_history_and_filters(db_session: Session) -> None:
    target_document = _create_policy_document(
        db_session,
        policy_name="采购管理制度",
        policy_category="管理制度",
        responsible_department="采购部",
        versions=[
            {
                "version_label": "2024",
                "section_title": "历史版本",
                "section_path": "第一章 / 历史版本",
                "chunk_text": "历史版本要求两级审批。",
                "embedding": _vector(1.0, 0.0),
                "page_no": 2,
            },
            {
                "version_label": "2025",
                "section_title": "最新版本",
                "section_path": "第一章 / 最新版本",
                "chunk_text": "最新版本要求三级审批。",
                "embedding": _vector(0.8, 0.2),
                "page_no": 3,
            },
        ],
    )
    _create_policy_document(
        db_session,
        policy_name="人事管理制度",
        policy_category="人事制度",
        responsible_department="人力资源部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "考勤",
                "section_path": "第二章 / 考勤",
                "chunk_text": "考勤审批由部门负责人确认。",
                "embedding": _vector(0.6, 0.4),
                "page_no": 5,
            }
        ],
    )
    repository = PolicyRepository(db_session)

    hits = repository.search_chunks(
        query_embedding=_vector(1.0, 0.0),
        top_k=10,
        policy_category="管理制度",
        responsible_department="采购部",
        document_id=target_document.id,
        include_history=True,
    )

    assert len(hits) == 2
    assert [hit.version_label for hit in hits] == ["2024", "2025"]
    assert all(hit.document_id == target_document.id for hit in hits)
    assert all(hit.policy_category == "管理制度" for hit in hits)
    assert all(hit.responsible_department == "采购部" for hit in hits)
    assert hits[0].score >= hits[1].score


def test_retrieval_query_policy_strips_question_phrases_and_noise_terms() -> None:
    # 查询规则已经抽到领域层，后续即便继续写死，也要保证行为可回归验证。
    policy = PolicyRetrievalQueryPolicy()

    plan = policy.build_keyword_plan("员工试用期多久？")

    assert plan.normalized_query == "员工试用期多久"
    assert plan.focus_query == "员工试用期"
    assert "员工试用期" in plan.keywords
    assert "试用期" in plan.keywords
    assert "多久" not in plan.keywords


def test_repository_keyword_search_returns_ranked_hits(db_session: Session) -> None:
    # 覆盖 Step B1：确认最小关键词召回能把试用期条款命中出来。
    _create_policy_document(
        db_session,
        policy_name="人事管理制度",
        policy_category="人事制度",
        responsible_department="人力资源部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "试用期",
                "section_path": "第一章 / 试用期",
                "chunk_text": "员工试用期为六个月，试用期内由直属主管辅导。",
                "embedding": _vector(0.2, 0.8),
                "page_no": 4,
            }
        ],
    )
    _create_policy_document(
        db_session,
        policy_name="宿舍管理制度",
        policy_category="后勤制度",
        responsible_department="行政部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "住宿安排",
                "section_path": "第二章 / 住宿安排",
                "chunk_text": "宿舍申请须由行政部审批。",
                "embedding": _vector(0.1, 0.9),
                "page_no": 7,
            }
        ],
    )
    repository = PolicyRepository(db_session)

    hits = repository.search_chunks_by_keywords(
        focus_query="员工试用期",
        keywords=["员工试用期", "试用期", "员工", "试用"],
        top_k=5,
    )

    assert len(hits) == 1
    assert hits[0].policy_name == "人事管理制度"
    assert hits[0].section_title == "试用期"
    assert hits[0].retrieval_source == "keyword"
    assert hits[0].score_breakdown["keyword"] == hits[0].score
    assert hits[0].score >= settings.retrieval_min_score
    assert hits[0].debug_details["matched_fields"] == "chunk_text, section_title, section_path"
    assert "试用期" in str(hits[0].debug_details["matched_keywords"])


def test_search_api_returns_empty_hits_for_empty_library(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 覆盖 Step B2/B3：空库时也要保留完整的双路调试阶段，方便前后端排查。
    _install_fake_query_embedding(monkeypatch)

    response = client.post(
        "/api/v1/kb/retrieval/search",
        json={"query": "没有任何数据时的检索", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "没有任何数据时的检索"
    assert payload["hits"] == []
    assert payload["debug"]["pipeline"] == "knowledge-retrieval-v2"
    assert payload["debug"]["strategy"] == "hybrid-vector-keyword"
    assert [stage["name"] for stage in payload["debug"]["stages"]] == [
        "query_embedding",
        "vector_recall",
        "keyword_recall",
        "result_fusion",
        "score_filter",
    ]
    assert payload["debug"]["stages"][-1]["output_count"] == 0


def test_search_api_returns_rank_score_and_metadata(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 覆盖 Step B3：同一结果被双路同时命中时，应返回 hybrid 来源和分数拆解。
    _create_policy_document(
        db_session,
        policy_name="采购管理制度",
        policy_category="管理制度",
        responsible_department="采购部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "审批流程",
                "section_path": "第一章 / 审批流程",
                "chunk_text": "采购申请需要部门负责人、分管领导和财务三级审批。",
                "embedding": _vector(1.0, 0.0),
                "page_no": 6,
            }
        ],
    )
    _create_policy_document(
        db_session,
        policy_name="合同管理制度",
        policy_category="管理制度",
        responsible_department="法务部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "合同评审",
                "section_path": "第二章 / 合同评审",
                "chunk_text": "合同评审由法务牵头。",
                "embedding": _vector(0.7, 0.3),
                "page_no": 8,
            }
        ],
    )
    _install_fake_query_embedding(monkeypatch, vector=_vector(1.0, 0.0))

    response = client.post(
        "/api/v1/kb/retrieval/search",
        json={"query": "采购申请审批", "top_k": 5, "policy_category": "管理制度"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_k"] == 5
    assert payload["filters"]["policy_category"] == "管理制度"
    assert len(payload["hits"]) == 2
    assert payload["hits"][0]["rank"] == 1
    assert payload["hits"][0]["policy_name"] == "采购管理制度"
    assert payload["hits"][0]["section_title"] == "审批流程"
    assert payload["hits"][0]["page_no"] == 6
    assert payload["hits"][0]["score"] >= payload["hits"][1]["score"]
    assert payload["hits"][0]["retrieval_source"] == "hybrid"
    assert payload["hits"][0]["score_breakdown"]["vector"] > 0
    assert payload["hits"][0]["score_breakdown"]["keyword"] > 0
    assert payload["debug"]["min_score"] == settings.retrieval_min_score
    assert [stage["name"] for stage in payload["debug"]["stages"]] == [
        "query_embedding",
        "vector_recall",
        "keyword_recall",
        "result_fusion",
        "score_filter",
    ]
    assert "sample_hit_1" in payload["debug"]["stages"][2]["details"]
    assert "keywords=" in payload["debug"]["stages"][2]["details"]["sample_hit_1"]


def test_search_api_filters_low_score_hits_as_no_result(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_policy_document(
        db_session,
        policy_name="人事管理制度",
        policy_category="管理制度",
        responsible_department="综合管理部",
        versions=[
            {
                "version_label": "v2",
                "section_title": "录用",
                "section_path": "第一章 录用",
                "chunk_text": "录用相关制度内容。",
                "embedding": _vector(0.4175, 0.9),
                "page_no": 1,
            }
        ],
    )
    _install_fake_query_embedding(monkeypatch, vector=_vector(1.0, 0.0))

    response = client.post(
        "/api/v1/kb/retrieval/search",
        json={"query": "腾讯QQ", "top_k": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"] == []
    assert payload["debug"]["stages"][-1]["input_count"] == 1
    assert payload["debug"]["stages"][-1]["output_count"] == 0


def test_search_api_maps_embedding_failure_to_502(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_query_embedding(
        monkeypatch,
        error=UpstreamServiceError("Gitee embedding request failed"),
    )

    response = client.post(
        "/api/v1/kb/retrieval/search",
        json={"query": "上游故障", "top_k": 5},
    )

    assert response.status_code == 502
    assert "Gitee embedding" in response.json()["detail"]


def test_ask_api_without_hits_returns_evidence_insufficient_and_skips_glm(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_query_embedding(monkeypatch)

    def fail_init(self, client=None) -> None:
        raise AssertionError("GLM should not be initialized when there are no hits")

    monkeypatch.setattr(RagAnswerService, "__init__", fail_init)

    response = client.post(
        "/api/v1/kb/retrieval/ask",
        json={"query": "空库提问", "top_k": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "未在知识库中找到足够依据。"
    assert payload["citations"] == []
    assert payload["hits"] == []


def test_ask_api_uses_retrieval_hits_and_returns_answer(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 覆盖 ask 复用同一 retrieval pipeline，避免 search/ask 两条链路跑偏。
    _create_policy_document(
        db_session,
        policy_name="采购管理制度",
        policy_category="管理制度",
        responsible_department="采购部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "审批流程",
                "section_path": "第一章 / 审批流程",
                "chunk_text": "采购申请需要部门负责人、分管领导和财务三级审批。",
                "embedding": _vector(1.0, 0.0),
                "page_no": 6,
            }
        ],
    )
    _install_fake_query_embedding(monkeypatch, vector=_vector(1.0, 0.0))
    captured: dict[str, object] = {}

    def fake_init(self, client=None) -> None:
        self.model = "glm-test"

    def fake_answer(self, *, query: str, hits):
        captured["query"] = query
        captured["hits"] = hits
        return RagAskResponse(
            query=query,
            answer="采购申请需要三级审批。[1]",
            model="glm-test",
            citations=[
                AnswerCitation(
                    ref_no=1,
                    document_id=hits[0].document_id,
                    version_id=hits[0].version_id,
                    chunk_id=hits[0].chunk_id,
                    policy_name=hits[0].policy_name,
                    section_title=hits[0].section_title,
                    page_no=hits[0].page_no,
                    quote=hits[0].chunk_text,
                )
            ],
            hits=hits,
        )

    monkeypatch.setattr(RagAnswerService, "__init__", fake_init)
    monkeypatch.setattr(RagAnswerService, "answer", fake_answer)

    response = client.post(
        "/api/v1/kb/retrieval/ask",
        json={"query": "采购申请需要几级审批？", "top_k": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["query"] == "采购申请需要几级审批？"
    assert len(captured["hits"]) == 1
    assert payload["answer"] == "采购申请需要三级审批。[1]"
    assert payload["model"] == "glm-test"
    assert payload["citations"][0]["ref_no"] == 1
    assert payload["hits"][0]["policy_name"] == "采购管理制度"
    assert payload["hits"][0]["retrieval_source"] == "hybrid"
    assert payload["debug"]["strategy"] == "hybrid-vector-keyword"


def test_ask_api_hides_hits_and_citations_when_glm_returns_insufficient_evidence(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_policy_document(
        db_session,
        policy_name="policy-a",
        policy_category="test-category",
        responsible_department="test-dept",
        versions=[
            {
                "version_label": "v1",
                "section_title": "section-a",
                "section_path": "section-a",
                "chunk_text": "Temporary housing can be arranged for employees.",
                "embedding": _vector(1.0, 0.0),
                "page_no": 12,
            }
        ],
    )
    _install_fake_query_embedding(monkeypatch, vector=_vector(1.0, 0.0))

    def fake_init(self, client=None) -> None:
        self.model = "glm-test"

    def fake_answer(self, *, query: str, hits):
        return RagAskResponse(
            query=query,
            answer="未在知识库中找到足够依据。",
            model="glm-test",
            citations=[
                AnswerCitation(
                    ref_no=1,
                    document_id=hits[0].document_id,
                    version_id=hits[0].version_id,
                    chunk_id=hits[0].chunk_id,
                    policy_name=hits[0].policy_name,
                    section_title=hits[0].section_title,
                    page_no=hits[0].page_no,
                    quote=hits[0].chunk_text,
                )
            ],
            hits=hits,
        )

    monkeypatch.setattr(RagAnswerService, "__init__", fake_init)
    monkeypatch.setattr(RagAnswerService, "answer", fake_answer)

    response = client.post(
        "/api/v1/kb/retrieval/ask",
        json={"query": "What is the Tencent QQ dorm policy?", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "未在知识库中找到足够依据。"
    assert payload["citations"] == []
    assert payload["hits"] == []
    assert payload["debug"]["pipeline"] == "knowledge-retrieval-v2"
    assert payload["debug"]["strategy"] == "hybrid-vector-keyword"


def test_ask_api_maps_glm_failure_to_502(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_policy_document(
        db_session,
        policy_name="采购管理制度",
        policy_category="管理制度",
        responsible_department="采购部",
        versions=[
            {
                "version_label": "2025",
                "section_title": "审批流程",
                "section_path": "第一章 / 审批流程",
                "chunk_text": "采购申请需要三级审批。",
                "embedding": _vector(1.0, 0.0),
                "page_no": 6,
            }
        ],
    )
    _install_fake_query_embedding(monkeypatch, vector=_vector(1.0, 0.0))

    def fake_init(self, client=None) -> None:
        self.model = "glm-test"

    def fake_answer(self, *, query: str, hits):
        raise UpstreamServiceError("GLM request failed")

    monkeypatch.setattr(RagAnswerService, "__init__", fake_init)
    monkeypatch.setattr(RagAnswerService, "answer", fake_answer)

    response = client.post(
        "/api/v1/kb/retrieval/ask",
        json={"query": "采购申请需要几级审批？", "top_k": 6},
    )

    assert response.status_code == 502
    assert "GLM" in response.json()["detail"]
