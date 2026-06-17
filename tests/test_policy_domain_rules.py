from app.domain.policy import PolicyIdentityPolicy, PolicyIntakePolicy, PolicySectionStructurePolicy


def test_policy_intake_policy_accepts_docx() -> None:
    decision = PolicyIntakePolicy().decide(
        file_name="资产评估报告审核制度.docx",
        extension=".docx",
        size_bytes=1024,
    )

    assert decision.is_allowed is True
    assert decision.needs_normalization is False
    assert decision.recommended_parse_method == "docx"


def test_policy_identity_policy_derives_name_and_version() -> None:
    policy = PolicyIdentityPolicy()

    assert policy.guess_policy_name(file_name="资产评估--报告审核制度.docx") == "资产评估-报告审核制度"
    assert policy.build_version_label(explicit_label=None, modified_at_text="20260617") == "20260617"


def test_policy_section_structure_policy_matches_article_heading() -> None:
    heading = PolicySectionStructurePolicy().match_heading("第一条 员工离职后仍应承担保密义务")

    assert heading is not None
    assert heading.section_no == "第一条"
    assert heading.section_level == 3
