export const appConfig = {
  appName: "Bid Document Agent",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api",
  knowledgeBaseDataSource: import.meta.env.VITE_KB_DATA_SOURCE ?? "mock",
  requestTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 15_000),
} as const;
