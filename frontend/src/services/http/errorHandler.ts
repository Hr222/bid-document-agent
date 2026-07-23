import axios from "axios";

import type { ApiError } from "./requestTypes";

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    return {
      message: typeof detail === "string" ? detail : error.message || "请求失败，请稍后重试。",
      status: error.response?.status,
      code: error.code,
    };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  return { message: "请求失败，请稍后重试。" };
}
