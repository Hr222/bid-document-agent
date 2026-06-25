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

function renderMode(mode: PipelineResponse["mode"]) {
  return UI_TEXT.modeLabels[mode] ?? mode;
}

function renderStage(stage: string) {
  return UI_TEXT.stageLabels[stage as keyof typeof UI_TEXT.stageLabels] ?? stage;
}

function renderStatus(status: string) {
  return UI_TEXT.statusLabels[status as keyof typeof UI_TEXT.statusLabels] ?? status;
}

function renderStrategy(strategy: string) {
  return UI_TEXT.strategyLabels[strategy as keyof typeof UI_TEXT.strategyLabels] ?? strategy;
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
              <strong>{renderMode(result.mode)}</strong>
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
                    <strong>{renderStage(stage.stage)}</strong>
                    <p>{stage.message}</p>
                  </div>
                  <span>{renderStatus(stage.status)}</span>
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
            <h3>{UI_TEXT.chunkPreview}</h3>
            <div className="section-list">
              {result.chunk_result?.sample_chunks?.length ? (
                result.chunk_result.sample_chunks.map((chunk, index) => (
                  <article key={`${chunk.section_path ?? "chunk"}-${index}`} className="section-item">
                    <div className="section-meta">
                      <strong>{chunk.section_title ?? UI_TEXT.fullText}</strong>
                      <span>{chunk.section_path ?? UI_TEXT.noSectionPath}</span>
                      <span>{UI_TEXT.charCount}: {chunk.char_count}</span>
                    </div>
                    <p>{chunk.chunk_preview}</p>
                  </article>
                ))
              ) : (
                <p className="empty-state">{UI_TEXT.noChunksYet}</p>
              )}
            </div>
            {result.chunk_result ? (
              <div className="persistence-meta">
                <span>{UI_TEXT.chunkCount}: {result.chunk_result.total_chunks}</span>
                <span>{UI_TEXT.chunkStrategy}: {renderStrategy(result.chunk_result.strategy)}</span>
              </div>
            ) : null}
          </div>

          <div className="result-block">
            <h3>{UI_TEXT.sectionPreview}</h3>
            <div className="section-list">
              {(result.section_result?.sections?.length
                ? result.section_result.sections.slice(0, 6)
                : [])
              .map((section) => (
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
                  <span>{UI_TEXT.documentId}: {result.persistence.document_id ?? "-"}</span>
                  <span>{UI_TEXT.versionId}: {result.persistence.version_id ?? "-"}</span>
                  <span>{UI_TEXT.versionSeq}: {result.persistence.version_seq ?? "-"}</span>
                  <span>{UI_TEXT.sectionCount}: {result.persistence.section_count}</span>
                  <span>{UI_TEXT.chunkCount}: {result.persistence.chunk_count}</span>
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
