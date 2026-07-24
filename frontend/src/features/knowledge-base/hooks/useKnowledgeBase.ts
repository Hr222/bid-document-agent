import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  activateKnowledgeDocument,
  getKnowledgeBaseOverview,
  listKnowledgeBaseCategories,
  getKnowledgeDocumentDetail,
  listRecentKnowledgeDocuments,
  ingestKnowledgeDocument,
  listKnowledgeDocuments,
  previewKnowledgeDocument,
  retryKnowledgeDocument,
  searchKnowledgeBase,
} from "../api/knowledgeBaseApi";
import type {
  KnowledgeUploadPreview,
  KnowledgeRetrievalMode,
  ListKnowledgeDocumentsParams,
  UploadDocumentRequest,
} from "../types";

export function useKnowledgeBaseOverview() {
  return useQuery({ queryKey: ["knowledge-base", "overview"], queryFn: getKnowledgeBaseOverview });
}

export function useKnowledgeBaseCategories() {
  return useQuery({ queryKey: ["knowledge-base", "categories"], queryFn: listKnowledgeBaseCategories });
}

export function useKnowledgeBaseDocuments(params: ListKnowledgeDocumentsParams, enabled = true) {
  return useQuery({ queryKey: ["knowledge-base", "documents", params], queryFn: () => listKnowledgeDocuments(params), enabled });
}

export function useKnowledgeBaseRecentDocuments(params: ListKnowledgeDocumentsParams, enabled = true) {
  return useQuery({ queryKey: ["knowledge-base", "recent-documents", params], queryFn: () => listRecentKnowledgeDocuments(params), enabled });
}

export function useKnowledgeBaseDocumentDetail(documentId: number | null) {
  return useQuery({
    queryKey: ["knowledge-base", "document", documentId],
    queryFn: () => getKnowledgeDocumentDetail(documentId as number),
    enabled: documentId !== null,
  });
}

export function usePreviewKnowledgeDocument() {
  return useMutation({
    mutationFn: (request: UploadDocumentRequest) => previewKnowledgeDocument(request),
  });
}

export function useIngestKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (preview: KnowledgeUploadPreview) => ingestKnowledgeDocument(preview),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
    },
  });
}

export function useActivateKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: activateKnowledgeDocument,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
    },
  });
}

export function useRetryKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: number) => retryKnowledgeDocument(documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["knowledge-base"] });
    },
  });
}

export function useKnowledgeBaseSearch(
  query: string,
  retrievalMode: KnowledgeRetrievalMode,
  topK: number,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["knowledge-base", "search", query, retrievalMode, topK],
    queryFn: () => searchKnowledgeBase(query, retrievalMode, topK),
    enabled: enabled && Boolean(query.trim()),
  });
}
