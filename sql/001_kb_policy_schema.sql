-- 政策知识库表结构
-- 第一阶段：制度主档 / 版本管理 / 审核留痕 / 检索切块
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

/*
政策主档表
字段：id, policy_code, policy_name, policy_type, department_owner,
current_version_id, status, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_document (
    id BIGSERIAL PRIMARY KEY,
    policy_code TEXT UNIQUE,
    policy_name TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    department_owner TEXT,
    current_version_id BIGINT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE kb_policy_document IS '政策主档表：记录一项制度或规范的基础信息和当前状态。';
COMMENT ON COLUMN kb_policy_document.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_document.policy_code IS '政策唯一编码或外部编号。';
COMMENT ON COLUMN kb_policy_document.policy_name IS '政策名称。';
COMMENT ON COLUMN kb_policy_document.policy_type IS '政策类型或分类。';
COMMENT ON COLUMN kb_policy_document.department_owner IS '归口管理部门。';
COMMENT ON COLUMN kb_policy_document.current_version_id IS '当前生效版本ID，由业务侧维护。';
COMMENT ON COLUMN kb_policy_document.status IS '主档状态，例如 active、archived。';
COMMENT ON COLUMN kb_policy_document.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_document.updated_at IS '更新时间。';

/*
政策版本表
字段：id, policy_id, version_seq, version_label, source_year,
source_document_date, issued_at, effective_date, expired_at,
supersedes_version_id, revision_type, change_summary, change_reason,
source_path, file_name, file_ext, file_hash, is_scanned, parse_method,
raw_text, clean_text, page_count, parser_status, version_status,
ingested_at, reviewed_at, approved_at, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_version (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    version_seq INTEGER NOT NULL,
    version_label TEXT,
    source_year INTEGER,
    source_document_date DATE,
    issued_at DATE,
    effective_date DATE,
    expired_at DATE,
    supersedes_version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    revision_type TEXT NOT NULL DEFAULT 'revise',
    change_summary TEXT,
    change_reason TEXT,
    source_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_ext TEXT,
    file_hash TEXT,
    is_scanned BOOLEAN NOT NULL DEFAULT FALSE,
    parse_method TEXT NOT NULL DEFAULT 'direct',
    raw_text TEXT,
    clean_text TEXT,
    page_count INTEGER,
    parser_status TEXT NOT NULL DEFAULT 'pending',
    version_status TEXT NOT NULL DEFAULT 'draft',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_version UNIQUE (policy_id, version_seq)
);

COMMENT ON TABLE kb_policy_version IS '政策版本表：记录某一政策的具体版本及其来源文件信息。';
COMMENT ON COLUMN kb_policy_version.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_version.policy_id IS '所属政策主档ID。';
COMMENT ON COLUMN kb_policy_version.version_seq IS '同一政策内的版本序号。';
COMMENT ON COLUMN kb_policy_version.version_label IS '版本显示名称。';
COMMENT ON COLUMN kb_policy_version.source_year IS '来源年份。';
COMMENT ON COLUMN kb_policy_version.source_document_date IS '原始文档上的日期。';
COMMENT ON COLUMN kb_policy_version.issued_at IS '发布或签发日期。';
COMMENT ON COLUMN kb_policy_version.effective_date IS '生效日期。';
COMMENT ON COLUMN kb_policy_version.expired_at IS '失效日期。';
COMMENT ON COLUMN kb_policy_version.supersedes_version_id IS '被当前版本替代的旧版本ID。';
COMMENT ON COLUMN kb_policy_version.revision_type IS '修订类型，例如 revise、replace、initial。';
COMMENT ON COLUMN kb_policy_version.change_summary IS '本版本变更摘要。';
COMMENT ON COLUMN kb_policy_version.change_reason IS '本次修订原因。';
COMMENT ON COLUMN kb_policy_version.source_path IS '源文件存储路径。';
COMMENT ON COLUMN kb_policy_version.file_name IS '源文件名。';
COMMENT ON COLUMN kb_policy_version.file_ext IS '文件扩展名。';
COMMENT ON COLUMN kb_policy_version.file_hash IS '文件哈希值，用于去重或校验。';
COMMENT ON COLUMN kb_policy_version.is_scanned IS '是否扫描件。';
COMMENT ON COLUMN kb_policy_version.parse_method IS '解析方式，例如 direct、ocr。';
COMMENT ON COLUMN kb_policy_version.raw_text IS '原始抽取文本。';
COMMENT ON COLUMN kb_policy_version.clean_text IS '清洗后的全文。';
COMMENT ON COLUMN kb_policy_version.page_count IS '页数。';
COMMENT ON COLUMN kb_policy_version.parser_status IS '解析状态。';
COMMENT ON COLUMN kb_policy_version.version_status IS '版本状态，例如 draft、approved、active、superseded。';
COMMENT ON COLUMN kb_policy_version.ingested_at IS '入库时间。';
COMMENT ON COLUMN kb_policy_version.reviewed_at IS '审核完成时间。';
COMMENT ON COLUMN kb_policy_version.approved_at IS '审批完成时间。';
COMMENT ON COLUMN kb_policy_version.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_version.updated_at IS '更新时间。';

/*
政策章节表
字段：id, version_id, parent_section_id, section_no, section_title,
section_order, page_start, page_end, section_text, review_status,
review_note, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_section (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    parent_section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE CASCADE,
    section_no TEXT,
    section_title TEXT,
    section_order INTEGER NOT NULL DEFAULT 0,
    page_start INTEGER,
    page_end INTEGER,
    section_text TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'pending',
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE kb_policy_section IS '政策章节表：按章、条、款拆分后的结构化正文。';
COMMENT ON COLUMN kb_policy_section.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_section.version_id IS '所属政策版本ID。';
COMMENT ON COLUMN kb_policy_section.parent_section_id IS '父章节ID，用于构建章节树。';
COMMENT ON COLUMN kb_policy_section.section_no IS '章节编号。';
COMMENT ON COLUMN kb_policy_section.section_title IS '章节标题。';
COMMENT ON COLUMN kb_policy_section.section_order IS '章节顺序号。';
COMMENT ON COLUMN kb_policy_section.page_start IS '起始页码。';
COMMENT ON COLUMN kb_policy_section.page_end IS '结束页码。';
COMMENT ON COLUMN kb_policy_section.section_text IS '章节正文。';
COMMENT ON COLUMN kb_policy_section.review_status IS '章节审核状态。';
COMMENT ON COLUMN kb_policy_section.review_note IS '章节审核备注。';
COMMENT ON COLUMN kb_policy_section.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_section.updated_at IS '更新时间。';

/*
检索切块表
字段：id, version_id, section_id, chunk_index, page_no, chunk_text,
embedding, metadata, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_chunk (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL,
    page_no INTEGER,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_chunk UNIQUE (version_id, chunk_index)
);

COMMENT ON TABLE kb_policy_chunk IS '检索切块表：用于向量检索和 RAG 的文本切块。';
COMMENT ON COLUMN kb_policy_chunk.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_chunk.version_id IS '所属政策版本ID。';
COMMENT ON COLUMN kb_policy_chunk.section_id IS '所属章节ID，可为空。';
COMMENT ON COLUMN kb_policy_chunk.chunk_index IS '切块序号。';
COMMENT ON COLUMN kb_policy_chunk.page_no IS '页码。';
COMMENT ON COLUMN kb_policy_chunk.chunk_text IS '切块文本内容。';
COMMENT ON COLUMN kb_policy_chunk.embedding IS '文本向量，当前维度为 1536。';
COMMENT ON COLUMN kb_policy_chunk.metadata IS '检索用元数据。';
COMMENT ON COLUMN kb_policy_chunk.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_chunk.updated_at IS '更新时间。';

/*
审核留痕表
字段：id, target_type, target_id, version_id, review_action,
review_comment, reviewer, reviewed_at, created_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_review_record (
    id BIGSERIAL PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id BIGINT NOT NULL,
    version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    review_action TEXT NOT NULL,
    review_comment TEXT,
    reviewer TEXT,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE kb_policy_review_record IS '审核留痕表：记录对各类对象的审核动作。';
COMMENT ON COLUMN kb_policy_review_record.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_review_record.target_type IS '被审核对象类型。';
COMMENT ON COLUMN kb_policy_review_record.target_id IS '被审核对象ID。';
COMMENT ON COLUMN kb_policy_review_record.version_id IS '关联的政策版本ID。';
COMMENT ON COLUMN kb_policy_review_record.review_action IS '审核动作。';
COMMENT ON COLUMN kb_policy_review_record.review_comment IS '审核意见。';
COMMENT ON COLUMN kb_policy_review_record.reviewer IS '审核人。';
COMMENT ON COLUMN kb_policy_review_record.reviewed_at IS '审核时间。';
COMMENT ON COLUMN kb_policy_review_record.created_at IS '创建时间。';

/*
版本变更表
字段：id, policy_id, from_version_id, to_version_id, change_type,
change_scope, affected_sections, change_summary, created_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_version_change (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    from_version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    to_version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    change_scope TEXT NOT NULL DEFAULT 'section',
    affected_sections TEXT,
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE kb_policy_version_change IS '版本变更表：记录两个版本之间的差异摘要。';
COMMENT ON COLUMN kb_policy_version_change.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_version_change.policy_id IS '所属政策主档ID。';
COMMENT ON COLUMN kb_policy_version_change.from_version_id IS '原版本ID。';
COMMENT ON COLUMN kb_policy_version_change.to_version_id IS '目标版本ID。';
COMMENT ON COLUMN kb_policy_version_change.change_type IS '变更类型。';
COMMENT ON COLUMN kb_policy_version_change.change_scope IS '变更范围。';
COMMENT ON COLUMN kb_policy_version_change.affected_sections IS '受影响章节列表。';
COMMENT ON COLUMN kb_policy_version_change.change_summary IS '变更摘要。';
COMMENT ON COLUMN kb_policy_version_change.created_at IS '创建时间。';

/*
政策画像表
字段：id, policy_id, version_id, policy_type, applicable_scope,
department_owner, approval_level, keywords, summary, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_profile (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    policy_type TEXT NOT NULL,
    applicable_scope TEXT,
    department_owner TEXT,
    approval_level TEXT,
    keywords TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE kb_policy_profile IS '政策画像表：用于筛选、展示和摘要的业务元数据。';
COMMENT ON COLUMN kb_policy_profile.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_profile.policy_id IS '所属政策主档ID。';
COMMENT ON COLUMN kb_policy_profile.version_id IS '关联的政策版本ID，可为空。';
COMMENT ON COLUMN kb_policy_profile.policy_type IS '政策分类。';
COMMENT ON COLUMN kb_policy_profile.applicable_scope IS '适用范围。';
COMMENT ON COLUMN kb_policy_profile.department_owner IS '归口部门。';
COMMENT ON COLUMN kb_policy_profile.approval_level IS '审批级别。';
COMMENT ON COLUMN kb_policy_profile.keywords IS '关键词。';
COMMENT ON COLUMN kb_policy_profile.summary IS '摘要。';
COMMENT ON COLUMN kb_policy_profile.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_profile.updated_at IS '更新时间。';

CREATE INDEX IF NOT EXISTS idx_kb_policy_document_status ON kb_policy_document(status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_document_type ON kb_policy_document(policy_type);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_policy_id ON kb_policy_version(policy_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_status ON kb_policy_version(version_status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_effective_date ON kb_policy_version(effective_date);
CREATE INDEX IF NOT EXISTS idx_kb_policy_section_version_id ON kb_policy_section(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_chunk_version_id ON kb_policy_chunk(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_review_record_target ON kb_policy_review_record(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_change_policy_id ON kb_policy_version_change(policy_id);
