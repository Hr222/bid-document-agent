from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

CHINESE_NUMERAL_FRAGMENT = r"[一二三四五六七八九十百千万零〇两0-9]+"
HeadingLevel = Literal[1, 2, 3]


@dataclass(slots=True)
class PolicyIntakeDecision:
    """领域层的准入决策对象。"""

    is_allowed: bool
    detected_file_kind: str
    needs_normalization: bool
    recommended_parse_method: str
    warnings: list[str]


class PolicyIntakePolicy:
    """制度文档准入规则。"""

    _image_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }
    _allowed_extensions = {".doc", ".docx", ".pdf", *_image_extensions}
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

    def decide(self, *, file_name: str, extension: str, size_bytes: int) -> PolicyIntakeDecision:
        if extension not in self._allowed_extensions:
            return PolicyIntakeDecision(
                is_allowed=False,
                detected_file_kind="unsupported",
                needs_normalization=False,
                recommended_parse_method="skip",
                warnings=["当前 MVP 仅允许 .doc/.docx/.pdf 以及常见图片扫描件文件。"],
            )

        if size_bytes <= 0:
            return PolicyIntakeDecision(
                is_allowed=False,
                detected_file_kind="empty",
                needs_normalization=False,
                recommended_parse_method="skip",
                warnings=["源文件为空。"],
            )

        lower_name = file_name.lower()
        for keyword in self._excluded_keywords:
            if keyword.lower() in lower_name:
                return PolicyIntakeDecision(
                    is_allowed=False,
                    detected_file_kind="excluded_by_keyword",
                    needs_normalization=False,
                    recommended_parse_method="skip",
                    warnings=[f"文件名命中排除关键词：{keyword}"],
                )

        if extension == ".doc":
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="word_legacy",
                needs_normalization=True,
                recommended_parse_method="doc",
                warnings=["旧版 .doc 文件会先转换为 .docx，再进入后续解析流程。"],
            )

        if extension == ".docx":
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="word_openxml",
                needs_normalization=False,
                recommended_parse_method="docx",
                warnings=[],
            )

        if extension in self._image_extensions:
            return PolicyIntakeDecision(
                is_allowed=True,
                detected_file_kind="image_scan",
                needs_normalization=False,
                recommended_parse_method="image",
                warnings=["图片文件将直接进入 OCR 流程。"],
            )

        return PolicyIntakeDecision(
            is_allowed=True,
            detected_file_kind="pdf",
            needs_normalization=False,
            recommended_parse_method="pdf",
            warnings=[],
        )


class PolicyIdentityPolicy:
    """根据文件名推导制度名称和版本标签。"""

    _bracket_noise_pattern = re.compile(
        r"[（(][^）)]{0,40}(模板|空白|盖章|签字|签名|扫描)[^）)]{0,40}[）)]"
    )

    def build_version_label(self, *, explicit_label: str | None, modified_at_text: str) -> str:
        if explicit_label:
            return explicit_label
        return modified_at_text

    def guess_policy_name(self, *, file_name: str) -> str:
        stem = file_name.rsplit(".", maxsplit=1)[0]
        cleaned = re.sub(r"^\d{6,8}", "", stem)
        cleaned = self._bracket_noise_pattern.sub("", cleaned)
        cleaned = cleaned.replace("--", "-").replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"-{2,}", "-", cleaned)
        return cleaned.strip(" -_") or stem


@dataclass(slots=True)
class SectionHeading:
    section_no: str
    section_title: str
    section_level: HeadingLevel


class PolicySectionStructurePolicy:
    """章节标题识别规则。"""

    _chapter_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}章)\s*(.*)$")
    _section_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}节)\s*(.*)$")
    _article_pattern = re.compile(rf"^(第{CHINESE_NUMERAL_FRAGMENT}条)\s*(.*)$")
    _body_punctuation_pattern = re.compile(r"[，。；：！？]")
    _article_title_max_length = 18
    _generic_title_max_length = 40

    def match_heading(self, line: str) -> SectionHeading | None:
        stripped = line.strip()
        for pattern, level in (
            (self._chapter_pattern, 1),
            (self._section_pattern, 2),
            (self._article_pattern, 3),
        ):
            match = pattern.match(stripped)
            if match:
                section_no = match.group(1)
                raw_title = match.group(2).strip()
                return SectionHeading(
                    section_no=section_no,
                    section_title=self._resolve_section_title(
                        section_no=section_no,
                        raw_title=raw_title,
                        level=level,
                    ),
                    section_level=level,
                )
        return None

    def rebuild_path(self, *, current_path: list[str], heading: SectionHeading) -> list[str]:
        if heading.section_level <= 1:
            return [heading.section_title]
        if len(current_path) < heading.section_level - 1:
            return current_path + [heading.section_title]
        return current_path[: heading.section_level - 1] + [heading.section_title]

    def _resolve_section_title(
        self,
        *,
        section_no: str,
        raw_title: str,
        level: HeadingLevel,
    ) -> str:
        if not raw_title:
            return section_no

        title = re.sub(r"\s+", " ", raw_title).strip()
        if not title:
            return section_no

        if level == 3 and self._looks_like_article_body(title):
            return section_no
        if len(title) > self._generic_title_max_length and self._body_punctuation_pattern.search(title):
            return section_no
        return title

    def _looks_like_article_body(self, title: str) -> bool:
        return (
            len(title) > self._article_title_max_length
            or self._body_punctuation_pattern.search(title) is not None
        )


@dataclass(slots=True)
class ChunkSlice:
    start: int
    end: int
    text: str
    chunk_in_section: int


@dataclass(slots=True)
class RetrievalKeywordPlan:
    """关键词召回前的查询拆解结果。"""

    normalized_query: str
    focus_query: str
    keywords: list[str]
    priority_keywords: list[str] = field(default_factory=list)
    anchor_keywords: list[str] = field(default_factory=list)


class PolicyRetrievalQueryPolicy:
    """制度检索中的查询归一化与关键词提取规则。"""

    # TODO: 当前仍处于 MVP 阶段，这批规则先写死在领域层，方便快速验证效果。
    # 后续如果问题类型变多，或需要按业务线维护不同规则，再演进为可配置规则集。
    _question_phrases = (
        "在什么情况下",
        "什么情况下",
        "什么情形下",
        "什么时候",
        "要做什么",
        "该怎么做",
        "怎么处理",
        "如何处理",
        "如何计算",
        "怎么计算",
        "多久一次",
        "在哪里",
        "在哪儿",
        "哪些人",
        "哪些行为",
        "哪些",
        "什么人",
        "什么",
        "多久",
        "多长时间",
        "多长",
        "多少",
        "几个",
        "几级",
        "几天",
        "几个月",
        "是否",
        "吗",
        "么",
        "如何",
        "怎么",
        "怎么办",
        "有哪",
        "有哪些",
        "在哪",
        "哪里",
        "何时",
    )
    _year_pattern = re.compile(r"(?:19|20)\d{2}年?|(?:19|20)\d{2}(?:0[1-9]|1[0-2])")
    _article_pattern = re.compile(
        rf"第{CHINESE_NUMERAL_FRAGMENT}(?:章|节|条)"
    )
    _max_priority_span_size = 8
    _max_priority_keyword_count = 8
    _noise_terms = {
        "什么",
        "哪些",
        "多久",
        "多少",
        "是否",
        "如何",
        "怎么",
        "办法",
        "规定",
        "要求",
    }

    def build_keyword_plan(self, query: str) -> RetrievalKeywordPlan:
        normalized_query = self.normalize_query(query)
        focus_query = self._strip_question_shell(normalized_query)
        anchor_keywords = self._extract_anchor_keywords(focus_query)
        priority_keywords = self._extract_priority_keywords(
            normalized_query=normalized_query,
            focus_query=focus_query,
            anchor_keywords=anchor_keywords,
        )

        candidates: list[str] = []
        candidates.extend(priority_keywords)
        if len(focus_query) >= 2:
            candidates.append(focus_query)
        if focus_query != normalized_query and len(normalized_query) >= 2:
            candidates.append(normalized_query)
        for size in (4, 3, 2):
            for index in range(0, max(0, len(focus_query) - size + 1)):
                term = focus_query[index : index + size]
                if self.should_keep_keyword(term):
                    candidates.append(term)

        deduplicated_keywords: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            if item not in seen:
                deduplicated_keywords.append(item)
                seen.add(item)
            if len(deduplicated_keywords) >= 12:
                break

        return RetrievalKeywordPlan(
            normalized_query=normalized_query,
            focus_query=focus_query,
            keywords=deduplicated_keywords,
            priority_keywords=priority_keywords,
            anchor_keywords=anchor_keywords,
        )

    def normalize_query(self, query: str) -> str:
        return "".join(re.findall(r"[0-9a-zA-Z\u4e00-\u9fff]+", query.lower()))

    def should_keep_keyword(self, term: str) -> bool:
        if len(term) < 2:
            return False
        if re.fullmatch(r"(?:19|20)\d{2}", term):
            return True
        if term in self._noise_terms:
            return False
        if len(set(term)) == 1:
            return False
        return True

    def _strip_question_shell(self, normalized_query: str) -> str:
        focus_query = normalized_query
        for phrase in sorted(self._question_phrases, key=len, reverse=True):
            focus_query = focus_query.replace(phrase, "")
        return focus_query or normalized_query

    def _extract_priority_keywords(
        self,
        *,
        normalized_query: str,
        focus_query: str,
        anchor_keywords: list[str],
    ) -> list[str]:
        candidates: list[str] = []

        for pattern in (self._year_pattern, self._article_pattern):
            for match in pattern.finditer(normalized_query):
                term = match.group(0)
                if term.endswith("年") and len(term) == 5:
                    candidates.append(term)
                    candidates.append(term[:-1])
                else:
                    candidates.append(term)

        if len(focus_query) >= 4:
            candidates.append(focus_query)

        candidates.extend(anchor_keywords)
        candidates.extend(self._extract_informative_spans(focus_query))
        if focus_query != normalized_query:
            candidates.extend(self._extract_informative_spans(normalized_query))

        deduplicated: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if candidate and candidate not in seen:
                deduplicated.append(candidate)
                seen.add(candidate)
        return deduplicated[: self._max_priority_keyword_count]

    def _extract_anchor_keywords(self, text: str) -> list[str]:
        normalized_text = text.strip()
        if len(normalized_text) < 2:
            return []

        candidates: list[str] = []
        candidate_sizes: list[int] = []
        for size in (
            min(6, len(normalized_text)),
            min(4, len(normalized_text)),
            min(3, len(normalized_text)),
            2 if len(normalized_text) <= 6 else None,
        ):
            if size is None or size < 2 or size in candidate_sizes:
                continue
            candidate_sizes.append(size)

        for size in candidate_sizes:
            candidates.append(normalized_text[:size])
            candidates.append(normalized_text[-size:])

        deduplicated: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not self.should_keep_keyword(candidate):
                continue
            if candidate not in seen:
                deduplicated.append(candidate)
                seen.add(candidate)
        return deduplicated[:8]

    def _extract_informative_spans(self, text: str) -> list[str]:
        normalized_text = text.strip()
        if len(normalized_text) < 4:
            return []

        scored_spans: list[tuple[int, int, int, str]] = []
        max_span_size = min(self._max_priority_span_size, len(normalized_text))
        for size in range(max_span_size, 3, -1):
            for index in range(0, len(normalized_text) - size + 1):
                term = normalized_text[index : index + size]
                if not self.should_keep_keyword(term):
                    continue
                score = size * 10
                if any(char.isdigit() for char in term):
                    score += 20
                if index == 0 or index + size == len(normalized_text):
                    score += 3
                if term == normalized_text:
                    score += 5
                scored_spans.append((score, size, -index, term))

        scored_spans.sort(reverse=True)
        selected: list[str] = []
        for _, _, _, term in scored_spans:
            if term in selected:
                continue
            if any(term in existing for existing in selected if len(existing) >= len(term) + 2):
                continue
            selected.append(term)
            if len(selected) >= self._max_priority_keyword_count:
                break
        return selected


class PolicyChunkingPolicy:
    """先保留 section 边界，再按长度切块的规则。"""

    def __init__(self, *, target_chars: int, overlap_chars: int) -> None:
        if target_chars <= 0:
            raise ValueError("target_chars 必须大于 0。")
        if overlap_chars < 0:
            raise ValueError("overlap_chars 不能小于 0。")
        if overlap_chars >= target_chars:
            raise ValueError("overlap_chars 必须小于 target_chars。")

        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def split_section_text(self, text: str) -> list[ChunkSlice]:
        """单个 section 过长时，再按长度切成多个片段。"""
        normalized = text.strip()
        if not normalized:
            return []
        if len(normalized) <= self.target_chars:
            return [ChunkSlice(start=0, end=len(normalized), text=normalized, chunk_in_section=0)]

        chunks: list[ChunkSlice] = []
        start = 0
        chunk_in_section = 0
        step = self.target_chars - self.overlap_chars
        while start < len(normalized):
            end = min(len(normalized), start + self.target_chars)
            if end < len(normalized):
                candidate = normalized[start:end]
                split_at = max(
                    candidate.rfind("\n"),
                    candidate.rfind("。"),
                    candidate.rfind("，"),
                )
                if split_at >= max(0, len(candidate) // 2):
                    end = start + split_at + 1
            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunks.append(
                    ChunkSlice(
                        start=start,
                        end=end,
                        text=chunk_text,
                        chunk_in_section=chunk_in_section,
                    )
                )
                chunk_in_section += 1
            if end >= len(normalized):
                break
            start = max(end - self.overlap_chars, start + step)
        return chunks
