from __future__ import annotations

from collections.abc import Callable

from openai import OpenAI

from app.modules.knowledge.ports.read_port import KnowledgeSearchHit
from app.modules.online.contracts import AnswerCitationResult, AnswerResult
from app.shared.config import settings
from app.shared.exceptions import ServiceNotConfiguredError, UpstreamServiceError

INSUFFICIENT_EVIDENCE_ANSWER = "未在知识库中找到足够依据。"


class RagAnswerGenerator:
    """基于知识证据生成内部回答结果的 LLM 技术适配器。"""

    def __init__(self, client: OpenAI | None = None) -> None:
        if client is not None:
            self.client = client
            self.model = settings.zhipu_chat_model
            return

        if not settings.zhipu_api_key or not settings.zhipu_chat_model:
            raise ServiceNotConfiguredError(
                "未配置 ZHIPU_API_KEY 或 ZHIPU_CHAT_MODEL，无法执行问答。"
            )

        self.client = OpenAI(
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_base_url,
        )
        self.model = settings.zhipu_chat_model

    def answer(self, *, query: str, hits: list[KnowledgeSearchHit]) -> AnswerResult:
        if not hits:
            return AnswerResult(
                query=query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                model=self.model,
                citations=(),
                hits=(),
                knowledge=None,
            )

        context_hits = hits[: settings.rag_answer_top_k]
        citations = tuple(
            AnswerCitationResult(
                ref_no=index,
                document_id=hit.document_id,
                version_id=hit.version_id,
                chunk_id=hit.chunk_id,
                policy_name=hit.policy_name,
                section_title=hit.section_title,
                page_no=hit.page_no,
                quote=hit.chunk_text[: settings.rag_max_context_chars_per_chunk],
            )
            for index, hit in enumerate(context_hits, start=1)
        )
        context_blocks = [
            "\n".join(
                [
                    f"[{citation.ref_no}] 制度：{hit.policy_name}",
                    f"版本：{hit.version_label}",
                    f"章节：{hit.section_title or '全文'}",
                    f"页码：{hit.page_no or '-'}",
                    f"内容：{citation.quote}",
                ]
            )
            for citation, hit in zip(citations, context_hits, strict=True)
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个制度知识库问答助手。"
                            "只能依据提供的检索片段回答。"
                            "结论尽量简短，偏业务表述。"
                            "引用必须使用 [1] [2] 这种格式。"
                            f"如果证据不足，明确回答“{INSUFFICIENT_EVIDENCE_ANSWER}”。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": "\n\n".join(
                            [f"问题：{query}", "可用证据：", *context_blocks]
                        ),
                    },
                ],
            )
        except Exception as exc:
            raise UpstreamServiceError(f"GLM 问答请求失败：{exc}") from exc

        message = response.choices[0].message
        content = message.content or ""
        if isinstance(content, str):
            answer = content.strip()
        else:
            answer = "\n".join(
                part.get("text", "").strip()
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ).strip()
        if not answer:
            answer = INSUFFICIENT_EVIDENCE_ANSWER

        return AnswerResult(
            query=query,
            answer=answer,
            model=self.model,
            citations=citations,
            hits=tuple(hits),
            knowledge=None,
        )


class LazyRagAnswerGenerator:
    """只有真正进入问答用例时才创建 LLM 客户端。"""

    def __init__(self, factory: Callable[[], RagAnswerGenerator]) -> None:
        self.factory = factory
        self._delegate: RagAnswerGenerator | None = None

    def answer(self, *, query: str, hits: list[KnowledgeSearchHit]) -> AnswerResult:
        if self._delegate is None:
            self._delegate = self.factory()
        return self._delegate.answer(query=query, hits=hits)
