export type KnowledgeDocumentStatus = "ready" | "processing" | "failed";

export type KnowledgeDocument = {
  id: number;
  name: string;
  type: "PDF" | "DOCX" | "XLSX";
  size: string;
  category: string;
  version: string;
  status: KnowledgeDocumentStatus;
  progress?: number;
  chunks: number;
  updatedAt: string;
  updatedBy: string;
  error?: string;
};

export type KnowledgeBaseOverview = {
  documentCount: number;
  chunkCount: number;
  retrievalAvailability: number;
  pendingCount: number;
  failedCount: number;
  updatedAt: string;
};

export type ListKnowledgeDocumentsParams = {
  search?: string;
  status?: "all" | KnowledgeDocumentStatus;
};

export type UploadDocumentRequest = {
  file: File;
  category: string;
};

export type RetrievalResult = {
  id: number;
  title: string;
  source: string;
  section: string;
  page: string;
  score: number;
  text: string;
  tags: string[];
};

export type KnowledgeSearchResponse = {
  query: string;
  results: RetrievalResult[];
};
