import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntApp, ConfigProvider } from "antd";
import type { PropsWithChildren } from "react";

import { appConfig } from "./appConfig";
import { workspaceTheme } from "../styles/theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: workspaceTheme.colors.primary,
            borderRadius: 8,
            fontFamily: 'Inter, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
          },
        }}
      >
        <AntApp notification={{ placement: "topRight" }}>{children}</AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export { appConfig };
