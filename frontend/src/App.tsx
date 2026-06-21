import { ChangeEvent, FormEvent, useMemo, useState } from "react";

type PipelineStage = {
  stage: string;
  status: "pending" | "skipped" | "success" | "failed";
  message: string;
};

type SectionItem = {
  section_no: string | null;
  section_title: string | null;
  section_level: number;
  section_path: string | null;
  section_order: number;
  section_text: string;
};

type PipelineResponse = {
  mode: "preview" | "ingest";
  source_path: string;
  started_at: string;
  stages: PipelineStage[];
  policy_name_guess: string | null;
  derived_version_label: string | null;
  parsed_text?: {
    parser_status: string;
    suspected_scanned: boolean;
    notes: string[];
    title_candidates: string[];
    page_count: number | null;
  } | null;
  cleaned_text?: {
    clean_text: string;
    removed_noise_examples: string[];
    notes: string[];
  } | null;
  section_result?: {
    total_sections: number;
    strategy: string;
    notes: string[];
    sections: SectionItem[];
  } | null;
  persistence?: {
    persisted: boolean;
    document_id: number | null;
    version_id: number | null;
    version_seq: number | null;
    version_label: string | null;
    section_count: number;
    message: string;
  } | null;
};

type PreviewUploadResponse = PipelineResponse & {
  upload_id: string;
};

const API_BASE = "/api/v1/kb/policy-pipeline";

const UI_TEXT = {
  defaultDepartment: "\u7EFC\u5408\u7BA1\u7406\u90E8",
  defaultCategory: "\u7BA1\u7406\u5236\u5EA6",
  requestFailed: "\u8BF7\u6C42\u5931\u8D25",
  chooseFileFirst: "\u8BF7\u5148\u9009\u62E9\u4E00\u4E2A\u8981\u5165\u5E93\u7684\u6587\u4EF6\u3002",
  previewFailed: "\u9884\u89C8\u5931\u8D25\u3002",
  previewFirst: "\u8BF7\u5148\u5B8C\u6210\u9884\u89C8\u3002",
  ingestFailed: "\u5165\u5E93\u5931\u8D25\u3002",
  appTitle: "\u5355\u6587\u4EF6\u5165\u5E93\u5DE5\u4F5C\u53F0",
  appIntro:
    "\u5148\u9009\u4E00\u4E2A\u6587\u4EF6\uFF0C\u5B8C\u6210\u9884\u89C8\u548C\u4EBA\u5DE5\u590D\u6838\uFF0C\u518D\u786E\u8BA4\u6B63\u5F0F\u5165\u5E93\u3002\u8FD9\u4E2A MVP \u53EA\u5904\u7406\u5355\u4E2A\u6587\u4EF6\uFF0C\u65B9\u4FBF\u6211\u4EEC\u628A\u540E\u7AEF\u94FE\u8DEF\u4E00\u70B9\u70B9\u8DD1\u7A33\u3002",
  formTitle: "\u5BFC\u5165\u8868\u5355",
  formIntro: "\u4E0A\u4F20\u4E00\u6B21\uFF0C\u5148\u9884\u89C8\uFF0C\u518D\u51B3\u5B9A\u662F\u5426\u843D\u5E93\u3002",
  fileLabel: "\u5F85\u5165\u5E93\u6587\u4EF6",
  categoryLabel: "\u8D44\u6599\u5206\u7C7B",
  categoryPlaceholder: "\u4F8B\u5982\uFF1A\u7BA1\u7406\u5236\u5EA6",
  departmentLabel: "\u8D23\u4EFB\u90E8\u95E8",
  departmentPlaceholder: "\u4F8B\u5982\uFF1A\u7EFC\u5408\u7BA1\u7406\u90E8",
  versionLabel: "\u7248\u672C\u6807\u7B7E\uFF08\u53EF\u9009\uFF09",
  versionPlaceholder: "\u4E0D\u586B\u65F6\u5C06\u7531\u540E\u7AEF\u81EA\u52A8\u63A8\u5BFC",
  currentFile: "\u5F53\u524D\u6587\u4EF6",
  noFileSelected: "\u5C1A\u672A\u9009\u62E9\u6587\u4EF6",
  supportedTypes: "\u652F\u6301 .docx / .pdf",
  previewing: "\u9884\u89C8\u4E2D...",
  preview: "\u5148\u9884\u89C8",
  ingesting: "\u5165\u5E93\u4E2D...",
  confirmIngest: "\u786E\u8BA4\u5165\u5E93",
  resultTitle: "\u7ED3\u679C\u603B\u89C8",
  resultIntro: "\u628A\u6BCF\u4E2A\u9636\u6BB5\u7684\u8FD4\u56DE\u90FD\u644A\u5F00\uFF0C\u65B9\u4FBF\u4F60\u6838\u5BF9\u540E\u7AEF\u884C\u4E3A\u3002",
  mode: "\u6A21\u5F0F",
  guessedName: "\u5236\u5EA6\u540D\u79F0\u731C\u6D4B",
  versionTag: "\u7248\u672C\u6807\u7B7E",
  sectionCount: "\u7AE0\u8282\u6570",
  none: "\u65E0",
  stageStatus: "\u9636\u6BB5\u72B6\u6001",
  parseNotes: "\u89E3\u6790\u63D0\u793A",
  noParseNotes: "\u5F53\u524D\u65E0\u989D\u5916\u89E3\u6790\u5907\u6CE8\u3002",
  cleanNotes: "\u6E05\u6D17\u8BF4\u660E",
  noCleanNotes: "\u5F53\u524D\u65E0\u989D\u5916\u6E05\u6D17\u8BF4\u660E\u3002",
  removedNoise: "\u6E05\u6D17\u6389\u7684\u566A\u97F3\u793A\u4F8B",
  noRemovedNoise: "\u5F53\u524D\u6CA1\u6709\u8BC6\u522B\u5230\u53EF\u5220\u9664\u566A\u97F3\u3002",
  titleCandidates: "\u6807\u9898\u5019\u9009",
  noTitleCandidates: "\u5F53\u524D\u6CA1\u6709\u8BC6\u522B\u5230\u660E\u663E\u6807\u9898\u3002",
  sectionPreview: "\u7AE0\u8282\u9884\u89C8",
  fullText: "\u5168\u6587",
  noSectionPath: "\u672A\u751F\u6210\u7AE0\u8282\u8DEF\u5F84",
  noSectionsYet: "\u9884\u89C8\u5B8C\u6210\u540E\uFF0C\u8FD9\u91CC\u4F1A\u663E\u793A\u7AE0\u8282\u62C6\u5206\u7ED3\u679C\u3002",
  persistenceTitle: "\u5165\u5E93\u7ED3\u679C",
  persistenceEmpty: "\u786E\u8BA4\u5165\u5E93\u540E\uFF0C\u8FD9\u91CC\u4F1A\u663E\u793A\u843D\u5E93\u7ED3\u679C\u3002",
  noResultsYet: "\u8FD8\u6CA1\u6709\u7ED3\u679C\u3002\u5148\u9009\u4E00\u4E2A\u6587\u4EF6\uFF0C\u7136\u540E\u70B9\u201C\u5148\u9884\u89C8\u201D\u3002",
} as const;

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // ignore parse error
  }
  return `${UI_TEXT.requestFailed}: ${response.status}`;
}

export default function App() {
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

  const canPreview = Boolean(selectedFile) && loadingAction === null;
  const canIngest = Boolean(previewResult?.upload_id) && loadingAction === null;

  const currentResult = useMemo(
    () => ingestResult ?? previewResult,
    [ingestResult, previewResult],
  );

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setPreviewResult(null);
    setIngestResult(null);
    setErrorMessage(null);
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

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("policy_category", policyCategory);
    formData.append("responsible_department", responsibleDepartment);
    if (versionLabel.trim()) {
      formData.append("version_label", versionLabel.trim());
    }

    try {
      const response = await fetch(`${API_BASE}/preview-upload`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await parseError(response));
      }
      const payload = (await response.json()) as PreviewUploadResponse;
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

    setLoadingAction("ingest");
    setErrorMessage(null);
    setIngestResult(null);

    try {
      const response = await fetch(`${API_BASE}/ingest-upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          upload_id: previewResult.upload_id,
          policy_category: policyCategory,
          responsible_department: responsibleDepartment || null,
          version_label: versionLabel.trim() || null,
        }),
      });
      if (!response.ok) {
        throw new Error(await parseError(response));
      }
      const payload = (await response.json()) as PipelineResponse;
      setIngestResult(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : UI_TEXT.ingestFailed);
    } finally {
      setLoadingAction(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <p className="eyebrow">Bid Document Agent</p>
        <h1>{UI_TEXT.appTitle}</h1>
        <p className="lede">{UI_TEXT.appIntro}</p>
      </section>

      <section className="workspace">
        <form className="panel form-panel" onSubmit={handlePreview}>
          <div className="panel-heading">
            <h2>{UI_TEXT.formTitle}</h2>
            <p>{UI_TEXT.formIntro}</p>
          </div>

          <label className="field">
            <span>{UI_TEXT.fileLabel}</span>
            <input type="file" accept=".docx,.pdf" onChange={handleFileChange} />
          </label>

          <div className="field-grid">
            <label className="field">
              <span>{UI_TEXT.categoryLabel}</span>
              <input
                value={policyCategory}
                onChange={(event) => setPolicyCategory(event.target.value)}
                placeholder={UI_TEXT.categoryPlaceholder}
              />
            </label>

            <label className="field">
              <span>{UI_TEXT.departmentLabel}</span>
              <input
                value={responsibleDepartment}
                onChange={(event) => setResponsibleDepartment(event.target.value)}
                placeholder={UI_TEXT.departmentPlaceholder}
              />
            </label>
          </div>

          <label className="field">
            <span>{UI_TEXT.versionLabel}</span>
            <input
              value={versionLabel}
              onChange={(event) => setVersionLabel(event.target.value)}
              placeholder={UI_TEXT.versionPlaceholder}
            />
          </label>

          <div className="file-summary">
            <span>{UI_TEXT.currentFile}</span>
            <strong>{selectedFile?.name ?? UI_TEXT.noFileSelected}</strong>
            <span>
              {selectedFile
                ? `${(selectedFile.size / 1024).toFixed(1)} KB`
                : UI_TEXT.supportedTypes}
            </span>
          </div>

          <div className="actions">
            <button type="submit" disabled={!canPreview}>
              {loadingAction === "preview" ? UI_TEXT.previewing : UI_TEXT.preview}
            </button>
            <button
              type="button"
              className="secondary"
              disabled={!canIngest}
              onClick={handleIngest}
            >
              {loadingAction === "ingest" ? UI_TEXT.ingesting : UI_TEXT.confirmIngest}
            </button>
          </div>

          {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
        </form>

        <section className="panel result-panel">
          <div className="panel-heading">
            <h2>{UI_TEXT.resultTitle}</h2>
            <p>{UI_TEXT.resultIntro}</p>
          </div>

          {currentResult ? (
            <>
              <div className="summary-grid">
                <article className="metric">
                  <span>{UI_TEXT.mode}</span>
                  <strong>{currentResult.mode}</strong>
                </article>
                <article className="metric">
                  <span>{UI_TEXT.guessedName}</span>
                  <strong>{currentResult.policy_name_guess ?? UI_TEXT.none}</strong>
                </article>
                <article className="metric">
                  <span>{UI_TEXT.versionTag}</span>
                  <strong>{currentResult.derived_version_label ?? UI_TEXT.none}</strong>
                </article>
                <article className="metric">
                  <span>{UI_TEXT.sectionCount}</span>
                  <strong>{currentResult.section_result?.total_sections ?? 0}</strong>
                </article>
              </div>

              <div className="result-block">
                <h3>{UI_TEXT.stageStatus}</h3>
                <div className="stage-list">
                  {currentResult.stages.map((stage) => (
                    <article
                      key={`${stage.stage}-${stage.message}`}
                      className={`stage-item ${stage.status}`}
                    >
                      <div>
                        <strong>{stage.stage}</strong>
                        <p>{stage.message}</p>
                      </div>
                      <span>{stage.status}</span>
                    </article>
                  ))}
                </div>
              </div>

              <div className="result-block two-column">
                <article className="sub-panel">
                  <h3>{UI_TEXT.parseNotes}</h3>
                  <ul className="plain-list">
                    {(currentResult.parsed_text?.notes?.length
                      ? currentResult.parsed_text.notes
                      : [UI_TEXT.noParseNotes]
                    ).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </article>

                <article className="sub-panel">
                  <h3>{UI_TEXT.cleanNotes}</h3>
                  <ul className="plain-list">
                    {(currentResult.cleaned_text?.notes?.length
                      ? currentResult.cleaned_text.notes
                      : [UI_TEXT.noCleanNotes]
                    ).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </article>
              </div>

              <div className="result-block two-column">
                <article className="sub-panel">
                  <h3>{UI_TEXT.removedNoise}</h3>
                  <ul className="plain-list">
                    {(currentResult.cleaned_text?.removed_noise_examples?.length
                      ? currentResult.cleaned_text.removed_noise_examples
                      : [UI_TEXT.noRemovedNoise]
                    ).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </article>

                <article className="sub-panel">
                  <h3>{UI_TEXT.titleCandidates}</h3>
                  <ul className="plain-list">
                    {(currentResult.parsed_text?.title_candidates?.length
                      ? currentResult.parsed_text.title_candidates.slice(0, 8)
                      : [UI_TEXT.noTitleCandidates]
                    ).map((title) => (
                      <li key={title}>{title}</li>
                    ))}
                  </ul>
                </article>
              </div>

              <div className="result-block">
                <h3>{UI_TEXT.sectionPreview}</h3>
                <div className="section-list">
                  {(currentResult.section_result?.sections?.length
                    ? currentResult.section_result.sections.slice(0, 6)
                    : []
                  ).map((section) => (
                    <article
                      key={`${section.section_order}-${section.section_title ?? "full"}`}
                      className="section-item"
                    >
                      <div className="section-meta">
                        <strong>{section.section_title ?? UI_TEXT.fullText}</strong>
                        <span>{section.section_path ?? UI_TEXT.noSectionPath}</span>
                      </div>
                      <p>{section.section_text.slice(0, 160)}</p>
                    </article>
                  ))}
                  {!currentResult.section_result?.sections?.length ? (
                    <p className="empty-state">{UI_TEXT.noSectionsYet}</p>
                  ) : null}
                </div>
              </div>

              <div className="result-block">
                <h3>{UI_TEXT.persistenceTitle}</h3>
                {currentResult.persistence ? (
                  <div className="persistence-box">
                    <p>{currentResult.persistence.message}</p>
                    <div className="persistence-meta">
                      <span>document_id: {currentResult.persistence.document_id ?? "-"}</span>
                      <span>version_id: {currentResult.persistence.version_id ?? "-"}</span>
                      <span>version_seq: {currentResult.persistence.version_seq ?? "-"}</span>
                      <span>section_count: {currentResult.persistence.section_count}</span>
                    </div>
                  </div>
                ) : (
                  <p className="empty-state">{UI_TEXT.persistenceEmpty}</p>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state large">{UI_TEXT.noResultsYet}</div>
          )}
        </section>
      </section>
    </main>
  );
}
