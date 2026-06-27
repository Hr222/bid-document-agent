import type { FormEvent } from "react";

import { UI_TEXT } from "../constants/uiText";

type RetrievalFormProps = {
  query: string;
  topK: number;
  policyCategory: string;
  responsibleDepartment: string;
  documentId: string;
  includeHistory: boolean;
  loadingAction: "search" | "ask" | null;
  errorMessage: string | null;
  onQueryChange: (value: string) => void;
  onTopKChange: (value: number) => void;
  onPolicyCategoryChange: (value: string) => void;
  onResponsibleDepartmentChange: (value: string) => void;
  onDocumentIdChange: (value: string) => void;
  onIncludeHistoryChange: (value: boolean) => void;
  onSearch: (event: FormEvent<HTMLFormElement>) => void;
  onAsk: () => void;
};

export function RetrievalForm({
  query,
  topK,
  policyCategory,
  responsibleDepartment,
  documentId,
  includeHistory,
  loadingAction,
  errorMessage,
  onQueryChange,
  onTopKChange,
  onPolicyCategoryChange,
  onResponsibleDepartmentChange,
  onDocumentIdChange,
  onIncludeHistoryChange,
  onSearch,
  onAsk,
}: RetrievalFormProps) {
  const disabled = loadingAction !== null;
  const queryMissing = !query.trim();

  return (
    <form className="panel form-panel" onSubmit={onSearch}>
      <div className="panel-heading">
        <h2>{UI_TEXT.retrievalTitle}</h2>
        <p>{UI_TEXT.retrievalIntro}</p>
      </div>

      <label className="field">
        <span>{UI_TEXT.queryLabel}</span>
        <textarea
          className="query-textarea"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder={UI_TEXT.queryPlaceholder}
        />
      </label>

      <div className="field-grid">
        <label className="field">
          <span>{UI_TEXT.topKLabel}</span>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(event) => onTopKChange(Number(event.target.value) || 1)}
          />
        </label>

        <label className="field">
          <span>{UI_TEXT.documentIdLabel}</span>
          <input
            value={documentId}
            onChange={(event) => onDocumentIdChange(event.target.value)}
            placeholder={UI_TEXT.documentIdPlaceholder}
          />
        </label>
      </div>

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

      <label className="checkbox-field">
        <input
          type="checkbox"
          checked={includeHistory}
          onChange={(event) => onIncludeHistoryChange(event.target.checked)}
        />
        <span>{UI_TEXT.includeHistoryLabel}</span>
      </label>

      <div className="actions">
        <button type="submit" disabled={disabled || queryMissing}>
          {loadingAction === "search" ? UI_TEXT.searching : UI_TEXT.searchOnly}
        </button>
        <button
          type="button"
          className="secondary"
          disabled={disabled || queryMissing}
          onClick={onAsk}
        >
          {loadingAction === "ask" ? UI_TEXT.asking : UI_TEXT.searchAndAsk}
        </button>
      </div>

      {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
    </form>
  );
}
