import { appConfig } from "../../../app/appConfig";
import { axiosClient } from "../../../services/http/axiosClient";
import { toApiError } from "../../../services/http/errorHandler";

import { knowledgeBaseMockApi } from "./knowledgeBaseMockApi";
import type {
  KnowledgeBaseOverview,
  KnowledgeDocument,
  KnowledgeSearchResponse,
  ListKnowledgeDocumentsParams,
  UploadDocumentRequest,
} from "../types";

const useMock = appConfig.knowledgeBaseDataSource === "mock";

export async function getKnowledgeBaseOverview(): Promise<KnowledgeBaseOverview> {
  if (useMock) return knowledgeBaseMockApi.getOverview();
  try {
    const response = await axiosClient.get<KnowledgeBaseOverview>("/v1/kb/overview");
    return response.data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function listKnowledgeDocuments(params: ListKnowledgeDocumentsParams): Promise<KnowledgeDocument[]> {
  if (useMock) return knowledgeBaseMockApi.listDocuments(params);
  try {
    const response = await axiosClient.get<{ items: KnowledgeDocument[] }>("/v1/kb/documents", { params });
    return response.data.items;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function uploadKnowledgeDocument(request: UploadDocumentRequest): Promise<KnowledgeDocument> {
  if (useMock) return knowledgeBaseMockApi.uploadDocument(request);
  try {
    const formData = new FormData();
    formData.append("file", request.file);
    formData.append("policy_category", request.category);
    const response = await axiosClient.post<KnowledgeDocument>("/v1/kb/policy-pipeline/preview-upload", formData);
    return response.data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function retryKnowledgeDocument(documentId: number): Promise<KnowledgeDocument> {
  if (useMock) return knowledgeBaseMockApi.retryDocument(documentId);
  try {
    const response = await axiosClient.post<KnowledgeDocument>(`/v1/kb/documents/${documentId}/retry`);
    return response.data;
  } catch (error) {
    throw toApiError(error);
  }
}

export async function searchKnowledgeBase(query: string): Promise<KnowledgeSearchResponse> {
  if (useMock) return knowledgeBaseMockApi.search(query);
  try {
    const response = await axiosClient.post<KnowledgeSearchResponse>("/v1/kb/retrieval/search", { query, top_k: 5 });
    return response.data;
  } catch (error) {
    throw toApiError(error);
  }
}
