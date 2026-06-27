from app.schemas import CleanedTextResult
from app.services.step.policy_section_splitter import PolicySectionSplitter


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
    assert result.sections[0].section_title == "总则"
    assert result.sections[1].section_title == "第一条"
    assert result.sections[2].section_title == "第二条"


def test_policy_section_splitter_discards_cover_noise_before_first_heading() -> None:
    cleaner_output = CleanedTextResult(
        clean_text=(
            "估\n"
            "价\n"
            "质\n"
            "量\n"
            "质量控制和管理制度\n"
            "第一章 总则\n"
            "第一条 为了加强管理。"
        ),
        page_count=1,
        removed_noise_examples=[],
        notes=[],
    )

    result = PolicySectionSplitter().split(cleaner_output)

    assert result.total_sections == 2
    assert result.sections[0].section_no == "第一章"
    assert result.sections[0].section_title == "总则"
    assert all("估\n价\n质\n量" not in section.section_text for section in result.sections)


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
