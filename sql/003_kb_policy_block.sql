CREATE TABLE IF NOT EXISTS kb_policy_block (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    block_index INTEGER NOT NULL,
    page_no INTEGER,
    block_type TEXT NOT NULL,
    source_method TEXT NOT NULL,
    text TEXT,
    layout_hint JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_block UNIQUE (version_id, block_index),
    CONSTRAINT chk_kb_policy_block_index_non_negative CHECK (block_index >= 0),
    CONSTRAINT chk_kb_policy_block_type CHECK (
        block_type IN ('text', 'table', 'image', 'page_break')
    ),
    CONSTRAINT chk_kb_policy_block_source_method CHECK (
        source_method IN ('direct', 'ocr', 'mixed')
    )
);

COMMENT ON TABLE kb_policy_block IS '文档块表：保存文档流 block、OCR 来源和顺序位置，用于追踪解析结果。';
COMMENT ON COLUMN kb_policy_block.version_id IS '所属版本ID。';
COMMENT ON COLUMN kb_policy_block.block_index IS '块顺序号。';
COMMENT ON COLUMN kb_policy_block.page_no IS '页码。';
COMMENT ON COLUMN kb_policy_block.block_type IS '块类型：text/table/image/page_break。';
COMMENT ON COLUMN kb_policy_block.source_method IS '文本来源：direct/ocr/mixed。';
COMMENT ON COLUMN kb_policy_block.text IS '块文本内容。';
COMMENT ON COLUMN kb_policy_block.layout_hint IS '布局提示，例如 bbox、尺寸、宿主段落信息。';
COMMENT ON COLUMN kb_policy_block.metadata IS '扩展元数据。';

CREATE INDEX IF NOT EXISTS idx_kb_policy_block_version_id ON kb_policy_block(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_block_page_no ON kb_policy_block(page_no);
