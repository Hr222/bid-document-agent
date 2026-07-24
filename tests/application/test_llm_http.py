from fastapi.testclient import TestClient

from app.interfaces.http.dependencies import get_chat_application
from app.main import create_app
from app.modules.llm.application.chat import ChatApplication
from app.modules.llm.contracts import ChatLlmResult


class FakeChatLlm:
    def invoke(self, request):  # noqa: ANN001
        return ChatLlmResult(
            content=f"收到：{request.user_prompt}",
            model="glm-test",
            prompt_version=request.prompt_version,
            total_tokens=8,
        )


def test_llm_chat_http_route_returns_single_turn_response() -> None:
    application = create_app()
    application.dependency_overrides[get_chat_application] = lambda: ChatApplication(FakeChatLlm())

    response = TestClient(application).post(
        "/api/v1/llm/chat",
        json={"message": "你好"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "收到：你好",
        "model": "glm-test",
        "prompt_version": "llm-chat-v1",
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": 8,
        },
    }
    application.dependency_overrides.clear()


def test_llm_chat_http_route_rejects_blank_message() -> None:
    application = create_app()

    response = TestClient(application).post(
        "/api/v1/llm/chat",
        json={"message": ""},
    )

    assert response.status_code == 422
