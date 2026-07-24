from fastapi import APIRouter, Depends, HTTPException

from app.interfaces.http.dependencies import get_chat_application
from app.interfaces.http.schemas.llm import LlmChatRequest, LlmChatResponse, LlmUsage
from app.modules.llm.application.chat import ChatApplication, ChatCommand
from app.shared.exceptions import ServiceNotConfiguredError, UpstreamServiceError

router = APIRouter()


@router.post("/chat", response_model=LlmChatResponse)
async def chat(
    request: LlmChatRequest,
    application: ChatApplication = Depends(get_chat_application),
) -> LlmChatResponse:
    """执行一次不保存上下文、不调用工具的 LLM 单轮请求。"""

    try:
        result = application.execute(ChatCommand(message=request.message))
    except ServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LlmChatResponse(
        answer=result.answer,
        model=result.model,
        prompt_version=result.prompt_version,
        usage=LlmUsage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
        ),
    )
