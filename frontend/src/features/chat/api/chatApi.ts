import { axiosClient } from "../../../services/http/axiosClient";
import { toApiError } from "../../../services/http/errorHandler";
import { appConfig } from "../../../app/appConfig";

import type { ChatApiResponse, ChatResult } from "../types";

export async function sendChatMessage(message: string): Promise<ChatResult> {
  const startedAt = performance.now();
  try {
    const response = await axiosClient.post<ChatApiResponse>(
      "/v1/llm/chat",
      { message },
      { timeout: appConfig.llmRequestTimeoutMs },
    );
    return {
      answer: response.data.answer,
      model: response.data.model,
      promptVersion: response.data.prompt_version,
      durationMs: Math.round(performance.now() - startedAt),
      totalTokens: response.data.usage.total_tokens,
    };
  } catch (error) {
    throw toApiError(error);
  }
}
