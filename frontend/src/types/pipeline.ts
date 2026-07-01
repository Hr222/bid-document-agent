export type PipelineStage = {
  stage: string;
  status: "pending" | "skipped" | "success" | "failed";
  message: string;
};

export type SectionItem = {
  section_no: string | null;
  section_title: string | null;
  section_level: number;
  section_path: string | null;
  section_order: number;
  section_text: string;
};

export type ChunkSampleItem = {
  section_title: string | null;
  section_path: string | null;
  chunk_preview: string;
  char_count: number;
};

export type PipelineResponse = {
  mode: "preview" | "ingest";
  source_path: string;
  started_at: string;
  stages: PipelineStage[];
  policy_name_guess: string | null;
  derived_version_label: string | null;
  target_document_id?: number | null;
  validation?: {
    is_allowed: boolean;
    detected_file_kind: string;
    needs_normalization: boolean;
    recommended_parse_method: string;
    warnings: string[];
  } | null;
  parsed_text?: {
    parser_status: string;
    parse_method: "direct" | "ocr" | "mixed";
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
  chunk_result?: {
    total_chunks: number;
    strategy: string;
    notes: string[];
    sample_chunks: ChunkSampleItem[];
  } | null;
  persistence?: {
    persisted: boolean;
    document_id: number | null;
    version_id: number | null;
    version_seq: number | null;
    version_label: string | null;
    section_count: number;
    chunk_count: number;
    message: string;
  } | null;
};

export type PreviewUploadResponse = PipelineResponse & {
  upload_id: string;
};
