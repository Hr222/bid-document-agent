export type RetrievalHit = {
  document_id: number;
  version_id: number;
  chunk_id: number;
  policy_name: string;
  policy_category: string;
  responsible_department: string | null;
  version_label: string;
  section_title: string | null;
  section_path: string | null;
  page_no: number | null;
  chunk_text: string;
  score: number;
  rank: number;
  retrieval_source: string;
  score_breakdown: Record<string, number>;
};

export type RetrievalStageDebug = {
  name: string;
  source: string | null;
  input_count: number | null;
  output_count: number | null;
  details: Record<string, string | number | boolean | null>;
};

export type RetrievalDebugInfo = {
  pipeline: string;
  strategy: string;
  min_score: number;
  stages: RetrievalStageDebug[];
};

export type RetrievalSearchRequest = {
  query: string;
  topK: number;
  policyCategory: string;
  responsibleDepartment: string;
  documentId: string;
  includeHistory: boolean;
};

export type RetrievalSearchResponse = {
  query: string;
  top_k: number;
  filters: {
    policy_category: string | null;
    responsible_department: string | null;
    document_id: number | null;
    include_history: boolean;
  };
  hits: RetrievalHit[];
  debug: RetrievalDebugInfo;
};

export type AnswerCitation = {
  ref_no: number;
  document_id: number;
  version_id: number;
  chunk_id: number;
  policy_name: string;
  section_title: string | null;
  page_no: number | null;
  quote: string;
};

export type RagAskRequest = RetrievalSearchRequest;

export type RagAskResponse = {
  query: string;
  answer: string;
  model: string | null;
  citations: AnswerCitation[];
  hits: RetrievalHit[];
  debug: RetrievalDebugInfo | null;
};
