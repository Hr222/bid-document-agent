import type { PolicyDocumentOptionList } from "../types/knowledgeBase";

const API_BASE = "/api/v1/kb";

export async function listPolicyDocuments(params?: {
  search?: string;
  policyCategory?: string;
  limit?: number;
}): Promise<PolicyDocumentOptionList> {
  const query = new URLSearchParams();
  if (params?.search?.trim()) {
    query.set("search", params.search.trim());
  }
  if (params?.policyCategory?.trim()) {
    query.set("policy_category", params.policyCategory.trim());
  }
  if (params?.limit) {
    query.set("limit", String(params.limit));
  }

  const response = await fetch(
    `${API_BASE}/documents${query.size ? `?${query.toString()}` : ""}`,
  );

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }

  return (await response.json()) as PolicyDocumentOptionList;
}
