from app.schemas.policy_pipeline import CleanedTextResult
from app.services.policy_section_splitter import PolicySectionSplitter


def test_policy_section_splitter_splits_chapter_and_article() -> None:
    cleaner_output = CleanedTextResult(
        clean_text=(
            "第一章 总则\n"
            "第一条 为了加强管理。\n"
            "第二条 本制度适用于全体员工。\n"
            "第二章 附则\n"
            "第三条 本制度由综合管理部负责解释。"
        ),
        page_count=2,
        removed_noise_examples=[],
        notes=[],
    )

    result = PolicySectionSplitter().split(cleaner_output)

    assert result.total_sections >= 3
    assert result.sections[0].section_title in {"总则", "第一章"}


def test_policy_section_splitter_falls_back_to_full_text() -> None:
    cleaner_output = CleanedTextResult(
        clean_text="这是一个没有明确章条标题的制度正文。",
        page_count=1,
        removed_noise_examples=[],
        notes=[],
    )

    result = PolicySectionSplitter().split(cleaner_output)

    assert result.total_sections == 1
    assert result.sections[0].section_title == "全文"
