import type { FormEvent } from "react";

import { UI_TEXT } from "../constants/uiText";
import type { PolicyDocumentOption } from "../types/knowledgeBase";

type UploadFormProps = {
  selectedFile: File | null;
  policyCategory: string;
  responsibleDepartment: string;
  versionLabel: string;
  documentSearch: string;
  documentOptions: PolicyDocumentOption[];
  selectedTargetDocumentId: string;
  loadingAction: "preview" | "ingest" | null;
  canPreview: boolean;
  canIngest: boolean;
  errorMessage: string | null;
  onFileSelect: (file: File | null) => void;
  onPolicyCategoryChange: (value: string) => void;
  onResponsibleDepartmentChange: (value: string) => void;
  onVersionLabelChange: (value: string) => void;
  onDocumentSearchChange: (value: string) => void;
  onTargetDocumentChange: (value: string) => void;
  onPreview: (event: FormEvent<HTMLFormElement>) => void;
  onIngest: () => void;
};

function formatFileSummary(file: File | null): string {
  if (!file) {
    return UI_TEXT.supportedTypes;
  }

  return `${(file.size / 1024).toFixed(1)} KB`;
}

export function UploadForm({
  selectedFile,
  policyCategory,
  responsibleDepartment,
  versionLabel,
  documentSearch,
  documentOptions,
  selectedTargetDocumentId,
  loadingAction,
  canPreview,
  canIngest,
  errorMessage,
  onFileSelect,
  onPolicyCategoryChange,
  onResponsibleDepartmentChange,
  onVersionLabelChange,
  onDocumentSearchChange,
  onTargetDocumentChange,
  onPreview,
  onIngest,
}: UploadFormProps) {
  return (
    <form className="panel form-panel" onSubmit={onPreview}>
      <div className="panel-heading">
        <h2>{UI_TEXT.formTitle}</h2>
        <p>{UI_TEXT.formIntro}</p>
      </div>

      <label className="field">
        <span>{UI_TEXT.fileLabel}</span>
        <input
          type="file"
          accept=".docx,.pdf"
          onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
        />
      </label>

      <div className="field-grid">
        <label className="field">
          <span>{UI_TEXT.categoryLabel}</span>
          <input
            value={policyCategory}
            onChange={(event) => onPolicyCategoryChange(event.target.value)}
            placeholder={UI_TEXT.categoryPlaceholder}
          />
        </label>

        <label className="field">
          <span>{UI_TEXT.departmentLabel}</span>
          <input
            value={responsibleDepartment}
            onChange={(event) => onResponsibleDepartmentChange(event.target.value)}
            placeholder={UI_TEXT.departmentPlaceholder}
          />
        </label>
      </div>

      <label className="field">
        <span>{UI_TEXT.versionLabel}</span>
        <input
          value={versionLabel}
          onChange={(event) => onVersionLabelChange(event.target.value)}
          placeholder={UI_TEXT.versionPlaceholder}
        />
      </label>

      <div className="field">
        <span>{UI_TEXT.targetDocumentLabel}</span>
        <input
          value={documentSearch}
          onChange={(event) => onDocumentSearchChange(event.target.value)}
          placeholder={UI_TEXT.targetDocumentSearchPlaceholder}
        />
        <select
          className="select-field"
          value={selectedTargetDocumentId}
          onChange={(event) => onTargetDocumentChange(event.target.value)}
        >
          <option value="">{UI_TEXT.targetDocumentEmptyOption}</option>
          {documentOptions.map((item) => (
            <option key={item.document_id} value={item.document_id}>
              {`${item.policy_name} · ${item.policy_category}${
                item.latest_version_label ? ` · ${item.latest_version_label}` : ""
              }`}
            </option>
          ))}
        </select>
      </div>

      <div className="file-summary">
        <span>{UI_TEXT.currentFile}</span>
        <strong>{selectedFile?.name ?? UI_TEXT.noFileSelected}</strong>
        <span>{formatFileSummary(selectedFile)}</span>
      </div>

      <div className="actions">
        <button type="submit" disabled={!canPreview}>
          {loadingAction === "preview" ? UI_TEXT.previewing : UI_TEXT.preview}
        </button>
        <button type="button" className="secondary" disabled={!canIngest} onClick={onIngest}>
          {loadingAction === "ingest" ? UI_TEXT.ingesting : UI_TEXT.confirmIngest}
        </button>
      </div>

      {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
    </form>
  );
}
