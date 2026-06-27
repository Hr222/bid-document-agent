from pathlib import Path

import pypdf

from app.schemas import ParsedBlock, ParsedDocumentResult
from app.services.step.policy_ocr import PolicyOcrService
from app.services.step.policy_parser import PolicyParserService


class _FakeOcrMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeOcrChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeOcrMessage(content)


class _FakeOcrResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeOcrChoice(content)]


class _FakeChatCompletionsApi:
    def __init__(self, content: str) -> None:
        self.content = content

    def create(self, *, model: str, messages: list[dict]) -> _FakeOcrResponse:
        return _FakeOcrResponse(self.content)


class _FakeChatApi:
    def __init__(self, content: str) -> None:
        self.completions = _FakeChatCompletionsApi(content)


class _FakeOcrOpenAIClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChatApi(content)


def test_policy_parser_pdf_without_text_uses_page_render_block(monkeypatch) -> None:
    class _FakeImage:
        def __init__(self, name: str, data: bytes) -> None:
            self.name = name
            self.data = data

    class _FakePage:
        def __init__(self) -> None:
            self.images = [_FakeImage("scan-page.jpg", b"\xff\xd8\xff")]

        def extract_text(self) -> str:
            return ""

    class _FakeReader:
        def __init__(self, source_path: str) -> None:
            self.pages = [_FakePage()]

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)

    result = PolicyParserService()._parse_pdf("fake.pdf")

    image_blocks = [block for block in result.blocks if block.block_type == "image"]
    assert result.suspected_scanned is True
    assert len(image_blocks) == 1
    assert image_blocks[0].metadata["pdf_page_render"] is True
    assert image_blocks[0].metadata["embedded_image_count"] == 1


def test_policy_ocr_skips_docx_inline_images_by_default() -> None:
    document = ParsedDocumentResult(
        parser_status="parsed",
        source_path=str(Path("fake.docx")),
        file_type="docx",
        suspected_scanned=False,
        blocks=[
            ParsedBlock(
                block_id="t1",
                order=0,
                page_no=None,
                block_type="text",
                source="direct",
                text="第一章 总则",
                metadata={},
                layout_hint={},
            ),
            ParsedBlock(
                block_id="i1",
                order=1,
                page_no=None,
                block_type="image",
                source="direct",
                text=None,
                metadata={"image_bytes": "00", "image_media_type": "image/png"},
                layout_hint={},
            ),
        ],
        notes=[],
    )

    result = PolicyOcrService(client=_FakeOcrOpenAIClient("ocr text")).process(
        document,
        persist=False,
    )

    assert result.applied is False
    assert result.parse_method == "direct"
    assert result.failed_blocks == 0
    assert result.blocks == document.blocks
    assert result.notes
