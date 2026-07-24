import { z } from "zod";

import type {
  KnowledgeBaseOverview,
  KnowledgeDocumentPage,
  KnowledgeIngestResult,
  KnowledgeDocument,
  KnowledgeSearchResponse,
  KnowledgeUploadPreview,
  ListKnowledgeDocumentsParams,
  UploadDocumentRequest,
} from "../types";

const documentSchema = z.object({
  id: z.number(),
  name: z.string(),
  type: z.enum(["PDF", "DOCX", "XLSX"]),
  size: z.string(),
  category: z.string(),
  version: z.string(),
  status: z.enum(["ready", "processing", "failed"]),
  progress: z.number().optional(),
  chunks: z.number(),
  updatedAt: z.string(),
  updatedBy: z.string(),
  error: z.string().optional(),
});

const retrievalResults = [
  {
    id: 1,
    title: "申请材料完整性核验",
    source: "委托评估机构申请材料核验制度.pdf",
    section: "第三章 / 申请材料核验",
    page: "第 8 页",
    score: 0.942,
    text: "申请机构应提交营业执照、资质证书、法定代表人身份证明及近三年项目业绩等证明材料。材料缺失时，应标记为待补充，不得直接判定为符合。",
    tags: ["业务制度", "引用明确"],
  },
  {
    id: 2,
    title: "材料核验结果分级",
    source: "委托评估机构申请材料核验制度.pdf",
    section: "第四章 / 结果处理",
    page: "第 12 页",
    score: 0.887,
    text: "核验结果分为通过、不通过和证据不足三类。对于无法由现有材料确认的事项，应保留原始依据并输出证据不足。",
    tags: ["结果规则", "可追溯"],
  },
  {
    id: 3,
    title: "供应商资质有效期",
    source: "供应商准入与资质审查办法.docx",
    section: "第二章 / 资质要求",
    page: "第 4 页",
    score: 0.812,
    text: "供应商提交的资质证明应处于有效期内。资质即将到期的，应在准入记录中标注风险提示，并由业务人员进行人工确认。",
    tags: ["采购管理", "风险提示"],
  },
] as const;

let documents: KnowledgeDocument[] = [
  { id: 101, name: "委托评估机构申请材料核验制度.pdf", type: "PDF", size: "4.8 MB", category: "业务制度", version: "v2.1", status: "ready", chunks: 1284, updatedAt: "今天 09:42", updatedBy: "系统管理员" },
  { id: 102, name: "供应商准入与资质审查办法.docx", type: "DOCX", size: "1.6 MB", category: "采购管理", version: "v1.4", status: "ready", chunks: 862, updatedAt: "昨天 16:08", updatedBy: "林晓" },
  { id: 103, name: "2024 年度风险评估口径说明.pdf", type: "PDF", size: "6.2 MB", category: "风险管理", version: "v1.0", status: "processing", progress: 68, chunks: 0, updatedAt: "昨天 14:26", updatedBy: "周然" },
  { id: 104, name: "项目材料清单与归档规范.xlsx", type: "XLSX", size: "920 KB", category: "档案管理", version: "v3.0", status: "ready", chunks: 436, updatedAt: "07 月 21 日", updatedBy: "系统管理员" },
  { id: 105, name: "历史项目验收标准（待修复）.pdf", type: "PDF", size: "2.1 MB", category: "项目管理", version: "v0.9", status: "failed", chunks: 0, updatedAt: "07 月 20 日", updatedBy: "陈默", error: "文档解析失败：未识别到有效文本层，请重新上传可复制文本的文件。" },
  { id: 106, name: "外部合作机构管理细则.pdf", type: "PDF", size: "3.4 MB", category: "合作管理", version: "v2.0", status: "ready", chunks: 974, updatedAt: "07 月 18 日", updatedBy: "林晓" },
];

const pendingUploads = new Map<string, UploadDocumentRequest>();

function wait<T>(value: T, delay = 180): Promise<T> {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), delay));
}

function parseDocuments(value: KnowledgeDocument[]) {
  return value.map((document) => documentSchema.parse(document));
}

export const knowledgeBaseMockApi = {
  async getOverview(): Promise<KnowledgeBaseOverview> {
    const parsed = parseDocuments(documents);
    return wait({
      documentCount: parsed.length,
      chunkCount: parsed.reduce((sum, document) => sum + document.chunks, 0),
      retrievalAvailability: 99.8,
      pendingCount: parsed.filter((document) => document.status === "processing").length,
      failedCount: parsed.filter((document) => document.status === "failed").length,
      updatedAt: "刚刚",
    });
  },

  async listDocuments(params: ListKnowledgeDocumentsParams): Promise<KnowledgeDocument[]> {
    const keyword = params.search?.trim().toLowerCase() ?? "";
    const filtered = documents.filter((document) => {
      const matchesKeyword = !keyword || document.name.toLowerCase().includes(keyword);
      const matchesStatus = !params.statuses?.length || params.statuses.includes(document.status);
      const matchesCategory = !params.category || document.category === params.category;
      return matchesKeyword && matchesStatus && matchesCategory;
    });
    const offset = params.offset ?? 0;
    const limit = params.limit ?? filtered.length;
    return wait(parseDocuments(filtered.slice(offset, offset + limit)));
  },

  async listDocumentsPage(params: ListKnowledgeDocumentsParams): Promise<KnowledgeDocumentPage> {
    const keyword = params.search?.trim().toLowerCase() ?? "";
    const filtered = documents.filter((document) => {
      const matchesKeyword = !keyword || document.name.toLowerCase().includes(keyword);
      const matchesStatus = !params.statuses?.length || params.statuses.includes(document.status);
      const matchesCategory = !params.category || document.category === params.category;
      return matchesKeyword && matchesStatus && matchesCategory;
    });
    const offset = params.offset ?? 0;
    const limit = params.limit ?? 10;
    return wait({
      items: parseDocuments(filtered.slice(offset, offset + limit)),
      totalCount: filtered.length,
    });
  },

  async listRecentDocuments(params: ListKnowledgeDocumentsParams): Promise<KnowledgeDocument[]> {
    const documents = await this.listDocuments({ ...params, limit: params.limit ?? 6, offset: 0 });
    return documents;
  },

  async listCategories(): Promise<string[]> {
    return wait([...new Set(documents.map((document) => document.category))].sort());
  },

  async previewUpload(request: UploadDocumentRequest): Promise<KnowledgeUploadPreview> {
    const uploadId = `mock-${Date.now()}`;
    pendingUploads.set(uploadId, request);
    return wait({
      uploadId,
      fileName: request.file.name,
      category: request.category,
      policyNameGuess: request.file.name.replace(/\.[^.]+$/, ""),
      versionLabel: "v1.0",
      fileSizeBytes: request.file.size,
      isAllowed: true,
      warnings: [],
      sectionCount: 12,
      chunkCount: 96,
    });
  },

  async ingestUpload(preview: KnowledgeUploadPreview): Promise<KnowledgeIngestResult> {
    const request = pendingUploads.get(preview.uploadId);
    if (!request) throw new Error("上传预览已失效，请重新选择文件。");
    pendingUploads.delete(preview.uploadId);

    const fileName = request.file.name;
    const type = fileName.toLowerCase().endsWith(".docx") ? "DOCX" : fileName.toLowerCase().endsWith(".xlsx") ? "XLSX" : "PDF";
    const document: KnowledgeDocument = {
      id: Date.now(),
      name: fileName,
      type,
      size: "1.8 MB",
      category: request.category,
      version: "v1.0",
      status: "ready",
      progress: 100,
      chunks: preview.chunkCount,
      updatedAt: "刚刚",
      updatedBy: "当前用户",
    };
    documents = [document, ...documents];
    return wait({
      documentId: document.id,
      versionId: document.id,
      versionLabel: document.version,
      chunkCount: document.chunks,
      persisted: true,
    });
  },

  async activatePublication(_documentId: number, _versionId: number): Promise<void> {
    await wait(undefined, 80);
  },

  async retryDocument(documentId: number): Promise<KnowledgeDocument> {
    const index = documents.findIndex((document) => document.id === documentId);
    if (index < 0) throw new Error("文档不存在或已被删除。");
    const next = { ...documents[index], status: "processing" as const, progress: 18, error: undefined };
    documents = documents.map((document) => document.id === documentId ? next : document);
    return wait(parseDocuments([next])[0]);
  },

  async search(query: string, topK = 5): Promise<KnowledgeSearchResponse> {
    return wait({
      query,
      strategy: "mock",
      stages: [],
      results: retrievalResults
        .slice(0, topK)
        .map((result) => ({ ...result, tags: [...result.tags] })),
    });
  },
};
