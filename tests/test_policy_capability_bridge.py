from __future__ import annotations

from app.bridges import PolicyCapabilityBridge
from app.schemas import (
    RagAskRequest,
    RagAskResponse,
    RetrievalDebugInfo,
    RetrievalFilters,
    RetrievalHit,
    RetrievalSearchResponse,
    RetrievalStageDebug,
)
from app.services.retrieval import INSUFFICIENT_EVIDENCE_ANSWER


def _make_search_response(*, hits: list[RetrievalHit]) -> RetrievalSearchResponse:
    return RetrievalSearchResponse(
        query="测试问题",
        top_k=5,
        filters=RetrievalFilters(
            policy_category="管理制度",
            responsible_department=None,
            document_id=None,
            include_history=False,
        ),
        hits=hits,
        debug=RetrievalDebugInfo(
            pipeline="test-pipeline",
            strategy="test-strategy",
            min_score=0.45,
            stages=[
                RetrievalStageDebug(
                    name="hybrid_recall",
                    source="fake",
                    input_count=1,
                    output_count=len(hits),
                )
            ],
        ),
    )


def _make_hit() -> RetrievalHit:
    return RetrievalHit(
        document_id=101,
        version_id=201,
        chunk_id=301,
        policy_name="示例制度",
        policy_category="管理制度",
        responsible_department=None,
        version_label="现行",
        section_title="第一条",
        section_path="第一条",
        page_no=1,
        chunk_text="这是用于测试的制度片段。",
        score=1.0,
        rank=1,
        retrieval_source="hybrid",
        score_breakdown={"keyword": 1.0},
    )


class FakeRetrievalService:
    def __init__(self, response: RetrievalSearchResponse) -> None:
        self.response = response
        self.search_call_count = 0

    def search(self, request):  # noqa: ANN001
        self.search_call_count += 1
        return self.response


class FakeAnswerService:
    def __init__(self, answer: str) -> None:
        self.answer_text = answer
        self.call_count = 0
        self.model = "fake-model"

    def answer(self, *, query: str, hits: list[RetrievalHit]) -> RagAskResponse:
        self.call_count += 1
        return RagAskResponse(
            query=query,
            answer=self.answer_text,
            model=self.model,
            citations=[],
            hits=hits,
        )


class FakeRuleRetrievalService:
    def retrieve_rule_pack(self, request):  # noqa: ANN001
        raise AssertionError("当前测试不应调用规则获取能力。")


class FakeDataAcquisitionService:
    def acquire_checklist_data(self, request):  # noqa: ANN001
        raise AssertionError("当前测试不应调用数据获取能力。")


class FakeDecisionService:
    def review_court_evaluation_materials(self, request):  # noqa: ANN001
        raise AssertionError("当前测试不应调用判定能力。")


def _make_bridge(
    *,
    retrieval_response: RetrievalSearchResponse,
    answer_text: str = "这是回答。",
) -> tuple[PolicyCapabilityBridge, FakeRetrievalService, FakeAnswerService]:
    retrieval_service = FakeRetrievalService(retrieval_response)
    answer_service = FakeAnswerService(answer_text)
    bridge = PolicyCapabilityBridge(
        retrieval_service=retrieval_service,
        answer_service=answer_service,
        rule_retrieval_service=FakeRuleRetrievalService(),
        data_acquisition_service=FakeDataAcquisitionService(),
        checklist_decision_service=FakeDecisionService(),
    )
    return bridge, retrieval_service, answer_service


def test_bridge_ask_reuses_search_before_answer_generation() -> None:
    bridge, retrieval_service, answer_service = _make_bridge(
        retrieval_response=_make_search_response(hits=[_make_hit()])
    )

    response = bridge.ask(RagAskRequest(query="测试问题"))

    assert retrieval_service.search_call_count == 1
    assert answer_service.call_count == 1
    assert response.debug is not None
    assert response.debug.pipeline == "test-pipeline"
    assert response.model == "fake-model"


def test_bridge_ask_hides_hits_when_answer_is_insufficient_evidence() -> None:
    bridge, _, _ = _make_bridge(
        retrieval_response=_make_search_response(hits=[_make_hit()]),
        answer_text=INSUFFICIENT_EVIDENCE_ANSWER,
    )

    response = bridge.ask(RagAskRequest(query="测试问题"))

    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.hits == []
    assert response.citations == []


def test_bridge_ask_returns_insufficient_evidence_without_calling_answer_service() -> None:
    bridge, retrieval_service, answer_service = _make_bridge(
        retrieval_response=_make_search_response(hits=[])
    )

    response = bridge.ask(RagAskRequest(query="测试问题"))

    assert retrieval_service.search_call_count == 1
    assert answer_service.call_count == 0
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.hits == []
