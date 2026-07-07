import { UI_TEXT } from "../constants/uiText";
import type {
  RagAskResponse,
  RetrievalDebugInfo,
  RetrievalSearchResponse,
} from "../types/retrieval";

// 调试信息里既有布尔值也有空值，这里统一转成界面可展示的字符串。
function formatDebugValue(value: string | number | boolean | null) {
  if (value === null) {
    return UI_TEXT.none;
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

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
            <span>{UI_TEXT.sourceLabel}: {hit.retrieval_source}</span>
            <span>{UI_TEXT.versionTag}: {hit.version_label}</span>
            <span>{UI_TEXT.pageLabel}: {hit.page_no ?? UI_TEXT.none}</span>
          </div>
          <div className="section-meta">
            <span>{hit.section_title ?? UI_TEXT.fullText}</span>
            <span>{hit.section_path ?? UI_TEXT.noSectionPath}</span>
          </div>
          <div className="section-meta">
            {/* 把后端返回的分数拆解直接展示出来，方便人工理解命中原因。 */}
            {Object.entries(hit.score_breakdown).map(([key, value]) => (
              <span key={key}>{`${key}: ${value.toFixed(4)}`}</span>
            ))}
          </div>
          <p>{hit.chunk_text}</p>
        </article>
      ))}
    </div>
  );
}

function renderDebugInfo(debug: RetrievalDebugInfo | null) {
  if (!debug) {
    return <p className="empty-state">{UI_TEXT.noDebugInfo}</p>;
  }

  return (
    <div className="section-list">
      <article className="section-item">
        <div className="section-meta">
          <strong>{UI_TEXT.pipelineLabel}: {debug.pipeline}</strong>
          <span>{UI_TEXT.strategyLabel}: {debug.strategy}</span>
          <span>{UI_TEXT.thresholdLabel}: {debug.min_score.toFixed(2)}</span>
        </div>
      </article>

      {/* 逐阶段展示检索链路，让前端也能看到“输入经过了哪些步骤、产出了多少结果”。 */}
      {debug.stages.map((stage) => (
        <article key={`${stage.name}-${stage.source ?? "none"}`} className="section-item">
          <div className="section-meta">
            <strong>{UI_TEXT.stageNameLabel}: {stage.name}</strong>
            <span>{UI_TEXT.sourceLabel}: {stage.source ?? UI_TEXT.none}</span>
            <span>{UI_TEXT.inputCountLabel}: {stage.input_count ?? UI_TEXT.none}</span>
            <span>{UI_TEXT.outputCountLabel}: {stage.output_count ?? UI_TEXT.none}</span>
          </div>
          <div className="section-meta">
            {Object.entries(stage.details).map(([key, value]) => (
              <span key={key}>{`${key}: ${formatDebugValue(value)}`}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

export function RetrievalResultPanel({
  searchResult,
  answerResult,
}: RetrievalResultPanelProps) {
  // ask 成功后优先展示问答链路返回的数据；否则回退到 search 结果。
  const activeHits = answerResult?.hits ?? searchResult?.hits ?? [];
  const debugInfo = answerResult?.debug ?? searchResult?.debug ?? null;

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

      <div className="result-block">
        <h3>{UI_TEXT.debugTitle}</h3>
        {renderDebugInfo(debugInfo)}
      </div>
    </section>
  );
}
