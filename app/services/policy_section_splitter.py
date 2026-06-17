from __future__ import annotations

from app.domain.policy import PolicySectionStructurePolicy
from app.schemas.policy_pipeline import CleanedTextResult, SectionSplitItem, SectionSplitResult


class PolicySectionSplitter:
    """Split cleaned policy text into chapter/article oriented sections."""

    def __init__(self, structure_policy: PolicySectionStructurePolicy | None = None) -> None:
        self.structure_policy = structure_policy or PolicySectionStructurePolicy()

    def split(self, cleaned_text: CleanedTextResult) -> SectionSplitResult:
        """
        Build structural sections for policy-style documents.

        The strategy is "structure first, length later". At this stage we only
        care about meaningful legal/business units, not embedding chunk size.
        """
        lines = [line for line in cleaned_text.clean_text.splitlines() if line.strip()]
        if not lines:
            return SectionSplitResult(
                total_sections=0,
                strategy="chapter-article",
                sections=[],
                notes=["No content available after cleaning."],
            )

        sections: list[SectionSplitItem] = []
        current_lines: list[str] = []
        current_no: str | None = None
        current_title: str | None = None
        current_level = 1
        current_path: list[str] = []

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
                    metadata={
                        "section_no": current_no,
                        "section_title": current_title,
                        "section_level": current_level,
                    },
                )
            )

        for line in lines:
            heading = self.structure_policy.match_heading(line)
            if heading is None:
                current_lines.append(line)
                continue

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

        if not sections:
            sections.append(
                SectionSplitItem(
                    section_no=None,
                    section_title="全文",
                    section_level=1,
                    section_path="全文",
                    section_order=0,
                    section_text=cleaned_text.clean_text,
                    metadata={"section_title": "全文", "section_level": 1},
                )
            )

        return SectionSplitResult(
            total_sections=len(sections),
            strategy="chapter-article",
            sections=sections,
            notes=["Split by chapter/section/article headings where available."],
        )
