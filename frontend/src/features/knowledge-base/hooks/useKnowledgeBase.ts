import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getKnowledgeBaseOverview,
  listKnowledgeDocuments,
  retryKnowledgeDocument,
  searchKnowledgeBase,
  uploadKnowledgeDocument,
} from "../api/knowledgeBaseApi";
import type { ListKnowledgeDocumentsParams, UploadDocumentRequest } from "../types";

export function useKnowledgeBaseOverview() {
  return useQuery({ queryKey: ["knowledge-base", "overview"], queryFn: getKnowledgeBaseOverview });
}

export function useKnowledgeBaseDocuments(params: ListKnowledgeDocumentsParams) {
  return useQuery({ queryKey: ["knowledge-base", "documents", params], queryFn: () => listKnowledgeDocuments(params) });
}

export function useUploadKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UploadDocumentRequest) => uploadKnowledgeDocument(request),
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

export function useKnowledgeBaseSearch(query: string, enabled: boolean) {
  return useQuery({ queryKey: ["knowledge-base", "search", query], queryFn: () => searchKnowledgeBase(query), enabled: enabled && Boolean(query.trim()) });
}
