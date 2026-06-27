import { UI_TEXT } from "../constants/uiText";
import type {
  RagAskRequest,
  RagAskResponse,
  RetrievalSearchRequest,
  RetrievalSearchResponse,
} from "../types/retrieval";

const API_BASE = "/api/v1/kb/retrieval";

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // ignore JSON parse failure and fall back to generic text
  }

  return `${UI_TEXT.requestFailed}: ${response.status}`;
}

function buildPayload(payload: RetrievalSearchRequest | RagAskRequest) {
  return {
    query: payload.query.trim(),
    top_k: payload.topK,
    policy_category: payload.policyCategory.trim() || null,
    responsible_department: payload.responsibleDepartment.trim() || null,
    document_id: payload.documentId.trim() ? Number(payload.documentId.trim()) : null,
    include_history: payload.includeHistory,
  };
}

export async function searchKnowledgeBase(
  payload: RetrievalSearchRequest,
): Promise<RetrievalSearchResponse> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(buildPayload(payload)),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as RetrievalSearchResponse;
}

export async function askKnowledgeBase(payload: RagAskRequest): Promise<RagAskResponse> {
  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(buildPayload(payload)),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as RagAskResponse;
}
