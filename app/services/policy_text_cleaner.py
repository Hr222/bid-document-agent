from __future__ import annotations

import re
from collections import Counter

from app.schemas.policy_pipeline import CleanedTextResult, ParsedTextResult


class PolicyTextCleaner:
    """在尽量不改变原意的前提下，对文本执行保守清洗。"""

    def clean(self, parsed_text: ParsedTextResult) -> CleanedTextResult:
        """
        步骤 6：规范空白字符，并移除低价值噪音。

        规范空白字符，并移除低价值噪音。

        这里刻意保持保守，因为后续章节拆分依赖原始章/条结构不要被破坏。
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
            if re.fullmatch(r"第\s*\d+\s*页", line) or re.fullmatch(r"-\s*\d+\s*-", line):
                removed_noise_examples.append(line)
                continue
            cleaned_lines.append(line)

        return CleanedTextResult(
            clean_text="\n".join(cleaned_lines).strip(),
            page_count=parsed_text.page_count,
            removed_noise_examples=removed_noise_examples[:10],
            notes=[
                "当前只做保守清洗。",
                "章、节、条编号会被刻意保留。",
            ],
        )

    def _detect_repeated_noise(self, lines: list[str]) -> set[str]:
        """
        步骤 6 的辅助动作：启发式识别疑似页眉/页脚的重复短行。

        启发式识别疑似页眉/页脚的重复短行。

        这里只删除重复多次出现的短文本，避免误删真实业务内容。
        """
        counter = Counter(line for line in lines if line and len(line) <= 30)
        return {line for line, count in counter.items() if count >= 3}
