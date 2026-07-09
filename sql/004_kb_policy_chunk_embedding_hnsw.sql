CREATE INDEX IF NOT EXISTS idx_kb_policy_chunk_embedding_hnsw_cosine
    ON kb_policy_chunk USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
