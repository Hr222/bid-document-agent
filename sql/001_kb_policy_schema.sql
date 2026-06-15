-- 制度规范类知识库表结构
-- 第一阶段：针对管理制度、绩效考核等存在版本迭代逻辑的资料设计
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

/*
制度规范类主档表
一条记录表示一项“资料本体”，例如《信息安全及保密制度》或《绩效考核办法》。
字段：id, policy_code, policy_name, policy_category, responsible_department,
current_version_id, latest_version_id, status, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_document (
    id BIGSERIAL PRIMARY KEY,
    policy_code TEXT UNIQUE,
    policy_name TEXT NOT NULL,
    policy_category TEXT NOT NULL,
    responsible_department TEXT,
    current_version_id BIGINT,
    latest_version_id BIGINT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kb_policy_document_status
        CHECK (status IN ('draft', 'active', 'archived'))
);

COMMENT ON TABLE kb_policy_document IS '制度规范类主档表：记录一项资料本体的基础信息，以及当前生效版本与最新收录版本。';
COMMENT ON COLUMN kb_policy_document.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_document.policy_code IS '资料唯一编码或外部编号。';
COMMENT ON COLUMN kb_policy_document.policy_name IS '资料名称。';
COMMENT ON COLUMN kb_policy_document.policy_category IS '资料类别，例如管理制度、绩效考核。';
COMMENT ON COLUMN kb_policy_document.responsible_department IS '负责维护该资料的部门。';
COMMENT ON COLUMN kb_policy_document.current_version_id IS '当前生效版本ID。';
COMMENT ON COLUMN kb_policy_document.latest_version_id IS '当前最新收录版本ID，未必已生效。';
COMMENT ON COLUMN kb_policy_document.status IS '主档状态：draft=主档已创建但未正式纳入可用知识库；active=主档有效且正常参与检索和版本管理；archived=主档已归档，不再作为当前运营资料使用但保留历史记录。';
COMMENT ON COLUMN kb_policy_document.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_document.updated_at IS '更新时间。';

/*
制度规范类版本表
一条记录表示某项资料的一个具体版本。
字段：id, policy_id, version_seq, version_label, source_year,
source_document_date, issued_at, effective_date, expired_at,
previous_version_id, revision_type, version_status, change_summary,
change_reason, source_path, file_name, file_ext, file_hash,
is_scanned, parse_method, raw_text, clean_text, page_count,
parser_status, ingested_at, reviewed_at, approved_at, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_version (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    version_seq INTEGER NOT NULL,
    version_label TEXT NOT NULL,
    source_year INTEGER,
    source_document_date DATE,
    issued_at DATE,
    effective_date DATE,
    expired_at DATE,
    previous_version_id BIGINT,
    revision_type TEXT NOT NULL DEFAULT 'revise',
    version_status TEXT NOT NULL DEFAULT 'draft',
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
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_version_id_policy UNIQUE (id, policy_id),
    CONSTRAINT uq_kb_policy_version_seq UNIQUE (policy_id, version_seq),
    CONSTRAINT uq_kb_policy_version_label UNIQUE (policy_id, version_label),
    CONSTRAINT uq_kb_policy_version_file_hash UNIQUE (policy_id, file_hash),
    CONSTRAINT chk_kb_policy_version_seq_positive CHECK (version_seq > 0),
    CONSTRAINT chk_kb_policy_version_year CHECK (
        source_year IS NULL OR source_year BETWEEN 1900 AND 2100
    ),
    CONSTRAINT chk_kb_policy_version_dates CHECK (
        expired_at IS NULL
        OR effective_date IS NULL
        OR expired_at >= effective_date
    ),
    CONSTRAINT chk_kb_policy_version_revision_type CHECK (
        revision_type IN ('initial', 'revise', 'replace', 'supplement', 'abolish')
    ),
    CONSTRAINT chk_kb_policy_version_status CHECK (
        version_status IN ('draft', 'reviewing', 'approved', 'active', 'superseded', 'retired')
    ),
    CONSTRAINT chk_kb_policy_version_parser_status CHECK (
        parser_status IN ('pending', 'processing', 'parsed', 'failed')
    ),
    CONSTRAINT chk_kb_policy_version_previous_self CHECK (
        previous_version_id IS NULL OR previous_version_id <> id
    ),
    CONSTRAINT chk_kb_policy_version_hash_not_blank CHECK (
        file_hash IS NULL OR btrim(file_hash) <> ''
    ),
    CONSTRAINT fk_kb_policy_version_previous_same_policy
        FOREIGN KEY (previous_version_id, policy_id)
        REFERENCES kb_policy_version(id, policy_id)
        ON DELETE RESTRICT
);

COMMENT ON TABLE kb_policy_version IS '制度规范类版本表：记录资料的各代版本、版本链关系、状态与来源文件信息。';
COMMENT ON COLUMN kb_policy_version.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_version.policy_id IS '所属主档ID。';
COMMENT ON COLUMN kb_policy_version.version_seq IS '同一资料内的版本顺序号，用于统计一共迭代了多少代。';
COMMENT ON COLUMN kb_policy_version.version_label IS '版本显示名称，例如 2023版、2025版。';
COMMENT ON COLUMN kb_policy_version.source_year IS '来源年份，便于按年度筛选。';
COMMENT ON COLUMN kb_policy_version.source_document_date IS '原文件上的日期。';
COMMENT ON COLUMN kb_policy_version.issued_at IS '发布或签发日期。';
COMMENT ON COLUMN kb_policy_version.effective_date IS '生效日期。';
COMMENT ON COLUMN kb_policy_version.expired_at IS '失效日期。';
COMMENT ON COLUMN kb_policy_version.previous_version_id IS '上一版本ID，必须属于同一资料，用于版本迭代链追踪。';
COMMENT ON COLUMN kb_policy_version.revision_type IS '修订类型：initial=首版；revise=常规修订；replace=整体替换；supplement=补充说明或补充条款；abolish=废止。';
COMMENT ON COLUMN kb_policy_version.version_status IS '版本状态：draft=已入库但仍在整理；reviewing=审核中；approved=审核通过但未正式启用；active=当前生效版本；superseded=已被新版本替代；retired=明确停用或废止。';
COMMENT ON COLUMN kb_policy_version.change_summary IS '本版本相较上一版的变更摘要。';
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
COMMENT ON COLUMN kb_policy_version.parser_status IS '解析状态：pending=待解析；processing=解析中；parsed=解析完成；failed=解析失败。';
COMMENT ON COLUMN kb_policy_version.ingested_at IS '系统入库时间。';
COMMENT ON COLUMN kb_policy_version.reviewed_at IS '审核完成时间。';
COMMENT ON COLUMN kb_policy_version.approved_at IS '知识库正式通过时间。';
COMMENT ON COLUMN kb_policy_version.created_at IS '创建时间。';
COMMENT ON COLUMN kb_policy_version.updated_at IS '更新时间。';

/*
制度规范类章节表
字段：id, version_id, parent_section_id, section_no, section_title,
section_level, section_path, section_order, page_start, page_end,
section_text, review_status, review_note, created_at, updated_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_section (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    parent_section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE CASCADE,
    section_no TEXT,
    section_title TEXT,
    section_level INTEGER NOT NULL DEFAULT 1,
    section_path TEXT,
    section_order INTEGER NOT NULL DEFAULT 0,
    page_start INTEGER,
    page_end INTEGER,
    section_text TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'pending',
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kb_policy_section_level CHECK (section_level > 0),
    CONSTRAINT chk_kb_policy_section_page_range CHECK (
        page_end IS NULL OR page_start IS NULL OR page_end >= page_start
    ),
    CONSTRAINT chk_kb_policy_section_review_status CHECK (
        review_status IN ('pending', 'reviewing', 'passed', 'rejected')
    )
);

COMMENT ON TABLE kb_policy_section IS '制度规范类章节表：按章、条、款拆分后的结构化正文，支持逐段审核与差异定位。';
COMMENT ON COLUMN kb_policy_section.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_section.version_id IS '所属版本ID。';
COMMENT ON COLUMN kb_policy_section.parent_section_id IS '父章节ID，用于构建章节树。';
COMMENT ON COLUMN kb_policy_section.section_no IS '章节编号。';
COMMENT ON COLUMN kb_policy_section.section_title IS '章节标题。';
COMMENT ON COLUMN kb_policy_section.section_level IS '章节层级。';
COMMENT ON COLUMN kb_policy_section.section_path IS '章节路径，例如 第一章/第一条。';
COMMENT ON COLUMN kb_policy_section.section_order IS '章节顺序号。';
COMMENT ON COLUMN kb_policy_section.page_start IS '起始页码。';
COMMENT ON COLUMN kb_policy_section.page_end IS '结束页码。';
COMMENT ON COLUMN kb_policy_section.section_text IS '章节正文。';
COMMENT ON COLUMN kb_policy_section.review_status IS '章节审核状态：pending=待审核；reviewing=审核中；passed=审核通过；rejected=审核驳回。';
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
    CONSTRAINT uq_kb_policy_chunk UNIQUE (version_id, chunk_index),
    CONSTRAINT chk_kb_policy_chunk_index_positive CHECK (chunk_index >= 0)
);

COMMENT ON TABLE kb_policy_chunk IS '检索切块表：用于向量检索和 RAG 的资料文本切块。';
COMMENT ON COLUMN kb_policy_chunk.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_chunk.version_id IS '所属版本ID。';
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kb_policy_review_target_type CHECK (
        target_type IN ('document', 'version', 'section', 'chunk')
    ),
    CONSTRAINT chk_kb_policy_review_action CHECK (
        review_action IN ('submit', 'approve', 'reject', 'return', 'activate', 'retire')
    )
);

COMMENT ON TABLE kb_policy_review_record IS '审核留痕表：记录主档、版本、章节等对象的审核动作。';
COMMENT ON COLUMN kb_policy_review_record.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_review_record.target_type IS '被审核对象类型：document=主档；version=版本；section=章节；chunk=切块。';
COMMENT ON COLUMN kb_policy_review_record.target_id IS '被审核对象ID。';
COMMENT ON COLUMN kb_policy_review_record.version_id IS '关联的版本ID。';
COMMENT ON COLUMN kb_policy_review_record.review_action IS '审核动作：submit=提交审核；approve=通过；reject=驳回；return=退回修改；activate=启用；retire=停用/归档。';
COMMENT ON COLUMN kb_policy_review_record.review_comment IS '审核意见。';
COMMENT ON COLUMN kb_policy_review_record.reviewer IS '审核人。';
COMMENT ON COLUMN kb_policy_review_record.reviewed_at IS '审核时间。';
COMMENT ON COLUMN kb_policy_review_record.created_at IS '创建时间。';

/*
版本变更表
字段：id, policy_id, from_version_id, to_version_id, change_type,
change_scope, affected_sections, change_summary, impact_level, created_at
*/
CREATE TABLE IF NOT EXISTS kb_policy_version_change (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    from_version_id BIGINT,
    to_version_id BIGINT NOT NULL,
    change_type TEXT NOT NULL,
    change_scope TEXT NOT NULL DEFAULT 'section',
    affected_sections TEXT,
    change_summary TEXT,
    impact_level TEXT NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kb_policy_version_change_type CHECK (
        change_type IN ('add', 'update', 'delete', 'replace', 'restructure')
    ),
    CONSTRAINT chk_kb_policy_version_change_scope CHECK (
        change_scope IN ('document', 'chapter', 'section', 'clause', 'metadata')
    ),
    CONSTRAINT chk_kb_policy_version_change_impact CHECK (
        impact_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT fk_kb_policy_version_change_from_same_policy
        FOREIGN KEY (from_version_id, policy_id)
        REFERENCES kb_policy_version(id, policy_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_kb_policy_version_change_to_same_policy
        FOREIGN KEY (to_version_id, policy_id)
        REFERENCES kb_policy_version(id, policy_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE kb_policy_version_change IS '版本变更表：记录两个版本之间的差异摘要，服务于版本迭代追踪。';
COMMENT ON COLUMN kb_policy_version_change.id IS '主键ID。';
COMMENT ON COLUMN kb_policy_version_change.policy_id IS '所属主档ID。';
COMMENT ON COLUMN kb_policy_version_change.from_version_id IS '原版本ID。';
COMMENT ON COLUMN kb_policy_version_change.to_version_id IS '目标版本ID。';
COMMENT ON COLUMN kb_policy_version_change.change_type IS '变更类型：add=新增；update=修改；delete=删除；replace=替换；restructure=结构重组。';
COMMENT ON COLUMN kb_policy_version_change.change_scope IS '变更范围：document=整篇文档；chapter=章；section=节/条；clause=具体条款；metadata=元数据。';
COMMENT ON COLUMN kb_policy_version_change.affected_sections IS '受影响章节列表。';
COMMENT ON COLUMN kb_policy_version_change.change_summary IS '变更摘要。';
COMMENT ON COLUMN kb_policy_version_change.impact_level IS '影响级别：low=低影响；medium=中影响；high=高影响。';
COMMENT ON COLUMN kb_policy_version_change.created_at IS '创建时间。';

ALTER TABLE kb_policy_document
    ADD CONSTRAINT fk_kb_policy_document_current_version_same_policy
    FOREIGN KEY (current_version_id, id)
    REFERENCES kb_policy_version(id, policy_id)
    ON DELETE RESTRICT;

ALTER TABLE kb_policy_document
    ADD CONSTRAINT fk_kb_policy_document_latest_version_same_policy
    FOREIGN KEY (latest_version_id, id)
    REFERENCES kb_policy_version(id, policy_id)
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_kb_policy_document_status ON kb_policy_document(status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_document_category ON kb_policy_document(policy_category);
CREATE INDEX IF NOT EXISTS idx_kb_policy_document_current_version_id ON kb_policy_document(current_version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_document_latest_version_id ON kb_policy_document(latest_version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_policy_id ON kb_policy_version(policy_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_status ON kb_policy_version(version_status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_source_year ON kb_policy_version(source_year);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_effective_date ON kb_policy_version(effective_date);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_previous_version_id ON kb_policy_version(previous_version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_section_version_id ON kb_policy_section(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_section_parent_section_id ON kb_policy_section(parent_section_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_chunk_version_id ON kb_policy_chunk(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_review_record_target ON kb_policy_review_record(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_change_policy_id ON kb_policy_version_change(policy_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_change_to_version_id ON kb_policy_version_change(to_version_id);
