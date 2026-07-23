import { App, Button, Tabs, Typography } from "antd";
import { Upload } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { DocumentDetailDrawer } from "../components/DocumentDetailDrawer";
import { DocumentTable } from "../components/DocumentTable";
import { KnowledgeBaseHero } from "../components/KnowledgeBaseHero";
import { KnowledgeBaseSearchPanel } from "../components/KnowledgeBaseSearchPanel";
import { KnowledgeBaseStats } from "../components/KnowledgeBaseStats";
import { UploadDocumentModal } from "../components/UploadDocumentModal";
import { useKnowledgeBaseDocuments, useKnowledgeBaseOverview, useKnowledgeBaseSearch, useRetryKnowledgeDocument, useUploadKnowledgeDocument } from "../hooks/useKnowledgeBase";
import type { KnowledgeDocument, KnowledgeDocumentStatus, UploadDocumentRequest } from "../types";

import styles from "./KnowledgeBasePage.module.css";

const knowledgeBaseId = "policy";

export function KnowledgeBasePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [documentSearch, setDocumentSearch] = useState("");
  const [status, setStatus] = useState<"all" | KnowledgeDocumentStatus>("all");
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocument | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");

  const view = location.pathname.endsWith("/search") ? "search" : location.pathname === "/knowledge-bases" ? "overview" : "documents";
  const overviewQuery = useKnowledgeBaseOverview();
  const documentsQuery = useKnowledgeBaseDocuments({ search: documentSearch, status });
  const uploadMutation = useUploadKnowledgeDocument();
  const retryMutation = useRetryKnowledgeDocument();
  const searchQuery = useKnowledgeBaseSearch(submittedQuery, view === "search");

  const navigateView = (nextView: "overview" | "documents" | "search") => {
    if (nextView === "overview") navigate("/knowledge-bases");
    if (nextView === "documents") navigate(`/knowledge-bases/${knowledgeBaseId}`);
    if (nextView === "search") navigate(`/knowledge-bases/${knowledgeBaseId}/search`);
  };

  const handleUpload = async (request: UploadDocumentRequest) => {
    await uploadMutation.mutateAsync(request);
    message.success("文档已加入处理队列");
  };

  const handleRetry = async (documentId: number) => {
    await retryMutation.mutateAsync(documentId);
    message.success("已重新加入处理队列");
    setSelectedDocument(null);
  };

  const handleSearch = (value: string) => {
    const normalized = value.trim();
    if (!normalized) {
      message.warning("请输入检索问题");
      return;
    }
    setQuery(normalized);
    setSubmittedQuery(normalized);
  };

  return <div className={styles.page}><div className={styles.heading}><div><div className={styles.eyebrow}><span className={styles.onlineDot} />知识库服务正常运行</div><Typography.Title level={1}>知识库</Typography.Title><Typography.Paragraph>管理企业制度文档，沉淀可检索、可追溯的知识资产。</Typography.Paragraph></div><Button type="primary" icon={<Upload size={14} />} onClick={() => setUploadOpen(true)}>导入文档</Button></div><KnowledgeBaseStats overview={overviewQuery.data} loading={overviewQuery.isLoading} /><Tabs className={styles.tabs} activeKey={view} onChange={(key) => navigateView(key as "overview" | "documents" | "search")} items={[{ key: "overview", label: "概览" }, { key: "documents", label: `文档管理 ${overviewQuery.data?.documentCount ?? ""}` }, { key: "search", label: "知识检索" }]} />{view === "search" ? <KnowledgeBaseSearchPanel query={query} response={searchQuery.data} loading={searchQuery.isFetching} error={searchQuery.error instanceof Error ? searchQuery.error.message : undefined} onQueryChange={setQuery} onSearch={handleSearch} /> : <>{view === "overview" && <KnowledgeBaseHero onUpload={() => setUploadOpen(true)} onSearch={() => navigateView("search")} />}<DocumentTable documents={documentsQuery.data ?? []} search={documentSearch} status={status} loading={documentsQuery.isLoading} onSearchChange={setDocumentSearch} onStatusChange={setStatus} onUpload={() => setUploadOpen(true)} onOpen={setSelectedDocument} onRetry={(documentId) => void handleRetry(documentId)} /></>}<UploadDocumentModal open={uploadOpen} loading={uploadMutation.isPending} onClose={() => setUploadOpen(false)} onSubmit={handleUpload} /><DocumentDetailDrawer document={selectedDocument} onClose={() => setSelectedDocument(null)} onRetry={(documentId) => void handleRetry(documentId)} /></div>;
}
