from __future__ import annotations

from collections import Counter
import re

from app.schemas.policy_pipeline import CleanedTextResult, ParsedTextResult


class PolicyTextCleaner:
    """Apply conservative cleanup rules without changing document meaning."""

    def clean(self, parsed_text: ParsedTextResult) -> CleanedTextResult:
        """
        Normalize whitespace and remove low-value noise.

        This stage is intentionally conservative because later section splitting
        depends on the original chapter/article structure still being intact.
        """
        text = parsed_text.raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
        text = re.sub(r"[ \t]+", " ", text)
        lines = [line.strip() for line in text.split("\n")]

        repeated_noise = self._detect_repeated_noise(lines)
        removed_noise_examples: list[str] = []
        cleaned_lines: list[str] = []
        blank_streak = 0

        for line in lines:
            if not line:
                blank_streak += 1
                if blank_streak <= 1:
                    cleaned_lines.append("")
                continue

            blank_streak = 0
            if line in repeated_noise:
                removed_noise_examples.append(line)
                continue
            if re.fullmatch(r"第?\s*\d+\s*页", line) or re.fullmatch(r"-\s*\d+\s*-", line):
                removed_noise_examples.append(line)
                continue
            cleaned_lines.append(line)

        return CleanedTextResult(
            clean_text="\n".join(cleaned_lines).strip(),
            page_count=parsed_text.page_count,
            removed_noise_examples=removed_noise_examples[:10],
            notes=[
                "Applied conservative cleanup only.",
                "Chapter/article numbering was intentionally preserved.",
            ],
        )

    def _detect_repeated_noise(self, lines: list[str]) -> set[str]:
        """
        Heuristically detect repeated short lines that look like headers/footers.

        We only remove short lines repeated multiple times to avoid deleting real
        business content by mistake.
        """
        counter = Counter(line for line in lines if line and len(line) <= 30)
        return {line for line, count in counter.items() if count >= 3}
