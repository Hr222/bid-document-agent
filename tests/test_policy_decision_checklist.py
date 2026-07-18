from __future__ import annotations

from app.schemas import (
    PolicyDecisionChecklistRequest,
    RetrievalDebugInfo,
    RetrievalFilters,
    RetrievalHit,
    RetrievalSearchResponse,
    RetrievalStageDebug,
)
from app.services.policy_decision import RuleDrivenChecklistDecisionService


RULE_CHUNK_TEXT = """第十条 评估、拍卖机构自愿参与人民法院委托工作的，应在指定时间到人民法院申请登记，提交相关资料。申请参与委托评估（审计）的机构应提交如下审验资料：
(1)申请书、登记表及机构简介；
(2)经年检合格的企业法人营业执照副本和税务登记证副本；
(3)经年检合格的机构资质、资格证书副本；
(4)机构评估（审计）人员名单及其相关资质、机构营业场所证明资料；
(5)资格证书副本；
(6)注资证明及资产明细表；
(7)税务机关出具的纳税证明；
(8)法院指定提交的其他资料。"""


class FakeRetrievalService:
    """用固定命中结果替代真实检索，便于稳定覆盖规则判定路径。"""

    def __init__(self, hits: list[RetrievalHit]) -> None:
        self.hits = hits

    def search(self, request):  # noqa: ANN001
        return RetrievalSearchResponse(
            query=request.query,
            top_k=request.top_k,
            filters=RetrievalFilters(
                policy_category=request.policy_category,
                responsible_department=request.responsible_department,
                document_id=request.document_id,
                include_history=request.include_history,
            ),
            hits=self.hits,
            debug=RetrievalDebugInfo(
                pipeline="test-pipeline",
                strategy="test-strategy",
                min_score=0.45,
                stages=[
                    RetrievalStageDebug(
                        name="keyword_recall",
                        source="fake",
                        input_count=1,
                        output_count=len(self.hits),
                    )
                ],
            ),
        )


def _make_hit(chunk_text: str) -> RetrievalHit:
    """构造最小可用的制度命中片段。"""
    return RetrievalHit(
        document_id=101,
        version_id=201,
        chunk_id=301,
        policy_name="广东省高级人民法院关于委托评估拍卖工作的若干规定",
        policy_category="收费标准",
        responsible_department=None,
        version_label="现行",
        section_title="第十条",
        section_path="第十条",
        page_no=1,
        chunk_text=chunk_text,
        score=1.0,
        rank=1,
        retrieval_source="hybrid",
        score_breakdown={"keyword": 1.0},
    )


def test_rule_driven_checklist_reports_missing_materials() -> None:
    service = RuleDrivenChecklistDecisionService(FakeRetrievalService([_make_hit(RULE_CHUNK_TEXT)]))

    response = service.review_court_evaluation_materials(
        PolicyDecisionChecklistRequest(
            submitted_materials=[
                "申请书",
                "机构简介",
                "营业执照副本",
                "税务登记证副本",
                "机构资质证书副本",
                "评估人员名单",
                "相关资质说明",
                "营业场所证明",
                "纳税证明",
            ]
        )
    )

    assert response.decision == "fail"
    assert response.missing_input_fields == []
    assert "资格证书副本" in response.missing_fields
    assert "注资证明及资产明细表" in response.missing_fields
    assert "法院指定提交的其他资料" in response.missing_fields
    assert response.debug.matched_rule_requirement_count == 8
    assert response.debug.data_acquisition.provider == "inline_submitted_materials"


def test_rule_driven_checklist_passes_when_all_materials_exist() -> None:
    service = RuleDrivenChecklistDecisionService(FakeRetrievalService([_make_hit(RULE_CHUNK_TEXT)]))

    response = service.review_court_evaluation_materials(
        PolicyDecisionChecklistRequest(
            submitted_materials=[
                "申请书",
                "机构简介",
                "企业法人营业执照副本",
                "税务登记证副本",
                "机构资质证书副本",
                "评估人员名单",
                "相关资质",
                "机构营业场所证明资料",
                "资格证书副本",
                "注资证明",
                "资产明细表",
                "纳税证明",
                "法院指定资料",
            ]
        )
    )

    assert response.decision == "pass"
    assert response.missing_input_fields == []
    assert response.missing_fields == []
    assert len(response.used_fields) == 8


def test_rule_driven_checklist_returns_insufficient_evidence_for_partial_rule_text() -> None:
    service = RuleDrivenChecklistDecisionService(
        FakeRetrievalService([_make_hit("申请参与委托评估的机构应提交资料，具体要求以法院通知为准。")])
    )

    response = service.review_court_evaluation_materials(
        PolicyDecisionChecklistRequest(submitted_materials=["申请书", "营业执照副本"])
    )

    assert response.decision == "insufficient_evidence"
    assert response.used_fields == []
    assert response.missing_input_fields == []
    assert response.missing_fields == []
    assert response.debug.matched_rule_requirement_count < 8


def test_rule_driven_checklist_returns_insufficient_evidence_for_missing_business_input() -> None:
    service = RuleDrivenChecklistDecisionService(FakeRetrievalService([_make_hit(RULE_CHUNK_TEXT)]))

    response = service.review_court_evaluation_materials(PolicyDecisionChecklistRequest())

    assert response.decision == "insufficient_evidence"
    assert response.used_fields == []
    assert response.missing_input_fields == ["已提交材料列表"]
    assert response.missing_fields == []
    assert response.debug.data_acquisition.missing_input_fields == ["已提交材料列表"]
