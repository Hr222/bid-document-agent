import axios from "axios";

import { appConfig } from "../../app/appConfig";

export const axiosClient = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: appConfig.requestTimeoutMs,
  headers: { Accept: "application/json" },
});

axiosClient.interceptors.request.use((config) => {
  config.headers.set("X-Client", "bid-document-agent-frontend");
  return config;
});
