from __future__ import annotations

from app.domain.policy import PolicySectionStructurePolicy
from app.schemas.policy_pipeline import CleanedTextResult, SectionSplitItem, SectionSplitResult


class PolicySectionSplitter:
    """把清洗后的制度文本拆分成按章/节/条组织的 section。"""

    def __init__(self, structure_policy: PolicySectionStructurePolicy | None = None) -> None:
        self.structure_policy = structure_policy or PolicySectionStructurePolicy()

    def split(self, cleaned_text: CleanedTextResult) -> SectionSplitResult:
        """
        步骤 7：为制度类文档构建结构化章节。

        当前策略是“先结构、后长度”。
        这个阶段只关心业务上有意义的章/节/条单元，不关心 embedding chunk 大小。
        """
        lines = [line for line in cleaned_text.clean_text.splitlines() if line.strip()]
        if not lines:
            return SectionSplitResult(
                total_sections=0,
                strategy="chapter-article",
                sections=[],
                notes=["清洗后没有可用内容。"],
            )

        sections: list[SectionSplitItem] = []
        current_lines: list[str] = []
        current_no: str | None = None
        current_title: str | None = None
        current_level = 1
        current_path: list[str] = []
        saw_heading = False

        def flush_section() -> None:
            if not current_lines:
                return
            section_text = "\n".join(current_lines).strip()
            if not section_text:
                return
            sections.append(
                SectionSplitItem(
                    section_no=current_no,
                    section_title=current_title,
                    section_level=current_level,
                    section_path=" / ".join(current_path) if current_path else None,
                    section_order=len(sections),
                    section_text=section_text,
                )
            )

        for line in lines:
            heading = self.structure_policy.match_heading(line)
            if heading is None:
                current_lines.append(line)
                continue

            if not saw_heading and current_lines and not self._should_keep_preface(current_lines):
                current_lines = []

            saw_heading = True
            flush_section()
            current_no = heading.section_no
            current_title = heading.section_title
            current_level = heading.section_level
            current_path = self.structure_policy.rebuild_path(
                current_path=current_path,
                heading=heading,
            )
            current_lines = [line]

        flush_section()

        if not saw_heading:
            sections = [
                SectionSplitItem(
                    section_no=None,
                    section_title="全文",
                    section_level=1,
                    section_path="全文",
                    section_order=0,
                    section_text=cleaned_text.clean_text,
                )
            ]

        return SectionSplitResult(
            total_sections=len(sections),
            strategy="chapter-article",
            sections=sections,
            notes=["优先按章/节/条标题拆分；识别不到时退化为全文。"],
        )

    def _should_keep_preface(self, lines: list[str]) -> bool:
        joined = "".join(lines).strip()
        if not joined:
            return False

        single_char_lines = sum(1 for line in lines if len(line.strip()) == 1)
        short_lines = sum(1 for line in lines if len(line.strip()) <= 4)

        if single_char_lines >= 2:
            return False
        if len(lines) <= 5 and len(joined) <= 24 and short_lines >= len(lines) - 1:
            return False
        return True
