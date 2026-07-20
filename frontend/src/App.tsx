import { FormEvent, useEffect, useMemo, useState } from "react";

import { listPolicyDocuments } from "./api/knowledgeBase";
import { askKnowledgeBase, searchKnowledgeBase } from "./api/knowledgeRetrieval";
import { ingestUpload, previewUpload } from "./api/policyPipeline";
import { RetrievalForm } from "./components/RetrievalForm";
import { RetrievalResultPanel } from "./components/RetrievalResultPanel";
import { ResultPanel } from "./components/ResultPanel";
import { UploadForm } from "./components/UploadForm";
import { UI_TEXT } from "./constants/uiText";
import type { PolicyDocumentOption } from "./types/knowledgeBase";
import type { PipelineResponse, PreviewUploadResponse } from "./types/pipeline";
import type { RagAskResponse, RetrievalSearchResponse } from "./types/retrieval";

type WorkspaceMode = "ingestion" | "retrieval";
const SUPPORTED_UPLOAD_EXTENSIONS = new Set(["docx", "pdf"]);
const STALE_TARGET_DOCUMENT_MESSAGE =
  "你之前选择的关联制度已经不存在了，可能是数据库已重建。我已经帮你清空这个选择，请重新选择后再试。";

export default function App() {
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("ingestion");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [policyCategory, setPolicyCategory] = useState<string>(UI_TEXT.defaultCategory);
  const [responsibleDepartment, setResponsibleDepartment] = useState<string>(
    UI_TEXT.defaultDepartment,
  );
  const [versionLabel, setVersionLabel] = useState("");
  const [previewResult, setPreviewResult] = useState<PreviewUploadResponse | null>(null);
  const [ingestResult, setIngestResult] = useState<PipelineResponse | null>(null);
  const [loadingAction, setLoadingAction] = useState<"preview" | "ingest" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [documentOptions, setDocumentOptions] = useState<PolicyDocumentOption[]>([]);
  const [documentSearch, setDocumentSearch] = useState("");
  const [selectedTargetDocument, setSelectedTargetDocument] = useState<PolicyDocumentOption | null>(null);

  const [query, setQuery] = useState("");
  const [retrievalTopK, setRetrievalTopK] = useState(5);
  const [retrievalCategory, setRetrievalCategory] = useState("");
  const [retrievalDepartment, setRetrievalDepartment] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [includeHistory, setIncludeHistory] = useState(false);
  const [retrievalLoadingAction, setRetrievalLoadingAction] = useState<"search" | "ask" | null>(
    null,
  );
  const [retrievalErrorMessage, setRetrievalErrorMessage] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<RetrievalSearchResponse | null>(null);
  const [answerResult, setAnswerResult] = useState<RagAskResponse | null>(null);

  const previewPassedValidation = Boolean(previewResult?.validation?.is_allowed);
  const ingestSucceeded = Boolean(ingestResult?.persistence?.persisted);
  const canPreview = Boolean(selectedFile) && loadingAction === null;
  const canIngest =
    Boolean(previewResult?.upload_id) &&
    previewPassedValidation &&
    !ingestSucceeded &&
    loadingAction === null;

  const currentResult = useMemo(
    () => ingestResult ?? previewResult,
    [ingestResult, previewResult],
  );

  useEffect(() => {
    void refreshDocumentOptions("");
  }, []);

  async function refreshDocumentOptions(search = documentSearch) {
    try {
      const payload = await listPolicyDocuments({
        search,
        limit: 50,
      });
      setDocumentOptions(payload.items);
      if (
        selectedTargetDocument &&
        !payload.items.some((item) => item.document_id === selectedTargetDocument.document_id)
      ) {
        setSelectedTargetDocument(null);
        setErrorMessage(STALE_TARGET_DOCUMENT_MESSAGE);
      }
    } catch {
      // 即使制度选项加载失败，也要保证当前上传流程仍然可以继续使用。
    }
  }

  function handleFileSelect(file: File | null) {
    if (file) {
      const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
      if (!SUPPORTED_UPLOAD_EXTENSIONS.has(extension)) {
        setSelectedFile(null);
        setPreviewResult(null);
        setIngestResult(null);
        setErrorMessage(UI_TEXT.unsupportedFileType);
        return;
      }
    }

    setSelectedFile(file);
    setPreviewResult(null);
    setIngestResult(null);
    setErrorMessage(null);
  }

  function handleDocumentSearchChange(value: string) {
    setDocumentSearch(value);
    void refreshDocumentOptions(value);
  }

  function handleTargetDocumentChange(documentId: string) {
    const next = documentOptions.find((item) => String(item.document_id) === documentId) ?? null;
    setSelectedTargetDocument(next);
  }

  async function handlePreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setErrorMessage(UI_TEXT.chooseFileFirst);
      return;
    }

    setLoadingAction("preview");
    setErrorMessage(null);
    setPreviewResult(null);
    setIngestResult(null);

    try {
      const payload = await previewUpload({
        file: selectedFile,
        policyCategory,
        responsibleDepartment,
        versionLabel,
      });
      setPreviewResult(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : UI_TEXT.previewFailed);
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleIngest() {
    if (!previewResult?.upload_id) {
      setErrorMessage(UI_TEXT.previewFirst);
      return;
    }
    if (!previewPassedValidation) {
      setErrorMessage(UI_TEXT.previewValidationFailed);
      return;
    }

    setLoadingAction("ingest");
    setErrorMessage(null);
    setIngestResult(null);

    try {
      const payload = await ingestUpload({
        uploadId: previewResult.upload_id,
        policyCategory,
        responsibleDepartment,
        versionLabel,
        targetDocumentId: selectedTargetDocument?.document_id ?? null,
      });
      setIngestResult(payload);
      void refreshDocumentOptions();
    } catch (error) {
      const message = error instanceof Error ? error.message : UI_TEXT.ingestFailed;
      if (message.includes("指定的已有关联制度不存在")) {
        setSelectedTargetDocument(null);
        setDocumentSearch("");
        void refreshDocumentOptions("");
        setErrorMessage(STALE_TARGET_DOCUMENT_MESSAGE);
        return;
      }
      setErrorMessage(message);
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!query.trim()) {
      setRetrievalErrorMessage(UI_TEXT.queryRequired);
      return;
    }

    setRetrievalLoadingAction("search");
    setRetrievalErrorMessage(null);
    setSearchResult(null);
    setAnswerResult(null);

    try {
      const payload = await searchKnowledgeBase({
        query,
        topK: retrievalTopK,
        policyCategory: retrievalCategory,
        responsibleDepartment: retrievalDepartment,
        documentId,
        includeHistory,
      });
      setSearchResult(payload);
    } catch (error) {
      setRetrievalErrorMessage(error instanceof Error ? error.message : UI_TEXT.retrievalFailed);
    } finally {
      setRetrievalLoadingAction(null);
    }
  }

  async function handleAsk() {
    if (!query.trim()) {
      setRetrievalErrorMessage(UI_TEXT.queryRequired);
      return;
    }

    setRetrievalLoadingAction("ask");
    setRetrievalErrorMessage(null);
    setSearchResult(null);
    setAnswerResult(null);

    try {
      const payload = await askKnowledgeBase({
        query,
        topK: retrievalTopK,
        policyCategory: retrievalCategory,
        responsibleDepartment: retrievalDepartment,
        documentId,
        includeHistory,
      });
      setAnswerResult(payload);
    } catch (error) {
      setRetrievalErrorMessage(error instanceof Error ? error.message : UI_TEXT.answerFailed);
    } finally {
      setRetrievalLoadingAction(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <p className="eyebrow">{UI_TEXT.appEyebrow}</p>
        <h1>{UI_TEXT.appTitle}</h1>
        <p className="lede">{UI_TEXT.appIntro}</p>
      </section>

      <section className="tab-strip">
        <button
          type="button"
          className={workspaceMode === "ingestion" ? "tab-button active" : "tab-button"}
          onClick={() => setWorkspaceMode("ingestion")}
        >
          {UI_TEXT.ingestionWorkspaceTitle}
        </button>
        <button
          type="button"
          className={workspaceMode === "retrieval" ? "tab-button active" : "tab-button"}
          onClick={() => setWorkspaceMode("retrieval")}
        >
          {UI_TEXT.retrievalWorkspaceTitle}
        </button>
      </section>

      {workspaceMode === "ingestion" ? (
        <section className="workspace">
          <UploadForm
            selectedFile={selectedFile}
            policyCategory={policyCategory}
            responsibleDepartment={responsibleDepartment}
            versionLabel={versionLabel}
            documentSearch={documentSearch}
            documentOptions={documentOptions}
            selectedTargetDocumentId={selectedTargetDocument ? String(selectedTargetDocument.document_id) : ""}
            loadingAction={loadingAction}
            canPreview={canPreview}
            canIngest={canIngest}
            errorMessage={errorMessage}
            onFileSelect={handleFileSelect}
            onPolicyCategoryChange={setPolicyCategory}
            onResponsibleDepartmentChange={setResponsibleDepartment}
            onVersionLabelChange={setVersionLabel}
            onDocumentSearchChange={handleDocumentSearchChange}
            onTargetDocumentChange={handleTargetDocumentChange}
            onPreview={handlePreview}
            onIngest={handleIngest}
          />

          <ResultPanel result={currentResult} />
        </section>
      ) : (
        <section className="workspace">
          <RetrievalForm
            query={query}
            topK={retrievalTopK}
            policyCategory={retrievalCategory}
            responsibleDepartment={retrievalDepartment}
            documentId={documentId}
            includeHistory={includeHistory}
            loadingAction={retrievalLoadingAction}
            errorMessage={retrievalErrorMessage}
            onQueryChange={setQuery}
            onTopKChange={setRetrievalTopK}
            onPolicyCategoryChange={setRetrievalCategory}
            onResponsibleDepartmentChange={setRetrievalDepartment}
            onDocumentIdChange={setDocumentId}
            onIncludeHistoryChange={setIncludeHistory}
            onSearch={handleSearch}
            onAsk={handleAsk}
          />

          <RetrievalResultPanel searchResult={searchResult} answerResult={answerResult} />
        </section>
      )}
    </main>
  );
}
