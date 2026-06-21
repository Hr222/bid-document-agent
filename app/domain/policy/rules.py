from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

CHINESE_NUMERAL_FRAGMENT = r"[一二三四五六七八九十百千万零〇两0-9]+"

# 标题层级类型别名：
# 1 = 章，2 = 节，3 = 条。
# 可以把它理解成一个轻量级的类型约束，主要用于提高可读性和类型检查效果。
HeadingLevel = Literal[1, 2, 3]

@dataclass(slots=True)
class PolicyIntakeDecision:
    """用于表达源文件是否允许进入流水线的领域决策对象。"""

    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class PolicyIntakePolicy:
    """
    第一阶段制度文件 intake 规则。

    当前 MVP 只接收原生 DOCX 和可直接抽文本的 PDF。
    """

    _allowed_extensions = {".docx", ".pdf"}

    _excluded_keywords = {
        "身份证",
        "签字",
        "签名",
        "公章",
        "法人章",
        "印章",
        "账号",
        "密码",
        "联系方式",
        "联系",
        "logo",
        "照片",
        "截图",
        "盖章",
        "空白",
        "模板",
    }

    def decide(
        self,
        *,
        file_name: str,
        extension: str,
        size_bytes: int,
    ) -> PolicyIntakeDecision:
        """判断文件是否允许继续进入解析流水线。"""
        # 这里 * 的作用是：后面的参数必须用“具名参数”传入。
        # 也就是调用时要写 decide(file_name=..., extension=..., size_bytes=...)
        # 这样做比只靠位置传参更清晰，尤其适合规则判断这类方法。
        if extension not in self._allowed_extensions:
            return PolicyIntakeDecision(
                is_allowed=False,
                detected_file_kind="unsupported",
                needs_normalization=False,
                recommended_parse_method="skip",
                warnings=["Only .docx and native-text .pdf files are allowed in this MVP."],
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
        for keyword in self._excluded_keywords:
            if keyword.lower() in lower_name:
                return PolicyIntakeDecision(
                    is_allowed=False,
                    detected_file_kind="excluded_by_keyword",
                    needs_normalization=False,
                    recommended_parse_method="skip",
                    warnings=[f"File name contains excluded keyword: {keyword}"],
                )

        if extension == ".docx":
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="word_openxml",
                needs_normalization=False,
                recommended_parse_method="docx",
                warnings=[],
            )

        return PolicyIntakeDecision(
            is_allowed=True,
            detected_file_kind="pdf",
            needs_normalization=False,
            recommended_parse_method="pdf",
            warnings=[],
        )


class PolicyIdentityPolicy:
    """
    制度主档命名和版本标签推导规则。

    这些都属于业务规则，因此放在领域层，而不是写死在应用服务里。
    """

    _bracket_noise_pattern = re.compile(
        r"[（(][^（）()]{0,40}(模板|空白|盖章|签字|签名|扫描)[^（）()]{0,40}[）)]"
    )

    def build_version_label(self, *, explicit_label: str | None, modified_at_text: str) -> str:
        """优先返回显式传入的版本标签，否则根据文件时间推导。"""
        # str | None 是 Python 3.10+ 的联合类型写法。
        # 可以把它理解成 Java 里的“这个参数允许为 null”，
        # 只是 Python 用类型提示直接表达出来。
        if explicit_label:
            return explicit_label
        return modified_at_text

    def guess_policy_name(self, *, file_name: str) -> str:
        """根据源文件名推导第一阶段使用的制度名称。"""
        stem = file_name.rsplit(".", maxsplit=1)[0]
        cleaned = re.sub(r"^\d{6,8}", "", stem)
        cleaned = self._bracket_noise_pattern.sub("", cleaned)
        cleaned = cleaned.replace("--", "-").replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"-{2,}", "-", cleaned)
        return cleaned.strip(" -_") or stem


@dataclass(slots=True)
class SectionHeading:
    """表示一次识别到的章/节/条标题的领域值对象。"""

    section_no: str
    section_title: str
    section_level: HeadingLevel


class PolicySectionStructurePolicy:
    """
    制度文档结构识别规则。

    章、节、条这些语义本身就是业务概念，因此放在领域层，而不是藏到通用工具类里。
    """

    _chapter_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}章)\s*(.*)$")
    _section_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}节)\s*(.*)$")
    _article_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}条)\s*(.*)$")
    # rf"..."
    # r 表示原始字符串，适合写正则，减少转义干扰。
    # f 表示格式化字符串，可以把上面的 CHINESE_NUMERAL_FRAGMENT 插进来。
    # 合在一起就是“支持变量插值的原始正则字符串”。

    def match_heading(self, line: str) -> SectionHeading | None:
        """从一行文本中识别章、节、条标题。"""
        stripped = line.strip()
        for pattern, level in (
            (self._chapter_pattern, 1),
            (self._section_pattern, 2),
            (self._article_pattern, 3),
        ):
            match = pattern.match(stripped)
            if match:
                return SectionHeading(
                    section_no=match.group(1),
                    section_title=match.group(2).strip() or match.group(1),
                    section_level=level,
                )
        return None

    def rebuild_path(self, *, current_path: list[str], heading: SectionHeading) -> list[str]:
        """按标题层级维护一个简化的章节路径。"""
        # list[str] 是 Python 类型注解，表示“字符串列表”。
        # 可以近似类比成 Java 里的 List<String>。
        if heading.section_level <= 1:
            return [heading.section_title]
        if len(current_path) < heading.section_level - 1:
            return current_path + [heading.section_title]
        return current_path[: heading.section_level - 1] + [heading.section_title]
