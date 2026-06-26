ALTER TABLE kb_policy_chunk
    ALTER COLUMN embedding TYPE vector(1024);

COMMENT ON COLUMN kb_policy_chunk.embedding IS '文本向量，当前维度为 1024。';
