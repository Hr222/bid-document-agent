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
import { useActivateKnowledgeDocument, useIngestKnowledgeDocument, useKnowledgeBaseCategories, useKnowledgeBaseDocumentDetail, useKnowledgeBaseDocuments, useKnowledgeBaseOverview, useKnowledgeBaseRecentDocuments, useKnowledgeBaseSearch, usePreviewKnowledgeDocument, useRetryKnowledgeDocument } from "../hooks/useKnowledgeBase";
import type { KnowledgeDocument, KnowledgeDocumentStatus, KnowledgeRetrievalMode } from "../types";

import styles from "./KnowledgeBasePage.module.css";

const knowledgeBaseId = "policy";

export function KnowledgeBasePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [documentSearch, setDocumentSearch] = useState("");
  const [statuses, setStatuses] = useState<KnowledgeDocumentStatus[]>([]);
  const [category, setCategory] = useState<string | undefined>();
  const [documentPage, setDocumentPage] = useState(1);
  const [documentPageSize, setDocumentPageSize] = useState(10);
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocument | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [retrievalMode, setRetrievalMode] = useState<KnowledgeRetrievalMode>("hybrid");
  const [topK, setTopK] = useState(5);

  const view = location.pathname.endsWith("/search") ? "search" : location.pathname === "/knowledge-bases" ? "overview" : "documents";
  const overviewQuery = useKnowledgeBaseOverview();
  const categoriesQuery = useKnowledgeBaseCategories();
  const documentsQuery = useKnowledgeBaseDocuments({
    search: documentSearch,
    statuses,
    category,
    limit: documentPageSize,
    offset: (documentPage - 1) * documentPageSize,
  }, view === "documents");
  const recentDocumentsQuery = useKnowledgeBaseRecentDocuments({ search: documentSearch, statuses, category }, view === "overview");
  const previewMutation = usePreviewKnowledgeDocument();
  const ingestMutation = useIngestKnowledgeDocument();
  const activateMutation = useActivateKnowledgeDocument();
  const retryMutation = useRetryKnowledgeDocument();
  const detailQuery = useKnowledgeBaseDocumentDetail(selectedDocumentId);
  const searchQuery = useKnowledgeBaseSearch(submittedQuery, retrievalMode, topK, view === "search");

  const navigateView = (nextView: "overview" | "documents" | "search") => {
    if (nextView === "overview") navigate("/knowledge-bases");
    if (nextView === "documents") navigate(`/knowledge-bases/${knowledgeBaseId}`);
    if (nextView === "search") navigate(`/knowledge-bases/${knowledgeBaseId}/search`);
  };

  const handlePreview = (request: Parameters<typeof previewMutation.mutateAsync>[0]) => (
    previewMutation.mutateAsync(request)
  );

  const handleConfirmUpload = async (preview: Parameters<typeof ingestMutation.mutateAsync>[0]) => {
    const result = await ingestMutation.mutateAsync(preview);
    if (!result.persisted || !result.documentId || !result.versionId) {
      throw new Error("文档入库未完成，后端未返回有效文档版本。");
    }
    await activateMutation.mutateAsync(result);
    message.success("文档已完成入库并发布");
  };

  const handleRetry = async (documentId: number) => {
    await retryMutation.mutateAsync(documentId);
    message.success("文档已重新入库并发布");
    setSelectedDocument(null);
    setSelectedDocumentId(null);
  };

  const handleOpenDocument = (document: KnowledgeDocument) => {
    setSelectedDocument(document);
    setSelectedDocumentId(document.id);
  };

  const handleCloseDocument = () => {
    setSelectedDocument(null);
    setSelectedDocumentId(null);
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

  const handleDocumentSearchChange = (value: string) => {
    setDocumentPage(1);
    setDocumentSearch(value);
  };

  const handleStatusesChange = (value: KnowledgeDocumentStatus[]) => {
    setDocumentPage(1);
    setStatuses(value);
  };

  const handleCategoryChange = (value?: string) => {
    setDocumentPage(1);
    setCategory(value);
  };

  const handleDocumentPageChange = (page: number, pageSize: number) => {
    setDocumentPage(pageSize === documentPageSize ? page : 1);
    setDocumentPageSize(pageSize);
  };

  const tableDocuments = view === "overview" ? recentDocumentsQuery.data ?? [] : documentsQuery.data?.items ?? [];
  const tableLoading = view === "overview" ? recentDocumentsQuery.isLoading : documentsQuery.isLoading;
  const tableTotal = view === "overview" ? undefined : documentsQuery.data?.totalCount;

  return <div className={styles.page}><div className={styles.heading}><div><div className={styles.eyebrow}><span className={styles.onlineDot} />知识库服务正常运行</div><Typography.Title level={1}>知识库</Typography.Title><Typography.Paragraph>管理企业制度文档，沉淀可检索、可追溯的知识资产。</Typography.Paragraph></div><Button type="primary" icon={<Upload size={14} />} onClick={() => setUploadOpen(true)}>导入文档</Button></div><KnowledgeBaseStats overview={overviewQuery.data} loading={overviewQuery.isLoading} /><Tabs className={styles.tabs} activeKey={view} onChange={(key) => navigateView(key as "overview" | "documents" | "search")} items={[{ key: "overview", label: "概览" }, { key: "documents", label: `文档管理 ${overviewQuery.data?.documentCount ?? ""}` }, { key: "search", label: "知识检索" }]} />{view === "search" ? <KnowledgeBaseSearchPanel query={query} response={searchQuery.data} loading={searchQuery.isFetching} error={searchQuery.error instanceof Error ? searchQuery.error.message : undefined} retrievalMode={retrievalMode} topK={topK} onRetrievalModeChange={setRetrievalMode} onTopKChange={setTopK} onQueryChange={setQuery} onSearch={handleSearch} /> : <>{view === "overview" && <KnowledgeBaseHero onUpload={() => setUploadOpen(true)} onSearch={() => navigateView("search")} />}<DocumentTable documents={tableDocuments} search={documentSearch} statuses={statuses} category={category} categories={categoriesQuery.data ?? []} loading={tableLoading} total={tableTotal} currentPage={documentPage} pageSize={documentPageSize} isRecent={view === "overview"} onPageChange={handleDocumentPageChange} onSearchChange={handleDocumentSearchChange} onStatusesChange={handleStatusesChange} onCategoryChange={handleCategoryChange} onUpload={() => setUploadOpen(true)} onOpen={handleOpenDocument} onRetry={(documentId) => void handleRetry(documentId)} onViewAll={() => navigateView("documents")} /></>}<UploadDocumentModal open={uploadOpen} loading={previewMutation.isPending || ingestMutation.isPending || activateMutation.isPending} onClose={() => setUploadOpen(false)} onPreview={handlePreview} onConfirm={handleConfirmUpload} /><DocumentDetailDrawer document={detailQuery.data ?? selectedDocument} loading={detailQuery.isFetching} onClose={handleCloseDocument} onRetry={(documentId) => void handleRetry(documentId)} /></div>;
}
