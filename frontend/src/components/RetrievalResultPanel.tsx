import { UI_TEXT } from "../constants/uiText";
import type { RagAskResponse, RetrievalSearchResponse } from "../types/retrieval";

type RetrievalResultPanelProps = {
  searchResult: RetrievalSearchResponse | null;
  answerResult: RagAskResponse | null;
};

function renderHits(
  hits: RetrievalSearchResponse["hits"] | RagAskResponse["hits"],
) {
  if (!hits.length) {
    return <p className="empty-state">{UI_TEXT.noRetrievalResults}</p>;
  }

  return (
    <div className="section-list">
      {hits.map((hit) => (
        <article key={`${hit.chunk_id}-${hit.rank}`} className="section-item">
          <div className="section-meta">
            <strong>{hit.policy_name}</strong>
            <span>{UI_TEXT.scoreLabel}: {hit.score.toFixed(4)}</span>
            <span>{UI_TEXT.versionTag}: {hit.version_label}</span>
            <span>{UI_TEXT.pageLabel}: {hit.page_no ?? UI_TEXT.none}</span>
          </div>
          <div className="section-meta">
            <span>{hit.section_title ?? UI_TEXT.fullText}</span>
            <span>{hit.section_path ?? UI_TEXT.noSectionPath}</span>
          </div>
          <p>{hit.chunk_text}</p>
        </article>
      ))}
    </div>
  );
}

export function RetrievalResultPanel({
  searchResult,
  answerResult,
}: RetrievalResultPanelProps) {
  const activeHits = answerResult?.hits ?? searchResult?.hits ?? [];

  return (
    <section className="panel result-panel">
      <div className="panel-heading">
        <h2>{UI_TEXT.retrievalResultTitle}</h2>
        <p>{UI_TEXT.retrievalResultIntro}</p>
      </div>

      {answerResult ? (
        <div className="result-block">
          <h3>{UI_TEXT.answerTitle}</h3>
          <div className="persistence-box">
            <p>{answerResult.answer}</p>
            <div className="persistence-meta">
              <span>{UI_TEXT.modelLabel}: {answerResult.model ?? UI_TEXT.none}</span>
              <span>{UI_TEXT.chunkCount}: {answerResult.hits.length}</span>
            </div>
          </div>
        </div>
      ) : null}

      {answerResult ? (
        <div className="result-block">
          <h3>{UI_TEXT.citationTitle}</h3>
          {answerResult.citations.length ? (
            <div className="section-list">
              {answerResult.citations.map((citation) => (
                <article key={`${citation.chunk_id}-${citation.ref_no}`} className="section-item">
                  <div className="section-meta">
                    <strong>[{citation.ref_no}] {citation.policy_name}</strong>
                    <span>{citation.section_title ?? UI_TEXT.fullText}</span>
                    <span>{UI_TEXT.pageLabel}: {citation.page_no ?? UI_TEXT.none}</span>
                  </div>
                  <p>{citation.quote}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">{UI_TEXT.noCitations}</p>
          )}
        </div>
      ) : null}

      <div className="result-block">
        <h3>{UI_TEXT.hitListTitle}</h3>
        {renderHits(activeHits)}
      </div>
    </section>
  );
}
