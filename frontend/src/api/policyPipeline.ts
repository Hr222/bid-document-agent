import { UI_TEXT } from "../constants/uiText";
import type { PipelineResponse, PreviewUploadResponse } from "../types/pipeline";

const API_BASE = "/api/v1/kb/policy-pipeline";

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // 忽略错误响应解析失败，回退到通用提示。
  }

  return `${UI_TEXT.requestFailed}: ${response.status}`;
}

export async function previewUpload(payload: {
  file: File;
  policyCategory: string;
  responsibleDepartment: string;
  versionLabel: string;
}): Promise<PreviewUploadResponse> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("policy_category", payload.policyCategory);
  formData.append("responsible_department", payload.responsibleDepartment);

  if (payload.versionLabel.trim()) {
    formData.append("version_label", payload.versionLabel.trim());
  }

  const response = await fetch(`${API_BASE}/preview-upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as PreviewUploadResponse;
}

export async function ingestUpload(payload: {
  uploadId: string;
  policyCategory: string;
  responsibleDepartment: string;
  versionLabel: string;
}): Promise<PipelineResponse> {
  const response = await fetch(`${API_BASE}/ingest-upload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      upload_id: payload.uploadId,
      policy_category: payload.policyCategory,
      responsible_department: payload.responsibleDepartment || null,
      version_label: payload.versionLabel.trim() || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as PipelineResponse;
}
