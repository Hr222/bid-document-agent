import base64
import json
import logging
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas import ChunkItem, ParsedBlock
from app.services.step.policy_embedding import PolicyEmbeddingService
from app.services.step.policy_ocr import PolicyOcrService

_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5W4WQAAAAASUVORK5CYII="
)


def test_http_request_logging_emits_access_log(caplog) -> None:
    with TestClient(app) as client:
        with caplog.at_level(logging.INFO):
            response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "HTTP request method=GET path=/api/v1/health" in caplog.text


class _FakeEmbeddingItem:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.data = [_FakeEmbeddingItem(embedding) for embedding in embeddings]


class _FakeEmbeddingsApi:
    def create(
        self,
        *,
        model: str,
        input: list[str],
        dimensions: int,
    ) -> _FakeEmbeddingResponse:
        return _FakeEmbeddingResponse(
            [[float(index + 1)] * dimensions for index, _ in enumerate(input)]
        )


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddingsApi()


class _FakeOcrMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeOcrChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeOcrMessage(content)


class _FakeOcrResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeOcrChoice(content)]
        self._payload = {
            "id": "ocr-response-1",
            "choices": [{"message": {"content": content}}],
        }

    def model_dump_json(self) -> str:
        return json.dumps(self._payload, ensure_ascii=False)


class _FakeChatCompletionsApi:
    def __init__(self, content: str) -> None:
        self.content = content
        self.last_messages: list[dict] | None = None

    def create(self, *, model: str, messages: list[dict]) -> _FakeOcrResponse:
        self.last_messages = messages
        return _FakeOcrResponse(self.content)


class _FakeChatApi:
    def __init__(self, content: str) -> None:
        self.completions = _FakeChatCompletionsApi(content)


class _FakeOcrOpenAIClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChatApi(content)


def test_embedding_logging_emits_batch_details(caplog) -> None:
    chunks = [
        ChunkItem(
            chunk_index=index,
            section_order=0,
            section_title="section",
            section_path="section",
            chunk_text=f"chunk-{index}",
            chunk_in_section=index,
            chunk_start_offset=0,
            chunk_end_offset=7,
            char_count=7,
            metadata={},
        )
        for index in range(3)
    ]

    with caplog.at_level(logging.INFO):
        service = PolicyEmbeddingService(client=_FakeOpenAIClient())
        service.embed_chunks(chunks)

    assert "向量生成开始 total_chunks=3" in caplog.text
    assert "向量批次完成 batch_index=1" in caplog.text
    assert "向量生成完成 embedded_chunks=3" in caplog.text


def test_ocr_logging_emits_raw_response(caplog, monkeypatch) -> None:
    monkeypatch.setattr(PolicyOcrService, "_next_request_at", 0.0)

    with caplog.at_level(logging.INFO):
        service = PolicyOcrService(client=_FakeOcrOpenAIClient("ocr text"))
        service.request_interval_seconds = 0.0
        result = service._ocr_image_bytes(
            _ONE_PIXEL_PNG,
            media_type="image/png",
            block_id="img-1",
            page_no=1,
        )

    assert result == "ocr text"
    assert 'OCR raw response block_id=img-1 page_no=1 response={"id": "ocr-response-1"' in caplog.text


def test_ocr_keeps_correct_media_type_in_request(monkeypatch) -> None:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buffer, format="JPEG")
    jpeg_bytes = buffer.getvalue()

    monkeypatch.setattr(PolicyOcrService, "_next_request_at", 0.0)
    service = PolicyOcrService(client=_FakeOcrOpenAIClient("ocr text"))
    service.request_interval_seconds = 0.0
    service._ocr_image_bytes(jpeg_bytes, media_type="image/jpeg", block_id="img-2", page_no=2)

    messages = service.client.chat.completions.last_messages
    assert messages is not None
    image_url = messages[1]["content"][1]["image_url"]["url"]
    assert image_url.startswith("data:image/jpeg;base64,")


def test_ocr_normalizes_unknown_image_payload_to_png() -> None:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(0, 128, 255)).save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    service = PolicyOcrService(client=_FakeOcrOpenAIClient("ocr text"))
    block = ParsedBlock(
        block_id="img-3",
        order=0,
        page_no=1,
        block_type="image",
        source="direct",
        text=None,
        metadata={
            "image_name": "scan.jp2",
            "image_bytes": png_bytes.hex(),
        },
        layout_hint={},
    )

    resolved_bytes, media_type = service._resolve_image_payload("unused", block)
    assert media_type == "image/png"
    assert resolved_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_ocr_rate_limit_waits_between_requests(monkeypatch) -> None:
    waits: list[float] = []
    timestamps = iter([100.0, 101.0])

    monkeypatch.setattr(PolicyOcrService, "_next_request_at", 0.0)
    monkeypatch.setattr("app.services.step.policy_ocr.monotonic", lambda: next(timestamps))
    monkeypatch.setattr("app.services.step.policy_ocr.sleep", lambda seconds: waits.append(seconds))

    service = PolicyOcrService(client=_FakeOcrOpenAIClient("ocr text"))
    service.request_interval_seconds = 10.0

    service._reserve_request_slot(block_id="img-1", page_no=1)
    service._reserve_request_slot(block_id="img-2", page_no=2)

    assert waits == [9.0]
