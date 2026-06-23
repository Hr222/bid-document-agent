import { UI_TEXT } from "../constants/uiText";
import type { PipelineResponse } from "../types/pipeline";

type ResultPanelProps = {
  result: PipelineResponse | null;
};

function renderList(items: string[] | undefined, emptyText: string) {
  const values = items?.length ? items : [emptyText];

  return (
    <ul className="plain-list">
      {values.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function ResultPanel({ result }: ResultPanelProps) {
  return (
    <section className="panel result-panel">
      <div className="panel-heading">
        <h2>{UI_TEXT.resultTitle}</h2>
        <p>{UI_TEXT.resultIntro}</p>
      </div>

      {result ? (
        <>
          <div className="summary-grid">
            <article className="metric">
              <span>{UI_TEXT.mode}</span>
              <strong>{result.mode}</strong>
            </article>
            <article className="metric">
              <span>{UI_TEXT.guessedName}</span>
              <strong>{result.policy_name_guess ?? UI_TEXT.none}</strong>
            </article>
            <article className="metric">
              <span>{UI_TEXT.versionTag}</span>
              <strong>{result.derived_version_label ?? UI_TEXT.none}</strong>
            </article>
            <article className="metric">
              <span>{UI_TEXT.sectionCount}</span>
              <strong>{result.section_result?.total_sections ?? 0}</strong>
            </article>
          </div>

          <div className="result-block">
            <h3>{UI_TEXT.stageStatus}</h3>
            <div className="stage-list">
              {result.stages.map((stage) => (
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
              {renderList(result.parsed_text?.notes, UI_TEXT.noParseNotes)}
            </article>

            <article className="sub-panel">
              <h3>{UI_TEXT.cleanNotes}</h3>
              {renderList(result.cleaned_text?.notes, UI_TEXT.noCleanNotes)}
            </article>
          </div>

          <div className="result-block two-column">
            <article className="sub-panel">
              <h3>{UI_TEXT.removedNoise}</h3>
              {renderList(
                result.cleaned_text?.removed_noise_examples,
                UI_TEXT.noRemovedNoise,
              )}
            </article>

            <article className="sub-panel">
              <h3>{UI_TEXT.titleCandidates}</h3>
              {renderList(
                result.parsed_text?.title_candidates?.slice(0, 8),
                UI_TEXT.noTitleCandidates,
              )}
            </article>
          </div>

          <div className="result-block">
            <h3>{UI_TEXT.sectionPreview}</h3>
            <div className="section-list">
              {(result.section_result?.sections?.length
                ? result.section_result.sections.slice(0, 6)
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
              {!result.section_result?.sections?.length ? (
                <p className="empty-state">{UI_TEXT.noSectionsYet}</p>
              ) : null}
            </div>
          </div>

          <div className="result-block">
            <h3>{UI_TEXT.persistenceTitle}</h3>
            {result.persistence ? (
              <div className="persistence-box">
                <p>{result.persistence.message}</p>
                <div className="persistence-meta">
                  <span>document_id: {result.persistence.document_id ?? "-"}</span>
                  <span>version_id: {result.persistence.version_id ?? "-"}</span>
                  <span>version_seq: {result.persistence.version_seq ?? "-"}</span>
                  <span>section_count: {result.persistence.section_count}</span>
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
  );
}
