from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


@dataclass(slots=True)
class PolicyIntakeDecision:
    """Domain decision object for whether a source file may enter the pipeline."""

    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class PolicyIntakePolicy:
    """
    Domain rule set for policy source-file intake.

    In Java terms, this is a lightweight domain policy object. It owns business
    admission rules, while the application service only orchestrates the flow.
    """

    _allowed_extensions = {".doc", ".docx", ".pdf"}
    _warning_keywords = {"模板", "空白", "盖章", "签字", "签名"}

    def decide(
        self,
        *,
        file_name: str,
        extension: str,
        size_bytes: int,
    ) -> PolicyIntakeDecision:
        """Evaluate whether a file may continue into the parsing pipeline."""
        warnings: list[str] = []

        if extension not in self._allowed_extensions:
            return PolicyIntakeDecision(
                is_allowed=False,
                detected_file_kind="unsupported",
                needs_normalization=False,
                recommended_parse_method="skip",
                warnings=["Only .doc, .docx, and .pdf are allowed."],
            )

        if size_bytes <= 0:
            return PolicyIntakeDecision(
                is_allowed=False,
                detected_file_kind="empty",
                needs_normalization=False,
                recommended_parse_method="skip",
                warnings=["The source file is empty."],
            )

        lower_name = file_name.lower()
        for keyword in self._warning_keywords:
            if keyword.lower() in lower_name:
                warnings.append(f"File name contains warning keyword: {keyword}")

        if extension == ".doc":
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="legacy_word",
                needs_normalization=True,
                recommended_parse_method="word_to_docx",
                warnings=warnings,
            )

        if extension == ".docx":
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="word_openxml",
                needs_normalization=False,
                recommended_parse_method="docx",
                warnings=warnings,
            )

        return PolicyIntakeDecision(
            is_allowed=True,
            detected_file_kind="pdf",
            needs_normalization=False,
            recommended_parse_method="pdf",
            warnings=warnings,
        )


class PolicyIdentityPolicy:
    """
    Domain rule set for policy naming and version labeling.

    These are business concepts, so they belong in the domain layer instead of
    being hardcoded inside the application service.
    """

    def build_version_label(self, *, explicit_label: str | None, modified_at_text: str) -> str:
        """Return the explicit version label when present, otherwise derive one."""
        if explicit_label:
            return explicit_label
        return modified_at_text

    def guess_policy_name(self, *, file_name: str) -> str:
        """Derive a first-stage policy name from the source file name."""
        stem = file_name.rsplit(".", maxsplit=1)[0]
        return stem.strip().replace("_", " ").replace("--", "-")


HeadingLevel = Literal[1, 2, 3]


@dataclass(slots=True)
class SectionHeading:
    """Domain value object for one recognized section heading."""

    section_no: str
    section_title: str
    section_level: HeadingLevel


class PolicySectionStructurePolicy:
    """
    Domain rule set for recognizing policy document structure.

    The point of this class is to keep chapter/section/article semantics close
    to the domain instead of hiding them in a generic utility service.
    """

    _chapter_pattern = re.compile(r"^(第[一二三四五六七八九十百千0-9]+章)\s*(.*)$")
    _section_pattern = re.compile(r"^(第[一二三四五六七八九十百千0-9]+节)\s*(.*)$")
    _article_pattern = re.compile(r"^(第[一二三四五六七八九十百千0-9]+条)\s*(.*)$")

    def match_heading(self, line: str) -> SectionHeading | None:
        """Recognize a chapter/section/article heading from one line."""
        for pattern, level in (
            (self._chapter_pattern, 1),
            (self._section_pattern, 2),
            (self._article_pattern, 3),
        ):
            match = pattern.match(line)
            if match:
                return SectionHeading(
                    section_no=match.group(1),
                    section_title=match.group(2).strip() or match.group(1),
                    section_level=level,
                )
        return None

    def rebuild_path(self, *, current_path: list[str], heading: SectionHeading) -> list[str]:
        """Maintain a simple hierarchical path according to heading depth."""
        if heading.section_level <= 1:
            return [heading.section_title]
        if len(current_path) < heading.section_level - 1:
            return current_path + [heading.section_title]
        return current_path[: heading.section_level - 1] + [heading.section_title]
