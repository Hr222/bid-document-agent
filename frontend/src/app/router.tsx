import { Navigate, createBrowserRouter } from "react-router-dom";

import { AgentWorkspaceLayout } from "../layouts/AgentWorkspaceLayout";
import { KnowledgeBasePage } from "../features/knowledge-base/pages/KnowledgeBasePage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AgentWorkspaceLayout />,
    children: [
      { index: true, element: <Navigate to="/knowledge-bases" replace /> },
      { path: "knowledge-bases", element: <KnowledgeBasePage /> },
      { path: "knowledge-bases/:knowledgeBaseId", element: <KnowledgeBasePage /> },
      { path: "knowledge-bases/:knowledgeBaseId/search", element: <KnowledgeBasePage /> },
      { path: "*", element: <Navigate to="/knowledge-bases" replace /> },
    ],
  },
]);
